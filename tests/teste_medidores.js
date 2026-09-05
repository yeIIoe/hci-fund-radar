/* ============================================================================
   tests/teste_medidores.js — teste do módulo ui_medidores.js

   Roda em node puro, com DOM falso. Carrega o módulo, chama as SETE funções
   com os JSONs REAIS lidos por fs e confirma:
     1. nenhuma função lança;
     2. nenhuma devolve "undefined", "NaN" ou "null" dentro do HTML;
     3. blocoAlarme produz CONSEQUÊNCIA em toda linha;
     4. dado faltando devolve string vazia (não explode, não inventa);
     5. nada de cor em estilo inline;
     6. entrada hostil sai escapada.

   Uso:  node tests/teste_medidores.js
   ============================================================================ */

'use strict';

const fs = require('fs');
const path = require('path');

/* ------------------------------------------------------------ DOM falso */

const documentoFalso = {
  createElement: () => ({ style: {}, setAttribute() {}, appendChild() {} }),
  querySelector: () => null,
  querySelectorAll: () => [],
  body: { appendChild() {} }
};

const janelaFalsa = {
  document: documentoFalso,
  console: { warn: (...a) => avisos.push(a.join(' ')) },
  navigator: { language: 'pt-BR' },
  location: { href: 'file:///teste' }
};

const avisos = [];
global.window = janelaFalsa;
global.document = documentoFalso;

/* ------------------------------------------------------- carrega o módulo */

const RAIZ = path.resolve(__dirname, '..');
require(path.join(RAIZ, 'ui_medidores.js'));

const M = global.window.HCI_MEDIDORES;

/* --------------------------------------------------------- dados reais */

function lerJson(nome) {
  return JSON.parse(fs.readFileSync(path.join(RAIZ, 'data', nome), 'utf8'));
}

const sentimento = lerJson('sentimento.json');
const eventos = lerJson('macro_eventos.json');
const eua = lerJson('eua_leitura.json');
const discursos = lerJson('bc_discursos.json');
const geo = lerJson('geopolitica.json');

/* ------------------------------------------------------------ asserções */

let passou = 0;
const falhas = [];

function ok(condicao, titulo, detalhe) {
  if (condicao) {
    passou++;
    console.log('  ok    ' + titulo);
  } else {
    falhas.push(titulo + (detalhe ? ' — ' + detalhe : ''));
    console.log('  FALHA ' + titulo + (detalhe ? ' — ' + detalhe : ''));
  }
}

const LIXO = /\bundefined\b|\bNaN\b|>null<|\[object Object\]/;

function htmlLimpo(html, titulo) {
  ok(typeof html === 'string', titulo + ': devolve string', 'veio ' + typeof html);
  ok(html.length > 0, titulo + ': não veio vazio com dado real');
  const achado = html.match(LIXO);
  ok(!achado, titulo + ': sem undefined/NaN/null no HTML', achado ? 'achou "' + achado[0] + '"' : '');
  const corInline = html.match(/style="[^"]*(?:color|background|var\(--)[^"]*"/);
  ok(!corInline, titulo + ': nenhum estilo inline com cor', corInline ? corInline[0] : '');
  ok(!/<script/i.test(html), titulo + ': nenhum <script> no HTML');
}

function naoLanca(titulo, fn) {
  try {
    const r = fn();
    ok(true, titulo + ': não lançou');
    return r;
  } catch (e) {
    ok(false, titulo + ': não lançou', e && e.message);
    return null;
  }
}

/* ================================================================ testes */

console.log('\n== ui_medidores v' + M.VERSAO + ' · sete funções contra os JSONs reais ==\n');

console.log('[0] fachada');
['faixaEstado', 'escalaDivergente', 'faixaComAgulha', 'barrasQualidade',
 'reguaDias', 'blocoAlarme', 'notas'].forEach((f) => {
  ok(typeof M[f] === 'function', 'expõe ' + f + '()');
});

/* --- 1 · faixaEstado (§6.1) --- */
console.log('\n[1] faixaEstado(sentimento, {eventos, eua, discursos})');
const faixa = naoLanca('faixaEstado', () =>
  M.faixaEstado(sentimento, { eventos, eua, discursos }));
htmlLimpo(faixa, 'faixaEstado');
ok(/med-led-ok|med-led-av|med-led-off/.test(faixa), 'faixaEstado: tem LED de estado');
ok(/med-led-mudo/.test(faixa), 'faixaEstado: tem LED cinza informativo (defasagem de referência)');
ok((faixa.match(/med-faixa-seg/g) || []).length >= 5, 'faixaEstado: >= 5 segmentos',
   'achou ' + (faixa.match(/med-faixa-seg/g) || []).length);
ok(/class="rot"/.test(faixa) || /med-faixa-chave rot/.test(faixa), 'faixaEstado: chave em .rot');
ok(faixa.includes(M.escapar('defasagem de referência')), 'faixaEstado: traz a defasagem de referência');
ok(M.faixaEstado(sentimento) !== '', 'faixaEstado: funciona só com sentimento (extras opcional)');

/* --- 2 · escalaDivergente (§6.4 item 1) --- */
console.log('\n[2] escalaDivergente(moedas)');
const escala = naoLanca('escalaDivergente', () => M.escalaDivergente(sentimento.moedas));
htmlLimpo(escala, 'escalaDivergente');
const nLinhas = (escala.match(/med-escala-linha/g) || []).length;
ok(nLinhas === Object.keys(sentimento.moedas).length,
   'escalaDivergente: uma linha por moeda', nLinhas + ' linhas');
ok(/med-barra-oca/.test(escala), 'escalaDivergente: barra VAZADA para MANTÉM');
const temDeclarada = Object.values(sentimento.moedas)
  .some((m) => ['SOBE', 'CORTA'].includes(String(m.direcao).toUpperCase()));
if (temDeclarada) {
  const solidas = (escala.match(/med-barra med-barra-(?:pos|neg)"/g) || []).length;
  ok(solidas > 0, 'escalaDivergente: barra SÓLIDA para direção declarada', solidas + ' sólidas');
} else {
  ok(true, 'escalaDivergente: nenhuma direção declarada hoje — todas vazadas, correto');
}
ok(/med-legenda/.test(escala), 'escalaDivergente: legenda obrigatória presente');
ok(/<sup>\d\/\d<\/sup>/.test(escala), 'escalaDivergente: sobrescrito n/4');
// ordem: hawkish -> dovish
const ordem = [...escala.matchAll(/med-escala-cod">([A-Z]{3})/g)].map((m) => m[1]);
const scoresOrdem = ordem.map((c) => sentimento.moedas[c].score);
ok(scoresOrdem.every((v, i) => i === 0 || scoresOrdem[i - 1] >= v),
   'escalaDivergente: ordenado da mais hawkish para a mais dovish', ordem.join(' > '));
ok(!/med-trilho"[^>]*aria-hidden="true"/.test(escala) === false ||
   /med-trilho" aria-hidden="true"/.test(escala), 'escalaDivergente: trilho é aria-hidden');

/* --- 3 · faixaComAgulha (§6.4 item 2) --- */
console.log('\n[3] faixaComAgulha(divergencia, faixas)');
const par = sentimento.pares[0];
const agulha = naoLanca('faixaComAgulha', () =>
  M.faixaComAgulha(par.divergencia, par.faixas_provisorias));
htmlLimpo(agulha, 'faixaComAgulha');
ok((agulha.match(/med-banda med-banda-/g) || []).length === 4, 'faixaComAgulha: quatro bandas');
ok(/med-agulha/.test(agulha), 'faixaComAgulha: agulha presente');
['15', '25', '40'].forEach((c) => {
  ok(agulha.includes('>' + c + ' ') || agulha.includes('>' + c + '<'),
     'faixaComAgulha: corte ' + c + ' marcado');
});
ok(agulha.includes('divergência'), 'faixaComAgulha: o número em texto ao lado do gráfico');
// todos os 28 pares
let agulhaOk = true;
sentimento.pares.forEach((p) => {
  const h = M.faixaComAgulha(p.divergencia, p.faixas_provisorias);
  if (!h || LIXO.test(h)) agulhaOk = false;
});
ok(agulhaOk, 'faixaComAgulha: os 28 pares saem limpos');

/* --- 4 · barrasQualidade (§6.4 item 3) --- */
console.log('\n[4] barrasQualidade(componentes)');
const qual = naoLanca('barrasQualidade', () =>
  M.barrasQualidade(sentimento.moedas.USD.qualidade_evidencia.componentes));
htmlLimpo(qual, 'barrasQualidade');
ok((qual.match(/med-qual"/g) || []).length === 4, 'barrasQualidade: quatro trilhos');
const temNulo = Object.values(sentimento.moedas.USD.qualidade_evidencia.componentes)
  .some((v) => typeof v !== 'number');
ok(temNulo ? /med-vazio/.test(qual) : true, 'barrasQualidade: hachura na parte SEM DADO');
ok(temNulo ? /med-qual-vv av">sem dado/.test(qual) : true,
   'barrasQualidade: valor da parte sem dado em âmbar, escrito');
let qualOk = true;
Object.keys(sentimento.moedas).forEach((k) => {
  const h = M.barrasQualidade(sentimento.moedas[k].qualidade_evidencia);
  if (!h || LIXO.test(h)) qualOk = false;
});
ok(qualOk, 'barrasQualidade: as 8 moedas saem limpas (aceita o objeto inteiro)');

/* --- 5 · reguaDias (§6.4 item 4) --- */
console.log('\n[5] reguaDias(dias, rotulo)');
const regua = naoLanca('reguaDias', () =>
  M.reguaDias(sentimento.moedas.USD.dias_ate, 'Fed · ' + sentimento.moedas.USD.proxima));
htmlLimpo(regua, 'reguaDias');
ok(/aria-hidden="true"/.test(regua), 'reguaDias: régua com aria-hidden');
ok(/med-dias-num/.test(regua), 'reguaDias: o número em texto ao lado');
ok(/class="fim/.test(regua), 'reguaDias: barra final marcando a decisão');
const curta = M.reguaDias(5, 'BCE · 2026-09-10');
ok(/med-dias-num med-num av/.test(curta) && /\bav\b/.test(curta),
   'reguaDias: tudo âmbar quando faltam menos de 7 dias');
const longa = M.reguaDias(53, 'BoC');
ok((longa.match(/alto/g) || []).length >= 7, 'reguaDias: tique alto a cada 7 dias');
let reguaOk = true;
Object.keys(sentimento.moedas).forEach((k) => {
  const h = M.reguaDias(sentimento.moedas[k].dias_ate, sentimento.moedas[k].banco);
  if (!h || LIXO.test(h)) reguaOk = false;
});
ok(reguaOk, 'reguaDias: as 8 moedas saem limpas');

/* --- 6 · blocoAlarme (§6.6) --- */
console.log('\n[6] blocoAlarme(sentimento, eventos, eua, discursos)');
const alarme = naoLanca('blocoAlarme', () =>
  M.blocoAlarme(sentimento, eventos, eua, discursos));
htmlLimpo(alarme, 'blocoAlarme');
const linhas = alarme.split('<div class="med-alarme-linha">').slice(1);
ok(linhas.length > 0, 'blocoAlarme: gerou alarmes dos dados reais', linhas.length + ' linhas');
let todasComConsequencia = true;
let semTexto = [];
linhas.forEach((linha, i) => {
  const m = linha.match(/>consequência<\/span><span class="med-alarme-v">([\s\S]*?)<\/span><\/div>/);
  const texto = m ? m[1].replace(/<[^>]+>/g, '').trim() : '';
  // frase inteira: pelo menos 40 caracteres e termina em ponto
  if (!texto || texto.length < 40 || !/[.!]$/.test(texto)) {
    todasComConsequencia = false;
    semTexto.push('AL-' + (i + 1) + ' («' + texto.slice(0, 40) + '»)');
  }
});
ok(todasComConsequencia, 'blocoAlarme: TODA linha tem consequência em frase inteira',
   semTexto.join(' '));
ok((alarme.match(/med-alarme-id/g) || []).length === linhas.length,
   'blocoAlarme: todo alarme tem identificador AL-NN');
ok((alarme.match(/class="med-chip med-chip-\w+"/g) || []).length === linhas.length,
   'blocoAlarme: todo alarme tem chip',
   (alarme.match(/class="med-chip med-chip-\w+"/g) || []).length + ' chips para ' + linhas.length + ' linhas');
ok(/Estado degradado · \d+ alarmes ativos/.test(alarme), 'blocoAlarme: cabeça com a contagem');
ok(alarme.includes('ressalvas ativas nesta edição'), 'blocoAlarme: frase de escopo obrigatória');
ok(/verificado /.test(alarme), 'blocoAlarme: verificação à direita');
// os alarmes que os dados de hoje exigem
ok(/RBA|RBNZ|SNB|AUD|NZD|CHF/.test(alarme), 'blocoAlarme: pegou a fonte fora do ar (403/404)');
const domAlta = Object.entries(sentimento.moedas)
  .filter(([, m]) => m.dominancia && m.dominancia.share_pct > 50).map(([k]) => k);
ok(domAlta.every((k) => alarme.includes('>' + k + ' · ') || alarme.includes(k)),
   'blocoAlarme: pegou dominância acima de 50%', domAlta.join(',') || 'nenhuma hoje');
const evidBaixa = Object.entries(sentimento.moedas)
  .filter(([, m]) => m.qualidade_evidencia && m.qualidade_evidencia.nota < 40).map(([k]) => k);
ok(evidBaixa.every((k) => alarme.includes(k)),
   'blocoAlarme: pegou evidência abaixo de 40', evidBaixa.join(',') || 'nenhuma hoje');
const atrasadas = (sentimento.frescor.fontes || [])
  .filter((f) => f.atraso_min >= (sentimento.frescor.limiares_provisorios.atrasado_min || 45));
ok(atrasadas.every((f) => alarme.includes(M.escapar(f.arquivo || f.fonte))),
   'blocoAlarme: pegou dado atrasado / fora de tolerância',
   atrasadas.map((f) => f.arquivo).join(',') || 'nenhuma hoje');
ok(/dimensões fora do voto|DIMENSÃO/.test(alarme), 'blocoAlarme: pegou dimensão que não vota');

/* --- 7 · notas (§6.7) --- */
console.log('\n[7] notas(lista)');
const lista = [
  'As faixas 0-14 / 15-24 / 25-39 / 40+ são provisórias: escolhidas por ordem de grandeza, ainda sem calibração histórica.',
  { termo: 'defasagem de entrega', texto: 'medida por evento no calendário; para a API do BLS não é medida, porque exige chave registrada.' },
  { termo: 'geopolítica', texto: 'saiu do voto em 05/set/2026 e ficou como contexto declarado — atraso de ' + geo.gerado_em + '.' }
];
const nt = naoLanca('notas', () => M.notas(lista));
ok(nt && typeof nt.marcador === 'function' && typeof nt.bloco === 'function',
   'notas: devolve {marcador, bloco}');
const marc = nt.marcador(2);
const blocoNotas = nt.bloco();
ok(/^<sup class="med-nota-marca">/.test(marc), 'notas: marcador em <sup>');
htmlLimpo(blocoNotas, 'notas.bloco');
ok((blocoNotas.match(/med-notas-item/g) || []).length === 3, 'notas: uma linha por nota');
ok(blocoNotas.includes('id="med-nota-1"') && blocoNotas.includes('id="med-nota-3"'),
   'notas: numeração corrida começando em 1');
ok(nt.marcador(99) === '' && nt.marcador(0) === '' && nt.marcador('x') === '',
   'notas: marcador fora da lista devolve vazio');

/* --- 8 · degradação: faltou dado, devolve string vazia --- */
console.log('\n[8] degradação — faltou dado, devolve "" e não lança');
const vazios = [
  ['faixaEstado(null)', () => M.faixaEstado(null)],
  ['faixaEstado({})', () => M.faixaEstado({})],
  ['escalaDivergente(null)', () => M.escalaDivergente(null)],
  ['escalaDivergente({})', () => M.escalaDivergente({})],
  ['escalaDivergente([{}])', () => M.escalaDivergente([{}])],
  ['faixaComAgulha(undefined)', () => M.faixaComAgulha(undefined)],
  ['faixaComAgulha("x")', () => M.faixaComAgulha('x')],
  ['barrasQualidade(null)', () => M.barrasQualidade(null)],
  ['barrasQualidade({})', () => M.barrasQualidade({})],
  ['reguaDias(null)', () => M.reguaDias(null)],
  ['reguaDias(NaN)', () => M.reguaDias(NaN)],
  ['blocoAlarme(null)', () => M.blocoAlarme(null)],
  ['blocoAlarme({} sem alarme)', () => M.blocoAlarme({ moedas: {}, frescor: {}, regua: {} })],
  ['notas([]).bloco()', () => M.notas([]).bloco()],
  ['notas(null).bloco()', () => M.notas(null).bloco()]
];
vazios.forEach(([titulo, fn]) => {
  try {
    const r = fn();
    ok(r === '', titulo + ' devolve ""', 'devolveu ' + JSON.stringify(String(r).slice(0, 60)));
  } catch (e) {
    ok(false, titulo + ' não lança', e && e.message);
  }
});
// faixaComAgulha sem faixas cai no padrão 15/25/40
const semFaixas = M.faixaComAgulha(45);
ok(semFaixas !== '' && !LIXO.test(semFaixas), 'faixaComAgulha sem faixas usa a régua padrão');

/* --- 9 · escapamento de entrada hostil --- */
console.log('\n[9] escapamento');
const hostil = '<img src=x onerror="alert(1)">&"\'';
const sujo = JSON.parse(JSON.stringify(sentimento.moedas));
sujo.USD.moeda = hostil;
sujo.USD.dominancia = { share_pct: 99, item: hostil };
const escalaSuja = M.escalaDivergente(sujo);
ok(!escalaSuja.includes('<img'), 'escalaDivergente: código do dado sai escapado');
ok(escalaSuja.includes('&lt;img'), 'escalaDivergente: escapa < como &lt;');
const notasSujas = M.notas([hostil]).bloco();
ok(!notasSujas.includes('<img') && notasSujas.includes('&lt;img'), 'notas: escapa o texto da nota');
const alarmeSujo = M.blocoAlarme({ moedas: sujo, frescor: sentimento.frescor, regua: sentimento.regua },
  eventos, eua, discursos);
ok(!alarmeSujo.includes('<img'), 'blocoAlarme: escapa o assunto do alarme');
ok(M.reguaDias(11, hostil).includes('&lt;img'), 'reguaDias: escapa o rótulo');

/* --- 10 · sem avisos silenciosos --- */
console.log('\n[10] console');
ok(avisos.length === 0, 'nenhum aviso engolido por try/catch nos caminhos com dado real',
   avisos.slice(0, 3).join(' | '));

/* ---------------------------------------------------------------- saída */

console.log('\n' + '='.repeat(70));
console.log('passou: ' + passou + ' · falhou: ' + falhas.length);
if (falhas.length) {
  console.log('\nFALHAS:');
  falhas.forEach((f) => console.log('  - ' + f));
}
console.log('='.repeat(70) + '\n');
process.exit(falhas.length ? 1 : 0);
