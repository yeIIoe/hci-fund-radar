# -*- coding: utf-8 -*-
"""FUND D+0 — medidor de suporte de juro para GESTAO da operacao (25/ago/2026).

O QUE ELE RESPONDE
------------------
"O movimento que o par ja fez hoje esta sustentado pelo juro, ou nao?"

Nao e previsao. E COMPARACAO entre duas coisas conhecidas agora:
  esperado = beta_do_par x (variacao do spread 2a desde a abertura da janela)
  real     = variacao do preco desde a abertura da janela
Se o preco andou MUITO MAIS que o juro justifica, o movimento e de fluxo e a
literatura de reversao diz que volta. Se andou MENOS, ha folga. Se andou CONTRA,
a premissa da tese morreu.

⚠️⚠️ ISTO E UM MEDIDOR, NAO UM SINAL. A relacao contemporanea esta MEDIDA
(147.590 pares-dia). Se "esticado em relacao ao juro" preve alguma coisa nas horas
seguintes NUNCA FOI TESTADO. Usar para parcial ou stop e HIPOTESE — precisa de
PREREG e de amostra antes de virar regra.

TRES TRAVAS DE HONESTIDADE, EMBUTIDAS
-------------------------------------
1. ASSINCRONIA. Medido em 25/ago as 06:59 UTC: EUR e GBP se moviam, as outras 6
   estavam congeladas. Nao existe instante com as 8 vivas. Por isso o medidor
   informa QUANTO da janela cada perna ja negociou, e marca leitura parcial.
2. SENSIBILIDADE POR MOEDA (medido no nosso dado, 2022+, corr do proprio yield
   com o indice da moeda): USD +0,47 | CAD +0,42 | AUD +0,23 | NZD +0,13 |
   JPY +0,02 | GBP -0,09 | CHF -0,12. Em par de JPY, GBP ou CHF o instrumento
   nao explica nada — o medidor DIZ ISSO em vez de inventar numero.
3. O beta e calibrado no historico e reportado com o R2 dele. Beta sem R2 e chute
   com casas decimais.
"""
from __future__ import annotations
import io, csv, json, math, os, ssl, sys, time, urllib.request
from datetime import datetime, timedelta, timezone, date
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MOEDAS = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"]
CAL_BETA = ROOT / "data" / "fund_d0_beta.json"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# sensibilidade medida no nosso dado, 2022+ (corr do proprio yield 2a com o
# indice da moeda, H=20). EUR nao e mensuravel: e o numerario das series do BCE.
SENS = {"USD": 0.47, "CAD": 0.42, "AUD": 0.23, "NZD": 0.13,
        "JPY": 0.02, "GBP": -0.09, "CHF": -0.12, "EUR": None}

# sessao do mercado de juros de cada moeda, em UTC (aproximado, para medir
# QUANTO da janela cada perna ja negociou)
SESSAO = {"NZD": (21, 4), "AUD": (23, 6), "JPY": (0, 6), "EUR": (7, 16),
          "CHF": (7, 16), "GBP": (7, 16), "USD": (13, 21), "CAD": (13, 21)}

SIMB_Y = {"USD": "US02Y", "EUR": "DE02Y", "GBP": "GB02Y", "JPY": "JP02Y",
          "AUD": "AU02Y", "CAD": "CA02Y", "CHF": "CH02Y", "NZD": "NZ02Y"}


def tv(sym, campos="close"):
    url = ("https://scanner.tradingview.com/symbol?symbol=%s&fields=%s"
           % (sym.replace(":", "%3A"), campos))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))


# ============================================================== CALIBRACAO
def calibra():
    """beta de 1 dia por par: quantos % de preco por 1 ponto percentual de spread."""
    sys.path.insert(0, str(ROOT))
    from update_fund import read_all_yields
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
    Y = read_all_yields()
    YS = {m: {d.isoformat(): v for d, v in (Y.get(m) or {}).items() if v is not None} for m in Y}

    out = {}
    for a, b in combinations(MOEDAS, 2):
        par = a + b
        s = []
        for t in datas:
            pa, pb = serie[a].get(t), serie[b].get(t)
            ya, yb = YS.get(a, {}).get(t), YS.get(b, {}).get(t)
            if pa and pb and ya is not None and yb is not None:
                s.append((t, pb / pa, ya - yb))
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
        beta = sxy / sxx
        r = sxy / math.sqrt(sxx * syy)
        out[par] = {"beta_pct_por_pp": round(beta, 4), "r2": round(r * r, 4),
                    "corr": round(r, 4), "n": n}
    CAL_BETA.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("calibrado: %d pares -> %s" % (len(out), CAL_BETA))
    piores = sorted(out.items(), key=lambda kv: kv[1]["r2"])
    print("\nmenor R2 (o medidor nao tem o que dizer nestes):")
    for p, v in piores[:6]:
        print("   %-8s beta %+7.3f %%/pp   R2 %5.3f" % (p, v["beta_pct_por_pp"], v["r2"]))
    print("maior R2:")
    for p, v in sorted(out.items(), key=lambda kv: -kv[1]["r2"])[:6]:
        print("   %-8s beta %+7.3f %%/pp   R2 %5.3f" % (p, v["beta_pct_por_pp"], v["r2"]))
    return out


# ============================================================== LEITURA AO VIVO
def fracao_negociada(moeda, ini_utc, agora_utc):
    """Quanto da sessao daquela moeda ja aconteceu dentro da janela."""
    h0, h1 = SESSAO[moeda]
    horas = 0.0
    t = ini_utc
    while t < agora_utc:
        h = t.hour
        dentro = (h0 <= h < h1) if h0 < h1 else (h >= h0 or h < h1)
        if dentro:
            horas += 1.0
        t += timedelta(hours=1)
    total = (h1 - h0) if h0 < h1 else (24 - h0 + h1)
    return min(1.0, horas / total)


def leitura(pares):
    if not CAL_BETA.exists():
        print("sem calibracao — rodando primeiro")
        calibra()
    BET = json.loads(CAL_BETA.read_text(encoding="utf-8"))

    sys.path.insert(0, str(ROOT))
    from update_fund import read_all_yields
    Y = read_all_yields()
    ult = {}
    for m in MOEDAS:
        s = Y.get(m) or {}
        ds = [d for d, v in s.items() if v is not None]
        if ds:
            ult[m] = (max(ds), s[max(ds)])

    agora = datetime.now(timezone.utc)
    # a janela abre as 19:00 UTC-3 = 22:00 UTC do dia anterior
    ini = (agora - timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
    if agora.hour >= 22:
        ini = agora.replace(hour=22, minute=0, second=0, microsecond=0)

    vivo = {}
    for m, sym in SIMB_Y.items():
        try:
            vivo[m] = float(tv("TVC:" + sym)["close"])
        except Exception as e:
            print("  %s: yield ao vivo falhou (%s)" % (m, str(e)[:30]))
        time.sleep(0.15)

    print("\n" + "=" * 104)
    print("FUND D+0 — suporte de juro do movimento de HOJE   (%s UTC-3)"
          % (agora - timedelta(hours=3)).strftime("%d/%m %H:%M"))
    print("janela desde %s UTC-3" % (ini - timedelta(hours=3)).strftime("%d/%m %H:%M"))
    print("=" * 104)
    print("%-8s %9s %9s %9s %9s %7s %-22s %s"
          % ("par", "dspread", "esperado", "real", "excesso", "janela", "leitura", "confianca"))

    for par in pares:
        a, b = par[:3], par[3:]
        if a not in vivo or b not in vivo or a not in ult or b not in ult:
            print("%-8s  sem dado" % par)
            continue
        cal = BET.get(par) or BET.get(b + a)
        invertido = par not in BET
        if not cal:
            print("%-8s  sem calibracao" % par)
            continue
        dsp = (vivo[a] - vivo[b]) - (ult[a][1] - ult[b][1])
        beta = cal["beta_pct_por_pp"] * (-1 if invertido else 1)
        esperado = beta * dsp
        try:
            px = float(tv("FX_IDC:" + par)["close"])
            ab = float(tv("FX_IDC:" + par, "close,open")["open"])
            real = (px / ab - 1.0) * 100
        except Exception:
            real = float("nan")
        exc = real - esperado
        fr = min(fracao_negociada(a, ini, agora), fracao_negociada(b, ini, agora))
        sa, sb = SENS.get(a), SENS.get(b)
        forte = [x for x in (sa, sb) if x is not None and abs(x) >= 0.20]
        if cal["r2"] < 0.02 or not forte:
            conf, txt = "SEM LEITURA", "instrumento nao explica este par"
        elif fr < 0.5:
            conf, txt = "PARCIAL", "janela incompleta"
        elif abs(exc) < 0.10:
            conf, txt = "ok", "movimento consistente com o juro"
        elif (exc > 0) == (real > 0):
            conf, txt = "ok", "ESTICADO alem do juro (fluxo)"
        else:
            conf, txt = "ok", "aquem do juro (folga)"
        print("%-8s %+9.3f %+9.3f %+9.3f %+9.3f %6.0f%% %-22s %s (R2 %.2f)"
              % (par, dsp, esperado, real, exc, 100 * fr, txt, conf, cal["r2"]))

    print("-" * 104)
    print("MEDIDOR, NAO SINAL. Que 'esticado' preveja reversao nas horas seguintes")
    print("NUNCA FOI TESTADO. Usar para parcial/stop exige PREREG e amostra.")


if __name__ == "__main__":
    if "--calibra" in sys.argv:
        calibra()
    else:
        alvo = [a for a in sys.argv[1:] if not a.startswith("-")]
        leitura(alvo or ["EURUSD", "USDJPY", "AUDCAD", "NZDCAD", "EURAUD", "CADJPY", "CHFJPY"])
