/* Geoportal IDE Comodoro Rivadavia
 *
 * The dataset cards are written into the HTML at publish time, not fetched
 * here. This file only enhances what is already on the page: if it never
 * loads, the listing still works. That is the point — a public open data
 * portal should not go blank because a script failed.
 */

(function () {
  "use strict";

  // Below this many datasets a search box is clutter, not help.
  var MINIMO_PARA_BUSCAR = 4;

  var contenedor = document.getElementById("fichas");
  var buscador = document.getElementById("buscador");
  var entrada = document.getElementById("filtro");
  var sinResultados = document.getElementById("sin-resultados");
  var bloqueConteo = document.querySelector(".conteo");
  var conteo = bloqueConteo && bloqueConteo.querySelector("strong");
  var unidad = bloqueConteo && bloqueConteo.querySelector(".unidad");

  if (!contenedor || !buscador || !entrada) return;

  var fichas = Array.prototype.slice.call(contenedor.querySelectorAll(".ficha"));
  if (fichas.length < MINIMO_PARA_BUSCAR) return;

  buscador.hidden = false;

  // Index each card once, so typing does not walk the DOM on every keystroke.
  var indice = fichas.map(function (ficha) {
    return {
      nodo: ficha,
      texto: normalizar(ficha.textContent)
    };
  });

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
    var consulta = normalizar(entrada.value);
    var terminos = consulta ? consulta.split(" ") : [];
    var visibles = 0;

    indice.forEach(function (item) {
      var coincide = terminos.every(function (termino) {
        return item.texto.indexOf(termino) !== -1;
      });
      item.nodo.hidden = !coincide;
      if (coincide) visibles++;
    });

    if (sinResultados) sinResultados.hidden = visibles !== 0;
    if (conteo) conteo.textContent = String(visibles);
    if (unidad) {
      unidad.textContent =
        visibles === 1
          ? bloqueConteo.dataset.singular
          : bloqueConteo.dataset.plural;
    }
  }

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
