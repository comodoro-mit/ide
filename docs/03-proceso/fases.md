## Fases de la Transición

Cronograma: 6 fases, 18 meses (agosto 2026 - febrero 2028).

Presupuesto: $0 para Fases 0-4, ~USD 120/año para Fase 5 en adelante.

### Fase 0: Preparación (Agosto-Septiembre 2026)

**Objetivo**: Diagnosticar, documentar, migrar repo a institucional.

### Tareas
- [ ] Clonar repo personal a cuenta institucional
- [ ] Crear estructura de documentación (ADRs, changelog)
- [ ] Validar GPKG maestro con GDAL/QGIS
- [ ] Listar todos los datasets duplicados (transporte, barrios, censos)
- [ ] Calcular tamaño real de datos vs. derivados
- [ ] Setup .gitignore para excluir derivados

**Entregables**:
- Repositorio institucional (`municipalidad/ide` o equivalente)
- README + ADRs 001-003 aprobados
- Plan de deuda técnica (cinco datasets sin maestro)

**Duración**: ~6 semanas

---

### Fase 1: Setup CI/CD (Octubre-Noviembre 2026)

**Objetivo**: Automatizar generación de derivados, validación de metadatos.

### Tareas
- [ ] Configurar GitHub Actions
- [ ] Script: GPKG → GeoJSON (ogr2ogr)
- [ ] Script: GPKG → JS (geojson_to_js.py mejorado)
- [ ] Script: GPKG + CSV metadatos → ISO 19115 XML
- [ ] Validador: ISO 19115 contra perfil IDERA
- [ ] Tests: geometría válida, CRS correcto, no registros duplicados
- [ ] Workflow: PR requiere tests pasados, merge genera derivados

**Entregables**:
- `.github/workflows/build.yml` funcional
- Derivados en GeoJSON y JS regenerados correctamente
- Catálogo de metadatos válido (ISO 19115)
- 38 MB repo → 12-15 MB (regla del derivado aplicada)

**Duración**: ~8 semanas

---

### Fase 2: Resolver Deuda Técnica (Diciembre 2026-Enero 2027)

**Objetivo**: Migrar cinco datasets sin maestro (transporte, barrios) al GPKG.

### Tareas
- [ ] Transporte (líneas): GeoJSON → GPKG, validar topología
- [ ] Transporte (paradas): GeoJSON → GPKG, validar attributes
- [ ] Barrios: barrios_data.js → GPKG, preservar atributos
- [ ] Barrios nivel instrucción: barrios_nivel_instruccion_data.js → GPKG
- [ ] Barrios sexo: barrios_sexo_data.js → GPKG
- [ ] Deprecar archivos JavaScript/GeoJSON viejos (marcar, no eliminar)
- [ ] CI regenera derivados automáticamente

**Entregables**:
- GPKG maestro con 23 datasets consolidados
- Cero datos en .js (solo generados por CI)
- Histórico preservado (ramas viejas accesibles)
- Repo ~10 MB (sin derivados)

**Duración**: ~6 semanas

---

### Fase 3: Catálogo Mejorado (Febrero-Marzo 2027)

**Objetivo**: Catálogo de metadatos conformes a IDERA, listo para federar.

### Tareas
- [ ] Google Sheets: formulario de campos manuales (13 campos)
- [ ] Script: Sheets → CSV
- [ ] CI: CSV + GPKG → ISO 19115 + JSON + HTML catalog
- [ ] Validación: cada cambio en Sheets triggerear CI
- [ ] Cloudflare Pages setup (si tráfico > 1 GB/mes actual)
- [ ] R2 setup para respaldo de GPKG y derivados
- [ ] Tests de federación IDERA (envelope XML válido)

**Entregables**:
- Catálogo HTML navegable (searchable, filtrable)
- ISO 19115 XML válido para cada dataset
- Solicitud de federación en IDERA lista
- R2 con respaldo sincronizado por CI

**Duración**: ~7 semanas

---

### Fase 4: Optimización y Hardening (Abril-Mayo 2027)

**Objetivo**: Performance, seguridad, auditoría, documentación.

### Tareas
- [ ] Compresión de GPKG (gzip, reducir .git size)
- [ ] Shallow clone para nuevos contribidores (reducir descarga inicial)
- [ ] Signing de commits (GPG)
- [ ] Audit log: quién cambió qué, cuándo, por qué
- [ ] Branch protection rules (requiere 1 review, tests pasados)
- [ ] Documentación de "cómo contribuir"
- [ ] Benchmark: tiempo GPKG → derivados, tamaño vs. métrica
- [ ] Migración de Team (si necesario): permisos finales

**Entregables**:
- Repo hardened, auditable, producción-ready
- Team training completado
- SLA documentado (RTO, RPO)

**Duración**: ~6 semanas

---

### Fase 5: PostGIS y Escalabilidad (Junio 2027+)

**Objetivo**: Prepararse para escalabilidad cuando sea necesario. Ejecutar SOLO si:
- ✅ Más de un área escribiendo con concurrencia, O
- ✅ Más de ~50 datasets, O
- ✅ Consulta dinámica por atributo (WFS, búsqueda en visor)

### Tareas (si se necesita)
- [ ] Provisionar VPS (4-8 GB RAM, 2 cores, ~USD 10/mes)
- [ ] PostGIS en VPS
- [ ] CI: GPKG ↔ PostGIS bidireccional (maestro sigue siendo GPKG)
- [ ] WFS endpoint (OGC Web Feature Service)
- [ ] CF Workers para proxy de consultas dinámicas
- [ ] Load testing

**Costo**: ~USD 120/año (VPS) + Cloudflare Pro si necesita (USD 20/mes)

**Duración**: ~8 semanas (solo si se activa)

---

### Hitos de Transición

| Fecha | Fase | Hito |
|-------|------|------|
| 2026-09-30 | 0 | Repo institucional, ADRs aprobados |
| 2026-11-30 | 1 | CI/CD funcionando, 38 MB → 12 MB |
| 2027-01-31 | 2 | Deuda técnica resuelta, GPKG maestro único |
| 2027-03-31 | 3 | Catálogo IDERA listo, solicitud federación |
| 2027-05-31 | 4 | Hardening, SLA, team training |
| 2027-06+ | 5 | PostGIS (solo si se necesita) |

---

### Cómo usar esta sección

- **Para planificación**: estima recursos por fase, asigna personas
- **Para seguimiento**: actualiza estado de tareas en CHANGELOG
- **Para cambios**: si fase toma más tiempo, ajusta timeline en Fase siguiente (no retrases todas)
- **Decisiones por fase**: cada fase puede generar nuevos ADRs si aparecen cambios en constraints
