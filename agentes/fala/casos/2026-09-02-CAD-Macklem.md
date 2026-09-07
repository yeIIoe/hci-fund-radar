# CAD/Macklem — 02/set/2026

```
versao_prompt   fala@v1
veredito        manutenção
confianca       alta
fonte           "Monetary Policy Decision Press Conference Opening Statement" (BoC)
link            https://www.bankofcanada.ca/2026/09/opening-statement-2026-09-02/
origem          comunicado_ata (peso 1,0)
numeros_citados frases_analisadas=2 · peso_da_fonte=1,0 · forca_da_regra=4
```

## Trecho que decidiu

> "With recent data coming out largely in line with our July forecast, **we decided to maintain
> the policy interest rate at 2.25%**."

## Motivo

É o **anúncio da decisão**, escrito no passado porque anuncia o que acabou de ser decidido. A
postura descrita está **em vigor**, não é recibo de um movimento superado. Veredito:
**manutenção**, força firme.

## A armadilha: passado que não é passado

O veto de tempo verbal foi desenhado para discurso ("subimos 425 pb em 2022" não diz nada sobre o
próximo passo). Aplicado ao **comunicado** — a fonte de maior peso da hierarquia — ele calava
justamente quem mais tem autoridade: as duas falas do BoC de 02/set saíam com "nenhuma frase de
postura foi extraída do texto", uma afirmação falsa sobre o anúncio de decisão do próprio banco.

A distinção é **semântica, não remendo**:

- "decidimos **manter** / **deixar inalterado**" → efeito continua valendo → **conta**
- "**subimos** 425 pb em 2022" → já foi substituído pelas decisões seguintes → **não conta**

Por isso a exceção vale **só** para verbo de decisão seguido de manutenção. Para alta e corte,
passado continua sendo passado.

## Nota de coleta

O outro item do BoC no mesmo dia (a coletiva, mesmo peso) chegou com **zero frases** e caiu em
`nao_julgados`. Dois itens do mesmo evento, um legível e outro não — é o pré-filtro da camada 1,
não o conteúdo.

## Divergência com a regra

Nenhuma hoje. Havia até 06/set, quando a regra não conhecia as flexões `held` / `maintains` /
`decided to maintain`.

## Desfecho

```
decisao_seguinte_do_banco   (a preencher: próxima reunião do BoC)
resultado                   (subiu | manteve | cortou)
acertou                     (a preencher)
medido_em                   (a preencher)
```
