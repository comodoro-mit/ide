<p align="center">
  <img src="ide-visores/geoportal/img/logotipo.png" alt="Dirección General de Modernización e Investigación Territorial" height="70">
</p>

<h1 align="center">IDE Comodoro</h1>

<br>
Repositorio oficial de la IDE del Municipio de Comodoro Rivadavia, Chubut,
Argentina. Reúne, estandariza y publica la información geoespacial oficial del
municipio para que cualquier persona pueda consultarla, descargarla y
reutilizarla.

Responsable: Dirección General de
Modernización e Investigación Territorial.

---

## Qué es una IDE y por qué importa

IDERA, la Infraestructura de Datos Espaciales de la República Argentina,
define una IDE como *"un ámbito de trabajo colaborativo conformado por los
diferentes niveles de gobierno, cuyo objetivo es la estandarización y la
difusión del acceso a la información geoespacial del país"*.

La palabra clave es **estandarización**. Un municipio siempre tuvo datos
geoespaciales; lo que no siempre tuvo es una forma única de nombrarlos,
documentarlos y entregarlos. Sin eso, cada área guarda su propia versión de
"los barrios", nadie sabe cuál es la vigente, y el dato no sale del escritorio
donde se produjo.

Una IDE resuelve tres problemas concretos de la gestión local:

- **Una sola fuente autoritativa.** Para cada conjunto de datos hay un archivo
  maestro, con un identificador estable, y todo lo demás se deriva de él.
- **Interoperabilidad.** El dato se publica en formatos abiertos y con
  metadatos normalizados, así que lo puede leer otra área del municipio, la
  provincia, la Nación o cualquier vecino, sin pedir permiso ni conversiones.
- **Trazabilidad.** Cada cambio queda registrado y es auditable.

Esta IDE es además el nodo local que aporta al nodo provincial y, a través de
él, al catálogo federado de IDERA.

## Estándares que se cumplen

| Ámbito | Estándar | Dónde se aplica |
|---|---|---|
| Metadatos | Perfil de Metadatos para Datos Vectoriales v2.0 de IDERA | Formato XML para cada dataset |
| Metadatos | ISO 19115 / ISO 19139 | Formato de serialización de ese perfil |
| Categorías temáticas | `topicCategory` de ISO 19115 | Cada uno de los 14 prefijos temáticos mapea 1:1 a una categoría |
| Sistema de referencia | EPSG:5344, POSGAR 2007 / Argentina faja 2 | CRS de todos los archivos maestros |
| Sistema de referencia | EPSG:4326, WGS 84 | CRS de publicación, exigido por RFC 7946 para GeoJSON |
| Intercambio | GeoPackage (OGC) y GeoJSON (RFC 7946) | Formatos publicados |
| Licencia de datos | Creative Commons Atribución 4.0 | Declarada en el catálogo y en cada metadato |

La nomenclatura interna (identificadores, prefijos temáticos, nombres de
campo) está predefinida y **la valida el CI**: un
dataset que no la cumple no se publica.

## Flujo de trabajo

Un dataset nuevo recorre cuatro pasos. Los tres primeros son manuales y se
hacen una sola vez por dataset; el cuarto es automático y se repite en cada
push.

**1. Normalizar en QGIS.**

**2. Guardar el maestro y su metadato.**

**3. Declarar el dataset en el catálogo.**

**4. Commit y push a `main`.**

```
validar_catalogo.py      rechaza lo que no cumple la nomenclatura
derivar_catalogo.py      arma el catálogo completo (CSV y JSON)
generar_derivados.py     produce el GeoJSON en EPSG:4326
creador_metadata.py      produce el XML ISO 19139
armar_sitio.py           ensambla la carpeta que se publica
```

GitHub Actions corre esa cadena y GitHub Pages publica el resultado. Si algo
no cumple, el workflow falla y no se publica nada: el sitio en línea nunca
queda en un estado inválido.

## Estructura del repositorio

```
ide-datos/
  maestros/<tema>/     archivos maestros .gpkg + .qmd  (fuente autoritativa)
  catalogo/            catalogo.csv, la única carga manual
  derivados/           salidas generadas, no se versionan
  scripts/             el pipeline, standard library de Python solamente
ide-visores/
  geoportal/           la página principal: HTML, CSS, JS y parciales
  src/                 visores de mapa
docs/                  contexto, decisiones (ADR), proceso y detalle técnico
```

## Licencias

Código y datos son obras distintas y se licencian por separado:

- **Datos:** Creative Commons Atribución 4.0. Ver [LICENSE-DATOS.md](LICENSE-DATOS.md).
- **Código:** MIT. Ver [LICENSE](LICENSE).

## Documentación

El detalle del proyecto, las decisiones de arquitectura y el proceso de
transición están en [docs/](docs/README.md).
