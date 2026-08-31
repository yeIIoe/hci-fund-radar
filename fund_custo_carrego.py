# -*- coding: utf-8 -*-
"""CAMADA DE CUSTO DE CARREGO — para o painel do FUND.

Calibrado em 31-ago-2026 contra a tabela real da FTMO: r=0,9752 (R2=0,951),
inclinacao 0,970, erro mediano 0,086 pip/noite. Ou seja: o swap que a corretora
cobra SAI do diferencial de juro de 2 anos que este radar ja ingere todo dia.

Consequencia pratica: nao e preciso ler a pagina da corretora. O custo de segurar
uma posicao pode ser calculado aqui, atualizado sozinho, e alertar quando o LADO
BARATO de um par virar.

    swap_pip_por_noite = preco x (r_base - r_quote) / 100 / 365 / pip

⚠️ Isto estima o DIFERENCIAL. A corretora ainda cobra uma taxa por cima, medida em
   ~0,49 pip/noite mediana (varia 0,22 a 1,00 por par). Ela entra como MARKUP.

REGRA ACHADA (correlacao -0,683 entre |diferencial| e custo do melhor lado):
   |dif| < 0,8%  -> melhor lado custa 4,29% da faixa de 5 dias (mediana)
   |dif| > 2,5%  -> melhor lado custa 0,10%
   Diferencial perto de zero = sem carry para compensar a taxa = RUIM DOS DOIS LADOS.
"""
from __future__ import annotations
import glob, json, os, sys
from datetime import datetime
import numpy as np, pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
CAL  = os.path.join(AQUI, "data", "calendar")
RAW  = os.path.join(AQUI, "data", "raw")
SPR  = os.path.join(AQUI, "data", "spread_medido.csv")
SAIDA = os.path.join(AQUI, "data", "custo_carrego.json")

MOEDAS = ["USD","EUR","GBP","JPY","AUD","CAD","NZD","CHF"]
MARKUP_PIP = 0.489      # taxa mediana da FTMO por noite, medida
COMISSAO_PIP = 0.5      # US$5/lote round turn
NOITES_5D = 7           # 5 dias uteis = 7 noites (quarta cobra 3x)

def pip_de(par): return 0.01 if par.endswith("JPY") else 0.0001

def par_conv(b, q):
    """Convencao de mercado: quem e base."""
    ordem = ["EUR","GBP","AUD","NZD","USD","CAD","CHF","JPY"]
    return (b+q) if ordem.index(b) < ordem.index(q) else (q+b)

def painel_yields():
    L = []
    for fn in sorted(glob.glob(os.path.join(CAL, "calendar_*.json"))):
        j = json.load(open(fn, encoding="utf-8"))
        for d in j.get("days", []):
            cs = d.get("currencies") or []
            if not cs: continue
            r = {c["currency"]: c.get("yield_2y") for c in cs}
            r["date"] = d["date"]
            L.append(r)
    Y = pd.DataFrame(L)
    Y["date"] = pd.to_datetime(Y.date)
    return Y.set_index("date").sort_index()

def precos_hoje():
    T = {"EUR": 1.0}
    for fn in glob.glob(os.path.join(RAW, "fx_ecb_*.csv")):
        m = os.path.basename(fn)[7:10].upper()
        d = pd.read_csv(fn, usecols=["TIME_PERIOD","OBS_VALUE"]).dropna()
        T[m] = float(d.OBS_VALUE.astype(float).iloc[-1])
    return T

def calcula():
    Y = painel_yields()
    T = precos_hoje()
    SP = pd.read_csv(SPR).set_index("par").spr_p50.to_dict() if os.path.exists(SPR) else {}
    hoje = Y.dropna(how="all").index[-1]
    yh = Y.loc[hoje]

    saida = []
    vistos = set()
    for b in MOEDAS:
        for q in MOEDAS:
            if b == q: continue
            par = par_conv(b, q)
            if par in vistos: continue
            vistos.add(par)
            B, Q = par[:3], par[3:]
            if B not in yh or Q not in yh or pd.isna(yh[B]) or pd.isna(yh[Q]): continue
            if B not in T or Q not in T: continue
            preco = T[Q] / T[B]
            pip = pip_de(par)
            dif = float(yh[B] - yh[Q])
            carry = preco * (dif/100.0) / 365.0 / pip          # pip/noite a favor do comprado
            swap_l = carry - MARKUP_PIP
            swap_s = -carry - MARKUP_PIP

            # historico do diferencial: quantas viradas e quao longe do zero
            serie = (Y[B] - Y[Q]).dropna()
            viradas = int((np.sign(serie).diff().abs() > 1).sum())
            anos = max((serie.index[-1] - serie.index[0]).days / 365.25, 0.1)
            vol60 = float(serie.diff(60).std()) if len(serie) > 80 else np.nan
            sig = abs(dif)/vol60 if vol60 and vol60 > 0 else None

            spread = SP.get(par)
            reg = dict(par=par, dif_juro=round(dif,4), preco=round(preco,5),
                       carry_pip_noite=round(carry,4),
                       swap_long_pip=round(swap_l,4), swap_short_pip=round(swap_s,4),
                       lado_barato="COMPRADO" if swap_l > swap_s else "VENDIDO",
                       viradas_por_ano=round(viradas/anos,2),
                       sigmas_do_zero=round(sig,2) if sig else None,
                       risco_virada=("IMINENTE" if sig and sig < 0.5 else
                                     "PROXIMO" if sig and sig < 1.0 else "estavel"),
                       sem_lado_bom=bool(abs(dif) < 0.8))
            if spread is not None:
                reg["spread_medido_pip"] = round(float(spread),2)
                reg["custo_5d_long_pip"]  = round(float(spread) + COMISSAO_PIP - swap_l*NOITES_5D, 2)
                reg["custo_5d_short_pip"] = round(float(spread) + COMISSAO_PIP - swap_s*NOITES_5D, 2)
            saida.append(reg)

    saida.sort(key=lambda r: (r["sigmas_do_zero"] is None, r["sigmas_do_zero"] or 9e9))
    doc = dict(
        gerado_em=datetime.now().strftime("%Y-%m-%d %H:%M"),
        yields_de=str(hoje.date()),
        calibracao=dict(r=0.9752, r2=0.951, inclinacao=0.970, erro_mediano_pip=0.086,
                        fonte="ftmo.com/symbols 31-ago-2026", n_pares=28),
        markup_pip_noite=MARKUP_PIP, comissao_pip=COMISSAO_PIP, noites_5d=NOITES_5D,
        regra="|dif juro| < 0,8% => sem lado bom (sem carry para compensar a taxa)",
        pares=saida)
    json.dump(doc, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return doc

if __name__ == "__main__":
    d = calcula()
    print("=" * 100)
    print("CUSTO DE CARREGO — gerado dos yields de %s" % d["yields_de"])
    print("=" * 100)
    print("  %-9s %10s %11s %12s %11s  %s" % ("par","dif juro","lado barato","custo 5d","risco",""))
    print("  " + "-" * 66)
    for p in d["pares"][:12]:
        c = p.get("custo_5d_long_pip") if p["lado_barato"]=="COMPRADO" else p.get("custo_5d_short_pip")
        flag = "🔴" if p["risco_virada"]=="IMINENTE" else ("🟡" if p["risco_virada"]=="PROXIMO" else "  ")
        sem = " SEM LADO BOM" if p["sem_lado_bom"] else ""
        print("  %-9s %+8.3f%% %11s %9s pip %10s %s%s"
              % (p["par"], p["dif_juro"], p["lado_barato"],
                 ("%.2f"%c) if c is not None else "-", p["risco_virada"], flag, sem))
    print()
    print("  gravado: data/custo_carrego.json  (%d pares)" % len(d["pares"]))
