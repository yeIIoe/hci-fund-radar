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
| 2026-09-08 | AUD | ALINHADO | primeira linha com as TRÊS colunas existindo, e as três do mesmo lado (casa SOBE, p_alta 0,66, notícia alta condicional) — RBA em 21 dias | [2026-09-08-AUD-tres-colunas-mesmo-lado.md](casos/2026-09-08-AUD-tres-colunas-mesmo-lado.md) | aberto |
| 2026-09-08 | USD | SEM FONTE | a coluna A do caso de 07/set sumiu: a casa foi para "sem leitura" (intensidade 14%, mínimo 15%) e o preço continua pagando alta a 8 dias do FOMC | [2026-09-08-USD-casa-ficou-sem-leitura.md](casos/2026-09-08-USD-casa-ficou-sem-leitura.md) | aberto |
| 2026-09-08 | CAD | SEM FONTE | o comunicado do próprio BoC diz "mantivemos" e a casa lê corte (evidência 24/100) — sem preço para desempatar | [2026-09-08-CAD-noticia-contra-a-casa-sem-preco.md](casos/2026-09-08-CAD-noticia-contra-a-casa-sem-preco.md) | aberto |

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

**L6 — O snapshot tem de ser travado antes de julgar (08/set).** Na primeira rodada real, o
pipeline reescreveu `data/sentimento.json` **quatro vezes** enquanto eu lia (14:53 → 15:10 →
15:17 → 15:20, com o frescor caindo de `atraso_min` 192 e `bloqueia_leitura: true` para
`estado: ok`), e três agentes de camada 2 saíram de arquivo-semente para rodada real no meio
do caminho — inclusive o `noticia`, que **não existia** quando comecei. Resultado: três
linhas erradas no histórico antes da certa. A regra agora: **ler, esperar, reler, e só julgar
quando o mesmo carimbo sobreviver à dupla leitura**; e listar `data/agentes/` na hora, nunca
presumir quais agentes existem. Correção é linha nova, sempre: as três erradas ficam.

**L7 — Todo número do meu texto sai do arquivo, inclusive nos limites.** O erro da segunda
linha de 08/set não foi de julgamento: foi ter **digitado à mão**, dentro de `limites[]`, uma
intensidade e duas notas de evidência que vinham de um snapshot anterior e contradiziam os
números gravados na própria linha. Motivo e limite têm o mesmo peso de auditoria.

**L8 — ALINHADO não é achado; é ausência de divergência (08/set).** No AUD as três colunas
apontaram para cima e o destaque que o dono quer ver **não** disparou, porque o preço se
mexeu junto. O destaque é para o contrário disso. Quando tudo concorda, o produto deste
agente é justamente **não ter produto** — e dizer isso.
