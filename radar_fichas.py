# -*- coding: utf-8 -*-
"""FICHA DA EMPRESA — a lacuna que o RADAR tinha e que mais importava.

O Eduardo apontou em 31/ago: os cinco componentes entregavam NUMEROS, e nenhum dizia
DE ONDE vinham nem para onde ir se aprofundar. Sem fonte nao da para auditar o dado nem
formar opiniao sobre a empresa — e a leitura humana e justamente a funcao do RADAR.

Esta ficha acrescenta, por ticker:
  - o que a empresa FAZ (resumo do proprio emissor)
  - site oficial e site de RELACOES COM INVESTIDORES (onde moram release e balanco)
  - setor, industria, pais, funcionarios, valor de mercado
  - noticias recentes COM FONTE E LINK
  - a PROVENIENCIA: qual API, em que dia, e o que e derivado

Cache: o perfil muda pouco (validade de 30 dias); noticia e do dia.
Assim uma execucao diaria custa pouco e o historico nao se perde.
"""
from __future__ import annotations
import glob, json, os, sys, time
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "data")
SAIDA = os.path.join(DADOS, "empresas.json")
VALIDADE_PERFIL_DIAS = 30
MAX_NOTICIAS = 4


def tickers_do_radar():
    """A uniao dos tickers que os cinco componentes citam hoje."""
    alvo = set()
    fontes = [("fornecedores.json", "nomes"), ("deep_value_scan.json", "nomes"),
              ("btd_scan.json", "nomes"), ("equities_research.json", "nomes"),
              ("revisoes.json", None)]
    for arq, chave in fontes:
        p = os.path.join(DADOS, arq)
        if not os.path.exists(p):
            continue
        try:
            j = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if chave:
            for x in j.get(chave, []):
                if x.get("ticker"):
                    alvo.add(x["ticker"])
        else:
            for lado in ("cima", "baixo"):
                for x in j.get(lado, []):
                    if x.get("ticker"):
                        alvo.add(x["ticker"])
    return sorted(alvo)


def carrega_cache():
    if os.path.exists(SAIDA):
        try:
            return json.load(open(SAIDA, encoding="utf-8"))
        except Exception:
            pass
    return {"gerado_em": None, "empresas": {}}


def perfil_velho(reg):
    if not reg or not reg.get("perfil_em"):
        return True
    try:
        d = datetime.strptime(reg["perfil_em"], "%Y-%m-%d")
    except Exception:
        return True
    return (datetime.now() - d).days >= VALIDADE_PERFIL_DIAS


def busca(tk, reg):
    import yfinance as yf
    t = yf.Ticker(tk)
    novo = dict(reg or {})
    novo["ticker"] = tk

    if perfil_velho(reg):
        try:
            i = t.info or {}
            novo.update({
                "nome": i.get("longName") or i.get("shortName"),
                "o_que_faz": (i.get("longBusinessSummary") or "")[:900] or None,
                "site": i.get("website"),
                "site_ri": i.get("irWebsite"),
                "setor": i.get("sector"), "industria": i.get("industry"),
                "pais": i.get("country"), "funcionarios": i.get("fullTimeEmployees"),
                "valor_mercado": i.get("marketCap"), "moeda": i.get("currency"),
                "bolsa": i.get("fullExchangeName") or i.get("exchange"),
                "perfil_em": datetime.now().strftime("%Y-%m-%d"),
                "perfil_fonte": "Yahoo Finance via yfinance",
            })
        except Exception as e:
            novo.setdefault("erro_perfil", str(e)[:120])

    # noticia e do dia, sempre
    try:
        ns = []
        for x in (t.news or [])[:MAX_NOTICIAS]:
            c = x.get("content", x)
            url = ((c.get("canonicalUrl") or {}).get("url")
                   or (c.get("clickThroughUrl") or {}).get("url") or c.get("link"))
            if not url:
                continue
            ns.append({
                "titulo": c.get("title"),
                "fonte": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                "url": url,
                "quando": c.get("pubDate") or c.get("displayTime"),
            })
        novo["noticias"] = ns
        novo["noticias_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        novo.setdefault("erro_noticias", str(e)[:120])
    return novo


if __name__ == "__main__":
    alvo = tickers_do_radar()
    cache = carrega_cache()
    emp = cache.get("empresas", {})
    print("=" * 92)
    print("FICHA DA EMPRESA — de onde vem o numero e onde ler mais")
    print("=" * 92)
    print("  tickers citados pelos componentes do RADAR: %d" % len(alvo))
    novos = renov = 0
    for k, tk in enumerate(alvo, 1):
        reg = emp.get(tk)
        era_novo = reg is None
        try:
            emp[tk] = busca(tk, reg)
            novos += era_novo
            renov += (not era_novo)
        except Exception as e:
            print("  [%s] falhou: %s" % (tk, str(e)[:70]))
        if k % 20 == 0:
            print("  %d/%d..." % (k, len(alvo)), flush=True)
        time.sleep(0.15)          # gentil com a API

    doc = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "proveniencia": {
            "perfil_e_noticias": "Yahoo Finance via yfinance (public endpoint)",
            "estimativas": "Financial Modeling Prep (FMP) — weekly PIT snapshots",
            "precos_e_metricas": "Yahoo Finance via yfinance",
            "nota": "Numbers are read from these sources on the date shown, not modelled by us. "
                    "Theses, target multiples and screening rules are ours and are declared per component.",
        },
        "validade_perfil_dias": VALIDADE_PERFIL_DIAS,
        "empresas": emp,
    }
    json.dump(doc, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    com_ri = sum(1 for v in emp.values() if v.get("site_ri"))
    com_news = sum(1 for v in emp.values() if v.get("noticias"))
    print()
    print("  %d empresas | %d perfis novos | %d renovados" % (len(emp), novos, renov))
    print("  com site de RI: %d | com noticia e link: %d" % (com_ri, com_news))
    print("  gravado: data/empresas.json")
