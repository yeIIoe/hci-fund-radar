# CASO — USD, 07/09/2026 · "Trump exige cortes de juros do Fed"

*Este arquivo é o **modelo de formato** de todo caso do agente `noticia`. Copie a estrutura
inteira, inclusive os cabeçalhos.*

⚠️ **Ele NÃO é um caso real.** Foi escrito à mão em 07/09/2026, antes de qualquer rodada existir
(`data/agentes/noticia/` sequer havia sido criado), e quatro dos números dele não existiam no
`data/noticias.json` daquele dia — ver a correção na seção 3 e a lápide L-08. Ficou aqui, com o
erro à vista, porque **lápide não sai**: é mais útil como exemplo do erro do que apagado.*

```
caso_id        noticia-2026-09-07-USD-trump-cortes
agente         noticia
versao_prompt  noticia@v1
rodada_id      noticia-2026-09-07T12:00:00Z
julgado_em     2026-09-07T12:00:00Z
chave          USD
banco          Federal Reserve (Fed)
decisao_alvo   FOMC de 2026-09-16
```

---

## 1. O QUE ENTROU

| Campo | Valor |
|---|---|
| Título | *Trump demands significant interest rate cuts from the Federal Reserve, threatening to halt trade with countries that maintain a trade surplus with the United States* |
| Veículo | 富途牛牛 |
| Quando (UTC) | 2026-09-07T02:29:25+00:00 |
| Link | `https://news.google.com/rss/articles/CBMirwFBVV95cUxQY2Zt…` |
| Degrau da hierarquia | `manchete` — peso **0,0** |
| `peso_fonte` (camada 1) | **0,3** |
| `motivo_origem` (camada 1) | "verbo de fala sem dirigente nomeado" |

Item de contraste na mesma janela, mesma moeda:

| Campo | Valor |
|---|---|
| Título | *Week Ahead for FX, Bonds: U.S. Inflation Data in Focus; ECB Expected to Raise Rates — WSJ* |
| Degrau | `manchete` — peso **0,0**, apesar de `peso_fonte` **1,0** |

---

## 2. AS RÉGUAS, NA ORDEM

| Régua | Resultado |
|---|---|
| **R1 sujeito** | ❌ Derruba. A matéria é sobre a **pressão política** de quem quer o corte, não sobre a política do Fed. Quem pede o corte não decide o corte. |
| **R2 quem fala** | Degrau `manchete` (0,0). Não há dirigente do Fed nomeado com verbo de fala. Não é `imprensa_com_fala`. |
| **R3 tempo verbal** | Não se aplica (R1 já derrubou). |
| **R4 expectativa** | O item de contraste do WSJ ("ECB Expected to Raise") é aposta de jornalista, e ainda é sobre o **EUR**, não o USD. |
| **R5 negação** | Não se aplica. |
| **R6 condição** | Não se aplica. |
| **R7 duplicata** | A camada 1 removeu 1 republicação no USD (`duplicatas_removidas: 1`); este item tem `n_no_grupo: 1`. |

---

## 3. O JULGAMENTO

```
veredito     indeterminado
confianca    baixa
vota         false
selo         experimental — contexto, não vota
```

**Motivo (o que vai para o JSON):** os itens da janela são degrau manchete (peso 0,0): pressão
política pedindo corte e resumo de semana. Nenhum traz dirigente do Fed com verbo de fala. Quem
pede o corte não decide o corte — não há postura do banco a ser lida.

**Trecho literal:**
> "Trump demands significant interest rate cuts from the Federal Reserve"

**Números citados** — todos copiados da camada 1, nenhum calculado aqui:

> ⚠️ **CORREÇÃO DE 07/09/2026, e ela é a lição mais importante deste arquivo.** Este bloco
> saiu com `n_unicos: 78`, `duplicatas_removidas: 13`, `n_cita_dirigente: 2` e `corte 13` —
> **nenhum desses quatro números existia** no `data/noticias.json` da rodada. O arquivo dizia
> 38, 1, 1 e corte 7. O modelo que o agente deve imitar ensinava, por descuido, a inventar
> número — e o item 3 do checklist da seção 6 ficou marcado ✅ mesmo assim. Virou a **lápide
> L-08**, e é o motivo de existir o `verificador_numeros.py`. Os valores abaixo são os medidos.
>
> Fica também o buraco que isso revelou: `data/noticias.json` é **reescrito** a cada 15-35 min
> e **não tem arquivo ponto-no-tempo**. Número citado hoje não é mais conferível amanhã. Por
> isso o verificador roda na mesma rodada, antes do commit.

| Chave | Valor | Origem |
|---|---|---|
| `noticias.moedas.USD.n_unicos` | 38 | `data/noticias.json` |
| `noticias.moedas.USD.n_gravados` | 14 | `data/noticias.json` |
| `noticias.moedas.USD.duplicatas_removidas` | 1 | `data/noticias.json` |
| `noticias.moedas.USD.n_cita_dirigente` | 1 | `data/noticias.json` |
| `noticias.moedas.USD.contagem` | alta 6 / corte 7 / mantém 1 | `data/noticias.json` (**contraste**, não leitura — lápide L-04) |
| `precificacao.moedas.USD.p_alta` | 0.5786 | `data/precificacao.json` |
| `precificacao.moedas.USD.p_manutencao` | 0.4214 | `data/precificacao.json` |

---

## 4. O QUE A FONTE PRIMÁRIA DIZ (seção 8 do PROMPT — fala do banco vence notícia)

*(Corrigido em 07/09: este bloco chamava a seção 8 de "R8". R8 é outra coisa — é a régua de
moeda da seção 5.1, "manchete sozinha nunca vira direção".)*

`data/bc_discursos.json`, mesma janela, USD:

| Orador | Data | Veredito registrado |
|---|---|---|
| Waller | 2026-09-03 | `manutenção` — *"I would be inclined to support holding the target…"* |
| Barr | 2026-09-01 | `alta condicional` — *"if inflation appears not to be moderating sufficiently…"* |
| Warsh | 2026-08-28 | `indeterminado` |

**Contradição a mostrar, não a resolver em silêncio:** a contagem de manchete inclina para
**corte** (7 contra 6), o mercado precifica **alta** (`p_alta` 0,5786) e a fonte primária traz
**manutenção** e **alta condicional**. Três coisas diferentes. O produto da casa é exatamente essa
divergência — o agente a expõe, não escolhe uma delas.

---

## 5. DESFECHO — *preencher DEPOIS da decisão do banco*

> ⚠️ Preencher este bloco no dia do julgamento é look-ahead. Ele só é preenchido depois que a
> reunião acontecer, e o `historico.jsonl` continua guardando o que foi julgado antes.

```
decisao_do_banco      (vazio — FOMC de 2026-09-16)
data_da_decisao       (vazio)
acertou               (vazio: sim / não / não se aplica)
condicao_se_realizou  (só para vereditos condicionais — vazio)
o_que_aprendi         (vazio)
virou_lapide          (vazio: número da lápide, se houver)
```

---

## 6. CHECKLIST DE FECHAMENTO DO CASO

- [x] As sete réguas de item rodaram na ordem, e a que derrubou está escrita; R8 (seção 5.1)
      rodou por último, sobre a moeda inteira.
- [x] O trecho é literal e não foi editado.
- [x] Todo número citado tem caminho de origem na camada 1; nenhum foi calculado aqui.
      **Marcar este item exige ter rodado `python verificador_numeros.py --agente noticia --estrito`
      e colado a saída.** Marcá-lo de memória foi exatamente o que produziu a lápide L-08.
- [x] `vota: false` e o selo estão na saída.
- [x] A contradição com a fonte primária e com o mercado está mostrada.
- [x] O desfecho ficou **vazio**.
- [x] Uma linha foi acrescentada ao `MEMORIA.md` apontando para este arquivo.

*Caso de julgamento. Não é medição e não é recomendação de investimento.*
