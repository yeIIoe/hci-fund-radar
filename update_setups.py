# -*- coding: utf-8 -*-
"""Gera data/setups.json — o passo 2 do processo do Eduardo, automatizado.

Fluxo que este script reproduz:
  1. le os candidatos do radar PRE-FUND (quem pode virar tradable amanha);
  2. baixa/usa o grafico de 30 minutos do par;
  3. procura o BO ja formado NA DIRECAO que o FUND deve tomar;
  4. marca a ZOI de origem daquele BO e calcula o SL de 1xATR;
  5. informa se o preco ainda precisa voltar na zona ou se ela ja foi consumida.

Assim, quando o par aparecer na lista de "tradable", a zona ja esta mapeada e a
entrada nao se perde. Nenhum dado posterior a ultima barra fechada e usado.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), r"C:\Users\eduar\Downloads\CÓDIGOS", r"C:\Trading\hci-ea",
                r"C:\Trading\hci-ea\python_core\databento_adapter"]

import bo_v9_multiasset_duka as duka
from swing_forex_backtest import atr14, structural_engine
from swing_forex_zoi_v6_rule import select_origin

DEST = ROOT / "data" / "setups.json"
JANELA_DIAS = 25

# faixas de preco plausiveis para a deteccao de escala do Dukascopy
FAIXAS = {
    "EURUSD": (0.8, 1.6), "GBPUSD": (1.0, 2.2), "USDJPY": (70, 170), "USDCHF": (0.6, 1.3),
    "USDCAD": (1.0, 1.8), "AUDUSD": (0.5, 1.1), "NZDUSD": (0.4, 0.9), "EURGBP": (0.6, 1.0),
    "EURJPY": (90, 200), "EURCHF": (0.8, 1.3), "EURAUD": (1.2, 2.0), "EURCAD": (1.2, 1.8),
    "EURNZD": (1.4, 2.2), "GBPJPY": (110, 220), "GBPCHF": (1.0, 1.5), "GBPAUD": (1.5, 2.3),
    "GBPCAD": (1.4, 2.0), "GBPNZD": (1.7, 2.6), "AUDJPY": (55, 120), "AUDCHF": (0.4, 0.9),
    "AUDCAD": (0.7, 1.1), "AUDNZD": (0.9, 1.3), "NZDJPY": (50, 110), "NZDCHF": (0.4, 0.9),
    "NZDCAD": (0.6, 1.0), "CADJPY": (60, 130), "CADCHF": (0.5, 1.0), "CHFJPY": (90, 200),
}
PIP = {p: (0.01 if "JPY" in p else 0.0001) for p in FAIXAS}


def pip_de(par: str) -> float:
    return PIP.get(par, 0.0001)


def carrega_30m(par: str, ate: date, dias: int = JANELA_DIAS) -> pd.DataFrame | None:
    if par not in duka.SYMS:
        duka.SYMS[par] = (FAIXAS.get(par, (0.4, 200.0)), pip_de(par) * 1.5)
    amostra = [ate - timedelta(days=k) for k in range(20, 5, -1) if (ate - timedelta(days=k)).weekday() < 5]
    escala = duka.detecta(par, amostra)
    SC, ORD = escala if escala[0] else (100000.0, "oclh")
    linhas = []
    d = ate - timedelta(days=dias)
    while d <= ate:
        if d.weekday() < 5:
            try:
                for r in duka.parse_day(par, d, SC, ORD):
                    linhas.append((r[0], r[1], r[2], r[3], r[4]))
            except Exception:
                pass
        d += timedelta(days=1)
    if len(linhas) < 500:
        return None
    m1 = pd.DataFrame(linhas, columns=["ts", "o", "h", "l", "c"]).drop_duplicates("ts")
    m1["ts"] = pd.to_datetime(m1.ts, utc=True)
    m1 = m1.set_index("ts").sort_index()
    d30 = (m1.resample("30min")
             .agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
             .dropna().reset_index())
    return d30 if len(d30) >= 60 else None


def analisa(par: str, direcao: int, ate: date) -> dict:
    """direcao: -1 quando esperamos o FUND virar BEAR (short), +1 para long."""
    bars = carrega_30m(par, ate)
    if bars is None:
        return {"pair": par, "status": "SEM_DADO",
                "note": "not enough 30-minute data for this pair"}
    bars["atr14"] = atr14(bars)
    trends, events = structural_engine(bars)
    ultimo = float(bars.c.iloc[-1])
    pip = pip_de(par)
    saida = {
        "pair": par,
        "direction": "SHORT" if direcao == -1 else "LONG",
        "last_price": round(ultimo, 5),
        "last_bar": bars.ts.iloc[-1].isoformat(),
        "tend30": "BULL" if trends[-1] == 1 else "BEAR" if trends[-1] == -1 else "NEUTRAL",
        "bars": len(bars),
    }
    candidatos = sorted(i for i, e in events.items() if e["direction"] == direcao)
    if not candidatos:
        saida["status"] = "SEM_BO"
        saida["note"] = "no breakout in that direction within the window — nothing pre-mapped"
        return saida

    setups = []
    for i in candidatos[-3:][::-1]:
        e = events[i]
        leg = int(e["leg_start"])
        try:
            zoi, regra = select_origin(bars, i, direcao, leg, None)
        except Exception:
            zoi, regra = None, "falhou"
        if zoi is None or not (zoi.bottom < zoi.top):
            continue
        atr_bo = float(bars.atr14.iloc[i])
        if not np.isfinite(atr_bo):
            continue
        # SHORT: zona de oferta ACIMA; o preco precisa SUBIR ate ela.
        # LONG: zona de demanda ABAIXO; o preco precisa CAIR ate ela.
        if direcao == -1:
            sl = zoi.top + atr_bo
            falta = (zoi.bottom - ultimo) / pip      # >0: ainda precisa subir
            dentro = zoi.bottom <= ultimo <= zoi.top
            passou = ultimo > zoi.top
        else:
            sl = zoi.bottom - atr_bo
            falta = (ultimo - zoi.top) / pip         # >0: ainda precisa cair
            dentro = zoi.bottom <= ultimo <= zoi.top
            passou = ultimo < zoi.bottom
        depois = bars.iloc[i + 1:]
        tocada = bool(((depois.l <= zoi.top) & (depois.h >= zoi.bottom)).any())
        risco = abs(ultimo - sl) / pip
        if dentro:
            estado, nota = "NA_ZONA", "price is inside the zone now — wait for the 30m candle to close reacting"
        elif passou:
            estado, nota = "PASSOU", "price went straight through the zone; it is no longer valid"
        elif tocada:
            estado, nota = "CONSUMIDA", "the zone was already retested after the breakout — that entry has passed"
        else:
            estado, nota = "AGUARDANDO", f"the zone is still standing; price needs {abs(falta):.0f} pips to come back into it"
        setups.append({
            "bo_time": bars.ts.iloc[i].isoformat(),
            "bo_age_bars": len(bars) - 1 - i,
            "bo_level": round(float(e["level"]), 5),
            "zoi_bottom": round(float(zoi.bottom), 5),
            "zoi_top": round(float(zoi.top), 5),
            "zoi_width_pips": round((zoi.top - zoi.bottom) / pip, 1),
            "zoi_anchor_time": bars.ts.iloc[zoi.pivot_idx].isoformat(),
            "stop": round(float(sl), 5),
            "risk_pips": round(risco, 1),
            "distance_pips": round(float(falta), 1),
            "touched_after_bo": tocada,
            "state": estado,
            "note": nota,
            "rule": regra,
        })
    if not setups:
        saida["status"] = "SEM_ZOI"
        saida["note"] = "there was a breakout, but no valid origin zone was found"
        return saida
    saida["status"] = "OK"
    saida["setups"] = setups
    return saida


def main() -> None:
    snap = json.loads((ROOT / "data" / "fund_snapshot.json").read_text(encoding="utf-8"))
    pre = snap.get("pre_fund", {})
    observacoes = pre.get("observations", [])
    hoje = date.fromisoformat(pre.get("meta", {}).get("generated_on") or date.today().isoformat())
    print(f"Candidatos PRE-FUND em {hoje}: {len(observacoes)}")
    resultados = []
    for obs in observacoes:
        par = obs["pair"]
        print(f"  analisando {par} (chance {obs['empirical_probability']}%)...")
        item = analisa(par, -1, hoje)          # o radar PRE-FUND antecipa viradas para BEAR
        item["prefund"] = {
            "rank": obs["rank"],
            "fund": obs["fund"],
            "probability": obs["empirical_probability"],
            "samples": obs["empirical_samples"],
            "signal_date": obs["signal_date"],
        }
        resultados.append(item)
        est = item.get("setups", [{}])[0].get("state", item["status"]) if item["status"] == "OK" else item["status"]
        print(f"    -> {est}")
    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "signal_date": hoje.isoformat(),
            "engine": "30m breakout (structural pivot 5) + origin zone + 1xATR stop",
            "note": "Setup pre-mapped from the PRE-FUND candidates. Not an order: entry still requires a 30m candle to close reacting inside the zone.",
        },
        "candidates": resultados,
    }
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nsalvo: {DEST} | {len(resultados)} candidatos")


if __name__ == "__main__":
    main()
