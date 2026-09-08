# CAD — o `indeterminado` do `noticia` virou `manutenção` no campo que a tela lê

```
caso            2026-09-08-divergencia-CAD-indeterminado-virou-manutencao
alvo_agente     divergencia
alvo_versao     divergencia@v1
alvo_rodada     divergencia-20260908T1534Z
alvo_chave      CAD
tipo            buraco tratado como neutro
gravidade       alta
confianca       alta
derruba_a_tese  false   (sempre false na v1 — D4 em aberto)
rodada_id       advogado-20260908T1542Z
versao_prompt   advogado@v1
estado          aberto
```

## O que o agente afirmou

Campo estruturado, na linha do CAD de `data/agentes/divergencia/ultimo.json`:

> `"C_noticia": {"agente": "fala, noticia", "veredito": "manutenção", "versao_prompt": "fala@v1, noticia@v1"}`

## O que a camada 1 diz

| o que | valor | campo | arquivo | carimbo |
|---|---|---|---|---|
| citado pelo agente | `manutenção`, creditado a `fala@v1` **e** `noticia@v1` | `julgamentos[CAD].colunas.C_noticia.veredito` | `data/agentes/divergencia/ultimo.json` | 2026-09-08T15:34:00Z |
| o que o `noticia` de fato julgou | `indeterminado` (confiança baixa) | `julgamentos[CAD].veredito` | `data/agentes/noticia/ultimo.json` | 2026-09-08T15:20:00Z |
| a mesma forma, tratada de outro modo no mesmo arquivo | `contraditoria` | `julgamentos[USD].colunas.C_noticia.veredito` | `data/agentes/divergencia/ultimo.json` | 2026-09-08T15:34:00Z |

O lado do `fala` está certo e conferido na camada 1: `data/bc_discursos.json`, `itens[4]`,
CAD/Macklem, `veredito_leitor.veredito` = `manutenção`, `forca` 4, `frases_analisadas` 2,
`peso` 1,0 (arquivo gerado em 2026-09-08T14:46:35.875216+00:00). O que não existe é o
`manutenção` do lado do `noticia`.

## A regra violada

Duas, as duas escritas pelo próprio agente:

1. `agentes/divergencia/PROMPT.md`, seção 3.3 — *"`indeterminado` é resposta legítima e
   frequente. Ela **não** é 'neutro' e **não** é 'manutenção': trate-a como coluna C ausente
   para efeito de destaque."*
2. `agentes/divergencia/LAPIDES.md`, **L-H7 · Silêncio não é voto** — *"agente ausente não
   vira 'a notícia concorda'. Sai `SEM FONTE` ou `nao_julgados`, com o motivo escrito."*

E a inconsistência interna, que é a prova mais limpa de que a régua existe e foi aplicada em
um lugar e não no outro: no **USD**, com a mesma forma (um `manutenção`, um `alta condicional`
e três `indeterminado`), o mesmo arquivo escreveu corretamente `"contraditoria"`.

## Por que isto importa para quem lê a tela

O site lê `colunas.C_noticia`. Na linha do CAD ele vai renderizar
**"manutenção · fala@v1, noticia@v1"** — dois agentes, um veredito, um par de versões de
prompt do lado. O leitor lê isso como **dois julgamentos concordando**, que é exatamente o
mecanismo de convicção falsa que a camada 2 existe para não produzir. E o CAD é a linha que o
próprio agente chamou de *"a observação mais forte da rodada"*.

O veredito **não muda**: o CAD continua `SEM FONTE`, porque o lado do mercado continua ausente
(`data/precificacao.json`, `moedas.CAD.qualidade` = "sem fonte", 2026-09-08T14:14:10Z).

## O que eu **não** afirmei

- **Não afirmei que o agente entendeu errado.** Ele entendeu. O `motivo` da linha do CAD, o
  `coluna_C_detalhe` e o caso que ele abriu hoje
  (`agentes/divergencia/casos/2026-09-08-CAD-noticia-contra-a-casa-sem-preco.md`, linha 51)
  dizem por extenso: *"`noticia:CAD` = indeterminado (confiança baixa). Indeterminado **não** é
  manutenção e **não** é neutro: só a linha do `fala` sustenta a coluna C aqui."* O defeito
  está no campo estruturado, não no raciocínio — e é por isso que é perigoso: a prosa não vai
  para o campo que a tela renderiza.
- Não corrigi o campo. Não escrevo em arquivo de outro agente.
- Não derrubei a tese, não mudei o veredito e não rebaixei a confiança de ninguém: eu não
  tenho veto (D4 em aberto).
- Não afirmei que `manutenção` e `indeterminado` são "incompatíveis" no sentido da seção 3.3 —
  essa é a decisão que falta. O que afirmo é que o campo credita a **`noticia@v1`** um veredito
  que ela não emitiu.

## Conserto possível, para quem for verificar

Ou `colunas.C_noticia.veredito` = `"contraditoria"` (como no USD), ou o `versao_prompt` deixa
de citar `noticia@v1` quando a leitura dele não sustenta o veredito impresso. Qualquer um dos
dois resolve sem mudar régua.

---

## DESFECHO — **preencher DEPOIS da verificação**

```
data_da_verificacao  ____-__-__
quem verificou       Eduardo | revisão | camada 1
a objeção procedia   sim | não | parcialmente
o que mudou          número corrigido | prompt versionado | tese caiu | nada
estado               procedia | nao procedia | sem desfecho
```
