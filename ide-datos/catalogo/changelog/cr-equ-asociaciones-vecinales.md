# cr-equ-asociaciones-vecinales - Asociaciones vecinales

Historial de cambios del dataset. Uno por versión, más reciente arriba.
El formato de versión es SemVer según `nomenclatura.md` §6:

- **MAJOR**: cambia el esquema (campos, tipo de geometría) o el CRS.
- **MINOR**: se agregan, quitan o modifican registros.
- **PATCH**: correcciones de atributos que no cambian la cantidad de registros.

---

## 2.0.0 - 2026-08-28

Se saca del maestro el dato personal que nunca debio estar en un repositorio
publico, y se corrigen las geometrias vacias que rompian el build.

- **Se elimina la columna `tel`.** Guardaba los telefonos de las personas que
  presiden cada asociacion, 64 de 68 registros. El campo estaba declarado como
  reservado y el pipeline lo excluia de las tres salidas publicadas, pero eso
  protege lo que se publica, **no el maestro**, y el maestro se commitea a un
  repositorio publico. El dato estuvo accesible en el historial de git desde la
  carga inicial hasta esta version.
- **Se elimina la columna `correo`**, vacia en los 68 registros.
- **Las 15 geometrias vacias pasan de `POINT EMPTY` a `NULL`.** `ogr2ogr` no
  puede reproyectar coordenadas `NaN` y abortaba la derivacion en la entidad 54.
  Con geometria nula las 15 entidades siguen publicandose, con sus atributos y
  sin ubicacion: en el GeoJSON salen como `"geometry": null`. Se corrigio con
  una sentencia SQL desde el DB Manager de QGIS, no con un parche en el
  pipeline.
- **`responsable` se mantiene publicado.** Decision tomada, no pendiente: es un
  rol de representacion vecinal y el dato se considera publico. Queda asentado
  aca para que no se vuelva a discutir por omision.
- Se reescribio el historial del repositorio con `git filter-repo` para purgar
  todas las versiones del maestro que contenian la columna `tel`.

### Esquema

Cambio MAJOR: el maestro pasa de 14 a 12 columnas. Quedan `id`, `geom`, `tipo`,
`posee_comision`, `nombre`, `calle`, `altura`, `interseccion`, `barrio`,
`responsable`, `latitud`, `longitud`.

### Lo que sigue pendiente

- `frecuencia_actualizacion` vacia en `catalogo.csv`: elemento A8 del perfil
  IDERA v2.0, obligatorio para la cosecha.
- La descripcion del catalogo tiene 77 caracteres; la ficha institucional pide
  un minimo de 200.
- `<history>` del `.qmd` vacio: el linaje del dato no esta documentado.
- `validar_catalogo.py` no detecta geometrias vacias ni nulas. Se entero el
  build, que es tarde.
- Las 15 entidades sin ubicacion siguen sin coordenadas. Publicarlas sin
  ubicacion es el estado actual, no una decision cerrada.

---

## 1.0.0 - 2026-08-27

Primera carga del dataset como maestro versionado.

- 68 registros, POINT, EPSG:5344.
- Campos del maestro: `id`, `tipo`, `posee_comision`, `nombre`, `calle`,
  `altura`, `interseccion`, `barrio`, `tel`, `correo`, `responsable`,
  `latitud`, `longitud`.
- Metadato `.qmd` sidecar con licencia CC-BY-4.0 y contacto institucional.
- Responsable: navarro. Estado: publicado.

### Campo reservado: `tel` no se publica

`tel` guarda los teléfonos de las personas que presiden cada asociación
vecinal, 64 de los 68 registros. Son datos personales de particulares, y el
catálogo se publica bajo CC BY 4.0, o sea reutilizable por cualquiera para
cualquier fin.

Se declaró como campo reservado en `comun.CAMPOS_RESERVADOS`, así que el
pipeline lo saca de las **tres** salidas publicadas:

- el `.geojson` derivado no lo incluye,
- el `.gpkg` publicado es una copia saneada del maestro, sin la columna,
- la columna `campos` del catálogo publicado ni siquiera lo nombra.

**El maestro conserva la columna y los 64 teléfonos.** Esto oculta el campo de
lo que sale a la web, no lo borra de la fuente de verdad.

> Corregido en 2.0.0: esa era exactamente la falla. El maestro se commitea a un
> repositorio publico, asi que reservar el campo nunca alcanzo. La columna se
> elimino y el historial se purgo.

### Deuda conocida al momento de la carga

- **15 de las 68 entidades tienen la geometría vacía** (el flag `empty` del
  encabezado GeoPackage; no son NULL ni tienen coordenadas inválidas). Se
  publican en el catálogo y en el GeoJSON pero nunca se dibujan: en el visor se
  ven 53 puntos. Son ARA San Juan, Padre Juan Corti, Bella Vista Oeste, Los
  Bretes, Roque González y diez más. Hay que ubicarlas en QGIS o decidir que se
  publican sin ubicación a propósito. `validar_catalogo.py` todavía no detecta
  este caso.
- **`responsable` guarda nombre y apellido de personas**, 64 de 68 registros.
  Hoy se publica. Queda la misma pregunta que se resolvió para `tel`: si no
  corresponde publicarlo, alcanza con sumarlo a la tupla de
  `comun.CAMPOS_RESERVADOS`.
- `correo` está vacío en los 68 registros. O se completa o se saca del maestro.
- `frecuencia_actualizacion` vacía en `catalogo.csv`: es el elemento A8 del
  perfil IDERA v2.0 y es obligatorio para la cosecha.
- La descripción del catálogo tiene 77 caracteres; la ficha institucional pide
  un mínimo de 200.
- `<history>` del `.qmd` vacío: el linaje del dato no está documentado.
- `latitud` y `longitud` duplican la geometría como atributos, con la misma
  salvedad que en `cr-equ-playones-deportivos`: hay que recalcularlas a mano si
  se mueve un punto. Solo 53 de 68 las tienen cargadas, coincidiendo con las
  entidades que sí tienen geometría.

**Linaje**: pendiente de completar. Registrar aquí el origen del dato
(relevamiento propio, ordenanza, convenio), la fecha de captura, la escala y las
transformaciones aplicadas antes de la carga.
