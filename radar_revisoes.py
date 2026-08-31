# -*- coding: utf-8 -*-
"""RADAR — motor FUNDAMENTAL v0: o que os snapshots do logger ja entregam.

O logger (schtask HCI_EstimatesLogger, sextas 19:30) acumula desde 14/ago:
  snapshot_date, symbol, fy_date, epsAvg/High/Low, numAnalystsEps,
  revenueAvg, numAnalystsRevenue, sector, price, marketCap, volume

Com 2+ snapshots da para calcular REVISAO DE ESTIMATIVAS — o unico sinal fundamental
que sobreviveu aos testes da casa para swing de acoes (ver HCI_Swing_Acoes_ML).

E PIT de verdade: cada snapshot foi tirado NAQUELE dia, sem revisao retroativa e sem
survivorship. Isso e raro e e o que torna o dado utilizavel.
"""
from __future__ import annotations
import glob, io, os, sys
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# Portado 31-ago-2026 para o repo do site. O caminho era fixo em C:/Trading.
import os as _os
AQUI = _os.path.dirname(_os.path.abspath(__file__))
DIR = _os.path.join(AQUI, "data", "estimates_snapshots")
SAIDA = _os.path.join(AQUI, "data", "revisoes.json")


def carrega():
    fs = sorted(glob.glob(os.path.join(DIR, "estimates_*.csv")))
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    d["snapshot_date"] = pd.to_datetime(d.snapshot_date)
    d["fy_date"] = pd.to_datetime(d.fy_date)
    return d


d = carrega()
snaps = sorted(d.snapshot_date.unique())
print("=" * 100)
print("MOTOR FUNDAMENTAL v0 — revisao de estimativas")
print("=" * 100)
print("  snapshots: %s" % ", ".join(pd.Timestamp(s).strftime("%d/%m") for s in snaps))
print("  tickers no ultimo: %d | setores: %d" % (d[d.snapshot_date == snaps[-1]].symbol.nunique(),
                                                 d.sector.nunique()))

# ---- o FY corrente de cada ticker = o fy_date mais PROXIMO no futuro do snapshot
d["dias"] = (d.fy_date - d.snapshot_date).dt.days
fy1 = d[d.dias > 0].sort_values("dias").groupby(["snapshot_date", "symbol"], as_index=False).first()

piv_eps = fy1.pivot_table(index="symbol", columns="snapshot_date", values="epsAvg")
piv_rev = fy1.pivot_table(index="symbol", columns="snapshot_date", values="revenueAvg")
piv_n = fy1.pivot_table(index="symbol", columns="snapshot_date", values="numAnalystsEps")
meta = fy1[fy1.snapshot_date == snaps[-1]].set_index("symbol")[["sector", "price", "marketCap", "volume"]]

a, b = snaps[0], snaps[-1]
cols = [c for c in (a, b) if c in piv_eps.columns]
if len(cols) < 2:
    print("  snapshots insuficientes"); sys.exit()

r = pd.DataFrame(index=piv_eps.index)
r["eps_ini"] = piv_eps[a]
r["eps_fim"] = piv_eps[b]
r["rev_eps_pct"] = 100 * (piv_eps[b] - piv_eps[a]) / piv_eps[a].abs()
r["rev_receita_pct"] = 100 * (piv_rev[b] - piv_rev[a]) / piv_rev[a].abs()
r["n_analistas"] = piv_n[b]
r = r.join(meta)
r = r[(r.eps_ini.abs() > 0.10) & r.rev_eps_pct.notna()]        # EPS proximo de zero explode a %

print("  tickers com revisao calculavel: %d  (de %s a %s)"
      % (len(r), pd.Timestamp(a).strftime("%d/%m"), pd.Timestamp(b).strftime("%d/%m")))
print()

print("=" * 100)
print("A REVISAO SE MEXE? (se quase tudo for zero, 2 semanas e pouco tempo)")
print("=" * 100)
q = r.rev_eps_pct
print("  revisao de EPS:      mediana %+.2f%% | p10 %+.2f%% | p90 %+.2f%%" % (q.median(), q.quantile(.1), q.quantile(.9)))
print("  |revisao| > 0,5%%:    %d de %d = %.0f%%" % ((q.abs() > 0.5).sum(), len(q), 100 * (q.abs() > 0.5).mean()))
print("  |revisao| > 2,0%%:    %d de %d = %.0f%%" % ((q.abs() > 2.0).sum(), len(q), 100 * (q.abs() > 2.0).mean()))
print("  subiram / cairam:    %d / %d" % ((q > 0).sum(), (q < 0).sum()))

print()
print("=" * 100)
print("POR SETOR — quem esta sendo revisado para cima")
print("=" * 100)
g = r.groupby("sector").agg(n=("rev_eps_pct", "size"), rev_mediana=("rev_eps_pct", "median"),
                            pct_subindo=("rev_eps_pct", lambda s: 100 * (s > 0).mean()))
g = g[g.n >= 15].sort_values("rev_mediana", ascending=False)
print("%-26s %6s %14s %14s" % ("setor", "n", "rev. mediana", "% subindo"))
print("-" * 66)
for s, x in g.iterrows():
    print("%-26s %6d %13.2f%% %13.0f%%" % (s, x.n, x.rev_mediana, x.pct_subindo))

print()
print("=" * 100)
print("TOP 20 — maior revisao de EPS para CIMA (liquidez minima: vol>500k, mcap>2B)")
print("=" * 100)
liq = r[(r.volume > 500000) & (r.marketCap > 2e9) & (r.n_analistas >= 3)]
top = liq.sort_values("rev_eps_pct", ascending=False).head(20)
print("%-8s %-24s %10s %10s %8s %10s" % ("ticker", "setor", "rev EPS", "rev rec.", "analist", "preco"))
print("-" * 76)
for t, x in top.iterrows():
    print("%-8s %-24s %+9.2f%% %+9.2f%% %8.0f %10.2f"
          % (t, str(x.sector)[:24], x.rev_eps_pct, x.rev_receita_pct, x.n_analistas, x.price))

print()
print("=" * 100)
print("TOP 10 — maior revisao para BAIXO (o outro lado, igualmente informativo)")
print("=" * 100)
bot = liq.sort_values("rev_eps_pct").head(10)
print("%-8s %-24s %10s %10s %8s %10s" % ("ticker", "setor", "rev EPS", "rev rec.", "analist", "preco"))
print("-" * 76)
for t, x in bot.iterrows():
    print("%-8s %-24s %+9.2f%% %+9.2f%% %8.0f %10.2f"
          % (t, str(x.sector)[:24], x.rev_eps_pct, x.rev_receita_pct, x.n_analistas, x.price))

print()
print("  universo com liquidez: %d de %d tickers" % (len(liq), len(r)))
r.to_csv(r"C:\Trading\hci-ea\out\radar_fund_revisoes.csv")
print("  gravado: out\\radar_fund_revisoes.csv")


# ---------------------------------------------------------------- saida para o site
import json as _json
from datetime import datetime as _dt

_liq = r[(r.volume.fillna(0) > 500_000) & (r.marketCap.fillna(0) > 2e9)].copy()
_liq = _liq.sort_values("rev_eps_pct", ascending=False)

def _reg(x, tk):
    return {
        "ticker": tk,
        "setor": (x.sector if isinstance(x.sector, str) else None),
        "preco": round(float(x.price), 2) if pd.notna(x.price) else None,
        "rev_eps_pct": round(float(x.rev_eps_pct), 2),
        "rev_receita_pct": round(float(x.rev_receita_pct), 2) if pd.notna(x.rev_receita_pct) else None,
        "eps_ini": round(float(x.eps_ini), 3), "eps_fim": round(float(x.eps_fim), 3),
        "n_analistas": int(x.n_analistas) if pd.notna(x.n_analistas) else None,
    }

_cima = [_reg(x, tk) for tk, x in _liq.head(20).iterrows()]
_baixo = [_reg(x, tk) for tk, x in _liq.tail(20).iloc[::-1].iterrows()]
_setores = [{"setor": s_, "n": int(x.n), "rev_mediana": round(float(x.rev_mediana), 2),
             "pct_subindo": round(float(x.pct_subindo), 0)} for s_, x in g.iterrows()]

_doc = {
    "gerado_em": _dt.now().strftime("%Y-%m-%d %H:%M"),
    "snapshots": [pd.Timestamp(x).strftime("%Y-%m-%d") for x in snaps],
    "janela": "%s a %s" % (pd.Timestamp(a).strftime("%Y-%m-%d"), pd.Timestamp(b).strftime("%Y-%m-%d")),
    "n_tickers": int(len(r)),
    "metodo": "Revision of consensus EPS for the current fiscal year, between two PIT snapshots. "
              "Point-in-time by construction: each snapshot was taken that day, with no retroactive "
              "revision and no survivorship. Liquidity floor: volume > 500k, market cap > 2B.",
    "limite": "Screening for human reading. Not an order, not an entry trigger. "
              "Estimate revision is the fundamental signal that survived this house's equity tests — "
              "surviving a screen is not the same as being validated as a strategy.",
    "estatistica": {"mediana": round(float(q.median()), 2), "p10": round(float(q.quantile(.1)), 2),
                    "p90": round(float(q.quantile(.9)), 2),
                    "acima_0_5pct": int((q.abs() > 0.5).sum()),
                    "subiram": int((q > 0).sum()), "cairam": int((q < 0).sum())},
    "setores": _setores, "cima": _cima, "baixo": _baixo,
}
io.open(SAIDA, "w", encoding="utf-8").write(_json.dumps(_doc, indent=1, ensure_ascii=False))
print()
print("  site: %s (%d subindo, %d caindo, %d setores)" % (SAIDA, len(_cima), len(_baixo), len(_setores)))
