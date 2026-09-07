# MODELO DE CASO — agente `vigia`

Copie para `casos/AAAA-MM-DD-<cadeia>-<resumo-curto>.md` e preencha. O bloco **CAUSA
CONFIRMADA** fica em branco na hora do alarme — ele é preenchido **depois**, quando o
conserto for feito e a cadeia voltar. É esse preenchimento posterior que transforma memória
em aprendizado; sem ele, a pasta `casos/` é só um diário.

---

```
caso              AAAA-MM-DD-<cadeia>-<resumo>
cadeia            macro-direction | cadeia-2x-dia | nowcast-1h | macro | sentinela-equities | pages
rodada_id         vigia-AAAAMMDDTHHMMZ
versao_prompt     vigia@v1
alarmes           <identificadores, separados por vírgula>
gravidade         alta | media | baixa
causa_suspeitada  teto de tempo estourado | fonte fora do ar | cota da fonte esgotada |
                  permissão ou chave ausente | configuração alterada |
                  cancelada por sobreposição | atraso do próprio GitHub |
                  workflow desligado | indeterminado
causa_confianca   alta | media | baixa | null
estado            aberto
```

## A medição no instante do alarme

| checagem | número | de onde veio |
|---|---|---|
| execuções | rodou X de Y previstas em Z h | `medicao.execucoes` · API do GitHub |
| conclusões | A sucesso · B canceladas · C falha · D estouro de teto | `medicao.execucoes` |
| passos pulados | quais, em quais execuções, duração contra o teto | `medicao.passos_pulados` |
| idade | quais arquivos, com que carimbo e que tolerância provisória | `medicao.idade` |
| frescor | `atraso_min`, `estado`, `bloqueia_leitura`, `fora_da_tolerancia` | `medicao.frescor` |
| snapshots | última linha, linhas por dia, dias sem linha | `medicao.snapshots` |

## Por que este caso foi registrado
*(uma frase: o que nele é inédito, ou qual assinatura ele ensina a reconhecer)*

## A assinatura — o que exatamente permitiu (ou não) nomear a causa
*(item por item da tabela da seção 5 do PROMPT. Se faltou um, escreva qual, e por que a
causa saiu `indeterminado`.)*

## O que o painel disse, palavra por palavra
> *(o `resumo_pt` da rodada, copiado)*

## O custo, em frase inteira
*(o que ficou velho, o que não foi recalculado, o que a série de snapshots perdeu. O dano
irreversível — dia sem snapshot — vem separado do reversível.)*

## Limites declarados na hora
- *(API não consultada, carimbo sem fuso, tolerância provisória, teto de consultas...)*

---

## CAUSA CONFIRMADA — **preencher DEPOIS do conserto**

```
data_do_conserto  ____-__-__
o que foi feito   ____
a cadeia voltou   sim | não | parcialmente
causa real        ____
estado            confirmado | refutado | sem desfecho
```

**O que aprendi:**
*(uma frase. Se for erro repetível meu, abrir lápide em `LAPIDES.md`, seção 2 — e só a
revisão escreve lápide, nunca a rodada.)*

**Cuidado com a leitura do desfecho:** uma causa confirmada não valida o agente e uma
refutada não o invalida. Um caso não é amostra. Não existe convicção histórica aqui: as
tolerâncias são provisórias e nunca foram medidas contra uma distribuição real.
