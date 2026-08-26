## Objetivos de la Transición

### Objetivo General

Transformar la IDE Comodoro Rivadavia en un geoportal confiable, institucional y escalable, con maestro de datos versionado, metadatos conformes a estándares ISO 19115, y capacidad de federación en IDERA.

### Objetivos Específicos

### 1. Establecer Maestro de Datos Único

- **Formato**: GeoPackage (GPKG) versionado en Git
- **Ubicación**: Repositorio institucional (no personal)
- **Responsabilidad**: CI/CD automático valida, genera derivados, sincroniza con análisis
- **Why**: presupuesto cero → no podemos confiar en free tiers de Postgres

**Resultado esperado**: "Fuente de verdad" única, auditable, recuperable de cualquier versión histórica.

### 2. Eliminar Duplicación de Datos

- **Regla**: Si un script puede regenerarlo, no se commitea (es caché, no dato)
- **Derivados automáticos**: 
  - GeoJSON para web (desde GPKG por CI)
  - JavaScript (si aún se necesita para visor histórico, desde GPKG)
  - Catálogo de metadatos (campos derivados: CRS, geometría, bbox, checksum, cantidad de registros)
- **Aplicación**: Resolver cinco datasets sin maestro (transporte, barrios)

**Resultado esperado**: Repo baja de 38 MB a ~8-12 MB. Crecimiento mono tónico elimina do.

### 3. Generar Metadatos Conformes a Estándares

- **Estándar**: ISO 19115 (metadatos geoespaciales)
- **Validación**: CI valida contra perfil IDERA antes de mergear
- **Campos manuales**: 13 (título, resumen, palabras clave, responsable, etc.)
- **Campos derivados**: 13 (CRS, tipo de geometría, cantidad de registros, bbox, checksum, URLs, etc.)
- **Herramienta**: Sheets como formulario de entrada (no como maestro)

**Resultado esperado**: Metadatos válidos para federación en IDERA. Auditoría del origen de cada dato.

### 4. Institucionalizar el Repositorio

- **Migración**: De cuenta personal (`agstnrdz/ide`) a cuenta institucional (`municipalidad/ide` o equivalente)
- **Permisos**: Equipo DGMIT tiene control, no depende de persona individual
- **Documentación**: ADRs versionados en Git explican cada decisión de arquitectura

**Resultado esperado**: Continuidad garantizada. Si alguien se va, el proyecto continúa.

### 5. Implementar Versionado Auditable

- **Formato de commit**: Cada cambio de dataset va acompañado de:
  - Qué cambió (capa, registros añadidos/borrados/modificados)
  - Por qué cambió (resolución, actualización periódica, corrección, etc.)
  - Quién cambió (usuario responsable)
  - Cuándo cambió (timestamp)
- **Historial**: `git log` permite reconstruir cualquier versión anterior

**Resultado esperado**: Trazabilidad completa. Cumple con requisitos de auditoría (IDERA, IGN).

### 6. Escalar a PostGIS sin Cambiar Arquitectura (Fase 5)

- **Condición**: Se migra a PostGIS solo cuando se cumpla UNO de:
  - Más de un área escribiendo con concurrencia
  - Más de ~50 datasets
  - Consulta dinámica por atributo
- **Cambio mínimo**: Sincronización GPKG ↔ PostGIS por CI, maestro sigue siendo GPKG
- **Costo**: VPS de 4-8 GB, ~USD 100-150/año (presupuesto futuro)

**Resultado esperado**: Escalabilidad probada sin perder simplicidad de Fases 0-4.

## Éxito Medible

Al finalizar la transición (Fase 4), el proyecto cumple:

- ✅ 23 datasets en 1 GPKG versionado en Git
- ✅ Cero duplicación de datos (repo < 15 MB)
- ✅ Metadatos 100% conformes ISO 19115
- ✅ Federación en IDERA aprobada
- ✅ Repositorio institucional, no personal
- ✅ CI/CD valida y genera derivados automáticamente
- ✅ Historial completo auditable desde `git log`
