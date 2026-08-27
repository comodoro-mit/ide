# cr-equ-asociaciones-vecinales - Asociaciones vecinales

Historial de cambios del dataset. Uno por versión, más reciente arriba.
El formato de versión es SemVer según `nomenclatura.md` §6:

- **MAJOR**: cambia el esquema (campos, tipo de geometría) o el CRS.
- **MINOR**: se agregan, quitan o modifican registros.
- **PATCH**: correcciones de atributos que no cambian la cantidad de registros.

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
