/* ============================================================================
   ui_medidores.js — HCI MACRO DIRECTION
   Peças gráficas e estruturais da direção C ("sala de controle").
   Especificação: especificacao_visual.md v1.0 (§6.1, §6.4, §6.6, §6.7).

   Módulo JavaScript puro, sem dependência. Expõe window.HCI_MEDIDORES.
   Quem chama é o ui_macro.js. Este arquivo NÃO toca no DOM: toda função
   devolve STRING de HTML já escapada, e nunca lança.

   LEIS DESTE ARQUIVO
   1. nada de HTML com dado não escapado — tudo passa por escapar().
   2. faltou dado, devolve string vazia. Nunca "undefined", nunca "NaN".
   3. nenhum estilo inline com COR. Só medida (width/left em %), que é dado.
   4. SVG inline herda a cor por currentColor; classe .med-* manda na cor.
   5. reforço gráfico leva aria-hidden="true" e o número fica em texto ao lado.

   ---------------------------------------------------------------------------
   CONTRATO DE CSS — o estilo_hci.css precisa definir estas classes .med-*.
   Cópia pronta para colar (usa os tokens da §1 da especificação):

   .med-num{font-family:var(--mono);font-variant-numeric:tabular-nums lining-nums;letter-spacing:-.01em}
   .med-oculto{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

   .med-faixa{position:sticky;top:0;z-index:40;display:flex;align-items:stretch;height:30px;
     background:var(--fundo-band);border-bottom:1px solid var(--regua);
     font-family:var(--mono);font-size:10.5px;color:var(--tinta-2);overflow-x:auto;scrollbar-width:thin}
   .med-faixa-seg{display:flex;align-items:center;gap:6px;padding:0 12px;white-space:nowrap;
     border-right:1px solid var(--regua-fraca)}
   .med-faixa-seg.med-faixa-fim{border-right:0;border-left:1px solid var(--regua-fraca);margin-left:auto}
   .med-faixa-chave{color:var(--tinta-3)}
   .med-faixa-valor{color:var(--tinta);font-weight:600}
   .med-faixa-nota{color:var(--tinta-3)}
   .med-led{width:6px;height:6px;border-radius:50%;flex:none}
   .med-led-ok{background:var(--alta)} .med-led-av{background:var(--aviso)}
   .med-led-off{background:var(--corte)} .med-led-mudo{background:#2C4A42}

   .med-escala-eixo{display:grid;grid-template-columns:52px 1fr 60px;gap:8px;align-items:center;padding-bottom:6px}
   .med-escala-eixo .e-neg{color:var(--corte);font-family:var(--mono);font-size:9.5px}
   .med-escala-eixo .e-zero{color:var(--tinta-3);font-family:var(--mono);font-size:9.5px;text-align:center}
   .med-escala-eixo .e-pos{color:var(--alta);font-family:var(--mono);font-size:9.5px;text-align:right}
   .med-escala-linha{display:grid;grid-template-columns:52px 1fr 60px;gap:8px;align-items:center;
     padding:3.5px 0;border-top:1px solid var(--regua-fraca)}
   .med-escala-linha:first-of-type{border-top:0}
   .med-escala-cod{font-family:var(--mono);font-size:11.5px;font-weight:600;color:var(--tinta)}
   .med-escala-cod sup{font-size:8px;color:var(--tinta-3);font-weight:400;margin-left:2px}
   .med-trilho{position:relative;height:15px;background:var(--fundo-band);
     border:1px solid var(--regua-fraca);border-radius:2px;overflow:hidden}
   .med-trilho-zero{position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--regua-forte)}
   .med-barra{position:absolute;top:3px;bottom:3px;border-radius:1px}
   .med-barra-pos{left:50%;background:var(--alta)} .med-barra-neg{right:50%;background:var(--corte)}
   .med-barra-oca{background:transparent;border:1px solid}
   .med-barra-oca.med-barra-pos{border-color:var(--alta)} .med-barra-oca.med-barra-neg{border-color:var(--corte)}
   .med-escala-vl{font-family:var(--mono);font-size:11.5px;text-align:right;color:var(--tinta)}
   .med-escala-vl.alta{color:var(--alta)} .med-escala-vl.corte{color:var(--corte)}
   .med-legenda{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;padding-top:8px;
     border-top:1px solid var(--regua);font-family:var(--mono);font-size:9.5px;color:var(--tinta-3)}
   .med-legenda b{color:var(--tinta-2);font-weight:500}
   .med-legenda i{display:inline-block;width:14px;height:6px;border-radius:1px;transform:translateY(-1px)}
   .med-legenda i.cheia{background:var(--alta)} .med-legenda i.oca{border:1px solid var(--alta)}

   .med-faixa-agulha{margin-top:2px}
   .med-bandas{position:relative;height:22px;display:flex;border:1px solid var(--regua-forte);
     border-radius:2px;background:var(--fundo-band)}
   .med-banda{position:relative;height:100%}
   .med-banda+.med-banda{border-left:1px solid var(--regua-forte)}
   .med-banda-1{background:rgba(159,182,175,.04)} .med-banda-2{background:rgba(79,208,142,.05)}
   .med-banda-3{background:rgba(79,208,142,.08)}  .med-banda-4{background:rgba(79,208,142,.12)}
   .med-agulha{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--marca);z-index:3}
   .med-agulha::before{content:"";position:absolute;top:-1px;left:-3px;border-left:4px solid transparent;
     border-right:4px solid transparent;border-top:5px solid var(--marca)}
   .med-bandas-rot{display:flex;margin-top:4px;font-family:var(--mono);font-size:9.5px;color:var(--tinta-3)}
   .med-bandas-rot span{border-left:1px solid var(--regua-fraca);padding-left:4px}
   .med-bandas-rot span:first-child{border-left:0;padding-left:0}
   .med-agulha-num{margin-top:6px;font-family:var(--mono);font-size:9.5px;color:var(--tinta-2)}
   .med-agulha-num b{color:var(--tinta);font-weight:600}

   .med-qual{display:grid;grid-template-columns:70px 1fr 44px;gap:8px;align-items:center;padding:2.5px 0}
   .med-qual-nm{font-family:var(--mono);font-size:9.5px;color:var(--tinta-3);text-transform:uppercase;letter-spacing:.05em}
   .med-qual-trilho{position:relative;height:6px;background:var(--fundo-band);border:1px solid var(--regua-fraca);
     border-radius:1px;overflow:hidden}
   .med-qual-fl{position:absolute;inset:0 auto 0 0;background:var(--tinta-2)}
   .med-qual-fl.av{background:var(--aviso)}
   .med-qual-trilho.med-vazio{background:repeating-linear-gradient(45deg,var(--fundo-band) 0 3px,rgba(240,178,82,.13) 3px 6px);
     border:1px dashed rgba(240,178,82,.55)}
   .med-qual-vv{font-family:var(--mono);font-size:10.5px;text-align:right;color:var(--tinta-2)}
   .med-qual-vv.av{color:var(--aviso)}

   .med-dias{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
   .med-dias-num{font-family:var(--mono);font-size:14px;font-weight:600;color:var(--tinta);flex:none}
   .med-dias-num.av{color:var(--aviso)}
   .med-dias-rot{font-family:var(--mono);font-size:9.5px;color:var(--tinta-3)}
   .med-dias-regua{display:flex;align-items:flex-end;gap:1.5px;height:13px}
   .med-dias-regua i{width:2px;height:5px;display:block;border-radius:.5px;background:var(--regua-forte)}
   .med-dias-regua i.alto{height:9px}
   .med-dias-regua i.on{background:var(--marca)}
   .med-dias-regua i.av{background:var(--aviso)}
   .med-dias-regua i.fim{width:3px;height:13px;background:var(--tinta-2)}
   .med-dias-regua i.fim.av{background:var(--aviso)}

   .med-alarme{border:1px solid rgba(240,178,82,.38);background:var(--aviso-fraca);border-radius:3px;overflow:hidden}
   .med-alarme-cab{display:flex;align-items:center;gap:8px;padding:5px 12px;
     border-bottom:1px solid rgba(240,178,82,.24)}
   .med-alarme-cab .rot{color:var(--aviso)}
   .med-alarme-verif{margin-left:auto;font-family:var(--mono);font-size:10.5px;color:var(--aviso)}
   .med-alarme-escopo{padding:7px 12px;border-bottom:1px solid rgba(240,178,82,.16);
     font-size:11.5px;line-height:1.5;color:var(--tinta-2)}
   .med-alarme-linha{display:grid;grid-template-columns:96px 190px 1fr 1fr;
     border-top:1px solid rgba(240,178,82,.16);align-items:stretch}
   .med-alarme-linha:first-of-type{border-top:0}
   .med-alarme-linha>div{padding:8px 12px;border-left:1px solid rgba(240,178,82,.16);min-width:0}
   .med-alarme-linha>div:first-child{border-left:0;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
   .med-alarme-id{font-family:var(--mono);font-size:10.5px;color:var(--aviso);letter-spacing:.06em}
   .med-alarme-assunto{font-family:var(--mono);font-size:12.5px;color:var(--tinta);font-weight:600;
     overflow-wrap:anywhere}
   .med-alarme-k{display:block;margin-bottom:2px}
   .med-alarme-v{font-size:11.5px;line-height:1.5;color:var(--tinta-2)}
   .med-alarme-v .med-num{color:var(--tinta)}
   .med-alarme-v em{font-style:normal;color:var(--aviso)}
   .med-alarme-v b{color:var(--tinta);font-weight:600}
   @media(max-width:900px){.med-alarme-linha{grid-template-columns:1fr}
     .med-alarme-linha>div{border-left:0;border-top:1px solid rgba(240,178,82,.12)}}

   .med-chip{display:inline-flex;align-items:center;height:18px;padding:0 6px;border-radius:2px;
     border:1px solid;font-family:var(--mono);font-size:9.5px;letter-spacing:.05em;white-space:nowrap}
   .med-chip-aviso{color:var(--aviso);border-color:rgba(240,178,82,.42);background:var(--aviso-fraca)}
   .med-chip-corte{color:var(--corte);border-color:rgba(255,124,104,.42);background:var(--corte-fraca)}
   .med-chip-mudo{color:var(--tinta-3);border-color:var(--regua-forte);background:var(--painel-alto)}

   .med-nota-marca{font-family:var(--mono);font-size:9.5px;color:var(--tinta-3);margin-left:2px}
   .med-notas{border-top:1px solid var(--regua);padding-top:8px}
   .med-notas-lista{list-style:none;margin:0;padding:0}
   .med-notas-item{display:grid;grid-template-columns:22px 1fr;gap:6px;padding:6px 0;
     border-top:1px solid var(--regua-fraca)}
   .med-notas-item:first-child{border-top:0}
   .med-notas-n{font-family:var(--mono);font-size:9.5px;color:var(--tinta-3);text-align:right}
   .med-notas-txt{font-family:"Spectral",Georgia,serif;font-size:12.5px;line-height:1.62;color:var(--tinta-2)}
   .med-notas-termo{font-family:var(--mono);font-size:9.5px;color:var(--tinta-3);
     text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:2px}
   ---------------------------------------------------------------------------
============================================================================ */

(function (raiz) {
  'use strict';

  var VERSAO = '1.0.0';
  var MENOS = '−';                    // U+2212, nunca hífen
  var MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  /* ---------------------------------------------------------------- básico */

  function escapar(v) {
    if (v === null || v === undefined) return '';
    return String(v)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function ehNum(v) { return typeof v === 'number' && isFinite(v); }

  function ehObj(v) { return !!v && typeof v === 'object'; }

  // decimal com vírgula, milhar com ponto, menos tipográfico
  function fmt(v, casas) {
    if (!ehNum(v)) return '';
    var c = ehNum(casas) ? casas : 0;
    var neg = v < 0;
    var s = Math.abs(v).toFixed(c);
    var p = s.split('.');
    p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return (neg ? MENOS : '') + p.join(',');
  }

  // sinal explícito em toda variação
  function fmtSinal(v, casas) {
    if (!ehNum(v)) return '';
    var s = fmt(v, casas);
    return v > 0 ? '+' + s : s;
  }

  function data(iso) {
    if (!iso) return null;
    var d = new Date(iso);
    return isNaN(d.getTime()) ? null : d;
  }

  function dp(n) { return (n < 10 ? '0' : '') + n; }

  // 05/set 05:42Z
  function horaUTC(iso) {
    var d = data(iso);
    if (!d) return '';
    return dp(d.getUTCDate()) + '/' + MESES[d.getUTCMonth()] + ' ' +
           dp(d.getUTCHours()) + ':' + dp(d.getUTCMinutes()) + 'Z';
  }

  // 05/set/2026
  function dataCurta(iso) {
    var d = data(iso);
    if (!d) return '';
    return dp(d.getUTCDate()) + '/' + MESES[d.getUTCMonth()] + '/' + d.getUTCFullYear();
  }

  function minutosEntre(isoA, isoB) {
    var a = data(isoA), b = data(isoB);
    if (!a || !b) return null;
    return Math.round((b.getTime() - a.getTime()) / 60000);
  }

  function idadeTexto(min) {
    if (!ehNum(min)) return '';
    var m = Math.max(0, Math.round(min));
    if (m < 60) return 'há ' + m + ' min';
    var h = Math.floor(m / 60), r = m % 60;
    if (h < 24) return 'há ' + h + 'h' + (r ? ' ' + r + 'min' : '');
    return 'há ' + Math.floor(h / 24) + ' d';
  }

  function limita(v, min, max) { return Math.min(max, Math.max(min, v)); }

  // lista de itens em frase: "AUD, NZD e CHF"
  function emFrase(lista) {
    var l = (lista || []).filter(function (x) { return x !== null && x !== undefined && x !== ''; });
    if (!l.length) return '';
    if (l.length === 1) return String(l[0]);
    return l.slice(0, -1).join(', ') + ' e ' + l[l.length - 1];
  }

  function n(v) { return '<span class="med-num">' + escapar(v) + '</span>'; }

  // embrulha uma função pública: nunca lança, sempre devolve string
  function seguro(nome, fn) {
    return function () {
      try {
        var r = fn.apply(null, arguments);
        return typeof r === 'string' ? r : '';
      } catch (e) {
        if (raiz && raiz.console && raiz.console.warn) {
          raiz.console.warn('[HCI_MEDIDORES] ' + nome + ' falhou: ' + (e && e.message));
        }
        return '';
      }
    };
  }

  /* ================================================================ §6.1
     faixaEstado(sentimento [, extras])
     Faixa sticky do topo. Um segmento por fonte: LED de 6px + chave em .rot
     + valor. LED verde sincronizado, âmbar atrasado, vermelho fonte fora do
     ar, cinza informativo.

     extras (opcional, tudo degrada sozinho quando falta):
       { eventos: macro_eventos.json, eua: eua_leitura.json,
         discursos: bc_discursos.json }
     ================================================================ */

  function segmento(led, chave, valor, nota, empurra) {
    if (!valor) return '';
    return '<div class="med-faixa-seg' + (empurra ? ' med-faixa-fim' : '') + '">' +
      '<span class="med-led med-led-' + led + '" aria-hidden="true"></span>' +
      '<span class="med-faixa-chave rot">' + escapar(chave) + '</span>' +
      '<b class="med-faixa-valor med-num">' + escapar(valor) + '</b>' +
      (nota ? '<span class="med-faixa-nota">· ' + escapar(nota) + '</span>' : '') +
      '</div>';
  }

  function _faixaEstado(sentimento, extras) {
    if (!ehObj(sentimento)) return '';
    var ex = ehObj(extras) ? extras : {};
    var fr = ehObj(sentimento.frescor) ? sentimento.frescor : {};
    var lim = ehObj(fr.limiares_provisorios) ? fr.limiares_provisorios : {};
    var atrasado = ehNum(lim.atrasado_min) ? lim.atrasado_min : 45;
    var agora = sentimento.gerado_em;
    var segs = [];

    // 1 · sistema — do campo frescor
    var estado = fr.estado || '';
    var ledSis = estado === 'ok' ? 'ok' : (estado === 'muito_atrasado' ? 'off' : 'av');
    var txtSis = estado === 'ok' ? 'SINCRONIZADO'
      : (estado === 'muito_atrasado' ? 'MUITO ATRASADO' : (estado ? 'ATRASADO' : ''));
    if (txtSis) segs.push(segmento(ledSis, 'sistema', txtSis, fr.atraso_texto ? 'atraso ' + fr.atraso_texto : ''));

    // 2 · sentimento — gerado_em
    if (horaUTC(agora)) {
      segs.push(segmento('ok', 'sentimento', horaUTC(agora), fr.atraso_texto ? idadeTexto(fr.atraso_min) : ''));
    }

    // 3 · calendário — fonte_gerado_em de macro_eventos
    if (ehObj(ex.eventos)) {
      var fg = ex.eventos.fonte_gerado_em || ex.eventos.gerado_em;
      var idadeCal = minutosEntre(fg, agora);
      if (horaUTC(fg)) {
        segs.push(segmento(ehNum(idadeCal) && idadeCal > atrasado ? 'av' : 'ok',
          'calendário', horaUTC(fg),
          ehNum(ex.eventos.total) ? fmt(ex.eventos.total, 0) + ' eventos' : ''));
      }
    }

    // 4 · BLS — gerado_em de eua_leitura
    if (ehObj(ex.eua) && horaUTC(ex.eua.gerado_em)) {
      var idadeBls = minutosEntre(ex.eua.gerado_em, agora);
      segs.push(segmento(ehNum(idadeBls) && idadeBls > atrasado ? 'av' : 'ok',
        'bls', horaUTC(ex.eua.gerado_em), ''));
    }

    // 5 · fala dos bancos centrais — vermelho quando alguma fonte está fora do ar
    if (ehObj(ex.discursos) && ehObj(ex.discursos.status_fontes)) {
      var st = ex.discursos.status_fontes;
      var chaves = Object.keys(st);
      var ok = chaves.filter(function (k) { return String(st[k]).toLowerCase() === 'ok'; });
      var fora = chaves.filter(function (k) { return String(st[k]).toLowerCase() !== 'ok'; });
      if (chaves.length) {
        segs.push(segmento(fora.length ? 'off' : 'ok', 'fala do bc',
          ok.length + ' de ' + chaves.length,
          fora.length ? fora.join('·') + ' fora do ar' : ''));
      }
    }

    // 6 · referência de defasagem — informativo, cinza
    var meses = ehObj(ex.eua) ? ex.eua.defasagem_referencia_meses : null;
    if (ehNum(meses)) {
      segs.push(segmento('mudo', 'defasagem de referência',
        fmt(meses, 0) + (meses === 1 ? ' mês' : ' meses'), 'inevitável, não é atraso', true));
    }

    segs = segs.filter(Boolean);
    if (!segs.length) return '';
    return '<div class="med-faixa" role="status" aria-label="estado do sistema">' + segs.join('') + '</div>';
  }

  /* ================================================================ §6.4 · 1
     escalaDivergente(moedas)
     Ranking das 8 moedas, da mais hawkish para a mais dovish.
     Trilho de 15px, fio de zero ao centro, barra SÓLIDA quando a direção é
     declarada (SOBE/CORTA) e VAZADA quando é MANTÉM, sobrescrito n/4 com as
     dimensões que votam, legenda obrigatória embaixo.
     ================================================================ */

  function _escalaDivergente(moedas) {
    if (!ehObj(moedas)) return '';
    var lista = Array.isArray(moedas)
      ? moedas.slice()
      : Object.keys(moedas).map(function (k) {
          var m = moedas[k];
          return ehObj(m) ? (m.moeda ? m : Object.assign({ moeda: k }, m)) : null;
        });

    lista = lista.filter(function (m) { return ehObj(m) && ehNum(m.score); });
    if (!lista.length) return '';
    lista.sort(function (a, b) { return b.score - a.score; });

    var linhas = lista.map(function (m) {
      var cod = m.moeda || m.codigo || '';
      var teto = ehNum(m.score_teto_teorico) && m.score_teto_teorico > 0 ? m.score_teto_teorico
               : (ehNum(m.score_teto) && m.score_teto > 0 ? m.score_teto : 0.5);
      var larg = limita(Math.abs(m.score) / teto * 50, 0, 50);
      var dir = String(m.direcao || '').toUpperCase();
      var declarada = dir === 'SOBE' || dir === 'CORTA';
      var lado = m.score < 0 ? 'neg' : 'pos';
      var votam = ehNum(m.dimensoes_ligadas) ? m.dimensoes_ligadas
                : (Array.isArray(m.dimensoes_que_votam) ? m.dimensoes_que_votam.length : null);
      var total = ehNum(m.dimensoes_total) ? m.dimensoes_total : 4;
      var leitura = String(m.leitura || '');
      var classeVl = '';
      if (declarada || leitura === 'inclinado_alta' || leitura === 'inclinado_corte') {
        classeVl = m.score > 0 ? ' alta' : (m.score < 0 ? ' corte' : '');
      }

      return '<div class="med-escala-linha">' +
        '<div class="med-escala-cod">' + escapar(cod) +
          (ehNum(votam) ? '<sup>' + escapar(votam + '/' + total) + '</sup>' : '') + '</div>' +
        '<div class="med-trilho" aria-hidden="true">' +
          '<span class="med-trilho-zero"></span>' +
          '<span class="med-barra med-barra-' + lado + (declarada ? '' : ' med-barra-oca') +
            '" style="width:' + larg.toFixed(1) + '%"></span>' +
        '</div>' +
        '<div class="med-escala-vl' + classeVl + ' med-num">' + escapar(fmtSinal(m.score, 3)) + '</div>' +
      '</div>';
    }).join('');

    return '<div class="med-escala">' +
      '<div class="med-escala-eixo" aria-hidden="true">' +
        '<span class="e-neg">&#9664; CORTA</span>' +
        '<span class="e-zero">0</span>' +
        '<span class="e-pos">SOBE &#9654;</span>' +
      '</div>' +
      linhas +
      '<div class="med-legenda">' +
        '<span><i class="cheia" aria-hidden="true"></i> <b>sólido</b> = direção declarada (SOBE ou CORTA)</span>' +
        '<span><i class="oca" aria-hidden="true"></i> <b>vazado</b> = MANTÉM</span>' +
        '<span><b>n/4</b> = dimensões que votam</span>' +
        '<span>ordem: da mais hawkish para a mais dovish</span>' +
      '</div>' +
    '</div>';
  }

  /* ================================================================ §6.4 · 2
     faixaComAgulha(divergencia, faixas)
     Quatro bandas com os cortes 15/25/40 marcados, agulha turquesa de 2px
     com triângulo no topo, rótulo da banda embaixo.
     ================================================================ */

  var FAIXAS_PADRAO = { sem_tese: [0, 14], observacao: [15, 24], moderada: [25, 39], forte: [40, 100] };
  var NOME_FAIXA = { sem_tese: 'sem tese', observacao: 'observação', moderada: 'moderada', forte: 'forte' };

  function _faixaComAgulha(divergencia, faixas) {
    if (!ehNum(divergencia)) return '';
    var f = ehObj(faixas) ? faixas : FAIXAS_PADRAO;
    var ordem = ['sem_tese', 'observacao', 'moderada', 'forte'];
    var bandas = [];
    for (var i = 0; i < ordem.length; i++) {
      var p = f[ordem[i]];
      if (!Array.isArray(p) || !ehNum(p[0]) || !ehNum(p[1])) { bandas = []; break; }
      bandas.push({ chave: ordem[i], de: p[0], ate: p[1] });
    }
    if (!bandas.length) {
      bandas = ordem.map(function (k) {
        return { chave: k, de: FAIXAS_PADRAO[k][0], ate: FAIXAS_PADRAO[k][1] };
      });
    }

    var v = limita(divergencia, 0, 100);
    var atual = null;
    var html = bandas.map(function (b, i) {
      var fim = i === bandas.length - 1 ? 100 : bandas[i + 1].de;
      var larg = limita(fim - b.de, 0, 100);
      if (v >= b.de && (i === bandas.length - 1 || v < fim)) atual = b;
      return { chave: b.chave, de: b.de, larg: larg };
    });

    var barras = html.map(function (b, i) {
      return '<span class="med-banda med-banda-' + (i + 1) + '" style="width:' + b.larg + '%"></span>';
    }).join('');

    var rots = html.map(function (b) {
      return '<span style="width:' + b.larg + '%">' + escapar(fmt(b.de, 0)) + ' ' +
        escapar(NOME_FAIXA[b.chave] || b.chave) + '</span>';
    }).join('');

    var nomeAtual = atual ? (NOME_FAIXA[atual.chave] || atual.chave) : 'fora da régua';

    return '<div class="med-faixa-agulha">' +
      '<div class="med-bandas" aria-hidden="true">' + barras +
        '<span class="med-agulha" style="left:' + v.toFixed(1) + '%"></span>' +
      '</div>' +
      '<div class="med-bandas-rot" aria-hidden="true">' + rots + '</div>' +
      '<div class="med-agulha-num">divergência <b class="med-num">' + escapar(fmt(divergencia, 0)) +
        '</b> de 100 · faixa <b>' + escapar(nomeAtual) + '</b> · cortes em ' +
        n(fmt(bandas[1].de, 0)) + ' / ' + n(fmt(bandas[2].de, 0)) + ' / ' + n(fmt(bandas[3].de, 0)) +
        ' · faixas provisórias</div>' +
    '</div>';
  }

  /* ================================================================ §6.4 · 3
     barrasQualidade(componentes)
     Quatro trilhos de 6px. A parte SEM DADO recebe hachura diagonal a 45° com
     borda âmbar tracejada e o valor ao lado em âmbar. A hachura é o único
     padrão do sistema e significa exatamente "não existe dado aqui".
     ================================================================ */

  var PARTES = [
    { chave: 'quantidade', nome: 'quantidade' },
    { chave: 'diversidade', nome: 'diversidade' },
    { chave: 'atualidade', nome: 'atualidade' },
    { chave: 'confiabilidade', nome: 'confiabil.' }
  ];

  function _barrasQualidade(componentes) {
    if (!ehObj(componentes)) return '';
    var c = ehObj(componentes.componentes) ? componentes.componentes : componentes;
    var achou = PARTES.some(function (p) { return Object.prototype.hasOwnProperty.call(c, p.chave); });
    if (!achou) return '';

    var linhas = PARTES.map(function (p) {
      var v = c[p.chave];
      if (!ehNum(v)) {
        // sem dado: hachura + âmbar. Não é zero, e o texto diz isso.
        return '<div class="med-qual">' +
          '<div class="med-qual-nm">' + escapar(p.nome) + '</div>' +
          '<div class="med-qual-trilho med-vazio" aria-hidden="true"></div>' +
          '<div class="med-qual-vv av">sem dado</div>' +
        '</div>';
      }
      var larg = limita(v, 0, 100);
      var baixo = larg < 40;
      return '<div class="med-qual">' +
        '<div class="med-qual-nm">' + escapar(p.nome) + '</div>' +
        '<div class="med-qual-trilho" aria-hidden="true">' +
          '<span class="med-qual-fl' + (baixo ? ' av' : '') + '" style="width:' + larg.toFixed(0) + '%"></span>' +
        '</div>' +
        '<div class="med-qual-vv' + (baixo ? ' av' : '') + ' med-num">' + escapar(fmt(v, 0)) + '</div>' +
      '</div>';
    }).join('');

    var semDado = PARTES.filter(function (p) { return !ehNum(c[p.chave]); }).map(function (p) { return p.nome; });
    var pe = semDado.length
      ? '<div class="med-legenda"><span>hachura = <b>não existe dado aqui</b>: ' +
          escapar(emFrase(semDado)) + ' fica fora da média, não entra como zero</span></div>'
      : '';

    return '<div class="med-qualidade">' + linhas + pe + '</div>';
  }

  /* ================================================================ §6.4 · 4
     reguaDias(dias, rotulo)
     Tiques de 2px, tique alto a cada 7 dias, barra final clara marcando a
     decisão, tudo âmbar quando faltam menos de 7 dias, aria-hidden="true".
     ================================================================ */

  var TETO_TIQUES = 56;

  function _reguaDias(dias, rotulo) {
    if (!ehNum(dias) || dias < 0) return '';
    var d = Math.round(dias);
    var urgente = d < 7;
    var mostra = Math.min(d, TETO_TIQUES);
    var cortada = d > TETO_TIQUES;

    var tiques = '';
    for (var i = 0; i < mostra; i++) {
      var cls = 'med-tique';
      if (i % 7 === 0) cls += ' alto';
      cls += urgente ? ' av' : ' on';
      tiques += '<i class="' + cls + '"></i>';
    }
    tiques += '<i class="fim' + (urgente ? ' av' : '') + '"></i>';

    return '<div class="med-dias">' +
      '<span class="med-dias-num med-num' + (urgente ? ' av' : '') + '">' +
        escapar(fmt(d, 0)) + ' d</span>' +
      '<span class="med-dias-regua" aria-hidden="true">' + tiques + '</span>' +
      (rotulo ? '<span class="med-dias-rot">' + escapar(rotulo) + '</span>' : '') +
      (cortada ? '<span class="med-dias-rot">régua cortada em ' + escapar(fmt(TETO_TIQUES, 0)) +
        ' tiques · o número ao lado é o prazo inteiro</span>' : '') +
    '</div>';
  }

  /* ================================================================ §6.6
     blocoAlarme(sentimento, eventos, eua, discursos)
     Cabeça com triângulo, "Estado degradado · N alarmes ativos" em .rot âmbar
     e a verificação à direita; a frase de escopo obrigatória; e uma linha por
     alarme com QUATRO colunas: identificador AL-NN com chip, assunto, medida
     (o número) e CONSEQUÊNCIA escrita em frase inteira.
     Um aviso sem consequência é decoração: nunca é gerado.
     ================================================================ */

  var TRIANGULO =
    '<svg width="13" height="12" viewBox="0 0 14 12" aria-hidden="true" focusable="false">' +
    '<path d="M7 .8 13.2 11.2H.8Z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>' +
    '<path d="M7 4.2v3.4" stroke="currentColor" stroke-width="1.4"/>' +
    '<circle cx="7" cy="9.3" r=".8" fill="currentColor"/></svg>';

  function alarmesDeFalaForaDoAr(discursos) {
    if (!ehObj(discursos) || !ehObj(discursos.status_fontes)) return [];
    var st = discursos.status_fontes;
    var txt = ehObj(discursos.status_fontes_texto) ? discursos.status_fontes_texto : {};
    var chaves = Object.keys(st);
    var fora = chaves.filter(function (k) { return String(st[k]).toLowerCase() !== 'ok'; });
    if (!fora.length) return [];

    var motivos = fora.map(function (k) {
      return k + ': ' + (txt[k] || st[k]);
    });

    return [{
      chip: 'FONTE',
      assuntoRot: 'dimensão de fala',
      assunto: fora.join(' · '),
      medida: escapar(fora.length + ' de ' + chaves.length) + ' fontes fora do ar · ligadas ' +
        n(chaves.length - fora.length) + ' de ' + n(chaves.length) + '.<br>' +
        escapar(motivos.join(' · ')),
      consequencia: 'as pernas <b>' + escapar(emFrase(fora)) + '</b> ficam sem fala coletada: ' +
        'a dimensão de texto delas nasce vazia e nenhum discurso dessas moedas aparece nesta edição — ' +
        'o que se lê ali é ausência de coleta, nunca silêncio do banco central.'
    }];
  }

  function alarmesDeDimensaoQueNaoVota(sentimento) {
    var regua = ehObj(sentimento.regua) ? sentimento.regua : null;
    if (!regua || !ehObj(regua.dimensoes_que_nao_votam)) return [];
    var chaves = Object.keys(regua.dimensoes_que_nao_votam);
    if (!chaves.length) return [];

    var total = Array.isArray(regua.dimensoes) ? regua.dimensoes.length : 4;
    var votam = Array.isArray(regua.dimensoes_que_votam) ? regua.dimensoes_que_votam.length
              : Math.max(0, total - chaves.length);
    var desde = '';
    chaves.forEach(function (k) {
      var d = regua.dimensoes_que_nao_votam[k];
      if (ehObj(d) && d.desde && !desde) desde = d.desde;
    });

    return [{
      chip: 'DIMENSÃO',
      assuntoRot: 'dimensões fora do voto',
      assunto: chaves.join(' · '),
      medida: n(votam) + ' de ' + n(total) + ' dimensões votam' +
        (desde ? ' · desde ' + n(dataCurta(desde)) : '') +
        (ehNum(regua.teto_por_moeda) ? ' · teto por moeda ' + n(fmt(regua.teto_por_moeda, 2)) : '') +
        (ehNum(regua.teto_por_par) ? ' · teto por par ' + n(fmt(regua.teto_por_par, 2)) : ''),
      consequencia: 'com ' + escapar(emFrase(chaves)) + ' fora do voto, o denominador encolheu: ' +
        'a mesma diferença econômica sai <b>maior</b> em divergência do que saía na escala velha, ' +
        'e as faixas provisórias foram desenhadas na escala velha — compare divergência de hoje com a de ontem com essa ressalva.'
    }];
  }

  function alarmesDeFrescor(sentimento) {
    var fr = ehObj(sentimento.frescor) ? sentimento.frescor : null;
    if (!fr || !Array.isArray(fr.fontes)) return [];
    var lim = ehObj(fr.limiares_provisorios) ? fr.limiares_provisorios : {};
    var atrasado = ehNum(lim.atrasado_min) ? lim.atrasado_min : 45;
    var fora = ehNum(lim.muito_atrasado_min) ? lim.muito_atrasado_min : 120;

    return fr.fontes.filter(function (f) {
      return ehObj(f) && ehNum(f.atraso_min) && f.atraso_min >= atrasado;
    }).map(function (f) {
      var estourou = f.atraso_min >= fora;
      var vota = f.vota === true;
      return {
        chip: estourou ? 'FORA DE TOLERÂNCIA' : 'ATRASO',
        assuntoRot: 'arquivo',
        assunto: f.arquivo || f.fonte || '',
        medida: 'atraso ' + n(f.atraso_texto || (fmt(f.atraso_min, 0) + ' min')) +
          ' · tolerância ' + n(fmt(estourou ? fora : atrasado, 0) + ' min') +
          (f.sincronizado_em ? ' · última sincronização ' + n(horaUTC(f.sincronizado_em)) : ''),
        consequencia: vota
          ? 'esta fonte <b>vota</b> (' + escapar(f.alimenta || 'dimensão que vota') + '): toda leitura que ' +
            'depende dela está lendo dado de ' + escapar(f.atraso_texto || fmt(f.atraso_min, 0) + ' min') +
            ' atrás, e uma divulgação ocorrida nesse intervalo ainda não entrou em nenhuma moeda.'
          : 'esta fonte <b>não vota</b> (' + escapar(f.alimenta || 'contexto') + '), então o score não muda; ' +
            'o que está velho é o contexto mostrado na tela — quem ler o bloco dela está lendo o mundo de ' +
            escapar(f.atraso_texto || fmt(f.atraso_min, 0) + ' min') + ' atrás.'
      };
    });
  }

  function alarmesDeCalendario(sentimento, eventos) {
    if (!ehObj(eventos)) return [];
    var fr = ehObj(sentimento.frescor) ? sentimento.frescor : {};
    var lim = ehObj(fr.limiares_provisorios) ? fr.limiares_provisorios : {};
    var atrasado = ehNum(lim.atrasado_min) ? lim.atrasado_min : 45;
    var fg = eventos.fonte_gerado_em;
    var idade = minutosEntre(fg, sentimento.gerado_em);
    if (!ehNum(idade) || idade < atrasado) return [];

    return [{
      chip: 'CALENDÁRIO',
      assuntoRot: 'fonte do calendário',
      assunto: String(eventos.fonte || 'calendário'),
      medida: 'fonte gerada em ' + n(horaUTC(fg)) + ' · ' + n(fmt(idade, 0) + ' min') +
        ' atrás · tolerância ' + n(fmt(atrasado, 0) + ' min') +
        (ehNum(eventos.total) ? ' · ' + n(fmt(eventos.total, 0)) + ' eventos' : ''),
      consequencia: 'o calendário na tela é o de ' + escapar(horaUTC(fg)) + ': qualquer divulgação ' +
        'ocorrida depois disso ainda não entrou na dimensão de dados de nenhuma moeda, e a leitura ' +
        'de hoje é a de antes dessa janela.'
    }];
  }

  function alarmesDeEua(eua) {
    if (!ehObj(eua) || !ehObj(eua.indicadores)) return [];
    var chaves = Object.keys(eua.indicadores);
    if (!chaves.length) return [];
    var sem = chaves.filter(function (k) {
      var i = eua.indicadores[k];
      return ehObj(i) && (i.sem_consenso === true || i.esperado === null || i.esperado === undefined);
    });
    if (!sem.length) return [];

    var siglas = sem.map(function (k) {
      var i = eua.indicadores[k];
      return (ehObj(i) && (i.sigla || i.nome)) || k;
    });

    return [{
      chip: 'SEM CONSENSO',
      assuntoRot: 'níveis oficiais (BLS)',
      assunto: siglas.slice(0, 4).join(' · ') + (siglas.length > 4 ? ' …' : ''),
      medida: n(sem.length) + ' de ' + n(chaves.length) + ' indicadores sem consenso casado' +
        (ehNum(eua.defasagem_referencia_meses)
          ? ' · defasagem de referência ' + n(fmt(eua.defasagem_referencia_meses, 0) +
            (eua.defasagem_referencia_meses === 1 ? ' mês' : ' meses')) : ''),
      consequencia: 'esses níveis não têm "esperado", então não viram surpresa e <b>não entram na ' +
        'dimensão de dados</b> — eles ficam só como ficha de nível. Quem procurar o CPI dentro da ' +
        'leitura direcional não vai encontrar, e isso é a régua funcionando, não falha de coleta.'
    }];
  }

  function alarmesDeDominancia(sentimento) {
    if (!ehObj(sentimento.moedas)) return [];
    var res = [];
    Object.keys(sentimento.moedas).forEach(function (k) {
      var m = sentimento.moedas[k];
      if (!ehObj(m) || !ehObj(m.dominancia)) return;
      var d = m.dominancia;
      if (!ehNum(d.share_pct) || d.share_pct <= 50) return;
      res.push({
        chip: 'DOMINÂNCIA',
        assuntoRot: 'perna concentrada',
        assunto: (m.moeda || k) + ' · ' + (d.item || 'item único'),
        medida: 'o maior item vale ' + n(fmt(d.share_pct, 0) + '%') + ' da dimensão de dados' +
          (ehNum(d.share_pct_antes_do_teto) ? ' · antes do teto ' + n(fmt(d.share_pct_antes_do_teto, 0) + '%') : '') +
          ' · corte de alerta ' + n('50%'),
        consequencia: 'a leitura de <b>' + escapar(m.moeda || k) + '</b> depende de uma divulgação só (' +
          escapar(d.item || 'item único') + '): se ela for revisada, a perna inteira muda de lado, ' +
          'e todo par que a contém muda junto. Não é leitura de conjunto, é leitura de um número.'
      });
    });
    return res;
  }

  function alarmesDeEvidencia(sentimento) {
    if (!ehObj(sentimento.moedas)) return [];
    var res = [];
    Object.keys(sentimento.moedas).forEach(function (k) {
      var m = sentimento.moedas[k];
      if (!ehObj(m) || !ehObj(m.qualidade_evidencia)) return;
      var q = m.qualidade_evidencia;
      if (!ehNum(q.nota) || q.nota >= 40) return;
      var sem = Array.isArray(q.partes_sem_dado) ? q.partes_sem_dado : [];
      res.push({
        chip: 'EVIDÊNCIA',
        assuntoRot: 'qualidade da evidência',
        assunto: (m.moeda || k) + ' · nota ' + fmt(q.nota, 0),
        medida: 'evidência ' + n(fmt(q.nota, 0) + '/100') + ' · corte ' + n('40') +
          (ehNum(q.partes_usadas) ? ' · ' + n(fmt(q.partes_usadas, 0)) + ' parte(s) com dado' : '') +
          (sem.length ? ' · sem dado em ' + escapar(sem.join(', ')) : ''),
        consequencia: 'a perna <b>' + escapar(m.moeda || k) + '</b> entra nos pares com base fina: ' +
          'todo par que a contém herda essa nota como elo fraco, e a divergência desses pares ' +
          'deve ser lida como ordem de grandeza, nunca como número calibrado.'
      });
    });
    return res;
  }

  function _blocoAlarme(sentimento, eventos, eua, discursos) {
    if (!ehObj(sentimento)) return '';

    var alarmes = []
      .concat(alarmesDeFalaForaDoAr(discursos))
      .concat(alarmesDeDimensaoQueNaoVota(sentimento))
      .concat(alarmesDeFrescor(sentimento))
      .concat(alarmesDeCalendario(sentimento, eventos))
      .concat(alarmesDeDominancia(sentimento))
      .concat(alarmesDeEvidencia(sentimento))
      .concat(alarmesDeEua(eua))
      // um aviso sem consequência é decoração: não entra
      .filter(function (a) { return ehObj(a) && a.consequencia && a.medida; });

    if (!alarmes.length) return '';

    var fr = ehObj(sentimento.frescor) ? sentimento.frescor : {};
    var verif = fr.ultima_sincronizacao_ok_brt || sentimento.gerado_em_brt || horaUTC(sentimento.gerado_em);

    var linhas = alarmes.map(function (a, i) {
      var id = 'AL-' + (i + 1 < 10 ? '0' : '') + (i + 1);
      return '<div class="med-alarme-linha">' +
        '<div><span class="med-alarme-id">' + escapar(id) + '</span>' +
          '<span class="med-chip med-chip-aviso">' + escapar(a.chip) + '</span></div>' +
        '<div><span class="rot med-alarme-k">' + escapar(a.assuntoRot) + '</span>' +
          '<span class="med-alarme-assunto">' + escapar(a.assunto) + '</span></div>' +
        '<div><span class="rot med-alarme-k">medida</span>' +
          '<span class="med-alarme-v">' + a.medida + '</span></div>' +
        '<div><span class="rot med-alarme-k">consequência</span>' +
          '<span class="med-alarme-v">' + a.consequencia + '</span></div>' +
      '</div>';
    }).join('');

    return '<section class="med-alarme" role="alert">' +
      '<div class="med-alarme-cab">' + TRIANGULO +
        '<span class="rot">Estado degradado · ' + escapar(fmt(alarmes.length, 0)) + ' alarmes ativos</span>' +
        (verif ? '<span class="med-alarme-verif">verificado ' + escapar(verif) + ' · frescor.py</span>' : '') +
      '</div>' +
      '<div class="med-alarme-escopo"><em>' + escapar(fmt(alarmes.length, 0)) +
        ' ressalvas ativas nesta edição — nenhuma invalida a tabela, todas mudam o peso.</em></div>' +
      linhas +
    '</section>';
  }

  /* ================================================================ §6.7
     notas(lista) -> { marcador(n), bloco() }
     Marcador colado ao termo; o bloco numerado resolve no fim da página.
     Numeração corrida, começando em 1.
     ================================================================ */

  function _notas(lista) {
    var itens = Array.isArray(lista) ? lista.filter(function (x) {
      return typeof x === 'string' ? x.length > 0 : (ehObj(x) && (x.texto || x.nota));
    }) : [];

    function marcador(num) {
      if (!ehNum(num)) return '';
      var i = Math.round(num);
      if (i < 1 || i > itens.length) return '';
      return '<sup class="med-nota-marca"><a href="#med-nota-' + i + '">' + i + '</a></sup>';
    }

    function bloco() {
      if (!itens.length) return '';
      var lis = itens.map(function (it, i) {
        var termo = ehObj(it) ? (it.termo || it.titulo || '') : '';
        var texto = typeof it === 'string' ? it : (it.texto || it.nota || '');
        return '<li class="med-notas-item" id="med-nota-' + (i + 1) + '">' +
          '<span class="med-notas-n med-num">' + (i + 1) + '</span>' +
          '<span class="med-notas-txt">' +
            (termo ? '<span class="med-notas-termo">' + escapar(termo) + '</span>' : '') +
            escapar(texto) +
          '</span></li>';
      }).join('');
      return '<div class="med-notas">' +
        '<div class="rot med-notas-cab">Notas</div>' +
        '<ol class="med-notas-lista">' + lis + '</ol>' +
      '</div>';
    }

    return {
      marcador: seguro('notas.marcador', marcador),
      bloco: seguro('notas.bloco', bloco),
      total: itens.length
    };
  }

  /* ------------------------------------------------------------- fachada */

  var API = {
    VERSAO: VERSAO,
    escapar: escapar,
    faixaEstado: seguro('faixaEstado', _faixaEstado),
    escalaDivergente: seguro('escalaDivergente', _escalaDivergente),
    faixaComAgulha: seguro('faixaComAgulha', _faixaComAgulha),
    barrasQualidade: seguro('barrasQualidade', _barrasQualidade),
    reguaDias: seguro('reguaDias', _reguaDias),
    blocoAlarme: seguro('blocoAlarme', _blocoAlarme),
    notas: function (lista) {
      try {
        return _notas(lista);
      } catch (e) {
        return {
          marcador: function () { return ''; },
          bloco: function () { return ''; },
          total: 0
        };
      }
    }
  };

  raiz.HCI_MEDIDORES = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;

})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
