# LÁPIDES — agente `vigia`

O que este agente **não pode repetir**. Lápide é erro comprovado, com número e data ao
lado. Refutação é ativo: a mesma sereia não canta duas vezes.

Este arquivo nasce com as lápides **herdadas da casa** — erros que a HCI já cometeu e que
este agente está em posição de cometer de novo. As lápides **próprias** entram na seção 2, e
só a revisão as escreve, nunca a rodada.

---

## 1. HERDADAS DA CASA — valem desde o primeiro disparo

### ⚰️ L-H8 · O `mtime` mente na nuvem
**O erro:** 31/ago/2026 — todas as fontes ficaram **uma semana congeladas** (curvas de 2
anos das oito moedas, preços do BCE, calendário) e **nada reclamou**. O TTL decidia refazer
o download pelo `mtime`, e o `actions/checkout` reescreve o mtime de todo arquivo a cada
execução: na nuvem o arquivo é sempre "de agora". O bug só aparece **depois** de migrar para
CI — na máquina local o mtime era real e tudo funcionava.
**A proibição:** eu **nunca** leio o `mtime`, o `st_ctime` ou a data do sistema de arquivos.
Idade sai do carimbo **dentro** do arquivo (`gerado_em`, `meta.generated_at`), com o campo
lido declarado ao lado. Se o arquivo não tem carimbo, a resposta é "não é vigiado por
ninguém" — nunca uma idade que eu tirei de outro lugar.

### ⚰️ L-H9 · Vigiar a caixa de e-mail é vigiar o modo errado de falhar
**O erro:** 07/set/2026 — a cadeia `macro-direction` rodou **6 vezes de 96** em 24 h, com
**4 execuções canceladas**, e o dono **não recebeu nada**. Cancelamento não gera e-mail do
GitHub; só `failure` gera. Os arquivos ficaram de **17 a 35 horas** velhos e a série de
snapshots parou.
**A proibição:** eu não uso notificação, e-mail ou alerta como evidência de nada. Minhas
duas fontes são o **repositório** (carimbo dentro do arquivo) e a **API pública do GitHub**
(execuções, conclusões e passos). E `cancelled` conta como falha, sempre.

### ⚰️ L-H10 · Artefato de relógio: fuso e defasagem antes de qualquer conclusão
**O erro:** o "+0,107 em 1 dia" do FUND era artefato de relógio — o BCE fixa às 14:15 CET e
o yield fechava depois; com 1 dia de gap o achado sumia. E as horas do dono são BRT
enquanto a Dukascopy é UTC (+3 h).
**A proibição:** `frescor.json` e `juros_vs_cambio.json` gravam a hora **sem fuso**. Quando
`carimbo_sem_fuso` for verdadeiro, a frase vai junto: lido como UTC, e se foi escrito na
máquina do dono (BRT) a idade está superestimada em até 3 h. Nunca abro alarme de idade por
margem menor que essa em arquivo com carimbo ingênuo.

### ⚰️ L-H11 · Percentil sem janela declarada não existe
**O erro:** 31/ago/2026 — o painel afirmou percentil 98 para o AUDCHF e 97 para o GBPNZD;
com a janela corrigida eram **85 e 61**. Dois dias depois o dono cometeu o gêmeo: confundiu
a máxima de **5 anos** do AUDCAD (0,99672) com a máxima histórica (1,07738, fev/2012, 8%
acima).
**A proibição:** nenhum "pior dia", "recorde", "nunca visto" ou percentil sai da minha boca
sem a **janela declarada grudada no número**. A minha série tem poucos dias; dizer "o pior
dia da série" sem dizer que a série tem uma semana é mentir com número verdadeiro.

### ⚰️ L-H12 · Silêncio não é voto, e ausência de medição não é saúde
**O erro:** a régua da casa é explícita — dimensão sem dado sai `null` e **baixa o
denominador**, nunca conta como zero. O buraco que faz "sem informação" virar "equilíbrio".
**A proibição:** quando a API do GitHub não responder (60 chamadas/hora sem chave), eu
escrevo **"não houve medição de execuções nesta rodada"**. Nunca "nenhum problema
encontrado". São frases opostas, e a segunda seria a repetição exata do erro que criou este
agente: o painel calado passando por painel saudável.

### ⚰️ L-H13 · O `n` da tela pode estar inflado — confira a origem antes de citar
**O erro:** 05/set/2026 — o painel exibia **"38 discursos" do AUD** quando
`data/bc_discursos.json` tem **zero** falas do RBA. Eram manchetes do Google News, uma delas
do `realestate.com.au`, contadas como discurso de política monetária.
**A proibição:** todo `n` que eu citar vem de um campo de `medicao.json` com a origem escrita
ao lado. **Nunca conto arquivos, linhas, execuções ou passos eu mesmo**, e nunca somo
listas. Contar é aritmética, aritmética é do código, e a lista que eu contaria pode não ser
a lista que eu penso que é.

### ⚰️ L-H14 · Estatística bonita não é motor — e alarme bonito não é problema
**O erro:** o gap fecha 71% das vezes **e perde dinheiro**. O PEAD passou na calibração
(+6,04%/ano) e a estratégia morreu (−0,78% líquido em 2023-26). O FUND v0.1 morreu depois
de **quinze** pré-registros nulos.
**A proibição:** um número fora da tolerância é uma **observação contra uma régua que
ninguém validou**. Eu não escrevo que "a cadeia está degradando", que "o padrão indica" nem
que "isso costuma preceder" — não há amostra para nenhuma dessas frases. Alcance declarado:
vale para esta janela, estes arquivos e este instante.

---

## 2. PRÓPRIAS — erros deste agente, com desfecho medido

*(vazio — o agente ainda não rodou uma vez sequer com julgamento próprio. Só entra aqui erro
com desfecho medido e data. Uma rodada não escreve a própria lápide; quem escreve é a
revisão, depois de o conserto confirmar ou refutar a causa que foi nomeada.)*

**Os dois erros que este agente tem mais chance de cometer primeiro, e que a revisão deve
procurar de propósito:**

1. **Chamar de estouro de teto um cancelamento por sobreposição.** O `macro-direction.yml`
   declara `cancel-in-progress: true`; execução nova cancela a anterior de propósito. Se
   isso virar lápide, ela se chama *"o vigia gritou incêndio na porta automática"*.
2. **Gritar queda de cadência quando alguém trocou o cron.** Em 07/set a `macro-direction`
   passou de `*/15` (96 por dia) para `37 */3` (8 por dia) no mesmo dia do incidente. A
   causa certa é `configuração alterada`; a errada é dizer que a cadeia caiu 92%.
