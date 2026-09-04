# -*- coding: utf-8 -*-
"""DISCURSOS DO FED — a camada de TEXTO que o calendario de numeros nao le.

O CASO QUE MOTIVOU (03/set/2026, 08:30 ET)
    Nada de numero fora da linha nesse minuto: claims 206 vs 205, custo unitario 1,2 vs 1,3,
    produtividade 1,4 = 1,4. Mas no MESMO minuto saiu um discurso do Waller — e o texto dizia
    "I would be inclined to support holding the target" e "it may be appropriate to raise the
    policy rate when the FOMC meets on September 15 and 16". Isso e o evento do minuto, e o
    calendario so tinha "Fed's Waller speech" com actual=None.
    Um discurso NAO tem numero. O que ele tem e a FRASE de postura. Este modulo extrai a frase.

O QUE ELE FAZ — e o que ele NAO faz
    FAZ:  busca os discursos e o ultimo comunicado direto do Fed (RSS + pagina), separa em
          frases e guarda as que carregam postura de politica ("I would", "appropriate to",
          "hold", "raise", "cut"...). Conta marcadores hawkish e dovish. E EXTRACAO mecanica.
    NAO:  nao "entende" o discurso. A contagem de palavras e um indice grosseiro, rotulado como
          tal na saida. A camada de interpretacao de verdade (um modelo lendo o texto) entra
          depois e nasce marcada como interpretacao, valendo so para frente.

    ⚠️ Vies conhecido da contagem: "hold" aparece em "holding the target" (hawkish) e em
    "households" (nada). Por isso os marcadores sao expressoes, nao palavras soltas, e a
    lista fica AQUI em cima, visivel, para ser corrigida quando errar.
"""
from __future__ import annotations

import datetime as dt
import html as H
import io
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "fed_discursos.json")

RSS_DISCURSOS = "https://www.federalreserve.gov/feeds/speeches.xml"
RSS_POLITICA = "https://www.federalreserve.gov/feeds/press_monetary.xml"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
DIAS = 21          # janela de discursos que interessa ao proximo FOMC
MAX_ITENS = 6

# Expressoes, nunca palavras soltas. Postura, nao descricao da economia.
HAWKISH = ["raise the policy rate", "raise rates", "rate increase", "hike", "holding the target",
           "hold the target", "keep the policy rate", "remain restrictive", "restrictive for longer",
           "premature to", "upside risks to inflation", "inflation remains too high",
           "not yet time", "patient before", "tighten"]
DOVISH = ["cut the policy rate", "lower the policy rate", "reduce the policy rate", "rate cut",
          "cut rates", "cutting rates", "ease policy", "easing policy", "appropriate to reduce",
          "downside risks to employment", "labor market is weakening", "labor market has weakened",
          "further softening", "insurance cut", "move toward neutral", "less restrictive"]
# Frases em primeira pessoa com verbo de postura — o que o proprio membro diz que fara
POSTURA = ["i would", "i believe", "i expect", "i support", "i favor", "inclined to",
           "it may be appropriate", "it would be appropriate", "appropriate to", "my view",
           "i think the committee", "we should", "the committee should"]


def busca(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


def itens_rss(xml: str) -> list:
    out = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def campo(t):
            m = re.search(r"<%s>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (t, t), it, re.S)
            return H.unescape(m.group(1).strip()) if m else None
        out.append({"titulo": campo("title"), "link": campo("link"), "publicado": campo("pubDate")})
    return out


def data_de(pub: str):
    for f in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y"):
        try:
            return dt.datetime.strptime(pub.strip(), f).date()
        except (ValueError, AttributeError):
            continue
    return None


def texto_da_pagina(html: str) -> str:
    """O corpo do discurso fica na coluna principal do site do Fed. Cai para a pagina toda."""
    m = re.search(r'<div[^>]+class="col-xs-12 col-sm-8 col-md-8"[^>]*>(.*?)<div[^>]+class="col-xs-12 col-sm-4',
                  html, re.S)
    corpo = m.group(1) if m else html
    corpo = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", corpo, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", corpo)
    return H.unescape(re.sub(r"\s+", " ", t)).strip()


def frases_de_postura(texto: str) -> dict:
    frases = re.split(r"(?<=[.!?])\s+", texto)
    chave, hawk, dove = [], 0, 0
    for f in frases:
        fl = f.lower()
        if not (40 < len(f) < 420):
            continue
        h = sum(1 for k in HAWKISH if k in fl)
        d = sum(1 for k in DOVISH if k in fl)
        p = any(k in fl for k in POSTURA)
        hawk += h
        dove += d
        if p and (h or d or "policy rate" in fl or "federal funds" in fl or "fomc meets" in fl):
            chave.append({"frase": f.strip(), "hawkish": h, "dovish": d})
    # as frases de postura com marcador vem primeiro; depois as demais, na ordem do texto
    chave.sort(key=lambda x: -(x["hawkish"] + x["dovish"]))
    lean = "hawkish" if hawk > dove else "dovish" if dove > hawk else "mixed"
    return {"frases": chave[:5], "marcadores_hawkish": hawk, "marcadores_dovish": dove,
            "inclinacao_por_contagem": lean if (hawk or dove) else "none"}


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 84)
    print("DISCURSOS DO FED — extracao de frases de postura")
    print("=" * 84)
    saida = []
    for fonte, url, tipo in (("discursos", RSS_DISCURSOS, "speech"),
                             ("politica", RSS_POLITICA, "statement")):
        try:
            itens = itens_rss(busca(url))
        except Exception as e:
            print("  ! %s: %s" % (fonte, e))
            continue
        for it in itens:
            d = data_de(it.get("publicado") or "")
            if not d or (agora.date() - d).days > DIAS:
                continue
            if tipo == "statement" and not re.search(r"FOMC statement", it.get("titulo") or "", re.I):
                continue
            if not it.get("link"):
                continue
            try:
                txt = texto_da_pagina(busca(it["link"]))
            except Exception as e:
                print("  ! %s: %s" % (it["link"], e))
                continue
            titulo = it.get("titulo") or ""
            orador = titulo.split(",")[0].strip() if tipo == "speech" and "," in titulo else \
                     ("FOMC" if tipo == "statement" else titulo[:30])
            ext = frases_de_postura(txt)
            saida.append({"tipo": tipo, "data": d.isoformat(), "orador": orador,
                          "titulo": titulo, "link": it["link"], "caracteres": len(txt), **ext})
            if len([x for x in saida if x["tipo"] == tipo]) >= MAX_ITENS:
                break

    saida.sort(key=lambda x: x["data"], reverse=True)

    # Nada veio? Entao o Fed nao respondeu (ou a janela esta vazia). Gravar itens=[] com
    # carimbo novo apagaria as falas boas de ontem e o site mostraria "nothing said" com data
    # de hoje — revisao de 03/set. Sai com erro e preserva o arquivo anterior.
    if not saida:
        anterior = None
        try:
            anterior = json.load(io.open(SAIDA, encoding="utf-8"))
        except Exception:
            pass
        if anterior and anterior.get("itens"):
            print("  !! nenhuma fala coletada nesta rodada — arquivo anterior PRESERVADO "
                  "(%d itens de %s)" % (len(anterior["itens"]), anterior.get("gerado_em", "?")[:16]))
            sys.exit(1)
    for s in saida:
        print("  %s  %-10s %-7s hawk=%d dove=%d  %s"
              % (s["data"], s["orador"][:10], s["inclinacao_por_contagem"], s["marcadores_hawkish"],
                 s["marcadores_dovish"], s["titulo"][:48]))
        for f in s["frases"][:2]:
            print("       • %s" % f["frase"][:150])

    rel = {"gerado_em": agora.isoformat(),
           "fonte": [RSS_DISCURSOS, RSS_POLITICA],
           "aviso": "EXTRACAO mecanica de frases de postura e contagem de expressoes. Nao e "
                    "interpretacao: um indice grosseiro para apontar QUAL discurso ler, nao o "
                    "que ele significa. A leitura do texto e a camada seguinte.",
           "marcadores": {"hawkish": HAWKISH, "dovish": DOVISH, "postura": POSTURA},
           "itens": saida}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s  (%d itens)" % (SAIDA, len(saida)))


if __name__ == "__main__":
    main()
