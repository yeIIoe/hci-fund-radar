# -*- coding: utf-8 -*-
"""Projecao BIDIRECIONAL do FUND para todo o historico do calendario.

Por que existe
--------------
A watchlist PRE-FUND do calendario so previa BEAR. O modelo foi escrito assim
(`target_transition = 1 if next_fund <= -25`), entao o card mostrava "chance
34,74%" sem dizer de que — porque so havia uma direcao possivel. O Eduardo
perguntou como saber se o FUND vai ficar positivo ou negativo, e a resposta
honesta era: com aquele modelo, nao dava.

Aqui a pergunta e respondida pelos dois lados, e por inversao exata da formula
do FUND em vez de modelo ajustado. Para o indice i+1:

    mu, sigma  ->  janela de raw que termina em i          (ja fixada hoje)
    spread[i-19]                                            (ja conhecido)
    unica incognita: o movimento do spread de 2 anos amanha

Logo da para resolver, para cada borda de faixa, quanto o spread precisa andar,
e converter isso em probabilidade pela distribuicao empirica causal dos ultimos
252 movimentos diarios daquele mesmo spread.

Grava em cada data/calendar/calendar_AAAA.json, por dia:

    "projection": {
        "down": [ {pair, fund, fund_roll, boundary, band, p, bp}, ... ],
        "up":   [ ... ],
        "outcome": {pair: next_fund}          <- conferencia posterior
    }

Somente os 3 melhores de cada lado, para nao inchar o arquivo.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from update_fund import (FFILL_LIMIT, LOOKBACK, MIN_HISTORY, NORM_WINDOW, PAIR_ORDER,
                         read_all_yields)

BORDAS = (-60.0, -25.0, 25.0, 60.0)
FAIXA_ACIMA = {-60.0: "BEAR", -25.0: "NEUTRAL", 25.0: "BULL", 60.0: "STRONG_BULL"}
FAIXA_ABAIXO = {-60.0: "STRONG_BEAR", -25.0: "BEAR", 25.0: "NEUTRAL", 60.0: "BULL"}
JANELA_DELTA = 252
MIN_DELTAS = 60
TOP = 3


def serie(par: str, y: dict) -> pd.DataFrame:
    """Reproduz o calendario-uniao e o spread/raw exatamente como compute_pair()."""
    b, q = y[par[:3]], y[par[3:]]
    cal = sorted(set(b) | set(q))
    sb = pd.Series([b.get(d) for d in cal], index=pd.DatetimeIndex(cal), dtype="float64")
    sq = pd.Series([q.get(d) for d in cal], index=pd.DatetimeIndex(cal), dtype="float64")
    sb = sb.ffill(limit=FFILL_LIMIT)
    sq = sq.ffill(limit=FFILL_LIMIT)
    spread = sb - sq
    raw = spread - spread.shift(LOOKBACK)
    hist = raw.shift(1)
    mu = hist.rolling(NORM_WINDOW, min_periods=MIN_HISTORY).mean()
    sg = hist.rolling(NORM_WINDOW, min_periods=MIN_HISTORY).std(ddof=1)
    fund = (100.0 * np.tanh(((raw - mu) / sg.replace(0.0, np.nan)) / 2.0)).clip(-100, 100)
    # mu/sigma que normalizam o dia SEGUINTE: janela de raw terminando em i
    mu_n = raw.rolling(NORM_WINDOW, min_periods=MIN_HISTORY).mean()
    sg_n = raw.rolling(NORM_WINDOW, min_periods=MIN_HISTORY).std(ddof=1)
    return pd.DataFrame({"spread": spread, "raw": raw, "fund": fund,
                         "mu_n": mu_n, "sg_n": sg_n, "dspread": spread.diff()})


def projeta_par(par: str, y: dict) -> pd.DataFrame:
    d = serie(par, y)
    sp = d.spread.to_numpy(float); fu = d.fund.to_numpy(float)
    mu = d.mu_n.to_numpy(float); sg = d.sg_n.to_numpy(float)
    dsp = d.dspread.to_numpy(float)
    idx = d.index
    saida = []
    for i in range(len(idx)):        # o ultimo dia TEM projecao; so nao tem conferencia
        if not (np.isfinite(fu[i]) and np.isfinite(mu[i]) and np.isfinite(sg[i]) and sg[i] > 0):
            continue
        js = i + 1 - LOOKBACK
        if js < 0 or not np.isfinite(sp[js]) or not np.isfinite(sp[i]):
            continue
        dd = dsp[max(1, i - JANELA_DELTA + 1): i + 1]
        dd = dd[np.isfinite(dd)]
        if len(dd) < MIN_DELTAS:
            continue
        ord_ = np.sort(dd); n = len(ord_)
        roll = 100.0 * math.tanh((((sp[i] - sp[js]) - mu[i]) / sg[i]) / 2.0)
        roll = max(-100.0, min(100.0, roll))
        melhor_d = melhor_u = None
        for b in BORDAS:
            t = max(-0.999999, min(0.999999, b / 100.0))
            delta = (mu[i] + sg[i] * 2.0 * math.atanh(t)) + sp[js] - sp[i]
            p_menor = float(np.searchsorted(ord_, delta, side="right")) / n
            if b > roll:
                if melhor_u is None:      # primeira borda acima = a vizinha
                    melhor_u = (b, FAIXA_ACIMA[b], 100.0 * (1.0 - p_menor), delta * 100.0)
            else:
                melhor_d = (b, FAIXA_ABAIXO[b], 100.0 * p_menor, delta * 100.0)
        prox = (round(float(fu[i + 1]), 2)
                if i + 1 < len(idx) and np.isfinite(fu[i + 1]) else None)
        saida.append((idx[i].date(), par, round(float(fu[i]), 2), round(roll, 2),
                      melhor_d, melhor_u, prox))
    return saida


def main() -> None:
    y = read_all_yields()
    tudo = {}
    for par in PAIR_ORDER:
        try:
            for dia, p, f, roll, dn, up, prox in projeta_par(par, y):
                tudo.setdefault(dia, []).append((p, f, roll, dn, up, prox))
        except Exception as erro:
            print(f"  {par}: falhou ({erro})")
    print(f"dias com projecao: {len(tudo):,}")

    def linha(p, f, roll, cen):
        b, faixa, prob, bp = cen
        return {"pair": p, "fund": f, "fund_roll": roll, "boundary": b, "band": faixa,
                "p": round(prob, 1), "bp": round(bp, 1)}

    escritos = 0
    for arq in sorted((ROOT / "data" / "calendar").glob("calendar_*.json")):
        payload = json.loads(arq.read_text(encoding="utf-8"))
        mudou = False
        for dia in payload["days"]:
            chave = pd.Timestamp(dia["date"]).date()
            itens = tudo.get(chave)
            if not itens:
                continue
            baixo = sorted((x for x in itens if x[3]), key=lambda x: -x[3][2])[:TOP]
            cima = sorted((x for x in itens if x[4]), key=lambda x: -x[4][2])[:TOP]
            # FUND de TODOS os pares naquele dia: sem isto o corte de tempo nao
            # consegue reconstruir a matriz nem a faixa de moedas, e elas ficavam
            # mostrando HOJE por baixo de um corte no passado.
            dia["pair_funds"] = {p: f for p, f, _, _, _, _ in itens}
            dia["projection"] = {
                "down": [linha(p, f, r, dn) for p, f, r, dn, _, _ in baixo],
                "up": [linha(p, f, r, up) for p, f, r, _, up, _ in cima],
                "outcome": {p: prox for p, _, _, _, _, prox in itens if prox is not None},
            }
            mudou = True
        if mudou:
            arq.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            escritos += 1
            print(f"  {arq.name}: gravado")
    print(f"\n{escritos} arquivos de calendario atualizados")


if __name__ == "__main__":
    main()
