# MODELO DE CASO — agente `divergencia`

Copie este arquivo para `casos/AAAA-MM-DD-<moeda>-<resumo-curto>.md` e preencha. **O bloco
DESFECHO fica em branco na hora do julgamento** — ele é preenchido depois, quando o banco
central decidir. É esse preenchimento posterior que transforma memória em aprendizado; sem
ele, a pasta `casos/` é só um diário.

---

```
caso            AAAA-MM-DD-<moeda>-<resumo>
moeda           USD | EUR | GBP | JPY | AUD | NZD | CAD | CHF
rodada_id       divergencia-AAAAMMDDTHHMMZ
versao_prompt   divergencia@v1
veredito        ALINHADO | HCI MAIS HAWKISH | HCI MAIS DOVISH | SEM FONTE
confianca       alta | media | baixa
destaque        noticia_aperta_preco_parado | noticia_afrouxa_preco_parado | null
proxima_reuniao AAAA-MM-DD (banco)
estado          aberto
```

## As três colunas, como estavam no instante do julgamento

| coluna | valor | número citado | arquivo e carimbo |
|---|---|---|---|
| **A — casa** | `leitura_texto` | intensidade X% do teto · convicção Y de Z · N de 4 dimensões · qualidade da evidência W/100 | `data/sentimento.json` · `gerado_em` |
| **B — mercado** | `direcao_mercado` | p_alta · p_corte · p_manutencao · implícito em bp · qualidade | `data/precificacao.json` · `gerado_em` |
| **C — notícia** | veredito do agente | confiança · versão do prompt | `data/agentes/<nome>/ultimo.json` · `gerado_em` |

## Por que este caso foi registrado
*(uma frase: o que nele é inédito ou digno de destaque)*

## O que o painel disse, palavra por palavra
> *(o `motivo` do julgamento, copiado)*

## Limites declarados na hora
- *(frescor, qualidade da precificação, coluna ausente...)*

---

## DESFECHO — **preencher DEPOIS da decisão do banco central**

```
data_da_decisao   ____-__-__
o que o banco fez  alta | corte | manutenção  (+ tamanho em bp)
o que a casa lia   ____
o que o preço pagava ____
quem estava mais perto ____
estado             acertou | errou | sem desfecho
```

**O que aprendi:**
*(uma frase. Se for erro repetível, abrir lápide em `LAPIDES.md`, seção 2 — só a revisão
escreve lápide, nunca a rodada.)*

**Cuidado com a leitura do desfecho:** um acerto não valida o agente e um erro não o
invalida. Um caso não é amostra. Convicção histórica continua `null` até haver backtest com
amostra declarada e controle pareado.
