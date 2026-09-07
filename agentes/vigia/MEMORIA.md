# MEMÓRIA — agente `vigia`

Índice dos incidentes. **Uma linha por caso.** O arquivo do caso mora em `casos/`, e o
bloco **CAUSA CONFIRMADA** dele é preenchido **depois**, quando o conserto for feito e a
cadeia voltar.

Esta memória não guarda observação; guarda **incidente com causa**. É o que permite
reconhecer na segunda vez, em segundos, o que na primeira vez custou horas.

Como ler a coluna *estado*:
- `aberto` — o alarme está de pé, a causa ainda não foi confirmada pelo conserto
- `confirmado` — o conserto foi feito e a cadeia voltou: a causa suspeitada era a causa
- `refutado` — o conserto foi feito e o problema continuou: a causa estava errada
- `sem desfecho` — o problema sumiu sozinho e ninguém consegue dizer por quê

| data | cadeia | alarme | medida | causa suspeitada | caso | estado |
|---|---|---|---|---|---|---|
| 2026-09-07 | macro-direction | 4 execuções canceladas em 24 h e 3 passos essenciais pulados em cada | 6 de 96 execuções; 15,2 min contra teto de 15 | teto de tempo estourado | [2026-09-07-macro-direction-teto-estourado.md](casos/2026-09-07-macro-direction-teto-estourado.md) | confirmado |

---

## As lições até aqui (revisar antes de cada rodada)

**L1 — Cancelado não gera e-mail.** É a lição de origem deste agente. O GitHub só notifica
`failure`. `cancelled` e `timed_out` passam em silêncio, e é justamente neles que os passos
finais são pulados. Um vigia de caixa de entrada é surdo para o modo de falha mais comum
desta casa. Por isso: lemos a API e o repositório, nunca a caixa de entrada.

**L2 — O silêncio da cadeia se parece com saúde.** Quando o commit é pulado, o site
continua servindo o arquivo anterior **com o carimbo anterior** — que é o comportamento
correto e honesto. O painel não fica errado; ele fica **velho e certo**. É exatamente por
isso que ninguém percebe. A idade é a única coisa que denuncia, e só se alguém a olhar.

**L3 — O `mtime` mente na nuvem.** O `actions/checkout` reescreve o mtime de todo arquivo a
cada execução. Em 31/ago/2026 isso manteve todas as fontes congeladas por uma semana com
cara de frescas. Idade vem do carimbo **dentro** do arquivo, sempre, e o campo lido vem
declarado ao lado.

**L4 — Tolerância escolhida à mão não é lei.** As 15 tolerâncias de `vigia.py` foram
arbitradas em 07/set sem amostra. Elas servem para acordar alguém, não para provar nada.
Enquanto não houver a distribuição medida do intervalo real entre commits, toda menção a
elas vem com a palavra "provisória" colada.

**L5 — Assinatura incompleta é `indeterminado`.** Nomear a causa errada com cara de certeza
manda o dono consertar a coisa errada, e o custo real disso não é o tempo perdido: é que na
próxima vez ele não lê o alarme. Faltando um item da assinatura, a causa é `indeterminado` e
o que falta vai escrito.

**L6 — Nem todo cancelamento é falha.** O `macro-direction.yml` declara
`cancel-in-progress: true`: uma execução nova cancela a anterior **de propósito**. Estouro
de teto tem duração colada no teto; sobreposição é curta e tem execução nova logo em
seguida. Confundir os dois é inventar um incêndio.

**L7 — Ausência de medição não é saúde.** Quando a API do GitHub não responde (60 chamadas
por hora sem chave), a rodada não mede execuções. A saída tem de dizer isso com todas as
letras. "Nenhum alarme de execução" e "não houve medição de execução" são frases opostas, e
a segunda é a verdadeira nesse caso.

**L8 — O snapshot é o único dano irreversível.** Arquivo velho se conserta rodando de novo.
Dia sem linha de snapshot não volta: a leitura de hoje não pode ser reconstruída amanhã,
porque a FXStreet é buscada ao vivo e as manchetes têm janela de 72 h. Quando a série parar,
essa frase entra no resumo, por extenso.

**L9 — `deveria` que muda sozinho é configuração, não falha.** Se o número previsto pelo
cron mudar de uma rodada para outra sem nenhuma execução ruim, alguém editou o workflow. A
causa é `configuração alterada`, e o alarme correto é informar a mudança — não gritar que a
cadeia caiu. (Aconteceu em 07/set: a `macro-direction` passou de `*/15` para `37 */3`,
de 96 previstas por dia para 8, no mesmo dia do incidente do teto.)
