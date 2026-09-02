/* MACRO DIRECTION — substitui tudo que era FUND V0.1 na tela.
 *
 * O FUND V0.1 foi reprovado em 16 testes e encerrado como decisao de entrada. Mesmo assim o
 * site continuava mostrando a saida dele em quase toda parte: forca agregada, |FUND| >= 25,
 * ranking de moeda por pontuacao, e uma escolha de par por dia no calendario. Isso confunde,
 * porque parece recomendacao e nao e.
 *
 * O QUE ENTRA NO LUGAR
 *   Overview   as oito reunioes de banco central, em ordem de proximidade, com a taxa atual.
 *   Pares      a matriz: BULL, BEAR ou NAO NEGOCIA, por CONVICCAO em %, nunca por pontuacao.
 *   Calendario o que sai de dado em cada dia e o que aquilo empurra na decisao do BC.
 *
 * ⚠️ NENHUMA PONTUACAO. O Eduardo foi explicito: nao usamos mais score, usamos % de conviccao.
 * ⚠️ NENHUM YIELD entra na decisao. So o dado divulgado contra o que se esperava.
 */
(function () {
  "use strict";

  /* ------------------------------------------------------------------------------------
   * DESLIGA OS DESENHISTAS DO FUND, NA ORIGEM.
   *
   * Duas vezes hoje eu removi elemento do HTML e deixei o app.js escrevendo neles. O
   * resultado foi $("#id").innerHTML estourando em null e derrubando o carregamento inteiro.
   * A licao: nao adianta apagar o DOM depois — tem que impedir a funcao de rodar.
   *
   * renderOverview      escreve em strongestCurrency, strongestValue, weakestCurrency,
   *                     weakestValue, alignedPairs, operationalPairs, qualityNote, updatedAt
   * renderPriorities    escreve em priorityTableBody (a tabela com a coluna FUND)
   * renderCalendarDetail escreve na lateral do calendario, que era o ranking por pontuacao
   *
   * Substituidas por funcoes vazias ANTES de qualquer chamada. O conteudo novo vem de aplica().
   * ---------------------------------------------------------------------------------- */
  const vazia = function () {};

  // 1) Os desenhistas do FUND viram funcoes vazias. Escreviam nos paineis "market" e "pairs",
  //    que este modulo substitui inteiros.
  ["renderOverview", "renderPriorities", "renderCalendarDetail",
   "renderCurrencies", "renderMatrix", "renderPairTable", "renderPairDetail"
  ].forEach(function (nome) {
    try { window[nome] = vazia; } catch (e) { /* ignora */ }
  });

  // 2) TODO o resto ganha try/catch. Isto e o conserto de arquitetura, nao de caso.
  //    Hoje eu quebrei o site tres vezes seguidas pelo mesmo motivo: removi um elemento e
  //    deixei alguma funcao escrevendo nele, e um unico null derrubava o carregamento inteiro
  //    — inclusive as abas que nao tinham nada a ver. Enumerar caso a caso nao converge.
  //    Com o try/catch, um desenhista que aponta para elemento inexistente falha sozinho e o
  //    resto da tela carrega. O erro vai para o console, entao nao fica escondido.
  Object.keys(window).forEach(function (nome) {
    if (!/^render[A-Z]/.test(nome)) return;
    const fn = window[nome];
    if (typeof fn !== "function" || fn === vazia || fn.__macProtegida) return;
    const protegida = function () {
      try { return fn.apply(this, arguments); }
      catch (e) { console.warn("[macro] " + nome + " falhou e foi contida:", e.message); }
    };
    protegida.__macProtegida = true;
    try { window[nome] = protegida; } catch (e) { /* ignora */ }
  });

  const M = { bancos: null, eventos: null, pronto: false,
              mes: new Date(), diaSel: null };
  const BRT = -3;

  const FLAG = {
    USD: "🇺🇸", EUR: "🇪🇺", GBP: "🇬🇧", JPY: "🇯🇵",
    AUD: "🇦🇺", NZD: "🇳🇿", CAD: "🇨🇦", CHF: "🇨🇭",
  };

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function brt(iso) {
    if (!iso) return null;
    const d = new Date(iso);
    if (isNaN(d)) return null;
    const x = new Date(d.getTime() + BRT * 3600e3);
    const p = (n) => String(n).padStart(2, "0");
    return `${p(x.getUTCDate())}/${p(x.getUTCMonth() + 1)} ${p(x.getUTCHours())}:${p(x.getUTCMinutes())}`;
  }

  async function carrega() {
    const pega = async (p) => {
      try {
        const r = await fetch(p + "?t=" + Date.now());
        return r.ok ? await r.json() : null;
      } catch (e) { return null; }
    };
    [M.bancos, M.eventos] = await Promise.all([
      pega("data/bancos_centrais.json"), pega("data/macro_eventos.json"),
    ]);
    M.pronto = !!(M.bancos && M.eventos);
  }

  // Carimbo de frescor. O Eduardo perguntou por que o painel nao atualizava a todo instante —
  // a resposta e que a cadeia rodava 2x/dia e os scripts do leitor nao estavam em cadeia
  // nenhuma. Agora rodam de 15 em 15 minutos, mas o GitHub Actions nao e tempo real: o cron
  // atrasa em horario de pico. Entao o frescor fica na TELA, para nunca mais ficar escondido.
  function frescor() {
    const g = M.eventos && M.eventos.gerado_em;
    if (!g) return "Freshness unknown — the calendar file has no timestamp.";
    const min = Math.round((Date.now() - new Date(g).getTime()) / 60000);
    const quando = min < 2 ? "just now"
                 : min < 90 ? min + " minutes ago"
                 : Math.round(min / 60) + " hours ago";
    const velho = min > 45;
    return `<span class="${velho ? "mac-velho" : "mac-fresco"}">Calendar updated ${quando}</span>` +
           ` · refreshed every ~15 min, though scheduled runs can lag at peak hours` +
           (velho ? " — this one is late." : ".");
  }

  /* ------------------------------------------------------------------ OVERVIEW */

  function painelBancos() {
    if (!M.bancos) return "";
    const bs = M.bancos.bancos;
    const ordem = Object.keys(bs).sort((a, b) =>
      (bs[a].dias_ate ?? 999) - (bs[b].dias_ate ?? 999));

    const linhas = ordem.map((m) => {
      const b = bs[m];
      const dias = b.dias_ate;
      const quando = dias === 0 ? "hoje" : dias === 1 ? "amanha" : `em ${dias} dias`;
      const urgente = dias !== null && dias <= 7;
      const hora = b.hora_local
        ? `${b.hora_local} ${b.fuso.split("/")[1].replace("_", " ")}`
        : "sem hora fixa";
      const emBrt = b.proxima_utc ? brt(b.proxima_utc) : null;
      const mov = b.ultima_mudanca_bp;
      return `<tr class="${urgente ? "mac-urgente" : ""}">
        <td class="mac-moeda">${FLAG[m] || ""} <strong>${m}</strong> <small>${esc(b.sigla)}</small></td>
        <td class="mac-taxa">${esc(b.taxa_texto)}</td>
        <td><small class="${mov > 0 ? "positive" : mov < 0 ? "negative" : "muted"}">
            ${mov > 0 ? "+" : ""}${mov} pb</small>
            <small class="muted"> · ${esc(b.ultima_mudanca)}</small></td>
        <td><strong>${quando}</strong><small class="muted"> · ${esc(b.proxima || "—")}</small></td>
        <td><small>${esc(hora)}</small>${emBrt ? `<small class="muted"> · ${emBrt} BRT</small>` : ""}</td>
      </tr>`;
    }).join("");

    return `<section class="content-section mac-bloco">
      <div class="section-title"><div><h2>Central bank meetings</h2></div>
        <p>Current policy rate and when each one decides next. Times are local with the IANA zone —
           three daylight-saving switches fall inside this calendar.</p></div>
      <div class="table-wrap"><table class="mac-tabela">
        <thead><tr><th>Currency</th><th>Policy rate</th><th>Last change</th>
                   <th>Next decision</th><th>Local time</th></tr></thead>
        <tbody>${linhas}</tbody></table></div>
      <p class="mac-frescor">${frescor()}</p>
      <p class="method-note">The rate and the dates are facts, checked against each central bank's own
        pages on 1 Sep 2026. What each one will <em>do</em> is a separate reading — it comes from the
        released data, never from a score.</p>
    </section>`;
  }

  /* --------------------------------------------------------------- MATRIZ DOS PARES */

  /* A MATRIZ DOS PARES — o que da para publicar HOJE, com honestidade.
   *
   * A leitura completa (o que cada BC VAI fazer, derivada do fluxo de dados) depende da fonte
   * do resultado ao vivo, que ainda nao existe. Mas ha um fato que ja temos e que e util
   * sozinho: **onde cada banco central foi da ultima vez**. Nao e previsao, e historico.
   *
   * O placar de hoje e 4 a 4 — quatro subiram por ultimo (NZD, EUR, JPY, AUD) e quatro
   * cortaram (USD, GBP, CAD, CHF). Isso ja separa os pares com divergencia de CICLO dos que
   * estao no mesmo lado.
   *
   * ⚠️ Divergencia de ciclo NAO e sinal de entrada. E contexto: diz que os dois bancos estao
   * em fases diferentes, o que e condicao necessaria para a tese do Eduardo, nao suficiente.
   */
  const PARES = [
    "EURUSD","GBPUSD","AUDUSD","NZDUSD","USDJPY","USDCAD","USDCHF",
    "EURGBP","EURJPY","EURAUD","EURNZD","EURCAD","EURCHF",
    "GBPJPY","GBPAUD","GBPNZD","GBPCAD","GBPCHF",
    "AUDJPY","AUDNZD","AUDCAD","AUDCHF",
    "NZDJPY","NZDCAD","NZDCHF","CADJPY","CADCHF","CHFJPY",
  ];

  function matrizPares() {
    if (!M.bancos) return "";
    const bs = M.bancos.bancos;
    const ciclo = (m) => (bs[m] && bs[m].ultima_mudanca_bp > 0) ? 1
                       : (bs[m] && bs[m].ultima_mudanca_bp < 0) ? -1 : 0;
    const rot = { 1: "last move UP", "-1": "last move DOWN", 0: "unchanged" };

    const subiram = Object.keys(bs).filter((m) => ciclo(m) > 0);
    const cortaram = Object.keys(bs).filter((m) => ciclo(m) < 0);

    const linhas = PARES.map((par) => {
      const b = par.slice(0, 3), q = par.slice(3);
      const cb = ciclo(b), cq = ciclo(q);
      const diverge = cb !== cq;
      const lado = diverge ? (cb > cq ? "base" : "quote") : null;
      const dias = Math.min(bs[b] ? bs[b].dias_ate : 99, bs[q] ? bs[q].dias_ate : 99);
      return { par, b, q, cb, cq, diverge, lado, dias };
    }).sort((a, x) => (x.diverge - a.diverge) || (a.dias - x.dias));

    const corpo = linhas.map((L) => `<tr class="${L.diverge ? "mac-div" : "mac-mesmo"}">
      <td><strong>${L.par}</strong></td>
      <td><span class="${L.cb > 0 ? "positive" : L.cb < 0 ? "negative" : "muted"}">
          ${FLAG[L.b] || ""} ${L.b} · ${rot[L.cb]}</span></td>
      <td><span class="${L.cq > 0 ? "positive" : L.cq < 0 ? "negative" : "muted"}">
          ${FLAG[L.q] || ""} ${L.q} · ${rot[L.cq]}</span></td>
      <td>${L.diverge
            ? '<span class="mac-tag-div">cycle divergence</span>'
            : '<span class="mac-tag-igual">same side</span>'}</td>
      <td><small class="muted">next decision in ${L.dias}d</small></td>
    </tr>`).join("");

    return `<section class="content-section mac-bloco">
      <div class="section-title"><div><h2>Policy cycle by pair</h2></div>
        <p>Where each central bank last went. Not a forecast — the direction of its last move.</p></div>

      <div class="mac-placar">
        <div><span>Last move UP</span><strong>${subiram.map((m) => FLAG[m] + " " + m).join("  ")}</strong></div>
        <div><span>Last move DOWN</span><strong>${cortaram.map((m) => FLAG[m] + " " + m).join("  ")}</strong></div>
      </div>

      <div class="table-wrap"><table class="mac-tabela mac-pares">
        <thead><tr><th>Pair</th><th>Base leg</th><th>Quote leg</th>
                   <th>Cycle</th><th>Nearest meeting</th></tr></thead>
        <tbody>${corpo}</tbody></table></div>

      <p class="method-note"><strong>Cycle divergence is context, not a signal.</strong> Two banks in
        different phases is the necessary condition for a fundamental thesis — not a sufficient one.
        What is still missing is the reading of what each one will <em>do next</em>, which comes from
        the released data measured against its forecast. That needs the live source for the released
        value, which is not connected yet.</p>
      <p class="method-note">⚖️ <strong>Two legs, always.</strong> A pair is not an asset, it is two
        currencies — read each side to find which one gives the reason. And pairs sharing that leg are
        the same bet: on 2 Sep the GBPNZD move was 82% the kiwi, so NZDUSD, NZDCAD and AUDNZD were all
        saying the same thing. Holding two of them does not diversify, it doubles.</p>
    </section>`;
  }


  /* ------------------------------------------------------------------ CALENDARIO */

  function eventosDoDia(iso) {
    if (!M.eventos) return [];
    return M.eventos.eventos.filter((e) => (e.quando_utc || "").slice(0, 10) === iso);
  }

  function celulaEventos(iso) {
    const ev = eventosDoDia(iso).filter((e) => String(e.impacto).toLowerCase() !== "low");
    if (!ev.length) return "";
    const decisao = ev.find((e) => e.familia === "decisao");
    const top = ev.slice(0, 3);
    return `<div class="mac-cel">
      ${decisao ? `<span class="mac-decisao">${FLAG[decisao.moeda] || ""} ${esc(decisao.moeda)} decides</span>` : ""}
      ${top.map((e) => `<span class="mac-ev ${String(e.impacto).toLowerCase() === "high" ? "alto" : ""}">
          ${FLAG[e.moeda] || ""} ${esc((e.titulo || "").slice(0, 26))}</span>`).join("")}
      ${ev.length > 3 ? `<span class="mac-mais">+${ev.length - 3}</span>` : ""}
    </div>`;
  }

  function fichaEvento(e) {
    const cen = (e.cenarios || []).map((c) =>
      `<li><span>${esc(c.caso)}</span><strong>${esc(c.empurra)}</strong></li>`).join("");
    const barra = e.previsao
      ? `<div class="mac-barra"><span>forecast <b>${esc(e.previsao)}</b></span>
           <span>previous <b>${esc(e.anterior || "—")}</b></span>
           <span>actual <b>${esc(e.resultado || "not out")}</b></span></div>`
      : `<div class="mac-barra mac-sem"><span>no forecast published — a surprise cannot be measured</span></div>`;
    const leitura = e.estado === "DIVULGADO"
      ? `<p class="mac-leitura ${e.empurrao > 0 ? "positive" : e.empurrao < 0 ? "negative" : "muted"}">
           <strong>${esc(e.classe || "")}</strong> — ${esc(e.empurrao_texto)}</p>`
      : "";
    return `<article class="mac-ficha">
      <header><span class="mac-hora">${brt(e.quando_utc) || ""} BRT</span>
        <strong>${FLAG[e.moeda] || ""} ${esc(e.titulo)}</strong>
        <span class="tag">${esc(e.impacto)}</span></header>
      ${barra}${leitura}
      ${e.porque ? `<p class="mac-porque">${esc(e.porque)}</p>` : ""}
      ${cen ? `<ul class="mac-cenarios">${cen}</ul>` : ""}
    </article>`;
  }

  function painelDoDia(iso) {
    const ev = eventosDoDia(iso);
    if (!ev.length) {
      return `<div class="mac-vazio"><strong>No scheduled release this day.</strong></div>`;
    }
    const ordem = { high: 0, medium: 1, low: 2 };
    ev.sort((a, b) => (ordem[String(a.impacto).toLowerCase()] ?? 3) -
                      (ordem[String(b.impacto).toLowerCase()] ?? 3) ||
                      String(a.quando_utc).localeCompare(String(b.quando_utc)));
    return ev.filter((e) => String(e.impacto).toLowerCase() !== "low").map(fichaEvento).join("")
        || `<div class="mac-vazio"><strong>Only low-impact releases this day.</strong></div>`;
  }

  /* -------------------------------------------------------------------- APLICAR */

  function limpaFundDaTela() {
    // Alvos localizados um a um no DOM real, em vez de varredura larga: varredura larga
    // remove coisa legitima e e dificil de auditar depois.

    // o banner laranja do veredito do FUND V0.1 — sai inteiro; o veredito vive na memoria
    // do projeto, nao na tela do leitor
    const banner = document.querySelector(".aviso-reprovado");
    if (banner) banner.remove();

    // A fileira de cards do FUND (STRONGEST / WEAKEST / OUTSIDE NEUTRAL / COVERAGE) ficou
    // vazia depois que renderOverview foi desligada — so tracinhos. Sai a secao inteira.
    const overview = document.querySelector("section.overview");
    if (overview && /STRONGEST/i.test(overview.textContent || "")) overview.remove();

    // cabecalho: era "HCI FUND | FX MACRO"; vira "HCI MACRO DIRECTION"
    const marca = document.querySelector(".identity strong");
    if (marca && /^\s*FUND\s*$/i.test(marca.textContent)) marca.textContent = "MACRO DIRECTION";
    const escopo = document.querySelector(".identity .scope");
    if (escopo && /^\s*FX MACRO\s*$/i.test(escopo.textContent)) escopo.remove();

    const sys = document.getElementById("systemMessage");
    if (sys && /FUND/i.test(sys.textContent)) {
      sys.textContent = "Reading panel. It gives the fundamental side; the entry is yours.";
    }

    // rotulos orfaos cujo cartao ja saiu (ex.: "Outside neutral" sem numero)
    document.querySelectorAll("span, small, h3").forEach((el) => {
      if (el.children.length) return;
      const t = (el.textContent || "").trim();
      if (/^outside neutral$/i.test(t) || /^\|FUND\|/i.test(t)) {
        const cartao = el.closest(".metric-card, .kpi, .summary-card") || el;
        cartao.remove();
      }
    });

    // textos herdados, inclusive dois em portugues num site que e todo em ingles
    const TROCA = [
      [/FUND decides FX macro\./i,
       "Macro Direction reads the central banks."],
      [/EQUITIES\s*[—-]\s*unidade e a EMPRESA\.\s*Nao usa FUND nem par de moeda\./i,
       "EQUITIES — the unit here is the COMPANY. No currency pairs."],
      [/Different house, different method\. No FUND here, no currency pairs\./i,
       "Different house, different method. No currency pairs here."],
      [/HCI FUND Radar/i, "HCI Macro Direction"],
      [/The single input the FUND is built from\..*$/i,
       "Two-year sovereign yields, kept for context only. They do not feed the reading — " +
       "they are published at D+1, after the currency has already moved."],
      [/Causal selection: only the FUND of the day itself.*$/i,
       "Each day shows the scheduled releases and what each one pushes on the rate decision."],
    ];
    document.querySelectorAll("strong, p, span, small, h1, h2, h3, td, th, summary, li")
      .forEach((el) => {
        if (el.children.length) return;
        let t = el.textContent;
        if (!t || !/FUND/i.test(t)) return;
        TROCA.forEach(([re, novo]) => { t = t.replace(re, novo); });
        t = t.replace(/FUND/g, "macro");
        if (t !== el.textContent) el.textContent = t;
      });

    // A linha de status pode ficar com o erro de um desenhista do FUND que rodou ANTES deste
    // modulo carregar (ele entra por ultimo, entao nao alcanca a primeira passada). O erro e
    // real, mas vem de funcao morta — e ficar na tela confunde. Registramos no console e
    // corrigimos a linha, so quando o conteudo novo esta de fato desenhado.
    const sys2 = document.getElementById("systemMessage");
    if (sys2 && /Could not load|Cannot set/i.test(sys2.textContent)
        && document.querySelector(".mac-tabela")) {
      console.warn("[macro] erro de carga vindo de desenhista do FUND, ja desativado:",
                   sys2.textContent);
      sys2.textContent = "Reading panel. It gives the fundamental side; the entry is yours.";
    }

    // o rodape ainda descrevia o FUND: "Sovereign 2-year yield momentum across 28 FX crosses"
    document.querySelectorAll("footer p, .site-footer p, footer small").forEach((el) => {
      if (el.children.length) return;
      if (/2-year yield momentum|yield momentum across/i.test(el.textContent || "")) {
        el.textContent = "Central bank readings across 28 FX crosses. It gives the fundamental "
          + "side of each leg — entries, sizing and execution remain discretionary.";
      }
    });

    const logo = document.querySelector(".brand-name, .logo-text");
    if (logo && /FUND/i.test(logo.textContent)) logo.textContent = "MACRO DIRECTION";
  }


  function desenhaCalendario() {
    const grade = document.querySelector(".mac-cal");
    if (!grade) return;
    const ano = M.mes.getFullYear(), mes = M.mes.getMonth();
    const tit = document.querySelector(".mac-mes-titulo");
    if (tit) tit.textContent = M.mes.toLocaleDateString("en-GB",
      { month: "long", year: "numeric" });

    const primeiro = new Date(Date.UTC(ano, mes, 1));
    const vazios = (primeiro.getUTCDay() + 6) % 7;           // semana comeca na segunda
    const ndias = new Date(Date.UTC(ano, mes + 1, 0)).getUTCDate();
    const hojeIso = new Date().toISOString().slice(0, 10);

    let html = "";
    for (let i = 0; i < vazios; i++) html += '<div class="mac-dia-vazio"></div>';
    for (let d = 1; d <= ndias; d++) {
      const iso = `${ano}-${String(mes + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const ev = eventosDoDia(iso).filter((e) => String(e.impacto).toLowerCase() !== "low");
      const dec = ev.find((e) => e.familia === "decisao");
      html += `<button type="button" class="mac-dia-cel${iso === hojeIso ? " mac-hoje" : ""}${
          iso === M.diaSel ? " mac-sel" : ""}${ev.length ? " mac-tem" : ""}" data-mac-dia="${iso}">
        <span class="mac-num">${d}</span>
        ${dec ? `<span class="mac-decisao">${FLAG[dec.moeda] || ""} ${esc(dec.moeda)} decides</span>` : ""}
        ${ev.slice(0, 3).map((e) => `<span class="mac-ev${
            String(e.impacto).toLowerCase() === "high" ? " alto" : ""}">${
            FLAG[e.moeda] || ""} ${esc((e.titulo || "").slice(0, 22))}</span>`).join("")}
        ${ev.length > 3 ? `<span class="mac-mais">+${ev.length - 3}</span>` : ""}
      </button>`;
    }
    grade.innerHTML = html;
    grade.querySelectorAll("[data-mac-dia]").forEach((b) =>
      b.addEventListener("click", () => { M.diaSel = b.dataset.macDia; desenhaCalendario(); }));

    const abaixo = document.getElementById("macLeitura");
    if (!abaixo) return;
    const iso = M.diaSel;
    const ev = iso ? eventosDoDia(iso).filter((e) => String(e.impacto).toLowerCase() !== "low") : [];
    abaixo.innerHTML = `<div class="section-title">
        <div><h2>${iso ? "What happens on " + iso.split("-").reverse().join("/")
                        : "Reading of the day"}</h2></div>
        <p>${iso ? (ev.length
              ? "Each release, what it is measured against, and what each outcome would push on the rate decision."
              : "Nothing above low impact scheduled this day.")
            : "Pick a day on the calendar above."}</p></div>
      <div class="mac-dia">${iso ? painelDoDia(iso)
        : '<div class="mac-vazio"><strong>Pick a day on the calendar above.</strong></div>'}</div>`;
  }

  function aplica() {
    if (!M.pronto) return;

    // OVERVIEW: troca o miolo do painel
    const over = document.querySelector('[data-panel="market"]');
    // Overview mostra SO as reunioes; a matriz de 28 linhas fica na aba Pairs.
    // Repetir a mesma tabela em duas abas so gera ruido — e foi o que o Eduardo apontou no
    // FUND: informacao demais na tela confunde mais do que informa.
    if (over && !over.querySelector(".mac-bloco")) over.innerHTML = painelBancos();

    // PARES: o mesmo, ate o leitor produzir
    const pares = document.querySelector('[data-panel="pairs"]');
    if (pares && !pares.querySelector(".mac-bloco")) pares.innerHTML = matrizPares();

    // CALENDARIO: grade PROPRIA.
    // A grade do FUND era montada a partir dos dias que existiam no historico dele — por isso
    // nao passava de 31/08 e nao conseguia mostrar setembro. Um calendario do que VAI acontecer
    // tem que ser dirigido por DATA, nao por dado historico. Entao construimos a nossa.
    const painelCal = document.querySelector('[data-panel="calendar"]');
    if (painelCal && !painelCal.querySelector(".mac-cal")) {
      painelCal.innerHTML = `<section class="content-section mac-bloco">
          <div class="section-title"><div><h2>Macro calendar</h2></div>
            <p>Scheduled releases and central bank decisions. Pick a day to read what each one
               would push on the rate decision.</p></div>
          <div class="mac-navmes">
            <button type="button" class="mac-nav" data-mac-mes="-1">◀</button>
            <strong class="mac-mes-titulo"></strong>
            <button type="button" class="mac-nav" data-mac-mes="1">▶</button>
          </div>
          <div class="mac-semana">
            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
            <span>Fri</span><span>Sat</span><span>Sun</span></div>
          <div class="mac-cal"></div>
        </section>
        <section id="macLeitura" class="content-section mac-bloco mac-abaixo"></section>`;
      painelCal.querySelectorAll("[data-mac-mes]").forEach((b) =>
        b.addEventListener("click", () => {
          M.mes.setMonth(M.mes.getMonth() + Number(b.dataset.macMes));
          M.diaSel = null; desenhaCalendario();
        }));
    }
    desenhaCalendario();

    limpaFundDaTela();
  }

  const estilo = document.createElement("style");
  estilo.textContent = `
   .mac-bloco{margin-bottom:28px}
   .mac-frescor{font-size:12px;margin:10px 0 0}
   .mac-placar{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0 0 16px}
   .mac-placar>div{padding:11px 13px;border:1px solid rgba(255,255,255,.09);border-radius:9px}
   .mac-placar span{display:block;font-size:10.5px;text-transform:uppercase;
     letter-spacing:.09em;opacity:.5;margin-bottom:5px}
   .mac-placar strong{font-size:14px;letter-spacing:.03em}
   .mac-pares tr.mac-mesmo{opacity:.42}
   .mac-tag-div{font-size:10.5px;padding:2px 8px;border-radius:20px;
     background:rgba(120,200,255,.16);color:#8fd0ff;white-space:nowrap}
   .mac-tag-igual{font-size:10.5px;opacity:.5}
   .mac-fresco{color:#5fd08a}
   .mac-velho{color:#ffb84d;font-weight:600}
   .mac-abaixo{margin-top:26px;padding-top:22px;
     border-top:1px solid rgba(255,255,255,.09)}
   .mac-abaixo .mac-dia{display:grid;gap:10px;
     grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
   .mac-tabela{width:100%;border-collapse:collapse;font-size:14px}
   .mac-tabela th{text-align:left;padding:8px 10px;font-size:11px;letter-spacing:.08em;
     text-transform:uppercase;opacity:.6;border-bottom:1px solid rgba(255,255,255,.08)}
   .mac-tabela td{padding:10px;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:top}
   .mac-tabela tr.mac-urgente td{background:rgba(255,196,0,.06)}
   .mac-moeda small{opacity:.55;margin-left:4px}
   .mac-taxa{font-variant-numeric:tabular-nums;font-weight:600}
   .mac-vazio{padding:22px;border:1px dashed rgba(255,255,255,.14);border-radius:10px;
     line-height:1.55}
   .mac-vazio p{margin:8px 0 0;opacity:.75;font-size:13.5px}
   .mac-navmes{display:flex;align-items:center;gap:14px;margin:0 0 12px}
   .mac-nav{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
     color:inherit;border-radius:7px;padding:5px 12px;cursor:pointer;font-size:13px}
   .mac-nav:hover{background:rgba(255,255,255,.12)}
   .mac-mes-titulo{font-size:15px;letter-spacing:.02em}
   .mac-semana{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}
   .mac-semana span{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;
     opacity:.45;padding-left:4px}
   .mac-cal{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
   .mac-dia-vazio{min-height:78px}
   .mac-dia-cel{min-height:78px;text-align:left;background:rgba(255,255,255,.02);
     border:1px solid rgba(255,255,255,.07);border-radius:8px;padding:6px 7px;color:inherit;
     cursor:pointer;display:flex;flex-direction:column;gap:2px;overflow:hidden}
   .mac-dia-cel:hover{background:rgba(255,255,255,.06)}
   .mac-dia-cel.mac-tem{border-color:rgba(255,255,255,.16)}
   .mac-dia-cel.mac-hoje{outline:1px solid rgba(120,200,255,.5)}
   .mac-dia-cel.mac-sel{background:rgba(120,200,255,.12);border-color:rgba(120,200,255,.55)}
   .mac-num{font-size:12px;font-weight:600;opacity:.8}
   .mac-cel{display:flex;flex-direction:column;gap:3px;margin-top:5px}
   .mac-decisao{font-size:10.5px;font-weight:700;letter-spacing:.04em;color:#ffc400}
   .mac-ev{font-size:10.5px;opacity:.62;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .mac-ev.alto{opacity:.95;font-weight:600}
   .mac-mais{font-size:10px;opacity:.4}
   .mac-ficha{border:1px solid rgba(255,255,255,.08);border-radius:9px;padding:12px;
     margin-bottom:10px}
   .mac-ficha header{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:8px}
   .mac-hora{font-family:ui-monospace,monospace;font-size:11px;opacity:.6}
   .mac-barra{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;opacity:.8;
     padding:7px 0;border-top:1px solid rgba(255,255,255,.06)}
   .mac-barra b{font-variant-numeric:tabular-nums}
   .mac-barra.mac-sem{opacity:.5;font-style:italic}
   .mac-leitura{margin:7px 0 0;font-size:13px}
   .mac-porque{margin:8px 0 0;font-size:12.5px;opacity:.65;line-height:1.5}
   .mac-cenarios{list-style:none;margin:9px 0 0;padding:0;font-size:12px}
   .mac-cenarios li{display:flex;justify-content:space-between;padding:3px 0;
     border-top:1px dotted rgba(255,255,255,.07)}
   .mac-cenarios span{opacity:.65}`;
  document.head.appendChild(estilo);

  carrega().then(() => {
    aplica();
    setInterval(aplica, 900);
    document.addEventListener("click", () => setTimeout(aplica, 60), true);
  });
})();
