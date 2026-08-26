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
- **GitHub Pages**: gratis, sin setup extra.
- **Cloudflare Pages**: gratis, sin topes de ancho de banda, R2 (10 GB gratis, egreso 0 desde CF), no tiene cláusula comercial.

La pregunta es: ¿cuándo migrar?

### Límites reales (corregido 2026-08-25)

La versión original de este ADR decía que GitHub Pages tenía "~1 GB de ancho de
banda/mes". **Era incorrecto**: confundía el tope de tamaño del sitio con el de
tráfico. Los límites publicados son:

| | GitHub Pages | Cloudflare Pages (gratis) |
|---|---|---|
| Ancho de banda | 100 GB/mes (soft) | sin tope |
| Tamaño del sitio | **1 GB** | sin tope declarado |
| Tamaño por archivo | - | **25 MiB** (más grande va a R2) |
| Cantidad de archivos | - | 20.000 |
| Builds | 10/hora (no aplica usando Actions) | 500/mes |

Los dos aprietan por lados distintos, y eso cambia el criterio de migración:

- **GitHub Pages** aprieta por **volumen total**. Un portal que publica
  GeoPackages llega al giga antes de lo que parece.
- **Cloudflare Pages** aprieta por **archivo individual**. Una capa de catastro
  de más de 25 MiB no entra y hay que servirla desde R2.

El tráfico, que era el disparador original, resultó el límite menos
restrictivo: 100 GB/mes es mucho más de lo que va a mover este geoportal.

Sobre la cláusula comercial: los términos de GitHub Pages prohíben usarlo como
hosting gratuito para *"your online business, e-commerce site, or any other
website that is primarily directed at either facilitating commercial
transactions or providing commercial SaaS"*. Un portal municipal de datos
abiertos no es ninguna de esas cosas, así que no le aplica la objeción que sí
descartó a Vercel.

### Decisión

**Fase 0-2: GitHub Pages**
- Costo $0 y sin cuenta nueva: se activa desde la configuración del repositorio
  que ya existe.

**Fase 3 en adelante: migración a Cloudflare Pages cuando aparezca:**
- El sitio publicado acercándose a 1 GB, **o**
- Un dataset pesado (raster, PMTiles, MBTiles) que además obligue a usar R2

**Corolario de implementación**: `publicar.yml` separa el job que arma la
carpeta `sitio/` del job que la despliega. El primero no sabe nada del host;
migrar es reemplazar el segundo. Como la decisión de host no condiciona nada
más del pipeline, no hace falta apurarla.

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

- [GitHub Pages: límites de uso](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [Cloudflare Pages: límites](https://developers.cloudflare.com/pages/platform/limits/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [ADR-001: GeoPackage Maestro](ADR-001-maestro-gpkg.md) - los datos detrás del visor
- Fase 3: migración a CF Pages (condición: sitio cerca de 1 GB **o** dataset pesado)
