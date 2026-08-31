/* Aba SPREADS — custo real de manter posicao, por par e por lado.
   Le data/custo_carrego.json (gerado por fund_custo_carrego.py).
   Arquivo separado de proposito: nao toca no app.js que ja funciona. */
(function () {
  "use strict";
  const N = (v, d) => (v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(d === undefined ? 2 : d));

  function riscoPill(r) {
    if (r === "IMINENTE") return '<span class="spr-pill spr-red">virada iminente</span>';
    if (r === "PROXIMO") return '<span class="spr-pill spr-amber">virada proxima</span>';
    return '<span class="spr-pill spr-dim">estavel</span>';
  }

  function linha(p) {
    const cl = p.custo_5d_long_pip, cs = p.custo_5d_short_pip;
    const compradoBarato = p.lado_barato === "COMPRADO";
    const mkL = compradoBarato ? ' class="spr-good"' : "";
    const mkS = compradoBarato ? "" : ' class="spr-good"';
    const semLado = p.sem_lado_bom ? '<span class="spr-pill spr-red">sem lado bom</span>' : "";
    return `<tr>
      <td><strong>${p.par}</strong></td>
      <td class="mono">${N(p.spread_medido_pip)}</td>
      <td class="mono">${p.dif_juro > 0 ? "+" : ""}${N(p.dif_juro, 3)}%</td>
      <td class="mono"${mkL}>${N(p.swap_long_pip, 3)}</td>
      <td class="mono"${mkS}>${N(p.swap_short_pip, 3)}</td>
      <td class="mono"${mkL}>${cl === undefined ? "—" : N(cl)}</td>
      <td class="mono"${mkS}>${cs === undefined ? "—" : N(cs)}</td>
      <td>${p.lado_barato === "COMPRADO" ? "comprado" : "vendido"}</td>
      <td>${riscoPill(p.risco_virada)} ${semLado}</td>
    </tr>`;
  }

  async function render() {
    const alvo = document.getElementById("spreadBody");
    if (!alvo) return;
    let doc;
    try {
      const r = await fetch(`data/custo_carrego.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      doc = await r.json();
    } catch (e) {
      alvo.innerHTML = `<p class="method-note">Nao consegui ler data/custo_carrego.json (${e.message}).
        Rode <code>python fund_custo_carrego.py</code> ou o <code>atualiza_radar.bat</code>.</p>`;
      return;
    }
    const ps = doc.pares || [];
    const alerta = ps.filter((p) => p.risco_virada === "IMINENTE" || p.risco_virada === "PROXIMO");
    const semLado = ps.filter((p) => p.sem_lado_bom);
    const ordenado = ps.slice().sort((a, b) => {
      const ca = Math.min(a.custo_5d_long_pip ?? 9e9, a.custo_5d_short_pip ?? 9e9);
      const cb = Math.min(b.custo_5d_long_pip ?? 9e9, b.custo_5d_short_pip ?? 9e9);
      return ca - cb;
    });

    alvo.innerHTML = `
      ${alerta.length ? `<div class="spr-alert"><strong>Lado barato prestes a virar:</strong>
        ${alerta.map((p) => `${p.par} (${p.dif_juro > 0 ? "+" : ""}${N(p.dif_juro, 3)}%, ${N(p.sigmas_do_zero)} sigmas do zero)`).join(" · ")}
        </div>` : ""}
      ${semLado.length ? `<div class="spr-alert spr-alert-dim"><strong>Sem lado bom para swing</strong>
        (diferencial abaixo de 0,8% — nao ha carry para compensar a taxa):
        ${semLado.map((p) => p.par).join(" · ")}</div>` : ""}
      <div class="table-wrap"><table class="data-table">
        <thead><tr>
          <th>Par</th><th>Spread medido</th><th>Dif. juro 2a</th>
          <th>Swap compr.</th><th>Swap vend.</th>
          <th>Custo 5d compr.</th><th>Custo 5d vend.</th>
          <th>Lado barato</th><th>Estado</th>
        </tr></thead>
        <tbody>${ordenado.map(linha).join("")}</tbody>
      </table></div>
      <p class="method-note">
        Spread medido de bid x ask m1 da Dukascopy (mediana, 24 a 38 dias por par).
        Swap estimado do diferencial de 2 anos e calibrado contra a tabela real da FTMO em
        ${doc.calibracao?.fonte || "31-ago-2026"}: r=${doc.calibracao?.r}, R2=${doc.calibracao?.r2},
        erro mediano ${doc.calibracao?.erro_mediano_pip} pip por noite.
        Custo de 5 dias = spread + comissao (${doc.comissao_pip} pip) + swap x ${doc.noites_5d} noites
        (a quarta-feira cobra 3x). Valores em pips por lote. Yields de ${doc.yields_de}.
        Gerado em ${doc.gerado_em}.
      </p>`;
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "spreads") render();
  });
})();
