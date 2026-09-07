# ARQUITETURA DE AGENTES — o painel deixa de ser um algoritmo e vira um time

*Proposta do Eduardo, 06/set/2026: "cada um deles é uma parte individual, o site só lê o que
eles foram programados para fazer. Pegamos o processo todo e transformamos num prompt do que
uma IA deve fazer, e outra IA lê tudo isso e passa para o site. Não vai mais ser um ALGO e sim
uma IA treinada e com memória específica para isso."*

Resposta curta: **dá para fazer, e é melhor do que o que temos hoje** — com uma linha dura no
meio, descrita na seção 1. Sem essa linha, o projeto perde a capacidade de ser validado, que é
justamente o que separa a HCI de um painel qualquer.

---

## 1. A LINHA DURA — o que NUNCA pode virar IA

**Número medido é código. Julgamento é IA.**

Uma IA não é reprodutível: a mesma entrada pode dar saída diferente. Isso é irrelevante para
escrever uma tese e **fatal** para calcular um desvio-padrão. Se a IA calcular o z, o ATR, a
média de 200 dias ou a variação do consenso, acontecem três coisas, todas ruins:

1. **O backtest morre.** O `PREREG_CONVICCAO.md` e o `equities_ledger.jsonl` só valem se o
   número de hoje puder ser recalculado igual daqui a três meses. Com IA no meio, não pode.
2. **A refutação morre.** "Testamos e não funcionou, aqui está o número" deixa de ser
   verificável — e publicar refutação é o diferencial declarado da casa.
3. **O custo explode.** São 848 papéis líquidos por semana. Aritmética em código custa 69
   segundos e zero centavo; em IA custa muito e demora muito.

> **Regra:** a IA nunca produz um número que entra em conta. Ela produz **classificação,
> julgamento e texto**, e sempre citando o número que o código mediu.

---

## 2. AS QUATRO CAMADAS

```
CAMADA 1  MEDIÇÃO      código puro, determinístico, barato
CAMADA 2  JULGAMENTO   um agente por tarefa, cada um com prompt versionado e memória própria
CAMADA 3  REDAÇÃO      um agente que lê tudo e escreve para o site e para as redes
CAMADA 4  SITE         só lê JSON. Zero lógica.
```

### Camada 1 — MEDIÇÃO (código)
Roda sobre o universo inteiro. Entrega números e o funil.
- preço, volume, ATR14, desvio de 52 semanas, **z da semana**, média de 200 dias
- decomposição da queda em mercado / setor / resíduo idiossincrático (beta de 52 semanas)
- variação do consenso de EPS entre os snapshots ponto-no-tempo → **o teste de lastro**
- o funil, com quantos morrem em cada etapa
- o `equities_ledger.jsonl`, append-only

**Corta de ~848 para ~15 papéis.** É esse corte que torna a camada 2 viável: a IA só é chamada
para 15 empresas, não para 848.

### Camada 2 — JULGAMENTO (agentes)
Um agente por tarefa. Cada um recebe os números da camada 1 e **nunca os recalcula**.

| Agente | O que faz | O que a memória dele guarda |
|---|---|---|
| `motivo` | lê 8-K, notícia e resultado; classifica o que aconteceu e a gravidade | como classificou casos parecidos, e o que aconteceu depois |
| `excesso` | dado o motivo e os números, julga se a reação passou do que o fato pedia | casos análogos passados, com o desfecho medido |
| `fundamento` | lê os dados contábeis; escreve a ficha e levanta bandeiras | armadilhas que já viu, setor por setor |
| `advogado_do_diabo` | tenta derrubar a tese dos outros três | os erros que a casa já cometeu |

O quarto agente existe porque uma máquina de gerar teses sem uma máquina de derrubá-las produz
lista longa e convicção falsa.

### Camada 3 — REDAÇÃO
Um agente lê a camada 1 e a camada 2 e escreve:
- a ficha da empresa em português, para o site
- o post de cenário condicional para Reddit, X e Threads
- o post de refutação quando o funil não aprova ninguém

### Camada 4 — SITE
Só lê `data/*.json`. Nenhuma regra, nenhuma conta, nenhuma decisão. É o que já fazemos hoje com
o `sentimento.json`; muda só quem escreve o arquivo.

---

## 3. A MEMÓRIA — o que dá "IA treinada" de verdade

Não é fine-tuning. É memória em arquivo, versionada no git, que o agente lê antes de julgar e
escreve depois. Uma pasta por agente:

```
agentes/<nome>/PROMPT.md        o que ele deve fazer, versionado (v1, v2...)
agentes/<nome>/MEMORIA.md       índice das lições
agentes/<nome>/casos/*.md       um arquivo por caso julgado, com o desfecho medido depois
agentes/<nome>/LAPIDES.md       o que ele já errou e não pode repetir
```

O ciclo que faz o time melhorar: o agente julga → o ledger guarda o julgamento **com a versão
do prompt** → semanas depois o desfecho é medido → o caso volta para a memória dele com o
acerto ou o erro. É assim que ele "aprende", e é auditável, o que fine-tuning não é.

---

## 4. O QUE O LEDGER PASSA A GRAVAR

Sem isto, a arquitetura não é validável e não vale a pena trocar:

```json
{ "data": "...", "ticker": "...",
  "camada1": { "z": -3.06, "residuo_pct": -7.4, "delta_eps_pct": 0.0, "sma200": "abaixo" },
  "camada2": { "motivo": {"classe": "...", "versao_prompt": "motivo@v3", "confianca": "..."},
               "excesso": {"veredito": "...", "versao_prompt": "excesso@v2"},
               "fundamento": {"bandeiras": ["..."], "versao_prompt": "fundamento@v1"},
               "advogado": {"objecao": "..."} },
  "camada3": { "texto_publicado": "...", "onde": ["reddit","x"] },
  "desfecho": { "preenchido_depois": null } }
```

Guardar a **versão do prompt** é o que permite dizer, depois, *qual camada errou*: a medição, o
julgamento ou a escrita. Sem isso a gente só sabe que errou.

---

## 5. O QUE MUDA NA PRÁTICA, E O QUE NÃO MUDA

**Muda para melhor:** classificar o motivo de uma queda lendo um 8-K é coisa que código não faz
bem e IA faz muito bem. Julgar se a reação passou do ponto exige contexto, e contexto é a maior
força de um modelo. E o texto para publicar deixa de ser modelo preenchido e passa a ser
análise escrita.

**Não muda:** o funil, o ledger, o pré-registro e as leis da casa continuam iguais. Máximo de 3
filtros, controle por sorteio pareado, refutação vira lápide, nada em valor absoluto.

**Custa:** cerca de 15 empresas × 4 agentes = 60 chamadas por semana, mais uma de redação. É
barato. Rodar a camada 2 sobre 848 papéis não seria, e é por isso que a camada 1 precisa cortar
antes.

---

## 6. RISCOS, com o remédio ao lado

| Risco | Remédio |
|---|---|
| A IA inventa um número que ninguém mediu | ela recebe os números prontos e é proibida de calcular; o verificador confere cada número citado contra a camada 1 |
| Dois agentes se contradizem | o de redação é obrigado a **mostrar** a contradição, nunca escolher em silêncio |
| A memória vira eco: o agente repete o próprio erro por já ter escrito antes | o `advogado_do_diabo` lê a memória **contra** a tese, e as lápides ficam em arquivo separado |
| O prompt muda e ninguém percebe | versão do prompt gravada em toda linha do ledger |
| Vira recomendação sem querer | a camada 3 tem régua de linguagem própria; pessoa física sem registro na CVM publica cenário condicional |

---

## 7. O SITE — o ponto de encontro de tudo que os agentes pesquisaram, concluíram e julgaram

*Pedido do Eduardo: "quero que o nosso site seja um encontro de tudo do que todos os agentes
pesquisaram, concluíram e julgaram."*

Hoje o site é um painel de macro. Ele passa a ser **o registro público do trabalho do time** —
e é essa mudança que faz o diferencial declarado da casa (publicar o método e as refutações)
sair do papel, porque a refutação deixa de ser um documento perdido e vira uma seção da tela.

### 7.1 As cinco salas

| Sala | O que mostra | Quem escreve |
|---|---|---|
| **MACRO** | bancos centrais, leitura por moeda e por par, calendário com surpresa, o que o mercado precifica | os coletores + o agente de leitura macro |
| **AÇÕES** | as fichas da semana: quanto caiu, por quê, se a reação passou do ponto, a ficha de fundamento e a objeção do advogado do diabo | camada 1 + os quatro agentes |
| **JULGAMENTOS** | o placar de tudo que a casa já testou — aprovado, reprovado, em teste — cada linha com o número que decidiu e a data | todos os agentes, mais as lápides |
| **MÉTODO** | os documentos vivos e congelados: método do sentimento, método da queda, os pré-registros, com a data de congelamento | escrito à mão e por agente, versionado |
| **DIÁRIO** | o que mudou desde ontem: agente X mudou de opinião sobre Y, e por quê | o agente de redação |

A sala de **JULGAMENTOS** é a mais importante das cinco, e é a que ninguém mais tem. É onde
fica escrito que o FUND v0.1 morreu depois de 15 pré-registros nulos, que o filtro do dólar
reduziu o resultado nas seis células, que o PEAD só sobrevive na perna comprada. Acerto todo
mundo publica; **lápide com número é o que constrói reputação.**

### 7.2 A regra de proveniência — toda tela diz quem falou

Nenhum bloco aparece no site sem responder quatro coisas, visíveis ou a um clique:

```
quem      agente `excesso`, prompt v2
quando    06/09/2026 14:58 BRT
fonte     8-K de 03/09 (link) + snapshot de consenso de 05/09
o que é   JULGAMENTO (não é medição, não é recomendação)
```

E cada bloco carrega um selo de natureza, porque misturar os três é o erro que mata a
credibilidade:

- **MEDIDO** — número que o código calculou; reproduzível
- **JULGADO** — leitura de um agente; pode estar errada e tem versão de prompt
- **EM TESTE** — hipótese com data de leitura marcada e n declarado

O painel de macro já faz isso em parte (selo de experimental na geopolítica e nas falas). A
regra passa a valer para tudo.

### 7.3 O contrato de dados

O site continua burro, e isso é proposital: ele **só lê JSON**. Cada agente grava o seu, e há
um índice que a tela lê primeiro.

```
data/agentes/<nome>/ultimo.json      a saída mais recente daquele agente
data/agentes/<nome>/historico.jsonl  append-only, para o diário e o placar
data/julgamentos.json                o placar: id, tese, estado, número, data, link do método
data/indice_agentes.json             quem existe, quando rodou, se falhou, versão do prompt
```

Se um agente falha, o site mostra a sala dele **com o último resultado e a idade**, mais o aviso
de que está velho. Nunca esconde e nunca inventa — a mesma lei do frescor que já vale no macro.

### 7.4 O que isso resolve

O site deixa de ser uma tela que alguém precisa lembrar de atualizar e vira a **saída natural**
do trabalho. Cada agente que roda já publica. E quando o funil não aprova ninguém numa semana, a
tela diz "esta semana o funil não aprovou nenhuma empresa" — que também é conteúdo, e é o tipo
de conteúdo que ninguém publica.

---

## 8. POR ONDE COMEÇAR

A camada 1 já está sendo construída agora (`ficha_queda.py`, `fundamento_ficha.py`) e continua
valendo inteira — ela é a fundação, não trabalho perdido.

1. Fechar a camada 1 e o ledger.
2. Escrever o `PROMPT.md` dos quatro agentes e as pastas de memória.
3. Rodar as duas camadas em paralelo por algumas semanas, com o ledger gravando as duas, e
   comparar: o julgamento da IA melhora a seleção em relação ao corte puramente numérico?
   **Essa comparação é a única forma honesta de saber se a troca valeu.**
4. Só então tirar a versão só-numérica do caminho — ou não tirar, se ela ganhar.

*Documento de arquitetura. Nada aqui é recomendação de investimento.*
