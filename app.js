"use strict";

const state = {
  snapshot: null,
  defaultBacktest: null,
  currentBacktest: null,
  selectedPair: null,
  pairFilter: "all",
  pairSearch: "",
  newsCurrency: "ALL",
  newsImpact: "ALL",
  calendarIndex: null,
  calendarYears: new Map(),
  calendarMonth: null,
  calendarSelectedDate: null,
};

const currencyOrder = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"];
const $ = (selector) => document.querySelector(selector);

const strengthLabels = {
  STRONG_BULL: "STRONG BULL", BULL: "BULL", NEUTRAL: "NEUTRAL",
  BEAR: "BEAR", STRONG_BEAR: "STRONG BEAR", SEM_DADO: "NO DATA",
};

const weightLabels = {"NIVEL_FUND": "FUND level", "FUND_PESADO": "FUND heavy", "PESOS_IGUAIS": "Equal weights", "PRECO_PESADO": "Price heavy", "APRENDIDO": "Learned weights"};
const decisionLabels = {
  COMPRAR_BASE: "BUY BASE", VENDER_BASE: "SELL BASE",
  NEUTRAL: "AGUARDAR", DADO_BLOQUEADO: "DADO BLOQUEADO",
};
const qualityLabels = { CURRENT: "CURRENT", DELAYED: "DELAYED", STALE: "STALE" };
const exitLabels = {
  SAIR_LONG: "EXIT LONG", SAIR_SHORT: "EXIT SHORT",
  FORTALECEU: "STRENGTHENED", MUDOU_FAIXA: "BAND CHANGED",
};

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[char]));
}

function signed(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  const number = Number(value);
  return `${number > 0 ? "+" : ""}${number.toFixed(digits)}`;
}

function plain(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toFixed(digits);
}

function percent(value, digits = 1) {
  return value === null || value === undefined ? "—" : `${signed(value, digits)}%`;
}

function pfText(summary) {
  if (!summary) return "—";
  if (summary.no_loss_pf) return "∞";
  return summary.profit_factor === null ? "—" : plain(summary.profit_factor, 2);
}

function brDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })
    .format(new Date(`${value.slice(0, 10)}T12:00:00`));
}

function brDateTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit",
    hour: "2-digit", minute: "2-digit",
  }).format(new Date(value));
}

function signClass(value) {
  if (Number(value) > 0) return "positive";
  if (Number(value) < 0) return "negative";
  return "muted";
}

function tone(score, blocked = false) {
  if (blocked) return "tone-blocked";
  if (score >= 60) return "tone-strong-bull";
  if (score >= 25) return "tone-bull";
  if (score <= -60) return "tone-strong-bear";
  if (score <= -25) return "tone-bear";
  return "tone-neutral";
}

function qualityClass(status) { return `quality-${String(status).toLowerCase()}`; }
function validationText(value) { return value === "PIT_CAUSAL" ? "CAUSAL" : "PROVISIONAL"; }

function pairByCurrencies(left, right) {
  return state.snapshot.pairs.find((pair) =>
    (pair.base === left && pair.quote === right) || (pair.base === right && pair.quote === left));
}

function pairReading(priority) {
  const pf = Number(priority.profit_factor || 0);
  if (pf >= 1.5) return ["STRONG HISTORY", "read-pass"];
  if (pf >= 1.2) return ["POSITIVE HISTORY", "read-pass"];
  if (pf > 1.0) return ["FRAGILE EDGE", "warning"];
  return ["REPROVADO", "read-fail"];
}

function showMessage(text, error = false) {
  const node = $("#systemMessage");
  node.textContent = text;
  node.classList.toggle("error", error);
}

function renderOverview() {
  const currencies = state.snapshot.currencies.filter((item) => item.score !== null);
  const strongest = currencies[0];
  const weakest = currencies[currencies.length - 1];
  $("#strongestCurrency").textContent = strongest?.currency || "—";
  $("#strongestValue").textContent = strongest ? `${signed(strongest.score)} aggregate strength` : "no reading";
  $("#weakestCurrency").textContent = weakest?.currency || "—";
  $("#weakestValue").textContent = weakest ? `${signed(weakest.score)} aggregate strength` : "no reading";
  $("#alignedPairs").textContent = state.snapshot.meta.aligned_pairs;
  $("#operationalPairs").textContent = `${state.snapshot.meta.operational_pairs}/${state.snapshot.meta.pairs}`;
  const blocked = state.snapshot.sources.filter((source) => source.status !== "CURRENT").map((source) => source.currency);
  $("#qualityNote").textContent = blocked.length ? `${blocked.join(", ")} stale` : "all current";
  $("#updatedAt").textContent = brDateTime(state.snapshot.meta.generated_at);
}

function renderPriorities() {
  const body = $("#priorityTableBody");
  const rows = state.snapshot.priorities;
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="10" class="empty-state">No pair currently clears direction, data quality and a historical PF above 1 at the same time.</td></tr>';
    return;
  }
  body.innerHTML = rows.map((item) => {
    const [reading, className] = pairReading(item);
    return `<tr data-pair="${item.pair}">
      <td class="mono">${item.rank}</td><td class="pair-code">${item.pair}</td>
      <td>${decisionLabels[item.decision]}</td><td class="mono ${signClass(item.fund)}">${signed(item.fund)}</td>
      <td class="mono"><strong>${plain(item.profit_factor, 2)}</strong></td><td class="mono">${item.trades}</td>
      <td class="mono">${plain(item.win_rate, 1)}%</td><td class="mono ${signClass(item.net_return_pct)}">${percent(item.net_return_pct)}</td>
      <td class="mono negative">−${plain(item.max_drawdown_pct, 1)}%</td><td class="${className}">${reading}</td>
    </tr>`;
  }).join("");
  bindPairRows(body);
}

function renderNextDay() {
  const data = state.snapshot.pre_fund;
  const priceData = state.snapshot.next_day;
  const status = $("#nextDayStatus");
  const summary = $("#nextDaySummary");
  const list = $("#nextDayList");
  const table = $("#weightTableBody");
  if (!data) {
    status.className = "observation-verdict is-rejected";
    status.innerHTML = "<strong>UNAVAILABLE</strong><span>Refresh the radar to build the pre-FUND audit.</span>";
    summary.innerHTML = ""; list.innerHTML = ""; table.innerHTML = "";
    return;
  }

  const best = data.best_model;
  const modelLabels = {
    NIVEL_FUND: "FUND level", FUND_PESADO: "FUND heavy", PESOS_IGUAIS: "Equal weights",
    PRECO_PESADO: "Price heavy", APRENDIDO: "Learned weights",
  };
  const lift = Number(best.top1_transition_rate) / Math.max(Number(best.baseline_transition_rate), 0.0001);
  status.className = "observation-verdict is-pre-fund";
  status.innerHTML = `<strong>PRE-FUND WATCHLIST</strong>
    <span>Rank 1 entered BEAR the next day in ${plain(best.top1_transition_rate, 2)}% of tests, against a base rate of ${plain(best.baseline_transition_rate, 2)}%.</span>`;

  summary.innerHTML = `
    <div><span>Out-of-sample days</span><strong>${best.days}</strong><small>${data.meta.history_start.slice(0, 4)}–${data.meta.history_end.slice(0, 4)}</small></div>
    <div><span>Base rate of a flip</span><strong>${plain(best.baseline_transition_rate, 2)}%</strong><small>all eligible pairs</small></div>
    <div><span>Pre-FUND rank 1</span><strong>${plain(best.top1_transition_rate, 2)}%</strong><small>${plain(lift, 2)}× the base rate</small></div>
    <div><span>Events captured</span><strong>${plain(best.event_recall_top5, 2)}%</strong><small>present in the top 5</small></div>
    <div><span>Price fell D+1</span><strong>${plain(best.top1_price_fall_rate, 2)}%</strong><small>no price edge</small></div>`;

  const weightsText = (weights) => {
    return [weights.level, weights.trajectory, weights.price]
      .map((value) => `${Math.round(Number(value) * 100)}`).join("/");
  };
  table.innerHTML = data.comparison.map((row) => `<tr class="${row.model === data.meta.best_model ? "is-best-weight" : ""}">
    <td>${modelLabels[row.model] || esc(row.model)}</td><td class="mono">${weightsText(row.weights)}</td>
    <td class="mono">${plain(row.top1_transition_rate, 2)}%</td>
    <td class="mono">${plain(row.top5_transition_rate, 2)}%</td>
    <td class="mono">${plain(row.event_recall_top5, 2)}%</td>
    <td class="mono ${Number(row.top1_price_fall_rate) > 50 ? "positive" : "negative"}">${plain(row.top1_price_fall_rate, 2)}%</td>
    <td class="mono ${signClass(row.top5_avg_price_return_pct)}">${percent(row.top5_avg_price_return_pct, 3)}</td>
  </tr>`).join("");

  const observationFloor = Number(best.baseline_transition_rate) * 1.25;
  const goodObservations = data.observations.filter((item) => Number(item.empirical_probability) >= observationFloor);
  if (!goodObservations.length) {
    list.innerHTML = `<div class="empty-state">No pair cleared the ${plain(observationFloor, 2)}% observation floor today.</div>`;
  } else {
    const baseRate = Number(best.baseline_transition_rate);
    list.innerHTML = goodObservations.map((item, index) => {
      const chance = Number(item.empirical_probability);
      const multiplo = baseRate > 0 ? chance / baseRate : null;
      // distancia ate a borda BEAR: o unico numero que o Eduardo usa para decidir se vale abrir o grafico
      const faltam = -25 - Number(item.fund);
      const banda = Number(item.fund) <= -25
        ? "already inside the BEAR band"
        : `${plain(Math.abs(faltam), 1)} points from the BEAR band`;
      return `<details class="observation-item" ${index === 0 ? "open" : ""}>
      <summary>
        <span class="observation-rank">${item.rank}</span><strong>${item.pair}</strong>
        <span class="warning">WATCH</span>
        <span class="observation-chance">${plain(chance, 1)}%${multiplo ? ` <i>${plain(multiplo, 1)}× base rate</i>` : ""}</span>
      </summary>
      <div class="observation-detail">
        <p class="observation-band"><strong class="${signClass(item.fund)}">FUND ${signed(item.fund)}</strong><span>${banda}</span></p>
        <div class="observation-reasons">${item.reasons.filter((reason) => !/proximity/i.test(reason.factor)).map((reason) => `<p class="${reason.supports_alert ? "supports" : "opposes"}"><strong>${esc(reason.factor)}</strong>${esc(reason.text)}</p>`).join("")}</div>
      </div>
    </details>`;
    }).join("");
  }

  $("#preFundAudit").innerHTML = "";   // replay cego removido a pedido do Eduardo (21/ago)

  if (priceData) {
    const direct = priceData.best_model;
    $("#priceNextDayVerdict").innerHTML = `<strong>Price fall D+1: no edge</strong><span>Best direct test was ${plain(direct.top1_fall_accuracy, 2)}% (95% CI ${plain(direct.top1_ci95_low, 2)}–${plain(direct.top1_ci95_high, 2)}%). The alert anticipates the direction of the FUND — it does not authorise a trade before the structure confirms.</span>`;
  }
  $("#nextDayMethod").textContent = `${data.meta.status}: ${data.meta.validation}. ${data.meta.warning}`;
}

function renderCurrencies() {
  $("#currencyGrid").innerHTML = state.snapshot.currencies.map((item, index) => `
    <article class="currency-item ${item.data_status !== "CURRENT" ? "is-blocked" : ""}">
      <header><strong>${item.currency}</strong><span>#${index + 1}</span></header>
      <div class="value ${signClass(item.score)}">${signed(item.score)}</div>
      <footer><span>${strengthLabels[item.strength]}</span><span>${item.valid_crosses}/7</span></footer>
    </article>`).join("");
}

function renderMatrix() {
  const header = `<thead><tr><th>STRENGTH</th>${currencyOrder.map((currency) => `<th>${currency}</th>`).join("")}</tr></thead>`;
  const rows = currencyOrder.map((rowCurrency) => {
    const cells = currencyOrder.map((columnCurrency) => {
      if (rowCurrency === columnCurrency) return '<td class="matrix-empty">—</td>';
      const pair = pairByCurrencies(rowCurrency, columnCurrency);
      const score = pair.base === rowCurrency ? pair.fund : -pair.fund;
      return `<td><button type="button" class="matrix-cell ${tone(score, !pair.operational)}" data-pair="${pair.pair}" aria-label="${rowCurrency} against ${columnCurrency}: ${signed(score)}">${signed(score, 0)}</button></td>`;
    }).join("");
    return `<tr><th>${rowCurrency}</th>${cells}</tr>`;
  }).join("");
  const table = $("#strengthMatrix");
  table.innerHTML = `${header}<tbody>${rows}</tbody>`;
  table.querySelectorAll("[data-pair]").forEach((button) => button.addEventListener("click", () => selectPair(button.dataset.pair, true)));
}

function selectPair(pairName, scroll = false) {
  const pair = state.snapshot.pairs.find((item) => item.pair === pairName);
  if (!pair) return;
  state.selectedPair = pairName;
  renderPairDetail(pair);
  if (scroll) $("#pairDetail").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderPairDetail(pair) {
  $("#detailPair").textContent = pair.pair;
  $("#detailStrength").textContent = strengthLabels[pair.strength];
  $("#detailQuality").textContent = qualityLabels[pair.data_status];
  $("#detailQuality").className = `tag ${qualityClass(pair.data_status)}`;
  $("#detailDecision").textContent = decisionLabels[pair.decision];
  $("#detailDecision").className = pair.decision === "COMPRAR_BASE" ? "positive" : pair.decision === "VENDER_BASE" ? "negative" : pair.decision === "DADO_BLOQUEADO" ? "warning" : "muted";
  $("#detailFund").textContent = signed(pair.fund); $("#detailFund").className = signClass(pair.fund);
  $("#detailChange").textContent = signed(pair.change_5d); $("#detailChange").className = signClass(pair.change_5d);
  $("#detailSpread").textContent = `${signed(pair.spread, 3)} pp`;
  $("#detailMomentum").textContent = `${signed(pair.momentum20, 3)} pp`;
  $("#detailBaseYield").textContent = `${pair.base} ${plain(pair.yield_base, 3)}%`;
  $("#detailQuoteYield").textContent = `${pair.quote} ${plain(pair.yield_quote, 3)}%`;
  $("#detailAsOf").textContent = `As of ${brDate(pair.as_of)}`;
  const alert = $("#detailAlert");
  if (pair.operational && pair.exit_alert) {
    alert.hidden = false;
    alert.textContent = `${exitLabels[pair.exit_alert]} — ${pair.exit_detail}.`;
  } else { alert.hidden = true; alert.textContent = ""; }
  drawFundChart(pair.history);
}

function drawFundChart(history) {
  const svg = $("#fundChart");
  const points = history.slice(-150);
  const width = 960, height = 260, left = 45, right = 43, top = 14, bottom = 27;
  const x = (index) => left + index / Math.max(1, points.length - 1) * (width - left - right);
  const y = (value) => top + (100 - value) / 200 * (height - top - bottom);
  const path = points.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(2)},${y(point.fund).toFixed(2)}`).join(" ");
  const guides = [60, 25, 0, -25, -60].map((value) => `<line class="${value ? "chart-threshold" : "chart-zero"}" x1="${left}" y1="${y(value)}" x2="${width - right}" y2="${y(value)}"></line><text class="chart-label" x="${width - right + 7}" y="${y(value) + 3}">${signed(value, 0)}</text>`).join("");
  const tickIndexes = [0, Math.floor((points.length - 1) / 2), Math.max(0, points.length - 1)];
  const ticks = tickIndexes.filter((value, index, values) => values.indexOf(value) === index).map((index) => `<text class="chart-label" x="${x(index)}" y="${height - 8}" text-anchor="${index === 0 ? "start" : index === points.length - 1 ? "end" : "middle"}">${brDate(points[index]?.date)}</text>`).join("");
  const latest = points[points.length - 1];
  svg.innerHTML = `${guides}${path ? `<path class="chart-line" d="${path}"></path>` : ""}${latest ? `<circle class="chart-latest" cx="${x(points.length - 1)}" cy="${y(latest.fund)}" r="3"></circle>` : ""}${ticks}`;
}

function filteredPairs() {
  const term = state.pairSearch.toUpperCase().trim();
  return state.snapshot.pairs.filter((pair) => {
    if (term && !pair.pair.includes(term)) return false;
    if (state.pairFilter === "directional") return pair.operational && Math.abs(pair.fund) >= 25;
    if (state.pairFilter === "neutral") return pair.operational && Math.abs(pair.fund) < 25;
    if (state.pairFilter === "blocked") return !pair.operational;
    if (state.pairFilter === "exit") return pair.operational && pair.exit_alert?.startsWith("SAIR");
    return true;
  });
}

function renderPairTable() {
  const body = $("#pairTableBody");
  const rows = filteredPairs();
  if (!rows.length) { body.innerHTML = '<tr><td colspan="9" class="empty-state">No pair found.</td></tr>'; return; }
  body.innerHTML = rows.map((pair) => `<tr data-pair="${pair.pair}" class="${pair.operational ? "" : "blocked-row"}">
    <td class="pair-code">${pair.pair}</td><td class="mono ${signClass(pair.fund)}">${signed(pair.fund)}</td>
    <td>${strengthLabels[pair.strength]}</td><td>${decisionLabels[pair.decision]}</td><td class="mono ${signClass(pair.change_5d)}">${signed(pair.change_5d)}</td>
    <td class="mono">${pfText(pair.backtest)}</td><td class="mono">${pair.backtest?.trades ?? "—"}</td>
    <td class="${pair.backtest?.validation === "PIT_CAUSAL" ? "positive" : "warning"}">${validationText(pair.backtest?.validation)}</td>
    <td><span class="tag ${qualityClass(pair.data_status)}">${qualityLabels[pair.data_status]}</span></td>
  </tr>`).join("");
  bindPairRows(body);
}

function bindPairRows(container) {
  container.querySelectorAll("[data-pair]").forEach((row) => row.addEventListener("click", () => selectPair(row.dataset.pair, true)));
}

function renderSources() {
  $("#sourceTableBody").innerHTML = state.snapshot.sources.map((source) => `<tr>
    <td class="pair-code">${source.currency}</td><td class="mono">${plain(source.yield_2y, 3)}%</td><td>${brDate(source.first_observation)}</td><td>${brDate(source.last_observation)}</td>
    <td class="mono">${source.business_days_old} du</td><td><span class="tag ${qualityClass(source.status)}">${qualityLabels[source.status]}</span></td>
    <td><a href="${esc(source.source_url)}" target="_blank" rel="noreferrer">${esc(source.source)}</a></td><td class="muted">${esc(source.route)}</td>
  </tr>`).join("");
}

function populateControls() {
  $("#btPair").innerHTML = '<option value="ALL">All pairs</option>' + state.snapshot.pairs.map((pair) => `<option value="${pair.pair}">${pair.pair}</option>`).join("");
  $("#newsCurrency").innerHTML = '<option value="ALL">All currencies</option>' + currencyOrder.map((currency) => `<option value="${currency}">${currency}</option>`).join("");
  $("#btStart").value = state.defaultBacktest.meta.start;
  $("#btEnd").value = state.defaultBacktest.meta.end;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function renderBacktest(data, selected = "ALL") {
  state.currentBacktest = data;
  const results = data.results;
  if (selected === "ALL") renderBacktestUniverse(results);
  else renderBacktestPair(results.find((result) => result.summary.pair === selected) || results[0]);
}

function renderBacktestUniverse(results) {
  const causal = results.filter((result) => result.summary.validation === "PIT_CAUSAL");
  const profitable = causal.filter((result) => Number(result.summary.profit_factor || 0) > 1);
  const pfs = causal.map((result) => result.summary.profit_factor).filter((value) => value !== null);
  const best = causal.reduce((top, item) => !top || Number(item.summary.profit_factor || 0) > Number(top.summary.profit_factor || 0) ? item : top, null);
  const trades = causal.reduce((sum, item) => sum + item.summary.trades, 0);
  $("#btSummary").innerHTML = summaryCells([
    ["Pares causais", causal.length], ["PF mediano", plain(median(pfs), 2)], ["PF acima de 1", `${profitable.length}/${causal.length}`],
    ["Melhor par", best?.summary.pair || "—"], ["Melhor PF", pfText(best?.summary)], ["Operações", trades],
  ]);
  $("#btChartTitle").textContent = best ? `CURVA DE CAPITAL — ${best.summary.pair}` : "CURVA DE CAPITAL";
  drawEquityChart(best?.equity || []);
  $("#btResultHead").innerHTML = "<tr><th>Rank</th><th>Par</th><th>PF</th><th>N</th><th>WR</th><th>Retorno</th><th>DD</th><th>Avg hold</th><th>Validation</th></tr>";
  $("#btResultBody").innerHTML = results.map((result, index) => {
    const summary = result.summary;
    return `<tr data-bt-pair="${summary.pair}"><td class="mono">${index + 1}</td><td class="pair-code">${summary.pair}</td><td class="mono">${pfText(summary)}</td>
      <td class="mono">${summary.trades}</td><td class="mono">${plain(summary.win_rate, 1)}%</td><td class="mono ${signClass(summary.net_return_pct)}">${percent(summary.net_return_pct)}</td>
      <td class="mono negative">−${plain(summary.max_drawdown_pct, 1)}%</td><td class="mono">${plain(summary.avg_holding_days, 1)}d</td>
      <td class="${summary.validation === "PIT_CAUSAL" ? "positive" : "warning"}">${validationText(summary.validation)}</td></tr>`;
  }).join("");
  $("#btResultBody").querySelectorAll("[data-bt-pair]").forEach((row) => row.addEventListener("click", () => {
    $("#btPair").value = row.dataset.btPair;
    renderBacktest(data, row.dataset.btPair);
  }));
}

function renderBacktestPair(result) {
  if (!result) return;
  const summary = result.summary;
  $("#btSummary").innerHTML = summaryCells([
    ["PF", pfText(summary)], ["Operações", summary.trades], ["Win rate", `${plain(summary.win_rate, 1)}%`],
    ["Retorno", percent(summary.net_return_pct)], ["Drawdown", `−${plain(summary.max_drawdown_pct, 1)}%`], ["Avg hold", `${plain(summary.avg_holding_days, 1)}d`],
  ]);
  $("#btChartTitle").textContent = `CURVA DE CAPITAL — ${summary.pair}`;
  drawEquityChart(result.equity);
  $("#btResultHead").innerHTML = "<tr><th>Lado</th><th>Entrada</th><th>Saída</th><th>Preço entrada</th><th>Preço saída</th><th>FUND entrada</th><th>Retorno</th><th>Dias</th><th>Motivo</th></tr>";
  const trades = [...result.trades].reverse().slice(0, 80);
  $("#btResultBody").innerHTML = trades.length ? trades.map((trade) => `<tr>
    <td class="${trade.side === "LONG" ? "positive" : "negative"}">${trade.side}</td><td>${brDate(trade.entry_date)}</td><td>${brDate(trade.exit_date)}</td>
    <td class="mono">${plain(trade.entry_price, 5)}</td><td class="mono">${plain(trade.exit_price, 5)}</td><td class="mono">${signed(trade.fund_entry)}</td>
    <td class="mono ${signClass(trade.return_pct)}">${percent(trade.return_pct, 2)}</td><td class="mono">${trade.holding_days}</td><td>${trade.reason}</td>
  </tr>`).join("") : '<tr><td colspan="9" class="empty-state">Nenhuma operação no período.</td></tr>';
}

function summaryCells(items) {
  return items.map(([label, value]) => `<div><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("");
}

function drawEquityChart(curve) {
  const svg = $("#btEquityChart");
  if (!curve.length) { svg.innerHTML = ""; return; }
  const width = 960, height = 260, left = 52, right = 28, top = 17, bottom = 28;
  const values = curve.map((point) => Number(point.equity));
  let min = Math.min(...values), max = Math.max(...values);
  const padding = Math.max(2, (max - min) * 0.12);
  min -= padding; max += padding;
  const x = (index) => left + index / Math.max(1, curve.length - 1) * (width - left - right);
  const y = (value) => top + (max - value) / Math.max(0.0001, max - min) * (height - top - bottom);
  const path = curve.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(2)},${y(point.equity).toFixed(2)}`).join(" ");
  const levels = [min + padding, (min + max) / 2, max - padding];
  const guides = levels.map((value) => `<line class="chart-threshold" x1="${left}" y1="${y(value)}" x2="${width - right}" y2="${y(value)}"></line><text class="chart-label" x="5" y="${y(value) + 3}">${plain(value, 1)}</text>`).join("");
  const dates = [0, Math.floor((curve.length - 1) / 2), curve.length - 1].map((index) => `<text class="chart-label" x="${x(index)}" y="${height - 8}" text-anchor="${index === 0 ? "start" : index === curve.length - 1 ? "end" : "middle"}">${brDate(curve[index].date)}</text>`).join("");
  svg.innerHTML = `${guides}<path class="chart-line" d="${path}"></path>${dates}`;
}

const calendarCoverageLabels = {
  STRICT_FULL: "FULL 8/8", PARTIAL: "PARTIAL", NO_DATA: "NO DATA", CLOSED: "CLOSED",
};

function monthParts(value) {
  const [year, month] = value.split("-").map(Number);
  return { year, month };
}

function shiftMonth(value, delta) {
  const { year, month } = monthParts(value);
  const shifted = new Date(Date.UTC(year, month - 1 + delta, 1));
  return `${shifted.getUTCFullYear()}-${String(shifted.getUTCMonth() + 1).padStart(2, "0")}`;
}

function clampCalendarMonth(value) {
  const start = state.calendarIndex.meta.start.slice(0, 7);
  const end = state.calendarIndex.meta.end.slice(0, 7);
  return value < start ? start : value > end ? end : value;
}

async function loadCalendarYear(year) {
  if (state.calendarYears.has(year)) return state.calendarYears.get(year);
  const response = await fetch(`data/calendar/calendar_${year}.json?t=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`calendário ${year} indisponível`);
  const payload = await response.json();
  state.calendarYears.set(year, payload);
  return payload;
}

function calendarDayLabel(day) {
  if (day.coverage === "CLOSED") return '<span class="day-closed">MARKET CLOSED</span>';
  const top = day.recommendations[0];
  const extremes = day.strongest && day.weakest ? `${day.strongest.currency} / ${day.weakest.currency}` : "NO RANKING";
  return `<span class="day-extremes">${extremes}</span>${top
    ? `<strong>${top.pair}</strong><small class="${top.decision === "COMPRAR_BASE" ? "positive" : "negative"}">${decisionLabels[top.decision]} · ${signed(top.fund, 0)}</small>`
    : '<small class="muted">NO DIRECTIONAL PAIR</small>'}`;
}

async function renderCalendarMonth() {
  if (!state.calendarIndex || !state.calendarMonth) return;
  const { year, month } = monthParts(state.calendarMonth);
  const payload = await loadCalendarYear(year);
  const monthPrefix = `${year}-${String(month).padStart(2, "0")}`;
  state.calendarYearDays = payload.days;   // ano inteiro: usado para recuar
                                          // ate a projecao mais recente
  const days = payload.days.filter((day) => day.date.startsWith(monthPrefix));
  const firstWeekday = (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7;
  const blanks = Array.from({ length: firstWeekday }, () => '<div class="calendar-blank" aria-hidden="true"></div>');
  const cells = days.map((day) => `<button type="button" class="calendar-day coverage-${day.coverage.toLowerCase()} ${day.date === state.calendarSelectedDate ? "is-selected" : ""}" data-calendar-date="${day.date}">
    <span class="day-head"><time datetime="${day.date}">${Number(day.date.slice(8, 10))}</time><i>${calendarCoverageLabels[day.coverage]}</i></span>
    ${calendarDayLabel(day)}
  </button>`);
  $("#calendarGrid").innerHTML = [...blanks, ...cells].join("");
  $("#calendarMonth").value = state.calendarMonth;
  $("#calendarPrev").disabled = state.calendarMonth <= state.calendarIndex.meta.start.slice(0, 7);
  $("#calendarNext").disabled = state.calendarMonth >= state.calendarIndex.meta.end.slice(0, 7);

  const weekdays = days.filter((day) => day.market === "ABERTO");
  const complete = weekdays.filter((day) => day.coverage === "STRICT_FULL").length;
  const partial = weekdays.filter((day) => day.coverage === "PARTIAL").length;
  $("#calendarStatus").textContent = `${complete} full days · ${partial} partial · full coverage since ${brDate(state.calendarIndex.meta.first_strict_full)}.`;

  $("#calendarGrid").querySelectorAll("[data-calendar-date]").forEach((button) => button.addEventListener("click", () => {
    state.calendarSelectedDate = button.dataset.calendarDate;
    const selected = days.find((day) => day.date === state.calendarSelectedDate);
    renderCalendarDetail(selected);
    $("#calendarGrid").querySelectorAll(".calendar-day").forEach((node) => node.classList.toggle("is-selected", node.dataset.calendarDate === state.calendarSelectedDate));
  }));

  let selected = days.find((day) => day.date === state.calendarSelectedDate);
  if (!selected) {
    selected = [...days].reverse().find((day) => day.market === "ABERTO") || days[0];
    state.calendarSelectedDate = selected?.date || null;
    const selectedButton = selected ? $("#calendarGrid").querySelector(`[data-calendar-date="${selected.date}"]`) : null;
    selectedButton?.classList.add("is-selected");
  }
  renderCalendarDetail(selected);
}

function renderCalendarDetail(day) {
  if (!day) return;
  const coverage = $("#calendarCoverage");
  coverage.textContent = calendarCoverageLabels[day.coverage];
  coverage.className = `tag calendar-tag coverage-${day.coverage.toLowerCase()}`;
  $("#calendarDate").textContent = brDate(day.date);
  $("#calendarPairCount").textContent = day.market === "FECHADO" ? "NO SIGNAL" : `${day.valid_pairs}/28 pairs · ${day.available_currencies}/8 currencies`;
  $("#calendarStrongest").textContent = day.strongest ? `${day.strongest.currency} ${signed(day.strongest.score)}` : "—";
  $("#calendarWeakest").textContent = day.weakest ? `${day.weakest.currency} ${signed(day.weakest.score)}` : "—";

  $("#calendarCurrencies").innerHTML = day.currencies.length ? day.currencies.map((item, index) => `<div class="calendar-currency-row ${item.score === null ? "is-missing" : ""}">
    <span class="mono">${item.score === null ? "—" : index + 1}</span><strong>${item.currency}</strong>
    <span>${strengthLabels[item.strength]}</span><i class="mono ${signClass(item.score)}">${signed(item.score)}</i>
  </div>`).join("") : '<div class="calendar-empty">Market closed. No reading is carried over.</div>';

  const missing = day.missing_currencies?.length ? `<p class="calendar-warning">Missing on this day: ${day.missing_currencies.join(", ")}.</p>` : "";

  const watch = day.pre_fund_watch || [];
  // Projecao bidirecional em LINHAS que abrem, agrupadas por direcao:
  // COMPRA primeiro, VENDA depois. Cruzar uma borda para cima e a base
  // fortalecendo (compra da base); para baixo e o contrario.
  let proj = day.projection;
  let projDia = null;
  if (!proj) {
    // hoje nunca tem projecao: os yields de 2 anos saem em D+1
    const anteriores = (state.calendarYearDays || []).filter((d) => d.date <= day.date && d.projection);
    const ultimo = anteriores[anteriores.length - 1];
    if (ultimo) { proj = ultimo.projection; projDia = ultimo.date; }
  }
  const faixaDe = (v) => v >= 60 ? "STRONG_BULL" : v >= 25 ? "BULL"
    : v > -25 ? "NEUTRAL" : v > -60 ? "BEAR" : "STRONG_BEAR";
  const fonteDe = (moeda) => {
    const f = (state.snapshot.sources || []).find((x) => x.currency === moeda);
    return f ? `<a href="${esc(f.source_url)}" target="_blank" rel="noreferrer">${esc(moeda)} 2Y — ${esc(f.source)}</a>`
             : `<span>${esc(moeda)} 2Y</span>`;
  };
  const linhaProj = (x, sentido, i) => {
    const base = x.pair.slice(0, 3), quote = x.pair.slice(3);
    const compra = sentido === "up";
    const real = proj.outcome ? proj.outcome[x.pair] : undefined;
    const cruzou = real === undefined ? null : (compra ? real >= x.boundary : real <= x.boundary);
    const selo = cruzou === null
      ? '<em class="proj-outcome pend">outcome not known yet</em>'
      : `<em class="proj-outcome ${cruzou ? "hit" : "miss"}">${cruzou ? "crossed" : "did not cross"} · FUND ${signed(real)}</em>`;
    const como = x.bp > 0
      ? `the <b>${base}</b> 2-year yield has to rise, or the <b>${quote}</b> one has to fall`
      : `the <b>${base}</b> 2-year yield has to fall, or the <b>${quote}</b> one has to rise`;
    return `<details class="observation-item nextmove">
      <summary>
        <span class="observation-rank">${i + 1}</span><strong>${x.pair}</strong>
        <span class="side-tag ${compra ? "is-buy" : "is-sell"}">${compra ? "BUY" : "SELL"} ${base}</span>
        <span class="observation-chance">${plain(x.p, 1)}%<i>${faixaDe(x.fund_roll)} → ${x.band}</i></span>
      </summary>
      <div class="observation-detail">
        <p class="observation-band"><strong class="${x.fund >= 0 ? "positive" : "negative"}">FUND ${signed(x.fund)}</strong>
        <span>→ <b>${signed(x.fund_roll)}</b> if the yield spread does not move, from the 20-day window rolling alone</span></p>
        <div class="observation-reasons">
          <p><strong>What has to move</strong>${como} — <b>${plain(Math.abs(x.bp), 1)} bp</b> between them,
          to cross ${signed(x.boundary, 0)}.</p>
          <p><strong>Check it yourself</strong>${fonteDe(base)} · ${fonteDe(quote)}</p>
        </div>
        ${selo}
      </div>
    </details>`;
  };
  const grupo = (itens, sentido, titulo) => {
    const corpo = !itens || !itens.length
      ? '<p class="proj-empty">No pair is near a band edge on that side.</p>'
      : itens.map((x, i) => linhaProj(x, sentido, i)).join("");
    return `<div class="proj-side is-${sentido}"><span class="proj-head">${titulo}</span>${corpo}</div>`;
  };
  $("#calendarProjection").innerHTML = !proj
    ? `<div class="calendar-empty">No projection available for this day or any earlier one in this year.</div>`
    : `${projDia ? `<p class="proj-stale">The 2-year yields for ${brDate(day.date)} are not published yet —
         sovereign yields arrive at D+1. Showing the most recent projection available, from
         <b>${brDate(projDia)}</b>.</p>` : ""}
       ${grupo(proj.up, "up", "Buy side — could cross a band edge upward")}
       ${grupo(proj.down, "down", "Sell side — could cross a band edge downward")}
       <p class="prefund-note">Exact inversion of the FUND formula: the mean and deviation that normalise tomorrow are
       already fixed today, so the only unknown is tomorrow's move in the 2-year yield spread. This projects the
       <b>indicator</b>, not the price. The outcome on each row is a later check and took no part in the calculation.</p>`;

  $("#calendarPreFund").innerHTML = watch.length ? `${watch.map((item) => {
    const out = item.outcome || {};
    const acertou = out.entered_bear === true;
    const selo = out.entered_bear === undefined ? "" : `<em class="prefund-outcome ${acertou ? "hit" : "miss"}">${acertou ? "ENTERED BEAR" : "did not enter"}${out.next_fund === undefined ? "" : ` · FUND ${signed(out.next_fund)}`}</em>`;
    return `<article class="prefund-row">
      <span class="mono">${item.rank}</span>
      <div><strong>${item.pair}</strong><small>FUND ${signed(item.fund)} · chance of turning BEAR ${item.empirical_probability}% (n ${item.empirical_samples})</small></div>
      ${selo}
    </article>`;
  }).join("")}<p class="prefund-note">Causal selection from that day only (annual walk-forward). The outcome on the right is a later check and never took part in the choice.</p>` : '<div class="calendar-empty">No pair passed the observation floor on this day.</div>';
  $("#calendarRecommendations").innerHTML = day.recommendations.length ? `${missing}${day.recommendations.map((item) => `<article>
    <span class="mono">${item.rank}</span><div><strong>${item.pair}</strong><small>${esc(item.reason)}</small></div>
    <div class="calendar-side ${item.decision === "COMPRAR_BASE" ? "positive" : "negative"}">${decisionLabels[item.decision]}<small>${signed(item.fund)}</small></div>
  </article>`).join("")}` : `${missing}<div class="calendar-empty">No pair reached |FUND| ≥ 25 on this day.</div>`;
}

async function setCalendarMonth(value) {
  state.calendarMonth = clampCalendarMonth(value);
  state.calendarSelectedDate = null;
  try { await renderCalendarMonth(); }
  catch (error) { $("#calendarStatus").textContent = `Could not open the month: ${error.message}`; }
}

async function runBacktest(event) {
  event.preventDefault();
  const button = $("#btRun");
  button.disabled = true; button.textContent = "Running";
  $("#btStatus").textContent = "Computing causal signals and D+1 executions.";
  const payload = { pair: $("#btPair").value, start: $("#btStart").value, end: $("#btEnd").value, cost_pips: Number($("#btCost").value) };
  try {
    const response = await fetch("api/backtest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || `HTTP ${response.status}`);
    const data = { meta: result.meta, results: result.results };
    renderBacktest(data, payload.pair);
    $("#btStatus").textContent = `${result.meta.entry}. ${result.meta.exit}.`;
  } catch (error) {
    $("#btStatus").textContent = `Falha no backtest: ${error.message}`;
  } finally { button.disabled = false; button.textContent = "Rodar backtest"; }
}

function renderNews() {
  const impacts = { High: "HIGH", Medium: "MEDIUM", Low: "LOW", Holiday: "FERIADO" };
  const events = state.snapshot.news.filter((item) => {
    if (state.newsCurrency !== "ALL" && item.currency !== state.newsCurrency) return false;
    if (state.newsImpact === "High" && item.impact !== "High") return false;
    if (state.newsImpact === "Medium" && !["High", "Medium"].includes(item.impact)) return false;
    return true;
  });
  const list = $("#newsList");
  $("#newsSource").innerHTML = `Fonte de agenda: <a href="${esc(state.snapshot.news_source.url)}" target="_blank" rel="noreferrer">${esc(state.snapshot.news_source.name)}</a>. ${esc(state.snapshot.news_source.scope)}.`;
  if (!events.length) { list.innerHTML = '<div class="empty-state">No upcoming event matches this filter for the current week.</div>'; return; }
  list.innerHTML = events.map((item) => `<details class="news-item">
    <summary><span class="news-time">${brDateTime(item.date)}</span><span class="news-currency">${item.currency}</span>
      <span class="news-impact impact-${item.impact}">${impacts[item.impact] || item.impact}</span><span class="news-title">${esc(item.title)}</span>
      <span class="news-number">Prev. ${esc(item.previous || "—")}</span><span class="news-number">Cons. ${esc(item.forecast || "—")}</span></summary>
    <div class="news-detail"><div><span>Se sair acima / mais hawkish</span><p>${esc(item.above_scenario)}</p></div>
      <div><span>Se sair abaixo / mais dovish</span><p>${esc(item.below_scenario)}</p><p class="news-pairs">Pares relacionados: ${esc(item.related_pairs.join(", "))}</p></div></div>
  </details>`).join("");
}

function renderMethodology() {
  const method = state.snapshot.methodology;
  $("#formulaText").textContent = `Momento ${method.lookback}d · normalização ${method.normalization_window}d ex ante · lag ${method.pit_lag}`;
}

function renderAll() {
  renderOverview(); renderPriorities(); renderNextDay(); renderCurrencies(); renderMatrix(); renderPairTable(); renderSources(); renderNews(); renderMethodology();
  const first = state.snapshot.priorities[0]?.pair || state.snapshot.pairs.find((pair) => pair.operational)?.pair;
  selectPair(state.selectedPair || first, false);
  populateControls();
  renderBacktest(state.defaultBacktest, "ALL");
}

async function loadData() {
  const stamp = Date.now();
  const [snapshotResponse, backtestResponse, calendarResponse] = await Promise.all([
    fetch(`data/fund_snapshot.json?t=${stamp}`, { cache: "no-store" }),
    fetch(`data/backtest_default.json?t=${stamp}`, { cache: "no-store" }),
    fetch(`data/calendar/index.json?t=${stamp}`, { cache: "no-store" }),
  ]);
  if (!snapshotResponse.ok || !backtestResponse.ok || !calendarResponse.ok) throw new Error("radar files unavailable");
  state.snapshot = await snapshotResponse.json();
  state.defaultBacktest = await backtestResponse.json();
  state.calendarIndex = await calendarResponse.json();
  state.calendarYears = new Map();
  state.calendarMonth = state.calendarIndex.meta.end.slice(0, 7);
  state.calendarSelectedDate = state.calendarIndex.meta.end;
  state.currentBacktest = state.defaultBacktest;
  renderAll();
  await renderCalendarMonth();
}

async function updateData() {
  const button = $("#updateButton");
  button.disabled = true; button.textContent = "Atualizando";
  showMessage("Atualizando yields, preços do ECB, ranking, backtests, observações D+1 e calendário diário desde 2002.");
  try {
    const capability = await fetch("api/pre-fund-health", { cache: "no-store" });
    if (!capability.ok) throw new Error("a previous server is still running; close it and reopen from the shortcut to refresh without wiping the pre-FUND");
    const response = await fetch("api/update", { method: "POST" });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || `HTTP ${response.status}`);
    await loadData();
    showMessage("Data refreshed. FUND sets direction; execution stays manual.");
  } catch (error) { showMessage(`Refresh failed: ${error.message}. Previous snapshot kept.`, true); }
  finally { button.disabled = false; button.textContent = "Refresh"; }
}

$("#pairSearch").addEventListener("input", (event) => { state.pairSearch = event.target.value; renderPairTable(); });
$("#pairFilter").addEventListener("change", (event) => { state.pairFilter = event.target.value; renderPairTable(); });
$("#newsCurrency").addEventListener("change", (event) => { state.newsCurrency = event.target.value; renderNews(); });
$("#newsImpact").addEventListener("change", (event) => { state.newsImpact = event.target.value; renderNews(); });
$("#btPair").addEventListener("change", (event) => {
  const pair = event.target.value;
  const currentHasPair = state.currentBacktest?.results?.some((result) => result.summary.pair === pair);
  const source = pair === "ALL" || !currentHasPair ? state.defaultBacktest : state.currentBacktest;
  renderBacktest(source, pair);
});
$("#backtestForm").addEventListener("submit", runBacktest);
$("#updateButton").addEventListener("click", updateData);
$("#calendarPrev").addEventListener("click", () => setCalendarMonth(shiftMonth(state.calendarMonth, -1)));
$("#calendarNext").addEventListener("click", () => setCalendarMonth(shiftMonth(state.calendarMonth, 1)));
$("#calendarMonth").addEventListener("change", (event) => setCalendarMonth(event.target.value));

loadData().catch((error) => {
  const hint = location.protocol === "file:" ? " Open it through ABRIR_RADAR.bat." : "";
  showMessage(`Could not load the radar: ${error.message}.${hint}`, true);
});

