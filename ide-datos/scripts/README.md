# scripts/

Automatización del ciclo de vida de los datos maestros.

**Sin dependencias externas.** Un GeoPackage es un archivo SQLite, así que
`sqlite3` de la biblioteca estándar alcanza para leer estructura, extensión,
registros y geometría. Solo `generar_derivados.py` sabe aprovechar GDAL si está,
pero no lo necesita.

```
py -3 ide-datos\scripts\validar_catalogo.py
py -3 ide-datos\scripts\derivar_catalogo.py
py -3 ide-datos\scripts\generar_derivados.py
py -3 ide-datos\scripts\creador_metadata.py
py -3 ide-datos\scripts\armar_sitio.py
```

Ese es el orden: cada uno consume lo que dejó el anterior.

| Script | Entrada | Salida |
|---|---|---|
| `comun.py` | — | Módulo compartido: constantes, lectura `.gpkg`/`.qmd`, checksum, reproyección |
| `validar_catalogo.py` | `catalogo.csv` + maestros | Reporte y código de salida |
| `derivar_catalogo.py` | `catalogo.csv` + maestros | `catalogo/catalogo_completo.{csv,json}` |
| `generar_derivados.py` | maestros | `derivados/<id>.geojson` en EPSG:4326 |
| `creador_metadata.py` | catálogo derivado + `.qmd` | `derivados/iso19139/<id>.xml` |
| `armar_sitio.py` | todo lo anterior | `sitio/`, la carpeta que se publica |

## validar_catalogo.py

Chequea lo que una máquina puede chequear de `nomenclatura.md`: formato del
`id` y tema válido (§2), pareja `.gpkg` + `.qmd`, capa única con CRS 5344,
nombres de campo y campos prohibidos (§5), coherencia del `.qmd`, y `.gpkg`
huérfanos sin fila en el catálogo.

Distingue **errores** (frenan el CI) de **avisos** (no lo frenan). `--estricto`
hace que los avisos también frenen.

## derivar_catalogo.py

Mergea las 8 columnas manuales con 21 leídas del `.gpkg` y del `.qmd`, para que
nadie tipee dos veces un CRS ni una cantidad de registros.

- **Manuales** (`catalogo.csv`, se commitea): `id`, `titulo`, `descripcion`,
  `responsable`, `estado`, `categoria`, `version`, `notas_internas`.
- **Derivadas**: `tema`, `categoria_iso`, `crs`, `tipo_geometria`,
  `cantidad_registros`, `cantidad_campos`, `campos`, `bbox_5344`, `bbox_4326`,
  `licencia`, `palabras_clave`, `linaje`, `contacto_email`, `organizacion`,
  `titulo_metadato`, `resumen_metadato`, `archivo_gpkg`, `archivo_qmd`,
  `tamano_bytes`, `checksum_sha256`, `fecha_modificacion`, `url_descarga`,
  `url_descarga_geojson`, `url_metadatos`.

`catalogo_completo.csv` y `.json` son derivados: están en `.gitignore` y se
regeneran en cada corrida. No editarlos a mano.

## generar_derivados.py

GeoJSON en EPSG:4326, que RFC 7946 exige. El maestro se queda en 5344; la
reproyección pasa solo acá.

Dos motores intercambiables, `--motor auto|ogr2ogr|python`:

- **ogr2ogr** si está en el PATH (viene con QGIS, y CI instala `gdal-bin`).
- **python**, con `sqlite3` + decodificación de WKB + `comun.a_wgs84()`.

Los dos producen **archivos idénticos**, verificado vértice por vértice sobre
los 2558 de la capa de barrios. Eso no salió gratis: hubo que resolver dos
divergencias.

### Divergencia 1: la transformación de datum

Pedirle a PROJ que vaya de `EPSG:5344` a `EPSG:4326` hace que inserte la
transformación registrada *POSGAR 2007 to WGS 84 (2)*, que **corre cada
coordenada unos 0,66 m al norte y 0,20 m al este, declarando una exactitud
propia de 0,5 m**: mueve más de lo que promete corregir.

POSGAR 2007 usa el elipsoide WGS 84 y ambas realizaciones son ITRF, así que
tratarlas como equivalentes es la práctica habitual para publicación web.
`comun.PROJ4_MAESTRO` declara la misma proyección sin datum y se pasa como
`-s_srs`, de modo que PROJ no inserta nada y los dos motores coinciden.

> Si el IGN alguna vez pide la transformación registrada, hay que aplicarla en
> **los dos** motores, nunca en uno solo.

### Divergencia 2: la orientación de los anillos

RFC 7946 §3.1.6 pide anillo exterior antihorario y huecos horarios. `ogr2ogr`
lo hace con `RFC7946=YES`; la ruta en Python no. En vez de duplicar la regla,
**los dos motores terminan en la misma función** `escribir_coleccion()`, que
ordena los anillos y serializa el JSON. La salida de `ogr2ogr` se vuelve a
emitir por ahí.

### Precisión

7 decimales, aproximadamente 1 cm, según recomienda RFC 7946 §11.2. Más es
ruido. La Transversa de Mercator inversa de `comun.a_wgs84()` (Snyder, ecs.
3-21 y 8-1..8-8, llevada a e⁸) coincide con PROJ **a 0,002 mm**.

## creador_metadata.py

Genera el XML **ISO 19139** que exige el
[Perfil de Metadatos para Datos Vectoriales v2.0 de IDERA](https://www.idera.gob.ar/index.php/recursos/perfil-de-metadatos).
El perfil define 26 elementos, **17 obligatorios**. El script los arma desde el
catálogo derivado y el `.qmd`; lo que no tiene origen no se inventa, se informa
como hueco de cumplimiento:

```
cr-adm-limites-barrios.xml: completo, 17/17 obligatorios de IDERA
```

Con `--estricto` sale con error si falta alguno.

Reemplaza al script homónimo del repo viejo, que escribía
`topiccategory: boundaries` fijo para toda capa, `geomtype: unknown`, un bbox
fijo del ejido, y definía `CRS_EPSG` sin llegar a escribirla nunca.

### De dónde sale cada obligatorio

| | Elemento | Origen |
|---|---|---|
| A1 | Título | catálogo |
| A2 / A2.1 | Fecha de referencia y tipo | `fecha_modificacion`, que sale de Git |
| A4 | Resumen | `<abstract>` del `.qmd` |
| A6 / A7 | Contactos | `<contact>` del `.qmd` |
| A8 | Frecuencia de mantenimiento | **columna `frecuencia_actualizacion`** |
| A9 | Tema | `categoria_iso`, derivado del prefijo |
| A10 | Palabras clave | `<keywords>` del `.qmd` |
| A11 | Restricciones | `<license>` del `.qmd` |
| A12 | Tipo de representación | fijo: `vector` |
| A14 / A15 | Idioma y charset | fijos: `spa`, `utf8` |
| B1 | Proyección | `crs`, leído del GeoPackage |
| C1 | Enlace de descarga | `url_descarga`, **requiere `url_base`** |
| E1 / E6 | Identificador y fecha del metadato | `id` y la fecha de corrida |

Dos de esos no salían de ningún lado y hubo que resolverlos:

- **A8** no existe en el esquema `.qmd` de QGIS, así que va como columna del
  catálogo. No es una columna inventada: la pide el perfil.
- **C1** depende de `url_base`. Mientras esté sin definir, el XML se genera
  igual pero le falta ese elemento y no está listo para cosecha.

Sobre el idioma: el `.qmd` guarda `<language>ARG</language>`, que es un código
de país, no de idioma. El XML escribe `spa`, que es lo que corresponde.

`url_metadatos` del catálogo apunta al **`.xml`**, no al `.qmd`: es la URL que
sigue un cosechador de catálogos. El `.qmd` se publica igual, pero es el
archivo de trabajo de QGIS, no un formato de intercambio.

## armar_sitio.py

Copia e indexa; nunca convierte. Produce una carpeta estática:

```
sitio/
  index.html            la plantilla del geoportal, rellenada
  estilos.css, app.js   copiados de ide-visores/geoportal/
  catalogo.csv, .json   el catálogo completo
  datos/<id>.gpkg       el maestro, para QGIS y ArcGIS
  datos/<id>.geojson    para visores web y todo lo demás
  metadatos/<id>.xml     ISO 19139, el metadato interoperable
  metadatos/<id>.qmd     el archivo de trabajo de QGIS
```

Se publican **los dos formatos a propósito**. El GeoPackage es el dato
autoritativo: un archivo, con CRS y tipos declarados, es lo que un usuario de
QGIS quiere bajar. El GeoJSON es lo que consume cualquier cosa en la web y ya
se genera igual para los visores. Ninguno de los dos cuesta trabajo extra, así
que no publicarlos sería una decisión, no un ahorro.

Avisa si algún archivo pasa los 25 MiB (Cloudflare Pages los rechaza en el plan
gratuito y hay que ir a R2) o si el sitio entero pasa 1 GB (tope de GitHub
Pages).

Es agnóstico del host: una carpeta estática es todo lo que piden los dos.

### La página la escribe el geoportal, no este script

El HTML, el CSS y el JS viven en `ide-visores/geoportal/` como archivos
normales. `armar_sitio.py` solo rellena la plantilla: reemplaza todo lo que hay
entre `<!--{{FICHAS_INICIO}}-->` y `<!--{{FICHAS_FIN}}-->` por una ficha por
dataset, y sustituye `{{CANTIDAD}}`, `{{PLURAL}}` y `{{FECHA}}`.

Dos consecuencias que conviene mantener:

- El listado queda **escrito dentro del HTML** al publicar, no lo arma
  JavaScript. El sitio funciona con JS deshabilitado y los buscadores lo
  indexan. `app.js` solo agrega búsqueda encima de fichas que ya están.
- El diseño se edita como un archivo que se abre en el navegador, no como un
  string dentro de Python. La plantilla trae una ficha de ejemplo entre los
  marcadores justamente para eso: se ve el estilo sin correr el pipeline, y en
  el sitio publicado desaparece.

### La URL base

`ide-datos/config.json` tiene `url_base`, vacía por defecto. Mientras lo esté,
`derivar_catalogo.py` deja `url_descarga`, `url_descarga_geojson` y
`url_metadatos` en blanco en vez de inventar un dominio que después quedaría
circulando dentro de metadatos publicados. La variable de entorno
`IDE_URL_BASE` tiene prioridad, para que CI la defina por despliegue.

## Exportar un maestro desde QGIS: la opción FID

Al exportar a GeoPackage, la opción **FID** define el nombre de la clave
primaria. Por defecto es `fid`, que `nomenclatura.md` §5 prohíbe. Poniendo
**`FID` = `id`** la clave pasa a llamarse `id`:

```sql
CREATE TABLE "cr_adm_limites_barrios" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "geom" MULTIPOLYGON, ...
)
```

Si el origen ya traía un campo `fid`, queda como atributo común. QGIS no lo
deja borrar mientras siga siendo la clave primaria, pero una vez que `id` lo
es, sale sin problema desde Propiedades de la capa > Campos. Si quedó,
`validar_catalogo.py` lo reporta como error.

## Vocabularios

`validar_catalogo.py` lee `catalogo/vocabularios/estados.csv` si existe, y si
no usa los cinco valores de `nomenclatura.md` §7. El comité técnico cambia el
vocabulario sin tocar código.
