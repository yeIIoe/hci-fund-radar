# evento/sancoes-canada-eua — guerra comercial Canadá-EUA, 08/set/2026

```
versao_prompt   geopolitica@v1
assinatura      acao=sancoes · entidades=[canada, eua]
mecanismo       M3 barrou (comentário, não fato) — M2 seria o canal se houvesse fato
onde apareceu   mundo.energia (a consulta de energia capturou "trade war"/"tariff")
veredito        já precificado · confiança baixa
numeros_citados z_energia_mundo=0,25 · razao_energia_mundo=1,03 · n=14 · recente_3d=1,1813
                base_14d=1,1468 · n_republicacoes=3 e 1 · duplicatas_removidas=2
```

## As duas manchetes — e por que viraram UM julgamento

> "Canada - U.S. trade war takes centre stage at Toronto annual Labour Day parade"
> — cbc.ca, 08/09/2026 01:30 UTC, confiabilidade **media**, 3 republicações, entidades `[canada, eua]`
> https://www.cbc.ca/news/canada/toronto/canada-us-trade-war-toronto-labour-day-parade-9.7334984

> "Counter - tariff fallout could be ugly, expert warns"
> — cbc.ca, 07/09/2026 15:00 UTC, confiabilidade **media**, 1 republicação, entidades `[]`

A régua entregou os dois como itens **separados** de `manchetes_unicas`. É o **buraco 2 declarado**
no próprio arquivo: *"evento com uma entidade só não agrupa (exige 2 em comum)"* — o segundo título
não tem nenhuma entidade do léxico, então nem chegou à regra 2, e a regra 1 (Jaccard de palavras)
não bate entre "trade war parade" e "counter-tariff fallout".

Mesmo veículo, mesma ação `sancoes`, mesmo assunto. **Fundidos em um julgamento**, como manda a
seção 6 do prompt e a lápide L1.

## M3 — o evento é novo? **Não.**

| Pergunta do M3 | Resposta |
|---|---|
| assinatura já julgada? | não, é a primeira vez que `sancoes-canada-eua` aparece |
| `razao` perto de 1? | **1,03**, e `z` **0,25** — o assunto está exatamente no seu ritmo normal dos 14 dias |
| bloco `reaproveitado`? | não (`mundo.energia` não traz a marca) |
| **título anuncia FATO ou comenta?** | **comenta.** Um é cobertura de um desfile em que o tema apareceu; o outro é especialista dizendo o que *"could be"* |

A pergunta 4 decide sozinha. Nenhum dos dois títulos traz alíquota, data de vigência ou retaliação
formalizada. **Comentário não é evento** — e o volume, parado em razão 1,03, concorda.

## M2 — o canal, se houvesse fato

Tarifa entre Canadá e EUA é **M2 (crescimento)**, não M1, apesar de as manchetes terem sido pescadas
pela consulta de *energia*. A pergunta obrigatória do M2 — *isto tira oferta do mercado, ou só tira
confiança?* — se responde sozinha: nenhum dos títulos fala em corte de oferta de petróleo, gás ou
insumo. Tira **confiança**.

Se a próxima rodada trouxer fato datado, o canal M2 aponta **pressão de baixa** no juro do CAD
(exportação mais fraca → crescimento mais fraco). Em **cenário condicional**, e só então.

## A armadilha desta rodada

O CAD não teve **nenhuma** manchete própria (`CAD/energia: HTTP Error 429`, conflito com lista
vazia). A tentação era usar estas manchetes de `mundo` como se fossem julgamento do CAD. Não são:
ficam como **evento**, com as moedas tocadas nomeadas no motivo. Um evento, uma linha.

## Desfecho

```
reapareceu_com_fato_datado   (a preencher — alíquota, data, retaliação formalizada)
razao_energia_subiu          (a preencher: camada 1, não estimar)
juro_do_CAD_reagiu           (a preencher: data/precificacao.json — CAD está SEM FONTE hoje)
acertou                      (a preencher)
medido_em                    (a preencher)
```
