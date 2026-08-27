# cr-equ-playones-deportivos - Playones deportivos

Historial de cambios del dataset. Uno por versión, más reciente arriba.
El formato de versión es SemVer según `nomenclatura.md` §6:

- **MAJOR**: cambia el esquema (campos, tipo de geometría) o el CRS.
- **MINOR**: se agregan, quitan o modifican registros.
- **PATCH**: correcciones de atributos que no cambian la cantidad de registros.

---

## 1.0.0 - 2026-08-27

Primera carga del dataset como maestro versionado. Primer dataset de puntos del
catálogo: los dos anteriores son polígonos.

- 77 registros, POINT, EPSG:5344.
- Campos: `id`, `tipo`, `calle`, `barrio`, `obs`, `latitud`, `longitud`.
- Extensión: -67.672598, -45.900972, -67.374034, -45.727191 (EPSG:4326).
- Metadato `.qmd` sidecar con licencia CC-BY-4.0 y contacto institucional.
- Responsable: navarro. Estado: publicado.
- El `<extent>` del `.qmd` sí está calculado desde la capa, a diferencia de los
  dos datasets anteriores.

**Deuda conocida al momento de la carga** (ver `docs/03-proceso/pipeline.md`):

- `frecuencia_actualizacion` vacía en `catalogo.csv`. Es el elemento A8 del
  perfil IDERA v2.0 y es obligatorio: sin ese valor el XML ISO 19139 se genera
  incompleto y el dataset no está listo para cosecha.
- `<history>` del `.qmd` vacío: falta documentar de dónde salió el dato, con qué
  fecha de captura y cómo se normalizó.
- La descripción del catálogo tiene 74 caracteres; la ficha institucional pide
  un mínimo de 200 para que sirva como metadato publicable.
- Los campos `latitud` y `longitud` guardan el punto en WGS 84 (EPSG:4326), en
  grados decimales, mientras que `geom` lo guarda en EPSG:5344, en metros. Se
  publican a propósito, para que quien descargue la capa tenga las coordenadas
  legibles sin reproyectar. Dos consecuencias a tener presentes:
  - Son una copia, no la geometría. Si se mueve un punto en QGIS hay que
    recalcularlos con la calculadora de campos (`$x`/`$y` sobre la capa
    reproyectada, o `x(transform($geometry, 'EPSG:5344', 'EPSG:4326'))`), o los
    dos números quedan desactualizados en silencio.
  - Difieren del GeoJSON publicado en unos 0,66 m: los valores del `.gpkg` se
    calcularon aplicando la transformación de datum POSGAR 2007 a WGS 84, y
    `comun.py::a_wgs84()` la neutraliza a propósito. Es el mismo corrimiento
    documentado para el resto del catálogo, no un error de carga.

**Linaje**: pendiente de completar. Registrar aquí el origen del dato
(relevamiento propio, ordenanza, convenio), la fecha de captura, la escala y las
transformaciones aplicadas antes de la carga.
