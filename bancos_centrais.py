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
CALENDARIO = os.path.join(AQUI, "data", "calendario_resultado.json")

# O cadastro abaixo continua sendo a fonte das reunioes, horarios e convencoes de cada banco.
# A taxa corrente, porem, nao pode ficar congelada nele depois que uma decisao ja foi publicada.
# A reconciliacao usa o mesmo resultado de decisao que alimenta o Calendario do site, mantendo
# todas as telas no mesmo estado ate a conferencia seguinte contra a fonte oficial.
TITULOS_DECISAO = {
    "USD": ("fed interest rate decision", "fomc interest rate decision"),
    "EUR": ("ecb rate on deposit facility", "ecb deposit facility rate"),
    "GBP": ("boe interest rate decision", "official bank rate"),
    "JPY": ("boj interest rate decision",),
    "AUD": ("rba interest rate decision", "cash rate target"),
    "NZD": ("rbnz interest rate decision", "official cash rate"),
    "CAD": ("boc interest rate decision", "overnight rate"),
    "CHF": ("snb interest rate decision", "snb policy rate"),
}

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
        "taxa_texto": "2,25%  (taxa básica 2,50 · depósito 2,20)",
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


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _quando(valor):
    try:
        x = dt.datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        return x.replace(tzinfo=dt.timezone.utc) if x.tzinfo is None else x
    except (TypeError, ValueError):
        return None


DIAS_ATRAS_DECISAO = 120     # PROVISORIO: cobre folgado o intervalo entre reunioes (6 a 8 semanas)


def _eventos_para_decisao(caminho, ao_vivo=True):
    """Os eventos onde procurar a ultima decisao — janela LARGA primeiro, arquivo depois.

    ⚠️ O arquivo data/calendario_resultado.json e uma janela ROLANTE de poucos dias (medido em
    06/set: de 03/set a 13/set). Uma decisao de 02/set ja esta fora dele. Por isso a busca ao
    vivo de %d dias para tras vem PRIMEIRO: sem ela a reconciliacao expira sozinha alguns dias
    depois de cada reuniao e a taxa volta para o cadastro estatico, que fica errado ate alguem
    editar na mao.""" % DIAS_ATRAS_DECISAO
    if not ao_vivo:
        # caminho explicito (teste, ou um arquivo escolhido a mao): le SO o que foi pedido.
        try:
            with io.open(caminho, encoding="utf-8") as arquivo:
                return (json.load(arquivo).get("eventos") or []), "arquivo indicado"
        except Exception:
            return [], "nenhuma"
    try:
        from fxstreet_calendario import buscar, normaliza
        cru = buscar(dias_atras=DIAS_ATRAS_DECISAO, dias_frente=1)
        vivos = [x for x in (normaliza(e) for e in cru) if x]
        if vivos:
            return vivos, "fxstreet %d dias atras" % DIAS_ATRAS_DECISAO
    except Exception as erro:
        print("  ! busca larga de decisoes indisponivel (%s) — usando o arquivo local" % erro)
    try:
        with io.open(caminho, encoding="utf-8") as arquivo:
            return (json.load(arquivo).get("eventos") or []), "arquivo local (janela curta)"
    except Exception:
        return [], "nenhuma"


def decisoes_publicadas(agora=None, caminho=CALENDARIO):
    """Ultima decisao ja publicada por moeda no mesmo calendario exibido pelo site."""
    agora = agora or dt.datetime.now(dt.timezone.utc)
    eventos, origem = _eventos_para_decisao(caminho, ao_vivo=(caminho == CALENDARIO))
    print("  decisoes procuradas em: %s (%d eventos)" % (origem, len(eventos)))
    out = {}
    for evento in eventos:
        moeda = evento.get("moeda")
        titulo = str(evento.get("titulo") or "").strip().lower()
        if moeda not in TITULOS_DECISAO or not any(x in titulo for x in TITULOS_DECISAO[moeda]):
            continue
        quando = _quando(evento.get("quando_utc"))
        taxa = _numero(evento.get("divulgado"))
        if quando is None or quando > agora or taxa is None:
            continue
        atual = out.get(moeda)
        if atual is None or quando > atual["_quando"]:
            out[moeda] = dict(evento, _quando=quando)
    return out


def _taxa_texto(moeda, taxa):
    def pt(v):
        return ("%.2f" % v).replace(".", ",")
    if moeda == "USD":
        return "%s–%s%%" % (pt(taxa - 0.25), pt(taxa))
    if moeda == "CAD":
        # ⚠️ 06/set: nascia em INGLES ("Bank Rate") e a interface remendava no render.
        # A lei da casa e nascer em portugues NA FONTE — o remendo do ui_macro.js
        # continua la, inofensivo, so nao acha mais o que trocar.
        return "%s%%  (taxa básica %s · depósito %s)" % (pt(taxa), pt(taxa + 0.25), pt(taxa - 0.05))
    if moeda == "JPY":
        return "cerca de %s%%" % pt(taxa)
    return "%s%%" % pt(taxa)


def reconcilia_taxa(moeda, banco, evento):
    """Aplica a ultima decisao conhecida sem alterar o cadastro-base global."""
    out = dict(banco)
    if not evento:
        out["taxa_origem"] = "cadastro conferido"
        out["taxa_reconciliada"] = False
        return out

    publicada = _numero(evento.get("divulgado"))
    anterior = _numero(evento.get("anterior"))
    quando = evento["_quando"]
    data_local = quando.astimezone(ZoneInfo(banco["fuso"])).date().isoformat()
    taxa_interna = publicada - 0.125 if moeda == "USD" else publicada
    out["taxa"] = round(taxa_interna, 4)
    out["taxa_texto"] = _taxa_texto(moeda, publicada)
    out["ultima_decisao"] = data_local
    out["ultima_decisao_resultado"] = (
        "alta" if anterior is not None and publicada > anterior else
        "corte" if anterior is not None and publicada < anterior else "manutencao"
    )
    out["taxa_origem"] = "calendario:%s" % (evento.get("fonte") or "resultado publicado")
    out["taxa_confirmada_em"] = quando.isoformat()
    out["taxa_reconciliada"] = True
    if anterior is not None and abs(publicada - anterior) >= 0.001:
        if data_local >= str(out.get("ultima_mudanca") or ""):
            out["ultima_mudanca"] = data_local
            out["ultima_mudanca_bp"] = int(round((publicada - anterior) * 100))
            out["nota_vigencia"] = "reconciliado com o resultado publicado no calendario"
    return out


def memoria_da_reconciliacao(caminho=SAIDA):
    """A ULTIMA decisao ja reconciliada, guardada na propria saida anterior.

    POR QUE EXISTE (medido em 06/set/2026, com o historico do repositorio):
    `decisoes_publicadas` le data/calendario_resultado.json, que e uma JANELA ROLANTE curta —
    hoje ela vai de 03/set a 13/set, ou seja, guarda cerca de tres dias para tras. A decisao do
    RBNZ de 02/set (OCR 2,50 -> 2,75) foi reconciliada e ficou correta no arquivo das 03:02Z de
    05/set ate as 22:19Z do mesmo dia; na rodada das 00:15Z de 06/set a decisao caiu para fora
    da janela, `decisoes_reconciliadas` voltou a ser lista vazia e a taxa do NZD VOLTOU para o
    cadastro estatico: 2,50%, ultima mudanca 08/jul, 60 dias de idade. O painel nao ficou em
    silencio — ficou ERRADO, e o ciclo do NZD (a unica dimensao que vota naquela moeda) passou
    a pesar 0,71 em vez de 0,98.

    Isso nao e caso do NZD: acontece com TODO banco, cerca de tres dias depois de cada decisao.
    A memoria abaixo faz a reconciliacao durar. Ela so vale quando a decisao guardada e mais
    NOVA que a `ultima_mudanca` do cadastro estatico — assim uma correcao feita a mao no
    cadastro continua ganhando da memoria.
    """
    try:
        with io.open(caminho, encoding="utf-8") as arquivo:
            velho = json.load(arquivo)
    except Exception:
        return {}
    out = {}
    for moeda, banco in (velho.get("bancos") or {}).items():
        if not banco.get("taxa_reconciliada"):
            continue
        if not banco.get("taxa_confirmada_em"):
            continue
        out[moeda] = banco
    return out


def aplica_memoria(moeda, banco_calculado, cadastro, lembrado):
    """Devolve o banco com a reconciliacao lembrada, quando ela e mais nova que o cadastro."""
    if not lembrado:
        return banco_calculado
    if banco_calculado.get("taxa_reconciliada"):
        return banco_calculado                      # o calendario ainda tem a decisao: ele manda
    confirmada = str(lembrado.get("taxa_confirmada_em") or "")[:10]
    if not confirmada or confirmada <= str(cadastro.get("ultima_mudanca") or ""):
        return banco_calculado                      # cadastro igual ou mais novo: ele manda
    out = dict(banco_calculado)
    for campo in ("taxa", "taxa_texto", "ultima_decisao", "ultima_decisao_resultado",
                  "ultima_mudanca", "ultima_mudanca_bp", "taxa_confirmada_em"):
        if lembrado.get(campo) is not None:
            out[campo] = lembrado[campo]
    out["taxa_origem"] = "memoria da reconciliacao (%s) — a decisao saiu da janela do calendario" % confirmada
    out["taxa_reconciliada"] = True
    out["taxa_veio_da_memoria"] = True
    out["nota_vigencia"] = ("reconciliado com o resultado publicado no calendario e mantido "
                            "pela memoria depois que a decisao saiu da janela rolante")
    return out


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    hoje = agora.date()
    decisoes = decisoes_publicadas(agora)
    lembradas = memoria_da_reconciliacao()
    out = {}
    for m, b in BANCOS.items():
        futuras = [r for r in b["reunioes"] if dt.date.fromisoformat(r) >= hoje]
        # As listas sao ESTATICAS e acabam em dezembro/2026. Quando sobrar menos de 30 dias de
        # cobertura, grita no log — antes que o campo vire null no site (revisao de 03/set:
        # a partir de 09/dez os 28 pares sairiam "decides today" sem este aviso e sem a guarda
        # que a UI ganhou).
        if b["reunioes"]:
            fim = dt.date.fromisoformat(max(b["reunioes"]))
            if (fim - hoje).days < 30:
                print("  !! %s: a lista de reunioes acaba em %s (%d dias) — ESTENDER para 2027"
                      % (m, fim, (fim - hoje).days))
        prox = futuras[0] if futuras else None
        out[m] = aplica_memoria(m, reconcilia_taxa(m, b, decisoes.get(m)), b, lembradas.get(m))
        out[m]["proxima"] = prox
        out[m]["dias_ate"] = (dt.date.fromisoformat(prox) - hoje).days if prox else None
        out[m]["proxima_utc"] = em_utc(prox, b["hora_local"], b["fuso"]) if prox else None
        out[m]["coletiva_utc"] = em_utc(prox, b["coletiva_local"], b["fuso"]) if prox else None

    rel = {
        "gerado_em": agora.isoformat(),
        "fonte": "cadastro oficial conferido + reconciliacao com decisoes publicadas no calendario",
        "convencao": "ultima_mudanca = data do ANUNCIO; hora sempre LOCAL + fuso IANA",
        "integridade": {
            "decisoes_reconciliadas": sorted(decisoes),
            "regra": "uma decisao divulgada no Calendario atualiza a taxa usada em todas as abas",
        },
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
