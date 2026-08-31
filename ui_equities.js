/* Aba EQUITIES — saida do Research Agent (data/equities_research.json).
   Separado do FUND de proposito: a unidade aqui e a EMPRESA, nao a moeda. */
(function () {
  "use strict";
  const F = (v, d) => (v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(d === undefined ? 2 : d));

  function leitura(pos) {
    if (!pos) return '<span class="spr-pill spr-dim">sem leitura</span>';
    if (/COMPRA/i.test(pos)) return '<span class="spr-pill spr-buy">compra / manter</span>';
    if (/MANTER/i.test(pos)) return '<span class="spr-pill spr-dim">manter</span>';
    if (/REDUZ|VENDE|SAIR/i.test(pos)) return '<span class="spr-pill spr-red">reduzir</span>';
    return '<span class="spr-pill spr-dim">' + pos.slice(0, 24) + "</span>";
  }

  function linha(n) {
    const up = n.upside;
    const cor = up === null || up === undefined ? "" : (up >= 0.10 ? ' class="spr-good"' : (up <= -0.10 ? ' class="spr-bad"' : ""));
    const alertas = [];
    if (n.regime_ok === false) alertas.push('<span class="spr-pill spr-amber">regime contra</span>');
    if (n.earnings) alertas.push(`<span class="spr-pill spr-dim">resultado ${String(n.earnings).slice(0, 10)}</span>`);
    if (n.hi52 && n.preco && n.preco / n.hi52 - 1 > -0.03) alertas.push('<span class="spr-pill spr-amber">colado na maxima</span>');
    return `<tr>
      <td><strong>${n.ticker}</strong></td>
      <td class="mono">${F(n.preco)}</td>
      <td class="mono">${n.tp ? F(n.tp, 0) : "—"}</td>
      <td class="mono"${cor}>${up === null || up === undefined ? "—" : (up >= 0 ? "+" : "") + (100 * up).toFixed(0) + "%"}</td>
      <td>${leitura(n.posicao)}</td>
      <td>${alertas.join(" ")}</td>
      <td class="spr-tese">${n.tese ? n.tese : ""}</td>
    </tr>`;
  }

  async function render() {
    const alvo = document.getElementById("equitiesBody");
    if (!alvo) return;
    let doc;
    try {
      const r = await fetch(`data/equities_research.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      doc = await r.json();
    } catch (e) {
      alvo.innerHTML = `<p class="method-note">Nao consegui ler data/equities_research.json (${e.message}).
        Ele e gerado por <code>equities_research.py</code> na cadeia do GitHub.</p>`;
      return;
    }
    const ns = (doc.nomes || []).slice().sort((a, b) => (b.upside ?? -9) - (a.upside ?? -9));
    alvo.innerHTML = `
      <div class="spr-alert spr-alert-dim"><strong>${doc.escopo || "Equities"}</strong><br>
        ${doc.limite || ""}</div>
      <div class="table-wrap"><table class="data-table">
        <thead><tr>
          <th>Nome</th><th>Preco</th><th>Alvo</th><th>Upside</th>
          <th>Leitura</th><th>Alertas</th><th>Tese</th>
        </tr></thead>
        <tbody>${ns.map(linha).join("")}</tbody>
      </table></div>
      <p class="method-note">
        ${doc.metodo || ""}<br>
        O relatorio so e refeito quando o dado que o sustenta muda de verdade:
        ${doc.regenera_quando || ""}.<br>
        O alvo e multiplo pre-registrado vezes lucro projetado — nao e previsao de preco,
        e o que o multiplo declarado implica se o lucro projetado se realizar.
        Gerado em ${doc.gerado_em || "—"}.
      </p>
      <div id="sentinelaBody"></div>`;
    renderSentinela();
  }

  /* Varredura diaria (era a sentinela que postava no Discord) */
  async function renderSentinela() {
    const alvo = document.getElementById("sentinelaBody");
    if (!alvo) return;
    let doc;
    try {
      const r = await fetch(`data/sentinela.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) return;
      doc = await r.json();
    } catch (e) { return; }
    const turno = (nome, rotulo) => {
      const t = doc[nome];
      if (!t || !t.blocos || !t.blocos.length) return "";
      return `<div class="sent-turno">
        <h3>${rotulo} <span class="sent-quando">${t.quando || ""}</span></h3>
        ${t.blocos.map((b) => `<details class="sent-bloco"><summary>${b.titulo}</summary>
          <pre>${(b.texto || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]))}</pre>
        </details>`).join("")}
      </div>`;
    };
    const html = turno("manha", "Abertura") + turno("fechamento", "Fechamento");
    alvo.innerHTML = html ? `<div class="section-title" style="margin-top:26px">
        <div><h2>Varredura diaria</h2></div>
        <p>Dips em fornecedores, deep value e gatilhos BTD. Era o que ia para o Discord.</p>
      </div>${html}` : "";
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "equities") render();
  });
})();
