# evento/energia-eua-ira-fala-preco-petroleo — a previsão que não é fato, 08/set/2026

```
versao_prompt   geopolitica@v1
assinatura      acao=energia · entidades=[eua, ira]
mecanismo       M3 barrou na pergunta 4 (título é previsão, não fato datado)
onde apareceu   mundo.energia
veredito        indeterminado · confiança baixa
numeros_citados z_energia_mundo=0,25 · razao_energia_mundo=1,03 · n_republicacoes=1
```

## A manchete

> "Trump says oil prices will drop precipitously, gas could fall below $2 after US wins Iran war"
> — moneycontrol.com, 08/09/2026 03:15 UTC, confiabilidade **baixa**, 1 republicação
> https://www.moneycontrol.com/world/trump-says-oil-prices-will-drop-precipitously-gas-could-fall-below-2-after-us-wins-iran-war-article-14024746.html

## Por que este caso existe

Ele é o **espelho invertido** do caso de Ormuz de 06/set. Mesmas entidades `[eua, ira]`, mesma
região, mesmo conflito de fundo — e o canal de energia apontando para o **lado oposto**:

| Item de hoje | Ação | Canal M1 se fosse fato | Direção nos importadores |
|---|---|---|---|
| ataque a navio em Ormuz (`mundo.conflito`, cache de 06/set) | `ataque` | oferta de petróleo em risco | **para cima** |
| esta declaração (`mundo.energia`) | `energia` | petróleo mais barato | **para baixo** |

Um agente apressado somaria os dois e chamaria de "escalada". São vetores contrários dentro do
mesmo conflito, e o certo é não somar nada.

## M3 — o teste que barrou

O item é de hoje e a assinatura nunca foi julgada. Mas a **pergunta 4** derruba: o título não diz
o que **aconteceu**, diz o que alguém **prevê** — *"will drop"*, *"could fall"*, *"after US wins"*.
É uma **declaração**, e na hierarquia de falas da casa manchete de declaração tem peso mínimo.

Três coisas que o título **não** estabelece, e que eu não posso inventar:

1. que a guerra terminou;
2. que houve acordo, cessar-fogo ou liberação da rota;
3. que o preço do petróleo de fato caiu — isso é número, e número vem medido da camada 1, nunca
   de estimativa minha (lápide L7).

Deduzir "a guerra acabou, logo o petróleo cai, logo os importadores desinflacionam" a partir desta
frase seria **previsão militar**, vetada pela lápide **L6**.

## A lei que este caso escreve

> **Declaração não é evento — e uma declaração não revoga um ataque.**
> Quando o título é o que alguém *diz que vai acontecer*, o veredito é `indeterminado`. O canal
> fica descrito no motivo, para a rodada em que o fato aparecer.

## Nota de deduplicação

**Não** fundi este item com o de Ormuz, apesar das entidades idênticas. A `acao` é outra
(`energia` contra `ataque`), o conteúdo é outro, e a régua fez certo em separá-los. Fundir aqui
seria deduplicar **de mais** — o erro que a camada 1 evita por decisão declarada.

## Desfecho

```
houve_fato_datado_depois     (a preencher — cessar-fogo, acordo, rota liberada)
preco_de_energia_reagiu      (a preencher: camada 1, não estimar)
ormuz_foi_revogado           (a preencher — o ataque de 06/set perdeu efeito?)
acertou                      (a preencher)
medido_em                    (a preencher)
```
