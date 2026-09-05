# -*- coding: utf-8 -*-
"""DISCURSOS DOS BANCOS CENTRAIS — a camada de TEXTO, com a ORIGEM DE CADA FALA gravada.

SUCEDE fed_discursos.py (03/set), que so lia o Fed. O Eduardo pediu (04/set): "para todos
os paises". Testado feed por feed:

    USD  Fed        RSS de discursos + RSS de politica monetaria       200
    EUR  BCE        RSS de imprensa (traz discursos e decisoes)       200
    GBP  BoE        RSS de discursos + RSS de noticias                200
    JPY  BoJ        RSS "what's new" (discursos, comunicados)         200
    CAD  BoC        RSS de discursos + de comunicados (RDF 1.0)       200
    AUD  RBA        403 — bloqueia automacao por politica propria     NAO CONECTADO
    NZD  RBNZ       403 — idem                                        NAO CONECTADO
    CHF  SNB        feed nao encontrado (404 nas rotas conhecidas)    NAO CONECTADO

CONSERTO DE 05/set — A ORIGEM DA FALA (item 2 da revisao do dono)
    O painel mostrava "38 discursos" para o AUD tendo ZERO fala do RBA no arquivo, e exibia
    cerimonia de cedula do BoC ("Unveiling of Vertical $20 Bank Note") como se fosse fala de
    politica monetaria. Duas causas, dois consertos:

    1. HIERARQUIA DE PESO gravada no proprio item, para o sentimento aplicar:
         discurso_oficial   peso 1,0  fala de dirigente no site do banco central
         comunicado_ata     peso 1,0  comunicado, ata, relatorio de politica, coletiva
         imprensa_com_fala  peso 0,4  imprensa reproduzindo fala de dirigente NOMEADO
         manchete           peso 0,0  opiniao/analise/manchete sem fala: so contexto
       Este arquivo so produz as duas primeiras (sao paginas do proprio banco). As duas
       ultimas nascem em noticias.py. Cada item sai com "origem", "peso" e
       "orador_identificado" (nome do dirigente ou null).

    2. FILTRO DE ASSUNTO. Lista de EXCLUSAO (cedula, aniversario, homenagem, premio, museu,
       nomeacao administrativa) e lista de INCLUSAO (politica monetaria, inflacao, juros,
       economia e perspectivas, mercado de trabalho, estabilidade financeira). Item cujo
       titulo bate na exclusao e nao bate na inclusao e DESCARTADO com o motivo gravado.
       Item que nao bate em nada so sobrevive se vier de pagina de comunicado; senao,
       descartado — tambem com motivo. Os descartes ficam gravados em "descartados", para
       auditoria: nada some em silencio.

CONSERTO DE 05/set — O VEREDITO POR ORADOR (prioridade 3 da revisao do dono)
    A contagem de palavras chamava de "hawkish" o Waller dizendo que apoiaria MANTER, o Warsh
    falando em preservar liberdade para decidir e o Barr sendo hawkish CONDICIONAL. Entra o
    modulo leitor_falas.py, que le cada frase por REGRA — negacao, condicao, tempo verbal e
    sujeito — e devolve um veredito por orador, com o trecho, o motivo, a data e o link:

        Waller  manutenção        Barr  alta condicional        Warsh  indeterminado

    Onde fica gravado:  resumo_por_moeda[MOEDA]["veredito_por_orador"]  (uma linha por orador)
                        veredito_por_orador (raiz, o mesmo indexado por moeda)
                        item["veredito_leitor"]                        (a fala especifica)
                        leitor_falas (raiz: selo, regras e o que seria uma validacao)

    REGRA DURA: o veredito NAO VOTA. Sai com selo "experimental — contexto, nao vota" em toda
    parte e nao entra em soma nenhuma, exatamente como a geopolitica. So passa a votar depois
    de validado contra o que o banco realmente fez — o criterio esta no cabecalho de
    leitor_falas.py. Sem rede: "python bc_discursos.py --reaplica-leitor" recalcula o veredito
    sobre o arquivo ja gravado.

O QUE FAZ — e o que NAO faz
    FAZ:  baixa cada discurso/comunicado, separa em frases e guarda as que carregam postura
          de politica ("I would", "appropriate to", "hold", "raise", "cut"...). Conta
          marcadores hawkish e dovish. E EXTRACAO mecanica, rotulada como tal. Em cima disso,
          o leitor_falas da o veredito por orador — que informa, mas nao vota.
    NAO:  nao "entende" o discurso. A contagem e um indice grosseiro para apontar QUAL texto
          ler, e fica no arquivo so como rastro de auditoria (contagem x leitura).

    As expressoes sao em ingles: os cinco bancos conectados publicam em ingles.
    Nada aqui sobrescreve dado bom com vazio: se nenhuma fonte responder, sai com codigo 1
    e preserva o arquivo anterior.
    Todo limiar novo deste conserto e PROVISORIO (marcado no JSON), para o backtest calibrar.
"""
from __future__ import annotations

import datetime as dt
import html as H
import io
import json
import os
import re
import sys
import unicodedata
import urllib.request

# O LEITOR DE FALAS (05/set) le a frase por contexto — negacao, condicao, tempo e sujeito —
# no lugar da contagem de palavras. Ele NAO VOTA: entra como contexto, com selo.
from leitor_falas import (SELO as SELO_LEITOR, VALIDACAO_ACEITAVEL, VERSAO as VERSAO_LEITOR,
                          VEREDITOS, REGRAS_RESUMO, vereditos_por_moeda)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "bc_discursos.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
DIAS = 21
MAX_POR_BANCO = 5

# ---------------------------------------------------------------- hierarquia de peso da fala
# Gravada no item para o sentimento nao precisar adivinhar de onde veio o texto.
# GEMEA: a mesma tabela vive em noticias.py (que produz as duas ultimas linhas).
PESO_ORIGEM = {
    "discurso_oficial": 1.0,    # fala de dirigente no site do banco central
    "comunicado_ata": 1.0,      # comunicado, ata, relatorio de politica monetaria, coletiva
    "imprensa_com_fala": 0.4,   # imprensa reproduzindo fala de dirigente nomeado
    "manchete": 0.0,            # opiniao, analise, manchete sem fala: so contexto
}

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
# O prefixo "not connected" e CHAVE DE MAQUINA: sentimento.py testa startswith("not connected").
# O texto legivel em portugues sai em "status_fontes_texto".
NAO_CONECTADO = {"AUD": "RBA returns 403 to automation", "NZD": "RBNZ returns 403 to automation",
                 "CHF": "SNB feed not found (404 on the known routes)"}
NAO_CONECTADO_PT = {
    "AUD": "nao conectado: o RBA devolve 403 para automacao",
    "NZD": "nao conectado: o RBNZ devolve 403 para automacao",
    "CHF": "nao conectado: o SNB nao publica feed nas rotas conhecidas (404)",
}

# ------------------------------------------------------------------ quem e dirigente de quem
# Serve para identificar o ORADOR. Sobrenome basta: estamos dentro do site do proprio banco.
# GEMEA: noticias.py tem a lista de RBA, RBNZ e SNB (os tres que bloqueiam robo) com a mesma
# funcao, mas la a checagem e mais dura porque o texto vem da imprensa.
DIRIGENTES = {
    "Fed": ["Powell", "Jefferson", "Barr", "Bowman", "Waller", "Cook", "Kugler", "Williams",
            "Logan", "Bostic", "Goolsbee", "Kashkari", "Musalem", "Schmid", "Hammack",
            "Collins", "Barkin", "Daly", "Harker", "Miran"],
    "ECB": ["Lagarde", "de Guindos", "Lane", "Schnabel", "Cipollone", "Elderson", "Nagel",
            "Villeroy", "Panetta", "Knot", "Kazimir", "Simkus", "Centeno", "Escriva",
            "Holzmann", "Vujcic", "Rehn", "Muller", "Kazaks", "Wunsch", "Stournaras",
            "Makhlouf", "Herodotou", "Scicluna", "Reinesch", "Vasle", "Buch"],
    "BoE": ["Bailey", "Ramsden", "Pill", "Breeden", "Lombardelli", "Greene", "Mann",
            "Dhingra", "Taylor", "Haskel", "Woods", "Bhattacharya"],
    "BoJ": ["Ueda", "Himino", "Uchida", "Adachi", "Nakamura", "Noguchi", "Nakagawa",
            "Takata", "Tamura", "Koeda", "Masu", "Kato"],
    "BoC": ["Macklem", "Rogers", "Kozicki", "Gravelle", "Vincent", "Mendes", "Kelly"],
}
# Palavra que aparece em prefixo de titulo e NAO e nome de gente.
PREFIXO_NAO_E_PESSOA = {"press", "conference", "statement", "report", "minutes", "summary",
                        "highlights", "monetary", "policy", "bank", "interview", "panel",
                        "remarks", "speech", "opening", "annual", "review", "note", "notes",
                        "update", "outlook", "decision", "announcement", "webcast", "webcasts",
                        "the", "a", "an", "and", "of", "for", "on", "in"}
CARGOS = ["governor", "deputy governor", "senior deputy", "chair", "chairman", "president",
          "vice president", "vice-president", "board member", "chief economist",
          "member of the executive board", "member of the governing council", "mpc member"]

# ---------------------------------------------------------------------- filtros de ASSUNTO
# EXCLUSAO: cerimonia e vida institucional. Nao e fala de politica monetaria.
EXCLUSAO_ASSUNTO = {
    "cedula": ["bank note", "banknote", "bank-note", "currency note", "polymer note",
               "unveiling", "unveil", "new note", "note series"],
    "aniversario": ["anniversary", "centenary", "birthday", "years of the bank"],
    "homenagem": ["tribute", "in memoriam", "memorial", "farewell", "obituary", "eulogy",
                  "honouring", "honoring", "in honour of", "in honor of"],
    "premio": ["award", "prize", "medal", "laureate", "scholarship"],
    "museu": ["museum", "exhibition", "gallery", "art collection", "heritage"],
    "nomeacao administrativa": ["appointment", "appointed", "reappointment", "names new",
                                "board of directors", "staff change", "retirement of",
                                "resignation", "steps down", "term of office", "swearing-in",
                                "takes office", "new head of"],
}
# INCLUSAO: o que E politica monetaria e adjacencias que o dono listou.
INCLUSAO_ASSUNTO = {
    "politica monetaria": ["monetary policy", "policy decision", "policy rate", "bank rate",
                           "cash rate", "official cash rate", "federal funds", "rate decision",
                           "policy stance", "quantitative tightening", "quantitative easing",
                           "balance sheet policy", "asset purchase"],
    "inflacao": ["inflation", "price stability", "consumer price", "cpi", "disinflation",
                 "price pressure", "wage growth"],
    "juros": ["interest rate", "rate cut", "rate hike", "rate increase", "rate reduction",
              "restrictive", "accommodative", "neutral rate", "easing cycle"],
    "economia e perspectivas": ["economic outlook", "outlook for", "economic activity",
                                "growth outlook", "gdp", "projections", "forecast",
                                "the economy", "economic conditions", "economy", "economic",
                                "recession", "productivity"],
    "mercado de trabalho": ["labour market", "labor market", "employment", "unemployment",
                            "payrolls", "jobs report"],
    "estabilidade financeira": ["financial stability", "financial system", "banking system",
                                "systemic risk", "stress test", "financial conditions"],
}
# Quando o TITULO e neutro, o corpo decide — mas so com densidade: um "inflation" solto num
# discurso de cerimonia nao vale. Limiar PROVISORIO, a calibrar pelo backtest.
FORTES_CORPO = ["monetary policy", "policy rate", "interest rate", "inflation", "bank rate",
                "cash rate", "federal funds", "labour market", "labor market"]
MIN_FORTES_CORPO = 3

# Titulo que denuncia COMUNICADO/ATA/COLETIVA (peso igual ao do discurso, rotulo diferente).
COMUNICADO_TITULO = ["press conference", "opening statement", "monetary policy report",
                     "monetary policy summary", "monetary policy statement",
                     "monetary policy decisions", "policy rate announcement",
                     "rate announcement", "statement on monetary policy",
                     "summary of opinions", "minutes", "fomc statement", "press release",
                     "outlook for economic activity", "communique", "communiqué",
                     "financial stability report", "policy interest rate"]

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


def sem_acento(t: str) -> str:
    """Sem isto, 'Boris Vujcic' nao casa com 'Boris Vujcic' escrito com carons, e o orador
    sai como null — o item cai de discurso_oficial para comunicado_ata sem motivo real."""
    t = unicodedata.normalize("NFKD", t or "")
    return "".join(c for c in t if not unicodedata.combining(c))


def chave_titulo(t: str) -> str:
    """Chave de deduplicacao por TITULO, para o caso em que o mesmo discurso sai em duas
    paginas do banco com links diferentes.

    Ate 05/set a deduplicacao aqui era so por link identico. Era um furo real: o BoC publicou
    a MESMA cerimonia da cedula de $20 em duas paginas ("Unveiling of Vertical $20 Bank Note"
    e "Unveiling Canada's new $20 bank note - Speech"), com links distintos, e as duas
    entraram — so nao viraram fala de politica monetaria porque o filtro de ASSUNTO as pegou
    depois. Sem o filtro, teriam contado duas vezes. A rede de seguranca por titulo existia
    so la na frente, no sentimento.py; agora existe aqui tambem.

    Normalizacao: minusculas, sem acento, so letra e numero, e sem o sufixo de veiculo depois
    de travessao/hifen longo (" - Bank of England", " — Speech").
    """
    t = sem_acento((t or "").lower())
    t = re.split(r"\s+[-–—]\s+", t)[0]
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def contem(termo: str, texto: str) -> bool:
    """Busca com fronteira de palavra quando o termo comeca e termina em letra/numero.
    Sem isso, 'hike' casava dentro de outra palavra e 'jobs' dentro de 'jobsite'."""
    if termo[:1].isalnum() and termo[-1:].isalnum():
        return re.search(r"\b%s\b" % re.escape(termo), texto) is not None
    return termo in texto


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


# PROVISORIO (05/set): abaixo desta fracao de caracteres legiveis o "texto" nao e texto.
PROPORCAO_MINIMA_LEGIVEL = 0.80


def proporcao_legivel(texto: str) -> float:
    """Fracao de caracteres que sao letra ASCII, digito, espaco ou pontuacao comum.

    POR QUE EXISTE: o BCE publica parte dos discursos em PDF, e `texto_da_pagina` apenas tira
    tags de HTML — num PDF ela devolve o binario inteiro. Medido em 05/set: o discurso do Lane
    (.pdf) entrou como 576.795 "caracteres" com 34% de conteudo legivel, virou 60 "frases" de
    lixo binario dentro da janela de 40 a 420 caracteres, e o veredito saiu "indeterminado —
    nenhuma frase de postura foi extraida do texto", como se o homem nao tivesse falado de
    juro. As outras 12 falas do mesmo dia ficaram entre 0,992 e 1,000. O corte de 0,80 separa
    os dois grupos com folga larga e e PROVISORIO."""
    if not texto:
        return 0.0
    comuns = set(chr(32) + ".,;:'()-" + chr(34) + chr(10) + chr(9))
    ok = sum(1 for c in texto
             if (c.isalpha() and ord(c) < 128) or c.isdigit() or c in comuns)
    return ok / len(texto)


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


def assunto_de(titulo: str, texto: str) -> dict:
    """Decide se o item E politica monetaria. Devolve o veredito COM as provas, para auditoria.

    Regra (provisoria, a calibrar):
      titulo bate na exclusao e NAO bate na inclusao  -> "excluido"
      titulo bate na inclusao                          -> "politica_monetaria"
      titulo neutro, corpo com >= 3 termos fortes      -> "politica_monetaria" (pelo corpo)
      resto                                            -> "neutro"
    """
    tl, cl = titulo.lower(), texto.lower()
    exc = [tema for tema, termos in EXCLUSAO_ASSUNTO.items() if any(contem(k, tl) for k in termos)]
    inc = [tema for tema, termos in INCLUSAO_ASSUNTO.items() if any(contem(k, tl) for k in termos)]
    fortes = sum(len(re.findall(r"\b%s\b" % re.escape(k), cl)) for k in FORTES_CORPO)
    if exc and not inc:
        return {"veredito": "excluido", "temas_excluidos": exc, "temas_incluidos": [],
                "termos_fortes_no_corpo": fortes,
                "motivo": "assunto excluido no titulo (%s) e nenhum tema de politica monetaria" % ", ".join(exc)}
    if inc:
        return {"veredito": "politica_monetaria", "temas_excluidos": exc, "temas_incluidos": inc,
                "termos_fortes_no_corpo": fortes, "motivo": "titulo bate em: %s" % ", ".join(inc)}
    if fortes >= MIN_FORTES_CORPO:
        return {"veredito": "politica_monetaria", "temas_excluidos": exc, "temas_incluidos": ["pelo corpo"],
                "termos_fortes_no_corpo": fortes,
                "motivo": "titulo neutro, mas %d termos fortes no corpo (minimo %d)" % (fortes, MIN_FORTES_CORPO)}
    return {"veredito": "neutro", "temas_excluidos": exc, "temas_incluidos": [],
            "termos_fortes_no_corpo": fortes,
            "motivo": "titulo neutro e so %d termos fortes no corpo (minimo %d)" % (fortes, MIN_FORTES_CORPO)}


def orador_identificado_de(titulo: str, texto: str, banco: str) -> str | None:
    """Nome do dirigente, ou None. Nunca devolve o nome do BANCO no lugar da pessoa — era
    exatamente isso que fazia 'BoC' aparecer como se fosse um orador.

    Ordem: padrao explicito ("remarks by X") > nome conhecido no titulo > PREFIXO do titulo
    (BCE "Nome: assunto", Fed "Sobrenome, assunto") > nome conhecido no corpo. O prefixo vem
    antes do corpo de proposito: com a ordem invertida, "Warsh, In Our Time" era atribuido a
    Schmid, so porque Schmid aparecia citado nos primeiros paragrafos.
    """
    t_sa = sem_acento(titulo)
    m = re.search(r"(?:speech|remarks|lecture|address|keynote|panel)\s+by\s+"
                  r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3})", t_sa)
    if m:
        return m.group(1).strip(" .,-")
    tl = t_sa.lower()
    for nome in DIRIGENTES.get(banco, []):
        if contem(sem_acento(nome).lower(), tl):
            return nome
    pref = None
    if ":" in titulo:
        pref = titulo.split(":")[0].strip()
    elif banco == "Fed" and "," in titulo:
        pref = titulo.split(",")[0].strip()
    if pref and 3 <= len(pref) <= 40:
        p_sa = sem_acento(pref)
        palavras = p_sa.split()
        # "Press Conference: Policy Rate Announcement" tem prefixo capitalizado e NAO e gente:
        # o prefixo so vale se nenhuma palavra dele for de documento/cerimonia.
        generico = (any(contem(k, p_sa.lower()) for k in COMUNICADO_TITULO)
                    or any(w.lower() in PREFIXO_NAO_E_PESSOA for w in palavras))
        if not generico and 1 <= len(palavras) <= 4 and all(
                re.match(r"^[A-Z][A-Za-z.'\-]*$", w) for w in palavras):
            return pref
    cabeca = sem_acento(texto[:2000]).lower()
    for nome in DIRIGENTES.get(banco, []):
        if contem(sem_acento(nome).lower(), cabeca):
            return nome
    return None


def classifica_origem(titulo: str, texto: str, tipo: str, banco: str) -> dict:
    """Origem, peso e orador — a resposta da pergunta 'de onde saiu esta fala?'.

    'tipo' vem do FEED: "statement" e feed de comunicado; "speech" e feed de discurso.
    Item de assunto neutro so sobrevive se veio de pagina de comunicado (regra do dono)."""
    a = assunto_de(titulo, texto)
    nome = orador_identificado_de(titulo, texto, banco)
    tl = titulo.lower()
    e_comunicado = tipo == "statement" or any(contem(k, tl) for k in COMUNICADO_TITULO)

    if a["veredito"] == "excluido":
        return {"manter": False, "motivo": a["motivo"], "assunto": a, "orador_identificado": nome}
    if a["veredito"] == "neutro" and not e_comunicado:
        return {"manter": False,
                "motivo": "assunto neutro fora de pagina de comunicado — %s" % a["motivo"],
                "assunto": a, "orador_identificado": nome}

    if e_comunicado:
        origem, porque = "comunicado_ata", ("feed de comunicado do banco" if tipo == "statement"
                                            else "titulo de comunicado/ata/coletiva")
    elif nome:
        origem, porque = "discurso_oficial", "fala assinada por %s no site do banco" % nome
    else:
        # Pagina do proprio banco, assunto de politica, mas sem orador atribuivel: nao da para
        # chamar de "fala de dirigente". Vale como comunicado — mesmo peso, rotulo honesto.
        origem, porque = "comunicado_ata", "pagina oficial sem orador identificavel"
    return {"manter": True, "origem": origem, "peso": PESO_ORIGEM[origem],
            "orador_identificado": nome, "origem_motivo": porque, "assunto": a}


def aplica_leitor(itens: list, resumo: dict) -> dict:
    """Roda o LEITOR DE FALAS e grava o veredito por orador em cada moeda.

    Duas gravacoes, para nada ficar sem rastro:
      resumo[MOEDA]["veredito_por_orador"]  uma linha por orador, com motivo, trecho, data e link
      item["veredito_leitor"]               o veredito daquela fala especifica

    A contagem antiga (marcadores_hawkish / marcadores_dovish) CONTINUA no item de proposito:
    ela vira rastro de auditoria, para o dono comparar contagem x leitura. O que a interface
    mostra e o veredito, e ele NAO VOTA.
    """
    vereditos = vereditos_por_moeda({"itens": itens}, anotar_itens=True)
    for m in resumo:
        resumo[m]["veredito_por_orador"] = vereditos.get(m, [])
    return vereditos


def bloco_leitor() -> dict:
    """O cabecalho do leitor no JSON: selo, versao, regras e o que seria uma validacao."""
    return {"versao": VERSAO_LEITOR,
            "selo": SELO_LEITOR,
            "vota": False,
            "vereditos_possiveis": list(VEREDITOS),
            "regras": REGRAS_RESUMO,
            "validacao_aceitavel": VALIDACAO_ACEITAVEL,
            "nota": "classificador por REGRA (negação, condição, tempo verbal e sujeito). "
                    "É CONTEXTO: não entra em nenhuma soma e não move nenhuma leitura, "
                    "exatamente como a geopolítica. A contagem de marcadores segue gravada no "
                    "item apenas como rastro de auditoria."}


def imprime_vereditos(vereditos: dict) -> None:
    if not vereditos:
        return
    print()
    print("  VEREDITO POR ORADOR (leitor de falas — %s):" % SELO_LEITOR)
    for moeda in sorted(vereditos):
        for l in vereditos[moeda]:
            print("   . %-4s %-14s %-18s %s" % (moeda, l["orador"][:14], l["veredito"],
                                                (l["data"] or "-")))


def reaplica_leitor():
    """Reaplica o leitor ao arquivo JA gravado, SEM rede.

    Serve para (a) recalcular o veredito depois de mexer numa regra e (b) preencher o campo
    em maquina sem acesso aos feeds. Nao apaga nada: le, acrescenta e regrava.
    """
    with io.open(SAIDA, encoding="utf-8") as f:
        rel = json.load(f)
    itens = rel.get("itens") or []
    resumo = rel.get("resumo_por_moeda") or {}
    for m in sorted({i.get("moeda") for i in itens if i.get("moeda")}):
        resumo.setdefault(m, {})
    vereditos = aplica_leitor(itens, resumo)
    rel["resumo_por_moeda"] = resumo
    rel["veredito_por_orador"] = vereditos
    rel["leitor_falas"] = bloco_leitor()
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=" * 86)
    print("LEITOR DE FALAS reaplicado ao arquivo existente (sem rede)")
    print("=" * 86)
    imprime_vereditos(vereditos)
    print()
    print("  gravado: %s" % SAIDA)


def main():
    if "--reaplica-leitor" in sys.argv:
        return reaplica_leitor()
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 86)
    print("DISCURSOS DOS BANCOS CENTRAIS — origem, peso e orador de cada fala")
    print("=" * 86)
    saida, descartados, status = [], [], {}
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
            # duplicata por LINK ou por TITULO normalizado: o mesmo discurso sai em duas
            # paginas do banco com URLs diferentes (o BoC fez isso com a cedula de $20)
            k = chave_titulo(titulo)
            if any(x["link"] == it["link"] or chave_titulo(x.get("titulo")) == k
                   for x in saida)                or any(x["link"] == it["link"] or chave_titulo(x.get("titulo")) == k
                      for x in descartados):
                continue
            try:
                txt = texto_da_pagina(busca(it["link"]))
            except Exception as e:
                print("  ! %s: %s" % (it["link"][:70], str(e)[:50]))
                continue
            leg = proporcao_legivel(txt)
            if leg < PROPORCAO_MINIMA_LEGIVEL:
                # nao vira "indeterminado" em silencio: sai como descarte COM o motivo e o
                # numero, para o painel nunca confundir "nao deu para ler" com "nao falou".
                descartados.append({"moeda": moeda, "banco": banco, "tipo_feed": tipo,
                                    "data": d.isoformat(), "titulo": titulo[:160],
                                    "link": it["link"], "orador_identificado": None,
                                    "motivo": ("texto nao legivel (%.0f%% de caracteres "
                                               "legiveis, minimo provisorio %.0f%%) — a pagina "
                                               "provavelmente e PDF e o leitor so sabe tirar "
                                               "tag de HTML"
                                               % (leg * 100, PROPORCAO_MINIMA_LEGIVEL * 100))})
                continue
            c = classifica_origem(titulo, txt, tipo, banco)
            if not c["manter"]:
                descartados.append({"moeda": moeda, "banco": banco, "tipo_feed": tipo,
                                    "data": d.isoformat(), "titulo": titulo[:160],
                                    "link": it["link"], "motivo": c["motivo"],
                                    "orador_identificado": c["orador_identificado"]})
                continue
            ext = frases_de_postura(txt)
            saida.append({"moeda": moeda, "banco": banco, "tipo": tipo, "data": d.isoformat(),
                          "origem": c["origem"], "peso": c["peso"],
                          "orador_identificado": c["orador_identificado"],
                          # "orador" fica por compatibilidade com o painel antigo; quando nao ha
                          # pessoa identificada, mostra o BANCO — e "orador_identificado" e null.
                          "orador": c["orador_identificado"] or banco,
                          "origem_motivo": c["origem_motivo"],
                          "assunto": {"veredito": c["assunto"]["veredito"],
                                      "temas": c["assunto"]["temas_incluidos"],
                                      "termos_fortes_no_corpo": c["assunto"]["termos_fortes_no_corpo"],
                                      "motivo": c["assunto"]["motivo"]},
                          "titulo": titulo[:160], "link": it["link"], "caracteres": len(txt), **ext})
            n += 1
            if n >= MAX_POR_BANCO:
                break
    for m, motivo in NAO_CONECTADO.items():
        status[m] = "not connected: " + motivo

    saida.sort(key=lambda x: x["data"], reverse=True)
    descartados.sort(key=lambda x: x["data"], reverse=True)

    resumo = {}
    for m in sorted(set([s["moeda"] for s in saida] + [x["moeda"] for x in descartados] + list(NAO_CONECTADO))):
        d_of = len([s for s in saida if s["moeda"] == m and s["origem"] == "discurso_oficial"])
        c_at = len([s for s in saida if s["moeda"] == m and s["origem"] == "comunicado_ata"])
        desc = len([x for x in descartados if x["moeda"] == m])
        resumo[m] = {"discurso_oficial": d_of, "comunicado_ata": c_at, "descartados": desc,
                     "itens_que_votam": d_of + c_at,
                     "com_orador_identificado": len([s for s in saida if s["moeda"] == m
                                                     and s.get("orador_identificado")])}

    # VEREDITO POR ORADOR (prioridade 3): le a frase por contexto e grava o veredito por moeda.
    # Anota tambem cada item com "veredito_leitor", para a auditoria bater linha a linha.
    vereditos = aplica_leitor(saida, resumo)

    print("  itens mantidos: %d  ·  descartados: %d" % (len(saida), len(descartados)))
    print()
    print("  %-5s %-18s %-16s %-13s %s" % ("moeda", "discurso_oficial", "comunicado_ata",
                                           "descartados", "votam"))
    for m, r in resumo.items():
        print("  %-5s %-18d %-16d %-13d %d" % (m, r["discurso_oficial"], r["comunicado_ata"],
                                               r["descartados"], r["itens_que_votam"]))
    print()
    for s in saida[:14]:
        print("  %s %-4s %-17s %-12s h=%d d=%d  %s" % (s["data"], s["moeda"], s["origem"],
              (s["orador_identificado"] or "-")[:12], s["marcadores_hawkish"],
              s["marcadores_dovish"], s["titulo"][:44]))
    imprime_vereditos(vereditos)
    if descartados:
        print()
        print("  DESCARTADOS (motivo gravado, nada some em silencio):")
        for x in descartados[:12]:
            print("   x %s %-4s %-46s  %s" % (x["data"], x["moeda"], x["titulo"][:46], x["motivo"][:70]))

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
           "status_fontes_texto": dict(
               {m: ("conectado" if v == "ok" else v) for m, v in status.items() if m not in NAO_CONECTADO},
               **NAO_CONECTADO_PT),
           "aviso": "EXTRACAO mecanica de frases de postura e contagem de expressoes em ingles. A "
                    "contagem NAO e interpretacao: e um indice grosseiro para apontar QUAL texto "
                    "ler, e fica aqui so como rastro. O que se le na tela e o veredito por orador "
                    "do leitor_falas — que e CONTEXTO e NAO VOTA.",
           "hierarquia_pesos": PESO_ORIGEM,
           "hierarquia_nota": "peso gravado no item para o sentimento aplicar. Este arquivo so produz "
                              "discurso_oficial e comunicado_ata (paginas do proprio banco). "
                              "imprensa_com_fala (0,4) e manchete (0,0) nascem em noticias.py.",
           "filtro_assunto": {"inclusao": INCLUSAO_ASSUNTO, "exclusao": EXCLUSAO_ASSUNTO,
                              "termos_fortes_corpo": FORTES_CORPO,
                              "min_termos_fortes_no_corpo": MIN_FORTES_CORPO,
                              "provisorio": True,
                              "nota": "limiar PROVISORIO, a calibrar pelo backtest. Titulo com assunto "
                                      "excluido e sem tema de politica monetaria e descartado; titulo "
                                      "neutro so sobrevive vindo de pagina de comunicado."},
           "resumo_por_moeda": resumo,
           "veredito_por_orador": vereditos,
           "leitor_falas": bloco_leitor(),
           "marcadores": {"hawkish": HAWKISH, "dovish": DOVISH, "postura": POSTURA},
           "itens": saida,
           "descartados": descartados}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
