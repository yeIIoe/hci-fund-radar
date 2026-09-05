# -*- coding: utf-8 -*-
"""GEOPOLITICA — o que o noticiario do mundo diz sobre cada moeda, medido, e o que isso
IMPLICA por regra declarada. Nao entra na conviccao ate ser medido.

O PEDIDO (Eduardo, 04/set)
    "informacao macro e informacao geopolitica, cruzadas, dando uma conviccao dos proximos
    juros devido a x, y e z motivos". A parte macro esta no sentimento.py. Esta e a parte
    geopolitica: uma camada de CONTEXTO por moeda, com intensidade medida e manchetes.

FONTE
    GDELT DOC 2.0 API — gratuita, sem chave, cobre o noticiario mundial com atualizacao de
    15 minutos. Limite de taxa agressivo (429 com duas chamadas seguidas; testado em 04/set):
    uma chamada a cada 6 s, com espera de 20 s no 429. Sao 2 chamadas por moeda + 2 de mundo.
    ⚠️ Ao contrario do calendario, aqui a JANELA importa mais que o instante: intensidade de
    3 dias contra a media de 14 dias.

O QUE SAI, por moeda
    conflito     volume de artigos com guerra/sancoes/misseis/cessar-fogo ligados ao pais,
                 3 dias, comparado a media diaria dos 14 dias anteriores (razao e z)
    energia      idem para petroleo/energia/tarifas/embargo — o canal que vira INFLACAO
    tom          tom medio do GDELT (negativo = noticiario ruim)
    manchetes    as 5 mais relevantes de cada tema, com fonte e hora — o material CRU
    manchetes_unicas  o mesmo material AGRUPADO POR EVENTO (05/set): uma linha por evento,
                 com a lista de fontes, n_republicacoes e a confiabilidade da fonte
                 (alta/media/baixa). Ordenadas por confiabilidade e depois por
                 republicacoes. Ver o bloco (A)(B)(C) mais abaixo.
    implicacao   REGRA DECLARADA, nao medida:
                   choque de conflito -> risk-off: USD, CHF e JPY tendem a receber fluxo;
                                          AUD, NZD e CAD tendem a perder (FX, nao juro)
                   choque de energia  -> inflacao para importador liquido -> empurra APERTO;
                                          para exportador (CAD, NOK) o efeito e misto

⚰️ COMO ENTRA NA LEITURA — EXPERIMENTAL, NAO VOTA (decisao de 05/set/2026)
    Em 04/set a geopolitica tinha entrado como 4a dimensao do sentimento e como segunda
    perna do ouro. Em 05/set essa decisao foi REVOGADA e esta e a regra em vigor: a
    geopolitica NAO VOTA. Motivo: a regra da casa e que filtro novo passa por medicao antes
    de pontuar (o DXY foi reprovado nas 88 operacoes justamente por ter sido assumido), e a
    regra "energia z>=1,5 = ALTA para importador, conflito sem energia = CORTE" nunca foi
    medida. Ela foi declarada e nunca testada — logo nao pontua.

    O QUE ACONTECE HOJE: sentimento.py continua LENDO este arquivo e continua EXIBINDO os z
    e as manchetes, com selo "experimental" e vota:false. O componente entra com 0,000 e a
    dimensao fica FORA do teto. O valor que ela teria se votasse fica gravado ao lado, em
    "leitura_se_votasse", para o dia em que houver medicao. Aqui o arquivo carrega isso por
    escrito: vota:false, selo e recolher_por_padrao na raiz E em cada moeda, para a interface
    poder recolher a secao por padrao sem que a informacao suma.

    A HIPOTESE A MEDIR continua registrada, e e ela que destrava o voto: "conflito z>=2 muda
    o retorno de 20 dias das moedas de risco?".

⚠️ TAXA: 04/set, duas coletas simultaneas (uma esquecida viva) tomaram 429 em 12 de 13
    chamadas. Uma coleta por vez, 8 s entre chamadas, sem a chamada de tom. Na Action o cache
    de 3 h garante uma coleta a cada ~3 rodadas.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "geopolitica.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0"}
API = "https://api.gdeltproject.org/api/v2/doc/doc?"
CACHE_H = 3
PAUSA_S = 15                  # 04/set: o GDELT limita por IP; a 12 s o runner ainda perdeu 4 de 8 moedas
ORCAMENTO_S = 8 * 60          # a Action tem 15 min para a cadeia inteira; isto para em 8 e grava o que tem

PAIS = {
    "USD": '("United States" OR Washington OR "U.S.")',
    "EUR": '("euro area" OR eurozone OR "European Union" OR Germany OR France OR Brussels)',
    "GBP": '("United Kingdom" OR Britain OR "UK government" OR London)',
    "JPY": '(Japan OR Tokyo)',
    "AUD": '(Australia OR Canberra)',
    "NZD": '("New Zealand" OR Wellington)',
    "CAD": '(Canada OR Ottawa)',
    "CHF": '(Switzerland OR Swiss)',
}
TEMAS = {
    "conflito": '(war OR sanctions OR missile OR airstrike OR ceasefire OR "military strike" OR invasion)',
    "energia":  '("oil price" OR "crude oil" OR OPEC OR "energy prices" OR tariff OR tariffs OR embargo OR "trade war")',
}
# moedas de refugio e de risco — regra declarada, nao medida
REFUGIO = ("USD", "CHF", "JPY")
RISCO = ("AUD", "NZD", "CAD")
EXPORTADOR_ENERGIA = ("CAD",)


INICIO = time.time()


def estourou() -> bool:
    return (time.time() - INICIO) > ORCAMENTO_S


def gdelt(params: dict, tentativas: int = 2):
    u = API + urllib.parse.urlencode(params)
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                corpo = r.read().decode("utf-8", errors="replace")
            if not corpo.strip():
                return {}
            return json.loads(corpo)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tentativas - 1:
                time.sleep(15)
                continue
            raise
        except json.JSONDecodeError:
            return {}
    return {}


def volume(q: str) -> dict:
    """Volume diario dos ultimos 14 dias (timelinevol) -> intensidade dos 3 ultimos dias."""
    d = gdelt({"query": q, "mode": "timelinevol", "format": "json", "timespan": "14d"})
    serie = ((d.get("timeline") or [{}])[0].get("data") or [])
    vals = [float(p.get("value") or 0) for p in serie]
    if len(vals) < 6:
        return {"n": len(vals)}
    rec, base = vals[-3:], vals[:-3]
    m = sum(base) / len(base)
    sd = math.sqrt(sum((x - m) ** 2 for x in base) / max(1, len(base) - 1))
    media_rec = sum(rec) / 3.0
    return {"n": len(vals), "recente_3d": round(media_rec, 4), "base_14d": round(m, 4),
            "razao": round(media_rec / m, 2) if m > 0 else None,
            "z": round((media_rec - m) / sd, 2) if sd > 0 else None}


def tom(q: str):
    d = gdelt({"query": q, "mode": "timelinetone", "format": "json", "timespan": "7d"})
    serie = ((d.get("timeline") or [{}])[0].get("data") or [])
    vals = [float(p.get("value")) for p in serie if p.get("value") not in (None, "")]
    return round(sum(vals) / len(vals), 2) if vals else None


def manchetes(q: str, n: int = 5) -> list:
    d = gdelt({"query": q, "mode": "artlist", "maxrecords": n, "format": "json",
               "timespan": "3d", "sort": "hybridrel"})
    out = []
    for a in d.get("articles", [])[:n]:
        out.append({"titulo": (a.get("title") or "")[:140], "url": a.get("url"),
                    "fonte": a.get("domain"), "quando": a.get("seendate"),
                    "pais_fonte": a.get("sourcecountry")})
    return out


# =======================================================================================
# (A) DEDUPLICACAO SEMANTICA · (B) CONFIABILIDADE DA FONTE · (C) SELO EXPERIMENTAL
# =======================================================================================
# O PEDIDO (Eduardo, 05/set): "vi duas manchetes descrevendo praticamente o mesmo ataque".
# Estavam no pano de fundo do mundo:
#     "U . S . attacks leave IRGC soldiers dead in Iran Kermanshah Province"   (trend.az)
#     "Death Toll From U . S . Strikes in Iran Rises to 18 , IRGC Says ..."    (khaama.com)
# Sao o mesmo ataque e NENHUM limiar de Jaccard razoavel as junta: as palavras em comum sao
# duas ("iran", "irgc") em dezesseis — Jaccard 0,13. Contagem de palavra nao le sinonimo de
# acao (attacks/strikes) nem sinonimo de desfecho (dead/killed). Por isso a regra tem DUAS
# pernas, e a segunda e que resolve o caso do dono.
#
# REGRA ESCOLHIDA — as duas propostas, em OU, com os limiares todos PROVISORIOS:
#   1. Jaccard >= 0,55 sobre as palavras de 4+ letras do titulo normalizado.
#      Pega a republicacao literal: a mesma materia de agencia em dez portais.
#   2. ASSINATURA DE ENTIDADES: mesma CLASSE DE ACAO
#         E Jaccard das entidades >= 0,60
#         E pelo menos 2 entidades em comum.
#      Pega a mesma noticia reescrita. E a perna que junta o par que o dono viu.
#
# AS TRES CONDICOES DA REGRA 2 SAO CONJUNTAS DE PROPOSITO. Medido nas manchetes de hoje:
#   • so ENTIDADE juntaria o ataque dos EUA ao Ira com a conversa Putin-Ira (as duas tem
#     {eua, ira}); a CLASSE DE ACAO (ataque x diplomacia) separa.
#   • so ACAO juntaria o ataque em Kiev com o ataque em Gaza; a ENTIDADE separa.
#   • com 1 entidade em comum, "Ira" sozinho juntaria tudo que sai do Oriente Medio.
# Com o limiar de entidade em 0,50 o ataque e a conversa empatariam em 0,50 e so a acao
# seguraria — margem de uma condicao so. Em 0,60 sobram duas. Dai o 0,60.
#
# BURACOS DECLARADOS (o agrupamento erra para MENOS, nunca para mais):
#   • a entidade sai de um LEXICO finito. Manchete sobre lugar fora do lexico nao ganha
#     assinatura e cai so na regra 1.
#   • evento com UMA entidade so nao agrupa. "Russia launches missile strike on Kyiv" e
#     "Missile attack on Kyiv leaves 12 dead, Ukraine says" ficam separadas: a segunda so
#     nomeia a Ucrania. Preferimos a duplicata visivel a fusao errada.
#
# NAO E NER NEM MODELO DE LINGUA. E lexico declarado, auditavel, provisorio — como manda a
# lei da casa para todo limiar novo.

VAZIAS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "as", "at", "by", "with",
    "from", "is", "are", "was", "were", "be", "been", "after", "over", "amid", "up", "down",
    "new", "its", "it", "that", "this", "than", "but", "not", "no", "into", "about", "more",
    "most", "his", "her", "their", "they", "he", "she", "we", "you", "will", "would", "could",
    "should", "may", "can", "has", "have", "had", "who", "what", "why", "how", "when",
    "video", "live", "update", "updates", "analysis", "opinion", "exclusive", "watch", "read",
    "news", "latest", "report", "reports", "says", "said", "say", "during", "while",
}
MIN_LETRAS = 4                     # (A) so palavras de 4+ letras entram no Jaccard
LIMIAR_JACCARD = 0.55              # PROVISORIO — republicacao literal
LIMIAR_JACCARD_ENT = 0.60          # PROVISORIO — mesma noticia reescrita
MIN_ENTIDADES_COMUNS = 2           # PROVISORIO — abaixo disto, "Ira" sozinho juntaria tudo

# ------------------------------------------------------------------ lexico de ENTIDADES
# alias -> entidade canonica. O alias e casado no texto normalizado, entre espacos, entao
# "us" so casa a palavra solta (o "U . S ." do GDELT vira "US" antes disso).
ENTIDADES = {
    "eua": ["united states", "us", "usa", "washington", "american", "americans",
            "white house", "pentagon", "trump", "biden"],
    "ira": ["iran", "irans", "iranian", "iranians", "tehran"],
    "irgc": ["irgc", "revolutionary guard", "quds force"],
    "israel": ["israel", "israeli", "jerusalem", "netanyahu", "idf"],
    "gaza": ["gaza", "hamas", "palestinian", "palestinians", "west bank"],
    "libano": ["lebanon", "lebanese", "hezbollah", "beirut"],
    "iemen": ["yemen", "houthi", "houthis"],
    "russia": ["russia", "russias", "russian", "moscow", "kremlin", "putin"],
    "ucrania": ["ukraine", "ukraines", "ukrainian", "kyiv", "kiev", "zelensky", "zelenskyy"],
    "china": ["china", "chinas", "chinese", "beijing", "xi jinping", "taiwan"],
    "coreia_norte": ["north korea", "pyongyang", "kim jong"],
    "india": ["india", "indian", "new delhi"],
    "paquistao": ["pakistan", "pakistani", "islamabad"],
    "turquia": ["turkey", "turkish", "ankara", "erdogan"],
    "arabia": ["saudi", "riyadh", "aramco"],
    "emirados": ["uae", "emirates", "abu dhabi", "dubai"],
    "catar": ["qatar", "doha"],
    "egito": ["egypt", "egyptian", "cairo"],
    "siria": ["syria", "syrian", "damascus"],
    "iraque": ["iraq", "iraqi", "baghdad"],
    "venezuela": ["venezuela", "venezuelan", "caracas", "maduro"],
    "sudao": ["sudan", "sudanese", "khartoum"],
    "reino_unido": ["united kingdom", "britain", "british", "london", "downing street"],
    "alemanha": ["germany", "german", "berlin"],
    "franca": ["france", "french", "paris", "macron"],
    "ue": ["european union", "brussels", "european commission", "euro area", "eurozone"],
    "japao": ["japan", "japans", "japanese", "tokyo"],
    "australia": ["australia", "australian", "canberra"],
    "nova_zelandia": ["new zealand", "wellington"],
    "canada": ["canada", "canadian", "ottawa"],
    "suica": ["switzerland", "swiss", "bern", "zurich"],
    "opep": ["opec"],
    "otan": ["nato"],
    "onu": ["united nations", "un security council"],
    "fmi": ["imf", "international monetary fund"],
    "aiea": ["iaea", "atomic energy agency"],
}
# toda sigla ja coberta pelo lexico: a caixa alta nao pode criar uma SEGUNDA entidade para o
# mesmo ator ("US" virando "us" ao lado de "eua" inflava o Jaccard de graca).
SIGLAS_DO_LEXICO = {a for aliases in ENTIDADES.values() for a in aliases if " " not in a}
# sigla que NAO e ator geopolitico: veiculo, moeda, indicador, banco central, empresa. Sem
# esta lista, duas manchetes de mercado compartilhavam "JPY" e "USD" e viravam o mesmo evento.
SIGLAS_VAZIAS = {
    "the", "and", "news", "live", "update", "video", "am", "pm", "est", "gmt", "utc",
    "breaking", "watch", "read", "new", "ceo", "cfo", "tv", "ii", "iii",
    "usd", "eur", "jpy", "gbp", "aud", "nzd", "cad", "chf", "cny", "brl", "mxn",
    "cpi", "ppi", "pce", "gdp", "nfp", "pmi", "ism", "fomc", "boj", "boe", "boc", "ecb",
    "rba", "rbnz", "snb", "fed", "etf", "etfs", "ipo", "esg", "fy", "yoy", "mom",
    "bbc", "cnn", "cnbc", "abc", "nbc", "cbs", "afp", "wsj", "ft", "ap", "pti", "ani",
    "ians", "afr", "rte", "dw", "npr", "pbs", "sbs", "mufg", "fifa", "nfl", "nba", "ai",
}

# ------------------------------------------------------------------- lexico de ACOES
# Ordem de prioridade: a primeira classe que casar manda. "war" NAO entra em nenhuma: e o
# termo da propria busca do GDELT, aparece em quase toda manchete e nao separaria nada.
ACOES = [
    ("ataque", ["strike", "strikes", "struck", "attack", "attacks", "attacked", "airstrike",
                "air strike", "bomb", "bombing", "bombed", "missile", "missiles", "drone",
                "killed", "kills", "dead", "death toll", "casualties", "raid", "shelling",
                "offensive", "invasion", "invaded", "assault"]),
    ("cessar_fogo", ["ceasefire", "cease fire", "truce", "peace deal", "peace talks",
                     "armistice", "withdrawal", "hostage deal"]),
    ("sancoes", ["sanction", "sanctions", "sanctioned", "embargo", "tariff", "tariffs",
                 "export ban", "blacklist", "trade war"]),
    ("energia", ["oil price", "oil prices", "crude", "opec", "barrel", "gas price",
                 "gas prices", "energy price", "energy prices", "pipeline", "refinery",
                 "lng", "natural gas"]),
    ("nuclear", ["nuclear", "enrichment", "uranium", "centrifuge"]),
    ("diplomacia", ["talks", "meeting", "summit", "visit", "thanks", "praise", "praises",
                    "pledge", "pledges", "stance", "support", "backs", "urges", "warns",
                    "condemn", "condemns", "deal", "agreement", "negotiation", "negotiations",
                    "diplomat", "diplomacy", "envoy", "call", "calls"]),
]

# ------------------------------------------------------- (B) CONFIABILIDADE DA FONTE
# Tres faixas, regra declarada e PROVISORIA:
#   alta   agencia internacional, jornal financeiro de referencia, agencia oficial e governo
#   media  grande jornal ou emissora nacional conhecida
#   baixa  o resto, e TODO agregador — quem republica nao responde pelo que publicou
# O casamento aceita as duas formas em que a fonte chega: dominio ("reuters.com", que o GDELT
# manda) e nome ("The Japan Times", que o noticias.py manda). Chave de uma palavra casa TOKEN
# inteiro; chave de duas ou mais casa a sequencia.
DOMINIOS_OFICIAIS = (".gov", ".gov.uk", ".gov.au", ".govt.nz", ".gc.ca", ".gouv.fr",
                     ".europa.eu", ".un.org", ".int", ".mil")
CONFIABILIDADE_ALTA = [
    "reuters", "apnews", "associated press", "ap news", "afp", "agence france presse",
    "bloomberg", "ft", "financial times", "wsj", "wall street journal", "dow jones",
    "marketwatch", "barrons", "barron s", "economist", "nikkei",
    "federalreserve", "bankofengland", "bank of england", "boj or jp", "bankofcanada",
    "bank of canada", "rba gov", "reserve bank", "rbnz", "snb ch", "swiss national bank",
    "imf org", "worldbank", "iaea org", "oecd org", "bls gov", "census gov", "ons gov",
    "eurostat", "treasury", "european central bank", "ecb europa",
]
CONFIABILIDADE_MEDIA = [
    "bbc", "cnn", "nytimes", "new york times", "washingtonpost", "washington post",
    "theguardian", "guardian", "telegraph", "thetimes", "independent", "sky news", "skynews",
    "cnbc", "abc", "cbsnews", "cbs news", "nbcnews", "nbc news", "npr", "pbs",
    "cbc", "theglobeandmail", "globe and mail", "nationalpost", "national post",
    "financialpost", "financial post", "ctvnews",
    "smh", "sydney morning herald", "theage", "theaustralian", "the australian", "afr",
    "australian financial review", "news com au",
    "nzherald", "new zealand herald", "rnz", "stuff co nz",
    "japantimes", "japan times", "asahi", "yomiuri", "kyodo", "japannews",
    "lemonde", "le monde", "lefigaro", "spiegel", "handelsblatt", "faz", "zeit",
    "dw com", "deutsche welle", "france24", "rfi", "euronews", "politico", "axios",
    "aljazeera", "al jazeera", "haaretz", "timesofisrael", "times of israel", "jpost",
    "jerusalem post", "scmp", "south china morning post", "straitstimes", "straits times",
    "thehindu", "the hindu", "indianexpress", "indian express", "hindustantimes",
    "hindustan times", "channelnewsasia", "swissinfo", "nzz",
    "kyivpost", "kyiv post", "kyivindependent", "kyiv independent", "moscowtimes",
    "elpais", "el pais", "corriere", "lastampa", "irishtimes", "irish times",
    "forbes", "businessinsider", "business insider", "fortune", "thehill", "the hill",
    "usatoday", "usa today", "latimes", "los angeles times", "chicagotribune",
    "globaltimes", "xinhua", "tass",
]
CONFIABILIDADE_AGREGADOR = [
    "google", "news google", "msn", "yahoo", "flipboard", "newsbreak", "biztoc",
    "smartnews", "headtopics", "newsnow", "pressreader", "inkl", "zerohedge",
    "investing com", "benzinga", "menafn", "eurasiareview", "tradingview", "fxstreet",
    "tradingpedia", "stonex", "24 7 wall st", "seekingalpha", "simplywall",
]
ORDEM_CONFIABILIDADE = {"alta": 0, "media": 1, "baixa": 2}


def sem_acento(t: str) -> str:
    """Tira o acento sem tirar a letra: base de toda comparacao de texto daqui."""
    t = unicodedata.normalize("NFKD", t or "")
    return "".join(c for c in t if not unicodedata.combining(c))


def colapsa_siglas(titulo: str) -> str:
    """"U . S . Strikes" -> "US Strikes". O GDELT devolve a sigla com espaco e ponto, o que
    quebrava tanto a palavra quanto a entidade."""
    return re.sub(r"\b(?:[A-Za-z]\s*\.\s*){2,}",
                  lambda m: re.sub(r"[^A-Za-z]", "", m.group(0)) + " ", sem_acento(titulo or ""))


def normaliza(titulo: str) -> str:
    """Minusculas, sem acento, sem pontuacao, sigla colapsada, espaco unico."""
    t = re.sub(r"[^a-z0-9 ]+", " ", colapsa_siglas(titulo).lower())
    return re.sub(r"\s+", " ", t).strip()


def titulo_exibicao(titulo: str) -> str:
    """O titulo como ele deve APARECER na tela. O GDELT entrega a sigla e a pontuacao
    soltas — "U . S . attacks ... Rises to 18 , IRGC Says" — e era isso que ia para o
    painel. Aqui a sigla e recolada e o espaco antes da pontuacao some. O acento fica: esta
    e a versao de leitura, nao a de comparacao. O titulo cru continua em `titulo_original`
    e em `manchetes`, intocado."""
    t = re.sub(r"\b(?:[A-Za-z]\s*\.\s*){2,}",
               lambda m: re.sub(r"\s+", "", m.group(0)) + " ", titulo or "")
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def tokens_do_veiculo(fonte: str) -> set:
    """As palavras do nome/dominio do veiculo — saem do titulo antes de qualquer comparacao,
    senao "- Reuters" no fim de duas manchetes diferentes vira semelhanca."""
    return {w for w in re.split(r"[^a-z0-9]+", sem_acento(fonte or "").lower()) if len(w) > 1}


def palavras_de(titulo: str, fonte: str) -> set:
    """As palavras de 4+ letras do titulo normalizado, sem palavra vazia e sem o nome do
    veiculo. E a materia-prima da regra 1."""
    veiculo = tokens_do_veiculo(fonte)
    return {p for p in normaliza(titulo).split()
            if len(p) >= MIN_LETRAS and p not in VAZIAS and p not in veiculo}


def entidades_de(titulo: str, fonte: str = "") -> set:
    """Assinatura de entidades: o que o LEXICO reconhece, mais as siglas em caixa alta que
    nao sao do lexico, nem do veiculo, nem da lista de siglas sem valor geopolitico."""
    t = " %s " % normaliza(titulo)
    fora = {canonica for canonica, aliases in ENTIDADES.items()
            if any((" %s " % a) in t for a in aliases)}
    veiculo = tokens_do_veiculo(fonte)
    bruto = colapsa_siglas(titulo)
    palavras = [p for p in re.split(r"[^A-Za-z]+", bruto) if p]
    caixa_alta = [p for p in palavras if p.isupper() and 2 <= len(p) <= 6]
    # manchete inteira em caixa alta nao tem sigla: tem grito. Ignorada.
    if palavras and len(caixa_alta) / float(len(palavras)) < 0.5:
        for s in caixa_alta:
            b = s.lower()
            if b not in SIGLAS_VAZIAS and b not in SIGLAS_DO_LEXICO and b not in veiculo:
                fora.add(b)
    return fora


def acao_de(titulo: str) -> str:
    """Classe de acao do evento, pelo lexico, na ordem de prioridade declarada."""
    t = " %s " % normaliza(titulo)
    for classe, termos in ACOES:
        if any((" %s " % termo) in t for termo in termos):
            return classe
    return "outro"


def jaccard(a: set, b: set) -> float:
    """Interseccao sobre uniao. Zero quando qualquer um dos lados esta vazio."""
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def confiabilidade_de(fonte: str) -> str:
    """(B) alta / media / baixa. Agregador cai em baixa mesmo republicando agencia."""
    f = sem_acento(fonte or "").lower().strip()
    if not f:
        return "baixa"
    plano = " ".join(w for w in re.split(r"[^a-z0-9]+", f) if w)
    toks = set(plano.split())

    def casa(chaves):
        for k in chaves:
            if " " in k:
                if (" %s " % k) in (" %s " % plano):
                    return True
            elif k in toks:
                return True
        return False

    if casa(CONFIABILIDADE_AGREGADOR):
        return "baixa"
    if any(f.endswith(s) for s in DOMINIOS_OFICIAIS):
        return "alta"
    if casa(CONFIABILIDADE_ALTA):
        return "alta"
    if casa(CONFIABILIDADE_MEDIA):
        return "media"
    return "baixa"


def mesmo_evento(a: dict, g: dict) -> bool:
    """As duas regras, em OU. A regra 2 exige acao igual E entidade parecida E 2 em comum."""
    if jaccard(a["_palavras"], g["palavras"]) >= LIMIAR_JACCARD:
        return True
    ea, eg = a["_entidades"], g["entidades"]
    return (a["_acao"] == g["acao"] and a["_acao"] != "outro"
            and len(ea & eg) >= MIN_ENTIDADES_COMUNS
            and jaccard(ea, eg) >= LIMIAR_JACCARD_ENT)


def agrupa(manchetes: list) -> tuple:
    """(A) Um evento por grupo. Devolve (grupos, duplicatas_removidas)."""
    itens = []
    for m in manchetes or []:
        it = dict(m)
        it["_palavras"] = palavras_de(m.get("titulo"), m.get("fonte"))
        it["_entidades"] = entidades_de(m.get("titulo"), m.get("fonte"))
        it["_acao"] = acao_de(m.get("titulo"))
        itens.append(it)
    grupos = []
    for it in itens:
        alvo = next((g for g in grupos if mesmo_evento(it, g)), None)
        if alvo is None:
            grupos.append({"palavras": set(it["_palavras"]), "entidades": set(it["_entidades"]),
                           "acao": it["_acao"], "membros": [it]})
        else:
            alvo["membros"].append(it)
            alvo["palavras"] |= it["_palavras"]
            alvo["entidades"] |= it["_entidades"]
    return grupos, sum(len(g["membros"]) - 1 for g in grupos)


def representa(g: dict) -> dict:
    """Uma manchete por grupo: a de MAIOR confiabilidade e, empatando, a mais antiga — a
    primeira a publicar, nao a ultima a copiar. As outras viram fontes e n_republicacoes."""
    membros = sorted(g["membros"],
                     key=lambda m: (ORDEM_CONFIABILIDADE[confiabilidade_de(m.get("fonte"))],
                                    str(m.get("quando") or "")))
    r = {k: v for k, v in membros[0].items() if not k.startswith("_")}
    r["titulo_original"] = r.get("titulo")
    r["titulo"] = titulo_exibicao(r.get("titulo"))
    r["confiabilidade"] = confiabilidade_de(r.get("fonte"))
    r["fontes"] = []
    for m in membros:
        nome = m.get("fonte") or "?"
        if nome not in r["fontes"]:
            r["fontes"].append(nome)
    r["n_republicacoes"] = len(membros)
    r["acao"] = g["acao"]
    r["entidades"] = sorted(g["entidades"])
    r["agrupadas"] = [{"titulo": titulo_exibicao(m.get("titulo"))[:140], "fonte": m.get("fonte"),
                       "confiabilidade": confiabilidade_de(m.get("fonte")),
                       "url": m.get("url")} for m in membros[1:]][:6]
    return r


def deduplica(manchetes: list) -> tuple:
    """(A)+(B): manchetes unicas, ordenadas por confiabilidade e depois por republicacoes."""
    grupos, dupes = agrupa(manchetes)
    unicas = [representa(g) for g in grupos]
    unicas.sort(key=lambda r: (ORDEM_CONFIABILIDADE[r["confiabilidade"]],
                               -r["n_republicacoes"], str(r.get("quando") or "")))
    return unicas, dupes


# ------------------------------------------------- cabecalho do relatorio (em portugues)
FONTE_TXT = "GDELT DOC 2.0 API (gratuita, sem chave, atualização de 15 min); fontes em inglês"
METODO_TXT = ("volume de artigos dos últimos 3 dias contra a média diária da janela de 14 dias "
              "(razão e z); manchetes por relevância híbrida, agrupadas por evento antes de "
              "aparecer")
AVISO_TXT = ("Camada de CONTEXTO. A implicação é uma regra declarada (aversão a risco -> moedas "
             "de refúgio; choque de energia -> empurrão de inflação), não é medição, e NÃO entra "
             "na convicção. Hipótese a medir: um pico de conflito z>=2 muda o retorno de 20 dias "
             "das moedas de risco?")

# --------------------------------------------------------------------- (C) SELO
SELO = "experimental — contexto, não vota"
SELO_MOTIVO = ("Camada de contexto. A implicação é regra declarada, nunca medida, e não entra "
               "na convicção nem no teto do sentimento. A interface pode recolher esta seção "
               "por padrão: a informação continua inteira no arquivo.")


def enriquece(rel: dict) -> dict:
    """Aplica (A) deduplicação, (B) confiabilidade e (C) selo experimental sobre o relatório
    inteiro — o pano de fundo do mundo e cada tema de cada moeda. Não faz chamada de rede:
    é pós-processamento puro, e por isso também roda em `--reprocessar` sobre o arquivo que
    já está no disco (o GDELT bloqueia por IP; não se coleta para testar deduplicação)."""
    # o cabecalho e texto declarado: reescrito a cada passagem para que o arquivo nunca fique
    # com a frase em ingles da coleta antiga (lei da casa: zero ingles na tela)
    rel["fonte"] = FONTE_TXT
    rel["metodo"] = METODO_TXT
    rel["aviso"] = AVISO_TXT
    total_dupes = 0
    for _tema, bloco in (rel.get("mundo") or {}).items():
        if not isinstance(bloco, dict):
            continue
        unicas, dupes = deduplica(bloco.get("manchetes"))
        bloco["manchetes_unicas"] = unicas
        bloco["duplicatas_removidas"] = dupes
        bloco["vota"] = False
        bloco["selo"] = SELO
        total_dupes += dupes
    for _moeda, b in (rel.get("moedas") or {}).items():
        if not isinstance(b, dict):
            continue
        for _t, t in (b.get("temas") or {}).items():
            if not isinstance(t, dict):
                continue
            unicas, dupes = deduplica(t.get("manchetes"))
            t["manchetes_unicas"] = unicas
            t["duplicatas_removidas"] = dupes
            t["vota"] = False
            t["selo"] = SELO
            total_dupes += dupes
        # a implicacao e REESCRITA a cada passagem, a partir dos z que ja estao no arquivo.
        # E regra declarada pura (nao le nada de fora), entao reescrever nao inventa dado —
        # e o que traduz para portugues a frase que ficou gravada em ingles na coleta antiga.
        temas = b.get("temas") or {}
        b["implicacao"] = implicacao(
            _moeda,
            ((temas.get("conflito") or {}).get("volume") or {}),
            ((temas.get("energia") or {}).get("volume") or {}))
        # (C) cada moeda diz, sozinha, que e experimental e que nao vota — a interface pode
        # recolher a secao por padrao sem que a informacao suma do arquivo
        b["vota"] = False
        b["experimental"] = True
        b["selo"] = SELO
        b["selo_motivo"] = SELO_MOTIVO
        b["recolher_por_padrao"] = True
        b["peso_no_sentimento"] = 0.0
    rel["vota"] = False
    rel["experimental"] = True
    rel["selo"] = SELO
    rel["selo_motivo"] = SELO_MOTIVO
    rel["recolher_por_padrao"] = True
    rel["duplicatas_removidas_total"] = total_dupes
    rel["regra_deduplicacao"] = {
        "metodo": "duas regras em OU, sobre o título normalizado",
        "regra_1": "Jaccard >= %.2f sobre as palavras de %d+ letras" % (LIMIAR_JACCARD, MIN_LETRAS),
        "regra_2": "mesma classe de ação E Jaccard das entidades >= %.2f E >= %d entidades em comum"
                   % (LIMIAR_JACCARD_ENT, MIN_ENTIDADES_COMUNS),
        "normalizacao": "minúsculas, sem acento, sem pontuação, sigla pontuada colapsada "
                        "(U . S . -> US), sem o nome do veículo, sem palavras vazias em inglês",
        "representante": "a fonte de maior confiabilidade; empatando, a publicação mais antiga",
        "entidades": "léxico declarado e finito (países, capitais, gentílicos, organismos, "
                     "dirigentes) mais as siglas em caixa alta que não são veículo, moeda, "
                     "indicador nem banco central",
        "acoes": [c for c, _ in ACOES],
        "buracos_declarados": [
            "manchete sobre lugar fora do léxico não ganha assinatura de entidade e cai só "
            "na regra 1: deduplica menos, nunca deduplica errado",
            "evento com uma entidade só não agrupa (exige 2 em comum) — a duplicata visível "
            "é preferível à fusão errada",
        ],
        "provisorio": True,
    }
    rel["confiabilidade_fonte"] = {
        "faixas": {"alta": "agência internacional, jornal financeiro de referência, agência "
                           "oficial e governo",
                   "media": "grande jornal ou emissora nacional conhecida",
                   "baixa": "o resto, e todo agregador"},
        "casamento": "pelo domínio ou pelo nome da fonte; domínio oficial (.gov e afins) é alta",
        "ordenacao": "as manchetes exibidas saem por confiabilidade e depois por n_republicacoes",
        "provisorio": True,
    }
    return rel


def reprocessa() -> int:
    """`--reprocessar`: relê data/geopolitica.json e reaplica (A), (B) e (C). ZERO chamada de
    rede — é assim que se testa a deduplicação sem coletar (o GDELT bloqueia por IP)."""
    if not os.path.exists(SAIDA):
        print("  !! não há %s para reprocessar" % SAIDA)
        return 1
    rel = json.load(io.open(SAIDA, encoding="utf-8"))
    antes = sum(len(((b or {}).get("manchetes") or [])) for b in (rel.get("mundo") or {}).values())
    for b in (rel.get("moedas") or {}).values():
        antes += sum(len(((t or {}).get("manchetes") or [])) for t in (b.get("temas") or {}).values())
    enriquece(rel)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1, allow_nan=False)
    print("  reprocessado sem rede: %d manchetes -> %d únicas (%d duplicatas removidas)"
          % (antes, antes - rel["duplicatas_removidas_total"], rel["duplicatas_removidas_total"]))
    print("  gravado: %s" % SAIDA)
    return 0


def implicacao(moeda: str, conf: dict, ener: dict) -> dict:
    zc = conf.get("z") if conf else None
    ze = ener.get("z") if ener else None
    out = {"regra": "regra declarada, não medida — está aqui para o julgamento, não entra na convicção",
           "fx": None, "juro": None}
    if zc is not None and zc >= 1.5:
        if moeda in REFUGIO:
            out["fx"] = "aversão a risco: o fluxo de refúgio tende a SUSTENTAR o %s (regra)" % moeda
        elif moeda in RISCO:
            out["fx"] = "aversão a risco: moeda de risco tende a PERDER — %s (regra)" % moeda
        else:
            out["fx"] = "aversão a risco: efeito misto para o %s (regra)" % moeda
    if ze is not None and ze >= 1.5:
        if moeda in EXPORTADOR_ENERGIA:
            out["juro"] = ("choque de energia: exportador — termos de troca melhoram e a inflação "
                           "sobe; efeito misto para o juro (regra)")
        else:
            out["juro"] = "choque de energia: importador — empurrão de inflação, inclina ao APERTO (regra)"
    return out


def cache_vale(forcar: bool) -> bool:
    if forcar or not os.path.exists(SAIDA):
        return False
    try:
        g = dt.datetime.fromisoformat(json.load(io.open(SAIDA, encoding="utf-8"))["gerado_em"])
        return (dt.datetime.now(dt.timezone.utc) - g).total_seconds() < CACHE_H * 3600
    except Exception:
        return False


def main():
    forcar = "--forcar" in sys.argv
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 88)
    print("GEOPOLITICA — intensidade do noticiario por moeda (GDELT), regra declarada ao lado")
    print("=" * 88)
    # --reprocessar: so pos-processamento sobre o arquivo do disco, ZERO chamada ao GDELT.
    # E o modo de testar e reaplicar a deduplicacao sem gastar chamada nem tomar 429.
    if "--reprocessar" in sys.argv:
        sys.exit(reprocessa())
    if cache_vale(forcar):
        print("  leitura de menos de %d h ainda vale — use --forcar" % CACHE_H)
        return

    saida, erros = {}, []
    # A rodada anterior: quem falhar agora (429) carrega o dado de antes, com o carimbo dele,
    # valido por 24 h. Sem isto o CAD aparecia "nao conectado" so porque foi o 5o da fila
    # (Eduardo, 04/set). E a ORDEM gira a cada rodada, para o limite nao cair sempre nos mesmos.
    anterior = {}
    try:
        anterior = json.load(io.open(SAIDA, encoding="utf-8")) if os.path.exists(SAIDA) else {}
    except Exception:
        anterior = {}
    ordem = list(PAIS.keys())
    giro = int(agora.timestamp() // 3600) % len(ordem)
    ordem = ordem[giro:] + ordem[:giro]
    # o mundo primeiro: o pano de fundo que todas as moedas compartilham
    mundo = {}
    for tema, q in TEMAS.items():
        try:
            mundo[tema] = {"volume": volume(q + " sourcelang:english"), "manchetes": manchetes(q + " sourcelang:english")}
            time.sleep(PAUSA_S)
        except Exception as e:
            erros.append("mundo/%s: %s" % (tema, str(e)[:60]))
            time.sleep(PAUSA_S)
    print("  mundo: conflito z=%s · energia z=%s" % (
        (mundo.get("conflito") or {}).get("volume", {}).get("z"),
        (mundo.get("energia") or {}).get("volume", {}).get("z")))

    for moeda in ordem:
        qp = PAIS[moeda]
        if estourou():
            erros.append("orcamento de %d s estourado antes de %s — o resto fica para a proxima rodada" % (ORCAMENTO_S, moeda))
            break
        bloco = {"temas": {}, "tom": None}
        for tema, qt in TEMAS.items():
            q = "%s %s sourcelang:english" % (qt, qp)
            try:
                v = volume(q)
                time.sleep(PAUSA_S)
                # manchetes por moeda desligadas (04/set): so o mundo traz manchetes —
                # cada chamada a menos e uma chance a menos de 429
                bloco["temas"][tema] = {"volume": v, "manchetes": []}
            except Exception as e:
                erros.append("%s/%s: %s" % (moeda, tema, str(e)[:60]))
                bloco["temas"][tema] = {"erro": str(e)[:80]}
                time.sleep(PAUSA_S)
        # tom: desligado — e a chamada menos util e custa 8 chamadas por rodada (04/set)
        bloco["tom"] = None
        conf = (bloco["temas"].get("conflito") or {}).get("volume") or {}
        ener = (bloco["temas"].get("energia") or {}).get("volume") or {}
        bloco["implicacao"] = implicacao(moeda, conf, ener)
        bloco["coletado_em"] = agora.isoformat()
        saida[moeda] = bloco
        print("  %-4s conflito z=%-6s razao=%-5s · energia z=%-6s razao=%-5s · tom=%-6s %s"
              % (moeda, conf.get("z"), conf.get("razao"), ener.get("z"), ener.get("razao"), bloco["tom"],
                 (bloco["implicacao"].get("fx") or bloco["implicacao"].get("juro") or "")[:48]))
        m0 = ((bloco["temas"].get("conflito") or {}).get("manchetes") or [])[:1]
        if m0:
            print("       • %s (%s)" % (m0[0]["titulo"][:90], m0[0]["fonte"]))

    if erros:
        print("  ! erros: %d — %s" % (len(erros), "; ".join(erros[:4])))
    def tem_volume(b):
        return any(((b["temas"].get(t) or {}).get("volume") or {}).get("z") is not None for t in TEMAS)
    com_dado = [m for m, b in saida.items() if tem_volume(b)]
    if not com_dado:
        print("  !! GDELT nao respondeu nada util — arquivo anterior preservado")
        sys.exit(1)
    # coleta PARCIAL vale (04/set: 429 por IP deixava tudo de fora). Moeda sem volume nesta
    # rodada carrega a leitura anterior se tiver menos de 24 h — com o carimbo original e a
    # marca `reaproveitado` — senao sai do arquivo e le "not connected" no sentimento.
    reaproveitadas = []
    for m in list(PAIS):
        if m in com_dado:
            continue
        saida.pop(m, None)
        b = (anterior.get("moedas") or {}).get(m)
        if b and b.get("coletado_em") and not b.get("reaproveitado_de"):
            try:
                idade_h = (agora - dt.datetime.fromisoformat(b["coletado_em"])).total_seconds() / 3600.0
            except Exception:
                idade_h = 999
            if idade_h <= 24:
                saida[m] = dict(b, reaproveitado_de=b["coletado_em"])
                reaproveitadas.append("%s (%.0f h)" % (m, idade_h))
        elif b and b.get("reaproveitado_de"):
            try:
                idade_h = (agora - dt.datetime.fromisoformat(b["reaproveitado_de"])).total_seconds() / 3600.0
            except Exception:
                idade_h = 999
            if idade_h <= 24:
                saida[m] = b
                reaproveitadas.append("%s (%.0f h)" % (m, idade_h))
    print("  moedas com dado nesta rodada: %s" % ", ".join(com_dado))
    if reaproveitadas:
        print("  reaproveitadas da rodada anterior: %s" % ", ".join(reaproveitadas))
    # o mundo tambem carrega a rodada anterior quando o 429 o pega
    for tema in TEMAS:
        if not ((mundo.get(tema) or {}).get("volume") or {}).get("z"):
            ant = (anterior.get("mundo") or {}).get(tema)
            if ant and ((ant.get("volume") or {}).get("z") is not None):
                mundo[tema] = dict(ant, reaproveitado=True)

    rel = {"gerado_em": agora.isoformat(),
           "fonte": FONTE_TXT, "metodo": METODO_TXT, "aviso": AVISO_TXT,
           "mundo": mundo, "moedas": saida, "erros": erros}
    enriquece(rel)          # (A) deduplicação · (B) confiabilidade · (C) selo experimental
    print("  manchetes: %d duplicatas removidas pelo agrupamento por evento"
          % rel["duplicatas_removidas_total"])
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1, allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
