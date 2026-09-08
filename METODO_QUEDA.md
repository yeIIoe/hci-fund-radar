# MÉTODO QUEDA — reversão à média em empresa de qualidade depois de queda excessiva

**Documento de método, escrito ANTES de qualquer resultado.**
Autor: HCI / EGH · Data de redação: **2026-09-06 (domingo)** · Estado: **congelado nesta data**
Pré-registro assinável separado: `PREREG_QUEDA.md` (mesma pasta)
Motor gerador: `ficha_queda.py` → `data/fichas_queda.json` · `data/fichas_queda.txt` · `data/equities_ledger.jsonl`

> Este documento é DADO e MÉTODO. Não é recomendação, não é sinal de entrada,
> não contém sugestão de posição, tamanho, preço-alvo ou stop, e não promete retorno.
> A decisão e a entrada são do Eduardo. O sistema nunca emite ordem.

---

## 0. O ESTADO, EM UMA TABELA (para não haver ilusão de maturidade)

| item | número real hoje |
|---|---|
| snapshots ponto-no-tempo de consenso | **4** (14/ago, 21/ago, 28/ago, 05/set) |
| deltas de revisão calculáveis | **3** |
| semanas de fichas coletadas | **1** (semana 28/ago → 04/set) |
| fichas nessa semana | **20** |
| das quais "sem lastro" (a classe candidata) | **7** |
| das quais "com lastro" | **1** |
| das quais "SEM DADO" | **12 (60%)** |
| desfechos preenchidos no ledger | **0** |
| regimes de mercado na amostra | **1** (SPY +0,11% na semana; nenhum estresse) |

Com esses números **não é possível afirmar nada** sobre se o método funciona.
O propósito deste documento é fixar as réguas ANTES de haver resultado, para que
daqui a cinco meses exista um julgamento e não uma narrativa.

---

## 1. A TESE, EM DUAS FRASES — E QUEM ESTÁ PERDENDO DINHEIRO DO OUTRO LADO

**Tese.** Quando uma empresa líquida cai muito mais do que a sua própria volatilidade
costuma produzir, e essa queda é dela (não do mercado nem do setor), parte do movimento
é liquidação forçada e não reprecificação de lucro — e essa parte tende a voltar.
**O teste que separa uma coisa da outra é o consenso de lucro:** se o consenso caiu junto,
o preço estava reprecificando um fato e não há nada a colher; se o consenso não se moveu,
a queda foi maior do que o fato pedia.

**Quem está do outro lado, perdendo dinheiro, e por quê.** Três vendedores identificáveis,
nenhum deles vendendo por opinião sobre valor:

1. **O mandato que não pode segurar.** Fundos com regra de risco (VaR, banda de tracking
   error, limite de posição por nome) vendem porque a volatilidade do nome estourou o
   orçamento de risco deles, não porque revisaram o lucro. Um salto de volatilidade força
   redução mecânica de posição.
2. **O stop e a chamada de margem.** Quem estava comprado alavancado é liquidado no pior
   momento; o preço de execução dele não tem relação com o valor da empresa.
3. **O gestor que não quer o nome no extrato do trimestre** (janela de fechamento).
   Vende o perdedor visível para não ter de explicá-lo.

Nos três casos o vendedor está indiferente ao preço — ele está pagando por liquidez
imediata. Quem compra está vendendo liquidez, e o prêmio é o que se tenta colher.

**O que este método NÃO afirma.** Não afirma que a empresa está barata, não afirma que a
notícia foi mal interpretada, e não emite juízo sobre a tese de longo prazo do negócio.
Afirma uma coisa só, estreita e mensurável: **a queda teve lastro no consenso de lucro, ou não teve.**

> ⚠️ **08/set/2026 — o balde binário ganhou uma barra de erro, e a população do pré-registro NÃO
> mudou.** O limiar de 3% continua onde estava e os três estados (`com lastro` / `sem lastro` /
> `sem dado`) continuam calculados pela mesma regra — a população primária deste pré-registro
> segue sendo `sem lastro`, com a mesma definição. Ao **lado** dela passou a sair uma
> classificação graduada com a incerteza do próprio consenso, medida em `epsHigh`/`epsLow`/`n` do
> snapshot: quando a revisão está a menos de uma incerteza da borda (−3,0% ou +3,0%), a ficha sai
> rotulada **FRONTEIRA**, porque ali o dado não separa os dois baldes. Campos novos: `lastro_grau`,
> `lastro_fronteira`, `lastro_z`, `incerteza_eps_pct`; coletor `v1.2`. Na rodada de 08/set: **2 de
> 5 fichas na faixa de fronteira** (DYN e RPRX). Quando a análise deste pré-registro for feita, o
> `lastro_fronteira` permite repetir o teste **excluindo** os casos que o dado não distingue — o
> que é um corte declarado ANTES, não depois.

**Contra-mecanismo honesto, declarado agora.** O analista revisa DEPOIS do evento. Então
"consenso parado" numa janela de uma semana pode significar apenas "o analista ainda não
mexeu". Se for isso, "sem lastro" não é um fato sobre a empresa — é um atraso do analista,
e o método é uma máquina de comprar coisas que ainda vão ser rebaixadas. Este é o modo de
morte nº 4 da seção 9, e é o mais provável de todos.

---

## 2. UNIVERSO E PISO DE LIQUIDEZ

**Universo.** Ações listadas em NASDAQ/NYSE/AMEX, não-ETF, em negociação ativa, presentes
no snapshot semanal de consenso da casa (`estimates_logger.py`, FMP `/stable/company-screener`).
No snapshot de 2026-09-05: **1.638 tickers**.

**Piso de liquidez (as três réguas, todas do logger e do `revisoes.json` já existentes):**

| régua | valor | por quê |
|---|---|---|
| preço | ≥ US$ 10 | corta penny/micro; o catálogo da casa marca isto como obrigatório para ações (spread destrói o edge) |
| volume | > 500.000 ações/dia | idem |
| valor de mercado | > US$ 2 bi | corta o nome onde 20 bps viram 60 bps e onde a decomposição setorial não tem sentido |

**Por que o piso não está em dólares de volume financeiro e sim em ações/dia:** porque é a
régua que o logger da casa já usa há 4 semanas, e trocar a régua agora quebraria a
comparabilidade da única série ponto-no-tempo que temos. Fica registrado como dívida técnica:
o piso correto seria volume financeiro (US$/dia), e a troca só pode acontecer **na abertura
de uma nova série**, nunca no meio desta.

**Nota de fricção (lei do pedágio).** O custo estimado em ações líquidas deste porte é de
10 a 30 bps por perna, ou seja 20 a 60 bps ida-e-volta. Ver seção 6 para a conta do pedágio.

---

## 3. O FUNIL, ETAPA A ETAPA — COM OS NÚMEROS REAIS DESTA SEMANA

Semana das fichas: **2026-08-28 → 2026-09-04**. Contexto: **SPY +0,11%** (semana morta,
sem estresse de mercado). Rodada de 2026-09-06 20:44.

Todas as réguas estão em **percentil ou múltiplo de desvio vivo**, nunca em porcentagem fixa.
A razão é concreta e mensurável nesta própria semana: a AON caiu **−9,09%** e a CRDO caiu
**−26,72%**; um corte fixo em −10% pegaria a CRDO e jogaria a AON fora. Mas o desvio semanal
de 52 semanas da AON é 2,97% e o da CRDO é 12,73% — em múltiplos de desvio a AON é **−3,06**
e a CRDO é **−2,10**. **A AON é o evento mais raro dos dois, e o corte fixo inverteria a ordem.**

```
ETAPA 1 — UNIVERSO
  tickers no snapshot de 2026-09-05 ....................... 1.638
  após o piso de liquidez (px>=10, vol>500k, mcap>2bi) .... 1.433
  morreram na liquidez ...................................... 205   (12,5%)

ETAPA 2 — QUEDA (a régua viva)
  com histórico suficiente (>=210 barras) ................. 1.396
  morreram por histórico curto / preço ausente ............... 37
  vetados por desdobramento/dividendo (bruto x ajustado>3pp) .. 1   (APH: -47,5% bruto vs +4,96% ajustado)

  seletividade da régua (z = queda da semana / desvio semanal de 52s):
      z <= -1,5 ......... 45 nomes  (3,2% dos 1.396)
      z <= -2,0 ......... 20 nomes  (1,4%)   <-- corte
      z <= -2,5 .......... 8 nomes  (0,6%)
      z <= -3,0 .......... 4 nomes  (0,3%)
  PASSARAM no corte z <= -2,0 ................................ 20
  morreram no z ........................................... 1.376

ETAPA 3 — IDIOSSINCRASIA (a queda é dela, não do mercado/setor)
  regressão de 248 dias contra SPY e o ETF do setor;
  exige parcela própria >= 50% e negativa ..................... 20
  morreram (queda era do mercado/setor) ....................... 0

  [ETAPA 3 nao cortou ninguem esta semana, e isso e informacao, nao sucesso:
   numa semana em que o SPY andou +0,11%, TODA queda grande e por construcao
   idiossincratica. Este filtro so mostra o que vale numa semana de estresse,
   que ainda nao aconteceu na amostra.]

ETAPA 4 — LASTRO (a pergunta central)
  com lastro (o consenso de EPS caiu junto) .................... 1   (LULU, -4,19% de EPS)
  sem lastro (preço caiu, consenso parado ou subindo) .......... 7
  SEM DADO (sem par nos snapshots / ano fiscal mudou) ......... 12   (60%)

ETAPA 5 — MOTIVO (o fato duro, para o Eduardo ler)
  identificado ................................................ 20
  não identificado ............................................. 0
```

**O funil produz 20 fichas/semana, das quais 7 são da classe candidata ("sem lastro").**
Este é o ritmo real que alimenta a conta de prazo da seção 8.

**A etapa 4 é o gargalo, e é preciso dizer o tamanho dele.** 60% das fichas ficam "SEM DADO".
A causa dominante não é falta de cobertura: é **mudança de ano fiscal entre snapshots**
(10 dos 12 casos — o consenso pula de FY2027 para FY2026 e a comparação `epsAvg` deixa de ser
entre a mesma coisa). Os outros 2 são tickers ausentes do snapshot anterior. **Isto é conserto
de engenharia, não limitação de dado** — ancorar a comparação no mesmo `fy_date` em vez de
"o FY corrente de cada snapshot" recupera a maioria. Está registrado como o item nº 1 da
dívida técnica no pré-registro.

**A classe "SEM DADO" é obrigatória e nunca será escondida.** Preencher esses 12 com a
estimativa de hoje seria look-ahead; jogá-los fora inflaria artificialmente a taxa de
"sem lastro" de 7/20 (35%) para 7/8 (88%). Os dois números vão sempre impressos lado a lado.

### As 20 fichas da semana zero (anexo de auditoria)

| # | ticker | setor | var. semana | z | z_idio | lastro | acima SMA200 | motivo (fato duro) |
|---|---|---|---|---|---|---|---|---|
| 1 | CRDO | Technology | −26,72% | −2,10 | −2,24 | sem dado | não | resultado trimestral (8-K 2.02) |
| 2 | GWRE | Technology | −21,10% | −2,44 | −2,43 | **sem lastro** (+1,2%) | **sim** | saída/entrada de executivo (8-K 5.02) |
| 3 | FICO | Technology | −19,18% | −2,58 | −2,51 | sem dado | não | sem 8-K e sem léxico reconhecido |
| 4 | EIX | Utilities | −19,10% | −5,37 | −5,56 | sem dado | não | movimento de analista (Mizuho) |
| 5 | MDB | Technology | −17,44% | −2,20 | −2,26 | sem dado | **sim** | resultado trimestral (8-K 2.02) |
| 6 | LULU | Consumer Cyclical | −16,72% | −2,80 | −2,45 | **com lastro** (−4,19%) | não | resultado trimestral (8-K 2.02) |
| 7 | ADSK | Technology | −16,40% | −3,56 | −3,51 | sem dado | não | 10-Q na janela |
| 8 | CDNS | Technology | −14,01% | −2,78 | −2,88 | sem dado | não | sem 8-K e sem léxico reconhecido |
| 9 | PCG | Utilities | −13,86% | −3,90 | −4,12 | sem dado | não | Reg FD / guidance (8-K 7.01) |
| 10 | OSW | Consumer Cyclical | −11,32% | −2,59 | −2,48 | **sem lastro** (0,0%) | não | sem 8-K; manchete apenas |
| 11 | WLY | Comm. Services | −10,28% | −2,18 | −2,06 | sem dado | **sim** | resultado trimestral (8-K 2.02) |
| 12 | PTC | Technology | −10,26% | −2,09 | −2,05 | **sem lastro** (+0,15%) | não | sem 8-K; manchete apenas |
| 13 | TCOM | Consumer Cyclical | −9,53% | −2,18 | −2,01 | **sem lastro** (+0,53%) | não | sem 8-K; manchete apenas |
| 14 | CLX | Consumer Defensive | −9,24% | −2,25 | −1,98 | **sem lastro** (0,0%) | não | sem 8-K; manchete apenas |
| 15 | REYN | Consumer Defensive | −9,15% | −2,46 | −2,29 | sem dado | não | sem 8-K; manchete apenas |
| 16 | AON | Financial Services | −9,09% | −3,06 | −3,03 | **sem lastro** (−1,35%) | não | Reg FD / guidance (8-K 7.01) |
| 17 | CPB | Consumer Defensive | −8,59% | −2,07 | −1,80 | sem dado | não | resultado trimestral (8-K 2.02) |
| 18 | SYK | Healthcare | −8,33% | −2,42 | −2,47 | sem dado | não | sem 8-K; manchete apenas |
| 19 | GIS | Consumer Defensive | −7,85% | −2,32 | −1,98 | **sem lastro** (+0,03%) | não | sem 8-K e sem léxico reconhecido |
| 20 | NSC | Industrials | −5,51% | −2,17 | −1,84 | sem dado | **sim** | sem 8-K; manchete apenas |

Concentração setorial da semana: Technology 7, Consumer Defensive 4, Consumer Cyclical 3,
Utilities 2, e um cada em Comm. Services, Financial Services, Healthcare, Industrials.
**Esta concentração é exatamente o motivo pelo qual o sorteio de controle tem de ser pareado
por setor** (seção 7): sete nomes de tecnologia numa mesma semana não são sete apostas
independentes.

---

## 4. A CONTAGEM DE FILTROS — HONESTA, INCLUINDO OS DISFARÇADOS

A lei da casa é **no máximo 3 filtros por motor**. Contando de verdade, e contando o que
está disfarçado de "universo" e de "requisito de dado", o funil acima tem **cinco cortes**:

| # | corte | mata quantos | é filtro no sentido da lei? |
|---|---|---|---|
| 1 | piso de liquidez (preço, volume, valor de mercado) | 205 de 1.638 | **sim, disfarçado de universo** |
| 2 | histórico mínimo de 210 barras | 37 | pré-condição de medição (sem 52 semanas não existe desvio de 52 semanas) |
| 3 | queda (z) | 1.376 | **sim** |
| 4 | idiossincrasia (parcela própria ≥ 50%) | 0 nesta semana | **sim** |
| 5 | lastro (consenso de EPS parado) | 13 de 20 | **sim** |
| + | gate de regime (seção 5) | liga/desliga o motor inteiro | **sim** |

**Total honesto: 6 cortes, dos quais 5 são filtros de julgamento. Isso viola a lei dos 3.**
Não vou escrever um documento que finge o contrário. Duas correções, ambas congeladas aqui:

**Correção A — fundir a queda e a idiossincrasia numa régua só.**
Em vez de cortar duas vezes (primeiro o z do retorno total, depois a parcela própria),
mede-se **o z do resíduo idiossincrático**: a queda própria da empresa, em desvios do
próprio resíduo semanal de 52 semanas.

```
z_idio = (retorno da semana − beta_mercado x retorno do SPY − beta_setor x retorno do ETF do setor)
         / desvio-padrão semanal de 52 semanas desse mesmo resíduo
corte: z_idio <= -2,0
```

Uma régua, um corte, e mede exatamente o que a tese diz que importa. Efeito medido nesta
semana: **16 dos 20 nomes sobrevivem** (saem CLX −1,98, GIS −1,98, NSC −1,84 e CPB −1,80 —
todos nomes cuja queda "grande" era em boa parte carregada pelo beta). O corte fica **mais
seletivo e mais fiel à tese**, e não foi escolhido olhando resultado — não existe resultado.

**Correção B — a média de 200 dias NÃO vira filtro; vira variável medida.**
Há uma tensão real e conhecida: `HCI_Controle_Drawdown` mostra que o filtro de SMA200
entregou +3,75pp dos +7,49pp de vantagem da carteira; mas quem cai 20% numa semana quase
sempre perde a própria média. Esta semana, **16 das 20 fichas estão abaixo da própria SMA200**.
Exigir "acima da SMA200" reduziria o funil de 20 para 4 fichas/semana e seria um quarto filtro.

Decisão congelada: **a posição contra a SMA200 é GRAVADA no ledger como estado, não usada
como corte.** Ela vira uma hipótese que o próprio ledger responde daqui a cinco meses
("as fichas acima da média revertem mais do que as abaixo?"), em vez de uma crença aplicada hoje.
Isso transforma um filtro em uma medição — que é o que a casa deveria fazer sempre que não tem prova.

**Contagem final, após as correções:**

| | corte | contagem |
|---|---|---|
| pré-condições (declaradas, não creditadas como edge) | piso de liquidez · histórico de 210 barras | 2 |
| **FILTRO 1** | queda idiossincrática, `z_idio <= -2,0` | 1 |
| **FILTRO 2** | lastro: consenso de EPS parado | 2 |
| **FILTRO 3** | gate de regime (liga/desliga o motor) | 3 |
| medido, não filtrado | SMA200 do nome · setor · motivo (8-K) · movimento de analista | 0 |

**Três filtros. A lei é cumprida — mas as duas pré-condições cortam 242 dos 1.638 nomes,
e eu não vou chamar isso de zero.**

**Consequência operacional obrigatória:** a semana zero (28/ago→04/set) foi coletada com a
régua velha (dois cortes). Ela fica no ledger marcada como `regua: v0` e **fica fora do teste
primário**, entrando apenas como sensibilidade declarada. A régua congelada (`v1`, com `z_idio`)
vale **a partir da semana 2**. Se a mudança de código não for feita antes da próxima rodada,
o método continua com 4 filtros e **isso tem de ser escrito no relatório da semana**, não
silenciado.

---

## 5. O GATE DE REGIME — OBRIGATÓRIO, E POR QUÊ

`HCI_Swing_Acoes_ML` é explícita: a reversão à média foi **a única família que sobreviveu**
em ações (PF 1,56 fora de amostra, robusta a custo até ~51 bps/perna) **e sobreviveu em um
regime só** — o touro de 2025-26. Um motor de reversão sem gate de regime é um motor que
já sabemos que vai encontrar um mercado onde ele não vive, sem ter como se desligar.

### 5.1 Qual gate NÃO será usado, e por quê

A mesma memória testou um gate por estado de retorno do mercado (touro / neutro / queda
lenta / crash) e o resultado parecia excelente. **Esse achado foi RETRATADO pela própria casa:**
ele era artefato do universo us100 (102 nomes de beta alto) e **a ordenação INVERTEU no
universo amplo de 11.595 instrumentos.** Portanto o gate "evitar a queda lenta de −4% a −10%"
está proibido aqui. Usá-lo seria contradizer uma retratação da casa sem prova nova.

### 5.2 O gate que será usado

**Régua: o SPY acima ou abaixo da própria média de 200 dias, com o sinal defasado em um dia.**

| estado | condição | motor |
|---|---|---|
| LIGADO | SPY fecha acima da SMA200 (sinal de ontem) | fichas são geradas e classificadas normalmente |
| DESLIGADO | SPY fecha abaixo da SMA200 (sinal de ontem) | fichas continuam a ser **coletadas e gravadas**, marcadas `regime: OFF`, e ficam **fora do teste primário** |

**Por que esta régua e não outra.** É o único classificador de regime que a casa testou em
**dois regimes distintos e passou nos dois** (`HCI_Controle_Drawdown`, `regime_filtro.py`):
no período ruim de 2000-2010 entregou **+18,73pp** sobre comprar-e-segurar (12,28% de retorno,
queda máxima de −21,5%), e no período bom de 2010-2026 custou apenas **−0,48pp**. É barato
quando erra e decisivo quando acerta. Nenhum dos outros quatro classificadores testados
qualificou nos dois períodos.

**Mecanismo de religar (lei nº 6: gate sem volta é motor morto).** O gate volta sozinho
quando o SPY fecha de novo acima da SMA200, com o mesmo atraso de um dia. Não há intervenção
discricionária, não há "esperar confirmar", não há período de carência.

**Defasagem de um dia, obrigatória.** O veredito do Deep Value guarda o precedente: um bug de
look-ahead de um dia (`px[dt] > sma[dt]`, embolsando o retorno do próprio dia) inflou toda
uma família de números até que o teste de sanidade "bom demais" o expôs. Aqui o sinal é
sempre o de ontem.

### 5.3 A tensão que este gate cria, dita agora e não depois

O gate desliga o motor exatamente nos períodos de estresse — que são, plausivelmente, os
períodos em que há mais liquidação forçada e portanto mais prêmio de liquidez a colher.
**É possível que este gate custe justamente a melhor janela do motor.** Não tenho prova de
que custa nem de que salva; tenho prova de que ele controla queda em dois regimes e é barato
no regime bom. Por isso as semanas com `regime: OFF` **continuam sendo coletadas e gravadas**:
ao fim da série, a comparação entre as semanas LIGADO e DESLIGADO responde essa pergunta com
dado, e não com opinião. Se as semanas DESLIGADO tiverem reversão melhor, **o gate está errado
e é ele que morre** — não o motor.

### 5.4 Estado do gate hoje

**Não verificado nesta redação.** O gate não foi computado nem gravado ainda; `ficha_queda.py`
não o implementa. É o item nº 2 da dívida técnica. Até ele existir, **toda ficha é `regime: indefinido`**
e nenhuma delas conta para o teste primário.

---

## 6. HORIZONTE DO SWING E ROTATIVIDADE

**Horizonte de medição (declarado antes, e não trocável):**

| horizonte | papel |
|---|---|
| 1 semana | diagnóstico (mede o repique imediato, não é o critério) |
| **4 semanas** | **o horizonte PRIMÁRIO — é por ele que o método é julgado** |
| 12 semanas | secundário (mede se o efeito persiste ou se apenas atrasa a queda) |

Os três campos já existem no ledger (`ret_1sem_pct`, `ret_4sem_pct`, `ret_12sem_pct` e as
versões em excesso sobre o SPY). Estão declarados os três **de propósito**, para que ninguém
possa depois escolher o que ficou melhor: **o critério de aceite lê o de 4 semanas**, e os
outros dois entram no relatório como contexto obrigatório, tenham dado o que tenham dado.

**Rotatividade.** O funil produz ~20 fichas/semana, ~7 na classe candidata. Se o Eduardo
operasse metade delas, seriam 3-4 entradas/semana com posse média de 4 semanas — algo como
12 a 16 posições simultâneas e ~180 operações/ano. **Isto é rotatividade alta**, e tem duas
consequências que precisam estar escritas:

- **Imposto: não é o problema.** Veículo é conta no exterior, alíquota 15% sobre o ganho
  anual em reais com netting integral (Lei 14.754/2023). `HCI_Controle_Drawdown` mediu:
  **girar 7x/ano custa praticamente o mesmo que girar 1x/ano** — o custo está em realizar,
  não na frequência. Arrasto medido entre 0,70pp e 1,50pp ao ano.
- **Pedágio: passa, com folga.** Custo ida-e-volta de 20 a 60 bps. As quedas idiossincráticas
  desta semana vão de −5,5% a −26,7%; mesmo um alvo modesto de reversão de 3% deixa o custo
  em **2% a 20% do alvo** — abaixo do teto de 25% da lei nº 1. **A régua fica em bps, nunca em
  dólares**, e é recalculada se o veículo mudar.
- **Concentração é risco real, não teórico.** Sete nomes de Technology na mesma semana não
  são sete apostas. O relatório semanal imprime a concentração setorial; o método não impõe
  limite (isso é decisão do Eduardo), mas **mede** e mostra.

---

## 7. CRITÉRIO DE ACEITE — DECLARADO ANTES, CONTRA SORTEIO PAREADO

**A referência NÃO é "bateu o S&P".** Uma cesta de nomes que caiu muito tem beta alto; num
mercado de alta ela bate o índice sem ter edge nenhum. A referência é o **sorteio pareado**.

### 7.1 A métrica primária

Para cada ficha: **retorno de 4 semanas em excesso sobre o SPY, em pontos percentuais**
(`ret_4sem_vs_spy_pp`, campo que já existe no ledger).

- **Preço de referência de entrada:** fechamento do **primeiro pregão após a geração da ficha**.
  A ficha é gerada no domingo sobre dados até a sexta anterior; a entrada de referência é a
  segunda-feira. Nunca o fechamento da sexta que já está dentro da janela de medição — isso
  seria look-ahead de um dia, o mesmo erro que o Deep Value pagou.
- **Estatística:** mediana (não média — sete nomes de tecnologia numa semana de estresse
  produzem cauda que a média não descreve).
- **População primária:** fichas `sem lastro`, com `regime: ON`, régua `v1`.

### 7.2 Controle B — o pacote contra o acaso (PRIMÁRIO)

Para cada ficha, sorteia-se um ticker do universo líquido **na mesma semana e no mesmo setor**,
sem nenhuma condição de queda. Mesmo n, mesma distribuição de setores, mesma distribuição de
semanas. Repete-se **2.000 vezes** para construir a distribuição nula da mediana.

Isto responde: *ser uma ficha vale alguma coisa contra um nome qualquer do mesmo setor na mesma semana?*

### 7.3 Controle A — o lastro contra o não-lastro (SECUNDÁRIO, e provavelmente sem n)

Para cada ficha `sem lastro`, pareia-se com uma ficha da **mesma semana, mesmo setor e
`z_idio` comparável (diferença ≤ 0,5)** classificada como `com lastro`.

Isto responde a pergunta que dá ou tira o valor do método inteiro: *é o lastro que separa,
ou é só a queda?*

**Aviso honesto, escrito antes:** o braço `com lastro` teve **1 nome** nesta semana. A um ou
dois por semana, este controle só fica legível quando acumular **≥ 30 nomes com lastro** —
entre 15 e 30 semanas, e possivelmente nunca. **O controle A será declarado "sem n" e não será
substituído por um controle mais fácil** (por exemplo, comparar contra "sem dado", que não é
"com lastro"). Prometer o controle A e depois entregar um primo dele é a fraude silenciosa
que este documento existe para impedir.

### 7.4 O aceite, em números

O método é **APROVADO como observação forward** — e nada além disso — se, na data da
seção 8, todas as condições valerem ao mesmo tempo:

1. **n suficiente**: ≥ 60 fichas `sem lastro` **e** ≥ 20 semanas distintas com `regime: ON`.
2. **Controle B batido**: mediana do excesso de 4 semanas acima do **percentil 95** da
   distribuição nula pareada (p ≤ 0,05, 2.000 reamostragens).
3. **Coerência de sub-período**: o excesso é positivo **nas duas metades** da série
   (primeiras 10 semanas e últimas 10). Um resultado carregado por uma metade não passa.
4. **Não é cauda**: retirando as **3 maiores** contribuições individuais, o excesso continua
   positivo. (`HCI_Filtros_Catalogo`, controle nº 3 do protocolo anti-fantasia: TREND, PEAD e
   pairs já morreram nesse teste.)
5. **Sobrevive ao custo**: o excesso continua positivo com 60 bps ida-e-volta descontados.

**Se as cinco valerem**, o veredito máximo permitido é: *"há sinal forward que merece continuar
sendo observado"*. **Não é aprovação de motor** — ver seção 12.

**Se a 2 valer mas a do controle A não** (quando houver n), o veredito é: *"a queda
idiossincrática funciona; o lastro é decoração"*. Isso mata o método **como escrito**, e o que
sobra é um motor diferente, que exige pré-registro próprio.

---

## 8. O n MÍNIMO E A DATA DA PRIMEIRA LEITURA

**O que limita não é o número de fichas — é o número de semanas.** As fichas se aglomeram
(7 nomes de tecnologia numa semana são uma aposta, não sete). A independência efetiva é
semanal, e a memória já pagou por essa lição: no teste de reversão, 6.820 apostas-dia valiam
~283 apostas independentes.

**Conta com o ritmo real medido:** 7 fichas `sem lastro`/semana.

| exigência | valor | quando chega |
|---|---|---|
| ≥ 60 fichas `sem lastro` | 60 ÷ 7 ≈ **9 semanas** | não é o gargalo |
| **≥ 20 semanas com `regime: ON`** | **20 semanas** | **é o gargalo** |

| marco | data |
|---|---|
| semana 1 (régua v0, fora do teste primário) | 2026-09-06 |
| semana 2 (primeira sob a régua congelada v1) | 2026-09-13 |
| semana 20 (última coleta do teste primário) | **2027-01-17** |
| desfecho de 4 semanas da semana 20 fecha | **2027-02-14** |
| **PRIMEIRA LEITURA — horizonte de 4 semanas** | **2027-02-21** |
| desfecho de 12 semanas da semana 20 fecha | 2027-04-11 |
| LEITURA SECUNDÁRIA — horizonte de 12 semanas | **2027-04-18** |

Se houver semanas com `regime: OFF`, a data escorrega — conta-se 20 semanas **ligadas**,
não 20 semanas de calendário. As semanas desligadas são gravadas e lidas separadamente.

**Antes de 2027-02-21, nada de retorno é olhado.** Há **uma única inspeção intermediária
permitida**, em **2026-11-15 (semana 10)**, e ela é **cega ao resultado**: verifica apenas
encanamento — taxa de `SEM DADO` caindo, integridade do ledger, ausência de duplicatas,
gate de regime gravado. **Se qualquer retorno for olhado antes da data, a série está
contaminada e o teste primário morre.** Esta é a porta pela qual entra o garimpo, e ela
fica fechada por escrito.

---

## 9. COMO ESTE MÉTODO MORRE

Em ordem de probabilidade estimada, do mais provável ao menos:

**1. O atraso do analista (o mais provável).** Se as fichas `sem lastro` tiverem o consenso
de EPS revisado para baixo nas 1-4 semanas seguintes, então "sem lastro" nunca foi um fato
sobre a empresa — era só "o analista ainda não mexeu". O método viraria uma máquina de
comprar o que está prestes a ser rebaixado. **Teste embutido:** o campo
`eps_revisado_depois_pct` do ledger é preenchido no desfecho e mede isso diretamente.
**Regra de morte: se >50% das fichas `sem lastro` tiverem revisão negativa nas 4 semanas
seguintes, a classificação é um atraso e o método morre**, mesmo que o retorno tenha sido bom
(retorno bom com mecanismo falso é sorte de amostra, e a casa já enterrou vários).

**2. O controle B não é batido em 2027-02-21.** Lápide direta. O pacote inteiro — queda
idiossincrática, consenso parado, gate de regime — não vale mais que sortear um nome do mesmo
setor na mesma semana.

**3. Morte por instrumentação.** Se a taxa de `SEM DADO` continuar acima de 50% na inspeção
de 2026-11-15 depois do conserto da ancoragem de ano fiscal, a pergunta central é
inrespondível pela máquina e o método morre por não ter instrumento. (Hoje: 60%.)

**4. O controle B passa e o A reprova.** O lastro é decoração. Morre este método; nasce
outro, com pré-registro próprio.

**5. O gate nunca desliga.** Se o SPY ficar acima da SMA200 as 20 semanas inteiras, o gate
não foi testado e o resultado é de regime único — exatamente o defeito que
`HCI_Swing_Acoes_ML` já apontou. Nesse caso o veredito máximo é "sem informação sobre regime",
e o método **não pode ser promovido**, mesmo passando em tudo.

**6. Morte por não-execução.** Se o ledger não for preenchido semanalmente, não há
julgamento possível. Cada semana não gravada é perdida para sempre — o consenso ponto-no-tempo
não se recupera depois. **Uma série com buracos não é uma série curta; é uma série viciada**,
porque os buracos tendem a cair justamente nas semanas agitadas.

**7. Morte por decaimento.** Se o método for publicado com nomes ao vivo e o efeito sumir,
a causa é conhecida (McLean-Pontiff: −26% fora de amostra, −58% após publicação). Ver seção 13.

**A morte é registrada como lápide neste mesmo arquivo, com data e número.** Refutação é
ativo — a casa tem 17 pré-registros e 16 reprovações, e é esse estoque que dá credibilidade
ao que sobra.

---

## 10. O QUE NÃO SERÁ FEITO

Cada item abaixo é uma porta pela qual a casa já perdeu dinheiro ou tempo. Ficam fechadas
por escrito, antes de haver resultado:

1. **Não se reotimiza depois de ver resultado.** As réguas (`z_idio ≤ −2,0`, limiar de lastro
   de 3%, parcela idiossincrática, gate SMA200) estão congeladas até 2027-02-21. Se o
   resultado for ruim, o veredito é lápide — **não é uma varredura de vizinhos até encontrar
   um corte que funciona**.
2. **Não se troca a métrica.** O julgamento é a mediana do excesso de 4 semanas sobre o SPY.
   Não vira "e se olhássemos 8 semanas", "e se fosse a média", "e se tirássemos os utilities",
   "e se fosse retorno absoluto em vez de excesso".
3. **Não haverá backfill de consenso.** Existem 4 snapshots. Estimativa não se recupera
   retroativamente — os provedores sobrescrevem. **Qualquer número anterior a 2026-08-14 que
   apareça é look-ahead, sem exceção e sem "só para conferir".**
4. **Não se esconde a classe SEM DADO.** As duas taxas (sobre o total e sobre os classificáveis)
   vão sempre impressas juntas.
5. **Não se adiciona um quarto filtro para salvar um resultado ruim.** Lei da casa: filtro não
   cria edge, só protege edge que existe. Se não houver edge, não há o que proteger.
6. **Não se olha retorno antes de 2027-02-21**, exceto a inspeção de encanamento de 2026-11-15,
   que é cega ao resultado.
7. **Não se muda o piso de liquidez no meio da série.** Mudar a régua quebra a comparabilidade
   da única série ponto-no-tempo que a casa tem.
8. **Não se substitui o controle A por um primo mais fácil.** Se não houver n, escreve-se
   "sem n".
9. **Não se conta a semana zero (régua v0) no teste primário.**
10. **Não se promove a motor com um regime só.** Mesmo passando em tudo (seção 12).

---

## 11. A DIVISÃO DE TRABALHO — COM TODAS AS LETRAS

**O sistema entrega:**
- os dados da empresa (preço, queda em múltiplos de desvio, decomposição mercado/setor/próprio,
  posição contra a média de 200 dias, setor, valor de mercado, liquidez);
- a **classificação de lastro** (com lastro / sem lastro / sem dado, com o número do consenso
  e a janela de snapshots que o produziu);
- o **motivo**, com hierarquia de confiança declarada: item do 8-K na SEC (fato registrado) >
  movimento datado de analista (permite dizer se foi causa ou reação) > manchete
  (reforço, peso baixo, sempre marcada como inferência);
- o funil, para que se veja onde os candidatos morreram;
- os limites e as classes de "não sei".

**O Eduardo entrega:** a decisão de entrar ou não, e **a entrada, pela análise técnica dele**.
Também o preenchimento da nota no ledger, que é o que depois permite separar o valor da
tela do valor da leitura dele. Esta separação não é formalidade: no BO do ouro, o auto-grader
teve AUC 0,39 (pior que moeda) enquanto **a nota do Eduardo foi o edge** (A+ +1,542R vs A− +0,806R).
A hipótese de que o mesmo se repita aqui é séria, e o ledger é montado para poder medi-la.

**O sistema NUNCA:**
- emite ordem, nem simulada, nem em papel, nem "só para testar";
- diz compre, venda, entre, saia, segure;
- sugere tamanho de posição, preço-alvo, stop ou ponto de entrada;
- ordena as fichas por "atratividade" ou dá nota de compra — a ordenação é pela **queda
  idiossincrática**, que é uma medida, não um juízo;
- afirma que uma empresa está barata ou cara.

O preço de referência de 4 semanas do ledger existe **para julgar o método**, não para
avaliar o desempenho do Eduardo. São duas colunas separadas, de propósito.

---

## 12. OS LIMITES HONESTOS — O QUE OS NÚMEROS DE HOJE IMPEDEM DE AFIRMAR

**A série tem 4 snapshots de consenso (3 deltas) e 1 semana de fichas.** Decorre disso:

1. **Nada pode ser afirmado sobre desempenho.** Zero desfechos preenchidos. Qualquer frase
   sobre o método funcionar ou não funcionar, hoje, é invenção.
2. **A classificação de lastro é hipótese, não veredito.** Numa janela de uma semana, o
   analista revisa depois do evento. "Sem lastro" hoje significa "o consenso ainda não se
   moveu", que não é a mesma coisa que "o consenso não vai se mover".
3. **60% das fichas não têm resposta.** O `n` real de fichas classificadas nesta semana é 8,
   não 20. E dentro dos 8, o braço `com lastro` tem **um** nome.
4. **Um regime só, e nem isso.** O SPY andou +0,11% na semana. Não houve estresse. A etapa de
   idiossincrasia não cortou ninguém — o que não é qualidade do filtro, é ausência de teste.
5. **O gate de regime não existe em código ainda.** Está especificado nesta página e não
   implementado. Toda ficha é hoje `regime: indefinido`.
6. **O funil não é determinístico entre rodadas.** Fato observado hoje: a rodada das 20:14
   produziu 18 fichas e perdeu 179 nomes por "histórico curto"; a rodada das 20:44 produziu 20
   fichas e perdeu apenas 37. **A diferença foi falha de download, não dado.** O ledger
   registrou os dois eventos de escrita para a mesma semana. Consequência: **o ledger precisa
   gravar qual rodada gerou cada ficha**, e uma rodada com taxa de perda anômala tem de ser
   descartada e refeita, não aceita. Item nº 3 da dívida técnica.
7. **Este método não satisfaz as condições de reabertura da Fase 2.** `HCI_Swing_Acoes_ML`
   fechou o swing de ações com veredito duro e listou o que exigiria para reabrir: universo
   amplo real com deslistados, **um bear no teste cego**, e fundamentos ponto-no-tempo.
   Este método traz o terceiro (ponto-no-tempo próprio, forward, sem viés de sobrevivência —
   que é uma conquista real) e **não traz o segundo**. Vinte semanas não fabricam um bear.
   **Portanto o teto deste método, mesmo passando em tudo, é o mesmo do Deep Value:
   observação forward, jamais motor aprovado.** Promovê-lo a motor exigiria um pré-registro
   novo, com regime de estresse na amostra.
8. **O que a casa tem de raro aqui é o dado, não a conclusão.** Os snapshots semanais são
   ponto-no-tempo de verdade: tirados naquele dia, sem revisão retroativa, sem viés de
   sobrevivência. Isso é caro de comprar e impossível de reconstruir. **É por isso que a
   coleta semanal importa mesmo que o método morra** — a série sobrevive à lápide e serve
   ao próximo teste.

---

## 13. PUBLICAÇÃO — COMO ISSO VIRA POST SEM VIRAR RECOMENDAÇÃO

**A condição jurídica, dita sem rodeio.** O dono publica como **pessoa física, sem registro
na CVM como analista de valores mobiliários** (Resolução CVM 20/2021). Não há empresa entre
ele e o conteúdo: a responsabilidade é pessoal. A linha editorial decidida em 28/ago/2026 é
**cenário condicional apenas**.

**A régua em uma frase: informar o mapa, não indicar o caminho.**

**Pode:** descrever o gráfico, os níveis, a tendência, o volume, o quadro fundamental, a
decomposição da queda, a classificação de lastro, o método, os limites, e enunciar cenários
condicionais ("se o consenso for revisado para baixo, a queda ganha lastro; se ficar parado,
não ganhou").

**Não pode:** dizer compre ou venda, sugerir posição, tamanho, entrada, saída, preço-alvo
próprio, nem prometer retorno.

### 13.1 Três frases proibidas, com a versão corrigida ao lado

| PROIBIDO | CORRIGIDO |
|---|---|
| "CRDO caiu 26,7% sem lastro nas estimativas — oportunidade de compra abaixo de 175." | "CRDO caiu 26,7% na semana, 2,1 desvios da própria volatilidade; 93% da queda é da empresa, não do setor. O lastro **não pôde ser medido**: o ano fiscal mudou entre os snapshots. O gatilho registrado foi um 8-K de resultado trimestral em 01/set. **Se** o consenso for revisado para baixo nas próximas semanas, a queda ganha lastro; **se** ficar parado, não ganhou." |
| "As 7 empresas sem lastro desta semana devem se recuperar; historicamente reversão à média entrega 1,5% em 5 dias." | "Sete das vinte fichas ficaram na classe 'sem lastro'. **Não há resultado apurado**: a série tem uma semana e nenhum desfecho fechado. O número de 5 dias que já circulou nesta casa vem de um teste em **um único regime** e não descreve estas fichas. A primeira leitura com n suficiente está marcada para 21/02/2027." |
| "Nosso screen bateu o S&P nas primeiras semanas." | "Comparar uma cesta de nomes que caiu muito contra o S&P mede beta, não seleção. A referência deste método é **sorteio pareado** — mesmo n, mesmos setores, mesmas semanas. Até a data declarada, não há comparação a reportar." |

### 13.2 Regras de publicação específicas deste método

1. **Nunca se publica a semana corrente.** Ficha só pode ser publicada depois que o desfecho
   de 12 semanas dela fechou — ou seja, com **três meses de atraso**. Publicar a tela ao vivo
   entrega o que a casa gasta meses para achar, e o decaimento pós-publicação é documentado.
2. **O produto publicável é o MÉTODO e a REFUTAÇÃO**, não o nome. A casa tem 16 reprovações
   em 17 pré-registros, e esse é o estoque que quase ninguém publica.
3. **A classe "sem dado" aparece em todo post** que cite a taxa de "sem lastro". Publicar
   7/8 (88%) escondendo os 12 sem dado seria propaganda.
4. **Toda afirmação vem com a janela declarada ao lado.** Lei paga com sangue em 02/set: um
   percentil sem janela declarada é um erro à espera de acontecer (o dono confundiu máxima de
   5 anos com máxima histórica; eu havia cometido o mesmo erro dois dias antes, no AUDCHF).
5. **Nenhum número em dólar absoluto**, sempre percentil ou múltiplo de desvio — a régua
   pública é a mesma régua interna.
6. **Se o método morrer, a lápide é publicada** com a mesma prioridade que teria o sucesso.
   Essa é a diferença editorial da casa, e ela só vale se for cumprida quando dói.

---

## APÊNDICE — DÍVIDA TÉCNICA (o que precisa existir antes da semana 2)

| # | item | efeito se não for feito |
|---|---|---|
| 1 | ancorar a comparação de consenso no **mesmo `fy_date`**, não no "FY corrente de cada snapshot" | a taxa de SEM DADO fica em 60% e a pergunta central segue inrespondível (modo de morte nº 3) |
| 2 | implementar e gravar o **gate de regime** (SPY vs SMA200, sinal defasado 1 dia) | não há teste primário — toda ficha fica `regime: indefinido` |
| 3 | trocar o corte por **`z_idio`** (uma régua) e gravar `regua: v0/v1` e o id da rodada no ledger | o método fica com 4 filtros e viola a lei dos 3; e rodadas com falha de download entram na série |
| 4 | preencher os desfechos do ledger (`ret_1/4/12sem`, `vs_spy`, `eps_revisado_depois_pct`) | não há julgamento possível (modo de morte nº 6) |

---

*Congelado em 2026-09-06. Alterações a partir daqui são registradas no rodapé com data e motivo,*
*e qualquer alteração de régua invalida a série e reinicia a contagem das 20 semanas.*
