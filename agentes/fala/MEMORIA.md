# MEMÓRIA DO AGENTE `fala` — índice das lições

Uma linha por caso. O caso inteiro fica em `casos/`. Leia isto **antes** de julgar; escreva
aqui **depois**. Ordem: mais recente em cima.

| Data | Chave | Veredito | Lição em uma linha | Caso |
|---|---|---|---|---|
| 2026-08-05 | USD/Cook | indeterminado | **1ª divergência IA × regra**: "I would consider how a rate increase could negatively affect that stability" não é postura de alta — é critério de decisão sobre o efeito de uma alta hipotética; a regra carimbou **alta firme (força 4)** só porque o marcador veio em 1ª pessoa, sem "if" e sem negação | [caso](casos/2026-08-05-USD-Cook.md) |
| 2026-09-03 | USD/Waller | manutenção | "holding the target" é MANTER, não alta — a palavra "target" enganava a contagem; e as duas altas condicionais na mesma fala não mudam o próximo passo | [caso](casos/2026-09-03-USD-Waller.md) |
| 2026-09-01 | USD/Barr | alta condicional | hawkish com "if" é **cenário**, não direção firme; o "not" da condição ("if inflation appears not to be moderating") não nega o "raise rates" que vem depois do "then" | [caso](casos/2026-09-01-USD-Barr.md) |
| 2026-08-28 | USD/Warsh | indeterminado | defender a liberdade de decidir não é alta nem corte; falar de "interest rates" não é ter postura sobre eles | [caso](casos/2026-08-28-USD-Warsh.md) |
| 2026-09-03 | GBP/Pill | indeterminado | "market participants … the MPC is seeking to keep rates on hold" é leitura do MERCADO; nomear o banco não identifica quem fala — só a primeira pessoa identifica | [caso](casos/2026-09-03-GBP-Pill.md) |
| 2026-09-02 | CAD/Macklem | manutenção | a decisão ANUNCIADA no passado ("we decided to maintain") é a postura em vigor, não recibo; a exceção vale só para manutenção | [caso](casos/2026-09-02-CAD-Macklem.md) |
| 2026-09-07 | — (linha de base) | — | a regra devolve 99,7% de indeterminado nas 1.319 falas do histórico **porque o arquivo não tem o corpo** (resumo de 174 caracteres de mediana); a linha de base que vale é a dos vivos, 63,6% | [caso](casos/2026-09-07-linha-de-base.md) |

## Padrões que já se repetiram (leia como aviso, não como regra nova)

- **Metade dos itens vivos chega sem frase.** 6 de 12 em 07/set. Não é falha de leitura: é o
  pré-filtro de palavra-chave da camada 1. Vá para `nao_julgados` e diga qual link falta.
- **O BCE é o buraco maior.** Em 07/set, os quatro itens do BCE (Vujcic, Schnabel, Cipollone,
  Lagarde) vieram com zero frases. Nenhum veredito de EUR saiu daquela rodada.
- **Comunicado vale mais que conversa.** `origem` e `peso` estão no item; o comunicado de decisão
  tem peso 1,0 e escreve a postura em vigor no passado.
- **Fala do BIS chega velha.** `defasagem_bis_dias` chegou a 19 e `idade_dias` a 25 numa fala do
  RBA. Em 08/set os três itens do BIS tinham `idade_dias` 26, 34 e 42. Isso rebaixa confiança,
  nunca inverte veredito.
- **Marcador em primeira pessoa não basta.** O caso Cook (08/set) mostra o buraco que sobrou
  depois de Waller, Barr e Warsh: a regra exige marcador + 1ª pessoa + sem "if" + sem negação, e
  isso ainda deixa passar frases cujo NÚCLEO é o *efeito* de uma alta ("how a rate increase could
  negatively affect…"), não o próximo passo. Sempre pergunte: o verbo da oração é **mexer no
  juro**, ou é **ponderar/descrever** algo sobre mexer no juro?
- **Cada rodada, o mesmo buraco de coleta.** Em 08/set, seis itens do bloco vivo do BCE/BoE/BoC e
  dois do BIS chegaram com **zero frases**. Nenhum veredito de EUR saiu — pelo segundo dia
  seguido.
