# Inventario do Wayback sobre o calendario do Forex Factory

`cdx_all.json.gz` — 59.953 snapshots HTTP 200 de `forexfactory.com/calendar*`,
deduplicados por digest, levantados em 01/set/2026 numa unica chamada a API CDX.

E o MAPA do que da para colher, nao o dado colhido.

Por que importa: entre 2014 e 2024, cerca de 90% dos dias uteis tem um snapshot
tirado ANTES do evento — ou seja, com a previsao de consenso e o campo do resultado
ainda vazio. Isso e point-in-time por construcao: o arquivo foi congelado antes de
o desfecho existir, entao ninguem revisou nada depois.

⚠️ 2025 e 2026 estao mortos: o Forex Factory entrou atras de Cloudflare e o crawler
do Internet Archive parou (15.483 linhas em 2024 contra 961 em 2026). Dai para frente
so arquivador proprio.

⚠️ O relogio das paginas e o do CRAWL, nao o do evento: o mesmo evento renderiza
8:15am num snapshot de marco e 9:15am num de maio. Ler `FF.timezone` de dentro da
pagina, nunca assumir.
