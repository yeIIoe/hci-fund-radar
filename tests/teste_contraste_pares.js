/* ============================================================================
   tests/teste_contraste_pares.js — CONFERENTE DE CONTRASTE POR PAR REAL

   O irmao deste arquivo (teste_contraste.js) cruza TODA tinta com TODA
   superficie. Este aqui faz a pergunta menor e mais dura: quais pares de
   (cor de texto x superficie) o estilo_hci.css realmente ESCREVE, e qual e a
   razao de contraste de cada um.

   Como acha o par:
     1. le o CSS, tira comentario, quebra em regras (inclusive dentro de @media);
     2. resolve var(--x) contra o :root;
     3. toda regra que pinta background/background-color vira SUPERFICIE, com o
        seletor e a LINHA em que foi declarada;
     4. superficie translucida e COMPOSTA sobre as tres bases opacas plausiveis
        (--fundo, --painel, --painel-alto) e vale a mais clara das tres, que e o
        pior caso;
     5. em cada superficie assentam: a cor da propria regra, as tres tintas e,
        quando a superficie e um preenchimento semantico, as quatro cores da
        regua — porque um chip verde pode cair dentro de um bloco ambar;
     6. --tinta-3 e avaliada NO CONTEXTO: se a regra da superficie redefine
        `--tinta-3` (a correcao da §1.3-bis), vale o valor redefinido.

   Formula WCAG 2.x, sRGB:
     L = 0,2126 R + 0,7152 G + 0,0722 B, canal c em [0,1]
       c <= 0,03928 -> c/12,92 ; senao ((c+0,055)/1,055)^2,4
     razao = (L_claro + 0,05) / (L_escuro + 0,05)

   Piso 4,5:1. Rodar:  node tests/teste_contraste_pares.js
   ========================================================================== */
'use strict';

var fs = require('fs');
var path = require('path');

var ARQ = path.join(__dirname, '..', 'estilo_hci.css');
var CSS_BRUTO = fs.readFileSync(ARQ, 'utf8');
var PISO = 4.5;

/* ------------------------------------------------------------ cor -> rgb */
function hex2rgb(h) {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
  return { r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16),
           b: parseInt(h.slice(4, 6), 16), a: 1 };
}
function parseCor(txt) {
  txt = String(txt || '').trim();
  if (txt.charAt(0) === '#') return hex2rgb(txt);
  var m = txt.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)/i);
  if (m) return { r: +m[1], g: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] };
  return null;
}
function compor(frente, base) {
  if (frente.a >= 1) return { r: frente.r, g: frente.g, b: frente.b, a: 1 };
  return {
    r: frente.a * frente.r + (1 - frente.a) * base.r,
    g: frente.a * frente.g + (1 - frente.a) * base.g,
    b: frente.a * frente.b + (1 - frente.a) * base.b,
    a: 1
  };
}
function canal(v) { var c = v / 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
function lum(c) { return 0.2126 * canal(c.r) + 0.7152 * canal(c.g) + 0.0722 * canal(c.b); }
function contraste(a, b) {
  var la = lum(a), lb = lum(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
function hexOf(c) {
  function h(v) { var s = Math.round(v).toString(16).toUpperCase(); return s.length < 2 ? '0' + s : s; }
  return '#' + h(c.r) + h(c.g) + h(c.b);
}

/* ------------------------------------------- CSS sem comentario, com linha */
var LINHAS = CSS_BRUTO.split('\n');
function linhaDe(indice) { return CSS_BRUTO.slice(0, indice).split('\n').length; }
// troca cada comentario por espacos do mesmo tamanho: some o texto, ficam as linhas
var CSS = CSS_BRUTO.replace(/\/\*[\s\S]*?\*\//g, function (m) {
  return m.replace(/[^\n]/g, ' ');
});

/* ------------------------------------------------------ tokens do :root */
var TOKEN = {};
var raiz = CSS.match(/:root\s*\{([\s\S]*?)\n\}/);
if (raiz) {
  raiz[1].replace(/(--[\w-]+)\s*:\s*([^;]+);/g, function (_, k, v) { TOKEN[k] = v.trim(); return ''; });
}
function resolve(v, escopo, prof) {
  prof = prof || 0;
  if (prof > 8) return String(v).trim();
  var m = String(v).match(/var\(\s*(--[\w-]+)\s*(?:,([^)]*))?\)/);
  if (!m) return String(v).trim();
  var val = (escopo && escopo[m[1]] !== undefined) ? escopo[m[1]]
          : (TOKEN[m[1]] !== undefined ? TOKEN[m[1]] : (m[2] || ''));
  return resolve(val, escopo, prof + 1);
}

/* --------------------------------------------------------- quebra em regras */
var REGRA = /([^{}]+)\{([^{}]*)\}/g;
var regras = [];
var mm;
while ((mm = REGRA.exec(CSS)) !== null) {
  var sel = mm[1].trim().replace(/\s+/g, ' ');
  if (!sel || sel.charAt(0) === '@') continue;
  var corpo = mm[2];
  var d = {};
  corpo.replace(/([-\w]+)\s*:\s*([^;]+);?/g, function (_, k, v) { d[k.trim()] = v.trim(); return ''; });
  regras.push({ sel: sel, decl: d, linha: linhaDe(mm.index) });
}

/* ------------------------------------------------- superficies declaradas */
var BASES = [
  { nome: '--fundo', rgb: parseCor(resolve('var(--fundo)')) },
  { nome: '--painel', rgb: parseCor(resolve('var(--painel)')) },
  { nome: '--painel-alto (ZEBRA)', rgb: parseCor(resolve('var(--painel-alto)')) }
];

/* PECA GRAFICA NAO E SUPERFICIE DE TEXTO. LED de 6px, barra de forca, agulha de
   2px, tique da regua de dias, banda do medidor, fio de zero, <hr>: sao formas,
   nunca assentam letra, e a §6.1 exige que todo LED venha com a palavra escrita
   AO LADO. Entram na conta so as superficies em que texto pode cair. */
var NOME_GRAFICO = /[\s.-]led|barra|agulha|tique|\.med-banda|trilho|\.amostra|scrim|\.fim|dias-regua|regua-dias|-fl\b|\.zero\b|\.cheia|\.oca\b/;
function ehGrafico(r) {
  var temTexto = ['font-size', 'font-family', 'color', 'line-height', 'letter-spacing',
                  'padding', 'text-transform'].some(function (k) { return r.decl[k] !== undefined; });
  if (temTexto) return false;
  var selNu = r.sel.split(',')[0].trim();
  if (/^html (hr|\.mac-sep)/.test(selNu) || NOME_GRAFICO.test(r.sel)) return true;
  // "colado por fio de 1px": a cor so aparece na fresta entre as celulas (§6.5)
  if (r.decl.gap === '1px' && /grid|flex/.test(r.decl.display || '')) return true;
  var geo = ['width', 'height', 'min-height', 'max-height'].some(function (k) {
    var v = r.decl[k];
    if (!v) return false;
    if (v === '100%') return true;
    var m = String(v).match(/^([\d.]+)px$/);
    return !!m && parseFloat(m[1]) <= 24;
  });
  return geo || r.decl.inset !== undefined;
}

var superficies = [];
regras.forEach(function (r) {
  var bruto = r.decl['background-color'] || r.decl.background;
  if (!bruto) return;
  bruto = bruto.replace(/!important/g, '').trim();
  if (/^(none|transparent|inherit|initial|0)$/.test(bruto)) return;
  if (ehGrafico(r)) return;
  var primeiro = bruto.split(/\s+(?![^(]*\))/)[0];
  var c = parseCor(resolve(primeiro));
  if (!c) return;
  // a regra sobe a tinta terciaria? (correcao da §1.3-bis)
  var escopo = {};
  Object.keys(r.decl).forEach(function (k) { if (k.indexOf('--') === 0) escopo[k] = r.decl[k]; });
  // uma regra irma pode subir a tinta para o MESMO seletor
  regras.forEach(function (o) {
    if (o.sel === r.sel) {
      Object.keys(o.decl).forEach(function (k) { if (k.indexOf('--') === 0) escopo[k] = o.decl[k]; });
    }
  });
  // seletor que sobe a tinta e ancestral-ou-igual deste? compara compostos
  regras.forEach(function (o) {
    if (o.decl['--tinta-3'] === undefined) return;
    o.sel.split(',').forEach(function (os) {
      r.sel.split(',').forEach(function (rs) {
        if (ancestralOuIgual(os.trim(), rs.trim())) escopo['--tinta-3'] = o.decl['--tinta-3'];
      });
    });
  });

  if (c.a >= 1) {
    superficies.push({ sel: r.sel, linha: r.linha, valor: primeiro, rgb: c,
                       base: '(opaca)', escopo: escopo });
  } else {
    // a mais CLARA das tres composicoes e o pior caso
    var pior = null;
    BASES.forEach(function (b) {
      var comp = compor(c, b.rgb);
      if (!pior || lum(comp) > lum(pior.rgb)) pior = { rgb: comp, base: b.nome };
    });
    superficies.push({ sel: r.sel, linha: r.linha, valor: primeiro, rgb: pior.rgb,
                       base: 'composta sobre ' + pior.base, escopo: escopo, alfa: true });
  }
});

/* --------------------- ancestral-ou-igual por compostos (aproximacao honesta) */
function compostos(sel) {
  return sel.replace(/\s*[>+~]\s*/g, ' ').split(' ').filter(Boolean).map(function (c) {
    var classes = (c.match(/\.[-\w]+/g) || []).sort().join('');
    var tag = (c.match(/^[a-zA-Z][-\w]*/) || [''])[0];
    return { classes: classes, tag: tag, cru: c };
  });
}
function casa(a, b) {
  if (a.classes && b.classes.indexOf(a.classes) === -1) {
    // toda classe de a precisa estar em b
    var ca = a.cru.match(/\.[-\w]+/g) || [];
    for (var i = 0; i < ca.length; i++) if (b.cru.indexOf(ca[i]) === -1) return false;
  }
  if (a.tag && b.tag && a.tag !== b.tag) return false;
  return true;
}
function ancestralOuIgual(pai, filho) {
  var A = compostos(pai), B = compostos(filho);
  if (!A.length) return false;
  var i = 0;
  for (var j = 0; j < B.length && i < A.length; j++) if (casa(A[i], B[j])) i++;
  return i === A.length;
}

/* ------------------------------------------------------------ tintas */
var TINTAS = [
  { nome: '--tinta',   token: 'var(--tinta)' },
  { nome: '--tinta-2', token: 'var(--tinta-2)' },
  { nome: '--tinta-3', token: 'var(--tinta-3)' },
  { nome: '--alta',    token: 'var(--alta)' },
  { nome: '--corte',   token: 'var(--corte)' },
  { nome: '--aviso',   token: 'var(--aviso)' },
  { nome: '--marca',   token: 'var(--marca)' }
];

/* que tintas podem assentar nesta superficie */
function tintasDe(s) {
  var lista = [];
  TINTAS.forEach(function (t) {
    var rgb = parseCor(resolve(t.token, s.escopo));
    var rotulo = t.nome;
    if (t.nome === '--tinta-3' && s.escopo && s.escopo['--tinta-3']) {
      rotulo = '--tinta-3 (subida p/ ' + s.escopo['--tinta-3'] + ')';
    }
    lista.push({ nome: rotulo, rgb: rgb });
  });
  return lista;
}

/* --------------------------------------------------------------- relatorio */
function f2(x) { return x.toFixed(2).replace('.', ','); }
function pad(s, n) { s = String(s); while (s.length < n) s += ' '; return s; }
function padE(s, n) { s = String(s); while (s.length < n) s = ' ' + s; return s; }

// superficies distintas por cor efetiva (varias regras pintam a mesma coisa)
var porCor = {};
superficies.forEach(function (s) {
  var k = hexOf(s.rgb) + '|' + (s.escopo && s.escopo['--tinta-3'] ? 'subida' : 'normal');
  if (!porCor[k]) porCor[k] = { rgb: s.rgb, escopo: s.escopo, exemplos: [] };
  if (porCor[k].exemplos.length < 3) {
    porCor[k].exemplos.push(s.sel.split(',')[0].trim() + ' (l.' + s.linha + ')');
  }
});

console.log('CONTRASTE POR PAR REAL — estilo_hci.css · WCAG 2.x · piso ' + f2(PISO) + ':1');
console.log('regras lidas: ' + regras.length + ' · superficies pintadas: ' + superficies.length +
            ' · cores efetivas distintas: ' + Object.keys(porCor).length);
console.log('');

var cab = pad('superficie efetiva', 20) + pad('quem pinta (1o seletor + linha)', 46);
TINTAS.forEach(function (t) { cab += padE(t.nome.replace('--', ''), 9); });
console.log(cab);
console.log(new Array(cab.length + 1).join('-'));

var reprovados = [];
Object.keys(porCor).sort(function (a, b) { return lum(porCor[b].rgb) - lum(porCor[a].rgb); })
  .forEach(function (k) {
    var s = porCor[k];
    var linha = pad(hexOf(s.rgb) + (s.escopo && s.escopo['--tinta-3'] ? ' ^' : ''), 20) +
                pad(s.exemplos[0], 46);
    tintasDe(s).forEach(function (t) {
      var r = contraste(t.rgb, s.rgb);
      linha += padE(f2(r) + (r < PISO ? '*' : ''), 9);
      if (r < PISO) reprovados.push({ tinta: t.nome, hex: hexOf(s.rgb), r: r, onde: s.exemplos.join(' · ') });
    });
    console.log(linha);
  });

console.log('');
console.log('^ = superficie em que a folha SOBE --tinta-3 para --tinta-2 (§1.3-bis)');
console.log('* = abaixo de ' + f2(PISO) + ':1');
console.log('');
if (!reprovados.length) {
  console.log('NENHUM PAR ABAIXO DE ' + f2(PISO) + ':1.');
} else {
  console.log('REPROVADOS (' + reprovados.length + '):');
  reprovados.sort(function (a, b) { return a.r - b.r; }).forEach(function (x) {
    console.log('  ' + x.tinta + ' sobre ' + x.hex + ' = ' + f2(x.r) + ':1  →  ' + x.onde);
  });
}

var pior = null;
Object.keys(porCor).forEach(function (k) {
  var s = porCor[k];
  tintasDe(s).forEach(function (t) {
    var r = contraste(t.rgb, s.rgb);
    if (r >= PISO && (!pior || r < pior.r)) pior = { r: r, tinta: t.nome, hex: hexOf(s.rgb), onde: s.exemplos[0] };
  });
});
console.log('');
console.log('Pior caso aprovado: ' + pior.tinta + ' sobre ' + pior.hex + ' = ' + f2(pior.r) +
            ':1  (' + pior.onde + ')');

process.exitCode = reprovados.length ? 1 : 0;
