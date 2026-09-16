"""
Extrae metadata única de tracks (track_uri, artist_name, track_name,
album_name, duration_ms) desde los archivos "slice" del Spotify Million
Playlist Dataset (mpd.slice.XXXXX-YYYYY.json).

El dataset trae 1,000 archivos, cada uno con ~1,000 playlists, y cada
playlist con varios tracks. Un mismo track_uri aparece repetido en miles
de playlists distintas, así que este script deduplica en memoria
(diccionario por track_uri) mientras recorre todos los archivos en
streaming (no carga cada slice completo de golpe).

Uso:
    python extraer_metadata_mpd.py carpeta_con_slices/ metadata_tracks.csv
"""

import sys
import os
import ijson
import polars as pl


def iterar_archivos_slice(carpeta):
    archivos = sorted(
        f for f in os.listdir(carpeta)
        if f.startswith("mpd.slice.") and f.endswith(".json")
    )
    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron archivos 'mpd.slice.*.json' en {carpeta}"
        )
    return [os.path.join(carpeta, f) for f in archivos]


def extraer_tracks_de_archivo(ruta_archivo, tracks_unicos):
    with open(ruta_archivo, "rb") as f:
        for playlist in ijson.items(f, "playlists.item"):
            for track in playlist.get("tracks", []):
                uri = track.get("track_uri")
                if uri:
                    # normaliza "spotify:track:XXXX" -> "XXXX" para que
                    # coincida con el formato de track_id/track_uri de tu
                    # otro CSV (22 caracteres, sin prefijo)
                    uri = uri.replace("spotify:track:", "")
                if uri and uri not in tracks_unicos:
                    tracks_unicos[uri] = {
                        "track_uri": uri,
                        "artist_name": track.get("artist_name"),
                        "track_name": track.get("track_name"),
                        "album_name": track.get("album_name"),
                        "duration_ms": track.get("duration_ms"),
                    }


def main():
    if len(sys.argv) != 3:
        print("Uso: python extraer_metadata_mpd.py carpeta_con_slices/ salida.csv")
        sys.exit(1)

    carpeta, salida = sys.argv[1], sys.argv[2]

    archivos = iterar_archivos_slice(carpeta)
    print(f"Encontrados {len(archivos)} archivos slice.")

    tracks_unicos = {}
    for i, ruta in enumerate(archivos, start=1):
        extraer_tracks_de_archivo(ruta, tracks_unicos)
        if i % 50 == 0 or i == len(archivos):
            print(f"  {i}/{len(archivos)} archivos procesados — "
                  f"{len(tracks_unicos):,} tracks únicos hasta ahora")

    print(f"Total tracks únicos: {len(tracks_unicos):,}")
    print("Escribiendo CSV...")

    df = pl.DataFrame(list(tracks_unicos.values()))
    df.write_csv(salida)

    print(f"Listo: {salida} generado con {df.height:,} filas.")


if __name__ == "__main__":
    main()
