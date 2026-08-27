# cr-equ-espacios-verdes - Espacios verdes

Historial de cambios del dataset. Uno por versión, más reciente arriba.
El formato de versión es SemVer según `nomenclatura.md` §6:

- **MAJOR**: cambia el esquema (campos, tipo de geometría) o el CRS.
- **MINOR**: se agregan, quitan o modifican registros.
- **PATCH**: correcciones de atributos que no cambian la cantidad de registros.

---

## 1.0.0 - 2026-08-26

Primera carga del dataset como maestro versionado.

- 383 registros, MULTIPOLYGON, EPSG:5344.
- Campos: `id`, `area_m2`, `nombre`, `cat`, `barrio`, `calle`, `interseccion`.
- Extensión: -67.678974, -45.911239, -67.367476, -45.729520 (EPSG:4326).
- Metadato `.qmd` sidecar con licencia CC-BY-4.0 y contacto institucional.
- Responsable: rodriguez. Estado: publicado.

**Deuda conocida al momento de la carga** (ver `docs/03-proceso/pipeline.md`):

- `frecuencia_actualizacion` vacía en `catalogo.csv`. Es el elemento A8 del
  perfil IDERA v2.0 y es obligatorio: sin ese valor el XML ISO 19139 se genera
  incompleto y el dataset no está listo para cosecha.
- `<history>` del `.qmd` vacío: falta documentar de dónde salió el dato, con qué
  fecha de captura y cómo se normalizó.
- El `<extent>` del `.qmd` guarda el valor centinela de QGIS en lugar de la
  extensión real de la capa. Se corrige en Propiedades de la capa > Metadatos >
  Extensión > "Establecer desde la capa", y volviendo a guardar el `.qmd`.
- La descripción del catálogo tiene 70 caracteres; la ficha institucional pide
  un mínimo de 200 para que sirva como metadato publicable.
- El campo `area_m2` es redundante con la geometría. No es un error, pero queda
  registrado: si se editan los polígonos hay que recalcularlo a mano o el
  atributo miente.

**Linaje**: pendiente de completar. Registrar aquí el origen del dato
(relevamiento propio, ordenanza, convenio), la fecha de captura, la escala y las
transformaciones aplicadas antes de la carga.
