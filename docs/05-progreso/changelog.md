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

### [2026-08-27] - Pipeline completo y geoportal en linea

### Completado
- ✅ Pipeline de 5 scripts cerrado y corriendo de punta a punta: `validar_catalogo.py`,
  `derivar_catalogo.py`, `generar_derivados.py`, `creador_metadata.py`, `armar_sitio.py`
- ✅ `creador_metadata.py` reescrito: ISO 19139 según el perfil IDERA v2.0, sin inventar
  elementos (lo que no tiene fuente se reporta como brecha, no se rellena)
- ✅ Geoportal en `ide-visores/geoportal/`: 5 páginas (index, datasets, visor,
  documentación, institucional) con parciales de header y pie
- ✅ Visor de mapas con Leaflet: 3 mapas base (Argenmap claro y oscuro del IGN,
  satelital de Esri), panel de capas y vista compartible por hash
- ✅ Reproyección 5344 a 4326 sin GDAL, verificada contra los dos motores
- ✅ Tercer dataset cargado: `cr-equ-playones-deportivos` (77 puntos)
- ✅ Changelog por dataset completo: los 3 datasets tienen el suyo en
  `ide-datos/catalogo/changelog/`
- ✅ Licencias separadas: código MIT, datos CC BY 4.0

### Estado del Repo
- Datasets publicados: 3 (`cr-adm-limites-barrios` 77 polígonos,
  `cr-equ-espacios-verdes` 383 polígonos, `cr-equ-playones-deportivos` 77 puntos)
- Validación: 0 errores, 11 avisos
- Sitio armado: 5 MB, 5 páginas, GPKG + GeoJSON + XML ISO + QMD por dataset
- Metadatos ISO: los 3 se generan, los 3 incompletos para cosecha (falta A8 y C1)

### Deuda tecnica abierta
- `frecuencia_actualizacion` vacía en los 3 datasets: bloquea el elemento A8 del
  perfil IDERA y con eso la cosecha del catálogo
- `url_descarga` sin definir: bloquea el elemento C1. La URL base la aporta
  GitHub Pages en el deploy, falta cablearla al catálogo
- Descripciones de 70 a 83 caracteres en los 3 datasets; la ficha institucional
  pide 200 como mínimo
- `<history>` vacío en los 3 `.qmd`: ningún dataset tiene el linaje documentado
- `<extent>` centinela en `cr-adm-limites-barrios` y `cr-equ-espacios-verdes`
- `nomenclatura.md` §10.2 quedó desactualizado: dice que el geoportal lee
  `catalogo.json` en el navegador, pero el listado se renderiza al publicar

### Proximos Pasos
1. Completar `frecuencia_actualizacion` en `catalogo.csv` para los 3 datasets
2. Cablear la URL base al catálogo para cerrar el elemento C1
3. Recalcular el `<extent>` y completar el `<history>` de los `.qmd` en QGIS
4. Ampliar las descripciones a 200 caracteres
5. Eliminar el scaffolding muerto de `ide-datos/.github/` e `ide-visores/.github/`

### Notas
- El orden de los scripts no es opcional: `armar_sitio.py` copia e indexa, nunca
  convierte. Corriéndolo solo, un dataset nuevo no llega al sitio aunque el
  catálogo ya lo declare
- Los workflows de CI viven en `.github/workflows/` en la raíz del repo, no dentro
  de `ide-datos/` ni de `ide-visores/`: es un solo repositorio

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
