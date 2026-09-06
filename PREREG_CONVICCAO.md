# PRÉ-REGISTRO — a calibração da CONVICÇÃO HISTÓRICA

**Escrito e congelado em 2026-09-06 (domingo).**
**Amostra existente neste instante: 2 dias de snapshot (05 e 06/set), ZERO par-eventos fechados.**

Este documento é escrito hoje exatamente porque hoje não há resultado nenhum para olhar. Um
pré-registro escrito depois do primeiro número não é pré-registro, é justificativa. A partir da
assinatura abaixo, nada aqui muda: nem a métrica, nem o limiar, nem a referência, nem a data da
leitura. O que não estiver escrito aqui **não conta** (lei do dono, e).

---

## 0. A pergunta, em uma frase

O painel diz, para cada par, uma direção (COMPRA/VENDA), uma divergência (0-100) e uma
qualidade de evidência (0-100). A pergunta é uma só:

> **Uma leitura direcional do painel, tomada num instante e medida até o próximo evento
> invalidante daquele par, acerta o lado mais vezes do que uma direção sorteada nas mesmas
> janelas e nos mesmos pares?**

Enquanto essa pergunta não for respondida com amostra declarada, o campo `conviccao_historica`
continua `null` com a nota *"ainda não calibrada"*. Ele **nunca** é derivado da divergência, nem
da qualidade da evidência, nem de palpite (METODO_SENTIMENTO §1 e §9.3).

### O que este pré-registro NÃO pergunta

- Não pergunta se dá dinheiro. Não há stop, não há alvo, não há custo, não há tamanho. É um
  teste de **direção**, não de estratégia. Aprovação aqui não autoriza operar nada.
- Não usa a coluna do operador (`bo_h4`, `zoi_m30`, `primeiro_toque`, `entrada`, `resultado_r`).
  **Isso é deliberado**: se a métrica dependesse do preenchimento manual, o preenchimento
  seletivo (lembrar de anotar o que deu certo) seria uma porta de viés que nenhum controle
  estatístico fecha. A métrica aqui é **preço puro**, cega ao operador. A coluna do operador
  serve a um pré-registro futuro e separado, sobre execução.
- Não usa yield, nem precificação de mercado, nem probabilidade implícita. Lei do dono.

---

## 1. A UNIDADE DE OBSERVAÇÃO — o par-evento

**Uma observação = um par × um ciclo de evento invalidante.**

### 1.1 Quando a observação ABRE

A observação abre na **primeira linha do snapshot daquele par, dentro daquele ciclo, com
`direcao` diferente de `SEM_TESE`**.

- "Ciclo" de um par = o intervalo entre dois eventos invalidantes consecutivos daquele par. O
  evento invalidante é o que já vem gravado na própria linha, em
  `proximo_evento_invalidante` — a decisão de juro mais próxima entre as duas pernas.
- Se a primeira linha do ciclo estiver `SEM_TESE` e o par ganhar tese depois, a observação abre
  na linha em que a tese aparece. A janela encurta na mesma medida. Isso está decidido **antes**
  de ver qualquer dado, e vale nos dois sentidos.
- Se o par nunca tiver tese dentro do ciclo, **não há observação**. Não entra nem como acerto
  nem como erro.

### 1.2 O que NÃO abre observação nova

- Segunda, terceira, décima linha do mesmo par dentro do mesmo ciclo: **não abrem nada**. A
  leitura vale a de abertura. Isso impede que um par com muitas gravações domine a amostra.
- **Virada de direção no meio do ciclo: não abre e não fecha nada.** A observação continua com a
  direção de abertura até o evento. A virada fica registrada como descritiva declarada
  (`virou_no_meio`), sem teste associado. Deixar a virada abrir observação nova seria deixar o
  painel escolher o ponto de partida depois de ver o preço.

### 1.3 Quando a observação FECHA

No **último fechamento diário estritamente anterior à data do evento invalidante declarado na
linha de abertura**. O evento em si fica **fora** da janela: mede-se a caminhada até o evento,
nunca a reação a ele.

Regras de contorno, decididas agora:

| Situação | Regra |
|---|---|
| O banco central **adiou** a decisão | A janela permanece a **declarada na linha**. A linha é imutável; a leitura foi feita contra aquele relógio. |
| O banco central **antecipou** (reunião extraordinária) | Fecha na data efetiva, e a observação sai marcada `evento_antecipado: true`. Entra na análise principal. |
| Janela com **menos de 3 pregões** entre P0 e P1 | **Descartada**, marcada `janela_curta`. Critério mecânico, cego à direção, aplicado igual no sorteio. |
| Janela com **mais de 45 dias corridos** | Truncada em 45 dias corridos, marcada `truncada`. Acima disso o "próximo evento" já não é a restrição que manda. O truncamento é aplicado **idêntico** no sorteio. |
| `proximo_evento_invalidante` vindo `null` na linha | Observação **não abre**. Sem relógio de fim declarado não há par-evento. |

---

## 2. A MÉTRICA — "andou a favor", sem ambiguidade

Binária, uma por observação: **andou a favor da leitura antes do próximo evento invalidante —
sim ou não.**

### 2.1 A fonte de preço, congelada hoje

**Yahoo Finance, série diária (`interval=1d`), símbolo `<PAR>=X`** (ex.: `EURUSD=X`,
`AUDCAD=X`), lida por `urllib` com User-Agent de navegador, no padrão de `fomc_precificacao.py`.
Carimbo de tempo: o campo `timestamp` do próprio JSON, em UTC.

**Por que essa e não outra — medido hoje, 06/set, não suposto:**

- **MT5 (FTMO-Server4) foi TESTADO e REPROVADO como fonte primária.** `mt5.initialize()`
  retorna `True` e o terminal diz `connected=True`, mas a última barra M1 de EURUSD é de
  **2025-12-22** — nove meses atrás. `copy_rates_from` para 05/set/2026 devolve as barras de
  dezembro de 2025 **sem erro nenhum**. Uma fonte que devolve preço errado calada é pior que
  uma fonte que falha.
- **Yahoo intradiário de 1 minuto não serve**: só entrega os últimos ~7 dias (medido: 2.878
  barras, de 02/set a 04/set). Na data da leitura, em dezembro, o minuto de setembro já não
  existirá. O diário existe para sempre. **A métrica tem de ser reconstruível na
  data da leitura, senão o pré-registro é uma promessa vazia.**

**Fonte única para a amostra inteira.** Nada de misturar fontes entre observações. Se na data da
leitura o Yahoo estiver fora do ar ou tiver mudado de formato, a regra é **esperar**, não trocar.

**Conferência independente, sem poder de troca:** na data da leitura, 20 observações sorteadas
têm P0 e P1 conferidos contra a fonte que estiver viva (MT5, se o terminal tiver a história). A
divergência mediana é **reportada** no veredito. Ela **não** autoriza trocar de fonte nem
descartar observação — só descreve o erro de medida.

### 2.2 Os dois preços

- **P0** = o **primeiro fechamento diário com carimbo estritamente POSTERIOR a `gravado_em`** da
  linha de abertura.
  *Por que o de depois e não o da véspera:* o movimento entre o fechamento anterior e o instante
  da gravação já era conhecido quando a leitura foi feita. Contá-lo seria dar de presente ao
  painel um pedaço de passado. Começar no primeiro fechamento posterior joga fora até um dia de
  movimento — é conservador contra a hipótese, que é o lado certo de errar.
- **P1** = o **último fechamento diário estritamente anterior à data do evento invalidante**
  (§1.3).

### 2.3 O retorno e o sinal

```
r = ln(P1 / P0)
r_favor = (+1 se direcao == "COMPRA", −1 se direcao == "VENDA") × r
```
Log-retorno porque é simétrico entre comprado e vendido: uma alta de 1% e uma queda de 1% têm o
mesmo tamanho. Com retorno simples, VENDA teria escala diferente de COMPRA e a moeda do sorteio
não seria justa.

### 2.4 O limiar de ruído — PROVISÓRIO

Movimento pequeno não é acerto, é vibração. O limiar tem de escalar com a volatilidade do par e
com o tamanho da janela — nada em pontos absolutos e nada em dólar (lei-mãe do método HCI).

```
ATR14 = média verdadeira de 14 pregões (High/Low/Close diários do Yahoo)
        nas 14 barras que terminam na barra de P0
L = 0,25 × (ATR14 / P0) × raiz(N)      [em log-retorno]
N = número de pregões entre P0 e P1
```

O fator **0,25** e o **raiz(N)** são **PROVISÓRIOS** e ficam rotulados como tal no código e no
veredito. Justificativa de ordem de grandeza, declarada agora para não ser inventada depois: o
movimento típico acumulado em N pregões é da ordem de `ATR × raiz(N)`; exigir 25% disso separa
"andou" de "tremeu" sem exigir tendência forte.

**O limiar está CONGELADO.** Se o resultado sair no fio, o limiar não muda. Reotimizar 0,25
depois de ver o número é garimpo, e é o que este documento existe para impedir.

### 2.5 O desfecho binário

```
ACERTO (1)  se  r_favor >  +L
ERRO   (0)  se  r_favor <  −L
NEUTRO (0)  se  |r_favor| ≤ L
```

**Neutro conta como ZERO, e não é descartado.** Descartar neutro mudaria o n e abriria a porta
para "a amostra que sobrou". Como o sorteio de referência usa **as mesmas janelas, os mesmos
pares e o mesmo L**, ele sofre o mesmo desconto — a comparação continua justa. A repartição
tríplice (acerto / erro / neutro) é reportada à parte, como descritiva, sem teste.

---

## 3. A REFERÊNCIA A BATER — o sorteio pareado, com nulo de BLOCO

Percentual de acerto sozinho não diz nada: 15 pares com tese hoje saem de 6 moedas, e 7 deles
morrem na mesma reunião do BCE. Eles não são 15 apostas, são poucas. O sorteio existe para medir
quanto do acerto é **leitura** e quanto é **deriva de moeda mais geometria**.

### 3.1 O que é pareado

O sorteio **não** re-sorteia par, nem data, nem janela, nem limiar. Ele mantém a amostra inteira
e troca **só a direção**. Por construção, a distribuição de pares e de janelas do sorteio é
**idêntica** à real, com o mesmo n.

### 3.2 O BLOCO — porque o sinal é contíguo (lei do dono, b)

**BLOCO = (semana ISO em que a janela fecha) × (moeda da perna dominante da linha de abertura).**

Todas as observações de um mesmo bloco andam juntas: são a mesma perna, na mesma semana,
recebendo o mesmo choque. Sorteá-las independentemente inventaria informação que não existe e
estreitaria a distribuição nula — o erro clássico que faz um resultado medíocre parecer
significante.

**No sorteio, cada BLOCO recebe UMA direção sorteada, aplicada a todas as suas observações.**

**Por que semana × moeda, e não data do evento × moeda** — medido hoje, sobre os 28 par-eventos
já abertos:

| Definição de bloco | Blocos | Maior bloco | Veredito |
|---|---|---|---|
| data do evento × moeda | 23 | 5 | quase um bloco por observação — **não é nulo de bloco, é nulo disfarçado** |
| **semana ISO × moeda** | **15** | 5 | **adotado** — 1,87 observação por bloco |
| só a moeda | 7 | 7 | severo demais: trata NZD de setembro e NZD de novembro como o mesmo choque |

A concentração é real e visível: cinco dos 28 par-eventos são pares com perna dominante EUR
morrendo todos na semana do BCE. Nulo por observação, aqui, seria fraude aritmética.

### 3.3 Os dois nulos — a regra tem de bater os DOIS

- **NULO A — moeda por bloco.** Cada bloco recebe COMPRA ou VENDA por Bernoulli(0,5).
  **10.000 sorteios.** Responde: "a leitura bate cara-ou-coroa?"
- **NULO B — permutação dos rótulos entre blocos.** As direções **reais** de abertura de cada
  bloco são embaralhadas entre os blocos, preservando a proporção COMPRA/VENDA observada.
  **10.000 permutações.** Responde: "a leitura bate uma leitura com a mesma inclinação
  direcional, só que colada no bloco errado?" É este que mata o artefato "o painel estava
  majoritariamente comprado e o mercado subiu".

Distribuições nulas com **percentil declarado ao lado da janela** (lei do dono, c): p50, p95 e
p99 sobre os 10.000 sorteios de cada nulo, reportados por extenso.

### 3.4 O haircut (lei do dono, d)

```
excesso_bruto     = acerto_real − p50 do nulo
excesso_reportado = 0,50 × excesso_bruto
```

O número que vai para a tela, se houver, é o **excesso reportado**, nunca o bruto. O haircut é
aplicado ao excesso, não à taxa de acerto — cortar a taxa pela metade não teria significado.

### 3.5 A robustez do bloco — e o que ela pode fazer com o veredito

O corte "semana" é uma escolha, e escolha declarada tem de ser testada contra a vizinha. Na data
da leitura, os dois nulos são rodados **também** com **BLOCO = só a moeda da perna dominante**
(a definição severa da tabela acima), e o resultado dos dois cortes vai lado a lado no veredito.

> **Se o veredito mudar entre as duas definições de bloco, o rótulo é INCONCLUSIVO — nunca
> APROVADA.** Aprovar pelo corte que dá certo é escolher o nulo depois de ver o resultado.

---

## 4. O n MÍNIMO — 60 par-eventos, e o que 60 NÃO enxerga

### 4.1 A condição de leitura

**n ≥ 60 par-eventos fechados e válidos, E n_blocos ≥ 25.**

O segundo critério não é decoração. Sessenta observações em oito blocos é um teste de oito
observações com maquiagem. Como o nulo é de bloco, o bloco é a unidade de informação, e o poder
sai do número de blocos, não do número de linhas.

O 25 vem da densidade medida hoje: 28 par-eventos em 15 blocos = **1,87 observação por bloco**.
Sessenta observações nessa densidade dão ~32 blocos. Exigir 25 é aceitar até 30% de piora na
dispersão antes de recusar a leitura.

### 4.2 O poder — calculado hoje, com os números na mesa

Teste binomial unilateral contra p=0,50, α=0,05:

| n efetivo | corte crítico | poder se a verdade for 55% | 60% | 65% | 70% |
|---|---|---|---|---|---|
| **60** | 37/60 = **61,7%** | 0,18 | 0,45 | **0,75** | 0,94 |
| **32** (≈ blocos, densidade medida 1,87 obs/bloco) | 22/32 = **68,8%** | 0,08 | 0,20 | **0,40** | 0,64 |
| 20 | 15/20 = 75,0% | 0,06 | 0,13 | 0,25 | 0,42 |
| 120 | 70/120 = 58,3% | 0,26 | 0,68 | 0,95 | 1,00 |

**Leitura honesta, escrita antes de qualquer resultado:**

- 60 par-eventos é o mínimo para o teste **existir**, não para ele ser bom. Ele enxerga com
  poder decente (≥ 0,75) apenas um efeito **grande**: acerto verdadeiro de ~65%, isto é **+15
  pontos percentuais** sobre a moeda.
- Um efeito real de 55% — que já seria útil — é **invisível** com n=60 (poder 0,18). Portanto
  **"não passou" com n=60 significa "não é grande", nunca "não existe"**. Isso vai escrito no
  veredito, com o poder ao lado, como manda o AEGH v3.
- Com o nulo de bloco e ~32 blocos, o corte sobe para **68,8%** e o poder em 65% cai de 0,75
  para **0,40**. É o preço de contar a dependência em vez de ignorá-la — e é a razão de o
  veredito de reprovação vir sempre com o poder ao lado, nunca sozinho.

### 4.3 Consequência para o status

Aprovação nesta primeira leitura promove a regra a **HIPÓTESE-FORTE**, jamais a COFRE. O campo
do painel, se acender, acende com **o número, o n, os blocos, o intervalo de confiança e a
palavra PROVISÓRIO** ao lado — nunca um número sozinho.

Um **segundo lote de 60 par-eventos**, colhido depois da leitura e sem tocar em nada, é o cego
que decide de verdade. Está declarado desde já para não parecer conveniência depois.

---

## 5. A DATA DA LEITURA — 2026-12-21, e nada antes

### 5.1 A aritmética, mostrada

Contada pelo `le_prereg_conviccao.py` sobre os dois dias que existem, não estimada no olho:

- **28 par-eventos já abertos**, em **15 blocos**, com relógio de fim entre 10/set e 28/out
  (BCE 7, Fed 6, BoE 5, BoJ 4, SNB 3, RBA 2, RBNZ 1). São os 28 pares do painel, e não os 15
  "com tese agora", porque a regra de §1.1 abre a observação na **primeira** linha com tese
  dentro do ciclo — ao longo de dois dias, todos os 28 tiveram tese em algum instante.
- Um par fecha um ciclo a cada decisão de **qualquer uma das suas duas pernas**. Os oito bancos
  reúnem entre 4 e 11 vezes por ano (SNB 4, Fed/BCE/BoE/BoJ/BoC 8, RBNZ 7, RBA 11) — cerca de
  **16 eventos por ano por par**, ~0,31 por semana por par.

```
28 pares × 0,31 evento/semana            = 8,6 par-eventos/semana no papel
menos ~25% descartados por janela curta  ≈ 6,5 par-eventos/semana
```

- A borda inferior honesta é bem mais baixa: em ciclos onde a tese some, o par não abre nada, e
  o primeiro ciclo é sempre o mais cheio (todos os pares entram de uma vez). **Banda declarada:
  4 a 6,5 par-eventos por semana.**

```
60 par-eventos ÷ 4 por semana (borda conservadora) = 15 semanas
2026-09-06 + 105 dias = 2026-12-20 (domingo)
```

### 5.2 A data

> ## 📅 **DATA DA LEITURA: segunda-feira, 2026-12-21.**

**Antes dessa data ninguém calcula taxa de acerto nenhuma.** Nem espiada, nem "só para ver se
está indo bem", nem gráfico de acompanhamento. O script `le_prereg_conviccao.py` se recusa a
calcular e diz por quê.

### 5.3 Se o n não estiver fechado na data

A regra é **ESPERAR**. Nunca olhar antes, e nunca baixar a barra.

- Se em 2026-12-21 houver n < 60 ou blocos < 25, a leitura é adiada em blocos de **14 dias**,
  reconferidos às segundas, até as duas condições fecharem.
- Cada adiamento é anotado em §11, com a data e o n do dia. O histórico de adiamentos vai no
  veredito: adiar seis vezes é informação sobre o ritmo do projeto.
- **Um n maior que 60 na data é bem-vindo e entra inteiro.** Não se corta amostra para chegar em
  60 exatos, e não se para de colher antes da data por ter chegado a 60.

---

## 6. OS CORTES — o que aprova e o que reprova

### 6.1 APROVADA — os seis, todos, sem negociação

1. **n ≥ 60 par-eventos e n_blocos ≥ 25.** Senão não há leitura, há espera.
2. **Acerto real acima do p95 do NULO A** (moeda por bloco, 10.000 sorteios).
3. **Acerto real acima do p95 do NULO B** (permutação de rótulos entre blocos, 10.000).
4. **Sobrevive ao haircut:** `excesso_reportado = 0,5 × (real − p50 do nulo) > 0` **e** o
   limite inferior do IC 95% do acerto real — bootstrap **por BLOCO**, 10.000 reamostragens —
   fica acima do p50 do nulo.
5. **Coerência temporal de sinal:** partindo a amostra em duas metades cronológicas de blocos, o
   excesso tem **o mesmo sinal** nas duas. Não se exige significância em cada metade (não há
   poder para isso); exige-se que não seja uma metade carregando a outra no colo.
6. **Robustez do bloco (§3.5):** o veredito é o mesmo com BLOCO = semana × moeda e com
   BLOCO = só a moeda. Se os dois cortes discordarem, o rótulo é **INCONCLUSIVO**.

### 6.2 REPROVADA — qualquer um destes, sozinho, reprova

- Excesso bruto ≤ 0.
- Fica abaixo do p95 em **qualquer um** dos dois nulos. Bater um só não aprova.
- **Depende de um episódio:** retirando o **bloco de maior contribuição**, o excesso cai a ≤ 0.
  Este critério tem nome e sobrenome na casa — o EURJPY tirava 71-85% do resultado histórico de
  três episódios. Um resultado que mora num bloco é um resultado que não existe.
- Excesso troca de sinal entre as duas metades cronológicas.
- A amostra foi tocada: linha do snapshot editada, observação incluída ou excluída fora das
  regras de §1, ou fonte de preço trocada no meio.

### 6.3 O caso que já nos enganou duas vezes: "aprovada só num subconjunto"

> **Se a regra geral reprova e uma célula secundária passa, o veredito é REPROVADA. Ponto.**

Foi assim que morreram o **AEGH Teste 1** (0 de 9 células acima do p95 do sorteio pareado; o que
parecia seleção era redução de exposição) e o **filtro DXY** (as seis células reduziam o R total,
e as duas quase-significantes se contradiziam entre si).

Regras que valem para qualquer célula que "passe" com a regra geral reprovada:

- A célula **não** acende o campo do painel. Nem com asterisco, nem com "parcial", nem com
  "promissor". O campo continua `null` com "ainda não calibrada".
- A célula vira, no máximo, **uma hipótese nomeada para um pré-registro NOVO**, com amostra
  **nova**, colhida depois. Amostra que já foi olhada está gasta (Fase 3.4 do método HCI).
- O veredito escreve quantas células foram olhadas e qual o corte corrigido. Uma célula em oito
  passando ao acaso é o resultado esperado, não uma descoberta.
- **Simetria obrigatória:** se a regra geral **aprova** e uma célula secundária vai mal, isso
  também não reprova a regra geral. A regra geral manda nos dois sentidos — senão o subconjunto
  é usado só quando convém.

---

## 7. AS ANÁLISES SECUNDÁRIAS — declaradas agora, todas as que existem

Nenhuma delas aprova ou reprova coisa alguma (§6.3). Existem para gerar hipótese para o
pré-registro seguinte, e são declaradas antes para que ninguém possa inventar a nona depois.

| # | Família | Células | Corte |
|---|---|---|---|
| 1-3 | **Faixa de divergência** | 15-24 (observação) · 25-39 (moderada) · 40+ (forte) | faixas provisórias do dono de 05/set, gravadas em `regua_em_vigor.faixas_provisorias` |
| 4-6 | **Qualidade da evidência** | tercil baixo · médio · alto | os cortes dos tercis são calculados **na data da leitura, sobre a amostra**, e reportados — são descritivos, não escolhidos |
| 7-8 | **Perna dominante** | `share_pct` ≥ 70 · `share_pct` < 70 | corte 70 fixado **agora**, PROVISÓRIO |

**São 8 comparações. Total declarado e fechado.**

- Correção para comparação múltipla: **Holm-Bonferroni sobre as 8**, com os p vindos do NULO A
  aplicado dentro da célula (mesmo procedimento de bloco, 10.000 sorteios por célula).
- Célula com **n < 20 par-eventos ou n_blocos < 8** é reportada como **INCONCLUSIVA**, com o
  poder ao lado — **nunca** como "sem efeito". Ausência de diferença não é prova de equivalência.
- A faixa 0-14 (`SEM_TESE`) não é célula: por construção não gera observação.
- Descritivas sem teste, reportadas para leitura humana: repartição acerto/erro/neutro; quantas
  observações tinham `virou_no_meio`; quantas foram descartadas por janela curta; quantas
  truncadas em 45 dias; distribuição de observações por bloco; divergência entre Yahoo e a fonte
  de conferência nas 20 sorteadas.

---

## 8. O QUE NÃO SERÁ FEITO — a lista fechada

1. **Nada de backfill.** Não se reconstrói leitura de dia nenhum anterior a 05/set/2026. Não
   existe consenso point-in-time para trás; as manchetes têm janela de 72 h e não há arquivo; e
   as constantes de hoje aplicadas ao passado contaminam — está auditado em METODO_SENTIMENTO §7,
   inclusive o caso de seis dos oito bancos terem decisão posterior a um corte de 01/nov/2025.
   **A amostra começa em 05/set/2026 e cresce só para a frente.**
2. **Nada de reotimizar o limiar.** O 0,25 e o raiz(N) de §2.4 estão congelados. Nem "testamos
   também 0,20", nem "com 0,30 fica melhor". Um grid rodado depois de ver o resultado é garimpo,
   e o resultado do garimpo é sempre positivo.
3. **Nada de trocar a métrica.** Nem por retorno médio, nem por MFE, nem por "andou a favor em
   algum momento da janela", nem por resultado em R. Se a binária reprovar, quem quiser testar
   outra métrica escreve **outro** pré-registro e colhe **outra** amostra.
4. **Nada de mudar a janela.** Não se troca "até o próximo evento" por 5, 10 ou 20 dias depois
   de ver o número.
5. **Nada de trocar a fonte de preço** no meio da amostra nem na hora do resultado (§2.1).
6. **Nada de mexer nas faixas** de divergência para melhorar o resultado. Elas serão
   recalibradas um dia — por um pré-registro próprio, com amostra própria.
7. **Nada de incluir ou excluir par** fora de §1. Todos os 28 do painel são elegíveis; entra
   quem tiver tese, sai quem não tiver, pela regra mecânica.
8. **Nada de descartar neutros**, nem observações "estranhas", nem semanas de feriado.
9. **Nada de editar snapshot.** O diretório é append-only. Correção é linha nova com carimbo
   novo. Reescrever linha ali é apagar o backtest (LEIA-ME do diretório).
10. **Nada de usar a coluna do operador** nesta leitura (§0).
11. **Nada de olhar antes de 2026-12-21** (§5.2).
12. **Nada de resultado sem o n e os blocos ao lado.** Percentil sem janela declarada não existe
    (lei do dono, c).

---

## 9. O ARTEFATO DA LEITURA

Na data da leitura, `le_prereg_conviccao.py` grava **uma vez** `data/prereg_conviccao_leitura.json`
com: cada observação (par, gravado_em, direção, divergência, qualidade, perna dominante, bloco,
P0, P1, datas, N, ATR14, L, r_favor, desfecho), as duas distribuições nulas resumidas
(p50/p95/p99), o IC de bootstrap por bloco, as 8 células secundárias com Holm, e o veredito.

**Esse arquivo é congelado.** Se uma segunda execução devolver números diferentes (o Yahoo revisa
fechamento de vez em quando), a divergência é **reportada**, nunca sobrescrita — mesma lei do
snapshot.

---

## 10. RISCOS CONHECIDOS — escritos antes, não depois

- **O ritmo pode ser menor que 4/semana** e a data escorregar. O primeiro ciclo é o mais cheio
  (28 par-eventos abriram de uma vez) e pode estar inflando a projeção. A regra é esperar (§5.3).
- **A régua mudou em 05/set** (texto e geopolítica pararam de votar; teto do par 1,50 → 1,00).
  Se ela mudar de novo no meio da coleta, as observações antes e depois não estão na mesma
  escala. **Regra declarada agora:** mudança de régua **não invalida** a amostra — cada linha
  carrega a sua em `regua_em_vigor` — mas o veredito **tem de** reportar quantas observações
  foram colhidas sob cada régua, e a coerência temporal de §6.1.5 é a defesa contra isso.
- **A faixa "forte" (40+) pode terminar quase vazia**, como já está apontado em
  METODO_SENTIMENTO §10. Célula vazia sai INCONCLUSIVA, não "sem efeito".
- **A tese concentra em poucas moedas.** Hoje, 28 par-eventos em 15 blocos, e o maior deles tem
  5 (pares de perna EUR morrendo na semana do BCE); no corte severo são só 7 moedas. Se na
  leitura os blocos não chegarem a 25, não há leitura.
- **O painel muda de código a toda hora.** A defesa é o snapshot append-only, e só ele.

---

## 11. CONGELAMENTO E REGISTRO

**Congelado em 2026-09-06.** Alteração neste documento só por versão nova, em arquivo novo, com
o motivo escrito e este preservado intacto. Alterar em cima é o mesmo que não ter pré-registrado.

| Data | O que aconteceu | n do dia | Blocos | Quem |
|---|---|---|---|---|
| 2026-09-06 | Documento escrito e congelado. Amostra: 2 dias, 385 linhas íntegras, 28 par-eventos **abertos** em 15 blocos, **0 fechados**. | 0 | 0 | pré-registro |

**Assinaturas:** dono (Eduardo) __________ · executor __________

---

*HCI · hokiresearch.com — ferramenta de pesquisa. Não é recomendação de investimento.*
