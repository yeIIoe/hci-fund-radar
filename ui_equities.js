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
    renderCards();
    alvo.innerHTML = html ? `<div class="section-title" style="margin-top:26px">
        <div><h2>Varredura diaria</h2></div>
        <p>Dips em fornecedores, deep value e gatilhos BTD. Era o que ia para o Discord.</p>
      </div>${html}` : "";
  }


  /* ---- CARDS POR ACAO ----
     Antes o site mostrava o texto cru do scan dentro de um <pre>. Agora cada nome
     vira um card com o MOTIVO ao lado, separado entre comprar e evitar. Os scans
     passaram a emitir JSON na origem, entao nada aqui e reconstruido por regex. */
  const esc = (t) => String(t == null ? "" : t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function card(n, bom) {
    const met = n.metricas ? Object.entries(n.metricas)
      .filter(([, v]) => v !== null && v !== undefined && v !== false)
      .map(([k, v]) => `<span class="eq-met"><b>${esc(k)}</b> ${esc(v === true ? "sim" : v)}</span>`).join("") : "";
    const mov = n.retorno_hoje !== undefined
      ? `<span class="eq-met"><b>hoje</b> ${n.retorno_hoje > 0 ? "+" : ""}${n.retorno_hoje}%</span>
         <span class="eq-met"><b>vs maxima 12m</b> ${n.vs_maxima_12m}%</span>` : "";
    const motivo = bom ? n.porque : (n.porque_nao || n.porque);
    return `<article class="eq-card ${bom ? "eq-ok" : "eq-no"}">
      <header><strong>${esc(n.ticker)}</strong>
        <span class="eq-nota">${esc(n.nota)}</span>
        ${n.preco ? `<span class="eq-px">${esc(n.preco)}</span>` : ""}</header>
      <div class="eq-mets">${met}${mov}</div>
      ${motivo ? `<p class="eq-porque"><b>${bom ? "Por que" : "Por que nao"}:</b> ${esc(motivo)}</p>` : ""}
      ${n.tipo_queda ? `<p class="eq-linha"><b>Queda:</b> ${esc(n.tipo_queda)}${n.profundidade ? " · " + esc(n.profundidade) : ""}</p>` : ""}
      ${n.risco ? `<p class="eq-linha eq-risco"><b>Risco:</b> ${esc(n.risco)}</p>` : ""}
      ${n.confianca ? `<p class="eq-linha"><b>Confianca:</b> ${esc(n.confianca)}</p>` : ""}
      ${n.plano ? `<p class="eq-linha"><b>Plano:</b> ${esc(n.plano)}</p>` : ""}
      ${n.voce_assina ? `<p class="eq-assina">Voce assina: ${esc(n.voce_assina)}</p>` : ""}
    </article>`;
  }

  async function bloco(arq, titulo, subtitulo) {
    let doc;
    try {
      const r = await fetch(`data/${arq}?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) return "";
      doc = await r.json();
    } catch (e) { return ""; }
    const ns = doc.nomes || [];
    if (!ns.length) return "";
    const bons = ns.filter((n) => n.aprovado), maus = ns.filter((n) => !n.aprovado);
    const grade = (lista, bom, rot) => lista.length
      ? `<h4 class="eq-sub ${bom ? "eq-sub-ok" : "eq-sub-no"}">${rot} <span>${lista.length}</span></h4>
         <div class="eq-grade">${lista.map((n) => card(n, bom)).join("")}</div>` : "";
    return `<div class="section-title" style="margin-top:30px">
        <div><h2>${titulo}</h2></div><p>${subtitulo}</p>
      </div>
      <p class="method-note">${esc(doc.metodo || "")}<br><em>${esc(doc.limite || "")}</em></p>
      ${grade(bons, true, "Candidatos a comprar")}
      ${grade(maus, false, "Evitar")}`;
  }

  async function renderCards() {
    const alvo = document.getElementById("sentinelaBody");
    if (!alvo) return;
    const dv = await bloco("deep_value_scan.json", "Deep Value",
      "Barato de verdade, filtrado contra armadilha de valor.");
    const btd = await bloco("btd_scan.json", "BTD + HOLD",
      "Queda do dia em nome de qualidade — separando medo de mercado de problema da empresa.");
    if (dv || btd) alvo.insertAdjacentHTML("beforeend", dv + btd);
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "equities") render();
  });
})();
