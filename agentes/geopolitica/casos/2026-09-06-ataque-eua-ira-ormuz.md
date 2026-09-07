# evento/ataque-eua-ira — Estreito de Ormuz, 06/set/2026

```
versao_prompt   geopolitica@v1
assinatura      acao=ataque · entidades=[eua, ira]
mecanismo       M1 (energia) — rota de transporte
onde apareceu   mundo.conflito (as 7 moedas vieram sem manchete própria nesta rodada)
bloco           reaproveitado: true  (veio do cache, não de coleta nova)
numeros_citados z_conflito_mundo=1,06 · razao_conflito_mundo=1,1 · n=14 · recente_3d=3,2144
                base_14d=2,9231 · n_republicacoes=5 · duplicatas_removidas=4
```

## Manchete (título literal, e é o único material que existe)

> "Iran claims strike on US ship in Strait of Hormuz as fighting escalates"
> — wmtw.com, 06/09/2026 12:30 UTC, confiabilidade **baixa**
> https://www.wmtw.com/article/iran-us-war-strait-of-hormuz-ship/73624224

## M3 — o evento é novo?

**Parcialmente.** O ataque é fato datado ("claims strike"), o que é notícia. Mas três sinais
puxam para o outro lado: a razão de volume é **1,1** (o assunto está quase no seu ritmo normal
dos 14 dias, não é explosão), a manchete fala em **"as fighting escalates"** — ou seja, o
conflito **já estava em curso** —, e o bloco veio **`reaproveitado: true`**, isto é, cache de
rodada anterior.

**Leitura:** a escalada é incremental dentro de um conflito conhecido. Isso rebaixa a confiança
para **baixa** e, se a mesma assinatura reaparecer na próxima rodada sem fato novo, o veredito
seguinte é **já precificado**.

## M1 — o canal

Ormuz é **rota de transporte de energia**. Ataque a navio ali é risco de oferta de petróleo, não
"conflito genérico": o canal vai direto ao preço da energia e daí à inflação. É M1, não M2.

| Moeda | Papel | Veredito | Por quê |
|---|---|---|---|
| JPY, EUR, GBP, CHF, NZD | importadores líquidos | **pressão de alta** | energia mais cara → repasse a combustível, transporte e eletricidade → inflação para cima → juro para cima |
| CAD | exportador de energia | **sem direção** | o mesmo choque melhora os termos de troca e valoriza a moeda; o repasse doméstico é menor → efeito misto |
| AUD | exportador parcial (GNL, carvão) | **sem direção** | mesma lógica do CAD, mais fraca |
| USD | não coletado pelo arquivo | **não julgado** | `geopolitica.py` não coleta USD |

## A armadilha da fonte

`n_republicacoes = 5`, e as cinco são emissoras locais dos Estados Unidos — wtae, wesh, kcra,
wdsu, wmtw — publicando **o mesmo texto, com o mesmo id de artigo**. Isso é **um** despacho, não
cinco confirmações. A camada 1 já removeu **4 duplicatas** e classificou a confiabilidade como
**baixa**. Confiança do julgamento: **baixa**, e por essa razão.

Se houvesse a mesma notícia numa agência internacional ou num jornal financeiro de referência
(confiabilidade `alta`), a confiança subiria — mas o veredito continuaria o mesmo, porque
mecanismo não muda com o veículo.

## O que NÃO foi dito

Fluxo de refúgio (dólar, franco, iene recebendo fluxo) é **câmbio**, e não entra aqui como
veredito de juro. Ver `LAPIDES.md`, L4.

## Desfecho

```
reapareceu_em_rodada_seguinte   (a preencher — se sim e sem fato novo: já precificado)
preco_de_energia_reagiu         (a preencher: camada 1, não estimar)
prob_implicita_mudou            (a preencher: data/precificacao.json, só USD e AUD têm qualidade alta)
acertou                         (a preencher)
medido_em                       (a preencher)
```
