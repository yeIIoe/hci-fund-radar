# divergencia@v1:USD — julgou com o dado bloqueado e não declarou

> ⚠️ **Caso semeado à mão em 07/set/2026** para dar ao agente um exemplo concreto de formato
> ao acordar sem contexto. **Não é objeção de rodada real**: nenhum agente havia gravado
> `ultimo.json` nesta data. O trecho abaixo é a **hipótese de julgamento** documentada no
> caso semente do agente `divergencia`, e os números da camada 1 são os reais do dia.

```
caso            2026-09-07-divergencia-USD-frescor-nao-declarado
alvo_agente     divergencia
alvo_versao     divergencia@v1
alvo_rodada     (semeado — sem rodada)
alvo_chave      USD
tipo            buraco tratado como neutro
gravidade       alta
confianca       alta
derruba_a_tese  false
rodada_id       (semeado — sem rodada)
versao_prompt   advogado@v1
estado          aberto
```

## O que o agente afirmou
> *"A casa lê o USD inclinado ao corte (intensidade 36% do teto, convicção 25 de 50, 2 de 4
> dimensões votando); os futuros de fed funds pagam alta, com p_alta 0,5786 contra
> p_manutencao 0,4214 e p_corte 0,0000 (qualidade alta). A casa está mais dovish que o
> preço."*

## O que a camada 1 diz

| o que | valor | campo | arquivo | carimbo |
|---|---|---|---|---|
| estado do dado usado | `muito_atrasado`, `atraso_min: 219` (3h39), **`bloqueia_leitura: true`** | `frescor` | `data/sentimento.json` | `2026-09-06T23:34:07Z` |
| texto do próprio arquivo | *"Dados atrasados em 3h 39min — leituras potencialmente desatualizadas. Não utilizar como nova tese até a sincronização."* | `frescor.texto` | `data/sentimento.json` | idem |
| p_alta USD | `0.5786` | `moedas.USD.p_alta` | `data/precificacao.json` | `2026-09-07T02:44:32Z` |
| direção do lado A | `CORTA` **só depois do teto** — soma antes `-1.19` (direção `MANTEM`), depois `-9.15` | `moedas.USD.dimensoes.dados.deslocamento_pelo_teto` | `data/sentimento.json` | idem |

## A regra violada
- **L6 do meu `LAPIDES.md`** — silêncio não é voto; parte sem dado baixa o denominador. Um
  dado que o próprio painel marca como *"não utilizar como nova tese"* usado sem a
  declaração equivale a tratá-lo como dado bom.
- **Seção 3.4 do `PROMPT.md` do `divergencia`**, escrita por ele mesmo: com
  `bloqueia_leitura = true`, **toda a rodada sai com `confianca: "baixa"`** e a frase do
  frescor entra em `limites`, com o atraso em minutos.
- **L8** como agravante: a direção `CORTA` do lado A só existe **depois** da winsorização —
  cortar cinco itens deslocou a soma em −7,96 e mudou a direção de MANTEM para CORTA. Uma
  divergência cuja direção nasce do teto tem de dizer isso ao lado.

## Por que isto importa para quem lê a tela
A conclusão ("a casa está mais dovish que o preço") pode continuar de pé — a distância entre
`inclinado ao corte` e `p_alta 0,5786` é grande demais para 3h39 de atraso reverterem. O que
está errado é o **estatuto**: sem a declaração, o leitor recebe uma comparação velha com
cara de comparação fresca, a dez dias do FOMC. É a nota que o dono mede e chama de
confiabilidade operacional.

## O que eu **não** afirmei
- Não afirmei que o veredito está errado.
- Não recalculei nada, não estimei o que a leitura seria com dado fresco, e não corrigi
  número nenhum: apontar a discrepância é meu, corrigir é da camada 1.
- Não removi, não rebaixei e não vetei a tese. **Não tenho veto** (D4 em aberto): esta
  objeção vai para a tela ao lado do julgamento.

---

## DESFECHO — **preencher DEPOIS da verificação**

```
data_da_verificacao  ____-__-__
quem verificou       ____
a objeção procedia   ____
o que mudou          ____
estado               aberto
```

**O que aprendi:**
*(em branco)*
