/* Ficha do par — o upgrade do FUND conforme o Volume I do AEGH.
   Injeta, em cada linha da tabela de candidatos, uma ficha expansivel com as QUATRO
   saidas que a secao 05 mantem separadas, cada uma com fonte e data.
   Nao emite direcao: o FUND V0.1 esta congelado como reprovado nos testes direcionais. */
(function () {
  "use strict";
  let F = null;
  const esc = (t) => String(t == null ? "" : t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  const PILL = {
    coerente: "ff-ok", fortalecendo: "ff-ok", alta: "ff-ok",
    contraditoria: "ff-warn", enfraquecendo: "ff-warn", baixa: "ff-warn",
    parcial: "ff-dim", estavel: "ff-dim", media: "ff-dim",
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
    const causa = c ? `<div class="ff-bloco"><h5>Dominant cause</h5>
        <p>${esc(c.frase)}</p>
        <p class="ff-src">2y at ${c.yield}% · 1d ${c.bp_1d} bp · 20d ${c.bp_20d} bp ·
        read ${esc(c.lido_em || "")}<br>
        ${c.fonte_url ? `<a href="${esc(c.fonte_url)}" target="_blank" rel="noopener">${esc(c.fonte || "source")}</a>` : esc(c.fonte || "")}
        ${c.bc_url ? ` · <a href="${esc(c.bc_url)}" target="_blank" rel="noopener">${esc(c.banco_central || "central bank")}</a>` : ""}</p>
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
      ${bloco("Analytical confidence", d.confianca_analitica)}
      ${contra ? `<div class="ff-bloco ff-contra"><h5>What contradicts it</h5><ul>${contra}</ul></div>` : ""}
      ${ev ? `<div class="ff-bloco"><h5>Scheduled events that can reprice the path</h5><ul class="ff-ev">${ev}</ul></div>` : ""}
    </div></details>`;
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
  }

  // o painel redesenha a tabela em varios momentos; reinjeta quando isso acontece
  const obs = new MutationObserver(() => { injeta(); });
  document.addEventListener("DOMContentLoaded", () => {
    injeta();
    const alvo = document.querySelector("[data-panel='market']") || document.body;
    obs.observe(alvo, { childList: true, subtree: true });
  });
})();
