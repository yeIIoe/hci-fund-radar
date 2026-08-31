# -*- coding: utf-8 -*-
"""btd_hold_scan.py — SCANNER DIÁRIO BTD+HOLD (Eduardo assina). Roda depois do fechamento.
Peneira: UNIVERSO líquido -> QUALIDADE (ROE/dívida/FCF) -> DIREÇÃO (crescimento) -> VALUATION guard ->
GATILHO (dip >=3% hoje) -> relatório com a tese p/ Eduardo ASSINAR (checar se a queda quebra a tese ou não).
Uso: python btd_hold_scan.py            (scan de hoje)
     python btd_hold_scan.py 2026-06-30 (scan de uma data específica)"""
# Portado para o repo do radar em 31-ago-2026 (Eduardo: nada roda na maquina dele,
# nada vai pro Discord). Os caminhos eram fixos em C:/Trading.
from __future__ import annotations
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

OUTDIR = Path(__file__).resolve().parent / "data"
OUTDIR.mkdir(parents=True, exist_ok=True)
US = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "V", "UNH", "XOM",
      "LLY", "COST", "MA", "HD", "ORCL", "NFLX", "AMD", "CRM"]
B3 = ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "BBAS3.SA",
      "B3SA3.SA", "RENT3.SA", "SUZB3.SA", "PRIO3.SA", "RADL3.SA"]
ETF = ["SPY", "QQQ", "BOVA11.SA"]
DIP1, DIP2 = -0.03, -0.05        # gatilhos (dip normal / dip fundo = mais prêmio)

# thresholds da peneira de QUALIDADE (fontes: pesquisa HOLD 01-jul — Berkshire/MSCI-Q/Mauboussin)
ROE_MIN = 0.15                    # ROE >= 15% (earning power consistente, Berkshire)
DE_MAX = 150.0                    # divida/equity <= 150% (yfinance em %)
PE_MAX = 45.0                     # guarda de valuation (nao pagar qualquer preco)


def main():
    _recs = []          # saida estruturada para o site
    ref = sys.argv[1] if len(sys.argv) > 1 else None
    ticks = US + B3 + ETF
    px = yf.download(ticks, period="1y", interval="1d", auto_adjust=True, progress=False)["Close"]
    if ref:
        px = px[px.index <= ref]
    day = px.index[-1]
    rets = px.pct_change()
    r1 = rets.iloc[-1]
    dips = r1[r1 <= DIP1].sort_values()
    breadth = (r1[US + B3] <= -0.02).mean()            # % do universo caindo >=2% = dia de MEDO sistêmico
    lines = [f"# BTD+HOLD SCAN — {day.date()}", f"(breadth: {breadth*100:.0f}% do universo caiu >=2%"
             + (" -> DIA DE MEDO SISTEMICO, os melhores dips historicos)" if breadth >= 0.5 else ")"), ""]
    if dips.empty:
        lines.append("Sem dips >= 3% no universo hoje. (Normal — paciência é parte do método.)")
    for t, ret in dips.items():
        is_etf = t in ETF
        tese, aprova = [], True
        if not is_etf:
            try:
                info = yf.Ticker(t).info
            except Exception:
                info = {}
            roe = info.get("returnOnEquity")
            de = info.get("debtToEquity")
            fcf = info.get("freeCashflow")
            pe = info.get("trailingPE")
            g = info.get("earningsGrowth") or info.get("revenueGrowth")
            # QUALIDADE
            if roe is not None and roe < ROE_MIN:
                aprova = False; tese.append(f"REPROVA qualidade: ROE {roe*100:.0f}% < {ROE_MIN*100:.0f}%")
            elif roe is not None:
                tese.append(f"ROE {roe*100:.0f}% OK")
            if de is not None and de > DE_MAX:
                aprova = False; tese.append(f"REPROVA divida: D/E {de:.0f}% > {DE_MAX:.0f}%")
            if fcf is not None and fcf <= 0:
                aprova = False; tese.append("REPROVA: FCF negativo")
            # DIRECAO
            if g is not None:
                tese.append(f"crescimento {'+' if g >= 0 else ''}{g*100:.0f}%" + (" (contra: negativo)" if g < -0.10 else ""))
                if g < -0.25:
                    aprova = False; tese.append("REPROVA direcao: lucro derretendo >25%")
            # VALUATION guard
            if pe is not None and pe > PE_MAX:
                aprova = False; tese.append(f"REPROVA valuation: P/E {pe:.0f} > {PE_MAX:.0f}")
        else:
            tese.append("ETF de indice: sem peneira de qualidade (diversificado por natureza)")
        # ---- MEDO vs IDIO (mecanizado; validado 02-jul: MEDO = WR maior nos 2 mercados) ----
        idxt = "BOVA11.SA" if t.endswith(".SA") else "SPY"
        mret = r1.get(idxt, 0.0)
        rr_ = rets[t].dropna(); mm_ = rets[idxt].reindex(rr_.index)
        b_ = (rr_.rolling(200, min_periods=60).cov(mm_) / mm_.rolling(200, min_periods=60).var()).iloc[-1]
        beta = float(b_) if np.isfinite(b_) else 1.0
        idio = ret - beta * (mret if np.isfinite(mret) else 0)
        syst = 1 - abs(idio) / max(abs(ret), 1e-9)
        medo = syst >= 0.5 or breadth >= 0.5
        tese.append(f"decomposicao: mercado {mret*100:+.1f}% x beta {beta:.1f} -> idio {idio*100:+.1f}% "
                    + ("= queda de MEDO (junto c/ mercado) ✅" if medo else "= queda IDIOSSINCRATICA ⚠️ (cheque a noticia!)"))
        try:                                            # noticia recente = contexto p/ a assinatura
            news = yf.Ticker(t).news[:2]
            for n_ in news:
                tt_ = (n_.get("content", n_) or {}).get("title") or n_.get("title", "")
                if tt_:
                    tese.append(f"news: {tt_[:90]}")
        except Exception:
            pass
        prof = "FUNDO (>=5%)" if ret <= DIP2 else "normal (>=3%)"
        if not aprova:
            nota = "D (reprovado)"
        elif medo and ret <= DIP2:
            nota = "A+ (dip fundo de MEDO + qualidade)"
        elif medo:
            nota = "A (medo + qualidade)"
        elif ret <= DIP2:
            nota = "B (fundo mas IDIO — assinar exige a noticia)"
        else:
            nota = "C (idio raso — so com noticia inocente)"
        s = px[t].dropna()
        vs_alta = (s.iloc[-1] / s.max() - 1) * 100
        _recs.append({
            "ticker": t, "aprovado": bool(aprova), "nota": nota,
            "retorno_hoje": round(float(ret) * 100, 1),
            "vs_maxima_12m": round(float(vs_alta), 0),
            "profundidade": prof,
            "tipo_queda": "medo de mercado" if medo else "idiossincratica",
            "porque": " · ".join(tese) if aprova else None,
            "porque_nao": None if aprova else "nao passou no filtro de qualidade",
        })
        lines.append(f"## {'✅' if aprova else '❌'} {t}  {ret*100:+.1f}% hoje  | dip {prof} | nota {nota}")
        lines.append(f"   preco vs maxima 12m: {vs_alta:+.0f}% | " + " · ".join(tese))
        if aprova:
            conf = ("~75% (backtest 11a: dip fundo de MEDO em qualidade = +14-26% excesso/6m, WR 73-79%)" if nota.startswith("A+")
                    else "~70% (medo+qualidade = o perfil mais seguro do backtest)" if nota.startswith("A")
                    else "~65% (dip fundo mas IDIO — sua leitura da noticia decide)" if nota.startswith("B")
                    else "~55-60% (idio raso — so com noticia inocente)")
            _recs[-1]["confianca"] = conf
            _recs[-1]["risco"] = "cauda p5 = -20/-30% no caminho (por isso qualidade e sem alavancagem)"
            _recs[-1]["plano"] = "compra lump-sum no close, hold 3-6+ meses, venda so por TESE (qualidade caindo), nao por preco"
            _recs[-1]["voce_assina"] = "a queda de hoje quebra a tese (fraude/guidance/negocio) ou e ruido/medo de mercado?"
            lines.append(f"   CONFIANCA: {conf}. RISCO: cauda p5 = -20/-30% no caminho (por isso qualidade + sem alavancagem).")
            lines.append("   PLANO: compra lump-sum no close · hold 3-6+ meses · venda só por TESE (qualidade caindo), não preço.")
            lines.append("   ✍️ VOCÊ ASSINA: a queda de hoje quebra a tese (fraude/guidance/negócio) ou é ruído/medo de mercado?")
        lines.append("")
    rep = "\n".join(lines)
    print(rep)
    out = OUTDIR / f"btd_scan_{day.date()}.txt"
    out.write_text(rep, encoding="utf-8")
    print(f"[relatorio salvo: {out}]")
    import json as _json
    (OUTDIR / "btd_scan.json").write_text(
        _json.dumps({"metodo": "dip em nome de qualidade; separa queda de MEDO (mercado junto) de IDIOSSINCRATICA",
                     "limite": "candidato para VOCE assinar. Nao e ordem.",
                     "dia": str(day.date()), "nomes": _recs}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print(f"[json: {OUTDIR / 'btd_scan.json'}]")


if __name__ == "__main__":
    main()
