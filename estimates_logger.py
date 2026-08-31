# -*- coding: utf-8 -*-
"""
HCI — Logger semanal de consenso de estimativas (FMP /stable/)
Objetivo: construir o POINT-IN-TIME proprio do sinal F1 do HCI-SWING FUNDTEC
(revisoes de estimativa de EPS). Cada rodada = 1 snapshot datado do consenso.
Em 8-12 semanas: base para medir a REVISAO (delta entre snapshots) sem look-ahead.
Agendado: sextas 19:30 BRT (schtask HCI_EstimatesLogger). Idempotente por dia.
API key: SO via env FMP_KEY (lei da casa).
"""
import os, sys, json, csv, time, urllib.request
from datetime import date

K = os.environ.get("FMP_KEY")
if not K:
    print("ERRO: FMP_KEY ausente no env")
    sys.exit(1)

# Portado 31-ago-2026 para o repo do site (nada roda na maquina do Eduardo).
# O historico e PIT: dado de estimativa nao se recupera depois, so se acumula —
# por isso cada semana parada e uma semana perdida para sempre.
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "estimates_snapshots")
os.makedirs(OUT_DIR, exist_ok=True)
HOJE = date.today().isoformat()
OUT = os.path.join(OUT_DIR, f"estimates_{HOJE}.csv")
if os.path.exists(OUT):
    print(f"snapshot de {HOJE} ja existe — nada a fazer")
    sys.exit(0)

def get(url, tent=3):
    for i in range(tent):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception:
            if i == tent - 1:
                raise
            time.sleep(2 ** i)

# 1) universo liquido (leis da casa: px>=10, liquidez; sem ETF)
universo = {}
for ex in ("NASDAQ", "NYSE", "AMEX"):
    d = get(f"https://financialmodelingprep.com/stable/company-screener?exchange={ex}"
            f"&priceMoreThan=10&volumeMoreThan=500000&marketCapMoreThan=300000000"
            f"&isEtf=false&isActivelyTrading=true&limit=10000&apikey={K}")
    for x in d or []:
        s = (x.get("symbol") or "").upper()
        if s and s not in universo:
            universo[s] = x
print(f"universo: {len(universo)} tickers", flush=True)

# 2) estimates anuais por ticker (snapshot do consenso de HOJE)
rows, sem_est, erros = [], 0, 0
for n, (sym, meta) in enumerate(sorted(universo.items()), 1):
    try:
        est = get(f"https://financialmodelingprep.com/stable/analyst-estimates?symbol={sym}"
                  f"&period=annual&limit=12&apikey={K}")   # FIX 30/ago: o FMP devolve em ordem DECRESCENTE; limit=4 ficava com os 4 anos MAIS DISTANTES e jogava fora o FY1 de 54,5% do universo
        if not est:
            sem_est += 1
            continue
        for e in est:
            rows.append({
                "snapshot_date": HOJE, "symbol": sym,
                "fy_date": e.get("date"),
                "epsAvg": e.get("epsAvg"), "epsHigh": e.get("epsHigh"), "epsLow": e.get("epsLow"),
                "numAnalystsEps": e.get("numAnalystsEps"),
                "revenueAvg": e.get("revenueAvg"), "numAnalystsRevenue": e.get("numAnalystsRevenue"),
                "sector": meta.get("sector"), "price": meta.get("price"),
                "marketCap": meta.get("marketCap"), "volume": meta.get("volume"),
            })
    except Exception:
        erros += 1
    if n % 250 == 0:
        print(f"  {n}/{len(universo)} ({len(rows)} linhas)", flush=True)
    time.sleep(0.12)  # ~8/s — folga vs rate limit

if not rows:
    print("ERRO: zero linhas — snapshot NAO gravado")
    sys.exit(1)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"OK: {OUT} — {len(rows)} linhas | {len(universo) - sem_est - erros} tickers com estimates | "
      f"{sem_est} sem cobertura | {erros} erros")
