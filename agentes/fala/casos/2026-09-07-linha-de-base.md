# LINHA DE BASE DA REGRA — medida em 07/set/2026

```
versao_prompt   fala@v1
tipo            medição (camada 1), não julgamento
como recalcular python agentes/fala/mede_linha_de_base.py
saida           agentes/fala/linha_de_base.json
```

## O número

| Amostra | n | `indeterminado` | O que saiu com direção |
|---|---|---|---|
| `data/bis_discursos_historico.jsonl` inteiro | **1.319** | **99,7%** | 3 cortes, 1 alta |
| idem, só `assunto = politica_monetaria` | 581 | **99,8%** | 1 alta |
| `data/bc_discursos.json` (por orador) | 11 | **63,6%** | 2 manutenção, 1 alta condicional, 1 alta |
| `data/bis_discursos.json` (por orador) | 3 | **66,7%** | 1 alta |

Por moeda no histórico: AUD 440 (100% indeterminado), CHF 223 (99,6%), USD 173 (98,8%),
NZD 137 (100%), EUR 119 (100%), GBP 99 (100%), JPY 82 (100%), CAD 46 (97,8%).

Os quatro que escaparam saíram **do título**, não do conteúdo: "The rationale for discontinuing
the minimum exchange rate and lowering interest rates" (Jordan, SNB, 15/01/2015), "Cutting rates
in the face of conflicting data" (Waller, 16/10/2025), "The case for continuing rate cuts"
(Waller, 17/11/2025) e "Financial stability in a world of higher interest rates" (Rogers, BoC,
09/11/2023) — este último, aliás, é um **falso positivo**: "um mundo de juros mais altos" é
descrição de cenário, não postura de alta.

## O diagnóstico — e ele muda tudo

**Os 99,7% não medem a regra. Medem a entrada.** O histórico do BIS guarda `titulo` e
`resumo_bis`, e o resumo é a linha bibliográfica do BIS: *"Speech by Mr X, Governor of Y, at Z,
cidade, data"*, com **174 caracteres de mediana**. Não há postura ali para regra nenhuma achar,
nem para IA nenhuma achar.

Três consequências, todas duras:

1. **A linha de base que vale é a dos arquivos vivos: 63,6%.** É esse número que o agente tem de
   baixar — sem inventar direção, ou trocou um problema por outro pior.
2. **Metade do teto está fora do alcance do agente:** 6 dos 12 itens vivos chegam com **zero
   frases** extraídas. Sem corpo, não há leitura — só `nao_julgados` com o link que falta.
3. **O histórico não valida conteúdo.** Serve para o esqueleto ponto-no-tempo (quem falou, de que
   banco, em que data) e para a memória. Para validar julgamento, a camada 1 precisa baixar os
   corpos; o agente na nuvem não baixa nada.

## Pedidos à camada 1 que este caso justifica

1. Guardar o **corpo** (ou pelo menos 20 frases, não 5) em `bc_discursos.json` e
   `bis_discursos.json` — hoje 50% dos itens chegam mudos.
2. Construir `data/decisoes_historico.jsonl` (data, banco, resultado: subiu/manteve/cortou).
   Sem ele não existe alvo, não existe **taxa-base de manutenção** e não existe validação —
   `data/bancos_centrais.json` só traz a última decisão, e `data/calendario_arquivo/` começa em
   setembro de 2026.
3. Baixar os corpos dos discursos históricos do BIS, se um dia a validação de conteúdo for feita.

## Desfecho

```
re_medir_quando   a camada 1 passar a guardar o corpo
numero_novo       (a preencher)
comparacao        (a preencher: caiu de 63,6% para quanto, e sem inventar direção?)
```
