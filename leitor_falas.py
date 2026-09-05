# -*- coding: utf-8 -*-
"""LEITOR DE FALAS — classificador de discurso de banco central POR CONTEXTO, nao por contagem.

PARA QUE SERVE (prioridade 3 da revisao do dono, 05/set/2026)
    A camada de texto contava palavras soltas. Tres erros REAIS que o dono viu no painel:

      Waller  disse que apoiaria MANTER os juros  -> a contagem marcou "hawkish"
      Warsh   falou em preservar liberdade para decidir (nem alta nem corte) -> "hawkish"
      Barr    e hawkish, mas CONDICIONAL ("se a inflacao nao moderar") -> "hawkish" firme

    Contagem de palavras nao le NEGACAO, nao le CONDICAO, nao le TEMPO VERBAL e nao le
    SUJEITO. Este modulo le as quatro coisas, por regra explicita e auditavel.

REGRA DURA — ESTE CLASSIFICADOR NAO VOTA
    VOTA = False e SELO = "experimental - contexto, nao vota" acompanham o resultado em
    TODA parte (no JSON de cada veredito, no resumo por moeda e na interface). Ele e
    CONTEXTO, como a geopolitica. Nao entra em nenhuma soma, nao move nenhuma leitura.
    Lei do dono (f): dimensao que nao foi validada NAO VOTA, apenas informa.

O QUE SERIA UMA VALIDACAO ACEITAVEL (para ele um dia poder votar)
    Comparar o VEREDITO com a DECISAO SEGUINTE do proprio banco, com amostra declarada:

    1. PIT (point-in-time): so texto publicado ANTES da decisao. A fala entra com a data de
       publicacao; a decisao entra com a data da reuniao. Nada de reler discurso com o
       resultado na mao.
    2. Alvo: a decisao seguinte do banco daquele orador, em tres classes (subiu / manteve /
       cortou). Uma linha por (orador, fala, decisao seguinte).
    3. Amostra minima declarada ANTES de rodar: n >= 200 falas, >= 5 bancos, >= 3 anos, com
       pelo menos 30 falas em cada uma das tres classes de decisao. Amostra menor nao conclui.
    4. Referencia obrigatoria: a taxa de acerto do palpite burro "sempre MANUTENCAO" — que
       acerta a grande maioria das reunioes. O classificador so serve se ganhar DESSA
       referencia, e a diferenca precisa sobreviver a um teste com a amostra declarada.
    5. Os vereditos CONDICIONAIS sao avaliados a parte: a pergunta neles nao e "o banco
       subiu?", e "o banco subiu QUANDO a condicao se realizou?". Sem separar, o condicional
       contamina a conta.
    6. Fora da amostra: calibrar em uma janela e medir em outra, com a regra congelada.
    7. Enquanto isso nao existir, o campo "vota" segue false — nao ha atalho.

COMO A REGRA FUNCIONA (ordem de leitura de cada frase)
    1. SUJEITO   a frase trata de politica de juros? Se trata de cedula, pagamentos,
                 regulacao ou tema institucional, o veredito e INDETERMINADO.
    2. MARCADOR  procura expressao de ALTA, CORTE ou MANUTENCAO (nao palavra solta:
                 expressao, com o objeto junto — "raise the policy rate", nao "raise").
    3. TEMPO     marcador dentro de oracao no passado ("we raised", "the tightening we
                 delivered", ano anterior) e DESCARTADO: nao e postura sobre o proximo passo.
    4. TERCEIROS marcador que descreve expectativa de MERCADO ("prospective hikes",
                 "expected Bank Rate increases") e DESCARTADO: nao e postura do orador.
    5. NEGACAO   cue de negacao na mesma oracao e ANTES do marcador ("no need to raise",
                 "would not support a cut", "sem pressa para cortar") anula o marcador. Sem
                 outro marcador firme, o veredito vira MANUTENCAO (negar mexer e ficar
                 parado) — com o motivo escrito.
    6. CONDICAO  "if", "should inflation", "caso os dados piorem" rebaixam ALTA e CORTE para
                 ALTA CONDICIONAL / CORTE CONDICIONAL. A MANUTENCAO nao e rebaixada: manter
                 sob condicao continua sendo manter (nao existe "manutencao condicional" na
                 lista de vereditos, e o proximo passo esperado continua o mesmo).

FORCA DO SINAL (maior manda, tanto dentro da frase quanto entre falas do mesmo orador)
    4 firme         marcador limpo: sem condicao (ou manutencao), sem negacao, sem passado,
                    sem atribuicao a terceiros
    3 negacao       manutencao deduzida da negacao explicita de um movimento
    2 condicional   alta condicional / corte condicional
    1 nada          indeterminado

    Duas posturas FIRMES diferentes na mesma frase -> indeterminado (contradicao).
    Entre falas do mesmo orador, se as firmes divergirem vale a MAIS RECENTE, e o motivo diz
    que houve postura diferente antes. Se divergirem no MESMO dia -> indeterminado.

VEREDITOS POSSIVEIS
    "alta", "corte", "manutenção", "alta condicional", "corte condicional", "indeterminado"

TODO LIMIAR AQUI E PROVISORIO (lei do dono (e)) e esta marcado como tal no JSON.
As expressoes sao em ingles e em portugues: os cinco bancos conectados publicam em ingles,
e o dono escreve os exemplos em portugues.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DISCURSOS = os.path.join(AQUI, "data", "bc_discursos.json")

VERSAO = "leitor_falas v0.1 (05/set/2026) — regras PROVISÓRIAS, sem validação histórica"
SELO = "experimental — contexto, não vota"
VOTA = False
VEREDITOS = ("alta", "corte", "manutenção", "alta condicional", "corte condicional",
             "indeterminado")

VALIDACAO_ACEITAVEL = (
    "Só passa a votar depois de comparar o veredito com a DECISÃO SEGUINTE do próprio banco, "
    "ponto-no-tempo (só texto publicado antes da reunião), em amostra declarada antes de rodar: "
    "n ≥ 200 falas, ≥ 5 bancos, ≥ 3 anos, com pelo menos 30 falas em cada classe de decisão "
    "(subiu / manteve / cortou); tem de ganhar da referência burra “sempre manutenção”; os "
    "vereditos condicionais são medidos à parte (o banco subiu QUANDO a condição se realizou?); "
    "e a regra é congelada antes da janela de fora da amostra. Nada disso existe hoje."
)

# ------------------------------------------------------------------------------- normalizacao
def _normaliza(texto: str) -> str:
    """Minusculas, sem acento e com aspas tipograficas viradas em ASCII.

    Sem isto, "não" e "nao" sao duas coisas, e o apostrofo curvo de "it's" quebra o \bn't\b.
    O TRECHO devolvido ao dono e sempre o ORIGINAL — a normalizacao so serve para casar regra.
    """
    t = texto or ""
    for de, para in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                     ("–", "-"), ("—", "-"), (" ", " ")):
        t = t.replace(de, para)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).lower().strip()


# ------------------------------------------------------------------------- SUJEITO (assunto)
# A frase e sobre a politica de juros? Termos ja normalizados (minuscula, sem acento).
SUJEITO_POLITICA = [
    "policy rate", "interest rate", "bank rate", "cash rate", "official cash rate",
    "federal funds", "monetary policy", "policy stance", "rate decision", "target range",
    "inflation", "disinflation", "price stability", "restrictive", "accommodative",
    "quantitative tightening", "quantitative easing", "tightening", "easing", "rate hike",
    "rate cut", "juros", "taxa basica", "taxa de juros", "politica monetaria", "inflacao",
    "selic", "aperto monetario", "afrouxamento", "taxa de referencia",
]

# Se NENHUM termo de politica aparecer e um destes aparecer, o motivo diz QUAL era o assunto.
OUTRO_ASSUNTO = {
    "cédula": ["bank note", "banknote", "bank-note", "polymer note", "currency note",
               "note series", "cedula", "papel-moeda"],
    "pagamentos e moeda digital": ["payment system", "payments", "instant payment", "cbdc",
                                   "digital euro", "digital currency", "stablecoin",
                                   "on-chain", "tokenis", "tokeniz", "settlement system",
                                   "pagamentos", "moeda digital"],
    "regulação e supervisão": ["supervision", "supervisory", "capital requirement", "basel",
                               "stress test", "prudential", "regulation", "regulatory",
                               "licensing", "supervisao", "regulacao", "resolution regime"],
    "tema institucional": ["museum", "anniversary", "award", "criminal record",
                           "financial literacy", "governance of the bank", "recruitment",
                           "tribute", "aniversario", "homenagem", "premio"],
}

# ------------------------------------------------------------------------------- MARCADORES
# Expressao COM o objeto junto. "raise" sozinho nao entra: casa com "raise questions".
# "tighten" sozinho tambem nao: casa com "tighten financial conditions", que nao e o juro.
MARCADORES_ALTA = [
    (r"rais(?:e|ing) (?:the |our |its )?(?:policy |interest |target |bank |cash |official )*rates?\b", "subir os juros"),
    (r"rais(?:e|ing) the (?:target|federal funds)\b", "subir o alvo dos juros"),
    (r"increas(?:e|ing) (?:the |our )?(?:policy |interest |target |bank )*rates?\b", "elevar os juros"),
    (r"increase the target\b", "elevar o alvo dos juros"),
    (r"\brate (?:hike|increase|rise)s?\b", "alta de juros"),
    (r"\b(?:to|will|would|should|may|might|another) hikes?\b", "alta de juros"),
    (r"\bhikes? in (?:the )?(?:policy |bank )?rates?\b", "alta de juros"),
    (r"\bfurther (?:rate )?(?:increases|hikes|tightening)\b", "mais aperto"),
    (r"\badditional tightening\b", "aperto adicional"),
    (r"tighten(?:ing)? (?:monetary )?policy\b", "apertar a política"),
    (r"\bpolicy (?:needs to be|should be|must be) tighten", "apertar a política"),
    (r"\bhigher (?:policy |interest |bank )?rates\b", "juros mais altos"),
    (r"\bmore restrictive\b", "mais restritivo"),
    (r"the tightening (?:that )?we (?:delivered|implemented|undertook|did)\b", "o aperto que já fizemos"),
    (r"\bsubir (?:os |as |a )?(?:juros|taxa)", "subir os juros"),
    (r"\belevar (?:a |as |os )?(?:taxa|juros)", "elevar os juros"),
    (r"\balta (?:de |dos |da )?juros\b", "alta de juros"),
    (r"\baumentar (?:a |os )?(?:taxa|juros)", "aumentar os juros"),
]

MARCADORES_CORTE = [
    (r"cut(?:ting)? (?:the |our |its )?(?:policy |interest |target |bank |cash |official )*rates?\b", "cortar os juros"),
    (r"\brate (?:cut|reduction)s?\b", "corte de juros"),
    (r"cuts? in (?:the )?(?:policy |bank )?rates?\b", "corte de juros"),
    (r"lower(?:ing)? (?:the |our |its )?(?:policy |interest |target |bank |cash )*rates?\b", "baixar os juros"),
    (r"reduc(?:e|ing) (?:the |our |its )?(?:policy |interest |target |bank )*rates?\b", "reduzir os juros"),
    (r"eas(?:e|ing) (?:monetary )?policy\b", "afrouxar a política"),
    (r"\beasing cycle\b", "ciclo de corte"),
    (r"\bless restrictive\b", "menos restritivo"),
    (r"\bmove towards? neutral\b", "caminhar para o neutro"),
    (r"\binsurance cut\b", "corte preventivo"),
    (r"\bcortar (?:os |as |a )?(?:juros|taxa)", "cortar os juros"),
    (r"\bcorte (?:de |dos |da )?juros\b", "corte de juros"),
    (r"\breduzir (?:a |os )?(?:taxa|juros)", "reduzir os juros"),
    (r"\bbaixar (?:os |a )?(?:juros|taxa)", "baixar os juros"),
]

MARCADORES_MANUTENCAO = [
    (r"hold(?:ing)? (?:the )?(?:target|policy rate|bank rate|cash rate|rates?)\b", "manter os juros"),
    (r"\brates? on hold\b", "juros parados"),
    (r"\bon hold\b", "parado"),
    (r"\bhold for now\b", "manter por ora"),
    (r"\bhold steady\b", "manter estável"),
    (r"keep(?:ing)? (?:the )?(?:policy |bank |cash )?rates? (?:at|on hold|unchanged|steady|where)", "manter os juros"),
    (r"keep(?:ing)? (?:the )?target\b", "manter o alvo dos juros"),
    (r"\bcomfortable holding\b", "confortável em manter"),
    (r"leav(?:e|ing) (?:the )?(?:policy |bank |cash )?rates? unchanged\b", "deixar os juros inalterados"),
    (r"\brates? unchanged\b", "juros inalterados"),
    (r"\bat its current setting\b", "no patamar atual"),
    (r"\bcurrent setting\b", "patamar atual"),
    (r"maintain (?:the )?current (?:policy|stance|setting|rate)", "manter o patamar atual"),
    (r"\bno (?:rush|hurry)\b", "sem pressa"),
    (r"\bnot in a (?:rush|hurry)\b", "sem pressa"),
    (r"\bbe patient\b", "ter paciência"),
    (r"\bwait for more (?:data|evidence|information)\b", "esperar mais dados"),
    (r"\bwait and see\b", "esperar para ver"),
    (r"\bmanter (?:os |as |a )?(?:juros|taxa)", "manter os juros"),
    (r"\bapoiaria manter\b", "apoiaria manter"),
    (r"\bmanutencao (?:da |dos )?(?:taxa|juros)", "manutenção dos juros"),
    (r"\binalterad", "inalterado"),
    (r"\bsem pressa\b", "sem pressa"),
    (r"\bpaciencia\b", "paciência"),
]

# ------------------------------------------------------------- cues de contexto (PROVISORIOS)
CUES_CONDICAO = [
    r"\bif\b", r"\bshould inflation\b", r"\bshould the\b", r"\bshould price", r"\bshould data\b",
    r"\bwere to\b", r"\bin the event\b", r"\bprovided that\b", r"\bunless\b",
    r"\bdepending on\b", r"\bcontingent on\b", r"\bconditional on\b", r"\bas long as\b",
    r"\bcaso\b", r"\bse a\b", r"\bse o\b", r"\bse os\b", r"\bse as\b", r"\ba depender\b",
]

CUES_PASSADO = [
    r"\b(?:we|i) (?:have |had |already )*(?:raised|lowered|cut|reduced|increased|tightened"
    r"|eased|hiked|delivered|implemented|undertook|supported|began|started|kept|held|decided|voted)\b",
    r"\b(?:has|have) (?:raised|lowered|cut|reduced|increased|tightened|eased|delivered)\b",
    r"\bthe (?:tightening|easing|increases|cuts) (?:that )?we\b",
    r"\blast year\b", r"\bover the past year\b", r"\bin recent years\b", r"\bsince we\b",
    r"\bhad stopped\b", r"\bhad been\b", r"\bto date\b",
    r"\bja (?:subimos|cortamos|elevamos|reduzimos|mantivemos)\b", r"\bno ano passado\b",
]

CUES_NEGACAO = [
    r"\bnot\b", r"n't\b", r"\bcannot\b", r"\bno need\b", r"\bno reason\b", r"\bno urgency\b",
    r"\bno case for\b", r"\bnever\b", r"\bwithout\b", r"\brather than\b", r"\binstead of\b",
    r"\bfar from\b", r"\bnor\b", r"\bnao\b", r"\bnenhuma necessidade\b", r"\bsem necessidade\b",
]
# "no rush"/"no hurry" NAO entram aqui como negacao pura: eles ja sao marcador de MANUTENCAO
# (e, estando antes do movimento, negam o movimento pela regra normal de negacao).
CUES_NEGACAO += [r"\bno rush\b", r"\bno hurry\b", r"\bsem pressa\b"]

CUES_TERCEIROS = [r"\bthe markets?\b", r"\bmarkets\b", r"\bmarket participants\b",
                  r"\binvestors\b", r"\btraders\b", r"\banalysts\b", r"\bo mercado\b",
                  r"\bos mercados\b"]
CUES_ORADOR = [r"\bi\b", r"\bwe\b", r"\bmy\b", r"\bour\b", r"\bthe mpc\b", r"\bthe committee\b",
               r"\bthe fomc\b", r"\bthe council\b", r"\bgoverning council\b", r"\bthe bank\b",
               r"\bthe fed\b", r"\bpolicymakers\b", r"\bthe board\b", r"\bthe rba\b",
               r"\bthe boj\b", r"\beu\b", r"\bnos\b", r"\bo comite\b", r"\bo banco\b"]

CUES_EXPECTATIVA = [r"\bexpected\b", r"\bprospective\b", r"\banticipated\b", r"\bpriced\b",
                    r"\bpricing\b", r"\bexpectations?\b", r"\bforecast of\b", r"\bimplied\b",
                    r"\besperad", r"\bprecificad"]
JANELA_EXPECTATIVA = 40   # PROVISORIO: caracteres antes do marcador onde o qualificador vale

SEPARADOR_ORACAO = (r"[,;:]|\bthen\b|\bbut\b|\bhowever\b|\bwhile\b|\balthough\b|\bwhereas\b"
                    r"|\byet\b|\bmas\b|\bporem\b|\bentretanto\b|\benquanto\b")

FORCA = {"firme": 4, "negacao": 3, "condicional": 2, "nada": 1}

REGRAS_RESUMO = {
    "ordem": ["sujeito", "marcador", "tempo verbal", "atribuição a terceiros", "negação", "condição"],
    "forca": {"4_firme": "marcador limpo", "3_negacao": "manutenção deduzida da negação",
              "2_condicional": "alta/corte condicional", "1_nada": "indeterminado"},
    "manutencao_sob_condicao": "continua manutenção (não existe veredito 'manutenção condicional')",
    "provisorio": True,
    "janela_expectativa_caracteres": JANELA_EXPECTATIVA,
}


# ------------------------------------------------------------------------------- ferramentas
def _tem(cues: list, texto: str) -> str | None:
    for c in cues:
        m = re.search(c, texto)
        if m:
            return m.group(0)
    return None


def _tem_ano_passado(texto: str) -> str | None:
    ano_agora = dt.date.today().year
    for m in re.finditer(r"\b(19|20)\d{2}\b", texto):
        if int(m.group(0)) < ano_agora:
            return m.group(0)
    return None


def _oracoes(frase_norm: str) -> list:
    """Quebra a frase em oracoes. Sem isto, o 'not' de 'if inflation appears NOT to be
    moderating' negaria o 'raise rates' que vem depois do 'then' — e o Barr viraria corte."""
    partes = [p.strip() for p in re.split(SEPARADOR_ORACAO, frase_norm) if p and p.strip()]
    return partes or [frase_norm]


def _marcadores_da_oracao(oracao: str) -> list:
    achados = []
    for direcao, tabela in (("alta", MARCADORES_ALTA), ("corte", MARCADORES_CORTE),
                            ("manutenção", MARCADORES_MANUTENCAO)):
        for padrao, legivel in tabela:
            for m in re.finditer(padrao, oracao):
                achados.append({"direcao": direcao, "expressao": m.group(0).strip(),
                                "legivel": legivel, "ini": m.start()})
    # marcadores que se sobrepoem: fica o mais longo (evita contar "hikes" dentro de "rate hikes")
    achados.sort(key=lambda a: (a["ini"], -len(a["expressao"])))
    limpos, fim_anterior = [], -1
    for a in achados:
        if a["ini"] >= fim_anterior:
            limpos.append(a)
            fim_anterior = a["ini"] + len(a["expressao"])
    return limpos


def _assunto_da_frase(frase_norm: str) -> dict:
    politica = [t for t in SUJEITO_POLITICA if t in frase_norm]
    if politica:
        return {"e_politica": True, "termo": politica[0], "outro": None}
    for tema, termos in OUTRO_ASSUNTO.items():
        for t in termos:
            if t in frase_norm:
                return {"e_politica": False, "termo": None, "outro": tema}
    return {"e_politica": False, "termo": None, "outro": None}


# --------------------------------------------------------------------- classificador da frase
def classifica_frase(frase: str) -> dict:
    """Le UMA frase e devolve veredito, motivo em portugues e o trecho que o justificou.

    Devolve sempre: veredito, motivo, trecho, forca (1 a 4), selo, vota=False e o detalhe
    dos marcadores encontrados (com o que foi descartado e por que) — para auditoria.
    """
    original = (frase or "").strip()
    trecho = original[:320] + ("..." if len(original) > 320 else "")
    base = {"trecho": trecho, "selo": SELO, "vota": VOTA}
    if len(original) < 12:
        return dict(base, veredito="indeterminado", forca=FORCA["nada"],
                    motivo="frase vazia ou curta demais para ser lida.", marcadores=[])

    # PERGUNTA NAO E POSTURA (regra PROVISORIA, 05/set). Em entrevista quem pergunta e o
    # jornalista, e o marcador que aparece na pergunta e do jornalista, nao do dirigente.
    # Medido no dia: a unica frase com marcador da entrevista do Cipollone (BCE) era
    # "could there be any drawbacks to increasing interest rates to stabilise prices?" —
    # o classificador a lia como postura FIRME de alta (forca 4) e teria carimbado o BCE
    # de hawkish com base numa pergunta de reporter. Nao ha atribuicao de falante no texto,
    # entao a leitura honesta e nao ler.
    if original.rstrip().endswith("?"):
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], marcadores=[],
                    motivo=("a frase é uma PERGUNTA, não uma postura — em entrevista quem "
                            "pergunta é o repórter, e o texto não diz quem fala. Regra "
                            "provisória de 05/set."))

    fn = _normaliza(original)
    condicao = _tem(CUES_CONDICAO, fn)
    firmes, condicionais, negados, descartados = [], [], [], []

    for oracao in _oracoes(fn):
        passado = _tem(CUES_PASSADO, oracao) or _tem_ano_passado(oracao)
        terceiros = _tem(CUES_TERCEIROS, oracao)
        orador = _tem(CUES_ORADOR, oracao)
        for mk in _marcadores_da_oracao(oracao):
            antes = oracao[:mk["ini"]]
            janela = antes[-JANELA_EXPECTATIVA:]
            registro = {"direcao": mk["direcao"], "expressao": mk["expressao"],
                        "legivel": mk["legivel"]}
            if passado:
                descartados.append(dict(registro, descarte="passado", prova=passado))
                continue
            if _tem(CUES_EXPECTATIVA, janela):
                descartados.append(dict(registro, descarte="expectativa de mercado",
                                        prova=_tem(CUES_EXPECTATIVA, janela)))
                continue
            if terceiros and not orador:
                descartados.append(dict(registro, descarte="fala de terceiros", prova=terceiros))
                continue
            neg = _tem(CUES_NEGACAO, antes)
            if neg:
                negados.append(dict(registro, negacao=neg))
                continue
            if condicao and mk["direcao"] in ("alta", "corte"):
                condicionais.append(dict(registro, condicao=condicao))
            else:
                firmes.append(registro)

    # SUJEITO: decidido SO AGORA, porque um marcador de movimento de juros ja prova o assunto.
    # ("we are in no rush to cut rates" nao traz nenhum termo da lista de assunto e e juros.)
    assunto = _assunto_da_frase(fn)
    achou_marcador = bool(firmes or condicionais or negados or descartados)
    if not assunto["e_politica"] and not achou_marcador:
        if assunto["outro"]:
            motivo = ("a frase trata de %s, não de política de juros — sem postura a extrair."
                      % assunto["outro"])
        else:
            motivo = "a frase não trata de política de juros — sem postura a extrair."
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], motivo=motivo,
                    marcadores=[])

    todos = ([dict(f, estado="firme") for f in firmes]
             + [dict(c, estado="condicional") for c in condicionais]
             + [dict(n, estado="negado") for n in negados]
             + [dict(d, estado="descartado") for d in descartados])

    # 1. postura firme
    direcoes_firmes = sorted({f["direcao"] for f in firmes})
    if len(direcoes_firmes) > 1:
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], marcadores=todos,
                    motivo=("a mesma frase traz posturas firmes contraditórias (%s) — não dá "
                            "para dizer o próximo passo." % " e ".join(direcoes_firmes)))
    if direcoes_firmes:
        d = direcoes_firmes[0]
        mk = [f for f in firmes if f["direcao"] == d][0]
        if d == "manutenção":
            extra = (" A condição não muda a manutenção: manter sob condição continua manter."
                     if condicao else "")
            motivo = ("apoio explícito a MANTER os juros (“%s”).%s" % (mk["expressao"], extra))
        else:
            motivo = ("postura firme de %s: “%s”, sem condição, sem negação e sobre o próximo passo."
                      % (d, mk["expressao"]))
        return dict(base, veredito=d, forca=FORCA["firme"], motivo=motivo, marcadores=todos)

    # 2. manutencao deduzida de negacao explicita de movimento
    neg_mov = [n for n in negados if n["direcao"] in ("alta", "corte")]
    if neg_mov:
        n = neg_mov[0]
        return dict(base, veredito="manutenção", forca=FORCA["negacao"], marcadores=todos,
                    motivo=("o orador NEGA o movimento (“%s” aparece negado por “%s”) — negar "
                            "mexer é ficar parado; leitura de manutenção, não de %s."
                            % (n["expressao"], n["negacao"], n["direcao"])))

    # 3. condicional
    direcoes_cond = sorted({c["direcao"] for c in condicionais})
    if len(direcoes_cond) > 1:
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], marcadores=todos,
                    motivo="a frase condiciona alta E corte ao mesmo tempo — sem direção.")
    if direcoes_cond:
        d = direcoes_cond[0]
        c = [x for x in condicionais if x["direcao"] == d][0]
        rotulo = "Alta CONDICIONADA" if d == "alta" else "Corte CONDICIONADO"
        return dict(base, veredito="%s condicional" % d, forca=FORCA["condicional"],
                    marcadores=todos,
                    motivo=("%s: “%s” só vale se a condição se realizar (marcador de condição: "
                            "“%s”) — é cenário, não direção firme."
                            % (rotulo, c["expressao"], c["condicao"])))

    # 4. nada
    if descartados:
        pior = descartados[0]
        if pior["descarte"] == "passado":
            motivo = ("a frase fala do que JÁ foi feito (marca de passado: “%s”), não do "
                      "próximo passo." % pior["prova"])
        elif pior["descarte"] == "expectativa de mercado":
            motivo = ("o que aparece é a expectativa do MERCADO (“%s %s”), não a postura do "
                      "orador." % (pior["prova"], pior["expressao"]))
        else:
            motivo = ("a frase descreve o que TERCEIROS esperam (“%s”), não a postura do orador."
                      % pior["prova"])
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], motivo=motivo,
                    marcadores=todos)
    if negados:
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], marcadores=todos,
                    motivo=("o único marcador da frase está negado (“%s”) e não sobra direção."
                            % negados[0]["expressao"]))
    passado_frase = _tem(CUES_PASSADO, fn) or _tem_ano_passado(fn)
    if passado_frase:
        # O verbo no passado ("we raised") nem chega a virar marcador — os marcadores sao todos
        # de intencao. Sem esta linha, o motivo dizia "nao indica direcao", escondendo o porque.
        return dict(base, veredito="indeterminado", forca=FORCA["nada"], marcadores=todos,
                    motivo=("a frase fala do que JÁ foi feito (marca de passado: “%s”), não do "
                            "próximo passo." % passado_frase))
    return dict(base, veredito="indeterminado", forca=FORCA["nada"], marcadores=todos,
                motivo=("trata de política de juros (“%s”), mas não indica alta, corte nem "
                        "manutenção." % (assunto["termo"] or "juros")))


# ------------------------------------------------------------------- agregacao: fala e orador
def _agrega(resultados: list) -> dict:
    """Junta vereditos de varias frases (ou varias falas) do MESMO orador.

    Cada elemento e o resultado de classifica_frase mais "data" e "link". Regra de precedencia
    descrita no cabecalho: firme > negacao > condicional > nada; firmes divergentes valem pela
    MAIS RECENTE (mesma data divergente = indeterminado)."""
    if not resultados:
        return {"veredito": "indeterminado", "forca": FORCA["nada"], "trecho": "",
                "motivo": "nenhuma frase de postura foi extraída do texto.", "data": None,
                "link": None, "selo": SELO, "vota": VOTA}

    def ordena(lista):
        return sorted(lista, key=lambda r: (r.get("data") or "", r.get("_i", 0)), reverse=True)

    firmes = ordena([r for r in resultados if r["forca"] == FORCA["firme"]])
    if firmes:
        distintos = {r["veredito"] for r in firmes}
        if len(distintos) == 1:
            return dict(firmes[0])
        recentes = [r for r in firmes if (r.get("data") or "") == (firmes[0].get("data") or "")]
        if len({r["veredito"] for r in recentes}) == 1:
            escolha = dict(recentes[0])
            escolha["motivo"] += (" Vale a fala mais recente: houve postura firme diferente antes "
                                  "na mesma janela (%s)." % ", ".join(sorted(distintos)))
            return escolha
        return {"veredito": "indeterminado", "forca": FORCA["nada"],
                "trecho": firmes[0]["trecho"], "data": firmes[0].get("data"),
                "link": firmes[0].get("link"), "selo": SELO, "vota": VOTA,
                "motivo": ("posturas firmes contraditórias no mesmo dia (%s) — sem direção."
                           % ", ".join(sorted(distintos)))}

    negacao = ordena([r for r in resultados if r["forca"] == FORCA["negacao"]])
    if negacao:
        return dict(negacao[0])

    cond = ordena([r for r in resultados if r["forca"] == FORCA["condicional"]])
    if cond:
        distintos = {r["veredito"] for r in cond}
        if len(distintos) == 1:
            return dict(cond[0])
        return {"veredito": "indeterminado", "forca": FORCA["nada"], "trecho": cond[0]["trecho"],
                "data": cond[0].get("data"), "link": cond[0].get("link"), "selo": SELO,
                "vota": VOTA,
                "motivo": "o orador condiciona alta E corte na mesma janela — sem direção."}

    # nenhum sinal: devolve o motivo mais informativo (passado > outro assunto > sem direcao)
    def prioridade(r):
        m = r.get("motivo", "")
        if "JÁ foi feito" in m:
            return 0
        if "MERCADO" in m or "TERCEIROS" in m:
            return 1
        if "não trata de política de juros" in m or "não de política de juros" in m:
            return 2
        return 3
    melhor = sorted(resultados, key=prioridade)[0]
    return dict(melhor)


def classifica_fala(item: dict) -> dict:
    """Classifica UM item de data/bc_discursos.json (usa as frases ja guardadas nele)."""
    resultados = []
    for i, f in enumerate(item.get("frases") or []):
        r = classifica_frase(f.get("frase", ""))
        r["_i"] = i
        r["data"] = item.get("data")
        r["link"] = item.get("link")
        resultados.append(r)
    fim = _agrega(resultados)
    fim.setdefault("data", item.get("data"))
    fim.setdefault("link", item.get("link"))
    fim["data"] = fim.get("data") or item.get("data")
    fim["link"] = fim.get("link") or item.get("link")
    fim["frases_analisadas"] = len(resultados)
    fim["titulo"] = item.get("titulo")
    fim["detalhe_por_frase"] = [{k: v for k, v in r.items() if k != "_i"} for r in resultados]
    fim.pop("_i", None)
    return fim


def vereditos_por_moeda(bc: dict, anotar_itens: bool = True) -> dict:
    """Le o dicionario de data/bc_discursos.json e devolve {MOEDA: [veredito por orador]}.

    Um orador = uma linha, ainda que ele tenha varias falas na janela. Sai ordenado: quem tem
    direcao primeiro, indeterminado por ultimo, e dentro disso pela fala mais recente."""
    por_chave = {}
    for item in bc.get("itens") or []:
        v = classifica_fala(item)
        if anotar_itens:
            item["veredito_leitor"] = {k: v[k] for k in ("veredito", "motivo", "trecho", "forca",
                                                         "selo", "vota", "frases_analisadas")}
        chave = (item.get("moeda"), item.get("orador") or item.get("banco") or "—")
        por_chave.setdefault(chave, []).append((item, v))

    saida = {}
    for (moeda, orador), pares in por_chave.items():
        resultados = []
        for item, v in pares:
            for d in v["detalhe_por_frase"]:
                d = dict(d)
                d["data"] = item.get("data")
                d["link"] = item.get("link")
                resultados.append(d)
        if resultados:
            escolha = _agrega(resultados)
        else:
            escolha = _agrega([])
            escolha["data"] = max(i.get("data") or "" for i, _ in pares) or None
            escolha["link"] = pares[0][0].get("link")
        linha = {
            "orador": orador,
            "veredito": escolha["veredito"],
            "motivo": escolha["motivo"],
            "trecho": escolha.get("trecho") or "",
            "data": escolha.get("data"),
            "link": escolha.get("link"),
            "banco": pares[0][0].get("banco"),
            "falas_lidas": len(pares),
            "frases_analisadas": len(resultados),
            "selo": SELO,
            "vota": VOTA,
        }
        saida.setdefault(moeda, []).append(linha)

    ordem = {"alta": 0, "corte": 0, "manutenção": 1, "alta condicional": 2,
             "corte condicional": 2, "indeterminado": 9}
    for moeda in saida:
        saida[moeda].sort(key=lambda l: (ordem.get(l["veredito"], 5),
                                         -int((l["data"] or "0000-00-00").replace("-", ""))))
    return saida


def vereditos_do_arquivo(caminho: str | None = None) -> dict:
    """Atalho para quem so quer os vereditos (sentimento.py, painel): le o JSON e classifica."""
    caminho = caminho or ARQUIVO_DISCURSOS
    with io.open(caminho, encoding="utf-8") as f:
        return vereditos_por_moeda(json.load(f), anotar_itens=False)


def bloco_para_sentimento(moeda: str, caminho: str | None = None) -> dict:
    """O bloco pronto para dimensoes.texto de data/sentimento.json — ja com vota=false e selo."""
    v = vereditos_do_arquivo(caminho).get(moeda, [])
    return {"vota": False, "selo": SELO, "versao": VERSAO,
            "veredito_por_orador": [{k: l[k] for k in ("orador", "veredito", "motivo", "trecho",
                                                       "data", "link")} for l in v],
            "validacao_aceitavel": VALIDACAO_ACEITAVEL}


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else ARQUIVO_DISCURSOS
    print("=" * 86)
    print("LEITOR DE FALAS — veredito por orador  ·  %s" % SELO)
    print("=" * 86)
    print("  %s" % VERSAO)
    print()
    v = vereditos_do_arquivo(caminho)
    for moeda in sorted(v):
        print("  %s" % moeda)
        for l in v[moeda]:
            print("    %-16s %-18s %s" % (l["orador"][:16], l["veredito"], (l["data"] or "-")))
            print("        motivo: %s" % l["motivo"][:150])
            if l["trecho"]:
                print("        trecho: %s" % l["trecho"][:130])
    print()
    print("  ESTE CLASSIFICADOR NAO VOTA. %s" % SELO)


if __name__ == "__main__":
    main()
