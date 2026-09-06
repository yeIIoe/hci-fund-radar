# LIGAR_VISUAL.md — como ligar `estilo_hci.css` e `ui_medidores.js` no painel

Documento do **conferente** para o **orquestrador**. As duas peças novas estão prontas,
conferidas e testadas, mas **desligadas**: hoje elas não são carregadas por ninguém.
Este arquivo diz exatamente o que acrescentar, onde, em que ordem, e o que **não** fazer.

Quem escreveu as duas peças não tocou em `index.html`, `ui_macro.js`, `ui_lang.js` nem em
nenhum `.py` — a ligação é sua.

**Aviso de concorrência.** O `ui_macro.js` estava sendo editado por outra força-tarefa
enquanto isto era escrito. Por isso **nenhum ponto de inserção abaixo é dado por número de
linha**: cada um é dado por *nome da função* mais um *trecho-âncora curto*. Procure a
âncora dentro da função nomeada. Se a âncora tiver mudado, o parágrafo diz o que ela faz,
para você reconhecê-la mesmo reescrita.

---

## 0. As duas peças, em uma frase cada

| Arquivo | O que é | O que ele NÃO faz |
|---|---|---|
| `estilo_hci.css` | a folha inteira do sistema visual da direção C: paleta, tipografia, tabela, cartão, chip, alarme, método, e a **§M** com o desenho dos medidores | não escreve conteúdo nenhum; só desenha |
| `ui_medidores.js` | sete funções que **devolvem string de HTML** (`window.HCI_MEDIDORES`) | não toca no DOM, não busca dado, não lança exceção: se faltar dado devolve `""` |

As sete funções:

```
faixaEstado(sentimento [, {eventos, eua, discursos}])   → faixa sticky do topo (§6.1)
escalaDivergente(moedas)                                → ranking das 8 moedas (§6.4-1)
faixaComAgulha(divergencia [, faixas])                  → faixa 15/25/40 com agulha (§6.4-2)
barrasQualidade(qualidade_evidencia)                    → quatro barras + hachura (§6.4-3)
reguaDias(dias [, rotulo])                              → régua de tiques até o evento (§6.4-4)
blocoAlarme(sentimento, eventos, eua, discursos)        → alarme de 4 colunas (§6.6)
notas(lista) → { marcador(n), bloco(), total }          → notas de rodapé numeradas (§6.7)
```

---

## 1. `index.html` — duas tags, e só

### 1.1 A folha de estilo

No `<head>`, **depois** de `styles.css` e de `theme.css`, como **última** folha:

```html
  <link rel="stylesheet" href="styles.css?v=20260905-rev1">
  <link rel="stylesheet" href="theme.css?v=20260905-rev1">
  <link rel="stylesheet" href="estilo_hci.css?v=20260906-rev1">   <!-- ACRESCENTAR -->
```

**A ordem é obrigatória.** A folha nova ganha das outras duas por vir por último *e* por
prefixar `html` em cada seletor. Se ela entrar antes, o `theme.css` volta a pintar por cima
e a página fica meio de cada sistema, que é pior que qualquer um dos dois inteiro.

Não precisa de `<link>` de fonte: o `@import` na primeira linha do próprio
`estilo_hci.css` já traz as três famílias (Archivo, Spline Sans Mono e Spectral) com
`display=swap`. Se quiser um pouco de velocidade, pode acrescentar antes dos `<link>`:

```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

Isso é opcional e não muda nada visualmente.

### 1.2 O módulo dos medidores

No fim do `<body>`, junto dos outros scripts, **antes** do `ui_macro.js`:

```html
  <script src="ui_nav.js?v=20260905-rev1"></script>
  <script src="ui_medidores.js?v=20260906-rev1"></script>   <!-- ACRESCENTAR AQUI -->
  <script src="ui_macro.js?v=20260905-rev1"></script>
```

Antes, não depois: o `ui_macro.js` começa a desenhar assim que os dados chegam, e o
`window.HCI_MEDIDORES` precisa existir nesse instante. O módulo não tem dependência, não
faz `fetch`, não registra evento: custa um `<script>` e nada mais.

---

## 2. `ui_macro.js` — primeiro o ajudante, depois os enxertos

### 2.1 O ajudante `med()` (faça este antes de todos os outros)

**Função:** nenhuma — é uma constante no escopo do IIFE.
**Âncora:** a linha que define `const esc = (s) => ...`, perto do topo do arquivo, logo
depois do mapa `FLAG`.

Acrescente **logo abaixo** dela:

```js
  // Ponte para o ui_medidores.js (§6.1, §6.4, §6.6, §6.7 da especificação visual).
  // Se o módulo não carregou, ou se uma peça falhar, devolve "" e o painel continua
  // desenhando o que já desenhava. Nada aqui pode derrubar a tela.
  const med = (nome, ...args) => {
    try {
      const API = window.HCI_MEDIDORES;
      return (API && typeof API[nome] === "function") ? API[nome](...args) : "";
    } catch (e) {
      console.warn("[macro] medidor " + nome + " falhou e foi contido:", e && e.message);
      return "";
    }
  };
```

Todo enxerto abaixo usa `med(...)` e **sempre com um `|| <o que já existia>` do lado**,
menos quando o texto disser o contrário. É essa a garantia de que ligar não pode piorar.

---

### 2.2 Faixa de estado no topo (§6.1)

**Função:** `aplica()`
**Âncora:** a primeira linha do corpo, `if (!M.pronto) return;`

Acrescente **logo depois** dela:

```js
    // FAIXA DE ESTADO (§6.1): primeira filha do <body>, e UMA VEZ SÓ.
    // aplica() roda a cada 900 ms — sem a guarda, a faixa entraria 66 vezes por minuto.
    if (!document.querySelector(".med-faixa")) {
      const faixa = med("faixaEstado", M.sent,
                        { eventos: M.eventos, eua: M.eua, discursos: M.discursos });
      if (faixa) document.body.insertAdjacentHTML("afterbegin", faixa);
    }
```

Três detalhes que não são estilo, são funcionamento:

1. **`afterbegin` no `<body>`, não dentro do `<main>`.** A faixa é `position:sticky` e
   precisa ser filha direta do `<body>`. O `estilo_hci.css` tem a regra
   `html body:has(> .med-faixa) .site-header{ top:30px }`, que empurra o cabeçalho para
   baixo da faixa — as duas barras são grudadas no topo e, sem isso, uma cobre a outra.
   Se a faixa entrar dentro do `<main>`, essa regra não casa e as duas se sobrepõem.
2. **A guarda do `querySelector` é obrigatória**, pelo motivo dito no comentário.
3. Se `M.sent` ainda não chegou, `faixaEstado` devolve `""` e nada é inserido; na próxima
   passada de `aplica()` ele tenta de novo. É esse o comportamento desejado.

---

### 2.3 Bloco de alarme no lugar da tarja (§6.6)

**Funções:** `painelBancos()` **e** `matrizPares()`
**Âncora (nas duas):** a interpolação `${tarjaAtraso()}` que fica **sozinha numa linha**,
logo depois do `</div>` do `.section-title`.

Troque, **nas duas funções**, exatamente esta linha:

```js
      ${tarjaAtraso()}
```

por:

```js
      ${med("blocoAlarme", M.sent, M.eventos, M.eua, M.discursos) || tarjaAtraso()}
```

O que muda: a tarja de três linhas vira o bloco de quatro colunas
(identificador · assunto · **medida** · **consequência**), com a frase de escopo
obrigatória em cima. Quando não há alarme nenhum, `blocoAlarme` devolve `""` e o
`|| tarjaAtraso()` mantém exatamente o comportamento de hoje.

**Não troque** o `${tarjaAtraso()}` que está dentro de `resumoPar()` e de
`detalheInstr()`: aquele fica dentro de um cartão pequeno, e o bloco de quatro colunas
não cabe ali. Ali a tarja continua.

O `blocoAlarme` já cobre, sozinho, os alarmes que os dados de hoje exigem: fonte de fala
fora do ar, dimensão que não vota, arquivo atrasado, calendário velho, dominância acima de
50%, evidência abaixo de 40 e nível do BLS sem consenso. Cada linha só é gerada se tiver
**consequência escrita** — um aviso sem consequência é filtrado antes de desenhar.

---

### 2.4 Régua de dias na tabela dos bancos (§6.4-4)

**Função:** `painelBancos()`, dentro do `.map()` que monta cada `<tr>`
**Âncora:** o `<td>` da coluna **Próxima decisão** — é o que contém
`<small class="mac-hora-local">`.

Acrescente a régua **imediatamente antes do `</td>`** desse `<td>`:

```js
          <small class="mac-hora-local">${b.hora_local ? "horário local " + esc(hora) : esc(hora)}</small>
          ${dias === null || dias === undefined ? "" : med("reguaDias", dias)}</td>
```

A variável `dias` já existe nesse escopo (`const dias = b.proxima ? diasAte(b.proxima) : null`).

**Opcional, e recomendado:** a régua já escreve o número (`"11 d"`), então o
`· em 11 dias` do `<small class="muted">` ao lado passa a ser repetição. Se quiser tirar,
troque nesse mesmo `<td>`

```js
          <small class="muted"> · ${esc(quando)}${b.proxima && emBrt ? " · " + esc(dataBr(b.proxima)) : ""}</small>
```

por

```js
          <small class="muted">${b.proxima && emBrt ? " · " + esc(dataBr(b.proxima)) : ""}</small>
```

Não é obrigatório; se ficar, ninguém quebra — só fica dito duas vezes.

A régua fica **inteira âmbar** quando faltam menos de 7 dias, tem tique alto a cada 7 dias
e barra clara marcando a decisão. Ela é `aria-hidden="true"`: é reforço do número, nunca a
única fonte.

---

### 2.5 Escala das 8 moedas (§6.4-1)

**Função:** `matrizPares()`
**Âncora:** a linha que abre o placar,
`<div class="mac-placar${S ? " mac-placar-3" : ""}${clsAtraso()}">`

Acrescente **uma linha antes** dela:

```js
      ${med("escalaDivergente", M.sent && M.sent.moedas)}
```

Sai o ranking das oito moedas, da mais hawkish para a mais dovish, com **barra sólida**
para direção declarada (SOBE/CORTA), **barra vazada** para MANTÉM, sobrescrito `n/4` com
as dimensões que votam e a legenda obrigatória embaixo.

Observação honesta: o `.mac-placar` logo abaixo diz a mesma coisa em palavras ("Inclinado
à alta / Em manutenção / Inclinado ao corte"). Ligue os dois primeiro, olhe, e então
decida se o placar sai. **Não tire o placar no mesmo commit da ligação** — se algo der
errado, você não vai saber qual das duas mudanças foi.

---

### 2.6 Faixa com agulha e barras de qualidade no cartão do par (§6.4-2 e §6.4-3)

**Função:** `resumoPar(d)`

**(a)** Junto das constantes do começo da função (âncora: `const qual = d.qual;`),
acrescente:

```js
    // o ELO FRACO das duas pernas: é a nota dele que vale para o par (§6.4-3)
    const eloFraco = [d.b, d.q]
      .map((m) => (sentDe(m) || {}).qualidade_evidencia)
      .filter((Q) => Q && Q.nota != null)
      .sort((a, b) => a.nota - b.nota)[0] || null;
```

**(b)** Âncora: a barra da divergência, dentro do primeiro `.mac-resumo-item`:

```js
          <div class="mac-barra-forca"><i style="width:${Math.max(2, Math.min(100, div))}%"></i></div>
```

troque por:

```js
          ${med("faixaComAgulha", div, fx) ||
            `<div class="mac-barra-forca"><i style="width:${Math.max(2, Math.min(100, div))}%"></i></div>`}
```

A variável `fx` já existe nesse escopo (as faixas provisórias). Se ela vier num formato que
o módulo não reconhece, ele cai sozinho na régua padrão 15/25/40 — não é preciso tratar.

**(c)** Âncora: a barra da qualidade, dentro do segundo `.mac-resumo-item`:

```js
          ${qual === null || qual === undefined ? "" :
            `<div class="mac-barra-forca q"><i style="width:${Math.max(2, Math.min(100, qual))}%"></i></div>`}
```

troque por:

```js
          ${med("barrasQualidade", eloFraco) ||
            (qual === null || qual === undefined ? "" :
             `<div class="mac-barra-forca q"><i style="width:${Math.max(2, Math.min(100, qual))}%"></i></div>`)}
```

As quatro barras são quantidade · diversidade · atualidade · confiabilidade. A parte **sem
dado** recebe hachura de 45° com borda âmbar tracejada e o valor sai escrito `sem dado`,
em âmbar — nunca zero. Hachura é a única trama do sistema e significa exatamente
"não existe dado aqui".

---

### 2.7 Notas de rodapé numeradas (§6.7) — opcional, entra por último

**Função:** `matrizPares()`
**Âncora:** o `</section>` que fecha o `return` da função.

Antes dele, e **nesta forma**, não com `med()`:

```js
      ${(window.HCI_MEDIDORES ? window.HCI_MEDIDORES.notas([
        "As faixas 0–14, 15–24, 25–39 e 40+ são provisórias: foram escolhidas por ordem de grandeza e vão ao backtest junto com o limiar. Não existe convicção histórica calibrada.",
        { termo: "defasagem de entrega", texto: "é o tempo entre o horário agendado e o dado chegar aqui; não confundir com a defasagem de referência do BLS, que é de um mês e é inevitável." },
        { termo: "geopolítica", texto: "saiu do voto em 05/set/2026 e ficou como contexto declarado — as dimensões que votam passaram a ser três." }
      ]).bloco() : "")}
```

O motivo de a forma ser outra: `notas()` é a única das sete que devolve um **objeto**
(`{ marcador, bloco, total }`), não string. Como `med()` devolve `""` quando o módulo não
está carregado, um `med("notas", ...).bloco()` estouraria justamente no caso em que tudo
mais degrada em silêncio. O `window.HCI_MEDIDORES ? ... : ""` acima resolve isso.

Se preferir simplicidade, **pule o passo 2.7 inteiro**: é o único enxerto que não corrige
nenhum item da lista da §8.

---

## 3. `colgroup` e a classe da tabela (item 8 da §8)

A §5.1 exige `colgroup` em toda tabela, e **CSS não pode criar `colgroup`** — é marcação.
Este é o único item da lista de verificação que ficou fora do alcance do `estilo_hci.css`,
e é seu.

Na tabela de `painelBancos()`, âncora `<div class="table-wrap"><table class="mac-tabela">`,
acrescente o `colgroup` logo depois da `<table ...>` e antes do `<thead>`:

```html
      <div class="table-wrap"><table class="mac-tabela">
        <colgroup>
          <col style="width:96px">              <!-- Moeda                     -->
          <col style="width:116px">             <!-- Taxa (número, à direita)   -->
          <col style="min-width:180px">         <!-- Regime                     -->
          <col style="min-width:210px">         <!-- Próximo evento relevante   -->
          <col style="width:200px">             <!-- Próxima decisão            -->
          <col style="width:150px">             <!-- Leitura                    -->
        </colgroup>
```

Essas medidas são as mesmas que o `estilo_hci.css` já aplica por `nth-child` à tabela dos
bancos **na ordem de colunas que ela tem hoje**. Elas casam; o `colgroup` só torna a
declaração explícita, como a especificação pede.

**Se um dia você reordenar as colunas** para a ordem da §5.5 da especificação
(Moeda · Banco/instrumento · Taxa vigente · Última mudança · Próxima reunião · Hora local),
então — e só então — ponha a classe:

```html
<table class="mac-tabela tabela-bancos">
```

e use as larguras da especificação: `58 · min180 · 158 · 172 · 192 · 128`. A classe
`tabela-bancos` carrega exatamente essas medidas, com número à direita e texto à esquerda
na ordem certa. **Não ponha a classe antes de reordenar**: ela alinharia à direita colunas
de texto. Vale o mesmo para `tabela-eua` (min-width 960) e `tabela-pares` (min-width 880).

---

## 4. O que NÃO fazer — cinco armadilhas medidas

1. **Não carregue o `estilo_hci.css` antes do `styles.css`/`theme.css`.** Ele precisa vir
   por último. E não apague os dois: a folha nova é aditiva, não é um substituto completo.
2. **Não tire o prefixo `html` dos seletores.** O `ui_macro.js` injeta um `<style>` em
   tempo de execução, ou seja, *depois* da folha. O prefixo `html` é o que faz a folha
   ganhar por especificidade (0,0,1,1 contra 0,0,1,0). Sem ele, o gradiente do `body`, a
   sombra dos cartões e o `opacity:.45` do `.mac-de100` voltam todos.
3. **Não apague os três varredores da §4.1** (`box-shadow:none`, `background-image:none`,
   `opacity:1`, os três com `!important`). São eles que apagam as sombras, os gradientes e
   as mais de oitenta declarações de `opacity` sobre texto do produto antigo. A régua de
   contraste depende disso: `opacity:.55` sobre `--tinta-2` derruba a leitura para 3,4:1.
4. **Não injete a faixa de estado dentro do `<main>`** — motivo no passo 2.2.
5. **Não chame `med(...)` sem a guarda `|| <o que já existia>`** (menos onde este documento
   disser). Cada enxerto tem de degradar sozinho.

---

## 5. Como conferir que ligou — e que não quebrou

Antes de commitar, rode os quatro conferentes. Todos leem os arquivos reais e saem com
código 0:

```
node tests/teste_medidores.js          # 118 asserções nas 7 funções contra os JSONs reais
node tests/teste_contraste.js          # toda tinta x toda superfície, WCAG calculado
node tests/teste_contraste_pares.js    # só os pares de cor que a folha realmente escreve
node tests/teste_lista_secao8.js       # a lista de dez itens da §8, item a item
```

Depois abra o painel (`python -m http.server 8797` na pasta, e
`http://localhost:8797`) e confira seis coisas na tela:

1. a **faixa de estado** aparece grudada no topo e o cabeçalho ficou logo abaixo dela,
   sem sobreposição;
2. a tabela dos bancos tem **zebra**, e passar o mouse por uma linha desenha um **fio
   turquesa de 2px à esquerda** — o fundo da linha **não** muda;
3. nenhuma sombra e nenhum gradiente em lugar nenhum;
4. o alarme, se houver, tem **quatro colunas** e a última é uma frase inteira;
5. os números estão todos em Spline Sans Mono, à direita, com vírgula decimal;
6. o bloco de método está em Spectral, três colunas, e **depois** do dado.

E rode este trecho no console do navegador — ele é o mesmo teste que o conferente usou, e
tem de sair com as quatro listas vazias:

```js
const OK = ['Archivo','Spline Sans Mono','Spectral'];
const fora=[],opac=[],somb=[],grad=[];
document.querySelectorAll('*').forEach(el=>{
  const s=getComputedStyle(el);
  const fam=(s.fontFamily||'').split(',')[0].replace(/["']/g,'').trim();
  const temTexto=[...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim().length);
  if(temTexto&&!OK.includes(fam)&&el.tagName!=='TITLE') fora.push(el.className+'|'+fam);
  if(temTexto&&parseFloat(s.opacity)<1) opac.push(el.className+'|'+s.opacity);
  if(s.boxShadow!=='none'&&s.boxShadow!=='rgb(69, 220, 203) 2px 0px 0px 0px inset') somb.push(el.className);
  if(s.backgroundImage!=='none'&&!/repeating-linear-gradient\(45deg/.test(s.backgroundImage)) grad.push(el.className);
});
console.log({fonte_de_sistema:fora, opacity_sobre_texto:opac, sombra:somb, gradiente:grad});
```

---

## 6. Se quebrar, desligar leva dez segundos

Tire as duas tags do `index.html`. Os enxertos do `ui_macro.js` **continuam funcionando
sem o módulo**: `med()` devolve `""`, todo enxerto cai no `|| <o que já existia>`, a faixa
de estado simplesmente não é inserida, e o painel volta a ser exatamente o de antes. Foi
para isso que cada enxerto foi escrito com a alternativa do lado — inclusive o do passo
2.7, que testa `window.HCI_MEDIDORES` antes de chamar.

Se quiser desligar só o desenho e manter os medidores, tire apenas o `<link>`; se quiser o
contrário, tire apenas o `<script>`. As duas peças são independentes uma da outra: a folha
desenha `.med-*` que ninguém emitiu (não aparece nada) e o módulo emite `.med-*` que
ninguém desenhou (aparece cru). Ligar as duas é o estado correto.

---

## 7. O que ficou aberto (não é bug, é fronteira)

| # | O quê | De quem é |
|---|---|---|
| 1 | número solto dentro de `<td>` sem classe não pega a fonte mono nem o alinhamento à direita | de quem escreve o HTML: basta pôr `class="num"` ou `class="mac-num-td"` |
| 2 | `colgroup` nas tabelas | passo 3 deste documento |
| 3 | a frase que nega o sinal ("leitura do lado fundamental, não sinal de entrada") no cabeçalho e no método | do gerador de HTML; a folha só garante que ela saia legível, em Spectral `--tinta-2` |
| 4 | a coluna **consequência** de cada alarme escrita em frase inteira | o `ui_medidores.js` já a escreve para os sete alarmes que gera; alarme novo tem de trazer a sua |
| 5 | as colunas da tabela dos bancos na ordem da §5.5 | opcional, passo 3 |
