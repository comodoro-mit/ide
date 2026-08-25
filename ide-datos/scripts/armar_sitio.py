"""Assemble the folder that gets published, from artifacts already built.

This script copies and indexes; it never converts. Run the pipeline first:

    validar_catalogo.py    refuses to publish data that breaks nomenclatura
    derivar_catalogo.py    writes catalogo_completo.{csv,json}
    generar_derivados.py   writes derivados/<id>.geojson
    armar_sitio.py         <- here

Result:

    sitio/
      index.html                  listing generated from the catalogue
      catalogo.csv, catalogo.json the full catalogue
      datos/<id>.gpkg             the master, for QGIS and ArcGIS
      datos/<id>.geojson          for web viewers and everything else
      metadatos/<id>.qmd          the QGIS metadata sidecar

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
        for nombre in ("index.html", "catalogo.csv", "catalogo.json"):
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
# Provisional: enough to browse and download while the real geoportal is built.

ESTILO = """
:root {
  --tinta: #1a1a1a; --suave: #5c5c5c; --linea: #e0ddd8;
  --fondo: #faf9f7; --tarjeta: #ffffff; --acento: #1c5d78;
}
@media (prefers-color-scheme: dark) {
  :root {
    --tinta: #ececec; --suave: #a0a0a0; --linea: #33312e;
    --fondo: #171614; --tarjeta: #201f1c; --acento: #7fc4e0;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2.5rem 1.25rem 4rem; background: var(--fondo);
  color: var(--tinta); line-height: 1.6;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 60rem; margin: 0 auto; }
h1 { font-size: 1.75rem; margin: 0 0 .25rem; letter-spacing: -.01em; }
.sub { color: var(--suave); margin: 0 0 2.5rem; }
.ficha {
  background: var(--tarjeta); border: 1px solid var(--linea);
  border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
}
.ficha h2 { font-size: 1.1rem; margin: 0 0 .35rem; }
.ficha p { margin: 0 0 .9rem; color: var(--suave); }
dl {
  display: grid; grid-template-columns: auto 1fr; gap: .15rem 1rem;
  margin: 0 0 1rem; font-size: .875rem;
}
dt { color: var(--suave); }
dd { margin: 0; font-variant-numeric: tabular-nums; }
a { color: var(--acento); }
.bajar a {
  display: inline-block; margin-right: .5rem; padding: .35rem .8rem;
  border: 1px solid var(--linea); border-radius: 6px;
  text-decoration: none; font-size: .875rem;
}
.bajar a:hover { border-color: var(--acento); }
.etiqueta {
  font-size: .75rem; text-transform: uppercase; letter-spacing: .04em;
  color: var(--suave); border: 1px solid var(--linea);
  border-radius: 4px; padding: .1rem .4rem;
}
footer {
  margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--linea);
  color: var(--suave); font-size: .875rem;
}
table { width: 100%; border-collapse: collapse; }
.envoltorio { overflow-x: auto; }
"""


def ficha_html(fila):
    def campo(clave):
        return html.escape(str(fila.get(clave, "") or ""))

    did = campo("id")
    descargas = [
        (f"{comun.CARPETA_DATOS}/{did}.gpkg", "GeoPackage"),
        (f"{comun.CARPETA_DATOS}/{did}.geojson", "GeoJSON"),
        (f"{comun.CARPETA_METADATOS}/{did}.xml", "Metadatos ISO"),
    ]
    enlaces = "".join(
        f'<a href="{ruta}" download>{texto}</a>' for ruta, texto in descargas
    )
    return f"""      <article class="ficha">
        <h2>{campo('titulo')} <span class="etiqueta">{campo('tema')}</span></h2>
        <p>{campo('descripcion')}</p>
        <dl>
          <dt>Identificador</dt><dd><code>{did}</code></dd>
          <dt>Registros</dt><dd>{campo('cantidad_registros')}</dd>
          <dt>Geometría</dt><dd>{campo('tipo_geometria')}</dd>
          <dt>Sistema de referencia</dt><dd>{campo('crs')}</dd>
          <dt>Versión</dt><dd>{campo('version')}</dd>
          <dt>Estado</dt><dd>{campo('estado')}</dd>
          <dt>Licencia</dt><dd>{campo('licencia')}</dd>
          <dt>Actualizado</dt><dd>{campo('fecha_modificacion')[:10]}</dd>
        </dl>
        <div class="bajar">{enlaces}</div>
      </article>"""


def escribir_indice(filas, destino):
    fichas = "\n".join(ficha_html(f) for f in filas)
    cantidad = len(filas)
    plural = "conjunto de datos" if cantidad == 1 else "conjuntos de datos"
    documento = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IDE Comodoro Rivadavia — Datos abiertos</title>
<style>{ESTILO}</style>
</head>
<body>
  <main>
    <h1>Infraestructura de Datos Espaciales</h1>
    <p class="sub">
      Municipalidad de Comodoro Rivadavia — {cantidad} {plural} publicados.
      El GeoPackage es el dato autoritativo, en EPSG:{comun.CRS_MAESTRO};
      el GeoJSON se deriva de él en EPSG:{comun.CRS_PUBLICACION} para uso web.
    </p>
{fichas}
    <footer>
      <p>
        Catálogo completo:
        <a href="catalogo.csv">CSV</a> · <a href="catalogo.json">JSON</a>
      </p>
      <p>
        Página provisional generada por <code>armar_sitio.py</code> desde el
        catálogo. No es el geoportal definitivo.
      </p>
    </footer>
  </main>
</body>
</html>
"""
    destino.write_text(documento, encoding="utf-8")


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
        print("[ERROR] falta catalogo_completo.json — correr derivar_catalogo.py")
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
        for origen, relativo in piezas:
            if not origen.exists():
                faltantes.append(f"{did}: falta {origen.name}")
                continue
            tamano = copiar(origen, salida / relativo)
            total += tamano
            if tamano > LIMITE_ARCHIVO:
                grandes.append((relativo, tamano))

    for nombre in ("catalogo_completo.csv", "catalogo_completo.json"):
        origen = raiz / "catalogo" / nombre
        if origen.exists():
            total += copiar(origen, salida / nombre.replace("_completo", ""))

    escribir_indice(filas, salida / "index.html")
    total += (salida / "index.html").stat().st_size

    base = comun.url_base()
    print(f"Sitio armado en {salida}")
    print(f"  {len(filas)} dataset(s), {formato_tamano(total)}")
    print(f"  URL base: {base or '(sin definir — el catálogo omite las URLs)'}")

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
