# CASO — AUD, 08/09/2026 · "RBA's Hunter Says Inflation Top Priority, May Have to Raise Rate"

```
caso_id        noticia-2026-09-08-AUD-rba-may-have-to-raise
agente         noticia
versao_prompt  noticia@v1
rodada_id      noticia-2026-09-08T15:20:00Z
julgado_em     2026-09-08T15:20:00Z
chave          AUD
banco          Reserve Bank of Australia (RBA)
decisao_alvo   RBA de 2026-09-29  (precificacao.moedas.AUD.proxima)
```

**Por que virou caso:** confiança `media` — o único item da rodada inteira, nas oito moedas,
que subiu acima do degrau `manchete`.

---

## 1. O QUE ENTROU

Item representante (o de maior `peso_fonte` entre os dois de degrau 0,4):

| Campo | Valor |
|---|---|
| Título | *RBA's Hunter Says Inflation Top Priority, May Have to Raise Rate* |
| Veículo | bloomberg.com |
| Quando (UTC) | 2026-09-08T09:19:51+00:00 |
| Degrau da hierarquia | `imprensa_com_fala` — peso **0,4** (`noticias.moedas.AUD.itens.1.peso`) |
| `peso_fonte` | **1,0** (`noticias.moedas.AUD.itens.1.peso_fonte`) |
| `orador_identificado` | Hunter |
| `motivo_origem` | `null` — passou na régua da camada 1 |

Segundo item do mesmo degrau, na mesma janela:

| Campo | Valor |
|---|---|
| Título | *Inflation is too high and rates may need to rise, warns RBA's Hauser* |
| Veículo | AFR — `peso_fonte` **0,8** (`noticias.moedas.AUD.itens.0.peso_fonte`) |
| Degrau | `imprensa_com_fala` — peso **0,4** |
| `orador_identificado` | Hauser |

---

## 2. AS RÉGUAS, NA ORDEM

| Régua | Resultado |
|---|---|
| **R1 sujeito** | ✅ Passa. O assunto é a política de juros do RBA, dita por dirigente do RBA. |
| **R2 quem fala** | Degrau `imprensa_com_fala` (0,4): dirigente **nomeado** (Hunter; Hauser) + verbo de fala ("Says"; "warns") + veículo acima do limiar. Não é manchete de jornalista opinando — é a diferença que a lápide L-05 cobra. |
| **R3 tempo verbal** | ✅ Passa. "May have to raise" é sobre o próximo passo, não balanço do aperto já feito. |
| **R4 expectativa** | ✅ Passa. Quem fala é o dirigente, não o mercado. Não é o caso Pill (L-02). |
| **R5 negação** | Não se aplica — não há cue de negação antes do marcador. |
| **R6 condição** | ⚠️ **Rebaixa.** "may need to rise" / "may have to raise" não é compromisso: o aperto está preso a a inflação não ceder. → `alta condicional`, nunca `alta`. |
| **R7 duplicata** | O mesmo episódio de fala do vice do RBA sobreviveu à deduplicação sob **sete** títulos (itens 2, 4, 6, 7, 9, 11 e 13 do AUD) e ainda vazou para a lista do GBP (item 12). Julgado **uma vez**, pelo item de maior `peso_fonte`; a falha da dedup foi para `limites`, não consertada em silêncio. |
| **R8 (moeda)** | Não dispara: há item acima do degrau 0,0. Foi a **única** moeda da rodada assim. |

---

## 3. O JULGAMENTO

```
veredito     alta condicional
confianca    media
vota         false
selo         experimental — contexto, não vota
```

**Trecho literal:**
> "RBA's Hunter Says Inflation Top Priority, May Have to Raise Rate"

**Números citados** — todos copiados da camada 1, nenhum calculado aqui. O
`verificador_numeros.py --agente noticia --estrito` rodou **nesta mesma rodada** e voltou limpo.

| Chave | Valor | Origem |
|---|---|---|
| `noticias.moedas.AUD.n_gravados` | 14 | `data/noticias.json` |
| `noticias.moedas.AUD.n_unicos` | 34 | `data/noticias.json` |
| `noticias.moedas.AUD.duplicatas_removidas` | 1 | `data/noticias.json` |
| `noticias.moedas.AUD.n_cita_dirigente` | 2 | `data/noticias.json` |
| `noticias.moedas.AUD.contagem.alta` | 7 | `data/noticias.json` (**contraste**, não leitura — L-04) |
| `noticias.moedas.AUD.itens.1.peso` / `.peso_fonte` | 0,4 / 1,0 | `data/noticias.json` |
| `noticias.moedas.AUD.itens.0.peso` / `.peso_fonte` | 0,4 / 0,8 | `data/noticias.json` |
| `precificacao.moedas.AUD.p_alta` | 0,66 | `data/precificacao.json` |
| `precificacao.moedas.AUD.p_manutencao` | 0,34 | `data/precificacao.json` |
| `precificacao.moedas.AUD.implicito_bp` | 16,5 | `data/precificacao.json` |

---

## 4. O QUE A FONTE PRIMÁRIA DIZ (seção 8)

**Não existe.** O RBA é buraco declarado em `data/noticias.json → buraco_declarado`: o banco
bloqueia automação, e `data/bc_discursos.json` não tem entrada de AUD. A leitura fica só sobre
imprensa — que é exatamente por que esta dimensão não vota.

**Divergência contra o mercado: não há.** A leitura aponta para aperto condicional e a
precificação aponta para alta (`p_alta` 0,66 contra `p_manutencao` 0,34 na reunião de 29/09).
Quando os dois lados apontam para o mesmo lugar, **não existe o produto da casa** — e dizer isso
é tão informativo quanto apontar a divergência.

---

## 5. A TENSÃO QUE ESTE CASO ABRIU — o modal "may"

A R6 lista marcadores de condição: "if", "should inflation", "were the data to", "caso", "se".
**"May" / "pode" não está na lista.** Li o modal como condicional, indo para o lado mais fraco,
mas isso é uma **extensão** da régua feita no julgamento — não um precedente. A régua precisa
decidir explicitamente se modal de possibilidade rebaixa como o "se" rebaixa. Enquanto não
decidir, dois leitores diferentes podem sair com `alta` e com `alta condicional` a partir da mesma
frase — que é o mesmo tipo de buraco que produziu a R8.

Registrado em `limites` da rodada.

---

## 6. DESFECHO — *preencher DEPOIS da decisão do banco*

```
decisao_do_banco      (vazio — RBA de 2026-09-29)
data_da_decisao       (vazio)
acertou               (vazio: sim / não / não se aplica)
condicao_se_realizou  (vazio — a condição é "a inflação não ceder"; medir à parte, como manda a seção 9)
o_que_aprendi         (vazio)
virou_lapide          (vazio)
```

---

## 7. CHECKLIST DE FECHAMENTO DO CASO

- [x] As sete réguas de item rodaram na ordem, e a que rebaixou (R6) está escrita; R8 rodou por
      último, sobre a moeda inteira, e não disparou.
- [x] O trecho é literal e não foi editado.
- [x] Todo número citado tem caminho de origem na camada 1; nenhum foi calculado aqui.
      `python verificador_numeros.py --agente noticia --estrito` rodou na mesma rodada e voltou
      **limpo** (todos `[ok]`, código de saída 0).
- [x] `vota: false` e o selo estão na saída.
- [x] A ausência de fonte primária e a ausência de divergência contra o mercado estão mostradas.
- [x] O desfecho ficou **vazio**.
- [x] Uma linha foi acrescentada ao `MEMORIA.md` apontando para este arquivo.

*Caso de julgamento. Não é medição e não é recomendação de investimento.*
