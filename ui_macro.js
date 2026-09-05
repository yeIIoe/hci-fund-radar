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
              parSel: null, filtro: "tese", moedaSel: null, moedaCal: null, sent: null,
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
    [M.bancos, M.eventos, M.eua, M.discursos, M.sent, M.geo, M.noticias] = await Promise.all([
      pega("data/bancos_centrais.json"), pega("data/macro_eventos.json"),
      pega("data/eua_leitura.json"), pega("data/bc_discursos.json"),
      pega("data/sentimento.json"), pega("data/geopolitica.json"), pega("data/noticias.json"),
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
  // Revisao do dono (item b): "dados de 3h" lia como "dados com 3 horas de duracao". O que ele
  // quer saber e QUANDO foi a ultima atualizacao. Texto unico, em portugues, usado em toda parte.
  function idadeTexto(min) {
    return min < 2 ? "agora mesmo"
         : min < 90 ? "há " + min + (min === 1 ? " minuto" : " minutos")
         : "há " + Math.round(min / 60) + (Math.round(min / 60) === 1 ? " hora" : " horas");
  }

  function frescor() {
    const E = M.eventos || {};
    // Dois carimbos: o do RELOGIO (a rodada) e o do DADO (a ultima leitura boa da fonte). Se a
    // fonte cair, a rodada continua e o relogio fica "fresco" — e o dado, velho. O que o
    // usuario precisa ver e a idade do DADO. Revisao de 03/set.
    const g = E.fonte_gerado_em || E.gerado_em;
    if (!g) return "Frescor desconhecido — o arquivo do calendário não tem carimbo.";
    const min = Math.round((Date.now() - new Date(g).getTime()) / 60000);
    const velho = min > LIM_PROV.atrasado_min;
    const F = frescorDados();
    let base = `<span class="${velho ? "mac-velho" : "mac-fresco"}">Calendário atualizado ${idadeTexto(min)}</span>` +
           (F.sinc_brt ? ` · última vez <b>sincronizado</b> em ${esc(comBrt(F.sinc_brt))}` : "") +
           ` · atualiza a cada ~15 min, mas a rodada agendada pode atrasar em horário de pico` +
           (velho ? " — esta está atrasada." : ".");
    if (E.fonte && E.fonte !== "fxstreet") {
      base += `<br><span class="mac-velho">Fonte reserva ativa: ${esc(E.aviso_fonte || E.fonte)}</span>`;
    }

    // Duas defasagens, separadas de proposito. A de cima e o RELOGIO (o cron). A de baixo e a
    // FONTE: quanto o numero levou do horario agendado ate aparecer nela, medido nesta rodada
    // e nao alegado. Confundir as duas foi um erro meu em 02/set.
    const L = E.latencia_medida;
    if (!L || L.mediana_alta == null) return base;
    const lento = L.mediana_alta > 120;
    return base + `<br><span class="${lento ? "mac-velho" : "mac-fresco"}">Entrega da fonte, medida nesta rodada:</span>` +
      ` os dados de alto impacto chegam <b>${fmtAtraso(L.mediana_alta)}</b> depois da hora agendada` +
      ` (mediana, n=${L.n_alta}; p90 ${fmtAtraso(L.p90_alta)} — carimbo tardio costuma ser uma revisão retocando o registro).` +
      (L.mediana_alta < 900 ? " O relógio de 15 minutos acima é mais lento que a fonte." : "");
  }

  /* ==================================================================================
   * (2) BLOQUEIO POR ATRASO — o estado geral de frescor, lido de sentimento.frescor.
   *
   * A queixa do dono (05/set): o painel avisava "dados do calendário de 4 horas atrás" e
   * seguia mostrando todas as direções normalmente. Se saiu notícia nessas 4 horas, a
   * leitura pode estar inválida — e quem lê não tem como saber disso pela cor da linha.
   *
   * CONTRATO: a raiz de sentimento.json ganha "frescor" {atraso_min, estado,
   * ultima_sincronizacao_ok_utc/brt, bloqueia_leitura, texto, limiares_provisorios}.
   * Enquanto o núcleo não grava, DERIVAMOS do carimbo do calendário com os mesmos
   * limiares provisórios — o aviso existe hoje, e o campo do núcleo manda assim que
   * chegar. Campo ausente nunca vira exceção.
   * ================================================================================ */
  const LIM_PROV = { atrasado_min: 45, muito_atrasado_min: 120 };

  // Acrescenta "BRT" só quando o texto ainda não diz o fuso. O núcleo grava
  // "05/09/2026 02:18 (BRT)"; concatenar às cegas dava "… (BRT) BRT" na tela.
  function comBrt(txt) {
    const t = String(txt || "").trim();
    if (!t) return "";
    return /BRT/i.test(t) ? t : t + " BRT";
  }

  // Nomes de mês em inglês que ainda chegam DENTRO do dado (o rótulo do FOMC vem
  // "September 15-16*"). Não editamos os arquivos Python, então a troca é aqui.
  const MES_EN_PT = { January: "janeiro", February: "fevereiro", March: "março",
    April: "abril", May: "maio", June: "junho", July: "julho", August: "agosto",
    September: "setembro", October: "outubro", November: "novembro", December: "dezembro" };
  function mesPt(txt) {
    let t = String(txt == null ? "" : txt);
    Object.keys(MES_EN_PT).forEach((en) => {
      t = t.replace(new RegExp("\\b" + en + "\\b", "g"), MES_EN_PT[en]);
    });
    return t;
  }

  // "4h", "50 min" — o formato curto que entra na tarja
  function atrasoCurto(min) {
    if (min === null || min === undefined) return "?";
    const n = Math.round(Number(min) || 0);
    if (n < 90) return n + " min";
    const h = Math.round(n / 60);
    return h + "h";
  }

  function frescorDados() {
    const F = (M.sent && M.sent.frescor) || null;
    if (F && F.estado) {
      const lim = F.limiares_provisorios || LIM_PROV;
      // o núcleo às vezes já escreve o fuso dentro do texto ("02:18 (BRT)"); duplicar
      // vira "02:18 (BRT) BRT" — visto na tela em 05/set
      return {
        atraso_min: F.atraso_min == null ? null : Math.round(Number(F.atraso_min)),
        estado: F.estado,
        bloqueia: !!F.bloqueia_leitura,
        sinc_brt: F.ultima_sincronizacao_ok_brt || brt(F.ultima_sincronizacao_ok_utc) || null,
        texto: F.texto || null,
        limiares: lim,
        derivado: false,
      };
    }
    // fallback: carimbo do calendário (a fonte que o dono viu atrasada)
    const E = M.eventos || {};
    const g = E.fonte_gerado_em || E.gerado_em || (M.sent && M.sent.gerado_em) || null;
    if (!g) return { atraso_min: null, estado: "ok", bloqueia: false, sinc_brt: null,
                     texto: null, limiares: LIM_PROV, derivado: true };
    const min = Math.round((Date.now() - new Date(g).getTime()) / 60000);
    const estado = min >= LIM_PROV.muito_atrasado_min ? "muito_atrasado"
                 : min >= LIM_PROV.atrasado_min ? "atrasado" : "ok";
    return {
      atraso_min: min,
      estado,
      // derivado: só o atraso GRANDE suspende a leitura; o pequeno acinzenta e avisa
      bloqueia: estado === "muito_atrasado",
      sinc_brt: brt(g),
      texto: null,
      limiares: LIM_PROV,
      derivado: true,
    };
  }

  const atrasado = () => frescorDados().estado !== "ok";
  // classe que acinzenta a linha de leitura (opacidade e sem cor semântica)
  const clsAtraso = () => (atrasado() ? " mac-atrasado" : "");
  const bloqueado = () => frescorDados().bloqueia;

  // A tarja âmbar de três linhas, no topo do painel. Só aparece quando há atraso.
  function tarjaAtraso() {
    const F = frescorDados();
    if (F.estado === "ok") return "";
    const l1 = `⚠ Dados atrasados em ${atrasoCurto(F.atraso_min)}`;
    return `<div class="mac-tarja-atraso${F.estado === "muito_atrasado" ? " grave" : ""}" role="status">
      <strong>${esc(l1)}</strong>
      <span>Leituras potencialmente desatualizadas</span>
      <span>Não utilizar como nova tese até a sincronização</span>
      <small>${F.sinc_brt
        ? `Última vez <b>sincronizado</b> com sucesso: ${esc(comBrt(F.sinc_brt))}`
        : "Sem carimbo de sincronização bem-sucedida no arquivo"}${
        F.derivado ? " · atraso derivado do carimbo do calendário" : ""} · limiares provisórios:
        ${F.limiares.atrasado_min} min atrasado, ${F.limiares.muito_atrasado_min} min muito atrasado</small>
    </div>`;
  }

  /* ------------------------------------------------------------------ OVERVIEW */

  /* (4) O REGIME — o que o banco ESTÁ fazendo (ciclo + dados), não o que vai fazer.
   * Campo novo "regime"; sem ele, o último movimento de juro é a queda natural. */
  const ROT_REGIME = { alta: "alta", manutencao: "manutenção", corte: "corte" };
  const CLS_REGIME = { alta: "positive", manutencao: "muted", corte: "negative" };
  function regimeDe(m) {
    const s = sentDe(m);
    if (s && s.regime && ROT_REGIME[s.regime]) return s.regime;
    const b = M.bancos && M.bancos.bancos && M.bancos.bancos[m];
    if (!b) return null;
    return b.ultima_mudanca_bp > 0 ? "alta" : b.ultima_mudanca_bp < 0 ? "corte" : "manutencao";
  }

  /* (4) O PRÓXIMO EVENTO RELEVANTE — o risco mais próximo, que não é a reunião.
   *
   * O dono, 05/set: "antes do RBA podem vir CPI, emprego, salários ou PIB". É esse evento
   * que determina a validade da ZOI e de novas entradas; a reunião continua sendo o limite
   * final do ciclo.
   *
   * Campo novo proximo_evento_relevante. Sem ele, o próximo evento de ALTO impacto da moeda
   * no calendário que já está em casa, excluindo a própria decisão. */
  function eventoRelevante(m) {
    const s = sentDe(m);
    const P = s && s.proximo_evento_relevante;
    if (P && P.titulo) {
      const dias = (P.dias != null) ? P.dias
                 : (P.quando_utc ? diasAte(String(P.quando_utc).slice(0, 10)) : null);
      return { titulo: P.titulo, brt: P.quando_brt || brt(P.quando_utc), impacto: P.impacto || null,
               dias, horas: P.horas != null ? P.horas : null, derivado: false };
    }
    if (!M.eventos || !Array.isArray(M.eventos.eventos)) return null;
    const agora = Date.now();
    const cand = M.eventos.eventos
      .filter((e) => e.moeda === m && e.familia !== "decisao" && !e.discurso &&
                     String(e.impacto).toLowerCase() === "high" &&
                     e.quando_utc && new Date(e.quando_utc).getTime() > agora)
      .sort((a, b) => String(a.quando_utc).localeCompare(String(b.quando_utc)))[0];
    if (!cand) return null;
    return { titulo: cand.titulo, brt: brt(cand.quando_utc), impacto: cand.impacto,
             dias: diasAte(String(cand.quando_utc).slice(0, 10)), horas: null, derivado: true };
  }

  const quandoTexto = (dias) => dias === null || dias === undefined ? "sem data publicada"
    : dias < 0 ? "já passou" : dias === 0 ? "hoje" : dias === 1 ? "amanhã" : "em " + dias + " dias";

  function painelBancos() {
    if (!M.bancos) return "";
    const bs = M.bancos.bancos;
    const ordem = Object.keys(bs).sort((a, b) =>
      ((bs[a].proxima ? diasAte(bs[a].proxima) : null) ?? 999) -
      ((bs[b].proxima ? diasAte(bs[b].proxima) : null) ?? 999));

    const linhas = ordem.map((m) => {
      const b = bs[m];
      const dias = b.proxima ? diasAte(b.proxima) : null;
      // null = a lista de reunioes acabou; nao e "hoje" nem "em null dias" (revisao de 03/set)
      const quando = quandoTexto(dias);
      const urgente = dias !== null && dias <= 7;
      // HORÁRIO BRT PRIMEIRO, em destaque; o local vem depois, menor e secundário.
      // Estava ao contrário — foi o pedido explícito do dono em 05/set.
      const hora = b.hora_local
        ? `${b.hora_local} ${b.fuso.split("/")[1].replace("_", " ")}`
        : "sem hora fixa de divulgação";
      const emBrt = b.proxima_utc ? brt(b.proxima_utc) : null;
      const reg = regimeDe(m);
      const ev = eventoRelevante(m);
      return `<tr class="${urgente ? "mac-urgente" : ""}${clsAtraso()}">
        <td class="mac-moeda">${FLAG[m] || ""} <strong>${m}</strong> <small>${esc(b.sigla)}</small></td>
        <td class="mac-taxa">${esc(b.taxa_texto)}</td>
        <td><span class="mac-regime ${reg ? CLS_REGIME[reg] : "muted"}">${
            reg ? esc(ROT_REGIME[reg]) : "—"}</span>
          <small class="muted"> · último movimento ${esc(b.ultima_mudanca || "—")}${
            b.ultima_mudanca_bp ? ` (${b.ultima_mudanca_bp > 0 ? "+" : ""}${b.ultima_mudanca_bp} pb)` : ""}</small></td>
        <td>${ev
          ? `<strong>${esc(ev.titulo)}</strong>
             <small class="mac-brt">${esc(ev.brt || "—")} BRT</small>
             <small class="muted"> · ${esc(quandoTexto(ev.dias))}${
               ev.impacto ? " · impacto " + esc(String(ev.impacto).toLowerCase() === "high" ? "alto"
                 : String(ev.impacto).toLowerCase() === "medium" ? "médio" : "baixo") : ""}</small>`
          : `<small class="muted">nenhum evento de alto impacto agendado na janela</small>`}</td>
        <td><strong class="mac-brt">${emBrt ? esc(emBrt) + " BRT" : esc(b.proxima || "—")}</strong>
          <small class="muted"> · ${esc(quando)}${b.proxima && emBrt ? " · " + esc(b.proxima) : ""}</small>
          <small class="mac-hora-local">${b.hora_local ? "horário local " + esc(hora) : esc(hora)}</small></td>
        <td>${leanCel(m)}</td>
      </tr>`;
    }).join("");

    return `<section class="content-section mac-bloco">
      <div class="section-title"><div><h2>Reuniões dos bancos centrais</h2></div>
        <p>A taxa em vigor, o regime em que cada banco está, o próximo evento que pode invalidar a
           tese, quando cada um decide de novo e a leitura para frente. O horário em <b>BRT</b> vem
           primeiro; o local fica ao lado, secundário.</p></div>
      ${tarjaAtraso()}
      <div class="table-wrap"><table class="mac-tabela">
        <thead><tr><th>Moeda</th><th>Taxa</th><th>Regime</th>
                   <th>Próximo evento relevante</th><th>Próxima decisão</th><th>Leitura</th></tr></thead>
        <tbody>${linhas}</tbody></table></div>
      <p class="mac-frescor">${frescor()}</p>
      <p class="method-note">A taxa e as datas são fatos, conferidos nas páginas dos próprios bancos
        centrais em 01/set/2026. O <em>regime</em> é o que o banco está fazendo; a <em>leitura</em> é
        para onde os dados divulgados, o texto e o ciclo apontam — e ela nunca sai de uma pontuação.
        O <em>próximo evento relevante</em> é o que decide a validade da ZOI e de entradas novas; a
        reunião é o limite final do ciclo.</p>
    </section>`;
  }

  /* ---------------------------------------------------------------- SENTIMENTO */

  // A leitura PARA FRENTE de uma moeda, vinda de sentimento.py. Quatro dimensoes, 25% cada:
  // dados, texto, ciclo, mercado. Dimensao nao conectada baixa o TETO — nunca vira zero.
  // O que a interface escreve hoje. Os rotulos ja saem em portugues NA FONTE, sem depender do
  // ui_lang.js — lei da casa: zero ingles na tela. Os mapas em ingles (ROT_DIR, ROT_SINAL,
  // ROT_FORCA) foram removidos junto com o score: nao havia mais quem os lesse.
  const ROT_DIR_PT = { SOBE: "alta", MANTEM: "manutenção", CORTA: "corte" };
  const SETA_DIR = { SOBE: "&#9650;", MANTEM: "&mdash;", CORTA: "&#9660;" };
  const CLS_DIR = { SOBE: "positive", MANTEM: "muted", CORTA: "negative" };

  function sentDe(m) {
    return (M.sent && M.sent.moedas && M.sent.moedas[m]) || null;
  }

  function regua() {
    return (M.sent && M.sent.regua) || {};
  }

  /* ---------------------------------------------------------------------------------
   * CONTRATO NOVO, LIDO COM TOLERANCIA.
   *
   * O nucleo (sentimento.py) esta sendo reescrito em paralelo e passa a gravar campos que
   * hoje ainda nao existem no JSON: estado, divergencia, qualidade_evidencia, acao,
   * dominancia, familias_independentes, origem do texto, vota/selo na geopolitica.
   *
   * REGRA DESTE ARQUIVO: campo ausente => comportamento antigo, nunca excecao. Toda leitura
   * passa por uma destas funcoes, que devolvem null quando o nucleo ainda nao gravou.
   * ------------------------------------------------------------------------------- */

  // (i) A GEOPOLITICA NAO VOTA. O nucleo ja a tira do score; aqui ela sai tambem da conta
  // "N de M dimensoes concordam" e ganha o selo experimental em toda a interface.
  const SELO_GEO = "experimental — contexto, não vota";
  function dimVota(k, v) {
    if (k === "geo") return false;                 // decisao do dono, vale mesmo sem o campo
    if (v && v.vota === false) return false;       // o nucleo pode desligar outras tambem
    return true;
  }

  // Quantas dimensoes QUE VOTAM concordam, sobre quantas votam. Substitui
  // Math.round(conviccao_pct / 25) / dimensoes_ligadas, que contava a geopolitica.
  function concordancia(s) {
    if (!s) return { ok: 0, total: 0 };
    const C = s.concordam || {};
    const D = s.dimensoes || {};
    const ks = Object.keys(C).filter((k) => dimVota(k, D[k]));
    if (!ks.length) {
      // contrato antigo sem "concordam": cai no numero de antes, ja sem a geopolitica
      const lig = Math.max(0, (s.dimensoes_ligadas || 0) - ((D.geo && D.geo.direcao) ? 1 : 0));
      return { ok: Math.min(lig, Math.round((s.conviccao_pct || 0) / 25)), total: lig };
    }
    return { ok: ks.filter((k) => C[k]).length, total: ks.length };
  }

  // (j) A ORIGEM da dimensao de texto. Quando a origem e manchete, a interface esta PROIBIDA
  // de escrever "discursos" — foi o erro que o dono viu: 38 manchetes do Google News exibidas
  // como falas do RBA, que nem feed tem.
  const ROT_ORIGEM = {
    discurso_oficial: "discurso oficial",
    comunicado_ata: "comunicado ou ata",
    imprensa_com_fala: "imprensa com fala de dirigente",
    manchete: "manchete (contexto, não vota)",
    headlines: "manchete (contexto, não vota)",   // rotulo legado do JSON de hoje
  };
  const ehManchete = (v) => !!(v && (v.origem === "manchete" || v.origem === "headlines"));
  function origemTexto(v) {
    if (!v || !v.origem) return null;
    return ROT_ORIGEM[v.origem] || String(v.origem);
  }
  // o nome da dimensao de texto muda com a origem. Manchete NUNCA pode sair como "discursos"
  // (foi o erro que o dono viu no AUD); e comunicado/ata tambem nao e discurso.
  const NOME_TEXTO = {
    discurso_oficial: "discursos",
    comunicado_ata: "comunicados e atas",
    imprensa_com_fala: "imprensa com fala",
    manchete: "manchetes (contexto)",
    headlines: "manchetes (contexto)",
  };
  function rotuloTexto(v) {
    if (ehManchete(v)) return "manchetes (contexto)";
    return (v && NOME_TEXTO[v.origem]) || "discursos";
  }

  // (h) Uma unica divulgacao dominando a leitura da moeda.
  function dominanciaDe(m) {
    const s = sentDe(m);
    const D = s && s.dominancia;
    if (!D || !D.alerta) return null;
    if (D.texto) return String(D.texto);
    const q = D.share_pct != null ? D.share_pct + "%" : "quase toda";
    return `uma única divulgação responde por ${q} da leitura do ${m}` +
           (D.item ? ` (${D.item})` : "");
  }
  function tarjaAlerta(txt, classe) {
    return txt ? `<div class="mac-tarja${classe ? " " + classe : ""}">⚠ ${esc(txt)}</div>` : "";
  }

  // Familias independentes que sustentam o sinal (inflacao, emprego, atividade, comunicacao).
  function familiasDe(m) {
    const s = sentDe(m);
    const F = s && s.familias_independentes;
    if (!F || F.n == null) return null;
    return { n: F.n, quais: Array.isArray(F.quais) ? F.quais : [] };
  }
  const ROT_FAMILIA = { inflacao: "inflação", emprego: "emprego", atividade: "atividade",
                        comunicacao: "comunicação" };

  function dimsChips(s) {
    const D = s.dimensoes || {};
    return `<span class="mac-dims">${["dados", "texto", "ciclo", "geo"].map((k) => {
      const v = D[k];
      const nome = k === "dados" ? "dados"
                 : k === "texto" ? rotuloTexto(v)
                 : k === "ciclo" ? "ciclo" : "geopolítica";
      const vota = dimVota(k, v);
      const selo = vota ? "" : ` <small class="mac-selo">${k === "geo" ? SELO_GEO : "não vota"}</small>`;
      if (!v) return `<span class="mac-dim off" title="não conectada">${nome} —${selo}</span>`;
      // geopolitica ligada mas sem pico: nao vota, e diz por que
      // title vazio nao ajuda ninguem: quando a dimensao esta quieta e nao trouxe motivo,
      // a dica diz o que "quieta" significa (verificacao 05/set — o chip de manchete do
      // JPY e do AUD saia com title="")
      if (!v.direcao) return `<span class="mac-dim quiet" title="${esc(v.motivo || v.nota ||
        "sem direção legível nesta dimensão — silêncio não é voto")}">${nome} <small>quieta</small>${selo}</span>`;
      const ok = s.concordam && s.concordam[k];
      // (3) A DICA DE TELA NAO MOSTRA MAIS CONTAGEM DE MARCADORES. Contagem de palavras nao
      // le negacao, condicao nem referencia temporal — foi o erro do "Waller hawkish".
      // No lugar entra o veredito por orador, quando o classificador ja gravou.
      const vs = (k === "texto") ? (Array.isArray(v.veredito_por_orador) && v.veredito_por_orador.length
        ? v.veredito_por_orador : null) : null;
      const det = k === "dados" ? `${v.n} divulgações desde ${v.desde}, ponderadas por família e impacto`
                : k === "texto" ? (vs
                    ? vs.slice(0, 4).map((x) => `${x.orador || "?"} — ${ROT_VEREDITO[x.veredito] || x.veredito || "indeterminado"}`).join(" · ")
                    : `${v.n} ${ehManchete(v) ? "manchete(s)" : "item(ns) de fala"} na janela, sem veredito classificado`) +
                                  (origemTexto(v) ? ` · origem: ${origemTexto(v)}` : "")
                : k === "ciclo" ? (v.nota || "")
                : (v.motivo || "");
      // COR SEMANTICA (lei do dono): verde SO para alta de juro, vermelho SO para corte.
      // Antes a cor era a CONCORDANCIA, e por isso a tela pintava de vermelho um chip escrito
      // "alta" (discursos do GBP, dados do CHF) e de verde um chip escrito "manutenção"
      // (ciclo do USD, do GBP, do CAD). A concordancia continua legivel no ✓ / ✗ e no rotulo
      // do title; a COR passa a ser so a direcao do juro.
      const cls = !vota ? "exp"
                : v.direcao === "SOBE" ? "d-alta"
                : v.direcao === "CORTA" ? "d-corte" : "d-mantem";
      const concordo = ok ? "concorda com a leitura da moeda" : "discorda da leitura da moeda";
      return `<span class="mac-dim ${cls}${vota && !ok ? " discorda" : ""}" title="${esc(det + " · " + concordo)}">${nome} ${vota ? (ok ? "&#10003;" : "&#10007;") : "&#9679;"}
        <small>${ROT_DIR_PT[v.direcao] || ""}</small>${selo}</span>`;
    }).join("")}</span>`;
  }

  /* ==================================================================================
   * (1) O BLOCO DA MOEDA — SEM PONTUAÇÃO, EM NENHUM LUGAR.
   *
   * A queixa do dono (05/set): a página escrevia "o que cada um vai fazer vem dos dados
   * divulgados, nunca de uma pontuação" e mostrava "+0,17", "+0,47", "−0,08" em todas as
   * linhas. Contradição na mesma tela. A pontuação sai INTEIRA — a palavra e o número.
   *
   * No lugar, exatamente três linhas:
   *     AUD — inclinado à alta
   *     1 de 2 dimensões concordam
   *     Evidência: moderada
   *
   * Campos do contrato novo: leitura_texto, concordancia_texto, evidencia_rotulo. Cada um
   * tem queda para o comportamento antigo quando o núcleo ainda não gravou.
   * ================================================================================ */
  const ROT_LEITURA = {
    inclinado_alta: "inclinado à alta",
    inclinado_corte: "inclinado ao corte",
    manutencao: "em manutenção",
    sem_leitura: "sem leitura",
  };
  const CLS_LEITURA = { inclinado_alta: "positive", inclinado_corte: "negative",
                        manutencao: "muted", sem_leitura: "muted" };
  const SETA_LEITURA = { inclinado_alta: "&#9650;", inclinado_corte: "&#9660;",
                         manutencao: "&mdash;", sem_leitura: "&middot;" };

  // (e) FAIXAS PROVISÓRIAS sobre qualidade_evidencia: <40 fraca · 40-69 moderada · >=70 forte
  const FAIXAS_EVID = { fraca: [0, 39], moderada: [40, 69], forte: [70, 100] };
  function evidenciaRotulo(s) {
    if (!s) return null;
    if (s.evidencia_rotulo) return String(s.evidencia_rotulo);
    const Q = s.qualidade_evidencia;
    const nota = (Q && Q.nota != null) ? Number(Q.nota)
               : (typeof Q === "number" ? Q : null);
    if (nota === null || isNaN(nota)) return null;
    return nota < FAIXAS_EVID.fraca[1] + 1 ? "fraca"
         : nota < FAIXAS_EVID.moderada[1] + 1 ? "moderada" : "forte";
  }

  /* A leitura de uma moeda, já resolvida. Devolve sempre as três linhas prontas.
   * REGRA DA ZONA SEM LEITURA (provisória, do contrato): é "sem_leitura" quando menos de
   * DUAS dimensões votam, ou quando a divergência sobre o teto fica abaixo de 15. */
  const PISO_SEM_LEITURA = 15;
  function leituraDe(m) {
    const s = sentDe(m);
    if (!s) return null;
    const c = concordancia(s);
    let chave = s.leitura || null;
    let texto = s.leitura_texto || (chave ? ROT_LEITURA[chave] : null);
    let motivo = s.leitura_motivo || null;
    if (!texto) {
      const d = divergenciaDe(s);
      if (c.total < 2) {
        chave = "sem_leitura";
        motivo = motivo || `só ${c.total} dimensão vota nesta moeda — silêncio não é voto, ` +
          `e uma dimensão sozinha não é leitura (piso provisório: 2)`;
      } else if (d < PISO_SEM_LEITURA) {
        chave = "sem_leitura";
        motivo = motivo || `sinal fraco demais para virar leitura (abaixo do piso provisório ` +
          `de ${PISO_SEM_LEITURA} sobre o teto das dimensões que votam)`;
      } else {
        chave = s.direcao === "SOBE" ? "inclinado_alta"
              : s.direcao === "CORTA" ? "inclinado_corte" : "manutencao";
      }
      texto = ROT_LEITURA[chave] || "sem leitura";
    }
    if (!chave) {
      chave = texto === ROT_LEITURA.inclinado_alta ? "inclinado_alta"
            : texto === ROT_LEITURA.inclinado_corte ? "inclinado_corte"
            : texto === ROT_LEITURA.sem_leitura ? "sem_leitura" : "manutencao";
    }
    const conc = s.concordancia_texto ||
      `${c.ok} de ${c.total} ${c.total === 1 ? "dimensão concorda" : "dimensões concordam"}`;
    return { chave, texto, motivo, conc, evid: evidenciaRotulo(s), ok: c.ok, total: c.total };
  }

  /* As três linhas, no formato que o dono escreveu. `tam` só muda o tamanho da fonte. */
  function blocoMoeda(m, tam) {
    const L = leituraDe(m);
    if (!L) return `<small class="muted">leitura ainda não construída</small>`;
    const cls = CLS_LEITURA[L.chave] || "muted";
    if (L.chave === "sem_leitura") {
      return `<div class="mac-bloco-moeda${tam === "big" ? " big" : ""}${clsAtraso()}">
        <div class="mac-bm-linha1 muted"><strong>${esc(m)}</strong> &mdash; sem leitura</div>
        ${L.motivo ? `<div class="mac-bm-motivo">${esc(L.motivo)}</div>` : ""}
        <div class="mac-bm-linha2">${esc(L.conc)}</div>
        ${L.evid ? `<div class="mac-bm-linha3">Evidência: <b>${esc(L.evid)}</b>
          <small class="mac-prov-mini">· faixa provisória</small></div>` : ""}
      </div>`;
    }
    return `<div class="mac-bloco-moeda${tam === "big" ? " big" : ""}${clsAtraso()}">
      <div class="mac-bm-linha1 ${cls}"><span class="mac-bm-seta">${SETA_LEITURA[L.chave]}</span>
        <strong>${esc(m)}</strong> &mdash; ${esc(L.texto)}</div>
      <div class="mac-bm-linha2">${esc(L.conc)}</div>
      <div class="mac-bm-linha3">${L.evid
        ? `Evidência: <b>${esc(L.evid)}</b> <small class="mac-prov-mini">· faixa provisória</small>`
        : `Evidência: <span class="muted">ainda não informada pelo núcleo</span>`}</div>
    </div>`;
  }

  // celula da tabela de bancos — o bloco da moeda, sem pontuação nenhuma
  function leanCel(m) {
    return blocoMoeda(m, "cel");
  }

  // Os motivos X, Y e Z: os prints que mais pesaram na dimensao de dados, e a frase do
  // dirigente quando ha discurso ligado. O Eduardo pediu a conviccao "devido a x, y e z".
  function motivosPerna(m, s) {
    const D = s.dimensoes || {};
    const top = ((D.dados || {}).principais || []).slice(0, 3);
    const ROT = { MUITO_ACIMA: "muito acima", MUITO_ABAIXO: "muito abaixo", EM_LINHA: "em linha" };
    const li = top.map((x) =>
      `<li><span class="muted mac-ref-td">${esc((x.quando_utc || "").slice(5, 10))}</span>
         ${esc(x.titulo)} <b class="${x.contribuicao > 0 ? "positive" : "negative"}">${esc(ROT[x.classe] || x.classe || "")}</b>
         <small class="muted">${x.contribuicao > 0 ? "+" : x.contribuicao < 0 ? "−" : ""}${
           Math.abs(Number(x.contribuicao) || 0).toFixed(2).replace(".", ",")}</small></li>`);
    // a fala mais recente desta moeda, se o feed dela estiver ligado
    const falas = (M.discursos && Array.isArray(M.discursos.itens)) ? M.discursos.itens : [];
    const fala = falas.find((f) => (f.moeda || "USD") === m && f.frases && f.frases.length);
    if (fala) {
      li.push(`<li><span class="muted mac-ref-td">${esc((fala.data || "").slice(5, 10))}</span>
        <b>${esc(fala.orador)}</b>: <em>“${esc(fala.frases[0].frase.slice(0, 150))}${fala.frases[0].frase.length > 150 ? "…" : ""}”</em></li>`);
    } else {
      // sem discurso proprio (RBA, RBNZ, SNB): a manchete classificada mais recente
      const Nm = M.noticias && M.noticias.moedas && M.noticias.moedas[m];
      const man = Nm && (Nm.itens || []).find((x) => x.classe);
      if (man) {
        li.push(`<li><span class="muted mac-ref-td">${esc((man.quando_utc || "").slice(5, 10))}</span>
          <b>${esc(man.fonte || "imprensa")}</b>: <em>“${esc(man.titulo.slice(0, 140))}”</em>
          <small class="muted">manchete (contexto)</small></li>`);
      }
    }
    if (!li.length) return `<div class="mac-perna-linha muted"><small>nenhuma divulgação com consenso na janela</small></div>`;
    return `<span class="mac-perna-papel" style="margin-top:10px">porque</span><ul class="mac-motivos">${li.join("")}</ul>`;
  }

  // bloco dentro do cartao da perna — (c) sem pontuacao; (h) tarja de dominancia; (j) origem do texto
  function leanPerna(m) {
    const s = sentDe(m);
    if (!s) return `<div class="mac-perna-linha muted"><small>leitura para frente ainda não construída</small></div>`;
    const D = s.dimensoes || {};
    const orig = origemTexto(D.texto);
    const fam = familiasDe(m);
    return `<div class="mac-perna-lean">
      <span class="mac-perna-papel">Leitura do próximo passo</span>
      ${blocoMoeda(m, "big")}
      <div class="mac-bm-nota">a geopolítica é ${SELO_GEO} e não entra nesta conta</div>
      ${tarjaAlerta(dominanciaDe(m), "mac-tarja-dom")}
      ${orig ? `<div class="mac-origem-txt"><span class="mac-perna-papel">origem do texto</span>${esc(orig)}</div>` : ""}
      ${fam ? `<div class="mac-familias"><span class="mac-perna-papel">famílias independentes</span>
        <b>${fam.n}</b>${fam.quais.length ? ` <small class="muted">${fam.quais.map((x) => esc(ROT_FAMILIA[x] || x)).join(", ")}</small>` : ""}</div>` : ""}
      ${dimsChips(s)}
      ${motivosPerna(m, s)}
      ${falasDeMoeda(m)}
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
  const ROT_CICLO = { "1": "último movimento para cima", "-1": "último movimento para baixo",
                      "0": "sem mudança" };

  /* ------------------------------------------------------- ESTADO, DIVERGENCIA E ACAO
   * Tres leituras do par que o nucleo novo grava e que a interface le com tolerancia. */

  // divergencia = o antigo conviccao_pct, renomeado. Continua lendo os dois.
  function divergenciaDe(s) {
    if (!s) return 0;
    const v = (s.divergencia != null) ? s.divergencia : s.conviccao_pct;
    return Math.round(Number(v) || 0);
  }

  const ROT_ESTADO = { sem_tese: "sem tese", observacao: "observação",
                       moderada: "tese moderada", forte: "tese forte" };
  const ACAO_ESTADO = { sem_tese: "nada a fazer", observacao: "apenas observar",
                        moderada: "aguardar BO + ZOI", forte: "aguardar BO + ZOI" };
  const CLS_ESTADO = { sem_tese: "e-sem", observacao: "e-obs", moderada: "e-mod", forte: "e-forte" };

  // Estado do par. Vem do campo "estado". Sem ele, so classifica se as FAIXAS PROVISORIAS
  // estiverem no JSON — senao devolve null e a tela cai no comportamento antigo (sinal
  // BULL/BEAR = tem tese), que e o contrato de hoje.
  function estadoDe(s) {
    if (!s) return null;
    if (s.estado && ROT_ESTADO[s.estado]) return s.estado;
    const f = s.faixas_provisorias || regua().faixas_provisorias || null;
    if (!f) return null;
    const d = divergenciaDe(s);
    for (const k of ["forte", "moderada", "observacao", "sem_tese"]) {
      const fx = f[k];
      if (Array.isArray(fx) && fx.length === 2 && d >= fx[0] && d <= fx[1]) return k;
    }
    return null;
  }

  // qualidade da evidencia do par: o ELO FRACO das duas pernas (o nucleo ja manda combinada)
  function qualidadeDe(s, b, q) {
    if (s && s.qualidade_evidencia != null) return Math.round(Number(s.qualidade_evidencia));
    const nota = (m) => {
      const x = sentDe(m);
      const Q = x && x.qualidade_evidencia;
      return (Q && Q.nota != null) ? Number(Q.nota) : null;
    };
    const a = b ? nota(b) : null, c = q ? nota(q) : null;
    if (a === null && c === null) return null;
    if (a === null) return Math.round(c);
    if (c === null) return Math.round(a);
    return Math.round(Math.min(a, c));
  }

  // (f) A ACAO, escrita por extenso. "Compra AUD/CAD", nunca BULL.
  // (2) COM DADO ATRASADO A AÇÃO SAI DA TELA. Enquanto o frescor bloqueia, nenhum par mostra
  // "Compra" nem "Venda": a leitura pode ter virado numa notícia dentro da janela de atraso.
  const ACAO_SUSPENSA = "leitura suspensa — dado atrasado";
  function acaoDe(d) {
    if (bloqueado()) return ACAO_SUSPENSA;
    const s = d.s;
    const alvo = d.instr ? (d.par === "XAUUSD" ? "XAU/USD" : d.par) : (d.b + "/" + d.q);
    if (s && s.acao) return String(s.acao);
    if (!d.tese) return "Sem tese";
    if (s && s.sinal === "BULL") return "Compra " + alvo;
    if (s && s.sinal === "BEAR") return "Venda " + alvo;
    return "Sem tese";
  }
  // o verbo e a sigla, separados: o verbo manda, a sigla fica secundaria
  function acaoPartes(d) {
    const txt = acaoDe(d);
    if (txt === ACAO_SUSPENSA) return { verbo: txt, alvo: "", cls: "v-suspensa" };
    const m = /^(Compra|Venda)\s+(.+)$/.exec(txt);
    if (m) return { verbo: m[1], alvo: m[2], cls: m[1] === "Compra" ? "v-bull" : "v-bear" };
    return { verbo: txt, alvo: "", cls: "v-nao" };
  }

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
    // (a) o ESTADO manda quando existe; sem ele, o criterio antigo do sinal
    const estado = estadoDe(s);
    const tese = estado ? estado !== "sem_tese"
                        : !!(s && (s.sinal === "BULL" || s.sinal === "BEAR"));
    return { par, b, q, cb, cq, diverge: cb !== cq, dias, s, tese, estado,
             conv: divergenciaDe(s), qual: qualidadeDe(s, b, q) };
  }

  // XAUUSD, NQ e ES entram na mesma lista, lidos pela perna do USD. Nao sao pares de duas
  // moedas — o cartao deles mostra o canal e o que esta (ou nao) medido em casa.
  const INSTR = ["XAUUSD", "NQ", "ES"];
  function dadosInstr(sym) {
    const I = (M.sent && Array.isArray(M.sent.instrumentos))
      ? M.sent.instrumentos.find((x) => x.simbolo === sym) : null;
    const bs = M.bancos ? M.bancos.bancos : {};
    const dias = bs.USD && bs.USD.proxima ? diasAte(bs.USD.proxima) : null;
    const sI = I ? { sinal: I.sinal, estado: I.estado, acao: I.acao,
                     divergencia: I.divergencia, conviccao_pct: I.conviccao_pct,
                     qualidade_evidencia: I.qualidade_evidencia } : null;
    const estado = estadoDe(sI);
    const tese = estado ? estado !== "sem_tese"
                        : !!(I && (I.sinal === "BULL" || I.sinal === "BEAR"));
    return { par: sym, b: "USD", q: "", rotulo: sym === "XAUUSD" ? "XAU<em>/</em>USD" : sym,
             instr: true, info: I, s: sI, tese, estado,
             conv: divergenciaDe(sI), qual: qualidadeDe(sI, "USD", null),
             dias, diverge: false, cb: 0, cq: 0 };
  }
  function instrumentosLista() {
    return (M.sent && Array.isArray(M.sent.instrumentos)) ? INSTR.map(dadosInstr) : [];
  }

  const CLS_SINAL = { BULL: "v-bull", BEAR: "v-bear", SEM_TESE: "v-nao", "NAO NEGOCIA": "v-nao", SEM_DADO: "v-nao" };

  // (f) A ACAO na frente, a sigla atras. (e) Mais contraste: o item nao selecionado tem
  // fundo e borda proprios — antes sumia no fundo da pagina.
  function itemLista(d) {
    const sel = d.par === M.parSel ? " mac-item-sel" : "";
    const a = acaoPartes(d);
    const est = d.estado || null;
    // sem tese: o verbo ja diz "Sem tese", entao a etiqueta mostra so a divergencia — repetir
    // a mesma palavra duas vezes no mesmo item nao informa nada
    // LEI DO DONO: limiar novo e PROVISORIO e tem de estar rotulado como tal EM TODA PARTE.
    // A lista era um dos dois lugares onde o rotulo faltava (o outro era a pastilha do
    // detalhe): "tese moderada" aparecia sozinho, como se a faixa ja estivesse calibrada.
    const tag = d.s
      ? `<span class="mac-item-tag ${a.cls}" title="faixa provisória, ainda não calibrada por backtest">${
          d.tese ? esc(est ? (ROT_ESTADO[est] || est) : "com tese") + " " : "divergência "
          }<b>${d.conv}</b><small class="mac-de100">/100</small>${
          est ? `<small class="mac-prov-mini">prov.</small>` : ""}</span>`
      : `<span class="mac-item-tag ${d.diverge ? "e-div" : "e-igual"}">${d.diverge ? "divergência" : "mesmo lado"}</span>`;
    return `<button type="button" class="mac-item${sel}${d.instr ? " mac-item-instr" : ""}${clsAtraso()}" data-mac-par="${d.par}">
      <span class="mac-item-acao ${a.cls}">${esc(a.verbo)}</span>
      <span class="mac-item-par">${d.instr ? d.rotulo : d.b + "<em>/</em>" + d.q}</span>
      ${tag}
      <span class="mac-item-dias">${d.dias === null ? "sem data" : d.dias === 0 ? "decide hoje" : d.dias + "d"}</span>
    </button>`;
  }

  function pernaCard(m, ciclo, papel) {
    const b = M.bancos && M.bancos.bancos[m];
    if (!b) {
      return `<div class="mac-perna"><span class="mac-perna-papel">${papel}</span>
        <strong class="mac-perna-nome">${m}</strong>
        <div class="mac-perna-linha muted">sem dado</div></div>`;
    }
    const dias = b.proxima ? diasAte(b.proxima) : null;
    const quando = dias === null ? "sem data publicada" : dias === 0 ? "hoje"
                 : dias === 1 ? "amanhã" : "em " + dias + " dias";
    const hora = b.hora_local
      ? esc(b.hora_local + " " + b.fuso.split("/")[1].replace("_", " "))
      : "sem hora fixa";
    return `<div class="mac-perna">
      <span class="mac-perna-papel">${papel}</span>
      <strong class="mac-perna-nome">${FLAG[m] || ""} ${m} <small>${esc(b.sigla)}</small></strong>
      <div class="mac-perna-taxa">${esc(b.taxa_texto)}</div>
      ${leanPerna(m)}
      <div class="mac-perna-linha ${ciclo > 0 ? "positive" : ciclo < 0 ? "negative" : "muted"}">
        ${ciclo > 0 ? "&#9650;" : ciclo < 0 ? "&#9660;" : "&mdash;"} ${ROT_CICLO[String(ciclo)]}
        <small class="muted">&middot; ${esc(b.ultima_mudanca)}</small></div>
      <div class="mac-perna-linha muted">próxima decisão <strong>${quando}</strong>
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
    // Rotulos em PORTUGUES na fonte: este cartao e todo em portugues e o ui_lang.js so troca
    // NOS DE TEXTO inteiros — "m/m · unemployment" caia num no unico que nenhuma chave casava,
    // e "unemployment" ficava em ingles no meio do cartao.
    if (cpi && cpi.aa != null) partes.push(`CPI <b>${p(cpi.aa)}%</b> a/a`);
    if (core && core.aa != null) partes.push(`núcleo <b>${p(core.aa)}%</b>`);
    if (nfp && nfp.mm != null) partes.push(`NFP <b>${p(nfp.mm, 0)}k</b> m/m`);
    if (u && u.valor != null) partes.push(`desemprego <b>${u.valor.toFixed(1)}%</b>`);
    if (!partes.length) return "";
    const ref = cpi && cpi.referencia ? cpi.referencia : "";
    return `<div class="mac-perna-linha mac-perna-eua">últimos dados <small class="muted">(${esc(ref)})</small><br>${partes.join(" &middot; ")}</div>`;
  }

  function detalhePar(par) {
    if (!par) {
      return `<div class="mac-vazio"><strong>Escolha um par na lista à esquerda.</strong>
        <p>Todo par são duas moedas. Este painel lê as duas pernas, porque o motivo de uma entrada
           costuma estar num dos lados, não no par.</p></div>`;
    }
    const d = INSTR.includes(par) ? dadosInstr(par) : dadosPar(par);
    const F = frescorDados();
    const g = M.bancos && M.bancos.gerado_em;
    const min = g ? Math.round((Date.now() - new Date(g).getTime()) / 60000) : null;
    const velho = (min !== null && min > LIM_PROV.atrasado_min) || atrasado();
    // (b) "atualizado há 3 horas" — nunca mais "dados de 3h"
    // (2) e a hora da ultima SINCRONIZACAO BEM-SUCEDIDA, nao so a idade generica
    const idade = (F.sinc_brt ? "sincronizado " + esc(comBrt(F.sinc_brt)) : null)
      || (min === null ? "frescor desconhecido" : "atualizado " + idadeTexto(min));
    if (d.instr) return detalheInstr(d, idade, velho);

    const s = d.s;
    const est = d.estado || null;
    // o "prov." e obrigatorio: a faixa que decide se isto e "tese moderada" ou "observação"
    // e PROVISORIA e nunca foi calibrada — lei do dono, e aqui o rotulo faltava
    const pill = s
      ? `<span class="mac-det-leitura ${est ? CLS_ESTADO[est] : (CLS_SINAL[s.sinal] || "v-nao")}"
              title="faixa provisória, ainda não calibrada por backtest">${
          est ? esc(ROT_ESTADO[est] || est) : (d.tese ? "com tese" : "sem tese")}${
          est ? `<small class="mac-prov-mini">prov.</small>` : ""}</span>`
      : `<span class="mac-det-leitura ${d.diverge ? "e-div" : "e-igual"}">${d.diverge ? "DIVERGÊNCIA DE CICLO" : "MESMO LADO"}</span>`;

    // (1) SEM PONTUACAO: a nota nao cita mais "diferenca relativa +0,55 de um maximo de 2,00".
    // A leitura de cada perna sai em PALAVRAS, e quem manda e a perna dominante.
    let nota;
    if (s && d.tese) {
      const Lb = leituraDe(d.b), Lq = leituraDe(d.q);
      nota = `<b>${esc(acaoDe(d))}</b> sai das duas pernas: ${esc(d.b)} ${esc((Lb && Lb.texto) || "sem leitura")}
        contra ${esc(d.q)} ${esc((Lq && Lq.texto) || "sem leitura")}. ${s.perna_motivo && s.perna_motivo !== "ambas"
          ? `O motivo está em <b>${esc(s.perna_motivo)}</b>.` : "As duas pernas carregam o motivo."}
        ${s.mesma_aposta && s.mesma_aposta.length
          ? `<span class="mac-mesma">Mesma aposta que ${s.mesma_aposta.map((p) => p.slice(0, 3) + "/" + p.slice(3)).join(", ")} &mdash; segurar dois não diversifica, dobra.</span>` : ""}`;
    } else if (s) {
      nota = `As duas pernas leem igual — não há vantagem entre elas neste eixo.`;
    } else {
      nota = d.diverge
        ? "Os dois bancos centrais se moveram para lados opostos da última vez. É a condição necessária de uma tese fundamental &mdash; não a suficiente."
        : "Os dois bancos centrais se moveram para o mesmo lado da última vez. Não há divergência para operar neste eixo.";
    }

    const a = acaoPartes(d);
    return `<div class="mac-det-topo">
        <h2 class="mac-det-par"><span class="mac-det-acao ${a.cls}">${esc(a.verbo)}</span>
          <span class="mac-det-sigla">${d.b}<em>/</em>${d.q}</span></h2>
        ${pill}
        <span class="mac-det-dado ${velho ? "e-velho" : "e-fresco"}">${idade}</span>
      </div>

      ${resumoPar(d)}

      <details class="mac-det-mais mac-det-nota-wrap"><summary>Como as duas pernas se comparam</summary>
        ${desenhoPernas(d)}
        <p class="mac-det-nota">${nota}</p></details>

      <div class="mac-pernas">${pernaCard(d.b, d.cb, "base")}${pernaCard(d.q, d.cq, "cotada")}</div>

      <details class="mac-det-mais">
        <summary>Como esta leitura é construída, e o que ainda falta</summary>
        <div class="mac-det-mais-corpo">
          <p>Dimensões que VOTAM, nenhuma delas um juro de mercado: <b>dados</b> (surpresas desde a última decisão do banco,
             ponderadas por família e impacto, meia-vida 21 dias), <b>texto</b> (marcadores de alta/corte no que o banco
             disse — e a interface diz a ORIGEM: discurso oficial, comunicado ou ata, imprensa com fala de dirigente,
             ou manchete, que é contexto e não vota) e <b>ciclo</b> (o último movimento, com decaimento pelo tempo
             e pelas reuniões de manutenção que passaram).</p>
          <p>A <b>geopolítica</b> aparece marcada como <b>${SELO_GEO}</b>: não entra no cálculo nem na conta
             "N de M dimensões concordam". Silêncio não é voto — dimensão sem dado não conta, nunca vira zero.</p>
          <p>O par mostra <b>três leituras separadas, nunca somadas</b>: a <b>divergência</b> (quanto as duas pernas
             discordam), a <b>qualidade da evidência</b> (quanto dado sustenta a leitura, que vira o rótulo
             <b>fraca / moderada / forte</b>) e a <b>convicção histórica</b>, que hoje sai como
             <b>ainda não calibrada</b> — só existirá com backtest de amostra declarada.
             Não existe pontuação nesta tela, nem no detalhe, nem em dica de tela.
             Todos os limiares de faixa são <b>provisórios</b>, rotulados como tal, para calibração posterior.</p>
          <p>Uma moeda entra na zona <b>sem leitura</b> quando menos de duas dimensões votam, ou quando o
             sinal fica abaixo do piso provisório sobre o teto das dimensões que votam. Foi o caso que o dono
             apontou: leitura anunciada com apenas duas de quatro dimensões conectadas.</p>
          <p>Qual perna carrega o peso importa. Em 02/set o GBPNZD foi <b>82% kiwi</b>; no mesmo dia o EURJPY foi
             <b>90% iene</b>. Quando o motivo está numa perna, todo par que compartilha essa perna é a mesma aposta.</p>
          <p>Ainda falta: falas próprias existem para Fed, BCE, BoE, BoJ e BoC (RBA e RBNZ bloqueiam automação, o SNB
             não tem feed) — nesses casos o que entra é manchete, marcada como contexto.</p>
          <p>Isto é uma leitura do lado fundamental, não um sinal: o FUND anterior foi encerrado como regra de entrada
             depois de 15 testes nulos. A entrada é sua.</p>
        </div>
      </details>`;
  }

  /* ---------------------------------------------------------- DESENHO DAS DUAS PERNAS
   * (g) No espírito do exemplo do dono:
   *     AUD +0,47  ─────────►
   *     CAD −0,08  ──►
   *     Diferença relativa: +0,55
   *     AUD responde por cerca de 85% da tese.
   * Barras proporcionais em HTML/CSS, com sinal e cor semântica (verde = alta de juro,
   * vermelho = corte). Este é o ÚNICO lugar onde o número contínuo continua aparecendo,
   * e ele fica atrás de um expansível. */
  function desenhoPernas(d) {
    const s = d.s;
    if (!s) return "";
    // A escala continua da perna (o antigo "score") NAO aparece mais em lugar nenhum: nem o
    // numero, nem a palavra. O que fica e a leitura de cada perna em palavras, a forca
    // RELATIVA em barra (sem eixo e sem numero) e a fatia da perna que manda.
    const lb = s.leitura_base || {}, lq = s.leitura_cotada || {};
    const magB = (lb.score == null) ? null : Math.abs(Number(lb.score));
    const magQ = (lq.score == null) ? null : Math.abs(Number(lq.score));
    const maxAbs = Math.max(magB || 0, magQ || 0, 0.01);
    const chaveDir = (dir) => dir === "SOBE" ? "inclinado_alta"
                            : dir === "CORTA" ? "inclinado_corte" : "manutencao";
    const barra = (m, mag, dir) => {
      const L = leituraDe(m);
      const chave = (L && L.chave) || chaveDir(dir);
      const larg = mag === null ? 0 : Math.max(4, Math.round(mag / maxAbs * 100));
      const cls = chave === "inclinado_alta" ? "p" : chave === "inclinado_corte" ? "n" : "z";
      return `<div class="mac-pl-linha">
        <span class="mac-pl-moeda">${FLAG[m] || ""} ${esc(m)}</span>
        <span class="mac-pl-rot ${cls}">${esc((L && L.texto) || ROT_LEITURA[chave] || "sem leitura")}</span>
        <span class="mac-pl-trilho"><i class="mac-pl-barra ${cls}" style="width:${larg}%"></i></span>
      </div>`;
    };
    // perna dominante: campo do nucleo; sem ele, a fracao de cada perna na forca somada
    let dom = null;
    if (s.perna_dominante && s.perna_dominante.moeda) {
      dom = { moeda: s.perna_dominante.moeda, pct: s.perna_dominante.share_pct };
    } else if (s.perna_motivo && s.perna_motivo !== "ambas") {
      dom = { moeda: s.perna_motivo, pct: null };
    } else if (magB !== null && magQ !== null) {
      const soma = magB + magQ;
      if (soma > 0) {
        dom = { moeda: magB >= magQ ? d.b : d.q,
                pct: Math.round((Math.max(magB, magQ) / soma) * 100) };
      }
    }
    return `<div class="mac-pernas-desenho">
      ${barra(d.b, magB, lb.direcao)}
      ${barra(d.q, magQ, lq.direcao)}
      <div class="mac-pl-rodape">
        ${dom ? `<span><b>${esc(dom.moeda)}</b> é a perna que carrega o motivo${
          dom.pct != null ? ` — cerca de <b>${dom.pct}%</b> da tese` : ""}.</span>`
          : `<span>As duas pernas carregam o motivo em partes parecidas.</span>`}
      </div>
      <p class="mac-pl-legenda">Verde = inclinação a subir juro. Vermelho = inclinação a cortar.
        A barra mostra a força de uma perna <b>em relação à outra</b>, nunca um número: não há
        pontuação nesta tela, e barra nenhuma é probabilidade.</p>
    </div>`;
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
    return `<span class="mac-perna-papel" style="margin-top:12px">correlação medida com o juro americano — 5 anos, blocos sem sobreposição</span>
      <div class="mac-eua-tabela"><table class="mac-tabela mac-corr">
        <thead><tr><th>juro</th><th class="mac-num-th">mesmo dia</th><th class="mac-num-th">mesmos 20 d</th>
          <th class="mac-num-th">mesmos 60 d</th>
          <th class="mac-num-th">dia seguinte</th><th class="mac-num-th">5 dias seguintes</th></tr></thead>
        <tbody>${linhas}</tbody></table></div>
      <small class="muted">${esc(C.nota || "")}</small>`;
  }

  // O detalhe de XAUUSD / NQ / ES: uma perna so, o canal, e o que esta medido em casa.
  function detalheInstr(d, idade, velho) {
    const I = d.info;
    if (!I) {
      return `<div class="mac-vazio"><strong>${esc(d.par)}</strong><p>A leitura do dólar ainda não foi construída.</p></div>`;
    }
    const u = I.leitura_usd || {};
    const est = d.estado || null;
    const a = acaoPartes(d);
    // (c) nada de score aqui: o instrumento mostra a divergência e o estado, e o número
    // contínuo fica no expansível das duas pernas, como no par.
    return `<div class="mac-det-topo">
        <h2 class="mac-det-par"><span class="mac-det-acao ${a.cls}">${esc(a.verbo)}</span>
          <span class="mac-det-sigla">${d.rotulo}</span></h2>
        <span class="mac-det-leitura ${est ? CLS_ESTADO[est] : (CLS_SINAL[I.sinal] || "v-nao")}"
              title="faixa provisória, ainda não calibrada por backtest">${
          est ? esc(ROT_ESTADO[est] || est) : (d.tese ? "com tese" : "sem tese")}${
          est ? `<small class="mac-prov-mini">prov.</small>` : ""}</span>
        <span class="mac-det-dado ${velho ? "e-velho" : "e-fresco"}">${idade}</span>
      </div>
      <div class="mac-resumo ${est ? CLS_ESTADO[est] : "e-sem"}${clsAtraso()}">
        ${tarjaAtraso()}
        <div class="mac-resumo-grid mac-resumo-3">
          <div class="mac-resumo-item"><span class="mac-resumo-rot">Divergência</span>
            <strong>${d.conv}<small class="mac-de100">/100</small></strong>
            <div class="mac-barra-forca"><i style="width:${Math.max(2, Math.min(100, d.conv))}%"></i></div>
            <small>quanto o canal do dólar puxa este instrumento</small></div>
          <div class="mac-resumo-item"><span class="mac-resumo-rot">Qualidade da evidência</span>
            <strong>${d.qual == null ? "—" : d.qual + `<small class="mac-de100">/100</small>`}</strong>
            <small>${d.qual == null ? "ainda não informada pelo núcleo" : "vem da perna do dólar"}</small></div>
          <div class="mac-resumo-item"><span class="mac-resumo-rot">Convicção histórica</span>
            <strong class="mac-naocal">ainda não calibrada</strong>
            <small>ainda não calibrada — precisa de backtest com amostra declarada</small></div>
        </div>
        <p class="mac-resumo-estado"><span class="mac-resumo-rot">Estado</span>
          <b>${est ? esc(ROT_ESTADO[est] || est) : (d.tese ? "com tese" : "sem tese")}</b>${
            est && ACAO_ESTADO[est] ? ` — ${ACAO_ESTADO[est]}` : ""}
          <small class="mac-provisorio">faixas provisórias</small></p>
        ${tarjaAlerta(dominanciaDe("USD"), "mac-tarja-dom")}
      </div>
      <p class="mac-det-nota">${esc(I.nome)} é lido por <b>duas pernas</b>: a leitura de juro do dólar,
        invertida (USD ${esc((leituraDe("USD") || {}).texto || ROT_DIR_PT[u.direcao] || "sem leitura")}), mais a <b>geopolítica</b>
        (${esc((I.geo || {}).estado || "não conectada")}) — marcada como <b>${SELO_GEO}</b>.
        ${I.sinal === "SEM_TESE" ? "Hoje as duas pernas se cancelam exatamente." : ""}</p>
      <div class="mac-pernas">
        ${pernaCard("USD", cicloDe("USD"), "a perna que manda")}
        <div class="mac-perna">
          <span class="mac-perna-papel">canal</span>
          <div class="mac-perna-linha">${esc(I.canal)}</div>
          <span class="mac-perna-papel" style="margin-top:12px">medido em casa</span>
          <div class="mac-perna-linha ${/NOT measured|nao medido|não medido/i.test(I.medido) ? "muted" : ""}">${esc(I.medido)}</div>
          ${correlacoesInstr(I)}
        </div>
      </div>
      <p class="mac-eua-nota">${esc(I.aviso)}</p>`;
  }

  /* O CARD DO PAR — (g) TRES NUMEROS SEPARADOS, NUNCA SOMADOS.
   *
   *   Divergência: 37/100
   *   Qualidade da evidência: 58/100
   *   Convicção histórica: ainda não calibrada
   *   Estado: tese moderada — aguardar BO + ZOI
   *
   * Somar os tres num "score" foi exatamente a queixa do dono: vira nota de prova e some a
   * informacao de qual das tres esta fraca. A conviccao historica so existe com backtest de
   * amostra declarada; hoje NAO existe, e sai escrita como nao calibrada — nunca como numero.
   * Mais: proximo evento invalidante, familias independentes e as tarjas de dominancia. */
  function resumoPar(d) {
    const s = d.s;
    if (!s) return "";
    const bs = M.bancos ? M.bancos.bancos : {};
    const forte = (s.perna_dominante && s.perna_dominante.moeda)
                || (s.perna_motivo && s.perna_motivo !== "ambas" ? s.perna_motivo : null);
    const estado = d.estado || null;
    const rotEstado = estado ? (ROT_ESTADO[estado] || estado) : (d.tese ? "com tese" : "sem tese");
    const acaoEstado = estado ? (ACAO_ESTADO[estado] || "") : (d.tese ? "aguardar BO + ZOI" : "nada a fazer");
    const div = d.conv;
    const qual = d.qual;

    // faixas provisorias: o rotulo tem de dizer que sao provisorias (lei do dono)
    const fx = s.faixas_provisorias || regua().faixas_provisorias || null;

    // (4) PROXIMO EVENTO RELEVANTE: o risco mais proximo das duas pernas, que quase nunca e a
    // reuniao. Ele determina ate quando a ZOI e a entrada nova continuam validas.
    // A ORDEM importa: o campo NOVO (proximo_evento_relevante, por perna) vem primeiro.
    // O campo antigo `proximo_evento_invalidante` costuma trazer a propria REUNIAO, que e
    // exatamente o que o dono disse NAO ser o risco mais proximo — ele fica de reserva.
    let inval = null;
    const riscos = [d.b, d.q].map((m) => {
      const ev = eventoRelevante(m);
      return ev ? { evento: ev.titulo, moeda: m, dias: ev.dias, data: null, brt: ev.brt } : null;
    }).filter((r) => r && r.dias !== null && r.dias !== undefined).sort((a, b) => a.dias - b.dias);
    if (riscos.length) {
      inval = riscos[0];
    } else if (s.proximo_evento_invalidante && s.proximo_evento_invalidante.evento) {
      const P = s.proximo_evento_invalidante;
      const dias = (P.dias != null) ? P.dias : (P.data ? diasAte(P.data) : null);
      inval = { evento: P.evento, moeda: P.moeda || "", dias, data: P.data || null, brt: null };
    }
    // a REUNIAO continua sendo o limite final do ciclo, numa linha propria
    const decisoes = [d.b, d.q].map((m) => {
      const b = bs[m];
      const dias = b && b.proxima ? diasAte(b.proxima) : null;
      return { evento: b ? b.sigla : m, moeda: m, dias, data: b ? b.proxima : null };
    }).filter((r) => r.dias !== null).sort((a, b) => a.dias - b.dias);
    const decisao = decisoes[0] || null;
    const invalTxt = !inval ? "sem evento de alto impacto agendado"
      : `${esc(inval.moeda ? inval.moeda + " · " : "")}${esc(inval.evento)} ${esc(quandoTexto(inval.dias))}`;

    // (g) familias independentes que sustentam o sinal, na perna que manda
    const fam = forte ? familiasDe(forte) : null;

    // (h) alertas do par + dominancia de cada perna
    // Dedupe por MOEDA, nao por texto: o nucleo manda o alerta do par ("...da leitura do CAD")
    // e a moeda manda o dela ("...da leitura de dados do CAD, com 3 divulgacoes"). Sao a mesma
    // coisa dita duas vezes — mostrar as duas polui a tarja e apaga o aviso.
    const alertas = [];
    const jaAvisada = new Set();
    const marcaMoeda = (txt) => [d.b, d.q].forEach((m) => {
      if (/única divulgação/i.test(txt) && txt.indexOf(m) >= 0) jaAvisada.add(m);
    });
    if (Array.isArray(s.alertas)) s.alertas.forEach((x) => {
      if (!x) return; const t = String(x);
      if (alertas.includes(t)) return;
      alertas.push(t); marcaMoeda(t);
    });
    [d.b, d.q].forEach((m) => {
      if (jaAvisada.has(m)) return;
      const t = dominanciaDe(m);
      if (t && !alertas.includes(t)) { alertas.push(t); jaAvisada.add(m); }
    });

    const cls = estado ? CLS_ESTADO[estado] : (s.sinal === "BULL" ? "e-mod" : s.sinal === "BEAR" ? "e-mod" : "e-sem");
    return `<div class="mac-resumo ${cls}${clsAtraso()}">
      ${tarjaAtraso()}
      <div class="mac-resumo-grid mac-resumo-3">
        <div class="mac-resumo-item">
          <span class="mac-resumo-rot">Divergência</span>
          <strong>${div}<small class="mac-de100">/100</small></strong>
          <div class="mac-barra-forca"><i style="width:${Math.max(2, Math.min(100, div))}%"></i></div>
          <small>quanto as duas pernas discordam</small>
        </div>
        <div class="mac-resumo-item">
          <span class="mac-resumo-rot">Qualidade da evidência</span>
          <strong>${qual === null || qual === undefined ? "—" : qual + `<small class="mac-de100">/100</small>`}</strong>
          ${qual === null || qual === undefined ? "" :
            `<div class="mac-barra-forca q"><i style="width:${Math.max(2, Math.min(100, qual))}%"></i></div>`}
          <small>${qual === null || qual === undefined
            ? "ainda não informada pelo núcleo"
            : "o elo fraco das duas pernas — quantidade, diversidade, atualidade e confiabilidade"}</small>
        </div>
        <div class="mac-resumo-item">
          <span class="mac-resumo-rot">Convicção histórica</span>
          <strong class="mac-naocal">ainda não calibrada</strong>
          <small>${esc(s.conviccao_historica_nota || "ainda não calibrada — precisa de backtest com amostra declarada")}</small>
        </div>
      </div>

      <p class="mac-resumo-estado"><span class="mac-resumo-rot">Estado</span>
        <b>${esc(rotEstado)}</b>${acaoEstado ? ` — ${esc(acaoEstado)}` : ""}
        <small class="mac-provisorio">faixas provisórias${fx ? "" : " (ainda não publicadas pelo núcleo)"}</small></p>

      ${alertas.map((t) => tarjaAlerta(t, "mac-tarja-dom")).join("")}

      <div class="mac-resumo-linhas">
        <div><span class="mac-resumo-rot">Próximo evento relevante</span> <b>${invalTxt}</b>
          ${inval && inval.brt ? `<small class="muted">· ${esc(inval.brt)} BRT</small>` : ""}
          ${inval && inval.data ? `<small class="muted">· ${esc(inval.data)}</small>` : ""}
          <small class="muted">— até aqui a ZOI e entradas novas seguem válidas</small></div>
        <div><span class="mac-resumo-rot">Próxima decisão</span>
          <b>${decisao ? esc(decisao.moeda + " · " + decisao.evento + " " + quandoTexto(decisao.dias))
                       : "sem data publicada"}</b>
          ${decisao && decisao.data ? `<small class="muted">· ${esc(decisao.data)}</small>` : ""}
          <small class="muted">— o limite final do ciclo</small></div>
        <div><span class="mac-resumo-rot">Famílias independentes</span>
          <b>${fam ? fam.n : "—"}</b>
          <small class="muted">${fam && fam.quais.length
            ? fam.quais.map((x) => esc(ROT_FAMILIA[x] || x)).join(", ")
            : "inflação, emprego, atividade, comunicação — contagem ainda não informada pelo núcleo"}</small></div>
        <div><span class="mac-resumo-rot">Horizonte</span> <b>semanas (swing)</b>
          <small class="muted">leitura do lado fundamental, não é entrada</small></div>
      </div>
    </div>`;
  }

  /* (a) O FILTRO PADRAO E "COM TESE". Os pares em estado sem_tese saem da lista principal —
   * ficam a um clique, em "Mostrar todos". Era a queixa do dono: 28 pares na tela, nenhum
   * marcado como sem tese, e a lista pedindo para operar tudo. */
  const FILTROS = [
    { k: "tese", r: "Com tese", f: (d) => d.tese },
    { k: "todos", r: "Mostrar todos", f: () => true },
    { k: "sem", r: "Sem tese", f: (d) => d.s && !d.tese },
    { k: "perto", r: "Decide em breve", f: (d) => d.dias !== null && d.dias <= 7 },
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
    // O PLACAR responde "qual moeda esta mais hawkish e qual esta mais dovish". Agrupado pela
    // LEITURA em palavras — sem pontuacao, e com as dimensoes que concordam ao lado.
    // (i) a geopolitica nao entra nesta conta.
    const porLeitura = (chave) => S ? Object.keys(S)
      .filter((m) => { const L = leituraDe(m); return L && L.chave === chave; })
      .map((m) => { const L = leituraDe(m);
        return `${FLAG[m] || ""} ${esc(m)} <small>${L.ok}/${L.total}${
          L.evid ? " · " + esc(L.evid) : ""}</small>`; }).join("&nbsp; ") : "";

    const chips = FILTROS.map((x) =>
      `<button type="button" class="mac-chip${x.k === filtro.k ? " on" : ""}" data-mac-filtro="${x.k}">${x.r}</button>`
    ).join("") + `<span class="mac-sep"></span>` + Object.keys(bs).map((m) =>
      `<button type="button" class="mac-chip mac-chip-moeda${m === M.moedaSel ? " on" : ""}" data-mac-moeda="${m}">${m}</button>`
    ).join("");

    const total = PARES.length + instr.length;
    const escondidos = total - lista.length;
    return `<section class="content-section mac-bloco mac-tela">
      <div class="section-title"><div><h2>Pares</h2></div>
        <p>Cada par lido perna por perna: para onde cada banco central está inclinado, e se as duas
           pernas divergem. Uma leitura do lado fundamental &mdash; a entrada é sua.</p></div>

      ${tarjaAtraso()}

      <div class="mac-placar${S ? " mac-placar-3" : ""}${clsAtraso()}">
        ${S ? `<div><span>Inclinado à alta</span><strong>${porLeitura("inclinado_alta") || "&mdash;"}</strong></div>
               <div><span>Em manutenção</span><strong>${porLeitura("manutencao") || "&mdash;"}</strong></div>
               <div><span>Inclinado ao corte</span><strong>${porLeitura("inclinado_corte") || "&mdash;"}</strong></div>`
            : `<div><span>Último movimento para cima</span><strong>${sobe.map((m) => (FLAG[m] || "") + " " + m).join("&nbsp; ")}</strong></div>
               <div><span>Último movimento para baixo</span><strong>${corta.map((m) => (FLAG[m] || "") + " " + m).join("&nbsp; ")}</strong></div>`}
      </div>
      ${S && porLeitura("sem_leitura")
        ? `<p class="mac-placar-sem${clsAtraso()}"><span>Sem leitura</span> ${porLeitura("sem_leitura")}
             <small class="muted">— menos de duas dimensões votando, ou sinal abaixo do piso provisório</small></p>`
        : ""}

      <div class="mac-chips">${chips}</div>
      <p class="mac-conta">${lista.length} de ${total}${instr.length ? ` — ${PARES.length} pares + ${instr.length} instrumentos puxados pelo dólar (ouro, NQ, ES)` : " pares"}${
        filtro.k === "tese" && escondidos > 0 ? ` · ${escondidos} sem tese escondidos — use “Mostrar todos”` : ""}</p>

      <div class="mac-duas">
        <div class="mac-lista">${lista.length
          ? lista.map(itemLista).join("")
          : `<div class="mac-vazio"><strong>Nenhum par com tese agora.</strong>
               <p>Clique em “Mostrar todos” para ver os ${total} pares, inclusive os que estão sem tese.</p></div>`}</div>
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
  /* ==================================================================================
   * (5) SURPRESA E TENDÊNCIA NOS DADOS AMERICANOS.
   *
   * O dono, 05/set: "hoje mostra último, mensal e anual, mas não mostra se surpreendeu".
   * A tabela passa a ser, por evento:
   *     Indicador | Atual | Esperado | Anterior | Surpresa | Média 3m
   *     NFP — Atual +162 mil · Esperado +105 mil · Anterior +74 mil · Surpresa: alta · Média 3m: +91 mil
   *
   * Campos novos de eua_leitura.json: atual, atual_texto, esperado, anterior, surpresa,
   * surpresa_rotulo, media_3m, nivel, casado_com, sem_consenso. Sem eles, cada célula cai no
   * que já existia (valor, mm, aa) e a coluna vazia sai como "sem consenso" ou "—", nunca
   * como número inventado.
   *
   * DOIS CASOS QUE O DONO NOMEOU:
   *   payroll — o Atual é a VARIAÇÃO do mês (+162 mil); o nível (159,1 milhões) é secundário.
   *   CPI     — o destaque é 3,54% ao ano; o índice (332,813) fica secundário.
   * ================================================================================ */
  const FAM_ANUAL = /inflacao|salarios/;      // famílias em que o número que importa é o a/a
  const num1 = (v, casas) => Number(v).toFixed(casas).replace(".", ",");
  const comSinal = (v, casas) => (v > 0 ? "+" : v < 0 ? "−" : "") + num1(Math.abs(v), casas);

  // o número que vale como "Atual" para este indicador
  function euaAtual(r) {
    if (r.atual !== null && r.atual !== undefined) return Number(r.atual);
    if (r.unidade === "mil") return (r.mm === null || r.mm === undefined) ? null : Number(r.mm);
    if (FAM_ANUAL.test(String(r.familia || "")) && r.aa !== null && r.aa !== undefined) return Number(r.aa);
    return (r.valor === null || r.valor === undefined) ? null : Number(r.valor);
  }

  // formata um valor NA MESMA unidade do "Atual" — serve para esperado, anterior e média 3m
  function euaFmt(r, v) {
    if (v === null || v === undefined || isNaN(Number(v))) return "—";
    const n = Number(v);
    if (r.unidade === "mil") return comSinal(n, 0) + " mil";
    if (FAM_ANUAL.test(String(r.familia || ""))) return num1(n, 2) + "%";
    if (r.unidade === "pp") return num1(n, 1) + "%";
    return num1(n, 2);
  }

  // o NÍVEL, secundário: o payroll em milhões, o CPI como índice
  function euaNivel(r) {
    const nv = (r.nivel !== null && r.nivel !== undefined) ? Number(r.nivel)
             : (r.valor !== null && r.valor !== undefined) ? Number(r.valor) : null;
    if (nv === null || isNaN(nv)) return null;
    if (r.unidade === "mil") return "nível " + num1(nv / 1000, 1) + " milhões";
    if (/inflacao/.test(String(r.familia || ""))) return "índice " + num1(nv, 3);
    if (/salarios/.test(String(r.familia || ""))) return "nível " + num1(nv, 2);
    return null;   // desemprego e participação: o nível JÁ é o "Atual"
  }

  /* Rótulo da surpresa em português. O contrato grava "hawkish"/"dovish"/"neutra"; a tela é
   * toda em português, então o rótulo sai traduzido — lei da casa, zero inglês. */
  const ROT_SURPRESA = { hawkish: "empurra à alta", dovish: "empurra ao corte", neutra: "neutra",
                         neutral: "neutra" };
  const CLS_SURPRESA = { hawkish: "positive", dovish: "negative", neutra: "muted", neutral: "muted" };

  /* O bloco dos EUA na Visão geral. Direto do BLS e do Fed, sem intermediário.
   * Dois relógios separados de propósito: o mês que o dado DESCREVE (referência, universal —
   * a Bloomberg tem a mesma) e o tempo do release até aqui (entrega). */
  function painelEUA() {
    const U = M.eua;
    if (!U || !U.indicadores) return "";
    const I = U.indicadores;
    const ORDEM = ["CUSR0000SA0", "CUSR0000SA0L1E", "CES0000000001", "LNS14000000",
                   "CES0500000003", "LNS11300000"];

    const linhas = ORDEM.filter((k) => I[k]).map((k) => {
      const r = I[k];
      const at = euaAtual(r);
      // o núcleo grava "+162k"; a tela é em português e o dono pediu "+162 mil"
      const atTxt = (r.atual_texto ? String(r.atual_texto).replace(/(\d)\s*[kK]\b/g, "$1 mil")
                                   : euaFmt(r, at));
      const nv = euaNivel(r);
      const semCons = !!r.sem_consenso || (r.esperado === null || r.esperado === undefined);
      const surp = (r.surpresa === null || r.surpresa === undefined) ? null : Number(r.surpresa);
      const rot = r.surpresa_rotulo || null;
      return `<tr>
        <td>${esc(r.nome_pt || r.nome)}${r.preliminar
          ? ' <span class="mac-prelim" title="o BLS ainda revisa os dois dados seguintes">preliminar</span>' : ""}
          <small class="muted mac-ref-td">${esc(r.referencia || "")}</small>
          ${r.casado_com && r.casado_com.titulo
            ? `<small class="muted mac-eua-casado">casado com ${esc(r.casado_com.titulo)}</small>` : ""}</td>
        <td class="mac-num-td"><b>${esc(atTxt)}</b>${
          nv ? `<small class="muted mac-eua-nivel">${esc(nv)}</small>` : ""}</td>
        <td class="mac-num-td">${semCons
          ? `<small class="muted">sem consenso</small>`
          : esc(euaFmt(r, r.esperado))}</td>
        <td class="mac-num-td">${esc(euaFmt(r, r.anterior))}</td>
        <td class="mac-num-td">${(semCons || surp === null)
          ? `<small class="muted">sem consenso</small>`
          : `<span class="mac-surp ${rot ? (CLS_SURPRESA[rot] || "muted") : "muted"}">${
              esc(euaFmt(r, surp))}${rot ? " · " + esc(ROT_SURPRESA[rot] || rot) : ""}</span>`}</td>
        <td class="mac-num-td muted">${esc(euaFmt(r, r.media_3m))}</td></tr>`;
    }).join("");

    const f = U.fomc && U.fomc.proxima;
    const b = M.bancos && M.bancos.bancos && M.bancos.bancos.USD;
    let fomc = "";
    if (f && f.data) {
      const dias = diasAte(f.data);
      fomc = `<div class="mac-eua-fomc">
        <span class="mac-perna-papel">Próxima decisão do FOMC</span>
        <div class="mac-eua-dias">${dias <= 0 ? "hoje" : dias} <small>${
          dias <= 0 ? "" : dias === 1 ? "dia" : "dias"}</small></div>
        <div class="mac-perna-linha">${esc(mesPt(f.rotulo))} &middot; ${esc(f.data)}</div>
        ${f.com_projecoes ? '<span class="mac-dot" title="a reunião que publica o caminho de juro do próprio comitê — a que mais move o preço">com projeções · mapa de pontos</span>' : ""}
        ${b ? `<div class="mac-perna-linha muted mac-eua-taxa">Juro do Fed <b>${esc(b.taxa_texto)}</b>
          <small>&middot; último movimento ${esc(b.ultima_mudanca || "")}${b.ultima_mudanca_bp ? " (" + (b.ultima_mudanca_bp > 0 ? "+" : "") + b.ultima_mudanca_bp + " pb)" : ""}</small></div>` : ""}
      </div>`;
    }

    const refs = Object.values(I).map((r) => r.referencia).filter(Boolean).sort();
    const ref = refs.length ? refs[refs.length - 1] : null;
    const atrasoRef = U.defasagem_referencia_meses;
    const L = M.eventos && M.eventos.latencia_medida;
    const entrega = (L && L.mediana_alta != null)
      ? `da divulgação até a fonte do calendário, medido por evento: os dados de alto impacto levam
         ${fmtAtraso(L.mediana_alta)} (mediana) — veja cada ficha; da divulgação até a API do BLS,
         ainda não cronometrado, depende da chave registrada`
      : "ainda não medida";

    const fed = ((U.fed && U.fed.ultimos) || []).slice(0, 3).map((x) =>
      `<li><span class="muted">${esc((x.publicado || "").slice(0, 16))}</span> ${
        x.link ? `<a href="${esc(x.link)}" target="_blank" rel="noopener">${esc(x.titulo || "")}</a>`
               : esc(x.titulo || "")}</li>`).join("");

    return `<section class="content-section mac-bloco mac-eua">
      <div class="section-title"><div><h2>Estados Unidos</h2></div>
        <p>Uma das pernas na maioria dos pares, e o juro a que ouro, NQ e ES respondem. Lido direto
           do BLS e do Fed, sem intermediário. Cada linha mostra <b>se o dado surpreendeu</b> — o
           número sozinho não diz nada sem o que se esperava dele.</p></div>
      <div class="mac-eua-grid">
        ${fomc}
        <div class="mac-eua-tabela">
          <table class="mac-tabela">
            <thead><tr><th>Indicador</th><th class="mac-num-th">Atual</th><th class="mac-num-th">Esperado</th>
              <th class="mac-num-th">Anterior</th><th class="mac-num-th">Surpresa</th>
              <th class="mac-num-th">Média 3m</th></tr></thead>
            <tbody>${linhas}</tbody>
          </table>
        </div>
      </div>
      <p class="mac-eua-nota">${ref ? `Os dados mais recentes descrevem <b>${esc(ref)}</b>${
          atrasoRef != null ? ` — ${atrasoRef} ${atrasoRef === 1 ? "mês" : "meses"} atrás` : ""}. Esse é o mês que
        terminou, não um atraso de entrega; todo terminal carrega a mesma defasagem.` : ""}
        Entrega (da divulgação até aqui): <b>${entrega}</b>.
        Onde não há consenso publicado, a coluna diz <b>sem consenso</b> — a surpresa não pode ser
        medida e nenhum número é inventado no lugar.</p>
      ${falasDoFed()}
      ${fed ? `<details class="mac-det-mais mac-eua-fed"><summary>Últimas publicações do Fed</summary>
        <ul>${fed}</ul></details>` : ""}
    </section>`;
  }

  /* ==================================================================================
   * (3) AS FALAS, POR ORADOR — VEREDITO, NÃO CONTAGEM.
   *
   * Os casos que o dono viu em 05/set: Waller disse que apoiaria MANTER os juros e o painel
   * marcou "hawkish"; Warsh falou em preservar liberdade para decidir, o que não é alta nem
   * corte; Barr é de alta mas CONDICIONAL ("se a inflação não moderar"). Contagem de palavras
   * não lê negação, não lê condição e não lê referência temporal.
   *
   * Entra o veredito por orador que o classificador novo grava
   * (dimensoes.texto.veredito_por_orador), cada um com o trecho que justificou, num
   * expansível, e o link. Enquanto o classificador não estiver validado, a seção inteira leva
   * o mesmo selo da geopolítica: CONTEXTO, SEM VOTO.
   *
   * Sem o campo, a interface NÃO cai de volta na contagem — ela diz que o veredito ainda não
   * foi classificado. Mostrar contagem como se fosse leitura é o erro que está sendo corrigido.
   * ================================================================================ */
  const SELO_FALAS = "experimental — contexto, não vota";
  const ROT_VEREDITO = {
    "manutenção": "manutenção", manutencao: "manutenção",
    alta: "alta", corte: "corte",
    "alta condicional": "alta condicional", "corte condicional": "corte condicional",
    indeterminado: "indeterminado",
  };
  const CLS_VEREDITO = {
    alta: "v-alta", "alta condicional": "v-alta-cond",
    corte: "v-corte", "corte condicional": "v-corte-cond",
    "manutenção": "v-mantem", manutencao: "v-mantem", indeterminado: "v-indet",
  };

  // O nome da seção depende da ORIGEM. "discursos" só quando é discurso oficial ou
  // comunicado/ata — nunca para manchete. Foi o erro que o dono viu no AUD.
  function nomeSecaoTexto(m) {
    const s = sentDe(m);
    const v = s && s.dimensoes && s.dimensoes.texto;
    if (v && (v.origem === "discurso_oficial" || v.origem === "comunicado_ata")) {
      return v.origem === "comunicado_ata" ? "comunicados e atas" : "discursos";
    }
    if (v && v.origem) return "manchetes (contexto)";
    // sem o campo: decide pelo feed de discursos que estiver em casa
    const itens = (M.discursos && Array.isArray(M.discursos.itens)) ? M.discursos.itens : [];
    const tem = itens.some((x) => (x.moeda || "USD") === m &&
      (x.origem === "discurso_oficial" || x.origem === "comunicado_ata"));
    return tem ? "discursos" : "manchetes (contexto)";
  }

  function vereditosDe(m) {
    const s = sentDe(m);
    const v = s && s.dimensoes && s.dimensoes.texto;
    const lista = v && Array.isArray(v.veredito_por_orador) ? v.veredito_por_orador : null;
    return (lista && lista.length) ? lista : null;
  }

  // uma linha "Waller — manutenção", com o trecho num expansível e o link
  function linhaVeredito(x) {
    const ver = ROT_VEREDITO[x.veredito] || x.veredito || "indeterminado";
    const cls = CLS_VEREDITO[x.veredito] || "v-indet";
    const trecho = x.trecho || x.frase || null;
    return `<li class="mac-fala">
      <div class="mac-fala-topo">
        ${x.data ? `<span class="muted mac-ref-td">${esc(String(x.data).slice(0, 10))}</span>` : ""}
        <strong>${esc(x.orador || "orador não identificado")}</strong>
        <span class="mac-veredito ${cls}">&mdash; ${esc(ver)}</span>
        ${x.link ? `<a class="mac-fala-link" href="${esc(x.link)}" target="_blank" rel="noopener">abrir a fonte</a>` : ""}
      </div>
      ${x.motivo ? `<div class="mac-fala-motivo">${esc(x.motivo)}</div>` : ""}
      ${trecho ? `<details class="mac-fala-trecho"><summary>o trecho que justificou</summary>
        <blockquote class="mac-fala-frase">“${esc(String(trecho).slice(0, 400))}${
          String(trecho).length > 400 ? "…" : ""}”</blockquote></details>` : ""}
    </li>`;
  }

  // Queda sem o campo novo: os itens do feed, SEM contagem de marcadores.
  function falasSemVeredito(m) {
    const D = M.discursos;
    if (!D || !Array.isArray(D.itens)) return "";
    const itens = D.itens.filter((x) => (x.moeda || "USD") === m).slice(0, 4);
    if (!itens.length) return "";
    return itens.map((x) => {
      const f = (x.frases && x.frases[0] && x.frases[0].frase) || "";
      return `<li class="mac-fala">
        <div class="mac-fala-topo"><span class="muted mac-ref-td">${esc(x.data || "")}</span>
          <strong>${esc(x.orador || "orador não identificado")}</strong>
          <span class="mac-veredito v-indet">&mdash; veredito ainda não classificado</span>
          ${x.link ? `<a class="mac-fala-link" href="${esc(x.link)}" target="_blank" rel="noopener">${
            esc((x.titulo || "abrir a fonte").slice(0, 70))}</a>` : ""}</div>
        ${f ? `<details class="mac-fala-trecho"><summary>o trecho extraído</summary>
          <blockquote class="mac-fala-frase">“${esc(f.slice(0, 300))}${f.length > 300 ? "…" : ""}”</blockquote>
          </details>` : ""}
      </li>`;
    }).join("");
  }

  function falasDeMoeda(m) {
    const vs = vereditosDe(m);
    const corpo = vs ? vs.map(linhaVeredito).join("") : falasSemVeredito(m);
    if (!corpo) return "";
    return `<div class="mac-falas">
      <div class="mac-falas-titulo">
        <span class="mac-perna-papel">O que os dirigentes disseram &mdash; ${esc(nomeSecaoTexto(m))}</span>
        <small class="mac-selo">${SELO_FALAS}</small></div>
      <ul>${corpo}</ul>
      <p class="mac-falas-nota">${vs
        ? "Veredito por orador, lido do texto: negação, condição e referência temporal entram na " +
          "classificação. Enquanto o classificador não for validado contra desfecho, isto é " +
          "<b>contexto e não vota</b> — exatamente como a geopolítica."
        : "O classificador de postura ainda não gravou veredito para estes itens. Contagem de " +
          "palavras não lê negação nem condição, então <b>nenhuma contagem é exibida como leitura</b>."}</p>
    </div>`;
  }

  function falasDoFed() { return falasDeMoeda("USD"); }

  /* ------------------------------------------------------------- GEOPOLITICA */

  // A camada de CONTEXTO: intensidade do noticiario por moeda (GDELT), com a implicacao por
  // REGRA DECLARADA ao lado. Nao entra na conviccao — filtro novo passa por medicao antes de
  // pontuar (lei da casa; o DXY foi reprovado nas 88 operacoes por ter sido assumido).
  function zPill(v, rotulo) {
    if (!v || v.z === null || v.z === undefined) return `<span class="mac-geo-pill off">${esc(rotulo)} —</span>`;
    const cls = v.z >= 2 ? "alto" : v.z >= 1 ? "medio" : v.z <= -1 ? "baixo" : "";
    return `<span class="mac-geo-pill ${cls}" title="volume de artigos de 3 dias contra a média diária de 14 dias: razão ${v.razao ?? "?"}×, z ${v.z}">${rotulo} <b>z ${v.z > 0 ? "+" : ""}${v.z}</b> <small>${v.razao ?? "?"}×</small></span>`;
  }

  /* (6) MANCHETES DEDUPLICADAS, COM FONTE E CONFIABILIDADE.
   *
   * O dono viu duas manchetes lado a lado descrevendo o MESMO ataque. O núcleo passa a
   * gravar `manchetes_unicas`, com as fontes que republicaram e um rótulo de confiabilidade.
   * Sem o campo novo, cai na lista antiga — sem inventar confiabilidade que ninguém mediu. */
  const ROT_CONF = { alta: "confiabilidade alta", media: "confiabilidade média",
                     baixa: "confiabilidade baixa" };
  const CLS_CONF = { alta: "c-alta", media: "c-media", baixa: "c-baixa" };

  function manchetesHtml(bloco, n) {
    // aceita o bloco do tema (com manchetes_unicas) ou a lista antiga, direto
    const unicas = (bloco && Array.isArray(bloco.manchetes_unicas)) ? bloco.manchetes_unicas : null;
    const lista = unicas || (Array.isArray(bloco) ? bloco : (bloco && bloco.manchetes) || []);
    const dup = (bloco && bloco.duplicatas_removidas) || 0;
    const li = (lista || []).slice(0, n).map((m) => {
      const fontes = Array.isArray(m.fontes) ? m.fontes : (m.fonte ? [m.fonte] : []);
      const rep = (m.n_republicacoes != null) ? Number(m.n_republicacoes) : null;
      const conf = m.confiabilidade || null;
      return `<li><a href="${esc(m.url || m.link || "#")}" target="_blank" rel="noopener">${
          esc(m.titulo || "")}</a>
        <small class="muted">${esc(fontes.join(", ") || "fonte não identificada")}${
          m.quando ? " · " + esc(String(m.quando).slice(0, 8)) : ""}</small>
        ${conf ? `<small class="mac-conf ${CLS_CONF[conf] || ""}">${esc(ROT_CONF[conf] || conf)}</small>` : ""}
        ${rep && rep > 1 ? `<small class="muted">republicada em ${rep} sites</small>` : ""}</li>`;
    }).join("");
    return li + (unicas && dup
      ? `<li class="muted mac-geo-dup"><small>${dup} ${dup === 1 ? "matéria repetida removida"
          : "matérias repetidas removidas"} desta lista</small></li>` : "");
  }

  /* (6) A GEOPOLÍTICA VEM RECOLHIDA POR PADRÃO.
   * Pedido do dono: ocupa muito espaço apesar de não votar. O selo continua em toda parte. */
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
          ${zPill(conf.volume, "conflito")} ${zPill(ener.volume, "energia")}
          ${b.tom !== null && b.tom !== undefined ? `<small class="muted" title="tom médio do GDELT em 7 dias">tom ${b.tom > 0 ? "+" : ""}${b.tom}</small>` : ""}</div>
        ${imp.fx || imp.juro ? `<div class="mac-geo-imp">${imp.fx ? `<span>${esc(imp.fx)}</span>` : ""}${imp.juro ? `<span>${esc(imp.juro)}</span>` : ""}</div>` : ""}
        <ul class="mac-geo-lista">${manchetesHtml(conf, 2)}${manchetesHtml(ener, 1)}</ul>
      </div>`;
    }).join("");

    return `<section class="content-section mac-bloco mac-geo">
      <details class="mac-geo-det">
        <summary><span class="mac-geo-sum">Geopolítica <small class="mac-selo">${SELO_GEO}</small>
          <small class="muted">— clique para abrir</small></span></summary>
        <div class="section-title"><div></div>
          <p>Intensidade do noticiário por moeda: artigos dos últimos 3 dias contra a média diária de
             14 dias, do GDELT. A implicação ao lado de cada cartão é uma <b>regra declarada</b> — ela
             não conta na leitura enquanto não for medida, e por isso a seção vem recolhida.</p></div>
        <div class="mac-geo-mundo">
          <span class="mac-perna-papel">Pano de fundo do mundo</span>
          ${zPill((W.conflito || {}).volume, "conflito")} ${zPill((W.energia || {}).volume, "energia")}
          <ul class="mac-geo-lista">${manchetesHtml(W.conflito || {}, 2)}${manchetesHtml(W.energia || {}, 1)}</ul>
        </div>
        <div class="mac-geo-grid">${cards}</div>
        <p class="mac-eua-nota">Regra, não medição: um pico de conflito tende a mandar fluxo para USD,
          CHF e JPY e a tirar de AUD, NZD e CAD; um pico de energia é empurrão de inflação para quem
          importa. A hipótese a testar antes que isto entre na leitura: um z de conflito ≥ 2 muda o
          retorno de 20 dias das moedas de risco?</p>
      </details>
    </section>`;
  }

  // linha de contexto no cartao da perna
  function geoPerna(m) {
    const G = M.geo && M.geo.moedas && M.geo.moedas[m];
    if (!G) return "";
    const conf = ((G.temas || {}).conflito || {}).volume;
    const ener = ((G.temas || {}).energia || {}).volume;
    const imp = G.implicacao || {};
    // (i) a geopolitica aparece marcada em TODA a interface e nao entra em conta nenhuma
    return `<div class="mac-perna-linha mac-perna-geo"><span class="mac-perna-papel">geopolítica
        <small class="mac-selo">${SELO_GEO}</small></span>
      ${zPill(conf, "conflito")} ${zPill(ener, "energia")}
      ${imp.fx || imp.juro ? `<small class="muted">${esc(imp.fx || imp.juro)}</small>` : `<small class="muted">sem pico nesta semana</small>`}</div>`;
  }

  /* ---------------------------------------------------------------- NOTICIAS */

  // A aba News deixa de ser o feed antigo e vira as manchetes por moeda (noticias.py, Google
  // News RSS): todas as oito, ultimas 72 h, com a contagem alta/corte/manutencao ao lado.
  function painelNoticias() {
    const N = M.noticias;
    if (!N || !N.moedas) return "";
    const sel = M.moedaNews || "USD";
    const chips = Object.keys(FLAG).filter((m) => N.moedas[m]).map((m) => {
      const c = N.moedas[m].contagem || {};
      return `<button type="button" class="mac-chip mac-chip-moeda${m === sel ? " on" : ""}" data-mac-news="${m}">${FLAG[m] || ""} ${m}
        <small class="mac-news-cont">${c.alta || 0}▲ ${c.corte || 0}▼</small></button>`;
    }).join("");
    const B = N.moedas[sel] || { itens: [], contagem: {} };
    const c = B.contagem || {};
    const lista = (B.itens || []).map((it) => `<li class="mac-news-item${it.classe ? " c-" + it.classe : ""}">
        <span class="muted mac-ref-td">${esc(brt(it.quando_utc) || "")}</span>
        <a href="${esc(it.link || "#")}" target="_blank" rel="noopener">${esc(it.titulo)}</a>
        <small class="muted">${esc(it.fonte || "")}</small>
        ${it.classe ? `<span class="mac-news-tag c-${it.classe}">${{ alta: "alta", corte: "corte", mantem: "manutenção" }[it.classe]}</span>` : ""}
      </li>`).join("");
    const g = N.gerado_em ? Math.round((Date.now() - new Date(N.gerado_em).getTime()) / 60000) : null;
    return `<section class="content-section mac-bloco mac-news">
      <div class="section-title"><div><h2>Notícias por moeda</h2></div>
        <p>Manchetes sobre cada banco central e cada economia nas últimas 72 horas, pelo feed de busca
           do Google Notícias. A etiqueta é <b>contagem de expressão no título</b> — um indicador do que
           ler, nunca uma leitura, e ela não vota. Para RBA, RBNZ e SNB, que bloqueiam automação, esta
           é também a fonte de reserva da dimensão de texto: entra como <b>manchete (contexto)</b>.</p></div>
      <div class="mac-chips">${chips}</div>
      <p class="mac-conta">${FLAG[sel] || ""} ${sel} · ${B.n_72h || 0} manchetes em 72 h · alta ${c.alta || 0} · corte ${c.corte || 0} · manutenção ${c.mantem || 0}${
        g !== null ? ` · <span class="${g > 240 ? "mac-velho" : "mac-fresco"}">coletadas ${idadeTexto(g)}</span>` : ""}</p>
      <ul class="mac-news-lista">${lista || "<li class='muted'>nenhuma manchete na janela</li>"}</ul>
    </section>`;
  }

  document.addEventListener("click", function (e) {
    const alvo = e.target.closest ? e.target.closest("[data-mac-news]") : null;
    if (!alvo) return;
    M.moedaNews = alvo.dataset.macNews;
    const painel = document.querySelector('[data-panel="news"]');
    if (painel) {
      try { painel.innerHTML = painelNoticias(); }
      catch (err) { console.warn("[macro] painelNoticias falhou e foi contido:", err.message); }
    }
  }, true);

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
      ${decisao ? `<span class="mac-decisao">${FLAG[decisao.moeda] || ""} ${esc(decisao.moeda)} decide</span>` : ""}
      ${top.map((e) => `<span class="mac-ev ${String(e.impacto).toLowerCase() === "high" ? "alto" : ""}">
          ${FLAG[e.moeda] || ""} ${esc(e.titulo || "")}</span>`).join("")}
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
           title="tempo entre a hora agendada da divulgação e o valor aparecer na fonte — carimbo tardio costuma ser uma revisão posterior retocando o registro, não um primeiro dado atrasado">chegou +${fmtAtraso(e.atraso_s)}</span>`
      : "";
    // diferenca de TAXA (juro, desemprego) e em pontos percentuais, nao em "%"
    const unSurp = (e.unidade === "%" && (e.familia === "decisao" || e.familia === "desemprego")) ? "pp" : e.unidade;
    const surp = (saiu && temPrev && e.diferenca !== null && e.diferenca !== undefined)
      ? `<span class="mac-surp ${e.empurrao > 0 ? "positive" : e.empurrao < 0 ? "negative" : "muted"}">${
          Number(e.diferenca) === 0 ? "igual ao esperado"
            : (e.diferenca > 0 ? "+" : "") + fmtN(e.diferenca, unSurp) + " contra o esperado"}</span>`
      : "";
    // resultado ausente: "not out" so vale quando a hora ainda nao chegou. Se ja passou e a
    // fonte de reserva esta ativa, a verdade e outra: a reserva nao carrega o resultado.
    const fonteReserva = M.eventos && M.eventos.fonte && M.eventos.fonte !== "fxstreet";
    const jaPassou = e.quando_utc && new Date(e.quando_utc).getTime() < Date.now();
    const semResultado = !saiu && jaPassou
      ? (fonteReserva ? "a fonte reserva não carrega o resultado" : "ainda não está na fonte")
      : "ainda não saiu";
    const ROT_CLASSE = { EM_LINHA: "em linha", MUITO_ACIMA: "muito acima", MUITO_ABAIXO: "muito abaixo" };
    const revis = (e.revisado !== null && e.revisado !== undefined)
      ? ` <small class="muted">→ revisado para ${fmtN(e.revisado, e.unidade)}</small>` : "";

    let barra;
    if (e.discurso) {
      barra = `<div class="mac-barra mac-sem"><span>é um discurso — não há número para medir; o texto é a divulgação</span></div>`;
    } else if (temPrev || saiu) {
      barra = `<div class="mac-barra">
           <span>esperado <b>${fmtN(e.previsao, e.unidade)}</b></span>
           <span>anterior <b>${fmtN(e.anterior, e.unidade)}</b>${revis}</span>
           <span>atual <b>${saiu ? fmtN(e.resultado, e.unidade) : semResultado}</b>${surp}</span>
           ${atraso}</div>` +
        (saiu && !temPrev
          ? `<div class="mac-barra mac-sem"><span>divulgado sem consenso publicado — a surpresa não pode ser medida</span></div>`
          : "");
    } else {
      barra = `<div class="mac-barra mac-sem"><span>sem consenso publicado — a surpresa não pode ser medida</span></div>`;
    }

    const leitura = e.estado === "DIVULGADO"
      ? `<p class="mac-leitura ${e.empurrao > 0 ? "positive" : e.empurrao < 0 ? "negative" : "muted"}">
           <strong>${esc(ROT_CLASSE[e.classe] || e.classe || "")}</strong> — ${esc(e.empurrao_texto)}</p>`
      : "";
    const avisos = [
      e.data_a_confirmar ? "horário a confirmar" : "",
      e.preliminar ? "dado preliminar" : "",
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
      return `<div class="mac-vazio"><strong>Nenhuma divulgação agendada neste dia.</strong></div>`;
    }
    const ordem = { high: 0, medium: 1, low: 2 };
    ev.sort((a, b) => (ordem[String(a.impacto).toLowerCase()] ?? 3) -
                      (ordem[String(b.impacto).toLowerCase()] ?? 3) ||
                      String(a.quando_utc).localeCompare(String(b.quando_utc)));
    return ev.filter((e) => String(e.impacto).toLowerCase() !== "low").map(fichaEvento).join("")
        || `<div class="mac-vazio"><strong>Só divulgações de baixo impacto neste dia.</strong></div>`;
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
    // Depois da tradução do index.html o texto virou "MAIS FORTE": o teste em inglês
    // deixou de casar e a fileira vazia voltou a aparecer (visto em 05/set). Testa os dois.
    const overview = document.querySelector("section.overview");
    if (overview && /STRONGEST|MAIS FORTE/i.test(overview.textContent || "")) overview.remove();

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
      sys.textContent = "Painel de leitura. Ele dá o lado fundamental; a entrada é sua.";
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
      if (/^outside neutral$/i.test(t) || /^fora do neutro$/i.test(t) || /^\|FUND\|/i.test(t)) {
        const cartao = el.closest(".metric-card, .kpi, .summary-card") || el;
        cartao.remove();
      }
    });

    // textos herdados, inclusive dois em portugues num site que e todo em ingles
    const TROCA = [
      [/FUND decides FX macro\./i,
       "O Macro Direction lê os bancos centrais."],
      [/EQUITIES\s*[—-]\s*unidade e a EMPRESA\.\s*Nao usa FUND nem par de moeda\./i,
       "AÇÕES — a unidade aqui é a EMPRESA. Nada de pares de moeda."],
      [/Different house, different method\. No FUND here, no currency pairs\./i,
       "Outra casa, outro método. Aqui não há par de moedas."],
      [/HCI FUND Radar/i, "HCI Macro Direction"],   // nome próprio, não se traduz
      [/The single input the FUND is built from\..*$/i,
       "Juro soberano de 2 anos, mantido só como contexto. Ele não alimenta a leitura — " +
       "é publicado em D+1, depois que a moeda já andou."],
      [/Causal selection: only the FUND of the day itself.*$/i,
       "Cada dia mostra as divulgações agendadas e o que cada uma empurra na decisão de juro."],
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
      sys2.textContent = "Painel de leitura. Ele dá o lado fundamental; a entrada é sua.";
    }

    // o rodape ainda descrevia o FUND: "Sovereign 2-year yield momentum across 28 FX crosses"
    document.querySelectorAll("footer p, .site-footer p, footer small").forEach((el) => {
      if (el.children.length) return;
      if (/2-year yield momentum|yield momentum across/i.test(el.textContent || "")) {
        el.textContent = "Leitura dos bancos centrais em 28 pares de moedas. Ela dá o lado "
          + "fundamental de cada perna — entrada, tamanho e execução seguem discricionários.";
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
    if (tit) tit.textContent = M.mes.toLocaleDateString("pt-BR",
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
        ${dec ? `<span class="mac-decisao">${FLAG[dec.moeda] || ""} ${esc(dec.moeda)} decide</span>` : ""}
        ${ev.slice(0, 3).map((e) => `<span class="mac-ev${
            String(e.impacto).toLowerCase() === "high" ? " alto" : ""}">${
            FLAG[e.moeda] || ""} ${esc(e.titulo || "")}</span>`).join("")}
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
        <div><h2>${iso ? "O que acontece em " + iso.split("-").reverse().join("/")
                        : "Leitura do dia"}${M.moedaCal ? ` <small class="muted">· só ${FLAG[M.moedaCal] || ""} ${esc(M.moedaCal)}</small>` : ""}</h2></div>
        <p>${iso ? (ev.length
              ? "Cada divulgação, contra o que ela é medida, e o que cada desfecho empurraria na decisão de juro."
              : (M.moedaCal ? `Nada acima de baixo impacto para ${esc(M.moedaCal)} neste dia.`
                            : "Nada acima de baixo impacto agendado neste dia."))
            : "Escolha um dia no calendário acima."}</p></div>
      <div class="mac-dia">${iso ? painelDoDia(iso)
        : '<div class="mac-vazio"><strong>Escolha um dia no calendário acima.</strong></div>'}</div>`;
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
    { r: "Análise",  abas: ["ratesfx", "spreads"] },
    { r: "Método",   abas: ["sources"] },
    { r: "Ações",    abas: ["equities"] },
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
      rot.textContent = "Outros";
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

  // Antes de substituir o miolo de um painel, os elementos com id que o app.js antigo ainda
  // escreve (#newsList, #calendarGrid, #pairTableBody...) sao MOVIDOS para um contêiner
  // oculto. Destrui-los fazia o app.js estourar em null e imprimir "Could not load the
  // radar" no topo — o revisor externo viu isso em 04/set. Mover preserva ouvintes e deixa
  // o app.js escrever onde ninguem ve.
  function recolheLegado(painel) {
    if (!painel) return;
    let sink = document.getElementById("macSink");
    if (!sink) {
      sink = document.createElement("div");
      sink.id = "macSink";
      sink.hidden = true;
      sink.setAttribute("aria-hidden", "true");
      document.body.appendChild(sink);
    }
    painel.querySelectorAll("[id]").forEach((el) => {
      if (el.closest("#macSink")) return;
      sink.appendChild(el);
    });
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
      if (h) { recolheLegado(over); over.innerHTML = h; }
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

    // NOTICIAS: a aba News vira as manchetes por moeda
    const news = document.querySelector('[data-panel="news"]');
    if (news && !news.querySelector(".mac-bloco")) {
      const h = contido("painelNoticias", painelNoticias);
      if (h) { recolheLegado(news); news.innerHTML = h; }
    }

    // PARES: o mesmo, ate o leitor produzir
    const pares = document.querySelector('[data-panel="pairs"]');
    if (pares && !pares.querySelector(".mac-bloco")) {
      const h = contido("matrizPares", matrizPares);
      if (h) { recolheLegado(pares); pares.innerHTML = h; }
    }

    // CALENDARIO: grade PROPRIA.
    // A grade do FUND era montada a partir dos dias que existiam no historico dele — por isso
    // nao passava de 31/08 e nao conseguia mostrar setembro. Um calendario do que VAI acontecer
    // tem que ser dirigido por DATA, nao por dado historico. Entao construimos a nossa.
    const painelCal = document.querySelector('[data-panel="calendar"]');
    if (painelCal && !painelCal.querySelector(".mac-cal")) {
      recolheLegado(painelCal);
      painelCal.innerHTML = `<section class="content-section mac-bloco">
          <div class="section-title"><div><h2>Calendário macro</h2></div>
            <p>Divulgações agendadas e decisões de banco central. Escolha um dia para ler o que cada
               uma empurraria na decisão de juro. Todos os horários em BRT.</p></div>
          <div class="mac-chips mac-cal-chips">
            <button type="button" class="mac-chip on" data-mac-cal-moeda="">Todas as moedas</button>
            ${Object.keys(FLAG).map((m) =>
              `<button type="button" class="mac-chip mac-chip-moeda" data-mac-cal-moeda="${m}">${FLAG[m]} ${m}</button>`).join("")}
          </div>
          <div class="mac-navmes">
            <button type="button" class="mac-nav" data-mac-mes="-1">◀</button>
            <strong class="mac-mes-titulo"></strong>
            <button type="button" class="mac-nav" data-mac-mes="1">▶</button>
          </div>
          <div class="mac-semana">
            <span>Seg</span><span>Ter</span><span>Qua</span><span>Qui</span>
            <span>Sex</span><span>Sáb</span><span>Dom</span></div>
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
   /* --- profundidade (revisao externa, 04/set): fundo verde-petroleo escuro com gradiente,
          cartoes com elevacao, bordas menos visiveis, brilho so no que importa --- */
   body{background:radial-gradient(1400px 700px at 18% -12%,#0d2420 0%,#07130f 42%,#050c0a 100%) fixed;
     color:#e6efeb}
   .content-section,.mac-perna,.mac-geo-card,.mac-fala,.mac-eua-fomc,.mac-geo-mundo,.mac-ficha{
     background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
     border-color:rgba(255,255,255,.06)!important;
     box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 10px 30px -18px rgba(0,0,0,.7)}
   .mac-detalhe{background:linear-gradient(180deg,rgba(94,234,212,.045),rgba(255,255,255,.012));
     border-color:rgba(94,234,212,.16)!important;box-shadow:0 20px 50px -30px rgba(94,234,212,.35)}
   .mac-item-sel{background:rgba(94,234,212,.10);border-left-color:#5eead4}
   .mac-item:hover{background:rgba(255,255,255,.04)}
   .mac-duas{grid-template-columns:minmax(180px,220px) minmax(0,1fr)}
   .mac-lista{gap:2px}
   .mac-item{padding:7px 10px}
   .mac-item-par{font-size:13.5px}
   .mac-item-tag b{font-size:12px}
   .mac-de100{opacity:.45;font-weight:400;margin-left:1px;font-family:var(--font-mono);font-size:.8em}
   .mac-det-par{font-size:34px;font-weight:700;letter-spacing:-.01em}
   .mac-det-leitura{font-size:11.5px;font-weight:600}
   .mac-det-leitura.v-bull{background:rgba(94,234,212,.16);color:#5eead4}
   .mac-det-leitura.v-bear{background:rgba(248,122,122,.16);color:#f87a7a}
   /* --- o card-resumo: conclusao primeiro --- */
   .mac-resumo{border:1px solid rgba(94,234,212,.18);border-radius:14px;padding:16px 18px;margin:12px 0 16px;
     background:linear-gradient(135deg,rgba(94,234,212,.09),rgba(94,234,212,.02) 60%,rgba(255,255,255,.01));
     box-shadow:0 0 0 1px rgba(94,234,212,.05) inset}
   .mac-resumo.r-short{border-color:rgba(248,122,122,.2);
     background:linear-gradient(135deg,rgba(248,122,122,.09),rgba(248,122,122,.02) 60%,rgba(255,255,255,.01))}
   .mac-resumo.r-nao{border-color:rgba(255,255,255,.1);background:rgba(255,255,255,.02)}
   .mac-resumo-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
   .mac-resumo-item{min-width:0}
   .mac-resumo-rot{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;opacity:.55;margin-bottom:5px}
   .mac-resumo-item strong{display:block;font-size:22px;font-weight:700;letter-spacing:-.01em;line-height:1.15;
     font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
   .mac-resumo-item small{display:block;font-size:12px;opacity:.7;margin-top:4px;line-height:1.45}
   .mac-barra-forca{height:5px;border-radius:3px;background:rgba(255,255,255,.08);margin:7px 0 4px;overflow:hidden}
   .mac-barra-forca i{display:block;height:100%;background:linear-gradient(90deg,#5eead4,#8fd0ff);border-radius:3px}
   .r-short .mac-barra-forca i{background:linear-gradient(90deg,#f87a7a,#f0b429)}
   .mac-resumo-frase{margin:14px 0 0;font-size:13.5px;line-height:1.55;opacity:.92}
   .mac-resumo-frase .mac-resumo-rot{display:inline;margin:0 6px 0 0}
   .mac-det-nota-wrap{margin:0 0 14px;border-top:0;padding-top:0}
   .mac-det-nota-wrap summary{font-size:12px;opacity:.55;cursor:pointer}
   .mac-det-nota-wrap .mac-det-nota{margin:8px 0 0;font-size:13px}
   .mac-perna-papel{font-size:10px;letter-spacing:.12em}
   .mac-perna-taxa{font-size:22px}
   .mac-lean-pill.big{font-size:15px}
   .mac-lean-pill.big b{font-size:16px}
   .mac-motivos{font-size:12.5px}
   .mac-det-mais summary{font-size:12.5px}
   .mac-tabela td{font-size:13.5px}
   .mac-tabela td small{font-size:12px}
   @media (max-width:1180px){.mac-resumo-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
   @media (max-width:640px){.mac-resumo-grid{grid-template-columns:1fr}}

   /* ===================== REVISAO DO DONO — item 6 =====================
      (c) nenhuma pontuacao na tela · (f) a acao na frente · (g) tres leituras separadas
      (h) tarja de dominancia · (i) selo experimental na geopolitica · (j) origem do texto */

   /* (g) tres colunas, uma por numero — nunca somados */
   .mac-resumo-3{grid-template-columns:repeat(3,minmax(0,1fr))}
   @media (max-width:1180px){.mac-resumo-3{grid-template-columns:repeat(2,minmax(0,1fr))}}
   @media (max-width:640px){.mac-resumo-3{grid-template-columns:1fr}}
   .mac-resumo.e-forte{border-color:rgba(94,234,212,.30)}
   .mac-resumo.e-mod{border-color:rgba(94,234,212,.18)}
   .mac-resumo.e-obs{border-color:rgba(255,196,0,.22);
     background:linear-gradient(135deg,rgba(255,196,0,.07),rgba(255,255,255,.01) 60%)}
   .mac-resumo.e-sem{border-color:rgba(255,255,255,.1);background:rgba(255,255,255,.02)}
   .mac-barra-forca.q i{background:linear-gradient(90deg,#8fd0ff,#c9a7ff)}
   .mac-naocal{font-size:15px !important;font-weight:600 !important;opacity:.7;
     letter-spacing:0 !important}
   .mac-resumo-estado{margin:15px 0 0;font-size:14px;line-height:1.5}
   .mac-resumo-estado .mac-resumo-rot{display:inline;margin:0 8px 0 0}
   .mac-resumo-estado b{font-weight:700}
   .mac-provisorio{display:inline-block;margin-left:8px;font-size:10.5px;letter-spacing:.05em;
     text-transform:uppercase;opacity:.5}
   /* marca curta de faixa provisoria, para caber na etiqueta da lista e na pastilha */
   .mac-prov-mini{margin-left:5px;font-size:9px;letter-spacing:.06em;text-transform:lowercase;
     opacity:.45;font-weight:400}
   .mac-resumo-linhas{margin-top:13px;padding-top:11px;display:grid;gap:6px;
     border-top:1px solid rgba(255,255,255,.09);font-size:13px;line-height:1.5}
   .mac-resumo-linhas .mac-resumo-rot{display:inline;margin:0 7px 0 0}
   .mac-resumo-linhas small{margin-left:7px;font-size:12px}

   /* (h) tarja discreta em amarelo — dentro do card do par e na pilula da perna */
   .mac-tarja{margin:10px 0 0;padding:6px 10px;border-radius:7px;font-size:12px;line-height:1.45;
     background:rgba(255,196,0,.10);border:1px solid rgba(255,196,0,.28);color:#ffcf5c}
   .mac-tarja-dom{font-weight:500}

   /* (i)+(j) selo pequeno: "experimental — nao vota", "manchete (contexto)" */
   .mac-selo{display:inline-block;margin-left:5px;font-size:9.5px;letter-spacing:.06em;
     text-transform:uppercase;padding:1px 6px;border-radius:20px;
     background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);opacity:.75}
   .mac-dim.exp{border-style:dashed;opacity:.55}
   .mac-origem-txt{margin-top:9px;font-size:12.5px}
   .mac-familias{margin-top:9px;font-size:12.5px}
   .mac-familias b{font-family:var(--font-mono);font-size:14px}

   /* (f) a acao manda no topo do detalhe; a sigla fica secundaria */
   .mac-det-acao{font-weight:700}
   .mac-det-acao.v-bull{color:#5fe0a0}
   .mac-det-acao.v-bear{color:#ff8f8f}
   .mac-det-acao.v-nao{opacity:.55}
   .mac-det-sigla{font-size:.62em;font-weight:500;opacity:.6;letter-spacing:.04em;margin-left:6px}
   .mac-det-leitura.e-forte{background:rgba(94,234,212,.18);color:#5eead4}
   .mac-det-leitura.e-mod{background:rgba(94,234,212,.12);color:#5eead4}
   .mac-det-leitura.e-obs{background:rgba(255,196,0,.14);color:#ffcf5c}
   .mac-det-leitura.e-sem{background:rgba(255,255,255,.06);opacity:.6}

   /* (g) o desenho das duas pernas — barras proporcionais, nunca caractere de desenho.
      E o UNICO lugar da tela com o numero continuo, e ele mora atras do expansivel. */
   .mac-pernas-desenho{margin:10px 0 4px}
   .mac-pl-linha{display:grid;grid-template-columns:82px 62px minmax(0,1fr);align-items:center;
     gap:10px;margin:7px 0}
   .mac-pl-moeda{font-size:13px;font-weight:600;letter-spacing:.02em}
   .mac-pl-num{font-family:var(--font-mono,ui-monospace,monospace);font-size:14px;font-weight:700;
     font-variant-numeric:tabular-nums;text-align:right}
   .mac-pl-num.p,.mac-pl-rodape b.p{color:#5fe0a0}
   .mac-pl-num.n,.mac-pl-rodape b.n{color:#ff8f8f}
   .mac-pl-trilho{display:block;height:10px;border-radius:5px;background:rgba(255,255,255,.07);
     overflow:hidden}
   .mac-pl-barra{display:block;height:100%;border-radius:5px}
   .mac-pl-barra.p{background:linear-gradient(90deg,#3aa06a,#5fe0a0)}
   .mac-pl-barra.n{background:linear-gradient(90deg,#a04343,#ff8f8f)}
   .mac-pl-barra.z{background:rgba(255,255,255,.2)}
   .mac-pl-rodape{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:10px;padding-top:9px;
     border-top:1px solid rgba(255,255,255,.09);font-size:13px}
   .mac-pl-rodape b{font-family:var(--font-mono,ui-monospace,monospace)}
   .mac-pl-legenda{margin:8px 0 0;font-size:11.5px;opacity:.55;line-height:1.5}
   @media (max-width:640px){
     .mac-pl-linha{grid-template-columns:70px 56px minmax(0,1fr);gap:8px}
   }
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
   .mac-perna-lean{margin:8px 0 10px;padding:10px 0 0;border-top:1px solid rgba(255,255,255,.07)}
   .mac-dims{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}
   .mac-dim{font-size:10.5px;letter-spacing:.04em;padding:2px 8px;border-radius:5px;
     border:1px solid rgba(255,255,255,.12);opacity:.85;white-space:nowrap}
   .mac-dim small{opacity:.6;margin-left:3px}
   /* COR SEMANTICA: verde = inclinacao a SUBIR juro, vermelho = inclinacao a CORTAR,
      cinza = manutencao. A concordancia com a leitura da moeda nao usa cor — usa o ✓/✗ e,
      quando discorda, o traco pontilhado. (Antes .ok/.no pintavam a concordancia e a tela
      chegava a mostrar "alta" em vermelho.) */
   .mac-dim.d-alta{border-color:rgba(82,217,138,.45);color:#52d98a}
   .mac-dim.d-corte{border-color:rgba(248,122,122,.4);color:#f87a7a}
   .mac-dim.d-mantem{border-color:rgba(255,255,255,.22);color:inherit}
   .mac-dim.discorda{border-style:dotted;opacity:.62}
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
   .mac-item-tag .mac-forca{opacity:.55;text-transform:none;letter-spacing:0;margin-left:2px}
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
   /* z baixo = noticiario quieto. Nao e alta de juro, entao NAO leva verde (lei da cor
      semantica): fica neutro, so mais apagado. */
   .mac-geo-pill.baixo{background:rgba(255,255,255,.05);opacity:.7}
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
   /* --- noticias por moeda --- */
   .mac-news-cont{font-family:var(--font-mono);opacity:.55;margin-left:5px;font-size:10px}
   .mac-news-lista{list-style:none;margin:0;padding:0;display:grid;gap:6px}
   .mac-news-item{display:grid;grid-template-columns:auto minmax(0,1fr) auto auto;gap:10px;
     align-items:baseline;padding:8px 10px;border:1px solid rgba(255,255,255,.07);border-radius:8px;
     font-size:13px}
   .mac-news-item a{color:inherit;text-decoration:none}
   .mac-news-item a:hover{text-decoration:underline}
   /* COR SEMANTICA (lei do dono, conferida em 05/set): verde = ALTA de juro, vermelho =
      CORTE. Estava INVERTIDO aqui — a etiqueta "alta" saia vermelha e a "corte" verde, que e
      a convencao de ACOES (juro sobe, bolsa cai), nao a deste painel. Trocado. */
   .mac-news-item.c-alta{border-left:2px solid rgba(82,217,138,.6)}
   .mac-news-item.c-corte{border-left:2px solid rgba(248,122,122,.6)}
   .mac-news-item.c-mantem{border-left:2px solid rgba(255,255,255,.25)}
   .mac-news-tag{font-size:10px;letter-spacing:.07em;text-transform:uppercase;padding:2px 7px;
     border-radius:20px;background:rgba(255,255,255,.06);white-space:nowrap}
   .mac-news-tag.c-alta{background:rgba(82,217,138,.14);color:#52d98a}
   .mac-news-tag.c-corte{background:rgba(248,122,122,.14);color:#f87a7a}
   @media (max-width:900px){.mac-news-item{grid-template-columns:1fr;gap:3px}}
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
   /* Dentro da GAVETA lateral (styles.css: body > nav#tabBar.tabs, 236 px, coluna), os grupos
      nao podem ficar lado a lado nem as abas em linha — a revisao de 04/set mostrou "Noticias"
      cortada e METODO/ACOES espremidos. Na gaveta tudo empilha: grupo embaixo de grupo, aba
      embaixo de aba, rotulo visivel (ha espaco), aba com a largura toda. */
   body > nav#tabBar.tabs .mac-nav-grupos{flex-direction:column;flex-wrap:nowrap;gap:16px;
     align-items:stretch;width:100%}
   body > nav#tabBar.tabs .mac-nav-grupo{gap:6px}
   body > nav#tabBar.tabs .mac-nav-rotulo{display:block;font-size:10px;opacity:.42;padding-left:12px}
   body > nav#tabBar.tabs .mac-nav-abas{flex-direction:column;gap:2px;align-items:stretch}
   body > nav#tabBar.tabs .mac-nav-abas .tab{width:100%;text-align:left;white-space:nowrap;
     overflow:hidden;text-overflow:ellipsis}
   @media (max-width:900px){
     .mac-nav-grupos{gap:12px}
     .mac-nav-rotulo{display:none}
   }
   /* --- tela de trabalho dos pares: lista a esquerda, detalhe fixo a direita --- */
   /* (e) 225 -> 250 px e MAIS CONTRASTE: o item nao selecionado sumia no fundo da pagina.
      Agora tem fundo e borda propria, e o selecionado se separa por cor, borda e barra. */
   .mac-duas{display:grid;grid-template-columns:minmax(210px,250px) minmax(0,1fr);gap:18px;
     align-items:start}
   .mac-detalhe{min-width:0}
   .mac-lista{display:flex;flex-direction:column;gap:5px;max-height:74vh;overflow-y:auto;
     padding-right:4px}
   .mac-item{display:grid;grid-template-columns:1fr auto;grid-template-rows:auto auto auto;
     gap:2px 8px;text-align:left;background:rgba(255,255,255,.045);
     border:1px solid rgba(255,255,255,.11);border-radius:8px;
     padding:9px 11px;color:inherit;cursor:pointer;border-left:3px solid rgba(255,255,255,.14)}
   .mac-item:hover{background:rgba(255,255,255,.10);border-color:rgba(255,255,255,.22)}
   .mac-item-sel{background:rgba(120,200,255,.17);border-color:rgba(120,200,255,.45);
     border-left-color:#6cc4ff;box-shadow:0 0 0 1px rgba(120,200,255,.22)}
   .mac-item-acao{grid-column:1;grid-row:1;font-size:13px;font-weight:700;letter-spacing:.02em}
   .mac-item-acao.v-bull{color:#5fe0a0}
   .mac-item-acao.v-bear{color:#ff8f8f}
   .mac-item-acao.v-nao{opacity:.5;font-weight:600}
   .mac-item-par{grid-column:1;grid-row:2;font-size:12.5px;font-weight:500;letter-spacing:.03em;
     opacity:.72}
   .mac-item-par em{opacity:.35;font-style:normal;margin:0 1px}
   .mac-item-dias{grid-column:2;grid-row:1;font-size:11px;opacity:.72;
     font-variant-numeric:tabular-nums;align-self:center}
   .mac-item-tag{grid-column:1/-1;grid-row:3;font-size:10px;letter-spacing:.06em;text-transform:uppercase;
     opacity:.85}
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
     .mac-duas{grid-template-columns:minmax(200px,250px) minmax(0,1fr)}
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
   .mac-cenarios span{opacity:.65}

   /* ===================== REVISAO DO DONO — 05/set =====================
      (1) bloco da moeda sem pontuacao · (2) tarja e acinzentamento por atraso
      (3) veredito por orador · (4) regime + proximo evento + BRT primeiro
      (5) surpresa nos dados americanos · (6) geopolitica recolhida e fonte das manchetes */

   /* (1) O BLOCO DA MOEDA — tres linhas, nenhum numero de pontuacao */
   .mac-bloco-moeda{line-height:1.45}
   .mac-bm-linha1{font-size:13.5px;font-weight:600;letter-spacing:.01em}
   .mac-bm-linha1 strong{font-weight:700}
   .mac-bm-seta{margin-right:3px;font-size:11px}
   .mac-bm-linha2{font-size:12px;opacity:.72;margin-top:2px}
   .mac-bm-linha3{font-size:12px;opacity:.72;margin-top:1px}
   .mac-bm-linha3 b{font-weight:600;opacity:.95}
   .mac-bm-motivo{font-size:11.5px;opacity:.62;margin-top:2px;line-height:1.4;max-width:44ch}
   .mac-bm-nota{font-size:11px;opacity:.5;margin-top:5px}
   .mac-bloco-moeda.big .mac-bm-linha1{font-size:16px}
   .mac-bloco-moeda.big .mac-bm-linha2,.mac-bloco-moeda.big .mac-bm-linha3{font-size:12.5px}
   .mac-bm-linha1.positive{color:#52d98a}
   .mac-bm-linha1.negative{color:#f87a7a}
   .mac-placar-sem{font-size:12.5px;margin:-6px 0 14px;opacity:.8}
   .mac-placar-sem span{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;opacity:.55;
     margin-right:7px}

   /* (2) BLOQUEIO POR ATRASO — tarja ambar de tres linhas e acinzentamento das leituras.
      "Acinzenta" e literal: opacidade baixa e a COR SEMANTICA desligada. Uma leitura que
      pode estar invalida nao pode continuar verde nem vermelha. */
   .mac-tarja-atraso{margin:0 0 16px;padding:11px 14px;border-radius:10px;
     background:rgba(255,196,0,.10);border:1px solid rgba(255,196,0,.34);color:#ffcf5c;
     display:grid;gap:2px;line-height:1.5}
   .mac-tarja-atraso.grave{background:rgba(248,122,122,.10);border-color:rgba(248,122,122,.38);
     color:#ffb0a0}
   .mac-tarja-atraso strong{font-size:15px;font-weight:700;letter-spacing:.01em}
   .mac-tarja-atraso span{font-size:13px;opacity:.92}
   .mac-tarja-atraso small{margin-top:5px;font-size:11.5px;opacity:.72;line-height:1.5}
   .mac-atrasado{opacity:.55}
   .mac-atrasado .positive,.mac-atrasado .negative,
   .mac-atrasado .mac-bm-linha1.positive,.mac-atrasado .mac-bm-linha1.negative,
   .mac-atrasado .mac-item-acao.v-bull,.mac-atrasado .mac-item-acao.v-bear,
   .mac-atrasado .mac-regime.positive,.mac-atrasado .mac-regime.negative{color:inherit}
   .mac-atrasado .mac-barra-forca i{background:rgba(255,255,255,.30)}
   .mac-item-acao.v-suspensa,.mac-det-acao.v-suspensa{color:#ffcf5c;font-weight:600;
     font-size:.72em;letter-spacing:.02em}
   .mac-item .mac-item-acao.v-suspensa{font-size:11px;line-height:1.3}

   /* (4) tabela de bancos: regime, BRT em destaque, horario local em segundo plano */
   .mac-regime{font-size:12.5px;font-weight:600;letter-spacing:.02em}
   .mac-brt{display:block;font-variant-numeric:tabular-nums;font-size:13.5px}
   td .mac-brt{font-weight:700}
   .mac-hora-local{display:block;margin-top:2px;font-size:11px;opacity:.45}
   .mac-tabela td small{display:inline}
   .mac-tabela td small.mac-brt,.mac-tabela td small.mac-hora-local{display:block}

   /* (3) veredito por orador */
   .mac-veredito{font-size:12.5px;font-weight:600;letter-spacing:.01em}
   .mac-veredito.v-alta{color:#52d98a}
   .mac-veredito.v-alta-cond{color:#a7dfbc}
   .mac-veredito.v-corte{color:#f87a7a}
   .mac-veredito.v-corte-cond{color:#f0b8b8}
   .mac-veredito.v-mantem{opacity:.85}
   .mac-veredito.v-indet{opacity:.55;font-weight:500}
   .mac-fala-motivo{margin-top:5px;font-size:12px;opacity:.75;line-height:1.5}
   .mac-fala-trecho{margin-top:6px}
   .mac-fala-trecho summary{cursor:pointer;font-size:11.5px;opacity:.55}
   .mac-fala-trecho summary:hover{opacity:.9}
   .mac-falas-nota{margin:9px 0 0;font-size:11.5px;opacity:.6;line-height:1.55;max-width:76ch}

   /* (5) dados americanos: o nivel fica secundario, embaixo do "Atual" */
   .mac-eua-nivel{display:block;font-size:11px;opacity:.5;font-weight:400;margin-top:2px}
   .mac-eua-casado{display:block;font-size:11px;opacity:.45;margin-top:2px}
   .mac-tabela td .mac-ref-td{display:block;margin-top:2px;opacity:.5}

   /* (6) geopolitica recolhida + confiabilidade da fonte */
   .mac-geo-det>summary{cursor:pointer;list-style:none}
   .mac-geo-det>summary::-webkit-details-marker{display:none}
   .mac-geo-sum{display:inline-flex;gap:8px;align-items:baseline;flex-wrap:wrap;
     font-size:17px;font-weight:600;letter-spacing:-.01em}
   .mac-geo-det>summary:hover .mac-geo-sum{opacity:.85}
   .mac-geo-det[open]>summary{margin-bottom:8px}
   .mac-conf{margin-left:6px;font-size:10px;letter-spacing:.05em;text-transform:uppercase;
     padding:1px 6px;border-radius:20px;background:rgba(255,255,255,.07)}
   .mac-conf.c-alta{background:rgba(82,217,138,.14);color:#52d98a}
   .mac-conf.c-media{background:rgba(240,180,41,.14);color:#f0b429}
   .mac-conf.c-baixa{background:rgba(248,122,122,.14);color:#f87a7a}
   .mac-geo-dup{border-left-color:transparent!important;opacity:.5}

   /* (1) o desenho das duas pernas perdeu o numero: o rotulo entra no lugar dele */
   .mac-pl-rot{font-size:12px;font-weight:600;letter-spacing:.01em;text-align:right;
     white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .mac-pl-rot.p{color:#5fe0a0}
   .mac-pl-rot.n{color:#ff8f8f}
   .mac-pl-linha{grid-template-columns:82px 120px minmax(0,1fr)}
   @media (max-width:640px){.mac-pl-linha{grid-template-columns:70px 104px minmax(0,1fr)}}`;
  document.head.appendChild(estilo);

  carrega().then(() => {
    aplica();
    setInterval(aplica, 900);
    document.addEventListener("click", () => setTimeout(aplica, 60), true);
  });
})();
