# LÁPIDES DO AGENTE `geopolitica` — o que já errou e não pode repetir

Lápide não se apaga. Só ganha data e número. Leia **antes** de julgar.
*Lei da casa: refutação é ativo — a mesma sereia não canta duas vezes.*

---

## L1 · Duas manchetes, um ataque — a lápide que existe desde antes de você (05/set/2026)
**O erro:** o painel mostrou **duas manchetes** para o dono. As duas descreviam **o mesmo
ataque**, republicado por veículos diferentes. Duas linhas na tela, um evento no mundo — e a
intensidade parecia o dobro do que era.
**A proibição:** **deduplicação semântica é obrigatória.** Leia `manchetes_unicas`, nunca
`manchetes`. E se dois itens de `manchetes_unicas` forem o mesmo fato (a régua deduplica de
menos por decisão declarada), **funda os dois no seu julgamento** e escreva que fundiu.
**Corolário:** `n_republicacoes` **não é confirmação**. Cinco ecos de uma fonte fraca continuam
sendo uma fonte fraca.

## L2 · Volume não é direção — o veto do dono (05/set/2026)
**O erro:** a dimensão media z de volume de notícia e virava pontuação. Em 04/set ela chegou a
entrar como quarta dimensão do sentimento e como segunda perna do ouro; em 05/set a decisão foi
**revogada**, porque a regra "energia z ≥ 1,5 = alta para importador, conflito sem energia =
corte" **nunca foi medida** — foi declarada.
**O precedente que decidiu:** o filtro do DXY foi assumido sem medição e depois **reprovado nas
88 operações** — as seis células reduziram o resultado.
**A proibição:** o z entra na **confiança**, nunca no veredito. Direção sai da leitura do fato e
do mecanismo, nunca da intensidade.

## L3 · Não julgar moeda sem manchete (medido em 07/set/2026)
**O caso:** o GBP aparecia com conflito `z = 2,05` — acima do limiar de 1,5 que dispara a
implicação automática da camada 1 — e com **zero manchete**. As sete moedas do arquivo estavam
com a lista vazia, por HTTP 429.
**A proibição:** lista vazia → `nao_julgados`, com o erro copiado de `erros[]`. Nunca deduzir o
assunto a partir do z, do país ou do noticiário que você conhece de fora do repositório.

## L4 · O canal de refúgio é FX, e não é juro
**O erro fácil:** "conflito → risk-off → dólar sobe → juro sobe". A segunda seta não existe.
Fluxo de refúgio move **câmbio**; para mover **juro** é preciso passar por inflação (energia) ou
por crescimento (demanda).
**A proibição:** risk-off entra no `motivo`, marcado como FX. Nunca vira veredito.

## L5 · Notícia velha não é notícia
**A lei:** preço reage a **surpresa**, não a fato conhecido — a mesma lei da dimensão de dados
(surpresa contra consenso, nunca o nível).
**A proibição:** um conflito que dura seis meses não empurra nada hoje. Antes de M1 ou M2, passe
por **M3**: assinatura já julgada em rodada anterior, `razao` perto de 1, bloco `reaproveitado:
true` ou título que só comenta o fato → **já precificado**.
**Nota:** em 07/set o único bloco com manchete estava `reaproveitado: true` — era cache, não
coleta nova.

## L6 · Não tomar partido, não fazer geopolítica de opinião
**A regra da casa:** o objeto é o **canal econômico** — energia, comércio, crescimento, prêmio de
risco. Não é o mérito das partes, não é previsão militar, não é política.
**Reforço:** a geopolítica **não vota** no sentimento (regra em vigor desde 05/set, que revogou
a de 04/set). Nada do que você escreve entra em soma nenhuma.

## L7 · Não inventar número
**A proibição:** todo número no seu julgamento é **copiado** de `data/geopolitica.json`, com o
nome do campo ao lado. Você não calcula z, não calcula razão, não conta artigo e não estima
percentual de petróleo que passa por lugar nenhum. Sem número medido, o campo vai `{}` e o motivo
descreve o mecanismo em palavras.
