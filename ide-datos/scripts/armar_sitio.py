"""Assemble the folder that gets published, from artifacts already built.

This script copies and indexes; it never converts. Run the pipeline first:

    validar_catalogo.py    refuses to publish data that breaks nomenclatura
    derivar_catalogo.py    writes catalogo_completo.{csv,json}
    generar_derivados.py   writes derivados/<id>.geojson
    armar_sitio.py         <- here

Result:

    sitio/
      index.html y las subpaginas the geoportal templates, filled in
      estilos.css, app.js         copied from ide-visores/geoportal/
      img/*.png                   logo and favicon, same origin
      catalogo.csv, catalogo.json the full catalogue
      datos/<id>.gpkg             the master, for QGIS and ArcGIS
      datos/<id>.geojson          for web viewers and everything else
      metadatos/<id>.xml          ISO 19139, the interoperable metadata
      metadatos/<id>.qmd          the QGIS working file

Deliberately host-agnostic: it produces a plain static folder, which is all
GitHub Pages and Cloudflare Pages both want.

Usage:
    py -3 ide-datos/scripts/armar_sitio.py [--salida sitio/]
"""

import argparse
import html
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comun  # noqa: E402

# Cloudflare Pages rejects individual files over 25 MiB on the free plan and
# points at R2 instead. Warn early rather than at deploy time.
LIMITE_ARCHIVO = 25 * 1024 * 1024
# GitHub Pages caps the whole published site at 1 GB.
LIMITE_SITIO = 1024 * 1024 * 1024


def formato_tamano(unidades):
    for sufijo in ("B", "KB", "MB", "GB"):
        if unidades < 1024 or sufijo == "GB":
            return f"{unidades:.0f} {sufijo}" if sufijo != "GB" else f"{unidades:.1f} GB"
        unidades /= 1024
    return f"{unidades:.1f} GB"


def limpiar(salida):
    """Remove only what this script writes.

    --salida comes from the command line, so an unconditional rmtree of it is a
    footgun: one careless `--salida .` and the repository is gone. Deleting the
    known outputs instead is enough to get a clean build and cannot destroy
    anything the script did not create.
    """
    if not salida.exists():
        return
    try:
        for nombre in (comun.CARPETA_DATOS, comun.CARPETA_METADATOS):
            carpeta = salida / nombre
            if carpeta.is_dir():
                shutil.rmtree(carpeta)
        paginas = tuple(p.name for p in paginas_geoportal())
        sueltos = paginas + ("catalogo.csv", "catalogo.json") + ARCHIVOS_GEOPORTAL
        for nombre in sueltos:
            archivo = salida / nombre
            if archivo.is_file():
                archivo.unlink()
    except PermissionError as exc:
        # Some environments allow writing but not deleting. Everything gets
        # overwritten anyway; the only cost is that files from a dataset that
        # was removed from the catalogue survive. Worth a warning, not a crash.
        print(f"[AVISO] no se pudo limpiar {salida}: {exc}")
        print("        se sobrescribe, pero pueden quedar archivos de corridas viejas")


def copiar(origen, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)
    return destino.stat().st_size


# --- index page ------------------------------------------------------------
# The page itself lives in ide-visores/geoportal/ as ordinary HTML, CSS and JS,
# edited by hand. This script only fills it in. Two consequences worth keeping:
# the listing is written into the HTML at publish time, so the site works with
# JavaScript disabled and search engines can index it; and the design is edited
# as a real file that opens in a browser, not as a string inside Python.

# Header and footer live in geoportal/partes/ so every future subpage can
# reuse them: edit the partial, not each page.
PARTES = {
    "<!--{{ENCABEZADO}}-->": "header.html",
    "<!--{{PIE}}-->": "footer.html",
}

MARCA_INICIO = "<!--{{FICHAS_INICIO}}-->"
MARCA_FIN = "<!--{{FICHAS_FIN}}-->"
ARCHIVOS_GEOPORTAL = (
    "estilos.css",
    "app.js",
    "visor.js",
    "img/logotipo.png",
    "img/logotipo_icono.png",
    "img/hero_background.png",
)


def ruta_geoportal():
    return comun.raiz_datos().parent / "ide-visores" / "geoportal"


def ficha_html(fila):
    def campo(clave):
        return html.escape(str(fila.get(clave, "") or ""))

    did = campo("id")
    descargas = [
        (f"{comun.CARPETA_DATOS}/{did}.gpkg", "GeoPackage", True),
        (f"{comun.CARPETA_DATOS}/{did}.geojson", "GeoJSON", True),
        (f"{comun.CARPETA_METADATOS}/{did}.xml", "Metadatos ISO", False),
    ]
    enlaces = "\n        ".join(
        f'<a href="{ruta}"{" download" if bajar else ""}'
        f' target="_blank" rel="noopener">{texto}</a>'
        for ruta, texto, bajar in descargas
    )

    tema = fila.get("tema", "")
    nombre_tema = html.escape(comun.NOMBRES_TEMA.get(tema, ""))

    return f"""    <article class="ficha" data-tema="{html.escape(tema)}">
      <span class="etiqueta">{nombre_tema}</span>
      <h2><span class="titulo">{campo('titulo')}</span></h2>
      <p class="descripcion">{campo('descripcion')}</p>
      <dl>
        <dt>Tema</dt><dd>{nombre_tema}</dd>
        <dt>Identificador</dt><dd><code>{did}</code></dd>
        <dt>Registros</dt><dd>{campo('cantidad_registros')}</dd>
        <dt>Geometría</dt><dd>{campo('tipo_geometria')}</dd>
        <dt>Actualizado</dt><dd>{campo('fecha_modificacion')[:10]}</dd>
      </dl>
      <details class="mas">
        <summary>Ver detalles</summary>
        <dl>
          <dt>Sistema de referencia</dt><dd>{campo('crs')}</dd>
          <dt>Versión</dt><dd>{campo('version')}</dd>
          <dt>Licencia</dt><dd>{campo('licencia')}</dd>
        </dl>
      </details>
      <div class="descargas">
        {enlaces}
      </div>
    </article>"""


def filtros_html(filas):
    """Theme chips, built from the catalogue: never a chip without datasets."""
    if not filas:
        return ""
    conteo = {}
    for fila in filas:
        tema = fila.get("tema", "")
        conteo[tema] = conteo.get(tema, 0) + 1

    botones = [
        '        <button type="button" class="chip" data-tema="" '
        f'aria-pressed="true">Todos <span class="cuenta">{len(filas)}</span></button>'
    ]
    # Alphabetical by label, so the order does not shift as data is added.
    for tema in sorted(conteo, key=lambda t: comun.NOMBRES_TEMA.get(t, t)):
        etiqueta = html.escape(comun.NOMBRES_TEMA.get(tema, tema))
        botones.append(
            f'        <button type="button" class="chip" data-tema="{html.escape(tema)}" '
            f'aria-pressed="false">{etiqueta} <span class="cuenta">{conteo[tema]}</span></button>'
        )
    return (
        '      <nav class="filtros" id="filtros" aria-label="Filtrar por tema" hidden>\n'
        + "\n".join(botones)
        + "\n      </nav>"
    )


# Panel order inside a theme: points first, then lines, then polygons. Small
# geometries sit on top of large ones on the map, so this puts the switches in
# the same order as what the eye finds: a point is easy to lose under a
# polygon, and the user reaches for it first.
ORDEN_GEOMETRIA = ("POINT", "LINESTRING", "POLYGON")


def rango_geometria(tipo):
    """Where a geometry type sits in the panel. Unknown types go last."""
    tipo = str(tipo or "").upper()
    for posicion, familia in enumerate(ORDEN_GEOMETRIA):
        # MULTIPOINT ranks with POINT, MULTIPOLYGON with POLYGON, and so on.
        if familia in tipo:
            return posicion
    return len(ORDEN_GEOMETRIA)


def clave_panel(fila):
    """Sort key for the panel: geometry family first, then title."""
    return (rango_geometria(fila.get("tipo_geometria")), str(fila.get("titulo", "")))


def capas_html(filas):
    """Layer switches for the viewer, one per published dataset."""
    if not filas:
        return '      <p class="nota-visor">Todavía no hay capas publicadas.</p>'

    grupos = {}
    for fila in filas:
        grupos.setdefault(fila.get("tema", ""), []).append(fila)

    bloques = []
    for tema in sorted(grupos, key=lambda t: comun.NOMBRES_TEMA.get(t, t)):
        bloques.append(
            f'        <li class="grupo">{html.escape(comun.NOMBRES_TEMA.get(tema, tema))}</li>'
        )
        for fila in sorted(grupos[tema], key=clave_panel):
            did = html.escape(str(fila.get("id", "")))
            bloques.append(
                f'        <li class="capa">\n'
                f'          <label>\n'
                f'            <input type="checkbox" value="{did}"\n'
                f'                   data-geojson="{comun.CARPETA_DATOS}/{did}.geojson">\n'
                f'            <span>{html.escape(str(fila.get("titulo", "")))}</span>\n'
                f'          </label>\n'
                f'        </li>'
            )
    return '      <ul class="capas">\n' + "\n".join(bloques) + "\n      </ul>"


def paginas_geoportal():
    """Every .html at the root of geoportal/. Partials live in partes/."""
    return sorted(ruta_geoportal().glob("*.html"))


def armar_pagina(plantilla, filas, fecha):
    """Assemble one page: partials, current tab, cards and placeholders."""
    documento = plantilla.read_text(encoding="utf-8")

    for marca, archivo in PARTES.items():
        if marca not in documento:
            continue
        parte = ruta_geoportal() / "partes" / archivo
        if not parte.exists():
            raise FileNotFoundError(f"falta la parte {parte}")
        documento = documento.replace(marca, parte.read_text(encoding="utf-8").strip())

    # The header is shared, so the active tab cannot be written into it. It is
    # marked here, once per page, by matching the link to the file being built.
    enlace = f'<a href="{plantilla.name}"'
    documento = documento.replace(enlace, enlace + ' aria-current="page"', 1)

    # Cards go wherever the markers are. Today that is index.html; moving the
    # catalogue to datasets.html means moving the marker block, nothing else.
    if MARCA_INICIO in documento:
        if MARCA_FIN not in documento:
            raise ValueError(f"{plantilla.name}: falta el marcador {MARCA_FIN}")
        inicio = documento.index(MARCA_INICIO) + len(MARCA_INICIO)
        fin = documento.index(MARCA_FIN)
        fichas = "\n".join(ficha_html(f) for f in filas)
        documento = documento[:inicio] + "\n" + fichas + "\n" + documento[fin:]

    documento = documento.replace("<!--{{FILTROS}}-->", filtros_html(filas))
    documento = documento.replace("<!--{{CAPAS}}-->", capas_html(filas))
    documento = documento.replace("{{CANTIDAD}}", str(len(filas)))
    documento = documento.replace("{{FECHA}}", fecha)
    return documento


def escribir_paginas(filas, salida, fecha):
    """Build every page of the geoportal and copy its static assets."""
    plantillas = paginas_geoportal()
    if not plantillas:
        raise FileNotFoundError(
            f"no hay ninguna plantilla en {ruta_geoportal()}. El geoportal vive "
            "en ide-visores/geoportal/, no en este script."
        )

    total = 0
    for plantilla in plantillas:
        destino = salida / plantilla.name
        destino.write_text(armar_pagina(plantilla, filas, fecha), encoding="utf-8")
        total += destino.stat().st_size

    for nombre in ARCHIVOS_GEOPORTAL:
        origen = ruta_geoportal() / nombre
        if origen.exists():
            total += copiar(origen, salida / nombre)
    return total, [p.name for p in plantillas]


# --- driver ----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", help="directorio del sitio (por defecto sitio/)")
    args = parser.parse_args()

    raiz = comun.raiz_datos()
    salida = Path(args.salida) if args.salida else raiz.parent / "sitio"
    limpiar(salida)
    salida.mkdir(parents=True, exist_ok=True)

    catalogo_json = raiz / "catalogo" / "catalogo_completo.json"
    if not catalogo_json.exists():
        print("[ERROR] falta catalogo_completo.json - correr derivar_catalogo.py")
        return 1

    with open(catalogo_json, encoding="utf-8") as fh:
        filas = json.load(fh)

    total = 0
    grandes = []
    faltantes = []

    for fila in filas:
        did = fila["id"]
        tema = comun.tema_de(did)
        piezas = [
            (comun.ruta_maestro(did, tema, "gpkg"), f"{comun.CARPETA_DATOS}/{did}.gpkg"),
            (comun.ruta_maestro(did, tema, "qmd"), f"{comun.CARPETA_METADATOS}/{did}.qmd"),
            (raiz / "derivados" / f"{did}.geojson", f"{comun.CARPETA_DATOS}/{did}.geojson"),
            (
                raiz / "derivados" / "iso19139" / f"{did}.xml",
                f"{comun.CARPETA_METADATOS}/{did}.xml",
            ),
        ]
        # Cada pieza faltante nombra el script que la produce: el mensaje
        # aparece en un log de CI, donde no hay nadie para deducirlo.
        productor = {
            ".gpkg": "es el maestro, tiene que estar en maestros/",
            ".qmd": "es el sidecar del maestro, tiene que estar en maestros/",
            ".geojson": "lo genera generar_derivados.py",
            ".xml": "lo genera creador_metadata.py",
        }
        for origen, relativo in piezas:
            if not origen.exists():
                pista = productor.get(origen.suffix, "")
                faltantes.append(
                    f"{did}: falta {origen.name}" + (f" - {pista}" if pista else "")
                )
                continue
            tamano = copiar(origen, salida / relativo)
            total += tamano
            if tamano > LIMITE_ARCHIVO:
                grandes.append((relativo, tamano))

    for nombre in ("catalogo_completo.csv", "catalogo_completo.json"):
        origen = raiz / "catalogo" / nombre
        if origen.exists():
            total += copiar(origen, salida / nombre.replace("_completo", ""))

    import datetime

    try:
        peso, paginas = escribir_paginas(
            filas, salida, datetime.date.today().isoformat()
        )
        total += peso
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    base = comun.url_base()
    print(f"Sitio armado en {salida}")
    print(f"  {len(filas)} dataset(s), {formato_tamano(total)}")
    print(f"  {len(paginas)} pagina(s): {', '.join(paginas)}")
    print(f"  URL base: {base or '(sin definir - el catálogo omite las URLs)'}")

    for fallo in faltantes:
        print(f"[ERROR] {fallo}")

    for relativo, tamano in grandes:
        print(
            f"[AVISO] {relativo} pesa {formato_tamano(tamano)}: Cloudflare Pages "
            "rechaza archivos de más de 25 MiB en el plan gratuito, hay que "
            "servirlo desde R2"
        )
    if total > LIMITE_SITIO:
        print(
            f"[AVISO] el sitio pesa {formato_tamano(total)}: GitHub Pages limita "
            "el sitio publicado a 1 GB"
        )

    return 1 if faltantes else 0


if __name__ == "__main__":
    sys.exit(main())
