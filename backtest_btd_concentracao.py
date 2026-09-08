# -*- coding: utf-8 -*-
"""backtest_btd_concentracao.py — O TESTE QUE PODE DERRUBAR O RESULTADO (08/set/2026)

O `backtest_btd.py` deu um resultado forte: no prazo de 60 pregoes, a compra na queda de 5%
rende +5,85pp acima do dia qualquer, e 19 dos 31 papeis ficam acima do percentil 95 do
proprio sorteio (o acaso daria 1,6). Antes de acreditar nisso, tem uma objecao obvia e cara:

    AS ENTRADAS NAO SAO INDEPENDENTES. Todo papel cai no MESMO dia — marco de 2020, 2022.
    "19 de 31 papeis" pode ser UM evento contado 31 vezes, e a leitura verdadeira seria
    "comprar o crash funciona", que e uma afirmacao muito mais rara e muito menos util:
    o cartao aparece todo mes, mas o crash acontece uma vez a cada tres anos.

Alem disso o periodo 2016-2026 e um regime so — a maior alta de mega caps da historia
recente. A lapide do EMA-pullback da casa diz exatamente isso: "colhedor de drift-long
modesto, nao alpha".

TRES TESTES, cada um capaz de matar o achado:

  A. ANO A ANO. Se o excesso vier de um ou dois anos, e evento, nao regra.
  B. SEM OS CRASHES. Remove as janelas de estresse conhecidas e repete. Se o excesso some,
     o cartao nao serve para o dia a dia — serve para o crash, e ai a regra tem outro nome.
  C. QUANTOS DIAS DE CALENDARIO DISTINTOS. Mede a concentracao direto: quantos dias unicos
     produzem as entradas, e que fatia do total vem do dia mais movimentado.

Uso: python backtest_btd_concentracao.py [anos]
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import yfinance as yf

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "data" / "backtest_btd_concentracao.json"

US = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "V", "UNH",
      "XOM", "LLY", "COST", "MA", "HD", "ORCL", "NFLX", "AMD", "CRM"]
B3 = ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "BBAS3.SA",
      "B3SA3.SA", "RENT3.SA", "SUZB3.SA", "PRIO3.SA", "RADL3.SA"]

DIP = -0.05          # o gatilho mais forte, que deu o maior excesso
PRAZO = 60           # o prazo onde o excesso apareceu
N_SORTEIOS = 2000
SEMENTE = 20260908

# Janelas de estresse conhecidas, declaradas ANTES de olhar o resultado por ano.
# Nao sao escolhidas pelo que elas fazem com o numero: sao os episodios que qualquer
# operador nomearia sem pensar.
CRASHES = [
    ("covid", "2020-02-15", "2020-05-31"),
    ("aperto de 2022", "2022-01-01", "2022-10-31"),
    ("tarifas/vol de 2025", "2025-03-01", "2025-05-31"),
]


def frente(s, idx, h):
    fim = idx + h
    ok = fim < len(s)
    idx, fim = idx[ok], fim[ok]
    return (s[fim] / s[idx] - 1.0) if len(idx) else np.array([])


def nuvem_pareada(s, n, h, rng):
    base = np.arange(len(s) - h)
    if len(base) < n or n == 0:
        return np.array([])
    fut = s[base + h] / s[base] - 1.0
    return np.array([fut[rng.choice(len(base), n, replace=False)].mean()
                     for _ in range(N_SORTEIOS)])


def main():
    anos = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    px = yf.download(US + B3, period=f"{anos}y", interval="1d",
                     auto_adjust=True, progress=False)["Close"].dropna(how="all")
    rng = np.random.default_rng(SEMENTE)
    print(f"BTD — concentracao no tempo · gatilho {DIP:.0%} · saida em {PRAZO} pregoes")
    print(f"{px.shape[1]} papeis · {str(px.index[0])[:10]} -> {str(px.index[-1])[:10]}")
    print("=" * 96)

    # -------------------------------------------------- coleta bruta de todas as entradas
    entradas = []          # (ticker, data, retorno)
    for tk in US + B3:
        if tk not in px.columns:
            continue
        se = px[tk].dropna()
        if len(se) < 400:
            continue
        s = se.to_numpy(dtype=float)
        r = np.concatenate([[np.nan], s[1:] / s[:-1] - 1.0])
        idx = np.where(r <= DIP)[0]
        fim = idx + PRAZO
        ok = fim < len(s)
        for i, f in zip(idx[ok], fim[ok]):
            entradas.append((tk, se.index[i], float(s[f] / s[i] - 1.0)))

    df = pd.DataFrame(entradas, columns=["ticker", "data", "ret"])
    df["ano"] = df.data.dt.year
    print(f"entradas totais: {len(df)}\n")

    # -------------------------------------------------- C. concentracao
    dias = Counter(df.data.dt.date)
    top = dias.most_common(10)
    n_dias = len(dias)
    print("C. CONCENTRACAO NO TEMPO")
    print(f"   {len(df)} entradas em {n_dias} dias de calendario distintos "
          f"({len(df) / n_dias:.1f} papeis por dia, de {px.shape[1]} possiveis)")
    fatia10 = sum(c for _, c in top) / len(df) * 100
    print(f"   os 10 dias mais movimentados concentram {fatia10:.0f}% de todas as entradas")
    print("   os 5 maiores: " + " · ".join(f"{d} ({c} papeis)" for d, c in top[:5]))
    print()

    # -------------------------------------------------- A. ano a ano
    print("A. ANO A ANO — o excesso e regra ou e evento?\n")
    print(f"   {'ano':>6} {'entradas':>9} {'gatilho':>9} {'qualquer':>9} {'excesso':>9}")
    print("   " + "-" * 50)
    por_ano = []
    for ano, g in df.groupby("ano"):
        # o "dia qualquer" do MESMO ano, para nao comparar 2020 com 2017
        incs = []
        for tk in g.ticker.unique():
            se = px[tk].dropna()
            s = se.to_numpy(dtype=float)
            mask = (se.index.year == ano)[: len(s) - PRAZO]
            base = np.arange(len(s) - PRAZO)[mask]
            if len(base):
                incs.append((s[base + PRAZO] / s[base] - 1.0).mean())
        inc = float(np.mean(incs)) if incs else float("nan")
        gm = float(g.ret.mean())
        por_ano.append({"ano": int(ano), "n": int(len(g)),
                        "gatilho_pct": round(gm * 100, 2),
                        "incondicional_pct": round(inc * 100, 2),
                        "excesso_pp": round((gm - inc) * 100, 2)})
        print(f"   {ano:>6} {len(g):>9} {gm * 100:>8.2f}% {inc * 100:>8.2f}% "
              f"{(gm - inc) * 100:>+8.2f}")
    anos_pos = sum(1 for x in por_ano if x["excesso_pp"] > 0)
    print(f"\n   anos com excesso positivo: {anos_pos} de {len(por_ano)}")
    print()

    # -------------------------------------------------- B. sem os crashes
    print("B. SEM AS JANELAS DE ESTRESSE (declaradas antes de olhar o resultado)\n")
    fora = pd.Series(False, index=df.index)
    for nome, ini, fim in CRASHES:
        m = (df.data >= ini) & (df.data <= fim)
        fora |= m
        print(f"   {nome:<22} {ini} a {fim} — remove {int(m.sum())} entradas")
    calmo = df[~fora]
    print(f"\n   sobram {len(calmo)} de {len(df)} entradas ({len(calmo) / len(df) * 100:.0f}%)\n")

    print(f"   {'conjunto':<24} {'papeis':>7} {'entradas':>9} {'gatilho':>9} "
          f"{'qualquer':>9} {'excesso':>9} {'p50 sorteio':>12} {'>p95':>8}")
    print("   " + "-" * 92)
    resumo = []
    for rot, sub in (("tudo", df), ("SEM os crashes", calmo)):
        linhas = []
        for tk, g in sub.groupby("ticker"):
            if len(g) < 10:
                continue
            se = px[tk].dropna()
            s = se.to_numpy(dtype=float)
            base = np.arange(len(s) - PRAZO)
            inc = float((s[base + PRAZO] / s[base] - 1.0).mean())
            nv = nuvem_pareada(s, len(g), PRAZO, rng)
            pct = float((nv < g.ret.mean()).mean() * 100) if len(nv) else float("nan")
            linhas.append({"ticker": tk, "n": int(len(g)),
                           "gatilho": float(g.ret.mean()), "inc": inc, "pct": pct})
        if not linhas:
            continue
        L = pd.DataFrame(linhas)
        acima = int((L.pct >= 95).sum())
        r = {"conjunto": rot, "papeis": int(len(L)), "entradas": int(L.n.sum()),
             "gatilho_pct": round(float(L.gatilho.mean()) * 100, 2),
             "incondicional_pct": round(float(L.inc.mean()) * 100, 2),
             "excesso_pp": round(float((L.gatilho - L.inc).mean()) * 100, 2),
             "percentil_mediano": round(float(L.pct.median()), 1),
             "papeis_acima_p95": acima,
             "esperado_por_acaso": round(len(L) * 0.05, 1)}
        resumo.append(r)
        print(f"   {rot:<24} {r['papeis']:>7} {r['entradas']:>9} {r['gatilho_pct']:>8.2f}% "
              f"{r['incondicional_pct']:>8.2f}% {r['excesso_pp']:>+8.2f} "
              f"{r['percentil_mediano']:>11.1f} {acima:>3} de {len(L):<3}")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": str(pd.Timestamp.now("UTC"))[:19] + "Z",
                   "natureza": "EXPLORACAO — nao e pre-registro",
                   "gatilho": DIP, "prazo_pregoes": PRAZO, "anos": anos,
                   "semente": SEMENTE, "n_sorteios": N_SORTEIOS,
                   "concentracao": {"entradas": len(df), "dias_distintos": n_dias,
                                    "fatia_top10_dias_pct": round(fatia10, 1),
                                    "maiores_dias": [[str(d), c] for d, c in top]},
                   "por_ano": por_ano, "crashes_removidos": CRASHES,
                   "resumo": resumo}, f, ensure_ascii=False, indent=1)
    print(f"\ngravado: {SAIDA}")


if __name__ == "__main__":
    main()
