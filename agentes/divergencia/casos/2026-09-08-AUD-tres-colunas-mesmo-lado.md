# AUD — as três colunas existem e apontam para o mesmo lado

```
caso            2026-09-08-AUD-tres-colunas-mesmo-lado
moeda           AUD
rodada_id       divergencia-20260908T1534Z
versao_prompt   divergencia@v1
veredito        ALINHADO
confianca       alta
destaque        null   (conferido e não marcado — ver abaixo)
proxima_reuniao 2026-09-29 (Reserve Bank of Australia, 01:30 BRT — 21 dias)
estado          aberto
```

## As três colunas, como estavam no instante do julgamento

| coluna | valor | número citado | arquivo e carimbo |
|---|---|---|---|
| **A — casa** | `inclinado à alta` (direção `SOBE`) | intensidade **73%** do teto · convicção **50 de 50** · **2 de 4** dimensões votando · qualidade da evidência **80/100** | `data/sentimento.json` · `2026-09-08T15:24:03Z` |
| **B — mercado** | `alta` | **p_alta 0,66** · **p_corte 0,0** · **p_manutencao 0,34** · implícito **+16,5 bp** · qualidade **alta** | `data/precificacao.json` · `2026-09-08T14:14:10Z` |
| **C — notícia** | `alta condicional` (agente `noticia`, `noticia@v1`) | confiança **média** · 1 leitura | `data/agentes/noticia/ultimo.json` · `2026-09-08T15:20:00Z` |

Fonte da coluna B, literal do arquivo: *futuros IB (30 Day Interbank Cash Rate, ASX) via
asx.api.markitdigital.com — a API do ASX RBA Rate Tracker*; contrato `IBV2026` (volume 201),
base 4,3500% do cadastro, que fecha com o mercado **dentro de 0,0 bp**.

Trecho da coluna C, literal:
> *"RBA's Hunter Says Inflation Top Priority, May Have to Raise Rate - bloomberg.com"*
> — https://news.google.com/rss/articles/CBMitAFBVV95cUxNdEI4RW5nR2FfbHg3VDlua2pVRlB… (via `noticia@v1`)

## Por que este caso foi registrado
É a **primeira linha do painel em que as três colunas existem ao mesmo tempo**, e a única
desta rodada. Nas outras sete, ou falta o preço (cinco moedas sem fonte), ou falta a leitura
da casa (USD), ou o preço só dá direção (NZD). É também o caso que **desarma** o destaque
que o dono quer ver: a notícia aperta **e o preço se mexeu junto**.

## O que o painel disse, palavra por palavra
> A casa lê o AUD "inclinado à alta" (direção SOBE, intensidade 73% do teto, convicção 50 de
> 50, 2 de 4 dimensões votando, qualidade da evidência 80/100); o mercado paga "alta", com
> p_alta 0,66, p_manutencao 0,34 e p_corte 0,0 (qualidade alta, implícito 16,5 bp); a coluna
> C traz 1 leitura para o AUD: `noticia:AUD` = alta condicional (confiança média). A leitura
> da casa e o preço apontam para o mesmo lado.

## Limites declarados na hora
- **Destaque conferido e NÃO marcado.** A condição 1 da seção 6 vale (aperto com confiança
  média), a condição 2 vale (preço de qualidade alta), mas a **condição 3 não**:
  `direcao_mercado` é `alta` e `p_manutencao` 0,34 **não** é a maior das três. É o oposto do
  caso que o destaque procura.
- Ressalva copiada do arquivo de preço: a conferência pelo mês da reunião *"NÃO vale como
  segunda medida"* — sobra 1 dia depois da decisão e a conta amplifica o ruído em 30x.
- Concordância entre três colunas **não é convicção**. Não há backtest: a convicção
  histórica deste agente é `null`.
- Nada aqui é recomendação. Este agente não vota.

---

## DESFECHO — **preencher DEPOIS da decisão do RBA de 29/09/2026**

```
data_da_decisao   ____-__-__
o que o banco fez  ____
o que a casa lia   inclinado à alta (SOBE)
o que o preço pagava alta (p_alta 0,66)
o que a notícia lia  alta condicional (confiança média)
quem estava mais perto ____
estado             aberto
```

**O que aprendi:**
*(em branco)*

**Cuidado:** as três colunas concordarem não torna o evento mais provável — torna a
divergência **ausente**. Um acerto aqui não valida nada: com as três do mesmo lado, qualquer
leitor acertaria igual. O caso serve para medir se ALINHADO significa alguma coisa.
