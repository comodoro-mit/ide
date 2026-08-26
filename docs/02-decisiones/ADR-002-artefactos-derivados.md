## ADR-002: Regla del Artefacto Derivado - No Commitear Generados

### Estado

- [x] Propuesto
- [x] Aceptado
- [ ] Deprecado
- [ ] Reemplazado por ADR-NNN

### Contexto

Hoy el repositorio tiene:
- Cada capa censal existe en 3 formatos: GPKG (maestro pretendido), GeoJSON (web), JavaScript (visor histórico)
- Resultado: 38 MB total, 11 MB en .git
- Cambios: cuando se actualiza una capa, nadie sincroniza manualmente los tres formatos
- Consecuencia: no está claro cuál es la fuente de verdad

Crecimiento monótono: cada nuevo dataset suma a 38 MB, sin poder limpiar versiones viejas sin perder historia.

### Decisión

**Regla del artefacto derivado:**

> Si un script puede regenerarlo, no es dato, es caché, y no se commitea.

Aplicación:
- **GeoJSON**: se genera desde GPKG por CI, no se commitea
- **JavaScript** (si aún se necesita): se genera desde GPKG por CI, no se commitea
- **Metadatos ISO 19115**: se generan desde GPKG + formulario (Sheets) por CI, no se commitean
- **Catálogo HTML/PDF**: se genera por CI, no se commitea

Repositorio commitea **solo**:
- GPKG maestro (datos)
- Formulario de metadatos (CSV/JSON de campos manuales)
- Scripts y CI/CD
- Documentación (esto)
- .gitignore, Config, etc.

### Consecuencias

### Positivas
- ✅ Repo baja de 38 MB a ~8-12 MB (elimina 60-70% de bloat)
- ✅ Una única fuente de verdad (GPKG)
- ✅ Si alguien daña un derivado, CI lo regenera
- ✅ Actualizaciones son atómicas: cambio GPKG, CI regenera todo
- ✅ Crecimiento futuro es lineal con datos, no exponencial

### Negativas
- ❌ Requiere CI/CD funcionando (sin CI, no hay derivados)
- ❌ Si CI falla, derivados no se actualizan
- ❌ Workflow más complejo: cambios deben pasar por automatización

### Riesgos
- **Riesgo**: CI falla silenciosamente, derivados quedan desactualizados
  - **Mitigación**: Workflow requiere pasar tests, validar metadatos, antes de mergear.

- **Riesgo**: GeoJSON cambio formato, visor viejo rompe
  - **Mitigación**: Versionamos el formato en la URL (v1, v2, etc.). Cambios van por minor/major semver.

### Alternativas Consideradas

- [x] **Commitear todo (status quo)**: repo crece monótonamente. Rechazado.
- [ ] **Regla del derivado**: elegida. Reduce bloat, una fuente de verdad.
- [x] **Almacenar derivados en R2/CDN sin commitear**: posible, pero más complejo. Pospuesto a Fase 3.

### Referencias

- [ADR-001: GeoPackage Versionado](ADR-001-maestro-gpkg.md) - maestro de datos
- [Fase 1: Implementación de CI/CD](../03-proceso/fases.md#fase-1-setup-ci)
