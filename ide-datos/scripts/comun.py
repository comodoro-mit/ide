"""Shared helpers for the IDE Comodoro data pipeline.

Standard library only: no GDAL, no geopandas. A GeoPackage is a SQLite file,
so sqlite3 is enough to read schema, extent and feature counts. Keeps the
scripts runnable with `py -3` on Windows and on a bare CI runner.
"""

import csv
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# --- constants from propuesta/nomenclatura.md ------------------------------

# Section 3: the 14 fixed themes, each mapped 1:1 to an ISO 19115 topicCategory.
TEMAS = {
    "adm": "boundaries",
    "amb": "environment",
    "cat": "planningCadastre",
    "cen": "society",
    "edu": "society",
    "equ": "structure",
    "hid": "inlandWaters",
    "inf": "utilitiesCommunication",
    "pla": "planningCadastre",
    "rie": "geoscientificInformation",
    "sal": "health",
    "top": "elevation",
    "tra": "transportation",
    "urb": "structure",
}

# Same keys, the label people read. nomenclatura.md section 3.
NOMBRES_TEMA = {
    "adm": "Límites y administración",
    "amb": "Ambiente y espacios verdes",
    "cat": "Catastro y parcelario",
    "cen": "Censo y demografía",
    "edu": "Educación",
    "equ": "Equipamiento comunitario",
    "hid": "Hidrografía",
    "inf": "Infraestructura y servicios",
    "pla": "Planeamiento urbano",
    "rie": "Riesgo y emergencias",
    "sal": "Salud",
    "top": "Topografía y relieve",
    "tra": "Transporte y movilidad",
    "urb": "Trama urbana",
}

CRS_MAESTRO = 5344  # POSGAR 2007 / Argentina zone 2
CRS_PUBLICACION = 4326  # WGS 84, required by RFC 7946 for GeoJSON

# The same projection as EPSG:5344, stated without a datum.
#
# Asking PROJ (and therefore ogr2ogr) to go from the EPSG code to EPSG:4326
# makes it insert the registered "POSGAR 2007 to WGS 84 (2)" transformation,
# which shifts every coordinate about 0.66 m north and 0.20 m east while
# declaring its own accuracy as 0.5 m. POSGAR 2007 uses the WGS 84 ellipsoid
# and both realizations are ITRF-based, so treating them as equivalent is the
# usual practice for web publication and is what our pure-Python path does.
#
# Using this as the source keeps ogr2ogr and the python engine bit-identical.
# If IGN ever asks for the registered transformation, drop this and apply it in
# BOTH engines, never in one.
PROJ4_MAESTRO = (
    "+proj=tmerc +lat_0=-90 +lon_0=-69 +k=1 +x_0=2500000 +y_0=0 "
    "+ellps=WGS84 +units=m +no_defs"
)

# Section 2: cr-<tema>-<entidad>[-<calificador>], max 50 chars, immutable.
RE_ID = re.compile(r"^cr-(" + "|".join(TEMAS) + r")-[a-z0-9]+(-[a-z0-9]+)*$")
LARGO_MAX_ID = 50

# Section 5: field naming rules.
RE_CAMPO = re.compile(r"^[a-z][a-z0-9_]*$")
LARGO_MAX_CAMPO = 30
CAMPOS_PROHIBIDOS = {"fid", "objectid", "shape_area", "shape_length", "shape_leng"}

# Section 7: dataset life cycle. Values live in catalogo/vocabularios/ so the
# committee can change them without touching code; this is the fallback.
ESTADOS = ["borrador", "en_revision", "publicado", "desactualizado", "retirado"]

RE_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# Columns the team actually maintains by hand in catalogo.csv. Everything else
# is derived from the .gpkg / .qmd by derivar_catalogo.py.
COLUMNAS_MANUALES = [
    "id",
    "titulo",
    "descripcion",
    "responsable",
    "estado",
    "categoria",
    "version",
    # IDERA element A8 (maintenance frequency) is mandatory and the QGIS .qmd
    # schema has no field for it, so it has to live in the catalogue. Optional
    # for now so existing rows keep validating; creador_metadata.py reports it
    # as a compliance gap until it is filled.
    "frecuencia_actualizacion",
    "notas_internas",
]
COLUMNAS_OPCIONALES = {"notas_internas", "frecuencia_actualizacion"}

# ISO 19115 MD_MaintenanceFrequencyCode.
FRECUENCIAS = [
    "continual",
    "daily",
    "weekly",
    "fortnightly",
    "monthly",
    "quarterly",
    "biannually",
    "annually",
    "asNeeded",
    "irregular",
    "notPlanned",
    "unknown",
]


# --- paths -----------------------------------------------------------------


def raiz_datos():
    """Return the ide-datos/ directory, walking up from this file."""
    return Path(__file__).resolve().parent.parent


def ruta_catalogo():
    return raiz_datos() / "catalogo" / "catalogo.csv"


def ruta_config():
    return raiz_datos() / "config.json"


def leer_config():
    """Read ide-datos/config.json. Missing file means every default applies."""
    ruta = ruta_config()
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def url_base():
    """Public base URL of the published site, without a trailing slash.

    Empty until somebody decides where the site lives. While it is empty the
    catalogue simply omits url_descarga and url_metadatos instead of inventing
    a hostname that would then circulate inside published metadata.
    The environment variable wins so CI can override it per deployment.
    """
    valor = os.environ.get("IDE_URL_BASE") or leer_config().get("url_base", "")
    return valor.rstrip("/")


def ruta_maestro(dataset_id, tema, extension):
    return raiz_datos() / "maestros" / tema / f"{dataset_id}.{extension}"


# Attributes that must never leave the municipality, per dataset.
#
# A master layer may legitimately hold data that the open catalogue must not
# republish. The phone numbers of the people who chair the neighbourhood
# associations are the case that created this: useful inside the municipality,
# personal data of private citizens once published under CC BY 4.0.
#
# That case is closed: `tel` was dropped from the master in 2.0.0, because this
# mechanism protects what gets published and not the master itself, and the
# master is committed to a public repository. Read the limit twice before
# relying on this: reserving a field is not a way to keep personal data in a
# public repo.
#
# Declared here and only here, so every script strips the same fields:
#   generar_derivados.py  leaves them out of the GeoJSON and writes a
#                         sanitised GeoPackage next to it
#   armar_sitio.py        publishes that sanitised copy, never the master
#   derivar_catalogo.py   leaves them out of the `campos` column, so the
#                         published catalogue does not even name them
#
# The master keeps the column: this hides the field from what is published, it
# does not delete anything from the source of truth.
#
# Empty on purpose right now. The mechanism stays wired into the three scripts
# below, so declaring a field here is all it takes.
CAMPOS_RESERVADOS = {}


def campos_reservados(dataset_id):
    """Attributes of this dataset that must not be published. Never None."""
    return tuple(CAMPOS_RESERVADOS.get(dataset_id, ()))


# Layout of the published site. derivar_catalogo.py builds the URLs and
# armar_sitio.py writes the files, both from here, so they cannot drift apart.
CARPETA_DATOS = "datos"
CARPETA_METADATOS = "metadatos"


def urls_publicacion(dataset_id):
    """Public URLs for one dataset. The keys always exist; the values are
    empty strings while url_base is undefined, so consumers of the catalogue
    see a stable shape either way."""
    base = url_base()
    if not base:
        return {
            "url_descarga": "",
            "url_descarga_geojson": "",
            "url_metadatos": "",
        }
    return {
        "url_descarga": f"{base}/{CARPETA_DATOS}/{dataset_id}.gpkg",
        "url_descarga_geojson": f"{base}/{CARPETA_DATOS}/{dataset_id}.geojson",
        # The ISO 19139 XML, not the .qmd: this is the URL a catalogue harvester
        # follows, and the .qmd is a QGIS working file, not an interchange
        # format. Both get published; only this one is advertised.
        "url_metadatos": f"{base}/{CARPETA_METADATOS}/{dataset_id}.xml",
    }


def tema_de(dataset_id):
    """Extract the 3-letter theme prefix from a dataset id."""
    partes = dataset_id.split("-")
    return partes[1] if len(partes) > 2 else ""


def nombre_capa(dataset_id):
    """Layer name inside the GeoPackage: same id with underscores."""
    return dataset_id.replace("-", "_")


# --- catalogo.csv ----------------------------------------------------------


def leer_catalogo(ruta=None):
    """Read catalogo.csv as a list of dicts. Returns (rows, fieldnames)."""
    ruta = Path(ruta) if ruta else ruta_catalogo()
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        lector = csv.DictReader(fh)
        filas = [{k: (v or "").strip() for k, v in fila.items()} for fila in lector]
        return filas, list(lector.fieldnames or [])


def leer_vocabulario(nombre, por_defecto):
    """Read catalogo/vocabularios/<nombre>.csv, first column. Falls back."""
    ruta = raiz_datos() / "catalogo" / "vocabularios" / f"{nombre}.csv"
    if not ruta.exists():
        return list(por_defecto)
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        lector = csv.reader(fh)
        next(lector, None)  # header
        return [fila[0].strip() for fila in lector if fila and fila[0].strip()]


# --- GeoPackage ------------------------------------------------------------


def leer_gpkg(ruta):
    """Read structure and extent of a single-layer GeoPackage.

    Returns a dict, or raises ValueError when the file is not a usable
    single-layer GPKG.
    """
    con = sqlite3.connect(f"file:{Path(ruta).as_posix()}?mode=ro", uri=True)
    try:
        capas = con.execute(
            "SELECT table_name, min_x, min_y, max_x, max_y, srs_id "
            "FROM gpkg_contents WHERE data_type = 'features'"
        ).fetchall()
        if len(capas) != 1:
            raise ValueError(
                f"se esperaba exactamente 1 capa vectorial, hay {len(capas)}"
            )
        tabla, min_x, min_y, max_x, max_y, srs_id = capas[0]

        geo = con.execute(
            "SELECT column_name, geometry_type_name, srs_id "
            "FROM gpkg_geometry_columns WHERE table_name = ?",
            (tabla,),
        ).fetchone()
        col_geom, tipo_geom, srs_geom = geo if geo else ("geom", "UNKNOWN", srs_id)

        authid = None
        srs = con.execute(
            "SELECT organization, organization_coordsys_id FROM gpkg_spatial_ref_sys "
            "WHERE srs_id = ?",
            (srs_id,),
        ).fetchone()
        if srs:
            authid = f"{srs[0]}:{srs[1]}"

        campos = []
        for _, nombre, tipo, notnull, _, pk in con.execute(
            f'PRAGMA table_info("{tabla}")'
        ):
            campos.append(
                {"nombre": nombre, "tipo": tipo, "notnull": bool(notnull), "pk": bool(pk)}
            )

        registros = con.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]

        # gpkg_contents holds exact doubles but can go stale after edits in
        # QGIS. The rtree index is always current, though its float32 bounds
        # are rounded outward. Prefer gpkg_contents; fall back to the rtree
        # when it is missing, or when the rtree reaches more than a metre
        # beyond it, which means the stored extent is stale.
        bbox_stale = False
        rtree = f"rtree_{tabla}_{col_geom}"
        existe = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
            (rtree,),
        ).fetchone()
        if existe:
            fila = con.execute(
                f'SELECT MIN(minx), MIN(miny), MAX(maxx), MAX(maxy) FROM "{rtree}"'
            ).fetchone()
            if fila and fila[0] is not None:
                if None in (min_x, min_y, max_x, max_y):
                    min_x, min_y, max_x, max_y = fila
                    bbox_stale = True
                else:
                    holgura = max(
                        min_x - fila[0], min_y - fila[1], fila[2] - max_x, fila[3] - max_y
                    )
                    if holgura > 1.0:
                        min_x, min_y, max_x, max_y = fila
                        bbox_stale = True

        # Columns with no values at all are forbidden by nomenclatura section 5.
        vacios = []
        for campo in campos:
            if campo["nombre"] == col_geom or campo["pk"]:
                continue
            nulos = con.execute(
                f'SELECT COUNT(*) FROM "{tabla}" '
                f"WHERE \"{campo['nombre']}\" IS NULL OR TRIM(CAST(\"{campo['nombre']}\" AS TEXT)) = ''"
            ).fetchone()[0]
            if registros and nulos == registros:
                vacios.append(campo["nombre"])

        return {
            "tabla": tabla,
            "columna_geom": col_geom,
            "tipo_geometria": tipo_geom,
            "srs_id": srs_id,
            "srs_geom": srs_geom,
            "authid": authid,
            "campos": campos,
            "nombres_campos": [c["nombre"] for c in campos],
            "cantidad_registros": registros,
            "bbox": (min_x, min_y, max_x, max_y),
            "bbox_desactualizado": bbox_stale,
            "campos_vacios": vacios,
        }
    finally:
        con.close()


# --- .qmd (QGIS layer metadata) --------------------------------------------

# QGIS writes DBL_MAX in <extent><spatial> when the layer extent was never
# computed. Any coordinate this large is a placeholder, not real data.
CENTINELA = 1e300


def leer_qmd(ruta):
    """Read the fields we care about from a QGIS .qmd sidecar."""
    raiz = ET.parse(ruta).getroot()

    def texto(etiqueta):
        nodo = raiz.find(etiqueta)
        return (nodo.text or "").strip() if nodo is not None else ""

    palabras = []
    for bloque in raiz.findall("keywords"):
        for kw in bloque.findall("keyword"):
            if kw.text and kw.text.strip():
                palabras.append(kw.text.strip())

    contacto = raiz.find("contact")
    email = organizacion = ""
    if contacto is not None:
        nodo = contacto.find("email")
        email = (nodo.text or "").strip() if nodo is not None else ""
        nodo = contacto.find("organization")
        organizacion = (nodo.text or "").strip() if nodo is not None else ""

    extent_valido = True
    espacial = raiz.find("extent/spatial")
    if espacial is not None:
        for clave in ("minx", "miny", "maxx", "maxy"):
            try:
                if abs(float(espacial.get(clave, 0))) > CENTINELA:
                    extent_valido = False
            except ValueError:
                extent_valido = False
    else:
        extent_valido = False

    autoridad = raiz.find("crs/spatialrefsys/authid")

    return {
        "identifier": texto("identifier"),
        "titulo": texto("title"),
        "abstract": texto("abstract"),
        "licencia": texto("license"),
        "linaje": texto("history"),
        "palabras_clave": palabras,
        "contacto_email": email,
        "organizacion": organizacion,
        "authid": (autoridad.text or "").strip() if autoridad is not None else "",
        "extent_valido": extent_valido,
    }


# --- derived values --------------------------------------------------------


def checksum_sha256(ruta, bloque=1 << 20):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for trozo in iter(lambda: fh.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def fecha_git(ruta):
    """Last commit date of a file (ISO 8601), or its mtime if not in Git."""
    try:
        salida = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(ruta)],
            capture_output=True,
            text=True,
            cwd=str(Path(ruta).parent),
            timeout=15,
        )
        if salida.returncode == 0 and salida.stdout.strip():
            return salida.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    import datetime

    ts = os.path.getmtime(ruta)
    return datetime.datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


# --- reprojection 5344 -> 4326 ---------------------------------------------
# Inverse Transverse Mercator (Snyder, Map Projections: A Working Manual,
# eqs. 3-21 and 8-1..8-8). Only used for bbox corners, never for geometry.

_A = 6378137.0
_F = 1 / 298.257223563
_E2 = _F * (2 - _F)
_LAT0 = math.radians(-90.0)
_LON0 = math.radians(-69.0)
_K0 = 1.0
_X0 = 2500000.0
_Y0 = 0.0


# Coefficient of phi in the meridian arc series, reused to get mu.
_M_LINEAL = 1 - _E2 / 4 - 3 * _E2**2 / 64 - 5 * _E2**3 / 256 - 175 * _E2**4 / 16384


def _arco_meridiano(phi):
    """Meridional arc distance from the equator to phi.

    Carried to e^8. Snyder prints the series to e^6, which is already accurate
    to 0.1 mm over this zone; e^8 brings it to 0.002 mm. Both are far below any
    meaningful threshold - the extra term is kept only because it is free.
    """
    return _A * (
        _M_LINEAL * phi
        - (3 * _E2 / 8 + 3 * _E2**2 / 32 + 45 * _E2**3 / 1024 + 105 * _E2**4 / 4096)
        * math.sin(2 * phi)
        + (15 * _E2**2 / 256 + 45 * _E2**3 / 1024 + 525 * _E2**4 / 16384)
        * math.sin(4 * phi)
        - (35 * _E2**3 / 3072 + 175 * _E2**4 / 12288) * math.sin(6 * phi)
        + (315 * _E2**4 / 131072) * math.sin(8 * phi)
    )


def a_wgs84(este, norte):
    """Project one EPSG:5344 coordinate to (lon, lat) in EPSG:4326."""
    m = _arco_meridiano(_LAT0) + (norte - _Y0) / _K0
    mu = m / (_A * _M_LINEAL)
    e1 = (1 - math.sqrt(1 - _E2)) / (1 + math.sqrt(1 - _E2))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )
    ep2 = _E2 / (1 - _E2)
    c1 = ep2 * math.cos(phi1) ** 2
    t1 = math.tan(phi1) ** 2
    n1 = _A / math.sqrt(1 - _E2 * math.sin(phi1) ** 2)
    r1 = _A * (1 - _E2) / (1 - _E2 * math.sin(phi1) ** 2) ** 1.5
    d = (este - _X0) / (n1 * _K0)

    phi = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lam = _LON0 + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / math.cos(phi1)

    return math.degrees(lam), math.degrees(phi)


def bbox_a_wgs84(bbox):
    """Project a bbox by its four corners and take the envelope."""
    min_x, min_y, max_x, max_y = bbox
    esquinas = [
        a_wgs84(min_x, min_y),
        a_wgs84(min_x, max_y),
        a_wgs84(max_x, min_y),
        a_wgs84(max_x, max_y),
    ]
    lons = [p[0] for p in esquinas]
    lats = [p[1] for p in esquinas]
    return (min(lons), min(lats), max(lons), max(lats))
