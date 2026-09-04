# -*- coding: utf-8 -*-
"""NOTICIAS — as manchetes de cada moeda, de todas as oito, sem chave e sem bloqueio.

O PEDIDO (Eduardo, 04/set)
    "todas as noticias de todas as moedas, disponiveis para a analise". E o buraco dos tres
    bancos que bloqueiam robo (RBA e RBNZ devolvem 403; SNB nao tem feed): a IMPRENSA que
    cobre os discursos deles nao bloqueia.

FONTE
    Google News RSS por busca — gratuito, sem chave, testado em 04/set: 100 itens por
    consulta, com Reuters, Bloomberg, WSJ, CNBC, em segundos. Duas consultas por moeda:
    o banco central + juros, e a economia do pais (inflacao, emprego, PIB).

O QUE SAI, por moeda
    itens        as manchetes das ultimas 72 h, sem duplicata, com fonte, hora e link
    contagem     quantas manchetes falam em ALTA, CORTE ou MANUTENCAO de juros — por
                 expressao, no titulo. E contagem, nao leitura: aponta o que ler.
    Esta contagem entra no sentimento como RESERVA da dimensao de discursos, so para as
    moedas cujo banco central nao tem feed (AUD, NZD, CHF) — e rotulada "from headlines".

⚠️ Uma manchete e opiniao de redator sobre o banco, nao a fala do banco. Por isso vale menos
    que o discurso e so entra onde nao ha discurso.
"""
from __future__ import annotations

import datetime as dt
import html as H
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "noticias.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
JANELA_H = 72
MAX_POR_MOEDA = 14
PAUSA_S = 1.5

CONSULTAS = {
    "USD": ['"Federal Reserve" OR Powell OR Waller interest rate',
            '"U.S. economy" inflation OR jobs OR payrolls'],
    "EUR": ['"European Central Bank" OR ECB OR Lagarde interest rate',
            '"euro zone" OR eurozone inflation OR economy'],
    "GBP": ['"Bank of England" OR BoE OR Bailey interest rate',
            'UK inflation OR "UK economy" OR "UK jobs"'],
    "JPY": ['"Bank of Japan" OR BOJ OR Ueda interest rate',
            'Japan inflation OR "Japan economy" OR yen'],
    "AUD": ['"Reserve Bank of Australia" OR RBA OR Bullock interest rate',
            'Australia inflation OR "Australian economy" OR jobs'],
    "NZD": ['"Reserve Bank of New Zealand" OR RBNZ interest rate',
            '"New Zealand" inflation OR economy OR "cash rate"'],
    "CAD": ['"Bank of Canada" OR Macklem interest rate',
            'Canada inflation OR "Canadian economy" OR jobs'],
    "CHF": ['"Swiss National Bank" OR SNB OR Schlegel interest rate',
            'Switzerland inflation OR franc OR "Swiss economy"'],
}

# expressoes de MANCHETE (curtas): alta / corte / manutencao — SEMPRE com o contexto de
# juro. "hike" solto pegava "price hike" e "tax hike" (JPY saiu com 41 "altas" em 72 h);
# "steady" solto pegava qualquer coisa.
ALTA = ["rate hike", "rate hikes", "rate increase", "raises rate", "raise rates", "raising rates",
        "hikes rate", "hike rates", "lifts rate", "rates higher", "higher rates", "more hikes",
        "further hike", "further increase", "tightening", "rate rise", "raises interest",
        "rate to rise", "hawkish"]
CORTE = ["rate cut", "rate cuts", "cuts rate", "cut rates", "cutting rates", "slash rates",
         "slashes rate", "lowers rate", "lower rates", "easing", "ease policy", "reduce rates",
         "rate reduction", "dovish", "cut interest"]
MANTEM = ["holds rate", "hold rate", "holds interest", "keeps rate", "keeps interest",
          "rates unchanged", "rate unchanged", "on hold", "holds key rate", "holds cash rate",
          "leaves rate", "stands pat", "pauses"]


def busca(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def itens_rss(xml: str) -> list:
    out = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def campo(t):
            m = re.search(r"<%s[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (t, t), it, re.S)
            return H.unescape(m.group(1).strip()) if m else None
        titulo = re.sub(r"<[^>]+>", "", campo("title") or "")
        fonte = campo("source") or ""
        if not fonte and " - " in titulo:
            fonte = titulo.rsplit(" - ", 1)[1].strip()
            titulo = titulo.rsplit(" - ", 1)[0].strip()
        out.append({"titulo": titulo, "link": campo("link"), "publicado": campo("pubDate"), "fonte": fonte})
    return out


def data_de(pub):
    try:
        d = parsedate_to_datetime(pub)
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def classifica(titulo: str) -> str | None:
    t = titulo.lower()
    if any(k in t for k in ALTA):
        return "alta"
    if any(k in t for k in CORTE):
        return "corte"
    if any(k in t for k in MANTEM):
        return "mantem"
    return None


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    inicio = agora - dt.timedelta(hours=JANELA_H)
    print("=" * 86)
    print("NOTICIAS — manchetes por moeda (Google News RSS), ultimas %d h" % JANELA_H)
    print("=" * 86)
    saida, erros = {}, []
    for moeda, consultas in CONSULTAS.items():
        vistos, itens = set(), []
        for q in consultas:
            u = "https://news.google.com/rss/search?q=%s&hl=en-US&gl=US&ceid=US:en" % urllib.parse.quote(q)
            try:
                brutos = itens_rss(busca(u))
            except Exception as e:
                erros.append("%s: %s" % (moeda, str(e)[:60]))
                time.sleep(PAUSA_S)
                continue
            for it in brutos:
                d = data_de(it.get("publicado") or "")
                if not d or d < inicio:
                    continue
                chave = re.sub(r"[^a-z0-9]", "", it["titulo"].lower())[:60]
                if not chave or chave in vistos:
                    continue
                vistos.add(chave)
                itens.append({"titulo": it["titulo"][:160], "fonte": it["fonte"][:40], "link": it["link"],
                              "quando_utc": d.astimezone(dt.timezone.utc).isoformat(),
                              "classe": classifica(it["titulo"])})
            time.sleep(PAUSA_S)
        itens.sort(key=lambda x: x["quando_utc"], reverse=True)
        cont = {"alta": 0, "corte": 0, "mantem": 0}
        for it in itens:
            if it["classe"]:
                cont[it["classe"]] += 1
        saida[moeda] = {"itens": itens[:MAX_POR_MOEDA], "n_72h": len(itens), "contagem": cont,
                        "inclinacao_por_manchete": ("alta" if cont["alta"] > cont["corte"] else
                                                    "corte" if cont["corte"] > cont["alta"] else
                                                    "mantem" if cont["mantem"] else "none")}
        print("  %-4s %3d manchetes em %dh · alta %d · corte %d · manutencao %d"
              % (moeda, len(itens), JANELA_H, cont["alta"], cont["corte"], cont["mantem"]))
        for it in itens[:2]:
            print("       • %s (%s)" % (it["titulo"][:88], it["fonte"]))

    if not any(v["itens"] for v in saida.values()):
        print("  !! nenhuma manchete — arquivo anterior preservado")
        sys.exit(1)
    rel = {"gerado_em": agora.isoformat(), "fonte": "Google News RSS (search), English",
           "janela_h": JANELA_H,
           "aviso": "headline COUNT by expression, not a reading. Enters the sentiment only as a fallback "
                    "for the speeches dimension where the central bank blocks automation (AUD, NZD, CHF).",
           "moedas": saida, "erros": erros}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
