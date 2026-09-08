/* ==========================================================================
   HCI FUND Radar — tabs, flags, TradingView, COT and TIME CUT
   Added 21/ago/2026. Additive: the original renderers are wrapped, never
   rewritten. No MutationObserver is used — editing observed nodes was
   re-triggering the observers and freezing the page.
   ========================================================================== */

const CCY = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "NZD", "CHF"];
/* `esc` ja existe no app.js — reaproveitado aqui. */
/* [08/set] "MUDE AS LETRAS DE CADA COT PARA A BANDEIRA DE CADA PAIS."
   O comentario que estava aqui dizia que emoji de bandeira nao renderiza no Windows e
   por isso o chip era de duas letras. Isso ficou FALSO: o ui_macro.js usa 🇺🇸 🇪🇺 🇬🇧 no
   calendario, na tabela dos bancos e nas manchetes, e renderiza na maquina dele — da para
   ver nas fotos que ele mandou hoje. O chip de letra era a unica ilha de "US EU GB" num
   site que ja e todo bandeira.
   O `data-c` continua no span: e ele que da a cor de fundo do chip no CSS, e serve de
   fallback silencioso se a fonte de emoji faltar. */
const BANDEIRA = {
  USD: "🇺🇸", EUR: "🇪🇺", GBP: "🇬🇧", JPY: "🇯🇵",
  AUD: "🇦🇺", CAD: "🇨🇦", NZD: "🇳🇿", CHF: "🇨🇭",
};
const chip = (c) => CCY.includes(c) ? `<span class="ccy-chip ccy-bandeira" data-c="${c}" title="${c}">${BANDEIRA[c] || c.slice(0, 2)}</span>` : "";
const pairChips = (p) => {
  const t = String(p || "").toUpperCase();
  if (t.length < 6) return "";
  const a = chip(t.slice(0, 3)), b = chip(t.slice(3, 6));
  return a && b ? `<span class="ccy-pair">${a}${b}</span>` : "";
};

function decorateFlags() {
  const put = (el) => {
    if (!el || el.dataset.flagDone) return;
    const txt = el.textContent.trim();
    const marca = txt.length >= 6 ? pairChips(txt) : chip(txt.toUpperCase());
    if (!marca) return;
    el.dataset.flagDone = "1";
    el.innerHTML = marca + esc(txt);
  };
  document.querySelectorAll("#priorityTableBody tr td:nth-child(2), #pairTableBody tr td:first-child").forEach(put);
  document.querySelectorAll(".currency-grid strong, .calendar-currency-row strong").forEach(put);
  document.querySelectorAll(".calendar-prefund .prefund-row strong, .calendar-recommendations article strong").forEach(put);
}

/* ---------------------------- TIME CUT ---------------------------------- */
const timeCut = {
  date: null,
  get active() { return Boolean(this.date); },
  isAfter(d) { return this.active && String(d) > this.date; },
  hidesOutcome(d) { return this.active && String(d) >= this.date; },
};

function paintTimeCut() {
  const banner = document.getElementById("timeCutBanner");
  const btn = document.getElementById("timeCutToggle");
  if (!banner || !btn) return;
  banner.hidden = !timeCut.active;
  btn.classList.toggle("is-armed", timeCut.active);
  btn.textContent = timeCut.active ? "Cut on" : "Time cut";
  document.body.classList.toggle("timecut-on", timeCut.active);
  if (timeCut.active) document.getElementById("timeCutLabel").textContent = brDate(timeCut.date);
}

function applyCutToGrid() {
  document.querySelectorAll(".calendar-day").forEach((cell) => {
    const iso = cell.dataset.calendarDate || "";
    const after = Boolean(iso && timeCut.isAfter(iso));
    cell.classList.toggle("is-after-cut", after);
    cell.disabled = after;
  });
}

function applyCutToOutcomes(dayStr) {
  if (!timeCut.hidesOutcome(dayStr)) return;
  document.querySelectorAll("#calendarPreFund .prefund-outcome").forEach((el) => {
    el.className = "prefund-outcome hidden-outcome";
    el.textContent = "outcome hidden";
  });
}

/* wrap the original renderers (classic script: declarations are reassignable) */
const _renderCalendarDetail = renderCalendarDetail;
renderCalendarDetail = function (day) {
  _renderCalendarDetail(day);
  decorateFlags();
  if (day) applyCutToOutcomes(day.date);
};

const _renderCalendarMonth = renderCalendarMonth;
renderCalendarMonth = async function (...args) {
  const out = await _renderCalendarMonth(...args);
  applyCutToGrid();
  decorateFlags();
  return out;
};

const _renderAll = renderAll;
renderAll = function (...args) {
  const out = _renderAll(...args);
  decorateFlags();
  return out;
};

const _renderPairTable = renderPairTable;
renderPairTable = function (...args) {
  const out = _renderPairTable(...args);
  decorateFlags();
  return out;
};

const _renderPairDetail = renderPairDetail;
renderPairDetail = function (pair, ...rest) {
  const out = _renderPairDetail(pair, ...rest);
  decorateFlags();
  const nome = typeof pair === "string" ? pair : (pair && pair.pair);
  if (!timeCut.active) mountTradingView(nome);
  return out;
};

async function setTimeCut(value) {
  timeCut.date = value || null;
  paintTimeCut();
  if (timeCut.active && state.calendarMonth > timeCut.date.slice(0, 7)) {
    await setCalendarMonth(timeCut.date.slice(0, 7));
  } else {
    await renderCalendarMonth();
  }
  applyCutToGrid();
  const sel = state.calendarSelectedDate;
  if (sel && timeCut.isAfter(sel)) {
    ["calendarPreFund", "calendarRecommendations", "calendarCurrencies"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = '<div class="calendar-empty">After the time cut. Not visible.</div>';
    });
    document.getElementById("calendarDate").textContent = "—";
  } else if (sel) {
    applyCutToOutcomes(sel);
  }
}

const _cutToggle = document.getElementById("timeCutToggle");
if (_cutToggle) {
  _cutToggle.addEventListener("click", async () => {
    if (timeCut.active) { await setTimeCut(null); return; }
    const escolhido = document.getElementById("timeCutDate").value;
    if (!escolhido) { showMessage("Pick a date first: the time cut hides everything after it.", true); return; }
    await setTimeCut(escolhido);
  });
}
const _cutClear = document.getElementById("timeCutClear");
if (_cutClear) _cutClear.addEventListener("click", () => setTimeCut(null));

/* ------------------------------ TABS ------------------------------------ */
function activateTab(name) {
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("is-active", b.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("is-active", p.dataset.panel === name));
  try { history.replaceState(null, "", `#${name}`); } catch (_) {}
  window.scrollTo({ top: 0 });
  if (name === "cot") renderCot();
  if (name === "pairs" && !timeCut.active) mountTradingView(state.selectedPair);
  decorateFlags();
}
const _tabBar = document.getElementById("tabBar");
if (_tabBar) {
  _tabBar.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (btn) activateTab(btn.dataset.tab);
  });
}

/* -------------------------- TRADINGVIEW --------------------------------- */
let tvLoaded = false;
function loadTradingView() {
  if (tvLoaded) return Promise.resolve(true);
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = "https://s3.tradingview.com/tv.js";
    s.onload = () => { tvLoaded = true; resolve(true); };
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
}

async function mountTradingView(pair) {
  const box = document.getElementById("tvChart");
  if (!box || !pair || box.dataset.pair === pair) return;
  box.dataset.pair = pair;
  box.innerHTML = '<p class="muted tv-hint">Loading chart…</p>';
  const ok = await loadTradingView();
  if (!ok || !window.TradingView) {
    box.innerHTML = '<p class="muted tv-hint">Chart unavailable offline. Everything else works without internet.</p>';
    return;
  }
  box.innerHTML = '<div id="tvInner" style="height:100%"></div>';
  new window.TradingView.widget({
    container_id: "tvInner",
    symbol: "FX_IDC:" + pair,
    interval: "D",
    theme: "dark",
    style: "1",
    locale: "en",
    autosize: true,
    hide_side_toolbar: true,
    allow_symbol_change: false,
    withdateranges: true,
  });
}

/* ------------------------------- COT ------------------------------------ */
let cotDone = false;
let cotCacheKey = "";
async function renderCot() {
  const chave = timeCut.active ? timeCut.date : "live";
  if (cotDone && cotCacheKey === chave) return;
  cotCacheKey = chave;
  const status = document.getElementById("cotStatus");
  const grid = document.getElementById("cotGrid");
  if (!grid) return;
  try {
    const res = await fetch("data/cot_snapshot.json?x=" + Date.now());
    if (!res.ok) throw new Error("no snapshot");
    const data = await res.json();
    let rows = data.currencies || [];
    if (!rows.length) throw new Error("empty");
    /* Time cut: a CFTC publica na sexta o livro da terca. Um relatorio posterior
       ao corte e informacao do futuro e nao pode aparecer. */
    if (timeCut.active) {
      rows = rows.map((c) => {
        const hist = (c.history || []).filter((h) => h.date <= timeCut.date);
        if (!hist.length) return null;
        const atual = hist[0], anterior = hist[1] || hist[0];
        return { ...c, report_date: atual.date, net: atual.net,
                 change: atual.net - anterior.net,
                 percentile: atual.percentile, zscore: atual.zscore };
      }).filter(Boolean);
      if (!rows.length) {
        status.textContent = "Nenhum relatório da CFTC foi publicado antes do corte de tempo.";
        grid.innerHTML = "";
        return;
      }
    }
    const dataRel = timeCut.active ? rows[0].report_date : ((data.meta && data.meta.report_date) || "—");
    const dataMs = /^\d{4}-\d{2}-\d{2}$/.test(dataRel) ? Date.parse(dataRel + "T00:00:00Z") : NaN;
    const idadeDias = Number.isFinite(dataMs) ? Math.floor((Date.now() - dataMs) / 864e5) : null;
    status.textContent = "Relatório Legacy da CFTC — semana de " + dataRel +
      (timeCut.active ? " (último disponível antes do corte)" : "") +
      (!timeCut.active && idadeDias > 10 ? " · ATENÇÃO: arquivo atrasado, " + idadeDias + " dias corridos" : "");
    grid.innerHTML = rows.map((c) => {
      const pct = Number(c.percentile);
      const crowd = pct >= 90 ? "crowded-long" : pct <= 10 ? "crowded-short" : "";
      const net = Number(c.net);
      const chg = Number(c.change);
      const selo = crowd ? '<em class="cot-badge">' + (pct >= 90 ? "COMPRADO LOTADO" : "VENDIDO LOTADO") + "</em>" : "";
      return '<article class="cot-card ' + crowd + '">' +
        '<header>' + chip(c.currency) + '<strong>' + c.currency + "</strong>" + selo + "</header>" +
        '<div class="cot-net ' + (net >= 0 ? "positive" : "negative") + '">' + net.toLocaleString("pt-BR") +
        "<small>posição líquida não comercial</small></div>" +
        '<div class="cot-meta">' +
        "<div><span>Variação semanal</span><strong class=\"" + (chg >= 0 ? "positive" : "negative") + "\">" +
        (chg >= 0 ? "+" : "") + chg.toLocaleString("pt-BR") + "</strong></div>" +
        "<div><span>Percentil (5 anos)</span><strong>" + (Number.isFinite(pct) ? pct.toFixed(0) + "%" : "—") + "</strong></div>" +
        "<div><span>Escore-z</span><strong>" + (Number.isFinite(Number(c.zscore)) ? Number(c.zscore).toFixed(2).replace(".", ",") : "—") + "</strong></div>" +
        "</div></article>";
    }).join("");
    cotDone = true;
  } catch (err) {
    console.error("[COT]", err);
    status.textContent = "COT indisponível: " + (err && err.message ? err.message : err);
    grid.innerHTML = "";
  }
}

/* ------------------------------- BOOT ----------------------------------- */
(function () {
  const wanted = (location.hash || "").replace("#", "");
  const existe = Array.prototype.some.call(document.querySelectorAll(".tab"), (b) => b.dataset.tab === wanted);
  if (existe) activateTab(wanted);
  setTimeout(decorateFlags, 900);
})();

/* ============================================================================
   ABA YIELDS — o juro de 2 anos das 8 moedas.
   Rele o arquivo a cada 60s: quando update_fund.py + update_yields.py rodam,
   o painel acompanha sem recarregar. NAO e tempo real e nao finge ser: cada
   card carrega o proprio atraso de publicacao.
   ========================================================================== */
(function yields() {
  const grid = document.getElementById("yieldGrid");
  if (!grid) return;

  const linha = (x) => {
    // separador DECIMAL em portugues e virgula — a tela mostrava "+13.3 pb" e "-1.4 pb".
    // Mesma lapide ja pega no ui_macro.js (06/set) e no ui_juros_cambio.js (08/set).
    const bp = (v) => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + v.toFixed(1).replace(".", ",");
    const cor = (v) => v === null || v === undefined ? "" : (v > 0 ? "positive" : v < 0 ? "negative" : "");
    const z = x.z1;
    const forca = z === null || z === undefined ? "sem leitura"
      : Math.abs(z) < 1 ? "dentro do ruído diário"
      : Math.abs(z) < 2 ? "movimento relevante, " + Math.abs(z).toFixed(1).replace(".", ",") + "\u03c3"
      : "movimento grande, " + Math.abs(z).toFixed(1).replace(".", ",") + "\u03c3";
    const velho = x.stale_days >= 5 ? "is-stale" : x.stale_days >= 3 ? "is-aging" : "";
    const spark = (() => {
      const h = x.history || [];
      if (h.length < 8) return "";
      const ys = h.map((p) => p.y), lo = Math.min.apply(null, ys), hi = Math.max.apply(null, ys);
      const faixa = (hi - lo) || 1;
      const pts = ys.map((v, i) => (i / (ys.length - 1) * 100).toFixed(1) + "," +
        (26 - (v - lo) / faixa * 24).toFixed(1)).join(" ");
      return '<svg class="yield-spark" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true">' +
        '<polyline points="' + pts + '"/></svg>';
    })();
    return '<article class="yield-card ' + velho + '" data-cur="' + x.currency + '">' +
      '<header><strong>' + x.currency + "</strong>" +
        '<span class="yield-stale">' + (x.stale_days === 0 ? "hoje" :
          x.stale_days + (x.stale_days === 1 ? " dia útil atrás" : " dias úteis atrás")) + "</span></header>" +
      '<div class="yield-value mono">' + x.yield.toFixed(3) + "<i>%</i></div>" + spark +
      '<div class="yield-changes">' +
        '<div><span>1 dia</span><strong class="mono ' + cor(x.d1) + '">' + bp(x.d1) + " pb</strong></div>" +
        '<div><span>5 dias</span><strong class="mono ' + cor(x.d5) + '">' + bp(x.d5) + " pb</strong></div>" +
        '<div><span>20 dias</span><strong class="mono ' + cor(x.d20) + '">' + bp(x.d20) + " pb</strong></div>" +
      "</div>" +
      '<details class="yield-why"><summary><span>Por que se moveu e onde verificar</span></summary>' +
        '<div class="yield-why-body">' +
          "<p><span>Tamanho do movimento de hoje</span>" + forca +
            (x.sigma_bp ? ". Um desvio padrão nesta curva é <b>" + x.sigma_bp.toFixed(1).replace(".", ",") +
             " pb</b>, nas últimas 252 observações." : ".") + "</p>" +
          "<p><span>O que explicaria uma alta</span>inflação acima do esperado, emprego firme ou uma virada " +
            "hawkish fazem o mercado precificar menos cortes ou cortes mais tarde pelo " +
            (x.central_bank || "banco central") + ". Uma queda indica o oposto.</p>" +
          "<p><span>Verificar a decisão</span>" + (x.central_bank_url
            ? '<a href="' + x.central_bank_url + '" target="_blank" rel="noreferrer">' + x.central_bank +
              " — comunicados</a>" : "\u2014") + "</p>" +
          "<p><span>Verificar o número</span>" + (x.source_url
            ? '<a href="' + x.source_url + '" target="_blank" rel="noreferrer">' + x.source + "</a>" : "\u2014") +
            " \u00b7 publicação " + ({ daily: "diária", weekly: "semanal",
              "daily (business days), published D+1 ~08:30 CET": "diária em dias úteis, D+1 por volta de 08:30 CET" }[x.cadence] || x.cadence || "\u2014") + "</p>" +
        "</div></details>" +
      "</article>";
  };

  async function carrega() {
    // com o corte ativo quem manda e pintaYields(); sem esta guarda o fetch
    // ao vivo resolvia depois e sobrescrevia o painel com o dado de HOJE
    if (window.timeCut && timeCut.active) return;
    try {
      const r = await fetch("data/yields.json?x=" + Date.now());
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      grid.innerHTML = (d.currencies || []).map(linha).join("");
      const nota = document.getElementById("yieldNote");
      if (nota) {
        const maior = Math.max.apply(null, (d.currencies || []).map((x) => x.stale_days || 0));
        // [08/set] a nota de rodape da aba de juros saiu — o Eduardo riscou o paragrafo
        // inteiro. O que ela dizia (cada fonte publica no proprio ritmo; nao e feed
        // ao vivo) vive no title do titulo da secao e na idade de cada cartao.
        nota.innerHTML = "";
      }
    } catch (_) {
      grid.innerHTML = '<div class="empty-state">yields.json ainda não foi gerado — execute update_yields.py.</div>';
    }
  }
  window.recarregaYields = carrega;   // o corte chama isto ao ser desligado
  carrega();
  setInterval(function () { if (!(window.timeCut && timeCut.active)) carrega(); }, 60000);
})();
