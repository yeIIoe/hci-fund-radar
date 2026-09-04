# -*- coding: utf-8 -*-
"""DISCURSOS DOS BANCOS CENTRAIS — a camada de TEXTO, para todas as moedas que deixam.

SUCEDE fed_discursos.py (03/set), que so lia o Fed. O Eduardo pediu (04/set): "para todos
os paises". Testado hoje, feed por feed:

    USD  Fed        RSS de discursos + RSS de politica monetaria       200
    EUR  BCE        RSS de imprensa (traz discursos e decisoes)       200
    GBP  BoE        RSS de discursos + RSS de noticias                200
    JPY  BoJ        RSS "what's new" (discursos, comunicados)         200
    CAD  BoC        RSS de discursos + de comunicados (RDF 1.0)       200
    AUD  RBA        403 — bloqueia automacao por politica propria     NAO CONECTADO
    NZD  RBNZ       403 — idem                                        NAO CONECTADO
    CHF  SNB        feed nao encontrado (404 nas rotas conhecidas)    NAO CONECTADO

O QUE FAZ — e o que NAO faz
    FAZ:  baixa cada discurso/comunicado, separa em frases e guarda as que carregam postura
          de politica ("I would", "appropriate to", "hold", "raise", "cut"...). Conta
          marcadores hawkish e dovish. E EXTRACAO mecanica, rotulada como tal.
    NAO:  nao "entende" o discurso. A contagem e um indice grosseiro para apontar QUAL texto
          ler. A camada de interpretacao entra depois e nasce marcada como interpretacao.

    ⚠️ As expressoes sao em ingles. Os cinco bancos conectados publicam em ingles.
    ⚠️ Nada aqui sobrescreve dado bom com vazio: se nenhuma fonte responder, sai com codigo 1
       e preserva o arquivo anterior.
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
SAIDA = os.path.join(AQUI, "data", "bc_discursos.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
DIAS = 21
MAX_POR_BANCO = 5

# Cada fonte: moeda, banco, tipo (speech|statement), url, filtro de titulo (regex) ou None
FONTES = [
    ("USD", "Fed", "speech",    "https://www.federalreserve.gov/feeds/speeches.xml", None),
    ("USD", "Fed", "statement", "https://www.federalreserve.gov/feeds/press_monetary.xml", r"FOMC statement"),
    ("EUR", "ECB", "speech",    "https://www.ecb.europa.eu/rss/press.html", r"^[A-ZÀ-Ý][^:]{2,40}: "),
    ("EUR", "ECB", "statement", "https://www.ecb.europa.eu/rss/press.html", r"Monetary policy decisions|monetary policy statement"),
    ("GBP", "BoE", "speech",    "https://www.bankofengland.co.uk/rss/speeches", None),
    ("GBP", "BoE", "statement", "https://www.bankofengland.co.uk/rss/news", r"Bank Rate|Monetary Policy Summary|Monetary Policy Report"),
    ("JPY", "BoJ", "speech",    "https://www.boj.or.jp/en/rss/whatsnew.xml", r"Speech|Remarks|Summary of Opinions"),
    ("JPY", "BoJ", "statement", "https://www.boj.or.jp/en/rss/whatsnew.xml", r"Statement on Monetary Policy|Outlook for Economic Activity"),
    ("CAD", "BoC", "speech",    "https://www.bankofcanada.ca/content_type/speeches/feed/", None),
    ("CAD", "BoC", "statement", "https://www.bankofcanada.ca/content_type/press-releases/feed/", r"policy interest rate|Monetary Policy Report|overnight rate"),
]
NAO_CONECTADO = {"AUD": "RBA returns 403 to automation", "NZD": "RBNZ returns 403 to automation",
                 "CHF": "SNB feed not found (404 on the known routes)"}

HAWKISH = ["raise the policy rate", "raise rates", "raise interest rates", "rate increase", "hike",
           "holding the target", "hold the target", "keep the policy rate", "remain restrictive",
           "restrictive for longer", "premature to", "upside risks to inflation",
           "inflation remains too high", "not yet time", "patient before", "tighten",
           "further increases", "additional tightening", "sufficiently restrictive"]
DOVISH = ["cut the policy rate", "lower the policy rate", "reduce the policy rate", "rate cut",
          "cut rates", "cutting rates", "cut interest rates", "lower interest rates",
          "reduce interest rates", "rate reduction", "ease policy", "easing policy",
          "appropriate to reduce", "downside risks to employment", "labor market is weakening",
          "labour market is weakening", "labor market has weakened", "further softening",
          "insurance cut", "move toward neutral", "less restrictive", "easing cycle"]
POSTURA = ["i would", "i believe", "i expect", "i support", "i favor", "i favour", "inclined to",
           "it may be appropriate", "it would be appropriate", "appropriate to", "my view",
           "i think the committee", "we should", "the committee should", "the council",
           "governing council", "the mpc", "the bank will", "the bank expects", "we expect",
           "we will", "we are prepared", "we judge", "our assessment"]


def busca(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


def itens_rss(xml: str) -> list:
    """RSS 2.0 (<item>), RDF 1.0 (<item rdf:about>) e Atom (<entry>)."""
    out = []
    blocos = re.findall(r"<item[^>]*>(.*?)</item>", xml, re.S) or re.findall(r"<entry[^>]*>(.*?)</entry>", xml, re.S)
    for it in blocos:
        def campo(t):
            m = re.search(r"<%s[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (t, t), it, re.S)
            return H.unescape(m.group(1).strip()) if m else None
        link = campo("link")
        if not link:
            m = re.search(r'<link[^>]*href="([^"]+)"', it)
            link = m.group(1) if m else None
        pub = campo("pubDate") or campo("dc:date") or campo("published") or campo("updated")
        out.append({"titulo": re.sub(r"<[^>]+>", "", campo("title") or ""), "link": link, "publicado": pub})
    return out


def data_de(pub: str):
    """RFC-822 (RSS: 'Fri, 04 Sep 2026 11:10:00 +0200') ou ISO (RDF/Atom).
    A versao anterior truncava o fuso e devolvia None para BCE, BoE e BoJ inteiros."""
    if not pub:
        return None
    pub = pub.strip()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pub).date()
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(pub.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})", pub)
    return dt.date.fromisoformat(m.group(1)) if m else None


def texto_da_pagina(html: str) -> str:
    # colunas principais conhecidas; senao a pagina inteira (o filtro de frases limpa o resto)
    for pad in (r'<div[^>]+class="col-xs-12 col-sm-8 col-md-8"[^>]*>(.*?)<div[^>]+class="col-xs-12 col-sm-4',
                r"<main[^>]*>(.*?)</main>", r"<article[^>]*>(.*?)</article>"):
        m = re.search(pad, html, re.S)
        if m:
            html = m.group(1)
            break
    html = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", html)
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
        if p and (h or d or "policy rate" in fl or "interest rate" in fl or "bank rate" in fl
                  or "federal funds" in fl or "meets on" in fl or "next meeting" in fl):
            chave.append({"frase": f.strip(), "hawkish": h, "dovish": d})
    chave.sort(key=lambda x: -(x["hawkish"] + x["dovish"]))
    lean = "hawkish" if hawk > dove else "dovish" if dove > hawk else "mixed"
    return {"frases": chave[:5], "marcadores_hawkish": hawk, "marcadores_dovish": dove,
            "inclinacao_por_contagem": lean if (hawk or dove) else "none"}


def orador_de(titulo: str, banco: str, tipo: str) -> str:
    """Fed: 'Waller, Titulo'. BCE: 'Nome: Titulo'. BoE: 'Titulo - speech by Nome' (o titulo
    pode ter dois-pontos dentro, por isso 'speech by' vem PRIMEIRO)."""
    if tipo == "statement":
        return banco
    m = re.search(r"(?:speech|remarks|lecture|address)\s+by\s+([A-Z][A-Za-zÀ-ÿ.'\- ]{3,40})", titulo, re.I)
    if m:
        return m.group(1).strip()
    if banco == "ECB" and ":" in titulo:
        return titulo.split(":")[0].strip()[:40]
    if banco == "Fed" and "," in titulo:
        return titulo.split(",")[0].strip()[:40]
    if ":" in titulo and len(titulo.split(":")[0]) <= 30:
        return titulo.split(":")[0].strip()
    return banco


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 86)
    print("DISCURSOS DOS BANCOS CENTRAIS — frases de postura, todas as moedas conectadas")
    print("=" * 86)
    saida, status = [], {}
    for moeda, banco, tipo, url, filtro in FONTES:
        try:
            itens = itens_rss(busca(url))
            status[moeda] = "ok"
        except Exception as e:
            print("  ! %s %s (%s): %s" % (moeda, banco, tipo, str(e)[:70]))
            status.setdefault(moeda, "erro: %s" % str(e)[:60])
            continue
        n = 0
        for it in itens:
            d = data_de(it.get("publicado") or "")
            if not d or (agora.date() - d).days > DIAS:
                continue
            titulo = it.get("titulo") or ""
            if filtro and not re.search(filtro, titulo, re.I):
                continue
            if not it.get("link"):
                continue
            if any(x["link"] == it["link"] for x in saida):
                continue
            try:
                txt = texto_da_pagina(busca(it["link"]))
            except Exception as e:
                print("  ! %s: %s" % (it["link"][:70], str(e)[:50]))
                continue
            ext = frases_de_postura(txt)
            saida.append({"moeda": moeda, "banco": banco, "tipo": tipo, "data": d.isoformat(),
                          "orador": orador_de(titulo, banco, tipo), "titulo": titulo[:160],
                          "link": it["link"], "caracteres": len(txt), **ext})
            n += 1
            if n >= MAX_POR_BANCO:
                break
    for m, motivo in NAO_CONECTADO.items():
        status[m] = "not connected: " + motivo

    saida.sort(key=lambda x: x["data"], reverse=True)
    por_moeda = {}
    for s in saida:
        por_moeda[s["moeda"]] = por_moeda.get(s["moeda"], 0) + 1
    print("  itens: %d  ·  por moeda: %s" % (len(saida), por_moeda))
    for s in saida[:12]:
        print("  %s %-4s %-12s %-7s h=%d d=%d  %s" % (s["data"], s["moeda"], s["orador"][:12],
              s["inclinacao_por_contagem"], s["marcadores_hawkish"], s["marcadores_dovish"], s["titulo"][:48]))
        if s["frases"]:
            print("       • %s" % s["frases"][0]["frase"][:140])

    if not saida:
        try:
            anterior = json.load(io.open(SAIDA, encoding="utf-8"))
        except Exception:
            anterior = None
        if anterior and anterior.get("itens"):
            print("  !! nenhuma fala coletada — arquivo anterior PRESERVADO (%d itens)" % len(anterior["itens"]))
            sys.exit(1)

    rel = {"gerado_em": agora.isoformat(),
           "status_fontes": status,
           "aviso": "EXTRACAO mecanica de frases de postura e contagem de expressoes em ingles. Nao e "
                    "interpretacao: um indice grosseiro para apontar QUAL texto ler.",
           "marcadores": {"hawkish": HAWKISH, "dovish": DOVISH, "postura": POSTURA},
           "itens": saida}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
