# USD — a casa ficou sem leitura e o preço continua pagando alta

> Sucessor do caso semeado `2026-09-07-USD-casa-le-corte-mercado-paga-alta.md`. **A coluna A
> daquele caso não existe mais**: em 07/set a casa lia "inclinado ao corte" (direção CORTA,
> intensidade 36%); hoje a leitura caiu abaixo do mínimo e virou "sem leitura". O caso velho
> continua aberto como registro; este é o estado de hoje.

```
caso            2026-09-08-USD-casa-ficou-sem-leitura
moeda           USD
rodada_id       divergencia-20260908T1534Z
versao_prompt   divergencia@v1
veredito        SEM FONTE
lado_ausente    hci
confianca       baixa
destaque        null   (conferido e não marcado — ver abaixo)
proxima_reuniao 2026-09-16 (Federal Reserve, 15:00 BRT — 8 dias)
estado          aberto
```

## As três colunas, como estavam no instante do julgamento

| coluna | valor | número citado | arquivo e carimbo |
|---|---|---|---|
| **A — casa** | **`sem leitura`** (campo `direcao` = `MANTEM`) | intensidade **14%** do teto · convicção **25 de 50** · **2 de 4** dimensões votando · qualidade da evidência **38/100** | `data/sentimento.json` · `2026-09-08T15:24:03Z` |
| **B — mercado** | `alta` | **p_alta 0,5786** · **p_corte 0,0** · **p_manutencao 0,4214** · implícito **+14,46 bp** · qualidade **alta** | `data/precificacao.json` · `2026-09-08T14:14:10Z` |
| **C — notícia** | **`contraditoria`** — 5 leituras | ver a tabela abaixo | `fala@v1` · `2026-09-08T15:14:33Z` · `noticia@v1` · `2026-09-08T15:20:00Z` |

### A coluna C, inteira — porque resolvê-la em silêncio é proibido

| leitura | veredito | confiança | trecho literal |
|---|---|---|---|
| `fala:USD/Waller` | **manutenção** | alta | *"If this continues in the data due over the next two weeks, I would be inclined to support holding the target for the fed…"* |
| `fala:USD/Barr` | **alta condicional** | média | *"However, if inflation appears not to be moderating sufficiently, then I think we should act decisively to raise rates."* |
| `fala:USD/Warsh` | indeterminado | alta | *"…when policymakers make quasi-commitments on interest rates through the cycle, we inhibit our own freedom…"* |
| `fala:USD/Lisa D Cook` | indeterminado | baixa | *"I would consider how a rate increase could negatively affect that stability."* |
| `noticia:USD` | indeterminado | baixa | *"COMMENTARY: Trump's baffling Fed threat could be gift to Warsh: Mike Dolan - Reuters"* |

**Não escolhi entre elas.** Há uma postura firme (manutenção) e uma condicional de aperto,
então a coluna C sai `contraditoria`, com as cinco versões de prompt gravadas.

## Por que este caso foi registrado
Porque o veredito de hoje **não é** o de ontem, e a razão não é o mercado: é a **casa que
emudeceu**. O preço não mudou (mesmo `p_alta 0,5786`), a reunião está mais perto (8 dias), e
a comparação deixou de existir porque a coluna A saiu do ar. Este é o caso-tipo da lápide
**L-H7 — silêncio não é voto**: seria fácil ler o campo `direcao: MANTEM` do arquivo e
declarar "casa neutra × mercado comprado = HCI MAIS DOVISH". Seria falso. `sem_leitura` é
porta de saída, não linha da tabela.

## O que o painel disse, palavra por palavra
> Silêncio da casa não é MANTEM: sem direção do lado HCI não existe comparação a fazer,
> mesmo com o preço medido e de qualidade alta.

## Limites declarados na hora
- **Destaque conferido e NÃO marcado.** Existe aperto na coluna C (`fala:USD/Barr`, alta
  condicional, confiança média), mas o preço **se mexeu para o mesmo lado**: `p_manutencao`
  0,4214 não é a maior das três. A condição 3 da seção 6 falha.
- A leitura da casa está frágil por dentro: qualidade da evidência **38/100**, convicção
  **25 de 50**, e a intensidade (14%) está **um ponto** abaixo do mínimo provisório de 15% —
  ou seja, a fronteira entre "sem leitura" e "inclinado" é fina, e o limiar é **provisório**.
- Waller é o nome da lápide **L-H6**: a contagem de palavras o marcou como hawkish quando
  ele defendia **manter**. Aqui quem leu foi o agente `fala`, com trecho e link, e o veredito
  dele é **manutenção**. Eu não classifico fala; só cito.
- Nada aqui é recomendação. Este agente não vota, e não há convicção histórica.

---

## DESFECHO — **preencher DEPOIS da decisão do FOMC de 16/09/2026**

```
data_da_decisao   ____-__-__
o que o banco fez  ____
o que a casa lia   sem leitura (nenhuma direção)
o que o preço pagava alta (p_alta 0,5786)
o que a notícia lia  contraditória: manutenção (alta) x alta condicional (média)
quem estava mais perto ____
estado             aberto
```

**O que aprendi:**
*(em branco)*

**Cuidado:** se o Fed subir, a tentação será dizer que "a casa errou". A casa **não disse
nada** — e não dizer nada não é errar. O que este caso mede é outra coisa: quantas vezes a
coluna A desliga justamente na semana da reunião.
