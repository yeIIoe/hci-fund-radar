# MÉTODO — a leitura de sentimento macro do HCI FUND RADAR

**Versão 2026-09-05.** Este documento é a referência pública do método. Ele descreve o que
o painel mede, com que pesos, e — igualmente importante — **o que ele ainda não sabe**.

Regra de leitura deste documento: onde estiver escrito **PROVISÓRIO**, o número foi escolhido
por ordem de grandeza e não por calibração. Ele existe para poder ser medido e derrubado
depois, não para ser acreditado agora.

---

## 1. O que a leitura é, e o que ela não é

O painel lê **para onde cada banco central está inclinado a mexer no juro**, moeda por moeda,
e depois compara as duas pernas de cada par. Ele produz três números **separados**, que nunca
devem ser somados nem confundidos:

| Número | O que mede | Escala |
|---|---|---|
| **Divergência** | quanto as duas pernas do par discordam entre si, hoje | 0 a 100 |
| **Qualidade da evidência** | quanto se sabe sobre essas duas pernas | 0 a 100 |
| **Convicção histórica** | quanto uma leitura dessas acertou no passado | **hoje é `null`** |

A convicção histórica **não existe hoje** e sai como `null` com a nota *"ainda não calibrada —
precisa de backtest com amostra declarada"*. Ela não é derivada da divergência, nem estimada,
nem preenchida com um palpite. Só passará a existir quando houver amostra gravada e um
backtest com o *n* declarado ao lado.

O painel **não é um sinal de entrada**. Ele é a leitura do lado fundamental ao longo de
semanas. A entrada, o stop e o tamanho continuam sendo decisão do operador.

**Nenhuma dimensão usa yield.** Decisão do dono, mantida. O yield de 2 anos manda no preço no
prazo longo (120 dias, correlação +0,43) mas **não antecipa** em 1 a 20 dias — foi medido e
reprovado em 15 pré-registros. Ele está fora daqui.

---

## 2. As dimensões — o que cada uma mede

São **quatro dimensões calculadas** e **duas que votam**: DADOS e CICLO. Cada dimensão que
vota vale até **±0,25** na leitura contínua da moeda, que vai de −1 a +1 — logo o teto por
moeda é **0,50** e o teto do par é **1,00**.

A dimensão de TEXTO parou de votar na tarde de 05/set, junto com a de GEOPOLÍTICA. As duas
continuam calculadas, exibidas e com selo `experimental`, fora do score e fora do teto.

### 2.1 DADOS — o que foi divulgado (vota, ±0,25)

Surpresas acumuladas desde a última decisão do banco central, ou nos últimos **42 dias**, o
que for mais curto. **Uma decisão dentro da janela zera o acumulado**: só contam os eventos
publicados depois dela, porque o que veio antes já foi digerido na própria decisão.

Cada divulgação entra com três fatores multiplicados:

1. **Peso da família** — quanto o banco central realmente olha para aquele tipo de dado.
   Julgamento declarado, visível, não medido:

   | Família | Peso | Sinal |
   |---|---|---|
   | inflação núcleo | 10 | + |
   | salários | 9 | + |
   | criação de emprego / desemprego | 8 | + / **−** |
   | inflação cheia | 7 | + |
   | expectativa de inflação, PIB | 6 | + |
   | PMI / ISM | 5 | + |
   | varejo | 4 | + |
   | produção, moradia, auxílio-desemprego | 3 | + / + / − |
   | confiança, balança comercial | 2 | + |
   | coletiva de imprensa, a própria decisão | 0 | — |

   O sinal **negativo** do desemprego é deliberado: desemprego acima da previsão significa
   folga, e folga tira a urgência de apertar.

2. **Modulador de impacto** — alto 1,0 · médio 0,5 · baixo 0,25.

3. **Decaimento no tempo** — meia-vida de **21 dias**. Um empurrão de 30 dias atrás vale
   cerca de 37% de um de hoje.

**Limiar:** a soma decaída precisa passar de **±5,0** para a dimensão ler ALTA ou CORTE.
Abaixo disso lê MANUTENÇÃO. (PROVISÓRIO)

### 2.2 TEXTO — o que os dirigentes disseram (experimental, **NÃO VOTA**)

Contagem de expressões de postura no que os dirigentes efetivamente disseram. É um
**ponteiro do que ler**, não uma interpretação de conteúdo.

**Por que parou de votar (05/set, tarde):** a leitura era CONTAGEM DE PALAVRAS, e contagem
de palavras não lê negação, nem condição, nem referência temporal. "holding the target" está
na lista de termos hawkish, então Waller defendendo MANTER saía como alta. Desde 05/set a
dimensão é CONTEXTO, com peso 0,0. Ao lado dela roda o `leitor_falas`, um classificador por
regra que lê negação, condição, tempo verbal e sujeito — e que **também não vota**, porque
nunca foi medido contra rótulo humano nem contra a decisão seguinte do próprio banco.

Cada leitura sai com a **origem declarada** e essa origem tem peso — ver a seção 3.

Fed, BCE, BoE, BoJ e BoC estão ligados direto na página do próprio banco. **RBA e RBNZ
devolvem 403 para automação e o SNB não tem feed conhecido.** Nessas três a dimensão cai
para manchete de imprensa, que **pesa zero e não vota**. Isso é um buraco declarado, não um
zero: a dimensão simplesmente não conta.

### 2.3 CICLO — o último movimento de juro (vota, ±0,25)

Direção do último movimento, pesada por um **decaimento contínuo no tempo**, com
**meia-vida de 120 dias**:

```
decaimento = 0,5 ^ (idade em dias / 120)
```

Abaixo do **piso de 0,25** o movimento lê como MANUTENÇÃO e a dimensão não vota. (Os três
números são PROVISÓRIOS.)

Isto substituiu um penhasco anterior de 180 dias, em que 179 dias valia peso inteiro e 181
dias valia zero. **Honestidade obrigatória: o penhasco não acabou, mudou de lugar.** O piso
de 0,25 é ele próprio um degrau, que cai aos **240 dias exatos**, onde a contribuição vai de
0,063 para 0,000 de um dia para o outro. É quatro vezes menor que o degrau antigo, mas
continua sendo degrau, e onde ele fica muda número de capa.

**O termo de "reuniões de manutenção" está DESLIGADO.** Ele existia para descontar o peso a
cada reunião em que o banco não mexeu. Ao ser auditado, provou-se que media o **arquivo** e
não o banco: `bancos_centrais.json` só guarda reuniões **futuras**, então a contagem só
enxergava as datas que por acaso ainda estavam na lista e já tinham passado. Medido em
05/set: NZD e CAD levavam penalidade de 1 reunião; USD (269 dias sem mexer), GBP (262) e CHF
(443) levavam **zero**, apesar de terem feito muito mais reuniões de manutenção. O termo
punia quem o arquivo denunciou por acaso. Ruído de calendário com viés conhecido não entra em
leitura. A contagem continua gravada, com `reunioes_no_decaimento: false` e o motivo ao lado.
Religa quando `bancos_centrais.py` passar a guardar o histórico de reuniões.

### 2.4 GEOPOLÍTICA — experimental, **NÃO VOTA**

Intensidade do noticiário do GDELT, por moeda: volume de artigos dos últimos 3 dias contra a
média diária de 14 dias.

Em 04/set esta dimensão foi ligada como quarta dimensão do sentimento e como segunda perna do
ouro. **Em 05/set essa decisão foi revogada.** A regra ("pico de energia é empurrão de
inflação, pico de conflito é risco de crescimento") foi **declarada e nunca medida**, e a
regra da casa é que filtro novo passa por medição antes de pontuar — foi assim que o filtro
do DXY foi reprovado, depois de ter sido assumido. Enquanto isso, ela mexia em leitura de
verdade: o NZD saía com teto 1,00 por um *z* de energia de 1,85.

Hoje ela sai com selo `experimental`, `vota: false`, **fora do score e fora do teto**. O
conteúdo continua calculado e exibido, e o valor que ela teria *se votasse* fica gravado ao
lado, em `leitura_se_votasse`. Isso derrubou o teto máximo por moeda de 1,00 para 0,75 e o
do par de 2,00 para 1,50 — e, na tarde do mesmo dia, quando a fala também saiu do voto, para
**0,50** por moeda e **1,00** por par.

A hipótese que destrava o voto está registrada: *"conflito z ≥ 2 muda o retorno de 20 dias
das moedas de risco?"*

---

## 3. A hierarquia das falas — quem tem direito de votar

Nem toda "fala" é fala. A régua:

| Origem | Peso | O que é |
|---|---|---|
| `discurso_oficial` | **1,0** | discurso publicado na página do próprio banco |
| `comunicado_ata` | **1,0** | comunicado, ata ou coletiva do próprio banco |
| `imprensa_com_fala` | **0,4** | veículo reproduzindo dirigente **nomeado** |
| `manchete` | **0,0** | manchete sem dirigente nomeado — **não vota** |

O peso entra em **dois** lugares: multiplica a dimensão de texto no score
(`dimensoes.texto.peso_aplicado`) **e** entra na qualidade da evidência (componente
confiabilidade).

Para uma matéria de imprensa valer 0,4 ela precisa das **três** coisas ao mesmo tempo:
dirigente **nomeado**, **verbo de fala** no título ou no resumo, e veículo com peso ≥ 0,60
(PROVISÓRIO). Na imprensa o sobrenome sozinho não basta: exige nome completo, ou sobrenome
mais sigla do banco, ou sobrenome mais cargo.

**Por que isso importa, com número:** o painel mostrava 38 "discursos" para o AUD sem que
uma única fala do RBA tivesse sido lida — eram manchetes do Google News contadas como fala.
Até a manhã de 05/set elas ainda **votavam com peso 1,0**. Corrigido primeiro para JPY, AUD
e NZD; na tarde de 05/set a dimensão de texto parou de votar nas **oito** moedas, e o teto de
todas passou a ser 0,50.

Também é filtrado o **assunto**: cerimônia de cédula, aniversário, homenagem, prêmio, museu e
nomeação administrativa são descartados, com o motivo gravado. O BoC publicou a mesma
cerimônia de lançamento de cédula em duas páginas, e as duas entravam como fala de política
monetária. Nada some em silêncio: todo descarte fica registrado com a razão.

**Deduplicação:** republicação da mesma notícia é absorvida — no `bc_discursos` por link ou
por título normalizado; no `noticias` por Jaccard ≥ 0,70 sobre as palavras do título
normalizado. O representante do grupo é a fonte de maior peso, e o grupo **herda a maior
origem** entre os membros: se uma republicação traz a fala, o evento tem fala.

---

## 4. A winsorização — nenhuma divulgação manda sozinha

Dentro da dimensão de dados, **cada divulgação entra com no máximo 4,0 em módulo**, que é
0,8 do limiar de 5,0.

A garantia é **aritmética, não observação de um dia**: como 4,0 é estritamente menor que
5,0, nenhuma divulgação sozinha atinge o limiar. São precisas pelo menos duas. (O 0,8 é
PROVISÓRIO — é a menor folga que ainda deixa duas divulgações grandes virarem a leitura.)

**Houve uma versão anterior, reprovada por medição no mesmo dia.** Ela usava
`teto = min(2,5 × mediana absoluta da moeda ; 5,0)` e falhava nos dois pilares:

1. **A promessa era falsa.** O teto absoluto era o próprio limiar (5,0) e a comparação de
   direção é `soma ≤ −5,0`, com menor **ou igual**. O CAD provou: uma única divulgação (Net
   Change in Employment, bruta −7,82) foi cortada para exatamente −5,00, bateu no limiar e
   virou a dimensão para CORTE sozinha, com dominância de 100% antes **e depois** do teto.

2. **O fator da mediana fabricava e apagava direção.** A mediana é calculada sobre todos os
   itens da janela, e a maioria contribui quase nada depois do decaimento — então ela vive
   perto de 0,5 e o teto caía para ~1,2. Dois casos medidos:
   - 1 item de +7,83 com 17 itens de −0,50: a soma ia de −0,67 (MANUTENÇÃO) para −7,25
     (CORTE). **O teto fabricava uma direção.**
   - dois extremos legítimos do mesmo lado (−9,0 e −8,0) no meio de ruído de 0,4: a soma ia
     de −16,60 (CORTE) para −1,85 (MANUTENÇÃO). **O teto apagava dois dados legítimos.**

Com o teto fixo de 4,0 e sem o fator da mediana, os dois casos voltam a ler o que a soma
bruta lê: +4,0 − 8,5 = −4,5 (MANUTENÇÃO) e −4 −4 +0,4 −0,3 +0,5 −0,2 = −7,6 (CORTE).

**O que continua verdade e fica dito:** cortar termos de uma soma **desloca** o total pelo
tanto cortado, no sentido contrário ao do item. Isso é a definição de winsorizar, não um bug
escondido — é o preço de não deixar uma divulgação mandar sozinha. O deslocamento sai medido
por moeda em `deslocamento_pelo_teto`, e `direcao_antes_do_teto` mostra o que a soma bruta
teria lido. Os dois números ficam lado a lado, para quem quiser auditar.

**Alerta de dominância:** quando o maior item responde por mais de 50% da leitura de dados de
uma moeda, dispara um alerta em texto que aparece na moeda **e** em todos os pares que a
contêm. Hoje: *"uma única divulgação responde por 100% da leitura do CAD (Net Change in
Employment)"*.

---

## 5. As faixas — a zona neutra

**Divergência = |diferença entre as duas pernas| ÷ 1,00 × 100.**

| Faixa | Divergência | O que significa |
|---|---|---|
| **sem tese** | 0 – 14 | não há tese; o par sai da lista principal |
| **observação** | 15 – 24 | apenas observar |
| **moderada** | 25 – 39 | tese moderada — aguardar BO + ZOI |
| **forte** | 40 – 100 | tese forte |

**As quatro faixas são PROVISÓRIAS** e estão rotuladas como tal em toda parte da interface.
Elas foram escritas na régua de 0 a 100 sem olhar a distribuição real.

⚠️ **E elas foram desenhadas na escala VELHA.** Quando o denominador caiu de 1,50 para 1,00,
na tarde de 05/set, a mesma diferença econômica passou a sair 50% maior em pontos de
divergência, sem que nada tivesse acontecido no mercado. Medido nas 28 divergências da mesma
tarde: com o denominador 1,00 elas vão de 1 a 45, mediana 22, e a distribuição é
sem tese 12 · observação 5 · moderada 9 · **forte 2**; recalculadas no denominador antigo de
1,50, as mesmas leituras dariam sem tese 14 · observação 11 · moderada 3 · **forte 0**. Ou
seja: as duas únicas teses "fortes" do painel (EURUSD e NZDUSD, ambas 45%) existem por causa
da troca de denominador, não por causa do mercado. **Isto é exatamente o que o backtest tem
de calibrar** — e não vai ser calibrado no olho.

Par em "sem tese" sai com sinal `SEM_TESE` e ação "Sem tese", mas **continua gravado** no
arquivo com a divergência e as duas pernas: ele sai da lista, não do registro.

### A zona SEM LEITURA, por moeda (PROVISÓRIA)

A moeda fica **sem leitura** — sem direção na tela — quando a intensidade relativa
(|leitura contínua| ÷ teto teórico de 0,50, em %) fica **abaixo de 15%**, OU quando **menos de
2 dimensões votam**. Os dois números são PROVISÓRIOS.

Medido em 05/set: **2 das 8 moedas** ficam sem leitura — o JPY pelo piso de intensidade (5%) e
o NZD pela contagem de dimensões (nenhuma divulgação sua em 42 dias, então só o ciclo vota). O
GBP fica exatamente **em cima** do piso, com 15%.

⚠️ **O buraco conhecido:** a zona sem leitura vale para a MOEDA e **não é herdada pelo PAR**.
Na mesma leitura, **7 dos 16 pares com tese** têm ao menos uma perna sem leitura, e em **4
deles a perna sem leitura é justamente a perna que dá o motivo**. O caso extremo é o NZDUSD,
que sai como a tese mais **forte** do painel (45%) com a perna NZD marcada "sem leitura" e com
qualidade de evidência **0/100** nessa perna.

### O denominador é o teto TEÓRICO, e o motivo importa

A divergência é dividida por **1,00** — o teto teórico de duas pernas com duas dimensões
votando cada. **Não** pelo teto ligado do par.

A conta antiga dividia pelo teto **ligado**, que cai quando uma dimensão não está conectada.
O efeito medido: o CADCHF saía com divergência 17 e estado "observação" usando teto 1,25 (o
CHF não tem feed do SNB); com as duas pernas completas, a mesma diferença daria 14, que é
sem tese. **O par entrava na lista principal por ignorância, não por evidência.** EURAUD e
EURNZD estavam na mesma fronteira.

Isso não fere a lei "silêncio não é voto": a dimensão ausente continua fora do **numerador**
— o score soma só o que existe, nada vira zero. O que mudou é o **denominador**, que agora é
constante. Assim menos evidência significa divergência **menor**, que é o sentido honesto: a
falta de dado nunca deve empurrar um par para cima. O tamanho do buraco continua declarado à
parte, na qualidade da evidência. Os dois números ficam gravados lado a lado:
`divergencia` e `divergencia_pelo_teto_ligado`.

---

## 6. A qualidade da evidência

Nota de 0 a 100 por moeda, média de **quatro partes de 25**:

| Parte | O que mede |
|---|---|
| **quantidade** | divulgações e falas **que votam** na janela; satura em 12 itens |
| **diversidade** | quantas das 4 famílias independentes apareceram: inflação, emprego, atividade, comunicação |
| **atualidade** | idade do item que mais pesa, com meia-vida de 21 dias |
| **confiabilidade** | o peso da origem da fala (seção 3) |

**Parte sem dado sai `null` e não entra na média** — o denominador cai, a parte nunca vira
zero. Isso é a lei "silêncio não é voto" aplicada à própria nota: o CHF, que não tem feed do
SNB, saía com (67+75+94+0)/4 = 59, ou seja 20 pontos de penalidade por um buraco declarado.
Com a média sobre as três partes que existem, sai 79.

**Só o que vota conta como evidência.** Manchete que não vota fica de fora da conta e é
reportada à parte, em `contexto_nao_contado`. O NZD chegava a tirar 100/100 em quantidade
tendo **zero** divulgações e **zero** falas, sustentado por 42 manchetes que o próprio
coletor marca como `vota: false`.

**No par, vale a MENOR das duas pernas: o elo fraco manda.** E isso vai escrito no alerta.

Todos os números desta seção (saturação em 12 itens, meia-vida de 21 dias, 25 por parte) são
PROVISÓRIOS.

---

## 7. O que é look-ahead conhecido

O painel tem um **corte de tempo**, que esconde o que veio depois de uma data escolhida. Ele
**não deixa a tela limpa**, e o banner diz isso com todas as letras. Auditoria item a item:

| Item | Veredito |
|---|---|
| Usa valor **revisado** ou originalmente divulgado? | **LIMPO.** Usa o original. `divulgado` e `revisado` ficam em campos separados e a palavra "revisado" tem zero ocorrências no motor de sentimento. Comparando o campo `divulgado` por id de evento entre commits de dias diferentes, nenhum valor mudou — mas o *n* honesto dessa comparação é pequeno (15 e 66 eventos com valor nos dois lados), porque o calendário é janela rolante de ±42 dias. Refazer com 30+ dias de histórico. |
| Manchete publicada **depois** do corte é excluída? | **CONSERTO PARCIAL.** A lista da aba Notícias esconde as posteriores, e diz quantas escondeu. Mas a contagem já entrou no cálculo e não há como desfazer: a janela é de 72 h e não existe arquivo do Google News. Para qualquer corte com mais de 3 dias, **100%** das manchetes que pesaram são posteriores. |
| Os pesos e limiares de **hoje** são aplicados ao passado? | **CONTAMINA.** Todas as constantes são de módulo e o arquivo é um retrato de um instante. Não existe recomputação histórica. O único remédio é para frente: o snapshot congela a leitura de cada dia com a régua daquele dia. |
| As reuniões e taxas **atuais** contaminam uma data anterior? | **CONTAMINA.** O arquivo de bancos centrais traz taxa e último movimento sempre atuais, e a dimensão de ciclo mede a idade contra hoje. Com corte em 01/nov/2025, **seis dos oito** bancos têm decisão posterior ao corte. O banner nomeia quais, na data escolhida. |
| Os painéis obedecem ao corte? | **CONTAMINA.** Visão geral, Notícias, Pares e Calendário são repintados a cada 900 ms por um desenhador que não conhece o corte. Nesses quatro, o corte desenha no escondido. É a dívida técnica nº 1. |

**Consequência prática:** nenhum número visto sob o corte de tempo serve como amostra de
backtest. A amostra válida é o registro imutável, e só ele.

---

## 8. O snapshot — o registro imutável

`data/snapshots/AAAA-MM-DD.jsonl`, **append-only**: nunca reescreve linha antiga.

Sem ele a convicção histórica fica `null` para sempre, porque **a leitura de hoje não pode
ser reconstruída amanhã** — o calendário é buscado ao vivo e as manchetes têm janela de 72 h.

**Regra anti-entulho.** Não grava os 28 pares em toda rodada (seriam 2.688 linhas/dia de lixo
quase idêntico). Grava em três casos, com o motivo carimbado no campo `gatilho`:
primeira leitura do dia; mudança em direção, divergência ou qualidade; e a leitura
imediatamente após evento de impacto alto de uma das duas pernas.

**Cada linha se explica sozinha daqui a um ano.** Ela leva a conta por extenso
(`como_a_divergencia_saiu`: a diferença, o teto teórico, o teto ligado e o score de cada
perna) **e a régua em vigor naquele dia** (`regua_em_vigor`: faixas, limiar, winsorização,
decaimento do ciclo, pesos de fala). Sem a régua junto, a linha não é reconstruível: no
mesmo dia 05/set o AUDCAD saiu com divergência 37 às 04:17 e 25 às 04:20 com o mesmo
mercado — o que mudou foi a régua, e a linha antiga não dizia isso.

**A escrita tem trava exclusiva.** O modo "append" do Python **não é atômico no Windows**:
com dois processos escrevendo juntos, 9 de 25 rodadas terminaram com metade das linhas
sumidas, sem erro e sem linha corrompida para denunciar. Com trava, 0 de 25.

**Colunas em branco, para o operador preencher:** `bo_h4`, `zoi_m30`, `primeiro_toque`,
`entrada`, `resultado_r`. Nenhum robô escreve nelas. **Enquanto elas não forem preenchidas,
o snapshot é arquivo morto e a convicção histórica continua `null`.** É esse preenchimento
que fecha o ciclo.

---

## 9. As leis da casa que este método obedece

1. **Yield nunca entra no sentimento.**
2. **Nada de "score" na interface principal.** O número contínuo existe internamente e só
   aparece dentro de um expansível, com a legenda "não é probabilidade".
3. **Nenhuma promessa de probabilidade.** Convicção histórica só existe vinda de backtest, e
   hoje não existe: sai `null`.
4. **Silêncio não é voto.** Dimensão sem dado não conta e nunca vira zero — nem no score, nem
   na nota de qualidade, nem na contagem de concordância.
5. **Todo limiar novo é PROVISÓRIO** e tem de estar rotulado como tal, no código e na tela.
6. **A lei das duas pernas.** Par não é ativo, são duas moedas. Cada par sai com a perna que
   dá o motivo e o percentual dela, e com a lista dos pares que compartilham essa perna —
   dois deles não diversificam, dobram.

---

## 10. O que ainda está aberto

- **A faixa "forte" está vazia e é quase inalcançável** com a régua atual. As faixas precisam
  ser recalibradas pelo backtest, não pelo olho.
- **A contagem "pares com tese" não aplica a lei das duas pernas.** Quando vários pares com
  tese compartilham a mesma perna dominante, eles são a mesma aposta, e a contagem honesta é
  por perna, não por par.
- **A convicção histórica continua `null`** e vai continuar até a coluna do operador ter
  amostra.
- **O termo de reuniões de manutenção está desligado** até `bancos_centrais.py` guardar o
  histórico.
- **O corte de tempo é decorativo em quatro painéis** (dívida técnica nº 1).
- **Sobra inglês em abas legadas** (Juros, Spreads, Juros × Câmbio, Ações, COT, Fontes). São
  parágrafos longos de método — reescrita de conteúdo, não conserto pontual. A camada nova
  (Visão geral, Pares, Calendário, Notícias) está em português na fonte.
- **Títulos de indicador e manchetes continuam em inglês** porque são **dado**, não interface.

---

*HCI · hokiresearch.com — ferramenta de pesquisa. Não é recomendação de investimento.*
