# WORKFLOWS DESLIGADOS — 08/set/2026

Movidos para ca por ordem do Eduardo: *"tire do ar o nosso site do HCI direction e cancela as
operacoes que ele roda automaticamente, eu estou recebendo notificacoes no email"*.

O GitHub Actions SO executa arquivos que estao em `.github/workflows/`. Movendo para esta
pasta, nenhum deles roda — nem por agenda, nem manualmente — e nenhum e-mail de falha e
enviado. Nada foi apagado.

## O que foi desligado

| arquivo | o que fazia | cron |
|---|---|---|
| `macro_direction.yml` | a cadeia do painel, RESERVA da VPS | `37 */3 * * *` |
| `cadeia.yml` | cadeia 2x por dia | `35 7` e `35 11` |
| `macro.yml` | inflation nowcast, FRED, COT de ouro | `0 15 * * 1-5` |
| `equities.yml` | pesquisa de acoes | `40 21 * * 1-5` |
| `nowcast.yml` | nowcast horario | — |
| `sentinela.yml` | sentinela | — |
| `pages.yml` | PUBLICACAO do site no GitHub Pages | por push |

## Como religar

Mover de volta e empurrar:

    git mv .github/workflows-desligados/<arquivo>.yml .github/workflows/
    git commit -m "religa <arquivo>"
    git push

## O que NAO foi feito aqui, e precisa da mao do Eduardo

O site JA PUBLICADO continua no ar com o ultimo conteudo, porque desligar o `pages.yml` para
as ATUALIZACOES, nao derruba a publicacao existente. Para tirar do ar de verdade:

    GitHub > repositorio yeIIoe/hci-fund-radar > Settings > Pages > Source = None

Isso exige acesso de dono no navegador (nao ha `gh` CLI instalado nesta maquina e nao ha
token disponivel).

## A VPS

Parada e DESABILITADA no mesmo dia, por SSH:

    systemctl stop hci-macro
    systemctl disable hci-macro

Nao volta sozinha no reboot. Para religar: `systemctl enable --now hci-macro`.
