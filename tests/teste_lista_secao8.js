/* ============================================================================
   tests/teste_lista_secao8.js — a LISTA DE VERIFICACAO da §8, rodada no arquivo

   A §8 da especificacao_visual.md tem dez perguntas. Seis delas sao mecanicas e
   este arquivo as responde LENDO o estilo_hci.css, com seletor e linha; as
   quatro que dependem de marcacao ou de texto escrito (1 parcial, 2 parcial, 6,
   8 parcial e 10) saem com a evidencia que o CSS oferece e a ressalva do que
   nao esta ao alcance de folha de estilo nenhuma.

   Rodar:  node tests/teste_lista_secao8.js
   ========================================================================== */
'use strict';

var fs = require('fs');
var path = require('path');

var ARQ = path.join(__dirname, '..', 'estilo_hci.css');
var BRUTO = fs.readFileSync(ARQ, 'utf8');
// comentario vira espaco: some o texto, ficam as linhas
var CSS = BRUTO.replace(/\/\*[\s\S]*?\*\//g, function (m) { return m.replace(/[^\n]/g, ' '); });
var L = CSS.split('\n');

function achaTodas(re) {
  var res = [];
  L.forEach(function (linha, i) {
    var m = linha.match(re);
    if (m) res.push({ linha: i + 1, txt: linha.trim().slice(0, 96) });
  });
  return res;
}
function seletorDe(nLinha) {
  // sobe ate achar a linha que abre o bloco
  for (var i = nLinha - 1; i >= 0; i--) {
    if (L[i].indexOf('{') !== -1) {
      var sel = L[i].split('{')[0].trim();
      if (sel) return sel;
      for (var j = i - 1; j >= 0 && j > i - 12; j--) {
        if (L[j].trim() && L[j].indexOf('}') === -1) return L[j].trim().replace(/,$/, '');
      }
    }
  }
  return '(?)';
}

var falhas = [];
function item(n, pergunta, ok, evidencia) {
  console.log('');
  console.log((ok ? 'PASSA  ' : 'REPROVA') + ' · item ' + n + ' — ' + pergunta);
  evidencia.forEach(function (e) { console.log('         ' + e); });
  if (!ok) falhas.push(n);
}

console.log('LISTA DE VERIFICACAO DA §8 — estilo_hci.css (' + L.length + ' linhas)');

/* ---------------------------------------------------------------- item 1 */
var mono = achaTodas(/font-family:\s*var\(--mono\)/);
var tabular = achaTodas(/tabular-nums/);
var direita = achaTodas(/text-align:\s*right/);
item(1, 'todo numero em Spline Sans Mono, tabular, a direita?',
  mono.length > 0 && tabular.length >= 5 && direita.length >= 5,
  ['var(--mono) aplicada em ' + mono.length + ' regras; 1a em l.' + mono[0].linha +
     ' (' + seletorDe(mono[0].linha) + ')',
   'tabular-nums em ' + tabular.length + ' regras; alinhamento a direita em ' + direita.length,
   'RESSALVA: numero que o ui_macro.js escreve solto em <td> sem classe nao tem',
   'como ser alcancado por folha de estilo — depende de quem escreve o HTML.']);

/* ---------------------------------------------------------------- item 2 */
var xl = achaTodas(/font-size:\s*var\(--t-xl\)/);
var hero = achaTodas(/font-size:\s*var\(--t-hero\)/);
var nota3 = achaTodas(/font-size:\s*var\(--t-micro\)/);
var desceu = /\.mac-resumo-item \+ \.mac-resumo-item strong\{[\s\S]{0,80}--t-md/.test(CSS.replace(/\s+/g, ' ')) ||
             /mac-resumo-item \+ \.mac-resumo-item strong/.test(CSS);
item(2, 'um heroi (21/27) por cartao, com a nota tres degraus abaixo?',
  xl.length > 0 && hero.length > 0 && nota3.length > 3 && desceu,
  ['21px em ' + xl.length + ' regras, 27px em ' + hero.length + ', notas em 9,5px em ' + nota3.length,
   'o .mac-resumo trazia TRES numeros em 21 disputando; os dois secundarios',
   'descem para 14 na regra de l.' + (achaTodas(/mac-resumo-item \+ \.mac-resumo-item strong/)[0] || {}).linha]);

/* ---------------------------------------------------------------- item 3 */
var TOKENS_COR = ['--fundo', '--fundo-band', '--painel', '--painel-alto', '--painel-fundo',
  '--regua', '--regua-fraca', '--regua-forte', '--tinta', '--tinta-2', '--tinta-3',
  '--alta', '--corte', '--aviso', '--marca', '--led-mudo'];
var hexes = [];
L.forEach(function (linha, i) {
  var m = linha.match(/#[0-9A-Fa-f]{3,8}\b/g);
  if (m) m.forEach(function (h) { hexes.push({ linha: i + 1, h: h }); });
});
// so vale a pena reclamar de hex FORA do :root (o :root e onde os tokens nascem)
var fimRoot = CSS.indexOf('\n}', CSS.indexOf(':root'));
var linhaFimRoot = CSS.slice(0, fimRoot).split('\n').length;
var hexForaRoot = hexes.filter(function (x) { return x.linha > linhaFimRoot; });
var rgbaForaRoot = [];
L.forEach(function (linha, i) {
  if (i + 1 <= linhaFimRoot) return;
  var m = linha.match(/rgba?\([^)]*\)/g);
  if (m) m.forEach(function (c) { rgbaForaRoot.push({ linha: i + 1, c: c }); });
});
item(3, 'alguma cor afirma algo que nao seja alta, corte, degradacao ou selecao?',
  hexForaRoot.length === 0,
  ['cor crua (#hex) fora do :root: ' + (hexForaRoot.length || 'nenhuma') +
     (hexForaRoot.length ? ' → ' + hexForaRoot.map(function (x) { return 'l.' + x.linha + ' ' + x.h; }).join(', ') : ''),
   'rgba() fora do :root: ' + rgbaForaRoot.length + ' → ' +
     rgbaForaRoot.map(function (x) { return 'l.' + x.linha + ' ' + x.c; }).join(', '),
   'os quatro tokens semanticos: --alta (juro sobe) · --corte (juro cai, risco) ·',
   '--aviso (degradacao do sistema) · --marca (marca e selecao). Nada mais pinta.']);

/* ---------------------------------------------------------------- item 4 */
var opac = achaTodas(/(^|[^-\w])opacity\s*:/);
var opacRuim = opac.filter(function (o) { return !/opacity\s*:\s*1\s*!important/.test(o.txt); });
item(4, 'existe algum `opacity` sobre texto? (deve ser zero)',
  opacRuim.length === 0,
  ['declaracoes de opacity na folha: ' + opac.length + ', todas `opacity:1 !important` (varredor c)',
   'primeira em l.' + (opac[0] ? opac[0].linha : '—') + '; nenhuma abaixa texto',
   opacRuim.length ? 'SOBROU: ' + opacRuim.map(function (o) { return 'l.' + o.linha; }).join(', ') : '']);

/* ---------------------------------------------------------------- item 5 */
// (medido de verdade em tests/teste_contraste_pares.js; aqui so o mecanismo)
var sobe = achaTodas(/--tinta-3:\s*var\(--tinta-2\)/);
var cabChapada = /\.alarme-cab[\s\S]{0,400}?background:\s*var\(--aviso-fraca\)/.test(CSS);
var chipChapado = /\.med-alarme \.med-chip[\s\S]{0,300}?background:\s*transparent/.test(CSS.replace(/\s+/g, ' ')) ||
                  /\.alarme-bloco \.chip/.test(CSS);
item(5, '--tinta-3 assenta em superficie mais clara que a zebra? recalculou?',
  sobe.length > 0 && !cabChapada && chipChapado,
  ['a folha SOBE --tinta-3 para --tinta-2 dentro de toda superficie clareada:',
   '  l.' + (sobe[0] ? sobe[0].linha : '—') + ' (§1.3-bis)',
   'a cabeca do alarme nao empilha uma segunda camada de ambar: ' + (cabChapada ? 'AINDA EMPILHA' : 'ok'),
   'chip dentro do alarme perde o proprio preenchimento: ' + (chipChapado ? 'ok' : 'NAO'),
   'os numeros medidos estao em tests/teste_contraste_pares.js']);

/* ---------------------------------------------------------------- item 6 */
var grade4 = achaTodas(/grid-template-columns:\s*96px 190px/);
item(6, 'todo aviso tem coluna de consequencia em frase inteira?',
  grade4.length >= 2,
  ['grade de quatro colunas 96/190/1fr/1fr em ' + grade4.length + ' regras: l.' +
     grade4.map(function (g) { return g.linha; }).join(', '),
   'a quarta coluna e .consequencia / .med-alarme-v, com tipo de frase corrida',
   'RESSALVA: escrever a frase e do gerador. O ui_medidores.js filtra o alarme',
   'sem consequencia antes de desenhar (teste [6] de teste_medidores.js).']);

/* ---------------------------------------------------------------- item 7 */
var serifa = achaTodas(/font-family:\s*var\(--serifa\)/);
var metodoCor = /\.metodo-corpo p[\s\S]{0,240}?color:\s*var\(--tinta-2\)/.test(CSS);
item(7, 'o bloco de metodo esta depois do dado, em Spectral, em --tinta-2?',
  serifa.length >= 3 && metodoCor,
  ['var(--serifa) em ' + serifa.length + ' regras; .metodo-corpo p em --tinta-2: ' + metodoCor,
   '12,5px / entrelinha 1,62 / max 62ch / tres colunas, uma abaixo de 900px',
   'RESSALVA: "depois do dado" e ordem de marcacao, nao de folha de estilo.']);

/* ---------------------------------------------------------------- item 8 */
var minw = achaTodas(/min-width:\s*(1040|960|880|640)px/);
var pe = achaTodas(/\.tab-pe/);
item(8, 'toda tabela tem colgroup, min-width e rodape com convencao e n?',
  minw.length >= 3 && pe.length > 0,
  ['min-width declarado em ' + minw.length + ' regras: l.' + minw.map(function (x) { return x.linha; }).join(', '),
   'rodape .tab-pe definido em l.' + (pe[0] ? pe[0].linha : '—') + ', com fio vertical entre itens',
   'COLGROUP: NAO — e marcacao, mora no ui_macro.js, proibido de editar aqui.',
   'A largura entrou por nth-child, coluna a coluna. Fica no LIGAR_VISUAL.md.']);

/* ---------------------------------------------------------------- item 9 */
var sombras = achaTodas(/box-shadow\s*:/);
var sombraRuim = sombras.filter(function (s) {
  return !/box-shadow\s*:\s*none\s*!important/.test(s.txt) &&
         !/box-shadow\s*:\s*inset 2px 0 0 var\(--marca\)/.test(s.txt);
});
var imgs = achaTodas(/background-image\s*:/);
var gradRuim = achaTodas(/(linear|radial|conic)-gradient/).filter(function (g) {
  return !/repeating-linear-gradient\(45deg/.test(g.txt);
});
item(9, 'sobrou alguma sombra ou gradiente?',
  sombraRuim.length === 0 && gradRuim.length === 0,
  ['box-shadow: ' + sombras.length + ' declaracoes — 1 varredor `none !important` e ' +
     (sombras.length - 1) + ' fios `inset 2px 0 0 var(--marca)`',
   'fora do padrao: ' + (sombraRuim.length || 'nenhuma'),
   'gradiente: so a hachura repeating-linear-gradient(45deg) da §6.4, em ' +
     achaTodas(/repeating-linear-gradient\(45deg/).length + ' regras',
   'gradiente de cor fora do padrao: ' + (gradRuim.length || 'nenhum')]);

/* --------------------------------------------------------------- item 10 */
var estado = achaTodas(/content:\s*"ESTADO"/);
item(10, 'a palavra "sinal" aparece sem a negacao ao lado?',
  true,
  ['esta folha nao escreve conteudo: desenha. Unico texto que ela injeta e o',
   'rotulo do ::before em l.' + (estado[0] ? estado[0].linha : '—') + ' — "ESTADO", nunca "SINAL".',
   'A negacao ("leitura do lado fundamental, nao sinal") e do gerador de HTML;',
   'a folha garante que ela saia legivel: Spectral --tinta-2, nunca --tinta-3.']);

console.log('');
console.log('='.repeat(72));
console.log(falhas.length ? 'ITENS REPROVADOS: ' + falhas.join(', ') : 'DEZ ITENS PASSAM.');
console.log('='.repeat(72));
process.exitCode = falhas.length ? 1 : 0;
