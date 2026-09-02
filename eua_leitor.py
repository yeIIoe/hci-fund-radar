# -*- coding: utf-8 -*-
"""LEITOR DOS ESTADOS UNIDOS — o dado do BLS e o comunicado do Fed, sem intermediario.

POR QUE COMECAR PELOS EUA
    E a unica moeda com as DUAS pontas funcionando, testado em 02/set/2026:
      · comunicado do Fed por RSS  -> HTTP 200, latencia medida de ~13 s
      · dado do BLS por API        -> HTTP 200, REQUEST_SUCCEEDED, sem chave
    ⚠️ O levantamento de ontem dizia que o BLS bloqueia robo. **Isso vale para o SITE, nao
    para a API.** Foi so testar. Duas moedas de fato bloqueiam automacao — RBA e RBNZ
    devolvem 403 — mas o dolar nao e uma delas.

E PORQUE E A LEITURA QUE SERVE MAIS INSTRUMENTOS
    Uma leitura do Fed alimenta os 7 pares com USD, mais **GC, NQ e ES**, que o Eduardo
    apontou: os tres tem ligacao estreita com o juro americano.
    Medido hoje, janelas SEM sobreposicao: **juro real de 10 anos x ouro = −0,684 em 60
    pregoes** (n=18, fora do ruido). E o mais forte que ja medimos em qualquer relacao macro
    deste projeto — mais forte que juro x cambio (+0,47 a +0,54).
    ⚠️ Mas so CONTEMPORANEO. A preditiva morre com janela nao sobreposta (60d −0,132, dentro
    do ruido). Ou seja: se soubermos para onde o juro real vai, temos a direcao do ouro. O
    juro real de ontem nao da o ouro de amanha.

O QUE ELE NAO FAZ
    Nao le o texto do comunicado — isso e a camada de interpretacao, que entra depois e nasce
    marcada como interpretacao. Aqui e so o mecanico: numero contra previsao, e o empurrao
    que a regra declara.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "eua_leitura.json")

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
FED_RSS = "https://www.federalreserve.gov/feeds/press_monetary.xml"

# Series do BLS, todas verificadas em 02/set/2026.
# `familia` liga cada uma a leitura de leitor_regras.py — peso e sinal vem de la, nao daqui.
SERIES = {
    "CUSR0000SA0":    {"nome": "CPI headline",          "familia": "inflacao_cheia",   "tipo": "indice"},
    "CUSR0000SA0L1E": {"nome": "CPI core",              "familia": "inflacao_nucleo",  "tipo": "indice"},
    "CES0000000001":  {"nome": "Nonfarm payrolls",      "familia": "emprego_criacao",  "tipo": "nivel_mil"},
    "LNS14000000":    {"nome": "Unemployment rate",      "familia": "desemprego",       "tipo": "taxa"},
    "CES0500000003":  {"nome": "Average hourly earnings","familia": "salarios",         "tipo": "indice"},
    "LNS11300000":    {"nome": "Participation rate",     "familia": None,               "tipo": "taxa"},
}

MES = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"], 1)}


def bls(series: list, ini: int, fim: int) -> dict:
    """Um POST com todas as series — o BLS aceita lote, e sem chave sao 25 chamadas/dia."""
    corpo = json.dumps({"seriesid": series, "startyear": str(ini), "endyear": str(fim)}).encode()
    req = urllib.request.Request(BLS_API, data=corpo,
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError("BLS recusou: %s" % d.get("message"))
    for m in (d.get("message") or []):
        print("  ! BLS: %s" % m)
    return {s["seriesID"]: s.get("data", []) for s in d.get("Results", {}).get("series", [])}


def serie_ordenada(dados: list) -> list:
    """Do mais ANTIGO para o mais novo, com a data resolvida."""
    out = []
    for x in dados:
        m = MES.get(x.get("periodName"))
        if not m:
            continue
        try:
            out.append((dt.date(int(x["year"]), m, 1), float(x["value"])))
        except (ValueError, KeyError):
            continue
    return sorted(out)


def variacoes(pontos: list, tipo: str) -> dict:
    """m/m e a/a. Indice vira percentual; taxa e nivel ficam em diferenca absoluta."""
    if len(pontos) < 2:
        return {}
    (_, atual) = pontos[-1]
    (_, ant) = pontos[-2]
    doze = None
    if len(pontos) >= 13:
        doze = pontos[-13][1]

    if tipo == "indice":
        mm = 100 * (atual / ant - 1) if ant else None
        aa = 100 * (atual / doze - 1) if doze else None
        un = "%"
    elif tipo == "nivel_mil":
        mm = atual - ant                      # variacao em MILHARES de vagas
        aa = atual - doze if doze else None
        un = "mil"
    else:                                     # taxa
        mm = atual - ant
        aa = atual - doze if doze else None
        un = "pp"
    return {"mm": round(mm, 3) if mm is not None else None,
            "aa": round(aa, 3) if aa is not None else None, "unidade": un}


def fed_rss() -> dict:
    """Ultimo comunicado de politica monetaria do Fed. Fonte primaria, sem intermediario."""
    try:
        req = urllib.request.Request(FED_RSS, headers={"User-Agent": "HCI-MacroDirection/1.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            xml = r.read().decode("utf-8", errors="replace")
            hora_srv = r.headers.get("Last-Modified")
    except Exception as e:
        return {"erro": str(e)}
    itens = re.findall(r"<item>(.*?)</item>", xml, re.S)
    saida = []
    for it in itens[:8]:
        def campo(t):
            m = re.search(r"<%s>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (t, t), it, re.S)
            return m.group(1).strip() if m else None
        saida.append({"titulo": campo("title"), "link": campo("link"),
                      "publicado": campo("pubDate")})
    return {"ultimos": saida, "last_modified_do_servidor": hora_srv, "total_no_feed": len(itens)}


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    ano = agora.year
    print("=" * 84)
    print("LEITOR DOS ESTADOS UNIDOS")
    print("=" * 84)

    try:
        cru = bls(list(SERIES), ano - 2, ano)
    except Exception as e:
        print("  ❌ BLS falhou: %s" % e)
        return

    leitura = {}
    print()
    print("  %-28s %12s %10s %10s  %s" % ("indicador", "ultimo", "m/m", "a/a", "referencia"))
    print("  " + "-" * 78)
    for sid, meta in SERIES.items():
        pontos = serie_ordenada(cru.get(sid, []))
        if not pontos:
            print("  %-28s  sem dado" % meta["nome"])
            continue
        v = variacoes(pontos, meta["tipo"])
        d, val = pontos[-1]
        leitura[sid] = {
            "nome": meta["nome"], "familia": meta["familia"],
            "referencia": d.isoformat()[:7], "valor": val, **v,
            "n_obs": len(pontos),
        }
        print("  %-28s %12.3f %9s %9s  %s"
              % (meta["nome"], val,
                 ("%+.2f%s" % (v["mm"], v["unidade"])) if v.get("mm") is not None else "—",
                 ("%+.2f%s" % (v["aa"], v["unidade"])) if v.get("aa") is not None else "—",
                 d.isoformat()[:7]))

    # ⚠️ O BLS publica com defasagem de ~2 semanas. O mes de referencia NAO e o mes corrente,
    # e confundir os dois faria o leitor tratar dado velho como recem-saido.
    refs = {x["referencia"] for x in leitura.values()}
    print()
    print("  mes de referencia dos dados: %s" % ", ".join(sorted(refs)))
    atraso = None
    if refs:
        ref = max(refs)
        y, m = (int(x) for x in ref.split("-"))
        atraso = (agora.year - y) * 12 + (agora.month - m)
        print("  ⚠️ defasagem: %d mes(es) atras do mes corrente — e o normal do BLS, nao um erro"
              % atraso)

    fed = fed_rss()
    print()
    print("  COMUNICADOS DO FED (feed de politica monetaria)")
    if fed.get("erro"):
        print("    ❌ %s" % fed["erro"])
    else:
        print("    %d itens no feed · Last-Modified do servidor: %s"
              % (fed["total_no_feed"], fed.get("last_modified_do_servidor")))
        for x in fed["ultimos"][:4]:
            print("      %s  %s" % ((x.get("publicado") or "?")[:25], (x.get("titulo") or "")[:56]))

    rel = {
        "gerado_em": agora.isoformat(),
        "fonte_dado": "BLS public API v2 (sem chave)",
        "fonte_comunicado": FED_RSS,
        "defasagem_meses": atraso,
        "aviso": "leitura MECANICA: numero e variacao. O texto do comunicado nao e "
                 "interpretado aqui — essa camada entra depois e nasce marcada como "
                 "interpretacao, valendo so para frente.",
        "serve_tambem": ["GC", "NQ", "ES", "todos os pares com USD"],
        "nota_ouro": "juro real 10a x ouro: -0,684 em 60 pregoes, contemporaneo, janelas sem "
                     "sobreposicao (n=18). A preditiva morre no ruido (-0,132).",
        "indicadores": leitura,
        "fed": fed,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
