## Changelog

Log de cambios del proyecto. Se actualiza después de cada hito completado.

Formato: `## [YYYY-MM-DD] - Descripción`

---

### [Unreleased]

### Planificado (Fase 0)
- [ ] Diagnóstico completo del repo
- [ ] Estructura de documentación (ADRs 001-003)
- [ ] Migración a repo institucional

---

### [2026-08-21] - Inicio Fase 0

### Completado
- ✅ Documentación de transición iniciada
- ✅ Estructura de carpetas creada (`docs/01-05`)
- ✅ ADRs 001-003 redactados (maestro GPKG, artefactos derivados, Cloudflare Pages)
- ✅ Fases 0-5 planificadas (timeline hasta 2028-02-28)

### Estado del Repo
- Tamaño: 38 MB (datos + .git)
- Datasets: 23 lógicos
- Deuda técnica: 5 datasets sin maestro (transporte, barrios)
- Maestro actual: GPKG pretendido, pero datos duplicados en GeoJSON y JS

### Contexto
- Proyecto de Resolución IDE-CR activo (Notas 009/25, 010/25)
- Convenios: IDERA (2021), UNPSJB (2021), IGN (2022)
- Restricción: presupuesto cero para Fases 0-4, ~USD 120/año para Fase 5+
- Responsables: TBD (Ver [[riesgos.md#escalada-y-autoridades](03-proceso/riesgos.md#escalada-y-autoridades)])

### Próximos Pasos (Semana del 2026-08-28)
1. Validar GPKG maestro con GDAL/QGIS
2. Diagnosticar datasets duplicados
3. Crear .gitignore para derivados
4. Iniciar migración a repo institucional

### Notas
- Base de documentación lista para iteración por equipo
- No hay cambios de código aún, solo planeamiento y documentación

---

### Plantilla para Nuevos Entries

Copiar y completar después de cada hito:

```markdown
### [YYYY-MM-DD] - Descripción del Hito

### Completado
- ✅ Tarea 1
- ✅ Tarea 2
- ✅ Tarea N

### Cambios Detectados
- Dataset X: cambios en cantidad de registros o atributos
- Deuda técnica: hallazgos nuevos

### Validación
- CI: ✅ All tests passed (X/X)
- Manual review: ✅ (reviewer: @usuario)
- Tamaño repo: ABC MB → DEF MB
- Datasets: X → Y total

### Métricas
- Tiempo de fase: X semanas (planeado: Y semanas)
- Commits: N nuevos
- Issues cerrados: #1, #2, #3

### Issues/Riesgos Encontrados
- [ ] Issue #NNN: Descripción (Severidad: MEDIA)
- [ ] Risk RN-N: Descripción (Mitigation: ...)

### Próximos Pasos
1. Tarea A (asignado a: @usuario)
2. Tarea B (asignado a: @usuario)

### Responsable
@usuario

### Aprobaciones
- [ ] Revisor 1: @usuario1
- [ ] Revisor 2: @usuario2

### Referencias
- [ADR-NNN](02-decisiones/ADR-NNN.md) relacionada
- [Fases](03-proceso/fases.md) planeamiento
- Issue/PR #NNN

---
```

### Convenciones

### Estado de Tareas
- ✅ Completada
- ⏳ En progreso
- ❌ Bloqueada
- ⏹️ Pospuesta

### Severidad de Issues
- **CRÍTICA**: Proyecto parado, aprobación requerida para continuar
- **ALTA**: Retraso estimado > 1 semana, requiere plan B
- **MEDIA**: Retraso estimado 2-5 días, proceder con caution
- **BAJA**: Retraso estimado < 2 días, proceder normalmente

### Validación Obligatoria
Cada entry debe incluir:
- ✅ Tests pasados (CI)
- ✅ Review aprobada
- ✅ Tamaño del repo documentado
- ✅ Cambios de datos cuantificados

Sin esto, no se da por completado.

---

### Hitos Principales (Meta-Timeline)

| Fecha | Fase | Hito | Estado |
|-------|------|------|--------|
| 2026-09-30 | 0 | Repo institucional + docs | ⏳ |
| 2026-11-30 | 1 | CI/CD + 38 MB → 12 MB | ⏳ |
| 2027-01-31 | 2 | Deuda técnica resuelta | ⏳ |
| 2027-03-31 | 3 | Catálogo IDERA listo | ⏳ |
| 2027-05-31 | 4 | Hardening + team training | ⏳ |
| 2027-07-31 | 5 | PostGIS (si aplica) | ⏳ |

---

### Búsqueda de Entries Anteriores

```bash
# Ver últimas 10 entradas
git log --oneline docs/05-progreso/changelog.md | head -10

# Buscar entry específica
grep -A 20 "\[2026-09-15\]" docs/05-progreso/changelog.md

# Ver cuándo completamos cada fase
grep -E "^## \[.*\] - .*Fase [0-5]" docs/05-progreso/changelog.md
```

---

### Notas Generales

- Este archivo se commitea junto con ADRs y cambios de código
- Cada semana, asignar responsable de actualizar changelog el viernes
- Si cambio es significativo, notificar equipo en Slack para visibilidad
- Mantener histórico completo (no borrar entries viejas)
- Cada entry es un "snapshot" del estado en ese momento
