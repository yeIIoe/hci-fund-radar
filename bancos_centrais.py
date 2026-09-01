# -*- coding: utf-8 -*-
"""Gera data/bancos_centrais.json — taxa de politica e calendario das 8 moedas.

Levantado e conferido em 01/set/2026 (workflow de 8 agentes + conferente contra fonte oficial).

CONVENCAO TRAVADA, decidida na consolidacao:
    `ultima_mudanca` guarda a data do ANUNCIO, nunca a da vigencia — e o anuncio que move o
    preco. A vigencia fica no texto. Fed, BCE, RBA e BoC tem as duas datas diferentes, e
    misturar as duas desloca qualquer estudo de evento em um dia.

⚠️ HORA E SEMPRE LOCAL + FUSO IANA, NUNCA UTC FIXO.
    Tres mudancas de horario caem dentro deste calendario:
      27/set  NZ entra em NZDT       -> RBNZ sai de 02:00 para 01:00 UTC
      04/out  Australia entra em AEDT -> RBA sai de 04:30 para 03:30 UTC
      25/out  Europa sai do verao     -> BCE, SNB e BoE andam uma hora
      01/nov  EUA e Canada saem do DST
    Gravar UTC constante produz erro de uma hora exatamente nos meses que interessam.
"""
from __future__ import annotations
import io, json, os, sys
import datetime as dt
from zoneinfo import ZoneInfo

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "bancos_centrais.json")

BANCOS = {
    "USD": {
        "banco": "Federal Reserve", "sigla": "Fed",
        "nome_taxa": "Federal funds target range", "taxa": 3.625,
        "taxa_texto": "3,50–3,75%",
        "ultima_mudanca": "2025-12-10", "ultima_mudanca_bp": -25,
        "nota_vigencia": "anuncio 10/dez/2025, vigencia 11/dez",
        "hora_local": "14:00", "fuso": "America/New_York", "coletiva_local": "14:30",
        "reunioes": ["2026-09-16", "2026-10-28", "2026-12-09"],
        "nota_proxima": "com SEP e dot plot",
        "feed": "https://www.federalreserve.gov/feeds/press_monetary.xml",
    },
    "EUR": {
        "banco": "Banco Central Europeu", "sigla": "BCE",
        "nome_taxa": "Deposit facility rate", "taxa": 2.25,
        "taxa_texto": "2,25%  (MRO 2,40 · MLF 2,65)",
        "ultima_mudanca": "2026-06-11", "ultima_mudanca_bp": 25,
        "nota_vigencia": "1a alta em cerca de 3 anos; vigencia 17/jun",
        "hora_local": "14:15", "fuso": "Europe/Berlin", "coletiva_local": "14:45",
        "reunioes": ["2026-09-10", "2026-10-29", "2026-12-17"],
        "nota_proxima": "com projecoes do staff; reuniao sediada pelo Bundesbank",
        "feed": None,
    },
    "GBP": {
        "banco": "Bank of England", "sigla": "BoE",
        "nome_taxa": "Official Bank Rate", "taxa": 3.75,
        "taxa_texto": "3,75%",
        "ultima_mudanca": "2025-12-17", "ultima_mudanca_bp": -25,
        "nota_vigencia": "reuniao encerrada 17/dez, publicado 18/dez",
        "hora_local": "12:00", "fuso": "Europe/London", "coletiva_local": None,
        "reunioes": ["2026-09-17", "2026-11-05", "2026-12-17"],
        "nota_proxima": "sem coletiva — setembro nao e mes de relatorio",
        "feed": None,
    },
    "JPY": {
        "banco": "Bank of Japan", "sigla": "BoJ",
        "nome_taxa": "Call rate overnight (guideline)", "taxa": 1.0,
        "taxa_texto": "cerca de 1,0%",
        "ultima_mudanca": "2026-06-16", "ultima_mudanca_bp": 25,
        "nota_vigencia": "votacao 7 a 1; vigencia 17/jun",
        "hora_local": None, "fuso": "Asia/Tokyo", "coletiva_local": "15:30",
        "hora_nota": "SEM HORA FIXA — sai quando a reuniao acaba. Janela medida em 2026: "
                     "11:45 as 12:20 (n=5).",
        "reunioes": ["2026-09-18", "2026-10-30", "2026-12-18"],
        "nota_proxima": "sem Outlook Report",
        "feed": None,
    },
    "AUD": {
        "banco": "Reserve Bank of Australia", "sigla": "RBA",
        "nome_taxa": "Cash Rate Target", "taxa": 4.35,
        "taxa_texto": "4,35%",
        "ultima_mudanca": "2026-05-05", "ultima_mudanca_bp": 25,
        "nota_vigencia": "anuncio 05/mai, efeito 06/mai",
        "hora_local": "14:30", "fuso": "Australia/Sydney", "coletiva_local": "15:30",
        "reunioes": ["2026-09-29", "2026-11-03", "2026-12-08"],
        "nota_proxima": None,
        "feed": "https://www.rba.gov.au/rss/rss-cb-media-releases.xml",
    },
    "NZD": {
        "banco": "Reserve Bank of New Zealand", "sigla": "RBNZ",
        "nome_taxa": "Official Cash Rate", "taxa": 2.50,
        "taxa_texto": "2,50%",
        "ultima_mudanca": "2026-07-08", "ultima_mudanca_bp": 25,
        "nota_vigencia": "por consenso do comite",
        "hora_local": "14:00", "fuso": "Pacific/Auckland", "coletiva_local": "15:00",
        "reunioes": ["2026-09-02", "2026-10-28", "2026-12-09"],
        "nota_proxima": "com Monetary Policy Statement completo e trajetoria projetada da OCR",
        "feed": None,
    },
    "CAD": {
        "banco": "Bank of Canada", "sigla": "BoC",
        "nome_taxa": "Target for the overnight rate", "taxa": 2.25,
        "taxa_texto": "2,25%  (Bank Rate 2,50 · deposito 2,20)",
        "ultima_mudanca": "2025-10-29", "ultima_mudanca_bp": -25,
        "nota_vigencia": None,
        "hora_local": "09:45", "fuso": "America/Toronto", "coletiva_local": "10:30",
        "reunioes": ["2026-09-02", "2026-10-28", "2026-12-09"],
        "nota_proxima": "sem relatorio de politica monetaria",
        "feed": "https://www.bankofcanada.ca/?feed=ical&content_type=upcoming-events",
    },
    "CHF": {
        "banco": "Swiss National Bank", "sigla": "SNB",
        "nome_taxa": "SNB policy rate", "taxa": 0.0,
        "taxa_texto": "0,00%",
        "ultima_mudanca": "2025-06-19", "ultima_mudanca_bp": -25,
        "nota_vigencia": "cinco reunioes atras — o mais parado do painel",
        "hora_local": "09:30", "fuso": "Europe/Zurich", "coletiva_local": "10:00",
        "reunioes": ["2026-09-24", "2026-12-10"],
        "nota_proxima": "decide TRIMESTRALMENTE, nao a cada seis semanas",
        "feed": "https://www.snb.ch/public/ical/calendar/en/"
                "872f3023-70ea-42a9-8c27-524da3533fb7.ics",
    },
}


def em_utc(data, hora, fuso):
    """Deriva o UTC a partir do local. Nunca o contrario — e a derivacao que respeita o DST."""
    if not hora:
        return None
    h, m = (int(x) for x in hora.split(":"))
    d = dt.date.fromisoformat(data)
    return dt.datetime(d.year, d.month, d.day, h, m,
                       tzinfo=ZoneInfo(fuso)).astimezone(dt.timezone.utc).isoformat()


def main():
    hoje = dt.date.today()
    out = {}
    for m, b in BANCOS.items():
        futuras = [r for r in b["reunioes"] if dt.date.fromisoformat(r) >= hoje]
        prox = futuras[0] if futuras else None
        out[m] = dict(b)
        out[m]["proxima"] = prox
        out[m]["dias_ate"] = (dt.date.fromisoformat(prox) - hoje).days if prox else None
        out[m]["proxima_utc"] = em_utc(prox, b["hora_local"], b["fuso"]) if prox else None
        out[m]["coletiva_utc"] = em_utc(prox, b["coletiva_local"], b["fuso"]) if prox else None

    rel = {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(),
        "fonte": "levantamento de 01/set/2026 contra fontes oficiais, com conferente",
        "convencao": "ultima_mudanca = data do ANUNCIO; hora sempre LOCAL + fuso IANA",
        "bancos": out,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, allow_nan=False)

    print("=" * 84)
    print("BANCOS CENTRAIS — proxima decisao de cada um")
    print("=" * 84)
    print("  %-5s %-6s %-22s %-12s %-6s %s" % ("", "sigla", "taxa", "proxima", "dias", "hora local"))
    print("  " + "-" * 78)
    for m in sorted(out, key=lambda k: out[k]["dias_ate"] if out[k]["dias_ate"] is not None else 999):
        b = out[m]
        hora = b["hora_local"] or "sem hora fixa"
        print("  %-5s %-6s %-22s %-12s %-6s %s %s"
              % (m, b["sigla"], b["taxa_texto"][:22], b["proxima"] or "—",
                 b["dias_ate"] if b["dias_ate"] is not None else "—", hora, b["fuso"]))
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
