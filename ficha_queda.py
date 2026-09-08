# -*- coding: utf-8 -*-
"""
HCI — FICHA DE QUEDA  (coletor semanal de candidatas a reversao apos queda)
===========================================================================

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O dono pediu (05-06/set/2026): "veja se a empresa ja caiu alguns X% nessa semana
e o seu motivo, e me traga se isso foi uma reacao ACIMA do que precisava".
Traduzindo em mecanismo: REVERSAO A MEDIA em empresa de qualidade depois de queda
excessiva. A divisao de trabalho e dura e esta escrita aqui para nao se perder:
  - NOS entregamos DADO e CLASSIFICACAO.
  - ELE decide e escolhe a entrada pela analise tecnica.
Nada neste arquivo e recomendacao, sinal de compra ou promessa de retorno.

A PERGUNTA CENTRAL, que da ou tira o valor de tudo: a queda teve LASTRO?
  COM LASTRO  = o consenso de lucro caiu junto com o preco. O mercado esta
                reprecificando um fato novo. Nao e oportunidade, e noticia.
  SEM LASTRO  = o preco caiu e a estimativa de lucro NAO se moveu.
  SEM DADO    = o ticker nao tem par nos snapshots ponto-no-tempo, ou a serie
                e curta demais. Esta classe e OBRIGATORIA: esconde-la e o que
                fabrica falso "sem lastro".

  ⚠️ 08/set/2026 — OS TRES ESTADOS CONTINUAM, MAS NAO SAO MAIS A RESPOSTA INTEIRA.
  O corte de 3% era binario: -2,9% caia num balde e -3,1% no oposto, na pergunta
  que da ou tira o valor da ficha. Agora, AO LADO dos tres estados, sai uma
  classificacao GRADUADA com a faixa de incerteza do proprio consenso (medida em
  epsHigh/epsLow/numAnalystsEps, colunas que ja estavam no CSV e nunca tinham sido
  lidas). Quando a revisao esta a menos de UMA incerteza da borda, o caso sai
  rotulado FRONTEIRA — e fronteira nao e veredito. O limiar nao mudou de lugar e
  nenhum numero novo foi calibrado: ver o bloco de reguas.

LIMITE DURO, DECLARADO DE PROPOSITO NA SAIDA
--------------------------------------------
Hoje existem apenas 4 snapshots semanais de consenso (14/ago, 21/ago, 28/ago,
05/set). Para muitos tickers a resposta honesta e "sem dado". NAO se preenche
com a estimativa de hoje — isso seria look-ahead. Alem disso, a defasagem do
analista (ele revisa DEPOIS do evento) faz com que "sem lastro" em janela de
1 semana seja HIPOTESE, nao classificacao fechada. Isso vai impresso.

LEIS DA CASA APLICADAS (METODO_HCI_Pesquisa.md)
-----------------------------------------------
 - Nada em valor absoluto: a queda e medida em MULTIPLOS DO DESVIO semanal de
   52 semanas (z), nunca em "% fixo". Um -9% na AON e evento; um -50% na ALMS
   e rotina. O corte fixo inverteria a ordem.
 - Funil interno: logar onde os candidatos morrem em CADA etapa.
 - Maximo 3 filtros. Aqui: liquidez, z e idiossincrasia. O filtro de media de
   200 dias NAO filtra nada neste coletor — ele e GRAVADO como estado, porque
   HCI_Controle_Drawdown diz que metade da vantagem da carteira veio dele, e
   HCI_Swing_Acoes_ML diz que reversao a media so sobreviveu em UM regime.
   Essa tensao (quem cai forte perde a media) fica visivel, nao resolvida.
 - Cache/retomada e chave so via env (aqui nao ha chave nenhuma: EDGAR, Yahoo
   e Google News RSS sao todos abertos).
 - Refutacao e ativo: o ledger append-only existe para julgar o METODO daqui a
   N semanas. Sem ele nao ha julgamento possivel — cada semana nao gravada e
   perdida para sempre.

FONTES (todas gratuitas, nenhuma chave)
---------------------------------------
 - Preco: Yahoo chart (via yfinance, auto_adjust=True). AJUSTADO de proposito:
   preco bruto transforma desdobramento em "queda de 47%" (caso APH).
 - Universo e consenso PIT: os CSVs de data/estimates_snapshots (repo) e de
   C:/Trading/hci-ea/out/estimates_snapshots (pasta antiga). As duas sao lidas
   e unificadas em memoria, porque estao desalinhadas em disco.
 - Motivo: SEC EDGAR submissions (campo `items` do 8-K = o fato duro),
   yfinance upgrades_downgrades (analista, com data-hora, o que permite dizer
   se ele foi CAUSA ou REACAO) e Google News RSS (manchete = reforco, peso
   baixo, sempre marcada como inferencia).

SAIDAS
------
 data/fichas_queda.json     — as fichas da semana (sobrescrito por rodada, mas
                              so no fim e de forma atomica; se a coleta falhar,
                              o arquivo anterior fica intacto e sai sys.exit(1))
 data/fichas_queda.txt      — relatorio legivel, ordenado pela queda IDIOSSINCRATICA
 data/equities_ledger.jsonl — APPEND-ONLY, uma linha por ficha por semana, com
                              os campos de desfecho EM BRANCO para preencher depois.
                              Este arquivo NUNCA e sobrescrito.

Uso:  python ficha_queda.py            (rodada normal)
      python ficha_queda.py --z -1.5   (afrouxa o corte provisorio)
      python ficha_queda.py --max 25   (teto de fichas com motivo coletado)
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import html as H
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import warnings

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except Exception as e:  # pragma: no cover
    print("ERRO: dependencia ausente (%s: %s)" % (type(e).__name__, e))
    sys.exit(1)

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_DATA = os.path.join(AQUI, "data")
DIR_SNAP_REPO = os.path.join(DIR_DATA, "estimates_snapshots")
DIR_SNAP_VELHO = r"C:/Trading/hci-ea/out/estimates_snapshots"
OUT_JSON = os.path.join(DIR_DATA, "fichas_queda.json")
OUT_TXT = os.path.join(DIR_DATA, "fichas_queda.txt")
LEDGER = os.path.join(DIR_DATA, "equities_ledger.jsonl")
CACHE_CIK = os.path.join(DIR_DATA, "cache_cik_edgar.json")

# --------------------------------------------------------------------------
# REGUAS — todas PROVISORIAS ate haver pre-registro assinado pelo Eduardo.
# Nenhuma delas foi validada contra resultado; sao cortes de LEITURA, nao de
# entrada. Estao aqui em nome, nao espalhadas pelo codigo.
# --------------------------------------------------------------------------
# Versao do COLETOR. Entra em cada linha do ledger e faz parte da chave de
# idempotencia: coletor corrigido gera lancamento NOVO, nunca apaga o antigo.
#  v1.0  — primeira rodada (06/set/2026)
#  v1.1  — lastro pareado por ano fiscal COMUM aos dois snapshots, com tolerancia
#          de 7 dias (calendario 52/53 semanas). Corrige o falso "ano fiscal
#          mudou" causado pelo bug do limit=4 nos snapshots ate 28/ago.
#  v1.2  — 08/set/2026: o lastro deixou de ser SO um balde binario. Os tres estados
#          continuam identicos (a populacao do pre-registro nao muda), e ao lado
#          deles entram a FAIXA DE INCERTEZA do consenso (medida em epsHigh/epsLow/n)
#          e o rotulo FRONTEIRA para o caso que o dado nao separa. Como a forma de
#          MEDIR mudou, a linha nova e ANEXADA ao ledger ao lado da v1.1 — livro-razao
#          se corrige com lancamento novo, nunca com borracha.
VERSAO_COLETOR = "v1.2"

PISO_PRECO = 10.0          # dolares — piso do logger da casa
PISO_VOLUME = 500_000      # acoes/dia — piso do logger da casa
PISO_MCAP = 2e9            # valor de mercado — piso do revisoes.json
CORTE_Z = -2.0             # PROVISORIO: queda da semana em desvios de 52 semanas
MIN_SHARE_IDIO = 0.50      # PROVISORIO: a parcela propria tem de dominar
MIN_BARRAS = 210           # historico minimo para SMA200 + regua de 52 semanas
LIM_LASTRO = 3.0           # PROVISORIO: |var EPS| < 3% = "consenso parado"
LIM_SPLIT_PP = 3.0         # divergencia bruto x ajustado que denuncia desdobramento

# --------------------------------------------------------------------------
# O LASTRO DEIXOU DE SER UM BALDE BINARIO — conserto 2.3, 08/set/2026
# --------------------------------------------------------------------------
# O QUE ERA: LIM_LASTRO = 3,0 e um corte seco na PERGUNTA CENTRAL da ficha. Uma revisao de
# EPS de -2,9% saia "sem lastro" e uma de -3,1% saia "com lastro" — dois vereditos opostos
# separados por dois decimos, num numero que ninguem calibrou. E a mesma doenca do piso do
# ciclo e do penhasco de 180 dias: parametro nao calibrado decidindo veredito por um
# centesimo (AUDITORIA_AGREGADOS.md §2.3).
#
# O QUE ENTROU, E O QUE DELIBERADAMENTE NAO ENTROU:
#   - NAO entrou limiar novo. O 3,0 continua exatamente onde estava, e os TRES ESTADOS
#     ("com lastro" / "sem lastro" / "sem dado") continuam sendo calculados pela MESMA regra
#     binaria de sempre — a interface, o ledger e o PRE-REGISTRO de METODO_QUEDA.md §7
#     (cuja populacao primaria e "sem lastro") nao mudam de definicao. Trocar a populacao de
#     um pre-registro no meio do caminho seria garimpo.
#   - Entrou, AO LADO, uma GRADUACAO com FAIXA DE INCERTEZA DECLARADA. A incerteza nao e
#     inventada: ela e MEDIDA no proprio snapshot, na dispersao dos analistas que formam o
#     consenso (epsHigh, epsLow e numAnalystsEps ja estavam no CSV e nunca foram lidos).
#
#       meia_amplitude   = (epsHigh - epsLow) / 2
#       erro_da_media    ~ meia_amplitude / raiz(n)          (n = numAnalystsEps)
#       incerteza_pct    = 100 x erro_da_media / |epsAvg|
#       incerteza usada  = a MAIOR das duas pontas (snapshot antigo e snapshot novo)
#
#     Isto e a lei da casa aplicada onde ela ainda nao estava: "nada em valor absoluto" — a
#     queda ja era medida em multiplos do desvio (z), e agora a REVISAO tambem. O numero que
#     sai e `lastro_z` = var_eps_pct / incerteza_pct: quantos desvios do proprio consenso a
#     revisao andou.
#   - FRONTEIRA: quando a revisao esta a MENOS DE UMA INCERTEZA de qualquer uma das duas
#     bordas (-3,0 ou +3,0), o caso sai rotulado FRONTEIRA e NAO como veredito. Nao e um
#     limiar novo: e o limiar antigo mais a barra de erro que o proprio dado carrega.
#
# HONESTIDADE DA MEDIDA, declarada de proposito:
#   (a) meia amplitude / raiz(n) e um PROXY GROSSEIRO de erro padrao (amplitude nao e desvio).
#   (b) os dois snapshots compartilham quase todos os analistas, entao o erro se cancela em
#       boa parte na DIFERENCA — a banda daqui e um TETO do ruido, nao a medida exata dele.
#       Errar para o lado do "fronteira" e o erro barato: ele nao fabrica veredito, ele o
#       suspende.
#   (c) quando o snapshot nao permite medir (n < 2, ou epsHigh = epsLow, ou EPS perto de
#       zero), a incerteza sai NULL e o grau sai "sem incerteza medida" — nunca vira
#       silenciosamente "nao e fronteira".
FRONTEIRA_EM_INCERTEZAS = 1.0    # PROVISORIO: 1 barra de erro de cada lado da borda
GRAU_LASTRO = {
    "com_lastro": "com lastro",
    "fronteira": "FRONTEIRA",
    "consenso_parado": "sem lastro (consenso parado)",
    "divergente": "sem lastro (divergência: consenso SUBIU)",
    "sem_incerteza": "sem incerteza medida",
    "sem_dado": "sem dado",
}

UA_SEC = {"User-Agent": "HCI Research eduardogodooihoki@gmail.com"}
UA_WEB = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"}

SETOR_ETF = {
    "Technology": "XLK", "Financial Services": "XLF", "Healthcare": "XLV",
    "Energy": "XLE", "Consumer Cyclical": "XLY", "Consumer Defensive": "XLP",
    "Industrials": "XLI", "Basic Materials": "XLB", "Utilities": "XLU",
    "Real Estate": "XLRE", "Communication Services": "XLC",
}

# Itens do 8-K: e este campo que diz O QUE aconteceu, sem depender de manchete.
ITEM_8K = {
    "1.01": ("contrato material", "EMPRESA"),
    "1.02": ("fim de contrato material", "EMPRESA"),
    "1.03": ("falencia/recuperacao judicial", "EMPRESA"),
    "1.05": ("incidente de ciberseguranca", "EMPRESA"),
    "2.01": ("aquisicao/venda concluida", "EMPRESA"),
    "2.02": ("RESULTADO trimestral", "RESULTADO"),
    "2.03": ("nova divida/obrigacao", "EMPRESA"),
    "2.04": ("aceleracao de divida", "EMPRESA"),
    "2.05": ("custo de reestruturacao/demissao", "EMPRESA"),
    "2.06": ("baixa contabil (impairment)", "EMPRESA"),
    "3.01": ("aviso de deslistagem", "EMPRESA"),
    "3.02": ("OFERTA de acoes (diluicao)", "EMPRESA"),
    "3.03": ("mudanca de direitos do acionista", "EMPRESA"),
    "4.01": ("troca de auditor", "EMPRESA"),
    "4.02": ("demonstracoes NAO confiaveis (restatement)", "EMPRESA"),
    "5.01": ("mudanca de controle", "EMPRESA"),
    "5.02": ("saida/entrada de executivo ou conselheiro", "EMPRESA"),
    "5.03": ("mudanca de estatuto/ano fiscal", "EMPRESA"),
    "5.07": ("votacao de acionistas", "EMPRESA"),
    "7.01": ("Reg FD (guidance/apresentacao)", "GUIDANCE"),
    "8.01": ("outro evento relevante", "EMPRESA"),
    "9.01": ("anexos", "-"),
}

LEXICO = [
    ("guidance", ["guidance", "outlook", "forecast", "cuts view", "lowers view", "warns"]),
    ("resultado", ["earnings", "results", "quarter", " q1", " q2", " q3", " q4",
                   "beats", "misses", " eps", "revenue"]),
    ("rebaixamento de analista", ["downgrade", "downgraded", "cuts price target",
                                  "lowers target", "underweight", "sell rating"]),
    ("processo/regulador", ["lawsuit", "sues", "sued", "probe", "investigation",
                            "sec charges", "doj", "fine", "settlement", "subpoena"]),
    ("recall/produto", ["recall", "recalls", "defect", "safety", "fda reject", "crl"]),
    ("executivo", ["ceo", "cfo", "steps down", "resigns", "departure", "interim"]),
    ("oferta/diluicao", ["offering", "convertible", "secondary", "dilution"]),
    ("m&a", ["acquire", "acquisition", "merger", "takeover", "stake"]),
]


def log(msg=""):
    print(msg, flush=True)


# ==========================================================================
# 0. INFRAESTRUTURA DE REDE (sem chave; retentador com espera crescente)
# ==========================================================================
def _http(url, hdr, tent=3, como_json=True, pausa=0.15):
    for i in range(tent):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=30) as r:
                b = r.read()
            time.sleep(pausa)
            return json.loads(b) if como_json else b.decode("utf-8", "replace")
        except Exception:
            if i == tent - 1:
                return None
            time.sleep(1.5 * (i + 1))
    return None


def mapa_cik():
    """ticker -> (CIK, razao social). Cache de 7 dias em disco (lei 11)."""
    if os.path.exists(CACHE_CIK) and time.time() - os.path.getmtime(CACHE_CIK) < 7 * 86400:
        try:
            return json.load(open(CACHE_CIK, encoding="utf-8"))
        except Exception:
            pass
    m = _http("https://www.sec.gov/files/company_tickers.json", UA_SEC)
    if not m:
        return {}
    d = {v["ticker"]: [str(v["cik_str"]).zfill(10), v["title"]] for v in m.values()}
    try:
        json.dump(d, open(CACHE_CIK, "w", encoding="utf-8"))
    except Exception:
        pass
    return d


# ==========================================================================
# 1. UNIVERSO — os tickers que a casa ja acompanha, com piso de liquidez
# ==========================================================================
def carrega_snapshots():
    """Le as DUAS pastas de snapshot e unifica. Elas estao desalinhadas em disco:
    a antiga (C:/Trading) parou em 28/ago; a do repo tem tambem o de 05/set."""
    arquivos = {}
    for d in (DIR_SNAP_VELHO, DIR_SNAP_REPO):
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "estimates_*.csv"))):
            data = os.path.basename(f)[10:20]
            arquivos.setdefault(data, f)       # repo NAO sobrescreve o que ja veio
            if d == DIR_SNAP_REPO:
                arquivos[data] = f             # ...exceto: o repo e a versao boa
    return dict(sorted(arquivos.items()))


def universo(snaps):
    if len(snaps) < 1:
        raise RuntimeError("nenhum snapshot de estimativas encontrado")
    datas = list(snaps.keys())
    d_ini, d_fim = datas[-2] if len(datas) >= 2 else datas[-1], datas[-1]
    a = pd.read_csv(snaps[d_ini])
    b = pd.read_csv(snaps[d_fim])

    def meta(df):
        return df.groupby("symbol").agg(preco=("price", "first"),
                                        mcap=("marketCap", "first"),
                                        volume=("volume", "first"),
                                        setor=("sector", "first"))

    mb = meta(b)
    ma = meta(a)
    total = len(mb)
    liq = mb[(mb.preco >= PISO_PRECO) & (mb.volume > PISO_VOLUME) & (mb.mcap > PISO_MCAP)].copy()
    liq["preco_snap_ant"] = ma.preco.reindex(liq.index)
    return liq, total, d_ini, d_fim


# ==========================================================================
# 2. CAIU — z semanal com o desvio das 52 semanas ANTERIORES
# ==========================================================================
def baixa_precos(tickers, lote=150):
    """Precos AJUSTADOS. Bruto transformaria desdobramento em queda fantasma."""
    quadros = []
    tk = sorted(set(tickers))
    for i in range(0, len(tk), lote):
        parte = tk[i:i + lote]
        for tent in range(3):
            try:
                px = yf.download(parte, period="2y", progress=False,
                                 auto_adjust=True, threads=True)["Close"]
                if isinstance(px, pd.Series):
                    px = px.to_frame(parte[0])
                quadros.append(px)
                break
            except Exception:
                if tent == 2:
                    log("  aviso: lote %d-%d falhou 3x, seguindo sem ele" % (i, i + len(parte)))
                else:
                    time.sleep(3 * (tent + 1))
        log("  precos: %d/%d" % (min(i + lote, len(tk)), len(tk)))
    if not quadros:
        raise RuntimeError("nenhum preco baixado")
    px = pd.concat(quadros, axis=1)
    px = px.loc[:, ~px.columns.duplicated()]
    return px.dropna(axis=1, how="all")


def semanal(serie):
    """Fechamento por semana ISO. Devolve (lista de closes semanais, ultima data)."""
    s = serie.dropna()
    if s.empty:
        return [], None
    iso = [(d.isocalendar()[0], d.isocalendar()[1]) for d in s.index]
    ult = {}
    for k, v in zip(iso, s.values):
        ult[k] = v
    return [ult[k] for k in sorted(ult)], s.index[-1]


def metricas_preco(serie):
    s = serie.dropna()
    if len(s) < MIN_BARRAS:
        return {"erro": "historico curto: %d barras" % len(s)}
    c = s.values
    wc, ult = semanal(s)
    if len(wc) < 40:
        return {"erro": "poucas semanas: %d" % len(wc)}
    wr = [wc[i] / wc[i - 1] - 1.0 for i in range(1, len(wc))]
    hist = wr[-53:-1]                     # 52 semanas ANTERIORES: a semana corrente
    if len(hist) < 30:                    # nao pode inflar a propria regua (achado
        return {"erro": "regua curta"}    # da sonda: z encolhia 10-25%)
    sd = float(np.std(hist))
    if sd <= 0:
        return {"erro": "desvio nulo"}
    var = wr[-1]
    sma200 = float(np.mean(c[-200:]))
    return {
        "ult_data": str(pd.Timestamp(ult).date()),
        "preco": round(float(c[-1]), 4),
        "var_semana_pct": round(100 * var, 2),
        "sd_semanal_52_pct": round(100 * sd, 2),
        "z_semana": round(var / sd, 2),
        "sma200": round(sma200, 4),
        "acima_sma200": bool(c[-1] > sma200),
        "dist_sma200_pct": round(100 * (c[-1] / sma200 - 1), 2),
        "n_barras": int(len(s)),
    }


# ==========================================================================
# 3. IDIOSSINCRATICA — decomposicao mercado / setor / residuo
# ==========================================================================
def decompoe(tic, setor, px, d0, d1, jan=252):
    """r_i = a + bm*r_SPY + bs*(r_ETF ortogonalizado contra SPY) + e
    Betas em ~52 semanas de retorno DIARIO que ENCERRAM antes da semana julgada
    (sem look-ahead). O ETF e ortogonalizado para o beta de mercado nao ser
    roubado pela colinearidade."""
    etf = SETOR_ETF.get(setor)
    if etf is None or tic not in px.columns or "SPY" not in px.columns or etf not in px.columns:
        return {"erro": "sem ETF de setor mapeado (%s)" % setor}
    R = np.log(px[[tic, "SPY", etf]].astype(float)).diff().dropna()
    est = R.iloc[-(jan + 1):-5]
    if len(est) < 120:
        return {"erro": "janela de estimacao curta (%d)" % len(est)}
    y, m, s = est[tic].values, est["SPY"].values, est[etf].values
    b_sm = float(np.polyfit(m, s, 1)[0])
    s_ort = s - b_sm * m
    X = np.column_stack([np.ones(len(m)), m, s_ort])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    _, bm, bs = coef
    resid = y - X @ coef
    try:
        Rm = math.log(px.loc[d1, "SPY"] / px.loc[d0, "SPY"])
        Rs = math.log(px.loc[d1, etf] / px.loc[d0, etf])
        Ri = math.log(px.loc[d1, tic] / px.loc[d0, tic])
    except Exception:
        return {"erro": "sem preco nas duas pontas da semana"}
    if any(map(lambda v: v != v, (Rm, Rs, Ri))):
        return {"erro": "preco NaN na janela"}
    Rs_ort = Rs - b_sm * Rm
    c_mkt, c_set = bm * Rm, bs * Rs_ort
    idio = Ri - c_mkt - c_set
    denom = abs(c_mkt) + abs(c_set) + abs(idio)
    return {
        "etf_setor": etf,
        "beta_mercado": round(float(bm), 3),
        "beta_setor": round(float(bs), 3),
        "r2": round(float(1 - resid.var() / y.var()), 3),
        "n_dias_estimacao": int(len(est)),
        "ret_total_pct": round((math.exp(Ri) - 1) * 100, 2),
        "mercado_pp": round((math.exp(c_mkt) - 1) * 100, 2),
        "setor_pp": round((math.exp(c_set) - 1) * 100, 2),
        "idiossincratico_pp": round((math.exp(idio) - 1) * 100, 2),
        "spy_semana_pct": round((math.exp(Rm) - 1) * 100, 2),
        "etf_semana_pct": round((math.exp(Rs) - 1) * 100, 2),
        "parcela_idio": round(abs(idio) / denom, 3) if denom else None,
    }


# ==========================================================================
# 4. LASTRO — a pergunta central
# ==========================================================================
_CACHE_SNAP = {}


def _le_snap(caminho):
    """Le o CSV do snapshot UMA vez por rodada. Sem isto o coletor releria o
    arquivo inteiro (18 mil linhas) uma vez por ticker."""
    if caminho not in _CACHE_SNAP:
        # epsHigh/epsLow entraram em 08/set: e deles que sai a FAIXA DE INCERTEZA do
        # consenso, que transforma o balde binario do lastro em classificacao graduada.
        base = ["symbol", "fy_date", "epsAvg", "revenueAvg", "numAnalystsEps"]
        try:
            _CACHE_SNAP[caminho] = pd.read_csv(
                caminho, usecols=base + ["epsHigh", "epsLow"])
        except ValueError:
            # ⚠️ REFUTADOR, 08/set: sem este resgate um snapshot antigo (ou de outra fonte)
            # SEM as duas colunas novas derrubava a rodada inteira com ValueError. O modulo
            # ja declara o que fazer quando a incerteza nao pode ser medida — "sem incerteza
            # medida", com fronteira=None. Entao o caminho degrada para isso em vez de morrer:
            # os TRES ESTADOS do lastro continuam saindo (eles nao dependem destas colunas) e
            # so a GRADUACAO fica sem faixa. Buraco declarado, nao falha silenciosa.
            df = pd.read_csv(caminho, usecols=base)
            df["epsHigh"] = float("nan")
            df["epsLow"] = float("nan")
            print("  ! snapshot sem epsHigh/epsLow (%s): a graduacao sai 'sem incerteza "
                  "medida'; os tres estados do lastro nao mudam"
                  % os.path.basename(caminho))
            _CACHE_SNAP[caminho] = df
    return _CACHE_SNAP[caminho]


def incerteza_do_consenso(linha):
    """A FAIXA DE INCERTEZA do consenso, medida no proprio snapshot (08/set/2026).

    O consenso e uma MEDIA de analistas, e media tem erro. O CSV ja trazia epsHigh, epsLow e
    numAnalystsEps — tres colunas que nunca tinham sido lidas. Delas sai, sem inventar
    calibracao nenhuma:

        meia_amplitude = (epsHigh - epsLow) / 2
        erro_da_media  ~ meia_amplitude / raiz(n)
        incerteza_pct  = 100 x erro_da_media / |epsAvg|

    E um PROXY GROSSEIRO e esta dito: amplitude nao e desvio-padrao, e amplitude/raiz(n) tende
    a SUPERESTIMAR o erro da media quando n e grande. Superestimar aqui e o erro barato — ele
    joga o caso para FRONTEIRA, que suspende veredito em vez de fabricar um.

    Devolve (incerteza_pct ou None, detalhe). None quando nao da para medir: n < 2, amplitude
    nula (um analista so, ou todos no mesmo numero) ou EPS perto de zero (a razao explode).
    """
    eps, alto, baixo, n = (linha.get("eps"), linha.get("eps_alto"),
                           linha.get("eps_baixo"), linha.get("n"))
    det = {"eps": eps, "eps_alto": alto, "eps_baixo": baixo, "n_analistas": n}
    if eps is None or abs(eps) < 0.10:
        det["motivo"] = "EPS perto de zero: a incerteza relativa explode"
        return None, det
    if alto is None or baixo is None or not (alto > baixo):
        det["motivo"] = "sem amplitude no snapshot (epsHigh = epsLow, ou coluna ausente)"
        return None, det
    if not n or n < 2:
        det["motivo"] = "um analista so: amplitude nao mede dispersao de opiniao"
        return None, det
    meia = (alto - baixo) / 2.0
    erro = meia / math.sqrt(n)
    inc = round(100.0 * erro / abs(eps), 2)
    det.update({"meia_amplitude": round(meia, 4), "erro_da_media": round(erro, 4),
                "incerteza_pct": inc})
    return inc, det


def graduacao_do_lastro(var_eps_pct, incerteza_pct):
    """A CLASSIFICACAO GRADUADA, ao lado dos tres estados — nao no lugar deles.

    O corte de 3,0 fica onde estava; o que muda e que ele passa a andar acompanhado da barra
    de erro do proprio consenso. A revisao e lida em MULTIPLOS dessa barra (`lastro_z`), que e
    a mesma lei que ja governa a queda (z semanal) — "nada em valor absoluto".

    FRONTEIRA quando a revisao esta a menos de UMA incerteza de qualquer uma das duas bordas
    (-3,0 ou +3,0): ali o dado nao distingue os dois baldes, e chamar de veredito seria
    inventar precisao. Devolve um dicionario; nunca altera `classe_lastro`.
    """
    if var_eps_pct is None:
        return {"grau": GRAU_LASTRO["sem_dado"], "fronteira": None,
                "texto": "sem par nos snapshots ponto-no-tempo: nao ha revisao para graduar"}
    de = float(var_eps_pct)
    dist_baixo = abs(de - (-LIM_LASTRO))       # distancia ate a borda do "com lastro"
    dist_alto = abs(de - LIM_LASTRO)           # distancia ate a borda da "divergencia"
    borda, dist = (("-%.1f%%" % LIM_LASTRO, dist_baixo) if dist_baixo <= dist_alto
                   else ("+%.1f%%" % LIM_LASTRO, dist_alto))
    base = {"var_eps_pct": round(de, 2), "incerteza_eps_pct": incerteza_pct,
            "limiar_pct": LIM_LASTRO, "borda_mais_proxima": borda,
            "distancia_ate_a_borda_pp": round(dist, 2),
            "fronteira_em_incertezas": FRONTEIRA_EM_INCERTEZAS, "provisorio": True}
    if incerteza_pct is None:
        base.update({
            "grau": GRAU_LASTRO["sem_incerteza"], "fronteira": None, "lastro_z": None,
            "texto": "revisao de %+.2f%%, a %.2f pp da borda de %s — mas a incerteza do "
                     "consenso NAO pode ser medida neste snapshot, entao nao da para dizer se "
                     "o caso esta ou nao na fronteira. Isto e buraco declarado, nao 'longe da "
                     "borda'." % (de, dist, borda)})
        return base
    faixa = FRONTEIRA_EM_INCERTEZAS * incerteza_pct
    z = round(de / incerteza_pct, 2) if incerteza_pct else None
    base["lastro_z"] = z
    base["faixa_de_fronteira_pp"] = round(faixa, 2)
    if dist <= faixa:
        base.update({
            "grau": GRAU_LASTRO["fronteira"], "fronteira": True,
            "texto": "FRONTEIRA: revisao de %+.2f%% esta a %.2f pp da borda de %s, e a "
                     "incerteza do proprio consenso e +-%.2f pp. O dado NAO separa 'com "
                     "lastro' de 'sem lastro' aqui — isto e fronteira, nao veredito. A "
                     "revisao vale %s desvios do proprio consenso."
                     % (de, dist, borda, incerteza_pct,
                        ("%+.2f" % z) if z is not None else "n/d")})
        return base
    if de <= -LIM_LASTRO:
        g, t = GRAU_LASTRO["com_lastro"], "o consenso de lucro caiu junto com o preco"
    elif de >= LIM_LASTRO:
        g, t = GRAU_LASTRO["divergente"], "o consenso SUBIU com o preco caindo"
    else:
        g, t = GRAU_LASTRO["consenso_parado"], "o consenso praticamente nao se moveu"
    base.update({"grau": g, "fronteira": False,
                 "texto": "%s: revisao de %+.2f%% (%s desvios do proprio consenso, incerteza "
                          "+-%.2f pp), a %.2f pp da borda de %s — fora da faixa de fronteira."
                          % (t, de, ("%+.2f" % z) if z is not None else "n/d", incerteza_pct,
                             dist, borda)})
    return base


def revisao_pit(tic, snaps, d_ini, d_fim, tol_dias=7):
    """Compara o consenso de EPS do MESMO ano fiscal entre dois snapshots
    ponto-no-tempo. Nunca preenche com a estimativa de hoje: sem par, a resposta
    e 'sem dado'.

    DOIS DEFEITOS REAIS DA BASE, TRATADOS AQUI E DECLARADOS NA SAIDA
    ----------------------------------------------------------------
    (a) O estimates_logger.py rodava com limit=4 ate 30/ago, e o FMP devolve os
        anos fiscais em ordem DECRESCENTE — ou seja, os snapshots de 14, 21 e
        28/ago guardaram os QUATRO ANOS MAIS DISTANTES, nao o FY1. Medido:
        28/ago tem 3,99 linhas por ticker; 05/set tem 11,08. Por isso comparar
        "o primeiro FY futuro de cada snapshot" devolvia FY2028 contra FY2027 e
        matava 10 dos 20 candidatos com um falso "ano fiscal mudou".
        O certo e parear pelo ano fiscal COMUM aos dois snapshots. Quando o ano
        comum mais proximo NAO for o FY1 do snapshot recente, isso vai gravado
        em `fy_e_o_primeiro` e sai impresso — porque revisao de FY2 e um dado
        mais fraco que revisao de FY1, e esconder a diferenca seria mentir.
        CONSEQUENCIA A DECLARAR: a serie PIT de FY1 so comeca em 05/set/2026.
    (b) Calendario fiscal de 52/53 semanas move a data do fechamento em ate uma
        semana (CPB: 2027-08-03 no snapshot antigo e 2027-08-02 no novo). Sao o
        MESMO exercicio. Por isso o pareamento tem tolerancia de +-`tol_dias`.
    """
    def futuros(data):
        f = snaps.get(data)
        if not f:
            return None, "snapshot ausente"
        try:
            df = _le_snap(f)
        except Exception as e:
            return None, "csv ilegivel (%s)" % type(e).__name__
        df = df[df.symbol == tic]
        if df.empty:
            return None, "ticker fora do snapshot de %s" % data
        df = df[df.fy_date > data].sort_values("fy_date")
        if df.empty:
            return None, "sem ano fiscal futuro em %s" % data
        return [{"fy": r.fy_date, "eps": float(r.epsAvg),
                 "eps_alto": float(r.epsHigh) if pd.notna(r.epsHigh) else None,
                 "eps_baixo": float(r.epsLow) if pd.notna(r.epsLow) else None,
                 "receita": float(r.revenueAvg) if pd.notna(r.revenueAvg) else None,
                 "n": int(r.numAnalystsEps) if pd.notna(r.numAnalystsEps) else None}
                for _, r in df.iterrows()], None

    LA, e1 = futuros(d_ini)
    LB, e2 = futuros(d_fim)
    if LA is None or LB is None:
        return None, (e1 or e2)

    def dias(x, y):
        return abs((dt.date.fromisoformat(x) - dt.date.fromisoformat(y)).days)

    par = None
    for ib, b in enumerate(LB):                       # LB ja vem do mais proximo
        for a in LA:
            if dias(a["fy"], b["fy"]) <= tol_dias:
                par = (a, b, ib)
                break
        if par:
            break
    if par is None:
        return None, ("nenhum ano fiscal comum aos dois snapshots "
                      "(antigo %s | atual %s) — snapshot antigo so tem os FYs distantes"
                      % (LA[0]["fy"], LB[0]["fy"]))

    a, b, ib = par
    if not a["eps"] or abs(a["eps"]) < 0.10:
        return None, "EPS base proximo de zero (%.4f) — a razao explode" % a["eps"]
    inc_a, det_a = incerteza_do_consenso(a)
    inc_b, det_b = incerteza_do_consenso(b)
    # A MAIOR das duas pontas. Os dois snapshots compartilham quase todos os analistas, entao
    # o erro se cancela em parte na diferenca: esta banda e um TETO do ruido, e o teto e o
    # lado barato de errar (suspende veredito, nunca fabrica).
    candidatas = [x for x in (inc_a, inc_b) if x is not None]
    incerteza = round(max(candidatas), 2) if candidatas else None
    return {
        "fy": b["fy"],
        "fy_snapshot_antigo": a["fy"],
        "fy_ordem_no_snapshot_atual": ib + 1,
        "fy_e_o_primeiro": ib == 0,
        "eps_antes": round(a["eps"], 4),
        "eps_depois": round(b["eps"], 4),
        "var_eps_pct": round((b["eps"] / a["eps"] - 1) * 100, 2),
        "var_receita_pct": (round((b["receita"] / a["receita"] - 1) * 100, 2)
                            if a["receita"] and b["receita"] else None),
        "n_analistas": b["n"],
        "n_analistas_antes": a["n"],
        # composicao: se o numero de analistas mudou, parte da "revisao" e gente diferente
        # opinando, nao analista mudando de ideia. Fica GRAVADO; nao entra na regra.
        "composicao_mudou": (a["n"] is not None and b["n"] is not None and a["n"] != b["n"]),
        # ---- FAIXA DE INCERTEZA, medida no proprio consenso (08/set) ------------------
        "incerteza_eps_pct": incerteza,
        "incerteza_detalhe": {"snapshot_antigo": det_a, "snapshot_atual": det_b,
                              "usada": "a maior das duas",
                              "formula": "100 x ((epsHigh - epsLow)/2) / raiz(n) / |epsAvg|",
                              "e_um_teto": "os dois snapshots compartilham analistas, entao o "
                                           "erro se cancela em parte na diferenca",
                              "provisorio": True},
    }, None


def classe_lastro(var_preco_pct, rev):
    """Tres baldes obrigatorios. 'sem dado' NUNCA vira 'sem lastro'."""
    if rev is None:
        return "sem dado", None, None
    dp, de = var_preco_pct, rev["var_eps_pct"]
    razao = round(de / dp, 3) if dp else None       # quanto do preco o lucro acompanhou
    if de <= -LIM_LASTRO:
        cl, obs = "com lastro", "o consenso de lucro caiu junto com o preco"
    elif de >= LIM_LASTRO:
        cl, obs = "sem lastro", "DIVERGENCIA: o consenso SUBIU com o preco caindo"
    else:
        cl, obs = "sem lastro", "consenso praticamente parado"
    if not rev.get("fy_e_o_primeiro", True):
        # Dado mais fraco: e revisao do FY%d, nao do FY1. Vai dito, nao escondido.
        obs += ("  [ATENCAO: comparado no FY%d (%s), nao no FY1 — o snapshot de %s"
                " so guardou os anos fiscais distantes (bug do limit=4). A serie"
                " PIT de FY1 comeca em 05/set/2026.]"
                % (rev["fy_ordem_no_snapshot_atual"], rev["fy"], rev["fy_snapshot_antigo"]))
    return cl, razao, obs


# ==========================================================================
# 5. MOTIVO — 8-K da SEC (fato duro), analista (com hora) e manchete (reforco)
# ==========================================================================
def edgar(tic, cikmap, ini, fim):
    if tic not in cikmap:
        return {"erro": "ticker sem CIK (emissor estrangeiro arquiva 20-F/6-K, sem campo items)",
                "filings": [], "nome": None, "form4_n": None}
    cik, nome = cikmap[tic]
    d = _http("https://data.sec.gov/submissions/CIK%s.json" % cik, UA_SEC)
    if not d:
        return {"erro": "submissions nao respondeu", "filings": [], "nome": nome, "form4_n": None}
    rec = d.get("filings", {}).get("recent", {})
    n = len(rec.get("form", []))
    saida, f4 = [], 0
    for i in range(n):
        data = rec["filingDate"][i]
        if not (ini <= data <= fim):
            continue
        form = rec["form"][i]
        if form == "4":
            f4 += 1
            continue
        itens = []
        for it in re.findall(r"\d+\.\d+", (rec.get("items") or [""] * n)[i] or ""):
            rot, cls = ITEM_8K.get(it, ("item nao mapeado", "EMPRESA"))
            itens.append({"item": it, "rotulo": rot, "classe": cls})
        acc = rec["accessionNumber"][i].replace("-", "")
        saida.append({
            "form": form, "data": data, "itens": itens,
            "link": "https://www.sec.gov/Archives/edgar/data/%d/%s/%s"
                    % (int(cik), acc, rec["primaryDocument"][i]),
        })
    return {"nome": nome, "cik": cik, "filings": saida, "form4_n": f4, "erro": None}


def google_news(consulta, n=6):
    u = ("https://news.google.com/rss/search?q=%s&hl=en-US&gl=US&ceid=US:en"
         % urllib.parse.quote(consulta))
    xml = _http(u, UA_WEB, como_json=False, pausa=1.0)
    if not xml:
        return []
    out = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S)[:n]:
        def campo(t):
            m = re.search(r"<%s[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (t, t), it, re.S)
            return H.unescape(m.group(1).strip()) if m else ""
        tit = re.sub(r"<[^>]+>", "", campo("title"))
        fon = campo("source")
        if not fon and " - " in tit:
            tit, fon = tit.rsplit(" - ", 1)
        out.append({"titulo": tit, "fonte": fon, "publicado": campo("pubDate"),
                    "link": campo("link")})
    return out


def rotula(titulos):
    t = " | ".join(titulos).lower()
    return [rot for rot, chaves in LEXICO if any(k in t for k in chaves)]


def analistas(tic, ini, fim):
    try:
        ud = yf.Ticker(tic).upgrades_downgrades
        if ud is None or not len(ud):
            return []
        j = ud[(ud.index >= ini) & (ud.index < fim)]
        return [{"data": str(i)[:19], "casa": r.get("Firm"),
                 "de": r.get("FromGrade"), "para": r.get("ToGrade"),
                 "acao": r.get("Action"), "alvo": r.get("priceTargetAction"),
                 "pt_novo": r.get("currentPriceTarget"), "pt_velho": r.get("priorPriceTarget")}
                for i, r in j.iterrows()]
    except Exception:
        return []


def monta_motivo(F):
    """Ordem dura: EDGAR manda (fato registrado), analista entra com a HORA
    (para dizer se foi causa ou reacao), manchete so reforca e vai marcada
    como inferencia. Sem nada: 'motivo nao identificado' — que e informacao."""
    E = F["edgar"]
    itens = [(f, i) for f in E.get("filings", []) for i in f.get("itens", [])]
    prioridade = ["2.02", "4.02", "1.03", "3.02", "2.06", "2.05", "5.02", "1.05",
                  "2.01", "5.01", "7.01", "1.01", "1.02", "8.01"]
    for p in prioridade:
        for f, i in itens:
            if i["item"] == p:
                return {"motivo": "%s (8-K item %s)" % (i["rotulo"].upper(), p),
                        "data": f["data"], "fonte": "SEC EDGAR 8-K", "link": f["link"],
                        "confianca": "fato registrado"}
    if itens:
        f, i = itens[0]
        return {"motivo": "8-K: %s" % i["rotulo"], "data": f["data"],
                "fonte": "SEC EDGAR 8-K", "link": f["link"], "confianca": "fato registrado"}
    for f in E.get("filings", []):
        if f["form"] in ("10-Q", "10-K", "8-K/A", "424B5", "S-3", "SC 13D/A"):
            return {"motivo": "arquivamento %s na janela (sem item de 8-K)" % f["form"],
                    "data": f["data"], "fonte": "SEC EDGAR", "link": f["link"],
                    "confianca": "fato registrado"}
    reb = [a for a in (F.get("analistas") or [])
           if str(a.get("acao", "")).startswith("down") or a.get("alvo") == "Lowers"]
    if reb:
        r = sorted(reb, key=lambda x: x["data"])[0]
        alvo = ""
        if r.get("pt_velho") and r.get("pt_novo"):
            alvo = " (alvo %s -> %s)" % (r["pt_velho"], r["pt_novo"])
        return {"motivo": "movimento de analista: %s %s->%s%s (%d evento(s) na semana)"
                          % (r.get("casa"), r.get("de"), r.get("para"), alvo, len(reb)),
                "data": r["data"][:10], "fonte": "Yahoo upgrades_downgrades",
                "link": "https://finance.yahoo.com/quote/%s/analysis" % F["ticker"],
                "confianca": "fato de terceiro (nao e registro da empresa)"}
    rot = F.get("rotulos_manchete") or []
    news = F.get("noticias") or []
    if rot and news:
        return {"motivo": "sem 8-K na janela; manchete sugere: " + ", ".join(rot),
                "data": None, "fonte": "Google News (%s)" % (news[0].get("fonte") or "?"),
                "link": news[0].get("link"), "confianca": "INFERENCIA por manchete (peso baixo)"}
    if news:
        return {"motivo": "sem 8-K e sem lexico reconhecido; manchete: %s" % news[0]["titulo"][:120],
                "data": None, "fonte": "Google News (%s)" % (news[0].get("fonte") or "?"),
                "link": news[0].get("link"), "confianca": "INFERENCIA por manchete (peso baixo)"}
    return {"motivo": "motivo nao identificado", "data": None, "fonte": None,
            "link": None, "confianca": "nenhuma fonte na janela — isto e informacao, nao falha"}


def papel_do_analista(F):
    reb = F.get("analistas") or []
    if not reb:
        return "sem movimento de analista na janela"
    datas_8k = [f["data"] for f in F["edgar"].get("filings", []) if f.get("itens")]
    if not datas_8k:
        return "movimento de analista SEM 8-K na janela — candidato a causa"
    d8 = min(datas_8k)
    if all(a["data"][:10] >= d8 for a in reb):
        return "REACAO ao evento (todo movimento veio depois do 8-K de %s)" % d8
    return "ha movimento de analista ANTERIOR ao 8-K de %s — possivel causa" % d8


# ==========================================================================
# GRAVACAO
# ==========================================================================
def grava_atomico(caminho, texto):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(texto)
    os.replace(tmp, caminho)


def append_ledger(fichas, semana_ini, semana_fim):
    """APPEND-ONLY. Nunca sobrescreve, nunca reescreve linha antiga.

    Idempotente por (semana_fim, ticker, VERSAO_COLETOR): rodar duas vezes com o
    mesmo coletor nao duplica linha. Mas quando o coletor e CORRIGIDO (mudou a
    forma de medir), a linha nova e ANEXADA ao lado da velha em vez de apagar a
    velha — e assim que se corrige um livro-razao: com um lancamento novo, nao
    com borracha. Quem for julgar o metodo depois deve ler, por (semana, ticker),
    a linha de MAIOR versao; as anteriores ficam de trilha de auditoria."""
    ja = set()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            for linha in f:
                try:
                    r = json.loads(linha)
                    ja.add((r.get("semana_fim"), r.get("ticker"),
                            r.get("versao_coletor")))
                except Exception:
                    continue
    novas = 0
    with open(LEDGER, "a", encoding="utf-8") as f:
        for F in fichas:
            if (semana_fim, F["ticker"], VERSAO_COLETOR) in ja:
                continue
            d = F.get("decomposicao") or {}
            lz = F.get("lastro") or {}
            linha = {
                "gravado_em": dt.datetime.now().isoformat(timespec="seconds"),
                "versao_coletor": VERSAO_COLETOR,
                "semana_ini": semana_ini, "semana_fim": semana_fim,
                "ticker": F["ticker"], "nome": F.get("nome"), "setor": F.get("setor"),
                "preco_fechamento": F.get("preco"),
                "queda_semana_pct": F.get("var_semana_pct"),
                "z_semana": F.get("z_semana"),
                "idiossincratico_pp": d.get("idiossincratico_pp"),
                "classe_lastro": F.get("classe_lastro"),
                "var_eps_pct": lz.get("var_eps_pct"),
                "lastro_fy": lz.get("fy"),
                "lastro_fy_e_o_primeiro": lz.get("fy_e_o_primeiro"),
                "razao_eps_preco": F.get("razao_eps_preco"),
                "lastro_grau": F.get("lastro_grau"),
                "lastro_fronteira": F.get("lastro_fronteira"),
                "lastro_z": F.get("lastro_z"),
                "incerteza_eps_pct": F.get("incerteza_eps_pct"),
                "motivo_sem_dado": F.get("motivo_sem_dado"),
                "acima_sma200": F.get("acima_sma200"),
                "motivo": (F.get("motivo") or {}).get("motivo"),
                # --- campos de DESFECHO, deliberadamente em branco ---
                # Sem eles nao existe julgamento do metodo daqui a N semanas.
                "preco_1sem": None, "preco_4sem": None, "preco_12sem": None,
                "ret_1sem_pct": None, "ret_4sem_pct": None, "ret_12sem_pct": None,
                "ret_1sem_vs_spy_pp": None, "ret_4sem_vs_spy_pp": None,
                "ret_12sem_vs_spy_pp": None,
                "reverteu": None, "eps_revisado_depois_pct": None,
                "lastro_confirmado": None, "nota_eduardo": None,
                "preenchido_em": None,
            }
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            novas += 1
    return novas


def relatorio(fichas, funil, meta):
    L = []
    A = L.append
    A("=" * 100)
    A("HCI — FICHAS DE QUEDA | semana %s -> %s | gerado em %s"
      % (meta["semana_ini"], meta["semana_fim"], meta["gerado_em"]))
    A("=" * 100)
    A("Isto e DADO e CLASSIFICACAO. Nao e recomendacao, nao e sinal de entrada,")
    A("nao ha promessa de retorno. A decisao e a tecnica de entrada sao do Eduardo.")
    A("")
    A("CONTEXTO DA SEMANA: SPY %+.2f%%" % meta["spy_pct"] if meta.get("spy_pct") is not None else "")
    A("")
    A("-" * 100)
    A("FUNIL (onde os candidatos morreram)")
    A("-" * 100)
    for k, v in funil:
        A("  %-58s %s" % (k, v))
    A("")
    A("-" * 100)
    A("LIMITE DECLARADO — a serie ponto-no-tempo tem %d snapshots (%s)."
      % (meta["n_snaps"], ", ".join(meta["snaps"])))
    A("Para muitos tickers a resposta honesta e 'sem dado'. Nao foi preenchido com")
    A("estimativa de hoje: isso seria look-ahead. Alem disso o analista revisa DEPOIS")
    A("do evento, entao 'sem lastro' em janela de 1 semana e HIPOTESE, nao veredito.")
    A("-" * 100)
    A("  com lastro: %d   |   sem lastro: %d   |   sem dado: %d"
      % (meta["n_com"], meta["n_sem"], meta["n_semdado"]))
    A("")
    A("  GRADUACAO COM FAIXA DE INCERTEZA (08/set/2026) — o limiar de %.1f%% NAO mudou e os"
      % meta["limiar_lastro_pct"])
    A("  tres estados acima continuam identicos (a populacao do pre-registro nao muda). Ao")
    A("  lado deles entra a incerteza do PROPRIO consenso, medida no snapshot:")
    A("      meia amplitude (epsHigh-epsLow)/2 / raiz(n analistas), em % do EPS")
    A("  Quando a revisao esta a menos de UMA incerteza da borda (%+.1f%% ou %+.1f%%), o caso"
      % (-meta["limiar_lastro_pct"], meta["limiar_lastro_pct"]))
    A("  sai rotulado FRONTEIRA — o dado nao separa os dois baldes, e chamar isso de veredito")
    A("  seria inventar precisao. Nenhum numero novo foi calibrado.")
    A("     na FAIXA DE FRONTEIRA: %d de %d ficha(s)   |   com dado mas sem incerteza"
      % (meta.get("n_fronteira", 0), meta["n_com"] + meta["n_sem"]))
    A("     mensuravel no snapshot: %d   |   sem dado nenhum: %d"
      % (meta.get("n_sem_incerteza", 0), meta["n_semdado"]))
    A("  DEFEITO CONHECIDO DA BASE, declarado: ate 30/ago o logger gravava limit=4 e o")
    A("  FMP devolve os anos fiscais em ordem DECRESCENTE — os snapshots de 14, 21 e")
    A("  28/ago guardaram os anos MAIS DISTANTES (3,99 linhas por ticker) e nao o FY1")
    A("  (o de 05/set tem 11,08). Por isso %d ficha(s) com dado foram medidas em FY"
      % meta.get("n_fy_distante", 0))
    A("  DISTANTE e nao no FY1 — marcado ficha a ficha. A serie PIT de FY1 so comeca")
    A("  em 05/set/2026, e e dela que sai o teste de lastro forte a partir de 12/set.")
    A("")
    if not fichas:
        A("Nenhuma ficha nesta semana com os cortes provisorios vigentes.")
        return "\n".join(L)
    A("=" * 100)
    A("FICHAS — ordenadas pela QUEDA IDIOSSINCRATICA (a parcela propria da empresa)")
    A("=" * 100)
    for i, F in enumerate(fichas, 1):
        d = F.get("decomposicao") or {}
        A("")
        A("[%02d] %-6s  %s" % (i, F["ticker"], F.get("nome") or ""))
        A("     setor ............ %s (ETF %s)" % (F.get("setor"), d.get("etf_setor")))
        A("     preco ............ %.2f   (fechamento de %s)" % (F["preco"], F.get("ult_data")))
        A("     queda da semana .. %+.2f%%   |   z = %+.2f  (desvio semanal de 52s = %.2f%%)"
          % (F["var_semana_pct"], F["z_semana"], F["sd_semanal_52_pct"]))
        if d.get("erro"):
            A("     decomposicao ..... INDISPONIVEL: %s" % d["erro"])
        else:
            A("     decomposicao ..... mercado %+.2f pp | setor %+.2f pp | PROPRIA %+.2f pp"
              % (d["mercado_pp"], d["setor_pp"], d["idiossincratico_pp"]))
            A("                        (SPY %+.2f%% x beta %.2f | %s %+.2f%% x beta %.2f | R2 %.2f | parcela propria %.0f%%)"
              % (d["spy_semana_pct"], d["beta_mercado"], d["etf_setor"],
                 d["etf_semana_pct"], d["beta_setor"], d["r2"], 100 * (d.get("parcela_idio") or 0)))
        lz = F.get("lastro")
        if lz:
            A("     LASTRO ........... %s  |  preco %+.2f%%  vs  EPS %s %+.2f%%  |  razao EPS/preco = %s"
              % (F["classe_lastro"].upper(), F["var_semana_pct"], lz["fy"],
                 lz["var_eps_pct"],
                 ("%.3f" % F["razao_eps_preco"]) if F.get("razao_eps_preco") is not None else "n/d"))
            A("                        (%d analistas | %s)"
              % (lz.get("n_analistas") or 0, F.get("obs_lastro") or ""))
            g = F.get("lastro_graduacao") or {}
            A("     GRAU ............. %s%s" % (F.get("lastro_grau") or "?",
              ("   [z do consenso = %+.2f]" % g["lastro_z"]) if g.get("lastro_z") is not None else ""))
            A("                        %s" % (g.get("texto") or ""))
        else:
            A("     LASTRO ........... SEM DADO — %s" % (F.get("motivo_sem_dado") or "?"))
            A("     GRAU ............. %s" % (F.get("lastro_grau") or "sem dado"))
        m = F.get("motivo") or {}
        A("     MOTIVO ........... %s" % m.get("motivo"))
        A("                        data %s | fonte %s | confianca: %s"
          % (m.get("data") or "n/d", m.get("fonte") or "n/d", m.get("confianca")))
        if m.get("link"):
            A("                        %s" % m["link"])
        A("     analista ......... %s" % F.get("papel_analista"))
        A("     media 200 dias ... %s (preco %+.2f%% vs SMA200 = %.2f)"
          % ("ACIMA" if F.get("acima_sma200") else "ABAIXO",
             F.get("dist_sma200_pct"), F.get("sma200")))
    A("")
    A("=" * 100)
    A("TENSAO CONHECIDA, NAO RESOLVIDA (fica registrada toda semana):")
    A("  HCI_Controle_Drawdown: metade da vantagem da carteira veio do filtro de SMA200.")
    A("  Mas quem cai forte perde a media — nesta rodada, %d de %d fichas estao ABAIXO dela."
      % (sum(1 for F in fichas if not F.get("acima_sma200")), len(fichas)))
    A("  'Queda forte' e 'acima da SMA200' sao parcialmente ANTAGONICOS. A escolha exige")
    A("  pre-registro ANTES de olhar resultado, ou vira garimpo (METODO_HCI, Fase 0.2).")
    A("  HCI_Swing_Acoes_ML: reversao a media em acoes sobreviveu em UM regime so —")
    A("  este coletor NAO tem portao de regime. Ele coleta; nao aprova nada.")
    A("=" * 100)
    return "\n".join(L)


# ==========================================================================
# PRINCIPAL
# ==========================================================================
def main():
    ap = argparse.ArgumentParser(description="Ficha de queda semanal (HCI)")
    ap.add_argument("--z", type=float, default=CORTE_Z,
                    help="corte PROVISORIO de z semanal (padrao %.1f)" % CORTE_Z)
    ap.add_argument("--max", type=int, default=30,
                    help="teto de fichas com motivo coletado (custo de rede)")
    args = ap.parse_args()

    t_ini = time.time()
    funil = []
    log("=" * 100)
    log("HCI — FICHA DE QUEDA   (coletor; nao decide, nao recomenda)")
    log("=" * 100)

    # ---------------- 1. UNIVERSO ----------------
    snaps = carrega_snapshots()
    if not snaps:
        log("ERRO: nenhum snapshot de estimativas. Arquivo anterior preservado.")
        sys.exit(1)
    log("snapshots ponto-no-tempo encontrados: %s" % ", ".join(snaps.keys()))
    liq, total, d_ini, d_fim = universo(snaps)
    funil.append(("1. UNIVERSO — tickers no snapshot de %s" % d_fim, total))
    funil.append(("   apos piso de liquidez (px>=%d, vol>%dk, mcap>%.0fbi)"
                  % (PISO_PRECO, PISO_VOLUME / 1000, PISO_MCAP / 1e9), len(liq)))
    funil.append(("   MORRERAM na liquidez", total - len(liq)))
    log("universo: %d tickers -> %d apos liquidez" % (total, len(liq)))

    # ---------------- 2. CAIU (z) ----------------
    log("baixando precos ajustados (%d tickers + 12 ETFs)..." % len(liq))
    etfs = ["SPY"] + sorted(set(SETOR_ETF.values()))
    px = baixa_precos(list(liq.index) + etfs)
    if "SPY" not in px.columns:
        log("ERRO: SPY nao veio. Sem referencia de mercado nao ha decomposicao honesta.")
        sys.exit(1)

    met, sem_hist = {}, 0
    for t in liq.index:
        if t not in px.columns:
            sem_hist += 1
            continue
        m = metricas_preco(px[t])
        if m.get("erro"):
            sem_hist += 1
            continue
        met[t] = m
    funil.append(("2. CAIU — com historico suficiente (>=%d barras)" % MIN_BARRAS, len(met)))
    funil.append(("   MORRERAM por historico curto / sem preco", sem_hist))

    # guarda de desdobramento: bruto (snapshot) x ajustado (Yahoo)
    vetados_split = []
    for t, m in list(met.items()):
        pa = liq.at[t, "preco_snap_ant"]
        if pa and pa == pa and pa > 0:
            bruto = 100 * (liq.at[t, "preco"] / pa - 1)
            if abs(bruto - m["var_semana_pct"]) > LIM_SPLIT_PP:
                vetados_split.append((t, round(bruto, 2), m["var_semana_pct"]))
    funil.append(("   sinalizados desdobramento/dividendo (bruto x ajustado > %.0f pp)"
                  % LIM_SPLIT_PP, len(vetados_split)))

    # seletividade do corte (fato medido, nao desenho)
    zs = sorted(m["z_semana"] for m in met.values())
    for corte in (-1.5, -2.0, -2.5, -3.0):
        funil.append(("   seletividade: z <= %.1f" % corte,
                      "%d (%.1f%%)" % (sum(1 for z in zs if z <= corte),
                                       100 * sum(1 for z in zs if z <= corte) / max(len(zs), 1))))
    cand = [t for t, m in met.items() if m["z_semana"] <= args.z]
    cand.sort(key=lambda t: met[t]["z_semana"])
    funil.append(("   PASSARAM no corte PROVISORIO z <= %.1f" % args.z, len(cand)))
    funil.append(("   MORRERAM no z", len(met) - len(cand)))
    log("caidos com z <= %.1f: %d" % (args.z, len(cand)))

    # semana de referencia
    d1 = px.index[-1]
    semanas = sorted({(d.isocalendar()[0], d.isocalendar()[1]) for d in px.index})
    sem_ant = semanas[-2]
    dias_ant = [d for d in px.index
                if (d.isocalendar()[0], d.isocalendar()[1]) == sem_ant]
    d0 = dias_ant[-1]
    log("semana julgada: %s -> %s" % (d0.date(), d1.date()))

    # ---------------- 3. IDIOSSINCRATICA ----------------
    decs, mortos_idio = {}, 0
    for t in cand:
        d = decompoe(t, liq.at[t, "setor"], px, d0, d1)
        decs[t] = d
    proprios = []
    for t in cand:
        d = decs[t]
        if d.get("erro"):
            mortos_idio += 1
            continue
        if d["idiossincratico_pp"] >= 0 or (d.get("parcela_idio") or 0) < MIN_SHARE_IDIO:
            mortos_idio += 1
            continue
        proprios.append(t)
    proprios.sort(key=lambda t: decs[t]["idiossincratico_pp"])
    funil.append(("3. IDIOSSINCRATICA — queda propria domina (>=%.0f%%) e e negativa"
                  % (100 * MIN_SHARE_IDIO), len(proprios)))
    funil.append(("   MORRERAM (queda era do mercado/setor, ou sem ETF/janela)", mortos_idio))
    log("idiossincraticos: %d" % len(proprios))

    alvo = proprios[:args.max]
    if len(proprios) > args.max:
        funil.append(("   teto de coleta de motivo (--max)", args.max))

    # ---------------- 4 e 5. LASTRO + MOTIVO ----------------
    cikmap = mapa_cik()
    if not cikmap:
        log("aviso: mapa de CIK do EDGAR indisponivel — o motivo cai para analista/manchete")
    ini = d0.strftime("%Y-%m-%d")
    fim = (d1 + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    fichas = []
    for k, t in enumerate(alvo, 1):
        t0 = time.time()
        m, d = met[t], decs[t]
        F = {"ticker": t, "setor": liq.at[t, "setor"], "janela": [ini, fim]}
        F.update({kk: m[kk] for kk in ("preco", "ult_data", "var_semana_pct", "z_semana",
                                       "sd_semanal_52_pct", "sma200", "acima_sma200",
                                       "dist_sma200_pct", "n_barras")})
        F["decomposicao"] = d
        # LASTRO
        rev, erro_rev = revisao_pit(t, snaps, d_ini, d_fim)
        F["lastro"] = rev
        F["motivo_sem_dado"] = erro_rev
        cl, razao, obs = classe_lastro(F["var_semana_pct"], rev)
        F["classe_lastro"] = cl                      # os TRES estados, intocados
        F["razao_eps_preco"] = razao
        F["obs_lastro"] = obs
        # ao LADO dos tres estados (nunca no lugar deles): a graduacao com faixa de
        # incerteza declarada. Perto da borda o caso sai FRONTEIRA, nao veredito.
        F["lastro_graduacao"] = graduacao_do_lastro(
            (rev or {}).get("var_eps_pct"), (rev or {}).get("incerteza_eps_pct"))
        F["lastro_grau"] = F["lastro_graduacao"]["grau"]
        F["lastro_fronteira"] = F["lastro_graduacao"]["fronteira"]
        F["lastro_z"] = F["lastro_graduacao"].get("lastro_z")
        F["incerteza_eps_pct"] = (rev or {}).get("incerteza_eps_pct")
        # MOTIVO
        F["edgar"] = edgar(t, cikmap, ini, fim)
        F["nome"] = F["edgar"].get("nome") or t
        F["analistas"] = analistas(t, ini, fim)
        nome_curto = re.sub(r"[,\.].*$", "", F["nome"]).replace(" Inc", "").replace(" Corp", "").strip()
        F["noticias"] = google_news('"%s" OR "%s" stock' % (nome_curto, t))
        F["rotulos_manchete"] = rotula([n["titulo"] for n in F["noticias"]])
        F["motivo"] = monta_motivo(F)
        F["papel_analista"] = papel_do_analista(F)
        F["segundos"] = round(time.time() - t0, 2)
        fichas.append(F)
        log("  [%02d/%02d] %-6s idio %+7.2f pp | z %+5.2f | lastro %-10s | grau %-32s | %s"
            % (k, len(alvo), t, d["idiossincratico_pp"], m["z_semana"], cl,
               F["lastro_grau"], F["motivo"]["motivo"][:40]))

    n_com = sum(1 for F in fichas if F["classe_lastro"] == "com lastro")
    n_sem = sum(1 for F in fichas if F["classe_lastro"] == "sem lastro")
    n_sd = sum(1 for F in fichas if F["classe_lastro"] == "sem dado")
    n_fyd = sum(1 for F in fichas
                if F.get("lastro") and not F["lastro"].get("fy_e_o_primeiro", True))
    funil.append(("4. LASTRO — com lastro (o EPS caiu junto)", n_com))
    funil.append(("   LASTRO — sem lastro (preco caiu, EPS parado ou subindo)", n_sem))
    funil.append(("   LASTRO — SEM DADO (sem par no snapshot / serie curta)", n_sd))
    funil.append(("   destes, medidos em FY DISTANTE (nao FY1) — dado mais fraco", n_fyd))
    n_front = sum(1 for F in fichas if F.get("lastro_fronteira") is True)
    n_semi = sum(1 for F in fichas if F.get("lastro_fronteira") is None
                 and F.get("classe_lastro") != "sem dado")
    funil.append(("   GRADUACAO — na FAIXA DE FRONTEIRA (o dado nao separa os baldes)", n_front))
    funil.append(("   GRADUACAO — com dado, mas sem incerteza mensuravel no snapshot", n_semi))
    n_ident = sum(1 for F in fichas if F["motivo"]["motivo"] != "motivo nao identificado")
    funil.append(("5. MOTIVO — identificado", n_ident))
    funil.append(("   MOTIVO — nao identificado (isto e informacao, nao falha)",
                  len(fichas) - n_ident))

    try:
        spy_pct = 100 * (px.loc[d1, "SPY"] / px.loc[d0, "SPY"] - 1)
    except Exception:
        spy_pct = None

    meta = {
        "gerado_em": dt.datetime.now().isoformat(timespec="seconds"),
        "semana_ini": str(d0.date()), "semana_fim": str(d1.date()),
        "snap_ini": d_ini, "snap_fim": d_fim,
        "snaps": list(snaps.keys()), "n_snaps": len(snaps),
        "corte_z": args.z, "cortes_provisorios": True,
        "piso_preco": PISO_PRECO, "piso_volume": PISO_VOLUME, "piso_mcap": PISO_MCAP,
        "min_parcela_idio": MIN_SHARE_IDIO, "limiar_lastro_pct": LIM_LASTRO,
        "fronteira_em_incertezas": FRONTEIRA_EM_INCERTEZAS,
        "n_fronteira": n_front, "n_sem_incerteza": n_semi,
        "nota_graduacao": ("o limiar de %.1f%% NAO mudou e os tres estados continuam os "
                           "mesmos. O que entrou ao lado e a faixa de incerteza do proprio "
                           "consenso (epsHigh/epsLow/n do snapshot): quando a revisao esta a "
                           "menos de uma incerteza da borda, o caso sai FRONTEIRA e nao "
                           "veredito. Nenhum numero novo foi calibrado." % LIM_LASTRO),
        "spy_pct": round(spy_pct, 2) if spy_pct is not None else None,
        "n_com": n_com, "n_sem": n_sem, "n_semdado": n_sd, "n_fy_distante": n_fyd,
        "vetados_split": vetados_split,
        "aviso": ("Dado e classificacao, nao recomendacao. Cortes PROVISORIOS, sem "
                  "pre-registro. 'sem lastro' em janela de 1 semana e hipotese: o "
                  "analista revisa depois do evento."),
    }

    # ---------------- GRAVACAO ----------------
    try:
        grava_atomico(OUT_JSON, json.dumps(
            {"meta": meta, "funil": [{"etapa": k, "n": v} for k, v in funil],
             "fichas": fichas}, ensure_ascii=False, indent=1, default=str))
        txt = relatorio(fichas, funil, meta)
        grava_atomico(OUT_TXT, txt)
        novas = append_ledger(fichas, meta["semana_ini"], meta["semana_fim"])
    except Exception as e:
        log("ERRO ao gravar (%s: %s). Arquivo anterior PRESERVADO." % (type(e).__name__, e))
        sys.exit(1)

    log("")
    log(txt)
    log("")
    log("gravado: %s" % OUT_JSON)
    log("gravado: %s" % OUT_TXT)
    log("ledger (append-only): +%d linha(s) em %s" % (novas, LEDGER))
    log("tempo total: %.1f s" % (time.time() - t_ini))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        log("FALHA na coleta (%s). Arquivos anteriores preservados." % type(e).__name__)
        sys.exit(1)
