# -*- coding: utf-8 -*-
"""NOTICIAS — as manchetes de cada moeda, com ORIGEM, PESO e DEDUPLICACAO.

O PEDIDO (Eduardo, 04/set)
    "todas as noticias de todas as moedas, disponiveis para a analise". E o buraco dos tres
    bancos que bloqueiam robo (RBA e RBNZ devolvem 403; SNB nao tem feed): a IMPRENSA que
    cobre os discursos deles nao bloqueia.

O CONSERTO DE 05/set (item 2 da revisao do dono, o mais grave)
    O painel mostrava "38 discursos" para o AUD tendo ZERO fala do RBA no arquivo: eram
    MANCHETES do Google News entrando como reserva da dimensao de texto e sendo exibidas como
    se fossem falas de dirigente. O dono viu realestate.com.au para o AUD e Financial Post
    para o CAD listados como discurso. Tres consertos:

    (A) HIERARQUIA DE PESO gravada no proprio item:
          discurso_oficial   1,0   fala de dirigente no site do banco central   (bc_discursos.py)
          comunicado_ata     1,0   comunicado, ata, relatorio, coletiva          (bc_discursos.py)
          imprensa_com_fala  0,4   imprensa reproduzindo fala de dirigente NOMEADO
          manchete           0,0   opiniao, analise, manchete sem fala: SO CONTEXTO
        Aqui nascem as duas ultimas. Todo item sai com "origem", "peso" e
        "orador_identificado". Para virar imprensa_com_fala tem de haver, no titulo ou no
        resumo, o NOME de um dirigente E um VERBO DE FALA — e o veiculo tem de ter peso de
        fonte >= 0,6 (limiar PROVISORIO). Senao e manchete, peso zero.

    (B) DEDUPLICACAO. A mesma noticia republicada em varios sites e UM evento. O titulo e
        normalizado (minusculas, sem acento, sem pontuacao, sem o nome do veiculo, sem
        palavras vazias) e os itens sao agrupados por JACCARD >= 0,70 sobre o conjunto de
        palavras — REGRA DECLARADA, escolhida entre as duas propostas. A assinatura das 8
        palavras mais longas fica gravada em cada grupo, para auditoria e para casar em O(1)
        os titulos identicos. Saem "n_unicos" e "duplicatas_removidas"; o representante do
        grupo e a fonte de MAIOR peso, e o grupo herda a MAIOR origem entre os membros (se um
        membro qualquer tem fala de dirigente, o evento tem fala).

    (C) O BURACO DECLARADO. Para AUD, NZD e CHF o banco central bloqueia robo. Depois de (A),
        a reserva por manchete vale ZERO na votacao: a dimensao de texto dessas tres moedas
        fica SEM VOTO, nao com voto fraco — "silencio nao e voto" aplicado direito. A
        dimensao continua exibida como CONTEXTO, com o rotulo em "rotulo_contexto".
        EXCECAO: item "imprensa_com_fala" com dirigente nomeado (Bullock, Hauser, Kent no
        RBA; Hawkesby, Conway, Silk no RBNZ; Schlegel, Tschudin, Moser no SNB) VOTA com peso
        0,4. Por isso ha uma consulta a mais por moeda, buscando esses nomes.

CONTRATO DE SAIDA, por moeda (data/noticias.json)
    itens                 manchetes unicas das ultimas 72 h, com fonte, hora, link, origem,
                          peso, orador_identificado e as duplicatas absorvidas
    contagem              alta/corte/manutencao em TODOS os itens unicos — CONTEXTO, e o que
                          a aba de noticias mostra. NAO e voto.
    contagem_voto         idem, so nos itens que VOTAM (peso > 0)
    voto                  {vota, peso, origem, direcao, n_falas, oradores, rotulo}
    n_unicos              eventos apos a deduplicacao
    duplicatas_removidas  republicacoes absorvidas

    Uma manchete e opiniao de redator sobre o banco, nao a fala do banco: peso ZERO.
    Nada aqui sobrescreve dado bom com vazio: sem manchete nenhuma, sai com codigo 1.
    Todo limiar novo e PROVISORIO (marcado no JSON), para o backtest calibrar.
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
import unicodedata
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

# ---------------------------------------------------------------- hierarquia de peso da fala
# GEMEA: a mesma tabela vive em bc_discursos.py (que produz as duas primeiras linhas).
PESO_ORIGEM = {
    "discurso_oficial": 1.0,
    "comunicado_ata": 1.0,
    "imprensa_com_fala": 0.4,
    "manchete": 0.0,
}
# Bancos que bloqueiam automacao: e para eles que existe o rotulo de contexto.
BANCO_BLOQUEIA = {"AUD": "RBA", "NZD": "RBNZ", "CHF": "SNB"}
ROTULO_CONTEXTO = ("sem fala oficial disponivel — o banco bloqueia automacao; "
                   "a imprensa abaixo e contexto, nao voto")

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
            'Australia inflation OR "Australian economy" OR jobs',
            # (C) cacada ATIVA de fala de dirigente — a unica coisa que vota nesta moeda
            '"Michele Bullock" OR "Andrew Hauser" OR "Christopher Kent" RBA'],
    "NZD": ['"Reserve Bank of New Zealand" OR RBNZ interest rate',
            '"New Zealand" inflation OR economy OR "cash rate"',
            '"Christian Hawkesby" OR "Paul Conway" OR "Karen Silk" RBNZ'],
    "CAD": ['"Bank of Canada" OR Macklem interest rate',
            'Canada inflation OR "Canadian economy" OR jobs'],
    "CHF": ['"Swiss National Bank" OR SNB OR Schlegel interest rate',
            'Switzerland inflation OR franc OR "Swiss economy"',
            '"Martin Schlegel" OR "Petra Tschudin" OR "Thomas Moser" OR "Antoine Martin" SNB'],
}

# ------------------------------------------------------------------ quem e dirigente de quem
# Sobrenome sozinho NAO basta na imprensa (um "Kent" pode ser um lugar): exige-se o nome
# completo, OU o sobrenome mais a sigla do banco, OU o sobrenome mais um cargo.
DIRIGENTES = {
    "USD": {"siglas": ["fed", "federal reserve", "fomc"],
            "nomes": [("jerome powell", "powell"), ("philip jefferson", "jefferson"),
                      ("michael barr", "barr"), ("michelle bowman", "bowman"),
                      ("christopher waller", "waller"), ("lisa cook", "cook"),
                      ("john williams", "williams"), ("lorie logan", "logan"),
                      ("raphael bostic", "bostic"), ("austan goolsbee", "goolsbee"),
                      ("neel kashkari", "kashkari"), ("alberto musalem", "musalem"),
                      ("jeffrey schmid", "schmid"), ("beth hammack", "hammack"),
                      ("susan collins", "collins"), ("tom barkin", "barkin"),
                      ("mary daly", "daly"), ("stephen miran", "miran")]},
    "EUR": {"siglas": ["ecb", "european central bank"],
            "nomes": [("christine lagarde", "lagarde"), ("luis de guindos", "de guindos"),
                      ("philip lane", "lane"), ("isabel schnabel", "schnabel"),
                      ("piero cipollone", "cipollone"), ("frank elderson", "elderson"),
                      ("joachim nagel", "nagel"), ("francois villeroy", "villeroy"),
                      ("fabio panetta", "panetta"), ("klaas knot", "knot"),
                      ("olli rehn", "rehn"), ("madis muller", "muller"),
                      ("martins kazaks", "kazaks"), ("pierre wunsch", "wunsch"),
                      ("yannis stournaras", "stournaras"), ("gabriel makhlouf", "makhlouf"),
                      ("robert holzmann", "holzmann"), ("boris vujcic", "vujcic")]},
    "GBP": {"siglas": ["boe", "bank of england", "mpc"],
            "nomes": [("andrew bailey", "bailey"), ("dave ramsden", "ramsden"),
                      ("huw pill", "pill"), ("sarah breeden", "breeden"),
                      ("clare lombardelli", "lombardelli"), ("megan greene", "greene"),
                      ("catherine mann", "mann"), ("swati dhingra", "dhingra"),
                      ("alan taylor", "taylor"), ("jonathan haskel", "haskel")]},
    "JPY": {"siglas": ["boj", "bank of japan"],
            "nomes": [("kazuo ueda", "ueda"), ("ryozo himino", "himino"),
                      ("shinichi uchida", "uchida"), ("seiji adachi", "adachi"),
                      ("toyoaki nakamura", "nakamura"), ("asahi noguchi", "noguchi"),
                      ("junko nakagawa", "nakagawa"), ("hajime takata", "takata"),
                      ("naoki tamura", "tamura"), ("junko koeda", "koeda")]},
    "AUD": {"siglas": ["rba", "reserve bank of australia"],
            "nomes": [("michele bullock", "bullock"), ("andrew hauser", "hauser"),
                      ("christopher kent", "kent"), ("chris kent", "kent"),
                      ("sarah hunter", "hunter"), ("brad jones", "jones")]},
    "NZD": {"siglas": ["rbnz", "reserve bank of new zealand"],
            "nomes": [("christian hawkesby", "hawkesby"), ("paul conway", "conway"),
                      ("karen silk", "silk"), ("anna breman", "breman")]},
    "CAD": {"siglas": ["boc", "bank of canada"],
            "nomes": [("tiff macklem", "macklem"), ("carolyn rogers", "rogers"),
                      ("sharon kozicki", "kozicki"), ("toni gravelle", "gravelle"),
                      ("nicolas vincent", "vincent"), ("rhys mendes", "mendes"),
                      ("michelle alexopoulos", "alexopoulos")]},
    "CHF": {"siglas": ["snb", "swiss national bank", "bns"],
            "nomes": [("martin schlegel", "schlegel"), ("antoine martin", "martin"),
                      ("petra tschudin", "tschudin"), ("attilio zanetti", "zanetti"),
                      ("thomas moser", "moser")]},
}
CARGOS = ["governor", "deputy governor", "assistant governor", "chief economist",
          "board member", "policymaker", "policy maker", "central banker", "rate-setter",
          "rate setter", "mpc member", "president", "chair", "chairman", "vice chair"]
# VERBO DE FALA: sem um destes no titulo ou no resumo, nao ha fala reproduzida — e manchete.
VERBOS_FALA = ["said", "says", "say", "told", "tells", "speech", "remarks", "spoke", "speaks",
               "warned", "warns", "signalled", "signaled", "signals", "comments", "commented",
               "stated", "states", "declared", "argued", "argues", "noted", "notes",
               "reiterated", "reiterates", "repeated", "flagged", "flags", "hinted", "hints",
               "urged", "urges", "added", "adds", "testified", "testimony", "interview",
               "according to", "in a speech", "told reporters", "address", "testifies"]

# --------------------------------------------------------------------- peso do VEICULO
# PROVISORIO (a calibrar). Agencia e jornal de mercado no topo; banco central e governo
# tambem no topo; imprensa nacional de qualidade no meio; portal e corretora embaixo.
PESO_FONTE = {
    1.00: ["reuters", "bloomberg", "financial times", "wall street journal", "wsj",
           "dow jones", "federal reserve", "european central bank", "bank of england",
           "bank of japan", "bank of canada", "reserve bank", "swiss national bank",
           "gov.uk", "gov.au", ".gov", "treasury", "statistics", "ons", "eurostat"],
    0.80: ["associated press", "ap news", "afp", "cnbc", "marketwatch", "barron", "nikkei",
           "the economist", "financial review", "afr", "politico", "axios", "bbc"],
    0.60: ["the guardian", "abc news", "the australian", "sydney morning herald", "the age",
           "new zealand herald", "nzherald", "rnz", "stuff.co.nz", "globe and mail",
           "financial post", "cbc", "national post", "the times", "telegraph", "independent",
           "japan times", "asahi", "yomiuri", "kyodo", "le monde", "handelsblatt",
           "frankfurter", "swissinfo", "neue zurcher", "nzz", "the national", "cnn",
           "new york times", "washington post", "forbes", "business insider", "sky news"],
}
PESO_FONTE_PADRAO = 0.30
PESO_FONTE_MIN_FALA = 0.60   # limiar PROVISORIO: abaixo disto, fala reproduzida nao vota

# -------------------------------------------------------------- deduplicacao (regra declarada)
LIMIAR_JACCARD = 0.70
N_ASSINATURA = 8
VAZIAS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "as", "at", "by", "with",
    "from", "is", "are", "was", "were", "be", "been", "after", "over", "amid", "up", "down",
    "new", "its", "it", "that", "this", "than", "but", "not", "no", "into", "about", "more",
    "most", "his", "her", "their", "they", "he", "she", "we", "you", "will", "would", "could",
    "should", "may", "can", "has", "have", "had", "who", "what", "why", "how", "when",
    "video", "live", "update", "updates", "analysis", "opinion", "exclusive", "watch", "read",
    "news", "latest", "report", "reports", "says", "said", "say",
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


def limpa_html(t: str) -> str:
    return H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or ""))).strip()


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
        out.append({"titulo": titulo, "link": campo("link"), "publicado": campo("pubDate"),
                    "fonte": fonte, "resumo": limpa_html(campo("description") or "")[:400]})
    return out


def data_de(pub):
    try:
        d = parsedate_to_datetime(pub)
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def sem_acento(t: str) -> str:
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


def peso_da_fonte(fonte: str) -> float:
    """Peso do VEICULO (credibilidade), separado do peso da ORIGEM (tipo de fala)."""
    f = sem_acento(fonte or "").lower()
    for peso in (1.00, 0.80, 0.60):
        if any(k in f for k in PESO_FONTE[peso]):
            return peso
    return PESO_FONTE_PADRAO


def palavras_de(titulo: str, fonte: str) -> list:
    """Titulo normalizado: minusculas, sem acento, sem pontuacao, sem o nome do veiculo,
    sem palavras vazias. E a materia-prima da deduplicacao."""
    t = re.sub(r"[^a-z0-9 ]+", " ", sem_acento(titulo or "").lower())
    tokens_fonte = {w for w in re.split(r"[^a-z0-9]+", sem_acento(fonte or "").lower()) if len(w) > 2}
    return [p for p in t.split() if len(p) > 2 and p not in VAZIAS and p not in tokens_fonte]


def assinatura_de(palavras: list) -> tuple:
    """As 8 palavras mais longas (N_ASSINATURA), ordenadas — atalho O(1) para titulo identico."""
    return tuple(sorted(sorted(set(palavras), key=lambda p: (-len(p), p))[:N_ASSINATURA]))


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def dirigente_no_texto(texto: str, moeda: str) -> str | None:
    """Nome do dirigente citado, ou None. Na imprensa o sobrenome sozinho nao basta:
    exige nome completo, ou sobrenome + sigla do banco, ou sobrenome + cargo."""
    D = DIRIGENTES.get(moeda) or {}
    t = sem_acento(texto or "").lower()
    tem_contexto = (any(re.search(r"\b%s\b" % re.escape(s), t) for s in D.get("siglas", []))
                    or any(c in t for c in CARGOS))
    for completo, sobrenome in D.get("nomes", []):
        if completo in t:
            return completo.title()
        if tem_contexto and re.search(r"\b%s\b" % re.escape(sobrenome), t):
            return sobrenome.title()
    return None


def tem_verbo_de_fala(texto: str) -> bool:
    t = sem_acento(texto or "").lower()
    return any(re.search(r"\b%s\b" % re.escape(v), t) for v in VERBOS_FALA)


def classifica_origem(titulo: str, resumo: str, fonte: str, moeda: str) -> dict:
    """imprensa_com_fala (0,4) exige as TRES coisas: dirigente nomeado, verbo de fala e
    veiculo com peso >= PESO_FONTE_MIN_FALA. Faltando qualquer uma, e manchete (0,0):
    contexto, nao voto."""
    texto = "%s. %s" % (titulo or "", resumo or "")
    nome = dirigente_no_texto(texto, moeda)
    verbo = tem_verbo_de_fala(texto)
    pf = peso_da_fonte(fonte)
    if nome and verbo and pf >= PESO_FONTE_MIN_FALA:
        return {"origem": "imprensa_com_fala", "peso": PESO_ORIGEM["imprensa_com_fala"],
                "orador_identificado": nome, "peso_fonte": pf, "motivo": None}
    if nome and verbo:
        motivo = "veiculo de peso %.2f — abaixo do limiar provisorio %.2f" % (pf, PESO_FONTE_MIN_FALA)
    elif nome:
        motivo = "dirigente citado (%s) sem verbo de fala no titulo ou resumo" % nome
    elif verbo:
        motivo = "verbo de fala sem dirigente nomeado"
    else:
        motivo = "sem dirigente nomeado e sem verbo de fala"
    return {"origem": "manchete", "peso": PESO_ORIGEM["manchete"], "orador_identificado": nome,
            "peso_fonte": pf, "motivo": motivo}


def classifica(titulo: str) -> str | None:
    t = titulo.lower()
    if any(k in t for k in ALTA):
        return "alta"
    if any(k in t for k in CORTE):
        return "corte"
    if any(k in t for k in MANTEM):
        return "mantem"
    return None


def agrupa(itens: list) -> tuple:
    """(B) Um evento por noticia. Agrupa por JACCARD >= LIMIAR_JACCARD (0,70) sobre as
    palavras normalizadas, com atalho pela assinatura das 8 palavras mais longas.
    Devolve (grupos, n_duplicatas)."""
    grupos = []
    for it in itens:
        P = set(it["_palavras"])
        alvo = None
        for g in grupos:
            if (it["_assinatura"] and it["_assinatura"] == g["assinatura"]) or jaccard(P, g["palavras"]) >= LIMIAR_JACCARD:
                alvo = g
                break
        if alvo is None:
            grupos.append({"assinatura": it["_assinatura"], "palavras": P, "membros": [it]})
        else:
            alvo["membros"].append(it)
            alvo["palavras"] |= P
    dupes = sum(len(g["membros"]) - 1 for g in grupos)
    return grupos, dupes


def representa(g: dict) -> dict:
    """Representante = a fonte de MAIOR peso do grupo (regra do dono). Mas a ORIGEM do evento
    e a MAIOR entre os membros: se qualquer republicacao traz a fala do dirigente, o evento
    tem fala — nao se perde o voto porque a agencia grande publicou so a manchete."""
    membros = sorted(g["membros"], key=lambda x: (-x["peso_fonte"], -x["peso"], x["quando_utc"]))
    r = dict(membros[0])
    melhor = max(membros, key=lambda x: (x["peso"], x["peso_fonte"]))
    if melhor["peso"] > r["peso"]:
        r["origem"] = melhor["origem"]
        r["peso"] = melhor["peso"]
        r["orador_identificado"] = melhor["orador_identificado"]
        r["motivo_origem"] = "fala trazida por outra fonte do mesmo evento (%s)" % melhor["fonte"]
        r["fala_em"] = melhor["fonte"]
    r["n_no_grupo"] = len(membros)
    r["duplicatas"] = [{"fonte": m["fonte"], "titulo": m["titulo"][:120]} for m in membros[1:]][:6]
    for k in ("_palavras", "_assinatura"):
        r.pop(k, None)
    r["assinatura"] = list(g["assinatura"])
    return r


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    inicio = agora - dt.timedelta(hours=JANELA_H)
    print("=" * 92)
    print("NOTICIAS — origem, peso e deduplicacao por moeda (Google News RSS), ultimas %d h" % JANELA_H)
    print("=" * 92)
    saida, erros = {}, []
    for moeda, consultas in CONSULTAS.items():
        vistos_link, brutos_moeda = set(), []
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
                if not it.get("link") or it["link"] in vistos_link:
                    continue
                vistos_link.add(it["link"])
                c = classifica_origem(it["titulo"], it.get("resumo") or "", it["fonte"], moeda)
                pal = palavras_de(it["titulo"], it["fonte"])
                brutos_moeda.append({
                    "titulo": it["titulo"][:160], "fonte": it["fonte"][:40], "link": it["link"],
                    "quando_utc": d.astimezone(dt.timezone.utc).isoformat(),
                    "classe": classifica(it["titulo"]),
                    "origem": c["origem"], "peso": c["peso"],
                    "orador_identificado": c["orador_identificado"],
                    "peso_fonte": c["peso_fonte"], "motivo_origem": c["motivo"],
                    "_palavras": pal, "_assinatura": assinatura_de(pal)})
            time.sleep(PAUSA_S)

        brutos_moeda.sort(key=lambda x: x["quando_utc"], reverse=True)
        grupos, dupes = agrupa(brutos_moeda)
        unicos = [representa(g) for g in grupos]
        unicos.sort(key=lambda x: x["quando_utc"], reverse=True)

        # CONTEXTO: todos os eventos unicos. E o que a aba de noticias mostra. Nao vota.
        cont = {"alta": 0, "corte": 0, "mantem": 0}
        for it in unicos:
            if it["classe"]:
                cont[it["classe"]] += 1
        # VOTO: so os itens com peso > 0 (imprensa_com_fala). Manchete NAO vota.
        falas = [it for it in unicos if it["peso"] > 0]
        cont_v = {"alta": 0, "corte": 0, "mantem": 0}
        for it in falas:
            if it["classe"]:
                cont_v[it["classe"]] += 1
        direcao_v = ("SOBE" if cont_v["alta"] > cont_v["corte"] else
                     "CORTA" if cont_v["corte"] > cont_v["alta"] else
                     "MANTEM" if cont_v["mantem"] else None)
        voto = {"vota": bool(falas) and direcao_v is not None,
                "peso": PESO_ORIGEM["imprensa_com_fala"] if falas else 0.0,
                "origem": "imprensa_com_fala" if falas else "manchete",
                "direcao": direcao_v, "n_falas": len(falas),
                "oradores": sorted({it["orador_identificado"] for it in falas if it["orador_identificado"]}),
                "fontes": sorted({it["fonte"] for it in falas})[:6],
                "rotulo": (ROTULO_CONTEXTO if moeda in BANCO_BLOQUEIA and not falas else
                           ("fala de dirigente reproduzida pela imprensa — peso 0,4" if falas else
                            "so manchete: contexto, nao voto"))}

        # POR QUE nao votou: a contagem roda sobre TODOS os eventos unicos, nao so os 14 que
        # aparecem na tela. E a resposta a pergunta do dono: "quantas falas com dirigente
        # nomeado existem hoje para o AUD?"
        cita = len([it for it in unicos if it["orador_identificado"]])
        motivos = {"sem dirigente nomeado": 0, "dirigente citado, sem verbo de fala": 0,
                   "dirigente e verbo, veiculo abaixo do limiar": 0}
        for it in unicos:
            mo = it.get("motivo_origem") or ""
            if not it["orador_identificado"]:
                motivos["sem dirigente nomeado"] += 1
            elif mo.startswith("veiculo de peso"):
                motivos["dirigente e verbo, veiculo abaixo do limiar"] += 1
            elif mo.startswith("dirigente citado"):
                motivos["dirigente citado, sem verbo de fala"] += 1

        # os itens que VOTAM nunca sao cortados pelo teto de exibicao
        resto = [it for it in unicos if it["peso"] <= 0]
        itens_saida = falas + resto[:max(0, MAX_POR_MOEDA - len(falas))]

        saida[moeda] = {
            "itens": itens_saida, "n_72h": len(brutos_moeda), "n_unicos": len(unicos),
            "duplicatas_removidas": dupes,
            "contagem": cont,
            "contagem_nota": "CONTEXTO: conta todos os eventos unicos das 72 h. Nao e voto — "
                             "manchete tem peso 0,0 na hierarquia de origem.",
            "contagem_voto": cont_v,
            "voto": voto,
            "banco_bloqueia_automacao": moeda in BANCO_BLOQUEIA,
            "rotulo_contexto": ROTULO_CONTEXTO if moeda in BANCO_BLOQUEIA else None,
            "por_origem": {"imprensa_com_fala": len(falas), "manchete": len(unicos) - len(falas)},
            "n_cita_dirigente": cita,
            "motivos_sem_voto": motivos,
            "inclinacao_por_manchete": ("alta" if cont["alta"] > cont["corte"] else
                                        "corte" if cont["corte"] > cont["alta"] else
                                        "mantem" if cont["mantem"] else "none")}
        print("  %-4s brutos %3d · unicos %3d · duplicatas %3d · citam dirigente %2d · com fala %2d "
              "· manchete %3d · voto %s"
              % (moeda, len(brutos_moeda), len(unicos), dupes, cita, len(falas),
                 len(unicos) - len(falas), (voto["direcao"] or "SEM VOTO")))
        for it in falas[:3]:
            print("       FALA %-9s %-22s %s" % (it["orador_identificado"] or "-", it["fonte"][:22],
                                                 it["titulo"][:60]))
        for it in resto[:2]:
            print("       ctx  %-32s %s" % (it["fonte"][:32], it["titulo"][:60]))

    if not any(v["itens"] for v in saida.values()):
        print("  !! nenhuma manchete — arquivo anterior preservado")
        sys.exit(1)

    print()
    print("  RESUMO — quantos itens VOTAM por moeda (peso 0,4 exige dirigente nomeado):")
    for m, v in saida.items():
        print("   %-4s unicos %3d · duplicatas removidas %3d · citam dirigente %2d · FALAS QUE VOTAM %2d"
              % (m, v["n_unicos"], v["duplicatas_removidas"], v["n_cita_dirigente"],
                 v["por_origem"]["imprensa_com_fala"]))
        for k, q in v["motivos_sem_voto"].items():
            if q:
                print("          %-44s %3d" % (k, q))

    rel = {"gerado_em": agora.isoformat(), "fonte": "Google News RSS (busca), em ingles",
           "janela_h": JANELA_H,
           "aviso": "Contagem de expressao na manchete, nao leitura. Manchete tem peso 0,0: e "
                    "CONTEXTO, nunca voto. So vota o item 'imprensa_com_fala' — dirigente "
                    "nomeado, verbo de fala e veiculo acima do limiar — e com peso 0,4.",
           "hierarquia_pesos": PESO_ORIGEM,
           "hierarquia_nota": "discurso_oficial e comunicado_ata nascem em bc_discursos.py (site do "
                              "proprio banco). Aqui nascem imprensa_com_fala (0,4) e manchete (0,0).",
           "regra_deduplicacao": {"metodo": "Jaccard sobre palavras normalizadas",
                                  "limiar_jaccard": LIMIAR_JACCARD,
                                  "atalho": "assinatura das %d palavras mais longas" % N_ASSINATURA,
                                  "normalizacao": "minusculas, sem acento, sem pontuacao, sem o nome "
                                                  "do veiculo, sem palavras vazias",
                                  "representante": "fonte de maior peso; a origem do grupo e a maior "
                                                   "entre os membros",
                                  "provisorio": True},
           "peso_fonte": {"tabela": PESO_FONTE, "padrao": PESO_FONTE_PADRAO,
                          "minimo_para_fala": PESO_FONTE_MIN_FALA, "provisorio": True},
           "buraco_declarado": {"moedas": sorted(BANCO_BLOQUEIA), "bancos": BANCO_BLOQUEIA,
                                "rotulo": ROTULO_CONTEXTO,
                                "nota": "sem fala de dirigente, a dimensao de texto destas moedas fica "
                                        "SEM VOTO — nao com voto fraco. Silencio nao e voto."},
           "moedas": saida, "erros": erros}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
