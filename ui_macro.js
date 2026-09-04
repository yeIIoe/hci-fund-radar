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

  const M = { bancos: null, eventos: null, eua: null, pronto: false,
              mes: new Date(), diaSel: null,
              parSel: null, filtro: "todos", moedaSel: null, moedaCal: null, sent: null,
              menuAgrupado: false };
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

  // Dias de CALENDARIO ate uma data, contados em BRT, inteiros. Math.round de dias fracionarios
  // dava "11 days" para o FOMC de 16/set na manha de 04/set — sao 12 (Eduardo pegou, 04/set).
  // E conta a partir de HOJE, nao do carimbo da rodada: se o cron pular horas, a contagem nao
  // envelhece junto.
  function diasAte(isoData) {
    if (!isoData || isoData.length < 10) return null;
    const alvo = Date.UTC(+isoData.slice(0, 4), +isoData.slice(5, 7) - 1, +isoData.slice(8, 10));
    const h = hojeBrt();
    const hoje = Date.UTC(+h.slice(0, 4), +h.slice(5, 7) - 1, +h.slice(8, 10));
    if (isNaN(alvo) || isNaN(hoje)) return null;
    return Math.round((alvo - hoje) / 864e5);
  }

  async function carrega() {
    const pega = async (p) => {
      try {
        const r = await fetch(p + "?t=" + Date.now());
        return r.ok ? await r.json() : null;
      } catch (e) { return null; }
    };
    // O leitor dos EUA e OPCIONAL: se o arquivo faltar (cota do BLS, fonte fora), o resto do
    // painel desenha igual. So o bloco dos EUA some — e some declarado, nao em branco.
    [M.bancos, M.eventos, M.eua, M.discursos, M.sent, M.geo] = await Promise.all([
      pega("data/bancos_centrais.json"), pega("data/macro_eventos.json"),
      pega("data/eua_leitura.json"), pega("data/bc_discursos.json"),
      pega("data/sentimento.json"), pega("data/geopolitica.json"),
    ]);
    // valida a FORMA, nao so a presenca: um JSON truncado passaria no teste de presenca e
    // estouraria dentro dos desenhistas
    M.pronto = !!(M.bancos && M.bancos.bancos && typeof M.bancos.bancos === "object" &&
                  M.eventos && Array.isArray(M.eventos.eventos));
    if (!M.pronto) console.warn("[macro] dados incompletos:", { bancos: !!M.bancos, eventos: !!M.eventos });
  }

  // Carimbo de frescor. O Eduardo perguntou por que o painel nao atualizava a todo instante —
  // a resposta e que a cadeia rodava 2x/dia e os scripts do leitor nao estavam em cadeia
  // nenhuma. Agora rodam de 15 em 15 minutos, mas o GitHub Actions nao e tempo real: o cron
  // atrasa em horario de pico. Entao o frescor fica na TELA, para nunca mais ficar escondido.
  function idadeTexto(min) {
    return min < 2 ? "just now" : min < 90 ? min + " minutes ago" : Math.round(min / 60) + " hours ago";
  }

  function frescor() {
    const E = M.eventos || {};
    // Dois carimbos: o do RELOGIO (a rodada) e o do DADO (a ultima leitura boa da fonte). Se a
    // fonte cair, a rodada continua e o relogio fica "fresco" — e o dado, velho. O que o
    // usuario precisa ver e a idade do DADO. Revisao de 03/set.
    const g = E.fonte_gerado_em || E.gerado_em;
    if (!g) return "Freshness unknown — the calendar file has no timestamp.";
    const min = Math.round((Date.now() - new Date(g).getTime()) / 60000);
    const velho = min > 45;
    let base = `<span class="${velho ? "mac-velho" : "mac-fresco"}">Calendar data ${idadeTexto(min)}</span>` +
           ` · refreshed every ~15 min, though scheduled runs can lag at peak hours` +
           (velho ? " — this one is late." : ".");
    if (E.fonte && E.fonte !== "fxstreet") {
      base += `<br><span class="mac-velho">Fallback source active: ${esc(E.aviso_fonte || E.fonte)}</span>`;
    }

    // Duas defasagens, separadas de proposito. A de cima e o RELOGIO (o cron). A de baixo e a
    // FONTE: quanto o numero levou do horario agendado ate aparecer nela, medido nesta rodada
    // e nao alegado. Confundir as duas foi um erro meu em 02/set.
    const L = E.latencia_medida;
    if (!L || L.mediana_alta == null) return base;
    const lento = L.mediana_alta > 120;
    return base + `<br><span class="${lento ? "mac-velho" : "mac-fresco"}">Source delivery, measured this run:</span>` +
      ` high-impact prints land <b>${fmtAtraso(L.mediana_alta)}</b> after the scheduled time` +
      ` (median, n=${L.n_alta}; p90 ${fmtAtraso(L.p90_alta)} — a late stamp usually means a revision re-touched the record).` +
      (L.mediana_alta < 900 ? " The 15-minute clock above is slower than the source." : "");
  }

  /* ------------------------------------------------------------------ OVERVIEW */

  function painelBancos() {
    if (!M.bancos) return "";
    const bs = M.bancos.bancos;
    const ordem = Object.keys(bs).sort((a, b) =>
      ((bs[a].proxima ? diasAte(bs[a].proxima) : null) ?? 999) -
      ((bs[b].proxima ? diasAte(bs[b].proxima) : null) ?? 999));

    const linhas = ordem.map((m) => {
      const b = bs[m];
      const dias = b.proxima ? diasAte(b.proxima) : null;
      // null = a lista de reunioes acabou; nao e "hoje" nem "in null days" (revisao de 03/set)
      const quando = dias === null ? "no date published" : dias === 0 ? "today"
                   : dias === 1 ? "tomorrow" : `in ${dias} days`;
      const urgente = dias !== null && dias <= 7;
      const hora = b.hora_local
        ? `${b.hora_local} ${b.fuso.split("/")[1].replace("_", " ")}`
        : "no fixed release time";
      const emBrt = b.proxima_utc ? brt(b.proxima_utc) : null;
      const mov = b.ultima_mudanca_bp;
      return `<tr class="${urgente ? "mac-urgente" : ""}">
        <td class="mac-moeda">${FLAG[m] || ""} <strong>${m}</strong> <small>${esc(b.sigla)}</small></td>
        <td class="mac-taxa">${esc(b.taxa_texto)}</td>
        <td><small class="${mov > 0 ? "positive" : mov < 0 ? "negative" : "muted"}">
            ${mov > 0 ? "+" : ""}${mov} bp</small>
            <small class="muted"> · ${esc(b.ultima_mudanca)}</small></td>
        <td><strong>${quando}</strong><small class="muted"> · ${esc(b.proxima || "—")}</small></td>
        <td>${leanCel(m)}</td>
        <td><small>${esc(hora)}</small>${emBrt ? `<small class="muted"> · ${emBrt} BRT</small>` : ""}</td>
      </tr>`;
    }).join("");

    return `<section class="content-section mac-bloco">
      <div class="section-title"><div><h2>Central bank meetings</h2></div>
        <p>Current policy rate, when each one decides next, and the forward reading — what the
           released data, the speeches and the cycle say it will do. Times are local with the IANA
           zone — three daylight-saving switches fall inside this calendar.</p></div>
      <div class="table-wrap"><table class="mac-tabela">
        <thead><tr><th>Currency</th><th>Policy rate</th><th>Last change</th>
                   <th>Next decision</th><th>Reading for next move</th><th>Local time</th></tr></thead>
        <tbody>${linhas}</tbody></table></div>
      <p class="mac-frescor">${frescor()}</p>
      <p class="method-note">The rate and the dates are facts, checked against each central bank's own
        pages on 1 Sep 2026. What each one will <em>do</em> is a separate reading — it comes from the
        released data, never from a score.</p>
    </section>`;
  }

  /* ---------------------------------------------------------------- SENTIMENTO */

  // A leitura PARA FRENTE de uma moeda, vinda de sentimento.py. Quatro dimensoes, 25% cada:
  // dados, texto, ciclo, mercado. Dimensao nao conectada baixa o TETO — nunca vira zero.
  const ROT_DIR = { SOBE: "hike", MANTEM: "hold", CORTA: "cut" };
  const SETA_DIR = { SOBE: "&#9650;", MANTEM: "&mdash;", CORTA: "&#9660;" };
  const CLS_DIR = { SOBE: "positive", MANTEM: "muted", CORTA: "negative" };

  function sentDe(m) {
    return (M.sent && M.sent.moedas && M.sent.moedas[m]) || null;
  }

  function dimsChips(s) {
    const D = s.dimensoes || {};
    const rot = { dados: "data", texto: "speeches", ciclo: "cycle", geo: "geopolitics" };
    return `<span class="mac-dims">${["dados", "texto", "ciclo", "geo"].map((k) => {
      const v = D[k];
      if (!v) return `<span class="mac-dim off" title="not connected">${rot[k]} —</span>`;
      // geopolitica ligada mas sem pico: nao vota, e diz por que
      if (!v.direcao) return `<span class="mac-dim quiet" title="${esc(v.motivo || "")}">${rot[k]} <small>quiet</small></span>`;
      const ok = s.concordam && s.concordam[k];
      const det = k === "dados" ? `data push ${v.soma > 0 ? "+" : ""}${v.soma} over ${v.n} prints since ${v.desde}`
                : k === "texto" ? `${v.hawkish} hawkish / ${v.dovish} dovish markers in ${v.n} speech(es)`
                : k === "ciclo" ? v.nota
                : k === "geo" ? (v.motivo || "") : "";
      return `<span class="mac-dim ${ok ? "ok" : "no"}" title="${esc(det)}">${rot[k]} ${ok ? "&#10003;" : "&#10007;"}
        <small>${ROT_DIR[v.direcao] || ""}</small></span>`;
    }).join("")}</span>`;
  }

  // celula da tabela de bancos
  function leanCel(m) {
    const s = sentDe(m);
    if (!s) return `<small class="muted">reading not built yet</small>`;
    return `<span class="mac-lean-pill ${CLS_DIR[s.direcao]}">${SETA_DIR[s.direcao]} ${ROT_DIR[s.direcao]}
        <b>${s.conviccao_pct}%</b></span>
      <small class="muted"> of ${s.conviccao_teto_pct}% · ${s.dimensoes_ligadas} of ${s.dimensoes_total} dimensions</small>`;
  }

  // Os motivos X, Y e Z: os prints que mais pesaram na dimensao de dados, e a frase do
  // dirigente quando ha discurso ligado. O Eduardo pediu a conviccao "devido a x, y e z".
  function motivosPerna(m, s) {
    const D = s.dimensoes || {};
    const top = ((D.dados || {}).principais || []).slice(0, 3);
    const ROT = { MUITO_ACIMA: "well above", MUITO_ABAIXO: "well below", EM_LINHA: "in line" };
    const li = top.map((x) =>
      `<li><span class="muted mac-ref-td">${esc((x.quando_utc || "").slice(5, 10))}</span>
         ${esc(x.titulo)} <b class="${x.contribuicao > 0 ? "positive" : "negative"}">${esc(ROT[x.classe] || x.classe || "")}</b>
         <small class="muted">${x.contribuicao > 0 ? "+" : ""}${x.contribuicao}</small></li>`);
    // a fala mais recente desta moeda, se o feed dela estiver ligado
    const falas = (M.discursos && Array.isArray(M.discursos.itens)) ? M.discursos.itens : [];
    const fala = falas.find((f) => (f.moeda || "USD") === m && f.frases && f.frases.length);
    if (fala) {
      li.push(`<li><span class="muted mac-ref-td">${esc((fala.data || "").slice(5, 10))}</span>
        <b>${esc(fala.orador)}</b>: <em>“${esc(fala.frases[0].frase.slice(0, 150))}${fala.frases[0].frase.length > 150 ? "…" : ""}”</em></li>`);
    }
    if (!li.length) return `<div class="mac-perna-linha muted"><small>no print with a forecast in the window</small></div>`;
    return `<span class="mac-perna-papel" style="margin-top:10px">because</span><ul class="mac-motivos">${li.join("")}</ul>`;
  }

  // bloco dentro do cartao da perna
  function leanPerna(m) {
    const s = sentDe(m);
    if (!s) return `<div class="mac-perna-linha muted"><small>forward reading not built yet</small></div>`;
    return `<div class="mac-perna-lean">
      <span class="mac-perna-papel">Reading for the next move</span>
      <div class="mac-lean-pill big ${CLS_DIR[s.direcao]}">${SETA_DIR[s.direcao]} ${ROT_DIR[s.direcao]} <b>${s.conviccao_pct}%</b>
        <small>ceiling ${s.conviccao_teto_pct}% — ${s.dimensoes_ligadas} of ${s.dimensoes_total} dimensions voting</small>
        <small class="mac-score" title="continuous score, −1 to +1: each dimension enters with its magnitude, up to ±0.25">score <b>${(s.score > 0 ? "+" : "") + Number(s.score || 0).toFixed(2)}</b></small></div>
      ${dimsChips(s)}
      ${motivosPerna(m, s)}
    </div>`;
  }

  /* --------------------------------------------------------------- MATRIZ DOS PARES */

  /* A TELA DE TRABALHO DOS PARES.
   *
   * Auditoria do Eduardo (02/set): "hoje o usuario escolhe um par na tabela de baixo, mas o
   * resultado aparece no painel de cima — isso obriga a ficar subindo e descendo a pagina".
   * Ele elegeu isto como a maior melhoria de praticidade, e esta certo.
   *
   * Vira duas colunas: lista dos 28 a esquerda, detalhe FIXO a direita. No celular a lista
   * ocupa a tela e o detalhe vem abaixo, porque duas colunas em 375px nao servem a ninguem.
   *
   * O QUE A TELA MOSTRA HOJE
   *   Nao ha leitura de direcao ainda — ela depende da fonte do resultado ao vivo. O que ha e
   *   FATO: onde cada banco central foi da ultima vez, quando decide de novo, e onde esta a
   *   taxa. Isso ja separa os pares em fases diferentes dos que estao do mesmo lado.
   *   Hierarquia pedida por ele: primeiro o par, depois a leitura, depois a qualidade do dado.
   *   O resto fica em "what is still missing", sem competir com o principal.
   */
  const PARES = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCAD", "USDCHF",
    "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCAD", "EURCHF",
    "GBPJPY", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF",
    "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF",
    "NZDJPY", "NZDCAD", "NZDCHF", "CADJPY", "CADCHF", "CHFJPY",
  ];

  const cicloDe = (m) => {
    const b = M.bancos && M.bancos.bancos[m];
    return !b ? 0 : b.ultima_mudanca_bp > 0 ? 1 : b.ultima_mudanca_bp < 0 ? -1 : 0;
  };
  const ROT_CICLO = { "1": "last move up", "-1": "last move down", "0": "unchanged" };

  function dadosPar(par) {
    const b = par.slice(0, 3), q = par.slice(3);
    const cb = cicloDe(b), cq = cicloDe(q);
    const bs = M.bancos ? M.bancos.bancos : {};
    // null quando a lista de reunioes de uma perna acabou — Math.min(null, 13) daria 0 e o
    // par viraria "decides today" (revisao de 03/set, reproduzido para dezembro/2026)
    const dd = (x) => (x && x.proxima) ? diasAte(x.proxima) : null;
    const db = dd(bs[b]), dq = dd(bs[q]);
    const dias = (db === null && dq === null) ? null
               : Math.min(db === null ? 999 : db, dq === null ? 999 : dq);
    const s = (M.sent && Array.isArray(M.sent.pares))
      ? M.sent.pares.find((p) => p.par === par) || null : null;
    const tese = !!(s && (s.sinal === "BULL" || s.sinal === "BEAR"));
    return { par, b, q, cb, cq, diverge: cb !== cq, dias, s, tese,
             conv: s ? (s.conviccao_pct || 0) : 0 };
  }

  // XAUUSD, NQ e ES entram na mesma lista, lidos pela perna do USD. Nao sao pares de duas
  // moedas — o cartao deles mostra o canal e o que esta (ou nao) medido em casa.
  const INSTR = ["XAUUSD", "NQ", "ES"];
  function dadosInstr(sym) {
    const I = (M.sent && Array.isArray(M.sent.instrumentos))
      ? M.sent.instrumentos.find((x) => x.simbolo === sym) : null;
    const bs = M.bancos ? M.bancos.bancos : {};
    const dias = bs.USD && bs.USD.proxima ? diasAte(bs.USD.proxima) : null;
    const tese = !!(I && (I.sinal === "BULL" || I.sinal === "BEAR"));
    return { par: sym, b: "USD", q: "", rotulo: sym === "XAUUSD" ? "XAU<em>/</em>USD" : sym,
             instr: true, info: I, s: I ? { sinal: I.sinal } : null, tese,
             conv: I ? (I.conviccao_pct || 0) : 0, dias, diverge: false, cb: 0, cq: 0 };
  }
  function instrumentosLista() {
    return (M.sent && Array.isArray(M.sent.instrumentos)) ? INSTR.map(dadosInstr) : [];
  }

  const ROT_SINAL = { BULL: "BULL", BEAR: "BEAR", SEM_TESE: "no edge", "NAO NEGOCIA": "no trade", SEM_DADO: "no data" };
  const CLS_SINAL = { BULL: "v-bull", BEAR: "v-bear", SEM_TESE: "v-nao", "NAO NEGOCIA": "v-nao", SEM_DADO: "v-nao" };

  function itemLista(d) {
    const sel = d.par === M.parSel ? " mac-item-sel" : "";
    const tag = d.s
      ? `<span class="mac-item-tag ${CLS_SINAL[d.s.sinal] || "v-nao"}">${ROT_SINAL[d.s.sinal] || esc(d.s.sinal)}${
          d.tese ? ` <b>${d.conv}%</b>` : ""}</span>`
      : `<span class="mac-item-tag ${d.diverge ? "e-div" : "e-igual"}">${d.diverge ? "divergence" : "same side"}</span>`;
    return `<button type="button" class="mac-item${sel}${d.instr ? " mac-item-instr" : ""}" data-mac-par="${d.par}">
      <span class="mac-item-par">${d.instr ? d.rotulo : d.b + "<em>/</em>" + d.q}</span>
      ${tag}
      <span class="mac-item-dias">${d.dias === null ? "no date" : d.dias === 0 ? "decides today" : d.dias + "d"}</span>
    </button>`;
  }

  function pernaCard(m, ciclo, papel) {
    const b = M.bancos && M.bancos.bancos[m];
    if (!b) {
      return `<div class="mac-perna"><span class="mac-perna-papel">${papel}</span>
        <strong class="mac-perna-nome">${m}</strong>
        <div class="mac-perna-linha muted">no data</div></div>`;
    }
    const dias = b.proxima ? diasAte(b.proxima) : null;
    const quando = dias === null ? "no date published" : dias === 0 ? "today"
                 : dias === 1 ? "tomorrow" : "in " + dias + " days";
    const hora = b.hora_local
      ? esc(b.hora_local + " " + b.fuso.split("/")[1].replace("_", " "))
      : "no fixed release time";
    return `<div class="mac-perna">
      <span class="mac-perna-papel">${papel}</span>
      <strong class="mac-perna-nome">${FLAG[m] || ""} ${m} <small>${esc(b.sigla)}</small></strong>
      <div class="mac-perna-taxa">${esc(b.taxa_texto)}</div>
      ${leanPerna(m)}
      <div class="mac-perna-linha ${ciclo > 0 ? "positive" : ciclo < 0 ? "negative" : "muted"}">
        ${ciclo > 0 ? "&#9650;" : ciclo < 0 ? "&#9660;" : "&mdash;"} ${ROT_CICLO[String(ciclo)]}
        <small class="muted">&middot; ${esc(b.ultima_mudanca)}</small></div>
      <div class="mac-perna-linha muted">next decision <strong>${quando}</strong>
        <small>&middot; ${esc(b.proxima || "—")}</small></div>
      <div class="mac-perna-linha muted"><small>${hora}</small></div>
      ${ultimosPrintsEUA(m)}
      ${geoPerna(m)}
    </div>`;
  }

  // A perna do dolar ganha a ultima leitura do BLS, porque o USD e uma das pernas na maioria
  // do book — e e a mesma taxa que ouro, NQ e ES respondem.
  function ultimosPrintsEUA(m) {
    if (m !== "USD" || !M.eua || !M.eua.indicadores) return "";
    const I = M.eua.indicadores;
    const cpi = I.CUSR0000SA0, core = I.CUSR0000SA0L1E, nfp = I.CES0000000001, u = I.LNS14000000;
    const p = (x, d = 2) => (x === null || x === undefined) ? "—" : (x > 0 ? "+" : "") + x.toFixed(d);
    const partes = [];
    if (cpi && cpi.aa != null) partes.push(`CPI <b>${p(cpi.aa)}%</b> y/y`);
    if (core && core.aa != null) partes.push(`core <b>${p(core.aa)}%</b>`);
    if (nfp && nfp.mm != null) partes.push(`NFP <b>${p(nfp.mm, 0)}k</b> m/m`);
    if (u && u.valor != null) partes.push(`unemployment <b>${u.valor.toFixed(1)}%</b>`);
    if (!partes.length) return "";
    const ref = cpi && cpi.referencia ? cpi.referencia : "";
    return `<div class="mac-perna-linha mac-perna-eua">latest prints <small class="muted">(${esc(ref)})</small><br>${partes.join(" &middot; ")}</div>`;
  }

  function detalhePar(par) {
    if (!par) {
      return `<div class="mac-vazio"><strong>Pick a pair on the left.</strong>
        <p>Each pair is two currencies. This panel reads both legs, because the reason for an
           entry usually sits on one side, not on the pair.</p></div>`;
    }
    const d = INSTR.includes(par) ? dadosInstr(par) : dadosPar(par);
    const g = M.bancos && M.bancos.gerado_em;
    const min = g ? Math.round((Date.now() - new Date(g).getTime()) / 60000) : null;
    const velho = min !== null && min > 45;
    const idade = min === null ? "freshness unknown"
      : velho ? "data " + (min < 90 ? min + " min" : Math.round(min / 60) + "h") + " old"
      : "data current";
    if (d.instr) return detalheInstr(d, idade, velho);

    const s = d.s;
    const pill = s
      ? `<span class="mac-det-leitura ${CLS_SINAL[s.sinal] || "v-nao"}">${ROT_SINAL[s.sinal] || esc(s.sinal)}${
          d.tese ? ` &middot; ${d.conv}%` : ""}</span>`
      : `<span class="mac-det-leitura ${d.diverge ? "e-div" : "e-igual"}">${d.diverge ? "CYCLE DIVERGENCE" : "SAME SIDE"}</span>`;

    const fs = (x) => (x === null || x === undefined) ? "?" : (x > 0 ? "+" : "") + Number(x).toFixed(2);
    let nota;
    if (s && d.tese) {
      const lb = s.leitura_base || {}, lq = s.leitura_cotada || {};
      nota = `<b>${s.sinal === "BULL" ? "Long" : "Short"} ${d.b}/${d.q}</b> reads from the two legs: ${d.b} leaning to ${ROT_DIR[lb.direcao] || "?"} (score ${fs(lb.score)}) against ${d.q} leaning to ${ROT_DIR[lq.direcao] || "?"} (score ${fs(lq.score)}) — edge ${fs(s.diff)} of a possible 2.00. ${s.perna_motivo && s.perna_motivo !== "ambas"
          ? `The reason sits on <b>${s.perna_motivo}</b>.` : "Both legs carry the reason."}
        ${s.mesma_aposta && s.mesma_aposta.length
          ? `<span class="mac-mesma">Same bet as ${s.mesma_aposta.map((p) => p.slice(0, 3) + "/" + p.slice(3)).join(", ")} &mdash; holding two does not diversify, it doubles.</span>` : ""}`;
    } else if (s) {
      const lb = s.leitura_base || {}, lq = s.leitura_cotada || {};
      nota = `The two legs score the same (${d.b} ${fs(lb.score)}, ${d.q} ${fs(lq.score)}) — no edge between them on this axis.`;
    } else {
      nota = d.diverge
        ? "The two central banks last moved in opposite directions. That is the necessary condition for a fundamental thesis &mdash; not a sufficient one."
        : "Both central banks last moved the same way. No divergence to trade on this axis.";
    }

    return `<div class="mac-det-topo">
        <h2 class="mac-det-par">${d.b}<em>/</em>${d.q}</h2>
        ${pill}
        <span class="mac-det-dado ${velho ? "e-velho" : "e-fresco"}">${idade}</span>
      </div>

      <p class="mac-det-nota">${nota}</p>

      <div class="mac-pernas">${pernaCard(d.b, d.cb, "base")}${pernaCard(d.q, d.cq, "quote")}</div>

      <details class="mac-det-mais">
        <summary>How this reading is built, and what is still missing</summary>
        <div class="mac-det-mais-corpo">
          <p>Four dimensions, 25% each, none of them a yield: <b>data</b> (surprises since the bank last decided, weighted by
             family and impact, half-life 21 days), <b>speeches</b> (hawkish/dovish markers in what the
             bank's people said), <b>cycle</b> (the last move, if under six months old) and
             <b>geopolitics</b> (news intensity from GDELT: an energy spike is an inflation push, a conflict spike a growth risk; quiet weeks do not vote).
             Conviction is the share of voting dimensions that agree &mdash; a missing or quiet dimension lowers the ceiling, it never counts as zero.</p>
          <p>The pair: each currency gets a score from −1 to +1 (each voting dimension adds +0.25 for hike, −0.25 for cut, 0 for hold).
             The pair reads the difference between its two legs &mdash; the sign gives the direction, the size gives the confidence
             (a 0.50 edge is 25% of the maximum 2.00). Every pair gets a reading; "no edge" only when the two legs tie exactly.</p>
          <p>Still missing: speeches are wired for the Fed, ECB, BoE, BoJ and BoC only (RBA and RBNZ block automation, the SNB has no feed),
             and the geopolitics rule counts by the owner's decision but has not been measured yet.</p>
          <p>Which leg carries the weight matters. On 2 Sep the GBPNZD move was <b>82% the kiwi</b>;
             the same day EURJPY was <b>90% the yen</b>. When the reason sits on one leg, every
             pair sharing that leg is the same bet.</p>
          <p>This is a reading of the fundamental side, not a signal: the earlier FUND was closed as
             an entry rule after 15 null tests. The entry is yours.</p>
        </div>
      </details>`;
  }

  // As correlacoes MEDIDAS entre o juro americano e o instrumento, quando sentimento.py as
  // traz (correlacao_juros.py). Contemporanea e preditiva lado a lado, com n — porque a
  // diferenca entre as duas e a licao inteira: o juro descreve o mes, nao antecipa a vela.
  function correlacoesInstr(I) {
    const C = I.correlacoes;
    if (!C || !C.series) return "";
    const f = (x) => (x === null || x === undefined) ? "—" : (x > 0 ? "+" : "") + Number(x).toFixed(2);
    const linhas = Object.keys(C.series).map((k) => {
      const s = C.series[k];
      return `<tr><td>${esc(s.rotulo || k)}</td>
        <td class="mac-num-td">${f(s.contemp_1d)}</td>
        <td class="mac-num-td">${f(s.contemp_20d)} <small class="muted">n=${s.n_20d || "?"}</small></td>
        <td class="mac-num-td"><b>${f(s.contemp_60d)}</b> <small class="muted">n=${s.n_60d || "?"}</small></td>
        <td class="mac-num-td muted">${f(s.pred_1d)}</td>
        <td class="mac-num-td muted">${f(s.pred_5d)}</td></tr>`;
    }).join("");
    return `<span class="mac-perna-papel" style="margin-top:12px">measured correlation with US rates — 5 years, non-overlapping blocks</span>
      <div class="mac-eua-tabela"><table class="mac-tabela mac-corr">
        <thead><tr><th>rate</th><th class="mac-num-th">same day</th><th class="mac-num-th">same 20 d</th>
          <th class="mac-num-th">same 60 d</th>
          <th class="mac-num-th">next day</th><th class="mac-num-th">next 5 d</th></tr></thead>
        <tbody>${linhas}</tbody></table></div>
      <small class="muted">${esc(C.nota || "")}</small>`;
  }

  // O detalhe de XAUUSD / NQ / ES: uma perna so, o canal, e o que esta medido em casa.
  function detalheInstr(d, idade, velho) {
    const I = d.info;
    if (!I) {
      return `<div class="mac-vazio"><strong>${d.par}</strong><p>The USD reading is not built yet.</p></div>`;
    }
    const u = I.leitura_usd || {};
    const comp = I.score_componentes || {};
    return `<div class="mac-det-topo">
        <h2 class="mac-det-par">${d.rotulo}</h2>
        <span class="mac-det-leitura ${CLS_SINAL[I.sinal] || "v-nao"}">${ROT_SINAL[I.sinal] || esc(I.sinal)}${
          d.tese ? ` &middot; ${d.conv}%` : ""}</span>
        <span class="mac-det-dado ${velho ? "e-velho" : "e-fresco"}">${idade}</span>
      </div>
      <p class="mac-det-nota">${esc(I.nome)} is read from <b>two legs</b>: the US dollar's rate reading, inverted
        (USD leaning to ${ROT_DIR[u.direcao] || "?"}, score ${(u.score > 0 ? "+" : "") + Number(u.score || 0).toFixed(2)} → ${(comp.usd_invertido > 0 ? "+" : "") + Number(comp.usd_invertido || 0).toFixed(2)} for ${esc(I.nome)}),
        plus <b>geopolitics</b> (${esc((I.geo || {}).estado || "not connected")} → ${(comp.geopolitica > 0 ? "+" : "") + Number(comp.geopolitica || 0).toFixed(2)}).
        Score ${(I.score > 0 ? "+" : "") + Number(I.score || 0).toFixed(2)} of a possible ${Number(comp.maximo || 1.25).toFixed(2)} → <b>${d.conv}%</b>.
        ${I.sinal === "SEM_TESE" ? "The two legs cancel out exactly today." : ""}</p>
      <div class="mac-pernas">
        ${pernaCard("USD", cicloDe("USD"), "the leg that drives it")}
        <div class="mac-perna">
          <span class="mac-perna-papel">channel</span>
          <div class="mac-perna-linha">${esc(I.canal)}</div>
          <span class="mac-perna-papel" style="margin-top:12px">measured in-house</span>
          <div class="mac-perna-linha ${/NOT measured/.test(I.medido) ? "muted" : ""}">${esc(I.medido)}</div>
          ${correlacoesInstr(I)}
        </div>
      </div>
      <p class="mac-eua-nota">${esc(I.aviso)}</p>`;
  }

  const FILTROS = [
    { k: "todos", r: "All", f: () => true },
    { k: "tese", r: "With a thesis", f: (d) => d.tese },
    { k: "sem", r: "No trade", f: (d) => d.s && !d.tese },
    { k: "perto", r: "Deciding soon", f: (d) => d.dias !== null && d.dias <= 7 },
  ];

  function matrizPares() {
    if (!M.bancos) return "";
    const bs = M.bancos.bancos;
    const sobe = Object.keys(bs).filter((m) => cicloDe(m) > 0);
    const corta = Object.keys(bs).filter((m) => cicloDe(m) < 0);

    const filtro = FILTROS.find((x) => x.k === M.filtro) || FILTROS[0];
    const instr = instrumentosLista();
    let lista = PARES.map(dadosPar).concat(instr).filter(filtro.f);
    if (M.moedaSel) lista = lista.filter((d) => d.b === M.moedaSel || d.q === M.moedaSel);
    // com tese primeiro, por conviccao; depois os demais por proximidade da decisao
    lista.sort((a, b) => (b.tese - a.tese) || (b.conv - a.conv) || (b.diverge - a.diverge) ||
                         ((a.dias ?? 999) - (b.dias ?? 999)) || a.par.localeCompare(b.par));

    const S = M.sent && M.sent.moedas;
    const lean = (dir) => S ? Object.keys(S).filter((m) => S[m].direcao === dir)
      .map((m) => `${FLAG[m] || ""} ${m} <small>${S[m].conviccao_pct}%</small>`).join("&nbsp; ") : "";

    const chips = FILTROS.map((x) =>
      `<button type="button" class="mac-chip${x.k === filtro.k ? " on" : ""}" data-mac-filtro="${x.k}">${x.r}</button>`
    ).join("") + `<span class="mac-sep"></span>` + Object.keys(bs).map((m) =>
      `<button type="button" class="mac-chip mac-chip-moeda${m === M.moedaSel ? " on" : ""}" data-mac-moeda="${m}">${m}</button>`
    ).join("");

    return `<section class="content-section mac-bloco mac-tela">
      <div class="section-title"><div><h2>Pairs</h2></div>
        <p>Each pair read leg by leg: what each central bank is leaning to do next, and whether
           the two legs diverge. A reading of the fundamental side &mdash; the entry is yours.</p></div>

      <div class="mac-placar${S ? " mac-placar-3" : ""}">
        ${S ? `<div><span>Leaning to hike</span><strong>${lean("SOBE") || "&mdash;"}</strong></div>
               <div><span>On hold</span><strong>${lean("MANTEM") || "&mdash;"}</strong></div>
               <div><span>Leaning to cut</span><strong>${lean("CORTA") || "&mdash;"}</strong></div>`
            : `<div><span>Last move up</span><strong>${sobe.map((m) => (FLAG[m] || "") + " " + m).join("&nbsp; ")}</strong></div>
               <div><span>Last move down</span><strong>${corta.map((m) => (FLAG[m] || "") + " " + m).join("&nbsp; ")}</strong></div>`}
      </div>

      <div class="mac-chips">${chips}</div>
      <p class="mac-conta">${lista.length} of ${PARES.length + instr.length}${instr.length ? ` — ${PARES.length} pairs + ${instr.length} USD-driven instruments (gold, NQ, ES)` : " pairs"}</p>

      <div class="mac-duas">
        <div class="mac-lista">${lista.length
          ? lista.map(itemLista).join("")
          : `<div class="mac-vazio"><strong>No pair matches this filter.</strong></div>`}</div>
        <aside class="mac-detalhe">${detalhePar(M.parSel)}</aside>
      </div>
    </section>`;
  }

  // Delegacao unica no documento: sobrevive a qualquer redesenho, sem religar ouvinte a cada vez.
  document.addEventListener("click", function (e) {
    const alvoPar = e.target.closest ? e.target.closest("[data-mac-par]") : null;
    const alvoFil = e.target.closest ? e.target.closest("[data-mac-filtro]") : null;
    const alvoMoe = e.target.closest ? e.target.closest("[data-mac-moeda]") : null;
    if (!alvoPar && !alvoFil && !alvoMoe) return;
    if (alvoPar) M.parSel = alvoPar.dataset.macPar;
    if (alvoFil) M.filtro = alvoFil.dataset.macFiltro;
    if (alvoMoe) M.moedaSel = (M.moedaSel === alvoMoe.dataset.macMoeda) ? null : alvoMoe.dataset.macMoeda;
    const painel = document.querySelector('[data-panel="pairs"]');
    if (painel) {
      try { painel.innerHTML = matrizPares(); }
      catch (err) { console.warn("[macro] matrizPares falhou no clique e foi contida:", err.message); }
    }
    if (alvoPar && window.innerWidth < 900) {
      const det = document.querySelector(".mac-detalhe");
      if (det) det.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, true);



  /* ------------------------------------------------------------ ESTADOS UNIDOS */

  // O bloco dos EUA na Overview. Direto do BLS e do Fed, sem intermediario.
  // Dois relogios separados de proposito: o mes que o dado DESCREVE (referencia, universal —
  // a Bloomberg tem a mesma) e o tempo do release ate aqui (entrega, ainda nao medido).
  function painelEUA() {
    const U = M.eua;
    if (!U || !U.indicadores) return "";
    const I = U.indicadores;
    const ORDEM = ["CUSR0000SA0", "CUSR0000SA0L1E", "CES0000000001", "LNS14000000",
                   "CES0500000003", "LNS11300000"];
    const sinal = (x, d) => (x === null || x === undefined) ? "—"
      : (x > 0 ? "+" : "") + Number(x).toFixed(d);
    const varia = (x, un) => {
      if (x === null || x === undefined) return "—";
      if (un === "%") return sinal(x, 2) + "%";
      if (un === "pp") return sinal(x, 2) + " pp";
      if (un === "mil") return sinal(x, 0) + "k";
      return sinal(x, 2);
    };
    const nivel = (r) => {
      if (r.valor === null || r.valor === undefined) return "—";
      if (r.unidade === "mil") return Number(r.valor).toLocaleString("en-US", { maximumFractionDigits: 0 }) + "k";
      if (r.unidade === "pp") return Number(r.valor).toFixed(1) + "%";
      return Number(r.valor).toLocaleString("en-US", { maximumFractionDigits: 3 });
    };
    const linhas = ORDEM.filter((k) => I[k]).map((k) => {
      const r = I[k];
      return `<tr>
        <td>${esc(r.nome)}${r.preliminar
          ? ' <span class="mac-prelim" title="the BLS still revises the next two prints">prelim</span>' : ""}</td>
        <td class="mac-num-td">${nivel(r)}</td>
        <td class="mac-num-td">${varia(r.mm, r.unidade)}</td>
        <td class="mac-num-td">${varia(r.aa, r.unidade)}</td>
        <td class="muted mac-ref-td">${esc(r.referencia || "")}</td></tr>`;
    }).join("");

    const f = U.fomc && U.fomc.proxima;
    const b = M.bancos && M.bancos.bancos && M.bancos.bancos.USD;
    let fomc = "";
    if (f && f.data) {
      const dias = diasAte(f.data);
      fomc = `<div class="mac-eua-fomc">
        <span class="mac-perna-papel">Next FOMC decision</span>
        <div class="mac-eua-dias">${dias <= 0 ? "today" : dias} <small>${dias <= 0 ? "" : dias === 1 ? "day" : "days"}</small></div>
        <div class="mac-perna-linha">${esc(f.rotulo)} &middot; ${esc(f.data)}</div>
        ${f.com_projecoes ? '<span class="mac-dot" title="the meeting that publishes the committee\'s own rate path — the one that moves price most">with projections · dot plot</span>' : ""}
        ${b ? `<div class="mac-perna-linha muted mac-eua-taxa">Fed funds <b>${esc(b.taxa_texto)}</b>
          <small>&middot; last move ${esc(b.ultima_mudanca || "")}${b.ultima_mudanca_bp ? " (" + (b.ultima_mudanca_bp > 0 ? "+" : "") + b.ultima_mudanca_bp + " bp)" : ""}</small></div>` : ""}
      </div>`;
    }

    const refs = Object.values(I).map((r) => r.referencia).filter(Boolean).sort();
    const ref = refs.length ? refs[refs.length - 1] : null;
    const atrasoRef = U.defasagem_referencia_meses;
    const L = M.eventos && M.eventos.latencia_medida;
    const entrega = (L && L.mediana_alta != null)
      ? `release → calendar source, measured per event: high-impact prints ${fmtAtraso(L.mediana_alta)} (median) — see each card; release → BLS API: not timed yet, needs the registered key`
      : "not measured yet";

    const fed = ((U.fed && U.fed.ultimos) || []).slice(0, 3).map((x) =>
      `<li><span class="muted">${esc((x.publicado || "").slice(0, 16))}</span> ${
        x.link ? `<a href="${esc(x.link)}" target="_blank" rel="noopener">${esc(x.titulo || "")}</a>`
               : esc(x.titulo || "")}</li>`).join("");

    return `<section class="content-section mac-bloco mac-eua">
      <div class="section-title"><div><h2>United States</h2></div>
        <p>One leg of most pairs, and the rate that gold, NQ and ES answer to. Read straight from
           the BLS and the Fed — no intermediary.</p></div>
      <div class="mac-eua-grid">
        ${fomc}
        <div class="mac-eua-tabela">
          <table class="mac-tabela">
            <thead><tr><th>indicator</th><th class="mac-num-th">latest</th><th class="mac-num-th">m/m</th>
              <th class="mac-num-th">y/y</th><th>month</th></tr></thead>
            <tbody>${linhas}</tbody>
          </table>
        </div>
      </div>
      <p class="mac-eua-nota">${ref ? `The newest prints describe <b>${esc(ref)}</b>${
          atrasoRef != null ? ` — ${atrasoRef} month${atrasoRef === 1 ? "" : "s"} back` : ""}. That is the month that
        ended, not a delivery delay; every terminal has the same lag.` : ""}
        Delivery (release → here): <b>${entrega}</b>.</p>
      ${falasDoFed()}
      ${fed ? `<details class="mac-det-mais mac-eua-fed"><summary>Latest from the Fed</summary>
        <ul>${fed}</ul></details>` : ""}
    </section>`;
  }

  // O que os membros do Fed DISSERAM — a camada de texto. O calendario de numeros marcava
  // "Fed's Waller speech" com actual=None no minuto em que o texto dizia "raise the policy
  // rate". Aqui entra a frase. E extracao por expressao, rotulada como tal, nao leitura.
  function falasDoFed() {
    const D = M.discursos;
    if (!D || !Array.isArray(D.itens) || !D.itens.length) return "";
    // no bloco dos EUA so o Fed; as outras moedas aparecem no cartao da perna delas
    const itens = D.itens.filter((s) => (s.moeda || "USD") === "USD").slice(0, 4).map((s) => {
      const f = (s.frases && s.frases[0] && s.frases[0].frase) || "";
      const lean = s.inclinacao_por_contagem || "none";
      return `<li class="mac-fala">
        <div class="mac-fala-topo"><span class="muted mac-ref-td">${esc(s.data)}</span>
          <strong>${esc(s.orador)}</strong>
          <span class="mac-lean mac-lean-${esc(lean)}">${
            lean === "none" ? "no policy markers" : esc(lean) + " by count"}
            <small>${s.marcadores_hawkish}h / ${s.marcadores_dovish}d</small></span>
          ${s.link ? `<a class="mac-fala-link" href="${esc(s.link)}" target="_blank" rel="noopener">${esc((s.titulo || "").slice(0, 70))}</a>` : ""}</div>
        ${f ? `<blockquote class="mac-fala-frase">“${esc(f.slice(0, 260))}${f.length > 260 ? "…" : ""}”</blockquote>` : ""}
      </li>`;
    }).join("");
    return `<div class="mac-falas">
      <div class="mac-falas-titulo"><span class="mac-perna-papel">What Fed speakers said</span>
        <small class="muted">policy sentences pulled by expression match — a pointer to what to read, not a reading</small></div>
      <ul>${itens}</ul></div>`;
  }

  /* ------------------------------------------------------------- GEOPOLITICA */

  // A camada de CONTEXTO: intensidade do noticiario por moeda (GDELT), com a implicacao por
  // REGRA DECLARADA ao lado. Nao entra na conviccao — filtro novo passa por medicao antes de
  // pontuar (lei da casa; o DXY foi reprovado nas 88 operacoes por ter sido assumido).
  function zPill(v, rotulo) {
    if (!v || v.z === null || v.z === undefined) return `<span class="mac-geo-pill off">${rotulo} —</span>`;
    const cls = v.z >= 2 ? "alto" : v.z >= 1 ? "medio" : v.z <= -1 ? "baixo" : "";
    return `<span class="mac-geo-pill ${cls}" title="3-day article volume vs the 14-day daily mean: ratio ${v.razao ?? "?"}×, z ${v.z}">${rotulo} <b>z ${v.z > 0 ? "+" : ""}${v.z}</b> <small>${v.razao ?? "?"}×</small></span>`;
  }

  function manchetesHtml(lista, n) {
    return (lista || []).slice(0, n).map((m) =>
      `<li><a href="${esc(m.url || "#")}" target="_blank" rel="noopener">${esc(m.titulo || "")}</a>
         <small class="muted">${esc(m.fonte || "")}${m.quando ? " · " + esc(String(m.quando).slice(0, 8)) : ""}</small></li>`).join("");
  }

  function painelGeo() {
    const G = M.geo;
    if (!G || !G.moedas) return "";
    const W = G.mundo || {};
    const cards = Object.keys(FLAG).filter((m) => G.moedas[m]).map((m) => {
      const b = G.moedas[m];
      const conf = (b.temas && b.temas.conflito) || {};
      const ener = (b.temas && b.temas.energia) || {};
      const imp = b.implicacao || {};
      return `<div class="mac-geo-card">
        <div class="mac-geo-topo"><strong>${FLAG[m] || ""} ${m}</strong>
          ${zPill(conf.volume, "conflict")} ${zPill(ener.volume, "energy")}
          ${b.tom !== null && b.tom !== undefined ? `<small class="muted" title="mean GDELT tone over 7 days">tone ${b.tom > 0 ? "+" : ""}${b.tom}</small>` : ""}</div>
        ${imp.fx || imp.juro ? `<div class="mac-geo-imp">${imp.fx ? `<span>${esc(imp.fx)}</span>` : ""}${imp.juro ? `<span>${esc(imp.juro)}</span>` : ""}</div>` : ""}
        <ul class="mac-geo-lista">${manchetesHtml(conf.manchetes, 2)}${manchetesHtml(ener.manchetes, 1)}</ul>
      </div>`;
    }).join("");

    return `<section class="content-section mac-bloco mac-geo">
      <div class="section-title"><div><h2>Geopolitics</h2></div>
        <p>News intensity by currency: articles in the last 3 days against the 14-day daily mean,
           from GDELT. The implication next to each card is a declared rule — it does not count
           toward the conviction until it is measured.</p></div>
      <div class="mac-geo-mundo">
        <span class="mac-perna-papel">World backdrop</span>
        ${zPill((W.conflito || {}).volume, "conflict")} ${zPill((W.energia || {}).volume, "energy")}
        <ul class="mac-geo-lista">${manchetesHtml((W.conflito || {}).manchetes, 2)}${manchetesHtml((W.energia || {}).manchetes, 1)}</ul>
      </div>
      <div class="mac-geo-grid">${cards}</div>
      <p class="mac-eua-nota">Rule, not measurement: a conflict spike tends to send flow to USD, CHF and JPY and out of
        AUD, NZD and CAD; an energy spike is an inflation push for importers. The hypothesis to test before
        it ever scores: does a conflict z ≥ 2 change the 20-day return of the risk currencies?</p>
    </section>`;
  }

  // linha de contexto no cartao da perna
  function geoPerna(m) {
    const G = M.geo && M.geo.moedas && M.geo.moedas[m];
    if (!G) return "";
    const conf = ((G.temas || {}).conflito || {}).volume;
    const ener = ((G.temas || {}).energia || {}).volume;
    const imp = G.implicacao || {};
    return `<div class="mac-perna-linha mac-perna-geo"><span class="mac-perna-papel">geopolitics</span>
      ${zPill(conf, "conflict")} ${zPill(ener, "energy")}
      ${imp.fx || imp.juro ? `<small class="muted">${esc(imp.fx || imp.juro)}</small>` : `<small class="muted">no spike this week</small>`}</div>`;
  }

  /* ------------------------------------------------------------------ CALENDARIO */

  // O DIA e em BRT — a lei do Eduardo: as horas dele sao BRT. A grade agrupava por dia UTC e
  // mostrava o Trade Balance australiano das 01:30 UTC de 03/09 dentro do dia 03 com a hora
  // "02/09 22:30 BRT" ao lado. Mesma classe do erro de relogio que ja custou caro duas vezes.
  function diaBrt(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    return new Date(d.getTime() + BRT * 3600e3).toISOString().slice(0, 10);
  }
  function hojeBrt() { return diaBrt(new Date().toISOString()); }

  // O filtro por moeda vive AQUI, num lugar so: a grade, a contagem "+N" e o painel do dia
  // passam todos por esta funcao, entao nao ha como um deles esquecer o filtro.
  function eventosDoDia(iso) {
    if (!M.eventos) return [];
    return M.eventos.eventos.filter((e) => diaBrt(e.quando_utc) === iso &&
      (!M.moedaCal || e.moeda === M.moedaCal));
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

  // Atraso de entrega em unidade legivel. "+16641 s" nao diz nada; "+4.6 h" diz.
  function fmtAtraso(s) {
    const n = Number(s);
    if (isNaN(n)) return "";
    if (n < 120) return Math.round(n) + " s";
    if (n < 7200) return Math.round(n / 60) + " min";
    return (Math.round(n / 360) / 10) + " h";
  }

  // Numero com a unidade da fonte. Nulo continua "—": 0.0 e um resultado, nao uma ausencia.
  function fmtN(v, un) {
    if (v === null || v === undefined || v === "") return "—";
    const n = Number(v);
    if (isNaN(n)) return esc(v);
    const s = Math.abs(n) >= 1000 ? n.toLocaleString("en-US", { maximumFractionDigits: 1 })
            : String(Math.round(n * 1000) / 1000);
    if (!un) return s;
    return /^(%|K|M|B|pp)$/.test(un) ? s + esc(un) : s + " " + esc(un);
  }

  function fichaEvento(e) {
    const cen = (e.cenarios || []).map((c) =>
      `<li><span>${esc(c.caso)}</span><strong>${esc(c.empurra)}</strong></li>`).join("");
    const saiu = e.resultado !== null && e.resultado !== undefined && e.resultado !== "";
    const temPrev = e.previsao !== null && e.previsao !== undefined && e.previsao !== "";

    // quanto o numero levou do horario agendado ate a fonte — medido, por evento
    const atraso = (saiu && e.atraso_s !== null && e.atraso_s !== undefined)
      ? `<span class="mac-atraso${e.atraso_s > 300 ? " mac-atraso-lento" : ""}"
           title="time from the scheduled release to the value landing in the source — a late stamp usually means a later revision touched the record, not a late first print">landed +${fmtAtraso(e.atraso_s)}</span>`
      : "";
    // diferenca de TAXA (juro, desemprego) e em pontos percentuais, nao em "%"
    const unSurp = (e.unidade === "%" && (e.familia === "decisao" || e.familia === "desemprego")) ? "pp" : e.unidade;
    const surp = (saiu && temPrev && e.diferenca !== null && e.diferenca !== undefined)
      ? `<span class="mac-surp ${e.empurrao > 0 ? "positive" : e.empurrao < 0 ? "negative" : "muted"}">${
          Number(e.diferenca) === 0 ? "= forecast"
            : (e.diferenca > 0 ? "+" : "") + fmtN(e.diferenca, unSurp) + " vs forecast"}</span>`
      : "";
    // resultado ausente: "not out" so vale quando a hora ainda nao chegou. Se ja passou e a
    // fonte de reserva esta ativa, a verdade e outra: a reserva nao carrega o resultado.
    const fonteReserva = M.eventos && M.eventos.fonte && M.eventos.fonte !== "fxstreet";
    const jaPassou = e.quando_utc && new Date(e.quando_utc).getTime() < Date.now();
    const semResultado = !saiu && jaPassou
      ? (fonteReserva ? "not carried by the fallback source" : "not in the source yet")
      : "not out";
    const ROT_CLASSE = { EM_LINHA: "in line", MUITO_ACIMA: "well above", MUITO_ABAIXO: "well below" };
    const revis = (e.revisado !== null && e.revisado !== undefined)
      ? ` <small class="muted">→ revised ${fmtN(e.revisado, e.unidade)}</small>` : "";

    let barra;
    if (e.discurso) {
      barra = `<div class="mac-barra mac-sem"><span>a speech — no number to measure; the text is the release</span></div>`;
    } else if (temPrev || saiu) {
      barra = `<div class="mac-barra">
           <span>forecast <b>${fmtN(e.previsao, e.unidade)}</b></span>
           <span>previous <b>${fmtN(e.anterior, e.unidade)}</b>${revis}</span>
           <span>actual <b>${saiu ? fmtN(e.resultado, e.unidade) : semResultado}</b>${surp}</span>
           ${atraso}</div>` +
        (saiu && !temPrev
          ? `<div class="mac-barra mac-sem"><span>released without a published forecast — the surprise cannot be measured</span></div>`
          : "");
    } else {
      barra = `<div class="mac-barra mac-sem"><span>no forecast published — a surprise cannot be measured</span></div>`;
    }

    const leitura = e.estado === "DIVULGADO"
      ? `<p class="mac-leitura ${e.empurrao > 0 ? "positive" : e.empurrao < 0 ? "negative" : "muted"}">
           <strong>${esc(ROT_CLASSE[e.classe] || e.classe || "")}</strong> — ${esc(e.empurrao_texto)}</p>`
      : "";
    const avisos = [
      e.data_a_confirmar ? "time tentative" : "",
      e.preliminar ? "preliminary print" : "",
    ].filter(Boolean).join(" · ");

    return `<article class="mac-ficha">
      <header><span class="mac-hora">${brt(e.quando_utc) || ""} BRT</span>
        <strong>${FLAG[e.moeda] || ""} ${esc(e.titulo)}</strong>
        <span class="tag">${esc(e.impacto)}</span>${
          avisos ? `<small class="muted mac-aviso">${esc(avisos)}</small>` : ""}</header>
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

    // O carimbo do cabecalho ficava em "Loading" para sempre: quem o preenchia era um
    // desenhista do FUND, hoje desligado. Passa a ser a hora do calendario — em BRT.
    const carimbo = document.getElementById("updatedAt");
    const g = M.eventos && (M.eventos.fonte_gerado_em || M.eventos.gerado_em);
    if (carimbo && g) {
      const h = brt(g);
      const novo = "data " + h + " BRT";
      // so escreve quando muda: reescrever o mesmo texto a cada 900 ms gerava uma mutacao
      // por tique, e o modulo de idioma varria a pagina inteira a toa
      if (h && carimbo.textContent !== novo && !/^dados /.test(carimbo.textContent || "")) {
        carimbo.textContent = novo;
      }
    }

    const sys = document.getElementById("systemMessage");
    if (sys && /FUND/i.test(sys.textContent)) {
      sys.textContent = "Reading panel. It gives the fundamental side; the entry is yours.";
    }
    // O app.js antigo marca a linha com a classe "error" (vermelha) quando o carregamento do
    // FUND falha — e ele falha de proposito, porque os desenhistas do FUND foram desligados.
    // O texto ja e nosso; o estado de erro nao e. (Eduardo, 04/set: "esta dando um bug".)
    if (sys && sys.classList.contains("error") && !/Could not load|Cannot set/i.test(sys.textContent)) {
      sys.classList.remove("error");
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
    const hojeIso = hojeBrt();

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
                        : "Reading of the day"}${M.moedaCal ? ` <small class="muted">· ${FLAG[M.moedaCal] || ""} ${esc(M.moedaCal)} only</small>` : ""}</h2></div>
        <p>${iso ? (ev.length
              ? "Each release, what it is measured against, and what each outcome would push on the rate decision."
              : (M.moedaCal ? `Nothing above low impact for ${esc(M.moedaCal)} this day.`
                            : "Nothing above low impact scheduled this day."))
            : "Pick a day on the calendar above."}</p></div>
      <div class="mac-dia">${iso ? painelDoDia(iso)
        : '<div class="mac-vazio"><strong>Pick a day on the calendar above.</strong></div>'}</div>`;
  }

  /* MENU AGRUPADO.
   *
   * Auditoria do Eduardo: "ha dez abas no mesmo nivel, e muita coisa". O agrupamento e o dele.
   * Os BOTOES originais sao MOVIDOS, nao recriados — assim os ouvintes de clique que o app.js
   * registrou continuam valendo. Recriar quebraria a navegacao, e foi o tipo de coisa que
   * derrubou o site tres vezes ontem.
   */
  const GRUPOS = [
    { r: "Radar",    abas: ["market", "pairs"] },
    { r: "Macro",    abas: ["yields", "calendar", "news", "cot"] },
    { r: "Analysis", abas: ["ratesfx", "spreads"] },
    { r: "Method",   abas: ["sources"] },
    { r: "Equities", abas: ["equities"] },
  ];

  function agrupaMenu() {
    // A guarda NAO pode olhar o pai dos botoes: depois que eles sao movidos para dentro dos
    // grupos, o pai passa a ser .mac-nav-abas e a marca se perde — o menu regrupava a cada
    // passada e os rotulos duplicavam (medido: 100 rotulos em ~90 segundos).
    // A marca vai numa variavel do modulo, que nao depende do DOM.
    if (M.menuAgrupado) return;
    const botoes = [...document.querySelectorAll("[data-tab]")];
    if (!botoes.length) return;
    const barra = botoes[0].parentElement;
    if (!barra) return;

    const mapa = {};
    botoes.forEach((b) => { mapa[b.dataset.tab] = b; });

    const caixa = document.createElement("div");
    caixa.className = "mac-nav-grupos";

    GRUPOS.forEach((g) => {
      const presentes = g.abas.map((a) => mapa[a]).filter(Boolean);
      if (!presentes.length) return;
      const bloco = document.createElement("div");
      bloco.className = "mac-nav-grupo";
      const rot = document.createElement("span");
      rot.className = "mac-nav-rotulo";
      rot.textContent = g.r;
      bloco.appendChild(rot);
      const linha = document.createElement("div");
      linha.className = "mac-nav-abas";
      presentes.forEach((b) => linha.appendChild(b));   // MOVE, nao clona
      bloco.appendChild(linha);
      caixa.appendChild(bloco);
    });

    // qualquer aba que nao esteja no agrupamento vai para o fim, para nunca sumir
    const sobrando = botoes.filter((b) => !GRUPOS.some((g) => g.abas.includes(b.dataset.tab)));
    if (sobrando.length) {
      const bloco = document.createElement("div");
      bloco.className = "mac-nav-grupo";
      const rot = document.createElement("span");
      rot.className = "mac-nav-rotulo";
      rot.textContent = "Other";
      bloco.appendChild(rot);
      const linha = document.createElement("div");
      linha.className = "mac-nav-abas";
      sobrando.forEach((b) => linha.appendChild(b));
      bloco.appendChild(linha);
      caixa.appendChild(bloco);
    }

    barra.appendChild(caixa);
    M.menuAgrupado = true;
  }

  function aplica() {
    if (!M.pronto) return;

    // OVERVIEW: troca o miolo do painel
    const over = document.querySelector('[data-panel="market"]');
    // Overview mostra SO as reunioes; a matriz de 28 linhas fica na aba Pairs.
    // Repetir a mesma tabela em duas abas so gera ruido — e foi o que o Eduardo apontou no
    // FUND: informacao demais na tela confunde mais do que informa.
    // Cada bloco falha SOZINHO. A primeira passada de aplica() nao tinha protecao nenhuma: um
    // erro em painelBancos derrubava Pairs e Calendar juntos (revisao de 03/set).
    const contido = (nome, fn) => {
      try { return fn(); }
      catch (e) { console.warn("[macro] " + nome + " falhou e foi contido:", e.message); return null; }
    };
    if (over && !over.querySelector(".mac-bloco")) {
      const h = contido("painelBancos", painelBancos);
      if (h) over.innerHTML = h;
    }
    // O bloco dos EUA entra DEPOIS das reunioes e contido: um erro nele nao pode apagar a
    // Overview inteira — foi assim que o site caiu da segunda vez.
    if (over && over.querySelector(".mac-bloco") && !over.querySelector(".mac-eua")) {
      try {
        const h = painelEUA();
        if (h) over.insertAdjacentHTML("beforeend", h);
      } catch (e) { console.warn("[macro] painel dos EUA falhou e foi contido:", e.message); }
    }
    if (over && over.querySelector(".mac-bloco") && !over.querySelector(".mac-geo")) {
      try {
        const h = painelGeo();
        if (h) over.insertAdjacentHTML("beforeend", h);
      } catch (e) { console.warn("[macro] painel de geopolitica falhou e foi contido:", e.message); }
    }

    // PARES: o mesmo, ate o leitor produzir
    const pares = document.querySelector('[data-panel="pairs"]');
    if (pares && !pares.querySelector(".mac-bloco")) {
      const h = contido("matrizPares", matrizPares);
      if (h) pares.innerHTML = h;
    }

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
          <div class="mac-chips mac-cal-chips">
            <button type="button" class="mac-chip on" data-mac-cal-moeda="">All currencies</button>
            ${Object.keys(FLAG).map((m) =>
              `<button type="button" class="mac-chip mac-chip-moeda" data-mac-cal-moeda="${m}">${FLAG[m]} ${m}</button>`).join("")}
          </div>
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
      // filtro por moeda: o pedido do Eduardo em 03/set. Nao muda o dia escolhido — so o que
      // aparece nele e na grade.
      painelCal.querySelectorAll("[data-mac-cal-moeda]").forEach((b) =>
        b.addEventListener("click", () => {
          M.moedaCal = b.dataset.macCalMoeda || null;
          painelCal.querySelectorAll("[data-mac-cal-moeda]").forEach((x) =>
            x.classList.toggle("on", (x.dataset.macCalMoeda || null) === M.moedaCal));
          desenhaCalendario();
        }));
    }
    // So redesenha o calendario quando a FONTE muda (ou na primeira vez). aplica() roda a cada
    // 900 ms, e redesenhar a grade e o painel do dia a cada tique apagava a traducao 60 ms
    // depois de aplicada — a tela oscilava entre ingles e portugues (medido em 04/set) — alem
    // de ser trabalho inutil. Os cliques chamam desenhaCalendario() diretamente.
    if (M.calFonte !== M.eventos) {
      M.calFonte = M.eventos;
      contido("desenhaCalendario", desenhaCalendario);
    }
    contido("agrupaMenu", agrupaMenu);
    contido("limpaFundDaTela", limpaFundDaTela);
  }

  const estilo = document.createElement("style");
  estilo.textContent = `
   .mac-bloco{margin-bottom:28px}
   /* --- Estados Unidos: contagem para o FOMC a esquerda, os prints do BLS a direita --- */
   .mac-eua{margin-top:22px}
   .mac-eua-grid{display:grid;grid-template-columns:minmax(230px,290px) 1fr;gap:18px;
     align-items:start}
   .mac-eua-fomc{border:1px solid rgba(255,255,255,.09);border-radius:12px;padding:16px 18px}
   .mac-eua-dias{font-size:38px;font-weight:600;letter-spacing:-.02em;line-height:1;
     font-variant-numeric:tabular-nums;margin:6px 0 8px}
   .mac-eua-dias small{font-size:13px;font-weight:400;opacity:.55;margin-left:7px;
     letter-spacing:0}
   .mac-dot{display:inline-block;margin-top:9px;font-size:10.5px;letter-spacing:.08em;
     text-transform:uppercase;padding:3px 10px;border-radius:20px;
     background:rgba(94,234,212,.14);color:#5eead4}
   .mac-eua-taxa{margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.07)}
   .mac-eua-tabela{overflow-x:auto}
   .mac-num-td,.mac-num-th{text-align:right;white-space:nowrap}
   .mac-num-td{font-family:var(--font-mono);font-variant-numeric:tabular-nums}
   .mac-ref-td{font-family:var(--font-mono);font-size:12px}
   .mac-prelim{font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;opacity:.55;
     border:1px solid rgba(255,255,255,.18);border-radius:4px;padding:1px 5px;margin-left:6px;
     vertical-align:middle}
   .mac-eua-nota{font-size:12.5px;line-height:1.6;opacity:.7;margin:14px 0 0;max-width:72ch}
   .mac-eua-fed ul{list-style:none;padding:0;margin:8px 0 0;font-size:12.5px}
   .mac-eua-fed li{margin:5px 0;opacity:.85}
   .mac-eua-fed a{color:inherit}
   .mac-perna-eua{margin-top:9px;padding-top:9px;border-top:1px solid rgba(255,255,255,.07);
     font-size:12px;line-height:1.7}
   /* --- sentimento: a leitura para frente, por moeda e por par --- */
   .mac-cal-chips{margin:0 0 12px}
   .mac-lean-pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;padding:3px 10px;
     border-radius:20px;background:rgba(255,255,255,.06);white-space:nowrap}
   .mac-lean-pill b{font-family:var(--font-mono)}
   .mac-lean-pill.positive{background:rgba(82,217,138,.12)}
   .mac-lean-pill.negative{background:rgba(248,122,122,.12)}
   .mac-lean-pill.big{font-size:14px;padding:6px 12px;gap:8px;flex-wrap:wrap}
   .mac-lean-pill.big small{font-size:10.5px;opacity:.65;white-space:normal;font-weight:400}
   .mac-lean-pill.big .mac-score{opacity:.9;font-family:var(--font-mono)}
   .mac-lean-pill.big .mac-score b{font-size:11px}
   .mac-perna-lean{margin:8px 0 10px;padding:10px 0 0;border-top:1px solid rgba(255,255,255,.07)}
   .mac-dims{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}
   .mac-dim{font-size:10.5px;letter-spacing:.04em;padding:2px 8px;border-radius:5px;
     border:1px solid rgba(255,255,255,.12);opacity:.85;white-space:nowrap}
   .mac-dim small{opacity:.6;margin-left:3px}
   .mac-dim.ok{border-color:rgba(82,217,138,.45);color:#52d98a}
   .mac-dim.no{border-color:rgba(248,122,122,.4);color:#f87a7a}
   .mac-dim.off{opacity:.38;border-style:dashed}
   .mac-dim.quiet{opacity:.6;border-style:dotted}
   .mac-motivos{list-style:none;margin:6px 0 0;padding:0;font-size:12px;line-height:1.55}
   .mac-motivos li{margin:3px 0;padding-left:8px;border-left:2px solid rgba(255,255,255,.12)}
   .mac-motivos b{font-weight:600}
   .mac-item-instr{border-top:1px dashed rgba(255,255,255,.12);margin-top:4px;padding-top:11px}
   .mac-item-tag.v-bull{color:#52d98a}
   .mac-item-tag.v-bear{color:#f87a7a}
   .mac-item-tag.v-nao{opacity:.38}
   .mac-item-tag b{font-family:var(--font-mono);font-weight:600}
   .mac-det-leitura.v-bull{background:rgba(82,217,138,.16);color:#52d98a}
   .mac-det-leitura.v-bear{background:rgba(248,122,122,.16);color:#f87a7a}
   .mac-det-leitura.v-nao{background:rgba(255,255,255,.06);opacity:.6}
   .mac-mesma{display:block;margin-top:8px;font-size:12px;color:#f0b429}
   .mac-placar-3{grid-template-columns:1fr 1fr 1fr}
   .mac-placar strong small{font-family:var(--font-mono);opacity:.55;font-weight:400;margin-left:2px}
   @media (max-width:900px){.mac-placar-3{grid-template-columns:1fr}}
   /* --- geopolitica: intensidade por moeda, regra declarada ao lado --- */
   .mac-geo{margin-top:22px}
   .mac-geo-mundo{border:1px solid rgba(255,255,255,.09);border-radius:12px;padding:12px 16px;
     margin-bottom:14px}
   .mac-geo-mundo .mac-perna-papel{display:inline-block;margin-right:10px}
   .mac-geo-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
   .mac-geo-card{border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px 14px}
   .mac-geo-topo{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
   .mac-geo-topo strong{font-size:15px;margin-right:4px}
   .mac-geo-pill{display:inline-flex;gap:5px;align-items:baseline;font-size:11px;padding:2px 9px;
     border-radius:20px;background:rgba(255,255,255,.06);white-space:nowrap}
   .mac-geo-pill b{font-family:var(--font-mono)}
   .mac-geo-pill small{opacity:.55;font-family:var(--font-mono)}
   .mac-geo-pill.medio{background:rgba(240,180,41,.14);color:#f0b429}
   .mac-geo-pill.alto{background:rgba(248,122,122,.16);color:#f87a7a}
   .mac-geo-pill.baixo{background:rgba(82,217,138,.10);color:#52d98a}
   .mac-geo-pill.off{opacity:.4;border:1px dashed rgba(255,255,255,.18);background:transparent}
   .mac-geo-imp{display:flex;flex-direction:column;gap:3px;font-size:12px;color:#f0b429;
     margin:4px 0 6px}
   .mac-geo-lista{list-style:none;margin:6px 0 0;padding:0;font-size:12.5px;line-height:1.5}
   .mac-geo-lista li{margin:3px 0;padding-left:8px;border-left:2px solid rgba(255,255,255,.12)}
   .mac-geo-lista a{color:inherit;text-decoration:none;border-bottom:1px dotted rgba(255,255,255,.3)}
   .mac-geo-lista a:hover{border-bottom-style:solid}
   .mac-perna-geo{margin-top:9px;padding-top:9px;border-top:1px solid rgba(255,255,255,.07);
     display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px}
   .mac-perna-geo .mac-perna-papel{margin:0 4px 0 0}
   /* --- falas do Fed: a frase de postura, com o indice de contagem ao lado --- */
   .mac-falas{margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,255,255,.07)}
   .mac-falas-titulo{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;margin-bottom:8px}
   .mac-falas-titulo small{font-size:11.5px}
   .mac-falas ul{list-style:none;margin:0;padding:0;display:grid;gap:10px}
   .mac-fala{border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:11px 14px}
   .mac-fala-topo{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:13px}
   .mac-fala-link{color:inherit;opacity:.6;font-size:12px;text-decoration:none;
     border-bottom:1px dotted rgba(255,255,255,.3)}
   .mac-fala-link:hover{opacity:1}
   .mac-lean{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;padding:2px 9px;
     border-radius:20px;background:rgba(255,255,255,.06)}
   .mac-lean small{opacity:.6;margin-left:5px;letter-spacing:0;text-transform:none;
     font-family:var(--font-mono)}
   .mac-lean-hawkish{background:rgba(248,122,122,.14);color:#f87a7a}
   .mac-lean-dovish{background:rgba(82,217,138,.14);color:#52d98a}
   .mac-lean-mixed{background:rgba(240,180,41,.14);color:#f0b429}
   .mac-fala-frase{margin:9px 0 0;padding:0 0 0 12px;border-left:2px solid rgba(94,234,212,.5);
     font-size:13px;line-height:1.6;opacity:.9;font-style:italic}
   /* --- ficha do evento: surpresa e atraso de entrega, medidos --- */
   .mac-surp{font-family:var(--font-mono);font-size:11px;padding:2px 8px;border-radius:5px;
     margin-left:8px;white-space:nowrap}
   .mac-surp.positive{background:rgba(82,217,138,.12)}
   .mac-surp.negative{background:rgba(248,122,122,.12)}
   .mac-surp.muted{background:rgba(255,255,255,.06)}
   .mac-atraso{font-family:var(--font-mono);font-size:10.5px;padding:2px 7px;border-radius:5px;
     background:rgba(82,217,138,.12);color:#52d98a;white-space:nowrap;margin-left:auto}
   .mac-atraso-lento{background:rgba(240,180,41,.14);color:#f0b429}
   .mac-aviso{font-size:10.5px;letter-spacing:.04em}
   @media (max-width:900px){
     .mac-eua-grid{grid-template-columns:1fr}
     .mac-eua-dias{font-size:30px}
   }
   .mac-frescor{font-size:12px;margin:10px 0 0}
   .mac-nav-grupos{display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end;width:100%}
   .mac-nav-grupo{display:flex;flex-direction:column;gap:4px}
   .mac-nav-rotulo{font-size:9.5px;letter-spacing:.13em;text-transform:uppercase;opacity:.34;
     padding-left:2px}
   .mac-nav-abas{display:flex;gap:3px}
   @media (max-width:900px){
     .mac-nav-grupos{gap:12px}
     .mac-nav-rotulo{display:none}
   }
   /* --- tela de trabalho dos pares: lista a esquerda, detalhe fixo a direita --- */
   .mac-duas{display:grid;grid-template-columns:minmax(210px,270px) minmax(0,1fr);gap:18px;
     align-items:start}
   .mac-detalhe{min-width:0}
   .mac-lista{display:flex;flex-direction:column;gap:3px;max-height:74vh;overflow-y:auto;
     padding-right:4px}
   .mac-item{display:grid;grid-template-columns:1fr auto;grid-template-rows:auto auto;
     gap:2px 8px;text-align:left;background:transparent;border:0;border-radius:8px;
     padding:9px 11px;color:inherit;cursor:pointer;border-left:2px solid transparent}
   .mac-item:hover{background:rgba(255,255,255,.05)}
   .mac-item-sel{background:rgba(120,200,255,.11);border-left-color:#6cc4ff}
   .mac-item-par{font-size:14px;font-weight:600;letter-spacing:.02em}
   .mac-item-par em{opacity:.35;font-style:normal;margin:0 1px}
   .mac-item-dias{grid-column:2;grid-row:1;font-size:11px;opacity:.5;
     font-variant-numeric:tabular-nums;align-self:center}
   .mac-item-tag{grid-column:1/-1;font-size:10px;letter-spacing:.06em;text-transform:uppercase}
   .mac-item-tag.e-div{color:#8fd0ff}
   .mac-item-tag.e-igual{opacity:.35}

   /* o detalhe acompanha a rolagem — era a queixa principal do Eduardo */
   .mac-detalhe{position:sticky;top:16px;border:1px solid rgba(255,255,255,.09);
     border-radius:12px;padding:20px 22px;min-height:300px}
   .mac-det-topo{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px}
   .mac-det-par{margin:0;font-size:30px;letter-spacing:.01em}
   .mac-det-par em{opacity:.28;font-style:normal;margin:0 2px}
   .mac-det-leitura{font-size:11px;letter-spacing:.09em;padding:4px 11px;border-radius:20px}
   .mac-det-leitura.e-div{background:rgba(120,200,255,.16);color:#8fd0ff}
   .mac-det-leitura.e-igual{background:rgba(255,255,255,.06);opacity:.55}
   .mac-det-dado{margin-left:auto;font-size:11.5px}
   .mac-det-dado.e-fresco{color:#5fd08a}
   .mac-det-dado.e-velho{color:#ffb84d;font-weight:600}
   .mac-det-nota{font-size:13px;opacity:.72;line-height:1.55;margin:8px 0 18px}

   /* minmax(0,1fr) e min-width:0: sem isso a tabela de correlacao empurrava o cartao para
      fora da tela em janela estreita (Eduardo, 04/set, janela de ~950 px) */
   .mac-pernas{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px}
   .mac-perna{border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:14px 15px;min-width:0}
   .mac-perna .mac-eua-tabela{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
   .mac-corr th,.mac-corr td{white-space:nowrap;font-size:12px;padding:6px 8px}
   .mac-corr td:first-child{font-size:12px}
   .mac-det-nota{overflow-wrap:anywhere}
   @media (max-width:1180px){
     .mac-pernas{grid-template-columns:1fr}
     .mac-duas{grid-template-columns:minmax(180px,230px) minmax(0,1fr)}
     .mac-det-par{font-size:26px}
   }
   .mac-perna-papel{display:block;font-size:10px;letter-spacing:.11em;text-transform:uppercase;
     opacity:.4;margin-bottom:6px}
   .mac-perna-nome{display:block;font-size:17px;margin-bottom:3px}
   .mac-perna-nome small{opacity:.45;font-size:11px;font-weight:400;margin-left:4px}
   .mac-perna-taxa{font-size:20px;font-weight:600;font-variant-numeric:tabular-nums;
     margin-bottom:9px}
   .mac-perna-linha{font-size:12.5px;line-height:1.7}

   .mac-det-mais{margin-top:18px;border-top:1px solid rgba(255,255,255,.07);padding-top:13px}
   .mac-det-mais summary{cursor:pointer;font-size:12.5px;opacity:.6}
   .mac-det-mais summary:hover{opacity:.9}
   .mac-det-mais-corpo{font-size:12.5px;line-height:1.62;opacity:.72;margin-top:9px}
   .mac-det-mais-corpo p{margin:0 0 9px}

   /* filtros rapidos */
   .mac-chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:2px 0 8px}
   .mac-chip{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);
     color:inherit;border-radius:20px;padding:5px 13px;font-size:12px;cursor:pointer}
   .mac-chip:hover{background:rgba(255,255,255,.11)}
   .mac-chip.on{background:rgba(120,200,255,.18);border-color:rgba(120,200,255,.5);color:#8fd0ff}
   .mac-chip-moeda{font-size:11px;padding:4px 10px;letter-spacing:.04em}
   .mac-sep{width:1px;height:20px;background:rgba(255,255,255,.12);margin:0 5px}
   .mac-conta{font-size:11.5px;opacity:.45;margin:0 0 14px}

   /* celular: uma coluna, detalhe abaixo da lista */
   @media (max-width:900px){
     .mac-duas{grid-template-columns:1fr}
     .mac-lista{max-height:none;flex-direction:row;flex-wrap:wrap}
     .mac-item{flex:1 1 132px}
     .mac-detalhe{position:static}
     .mac-pernas{grid-template-columns:1fr}
     .mac-placar{grid-template-columns:1fr}
     .mac-det-par{font-size:25px}
   }
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
