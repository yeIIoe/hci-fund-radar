# -*- coding: utf-8 -*-
"""tv_yields_nowcast.py — NOWCAST dos yields via TradingView (24/ago/2026).

POR QUE EXISTE
--------------
As fontes oficiais publicam com 2-4 dias de atraso (AUD chega a 7). Mas o yield
soberano e um PRECO negociado ao vivo — o TradingView expoe as series TVC de
graca, em streaming.

Este coletor grava o valor DE HOJE em data/raw/tv_nowcast.json. O merge em
update_fund.read_all_yields() usa esse ponto SO quando a serie oficial ainda nao
tem o dia — o oficial continua sendo a espinha dorsal historica e a auditoria.

PIT: usar o preco de mercado conhecido HOJE no sinal de HOJE e mais correto, nao
menos — o atraso oficial era o defeito. O historico backfilled nos calendarios
continua vindo do oficial (o que era conhecido em cada dia daquela epoca).

CURTO DA CURVA (25/ago/2026) — POR QUE FOI ADICIONADO
-----------------------------------------------------
O BIS (WP 626, Ferrari-Kearns-Schrimpf, publicado no JBF 2021) separa dois
fatores no choque de politica monetaria:
  TARGET = mudanca na taxa curtissima (1 mes)
  PATH   = mudanca na INCLINACAO da curva (a revisao do caminho futuro)
e mede que quem carrega o cambio e o PATH, nao o nivel.

O FUND v0.1 usa SO o 2 anos, que e a soma confusa dos dois. Com 1 ano e 2 anos
das 8 moedas a inclinacao fica disponivel, e a VARIACAO dela e o fator PATH.

⚠️ ESTE ARQUIVO SO COLETA E EXPOE. Nao altera o FUND, nao altera o calendario,
nao altera nada a jusante. Mudar o sinal exige PREREG assinado — a coleta nao.

DISPONIBILIDADE MEDIDA EM 25/ago (endpoint testado moeda a moeda):
  1 ano   -> 8/8 moedas
  3 meses -> 7/8 (AU03MY devolve 404; a Australia nao tem a serie no TVC)
  2 anos  -> 8/8 (ja era o que existia)

GUARDA-CHUVAS
-------------
- 2 anos: |TV − ultimo oficial| > 0,80 pp -> descarta (regra original, intacta).
- 1 ano e 3 meses: nao ha serie oficial para comparar, entao a guarda e
  (a) faixa de plausibilidade e (b) salto contra o proprio nowcast anterior.
- Resposta fora do padrao -> descarta o tenor, segue com os outros.
- O arquivo carrega fetched_at; o merge ignora nowcast com mais de 24h.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 2 anos — a espinha dorsal, NAO MEXER (o merge do FUND depende deste bloco)
SIMBOLO = {"USD": "US02Y", "EUR": "DE02Y", "GBP": "GB02Y", "JPY": "JP02Y",
           "AUD": "AU02Y", "CAD": "CA02Y", "CHF": "CH02Y", "NZD": "NZ02Y"}

# curto da curva — aditivo. AUD nao tem 3 meses no TVC (404 verificado).
PREFIXO = {"USD": "US", "EUR": "DE", "GBP": "GB", "JPY": "JP",
           "AUD": "AU", "CAD": "CA", "CHF": "CH", "NZD": "NZ"}
TENORES = [("3m", "03MY"), ("1y", "01Y"), ("2y", "02Y")]
SEM_3M = {"AUD"}

DEST = ROOT / "data" / "raw" / "tv_nowcast.json"
LIMITE_PP = 0.80          # guarda do 2 anos contra o oficial
SALTO_MAX_PP = 1.00       # guarda do curto contra o nowcast anterior


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


def anterior():
    """Le o nowcast anterior para a guarda de salto do curto da curva."""
    try:
        return json.loads(DEST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def coleta_curva(ant):
    """3m / 1y / 2y por moeda + inclinacao. Aditivo: nada aqui alimenta o FUND."""
    prev = (ant.get("curve") or {})
    out = {}
    for moeda, pref in PREFIXO.items():
        pontos, descartes = {}, []
        for nome, suf in TENORES:
            if nome == "3m" and moeda in SEM_3M:
                continue
            sym = pref + suf
            try:
                v = busca(sym)
            except Exception as e:
                descartes.append("%s: %s" % (nome, str(e)[:40]))
                continue
            velho = ((prev.get(moeda) or {}).get(nome) or {}).get("value")
            if isinstance(velho, (int, float)) and abs(v - velho) > SALTO_MAX_PP:
                descartes.append("%s: salto %.2fpp vs anterior" % (nome, v - velho))
                continue
            pontos[nome] = {"value": v, "symbol": "TVC:" + sym}
            time.sleep(0.15)
        if "1y" in pontos and "2y" in pontos:
            pontos["slope_2y_1y"] = round(pontos["2y"]["value"] - pontos["1y"]["value"], 4)
        if "3m" in pontos and "2y" in pontos:
            pontos["slope_2y_3m"] = round(pontos["2y"]["value"] - pontos["3m"]["value"], 4)
        if descartes:
            pontos["descartes"] = descartes
        out[moeda] = pontos
    return out


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from update_fund import read_all_yields
    oficial = read_all_yields()
    ant = anterior()

    agora = datetime.now(timezone.utc)
    out = {"fetched_at": agora.isoformat(), "date": agora.date().isoformat(),
           "source": "TradingView TVC (scanner endpoint)", "yields": {}}

    # ---- 2 anos: comportamento original, intacto
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

    # ---- curto da curva: ADITIVO, nao alimenta o FUND
    print("\ncurto da curva (3m/1y/2y) — coleta apenas, nao altera o FUND:")
    out["curve"] = coleta_curva(ant)
    out["curve_note"] = ("coleta para o fator PATH (BIS WP 626). NAO alimenta o FUND. "
                         "AUD sem 3m no TVC.")
    for moeda in PREFIXO:
        c = out["curve"].get(moeda) or {}
        t = " ".join("%s %.3f" % (n, c[n]["value"]) for n, _ in TENORES if n in c)
        inc = c.get("slope_2y_1y")
        print("  %-4s %-32s  inclinacao 2y-1y %s%s"
              % (moeda, t, ("%+.3f" % inc) if inc is not None else "n/d",
                 ("   [%s]" % "; ".join(c["descartes"])) if c.get("descartes") else ""))

    DEST.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_curva = len([m for m in out["curve"] if "slope_2y_1y" in out["curve"][m]])
    print("\nnowcast: %d/8 moedas (2 anos) | %d/8 com inclinacao -> %s"
          % (len(out["yields"]), n_curva, DEST))


if __name__ == "__main__":
    main()
