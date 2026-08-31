"""
cot_downloader.py — Download semanal CFTC Disaggregated Commitments of Traders.

Fonte: Socrata Open Data API (CFTC oficial)
- Endpoint: https://publicreporting.cftc.gov/resource/72hh-3qpy.json
- Dataset:  Disaggregated Futures-Only Reports
- Gold:     cftc_contract_market_code = "088691" (Gold, COMEX)

Schedule oficial CFTC:
- Tuesday close (cutoff)
- Friday 15:30 ET (publish)
→ Rodar este script toda sexta-feira 22:00 UTC (após publish)

Output:
- state/cot_latest.json     : última leitura + z-scores rolando 52 semanas
- state/cot_history/*.json  : snapshots semanais

Métricas calculadas:
- Net Managed Money = MM_long - MM_short
- Net Producer      = Producer_long - Producer_short
- MM_position_ratio = MM_long / (MM_long + MM_short)   ← 0.5 = neutro
- MM_z_score_52w    = (current - mean_52w) / std_52w   ← |z|>2 = extremo

Uso:
    python -m macro_layer.cot_downloader           # download + cache + resumo
    python -m macro_layer.cot_downloader --json    # output JSON puro
    python -m macro_layer.cot_downloader --weeks 104  # baixa 2 anos de history

Autor: Eduardo G. Hoki + Claude
Data: Dia 11
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore


# Portado 31-ago-2026 para o repo do site (Eduardo: nada roda na maquina dele).
# O caminho era fixo em C:/Trading e so funcionava naquela maquina.
STATE_DIR = Path(__file__).resolve().parent / "data"
LATEST_FILE = STATE_DIR / "cot_latest.json"
HISTORY_DIR = STATE_DIR / "cot_history"

SOCRATA_BASE = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
GOLD_CODE = "088691"  # Gold, COMEX (Disaggregated Futures Only)


@dataclass
class CotSnapshot:
    report_date: str  # YYYY-MM-DD
    mm_long: int
    mm_short: int
    mm_spread: int
    mm_net: int
    mm_long_pct: float           # MM_long / total_OI
    mm_position_ratio: float     # MM_long / (MM_long + MM_short)
    producer_long: int
    producer_short: int
    producer_net: int
    total_oi: int
    source: str  # "api" | "cache"


def _fetch_socrata(weeks: int = 52, timeout: int = 15) -> list[dict]:
    """Pull últimas N semanas de COT Gold via Socrata. Retorna lista de dicts."""
    if requests is None:
        return []

    params = {
        "cftc_contract_market_code": GOLD_CODE,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": str(weeks),
    }
    try:
        r = requests.get(SOCRATA_BASE, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        print(f"[cot_downloader] WARN: Socrata fetch falhou: {exc}", file=sys.stderr)
        return []


def _to_int(v) -> int:
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return 0


def _parse_row(row: dict) -> CotSnapshot:
    """Converte 1 row Socrata em CotSnapshot.

    Campos relevantes (Disaggregated Futures Only):
    - m_money_positions_long_all   : Managed Money long
    - m_money_positions_short_all  : Managed Money short
    - m_money_positions_spread     : Managed Money spread
    - prod_merc_positions_long     : Producer/Merchant long
    - prod_merc_positions_short    : Producer/Merchant short
    - open_interest_all            : Total open interest
    - report_date_as_yyyy_mm_dd    : Report date
    """
    mm_long  = _to_int(row.get("m_money_positions_long_all"))
    mm_short = _to_int(row.get("m_money_positions_short_all"))
    mm_spread = _to_int(row.get("m_money_positions_spread"))
    prod_long  = _to_int(row.get("prod_merc_positions_long"))
    prod_short = _to_int(row.get("prod_merc_positions_short"))
    total_oi = _to_int(row.get("open_interest_all"))

    mm_total_dir = mm_long + mm_short
    mm_position_ratio = (mm_long / mm_total_dir) if mm_total_dir > 0 else 0.5
    mm_long_pct = (mm_long / total_oi) if total_oi > 0 else 0.0

    report_date = str(row.get("report_date_as_yyyy_mm_dd", ""))[:10]

    return CotSnapshot(
        report_date=report_date,
        mm_long=mm_long, mm_short=mm_short, mm_spread=mm_spread,
        mm_net=mm_long - mm_short,
        mm_long_pct=round(mm_long_pct, 4),
        mm_position_ratio=round(mm_position_ratio, 4),
        producer_long=prod_long, producer_short=prod_short,
        producer_net=prod_long - prod_short,
        total_oi=total_oi,
        source="api",
    )


def _zscore(values: list[float]) -> float:
    """Z-score do último valor vs todos anteriores. Sem numpy."""
    if len(values) < 2:
        return 0.0
    current = values[0]
    historical = values[1:]
    n = len(historical)
    mean = sum(historical) / n
    variance = sum((x - mean) ** 2 for x in historical) / n
    std = variance ** 0.5
    if std < 1e-9:
        return 0.0
    return round((current - mean) / std, 3)


def _percentile_rank(values: list[float]) -> float:
    """Percentile rank do current entre histórico (0.0-1.0). 1.0 = max, 0.0 = min."""
    if len(values) < 2:
        return 0.5
    current = values[0]
    historical = values[1:]
    below = sum(1 for x in historical if x < current)
    return round(below / len(historical), 3)


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

    # Snapshot por report_date (idempotente — rodar 2× mesma semana sobrescreve igual)
    rd = payload.get("latest", {}).get("report_date", "unknown")
    hist_file = HISTORY_DIR / f"cot_{rd}.json"
    hist_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def pull(weeks: int = 52, verbose: bool = True) -> dict:
    """Pull último COT + calcula z-scores. Fail-open via cache."""
    cache = _load_cache()
    rows = _fetch_socrata(weeks=weeks)
    now_iso = datetime.now(timezone.utc).isoformat()

    if not rows:
        if verbose:
            print("[cot_downloader] Sem dados novos — retornando cache", file=sys.stderr)
        return cache if cache else {
            "fetched_at": now_iso,
            "latest": None,
            "history_count": 0,
            "error": "fetch_failed_and_no_cache",
        }

    snapshots = [_parse_row(r) for r in rows]
    latest = snapshots[0]

    # Z-scores e percentile ranks sobre histórico (incluindo o atual no índice 0)
    mm_nets = [s.mm_net for s in snapshots]
    mm_ratios = [s.mm_position_ratio for s in snapshots]
    prod_nets = [s.producer_net for s in snapshots]

    payload = {
        "fetched_at": now_iso,
        "latest": asdict(latest),
        "history_count": len(snapshots),
        "metrics": {
            "mm_net_zscore_52w": _zscore(mm_nets),
            "mm_net_percentile_52w": _percentile_rank(mm_nets),
            "mm_ratio_zscore_52w": _zscore(mm_ratios),
            "producer_net_zscore_52w": _zscore(prod_nets),
        },
        "history": [asdict(s) for s in snapshots],
    }

    _save_cache(payload)

    if verbose:
        m = payload["metrics"]
        L = payload["latest"]
        z = m["mm_net_zscore_52w"]
        signal = (
            "BULL_EXTREME" if z > 1.5 else
            "BULL" if z > 0.5 else
            "BEAR" if z < -0.5 else
            "BEAR_EXTREME" if z < -1.5 else
            "NEUTRAL"
        )
        print(f"[cot_downloader] {now_iso}")
        print(f"  Latest report_date: {L['report_date']}")
        print(f"  Managed Money: long={L['mm_long']:>7,}  short={L['mm_short']:>7,}  net={L['mm_net']:>+8,}")
        print(f"  Producer:      long={L['producer_long']:>7,}  short={L['producer_short']:>7,}  net={L['producer_net']:>+8,}")
        print(f"  Open Interest: {L['total_oi']:,}")
        print(f"  MM net z-score 52w:    {z:>+6.2f}  ({signal})")
        print(f"  MM net percentile:     {m['mm_net_percentile_52w']*100:>5.1f}%")
        print(f"  MM long ratio:         {L['mm_position_ratio']*100:>5.1f}%")
        print(f"  History weeks loaded:  {payload['history_count']}")

    return payload


def load_latest() -> dict:
    return _load_cache()


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CFTC Disaggregated COT puller (Gold)")
    parser.add_argument("--json", action="store_true", help="output JSON puro")
    parser.add_argument("--weeks", type=int, default=52, help="número de semanas de histórico")
    args = parser.parse_args()

    payload = pull(weeks=args.weeks, verbose=not args.json)

    if args.json:
        print(json.dumps(payload, indent=2))
