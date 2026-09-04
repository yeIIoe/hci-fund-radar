# -*- coding: utf-8 -*-
"""GEOPOLITICA — o que o noticiario do mundo diz sobre cada moeda, medido, e o que isso
IMPLICA por regra declarada. Nao entra na conviccao ate ser medido.

O PEDIDO (Eduardo, 04/set)
    "informacao macro e informacao geopolitica, cruzadas, dando uma conviccao dos proximos
    juros devido a x, y e z motivos". A parte macro esta no sentimento.py. Esta e a parte
    geopolitica: uma camada de CONTEXTO por moeda, com intensidade medida e manchetes.

FONTE
    GDELT DOC 2.0 API — gratuita, sem chave, cobre o noticiario mundial com atualizacao de
    15 minutos. Limite de taxa agressivo (429 com duas chamadas seguidas; testado em 04/set):
    uma chamada a cada 6 s, com espera de 20 s no 429. Sao 2 chamadas por moeda + 2 de mundo.
    ⚠️ Ao contrario do calendario, aqui a JANELA importa mais que o instante: intensidade de
    3 dias contra a media de 14 dias.

O QUE SAI, por moeda
    conflito     volume de artigos com guerra/sancoes/misseis/cessar-fogo ligados ao pais,
                 3 dias, comparado a media diaria dos 14 dias anteriores (razao e z)
    energia      idem para petroleo/energia/tarifas/embargo — o canal que vira INFLACAO
    tom          tom medio do GDELT (negativo = noticiario ruim)
    manchetes    as 5 mais relevantes de cada tema, com fonte e hora
    implicacao   REGRA DECLARADA, nao medida:
                   choque de conflito -> risk-off: USD, CHF e JPY tendem a receber fluxo;
                                          AUD, NZD e CAD tendem a perder (FX, nao juro)
                   choque de energia  -> inflacao para importador liquido -> empurra APERTO;
                                          para exportador (CAD, NOK) o efeito e misto

🔴 O QUE ISTO NAO E
    Nao entra nas 4 dimensoes da conviccao. E a regra da casa: filtro novo passa por medicao
    antes de pontuar (o DXY como filtro foi reprovado nas 88 operacoes exatamente por ter
    sido assumido). Aqui a implicacao e mostrada ao lado, rotulada como regra, para o Eduardo
    julgar — e para virar hipotese testavel: "conflito z>2 muda o retorno de 20 dias das
    moedas de risco?".
"""
from __future__ import annotations

import datetime as dt
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "geopolitica.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
API = "https://api.gdeltproject.org/api/v2/doc/doc?"
CACHE_H = 3
PAUSA_S = 5
ORCAMENTO_S = 8 * 60          # a Action tem 15 min para a cadeia inteira; isto para em 8 e grava o que tem

PAIS = {
    "USD": '("United States" OR Washington OR "U.S.")',
    "EUR": '("euro area" OR eurozone OR "European Union" OR Germany OR France OR Brussels)',
    "GBP": '("United Kingdom" OR Britain OR "UK government" OR London)',
    "JPY": '(Japan OR Tokyo)',
    "AUD": '(Australia OR Canberra)',
    "NZD": '("New Zealand" OR Wellington)',
    "CAD": '(Canada OR Ottawa)',
    "CHF": '(Switzerland OR Swiss)',
}
TEMAS = {
    "conflito": '(war OR sanctions OR missile OR airstrike OR ceasefire OR "military strike" OR invasion)',
    "energia":  '("oil price" OR "crude oil" OR OPEC OR "energy prices" OR tariff OR tariffs OR embargo OR "trade war")',
}
# moedas de refugio e de risco — regra declarada, nao medida
REFUGIO = ("USD", "CHF", "JPY")
RISCO = ("AUD", "NZD", "CAD")
EXPORTADOR_ENERGIA = ("CAD",)


INICIO = time.time()


def estourou() -> bool:
    return (time.time() - INICIO) > ORCAMENTO_S


def gdelt(params: dict, tentativas: int = 2):
    u = API + urllib.parse.urlencode(params)
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                corpo = r.read().decode("utf-8", errors="replace")
            if not corpo.strip():
                return {}
            return json.loads(corpo)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tentativas - 1:
                time.sleep(15)
                continue
            raise
        except json.JSONDecodeError:
            return {}
    return {}


def volume(q: str) -> dict:
    """Volume diario dos ultimos 14 dias (timelinevol) -> intensidade dos 3 ultimos dias."""
    d = gdelt({"query": q, "mode": "timelinevol", "format": "json", "timespan": "14d"})
    serie = ((d.get("timeline") or [{}])[0].get("data") or [])
    vals = [float(p.get("value") or 0) for p in serie]
    if len(vals) < 6:
        return {"n": len(vals)}
    rec, base = vals[-3:], vals[:-3]
    m = sum(base) / len(base)
    sd = math.sqrt(sum((x - m) ** 2 for x in base) / max(1, len(base) - 1))
    media_rec = sum(rec) / 3.0
    return {"n": len(vals), "recente_3d": round(media_rec, 4), "base_14d": round(m, 4),
            "razao": round(media_rec / m, 2) if m > 0 else None,
            "z": round((media_rec - m) / sd, 2) if sd > 0 else None}


def tom(q: str):
    d = gdelt({"query": q, "mode": "timelinetone", "format": "json", "timespan": "7d"})
    serie = ((d.get("timeline") or [{}])[0].get("data") or [])
    vals = [float(p.get("value")) for p in serie if p.get("value") not in (None, "")]
    return round(sum(vals) / len(vals), 2) if vals else None


def manchetes(q: str, n: int = 5) -> list:
    d = gdelt({"query": q, "mode": "artlist", "maxrecords": n, "format": "json",
               "timespan": "3d", "sort": "hybridrel"})
    out = []
    for a in d.get("articles", [])[:n]:
        out.append({"titulo": (a.get("title") or "")[:140], "url": a.get("url"),
                    "fonte": a.get("domain"), "quando": a.get("seendate"),
                    "pais_fonte": a.get("sourcecountry")})
    return out


def implicacao(moeda: str, conf: dict, ener: dict) -> dict:
    zc = conf.get("z") if conf else None
    ze = ener.get("z") if ener else None
    out = {"regra": "declared rule, not measured — shown for judgement, not counted in conviction",
           "fx": None, "juro": None}
    if zc is not None and zc >= 1.5:
        if moeda in REFUGIO:
            out["fx"] = "risk-off: safe-haven flow tends to SUPPORT %s (rule)" % moeda
        elif moeda in RISCO:
            out["fx"] = "risk-off: risk currencies tend to LOSE — %s (rule)" % moeda
        else:
            out["fx"] = "risk-off: mixed for %s (rule)" % moeda
    if ze is not None and ze >= 1.5:
        if moeda in EXPORTADOR_ENERGIA:
            out["juro"] = "energy shock: exporter — terms of trade up, inflation up; mixed for the rate (rule)"
        else:
            out["juro"] = "energy shock: importer — inflation push, leans TIGHTENING (rule)"
    return out


def cache_vale(forcar: bool) -> bool:
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
    print("GEOPOLITICA — intensidade do noticiario por moeda (GDELT), regra declarada ao lado")
    print("=" * 88)
    if cache_vale(forcar):
        print("  leitura de menos de %d h ainda vale — use --forcar" % CACHE_H)
        return

    saida, erros = {}, []
    # o mundo primeiro: o pano de fundo que todas as moedas compartilham
    mundo = {}
    for tema, q in TEMAS.items():
        try:
            mundo[tema] = {"volume": volume(q + " sourcelang:english"), "manchetes": manchetes(q + " sourcelang:english")}
            time.sleep(PAUSA_S)
        except Exception as e:
            erros.append("mundo/%s: %s" % (tema, str(e)[:60]))
            time.sleep(PAUSA_S)
    print("  mundo: conflito z=%s · energia z=%s" % (
        (mundo.get("conflito") or {}).get("volume", {}).get("z"),
        (mundo.get("energia") or {}).get("volume", {}).get("z")))

    for moeda, qp in PAIS.items():
        if estourou():
            erros.append("orcamento de %d s estourado antes de %s — o resto fica para a proxima rodada" % (ORCAMENTO_S, moeda))
            break
        bloco = {"temas": {}, "tom": None}
        for tema, qt in TEMAS.items():
            q = "%s %s sourcelang:english" % (qt, qp)
            try:
                v = volume(q)
                time.sleep(PAUSA_S)
                # manchetes so do conflito (o tema que move); energia entra pelo volume
                mh = manchetes(q, 3) if tema == "conflito" else []
                if tema == "conflito":
                    time.sleep(PAUSA_S)
                bloco["temas"][tema] = {"volume": v, "manchetes": mh}
            except Exception as e:
                erros.append("%s/%s: %s" % (moeda, tema, str(e)[:60]))
                bloco["temas"][tema] = {"erro": str(e)[:80]}
                time.sleep(PAUSA_S)
        # tom: uma chamada por moeda; pulada quando o orcamento aperta
        if not estourou():
            try:
                bloco["tom"] = tom("%s sourcelang:english" % qp)
                time.sleep(PAUSA_S)
            except Exception as e:
                erros.append("%s/tom: %s" % (moeda, str(e)[:60]))
        conf = (bloco["temas"].get("conflito") or {}).get("volume") or {}
        ener = (bloco["temas"].get("energia") or {}).get("volume") or {}
        bloco["implicacao"] = implicacao(moeda, conf, ener)
        saida[moeda] = bloco
        print("  %-4s conflito z=%-6s razao=%-5s · energia z=%-6s razao=%-5s · tom=%-6s %s"
              % (moeda, conf.get("z"), conf.get("razao"), ener.get("z"), ener.get("razao"), bloco["tom"],
                 (bloco["implicacao"].get("fx") or bloco["implicacao"].get("juro") or "")[:48]))
        m0 = ((bloco["temas"].get("conflito") or {}).get("manchetes") or [])[:1]
        if m0:
            print("       • %s (%s)" % (m0[0]["titulo"][:90], m0[0]["fonte"]))

    if erros:
        print("  ! erros: %d — %s" % (len(erros), "; ".join(erros[:4])))
    if not saida or all(not (b["temas"].get("conflito") or {}).get("volume") for b in saida.values()):
        print("  !! GDELT nao respondeu nada util — arquivo anterior preservado")
        sys.exit(1)

    rel = {"gerado_em": agora.isoformat(),
           "fonte": "GDELT DOC 2.0 API (free, no key, 15-min updates); English-language sources",
           "metodo": "article volume for the last 3 days vs the daily mean of the 14-day window (ratio and z); "
                     "mean tone over 7 days; top headlines by hybrid relevance",
           "aviso": "CONTEXT layer. The implication is a declared rule (risk-off -> safe havens; energy shock -> "
                    "inflation push), not a measurement, and it is NOT counted in the conviction. Hypothesis to "
                    "test: does conflict z>=2 change 20-day returns of risk currencies?",
           "mundo": mundo, "moedas": saida, "erros": erros}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1, allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
