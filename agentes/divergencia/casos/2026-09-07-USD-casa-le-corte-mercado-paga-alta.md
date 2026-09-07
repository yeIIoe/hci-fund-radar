# USD — a casa lê corte, os futuros pagam alta

> ⚠️ **Caso semeado à mão em 07/set/2026**, a partir de `data/sentimento.json` e
> `data/precificacao.json` daquela data, para que o agente tenha um exemplo concreto de
> formato ao acordar sem contexto. **Não é saída de rodada**: não existe `rodada_id` real e
> a coluna C está vazia porque nenhum agente de notícia havia rodado ainda.

```
caso            2026-09-07-USD-casa-le-corte-mercado-paga-alta
moeda           USD
rodada_id       (semeado — sem rodada)
versao_prompt   divergencia@v1
veredito        HCI MAIS DOVISH
confianca       baixa
destaque        null   (a coluna C não existe: sem agente de notícia, não há destaque)
proxima_reuniao 2026-09-16 (Federal Reserve, 15:00 BRT — 10 dias)
estado          aberto
```

## As três colunas, como estavam no instante do julgamento

| coluna | valor | número citado | arquivo e carimbo |
|---|---|---|---|
| **A — casa** | `inclinado ao corte` (direção `CORTA`) | intensidade **36%** do teto · convicção **25 de 50** · **2 de 4** dimensões votando · qualidade da evidência **86/100** | `data/sentimento.json` · `2026-09-06T23:34:07Z` |
| **B — mercado** | `alta` | **p_alta 0,5786** · **p_corte 0,0000** · **p_manutencao 0,4214** · implícito **+14,46 bp** · qualidade **alta** | `data/precificacao.json` · `2026-09-07T02:44:32Z` |
| **C — notícia** | — | — | nenhum agente da camada 2 havia gravado saída |

Fonte da coluna B, literal do arquivo: *futuros de fed funds 30d (ZQ, CME) via API de
gráfico do Yahoo + EFFR do NY Fed*; contrato `ZQU26.CBT`, base EFFR 3,6300% de 03/09.

## Por que este caso foi registrado
É a divergência mais larga do painel e a mais fácil de ler errado: a casa lê **corte** com
apenas duas das quatro dimensões votando, enquanto o preço não paga corte nenhum
(`p_corte = 0,0000`) e paga **alta** com quase 58%. Faltam dez dias para o FOMC.

## O que o painel diria, palavra por palavra
> A casa lê o USD inclinado ao corte (intensidade 36% do teto, convicção 25 de 50, 2 de 4
> dimensões votando); os futuros de fed funds pagam alta, com p_alta 0,5786 contra
> p_manutencao 0,4214 e p_corte 0,0000 (qualidade alta); não há agente de notícia nesta
> rodada. A casa está mais dovish que o preço.

## Limites declarados na hora
- `frescor.bloqueia_leitura = true` — o sentimento estava **3h39** atrasado
  (`atraso_min: 219`, estado `muito_atrasado`). Toda a rodada sairia com confiança baixa.
- A dimensão de dados do USD só virou para `CORTA` **depois** da winsorização: a soma antes
  do teto era −1,19 (direção `MANTEM`) e depois dos cortes ficou −9,15. O próprio arquivo
  registra que cortar itens **deslocou** a soma em −7,96 e **mudou a direção**. Isso é
  fragilidade da coluna A e tem de estar escrito ao lado do veredito.
- Coluna C ausente: sem ela não se pode dizer nada sobre "a notícia aperta e o preço não se
  mexeu".
- Nada aqui é recomendação. Não há convicção histórica: este agente nunca foi medido.

---

## DESFECHO — **preencher DEPOIS da decisão do FOMC de 16/09/2026**

```
data_da_decisao   ____-__-__
o que o banco fez  ____
o que a casa lia   inclinado ao corte
o que o preço pagava alta (p_alta 0,5786)
quem estava mais perto ____
estado             aberto
```

**O que aprendi:**
*(em branco)*

**Cuidado:** uma reunião não é amostra. Nem acerto nem erro aqui mudam o estatuto do
agente, que continua sem voto e sem convicção histórica.
