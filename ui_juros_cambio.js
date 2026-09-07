/* Aba RATES x FX — o painel especificado pelo Eduardo em 31/ago e validado no artefato.
   Le data/juros_vs_cambio.json. Tres campos SEPARADOS por par: trajetoria, magnitude e
   concordancia. Um rotulo unico esconderia a nuance que o painel existe para mostrar. */
(function () {
  "use strict";
  const esc = (t) => String(t == null ? "" : t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const n1 = (v) => (v == null ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1));
  const n2 = (v) => (v == null ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(2) + "%");
  const cls = (v) => (v == null ? "" : v > 0 ? "jc-up" : v < 0 ? "jc-dn" : "jc-fl");
  const PT = {
    "dates aligned; times to verify": "datas alinhadas; horários a verificar",
    "different periods — comparison unavailable": "períodos diferentes — comparação indisponível",
    "fall distributed across the sessions": "queda distribuída entre os pregões",
    "fall with no consistency across sessions": "queda sem consistência entre os pregões",
    "rise concentrated in a few sessions": "alta concentrada em poucos pregões",
    "rise with no consistency across sessions": "alta sem consistência entre os pregões",
    "directional movement": "movimento direcional", "stability": "estabilidade",
    "comparison unavailable — different periods": "comparação indisponível — períodos diferentes",
    "opposite directions — magnitude insufficient by the adopted criterion": "direções opostas — magnitude insuficiente pelo critério adotado",
    "same direction, both down — both relevant": "mesma direção, ambos caindo — ambos relevantes",
    "same direction, both up — magnitude insufficient by the adopted criterion": "mesma direção, ambos subindo — magnitude insuficiente pelo critério adotado"
  };
  const pt = (v) => PT[String(v || "")] || String(v || "");

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
        <span class="jc-when">${esc(pt(p.sincronizacao))}</span>
      </header>

      <div class="jc-grid">
        <div class="jc-box">
          <h6>Movimento</h6>
          <table class="jc-t"><tbody>
            <tr><td>${esc(p.base)} 2y</td><td class="mono">${p.yield_base}%</td>
                <td class="mono ${cls(p.base_d5)}">${n1(p.base_d5)}</td>
                <td class="mono ${cls(p.base_d20)}">${n1(p.base_d20)}</td></tr>
            <tr><td>${esc(p.quote)} 2y</td><td class="mono">${p.yield_quote}%</td>
                <td class="mono ${cls(p.quote_d5)}">${n1(p.quote_d5)}</td>
                <td class="mono ${cls(p.quote_d20)}">${n1(p.quote_d20)}</td></tr>
            <tr class="jc-tot"><td>Diferencial</td><td class="mono">${p.dif_nivel} pp</td>
                <td class="mono ${cls(p.dif_d5)}">${n1(p.dif_d5)}</td>
                <td class="mono ${cls(p.dif_d20)}">${n1(p.dif_d20)}</td></tr>
          </tbody></table>
          <p class="jc-h">último · 5 pregões · 20 pregões, em pb</p>
        </div>

        <div class="jc-box">
          <h6>Trajetória</h6>
          <p>${esc(pt(t.descricao) || "—")}</p>
          ${passos(p)}
        </div>

        <div class="jc-box">
          <h6>Magnitude <span class="jc-tag ${TAG[t.classe] || ""}">${esc(pt(t.classe) || "—")}</span></h6>
          <table class="jc-t"><tbody>
            <tr><td>Amplitude · max−min</td><td class="mono">${t.amplitude_bp ?? "—"}</td>
                <td class="jc-h">corte ${t.corte_amplitude_bp ?? "—"}</td></tr>
            <tr><td>Saldo</td><td class="mono">${n1(t.saldo_bp)}</td>
                <td class="jc-h">pequeno abaixo de ${t.corte_saldo_bp ?? "—"}</td></tr>
            <tr><td>Caminho percorrido</td><td class="mono jc-h">${t.caminho_bp ?? "—"}</td>
                <td class="jc-h">somente informação</td></tr>
          </tbody></table>
        </div>

        <div class="jc-box">
          <h6>Concordância com o câmbio</h6>
          <p>${esc(pt(c.frase || c) || "—")}</p>
          ${p.fx_d5 != null ? `<table class="jc-t"><tbody>
            <tr><td>5 pregões</td><td class="mono ${cls(p.dif_d5)}">${n1(p.dif_d5)} pb</td>
                <td class="mono ${cls(p.fx_d5)}">${n2(p.fx_d5)}</td></tr>
            <tr><td>20 pregões</td><td class="mono ${cls(p.dif_d20)}">${n1(p.dif_d20)} pb</td>
                <td class="mono ${cls(p.fx_d20)}">${n2(p.fx_d20)}</td></tr>
          </tbody></table>` : ""}
          <p class="jc-h">Direção e suficiência são informadas separadamente. Nenhuma delas afirma
          que o preço seguirá o diferencial.</p>
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
      alvo.innerHTML = `<p class="method-note">Não foi possível ler data/juros_vs_cambio.json (${e.message}).</p>`;
      return;
    }
    const ps = (d.pares || []).slice().sort((a, b) =>
      (a.trajetoria?.suspeita_repeticao ? 1 : 0) - (b.trajetoria?.suspeita_repeticao ? 1 : 0));
    alvo.innerHTML = `
      <div class="jc-sync">
        <b>Juros até ${esc(d.ultima_obs_juro)}; fixing do BCE até ${esc(d.ultima_obs_fx)}.</b>
        Cálculo na janela comum encerrada em <b>${esc(d.janela_comum)}</b>.
        <b>Mesma data final não significa sincronização completa</b> — o fixing ocorre às 16:00 CET e
        os juros são observados em outros horários. <b>${d.comparaveis} de ${d.total} pares têm datas
        alinhadas; horários não verificados.</b>
      </div>
      <div class="jc-cards">${ps.map(card).join("")}</div>
      <p class="method-note">${esc(d.metodo?.diferencial || "")}.
        ${esc(d.metodo?.relevancia || "")}<br>
        Amplitude é o <b>máximo menos o mínimo</b> dos níveis acumulados na janela, não o caminho
        percorrido; a razão caminho ÷ |saldo| aparece apenas como informação e nunca como critério,
        pois explode quando o saldo se aproxima de zero (p99 medido = 98; máximo = 3.973).
        Os percentis foram medidos em 28 pares e 24 anos e depois congelados — convenção documentada,
        não uma verdade descoberta, e sem ajuste pela rentabilidade.<br>
        ${esc(d.metodo?.horizontes || "")}. Gerado em ${esc(d.gerado_em || "")}.</p>`;
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "ratesfx") render();
  });
})();
