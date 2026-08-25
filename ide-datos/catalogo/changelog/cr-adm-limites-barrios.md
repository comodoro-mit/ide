# cr-adm-limites-barrios — Límites de barrios

Historial de cambios del dataset. Uno por versión, más reciente arriba.
El formato de versión es SemVer según `nomenclatura.md` §6:

- **MAJOR**: cambia el esquema (campos, tipo de geometría) o el CRS.
- **MINOR**: se agregan, quitan o modifican registros.
- **PATCH**: correcciones de atributos que no cambian la cantidad de registros.

---

## 1.0.0 — 2026-08-24

Primera carga del dataset como maestro versionado.

- 77 registros, MULTIPOLYGON, EPSG:5344.
- Campos: `id`, `nombre`, `zona`, `circ`, `sector`.
- Metadato `.qmd` sidecar con licencia CC-BY-4.0 y contacto institucional.

**Deuda conocida al momento de la carga** (ver `docs/03-proceso/pipeline.md`):

- El GeoPackage arrastra un campo `fid` que duplica `id`. Prohibido por
  `nomenclatura.md` §5. Pendiente de eliminar en QGIS.
- `<history>` del `.qmd` vacío: falta documentar de dónde salió el dato, con qué
  fecha de captura y cómo se normalizó.
- El `<extent>` del `.qmd` guarda el valor centinela de QGIS en lugar de la
  extensión real de la capa.
- La descripción del catálogo tiene 83 caracteres; la ficha institucional pide
  un mínimo de 200 para que sirva como metadato publicable.

**Linaje**: pendiente de completar. Registrar aquí el origen del dato (relevamiento
propio, ordenanza, convenio), la fecha de captura, la escala y las
transformaciones aplicadas antes de la carga.
