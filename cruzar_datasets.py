"""
Cruza dos datasets de Spotify:
  - masivo.csv (2.3M filas): solo audio features, indexado por track_uri
  - metadata.csv (232K filas): artist_name, track_name, genre, popularity,
    indexado por track_id

El cruce es por track_id == track_uri (mismo formato de ID de Spotify).

Resultado: dos archivos de salida
  - enriquecido.csv   -> filas del masivo que SÍ tienen metadata (inner join)
  - solo_features.csv -> filas del masivo que NO tienen metadata (quedan
                          solo con las métricas de audio, sin nombre/artista)

Uso:
    python cruzar_datasets.py masivo.csv metadata.csv
"""

import sys
import polars as pl


def main():
    if len(sys.argv) != 3:
        print("Uso: python cruzar_datasets.py masivo.csv metadata.csv")
        sys.exit(1)

    ruta_masivo, ruta_metadata = sys.argv[1], sys.argv[2]

    print(f"Cargando metadata desde {ruta_metadata} ...")
    metadata = pl.read_csv(ruta_metadata)
    metadata = metadata.rename({"track_id": "track_uri"})

    # Del CSV de metadata solo nos interesan estas columnas (evita duplicar
    # las columnas de audio features, que ya vienen del dataset masivo)
    columnas_utiles = ["track_uri", "genre", "artist_name", "track_name", "popularity"]
    metadata = metadata.select([c for c in columnas_utiles if c in metadata.columns])

    # Si un track_id se repite en metadata (mismo track en varios géneros),
    # nos quedamos con la primera aparición para evitar duplicar filas al cruzar
    metadata = metadata.unique(subset=["track_uri"], keep="first")
    print(f"  Metadata: {metadata.height:,} filas únicas por track_uri")

    print(f"Leyendo masivo en modo lazy desde {ruta_masivo} ...")
    masivo = pl.scan_csv(ruta_masivo)

    print("Haciendo left join (masivo + metadata) ...")
    resultado = masivo.join(metadata.lazy(), on="track_uri", how="left")

    resultado = resultado.collect(engine="streaming")
    print(f"Total filas resultado: {resultado.height:,}")

    enriquecido = resultado.filter(pl.col("artist_name").is_not_null())
    solo_features = resultado.filter(pl.col("artist_name").is_null())

    print(f"  Con metadata (enriquecido.csv):   {enriquecido.height:,} filas")
    print(f"  Sin metadata (solo_features.csv): {solo_features.height:,} filas")

    enriquecido.write_csv("enriquecido.csv")
    solo_features.write_csv("solo_features.csv")

    print("Listo: enriquecido.csv y solo_features.csv generados.")


if __name__ == "__main__":
    main()
