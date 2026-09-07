# LÁPIDES — agente `advogado`

Este arquivo tem dois papéis. É o **catálogo de caça** do advogado do diabo — cada lápide
aqui é um erro que a casa **já cometeu e já pagou**, e que os agentes da camada 2 estão em
posição de cometer de novo — e é o registro dos erros **dele próprio**, na seção 3.

Refutação é ativo. Lápide tem número e data ao lado, senão é folclore.

---

## 1. OS QUATRO ERROS DE ORIGEM — o que o dono mandou escrever primeiro

### ⚰️ L1 · O percentil sem a janela declarada
**O que aconteceu.** Em 31/ago/2026 o painel disse que o AUDCHF estava no **percentil 98** e
o GBPNZD no **97**. Corrigido o look-ahead do cálculo, eram **85 e 61** — o aviso de "preço
esticado" no GBPNZD estava errado, e foi um aviso que saiu para o dono. Dois dias depois o
gêmeo, do outro lado da mesa: o AUDCAD a **0,99672** foi lido como máxima histórica quando
era a máxima de **5 anos** — o topo verdadeiro é **1,07738**, de fev/2012, **8% acima**. No
AUDCHF o mesmo erro já tinha sido cometido antes: o EURJPY foi chamado de máxima histórica
quando o topo era **187,720**, de 17/abr, e a janela móvel era de **252 dias**.
**A lei que nasceu:** *percentil só existe com a JANELA declarada ao lado.*
**O que eu procuro:** todo percentil, "máxima", "mínima", "extremo", "esticado", "no topo
da faixa" sem a janela grudada no número. E janela declarada que não corresponde ao campo
que a camada 1 mediu.
**Rótulo:** `numero fantasma` (gravidade alta) — ou `fonte fraca`, se a janela existe mas
vem de fonte diferente da do número.

### ⚰️ L2 · O filtro que reduzia o resultado em todas as células
**O que aconteceu.** Duas vezes, com desenhos diferentes e o mesmo veredito.
(a) O **DXY como filtro do BO**, testado nas 88 operações manuais de ouro (+81,26R, 67% de
acerto): **as seis células reduziram o R total**, e a melhor custava **−32,95R**. As duas
quase-significantes se **contradiziam** entre si (5 min concordava, 30 min discordava), e
seis comparações empurram o corte de significância para p99,2.
(b) O **AEGH Teste 1**, o FUND como filtro de entrada técnica: **0 de 9 células** acima do
p95 do sorteio pareado. No T1 h=60 o acumulado do CONCORDA era −170 contra −849 do
sem-filtro, o que parecia corte de prejuízo de 5×; mas o CONCORDA tinha **um terço** das
operações, e mil sorteios aleatórios com o mesmo n, estratificados por ano × par, faziam
igual. **O que parecia seleção era redução de exposição.**
**A lei que nasceu:** *todo filtro que corta amostra exige controle aleatório pareado com o
mesmo n.*
**O que eu procuro:** qualquer agente escrevendo que uma leitura "seleciona", "filtra",
"melhora", "aumenta a qualidade" ou "reduz o ruído" sem controle pareado. E — o meu próprio
caso — **o veto**: vetar tese é filtrar amostra. É por isso que eu não tenho veto (D4).
**Rótulo:** `contradiz lapide` (gravidade alta).

### ⚰️ L3 · O "n" inflado da auditoria
**O que aconteceu.** Em 05/set/2026 o painel exibia **"38 discursos" do AUD** quando
`data/bc_discursos.json` tem **zero** falas do RBA (o site do banco bloqueia robô). Os 38
eram manchetes do Google News — uma delas do **realestate.com.au** — contadas como discurso
de política monetária. No BoC, *"Unveiling of Vertical $20 Bank Note"* entrava como fala.
O dono resumiu a lição na nota que deu ao painel: confiabilidade operacional **5 de 10**.
**A lei que nasceu:** *um número com cara de precisão que não vem de fonte auditável é pior
do que nenhum número.* E a hierarquia de falas: discurso oficial e comunicado votam cheio;
imprensa reproduzindo dirigente nomeado vale 0,4 e é deduplicada; manchete e artigo de
opinião valem **zero**.
**O que eu procuro:** todo `n` citado — quantidade de falas, de notícias, de divulgações —
sem o campo da camada 1 que o produziu; contagem que mistura fonte primária com agregador;
notícia republicada em vários sites contada como vários eventos; item de calendário
institucional (inauguração, cerimônia, homenagem) contado como fala de política monetária.
**Rótulo:** `fonte fraca` ou `numero fantasma`, conforme o caso (gravidade alta).

### ⚰️ L4 · A estatística bonita que não vira motor
**O que aconteceu.** Três vezes, com números excelentes e resultado nenhum.
(a) O **gap fecha 71%** das vezes — e perde dinheiro.
(b) O **PEAD**, com 147.776 eventos ponto-no-tempo e deslistadas incluídas: a **calibração
passou** (+6,04%/ano contra ~7% esperado) e a **estratégia morreu** (2023-26: −0,78%
líquido). Só a perna comprada sobrevive.
(c) O **FUND v0.1**: quinze pré-registros, **quinze nulos**. O juro manda no preço em 120
dias (+0,43) e **não antecipa** em 1 a 20 dias. O "+0,107 em 1 dia" que parecia sobrar era
**artefato de relógio** — o BCE fixa às 14:15 CET, o yield fechava depois; com um dia de
gap, sumia.
**A lei que nasceu (lei 8 do método):** *estatística bonita ≠ motor. Sempre simular o trade
completo.*
**O que eu procuro:** coerência sendo apresentada como utilidade. Um agente que escreve que
uma divergência é "grande", "clara" ou "forte" e daí conclui que ela **serve para alguma
coisa**. Concordância entre agentes apresentada como confirmação. Qualquer frase que
transforme uma medida em expectativa de resultado.
**Rótulo:** `contradiz lapide` (gravidade alta) — e, se a frase virou recomendação,
gravidade alta com o texto da CVM citado em `limites`.

---

## 2. AS OUTRAS LÁPIDES DA CASA — o resto do catálogo

### ⚰️ L5 · Contagem de palavra não lê negação, condição nem tempo verbal
Waller disse que apoiaria **manter** e o painel marcou **hawkish**, porque *"holding the
target"* estava na lista de termos de alta. A dimensão de fala parou de votar em 05/set; o
teto por moeda caiu de 0,75 para 0,50. Existe um classificador por regra
(`leitor_falas.py`) que acerta os três casos do dono — Waller = manutenção, Barr = alta
condicional, Warsh = indeterminado — e **mesmo ele não vota**, porque nunca foi medido
contra rótulo humano.
**O que eu procuro:** um veredito de fala contando como evidência; uma fala condicional
lida como firme; uma negação lida ao contrário; a dimensão de fala ou de geopolítica
entrando na conclusão de qualquer agente. **Rótulo:** `buraco tratado como neutro`.

### ⚰️ L6 · Silêncio não é voto; parte sem dado baixa o denominador
A régua da qualidade de evidência é explícita: a parte sem dado sai `null` e **não entra na
média** — nunca conta como zero. A dimensão de confiabilidade da fala saiu `null` para as
oito moedas quando a fala parou de votar, em vez de valer 0 ou 100.
**O que eu procuro:** `sem_leitura` virando `MANTEM`; `qualidade: "sem fonte"` virando
`manutencao`; `p_*` nulo aparecendo como 0; agente ausente virando concordância.
**Rótulo:** `buraco tratado como neutro` (gravidade alta).

### ⚰️ L7 · Divergência não é convicção; e "score" não existe na tela
São três números distintos e **nunca somados**: (a) divergência, a diferença econômica;
(b) qualidade da evidência, que no par vale o **elo fraco**; (c) convicção histórica, que é
`null` até haver backtest. Transformar divergência em "90% de convicção" está proibido por
escrito. E a palavra **"score"** — e o número dele — não aparecem em lugar nenhum da
interface, nem em detalhe, nem em tooltip.
**O que eu procuro:** probabilidade de acerto inventada; convicção com número; a palavra
"score" em qualquer saída de agente. **Rótulo:** `contradiz lapide`.

### ⚰️ L8 · Uma única divulgação não pode dominar a leitura
O CAD com emprego a z −7,86 e apenas **três** divulgações no ciclo. Daí a winsorização por
item e o alerta quando o maior item passa de 50% da dimensão. E o efeito colateral medido:
no USD, cortar cinco itens **deslocou a soma em −7,96** (de −1,19 para −9,15) e **mudou a
direção** de MANTEM para CORTA — winsorizar uma **soma** desloca o total para o lado
contrário ao do item cortado, não amortece.
**O que eu procuro:** conclusão apoiada num item só; e leitura cuja direção só existe
depois do teto, sem que isso esteja declarado. **Rótulo:** `fonte fraca`.

### ⚰️ L9 · Par não é ativo: são duas moedas, e uma delas dá o motivo
Lei do dono, 02/set. Medido: o AUDJPY de 2021-22 foi **88% iene** (o AUD era a sexta mais
fraca de oito); em 02/set o EURJPY foi **90% iene** e o GBPNZD **82% kiwi**. Consequência:
pares que compartilham perna são a **mesma aposta** — dois deles não diversificam, dobram.
**O que eu procuro:** agente lendo par sem dizer qual perna dá o motivo; e dois pares com
perna comum apresentados como duas evidências. **Rótulo:** `contradicao entre agentes` ou
`fonte fraca`.

### ⚰️ L10 · Artefato de relógio
Além do "+0,107 em 1 dia" da L4: as horas do dono são **BRT**, a Dukascopy é **UTC (+3h)**,
e a R8 tinha horário fixo que só valia no horário de verão americano — **52 de 207**
operações estavam do lado errado. E `projection.outcome` do calendário é o FUND de **D+2**,
não de D nem de D+1.
**O que eu procuro:** dois arquivos comparados sem os dois `gerado_em` declarados; conclusão
que depende de ordem temporal sem fuso escrito; defasagem citada sem teste de gap.
**Rótulo:** `numero fantasma` (gravidade média) ou `buraco tratado como neutro`.

### ⚰️ L11 · Sinal contíguo exige nulo de BLOCO
Nasceu no AUDCHF: quando o sinal é contíguo no tempo, o sorteio aleatório ponto a ponto
subestima a variância, e o achado passa por engano.
**O que eu procuro:** afirmação de significância — de qualquer agente, sobre qualquer coisa
— sem o desenho do nulo declarado. **Rótulo:** `contradiz lapide`.

### ⚰️ L12 · O alcance declarado
Do AEGH: *"vale para ESTA versão do FUND, ESTES setups, ESTA amostra, ESTAS regras e ESTE
modelo de custo. Não demonstra impossibilidade de contribuição do fundamento em qualquer
estratégia."* E a lei 10 do método: **nunca portar para outro ativo ou janela sem
re-julgar** (doze tribunais, dez reprovações no Dia 27).
**O que eu procuro:** conclusão sobre uma moeda sendo estendida a outra; régua calibrada num
banco central aplicada a outro; "isto vale em geral".
**Rótulo:** `contradiz lapide`.

---

## 3. AS MINHAS PRÓPRIAS — objeções que eu levantei e que não procediam

*(vazio — o agente ainda não rodou.)*

Regra: uma objeção infundada é um erro **meu**, e entra aqui com data, a objeção original e
por que ela não procedia. Um advogado do diabo que grita em toda rodada é ruído, e o efeito
prático do ruído é o mesmo de não existir: ninguém lê. Só a revisão escreve nesta seção —
uma rodada não escreve a própria lápide.
