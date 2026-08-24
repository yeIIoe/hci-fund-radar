// ui_live_yields.js — yields 2y AO VIVO, direto do navegador (24/ago/2026).
//
// O endpoint scanner.tradingview.com devolve CORS liberado para qualquer
// origem, entao o VISITANTE busca o preco ele mesmo: zero cron, zero atraso.
// O Actions horario continua persistindo em yields.json — e o que alimenta o
// calculo do FUND e o fallback se o TradingView bloquear um dia.
//
// Regras:
//  - corte temporal ativo => camada viva DESLIGADA (o passado nao tem "ao vivo")
//  - |vivo - publicado| > 0,80pp => descarta (mesmo guarda-chuva do coletor)
//  - aba escondida => pausa (visibilitychange)
(function () {
  "use strict";
  var SIMB = { USD: "US02Y", EUR: "DE02Y", GBP: "GB02Y", JPY: "JP02Y",
               AUD: "AU02Y", CAD: "CA02Y", CHF: "CH02Y", NZD: "NZ02Y" };
  var LIMITE_PP = 0.80;

  function buscaUma(cur) {
    var url = "https://scanner.tradingview.com/symbol?symbol=TVC%3A" +
              SIMB[cur] + "&fields=close";
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (d) {
      var v = d && d.close;
      if (typeof v !== "number" || v <= -2 || v >= 25) throw new Error("implausivel");
      return v;
    });
  }

  function aplica(cur, v) {
    var card = document.querySelector('#yieldGrid .yield-card[data-cur="' + cur + '"]');
    if (!card) return;
    var alvo = card.querySelector(".yield-value");
    if (!alvo) return;
    var pub = parseFloat((alvo.textContent || "").replace("%", ""));
    if (isFinite(pub) && Math.abs(v - pub) > LIMITE_PP) return;   // guarda
    var antes = parseFloat(alvo.getAttribute("data-live") || pub);
    alvo.innerHTML = v.toFixed(3) + "<i>%</i>";
    alvo.setAttribute("data-live", v);
    alvo.classList.remove("live-up", "live-down");
    if (isFinite(antes) && v !== antes) {
      alvo.classList.add(v > antes ? "live-up" : "live-down");
    }
    var selo = card.querySelector(".yield-stale");
    if (selo) {
      selo.textContent = "LIVE " + new Date().toLocaleTimeString();
      selo.classList.add("is-live");
    }
    card.classList.remove("is-stale", "is-aging");
  }

  function rodada() {
    if (window.timeCut && timeCut.active) return;
    if (document.hidden) return;
    var grid = document.getElementById("yieldGrid");
    if (!grid || !grid.querySelector(".yield-card")) return;
    Object.keys(SIMB).forEach(function (cur) {
      buscaUma(cur).then(function (v) { aplica(cur, v); }).catch(function () {});
    });
  }

  var css = document.createElement("style");
  css.textContent =
    ".yield-stale.is-live{color:#5eead4;font-weight:600}" +
    ".yield-value.live-up{color:#34d399;transition:color .6s}" +
    ".yield-value.live-down{color:#f87171;transition:color .6s}";
  document.head.appendChild(css);

  setTimeout(rodada, 2500);          // depois do primeiro render dos cards
  setInterval(rodada, 60000);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) rodada();
  });
})();
