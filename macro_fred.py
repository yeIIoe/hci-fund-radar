"""
fred_client.py — Pull diário FRED (Federal Reserve Economic Data).

4 séries chave pra Gold:
- DGS10    : 10-Year Treasury Constant Maturity Rate (nominal yield, daily)
- DFII10   : 10-Year TIPS yield (REAL yield) — correlação -0.85 com gold
- T10YIE   : 10-Year Breakeven Inflation Rate
- DTWEXBGS : Trade Weighted U.S. Dollar Index (Broad, Goods & Services) — correlação -0.60 com gold

API:
- Base URL: https://api.stlouisfed.org/fred/series/observations
- API key OPCIONAL via env var FRED_API_KEY (registrar grátis em fred.stlouisfed.org).
- Sem key, tentamos endpoint público (rate-limited mas funcional).

Fail-open:
- Se request falha, usa cache anterior (state/fred_latest.json).
- Pipeline nunca quebra: macro_score.py degrada graciosamente.

Uso:
    python -m macro_layer.fred_client          # pull + cache + print resumo
    python -m macro_layer.fred_client --json   # output JSON puro pra outros scripts

Autor: Eduardo G. Hoki + Claude
Data: Dia 11
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import yfinance as yf
except ImportError:
    yf = None  # type: ignore


# Portado 31-ago-2026 para o repo do site (Eduardo: nada roda na maquina dele).
# O caminho era fixo em C:/Trading e so funcionava naquela maquina.
STATE_DIR = Path(__file__).resolve().parent / "data"
LATEST_FILE = STATE_DIR / "fred_latest.json"
HISTORY_DIR = STATE_DIR / "fred_history"

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Séries chave Gold (ID FRED → descrição curta)
SERIES = {
    "DGS10":    "10Y Treasury Yield (nominal)",
    "DFII10":   "10Y TIPS Yield (real)",
    "T10YIE":   "10Y Breakeven Inflation",
    "DTWEXBGS": "DXY Broad Trade-Weighted (Fed, 26 moedas)",
}

# Fallback Yahoo Finance pra séries que tem equivalente público.
# (DFII10 / T10YIE só existem no FRED — sem fallback público confiável.)
YF_FALLBACK = {
    "DGS10":    "^TNX",       # 10Y Treasury yield
}

# Séries SEMPRE via yfinance (sem equivalente FRED ou queremos um índice diferente).
# Eduardo (Dia 11): pediu DOIS DXY combinados — Broad (FRED) + ICE (yfinance).
YF_FORCED = {
    "DXY_ICE":  ("DX-Y.NYB", "DXY ICE (6 moedas, base 1973=100)"),
}


@dataclass
class FredObservation:
    series_id: str
    description: str
    value: Optional[float]
    date: Optional[str]
    fetched_at: str
    source: str  # "api" | "cache" | "missing"


def _fetch_series(series_id: str, api_key: Optional[str],
                  timeout: tuple = (10, 30), retries: int = 3) -> Optional[tuple[float, str]]:
    """Fetch última observação válida (não '.') de uma série FRED.

    Robusto: timeout (connect=10s, read=30s) + retry com backoff exponencial.
    A API do FRED as vezes demora >10s; 1 timeout nao pode matar a serie.
    Retorna (value, date) ou None se falhar apos todas as tentativas.
    """
    if requests is None:
        return None

    params = {
        "series_id": series_id,
        "file_type": "json",
        "sort_order": "desc",
        "limit": "10",  # pega últimas 10 pra pular weekends/holidays ('.')
    }
    if api_key:
        params["api_key"] = api_key

    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(FRED_BASE, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            obs_list = data.get("observations", [])
            for obs in obs_list:
                val_str = obs.get("value", ".")
                if val_str and val_str != ".":
                    try:
                        return float(val_str), obs.get("date", "")
                    except (ValueError, TypeError):
                        continue
            return None  # respondeu mas sem valor valido -> nao adianta retry
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))   # backoff 1.5s, 3.0s
    print(f"[fred_client] WARN: {series_id} fetch falhou apos {retries} tentativas: {last_exc}", file=sys.stderr)
    return None


def _fetch_yf_ticker(yf_ticker: str, timeout: int = 10) -> Optional[tuple[float, str]]:
    """Helper genérico: pega último close válido de um ticker yfinance."""
    if yf is None:
        return None
    try:
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return None
        valid = hist["Close"].dropna()
        if valid.empty:
            return None
        last_val = float(valid.iloc[-1])
        last_date = valid.index[-1].strftime("%Y-%m-%d")
        return last_val, last_date
    except Exception as exc:
        print(f"[fred_client] WARN: yfinance {yf_ticker} falhou: {exc}", file=sys.stderr)
        return None


def _fetch_yf(series_id: str) -> Optional[tuple[float, str]]:
    """Fallback yfinance pra séries FRED que tem equivalente público."""
    yf_ticker = YF_FALLBACK.get(series_id)
    if not yf_ticker:
        return None
    return _fetch_yf_ticker(yf_ticker)


def _load_cache() -> dict:
    if not LATEST_FILE.exists():
        return {}
    try:
        return json.loads(LATEST_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    LATEST_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Snapshot histórico (1 por dia, idempotente)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hist_file = HISTORY_DIR / f"fred_{today}.json"
    hist_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def pull_all(api_key: Optional[str] = None, verbose: bool = True) -> dict:
    """Pull todas as séries. Fail-open: usa cache pra séries que falharam.

    Retorna dict com:
        - series: {ID: FredObservation as dict}
        - real_yield_10y: float (DFII10 direto)
        - breakeven_10y: float (T10YIE)
        - dxy: float (DTWEXBGS)
        - nominal_10y: float (DGS10)
        - fetched_at: ISO timestamp UTC
        - sources_summary: {api: N, cache: N, missing: N}
    """
    api_key = api_key or os.environ.get("FRED_API_KEY", "")
    cache = _load_cache()
    cached_series = cache.get("series", {})

    results = {}
    counts = {"api": 0, "yf": 0, "cache": 0, "missing": 0}
    now_iso = datetime.now(timezone.utc).isoformat()

    for sid, desc in SERIES.items():
        fetched = _fetch_series(sid, api_key) if requests else None
        if fetched:
            obs = FredObservation(
                series_id=sid, description=desc,
                value=fetched[0], date=fetched[1],
                fetched_at=now_iso, source="api",
            )
            counts["api"] += 1
        elif (yf_fetched := _fetch_yf(sid)) is not None:
            obs = FredObservation(
                series_id=sid, description=desc,
                value=yf_fetched[0], date=yf_fetched[1],
                fetched_at=now_iso, source="yfinance",
            )
            counts["yf"] += 1
        elif sid in cached_series:
            old = cached_series[sid]
            obs = FredObservation(
                series_id=sid, description=desc,
                value=old.get("value"), date=old.get("date"),
                fetched_at=old.get("fetched_at", now_iso), source="cache",
            )
            counts["cache"] += 1
        else:
            obs = FredObservation(
                series_id=sid, description=desc,
                value=None, date=None,
                fetched_at=now_iso, source="missing",
            )
            counts["missing"] += 1
        results[sid] = asdict(obs)

    # Séries forçadas sempre via yfinance (DXY_ICE etc — não querem fallback nem FRED)
    for sid, (yf_ticker, desc) in YF_FORCED.items():
        fetched = _fetch_yf_ticker(yf_ticker) if yf else None
        if fetched:
            obs = FredObservation(
                series_id=sid, description=desc,
                value=fetched[0], date=fetched[1],
                fetched_at=now_iso, source="yfinance",
            )
            counts["yf"] += 1
        elif sid in cached_series:
            old = cached_series[sid]
            obs = FredObservation(
                series_id=sid, description=desc,
                value=old.get("value"), date=old.get("date"),
                fetched_at=old.get("fetched_at", now_iso), source="cache",
            )
            counts["cache"] += 1
        else:
            obs = FredObservation(
                series_id=sid, description=desc,
                value=None, date=None,
                fetched_at=now_iso, source="missing",
            )
            counts["missing"] += 1
        results[sid] = asdict(obs)

    payload = {
        "fetched_at": now_iso,
        "series": results,
        "real_yield_10y":  results["DFII10"]["value"],
        "breakeven_10y":   results["T10YIE"]["value"],
        "dxy":             results["DTWEXBGS"]["value"],   # legacy alias = broad
        "dxy_broad":       results["DTWEXBGS"]["value"],   # Fed broad (26 moedas)
        "dxy_ice":         results.get("DXY_ICE", {}).get("value"),  # ICE 6 moedas
        "nominal_10y":     results["DGS10"]["value"],
        "sources_summary": counts,
    }

    _save_cache(payload)

    if verbose:
        print(f"[fred_client] {now_iso}")
        for sid, obs in results.items():
            val = obs["value"]
            val_str = f"{val:.3f}" if val is not None else "N/A"
            print(f"  {sid:<10} = {val_str:>8}  ({obs['date'] or '----'}, {obs['source']})  # {obs['description']}")
        print(f"  sources: api={counts['api']} yfinance={counts['yf']} cache={counts['cache']} missing={counts['missing']}")

    return payload


def load_latest() -> dict:
    """Lê snapshot mais recente sem pull. Usado pelo macro_score e dashboard."""
    return _load_cache()


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FRED daily puller pra HCI-EA")
    parser.add_argument("--json", action="store_true", help="output JSON puro (silencioso)")
    parser.add_argument("--api-key", default=None, help="override FRED_API_KEY")
    args = parser.parse_args()

    payload = pull_all(api_key=args.api_key, verbose=not args.json)

    if args.json:
        print(json.dumps(payload, indent=2))
