## Problema

### Situación Actual

El repositorio de la IDE Comodoro Rivadavia (`agstnrdz/ide`, 38 MB) necesita una transición de arquitectura urgente por varios problemas acumulados:

### Deuda Técnica Crítica

1. **Cinco datasets sin maestro de datos confiable**
   - Transporte (líneas, paradas): almacenados *solo* en `layers_transporte/*.geojson`
   - Barrios: datos en tres archivos JavaScript (`barrios_data.js`, `barrios_nivel_instruccion_data.js`, `barrios_sexo_data.js`)
   - Problema: si se pierden estos archivos, no hay forma de recuperar los datos. Son fuente de verdad único.

2. **Metadatos falsos generados automáticamente**
   - `creador_metadata.py` escribe:
     - `topiccategory: boundaries` para todas las capas (incorrecto)
     - `geomtype: unknown` (nunca se calcula)
     - bbox fijo del ejido (no por capa)
     - `CRS_EPSG: EPSG:5344` definido pero nunca escrito en XML
   - Problema: metadatos no conforman a estándares (ISO 19115, IDERA). No se pueden federar.

3. **Duplicación de datos masiva**
   - Ejemplo: cada capa censal existe en:
     - GeoPackage (maestro pretendido)
     - GeoJSON (derivado para web)
     - JavaScript (copia para visor histórico)
   - Problema: cambios no se sincronizan. Nadie sabe cuál es la versión correcta.

4. **Sin versionado de datos utilizable**
   - Commits tipo "Actualizar visor" sin contexto
   - No hay forma de auditar "cuándo cambió este dataset y por qué"
   - Problema: cumplimiento regulatorio débil (IDERA, IGN).

5. **Repositorio en cuenta personal**
   - Riesgo de continuidad #1: si la persona se va, se pierden los permisos.
   - Problema: el área (DGMIT) no es propietaria del repositorio institucionalmente.

### Restricción de Presupuesto

- VPS solicitado (24 GB, 8 cores, cPanel) en marzo 2025: **nunca aprobado**
- Free tiers de base de datos son inestables:
  - Supabase: suspende a la semana de inactividad
  - Neon: escala a cero sin aviso
- Problema: no podemos usar PostGIS como maestro si el proveedor puede apagar la base de datos.

### Contexto Institucional

- Convenios vigentes: IDERA (2021), UNPSJB (2021), IGN (2022)
- Resolución IDE-CR activa (Notas 009/25, 010/25, 17/03/2025)
- Expectativa: federar el catálogo en IDERA. Requiere metadatos ISO 19115 válidos y maestro confiable.

## Impacto

Sin transición, en 12-18 meses:
- El repositorio crece a 100+ MB (no es escalable en GitHub)
- Los metadatos siguen siendo falsos → IDERA rechaza la federación
- Nuevos datos se duplican automáticamente → imposible auditar
- Riesgo: perder continuidad institucional si cambia el personal
