# -*- coding: utf-8 -*-
"""deep_value_scan.py — SCANNER DEEP VALUE v0 (scorecard da pesquisa 03-jul; Eduardo assina).
Peneira: EXCLUSOES (cap>=200M, vol>=500k/d, preco>=2, P/B>0) -> BARATO (EV/EBITDA baixo=Acquirer's proxy,
P/B baixo) -> ANTI-TRAP (lucro+, FCF+, D/E<=50% Tweedy-Browne) -> CATALISADOR (net cash) -> nota.
Universo v0 = lista manual (screener FMP depois). Uso: python deep_value_scan.py"""
# Portado para o repo do radar em 31-ago-2026 (Eduardo: nada roda na maquina dele,
# nada vai pro Discord). Os caminhos eram fixos em C:/Trading.
from __future__ import annotations
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import yfinance as yf

UNIV = ["PBF", "DINO", "CVI", "UAN", "AMR", "ARCH", "BTU", "CEIX", "TDW", "GSL", "DAC", "ZIM",
        "GOGL", "SB", "EGY", "REPX", "CRC", "MUR", "SM", "CIVI", "PARR", "DHT", "FRO", "STNG",
        "CSAN3.SA", "CMIN3.SA", "GOAU4.SA", "USIM5.SA", "CSNA3.SA", "SAPR11.SA", "CPLE6.SA",
        "TASA4.SA", "ROMI3.SA", "KEPL3.SA", "FESA4.SA"]
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

RISCO = {"Energy": "preco do petroleo/gas", "Basic Materials": "preco da commodity",
         "Industrials": "ciclo industrial/frete", "Consumer Cyclical": "ciclo de consumo",
         "Financial Services": "credito/juros", "Utilities": "regulacao/juros"}

rows = []
for t in UNIV:
    try:
        i = yf.Ticker(t).info
    except Exception:
        continue
    cap = i.get("marketCap") or 0
    vol = (i.get("averageVolume") or 0) * (i.get("currentPrice") or i.get("regularMarketPrice") or 0)
    px = i.get("currentPrice") or i.get("regularMarketPrice") or 0
    pb = i.get("priceToBook")
    ev = i.get("enterpriseValue"); ebitda = i.get("ebitda")
    de = i.get("debtToEquity"); ni = i.get("netIncomeToCommon"); fcf = i.get("freeCashflow")
    cash = i.get("totalCash") or 0; debt = i.get("totalDebt") or 0
    # exclusoes
    if cap < 2e8 or vol < 5e5 or px < 2 or not pb or pb <= 0:
        continue
    ev_eb = (ev / ebitda) if (ev and ebitda and ebitda > 0) else None
    cheap = (ev_eb is not None and ev_eb <= 5) or pb <= 0.8
    if not cheap:
        continue
    trap = []
    if ni is not None and ni <= 0: trap.append("lucro<=0")
    if fcf is not None and fcf <= 0: trap.append("FCF<=0")
    if de is not None and de > 50: trap.append(f"D/E {de:.0f}%>50")
    netcash = cash > debt
    sc = (2 if (ev_eb and ev_eb <= 4) else 1) + (1 if pb <= 0.8 else 0) + (1 if netcash else 0) - len(trap)
    nota = "A" if (sc >= 3 and not trap) else "B" if (sc >= 2 and not trap) else "C" if not trap else "D"
    # tese + confianca (formato obrigatorio HCI)
    barato = (f"fluxo barato (EV/EBITDA {ev_eb:.1f})" if (ev_eb and ev_eb <= 5) else "") + \
             (" + " if (ev_eb and ev_eb <= 5 and pb <= 0.8) else "") + \
             (f"ativos c/ desconto (P/B {pb:.2f})" if pb <= 0.8 else "")
    forca = ("NET CASH (sobrevive ao inverno)" if netcash else (f"divida controlada (D/E {de:.0f}%)" if de is not None and de <= 30 else "balanco ok"))
    conf = min(70, 55 + (10 if netcash else 0) + (5 if (de is not None and de <= 30) else 0))
    risco = RISCO.get(i.get("sector", ""), "ciclo do setor")
    rows.append((nota, t, px, ev_eb, pb, de, netcash, trap, barato, forca, conf, risco))

rows.sort()
lines = ["# DEEP VALUE SCAN", ""]
for (nota, t, px, ev_eb, pb, de, nc, trap, barato, forca, conf, risco) in rows:
    ok = nota in "AB"
    ev_s = f"{ev_eb:.1f}" if ev_eb else "n/a"
    de_s = f"{de:.0f}%" if de is not None else "n/a"
    lines.append(f"{'✅' if ok else '❌'} {t:10} nota {nota} | {px:.2f} | EV/EBITDA {ev_s} | P/B {pb:.2f} | D/E {de_s}")
    if ok:
        lines.append(f"   TESE: {barato}; {forca}. RISCO: {risco}. CONFIANCA: ~{conf}% individual.")
    else:
        lines.append(f"   REJEITADA: {', '.join(trap) if trap else 'sem margem'} -> barato que pode quebrar/sangrar (a licao da peneira).")
lines.append("")
lines.append("METODO: comprar como CESTA (10-15 nomes equal-weight, hold 1-3 anos) ~70-75% de bater o indice; NAO casar com 1 nome. Voce assina: POR QUE esta barato?")
rep = "\n".join(lines)
print(rep)
(OUT / "deep_value_scan.txt").write_text(rep, encoding="utf-8")
print(f"\n[salvo: {OUT / 'deep_value_scan.txt'}] — A/B = candidatos p/ VOCE checar a tese (por que esta barato?) e assinar. Hold 1-3 anos, 15-25 posicoes.")
