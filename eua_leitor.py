# -*- coding: utf-8 -*-
"""LEITOR DOS ESTADOS UNIDOS — o dado do BLS e o calendario do Fed, sem intermediario.

POR QUE COMECAR PELOS EUA
    E a unica moeda com as DUAS pontas funcionando, testado em 02/set/2026:
      · Fed  -> RSS de politica monetaria E calendario do FOMC, ambos HTTP 200
      · BLS  -> API publica v2, HTTP 200, REQUEST_SUCCEEDED, sem chave, ~470 ms
    ⚠️ O levantamento de 01/set dizia que o BLS bloqueia robo. Isso vale para o SITE, nao
    para a API — e vale FORTE: pagina do release, RSS e .ics devolvem 403, so a API passa.

🔴 DUAS DEFASAGENS DIFERENTES, QUE EU JA CONFUNDI UMA VEZ
    (1) DEFASAGEM DE REFERENCIA — o dado descreve um mes que ja acabou. O CPI de agosto so
        pode existir depois que agosto termina, e sai por volta do dia 10 de setembro.
        E universal: a Bloomberg tem exatamente a mesma. Nao e defeito, e aritmetica.
    (2) DEFASAGEM DE ENTREGA — do instante em que o BLS publica (08:30 ET, cravado) ate o
        numero estar aqui. ESSA e a que importa para ler na hora, e ESSA ainda nao foi medida.
    Dizer "o BLS atrasa duas semanas" descreve a (1) e soa como a (2). Sao coisas distintas:
    o campo `defasagem_referencia_meses` e a primeira; a segunda so a medicao responde.

O QUE FALTA E SO A PONTE DA
    O BLS **nunca publica consenso**. Surpresa = divulgado - previsto, e o previsto so existe
    em calendario de vendor. Por isso a ponte MT5 nao e redundante com a API: a ponte da o
    QUANDO e o PREVISTO, a API da o NUMERO oficial e as revisoes. Sao complementares.

O QUE ELE NAO FAZ
    Nao le o texto do comunicado — isso e a camada de interpretacao, que entra depois e nasce
    marcada como interpretacao. Aqui e so o mecanico: numero, variacao e calendario.
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
FED_CAL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}

# 🔴 COTA — descoberto na marra em 02/set, estourando a cota enquanto testava.
#    sem chave    25 chamadas/dia
#    com chave    500 chamadas/dia   registro gratuito em data.bls.gov/registrationEngine/
#
#    Isto quase virou bug de producao: o cron do MACRO DIRECTION roda a cada 15 minutos, ou
#    seja 96 vezes por dia. Sem chave, a partir da 26a o BLS devolve REQUEST_NOT_PROCESSED e o
#    leitor ficaria mudo o resto do dia — com o site mostrando dado velho e carimbo novo, que e
#    exatamente o genero de falha silenciosa que ja custou caro aqui.
#
#    A defesa nao e so a chave: o dado do BLS e MENSAL. Perguntar de 15 em 15 minutos nao traz
#    informacao nenhuma. O cache abaixo derruba 96 chamadas/dia para no maximo 24, e o leitor
#    passa a caber na cota mesmo SEM chave.
CHAVE = os.environ.get("BLS_API_KEY", "").strip()
CACHE_MIN = 60

# Series do BLS, todas verificadas em 02/set/2026.
# `familia` liga cada uma a leitura de leitor_regras.py — peso e sinal vem de la, nao daqui.
SERIES = {
    "CUSR0000SA0":    {"nome": "CPI headline",           "familia": "inflacao_cheia",  "tipo": "indice"},
    "CUSR0000SA0L1E": {"nome": "CPI core",               "familia": "inflacao_nucleo", "tipo": "indice"},
    "CES0000000001":  {"nome": "Nonfarm payrolls",       "familia": "emprego_criacao", "tipo": "nivel_mil"},
    "LNS14000000":    {"nome": "Unemployment rate",      "familia": "desemprego",      "tipo": "taxa"},
    "CES0500000003":  {"nome": "Average hourly earnings", "familia": "salarios",       "tipo": "indice"},
    "LNS11300000":    {"nome": "Participation rate",     "familia": None,              "tipo": "taxa"},
}

MESES = ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"]
MES = {m: i for i, m in enumerate(MESES, 1)}


class CotaEstourada(RuntimeError):
    """A cota diaria do BLS acabou. Distinta de falha de rede: nao adianta tentar de novo hoje."""


def bls(series: list, ini: int, fim: int) -> dict:
    """Um POST com TODAS as series de uma vez — o BLS aceita lote, e cada chamada custa cota."""
    corpo = {"seriesid": series, "startyear": str(ini), "endyear": str(fim)}
    if CHAVE:
        corpo["registrationkey"] = CHAVE
    req = urllib.request.Request(BLS_API, data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    msgs = " ".join(d.get("message") or [])
    if d.get("status") != "REQUEST_SUCCEEDED":
        if "threshold" in msgs.lower() or "daily" in msgs.lower():
            raise CotaEstourada(
                "cota diaria do BLS esgotada (%s/dia). Registre a chave gratuita em "
                "data.bls.gov/registrationEngine/ e ponha em BLS_API_KEY -> 500/dia."
                % ("500" if CHAVE else "25"))
        raise RuntimeError("BLS recusou: %s" % (msgs or d.get("status")))
    for m in (d.get("message") or []):
        print("  ! BLS: %s" % m)
    return {s["seriesID"]: s.get("data", []) for s in d.get("Results", {}).get("series", [])}


def cache_ainda_serve(forcar: bool) -> dict | None:
    """O dado do BLS e mensal. Se a leitura anterior e recente, nao gasta cota de novo.

    Devolve o relatorio anterior quando ele ainda vale, ou None quando e hora de buscar.
    """
    if forcar or not os.path.exists(SAIDA):
        return None
    try:
        velho = json.load(io.open(SAIDA, encoding="utf-8"))
        gerado = dt.datetime.fromisoformat(velho["gerado_em"])
    except Exception:
        return None
    idade_min = (dt.datetime.now(dt.timezone.utc) - gerado).total_seconds() / 60.0
    if idade_min < CACHE_MIN and velho.get("indicadores"):
        velho["reaproveitado_do_cache"] = True
        velho["idade_min"] = round(idade_min, 1)
        return velho
    return None


def serie_ordenada(dados: list) -> list:
    """Do mais ANTIGO para o mais novo, com a data e o selo de preliminar resolvidos."""
    out = []
    for x in dados:
        m = MES.get(x.get("periodName"))
        if not m:
            continue
        try:
            prelim = any("prelim" in (f.get("text") or "").lower()
                         for f in (x.get("footnotes") or []) if f)
            out.append((dt.date(int(x["year"]), m, 1), float(x["value"]), prelim))
        except (ValueError, KeyError):
            continue
    return sorted(out)


def variacoes(pontos: list, tipo: str) -> dict:
    """m/m e a/a. Indice vira percentual; taxa e nivel ficam em diferenca absoluta."""
    if len(pontos) < 2:
        return {}
    atual = pontos[-1][1]
    ant = pontos[-2][1]
    doze = pontos[-13][1] if len(pontos) >= 13 else None

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
        with urllib.request.urlopen(urllib.request.Request(FED_RSS, headers=UA), timeout=45) as r:
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


def fomc_calendario() -> dict:
    """Datas das reunioes do FOMC, direto do Fed. 55 reunioes, de 2021 a 2027.

    O asterisco no site marca a reuniao que sai COM projecoes (o dot plot) — e a que revela
    o caminho de juro que o proprio comite projeta, e por isso a que mais move preco.
    A data guardada e o ULTIMO dia do intervalo: a decisao sai no fim da reuniao, nao no comeco.
    """
    try:
        with urllib.request.urlopen(urllib.request.Request(FED_CAL, headers=UA), timeout=45) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"erro": str(e)}

    reunioes = []
    partes = re.split(r"(\d{4})\s+FOMC\s+Meetings", html)
    for i in range(1, len(partes) - 1, 2):
        ano = int(partes[i])
        bloco = partes[i + 1]
        meses = re.findall(r"fomc-meeting__month[^>]*>\s*(?:<[^>]+>\s*)*([A-Za-z/\s]+?)\s*<", bloco)
        datas = re.findall(r"fomc-meeting__date[^>]*>\s*([^<]+?)\s*<", bloco)
        for m, d in zip(meses, datas):
            nomes = [x for x in re.split(r"[/\s]+", m.strip()) if x in MES]
            dd = re.findall(r"\d+", d)
            if not nomes or not dd:
                continue
            # reuniao que vira o mes (ex.: "April/May 29-1"): o dia da decisao esta no 2o mes
            mes = MES[nomes[-1]] if (len(nomes) > 1 and len(dd) > 1) else MES[nomes[0]]
            try:
                data = dt.date(ano, mes, int(dd[-1]))
            except ValueError:
                continue
            reunioes.append({"data": data.isoformat(),
                             "rotulo": "%s %s" % (m.strip(), d.strip()),
                             "com_projecoes": "*" in d,
                             "voto_por_notacao": "notation" in d.lower()})
    reunioes.sort(key=lambda x: x["data"])
    hoje = dt.date.today().isoformat()
    futuras = [r for r in reunioes if r["data"] >= hoje and not r["voto_por_notacao"]]
    return {"total": len(reunioes), "proximas": futuras[:6],
            "proxima": futuras[0] if futuras else None}


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    forcar = "--forcar" in sys.argv
    print("=" * 86)
    print("LEITOR DOS ESTADOS UNIDOS")
    print("=" * 86)
    print("  chave do BLS: %s" % ("registrada (500 chamadas/dia)" if CHAVE else
                                  "AUSENTE — 25 chamadas/dia. Registre em "
                                  "data.bls.gov/registrationEngine/"))

    guardado = cache_ainda_serve(forcar)
    if guardado:
        ind = guardado.get("indicadores", {})
        ref = max((x.get("referencia", "") for x in ind.values()), default="?")
        print("  leitura de %.0f min atras ainda vale (dado do BLS e MENSAL) — cota poupada."
              % guardado["idade_min"])
        print("  %d indicadores, referencia %s. Use --forcar para buscar mesmo assim."
              % (len(ind), ref))
        return

    try:
        cru = bls(list(SERIES), agora.year - 2, agora.year)
    except CotaEstourada as e:
        # Sai com codigo de erro para o cron ficar VERMELHO. Falha silenciosa aqui viraria
        # dado velho com carimbo novo no site — o pior desfecho possivel.
        print()
        print("  !! COTA ESTOURADA: %s" % e)
        print("  !! A leitura anterior foi PRESERVADA — nada foi sobrescrito com vazio.")
        sys.exit(2)
    except Exception as e:
        print("  X BLS falhou: %s" % e)
        sys.exit(1)

    leitura = {}
    print()
    print("  %-28s %12s %10s %10s  %-8s" % ("indicador", "ultimo", "m/m", "a/a", "ref"))
    print("  " + "-" * 82)
    for sid, meta in SERIES.items():
        pontos = serie_ordenada(cru.get(sid, []))
        if not pontos:
            print("  %-28s  sem dado" % meta["nome"])
            continue
        v = variacoes(pontos, meta["tipo"])
        d, val, prelim = pontos[-1]
        leitura[sid] = {"nome": meta["nome"], "familia": meta["familia"],
                        "referencia": d.isoformat()[:7], "valor": val,
                        "preliminar": prelim, "n_obs": len(pontos), **v}
        print("  %-28s %12.3f %9s %9s  %-8s %s"
              % (meta["nome"], val,
                 ("%+.2f%s" % (v["mm"], v["unidade"])) if v.get("mm") is not None else "-",
                 ("%+.2f%s" % (v["aa"], v["unidade"])) if v.get("aa") is not None else "-",
                 d.isoformat()[:7], "preliminar - o BLS ainda revisa" if prelim else ""))

    # DEFASAGEM (1): de REFERENCIA. O dado descreve um mes que ja acabou. Universal.
    refs = {x["referencia"] for x in leitura.values()}
    atraso = None
    if refs:
        y, m = (int(x) for x in max(refs).split("-"))
        atraso = (agora.year - y) * 12 + (agora.month - m)
        print()
        print("  DEFASAGEM DE REFERENCIA: %d mes(es). O dado mais novo descreve %s."
              % (atraso, max(refs)))
        print("     Nao e atraso de entrega - e o mes que ja acabou. A Bloomberg tem a mesma.")
        print("  DEFASAGEM DE ENTREGA (release 08:30 ET -> aqui): AINDA NAO MEDIDA.")
        print("     E o que a sexta responde, com o NFP, cronometrando API e ponte MT5 juntas.")

    # Se o Fed nao responder, fica o calendario e o feed da leitura ANTERIOR — nunca um
    # {"erro": ...} sobrescrevendo 55 reunioes boas (revisao de 03/set).
    anterior = {}
    try:
        anterior = json.load(io.open(SAIDA, encoding="utf-8")) if os.path.exists(SAIDA) else {}
    except Exception:
        anterior = {}
    fomc = fomc_calendario()
    if fomc.get("erro") and (anterior.get("fomc") or {}).get("proximas"):
        print("  ! calendario do FOMC falhou (%s) — mantido o anterior" % fomc["erro"])
        fomc = dict(anterior["fomc"], reaproveitado=True)
    print()
    print("  CALENDARIO DO FOMC (direto do Fed)")
    if fomc.get("erro"):
        print("    X %s" % fomc["erro"])
    else:
        print("    %d reunioes no calendario publicado" % fomc["total"])
        for r in fomc["proximas"][:3]:
            faltam = (dt.date.fromisoformat(r["data"]) - dt.date.today()).days
            print("      %s  em %3d dias   %-20s %s"
                  % (r["data"], faltam, r["rotulo"],
                     "COM projecoes (dot plot)" if r["com_projecoes"] else ""))

    fed = fed_rss()
    if fed.get("erro") and (anterior.get("fed") or {}).get("ultimos"):
        print("  ! feed do Fed falhou (%s) — mantido o anterior" % fed["erro"])
        fed = dict(anterior["fed"], reaproveitado=True)
    print()
    print("  COMUNICADOS DO FED")
    if fed.get("erro"):
        print("    X %s" % fed["erro"])
    else:
        print("    %d itens no feed - Last-Modified: %s"
              % (fed["total_no_feed"], fed.get("last_modified_do_servidor")))
        for x in fed["ultimos"][:3]:
            print("      %s  %s" % ((x.get("publicado") or "?")[:25], (x.get("titulo") or "")[:54]))

    rel = {
        "gerado_em": agora.isoformat(),
        "fonte_dado": "BLS public API v2 (sem chave; o SITE do BLS devolve 403, a API nao)",
        "fonte_comunicado": FED_RSS,
        "fonte_calendario": FED_CAL,
        "defasagem_referencia_meses": atraso,
        "defasagem_entrega_ms": None,
        "aviso_defasagem": "sao DUAS coisas distintas. referencia = o mes que o dado descreve, "
                           "universal e inevitavel. entrega = do release ate aqui: MEDIDA por "
                           "evento na fonte do calendario (FXStreet, campo atraso_s); NAO medida "
                           "para a API do BLS, que exige a chave registrada para ser cronometrada.",
        "aviso_consenso": "o BLS nunca publica previsao. surpresa = divulgado - previsto exige "
                          "o previsto, que so existe em calendario de vendor. por isso a ponte "
                          "MT5 nao e redundante: ela da o QUANDO e o PREVISTO.",
        "aviso": "leitura MECANICA: numero e variacao. O texto do comunicado nao e interpretado "
                 "aqui - essa camada entra depois e nasce marcada como interpretacao.",
        "serve_tambem": ["GC", "NQ", "ES", "todos os pares com USD"],
        "nota_ouro": "juro real 10a x ouro: -0,684 em 60 pregoes, contemporaneo, janelas sem "
                     "sobreposicao (n=18). A preditiva morre no ruido (-0,132).",
        "indicadores": leitura,
        "fomc": fomc,
        "fed": fed,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
