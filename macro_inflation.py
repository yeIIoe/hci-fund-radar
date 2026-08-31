"""
inflation_nowcast.py — Pull do Cleveland Fed Inflation Nowcast (Dia 12).

Source: Federal Reserve Bank of Cleveland publica diariamente (~10am ET)
um nowcast model-based pra inflação do mês CORRENTE (antes do release oficial).

Cobertura:
  - CPI Inflation (headline) MoM
  - Core CPI Inflation MoM
  - PCE Inflation (headline) MoM
  - Core PCE Inflation MoM

Endpoint discovered (não documentado oficialmente):
  https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_month.json
  https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_quarter.json

Formato: FusionCharts-style com 155 snapshots históricos (1 por dia útil).

Uso CLI:
    python -m macro_layer.inflation_nowcast --refresh      # pull + cache
    python -m macro_layer.inflation_nowcast                # mostra current
    python -m macro_layer.inflation_nowcast --json         # JSON puro
    python -m macro_layer.inflation_nowcast --history 10   # ultimas 10 daily updates

Uso programatico:
    from macro_layer.inflation_nowcast import load_current
    nc = load_current()
    print(nc['cpi_mom'], nc['period_label'])

Autor: Eduardo G. Hoki + Claude
Data: Dia 12
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Portado 31-ago-2026 (nada roda na maquina do Eduardo). Caminho era fixo em C:/Trading.
STATE_DIR = Path(__file__).resolve().parent / "data"
CACHE_FILE = STATE_DIR / "inflation_nowcast.json"

URL_MONTH = "https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_month.json"
URL_QUARTER = "https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_quarter.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0",
    "Accept": "application/json, */*",
}

# Mapeia seriesname interno do Cleveland Fed -> key padronizada
SERIES_MAP = {
    "CPI Inflation": "cpi_mom",
    "Core CPI Inflation": "core_cpi_mom",
    "PCE Inflation": "pce_mom",
    "Core PCE Inflation": "core_pce_mom",
    "Actual CPI Inflation": "actual_cpi_mom",
    "Actual Core CPI Inflation": "actual_core_cpi_mom",
    "Actual PCE Inflation": "actual_pce_mom",
    "Actual Core PCE Inflation": "actual_core_pce_mom",
}


def _fetch_json(url: str, timeout: int = 15) -> Optional[list]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="ignore"))
    except Exception as exc:
        print(f"[inflation_nowcast] fetch fail {url}: {exc}", file=sys.stderr)
        return None


def _extract_latest_values(snapshot: dict) -> dict:
    """Pega último valor não-vazio de cada serie do snapshot."""
    out: dict = {}
    for s in snapshot.get("dataset", []):
        key = SERIES_MAP.get(s.get("seriesname"))
        if not key:
            continue
        last_val: Optional[float] = None
        last_idx: Optional[int] = None
        for i, p in enumerate(s.get("data", [])):
            v = (p.get("value") or "").strip()
            if v and v not in ("-", "0", "null"):
                try:
                    last_val = float(v)
                    last_idx = i
                except ValueError:
                    continue
        out[key] = last_val
        out[key + "_idx"] = last_idx
    return out


def refresh() -> dict:
    """Pull Cleveland Fed nowcast (month + quarter), processa, cacheia."""
    month_data = _fetch_json(URL_MONTH)
    quarter_data = _fetch_json(URL_QUARTER)

    payload: dict = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Federal Reserve Bank of Cleveland (Inflation Nowcasting)",
    }

    if month_data and isinstance(month_data, list) and month_data:
        last_snap = month_data[-1]
        chart = last_snap.get("chart", {})
        vals = _extract_latest_values(last_snap)
        payload["month"] = {
            "snapshot_date_et": chart.get("_comment", "").split(" ")[0],
            "period_label": chart.get("subcaption", "?"),  # ex: "2026-5"
            "yaxis": chart.get("yaxisname", ""),
            "snapshots_total": len(month_data),
            **vals,
        }

    if quarter_data and isinstance(quarter_data, list) and quarter_data:
        last_snap = quarter_data[-1]
        chart = last_snap.get("chart", {})
        vals = _extract_latest_values(last_snap)
        payload["quarter"] = {
            "snapshot_date_et": chart.get("_comment", "").split(" ")[0],
            "period_label": chart.get("subcaption", "?"),
            "yaxis": chart.get("yaxisname", ""),
            "snapshots_total": len(quarter_data),
            **vals,
        }

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_current() -> dict:
    """Atalho pra outros modulos: retorna dict simples com os nowcasts MoM."""
    cache = load_cache()
    month = cache.get("month", {})
    return {
        "period_label": month.get("period_label", ""),
        "snapshot_date_et": month.get("snapshot_date_et", ""),
        "cpi_mom": month.get("cpi_mom"),
        "core_cpi_mom": month.get("core_cpi_mom"),
        "pce_mom": month.get("pce_mom"),
        "core_pce_mom": month.get("core_pce_mom"),
        "source": cache.get("source", ""),
    }


def history_for_series(series_key: str, n_days: int = 30) -> list[dict]:
    """Lê SNAPSHOTS_DIR histórica do month JSON (último n_days valores diários
    do nowcast pra acompanhar evolução).

    Args:
        series_key: 'cpi_mom' / 'core_cpi_mom' / 'pce_mom' / 'core_pce_mom'
        n_days: quantos snapshots históricos retornar
    """
    seriesname_map_reverse = {v: k for k, v in SERIES_MAP.items()}
    series_name = seriesname_map_reverse.get(series_key)
    if not series_name:
        return []

    month_data = _fetch_json(URL_MONTH)
    if not month_data or not isinstance(month_data, list):
        return []

    out: list[dict] = []
    for snap in month_data[-n_days:]:
        chart = snap.get("chart", {})
        for s in snap.get("dataset", []):
            if s.get("seriesname") != series_name:
                continue
            for p in s.get("data", []):
                v = (p.get("value") or "").strip()
                if v and v not in ("-", "0"):
                    try:
                        out.append({
                            "snapshot_date_et": chart.get("_comment", "").split(" ")[0],
                            "value": float(v),
                        })
                        break  # primeiro valor não-vazio
                    except ValueError:
                        continue
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleveland Fed Inflation Nowcast puller")
    parser.add_argument("--refresh", action="store_true", help="pull + cache")
    parser.add_argument("--json", action="store_true", help="JSON puro")
    parser.add_argument("--history", type=int, default=0,
                        help="Mostra N snapshots históricos da serie CPI MoM")
    args = parser.parse_args()

    if args.refresh:
        print("[inflation_nowcast] pull Cleveland Fed...", file=sys.stderr)
        payload = refresh()
        print(f"[inflation_nowcast] cacheado em {CACHE_FILE}", file=sys.stderr)
    else:
        payload = load_cache()
        if not payload:
            print("[inflation_nowcast] cache vazio, rodando refresh...", file=sys.stderr)
            payload = refresh()

    if args.history > 0:
        hist = history_for_series("cpi_mom", n_days=args.history)
        if args.json:
            print(json.dumps(hist, indent=2))
        else:
            print(f"\n=== CPI MoM Nowcast — últimos {len(hist)} dias ===")
            for h in hist:
                print(f"  {h['snapshot_date_et']}  {h['value']:+.3f}%")
        return 0

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"\n=== Cleveland Fed Inflation Nowcast ===")
    print(f"Source: {payload.get('source', '?')}")
    print(f"Updated: {payload.get('updated_at_utc', '?')}\n")

    month = payload.get("month", {})
    if month:
        print(f"--- MONTH ({month.get('period_label', '?')}) "
              f"snapshot {month.get('snapshot_date_et', '?')} ---")
        for label, key in [("CPI MoM", "cpi_mom"), ("Core CPI MoM", "core_cpi_mom"),
                           ("PCE MoM", "pce_mom"), ("Core PCE MoM", "core_pce_mom")]:
            v = month.get(key)
            print(f"  {label:18s}  {v:+.3f}%" if v is not None else f"  {label:18s}  N/A")

    quarter = payload.get("quarter", {})
    if quarter:
        print(f"\n--- QUARTER ({quarter.get('period_label', '?')}) "
              f"snapshot {quarter.get('snapshot_date_et', '?')} ---")
        for label, key in [("CPI QoQ", "cpi_mom"), ("Core CPI QoQ", "core_cpi_mom"),
                           ("PCE QoQ", "pce_mom"), ("Core PCE QoQ", "core_pce_mom")]:
            v = quarter.get(key)
            print(f"  {label:18s}  {v:+.3f}%" if v is not None else f"  {label:18s}  N/A")

    return 0


if __name__ == "__main__":
    sys.exit(main())
