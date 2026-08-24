# -*- coding: utf-8 -*-
"""Projeta o FUND de AMANHA para os 28 pares, nas duas direcoes.

Por que isto e exato e nao um modelo
------------------------------------
O FUND do site e, para o indice i do calendario-uniao das duas pernas:

    spread[i] = base[i] - quote[i]              (ffill limite 5)
    raw[i]    = spread[i] - spread[i-20]
    hist      = raw[i-252 : i]                  <- NAO inclui i
    fund[i]   = 100 * tanh( ((raw[i] - media(hist)) / desvio(hist)) / 2 )

Como `hist` termina em i-1, a media e o desvio que vao normalizar o FUND de
amanha **ja estao determinados hoje**. E `spread[i-20]` de amanha e o spread de
19 pregoes atras, tambem conhecido. Sobra UMA incognita: quanto o spread de
juros 2 anos se move amanha.

Entao da para inverter a formula e responder, sem estimar nada:

  * se o spread nao se mexer, qual sera o FUND amanha  (a parte DETERMINISTICA,
    que existe porque a janela de 20 dias rola e a observacao de 20 dias atras
    sai da conta);
  * quantos pontos-base o spread precisa andar para o FUND cruzar cada borda
    de faixa, para cima e para baixo.

So a probabilidade e estatistica, e vem da distribuicao empirica dos movimentos
diarios do proprio spread, em janela movel causal.

Saida: data/projection.json
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from update_fund import (FFILL_LIMIT, LOOKBACK, MIN_HISTORY, NORM_WINDOW, PAIR_ORDER,
                         classify, ffill, read_all_yields)

DEST = ROOT / "data" / "projection.json"

# bordas das faixas, na ordem em que o FUND as encontra subindo
BORDAS = (-60.0, -25.0, 25.0, 60.0)
# ao CRUZAR uma borda, em que faixa se cai — depende do sentido do cruzamento.
# Subir por -60 leva a BEAR, nao a STRONG_BEAR; descer por -60 e que leva a STRONG_BEAR.
FAIXA_ACIMA = {-60.0: "BEAR", -25.0: "NEUTRAL", 25.0: "BULL", 60.0: "STRONG_BULL"}
FAIXA_ABAIXO = {-60.0: "STRONG_BEAR", -25.0: "BEAR", 25.0: "NEUTRAL", 60.0: "BULL"}

JANELA_MOVIMENTO = 252   # amostra para a distribuicao dos movimentos diarios do spread
MIN_MOVIMENTOS = 60


def serie_do_par(par: str, series: dict) -> tuple[list[date], list[float | None], list[float | None]]:
    """Reproduz exatamente o calendario-uniao e o spread/raw de compute_pair()."""
    base, quote = par[:3], par[3:]
    b, q = series[base], series[quote]
    calendario = sorted(set(b) | set(q))
    bv = ffill(b, calendario, FFILL_LIMIT)
    qv = ffill(q, calendario, FFILL_LIMIT)
    spread: list[float | None] = []
    raw: list[float | None] = []
    for i, (x, y) in enumerate(zip(bv, qv)):
        s = None if x is None or y is None else x - y
        spread.append(s)
        antigo = spread[i - LOOKBACK] if i >= LOOKBACK else None
        raw.append(None if s is None or antigo is None else s - antigo)
    return calendario, spread, raw


def fund_de(raw_valor: float, mu: float, sigma: float) -> float:
    z = (raw_valor - mu) / sigma
    return max(-100.0, min(100.0, 100.0 * math.tanh(z / 2.0)))


def raw_para_fund(alvo: float, mu: float, sigma: float) -> float:
    """Inverte fund = 100*tanh(z/2) -> qual raw produz exatamente `alvo`."""
    t = max(-0.999999, min(0.999999, alvo / 100.0))
    z = 2.0 * math.atanh(t)
    return mu + sigma * z


def projeta(par: str, series: dict) -> dict | None:
    calendario, spread, raw = serie_do_par(par, series)

    # ultimo indice com FUND valido (mesma regra do compute_pair)
    def hist_em(i: int) -> list[float]:
        return [v for v in raw[max(0, i - NORM_WINDOW):i] if v is not None]

    validos = [i for i in range(len(raw))
               if raw[i] is not None and len(hist_em(i)) >= MIN_HISTORY
               and statistics.stdev(hist_em(i)) > 0]
    if not validos:
        return None
    hoje = validos[-1]

    h_hoje = hist_em(hoje)
    fund_hoje = fund_de(raw[hoje], statistics.mean(h_hoje), statistics.stdev(h_hoje))

    # ---- amanha: indice hoje+1 do mesmo calendario -------------------------
    # mu/sigma de amanha usam raw[hoje+1-252 : hoje+1], que termina em `hoje`.
    h_amanha = [v for v in raw[max(0, hoje + 1 - NORM_WINDOW):hoje + 1] if v is not None]
    if len(h_amanha) < MIN_HISTORY:
        return None
    mu, sigma = statistics.mean(h_amanha), statistics.stdev(h_amanha)
    if sigma <= 0:
        return None

    # spread que sai da janela de 20 dias quando amanha entra
    idx_saindo = hoje + 1 - LOOKBACK
    if idx_saindo < 0 or spread[idx_saindo] is None or spread[hoje] is None:
        return None
    spread_saindo = spread[idx_saindo]
    spread_hoje = spread[hoje]

    # PARTE DETERMINISTICA: spread parado amanha (delta = 0)
    raw_parado = spread_hoje - spread_saindo
    fund_parado = fund_de(raw_parado, mu, sigma)

    # distribuicao causal dos movimentos diarios do spread
    movimentos = []
    for i in range(max(1, hoje - JANELA_MOVIMENTO + 1), hoje + 1):
        a, b = spread[i - 1], spread[i]
        if a is not None and b is not None:
            movimentos.append(b - a)
    if len(movimentos) < MIN_MOVIMENTOS:
        return None
    movimentos_ord = sorted(movimentos)
    n = len(movimentos_ord)

    def p_abaixo(x: float) -> float:
        return sum(1 for m in movimentos_ord if m <= x) / n

    def delta_para(alvo: float) -> float:
        """Movimento do spread amanha que poe o FUND exatamente em `alvo`."""
        return raw_para_fund(alvo, mu, sigma) + spread_saindo - spread_hoje

    faixa_hoje = classify(fund_hoje)
    cenarios = []
    for borda in BORDAS:
        d = delta_para(borda)
        subindo = borda > fund_parado
        # probabilidade de CRUZAR: subir acima da borda, ou cair abaixo dela
        prob = (1.0 - p_abaixo(d)) if subindo else p_abaixo(d)
        cenarios.append({
            "boundary": borda,
            "band_if_crossed": FAIXA_ACIMA[borda] if subindo else FAIXA_ABAIXO[borda],
            "direction": "UP" if subindo else "DOWN",
            "spread_move_bp": round(d * 100.0, 1),      # pontos percentuais -> bp
            "probability": round(100.0 * prob, 2),
        })

    # as duas possibilidades vizinhas: a borda mais proxima para baixo e para cima
    abaixo = [c for c in cenarios if c["direction"] == "DOWN"]
    acima = [c for c in cenarios if c["direction"] == "UP"]
    vizinha_baixo = max(abaixo, key=lambda c: c["boundary"]) if abaixo else None
    vizinha_cima = min(acima, key=lambda c: c["boundary"]) if acima else None

    p_baixo = vizinha_baixo["probability"] if vizinha_baixo else 0.0
    p_cima = vizinha_cima["probability"] if vizinha_cima else 0.0

    # intervalo do FUND de amanha a partir dos percentis dos movimentos
    def pct(p: float) -> float:
        k = min(n - 1, max(0, int(round(p * (n - 1)))))
        return movimentos_ord[k]

    faixa_fund = {
        rotulo: round(fund_de(spread_hoje + pct(p) - spread_saindo, mu, sigma), 1)
        for rotulo, p in (("p10", 0.10), ("p50", 0.50), ("p90", 0.90))
    }

    return {
        "pair": par,
        "as_of": calendario[hoje].isoformat(),
        "fund_today": round(fund_hoje, 2),
        "band_today": faixa_hoje,
        "fund_if_spread_unchanged": round(fund_parado, 2),
        "roll_drift": round(fund_parado - fund_hoje, 2),
        "spread_today_pct": round(spread_hoje, 4),
        "spread_daily_std_bp": round(statistics.stdev(movimentos) * 100.0, 2),
        "move_sample": n,
        "fund_range_tomorrow": faixa_fund,
        "down": vizinha_baixo,
        "up": vizinha_cima,
        "p_down": p_baixo,
        "p_up": p_cima,
        "p_stay": round(max(0.0, 100.0 - p_baixo - p_cima), 2),
        "scenarios": cenarios,
    }


def main() -> None:
    series = read_all_yields()
    saida, faltando = [], []
    for par in PAIR_ORDER:
        try:
            item = projeta(par, series)
        except Exception as erro:
            item, motivo = None, str(erro)
        else:
            motivo = "historico insuficiente"
        if item is None:
            faltando.append(f"{par} ({motivo})")
        else:
            saida.append(item)
    saida.sort(key=lambda x: -max(x["p_down"], x["p_up"]))

    payload = {
        "meta": {
            "generated_on": date.today().isoformat(),
            "method": ("Exact inversion of the FUND formula. mu and sigma for tomorrow use "
                       "raw[t-251..t], which is already fixed today; spread[t-19] is also known. "
                       "The only unknown is tomorrow's move in the 2-year yield spread, so the "
                       "required move is solved for, not estimated."),
            "probability_source": (f"empirical distribution of the last {JANELA_MOVIMENTO} daily "
                                   "spread changes for that pair (causal, no look-ahead)"),
            "roll_drift_note": ("Even with a completely unchanged spread the FUND moves, because the "
                                "20-day window rolls and the observation from 20 sessions ago drops out. "
                                "That part of tomorrow is already decided."),
            "bands": {"STRONG_BEAR": "<= -60", "BEAR": "-60 to -25", "NEUTRAL": "-25 to +25",
                      "BULL": "+25 to +60", "STRONG_BULL": ">= +60"},
            "pairs": len(saida),
            "missing": faltando,
        },
        "projections": saida,
    }
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"salvo: {DEST} | {len(saida)} pares" + (f" | sem projecao: {faltando}" if faltando else ""))


if __name__ == "__main__":
    main()
