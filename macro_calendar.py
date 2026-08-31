"""
calendar.py — Calendar de eventos macro pra HCI-EA (Dia 12 — Eduardo).

Combina:
  - ForexFactory RSS (thisweek.xml) — fonte primária, ~7 dias de cobertura
  - FOMC dates hardcoded 2026-2027 — pra cobrir além de 7 dias
  - (futuro) Fed press releases RSS pra speeches Powell

Output cacheado em state/calendar_events.json com normalização:
  - Timestamps UTC (ForexFactory já vem UTC)
  - Impact enum: High / Medium / Low / Holiday
  - Relevância pro gold (HIGH/MED/LOW) auto-computada
  - event_type pro EventScenario (PCE / CPI / NFP / FOMC / GDP / etc, ou null)

Uso CLI:
    python -m macro_layer.calendar --refresh     # pull + cache
    python -m macro_layer.calendar               # le cache + print
    python -m macro_layer.calendar --json        # JSON puro
    python -m macro_layer.calendar --next-24h    # so eventos prox 24h
    python -m macro_layer.calendar --high-only   # so HIGH relevancia GC

Autor: Eduardo G. Hoki + Claude
Data: Dia 12
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


# Portado para o repo do radar em 31-ago-2026: o caminho era fixo em C:\Trading e
# so funcionava na maquina do Eduardo. Agora e relativo ao proprio script, entao roda
# igual no GitHub Actions e localmente.
STATE_DIR = Path(__file__).resolve().parent / "data"
CACHE_FILE = STATE_DIR / "calendar_events.json"

FOREX_FACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# FOMC meeting dates (hardcoded — 8 meetings/ano). Atualizar anualmente.
# Source: federalreserve.gov/monetarypolicy/fomccalendars.htm
# Cada tupla = (start_date, end_date, statement_time_utc).
# Statement sai geralmente 18:00 UTC (14:00 ET) no SEGUNDO dia.
FOMC_MEETINGS = [
    # 2026
    ("2026-06-17", "2026-06-18", "18:00"),
    ("2026-07-28", "2026-07-29", "18:00"),
    ("2026-09-15", "2026-09-16", "18:00"),
    ("2026-10-27", "2026-10-28", "18:00"),
    ("2026-12-08", "2026-12-09", "19:00"),  # DST off, 14:00 ET = 19:00 UTC
    # 2027
    ("2027-01-26", "2027-01-27", "19:00"),
    ("2027-03-16", "2027-03-17", "18:00"),
    ("2027-04-27", "2027-04-28", "18:00"),
    ("2027-06-15", "2027-06-16", "18:00"),
    ("2027-07-27", "2027-07-28", "18:00"),
    ("2027-09-14", "2027-09-15", "18:00"),
    ("2027-10-26", "2027-10-27", "18:00"),
    ("2027-12-07", "2027-12-08", "19:00"),
]


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    country: str
    ts_utc: str             # ISO 8601
    impact: str             # High | Medium | Low | Holiday
    forecast: str
    previous: str
    actual: str
    source: str             # forexfactory | fomc_hardcoded
    url: str
    relevance_gc: str       # HIGH | MED | LOW — relevancia pra Gold trading
    event_type: Optional[str]  # PCE | CPI | NFP | FOMC | GDP | RETAIL_SALES | PPI | JOBS | None


# ──────────────────────────────────────────────────────────────────────
# RELEVANCIA + EVENT TYPE
# ──────────────────────────────────────────────────────────────────────

def relevance_for_gold(country: str, impact: str, title: str) -> str:
    """Determina relevancia do evento pra trade de Gold.

    HIGH: tudo que move DXY/real yields fortemente
    MED:  USD medium + EUR/GBP high (DXY proxy)
    LOW:  resto
    """
    t = title.lower()

    # Keywords macro chave — sempre HIGH
    keywords_high = ['pce price', 'cpi', 'non-farm payrolls', 'fomc statement',
                     'fomc press conf', 'fed chair', 'powell', 'unemployment claims',
                     'jobless claims', 'retail sales', 'ppi', 'core pce', 'core cpi',
                     'fomc economic projections', 'fed rate decision']
    if any(kw in t for kw in keywords_high):
        return 'HIGH'

    # USD High impact = HIGH
    if country == 'USD' and impact == 'High':
        return 'HIGH'

    # USD Medium impact = MED
    if country == 'USD' and impact == 'Medium':
        return 'MED'

    # EUR/GBP High impact = MED (afeta DXY index)
    if country in ('EUR', 'GBP', 'JPY') and impact == 'High':
        return 'MED'

    return 'LOW'


def event_type_for_scenario(title: str, country: str) -> Optional[str]:
    """Mapeia title -> event_type esperado pelo EventScenario agent.

    Retorna None se evento nao deve disparar scenario.
    """
    t = title.lower()
    # So USD events disparam scenario (pivotais pro DXY)
    if country != 'USD':
        return None

    if 'pce' in t:
        return 'PCE'
    if 'cpi' in t:
        return 'CPI'
    if 'non-farm payrolls' in t or t == 'nfp':
        return 'NFP'
    if 'fomc statement' in t or 'fed rate' in t or 'fed chair' in t:
        return 'FOMC'
    if 'gdp' in t and 'price' not in t:
        return 'GDP'
    if 'retail sales' in t and 'control' not in t:
        return 'RETAIL_SALES'
    if 'ppi' in t and 'core' in t:
        return 'PPI'
    if 'ppi' in t:
        return 'PPI'
    if 'unemployment claims' in t or 'jobless claims' in t:
        return 'JOBS'

    return None


# ──────────────────────────────────────────────────────────────────────
# PARSE FOREX FACTORY
# ──────────────────────────────────────────────────────────────────────

def _parse_ff_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Converte 'MM-DD-YYYY' + 'H:MMam/pm' → datetime UTC.

    ForexFactory RSS retorna horarios em UTC (validado empiricamente:
    PCE 8:30 ET aparece como 12:30pm = 12:30 UTC).
    """
    if not date_str or not time_str:
        return None
    # "All Day" / "Tentative" / "" → meio-dia UTC fallback
    if time_str.lower() in ('all day', 'tentative', '', '-'):
        try:
            dt = datetime.strptime(date_str, '%m-%d-%Y')
            return dt.replace(hour=12, minute=0, tzinfo=timezone.utc)
        except ValueError:
            return None
    try:
        full = f"{date_str} {time_str}"
        dt = datetime.strptime(full, '%m-%d-%Y %I:%M%p')
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def fetch_forex_factory(timeout_s: int = 15, retries: int = 2) -> list[CalendarEvent]:
    """Puxa o RSS thisweek.xml do ForexFactory e parseia.

    Retorna lista de CalendarEvent. Vazia se falhar.
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/xml, text/xml, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(FOREX_FACTORY_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                xml_bytes = r.read()
            break
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                print(f"[calendar] ForexFactory fetch falhou: {e}", file=sys.stderr)
                return []

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"[calendar] ForexFactory XML invalido: {e}", file=sys.stderr)
        return []

    events: list[CalendarEvent] = []
    for ev in root.findall('event'):
        title = (ev.findtext('title') or '').strip()
        country = (ev.findtext('country') or '').strip()
        date = (ev.findtext('date') or '').strip()
        timetxt = (ev.findtext('time') or '').strip()
        impact = (ev.findtext('impact') or '').strip()

        dt = _parse_ff_datetime(date, timetxt)
        if dt is None or not title:
            continue

        ts_iso = dt.isoformat()
        eid = hashlib.md5(f"{title}|{country}|{ts_iso}".encode()).hexdigest()[:12]
        events.append(CalendarEvent(
            event_id=eid,
            title=title,
            country=country,
            ts_utc=ts_iso,
            impact=impact or 'Low',
            forecast=(ev.findtext('forecast') or '').strip(),
            previous=(ev.findtext('previous') or '').strip(),
            actual='',
            source='forexfactory',
            url=(ev.findtext('url') or '').strip(),
            relevance_gc=relevance_for_gold(country, impact, title),
            event_type=event_type_for_scenario(title, country),
        ))
    return events


# ──────────────────────────────────────────────────────────────────────
# FOMC HARDCODED (alem dos 7 dias do ForexFactory)
# ──────────────────────────────────────────────────────────────────────

def fomc_events() -> list[CalendarEvent]:
    """Gera CalendarEvent pras reunioes FOMC hardcoded.

    Statement + Press Conf na data do 2o dia, hora UTC config.
    """
    out: list[CalendarEvent] = []
    for start, end, time_utc in FOMC_MEETINGS:
        try:
            hh, mm = map(int, time_utc.split(':'))
            dt = datetime.strptime(end, '%Y-%m-%d').replace(
                hour=hh, minute=mm, tzinfo=timezone.utc
            )
        except ValueError:
            continue

        title = "FOMC Statement + Press Conference"
        ts_iso = dt.isoformat()
        eid = hashlib.md5(f"{title}|USD|{ts_iso}".encode()).hexdigest()[:12]
        out.append(CalendarEvent(
            event_id=eid,
            title=title,
            country='USD',
            ts_utc=ts_iso,
            impact='High',
            forecast='',
            previous='',
            actual='',
            source='fomc_hardcoded',
            url='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm',
            relevance_gc='HIGH',
            event_type='FOMC',
        ))
    return out


# ──────────────────────────────────────────────────────────────────────
# MERGE + DEDUPE + CACHE
# ──────────────────────────────────────────────────────────────────────

def merge_and_dedupe(*lists: list[CalendarEvent]) -> list[CalendarEvent]:
    """Junta multiplas listas, deduplica por event_id, ordena por ts_utc."""
    seen: dict[str, CalendarEvent] = {}
    for lst in lists:
        for e in lst:
            if e.event_id not in seen:
                seen[e.event_id] = e
    return sorted(seen.values(), key=lambda x: x.ts_utc)


def save_cache(events: list[CalendarEvent]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        'updated_at_utc': datetime.now(timezone.utc).isoformat(),
        'count': len(events),
        'events': [asdict(e) for e in events],
    }
    CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {'updated_at_utc': None, 'count': 0, 'events': []}
    try:
        return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {'updated_at_utc': None, 'count': 0, 'events': []}


def refresh() -> dict:
    """Pull todas as fontes + merge + save. Retorna o cache resultante."""
    ff_events = fetch_forex_factory()
    fomc = fomc_events()
    merged = merge_and_dedupe(ff_events, fomc)
    save_cache(merged)
    return load_cache()


# ──────────────────────────────────────────────────────────────────────
# CONSULTAS
# ──────────────────────────────────────────────────────────────────────

def filter_events(events: list[dict], *,
                  only_high_gc: bool = False,
                  next_hours: Optional[int] = None,
                  countries: Optional[set[str]] = None) -> list[dict]:
    """Filtra cache de eventos por criterios."""
    out = events
    now = datetime.now(timezone.utc)

    if next_hours is not None:
        limit_dt = now + timedelta(hours=next_hours)
        out = [e for e in out if now <= datetime.fromisoformat(e['ts_utc']) <= limit_dt]

    if only_high_gc:
        out = [e for e in out if e.get('relevance_gc') == 'HIGH']

    if countries:
        out = [e for e in out if e.get('country') in countries]

    return out


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def _print_events(events: list[dict]) -> None:
    if not events:
        print("  (nenhum evento)")
        return
    for e in events:
        dt = datetime.fromisoformat(e['ts_utc'])
        local = dt.astimezone()  # timezone do sistema
        rel = e.get('relevance_gc', '?')
        et = e.get('event_type', '') or '-'
        title = e['title'][:55]
        flag = '🔴' if rel == 'HIGH' else ('🟡' if rel == 'MED' else '  ')
        print(f"  {flag} {dt.strftime('%a %m-%d %H:%M')}UTC ({local.strftime('%H:%M')}local) "
              f"{e['country']:3s} {e['impact']:6s} [{rel:4s}/{et:6s}] {title}")


def main() -> int:
    parser = argparse.ArgumentParser(description="HCI-EA Calendar — ForexFactory + FOMC hardcoded")
    parser.add_argument('--refresh', action='store_true', help='puxa fontes e atualiza cache')
    parser.add_argument('--json', action='store_true', help='output JSON puro')
    parser.add_argument('--next-24h', action='store_true', help='filtra prox 24h')
    parser.add_argument('--next-7d', action='store_true', help='filtra prox 7 dias')
    parser.add_argument('--high-only', action='store_true', help='so relevancia HIGH pro Gold')
    parser.add_argument('--usd-only', action='store_true', help='so eventos USD')
    args = parser.parse_args()

    if args.refresh:
        print(f"[calendar] pull ForexFactory + FOMC hardcoded...", file=sys.stderr)
        cache = refresh()
        print(f"[calendar] {cache['count']} eventos cacheados em {CACHE_FILE}", file=sys.stderr)
    else:
        cache = load_cache()
        if cache['count'] == 0:
            print(f"[calendar] cache vazio, rodando refresh automatico...", file=sys.stderr)
            cache = refresh()

    events = cache['events']
    if args.next_24h:
        events = filter_events(events, next_hours=24)
    elif args.next_7d:
        events = filter_events(events, next_hours=24*7)
    if args.high_only:
        events = filter_events(events, only_high_gc=True)
    if args.usd_only:
        events = filter_events(events, countries={'USD'})

    if args.json:
        print(json.dumps({'updated_at_utc': cache['updated_at_utc'], 'events': events},
                         indent=2, default=str))
        return 0

    print(f"\n=== HCI-EA Calendar — {len(events)} eventos "
          f"(cache atualizado: {cache.get('updated_at_utc', 'nunca')}) ===\n")
    _print_events(events)
    return 0


if __name__ == '__main__':
    sys.exit(main())
