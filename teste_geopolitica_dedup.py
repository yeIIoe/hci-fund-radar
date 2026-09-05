# -*- coding: utf-8 -*-
"""TESTE DA DEDUPLICACAO — le data/geopolitica.json e data/noticias.json do disco e roda o
agrupamento de geopolitica.py. NENHUMA chamada ao GDELT: importar o modulo nao dispara nada
(main() esta atras do guard) e a funcao de rede e substituida por uma trava que estoura."""
import io, json, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import geopolitica as G


def _proibido(*a, **k):
    raise AssertionError("PROIBIDO: o teste tentou falar com o GDELT")


G.gdelt = _proibido


def mostra(rotulo, manchetes, detalhe=True):
    grupos, dupes = G.agrupa(manchetes)
    print("\n" + "=" * 92)
    print("%s — %d manchetes -> %d grupos (%d duplicatas removidas)"
          % (rotulo, len(manchetes), len(grupos), dupes))
    print("=" * 92)
    unicas, _ = G.deduplica(manchetes)
    for i, r in enumerate(unicas, 1):
        if not detalhe and r["n_republicacoes"] == 1:
            continue
        print("\n GRUPO %d · ação=%s · entidades=%s · confiabilidade=%s · n_republicacoes=%d"
              % (i, r["acao"], ",".join(r["entidades"]) or "—", r["confiabilidade"],
                 r["n_republicacoes"]))
        print("   [representante] %s  (%s)" % (r["titulo"][:96], r["fonte"]))
        for d in r["agrupadas"]:
            print("   [agrupada     ] %s  (%s · %s)" % (d["titulo"][:96], d["fonte"],
                                                        d["confiabilidade"]))
    return dupes


print("#" * 92)
print("# 1. MANCHETES REAIS DE HOJE (data/geopolitica.json)")
print("#" * 92)
total = 0
geo = json.load(io.open(os.path.join(AQUI, "data", "geopolitica.json"), encoding="utf-8"))
for tema, b in (geo.get("mundo") or {}).items():
    total += mostra("MUNDO / %s" % tema, b.get("manchetes") or [])
for m, b in (geo.get("moedas") or {}).items():
    for tema, t in (b.get("temas") or {}).items():
        lst = t.get("manchetes") or []
        if lst:
            total += mostra("%s / %s" % (m, tema), lst)
        else:
            print("\n  %s / %s: 0 manchetes no arquivo (a coleta por moeda está desligada "
                  "desde 04/set para não tomar 429) -> manchetes_unicas fica vazia" % (m, tema))
print("\n>>> geopolitica.json: %d duplicatas removidas no total" % total)
assert total == 2, "esperava 2 duplicatas nas manchetes de hoje, veio %d" % total

print("\n" + "#" * 92)
print("# 2. MAIS CASOS: manchetes reais de data/noticias.json (só o que AGRUPOU)")
print("#" * 92)
nz = json.load(io.open(os.path.join(AQUI, "data", "noticias.json"), encoding="utf-8"))
for moeda in ("USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"):
    itens = ((nz.get("moedas") or {}).get(moeda) or {}).get("itens") or []
    lst = [{"titulo": i.get("titulo"), "fonte": i.get("fonte"), "url": i.get("link"),
            "quando": i.get("quando_utc")} for i in itens]
    if lst:
        mostra("NOTICIAS / %s" % moeda, lst, detalhe=False)

print("\n" + "#" * 92)
print("# 3. CONTROLES")
print("#" * 92)
# 3a. NAO PODE agrupar: dois ataques em pontos opostos do mundo, mais um de energia
nao_agrupa = [
    {"titulo": "Russia launches missile strike on Kyiv, killing 12", "fonte": "reuters.com",
     "quando": "20260904T060000Z"},
    {"titulo": "Israel strikes Gaza, dozens dead", "fonte": "apnews.com",
     "quando": "20260904T070000Z"},
    {"titulo": "OPEC keeps oil output steady as crude prices slide", "fonte": "bloomberg.com",
     "quando": "20260904T090000Z"},
]
d = mostra("CONTROLE 3a — NÃO pode agrupar (Kiev x Gaza x OPEP)", nao_agrupa)
assert d == 0, "agrupou o que não devia: %d" % d
print("\n>>> 3a OK: a classe de ação é a mesma nos dois ataques, a entidade separou")

# 3b. TEM de agrupar: o mesmo ataque contado por dois veiculos, com 2 entidades em comum
agrupa_sim = [
    {"titulo": "Russian missile strike on Kyiv kills 12", "fonte": "trend.az",
     "quando": "20260904T060000Z"},
    {"titulo": "Moscow attack leaves 12 dead in Ukraine, Kyiv says", "fonte": "reuters.com",
     "quando": "20260904T063000Z"},
]
d = mostra("CONTROLE 3b — TEM de agrupar (mesmo ataque, dois veículos)", agrupa_sim)
assert d == 1, "não agrupou o mesmo ataque: %d" % d
u, _ = G.deduplica(agrupa_sim)
assert u[0]["fonte"] == "reuters.com", "o representante devia ser a fonte de maior confiabilidade"
print("\n>>> 3b OK: agrupou, e o representante é a Reuters (confiabilidade alta), não o trend.az")

# 3c. BURACO DECLARADO: evento com UMA entidade so nao agrupa
buraco = [
    {"titulo": "Russia launches missile strike on Kyiv, killing 12", "fonte": "reuters.com",
     "quando": "20260904T060000Z"},
    {"titulo": "Missile attack on Kyiv leaves 12 dead, Ukraine says", "fonte": "trend.az",
     "quando": "20260904T080000Z"},
]
d = mostra("CONTROLE 3c — BURACO DECLARADO (a 2ª manchete só nomeia a Ucrânia)", buraco)
assert d == 0
print("\n>>> 3c: não agrupou, e está DECLARADO no JSON. Erra para menos, nunca para mais.")

print("\n" + "#" * 92)
print("# 4. CONFIABILIDADE por fonte")
print("#" * 92)
esperado = {
    "reuters.com": "alta", "apnews.com": "alta", "bloomberg.com": "alta",
    "federalreserve.gov": "alta", "ons.gov.uk": "alta", "Reuters": "alta",
    "bbc.co.uk": "media", "kyivpost.com": "media", "nytimes.com": "media",
    "The Japan Times": "media", "Barron's": "alta", "CNBC": "media",
    "trend.az": "baixa", "khaama.com": "baixa", "freemalaysiatoday.com": "baixa",
    "dailypioneer.com": "baixa", "news.google.com": "baixa", "msn.com": "baixa",
    "finance.yahoo.com": "baixa", "FXStreet": "baixa", "TradingView": "baixa",
}
erros = 0
for f, esp in esperado.items():
    veio = G.confiabilidade_de(f)
    marca = "ok " if veio == esp else "!! "
    erros += veio != esp
    print("   %s%-26s %-6s (esperado %s)" % (marca, f, veio, esp))
assert erros == 0, "%d fontes fora do esperado" % erros
print("\n>>> 4 OK: %d fontes classificadas como declarado" % len(esperado))
print("\nTODOS OS TESTES PASSARAM — nenhuma chamada de rede foi feita.")
