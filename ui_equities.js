/* Aba EQUITIES — saida do Research Agent (data/equities_research.json).
   Separado do FUND de proposito: a unidade aqui e a EMPRESA, nao a moeda. */
(function () {
  "use strict";
  const F = (v, d) => (v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(d === undefined ? 2 : d));
  const numero = (v) => (v === null || v === undefined || v === "") ? null : (Number.isFinite(Number(v)) ? Number(v) : null);

  function leitura(pos) {
    if (!pos) return '<span class="spr-pill spr-dim">sem leitura</span>';
    if (/COMPRA/i.test(pos)) return '<span class="spr-pill spr-buy">comprar / manter</span>';
    if (/MANTER/i.test(pos)) return '<span class="spr-pill spr-dim">manter</span>';
    if (/REDUZ|VENDE|SAIR/i.test(pos)) return '<span class="spr-pill spr-red">reduzir</span>';
    return '<span class="spr-pill spr-dim">' + pos.slice(0, 24) + "</span>";
  }

  function linha(n) {
    const up = n.upside;
    const cor = up === null || up === undefined ? "" : (up >= 0.10 ? ' class="spr-good"' : (up <= -0.10 ? ' class="spr-bad"' : ""));
    const alertas = [];
    if (n.regime_ok === false) alertas.push('<span class="spr-pill spr-amber">regime contrário</span>');
    if (n.earnings) alertas.push(`<span class="spr-pill spr-dim">resultado ${String(n.earnings).slice(0, 10)}</span>`);
    if (n.hi52 && n.preco && n.preco / n.hi52 - 1 > -0.03) alertas.push('<span class="spr-pill spr-amber">perto da máxima de 52 semanas</span>');
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
      alvo.innerHTML = `<p class="method-note">Não foi possível ler data/equities_research.json (${e.message}).
        O arquivo é gerado por <code>equities_research.py</code> na atualização do site.</p>`;
      return;
    }
    const ns = (doc.nomes || []).slice().sort((a, b) => (b.upside ?? -9) - (a.upside ?? -9));
    alvo.innerHTML = `
      <div class="spr-alert spr-alert-dim"><strong>${doc.escopo || "Equities"}</strong><br>
        ${doc.limite || ""}</div>
      <div class="table-wrap"><table class="data-table">
        <thead><tr>
          <th>Nome</th><th>Preço</th><th>Alvo</th><th>Potencial</th>
          <th>Leitura</th><th>Alertas</th><th>Tese</th>
        </tr></thead>
        <tbody>${ns.map(linha).join("")}</tbody>
      </table></div>
      <!-- [08/set] a nota de metodo saiu da tela por ordem do dono: "tire o metodo de
           pesquisa". Ela dizia o mesmo em toda secao, em toda carga. O conteudo vive no
           title do titulo da secao e em METODO_HCI_Pesquisa.md, que e onde metodo mora. -->
      <div id="sentinelaBody"></div>`;
    renderCards();
  }

  /* ---- CARDS POR ACAO ----
     Antes o site mostrava o texto cru do scan dentro de um <pre>. Agora cada nome
     vira um card com o MOTIVO ao lado, separado entre comprar e evitar. Os scans
     passaram a emitir JSON na origem, entao nada aqui e reconstruido por regex. */
  /* Ficha da empresa: de onde vem o numero e onde ler mais. Carregada uma vez e
     compartilhada por todos os componentes — 94 empresas num arquivo so. */
  let FICHAS = null;
  async function fichas() {
    if (FICHAS !== null) return FICHAS;
    try {
      const r = await fetch(`data/empresas.json?t=${Date.now()}`, { cache: "no-store" });
      FICHAS = r.ok ? await r.json() : { empresas: {} };
    } catch (e) { FICHAS = { empresas: {} }; }
    return FICHAS;
  }

  function fichaHTML(tk) {
    const d = FICHAS && FICHAS.empresas ? FICHAS.empresas[tk] : null;
    if (!d) return "";
    const links = [];
    if (d.site) links.push(`<a href="${esc(d.site)}" target="_blank" rel="noopener">Site da empresa</a>`);
    if (d.site_ri) links.push(`<a href="${esc(d.site_ri)}" target="_blank" rel="noopener">Relações com investidores</a>`);
    links.push(`<a href="https://finance.yahoo.com/quote/${encodeURIComponent(tk)}" target="_blank" rel="noopener">Yahoo Finance</a>`);
    if (!/\./.test(tk)) links.push(`<a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker=${encodeURIComponent(tk)}&type=10-K" target="_blank" rel="noopener">Documentos na SEC</a>`);
    const meta = [d.setor, d.industria, d.pais,
                  d.funcionarios ? Number(d.funcionarios).toLocaleString("pt-BR") + " funcionários" : null]
                 .filter(Boolean).map((x) => `<span class="eq-met">${esc(x)}</span>`).join("");
    const news = (d.noticias || []).map((n) =>
      `<li><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.titulo)}</a>
       <em>${esc(n.fonte || "")}</em></li>`).join("");
    return `<details class="eq-ficha"><summary>Ficha da empresa e fontes</summary>
      <div class="eq-ficha-body">
        ${d.nome ? `<p class="eq-nome">${esc(d.nome)}</p>` : ""}
        <div class="eq-mets">${meta}</div>
        ${d.o_que_faz ? `<p class="eq-faz">${esc(d.o_que_faz)}</p>` : ""}
        <p class="eq-links">${links.join(" · ")}</p>
        ${news ? `<p class="eq-linha"><b>Cobertura recente</b></p><ul class="eq-news">${news}</ul>` : ""}
        <p class="eq-fonte">Perfil e notícias: Yahoo Finance, leitura em ${esc(d.perfil_em || "—")}.
        ${d.noticias_em ? "Cobertura em " + esc(d.noticias_em) + "." : ""}</p>
      </div></details>`;
  }

  const esc = (t) => String(t == null ? "" : t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function motivoPadrao(n, bom, tipo) {
    if (bom) return n.porque;
    if (tipo === "fornecedores") {
      const r = numero(n.retorno_hoje);
      if (r === null) return "Variação diária indisponível; sem setup até a próxima leitura válida.";
      if (r < 0) return `Queda de ${Math.abs(r).toFixed(1)}%, abaixo do gatilho de 3%.`;
      return `Alta de ${r.toFixed(1)}%; não houve queda para acionar o gatilho.`;
    }
    if (tipo === "deep-value" && Array.isArray(n.reprovacoes) && n.reprovacoes.length) {
      return `Reprovada por ${n.reprovacoes.join(", ")}.`;
    }
    if (tipo === "deep-value" && /NET CASH|balan[cç]o ok/i.test(n.porque_nao || "")) {
      return "Reprovada pela peneira anti-armadilha; revise lucro, fluxo de caixa e endividamento.";
    }
    return n.porque_nao || n.porque;
  }

  function card(n, bom, tipo) {
    const met = n.metricas ? Object.entries(n.metricas)
      .filter(([, v]) => v !== null && v !== undefined && v !== false)
      .map(([k, v]) => `<span class="eq-met"><b>${esc(k)}</b> ${esc(v === true ? "sim" : v)}</span>`).join("") : "";
    const ret = numero(n.retorno_hoje), maxima = numero(n.vs_maxima_12m);
    const mov = (ret !== null || maxima !== null)
      ? `${ret === null ? "" : `<span class="eq-met"><b>hoje</b> ${ret > 0 ? "+" : ""}${ret.toFixed(1)}%</span>`}
         ${maxima === null ? "" : `<span class="eq-met"><b>vs máxima 12m</b> ${maxima > 0 ? "+" : ""}${maxima.toFixed(0)}%</span>`}` : "";
    const motivo = motivoPadrao(n, bom, tipo);
    return `<article class="eq-card ${bom ? "eq-ok" : "eq-no"}">
      <header><strong>${esc(n.ticker)}</strong>
        <span class="eq-nota">${esc(n.nota)}</span>
        ${n.preco ? `<span class="eq-px">${esc(n.preco)}</span>` : ""}</header>
      <div class="eq-mets">${met}${mov}</div>
      ${motivo ? `<p class="eq-porque"><b>${bom ? "Por quê" : "Por que não"}:</b> ${esc(motivo)}</p>` : ""}
      ${n.tipo_queda ? `<p class="eq-linha"><b>Queda:</b> ${esc(n.tipo_queda)}${n.profundidade ? " · " + esc(n.profundidade) : ""}</p>` : ""}
      ${n.risco ? `<p class="eq-linha eq-risco"><b>Risco:</b> ${esc(n.risco)}</p>` : ""}
      ${(n.confianca_status || n.confianca) ? `<p class="eq-linha"><b>Convicção histórica:</b> não calibrada</p>` : ""}
      ${n.plano ? `<p class="eq-linha"><b>Plano:</b> ${esc(n.plano)}</p>` : ""}
      ${n.voce_assina ? `<p class="eq-assina">Você valida: ${esc(n.voce_assina)}</p>` : ""}
      ${fichaHTML(n.ticker)}
    </article>`;
  }

  async function bloco(arq, titulo, subtitulo, tipo, rotulos) {
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
         <div class="eq-grade">${lista.map((n) => card(n, bom, tipo)).join("")}</div>` : "";
    const rejeitados = maus.length ? `<details class="eq-recolhido"><summary>${esc(rotulos[1])} · ${maus.length}</summary>
      ${grade(maus, false, rotulos[1])}</details>` : "";
    return `<div class="section-title" style="margin-top:30px">
        <div><h2 title="${[subtitulo, doc.metodo, doc.limite].filter(Boolean).join(" — ")}">${titulo}</h2></div>
      </div>
      ${grade(bons, true, rotulos[0])}
      ${rejeitados}`;
  }

  /* Revisao de estimativas — o unico sinal fundamental que sobreviveu aos testes de
     equities da casa. Nao vira card por nome: a leitura util e o RANKING e o setor. */
  async function blocoRevisoes() {
    let d;
    try {
      const r = await fetch(`data/revisoes.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) return "";
      d = await r.json();
    } catch (e) { return ""; }
    if (!d.cima || !d.cima.length) return "";
    const todos = [...(d.cima || []), ...(d.baixo || [])].filter((n, i, a) =>
      a.findIndex((x) => x.ticker === n.ticker) === i);
    const tipoRev = (n) => {
      const ini = numero(n.eps_ini), fim = numero(n.eps_fim), analistas = numero(n.n_analistas) || 0;
      if (ini == null || fim == null) return "sem base comparável";
      if (ini < 0 && fim >= 0) return "prejuízo → lucro";
      if (ini >= 0 && fim < 0) return "lucro → prejuízo";
      if (Math.abs(ini) < 0.25) return "base pequena";
      if (analistas < 5) return "menos de 5 analistas";
      return "comparável";
    };
    const comparaveis = todos.filter((n) => tipoRev(n) === "comparável");
    const cima = comparaveis.filter((n) => numero(n.rev_eps_pct) > 0)
      .sort((a, b) => b.rev_eps_pct - a.rev_eps_pct).slice(0, 20);
    const baixo = comparaveis.filter((n) => numero(n.rev_eps_pct) < 0)
      .sort((a, b) => a.rev_eps_pct - b.rev_eps_pct).slice(0, 20);
    const especiais = todos.filter((n) => ["prejuízo → lucro", "lucro → prejuízo", "base pequena"].includes(tipoRev(n)));
    const linha = (n) => `<tr>
      <td><strong>${esc(n.ticker)}</strong></td>
      <td class="eq-setor">${esc(n.setor || "")}</td>
      <td class="mono">${n.preco ?? "—"}</td>
      <td class="mono ${n.rev_eps_pct >= 0 ? "spr-good" : "spr-bad"}">${n.rev_eps_pct >= 0 ? "+" : ""}${n.rev_eps_pct}%</td>
      <td class="mono">${n.rev_receita_pct === null ? "—" : (n.rev_receita_pct >= 0 ? "+" : "") + n.rev_receita_pct + "%"}</td>
      <td class="mono">${n.eps_ini} &rarr; ${n.eps_fim}</td>
      <td class="mono">${n.n_analistas ?? "—"}</td></tr>`;
    const tabela = (ns, rot, cls) => ns.length ? `<h4 class="eq-sub ${cls}">${rot} <span>${ns.length}</span></h4>
      <div class="table-wrap"><table class="data-table"><thead><tr>
        <th>Nome</th><th>Setor</th><th>Preço</th><th>Revisão do LPA</th><th>Revisão da receita</th>
        <th>LPA antes &rarr; depois</th><th>Analistas</th></tr></thead>
        <tbody>${ns.map(linha).join("")}</tbody></table></div>` : "";
    const especiaisHtml = especiais.length ? `<details class="eq-recolhido"><summary>Mudança de sinal ou base pequena · ${especiais.length}</summary>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Nome</th><th>Setor</th><th>Classificação</th>
      <th>LPA antes &rarr; depois</th><th>Analistas</th></tr></thead><tbody>${especiais.map((n) => `<tr>
      <td><strong>${esc(n.ticker)}</strong></td><td>${esc(n.setor || "")}</td><td>${esc(tipoRev(n))}</td>
      <td class="mono">${n.eps_ini} &rarr; ${n.eps_fim}</td><td class="mono">${n.n_analistas ?? "—"}</td></tr>`).join("")}
      </tbody></table></div></details>` : "";
    const porSetor = {};
    comparaveis.forEach((n) => { (porSetor[n.setor || "Sem setor"] ||= []).push(Number(n.rev_eps_pct)); });
    const mediana = (xs) => { const a = xs.slice().sort((x, y) => x - y), m = Math.floor(a.length / 2);
      return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; };
    const set = Object.entries(porSetor).map(([setor, xs]) => ({ setor, n: xs.length, rev_mediana: mediana(xs),
      pct_subindo: Math.round(xs.filter((x) => x > 0).length / xs.length * 100) }))
      .filter((x) => x.n >= 2).sort((a, b) => b.rev_mediana - a.rev_mediana);
    return `<div class="section-title" style="margin-top:30px">
        <div><h2 title="O que os analistas mudaram entre dois retratos congelados no tempo. Revisão do consenso de LPA do ano fiscal entre dois retratos sem revisão retroativa. Filtro do ranking: mesmo sinal do LPA, base inicial absoluta de pelo menos 0,25 e no mínimo 5 analistas. Janela ${esc(d.janela || "")} · universo de ${d.n_tickers} nomes · ${comparaveis.length} casos comparáveis · gerado em ${esc(d.gerado_em || "")}.">Revisões de lucros</h2></div>
        
      </div>
      <!-- [08/set] "revisoes de lucro a mesma coisa": a nota de metodo sai da tela e vai
           para o title do titulo da secao, como nas outras quatro. -->
      <div class="eq-setores">${set.map((x) => `<span class="eq-set ${x.rev_mediana >= 0 ? "eq-set-up" : "eq-set-dn"}">
        ${esc(x.setor)} <b>${x.rev_mediana >= 0 ? "+" : ""}${x.rev_mediana}%</b>
        <i>${x.pct_subindo}% subindo · n=${x.n}</i></span>`).join("")}</div>
      ${tabela(cima, "Revisadas para cima", "eq-sub-ok")}
      ${tabela(baixo, "Revisadas para baixo", "eq-sub-no")}
      ${especiaisHtml}`;
  }

  async function renderCards() {
    const alvo = document.getElementById("sentinelaBody");
    if (!alvo) return;
    await fichas();                       // sem isto os cards saem sem fonte
    // Fornecedores voltou: sumiu quando o despejo de texto saiu, porque so existia como <pre>.
    const forn = await bloco("fornecedores.json", "Fornecedores estratégicos",
      "Fornecedores das gigantes — semicondutores, datacenters, energia, água, saúde e defesa. Quedas em nomes com tese registrada.",
      "fornecedores", ["Com gatilho", "Sem setup"]);
    const dv = await bloco("deep_value_scan.json", "Valor profundo",
      "Empresas realmente baratas, filtradas contra armadilhas de valor.",
      "deep-value", ["Candidatos para análise", "Reprovados pela peneira"]);
    const btd = await bloco("btd_scan.json", "Comprar a queda + manter",
      "Queda do dia em uma empresa de qualidade — separando medo do mercado de problema da companhia.",
      "btd", ["Com gatilho", "Sem setup"]);
    const rev = await blocoRevisoes();
    const html = forn + dv + btd + rev;
    if (html) alvo.insertAdjacentHTML("beforeend", html);
  }

  document.addEventListener("DOMContentLoaded", render);
  const bar = document.getElementById("tabBar");
  if (bar) bar.addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (b && b.dataset.tab === "equities") render();
  });
})();
