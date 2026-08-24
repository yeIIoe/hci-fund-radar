/* ==========================================================================
   HCI FUND Radar — tabs, flags, TradingView, COT and TIME CUT
   Added 21/ago/2026. Additive: the original renderers are wrapped, never
   rewritten. No MutationObserver is used — editing observed nodes was
   re-triggering the observers and freezing the page.
   ========================================================================== */

const CCY = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "NZD", "CHF"];
/* `esc` ja existe no app.js — reaproveitado aqui. */
/* Emoji de bandeira (regional indicator) nao renderiza no Windows: vira "US".
   Chip de duas letras colorido funciona em qualquer sistema, offline. */
const chip = (c) => CCY.includes(c) ? `<span class="ccy-chip" data-c="${c}">${c.slice(0, 2)}</span>` : "";
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
        status.textContent = "No CFTC report published before the time cut.";
        grid.innerHTML = "";
        return;
      }
    }
    const dataRel = timeCut.active ? rows[0].report_date : ((data.meta && data.meta.report_date) || "—");
    status.textContent = "CFTC Legacy report — week of " + dataRel +
      (timeCut.active ? " (latest available before the cut)" : "");
    grid.innerHTML = rows.map((c) => {
      const pct = Number(c.percentile);
      const crowd = pct >= 90 ? "crowded-long" : pct <= 10 ? "crowded-short" : "";
      const net = Number(c.net);
      const chg = Number(c.change);
      const selo = crowd ? '<em class="cot-badge">' + (pct >= 90 ? "CROWDED LONG" : "CROWDED SHORT") + "</em>" : "";
      return '<article class="cot-card ' + crowd + '">' +
        '<header>' + chip(c.currency) + '<strong>' + c.currency + "</strong>" + selo + "</header>" +
        '<div class="cot-net ' + (net >= 0 ? "positive" : "negative") + '">' + net.toLocaleString("en-US") +
        "<small>net non-commercial contracts</small></div>" +
        '<div class="cot-meta">' +
        "<div><span>Weekly change</span><strong class=\"" + (chg >= 0 ? "positive" : "negative") + "\">" +
        (chg >= 0 ? "+" : "") + chg.toLocaleString("en-US") + "</strong></div>" +
        "<div><span>Percentile (5y)</span><strong>" + (Number.isFinite(pct) ? pct.toFixed(0) + "%" : "—") + "</strong></div>" +
        "<div><span>Z-score</span><strong>" + (Number.isFinite(Number(c.zscore)) ? Number(c.zscore).toFixed(2) : "—") + "</strong></div>" +
        "</div></article>";
    }).join("");
    cotDone = true;
  } catch (err) {
    console.error("[COT]", err);
    status.textContent = "COT unavailable: " + (err && err.message ? err.message : err);
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
    const bp = (v) => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + v.toFixed(1);
    const cor = (v) => v === null || v === undefined ? "" : (v > 0 ? "positive" : v < 0 ? "negative" : "");
    const z = x.z1;
    const forca = z === null || z === undefined ? "no reading"
      : Math.abs(z) < 1 ? "inside the daily noise"
      : Math.abs(z) < 2 ? "a real move, " + Math.abs(z).toFixed(1) + "\u03c3"
      : "a large move, " + Math.abs(z).toFixed(1) + "\u03c3";
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
    return '<article class="yield-card ' + velho + '">' +
      '<header><strong>' + x.currency + "</strong>" +
        '<span class="yield-stale">' + (x.stale_days === 0 ? "today" :
          x.stale_days + (x.stale_days === 1 ? " business day old" : " business days old")) + "</span></header>" +
      '<div class="yield-value mono">' + x.yield.toFixed(3) + "<i>%</i></div>" + spark +
      '<div class="yield-changes">' +
        '<div><span>1 day</span><strong class="mono ' + cor(x.d1) + '">' + bp(x.d1) + " bp</strong></div>" +
        '<div><span>5 days</span><strong class="mono ' + cor(x.d5) + '">' + bp(x.d5) + " bp</strong></div>" +
        '<div><span>20 days</span><strong class="mono ' + cor(x.d20) + '">' + bp(x.d20) + " bp</strong></div>" +
      "</div>" +
      '<details class="yield-why"><summary><span>Why it moved, and where to look</span></summary>' +
        '<div class="yield-why-body">' +
          "<p><span>Size of today's move</span>" + forca +
            (x.sigma_bp ? ". One standard deviation on this curve is <b>" + x.sigma_bp.toFixed(1) +
             " bp</b>, from the last 252 observations." : ".") + "</p>" +
          "<p><span>What would explain a rise</span>inflation above expectations, a firm labour market, or a " +
            "hawkish turn — all of them make the market price fewer or later cuts from the " +
            (x.central_bank || "central bank") + ". A fall means the opposite.</p>" +
          "<p><span>Check the decision</span>" + (x.central_bank_url
            ? '<a href="' + x.central_bank_url + '" target="_blank" rel="noreferrer">' + x.central_bank +
              " — press releases</a>" : "\u2014") + "</p>" +
          "<p><span>Check the number</span>" + (x.source_url
            ? '<a href="' + x.source_url + '" target="_blank" rel="noreferrer">' + x.source + "</a>" : "\u2014") +
            " \u00b7 published " + (x.cadence || "\u2014") + "</p>" +
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
        nota.innerHTML = (d.meta && d.meta.note ? d.meta.note : "") +
          " Oldest reading on screen: <b>" + maior + " business days</b>. This page re-reads the file every " +
          "60 seconds, so it follows the next update without a reload.";
      }
    } catch (_) {
      grid.innerHTML = '<div class="empty-state">yields.json not generated yet — run update_yields.py.</div>';
    }
  }
  window.recarregaYields = carrega;   // o corte chama isto ao ser desligado
  carrega();
  setInterval(function () { if (!(window.timeCut && timeCut.active)) carrega(); }, 60000);
})();
