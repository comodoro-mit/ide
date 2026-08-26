## Riesgos y Planes de Contingencia

Identificación de riesgos por fase, probabilidad, impacto, y plan B.

---

### Riesgos Críticos (Aplican a Todas las Fases)

### R1: Pérdida de Acceso al Repositorio Institucional

**Descripción**: Cuenta del repositorio se desactiva, permisos se pierden, o no se puede hacer push.

**Probabilidad**: Media (cambios de personal, auditoría de accesos)
**Impacto**: Crítico (trabajo paralizado, no se puede mergear)

**Plan B**:
1. Maintain un respaldo en GitHub (sync automático a `municipalidad-backup/ide`)
2. Permisos: mínimo 3 personas con acceso administrativo (no una)
3. Documentación de recuperación en el repo (README → "Acceso de Emergencia")
4. R2 respaldo sincronizado por CI cada hora

**Dueño del riesgo**: DGMIT (IT/administrador repo)

---

### R2: Maestro de Datos (GPKG) Corrompido

**Descripción**: Archivo GPKG queda ilegible, índices corruptos, o valores inválidos no detectados.

**Probabilidad**: Baja (ocurre si no hay validación en CI)
**Impacto**: Crítico (datos no recuperables sin rollback manual)

**Plan B**:
1. CI valida cada cambio con GDAL (ogrinfo, ogr2ogr test)
2. Git history permite rollback a commit anterior en segundos
3. R2 mantiene snapshots diarios (Fase 3)
4. Backup offline en máquina local cada semana (responsable: TBD)

**Prevención**:
- Tests obligatorios en CI:
  - `ogrinfo <GPKG>` no retorna error
  - Cantidad de registros por capa conocida
  - Proyección es EPSG:5344
  - Geometría válida (no self-intersecting)

**Dueño del riesgo**: Desarrollador responsable de CI

---

### R3: Metadatos No Conformes a ISO 19115

**Descripción**: IDERA rechaza solicitud de federación porque metadatos no cumplen estándar.

**Probabilidad**: Media (creador_metadata.py genera falsos)
**Impacto**: Alto (retrasa federación 4-8 semanas)

**Plan B**:
1. Validador ISO 19115 integrado en CI antes de Fase 3
2. Template de metadatos correcto documentado
3. Revisión manual por especialista IDERA (contacto: TBD) antes de enviar
4. Iteración rápida (si IDERA pide cambios, aplicar dentro de semana)

**Dueño del riesgo**: Especialista en metadatos (UNPSJB?, IGN?)

---

### Riesgos por Fase

### Fase 0: Preparación

**R0-1: Documentación incompleta o ambigua**

**Descripción**: ADRs no quedan claros, equipo no entiende decisiones.

**Probabilidad**: Media | **Impacto**: Medio (confusión, retrasos)

**Plan B**:
- ADR debe tener ejemplos concretos, no solo teoría
- Review obligatorio por 2+ personas antes de mergear
- Si hay dudas, abrir issue en repo con preguntas específicas

---

**R0-2: Repo personal no se migra correctamente**

**Descripción**: Histórico se pierde, commits duplicados, o referencias rotas.

**Probabilidad**: Baja | **Impacto**: Crítico (historia del proyecto se pierde)

**Plan B**:
- Usar `git remote add upstream <repo-nuevo>` + `git push --mirror`
- Validar que todos los commits, branches y tags estén en el nuevo repo
- Mantener repo viejo como "archive" (readonly) con notice de redirección

---

### Fase 1: Setup CI/CD

**R1-1: GitHub Actions falla silenciosamente**

**Descripción**: Workflow en `.github/workflows/build.yml` no ejecuta o ejecuta pero no falla cuando debería.

**Probabilidad**: Media | **Impacto**: Alto (derivados desactualizados, nadie lo nota)

**Plan B**:
- Todos los jobs retornan exit code != 0 si falla algo
- Notificación a Slack/email si build falla
- Test manual cada PR antes de mergear (reviewer ejecuta localmente)

---

**R1-2: GPKG→GeoJSON genera formato incorrecto**

**Descripción**: ogr2ogr cambia propiedades, CRS se pierden, o tipo de geometría es incorrecto.

**Probabilidad**: Baja | **Impacto**: Medio (visor no renderiza capa)

**Plan B**:
- Test: GeoJSON resultante se carga en QGIS/Leaflet sin error
- Test: cantidad de registros y propiedades son iguales antes/después
- Script con `--skipfailures` deshabilitado (falla si hay error)

---

**R1-3: Repositorio crece > 100 MB durante Fase 1**

**Descripción**: Git sigue siendo lento a pesar de .gitignore correcto.

**Probabilidad**: Baja | **Impacto**: Medio (clones lentos, CI tarda más)

**Plan B**:
- Si ocurre: hacer `git gc` aggressive (compactación)
- Shallow clone por defecto para nuevos contribidores
- Considerar `git-lfs` solo para GPKG si crece > 50 MB

---

### Fase 2: Deuda Técnica

**R2-1: Datos en transporte/barrios tiene inconsistencias**

**Descripción**: Al migrar GeoJSON/JS a GPKG, se descubren duplicados, geometría inválida o atributos faltantes.

**Probabilidad**: Media | **Impacto**: Medio (validación retrasa 1-2 semanas)

**Plan B**:
- Inspeccionar cada capa antes de migrar (con QGIS o `ogrinfo`)
- Documentar inconsistencias encontradas en issue
- Decidir si corregir datos o preservar estado actual (con nota en metadatos)

---

**R2-2: Visor histórico rompe después de deprecar .js**

**Descripción**: Visor antiguo depende de datos en `barrios_data.js`, al removerlo, visor no funciona.

**Probabilidad**: Alta | **Impacto**: Medio (visor offline temporalmente)

**Plan B**:
- No deprecar archivos, solo marcar como deprecated
- Mantener ramas viejas accesibles: tag `v1.0-legacy` apunta a último commit con visor viejo
- GeoJSON derivado es drop-in replacement para visor nuevo (¿requiere cambios?)

---

### Fase 3: Catálogo Mejorado

**R3-1: IDERA solicitud rechazada**

**Descripción**: Metadatos pasan validación ISO 19115 local, pero IDERA pide cambios.

**Probabilidad**: Media | **Impacto**: Alto (retrasa 4-8 semanas)

**Plan B**:
- Contactar IDERA con borrador antes de envío formal
- Ciclo iterativo rápido (si piden cambios, hacer en semana)
- Tener backup plan: si IDERA no responde, publicar catálogo en IGN directamente (¿posible?)

---

**R3-2: Cloudflare Pages migration falla**

**Descripción**: DNS updates rompen, visor offline, o R2 no sincroniza.

**Probabilidad**: Baja | **Impacto**: Alto (usuarios sin acceso)

**Plan B**:
- Hacer migration en fin de semana, con rollback plan listo
- Prueba en staging (subdomain) antes de migrar producción
- Keep GitHub Pages activo en paralelo durante 2 semanas (fallback)

---

### Fase 4: Hardening

**R4-1: Team no está trained**

**Descripción**: Personas nuevo llegan en Fase 4, no saben cómo usar repo, CI o makegit workflow.

**Probabilidad**: Media | **Impacto**: Medio (productividad baja, errores)

**Plan B**:
- Documentación "Cómo Contribuir" con ejemplos paso a paso
- Sesión de training de 2 horas (repo, CI, commit message, PR review)
- Pairing la primero PR de cada persona (peer review obligatorio)

---

**R4-2: GPG signing falla o llave se pierde**

**Descripción**: Alguien pierde su clave GPG privada, o GitHub no valida firma.

**Probabilidad**: Baja | **Impacto**: Bajo (commits no firmados, no es bloqueador)

**Plan B**:
- GPG signing es nice-to-have, no bloqueador
- Si alguien lo necesita, contactar GitHub docs para recuperar
- Fallback: usar SSH keys en lugar de GPG si hay problemas

---

### Fase 5: PostGIS (Condicional)

**R5-1: Sincronización GPKG ↔ PostGIS desincroniza**

**Descripción**: Una escritura es local en GPKG pero no se replica a PostGIS, o vice versa.

**Probabilidad**: Media | **Impacto**: Crítico (datos inconsistentes)

**Plan B**:
- Maestro sigue siendo GPKG (no PostGIS)
- CI sincroniza en una sola dirección: GPKG → PostGIS (no bidireccional)
- Test: consulta a PostGIS retorna misma cantidad de registros que GPKG
- Monitorear lag de replicación (SLA: < 1 hora)

---

**R5-2: VPS se queda sin espacio**

**Descripción**: Base de datos PostGIS crece > disk available, inserciones fallan.

**Probabilidad**: Media | **Impacto**: Alto (escrituras paradas)

**Plan B**:
- Alertas de monitoreo cuando disk > 80%
- Escalada: upgrade VPS o limpieza de datos viejos (con ADR primero)
- Backup diario en R2 (accesible en 30 min si falla)

---

### Matriz de Riesgos

| Riesgo | Probabilidad | Impacto | Prioridad | Plan B |
|--------|--------------|---------|-----------|--------|
| R1: Repo inaccesible | Media | Crítico | **CRÍTICA** | Respaldo + permisos distribuidos |
| R2: GPKG corrompido | Baja | Crítico | **CRÍTICA** | Validación CI + Git rollback |
| R3: Metadatos ISO fallan | Media | Alto | **ALTA** | Validator integrado + review manual |
| R0-1: Docs ambiguas | Media | Medio | **MEDIA** | Review + ejemplos concretos |
| R0-2: Migración incompleta | Baja | Crítico | **MEDIA** | Mirror + validación tags |
| R1-1: CI falla silenciosa | Media | Alto | **ALTA** | Notificaciones + test manual |
| R1-2: GeoJSON format error | Baja | Medio | **MEDIA** | Validación formato + test carga |
| R1-3: Repo crece > 100 MB | Baja | Medio | **MEDIA** | git gc + shallow clone |
| R2-1: Datos inconsistentes | Media | Medio | **MEDIA** | Inspección previa + doc issues |
| R2-2: Visor rompe | Alta | Medio | **MEDIA** | Tags legacy + GeoJSON drop-in |
| R3-1: IDERA rechaza | Media | Alto | **ALTA** | Pre-review + ciclo iterativo rápido |
| R3-2: CF Pages migration falla | Baja | Alto | **MEDIA** | Staging + rollback + fallback GH Pages |
| R4-1: Team sin training | Media | Medio | **MEDIA** | Docs + sesión training + pairing |
| R4-2: GPG key pierde | Baja | Bajo | **BAJA** | GPG optional, SSH fallback |
| R5-1: PG desincroniza | Media | Crítico | **ALTA** (Fase 5) | Maestro GPKG, sync one-way |
| R5-2: VPS sin espacio | Media | Alto | **ALTA** (Fase 5) | Alertas monitoreo + backup R2 |

---

### Escalada y Autoridades

- **Riesgos CRÍTICOS**: reportar a director DGMIT, pause work si es necesario
- **Riesgos ALTOS**: reportar a responsable Fase, crear ADR si cambia decisión
- **Riesgos MEDIOS**: crear issue en repo, resolver en semana siguiente
- **Riesgos BAJOS**: documentar en CHANGELOG, resolver cuando sea posible

### Contactos de Emergencia

- DGMIT IT: TBD
- IDERA responsable: TBD
- IGN contacto: TBD
- Especialista Git/CI: TBD
