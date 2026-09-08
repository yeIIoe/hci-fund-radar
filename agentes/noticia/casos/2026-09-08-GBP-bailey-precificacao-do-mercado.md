# CASO — GBP, 08/09/2026 · "Bailey Says Market Rate-Hike Pricing Reflects 'Risk Premium'"

```
caso_id        noticia-2026-09-08-GBP-bailey-precificacao-do-mercado
agente         noticia
versao_prompt  noticia@v1
rodada_id      noticia-2026-09-08T15:20:00Z
julgado_em     2026-09-08T15:20:00Z
chave          GBP
banco          Bank of England (BoE)
decisao_alvo   BoE de 2026-09-17  (precificacao.moedas.GBP.proxima)
```

**Por que virou caso:** duas réguas brigaram — R4 e R2/R8 — e é a **segunda vez** que o BoE
produz o mesmo padrão: a palavra "hike" na frase de um dirigente, mas o sujeito da frase é o
**mercado**. A primeira foi o Pill, e virou a lápide **L-02**.

---

## 1. O QUE ENTROU

| Campo | Valor |
|---|---|
| Título | *BOE Governor Bailey Says Market Rate-Hike Pricing Reflects 'Risk Premium'* |
| Veículo | finance.biggo.com |
| Quando (UTC) | 2026-09-08T14:35:00+00:00 |
| Degrau da hierarquia | `manchete` — peso **0,0** (`noticias.moedas.GBP.itens.0.peso`) |
| `peso_fonte` | **0,3** (`noticias.moedas.GBP.itens.0.peso_fonte`) |
| `orador_identificado` | Bailey |
| `motivo_origem` (camada 1) | "veiculo de peso 0.30 — abaixo do limiar provisorio 0.60" |

Mesma notícia, outro título, sobreviveu à deduplicação:

| Campo | Valor |
|---|---|
| Título | *BoE's Bailey: Market Curve Reflects Inflation Risk Premium for UK* |
| Veículo | Global Banking & Finance Review — `n_no_grupo` 2 |

Itens de contraste na mesma janela, todos degrau 0,0:

- *Bank of England to hold rates, show patience with war-driven inflation: **Reuters poll*** —
  pesquisa com economistas, `peso_fonte` 1,0, degrau ainda 0,0.
- *BNP Paribas **expects** the BoE to lift interest rates by 25bps in November 2026* — previsão
  de banco.
- *Chile Inflation Comes in Above Expectations…* e *'People are furious': RBA deputy governor
  says…* — **moeda errada**, caíram na lista da libra.

---

## 2. AS RÉGUAS, NA ORDEM

| Régua | Resultado |
|---|---|
| **R1 sujeito** | ✅ Passa no item do Bailey: é o governador do BoE falando de juro do Reino Unido. |
| **R2 quem fala** | ⚠️ **Derruba.** Dirigente nomeado + verbo de fala existem, mas o veículo tem `peso_fonte` 0,30, abaixo do limiar provisório 0,60 — a camada 1 gravou degrau `manchete`, peso 0,0. Nome de dirigente **não basta**: o degrau exige os três. |
| **R3 tempo verbal** | Não se aplica. |
| **R4 expectativa** | ⚠️ **Derruba também, e é o coração do caso.** O que a frase diz é que a **precificação do mercado** embute prêmio de risco. Isso é comentário sobre o mercado, não postura sobre o próximo passo. Marcar `alta` porque a palavra "Rate-Hike" está ali seria repetir a L-02 — e, como no caso Pill, marcar o **oposto** da intenção: o orador está relativizando a curva, não endossando-a. |
| **R5 negação** | Não se aplica. |
| **R6 condição** | Não se aplica. |
| **R7 duplicata** | Os itens 0 e 1 são a mesma notícia com títulos diferentes. Julgada **uma vez**; a falha da deduplicação foi para `limites`. |
| **R8 (moeda)** | Dispara: **todos** os itens que sobreviveram são degrau 0,0 → o veredito da moeda não pode ser direção. |

---

## 3. O JULGAMENTO

```
veredito     indeterminado
confianca    baixa
vota         false
selo         experimental — contexto, não vota
```

**Trecho literal:**
> "BOE Governor Bailey Says Market Rate-Hike Pricing Reflects 'Risk Premium'"

**Números citados** — todos da camada 1; `verificador_numeros.py --agente noticia --estrito`
rodou nesta mesma rodada e voltou limpo.

| Chave | Valor | Origem |
|---|---|---|
| `noticias.moedas.GBP.n_gravados` | 14 | `data/noticias.json` |
| `noticias.moedas.GBP.n_unicos` | 46 | `data/noticias.json` |
| `noticias.moedas.GBP.duplicatas_removidas` | 2 | `data/noticias.json` |
| `noticias.moedas.GBP.n_cita_dirigente` | 3 | `data/noticias.json` |
| `noticias.moedas.GBP.contagem.alta` / `.mantem` | 2 / 1 | `data/noticias.json` (**contraste** — L-04) |
| `noticias.moedas.GBP.itens.0.peso` / `.peso_fonte` | 0,0 / 0,3 | `data/noticias.json` |

Sem coluna de mercado: `precificacao.moedas.GBP` está com qualidade "sem fonte" nesta rodada —
*"nenhum item de Reuters/Bloomberg/FT/WSJ com ate 7 dias entre os 116 resultados lidos"*. Logo,
não existe divergência a medir para a libra hoje.

---

## 4. O QUE A FONTE PRIMÁRIA DIZ (seção 8)

`data/bc_discursos.json`, `veredito_por_orador.GBP`:

| Orador | Data | Veredito registrado |
|---|---|---|
| Andrew Bailey | 2026-09-04 | `indeterminado` — *"nenhuma frase de postura foi extraída do texto"* |
| Pill | 2026-09-03 | `indeterminado` — *"o que aparece é a expectativa do MERCADO…"* |

**Não há contradição a expor: há concordância.** O site do BoE, lido pela camada 1, também não
produziu postura; a notícia sobre o Bailey também não. A imprensa aqui não está adiantando nada
que a fonte primária desminta — ela está repetindo, com uma palavra chamativa no título, um
comentário sobre a curva.

---

## 5. O QUE ESTE CASO ENSINA

1. **O padrão L-02 não era do Pill; é do BoE.** Dois oradores diferentes, duas rodadas
   diferentes, a mesma armadilha: dirigente do BoE comentando o que o **mercado** precifica. Vale
   tratar "market pricing", "market curve", "risk premium" na frase de um dirigente como sinal de
   alerta de R4, não como postura.
2. **Cargo e nome não compram degrau.** "BOE Governor Bailey" é o nome mais forte possível e o
   item continua peso 0,0, porque o veículo ficou abaixo do limiar. O limiar de 0,60 é
   **provisório** e não tem backtest — está registrado como tal na camada 1.
3. **A lista da libra está vazando.** Dois dos 14 itens são de outras moedas (Chile, RBA). Foi
   para `limites`.

---

## 6. DESFECHO — *preencher DEPOIS da decisão do banco*

```
decisao_do_banco      (vazio — BoE de 2026-09-17)
data_da_decisao       (vazio)
acertou               (vazio: sim / não / não se aplica)
condicao_se_realizou  (não se aplica — o veredito não é condicional)
o_que_aprendi         (vazio)
virou_lapide          (vazio)
```

---

## 7. CHECKLIST DE FECHAMENTO DO CASO

- [x] As sete réguas de item rodaram na ordem, e as duas que derrubaram (R2 e R4) estão escritas;
      R8 rodou por último, sobre a moeda inteira.
- [x] O trecho é literal e não foi editado.
- [x] Todo número citado tem caminho de origem na camada 1; nenhum foi calculado aqui.
      `python verificador_numeros.py --agente noticia --estrito` rodou na mesma rodada e voltou
      **limpo** (todos `[ok]`, código de saída 0).
- [x] `vota: false` e o selo estão na saída.
- [x] A relação com a fonte primária está mostrada (concordância, não contradição), e a ausência
      de precificação com fonte está declarada.
- [x] O desfecho ficou **vazio**.
- [x] Uma linha foi acrescentada ao `MEMORIA.md` apontando para este arquivo.

*Caso de julgamento. Não é medição e não é recomendação de investimento.*
