# HCI FUND Radar

Painel local de direção fundamental para swing em Forex.

## Abrir

Clique duas vezes em `ABRIR_HCI_FUND_RADAR.bat`. O navegador abre em
`http://127.0.0.1:8765`. Mantenha a janela preta aberta enquanto usa o painel.

## O que o painel faz

- lê yields soberanos de 2 anos para USD, EUR, GBP, JPY, AUD, CAD, NZD e CHF;
- calcula os 28 cruzamentos com o FUND V0.1 congelado;
- mostra força relativa, matriz e detalhe histórico por par;
- mantém um calendário diário de 01/01/2002 até o presente;
- em cada dia, mostra moedas mais forte/fraca e até cinco pares direcionais;
- roda backtest por par ou nos 28 pares, com período e custo em pips;
- usa fixing cambial diário oficial do ECB e executa o sinal somente no dia seguinte;
- mostra notícias futuras da semana e cenários de impacto por moeda;
- bloqueia a prioridade atual quando qualquer perna está atrasada ou vencida;
- sinaliza perda de faixa do FUND para gestão de saída;
- antecipa quais pares ainda neutros podem entrar em FUND BEAR no próximo dia;
- mantém separado o teste direto de queda do preço no próximo fixing.

O painel não executa ordens. FUND escolhe o lado; BO, REGIÃO, ZOI e timing são
confirmados manualmente.

## Radar pré-FUND

Este motor usa somente a informação disponível em D e considera pares que ainda
não estão vendedores (`FUND > -25`). Ele estima a chance de o par entrar em
`FUND <= -25` no próximo dia útil, para que a ZOI possa ser observada antes da
confirmação oficial. Isso não autoriza entrada antecipada.

A validação é walk-forward anual: em cada ano, o modelo e os pesos só conhecem
os anos anteriores. Em 54.089 amostras PIT causais, a taxa-base de uma virada
para BEAR foi 7,15%. O candidato número 1 do radar virou BEAR em 27,08% dos
dias, e o top 5 capturou 93,11% das transições.

O replay de 06/01/2026 colocou NZDJPY em primeiro e EURJPY em segundo entre 11
pares elegíveis. Ambos ainda estavam NEUTRAL naquele dia e entraram em BEAR em
07/01, reproduzindo os dois exemplos de ZOI enviados.

O melhor motor foi apenas a proximidade do nível −25. Acrescentar trajetória ou
preço não melhorou a seleção. A probabilidade exibida no site é a frequência
empírica fora da amostra da faixa de calibração, não o número bruto do modelo.
O painel só mostra para observação probabilidades pelo menos 25% maiores que a
taxa-base histórica do evento.

## Queda direta do preço D+1

Este teste permanece separado do pré-FUND. Ele considera pares operacionais já
vendedores (`FUND <= -25`) e tenta ordenar qual cairia no próximo fixing.

No tribunal de 2002 a 2026, nenhum conjunto passou. O melhor resultado observado
foi o FUND puro, com 50,07% no candidato número 1 (IC 95%: 48,67%–51,47%). Os
pesos aprendidos ficaram em 49,56%. Entre os alertas pré-FUND, o preço caiu no
fixing seguinte em apenas 48,38% dos candidatos número 1. Portanto o edge
encontrado é antecipar a futura faixa do FUND, não prever a queda D+1.

## Calendário histórico

O calendário é causal: a recomendação de uma data usa somente as leituras FUND
disponíveis naquele dia. Não usa o PF calculado com resultados posteriores.

- `COMPLETA 8/8`: as oito moedas e os 28 pares têm leitura válida;
- `PARCIAL`: mostra apenas pares cujas duas pernas existiam naquele dia;
- `FECHADO`: fim de semana ou dia histórico sem fixing ECB; nenhuma recomendação;
- primeira data `COMPLETA 8/8`: 27/08/2009.

A cobertura anterior é parcial porque a curva oficial EUR 2Y usada começa em
06/09/2004 e o benchmark soberano NZD 2Y começa em 29/01/2009. O sistema não
substitui essas lacunas por proxies silenciosas.

## Fontes históricas

- USD: US Treasury, arquivos anuais da curva diária;
- EUR: ECB, curva AAA spot de 2 anos;
- GBP: Bank of England, GLC nominal spot de 2 anos;
- JPY: Ministry of Finance Japan, JGB 2 anos;
- AUD: RBA F2 histórico direto e série atual RBA via DBnomics;
- CAD: Bank of Canada Valet, benchmark 2 anos;
- NZD: RBNZ B2 histórico e atual;
- CHF: SNB, Confederation spot rate 2 anos;
- preços FX: fixing diário ECB desde 2002.

## Atualizar

Use o botão **Atualizar** dentro do painel. Também é possível executar
`ATUALIZAR_FUND.bat` sem abrir o servidor. Arquivos históricos encerrados ficam
em cache; a rotina atualiza as séries correntes.

## Escopo do backtest

O backtest disponível no painel isola o motor FUND:

- entrada quando o FUND sai da faixa NEUTRAL;
- execução no próximo fixing diário do ECB;
- saída quando o FUND perde uma faixa de força;
- custo total configurável em pips.

Ele não inclui BO, REGIÃO, ZOI, SL ATR nem candles de 30 minutos. Pares que
envolvem AUD ou CHF aparecem como `PROVISIONAL_PIT`, pois os lotes históricos
dessas fontes não preservam precisamente a data de publicação de cada
observação.

O calendário de notícias é contexto secundário. Confirme horário e release na
fonte oficial antes de operar.
