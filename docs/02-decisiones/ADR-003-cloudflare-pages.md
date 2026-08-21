## ADR-003: Cloudflare Pages para Host Estático (No Vercel)

### Estado

- [x] Propuesto
- [x] Aceptado
- [ ] Deprecado
- [ ] Reemplazado por ADR-NNN

### Contexto

Necesitamos hostear el geoportal (HTML, visor interactivo, catálogo).

Alternativas evaluadas:
- **Vercel (Hobby)**: plan gratuito restringe explícitamente a *"non-commercial, personal use only"*. Geoportal municipal es comercial → violación de términos. Rechazado.
- **GitHub Pages**: gratis, pero sin banda variable. Ideal para Fase 0–2 (sitio estático pequeño).
- **Cloudflare Pages**: gratis, sin topes de ancho de banda, R2 (10 GB gratis, egreso 0 desde CF), no tiene cláusula comercial.

Hoy usamos GitHub Pages. La pregunta es: ¿cuándo migrar?

### Decisión

**Fase 0–2: GitHub Pages (mientras sea posible)**
- Visor estático + GeoJSON vía API
- Costo: $0, sin setup extra
- Limitación: ~1 GB de ancho de banda/mes (suficiente para MVP)

**Fase 3 en adelante: Migración a Cloudflare Pages si aparece:**
- Dataset pesado (raster, PMTiles, MBTiles)
- O tráfico > 1 GB/mes estimado

**Por qué Cloudflare, no otra:**
- R2: 10 GB almacenamiento gratis, egreso gratis desde CF
- Pages: cero downtime deploys, CF Workers disponibles para lógica (Fase 4+)
- No hay cláusula comercial restrictiva
- Integración con GitHub → push → deploy automático

### Consecuencias

### Positivas
- ✅ GitHub Pages funciona hoy, costo 0
- ✅ Cloudflare cuando lo necesitemos, costo aún 0 (hasta 10 GB datos)
- ✅ R2 egreso gratis desde CF (no contabiliza como tráfico saliente)
- ✅ Workers habilitados para serverless en Fase 4 (consultas dinámicas, WFS)

### Negativas
- ❌ Migration de GitHub Pages → CF Pages requiere cambiar DNS/setup
- ❌ R2 pricing escalable: si superamos 10 GB, empezamos a pagar por almacenamiento

### Riesgos
- **Riesgo**: PMTiles / MBTiles sin servidor. CF Pages no ejecuta lógica por defecto
  - **Mitigación**: CF Workers ejecuta lógica (Fase 4). Costo: 10M requests/mes gratis.

- **Riesgo**: Tráfico impredecible. "Sin topes" = facturación potencial
  - **Mitigación**: Monitorear analíticos. Establecer alertas a nivel de uso.

### Alternativas Consideradas

- [x] **Vercel (Hobby)**: plan no permite comercial. Rechazado.
- [x] **AWS S3 + CloudFront**: costo mensual, más complejo. Rechazado (presupuesto cero).
- [ ] **Cloudflare Pages**: elegida. Gratis, sin restricciones comerciales, R2 integrado.
- [x] **Netlify**: similar a Vercel, pero con ancho de banda limitado. Rechazado.

### Referencias

- [Cloudflare Pages Pricing](https://pages.cloudflare.com/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [ADR-001: GeoPackage Maestro](ADR-001-maestro-gpkg.md) — los datos detrás del visor
- Fase 3: Migración a CF Pages (condición: dataset pesado O tráfico > 1 GB/mes)
