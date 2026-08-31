/* Aba RATES x FX — o painel especificado pelo Eduardo em 31/ago e validado no artefato.
   Le data/juros_vs_cambio.json. Tres campos SEPARADOS por par: trajetoria, magnitude e
   concordancia. Um rotulo unico esconderia a nuance que o painel existe para mostrar. */
(function () {
  "use strict";
  const esc = (t) => String(t == null ? "" : t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const n1 = (v) => (v == null ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1));
  const n2 = (v) => (v == null ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(2) + "%");
  const cls = (v) => (v == null ? "" : v > 0 ? "jc-up" : v < 0 ? "jc-dn" : "jc-fl");

  const TAG = {
    "movimento direcional": "jc-dir", "estabilidade": "jc-est",
    "oscilacao sem direcao liquida": "jc-osc", "movimento intermediario": "jc-int",
    "fronteira do corte de amplitude": "jc-fro", "atualizacao nao verificavel": "jc-nv",
  };

  function passos(p) {
    const ps = p.passos_bp || [];
    if (!ps.length) return "";
    const mx = Math.max(...ps.map(Math.abs));
    return `<div class="jc-steps">${ps.map((x) =>
      `<span class="jc-step ${x < 0 ? "neg" : Math.abs(x) >= mx * 0.8 ? "big" : ""}">${n1(x)}</span>`).join("")}</div>`;
  }

  function card(p) {
    const t = p.trajetoria || {}, c = p.estado_cambial || {};
    const nv = t.suspeita_repeticao;
    return `<article class="jc-card${nv ? " jc-card-nv" : ""}">
      <header>
        <strong>${esc(p.par)}</strong>
        <span class="jc-def">${esc(p.base)} 2y − ${esc(p.quote)} 2y</span>
        <span class="jc-when">${esc(p.sincronizacao || "")}</span>
      </header>

      <div class="jc-grid">
        <div class="jc-box">
          <h6>Movement</h6>
          <table class="jc-t"><tbody>
            <tr><td>${esc(p.base)} 2y</td><td class="mono">${p.yield_base}%</td>
                <td class="mono ${cls(p.base_d5)}">${n1(p.base_d5)}</td>
                <td class="mono ${cls(p.base_d20)}">${n1(p.base_d20)}</td></tr>
            <tr><td>${esc(p.quote)} 2y</td><td class="mono">${p.yield_quote}%</td>
                <td class="mono ${cls(p.quote_d5)}">${n1(p.quote_d5)}</td>
                <td class="mono ${cls(p.quote_d20)}">${n1(p.quote_d20)}</td></tr>
            <tr class="jc-tot"><td>Differential</td><td class="mono">${p.dif_nivel} pp</td>
                <td class="mono ${cls(p.dif_d5)}">${n1(p.dif_d5)}</td>
                <td class="mono ${cls(p.dif_d20)}">${n1(p.dif_d20)}</td></tr>
          </tbody></table>
          <p class="jc-h">last · 5 sessions · 20 sessions, in bp</p>
        </div>

        <div class="jc-box">
          <h6>Trajectory</h6>
          <p>${esc(t.descricao || "—")}</p>
          ${passos(p)}
        </div>

        <div class="jc-box">
          <h6>Magnitude <span class="jc-tag ${TAG[t.classe] || ""}">${esc(t.classe || "—")}</span></h6>
          <table class="jc-t"><tbody>
            <tr><td>Amplitude · max−min</td><td class="mono">${t.amplitude_bp ?? "—"}</td>
                <td class="jc-h">cut ${t.corte_amplitude_bp ?? "—"}</td></tr>
            <tr><td>Balance</td><td class="mono">${n1(t.saldo_bp)}</td>
                <td class="jc-h">small below ${t.corte_saldo_bp ?? "—"}</td></tr>
            <tr><td>Path travelled</td><td class="mono jc-h">${t.caminho_bp ?? "—"}</td>
                <td class="jc-h">information only</td></tr>
          </tbody></table>
        </div>

        <div class="jc-box">
          <h6>FX agreement</h6>
          <p>${esc(c.frase || c || "—")}</p>
          ${p.fx_d5 != null ? `<table class="jc-t"><tbody>
            <tr><td>5 sessions</td><td class="mono ${cls(p.dif_d5)}">${n1(p.dif_d5)} bp</td>
                <td class="mono ${cls(p.fx_d5)}">${n2(p.fx_d5)}</td></tr>
            <tr><td>20 sessions</td><td class="mono ${cls(p.dif_d20)}">${n1(p.dif_d20)} bp</td>
                <td class="mono ${cls(p.fx_d20)}">${n2(p.fx_d20)}</td></tr>
          </tbody></table>` : ""}
          <p class="jc-h">Direction and sufficiency are reported separately. Neither claims the
          price will follow the differential.</p>
        </div>
      </div>
    </article>`;
  }

  async function render() {
    const alvo = document.getElementById("jcBody");
    if (!alvo) return;
    let d;
    try {
      const r = await fetch(`data/juros_vs_cambio.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      d = await r.json();
    } catch (e) {
      alvo.innerHTML = `<p class="method-note">Could not read data/juros_vs_cambio.json (${e.message}).</p>`;
      return;
    }
    const ps = (d.pares || []).slice().sort((a, b) =>
      (a.trajetoria?.suspeita_repeticao ? 1 : 0) - (b.trajetoria?.suspeita_repeticao ? 1 : 0));
    alvo.innerHTML = `
      <div class="jc-sync">
        <b>Rates through ${esc(d.ultima_obs_juro)}; ECB fixing through ${esc(d.ultima_obs_fx)}.</b>
        Computed on the common window ending <b>${esc(d.janela_comum)}</b>.
        <b>Same end date is not full synchronisation</b> — the fixing is struck at 16:00 CET and the
        yields are observed at other hours, so every pair carries <i>dates aligned; times to
        verify</i>. <b>${d.comparaveis} of ${d.total} pairs have aligned dates; times not verified.</b>
      </div>
      <div class="jc-cards">${ps.map(card).join("")}</div>
      <p class="method-note">${esc(d.metodo?.diferencial || "")}.
        ${esc(d.metodo?.relevancia || "")}<br>
        Amplitude is <b>maximum minus minimum</b> of the cumulative levels inside the window, not the
        path travelled; the ratio path ÷ |balance| is shown as information and never as a criterion,
        because it explodes as the balance approaches zero (measured p99 = 98, maximum = 3,973).
        Percentiles were measured across 28 pairs and 24 years and then frozen — a documented
        convention, not a discovered truth, and not tuned against profitability.<br>
        ${esc(d.metodo?.horizontes || "")}. Generated ${esc(d.gerado_em || "")}.</p>`;
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "ratesfx") render();
  });
})();
