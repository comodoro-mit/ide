# scripts/

Automatización del ciclo de vida de los datos maestros. **Sin dependencias
externas**: un GeoPackage es un archivo SQLite, así que `sqlite3` de la
biblioteca estándar alcanza para leer estructura, extensión y cantidad de
registros. No hace falta instalar GDAL ni geopandas para validar ni para
derivar el catálogo.

## Cómo correrlos

Desde la raíz del repositorio, en Windows:

```
py -3 ide-datos\scripts\validar_catalogo.py
py -3 ide-datos\scripts\derivar_catalogo.py
```

En Linux/CI:

```
python ide-datos/scripts/validar_catalogo.py
python ide-datos/scripts/derivar_catalogo.py
```

## Qué hace cada uno

| Script | Entrada | Salida | Estado |
|---|---|---|---|
| `comun.py` | — | — | Listo. Módulo compartido: constantes de `nomenclatura.md`, lectura de `.gpkg` y `.qmd`, checksum, reproyección 5344→4326. |
| `validar_catalogo.py` | `catalogo.csv` + maestros | Reporte por consola, código de salida | Listo |
| `derivar_catalogo.py` | `catalogo.csv` + maestros | `catalogo/catalogo_completo.{csv,json}` | Listo |
| `generar_derivados.py` | maestros | GeoJSON 4326, PMTiles | **Pendiente** |
| `creador_metadata.py` | `.qmd` + derivados | ISO 19139 XML para cosecha CSW | **Pendiente** |

## validar_catalogo.py

Chequea lo que una máquina puede chequear de `propuesta/nomenclatura.md`:

- **Catálogo**: columnas presentes, campos obligatorios no vacíos, `id` sin
  duplicar.
- **ID** (§2): formato `cr-<tema>-<entidad>[-<calificador>]`, tema entre los 14
  válidos, máximo 50 caracteres, coincidencia con la columna `categoria`.
- **Pareja de archivos**: existe `maestros/<tema>/<id>.gpkg` y su `.qmd` sidecar.
- **GeoPackage**: una sola capa vectorial, nombre `cr_<id>` con guiones bajos,
  CRS EPSG:5344, al menos un registro.
- **Campos** (§5): `snake_case` sin tildes ni mayúsculas, máximo 30 caracteres,
  `id` obligatorio, prohibidos `fid` / `OBJECTID` / `Shape_Area`.
- **Metadato `.qmd`**: `<identifier>` igual al `id`, título, resumen y licencia
  no vacíos, extensión efectivamente calculada por QGIS.
- **Huérfanos**: `.gpkg` en `maestros/` que ninguna fila del catálogo declara.

Distingue **errores** (frenan el CI) de **avisos** (no lo frenan). Con
`--estricto` los avisos también frenan.

## derivar_catalogo.py

Mergea las 8 columnas que el equipo mantiene a mano con 21 columnas que se
leen del `.gpkg` y del `.qmd`. Nadie tipea dos veces un CRS ni una cantidad de
registros.

**Manuales** (`catalogo.csv`, se commitea): `id`, `titulo`, `descripcion`,
`responsable`, `estado`, `categoria`, `version`, `notas_internas`.

**Derivadas** (nunca a mano): `tema`, `categoria_iso`, `crs`,
`tipo_geometria`, `cantidad_registros`, `cantidad_campos`, `campos`,
`bbox_5344`, `bbox_4326`, `licencia`, `palabras_clave`, `linaje`,
`contacto_email`, `organizacion`, `titulo_metadato`, `resumen_metadato`,
`archivo_gpkg`, `archivo_qmd`, `tamano_bytes`, `checksum_sha256`,
`fecha_modificacion`.

`catalogo_completo.csv` y `.json` son **artefactos derivados**: los regenera
CI en cada push y están en `.gitignore`. No los edites a mano.

## Exportar un maestro desde QGIS: la opción FID

Al exportar una capa a GeoPackage, en el diálogo de QGIS hay que poner el
nombre del campo identificador en la opción **FID**. Por defecto QGIS usa
`fid`, y entonces la clave primaria del GeoPackage se llama `fid`, que
`nomenclatura.md` §5 prohíbe.

Poniendo **`FID` = `id`** la clave primaria pasa a llamarse `id`, que es lo que
pide la nomenclatura. El DDL resultante tiene que verse así:

```sql
CREATE TABLE "cr_adm_limites_barrios" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "geom" MULTIPOLYGON,
  ...
)
```

Si el archivo de origen ya traía un campo llamado `fid`, después del export
queda como **atributo común** además de la nueva clave `id`, y QGIS no lo deja
borrar mientras siga siendo la clave primaria. Una vez que `id` es la PK, el
campo `fid` sobrante sí se puede eliminar normalmente desde Propiedades de la
capa > Campos.

`validar_catalogo.py` detecta este caso y lo reporta como error, así que no
hace falta acordarse: si el `fid` quedó, el CI avisa.

## Nota sobre la reproyección

`comun.a_wgs84()` implementa la Transversa de Mercator inversa (Snyder,
*Map Projections: A Working Manual*, ecs. 3-21 y 8-1..8-8) para no depender de
GDAL solo para calcular un bbox. Se usa **únicamente para las cuatro esquinas
del bbox**, nunca para reproyectar geometrías: cuando exista
`generar_derivados.py`, ese sí va a usar `ogr2ogr` (que ya viene con QGIS y se
instala en CI con `apt install gdal-bin`).

## Vocabularios

`validar_catalogo.py` lee `catalogo/vocabularios/estados.csv` si existe, y si
no usa los cinco valores de `nomenclatura.md` §7. El comité técnico puede
cambiar el vocabulario sin tocar código.
