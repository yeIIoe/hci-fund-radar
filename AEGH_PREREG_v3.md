# PRÉ-REGISTRO — AEGH v3 · os dois desfechos do Found

**Assinado em 31/ago/2026, antes de qualquer execução.**
Desfechos e as cinco correções metodológicas: Eduardo. Desenho e critérios: Claude.

> **Histórico de versões — resultado negativo é ativo, inclusive o meu.**
> **v1** desenhou o Teste 1 como previsão direcional isolada. Errado: é o que os 15
> pré-registros já reprovaram.
> **v2** corrigiu para pergunta condicional (o FUND filtra a entrada técnica?).
> **v3** incorpora cinco correções do Eduardo — período congelado, aprovação por
> expectativa líquida, controle de amostra aleatória, calibração de verdade, e a
> separação entre custo medido e custo estimado.

---

## LEI QUE VALE PARA OS DOIS TESTES

> Sustentação fundamental e resultado direcional são **dimensões distintas**. Uma tese pode
> manter suas premissas enquanto o câmbio se move contra o lado indicado. Ausência de dados
> é **indeterminação**; nenhum dos dois desfechos, isoladamente, comprova rentabilidade.

**Proibido usar o resultado de um teste como prova do outro.**

---

## 🔒 PERÍODO CONGELADO — a especificação abaixo não muda depois de rodar

Nada aqui pode ser ajustado após a primeira execução. Qualquer alteração cria uma
**variante nova**, que entra no registro de tentativas com número próprio e volta ao fim
da fila. É o que impede escolher o parâmetro depois de ver o resultado.

### Congelado: as três entradas técnicas

| # | disparo exato | lado | família |
|---|---|---|---|
| **T1** | `close[t] > max(high[t-20 … t-1])` (ou `<` mínima) | direção do rompimento | rompimento |
| **T2** | `close[t-1] < média20 − 2×desvio20` **e** `close[t] > close[t-1]` (espelhado para cima) | contra o toque | reversão |
| **T3** | `média50` cruza `média200` no dia *t* | direção do cruzamento | tendência |

- Médias e desvio: **simples**, sobre o **fechamento do fixing do BCE**, janela em **pregões**.
- T2 exige o toque em *t−1* e a virada em *t*: **o toque sozinho não dispara.**

### Congelado: execução e gestão

| item | regra |
|---|---|
| **Entrada** | fixing de **t+1**. Nunca o fechamento que gerou o sinal. |
| **Saída** | horizonte fixo: **t+1+h**, com h = 5, 20, 60 pregões. Sem stop, sem alvo. |
| **Tamanho** | **1 unidade por sinal**, sempre. Sem dimensionamento por convicção. |
| **Sinais sobrepostos** | permitidos, **contados uma vez por par**. Novo sinal no mesmo par e mesma direção com posição aberta **não abre outra**; direção contrária **substitui**. |
| **Sem posição** | dia sem sinal é dia sem exposição — entra no cálculo de exposição, não no de expectativa. |

Sem stop e sem alvo **de propósito**: este teste mede o valor do *filtro*, não de uma
regra de gestão. Gestão entra depois, se o filtro passar.

---

# TESTE 1 — o FUND filtra a entrada técnica?

## A pergunta
Dado que uma entrada técnica disparou, **o FUND concordar com aquele lado melhora o
resultado da estratégia** — não só o da operação média?

## Dados
- 28 pares, fixing diário do BCE, 2002-01-04 a 2026-08-24 — **148.473 linhas**.
- FUND: **o valor que o próprio site calcula**. O recálculo próprio reprovou na calibração
  (corr 0,915, erro mediano 9,2). Alinhamento **medido**: `projection.outcome` do dia D é o
  FUND de **D+2** (corr 0,996, erro 0,0000, 97,9% idênticos contra 7.280 pontos datados).

## O filtro
FUND do **mesmo dia do sinal** (execução em t+1):
**CONCORDA** `|FUND| ≥ 25` e mesmo sinal · **DISCORDA** `|FUND| ≥ 25` e sinal contrário ·
**NEUTRO** `|FUND| < 25`.

## ⚖️ O que decide a aprovação — e o que NÃO decide

**Decide: a expectativa LÍQUIDA por operação.** Taxa de acerto não aprova nada sozinha.

**E não basta a operação média.** Um filtro pode melhorar cada trade e eliminar tantas
oportunidades que **o resultado da estratégia piora**. Por isso todo relato traz, sempre
junto e nunca isolado:

| métrica | por quê |
|---|---|
| **Expectativa líquida por operação** | o critério principal |
| **Número de operações** | o filtro cortou quanto? |
| **Exposição** | fração de dias-par com posição aberta |
| **Resultado acumulado** | o que o filtro faz com a estratégia inteira |
| **Drawdown máximo** | melhora que vem com cauda pior não é melhora |

**Reprova** se a expectativa por operação melhorar mas o resultado acumulado piorar.

## As comparações — e a interpretação correta

1. **CONCORDA vs sem filtro** — valor de aceitar só sinais alinhados.
2. **CONCORDA vs DISCORDA** — o alinhamento direcional distingue resultados?
3. **NEUTRO vs sem filtro** — como se comporta a zona intermediária.
4. **🎲 CONCORDA vs SUBCONJUNTO ALEATÓRIO** — o controle que separa seleção informativa
   de mera redução de exposição.

### O controle aleatório, em detalhe
Sorteio subconjuntos dos sinais **sem filtro** com o **mesmo número de operações** que o
CONCORDA produziu, **preservando aproximadamente a distribuição por período e por par**
(amostragem estratificada por ano × par). **1.000 sorteios.** O CONCORDA precisa ficar
acima do percentil 95 dessa distribuição.

Sem isso, qualquer corte de amostra que reduza exposição em período ruim pareceria filtro.

### ⚠️ Ausência de diferença NÃO é prova de equivalência
Se CONCORDA e DISCORDA não diferirem de forma demonstrável, **a contribuição direcional
não está aprovada** — mas isso **não prova que os grupos são iguais**. Amostra pequena
produz inconclusivo, não equivalência.

Por isso todo resultado nulo vem com **intervalo de confiança e poder estatístico
declarados**. Célula com menos de **200 sinais** é reportada como **INCONCLUSIVA**, nunca
como "sem efeito".

## Controles estatísticos
1. **t agrupa por DATA** — 28 pares num dia compartilham choque.
2. **Cluster duplo: data × moeda** — 28 pares saem de 8 moedas.
3. **Purga e embargo** onde as janelas se sobrepõem (h=20, h=60).
4. **Split temporal:** 2002-2014 exploração · 2015-2019 validação · **2020-2026 CEGO,
   aberto uma vez só.**

## Critérios de APROVAÇÃO — os cinco
1. **Expectativa líquida do CONCORDA > sem filtro** em ≥ 2 das 3 entradas técnicas, com
   **t ≥ 2,0** (cluster duplo), em ≥ 2 dos 3 horizontes.
2. **Resultado acumulado não piora** — o corte de oportunidades não come o ganho.
3. **CONCORDA > DISCORDA** na mesma direção.
4. **CONCORDA acima do percentil 95** do controle aleatório pareado.
5. Sobrevive no **cego 2020-2026** com ≥ **metade** do tamanho de efeito, **após custo e
   haircut de 50%**.

## O que reprova na hora
- Expectativa por operação melhora, acumulado piora.
- Ganho só aparece agregando as três entradas.
- Efeito concentrado em um par ou um ano.
- CONCORDA não bate o sorteio pareado.

## O rótulo se reprovar — na tela, não em rodapé
> **Coerência fundamental, isoladamente, não aprova a utilidade direcional do Score.**
> Enquanto não demonstrada, os pares são **candidatos para análise, sem vantagem comprovada.**

---

# TESTE 1b — ordenar confiança ≠ calibrar probabilidade

## A distinção que governa este teste
**Monotonicidade é evidência de ORDENAÇÃO, não calibração.** Mais `|FUND|` associado a mais
acerto é bom resultado — e **não basta** para transformar score em percentual.

### Etapa 1 — ORDENAÇÃO
Faixas de `|FUND|`: 25-40, 40-60, 60-80, 80-100.
**Avaliadas SEPARADAMENTE em CONCORDA e em DISCORDA.**

> FUND forte **contra** a entrada técnica não pode significar mais confiança naquela
> entrada. Se as duas curvas subirem juntas, o que a faixa mede é volatilidade ou regime —
> não convicção direcional.

**Passa** se a taxa de sucesso for monotônica no CONCORDA **e não** no DISCORDA.

### Etapa 2 — CALIBRAÇÃO (só se a etapa 1 passar)
1. Estimar a relação faixa → sucesso **numa amostra** (2002-2014).
2. Verificar a correspondência **em outra** (2015-2019), e só então no cego.
3. Reportar **Brier**, curva de calibração, **incerteza e n por faixa, visíveis**.
4. Referência de método: [calibração, scikit-learn](https://scikit-learn.org/stable/modules/calibration.html).

⚠️ **Enquanto a etapa 2 não passar, a confiança é exibida como faixa qualitativa.**
Um 8/10 não vira "80% de acerto" sem a curva verificada fora da amostra.

---

# 💰 CUSTOS — o que é medição e o que é estimativa

Misturar os dois é como tratar chute e régua igual. A tabela separa:

| componente | natureza | fonte |
|---|---|---|
| **Spread** | ✅ **MEDIDO** | bid × ask m1 da Dukascopy, 24-38 dias por par, mediana e p90 |
| **Comissão** | 🟡 **A CONFIRMAR** | ftmo.com/symbols diz `5 USD/LOT`. **Não está declarado se é por perna ou round turn.** Confirmar na plataforma. Enquanto não confirmar, roda com os **dois** valores. |
| **Swap** | 🟡 **ESTIMATIVA histórica** | reconstruído do diferencial de 2 anos, calibrado contra a FTMO em **um dia** (r=0,975). A FTMO informa que as condições **podem mudar**. Não há série histórica de swap real. |

## Regras de custo
1. **Três cenários obrigatórios:** medido · medido +50% · medido +100%. Achado que só
   sobrevive no cenário barato **não passa**.
2. **Swap respeita instrumento, direção e calendário de cobrança** — quarta-feira cobra 3×.
   Direção importa: o mesmo par tem custo diferente comprado e vendido.
3. **NÃO presumir que o swap domina em 20 ou 60 pregões.** Eu afirmei isso na v2 **sem ter
   medido** — a afirmação sai daqui e vira **uma medição a reportar**: qual a fração do
   custo total que é swap, por horizonte.
4. A **fonte de cada número** aparece no relatório, com a etiqueta medido/estimado.

---

# TESTE 2 — persistência e deterioração

## A pergunta
O sistema identifica **continuidade, enfraquecimento e invalidação** das premissas —
inclusive nas posições escolhidas pelo Eduardo?

## Por que não é o Teste 1 outra vez
Entrada exige **previsão**; saída exige **detecção**. A transmissão juro→preço que medimos
é **contemporânea** (+0,430 em 120d) e não preditiva — inútil para antecipar, e é
exatamente o que uma saída precisa: perceber a tese morrendo **enquanto** morre.

## A premissa, definida SEM o Score
> **O Score permanecer alto não é prova de persistência.** (Eduardo)

### ⚠️ Regra EXPERIMENTAL, escopo limitado — não universal
O Eduardo recusou tratar a definição abaixo como regra geral, e com razão:

> **Válida SOMENTE para tese originada no diferencial de juro de 2 anos.**
> A premissa se sustenta enquanto o diferencial mantiver o sinal que originou a tese.
> É invalidada quando cruza zero **ou** devolve ≥ 50% do movimento que a criou.

**Isto não se aplica a premissa fundamental de outra natureza** — mudança de regime de
política, choque fiscal, prêmio de risco. Cada família de premissa precisa da sua própria
condição de invalidação, registrada antes.

Como o FUND V0.1 **é** momento do diferencial de 2 anos, a regra cobre o que existe hoje.
Quando o Found ganhar premissas de outra natureza, **este teste não as cobre.**

## O que é medido
| métrica | definição |
|---|---|
| **Tempo até detectar** | dias entre a invalidação e o alerta |
| **Alerta falso** | alerta e a premissa **não** é invalidada em 20 dias |
| **Não detectado** | premissa invalidada e **nenhum** alerta em 10 dias |
| **Sobrevivência** | tempo em banda por regime — **descritivo, não é prazo** |

## 🚨 CORREÇÃO DO EDUARDO (31/ago) — o teste tem de exigir contribuição ADICIONAL

> Se a invalidação é apenas cruzar um nível do diferencial de juros, **um alerta simples já
> faz isso**. O agente precisa demonstrar alguma contribuição adicional — por exemplo,
> identificar corretamente **qual premissa** está sendo afetada e explicar a mudança com
> evidências.

Está certo, e desmonta o desenho anterior. Detectar o cruzamento de zero é **aritmética de
uma linha**: qualquer `if` faz. Se o teste medisse só isso, aprovaria um `if` e chamaria de
agente.

Então a referência **não é mais** o alerta ingênuo como adversário fraco — ele passa a ser
o **piso obrigatório**, e o que se mede é o que existe **acima** dele.

## Referência: PISO, não adversário
**Alerta ingênuo:** dispara quando o diferencial cruza zero ou devolve 50%.
Ele detecta por construção. **Empatar com ele é reprovar.**

## Critérios de APROVAÇÃO — os quatro
1. **Tempo mediano de detecção menor** que o do ingênuo (bootstrap, IC declarado).
2. **Taxa de alerta falso não maior** que a do ingênuo.
3. **🎯 CONTRIBUIÇÃO ADICIONAL — o critério que decide.** Não basta detectar. É preciso:
   - **identificar corretamente QUAL premissa** está sendo afetada (política monetária,
     crescimento, inflação, prêmio de risco), verificado contra amostra anotada; **e**
   - **explicar a mudança com evidência rastreável** — evento, surpresa contra o consenso
     disponível na época, e a fonte, com data de publicação.

   Medida: **precisão factual** = alegações verificadas corretas ÷ alegações auditadas.
   Uma explicação que não aponta fonte conta como **errada**, não como omissa.
4. Sobrevive no cego 2020-2026.

## O que este teste autoriza, se passar — e o que NÃO autoriza
> Autoriza dizer **"acompanha esta premissa"**.
> **Não** autoriza dizer "prevê o câmbio" nem "melhora entradas".

E o Teste 2 é **avaliação independente, não salvação do Score**. Passar aqui não reabre
nada do Teste 1: são dimensões distintas, e a Lei no topo deste documento proíbe usar um
como prova do outro.

## O que reprova
- Detectar mais rápido comprando com mais alerta falso.
- Alertar só **depois** que o preço andou — aí é o preço avisando, não o fundamento.
- Alertar em todo dia de dado novo.

## Sem prazo
A tese **não tem duração fixa** — dias ou meses. Sem espera obrigatória, sem vencimento
automático, sem saída por tempo. Horizontes são janela de teste.

---

## 🚦 O PORTÃO — o que só roda depois de passar

Nenhum destes entra em produção antes do teste correspondente passar:

| o que | destravado por |
|---|---|
| FUND exibido como **filtro** de entrada técnica | Teste 1 |
| Confiança exibida como **percentual** | Teste 1b etapa 2 |
| Alerta de deterioração como **acompanhamento de premissa** | Teste 2 |
| Alerta de deterioração como **sinal de saída de operação** | ⛔ **nenhum teste autoriza hoje** |
| Agentes 2 a 6 e a nuvem do AEGH | Teste 1 |

Até lá o painel mostra **candidatos para análise, sem vantagem comprovada** — e essa frase
fica visível, não escondida em rodapé.

---

## Registro de tentativas

| # | data | teste | variante | resultado | cego |
|---|---|---|---|---|---|
| 0 | 31/ago | painel | recálculo próprio do FUND | **REPROVOU na calibração** (corr 0,915) — trocado pelo valor do site | — |
| **1** | **31/ago** | **Teste 1** | **T1/T2/T3 × h 5/20/60, banda 25, custo medido** | **REPROVOU na exploração** — 0 de 9 células acima do p95 do sorteio pareado | **fechado** |

## O que este pré-registro NÃO autoriza
- Não autoriza operar. Nenhum desfecho mede rentabilidade.
- Não autoriza mexer no FUND V0.1. Congelado.
- Não autoriza construir os agentes 2 a 6 antes do Teste 1 sair.

## Assinaturas
- **Desfechos e as cinco correções**: Eduardo, 31/ago/2026.
- **Desenho e critérios de reprovação**: Claude, 31/ago/2026, antes de executar.

---

# ⚖️ VEREDITO — Tentativa 1 · Teste 1 na exploração

**Assinado pelo Eduardo em 31/ago/2026, após o resultado.**

> A versão avaliada do FUND não atingiu os critérios de aprovação como filtro de
> entradas técnicas.
>
> Nos três setups e nos horizontes de 5, 20 e 60 pregões, **nenhuma das nove combinações
> superou o percentil 95 do controle aleatório pareado**, conforme os resultados
> reportados. As melhorias observadas em algumas métricas não demonstraram capacidade de
> seleção superior à redução de operações representada pelo controle.
>
> **Decisão:** encerrar esta tentativa como **reprovada na exploração** e manter fechado o
> período reservado de **2020-2026**.
>
> **Alcance:** a conclusão aplica-se à versão do FUND, aos setups, à amostra, às regras e ao
> modelo de custos utilizados. **Não demonstra impossibilidade de contribuição do fundamento
> em qualquer estratégia.**
>
> **Limitações:** custos históricos aproximados por referências posteriores; incerteza
> estatística e dependência entre operações devem acompanhar o relatório. O padrão positivo
> em 60 pregões fica registrado como **observação exploratória**, sem aprovação nem
> interpretação causal.
>
> Novas variantes exigem justificativa própria, identificação de tentativa e protocolo
> congelado antes da avaliação. **Não alteram retrospectivamente o resultado desta tentativa.**

## Os números que sustentam o veredito

| critério | resultado |
|---|---|
| 1 — expectativa líquida do CONCORDA > sem filtro | 3 de 9 células |
| 2 — acumulado não piora | 6 de 9 |
| 3 — CONCORDA > DISCORDA | 3 de 9 |
| **4 — acima do p95 do sorteio pareado** | **0 de 9** |
| 5 — cego | **não aberto** |

| entrada | h | n CONCORDA | C − sem filtro | C − DISCORDA | t |
|---|---|---|---|---|---|
| T1 rompimento 20d | 5 | 824 | −0,0068 | −0,0721 | 0,52 |
| T1 rompimento 20d | 20 | 820 | −0,0750 | −0,1966 | −2,11 |
| T1 rompimento 20d | 60 | 802 | +0,1515 | +0,0072 | −0,97 |
| T2 reversão 2σ | 5 | 281 | −0,2328 | −0,2549 | −0,98 |
| T2 reversão 2σ | 20 | 280 | −0,1312 | −0,3075 | 0,13 |
| T2 reversão 2σ | 60 | 274 | +0,0680 | +0,1160 | −0,50 |
| T3 cruzamento 50/200 | 5 | 296 | −0,0745 | −0,0031 | −2,13 |
| T3 cruzamento 50/200 | 20 | 294 | −0,2774 | −0,3785 | −2,25 |
| T3 cruzamento 50/200 | 60 | 292 | +0,1039 | +0,3693 | 0,14 |

## O que o controle pareado revelou — e por que ele foi decisivo

O controle aleatório entrou na v3 por correção do Eduardo. **Foi ele que impediu um falso
achado.**

No T1 em 60 pregões o acumulado do CONCORDA é **−170** contra **−849** do sem-filtro:
parece corte de prejuízo de cinco vezes. Mas o CONCORDA tem **um terço das operações**, e
um sorteio aleatório com o mesmo n faz igual. **O que parecia seleção era redução de
exposição.**

Sem esse controle, as células de 60 pregões teriam sido lidas como sinal.

## Observação exploratória, sem estatuto de achado
Os três setups dão diferença positiva em h=60 (+0,15 · +0,07 · +0,10). Nenhuma com t
significativo, nenhuma passando o sorteio. Coincide com o horizonte onde a transmissão
juro→preço é mais forte (+0,430 em 120d) — mas **contemporânea, não preditiva**.
Fica como direção não contrariada, não como resultado.

## Ressalva do executor
O custo aplicado usa **spread de 2026 sobre dado de 2002-2014** — anacrônico e para baixo,
já que o spread era maior naquela época. Isso **favorece** as estratégias, e mesmo assim
todas perdem. Não altera a conclusão; fica registrado.
