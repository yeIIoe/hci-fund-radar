# MEMÓRIA — agente `divergencia`

Índice das lições. **Uma linha por caso.** O arquivo do caso mora em `casos/`, e o campo
DESFECHO dele é preenchido **depois**, quando o banco central decidir.

Como ler a coluna *estado*:
- `aberto` — julgado, desfecho ainda não existe (a reunião não aconteceu)
- `acertou` / `errou` — desfecho medido contra a decisão seguinte do banco
- `sem desfecho` — o caso não é mensurável (ex.: SEM FONTE dos dois lados)

| data | moeda | veredito | o que estava em jogo | caso | estado |
|---|---|---|---|---|---|
| 2026-09-07 | USD | HCI MAIS DOVISH | a casa lê corte, os futuros de fed funds pagam alta (p_alta 0,5786) a 10 dias do FOMC | [2026-09-07-USD-casa-le-corte-mercado-paga-alta.md](casos/2026-09-07-USD-casa-le-corte-mercado-paga-alta.md) | aberto |
| 2026-09-07 | EUR | SEM FONTE | reunião do BCE em 3 dias e nenhuma fonte de precificação: a divergência não é mensurável | [2026-09-07-EUR-sem-fonte-para-comparar.md](casos/2026-09-07-EUR-sem-fonte-para-comparar.md) | sem desfecho |

---

## As lições até aqui (revisar antes de cada rodada)

**L1 — "Sem fonte" é resposta, não falha.** Cinco das oito moedas não têm precificação
comparável. Dizer isso com o motivo do arquivo copiado ao lado vale mais do que produzir
uma comparação inventada. O painel que esconde o buraco perde a confiabilidade operacional,
que é a nota que o dono mede.

**L2 — A escada de qualidade manda no que se pode afirmar.** `alta` (futuro da própria
taxa de política) permite falar de probabilidade; `baixa` (futuro a termo de 3 meses)
permite falar só de direção; `sem fonte` não permite nada. Confundir os três degraus é
inventar precisão.

**L3 — Divergência não é convicção.** A diferença entre a casa e o preço é uma medida
econômica. Ela não diz quem vai acertar, e enquanto não houver backtest a convicção
histórica é `null`. São três números distintos e nunca somados: divergência, qualidade da
evidência e convicção histórica.

**L4 — Quem não vota não decide por dentro.** As falas e a geopolítica são contexto desde
05/set. A coluna C entra no texto e no destaque; nunca no veredito.

**L5 — Repetir a rodada anterior sem número novo tem de estar escrito.** Se nada mudou na
camada 1, o motivo diz "repete a rodada anterior; nenhum número novo". É a defesa contra o
viés de eco, e é a primeira coisa que o advogado do diabo procura.
