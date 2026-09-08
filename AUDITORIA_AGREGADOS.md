# AUDITORIA DE AGREGADOS — a família inteira do erro de 08/set

> **A LÁPIDE (uma frase):** *mexer no TERMO para consertar o TODO desloca o todo para o lado dos
> termos que sobraram — teto, piso ou faixa, a aritmética é a mesma, e quem paga é a direção.*

**Quando:** 08/set/2026, à tarde, depois do conserto da winsorização.
**O que foi varrido:** `sentimento.py`, `ficha_queda.py`, `fundamento_ficha.py`,
`precificacao.py`, `geopolitica.py`, `correlacao_juros.py` (e, de passagem,
`macro_eventos.py` e `leitor_regras.py`, que são de onde a régua da soma vem).
**O que se procurou:** (1) limite/clipe/teto/**piso** aplicado a termos que depois são somados
ou tirada média; (2) normalização que possa mudar o SINAL do agregado; (3) direção final
dependendo de parâmetro que ninguém calibrou.

Todos os números abaixo foram medidos na rodada real, reproduzindo o arquivo publicado — não
são estimativa nem exemplo.

---

## 1. O QUE FOI ACHADO E CONSERTADO

### 1.1 🔴 A FAIXA NEUTRA é o mesmo erro, por baixo — `sentimento.py` / `macro_eventos.py`

**MUDA A LEITURA DE HOJE.**

A winsorização cortava os termos por **cima**. A faixa neutra (`macro_eventos.corte_da_surpresa`
→ `classifica` → `EM_LINHA` → `empurrao` devolve **0**) zera termos por **baixo**: divulgação com
`|divulgado − consenso|` dentro do corte da família entra na soma como zero.

**É a mesma operação.** Zerar um termo *x* muda a soma em `(0 − x) = −x`, com o sinal contrário
ao dele. Se o que cai dentro da faixa está concentrado de um lado, a soma anda para o outro.

**O número que prova (rodada de 08/set, 14:46 UTC, arquivo publicado):**

| moeda | itens zerados | peso que teriam | soma publicada | sem faixa | faixa ×0,5 | faixa ×2 |
|---|---|---|---|---|---|---|
| **USD** | 47 | **−15,11** | **−1,16 · MANTÉM** | **−16,28 · CORTA** | −10,80 · CORTA | +1,15 · MANTÉM |
| **GBP** | 21 | −1,04 | **−4,64 · MANTÉM** | **−5,69 · CORTA** | −5,77 · CORTA | −1,84 · MANTÉM |
| **AUD** | 8 | +1,43 | +21,03 · SOBE | +22,45 · SOBE | +22,14 · SOBE | **+2,70 · MANTÉM** |
| EUR | 90 | −3,98 | +15,03 · SOBE | +11,03 · SOBE | +13,21 · SOBE | +8,96 · SOBE |
| JPY | 12 | +3,37 | +9,75 · SOBE | +13,10 · SOBE | +10,11 · SOBE | +5,09 · SOBE |
| NZD / CAD / CHF | 0 / 1 / 1 | 0,00 | inalterado | inalterado | inalterado | inalterado |

**Leia a linha do dólar.** O "MANTÉM" do USD hoje **existe por causa da faixa**: sem ela a soma é
−16,28 e a leitura é CORTA; com a mesma régua pela metade já é −10,80 e também é CORTA. As 47
divulgações silenciadas pesam **−15,11**, treze vezes a soma publicada. E isso enquanto o painel
declarava, no mesmo arquivo, *"tratamento da soma: nenhum · deslocamento 0,00 · direção do dado e
não do método"*.

**Por que a declaração estava falsa:** a `guarda_de_direcao` compara a soma tratada com a
"crua" — mas o que ela chama de cru **já passou pela faixa**. A guarda não conseguia enxergar o
maior tratamento do caminho porque ele roda antes do ponto onde ela olha.

**O QUE FOI FEITO — e o que deliberadamente NÃO foi feito.**
A faixa **não foi revogada**. A diferença para a winsorização é real: winsorizar em 4,0 era um
número escolhido para segurar dominância, e dominância não é problema de soma; a faixa neutra tem
tese econômica declarada ("veio como esperado não muda o que já estava no preço"), é a régua
única dos três leitores e tem corte medido por família. Trocar de método sem medida seria
inventar refatoração — e escolha de método é do dono.

O que foi feito é tirá-la do silêncio, sem inventar nenhum número novo (a sensibilidade usa a
**própria régua**, reescalada):

- `sentimento.py` → nova constante documentada `FAIXA_NEUTRA` e nova função
  `mede_faixa_neutra()`;
- toda moeda passa a publicar `dimensoes.dados.faixa_neutra`: itens zerados, peso que teriam,
  soma e direção com a faixa em **0× / 0,5× / 1× / 2×**, e `direcao_depende_da_faixa`;
- a coluna de fator **1,0 reproduz exatamente a soma publicada** — está testado, senão a
  comparação seria conversa fiada;
- quando a direção depende da faixa: **bandeira** na moeda (`tipo: "faixa_neutra"`) e **alerta no
  par**, que é onde `ui_macro.js` lê (nenhum arquivo de interface foi tocado);
- `regua.tratamento_da_soma` ganhou `o_que_este_campo_NAO_cobre` e a `guarda_de_direcao` ganhou
  `onde_NAO_alcanca` — as duas declarações falsas viraram declarações honestas;
- `METODO_SENTIMENTO.md` §4.2 documenta tudo, com a tabela;
- `tests/test_sentimento_tratamento.py` ganhou 4 testes novos, um deles prendendo a aritmética
  sem depender do dado do dia.

**Hoje o alerta aparece em 18 dos 28 pares** (todos os que têm perna USD, GBP ou AUD).

### 1.2 🔴 O clipe da alíquota vira o SINAL do ROIC — `fundamento_ficha.py`

**MUDA A LEITURA DE HOJE** (na ficha de fundamento, não no painel de moedas).

`taxa = min(max(imp/lair, 0.0), 0.60)` e depois `ROIC = EBIT × (1 − taxa) / capital investido`.
Quando a alíquota efetiva passa de 100% — imposto maior que o lucro antes de impostos, coisa
comum em TTM com baixa de uma vez só — o `(1 − taxa)` verdadeiro é **negativo** e o clipado é
**positivo**. O tratamento não amortece: **vira o sinal do número publicado**.

**O número que prova:** de 152 TTMs recentes no cache do EDGAR, **26 caem fora de [0 ; 0,60]**, e
o sinal vira em dois casos, um deles no TTM **de referência** de uma empresa da lista de hoje:

| empresa | TTM | alíquota efetiva | ROIC publicado | ROIC sem o clipe |
|---|---|---|---|---|
| **General Mills (GIS)** | 2026-05-31 | **102,2%** | **+1,74%** | **−0,10%** |
| John Wiley (WLY) | 2024-10-31 | 463,4% | +2,82% | **−25,58%** |

O ROIC do GIS está do lado positivo do zero **só por causa do clipe**. E o ponto virado do WLY
entra na série que alimenta a tendência (Theil-Sen de 8 TTMs) — a tendência não muda hoje
(MELHORA com e sem clipe, inclinação 2,268 contra 2,970), mas ela está lendo um ponto de sinal
trocado.

**O QUE FOI FEITO:** o clipe **fica** — o número sem ele também não presta —, mas para de ser
mudo. Cada linha TTM passa a gravar `aliquota_efetiva`, `aliquota_usada`, `aliquota_clipada` e
`clipe_virou_o_sinal`; nova função `ressalva_roic()` escreve a ressalva na ficha, que já é
impressa no `.txt`. Rodado: **7 das 19 fichas** saem com a ressalva; o GIS sai dizendo, com todas
as letras, que sem o clipe o ROIC seria negativo. Tolerância de 0,5 pp para não gerar ressalva de
clipe que não move número.

---

## 2. RISCO LATENTE — 2.1 medido e NÃO consertado (é decisão do dono); 2.2 e 2.3 CONSERTADOS na noite de 08/set

### 2.1 🟡 Três parâmetros que ninguém calibrou decidem a direção do dólar

Não são clipes: são pesos. Por isso não foram mexidos — mas a direção depende deles tanto quanto
dependia da faixa. Medido na mesma rodada, mexendo em um de cada vez:

**Meia-vida do decaimento (`MEIA_VIDA = 21` dias, PROVISÓRIA):**

| meia-vida | USD | CAD |
|---|---|---|
| 10 dias | **+6,42 · SOBE** | −4,14 · MANTÉM |
| 14 dias | +3,53 · MANTÉM | −4,49 · MANTÉM |
| **21 dias (hoje)** | **−1,17 · MANTÉM** | −4,80 · MANTÉM |
| 30 dias | **−5,59 · CORTA** | **−5,00 · CORTA** |
| 45 dias | −10,19 · CORTA | −5,16 · CORTA |

O dólar percorre **SOBE → MANTÉM → CORTA** sem que um único dado mude, só girando o botão da
meia-vida.

**Modulador de impacto (alto 1,0 / médio 0,5 / baixo 0,2 — números nunca medidos):**

| variante | USD | GBP | CAD |
|---|---|---|---|
| hoje (1,0 / 0,5 / 0,2) | −1,17 · MANTÉM | −4,66 · MANTÉM | −4,80 · MANTÉM |
| só alto conta | +2,67 · MANTÉM | +1,16 · MANTÉM | **−6,99 · CORTA** |
| plano (tudo 1,0) | **−6,83 · CORTA** | **−22,20 · CORTA** | −2,61 · MANTÉM |
| médio 0,6 | −1,82 · MANTÉM | **−5,04 · CORTA** | −4,36 · MANTÉM |

Note o GBP na linha "plano": **−22,20**, cinco vezes a soma de hoje. O modulador de impacto é o
parâmetro mais sensível do arquivo inteiro e é o menos justificado.

**Sugestão (não executada):** o mesmo bloco `faixa_neutra` que entrou hoje serve de molde — um
`sensibilidade` com meia-vida e modulador daria a foto completa. Não foi feito porque seriam três
mecanismos novos numa auditoria, e a lei dos 3 filtros vale também para instrumentação.

### 2.2 ✅ CONSERTADO — o piso do ciclo virou RAMPA (08/set, à noite)

`CICLO_PISO_VOTO = 0,25` era um corte seco: acima dele o último movimento entrava no score com
`0,25 × decaimento`; abaixo, com **zero**, e a dimensão lia MANUTENÇÃO. Quatro das oito moedas
estavam logo abaixo — USD **0,208**, GBP **0,216**, CAD **0,163**, CHF **0,076** — e o GBP a
13,6% de trocar de leitura por um número que ninguém calibrou.

**O que entrou:** a rampa linear mais simples que remove a descontinuidade, **sem nenhum número
novo** — o próprio 0,25 que era porta virou o **joelho**:

```
peso(d) = d × min(1 ; d / 0,25)     →   d²/0,25 se d < 0,25   ·   d se d ≥ 0,25
contribuição no score = 0,25 × sinal do último movimento × peso(d)
```

Contínua no joelho (as duas pontas valem 0,25), monótona, e `peso(0) = 0`.

| decaimento | contribuição ANTES | contribuição DEPOIS |
|---|---|---|
| 0,05 | 0,0000 | 0,0025 |
| 0,10 | 0,0000 | 0,0100 |
| 0,15 | 0,0000 | 0,0225 |
| 0,20 | 0,0000 | 0,0400 |
| **0,24** | **0,0000** | **0,0576** |
| **0,25** | **0,0625** ← salto | **0,0625** |
| 0,26 | 0,0650 | 0,0650 |
| 0,50 | 0,1250 | 0,1250 |
| 1,00 | 0,2500 | 0,2500 |

**A prova de que não é degrau, e ela roda em toda rodada** (`tabela_da_rampa()`): o maior salto
entre dois vizinhos da grade era **0,0625** com o piso e **não encolhe** quando a grade afina 10×
(continua 0,0625) — essa é a assinatura do degrau. Com a rampa o maior salto é **0,0049** e cai
para **0,0005** com a grade 10× mais fina: encolhe junto com o passo, que é o que continuidade
significa.

**O antes e o depois das oito moedas** (mesma rodada congelada, 08/set 15:10 UTC; só a regra do
ciclo mudou):

| moeda | decaimento | peso antes | peso depois | ciclo antes | ciclo depois | leitura antes | leitura depois |
|---|---|---|---|---|---|---|---|
| USD | 0,208 | 0,000 | 0,173 | 0,000 | **−0,043** | sem leitura (6%) | sem leitura (14%) |
| EUR | 0,598 | 0,598 | 0,598 | +0,149 | +0,149 | inclinado à alta (75%) | inclinado à alta (75%) |
| GBP | 0,216 | 0,000 | 0,187 | 0,000 | **−0,047** | inclinado ao corte (22%) | inclinado ao corte (31%) |
| JPY | 0,616 | 0,616 | 0,616 | +0,154 | +0,154 | inclinado à alta (68%) | inclinado à alta (68%) |
| AUD | 0,483 | 0,483 | 0,483 | +0,121 | +0,121 | inclinado à alta (73%) | inclinado à alta (73%) |
| NZD | 0,966 | 0,966 | 0,966 | +0,241 | +0,241 | inclinado à alta (47%) | inclinado à alta (47%) |
| CAD | 0,163 | 0,000 | 0,106 | 0,000 | **−0,027** | inclinado ao corte (22%) | inclinado ao corte (28%) |
| CHF | 0,076 | 0,000 | 0,023 | 0,000 | **−0,006** | inclinado à alta (46%) | inclinado à alta (44%) |

**Nenhuma das oito trocou de leitura.** O que mudou foi a intensidade das quatro que estavam
abaixo do piso, e **2 dos 28 pares** subiram uma faixa de divergência: **AUDUSD e USDJPY**, os
dois de "moderada" para "forte". ⚠️ O USD ficou em **14%**, a **um ponto** do mínimo de 15% da
zona "sem leitura" — está declarado porque amanhã pode virar, e por continuidade, não por degrau.

> 🔴 **CORREÇÃO DO REFUTADOR, 08/set (tarde).** Esta linha dizia **"5 dos 28 pares"**, nomeando
> também NZDUSD, GBPNZD e NZDCAD como tendo subido para "moderada". **Está errado, e o erro veio
> de medir a rampa recalculando só a conta do ciclo sobre a rodada publicada, sem refazer o
> `le_pares`.** Medido rodando as duas configurações no MESMO processo e no MESMO instante
> (rampa ligada × desligada, calendário congelado de 15:28 UTC): a distribuição das faixas vai de
> `sem tese 12 · observação 4 · moderada 5 · forte 7` para `sem tese 12 · observação 4 ·
> moderada 3 · forte 9`. Os três pares com perna NZD sobem de faixa **pela divergência**
> (GBPNZD 34→39, NZDCAD 34→37, NZDUSD 26→30) mas o `estado` publicado **continua "observação"
> nos dois lados**, porque o par está travado por `estado_limitado_por`: a qualidade da
> evidência do NZD é **0/100** (uma única divulgação na janela), e sem evidência o par não sai
> da zona de observação por maior que seja a divergência. Ou seja: os três já estavam limitados
> ANTES da rampa e continuam limitados DEPOIS — a rampa não os moveu. A régua de robustez do
> §2.1, testada isoladamente do mesmo jeito, **não move nenhuma faixa**.

**Duas consequências assumidas, porque a rampa obriga à coerência.** Uma dimensão que contribui
−0,047 não pode declarar "MANUTENÇÃO": a `direcao` do ciclo passou a ser o **fato** (o último
movimento foi alta ou corte) em todas as moedas com movimento registrado, e o peso é quem diz o
quanto isso importa. Quem responde por "o banco está parado" é o **regime**, que continua no
mesmo joelho (`ainda_pesa`) e **não move mais nenhum número** — as oito seguem com o mesmo regime
de antes. Efeito colateral visível: os chips de ciclo de USD/GBP/CAD/CHF passam a dizer "corte"
em vez de "manutenção", e a contagem de concordância muda em quatro moedas.

**O que a rampa não conserta, e está dito no arquivo:** `regime` é uma **palavra**, e toda palavra
tem fronteira. A dela ficou no mesmo joelho, não entrou número novo, e agora ela não decide valor
nenhum.

### 2.3 ✅ CONSERTADO — `LIM_LASTRO = 3,0` deixou de ser balde binário (`ficha_queda.py`)

O corte de 3% decide a **pergunta central** da ficha, e decidia sozinho: −2,9% saía "sem lastro"
e −3,1% "com lastro".

**O que NÃO mudou, de propósito:** o limiar continua em 3,0 e os **três estados** ("com lastro" /
"sem lastro" / "sem dado") continuam calculados pela mesma regra binária. A interface, o ledger e
a população primária do pré-registro (`METODO_QUEDA.md` §7, que é `sem lastro`) ficam intactos —
trocar a população de um pré-registro no meio do caminho é garimpo.

**O que entrou ao lado:** uma classificação **graduada** com **faixa de incerteza medida**, não
inventada. As colunas `epsHigh`, `epsLow` e `numAnalystsEps` já estavam nos snapshots e nunca
tinham sido lidas:

```
meia_amplitude = (epsHigh − epsLow)/2
erro_da_média  ≈ meia_amplitude / √n
incerteza_pct  = 100 × erro_da_média / |epsAvg|      (usa-se a MAIOR das duas pontas)
lastro_z       = var_eps_pct / incerteza_pct
FRONTEIRA      = revisão a menos de UMA incerteza de qualquer borda (−3,0 ou +3,0)
```

É a lei "nada em valor absoluto" chegando onde ainda não estava: a queda já era medida em
múltiplos do desvio (z), agora a **revisão** também. Declarado de propósito: amplitude/√n é um
proxy grosseiro e os dois snapshots compartilham analistas, então esta banda é um **teto** do
ruído — errar para o lado do "fronteira" suspende veredito em vez de fabricar um. Quando não dá
para medir (n < 2, amplitude nula, EPS perto de zero), sai `sem incerteza medida`, nunca um
silencioso "não é fronteira".

**Rodado em 08/set — 5 fichas na semana, `2 na faixa de fronteira`:**

| ticker | revisão de EPS | incerteza | distância da borda | estado (3 baldes) | grau |
|---|---|---|---|---|---|
| **DYN** | +2,00% | ±8,48 pp | 1,00 pp de +3,0% | sem lastro | **FRONTEIRA** (z = +0,24) |
| **RPRX** | +0,00% | ±3,79 pp | 3,00 pp de −3,0% | sem lastro | **FRONTEIRA** (z = +0,00) |
| NVS | −0,01% | ±0,59 pp | 2,99 pp | sem lastro | consenso parado (z = −0,02) |
| AMGN | +0,00% | ±1,43 pp | 3,00 pp | sem lastro | consenso parado (z = 0,00) |
| SYK | −0,00% | ±0,48 pp | 3,00 pp | sem lastro | consenso parado (z = −0,00) |

Note o RPRX: revisão **zero** e mesmo assim FRONTEIRA — com quatro analistas e ±3,79 pp de
dispersão, "consenso parado" e "consenso caiu 3%" são **o mesmo dado**. O ledger passou a
`v1.2` (a forma de medir mudou, então a linha nova é **anexada** ao lado da v1.1, nunca no lugar).

---

## 3. O QUE FOI PROCURADO E **NÃO** FOI ACHADO

Isto vale tanto quanto a lista de cima: são os lugares onde a operação **parece** o erro e não é.

| onde | o que tem | por que NÃO é o erro |
|---|---|---|
| `sentimento.py` — `comp["dados"] = 0,25 × tanh(soma / 10)` | saturação | é aplicada ao **agregado já somado**, não ao termo. `tanh` é ímpar e monótona: satura a magnitude e **nunca** muda o sinal da parcela. Comentário obsoleto que dizia "soma winsorizada" foi corrigido |
| `sentimento.py` — teto da nota pela dominância (`nota = 100 − participação`) | teto | aplicado **ao agregado final** (a nota), que é exatamente o lugar certo segundo a lição de 08/set. Nunca toca a direção |
| `sentimento.py` — `quantidade = min(100, ...)` na qualidade da evidência | teto num termo que depois entra numa **média** | os três componentes são não-negativos e definidos na escala 0–100; saturar é a definição da escala, não distorção de soma com sinal. Não existe direção aqui |
| `sentimento.py` — `divergencia = |diff| / TETO_PAR × 100` | normalização | divisor **constante e positivo** (1,00). Não pode mudar sinal. O caso perigoso — dividir pelo teto LIGADO — já tinha sido consertado em 06/set |
| `sentimento.py` — `peso_se_votasse = min(peso, peso_regua)` | teto por item | `peso_aplicado` é **0,0** nas oito moedas: a fala não vota desde 05/set. Latente, não ativo |
| `precificacao.py` — `_limita01` em `p_alta` / `p_corte` / `p_manutencao` | clipe em [0;1] | são probabilidades **mutuamente exclusivas** de um único evento e somam 1 por construção; não há soma de termos com sinal. A saturação em 100% quando o texto traz mais de um passo já sai declarada no campo `nota` |
| `precificacao.py` — manchete | — | retorna na **primeira** manchete aceita: não existe média entre fontes que pudesse ser enviesada por clipe |
| `geopolitica.py` | z-score de volume e média de tom | nenhum clipe, nenhum teto. E a dimensão **não vota** desde 05/set |
| `correlacao_juros.py` | Pearson e blocos sem sobreposição | nenhum clipe, nenhuma normalização com risco de sinal. Módulo de medição, não de direção |
| `ficha_queda.py` — `decompoe()` | betas de regressão | sem clipe em beta, sem winsorização de retorno. `parcela_idio` é participação (mesma medida da dominância), não valor. Ressalva menor: as três parcelas são aditivas em **log** e publicadas em **pp** via `exp(x)−1`, então não fecham a soma na tela — o sinal de cada uma é preservado (exp é monótona), só a aditividade se perde |
| `fundamento_ficha.py` — `tendencia()` | Theil-Sen | **mediana** de inclinações par a par, sem corte de termo — é o estimador robusto certo. O que fica em aberto é a janela `N_TEND = 8` e o fato de não haver faixa morta na inclinação (qualquer `|m| > 1e-9` já vira MELHORA/PIORA) |

---

## 4. A REGRA QUE FICA

1. **Nunca conserte concentração mexendo em termo.** Peso relativo é problema de
   **participação**; participação se responde na **confiança** (bandeira + teto na evidência),
   nunca no valor.
2. **Teto e piso são a mesma doença.** Cortar por cima ou zerar por baixo desloca o total no
   sentido contrário ao do termo mexido. Se os termos mexidos estão de um lado só, a direção anda.
3. **"Nenhum tratamento" só vale para o trecho que a guarda enxerga.** Toda declaração de
   pureza tem de dizer **de onde até onde** vale. Foi essa frase mal delimitada que escondeu a
   faixa neutra por dias.
4. **Tratamento que pode virar a direção continua ligado se tiver tese — mas sai medido, nas
   quatro escalas, com a coluna 1× batendo com o publicado.** Comparação em que o "hoje" não
   reproduz o arquivo não é auditoria.
5. **Todo limiar novo desta auditoria é PROVISÓRIO** e nenhum foi validado contra o que o banco
   central fez depois.

---

## 5. ARQUIVOS TOCADOS

| arquivo | o que mudou |
|---|---|
| `sentimento.py` | `FAIXA_NEUTRA`, `mede_faixa_neutra()`, campo `faixa_neutra` por moeda, bandeira na moeda, alerta no par, `o_que_este_campo_NAO_cobre`, `onde_NAO_alcanca`, comentário obsoleto do `tanh` corrigido |
| `fundamento_ficha.py` | `aliquota_efetiva` / `aliquota_usada` / `aliquota_clipada` / `clipe_virou_o_sinal` por TTM, função `ressalva_roic()` |
| `METODO_SENTIMENTO.md` | nova §4.2 "Onde a guarda NÃO alcança — a faixa neutra" |
| `tests/test_sentimento_tratamento.py` | classe `FaixaNeutraTest`, 4 testes (19 passando no total) |
| `AUDITORIA_AGREGADOS.md` | este documento |
| `sentimento.py` (noite) | **conserto 2.2**: `CICLO_JOELHO_RAMPA`, `RAMPA_DO_CICLO`, `peso_do_ciclo()`, `peso_do_ciclo_antes()`, `tabela_da_rampa()`; campos `peso`, `peso_antes_da_rampa`, `contribuicao_no_score`, `ainda_pesa`, `regime_no_joelho`, `rampa` por moeda; `regime_do_banco()` passa a usar `ainda_pesa`; a régua publica a prova da continuidade |
| `ficha_queda.py` (noite) | **conserto 2.3**: `incerteza_do_consenso()`, `graduacao_do_lastro()`, `FRONTEIRA_EM_INCERTEZAS`, `GRAU_LASTRO`; leitura de `epsHigh`/`epsLow`; campos `lastro_grau`, `lastro_fronteira`, `lastro_z`, `incerteza_eps_pct` na ficha, no relatório, no funil e no ledger; coletor `v1.2` |
| `tests/test_sentimento_tratamento.py` (noite) | classe `RampaDoCicloTest`, 7 testes novos (27 passando no total) |
| `METODO_SENTIMENTO.md` (noite) | §2.3 reescrita: o piso virou rampa |

**Não tocados:** `ui_macro.js`, `ui_lang.js`, `index.html`, `precificacao.py`, `geopolitica.py`,
`correlacao_juros.py`. Nenhum commit, nenhum push.
