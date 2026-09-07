/* Diário local para calibrar a convicção histórica do HCI.
   Nenhum dado sai do navegador; exportação CSV serve como cópia e para análise externa. */
(function () {
  "use strict";

  const CHAVE = "hci.manualBacktest.v1";
  const PARES = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCAD", "USDCHF",
    "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCAD", "EURCHF", "GBPJPY",
    "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF", "AUDJPY", "AUDNZD", "AUDCAD",
    "AUDCHF", "NZDJPY", "NZDCAD", "NZDCHF", "CADJPY", "CADCHF", "CHFJPY"
  ];
  const esc = (v) => String(v == null ? "" : v).replace(/[&<>\"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const num = (v) => v === "" || v == null ? null : (Number.isFinite(Number(v)) ? Number(v) : null);
  const fmtR = (v) => v == null ? "—" : `${v > 0 ? "+" : ""}${Number(v).toFixed(2).replace(".", ",")}R`;

  function ler() {
    try {
      const v = JSON.parse(localStorage.getItem(CHAVE) || "[]");
      return Array.isArray(v) ? v : [];
    } catch (_) { return []; }
  }
  function gravar(itens) { localStorage.setItem(CHAVE, JSON.stringify(itens)); }

  function faixa(v) {
    if (v >= 60) return "60–100";
    if (v >= 40) return "40–59";
    if (v >= 25) return "25–39";
    if (v >= 15) return "15–24";
    return "0–14";
  }

  function wilson(vitorias, n) {
    if (!n) return null;
    const z = 1.96, p = vitorias / n, den = 1 + z * z / n;
    const centro = (p + z * z / (2 * n)) / den;
    const margem = z * Math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den;
    return [Math.max(0, centro - margem), Math.min(1, centro + margem)];
  }

  function taxa(itens, campo) {
    const validos = itens.filter((x) => num(x[campo]) != null);
    if (!validos.length) return "—";
    const wins = validos.filter((x) => num(x[campo]) > 0).length;
    return `${Math.round(wins / validos.length * 100)}% <small>(${wins}/${validos.length})</small>`;
  }

  function resumo(itens) {
    const finais = itens.filter((x) => num(x.r_final) != null);
    const wins = finais.filter((x) => num(x.r_final) > 0).length;
    const media = finais.length ? finais.reduce((s, x) => s + num(x.r_final), 0) / finais.length : null;
    const ic = wilson(wins, finais.length);
    const conv = finais.length >= 30
      ? `${Math.round(wins / finais.length * 100)}% <small>IC 95% ${Math.round(ic[0] * 100)}–${Math.round(ic[1] * 100)}%</small>`
      : `amostra insuficiente <small>${finais.length}/30 operações fechadas</small>`;
    return `<div class="bt-resumo">
      <div><span>Registros</span><strong>${itens.length}</strong></div>
      <div><span>T-7 positivo</span><strong>${taxa(itens, "r_t7")}</strong></div>
      <div><span>T-1 positivo</span><strong>${taxa(itens, "r_t1")}</strong></div>
      <div><span>R médio final</span><strong>${fmtR(media)}</strong></div>
      <div><span>Convicção histórica</span><strong>${conv}</strong></div>
    </div>`;
  }

  function tabelaFaixas(itens) {
    const ordem = ["0–14", "15–24", "25–39", "40–59", "60–100"];
    const linhas = ordem.map((f) => {
      const xs = itens.filter((x) => faixa(num(x.divergencia) || 0) === f);
      const fin = xs.filter((x) => num(x.r_final) != null);
      const media = fin.length ? fin.reduce((s, x) => s + num(x.r_final), 0) / fin.length : null;
      return `<tr><td>${f}</td><td>${xs.length}</td><td>${taxa(xs, "r_t7")}</td>
        <td>${taxa(xs, "r_t1")}</td><td>${fmtR(media)}</td>
        <td>${fin.length >= 30 ? "amostra utilizável" : `faltam ${Math.max(0, 30 - fin.length)}`}</td></tr>`;
    }).join("");
    return `<details class="bt-faixas"><summary>Resultado por faixa de divergência</summary>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Divergência</th><th>N</th>
      <th>T-7 positivo</th><th>T-1 positivo</th><th>R médio final</th><th>Calibração</th></tr></thead>
      <tbody>${linhas}</tbody></table></div></details>`;
  }

  function linha(x) {
    return `<tr><td>${esc(x.sinal_data)}</td><td><strong>${esc(x.par)}</strong></td>
      <td>${esc(x.direcao)}</td><td>${esc(x.divergencia)}</td><td>${x.bo ? "sim" : "não"}</td>
      <td>${esc(x.zoi_baixa || "—")}–${esc(x.zoi_alta || "—")}</td><td>${fmtR(num(x.r_t7))}</td>
      <td>${fmtR(num(x.r_t1))}</td><td>${fmtR(num(x.r_final))}</td>
      <td class="bt-acoes"><button type="button" data-bt-editar="${esc(x.id)}">Editar</button>
      <button type="button" data-bt-excluir="${esc(x.id)}">Excluir</button></td></tr>`;
  }

  function lista(itens) {
    if (!itens.length) return `<div class="mac-vazio bt-vazio"><strong>A amostra começa no primeiro registro.</strong>
      <p>Não preencha olhando o futuro: congele catalisador, direção, divergência e ZOI no instante do sinal.</p></div>`;
    const ordem = itens.slice().sort((a, b) => String(b.sinal_data).localeCompare(String(a.sinal_data)));
    return `<div class="bt-lista-topo"><h3>Operações registradas</h3><button type="button" data-bt-csv>Exportar CSV</button></div>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Sinal</th><th>Par</th><th>Direção</th>
      <th>Div.</th><th>BO</th><th>ZOI</th><th>T-7</th><th>T-1</th><th>Final</th><th></th></tr></thead>
      <tbody>${ordem.map(linha).join("")}</tbody></table></div>`;
  }

  function formulario() {
    return `<details class="bt-form-box" open><summary>Novo registro</summary>
      <form id="manualBacktestForm" class="bt-form">
        <input type="hidden" name="id">
        <label>Data do sinal<input name="sinal_data" type="date" required></label>
        <label>Par<input name="par" list="btPares" maxlength="10" required placeholder="AUDCAD"></label>
        <datalist id="btPares">${PARES.map((p) => `<option value="${p}">`).join("")}</datalist>
        <label>Catalisador<input name="catalisador" required placeholder="Emprego canadense acima do esperado"></label>
        <label>Direção fundamental<select name="direcao" required><option value="">Escolha</option>
          <option>Alta do par</option><option>Queda do par</option></select></label>
        <label>Divergência (0–100)<input name="divergencia" type="number" min="0" max="100" required></label>
        <label>Evidência (0–100)<input name="evidencia" type="number" min="0" max="100"></label>
        <label class="bt-check"><input name="bo" type="checkbox"> BO estrutural confirmado</label>
        <label>ZOI mínima<input name="zoi_baixa" inputmode="decimal" placeholder="0,91336"></label>
        <label>ZOI máxima<input name="zoi_alta" inputmode="decimal" placeholder="0,91348"></label>
        <label>Entrada<input name="entrada" type="datetime-local"></label>
        <label>Próximo evento / expiração<input name="expiracao" type="datetime-local"></label>
        <label>Resultado T-7 (R)<input name="r_t7" type="number" step="0.01"></label>
        <label>Resultado T-1 (R)<input name="r_t1" type="number" step="0.01"></label>
        <label>Resultado final (R)<input name="r_final" type="number" step="0.01"></label>
        <label class="bt-notas">Notas<textarea name="notas" rows="3" placeholder="Tese, invalidação e o que aconteceu até o próximo evento"></textarea></label>
        <div class="bt-botoes"><button type="submit">Salvar registro</button><button type="reset" class="bt-sec">Limpar</button></div>
      </form></details>`;
  }

  function render() {
    const alvo = document.getElementById("manualBacktestBody");
    if (!alvo) return;
    const itens = ler();
    alvo.innerHTML = resumo(itens) + formulario() + tabelaFaixas(itens) + lista(itens) +
      `<p class="method-note">Convicção histórica permanece “não calibrada” até haver ao menos 30 operações
      fechadas numa regra comparável. Acerto é retorno positivo; o R médio impede que taxa de acerto esconda perdas maiores.</p>`;
  }

  function valorForm(form, nome) { return form.elements[nome] ? form.elements[nome].value.trim() : ""; }
  function salvar(form) {
    const itens = ler();
    const id = valorForm(form, "id") || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const reg = { id, sinal_data: valorForm(form, "sinal_data"), par: valorForm(form, "par").toUpperCase(),
      catalisador: valorForm(form, "catalisador"), direcao: valorForm(form, "direcao"),
      divergencia: valorForm(form, "divergencia"), evidencia: valorForm(form, "evidencia"),
      bo: form.elements.bo.checked, zoi_baixa: valorForm(form, "zoi_baixa"), zoi_alta: valorForm(form, "zoi_alta"),
      entrada: valorForm(form, "entrada"), expiracao: valorForm(form, "expiracao"),
      r_t7: valorForm(form, "r_t7"), r_t1: valorForm(form, "r_t1"), r_final: valorForm(form, "r_final"),
      notas: valorForm(form, "notas"), atualizado_em: new Date().toISOString() };
    const pos = itens.findIndex((x) => x.id === id);
    if (pos >= 0) itens[pos] = reg; else itens.push(reg);
    gravar(itens); render();
  }

  function editar(id) {
    const x = ler().find((i) => i.id === id), form = document.getElementById("manualBacktestForm");
    if (!x || !form) return;
    Object.keys(x).forEach((k) => {
      if (!form.elements[k]) return;
      if (form.elements[k].type === "checkbox") form.elements[k].checked = !!x[k];
      else form.elements[k].value = x[k] == null ? "" : x[k];
    });
    form.closest("details").open = true;
    form.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function exportar() {
    const itens = ler();
    if (!itens.length) return;
    const campos = ["sinal_data", "par", "catalisador", "direcao", "divergencia", "evidencia", "bo",
      "zoi_baixa", "zoi_alta", "entrada", "expiracao", "r_t7", "r_t1", "r_final", "notas"];
    const q = (v) => `"${String(v == null ? "" : v).replace(/"/g, '""')}"`;
    const csv = [campos.join(","), ...itens.map((x) => campos.map((k) => q(x[k])).join(","))].join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
    a.download = `hci-backtest-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  document.addEventListener("submit", (e) => {
    if (e.target.id !== "manualBacktestForm") return;
    e.preventDefault(); salvar(e.target);
  });
  document.addEventListener("click", (e) => {
    const ed = e.target.closest && e.target.closest("[data-bt-editar]");
    const del = e.target.closest && e.target.closest("[data-bt-excluir]");
    const csv = e.target.closest && e.target.closest("[data-bt-csv]");
    if (ed) editar(ed.dataset.btEditar);
    if (del && confirm("Excluir este registro do diário local?")) {
      gravar(ler().filter((x) => x.id !== del.dataset.btExcluir)); render();
    }
    if (csv) exportar();
  });
  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab"); if (b && b.dataset.tab === "journal") render();
  });
})();
