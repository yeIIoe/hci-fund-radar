# MÉTODO — a leitura de sentimento macro do HCI FUND RADAR

*Documento vivo. Revisão de 08/set/2026 — a winsorização por item foi revogada (§4).*
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
peso       = decaimento × min(1 ; decaimento / 0,25)          ← RAMPA, 08/set
contribuição no score = 0,25 × sinal do último movimento × peso
```

Meia-vida de **120 dias**: o último movimento perde metade do peso em quatro meses.

**O SEGUNDO penhasco caiu em 08/set — o piso virou rampa.** O piso de 0,25 era ele próprio um
degrau: aos **240 dias exatos** a contribuição caía de 0,0625 para 0,0000 de um dia para o outro,
e **quatro das oito moedas** estavam logo abaixo dele (USD 0,208 · GBP 0,216 · CAD 0,163 · CHF
0,076), o GBP a 13,6% de trocar de leitura. Agora o mesmo 0,25 é o **joelho** de uma rampa
linear: acima dele nada muda, abaixo dele o peso desce em rampa até zero. **Nenhum número novo
entrou** — trocar degrau por rampa é conserto de forma; escolher um joelho diferente seria
calibrar sem backtest.

A prova roda em toda rodada (`tabela_da_rampa()`, publicada na régua): com o piso, o maior salto
entre dois vizinhos era 0,0625 e **não encolhia** quando a grade afinava 10× — assinatura do
degrau. Com a rampa é 0,0049 e cai para 0,0005 com a grade 10× mais fina. Efeito medido na mesma
rodada: nenhuma das oito moedas trocou de leitura; 5 dos 28 pares subiram uma faixa de
divergência.

**Duas coisas mudaram junto, por coerência.** A `direcao` do ciclo passou a ser o **fato** (o
último movimento foi alta ou corte) — uma dimensão que contribui −0,047 não pode declarar
"MANUTENÇÃO". E quem diz "o banco está parado" é o **regime**, que ficou no mesmo joelho
(`ainda_pesa`) e não move mais nenhum número. `regime` é uma palavra, e toda palavra tem
fronteira; o que a lei da casa proíbe é que um centésimo mude o **número**, e isso acabou.

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

## 4. A concentração — nenhuma divulgação manda sozinha, e a soma continua sendo a soma

*Reescrito em 08/set/2026. A winsorização por item foi **revogada**.*

**O pedido do dono estava certo; o lugar onde a regra foi posta estava errado.** O caso dele
(05/set): o CAD com uma única divulgação de emprego respondendo por quase toda a dimensão, com
três divulgações no ciclo. A resposta de 05/set foi cortar cada item em 4,0 dentro da **soma**.
Peso relativo é problema de **participação**, e ela foi tratada mexendo nos **termos da soma**.

### O que a winsorização fazia, medido em 08/set na própria rodada

| moeda | soma crua | soma winsorizada | direção |
|---|---|---|---|
| USD | −1,19 | **−8,29** | MANTÉM → **CORTA** |
| GBP | −4,66 | **−5,77** | MANTÉM → **CORTA** |

Os **três maiores** itens do dólar eram **altistas** e de impacto alto — ISM Services PMI
(+4,25), Average Hourly Earnings (+7,90), Nonfarm Payrolls (+7,02) — e só eles foram cortados
para 4,00. Os baixistas (−3,98, −3,82) passaram inteiros. **O corte tirou peso de um lado só.**
Consequência na tela: o painel lia *"USD inclinado ao corte"* enquanto os futuros de fed funds
pagavam p_alta = 0,5786 para o FOMC de 16/09. Parte da divergência que é o **produto** do painel
era defeito nosso.

E o efeito ia nos **dois sentidos**, conforme o lado em que estivessem os itens grandes: no CAD
a mesma regra puxava a soma de −4,80 para −1,81, a intensidade caía para 9% e a moeda **sumia**
em "sem leitura". Fabricava direção numa moeda e apagava direção noutra.

**A aritmética, para não precisar de fé:** cortar um termo *x* para *c* muda a soma em
`(c − x)`, que tem o **sinal contrário** ao de *x*. Winsorizar termos de uma soma não amortece o
item: **desloca o total**. Não existe escolha de teto que conserte isso — as duas versões da
regra (teto pela mediana, teto fixo 4,0) morreram da mesma causa com diagnósticos diferentes.

### O que vale desde 08/set — quatro regras

1. **A soma é a soma.** Cada divulgação entra com a contribuição real
   (`peso da família × modulador de impacto × decaimento`). Nenhum termo é cortado.
2. **A dominância é régua de CONFIANÇA, não de valor.** A participação do maior item na massa
   absoluta da dimensão continua medida — ela já existia e já funcionava. Passando de **50%**
   (corte PROVISÓRIO) a moeda sai com **bandeira** e a **qualidade da evidência fica limitada a
   `100 − participação`**. A direção **não** é tocada.
3. **Quem quiser limitar peso usa reescala proporcional** — multiplicar *todos* os itens pelo
   mesmo fator, a única forma que preserva o sinal e as proporções. Ela está implementada e
   **desligada**, com a prova de por que não serve aqui: a participação é
   `|x_max|·k / Σ|x_i|·k = |x_max| / Σ|x_i|` — **o fator comum cancela**. Nenhum *k* derruba os
   100% do NZD para abaixo de 50%. Reescalar limita **magnitude**; o pedido é sobre
   **participação**. E ela também não é neutra: com o limiar fixo em 5,0, dividir tudo por dois
   empurra moedas de SOBE/CORTA para MANTÉM sem que nenhum dado tenha mudado.
4. **Nenhum tratamento vira a direção em silêncio** (§4.1).

### 4.1 A guarda de direção — a lei que fecha a família inteira do erro

Qualquer transformação entre o dado cru e a leitura publicada é **comparada com o cru**, em dois
pontos: na dimensão de dados (`direcao_crua` × `direcao`) e na leitura da moeda (`leitura_crua`
× `leitura`). Se a direção mudar, o campo sai com **bandeira e texto**, e a moeda vai para
**sem leitura** até alguém decidir — *leitura cuja direção depende do tratamento não é leitura,
é escolha de método, e escolha de método é do dono, não do código.*

**Gravado sempre, em todas as moedas:** `soma_crua`, `soma_tratada`,
`participacao_maior_item_antes`, `participacao_maior_item_depois`,
`direcao_mudou_pelo_tratamento` e `bandeira_de_direcao`. Hoje o tratamento é `nenhum`: as duas
somas são iguais, o deslocamento é 0,00 e a bandeira é `false` nas oito — e isso pode ser
**conferido** no arquivo, não precisa ser acreditado. A prova sintética roda em toda execução,
em `regua.tratamento_da_soma.prova_sintetica`, e os testes estão em
`tests/test_sentimento_tratamento.py`.

### 4.2 Onde a guarda NÃO alcança — a faixa neutra (auditoria de 08/set, à tarde)

A guarda compara a soma tratada com a soma **crua**. Mas "crua", ali, quer dizer *depois de
classificada*: quando o item chega à soma ele **já passou pela faixa neutra**. E a faixa neutra é,
literalmente, a mesma operação da winsorização revogada — só que **por baixo**: divulgação com
`|divulgado − consenso|` dentro do corte da família entra na soma como **zero**. Zerar um termo
*x* desloca o total em `−x`, no sentido contrário ao dele. Se o que cai dentro da faixa está
concentrado de um lado, a soma anda para o outro.

**Medido na rodada de 08/set (14:46 UTC), com o mesmo arquivo publicado:**

| moeda | itens que a faixa zera | peso que teriam | soma com a faixa | sem faixa | com a faixa pela metade |
|---|---|---|---|---|---|
| USD | 47 | −15,11 | **−1,16 (MANTÉM)** | **−16,28 (CORTA)** | −10,80 (CORTA) |
| GBP | 21 | −1,04 | **−4,64 (MANTÉM)** | **−5,69 (CORTA)** | −5,77 (CORTA) |
| AUD | 8 | +1,43 | +21,03 (SOBE) | +22,45 (SOBE) | +22,14 (SOBE) — mas **+2,70 (MANTÉM)** com a faixa dobrada |
| EUR | 90 | −3,98 | +15,03 (SOBE) | +11,03 (SOBE) | +13,21 (SOBE) |
| JPY | 12 | +3,37 | +9,75 (SOBE) | +13,10 (SOBE) | +10,11 (SOBE) |

**A faixa NÃO foi desligada, e a diferença para a winsorização é essa.** A winsorização não tinha
tese: cortar em 4,0 era um número escolhido para segurar dominância, e dominância não é problema
de soma. A faixa neutra tem tese econômica declarada — *"veio como esperado não muda o que já
estava no preço"* — e é a régua única dos três leitores (`macro_eventos.corte_da_surpresa`).
Revogá-la aqui seria trocar um método por outro sem medida, e **escolha de método é do dono**.

**O que mudou é que ela parou de ser invisível.** Toda moeda publica agora
`dimensoes.dados.faixa_neutra`: itens zerados, o peso que eles teriam com o sinal do próprio
desvio, e a soma **e a direção** com a faixa em 0×, 0,5×, 1× e 2× — sendo que a coluna 1×
reproduz exatamente a soma publicada (isso é testado). Quando a direção depende da faixa, sai
**bandeira na moeda** e **alerta no par**, que é onde a tela lê.

⚠️ **Fica em aberto, com o número na mesa:** a largura da faixa é PROVISÓRIA e nunca foi validada
contra o que o banco central fez depois. Hoje, **o "MANTÉM" do dólar existe por causa dela**.

### 4.3 Onde a guarda também não alcançava — o PARÂMETRO (conserto 2.1, 08/set à tarde)

**O parágrafo honesto, primeiro:** *hoje a direção de algumas moedas deste painel depende de
botões que ninguém mediu.* A meia-vida do decaimento dos dados (21 dias) e o modulador de
impacto (alto 1,0 / médio 0,5 / baixo 0,2) foram **declarados**, nunca comparados com o que o
banco central fez depois. Não existe calibração e não vai existir antes do backtest pré-registrado
que abre em **21/dez/2026** — escolher "o melhor número" agora seria garimpo, e a casa tem lápide
para isso. Enquanto não houver calibração, o que dá para fazer é **medir de quanto a leitura
depende do botão, e mostrar**.

A guarda de direção (§4.1) prende o **tratamento**: dado cru × dado tratado. A faixa neutra (§4.2)
prende o que roda **antes da classificação**. Faltava o terceiro: o **parâmetro**. É a mesma
família de erro um andar acima — *leitura cuja direção depende de um número que ninguém mediu não
é leitura, é escolha de método*.

**A faixa plausível, declarada e argumentada (PROVISÓRIA):**

| parâmetro | faixa | por que o piso | por que o teto |
|---|---|---|---|
| **meia-vida dos dados** | 14 a 30 dias (passo 2) | abaixo de 14, um dado do dia da reunião anterior (~42 dias) já vale menos de 13%: a leitura vira "as duas últimas semanas", e a régua de evidência já pede 12 itens | a janela é de 42 dias; com meia-vida 30 o item mais velho admissível vale 38%, com 45 vale **52%** — o dado mais velho passaria a pesar mais que metade do de hoje |
| **modulador de impacto** | alto **fixo em 1,0**; `0 ≤ baixo ≤ médio ≤ 1`, 13 variantes | contém o extremo **"só alto conta" (0 / 0)** | contém o extremo **"plano" (1,0 / 1,0)** |

O **alto é a referência, não um botão**: encolher os três pelo mesmo fator empurraria moedas de
SOBE/CORTA para MANTÉM sem que nenhum dado mudasse, porque `LIMIAR_DADOS` é fixo — é a mesma prova
já escrita em `reescala_proporcional`. O que se varia é o peso **relativo** do médio e do baixo.
A restrição `baixo ≤ médio ≤ alto` é a única coisa que o calendário de fato afirma: é a definição
dos rótulos.

**A cada rodada** a leitura de cada moeda é refeita nas **130 células** dessa faixa (10 meias-vidas
× 13 variantes). É barato porque são somas sobre termos que já estão na memória: **12 ms** de grade
pura, **21 ms** medidos ponta a ponta nas oito moedas — contra um orçamento de 10 s e uma cadeia de
73 s. A célula 1× (21 dias, modulador de hoje) **reproduz exatamente a soma publicada**, e isso é
testado; sem isso a comparação seria conversa fiada.

**A régua de apresentação — confiança, não decisão:**

| concordância da grade | o que acontece |
|---|---|
| **100%** | leitura robusta ao parâmetro, segue como está |
| **abaixo de 100%** | bandeira *"direção depende de parâmetro não calibrado"* + **qualidade da evidência limitada à concordância** (mesma forma do teto da dominância) |
| **abaixo de 60%** (PROVISÓRIO) | **SEM LEITURA**, exatamente como quando o tratamento vira a direção |

**Por que 60:** tem de ser **acima de 50**, porque em 50 a direção publicada é cara-ou-coroa entre
métodos e abaixo disso ela é a leitura **minoritária** da faixa plausível — publicar minoria como
"a leitura" é indefensável. Tem de ser **abaixo de 100**, porque exigir unanimidade suspenderia uma
moeda por **uma** célula na ponta da faixa, e ponta de faixa é fronteira, não fragilidade. 60 é o
menor número redondo estritamente acima do cara-ou-coroa com folga: *3 em cada 5 escolhas
plausíveis concordam*. **PROVISÓRIO**, para o backtest calibrar junto com o resto.

⚠️ **A concordância é régua grossa, e isso sai declarado no arquivo.** Ela é a fração de uma
**grade que nós escolhemos**; adensá-la numa região muda o número. **Não é probabilidade.** O
número que **não** depende da densidade é o **marginal** — vira ou não vira girando um botão de
cada vez — e ele é publicado ao lado, sempre (`vira_pela_meia_vida`, `vira_pelo_modulador`,
`qual_parametro_faz_virar`, com as duas linhas inteiras e a fronteira).

**Medido na rodada de 08/set (à tarde), 130 células por moeda:**

| moeda | leitura publicada | concordância | vira p/ meia-vida | vira p/ modulador | quem faz virar | dimensão de dados |
|---|---|---|---|---|---|---|
| **USD** | sem leitura | **38%** | **SIM** | **SIM** | modulador | 72% (MANTÉM 93 · CORTA 34 · SOBE 3) |
| **GBP** | inclinado ao corte | **78%** | não | **SIM** | modulador | **54%** (MANTÉM 70 · CORTA 60) |
| EUR | inclinado à alta | 95% | não | SIM | modulador | 85% |
| JPY | inclinado à alta | 98% | não | não | só a combinação | 77% |
| AUD / NZD / CAD / CHF | — | **100%** | não | não | — | 100 / 100 / 77 / 100% |

**Leia a linha do dólar.** A leitura do USD só se sustenta em 38% da faixa: em **78 das 130
células** ela seria *inclinado ao corte*. E a fronteira é obscena de perto — com o modulador de
hoje, **21 dias dá "sem leitura" e 22 dias dá "inclinado ao corte"**. Um único dia num número que
ninguém mediu. Do lado do modulador, a soma do USD atravessa de **+2,67** ("só alto conta") a
**−6,84** ("plano") sem nenhum dado mudar. O USD já estava suspenso pela intensidade, então a regra
não mexeu na tela — mas agora o painel **diz por quê**, e a evidência do dólar caiu de 87 para 38.

**O GBP é o caso mais desconfortável:** ele sai publicado como *inclinado ao corte* e a **dimensão
de dados** dele é praticamente um empate — MANTÉM em 70 células, CORTA em 60. A leitura aguenta
(78%) porque o **ciclo** carrega o sinal; a dimensão de dados, sozinha, não decide nada. Isso está
publicado no bloco `dimensao` de cada moeda, que reproduz a medida do auditor (soma × `LIMIAR_DADOS`)
e **não comanda nada** — é medida, não regra.

**Efeito nos 28 pares (mesma rodada, mesmo instante, só ligando e desligando a régua):** nenhum par
trocou de faixa — sem tese 12 · observação 4 · moderada 3 · forte 9 dos dois lados. O que mudou foi
**confiança**: **5 pares** tiveram a qualidade da evidência derrubada pelo elo USD (EURUSD e USDJPY
de 85/87 para **38**, AUDUSD de 80 para 38, USDCHF e GBPUSD de 75 para 38) e **22 dos 28** passaram
a carregar o alerta *"a direção do X depende de PARÂMETRO NÃO CALIBRADO"* — todos os que têm perna
USD, EUR, GBP ou JPY.

**O que a grade NÃO cobre, declarado:** a largura da faixa neutra (já medida em §4.2, em
0×/0,5×/1×/2×), os parâmetros do **ciclo** (meia-vida de 120 dias e o joelho de 0,25, que têm bloco
próprio), e o efeito da meia-vida na parte *atualidade* da qualidade da evidência — a grade mede
**direção**, não nota.

#### 4.3.1 O que o REFUTADOR mediu em cima disto (08/set, fim da tarde)

**A faixa 14–30 NÃO estava protegendo o resultado, e isso foi testado alargando-a.** A grade
inteira foi refeita por um caminho independente — girando as constantes reais do módulo e chamando
a `dimensao_dados` de produção, sem usar o atalho `soma_da_dimensao_com` — e as oito concordâncias
gravadas foram **reproduzidas na casa do inteiro**, com a célula de hoje batendo a soma publicada
nas oito. Depois a faixa foi **alargada**:

| faixa da meia-vida | células | USD | EUR | GBP | JPY | AUD/NZD/CAD/CHF |
|---|---|---|---|---|---|---|
| só o ponto de hoje (21) | 13 | 38% | 92% | 77% | 100% | 100% |
| **declarada, 14–30 passo 2** | 130 | **38%** | **95%** | **78%** | **98%** | **100%** |
| a do auditor, 10–45 | 247 | 26% | 96% | 77% | 96% | 100% |
| absurda, 7–60 | 351 | 17% | 97% | 75% | 95% | 100% |
| 14–30 **com o `alto` também variando** | 280 | 51% | 96% | 68% | 99% | 100% |

**Nenhuma moeda cruza o corte de 60% em nenhum cenário** — o USD fica abaixo em todos (17 a 51) e
o GBP fica acima em todos (66 a 91). A faixa declarada não é o que segura a leitura de ninguém.

**O buraco que apareceu é o outro lado da mesma medida: os PONTOS da grade do modulador não têm
argumento escrito.** O piso, o teto e o passo da meia-vida estão argumentados um a um; os 5×4
pontos de `grade_medio`/`grade_baixo` não estão. E a escolha mexe: adensando para passo 0,1 (66
variantes em vez de 13, **a mesma faixa**), o **GBP vai de 78% para 91%** e o JPY de 98% para 100%.
Está declarado agora em `MODULADOR_FAIXA["por_que_a_grade"]`.

**O achado grave — a concordância tem um degrau que NÃO é desta grade.** Ela compara com o
**rótulo publicado**, e o rótulo tem uma borda fora daqui: o **piso de intensidade de 15%** da
`zona_de_leitura`. Varrendo a idade do último movimento do Fed dia a dia:

| idade do último movimento | intensidade | rótulo publicado | concordância |
|---|---|---|---|
| 271 dias | 15% | inclinado ao corte | **62%** |
| **272 dias (é onde o Fed está hoje)** | **14%** | **sem leitura** | **38%** |

**24 pontos de concordância em um dia, e o corte de 60% cai dentro do salto.** A rampa do §2.2
matou o degrau de 240 dias **no número**; este sobreviveu **no rótulo**, e ele é do piso de 15% —
que continua sem calibração e não foi tocado por nenhum dos dois consertos. Consequência prática:
o dólar está **em cima dessa borda, um dia depois dela**; nos **30 dias** entre 242 e 271 a rampa
publicaria *inclinado ao corte* onde a régua velha publicava *sem leitura*, com concordância de
**62% a 68%** — ou seja, **2 a 8 pontos** acima do corte de suspensão. Os dois consertos passaram
a um dia e a dois pontos de colidir. Está declarado em `ROBUSTEZ["aviso_da_borda_de_intensidade"]`.
**Enquanto o piso de 15% existir, a concordância de uma moeda encostada nele não mede a força da
leitura — leia o marginal, não a fração.**

**Isto não é um filtro novo.** A lei dos três filtros continua valendo: medir fragilidade é
**medida de confiança**, da mesma família da dominância, que já existia. A única decisão que a
régua toma é a que a guarda já tomava — **suspender** a leitura quando a direção deixou de ser do
dado. Está preso por teste em `tests/test_sentimento_tratamento.py` (`RobustezDeParametroTest`),
inclusive o invariante de que a régua **nunca** muda o sinal: ou a leitura fica como estava, ou vai
para *sem leitura*.

### O que se perdeu, declarado

A garantia aritmética de que **uma divulgação sozinha nunca atinge o limiar** existia, mas era
paga com deslocamento da soma — e o preço era virar a direção. Agora esse caso é **possível**, e
quando acontecer sai declarado no campo `virou_sozinho`, com bandeira e com a evidência
derrubada. **Visível em vez de mascarado.**

**Hoje, com o alerta ligado:** NZD **100%** (Terms of Trade Index, 1 divulgação na janela) e CAD
**76%** (Net Change in Employment, 3 divulgações). As duas continuam sinalizadas — por
dominância e por qualidade (NZD 39 → **0**, CAD 54 → **24**, as duas "fraca") — e **não** por
direção adulterada.

O corte de 50% e o teto `100 − participação` são **PROVISÓRIOS** e vão ao backtest junto com o
limiar.

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
| 08/set — com winsorização por item | 11 | 2 | 6 | 9 |
| 08/set — **soma crua** (winsorização revogada) | 12 | 4 | 5 | 7 |

As duas últimas linhas são o mesmo calendário, no mesmo instante, com as mesmas faixas: a única
coisa que mudou foi o tratamento da soma. **Sete pares trocaram de faixa e um trocou de lado** —
EURNZD saiu de *observação BULL* para *sem tese*, por divergência (16 → 14, dentro da zona
neutra). Três dos sete (NZDUSD, GBPNZD, NZDCAD) foram rebaixados para observação **pela regra
que já existia** (§5): a qualidade do par virou 0 quando o teto da dominância zerou a evidência
do NZD.

Nove pares na faixa mais alta não é um sinal de que há nove teses fortes: é o sinal de que **o
corte de 40 foi desenhado para outra escala**. Enquanto não houver backtest, use a **ordem** dos
pares, não o nome da faixa.

### A zona SEM LEITURA, por moeda (PROVISÓRIA)

Uma moeda sai **"sem leitura"** quando:

- a intensidade relativa `(|leitura| / 0,50) × 100` fica **abaixo de 15**, ou
- **menos de duas dimensões votam** naquela moeda.

Hoje: **1 de 8** — USD (intensidade 6). ⚠️ Antes do conserto de 08/set eram GBP e CAD; o USD
**não** aparecia aqui porque a winsorização lhe dava uma soma de −8,29 que os dados não
sustentam. Com a soma crua (−1,17) o dólar volta para dentro da zona neutra, que é o que a
evidência diz.

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

**Teto pela dominância (novo em 08/set, PROVISÓRIO).** Quando o maior item responde por mais de
50% da massa da dimensão de dados, a nota fica limitada a `100 − participação`: se 76% da
dimensão é uma divulgação só, no máximo 24% da evidência é **de conjunto**. É a mesma medida do
alerta que já existia, sem número novo, e só morde acima do corte. Efeito hoje: NZD 39 → **0**
(participação 100%) e CAD 54 → **24** (76%). O arquivo grava `nota_antes_da_dominancia`,
`teto_pela_dominancia` e `limitada_pela_dominancia`. **Isto substitui o antigo corte na soma:
concentração vira desconfiança, nunca mudança de direção.**

⚠️ **Consequência que precisa ser vista:** qualidade 0 aciona a regra dos pares (§5) — o par não
sai da zona de observação. Os sete pares que contêm NZD ficam limitados a observação enquanto a
dimensão de dados do NZD for uma divulgação só.

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
9. **Nenhum tratamento vira a direção em silêncio** (08/set). Se qualquer transformação mudar a
   direção da leitura em relação ao dado cru, isso **aparece** — bandeira, texto e a moeda em
   *sem leitura* até alguém decidir. Corolário: problema de **peso relativo** se resolve na
   **confiança** (bandeira + evidência), nunca nos **termos da soma**.

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
- **O teto pela dominância zera a evidência do NZD** e, por tabela, limita os sete pares que o
  contêm. É o comportamento pedido (concentração = desconfiança), mas o valor `100 −
  participação` é declarado, não calibrado.
- **A meia-vida (21 dias) e o modulador de impacto (1,0 / 0,5 / 0,2) continuam sem calibração** —
  a §4.3 mede de quanto a leitura depende deles, mas **medir não é calibrar**. Hoje a leitura do
  USD só se sustenta em 38% da faixa plausível e a fronteira dele está entre 21 e **22** dias de
  meia-vida. Quem decide o número é o dono, depois do backtest de 21/dez — não o código.
- **A própria concordância é régua grossa:** é a fração de uma grade escolhida (130 células), não
  uma probabilidade, e o corte de 60% é PROVISÓRIO (§4.3).
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
