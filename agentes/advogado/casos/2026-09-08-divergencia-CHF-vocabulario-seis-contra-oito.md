# CHF — dois prompts escritos, dois vocabulários: seis vereditos contra oito

```
caso            2026-09-08-divergencia-CHF-vocabulario-seis-contra-oito
alvo_agente     divergencia  (a outra ponta é noticia — contradição, não culpa)
alvo_versao     divergencia@v1
alvo_rodada     divergencia-20260908T1534Z
alvo_chave      CHF
tipo            contradicao entre agentes
gravidade       alta
confianca       alta
derruba_a_tese  false   (sempre false na v1 — D4 em aberto)
rodada_id       advogado-20260908T1542Z
versao_prompt   advogado@v1
estado          aberto
```

## As duas afirmações, lado a lado

**(a) `divergencia@v1`**, `data/agentes/divergencia/ultimo.json`, `nao_julgados[2].porque`
(gerado em 2026-09-08T15:34:00Z):

> *"o agente `noticia` devolveu o veredito 'não é sobre juro', que está **FORA** do vocabulário
> de seis palavras. Registrei em coluna_C_detalhe com a observação e não usei em veredito nem
> em destaque."*

Efeito no campo que a tela lê:
`julgamentos[CHF].colunas.C_noticia` = `{"agente": null, "veredito": null, "versao_prompt": null}`.

**(b) `noticia@v1`**, `agentes/noticia/PROMPT.md`, seção 3 — a régua do próprio agente lista
**oito** vereditos, e `não é sobre juro` é um deles, com a definição ao lado (*"a matéria não
trata da política de juros daquele banco"*), junto de `sem dados`. A seção 7.1 daquele prompt
existe exatamente para separar `sem dados`, `não é sobre juro` e `indeterminado`.

**A origem da contradição está escrita nos dois documentos**, e é uma cópia envelhecida:
`agentes/divergencia/PROMPT.md`, seção 3.3 — *"Os dois usam o mesmo vocabulário de veredito, o
de `leitor_falas.py`, e só estes seis"*.

## O que a camada 1 diz

| o que | valor | campo | arquivo | carimbo |
|---|---|---|---|---|
| itens do CHF na janela | 5 gravados, 5 únicos, 5 em 72 h | `moedas.CHF.n_gravados` / `n_unicos` / `n_72h` | `data/noticias.json` | 2026-09-08T14:47:08.054090+00:00 |
| dirigentes nomeados | 0 | `moedas.CHF.n_cita_dirigente` | `data/noticias.json` | idem |
| contagem de manchete | alta 0 · corte 0 · mantem 0 | `moedas.CHF.contagem` | `data/noticias.json` | idem |
| preço do SNB | `sem fonte`, p_* todos `null` | `moedas.CHF.qualidade` | `data/precificacao.json` | 2026-09-08T14:14:10Z |

Ou seja: o CHF já não tem coluna do mercado. A leitura de notícia era a **única** coluna C que
existia para essa moeda nesta rodada, e ela saiu de cena por um desacordo de vocabulário.

## Por que isto importa para quem lê a tela

Na linha do CHF, a coluna C aparece **vazia** — como se nenhum agente tivesse olhado a moeda.
Olharam: o `noticia` leu os cinco itens e concluiu, com a régua dele, que nenhum é sobre a
política do SNB. "Ninguém olhou" e "olharam e não era sobre juro" são informações diferentes, e
a segunda é a útil.

## Este é o MESMO buraco que já foi corrigido — em outro prompt

`agentes/advogado/PROMPT.md`, seção 3.1, revisão de 07/09/2026:

> *"⚠️ E mais dois... São oito, não seis. A versão anterior desta linha listava só seis e teria
> feito você acusar de 'veredito fora da lista' um CHF que saiu legitimamente como `não é sobre
> juro` — objeção falsa contra régua que existe... esta tabela é cópia, e cópia envelhece."*

A correção foi aplicada ao `advogado@v1` e **não foi propagada** ao `divergencia@v1`. Hoje eu
não caí no buraco porque fui abrir a seção 3 do prompt do `noticia` antes de acusar, como o meu
próprio prompt manda.

## O que eu **não** afirmei

- **Não escolhi o vencedor.** Não digo qual das duas listas é a correta. Mudar vocabulário
  exige subir a versão do prompt (`divergencia@v2` ou `noticia@v2`), e isso é decisão do dono.
- Não objetei contra o veredito `não é sobre juro` do `noticia`: ele está na régua escrita dele,
  e objetar ali seria a objeção falsa que o meu prompt existe para evitar.
- Não afirmei que o `divergencia` desobedeceu a si mesmo: ele seguiu a seção 3.3 dele, à risca.
  O defeito é do par de documentos, não da execução.
- Não mexi em arquivo de outro agente e não removi nada da tela.

## Conserto possível, para quem for verificar

Uma linha na seção 3.3 do `divergencia@v1` — a lista passa a apontar para a seção 3 do prompt de
cada agente da coluna C, em vez de copiar a lista — e a versão sobe. É o mesmo conserto que o
`advogado@v1` já recebeu, e ele impede a próxima cópia de envelhecer.

---

## DESFECHO — **preencher DEPOIS da verificação**

```
data_da_verificacao  ____-__-__
quem verificou       Eduardo | revisão | camada 1
a objeção procedia   sim | não | parcialmente
o que mudou          número corrigido | prompt versionado | tese caiu | nada
estado               procedia | nao procedia | sem desfecho
```
