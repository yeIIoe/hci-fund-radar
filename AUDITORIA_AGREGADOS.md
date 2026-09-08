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

## 2. RISCO LATENTE — medido, NÃO consertado (é decisão do dono)

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

### 2.2 🟡 O piso do ciclo é um penhasco — e quatro moedas estão do lado errado dele

Já estava declarado no código (o comentário de `dimensao_ciclo` mede o caso do GBP), então **não
é achado novo** — mas a leitura de hoje reforça: `CICLO_PISO_VOTO = 0,25` e o decaimento atual é
USD **0,208**, GBP **0,216**, CAD **0,163**, CHF **0,076**. Quatro das oito moedas leem o ciclo
como MANTÉM porque estão logo abaixo de um piso arbitrário; o GBP está 13,6% abaixo dele. Com
piso 0,20 — tão arbitrário quanto 0,25 — GBP e USD trocariam de leitura.

### 2.3 🟢 `LIM_LASTRO = 3,0` em `ficha_queda.py`

Faixa morta que decide "com lastro" contra "sem lastro" de **uma** empresa — não entra em soma
nem em média, então não é da família. Fica registrado só porque é PROVISÓRIO e binário: uma
revisão de EPS de −2,9% e uma de −3,1% saem em baldes opostos.

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

**Não tocados:** `ui_macro.js`, `ui_lang.js`, `index.html`, `precificacao.py`, `geopolitica.py`,
`correlacao_juros.py`, `ficha_queda.py`. Nenhum commit, nenhum push.
