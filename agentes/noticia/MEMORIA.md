# MEMÓRIA DO AGENTE `noticia`

*Índice das lições. **Uma linha por caso.** O caso inteiro fica em `casos/<arquivo>.md`, com o
DESFECHO preenchido só depois que o banco decidir. Esta memória é lida ANTES de julgar; as
lápides ficam em `LAPIDES.md`, em arquivo separado, para a memória não virar eco.*

**Como escrever uma linha:** data do julgamento · chave · veredito · a régua que decidiu · o
arquivo do caso · o desfecho (`—` enquanto não houver decisão do banco).

---

## Lições que já valem no dia 1 (herdadas da camada 1, antes de qualquer rodada)

| # | Lição | Origem |
|---|---|---|
| 1 | Apoiar **manter** é manutenção, mesmo quando a frase tem palavra da lista de alta. | Waller, Fed, 03/09/2026 — `LAPIDES.md` L-01 |
| 2 | "markets price cuts" é o que o mercado acha; não é postura do banco. | Pill, BoE, 03/09/2026 — L-02 |
| 3 | **Filtro é por FRASE, nunca por título** — o discurso do Barr se chamava "Destravando oportunidades para trabalhadores com ficha criminal" e continha um sinal real de alta condicional. | Barr, Fed, 01/09/2026 — L-03 |
| 4 | Condição rebaixa alta e corte para condicional; **não** rebaixa manutenção. | `leitor_falas.py`, regra 6 |
| 5 | Negação antes do marcador anula o marcador e, sozinha, produz `manutenção`. | `leitor_falas.py`, regra 5 |
| 6 | Marcador em oração no passado não é postura sobre o próximo passo. | `leitor_falas.py`, regra 3 |
| 7 | `peso_fonte` (qualidade do veículo) ≠ `hierarquia_pesos` (quem falou). Não somam. | `data/noticias.json` — L-05 |
| 8 | Volume de notícia não é direção; republicação conta uma vez. | geopolítica, 05/09/2026 — L-06 |
| 9 | Moeda sem fala fica **sem voto**, não com voto fraco. Silêncio não é voto. | `data/noticias.json → buraco_declarado` |
| 10 | AUD, NZD e CHF **não têm fala oficial automatizável** (RBA, RBNZ, SNB bloqueiam). O que existe delas é imprensa: contexto, não voto. | `data/noticias.json → buraco_declarado` |
| 11 | A precificação nunca entra na leitura; ela é a coluna de comparação, e a **divergência** é o produto. | `data/precificacao.json → lei` |
| 12 | **Proibição sem máquina que confira é decoração.** Quatro números inventados sobreviveram dentro do próprio exemplo do prompt até alguém rodar um verificador. | 07/09/2026 — `LAPIDES.md` L-08 |
| 13 | `bc_discursos.json` **não tem** a chave `moedas`: os vereditos estão em `veredito_por_orador.<X>[]`. Caminho errado = número inventado. | 07/09/2026, ensaio a seco |
| 14 | Manchete de degrau 0,0 **nunca** vira `alta`/`corte`/`manutenção`, nem com `peso_fonte` 1,0 — é a régua **R8** (seção 5.1). | 07/09/2026, ensaio a seco |

---

## Casos julgados

| Data | Chave | Veredito | Régua que decidiu | Caso | Desfecho |
|---|---|---|---|---|---|
| 2026-09-07 | USD | indeterminado | R1 sujeito + R2 quem fala | [casos/EXEMPLO.md](casos/EXEMPLO.md) | — (FOMC 16/09/2026) |
| 2026-09-08 | AUD | alta condicional | R6 condição (modal "may") sobre item de degrau `imprensa_com_fala` | [casos/2026-09-08-AUD-rba-may-have-to-raise.md](casos/2026-09-08-AUD-rba-may-have-to-raise.md) | — (RBA 29/09/2026) |
| 2026-09-08 | GBP | indeterminado | R4 expectativa do mercado + R2/R8 degrau 0,0 | [casos/2026-09-08-GBP-bailey-precificacao-do-mercado.md](casos/2026-09-08-GBP-bailey-precificacao-do-mercado.md) | — (BoE 17/09/2026) |

*(Uma linha por caso, a mais recente embaixo. O `EXEMPLO.md` é o modelo de formato e também um
caso real da rodada de 07/09/2026.)*

---

## O que ainda não sei — buracos declarados

- **Não sei se acerto.** Nenhum veredito deste agente foi comparado com a decisão seguinte do
  banco. Por isso `vota: false` em toda linha. A amostra para essa comparação existe:
  `data/bis_discursos_historico.jsonl`, 1.319 falas de 2009 a 2026 (AUD 440, CHF 223, USD 173,
  NZD 137, EUR 119, GBP 99, JPY 82, CAD 46).
- **A entrada é curta.** `data/noticias.json` grava só os itens do topo de cada moeda (14 no USD
  em 07/09), embora `n_unicos` some muito mais. O julgamento vale para o que está gravado, e isso
  vai escrito em `limites` toda rodada.
- **A janela é de 72 h.** Notícia mais velha que isso não chega até mim; postura anterior só pela
  fonte primária, em `data/bc_discursos.json`.
- **Cinco moedas sem precificação com fonte** (EUR, GBP, JPY, CAD, CHF): para elas não há número
  de mercado para citar em `numeros_citados`, e a divergência contra o mercado não existe.
- **A deduplicação é provisória** (Jaccard 0,7, marcada `provisorio: true` no próprio arquivo).
  Duplicata que passar é para ser registrada em `limites`, não consertada em silêncio.
- **A R6 não diz o que fazer com o modal "may" / "pode"** (a lista dela é "if", "should
  inflation", "were the data to", "caso", "se"). Na rodada de 08/09/2026 li *"may have to raise"*
  como `alta condicional`, indo para o lado mais fraco, e registrei em `limites` — é extensão da
  régua feita no julgamento, **não precedente**. Enquanto a régua não decidir, dois leitores podem
  sair com `alta` e `alta condicional` da mesma frase. Caso:
  [casos/2026-09-08-AUD-rba-may-have-to-raise.md](casos/2026-09-08-AUD-rba-may-have-to-raise.md).
- **A busca por moeda vaza item de outra moeda.** Em 08/09/2026, a lista do GBP trouxe matéria do
  Chile e fala do vice do RBA; a do NZD e a do CHF trouxeram comentário cambial sobre o Fed. Isso
  não é erro de leitura — é a consulta da camada 1, e vai para `limites` toda vez que aparecer.
