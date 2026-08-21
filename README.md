### Documentación de Transición - IDE Comodoro

Inicio del proyecto de transición: **agosto 2026**

### Estructura

- **[01-contexto/](01-contexto/)** — Contexto y objetivos del proyecto
- **[02-decisiones/](02-decisiones/)** — Architecture Decision Records (ADR) — cada decisión importante documentada
- **[03-proceso/](03-proceso/)** — Fases, timeline, riesgos y plan de contingencia
- **[04-tecnico/](04-tecnico/)** — Detalles técnicos de migración, testing y rollback
- **[05-progreso/](05-progreso/)** — Changelog y lecciones aprendidas (se actualiza regularmente)

### ADR

Un **Architecture Decision Record** es un documento que registra una decisión arquitectónica importante:
- **Por qué** se tomó (contexto y constraints)
- **Qué** se decidió
- **Cuáles fueron** las consecuencias y alternativas descartadas

Cada ADR es un archivo independiente en `02-decisiones/`. Ver [[ADR-001-maestro-gpkg.md](02-decisiones/ADR-001-maestro-gpkg.md)] como ejemplo.

### Cómo usar esta documentación

1. **Lee primero** `01-contexto/problema.md` y `01-contexto/objetivos.md`
2. **Consulta los ADRs** en `02-decisiones/` cuando necesites saber el "por qué" de una decisión
3. **Sigue el progreso** en `05-progreso/changelog.md`
4. **Revisa riesgos** en `03-proceso/riesgos.md` antes de cada fase
5. **Consulta lo técnico** en `04-tecnico/` para detalles de implementación

### Mantenimiento

- Cada ADR aprobado se commitea con un mensaje claro
- El CHANGELOG se actualiza en cada hito completado
- Las decisiones que cambian se marcan como "Depreciadas" con referencia al ADR que las reemplaza
