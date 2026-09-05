/* ============================================================================
   teste_contraste.js — CONFERENTE DE CONTRASTE do estilo_hci.css

   Nao confia em numero escrito em comentario: LE o CSS, resolve os var(),
   COMPOE as superficies translucidas sobre as opacas e calcula a razao de
   contraste WCAG 2.x pela formula da luminancia relativa.

     L = 0,2126 R + 0,7152 G + 0,0722 B, com cada canal c em [0,1]:
       c <= 0,03928  ->  c / 12,92
       c >  0,03928  -> ((c + 0,055) / 1,055) ^ 2,4
     razao = (L_claro + 0,05) / (L_escuro + 0,05)

   Piso 4,5:1. A superficie que CONTA e a zebra --painel-alto #0F241F.
   Rodar:  node tests/teste_contraste.js
   ========================================================================== */
'use strict';
var fs = require('fs');
var path = require('path');

var CSS = fs.readFileSync(path.join(__dirname, '..', 'estilo_hci.css'), 'utf8');
var PISO = 4.5;

/* ------------------------------------------------------------ cor -> rgb */
function hex2rgb(h) {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
  return { r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4, 6), 16), a: 1 };
}
function parseCor(txt) {
  txt = String(txt).trim();
  if (txt.charAt(0) === '#') return hex2rgb(txt);
  var m = txt.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)/i);
  if (m) return { r: +m[1], g: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] };
  return null;
}
/* composicao "source-over": cor translucida SOBRE uma base opaca */
function compor(frente, base) {
  if (frente.a >= 1) return { r: frente.r, g: frente.g, b: frente.b, a: 1 };
  return {
    r: frente.a * frente.r + (1 - frente.a) * base.r,
    g: frente.a * frente.g + (1 - frente.a) * base.g,
    b: frente.a * frente.b + (1 - frente.a) * base.b,
    a: 1
  };
}
/* ------------------------------------------------- luminancia e contraste */
function canal(v) {
  var c = v / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}
function lum(c) { return 0.2126 * canal(c.r) + 0.7152 * canal(c.g) + 0.0722 * canal(c.b); }
function contraste(a, b) {
  var la = lum(a), lb = lum(b);
  var claro = Math.max(la, lb), escuro = Math.min(la, lb);
  return (claro + 0.05) / (escuro + 0.05);
}

/* --------------------------------------------- tokens lidos do proprio CSS */
var TOKEN = {};
var raiz = CSS.match(/:root\s*\{([\s\S]*?)\n\}/);
if (raiz) {
  raiz[1].replace(/(--[\w-]+)\s*:\s*([^;]+);/g, function (_, k, v) { TOKEN[k] = v.trim(); return ''; });
}
function resolve(v, prof) {
  prof = prof || 0;
  if (prof > 8) return v;
  var m = String(v).match(/var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)/);
  if (!m) return String(v).trim();
  return resolve(TOKEN[m[1]] !== undefined ? TOKEN[m[1]] : '', prof + 1);
}
function cor(nome) {
  var c = parseCor(resolve(nome));
  if (!c) throw new Error('cor nao resolvida: ' + nome);
  return c;
}

/* ------------------------- superficies opacas declaradas na §1.1 do sistema */
var OPACAS = [
  ['--fundo',        'fundo da pagina'],
  ['--fundo-band',   'faixa de estado / rodape'],
  ['--painel',       'corpo do cartao'],
  ['--painel-alto',  'ZEBRA da tabela'],
  ['--painel-fundo', 'cabeca de cartao/tabela']
].map(function (p) { return { nome: p[0], onde: p[1], rgb: cor('var(' + p[0] + ')') }; });

/* ---- superficies TRANSLUCIDAS: compostas sobre cada base opaca plausivel --- */
var BASES = { '--painel-alto': 'zebra', '--painel': 'painel', '--fundo': 'fundo' };
var TRANSLUCIDAS = [];
function addTrans(rotulo, valor, bases) {
  var f = parseCor(resolve(valor));
  (bases || Object.keys(BASES)).forEach(function (b) {
    TRANSLUCIDAS.push({
      nome: rotulo + ' sobre ' + BASES[b],
      rgb: compor(f, cor('var(' + b + ')')),
      onde: rotulo
    });
  });
}
addTrans('--alta-fraca',  'var(--alta-fraca)');
addTrans('--corte-fraca', 'var(--corte-fraca)');
addTrans('--aviso-fraca', 'var(--aviso-fraca)');
addTrans('--marca-fraca', 'var(--marca-fraca)');

/* cabeca do alarme: --aviso-fraca EM CIMA de --aviso-fraca (pior empilhamento) */
(function () {
  var f = parseCor(resolve('var(--aviso-fraca)'));
  ['--fundo', '--painel'].forEach(function (b) {
    var um = compor(f, cor('var(' + b + ')'));
    TRANSLUCIDAS.push({
      nome: '--aviso-fraca DUPLA (cab.alarme) s/ ' + BASES[b],
      rgb: compor(f, um),
      onde: 'alarme-cab'
    });
  });
})();

/* bandas do medidor de agulha (contrato .med-banda-*), sobre --fundo-band */
[['rgba(159,182,175,.04)', 'banda 1 (agulha)'],
 ['rgba(79,208,142,.05)',  'banda 2 (agulha)'],
 ['rgba(79,208,142,.08)',  'banda 3 (agulha)'],
 ['rgba(79,208,142,.12)',  'banda 4 (agulha)']].forEach(function (p) {
  TRANSLUCIDAS.push({
    nome: p[1] + ' s/ --fundo-band',
    rgb: compor(parseCor(p[0]), cor('var(--fundo-band)')),
    onde: 'medidor de agulha'
  });
});

var SUPERFICIES = OPACAS.concat(TRANSLUCIDAS);

/* --------------------------------------------------- as tintas e as quatro */
var TINTAS = [
  ['--tinta',   'numero heroi, titulo'],
  ['--tinta-2', 'texto corrido, prosa'],
  ['--tinta-3', 'rotulo, unidade, nota'],
  ['--alta',    'alta de juro'],
  ['--corte',   'corte de juro, risco'],
  ['--aviso',   'degradacao do sistema'],
  ['--marca',   'marca, selecao, agulha']
].map(function (p) { return { nome: p[0], uso: p[1], rgb: cor('var(' + p[0] + ')') }; });

/* -------------------------------------------------------- tabela calculada */
function f2(x) { return x.toFixed(2).replace('.', ','); }
function pad(s, n) { s = String(s); while (s.length < n) s += ' '; return s; }
function padE(s, n) { s = String(s); while (s.length < n) s = ' ' + s; return s; }
function hexOf(c) {
  function h(v) { var s = Math.round(v).toString(16).toUpperCase(); return s.length < 2 ? '0' + s : s; }
  return '#' + h(c.r) + h(c.g) + h(c.b);
}

var reprovados = [];
var larg = 2;
SUPERFICIES.forEach(function (s) { if (s.nome.length + 2 > larg) larg = s.nome.length + 2; });

console.log('CONTRASTE CALCULADO — WCAG 2.x, sRGB, piso ' + f2(PISO) + ':1');
console.log('(alfa composto sobre a base opaca; a superficie que CONTA e a ZEBRA)');
console.log('');
var cab = pad('superficie', larg) + pad('hex efetivo', 13);
TINTAS.forEach(function (t) { cab += padE(t.nome.replace('--', ''), 9); });
console.log(cab);
console.log(new Array(cab.length + 1).join('-'));

SUPERFICIES.forEach(function (s) {
  var linha = pad(s.nome, larg) + pad(hexOf(s.rgb), 13);
  TINTAS.forEach(function (t) {
    var r = contraste(t.rgb, s.rgb);
    linha += padE(f2(r) + (r < PISO ? '*' : ''), 9);
    if (r < PISO) reprovados.push({ tinta: t.nome, sup: s.nome, hex: hexOf(s.rgb), r: r });
  });
  console.log(linha);
});

console.log('');
console.log('(* = abaixo de ' + f2(PISO) + ':1)');
if (!reprovados.length) {
  console.log('');
  console.log('NENHUM PAR ABAIXO DE 4,5:1.');
} else {
  console.log('');
  console.log('REPROVADOS (' + reprovados.length + '):');
  reprovados.sort(function (a, b) { return a.r - b.r; }).forEach(function (x) {
    console.log('  ' + x.tinta + ' sobre ' + x.sup + ' (' + x.hex + ') = ' + f2(x.r) + ':1');
  });
}
var pior = null;
SUPERFICIES.forEach(function (s) {
  TINTAS.forEach(function (t) {
    var r = contraste(t.rgb, s.rgb);
    if (r >= PISO && (!pior || r < pior.r)) pior = { r: r, tinta: t.nome, sup: s.nome, hex: hexOf(s.rgb) };
  });
});
console.log('');
console.log('Pior caso APROVADO do sistema: ' + pior.tinta + ' sobre ' + pior.sup +
            ' (' + pior.hex + ') = ' + f2(pior.r) + ':1');

process.exitCode = reprovados.length ? 1 : 0;
