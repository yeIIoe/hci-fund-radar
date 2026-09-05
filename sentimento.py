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
             dias. Um empurrao de 30 dias atras vale ~37% de um de hoje. Desde 05/set cada
             item entra WINSORIZADO: nenhuma divulgacao sozinha carrega a dimensao. Moeda
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
    scores das pernas encolhem, porque a parcela de fala saiu do numerador. Os dois efeitos
    andam em sentidos contrarios e nao se cancelam: as faixas provisorias (0-14 / 15-24 /
    25-39 / 40+) FORAM CALIBRADAS NA ESCALA VELHA e ficam desalinhadas ate o backtest.
    Isto esta dito aqui, na regua (regua.mudanca_de_escala_05set) e no relatorio.

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

REGUAS DECLARADAS (grossas de proposito — fino sem calibracao e falsa precisao)
    LIMIAR_DADOS = 5,0 na soma decaida: abaixo disso o fluxo de dados le MANTEM.
    Uma DECISAO dentro da janela zera o acumulado: so contam eventos depois dela.
    WINSOR: cada divulgacao entra com no maximo 4,0 em modulo — 0,8 do limiar. Como 4,0 e
    ESTRITAMENTE menor que 5,0, nenhuma divulgacao sozinha atinge o limiar: sao precisas
    duas. Isto e aritmetica do teto, nao observacao de um dia.
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
from macro_eventos import familia_de, classifica, empurrao, IMPACTO_FXS  # noqa: E402
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

# (4) winsorizacao por item: teto por divulgacao dentro da dimensao de dados.
#
# HISTORICO DAS DUAS VERSOES — a primeira foi REPROVADA por medicao, nao por gosto.
#
# VERSAO 1 (manha de 05/set): teto = min(2,5 x mediana absoluta da moeda ; 5,0). A auditoria
# do mesmo dia derrubou os dois pilares dela:
#   (i)  A PROMESSA ERA FALSA. O teto absoluto era o PROPRIO LIMIAR_DADOS (5,0) e a
#        comparacao de direcao e `soma <= -LIMIAR_DADOS`, com menor OU IGUAL. O CAD provou:
#        uma unica divulgacao (Net Change in Employment, bruta -7,82) foi cortada para
#        EXATAMENTE -5,00, bateu no limiar e virou a dimensao para CORTA sozinha, com
#        dominancia de 100% antes E depois do teto.
#   (ii) O FATOR DA MEDIANA FABRICAVA E APAGAVA DIRECAO. A mediana e calculada sobre TODOS
#        os itens da janela, e a maioria contribui quase zero depois do decaimento — entao
#        ela vive perto de 0,5 e o teto caia para ~1,2. Dois casos medidos:
#          - 1 item +7,83 com 17 itens de -0,50: mediana 0,50, teto 1,25, a soma vai de
#            -0,67 (MANTEM) para -7,25 (CORTA). O teto FABRICOU uma direcao.
#          - dois extremos legitimos do mesmo lado (-9,0 e -8,0) no meio de ruido de 0,4:
#            mediana 0,45, teto 1,12, a soma vai de -16,60 (CORTA) para -1,85 (MANTEM). O
#            teto APAGOU dois dados legitimos.
#
# VERSAO 2 (tarde de 05/set, esta) — duas mudancas, cada uma consertando um dos dois:
#   (i)  TETO ESTRITAMENTE ABAIXO DO LIMIAR: teto_absoluto = 0,8 x LIMIAR_DADOS = 4,0. Agora
#        a promessa e DEMONSTRAVEL, nao uma esperanca: o maior valor que UM item pode ter
#        depois do corte e 4,0, e 4,0 < 5,0, logo nenhuma divulgacao sozinha alcanca o
#        limiar em nenhuma moeda, em nenhum dia. Sao precisas DUAS divulgacoes.
#   (ii) O FATOR DA MEDIANA FOI RETIRADO. Refazendo os dois casos acima com teto fixo 4,0:
#          - 1 item +7,83 com 17 de -0,50: +4,0 -8,5 = -4,5 -> MANTEM, igual ao bruto. Nao
#            fabrica mais.
#          - dois extremos -9,0 e -8,0 no ruido: -4 -4 +0,4 -0,3 +0,5 -0,2 = -7,6 -> CORTA,
#            igual ao bruto. Nao apaga mais.
#        A mediana continua sendo CALCULADA e gravada (mediana_absoluta) porque e um bom
#        descritor da janela, mas nao manda mais no teto.
#
# O QUE CONTINUA VERDADE E FICA DITO: cortar termos de uma SOMA desloca o total pelo tanto
# cortado, no sentido contrario ao do item. Isso e a definicao de winsorizar, nao um bug — e
# o preco de nao deixar uma divulgacao mandar sozinha. O deslocamento sai medido em cada
# moeda, no campo `deslocamento_pelo_teto`, e o campo `direcao_antes_do_teto` mostra o que a
# soma bruta teria lido. Quem quiser auditar tem os dois numeros lado a lado.
#
# O 0,8 e PROVISORIO como todo o resto: e a menor folga que ainda deixa duas divulgacoes
# grandes virarem a leitura (2 x 4,0 = 8,0 > 5,0). Vai ao backtest junto com o limiar.
WINSOR = {
    "fator_mediana": None,
    "fator_mediana_retirado_em": "2026-09-05",
    "fator_mediana_por_que": "media na janela vive perto de 0,5 depois do decaimento, entao "
                             "2,5 x mediana derrubava o teto para ~1,2 e isso FABRICAVA "
                             "direcao (1 item +7,83 com 17 de -0,50: -0,67 virava -7,25) e "
                             "APAGAVA dado legitimo (-9,0 e -8,0 no ruido: -16,60 virava "
                             "-1,85). Medido, nao suposto.",
    "fracao_do_limiar": 0.8,
    "teto_absoluto": round(0.8 * LIMIAR_DADOS, 2),
    "provisorio": True,
    "texto": "cada divulgacao entra com no maximo 4,0 em modulo, que e 0,8 do limiar de 5,0 "
             "da dimensao. Como 4,0 < 5,0, NENHUMA divulgacao sozinha atinge o limiar: sao "
             "precisas pelo menos duas. Numero PROVISORIO, escolhido por ordem de grandeza "
             "(e a menor folga que ainda deixa duas divulgacoes grandes virarem a leitura), "
             "nao por calibracao — vai ao backtest junto com o limiar.",
    "garantia": "teto_absoluto (4,0) < limiar (5,0): uma divulgacao sozinha nunca vira a "
                "leitura. Isto e aritmetica do teto, nao observacao de um dia.",
    "aviso_auditoria": "winsorizar termos de uma SOMA desloca o total pelo tanto cortado, no "
                       "sentido contrario ao do item cortado. E o preco da regra, nao um "
                       "defeito escondido: veja `deslocamento_pelo_teto` e "
                       "`direcao_antes_do_teto` em cada moeda.",
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


# ---------------------------------------------------------------------------------------
# DIMENSAO 1 — DADOS (com winsorizacao por item e medida de dominancia)
# ---------------------------------------------------------------------------------------
def dimensao_dados(ev, moeda, agora):
    """Surpresas desde a ultima decisao, com TETO POR ITEM.

    (4) O caso do dono: o CAD tinha uma unica divulgacao de emprego com contribuicao -7,9
    respondendo por 100% da leitura de dados, com so tres divulgacoes no ciclo. Sem teto, um
    desvio extremo entra inteiro e a dimensao vira o eco de um numero so.
    """
    meus = [e for e in ev if e.get("moeda") == moeda and e.get("divulgado") is not None
            and e.get("quando_utc")]
    inicio = (agora - dt.timedelta(days=JANELA_DIAS)).isoformat()
    meus = [e for e in meus if e["quando_utc"] >= inicio and e["quando_utc"] <= agora.isoformat()]

    # a DECISAO zera o ciclo: so conta o que saiu depois da ultima
    decisoes = [e["quando_utc"] for e in meus if familia_de(e.get("titulo"))[0] == "decisao"]
    corte = max(decisoes) if decisoes else None

    n, n_alto, brutos, familias = 0, 0, [], set()
    for e in meus:
        if corte and e["quando_utc"] <= corte:
            continue
        nome, fam = familia_de(e.get("titulo"))
        if nome:
            familias.add(nome)
        if not fam or not fam.get("peso"):
            continue
        classe, dif = classifica(e.get("divulgado"), e.get("consenso"))
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
        if contrib:
            brutos.append({"quando_utc": e["quando_utc"], "titulo": e.get("titulo"),
                           "familia": nome, "classe": classe, "impacto": e.get("impacto"),
                           "divulgado": e.get("divulgado"), "consenso": e.get("consenso"),
                           "contribuicao_bruta": round(contrib, 2),
                           "contribuicao": round(contrib, 2), "idade_dias": round(idade, 1),
                           "winsorizado": False})

    # ---- winsorizacao por item -------------------------------------------------------
    # O teto e FIXO em 0,8 x limiar. A mediana continua calculada e gravada como descritor da
    # janela, mas nao manda mais no teto — ver o bloco WINSOR: o fator da mediana fabricava e
    # apagava direcao, e isso foi medido em 05/set.
    med = mediana([abs(x["contribuicao_bruta"]) for x in brutos])
    teto_item = float(WINSOR["teto_absoluto"])
    n_cortados = 0
    for x in brutos:
        c = x["contribuicao_bruta"]
        if abs(c) > teto_item:
            x["contribuicao"] = round(math.copysign(teto_item, c), 2)
            x["winsorizado"] = True
            n_cortados += 1

    soma_bruta = round(sum(x["contribuicao_bruta"] for x in brutos), 2)
    soma = round(sum(x["contribuicao"] for x in brutos), 2)
    brutos.sort(key=lambda x: -abs(x["contribuicao"]))

    # ---- dominancia: quanto o maior item responde da leitura ---------------------------
    abs_dep = sum(abs(x["contribuicao"]) for x in brutos)
    abs_ant = sum(abs(x["contribuicao_bruta"]) for x in brutos)
    share = round(abs(brutos[0]["contribuicao"]) / abs_dep * 100) if abs_dep else 0
    share_antes = round(abs(max(brutos, key=lambda x: abs(x["contribuicao_bruta"]))["contribuicao_bruta"])
                        / abs_ant * 100) if abs_ant else 0
    dominancia = {
        "alerta": bool(brutos) and share > 50,
        "item": brutos[0]["titulo"] if brutos else None,
        "share_pct": share,
        "share_pct_antes_do_teto": share_antes,
        "texto": None,
    }
    if dominancia["alerta"]:
        dominancia["texto"] = ("uma única divulgação responde por %d%% da leitura de dados do %s "
                               "(%s), com %d divulgações no ciclo"
                               % (share, moeda, brutos[0]["titulo"], n))

    direcao = "SOBE" if soma >= LIMIAR_DADOS else "CORTA" if soma <= -LIMIAR_DADOS else "MANTEM"

    # AUDITORIA 05/set: os dois efeitos que a frase antiga do WINSOR negava, medidos aqui e
    # gravados no JSON, para nunca mais precisarem de fe.
    #   virou_sozinho     a dimensao saiu de MANTEM porque UM item, mesmo depois do teto,
    #                     respondeu por mais de metade da leitura
    #   deslocamento      quanto a soma ANDOU por causa do corte, e para que lado
    maior = abs(brutos[0]["contribuicao"]) if brutos else 0.0
    # Depois da versao 2 do teto (4,0 < limiar 5,0) isto e IMPOSSIVEL por aritmetica, e fica
    # aqui como trava viva: se um dia alguem subir o teto ate o limiar de novo, o campo
    # denuncia sozinho em vez de a promessa voltar a ser falsa em silencio.
    virou_sozinho = bool(direcao != "MANTEM" and brutos and maior >= LIMIAR_DADOS - 1e-9
                         and share > 50)
    deslocamento = round(soma - soma_bruta, 2)
    dir_bruta = ("SOBE" if soma_bruta >= LIMIAR_DADOS else
                 "CORTA" if soma_bruta <= -LIMIAR_DADOS else "MANTEM")

    fam_ind = sorted({MAPA_FAMILIA[f] for f in familias if f in MAPA_FAMILIA})
    # SILENCIO NAO E VOTO (lei do dono, aplicada aqui em 05/set): moeda sem NENHUMA
    # divulgacao na janela lia "MANTEM" com soma 0,0 e contava como dimensao ligada — o NZD
    # saia com duas dimensoes votando tendo zero dado. A direcao continua exibida, mas com
    # "vota": false, e o teto da moeda cai para 0,25, o que joga a moeda em SEM LEITURA.
    return {"direcao": direcao, "direcao_antes_do_teto": dir_bruta,
            "vota": n > 0,
            "por_que_nao_vota": None if n > 0 else
            ("nenhuma divulgação do %s na janela de %d dias — silêncio não é voto: a dimensão "
             "não conta e BAIXA o teto da moeda, em vez de entrar como MANTEM" % (moeda, JANELA_DIAS)),
            "soma": soma, "soma_antes_do_teto": soma_bruta,
            "n": n, "n_alto": n_alto,
            "desde": corte or inicio[:10], "zerado_por_decisao": bool(corte),
            "limiar": LIMIAR_DADOS, "meia_vida_dias": MEIA_VIDA,
            "virou_sozinho": {
                "sim": virou_sozinho,
                "texto": ("a dimensão foi para %s com UMA divulgação sozinha: depois do teto "
                          "ela ainda vale %.2f (o limiar é %.1f) e responde por %d%% da "
                          "leitura — o teto não desmonopolizou nada"
                          % (direcao, maior, LIMIAR_DADOS, share)) if virou_sozinho else None},
            "deslocamento_pelo_teto": {
                "valor": deslocamento,
                "direcao_mudou": dir_bruta != direcao,
                "texto": ("cortar os itens moveu a soma em %+.2f (de %+.2f para %+.2f)%s — "
                          "winsorizar termos de uma SOMA desloca o total para o lado contrário "
                          "ao do item cortado, não amortece"
                          % (deslocamento, soma_bruta, soma,
                             "; a DIREÇÃO mudou de %s para %s" % (dir_bruta, direcao)
                             if dir_bruta != direcao else "")) if n_cortados else None},
            "winsor": {"teto_por_item": round(teto_item, 2),
                       "mediana_absoluta": round(med, 2),
                       "mediana_manda_no_teto": False,
                       "itens_cortados": n_cortados,
                       "regra": WINSOR["texto"],
                       "garantia": WINSOR["garantia"],
                       "aviso_auditoria": WINSOR["aviso_auditoria"], "provisorio": True},
            "dominancia": dominancia,
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
            "dimensão fica como CONTEXTO, com peso 0,0 — não entra no score, não entra no "
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
    """
    G = (geo or {}).get("moedas", {}).get(moeda)
    if not G:
        return None
    t = G.get("temas") or {}
    ze = ((t.get("energia") or {}).get("volume") or {}).get("z")
    zc = ((t.get("conflito") or {}).get("volume") or {}).get("z")
    base = {"z_energia": ze, "z_conflito": zc, "tom": G.get("tom"), "corte_z": GEO_Z_CORTE,
            "manchete": (((t.get("conflito") or {}).get("manchetes") or [{}])[0].get("titulo")),
            "vota": False, "selo": "experimental",
            "nota": "regra declarada sobre intensidade de notícia (GDELT). Contava desde "
                    "04/set; em 05/set o dono retirou o voto: regra nunca medida, e estava "
                    "mexendo em leitura de verdade. Fica visível, fora do score e fora do teto."}
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
    """Quatro partes, cada uma medida 0..100. A nota e a media das partes QUE TEM DADO.

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
    return {"nota": nota, "componentes": comp,
            "confiabilidade_da_fala_se_votasse": conf_se_votasse,
            "partes_usadas": len(usadas), "partes_sem_dado": sem_dado,
            "contexto_nao_contado": n_contexto,
            "explicacao": "qualidade %s/100 do %s (média de %d parte(s) com dado%s) — %s."
                          % ("—" if nota is None else nota, moeda, len(usadas),
                             "; sem dado em " + ", ".join(sem_dado) if sem_dado else "",
                             "; ".join(partes)),
            "provisorio": True,
            "regua": {"satura_em_itens": QUALIDADE_N_SATURA, "meia_vida_dias": MEIA_VIDA,
                      "pesos_de_fala": PESOS_DE_FALA,
                      "parte_sem_dado": "sai null e NÃO entra na média — dimensão sem dado "
                                        "baixa o denominador, nunca conta como zero",
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
    #   dados   soma decaida E WINSORIZADA, por tanh — sem teto abrupto
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

    qual = qualidade_evidencia(dd, tt, m)
    fams = set((dd or {}).get("familias_independentes") or [])
    # "comunicacao" so entra quando a fala VOTA — e ela nao vota mais.

    dom = dict((dd or {}).get("dominancia") or
               {"alerta": False, "item": None, "share_pct": 0, "texto": None})

    leitura, leitura_txt, leitura_motivo, intens_rel = zona_de_leitura(
        score, len(disponiveis), direcao,
        dimensoes_discordam=len({v["direcao"] for v in disponiveis.values()}) > 1)
    regime, regime_motivo = regime_do_banco(cc, dd, b)
    nota_q = (qual or {}).get("nota")
    if len(disponiveis) == 0:
        concord_txt = "nenhuma dimensão vota"
    elif len(disponiveis) == 1:
        # portugues de gente: "1 de 1 dimensoes concordam" nao existe
        concord_txt = ("a única dimensão que vota concorda" if concordam
                       else "a única dimensão que vota não fecha direção")
    else:
        concord_txt = "%d de %d dimensões concordam" % (concordam, len(disponiveis))

    return {
        "moeda": m, "direcao": direcao, "intensidade": intensidade,
        "score": score, "score_componentes": comp,
        "score_texto_se_votasse": texto_se_votasse,
        # teto do score = 0,25 por dimensao que VOTA — no maximo 0,50, porque a fala e a
        # geopolitica sairam do teto em 05/set.
        "score_teto": round(0.25 * len(disponiveis), 2),
        "score_teto_teorico": TETO_MOEDA,
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
        "proximo_evento_relevante": proximo_evento_relevante(m, futuros or [], agora),
        # ------------------------------------------------------------------------------
        "conviccao_pct": conv, "conviccao_teto_pct": teto,
        "dimensoes_ligadas": len(disponiveis), "dimensoes_total": len(dims),
        "dimensoes_que_votam": list(votantes),
        "dimensoes_que_nao_votam": {"texto": SELO_NAO_VOTA, "geo": "experimental"},
        "concordam": {k: (v["direcao"] == direcao) for k, v in disponiveis.items()},
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
        teto = round((lb.get("score_teto") or 0.0) + (lq.get("score_teto") or 0.0), 2)
        diverg = round(abs(diff) / teto_teorico * 100) if teto_teorico > 0 else 0
        diverg_ligado = round(abs(diff) / teto * 100) if teto > 0 else 0
        estado = estado_da_divergencia(diverg)

        if estado == "sem_tese":
            sinal, rotulo = "SEM_TESE", "sem tese"
            acao = "Sem tese"
        else:
            sinal = "BULL" if diff > 0 else "BEAR"
            rotulo = {"observacao": "observação", "moderada": "moderada", "forte": "forte"}[estado]
            acao = "%s %s/%s" % ("Compra" if diff > 0 else "Venda", b, q)

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

        alertas = []
        for m, L in ((b, lb), (q, lq)):
            d = L.get("dominancia") or {}
            if d.get("alerta") and d.get("texto"):
                alertas.append("uma única divulgação responde por %d%% da leitura do %s (%s)"
                               % (d.get("share_pct") or 0, m, d.get("item")))
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
            "motivo": "%s %+.2f contra %s %+.2f" % (b, sb, q, sq),
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
        teto_ligado = round(u.get("score_teto") or 0.0, 2)
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
    print("  regras novas de 05/set: FALA e geopolítica NÃO votam (teto 0,50) · ciclo com decaimento · "
          "winsorização por item · zona neutra 0-14")

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
                 ("%s (energia z=%s, conflito z=%s)" % (gg["estado"], gg["z_energia"], gg["z_conflito"]))
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
    print("  DOMINÂNCIA — quanto o maior item responde da dimensão de dados (teto por item %s)"
          % WINSOR["teto_absoluto"])
    for m in MOEDAS:
        dd = leituras[m]["dimensoes"]["dados"]
        d = dd["dominancia"]
        print("    %-4s soma %+6.2f (antes do teto %+6.2f) · maior item %3d%% (antes %3d%%) · "
              "cortados %d · %s"
              % (m, dd["soma"], dd["soma_antes_do_teto"], d["share_pct"],
                 d["share_pct_antes_do_teto"], dd["winsor"]["itens_cortados"],
                 "ALERTA" if d["alerta"] else "ok"))

    pares = le_pares(leituras, bancos)
    conta = Counter(r["estado"] for r in pares)
    neg = [r for r in pares if r["sinal"] in ("BULL", "BEAR")]
    print()
    print("  leitura contínua por moeda (-1 a +1): %s" % "  ".join("%s %+.2f" % (m, leituras[m]["score"]) for m in MOEDAS))
    print("  FAIXAS (provisórias): sem_tese %d · observação %d · moderada %d · forte %d"
          % (conta.get("sem_tese", 0), conta.get("observacao", 0),
             conta.get("moderada", 0), conta.get("forte", 0)))
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
                                         "maior em pontos de divergência; ao mesmo tempo os "
                                         "scores das pernas encolhem, porque a parcela de "
                                         "fala saiu do numerador. Os dois efeitos andam em "
                                         "sentidos contrários e NÃO se cancelam.",
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
                            "experimental, vota:false, fora do score e fora do teto — o teto "
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
                                            "05/set o peso entrava no SCORE e na "
                                            "QUALIDADE DA EVIDÊNCIA (componente "
                                            "confiabilidade). MANCHETE PESA ZERO: não vota, "
                                            "não entra no teto e não conta como MANTEM — fica "
                                            "só como contexto na tela. A única imprensa que "
                                            "vota é a que traz dirigente NOMEADO com verbo de "
                                            "fala e veículo acima do limiar (origem "
                                            "imprensa_com_fala), e pesa 0,4.",
                              "provisorio": True},
            "winsor": WINSOR,
            "ciclo_decaimento": {"meia_vida_dias": CICLO_MEIA_VIDA_DIAS,
                                 "meia_vida_reunioes": CICLO_MEIA_VIDA_REUNIOES,
                                 "meia_vida_reunioes_ligada": False,
                                 "reunioes_no_decaimento": False,
                                 "por_que_desligada": "a contagem so ve as reunioes que o arquivo listava olhando para frente e que ja passaram — media a cadencia do arquivo, nao a do banco. Religa quando bancos_centrais.py guardar o historico.",
                                 "piso_para_votar": CICLO_PISO_VOTO,
                                 "substitui": "CICLO_VALIDADE_DIAS = 180, que era um penhasco "
                                              "(179 dias valia 0,25 cheio, 181 valia zero)",
                                 "provisorio": True},
            "qualidade_evidencia": {"partes": ["quantidade", "diversidade", "atualidade",
                                               "confiabilidade"],
                                    "cada_parte_vale_pct": 25,
                                    "satura_em_itens": QUALIDADE_N_SATURA,
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
