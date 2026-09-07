# z alto sem manchete nenhuma — 07/set/2026

```
versao_prompt   geopolitica@v1
tipo            caso de NÃO-julgamento (e é o julgamento certo)
arquivo         data/geopolitica.json, gerado_em 2026-09-07T02:45:35Z
```

## O que a rodada trouxe

| Moeda | conflito `z` | conflito `razao` | manchetes únicas | energia `z` |
|---|---|---|---|---|
| GBP | **2,05** | 1,43 | **0** | −0,41 |
| EUR | 0,44 | 1,09 | 0 | 0,56 |
| AUD | −0,51 | 0,82 | 0 | — |
| CHF | −0,13 | 0,91 | 0 | — |
| CAD | −1,49 | 0,49 | 0 | — |
| JPY | — | — | 0 | −0,50 |
| NZD | — | — | 0 | −0,40 |

Manchetes cruas somadas em **todas** as moedas: **zero**. `tom`: `null` nas sete.
`erros`: sete blocos com **HTTP 429** e *"orçamento de 480 s estourado antes de CAD"*.

## O julgamento

**Todas as sete moedas vão para `nao_julgados`.** O USD vai junto, com outro motivo: ele **não é
coletado** por `geopolitica.py`.

## Por que o GBP é o caso exemplar

`z = 2,05` está **acima do limiar de 1,5** que dispara a implicação automática da camada 1. A
implicação foi escrita: *"aversão a risco: efeito misto para o GBP (regra)"* — e ela nasceu de um
número de volume, **sem uma única manchete** dizendo do que se tratava.

Um agente que julgasse pelo z produziria uma frase sobre o Reino Unido sem saber se o assunto era
um ataque, um cessar-fogo, uma eleição ou cinco jornais republicando a mesma matéria. As quatro
possibilidades empurram o juro para lados diferentes.

> **Volume não é direção.** É a frase que derrubou o voto desta dimensão em 05/set, e ela vale
> tanto para a regra quanto para o agente.

## O que se escreve numa rodada assim

```json
{"chave": "GBP",
 "porque": "z de conflito 2,05 mas ZERO manchete coletada (HTTP 429) — o volume diz que há assunto e não diz qual; sem manchete não há mecanismo, e z não é direção"}
```

E em `limites`: a lista de erros, copiada. E `estado: "sem dados"` em `data/agentes/indice.json`.

**Um painel que diz "sem dado hoje" é honesto.** Um painel que inventa direção a partir de um z
solto é o erro que a lápide L2 registra.

## Pedidos à camada 1 que este caso justifica

1. Reduzir o consumo do orçamento de 480 s, ou dividir a coleta em rodadas por moeda, para que a
   lista de manchetes deixe de vir vazia.
2. **Coletar o USD** — é a moeda mais exposta a evento global e é a que falta.
3. Gravar uma **série diária** de `geopolitica.json` (hoje o arquivo guarda só a rodada atual).
   Sem série não há n, e sem n não há teste — e é o teste que destrava o voto.

## Desfecho

```
rodada_seguinte_teve_manchete   (a preencher)
frequencia_de_rodada_vazia      (a preencher: contar em historico.jsonl, é a camada 1 que conta)
medido_em                       (a preencher)
```
