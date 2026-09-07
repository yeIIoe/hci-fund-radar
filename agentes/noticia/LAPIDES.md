# LÁPIDES DO AGENTE `noticia`

*Erros já cometidos pela casa na leitura de texto de banco central. **Leia isto ANTES de julgar,
não depois.** Lápide não sai, não se relativiza e não vira "mas neste caso…". Cada uma tem o caso
real, o que foi marcado, o que era, e a régua que passa a valer.*

---

## L-01 — "holding the target" contado como ALTA (Waller, Fed, 03/09/2026)

**O que aconteceu.** O painel marcava a leitura do USD como *hawkish* porque a expressão
`holding the target` estava na lista de termos de alta da contagem de palavra.

**O que o orador disse:**
> "If this continues in the data due over the next two weeks, I would be inclined to support
> holding the target for the federal funds rate at its current setting."

**O que era:** `manutenção`. Duas coisas erradas ao mesmo tempo: a contagem leu "target" e
"holding" como movimento de alta, e ignorou que apoiar **manter** é o oposto de apoiar subir.

**Régua que passa a valer (R5).** Expressão de manutenção nunca é lida como direção. E a condição
não rebaixa a manutenção: *manter sob condição continua manter* — não existe "manutenção
condicional".

**Consequência.** A dimensão FALA parou de votar em 05/09/2026. Registro em
`data/bc_discursos.json → veredito_por_orador.USD[Waller]`.

---

## L-02 — expectativa do MERCADO lida como postura do orador (Pill, BoE, 03/09/2026)

**O que aconteceu.** O classificador de regra encontrou "Bank Rate cuts" na frase e por pouco não
marcou `corte` para o GBP.

**O que o orador disse:**
> "Just as we the MPC was wary of allowing markets to 'get-ahead-of-themselves' with respect to
> prospective Bank Rate hikes …, we should also recognise that markets may have already
> 'gotten-ahead-of-themselves' with respect to prospective Bank Rate cuts…"

**O que era:** `indeterminado`. O orador estava avisando que **o mercado** se adiantou. Marcar
`corte` seria marcar o **oposto** do que ele quis dizer.

**Régua que passa a valer (R4).** "markets price", "traders bet", "economists expect", "expected
to raise", "futures imply", "odds rose" — nada disso é postura. Expectativa de mercado só aparece
em `numeros_citados`, copiada de `data/precificacao.json`, como coluna de comparação.

**Registro:** `data/bc_discursos.json → veredito_por_orador.GBP[Pill]`, motivo: *"o que aparece é
a expectativa do MERCADO ('prospective rate hikes'), não a postura do orador."*

---

## L-03 — filtrar por TÍTULO joga fora sinal real (Barr, Fed, 01/09/2026)

**O que aconteceu.** O filtro de assunto era por título. O discurso do Barr se chamava:

> "Unlocking Opportunities for Workers and Entrepreneurs with a Criminal Record"
> *(Destravando oportunidades para trabalhadores com ficha criminal)*

Um filtro por título descartaria a peça inteira — não fala de juro, não fala de inflação, parece
tema social. Só que **dentro do corpo** estava:

> "However, if inflation appears not to be moderating sufficiently, then I think we should act
> decisively to raise rates."

**O que era:** `alta condicional`, com trecho literal e condição explícita. Um sinal real, jogado
fora por causa do nome da peça.

**Régua que passa a valer.** **Filtro é por FRASE, nunca por título.** O título entra só como
contexto. O corpo mandava: 17 termos fortes, contra um mínimo de 3 — e o veredito de assunto
gravado é *"titulo neutro, mas 17 termos fortes no corpo"*.

**Consequência para o agente `noticia`:** manchete curta e aparentemente fora do assunto **não é
motivo suficiente** para mandar o item para `nao_julgados`. Se houver texto, leia o texto. Se não
houver, o motivo em `nao_julgados` é *"só título, sem corpo"* — não *"título fora do assunto"*.

**Registro:** `data/bc_discursos.json → itens[Barr 2026-09-01].assunto`.

---

## L-04 — contagem de palavra apresentada como leitura

**O que aconteceu.** `noticias.json` traz `moedas.<X>.contagem` (alta / corte / mantem) e
`inclinacao_por_manchete`. Isso é **contagem de expressão em manchete**, com peso 0,0 — não é
leitura, não lê negação, não lê condição, não lê tempo verbal e não lê sujeito. O próprio arquivo
avisa: *"Contagem de expressão na manchete, não leitura."*

**Régua que passa a valer.** Nunca copie `inclinacao_por_manchete` para o campo `veredito`. Se
citar `contagem`, cite como **contraste** — "a contagem de palavra inclina para corte; a leitura
das frases não sustenta" — e sempre com o número em `numeros_citados`.

---

## L-05 — veículo forte confundido com fonte primária

**O que aconteceu.** Manchete do WSJ — *"Week Ahead for FX, Bonds: U.S. Inflation Data in Focus;
ECB Expected to Raise Rates"* — tem `peso_fonte` 1,0, o mesmo da Reuters e do site do banco. É
tentador tratar como fala.

**O que era:** degrau `manchete`, peso 0,0. Jornalista resumindo a semana e **apostando**
("Expected to Raise") — o que ainda cai em L-02.

**Régua que passa a valer (R2).** `peso_fonte` mede a **qualidade do veículo**; `hierarquia_pesos`
mede **quem falou**. São coisas diferentes e não se somam. Veículo forte não transforma opinião de
jornalista em fala de dirigente. Só sobe para `imprensa_com_fala` (0,4) com **dirigente nomeado +
verbo de fala + veículo acima do limiar**.

---

## L-06 — volume de notícia tratado como direção (geopolítica, 05/09/2026)

**O que aconteceu.** A dimensão geopolítica media **quantas** notícias apareciam, não o que elas
diziam. Parou de votar em 05/09/2026 por isso.

**Régua que passa a valer (R7).** Cinco republicações da mesma frase não são cinco sinais. A mesma
notícia republicada conta **uma vez**. Um assunto muito coberto não é um assunto com direção mais
forte. E moeda com muita notícia e nenhuma fala continua `sem dados` — silêncio não é voto, e
barulho também não.

---

## L-07 — percentil sem a janela declarada ao lado

**O que aconteceu.** Fora deste agente, mas é lei da casa e vale aqui: em 31/08 e 02/09/2026, a
casa chamou de "máxima histórica" o que era máxima de 5 anos, duas vezes, em pares diferentes.

**Régua que passa a valer.** Se o `motivo` mencionar extremo, recorde, máxima ou percentil, a
**janela tem de estar escrita ao lado** ("máxima de 252 dias"). Sem janela, não escreva. E o
número vem da camada 1 — você não mede extremo nenhum.

---

## L-08 — número inventado no próprio exemplo do prompt (a casa, 07/09/2026)

**O que aconteceu.** O exemplo da seção 10 do `PROMPT.md` e o caso-modelo `casos/EXEMPLO.md`
citavam, como se fossem da camada 1:

| citado | o que `data/noticias.json` dizia |
|---|---|
| `noticias.moedas.USD.n_unicos` = 78 | **38** |
| `noticias.moedas.USD.duplicatas_removidas` = 13 | **1** |
| `noticias.moedas.USD.n_cita_dirigente` = 2 | **1** |
| `contagem.corte` = 13 | **7** |

Quatro números, nenhum existente. E o checklist do caso trazia marcado ✅ o item *"todo número
citado tem caminho de origem na camada 1; nenhum foi calculado aqui"*. O modelo que o agente
deve copiar ensinava a inventar número, e o item de conferência que existia para pegar isso foi
marcado de memória.

**Por que passou.** Porque **nada no repositório conferia**. O `ARQUITETURA_AGENTES.md`, seção
6, prometia o remédio — *"o verificador confere cada número citado contra a camada 1"* — e o
verificador não existia. Proibição em prompt, sem máquina que confira, é decoração.

**Régua que passa a valer.**
1. Antes de gravar, rode `python verificador_numeros.py --agente noticia --estrito` e só marque
   o item do checklist se ele voltar limpo. Rodar verificador é conferência de forma, como o
   `json.load` — não é conta de análise.
2. **Na mesma rodada.** `data/noticias.json` é reescrito a cada 15-35 min e **não tem arquivo
   ponto-no-tempo**: um número citado hoje deixa de ser conferível meia hora depois. Esse é um
   buraco declarado da camada 1, não um detalhe.
3. Exemplo de prompt e caso-modelo **são dado**, não ilustração. Número em exemplo tem de bater
   com o arquivo, ou vem escrito ao lado que é fictício.

---

*Oito lápides. Se você repetir qualquer uma delas, a versão do prompt sobe e o erro fica gravado
no `historico.jsonl` com o nome da versão que errou.*
