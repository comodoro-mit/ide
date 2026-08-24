### Documentación - IDE Comodoro

Inicio del proyecto de transición: **agosto 2026**

### Estructura

- **[docs/01-contexto/](docs/01-contexto/)** — Contexto y objetivos del proyecto
- **[docs/02-decisiones/](docs/02-decisiones/)** — Architecture Decision Records (ADR) — cada decisión importante documentada
- **[docs/03-proceso/](docs/03-proceso/)** — Fases, timeline, riesgos y plan de contingencia
- **[docs/04-tecnico/](docs/04-tecnico/)** — Detalles técnicos de migración, testing y rollback
- **[docs/05-progreso/](docs/05-progreso/)** — Changelog y lecciones aprendidas (se actualiza regularmente)

### Architecture Decision Record

Documento que registra una decisión arquitectónica importante:
- **Por qué** se tomó (contexto y constraints)
- **Qué** se decidió
- **Cuáles fueron** las consecuencias y alternativas descartadas

Cada ADR es un archivo independiente en `docs/02-decisiones/`. Ver [ADR-001-maestro-gpkg.md](docs/02-decisiones/ADR-001-maestro-gpkg.md) como ejemplo.

### Cómo usar esta documentación

1. **Leer primero** `docs/01-contexto/problema.md` y `docs/01-contexto/objetivos.md`
2. **Consultar los ADR** en `docs/02-decisiones/` cuando necesites saber el "por qué" de una decisión
3. **Seguir el progreso** en `docs/05-progreso/changelog.md`
4. **Revisar riesgos** en `docs/03-proceso/riesgos.md` antes de cada fase
5. **Consultar lo técnico** en `docs/04-tecnico/` para detalles de implementación

### Mantenimiento

- Cada ADR aprobado se commitea con un mensaje claro
- El CHANGELOG se actualiza en cada hito completado
- Las decisiones que cambian se marcan como "depreciadas" con referencia al ADR que las reemplaza

### Flujo de trabajo

Un dataset nuevo se normaliza primero en QGIS siguiendo `propuesta/nomenclatura.md` (CRS 5344, `snake_case`, `id` estable con formato `cr-<tema>-<entidad>`), se completan a mano los campos del catálogo en `ide-datos/catalogo/catalogo.csv` y el resto (CRS, geometría, bbox, checksum, etc.) lo calculan los scripts, nunca se tipea. Ese catálogo alimenta el pipeline: `generar_derivados.py` produce los formatos publicados que consumen los visores.

Los commits se agrupan por tipo de cambio (config, docs, código) en vez de un commit monolítico, y siguen conventional commits en inglés y breves (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`). Cada hito se commitea por separado.

Al pushear a `main`, el CI de GitHub Actions valida el catálogo y regenera los derivados, y GitHub Pages publica el resultado. El repo vive en [github.com/comodoro-mit/ide](https://github.com/comodoro-mit/ide) y su historial funciona como auditoría del proyecto: cada commit es un snapshot consultable de qué cambió y cuándo.
