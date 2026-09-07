# CASO — 07/set/2026 · `macro-direction` morreu em silêncio no teto de tempo

*O caso de origem do agente. Ele não foi julgado por uma rodada do vigia: foi medido à mão
antes de o vigia existir, e é justamente por isso que o vigia existe.*

```
caso              2026-09-07-macro-direction-teto-estourado
cadeia            macro-direction
rodada_id         (anterior ao agente — medido à mão em 07/set)
versao_prompt     vigia@v1 (registrado retroativamente)
alarmes           EXEC/macro-direction · CANC/macro-direction ·
                  PULO/macro-direction/geopolitica-gdelt · IDADE/data/*.json
gravidade         alta
causa_suspeitada  teto de tempo estourado
causa_confianca   alta
estado            confirmado
```

## A medição no instante do alarme

| checagem | número | de onde veio |
|---|---|---|
| execuções | **6 de 96** previstas em 24 h (cron `*/15`) | API do GitHub Actions |
| conclusões | 2 sucesso · **4 canceladas** · 0 falha · 0 `timed_out` | API do GitHub Actions |
| passos pulados | `sentimento (moeda e par)`, `registro imutavel (snapshot dos pares)`, `commita se mudou` — nas 4 execuções | jobs da execução `34151494850` e outras 3 |
| duração contra o teto | job em **15,2 min** contra teto de **15 min** declarado no workflow | jobs da execução |
| passo onde parou | `geopolitica (GDELT)`, medida em **8,3 min**; o `bis_discursos` antes dela, em **5,5 min** | log da execução |
| idade | os JSON da cadeia rápida entre **17 e 35 h** | carimbo `gerado_em` dentro dos arquivos |
| snapshots | a série parou de receber linha | `data/snapshots/*.jsonl` |
| notificação | **nenhuma** | — |

## Por que este caso foi registrado

Porque ele é a assinatura completa, e é a que este agente tem de reconhecer em segundos:
**cancelled + duração colada no teto + os três passos finais `skipped` + o passo onde parou
é um dos caros.** E porque expõe o modo de falha que nenhum alarme padrão pega:

> **cancelado não gera e-mail do GitHub.** Só `failure` gera.

## A assinatura — item por item

| item da assinatura | estava presente? | evidência |
|---|---|---|
| execução `cancelled` | sim | 4 das 6 execuções |
| duração colada no teto (`bateu_no_teto`) | sim | 15,2 min contra teto de 15 min |
| passos essenciais `skipped` | sim | `sentimento`, `registro imutavel`, `commit` |
| parou num passo caro | sim | `geopolitica (GDELT)`, 8,3 min |
| **não** era sobreposição | sim | duração longa, não curta — ver lápide da porta automática |

Assinatura completa nos cinco itens: causa nomeada com confiança **alta**.

## O que o painel disse, palavra por palavra

> *A cadeia rápida está mancando. Nas últimas 24 horas a `macro-direction` rodou 6 vezes das
> 96 previstas, e 4 dessas 6 terminaram canceladas. Nas quatro, os passos de sentimento, de
> registro imutável e de commit foram pulados — ou seja, a leitura não foi recalculada, a
> série do backtest não recebeu linha e nada chegou ao site. As execuções canceladas duraram
> 15,2 minutos contra um teto de 15: a causa é teto de tempo estourado, com confiança alta.
> O GitHub não envia e-mail quando uma execução é cancelada, e foi por isso que os arquivos
> ficaram de 17 a 35 horas velhos sem ninguém ser avisado.*

## O custo, em frase inteira

**Reversível:** os JSON da cadeia rápida ficaram de 17 a 35 h velhos. Isso se conserta
rodando a cadeia de novo, e o painel nunca chegou a mostrar número errado — mostrou número
**velho com carimbo velho**, que é o comportamento correto e é exatamente o que fez ninguém
perceber.

**Irreversível:** a série de `data/snapshots/` não recebeu as linhas daquelas rodadas, e
elas **não voltam**. A leitura de um instante não pode ser reconstruída depois, porque a
FXStreet é buscada ao vivo e as manchetes têm janela de 72 h. O backtest de 21/dez perdeu
essa amostra para sempre.

## Limites declarados na hora

- A medição de 6-de-96 foi feita à mão, antes de existir `vigia.py`; a partir de agora ela é
  refeita pelo script a cada rodada, com o `deveria` lido do cron do próprio workflow.
- As tolerâncias de idade usadas para julgar "17 a 35 h velhos" ainda não existiam: foram
  escritas depois, e são provisórias.

---

## CAUSA CONFIRMADA

```
data_do_conserto  2026-09-07
o que foi feito   três partes, no commit "Conserta a cadeia de 15 min: o teto de tempo
                  estava matando o painel desde ontem":
                  1) o BIS saiu da cadeia rápida e foi para a de 2x/dia (é arquivo
                     histórico, o próprio BIS publica com dias de defasagem);
                  2) a geopolítica desceu para DEPOIS do commit do essencial (ela não vota
                     desde 05/set, então atrasar um ciclo não muda leitura nenhuma);
                  3) o passo "publica o essencial" passou a rodar ANTES dos passos caros,
                     e o teto do job subiu de 15 para 20 minutos.
a cadeia voltou   sim
causa real        teto de tempo estourado
estado            confirmado
```

**O que aprendi:**
A ordem dos passos é uma decisão de risco, não de estética: publicar o essencial antes do
caro transforma "estourou o teto" de perda total em atraso parcial. E o modo de falha que
importa vigiar é o que **não** avisa.

**Cuidado com a leitura do desfecho:** uma causa confirmada não valida o agente. Este é um
caso, não uma amostra — e o vigia ainda não tem nenhuma tolerância medida contra
distribuição real.
