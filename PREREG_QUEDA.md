# PRÉ-REGISTRO — MÉTODO QUEDA (reversão pós-queda excessiva com teste de lastro)

**Pré-registro nº:** QUEDA-v1
**Redigido em:** 2026-09-06 (domingo), ANTES de qualquer desfecho apurado
**Método completo:** `METODO_QUEDA.md` (mesma pasta) — este arquivo é só o que fica CONGELADO
**Motor:** `ficha_queda.py` → `data/fichas_queda.json`, `data/equities_ledger.jsonl`

> Assinado, nada abaixo muda até **2027-02-21**. Qualquer alteração de régua
> invalida a série e reinicia a contagem das 20 semanas.

---

## 1. TESE (duas frases)

Quando uma empresa líquida cai muito além da própria volatilidade e a queda é dela — não do
mercado nem do setor — parte do movimento é liquidação forçada (mandato de risco estourado,
chamada de margem, limpeza de extrato no fim do trimestre) e não reprecificação de lucro.
O consenso de EPS ponto-no-tempo é o que separa as duas coisas: **caiu junto = havia lastro,
não é oportunidade; ficou parado = o preço reagiu além do que o fato pedia.**

---

## 2. RÉGUAS CONGELADAS

| régua | valor congelado | natureza |
|---|---|---|
| universo | NASDAQ/NYSE/AMEX, não-ETF, ativo, presente no snapshot semanal | pré-condição |
| piso de liquidez | preço ≥ US$10 · volume > 500k ações/dia · mcap > US$2 bi | pré-condição (corta 205/1.638) |
| histórico mínimo | 210 barras diárias | pré-condição (corta 37) |
| **FILTRO 1 — queda** | `z_idio ≤ −2,0` | resíduo idiossincrático da semana ÷ desvio semanal de 52s do próprio resíduo (betas de 248 dias contra SPY e ETF do setor) |
| **FILTRO 2 — lastro** | `|Δ EPS consenso| < 3,0%` entre os dois snapshots da janela = "sem lastro" | comparação ancorada no MESMO `fy_date` |
| **FILTRO 3 — regime** | SPY acima da própria SMA200, **sinal defasado 1 dia** | ON = conta no teste; OFF = coletado, gravado, fora do primário |
| medido, não filtrado | SMA200 do nome · setor · motivo (8-K) · movimento de analista | 0 filtros |

**Contagem honesta: 3 filtros + 2 pré-condições que cortam 242 de 1.638 nomes.**

**Nenhum número em valor absoluto.** A justificativa está medida na semana zero: AON −9,09%
e CRDO −26,72%; um corte fixo em −10% pegaria a CRDO e descartaria a AON, mas em desvios a
AON (−3,06) é o evento mais raro dos dois.

**Proibido explicitamente:** gate de regime por faixa de retorno do mercado (touro/neutro/
queda lenta/crash). Esse achado foi **retratado pela própria casa** — era artefato do universo
us100 e inverteu no universo amplo.

---

## 3. HORIZONTE E MÉTRICA

- **Horizonte primário: 4 semanas.** Secundários gravados e reportados: 1 e 12 semanas.
- **Métrica: mediana do retorno de 4 semanas em excesso sobre o SPY, em pp** (`ret_4sem_vs_spy_pp`).
- **Entrada de referência: fechamento do primeiro pregão após a geração da ficha** (segunda-feira).
  Nunca o fechamento da sexta que já está dentro da janela medida.
- **População primária:** fichas `sem lastro`, `regime: ON`, régua `v1`.

---

## 4. CONTROLE — SORTEIO PAREADO (a referência NÃO é o S&P)

**Controle B (primário).** Para cada ficha, sorteia-se um ticker do universo líquido na
**mesma semana e mesmo setor**, sem condição de queda. Mesmo n, mesma distribuição de setores
e de semanas. **2.000 reamostragens.**

**Controle A (secundário).** Ficha `sem lastro` contra ficha `com lastro` da mesma semana,
mesmo setor, `|Δ z_idio| ≤ 0,5`. Só é lido com **≥ 30 nomes `com lastro`** acumulados.
Se não houver n, escreve-se **"sem n"** — e não se troca por um controle mais fácil.

---

## 5. ACEITE (as cinco condições, todas ao mesmo tempo)

1. n ≥ **60 fichas `sem lastro`** E ≥ **20 semanas** com `regime: ON`.
2. Mediana do excesso de 4 semanas **acima do percentil 95** do nulo pareado (p ≤ 0,05).
3. Excesso **positivo nas duas metades** da série (semanas 1-10 e 11-20).
4. Excesso continua positivo **retirando as 3 maiores contribuições**.
5. Excesso continua positivo com **60 bps ida-e-volta** descontados.

**Veredito máximo se as cinco passarem:** *"há sinal forward que merece continuar sendo
observado"*. **Não é aprovação de motor** — falta um regime de estresse na amostra
(condição de reabertura da Fase 2 em `HCI_Swing_Acoes_ML`, não cumprida por 20 semanas).

---

## 6. DATAS

| marco | data |
|---|---|
| semana 1 (régua v0 — **fora do teste primário**) | 2026-09-06 |
| semana 2 (primeira sob a régua congelada v1) | 2026-09-13 |
| inspeção intermediária **CEGA AO RESULTADO** (só encanamento) | 2026-11-15 |
| semana 20 (última coleta) | 2027-01-17 |
| **PRIMEIRA LEITURA — 4 semanas** | **2027-02-21** |
| leitura secundária — 12 semanas | 2027-04-18 |

Semanas com `regime: OFF` não contam para as 20; a data escorrega.
**Olhar qualquer retorno antes de 2027-02-21 contamina a série e mata o teste primário.**

---

## 7. COMO MORRE (gatilhos de lápide)

1. **>50% das fichas `sem lastro` com EPS revisado para baixo nas 4 semanas seguintes** →
   "sem lastro" era atraso do analista, não fato. Morre **mesmo com retorno bom**.
2. Controle B não batido em 2027-02-21 → lápide direta.
3. Taxa de `SEM DADO` > 50% na inspeção de 2026-11-15 (após o conserto do `fy_date`) →
   morte por instrumentação. (Hoje: **60%**.)
4. B passa e A reprova → o lastro é decoração; morre este método, nasce outro com pré-registro próprio.
5. Gate nunca desliga em 20 semanas → regime único, **não pode ser promovido** mesmo passando.
6. Ledger não preenchido semanalmente → sem julgamento possível.

---

## 8. O QUE NÃO SERÁ FEITO

Sem reotimização após ver resultado · sem troca de métrica · **sem backfill de consenso**
(existem 4 snapshots; nada antes de 2026-08-14 é recuperável — qualquer número anterior é
look-ahead) · sem esconder a classe SEM DADO · sem quarto filtro para salvar resultado ruim ·
sem olhar retorno antes da data · sem mudar o piso de liquidez no meio da série · sem trocar
o controle A por um primo mais fácil · sem contar a semana zero no primário · sem promover a
motor com um regime só.

---

## 9. DIVISÃO DE TRABALHO

O sistema entrega **dado e classificação**. O Eduardo decide e escolhe a entrada **pela
análise técnica dele**. **O sistema nunca emite ordem**, nunca diz compre/venda/entre/saia,
nunca sugere tamanho, preço-alvo, stop ou ponto de entrada, e nunca ordena as fichas por
atratividade. O preço de referência do ledger existe para julgar o **método**, não o Eduardo —
são colunas separadas, de propósito.

---

## 10. ESTADO NA ASSINATURA (para que ninguém invente maturidade depois)

4 snapshots de consenso · 3 deltas · **1 semana** de fichas · 20 fichas · 7 `sem lastro` ·
1 `com lastro` · **12 `sem dado` (60%)** · **0 desfechos apurados** · 1 regime (SPY +0,11%) ·
gate de regime **ainda não implementado**.

**Com estes números não é possível afirmar nada sobre o método funcionar.**

---

## 11. PENDÊNCIAS BLOQUEANTES (antes da semana 2, 2026-09-13)

1. Ancorar a comparação de consenso no **mesmo `fy_date`** (hoje 10 dos 12 "sem dado" são
   mudança de ano fiscal).
2. Implementar e gravar o **gate de regime** (SPY vs SMA200, defasado 1 dia).
3. Trocar o corte para **`z_idio`** e gravar `regua` (v0/v1) e **id da rodada** no ledger.
   *(Fato observado em 2026-09-06: a rodada das 20:14 perdeu 179 nomes por falha de download
   e a das 20:44 perdeu 37 — o funil não é determinístico entre rodadas; rodada com perda
   anômala se refaz, não se aceita.)*
4. Rotina de preenchimento dos desfechos do ledger.

---

## ASSINATURA

Sem a assinatura abaixo, este documento é rascunho e as réguas seguem **provisórias**
(é o que `ficha_queda.py` já imprime hoje em toda ficha).

```
Eduardo (EGH) — li, entendi os modos de morte da seção 7 e o teto da seção 5.

assinado em: ____________________
```

---

*Congelado em 2026-09-06. Alterações registradas abaixo com data e motivo.*

### Registro de alterações
*(vazio)*
