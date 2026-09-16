# Normalización de datos de Spotify

Proyecto académico para la materia de bases de datos: transformación,
normalización y carga de un dataset masivo de canciones de Spotify
(~2 millones de registros) para su análisis en Power BI.

## Fuentes de datos

1. **[2 Million Song Spotify Dataset](https://www.kaggle.com/datasets/sergeserbinenko/2-million-song-spotify-dataset)**
   (Serge Serbinenko, Kaggle) — audio features (danceability, energy,
   tempo, etc.) por track, en formato JSON.

2. **[Spotify Million Playlist Dataset](https://www.kaggle.com/datasets/himanshuwagh/spotify-million)**
   — metadata de tracks (artista, nombre de canción, álbum) extraída de
   playlists de usuarios, en 1,000 archivos JSON (`mpd.slice.*.json`).

## Flujo del proyecto

```
2mil_dataset.json ──(json_to_csv.py)──> salida.csv ──(dedup)──> salida_limpia.csv
                                                                        │
mpd_slices/data/*.json ──(extraer_metadata_mpd.py)──> metadata_tracks.csv
                                                                        │
                                                                        ▼
                                                          MongoDB Atlas (NoSQL)
                                                          ├── audio_features
                                                          └── tracks
                                                                        │
                                                                        ▼
                                                                  Power BI
```

## Scripts

- **`json_to_csv.py`** — convierte el JSON de audio features a CSV,
  usando `ijson` (streaming) + `polars` para procesar millones de
  registros sin cargar todo el archivo en memoria.

- **`extraer_metadata_mpd.py`** — recorre los 1,000 archivos slice del
  Million Playlist Dataset y extrae metadata única por `track_uri`
  (artista, nombre, álbum), deduplicando tracks que se repiten en
  miles de playlists distintas.

- **`cruzar_datasets.py`** — cruza ambos datasets por `track_uri`
  cuando se necesita una tabla enriquecida (audio features + metadata
  en una sola fila).

## Resultados

| Archivo | Filas | Contenido |
|---|---|---|
| `salida.csv` | 2,305,616 | Audio features (con duplicados de track_uri) |
| `salida_limpia.csv` | 1,477,073 | Audio features (único por track_uri) |
| `metadata_tracks.csv` | 2,262,292 | Artista, canción, álbum (único por track_uri) |

## Base de datos NoSQL (MongoDB Atlas)

Los CSV resultantes se cargaron a un clúster gratuito de MongoDB Atlas
(M0) usando `mongoimport`, como dos colecciones separadas
(`audio_features` y `tracks`), relacionadas por `track_uri`. Debido al
límite de almacenamiento del tier gratuito (512 MB), se trabajó con una
muestra representativa en vez del volumen completo.

La conexión a Power BI se hace mediante el conector nativo
**MongoDB Atlas SQL**, disponible en Power BI Desktop bajo
"Obtener datos > Base de datos".

## Requisitos

```
pip install -r requirements.txt
```

Ver `requirements.txt` para las dependencias (`polars`, `ijson`).

## Notas

- Los archivos de datos (`.csv`, `.json`) no se incluyen en este
  repositorio por su tamaño y por los términos de licencia de los
  datasets originales — deben descargarse desde las fuentes citadas
  arriba.
- Este proyecto es de carácter educativo, desarrollado para la
  materia de bases de datos.