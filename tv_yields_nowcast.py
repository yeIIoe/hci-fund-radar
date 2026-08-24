# -*- coding: utf-8 -*-
"""tv_yields_nowcast.py — NOWCAST dos yields 2y via TradingView (24/ago/2026).

POR QUE EXISTE
--------------
As fontes oficiais publicam com 2-4 dias de atraso (AUD chega a 7). Mas o yield
de 2 anos e um PRECO negociado ao vivo — o TradingView expoe as series TVC:
US02Y, DE02Y, GB02Y, JP02Y, AU02Y, CA02Y, CH02Y, NZ02Y em streaming, de graca.

Este coletor grava o valor DE HOJE em data/raw/tv_nowcast.json. O merge em
update_fund.read_all_yields() usa esse ponto SO quando a serie oficial ainda nao
tem o dia — o oficial continua sendo a espinha dorsal historica e a auditoria.

PIT: usar o preco de mercado conhecido HOJE no sinal de HOJE e mais correto, nao
menos — o atraso oficial era o defeito. O historico backfilled nos calendarios
continua vindo do oficial (o que era conhecido em cada dia daquela epoca).

GUARDA-CHUVAS
-------------
- |TV − ultimo oficial| > 0,80 ponto percentual -> descarta (simbolo errado ou
  spike de feed) e loga.
- Resposta fora do padrao -> descarta a moeda, segue com as outras.
- O arquivo carrega fetched_at; o merge ignora nowcast com mais de 24h.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SIMBOLO = {"USD": "US02Y", "EUR": "DE02Y", "GBP": "GB02Y", "JPY": "JP02Y",
           "AUD": "AU02Y", "CAD": "CA02Y", "CHF": "CH02Y", "NZD": "NZ02Y"}
DEST = ROOT / "data" / "raw" / "tv_nowcast.json"
LIMITE_PP = 0.80


def busca(sym: str):
    url = ("https://scanner.tradingview.com/symbol?symbol=TVC%%3A%s"
           "&fields=close,update_mode" % sym)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode("utf-8"))
    v = d.get("close")
    if not isinstance(v, (int, float)) or not (-2.0 < v < 25.0):
        raise ValueError("valor implausivel: %r" % v)
    return float(v)


def main() -> None:
    # ultimo oficial, para o guarda-chuva de sanidade
    sys.path.insert(0, str(ROOT))
    from update_fund import read_all_yields
    oficial = read_all_yields()

    agora = datetime.now(timezone.utc)
    out = {"fetched_at": agora.isoformat(), "date": agora.date().isoformat(),
           "source": "TradingView TVC (scanner endpoint)", "yields": {}}
    for moeda, sym in SIMBOLO.items():
        try:
            v = busca(sym)
        except Exception as e:
            print("  %s (%s): FALHOU — %s" % (moeda, sym, e))
            continue
        ult = None
        s = oficial.get(moeda) or {}
        datas = [d for d, x in s.items() if x is not None]
        if datas:
            ult = s[max(datas)]
        if ult is not None and abs(v - ult) > LIMITE_PP:
            print("  %s: DESCARTADO — TV %.3f vs oficial %.3f (dif > %.2fpp)"
                  % (moeda, v, ult, LIMITE_PP))
            continue
        out["yields"][moeda] = {"value": v, "symbol": "TVC:" + sym,
                                "official_last": ult}
        print("  %s: %.4f%%  (oficial %.4f)" % (moeda, v, ult if ult is not None else float("nan")))
    DEST.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("nowcast: %d/8 moedas -> %s" % (len(out["yields"]), DEST))


if __name__ == "__main__":
    main()
