"""
Convierte un JSON grande de Spotify a CSV usando Polars (más eficiente
en memoria que pandas) + ijson (lectura en streaming, sin cargar los
2M registros completos en RAM de una vez).

Uso:
    python json_to_csv.py entrada.json salida.csv
"""

import sys
import json
import ijson
import polars as pl

TAMANO_LOTE = 100_000


def detectar_clave_lista(ruta_json):
    """Determina si los registros están en la raíz del JSON (lista)
    o anidados bajo una clave como 'tracks', 'songs', 'data', 'items'."""
    with open(ruta_json, "rb") as f:
        primer_char = f.read(1).strip()
    if primer_char == b"[":
        return None

    posibles = ("tracks", "songs", "data", "playlists", "items")
    with open(ruta_json, "rb") as f:
        for k, v in ijson.kvitems(f, ""):
            if k in posibles and isinstance(v, list):
                return k
    return None


def iterar_registros(ruta_json, clave_lista):
    """Generador: entrega un registro (dict) a la vez sin cargar todo el JSON."""
    prefijo = f"{clave_lista}.item" if clave_lista else "item"
    with open(ruta_json, "rb") as f:
        for registro in ijson.items(f, prefijo):
            yield registro


def aplanar_registro(registro, sep="_"):
    """Aplana un dict anidado; listas de valores simples -> texto con '; '."""
    plano = {}

    def _aplanar(obj, prefijo=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _aplanar(v, f"{prefijo}{k}{sep}" if prefijo else f"{k}{sep}")
        elif isinstance(obj, list):
            valores = [str(x) for x in obj if not isinstance(x, (dict, list))]
            plano[prefijo.rstrip(sep)] = "; ".join(valores)
        else:
            plano[prefijo.rstrip(sep)] = obj

    _aplanar(registro)
    return plano


def main():
    if len(sys.argv) != 3:
        print("Uso: python json_to_csv.py entrada.json salida.csv")
        sys.exit(1)

    entrada, salida = sys.argv[1], sys.argv[2]

    print(f"Detectando estructura de {entrada} ...")
    clave_lista = detectar_clave_lista(entrada)
    print(f"Clave raíz de la lista: {clave_lista or '(lista en la raíz)'}")

    print("Procesando en streaming por lotes de "
          f"{TAMANO_LOTE:,} registros (bajo consumo de RAM)...")

    total = 0
    lote = []

    with open(salida, "w", encoding="utf-8", newline="") as f_out:
        for registro in iterar_registros(entrada, clave_lista):
            lote.append(aplanar_registro(registro))
            total += 1

            if len(lote) >= TAMANO_LOTE:
                df = pl.DataFrame(lote, infer_schema_length=None)
                df.write_csv(f_out, include_header=(total == len(lote)))
                lote = []
                print(f"  {total:,} registros procesados...")

        if lote:
            df = pl.DataFrame(lote, infer_schema_length=None)
            df.write_csv(f_out, include_header=(total == len(lote)))

    print(f"Listo: {total:,} registros escritos en {salida}")


if __name__ == "__main__":
    main()
