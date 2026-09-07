# -*- coding: utf-8 -*-
"""
HCI — FICHA DE FUNDAMENTO  (o que a empresa JA REALIZOU, com data de publicacao)
================================================================================

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O dono pediu, com estas palavras (05-06/set/2026): "eu so quero que voce me traga
os DADOS das empresas e as coisas que podemos usar para tomar a decisao se a
empresa tem fundamento forte ou nao".

Entao isto NAO e um score, NAO e um veredito e NAO e recomendacao. E uma FICHA
que ele le. A divisao de trabalho e dura:
  - NOS entregamos NIVEL, TENDENCIA e BANDEIRA, cada um com o numero na frente.
  - ELE decide, e escolhe a entrada pela analise tecnica.
No fim de cada ficha sai UMA linha de sintese que apenas ENUMERA o que esta bom e
o que esta ruim. Ela nao conclui nada. A conclusao e dele, por escrito dele.

O QUE A FICHA RESPONDE (os 6 blocos que ele pediu)
--------------------------------------------------
 RENTABILIDADE  margem bruta, margem operacional, ROIC (ROE quando o ROIC nao
                fecha), cada uma com NIVEL e TENDENCIA de 4 a 8 trimestres.
 CAIXA          fluxo de caixa livre em nivel e SINAL, conversao de lucro em
                caixa, e ha quantos trimestres seguidos e positivo.
 BALANCO        divida liquida / EBITDA, cobertura de juros, e a direcao
                (endividando ou desalavancando).
 CRESCIMENTO    receita ano contra ano nos ultimos trimestres, e se ACELERA ou
                DESACELERA (isso e a 2a derivada: a variacao do YoY).
 DILUICAO       numero de acoes ao longo do tempo. Empresa que emite acao todo
                trimestre transfere valor do acionista para quem recebe a acao.
 ARMADILHAS     cinco bandeiras SEPARADAS, cada uma com o numero que a levantou:
                queima de caixa, divida subindo com lucro caindo, diluicao
                continua, prejuizo recorrente, estoque crescendo mais que a
                receita.

REGRA DE HONESTIDADE (a mais importante deste arquivo)
------------------------------------------------------
Campo sem dado sai como "sem dado" COM O MOTIVO. Nunca como zero, nunca
estimado, nunca preenchido com a media do setor. Um zero silencioso e pior que
um buraco declarado: o zero entra em conta e o buraco nao.
E toda bandeira de armadilha vem acompanhada do NUMERO que a levantou — sem o
numero a bandeira e opiniao.

FONTE, E POR QUE ESTA E NAO OUTRA
---------------------------------
PRIMARIA: SEC EDGAR, API companyfacts XBRL (data.sec.gov/api/xbrl/companyfacts).
  Gratuita, sem chave, sem cota (a SEC so pede User-Agent com e-mail e <=10 req/s).
  E a UNICA fonte pontual de verdade: cada fato traz o campo `filed`, a data em
  que aquele numero foi publicado, e o EDGAR guarda TODAS as versoes do mesmo
  fato. Por isso a ficha grava v_orig (1a publicacao, a unica valida para
  backtest) e v_atual (a de hoje) — a diferenca entre as duas E a reapresentacao.
RESERVA: Yahoo (yfinance). Entra SO no campo que o EDGAR nao preencheu, e sai
  sempre carimbado "Yahoo — sem data de publicacao". Sem `filed` nao ha
  ponto-no-tempo, logo o campo serve de leitura de hoje e NAO serve de backtest.
  Medido na sonda de 06/set: o operatingMargins do Yahoo discordou do EDGAR e do
  FMP nos 3 tickers testados (parece trimestre isolado, nao TTM), e o .info
  chegou a devolver fluxo de caixa livre MAIOR que o operacional (janelas
  misturadas no mesmo dicionario). Por isso: reserva, nunca fonte primaria.
A ficha diz, campo a campo, QUEM deu o numero.

AS CINCO ARMADILHAS DE EXTRACAO QUE JA CAIRAM NA SONDA E ESTAO CORRIGIDAS AQUI
------------------------------------------------------------------------------
 1. TROCA DE TAG XBRL no meio da vida da empresa. Pegar o primeiro conceito com
    dado e parar deixava TSLA com 9 trimestres e CVS terminando em 2019. Aqui os
    conceitos sao MESCLADOS por prioridade. Erro silencioso: nao levanta excecao,
    so encurta a serie.
 2. FLUXO DE CAIXA ACUMULADO NO ANO. TSLA e CVS publicam OCF/capex como 89, 180,
    272, 364 dias. Procurar so janela de ~90 dias devolvia FCF VAZIO. Aqui deriva
    Q = YTD(n) - YTD(n-1).
 3. O EDGAR NAO AJUSTA ACOES POR DESDOBRAMENTO. Netflix saltou de 434,0 mm para
    4.298,4 mm de acoes: a versao ingenua reportou "diluicao de +883,71% ao ano",
    que mataria a melhor empresa da lista num filtro de qualidade. Aqui um salto
    >=1,5x (ou <=0,67x) entre trimestres vizinhos e tratado como split e a serie
    e reescalada para tras.
 4. SEGURADORA / PLANO DE SAUDE esconde metade do custo. O CVS lanca sinistro
    medico em PolicyholderBenefits..., FORA de CostOfGoodsAndServicesSold. A
    versao ingenua deu margem bruta de 44,49% para o CVS; o certo e 14,15% —
    30 pontos percentuais de erro, que classificariam o CVS como negocio premium.
 5. MEDIA PONDERADA NAO E FLUXO. Derivar YTD na serie de ACOES (que e uma media,
    nao um fluxo) gera zero e divisao por zero. Aqui a serie de acoes nunca e
    derivada por subtracao.

LEIS DA CASA APLICADAS (C:/Trading/hci-ea/METODO_HCI_Pesquisa.md)
-----------------------------------------------------------------
 - Nao produzir veredito: a ficha entrega dado e direcao; o julgamento e do dono.
 - Nada estimado e nada em zero: "sem dado" com motivo (lei da honestidade).
 - Os limiares das BANDEIRAS sao PROVISORIOS e estao declarados na saida. Eles
   nao filtram nada aqui — so acendem uma luz com o numero ao lado. Nenhum deles
   foi pre-registrado, e por isso nenhum pode virar filtro de motor sem PREREG.
 - Cache e retomada em job de rede (o companyfacts vai para disco por 3 dias).
 - Refutacao e ativo: a secao PIT conta quantos trimestres foram REAPRESENTADOS
   depois da 1a publicacao — e o cartao de conduta contabil da empresa.

LIMITES DE ESCOPO, DECLARADOS
-----------------------------
 - EDGAR so tem quem arquiva na SEC. ADR e emissora estrangeira preenchem 20-F
   com XBRL parcial, em IFRS, com contas de nome diferente. NAO testado.
 - O EDGAR e GAAP puro. O mercado reage ao numero AJUSTADO da empresa, que nao
   esta aqui.
 - Indicador operacional (assinantes, entregas, vidas cobertas) nao e conta
   contabil e nao esta no companyfacts como serie limpa — e justamente o numero
   que costuma mover a acao.
 - Banco e seguradora exigem tratamento proprio. O caso do sinistro medico ja
   esta tratado; os demais setores regulados NAO foram auditados um a um.

USO
---
  python fundamento_ficha.py                  # roda os tickers que a ficha de queda aprovou
  python fundamento_ficha.py --tickers X,Y,Z  # roda uma lista sua
  python fundamento_ficha.py --limite 5       # corta a lista

SAIDA
  data/fundamentos.json   (a ficha inteira, campo a campo, com fonte e motivo)
  data/fundamentos.txt    (o relatorio legivel, que e o que o dono le)
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_DATA = os.path.join(AQUI, "data")
DIR_CACHE = os.path.join(DIR_DATA, "cache_edgar_facts")
CACHE_CIK = os.path.join(DIR_DATA, "cache_cik_edgar.json")
FICHAS_QUEDA = os.path.join(DIR_DATA, "fichas_queda.json")
OUT_JSON = os.path.join(DIR_DATA, "fundamentos.json")
OUT_TXT = os.path.join(DIR_DATA, "fundamentos.txt")

UA_SEC = {"User-Agent": "HCI Research eduardogodooihoki@gmail.com"}
TTL_FACTS = 3 * 86400          # companyfacts em cache por 3 dias
N_TEND = 8                     # trimestres usados na tendencia (o dono pediu 4 a 8)

# --------------------------------------------------------------------------
# LIMIARES DAS BANDEIRAS — TODOS PROVISORIOS, NENHUM PRE-REGISTRADO.
# Eles nao filtram: so acendem luz. O numero vai junto para o dono conferir.
# --------------------------------------------------------------------------
LIM = {
    "diluicao_trimestres": 3,        # de 4 trimestres com acoes subindo YoY
    "diluicao_pct_ano": 1.0,         # e diluicao YoY acima disto (em %)
    "prejuizo_trimestres": 2,        # de 4 trimestres com lucro liquido negativo
    "estoque_vs_receita_pp": 10.0,   # estoque YoY supera receita YoY em X pontos
    "divida_delta_pct": 5.0,         # divida liquida sobe X% em 4 trimestres
}


def log(m=""):
    print(m, flush=True)


def d(s):
    return dt.date.fromisoformat(s)


# ==========================================================================
# 0. REDE — sem chave, com retentador e cache em disco (lei 11)
# ==========================================================================
def _http(url, hdr, tent=3, pausa=0.15):
    for i in range(tent):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=40) as r:
                b = r.read()
            time.sleep(pausa)
            return json.loads(b)
        except Exception as e:
            if i == tent - 1:
                return {"__erro__": "%s: %s" % (type(e).__name__, e)}
            time.sleep(1.5 * (i + 1))
    return None


def mapa_cik():
    """ticker -> [CIK, razao social]. Cache de 7 dias."""
    if os.path.exists(CACHE_CIK) and time.time() - os.path.getmtime(CACHE_CIK) < 7 * 86400:
        try:
            return json.load(open(CACHE_CIK, encoding="utf-8"))
        except Exception:
            pass
    m = _http("https://www.sec.gov/files/company_tickers.json", UA_SEC)
    if not m or "__erro__" in m:
        return {}
    x = {v["ticker"]: [str(v["cik_str"]).zfill(10), v["title"]] for v in m.values()}
    try:
        json.dump(x, open(CACHE_CIK, "w", encoding="utf-8"))
    except Exception:
        pass
    return x


def ultimo_arquivamento(cik):
    """Data do ultimo 10-Q/10-K no endpoint `submissions`.
    POR QUE ISTO EXISTE (achado medido em 06/set/2026): o EIX arquivou um 10-Q em
    2026-07-30 e o companyfacts nao tinha UM UNICO fato daquele arquivamento —
    zero conceitos com filed >= 2026-07-01, enquanto o submissions listava o 10-Q.
    Ou seja: o companyfacts pode ficar PARA TRAS do que a empresa ja publicou.
    Sem esta conferencia a ficha serve dado de marco como se fosse de hoje, em
    silencio. Com ela, a defasagem sai impressa. Custa ~0,3 s por ticker."""
    d0 = _http("https://data.sec.gov/submissions/CIK%s.json" % cik, UA_SEC)
    if not d0 or "__erro__" in d0:
        return None, None
    r = (d0.get("filings", {}) or {}).get("recent", {}) or {}
    melhor = (None, None)
    for f, dat in zip(r.get("form", []), r.get("filingDate", [])):
        if f in ("10-Q", "10-K") and (melhor[1] is None or dat > melhor[1]):
            melhor = (f, dat)
    return melhor


def companyfacts(cik):
    """companyfacts do EDGAR, com cache de 3 dias em disco (o arquivo tem ~4 MB)."""
    os.makedirs(DIR_CACHE, exist_ok=True)
    cam = os.path.join(DIR_CACHE, "CIK%s.json" % cik)
    if os.path.exists(cam) and time.time() - os.path.getmtime(cam) < TTL_FACTS:
        try:
            return json.load(open(cam, encoding="utf-8")), "cache"
        except Exception:
            pass
    cf = _http("https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json" % cik, UA_SEC)
    if not cf or "__erro__" in cf:
        return cf, "erro"
    try:
        json.dump(cf, open(cam, "w", encoding="utf-8"))
    except Exception:
        pass
    return cf, "rede"


# ==========================================================================
# 1. EXTRACAO XBRL — as 5 correcoes da sonda vivem nesta secao
# ==========================================================================
def serie(cf, conceitos, tipo="dur", unidade="USD"):
    """Serie por periodo. tipo 'dur' -> chave (start,end); 'inst' -> chave end.
    v_orig = PRIMEIRA publicacao (a unica valida para backtest);
    v_atual = ULTIMA (a de hoje). A diferenca entre as duas e a reapresentacao.
    CORRECAO 1: mescla os conceitos por PRIORIDADE — a empresa troca de tag XBRL
    no meio da vida e um conceito sozinho nao cobre a serie inteira."""
    us = cf.get("facts", {}).get("us-gaap", {}) or {}
    dei = cf.get("facts", {}).get("dei", {}) or {}
    saida, usado = {}, []
    for c in conceitos:
        src = us.get(c) or dei.get(c)
        if not src:
            continue
        novos = 0
        for un, regs in src.get("units", {}).items():
            if un != unidade:
                continue
            for r in regs:
                if tipo == "dur":
                    if not r.get("start"):
                        continue
                    k = (r["start"], r["end"])
                else:
                    if r.get("start"):
                        continue
                    k = r["end"]
                cur = saida.get(k)
                f, v = r["filed"], r["val"]
                if cur is None:
                    saida[k] = {"v_orig": v, "filed_orig": f, "v_atual": v,
                                "filed_atual": f, "form": r.get("form"), "tag": c}
                    novos += 1
                elif cur["tag"] == c:
                    if f < cur["filed_orig"]:
                        cur["v_orig"], cur["filed_orig"] = v, f
                    if f >= cur["filed_atual"]:
                        cur["v_atual"], cur["filed_atual"] = v, f
        if novos:
            usado.append("%s(%d)" % (c, novos))
    return saida, ("+".join(usado) if usado else None)


def trimestres(s, lo=80, hi=100, deriva=True):
    """Trimestres DISCRETOS.
    CORRECAO 2: quando o filer publica FLUXO ACUMULADO NO ANO (89/180/272/364
    dias), deriva Q = YTD(n) - YTD(n-1). Sem isto o FCF de TSLA e CVS sai VAZIO.
    CORRECAO 5: `deriva=False` para series de MEDIA PONDERADA (acoes) — subtrair
    media de media gera zero e depois divisao por zero."""
    out = {}
    for (a, b), v in s.items():
        n = (d(b) - d(a)).days
        if lo <= n <= hi:
            out[b] = dict(v, dias=n, start=a, derivado=False)
    if not deriva:
        return dict(sorted(out.items()))
    porstart = defaultdict(list)
    for (a, b), v in s.items():
        porstart[a].append((b, v))
    for a, lst in porstart.items():
        lst.sort()
        for i in range(1, len(lst)):
            bp, vp = lst[i - 1]
            b, v = lst[i]
            if (d(b) - d(a)).days < 100:
                continue
            n = (d(b) - d(bp)).days
            if lo <= n <= hi and b not in out:
                out[b] = {"v_orig": v["v_orig"] - vp["v_orig"],
                          "filed_orig": max(v["filed_orig"], vp["filed_orig"]),
                          "v_atual": v["v_atual"] - vp["v_atual"],
                          "filed_atual": max(v["filed_atual"], vp["filed_atual"]),
                          "form": v.get("form"), "tag": v.get("tag"),
                          "dias": n, "start": bp, "derivado": True}
    return dict(sorted(out.items()))


def ttm(qs, n=4):
    """Soma movel de 4 trimestres contiguos -> {fim: soma}. Exige os 4 dentro de
    ~400 dias, senao um buraco na serie viraria um TTM falso."""
    ks = sorted(qs)
    out = {}
    for i in range(n - 1, len(ks)):
        jan = ks[i - n + 1:i + 1]
        if (d(jan[-1]) - d(jan[0])).days > 400:
            continue
        out[jan[-1]] = sum(qs[k]["v_orig"] for k in jan)
    return out


def inst_em(si, data, tol=95):
    """Valor de ESTOQUE (balanco) mais proximo <= data, dentro da tolerancia."""
    c = [k for k in si if k <= data and (d(data) - d(k)).days <= tol]
    return si[max(c)]["v_orig"] if c else None


def ajusta_split(aq):
    """CORRECAO 3: o EDGAR NAO ajusta a serie de acoes por desdobramento.
    Salto >=1,5x (ou <=0,67x) entre trimestres vizinhos = split/grupamento;
    a serie anterior e reescalada. Sem isto o NFLX aparece com +883% de diluicao
    ao ano, que e o desdobramento 10-por-1 lido como emissao de acoes."""
    ks = sorted(aq)
    if len(ks) < 2:
        return dict(aq), []
    fator, ajus, splits = 1.0, {}, []
    for i in range(len(ks) - 1, 0, -1):
        ant = aq[ks[i - 1]]
        r = (aq[ks[i]] / ant) if ant else 1.0
        ajus[ks[i]] = aq[ks[i]] * fator
        if r >= 1.5 or r <= 0.67:
            # Desdobramento real tem razao pequena (2x, 3x, 10x). Razao de ~1000x
            # (ou ~0,001x) e TROCA DE UNIDADE no arquivamento antigo — milhares
            # contra unidades. Chamar isso de "split" seria informacao falsa na
            # ficha, entao os dois casos sao rotulados separadamente. O reescalonamento
            # e o mesmo nos dois: o que muda e o nome que a ficha da ao evento.
            tipo = "unidade" if (r >= 50 or r <= 0.02) else "split"
            splits.append({"entre": [ks[i - 1], ks[i]], "razao": round(r, 3), "tipo": tipo})
            fator *= r
    ajus[ks[0]] = aq[ks[0]] * fator
    return ajus, splits


# --- contas XBRL efetivamente usadas (ordem = prioridade de mesclagem) -----
REC = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
       "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
       "SalesRevenueServicesNet", "SalesRevenueGoodsNet"]
CUS = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfServices", "CostOfGoodsSold"]
GP = ["GrossProfit"]
OP = ["OperatingIncomeLoss"]
NI = ["NetIncomeLoss", "ProfitLoss"]
JUR = ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
       "InterestAndDebtExpense", "InterestExpenseOperating", "InterestIncomeExpenseNet"]
OCF = ["NetCashProvidedByUsedInOperatingActivities",
       "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]
CAPEX = ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
         "PaymentsToAcquirePropertyPlantAndEquipmentExcludingCapitalizedInterest"]
DA = ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
      "DepreciationAndAmortization", "Depreciation", "DepreciationNonproduction"]
IMP = ["IncomeTaxExpenseBenefit"]
LAIR = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]
# CORRECAO 4: em seguradora / plano de saude o sinistro e CUSTO e fica fora do
# "cost of revenue". Sem somar, a margem bruta do CVS sai 44% em vez de 14%.
SIN = ["PolicyholderBenefitsAndClaimsIncurredNet",
       "PolicyholderBenefitsAndClaimsIncurredHealthCare"]
PL = ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
DLP = ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermDebt"]
DCP = ["LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent",
       "DebtCurrent", "ShortTermBorrowings"]
# ARMADILHA 1 batendo no CAIXA (achado em 06/set na LULU): ela usa
# CashAndCashEquivalentsAtCarryingValue ate 2019-02-03 e depois migra para a tag
# pos-ASU 2016-18 (com caixa restrito). Com uma tag so, o caixa recente sumia — e
# a versao anterior deste arquivo transformava esse buraco em ZERO, produzindo
# "divida liquida 0,00 bi" para uma empresa com bilhoes em caixa. Corrigido nas
# duas pontas: a lista abaixo mescla as tags, e caixa ausente agora e None.
CX = ["CashAndCashEquivalentsAtCarryingValue",
      "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
      "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations"]
STI = ["ShortTermInvestments", "OtherShortTermInvestments"]
EST = ["InventoryNet", "InventoryGross", "InventoryFinishedGoodsNetOfReserves"]
ACOES = ["WeightedAverageNumberOfDilutedSharesOutstanding",
         "WeightedAverageNumberOfSharesOutstandingBasic"]


def pct(x):
    return None if x is None else round(100 * x, 2)


def num(x, c=3):
    return None if x is None else round(x, c)


# ==========================================================================
# 2. CAMPO — a unidade da honestidade. Ou tem valor E fonte, ou tem motivo.
# ==========================================================================
def campo(valor, fonte=None, motivo=None, unidade=None):
    """NUNCA devolve zero no lugar de vazio. Se valor e None, exige motivo."""
    if valor is None:
        return {"valor": None, "fonte": None, "unidade": unidade,
                "sem_dado": motivo or "conta ausente no XBRL da empresa"}
    return {"valor": valor, "fonte": fonte, "unidade": unidade, "sem_dado": None}


def tendencia(sv, bom_subir=True, n=N_TEND):
    """Inclinacao de Theil-Sen (mediana das inclinacoes par a par) nos ultimos n
    TTMs + delta contra 4 trimestres atras. Theil-Sen porque um trimestre
    atipico nao deve virar 'tendencia' — a mediana resiste, a regressao nao.
    CONVENCAO DE SINAL: em alavancagem e diluicao SUBIR e PIORAR."""
    ks = sorted(sv)[-n:]
    if len(ks) < 4:
        return {"sentido": None, "sem_dado": "serie curta: %d TTMs (minimo 4)" % len(ks)}
    ys = [sv[k] for k in ks]
    incl = []
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            incl.append((ys[j] - ys[i]) / (j - i))
    incl.sort()
    m = incl[len(incl) // 2]
    if abs(m) < 1e-9:
        sent = "estavel"
    elif bom_subir:
        sent = "MELHORA" if m > 0 else "PIORA"
    else:
        sent = "PIORA" if m > 0 else "MELHORA"
    return {"sentido": sent, "inclinacao_por_trim": num(m),
            "n_pontos": len(ys), "primeiro": ks[0], "ultimo": ks[-1],
            "delta_4trim": num(ys[-1] - ys[-5]) if len(ys) >= 5 else None,
            "serie": [[k, num(sv[k], 2)] for k in ks], "sem_dado": None}


# ==========================================================================
# 3. O MOTOR — monta as linhas TTM a partir do companyfacts
# ==========================================================================
def linhas_ttm(cf):
    S, tags = {}, {}
    for nome, cs in [("rec", REC), ("cus", CUS), ("gp", GP), ("op", OP), ("ni", NI),
                     ("jur", JUR), ("ocf", OCF), ("capex", CAPEX), ("da", DA),
                     ("imp", IMP), ("lair", LAIR), ("sin", SIN)]:
        s, tag = serie(cf, cs, "dur")
        S[nome] = trimestres(s)
        tags[nome] = tag
    for nome, cs in [("pl", PL), ("dlp", DLP), ("dcp", DCP), ("cx", CX),
                     ("sti", STI), ("est", EST)]:
        s, tag = serie(cf, cs, "inst")
        S[nome] = dict(sorted(s.items()))
        tags[nome] = tag
    sa, tag = serie(cf, ACOES, "dur", "shares")
    S["acoes"] = trimestres(sa, deriva=False)   # CORRECAO 5: media nao se deriva
    tags["acoes"] = tag

    T = {k: ttm(S[k]) for k in ["rec", "cus", "gp", "op", "ni", "jur", "ocf",
                                "capex", "da", "imp", "lair", "sin"]}
    custo_composto = bool(T["sin"])
    # EBIT DERIVADO (achado em 06/set na CLX e na REYN): nem toda empresa tagueia
    # OperatingIncomeLoss — muitas vao do lucro bruto direto ao lucro antes de
    # impostos. Sem o fallback essas empresas saem da ficha com "0 TTMs montados",
    # que e uma ficha perdida por detalhe de taxonomia, nao por falta de dado.
    # EBIT ~= lucro antes de impostos + despesa de juros. Fica MARCADO como derivado
    # porque nao e o numero que a empresa publicou, e o que nos reconstruimos.
    opx, derivado_op = dict(T["op"]), set()
    for e, v in T["lair"].items():
        if e not in opx and T["jur"].get(e) is not None:
            opx[e] = v + abs(T["jur"][e])
            derivado_op.add(e)
    ends = sorted(set(T["rec"]) & set(opx))
    L = []
    for e in ends:
        rec, op, ni = T["rec"].get(e), opx.get(e), T["ni"].get(e)
        gp, custo = T["gp"].get(e), T["cus"].get(e)
        if T["sin"].get(e) is not None:      # CORRECAO 4
            custo = (custo or 0) + T["sin"][e]
            gp = None
        if gp is None and custo is not None and rec:
            gp = rec - custo
        ocf, cap = T["ocf"].get(e), T["capex"].get(e)
        da, jur = T["da"].get(e), T["jur"].get(e)
        pl = inst_em(S["pl"], e)
        # DIVIDA: nunca assumir zero. Empresa sem divida e tag ausente sao coisas
        # DIFERENTES e daqui de dentro parecem iguais — entao a ficha declara qual
        # dos dois casos e, em vez de somar zero e seguir em frente.
        dlp_v, dcp_v = inst_em(S["dlp"], e), inst_em(S["dcp"], e)
        achou_div = (dlp_v is not None or dcp_v is not None)
        dl = ((dlp_v or 0) + (dcp_v or 0)) if achou_div else None
        cx = inst_em(S["cx"], e)   # None quando ausente. NUNCA zero (ver CX acima).
        est = inst_em(S["est"], e)
        ebitda = (op + da) if (op is not None and da is not None) else None
        fcf = (ocf - cap) if (ocf is not None and cap is not None) else None
        imp, lair = T["imp"].get(e), T["lair"].get(e)
        taxa = (imp / lair) if (imp is not None and lair not in (None, 0)) else 0.21
        taxa = min(max(taxa, 0.0), 0.60)
        cap_inv = (pl + (dl or 0) - (cx or 0)) if pl is not None else None
        roic = (op * (1 - taxa) / cap_inv) if (op is not None and cap_inv and cap_inv > 0) else None
        L.append({
            "divida_encontrada": achou_div,
            "ebit_derivado": e in derivado_op,
            "fim_trim": e,
            "publicado_em": S["rec"].get(e, {}).get("filed_orig"),
            "receita_ttm": rec, "lucro_liq_ttm": ni, "ebitda_ttm": ebitda,
            "ocf_ttm": ocf, "capex_ttm": cap, "fcf_ttm": fcf, "estoque": est,
            "margem_bruta": pct(gp / rec) if (gp is not None and rec) else None,
            "margem_op": pct(op / rec) if (op is not None and rec) else None,
            "margem_liq": pct(ni / rec) if (ni is not None and rec) else None,
            # ROE so existe com PL POSITIVO. A CLX (06/set) tem PL quase zero por
            # recompra acumulada e devolvia ROE de -1128%, que nao e rentabilidade,
            # e um denominador colapsando. Numero sem significado nao entra na ficha.
            "roe": pct(ni / pl) if (ni is not None and pl and pl > 0) else None,
            "pl": pl,
            "roic": pct(roic),
            "div_bruta": dl, "caixa": cx,
            # divida liquida exige AS DUAS pontas medidas. Faltando uma, e sem dado.
            "div_liq": (dl - cx) if (dl is not None and cx is not None) else None,
            "div_liq_ebitda": (num((dl - cx) / ebitda)
                               if (dl is not None and cx is not None
                                   and ebitda and ebitda > 0) else None),
            "cobertura_juros": num(op / abs(jur)) if (op is not None and jur) else None,
            "margem_fcf": pct(fcf / rec) if (fcf is not None and rec) else None,
            "conversao_caixa": pct(fcf / ni) if (fcf is not None and ni and ni > 0) else None,
            "conversao_ocf": pct(ocf / ni) if (ocf is not None and ni and ni > 0) else None,
        })
    # crescimento de receita YoY sobre TTM (TTM contra o TTM de ~4 trimestres atras)
    for x in L:
        alvo = [y for y in L if y["fim_trim"] < x["fim_trim"]
                and 330 <= (d(x["fim_trim"]) - d(y["fim_trim"])).days <= 400]
        x["cresc_receita_yoy"] = (pct(x["receita_ttm"] / alvo[-1]["receita_ttm"] - 1)
                                  if (alvo and alvo[-1]["receita_ttm"]) else None)
        ae = [y for y in L if y["fim_trim"] < x["fim_trim"] and y.get("estoque")
              and 330 <= (d(x["fim_trim"]) - d(y["fim_trim"])).days <= 400]
        x["cresc_estoque_yoy"] = (pct(x["estoque"] / ae[-1]["estoque"] - 1)
                                  if (ae and x.get("estoque")) else None)
    # diluicao: acoes DILUIDAS do trimestre, ajustadas por split
    aq = {k: v["v_orig"] for k, v in S["acoes"].items() if v["v_orig"]}
    aq, splits = ajusta_split(aq)
    for x in L:
        a = aq.get(x["fim_trim"])
        x["acoes_diluidas_mm"] = round(a / 1e6, 1) if a else None
        alvo = [k for k in aq if k < x["fim_trim"]
                and 330 <= (d(x["fim_trim"]) - d(k)).days <= 400]
        x["diluicao_yoy_pct"] = pct(a / aq[max(alvo)] - 1) if (a and alvo) else None

    # trimestres DISCRETOS de FCF e de lucro: e o que responde "ha quantos
    # trimestres e positivo" e "prejuizo recorrente". TTM esconde o trimestre.
    fcfq, niq = {}, {}
    for k in sorted(set(S["ocf"]) & set(S["capex"])):
        fcfq[k] = S["ocf"][k]["v_orig"] - S["capex"][k]["v_orig"]
    for k, v in S["ni"].items():
        niq[k] = v["v_orig"]
    pit = {"trimestres_receita": len(S["rec"]),
           "reapresentados_depois": sum(1 for v in S["rec"].values()
                                        if abs(v["v_atual"] - v["v_orig"]) > 1),
           "primeiro_trim": min(S["rec"]) if S["rec"] else None,
           "ultima_publicacao": max((v["filed_orig"] for v in S["rec"].values()), default=None)}
    return L, {"tags": {k: v for k, v in tags.items() if v}, "splits": splits,
               "n_ebit_derivado": len(derivado_op),
               "custo_composto": custo_composto, "fcf_trimestral": fcfq,
               "lucro_trimestral": niq, "pit": pit}


# ==========================================================================
# 4. RESERVA YAHOO — so no campo que o EDGAR nao deu, e sempre carimbada
# ==========================================================================
def reserva_yahoo(tic):
    """Le .info do Yahoo. AVISO GRAVADO NA FICHA: sem data de publicacao, logo
    NAO e ponto-no-tempo e NAO serve para backtest. Medido na sonda: o
    operatingMargins discorda do EDGAR (parece trimestre isolado, nao TTM) e o
    .info ja devolveu FCF maior que o OCF (janelas misturadas)."""
    try:
        import yfinance as yf
        i = yf.Ticker(tic).info or {}
    except Exception as e:
        return {"__erro__": "%s: %s" % (type(e).__name__, e)}
    g = lambda k: (i.get(k) if isinstance(i.get(k), (int, float)) else None)
    ebitda, td, tc = g("ebitda"), g("totalDebt"), g("totalCash")
    return {
        "margem_bruta": pct(g("grossMargins")),
        "margem_op": pct(g("operatingMargins")),
        "roe": pct(g("returnOnEquity")),
        "fcf_ttm": g("freeCashflow"),
        "div_liq_ebitda": num((td - tc) / ebitda) if (td is not None and tc is not None and ebitda) else None,
        "cresc_receita_yoy": pct(g("revenueGrowth")),
    }


# ==========================================================================
# 5. AS CINCO BANDEIRAS DE ARMADILHA — cada uma com o NUMERO que a levantou
# ==========================================================================
def bandeiras(L, extra):
    U = L[-1] if L else {}
    B = []

    def band(nome, ativa, numero, motivo=None):
        B.append({"bandeira": nome, "ativa": ativa, "numero": numero,
                  "sem_dado": motivo})

    # 1. QUEIMA DE CAIXA
    fq = extra["fcf_trimestral"]
    ks = sorted(fq)[-8:]
    if U.get("fcf_ttm") is None and not ks:
        band("queima de caixa", None, None,
             "sem OCF ou sem capex no XBRL — FCF nao calculavel")
    else:
        neg = [k for k in ks if fq[k] < 0]
        f = U.get("fcf_ttm")
        ocf, cap = U.get("ocf_ttm"), U.get("capex_ttm")
        band("queima de caixa", (f is not None and f < 0),
             "FCF TTM %s | %d de %d trimestres negativos%s | OCF TTM %s menos capex TTM %s "
             "(FCF negativo por CAPEX e por OPERACAO sao coisas diferentes: os dois numeros "
             "estao aqui para o dono separar)" % (
                 ("US$ %.2f bi" % (f / 1e9)) if f is not None else "sem dado",
                 len(neg), len(ks),
                 (" (ultimos: %s)" % ", ".join(neg[-3:])) if neg else " (nenhum)",
                 ("US$ %.2f bi" % (ocf / 1e9)) if ocf is not None else "sem dado",
                 ("US$ %.2f bi" % (cap / 1e9)) if cap is not None else "sem dado"))

    # 2. DIVIDA SUBINDO COM LUCRO CAINDO — as duas condicoes, nao uma
    if len(L) >= 5 and L[-1].get("div_liq") is not None and L[-5].get("div_liq") is not None \
            and L[-1].get("lucro_liq_ttm") is not None and L[-5].get("lucro_liq_ttm") is not None:
        d0, d1 = L[-5]["div_liq"], L[-1]["div_liq"]
        n0, n1 = L[-5]["lucro_liq_ttm"], L[-1]["lucro_liq_ttm"]
        dd = 100 * (d1 - d0) / abs(d0) if d0 else None
        dn = 100 * (n1 - n0) / abs(n0) if n0 else None
        ativa = (dd is not None and dn is not None and dd > LIM["divida_delta_pct"] and dn < 0)
        band("divida subindo com lucro caindo", ativa,
             "divida liquida %.2f bi -> %.2f bi (%s) e lucro TTM %.2f bi -> %.2f bi (%s), em 4 trimestres" % (
                 d0 / 1e9, d1 / 1e9, ("%+.1f%%" % dd) if dd is not None else "n/d",
                 n0 / 1e9, n1 / 1e9, ("%+.1f%%" % dn) if dn is not None else "n/d"))
    else:
        band("divida subindo com lucro caindo", None, None,
             "faltam 5 TTMs com divida liquida e lucro liquido")

    # 3. DILUICAO CONTINUA
    dl = [x["diluicao_yoy_pct"] for x in L[-4:] if x.get("diluicao_yoy_pct") is not None]
    if len(dl) < 3:
        band("diluicao continua", None, None,
             "serie de acoes insuficiente (%d de 4 trimestres com YoY)" % len(dl))
    else:
        pos = [v for v in dl if v > 0]
        ativa = (len(pos) >= LIM["diluicao_trimestres"] and
                 (U.get("diluicao_yoy_pct") or 0) > LIM["diluicao_pct_ano"])
        band("diluicao continua", ativa,
             "%d de %d trimestres com acoes subindo YoY | ultimo %+.2f%% ao ano | acoes %s mm%s" % (
                 len(pos), len(dl), U.get("diluicao_yoy_pct") or 0.0,
                 U.get("acoes_diluidas_mm"),
                 (" | %d split(s) tratado(s)" % len(extra["splits"])) if extra["splits"] else ""))

    # 4. PREJUIZO RECORRENTE
    nq = extra["lucro_trimestral"]
    kn = sorted(nq)[-4:]
    if len(kn) < 3:
        band("prejuizo recorrente", None, None, "menos de 3 trimestres de lucro liquido")
    else:
        neg = [k for k in kn if nq[k] < 0]
        band("prejuizo recorrente", len(neg) >= LIM["prejuizo_trimestres"],
             "%d de %d trimestres com prejuizo (%s) | lucro TTM %s" % (
                 len(neg), len(kn), ", ".join(neg) if neg else "nenhum",
                 ("US$ %.2f bi" % (U["lucro_liq_ttm"] / 1e9)) if U.get("lucro_liq_ttm") is not None else "sem dado"))

    # 5. ESTOQUE CRESCENDO MAIS QUE A RECEITA
    ie, ir = U.get("cresc_estoque_yoy"), U.get("cresc_receita_yoy")
    if ie is None or ir is None:
        falta = "conta de estoque ausente (empresa de servico/software nao publica InventoryNet)" \
            if ie is None else "sem crescimento de receita YoY"
        band("estoque crescendo mais que a receita", None, None, falta)
    else:
        band("estoque crescendo mais que a receita", (ie - ir) > LIM["estoque_vs_receita_pp"],
             "estoque %+.2f%% YoY contra receita %+.2f%% YoY = %+.2f pontos de diferenca" % (ie, ir, ie - ir))
    return B


# ==========================================================================
# 6. A FICHA
# ==========================================================================
def monta_ficha(tic, cikmap):
    F = {"ticker": tic, "gerado_em": dt.datetime.now().isoformat(timespec="seconds")}
    reg = cikmap.get(tic)
    if not reg:
        F["erro"] = ("ticker sem CIK no EDGAR — provavelmente emissora estrangeira/ADR "
                     "(arquiva 20-F/6-K, nao 10-Q com XBRL us-gaap)")
        return F
    F["cik"], F["empresa"] = reg[0], reg[1]
    cf, origem = companyfacts(reg[0])
    if not cf or "__erro__" in (cf or {}):
        F["erro"] = "companyfacts nao respondeu: %s" % (cf or {}).get("__erro__", "sem resposta")
        return F
    F["fonte_facts"] = origem
    L, extra = linhas_ttm(cf)
    if len(L) < 4:
        forma, data_arq = ultimo_arquivamento(F["cik"])
        if forma is None:
            F["erro"] = ("serie XBRL curta demais: %d TTMs montados (minimo 4). Nenhum 10-Q/10-K "
                         "no submissions — provavel emissora estrangeira, que arquiva 20-F/6-K "
                         "anual em IFRS e nao entrega trimestre em us-gaap" % len(L))
        else:
            F["erro"] = ("serie XBRL curta demais: %d TTMs montados (minimo 4); ultimo %s em %s. "
                         "Faltou receita ou EBIT trimestral contiguo no companyfacts"
                         % (len(L), forma, data_arq))
        return F

    U = L[-1]
    yh = None   # so busca o Yahoo se algum campo do EDGAR faltar

    def precisa_yahoo():
        return any(U.get(k) is None for k in
                   ["margem_bruta", "margem_op", "roic", "roe", "div_liq_ebitda",
                    "fcf_ttm", "cresc_receita_yoy"])
    if precisa_yahoo():
        yh = reserva_yahoo(tic)
        if "__erro__" in yh:
            F["reserva_yahoo"] = "falhou: %s" % yh["__erro__"]
            yh = None
        else:
            F["reserva_yahoo"] = ("usada apenas nos campos vazios do EDGAR; "
                                  "SEM data de publicacao, logo NAO e ponto-no-tempo")

    def cmp_(chave, unidade, bom_subir=True, motivo=None, permite_reserva=True):
        """Monta o campo: EDGAR primeiro, Yahoo so se o EDGAR nao deu.

        `permite_reserva=False` para o campo que o EDGAR RECUSOU por motivo
        ECONOMICO, nao por buraco de dado. Exemplo medido na CLX: com patrimonio
        liquido nao positivo o ROE nao existe — deixar o Yahoo preencher 163,76%
        ali seria contrabandear de volta o numero que acabamos de julgar sem
        sentido, com outro carimbo. Buraco de dado se preenche; recusa nao."""
        v, fonte = U.get(chave), "EDGAR (XBRL, publicado em %s)" % U.get("publicado_em")
        de_reserva = False
        if v is None and permite_reserva and yh and yh.get(chave) is not None:
            v, fonte = yh[chave], "Yahoo (.info, SEM data de publicacao — nao e ponto-no-tempo)"
            de_reserva = True
        c = campo(v, fonte, motivo, unidade)
        sv = {x["fim_trim"]: x[chave] for x in L if x.get(chave) is not None}
        c["tendencia"] = (tendencia(sv, bom_subir) if len(sv) >= 4 else
                          {"sentido": None, "sem_dado": "so %d TTMs com este campo" % len(sv)})
        # FONTES DIFERENTES NAO SE MISTURAM EM SILENCIO: se o NIVEL veio do Yahoo,
        # a serie de tendencia continua sendo a do EDGAR. Isso vai dito.
        if de_reserva and c["tendencia"].get("sentido"):
            c["tendencia"]["ressalva_fonte"] = ("serie do EDGAR; o NIVEL acima veio do Yahoo — "
                                                "fontes diferentes, nao compare os dois numeros "
                                                "como se fossem a mesma medicao")
        return c

    # GUARDA DE DEFASAGEM: o companyfacts pode estar atras do que a empresa ja
    # arquivou (medido no EIX: 10-Q de 30/jul sem UM fato no companyfacts).
    forma, data_arq = ultimo_arquivamento(F["cik"])
    hoje = dt.date.today()
    pub = U.get("publicado_em")
    dias = (hoje - d(pub)).days if pub else None
    atraso = bool(data_arq and pub and data_arq > pub)
    F["frescor"] = {
        "ultimo_fato_publicado_em": pub,
        "dias_desde_a_publicacao": dias,
        "ultimo_arquivamento_na_sec": ([forma, data_arq] if data_arq else None),
        "companyfacts_atrasado": atraso,
        "aviso": (("DEFASADA: a empresa arquivou %s em %s e NENHUM fato desse "
                   "arquivamento esta no companyfacts. A ficha abaixo e do trimestre "
                   "anterior (%s). Nao e erro de extracao: e atraso da fonte."
                   % (forma, data_arq, U["fim_trim"])) if atraso else
                  ("ficha atual: o ultimo arquivamento na SEC (%s de %s) e o mesmo que "
                   "alimenta a ficha" % (forma, data_arq)) if data_arq else
                  "nao foi possivel conferir o submissions da SEC"),
    }

    F["referencia"] = {
        "ttm_encerrado_em": U["fim_trim"], "publicado_em": U["publicado_em"],
        "n_ttms_na_serie": len(L), "primeiro_ttm": L[0]["fim_trim"],
        "receita_ttm_bi": num(U["receita_ttm"] / 1e9, 2) if U.get("receita_ttm") else None,
        "lucro_liq_ttm_bi": num(U["lucro_liq_ttm"] / 1e9, 2) if U.get("lucro_liq_ttm") is not None else None,
        "ebitda_ttm_bi": num(U["ebitda_ttm"] / 1e9, 2) if U.get("ebitda_ttm") else None,
        "custo_composto_seguradora": extra["custo_composto"],
        "tags_xbrl_usadas": extra["tags"],
        "splits_tratados": extra["splits"],
        "pit_reapresentacao": extra["pit"],
    }

    F["rentabilidade"] = {
        "margem_bruta": cmp_("margem_bruta", "%",
                             motivo="a empresa nao publica custo do produto nem GrossProfit no "
                                    "XBRL (comum em concessionaria, banco e seguradora, que "
                                    "organizam a DRE por natureza de despesa)"),
        "margem_operacional": cmp_("margem_op", "%"),
        "ressalva_ebit": ("EBIT DERIVADO por nos (lucro antes de impostos + despesa de juros): "
                          "a empresa nao publica OperatingIncomeLoss no XBRL. Margem operacional, "
                          "ROIC, EBITDA e cobertura de juros herdam essa reconstrucao."
                          if U.get("ebit_derivado") else None),
        "ressalva_roe": (("patrimonio liquido de US$ %.2f bi e muito pequeno para a "
                          "escala do lucro — o ROE de %.0f%% vem do denominador colapsando "
                          "(tipicamente recompra acumulada), nao de rentabilidade. Leia o ROIC."
                          % (U["pl"] / 1e9, U["roe"]))
                         if (U.get("roe") is not None and abs(U["roe"]) > 100 and U.get("pl"))
                         else None),
        "roic": cmp_("roic", "%", motivo="ROIC exige PL, divida e caixa no mesmo trimestre; "
                                         "quando o capital investido nao fecha (ou e negativo), "
                                         "use o ROE ao lado"),
        "ressalva_roic": (None if U.get("divida_encontrada") else
                          "capital investido calculado SEM conta de divida (nenhuma foi "
                          "encontrada no XBRL) — pode ser empresa sem divida ou tag ausente"),
        "roe": cmp_("roe", "%", permite_reserva=(U.get("pl") is None),
                    motivo=("patrimonio liquido de US$ %.2f bi (NAO POSITIVO) — o ROE nao tem "
                            "significado economico aqui; leia o ROIC" % (U["pl"] / 1e9)
                            if U.get("pl") is not None else
                            "sem patrimonio liquido no trimestre")),
        "roic_substituido_por_roe": U.get("roic") is None and U.get("roe") is not None,
        "margem_liquida": cmp_("margem_liq", "%"),
    }

    fq = extra["fcf_trimestral"]
    ks = sorted(fq)
    seq = 0
    for k in reversed(ks):
        if fq[k] > 0:
            seq += 1
        else:
            break
    F["caixa"] = {
        "fcf_ttm_bi": campo(num(U["fcf_ttm"] / 1e9, 3) if U.get("fcf_ttm") is not None else None,
                            "EDGAR (OCF - capex, TTM)",
                            "sem OCF ou sem capex no XBRL", "US$ bi"),
        "fcf_sinal": campo(("POSITIVO" if U["fcf_ttm"] > 0 else "NEGATIVO")
                           if U.get("fcf_ttm") is not None else None,
                           "EDGAR", "FCF nao calculavel"),
        "margem_fcf": cmp_("margem_fcf", "%"),
        "conversao_lucro_em_caixa": campo(U.get("conversao_caixa"), "EDGAR (FCF TTM / lucro liquido TTM)",
                                          "lucro liquido TTM nao positivo — a razao perde sentido", "%"),
        "conversao_ocf_lucro": campo(U.get("conversao_ocf"), "EDGAR (OCF TTM / lucro liquido TTM)",
                                     "lucro liquido TTM nao positivo", "%"),
        "trimestres_seguidos_fcf_positivo": campo(seq if ks else None,
                                                  "EDGAR (trimestres discretos, do mais recente para tras)",
                                                  "sem serie trimestral de FCF", "trimestres"),
        "trimestres_com_fcf_na_serie": len(ks),
        "ocf_ttm_bi": campo(num(U["ocf_ttm"] / 1e9, 2) if U.get("ocf_ttm") is not None else None,
                            "EDGAR", "sem conta de caixa operacional", "US$ bi"),
        "capex_ttm_bi": campo(num(U["capex_ttm"] / 1e9, 2) if U.get("capex_ttm") is not None else None,
                              "EDGAR", "sem conta de capex", "US$ bi"),
        "nota": ("OCF e capex vao separados de proposito: FCF negativo por CAPEX (rede, "
                 "fabrica, expansao) e FCF negativo por OPERACAO sao coisas diferentes, "
                 "e a ficha nao decide qual e — mostra os dois numeros."),
    }

    F["balanco"] = {
        "div_liq_ebitda": cmp_("div_liq_ebitda", "x", bom_subir=False,
                               motivo=("nenhuma conta de divida no XBRL — NAO assumimos zero; "
                                       "veja o caixa ao lado"
                                       if not U.get("divida_encontrada") else
                                       "EBITDA nao positivo ou sem D&A no XBRL — o multiplo "
                                       "nao existe (nao e zero, e indefinido)")),
        "cobertura_juros": cmp_("cobertura_juros", "x",
                                motivo="despesa de juros ausente no XBRL"),
        "div_liq_bi": campo(num(U["div_liq"] / 1e9, 2) if U.get("div_liq") is not None else None,
                            "EDGAR", "exige divida E caixa medidos no mesmo trimestre; falta pelo menos um", "US$ bi"),
        "div_bruta_bi": campo(num(U["div_bruta"] / 1e9, 2) if U.get("div_bruta") is not None else None,
                              "EDGAR", "nenhuma conta de divida no XBRL (empresa sem divida ou "
                                       "tag ausente — daqui de dentro os dois casos sao iguais)",
                              "US$ bi"),
        "caixa_bi": campo(num(U["caixa"] / 1e9, 2) if U.get("caixa") is not None else None,
                          "EDGAR", "sem conta de caixa no trimestre (tag pode ter mudado)", "US$ bi"),
    }
    # DIRECAO: com CAIXA LIQUIDO o multiplo e negativo e "endividando" seria mentira.
    # Nesse caso o que a serie mede e o colchao de caixa em multiplos de EBITDA —
    # e ele encolhe tambem quando o EBITDA CRESCE, sem a empresa tomar um dolar.
    # MULTIPLO EXTREMO nao informa: |div.liq/EBITDA| > 25 significa denominador
    # quase zero (EBITDA minusculo) ou caixa muito maior que o negocio. Medido na
    # MDB: -170x. O numero fica na ficha, mas com o aviso de que ele nao mede
    # alavancagem — mede o EBITDA sendo pequeno.
    _dle = F["balanco"]["div_liq_ebitda"].get("valor")
    F["balanco"]["ressalva_multiplo"] = (
        ("multiplo de %.1fx e extremo: ele diz que o EBITDA e minusculo perto do caixa/divida, "
         "nao que a alavancagem seja essa. Leia o valor em dolar ao lado." % _dle)
        if isinstance(_dle, (int, float)) and abs(_dle) > 25 else None)
    tb = F["balanco"]["div_liq_ebitda"].get("tendencia") or {}
    dlq = U.get("div_liq")
    if dlq is None:
        yv = F["balanco"]["div_liq_ebitda"]
        F["balanco"]["posicao"] = (
            "sem dado no EDGAR (nenhuma conta de divida no XBRL); a leitura de %s ao lado "
            "vem do Yahoo, SEM data de publicacao" % fmt(yv)
            if (yv.get("valor") is not None and fonte_curta(yv) == "YAHOO*")
            else "sem dado (nenhuma conta de divida no XBRL)")
        F["balanco"]["direcao"] = "sem dado"
    elif dlq < 0:
        F["balanco"]["posicao"] = "CAIXA LIQUIDO (o caixa supera a divida em US$ %.2f bi)" % (-dlq / 1e9)
        F["balanco"]["direcao"] = (
            "colchao de caixa ENCOLHENDO em multiplos de EBITDA (atencao: tambem encolhe "
            "quando o EBITDA cresce)" if tb.get("sentido") == "PIORA" else
            "colchao de caixa CRESCENDO em multiplos de EBITDA" if tb.get("sentido") == "MELHORA" else
            tb.get("sentido") or "sem dado")
    else:
        F["balanco"]["posicao"] = "DIVIDA LIQUIDA de US$ %.2f bi" % (dlq / 1e9)
        F["balanco"]["direcao"] = ("DESALAVANCANDO" if tb.get("sentido") == "MELHORA" else
                                   "ENDIVIDANDO" if tb.get("sentido") == "PIORA" else
                                   tb.get("sentido") or "sem dado")
        # O MULTIPLO E UMA RAZAO: ele cai quando a divida cai OU quando o EBITDA
        # sobe. Medido no EIX (06/set): multiplo de 4,78x para 4,29x — "desalavancando"
        # — com a divida liquida SUBINDO de 37,07 bi para 40,14 bi. Dizer so
        # "desalavancando" ali esconde 3 bilhoes de divida nova. Entao a ficha
        # confere as duas pontas e avisa quando elas discordam.
        if len(L) >= 5 and L[-5].get("div_liq") is not None:
            d0 = L[-5]["div_liq"]
            if F["balanco"]["direcao"] == "DESALAVANCANDO" and dlq > d0:
                F["balanco"]["direcao"] = (
                    "multiplo MELHOROU, mas a divida liquida em dolar SUBIU de US$ %.2f bi para "
                    "US$ %.2f bi em 4 trimestres — quem caiu foi a RAZAO, porque o EBITDA cresceu "
                    "mais rapido que a divida, e nao a divida" % (d0 / 1e9, dlq / 1e9))
            elif F["balanco"]["direcao"] == "ENDIVIDANDO" and dlq < d0:
                F["balanco"]["direcao"] = (
                    "multiplo PIOROU, mas a divida liquida em dolar CAIU de US$ %.2f bi para "
                    "US$ %.2f bi — quem subiu foi a RAZAO, por queda do EBITDA" % (d0 / 1e9, dlq / 1e9))

    F["crescimento"] = {
        "receita_yoy": cmp_("cresc_receita_yoy", "%"),
        "serie_yoy": [[x["fim_trim"], x["cresc_receita_yoy"]] for x in L[-N_TEND:]
                      if x.get("cresc_receita_yoy") is not None],
    }
    sy = [x for _, x in F["crescimento"]["serie_yoy"]]
    if len(sy) >= 3:
        # ACELERACAO = 2a derivada. Media dos 2 ultimos YoY contra os 2 anteriores.
        rec, ant = sy[-2:], sy[-4:-2] if len(sy) >= 4 else sy[:-2]
        if ant:
            dif = sum(rec) / len(rec) - sum(ant) / len(ant)
            F["crescimento"]["aceleracao"] = campo(
                num(dif, 2), "EDGAR (media dos 2 YoY recentes menos a dos 2 anteriores)",
                None, "pontos percentuais")
            F["crescimento"]["ritmo"] = ("ACELERANDO" if dif > 0.5 else
                                         "DESACELERANDO" if dif < -0.5 else "ESTAVEL")
        else:
            F["crescimento"]["aceleracao"] = campo(None, motivo="serie de YoY curta")
            F["crescimento"]["ritmo"] = "sem dado"
    else:
        F["crescimento"]["aceleracao"] = campo(None, motivo="menos de 3 TTMs com YoY")
        F["crescimento"]["ritmo"] = "sem dado"

    F["diluicao"] = {
        "acoes_diluidas_mm": campo(U.get("acoes_diluidas_mm"), "EDGAR (media ponderada diluida, ajustada por split)",
                                   "sem serie de acoes no XBRL", "milhoes"),
        "diluicao_yoy": cmp_("diluicao_yoy_pct", "%", bom_subir=False),
        "serie_acoes_mm": [[x["fim_trim"], x["acoes_diluidas_mm"]] for x in L[-N_TEND:]
                           if x.get("acoes_diluidas_mm") is not None],
        "splits_tratados": extra["splits"],
        "nota": ("valor negativo = RECOMPRA (o numero de acoes caiu); "
                 "positivo = EMISSAO. O EDGAR nao ajusta por desdobramento, o ajuste e nosso."),
    }

    F["armadilhas"] = bandeiras(L, extra)
    F["linhas_ttm"] = [{k: x.get(k) for k in
                        ["fim_trim", "publicado_em", "margem_bruta", "margem_op", "roe", "roic",
                         "div_liq_ebitda", "cobertura_juros", "margem_fcf", "cresc_receita_yoy",
                         "diluicao_yoy_pct", "acoes_diluidas_mm"]} for x in L[-N_TEND:]]
    F["sintese"] = sintese(F)
    return F


def sintese(F):
    """UMA linha que ENUMERA. Nao conclui, nao pontua, nao recomenda.
    O dono foi explicito: a decisao e dele."""
    bom, ruim, vazio = [], [], []
    rot = [("rentabilidade", "margem_bruta", "margem bruta"),
           ("rentabilidade", "margem_operacional", "margem operacional"),
           ("rentabilidade", "roic", "ROIC"), ("rentabilidade", "roe", "ROE"),
           ("caixa", "margem_fcf", "margem de FCF"),
           ("balanco", "div_liq_ebitda", "divida/EBITDA"),
           ("balanco", "cobertura_juros", "cobertura de juros"),
           ("crescimento", "receita_yoy", "receita YoY"),
           ("diluicao", "diluicao_yoy", "diluicao")]
    for bl, ch, nome in rot:
        c = (F.get(bl) or {}).get(ch) or {}
        if c.get("valor") is None:
            vazio.append(nome)
            continue
        s = (c.get("tendencia") or {}).get("sentido")
        # CAIXA LIQUIDO: chamar de "divida/EBITDA piorando" um multiplo NEGATIVO
        # seria mentira. Aqui a leitura correta e o colchao de caixa encolhendo.
        if ch == "div_liq_ebitda" and isinstance(c["valor"], (int, float)) and c["valor"] < 0:
            nome = "colchao de caixa (%.2fx EBITDA)" % c["valor"]
            if s == "PIORA":
                ruim.append("%s encolhendo" % nome)
            elif s == "MELHORA":
                bom.append("%s crescendo" % nome)
            continue
        # a mesma discordancia razao-x-dolar que o bloco BALANCO ja detectou nao
        # pode voltar aqui como um "melhorando" limpo
        if ch == "div_liq_ebitda" and str((F.get("balanco") or {}).get("direcao", "")).startswith("multiplo"):
            ruim.append("divida/EBITDA %s: %s" % (c["valor"], F["balanco"]["direcao"]))
            continue
        if s == "MELHORA":
            bom.append("%s %s (%s)" % (nome, c["valor"], "melhorando"))
        elif s == "PIORA":
            ruim.append("%s %s (%s)" % (nome, c["valor"], "piorando"))
    fs = (F.get("caixa") or {}).get("fcf_sinal", {}).get("valor")
    seq = (F.get("caixa") or {}).get("trimestres_seguidos_fcf_positivo", {}).get("valor")
    if fs == "POSITIVO" and seq:
        bom.append("FCF positivo ha %d trimestres seguidos" % seq)
    elif fs == "POSITIVO":
        bom.append("FCF TTM positivo")
        ruim.append("o ULTIMO trimestre fechou com FCF negativo (a soma de 12 meses "
                    "ainda e positiva)")
    elif fs == "NEGATIVO":
        ruim.append("FCF TTM negativo")
    ac = [b["bandeira"] for b in F.get("armadilhas", []) if b.get("ativa") is True]
    nd = [b["bandeira"] for b in F.get("armadilhas", []) if b.get("ativa") is None]
    return {"bom": bom, "ruim": ruim, "sem_dado": vazio,
            "bandeiras_acesas": ac, "bandeiras_sem_dado": nd,
            "linha": "BOM: %s | RUIM: %s | BANDEIRAS ACESAS: %s | SEM DADO: %s" % (
                "; ".join(bom) or "nada nesta lista",
                "; ".join(ruim) or "nada nesta lista",
                ", ".join(ac) or "nenhuma",
                ", ".join(vazio + nd) or "nenhum"),
            "aviso": "Enumeracao, nao veredito. A decisao e do dono."}


# ==========================================================================
# 7. RELATORIO LEGIVEL
# ==========================================================================
def fmt(c, casas=2):
    if not isinstance(c, dict):
        return str(c)
    if c.get("valor") is None:
        return "sem dado (%s)" % c.get("sem_dado")
    v = c["valor"]
    s = ("%.*f" % (casas, v)) if isinstance(v, float) else str(v)
    u = c.get("unidade") or ""
    return ("%s%s" % (s, u if u in ("%", "x") else (" " + u if u else "")))


def fonte_curta(c):
    f = (c or {}).get("fonte") or ""
    if f.startswith("EDGAR"):
        return "EDGAR"
    if f.startswith("Yahoo"):
        return "YAHOO*"
    return "-"


def tend_txt(c):
    t = (c or {}).get("tendencia") or {}
    # "sem dado" ao lado de "MELHORA" e contraditorio: a serie historica pode existir
    # e mesmo assim o NIVEL de hoje nao ter significado (caso do ROE com PL negativo).
    if (c or {}).get("valor") is None and t.get("sentido"):
        return ("serie historica: %s (%+.3f/trim em %d TTMs) — mas o NIVEL atual esta sem dado, "
                "entao NAO leia como melhora de hoje"
                % (t["sentido"], t["inclinacao_por_trim"], t["n_pontos"]))
    if not t.get("sentido"):
        return "tendencia: sem dado (%s)" % t.get("sem_dado", "n/d")
    if t.get("ressalva_fonte"):
        return "tendencia: %s (%+.3f/trim em %d TTMs) [%s]" % (
            t["sentido"], t["inclinacao_por_trim"], t["n_pontos"], t["ressalva_fonte"])
    p = "tendencia: %s (%+.3f/trim em %d TTMs" % (t["sentido"], t["inclinacao_por_trim"], t["n_pontos"])
    if t.get("delta_4trim") is not None:
        p += "; %+.2f contra 4 trimestres atras" % t["delta_4trim"]
    return p + ")"


def relatorio(fichas, meta):
    o = []
    o.append("=" * 78)
    o.append("HCI — FICHA DE FUNDAMENTO")
    o.append("gerado em %s | %d tickers | fonte primaria: SEC EDGAR companyfacts (XBRL)"
             % (meta["gerado_em"], len(fichas)))
    o.append("origem da lista: %s" % meta["origem_lista"])
    o.append("")
    o.append("COMO LER: cada campo traz NIVEL, TENDENCIA e FONTE. Campo vazio sai como")
    o.append("'sem dado' COM O MOTIVO — nunca zero, nunca estimado. Bandeira de armadilha")
    o.append("vem sempre com o NUMERO que a levantou.")
    o.append("YAHOO* = campo que o EDGAR nao tinha; o Yahoo NAO traz data de publicacao,")
    o.append("logo esse campo serve de leitura de hoje e NAO serve para backtest.")
    o.append("Isto e DADO e CLASSIFICACAO. Nao ha veredito, nao ha recomendacao,")
    o.append("nao ha sinal de compra. A decisao e a entrada sao do Eduardo.")
    o.append("=" * 78)

    ok = [f for f in fichas if not f.get("erro")]
    er = [f for f in fichas if f.get("erro")]
    for F in ok:
        R = F["referencia"]
        o.append("")
        o.append("#" * 78)
        o.append("%s — %s  (CIK %s)" % (F["ticker"], F["empresa"], F["cik"]))
        o.append("TTM encerrado em %s, publicado em %s | serie de %d TTMs desde %s"
                 % (R["ttm_encerrado_em"], R["publicado_em"], R["n_ttms_na_serie"], R["primeiro_ttm"]))
        o.append("receita TTM US$ %s bi | lucro liquido TTM US$ %s bi | EBITDA TTM US$ %s bi"
                 % (R["receita_ttm_bi"], R["lucro_liq_ttm_bi"], R["ebitda_ttm_bi"]))
        if R["custo_composto_seguradora"]:
            o.append("  [tratamento] custo COMPOSTO: sinistro/beneficio somado ao custo do produto")
            o.append("               (sem isso a margem bruta sai inflada em dezenas de pontos)")
        if R["splits_tratados"]:
            sp = [x for x in R["splits_tratados"] if x.get("tipo") != "unidade"]
            un = [x for x in R["splits_tratados"] if x.get("tipo") == "unidade"]
            if sp:
                o.append("  [tratamento] %d desdobramento(s) detectado(s) e reescalado(s): %s"
                         % (len(sp), "; ".join("%sx entre %s e %s" % (x["razao"], x["entre"][0], x["entre"][1])
                                               for x in sp)))
            if un:
                o.append("  [tratamento] %d TROCA(S) DE UNIDADE na serie de acoes (razao ~%s), "
                         "reescalada(s) — nao sao desdobramentos, sao milhares contra unidades "
                         "em arquivamento antigo" % (len(un), un[0]["razao"]))
        p = R["pit_reapresentacao"]
        o.append("  [ponto-no-tempo] %d trimestres de receita, %d REAPRESENTADOS depois da 1a publicacao"
                 % (p["trimestres_receita"], p["reapresentados_depois"]))
        fr = F["frescor"]
        marca = "  [!! FRESCOR]" if fr["companyfacts_atrasado"] else "  [frescor]"
        o.append("%s %d dias desde a publicacao. %s" % (marca, fr["dias_desde_a_publicacao"] or -1,
                                                        fr["aviso"]))
        o.append("#" * 78)

        o.append("")
        o.append("RENTABILIDADE")
        for ch, nome in [("margem_bruta", "margem bruta"), ("margem_operacional", "margem operacional"),
                         ("roic", "ROIC"), ("roe", "ROE"), ("margem_liquida", "margem liquida")]:
            c = F["rentabilidade"][ch]
            o.append("  %-20s %-14s [%-6s] %s" % (nome, fmt(c), fonte_curta(c), tend_txt(c)))
        if F["rentabilidade"]["roic_substituido_por_roe"]:
            o.append("  (ROIC nao fechou; o ROE acima e o substituto, como combinado)")
        if F["rentabilidade"].get("ressalva_roe"):
            o.append("  (ressalva: %s)" % F["rentabilidade"]["ressalva_roe"])
        if F["rentabilidade"].get("ressalva_ebit"):
            o.append("  (ressalva: %s)" % F["rentabilidade"]["ressalva_ebit"])
        if F["rentabilidade"].get("ressalva_roic"):
            o.append("  (ressalva: %s)" % F["rentabilidade"]["ressalva_roic"])

        o.append("")
        o.append("CAIXA")
        C = F["caixa"]
        o.append("  %-20s %-14s [%-6s] %s" % ("FCF TTM", fmt(C["fcf_ttm_bi"], 3), fonte_curta(C["fcf_ttm_bi"]),
                                              "sinal: %s" % fmt(C["fcf_sinal"])))
        o.append("  %-20s %-14s [%-6s] %s" % ("margem de FCF", fmt(C["margem_fcf"]),
                                              fonte_curta(C["margem_fcf"]), tend_txt(C["margem_fcf"])))
        o.append("  %-20s %-14s conversao de LUCRO em caixa (FCF/lucro liquido)"
                 % ("conversao", fmt(C["conversao_lucro_em_caixa"])))
        o.append("  %-20s %-14s conversao OPERACIONAL (OCF/lucro liquido)"
                 % ("", fmt(C["conversao_ocf_lucro"])))
        o.append("  %-20s %-14s de %d trimestres na serie"
                 % ("FCF+ seguidos", fmt(C["trimestres_seguidos_fcf_positivo"]),
                    C["trimestres_com_fcf_na_serie"]))
        o.append("  %-20s OCF %s menos capex %s  (FCF por capex != FCF por operacao)"
                 % ("abertura do FCF", fmt(C["ocf_ttm_bi"]), fmt(C["capex_ttm_bi"])))

        o.append("")
        o.append("BALANCO — %s" % F["balanco"]["posicao"])
        o.append("         direcao: %s" % F["balanco"]["direcao"])
        B = F["balanco"]
        for ch, nome in [("div_liq_ebitda", "divida liq./EBITDA"), ("cobertura_juros", "cobertura de juros")]:
            c = B[ch]
            o.append("  %-20s %-14s [%-6s] %s" % (nome, fmt(c), fonte_curta(c), tend_txt(c)))
        if B.get("ressalva_multiplo"):
            o.append("  (ressalva: %s)" % B["ressalva_multiplo"])
        o.append("  %-20s divida bruta %s | caixa %s | divida liquida %s"
                 % ("", fmt(B["div_bruta_bi"]), fmt(B["caixa_bi"]), fmt(B["div_liq_bi"])))

        o.append("")
        G = F["crescimento"]
        o.append("CRESCIMENTO — ritmo: %s" % G["ritmo"])
        o.append("  %-20s %-14s [%-6s] %s" % ("receita YoY", fmt(G["receita_yoy"]),
                                              fonte_curta(G["receita_yoy"]), tend_txt(G["receita_yoy"])))
        o.append("  %-20s %s" % ("aceleracao", fmt(G["aceleracao"])))
        o.append("  %-20s %s" % ("YoY trimestre a trimestre",
                                 "  ".join("%s %+.1f%%" % (k[:7], v) for k, v in G["serie_yoy"][-6:])))

        o.append("")
        D = F["diluicao"]
        o.append("DILUICAO")
        o.append("  %-20s %-14s [%-6s] %s" % ("acoes diluidas", fmt(D["acoes_diluidas_mm"], 1),
                                              fonte_curta(D["acoes_diluidas_mm"]), ""))
        o.append("  %-20s %-14s [%-6s] %s" % ("diluicao YoY", fmt(D["diluicao_yoy"]),
                                              fonte_curta(D["diluicao_yoy"]), tend_txt(D["diluicao_yoy"])))
        o.append("  %-20s %s" % ("acoes trimestre a trimestre",
                                 "  ".join("%s %.1f" % (k[:7], v) for k, v in D["serie_acoes_mm"][-6:])))
        o.append("  (negativo = recompra; positivo = emissao)")

        o.append("")
        o.append("SINAIS DE ARMADILHA — cada bandeira com o numero que a levantou")
        for b in F["armadilhas"]:
            marca = "[ACESA]" if b["ativa"] is True else ("[ apaga]" if b["ativa"] is False else "[s/dado]")
            o.append("  %s %s" % (marca, b["bandeira"]))
            o.append("          %s" % (b["numero"] or ("sem dado: " + (b["sem_dado"] or "n/d"))))

        o.append("")
        S = F["sintese"]
        o.append("SINTESE (enumeracao, NAO veredito — a decisao e do Eduardo)")
        o.append("  BOM ...: %s" % ("; ".join(S["bom"]) or "nada nesta lista"))
        o.append("  RUIM ..: %s" % ("; ".join(S["ruim"]) or "nada nesta lista"))
        o.append("  ACESAS : %s" % (", ".join(S["bandeiras_acesas"]) or "nenhuma"))
        o.append("  S/DADO : %s" % (", ".join(S["sem_dado"] + S["bandeiras_sem_dado"]) or "nenhum"))

    if er:
        o.append("")
        o.append("=" * 78)
        o.append("SEM FICHA (%d) — isto e informacao, nao falha escondida" % len(er))
        for F in er:
            o.append("  %-8s %s" % (F["ticker"], F["erro"]))

    o.append("")
    o.append("=" * 78)
    o.append("LIMITES DECLARADOS")
    o.append("  - EDGAR e GAAP puro: o numero AJUSTADO da empresa, que o mercado costuma")
    o.append("    seguir, NAO esta aqui.")
    o.append("  - Emissora estrangeira / ADR arquiva 20-F em IFRS: fora do escopo, nao testado.")
    o.append("  - Indicador operacional (assinantes, entregas, vidas cobertas) nao e conta")
    o.append("    contabil e nao esta no companyfacts — e justamente o que costuma mover a acao.")
    o.append("  - Os limiares das bandeiras sao PROVISORIOS e nao foram pre-registrados:")
    o.append("    %s" % json.dumps(LIM))
    o.append("    Eles nao filtram nada; so acendem luz com o numero ao lado.")
    o.append("  - Esta ficha diz o que a empresa JA REALIZOU. Ela nao responde sozinha se a")
    o.append("    queda da semana teve lastro — isso e a ficha de queda, que le o consenso")
    o.append("    de lucro FUTURO. Os dois relogios sao diferentes e ambos sao necessarios.")
    o.append("=" * 78)
    return "\n".join(o)


def grava_atomico(caminho, texto):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(texto)
    os.replace(tmp, caminho)


# ==========================================================================
# 8. MAIN
# ==========================================================================
def lista_da_ficha_queda():
    if not os.path.exists(FICHAS_QUEDA):
        return None, None
    try:
        d0 = json.load(open(FICHAS_QUEDA, encoding="utf-8"))
    except Exception:
        return None, None
    ts = [f["ticker"] for f in d0.get("fichas", []) if f.get("ticker")]
    m = d0.get("meta", {})
    return ts, "ficha de queda de %s (semana %s a %s), %d aprovados" % (
        m.get("gerado_em", "?")[:10], m.get("semana_ini"), m.get("semana_fim"), len(ts))


def main():
    ap = argparse.ArgumentParser(description="Ficha de fundamento (HCI) — EDGAR XBRL")
    ap.add_argument("--tickers", help="lista separada por virgula (sobrepoe a ficha de queda)")
    ap.add_argument("--limite", type=int, default=0)
    a = ap.parse_args()

    if a.tickers:
        ts = [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
        origem = "lista passada na linha de comando"
    else:
        ts, origem = lista_da_ficha_queda()
        if not ts:
            ts = ["EIX", "LULU", "CRDO", "GWRE", "PCG"]
            origem = ("ficha de queda ausente — usados 5 tickers que cairam na semana "
                      "de 28/ago a 04/set/2026 (fallback declarado)")
    if a.limite:
        ts = ts[:a.limite]

    log("FICHA DE FUNDAMENTO — %d tickers" % len(ts))
    log("origem: %s" % origem)
    cikmap = mapa_cik()
    log("mapa CIK: %d tickers" % len(cikmap))
    fichas, t0 = [], time.time()
    for i, t in enumerate(ts, 1):
        s = time.time()
        F = monta_ficha(t, cikmap)
        F["segundos"] = round(time.time() - s, 2)
        fichas.append(F)
        if F.get("erro"):
            log("  %2d/%d %-6s ERRO: %s" % (i, len(ts), t, F["erro"][:70]))
        else:
            log("  %2d/%d %-6s ok  TTM %s  %s  %.1fs"
                % (i, len(ts), t, F["referencia"]["ttm_encerrado_em"],
                   ("%d bandeira(s) acesa(s)" % len(F["sintese"]["bandeiras_acesas"])),
                   F["segundos"]))

    meta = {"gerado_em": dt.datetime.now().isoformat(timespec="seconds"),
            "origem_lista": origem, "n": len(fichas),
            "n_com_ficha": sum(1 for f in fichas if not f.get("erro")),
            "n_sem_ficha": sum(1 for f in fichas if f.get("erro")),
            "fonte_primaria": "SEC EDGAR companyfacts XBRL (gratuita, sem chave, com data de publicacao)",
            "fonte_reserva": "Yahoo/yfinance .info — so nos campos vazios, SEM data de publicacao",
            "limiares_bandeiras_provisorios": LIM,
            "segundos_total": round(time.time() - t0, 1),
            "aviso": ("Dado e classificacao, nao recomendacao. Sem veredito 'forte'/'fraco': "
                      "a sintese apenas ENUMERA. A decisao e a entrada sao do Eduardo.")}
    grava_atomico(OUT_JSON, json.dumps({"meta": meta, "fichas": fichas},
                                       ensure_ascii=False, indent=1, default=str))
    grava_atomico(OUT_TXT, relatorio(fichas, meta))
    log("")
    log("gravado: %s" % OUT_JSON)
    log("gravado: %s" % OUT_TXT)
    log("%d com ficha, %d sem, %.1fs" % (meta["n_com_ficha"], meta["n_sem_ficha"], meta["segundos_total"]))


if __name__ == "__main__":
    sys.exit(main())
