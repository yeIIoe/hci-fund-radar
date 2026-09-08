# MEMÓRIA DO AGENTE `geopolitica` — índice das lições

Uma linha por caso. O caso inteiro fica em `casos/`. Leia isto **antes** de julgar; escreva aqui
**depois**. Ordem: mais recente em cima.

Esta tabela é também o **registro de eventos já vistos**: é consultando-a (e o `historico.jsonl`)
que você responde à pergunta M3 — *este evento já estava precificado?*

| Data | Chave / assinatura | Veredito | Lição em uma linha | Caso |
|---|---|---|---|---|
| 2026-09-08 | `evento/energia-eua-ira-fala-preco-petroleo` | indeterminado | **declaração não é evento, e uma declaração não revoga um ataque**: título que diz o que alguém *prevê* ("will drop", "could fall", "after US wins") não é fato datado — e o mesmo conflito trouxe hoje vetores contrários que não se somam | [caso](casos/2026-09-08-fala-preco-petroleo-eua-ira.md) |
| 2026-09-08 | `evento/sancoes-canada-eua` (tarifas) | já precificado | **comentário não é evento**: desfile e "expert warns" não trazem alíquota nem data, e a razão de volume em 1,03 confirma que o assunto está no ritmo normal. Fundi 2 itens de `manchetes_unicas` que a régua separou pelo buraco declarado (o 2º ficou sem entidade) | [caso](casos/2026-09-08-sancoes-canada-eua-tarifas.md) |
| 2026-09-08 | `evento/ataque-eua-ira` (Ormuz) | **já precificado** | a previsão do caso de 06/set **se cumpriu**: voltou idêntico (mesmo título, mesma url, mesma hora, mesmos números), com `reaproveitado: true` e HTTP 429 no bloco — cache não é notícia, e o julgamento de alta de 06/set **não se renova** | [caso](casos/2026-09-06-ataque-eua-ira-ormuz.md) |
| 2026-09-06 | `evento/ataque-eua-ira` (Ormuz) | pressão de alta (importadores) / sem direção (CAD) | mesmo evento, sinais opostos: Ormuz é energia, e energia empurra o juro para cima em quem compra e para lado nenhum em quem vende | [caso](casos/2026-09-06-ataque-eua-ira-ormuz.md) |
| 2026-09-05 | — (regra) | — | duas manchetes que o dono viu eram **o mesmo ataque**; deduplicação semântica é obrigatória e o campo `manchetes_unicas` já existe | [caso](casos/2026-09-05-duas-manchetes-um-ataque.md) |
| 2026-09-07 | GBP (e as outras 6 moedas) | indeterminado | `z = 2,05` de conflito com **zero manchete**: o volume diz que há assunto e não diz qual — sem manchete não há mecanismo | [caso](casos/2026-09-07-z-sem-manchete.md) |

## Padrões que já se repetiram (aviso, não regra nova)

- **A coleta falha muito.** 07/set: 7 blocos com HTTP 429 e orçamento de 480 s estourado antes do
  CAD. Rodada sem manchete é normal, e a resposta certa é `nao_julgados` com o erro copiado.
- **O USD passou a ser TENTADO** (mudança medida em 08/set: aparece em `erros[]` como
  `USD/conflito` e `USD/energia`, os dois com HTTP 429). Antes nem era tentado. Continua sem
  bloco e sem manchete — sempre declarar em `nao_julgados`, mas agora com o motivo certo
  (falhou por limite de taxa, não "não é coletado").
- **A moeda que cai fora do orçamento MUDA de rodada.** Em 07/set o estouro dos 480 s foi antes
  do **CAD**; em 08/set foi antes do **GBP**, e o **AUD** sumiu junto — sem aparecer nem em
  `erros[]`. Confira sempre quais moedas existem no arquivo antes de supor a lista de sete.
- **Rodada com manchete só no `mundo`.** Em 08/set as 5 moedas presentes (CHF, EUR, JPY, NZD,
  CAD) tiveram **zero** manchete própria, e os 3 julgamentos saíram todos de `mundo.energia` e
  `mundo.conflito`. Manchete de `mundo` que fala do Canadá **não** vira julgamento do CAD: fica
  como `evento/…`, com as moedas tocadas nomeadas no motivo.
- **Bloco de moeda também vem de cache.** Além do `reaproveitado: true` do `mundo`, existe
  `reaproveitado_de` por moeda: em 08/set, JPY e CAD de 11:42Z e NZD de 05:08Z, contra uma
  geração de 14:47Z. Registrar a idade e rebaixar a confiança.
- **`tom` vem `null`.** A chamada de tom do GDELT foi desligada por limite de taxa; não conte com
  ela.
- **Republicação local infla o volume.** Cinco emissoras do mesmo grupo republicando um despacho
  produzem 5 manchetes, 1 evento e nenhuma confirmação adicional.
- **Ormuz e Suez são casos de energia**, não de "conflito genérico". A rota é o canal.
