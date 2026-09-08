# CAD — o próprio banco diz "mantivemos", a casa lê corte, e não há preço para desempatar

```
caso            2026-09-08-CAD-noticia-contra-a-casa-sem-preco
moeda           CAD
rodada_id       divergencia-20260908T1534Z
versao_prompt   divergencia@v1
veredito        SEM FONTE
lado_ausente    mercado
confianca       baixa
destaque        null   (falta a condição 2: sem preço de qualidade alta não existe destaque)
proxima_reuniao 2026-10-28 (Bank of Canada, 10:45 BRT — 50 dias)
estado          aberto
```

## As três colunas, como estavam no instante do julgamento

| coluna | valor | número citado | arquivo e carimbo |
|---|---|---|---|
| **A — casa** | `inclinado ao corte` (direção `CORTA`) | intensidade **28%** do teto · convicção **25 de 50** · **2 de 4** dimensões votando · qualidade da evidência **24/100** | `data/sentimento.json` · `2026-09-08T15:24:03Z` |
| **B — mercado** | **`null`** | **p_alta `null` · p_corte `null` · p_manutencao `null`** · qualidade **sem fonte** · taxa atual 2,25 | `data/precificacao.json` · `2026-09-08T14:14:10Z` |
| **C — notícia** | **`manutenção`** | `fala:CAD/Macklem` confiança **alta**; `noticia:CAD` indeterminado, confiança baixa | `fala@v1` · `2026-09-08T15:14:33Z` · `noticia@v1` · `2026-09-08T15:20:00Z` |

Trecho da coluna C, literal, do comunicado do próprio Banco do Canadá:
> *"With recent data coming out largely in line with our July forecast, we decided to
> maintain the policy interest rate at 2.25%."*
> — https://www.bankofcanada.ca/2026/09/opening-statement-2026-09-02/ (via `fala@v1`)

Motivo da ausência da coluna B, **copiado literalmente** de `precificacao.moedas.CAD.detalhe.motivo`:
> *"futuros: Bolsa de Montreal (COA, One-Month CORRA Futures) serve preco por widget
> QuoteMedia com sessao presa ao dominio: getFuturesChain.json -> Invalid product.;
> getEnhancedQuotes.json -> HTTP 403 | manchete: 1 manchete(s) de veiculo aceito na janela,
> nenhuma passou na regua da proxima reuniao"*

## Por que este caso foi registrado
É a **única moeda da rodada em que a coluna C aponta para o lado oposto da casa**, e o
desempate não existe: não há preço. A casa lê corte com qualidade de evidência **24/100** —
a segunda pior das oito — enquanto o governador do banco em questão anuncia manutenção, com
o texto oficial na mão. Isso **não move o veredito** (na v1 a coluna C não vota, e sem preço
não há comparação), mas é exatamente o tipo de contraste que o painel tem obrigação de
mostrar em vez de resolver em silêncio.

## O que o painel disse, palavra por palavra
> Não existe comparação a fazer: falta a coluna do mercado. […] O ponto desta linha: a coluna
> C existe e aponta para o lado OPOSTO da casa. […] Isso NÃO move o veredito: na v1 a coluna
> C não vota, e sem preço não há comparação a fazer.

## Limites declarados na hora
- O buraco do preço do CAD é **técnico**, não de manchete: a Bolsa de Montreal serve preço
  por widget com sessão presa ao domínio. Se a coleta for consertada, **abrir caso novo**.
- `noticia:CAD` = indeterminado (confiança baixa). Indeterminado **não** é manutenção e
  **não** é neutro: só a linha do `fala` sustenta a coluna C aqui.
- A reunião é em **50 dias**. Uma postura anunciada em 02/set não é promessa sobre outubro,
  e a distância até a decisão está declarada ao lado do caso, não escondida.
- Nada aqui é recomendação. Este agente não vota, e não há convicção histórica.

---

## DESFECHO — **preencher DEPOIS da decisão do BoC de 28/10/2026**

```
data_da_decisao   ____-__-__
o que o banco fez  ____
o que a casa lia   inclinado ao corte (CORTA), qualidade da evidência 24/100
o que o preço pagava (não havia preço)
o que a notícia lia  manutenção (confiança alta), comunicado do próprio BoC
quem estava mais perto ____
estado             aberto
```

**O que aprendi:**
*(em branco)*

**Cuidado:** este caso só é mensurável de um lado — a casa contra a notícia. A divergência
"casa × preço", que é o produto deste agente, **não existiu** aqui, e nenhum desfecho pode
ser lido como se tivesse existido.
