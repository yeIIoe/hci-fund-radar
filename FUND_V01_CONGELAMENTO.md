# 🧊 FUND V0.1 — CONGELAMENTO

**Decisão do Eduardo, 31/ago/2026.** Versão experimental, **reprovada nos testes de
utilidade direcional**. Congelada como está, com fórmula, dados, resultados e limitações
preservados — para que a próxima tentativa parta daqui e não do zero.

---

## 1. A FÓRMULA — congelada, bit a bit

```
spread[t] = yield_2a(base) − yield_2a(quote)
raw[t]    = spread[t] − spread[t−20]                        LOOKBACK   = 20
z[t]      = (raw[t] − média(raw anteriores)) / desvio        NORM_WINDOW = 252
                                                             MIN_HISTORY = 126
FUND[t]   = 100 × tanh(z[t] / 2),  limitado a ±100
```

**Bandas:** `|FUND| ≥ 60` forte · `≥ 25` direcional · `< 25` neutro.

**Detalhe que não pode ser perdido:** o índice é a **união** das duas séries de yield, com
`ffill(limit=5)`. As janelas de 20 e 252 contam **linhas desse índice**, não dias de
calendário. Reproduzir isso de fora falhou (ver §4).

Fonte oficial: `hci_fund_radar/update_fund.py`, constantes em `:64-67`, cálculo em
`compute_pair:815`.

---

## 2. OS DADOS

| item | valor |
|---|---|
| Universo | 8 moedas · 28 pares |
| Insumo | yield soberano de 2 anos, por moeda, de fontes oficiais distintas |
| Preço | fixing diário do BCE |
| Painel reconstruído | **148.473 linhas · 2002-01-04 a 2026-08-24** |
| Arquivo | `C:\Trading\hci-ea\out\aegh_painel.parquet` |

**Cadência desigual, e isso importa:** o AUD publica **semanalmente** (RBA). O painel não
corrige isso; a defasagem entra como está.

---

## 3. OS RESULTADOS — o que foi testado e o que deu

### 3.1 Como preditor direcional isolado — REPROVADO 15×
15 pré-registros, 15 nulos: absoluto, gate, rank-1, cross-sectional, quintis, surpresa,
carry, horizonte longo, repetição, níveis públicos, saídas no S/R, reforço, veto.
**Nenhuma construção previu direção em nenhum horizonte de 1 a 120 dias.**

### 3.2 Como filtro de entrada técnica — REPROVADO (31/ago/2026)
3 setups × 3 horizontes, exploração 2002-2014. **0 de 9 células acima do p95 do controle
aleatório pareado.** O que parecia seleção era **redução de exposição**.
Protocolo e veredito: `AEGH_PREREG_v3.md`.

### 3.3 A transmissão que SOBREVIVE — e o que ela não autoriza
`transmissao_yield_preco.py`, 147.590 pares-dia, 25 anos:

| horizonte | contemporâneo | preditivo |
|---|---|---|
| 20 dias | +0,370 | +0,002 |
| **120 dias** | **+0,430** (pico) | **−0,046** |

**O juro MANDA no preço; não ANTECIPA.** Isso não autoriza uso em entrada. Deixa aberta a
pergunta de **detecção** — que é o Teste 2, e é avaliação independente, não salvação.

### 3.4 O que o pré-FUND acerta, e o limite dele
O radar pré-FUND antecipa a **própria mudança de banda do FUND** — não o preço.
Taxa-base de virada para BEAR 7,15%; candidato nº 1 em 27,08%; top 5 captura 93,11%.
No teste de queda de preço em D+1, **nenhum conjunto passou**: o melhor foi 50,07%
(IC 48,67-51,47) — cara-ou-coroa.
**O edge é antecipar a faixa do FUND, não prever o câmbio.**

---

## 4. AS LIMITAÇÕES — declaradas, não escondidas

**Reprodução externa falha.** Recalcular o FUND a partir dos yields do calendário dá
correlação 0,915 contra o valor oficial, erro mediano 9,2 pontos, casos de 64. Causa: o
`update_fund` monta cada moeda de fontes com datas próprias, e as janelas contam linhas
desse índice. **Quem for estudar o FUND deve usar o valor que o site publica.**

**Alinhamento não óbvio.** O `projection.outcome` gravado no dia D é o FUND de **D+2** —
medido contra 7.280 pontos datados (corr 0,996, erro 0,0000, 97,9% idênticos). Supor D+1
desloca o estudo inteiro.

**Custo histórico é aproximação.** O spread medido é de 2026; aplicá-lo a 2002-2014 é
anacrônico e **para baixo**. O swap é estimativa reconstruída, calibrada contra um único
dia da corretora.

**Artefato de relógio já ocorreu uma vez.** O "+0,107 em 1 dia" era diferença de fuso entre
o fixing do BCE e o fechamento do yield. Sumiu com 1 dia de folga. **Teste de gap antes de
reportar qualquer defasada.**

**Cadência desigual** entre moedas (AUD semanal) não é corrigida.

---

## 5. O QUE FOI RETIRADO DA TELA

| era | virou | por quê |
|---|---|---|
| "FUND sets direction" | **"Painel de pesquisa. O FUND não decide direção."** | ele não decide |
| "Tradable now" | **"Candidatos para análise"** | não há vantagem comprovada |
| **BUY BASE / SELL BASE** | **"base mais forte" / "base mais fraca"** | verbo de ação sugeria ordem |
| "Directional pairs" | **"Fora do neutro — contagem, não vantagem"** | contagem ≠ qualidade |

E um **aviso fixo no topo**, não em rodapé, declarando a reprovação, o alcance e a frase
obrigatória: *candidatos para análise, sem vantagem comprovada.*

---

## 6. O QUE CONTINUA VALENDO COMO INFRAESTRUTURA

Congelar o Score **não** aposenta o painel. Seguem úteis, e são o que o Volume I do AEGH
descreve como o produto:

- reunir fundamentos por moeda, com a fonte e a idade de cada leitura
- mostrar **mudanças** nas expectativas, não só o nível
- guardar evidência e versão de cada conclusão
- acompanhar as premissas de uma posição que o Eduardo escolheu

⚠️ **Isso não significa que a qualidade analítica esteja aprovada.** A pergunta passa a ser
outra, e é concreta:

> **Ele identifica e explica as mudanças corretamente, com fontes, sem inventar certeza?**

Enquanto essa pergunta não for respondida, **o número agregado pode ficar fora da tela.**
O que fica é o fundamento por moeda, a mudança e a evidência.

---

## 7. O QUE UMA PRÓXIMA VERSÃO PRECISA TRAZER

Não basta reajustar parâmetro — isso é a mesma tentativa com outra roupa. Uma V0.2 precisa
de **justificativa própria, número de tentativa e protocolo congelado antes de rodar**, e
deve enfrentar pelo menos um destes:

1. **Outro insumo além do juro de 2 anos** — o de hoje já mostrou o que tinha.
2. **Outro alvo que não direção** — amplitude, regime, ou qual premissa está em risco.
3. **Mecanismo declarado antes** — por que *deveria* funcionar, não só que funcionou.

**Nada disso altera retrospectivamente o resultado da tentativa 1.**

---

## Arquivos preservados
`hci_fund_radar/update_fund.py` (fonte oficial) · `AEGH_PREREG_v3.md` (protocolo + veredito)
`aegh_painel.py` · `aegh_teste1.py` · `out/aegh_painel.parquet` · `out/aegh_teste1_ops.parquet`
`hci_fund_radar/data/calendar/calendar_*.json` (24 anos de FUND por par)
