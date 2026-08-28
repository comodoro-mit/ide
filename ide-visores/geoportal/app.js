/* Geoportal IDE Comodoro Rivadavia
 *
 * The dataset cards are written into the HTML at publish time, not fetched
 * here. This file only enhances what is already on the page: if it never
 * loads, the listing still works. That is the point - a public open data
 * portal should not go blank because a script failed.
 */

/* --- hero parallax ------------------------------------------------------ */

(function () {
  "use strict";

  var portada = document.querySelector(".portada");
  if (!portada) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  // How far the backdrop drifts, in px, at the edges of the section.
  var RECORRIDO = 50;

  var pendiente = null;

  function mover(evento) {
    if (pendiente) return; // one update per frame, not one per event
    pendiente = window.requestAnimationFrame(function () {
      pendiente = null;
      var caja = portada.getBoundingClientRect();
      var x = (evento.clientX - caja.left) / caja.width - 0.5;
      var y = (evento.clientY - caja.top) / caja.height - 0.5;
      // Opposite to the pointer: the backdrop reads as further away.
      portada.style.setProperty("--hero-x", (-x * RECORRIDO).toFixed(2) + "px");
      portada.style.setProperty("--hero-y", (-y * RECORRIDO).toFixed(2) + "px");
    });
  }

  function volver() {
    if (pendiente) window.cancelAnimationFrame(pendiente);
    pendiente = null;
    portada.style.setProperty("--hero-x", "0px");
    portada.style.setProperty("--hero-y", "0px");
  }

  portada.addEventListener("pointermove", function (evento) {
    if (evento.pointerType === "touch") return;
    mover(evento);
  });
  portada.addEventListener("pointerleave", volver);
})();

/* --- dataset search and theme filter ------------------------------------ */

(function () {
  "use strict";

  // Below this many datasets a search box is clutter, not help.
  var MINIMO_PARA_BUSCAR = 4;

  var contenedor = document.getElementById("fichas");
  if (!contenedor) return;

  var buscador = document.getElementById("buscador");
  var entrada = document.getElementById("filtro");
  var filtros = document.getElementById("filtros");
  var sinResultados = document.getElementById("sin-resultados");
  var conteo = document.querySelector(".conteo strong");

  var fichas = Array.prototype.slice.call(contenedor.querySelectorAll(".ficha"));
  if (!fichas.length) return;

  // Index each card once, so typing does not walk the DOM on every keystroke.
  var indice = fichas.map(function (ficha) {
    return {
      nodo: ficha,
      tema: ficha.dataset.tema || "",
      texto: normalizar(ficha.textContent)
    };
  });

  var temaActivo = "";

  // Fold accents and case so "limites" finds "Límites".
  function normalizar(texto) {
    return texto
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function filtrar() {
    var consulta = entrada ? normalizar(entrada.value) : "";
    var terminos = consulta ? consulta.split(" ") : [];
    var visibles = 0;

    indice.forEach(function (item) {
      var coincide =
        (!temaActivo || item.tema === temaActivo) &&
        terminos.every(function (termino) {
          return item.texto.indexOf(termino) !== -1;
        });
      item.nodo.hidden = !coincide;
      if (coincide) visibles++;
    });

    if (sinResultados) sinResultados.hidden = visibles !== 0;
    if (conteo) conteo.textContent = String(visibles);
  }

  // --- theme chips

  if (filtros) {
    filtros.hidden = false;

    filtros.addEventListener("click", function (evento) {
      var chip = evento.target.closest(".chip");
      if (!chip) return;
      elegirTema(chip.dataset.tema || "", true);
    });

    // A shareable filter: datasets.html#tema=adm opens already filtered.
    leerHash();
    window.addEventListener("hashchange", leerHash);
  }

  function elegirTema(tema, escribirHash) {
    temaActivo = tema;
    Array.prototype.forEach.call(filtros.querySelectorAll(".chip"), function (chip) {
      chip.setAttribute(
        "aria-pressed",
        (chip.dataset.tema || "") === tema ? "true" : "false"
      );
    });
    if (escribirHash) {
      // replaceState, not a hash assignment: filtering should not fill the
      // back button with one entry per click.
      history.replaceState(null, "", tema ? "#tema=" + tema : location.pathname);
    }
    filtrar();
  }

  function leerHash() {
    var encontrado = /^#tema=([a-z]{3})$/.exec(location.hash);
    var tema = encontrado ? encontrado[1] : "";
    if (tema !== temaActivo) elegirTema(tema, false);
  }

  // --- search box

  if (!buscador || !entrada || fichas.length < MINIMO_PARA_BUSCAR) return;

  buscador.hidden = false;

  var pendiente;
  entrada.addEventListener("input", function () {
    window.clearTimeout(pendiente);
    pendiente = window.setTimeout(filtrar, 120);
  });

  // Escape clears the search, which is what people expect from a search box.
  entrada.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape" && entrada.value) {
      entrada.value = "";
      filtrar();
    }
  });
})();

/* --- back to top -------------------------------------------------------- */

(function () {
  "use strict";

  // Only on pages that are actually long: on a two screen page the button is
  // noise. Measured in viewports of scrollable content.
  var LARGO_MINIMO = 2;
  // And only once the top is far enough away to be worth a shortcut.
  var APARECE_A = 0.8;

  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Built here, never in the HTML: without this script it would be a dead
  // button, and the site has to work with no JS at all.
  var boton = document.createElement("button");
  boton.type = "button";
  boton.className = "al-tope";
  boton.setAttribute("aria-label", "Volver al inicio de la página");
  boton.hidden = true;
  boton.innerHTML =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  document.body.appendChild(boton);

  var visible = false;
  var pendiente = null;

  function paginaLarga() {
    return document.documentElement.scrollHeight >
      window.innerHeight * LARGO_MINIMO;
  }

  function revisar() {
    pendiente = null;
    var mostrar = paginaLarga() &&
      window.scrollY > window.innerHeight * APARECE_A;
    if (mostrar === visible) return;
    visible = mostrar;
    if (mostrar) {
      boton.hidden = false;
      // Next frame, so the browser has a hidden state to animate from.
      window.requestAnimationFrame(function () {
        boton.classList.add("visible");
      });
    } else {
      boton.classList.remove("visible");
      // With reduced motion there is no transition, so transitionend never
      // fires and the hidden attribute below would never be set.
      if (reducido.matches) boton.hidden = true;
    }
  }

  function pedirRevision() {
    if (pendiente) return;
    pendiente = window.requestAnimationFrame(revisar);
  }

  // Leaving it in the accessibility tree while it fades out would let a
  // keyboard reach an invisible control.
  boton.addEventListener("transitionend", function (evento) {
    if (evento.propertyName === "opacity" && !visible) boton.hidden = true;
  });

  boton.addEventListener("click", function () {
    window.scrollTo({
      top: 0,
      behavior: reducido.matches ? "auto" : "smooth"
    });
    // The button is about to disappear under the focus ring. Hand focus to the
    // top of the page instead of dropping it on the body.
    var destino = document.querySelector(".marca");
    if (destino) destino.focus({ preventScroll: true });
  });

  window.addEventListener("scroll", pedirRevision, { passive: true });
  window.addEventListener("resize", pedirRevision);
  revisar();
})();
