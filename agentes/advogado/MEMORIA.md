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
| 2026-09-07 | (semeado) divergencia@v1:USD | buraco tratado como neutro | julgar com `frescor.bloqueia_leitura = true` sem declarar o atraso de 3h39 em `limites` | [2026-09-07-divergencia-USD-frescor-nao-declarado.md](casos/2026-09-07-divergencia-USD-frescor-nao-declarado.md) | aberto |

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
