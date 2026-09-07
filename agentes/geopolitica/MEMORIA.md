# MEMÓRIA DO AGENTE `geopolitica` — índice das lições

Uma linha por caso. O caso inteiro fica em `casos/`. Leia isto **antes** de julgar; escreva aqui
**depois**. Ordem: mais recente em cima.

Esta tabela é também o **registro de eventos já vistos**: é consultando-a (e o `historico.jsonl`)
que você responde à pergunta M3 — *este evento já estava precificado?*

| Data | Chave / assinatura | Veredito | Lição em uma linha | Caso |
|---|---|---|---|---|
| 2026-09-06 | `evento/ataque-eua-ira` (Ormuz) | pressão de alta (importadores) / sem direção (CAD) | mesmo evento, sinais opostos: Ormuz é energia, e energia empurra o juro para cima em quem compra e para lado nenhum em quem vende | [caso](casos/2026-09-06-ataque-eua-ira-ormuz.md) |
| 2026-09-05 | — (regra) | — | duas manchetes que o dono viu eram **o mesmo ataque**; deduplicação semântica é obrigatória e o campo `manchetes_unicas` já existe | [caso](casos/2026-09-05-duas-manchetes-um-ataque.md) |
| 2026-09-07 | GBP (e as outras 6 moedas) | indeterminado | `z = 2,05` de conflito com **zero manchete**: o volume diz que há assunto e não diz qual — sem manchete não há mecanismo | [caso](casos/2026-09-07-z-sem-manchete.md) |

## Padrões que já se repetiram (aviso, não regra nova)

- **A coleta falha muito.** 07/set: 7 blocos com HTTP 429 e orçamento de 480 s estourado antes do
  CAD. Rodada sem manchete é normal, e a resposta certa é `nao_julgados` com o erro copiado.
- **O USD não é coletado** por `geopolitica.py` (só GBP, AUD, EUR, JPY, NZD, CAD, CHF) — e é a
  moeda mais exposta a evento global. Sempre declarar em `nao_julgados`.
- **`tom` vem `null`.** A chamada de tom do GDELT foi desligada por limite de taxa; não conte com
  ela.
- **Republicação local infla o volume.** Cinco emissoras do mesmo grupo republicando um despacho
  produzem 5 manchetes, 1 evento e nenhuma confirmação adicional.
- **Ormuz e Suez são casos de energia**, não de "conflito genérico". A rota é o canal.
