# LÁPIDES DO AGENTE `fala` — o que já errou e não pode repetir

Lápide não se apaga. Só ganha data e número. Leia **antes** de julgar.
*Lei da casa: refutação é ativo — a mesma sereia não canta duas vezes.*

---

## L1 · Contar palavra não é ler — o caso Waller (05/set/2026)
**O erro:** a camada de texto contava expressões hawkish e dovish. Waller disse que **apoiaria
manter** o alvo dos juros, e o painel o marcou como **hawkish**, porque `holding the target`
tinha a palavra "target" na lista de alta.
**O estrago:** o painel afirmou o contrário do que o dirigente do Fed disse, com o nome dele ao
lado.
**A proibição:** nunca decidir por presença de palavra. Toda direção passa pelos seis passos —
sujeito, marcador com objeto, tempo verbal, terceiros, negação, condição.

## L2 · Hawkish condicional não é hawkish — o caso Barr (05/set/2026)
**O erro:** "**if** inflation appears not to be moderating sufficiently, **then** … raise rates"
foi lido como alta firme.
**A proibição:** "if", "should", "were to", "caso", "a depender" rebaixam alta e corte para
**condicional**. Condicional é cenário, e cenário não é direção. E o "not" que mora **dentro da
condição** não nega o marcador que vem depois do "then" — quem separa é a oração.

## L3 · Falar de juros não é ter postura — o caso Warsh (05/set/2026)
**O erro:** Warsh defendeu a **liberdade do comitê para decidir** e foi marcado hawkish.
**A proibição:** meta-discurso sobre condução de política monetária é `indeterminado`.
`indeterminado` é resposta, não é falha.

## L4 · Expectativa do mercado não é postura do orador — o caso Pill (06/set/2026)
**O erro:** o **único** veredito de GBP no painel era "manutenção", tirado de
"it is natural for **market participants** to interpret this set of scenarios as suggesting the
MPC is seeking to keep rates on hold" — com o nome do dirigente do BoE ao lado. O filtro de
terceiros foi derrotado por duas coisas ao mesmo tempo: o nome da instituição ("the MPC")
resgatava a frase como se fosse do orador, e o "but" abria oração nova sem a palavra "mercado".
**A proibição:** nomear a instituição **não** diz quem fala. Só a primeira pessoa ("I", "we",
"eu", "nós") identifica o orador como fonte da postura. Na dúvida, silêncio.
**Nota dura:** este caso teve o gabarito do teste **trocado** — o antigo estava errado e o código
o obedecia. Teste verde não é prova de acerto.

## L5 · Percentil, contagem e porcentagem sem a janela declarada ao lado (02/set/2026)
**O erro da casa:** "máxima histórica" que era máxima de 5 anos; percentil com look-ahead.
**A proibição para você:** todo número que você citar vem com a **fonte e a janela**. "99,7% de
indeterminado" sem dizer "nas 1.319 falas do histórico, que não têm corpo" é uma frase falsa
disfarçada de medição.

## L6 · O veredito da regra não é gabarito
`veredito_leitor` é o palpite da camada 1 e tem erros **medidos** (seção 5 do `PROMPT.md`):
negação depois do marcador inverte o sinal ("raising the policy rate is not warranted" → alta).
**A proibição:** não copiar o veredito da regra sem ler o trecho. E não silenciar a divergência
quando ela existir — a divergência é o dado que justifica esta camada existir.

## L7 · Não inventar texto que não veio
Em 6 dos 12 itens vivos de 07/set o corpo do discurso **não estava no repositório**.
**A proibição:** não deduzir postura do título, do nome do orador, da fama dele ou do que ele
disse no mês passado. Sem texto, vai para `nao_julgados` com o link que faltou.

## L8 · Não votar, e não pedir para votar
Dimensão não validada **não vota**, só informa. Enquanto não houver histórico de decisões e
corpo dos discursos, não existe medição de acerto — e sem medição não existe voto, nem "voto
pequeno", nem "peso experimental".
