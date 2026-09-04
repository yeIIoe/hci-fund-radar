# -*- coding: utf-8 -*-
"""CORRELACAO JURO AMERICANO x FUTUROS — NQ/MNQ, ES/MES, ouro (GC/MGC). Medida, nao alegada.

O PEDIDO
    Eduardo (02 e 04/set): "coloque a correlacao do US com os futuros NQ/MNQ e ES/MES e
    GOLD/MGC". Ate agora so o ouro estava medido em casa (juro real 10a x ouro = -0,684
    contemporaneo em 60 pregoes). Aqui os tres saem com a MESMA regua, e a versao preditiva
    sai do lado — porque a diferenca entre as duas e a licao inteira deste projeto:
    o juro descreve o mes, nao antecipa a vela.

FONTES (gratis, sem chave, testadas em 04/set/2026)
    precos    Yahoo chart API, futuros continuos diarios, 5 anos: NQ=F ES=F GC=F e os micros
              MNQ=F MES=F MGC=F (os micros sao o mesmo preco — e isto tambem e medido aqui)
    nominal   Fed H.15, 2 e 10 anos (constant maturity)
    real      Tesouro americano, curva real diaria (TIPS), 10 anos

AS QUATRO MEDIDAS, por instrumento x serie de juro
    contemp_1d   corr(variacao do juro no dia, retorno do dia)               n ~ 1.200
    contemp_20d  corr em blocos de 20 pregoes SEM sobreposicao                n ~ 60
    contemp_60d  corr em blocos de 60 pregoes SEM sobreposicao                n ~ 20
    pred_1d      corr(variacao do juro hoje, retorno de AMANHA)
    pred_5d      corr(juro nos 5 dias, retorno dos 5 dias SEGUINTES), blocos sem sobreposicao
    Blocos sem sobreposicao de proposito: janelas sobrepostas inflam o n e foi assim que um
    achado anterior evaporou. Sinal esperado: NEGATIVO (juro sobe -> ativo cai).

CACHE
    Dado diario. Roda no maximo uma vez a cada 20 h; --forcar ignora.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import math
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "correlacao_juros.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
CACHE_H = 20

INSTR = {"XAUUSD": ("GC=F", "MGC=F", "Gold"), "NQ": ("NQ=F", "MNQ=F", "Nasdaq 100"),
         "ES": ("ES=F", "MES=F", "S&P 500")}
H15 = ("https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78"
       "&from=%s&to=%s&filetype=csv&label=include&layout=seriescolumn")
TESOURO_REAL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                "daily-treasury-rates.csv/%d/all?type=daily_treasury_real_yield_curve"
                "&field_tdr_date_value=%d&page&_format=csv")


def busca(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def yahoo(sym):
    u = "https://query1.finance.yahoo.com/v8/finance/chart/%s?range=5y&interval=1d" % sym.replace("=", "%3D")
    d = json.loads(busca(u))
    r = d["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(ts, cl):
        if c is not None:
            out[dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()] = float(c)
    return out


def h15(ini: dt.date, fim: dt.date):
    x = busca(H15 % (ini.strftime("%m/%d/%Y"), fim.strftime("%m/%d/%Y")))
    rows = list(csv.reader(io.StringIO(x)))
    ids = next(r for r in rows[:8] if r and "Unique Identifier" in r[0])
    col = {n: i for i, n in enumerate(ids)}
    c2, c10 = col.get("H15/H15/RIFLGFCY02_N.B"), col.get("H15/H15/RIFLGFCY10_N.B")
    y2, y10 = {}, {}
    for r in rows:
        if not r or not r[0][:4].isdigit():
            continue
        try:
            if c2 is not None and r[c2] not in ("", "ND"):
                y2[r[0]] = float(r[c2])
            if c10 is not None and r[c10] not in ("", "ND"):
                y10[r[0]] = float(r[c10])
        except ValueError:
            continue
    return y2, y10


def tesouro_real(anos):
    out = {}
    for ano in anos:
        try:
            rows = list(csv.reader(io.StringIO(busca(TESOURO_REAL % (ano, ano)))))
        except Exception as e:
            print("  ! Tesouro %d: %s" % (ano, e))
            continue
        if not rows:
            continue
        cab = [c.strip().upper() for c in rows[0]]
        try:
            ci = cab.index("10 YR")
        except ValueError:
            continue
        for r in rows[1:]:
            try:
                d = dt.datetime.strptime(r[0].strip(), "%m/%d/%Y").date().isoformat()
                out[d] = float(r[ci])
            except (ValueError, IndexError):
                continue
    return out


# ------------------------------------------------------------------ estatistica, sem numpy

def corr(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def blocos(dy, r, k):
    """Soma em blocos de k dias SEM sobreposicao: (Δjuro do bloco, retorno do bloco)."""
    xs, ys = [], []
    for i in range(0, len(dy) - k + 1, k):
        xs.append(sum(dy[i:i + k]))
        ys.append(sum(r[i:i + k]))
    return xs, ys


def blocos_pred(dy, r, k):
    """Juro nos k dias -> retorno nos k dias SEGUINTES, blocos sem sobreposicao."""
    xs, ys = [], []
    for i in range(0, len(dy) - 2 * k + 1, 2 * k):
        xs.append(sum(dy[i:i + k]))
        ys.append(sum(r[i + k:i + 2 * k]))
    return xs, ys


def medidas(precos, juro, rotulo):
    datas = sorted(set(precos) & set(juro))
    if len(datas) < 100:
        return None
    dy, r = [], []
    for a, b in zip(datas, datas[1:]):
        dy.append((juro[b] - juro[a]) * 100.0)           # bp
        r.append(math.log(precos[b] / precos[a]) * 100.0)  # %
    x20, y20 = blocos(dy, r, 20)
    x60, y60 = blocos(dy, r, 60)
    xp5, yp5 = blocos_pred(dy, r, 5)
    acerto20 = (sum(1 for x, y in zip(x20, y20) if x != 0 and (x > 0) == (y < 0)) / len(x20)) if x20 else None
    return {
        "rotulo": rotulo, "n_dias": len(dy), "de": datas[0], "ate": datas[-1],
        "contemp_1d": round(corr(dy, r), 3),
        "contemp_20d": round(corr(x20, y20), 3) if corr(x20, y20) is not None else None, "n_20d": len(x20),
        "contemp_60d": round(corr(x60, y60), 3) if corr(x60, y60) is not None else None, "n_60d": len(x60),
        "pred_1d": round(corr(dy[:-1], r[1:]), 3),
        "pred_5d": round(corr(xp5, yp5), 3) if corr(xp5, yp5) is not None else None, "n_5d": len(xp5),
        "sinal_oposto_20d_pct": round(100 * acerto20) if acerto20 is not None else None,
    }


def cache_vale(forcar):
    if forcar or not os.path.exists(SAIDA):
        return False
    try:
        g = dt.datetime.fromisoformat(json.load(io.open(SAIDA, encoding="utf-8"))["gerado_em"])
        return (dt.datetime.now(dt.timezone.utc) - g).total_seconds() < CACHE_H * 3600
    except Exception:
        return False


def main():
    forcar = "--forcar" in sys.argv
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 88)
    print("CORRELACAO JURO AMERICANO x FUTUROS (NQ, ES, ouro) — medida em casa")
    print("=" * 88)
    if cache_vale(forcar):
        print("  leitura de menos de %d h ainda vale (dado diario) — use --forcar" % CACHE_H)
        return

    hoje = agora.date()
    ini = hoje - dt.timedelta(days=5 * 365 + 10)
    try:
        y2, y10 = h15(ini, hoje)
        print("  H.15: 2a %d obs · 10a %d obs (%s -> %s)" % (len(y2), len(y10), min(y10), max(y10)))
    except Exception as e:
        print("  X H.15 falhou: %s" % e)
        sys.exit(1)
    real10 = tesouro_real(range(ini.year, hoje.year + 1))
    print("  Tesouro real 10a: %d obs%s" % (len(real10), "" if real10 else "  (ausente — sai so o nominal)"))

    series_juro = {"nominal2y": (y2, "US 2-year nominal"), "nominal10y": (y10, "US 10-year nominal")}
    if real10:
        series_juro["real10y"] = (real10, "US 10-year real (TIPS)")

    saida = {}
    for inst, (grande, micro, nome) in INSTR.items():
        try:
            pg = yahoo(grande)
            pm = yahoo(micro)
        except Exception as e:
            print("  ! %s: Yahoo falhou (%s)" % (inst, e))
            continue
        # micro x grande: o mesmo preco? medido, nao assumido
        dcom = sorted(set(pg) & set(pm))
        rg = [math.log(pg[b] / pg[a]) for a, b in zip(dcom, dcom[1:])]
        rm = [math.log(pm[b] / pm[a]) for a, b in zip(dcom, dcom[1:])]
        c_micro = corr(rg, rm)
        series = {}
        for k, (juro, rot) in series_juro.items():
            m = medidas(pg, juro, rot)
            if m:
                series[k] = m
        saida[inst] = {"nome": nome, "simbolo_grande": grande, "simbolo_micro": micro,
                       "micro_vs_grande_corr": round(c_micro, 4) if c_micro is not None else None,
                       "ultimo_preco": pg[max(pg)], "series": series}
        print()
        print("  %s (%s; micro %s tem corr %.4f com o grande, n=%d dias)"
              % (nome, grande, micro, c_micro or 0, len(rg)))
        print("    %-24s %8s %9s %9s %9s %9s  %s" % ("juro", "1d", "20d", "60d", "pred1d", "pred5d", "sinal oposto 20d"))
        for k, m in series.items():
            print("    %-24s %8s %9s %9s %9s %9s  %s%%"
                  % (m["rotulo"], m["contemp_1d"], m["contemp_20d"], m["contemp_60d"],
                     m["pred_1d"], m["pred_5d"], m["sinal_oposto_20d_pct"]))

    rel = {
        "gerado_em": agora.isoformat(),
        "fontes": {"precos": "Yahoo chart API, futuros continuos diarios, 5 anos",
                   "nominal": "Fed H.15 constant maturity 2y/10y",
                   "real": "US Treasury daily real yield curve 10y (TIPS)" if real10 else "indisponivel nesta rodada"},
        "metodo": "Pearson entre variacao do juro (bp) e retorno log (%). Blocos de 20 e 60 pregoes SEM "
                  "sobreposicao. Preditiva = juro hoje vs retorno de amanha, e juro em 5 dias vs os 5 "
                  "dias seguintes (blocos sem sobreposicao). Sinal esperado: negativo.",
        "nota": "contemporaneous columns describe the same window; the predictive columns are what an "
                "entry would need — and they sit inside noise. Rates describe the month, not the candle.",
        "instrumentos": saida,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1, allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
