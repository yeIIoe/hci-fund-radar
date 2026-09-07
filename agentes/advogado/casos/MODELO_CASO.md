# MODELO DE CASO — agente `advogado`

Copie este arquivo para `casos/AAAA-MM-DD-<agente>-<chave>-<tipo>.md` e preencha. **O bloco
DESFECHO fica em branco na hora da objeção** — ele é preenchido depois, quando alguém
verificar se a objeção procedia.

Abra caso para **toda objeção de gravidade alta**. As médias e baixas ficam só no
`historico.jsonl`.

---

```
caso            AAAA-MM-DD-<agente>-<chave>-<tipo>
alvo_agente     noticia | divergencia | falas | ...
alvo_versao     <agente>@vN
alvo_rodada     <rodada_id do julgamento auditado>
alvo_chave      USD | EUR | ... | par | evento
tipo            numero fantasma | contradiz lapide | fonte fraca |
                buraco tratado como neutro | contradicao entre agentes | eco
gravidade       alta | media | baixa
confianca       alta | media | baixa
derruba_a_tese  false   (sempre false na v1 — D4 em aberto)
rodada_id       advogado-AAAAMMDDTHHMMZ
versao_prompt   advogado@v1
estado          aberto
```

## O que o agente afirmou
> *(trecho literal, copiado do `motivo` ou do `trecho` dele)*

## O que a camada 1 diz

| o que | valor | campo | arquivo | carimbo |
|---|---|---|---|---|
| citado pelo agente | | | | |
| medido pela camada 1 | | | | |

## A regra violada
*(qual lápide, qual lei da casa, ou qual linha do `PROMPT.md` do próprio agente — citada
pelo identificador, não parafraseada)*

## Por que isto importa para quem lê a tela
*(uma frase: a conclusão muda? só o número exibido está errado? o leitor seria induzido a
quê?)*

## O que eu **não** afirmei
*(o limite da objeção — eu aponto a discrepância, não corrijo o número, não decido quem tem
razão, e não removo a tese)*

---

## DESFECHO — **preencher DEPOIS da verificação**

```
data_da_verificacao  ____-__-__
quem verificou       Eduardo | revisão | camada 1
a objeção procedia   sim | não | parcialmente
o que mudou          número corrigido | prompt versionado | tese caiu | nada
estado               procedia | nao procedia | sem desfecho
```

**O que aprendi:**
*(uma frase. Se a objeção **não** procedia, abrir lápide na seção 3 de `LAPIDES.md` — só a
revisão escreve lápide, nunca a rodada.)*

**Cuidado:** uma objeção procedente não me valida e uma infundada não me invalida. Um caso
não é amostra, e este agente não tem convicção histórica — nunca foi medido contra desfecho.
