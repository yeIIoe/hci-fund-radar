# LÁPIDES — agente `divergencia`

O que este agente **não pode repetir**. Lápide é erro comprovado, com número e data ao
lado. Refutação é ativo: a mesma sereia não canta duas vezes.

Este arquivo nasce com as lápides **herdadas da casa** — erros que a HCI já cometeu em
outros projetos e que este agente está em posição de cometer de novo. As lápides
**próprias** (com desfecho medido) entram abaixo, na seção 2, e só a revisão as escreve.

---

## 1. HERDADAS DA CASA — valem desde o primeiro disparo

### ⚰️ L-H1 · Percentil sem janela declarada não existe
**O erro:** 31/ago/2026 — o painel afirmou que o AUDCHF estava no percentil 98 e o GBPNZD
no 97. Com a janela corrigida (look-ahead removido), eram **85 e 61**. O aviso de "preço
esticado" no GBPNZD estava simplesmente errado. Dois dias depois o dono cometeu o gêmeo:
confundiu a máxima de **5 anos** do AUDCAD (0,99672) com a máxima histórica — o topo real
era 1,07738, de fev/2012, **8% acima**.
**A proibição:** nenhum percentil, extremo, "máxima", "mínima" ou "esticado" sai da minha
boca sem a **janela declarada grudada no número**. Se o arquivo da camada 1 não traz a
janela, o número não sai.

### ⚰️ L-H2 · Filtro que corta amostra não é seleção até passar no sorteio pareado
**O erro:** o filtro do dólar sobre as 88 operações de ouro (+81,26R, 67% de acerto)
reduziu o R total nas **seis** células testadas — a melhor custava **−32,95R** — e as duas
quase-significantes se contradiziam entre si. E o AEGH Teste 1: o FUND como filtro de
entrada deu **0 de 9 células** acima do p95 do sorteio pareado; o que parecia seleção era
**redução de exposição** (o CONCORDA tinha 1/3 das operações).
**A proibição:** eu **não** posso escrever que a divergência "seleciona" ou "melhora" nada.
Eu marco a diferença entre duas leituras. Qualquer frase que sugira desempenho exige
controle aleatório pareado com o mesmo n — que não existe.

### ⚰️ L-H3 · O "n" da tela pode estar inflado — confira a origem antes de citar
**O erro:** 05/set/2026 — o painel exibia **"38 discursos" do AUD** quando
`data/bc_discursos.json` tem **zero** falas do RBA. Eram manchetes do Google News (uma
delas do `realestate.com.au`) contadas como discurso de política monetária. O BoC tinha
*"Unveiling of Vertical $20 Bank Note"* entrando como fala.
**A proibição:** todo `n` que eu citar vem de um campo da camada 1 com a origem escrita ao
lado. Nunca conto itens eu mesmo, nunca somo listas, e nunca trato "quantidade de itens"
como "quantidade de evidência". Um número com cara de precisão sem fonte auditável é pior
do que nenhum número.

### ⚰️ L-H4 · Estatística bonita não é motor
**O erro:** o gap fecha 71% das vezes **e perde dinheiro**. O PEAD passou na calibração
(+6,04%/ano, dentro do esperado) e a estratégia morreu (−0,78% líquido em 2023-26). O FUND
v0.1 morreu depois de **quinze** pré-registros nulos: o juro manda no preço em 120 dias
(+0,43) e **não antecipa** nada em 1 a 20 dias.
**A proibição:** uma divergência grande e bonita continua sendo uma observação. Não escrevo
que ela "funciona", "tem edge", "antecipa" ou "vale operar". Alcance declarado: vale para
esta leitura, esta precificação e este instante.

### ⚰️ L-H5 · Artefato de relógio: fuso e defasagem antes de comparar
**O erro:** o "+0,107 em 1 dia" do FUND era **artefato de relógio** — o BCE fixa às 14:15
CET e o yield fechava depois; com 1 dia de gap o achado sumia. E as horas do dono são BRT
enquanto a Dukascopy é UTC (+3h).
**A proibição:** ao comparar a leitura da casa (`gerado_em` próprio) com a precificação
(`gerado_em` próprio) eu **declaro os dois carimbos** em `entradas.detalhe`. Se um deles é
anterior ao evento e o outro posterior, isso vai para `limites` — não para o veredito.

### ⚰️ L-H6 · Contagem de palavra não lê negação, condição nem tempo verbal
**O erro:** Waller disse que apoiaria **manter**, e o painel marcou **hawkish**, porque
"holding the target" estava na lista de termos de alta. Foi por isso que a dimensão de fala
parou de votar em 05/set e o teto por moeda caiu de 0,75 para 0,50.
**A proibição:** a coluna C entra como contexto e nunca move o veredito na v1. E eu nunca
classifico uma fala por conta própria: isso é tarefa do agente de fala, com prompt próprio
e validação própria.

### ⚰️ L-H7 · Silêncio não é voto
**O erro:** dimensão sem dado tratada como dimensão neutra — o buraco que faz "sem
informação" virar "equilíbrio". A régua da casa é explícita: a parte sem dado sai `null` e
**baixa o denominador**, nunca conta como zero.
**A proibição:** `sem_leitura` não vira `MANTEM`; `qualidade: "sem fonte"` não vira
`manutencao`; agente ausente não vira "a notícia concorda". Sai `SEM FONTE` ou
`nao_julgados`, com o motivo escrito.

---

## 2. PRÓPRIAS — erros deste agente, com desfecho medido

*(vazio — o agente ainda não rodou. Só entra aqui erro com desfecho medido e data. Uma
rodada não escreve a própria lápide; quem escreve é a revisão, depois da decisão do banco
central.)*
