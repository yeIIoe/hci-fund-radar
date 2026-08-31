/* Aba SPREADS — custo real de manter posicao, por par e por lado.
   Le data/custo_carrego.json (gerado por fund_custo_carrego.py).
   Arquivo separado de proposito: nao toca no app.js que ja funciona. */
(function () {
  "use strict";
  const N = (v, d) => (v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(d === undefined ? 2 : d));

  function riscoPill(r) {
    if (r === "IMINENTE") return '<span class="spr-pill spr-red">flip imminent</span>';
    if (r === "PROXIMO") return '<span class="spr-pill spr-amber">flip near</span>';
    return '<span class="spr-pill spr-dim">stable</span>';
  }

  function linha(p) {
    const cl = p.custo_5d_long_pip, cs = p.custo_5d_short_pip;
    const longBarato = p.lado_barato === "COMPRADO";
    const mkL = longBarato ? ' class="spr-good"' : "";
    const mkS = longBarato ? "" : ' class="spr-good"';
    const semLado = p.sem_lado_bom ? '<span class="spr-pill spr-red">no good side</span>' : "";
    return `<tr>
      <td><strong>${p.par}</strong></td>
      <td class="mono">${N(p.spread_medido_pip)}</td>
      <td class="mono">${p.dif_juro > 0 ? "+" : ""}${N(p.dif_juro, 3)}%</td>
      <td class="mono"${mkL}>${N(p.swap_long_pip, 3)}</td>
      <td class="mono"${mkS}>${N(p.swap_short_pip, 3)}</td>
      <td class="mono"${mkL}>${cl === undefined ? "—" : N(cl)}</td>
      <td class="mono"${mkS}>${cs === undefined ? "—" : N(cs)}</td>
      <td>${p.lado_barato === "COMPRADO" ? "long" : "short"}</td>
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
      alvo.innerHTML = `<p class="method-note">Could not read data/custo_carrego.json (${e.message}).
        Run <code>python fund_custo_carrego.py</code> or <code>atualiza_radar.bat</code>.</p>`;
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
      ${alerta.length ? `<div class="spr-alert"><strong>Cheap side about to flip:</strong>
        ${alerta.map((p) => `${p.par} (${p.dif_juro > 0 ? "+" : ""}${N(p.dif_juro, 3)}%, ${N(p.sigmas_do_zero)} sigmas from zero)`).join(" · ")}
        </div>` : ""}
      ${semLado.length ? `<div class="spr-alert spr-alert-dim"><strong>No good side for swing</strong>
        (differential below 0.8% — no carry to offset the markup):
        ${semLado.map((p) => p.par).join(" · ")}</div>` : ""}
      <div class="table-wrap"><table class="data-table">
        <thead><tr>
          <th>Pair</th><th>Spread measured</th><th>2y rate diff</th>
          <th>Swap long</th><th>Swap short</th>
          <th>5d cost long</th><th>5d cost short</th>
          <th>Cheap side</th><th>State</th>
        </tr></thead>
        <tbody>${ordenado.map(linha).join("")}</tbody>
      </table></div>
      <p class="method-note">
        Spread measured from 1-minute bid x ask (Dukascopy; median, 24-38 days per pair).
        Swap estimated from the 2-year differential and calibrated against the broker's own table
        (${doc.calibracao?.fonte || "31 Aug 2026"}): r=${doc.calibracao?.r}, R2=${doc.calibracao?.r2},
        median error ${doc.calibracao?.erro_mediano_pip} pip per night.
        5-day cost = spread + commission (${doc.comissao_pip} pip) + swap x ${doc.noites_5d} nights
        (Wednesday charges 3x). Values in pips per lot. Yields as of ${doc.yields_de}.
        Generated ${doc.gerado_em}.
      </p>`;
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "spreads") render();
  });
})();
