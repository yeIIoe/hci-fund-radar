/* ============================================================================
   ui_agentes.js — liga NO SITE a saida dos agentes e do vigia.

   DUAS PECAS, nesta ordem:
     1. FAIXA DE ESTADO no topo, alimentada por data/agentes/vigia/ultimo.json.
        Um LED por fonte: verde sincronizado, ambar atrasado, vermelho fora do ar.
        Havendo alarme, a tarja ABRE com o bloco de alarme de quatro colunas —
        identificador, assunto, MEDIDA e CONSEQUENCIA em frase inteira.
        Aviso sem consequencia escrita e decoracao: e filtrado antes de desenhar.
     2. SALA DE JULGAMENTOS (aba `agentes`), que le data/agentes/<nome>/ultimo.json e
        mostra, por moeda, o que cada agente julgou — com o trecho, o link da
        fonte, a versao do prompt e o selo. A objecao do advogado aparece AO LADO
        da tese, nunca escondida.

   REGRA DE PROVENIENCIA (vale para todo bloco que este arquivo desenha):
     quem falou (agente + versao do prompt) · quando · com que fonte · e o selo
     dizendo se aquilo e MEDIDO, JULGADO ou EM TESTE. Misturar os tres e o erro
     que mata credibilidade, entao os tres nunca saem sem etiqueta.

   LINHA DURA: este arquivo NAO calcula numero que entre em conta. Todo numero
   sai pronto do JSON e sempre com a origem ao lado. Onde o arquivo nao tem o
   numero, sai a palavra "nao medido" — nunca uma estimativa.

   NUNCA QUEBRA: todo fetch que falha vira `null`, toda peca que falta vira a
   sala vazia com "nenhum julgamento ainda". Nenhuma excecao sobe daqui.

   CSS: usa somente classes ja conferidas por contraste no estilo_hci.css
   (.faixa-estado/.faixa-seg/.led, .alarme-bloco/.alarme, .chip, .cartao, .rot,
   .num, .procedencia) mais o bloco §6.8 acrescentado no fim daquela folha.
   Nao injeta <style> em tempo de execucao — quem faz isso e o ui_macro.js, e e
   por causa dele que os seletores da folha tem de continuar prefixados com html.
   ========================================================================== */
(function (raiz) {
  "use strict";

  var VERSAO = "ui_agentes@2026-09-08";

  /* As oito moedas do painel. A ordem e fixa para a tela nao dancar entre
     recargas; nao e ranking de nada. */
  var MOEDAS = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"];

  /* Usada so quando data/agentes/indice.json nao abre. Nao inventa agente: se
     um destes nao existir em disco, ele simplesmente nao aparece. */
  var AGENTES_PADRAO = ["vigia", "fala", "noticia", "geopolitica", "divergencia", "advogado"];

  /* O advogado e lido a parte: ele nao tem tese propria, ele objeta a tese dos
     outros. Por isso sai do laco das teses e vira o indice de objecoes. */
  var ADVOGADO = "advogado";

  /* O vigia e a camada 1 (medicao de operacao). Ele alimenta a faixa do topo e
     NAO entra na sala por moeda: ele nao julga mercado, mede o encanamento. */
  var VIGIA = "vigia";

  /* ------------------------------------------------------------ ferramentas */

  function esc(v) {
    var API = raiz.HCI_MEDIDORES;
    if (API && typeof API.escapar === "function") return API.escapar(v);
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function ehObj(v) { return !!v && typeof v === "object"; }
  function ehNum(v) { return typeof v === "number" && isFinite(v); }
  function txt(v) { return typeof v === "string" ? v.trim() : ""; }

  /* Numero: SO formatacao (separador decimal pt-BR). Nenhuma conta. Quando o
     campo nao existe no arquivo, sai "nao medido" — nunca zero, nunca chute. */
  function num(v, casas) {
    if (!ehNum(v)) return null;
    try {
      return v.toLocaleString("pt-BR", {
        minimumFractionDigits: casas == null ? 0 : casas,
        maximumFractionDigits: casas == null ? 1 : casas
      });
    } catch (e) {
      return String(v);
    }
  }

  /* Carimbo: mostrado como veio, em UTC, cortado no minuto. Converter para BRT
     aqui seria aritmetica de fuso feita na tela — e ja custou caro uma vez. */
  function carimbo(iso) {
    var s = txt(iso);
    if (!s) return "";
    var m = s.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
    if (!m) return s.length > 24 ? s.slice(0, 24) : s;
    return m[3] + "/" + m[2] + " " + m[4] + ":" + m[5] + " UTC";
  }

  /* [08/set] QUEM VIGIA O VIGIA.
     O Eduardo perguntou por que a tela nao atualiza "na hora" tendo VPS. A medicao daquele
     momento: os DADOS do painel estavam com 11 min e o VIGIA com 19 h — ele nao estava em
     workflow nenhum nem no loop da VPS, tinha rodado uma vez a mao e congelado. A tela
     mostrava um retrato de ontem com cara de agora, que e o defeito que o proprio vigia
     existe para denunciar nos outros. Agora ele roda de hora em hora na VPS, e a idade dele
     aparece na tela como aparece a de qualquer outra fonte. */
  function idadeMin(iso) {
    var s = txt(iso);
    if (!s) return null;
    var t = Date.parse(/[Zz]|[+-]\d{2}:?\d{2}$/.test(s) ? s : s + "Z");
    if (isNaN(t)) return null;
    var m = Math.floor((Date.now() - t) / 60000);
    return m < 0 ? 0 : m;
  }
  function idadeTexto(m) {
    if (m === null) return "";
    if (m < 60) return m + " min";
    var h = Math.floor(m / 60);
    if (h < 24) return h + " h " + (m % 60) + " min";
    return Math.floor(h / 24) + " d " + (h % 24) + " h";
  }
  var VIGIA_TOLERANCIA_MIN = 180;   // ele roda de hora em hora; 3 h e o dobro do intervalo

  function ehLink(s) { return /^https?:\/\//i.test(txt(s)); }

  function link(fonte) {
    if (!ehObj(fonte)) return "";
    var titulo = txt(fonte.titulo) || txt(fonte.link) || "";
    var href = txt(fonte.link);
    var quando = txt(fonte.quando);
    if (!titulo && !href) return "";
    var alvo = ehLink(href)
      ? '<a href="' + esc(href) + '" target="_blank" rel="noopener noreferrer">' + esc(titulo || href) + "</a>"
      : esc(titulo || href) + (href && href !== titulo ? ' <span class="sala-caminho">' + esc(href) + "</span>" : "");
    return '<p class="sala-fonte"><span class="rot">fonte</span>' + alvo +
      (quando ? ' <span class="sala-quando">· ' + esc(quando) + "</span>" : "") + "</p>";
  }

  function chip(texto, variante) {
    if (!txt(texto)) return "";
    return '<span class="chip ' + (variante || "chip-mudo") + '">' + esc(texto) + "</span>";
  }

  /* O selo de natureza. Sai do campo `natureza` quando o arquivo o traz (o vigia
     traz: "MEDIDO"). Quando nao traz, o que se sabe com certeza e o que o proprio
     arquivo declara em `vota`/`selo`: julgamento de agente que nao vota e
     EM TESTE. Nao ha inferencia alem dessas duas leituras. */
  function selos(j, fonteDoArquivo) {
    var out = [];
    var nat = txt(j && j.natureza).toUpperCase();
    if (nat) out.push(chip(nat, nat === "MEDIDO" ? "chip-mudo" : "chip-marca"));
    else out.push(chip("JULGADO", "chip-marca"));
    if (j && j.vota === false) out.push(chip("em teste — não vota", "chip-aviso"));
    else if (j && j.vota === true) out.push(chip("vota", "chip-alta"));
    var s = txt(j && j.selo) || txt(fonteDoArquivo && fonteDoArquivo.selo);
    return { chips: out.join(""), selo: s };
  }

  function classeConfianca(c) {
    var v = txt(c).toLowerCase();
    if (v === "alta") return "chip-alta";
    if (v === "baixa") return "chip-corte";
    if (v === "media" || v === "média") return "chip-aviso";
    return "chip-mudo";
  }

  function classeGravidade(g) {
    var v = txt(g).toLowerCase();
    if (v === "alta") return "chip-corte";
    if (v === "media" || v === "média") return "chip-aviso";
    if (v === "ok") return "chip-alta";
    return "chip-mudo";
  }

  /* LED: verde sincronizado · ambar atrasado · vermelho fora do ar · cinza mudo.
     A cor vem da gravidade que o vigia MEDIU, nao de um limiar recalculado aqui. */
  function led(gravidade, veredito) {
    var g = txt(gravidade).toLowerCase();
    var v = txt(veredito).toUpperCase();
    if (g === "alta") return "led-fora";
    if (g === "media" || g === "média" || g === "baixa") return "led-atraso";
    if (g === "ok" || v === "OK") return "led-ok";
    return "led-mudo";
  }

  /* ------------------------------------------------------------------ dados */

  function busca(caminho) {
    try {
      return raiz.fetch(caminho + "?t=" + Date.now(), { cache: "no-store" })
        .then(function (r) { return r && r.ok ? r.json() : null; })
        .catch(function () { return null; });
    } catch (e) {
      return Promise.resolve(null);
    }
  }

  function carrega() {
    return busca("data/agentes/indice.json").then(function (indice) {
      var nomes = [];
      if (ehObj(indice) && Array.isArray(indice.agentes)) {
        indice.agentes.forEach(function (a) {
          var n = txt(ehObj(a) ? a.nome : a);
          if (n && nomes.indexOf(n) < 0) nomes.push(n);
        });
      }
      if (!nomes.length) nomes = AGENTES_PADRAO.slice();
      return Promise.all(nomes.map(function (n) {
        return busca("data/agentes/" + n + "/ultimo.json").then(function (d) {
          return { nome: n, dado: ehObj(d) ? d : null };
        });
      })).then(function (lista) {
        var por = {};
        lista.forEach(function (x) { por[x.nome] = x.dado; });
        return { indice: ehObj(indice) ? indice : null, nomes: nomes, agentes: por };
      });
    });
  }

  /* =========================================================== PECA 1 · FAIXA
     Faixa de estado do topo, alimentada SO pelo vigia. Um segmento por fonte.
     ======================================================================== */

  /* Nome curto da fonte: "IDADE/data/sentimento.json" -> "sentimento".
     E recorte de texto, nao interpretacao: o caminho inteiro fica no title. */
  function nomeCurto(chave) {
    return txt(chave)
      .replace(/^IDADE\//, "")
      .replace(/^data\//, "")
      .replace(/\.json$/i, "")
      .replace(/^https?:\/\/[^/]*\//, "");
  }

  function ehFonte(j) { return /^IDADE\//.test(txt(j && j.chave)); }

  function segmento(cls, rotulo, valor, nota, titulo) {
    return '<div class="faixa-seg"' + (titulo ? ' title="' + esc(titulo) + '"' : "") + ">" +
      '<span class="led ' + cls + '" aria-hidden="true"></span>' +
      '<span class="rot">' + esc(rotulo) + "</span>" +
      (valor ? '<b class="num">' + esc(valor) + "</b>" : "") +
      (nota ? "<span>" + esc(nota) + "</span>" : "") +
      "</div>";
  }

  /* Um alarme so entra se tiver MEDIDA e CONSEQUENCIA escritas. Sem consequencia
     e decoracao — e o filtro devolve quantos caiu, para a tela poder dize-lo. */
  function alarmesDoVigia(vig) {
    var todos = (ehObj(vig) && Array.isArray(vig.julgamentos)) ? vig.julgamentos : [];
    var candidatos = todos.filter(function (j) {
      var g = txt(j && j.gravidade).toLowerCase();
      return ehObj(j) && g && g !== "ok";
    });
    var bons = candidatos.filter(function (j) { return txt(j.medida) && txt(j.consequencia); });
    return { lista: bons, mudos: candidatos.length - bons.length };
  }

  function blocoAlarme(vig) {
    var a = alarmesDoVigia(vig);
    if (!a.lista.length) return "";

    var versao = txt(vig.versao_prompt) || "versão do prompt não declarada";
    var rodada = txt(vig.rodada_id);
    var quando = carimbo(vig.gerado_em);
    var placar = ehObj(vig.placar) ? vig.placar : {};
    var selo = txt(a.lista[0].selo);
    var idade = idadeMin(vig.gerado_em);
    var velho = idade !== null && idade > VIGIA_TOLERANCIA_MIN;

    var linhas = a.lista.map(function (j) {
      return '<div class="alarme">' +
        "<div>" +
          '<span class="identificador">' + esc(txt(j.chave) || "sem identificador") + "</span>" +
          chip(txt(j.gravidade) || "sem gravidade", classeGravidade(j.gravidade)) +
        "</div>" +
        "<div>" +
          '<span class="rot">assunto</span>' +
          '<span class="assunto">' + esc(txt(j.assunto) || txt(j.veredito) || "não declarado") + "</span>" +
        "</div>" +
        "<div>" +
          '<span class="rot">medida</span>' +
          '<span class="medida">' + esc(j.medida) + "</span>" +
        "</div>" +
        "<div>" +
          '<span class="rot">consequência</span>' +
          '<span class="consequencia">' + esc(j.consequencia) + "</span>" +
        "</div>" +
      "</div>";
    }).join("");

    var contagem = ehNum(placar.alarmes_alta) || ehNum(placar.alarmes_media) || ehNum(placar.alarmes_baixa)
      ? [["alta", placar.alarmes_alta], ["média", placar.alarmes_media], ["baixa", placar.alarmes_baixa]]
        .filter(function (p) { return ehNum(p[1]) && p[1] > 0; })
        .map(function (p) { return num(p[1], 0) + " " + p[0]; }).join(" · ")
      : "";

    return '<section class="alarme-bloco" role="alert" aria-label="alarmes do vigia">' +
      '<div class="alarme-cab">' +
        '<span class="rot">estado degradado — ' + esc(num(a.lista.length, 0)) + " de " +
          esc(num((ehObj(vig.julgamentos) ? vig.julgamentos.length : 0), 0)) + " checagens</span>" +
        chip("medido", "chip-mudo") +
        (idade !== null
          ? '<span class="chip ' + (velho ? "chip-aviso" : "chip-mudo") + '">medido ha ' +
            esc(idadeTexto(idade)) + "</span>"
          : "") +
        (contagem ? '<span class="chip chip-aviso">' + esc(contagem) + "</span>" : "") +
        '<span class="verificacao">' + esc(versao) +
          (rodada ? " · " + esc(rodada) : "") +
          (quando ? " · " + esc(quando) : "") + "</span>" +
      "</div>" +
      (velho
        ? '<div class="alarme-escopo alarme-velho"><strong>Esta medição tem ' +
          esc(idadeTexto(idade)) + ' — ela descreve o sistema como ele estava naquele ' +
          'instante, não agora.</strong> As linhas abaixo podem já ter sido resolvidas ou ' +
          'piorado. O vigia roda de hora em hora na VPS; passar de 3 h significa que ' +
          'ele próprio parou.</div>'
        : "") +
      '<div class="alarme-escopo"><em>Isto é medição da operação do sistema, não leitura de mercado: ' +
        'nenhuma linha abaixo vota na direção de moeda nenhuma e nenhuma invalida a tabela — todas ' +
        'mudam o peso do que está na tela.' +
        (selo ? " Selo declarado pelo próprio arquivo: " + esc(selo) + "." : "") +
        (a.mudos > 0 ? " " + esc(num(a.mudos, 0)) + " aviso(s) do vigia ficaram de fora por não trazerem " +
          "consequência escrita — aviso sem consequência é decoração." : "") +
      "</em></div>" +
      linhas +
    "</section>";
  }

  function faixaHTML(vig) {
    var segs = [];
    var alarmes = alarmesDoVigia(vig);

    if (!ehObj(vig)) {
      /* Nao inventa "fora do ar": o que se sabe e que o arquivo nao foi lido. */
      segs.push(segmento("led-mudo", "vigia", "",
        "não foi possível ler data/agentes/vigia/ultimo.json nesta carga",
        "A faixa de estado depende desse arquivo. Sem ele não há medição para mostrar, e nada é presumido."));
      return { faixa: '<div class="faixa-estado" role="status" aria-label="estado das fontes">' +
        segs.join("") + "</div>", alarme: "", n: 0 };
    }

    var placar = ehObj(vig.placar) ? vig.placar : {};
    var geral = txt(placar.estado_geral).toLowerCase();
    var clsGeral = geral === "verde" ? "led-ok" : (geral === "vermelho" ? "led-fora" : (geral ? "led-atraso" : "led-mudo"));
    var ok = ehNum(placar.checagens_ok) ? num(placar.checagens_ok, 0) : null;
    var total = Array.isArray(vig.julgamentos) ? num(vig.julgamentos.length, 0) : null;

    /* Segmento 1 — o proprio vigia, com proveniencia e o botao que abre a tarja.
       Vem PRIMEIRO de proposito: a faixa rola na horizontal, e o estado geral
       nao pode depender de o leitor rolar para ve-lo. */
    var resumo = ok && total ? ok + " de " + total + " ok" : (geral ? geral : "sem placar");
    if (alarmes.lista.length) {
      segs.push('<button type="button" class="faixa-seg faixa-toggle" id="faixaToggle" ' +
        'aria-expanded="false" aria-controls="faixaAlarmes" ' +
        'title="' + esc("Abre o bloco de alarme: identificador, medida e consequência de cada um.") + '">' +
        '<span class="led ' + clsGeral + '" aria-hidden="true"></span>' +
        '<span class="rot">vigia</span>' +
        '<b class="num">' + esc(num(alarmes.lista.length, 0)) + " alarmes</b>" +
        "<span>· " + esc(resumo) + " · abrir</span></button>");
    } else {
      segs.push(segmento(clsGeral, "vigia", "", resumo,
        "Medição de operação escrita por " + (txt(vig.versao_prompt) || "vigia") +
        " em " + (carimbo(vig.gerado_em) || "carimbo não declarado") + "."));
    }

    /* Um LED por fonte. A ordem e a do arquivo — nao ha reordenacao por
       gravidade, senao a faixa muda de forma a cada rodada e deixa de ser regua. */
    var fontes = (Array.isArray(vig.julgamentos) ? vig.julgamentos : []).filter(ehFonte);
    fontes.forEach(function (j) {
      var n = ehObj(j.numeros_citados) ? j.numeros_citados : {};
      var idade = ehNum(n.idade_min) ? num(n.idade_min, 1) + " min" : "não medido";
      var tol = ehNum(n.tolerancia_min) ? "tolerância " + num(n.tolerancia_min, 0) + " min" : "";
      segs.push(segmento(led(j.gravidade, j.veredito), nomeCurto(j.chave), idade, tol,
        (txt(j.medida) || txt(j.motivo) || "") +
        (txt(j.consequencia) ? "  →  " + j.consequencia : "")));
    });

    /* As esteiras (execucao, cancelamento, pulo) nao sao FONTES de dado: sao o
       transporte. Entram agregadas e ditas com esse nome, para nao se passarem
       por fonte na contagem de LEDs. */
    var esteiras = (Array.isArray(vig.julgamentos) ? vig.julgamentos : []).filter(function (j) {
      return !ehFonte(j) && txt(j.chave);
    });
    if (esteiras.length) {
      var ruins = esteiras.filter(function (j) { return txt(j.gravidade).toLowerCase() !== "ok"; });
      var pior = ruins.some(function (j) { return txt(j.gravidade).toLowerCase() === "alta"; })
        ? "led-fora" : (ruins.length ? "led-atraso" : "led-ok");
      segs.push(segmento(pior, "esteiras",
        num(esteiras.length - ruins.length, 0) + " de " + num(esteiras.length, 0) + " ok", "",
        esteiras.map(function (j) { return txt(j.chave) + ": " + (txt(j.veredito) || "?"); }).join(" · ")));
    }

    return {
      faixa: '<div class="faixa-estado" role="status" aria-label="estado das fontes">' + segs.join("") + "</div>",
      alarme: blocoAlarme(vig),
      n: alarmes.lista.length
    };
  }

  function montaFaixa(vig) {
    /* aplica() do ui_macro roda em laco; aqui a montagem e por carga, mas a
       guarda fica de qualquer forma: faixa duplicada empilha 30px sobre o
       cabecalho e cobre a navegacao. */
    var velha = document.querySelector(".faixa-estado");
    var velhoBloco = document.getElementById("faixaAlarmes");
    if (velha && velha.parentNode) velha.parentNode.removeChild(velha);
    if (velhoBloco && velhoBloco.parentNode) velhoBloco.parentNode.removeChild(velhoBloco);

    var peca = faixaHTML(vig);
    var html = peca.faixa +
      (peca.alarme ? '<div class="faixa-alarmes" id="faixaAlarmes" hidden>' + peca.alarme + "</div>" : "");

    /* afterbegin no <body>, e nao dentro do <main>: a faixa e position:sticky e
       a regra `body:has(> .faixa-estado) .site-header{top:30px}` do estilo_hci.css
       so casa quando ela e filha DIRETA do body. Dentro do main, as duas barras
       grudadas no topo se cobrem. */
    document.body.insertAdjacentHTML("afterbegin", html);

    var bt = document.getElementById("faixaToggle");
    var caixa = document.getElementById("faixaAlarmes");
    if (bt && caixa) {
      bt.addEventListener("click", function () {
        var abrir = caixa.hidden;
        caixa.hidden = !abrir;
        bt.setAttribute("aria-expanded", abrir ? "true" : "false");
        var fim = bt.querySelector("span:last-child");
        if (fim) fim.textContent = fim.textContent.replace(abrir ? "· abrir" : "· fechar", abrir ? "· fechar" : "· abrir");
      });
    }
  }

  /* ============================================================ PECA 2 · SALA
     Sala de julgamentos: por moeda, o que cada agente julgou.
     ======================================================================== */

  /* A moeda de um julgamento sai da CHAVE, nunca do texto do motivo: ler moeda
     dentro de prosa e adivinhacao. "USD" -> USD; "USD/Waller" -> USD;
     "noticia@v1:USD" -> USD (e o alvo confirma); "evento/..." -> nenhuma. */
  function moedaDe(j) {
    var candidatos = [];
    if (ehObj(j)) {
      if (ehObj(j.alvo) && txt(j.alvo.chave)) candidatos.push(j.alvo.chave);
      if (txt(j.moeda)) candidatos.push(j.moeda);
      if (txt(j.chave)) candidatos.push(j.chave);
    }
    for (var i = 0; i < candidatos.length; i++) {
      var pedacos = String(candidatos[i]).split(/[/:|@\s]+/);
      for (var k = 0; k < pedacos.length; k++) {
        var p = pedacos[k].toUpperCase();
        if (MOEDAS.indexOf(p) >= 0) return p;
      }
    }
    return null;
  }

  /* Indice das objecoes do advogado, chaveado por (agente alvo, chave alvo). */
  function indiceObjecoes(adv) {
    var mapa = {};
    if (!ehObj(adv) || !Array.isArray(adv.julgamentos)) return mapa;
    adv.julgamentos.forEach(function (j) {
      if (!ehObj(j) || !ehObj(j.alvo)) return;
      var k = txt(j.alvo.agente) + " " + txt(j.alvo.chave);
      if (!mapa[k]) mapa[k] = [];
      mapa[k].push(j);
    });
    return mapa;
  }

  function objecaoHTML(objs, adv) {
    var versaoAdv = txt(adv && adv.versao_prompt) || "advogado";
    if (!objs || !objs.length) {
      return '<div class="sala-objecao sala-objecao-vazia">' +
        '<div class="sala-cab"><span class="rot">objeção do advogado</span>' +
          chip("nada registrado", "chip-mudo") + "</div>" +
        '<p class="sala-prosa">O advogado não registrou objeção a este item nesta rodada. ' +
        'Silêncio não é aval: pode ser que ele não o tenha auditado.</p></div>';
    }
    return objs.map(function (o) {
      var s = selos(o, adv);
      var derruba = o.derruba_a_tese === true;
      return '<div class="sala-objecao' + (derruba ? " sala-objecao-grave" : "") + '">' +
        '<div class="sala-cab">' +
          '<span class="rot">objeção do advogado</span>' +
          chip(txt(o.veredito) || "sem veredito", derruba ? "chip-corte" : classeGravidade(o.gravidade)) +
          chip("gravidade " + (txt(o.gravidade) || "não declarada"), classeGravidade(o.gravidade)) +
          chip(derruba ? "derruba a tese" : "não derruba a tese", derruba ? "chip-corte" : "chip-mudo") +
          s.chips +
          '<span class="procedencia">' + esc(versaoAdv) +
            (txt(adv && adv.gerado_em) ? " · " + esc(carimbo(adv.gerado_em)) : "") + "</span>" +
        "</div>" +
        (txt(o.motivo) ? '<p class="sala-prosa">' + esc(o.motivo) + "</p>" : "") +
        (txt(o.o_que_o_site_faz)
          ? '<p class="sala-consequencia"><span class="rot">o que o site faz</span>' + esc(o.o_que_o_site_faz) + "</p>"
          : "") +
        link(o.fonte) +
        (s.selo ? '<p class="sala-selo">' + esc(s.selo) + "</p>" : "") +
      "</div>";
    }).join("");
  }

  function teseHTML(nome, dado, j, objs, adv) {
    var s = selos(j, dado);
    var versao = txt(dado && dado.versao_prompt) || "versão do prompt não declarada";
    var trechoDe = txt(j.trecho_de);
    var nums = ehObj(j.numeros_citados) ? Object.keys(j.numeros_citados) : [];

    var tese = '<div class="sala-tese">' +
      '<div class="sala-cab">' +
        '<span class="rot">' + esc(nome) + "</span>" +
        chip(txt(j.chave) || "sem chave", "chip-mudo") +
        chip(txt(j.veredito) || "sem veredito", "chip-marca") +
        chip("confiança " + (txt(j.confianca) || "não declarada"), classeConfianca(j.confianca)) +
        s.chips +
        '<span class="procedencia">' + esc(versao) +
          (txt(dado && dado.gerado_em) ? " · " + esc(carimbo(dado.gerado_em)) : "") +
          (txt(dado && dado.rodada_id) ? " · " + esc(dado.rodada_id) : "") + "</span>" +
      "</div>" +
      (txt(j.trecho)
        ? '<blockquote class="sala-trecho">' + esc(j.trecho) +
          (trechoDe ? '<cite class="sala-trecho-de">' + esc(trechoDe) + "</cite>" : "") + "</blockquote>"
        : '<p class="sala-vazio-linha">Sem trecho citado neste julgamento.</p>') +
      (txt(j.motivo) ? '<p class="sala-prosa">' + esc(j.motivo) + "</p>" : "") +
      link(j.fonte) +
      (nums.length
        ? '<p class="sala-nums"><span class="rot">números citados</span>' +
          nums.map(function (k) {
            var v = j.numeros_citados[k];
            var mostra = ehNum(v) ? num(v, 4) : (v == null ? "não medido" : String(v));
            return '<span class="sala-par"><i>' + esc(k) + '</i><b class="num">' + esc(mostra) + "</b></span>";
          }).join("") + "</p>"
        : "") +
      (s.selo ? '<p class="sala-selo">' + esc(s.selo) + "</p>" : "") +
    "</div>";

    return '<div class="sala-jul"><div class="sala-dupla">' + tese + objecaoHTML(objs, adv) + "</div></div>";
  }

  function ledgerHTML(est) {
    var indice = est.indice;
    var linhas = est.nomes.map(function (n) {
      var d = est.agentes[n];
      var meta = null;
      if (indice && Array.isArray(indice.agentes)) {
        indice.agentes.forEach(function (a) { if (ehObj(a) && txt(a.nome) === n) meta = a; });
      }
      if (!d) {
        return '<div class="cartao sala-ficha">' +
          '<div class="cartao-cab"><span class="rot">' + esc(n) + "</span>" +
            chip("sem arquivo", "chip-aviso") + "</div>" +
          '<div class="cartao-corpo"><p class="sala-prosa">Não foi possível ler ' +
            '<span class="sala-caminho">data/agentes/' + esc(n) + '/ultimo.json</span> nesta carga. ' +
            "Nada é presumido no lugar dele." +
            (meta && txt(meta.ultima_rodada) ? " O índice registra a última rodada em " +
              esc(carimbo(meta.ultima_rodada)) + "." : "") + "</p></div></div>";
      }
      var nj = Array.isArray(d.julgamentos) ? d.julgamentos.length : 0;
      var nn = Array.isArray(d.nao_julgados) ? d.nao_julgados.length : 0;
      var nl = Array.isArray(d.limites) ? d.limites.length : 0;
      return '<div class="cartao sala-ficha">' +
        '<div class="cartao-cab"><span class="rot">' + esc(n) + "</span>" +
          chip(txt(d.versao_prompt) || "versão não declarada", "chip-mudo") +
          (n === VIGIA ? chip("medido", "chip-mudo") : chip("julgado", "chip-marca")) +
          (d.vota === false || (nj && d.julgamentos[0] && d.julgamentos[0].vota === false)
            ? chip("não vota", "chip-aviso") : "") +
        "</div>" +
        '<div class="cartao-corpo">' +
          '<p class="sala-linha"><span class="rot">rodada</span><b>' + esc(carimbo(d.gerado_em) || "carimbo não declarado") + "</b></p>" +
          (txt(d.rodada_id) ? '<p class="sala-linha"><span class="rot">id</span><span class="sala-caminho">' + esc(d.rodada_id) + "</span></p>" : "") +
          '<p class="sala-linha"><span class="rot">julgou</span><b class="num">' + esc(num(nj, 0)) + "</b></p>" +
          '<p class="sala-linha"><span class="rot">deixou de julgar</span><b class="num">' + esc(num(nn, 0)) +
            "</b></p>" +
          '<p class="sala-linha"><span class="rot">limites declarados</span><b class="num">' + esc(num(nl, 0)) +
            "</b></p>" +
          (ehObj(d.entradas) && txt(d.entradas.arquivo)
            ? '<p class="sala-linha"><span class="rot">leu</span><span class="sala-caminho">' + esc(d.entradas.arquivo) + "</span></p>"
            : "") +
        "</div></div>";
    }).join("");
    return '<div class="sala-ledger">' + linhas + "</div>";
  }

  function pendenciasHTML(est) {
    var partes = est.nomes.map(function (n) {
      var d = est.agentes[n];
      if (!d) return "";
      var nao = Array.isArray(d.nao_julgados) ? d.nao_julgados : [];
      var lim = Array.isArray(d.limites) ? d.limites : [];
      if (!nao.length && !lim.length) return "";
      return "<details class=\"metodo sala-pend\"><summary class=\"metodo-cab\">" +
        '<span class="rot">' + esc(n) + "</span>" +
        '<span class="sala-pend-cont">' + esc(num(nao.length, 0)) + " sem julgamento · " +
          esc(num(lim.length, 0)) + " limites declarados</span></summary>" +
        '<div class="metodo-corpo">' +
          (nao.length
            ? "<p><span class=\"rot\">o que ficou sem julgamento — e por quê</span></p><ul class=\"sala-lista\">" +
              nao.map(function (x) {
                var k = txt(ehObj(x) ? x.chave : x);
                var p = txt(ehObj(x) ? x.porque : "");
                return "<li><b>" + esc(k || "item") + "</b>" + (p ? " — " + esc(p) : "") + "</li>";
              }).join("") + "</ul>"
            : "") +
          (lim.length
            ? "<p><span class=\"rot\">limites que o próprio agente declara</span></p><ul class=\"sala-lista\">" +
              lim.map(function (x) { return "<li>" + esc(txt(ehObj(x) ? (x.texto || x.limite) : x)) + "</li>"; }).join("") + "</ul>"
            : "") +
        "</div></details>";
    }).filter(Boolean).join("");
    if (!partes) return "";
    return '<section class="cartao sala-bloco"><div class="cartao-cab">' +
      '<span class="rot">o que ficou de fora</span>' +
      '<span class="procedencia">campos nao_julgados e limites, lidos de cada ultimo.json</span>' +
      '</div><div class="cartao-corpo">' +
      '<p class="sala-prosa">Silêncio não é voto. O que um agente não julgou fica aqui, com o motivo ' +
      'escrito por ele — isto é informação sobre a cobertura, não falha.</p>' + partes + "</div></section>";
  }

  function salaHTML(est) {
    var adv = est.agentes[ADVOGADO] || null;
    var objecoes = indiceObjecoes(adv);

    /* Teses = todo agente que nao e o advogado (que objeta) nem o vigia (que
       mede operacao, nao mercado). */
    var teses = est.nomes.filter(function (n) { return n !== ADVOGADO && n !== VIGIA; });

    var baldes = {};
    MOEDAS.forEach(function (m) { baldes[m] = []; });
    var semMoeda = [];
    var total = 0;

    teses.forEach(function (n) {
      var d = est.agentes[n];
      if (!ehObj(d) || !Array.isArray(d.julgamentos)) return;
      d.julgamentos.forEach(function (j) {
        if (!ehObj(j)) return;
        total++;
        var item = { nome: n, dado: d, j: j, objs: objecoes[n + " " + txt(j.chave)] || null };
        var m = moedaDe(j);
        if (m && baldes[m]) baldes[m].push(item); else semMoeda.push(item);
      });
    });

    if (!total) {
      return '<div class="mac-vazio"><p><b>Nenhum julgamento ainda.</b> ' +
        'Nenhum arquivo <span class="sala-caminho">data/agentes/*/ultimo.json</span> com julgamentos ' +
        'foi lido nesta carga. A sala fica vazia de propósito: ela não preenche o buraco com suposição.</p></div>' +
        ledgerHTML(est);
    }

    var blocos = MOEDAS.map(function (m) {
      var itens = baldes[m];
      if (!itens.length) {
        return '<section class="cartao sala-moeda sala-moeda-vazia">' +
          '<div class="cartao-cab"><span class="rot">' + esc(m) + "</span>" +
            chip("nenhum julgamento nesta rodada", "chip-mudo") + "</div></section>";
      }
      var quem = [];
      itens.forEach(function (it) { if (quem.indexOf(it.nome) < 0) quem.push(it.nome); });
      var comObj = itens.filter(function (it) { return it.objs && it.objs.length; }).length;
      return '<section class="cartao sala-moeda">' +
        '<div class="cartao-cab">' +
          '<span class="rot">' + esc(m) + "</span>" +
          chip(num(itens.length, 0) + " julgamento(s)", "chip-mudo") +
          chip(num(comObj, 0) + " com objeção", comObj ? "chip-aviso" : "chip-mudo") +
          '<span class="procedencia">' + esc(quem.join(" · ")) + "</span>" +
        "</div>" +
        '<div class="cartao-corpo">' +
          itens.map(function (it) { return teseHTML(it.nome, it.dado, it.j, it.objs, adv); }).join("") +
        "</div></section>";
    }).join("");

    var bloco2 = semMoeda.length
      ? '<section class="cartao sala-moeda">' +
        '<div class="cartao-cab"><span class="rot">sem moeda declarada</span>' +
          chip(num(semMoeda.length, 0) + " julgamento(s)", "chip-mudo") +
          '<span class="procedencia">a chave do julgamento não nomeia moeda</span></div>' +
        '<div class="cartao-corpo">' +
          '<p class="sala-prosa">Estes julgamentos não trazem moeda na chave (são eventos). ' +
          'A moeda sai sempre da chave — deduzi-la do texto do motivo seria adivinhação.</p>' +
          semMoeda.map(function (it) { return teseHTML(it.nome, it.dado, it.j, it.objs, adv); }).join("") +
        "</div></section>"
      : "";

    var rodape = "";
    try {
      var API = raiz.HCI_MEDIDORES;
      if (API && typeof API.notas === "function") {
        rodape = API.notas([
          { termo: "experimental — contexto, não vota",
            texto: "é o selo que os próprios arquivos dos agentes declaram no campo `selo`. Enquanto ele estiver lá, nada nesta aba entra no cálculo da direção: serve para explicar, não para decidir." },
          { termo: "MEDIDO · JULGADO · EM TESTE",
            texto: "MEDIDO sai do campo `natureza` do arquivo (hoje só o vigia o escreve); JULGADO é saída de agente; EM TESTE vem do campo `vota` valendo false. Nenhum dos três é inferido do texto." },
          { termo: "a objeção ao lado da tese",
            texto: "o advogado grava o alvo em `alvo.agente` + `alvo.chave`, e é por esse par que a objeção é casada com a tese. Objeção sem alvo casado não é escondida: ela aparece na ficha do advogado, no bloco de proveniência." },
          { termo: "convicção histórica",
            texto: "continua nula: não há backtest destes julgamentos. Nada nesta aba é ordem, sinal de entrada ou promessa de retorno — a entrada é sua." }
        ]).bloco() || "";
      }
    } catch (e) { rodape = ""; }

    return ledgerHTML(est) + blocos + bloco2 + pendenciasHTML(est) +
      '<p class="method-note">Cada bloco desta aba diz <b>quem falou</b> (agente e versão do prompt), ' +
      '<b>quando</b>, <b>com que fonte</b> e o <b>selo</b>. Os números aparecem como estão nos arquivos, ' +
      'sem nenhuma conta feita aqui; onde o arquivo não traz o número, está escrito “não medido”. ' +
      "Leitura do lado fundamental, não sinal de entrada.</p>" + rodape;
  }

  function montaSala(est) {
    var alvo = document.getElementById("salaJulgamentos");
    if (!alvo) return;
    try {
      alvo.innerHTML = salaHTML(est);
    } catch (e) {
      alvo.innerHTML = '<div class="mac-vazio"><p><b>Nenhum julgamento ainda.</b> ' +
        "A sala não conseguiu montar nesta carga e prefere ficar vazia a mostrar coisa inventada.</p></div>";
      if (raiz.console && raiz.console.warn) raiz.console.warn("[ui_agentes] sala contida:", e && e.message);
    }
  }

  /* ------------------------------------------------------------------ ligar */

  var estado = null;
  var carregando = false;

  function atualiza() {
    if (carregando) return;
    carregando = true;
    carrega().then(function (est) {
      carregando = false;
      estado = est;
      try { montaFaixa(est.agentes[VIGIA]); } catch (e) {
        if (raiz.console && raiz.console.warn) raiz.console.warn("[ui_agentes] faixa contida:", e && e.message);
      }
      montaSala(est);
    }).catch(function (e) {
      carregando = false;
      if (raiz.console && raiz.console.warn) raiz.console.warn("[ui_agentes] carga contida:", e && e.message);
      montaSala({ indice: null, nomes: AGENTES_PADRAO.slice(), agentes: {} });
    });
  }

  function iniciar() {
    atualiza();
    var bar = document.getElementById("tabBar");
    if (bar) {
      bar.addEventListener("click", function (e) {
        var b = e.target && e.target.closest ? e.target.closest(".tab") : null;
        if (b && b.dataset && b.dataset.tab === "agentes" && estado) montaSala(estado);
      });
    }
    var bt = document.getElementById("updateButton");
    if (bt) bt.addEventListener("click", function () { setTimeout(atualiza, 1200); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }

  raiz.HCI_AGENTES = { VERSAO: VERSAO, atualiza: atualiza };
})(typeof window !== "undefined" ? window : this);
