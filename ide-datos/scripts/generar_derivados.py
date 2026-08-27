"""Generate publishable artifacts from each master GeoPackage.

Right now that means GeoJSON in EPSG:4326, which RFC 7946 requires. The
masters stay in EPSG:5344; reprojection happens only here, never upstream.

Two backends, picked automatically:

  ogr2ogr  used when it is on PATH (it ships with QGIS, and CI installs
           gdal-bin). Battle-tested, handles every geometry edge case.
  python   pure standard library fallback: reads the GeoPackage with
           sqlite3, decodes WKB, and reprojects with comun.a_wgs84().
           Runs anywhere, with nothing installed.

Both write byte-comparable coordinates at 7 decimals (~1 cm), the precision
RFC 7946 recommends.

Usage:
    py -3 ide-datos/scripts/generar_derivados.py
    py -3 ide-datos/scripts/generar_derivados.py --motor python
    py -3 ide-datos/scripts/generar_derivados.py --salida dist/
"""

import argparse
import json
import shutil
import sqlite3
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comun  # noqa: E402

# RFC 7946 section 11.2: 7 decimals is about a centimetre. More is noise.
DECIMALES = 7


# --- WKB decoding ----------------------------------------------------------
# GeoPackage stores a small binary header before standard ISO WKB.
# Spec: http://www.geopackage.org/spec/#gpb_format

TIPOS_WKB = {
    1: "Point",
    2: "LineString",
    3: "Polygon",
    4: "MultiPoint",
    5: "MultiLineString",
    6: "MultiPolygon",
    7: "GeometryCollection",
}

# Envelope layouts by header flag: code -> how many doubles follow.
DOBLES_ENVOLVENTE = {0: 0, 1: 4, 2: 6, 3: 6, 4: 8}


class LectorWKB:
    """Cursor over a WKB buffer that projects every vertex as it reads."""

    def __init__(self, datos, desplazamiento, proyectar):
        self.datos = datos
        self.pos = desplazamiento
        self.proyectar = proyectar
        self.orden = "<"

    def _leer(self, formato):
        formato = self.orden + formato
        tam = struct.calcsize(formato)
        valores = struct.unpack_from(formato, self.datos, self.pos)
        self.pos += tam
        return valores

    def _cabecera(self):
        """Read byte order and geometry type. Returns (tipo, tiene_z, tiene_m)."""
        (orden,) = struct.unpack_from("B", self.datos, self.pos)
        self.pos += 1
        self.orden = "<" if orden == 1 else ">"
        (codigo,) = self._leer("I")

        # ISO WKB encodes dimensionality in the thousands digit:
        # 1000 = Z, 2000 = M, 3000 = ZM.
        tiene_z = 1000 <= codigo < 2000 or 3000 <= codigo < 4000
        tiene_m = 2000 <= codigo < 4000
        return codigo % 1000, tiene_z, tiene_m

    def _punto(self, tiene_z, tiene_m):
        extra = (1 if tiene_z else 0) + (1 if tiene_m else 0)
        valores = self._leer("dd" + "d" * extra)
        lon, lat = self.proyectar(valores[0], valores[1])
        return [round(lon, DECIMALES), round(lat, DECIMALES)]

    def _cadena(self, tiene_z, tiene_m):
        (cantidad,) = self._leer("I")
        return [self._punto(tiene_z, tiene_m) for _ in range(cantidad)]

    def _anillos(self, tiene_z, tiene_m):
        (cantidad,) = self._leer("I")
        return [self._cadena(tiene_z, tiene_m) for _ in range(cantidad)]

    def geometria(self):
        tipo, tiene_z, tiene_m = self._cabecera()
        nombre = TIPOS_WKB.get(tipo)
        if nombre is None:
            raise ValueError(f"tipo de geometría WKB desconocido: {tipo}")

        if nombre == "Point":
            return {"type": nombre, "coordinates": self._punto(tiene_z, tiene_m)}
        if nombre == "LineString":
            return {"type": nombre, "coordinates": self._cadena(tiene_z, tiene_m)}
        if nombre == "Polygon":
            return {"type": nombre, "coordinates": self._anillos(tiene_z, tiene_m)}

        # Multi* and GeometryCollection embed complete WKB geometries, each
        # with its own byte-order byte, so recurse instead of reading raw
        # coordinates.
        (cantidad,) = self._leer("I")
        partes = [self.geometria() for _ in range(cantidad)]
        if nombre == "GeometryCollection":
            return {"type": nombre, "geometries": partes}
        return {"type": nombre, "coordinates": [p["coordinates"] for p in partes]}


def wkb_a_geojson(blob, proyectar):
    """Decode a GeoPackage geometry blob into a GeoJSON geometry dict."""
    if blob is None:
        return None
    if blob[:2] != b"GP":
        raise ValueError("el blob no empieza con el magic 'GP' del GeoPackage")

    banderas = blob[3]
    orden_cabecera = "<" if banderas & 1 else ">"
    codigo_envolvente = (banderas >> 1) & 0x07
    vacia = bool((banderas >> 4) & 1)

    if codigo_envolvente not in DOBLES_ENVOLVENTE:
        raise ValueError(f"código de envolvente inválido: {codigo_envolvente}")

    # 2 magic + 1 version + 1 flags + 4 srs_id, then the envelope.
    desplazamiento = 8 + DOBLES_ENVOLVENTE[codigo_envolvente] * 8
    if vacia:
        return None

    del orden_cabecera  # srs_id is not needed; the CRS comes from gpkg_contents
    return LectorWKB(blob, desplazamiento, proyectar).geometria()


# --- normalization ---------------------------------------------------------
# Both engines finish here, so the file on disk is identical whichever ran.


def _area_con_signo(anillo):
    """Shoelace area. Positive means counterclockwise."""
    # Index instead of unpacking: a 3D ring would raise on (x, y) unpacking.
    total = 0.0
    for actual, siguiente in zip(anillo, anillo[1:]):
        total += (siguiente[0] - actual[0]) * (siguiente[1] + actual[1])
    return -total / 2.0


def _ordenar_anillos(poligono):
    """RFC 7946 section 3.1.6: exterior ring counterclockwise, holes clockwise."""
    salida = []
    for indice, anillo in enumerate(poligono):
        if len(anillo) < 4:
            salida.append(anillo)
            continue
        antihorario = _area_con_signo(anillo) > 0
        quiero_antihorario = indice == 0
        salida.append(anillo if antihorario == quiero_antihorario else anillo[::-1])
    return salida


def normalizar_geometria(geometria):
    if not geometria:
        return geometria
    tipo = geometria.get("type")
    if tipo == "Polygon":
        geometria["coordinates"] = _ordenar_anillos(geometria["coordinates"])
    elif tipo == "MultiPolygon":
        geometria["coordinates"] = [
            _ordenar_anillos(p) for p in geometria["coordinates"]
        ]
    elif tipo == "GeometryCollection":
        for parte in geometria.get("geometries", []):
            normalizar_geometria(parte)
    return geometria


def normalizar_propiedades(entidad):
    """Tidy the attribute values on the way out.

    QGIS exports carry whatever the operator typed: trailing spaces, a stray
    newline at the end of a name. That noise reaches every consumer of the
    published GeoJSON, so it is cleaned here rather than hidden by the viewer.
    An attribute left empty becomes null, which says "no value" instead of
    pretending there is a blank one.
    """
    propiedades = entidad.get("properties")
    if not isinstance(propiedades, dict):
        return
    for campo, valor in propiedades.items():
        if not isinstance(valor, str):
            continue
        limpio = " ".join(valor.split())
        propiedades[campo] = limpio or None


def escribir_coleccion(entidades, destino):
    for entidad in entidades:
        normalizar_geometria(entidad.get("geometry"))
        normalizar_propiedades(entidad)
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(
            {"type": "FeatureCollection", "features": entidades},
            fh,
            ensure_ascii=False,
        )
    return len(entidades)


# --- backends --------------------------------------------------------------


def hay_ogr2ogr():
    return shutil.which("ogr2ogr") is not None


def generar_con_ogr2ogr(gpkg, destino):
    # -s_srs restates the master projection without a datum, so PROJ does not
    # insert the POSGAR 2007 -> WGS 84 shift. See comun.PROJ4_MAESTRO.
    subprocess.run(
        [
            "ogr2ogr",
            "-f", "GeoJSON",
            str(destino),
            str(gpkg),
            "-s_srs", comun.PROJ4_MAESTRO,
            "-t_srs", f"EPSG:{comun.CRS_PUBLICACION}",
            "-lco", f"COORDINATE_PRECISION={DECIMALES}",
            # Drop Z/M. The python engine reads 2D only, so without this a
            # layer with elevation would come out different from each engine.
            "-dim", "XY",
            "-overwrite",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    # Re-emit through the same writer as the python engine, so ring winding
    # and JSON formatting do not depend on which engine ran.
    with open(destino, encoding="utf-8") as fh:
        entidades = json.load(fh)["features"]
    return escribir_coleccion(entidades, destino)


def generar_con_python(gpkg, destino):
    info = comun.leer_gpkg(gpkg)
    if info["srs_id"] != comun.CRS_MAESTRO:
        raise ValueError(
            f"el maestro está en EPSG:{info['srs_id']}; el motor python solo "
            f"reproyecta desde EPSG:{comun.CRS_MAESTRO}"
        )

    tabla = info["tabla"]
    col_geom = info["columna_geom"]
    atributos = [c for c in info["nombres_campos"] if c != col_geom]

    con = sqlite3.connect(f"file:{Path(gpkg).as_posix()}?mode=ro", uri=True)
    try:
        columnas = ", ".join(f'"{c}"' for c in atributos + [col_geom])
        entidades = []
        for fila in con.execute(f'SELECT {columnas} FROM "{tabla}"'):
            propiedades = dict(zip(atributos, fila[:-1]))
            geometria = wkb_a_geojson(fila[-1], comun.a_wgs84)
            entidades.append(
                {
                    "type": "Feature",
                    "id": propiedades.get("id"),
                    "geometry": geometria,
                    "properties": propiedades,
                }
            )
    finally:
        con.close()

    return escribir_coleccion(entidades, destino)


# --- driver ----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--motor",
        choices=("auto", "ogr2ogr", "python"),
        default="auto",
        help="auto usa ogr2ogr si está disponible (por defecto)",
    )
    parser.add_argument(
        "--salida", help="directorio de salida (por defecto ide-datos/derivados/)"
    )
    parser.add_argument("--catalogo", help="ruta alternativa a catalogo.csv")
    args = parser.parse_args()

    ruta = Path(args.catalogo) if args.catalogo else comun.ruta_catalogo()
    if not ruta.exists():
        print(f"[ERROR] no existe {ruta}")
        return 1

    salida = Path(args.salida) if args.salida else comun.raiz_datos() / "derivados"
    salida.mkdir(parents=True, exist_ok=True)

    motor = args.motor
    if motor == "auto":
        motor = "ogr2ogr" if hay_ogr2ogr() else "python"
    if motor == "ogr2ogr" and not hay_ogr2ogr():
        print("[ERROR] se pidió ogr2ogr pero no está en el PATH")
        return 1

    print(f"Motor: {motor}")
    print(f"Salida: {salida}")
    print()

    filas, _ = comun.leer_catalogo(ruta)
    fallos = []
    generados = 0

    for fila in filas:
        did = fila.get("id")
        if not did:
            continue
        tema = comun.tema_de(did)
        gpkg = comun.ruta_maestro(did, tema, "gpkg")
        if not gpkg.exists():
            fallos.append(f"{did}: no existe {gpkg.name}")
            continue

        destino = salida / f"{did}.geojson"
        try:
            if motor == "ogr2ogr":
                cantidad = generar_con_ogr2ogr(gpkg, destino)
            else:
                cantidad = generar_con_python(gpkg, destino)
        except subprocess.CalledProcessError as exc:
            fallos.append(f"{did}: ogr2ogr falló: {exc.stderr.strip()}")
            continue
        except Exception as exc:  # noqa: BLE001
            fallos.append(f"{did}: {exc}")
            continue

        tamano = destino.stat().st_size
        print(f"  {destino.name}: {cantidad} entidades, {tamano // 1024} KB")
        generados += 1

    print()
    print(f"{generados} archivo(s) generado(s)")
    for fallo in fallos:
        print(f"[ERROR] {fallo}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
