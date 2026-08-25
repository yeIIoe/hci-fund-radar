# -*- coding: utf-8 -*-
"""FUND D+0 POR MOEDA — qual PERNA esta esticada (25/ago/2026).

POR QUE EXISTE
--------------
A versao por PAR (fund_d0.py) dizia "AUDJPY esticado alem do juro" e nao dizia
QUAL das duas pernas. Com o JPY tendo sensibilidade +0,02 (praticamente nula) e o
AUD +0,23, o esticamento do AUDJPY quase certamente vem do AUD — mas o medidor de
par nao tinha como afirmar.

Aqui a conta e por MOEDA, contra uma CESTA, e nao contra uma unica contraparte:
    indice(c)  = media geometrica do preco de c em cada uma das outras 7
    esperado   = beta_c x (variacao do PROPRIO yield 2a de c)
    excesso    = variacao real do indice - esperado
E o par vira decomposicao:
    excesso(AB) ~= excesso(A) - excesso(B)

Duas vantagens sobre a versao por par:
  - o indice faz media sobre 7 pares, entao o ruido idiossincratico de um cruzado
    nao domina a leitura;
  - o EUR volta a ser mensuravel. Na versao por par ele era o numerario das
    series do BCE e ficava degenerado.

ANCORA (declarada): tanto o preco quanto o yield sao medidos contra o ULTIMO
FECHAMENTO OFICIAL de cada um. Os dois lados partem da mesma data, entao o delta
e consistente por construcao. Nao e exatamente a abertura das 19:00 da janela do
Eduardo — e o ancoradouro limpo disponivel sem dado intradiario historico.

⚠️ MEDIDOR, NAO SINAL. A relacao contemporanea esta medida. Que "esticado" preveja
reversao nas horas seguintes NAO FOI TESTADO.
"""
from __future__ import annotations
import io, csv, json, math, ssl, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MOEDAS = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"]
CAL = ROOT / "data" / "fund_d0_moeda.json"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

SIMB_Y = {"USD": "US02Y", "EUR": "DE02Y", "GBP": "GB02Y", "JPY": "JP02Y",
          "AUD": "AU02Y", "CAD": "CA02Y", "CHF": "CH02Y", "NZD": "NZ02Y"}
# preco: 7 pares do EUR bastam — deles sai qualquer cruzado
SIMB_FX = {"USD": "EURUSD", "GBP": "EURGBP", "JPY": "EURJPY", "AUD": "EURAUD",
           "CAD": "EURCAD", "CHF": "EURCHF", "NZD": "EURNZD"}
SESSAO = {"NZD": (21, 4), "AUD": (23, 6), "JPY": (0, 6), "EUR": (7, 16),
          "CHF": (7, 16), "GBP": (7, 16), "USD": (13, 21), "CAD": (13, 21)}


def tv(sym, campos="close"):
    url = ("https://scanner.tradingview.com/symbol?symbol=%s&fields=%s"
           % (sym.replace(":", "%3A"), campos))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def carrega_hist():
    serie = {"EUR": {}}
    for m in [x for x in MOEDAS if x != "EUR"]:
        d = {}
        with io.open(ROOT / "data" / "raw" / ("fx_ecb_%seur.csv" % m.lower()),
                     encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                v = (r.get("OBS_VALUE") or "").strip()
                t = (r.get("TIME_PERIOD") or "").strip()
                if v and t:
                    try:
                        d[t] = float(v)
                    except ValueError:
                        pass
        serie[m] = d
    datas = sorted(set.intersection(*[set(serie[m]) for m in serie if m != "EUR"]))
    for t in datas:
        serie["EUR"][t] = 1.0
    return serie, datas


def indice(serie, t, c):
    """preco de c contra a cesta = media geometrica de (serie[m]/serie[c])."""
    vs = []
    for m in MOEDAS:
        if m == c:
            continue
        a, b = serie[m].get(t), serie[c].get(t)
        if not a or not b:
            return None
        vs.append(a / b)
    return math.exp(sum(math.log(v) for v in vs) / len(vs))


def calibra():
    sys.path.insert(0, str(ROOT))
    from update_fund import read_all_yields
    serie, datas = carrega_hist()
    Y = read_all_yields()
    YS = {m: {d.isoformat(): v for d, v in (Y.get(m) or {}).items() if v is not None} for m in Y}
    out = {}
    for c in MOEDAS:
        s = []
        for t in datas:
            ix = indice(serie, t, c)
            y = YS.get(c, {}).get(t)
            if ix and y is not None:
                s.append((t, ix, y))
        if len(s) < 500:
            continue
        xs = [s[i][2] - s[i - 1][2] for i in range(1, len(s))]
        ys = [(s[i][1] / s[i - 1][1] - 1.0) * 100 for i in range(1, len(s))]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        syy = sum((y - my) ** 2 for y in ys)
        if sxx <= 0 or syy <= 0:
            continue
        r = sxy / math.sqrt(sxx * syy)
        out[c] = {"beta": round(sxy / sxx, 4), "r2": round(r * r, 4),
                  "corr": round(r, 4), "n": n}
    CAL.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("%-5s %10s %8s %8s %9s" % ("moeda", "beta %/pp", "corr", "R2", "n"))
    for c, v in sorted(out.items(), key=lambda kv: -kv[1]["r2"]):
        print("%-5s %+10.3f %+8.3f %8.3f %9d" % (c, v["beta"], v["corr"], v["r2"], v["n"]))
    print("\n-> %s" % CAL)
    return out


def frac(c, ini, agora):
    h0, h1 = SESSAO[c]
    horas, t = 0.0, ini
    while t < agora:
        h = t.hour
        if (h0 <= h < h1) if h0 < h1 else (h >= h0 or h < h1):
            horas += 1.0
        t += timedelta(hours=1)
    total = (h1 - h0) if h0 < h1 else (24 - h0 + h1)
    return min(1.0, horas / total)


def leitura(pares):
    if not CAL.exists():
        calibra()
    B = json.loads(CAL.read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT))
    from update_fund import read_all_yields
    serie, datas = carrega_hist()
    Y = read_all_yields()

    base_t = datas[-1]
    ancora_y = {}
    for m in MOEDAS:
        s = Y.get(m) or {}
        ds = [d for d, v in s.items() if v is not None]
        if ds:
            ancora_y[m] = s[max(ds)]

    vivo_y, vivo_fx = {}, {"EUR": 1.0}
    for m, sym in SIMB_Y.items():
        try:
            vivo_y[m] = float(tv("TVC:" + sym)["close"])
        except Exception:
            pass
        time.sleep(0.12)
    for m, sym in SIMB_FX.items():
        try:
            vivo_fx[m] = float(tv("FX_IDC:" + sym)["close"])
        except Exception:
            pass
        time.sleep(0.12)

    agora = datetime.now(timezone.utc)
    ini = agora.replace(hour=22, minute=0, second=0, microsecond=0)
    if agora.hour < 22:
        ini -= timedelta(days=1)

    exc, det = {}, {}
    for c in MOEDAS:
        cal = B.get(c)
        if not cal or c not in vivo_y or c not in ancora_y:
            continue
        try:
            ix0 = indice(serie, base_t, c)
            ix1 = indice(vivo_fx, None, c) if False else None
        except Exception:
            continue
        vs = []
        ok = True
        for m in MOEDAS:
            if m == c:
                continue
            a, b = vivo_fx.get(m), vivo_fx.get(c)
            if not a or not b:
                ok = False
                break
            vs.append(a / b)
        if not ok or ix0 is None:
            continue
        ix1 = math.exp(sum(math.log(v) for v in vs) / len(vs))
        real = (ix1 / ix0 - 1.0) * 100
        dy = vivo_y[c] - ancora_y[c]
        espe = cal["beta"] * dy
        exc[c] = real - espe
        det[c] = (dy, espe, real, cal["r2"], cal["corr"], frac(c, ini, agora))

    print("\n" + "=" * 100)
    print("FUND D+0 POR MOEDA — quem esta esticado em relacao ao PROPRIO juro")
    print("%s UTC-3 | ancora: fechamento oficial de %s"
          % ((agora - timedelta(hours=3)).strftime("%d/%m %H:%M"), base_t))
    print("=" * 100)
    print("%-5s %9s %10s %10s %10s %7s %6s  %s"
          % ("moeda", "dyield", "esperado", "real", "EXCESSO", "janela", "R2", "leitura"))
    for c in sorted(exc, key=lambda k: -abs(exc[k])):
        dy, espe, real, r2, cr, fr = det[c]
        if r2 < 0.02:
            txt = "SEM LEITURA (juro nao explica)"
        elif fr < 0.5:
            txt = "PARCIAL — sessao incompleta"
        elif abs(exc[c]) < 0.10:
            txt = "consistente com o juro"
        elif (exc[c] > 0):
            txt = "ESTICADO PARA CIMA alem do juro"
        else:
            txt = "ESTICADO PARA BAIXO alem do juro"
        print("%-5s %+9.3f %+10.3f %+10.3f %+10.3f %6.0f%% %6.2f  %s"
              % (c, dy, espe, real, exc[c], 100 * fr, r2, txt))

    if pares:
        print("\n" + "=" * 100)
        print("DECOMPOSICAO DO PAR — qual perna carrega o esticamento")
        print("=" * 100)
        for par in pares:
            a, b = par[:3], par[3:]
            if a not in exc or b not in exc:
                print("%-8s  sem leitura em uma das pernas" % par)
                continue
            e = exc[a] - exc[b]
            ta, tb = abs(exc[a]), abs(exc[b])
            dom = a if ta >= tb else b
            peso = 100 * max(ta, tb) / (ta + tb) if (ta + tb) else 0
            r2a, r2b = det[a][3], det[b][3]
            aviso = ""
            if det[dom][3] < 0.02:
                aviso = "  ⚠ a perna dominante e justamente a que o juro nao explica"
            print("%-8s excesso %+7.3f  =  %s %+7.3f  -  %s %+7.3f   -> %s carrega %.0f%%%s"
                  % (par, e, a, exc[a], b, exc[b], dom, peso, aviso))
            print("         R2: %s %.2f | %s %.2f" % (a, r2a, b, r2b))

    print("-" * 100)
    print("MEDIDOR, NAO SINAL. Que 'esticado' preveja reversao NAO FOI TESTADO.")


if __name__ == "__main__":
    if "--calibra" in sys.argv:
        calibra()
    else:
        alvo = [a for a in sys.argv[1:] if not a.startswith("-")]
        leitura(alvo or ["AUDJPY", "AUDNZD", "EURUSD", "USDJPY", "AUDCAD"])
