# Pipeline de datos: qué existe y qué falta

Estado al 2026-08-24. Este archivo es el mapa de la automatización: qué hace
cada pieza, en qué orden corre, y qué falta construir.

## El circuito completo

```
QGIS (normalizar)                    ← humano
  ↓
maestros/<tema>/cr-<id>.gpkg + .qmd  ← se commitea (es el dato)
  ↓
catalogo/catalogo.csv                ← humano, 8 columnas
  ↓
validar_catalogo.py                  ← CI, frena el merge si algo no cumple
  ↓
derivar_catalogo.py                  ← CI, agrega 21 columnas leídas del dato
  ↓
catalogo_completo.{csv,json}         ← derivado, NO se commitea
  ↓
generar_derivados.py                 ← CI, GeoJSON 4326 / PMTiles      [FALTA]
  ↓
creador_metadata.py                  ← CI, ISO 19139 para IDERA        [FALTA]
  ↓
ide-visores/ + geoportal             ← publicación                     [FALTA]
```

La regla que ordena todo: **si un script puede regenerarlo, no es dato, es
caché, y no se commitea** (ADR-002). Solo el `.gpkg`, el `.qmd` y el
`catalogo.csv` se versionan.

## Checklist

### Hecho

- [x] Estructura de carpetas de `ide-datos/` e `ide-visores/`
- [x] `catalogo.csv` con la primera capa (`cr-adm-limites-barrios`)
- [x] Primer maestro cargado: `maestros/adm/cr-adm-limites-barrios.gpkg` + `.qmd`
- [x] `scripts/comun.py` — módulo compartido, sin dependencias externas
- [x] `scripts/validar_catalogo.py` — valida nomenclatura, CRS, campos, pareja de archivos
- [x] `scripts/derivar_catalogo.py` — mergea el CSV manual con lo leído del `.gpkg`/`.qmd`
- [x] `catalogo/changelog/cr-adm-limites-barrios.md` — primer changelog por dataset
- [x] `.github/workflows/validar.yml` — corre ambos en cada push y PR
      (**en la raíz del repositorio**, ver nota abajo)
- [x] `catalogo/vocabularios/temas.csv` y `estados.csv`

### Estado del primer dataset

`cr-adm-limites-barrios` pasa la validación: **0 errores, 3 avisos**.

- [x] ~~Sacar el campo `fid`~~ — resuelto exportando desde QGIS con la opción
      **`FID` = `id`**, que cambia la clave primaria de `fid` a `id`. Una vez
      que `id` es la PK, el `fid` sobrante se borra normalmente desde
      Propiedades de la capa > Campos. Ver `scripts/README.md`.
- [x] ~~Vocabulario de `estado`~~: corregido a `publicado` (2026-08-24).
- [x] ~~`version` a SemVer~~: `1` → `1.0.0` (2026-08-24).
- [ ] **Recalcular la extensión del `.qmd`** en QGIS: Propiedades > Metadatos >
      Extensión > "Establecer desde la capa". Hoy guarda un valor centinela.
- [ ] **Completar `<history>` del `.qmd`** con el linaje: de dónde salió el
      dato, cómo se normalizó, con qué fecha de captura. Cerrarlo también en
      `catalogo/changelog/cr-adm-limites-barrios.md`.

### Antes de cargar el resto de las capas

- [ ] Ampliar `descripcion` a 200+ caracteres (la ficha institucional lo pide
      para que sirva como metadato publicable, no solo como nota interna).
- [ ] Decidir si `nivel_acceso` y `licencia` entran al `catalogo.csv` o se leen
      del `.qmd`. Hoy `derivar_catalogo.py` los lee del `.qmd`; funciona, pero
      significa que el nivel de acceso no es filtrable desde el CSV manual.
- [ ] Cargar las capas restantes siguiendo la tabla de correspondencia de
      `nomenclatura.md` §13.

### Falta construir

- [ ] **`generar_derivados.py`** — GeoJSON en EPSG:4326 desde cada maestro
      (obligatorio por RFC 7946), y PMTiles para las capas pesadas. Es el
      primer script que necesita GDAL: `ogr2ogr` ya viene con QGIS y en CI se
      instala con `apt install gdal-bin`.
- [ ] **`creador_metadata.py`** — reescrito. El original del repo viejo genera
      metadatos falsos (`topiccategory: boundaries` hardcodeado para toda capa,
      `geomtype: unknown`, bbox fijo del ejido, y `CRS_EPSG = "EPSG:5344"`
      definida y nunca escrita). El reemplazo sale del `.qmd` real más las
      columnas derivadas. **Pendiente de decidir**: si IDERA cosecha vía CSW,
      hace falta exportar a ISO 19139 XML; el `.qmd` nativo de QGIS no alcanza.
- [ ] **`publicar.yml`** — workflow de publicación a GitHub Pages (Fase 0–2) y
      luego a Cloudflare Pages (ADR-003).
- [ ] **`revisar-vencidos.yml`** — tarea programada que marca
      `desactualizado` todo dataset cuya `proxima_revision` ya pasó. Requiere
      que exista la columna `proxima_revision`, que hoy no está en el CSV.

## Qué se edita a mano y qué no

Esta es la distinción que sostiene todo el circuito. Si se rompe, el catálogo
vuelve a ser una planilla que hay que mantener sincronizada a mano.

| Archivo | ¿Se edita a mano? | ¿Se commitea? |
|---|---|---|
| `maestros/<tema>/*.gpkg` | Sí, en QGIS | Sí |
| `maestros/<tema>/*.qmd` | Sí, en QGIS | Sí |
| `catalogo/catalogo.csv` | **Sí** — es la única fuente manual | Sí |
| `catalogo/vocabularios/*.csv` | Sí, por decisión del comité | Sí |
| `catalogo/catalogo_completo.csv` | **No** | No (`.gitignore`) |
| `catalogo/catalogo_completo.json` | **No** | No (`.gitignore`) |

Los dos `catalogo_completo.*` los reescribe `derivar_catalogo.py` de cero en
cada corrida. Cualquier cambio hecho a mano ahí se pierde en el próximo push.
Si falta o está mal un dato: corregir `catalogo.csv`, el `.qmd` o el `.gpkg`,
y volver a correr el script.

## Convención de commits

Los commits y los push los hace el usuario. Formato de `nomenclatura.md` §8,
en inglés, breves, sin cuerpo:

```
<tipo>(<ámbito>): <qué cambió>
```

Tipos: `datos`, `catalogo`, `visor`, `ci`, `docs`, `fix`.

Un dataset nuevo entra con **dos** commits, no uno: el maestro por un lado y su
fila del catálogo por el otro, para que el historial muestre por separado
"llegó el dato" y "se declaró el dato".

```
datos(adm): add cr-adm-limites-barrios master layer
catalogo(adm): register cr-adm-limites-barrios
```

## Decisiones tomadas en esta etapa

**El catálogo manual se queda en 8 columnas, no 16.** El equipo mantiene a mano
solo lo que efectivamente sabe; el resto se lee del dato. `derivar_catalogo.py`
saca 21 columnas más del `.gpkg` y del `.qmd`, incluidos licencia, palabras
clave y contacto, que ya estaban cargados en el metadato QGIS. No hay que
inventar nada.

**Los scripts de validación y derivación no usan GDAL.** Un GeoPackage es
SQLite: `sqlite3` de la biblioteca estándar lee estructura, extensión y
registros. Ventaja concreta: corren con `py -3` en cualquier Windows sin
instalar nada y en un runner de CI pelado, sin minutos gastados en instalar
GDAL. La reproyección del bbox a 4326 se resuelve con la Transversa de Mercator
inversa implementada en `comun.py`. GDAL entra recién con
`generar_derivados.py`, donde sí hay que reproyectar geometrías.

**Todos los workflows viven en `.github/workflows/` de la raíz.**
`nomenclatura.md` §10 los pone dentro de `ide-datos/` e `ide-visores/`, pero eso
suponía dos repositorios separados. Con un solo repo, GitHub Actions solo lee la
carpeta de la raíz: un `.yml` en `ide-datos/.github/workflows/` nunca se
ejecuta. No es una limitación: un workflow filtra por `paths:` y corre solo
cuando cambia la parte del repo que le importa, que es exactamente lo que hace
`validar.yml`. Las carpetas `ide-datos/.github/` e `ide-visores/.github/` son
scaffolding muerto y conviene eliminarlas para que nadie deje un workflow ahí
esperando que corra.

**Errores vs. avisos.** El validador frena el CI solo ante errores
(nomenclatura violada, CRS incorrecto, archivo faltante). Los avisos —
descripción corta, linaje vacío, versión sin SemVer — quedan visibles en el log
sin bloquear la carga. La idea es que el primer dataset entre hoy y la calidad
del metadato mejore con el tiempo, no que la barra perfecta impida empezar.
