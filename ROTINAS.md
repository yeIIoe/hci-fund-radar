# ROTINAS — o manual da camada 2 na nuvem

*Como ligar, acompanhar, pausar e expandir o time de agentes do HCI MACRO DIRECTION.*

```
escrito_em   2026-09-07
prompt       agentes/ROTINA_PROMPT.md  (rotina@v1)
repositorio  https://github.com/yeIIoe/hci-fund-radar  (branch main)
```

---

## 1. O QUE É A ROTINA, EM UMA FRASE

Uma **sessão de IA que acorda sozinha de tempos em tempos**, clona o repositório, lê o prompt e
a memória dos agentes, julga o que a camada 1 já mediu, grava o julgamento em
`data/agentes/` e dá push. O site lê esse JSON. Só isso.

Ela **não coleta dado, não calcula número e não decide operação.** A coleta continua onde está
(GitHub Actions e a VPS). O cálculo continua em Python. A rotina só faz o que código não faz
bem: **ler texto e julgar.**

### A linha dura, de novo, porque é o que sustenta o resto

> **Número medido é código. Julgamento é IA.**

O agente recebe os números prontos e cita de qual campo copiou. Ele nunca recalcula. Se
recalculasse, o número de hoje deixaria de ser reproduzível daqui a três meses — e aí morrem o
backtest e a refutação, que é o diferencial declarado da casa.

---

## 2. O QUE ELA FAZ A CADA DISPARO

1. Lê `agentes/ROTINA_PROMPT.md` (o prompt inteiro, autossuficiente — a sessão acorda com zero
   contexto).
2. Roda o **vigia** primeiro — literalmente `python vigia.py` (4 s, sem dependências), e só
   depois julga a medição dele. Sem esse comando o vigia enxerga só a idade dos arquivos, e o
   incidente de 07/set (4 execuções `cancelled`, passos pulados, nenhum e-mail) **não aparece
   em idade nenhuma**: era exatamente o modo silencioso.
3. Roda os agentes de leitura na ordem: **notícia → fala → geopolítica → divergência**.
4. Roda o **advogado do diabo** por último, que lê a saída de todos e tenta derrubar.
5. Grava `ultimo.json` + uma linha em `historico.jsonl` de cada agente, atualiza
   `data/agentes/indice.json`.
6. `git add data/agentes` → commit em português → `pull --rebase --autostash` → push.
7. Escreve no log da rotina o que rodou, o que não rodou e por quê.

**Prazo: 20 minutos.** Passou disso, publica o que tem e sai. Agente que não rodou fica com a
linha da rodada anterior intacta — nunca com estado falso.

**Hoje nenhum agente vota.** Todos saem com `"vota": false` e o selo *"experimental — contexto,
não vota"*. Eles informam a tela; não movem medidor nenhum. Vale a lei: *dimensão não validada
NÃO VOTA, só informa.*

---

## 3. A PROPOSTA DE PARTIDA — uma rotina só, de 2 em 2 horas, com dois agentes

**Fase 1: `vigia` + `noticia`, de 2 em 2 horas.** É por aí que se começa, e não pela cadeia
inteira, por quatro motivos:

| Motivo | Detalhe |
|---|---|
| O vigia é o mais barato e o mais útil | ele responde "os dados estão vivos?", que é a pergunta que precede todas as outras |
| A notícia é a de maior giro | `noticias.json` é reescrito pela cadeia rápida a cada ~15-35 min; julgar de 2 em 2 h acompanha sem desperdiçar |
| Duas horas dão 12 disparos/dia | o suficiente para ver o comportamento da rotina em um dia só, e barato para errar |
| Cadeia curta erra menos | com dois agentes, quando algo quebra dá para saber onde |

Fala, geopolítica, divergência e advogado ficam **de fora no começo** — os prompts deles já
existem, mas entram depois, um de cada vez (seção 8).

O intervalo mínimo permitido pela plataforma é **1 hora**. Duas horas é escolha, não limite:
dá folga para a cadeia rápida terminar e para o custo ficar visível antes de crescer.

---

## 4. QUANTO CUSTA — ordem de grandeza

**Uma sessão de agente por disparo.** Não há custo de servidor, não há assinatura: o custo é o
da própria sessão.

Ordem de grandeza por disparo, na fase 1 (dois agentes):

- **entrada:** dezenas de milhares de tokens — os prompts dos agentes são longos de propósito
  (a régua inteira vai junto), mais o `noticias.json` e o `frescor.json`;
- **saída:** poucos milhares de tokens — dois JSON pequenos e a resposta final;
- **12 disparos por dia** (de 2 em 2 h).

Traduzindo em grandeza, não em precisão: **isso é ordem de dólares por dia, não de centavos e
não de centenas.** O número real só aparece medindo — confira o consumo depois do primeiro dia
inteiro, antes de aumentar frequência ou plugar mais agentes.

**O custo cresce quase linear com o número de agentes**, porque cada um lê o próprio prompt e as
próprias entradas. Rodar os seis de 2 em 2 horas custa da ordem de **três vezes** a fase 1. É
por isso que a expansão é por fase, e que o advogado (o mais caro, porque lê a saída de todos)
pode acabar rodando **1x por dia** em vez de a cada disparo.

Comparação útil: a camada 1 (GitHub Actions em repositório público) custa **zero**. Ela roda
2x/dia na cadeia pesada e a cada 15 min na rápida, e continua assim. A rotina não substitui
nada disso.

---

## 5. COMO VER O QUE ELA FEZ

### No repositório (a fonte da verdade)

```bash
git log --oneline -20 -- data/agentes          # o histórico de rodadas publicadas
cat data/agentes/indice.json                   # quem rodou, quando, em que estado
cat data/agentes/noticia/ultimo.json           # o julgamento mais recente
tail -3 data/agentes/noticia/historico.jsonl   # as três últimas rodadas
cat data/agentes/rotina.json                   # o log operacional da última rodada
```

O que olhar em `indice.json`:

| `estado` | O que significa | O que fazer |
|---|---|---|
| `ok` | julgou | nada |
| `sem dados` | a entrada estava vazia, ausente ou velha demais | olhar `data/frescor.json` — é a **camada 1** que está parada, não o agente |
| `falhou` | o agente não conseguiu produzir a saída | ler o log da rotina; o `ultimo.json` anterior **não** foi sobrescrito |

### No log da rotina

Cada disparo deixa uma resposta final curta: quais agentes rodaram, com quantos julgamentos,
qual a idade das entradas, se publicou (com o hash) ou qual foi o erro de push.

### No site

O painel lê `data/agentes/indice.json` primeiro e mostra cada sala com o **último resultado e a
idade dele**. Se um agente falhou, a tela mostra o julgamento antigo com o carimbo antigo —
nunca esconde e nunca inventa. É a mesma lei do frescor que já vale no macro.

---

## 6. COMO PAUSAR

Pausar ou apagar a rotina na lista de rotinas da Anthropic. **Nada quebra:**

- a camada 1 continua rodando (Actions + VPS), os dados continuam frescos;
- o site continua lendo o último `ultimo.json` de cada agente, com a idade à mostra;
- nenhum medidor muda, porque **nenhum agente vota**.

Pausar é a resposta certa quando: o custo surpreendeu, um agente começou a escrever bobagem, a
cadeia de coleta quebrou e vai ficar dias parada, ou você mudou um `PROMPT.md` e quer revisar
antes de deixar rodar sozinho.

Para pausar **um agente só**, sem mexer na rotina: tire o nome dele da lista de agentes do
disparo. A linha dele no índice congela com a última rodada, que é o comportamento correto.

---

## 7. A REGRA DE CAMINHOS SEPARADOS — a mais importante deste documento

**Três máquinas escrevem neste repositório.** Elas não se atropelam porque cada uma tem o seu
caminho:

| Quem escreve | Onde escreve | Quando |
|---|---|---|
| **GitHub Actions** — cadeia pesada (`cadeia.yml`) | `data/` (yields, FUND, calendários, COT, BIS) | 2x/dia, 04:35 e 08:35 BRT |
| **GitHub Actions** — cadeia rápida (`macro_direction.yml`) | `data/` (calendário, BLS, bancos centrais, eventos) | a cada 15 min (na prática 15-35) |
| **VPS** (quando ligada) | `data/` (a faixa rápida dos eventos) | contínuo |
| **A ROTINA (camada 2)** | **`data/agentes/` — e só** | a cada 2 h |

> ⚠️ **A rotina NUNCA toca nos JSON dos coletores.** Nem para corrigir, nem para completar, nem
> para reformatar.

Não é preciosismo: a cadeia dá push várias vezes por dia. Se um agente escrevesse em
`data/noticias.json`, o push da cadeia entraria em conflito, falharia, e **o painel pararia de
atualizar** — o pior desfecho possível, porque falha silenciosa de dado é exatamente o que a
guarda de frescor foi criada para impedir (31/ago: uma semana de fontes congeladas sem ninguém
reclamar).

⚠️ **Medido em 07/09 e a corrigir: a separação não é simétrica.** `macro_direction.yml`,
`nowcast.yml` e a VPS fazem `git add` por **lista explícita** e nunca tocam em `data/agentes/`.
Mas `cadeia.yml`, `macro.yml`, `equities.yml` e `sentinela.yml` fazem **`git add -A data`**, que
varre a pasta inteira — inclusive `data/agentes/`. Eles não rodam agentes, então não corrompem
conteúdo, mas podem commitar o julgamento da rotina sob a assinatura do coletor e abrem janela
de conflito no `historico.jsonl`. **Conserto pendente (uma linha em cada um dos quatro):**

```yaml
git add -A data ':(exclude)data/agentes'
```

Se um dado da camada 1 estiver errado, o agente **escreve o erro em `limites`** e alguém
conserta no código. Agente não conserta dado.

A memória dos agentes (`agentes/<nome>/casos/`, `MEMORIA.md`, `LAPIDES.md`) fica fora de `data/`
e nenhum automatismo escreve nela — por isso a rotina pode gravar ali sem risco de conflito. O
`PROMPT.md`, esse, **só muda por mão humana**.

---

## 8. O ROTEIRO DE EXPANSÃO

| Fase | Quem roda | Frequência | Só avança quando |
|---|---|---|---|
| **1** | `vigia` + `noticia` | 2 h | 3 dias seguidos publicando sem falha de push, custo medido e aceito, e os julgamentos lidos por você e considerados sãos |
| **2** | + `fala` + `geopolitica` | 2 h | os três de leitura concordam com o que você leria; nenhum inventou número |
| **3** | + `divergencia` | 2 h | a divergência marcada bate com a que você vê olhando o painel |
| **4** | + `advogado` | 1x/dia (é o mais caro) | as objeções dele têm conteúdo — se ele só repete "confiança baixa", o prompt sobe de versão antes de virar rotina |

**O critério para promover uma dimensão a VOTO é outro, e é muito mais duro** — não é a rotina
rodar bem. É o que está escrito no `PROMPT.md` de cada agente: comparar o veredito com a
**decisão seguinte do próprio banco**, ponto-no-tempo, em amostra declarada antes de rodar
(n ≥ 200, ≥ 5 bancos, ≥ 3 anos, ≥ 30 em cada classe), tendo de **ganhar da referência burra
"sempre manutenção"**, com a regra congelada antes da janela de fora da amostra. A amostra
existe: `data/bis_discursos_historico.jsonl`, 1.319 falas de 2009 a 2026.

Até lá: **contexto, não voto.**

---

## 9. QUANDO DER PROBLEMA

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `indice.json` com `sem dados` em vários agentes | a camada 1 parou | abrir `data/frescor.json`, olhar `fora_da_tolerancia`; o problema é Actions/VPS, não a rotina |
| O push da rotina falha sempre | a sessão não tem credencial de escrita no repositório | testar com um disparo manual; sem push, o julgamento morre com a sessão |
| Conflito de git em `data/agentes/` | duas rodadas se cruzaram | o prompt manda **manter as duas versões** no `historico.jsonl` e abortar se não resolver de primeira |
| Um agente sempre com confiança `baixa` | pode estar certo (manchete é degrau 0,0) ou o prompt está frouxo | ler os `casos/`; se for o prompt, subir para `@v2` |
| Julgamento com número que não existe em `data/` | violação da linha dura | vira **lápide** em `agentes/<nome>/LAPIDES.md`, com data e número |
| A rodada estoura os 20 min | cadeia longa demais para o prazo | reduzir a lista de agentes do disparo, ou separar em duas rotinas |

**Quando um agente erra, isso não se apaga.** Vai para `LAPIDES.md` com o número e a data, e o
agente lê as lápides **antes** de julgar na rodada seguinte. É esse ciclo — julgar → gravar com
a versão do prompt → medir o desfecho semanas depois → devolver o caso para a memória — que faz
o time melhorar de um jeito auditável, coisa que fine-tuning não é.

---

## 10. CHECKLIST PARA LIGAR A FASE 1

- [ ] **`git status` limpo: `vigia.py`, `verificador_numeros.py`, `agentes/`, `data/agentes/` e
      `ROTINAS.md` COMMITADOS E EMPURRADOS.** Em 07/09 os cinco estavam apenas como arquivos
      locais não rastreados — e a rotina roda sobre um **clone limpo**: o que não está no
      `origin/main` não existe para ela. Sem isso a rotina falha na primeira linha, ao tentar
      ler `agentes/ROTINA_PROMPT.md`.
- [ ] `agentes/vigia/PROMPT.md` existe e está commitado (se ainda não existir, a rotina o pula e
      avisa — mas aí a fase 1 vira só o `noticia`, e a leitura de frescor fica de fora).
- [ ] `vigia.py` roda no clone: `python vigia.py --so-tela` (4 s, sem dependências).
- [ ] `verificador_numeros.py` roda: `python verificador_numeros.py`.
- [ ] `agentes/noticia/PROMPT.md`, `MEMORIA.md`, `LAPIDES.md` commitados.
- [ ] `agentes/ROTINA_PROMPT.md` commitado — é ele que a rotina lê.
- [ ] Criar a rotina apontando para `agentes/ROTINA_PROMPT.md`, com a lista de agentes
      `vigia, noticia` e intervalo de 2 horas.
- [ ] **Primeiro disparo manual**, acompanhado: confirmar que ela clona, julga, commita e
      **empurra**. O push é o ponto que só se prova na prática.
- [ ] Depois do primeiro dia inteiro: olhar o custo real e os 12 julgamentos publicados antes de
      plugar a fase 2.

---

*Documento operacional. Nada aqui é recomendação de investimento — o painel publica cenário
condicional, e o dono publica como pessoa física sem registro na CVM.*
