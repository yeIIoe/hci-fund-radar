# -*- coding: utf-8 -*-
"""data/yields.json — o juro de 2 anos das 8 moedas, com variacao e frescor.

Honestidade sobre "tempo real"
------------------------------
Nao existe. Estas sao curvas soberanas oficiais, e cada uma publica no seu ritmo:
USD e NZD chegam em D+1, EUR/CAD/CHF em D+2, GBP e JPY em D+3, e o AUD e
SEMANAL — pode estar 7 dias parado. O painel mostra o atraso de cada moeda em
vez de fingir que tudo e do mesmo instante.

O que a pagina faz e reler este arquivo periodicamente; quando `update_fund.py`
roda e traz dado novo, o painel acompanha sem recarregar.

Campos por moeda:
  yield        ultimo valor publicado, em %
  d1 d5 d20    variacao em pontos-base sobre 1, 5 e 20 observacoes
  sigma_bp     desvio-padrao do movimento diario, 252 observacoes
  z1           quao incomum foi o movimento de 1 dia, em desvios
  history      252 pontos para o grafico
  as_of        data da observacao   |   stale_days  atraso em dias uteis
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from update_fund import CURRENCIES, business_age, read_all_yields

DEST = ROOT / "data" / "yields.json"
JANELA = 252

# o que move um juro de 2 anos, por moeda — a instituicao que decide a taxa curta
BANCO = {
    "EUR": ("European Central Bank", "https://www.ecb.europa.eu/press/pr/date/html/index.en.html"),
    "GBP": ("Bank of England", "https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate"),
    "AUD": ("Reserve Bank of Australia", "https://www.rba.gov.au/media-releases/"),
    "NZD": ("Reserve Bank of New Zealand", "https://www.rbnz.govt.nz/hub/news"),
    "USD": ("Federal Reserve", "https://www.federalreserve.gov/newsevents/pressreleases.htm"),
    "CAD": ("Bank of Canada", "https://www.bankofcanada.ca/press/press-releases/"),
    "CHF": ("Swiss National Bank", "https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy"),
    "JPY": ("Bank of Japan", "https://www.boj.or.jp/en/announcements/index.htm"),
}


def main() -> None:
    series = read_all_yields()
    snap = json.loads((ROOT / "data" / "fund_snapshot.json").read_text(encoding="utf-8"))
    fontes = {x["currency"]: x for x in snap.get("sources", [])}
    hoje = date.today()

    saida = []
    for moeda in CURRENCIES:
        s = series.get(moeda) or {}
        dias = sorted(d for d, v in s.items() if v is not None)
        if len(dias) < 30:
            continue
        vals = [float(s[d]) for d in dias]
        ultimo = dias[-1]

        def var(n: int) -> float | None:
            return None if len(vals) <= n else round((vals[-1] - vals[-1 - n]) * 100.0, 1)

        movs = [(vals[i] - vals[i - 1]) * 100.0 for i in range(max(1, len(vals) - JANELA), len(vals))]
        sigma = statistics.stdev(movs) if len(movs) > 2 else None
        d1 = var(1)
        f = fontes.get(moeda, {})
        banco, banco_url = BANCO.get(moeda, ("", ""))
        saida.append({
            "currency": moeda,
            "yield": round(vals[-1], 4),
            "as_of": ultimo.isoformat(),
            "stale_days": business_age(ultimo, hoje),
            "d1": d1, "d5": var(5), "d20": var(20),
            "sigma_bp": round(sigma, 2) if sigma else None,
            "z1": round(d1 / sigma, 2) if (d1 is not None and sigma and sigma > 0) else None,
            "cadence": f.get("cadence", ""),
            "source": f.get("source", ""),
            "source_url": f.get("source_url", ""),
            "central_bank": banco,
            "central_bank_url": banco_url,
            "history": [{"d": d.isoformat(), "y": round(float(s[d]), 4)} for d in dias[-JANELA:]],
        })

    saida.sort(key=lambda x: -x["yield"])
    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": ("Official sovereign 2-year curves. Each central bank publishes on its own "
                     "schedule — this is not a live feed and never can be from these sources. "
                     "Every card shows how many business days old its reading is."),
            "window": JANELA,
        },
        "currencies": saida,
    }
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"salvo: {DEST} | {len(saida)} moedas")
    for x in saida:
        print(f"  {x['currency']}: {x['yield']:>7.3f}%  1d {str(x['d1']):>6} bp  "
              f"5d {str(x['d5']):>6}  20d {str(x['d20']):>6}  sigma {x['sigma_bp']}  "
              f"atraso {x['stale_days']}d")


if __name__ == "__main__" and "--calendario" not in sys.argv:
    main()


# ---------------------------------------------------------------------------
# CORTE DE TEMPO: o yield que era conhecido em CADA dia do calendario.
# Sem isto a aba Yields mostrava HOJE por baixo de um corte no passado — o mesmo
# vazamento silencioso que a matriz tinha. Para o dia D grava-se a ultima
# observacao publicada ATE D, com a defasagem real e as variacoes calculadas so
# com observacoes anteriores. Nada depois de D entra.
# ---------------------------------------------------------------------------
def grava_no_calendario() -> None:
    import bisect
    series = read_all_yields()
    porMoeda = {}
    for moeda in CURRENCIES:
        s = series.get(moeda) or {}
        dias = sorted(d for d, v in s.items() if v is not None)
        vals = [float(s[d]) for d in dias]
        sig = []
        for i in range(len(vals)):
            ini = max(1, i - JANELA + 1)
            movs = [(vals[k] - vals[k - 1]) * 100.0 for k in range(ini, i + 1)]
            sig.append(round(statistics.stdev(movs), 2) if len(movs) > 2 else None)
        porMoeda[moeda] = (dias, vals, sig)

    escritos = 0
    for arq in sorted((ROOT / "data" / "calendar").glob("calendar_*.json")):
        payload = json.loads(arq.read_text(encoding="utf-8"))
        mudou = False
        for dia in payload["days"]:
            alvo = date.fromisoformat(dia["date"])
            bloco = {}
            for moeda, (dias, vals, sig) in porMoeda.items():
                j = bisect.bisect_right(dias, alvo) - 1     # ultima obs ATE o dia
                if j < 0:
                    continue
                def d(n):
                    return None if j - n < 0 else round((vals[j] - vals[j - n]) * 100.0, 1)
                bloco[moeda] = {"y": round(vals[j], 4), "a": dias[j].isoformat(),
                                "s": business_age(dias[j], alvo),
                                "d1": d(1), "d5": d(5), "d20": d(20), "sg": sig[j]}
            if bloco:
                dia["yields"] = bloco
                mudou = True
        if mudou:
            arq.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            escritos += 1
    print(f"calendario: {escritos} arquivos com o yield conhecido em cada dia")


if __name__ == "__main__" and "--calendario" in sys.argv:
    grava_no_calendario()
