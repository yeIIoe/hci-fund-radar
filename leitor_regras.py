# -*- coding: utf-8 -*-
"""LEITOR — o que cada dado divulgado significa para o banco central.

NAO E ESTRATEGIA. E um interprete: recebe o dado no instante da divulgacao, compara com a
previsao, e diz o que aquilo empurra na decisao do banco central. Depois cruza as duas moedas
do par e responde a pergunta do Eduardo: NEGOCIA ou NAO NEGOCIA.

REGRA DE OURO DESTE ARQUIVO
    Nenhum yield. Nenhuma curva. Nenhum dado de D-1.
    So o que foi divulgado, contra o que se esperava, no instante em que sai.

O QUE ELE PODE E O QUE NAO PODE ALEGAR
    PODE: ser explicito, rapido, consistente e auditavel — toda leitura aponta para quais
          dados a produziram e com que peso.
    NAO PODE: alegar que ganha dinheiro. Nao ha consenso historico point-in-time para
          backtestar (levantamento de 01/set: nenhum fornecedor comprovou entregar isso).
          Este arquivo e uma INTERPRETACAO declarada, nao uma medicao validada.
          A validacao possivel e outra: o leitor acertou o que o BC de fato fez?
          Isso se acumula para frente, reuniao a reuniao.

COMO LER O SINAL
    +1 empurra para APERTO (alta de juro / manter mais alto por mais tempo)
    -1 empurra para AFROUXAMENTO (corte / manter mais baixo)
     0 neutro

    O sinal do indicador diz para que lado a SURPRESA empurra:
      sinal +1  ->  veio ACIMA do esperado = hawkish  (ex: CPI, PMI, emprego criado)
      sinal -1  ->  veio ACIMA do esperado = dovish   (ex: desemprego, pedidos de auxilio)
"""
from __future__ import annotations

# ---------------------------------------------------------------------------------------
# 1) O QUE CADA FAMILIA DE INDICADOR SIGNIFICA
#
# peso: quanto o banco central realmente olha para aquilo. Inflacao manda; pesquisa de
#       sentimento e ruido comparada a ela. Os pesos sao JULGAMENTO DECLARADO, nao medidos —
#       e e por isso que estao aqui em cima, visiveis, para o Eduardo discordar.
# ---------------------------------------------------------------------------------------

FAMILIAS = {
    # ---------------- INFLACAO — o mandato. Peso maximo.
    "inflacao_nucleo": {
        "peso": 10, "sinal": +1,
        # ⚠️ dois vocabularios: o Forex Factory escreve "core cpi"; a FXStreet escreve
        # "Core Consumer Price Index" e "Core Harmonized Index of Consumer Prices".
        # Sem os dois, nenhum nucleo da FXStreet casava — conferido em 02/set contra os
        # 96 titulos HIGH/MEDIUM da semana.
        "padroes": ["core cpi", "core inflation", "trimmed mean", "core pce", "core hicp",
                    "median cpi", "core ppi", "core consumer price", "core harmonized",
                    "core personal consumption", "core producer price",
                    "ex food", "excluding food", "ex-food"],
        "porque": "What the central bank actually targets. Core above forecast is the strongest "
                  "case for tightening there is: it removes the 'it was energy and food' alibi.",
    },
    "inflacao_cheia": {
        "peso": 7, "sinal": +1,
        # "prices paid" e o sub-indice de precos do ISM — conta como inflacao, nao como
        # atividade, e por isso esta AQUI e nao no pmi (a ordem de casamento garante).
        "padroes": ["cpi", "hicp", "inflation rate", "ppi", "rpi", "consumer price index",
                    "harmonized index of consumer prices", "producer price index",
                    "prices paid", "personal consumption expenditures", "deflator",
                    "prices index", "price index"],
        "porque": "It matters, but the central bank discounts energy and food shocks. A high "
                  "headline with a well-behaved core weighs LESS than the number suggests.",
    },
    "expectativa_inflacao": {
        "peso": 6, "sinal": +1,
        "padroes": ["inflation expectations", "inflation gauge", "5-year", "breakeven"],
        "porque": "Central banks fear de-anchoring more than the current level. Rising expectations "
                  "trigger tightening even while current inflation falls.",
    },

    # ---------------- MERCADO DE TRABALHO — o segundo mandato (e o unico do Fed junto com preco)
    "emprego_criacao": {
        "peso": 8, "sinal": +1,
        "padroes": ["non-farm employment", "nfp", "employment change", "payrolls",
                    "job gains", "adp", "net change in employment", "job openings"],
        "porque": "A tight labour market sustains wages and services, the stubborn part of "
                  "inflation. Strong reading = hawkish.",
    },
    "desemprego": {
        "peso": 8, "sinal": -1,   # ACIMA do esperado = mercado fraco = DOVISH
        # "unemployment change" fica AQUI (sinal invertido), senao cai em "employment change"
        # e le desemprego subindo como criacao de emprego — revisao de 03/set
        "padroes": ["unemployment rate", "jobless rate", "u-rate", "unemployment change",
                    "unemployment"],
        "porque": "INVERTED sign: unemployment above forecast means slack, and slack removes "
                  "the urgency to tighten.",
    },
    "salarios": {
        "peso": 9, "sinal": +1,
        "padroes": ["average earnings", "wage", "labor cost", "shunto", "hourly earnings",
                    "employment cost", "cash earnings"],
        "porque": "The link between labour and services inflation. For the BoJ and the BoE it is "
                  "the number they publicly say they are waiting for.",
    },
    "auxilio_desemprego": {
        "peso": 3, "sinal": -1,
        "padroes": ["jobless claims", "unemployment claims", "continuing claims"],
        "porque": "High frequency and noisy. Useful for a turn in trend, not for a level.",
    },

    # ---------------- ATIVIDADE — decide o RITMO do aperto, nao a direcao
    "pmi": {
        "peso": 5, "sinal": +1,
        "padroes": ["pmi", "ism", "purchasing managers"],
        "porque": "A survey, not hard data, and it lands before everything else. Above 50 means "
                  "expansion. Useful for DIRECTION and EARLINESS, not magnitude. "
                  "The PRICES PAID sub-index counts as inflation, not as activity.",
    },
    "pib": {
        "peso": 6, "sinal": +1,
        "padroes": ["gdp", "gross domestic product"],
        "porque": "Confirms the state, but it is LATE — it covers a quarter that already ended. "
                  "It moves the decision little, because the bank already saw the monthly parts.",
    },
    "varejo": {
        "peso": 4, "sinal": +1,
        "padroes": ["retail sales", "consumer spending", "household spending", "retail trade",
                    "retailer sales"],
        "porque": "Domestic demand, which is what the policy rate actually controls.",
    },
    "producao": {
        "peso": 3, "sinal": +1,
        "padroes": ["industrial production", "manufacturing production", "factory orders"],
        "porque": "Lower weight in a service economy; still matters in Germany and Japan.",
    },
    "confianca": {
        "peso": 2, "sinal": +1,
        "padroes": ["confidence", "sentiment", "zew", "ifo", "gfk"],
        "porque": "A mood survey. It leads, but it misses often. Low weight on purpose.",
    },
    "moradia": {
        "peso": 3, "sinal": +1,
        "padroes": ["housing", "building permits", "home sales", "building consents",
                    "house price"],
        "porque": "The channel most sensitive to rates — it reacts first when tightening bites.",
    },

    # ---------------- EXTERNO — pesa pouco, salvo em economia aberta
    "balanca": {
        "peso": 2, "sinal": +1,
        "padroes": ["trade balance", "current account", "exports", "imports"],
        "porque": "Low weight except in AUD, NZD and CAD, where terms of trade genuinely matter.",
    },

    # A COLETIVA — separada da decisao de proposito.
    # Medido em 08/jul/2026: no RBNZ a decisao (14:00 NZ) moveu 57,5 pips num minuto e a
    # coletiva (15:00 NZ) moveu 3,9 pips. Mas no BCE a literatura mede o oposto (Altavilla
    # et al., JME 2019): na janela do comunicado so o alvo aparece; na janela da COLETIVA
    # surgem Timing, Forward Guidance e QE, com volatilidade muito maior.
    # ⚠️ Ou seja: qual dos dois manda depende do BANCO CENTRAL, e tem que ser medido por banco,
    # nunca assumido. Peso 0 ate termos a medicao de cada um.
    "coletiva": {
        "peso": 0, "sinal": +1,
        "padroes": ["press conference", "gov ", "governor speaks", "chair", "president speaks",
                    "testifies", "speech", "hearings", "testimony"],
        "porque": "Where the GUIDANCE usually appears. Weight is 0 because how much it matters "
                  "varies by central bank — measure before scoring.",
    },

    # ---------------- A PROPRIA DECISAO — nao e dado, e o desfecho
    "decisao": {
        "peso": 0, "sinal": +1,      # peso 0: nao entra no acumulado, ZERA o ciclo
        "padroes": ["official cash rate", "cash rate", "rate statement", "interest rate decision",
                    "policy rate", "monetary policy statement", "fomc statement", "bank rate",
                    "overnight rate", "ocr", "refi rate", "deposit facility",
                    "monetary policy review", "monetary policy decision",
                    "main refinancing", "refinancing operations rate", "marginal lending"],
        "porque": "It does not feed the running score — it CLOSES the cycle. What matters "
                  "here is the outcome against expectations and, above all, the GUIDANCE. "
                  "On 8 Jul 2026 the RBNZ hike was already priced and price moved only on "
                  "the guidance — which came in the STATEMENT at 14:00 NZ, not in the press "
                  "conference at 15:00, which moved nothing (3.9 pips of range).",
    },
}


# ---------------------------------------------------------------------------------------
# 2) O QUE MODULA O PESO — o mesmo dado nao vale o mesmo sempre
# ---------------------------------------------------------------------------------------

MODULADORES = {
    "impacto_alto":   1.0,    # o calendario marca alto impacto
    "impacto_medio":  0.5,
    "impacto_baixo":  0.2,

    # ⚠️ O Eduardo levantou isto e esta certo: a relacao inflacao-desemprego se comporta
    # diferente quando o choque e EXTERNO. Em 2021-22 inflacao e desemprego subiram juntos
    # porque a inflacao era de oferta, nao de demanda. Um leitor que assume Phillips
    # mecanicamente le errado exatamente nos periodos que mais importam.
    # Por isso o cruzamento inflacao x emprego NAO e automatico — fica declarado como
    # observacao para o Eduardo julgar, nunca como regra que soma sozinha.
    "phillips_automatico": False,

    # Quanto o dado envelhece dentro do ciclo: dado de 5 semanas atras pesa menos que o de
    # ontem para a decisao da semana que vem.
    "meia_vida_dias": 21,
}


# ---------------------------------------------------------------------------------------
# 3) A REGRA DO PAR — a pergunta do Eduardo, literalmente
#
#   "se os dois vao subir os juros eu nao negocio o par;
#    se um vai subir e outro vai manter eu negocio"
# ---------------------------------------------------------------------------------------

def veredito_do_par(leitura_base: str, leitura_cotada: str) -> dict:
    """leitura_* e uma de: SOBE, MANTEM, CORTA.

    Devolve se negocia, a direcao, e o motivo — em texto que o Eduardo le em 2 segundos.
    """
    ordem = {"CORTA": -1, "MANTEM": 0, "SOBE": +1}
    b, q = ordem[leitura_base], ordem[leitura_cotada]
    delta = b - q

    if delta == 0:
        return {
            "negocia": False,
            "direcao": None,
            "forca": "nenhuma",
            "motivo": "os dois bancos centrais na mesma direcao (%s) — sem divergencia, "
                      "sem tese fundamental" % leitura_base,
        }

    direcao = "COMPRA" if delta > 0 else "VENDE"
    forca = {1: "fraca", 2: "forte"}[abs(delta)]
    return {
        "negocia": True,
        "direcao": direcao,
        "forca": forca,
        "motivo": "base %s x cotada %s — divergencia de %d grau(s)"
                  % (leitura_base, leitura_cotada, abs(delta)),
    }


# ---------------------------------------------------------------------------------------
# 4) O QUE AINDA FALTA PARA ISTO RODAR AO VIVO — declarado, nao escondido
# ---------------------------------------------------------------------------------------

BURACOS = [
    "O feed semanal do Forex Factory NAO traz o campo do RESULTADO. Ele da previsao e "
    "anterior dos eventos futuros (38 de 61 com previsao), mas nao o valor divulgado. "
    "Sem uma fonte do resultado NO INSTANTE, o leitor nao dispara.",

    "Taxa de politica e data da proxima reuniao das 8 moedas — em levantamento. Sem isso o "
    "leitor nao sabe dizer 'mantem em 3,75%' nem quanto falta para a decisao.",

    "Calendario do BoJ nao existe em formato estruturado em lugar nenhum. Dos 8 bancos "
    "centrais, so SNB e BoC publicam data de decisao em feed.",

    "Os PESOS acima sao julgamento declarado, nao medidos. Nao ha consenso historico "
    "point-in-time para calibra-los. Eles existem para o Eduardo discordar e ajustar.",
]
