# MEMÓRIA — agente `advogado`

Índice das objeções. **Uma linha por caso.** O arquivo do caso mora em `casos/`, e o campo
DESFECHO dele é preenchido **depois** — a objeção procedia ou não?

Como ler a coluna *estado*:
- `aberto` — objeção levantada, ninguém verificou ainda
- `procedia` — o número foi corrigido, o prompt mudou, ou a tese caiu
- `nao procedia` — a objeção era minha e estava errada → vira lápide na seção 3 de `LAPIDES.md`
- `sem desfecho` — o julgamento auditado saiu do ar antes de qualquer verificação

| data | alvo | tipo | o que eu aleguei | caso | estado |
|---|---|---|---|---|---|
| 2026-09-07 | (semeado) divergencia@v1:USD | buraco tratado como neutro | julgar com `frescor.bloqueia_leitura = true` sem declarar o atraso de 3h39 em `limites` | [2026-09-07-divergencia-USD-frescor-nao-declarado.md](casos/2026-09-07-divergencia-USD-frescor-nao-declarado.md) | aberto (**não se repetiu em 08/set**: o frescor saiu declarado, com o número) |
| 2026-09-08 | divergencia@v1:CAD | buraco tratado como neutro | `colunas.C_noticia.veredito` diz `manutenção` creditado a `fala@v1` **e** `noticia@v1`, mas o `noticia` julgou `indeterminado` — e no USD, com a mesma forma, o mesmo arquivo escreveu `contraditoria` | [2026-09-08-divergencia-CAD-indeterminado-virou-manutencao.md](casos/2026-09-08-divergencia-CAD-indeterminado-virou-manutencao.md) | aberto |
| 2026-09-08 | divergencia@v1:CHF | contradicao entre agentes | o `divergencia` chama `não é sobre juro` de "fora do vocabulário de seis"; a seção 3 do `noticia@v1` autoriza **oito** vereditos — é a cópia envelhecida que já foi corrigida no meu prompt e não foi propagada | [2026-09-08-divergencia-CHF-vocabulario-seis-contra-oito.md](casos/2026-09-08-divergencia-CHF-vocabulario-seis-contra-oito.md) | aberto |

---

## O que eu já aprendi sobre objetar (revisar antes de cada rodada)

**O1 — Objeção sem campo, arquivo e carimbo é opinião.** A prova de uma objeção cabe em três
coisas: o trecho literal que o outro escreveu, o caminho do campo na camada 1, e o
`gerado_em` do arquivo. Faltando qualquer uma das três, eu não objeto — no máximo escrevo
uma linha em `limites`.

**O2 — `SEM FONTE` bem declarado é acerto, não defeito.** Cinco das oito moedas não têm
precificação comparável. Um agente que diz "não existe comparação a fazer", copiando o
`detalhe.motivo` do arquivo, fez a coisa certa. Objetar contra isso seria empurrar a casa
para inventar número, que é exatamente o erro que eu existo para caçar.

**O3 — Eu não escolho o vencedor.** Quando dois agentes se contradizem, eu registro a
contradição com as duas afirmações e as duas versões de prompt. A camada 3 é obrigada a
**mostrar** a contradição, nunca a resolver em silêncio.

**O4 — Repetição declarada não é eco.** Um agente que escreve "repete a rodada anterior;
nenhum número novo" está fazendo o certo com o mundo parado. Eco é repetir **sem** declarar,
porque aí duas rodadas iguais são lidas pelo leitor como duas evidências.

**O5 — Eu não tenho veto, e a razão é uma lápide.** Vetar tese é filtrar amostra, e filtro
que corta amostra exige controle aleatório pareado com o mesmo n. Sem essa medição, o veto
seria repetir na camada 2 o erro que o filtro do dólar e o AEGH Teste 1 já pagaram na
camada 1. D4 está em aberto com o dono.

**O6 — Gritar sempre é o mesmo que não existir.** Objeção infundada é erro meu e vira
lápide minha. Seis "sem objeção" com o motivo escrito valem mais do que seis objeções de
gosto.

**O7 — A prosa pode estar certa e o CAMPO errado; o site lê o campo.** (08/set, caso do CAD.)
O agente explicou a distinção corretamente no `motivo`, no `coluna_C_detalhe` e no caso que
abriu — e mesmo assim o campo estruturado `colunas.C_noticia.veredito` saiu com o veredito
colapsado. Ler só o texto do outro agente não basta: **abrir o JSON e olhar o campo que a
camada 3 renderiza** é um lugar de caça por si só, e não estava explícito nos seis.

**O8 — Antes de acusar vocabulário, abrir a seção 3 do prompt do outro.** (08/set, caso do
CHF.) O meu próprio prompt foi corrigido em 07/09 porque a lista de vereditos copiada dentro
dele tinha envelhecido. Hoje eu não caí — e encontrei a MESMA cópia envelhecida viva dentro do
`divergencia@v1`. Regra prática: toda lista de vereditos copiada de um agente para outro é
suspeita por construção; confira contra o prompt de origem, e se as duas discordarem, registre
a contradição sem escolher o vencedor.
