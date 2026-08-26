"""Validate catalogo.csv and every master dataset it lists.

Checks the rules in propuesta/nomenclatura.md that a machine can check:
id format, theme prefixes, file pairing (.gpkg + .qmd), storage CRS, field
naming and forbidden fields. Standard library only.

Usage:
    py -3 ide-datos/scripts/validar_catalogo.py [--estricto]

Exit code 1 when there is at least one error (or, with --estricto, at least
one warning). Warnings alone do not fail the build.
"""

import argparse
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comun  # noqa: E402


class Reporte:
    def __init__(self):
        self.errores = []
        self.avisos = []

    def error(self, ambito, mensaje):
        self.errores.append((ambito, mensaje))

    def aviso(self, ambito, mensaje):
        self.avisos.append((ambito, mensaje))

    def imprimir(self):
        for ambito, mensaje in self.errores:
            print(f"[ERROR] {ambito}: {mensaje}")
        for ambito, mensaje in self.avisos:
            print(f"[AVISO] {ambito}: {mensaje}")
        print()
        print(f"{len(self.errores)} error(es), {len(self.avisos)} aviso(s)")


def tiene_acentos(texto):
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", texto))


def validar_estructura_csv(filas, columnas, rep):
    faltantes = [c for c in comun.COLUMNAS_MANUALES if c not in columnas]
    if faltantes:
        rep.error("catalogo.csv", f"faltan columnas: {', '.join(faltantes)}")
    extra = [c for c in columnas if c not in comun.COLUMNAS_MANUALES]
    if extra:
        rep.aviso(
            "catalogo.csv",
            f"columnas no previstas (se ignoran al derivar): {', '.join(extra)}",
        )
    if not filas:
        rep.error("catalogo.csv", "no tiene ninguna fila de dataset")

    vistos = {}
    for n, fila in enumerate(filas, start=2):
        did = fila.get("id", "")
        if did in vistos:
            rep.error(f"fila {n}", f"id duplicado '{did}' (ya está en la fila {vistos[did]})")
        vistos[did] = n


def validar_fila(fila, numero, estados, rep):
    """Validate one catalog row against nomenclatura sections 2, 6 and 7."""
    did = fila.get("id", "")
    ambito = f"{did or f'fila {numero}'}"

    for columna in comun.COLUMNAS_MANUALES:
        if columna in comun.COLUMNAS_OPCIONALES:
            continue
        if not fila.get(columna):
            rep.error(ambito, f"campo obligatorio vacío: {columna}")

    if not did:
        return None

    # Section 2: id format and length.
    if not comun.RE_ID.match(did):
        rep.error(
            ambito,
            "el id no cumple cr-<tema>-<entidad>[-<calificador>] con un tema válido "
            f"({', '.join(sorted(comun.TEMAS))})",
        )
        return None
    if len(did) > comun.LARGO_MAX_ID:
        rep.error(ambito, f"el id tiene {len(did)} caracteres (máximo {comun.LARGO_MAX_ID})")

    tema = comun.tema_de(did)
    categoria = fila.get("categoria", "")
    if categoria and categoria != tema:
        rep.error(
            ambito,
            f"categoria '{categoria}' no coincide con el tema '{tema}' del id",
        )

    estado = fila.get("estado", "")
    if estado and estado not in estados:
        rep.aviso(
            ambito,
            f"estado '{estado}' fuera del vocabulario ({', '.join(estados)}) - "
            "corregir la fila o agregarlo a catalogo/vocabularios/estados.csv",
        )

    version = fila.get("version", "")
    if version and not comun.RE_SEMVER.match(version):
        rep.aviso(
            ambito,
            f"version '{version}' no es SemVer MAJOR.MINOR.PATCH (¿'{version}.0.0'?)",
        )

    frecuencia = fila.get("frecuencia_actualizacion", "")
    if not frecuencia:
        rep.aviso(
            ambito,
            "sin frecuencia_actualizacion: es el elemento A8 del perfil IDERA y "
            "es obligatorio para publicar el metadato ISO 19139",
        )
    elif frecuencia not in comun.FRECUENCIAS:
        rep.aviso(
            ambito,
            f"frecuencia_actualizacion '{frecuencia}' no es un valor de "
            f"MD_MaintenanceFrequencyCode ({', '.join(comun.FRECUENCIAS)})",
        )

    responsable = fila.get("responsable", "")
    if responsable and (
        responsable != responsable.lower() or tiene_acentos(responsable)
    ):
        rep.aviso(ambito, f"responsable '{responsable}': se espera minúsculas sin tildes")

    descripcion = fila.get("descripcion", "")
    if descripcion and len(descripcion) < 200:
        rep.aviso(
            ambito,
            f"descripcion de {len(descripcion)} caracteres; la ficha institucional "
            "pide un mínimo de 200 para que sirva como metadato publicable",
        )

    return tema


def validar_gpkg(did, ruta, rep):
    ambito = f"{did}.gpkg"
    try:
        info = comun.leer_gpkg(ruta)
    except Exception as exc:  # noqa: BLE001 - report, do not crash the run
        rep.error(ambito, f"no se pudo leer como GeoPackage: {exc}")
        return None

    esperado = comun.nombre_capa(did)
    if info["tabla"] != esperado:
        rep.error(
            ambito,
            f"la capa se llama '{info['tabla']}' y debería llamarse '{esperado}'",
        )

    if info["srs_id"] != comun.CRS_MAESTRO:
        rep.error(
            ambito,
            f"CRS EPSG:{info['srs_id']}; el maestro se almacena en "
            f"EPSG:{comun.CRS_MAESTRO}",
        )

    if info["cantidad_registros"] == 0:
        rep.error(ambito, "la capa no tiene registros")

    nombres = set(info["nombres_campos"])
    if "id" not in nombres:
        rep.error(ambito, "falta el campo obligatorio 'id'")
    if info["columna_geom"] not in nombres:
        rep.error(ambito, f"falta la columna de geometría '{info['columna_geom']}'")

    for campo in info["campos"]:
        nombre = campo["nombre"]
        if nombre == info["columna_geom"]:
            continue
        if nombre.lower() in comun.CAMPOS_PROHIBIDOS and nombre.lower() != "id":
            rep.error(
                ambito,
                f"campo prohibido '{nombre}' (nomenclatura §5: no duplicar 'id' "
                "ni arrastrar campos de shapefile/ArcGIS)",
            )
            continue
        if not comun.RE_CAMPO.match(nombre):
            rep.error(
                ambito,
                f"campo '{nombre}': se espera snake_case sin mayúsculas, tildes ni espacios",
            )
        if len(nombre) > comun.LARGO_MAX_CAMPO:
            rep.error(
                ambito,
                f"campo '{nombre}' tiene {len(nombre)} caracteres "
                f"(máximo {comun.LARGO_MAX_CAMPO})",
            )

    if info["bbox_desactualizado"]:
        rep.aviso(
            ambito,
            "la extensión guardada en gpkg_contents no coincide con la geometría; "
            "se usó el índice espacial. Volver a guardar la capa desde QGIS",
        )

    for nombre in info["campos_vacios"]:
        rep.aviso(ambito, f"campo '{nombre}' está vacío en los {info['cantidad_registros']} registros")

    return info


def validar_qmd(did, ruta, rep):
    ambito = f"{did}.qmd"
    try:
        meta = comun.leer_qmd(ruta)
    except Exception as exc:  # noqa: BLE001
        rep.error(ambito, f"no se pudo leer como XML de metadatos QGIS: {exc}")
        return None

    if meta["identifier"] != did:
        rep.error(
            ambito,
            f"<identifier> es '{meta['identifier']}' y debería ser '{did}'",
        )
    for etiqueta, clave in (("title", "titulo"), ("abstract", "abstract"), ("license", "licencia")):
        if not meta[clave]:
            rep.error(ambito, f"<{etiqueta}> vacío")
    if not meta["palabras_clave"]:
        rep.aviso(ambito, "sin palabras clave")
    if not meta["linaje"]:
        rep.aviso(ambito, "<history> vacío: el linaje del dato no está documentado")
    if not meta["extent_valido"]:
        rep.aviso(
            ambito,
            "el <extent> no fue calculado por QGIS (guarda un valor centinela). "
            "En QGIS: Propiedades de la capa > Metadatos > Extensión > "
            "'Establecer desde la capa', y volver a guardar el .qmd",
        )
    if meta["authid"] and meta["authid"] != f"EPSG:{comun.CRS_MAESTRO}":
        rep.aviso(ambito, f"CRS declarado {meta['authid']}, se esperaba EPSG:{comun.CRS_MAESTRO}")
    return meta


def validar_huerfanos(ids_catalogo, rep):
    """Flag .gpkg files sitting in maestros/ that no catalog row declares."""
    maestros = comun.raiz_datos() / "maestros"
    if not maestros.exists():
        return
    for ruta in sorted(maestros.rglob("*.gpkg")):
        did = ruta.stem
        if did not in ids_catalogo:
            rep.error(
                "maestros/",
                f"'{ruta.relative_to(comun.raiz_datos())}' no tiene fila en catalogo.csv",
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--estricto",
        action="store_true",
        help="tratar los avisos como errores (salida distinta de cero)",
    )
    parser.add_argument("--catalogo", help="ruta alternativa a catalogo.csv")
    args = parser.parse_args()

    rep = Reporte()
    ruta = Path(args.catalogo) if args.catalogo else comun.ruta_catalogo()
    if not ruta.exists():
        print(f"[ERROR] no existe {ruta}")
        return 1

    filas, columnas = comun.leer_catalogo(ruta)
    estados = comun.leer_vocabulario("estados", comun.ESTADOS)

    validar_estructura_csv(filas, columnas, rep)

    ids = set()
    for numero, fila in enumerate(filas, start=2):
        tema = validar_fila(fila, numero, estados, rep)
        if not tema:
            continue
        did = fila["id"]
        ids.add(did)

        gpkg = comun.ruta_maestro(did, tema, "gpkg")
        qmd = comun.ruta_maestro(did, tema, "qmd")

        if not gpkg.exists():
            rep.error(did, f"no existe el maestro {gpkg.relative_to(comun.raiz_datos())}")
        else:
            validar_gpkg(did, gpkg, rep)

        if not qmd.exists():
            rep.error(did, f"no existe el metadato {qmd.relative_to(comun.raiz_datos())}")
        else:
            validar_qmd(did, qmd, rep)

    validar_huerfanos(ids, rep)

    print(f"Validando {ruta}")
    print(f"{len(filas)} dataset(s) declarado(s)")
    print()
    rep.imprimir()

    if rep.errores:
        return 1
    if args.estricto and rep.avisos:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
