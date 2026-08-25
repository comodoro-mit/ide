# Pipeline de datos

Estado al 2026-08-24. Mapa de la automatización: qué corre, en qué orden, qué
falta.

## El circuito

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
generar_derivados.py                 ← CI, GeoJSON 4326
  ↓
creador_metadata.py                  ← CI, ISO 19139 XML para IDERA
  ↓
armar_sitio.py                       ← CI, arma sitio/ (agnóstico del host)
  ↓
publicar.yml → GitHub Pages          ← CI. Cloudflare en Fase 3

ide-visores/geoportal/               ← plantilla html+css+js, se edita a mano
ide-visores/src/visores/             ← FALTA: los visores de mapa
```

La regla que lo ordena (ADR-002): **si un script puede regenerarlo, no es dato,
es caché, y no se commitea.** Solo el `.gpkg`, el `.qmd` y el `catalogo.csv` se
versionan.

## Qué se edita a mano y qué no

| Archivo | ¿A mano? | ¿Se commitea? |
|---|---|---|
| `maestros/<tema>/*.gpkg` y `*.qmd` | Sí, en QGIS | Sí |
| `catalogo/catalogo.csv` | **Sí — única fuente manual** | Sí |
| `catalogo/vocabularios/*.csv` | Sí, por el comité | Sí |
| `catalogo/catalogo_completo.*` | **No** | No |
| `derivados/*.geojson` | **No** | No |
| `sitio/` | **No** | No |
| `ide-visores/geoportal/*` | **Sí — html, css y js a mano** | Sí |
| `config.json` | Sí (una línea: `url_base`) | Sí |

Los derivados se reescriben de cero en cada corrida. Un cambio hecho a mano ahí
se pierde en el próximo push: corregir `catalogo.csv`, el `.qmd` o el `.gpkg`.

## Convención de commits

Los commits y push los hace el usuario. Formato de `nomenclatura.md` §8, en
inglés, breves, sin cuerpo: `<tipo>(<ámbito>): <qué cambió>`, con tipo entre
`datos`, `catalogo`, `visor`, `ci`, `docs`, `fix`.

Un dataset nuevo entra con **dos** commits, para que el historial distingue
"llegó el dato" de "se declaró el dato":

```
datos(adm): add cr-adm-limites-barrios master layer
catalogo(adm): register cr-adm-limites-barrios
```

## Checklist

### Hecho

- [x] Estructura de carpetas, `catalogo.csv`, primer maestro
- [x] `scripts/comun.py`, `validar_catalogo.py`, `derivar_catalogo.py`
- [x] `scripts/generar_derivados.py` — GeoJSON 4326, dos motores equivalentes
- [x] `.github/workflows/validar.yml` (en la raíz del repo, ver abajo)
- [x] `catalogo/vocabularios/temas.csv` y `estados.csv`
- [x] `catalogo/changelog/cr-adm-limites-barrios.md`
- [x] `scripts/armar_sitio.py` + `.github/workflows/publicar.yml`
- [x] `config.json` con `url_base` configurable
- [x] ADR-003 corregido: el tope de GitHub Pages es 100 GB/mes, no 1 GB
- [x] `scripts/creador_metadata.py` — ISO 19139 según el perfil IDERA v2.0
- [x] `ide-visores/geoportal/` — página principal en tres archivos separados
- [x] Pages activado y `publicar.yml` corrigiendo: la URL la aporta GitHub vía
      `actions/configure-pages`, no está escrita a mano en ningún archivo

### Primer dataset: pasa la validación, 0 errores y 3 avisos

- [x] ~~Campo `fid`~~ — resuelto exportando desde QGIS con **`FID` = `id`**
- [x] ~~Vocabulario de `estado`~~ y ~~`version` a SemVer~~
- [ ] Recalcular la extensión del `.qmd`: Propiedades > Metadatos > Extensión >
      "Establecer desde la capa". Hoy guarda un valor centinela.
- [ ] Completar `<history>` del `.qmd` con el linaje: origen del dato, fecha de
      captura, transformaciones. Cerrarlo también en el changelog del dataset.
- [ ] Ampliar `descripcion` a 200+ caracteres para que sirva como metadato
      publicable.
- [ ] Completar `frecuencia_actualizacion` en `catalogo.csv`. Es el elemento A8
      de IDERA, obligatorio. Valores en `catalogo/vocabularios/frecuencias.csv`.

### Falta construir

- [ ] **Completar `frecuencia_actualizacion`** para que el metadato llegue a
      17/17. Es lo único que le falta al elemento A8; C1 ya se resuelve solo.
- [ ] **Los visores de mapa** en `ide-visores/src/`. La página principal ya está.
- [ ] **Confirmar con IDERA** cómo se incorpora el nodo: el XML ya cumple el
      perfil v2.0, falta saber si cosechan por CSW o alcanza con publicarlo.
- [ ] **`revisar-vencidos.yml`** — marca `desactualizado` lo que venció.
      Requiere una columna `proxima_revision` que hoy no existe.
- [ ] **PMTiles** — recién cuando haya una capa que lo justifique. Los 83 KB de
      barrios no lo necesitan.

## Decisiones tomadas

**Catálogo manual de 8 columnas, no 16.** El equipo mantiene solo lo que sabe;
el resto se lee del dato. Licencia, palabras clave, contacto y organización ya
estaban en el `.qmd`. No hay que inventar nada.

**Validación y derivación sin GDAL.** Un GeoPackage es SQLite. Corre con `py -3`
en cualquier Windows sin instalar nada y en un runner de CI pelado, coherente
con presupuesto cero. `generar_derivados.py` usa GDAL si está, pero produce el
mismo archivo si no.

**Los dos motores de reproyección dan salida idéntica.** Verificado vértice por
vértice. Hubo que neutralizar la transformación de datum que PROJ inserta sola
(corría todo 0,66 m) y unificar la orientación de anillos en una sola función.
El detalle está en `ide-datos/scripts/README.md`. Si alguna vez se cambia el
criterio geodésico, se cambia en los dos motores, nunca en uno.

**Todos los workflows van en `.github/workflows/` de la raíz.**
`nomenclatura.md` §10 los pone dentro de `ide-datos/` e `ide-visores/`, pero eso
suponía dos repositorios. Con un solo repo, GitHub Actions solo lee la carpeta
de la raíz. No es una limitación: cada workflow filtra por `paths:` y corre solo
cuando cambia lo suyo. Conviene borrar `ide-datos/.github/` e
`ide-visores/.github/` para que nadie deje un `.yml` ahí esperando que corra.

**La URL del sitio no se escribe a mano.** `actions/configure-pages` devuelve
`steps.pages.outputs.base_url`, que es la URL real de Pages —sirve igual para
`comodoro-mit.github.io/ide` que para un dominio propio configurado en
Settings > Pages—. `publicar.yml` la pasa como `IDE_URL_BASE` a los pasos que
la necesitan. Ojo: va en el `env:` **de cada paso**, nunca en el del job: el
contexto `steps` no existe cuando se evalúa el `env:` de un job y saldría
vacío. `config.json` y `vars.IDE_URL_BASE` quedan de respaldo para corridas
locales o para publicar fuera de GitHub Pages.

**Errores vs. avisos.** El CI frena solo ante errores. Los avisos quedan
visibles sin bloquear: la idea es que el primer dataset entre y la calidad del
metadato mejore con el tiempo, no que la barra perfecta impida empezar.
