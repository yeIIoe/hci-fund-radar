/* Ficha do par — o upgrade do FUND conforme o Volume I do AEGH.
   Injeta, em cada linha da tabela de candidatos, uma ficha expansivel com as QUATRO
   saidas que a secao 05 mantem separadas, cada uma com fonte e data.
   Nao emite direcao: o FUND V0.1 esta congelado como reprovado nos testes direcionais. */
(function () {
  "use strict";
  let F = null;
  const esc = (t) => String(t == null ? "" : t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  const PILL = {
    coherent: "ff-ok", strengthening: "ff-ok", high: "ff-ok",
    contradictory: "ff-warn", weakening: "ff-warn", low: "ff-warn",
    partial: "ff-dim", flat: "ff-dim", medium: "ff-dim",
  };
  const pill = (e) => `<span class="ff-pill ${PILL[e] || "ff-dim"}">${esc(e)}</span>`;

  function bloco(rot, obj, extra) {
    if (!obj) return "";
    return `<div class="ff-bloco"><h5>${rot} ${pill(obj.estado)}</h5>
      ${obj.porque ? `<p>${esc(obj.porque)}</p>` : ""}${extra || ""}</div>`;
  }

  function ficha(p) {
    const d = F && F.fichas ? F.fichas[p] : null;
    if (!d) return "";
    const c = d.causa_dominante;
    const causa = c ? `<div class="ff-bloco"><h5>Dominant component of the movement</h5>
        <p>${esc(c.frase)}</p>
        <p class="ff-src">2y at ${c.yield}% · 1d ${c.bp_1d} bp · 20d ${c.bp_20d} bp ·
        read ${esc(c.lido_em || "")}<br>
        ${c.fonte_url ? `<a href="${esc(c.fonte_url)}" target="_blank" rel="noopener">${esc(c.fonte || "source")}</a>` : esc(c.fonte || "")}
        ${c.bc_url ? ` · <a href="${esc(c.bc_url)}" target="_blank" rel="noopener">${esc(c.banco_central || "central bank")}</a>` : ""}</p>
        <div class="ff-invest">
          <p><b>Event identified:</b> ${c.evento_identificado ? esc(c.evento_identificado) : "<i>none — not yet investigated</i>"}</p>
          <p><b>Proposed mechanism:</b> ${c.interpretacao ? esc(c.interpretacao) : "<i>none</i>"}</p>
          <p><b>Contrary evidence:</b> ${c.evidencia_contraria ? esc(c.evidencia_contraria) : "<i>none</i>"}</p>
          <p class="ff-src"><b>Conclusion:</b> ${esc(c.conclusao || "")}</p>
        </div>
      </div>` : "";
    const ev = (d.evidencia || []).map((e) =>
      `<li><span class="ff-quando">${esc(e.quando)}</span>
        <span class="ff-moeda">${esc(e.moeda)}</span>
        ${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.titulo)}</a>` : esc(e.titulo)}
        ${e.impacto ? `<em>${esc(e.impacto)}</em>` : ""}</li>`).join("");
    const contra = (d.contradiz || []).map((x) => `<li>${esc(x)}</li>`).join("");
    return `<details class="ff"><summary>Pair file &amp; evidence</summary><div class="ff-body">
      ${causa}
      ${bloco("Fundamental conviction", d.conviccao_fundamental,
        `<p class="ff-src">Coherence of the thesis with its fundamentals — <b>not a probability of profit</b>.</p>`)}
      ${bloco("Thesis health", d.saude_da_tese,
        d.saude_da_tese && d.saude_da_tese.invalidaria
          ? `<p class="ff-src"><b>What would invalidate it:</b> ${esc(d.saude_da_tese.invalidaria)}</p>` : "")}
      ${bloco("Market confirmation", d.confirmacao_de_mercado)}
      ${bloco("Data quality", d.confianca_analitica,
        d.confianca_analitica ? `<p class="ff-src"><b>Analysis support:</b> ${esc(d.confianca_analitica.sustentacao_da_analise || "")}</p>
        <p class="ff-src"><b>Operational validity:</b> ${esc(d.confianca_analitica.validade_operacional || "")}</p>` : "")}
      ${contra ? `<div class="ff-bloco ff-contra"><h5>What contradicts it</h5><ul>${contra}</ul></div>` : ""}
      ${ev ? `<div class="ff-bloco"><h5>Scheduled events that can reprice the path</h5><ul class="ff-ev">${ev}</ul></div>` : ""}
    </div></details>`;
  }

  /* Preenche as colunas que substituiram PF/trades/WR/retorno/drawdown. */
  function preencheCelulas() {
    document.querySelectorAll("td.ff-inline[data-pair]").forEach((td) => {
      const d = F && F.fichas ? F.fichas[td.dataset.pair] : null;
      if (!d) return;
      const campo = td.dataset.ff;
      if (campo === "evidencia") {
        const n = (d.evidencia || []).length;
        const contra = (d.contradiz || []).length;
        td.innerHTML = `${n ? `<span class="ff-mini">${n} event${n > 1 ? "s" : ""}</span>` : ""}` +
          `${contra ? `<span class="ff-mini ff-warn">${contra} contradiction${contra > 1 ? "s" : ""}</span>` : ""}` ||
          "—";
      } else {
        const o = d[campo];
        td.innerHTML = o && o.estado ? pill(o.estado) : "—";
      }
    });
  }

  async function injeta() {
    if (F === null) {
      try {
        const r = await fetch(`data/fund_fichas.json?t=${Date.now()}`, { cache: "no-store" });
        F = r.ok ? await r.json() : { fichas: {} };
      } catch (e) { F = { fichas: {} }; }
    }
    document.querySelectorAll("table tbody tr[data-pair]").forEach((tr) => {
      if (tr.dataset.ffDone) return;
      const p = tr.dataset.pair;
      const h = ficha(p);
      if (!h) return;
      const td = document.createElement("td");
      td.colSpan = tr.children.length;
      td.className = "ff-cell";
      td.innerHTML = h;
      const linha = document.createElement("tr");
      linha.className = "ff-row";
      linha.appendChild(td);
      tr.after(linha);
      tr.dataset.ffDone = "1";
    });
    preencheCelulas();
  }

  // O painel redesenha a tabela em varios momentos, entao e preciso reinjetar. Mas a
  // propria injecao altera o DOM: sem desligar o observador durante ela, o observador
  // se re-dispara e entra em laco infinito (foi o que travou a pagina em 31/ago).
  let rodando = false, agendado = null;
  const obs = new MutationObserver(() => {
    if (rodando) return;
    clearTimeout(agendado);
    agendado = setTimeout(ciclo, 250);      // agrupa rajadas de mutacao
  });

  async function ciclo() {
    if (rodando) return;
    rodando = true;
    obs.disconnect();
    try { await injeta(); } catch (e) { /* nao derruba a pagina */ }
    const alvo = document.querySelector("[data-panel='market']") || document.body;
    obs.observe(alvo, { childList: true, subtree: true });
    rodando = false;
  }

  // Se o DOMContentLoaded ja disparou antes deste script carregar, o ouvinte nunca roda.
  // Cobre os dois casos.
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ciclo);
  else ciclo();
})();
