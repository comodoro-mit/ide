/* Map viewer for the IDE Comodoro geoportal.
 *
 * One viewer for every layer: the base map is fixed and the panel toggles the
 * published GeoJSON on and off. Each layer is fetched the first time it is
 * switched on and kept in memory, so nothing downloads until somebody asks.
 */

(function () {
  "use strict";

  var contenedor = document.getElementById("mapa");
  if (!contenedor || typeof window.L === "undefined") return;

  var CENTRO = [-45.846, -67.496];
  var ZOOM = 12;

  var CREDITO_IGN =
    'Mapa base <a href="https://www.ign.gob.ar/">Instituto Geográfico Nacional</a> + ' +
    '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  var CREDITO_ESRI =
    'Imágenes satelitales <a href="https://www.esri.com/">Esri</a>, Maxar, Earthstar Geographics';

  // IGN tile services. {-y} is Leaflet's inverted row for a TMS grid.
  var BASES = {
    claro: {
      url: "https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{z}/{x}/{-y}.png",
      credito: CREDITO_IGN,
      maxZoom: 20
    },
    oscuro: {
      url: "https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/argenmap_oscuro@EPSG%3A3857@png/{z}/{x}/{-y}.png",
      credito: CREDITO_IGN,
      maxZoom: 20
    },
    satelital: {
      url: "https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      credito: CREDITO_ESRI,
      maxZoom: 19
    }
  };

  // Layer colours, one per mode: the dark base needs a lighter stroke.
  var TRAZOS = {
    claro: { color: "#134768", fillColor: "#2f7fae" },
    oscuro: { color: "#7fd0f5", fillColor: "#7fd0f5" },
    satelital: { color: "#ffd166", fillColor: "#ffd166" }
  };

  // The opening view is the whole city and it stays put. Turning a layer on
  // never re-frames the map: only the user moves it, by panning, zooming, or
  // pressing the reset button.
  var mapa = L.map(contenedor, {
    center: CENTRO,
    zoom: ZOOM,
    zoomControl: false,
    attributionControl: false
  });

  L.control.scale({ imperial: false, position: "bottomleft" }).addTo(mapa);

  var oscuro = false;
  var satelital = false;
  var base = null;

  function modoActual() {
    if (satelital) return "satelital";
    return oscuro ? "oscuro" : "claro";
  }

  function pintarBase() {
    var modo = modoActual();
    var config = BASES[modo];
    if (base) mapa.removeLayer(base);
    base = L.tileLayer(config.url, { maxZoom: config.maxZoom }).addTo(mapa);
    base.bringToBack();

    var creditos = document.getElementById("creditos");
    if (creditos) {
      creditos.innerHTML =
        config.credito +
        ' &middot; Capas: Municipalidad de Comodoro Rivadavia, ' +
        '<a href="https://creativecommons.org/licenses/by/4.0/deed.es">CC BY 4.0</a>' +
        ' &middot; <a href="https://leafletjs.com/">Leaflet</a>';
    }

    contenedor.classList.toggle("mapa-oscuro", modo === "oscuro");
    var lienzo = contenedor.parentNode;
    if (lienzo) lienzo.classList.toggle("oscuro", modo !== "claro");
    repintarCapas(TRAZOS[modo]);
  }

  // --- popups

  /* Every field shows by default. A layer published tomorrow gets a working
   * popup with nothing to configure, which is the point: a whitelist would
   * have to be maintained per layer, and there is no field common to all of
   * them anyway (playones has no `nombre`).
   *
   * Three rules keep that from looking raw, and none of them is layer
   * specific.
   */

  // 1. Internal keys, plus the coordinates: the map is already showing you
  //    where the thing is.
  var OCULTOS = ["id", "fid", "latitud", "longitud"];

  // 2. One global dictionary, not one per layer: "barrio" means the same in
  //    every dataset. A field with no entry here falls back to its own column
  //    name, so an unknown field degrades instead of disappearing.
  var ALIAS = {
    nombre: "Nombre",
    tipo: "Tipo",
    cat: "Categoría",
    barrio: "Barrio",
    calle: "Calle",
    interseccion: "Intersección",
    obs: "Observaciones",
    area_m2: "Superficie",
    zona: "Zona",
    circ: "Circunscripción",
    sector: "Sector"
  };

  /* The one per layer override, and it is optional: a layer with no entry
   * here still gets a working popup. Only for fields that are meaningless to
   * the public, never to tidy a layer that simply has many fields.
   */
  var OCULTOS_POR_CAPA = {
    // Internal cadastral codes. Bare numbers with no legend to read them by,
    // and this is the base layer: the name is the whole point.
    "cr-adm-limites-barrios": ["zona", "circ", "sector"]
  };

  // 3. Empty is judged per feature, not per field: a playón with no remarks
  //    drops the row, one with remarks keeps it.
  function vacio(valor) {
    return valor === null || valor === undefined || String(valor).trim() === "";
  }

  function formatear(campo, valor) {
    if (campo === "area_m2" && isFinite(valor)) {
      return Number(valor).toLocaleString("es-AR", { maximumFractionDigits: 0 }) + " m²";
    }
    return String(valor);
  }

  var ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };

  function escapar(texto) {
    return String(texto).replace(/[&<>"]/g, function (c) { return ESCAPES[c]; });
  }

  /* The heading is the layer name, never a guessed field: with several layers
   * on at once, the first thing to answer is which one was clicked. The
   * feature's own `nombre` goes under it when it has one.
   */
  function popupHtml(propiedades, tituloCapa, idCapa) {
    propiedades = propiedades || {};
    var omitir = OCULTOS.concat(OCULTOS_POR_CAPA[idCapa] || []);
    var cabecera = '<p class="popup-capa">' + escapar(tituloCapa) + "</p>";

    if (!vacio(propiedades.nombre)) {
      cabecera += '<p class="popup-nombre">' + escapar(propiedades.nombre) + "</p>";
      omitir.push("nombre");
    }

    var filas = Object.keys(propiedades).filter(function (campo) {
      return omitir.indexOf(campo.toLowerCase()) === -1 && !vacio(propiedades[campo]);
    }).map(function (campo) {
      return '<tr><th scope="row">' + escapar(ALIAS[campo] || campo) + "</th>" +
             "<td>" + escapar(formatear(campo, propiedades[campo])) + "</td></tr>";
    });

    if (!filas.length) return cabecera;
    return cabecera + '<table class="popup-datos"><tbody>' + filas.join("") + "</tbody></table>";
  }

  // --- catalogue layers


  var cargadas = {};

  function estilo(trazo) {
    return {
      color: trazo.color,
      weight: 1.5,
      opacity: .95,
      fillColor: trazo.fillColor,
      fillOpacity: .25
    };
  }

  function repintarCapas(trazo) {
    Object.keys(cargadas).forEach(function (id) {
      cargadas[id].setStyle(estilo(trazo));
    });
  }

  function encender(entrada) {
    var id = entrada.value;

    if (cargadas[id]) {
      cargadas[id].addTo(mapa);
      return;
    }

    entrada.disabled = true;
    var fila = entrada.closest(".capa");
    if (fila) fila.classList.add("cargando");

    fetch(entrada.dataset.geojson)
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (datos) {
        var trazo = TRAZOS[modoActual()];
        var etiqueta = fila ? fila.querySelector("span") : null;
        var titulo = etiqueta ? etiqueta.textContent.trim() : id;
        var capa = L.geoJSON(datos, {
          style: estilo(trazo),
          onEachFeature: function (rasgo, sector) {
            sector.bindPopup(function () {
              return popupHtml(rasgo.properties, titulo, id);
            }, { maxWidth: 320, minWidth: 200 });
          },
          pointToLayer: function (_, punto) {
            return L.circleMarker(punto, {
              radius: 4,
              color: trazo.color,
              weight: 1.5,
              fillColor: trazo.fillColor,
              fillOpacity: .8
            });
          }
        });
        cargadas[id] = capa;
        // The user may have unchecked it while it was downloading.
        if (entrada.checked) capa.addTo(mapa);
      })
      .catch(function () {
        entrada.checked = false;
        if (fila) fila.classList.add("fallo");
      })
      .then(function () {
        entrada.disabled = false;
        if (fila) fila.classList.remove("cargando");
      });
  }

  function apagar(id) {
    if (cargadas[id]) mapa.removeLayer(cargadas[id]);
  }

  // --- controls

  // --- zoom group, left side

  var zoom = document.getElementById("zoom");
  if (zoom) zoom.hidden = false;

  function al(id, accion) {
    var boton = document.getElementById(id);
    if (boton) boton.addEventListener("click", accion);
  }

  al("acercar", function () { mapa.zoomIn(); });
  al("alejar", function () { mapa.zoomOut(); });
  al("encuadre", function () { mapa.setView(CENTRO, ZOOM); });

  var mando = document.getElementById("mando");
  var botonModo = document.getElementById("modo");
  var botonBase = document.getElementById("base");
  var textoBase = document.getElementById("base-texto");

  if (mando) mando.hidden = false;

  if (botonModo) {
    botonModo.addEventListener("click", function () {
      oscuro = !oscuro;
      botonModo.setAttribute("aria-pressed", String(oscuro));
      var rotulo = oscuro ? "Modo claro" : "Modo oscuro";
      botonModo.title = rotulo;
      // Keep the screen reader label in step with the icon and the tooltip.
      var oculto = botonModo.querySelector(".visualmente-oculto");
      if (oculto) oculto.textContent = rotulo;
      // The moon only means anything over the Argenmap base.
      botonModo.disabled = satelital;
      pintarBase();
    });
  }

  if (botonBase) {
    botonBase.addEventListener("click", function () {
      satelital = !satelital;
      botonBase.setAttribute("aria-pressed", String(satelital));
      if (textoBase) textoBase.textContent = satelital ? "Argenmap" : "Satelital";
      if (botonModo) botonModo.disabled = satelital;
      pintarBase();
    });
  }

  pintarBase();

  var panel = document.querySelector(".panel");
  if (panel) {
    panel.addEventListener("change", function (evento) {
      var entrada = evento.target;
      if (!entrada.matches('.capa input[type="checkbox"]')) return;
      if (entrada.checked) {
        encender(entrada);
      } else {
        apagar(entrada.value);
      }
    });

    var nota = panel.querySelector(".nota-visor");
    if (nota) nota.hidden = true;

    // A shareable view: visor.html#capas=cr-adm-limites-barrios,cr-equ-...
    var encontrado = /^#capas=([a-z0-9,-]+)$/.exec(location.hash);
    if (encontrado) {
      encontrado[1].split(",").forEach(function (id) {
        var entrada = panel.querySelector('input[value="' + id + '"]');
        if (entrada) {
          entrada.checked = true;
          encender(entrada);
        }
      });
    }
  }

  // Leaflet measures the container when the map is built. Web fonts and the
  // sticky-footer layout can settle after that, leaving a map sized for a box
  // that no longer exists: it only redrew when the window was resized.
  function remedir() { mapa.invalidateSize(); }

  window.requestAnimationFrame(remedir);
  window.addEventListener("load", remedir);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(remedir);
  if ("ResizeObserver" in window) new ResizeObserver(remedir).observe(contenedor);
})();
