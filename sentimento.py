# -*- coding: utf-8 -*-
"""SENTIMENTO — a leitura PARA FRENTE, por moeda e por par.

A PERGUNTA QUE ISTO RESPONDE
    "O que este banco central vai fazer na PROXIMA reuniao?" — e, com as duas pernas lidas,
    "este par tem tese fundamental ou nao?". E leitor, nao estrategia: ele da o lado
    fundamental de cada perna; a entrada continua sendo do Eduardo.

TRES COISAS QUE ANTES ERAM UMA SO (revisao do dono, 05/set/2026)
    DIVERGENCIA        0 a 100. E a diferenca economica entre as duas pernas, medida contra o
                       teto ligado do par. E o antigo "conviccao_pct" — o campo antigo continua
                       gravado por compatibilidade, mas o nome certo e divergencia.
    QUALIDADE DA       0 a 100, por moeda, quatro partes de 25: quantidade (divulgacoes e falas
    EVIDENCIA          na janela), diversidade (familias independentes), atualidade (idade do
                       item que mais pesa, com a mesma meia-vida dos dados) e confiabilidade
                       (peso da fonte de fala). No par vale a MENOR das duas pernas: o elo
                       fraco manda.
    CONVICCAO          quanto isto acertou no passado. HOJE E NULL, sempre, com a nota
    HISTORICA          "ainda nao calibrada — precisa de backtest com amostra declarada".
                       NUNCA se deriva conviccao da divergencia: sao perguntas diferentes.

ZONA NEUTRA REAL (faixas PROVISORIAS do dono, 05/set — para calibrar depois no backtest)
    0-14 sem_tese · 15-24 observacao · 25-39 moderada · 40+ forte.
    Antes so havia SEM_TESE no empate exato, e por isso ZERO de 28 pares ficava sem tese
    enquanto pares com divergencia 2 ou 3 saiam com direcao. Agora o par em sem_tese sai da
    lista principal, mas NAO some do arquivo: mantem divergencia e as duas pernas gravadas.

DUAS DIMENSOES QUE VOTAM, 25% CADA — TETO 0,50 POR MOEDA. NENHUMA USA YIELD.
    dados    ✅ VOTA
             surpresas acumuladas desde a ultima decisao do banco (ou 42 dias), cada evento
             pesado pela familia (leitor_regras), pelo impacto e por uma meia-vida de 21
             dias. Um empurrao de 30 dias atras vale ~37% de um de hoje. Desde 08/set a
             soma e CRUA: nenhum item e cortado, e a concentracao de uma divulgacao so vira
             BANDEIRA e teto na qualidade da evidencia, nunca mudanca de direcao. Moeda
             com ZERO divulgacao na janela nao vota nesta dimensao (silencio nao e voto): a
             direcao continua exibida, mas com "vota": false, e o teto da moeda cai.
    ciclo    ✅ VOTA
             a direcao do ultimo movimento de juro, com DECAIMENTO CONTINUO (05/set): pesa
             menos com o tempo. Antes era um penhasco em 180 dias — 179 dias valia 0,25
             cheio e 181 valia zero.
    texto    ⛔ NAO VOTA MAIS — decisao do dono de 05/set (tarde), prioridade 3 da revisao
             o que os dirigentes DISSERAM, com a ORIGEM declarada: discurso_oficial,
             comunicado_ata, imprensa_com_fala, manchete ou sem_fonte.
    geo      ⛔ NAO VOTA — decisao de 05/set (manha)
             intensidade de noticia do GDELT, experimental.

A DIMENSAO DE FALA PAROU DE VOTAR — 05/set/2026, PARA AS OITO MOEDAS
    MOTIVO ESCRITO PELO DONO: contagem de palavras nao le NEGACAO, nem CONDICAO, nem
    REFERENCIA TEMPORAL. Os tres casos que ele mediu na tela, todos do Fed:
        Waller  disse "I would be inclined to support HOLDING the target ... at its current
                setting" e a regua marcou HAWKISH — porque "holding the target" esta na
                lista de termos hawkish do bc_discursos.py. Defender MANTER virou alta.
        Barr    e hawkish, mas CONDICIONAL: "IF inflation appears not to be moderating
                sufficiently, then ... raise rates". A contagem nao ve o "if".
        Warsh   fala em preservar a liberdade de decidir — nao e alta nem corte. A contagem
                achou 3 marcadores hawkish assim mesmo.
    ATE 05/set: JPY, AUD, NZD e CHF ja saiam com peso 0,0 (manchete), mas USD, EUR, GBP e
    CAD votavam com peso 1,0 por CONTAGEM DE PALAVRAS. Agora nenhuma vota.
    A dimensao continua CALCULADA e EXIBIDA, com "vota": false e o selo
    "experimental — contexto, nao vota", exatamente igual a geopolitica, e ganha o
    VEREDITO POR ORADOR (manutencao / alta / corte / alta condicional / corte condicional /
    indeterminado), que le negacao, condicao e tempo verbal — e que TAMBEM nao vota, porque
    tambem nao foi validado.

    CONSEQUENCIA ASSUMIDA, EM NUMEROS (o teto encolheu um terco):
        teto por moeda   0,75 -> 0,50      teto do par      1,50 -> 1,00
        conviccao teto    75% ->  50%      dimensoes que votam   3 -> 2
    A DIVERGENCIA DOS PARES MUDA DE ESCALA: o denominador cai de 1,50 para 1,00, entao a
    mesma diferenca economica sai 50% MAIOR em pontos de divergencia — ao mesmo tempo que os
    leitura continua de cada perna encolhe, porque a parcela de fala saiu do numerador. Os
    dois efeitos andam em sentidos contrarios e nao se cancelam por construcao: as faixas
    provisorias (0-14 / 15-24 / 25-39 / 40+) FORAM CALIBRADAS NA ESCALA VELHA e ficam
    desalinhadas ate o backtest.

    DISTRIBUICAO DAS FAIXAS, ANTES E DEPOIS — medida nos 28 pares, mesmo calendario:
        04/set (3 dimensoes votando, teto do par 1,50)   sem tese 12 · observacao 7 ·
                                                         moderada 8 · forte 1
        06/set (2 dimensoes votando, teto do par 1,00)   sem tese 13 · observacao 5 ·
                                                         moderada 9 · forte 1
    Um par saiu de observacao para sem tese e outro de observacao para moderada. O
    deslocamento pequeno e COINCIDENCIA DESTE DIA, nao prova de que a escala ficou igual:
    os dois efeitos contrarios quase se cancelaram neste calendario. Em um dia com fala
    puxando forte para um lado, eles nao se cancelam.
    Isto esta dito aqui, na regua (regua.mudanca_de_escala_05set.
    distribuicao_das_faixas_antes_e_depois) e no relatorio impresso.

    ⚠️ A dimensao "mercado (probabilidade implicita)" saiu: ela dependeria de OIS/futuros de
    juro, e yield nao entra por decisao do Eduardo (repetida em 04/set).

ZONA "SEM LEITURA" POR MOEDA (regra PROVISORIA do dono, 05/set)
    O caso dele: "EUR +0,17 com apenas 2 de 4 dimensoes". Um numero pequeno vindo de pouca
    dimensao virava direcao na tela. Agora a moeda fica em SEM_LEITURA quando
        intensidade relativa = |score| / teto TEORICO (0,50) x 100  for MENOR que 15
        OU quando MENOS DE 2 dimensoes votarem.
    A moeda em sem_leitura NAO some do arquivo: sai com leitura "sem_leitura",
    leitura_texto "sem leitura" e leitura_motivo dizendo por que.

O QUE A MOEDA PASSA A GRAVAR PARA A TELA (no lugar do score, que nao aparece mais)
    regime                     alta | manutencao | corte — o que o banco ESTA fazendo
    leitura / leitura_texto    inclinado a alta | inclinado ao corte | sem leitura
    concordancia_texto         "1 de 2 dimensoes concordam"
    evidencia_rotulo           fraca <40 · moderada 40-69 · forte >=70 (faixas provisorias)
    proximo_evento_relevante   o proximo dado de impacto alto que ainda nao saiu (CPI,
                               emprego, salarios, PIB, varejo, PMI). E DIFERENTE da proxima
                               DECISAO: o evento relevante diz ate quando vale procurar
                               BO + ZOI; a decisao e o limite final do ciclo.

FRESCOR NA RAIZ (prioridade 2 do dono)
    raiz.frescor traz o atraso em minutos do dado MAIS VELHO que alimenta a leitura, o
    estado (ok / atrasado / muito_atrasado, limiares provisorios de 45 e 120 minutos), a
    hora da ULTIMA SINCRONIZACAO BEM-SUCEDIDA (nao a idade generica), bloqueia_leitura
    quando muito atrasado e o texto em portugues para a tela.

GEOPOLITICA NAO VOTA MAIS — decisao de 05/set/2026, que SUBSTITUI a de 04/set/2026
    Em 04/set o dono decidiu que o noticiario contaria ("quero que utilize as noticias") e a
    geopolitica virou a 4a dimensao, com voto e com 0,25 no teto. Em 05/set essa decisao foi
    revista: a regra foi DECLARADA e nunca MEDIDA — nao ha teste dizendo que um pico de
    conflito ou de energia muda o juro esperado — e ela estava mexendo em leitura de verdade
    (o NZD saia com 0,73 de score e teto 1,00 por causa de um z de energia de 1,85).
    Agora a dimensao leva o selo "experimental", sai com "vota": false, NAO entra no score e
    NAO entra no teto. O conteudo continua calculado e gravado para EXIBICAO. Na tarde de
    05/set a dimensao de FALA recebeu o mesmo tratamento, e por isso o teto maximo por moeda
    e hoje 0,50 (duas dimensoes) e o do par, 1,00.

    Direcao da moeda = a mais votada entre as dimensoes QUE VOTAM; empate = MANTEM.
    Buraco nao vira zero: dimensao sem dado nao conta, ela BAIXA O TETO.

A LEI DAS DUAS PERNAS
    Par nao e ativo, sao duas moedas. Cada par sai com a perna dominante (share do |score| de
    cada lado) e com a lista de pares que compartilham essa perna — dois deles nao
    diversificam, dobram.

LEI ESTRUTURAL DE 08/set/2026 — NENHUM TRATAMENTO VIRA A DIRECAO EM SILENCIO
    O DEFEITO QUE A ORIGINOU: a winsorizacao por item, criada em 05/set para atender um pedido
    legitimo do dono ("uma unica divulgacao nao pode carregar a leitura"), estava no LUGAR
    ERRADO — peso relativo e problema de PARTICIPACAO e ela mexia nos TERMOS DA SOMA. Medido
    em 08/set, na propria rodada: USD soma -1,19 -> -8,29 (MANTEM -> CORTA) e GBP -4,66 ->
    -5,77 (MANTEM -> CORTA). Os tres maiores itens do dolar eram ALTISTAS (ISM Services PMI,
    Average Hourly Earnings, Nonfarm Payrolls) e so eles foram cortados; os baixistas eram
    menores e passaram inteiros. O corte tirou peso de UM LADO SO. O painel lia "USD inclinado
    ao corte" enquanto os futuros de fed funds pagavam p_alta 0,5786 para o FOMC de 16/set.

    A REGRA, PARA A FAMILIA INTEIRA DO ERRO: qualquer transformacao entre o dado cru e a
    leitura publicada e comparada com o cru. Se a direcao mudar, o campo sai com BANDEIRA e
    texto, e a moeda vai para SEM LEITURA ate alguem decidir — leitura cuja direcao depende do
    tratamento nao e leitura, e escolha de metodo, e escolha de metodo e do dono.

    GRAVADO SEMPRE, em toda moeda, para auditoria: soma_crua, soma_tratada,
    participacao_maior_item_antes, participacao_maior_item_depois,
    direcao_mudou_pelo_tratamento e bandeira_de_direcao. Hoje o tratamento e "nenhum": as duas
    somas sao iguais, o deslocamento e 0,00 e a bandeira e false nas oito moedas — e isso pode
    ser CONFERIDO no arquivo, nao precisa ser acreditado.

REGUAS DECLARADAS (grossas de proposito — fino sem calibracao e falsa precisao)
    LIMIAR_DADOS = 5,0 na soma decaida: abaixo disso o fluxo de dados le MANTEM.
    Uma DECISAO dentro da janela zera o acumulado: so contam eventos depois dela.
    A SOMA E A SOMA (08/set): nenhum termo e cortado. A winsorizacao por item foi REVOGADA
    porque cortar termos de uma soma desloca o TOTAL para o lado dos itens que sobram — ela
    virou a direcao do USD e do GBP de MANTEM para CORTA. Concentracao passou a ser lida na
    CONFIANCA: acima de 50% de participacao do maior item a moeda leva bandeira e a qualidade
    da evidencia fica limitada a (100 - participacao). E NENHUM tratamento pode virar a
    direcao em silencio (guarda_de_direcao).
    TODO limiar novo desta revisao esta marcado "provisorio": true, para o backtest calibrar.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import math
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from leitor_regras import MODULADORES                                    # noqa: E402
from macro_eventos import (familia_de, classifica, empurrao, corte_da_surpresa,  # noqa: E402
                           IMPACTO_FXS)
from fxstreet_calendario import buscar, normaliza                        # noqa: E402
from leitor_pares import PARES, MOEDAS, Leitura, le_par                   # noqa: E402

SAIDA = os.path.join(AQUI, "data", "sentimento.json")
SNAPSHOTS = os.path.join(AQUI, "data", "snapshots")
BANCOS = os.path.join(AQUI, "data", "bancos_centrais.json")
DISCURSOS = os.path.join(AQUI, "data", "bc_discursos.json")      # todas as moedas conectadas
DISCURSOS_FED = os.path.join(AQUI, "data", "fed_discursos.json")  # reserva, so o Fed
GEO = os.path.join(AQUI, "data", "geopolitica.json")
NOTICIAS = os.path.join(AQUI, "data", "noticias.json")            # manchetes: reserva de "texto"
SEM_FEED_PROPRIO = ("AUD", "NZD", "CHF")                          # RBA/RBNZ 403, SNB sem feed

GEO_Z_CORTE = 1.5                      # pico = 3 dias acima da media de 14 dias em >= 1,5 desvios
EXPORTADOR_ENERGIA = ("CAD",)
CAL_LOCAL = os.path.join(AQUI, "data", "calendario_resultado.json")

JANELA_DIAS = 42
HORIZONTE_FRENTE_DIAS = 30        # so para achar o PROXIMO EVENTO RELEVANTE, nunca para votar
MEIA_VIDA = float(MODULADORES.get("meia_vida_dias", 21))
LIMIAR_DADOS = 5.0
PESO_DIM = 25

# QUEM VOTA. A fala saiu em 05/set (tarde) e a geopolitica em 05/set (manha) — as duas ficam
# calculadas e exibidas com selo, fora do score e fora do teto.
DIMENSOES_QUE_VOTAM = ("dados", "ciclo")
TETO_MOEDA = round(PESO_DIM / 100.0 * len(DIMENSOES_QUE_VOTAM), 2)   # 0,50
TETO_PAR = round(2 * TETO_MOEDA, 2)                                   # 1,00
SELO_NAO_VOTA = "experimental — contexto, não vota"

# ---------------------------------------------------------------------------------------
# REGUAS NOVAS DA REVISAO DE 05/set/2026 — TODAS PROVISORIAS
# ---------------------------------------------------------------------------------------
FAIXAS_PROVISORIAS = {"sem_tese": [0, 14], "observacao": [15, 24],
                      "moderada": [25, 39], "forte": [40, 100]}

# (B) ZONA "SEM LEITURA" POR MOEDA — regra provisoria do dono (05/set).
FAIXAS_LEITURA_PROVISORIAS = {
    "intensidade_minima_pct": 15,
    "dimensoes_minimas_votando": 2,
    "denominador": "teto TEORICO da moeda (%.2f = 0,25 x %d dimensoes que votam)"
                   % (TETO_MOEDA, len(DIMENSOES_QUE_VOTAM)),
    "texto": "a moeda fica SEM LEITURA quando a intensidade relativa (|leitura contínua| "
             "dividida pelo teto teórico, em %%) for menor que 15, OU quando menos de 2 "
             "dimensões votarem. Números PROVISÓRIOS do dono (05/set), a calibrar no "
             "backtest. O caso que originou a regra: 'EUR +0,17 com apenas 2 de 4 "
             "dimensões' — número pequeno vindo de pouca dimensão virava direção na tela.",
    "provisorio": True,
    "por_que_o_teto_teorico": "dividir pelo teto LIGADO faria a FALTA de dado INFLAR a "
                              "intensidade — o mesmo vício já corrigido na divergência dos "
                              "pares. Com o teto teórico, menos evidência dá intensidade "
                              "MENOR, que é o sentido honesto.",
}

# (C) rotulo provisorio da QUALIDADE DA EVIDENCIA, para a tela mostrar palavra e nao numero.
FAIXAS_EVIDENCIA_PROVISORIAS = {"fraca": [0, 39], "moderada": [40, 69], "forte": [70, 100]}

# A CONSEQUENCIA MEDIDA da saida da fala do voto, nos 28 pares. Nao e estimativa: sao duas
# rodadas do MESMO calendario, a de 04/set (tres dimensoes votando, teto do par 1,50) e a
# rodada de AGORA (duas dimensoes, teto 1,00), com as MESMAS faixas provisorias aplicadas.
#
# ⚠️ 06/set: o bloco "depois" era ESCRITO A MAO e ficou defasado em horas — dizia
# "moderada 9 · forte 1" enquanto a mesma execucao imprimia "moderada 8 · forte 2" (o RBNZ
# subiu a taxa em 02/set e o par NZDUSD trocou de faixa). Numero congelado dentro de um
# arquivo que se recalcula sozinho vira mentira no primeiro dia em que o dado anda. Agora
# so o "antes" e constante (e um valor historico, medido uma vez e nunca mais reproduzivel);
# o "depois" e CONTADO na propria rodada por distribuicao_depois().
DISTRIBUICAO_FAIXAS_ANTES = {
    "quando": "2026-09-04", "dimensoes_que_votavam": 3, "teto_do_par": 1.50,
    "sem_tese": 12, "observacao": 7, "moderada": 8, "forte": 1,
    "nota": "medido uma vez, na rodada de 04/set, antes de a fala sair do voto. É histórico: "
            "não pode ser recalculado hoje porque o calendário da FXStreet é buscado ao vivo.",
}

# O SEGUNDO ANTES/DEPOIS, e ele e mais importante que o primeiro: o conserto da REGUA DA
# SURPRESA (corte absoluto por familia), medido no MESMO calendario, na MESMA hora, com as
# MESMAS faixas. So mudou a regua que decide se a divulgacao empurra ou nao.
DISTRIBUICAO_ANTES_DA_REGUA = {
    "quando": "2026-09-06, mesma janela, régua relativa antiga (35% do nível)",
    "em_linha_pct": 76,
    "sem_tese": 13, "observacao": 5, "moderada": 8, "forte": 2,
    "leitura_por_moeda": {"USD": -0.20, "EUR": +0.23, "GBP": -0.07, "JPY": +0.03,
                          "AUD": +0.15, "NZD": +0.24, "CAD": -0.10, "CHF": +0.17},
    "nota": "com a régua relativa, 278 das 364 divulgações (76%) empurravam zero. Com o corte "
            "absoluto por família são 189 de 364 (51%). O painel ficou MAIS SENSÍVEL porque "
            "passou a ouvir dado que antes era apagado — e por isso a faixa 'forte' encheu: "
            "as faixas 0-14/15-24/25-39/40+ foram desenhadas para a escala em que três quartos "
            "das divulgações eram mudas. ⚠️ Elas estão desalinhadas e SÓ o backtest recalibra. "
            "Enquanto isso, leia a ORDEM dos pares, não a palavra da faixa.",
}

# O TERCEIRO ANTES/DEPOIS, e este é o do conserto de 08/set: a winsorização saiu da soma.
# Medido no MESMO calendário, no MESMO instante (08/set 14:18 UTC, 1.877 eventos em cache) e
# com as MESMAS faixas — a única coisa que mudou foi o tratamento da soma.
DISTRIBUICAO_ANTES_DO_CONSERTO_DA_SOMA = {
    "quando": "2026-09-08 14:18 UTC, mesma janela e mesmo instante, com winsorização por item",
    "sem_tese": 11, "observacao": 2, "moderada": 6, "forte": 9,
    "leitura_por_moeda": {"USD": "inclinado ao corte", "EUR": "inclinado à alta",
                          "GBP": "inclinado ao corte", "JPY": "inclinado à alta",
                          "AUD": "inclinado à alta", "NZD": "inclinado à alta",
                          "CAD": "sem leitura", "CHF": "inclinado à alta"},
    "duas_direcoes_viradas_pelo_teto": {
        "USD": "soma -1,19 -> -8,29; MANTÉM -> CORTA. Os TRÊS maiores itens eram altistas e "
               "de impacto alto (ISM Services PMI +4,25, Average Hourly Earnings +7,90, "
               "Nonfarm Payrolls +7,02) e só eles foram cortados para 4,00; os baixistas "
               "(-3,98 e -3,82) passaram inteiros. O corte tirou peso de um lado só.",
        "GBP": "soma -4,66 -> -5,77; MANTÉM -> CORTA."},
    "nota": "o efeito no CAD ia no sentido CONTRÁRIO e também era distorção: a winsorização "
            "puxava a soma de -4,80 para -1,81, a intensidade caía para 9% e a moeda sumia em "
            "'sem leitura'. Ou seja, o mesmo tratamento fabricava direção numa moeda e apagava "
            "direção noutra, conforme o lado em que estivessem os itens grandes.",
}

AVISO_DISTRIBUICAO = (
    "medido nos 28 pares, com as MESMAS faixas provisórias dos dois lados. O deslocamento "
    "pequeno é coincidência do dia: o denominador caiu de 1,50 para 1,00 (empurra a "
    "divergência para cima) e a parcela de fala saiu do numerador (empurra para baixo), e "
    "neste calendário os dois quase se cancelaram. Não trate isso como prova de que a escala "
    "é a mesma — ela não é, e as faixas foram desenhadas na escala velha. O lado 'antes' é um "
    "valor histórico congelado; o lado 'depois' é contado na própria rodada."
)


def distribuicao_depois(conta, hoje_iso):
    """Conta as faixas DESTA rodada e escreve a comparação com o 'antes' histórico.

    Recebe o Counter dos estados dos 28 pares. Nada aqui é escrito à mão: se um par trocar de
    faixa entre duas execuções, o texto muda junto — foi exatamente o que faltou em 06/set.
    """
    a = DISTRIBUICAO_FAIXAS_ANTES
    d = {"quando": hoje_iso, "dimensoes_que_votam": len(DIMENSOES_QUE_VOTAM),
         "teto_do_par": TETO_PAR}
    for k in ("sem_tese", "observacao", "moderada", "forte"):
        d[k] = int(conta.get(k, 0))
    mudou = " · ".join("%s %d -> %d" % (rot, a[k], d[k]) for k, rot in (
        ("sem_tese", "sem tese"), ("observacao", "observação"),
        ("moderada", "moderada"), ("forte", "forte")))
    r = DISTRIBUICAO_ANTES_DA_REGUA
    mudou_regua = " · ".join("%s %d -> %d" % (rot, r[k], d[k]) for k, rot in (
        ("sem_tese", "sem tese"), ("observacao", "observação"),
        ("moderada", "moderada"), ("forte", "forte")))
    w = DISTRIBUICAO_ANTES_DO_CONSERTO_DA_SOMA
    mudou_soma = " · ".join("%s %d -> %d" % (rot, w[k], d[k]) for k, rot in (
        ("sem_tese", "sem tese"), ("observacao", "observação"),
        ("moderada", "moderada"), ("forte", "forte")))
    return {"antes": a, "depois": d, "o_que_mudou": mudou,
            "antes_da_regua_de_surpresa": r,
            "o_que_a_regua_mudou": mudou_regua,
            "antes_do_conserto_da_soma_08set": w,
            "o_que_o_conserto_da_soma_mudou": mudou_soma,
            "aviso": AVISO_DISTRIBUICAO, "provisorio": True}

# (D) FRESCOR — limiares PROVISORIOS, em minutos.
FRESCOR_LIMIARES = {"atrasado_min": 45, "muito_atrasado_min": 120}

# (C) PROXIMO EVENTO RELEVANTE — as seis categorias que o dono nomeou: CPI, emprego,
# salarios, PIB, vendas no varejo e PMI. Decisao e coletiva NAO entram: a decisao ja tem
# campo proprio (proxima) e e o limite FINAL do ciclo, nao o proximo risco.
FAMILIAS_RELEVANTES = {
    "inflacao_cheia": "CPI", "inflacao_nucleo": "CPI (núcleo)",
    "emprego_criacao": "emprego", "desemprego": "desemprego",
    "salarios": "salários", "pib": "PIB", "varejo": "vendas no varejo", "pmi": "PMI",
}


def rotulo_do_evento(titulo_original, familia):
    """O nome CURTO e VERDADEIRO do evento, para a tela.

    O rótulo da FAMÍLIA sozinho mente. A família é um balde: "Producer Price Index ex Food &
    Energy" cai em `inflacao_nucleo`, cujo rótulo é "CPI (núcleo)" — e o dono lia CPI onde há
    PPI, na data do PPI (10/09) e não na do CPI (11/09). Do outro lado, "BoC Consumer Price
    Index Core" cai em `inflacao_cheia` (os padrões de núcleo pedem "core" ANTES) e saía como
    "CPI", escondendo que é o núcleo.

    Aqui o nome sai do TÍTULO REAL do evento. A família só entra quando o título não é
    reconhecido — aí o balde é a melhor informação que existe, e ele é honesto para emprego,
    PIB, varejo e PMI, onde não há dois índices diferentes disputando o mesmo nome.
    """
    t = (titulo_original or "").lower()
    nucleo = any(p in t for p in ("core", "ex food", "excluding food", "ex-food",
                                  "trimmed", "median", "underlying", "subjacente", "núcleo",
                                  "nucleo"))
    if "producer price" in t or re.search(r"\bppi\b", t):
        base = "PPI"
    elif ("consumer price" in t or "harmonized index of consumer prices" in t
          or "hicp" in t or re.search(r"\bcpi\b", t)):
        base = "CPI"
    elif "personal consumption" in t or re.search(r"\bpce\b", t):
        base = "PCE"
    elif "retail price" in t or re.search(r"\brpi\b", t):
        base = "RPI"
    else:
        return FAMILIAS_RELEVANTES.get(familia)
    return base + (" (núcleo)" if nucleo else "")

# ---------------------------------------------------------------------------------------
# (4) "UMA DIVULGACAO SO NAO PODE VIRAR A LEITURA" — E O CONSERTO DE 08/set/2026
# ---------------------------------------------------------------------------------------
# O PEDIDO DO DONO (05/set) ESTAVA CERTO. O caso dele: o CAD com uma unica divulgacao de
# emprego (z -7,86) respondendo por 100% da dimensao, com tres divulgacoes no ciclo.
# O LUGAR ONDE A REGRA FOI POSTA ESTAVA ERRADO. Peso relativo e problema de PARTICIPACAO, e
# a regra mexia nos TERMOS DA SOMA — winsorizava cada item em 4,0.
#
# O QUE A WINSORIZACAO FEZ, MEDIDO EM 08/set NA PROPRIA RODADA (o codigo se denunciou sozinho,
# no campo `deslocamento_pelo_teto`):
#     USD   soma -1,19 -> -8,29     direcao MANTEM -> CORTA
#     GBP   soma -4,66 -> -5,77     direcao MANTEM -> CORTA
# Os TRES maiores itens do dolar eram ALTISTAS e estouravam o teto (ISM Services PMI,
# Average Hourly Earnings e Nonfarm Payrolls, os tres MUITO_ACIMA e de impacto HIGH). Foram
# cortados. Os itens baixistas eram menores e passaram inteiros. O corte tirou peso de UM
# LADO SO. Consequencia pratica: o painel lia "USD inclinado ao corte" enquanto os futuros de
# fed funds pagavam p_alta = 0,5786 para o FOMC de 16/set — parte dessa divergencia, que e o
# PRODUTO do painel, era defeito nosso.
#
# A ARITMETICA, PARA NAO PRECISAR DE FE: cortar um termo x para c muda a soma em (c - x), que
# tem o sinal CONTRARIO ao de x. Winsorizar termos de uma soma NAO amortece o item: desloca o
# TOTAL para o lado dos itens que sobraram. Nao existe escolha de teto que conserte isso,
# porque o defeito e da OPERACAO, nao do numero — a versao 1 (teto pela mediana) e a versao 2
# (teto fixo 4,0) morreram da mesma causa, com dois diagnosticos diferentes.
#
# O QUE VALE DESDE 08/set — quatro regras:
#   1. A SOMA E A SOMA. Cada divulgacao entra com a contribuicao real (peso da familia x
#      modulador de impacto x decaimento por idade). NENHUM termo e cortado.
#   2. A DOMINANCIA E A REGUA DE CONFIANCA, NAO DE VALOR. A participacao do maior item na
#      massa absoluta da dimensao continua medida — ela ja existia e ja funcionava. Passando
#      do corte (50%, PROVISORIO) a moeda sai com BANDEIRA e a QUALIDADE DA EVIDENCIA fica
#      limitada. A DIRECAO nao e tocada.
#   3. QUEM QUISER LIMITAR PESO usa `reescala_proporcional`, que multiplica TODOS os itens
#      pelo MESMO fator — a unica forma que preserva o sinal e as proporcoes. Ela esta
#      DESLIGADA, e a propria funcao prova, com a conta, por que ela nao serve de remedio
#      para dominancia: o fator comum CANCELA na participacao.
#   4. LEI ESTRUTURAL: NENHUM TRATAMENTO VIRA A DIRECAO EM SILENCIO (`guarda_de_direcao`).
#      Se qualquer transformacao mudar a direcao em relacao ao cru, sai bandeira, sai texto,
#      e a moeda vai para SEM LEITURA ate alguem decidir — porque leitura cuja direcao depende
#      do tratamento nao e leitura, e escolha de metodo, e escolha de metodo e do dono.
TRATAMENTO_DA_SOMA = "nenhum"

WINSOR_REVOGADA = {
    "ligada": False,
    "revogada_em": "2026-09-08",
    "o_que_era": "cada divulgacao entrava na soma com no maximo 4,0 em modulo (0,8 x limiar)",
    "por_que_caiu": "winsorizar termos de uma SOMA desloca o TOTAL pelo tanto cortado, no "
                    "sentido contrario ao do item cortado. Quando os itens grandes estao "
                    "todos do MESMO lado — foi o caso do dolar, com os tres maiores altistas "
                    "e de impacto HIGH — o corte tira peso de um lado so e a soma anda para o "
                    "outro. Nao amortece: desloca.",
    "medido_em_08set": {"USD": {"soma_crua": -1.19, "soma_winsorizada": -8.29,
                                "direcao": "MANTEM -> CORTA"},
                        "GBP": {"soma_crua": -4.66, "soma_winsorizada": -5.77,
                                "direcao": "MANTEM -> CORTA"}},
    "o_que_entrou_no_lugar": "a soma crua manda na DIRECAO; a dominancia manda na CONFIANCA "
                             "(bandeira + teto na qualidade da evidencia); e a guarda de "
                             "direcao proibe que qualquer tratamento futuro vire a leitura em "
                             "silencio.",
    "o_que_se_perdeu_declarado": "a garantia aritmetica de que UMA divulgacao sozinha nunca "
                                  "atinge o limiar. Ela existia, mas era paga com deslocamento "
                                  "da soma. Agora esse caso e possivel e sai DECLARADO no "
                                  "campo `virou_sozinho`, com bandeira e com a qualidade da "
                                  "evidencia derrubada — visivel em vez de mascarado.",
}

# A REGUA DE CONFIANCA. O numero 50 e o mesmo corte que ja existia no alerta de dominancia.
DOMINANCIA = {
    "corte_participacao_pct": 50,
    "o_que_mede": "a participacao do MAIOR item na massa absoluta (soma dos modulos) da "
                  "dimensao de dados da moeda",
    "o_que_faz": "e regua de CONFIANCA, nao de valor: acima do corte a moeda sai com BANDEIRA "
                 "e a qualidade da evidencia fica limitada a (100 - participacao). A DIRECAO "
                 "nunca e alterada por causa dela.",
    "por_que_o_teto_e_100_menos_a_participacao": "a nota de evidencia nao pode ser maior que a "
        "fatia da massa que NAO vem do item dominante: se 76% da dimensao e uma divulgacao so, "
        "no maximo 24% da evidencia e de CONJUNTO. O teto usa a mesma medida do alerta, sem "
        "numero novo, e so morde acima do corte (participacao > 50 => teto < 50 => 'fraca').",
    "provisorio": True,
}


# ---------------------------------------------------------------------------------------
# A FAIXA NEUTRA — O MESMO ERRO DA WINSORIZACAO, NA OUTRA DIRECAO (auditoria de 08/set)
# ---------------------------------------------------------------------------------------
# A winsorizacao cortava por CIMA os termos da soma. A faixa neutra corta por BAIXO: toda
# divulgacao com |divulgado - consenso| <= corte da familia entra na soma como ZERO
# (macro_eventos.classifica -> EM_LINHA -> empurrao devolve 0).
#
# A ARITMETICA E A MESMA, E ISSO E O PONTO DESTA AUDITORIA: zerar um termo x muda a soma em
# (0 - x) = -x, com o sinal CONTRARIO ao do termo zerado. Se o que cai dentro da faixa esta
# concentrado de um lado, a soma anda para o outro — exatamente o mecanismo que virou a
# direcao do USD e do GBP com o teto de 4,0.
#
# MEDIDO EM 08/set, na mesma rodada publicada (data/sentimento.json, gerado 14:30 UTC):
#     USD  47 divulgacoes caem na faixa e entram como zero. Somadas com o sinal do proprio
#          desvio elas valeriam -15,11. A soma publicada e -1,17 (MANTEM); sem a faixa seria
#          -16,28 (CORTA). Com a MESMA regua pela METADE ja e -10,80 (CORTA).
#     EUR  90 zeradas, valeriam -3,98   ·   GBP 21 zeradas, valeriam -1,04
#     JPY  12 zeradas, valeriam +3,37   ·   AUD  8 zeradas, valeriam +1,43
#
# A DIFERENCA PARA A WINSORIZACAO — e por isso a faixa NAO foi revogada:
#   a winsorizacao nao tinha tese: cortar em 4,0 era um numero escolhido para segurar
#   dominancia, e dominancia nao e problema de soma. A faixa neutra TEM tese economica
#   declarada ("veio como esperado — nao muda o que ja estava no preco") e e a mesma regua
#   dos tres leitores (macro_eventos.corte_da_surpresa). Revoga-la aqui seria trocar um
#   metodo por outro sem medida, e a escolha de metodo e do dono, nao do codigo.
#
# O QUE ESTAVA ERRADO, E O QUE MUDA AGORA: o arquivo declarava "tratamento da soma: nenhum,
# deslocamento 0,00, direcao do dado e nao do metodo" — e isso so era verdade DEPOIS da
# classificacao. A guarda de direcao chamava de "cru" um numero que ja tinha passado pela
# faixa, entao ela nao conseguia enxergar o maior tratamento do caminho. Desde agora a faixa
# sai MEDIDA em toda rodada: quantos itens ela zera, quanto eles pesariam, qual seria a
# direcao sem ela e com ela pela metade e pelo dobro — e quando a direcao depende da faixa,
# isso vira alerta no par, que e onde a tela le.
FAIXA_NEUTRA = {
    "o_que_e": "divulgacao com |divulgado - consenso| dentro do corte da familia entra na "
               "soma como ZERO",
    "onde_mora": "macro_eventos.corte_da_surpresa (a mesma regua dos tres leitores)",
    "e_um_piso_em_termos_de_uma_soma": True,
    "mesma_aritmetica_da_winsorizacao": "zerar um termo x desloca a soma em -x, no sentido "
                                        "contrario ao do termo zerado",
    "por_que_nao_foi_revogada": "tem tese economica declarada e e a regua unica da casa; "
                                "trocar de metodo sem medida e decisao do dono",
    "o_que_passou_a_sair": "itens zerados, quanto pesariam, e a direcao com a faixa em 0x, "
                           "0,5x, 1x e 2x — o painel nao esconde tratamento que mexe na "
                           "direcao",
    "fatores_de_teste": [0.0, 0.5, 1.0, 2.0],
    "provisorio": True,
}


def participacao_do_maior(valores):
    """Participacao do MAIOR item na massa absoluta (soma dos modulos), em % inteiro.

    E a medida de dominancia do dono, e ela e INVARIANTE a qualquer reescala proporcional:
    multiplicar todos os itens por k multiplica numerador e denominador por k. E por isso que
    reescalar nao e remedio para concentracao — ver `reescala_proporcional`.
    """
    massa = sum(abs(v) for v in valores)
    if not massa:
        return 0
    return int(round(max(abs(v) for v in valores) / massa * 100))


def reescala_proporcional(valores, teto_participacao_pct=None, ligada=False):
    """Limitar peso SEM enviesar: multiplicar TODOS os itens pelo MESMO fator.

    E a unica forma que preserva o SINAL de cada item, o SINAL da soma e as proporcoes entre
    os itens — winsorizar nao preserva nenhuma das tres, porque so mexe em quem e grande.

    ⚠️ E EXATAMENTE POR PRESERVAR AS PROPORCOES QUE ELA NAO RESOLVE DOMINANCIA. A participacao
    do maior item e |x_max|.k / SOMA(|x_i|.k) = |x_max| / SOMA(|x_i|): o k CANCELA. Nenhum
    fator comum, por menor que seja, derruba a participacao de 100% do NZD para abaixo de 50%.
    Reescalar limita MAGNITUDE; o pedido do dono e sobre PARTICIPACAO. Sao coisas diferentes, e
    e por isso que a resposta de participacao mora na CONFIANCA (dominancia) e nao na soma.

    Fica implementada, medida e DESLIGADA. Devolve (fator, registro).
    """
    part = participacao_do_maior(valores)
    reg = {"nome": "reescala_proporcional", "ligada": bool(ligada),
           "teto_participacao_pct": teto_participacao_pct,
           "participacao_medida_pct": part,
           "preserva": ["sinal de cada item", "sinal da soma", "proporcoes entre os itens"],
           "prova": "participacao(k.x) = |x_max|.k / SOMA(|x_i|.k) = participacao(x) para "
                    "todo k > 0 — o fator comum cancela, entao nenhum fator atinge um teto de "
                    "PARTICIPACAO. Ver `regua.tratamento_da_soma.prova_sintetica`.",
           "provisorio": True}
    if not ligada:
        reg["fator"] = 1.0
        reg["por_que_desligada"] = (
            "ela limitaria MAGNITUDE, nao PARTICIPACAO, e magnitude nao e o problema que o "
            "dono levantou. Encolher a soma inteira por um fator comum tambem NAO e neutro "
            "para a leitura: o limiar de %s e fixo, entao dividir tudo por 2 empurra moedas "
            "de SOBE/CORTA para MANTEM sem que nenhum dado tenha mudado." % LIMIAR_DADOS)
        return 1.0, reg
    if teto_participacao_pct is None or part <= teto_participacao_pct:
        reg["fator"] = 1.0
        reg["resultado"] = "participacao %d%% ja esta no teto — nada a reescalar" % part
        return 1.0, reg
    # Ligada e acima do teto: NAO existe fator que resolva. Devolve 1,0 e diz por que.
    reg["fator"] = 1.0
    reg["resultado"] = (
        "participacao %d%% acima do teto de %d%%, e NENHUM fator comum a derruba (o k cancela). "
        "A reescala foi pedida e nao foi aplicada: aplicar qualquer fator aqui seria encolher a "
        "leitura sem tocar na concentracao, que e o defeito. Quem responde por concentracao e a "
        "bandeira de dominancia." % (part, teto_participacao_pct))
    return 1.0, reg


def direcao_da_soma(soma):
    """A direcao da dimensao de dados a partir da soma, com o limiar declarado."""
    return "SOBE" if soma >= LIMIAR_DADOS else "CORTA" if soma <= -LIMIAR_DADOS else "MANTEM"


def guarda_de_direcao(onde, leitura_crua, leitura_tratada, tratamento=TRATAMENTO_DA_SOMA):
    """LEI ESTRUTURAL (08/set): NENHUM TRATAMENTO VIRA A DIRECAO EM SILENCIO.

    Vale para QUALQUER transformacao entre o dado cru e a leitura publicada — winsorizacao,
    reescala, teto, aparo, o que for inventado depois. Se a direcao tratada difere da crua, o
    campo sai com bandeira e texto, e quem consome manda a moeda para SEM LEITURA.

    Nao e uma opiniao sobre qual das duas esta certa: e a constatacao de que a direcao passou a
    depender do METODO e nao do dado. Escolher entre elas e do dono, nao do codigo.
    """
    virou = (leitura_crua != leitura_tratada)
    return {
        "virou": bool(virou),
        "de": leitura_crua, "para": leitura_tratada, "tratamento": tratamento,
        "texto": ("o tratamento '%s' MUDOU a direcao de %s para %s em %s — a leitura passa a "
                  "depender do metodo e nao do dado, entao ela sai BANDEIRADA e a moeda vai "
                  "para SEM LEITURA ate alguem decidir qual das duas vale"
                  % (tratamento, leitura_crua, leitura_tratada, onde)) if virou else None,
        "regra": "lei estrutural de 08/set/2026: se qualquer transformacao mudar a direcao em "
                 "relacao ao cru, isso APARECE e a leitura e suspensa — nunca e silenciado. "
                 "Foi a familia inteira de erro que a winsorizacao produziu.",
        "provisorio": True,
    }


def prova_do_tratamento():
    """A PROVA SINTETICA, calculada em toda rodada — nao e comentario, e conta rodando.

    CASO 1 reproduz a forma do dolar: tres itens grandes de um lado, muitos pequenos do outro.
        cru      +9 +8 +7 e dez de -2   -> soma +4  (MANTEM, |4| < limiar 5)
        winsor 4 +4 +4 +4 e dez de -2   -> soma -8  (CORTA)   *** virou a direcao ***
        reescala k=0,5                  -> soma +2  (MANTEM)  sinal PRESERVADO
    CASO 2 mostra por que reescalar nao resolve concentracao: participacao INVARIANTE a k.
    """
    def soma(v):
        return round(sum(v), 2)

    c1 = [9.0, 8.0, 7.0] + [-2.0] * 10
    teto_velho = 4.0
    c1_w = [math.copysign(min(abs(x), teto_velho), x) for x in c1]
    k = 0.5
    c1_r = [x * k for x in c1]
    c2 = [-7.9, 0.3, -0.2]
    c2_r = [x * 0.1 for x in c2]
    return {
        "caso_1_forma_do_dolar": {
            "itens": c1,
            "cru": {"soma": soma(c1), "direcao": direcao_da_soma(soma(c1)),
                    "participacao_pct": participacao_do_maior(c1)},
            "winsorizado_4_0": {"soma": soma(c1_w), "direcao": direcao_da_soma(soma(c1_w)),
                                "participacao_pct": participacao_do_maior(c1_w),
                                "virou_a_direcao": direcao_da_soma(soma(c1_w)) != direcao_da_soma(soma(c1)),
                                "deslocamento": round(soma(c1_w) - soma(c1), 2)},
            "reescalado_k_0_5": {"soma": soma(c1_r), "direcao": direcao_da_soma(soma(c1_r)),
                                 "participacao_pct": participacao_do_maior(c1_r),
                                 "sinal_igual_ao_cru": (soma(c1_r) > 0) == (soma(c1) > 0),
                                 "virou_a_direcao": direcao_da_soma(soma(c1_r)) != direcao_da_soma(soma(c1))},
            "leitura": "o corte por item VIROU a direcao (MANTEM -> CORTA) deslocando a soma "
                       "em -12,0; a reescala proporcional manteve o SINAL (+4 -> +2) e manteve "
                       "a participacao. O que muda a direcao e cortar de um lado so."},
        "caso_2_participacao_invariante": {
            "itens": c2, "participacao_crua_pct": participacao_do_maior(c2),
            "itens_reescalados_k_0_1": c2_r,
            "participacao_reescalada_pct": participacao_do_maior(c2_r),
            "leitura": "a participacao do maior item nao se move com a reescala (o k cancela): "
                       "reescalar limita MAGNITUDE, nunca CONCENTRACAO. Por isso a resposta a "
                       "concentracao e a bandeira de dominancia e o teto na qualidade da "
                       "evidencia, e nao um tratamento na soma."},
        "conclusao": "a soma fica crua; concentracao vira CONFIANCA; e a guarda de direcao "
                     "impede que qualquer tratamento futuro vire a leitura em silencio.",
    }

# (3b) confiabilidade da fala. O que o construtor de fontes grava hoje: bc_discursos.json traz
# tipo "speech" (discurso oficial) e "statement" (comunicado/ata); noticias.json traz manchete
# do Google News. "imprensa_com_fala" existe na regua para quando a fonte trouxer citacao
# atribuida a um dirigente identificavel.
PESOS_DE_FALA = {"discurso_oficial": 1.0, "comunicado_ata": 1.0,
                 "imprensa_com_fala": 0.4, "manchete": 0.0}

# (6) ciclo com decaimento continuo, no lugar do penhasco de 180 dias.
CICLO_MEIA_VIDA_DIAS = 120.0        # o ultimo movimento perde metade do peso em 4 meses
CICLO_MEIA_VIDA_REUNIOES = 3.0      # DESLIGADO em 05/set: media o arquivo, nao o banco
CICLO_PISO_VOTO = 0.25              # abaixo disto o movimento le como MANUTENCAO, nao ciclo

QUALIDADE_N_SATURA = 12             # divulgacoes + falas na janela para a nota de quantidade

# (3b) diversidade: quantas familias INDEPENDENTES apareceram na janela.
FAMILIAS_INDEPENDENTES = ["inflacao", "emprego", "atividade", "comunicacao"]
MAPA_FAMILIA = {
    "inflacao_nucleo": "inflacao", "inflacao_cheia": "inflacao",
    "expectativa_inflacao": "inflacao",
    "emprego_criacao": "emprego", "desemprego": "emprego", "salarios": "emprego",
    "auxilio_desemprego": "emprego",
    "pmi": "atividade", "pib": "atividade", "varejo": "atividade", "producao": "atividade",
    "confianca": "atividade", "moradia": "atividade", "balanca": "atividade",
    "coletiva": "comunicacao", "decisao": "comunicacao",
}

NOTA_CONVICCAO_HISTORICA = "ainda não calibrada — precisa de backtest com amostra declarada"


def carrega_json(fn):
    try:
        return json.load(io.open(fn, encoding="utf-8"))
    except Exception:
        return None


def mediana(v):
    if not v:
        return 0.0
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def chave_titulo(t):
    """Titulo normalizado para achar duplicata: minusculo, so alfanumerico, sem a assinatura
    da fonte depois do ultimo travessao."""
    t = (t or "").lower()
    t = re.split(r"\s[-–—]\s", t)[0]
    return re.sub(r"[^a-z0-9]+", "", t)


def eventos_janela(agora):
    """Busca 42 dias PARA TRAS e 30 PARA FRENTE da FXStreet (o calendario do site so guarda
    ±8 dias). Se a fonte falhar, usa o arquivo local — janela curta, mas declarada na saida.

    Os 30 dias para FRENTE nao votam em nada: a dimensao de dados so olha eventos com
    `divulgado` preenchido e `quando_utc <= agora`. Eles existem por causa do PROXIMO EVENTO
    RELEVANTE (prioridade 4 do dono): com so 1 dia de horizonte, cinco das oito moedas ficavam
    sem evento nenhum a mostrar, e "null" por horizonte curto e diferente de "null" por nao
    haver evento.

    Devolve tambem QUANDO o calendario foi sincronizado com sucesso — e o dado que manda no
    bloco de FRESCOR da raiz.
    """
    try:
        cru = buscar(dias_atras=JANELA_DIAS, dias_frente=HORIZONTE_FRENTE_DIAS)
        ev = [x for x in (normaliza(e) for e in cru) if x]
        return (ev, "fxstreet %d dias atrás + %d à frente" % (JANELA_DIAS, HORIZONTE_FRENTE_DIAS),
                agora.isoformat(), True)
    except Exception as e:
        print("  ! FXStreet indisponivel para a janela longa (%s) — usando o arquivo local" % e)
        loc = carrega_json(CAL_LOCAL) or {}
        return (loc.get("eventos", []), "arquivo local (janela curta)",
                loc.get("gerado_em"), False)


def eventos_para_frente(ev, agora):
    """Uniao dos eventos FUTUROS que temos: os da busca ao vivo mais os dois arquivos de
    calendario (calendario_resultado.json e macro_eventos.json). Sem duplicata."""
    fut, vistos = [], set()
    fontes = [("ao vivo", ev)]
    for fn in (CAL_LOCAL, os.path.join(AQUI, "data", "macro_eventos.json")):
        arq = carrega_json(fn) or {}
        fontes.append((os.path.basename(fn), arq.get("eventos") or []))
    agora_iso = agora.isoformat()
    for _nome, lista in fontes:
        for e in lista:
            quando = e.get("quando_utc")
            if not quando or quando <= agora_iso:
                continue
            # macro_eventos.json chama de "resultado" o que o calendario chama de "divulgado"
            divulgado = e.get("divulgado", e.get("resultado"))
            if divulgado is not None:
                continue                       # ja saiu: nao e mais risco a frente
            chave = (e.get("moeda"), chave_titulo(e.get("titulo")), quando[:16])
            if chave in vistos:
                continue
            vistos.add(chave)
            fut.append(e)
    fut.sort(key=lambda x: x.get("quando_utc") or "")
    return fut


def mede_faixa_neutra(medidos, moeda, soma_publicada):
    """Quanto a FAIXA NEUTRA move a soma, e se a DIRECAO depende dela. Nao altera nada.

    A faixa e um PISO aplicado a cada termo ANTES da soma: quem fica dentro dela entra como
    zero. E a mesma aritmetica da winsorizacao revogada em 08/set — zerar um termo x desloca
    o total em -x —, so que por baixo em vez de por cima. Ela continua ligada porque tem tese
    ("veio como esperado nao muda o preco") e porque a regua e a mesma dos tres leitores; o
    que muda e que ela para de ser invisivel.

    Refaz a MESMA conta com o corte da familia multiplicado por 0 (sem faixa), 0,5, 1 (a de
    hoje, que reproduz a soma publicada) e 2. Nenhum numero novo e inventado: e a regua
    existente, reescalada, para mostrar de quanto a leitura depende dela.
    """
    def soma_com(k):
        t = 0.0
        for x in medidos:
            c = x["corte"] * k
            if x["dif"] > c:
                lado = +1
            elif x["dif"] < -c:
                lado = -1
            else:
                continue                       # dentro da faixa: entra como ZERO
            # arredonda o TERMO em 2 casas, como `contribuicao_bruta` — assim a coluna de
            # fator 1,0 reproduz exatamente a soma publicada, e a comparacao e honesta.
            t += round(x["peso"] * lado * x["sinal"] * x["mod"] * x["decai"], 2)
        return round(t, 2)

    zerados = [x for x in medidos if x["classe"] == "EM_LINHA"]
    peso_zerado = 0.0
    for x in zerados:
        lado = (1 if x["dif"] > 0 else -1 if x["dif"] < 0 else 0) * x["sinal"]
        peso_zerado += x["peso"] * lado * x["mod"] * x["decai"]
    peso_zerado = round(peso_zerado, 2)

    escala = []
    for k in FAIXA_NEUTRA["fatores_de_teste"]:
        sk = soma_com(k)
        escala.append({"fator": k, "soma": sk, "direcao": direcao_da_soma(sk)})
    direcoes = {e["direcao"] for e in escala}
    depende = len(direcoes) > 1
    sem_faixa = escala[0]

    txt = None
    if depende:
        txt = ("a direção da dimensão de dados do %s DEPENDE da faixa neutra: com a régua de "
               "hoje a soma é %+.2f (%s), sem faixa nenhuma seria %+.2f (%s), e com a mesma "
               "régua pela metade seria %+.2f (%s). A faixa zera %d divulgação(ões) que, com "
               "o sinal do próprio desvio, pesariam %+.2f — zerar um termo desloca a soma no "
               "sentido contrário ao dele, que é a mesma aritmética da winsorização revogada. "
               "A faixa NÃO foi desligada: ela tem tese e é a régua única da casa. O que muda "
               "é que isto aparece."
               % (moeda, soma_publicada, direcao_da_soma(soma_publicada),
                  sem_faixa["soma"], sem_faixa["direcao"],
                  escala[1]["soma"], escala[1]["direcao"], len(zerados), peso_zerado))

    return {
        "itens_zerados": len(zerados),
        "peso_que_os_zerados_teriam": peso_zerado,
        "soma_sem_faixa": sem_faixa["soma"],
        "direcao_sem_faixa": sem_faixa["direcao"],
        "deslocamento_pela_faixa": round(soma_publicada - sem_faixa["soma"], 2),
        "escala": escala,
        "direcao_depende_da_faixa": bool(depende),
        "texto": txt,
        "o_que_e": FAIXA_NEUTRA["o_que_e"],
        "por_que_nao_foi_revogada": FAIXA_NEUTRA["por_que_nao_foi_revogada"],
        "provisorio": True,
    }


# ---------------------------------------------------------------------------------------
# DIMENSAO 1 — DADOS (soma CRUA + dominancia como regua de confianca)
# ---------------------------------------------------------------------------------------
def dimensao_dados(ev, moeda, agora):
    """Surpresas desde a ultima decisao. A SOMA E A SOMA — nenhum termo e cortado (08/set).

    (4) O caso do dono continua valendo: o CAD tinha uma unica divulgacao de emprego
    respondendo por quase toda a leitura de dados, com pouquissimas divulgacoes no ciclo. Isso
    E um problema, e ele e tratado aqui — mas na CONFIANCA, nao no valor: a participacao do
    maior item sai medida, acima de 50% a moeda leva BANDEIRA e a qualidade da evidencia fica
    limitada a (100 - participacao). A direcao sai do dado, nao do tratamento.

    O que existia aqui ate 07/set — winsorizar cada item em 4,0 — deslocava a soma para o lado
    dos itens que sobravam e chegou a VIRAR a direcao do USD e do GBP em 08/set. Ver o bloco
    WINSOR_REVOGADA e `regua.tratamento_da_soma.prova_sintetica`.
    """
    meus = [e for e in ev if e.get("moeda") == moeda and e.get("divulgado") is not None
            and e.get("quando_utc")]
    inicio = (agora - dt.timedelta(days=JANELA_DIAS)).isoformat()
    meus = [e for e in meus if e["quando_utc"] >= inicio and e["quando_utc"] <= agora.isoformat()]

    # a DECISAO zera o ciclo: so conta o que saiu depois da ultima
    decisoes = [e["quando_utc"] for e in meus if familia_de(e.get("titulo"))[0] == "decisao"]
    corte = max(decisoes) if decisoes else None

    n, n_alto, brutos, familias = 0, 0, [], set()
    # o que a FAIXA NEUTRA precisa para ser medida: peso, sinal, desvio e o corte da familia
    # de CADA divulgacao, inclusive das que a faixa zera (essas nao entram em `brutos`).
    medidos = []
    for e in meus:
        if corte and e["quando_utc"] <= corte:
            continue
        nome, fam = familia_de(e.get("titulo"))
        if nome:
            familias.add(nome)
        if not fam or not fam.get("peso"):
            continue
        # `nome` (a familia) escolhe o corte: a regua e UMA so, em macro_eventos.corte_da_surpresa
        classe, dif = classifica(e.get("divulgado"), e.get("consenso"), familia=nome)
        if classe is None:
            continue
        forca, _txt = empurrao(classe, fam)
        imp = IMPACTO_FXS.get(str(e.get("impacto")).upper(), "Low").lower()
        mod = MODULADORES.get("impacto_" + {"high": "alto", "medium": "medio"}.get(imp, "baixo"), 0.2)
        try:
            quando = dt.datetime.fromisoformat(e["quando_utc"])
        except ValueError:
            continue
        idade = max(0.0, (agora - quando).total_seconds() / 86400.0)
        decai = 0.5 ** (idade / MEIA_VIDA)
        contrib = forca * mod * decai
        n += 1
        n_alto += (imp == "high")
        medidos.append({"dif": dif, "peso": fam["peso"], "sinal": fam["sinal"],
                        "mod": mod, "decai": decai,
                        "corte": corte_da_surpresa(e.get("consenso"), nome),
                        "titulo": e.get("titulo"), "familia": nome, "classe": classe})
        if contrib:
            brutos.append({"quando_utc": e["quando_utc"], "titulo": e.get("titulo"),
                           "familia": nome, "classe": classe, "impacto": e.get("impacto"),
                           "divulgado": e.get("divulgado"), "consenso": e.get("consenso"),
                           "contribuicao_bruta": round(contrib, 2),
                           "contribuicao": round(contrib, 2), "idade_dias": round(idade, 1),
                           "tratado": False})

    # ---- A SOMA VOLTOU A SER A SOMA (conserto de 08/set) -------------------------------
    # Nenhum termo e cortado. A mediana continua calculada como DESCRITOR da janela — ela nao
    # manda em nada desde 05/set e continua nao mandando.
    med = mediana([abs(x["contribuicao_bruta"]) for x in brutos])
    soma_crua = round(sum(x["contribuicao_bruta"] for x in brutos), 2)
    part_antes = participacao_do_maior([x["contribuicao_bruta"] for x in brutos])

    # O tratamento declarado de hoje e "nenhum". A reescala proporcional existe, esta
    # DESLIGADA, e a propria funcao prova por que ela nao e remedio para concentracao.
    fator, registro_tratamento = reescala_proporcional(
        [x["contribuicao_bruta"] for x in brutos],
        teto_participacao_pct=DOMINANCIA["corte_participacao_pct"],
        ligada=(TRATAMENTO_DA_SOMA == "reescala_proporcional"))
    n_tratados = 0
    if fator != 1.0:
        for x in brutos:
            x["contribuicao"] = round(x["contribuicao_bruta"] * fator, 2)
            x["tratado"] = True
            n_tratados += 1

    soma = round(sum(x["contribuicao"] for x in brutos), 2)
    part_depois = participacao_do_maior([x["contribuicao"] for x in brutos])
    brutos.sort(key=lambda x: -abs(x["contribuicao"]))

    direcao = direcao_da_soma(soma)
    direcao_crua = direcao_da_soma(soma_crua)
    guarda = guarda_de_direcao("a dimensão de dados do %s" % moeda, direcao_crua, direcao,
                               TRATAMENTO_DA_SOMA)
    # A FAIXA NEUTRA e o tratamento que sobrou de pe, e ela mora ANTES daqui: a guarda acima
    # compara a soma tratada com a "crua", mas as duas ja passaram pela faixa. Isto mede o que
    # a guarda nao alcanca.
    faixa = mede_faixa_neutra(medidos, moeda, soma_crua)

    # ---- DOMINANCIA — A REGUA DE CONFIANCA, NAO DE VALOR -------------------------------
    # Ela ja existia e ja funcionava; o que mudou em 08/set foi o que ela COMANDA. Passando do
    # corte, a moeda leva BANDEIRA e a qualidade da evidencia fica limitada a
    # (100 - participacao). A direcao nao e tocada — e essa e a diferenca inteira.
    corte_dom = DOMINANCIA["corte_participacao_pct"]
    dominancia = {
        "alerta": bool(brutos) and part_depois > corte_dom,
        "item": brutos[0]["titulo"] if brutos else None,
        "share_pct": part_depois,
        "corte_pct": corte_dom,
        "participacao_maior_item_antes": part_antes,
        "participacao_maior_item_depois": part_depois,
        "teto_na_qualidade_da_evidencia": ((100 - part_depois)
                                           if (brutos and part_depois > corte_dom) else None),
        "muda_a_direcao": False,
        "o_que_faz": DOMINANCIA["o_que_faz"],
        "texto": None,
        "provisorio": True,
    }
    if dominancia["alerta"]:
        dominancia["texto"] = ("uma única divulgação responde por %d%% da leitura de dados do %s "
                               "(%s), com %d divulgações no ciclo — a leitura sai MARCADA e a "
                               "qualidade da evidência fica limitada a %d/100; a DIREÇÃO não é "
                               "alterada por causa disto"
                               % (part_depois, moeda, brutos[0]["titulo"], n, 100 - part_depois))

    # AUDITORIA — os dois campos que denunciam o proprio metodo, agora com o sentido certo.
    #   virou_sozinho   UMA divulgacao sozinha passou do limiar E responde por mais de metade
    #                   da massa. Com a soma crua isso e POSSIVEL, e e exatamente por isso que
    #                   o campo existe: o caso sai DECLARADO — bandeira + evidencia derrubada —
    #                   em vez de mascarado por um corte que desloca o total para o outro lado.
    #   deslocamento    quanto a soma andou por causa de TRATAMENTO. Hoje e 0,00 sempre, porque
    #                   nao ha tratamento; o campo fica de pe para o dia em que houver.
    maior = abs(brutos[0]["contribuicao"]) if brutos else 0.0
    virou_sozinho = bool(direcao != "MANTEM" and brutos and maior >= LIMIAR_DADOS - 1e-9
                         and part_depois > corte_dom)
    deslocamento = round(soma - soma_crua, 2)

    fam_ind = sorted({MAPA_FAMILIA[f] for f in familias if f in MAPA_FAMILIA})
    # SILENCIO NAO E VOTO (lei do dono, aplicada aqui em 05/set): moeda sem NENHUMA
    # divulgacao na janela lia "MANTEM" com soma 0,0 e contava como dimensao ligada — o NZD
    # saia com duas dimensoes votando tendo zero dado. A direcao continua exibida, mas com
    # "vota": false, e o teto da moeda cai para 0,25, o que joga a moeda em SEM LEITURA.
    return {"direcao": direcao, "direcao_crua": direcao_crua,
            "vota": n > 0,
            "por_que_nao_vota": None if n > 0 else
            ("nenhuma divulgação do %s na janela de %d dias — silêncio não é voto: a dimensão "
             "não conta e BAIXA o teto da moeda, em vez de entrar como MANTEM" % (moeda, JANELA_DIAS)),
            # ---- OS QUATRO CAMPOS DE AUDITORIA QUE SAEM SEMPRE (lei de 08/set) ---------
            # soma crua · soma tratada · participação do maior item antes e depois · bandeira
            # de mudança de direção. Hoje as duas somas são iguais e a bandeira é false, e é
            # isso que se quer poder VERIFICAR sem ler o código.
            "soma": soma, "soma_crua": soma_crua, "soma_tratada": soma,
            "participacao_maior_item_antes": part_antes,
            "participacao_maior_item_depois": part_depois,
            "direcao_mudou_pelo_tratamento": guarda["virou"],
            "bandeira_de_direcao": guarda["texto"],
            "n": n, "n_alto": n_alto,
            "desde": corte or inicio[:10], "zerado_por_decisao": bool(corte),
            "limiar": LIMIAR_DADOS, "meia_vida_dias": MEIA_VIDA,
            "virou_sozinho": {
                "sim": virou_sozinho,
                "texto": ("a dimensão foi para %s com UMA divulgação: ela vale %.2f sozinha (o "
                          "limiar é %.1f) e responde por %d%% da massa da dimensão. A direção "
                          "FICA como está — quem responde por concentração é a bandeira de "
                          "dominância e a qualidade da evidência, nunca um corte na soma"
                          % (direcao, maior, LIMIAR_DADOS, part_depois)) if virou_sozinho
                         else None,
                "por_que_existe": "com a soma crua, uma divulgação sozinha PODE atingir o "
                                  "limiar. O caso sai declarado em vez de mascarado — a "
                                  "garantia antiga (teto 4,0 < limiar 5,0) era paga com "
                                  "deslocamento da soma, e o preço era virar a direção."},
            "tratamento_da_soma": {
                "nome": TRATAMENTO_DA_SOMA,
                "fator": fator, "itens_tratados": n_tratados,
                "deslocamento": deslocamento,
                "soma_crua": soma_crua, "soma_tratada": soma,
                "direcao_crua": direcao_crua, "direcao_tratada": direcao,
                "direcao_mudou": guarda["virou"],
                "bandeira": guarda["texto"],
                "guarda_de_direcao": guarda,
                "registro": registro_tratamento,
                "mediana_absoluta_da_janela": round(med, 2),
                "mediana_manda_em_alguma_coisa": False,
                "texto": "não há tratamento na soma desde 08/set: soma tratada = soma crua, "
                         "deslocamento 0,00, direção do dado e não do método. O que existia "
                         "aqui (winsorizar cada item em 4,0) deslocava o total para o lado dos "
                         "itens que sobravam e virou a direção do USD e do GBP. A autópsia "
                         "inteira está em regua.tratamento_da_soma.winsor_revogada.",
                "provisorio": True},
            "dominancia": dominancia,
            "faixa_neutra": faixa,
            "direcao_depende_da_faixa_neutra": faixa["direcao_depende_da_faixa"],
            "familias_na_janela": sorted(familias),
            "familias_independentes": fam_ind,
            "principais": brutos[:6]}


# ---------------------------------------------------------------------------------------
# VEREDITO POR ORADOR — le NEGACAO, CONDICAO e TEMPO VERBAL. NAO VOTA.
# ---------------------------------------------------------------------------------------
# Por que existe: a contagem de palavras do bc_discursos.py tem "holding the target" na lista
# de termos HAWKISH. Waller disse que apoiaria MANTER e a tela marcou alta. Barr e hawkish
# CONDICIONAL ("if inflation appears not to be moderating"). Warsh fala em preservar a
# liberdade de decidir, o que nao e alta nem corte. Este bloco separa as tres coisas.
#
# ⚠️ ELE TAMBEM NAO VOTA. E um classificador de regra, escrito a mao, nunca medido contra
# rotulo humano. Entra como CONTEXTO na tela, com o mesmo selo da dimensao. A regra do dono:
# "ate esse classificador ser validado, discursos por contagem deveriam ficar como contexto
# SEM VOTO, exatamente como a geopolitica".
VER_ALTA = ("raise the policy rate", "raise rates", "raise interest rates", "raise the target",
            "rate increase", "rate increases", "rate hike", "rate hikes", "hike", "hikes",
            "tighten", "tightening", "further increases", "additional tightening",
            "increase the policy rate", "higher rates", "act decisively to raise")
VER_CORTE = ("cut the policy rate", "lower the policy rate", "reduce the policy rate",
             "rate cut", "rate cuts", "cut rates", "cutting rates", "cut interest rates",
             "lower interest rates", "reduce interest rates", "rate reduction", "ease policy",
             "easing policy", "appropriate to reduce", "less restrictive", "insurance cut",
             "easing cycle", "move toward neutral")
VER_MANUTENCAO = ("holding the target", "hold the target", "keep the policy rate",
                  "keep rates on hold", "rates on hold", "on hold", "at its current setting",
                  "current setting", "leave the policy rate", "leave rates", "unchanged",
                  "maintain the current", "hold rates", "keep rates")
# a condicao pode vir antes ou depois; o que importa e o que fica DEPOIS do conector
VER_CONDICAO = ("if ", "unless ", "were to", "should the", "in the event", "depending on",
                "conditional on", "provided that", "as long as", "in case ")
# condicao de CONTINUIDADE = o cenario BASE ("se o dado seguir como esta"), nao um desvio
VER_CONTINUIDADE = ("continues", "continue to", "continues to", "as expected", "in line with",
                    "stays", "remains on track", "as i expect", "keeps improving",
                    "this continues", "data continue")
VER_MODAL = ("would", "could", "might", "may ", "were to", "should")
VER_NEGACAO = ("not ", "n't", " no ", "never", "unlikely", "rule out", "ruled out")
VER_PASSADO = ("back then", "at that time", "in the past", "i supported", "we supported",
               "had been", "had stopped", "used to", "last year", "years ago")
# descricao do que o MERCADO espera nao e postura do orador: "expected Bank Rate increases"
# fala da curva, nao do que ele quer fazer.
VER_MERCADO = ("market", "markets", "prospective", "priced", "investors", "expectations of",
               "expected bank", "expected rate", "expected policy", "curve")
VER_JANELA_NEGACAO = 25          # caracteres antes do termo em que a negacao ainda pega
VER_JANELA_MODAL = 30
VER_JANELA_MERCADO = 40


def _acha_termos(seg):
    """Todas as ocorrencias de verbo de politica no trecho, na ordem em que aparecem."""
    achados = []
    for direcao, termos in (("alta", VER_ALTA), ("corte", VER_CORTE),
                            ("manutenção", VER_MANUTENCAO)):
        for t in termos:
            i = seg.find(t)
            while i >= 0:
                achados.append((i, direcao, t))
                i = seg.find(t, i + 1)
    achados.sort()
    # o termo mais longo ganha quando dois se sobrepoem ("rate hikes" engole "hike")
    limpos, fim_anterior = [], -1
    for i, direcao, t in sorted(achados, key=lambda x: (x[0], -len(x[2]))):
        if i < fim_anterior:
            continue
        limpos.append((i, direcao, t))
        fim_anterior = i + len(t)
    return limpos


def classifica_frase(frase, ano_corrente):
    """Uma frase -> lista de achados {direcao, tipo, termo}. tipo: base | condicional.

    A ordem das travas: tempo verbal, depois condicao (com a excecao de continuidade), depois
    negacao e mercado. Cada descarte fica gravado, para o humano poder discordar.
    """
    t = (frase or "").lower().replace("’", "'").replace("‘", "'")
    anos = [int(a) for a in re.findall(r"\b(?:19|20)\d{2}\b", t)]
    if any(a < ano_corrente for a in anos) or any(p in t for p in VER_PASSADO):
        return [], "retrospectiva"                 # fala sobre o passado nao e guia do futuro

    pos = [t.find(c) for c in VER_CONDICAO if t.find(c) >= 0]
    tem_condicao = bool(pos)
    if not tem_condicao:
        base_seg, cond_seg, continuidade = t, "", False
    else:
        i = min(pos)
        clausula = re.split(r",| then ", t[i:])[0]
        continuidade = any(c in clausula for c in VER_CONTINUIDADE)
        if continuidade:
            # "se isto continuar, eu apoiaria MANTER" — o consequente e o cenario BASE
            resto = t[i + len(clausula):]
            base_seg, cond_seg = t[:i] + " " + resto, clausula
        else:
            base_seg, cond_seg = t[:i], t[i:]

    achados = []
    for seg, tipo in ((base_seg, "base"), (cond_seg, "condicional")):
        for i, direcao, termo in _acha_termos(seg):
            antes = seg[max(0, i - VER_JANELA_NEGACAO):i]
            if any(n in antes for n in VER_NEGACAO):
                achados.append({"direcao": None, "tipo": "negado", "termo": termo})
                continue
            antes_m = seg[max(0, i - VER_JANELA_MERCADO):i]
            if any(x in antes_m for x in VER_MERCADO):
                achados.append({"direcao": None, "tipo": "fala_do_mercado", "termo": termo})
                continue
            t_final = tipo
            if tipo == "base" and tem_condicao and not continuidade:
                antes_mod = seg[max(0, i - VER_JANELA_MODAL):i]
                if any(m in antes_mod for m in VER_MODAL):
                    t_final = "condicional"       # "would raise rates ... if ..."
            achados.append({"direcao": direcao, "tipo": t_final, "termo": termo})
    return achados, ("condicional" if tem_condicao and not continuidade else "direta")


def vereditos_da_moeda(moeda, itens, agora):
    """Quem manda no veredito e o leitor_falas.py — o construtor dedicado da prioridade 3.

    Ele le SUJEITO, NEGACAO, CONDICAO e TEMPO VERBAL com regra explicita, tem versao propria e
    ja sai com vota=false e selo. Aqui a gente so CONSOME. O classificador de reserva escrito
    neste arquivo (vereditos_por_orador) entra quando o modulo nao estiver disponivel, falhar
    ou nao tiver nada para aquela moeda — nunca ficamos sem veredito por causa de import.

    O import e PREGUICOSO e dentro de try: os dois arquivos sao editados em paralelo, e um
    erro de sintaxe la nao pode derrubar o nucleo aqui.
    """
    try:
        import leitor_falas                                            # noqa: WPS433
        bloco = leitor_falas.bloco_para_sentimento(moeda)
        v = bloco.get("veredito_por_orador") or []
        if v:
            return v, "leitor_falas.py — %s" % bloco.get("versao")
    except Exception as e:
        print("  ! leitor_falas indisponível (%s) — veredito pela reserva do sentimento.py" % e)
    return vereditos_por_orador(itens, agora), "reserva do sentimento.py (regra simples)"


def vereditos_por_orador(itens, agora):
    """Um veredito por ORADOR, com o trecho que o sustenta. Nao vota — e contexto de tela."""
    ano = agora.year
    por_orador = {}
    for x in itens:
        nome = (x.get("orador") or x.get("orador_identificado") or x.get("banco") or "?")
        alvo = por_orador.setdefault(nome, {"base": [], "cond": [], "descartes": [],
                                            "frases": 0, "item": x, "data": x.get("data"),
                                            "link": x.get("link")})
        if (x.get("data") or "") >= (alvo["data"] or ""):
            alvo["data"], alvo["link"], alvo["item"] = x.get("data"), x.get("link"), x
        for f in (x.get("frases") or []):
            txt = f.get("frase") or ""
            alvo["frases"] += 1
            achados, _forma = classifica_frase(txt, ano)
            for a in achados:
                if a["tipo"] in ("negado", "fala_do_mercado"):
                    alvo["descartes"].append((a["tipo"], a["termo"], txt))
                elif a["tipo"] == "base" and a["direcao"]:
                    alvo["base"].append((a["direcao"], a["termo"], txt))
                elif a["tipo"] == "condicional" and a["direcao"]:
                    alvo["cond"].append((a["direcao"], a["termo"], txt))

    saida = []
    for nome, d in por_orador.items():
        base_c = Counter(x[0] for x in d["base"])
        cond_c = Counter(x[0] for x in d["cond"])
        trecho, veredito, motivo = None, "indeterminado", None
        if base_c:
            top = base_c.most_common()
            if len(top) > 1 and top[0][1] == top[1][1]:
                veredito = "indeterminado"
                motivo = ("a fala tem %s no mesmo peso, sem cenário base único — empate não é "
                          "leitura" % " e ".join("%s (%d)" % (k, v) for k, v in top[:3]))
                trecho = d["base"][0][2]
            else:
                veredito = top[0][0]
                trecho = next(x[2] for x in d["base"] if x[0] == veredito)
                motivo = "cenário BASE de %s (\"%s\")" % (veredito, next(
                    x[1] for x in d["base"] if x[0] == veredito))
                if cond_c:
                    motivo += ("; além dele, %s cenário(s) CONDICIONAL(is) de %s, que não "
                               "mudam o caso base"
                               % (sum(cond_c.values()),
                                  " e ".join(sorted(set(cond_c.elements())))))
        elif cond_c:
            top = cond_c.most_common()
            if len(top) > 1 and top[0][1] == top[1][1]:
                veredito = "indeterminado"
                motivo = ("só cenários condicionais, e em direções opostas (%s)"
                          % ", ".join("%s %d" % (k, v) for k, v in top))
                trecho = d["cond"][0][2]
            else:
                dirc = top[0][0]
                veredito = ("%s condicional" % dirc) if dirc in ("alta", "corte") else dirc
                trecho = next(x[2] for x in d["cond"] if x[0] == dirc)
                motivo = ("só fala de %s DENTRO de condição (\"%s\") — sem condição satisfeita "
                          "não há direção" % (dirc, next(x[1] for x in d["cond"] if x[0] == dirc)))
        else:
            if d["frases"] == 0:
                motivo = ("o coletor não guardou nenhuma frase com postura deste discurso — "
                          "sem texto não há veredito, e contagem de marcador não substitui")
            else:
                motivo = ("%d frase(s) lida(s), nenhuma com verbo de alta, corte ou manutenção "
                          "que seja do próprio orador — a fala não diz o que fazer com o juro"
                          % d["frases"])
                trecho = ((d["item"].get("frases") or [{}])[0].get("frase"))
            if d["descartes"]:
                motivo += ("; %d termo(s) descartado(s) por negação ou por descrever o MERCADO"
                           % len(d["descartes"]))
        saida.append({"orador": nome, "veredito": veredito, "motivo": motivo,
                      "trecho": (trecho or "")[:400] or None,
                      "data": d["data"], "link": d["link"],
                      "frases_lidas": d["frases"],
                      "descartes": len(d["descartes"])})
    saida.sort(key=lambda x: (x.get("data") or ""), reverse=True)
    return saida


# ---------------------------------------------------------------------------------------
# DIMENSAO 2 — TEXTO (com origem, peso da fonte e contagem de duplicatas) — NAO VOTA MAIS
# ---------------------------------------------------------------------------------------
def origem_da_fala(item):
    """De onde veio a fala. Prefere o que o construtor de fontes gravou; se ele ainda nao
    gravar 'origem', deduz do tipo (speech = discurso oficial, statement = comunicado/ata)."""
    o = (item or {}).get("origem")
    if o in PESOS_DE_FALA:
        return o
    tipo = str((item or {}).get("tipo") or "").lower()
    if tipo in ("statement", "minutes", "comunicado", "ata"):
        return "comunicado_ata"
    return "discurso_oficial"


def por_que_a_fala_nao_vota():
    """A frase unica que explica o selo — usada na dimensao e no relatorio."""
    return ("a leitura de fala é CONTAGEM DE PALAVRAS, e contagem de palavras não lê negação, "
            "nem condição, nem referência temporal: 'holding the target' está na lista de "
            "termos hawkish, então Waller defendendo MANTER saía como alta. Desde 05/set a "
            "dimensão fica como CONTEXTO, com peso 0,0 — não entra na leitura contínua, "
            "não entra no "
            "teto e não conta como MANTEM. O veredito por orador ao lado lê condição e "
            "negação, mas TAMBÉM não vota: nunca foi medido contra rótulo humano.")


def dimensao_texto_buraco(moeda, origem, motivo, n_contexto=0):
    """Fala AUSENTE: buraco declarado, nunca zero e nunca None solto.

    ⚠️ CONSERTO DE 05/set: o CHF saía do arquivo com dimensoes.texto = null, e por tabela com
    fonte_texto = null e vota = null — a tela não tinha como distinguir "não perguntamos" de
    "perguntamos e não votou". Agora a dimensão existe sempre, com conectada=false e o motivo
    escrito. A qualidade da evidência continua tratando isso como parte SEM DADO (null), não
    como zero.
    """
    return {"direcao": None, "direcao_contexto": None,
            "vota": False, "selo": SELO_NAO_VOTA, "conectada": False,
            "hawkish": 0, "dovish": 0, "n": 0, "n_falas": 0, "n_contexto": int(n_contexto),
            "contagem_contexto": {"alta": 0, "corte": 0},
            "oradores": [], "datas": [], "origem": origem,
            "peso_aplicado": 0.0, "peso_da_fonte": None, "peso_se_votasse": 0.0,
            "itens_unicos": 0, "duplicatas_removidas": 0,
            "veredito_por_orador": [],
            "por_que_nao_vota": motivo,
            "nota": motivo, "nota_peso": motivo}


def dimensao_texto_manchetes(moeda, noticias, agora):
    """RESERVA para os bancos que bloqueiam robo: o que a imprensa trouxe nas ultimas 72 h.

    LEI DO DONO (05/set, manha): MANCHETE NAO VOTA. LEI DO DONO (05/set, tarde): FALA NENHUMA
    VOTA — nem discurso oficial, nem comunicado, nem imprensa com dirigente nomeado. Esta
    funcao ficou, entao, apenas com o trabalho de MOSTRAR o que a imprensa trouxe.

    Quem separa manchete de fala continua sendo o noticias.py, no bloco `voto` de cada moeda;
    a gente grava o que ele diria (peso_se_votasse, direcao_se_votasse) para o dia em que o
    classificador for validado, mas peso_aplicado e SEMPRE 0,0.

    ⚠️ O painel mostrava essas manchetes como se fossem "discursos" (o AUD aparecia com 38
    falas sem ter uma unica fala do RBA lida).
    """
    N = ((noticias or {}).get("moedas") or {}).get(moeda)
    if not N:
        return dimensao_texto_buraco(
            moeda, "nao_conectado",
            "nenhuma fonte de fala conectada para o %s: o banco bloqueia automação e não há "
            "nem manchete arquivada nesta rodada — buraco declarado, não zero" % moeda)
    ctx = N.get("contagem") or {}
    h_ctx, d_ctx = int(ctx.get("alta") or 0), int(ctx.get("corte") or 0)

    voto = N.get("voto") or {}
    origem = voto.get("origem") or "manchete"
    if origem not in PESOS_DE_FALA:
        origem = "manchete"
    peso_regua = PESOS_DE_FALA[origem]
    peso_se_votasse = min(float(voto.get("peso") if voto.get("peso") is not None else peso_regua),
                          peso_regua)

    cv = N.get("contagem_voto") or {}
    h_voto, d_voto = int(cv.get("alta") or 0), int(cv.get("corte") or 0)
    direcao_ctx = ("SOBE" if h_ctx > d_ctx else "CORTA" if d_ctx > h_ctx else
                   ("MANTEM" if (h_ctx or d_ctx) else None))

    itens = N.get("itens") or []
    if h_ctx == 0 and d_ctx == 0 and not itens:
        return dimensao_texto_buraco(
            moeda, "sem_fonte",
            "o %s não tem feed do banco e a imprensa não trouxe nada com marcador nesta "
            "janela — buraco declarado, não zero" % moeda,
            n_contexto=int(N.get("n_72h") or 0))
    if h_ctx == 0 and d_ctx == 0:
        return dimensao_texto_buraco(
            moeda, "sem_fonte",
            "o %s não tem feed do banco; a imprensa trouxe %d item(ns) na janela, nenhum com "
            "marcador de política monetária — contexto, não fala do banco"
            % (moeda, int(N.get("n_72h") or 0)),
            n_contexto=int(N.get("n_72h") or 0))

    unicos = N.get("n_unicos")
    dup = N.get("duplicatas_removidas")
    if unicos is None:
        vistos = set()
        for x in itens:
            vistos.add(chave_titulo(x.get("titulo")))
        unicos, dup = len(vistos), max(0, len(itens) - len(vistos))

    return {"direcao": None,                     # nao vota: nao emite direcao de voto
            "direcao_contexto": direcao_ctx,     # o que a contagem DIRIA, so para a tela
            "direcao_se_votasse": voto.get("direcao"),
            "vota": False, "selo": SELO_NAO_VOTA, "conectada": True,
            "hawkish": h_ctx, "dovish": d_ctx,
            # n = eventos UNICOS de imprensa. NAO e numero de falas do banco.
            "n": int(unicos or 0),
            "n_falas": int(voto.get("n_falas") or 0),
            "n_contexto": int(N.get("n_72h") or 0),
            "contagem_contexto": {"alta": h_ctx, "corte": d_ctx},
            "contagem_voto": {"alta": h_voto, "corte": d_voto},
            "oradores": (voto.get("oradores") or [x.get("fonte") for x in itens[:4]]),
            "datas": [str(x.get("quando_utc") or "")[:10] for x in itens[:6] if x.get("quando_utc")],
            "origem": origem,
            "peso_aplicado": 0.0,
            "peso_da_fonte": peso_regua,
            "peso_se_votasse": round(peso_se_votasse, 2),
            "itens_unicos": int(unicos or 0),
            "duplicatas_removidas": int(dup or 0),
            "rotulo_contexto": N.get("rotulo_contexto"),
            "veredito_por_orador": [],
            "por_que_nao_vota": por_que_a_fala_nao_vota(),
            "nota": "imprensa (Google News, 72 h) — o banco central bloqueia automação. É "
                    "contagem de expressão da imprensa, NÃO é fala do banco. Não vota desde "
                    "05/set, como nenhuma fala vota.",
            "nota_peso": "NÃO VOTA: os %d 'alta' e %d 'corte' são CONTEXTO da imprensa. Se a "
                         "régua antiga valesse, esta origem (%s) pesaria %.1f."
                         % (h_ctx, d_ctx, origem, peso_se_votasse)}


def dimensao_texto(moeda, discursos, agora, noticias=None):
    """Falas dos dirigentes desta moeda — CALCULADA E EXIBIDA, SEM VOTO desde 05/set.

    Onde o banco bloqueia robo (AUD, NZD, CHF), entra a reserva das manchetes; sem nada,
    o buraco declarado. Nunca None, nunca zero.
    """
    D = discursos or {}
    status = (D.get("status_fontes") or {}).get(moeda)
    itens = [x for x in D.get("itens", []) if (x.get("moeda") or "USD") == moeda]
    if moeda in SEM_FEED_PROPRIO or (status and str(status).startswith("not connected")):
        return dimensao_texto_manchetes(moeda, noticias, agora)
    if not itens and moeda != "USD" and not status:
        return dimensao_texto_manchetes(moeda, noticias, agora)
    inicio = (agora - dt.timedelta(days=JANELA_DIAS)).date().isoformat()
    itens = [x for x in itens if (x.get("data") or "") >= inicio]
    if not itens:
        return dimensao_texto_manchetes(moeda, noticias, agora)

    # duplicata: mesmo link ou mesmo titulo normalizado (o BoC publicou a MESMA cerimonia da
    # cedula de $20 em duas paginas, e as duas entravam como "fala de politica monetaria")
    vistos, unicos, dup = set(), [], 0
    for x in itens:
        k = x.get("link") or chave_titulo(x.get("titulo"))
        if k in vistos:
            dup += 1
            continue
        vistos.add(k)
        unicos.append(x)

    h = sum(int(x.get("marcadores_hawkish") or 0) for x in unicos)
    d = sum(int(x.get("marcadores_dovish") or 0) for x in unicos)
    vereditos, veredito_fonte = vereditos_da_moeda(moeda, unicos, agora)
    if h == 0 and d == 0 and not vereditos:
        return dimensao_texto_manchetes(moeda, noticias, agora)

    origens = Counter(origem_da_fala(x) for x in unicos)
    com_marca = [x for x in unicos
                 if int(x.get("marcadores_hawkish") or 0) or int(x.get("marcadores_dovish") or 0)]
    principal = max(com_marca, key=lambda x: int(x.get("marcadores_hawkish") or 0)
                    + int(x.get("marcadores_dovish") or 0)) if com_marca else unicos[0]
    origem = origem_da_fala(principal)
    direcao_ctx = "SOBE" if h > d else "CORTA" if d > h else "MANTEM"
    peso_regua = min(1.0, float(PESOS_DE_FALA.get(origem, 1.0)))
    # o veredito por orador, agregado: e o que a tela mostra no lugar de "8 hawkish"
    conta_ver = Counter(v["veredito"] for v in vereditos)
    return {"direcao": None,                      # NUNCA vota
            "direcao_contexto": direcao_ctx,      # o que a contagem de palavras DIRIA
            "vota": False, "selo": SELO_NAO_VOTA, "conectada": True,
            "hawkish": h, "dovish": d, "n": len(unicos),
            "n_falas": len(unicos), "n_contexto": 0,
            "oradores": [x.get("orador") for x in unicos][:6],
            "datas": [x.get("data") for x in unicos][:6],
            "origem": origem,
            "origens": dict(origens),
            "peso_aplicado": 0.0,
            "peso_da_fonte": PESOS_DE_FALA.get(origem, 1.0),
            "peso_se_votasse": peso_regua,
            "itens_unicos": len(unicos),
            "duplicatas_removidas": dup,
            "veredito_por_orador": vereditos,
            "veredito_resumo": dict(conta_ver),
            "veredito_fonte": veredito_fonte,
            "veredito_nota": "veredito por orador lê sujeito, negação, condição e tempo "
                             "verbal — e TAMBÉM não vota: nunca foi medido contra rótulo "
                             "humano nem contra a decisão seguinte do próprio banco.",
            "por_que_nao_vota": por_que_a_fala_nao_vota(),
            "nota": "contagem de expressões nos discursos e no comunicado — é um ponteiro, "
                    "não uma leitura, e desde 05/set não vota. O veredito por orador ao lado "
                    "lê negação, condição e tempo verbal, e também é contexto.",
            "nota_peso": "NÃO VOTA. Se a régua antiga valesse, esta origem (%s) pesaria %.1f "
                         "e a contagem diria %s (%d hawkish / %d dovish)."
                         % (origem, peso_regua, direcao_ctx, h, d)}


# ---------------------------------------------------------------------------------------
# DIMENSAO 3 — CICLO (decaimento continuo, no lugar do penhasco de 180 dias)
# ---------------------------------------------------------------------------------------
def reunioes_de_manutencao(b, agora):
    """Quantas reunioes ja aconteceram DEPOIS do ultimo movimento, sem mudar a taxa.

    ⚠️ data/bancos_centrais.json guarda a lista "reunioes" olhando PARA FRENTE — o passado nao
    esta la. Contamos so o que da para contar (as reunioes ja listadas que ja passaram) e
    declaramos que a contagem e PARCIAL, provavelmente subestimada. Quando a contagem sai
    zero, o decaimento fica valendo so pelo TEMPO, e isso vai dito na nota.
    """
    data = b.get("ultima_mudanca")
    lista = b.get("reunioes") or []
    hoje = agora.date()
    n = 0
    for d in lista:
        try:
            x = dt.date.fromisoformat(d)
        except Exception:
            continue
        if data and d > data and x <= hoje:
            n += 1
    return n, ("contagem PARCIAL: o arquivo só guarda as reuniões futuras, então só entram as "
               "que já passaram desde a última publicação — o número verdadeiro tende a ser maior")


def dimensao_ciclo(b, agora):
    """O ultimo movimento de juro, pesado por um DECAIMENTO CONTINUO.

    (6) Antes havia CICLO_VALIDADE_DIAS = 180, um penhasco: 179 dias valia 0,25 cheio e 181
    dias valia zero. O caso do dono: o AUD, com um movimento de 123 dias atras, entrava com o
    peso inteiro como se tivesse sido ontem. Agora:
        decaimento = 0,5^(idade/120 dias) x 0,5^(reunioes de manutencao/3)
    e abaixo de CICLO_PISO_VOTO (0,25) o movimento le como MANUTENCAO — nao vota ciclo.
    Os tres numeros sao PROVISORIOS.

    ⚠️ AUDITORIA 05/set — DUAS CORRECOES NO QUE ESTE BLOCO AFIRMAVA:

    1. O PENHASCO NAO ACABOU, MUDOU DE LUGAR. CICLO_PISO_VOTO e ele proprio um penhasco: com
       zero reunioes contadas, o decaimento cruza 0,25 aos 240 dias exatos, e a contribuicao
       cai de 0,063 para 0,000 de um dia para o outro. E 4x menor que o penhasco antigo (que
       derrubava 0,25 de uma vez), mas continua sendo um degrau. E o lugar do degrau importa:
       o GBP esta hoje com decaimento 0,220, 12% abaixo do piso; com piso 0,20 — tao arbitrario
       quanto 0,25 — a perna GBP passaria a votar CORTA e a conviccao do GBP cairia de 50%
       para 25%. O campo `penhasco` abaixo publica onde o degrau esta.

    2. A CONTAGEM DE REUNIOES NAO MEDE POLITICA MONETARIA, MEDE O ARQUIVO — TERMO DESLIGADO
       NA TARDE DE 05/set. Ela so enxerga as datas que o bancos_centrais.json ainda lista
       olhando para FRENTE e que ja passaram. Medido pela manha: NZD e CAD levavam 1 reuniao
       (fator 0,794) so porque a reuniao de 02/09/2026 ainda estava na lista; USD (ultimo
       movimento em 10/12/2025, 269 dias), GBP (17/12/2025, 262 dias) e CHF (19/06/2025, 443
       dias) levavam ZERO, embora tenham feito MUITO MAIS reunioes de manutencao que os dois
       primeiros. Ou seja: o termo penalizava quem a cadencia de atualizacao do arquivo por
       acaso denunciou, e premiava quem ela esqueceu. Isso e ruido de calendario vestido de
       sinal, e ruido com vies conhecido nao entra em leitura.

       O QUE FOI FEITO: o fator de reunioes saiu do decaimento (vale 1,0 fixo). O decaimento
       passa a ser SO pelo tempo, que e medido contra a data real do ultimo movimento e nao
       depende de o arquivo lembrar de nada. A contagem continua sendo feita e GRAVADA em
       `reunioes_de_manutencao_desde` — o contrato pede o campo e ele e informacao util —
       mas com `reunioes_no_decaimento: false` e o motivo ao lado, para ninguem achar que
       ela esta pesando.

       COMO RELIGAR DIREITO: bancos_centrais.py precisa guardar o HISTORICO de reunioes, nao
       so as futuras. Com o historico, a contagem passa a medir o banco e o termo volta —
       com meia-vida a calibrar pelo backtest, como todo o resto.
    """
    bp, data = b.get("ultima_mudanca_bp"), b.get("ultima_mudanca")
    try:
        idade = (agora.date() - dt.date.fromisoformat(data)).days
    except Exception:
        idade = None
    # onde o piso vira um degrau, com a contagem de reunioes que esta valendo
    idade_do_degrau = CICLO_MEIA_VIDA_DIAS * math.log(CICLO_PISO_VOTO, 0.5)
    base = {"bp": bp, "idade_dias": idade,
            "vota": True, "por_que_nao_vota": None,
            "meia_vida_dias": CICLO_MEIA_VIDA_DIAS,
            "meia_vida_reunioes": CICLO_MEIA_VIDA_REUNIOES,
            "meia_vida_reunioes_ligada": False,
            "piso_para_votar": CICLO_PISO_VOTO, "provisorio": True,
            "penhasco": {"idade_dias": round(idade_do_degrau),
                         "salto_no_score": round(0.25 * CICLO_PISO_VOTO, 3),
                         "texto": "o piso é um degrau, não uma curva: sem reunião contada, aos "
                                  "%d dias a contribuição cai de %.3f para 0,000 de um dia "
                                  "para o outro. O penhasco de 180 dias não sumiu, mudou de "
                                  "lugar e ficou 4x menor. Número PROVISÓRIO."
                                  % (round(idade_do_degrau), 0.25 * CICLO_PISO_VOTO)},
            "reunioes_medem_o_arquivo_nao_o_banco": True,
            "reunioes_no_decaimento": False}
    if bp is None or idade is None:
        # silencio nao e voto: sem ultimo movimento no arquivo, a dimensao NAO vota — ela
        # baixa o teto da moeda em vez de entrar como MANTEM.
        return dict(base, direcao="MANTEM", vota=False, decaimento=0.0,
                    reunioes_de_manutencao_desde=0,
                    por_que_nao_vota="sem último movimento de juro no arquivo: não há ciclo "
                                     "para ler — buraco declarado, não MANTEM",
                    nota="sem último movimento no arquivo")

    n_reu, nota_reu = reunioes_de_manutencao(b, agora)
    dec_tempo = 0.5 ** (idade / CICLO_MEIA_VIDA_DIAS)
    # O fator de reunioes esta DESLIGADO desde 05/set (vale 1,0): ele media a cadencia de
    # atualizacao do arquivo, nao a politica do banco. Ver o docstring, item 2.
    dec_reu_se_valesse = round(0.5 ** (n_reu / CICLO_MEIA_VIDA_REUNIOES), 3)
    dec = round(dec_tempo, 3)
    base.update({"decaimento": dec, "decaimento_por_tempo": round(dec_tempo, 3),
                 "decaimento_por_reunioes": 1.0,
                 "decaimento_por_reunioes_se_valesse": dec_reu_se_valesse,
                 "reunioes_no_decaimento": False,
                 "reunioes_de_manutencao_desde": n_reu,
                 "nota_reunioes": nota_reu})
    base["nota_reunioes"] = (
        "a contagem é GRAVADA mas NÃO entra no decaimento (desde 05/set): ela só enxerga as "
        "reuniões que o arquivo ainda listava olhando para frente e que já passaram, então "
        "media a cadência do arquivo e não a do banco — punia quem o arquivo denunciou e "
        "premiava quem ele esqueceu. Contadas aqui: %d (se pesasse, o fator seria %.3f). O "
        "decaimento usa SÓ o tempo. Para religar o termo, bancos_centrais.py precisa guardar "
        "o histórico de reuniões, não só as futuras." % (n_reu, dec_reu_se_valesse))
    if dec < CICLO_PISO_VOTO:
        return dict(base, direcao="MANTEM",
                    nota="último movimento %+d pb há %d dias; decaimento %.2f abaixo do piso "
                         "%.2f — lê como manutenção" % (bp, idade, dec, CICLO_PISO_VOTO))
    return dict(base, direcao="SOBE" if bp > 0 else "CORTA",
                nota="último movimento %+d pb há %d dias, %d reunião(ões) de manutenção depois; "
                     "vale %.0f%% do peso cheio" % (bp, idade, n_reu, dec * 100))


# ---------------------------------------------------------------------------------------
# DIMENSAO 4 — GEOPOLITICA: EXPERIMENTAL, NAO VOTA (05/set/2026)
# ---------------------------------------------------------------------------------------
def dimensao_geo(moeda, geo):
    """O noticiario, calculado e EXIBIDO — mas sem voto desde 05/set/2026.

    A regra foi declarada em 04/set e nunca medida. Fica com selo "experimental" e
    "vota": false: nao entra no score nem no teto. A hipotese a medir continua registrada:
    pico de conflito z>=2 muda o retorno de 20 dias das moedas de risco?

    ⚠️ CONSERTO DE 06/set: quando a coleta do GDELT falha para uma moeda (o USD levou 429
    nesta rodada), a dimensao saia do arquivo como `null` cru — o mesmo buraco que o CHF
    tinha na dimensao de fala ate 05/set, e que a tela nao consegue distinguir de "nao
    perguntamos". Agora ela existe sempre, com conectada=false e o motivo escrito.
    """
    G = (geo or {}).get("moedas", {}).get(moeda)
    if not G:
        return {"z_energia": None, "z_conflito": None, "tom": None, "corte_z": GEO_Z_CORTE,
                "manchete": None, "vota": False, "selo": "experimental",
                "conectada": False, "direcao": None, "estado": "não conectada",
                "leitura_se_votasse": None,
                "motivo": "a coleta do GDELT não trouxe esta moeda nesta rodada — buraco "
                          "declarado, não é ausência de notícia",
                "nota": "dimensão sem fonte nesta rodada. Não vota (nunca votou desde "
                        "05/set) e não entra no teto: o que falta aqui é o DADO, não o voto."}
    t = G.get("temas") or {}
    ze = ((t.get("energia") or {}).get("volume") or {}).get("z")
    zc = ((t.get("conflito") or {}).get("volume") or {}).get("z")
    base = {"z_energia": ze, "z_conflito": zc, "tom": G.get("tom"), "corte_z": GEO_Z_CORTE,
            "manchete": (((t.get("conflito") or {}).get("manchetes") or [{}])[0].get("titulo")),
            "vota": False, "selo": "experimental", "conectada": True,
            "nota": "regra declarada sobre intensidade de notícia (GDELT). Contava desde "
                    "04/set; em 05/set o dono retirou o voto: regra nunca medida, e estava "
                    "mexendo em leitura de verdade. Fica visível, fora da leitura contínua e "
                    "fora do teto."}
    if ze is not None and ze >= GEO_Z_CORTE:
        if moeda in EXPORTADOR_ENERGIA:
            return dict(base, direcao=None, estado="quieta", leitura_se_votasse=None,
                        motivo="pico de energia, mas o %s EXPORTA energia — ambíguo para o juro" % moeda)
        return dict(base, direcao=None, estado="pico", leitura_se_votasse="SOBE",
                    motivo="pico de energia (z %+.1f): empurrão de inflação para importador — "
                           "exibido, não votado" % ze)
    if zc is not None and zc >= GEO_Z_CORTE:
        return dict(base, direcao=None, estado="pico", leitura_se_votasse="CORTA",
                    motivo="pico de conflito (z %+.1f) sem pico de energia: risco de "
                           "crescimento — exibido, não votado" % zc)
    return dict(base, direcao=None, estado="quieta", leitura_se_votasse=None,
                motivo="sem pico de notícia nesta semana")


# ---------------------------------------------------------------------------------------
# QUALIDADE DA EVIDENCIA — 0 a 100, quatro partes de 25
# ---------------------------------------------------------------------------------------
def qualidade_evidencia(dd, tt, moeda):
    """Quatro partes na regua, TRES ligadas hoje, cada uma medida 0..100. A nota e a MEDIA
    das partes QUE TEM DADO — nunca uma soma de fatias fixas de 25.

    quantidade      quantas divulgacoes e falas QUE VOTAM entraram na janela
    diversidade     quantas familias independentes (inflacao, emprego, atividade, comunicacao)
    atualidade      idade do item que MAIS PESA, com a mesma meia-vida de 21 dias dos dados
    confiabilidade  peso da fonte de fala: discurso oficial e comunicado valem cheio, imprensa
                    com fala de dirigente nomeado vale 0,4, MANCHETE VALE ZERO

    ⚠️ DOIS CONSERTOS DA AUDITORIA DE 05/set — os dois sao a MESMA lei do dono ("silencio nao
    e voto: dimensao sem dado nao conta, nunca vira zero"), que a versao anterior quebrava:

    1. PARTE SEM DADO SAI null E NAO ENTRA NA MEDIA. Antes o CHF, que nao tem feed do SNB e
       portanto nao tem dimensao de fala nenhuma, levava confiabilidade = 0 e a nota era
       dividida por 4 assim mesmo: (67+75+94+0)/4 = 59. O buraco declarado custava 25 pontos.
       Agora a parte sai null, a media e sobre as 3 que existem — (67+75+94)/3 = 79 — e o
       JSON diz quantas partes entraram. Confiabilidade ZERO continua existindo quando HA
       fonte e a regua diz que ela vale zero (manchete): isso e medida, nao buraco.

    2. O QUE NAO VOTA NAO E EVIDENCIA. Antes `n_falas` era `tt["n"]`, o numero de itens de
       IMPRENSA da moeda, e "comunicacao" entrava na diversidade so por existir esse bloco.
       Resultado medido em 05/set: o NZD saia com quantidade 100/100 e diversidade 25/100
       tendo ZERO divulgacoes e ZERO falas na janela — 42 manchetes que o proprio
       noticias.py marca `vota: false` enchiam a nota. Agora so conta fala que VOTA; o resto
       vai para `contexto_nao_contado`, visivel e fora da conta.
    """
    vota_fala = bool((tt or {}).get("vota"))
    n_dados = int((dd or {}).get("n") or 0)
    if vota_fala:
        nf = tt.get("n_falas")
        n_falas = int(nf if nf is not None else (tt.get("n") or 0))
    else:
        n_falas = 0
    n_contexto = int((tt or {}).get("n") or 0) if (tt and not vota_fala) else 0
    quantidade = min(100, round(100.0 * (n_dados + n_falas) / QUALIDADE_N_SATURA))

    fams = set((dd or {}).get("familias_independentes") or [])
    if vota_fala:
        fams.add("comunicacao")
    diversidade = round(100.0 * len(fams) / len(FAMILIAS_INDEPENDENTES))

    principais = (dd or {}).get("principais") or []
    if principais:
        idade = float(principais[0].get("idade_dias") or 0.0)
    elif vota_fala and (tt.get("datas") or []):
        idade = 0.0
        try:
            d0 = max(x for x in tt["datas"] if x)
            idade = max(0.0, (dt.date.today() - dt.date.fromisoformat(d0)).days)
        except Exception:
            idade = 0.0
    else:
        idade = None
    # sem nada com peso na janela nao existe "idade do que mais pesa": a parte fica sem dado.
    atualidade = round(100.0 * (0.5 ** (idade / MEIA_VIDA))) if idade is not None else None

    # ⚠️ 05/set (tarde) — A CONFIABILIDADE DA FALA SAIU DA CONTA, PARA TODAS AS MOEDAS.
    # A parte "confiabilidade" media o peso da FONTE DE FALA. Desde que a fala parou de votar,
    # ela nao e mais evidencia que entra na leitura — e vale aqui a mesma lei que ja tirou a
    # manchete: O QUE NAO VOTA NAO E EVIDENCIA. Deixa-la valendo daria confiabilidade 100 ao
    # USD por um discurso que nao entra em lugar nenhum do score, inflando a nota.
    # A parte sai NULL (sem dado, nao zero) e a media passa a ser sobre 3 partes. O que a
    # regua antiga daria fica gravado ao lado, para auditoria.
    confiabilidade = None
    conf_se_votasse = (round(100.0 * (PESOS_DE_FALA.get((tt or {}).get("origem")) or 0.0))
                       if tt and tt.get("conectada") else None)

    comp = {"quantidade": int(quantidade), "diversidade": int(diversidade),
            "atualidade": None if atualidade is None else int(atualidade),
            "confiabilidade": None if confiabilidade is None else int(confiabilidade)}
    usadas = [v for v in comp.values() if v is not None]
    sem_dado = sorted(k for k, v in comp.items() if v is None)
    nota = int(round(sum(usadas) / float(len(usadas)))) if usadas else None

    # ---- TETO PELA DOMINANCIA (08/set) — a concentracao vira CONFIANCA, nao valor --------
    # Quando UM item responde por mais da metade da massa da dimensao de dados, a nota nao pode
    # ser maior que a fatia que NAO e desse item: se 76% da dimensao e uma divulgacao so, no
    # maximo 24% da evidencia e de CONJUNTO. Usa a MESMA medida do alerta que ja existia
    # (participacao do maior item), sem numero novo, e so morde acima do corte de 50%.
    # PROVISORIO como todo o resto. A DIRECAO nao e tocada aqui, em nenhuma hipotese.
    dom = (dd or {}).get("dominancia") or {}
    nota_antes_dom, teto_dom, limitada = nota, None, False
    if dom.get("alerta") and nota is not None:
        teto_dom = int(100 - int(dom.get("share_pct") or 0))
        if nota > teto_dom:
            nota, limitada = teto_dom, True

    partes = []
    partes.append("%d divulgações e %d fala(s) que votam na janela" % (n_dados, n_falas))
    if n_contexto:
        partes.append("%d item(ns) de imprensa que NÃO votam ficaram de fora da conta"
                      % n_contexto)
    partes.append("%d de %d famílias independentes (%s)"
                  % (len(fams), len(FAMILIAS_INDEPENDENTES), ", ".join(sorted(fams)) or "nenhuma"))
    if idade is None:
        partes.append("nada com peso na janela — a parte atualidade sai sem dado, não zero")
    else:
        partes.append("o item que mais pesa tem %.0f dia(s)" % idade)
    if tt and tt.get("conectada"):
        rot = {"discurso_oficial": "discurso oficial", "comunicado_ata": "comunicado/ata",
               "imprensa_com_fala": "imprensa com fala de dirigente nomeado",
               "manchete": "MANCHETE de imprensa"}
        partes.append("fonte da fala: %s — mas a fala NÃO VOTA desde 05/set, então a parte "
                      "confiabilidade sai SEM DADO em vez de valer %s/100"
                      % (rot.get(tt.get("origem"), tt.get("origem") or "?"),
                         "—" if conf_se_votasse is None else conf_se_votasse))
    else:
        partes.append("nenhuma fala conectada — a parte confiabilidade sai sem dado, não zero")
    if limitada:
        partes.append("⚠️ uma única divulgação responde por %d%% da dimensão de dados (%s): a "
                      "nota cai de %d para %d, o teto da concentração — a DIREÇÃO não muda por "
                      "isso" % (int(dom.get("share_pct") or 0), dom.get("item") or "?",
                                nota_antes_dom, nota))
    return {"nota": nota, "componentes": comp,
            "confiabilidade_da_fala_se_votasse": conf_se_votasse,
            "partes_usadas": len(usadas), "partes_sem_dado": sem_dado,
            "contexto_nao_contado": n_contexto,
            # ---- o que a dominância fez com a nota, sempre gravado ----------------------
            "nota_antes_da_dominancia": nota_antes_dom,
            "limitada_pela_dominancia": bool(limitada),
            "teto_pela_dominancia": teto_dom,
            "dominancia_share_pct": (dom.get("share_pct") if dom.get("alerta") else None),
            "explicacao": "qualidade %s/100 do %s (média de %d parte(s) com dado%s) — %s."
                          % ("—" if nota is None else nota, moeda, len(usadas),
                             "; sem dado em " + ", ".join(sem_dado) if sem_dado else "",
                             "; ".join(partes)),
            "provisorio": True,
            "regua": {"satura_em_itens": QUALIDADE_N_SATURA, "meia_vida_dias": MEIA_VIDA,
                      "pesos_de_fala": PESOS_DE_FALA,
                      "parte_sem_dado": "sai null e NÃO entra na média — dimensão sem dado "
                                        "baixa o denominador, nunca conta como zero",
                      "teto_pela_dominancia": {
                          "corte_pct": DOMINANCIA["corte_participacao_pct"],
                          "regra": "quando o maior item passa de %d%% da massa da dimensão de "
                                   "dados, a nota fica limitada a (100 - participação)"
                                   % DOMINANCIA["corte_participacao_pct"],
                          "por_que": DOMINANCIA["por_que_o_teto_e_100_menos_a_participacao"],
                          "nao_toca_a_direcao": True,
                          "desde": "2026-09-08", "provisorio": True},
                      "so_conta_quem_vota": "item de imprensa que não vota é contexto e não "
                                            "entra em quantidade, diversidade nem atualidade",
                      "confiabilidade_desligada_em": "2026-09-05",
                      "confiabilidade_por_que": "a parte media o peso da FONTE DE FALA, e a "
                                                "fala parou de votar. O que não vota não é "
                                                "evidência: a parte sai null para as oito "
                                                "moedas e a nota passa a ser a média de 3 "
                                                "partes. O valor que a régua antiga daria "
                                                "fica em confiabilidade_da_fala_se_votasse. "
                                                "Religa junto com o voto da fala, quando o "
                                                "classificador for validado."}}


def brt(iso):
    """UTC -> BRT (UTC-3, sem horario de verao desde 2019). O dono lê BRT primeiro."""
    try:
        q = dt.datetime.fromisoformat(str(iso))
    except Exception:
        return None
    if q.tzinfo is None:
        q = q.replace(tzinfo=dt.timezone.utc)
    return q.astimezone(dt.timezone(dt.timedelta(hours=-3)))


def texto_atraso(minutos):
    """Atraso em português, do jeito que o dono escreveu: '4h', '35 min', '1h 20min'."""
    if minutos is None:
        return "sem medida"
    minutos = int(round(minutos))
    if minutos < 60:
        return "%d min" % minutos
    h, mi = divmod(minutos, 60)
    return "%dh" % h if mi == 0 else "%dh %dmin" % (h, mi)


def proximo_evento_relevante(moeda, futuros, agora):
    """(C) O proximo DADO que pode derrubar a tese — nao a proxima DECISAO.

    O dono, na revisao de 05/set: "a proxima reuniao nao e o risco mais proximo: antes do RBA
    podem vir CPI, emprego, salarios ou PIB". O evento relevante diz ate quando vale procurar
    BO + ZOI; a reuniao continua sendo o limite FINAL do ciclo, e sai no campo `proxima`.

    Regra: o primeiro evento FUTURO, ainda nao divulgado, daquela moeda, cuja familia esteja
    na lista das seis categorias do dono (CPI, emprego, salarios, PIB, varejo, PMI). Prefere
    impacto HIGH; so cai para MEDIUM quando nao houver nenhum HIGH no horizonte, e nesse caso
    grava "reserva": true. Sem nada no horizonte, devolve None com o horizonte declarado —
    "null por horizonte curto" e diferente de "null porque nao ha evento".
    """
    cands = []
    for e in futuros:
        if e.get("moeda") != moeda:
            continue
        nome, _fam = familia_de(e.get("titulo"))
        if nome not in FAMILIAS_RELEVANTES:
            continue
        imp = str(e.get("impacto") or "").upper()
        if imp not in ("HIGH", "MEDIUM"):
            continue
        cands.append((0 if imp == "HIGH" else 1, e.get("quando_utc"), nome, imp, e))
    if not cands:
        return None
    tem_alto = any(c[0] == 0 for c in cands)
    cands = [c for c in cands if c[0] == 0] if tem_alto else cands
    cands.sort(key=lambda c: c[1] or "")
    _p, quando, nome, imp, e = cands[0]
    q = brt(quando)
    try:
        delta = dt.datetime.fromisoformat(quando) - agora
        horas_total = int(delta.total_seconds() // 3600)
        dias, horas = divmod(max(0, horas_total), 24)
    except Exception:
        horas_total, dias, horas = None, None, None
    rotulo = rotulo_do_evento(e.get("titulo"), nome)
    return {
        "titulo": rotulo,
        "titulo_original": e.get("titulo"),
        "familia": nome,
        "quando_utc": quando,
        "quando_brt": q.strftime("%d/%m %H:%M") if q else None,
        "impacto": imp,
        "dias": dias, "horas": horas, "horas_total": horas_total,
        "reserva": not tem_alto,
        "texto": "%s em %s (BRT)%s" % (rotulo,
                                       q.strftime("%d/%m às %H:%M") if q else "?",
                                       "" if tem_alto else " — impacto médio: não há nenhum "
                                                           "evento de impacto alto no horizonte"),
        "nota": "é o próximo DADO relevante, não a próxima decisão: ele diz até quando vale "
                "procurar BO + ZOI. A reunião continua no campo `proxima`, como limite final "
                "do ciclo.",
    }


def regime_do_banco(cc, dd, b):
    """(C) O que o banco ESTA fazendo: alta, manutencao ou corte.

    Vem do CICLO — o ultimo movimento de juro enquanto ele ainda pesa (decaimento acima do
    piso). Quando o ciclo nao tem dado nenhum, cai para a leitura de DADOS, e isso vai dito no
    motivo. Nao e previsao: previsao e a leitura.
    """
    if cc and cc.get("vota") is not False and cc.get("direcao") in ("SOBE", "CORTA"):
        reg = "alta" if cc["direcao"] == "SOBE" else "corte"
        return reg, ("último movimento de %+d pb há %d dias, ainda pesando (%.0f%% do peso "
                     "cheio)" % (cc.get("bp") or 0, cc.get("idade_dias") or 0,
                                 (cc.get("decaimento") or 0.0) * 100))
    if cc and cc.get("bp") is not None:
        return "manutencao", ("o último movimento (%+d pb, há %d dias) já não pesa: o banco "
                              "está parado" % (cc.get("bp") or 0, cc.get("idade_dias") or 0))
    dirs = {"SOBE": "alta", "CORTA": "corte"}
    if dd and dd.get("vota") and dd.get("direcao") in dirs:
        return dirs[dd["direcao"]], ("sem último movimento no arquivo; o regime foi inferido "
                                     "do fluxo de dados, não do que o banco fez")
    return "manutencao", "sem movimento de juro no arquivo e sem fluxo de dados que incline"


def rotulo_de_evidencia(nota):
    """(C) fraca <40 · moderada 40-69 · forte >=70. Faixas PROVISORIAS."""
    if nota is None:
        return None
    for nome in ("fraca", "moderada", "forte"):
        lo, hi = FAIXAS_EVIDENCIA_PROVISORIAS[nome]
        if lo <= nota <= hi:
            return nome
    return "forte"


def zona_de_leitura(score, n_votando, direcao, dimensoes_discordam=None):
    """(B) ZONA "SEM LEITURA" POR MOEDA — regra provisoria do dono (05/set).

    sem_leitura quando (|score| / teto TEORICO) x 100 < 15 OU quando menos de 2 dimensoes
    votam. Devolve (leitura, leitura_texto, motivo, intensidade_pct).

    `dimensoes_discordam` diz se as dimensoes que votam apontam para lados DIFERENTES. Sem
    este parametro a frase "as dimensoes que votam discordam entre si" era escrita sempre que
    a direcao agregada fosse MANTEM — e MANTEM tambem e o que sai quando as duas dimensoes
    CONCORDAM em manutencao. Em 05/set duas das oito moedas (GBP e CAD) saiam com
    "2 de 2 dimensoes concordam" ao lado de "as dimensoes que votam discordam entre si", na
    mesma tela. Quando o parametro nao vem, o comportamento antigo e preservado.
    """
    if dimensoes_discordam is None:
        dimensoes_discordam = (direcao == "MANTEM")
    intensidade = round(abs(score) / TETO_MOEDA * 100) if TETO_MOEDA else 0
    minimo = FAIXAS_LEITURA_PROVISORIAS["intensidade_minima_pct"]
    n_min = FAIXAS_LEITURA_PROVISORIAS["dimensoes_minimas_votando"]
    motivos = []
    if n_votando < n_min:
        motivos.append("só %d de %d dimensões votam (a régua pede pelo menos %d)"
                       % (n_votando, len(DIMENSOES_QUE_VOTAM), n_min))
    if intensidade < minimo:
        # ⚠️ lei do dono (b): este texto VAI PARA A TELA (é o motivo exibido na moeda sem
        # leitura). Nada de número da escala do score aqui — nem o teto. Só a intensidade
        # relativa, que é percentual e não revela o número.
        motivos.append("intensidade relativa %d%% abaixo do mínimo provisório de %d%% "
                       "(a leitura está perto demais de zero para virar direção)"
                       % (intensidade, minimo))
    if motivos:
        return ("sem_leitura", "sem leitura",
                "sem leitura: " + " e ".join(motivos) + ". A moeda continua no arquivo, com "
                "tudo o que foi medido — o que não existe é a DIREÇÃO.", intensidade)
    if score > 0:
        return ("inclinado_alta", "inclinado à alta",
                "inclinado à alta: intensidade relativa %d%% do teto, com %d de %d dimensões "
                "votando%s" % (intensidade, n_votando, len(DIMENSOES_QUE_VOTAM),
                               "; as dimensões que votam discordam entre si, então a direção "
                               "vem da MAGNITUDE, não da contagem de votos"
                               if dimensoes_discordam else ""), intensidade)
    return ("inclinado_corte", "inclinado ao corte",
            "inclinado ao corte: intensidade relativa %d%% do teto, com %d de %d dimensões "
            "votando%s" % (intensidade, n_votando, len(DIMENSOES_QUE_VOTAM),
                           "; as dimensões que votam discordam entre si, então a direção vem "
                           "da MAGNITUDE, não da contagem de votos"
                           if dimensoes_discordam else ""), intensidade)


# ---------------------------------------------------------------------------------------
# LEITURA POR MOEDA
# ---------------------------------------------------------------------------------------
def le_moeda(m, ev, bancos, discursos, agora, geo=None, noticias=None, futuros=None):
    b = (bancos or {}).get("bancos", {}).get(m, {})
    dims = {
        "dados": dimensao_dados(ev, m, agora),
        "texto": dimensao_texto(m, discursos, agora, noticias),
        "ciclo": dimensao_ciclo(b, agora),
        "geo": dimensao_geo(m, geo),
    }
    # VOTAM: dados e ciclo, quando ligadas, com direcao e com "vota" verdadeiro. A fala saiu
    # do voto em 05/set (tarde) e a geopolitica em 05/set (manha) — as duas continuam
    # calculadas e exibidas, com selo, fora do score e fora do teto.
    votantes = DIMENSOES_QUE_VOTAM
    disponiveis = {k: v for k, v in dims.items()
                   if k in votantes and v and v.get("direcao") and v.get("vota") is not False}
    votos = Counter(v["direcao"] for v in disponiveis.values())
    if not votos:
        direcao, concordam = "MANTEM", 0
    else:
        top = votos.most_common()
        if len(top) > 1 and top[0][1] == top[1][1]:
            direcao = "MANTEM"                    # empate nao e leitura
            concordam = votos.get("MANTEM", 0)
        else:
            direcao, concordam = top[0]
    conv = PESO_DIM * concordam
    teto = PESO_DIM * len(disponiveis)
    intensidade = 0 if direcao == "MANTEM" else (1 if conv <= 25 else 2 if conv <= 50 else 3)
    # SCORE CONTINUO, -1 a +1 — e o que o par usa. Cada dimensao que VOTA vale ate +-0,25, e
    # entra com a MAGNITUDE que tem, nao so com o voto:
    #   dados   soma decaida (CRUA — a winsorizacao foi revogada em 08/set), comprimida por
    #           tanh, que e monotona e impar: ela satura a MAGNITUDE da parcela sem nunca
    #           mudar o SINAL dela. E saturacao do AGREGADO, nao corte de termo.
    #   ciclo   +-0,25 x DECAIMENTO (tempo)
    #   texto   0,000 sempre — nao vota desde 05/set (o que ela diria fica em texto_se_votasse)
    #   geo     0,000 sempre — nao vota desde 05/set
    # ⚠️ A palavra "score" e o numero NAO VAO PARA A TELA (lei do dono): a interface mostra
    # leitura_texto, concordancia_texto e evidencia_rotulo. O numero fica no arquivo porque o
    # par e o instrumento precisam dele para a diferenca entre as pernas.
    comp = {}
    dd = dims["dados"]
    comp["dados"] = (0.25 * math.tanh(dd["soma"] / (2.0 * LIMIAR_DADOS))
                     if dd and dd.get("vota") else 0.0)
    # a MESMA conta com a soma CRUA — é a referência da guarda de direção (lei de 08/set).
    # Hoje as duas são idênticas, porque não há tratamento; o par de números existe para que
    # isso possa ser CONFERIDO no arquivo, e não acreditado.
    comp_dados_cru = (0.25 * math.tanh(dd["soma_crua"] / (2.0 * LIMIAR_DADOS))
                      if dd and dd.get("vota") else 0.0)
    tt = dims["texto"]
    comp["texto"] = 0.0
    cc = dims["ciclo"]
    if cc and cc.get("vota") is not False and cc.get("direcao") in ("SOBE", "CORTA"):
        comp["ciclo"] = 0.25 * (1 if cc["direcao"] == "SOBE" else -1) * float(cc.get("decaimento") or 0.0)
    else:
        comp["ciclo"] = 0.0
    comp["geo"] = 0.0
    comp = {k: round(v, 3) for k, v in comp.items()}
    # o que a fala CONTRIBUIRIA se a contagem de palavras votasse — so para auditoria
    if tt and (tt.get("hawkish") or tt.get("dovish")):
        texto_se_votasse = round(0.25 * (tt["hawkish"] - tt["dovish"])
                                 / (tt["hawkish"] + tt["dovish"] + 2.0)
                                 * float(tt.get("peso_se_votasse") or 0.0), 3)
    else:
        texto_se_votasse = 0.0
    score = round(sum(comp.values()), 3)
    score_cru = round(comp_dados_cru + comp["ciclo"] + comp["texto"] + comp["geo"], 3)

    qual = qualidade_evidencia(dd, tt, m)
    fams = set((dd or {}).get("familias_independentes") or [])
    # "comunicacao" so entra quando a fala VOTA — e ela nao vota mais.

    dom = dict((dd or {}).get("dominancia") or
               {"alerta": False, "item": None, "share_pct": 0, "texto": None})

    discordam = len({v["direcao"] for v in disponiveis.values()}) > 1
    leitura, leitura_txt, leitura_motivo, intens_rel = zona_de_leitura(
        score, len(disponiveis), direcao, dimensoes_discordam=discordam)

    # ---- GUARDA DE DIREÇÃO (lei estrutural de 08/set) -----------------------------------
    # A MESMA leitura, refeita com a soma CRUA. Se o tratamento mudar a leitura em relação ao
    # cru, isso não passa em silêncio: sai bandeira, sai texto, e a moeda vai para SEM LEITURA
    # até alguém decidir qual das duas vale — porque leitura cuja direção depende do tratamento
    # não é leitura, é escolha de método. Hoje o tratamento é "nenhum" e a guarda nunca dispara;
    # ela existe para que a família inteira do erro da winsorização não possa voltar calada.
    leitura_crua, _lc_txt, _lc_mot, intens_crua = zona_de_leitura(
        score_cru, len(disponiveis), direcao, dimensoes_discordam=discordam)
    guarda_leitura = guarda_de_direcao("a leitura do %s" % m, leitura_crua, leitura,
                                       TRATAMENTO_DA_SOMA)
    # ⚠️ BURACO FECHADO EM 08/set (auditoria do refutador): a suspensão olhava SÓ para a
    # leitura da moeda. Mas o tratamento pode virar a direção da DIMENSÃO DE DADOS sem virar a
    # leitura — basta o ciclo carregar o sinal. Medido em moeda sintética: soma crua +6,00
    # (SOBE) e soma tratada -6,00 (CORTA), com o ciclo em alta recente, saía com
    # `direcao_mudou_pelo_tratamento: true`, leitura publicada "inclinado à alta" e
    # "1 de 2 dimensões concordam" — a direção da dimensão publicada era a do MÉTODO e a moeda
    # continuava de pé. A lei escrita aqui e no §4 do método diz SUSPENDE, então suspende nos
    # dois níveis. Hoje o gatilho é código morto (o tratamento é "nenhum" e a soma tratada é
    # igual à crua nas oito moedas): a mudança não altera nenhum número publicado, ela fecha o
    # caminho para o dia em que alguém puser um tratamento de volta.
    virou_na_dimensao = bool((dd or {}).get("direcao_mudou_pelo_tratamento"))
    if guarda_leitura["virou"] or virou_na_dimensao:
        onde = ("a leitura da moeda" if guarda_leitura["virou"]
                else "a direção da dimensão de dados")
        de_para = ((leitura_crua, guarda_leitura["para"]) if guarda_leitura["virou"]
                   else ((dd or {}).get("direcao_crua"), (dd or {}).get("direcao")))
        leitura, leitura_txt = "sem_leitura", "sem leitura"
        leitura_motivo = ("sem leitura: o tratamento '%s' mudaria %s de '%s' para '%s'. "
                          "Leitura cuja direção depende do tratamento não é leitura — a moeda "
                          "fica suspensa até alguém decidir qual das duas vale. Tudo o que foi "
                          "medido continua no arquivo."
                          % (TRATAMENTO_DA_SOMA, onde, de_para[0], de_para[1]))

    # ---- AS BANDEIRAS DA MOEDA — o painel nunca esconde ---------------------------------
    bandeiras = []
    # A FAIXA NEUTRA mexeu na direcao desta perna? Ela continua ligada (tem tese), mas nao
    # passa calada — e a mesma lei que a winsorizacao produziu: tratamento que mexe na
    # direcao APARECE.
    _fx = (dd or {}).get("faixa_neutra") or {}
    if _fx.get("direcao_depende_da_faixa"):
        bandeiras.append({
            "tipo": "faixa_neutra",
            "muda_a_direcao": True,
            "soma_publicada": (dd or {}).get("soma"),
            "soma_sem_faixa": _fx.get("soma_sem_faixa"),
            "direcao_sem_faixa": _fx.get("direcao_sem_faixa"),
            "itens_zerados": _fx.get("itens_zerados"),
            "efeito": "a direção da dimensão de dados depende da largura da faixa neutra, que "
                      "é PROVISÓRIA e nunca foi validada contra o que o banco central fez "
                      "depois",
            "texto": _fx.get("texto")})
    if dom.get("alerta"):
        bandeiras.append({
            "tipo": "dominancia", "share_pct": dom.get("share_pct"),
            "corte_pct": dom.get("corte_pct"), "item": dom.get("item"),
            "muda_a_direcao": False,
            "efeito": "qualidade da evidência limitada a %s/100; a direção continua a do dado"
                      % dom.get("teto_na_qualidade_da_evidencia"),
            "texto": dom.get("texto")})
    if (dd or {}).get("direcao_mudou_pelo_tratamento"):
        bandeiras.append({"tipo": "direcao_virada_por_tratamento", "onde": "dimensão de dados",
                          "texto": (dd or {}).get("bandeira_de_direcao"), "muda_a_direcao": True,
                          "efeito": "moeda suspensa em SEM LEITURA"})
    if guarda_leitura["virou"]:
        bandeiras.append({"tipo": "direcao_virada_por_tratamento", "onde": "leitura da moeda",
                          "texto": guarda_leitura["texto"], "muda_a_direcao": True,
                          "efeito": "moeda suspensa em SEM LEITURA"})
    if ((dd or {}).get("virou_sozinho") or {}).get("sim"):
        bandeiras.append({"tipo": "uma_divulgacao_atinge_o_limiar",
                          "texto": dd["virou_sozinho"]["texto"], "muda_a_direcao": False,
                          "efeito": "a direção fica; a evidência cai e a bandeira aparece"})

    regime, regime_motivo = regime_do_banco(cc, dd, b)
    pev = proximo_evento_relevante(m, futuros or [], agora)
    nota_q = (qual or {}).get("nota")
    # A direcao publicada precisa ser a mesma que a leitura formada pela MAGNITUDE. Antes,
    # `direcao` guardava o vencedor da contagem de votos enquanto `leitura` vinha do sinal do
    # score continuo. Num empate, isso fazia o USD aparecer inclinado ao corte e, ao mesmo
    # tempo, marcar ciclo/MANTEM como a dimensao que "concordava". Preservamos o voto de
    # maioria para auditoria, mas toda explicacao da tela passa a comparar com a leitura final.
    direcao_voto_maioria = direcao
    direcao_leitura = ("SOBE" if leitura == "inclinado_alta"
                       else "CORTA" if leitura == "inclinado_corte"
                       else "MANTEM")
    direcao_formada = leitura in ("inclinado_alta", "inclinado_corte")
    concordam_por_dimensao = {
        k: bool(direcao_formada and v["direcao"] == direcao_leitura)
        for k, v in disponiveis.items()
    }
    n_concordam_leitura = sum(concordam_por_dimensao.values())

    if not disponiveis:
        concord_txt = "nenhuma dimensão vota"
    elif not direcao_formada:
        concord_txt = ("a dimensão disponível não forma direção" if len(disponiveis) == 1
                       else "%d dimensões disponíveis; direção não formada" % len(disponiveis))
    elif len(disponiveis) == 1:
        concord_txt = ("a única dimensão que vota concorda" if n_concordam_leitura
                       else "a única dimensão que vota não fecha direção")
    else:
        concord_txt = "%d de %d dimensões concordam" % (
            n_concordam_leitura, len(disponiveis))

    return {
        "moeda": m, "direcao": direcao_leitura, "direcao_voto_maioria": direcao_voto_maioria,
        "intensidade": intensidade,
        "score": score, "score_componentes": comp,
        # ---- AUDITORIA DO TRATAMENTO (lei de 08/set): a leitura crua ao lado da publicada ---
        "score_cru": score_cru,
        "leitura_crua": leitura_crua,
        "intensidade_relativa_crua_pct": intens_crua,
        "guarda_de_direcao": guarda_leitura,
        "bandeiras": bandeiras,
        "score_texto_se_votasse": texto_se_votasse,
        # TETO DA LEITURA = 0,25 por dimensao que VOTA. Sao duas (dados e ciclo) desde que a
        # fala e a geopolitica sairam do voto em 05/set, entao o teto e 0,50 — SEMPRE, nas
        # oito moedas. E o denominador da intensidade relativa e da divergencia: constante de
        # proposito, porque dividir pelo teto LIGADO fazia a FALTA de dado INFLAR a leitura.
        # ⚠️ CONSERTO DE 06/set: `score_teto` vinha 0,25 no NZD (uma dimensao de pe), o que
        # contraria o contrato ("score_teto e 0,50 em todas") e convidava quem lesse o campo a
        # normalizar pelo teto ligado. O teto que se move ganhou nome proprio,
        # `score_teto_ligado`, e ele so mede QUANTA dimensao esta de pe — nao normaliza nada.
        "score_teto": TETO_MOEDA,
        "score_teto_teorico": TETO_MOEDA,
        "score_teto_ligado": round(0.25 * len(disponiveis), 2),
        "score_nao_vai_para_a_tela": "lei do dono: a palavra 'score' e o número não aparecem "
                                     "em lugar nenhum da interface — nem no detalhe, nem em "
                                     "tooltip. Para a tela existem leitura_texto, "
                                     "concordancia_texto e evidencia_rotulo.",
        # ---- o que a tela mostra no lugar do numero -----------------------------------
        "regime": regime, "regime_motivo": regime_motivo,
        "leitura": leitura, "leitura_texto": leitura_txt, "leitura_motivo": leitura_motivo,
        "intensidade_relativa_pct": intens_rel,
        "intensidade_relativa_pelo_teto_ligado_pct": (
            round(abs(score) / (0.25 * len(disponiveis)) * 100) if disponiveis else 0),
        "faixas_leitura_provisorias": FAIXAS_LEITURA_PROVISORIAS,
        "concordancia_texto": concord_txt,
        "evidencia_rotulo": rotulo_de_evidencia(nota_q),
        "evidencia_faixas_provisorias": FAIXAS_EVIDENCIA_PROVISORIAS,
        "proximo_evento_relevante": pev,
        # ⚠️ CONSERTO DE 06/set: o contrato pede "existe OU e null COM MOTIVO". O null saia
        # cru, e null cru nao distingue "nao ha evento" de "nao perguntamos" — o mesmo buraco
        # que a dimensao de fala do CHF tinha. Agora o motivo vem escrito ao lado, e fica
        # null quando o evento existe (nao ha o que explicar).
        "proximo_evento_relevante_motivo": None if pev else (
            "nenhuma divulgação das %d famílias que o dono acompanha (%s) com impacto alto ou "
            "médio aparece no horizonte de %d dias do calendário carregado — é ausência no "
            "horizonte, não ausência de evento no mundo"
            % (len(FAMILIAS_RELEVANTES),
               ", ".join(sorted(set(FAMILIAS_RELEVANTES.values()))),
               HORIZONTE_FRENTE_DIAS)),
        # ------------------------------------------------------------------------------
        "conviccao_pct": conv, "conviccao_teto_pct": teto,
        "dimensoes_ligadas": len(disponiveis), "dimensoes_total": len(dims),
        "dimensoes_que_votam": list(votantes),
        "dimensoes_que_nao_votam": {"texto": SELO_NAO_VOTA, "geo": "experimental"},
        "concordam": concordam_por_dimensao,
        "dimensoes": dims,
        "qualidade_evidencia": qual,
        "familias_independentes": {"n": len(fams), "quais": sorted(fams)},
        "dominancia": dom,
        "fonte_texto": (tt or {}).get("origem"),
        "taxa": b.get("taxa"),
        "taxa_texto": b.get("taxa_texto"), "proxima": b.get("proxima"), "dias_ate": b.get("dias_ate"),
        "proxima_utc": b.get("proxima_utc"),
        "proxima_brt": (brt(b.get("proxima_utc")).strftime("%d/%m %H:%M")
                        if b.get("proxima_utc") else None),
        "banco": b.get("sigla"),
    }


# ---------------------------------------------------------------------------------------
# PARES
# ---------------------------------------------------------------------------------------
def estado_da_divergencia(d):
    """Faixas PROVISORIAS do dono (05/set). Zona neutra de verdade: ate 14 nao ha tese."""
    for nome in ("sem_tese", "observacao", "moderada", "forte"):
        lo, hi = FAIXAS_PROVISORIAS[nome]
        if lo <= d <= hi:
            return nome
    return "forte"


def proximo_invalidante(b, q, bancos):
    """A decisao mais proxima entre as duas pernas — o evento que pode derrubar a tese."""
    cand = []
    for m in (b, q):
        info = (bancos or {}).get("bancos", {}).get(m, {})
        data, dias, sigla = info.get("proxima"), info.get("dias_ate"), info.get("sigla")
        if data:
            cand.append({"moeda": m, "evento": sigla or m, "data": data,
                         "dias": dias if dias is not None else None})
    if not cand:
        return None
    return sorted(cand, key=lambda x: (x["data"]))[0]


def le_pares(leituras, bancos=None):
    """O par pela DIFERENCA dos scores das duas pernas.

    DIVERGENCIA = |diferenca| / TETO TEORICO do par x 100 (1,00 = 0,50 + 0,50). E o antigo
    "conviccao_pct" — o nome mudou porque conviccao e outra coisa (quanto isto acertou no
    passado), e isso HOJE NAO EXISTE: sai null com a nota de que precisa de backtest.
    ESTADO pelas faixas provisorias: ate 14 e sem_tese, e o par sai da lista principal sem
    sumir do arquivo — divergencia e as duas pernas continuam gravadas.

    ⚠️ CONSERTO DE 05/set (tarde) — O DENOMINADOR ERA O TETO LIGADO, E ISSO INFLAVA A
    DIVERGENCIA DE QUEM TINHA MENOS DADO. A conta era |diff| / teto LIGADO, e o teto ligado
    cai quando uma dimensao nao esta conectada. Consequencia medida na leitura da manha: o
    CADCHF saiu com divergencia 17 e estado "observacao" com teto 1,25 (o CHF nao tem feed do
    SNB, logo so duas dimensoes votam); com as duas pernas completas o MESMO diff de -0,217
    daria 14, que e sem_tese. Ou seja: o par entrava na lista principal por IGNORANCIA, nao
    por evidencia. EURAUD e EURNZD estavam na mesma fronteira (18 com 1,25 contra 15 com 1,50).

    Isto NAO fere a lei do dono "silencio nao e voto, dimensao sem dado nao vira zero": a
    dimensao ausente continua fora do NUMERADOR (o score soma so o que existe, nada vira
    zero). O que mudou e o DENOMINADOR, que agora e constante: 1,00, o teto teorico de duas
    pernas com DUAS dimensoes votando cada (era 1,50 ate a fala sair do voto, na tarde de
    05/set — ver `mudanca_de_escala_05set`). Assim menos evidencia significa divergencia
    MENOR, que e o sentido honesto — a falta de dado nunca deve empurrar um par para cima. O
    tamanho do buraco continua declarado a parte, na qualidade da evidencia.

    Os dois numeros ficam gravados lado a lado: `divergencia` (pelo teto teorico, a que
    manda) e `divergencia_pelo_teto_ligado` (a conta antiga, para auditoria).
    """
    saida = []
    for par in PARES:
        b, q = par[:3], par[3:]
        lb, lq = leituras[b], leituras[q]
        sb, sq = lb["score"], lq["score"]
        diff = round(sb - sq, 3)
        # teto TEORICO do par: 0,25 x 2 dimensoes que votam, nas duas pernas = 1,00. Constante
        # de proposito — e o que impede a falta de dado de inflar a leitura.
        # ⚠️ ERA 1,50 ate 05/set (tarde), quando a fala ainda votava. Com o denominador caindo
        # de 1,50 para 1,00, a MESMA diferenca economica sai 50% maior em divergencia; ao mesmo
        # tempo os scores encolhem, porque a parcela de fala saiu do numerador. As faixas
        # provisorias (0-14/15-24/25-39/40+) foram desenhadas na escala VELHA.
        teto_teorico = TETO_PAR
        # teto LIGADO = soma dos tetos das duas pernas. Nao normaliza mais nada; fica gravado
        # porque e a medida de quanta dimensao esta de pe neste par.
        teto = round((lb.get("score_teto_ligado") or 0.0)
                     + (lq.get("score_teto_ligado") or 0.0), 2)
        diverg = round(abs(diff) / teto_teorico * 100) if teto_teorico > 0 else 0
        diverg_ligado = round(abs(diff) / teto * 100) if teto > 0 else 0
        estado = estado_da_divergencia(diverg)

        # perna dominante: share do |score| de cada lado sobre a soma dos dois modulos
        tot = abs(sb) + abs(sq)
        if tot <= 0:
            perna_dom = {"moeda": None, "share_pct": 0}
        elif abs(sb) >= abs(sq):
            perna_dom = {"moeda": b, "share_pct": round(abs(sb) / tot * 100)}
        else:
            perna_dom = {"moeda": q, "share_pct": round(abs(sq) / tot * 100)}

        if abs(sb) == abs(sq):
            perna = None if sb == 0 and sq == 0 else "ambas"
        else:
            perna = b if abs(sb) > abs(sq) else q

        # qualidade do par = a MENOR das duas pernas: o elo fraco manda. Perna SEM nota
        # (nenhuma das quatro partes tem dado) nao vira zero: o par sai com qualidade null e
        # o alerta diz de qual perna faltou — lei do dono, silencio nao e voto.
        qb = ((lb.get("qualidade_evidencia") or {}).get("nota"))
        qq = ((lq.get("qualidade_evidencia") or {}).get("nota"))
        qb = int(qb) if qb is not None else None
        qq = int(qq) if qq is not None else None
        if qb is None or qq is None:
            q_par, elo = None, (b if qb is None else q)
        else:
            q_par = min(qb, qq)
            elo = b if qb <= qq else q

        # ⚠️ CONSERTO 06/set — A ZONA "SEM LEITURA" PASSA A VALER PARA O PAR.
        # Ate hoje a zona marcava a MOEDA e nao era herdada pelo par: nenhum dos 28 saia sem
        # leitura. Medido na rodada da manha: 18 dos 28 pares tinham ao menos uma perna sem
        # leitura, 9 dos 15 pares COM TESE tinham, e em 4 deles a perna que DA O MOTIVO estava
        # sem leitura com qualidade da evidencia 0/100. O topo da tela mandava "Compra
        # NZD/USD" com a maior divergencia do dia, atribuindo 55% do motivo a uma perna que o
        # proprio arquivo declarava sem direcao e sem evidencia.
        #
        # A regra nao inventa limiar novo: ela PROPAGA a regra que ja existe na moeda.
        #   (a) se a perna que da o MOTIVO esta sem leitura, o par nao tem tese — silencio nao
        #       e voto, e um par nao pode ser mais confiante que a perna que o move;
        #   (b) se a qualidade da evidencia do par e 0 ou nao existe, o par nao sai da zona de
        #       OBSERVACAO, por mais alta que seja a divergencia. Divergencia grande entre dois
        #       silencios continua sendo dois silencios.
        # Fica gravado em `estado_limitado_por` para ninguem precisar adivinhar por que um par
        # com 45% de divergencia esta rotulado observacao. PROVISORIO, como todo o resto.
        estado_bruto, limitado = estado, None
        motivo_perna = None if perna in (None, "ambas") else perna
        if motivo_perna and leituras[motivo_perna].get("leitura") == "sem_leitura":
            estado, limitado = "sem_tese", (
                "a perna que dá o motivo (%s) está sem leitura — silêncio não é voto, e o par "
                "não pode ter mais direção do que a perna que o move" % motivo_perna)
        elif (q_par is None or q_par == 0) and estado in ("moderada", "forte"):
            estado, limitado = "observacao", (
                "qualidade da evidência do par é %s — sem evidência o par não sai da zona de "
                "observação, por maior que seja a divergência"
                % ("nula (0/100)" if q_par == 0 else "inexistente"))

        if estado == "sem_tese":
            sinal, rotulo = "SEM_TESE", "sem tese"
            acao = "Sem tese"
        else:
            sinal = "BULL" if diff > 0 else "BEAR"
            rotulo = {"observacao": "observação", "moderada": "moderada", "forte": "forte"}[estado]
            acao = "%s %s/%s" % ("Compra" if diff > 0 else "Venda", b, q)

        alertas = []
        if limitado:
            alertas.append("estado rebaixado de '%s' para '%s': %s"
                           % (estado_bruto, estado, limitado))
        for m, L in ((b, lb), (q, lq)):
            d = L.get("dominancia") or {}
            if d.get("alerta") and d.get("texto"):
                alertas.append("uma única divulgação responde por %d%% da leitura do %s (%s)"
                               % (d.get("share_pct") or 0, m, d.get("item")))
            # auditoria de 08/set: a FAIXA NEUTRA é um piso aplicado a cada termo ANTES da
            # soma. Quando a direção de uma perna depende da largura dela, isso vai para a
            # tela — é onde o painel lê, e a lei é que tratamento que mexe na direção aparece.
            fx = ((L.get("dimensoes") or {}).get("dados") or {}).get("faixa_neutra") or {}
            if fx.get("direcao_depende_da_faixa"):
                _dd = (L.get("dimensoes") or {}).get("dados") or {}
                _hoje = _dd.get("direcao") or "?"
                _rot = {0.0: "sem faixa nenhuma", 0.5: "com a faixa pela metade",
                        2.0: "com a faixa dobrada"}
                _outras = ["%s a soma é %+.2f (%s)"
                           % (_rot.get(e["fator"], "com a faixa a %.1fx" % e["fator"]),
                              e["soma"], e["direcao"])
                           for e in (fx.get("escala") or [])
                           if e["fator"] != 1.0 and e["direcao"] != _hoje]
                alertas.append("a direção dos DADOS do %s depende da FAIXA NEUTRA (a régua de "
                               "'veio como esperado', PROVISÓRIA e nunca validada): hoje a "
                               "soma é %+.2f (%s), mas %s. A faixa zera %d divulgação(ões) "
                               "que, com o sinal do próprio desvio, pesariam %+.2f — zerar um "
                               "termo desloca a soma para o lado contrário, a mesma aritmética "
                               "da winsorização revogada"
                               % (m, _dd.get("soma") or 0.0, _hoje, "; ".join(_outras),
                                  fx.get("itens_zerados") or 0,
                                  fx.get("peso_que_os_zerados_teriam") or 0.0))
        if q_par is None:
            alertas.append("qualidade da evidência do par sai SEM NOTA: o %s não tem dado em "
                           "nenhuma das quatro partes — buraco declarado, não zero" % elo)
        else:
            alertas.append("qualidade da evidência do par = %d/100, a MENOR das duas pernas "
                           "(elo fraco: %s, %d/100 contra %d/100 do %s)"
                           % (q_par, elo, min(qb, qq), max(qb, qq), q if elo == b else b))
        for m, L in ((b, lb), (q, lq)):
            _t = (L.get("dimensoes") or {}).get("texto") or {}
            if not _t.get("conectada"):
                alertas.append("o %s não tem fonte de fala conectada (%s) — buraco declarado, "
                               "não zero" % (m, _t.get("origem")))
            if L.get("leitura") == "sem_leitura":
                alertas.append("a perna %s está SEM LEITURA (%s) — a tese do par se apoia só "
                               "na outra perna" % (m, L.get("leitura_motivo")))
        # a fala nao vota em nenhuma perna desde 05/set: dito uma vez, nao oito
        alertas.append("nenhuma das duas pernas tem fala votando: desde 05/set a dimensão de "
                       "discurso é contexto com selo, e a leitura vem de DADOS e CICLO apenas "
                       "— duas dimensões por perna, teto %.2f no par" % teto_teorico)
        if teto < teto_teorico:
            alertas.append("este par tem %.2f de %.2f do teto ligado: falta dimensão em uma "
                           "das pernas. A divergência é dividida pelo teto TEÓRICO (%.2f), "
                           "então a falta de dado BAIXA a leitura em vez de inflá-la — pela "
                           "conta antiga este par sairia com %d em vez de %d"
                           % (teto, teto_teorico, teto_teorico, diverg_ligado, diverg))
        if estado == "sem_tese":
            alertas.append("divergência %d está na zona neutra (0-14): sem tese, o par sai da "
                           "lista principal mas continua gravado" % diverg)

        saida.append({
            "par": par, "base": b, "cotada": q,
            "sinal": sinal, "forca": abs(diff), "rotulo": rotulo,
            "divergencia": diverg,
            "conviccao_pct": diverg,          # copia por compatibilidade — nome antigo
            "divergencia_pelo_teto_ligado": diverg_ligado,   # a conta antiga, so para auditar
            "divergencia_normalizador": {
                "usa": "teto_teorico", "teto_teorico": teto_teorico, "teto_ligado": teto,
                "texto": "divergência = |diferença| / teto TEÓRICO (%.2f) x 100. O teto "
                         "ligado deste par é %.2f e serve só para dizer quanta dimensão está "
                         "de pé — não normaliza mais nada, porque dividir pelo teto ligado "
                         "fazia a falta de dado INFLAR a divergência. ⚠️ O teto teórico caiu "
                         "de 1,50 para 1,00 em 05/set, quando a fala parou de votar: a mesma "
                         "diferença econômica sai 50%% maior em divergência, e as faixas "
                         "provisórias foram desenhadas na escala velha."
                         % (teto_teorico, teto)},
            "estado": estado,
            "estado_pela_divergencia": estado_bruto,
            "estado_limitado_por": limitado,
            "faixas_provisorias": FAIXAS_PROVISORIAS,
            "qualidade_evidencia": q_par,
            "qualidade_por_perna": {b: qb, q: qq},
            "qualidade_elo_fraco": elo,
            "conviccao_historica": None,
            "conviccao_historica_nota": NOTA_CONVICCAO_HISTORICA,
            "perna_dominante": perna_dom,
            "acao": acao,
            "proximo_evento_invalidante": proximo_invalidante(b, q, bancos),
            "alertas": alertas,
            "diff": diff, "diff_teto": teto, "diff_teto_teorico": teto_teorico,
            # ⚠️ LEI (b) DO DONO: nem a palavra "score" nem o NÚMERO do score aparecem na
            # interface — nem no detalhe, nem em tooltip. Este campo é texto de tela, então
            # ele passou a falar em LEITURA, não em número: até 05/set saía
            # "AUD +0.15 contra CAD -0.10", que é o score das duas pernas escrito por extenso.
            # O par de números continua existindo para auditoria, no campo abaixo, que é
            # DADO e não vai para a tela (o mesmo tratamento de `score`).
            "motivo": "%s %s contra %s %s"
                      % (b, lb.get("leitura_texto") or "sem leitura",
                         q, lq.get("leitura_texto") or "sem leitura"),
            "motivo_numerico_auditoria": "%s %+.2f contra %s %+.2f" % (b, sb, q, sq),
            "motivo_nao_vai_para_a_tela": "motivo_numerico_auditoria carrega o número da "
                                          "leitura contínua das duas pernas e existe só para "
                                          "auditoria — a tela usa `motivo`, que fala em "
                                          "leitura e não em número (lei do dono).",
            "perna_motivo": perna,
            "leitura_base": {"direcao": lb["direcao"], "score": sb, "conviccao_pct": lb["conviccao_pct"],
                             "votando": lb["dimensoes_ligadas"],
                             "leitura": lb.get("leitura"), "leitura_texto": lb.get("leitura_texto"),
                             "regime": lb.get("regime"),
                             "concordancia_texto": lb.get("concordancia_texto"),
                             "evidencia_rotulo": lb.get("evidencia_rotulo"),
                             "qualidade_evidencia": qb},
            "leitura_cotada": {"direcao": lq["direcao"], "score": sq, "conviccao_pct": lq["conviccao_pct"],
                               "votando": lq["dimensoes_ligadas"],
                               "leitura": lq.get("leitura"), "leitura_texto": lq.get("leitura_texto"),
                               "regime": lq.get("regime"),
                               "concordancia_texto": lq.get("concordancia_texto"),
                               "evidencia_rotulo": lq.get("evidencia_rotulo"),
                               "qualidade_evidencia": qq},
            # o proximo DADO que pode derrubar a tese do par: o mais proximo das duas pernas.
            # E diferente do proximo_evento_invalidante, que e a proxima DECISAO.
            "proximo_evento_relevante": min(
                [x for x in (lb.get("proximo_evento_relevante"),
                             lq.get("proximo_evento_relevante")) if x],
                key=lambda x: x.get("quando_utc") or "", default=None),
        })

    # a lei das duas pernas: quem compartilha a perna que da o motivo e a MESMA aposta
    por_perna = {}
    for r in saida:
        if r["sinal"] in ("BULL", "BEAR") and r.get("perna_motivo") not in (None, "ambas"):
            por_perna.setdefault(r["perna_motivo"], []).append(r["par"])
    for r in saida:
        p = r.get("perna_motivo")
        r["mesma_aposta"] = [x for x in por_perna.get(p, []) if x != r["par"]] if p in por_perna else []
        if r["mesma_aposta"] and r["sinal"] != "SEM_TESE":
            r["alertas"].append("mesma aposta que %s — compartilham a perna %s e não diversificam"
                                % (", ".join(r["mesma_aposta"][:4]), p))
    return saida


# ---------------------------------------------------------------------------------------
# SNAPSHOTS — arquivo imutavel, uma linha por par por instante de gravacao
# ---------------------------------------------------------------------------------------
def grava_snapshots(pares, leituras, agora, origem):
    """data/snapshots/AAAA-MM-DD.jsonl — so acrescenta, nunca reescreve.

    E o caderno para o backtest futuro: sem ele a conviccao historica nunca sai de null.
    Os campos de "preenchido_pelo_operador" ficam null para o Eduardo anotar depois.

    ⚠️ QUEM MANDA AQUI E O snapshot.py. Ele e o dono do diretorio (ver
    data/snapshots/LEIA-ME.md), grava com a regra anti-entulho (primeira do dia · mudou
    direcao/divergencia/qualidade · saiu evento de impacto alto) e acrescenta os campos
    `gatilho` e `ultimo_evento_alto_utc`. Se ele estiver presente, e ele que grava — dois
    escritores no mesmo arquivo dariam linha dobrada com formatos diferentes. A funcao
    abaixo so entra como RESERVA, quando o snapshot.py nao existe ou falha, para o contrato
    nao ficar sem registro nenhum.
    """
    _snap = None
    try:
        import snapshot as _snap                                        # noqa: WPS433
        codigo = _snap.main()
        fn = os.path.join(SNAPSHOTS, "%s.jsonl" % agora.date().isoformat())
        try:
            n = sum(1 for _ in io.open(fn, encoding="utf-8"))
        except Exception:
            n = 0
        if codigo in (0, 3):
            # 0 = gravou (ou nao havia o que gravar); 3 = a trava estava com outro processo,
            # e nesse caso a RESERVA nao pode entrar: seria exatamente o segundo escritor que
            # a trava existe para impedir.
            rot = "gravado pelo snapshot.py, com regra anti-entulho" if codigo == 0 else \
                  "outro processo estava gravando; nada gravado nesta rodada"
            return fn + "  (%s)" % rot, n
        print("  ! snapshot.py devolveu %s — gravando pela reserva do sentimento.py" % codigo)
    except Exception as e:
        print("  ! snapshot.py indisponível (%s) — gravando pela reserva do sentimento.py" % e)

    os.makedirs(SNAPSHOTS, exist_ok=True)
    fn = os.path.join(SNAPSHOTS, "%s.jsonl" % agora.date().isoformat())
    linhas = []
    for r in pares:
        b, q = r["base"], r["cotada"]
        lb, lq = leituras[b], leituras[q]
        ddb = (lb.get("dimensoes") or {}).get("dados") or {}
        ddq = (lq.get("dimensoes") or {}).get("dados") or {}
        ttb = (lb.get("dimensoes") or {}).get("texto") or {}
        ttq = (lq.get("dimensoes") or {}).get("texto") or {}
        ult = [x.get("quando_utc") for x in (ddb.get("principais") or []) + (ddq.get("principais") or [])
               if x.get("quando_utc")]
        fontes = [origem]
        for m, tt in ((b, ttb), (q, ttq)):
            if tt:
                fontes.append("%s: fala por %s" % (m, tt.get("origem")))
            else:
                fontes.append("%s: sem fala conectada" % m)
        direcao = {"BULL": "COMPRA", "BEAR": "VENDA"}.get(r["sinal"], "SEM_TESE")
        if r["estado"] == "sem_tese":
            direcao = "SEM_TESE"        # nunca um lado dentro da zona neutra
        linhas.append({
            "gravado_em": agora.isoformat(),
            "par": r["par"],
            "direcao": direcao,
            "divergencia": r["divergencia"],
            "qualidade_evidencia": r["qualidade_evidencia"],
            "estado": r["estado"],
            # a reserva se identifica: sem isto o arquivo de hoje ficou com 140 linhas SEM
            # `gatilho` e 43 COM, dois esquemas misturados e nada dizendo quem escreveu qual
            "gatilho": "reserva_do_sentimento",
            "perna_dominante": r["perna_dominante"],
            "como_a_divergencia_saiu": {
                "diff": r.get("diff"), "teto_ligado": r.get("diff_teto"),
                "teto_teorico": r.get("diff_teto_teorico"),
                "score_base": (r.get("leitura_base") or {}).get("score"),
                "score_cotada": (r.get("leitura_cotada") or {}).get("score"),
                "conta": "divergencia = |diff| / teto_teorico x 100 (o teto teorico e 1,00: 0,25 x 2 dimensoes que votam, nas duas pernas — era 1,50 ate a fala sair do voto em 05/set). O teto LIGADO fica ao lado so para dizer quanta dimensao estava de pe."},
            "dados_disponiveis": {
                "ultimo_evento_utc": max(ult) if ult else None,
                "ultimo_evento_alto_utc": None,
                "n_eventos_janela": int(ddb.get("n") or 0) + int(ddq.get("n") or 0),
                "n_falas": int(ttb.get("n") or 0) + int(ttq.get("n") or 0),
                "fontes": fontes,
            },
            "proximo_evento_invalidante": r["proximo_evento_invalidante"],
            "preenchido_pelo_operador": {"bo_h4": None, "zoi_m30": None, "primeiro_toque": None,
                                         "entrada": None, "resultado_r": None},
        })
    # A MESMA trava do snapshot.py: append concorrente no Windows apaga linha ja gravada
    # (medido: 9 de 25 rodadas perderam metade das linhas). Sem o snapshot.py importavel nao
    # ha trava disponivel — e ai a reserva grava do jeito antigo e avisa.
    trava = getattr(_snap, "trava_exclusiva", None) if _snap else None
    if trava is None:
        print("  ! sem trava disponível: gravação de reserva sujeita a perda se houver "
              "outro processo escrevendo agora")
        with io.open(fn, "a", encoding="utf-8", newline="\n") as f:
            for x in linhas:
                f.write(json.dumps(x, ensure_ascii=False, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return fn, len(linhas)
    with trava(fn) as preso:
        if not preso:
            print("  ! outro processo está gravando o snapshot — reserva não gravou")
            return fn + "  (trava ocupada; nada gravado)", 0
        with io.open(fn, "a", encoding="utf-8", newline="\n") as f:
            for x in linhas:
                f.write(json.dumps(x, ensure_ascii=False, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    return fn, len(linhas)


# ---------------------------------------------------------------------------------------
# INSTRUMENTOS
# ---------------------------------------------------------------------------------------
def le_instrumentos(leituras):
    """XAUUSD, NQ e ES — os tres respondem ao juro americano, e so a perna do USD conta.

    O Eduardo apontou (02/set): "eles tem correlacao estreitamente ligada com os juros dos
    USA". O que esta MEDIDO em casa e so o ouro: juro real de 10 anos x ouro = -0,684
    contemporaneo em 60 pregoes (n=18, janelas sem sobreposicao); a preditiva morre no ruido
    (-0,132). NQ e ES entram pelo canal de livro-texto (taxa de desconto comprime multiplo,
    NQ mais que ES por ter duracao maior) — NAO medido em casa, e sai declarado assim.

    ⚠️ GEOPOLITICA AQUI TAMBEM NAO VOTA (05/set). Em 04/set ela entrava como segunda perna do
    ouro; a decisao nova retirou o voto da regra declarada e nunca medida, em toda a casa.
    O pico continua calculado e exibido no cartao.

    ⚠️ Direcao de LEITURA, nao de entrada: nas 88 operacoes manuais do Eduardo o dolar no
    minuto correlacionou +0,26 com o ouro e quebrou 41% das vezes (filtro do DXY reprovado).
    """
    u = leituras.get("USD") or {}
    d = u.get("direcao", "MANTEM")
    s_usd = float(u.get("score") or 0.0)
    motivos = ((u.get("dimensoes") or {}).get("dados") or {}).get("principais", [])[:4]

    geo = carrega_json(GEO) or {}
    zw = (((geo.get("mundo") or {}).get("conflito") or {}).get("volume") or {}).get("z")
    zu = ((((geo.get("moedas") or {}).get("USD") or {}).get("temas") or {}).get("conflito") or {}).get("volume", {}).get("z")
    z_conf = max([z for z in (zw, zu) if z is not None], default=None)
    tem_pico = (z_conf is not None and z_conf >= GEO_Z_CORTE)
    manchete_geo = ((((geo.get("mundo") or {}).get("conflito") or {}).get("manchetes") or [{}])[0].get("titulo"))
    geo_estado = ("não conectada" if z_conf is None else
                  ("pico de conflito z %+.1f (exibido, NÃO votado)" % z_conf if tem_pico
                   else "quieta (z %+.1f)" % z_conf))

    def leitura_instr(sinal_geo):
        """score do instrumento = perna do USD invertida. A geopolitica entra com 0,000."""
        comp_usd = -s_usd
        comp_geo = 0.0
        s = round(comp_usd + comp_geo, 3)
        # teto TEORICO de UMA perna: 0,25 x 2 dimensoes que votam = 0,50 (era 0,75 ate a
        # fala sair do voto, na tarde de 05/set). Constante, pelo mesmo motivo dos pares —
        # dividir pelo teto LIGADO fazia a falta de dado INFLAR a divergencia. O teto ligado
        # fica gravado ao lado.
        maximo = TETO_MOEDA
        teto_ligado = round(u.get("score_teto_ligado") or 0.0, 2)
        diverg = round(abs(s) / maximo * 100)
        # a MESMA zona neutra dos pares vale aqui: 1% de divergência rotulado "BEAR" é
        # exatamente o vício que a revisão de 05/set foi corrigir.
        sinal = "SEM_TESE" if estado_da_divergencia(diverg) == "sem_tese" else \
            ("BULL" if s > 0 else "BEAR")
        return s, sinal, diverg, {"usd_invertido": round(comp_usd, 3),
                                  "geopolitica": comp_geo,
                                  "geopolitica_se_votasse": round(sinal_geo * 0.25, 3) if tem_pico else 0.0,
                                  "maximo": maximo, "teto_teorico": maximo,
                                  "teto_ligado": teto_ligado}

    corr = carrega_json(os.path.join(AQUI, "data", "correlacao_juros.json")) or {}
    corr_inst = corr.get("instrumentos", {})

    def medido_de(sym):
        c = corr_inst.get(sym)
        if not c or not c.get("series"):
            return None, "NÃO medido em casa ainda — correlacao_juros.py não rodou"
        s = c["series"]
        real = s.get("real10y") or {}
        nom2 = s.get("nominal2y") or {}
        txt = ("5 anos de dados diários, blocos sem sobreposição: juro real de 10 anos %s no mesmo dia, "
               "%s em 20 pregões (n=%s), %s em 60 pregões (n=%s); nominal de 2 anos %s em 60 pregões. "
               "Preditiva (juro hoje → preço amanhã / em 5 dias): %s / %s — dentro do ruído. "
               "O micro acompanha o grande em %s."
               % (real.get("contemp_1d"), real.get("contemp_20d"), real.get("n_20d"),
                  real.get("contemp_60d"), real.get("n_60d"), nom2.get("contemp_60d"),
                  real.get("pred_1d"), real.get("pred_5d"), c.get("micro_vs_grande_corr")))
        return {"series": s, "micro_vs_grande": c.get("micro_vs_grande_corr"),
                "simbolo_micro": c.get("simbolo_micro"), "gerado_em": corr.get("gerado_em"),
                "nota": corr.get("nota")}, txt

    base = {
        "perna": "USD",
        "leitura_usd": {"direcao": d, "score": s_usd, "conviccao_pct": u.get("conviccao_pct", 0),
                        "teto_pct": u.get("conviccao_teto_pct"),
                        "qualidade_evidencia": ((u.get("qualidade_evidencia") or {}).get("nota"))},
        "geo": {"z_conflito": z_conf, "estado": geo_estado, "manchete": manchete_geo,
                "vota": False, "selo": "experimental",
                "regra": "pico de conflito seria refúgio (ouro sobe, NQ e ES caem) — regra "
                         "declarada e nunca medida; desde 05/set não vota, só aparece"},
        "motivos": motivos,
        "conviccao_historica": None,
        "conviccao_historica_nota": NOTA_CONVICCAO_HISTORICA,
        "aviso": "é a leitura do lado fundamental ao longo de semanas, não uma regra de entrada: "
                 "em 88 operações manuais o dólar no minuto correlacionou +0,26 com o ouro e "
                 "quebrou 41% das vezes (filtro do DXY reprovado).",
    }
    out = []
    for sym, nome, canal, sinal_geo in (
        ("XAUUSD", "Ouro",
         "juro real: uma leitura hawkish do USD levanta o juro real e o ouro cai; uma dovish faz o "
         "contrário. A geopolítica fica visível ao lado, sem votar", +1),
        ("NQ", "Nasdaq 100",
         "taxa de desconto: juro esperado mais alto comprime múltiplo, e a tecnologia de duração longa "
         "sofre mais. A geopolítica fica visível ao lado, sem votar", -1),
        ("ES", "S&P 500",
         "taxa de desconto: mesmo canal do NQ, com menos duração e mais sensibilidade do lucro ao "
         "crescimento. A geopolítica fica visível ao lado, sem votar", -1),
    ):
        correl, medido = medido_de(sym)
        s, sinal, diverg, comp = leitura_instr(sinal_geo)
        estado = estado_da_divergencia(diverg)
        # (vUi) os tres instrumentos nao gravavam `acao` nem `qualidade_evidencia`, e a
        # interface tinha de deduzir os dois. Deduzir dava "Qualidade 100/100" nos tres,
        # numero que e do DOLAR e nao do instrumento. Agora saem gravados, e a qualidade vem
        # com a etiqueta dizendo de quem ela e — o instrumento tem UMA perna so.
        acao_i = "Sem tese" if estado == "sem_tese" else \
            ("Compra %s" % sym if s > 0 else "Venda %s" % sym)
        q_usd = ((u.get("qualidade_evidencia") or {}).get("nota"))
        out.append(dict(base, simbolo=sym, nome=nome, canal=canal, medido=medido, correlacoes=correl,
                        sinal=sinal, divergencia=diverg, conviccao_pct=diverg, score=s,
                        estado=estado, score_componentes=comp,
                        faixas_provisorias=FAIXAS_PROVISORIAS,
                        acao=acao_i,
                        qualidade_evidencia=(int(q_usd) if q_usd is not None else None),
                        qualidade_evidencia_de="USD",
                        qualidade_evidencia_nota="o instrumento tem UMA perna só (o dólar), "
                                                 "então esta é a qualidade da evidência do "
                                                 "USD, não uma medida do próprio instrumento"))
    return out


# ---------------------------------------------------------------------------------------
# FRESCOR — (D) prioridade 2 do dono: nao exibir leitura operacional com dado atrasado
# ---------------------------------------------------------------------------------------
def bloco_frescor(agora, cal_sincronizado_em, cal_ao_vivo, bancos, discursos, noticias, geo):
    """O atraso do dado MAIS VELHO que alimenta a leitura, e o que a tela deve dizer.

    O dono, na revisao de 05/set: "o painel avisa 'dados do calendario de 4 horas atras' mas
    continua mostrando todas as direcoes normalmente. Se saiu noticia nessas 4 horas, a
    leitura pode estar invalida".

    QUEM CONTA PARA O ATRASO: so as fontes que alimentam as dimensoes QUE VOTAM — o
    calendario (dimensao de dados) e o bancos_centrais.json (dimensao de ciclo). Discursos,
    noticias e geopolitica alimentam CONTEXTO, que nao vota; a idade deles fica gravada ao
    lado, rotulada, sem puxar o estado. Isso e a mesma lei de sempre: o que nao vota nao
    manda na leitura.

    ULTIMA SINCRONIZACAO BEM-SUCEDIDA = o instante ate o qual TODAS as fontes que votam
    estavam em dia, ou seja, o MENOR carimbo entre elas. Nao e "a idade generica do arquivo":
    quando a busca ao vivo da FXStreet funciona, o carimbo do calendario e AGORA, mesmo que o
    arquivo no disco seja de ontem.

    LIMIARES PROVISORIOS: 45 min = atrasado · 120 min = muito atrasado. Numeros do dono,
    escolhidos por ordem de grandeza (o cron roda a cada 15 minutos, entao 45 min sao tres
    ciclos perdidos), nao por calibracao.
    """
    def idade_min(iso):
        try:
            q = dt.datetime.fromisoformat(str(iso))
        except Exception:
            return None
        if q.tzinfo is None:
            q = q.replace(tzinfo=dt.timezone.utc)
        return max(0.0, (agora - q).total_seconds() / 60.0)

    fontes = [
        {"fonte": "calendário econômico", "arquivo": "FXStreet ao vivo" if cal_ao_vivo
         else os.path.basename(CAL_LOCAL), "alimenta": "dimensão de dados (VOTA)",
         "vota": True, "sincronizado_em": cal_sincronizado_em,
         "atraso_min": idade_min(cal_sincronizado_em),
         "ao_vivo": bool(cal_ao_vivo)},
        {"fonte": "bancos centrais", "arquivo": os.path.basename(BANCOS),
         "alimenta": "dimensão de ciclo (VOTA)", "vota": True,
         "sincronizado_em": (bancos or {}).get("gerado_em"),
         "atraso_min": idade_min((bancos or {}).get("gerado_em"))},
        {"fonte": "discursos dos bancos centrais", "arquivo": os.path.basename(DISCURSOS),
         "alimenta": "dimensão de fala (contexto, NÃO vota)", "vota": False,
         "sincronizado_em": (discursos or {}).get("gerado_em"),
         "atraso_min": idade_min((discursos or {}).get("gerado_em"))},
        {"fonte": "imprensa", "arquivo": os.path.basename(NOTICIAS),
         "alimenta": "contexto de fala (NÃO vota)", "vota": False,
         "sincronizado_em": (noticias or {}).get("gerado_em"),
         "atraso_min": idade_min((noticias or {}).get("gerado_em"))},
        {"fonte": "geopolítica (GDELT)", "arquivo": os.path.basename(GEO),
         "alimenta": "dimensão experimental (NÃO vota)", "vota": False,
         "sincronizado_em": (geo or {}).get("gerado_em"),
         "atraso_min": idade_min((geo or {}).get("gerado_em"))},
    ]
    for f in fontes:
        f["atraso_min"] = None if f["atraso_min"] is None else int(round(f["atraso_min"]))
        f["atraso_texto"] = texto_atraso(f["atraso_min"])

    votantes = [f for f in fontes if f["vota"] and f["atraso_min"] is not None]
    if votantes:
        pior = max(votantes, key=lambda f: f["atraso_min"])
        atraso = pior["atraso_min"]
        sinc = pior["sincronizado_em"]
    else:
        pior, atraso, sinc = None, None, None

    lim = FRESCOR_LIMIARES
    if atraso is None:
        estado = "muito_atrasado"
    elif atraso >= lim["muito_atrasado_min"]:
        estado = "muito_atrasado"
    elif atraso >= lim["atrasado_min"]:
        estado = "atrasado"
    else:
        estado = "ok"
    bloqueia = estado == "muito_atrasado"

    q = brt(sinc)
    if atraso is None:
        texto = ("Sem carimbo de sincronização em nenhuma fonte que vota — leituras sem "
                 "validade declarada. Não utilizar como nova tese até a sincronização.")
    elif estado == "ok":
        texto = ("Dados sincronizados há %s (%s, BRT). Leituras válidas."
                 % (texto_atraso(atraso), q.strftime("%d/%m %H:%M") if q else "?"))
    else:
        texto = ("Dados atrasados em %s — leituras potencialmente desatualizadas. Não "
                 "utilizar como nova tese até a sincronização." % texto_atraso(atraso))

    return {
        "atraso_min": atraso,
        "atraso_texto": texto_atraso(atraso),
        "estado": estado,
        "ultima_sincronizacao_ok_utc": sinc,
        "ultima_sincronizacao_ok_brt": (q.strftime("%d/%m/%Y %H:%M") + " (BRT)") if q else None,
        "bloqueia_leitura": bloqueia,
        "texto": texto,
        "limiares_provisorios": dict(lim),
        "fonte_mais_velha": (pior or {}).get("fonte"),
        "fontes": fontes,
        "o_que_conta": "só as fontes que alimentam dimensão QUE VOTA entram no atraso "
                       "(calendário e bancos centrais). Discurso, imprensa e geopolítica são "
                       "contexto: a idade deles fica gravada, rotulada, e não muda o estado.",
        "o_que_a_tela_faz": "com estado 'atrasado' ou 'muito_atrasado' a interface mostra o "
                            "aviso no topo e acinzenta as linhas; com bloqueia_leitura=true "
                            "nenhuma leitura direcional deve ser apresentada como tese nova.",
        "idade_da_publicacao": IDADE_DA_PUBLICACAO,
        "provisorio": True,
    }


# ⚠️ CONSERTO 06/set — SAO DOIS RELOGIOS, E ATE HOJE SO UM ERA MEDIDO.
# O `atraso_min` acima e a idade da FONTE no instante em que esta rodada foi gerada. Como
# data/bancos_centrais.json e reescrito pelo passo ANTERIOR da mesma rodada, e o calendario e
# buscado ao vivo, esse numero e o tempo entre dois PASSOS da mesma cadeia — quase sempre 1 a
# 18 minutos. Medido: nas 13 versoes de data/sentimento.json que ja tinham o bloco, o estado
# saiu "ok" em 13 de 13. A tarja NUNCA acendeu.
#
# O relogio que falta e o do LEITOR: quanto tempo faz que esta pagina foi publicada. Medido no
# historico do repositorio, 33 rodadas entre 02/set 10:34 e 06/set 17:59: intervalo minimo
# 91 min, MEDIANA 157 min (2h37), media 188, maximo 549 min (9h09). O cron pede */15; o
# GitHub Actions entrega mediana de 2h37, porque o proprio manual dele diz que o `schedule`
# pode atrasar e que trabalho na fila pode ser descartado.
#
# POR QUE OS LIMIARES SAO OUTROS AQUI. Aplicar 45/120 min ao relogio do leitor deixaria a
# tarja ambar em 100% das rodadas e vermelha em 78% — e uma tarja que grita sempre nao avisa
# nada, alem de suspender a leitura na maior parte do tempo. O painel nao e tempo real por
# construcao; o que o leitor precisa saber e quando a CADEIA PAROU, nao que passaram 20
# minutos. Por isso os cortes daqui saem do ritmo MEDIDO: 180 min (acima da mediana de 157) e
# 360 min (bem acima do intervalo tipico, abaixo do pior caso observado de 549).
# ⚠️ Os dois numeros sao PROVISORIOS como todos os outros, e derivados de 33 observacoes de
#    quatro dias — nao de um estudo de disponibilidade.
IDADE_DA_PUBLICACAO = {
    "o_que_e": "há quanto tempo esta leitura foi publicada, no relógio de quem lê",
    "como_medir": "agora menos a raiz gerado_em — a interface recalcula no navegador; o "
                  "número gravado no arquivo envelhece junto com o arquivo e por isso não "
                  "serve sozinho",
    "limiares_provisorios_min": {"atrasado_min": 180, "muito_atrasado_min": 360},
    "por_que_limiares_diferentes": "o atraso_min mede o intervalo entre dois PASSOS da mesma "
                                   "cadeia (1 a 18 min na prática) e usa 45/120; a idade da "
                                   "publicação mede o intervalo entre RODADAS, cuja mediana "
                                   "medida é de 157 min. Usar 45/120 aqui deixaria a tarja "
                                   "acesa em 100% das rodadas.",
    "ritmo_medido": {"janela": "02/09 10:34 a 06/09 17:59 (33 rodadas publicadas)",
                     "minimo_min": 91, "mediana_min": 157, "media_min": 188, "maximo_min": 549,
                     "cron_pedido": "*/15", "por_que_nao_cumpre":
                         "o GitHub Actions declara que o schedule pode atrasar em carga alta e "
                         "que trabalho na fila pode ser descartado"},
    "nao_bloqueia": "a idade da publicação NÃO liga bloqueia_leitura. Ela avisa; quem "
                    "suspende a leitura é o estado das fontes que votam.",
    "provisorio": True,
}


# ---------------------------------------------------------------------------------------
def main():
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 96)
    print("SENTIMENTO — leitura para frente, por moeda e por par")
    print("=" * 96)
    # eventos_janela devolve QUATRO valores desde a revisao do horizonte para frente:
    # (eventos, origem, quando o calendario sincronizou, sincronizou com sucesso?). O
    # main() ainda desempacotava dois e a cadeia inteira morria aqui com
    # 'too many values to unpack'. Os dois ultimos alimentam o bloco de FRESCOR da raiz.
    ev, origem, cal_sincronizado_em, cal_ao_vivo = eventos_janela(agora)
    bancos = carrega_json(BANCOS)
    discursos = carrega_json(DISCURSOS) or carrega_json(DISCURSOS_FED)
    print("  eventos na janela: %d  (%s)" % (len(ev), origem))
    print("  regras: FALA e geopolítica NÃO votam (teto 0,50) · ciclo com decaimento · zona "
          "neutra 0-14 · 08/set: soma CRUA (winsorização revogada), dominância = régua de "
          "CONFIANÇA, guarda de direção ligada")

    geo = carrega_json(GEO)
    noticias = carrega_json(NOTICIAS)
    futuros = eventos_para_frente(ev, agora)
    print("  eventos FUTUROS para o próximo evento relevante: %d" % len(futuros))
    frescor = bloco_frescor(agora, cal_sincronizado_em, cal_ao_vivo, bancos, discursos,
                            noticias, geo)
    print("  FRESCOR: %s — %s" % (frescor["estado"].upper(), frescor["texto"]))
    leituras = {m: le_moeda(m, ev, bancos, discursos, agora, geo, noticias, futuros)
                for m in MOEDAS}
    print()
    print("  %-4s %-7s %-5s %-6s %-5s  %-24s %-30s %-30s %s"
          % ("moeda", "viés", "conv", "teto", "qual", "dados (VOTA)", "fala (NÃO VOTA)",
             "ciclo (VOTA)", "geo (não vota)"))
    print("  " + "-" * 148)
    for m in MOEDAS:
        x = leituras[m]
        D = x["dimensoes"]
        dd = D["dados"]; tt = D["texto"]; cc = D["ciclo"]; gg = D["geo"]
        print("  %-4s %-7s %3d%%  %3d%%  %3s   %-24s %-30s %-30s %s"
              % (m, x["direcao"], x["conviccao_pct"], x["conviccao_teto_pct"],
                 "—" if x["qualidade_evidencia"]["nota"] is None
                 else str(x["qualidade_evidencia"]["nota"]),
                 "%s%s (%+.1f, n=%d)" % (dd["direcao"], "" if dd.get("vota") else "*",
                                         dd["soma"], dd["n"]),
                 ("contexto %s (%dh/%dd, %s)"
                  % (tt.get("direcao_contexto") or "—", tt["hawkish"], tt["dovish"],
                     tt.get("origem")))
                 if tt else "não conectada",
                 "%s%s (dec %.2f, %dd)" % (cc["direcao"], "" if cc.get("vota") is not False else "*",
                                           cc.get("decaimento") or 0.0,
                                           cc.get("idade_dias") or 0),
                 ("%s (energia z=%s, conflito z=%s)" % (gg["estado"], gg["z_energia"], gg["z_conflito"])
                  if gg.get("conectada") is not False else "não conectada (buraco declarado)")
                 if gg else "não conectada"))
    print("    * = dimensão NÃO VOTA nesta moeda (silêncio não é voto): ela baixa o teto.")

    # ---- O QUE VAI PARA A TELA, no lugar do número (prioridades 1, 4 e zona sem leitura) --
    print()
    print("  O QUE A TELA MOSTRA — sem a palavra 'score' e sem o número, por lei do dono")
    print("  %-4s %-7s %-12s %-22s %-26s %-24s %s"
          % ("moeda", "taxa", "regime", "leitura", "concordância / evidência",
             "próximo evento relevante", "próxima decisão"))
    print("  " + "-" * 152)
    for m in MOEDAS:
        x = leituras[m]
        pe = x.get("proximo_evento_relevante") or {}
        print("  %-4s %-7s %-12s %-22s %-26s %-24s %s"
              % (m, x.get("taxa_texto") or "—", x.get("regime"), x.get("leitura_texto"),
                 "%s · %s" % (x.get("concordancia_texto"), x.get("evidencia_rotulo") or "—"),
                 ("%s %s%s" % (pe.get("titulo"), pe.get("quando_brt"),
                               "" if pe.get("impacto") == "HIGH" else " (médio)"))
                 if pe else "nada no horizonte",
                 "%s %s" % (x.get("banco") or "—", x.get("proxima") or "—")))
    sem_leitura = [m for m in MOEDAS if leituras[m].get("leitura") == "sem_leitura"]
    print("  SEM LEITURA (zona provisória: intensidade < %d%% do teto %.2f, ou menos de %d "
          "dimensões votando): %d de %d — %s"
          % (FAIXAS_LEITURA_PROVISORIAS["intensidade_minima_pct"], TETO_MOEDA,
             FAIXAS_LEITURA_PROVISORIAS["dimensoes_minimas_votando"],
             len(sem_leitura), len(MOEDAS), ", ".join(sem_leitura) or "nenhuma"))

    print()
    print("  VEREDITO POR ORADOR — lê negação, condição e tempo verbal. NÃO VOTA.")
    achou_ver = False
    for m in MOEDAS:
        for v in ((leituras[m]["dimensoes"].get("texto") or {}).get("veredito_por_orador") or []):
            achou_ver = True
            print("    %-4s %-16s %-18s %s" % (m, v["orador"], v["veredito"], (v.get("motivo") or "")[:90]))
    if not achou_ver:
        print("    · nenhuma fala com texto lido na janela")

    print()
    print("  DOMINÂNCIA — régua de CONFIANÇA (corte %d%%). A soma é CRUA desde 08/set: nenhum "
          "termo é cortado, e a direção nunca é alterada por concentração."
          % DOMINANCIA["corte_participacao_pct"])
    for m in MOEDAS:
        x = leituras[m]
        dd = x["dimensoes"]["dados"]
        d = dd["dominancia"]
        q = x["qualidade_evidencia"]
        print("    %-4s soma crua %+6.2f = soma tratada %+6.2f (desloc %+.2f) · maior item %3d%% "
              "(antes %3d%%) · direção %-6s · qualidade %s%s · %s"
              % (m, dd["soma_crua"], dd["soma_tratada"],
                 dd["tratamento_da_soma"]["deslocamento"],
                 dd["participacao_maior_item_depois"], dd["participacao_maior_item_antes"],
                 dd["direcao"],
                 "—" if q["nota"] is None else str(q["nota"]),
                 (" (era %s, teto pela dominância)" % q["nota_antes_da_dominancia"])
                 if q.get("limitada_pela_dominancia") else "",
                 "ALERTA DE DOMINÂNCIA" if d["alerta"] else "ok"))
    viradas = [m for m in MOEDAS
               if leituras[m]["guarda_de_direcao"]["virou"]
               or leituras[m]["dimensoes"]["dados"]["direcao_mudou_pelo_tratamento"]]
    print("    GUARDA DE DIREÇÃO (nenhum tratamento vira a direção em silêncio): %s"
          % (", ".join(viradas) if viradas else
             "nenhuma moeda teve a direção mudada por tratamento — soma tratada = soma crua "
             "nas 8, deslocamento 0,00"))

    pares = le_pares(leituras, bancos)
    conta = Counter(r["estado"] for r in pares)
    neg = [r for r in pares if r["sinal"] in ("BULL", "BEAR")]
    print()
    print("  leitura contínua por moeda (-1 a +1): %s" % "  ".join("%s %+.2f" % (m, leituras[m]["score"]) for m in MOEDAS))
    print("  FAIXAS (provisórias): sem_tese %d · observação %d · moderada %d · forte %d"
          % (conta.get("sem_tese", 0), conta.get("observacao", 0),
             conta.get("moderada", 0), conta.get("forte", 0)))
    dist_faixas = distribuicao_depois(conta, agora.date().isoformat())
    _a = dist_faixas["antes"]
    print("  ANTES da fala sair do voto (%s, 3 dimensões, teto do par %.2f): sem_tese %d · "
          "observação %d · moderada %d · forte %d"
          % (_a["quando"], _a["teto_do_par"], _a["sem_tese"], _a["observacao"],
             _a["moderada"], _a["forte"]))
    print("  → %s. Os dois efeitos contrários (denominador 1,50→1,00 sobe a divergência; a "
          "parcela de fala fora do numerador desce) quase se cancelaram NESTE calendário — "
          "não é prova de que a escala ficou igual." % dist_faixas["o_que_mudou"])
    _r = dist_faixas["antes_da_regua_de_surpresa"]
    print("  ANTES do corte absoluto por família (mesma janela, régua relativa, %d%% das "
          "divulgações em linha): sem_tese %d · observação %d · moderada %d · forte %d"
          % (_r["em_linha_pct"], _r["sem_tese"], _r["observacao"], _r["moderada"], _r["forte"]))
    print("  → %s. O painel ficou MAIS sensível porque parou de apagar 3 em cada 4 "
          "divulgações; as faixas foram desenhadas na escala muda e estão desalinhadas até o "
          "backtest — leia a ORDEM dos pares, não a palavra da faixa."
          % dist_faixas["o_que_a_regua_mudou"])
    _w = dist_faixas["antes_do_conserto_da_soma_08set"]
    print("  ANTES do conserto da soma (08/set, MESMO calendário e MESMO instante, com "
          "winsorização por item): sem_tese %d · observação %d · moderada %d · forte %d"
          % (_w["sem_tese"], _w["observacao"], _w["moderada"], _w["forte"]))
    print("  → %s. Tirar o corte de dentro da soma devolveu a direção ao dado: o USD saiu de "
          "'inclinado ao corte' (soma -8,29 fabricada) para SEM LEITURA (soma crua -1,19), e o "
          "CAD saiu de 'sem leitura' (soma -1,81 apagada) para 'inclinado ao corte' (soma crua "
          "-4,80), agora com BANDEIRA de dominância e evidência fraca."
          % dist_faixas["o_que_o_conserto_da_soma_mudou"])
    print("  PARES COM TESE — %d de %d" % (len(neg), len(pares)))
    print("  %-8s %-5s %-11s %-5s %-5s %-6s %-26s %s"
          % ("par", "lado", "estado", "div", "qual", "perna", "ação / motivo", "invalidante"))
    print("  " + "-" * 132)
    for r in sorted(neg, key=lambda x: -x["divergencia"]):
        inv = r["proximo_evento_invalidante"] or {}
        print("  %-8s %-5s %-11s %3d%%  %3s   %-6s %-26s %s %s (%s dias)"
              % (r["par"], r["sinal"], r["estado"], r["divergencia"],
                 "—" if r["qualidade_evidencia"] is None else str(r["qualidade_evidencia"]),
                 "%s %d%%" % (r["perna_dominante"]["moeda"] or "—", r["perna_dominante"]["share_pct"]),
                 r["acao"] + " · " + r["motivo"],
                 inv.get("moeda") or "—", inv.get("evento") or "", inv.get("dias")))
    print()
    print("  SEM TESE (zona neutra 0-14, continuam no arquivo): %d — %s"
          % (conta.get("sem_tese", 0),
             ", ".join("%s %d%%" % (r["par"], r["divergencia"])
                       for r in pares if r["estado"] == "sem_tese")))
    print()
    print("  ALERTAS DE DOMINÂNCIA nos pares:")
    vistos = set()
    for r in pares:
        for a in r["alertas"]:
            if a.startswith("uma única divulgação") and a not in vistos:
                vistos.add(a)
                print("    · %s" % a)
    if not vistos:
        print("    · nenhum")

    instrumentos = le_instrumentos(leituras)
    print()
    print("  INSTRUMENTOS = perna do USD invertida (leitura %+.2f); geopolítica: %s"
          % (leituras["USD"]["score"], instrumentos[0]["geo"]["estado"] if instrumentos else "?"))
    for i in instrumentos:
        c = i["score_componentes"]
        print("    %-7s %-9s div %3d%%  leitura %+.3f = usd %+.3f + geo %+.3f (se votasse %+.3f)"
              % (i["simbolo"], i["sinal"], i["divergencia"], i["score"], c["usd_invertido"],
                 c["geopolitica"], c["geopolitica_se_votasse"]))

    rel = {
        "gerado_em": agora.isoformat(),
        "gerado_em_brt": (brt(agora.isoformat()).strftime("%d/%m/%Y %H:%M") + " (BRT)"),
        "origem_eventos": origem,
        # (D) FRESCOR NA RAIZ — prioridade 2 do dono: nao exibir leitura operacional com dado
        # atrasado. A interface le daqui para pintar o aviso do topo e acinzentar as linhas.
        "frescor": frescor,
        "regua": {
            "dimensoes": ["dados", "texto", "ciclo", "geo"],
            "dimensoes_que_votam": list(DIMENSOES_QUE_VOTAM),
            "dimensoes_que_nao_votam": {
                "texto": {"selo": SELO_NAO_VOTA, "desde": "2026-09-05",
                          "por_que": por_que_a_fala_nao_vota()},
                "geo": {"selo": "experimental — contexto, não vota", "desde": "2026-09-05",
                        "por_que": "regra declarada sobre intensidade de notícia e nunca "
                                   "medida"}},
            "teto_por_moeda": TETO_MOEDA,
            "teto_por_par": TETO_PAR,
            # A CONSEQUENCIA ESCRITA, EM NUMEROS — o dono pediu que estivesse na regua.
            "mudanca_de_escala_05set": {
                "o_que_mudou": "a dimensão de FALA parou de votar nas OITO moedas (antes USD, "
                               "EUR, GBP e CAD votavam por contagem de palavras, com peso "
                               "1,0; JPY, AUD, NZD e CHF já pesavam 0,0 por serem manchete)",
                "dimensoes_que_votam": "3 -> 2 (dados e ciclo)",
                "teto_por_moeda": "0,75 -> 0,50",
                "teto_por_par": "1,50 -> 1,00",
                "conviccao_teto_pct": "75 -> 50",
                "efeito_na_divergencia": "o denominador da divergência caiu de 1,50 para "
                                         "1,00, então a MESMA diferença econômica sai 50% "
                                         "maior em pontos de divergência; ao mesmo tempo a "
                                         "leitura contínua de cada perna encolhe, porque a parcela de "
                                         "fala saiu do numerador. Os dois efeitos andam em "
                                         "sentidos contrários e NÃO se cancelam.",
                "distribuicao_das_faixas_antes_e_depois": dist_faixas,
                "aviso": "as faixas provisórias (0-14 / 15-24 / 25-39 / 40+) foram desenhadas "
                         "na escala VELHA e ficam desalinhadas até o backtest. Enquanto isso, "
                         "a distribuição das faixas não é comparável com a de antes de "
                         "05/set — está declarado, não escondido.",
                "confiabilidade_da_evidencia": "a parte 'confiabilidade' da qualidade da "
                                               "evidência media o peso da FONTE DE FALA e "
                                               "saiu da conta pela mesma lei (o que não vota "
                                               "não é evidência): agora a nota é a média de "
                                               "3 partes, não de 4.",
                "provisorio": True},
            "peso_por_dimensao_pct": PESO_DIM,
            "janela_dias": JANELA_DIAS, "meia_vida_dias": MEIA_VIDA, "limiar_dados": LIMIAR_DADOS,
            "geo_z_corte": GEO_Z_CORTE,
            "faixas_provisorias": FAIXAS_PROVISORIAS,
            "faixas_provisorias_nota": "divergência 0-100: 0-14 sem tese · 15-24 observação · "
                                       "25-39 moderada · 40+ forte. Faixas PROVISÓRIAS do dono "
                                       "(05/set), a calibrar no backtest.",
            # (B) zona SEM LEITURA por moeda e (C) rótulo de evidência — provisórios
            "faixas_leitura_provisorias": FAIXAS_LEITURA_PROVISORIAS,
            "faixas_evidencia_provisorias": {
                "faixas": FAIXAS_EVIDENCIA_PROVISORIAS,
                "texto": "qualidade da evidência 0-100 vira palavra: fraca <40 · moderada "
                         "40-69 · forte >=70. Faixas PROVISÓRIAS, para a tela mostrar "
                         "'Evidência: moderada' no lugar de um número.",
                "provisorio": True},
            "frescor_limiares_provisorios": {
                "limiares": FRESCOR_LIMIARES,
                "texto": "atraso do dado mais velho que alimenta a leitura: até 45 min ok, "
                         "45-120 min atrasado, acima de 120 min muito atrasado (e aí "
                         "bloqueia_leitura=true). Números PROVISÓRIOS: o cron roda a cada 15 "
                         "minutos, então 45 min são três ciclos perdidos.",
                "provisorio": True},
            "proximo_evento_relevante": {
                "familias": FAMILIAS_RELEVANTES,
                "horizonte_dias": HORIZONTE_FRENTE_DIAS,
                "texto": "o próximo DADO de impacto alto que ainda não saiu (CPI, emprego, "
                         "salários, PIB, vendas no varejo, PMI). É diferente da próxima "
                         "DECISÃO: o evento relevante diz até quando vale procurar BO + ZOI, "
                         "e a reunião é o limite final do ciclo. Quando não há nenhum de "
                         "impacto alto no horizonte, cai para impacto médio com "
                         "'reserva': true; quando não há nem isso, sai null.",
                "provisorio": True},
            "geo_nao_vota": "a geopolítica saiu do voto em 05/set/2026, decisão que SUBSTITUI a "
                            "de 04/set ('quero que utilize as notícias'). Motivo: regra "
                            "declarada e nunca medida, mexendo em leitura de verdade (o NZD "
                            "saía com teto 1,00 por um z de energia de 1,85). Fica com selo "
                            "experimental, vota:false, fora da leitura contínua e fora do teto — o teto "
                            "máximo por moeda passou a 0,75, e a 0,50 quando a fala saiu do "
                            "voto na tarde do mesmo dia. O conteúdo "
                            "continua calculado e gravado para exibição.",
            "pesos_de_fala": {"pesos": PESOS_DE_FALA,
                              "onde_entra": "NÃO ENTRA MAIS EM LUGAR NENHUM DA CONTA desde "
                                            "a tarde de 05/set, quando a fala parou de votar: "
                                            "peso_aplicado é 0,0 nas oito moedas e a parte "
                                            "'confiabilidade' saiu da qualidade da evidência. "
                                            "A régua fica gravada (peso_se_votasse) para o "
                                            "dia em que o classificador for validado. Até "
                                            "05/set o peso entrava na LEITURA CONTÍNUA e na "
                                            "QUALIDADE DA EVIDÊNCIA (componente "
                                            "confiabilidade). MANCHETE PESA ZERO: não vota, "
                                            "não entra no teto e não conta como MANTEM — fica "
                                            "só como contexto na tela. A única imprensa que "
                                            "vota é a que traz dirigente NOMEADO com verbo de "
                                            "fala e veículo acima do limiar (origem "
                                            "imprensa_com_fala), e pesa 0,4.",
                              "provisorio": True},
            # ⚠️ CONSERTO DE 08/set — a winsorização por item foi REVOGADA. O que existe no
            # lugar: soma crua + dominância como régua de CONFIANÇA + guarda de direção.
            "tratamento_da_soma": {
                "nome": TRATAMENTO_DA_SOMA,
                "texto": "a dimensão de dados é a SOMA das contribuições reais (peso da "
                         "família × modulador de impacto × decaimento por idade). Nenhum termo "
                         "é cortado, aparado ou reescalado DEPOIS de classificado.",
                "o_que_este_campo_NAO_cobre": "a FAIXA NEUTRA, que roda ANTES: divulgação "
                         "dentro do corte da família entra na soma como ZERO. É um PISO em "
                         "termos de uma soma — a mesma aritmética da winsorização, por baixo. "
                         "Ela continua ligada porque tem tese econômica e é a régua única da "
                         "casa, mas parou de ser invisível: cada moeda publica "
                         "dimensoes.dados.faixa_neutra com os itens zerados, o peso que eles "
                         "teriam e a direção com a faixa em 0x, 0,5x, 1x e 2x. Quando a "
                         "direção depende dela, sai bandeira na moeda e alerta no par.",
                "faixa_neutra": FAIXA_NEUTRA,
                "por_que": "cortar termos de uma soma desloca o TOTAL pelo tanto cortado, no "
                           "sentido contrário ao do item cortado. Quando os itens grandes "
                           "estão do mesmo lado — o caso do dólar em 08/set, com os três "
                           "maiores altistas e de impacto alto — o corte tira peso de UM LADO "
                           "SÓ e a leitura anda para o outro. Peso relativo é problema de "
                           "PARTICIPAÇÃO e se resolve na CONFIANÇA, não nos termos da soma.",
                "winsor_revogada": WINSOR_REVOGADA,
                "reescala_proporcional": {
                    "ligada": False,
                    "o_que_seria": "multiplicar TODOS os itens pelo mesmo fator — a única forma "
                                   "de limitar peso que preserva o sinal e as proporções",
                    "por_que_nao_resolve_dominancia": "a participação do maior item é "
                        "|x_max|·k / Σ|x_i|·k = |x_max| / Σ|x_i|: o fator comum CANCELA. "
                        "Nenhum k derruba a participação de 100% do NZD para abaixo de 50%. "
                        "Reescalar limita MAGNITUDE; o pedido do dono é sobre PARTICIPAÇÃO.",
                    "por_que_tambem_nao_e_neutra": "o limiar de %s é fixo, então encolher tudo "
                                                   "por um fator comum empurra moedas de "
                                                   "SOBE/CORTA para MANTÉM sem que nenhum dado "
                                                   "tenha mudado." % LIMIAR_DADOS},
                "prova_sintetica": prova_do_tratamento(),
                "grava_sempre": ["soma_crua", "soma_tratada",
                                 "participacao_maior_item_antes",
                                 "participacao_maior_item_depois",
                                 "direcao_mudou_pelo_tratamento", "bandeira_de_direcao"],
                "provisorio": True},
            "dominancia": {
                "corte_participacao_pct": DOMINANCIA["corte_participacao_pct"],
                "o_que_mede": DOMINANCIA["o_que_mede"],
                "o_que_faz": DOMINANCIA["o_que_faz"],
                "por_que_o_teto_e_100_menos_a_participacao":
                    DOMINANCIA["por_que_o_teto_e_100_menos_a_participacao"],
                "nunca_muda_a_direcao": True,
                "provisorio": True},
            "guarda_de_direcao": {
                "lei": "NENHUM TRATAMENTO VIRA A DIREÇÃO EM SILÊNCIO. Se qualquer "
                       "transformação mudar a direção da leitura em relação ao cru, o campo "
                       "sai com bandeira e texto, e a moeda vai para SEM LEITURA até alguém "
                       "decidir — leitura cuja direção depende do tratamento não é leitura, é "
                       "escolha de método, e escolha de método é do dono.",
                "desde": "2026-09-08",
                "onde_vale": ["dimensão de dados (direcao_crua × direcao)",
                              "leitura da moeda (leitura_crua × leitura)"],
                "onde_NAO_alcanca": "o que acontece ANTES da classificação. A soma que a "
                                    "guarda chama de 'crua' já passou pela FAIXA NEUTRA, pelo "
                                    "modulador de impacto e pelo decaimento. Medido em 08/set: "
                                    "a faixa neutra sozinha decide a direção do USD (com ela "
                                    "MANTÉM, sem ela CORTA), e o campo `faixa_neutra` de cada "
                                    "moeda é quem cobre esse trecho.",
                "o_que_a_originou": "a winsorização virou a direção do USD (MANTÉM→CORTA) e do "
                                    "GBP (MANTÉM→CORTA) em 08/set, e o painel publicou as duas "
                                    "como se fossem leitura do dado.",
                "provisorio": True},
            "ciclo_decaimento": {"meia_vida_dias": CICLO_MEIA_VIDA_DIAS,
                                 "meia_vida_reunioes": CICLO_MEIA_VIDA_REUNIOES,
                                 "meia_vida_reunioes_ligada": False,
                                 "reunioes_no_decaimento": False,
                                 "por_que_desligada": "a contagem so ve as reunioes que o arquivo listava olhando para frente e que ja passaram — media a cadencia do arquivo, nao a do banco. Religa quando bancos_centrais.py guardar o historico.",
                                 "piso_para_votar": CICLO_PISO_VOTO,
                                 "substitui": "CICLO_VALIDADE_DIAS = 180, que era um penhasco "
                                              "(179 dias valia 0,25 cheio, 181 valia zero)",
                                 "provisorio": True},
            # ⚠️ desde a tarde de 05/set a nota é a média das partes QUE TÊM DADO, e a parte
            # "confiabilidade" está DESLIGADA nas oito moedas (ela media o peso da fonte de
            # FALA, e a fala parou de votar — o que não vota não é evidência). A régua dizia
            # "quatro partes de 25%" e isso já não descrevia a conta.
            "qualidade_evidencia": {"partes_ativas": ["quantidade", "diversidade",
                                                      "atualidade"],
                                    "partes_desligadas": {
                                        "confiabilidade": "media o peso da FONTE DE FALA; sai "
                                                          "null desde 05/set, porque a fala "
                                                          "não vota. Religa junto com o voto "
                                                          "da fala, quando o classificador "
                                                          "for validado."},
                                    "como_soma": "a nota é a MÉDIA SIMPLES das partes com "
                                                 "dado, não uma soma de fatias fixas: parte "
                                                 "sem dado baixa o denominador em vez de "
                                                 "contar como zero (silêncio não é voto). "
                                                 "Com as três partes ativas de hoje, cada uma "
                                                 "pesa 1/3 quando todas têm dado.",
                                    "satura_em_itens": QUALIDADE_N_SATURA,
                                    "rotulos_provisorios": FAIXAS_EVIDENCIA_PROVISORIAS,
                                    "no_par": "vale a MENOR das duas pernas — o elo fraco manda",
                                    "provisorio": True},
            "conviccao_historica": NOTA_CONVICCAO_HISTORICA,
            "sem_yield": "nenhuma dimensão usa yield — decisão do dono, repetida em 04/set/2026",
            "nao_conectado": {
                "texto": "Fed, BCE, BoE, BoJ e BoC ligados; RBA e RBNZ devolvem 403 e o SNB não "
                         "tem feed — nessas três a dimensão de fala cai para MANCHETE de "
                         "imprensa, que vale zero na confiabilidade",
                "geo": "intensidade de notícia do GDELT; regra declarada, experimental, SEM VOTO "
                       "desde 05/set/2026"},
        },
        "aviso": "é uma LEITURA do lado fundamental de cada perna, não um sinal. Divergência é a "
                 "diferença econômica entre as pernas contra o teto TEÓRICO (1,00 desde que a "
                 "fala saiu do voto, em 05/set — era 1,50); qualidade da "
                 "evidência diz o quanto se sabe; convicção histórica é null porque não existe "
                 "backtest. Dimensão ausente ou quieta baixa o teto, nunca conta como zero. "
                 "O FUND v0.1 foi encerrado como regra de entrada depois de 15 testes nulos.",
        "moedas": leituras,
        "pares": pares,
        "instrumentos": instrumentos,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              allow_nan=False)
    fn_snap, n_snap = grava_snapshots(pares, leituras, agora, origem)
    print()
    print("  gravado: %s" % SAIDA)
    print("  snapshot (imutável, só acrescenta): %s — %d linhas" % (fn_snap, n_snap))


if __name__ == "__main__":
    main()
