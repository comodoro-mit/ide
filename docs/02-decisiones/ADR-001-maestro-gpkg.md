## ADR-001: GeoPackage Versionado en Git como Maestro de Datos

### Estado

- [x] Propuesto
- [x] Aceptado
- [ ] Deprecado
- [ ] Reemplazado por ADR-NNN

### Contexto

Con presupuesto cero, no podemos confiar en free tiers de bases de datos en la nube:
- Supabase: suspende tras una semana de inactividad
- Neon: escala a cero sin aviso previo
- Heroku: cobran desde 2025

Un maestro de datos que el proveedor puede apagar o suspender en cualquier momento **no es un maestro confiable**. Además:
- 23 datasets actuales (~8 MB de datos, sin duplicación)
- Presupuesto VPS solicitado en marzo 2025 nunca se aprobó
- Fases 0–4 deben ser 100% gratis con servicios que no se cierren

Alternativas descartadas:
- PostGIS en Supabase/Neon: inestable, suspensible
- SQLite: no es de propósito geoespacial
- Almacenamiento en JSON/GeoJSON: sin índices, búsqueda lenta

### Decisión

**Maestro de datos = GeoPackage (GPKG) versionado en Git.**

El GPKG es:
- Estándar OGC (abierto, portable)
- Formato SQLite (índices espaciales, transacciones)
- Versionable en Git (binario comprimido, diffs detectables con herramientas especializadas)
- Recuperable desde cualquier commit histórico

PostGIS actúa como **motor de análisis**, sincronizado *desde* el GPKG por CI/CD, no como maestro.

### Consecuencias

### Positivas
- ✅ Maestro de datos 100% bajo control institucional (Git, repo propio)
- ✅ Versionable: `git log` permite auditar qué cambió, cuándo y por quién
- ✅ Recuperable: cualquier versión histórica está en Git
- ✅ Costo: $0 para Fases 0–4 (solo GitHub)
- ✅ Portable: GPKG se abre con QGIS, ogr2ogr, libspatialite, etc.

### Negativas
- ❌ No permite concurrencia: solo un escritor a la vez (limitación del repositorio Git)
- ❌ Consultas dinámicas complejas: GPKG es más lento que PostGIS para análisis pesado
- ❌ Dificulta colaboración real-time: cambios deben ir por PR/merge, no instantáneos

### Riesgos
- **Riesgo**: El archivo GPKG crece > 100 MB en Git (repo se vuelve lento)
  - **Mitigación**: Regla del artefacto derivado → cero duplicación. Capa censal solo en GPKG, no en GeoJSON ni JS.
  - **Escalada (Fase 5)**: Si los datos crecen a >50 datasets, migramos a PostGIS + R2 (Cloudflare) para binarios grandes.

- **Riesgo**: Conflictos de merge si dos personas editan el GPKG simultáneamente
  - **Mitigación**: Procesos de revision clara (PR requerida). Una persona por dataset en la escritura.
  - **Escalada (Fase 5)**: Migración a PostGIS cuando la colaboración real-time sea necesaria.

- **Riesgo**: No hay respaldo automático
  - **Mitigación**: GitHub tiene backups. Además, usamos R2 (Cloudflare, 10 GB gratis) desde Fase 2 como respaldo.

### Alternativas Consideradas

- [x] **PostGIS en Supabase/Neon**: free tier inestable, suspensible. Rechazado.
- [x] **SQLite en Git**: posible, pero no tiene índices espaciales nativos. Rechazado.
- [ ] **GeoPackage en Git**: elegida. Estándar OGC, versionable, portable, gratis.
- [x] **Almacenamiento en GeoJSON/JSON en Git**: sin índices. Rechazado.

### Referencias

- [OGC GeoPackage Standard](https://www.geopackage.org/)
- [ADR-003: Cloudflare Pages para Host Estático](ADR-003-cloudflare-pages.md) — complementario
- Fase 5: Migración a PostGIS (condición: >50 datasets O >1 escritor concurrente O consulta dinámica)
