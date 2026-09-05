/* AUDITORIA DO CORTE DE TEMPO — o aviso honesto, com o que ainda contamina a tela.
 *
 * O DONO ESCREVEU (05/set):
 *   "cortar a data visualmente nao basta se o sistema recalcula o passado com dados
 *    revisados, manchetes publicadas depois, modelo ou pesos atuais, e decisoes
 *    posteriores do banco central".
 *
 * Ele esta certo em tres dos quatro. O resultado da auditoria, com a evidencia no codigo.
 * (Cito FUNCOES e CONSTANTES, nunca numeros de linha: quatro construtores mexem nestes
 *  arquivos em paralelo e um numero de linha envelhece no mesmo dia.)
 *
 *   1. VALOR REVISADO ......... LIMPO, e medido.
 *      `normaliza` em fxstreet_calendario.py grava `divulgado` (o campo `actual` da fonte) e
 *      `revisado` (o campo `revised`) em chaves SEPARADAS. sentimento.py nunca le `revisado`
 *      — zero ocorrencias da palavra no arquivo — e `dimensao_dados` classifica `divulgado`
 *      contra `consenso`.
 *      ⚠️ O n DESTA EVIDENCIA ESTAVA INFLADO — corrigido na auditoria de 05/set. A versao
 *      anterior dizia "254 e 295 ids em comum, ZERO valores mudaram", o que se le como se
 *      254 e 295 VALORES tivessem sido comparados. Nao foram: aquilo era a interseccao das
 *      LISTAS de evento, nao o n da comparacao. Refeito hoje contra os commits 559dfab
 *      (30/ago) e 6180583 (03/set): 184 e 225 ids em comum, e desses apenas 15 e 66 tinham
 *      valor divulgado nos DOIS lados — esse e o n de verdade. Nesses 15 e 66, zero valores
 *      mudaram. O calendario e uma janela rolante de +-42 dias, entao esse n encolhe todo
 *      dia: numero medido aqui so vale com a data ao lado.
 *      A FXStreet publica a revisao do periodo anterior como campo novo na divulgacao
 *      seguinte; nao reescreve o print.
 *
 *   2. MANCHETE POSTERIOR AO CORTE ... CONTAMINA. Conserto parcial feito aqui.
 *      noticias.py varre uma janela de 72 h ao vivo. `dimensao_texto_manchetes` recebe o
 *      instante atual como parametro e NUNCA o usa: le a contagem inteira do arquivo, sem
 *      filtro de data. ui_macro.js nao tem uma unica referencia a `timeCut`. Este modulo
 *      esconde da lista as manchetes posteriores ao corte e diz quantas escondeu — mas a
 *      contagem ja entrou no sentimento e nao da para desfazer, e noticias.py guarda so as
 *      primeiras manchetes enquanto conta todas (`itens[:MAX]` com `n_72h: len(itens)`),
 *      entao nem recontar da.
 *
 *   3. PESOS E LIMIARES DE HOJE ..... CONTAMINA. Nao consertavel sem reescrever.
 *      JANELA_DIAS, MEIA_VIDA, LIMIAR_DADOS, PESO_DIM, GEO_Z_CORTE e as reguas novas de
 *      05/set (FAIXAS_PROVISORIAS, WINSOR, CICLO_MEIA_VIDA_DIAS, CICLO_PISO_VOTO, pesos de
 *      fala) sao constantes de modulo, e os pesos do score sao CODIGO, nao dado. Nao existe
 *      recomputacao historica: sentimento.py faz `agora = now(utc)` e o arquivo e UM
 *      retrato. Cada regua nova que entra PIORA este item.
 *      O que resolve e o registro imutavel (snapshot.py) daqui para a frente.
 *
 *   4. REUNIOES E TAXAS ATUAIS ...... CONTAMINA. Detectado e listado aqui.
 *      bancos_centrais.py traz taxa, ultima_mudanca e ultima_mudanca_bp fixas e sempre
 *      ATUAIS, e calcula `proxima` e `dias_ate` a partir de `date.today()`. `dimensao_ciclo`
 *      le essa `ultima_mudanca` e mede a idade contra HOJE — inclusive o decaimento novo por
 *      reunioes de manutencao, que conta reunioes ocorridas DEPOIS do corte. Com o corte em
 *      01/nov/2025, SEIS dos oito bancos aparecem com uma decisao de juro que ainda nao
 *      tinha acontecido. Este modulo nao conserta o score; ele NOMEIA os bancos.
 *
 *   E O BURACO MAIOR, que nenhum dos quatro cobre:
 *      a funcao `aplica` do ui_macro.js (agendada a cada 900 ms) TROCA o innerHTML dos
 *      paineis Visao geral, Noticias, Pares e Calendario, e `recolheLegado` move para um
 *      `#macSink` oculto justamente os elementos que ui_cut_global.js reescreve quando o
 *      corte liga. O comentario do proprio arquivo admite: "deixa o app.js escrever onde
 *      ninguem ve". Ou seja: nesses quatro paineis o corte de tempo desenha num conteiner
 *      escondido, e o que aparece na tela e a leitura de HOJE. Consertar isso e reescrever a
 *      camada de desenho; enquanto nao for reescrita, o aviso abaixo diz na cara que a tela
 *      e de hoje.
 *
 * O QUE ESTE ARQUIVO FAZ, ENTAO: (a) esconde manchete posterior ao corte e conta;
 * (b) nomeia os bancos com decisao posterior ao corte; (c) escreve o aviso honesto no
 * banner. Ele nunca diz que a tela esta limpa.
 */
(function () {
  "use strict";

  var D = { noticias: null, bancos: null, sentimento: null, carregado: false };
  var ultimoCorte = "__nunca__";

  function corteAtivo() {
    try {
      return (typeof timeCut !== "undefined" && timeCut && timeCut.active) ? timeCut.date : null;
    } catch (e) { return null; }
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function dataBr(iso) {
    var p = String(iso || "").slice(0, 10).split("-");
    return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : String(iso || "");
  }

  function carrega() {
    if (D.carregado) return Promise.resolve();
    var pega = function (p) {
      return fetch(p + "?t=" + Date.now())
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; });
    };
    return Promise.all([
      pega("data/noticias.json"), pega("data/bancos_centrais.json"), pega("data/sentimento.json"),
    ]).then(function (v) {
      D.noticias = v[0]; D.bancos = v[1]; D.sentimento = v[2]; D.carregado = true;
    });
  }

  /* ---------------------------------------------------------------- CONSERTO 1
   * Manchete publicada depois do corte sai da lista. Casa pelo link, que e unico —
   * o titulo passa por esc() no desenho e nao bate caractere a caractere. */
  function escondeManchetes(corte) {
    var limite = corte + "T23:59:59Z";
    var porLink = {};
    var moedas = (D.noticias && D.noticias.moedas) || {};
    Object.keys(moedas).forEach(function (m) {
      (moedas[m].itens || []).forEach(function (it) {
        if (it && it.link) porLink[it.link] = it.quando_utc || "";
      });
    });
    var escondidas = 0, mostradas = 0;
    document.querySelectorAll("li.mac-news-item").forEach(function (li) {
      var a = li.querySelector("a[href]");
      var quando = a ? porLink[a.getAttribute("href")] : null;
      var depois = Boolean(quando && quando > limite);
      li.hidden = depois;
      if (depois) escondidas++; else mostradas++;
    });
    return { escondidas: escondidas, mostradas: mostradas };
  }

  function mostraTodasManchetes() {
    document.querySelectorAll("li.mac-news-item").forEach(function (li) { li.hidden = false; });
  }

  /* Quantas manchetes do ARQUIVO inteiro sao posteriores ao corte — inclusive as das
   * moedas que nao estao na tela, porque todas entraram na contagem do sentimento. */
  function manchetesPosteriores(corte) {
    var limite = corte + "T23:59:59Z";
    var moedas = (D.noticias && D.noticias.moedas) || {};
    var depois = 0, total = 0, contadas = 0;
    Object.keys(moedas).forEach(function (m) {
      var b = moedas[m] || {};
      contadas += Number(b.n_72h || 0);
      (b.itens || []).forEach(function (it) {
        total++;
        if ((it.quando_utc || "") > limite) depois++;
      });
    });
    return { depois: depois, guardadas: total, contadas: contadas };
  }

  /* ---------------------------------------------------------------- CONSERTO 2
   * Nomeia os bancos cuja ULTIMA DECISAO e posterior ao corte (a dimensao ciclo esta
   * lendo o futuro) e os que ja decidiram entre o corte e hoje. */
  function bancosContaminados(corte) {
    var B = (D.bancos && D.bancos.bancos) || {};
    var decisaoFutura = [], reuniaoPassada = [];
    Object.keys(B).forEach(function (m) {
      var b = B[m] || {};
      if (b.ultima_mudanca && String(b.ultima_mudanca) > corte) {
        decisaoFutura.push(m + " (" + (b.sigla || "") + ", " + dataBr(b.ultima_mudanca) +
          (b.ultima_mudanca_bp != null
            ? ", " + (b.ultima_mudanca_bp > 0 ? "+" : "") + b.ultima_mudanca_bp + " bp" : "") + ")");
      }
      (b.reunioes || []).forEach(function (r) {
        if (String(r) > corte && String(r) <= new Date().toISOString().slice(0, 10)) {
          reuniaoPassada.push(m + " " + dataBr(r));
        }
      });
    });
    return { decisaoFutura: decisaoFutura, reuniaoPassada: reuniaoPassada };
  }

  /* ------------------------------------------------------------------- O AVISO */
  function item(estado, titulo, corpo) {
    var rot = { limpo: "LIMPO", contamina: "CONTAMINA", parcial: "CONSERTO PARCIAL" }[estado];
    return '<li class="cta-item cta-' + estado + '"><span class="cta-selo">' + rot + "</span>" +
      "<div><strong>" + titulo + "</strong><p>" + corpo + "</p></div></li>";
  }

  function desenha(corte) {
    var banner = document.getElementById("timeCutBanner");
    if (!banner) return;
    var caixa = document.getElementById("timeCutAuditoria");
    if (!corte) {
      if (caixa) caixa.remove();
      mostraTodasManchetes();
      return;
    }
    if (!caixa) {
      caixa = document.createElement("div");
      caixa.id = "timeCutAuditoria";
      caixa.className = "cta-caixa";
      banner.after(caixa);
    }

    var n = escondeManchetes(corte);
    var mn = manchetesPosteriores(corte);
    var bc = bancosContaminados(corte);
    var geradoEm = (D.sentimento && D.sentimento.gerado_em) || null;
    var hoje = new Date().toISOString().slice(0, 10);

    var lista = "";

    lista += item("limpo", "O valor usado e o ORIGINALMENTE DIVULGADO, nao o revisado",
      "O calendario grava <code>divulgado</code> e <code>revisado</code> em campos separados " +
      "(<code>fxstreet_calendario.py</code>, funcao <code>normaliza</code>) e o sentimento nunca " +
      "le o revisado: <code>dimensao_dados</code> classifica <code>divulgado</code> contra " +
      "<code>consenso</code>, e a palavra &ldquo;revisado&rdquo; nao aparece uma unica vez em " +
      "<code>sentimento.py</code>. Medido, nao suposto — e com o <b>n honesto</b>, corrigido em " +
      "05/09/2026: comparando o valor divulgado por id de evento entre o calendario de hoje e as " +
      "versoes de 30/08 e 03/09, sao 184 e 225 ids em comum, mas so <b>15 e 66</b> tem valor " +
      "divulgado nos DOIS lados — esse e o n da comparacao, e nele <b>nenhum valor mudou</b>. " +
      "(A versao anterior deste aviso citava &ldquo;254 e 295&rdquo;, que era a interseccao das " +
      "listas de evento, nao o n comparado. O calendario e uma janela rolante de &plusmn;42 dias: " +
      "esse n encolhe todo dia, entao ele so vale com a data ao lado.) A FXStreet publica a " +
      "revisao do periodo anterior como campo novo na divulgacao seguinte; ela nao reescreve o " +
      "print original.");

    lista += item("parcial", "Manchetes publicadas depois de " + dataBr(corte),
      "<b>" + mn.depois + " de " + mn.guardadas + "</b> manchetes guardadas no arquivo sao " +
      "posteriores ao corte; " + (n.escondidas > 0
        ? "<b>" + n.escondidas + "</b> foram escondidas da lista da aba Noticias agora."
        : "nenhuma esta visivel na lista neste momento.") +
      " <b>O que NAO da para desfazer:</b> essas manchetes ja entraram na contagem que virou a " +
      "dimensao de texto do sentimento — <code>dimensao_texto_manchetes</code> recebe o instante " +
      "atual como parametro e <b>nunca o usa</b>, le a contagem inteira sem filtro de data — e o " +
      "arquivo conta <b>" + mn.contadas + "</b> manchetes guardando so " + mn.guardadas +
      " (<code>noticias.py</code> guarda <code>itens[:MAX]</code> e conta todas) — nem recontar da. " +
      "A janela e de 72 h e nao ha arquivo do Google News: para um corte com mais de 3 dias, " +
      "<b>100% das manchetes que pesaram sao posteriores ao corte</b>.");

    lista += item("contamina", "Os pesos e limiares aplicados sao os de HOJE",
      "Nao existe recomputacao com a regua da epoca. Janela de 42 dias, meia-vida de 21 dias, " +
      "limiar de dados 5,0, 25% por dimensao, corte z de 1,5 e as reguas novas de 05/set " +
      "(faixas provisorias, winsorizacao por item, decaimento do ciclo, pesos de fala) sao todas " +
      "<b>constantes de codigo</b> em <code>sentimento.py</code>, e os pesos de cada dimensao sao " +
      "codigo tambem. O arquivo e um unico retrato do agora" +
      (geradoEm ? ", gerado em <b>" + dataBr(geradoEm) + "</b>" : "") +
      ". Cada regua nova que entra piora este item: mudar um limiar amanha muda retroativamente " +
      "tudo o que a tela diz sobre ontem. " +
      "<b>O unico remedio e para frente:</b> o <code>snapshot.py</code> congela a leitura de cada " +
      "dia em <code>data/snapshots/</code>, append-only, para o backtest ler o registro em vez de " +
      "recalcular.");

    var txtBc = "";
    if (bc.decisaoFutura.length) {
      txtBc += "<b>A ultima decisao de juro no ar e POSTERIOR ao corte em: " +
        esc(bc.decisaoFutura.join("; ")) + ".</b> Essas decisoes ainda nao tinham acontecido em " +
        dataBr(corte) + " e mesmo assim movem 25% do peso da moeda, pela dimensao ciclo. ";
    } else {
      txtBc += "Nenhum banco tem ultima decisao posterior a " + dataBr(corte) +
        " — mas isso e sorte da data escolhida, nao protecao do sistema. ";
    }
    if (bc.reuniaoPassada.length) {
      txtBc += "Reunioes que aconteceram entre o corte e hoje e que a tela ja conhece: " +
        esc(bc.reuniaoPassada.join(", ")) + ". ";
    }
    txtBc += "A taxa vigente, a proxima reuniao e a contagem de dias sao sempre as de hoje: a " +
      "tabela do <code>bancos_centrais.py</code> guarda so os valores ATUAIS e calcula " +
      "<code>proxima</code> e <code>dias_ate</code> a partir de <code>date.today()</code>. E a " +
      "<code>dimensao_ciclo</code> mede a idade do ultimo movimento contra hoje — inclusive o " +
      "decaimento novo por reunioes de manutencao, que conta reunioes que so aconteceram depois " +
      "do corte.";
    lista += item("contamina", "Decisoes e reunioes dos bancos centrais", txtBc);

    lista += item("contamina", "Estes quatro paineis nao obedecem ao corte",
      "Visao geral, Noticias, Pares e Calendario sao repintados a cada 900 ms pela funcao " +
      "<code>aplica</code> do <code>ui_macro.js</code>, que <b>nao tem uma unica referencia ao " +
      "corte de tempo</b> (zero ocorrencias de <code>timeCut</code> no arquivo inteiro). Pior: a " +
      "funcao <code>recolheLegado</code> do mesmo arquivo move para um conteiner oculto " +
      "(<code>#macSink</code>) justamente os elementos que o <code>ui_cut_global.js</code> " +
      "reescreve quando o corte liga — o comentario do proprio codigo diz que isso &ldquo;deixa o " +
      "app.js escrever onde ninguem ve&rdquo;. <b>Nesses paineis o corte desenha no escondido, e o " +
      "que esta na tela e a leitura de " + dataBr(hoje) + ".</b> Consertar e reescrever a camada " +
      "de desenho, e nao foi feito aqui.");

    caixa.innerHTML =
      '<div class="cta-topo"><strong>AUDITORIA DO CORTE DE TEMPO</strong>' +
      "<span>Corte em <b>" + dataBr(corte) + "</b>. Esta tela <b>nao</b> esta limpa de " +
      "look-ahead. O que ainda contamina, item por item:</span></div>" +
      '<ul class="cta-lista">' + lista + "</ul>" +
      '<p class="cta-rodape">Auditoria de 05/set/2026. Enquanto os quatro itens acima nao forem ' +
      "resolvidos, nenhum numero desta tela sob o corte serve como amostra de backtest — a amostra " +
      "valida e o registro gravado no instante, em <code>data/snapshots/</code>.</p>";
  }

  var estilo = document.createElement("style");
  estilo.textContent =
    ".cta-caixa{margin:0 0 16px;border:1px solid rgba(240,180,41,.34);border-radius:12px;" +
    "background:linear-gradient(180deg,rgba(240,180,41,.09),rgba(255,255,255,.012));" +
    "padding:14px 16px;font-size:13px;line-height:1.55}" +
    ".cta-topo strong{display:block;font-size:11px;letter-spacing:.13em;color:#f0b429;margin-bottom:5px}" +
    ".cta-topo span{display:block;opacity:.88;margin-bottom:10px}" +
    ".cta-lista{list-style:none;margin:0;padding:0;display:grid;gap:9px}" +
    ".cta-item{display:grid;grid-template-columns:118px minmax(0,1fr);gap:12px;align-items:start;" +
    "padding:9px 0;border-top:1px solid rgba(255,255,255,.07)}" +
    ".cta-item strong{display:block;font-size:13.5px;margin-bottom:3px}" +
    ".cta-item p{margin:0;opacity:.82;font-size:12.5px}" +
    ".cta-item code{font-family:ui-monospace,monospace;font-size:11.5px;opacity:.8}" +
    ".cta-selo{font-size:10px;letter-spacing:.1em;font-weight:700;padding:3px 7px;border-radius:5px;" +
    "text-align:center;white-space:nowrap}" +
    ".cta-limpo .cta-selo{background:rgba(94,234,212,.16);color:#5eead4}" +
    ".cta-parcial .cta-selo{background:rgba(240,180,41,.16);color:#f0b429}" +
    ".cta-contamina .cta-selo{background:rgba(248,122,122,.16);color:#f87a7a}" +
    ".cta-rodape{margin:11px 0 0;font-size:12px;opacity:.62;border-top:1px solid rgba(255,255,255,.07);padding-top:9px}" +
    "@media (max-width:720px){.cta-item{grid-template-columns:1fr}}";
  document.head.appendChild(estilo);

  function tique() {
    var corte = corteAtivo();
    if (corte !== ultimoCorte) {
      ultimoCorte = corte;
      if (!corte) { desenha(null); return; }
    }
    if (!corte) return;
    carrega().then(function () { desenha(corte); });
  }

  // 1100 ms: um pouco mais lento que o repintor do ui_macro (900 ms), para reaplicar o
  // esconde-manchetes depois de cada redesenho dele, nunca antes.
  setInterval(tique, 1100);
  tique();
})();
