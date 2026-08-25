"""Merge catalogo.csv with what can be read from each .gpkg and .qmd.

The team maintains 8 columns by hand. Everything else in the published
catalogue is computed here so nobody types a CRS or a record count twice.

Output is a derived artifact (nomenclatura: if a script can regenerate it, it
is cache, not data) and is not committed:

    catalogo/catalogo_completo.csv   flat table, for people and spreadsheets
    catalogo/catalogo_completo.json  same data, for the geoportal

Usage:
    py -3 ide-datos/scripts/derivar_catalogo.py [--salida DIR]
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comun  # noqa: E402

COLUMNAS_DERIVADAS = [
    "tema",
    "categoria_iso",
    "crs",
    "tipo_geometria",
    "cantidad_registros",
    "cantidad_campos",
    "campos",
    "bbox_5344",
    "bbox_4326",
    "licencia",
    "palabras_clave",
    "linaje",
    "contacto_email",
    "organizacion",
    "titulo_metadato",
    "resumen_metadato",
    "archivo_gpkg",
    "archivo_qmd",
    "tamano_bytes",
    "checksum_sha256",
    "fecha_modificacion",
]


def derivar(fila):
    """Build the derived half of one catalogue row. Returns (dict, error)."""
    did = fila["id"]
    tema = comun.tema_de(did)
    gpkg = comun.ruta_maestro(did, tema, "gpkg")
    qmd = comun.ruta_maestro(did, tema, "qmd")

    if not gpkg.exists():
        return None, f"{did}: no existe {gpkg.name}"

    info = comun.leer_gpkg(gpkg)
    meta = comun.leer_qmd(qmd) if qmd.exists() else {}

    bbox = info["bbox"]
    tiene_bbox = all(v is not None for v in bbox)
    raiz = comun.raiz_datos()

    campos = [c for c in info["nombres_campos"] if c != info["columna_geom"]]

    derivado = {
        "tema": tema,
        "categoria_iso": comun.TEMAS.get(tema, ""),
        "crs": info["authid"] or f"EPSG:{info['srs_id']}",
        "tipo_geometria": info["tipo_geometria"],
        "cantidad_registros": info["cantidad_registros"],
        "cantidad_campos": len(campos),
        "campos": "|".join(campos),
        "bbox_5344": ",".join(f"{v:.3f}" for v in bbox) if tiene_bbox else "",
        "bbox_4326": (
            ",".join(f"{v:.6f}" for v in comun.bbox_a_wgs84(bbox)) if tiene_bbox else ""
        ),
        "licencia": meta.get("licencia", ""),
        "palabras_clave": "|".join(meta.get("palabras_clave", [])),
        "linaje": meta.get("linaje", ""),
        "contacto_email": meta.get("contacto_email", ""),
        "organizacion": meta.get("organizacion", ""),
        "titulo_metadato": meta.get("titulo", ""),
        "resumen_metadato": meta.get("abstract", ""),
        "archivo_gpkg": gpkg.relative_to(raiz).as_posix(),
        "archivo_qmd": qmd.relative_to(raiz).as_posix() if qmd.exists() else "",
        "tamano_bytes": gpkg.stat().st_size,
        "checksum_sha256": comun.checksum_sha256(gpkg),
        "fecha_modificacion": comun.fecha_git(gpkg),
    }
    return derivado, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", help="directorio de salida (por defecto catalogo/)")
    parser.add_argument("--catalogo", help="ruta alternativa a catalogo.csv")
    args = parser.parse_args()

    ruta = Path(args.catalogo) if args.catalogo else comun.ruta_catalogo()
    if not ruta.exists():
        print(f"[ERROR] no existe {ruta}")
        return 1

    salida = Path(args.salida) if args.salida else comun.raiz_datos() / "catalogo"
    salida.mkdir(parents=True, exist_ok=True)

    filas, _ = comun.leer_catalogo(ruta)
    completas = []
    fallos = []

    for fila in filas:
        if not fila.get("id"):
            continue
        try:
            derivado, error = derivar(fila)
        except Exception as exc:  # noqa: BLE001
            derivado, error = None, f"{fila['id']}: {exc}"
        if error:
            fallos.append(error)
            continue
        completa = {c: fila.get(c, "") for c in comun.COLUMNAS_MANUALES}
        completa.update(derivado)
        completas.append(completa)
        print(
            f"  {fila['id']}: {derivado['cantidad_registros']} registros, "
            f"{derivado['cantidad_campos']} campos, {derivado['crs']}"
        )

    columnas = comun.COLUMNAS_MANUALES + COLUMNAS_DERIVADAS
    csv_salida = salida / "catalogo_completo.csv"
    with open(csv_salida, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=columnas, quoting=csv.QUOTE_ALL)
        escritor.writeheader()
        escritor.writerows(completas)

    json_salida = salida / "catalogo_completo.json"
    with open(json_salida, "w", encoding="utf-8") as fh:
        json.dump(completas, fh, ensure_ascii=False, indent=2)

    print()
    print(f"{len(completas)} dataset(s) derivado(s)")
    print(f"  {csv_salida}")
    print(f"  {json_salida}")

    for fallo in fallos:
        print(f"[ERROR] {fallo}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
