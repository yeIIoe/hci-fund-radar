# Arquivo point-in-time do calendario macro

Gerado e mantido por `calendario_arquivo.py`. Este texto e documentacao e pode
ser reescrito; os `.jsonl` ao lado NAO — eles sao append-only.

## Por que este arquivo existe

A FXStreet serve uma janela ROLANTE de ~42 dias. Medido em 06/set/2026:
`data/calendario_resultado.json` trazia 233 eventos, de 2026-09-03 a 2026-09-13.
Evento que sai da janela leva o consenso junto, e nao ha endpoint de historico.

Surpresa = divulgado - consenso. Sem o consenso congelado ANTES do resultado, a
surpresa vira reconstrucao a posteriori — o mesmo furo que matou o backtest do
Deep Value. Este diretorio e a unica copia point-in-time que teremos.

## Formato

Um arquivo por MES DA LEITURA: `AAAA-MM.jsonl`, uma linha JSON por leitura de
evento. O mes e o do `quando_li_utc`, nao o do evento — assim cada execucao
escreve em um unico arquivo, e arquivo de mes fechado nunca mais e aberto para
escrita.

Campos de cada linha:

| campo | o que e |
|---|---|
| `seq` | posicao da linha dentro do arquivo (1, 2, 3...) |
| `evento_id` | identidade do evento: o `id` da fonte quando existe, senao a `chave` |
| `id_fonte` | `id` estavel da FXStreet, ou nulo |
| `chave` | `d-` + sha256(titulo+moeda+quando_utc), 16 hex — usada quando nao ha id |
| `titulo`, `titulo_pt`, `moeda`, `pais`, `quando_utc`, `impacto`, `unidade` | identidade e metadado |
| `consenso`, `anterior`, `divulgado`, `revisado` | **os campos de valor** |
| `quando_li_utc` | instante em que ESTE processo leu (o carimbo point-in-time) |
| `fonte_gerado_em` | `gerado_em` do JSON de origem (sempre <= `quando_li_utc`) |
| `fontes` | quais arquivos contribuiram |
| `mudou` | quais campos de valor mudaram e provocaram esta linha |
| `perdeu` | campos que eram conhecidos e voltaram nulos nesta leitura |
| `hash_valores` | sha256(evento_id + 4 campos de valor), 12 hex |
| `hash_cadeia` | sha256 encadeado com a linha anterior do mesmo arquivo, 12 hex |

`titulo_pt` sai **nulo** hoje: nenhuma das duas fontes publica titulo em
portugues (a traducao vive na interface). Campo sem fonte fica nulo — nao se
inventa traducao no arquivo.

## Append-only e anti-entulho

- Linha antiga nunca e reescrita nem removida. So se acrescenta ao fim.
- So se grava quando **consenso, anterior, divulgado ou revisado** mudou em
  relacao a ultima linha daquele evento. Rodar de novo sem novidade grava zero
  bytes — e o que permite o cron de 15 minutos.
- Valor conhecido que volta **nulo** nao conta como mudanca (a fonte piscando
  nao apaga o que ja foi visto). Se a linha for gravada por outro motivo, o
  campo sai nulo mesmo e o nome dele aparece em `perdeu`.
- Limite conhecido: **remarcacao de horario sozinha nao gera linha**. Se um
  evento com `id` for adiado sem mudar nenhum valor, o `quando_utc` novo so
  aparece na proxima linha que algum valor provocar. Para evento sem `id`, o
  horario entra na `chave`, entao a remarcacao vira um evento novo.

## Integridade — como provar que ninguem editou

    python calendario_arquivo.py --verifica

Recalcula `hash_valores` de cada linha e refaz a cadeia. Linha editada quebra o
hash dela; linha inserida, apagada ou reordenada quebra a cadeia dali para
frente, e a verificacao aponta a primeira divergencia.

## Como reconstruir o estado de uma data qualquer

    from calendario_arquivo import reconstroi
    estado = reconstroi("2026-09-06T12:00:00+00:00")
    estado["eventos"]["<evento_id>"]["consenso"]

`reconstroi` le so arquivos ate o mes pedido e descarta linha a linha tudo com
`quando_li_utc` posterior ao instante — o total descartado sai em
`linhas_ignoradas_futuro`, para o corte poder ser conferido. Data sem hora
(`2026-09-06`) e lida como 00:00:00 UTC daquele dia, o corte mais conservador.

Pela linha de comando:

    python calendario_arquivo.py --reconstroi 2026-09-06T12:00:00+00:00

## Ate onde a serie vai para tras

**A serie propria comeca em 06/set/2026.** Antes disso nao ha consenso
arquivado por nos — nao se inventa.

Existe um caminho de backfill PARCIAL, ainda nao executado, medido em
06/set/2026 sobre `wayback_ff/cdx_all.json.gz` (59.953 capturas do calendario do
Forex Factory no Internet Archive):

- capturas de pagina de calendario "limpa" (sem filtro na URL) e com corpo
  > 8 kB: **12.417**, de 2007 a 2026;
- dias uteis com captura tirada no mesmo dia ou antes, dentro da semana
  exibida — ou seja, com consenso congelado antes do resultado:
  **2.584 de 2.870 dias uteis entre 2014 e 2024 = 90,0%**;
  por ano: 2014 96,2% · 2015 73,9% · 2016 82,8% · 2017 89,6% · 2018 91,6% ·
  2019 92,7% · 2020 93,9% · 2021 91,2% · 2022 97,7% · 2023 95,8% · 2024 85,1%;
- antes de 2014 a cobertura cai muito: 2013 50,2% · 2012 43,7% · 2011 44,2% ·
  2010 26,4% · 2009 17,2% · 2008 6,1% · 2007 41,0%;
- 2025 (27,6%) e 2026 (8,8%) estao mortos: o Forex Factory entrou atras de
  Cloudflare e o crawler do Archive parou. Dali em diante so arquivador proprio
  — este aqui.

Amostra REAL de 8 capturas baixadas em 06/set/2026 (2015, 2018, 2021, 2024):
537 linhas das 8 majors, 258 com resultado, 355 com previsao e **146
observacoes point-in-time** (resultado vazio + previsao preenchida), ou seja
**18,2 observacoes PIT por captura**. Nas duas capturas de 2015 o leitor
devolveu 0 linhas: o HTML daquela epoca usa `class="currency"`, e o de 2017+ usa
`class="calendar__currency"`, e 2023+ tem um JSON embutido
(`calendarComponentStates`). Sao **tres leitores diferentes** — o backfill custa
codigo, nao acesso.

Conclusao honesta: da para reconstruir consenso historico do Forex Factory de
~2014 a 2024 com ~90% dos dias uteis cobertos, e de 2007 a 2013 com cobertura
irregular (6% a 50%), desde que se escrevam os leitores das tres eras e se leia
`FF.timezone` de dentro de cada pagina (o relogio da pagina e o do crawl, nao o
do evento). Nada disso foi colhido ainda: **hoje o arquivo comeca em
06/set/2026**.

