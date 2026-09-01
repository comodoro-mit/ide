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

  var CENTRO = [-45.828, -67.522];
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

  /* Per layer override, optional: a layer with no entry here falls back to
   * TRAZOS and still draws. The point is thematic identity — a reader with
   * three layers on at once should tell them apart without the legend.
   *
   * Boundaries are the base layer everything else sits on: grey fill, plain
   * outline that flips with the base, so they frame the map without competing.
   * Green for open space, orange for sport, purple for neighbourhood
   * associations, red for health. `radio` is the point size, ignored by
   * polygons. Same three modes as TRAZOS. */
  var TRAZOS_POR_CAPA = {
    "cr-adm-limites-barrios": {
      claro: { color: "#000", fillColor: "#808080", fillOpacity: .1 },
      oscuro: { color: "#fff", fillColor: "#808080", fillOpacity: .1 },
      satelital: { color: "#000", fillColor: "#808080", fillOpacity: .1 }
    },
    "cr-equ-espacios-verdes": {
      claro: { color: "#1b5e20", fillColor: "#4caf50", fillOpacity: .38 },
      oscuro: { color: "#a5d6a7", fillColor: "#66bb6a", fillOpacity: .38 },
      satelital: { color: "#ccff90", fillColor: "#76ff03", fillOpacity: .30 }
    },
    "cr-equ-playones-deportivos": {
      radio: 5,
      claro: { color: "#7f3300", fillColor: "#f57c00", fillOpacity: .9 },
      oscuro: { color: "#3a1c00", fillColor: "#ffa726", fillOpacity: .95 },
      satelital: { color: "#ffffff", fillColor: "#ff9100", fillOpacity: .95 }
    },
    "cr-equ-asociaciones-vecinales": {
      radio: 5,
      claro: { color: "#3d0a58", fillColor: "#8e24aa", fillOpacity: .9 },
      oscuro: { color: "#24042f", fillColor: "#ce93d8", fillOpacity: .95 },
      satelital: { color: "#ffffff", fillColor: "#d500f9", fillOpacity: .95 }
    },
    "cr-sal-salud-publica": {
      radio: 6,
      claro: { color: "#6b0000", fillColor: "#e53935", fillOpacity: .9 },
      oscuro: { color: "#360000", fillColor: "#ef5350", fillOpacity: .95 },
      satelital: { color: "#ffffff", fillColor: "#ff1744", fillOpacity: .95 }
    }
  };

  /* Sequential ramps, five classes, colour-blind safe (ColorBrewer). One per
   * census theme so two choropleths on at once never read as the same map. */
  var PALETAS = {
    carencia: ["#fef0d9", "#fdcc8a", "#fc8d59", "#e34a33", "#b30000"],
    densidad: ["#edf8fb", "#b3cde3", "#8c96c6", "#8856a7", "#810f7c"],
    edad:     ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"],
    vivienda: ["#edf8fb", "#b2e2e2", "#66c2a4", "#2ca25f", "#006d2c"],
    salud:    ["#f1eef6", "#d7b5d8", "#df65b0", "#dd1c77", "#980043"]
  };

  /* Census tracts are not a category, they are a number: 325 identical
   * polygons in one colour say nothing. Each of these is shaded by its own
   * variable. `valor` derives it from the feature so the published fields stay
   * as they are — a rate is computed here, not stored twice.
   *
   * The class breaks are NOT hard-coded: they are quintiles of the data as
   * downloaded, so a master file updated tomorrow re-classes itself.
   */
  var COROPLETAS = {
    "cr-cen-radios-nbi": {
      etiqueta: "Hogares con NBI (%)",
      paleta: PALETAS.carencia,
      decimales: 1,
      valor: function (p) {
        return p.hogares > 0 ? (p.nbi_si / p.hogares) * 100 : null;
      }
    },
    "cr-cen-radios-densidad-poblacion": {
      etiqueta: "Densidad (hab/km²)",
      paleta: PALETAS.densidad,
      decimales: 0,
      valor: function (p) { return p.densidad; }
    },
    "cr-cen-radios-edad-grupos": {
      etiqueta: "Población de 65 años y más (%)",
      paleta: PALETAS.edad,
      decimales: 1,
      valor: function (p) {
        return p.pob_total > 0 ? (p.pob_65_mas / p.pob_total) * 100 : null;
      }
    },
    "cr-cen-radios-densidad-viviendas": {
      etiqueta: "Densidad de viviendas (viv/km²)",
      paleta: PALETAS.vivienda,
      decimales: 0,
      valor: function (p) { return p.dens_viv; }
    },
    "cr-cen-radios-cobertura-salud": {
      etiqueta: "Sin cobertura de salud (%)",
      paleta: PALETAS.salud,
      decimales: 0,
      valor: function (p) { return p.porc_sin; }
    }
  };

  // A tract with no value is not a zero: it gets its own neutral grey.
  var SIN_DATO = { claro: "#d9d9d9", oscuro: "#4a4a4a", satelital: "#bdbdbd" };

  // Hairline between tracts. The ramp carries the meaning; the outline only
  // has to keep 325 polygons from melting into one blob.
  var BORDE_CORO = { claro: "#6b6b6b", oscuro: "#dcdcdc", satelital: "#ffffff" };

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
    // The swatches follow the layer colours, which follow the base map.
    if (typeof dibujarLeyenda === "function") dibujarLeyenda();
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
    altura: "Altura",
    posee_comision: "Comisión vecinal",
    responsable: "Responsable",
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
  var cortes = {};     // id -> class breaks, computed once from the data
  var espunto = {};    // id -> the layer draws points
  var titulos = {};    // id -> the label shown in the panel

  /* Quintiles, not equal intervals: density runs from 0.09 to 47500 hab/km²
   * and equal intervals would put 320 of the 325 tracts in the first class.
   * Quintiles guarantee every colour is used and the map stays readable
   * whatever the distribution looks like after the next update.
   */
  function calcularCortes(idCapa, datos) {
    var conf = COROPLETAS[idCapa];
    if (!conf) return;
    var valores = (datos.features || []).map(function (rasgo) {
      return conf.valor(rasgo.properties || {});
    }).filter(function (v) {
      return typeof v === "number" && isFinite(v);
    }).sort(function (a, b) { return a - b; });

    if (!valores.length) return;

    var quiebres = [];
    for (var i = 1; i < conf.paleta.length; i++) {
      quiebres.push(valores[Math.floor(valores.length * i / conf.paleta.length)]);
    }
    cortes[idCapa] = {
      quiebres: quiebres,
      min: valores[0],
      max: valores[valores.length - 1]
    };
  }

  // -1 means no value: the feature is drawn in SIN_DATO, never in class 0.
  function clase(idCapa, valor) {
    var c = cortes[idCapa];
    if (!c || typeof valor !== "number" || !isFinite(valor)) return -1;
    var i = 0;
    while (i < c.quiebres.length && valor >= c.quiebres[i]) i++;
    return i;
  }

  /* Returns either a plain style object or, for a choropleth, the per feature
   * function Leaflet accepts in the same slot. `setStyle` takes both, so the
   * mode switch repaints graduated and flat layers through one code path.
   */
  function estilo(trazo, idCapa) {
    var modo = modoActual();
    var conf = COROPLETAS[idCapa];

    if (conf) {
      return function (rasgo) {
        var i = clase(idCapa, conf.valor((rasgo && rasgo.properties) || {}));
        return {
          color: BORDE_CORO[modo],
          weight: .6,
          opacity: .85,
          fillColor: i < 0 ? SIN_DATO[modo] : conf.paleta[i],
          fillOpacity: modo === "satelital" ? .72 : .8
        };
      };
    }

    var porCapa = TRAZOS_POR_CAPA[idCapa];
    var propio = (porCapa && porCapa[modo]) || {};
    return {
      color: propio.color || trazo.color,
      weight: 1.5,
      opacity: .95,
      fillColor: propio.fillColor || trazo.fillColor,
      fillOpacity: propio.fillOpacity !== undefined ? propio.fillOpacity : .25,
      // Ignored by polygons; CircleMarker.setStyle reads it, so points keep
      // their size when the base map flips.
      radius: (porCapa && porCapa.radio) || 4
    };
  }

  function repintarCapas(trazo) {
    Object.keys(cargadas).forEach(function (id) {
      cargadas[id].setStyle(estilo(trazo, id));
    });
  }

  /* Order in the overlay pane is order of arrival, which is whatever the user
   * clicked first: a choropleth switched on last would bury the points drawn
   * under it. Filled areas sink, points rise, whatever the click order was.
   */
  function ordenar(idCapa) {
    var capa = cargadas[idCapa];
    if (!capa) return;
    if (espunto[idCapa]) capa.bringToFront();
    else capa.bringToBack();
  }

  function encender(entrada) {
    var id = entrada.value;

    if (cargadas[id]) {
      cargadas[id].addTo(mapa);
      ordenar(id);
      dibujarLeyenda();
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
        titulos[id] = titulo;
        var primera = (datos.features || [])[0];
        espunto[id] = !!(primera && primera.geometry &&
                         primera.geometry.type.indexOf("Point") !== -1);
        calcularCortes(id, datos);
        var capa = L.geoJSON(datos, {
          style: estilo(trazo, id),
          onEachFeature: function (rasgo, sector) {
            sector.bindPopup(function () {
              return popupHtml(rasgo.properties, titulo, id);
            }, { maxWidth: 320, minWidth: 200 });
          },
          // Bare marker: `style` above is applied to it by resetStyle, so the
          // colours live in one place instead of two that drift apart.
          pointToLayer: function (_, punto) {
            return L.circleMarker(punto);
          }
        });
        cargadas[id] = capa;
        // The user may have unchecked it while it was downloading.
        if (entrada.checked) {
          capa.addTo(mapa);
          ordenar(id);
        }
        dibujarLeyenda();
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
    dibujarLeyenda();
  }

  // --- legend

  /* Built here, not in visor.html: it only ever describes layers that are on,
   * so with nothing checked there is nothing to mark up. It lists the active
   * layers in panel order, ramp for the graduated ones and a single swatch for
   * the rest, and it is rebuilt on every toggle and on every base map change.
   */
  var lienzoLeyenda = contenedor.parentNode;
  var leyenda = document.createElement("div");
  leyenda.className = "ctrl leyenda";
  leyenda.id = "leyenda";
  leyenda.hidden = true;
  if (lienzoLeyenda) lienzoLeyenda.appendChild(leyenda);

  function numero(valor, decimales) {
    return Number(valor).toLocaleString("es-AR", {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales
    });
  }

  function bloqueRampa(id) {
    var conf = COROPLETAS[id];
    var c = cortes[id];
    if (!c) return "";
    var dec = conf.decimales;
    var ultima = conf.paleta.length - 1;

    var filas = conf.paleta.map(function (color, i) {
      var desde = i === 0 ? c.min : c.quiebres[i - 1];
      var hasta = i === ultima ? c.max : c.quiebres[i];
      return '<li><i style="background:' + color + '"></i>' +
             numero(desde, dec) + " – " + numero(hasta, dec) + "</li>";
    });

    return '<div class="leyenda-capa">' +
           "<p>" + escapar(conf.etiqueta) + "</p>" +
           '<ul class="leyenda-rampa">' + filas.join("") + "</ul></div>";
  }

  function bloqueSimple(id) {
    var trazo = TRAZOS[modoActual()];
    var e = estilo(trazo, id);
    var forma = espunto[id] ? "punto" : "area";
    return '<div class="leyenda-capa"><p>' +
           '<i class="muestra ' + forma + '" style="background:' + e.fillColor +
           ";border-color:" + e.color + '"></i>' +
           escapar(titulos[id] || id) + "</p></div>";
  }

  /* Panel order, not load order: `cargadas` is keyed in the order the fetches
   * came back, so the legend would shuffle itself on a slow connection. */
  function ordenPanel(id) {
    var entrada = document.querySelector('.capa input[value="' + id + '"]');
    if (!entrada) return 999;
    return Array.prototype.indexOf.call(
      document.querySelectorAll('.capa input[type="checkbox"]'), entrada);
  }

  function dibujarLeyenda() {
    if (!leyenda) return;
    var bloques = Object.keys(cargadas).filter(function (id) {
      return mapa.hasLayer(cargadas[id]);
    }).sort(function (a, b) {
      return ordenPanel(a) - ordenPanel(b);
    }).map(function (id) {
      return COROPLETAS[id] ? bloqueRampa(id) : bloqueSimple(id);
    }).filter(Boolean);

    leyenda.innerHTML = bloques.join("");
    leyenda.hidden = !bloques.length;
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
