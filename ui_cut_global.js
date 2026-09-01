/* ==========================================================================
   HCI FUND Radar — corte temporal GLOBAL, setups pre-mapeados e traducao
   21/ago/2026. Carregado depois de ui_extras.js.
   Regra: com o corte ligado, NADA na tela pode ser posterior a data escolhida.
   O que nao pode ser reconstruido no passado e escondido, nunca estimado.
   ========================================================================== */

/* ---------- 1. bandeiras reais com fallback offline no chip ---------- */
const ISO2 = { USD: "us", EUR: "eu", GBP: "gb", JPY: "jp", AUD: "au", CAD: "ca", NZD: "nz", CHF: "ch" };

function bandeira(code) {
  const c = String(code || "").toUpperCase();
  const iso = ISO2[c];
  if (!iso) return "";
  const alt = c.slice(0, 2);
  return '<img class="ccy-flag" src="https://flagcdn.com/w40/' + iso + '.png" alt="' + c + '" loading="lazy" ' +
         'onerror="this.outerHTML=&quot;<span class=\'ccy-chip\' data-c=\'' + c + '\'>' + alt + '</span>&quot;">';
}
function marcaMoeda(code) { return bandeira(code) || chip(code); }
function marcaPar(par) {
  const t = String(par || "").toUpperCase();
  if (t.length < 6) return "";
  return '<span class="ccy-pair">' + marcaMoeda(t.slice(0, 3)) + marcaMoeda(t.slice(3, 6)) + "</span>";
}

/* ---------- 2. textos que ficaram em portugues ---------- */
const TRADUZ = [
  ["força agregada", "aggregate strength"], ["sem leitura", "no reading"],
  ["todas atuais", "all current"], ["bloqueado", "stale"],
  ["Todas as moedas", "All currencies"], ["Todos os impactos", "All impacts"],
  ["MÉDIO", "MEDIUM"], ["BAIXO", "LOW"], ["ALTO", "HIGH"],
  ["COMPRAR BASE", "BUY BASE"], ["VENDER BASE", "SELL BASE"],
  ["MERCADO FECHADO", "MARKET CLOSED"], ["FECHADO", "CLOSED"],
  ["COMPLETA", "FULL"], ["PARCIAL", "PARTIAL"], ["SEM DADO", "NO DATA"],
  ["dias completos", "full days"], ["parciais", "partial"],
  ["cobertura integral desde", "full coverage since"],
  ["Mercado fechado. Nenhuma leitura é reaproveitada.", "Market closed. No reading is carried over."],
  ["Referência", "As of"], ["Momento 20d", "20d momentum"],
  ["normalização 252d ex ante", "252d ex-ante normalisation"],
  ["lag +1 dia útil", "+1 business day lag"],
];

function traduzTela() {
  const sel = ".overview small, .overview span, #qualityNote, #calendarStatus, .calendar-day i, " +
    ".calendar-empty, #newsCurrency option, #newsImpact option, .news-impact, .formula, " +
    ".detail-label, #detailAsOf, .calendar-recommendations article, .empty-state, " +
    ".observation-summary, #nextDayStatus, .calendar-side, .direction-block span";
  document.querySelectorAll(sel).forEach((el) => {
    if (el.dataset.trad) return;
    let t = el.innerHTML;
    let mudou = false;
    TRADUZ.forEach((par) => {
      if (t.indexOf(par[0]) !== -1) { t = t.split(par[0]).join(par[1]); mudou = true; }
    });
    if (mudou) { el.innerHTML = t; el.dataset.trad = "1"; }
  });
}

/* ---------- 3. corte temporal GLOBAL ---------- */
const ABAS_SEM_PASSADO = {
  news: "Economic calendar history is not stored, so upcoming releases cannot be rebuilt for a past date.",
  backtest: "The backtest already runs on closed data — set an end date there instead of using the time cut.",
};

let anoDoCorte = [];

async function diaDoCalendario(iso) {
  try {
    const r = await fetch("data/calendar/calendar_" + iso.slice(0, 4) + ".json?x=" + Date.now());
    if (!r.ok) return null;
    const j = await r.json();
    anoDoCorte = j.days || [];                 // usado para refazer o grafico do par
    const dias = (j.days || []).filter((d) => d.date <= iso && d.market !== "FECHADO");
    return dias.length ? dias[dias.length - 1] : null;
  } catch (_) { return null; }
}

function avisoAba(nome, texto) {
  const painel = document.querySelector('.tab-panel[data-panel="' + nome + '"]');
  if (!painel) return;
  let av = painel.querySelector(".cut-block");
  if (!av) {
    av = document.createElement("div");
    av.className = "cut-block";
    painel.prepend(av);
  }
  av.innerHTML = "<strong>Hidden by the time cut</strong><span>" + texto + "</span>";
  painel.classList.add("is-cut-blocked");
}

function limpaAvisos() {
  document.querySelectorAll(".cut-block").forEach((e) => e.remove());
  document.querySelectorAll(".is-cut-blocked").forEach((e) => e.classList.remove("is-cut-blocked"));
}

async function sincronizaCorteGlobal() {
  if (!timeCut.active) {
    limpaAvisos();
    const nota = document.getElementById("cutSyncNote");
    if (nota) nota.remove();
    if (state.snapshot) { renderOverview(); renderPriorities(); renderNextDay(); }
    if (typeof recarregaYields === "function") recarregaYields();
    document.querySelectorAll(".cut-inline").forEach((e) => e.remove());
    if (state.snapshot) { renderPairTable(); renderSources(); renderCurrencies(); renderMatrix(); }
    setTimeout(() => { decorateFlags(); traduzTela(); }, 60);
    return;
  }
  Object.keys(ABAS_SEM_PASSADO).forEach((aba) => avisoAba(aba, ABAS_SEM_PASSADO[aba]));
  const dia = await diaDoCalendario(timeCut.date);
  if (!dia) {
    // FALHA SEGURA. Antes so imprimia a mensagem e voltava, deixando na tela os
    // numeros de HOJE com o corte ativo — uma queda de rede virava vazamento
    // silencioso, exatamente o que o corte existe para impedir.
    ["strongestCurrency", "weakestCurrency", "alignedPairs", "operationalPairs"]
      .forEach((id) => { const e = document.getElementById(id); if (e) e.textContent = "—"; });
    ["strongestValue", "weakestValue", "qualityNote"]
      .forEach((id) => { const e = document.getElementById(id); if (e) e.textContent = "hidden by the cut"; });
    const corpoVazio = document.getElementById("priorityTableBody");
    if (corpoVazio) corpoVazio.innerHTML = '<tr><td colspan="10" class="empty-state">Hidden by the time cut — that day could not be loaded.</td></tr>';
    const lista = document.getElementById("nextDayList");
    if (lista) lista.innerHTML = '<div class="calendar-empty">Hidden by the time cut.</div>';
    const yg = document.getElementById("yieldGrid");
    if (yg) yg.innerHTML = '<div class="empty-state">Hidden by the time cut — that day could not be loaded.</div>';
    document.getElementById("systemMessage").textContent =
      "No session data could be loaded for that date. Everything after the cut is hidden; nothing on screen is current.";
    return;
  }
  // Tudo que mostrava HOJE por baixo de um corte no passado. O calendario guarda,
  // por dia, o yield conhecido (`yields`) e o FUND dos 28 pares (`pair_funds`).
  pintaYields(dia.yields, dia.date);
  pintaPares(dia.pair_funds, dia);
  pintaFontes(dia.yields, dia.date);
  pintaMoedasEMatriz(dia);
  setTimeout(decorateFlags, 40);      // bandeiras nos paineis repintados

  const forte = dia.strongest, fraco = dia.weakest;
  document.getElementById("strongestCurrency").innerHTML = forte ? marcaMoeda(forte.currency) + " " + forte.currency : "—";
  document.getElementById("strongestValue").textContent = forte ? signed(forte.score) + " aggregate strength" : "no reading";
  document.getElementById("weakestCurrency").innerHTML = fraco ? marcaMoeda(fraco.currency) + " " + fraco.currency : "—";
  document.getElementById("weakestValue").textContent = fraco ? signed(fraco.score) + " aggregate strength" : "no reading";
  document.getElementById("alignedPairs").textContent = (dia.recommendations || []).length;
  document.getElementById("operationalPairs").textContent = dia.valid_pairs + "/28";
  document.getElementById("qualityNote").textContent =
    (dia.missing_currencies || []).length ? dia.missing_currencies.join(", ") + " stale" : "all current";
  document.getElementById("updatedAt").textContent = brDate(dia.date);

  const corpo = document.getElementById("priorityTableBody");
  const recs = dia.recommendations || [];
  corpo.innerHTML = recs.length
    ? recs.map((r, i) => '<tr data-pair="' + r.pair + '"><td class="mono">' + (i + 1) + "</td>" +
        '<td class="pair-code">' + marcaPar(r.pair) + r.pair + "</td>" +
        "<td>" + (r.decision === "COMPRAR_BASE" ? "BUY BASE" : "SELL BASE") + "</td>" +
        '<td class="mono ' + signClass(r.fund) + '">' + signed(r.fund) + "</td>" +
        '<td class="mono" colspan="6">' + esc(r.reason || "") + "</td></tr>").join("")
    : '<tr><td colspan="10" class="empty-state">No pair reached |FUND| &ge; 25 on this day.</td></tr>';

  const lista = document.getElementById("nextDayList");
  const watch = dia.pre_fund_watch || [];
  if (lista) {
    lista.innerHTML = watch.length
      ? watch.map((w) => '<article class="observation-card"><div class="obs-head">' +
          '<span class="mono">' + w.rank + "</span>" + marcaPar(w.pair) + "<strong>" + w.pair + "</strong>" +
          '<em class="prefund-outcome hidden-outcome">outcome hidden</em></div>' +
          '<div class="obs-body"><span>FUND ' + signed(w.fund) + "</span>" +
          "<span>chance " + w.empirical_probability + "%</span>" +
          '<span class="muted">n ' + w.empirical_samples + "</span></div></article>").join("")
      : '<div class="calendar-empty">No pair passed the observation floor on this day.</div>';
  }
  const st = document.getElementById("nextDayStatus");
  if (st) st.textContent = "Watchlist as published on " + brDate(dia.date) + " — outcomes hidden by the time cut.";

  if (!document.getElementById("cutSyncNote")) {
    const nota = document.createElement("p");
    nota.id = "cutSyncNote";
    nota.className = "cut-sync-note";
    nota.textContent = "Header, overview and watchlist rebuilt from that day's calendar. News and backtest are hidden.";
    document.getElementById("timeCutBanner").after(nota);
  }
  traduzTela();
}

const _setTimeCutBase = setTimeCut;
setTimeCut = async function (valor) {
  await _setTimeCutBase(valor);
  await sincronizaCorteGlobal();
  await renderSetups();
};

/* ---------- 4. watchlist de setups (sem coordenadas) ----------
   Decisao do Eduardo (21/ago): o site NAO mostra zona, stop nem nivel do BO
   enquanto o motor de BO/ZOI nao estiver maduro. Aqui fica so a DIRECAO e o
   estado de vigilancia. As coordenadas continuam no setups.json para estudo.

   ATIVO ("watching") exige as duas coisas:
     (a) o par estar no TOP 5 tradable do dia, e
     (b) o FUND estar MADURO — pelo menos 4 pregoes na mesma faixa.
   Abaixo de 4 pregoes o proprio backtest mostra PF ~1,0 (ruido).            */
const MATURIDADE_MINIMA = 4;

async function idadeDoFund(par) {
  try {
    if (!window.__fundCsv) {
      const r = await fetch("data/fund_snapshot.json?x=" + Date.now());
      window.__fundCsv = await r.json();
    }
    const p = (window.__fundCsv.pairs || []).find((x) => x.pair === par);
    return p && typeof p.days_in_band === "number" ? p.days_in_band : null;
  } catch (_) { return null; }
}

function topCincoTradable() {
  const linhas = document.querySelectorAll("#priorityTableBody tr[data-pair]");
  return Array.from(linhas).slice(0, 5).map((tr) => tr.dataset.pair);
}

async function renderSetups() {
  // 01/set: a aba Pre-FUND (observations) saiu do site.
  if (!document.getElementById("setupList")) return;
  const lista = document.getElementById("setupList");
  const status = document.getElementById("setupStatus");
  if (!lista) return;
  if (typeof timeCut !== "undefined" && timeCut.active) {
    lista.innerHTML = "";
    status.textContent = "The watchlist is built from the live chart and is hidden under the time cut.";
    return;
  }
  try {
    const r = await fetch("data/setups.json?x=" + Date.now());
    if (!r.ok) throw new Error("no file");
    const j = await r.json();
    const cands = j.candidates || [];
    if (!cands.length) throw new Error("empty");
    const top5 = topCincoTradable();
    status.textContent = "Signal date " + j.meta.signal_date +
      " · watching turns on when the pair is in the top 5 and the FUND has held its band for " +
      MATURIDADE_MINIMA + "+ sessions";

    const cartoes = await Promise.all(cands.map(async (c) => {
      const pf = c.prefund || {};
      const venda = c.direction === "SHORT";
      const temEstrutura = c.status === "OK";
      const s = temEstrutura ? c.setups[0] : null;
      const noTop5 = top5.indexOf(c.pair) !== -1;
      const idade = await idadeDoFund(c.pair);
      const maduro = idade === null ? null : idade >= MATURIDADE_MINIMA;
      const ativo = noTop5 && maduro === true;
      const estado = ativo ? ["WATCHING", "live"]
        : !temEstrutura ? ["NO STRUCTURE", "spent"]
        : s.state === "CONSUMIDA" || s.state === "PASSOU" ? ["SPENT", "spent"]
        : ["ON DECK", "waiting"];
      const passo = (ok, txt, det) =>
        '<li class="' + (ok === true ? "done" : ok === null ? "unknown" : "pending") + '">' +
        '<span class="tick">' + (ok === true ? "✓" : ok === null ? "?" : "○") + "</span>" +
        "<div><strong>" + txt + "</strong>" + (det ? "<small>" + det + "</small>" : "") + "</div></li>";
      return '<article class="setup-card' + (ativo ? " is-live" : "") + '">' +
        "<header>" + marcaPar(c.pair) + "<strong>" + c.pair + "</strong>" +
        '<span class="setup-side ' + (venda ? "sell" : "buy") + '">' + (venda ? "SELL" : "BUY") + "</span>" +
        '<em class="setup-state ' + estado[1] + '">' + estado[0] + "</em></header>" +
        '<p class="setup-lead">What has to line up</p>' +
        "<ol class=\"setup-check\">" +
          passo(true, "FUND may flip", pf.probability + "% vs 7.15% base rate") +
          passo(noTop5, "Pair in the top 5 tradable", noTop5 ? "yes" : "not yet") +
          passo(maduro, "FUND band is mature",
                idade === null ? "age unavailable" : idade + " session" + (idade === 1 ? "" : "s") +
                " in band · needs " + MATURIDADE_MINIMA + "+") +
          passo(temEstrutura && s.state !== "PASSOU" && s.state !== "CONSUMIDA",
                "Structure on the chart",
                temEstrutura ? (s.state === "NA_ZONA" ? "price at the zone" :
                  s.state === "AGUARDANDO" ? "zone still standing" : "already spent")
                  : "nothing pre-mapped") +
          passo(false, "30m candle reacts in the zone", "your call, on the chart") +
        "</ol>" +
        '<p class="setup-note">Direction only. Levels stay off the panel while the ' +
        "structure engine is still being calibrated.</p></article>";
    }));
    lista.innerHTML = cartoes.join("");
  } catch (_) {
    lista.innerHTML = "";
    status.textContent = "No watchlist yet. Run update_setups.py after refreshing the FUND.";
  }
}

/* ---------- 5. engate no ciclo de vida ---------- */
const _activateTabBase = activateTab;
activateTab = function (nome) {
  _activateTabBase(nome);
  if (nome === "observations") renderSetups();
  traduzTela();
};

setTimeout(function () { renderSetups(); traduzTela(); }, 1300);

/* ---------- 6. decorateFlags passa a usar bandeira real ---------- */
decorateFlags = function () {
  const put = (el) => {
    if (!el || el.dataset.flagDone) return;
    const txt = el.textContent.trim();
    const marca = txt.length >= 6 ? marcaPar(txt) : marcaMoeda(txt.toUpperCase());
    if (!marca) return;
    el.dataset.flagDone = "1";
    el.innerHTML = marca + esc(txt);
  };
  document.querySelectorAll("#priorityTableBody tr td:nth-child(2), #pairTableBody tr td:first-child").forEach(put);
  document.querySelectorAll(".currency-grid strong, .calendar-currency-row strong").forEach(put);
  document.querySelectorAll(".calendar-prefund .prefund-row strong, .calendar-recommendations article strong").forEach(put);
  document.querySelectorAll(".observation-card strong, .cot-card header strong").forEach(put);
  document.querySelectorAll("#calendarProjection .observation-item summary strong").forEach(put);
};
setTimeout(decorateFlags, 1500);


/* ---------- 7. aba YIELDS sob o corte de tempo ----------
   Reusa o mesmo cartao da versao ao vivo, mas com o valor que era conhecido no
   dia selecionado: `dia.yields[MOEDA]` traz a ultima observacao publicada ATE
   aquela data, com a defasagem real e as variacoes calculadas so com o passado. */
function pintaYields(mapa, diaISO) {
  const grid = document.getElementById("yieldGrid");
  if (!grid) return;
  if (!mapa) {
    grid.innerHTML = '<div class="empty-state">No yield reading available on or before that date.</div>';
    return;
  }
  const bp = (v) => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + v.toFixed(1);
  const cor = (v) => v === null || v === undefined ? "" : (v > 0 ? "positive" : v < 0 ? "negative" : "");
  const itens = Object.keys(mapa).map((m) => Object.assign({ c: m }, mapa[m]))
    .sort((a, b) => b.y - a.y);
  grid.innerHTML = itens.map((x) => {
    const z = (x.d1 !== null && x.sg) ? Math.abs(x.d1 / x.sg) : null;
    const forca = z === null ? "no reading"
      : z < 1 ? "inside the daily noise"
      : z < 2 ? "a real move, " + z.toFixed(1) + "σ"
      : "a large move, " + z.toFixed(1) + "σ";
    const velho = x.s >= 5 ? "is-stale" : x.s >= 3 ? "is-aging" : "";
    return '<article class="yield-card ' + velho + '">' +
      '<header><strong>' + x.c + "</strong><span class=\"yield-stale\">" +
        (x.s === 0 ? "same day" : x.s + (x.s === 1 ? " business day old" : " business days old")) +
      "</span></header>" +
      '<div class="yield-value mono">' + x.y.toFixed(3) + "<i>%</i></div>" +
      '<div class="yield-changes">' +
        '<div><span>1 day</span><strong class="mono ' + cor(x.d1) + '">' + bp(x.d1) + " bp</strong></div>" +
        '<div><span>5 days</span><strong class="mono ' + cor(x.d5) + '">' + bp(x.d5) + " bp</strong></div>" +
        '<div><span>20 days</span><strong class="mono ' + cor(x.d20) + '">' + bp(x.d20) + " bp</strong></div>" +
      "</div>" +
      '<details class="yield-why"><summary><span>Why it moved</span></summary><div class="yield-why-body">' +
        "<p><span>Size of that move</span>" + forca +
          (x.sg ? ". One standard deviation was <b>" + x.sg.toFixed(1) + " bp</b> at the time." : ".") + "</p>" +
        "<p><span>Observation used</span><b>" + x.a + "</b> — the last one published on or before " +
          brDate(diaISO) + ". Links are hidden under the cut: they would show today's page.</p>" +
      "</div></details></article>";
  }).join("");
  const nota = document.getElementById("yieldNote");
  if (nota) {
    nota.innerHTML = "Time cut active. Showing the 2-year yield as it was known on <b>" + brDate(diaISO) +
      "</b> — the last observation published on or before that date, with changes computed only from earlier " +
      "observations. Nothing after the cut is used.";
  }
}

/* ---------- 8. abas PAIRS e SOURCES sob o corte de tempo ----------
   Eram os dois ultimos vazamentos: a tabela de pares e o detalhe do par
   mostravam o FUND de HOJE, e a tabela de fontes mostrava a ultima observacao
   de HOJE, tudo por baixo de um corte no passado. O calendario ja guarda, por
   dia, o FUND dos 28 pares (`pair_funds`) e o yield conhecido (`yields`). */
function faixaDoFund(v) {
  return v >= 60 ? "STRONG_BULL" : v >= 25 ? "BULL"
    : v > -25 ? "NEUTRAL" : v > -60 ? "BEAR" : "STRONG_BEAR";
}

function pintaPares(mapa, dia) {
  const diaISO = dia.date;
  const corpo = document.getElementById("pairTableBody");
  if (corpo) {
    if (!mapa) {
      corpo.innerHTML = '<tr><td colspan="9" class="empty-state">Hidden by the time cut.</td></tr>';
    } else {
      const linhas = Object.keys(mapa).map((p) => ({ p: p, f: mapa[p] }))
        .sort((a, b) => Math.abs(b.f) - Math.abs(a.f));
      corpo.innerHTML = linhas.map((x) => {
        const fx = faixaDoFund(x.f);
        const lado = Math.abs(x.f) < 25 ? "—" : (x.f > 0 ? "BUY BASE" : "SELL BASE");
        return '<tr data-pair="' + x.p + '"><td class="pair-code">' + x.p + "</td>" +
          '<td class="mono ' + (x.f >= 0 ? "positive" : "negative") + '">' + signed(x.f) + "</td>" +
          "<td>" + fx.replace("_", " ") + "</td><td>" + lado + "</td>" +
          '<td class="mono muted">—</td><td class="mono muted">—</td><td class="mono muted">—</td>' +
          '<td class="muted">—</td><td class="muted">after the cut</td></tr>';
      }).join("");
    }
  }

  // O PAR INDICADO DO DIA: o primeiro da lista de tradable daquela data.
  // Antes o painel ficava com o par de HOJE e os campos zerados; agora ele
  // mostra o par que o radar apontaria naquele dia, com o grafico refeito a
  // partir do FUND diario que o calendario guarda.
  const rec = (dia.recommendations || [])[0];
  const det = document.getElementById("pairDetail");
  if (!det) return;
  det.querySelectorAll(".cut-inline").forEach((e) => e.remove());
  if (!rec || !mapa) {
    const av = document.createElement("p");
    av.className = "cut-inline";
    av.innerHTML = "Time cut active. No pair reached the tradable threshold on " + brDate(diaISO) + ".";
    det.prepend(av);
    return;
  }
  const par = rec.pair, base = par.slice(0, 3), quote = par.slice(3);
  const hist = anoDoCorte
    .filter((d) => d.date <= diaISO && d.pair_funds && d.pair_funds[par] !== undefined)
    .map((d) => ({ date: d.date, fund: d.pair_funds[par] }));
  const f5 = hist.length > 5 ? rec.fund - hist[hist.length - 6].fund : null;
  const yb = (dia.yields || {})[base], yq = (dia.yields || {})[quote];
  renderPairDetail({
    pair: par, base: base, quote: quote, fund: rec.fund,
    strength: rec.strength, decision: rec.decision, data_status: "CURRENT",
    change_5d: f5, operational: true, exit_alert: null,
    spread: (yb && yq) ? yb.y - yq.y : null,
    momentum20: (yb && yq && yb.d20 !== null && yq.d20 !== null) ? (yb.d20 - yq.d20) / 100 : null,
    yield_base: yb ? yb.y : null, yield_quote: yq ? yq.y : null,
    as_of: diaISO, history: hist,
  });
  const av = document.createElement("p");
  av.className = "cut-inline";
  av.innerHTML = "Time cut active. Showing <b>" + par + "</b> — the pair the radar ranked first on " +
    brDate(diaISO) + ". The chart is rebuilt from the daily FUND stored for each session up to that date; " +
    "nothing after the cut is used. The backtest column stays hidden because it ends today.";
  det.prepend(av);
}

function pintaFontes(mapa, diaISO) {
  const corpo = document.getElementById("sourceTableBody");
  if (!corpo) return;
  if (!mapa) {
    corpo.innerHTML = '<tr><td colspan="8" class="empty-state">Hidden by the time cut.</td></tr>';
    return;
  }
  const fontes = (typeof state !== "undefined" && state.snapshot && state.snapshot.sources) || [];
  corpo.innerHTML = fontes.map((f) => {
    const y = mapa[f.currency];
    if (!y) return "";
    const est = y.s >= 5 ? "STALE" : y.s >= 3 ? "DELAYED" : "CURRENT";
    const cls = est === "CURRENT" ? "quality-current" : est === "DELAYED" ? "quality-delayed" : "quality-stale";
    return '<tr><td class="pair-code">' + f.currency + "</td>" +
      '<td class="mono">' + y.y.toFixed(3) + "%</td>" +
      "<td>" + brDate(f.first_observation) + "</td><td>" + brDate(y.a) + "</td>" +
      '<td class="mono">' + y.s + " du</td>" +
      '<td><span class="tag ' + cls + '">' + est + "</span></td>" +
      '<td><a href="' + f.source_url + '" target="_blank" rel="noreferrer">' + f.source + "</a></td>" +
      '<td class="muted">' + (f.route || "") + "</td></tr>";
  }).join("");
}

/* ---------- 9. faixa de moedas e matriz sob o corte ----------
   Ultimos dois paineis que ainda mostravam HOJE. A faixa vem do ranking do dia
   (`dia.currencies`); a matriz vem do FUND dos 28 pares (`dia.pair_funds`),
   invertendo o sinal quando a moeda da linha e a QUOTE do par. */
const ORDEM_MOEDAS = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"];

function pintaMoedasEMatriz(dia) {
  const grid = document.getElementById("currencyGrid");
  if (grid) {
    const cs = (dia.currencies || []).filter((c) => c.score !== null && c.score !== undefined);
    grid.innerHTML = cs.length ? cs.map((c, i) =>
      '<article class="currency-item"><header><strong>' + c.currency + "</strong><span>#" + (i + 1) +
      '</span></header><div class="value ' + (c.score >= 0 ? "positive" : "negative") + '">' +
      signed(c.score) + '</div><footer><span>' + String(c.strength || "").replace("_", " ") +
      "</span><span>" + (c.valid_crosses !== undefined ? c.valid_crosses + "/7" : "—") +
      "</span></footer></article>").join("")
      : '<div class="empty-state">No currency ranking for that day.</div>';
  }
  const tab = document.getElementById("strengthMatrix");
  const pf = dia.pair_funds;
  if (tab) {
    if (!pf) {
      tab.innerHTML = '<tbody><tr><td class="empty-state">Hidden by the time cut.</td></tr></tbody>';
    } else {
      const val = (a, b) => pf[a + b] !== undefined ? pf[a + b]
        : pf[b + a] !== undefined ? -pf[b + a] : null;
      const tom = (v) => v === null ? "tone-blocked" : v >= 60 ? "tone-strong-bull" : v >= 25 ? "tone-bull"
        : v > -25 ? "tone-neutral" : v > -60 ? "tone-bear" : "tone-strong-bear";
      tab.innerHTML = "<thead><tr><th>STRENGTH</th>" +
        ORDEM_MOEDAS.map((c) => "<th>" + c + "</th>").join("") + "</tr></thead><tbody>" +
        ORDEM_MOEDAS.map((linha) => "<tr><th>" + linha + "</th>" +
          ORDEM_MOEDAS.map((col) => {
            if (linha === col) return '<td class="matrix-empty">—</td>';
            const v = val(linha, col);
            return '<td><button type="button" class="matrix-cell ' + tom(v) + '" disabled>' +
              (v === null ? "—" : signed(v, 0)) + "</button></td>";
          }).join("") + "</tr>").join("") + "</tbody>";
    }
  }
}
