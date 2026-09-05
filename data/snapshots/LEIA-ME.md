# data/snapshots — REGISTRO IMUTAVEL

## A regra, antes de qualquer coisa

**Estes arquivos sao APPEND-ONLY. Nunca se edita nem se apaga uma linha ja gravada.**

Quem escreve aqui e o `snapshot.py`, e ele so sabe acrescentar. Se um numero de uma linha
antiga estiver errado, a correcao e uma **linha nova depois**, com carimbo novo — jamais um
retoque na linha velha. Todo o valor deste diretorio para o backtest vem disso: uma leitura
gravada nao pode ser reescrita pelo que se aprendeu depois. Reescrever uma linha aqui e a
mesma coisa que apagar o backtest.

Nao rode script nenhum que reordene, deduplique ou "limpe" estes arquivos. Linhas repetidas
com carimbos diferentes sao informacao (a leitura nao mudou entre dois instantes), nao lixo.

## O que e cada arquivo

`AAAA-MM-DD.jsonl` — um arquivo por dia, uma linha JSON por par por instante de gravacao.
O par aparece varias vezes no mesmo dia, com carimbos diferentes.

## Quando uma linha e gravada

A cadeia roda de 15 em 15 minutos. Gravar tudo em toda rodada dariam ~2.688 linhas por dia,
quase todas identicas. Entao grava-se quando:

1. e a **primeira leitura do par no dia** — sempre;
2. mudou a **direcao**, a **divergencia** ou a **qualidade da evidencia** em relacao a
   ultima linha daquele par no dia — qualquer um dos tres basta;
3. saiu um **evento de impacto alto** de uma das duas pernas depois da ultima linha —
   a leitura logo apos o evento entra mesmo se os tres numeros nao se mexeram. E
   justamente o "nao se mexeu com o NFP na mesa" que o backtest vai querer ler.

O campo `gatilho` de cada linha diz qual das tres regras a fez existir.

## O formato de uma linha

```json
{"gravado_em": "2026-09-05T12:34:56.789012+00:00",
 "par": "AUDCAD",
 "direcao": "COMPRA",
 "divergencia": 37,
 "qualidade_evidencia": 58,
 "estado": "moderada",
 "gatilho": "primeira_do_dia",
 "perna_dominante": {"moeda": "AUD", "share_pct": 85},
 "dados_disponiveis": {"ultimo_evento_utc": "2026-09-04T01:30:00+00:00",
                       "ultimo_evento_alto_utc": "2026-09-03T01:30:00+00:00",
                       "n_eventos_janela": 27, "n_falas": 19,
                       "fontes": ["bancos_centrais", "fxstreet", "manchetes_google_news"]},
 "proximo_evento_invalidante": {"moeda": "AUD", "evento": "RBA",
                                "data": "2026-09-29", "dias": 24},
 "preenchido_pelo_operador": {"bo_h4": null, "zoi_m30": null, "primeiro_toque": null,
                              "entrada": null, "resultado_r": null}}
```

`gatilho` e `dados_disponiveis.ultimo_evento_alto_utc` sao acrescimos ao contrato, ambos
aditivos: o primeiro para a auditoria saber por que a linha existe, o segundo porque e o
relogio que dispara a regra 3.

## O bloco do operador

`preenchido_pelo_operador` sai **todo em null**, de proposito. Nenhum robo escreve nele.
E o Eduardo que preenche a mao, depois, o que aconteceu com aquela leitura:

- `bo_h4` — houve rompimento na janela de 4 h?
- `zoi_m30` — o preco chegou na zona de 30 min?
- `primeiro_toque` — carimbo do primeiro toque
- `entrada` — entrou, e a que preco
- `resultado_r` — o resultado em multiplos de risco

Enquanto essa coluna estiver vazia nao ha backtest, e por isso o campo
`conviccao_historica` do painel continua saindo `null` com "ainda nao calibrada".

## O que uma linha NAO prova

A linha e o retrato do que o **painel de hoje** dizia naquele instante. Ela nao e imune a
tudo: os pesos e limiares usados sao os do dia da gravacao, e se a regua mudar amanha, as
linhas velhas continuam com a regua velha — o que e correto para o backtest e uma armadilha
para quem comparar linhas de meses diferentes sem olhar a data. Ver a auditoria de
look-ahead no banner do corte de tempo do painel.
