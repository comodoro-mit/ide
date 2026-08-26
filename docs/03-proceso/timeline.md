## Timeline Detallado

Fechas calendario base: agosto 2026 - febrero 2028 (18 meses).

Zona horaria: Argentina (UTC-3, America/Buenos_Aires).

### Fase 0: Preparación
**Inicio**: 2026-08-21 | **Fin**: 2026-09-30

| Semana | Tarea | Responsable | Fecha Límite |
|--------|-------|-------------|--------------|
| 1 (ago 21-27) | Diagnosticar repo, validar GPKG maestro | TBD | 2026-08-27 |
| 2 (ago 28-sep 3) | Crear documentación, ADRs 001-003 | TBD | 2026-09-03 |
| 3 (sep 4-10) | Setup .gitignore, listar datasets duplicados | TBD | 2026-09-10 |
| 4 (sep 11-17) | Migración a repo institucional, setup inicial | TBD | 2026-09-17 |
| 5 (sep 18-24) | Validación, tests manuales, review | TBD | 2026-09-24 |
| 6 (sep 25-30) | Hito: Repo institucional + docs listos | TBD | **2026-09-30** |

---

### Fase 1: Setup CI/CD
**Inicio**: 2026-10-01 | **Fin**: 2026-11-30

| Semana | Tarea | Responsable | Fecha Límite |
|--------|-------|-------------|--------------|
| 7-8 (oct 1-14) | GitHub Actions setup, scripts GPKG→GeoJSON | TBD | 2026-10-14 |
| 9-10 (oct 15-28) | Validadores metadatos, tests geometría | TBD | 2026-10-28 |
| 11-12 (oct 29-nov 11) | Workflow completo (PR→build→merge) | TBD | 2026-11-11 |
| 13-14 (nov 12-25) | Optimización, documentación CI | TBD | 2026-11-25 |
| 15 (nov 26-30) | Hito: 38 MB → 12 MB, derivados OK | TBD | **2026-11-30** |

---

### Fase 2: Deuda Técnica
**Inicio**: 2026-12-01 | **Fin**: 2027-01-31

| Semana | Tarea | Responsable | Fecha Límite |
|--------|-------|-------------|--------------|
| 16-17 (dic 1-14) | Transporte (líneas, paradas) → GPKG | TBD | 2026-12-14 |
| 18-19 (dic 15-28) | Barrios (tres datasets) → GPKG | TBD | 2026-12-28 |
| 20 (dic 29-ene 4) | Feriados; revisión, ajustes | TBD | 2027-01-04 |
| 21-22 (ene 5-18) | Deprecación de archivos viejos, CI regenera | TBD | 2027-01-18 |
| 23 (ene 19-25) | Validación, tests historiales | TBD | 2027-01-25 |
| 24 (ene 26-31) | Hito: GPKG maestro único, repo 10 MB | TBD | **2027-01-31** |

---

### Fase 3: Catálogo Mejorado
**Inicio**: 2027-02-01 | **Fin**: 2027-03-31

| Semana | Tarea | Responsable | Fecha Límite |
|--------|-------|-------------|--------------|
| 25-26 (feb 1-14) | Google Sheets formulario, script Sheets→CSV | TBD | 2027-02-14 |
| 27-28 (feb 15-28) | CI: CSV + GPKG → ISO 19115 + HTML | TBD | 2027-02-28 |
| 29-30 (mar 1-14) | Cloudflare Pages migration (si aplica), R2 setup | TBD | 2027-03-14 |
| 31 (mar 15-21) | Tests federación IDERA, preparar solicitud | TBD | 2027-03-21 |
| 32 (mar 22-31) | Hito: Catálogo listo, solicitud IDERA | TBD | **2027-03-31** |

---

### Fase 4: Hardening
**Inicio**: 2027-04-01 | **Fin**: 2027-05-31

| Semana | Tarea | Responsable | Fecha Límite |
|--------|-------|-------------|--------------|
| 33-34 (abr 1-14) | Compresión GPKG, shallow clone, GPG signing | TBD | 2027-04-14 |
| 35-36 (abr 15-28) | Branch protection, audit log | TBD | 2027-04-28 |
| 37-38 (abr 29-may 12) | Documentación "cómo contribuir", training | TBD | 2027-05-12 |
| 39-40 (may 13-26) | Benchmarks, SLA, permisos finales | TBD | 2027-05-26 |
| 41 (may 27-31) | Hito: Producción-ready, team trained | TBD | **2027-05-31** |

---

### Fase 5: PostGIS (Condicional)
**Inicio**: 2027-06-01 | **Duración**: ~8 semanas (solo si se necesita)

| Semana | Tarea | Responsable | Fecha Límite |
|--------|-------|-------------|--------------|
| 42-43 (jun 1-14) | Evaluación si se necesita (>50 datasets? concurrencia?) | TBD | 2027-06-14 |
| 44-47 (jun 15-jul 12) | VPS, PostGIS setup, GPKG↔PG sync | TBD | 2027-07-12 |
| 48-49 (jul 13-26) | WFS endpoint, CF Workers, load testing | TBD | 2027-07-26 |
| 50 (jul 27-31) | Hito: PostGIS en prod (si se activó) | TBD | **2027-07-31** |

---

### Notas de Planificación

### Factores de ajuste

- **Feriados argentinos**: semanas del 21/08 (Revolución de Mayo), 20/06 (Bandera), 25/05, 25/12, 01/01 reducen disponibilidad
- **Revisiones externas**: IDERA puede tardar 4-8 semanas en revisar solicitud de federación (ajustar Fase 3 si es necesario)
- **Dependencias**: Fase N depende de Fase N-1 completada. No iniciar Fase siguiente si hito anterior no se cerró

### Cambios a timeline

Si una fase toma más tiempo:
- Retrasa solo esa fase, no las siguientes (reduce scope o extiende duración)
- Documenta cambio en ADR si afecta decisiones arquitectónicas
- Actualiza CHANGELOG

Ejemplo: si Fase 1 toma 12 semanas en lugar de 8:
- Fase 2 se mueve de 2026-12-01 a 2026-12-15 (+2 semanas)
- No retrases Fase 3 si puedes comprimirla

### Validación de hitos

Cada hito requiere:
- ✅ Tareas completadas (100%)
- ✅ Tests pasados (CI green)
- ✅ Documentación actualizada (CHANGELOG, ADRs si aplica)
- ✅ Review de 1+ persona (branch protection)
- ✅ Merge a `main`

Sin estos, el hito no se da por cerrado.

---

### Slack/Asyncronía

- Toda comunicación en repo (issues, PRs, commits)
- Reuniones semanales opcionales para sincronizar (jueves 10:00 ART?)
- Reportes de progreso en CHANGELOG cada viernes
