# EUR — reunião do BCE em três dias e nenhuma fonte para comparar

> ⚠️ **Caso semeado à mão em 07/set/2026**, a partir de `data/sentimento.json` e
> `data/precificacao.json` daquela data. Existe para fixar o formato do veredito
> **SEM FONTE**, que é o mais frequente do painel hoje — cinco das oito moedas — e o mais
> fácil de degenerar em comparação inventada.

```
caso            2026-09-07-EUR-sem-fonte-para-comparar
moeda           EUR
rodada_id       (semeado — sem rodada)
versao_prompt   divergencia@v1
veredito        SEM FONTE
lado_ausente    mercado
confianca       baixa
destaque        null
proxima_reuniao 2026-09-10 (Banco Central Europeu, 09:15 BRT — 4 dias)
estado          sem desfecho
```

## As três colunas, como estavam no instante do julgamento

| coluna | valor | número citado | arquivo e carimbo |
|---|---|---|---|
| **A — casa** | `inclinado à alta` (direção `SOBE`) | intensidade **78%** do teto · convicção **50 de 50** · **2 de 4** dimensões votando · qualidade da evidência **85/100** | `data/sentimento.json` · `2026-09-06T23:34:07Z` |
| **B — mercado** | **`null`** | **p_alta `null` · p_corte `null` · p_manutencao `null`** · qualidade **sem fonte** · taxa atual 2,25 (depósito) | `data/precificacao.json` · `2026-09-07T02:44:32Z` |
| **C — notícia** | — | — | nenhum agente da camada 2 havia gravado saída |

Motivo da ausência, **copiado literalmente** de `precificacao.moedas.EUR.detalhe.motivo`:
> *"manchete: nenhum item de Reuters/Bloomberg/FT/WSJ com ate 7 dias entre os 119
> resultados lidos"*

## Por que este caso foi registrado
É o caso-limite mais tentador do painel: a leitura da casa é **forte** (a mais intensa das
oito, 78% do teto, com convicção no máximo) e a reunião é **em quatro dias**. Exatamente a
situação em que dá vontade de arranjar uma comparação. Não há. O veredito honesto é
**SEM FONTE**, e isso é informação: diz ao leitor que o painel não sabe se essa leitura
está dentro ou fora do preço.

## O que o painel diria, palavra por palavra
> A casa lê o EUR inclinado à alta (intensidade 78% do teto, convicção 50 de 50, 2 de 4
> dimensões votando); não há precificação para o BCE — nenhum futuro da própria taxa de
> política e nenhuma manchete de veículo aceito com número amarrado à próxima reunião entre
> os 119 resultados lidos —, então p_alta, p_corte e p_manutencao estão todos `null`; não há
> agente de notícia nesta rodada. **Não existe comparação a fazer.**

## Limites declarados na hora
- `frescor.bloqueia_leitura = true` — sentimento **3h39** atrasado.
- Cinco moedas estão neste mesmo estado hoje: **EUR, GBP, JPY, CAD e CHF**. No CAD o buraco
  não é falta de manchete e sim técnico: a Bolsa de Montreal serve preço por widget com
  sessão presa ao domínio (`getFuturesChain.json -> Invalid product`). No JPY houve duas
  manchetes de veículo aceito na janela, mas nenhuma passou na régua da próxima reunião.
- Proibido preencher `p_*` com estimativa, com a taxa atual, com o consenso de economistas
  ou com o que o painel "acha". Buraco declarado é buraco declarado.

---

## DESFECHO

```
estado             sem desfecho
por que            não há comparação a medir: uma das duas colunas não existe.
```

Se a coleta de precificação do EUR passar a funcionar, **abrir caso novo** a partir daquele
dia. Este caso permanece como registro do buraco, com a data — é assim que se prova depois
que o painel não inventou a divergência quando não tinha fonte.
