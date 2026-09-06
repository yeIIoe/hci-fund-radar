# MÉTODO — a leitura de sentimento macro do HCI FUND RADAR

*Documento vivo. Revisão de 06/set/2026.*
*Cada número aqui tem, ao lado, a janela em que foi medido e o rótulo de PROVISÓRIO quando é
provisório. Onde não há medição, está escrito que não há.*

---

## 1. O que a leitura é, e o que ela não é

**É** uma leitura declarada: pega o que foi divulgado nos últimos 42 dias, compara com o que se
esperava, soma isso ao ponto do ciclo em que cada banco central está, e diz para que lado a
política monetária de cada moeda está inclinada.

**NÃO É** uma previsão de preço, e **não há backtest**. Nenhuma dimensão, nenhum peso, nenhum
limiar deste documento foi validado contra o que aconteceu depois. Por isso o campo
`conviccao_historica` sai `null` em todos os 28 pares e continuará saindo até existir um teste
com amostra declarada.

**Três coisas que este método nunca faz:**

1. **Não usa juro.** Nenhuma dimensão lê curva, yield ou diferencial. Decisão do dono, repetida
   em 04/set. A aba de juros do painel existe como contexto e está rotulada como tal.
2. **Não mostra pontuação.** A leitura contínua existe dentro do arquivo, para auditoria, e
   nunca aparece na tela — nem o número, nem a palavra. O que a tela mostra é
   *"inclinado à alta"*, *"2 de 2 dimensões concordam"*, *"evidência forte"*.
3. **Não conta silêncio como voto.** Fonte que não respondeu sai como buraco declarado, com o
   motivo escrito. Ela nunca vira zero, porque zero é uma leitura e ausência não é.

---

## 2. As dimensões — o que cada uma mede

São quatro dimensões. **Duas votam. Duas informam.**

| dimensão | o que mede | vota hoje? | peso |
|---|---|---|---|
| **DADOS** | as divulgações desde a última decisão, contra o consenso | **sim** | ±0,25 |
| **CICLO** | o último movimento de juro, envelhecido | **sim** | ±0,25 |
| TEXTO (falas) | o que os dirigentes disseram | **não** — experimental | 0,00 |
| GEOPOLÍTICA | picos de conflito e de energia | **não** — experimental | 0,00 |

Teto por moeda: **0,50** (duas dimensões × 0,25). Teto por par: **1,00** (as duas pernas).

### 2.1 DADOS — o que foi divulgado (vota, ±0,25)

Janela de **42 dias**, cortada pela última decisão do banco: o que saiu antes da reunião já foi
respondido por ela e não conta de novo.

Cada divulgação entra com `peso da família × modulador de impacto × decaimento`:

- **peso da família** — 10 para inflação núcleo, 9 salários, 8 emprego e desemprego, 7 inflação
  cheia, 6 PIB e expectativa, 5 PMI, 4 varejo, 3 produção/moradia/auxílio, 2 balança e
  confiança. São **julgamento declarado**, não medição.
- **modulador de impacto** — alto 1,0 · médio 0,5 · baixo 0,2 (rótulo da própria fonte).
- **decaimento** — meia-vida de **21 dias**. Dado de ontem pesa o dobro do dado de três semanas
  atrás.

A soma vira direção quando passa de **±5,0**; abaixo disso a dimensão lê MANUTENÇÃO. A soma é
comprimida por `tanh(soma/10)` antes de virar leitura, o que satura o efeito de janelas muito
carregadas.

#### A régua da surpresa — o que conta como "veio diferente do esperado"

Esta régua é a mesma nos três leitores (calendário, sentimento e dados americanos). Ela existe
numa função só, `macro_eventos.corte_da_surpresa`, justamente para que o mesmo dado não possa
sair "em linha" numa tela e "hawkish" na outra.

**Conserto de 06/set — e ele mudou a escala do painel inteiro.** Até esta revisão a faixa neutra
era relativa ao NÍVEL do indicador: `max(|consenso| × 0,35 ; 0,10)`. Isso é 35% do nível, não da
surpresa, e para todo indicador que vive num nível alto o corte ficava absurdo. Medido nas
**364 divulgações** com consenso e família com peso da janela de 42 dias (8 moedas, 06/set):

| família | corte que a régua antiga produzia | divulgações "em linha" |
|---|---|---|
| PMI | 18,5 pontos numa escala 0–100 | **100%** |
| confiança | 18,9 pontos | **100%** |
| auxílio-desemprego | 70,4 mil pedidos | **100%** |
| desemprego | 1,96 ponto percentual | 90% |
| inflação núcleo | 0,88 ponto percentual | 90% |
| **total** | | **278 de 364 = 76%** |

Ou seja: o peso 10 da inflação núcleo era decorativo, porque 9 em cada 10 divulgações de núcleo
eram zeradas **antes** de o peso ser aplicado.

**O que passou a valer:** um corte **absoluto por família**, no valor da **mediana do |surpresa|
daquela família na janela medida**. Lê-se: *a divulgação só conta quando surpreende mais do que o
normal para o próprio indicador.*

| família | corte (±) | unidade | mediana medida | n |
|---|---|---|---|---|
| inflação núcleo | 0,10 | pontos percentuais | 0,10 | 21 |
| inflação cheia | 0,10 | pontos percentuais | 0,10 | 108 |
| expectativa de inflação | 0,10 | pontos percentuais | 0,00 | 4 |
| salários | 0,10 | pontos percentuais | 0,10 | 12 |
| desemprego | 0,10 | pontos percentuais | 0,10 | 22 |
| PIB | 0,10 | pontos percentuais | 0,10 | 35 |
| produção | 0,50 | pontos percentuais | 0,50 | 15 |
| varejo | 0,60 | pontos percentuais | 0,60 | 26 |
| PMI | 0,40 | pontos de índice | 0,40 | 35 |
| confiança | 0,90 | pontos de índice | 0,90 | 29 |
| auxílio-desemprego | 3,00 | mil pedidos | 3,00 | 10 |

**Onde o corte absoluto NÃO se aplica, e por quê:** balança, moradia e criação de vagas continuam
na régua relativa antiga, porque a **unidade muda de país para país dentro da mesma família** — a
criação de vagas americana vem em milhares e a neozelandesa em porcento; a balança vem em milhões
num país e em bilhões noutro. Um único número absoluto para a família inteira mentiria. Fica
declarado como buraco, não consertado em silêncio. A decisão de juro tem corte próprio de
**0,10 pp** (menos de meio quantum de 25 pb).

**⚠️ Efeito medido, e ele é grande.** Na mesma janela, "em linha" caiu de 278/364 (76%) para
189/364 (51%). 117 divulgações trocaram de classe: 103 ganharam direção (o CPI australiano de 3,8
contra 4,0 esperado, que saía "em linha"; o Ivey PMI canadense de 64,3 contra 56,2) e 14 perderam
(vendas no varejo de −0,3 contra +0,1, que é o ruído normal daquela série). **Consequência
direta na tela:** a distribuição dos 28 pares foi de `sem tese 13 · observação 5 · moderada 8 ·
forte 2` para `sem tese 9 · observação 4 · moderada 6 · forte 9`. O painel ficou mais sensível
porque parou de apagar três em cada quatro divulgações — e as faixas, desenhadas para a escala
muda, **ficaram desalinhadas**. Enquanto não houver backtest, leia a **ordem** dos pares, não a
palavra da faixa (ver §5).

**⚠️ Limite conhecido desta régua:** os cortes vieram de uma mediana medida numa janela de 42
dias, numa única leitura, e não foram validados contra o que o banco central fez depois. São
PROVISÓRIOS. O que eles consertam é a **heterogeneidade** — antes a fatia neutra ia de 20%
(produção) a 100% (PMI, confiança, auxílio); depois fica entre 40% e 57% em quase todas. Nenhuma
família continua muda por construção, e nenhuma dispara por construção. Isso é diferente de estar
certo.

**⚠️ Segundo limite, que a correção deixou visível:** a dimensão de dados é uma **soma**, não uma
média. Uma moeda com 157 divulgações na janela (EUR) acumula muito mais do que uma com 3 (CAD),
e o `tanh` só satura no fim. Isso já era assim antes; ao parar de apagar 76% das divulgações, o
efeito ficou grande o bastante para ser visto (EUR foi de +3,4 para +18,8 de soma; CAD de −4,0
para −1,7). Normalizar pela contagem é uma decisão de método que **ainda não foi tomada**.

### 2.2 TEXTO — o que os dirigentes disseram (experimental, **NÃO VOTA**)

Selo em todas as oito moedas: **"experimental — contexto, não vota"**. Peso aplicado 0,0.

Ela existe porque o que o dirigente diz é informação legítima. Ela não vota porque a forma de
lê-la nunca foi medida. Ver §3.

### 2.3 CICLO — o último movimento de juro (vota, ±0,25)

Não é o nível da taxa: é **o que o banco fez por último e há quanto tempo**.

```
decaimento = 0,5 ^ (idade em dias / 120)
```

Meia-vida de **120 dias**: o último movimento perde metade do peso em quatro meses. Abaixo do
piso de **0,25** o movimento lê como MANUTENÇÃO e a dimensão não vota.

**O penhasco não acabou, mudou de lugar.** O piso de 0,25 é ele próprio um degrau: o decaimento
cruza 0,25 aos **240 dias exatos**, e a contribuição cai de 0,063 para 0,000 de um dia para o
outro. É quatro vezes menor que o penhasco antigo (que derrubava 0,25 de uma vez), mas continua
sendo um degrau, e o lugar dele importa: o GBP está hoje com decaimento 0,220, 12% abaixo do
piso; com piso 0,20 — tão arbitrário quanto 0,25 — a perna GBP passaria a votar CORTA. O campo
`penhasco` do arquivo publica onde o degrau está.

**Um termo foi desligado e o motivo está registrado.** Havia um segundo fator, por reuniões de
manutenção desde o último movimento. Ele foi desligado em 05/set porque **media o arquivo, não o
banco**: só enxergava as reuniões que `bancos_centrais.json` ainda listava olhando para frente e
que já tinham passado. Medido: NZD e CAD levavam 1 reunião só porque a reunião de 02/09 ainda
estava na lista, enquanto USD, GBP e CHF levavam zero apesar de terem feito muito mais reuniões
de manutenção. Ruído de calendário vestido de sinal. A contagem continua sendo gravada
(`reunioes_de_manutencao_desde`) com `reunioes_no_decaimento: false` ao lado. Religar exige que
`bancos_centrais.py` guarde o **histórico** de reuniões, não só as futuras.

**A taxa e o último movimento expiram — e isso já quebrou uma vez.** Em 06/set descobriu-se que a
reconciliação da taxa lia apenas a janela rolante do calendário (~3 dias para trás): quando a
decisão saía da janela, o cadastro estático voltava a valer e o painel mostrava número errado.
Foi exatamente o que aconteceu com o RBNZ, que subiu a taxa de 2,50% para 2,75% em 02/set e
"desapareceu" do arquivo em 06/set. Consertado com busca de 120 dias mais memória da última
reconciliação. **A lição vale para o método inteiro: janela rolante não serve de memória.**

### 2.4 GEOPOLÍTICA — experimental, **NÃO VOTA**

Picos de conflito e de energia por moeda, via GDELT, com corte em z ≥ 1,5. Selo experimental,
peso 0,0, seção recolhida por padrão na tela.

Ela **votou por um dia** (decisão de 04/set) e a decisão foi **revogada em 05/set** por nunca ter
sido medida. A hipótese que precisaria ser testada antes de qualquer voto está escrita no
arquivo: *um pico de conflito com z ≥ 2 muda o retorno de 20 dias das moedas de risco?* Não foi
testada.

---

## 3. A régua das falas — o que o leitor de discursos faz, e por que ele não vota

O painel **não conta palavras hawkish e dovish**. Contar palavras foi o erro que o dono apontou,
com três exemplos que agora servem de teste permanente:

| dirigente | a contagem dizia | a régua diz | por quê |
|---|---|---|---|
| Waller | hawkish | **manutenção** | "holding the target" é apoio explícito a MANTER |
| Barr | hawkish firme | **alta condicional** | "raise rates" só vale se a condição se realizar |
| Warsh | hawkish | **indeterminado** | fala de política de juros sem indicar direção |

**Ordem de leitura, fixa:** sujeito → marcador → tempo verbal → atribuição a terceiros → negação
→ condição.

- **Marcadores são expressões com objeto junto**, nunca palavra solta: `raise ... rates`, não
  `raise` (que casa com "raise questions"); `tighten ... policy`, não `tighten` (que casa com
  "tighten financial conditions").
- **A frase é quebrada em orações antes da negação.** Sem isso, o "not" de *"if inflation appears
  NOT to be moderating"* negaria o "raise rates" que vem depois do "then", e o Barr sairia corte.
- **Negar movimento é manutenção.** "would not support a rate cut" → manutenção.
- **Condição rebaixa alta e corte para condicional, mas não rebaixa manutenção** — manter sob
  condição continua manter.
- **Passado é descartado.** "we raised the policy rate by 425bp in 2022" não diz nada sobre o
  próximo passo.
- **Exceção medida (06/set): a decisão anunciada não é passado.** O nível de maior peso da
  hierarquia — o comunicado — é sempre escrito no passado, porque ele *anuncia* o que acabou de
  ser decidido: *"we decided to maintain the policy interest rate at 2.25%"*. O veto de tempo
  verbal calava justamente a fonte de peso 1,0 e devolvia "nenhuma frase de postura foi
  extraída", uma afirmação falsa sobre o anúncio de decisão do próprio banco. A exceção vale
  **só** para manutenção anunciada; "we decided to cut" continua sendo passado.
- **Atribuição a terceiros descarta a frase — e o nome do banco não a resgata.** Este foi o
  segundo conserto de 06/set. A regra antiga resgatava a frase sempre que a instituição fosse
  nomeada, e isso derrotava o filtro na forma mais comum do gênero: *"o mercado espera que o
  banco X faça Y"*. Medido:
  - `"Market participants expect a rate cut in December."` → indeterminado *(certo)*
  - `"Market participants expect the MPC to keep rates on hold."` → **manutenção** *(errado)*
  - `"The market expects the Fed to cut rates in December."` → **corte** *(errado)*

  E estava ao vivo: o único veredito do GBP saía "manutenção", justificado pelo trecho *"it is
  natural for market participants to interpret this set of scenarios as suggesting the MPC is
  seeking to keep rates on hold"*. Agora só a **primeira pessoa** ("I", "we", "eu", "nós")
  resgata, porque nomear a instituição não diz quem está falando — e a atribuição vale para a
  **frase inteira**, não só para a oração, senão um "but" abre uma oração nova e a segunda metade
  escapa.
- **Pergunta é indeterminada.** Em entrevista, quem pergunta é o repórter. Regra provisória,
  criada a partir de UM caso medido (a entrevista do Cipollone, cuja única frase com marcador era
  uma pergunta e teria carimbado o BCE de hawkish firme).

**A hierarquia da fonte** — comunicado e ata (1,0) · discurso oficial (1,0) · imprensa que cita
fala com nome (0,4) · manchete (0,0). **Manchete pesa zero**: o painel já mostrou "38 discursos"
do AUD que eram matérias de jornal.

**O trecho que vai para a tela é o do orador, não da página.** Conserto de 06/set: o veredito do
BoC vinha justificado por *"Content Type(s) : Press , Speeches and appearances , Webcasts Bank of
Canada maintains the policy rate at 2¼%…"* — a linha de metadados do site colada à **manchete**,
e o marcador que decidia o veredito estava dentro da manchete, que a lei da casa precifica em
zero. O bloco de metadados agora é descartado antes de a página virar frase, em duas barreiras.

### Por que ela não vota

Porque **nada disso foi medido**. A validação aceitável está escrita no cabeçalho do módulo, em
sete pontos: n ≥ 200 falas, ≥ 5 bancos, ≥ 3 anos, ≥ 30 falas por classe de decisão, consenso
point-in-time, ter de ganhar da referência burra *"sempre manutenção"*, condicionais medidos à
parte, e a regra congelada antes do teste fora da amostra. **Nenhum desses sete existe hoje.**
Até existirem, a dimensão informa e não vota, sem atalho.

### O que a régua ainda não alcança

- **Cobertura, não classificação.** Sete dos doze documentos chegam com zero frases extraídas
  (BCE inteiro, entre eles). O veredito sai "indeterminado — nenhuma frase de postura foi
  extraída", que é honesto e vazio. O conserto é no extrator de páginas, não na régua.
- **AUD, NZD e CHF saem com lista vazia** porque não há discurso oficial coletado (RBA e RBNZ
  bloqueiam por 403; o SNB não tem feed conhecido). Correto pela lei — silêncio não é voto — mas
  o leitor verá "veredito ainda não classificado" nessas três moedas.

---

## 4. A winsorização — nenhuma divulgação manda sozinha

Cada divulgação entra na soma com no máximo **4,0 em módulo**. Como o limiar da dimensão é
**5,0**, e 4,0 < 5,0, **nenhuma divulgação sozinha atinge o limiar**: são precisas pelo menos
duas. Isso é aritmética do teto, não observação de um dia.

**O caso que originou a regra:** o CAD tinha uma única divulgação de emprego com contribuição
−7,9 respondendo por 100% da leitura de dados, com três divulgações no ciclo.

**Um fator foi retirado, e o motivo é medido.** O teto era `2,5 × mediana da janela`. Depois do
decaimento a mediana vive perto de 0,5, então o teto caía para ~1,2 — e isso **fabricava**
direção (um item de +7,83 com dezessete de −0,50 fazia −0,67 virar −7,25) e **apagava** dado
legítimo (−9,0 e −8,0 no meio do ruído: −16,60 virava −1,85). Hoje o teto é absoluto e fixo.

**O preço da regra, dito na cara:** winsorizar termos de uma soma **desloca o total** pelo tanto
que foi cortado, no sentido contrário ao do item cortado. Não é defeito escondido — cada moeda
grava `deslocamento_pelo_teto` e `direcao_antes_do_teto`.

**O alerta de dominância continua.** Quando o maior item responde por mais de 50% da dimensão, o
par recebe um alerta escrito. Hoje: NZD 100% (Terms of Trade Index) e CAD 63% (Net Change in
Employment).

O valor 4,0 é **PROVISÓRIO**, escolhido por ordem de grandeza — a menor folga que ainda deixa
duas divulgações grandes virarem a leitura — e vai ao backtest junto com o limiar.

---

## 5. As faixas — a zona neutra

### Faixas do par (PROVISÓRIAS)

Divergência de 0 a 100, calculada como `|diferença entre as duas pernas| / teto TEÓRICO × 100`:

| faixa | divergência | o que significa |
|---|---|---|
| sem tese | 0 – 14 | as duas pernas leem quase igual |
| observação | 15 – 24 | há diferença, não há tese |
| moderada | 25 – 39 | tese, com evidência a conferir |
| forte | 40 – 100 | a maior diferença que a régua produz |

**⚠️ Estas faixas estão desalinhadas, e isso é um fato, não uma ressalva de estilo.** Elas foram
desenhadas em 05/set, para uma escala em que (a) três dimensões votavam e o teto do par era 1,50,
e (b) 76% das divulgações eram apagadas pela régua da surpresa. Hoje duas dimensões votam, o teto
é 1,00 e 51% das divulgações são apagadas. Os dois efeitos mexem a escala em sentidos diferentes
e **não se cancelam**. Medido nos mesmos 28 pares:

| momento | sem tese | observação | moderada | forte |
|---|---|---|---|---|
| 04/set — 3 dimensões, teto 1,50 | 12 | 7 | 8 | 1 |
| 06/set — 2 dimensões, régua antiga | 13 | 5 | 8 | 2 |
| 06/set — 2 dimensões, régua nova | 9 | 4 | 6 | **9** |

Nove pares na faixa mais alta não é um sinal de que há nove teses fortes: é o sinal de que **o
corte de 40 foi desenhado para outra escala**. Enquanto não houver backtest, use a **ordem** dos
pares, não o nome da faixa.

### A zona SEM LEITURA, por moeda (PROVISÓRIA)

Uma moeda sai **"sem leitura"** quando:

- a intensidade relativa `(|leitura| / 0,50) × 100` fica **abaixo de 15**, ou
- **menos de duas dimensões votam** naquela moeda.

Hoje: **2 de 8** — GBP (intensidade 14, um ponto abaixo do piso) e CAD (intensidade 8).

O denominador é o teto **teórico** (0,50), não o teto ligado. Isso é deliberado: dividir pelo teto
ligado fazia a **falta de dado inflar** a leitura, que é exatamente o vício oposto ao que se quer.
Com o teto teórico, menos evidência dá intensidade menor.

### A zona SEM LEITURA agora vale para o PAR (conserto de 06/set)

Até esta revisão a zona marcava a moeda e **não era herdada pelo par**: nenhum dos 28 pares saía
sem leitura. Medido na rodada da manhã: 18 dos 28 pares tinham ao menos uma perna sem leitura; 9
dos 15 pares com tese tinham; e em 4 deles a perna que **dá o motivo** estava sem leitura, com
qualidade da evidência 0/100. O topo da tela mandava comprar NZD/USD com a maior divergência do
dia, atribuindo 55% do motivo a uma perna que o próprio arquivo declarava sem direção.

Duas regras novas, que **propagam** a regra que já existia na moeda em vez de inventar limiar:

1. Se a perna que dá o motivo está sem leitura, **o par não tem tese** — um par não pode ter mais
   direção do que a perna que o move.
2. Se a qualidade da evidência do par é 0 ou não existe, **o par não sai da zona de observação**,
   por maior que seja a divergência. Divergência grande entre dois silêncios continua sendo dois
   silêncios.

O rebaixamento fica gravado em `estado_limitado_por`, com o motivo escrito, para ninguém precisar
adivinhar por que um par com divergência alta está rotulado observação.

---

## 6. A qualidade da evidência

Nota de 0 a 100 por moeda, com rótulo provisório: **fraca** < 40 · **moderada** 40–69 ·
**forte** ≥ 70. A do par é a **menor das duas pernas** — o elo fraco manda, e o arquivo diz qual
perna é o elo.

A nota é a média das partes **que têm dado**. A parte "confiabilidade da fonte" foi desligada em
05/set porque media o peso da fonte de **fala**, e fala não vota — o que não vota não é evidência.

**Perna sem nota não vira zero.** Quando nenhuma parte tem dado, o par sai com qualidade `null` e
o alerta diz de qual perna faltou.

**⚠️ Buraco conhecido:** a parte "quantidade" conta divulgações que **não formaram** a leitura —
inclusive as que saíram em linha e empurraram zero. Uma moeda com 84 divulgações na janela
recebe quantidade 100/100 mesmo que só 14 tenham direção. A leitura oposta também é defensável
(uma janela com 84 divulgações genuinamente está melhor evidenciada do que uma com 3, e "tudo
saiu em linha" é informação), e por isso a conta não foi mudada — mas o buraco fica declarado.

---

## 7. O frescor — a validade da leitura, e os dois relógios

O painel **não é tempo real e não se apresenta como tal**. Ele roda numa cadeia agendada, e a
honestidade aqui é dizer há quanto tempo o dado foi visto.

### Relógio 1 — as fontes que votam

`frescor.atraso_min` é a idade da fonte mais velha **entre as que votam** (calendário e bancos
centrais) no instante em que a rodada foi gerada. Discurso, imprensa e geopolítica são contexto:
a idade deles fica gravada, rotulada, e **não muda o estado**.

Limiares **PROVISÓRIOS**: **45 min** → atrasado · **120 min** → muito atrasado.
Só `muito_atrasado` liga `bloqueia_leitura`, e com ele a interface substitui toda ação
direcional por *"leitura suspensa — dado atrasado"*.

### Relógio 2 — a idade da publicação (novo em 06/set)

O relógio 1 sozinho **mente por omissão**, e isso foi medido: como `bancos_centrais.json` é
reescrito pelo passo anterior da mesma cadeia e o calendário é buscado ao vivo, `atraso_min` é o
tempo entre dois **passos da mesma rodada** — de 1 a 18 minutos na prática. Nas 13 versões do
arquivo que já traziam o bloco de frescor, o estado saiu "ok" em **13 de 13**. A tarja nunca
acendeu. E o número gravado envelhece junto com o arquivo: ler o campo congelado é ler um relógio
parado.

O relógio 2 mede o que o leitor precisa: `agora − gerado_em`, **recalculado no navegador**.

Os limiares aqui são outros de propósito, e saem do ritmo **medido**: 33 rodadas publicadas entre
02/set 10:34 e 06/set 17:59 tiveram intervalo mínimo de 91 min, **mediana de 157 min (2h37)**,
média 188 e máximo 549 min (9h09) — o cron pede a cada 15 minutos, mas a própria documentação do
GitHub Actions diz que o `schedule` pode atrasar em carga alta e que trabalho na fila pode ser
descartado. Aplicar 45/120 a este relógio deixaria a tarja âmbar em **100%** das rodadas e
vermelha em **78%**, e tarja que grita sempre não avisa nada.

Limiares **PROVISÓRIOS** da publicação: **180 min** → atrasada · **360 min** → muito atrasada.
A idade da publicação **avisa e nunca suspende** a leitura: quem suspende é o estado das fontes
que votam. Os dois números vêm de 33 observações em quatro dias, não de um estudo de
disponibilidade.

---

## 8. O que é look-ahead conhecido

O painel tem um corte de tempo, para olhar um dia passado. **Ele não está limpo**, e a auditoria
está publicada dentro do próprio painel. Dos quatro riscos que o dono levantou:

1. **Valor revisado — LIMPO, e medido.** `divulgado` e `revisado` são chaves separadas na fonte;
   o sentimento nunca lê `revisado`. Conferido contra dois commits (30/ago e 03/set): dos ids em
   comum, apenas 15 e 66 tinham valor divulgado nos dois lados — esse é o n de verdade, e nesses,
   zero valores mudaram. O calendário é janela rolante, então esse n encolhe todo dia: **número
   medido aqui só vale com a data ao lado**.
2. **Manchete posterior ao corte — CONTAMINA**, conserto parcial. A varredura de notícias é uma
   janela de 72 h ao vivo, sem filtro de data. O módulo de auditoria esconde da lista as
   manchetes posteriores ao corte e diz quantas escondeu, mas a contagem **já entrou** e não dá
   para desfazer.
3. **Pesos e limiares de hoje — CONTAMINA**, não consertável sem reescrever. Janela, meia-vida,
   limiar, pesos e todas as réguas novas são **constantes de código**, não dado. Não existe
   recomputação histórica: o arquivo é um retrato. **Cada régua nova que entra piora este item —
   inclusive a régua da surpresa de 06/set.** O que resolve é o registro imutável (§9).
4. **Reuniões e taxas atuais — CONTAMINA**, detectado e nomeado. As taxas e o último movimento são
   sempre os atuais, e a idade do ciclo é medida contra hoje. Com o corte em 01/nov/2025, seis dos
   oito bancos aparecem com uma decisão de juro que ainda não tinha acontecido.

**E o buraco maior, que nenhum dos quatro cobre:** a camada de desenho troca o conteúdo de quatro
painéis a cada 900 ms e move para um contêiner oculto justamente os elementos que o corte de tempo
reescreve. Nesses quatro painéis, **o corte desenha onde ninguém vê e a tela mostra a leitura de
hoje**. Consertar isso é reescrever a camada de desenho. Enquanto não for, o aviso no banner diz
na cara que a tela é de hoje.

---

## 9. O snapshot — o registro imutável

`data/snapshots/AAAA-MM-DD.jsonl`, **append-only, com trava exclusiva: nenhuma linha antiga é
reescrita**.

**Por que existe:** a leitura de hoje **não pode ser reconstruída amanhã**. O calendário é buscado
ao vivo numa janela rolante, as manchetes têm janela de 72 h e o consenso de um evento some quando
a janela passa. Sem gravar agora, a "convicção histórica" fica `null` para sempre, porque não há
amostra para calibrar — e a tentação passa a ser reconstruir o consenso a posteriori, que é
exatamente o furo que matou o backtest do Deep Value.

**Regra anti-entulho:** não grava os 28 pares a cada rodada. Grava a primeira leitura do dia,
quando muda direção / divergência / qualidade da evidência, e logo depois de evento de impacto
alto. Cada linha diz **por que** foi gravada.

Um arquivo irmão (`data/calendario_arquivo/AAAA-MM.jsonl`) faz o mesmo para o **consenso** de cada
evento, com hash por linha e encadeamento por arquivo: editar uma linha antiga quebra a cadeia de
todas as seguintes.

**Nada disso é backtest.** É a condição para que um exista algum dia. Hoje o registro tem quatro
dias.

---

## 10. As leis da casa que este método obedece

1. **Yield nunca entra no sentimento.**
2. **A pontuação não aparece na interface** — nem o número, nem a palavra, nem em dica de tela.
3. **Convicção histórica é `null`** até haver backtest com amostra declarada.
4. **Silêncio não é voto.** Fonte que não respondeu é buraco declarado, nunca zero.
5. **Todo limiar novo é PROVISÓRIO** e sai rotulado como tal — na tela e no arquivo.
6. **Dimensão que não foi validada não vota**, apenas informa.
7. **Uma régua só.** O mesmo dado não pode sair "em linha" numa tela e "hawkish" na outra.
8. **Janela rolante não é memória.** O que sai da janela precisa estar gravado, ou o painel volta
   a mostrar o cadastro antigo como se fosse notícia.

**⚠️ A lei 6, aplicada com rigor, também acusa as duas dimensões que sobraram.** DADOS e CICLO
votam **sem validação declarada** — não há backtest para elas em lugar nenhum deste repositório.
A diferença em relação a fala e geopolítica é que estas foram testadas contra o exemplo do dono e
reprovaram, enquanto aquelas nunca foram testadas. Não é o mesmo que estar certo.

---

## 11. O que ainda está aberto

- **Nenhum backtest.** Todos os pesos, limiares e faixas são declarados, não calibrados. As
  faixas do par estão comprovadamente desalinhadas com a escala atual (§5).
- **A dimensão de dados é soma, não média**, e moeda com muitas divulgações acumula mais (§2.1).
- **Corte absoluto por família não existe** para balança, moradia e criação de vagas, porque a
  unidade muda de país para país (§2.1).
- **O extrator de falas não alcança o BCE**: sete de doze documentos chegam sem frase (§3).
- **Não há discurso oficial de RBA, RBNZ e SNB** (403 e ausência de feed) — três moedas sem
  veredito por orador (§3).
- **A parte "quantidade" da qualidade da evidência conta divulgação que não votou** (§6).
- **O corte de tempo contamina em três dos quatro riscos**, e a camada de desenho anula o corte em
  quatro painéis (§8).
- **O painel perdeu o estado "manutenção" na leitura**: a zona só devolve *sem leitura*,
  *inclinado à alta* ou *inclinado ao corte*, então a coluna "em manutenção" do placar é
  estruturalmente inalcançável. Uma moeda com as duas dimensões rotuladas MANUTENÇÃO pode sair
  "inclinado ao corte" com intensidade baixa.
- **O voto do comitê está no calendário e é jogado fora**: "BoE MPC Vote Rate Hike / Unchanged /
  Cut" saiu 3/6/0 contra 2/7/0 na reunião anterior — número publicado pelo banco, não contagem de
  palavra — e não tem família mapeada, logo pesa zero. Enquanto isso o GBP sai sem leitura.

---

*Quem discorda de um peso, de um limiar ou de uma faixa deste documento está discordando de um
julgamento declarado, não de uma medição — e é para isso que eles estão escritos aqui.*
