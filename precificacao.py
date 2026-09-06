# -*- coding: utf-8 -*-
"""PRECIFICACAO — o que o MERCADO cobra hoje pela proxima decisao dos OITO bancos centrais.

POR QUE ESTE ARQUIVO EXISTE
    O radar ja tem a LEITURA HCI (sentimento.py). Falta a coluna do lado: o numero que o
    mercado esta pagando. O produto nao e nenhuma das duas — e a DIVERGENCIA entre elas.
    Por isso vale a LEI DO DONO, repetida aqui para nao se perder:

        A PRECIFICACAO NUNCA ENTRA NO SENTIMENTO.
        Ela e dado exibido e coluna de comparacao. Nada daqui vota em nada.

    E a segunda lei: campo sem fonte e None com o MOTIVO escrito. Jamais estimativa
    disfarcada, jamais "provavelmente 60%".

O QUE FUNCIONA (testado ao vivo em 06/set/2026, sem chave e sem cadastro)
    USD  Fed    futuros de fed funds de 30 dias (ZQ) pela API de grafico do Yahoo + EFFR do
                NY Fed. Ja resolvido em fomc_precificacao.py — importado, nao reescrito.
    AUD  RBA    futuros IB (30 Day Interbank Cash Rate) pela API que alimenta o ASX RBA Rate
                Tracker: asx.api.markitdigital.com. E o FedWatch australiano e e gratis.
    NZD  RBNZ   futuros BB (New Zealand 90 Day Bank Bill) na MESMA API da ASX. FUNCIONA, mas
                e taxa a TERMO de 3 meses, nao media mensal: da DIRECAO, nao probabilidade.
                Ver "A ARMADILHA DO CONTRATO A TERMO" abaixo.

    Os tres codigos foram confirmados na propria pagina da ASX, que carrega as abas com
    data-f2-context-code:  IB = "30 day interbank cash rate", IR = "90 day bank bill",
    BB = "New Zealand 90 day bank bill".

O QUE NAO FUNCIONA (testado ao vivo, com o codigo do erro)
    CAD  BoC    m-x.ca serve as cotacoes por widget da QuoteMedia. getEnhancedQuotes e
                getQuotes devolvem 403 FORBIDDEN sem sessao; app.quotemedia.com/auth/v0/session
                devolve 401 e o qmodLoader.js so autentica se o dominio do script bater com um
                hash de uma lista fechada. O produto certo EXISTE e esta identificado —
                COA, One-Month CORRA Futures, media mensal do CORRA, o ZQ canadense — falta
                so a porta. A API Valet do Banco do Canada (livre, sem chave) tem o CORRA
                REALIZADO, nao a curva; nao serve para expectativa.
    EUR  BCE    Eurex: www.eurex.com/api/v1/... devolve 404 em todas as formas testadas.
    GBP  BoE    ICE: DelayedMarkets.shtml?getContractsAsJson devolve 403.
    JPY  BoJ    JPX nao publica preco de TONA 3m em API; so paginas de estatistica.
    CHF  SNB    SARON na Eurex — mesmo 404 do BCE.
    Yahoo so tem contrato da CME (varredura de 30 simbolos: ZQ e SR3 passam, FEU3/SFI/BAX/
    COA/TONA/SARON nao existem). stooq.com devolve 404 ate para eurusd — bloqueia por IP.
    CME e FedWatch estao DESCARTADOS por decisao anterior (Akamai barra robo). Nao insistir.

A CONTA — MES DA REUNIAO MISTURA OS DOIS REGIMES
    ZQ (EUA) e IB (Australia) liquidam pela MEDIA da taxa overnight no MES CIVIL. Logo o mes
    da reuniao nao e "a taxa depois da decisao": e uma mistura.

        taxa_media_do_mes = (base * dias_antes + taxa_pos * dias_depois) / dias_do_mes

    com dias_antes = dia do anuncio (a taxa nova so vale no dia SEGUINTE) e
    dias_depois = dias_do_mes - dias_antes. Invertendo:

        taxa_pos = (taxa_media_do_mes * dias_do_mes - base * dias_antes) / dias_depois

    Note o divisor: quando dias_depois e pequeno, qualquer ruido no preco e multiplicado por
    dias_do_mes/dias_depois. Com a reuniao no dia 29 de um mes de 30 dias o fator e 30x — a
    conta vira lixo. Dai as duas regras (limiares PROVISORIOS):

      (1) Se o mes SEGUINTE ao da reuniao NAO tem outra reuniao, o contrato daquele mes ja E
          a taxa pos-decisao inteira, sem alavancagem de ruido. Usa-se ele. PREFERIDO.
      (2) Senao, usa-se a inversao acima, exigindo dias_depois >= MIN_DIAS_DEPOIS (7) e
          nenhuma SEGUNDA reuniao no mesmo mes.
      (3) Se nenhuma das duas vale, o campo sai None com o motivo.

    E o caso do Fed hoje: a reuniao e 16/set (14 dias depois, passa na regra 2) mas outubro
    TEM reuniao no dia 28 — entao o contrato de outubro esta CONTAMINADO e a regra 1 nao se
    aplica. Ja o RBA e o oposto: reuniao em 29/set (1 dia depois, reprova na regra 2) mas
    outubro NAO tem reuniao do RBA — o contrato de outubro serve limpo.

    Com a taxa pos-decisao na mao, passo de 25 bp:
        delta = taxa_pos - base
        p_alta  = limita(delta / 0,25 , 0, 1)
        p_corte = limita(-delta / 0,25 , 0, 1)
        p_manutencao = 1 - p_alta - p_corte          (soma sempre 1, por construcao)

A ARMADILHA DO CONTRATO A TERMO (por que o NZD nao ganha probabilidade)
    BB liquida pela taxa do bank bill de 90 DIAS na data de expiracao. Ela carrega premio de
    prazo e de credito sobre a OCR, e cobre uma janela de 90 dias que atravessa MAIS DE UMA
    reuniao. Para tirar nivel dela eu precisaria arbitrar o spread bank bill x OCR — que e
    exatamente a estimativa disfarcada que a lei proibe. Entao o NZD sai com DIRECAO
    (inclinacao entre dois contratos, onde o spread se cancela se for constante) e com
    p_alta/p_corte/implicito_bp = None, motivo escrito. Qualidade "baixa".

MANCHETE — a regua ja decidida pelo dono
    Vale so para quem nao tem futuro. Reuters, Bloomberg, FT e WSJ dizendo "markets price
    N bp of cuts by <mes>" ou "NN% chance of a hike" entram com qualidade "media".
      - item com mais de 7 dias e DESCARTADO;
      - republicacao conta uma vez (deduplicacao por Jaccard, reaproveitada de noticias.py);
      - e o numero tem de se referir a PROXIMA REUNIAO, nunca a "ate dezembro".
    A ultima e a armadilha principal e por isso e a regra mais dura daqui: o texto tem de
    trazer uma ancora que resolva para a proxima reuniao (o nome do mes dela, ou "next
    meeting" / "this week" / "next week") e NAO pode trazer nenhum outro nome de mes nem
    termo de horizonte acumulado ("by year-end", "cumulative", "over the next", "next year").
    Na duvida, descarta. Silencio nao e voto.

SAIDA
    data/precificacao.json        as 8 moedas, sempre todas presentes.
    data/precificacao_hist.jsonl  append-only, uma linha por execucao, com p_alta, p_corte e
                                  implicito_bp por moeda. E o que permite mostrar depois
                                  "probabilidade antes e depois do dado".

    Falha de coleta preserva o arquivo anterior e sai com codigo 1.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import fomc_precificacao as FOMC   # noqa: E402  (ZQ no Yahoo + EFFR do NY Fed, ja pronto)
import noticias as NOT             # noqa: E402  (leitor de RSS, deduplicacao, peso de fonte)

CADASTRO = os.path.join(AQUI, "data", "bancos_centrais.json")
SAIDA = os.path.join(AQUI, "data", "precificacao.json")
HIST = os.path.join(AQUI, "data", "precificacao_hist.jsonl")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*"}

MOEDAS = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]

PASSO_BP = 25.0                # passo de politica. Nenhum dos oito move de 10 em 10.
MIN_DIAS_DEPOIS = 7            # PROVISORIO: abaixo disto a inversao amplifica ruido demais
BANDA_MORTA_BP = 3.0           # PROVISORIO: |implicito| <= 3 bp le-se como "manutencao"
JANELA_MANCHETE_D = 7          # regua do dono: item com mais de 7 dias e descartado
JACCARD_DEDUP = 0.70           # mesma regra declarada em noticias.py
PAUSA_S = 1.5

# Os quatro veiculos nomeados pelo dono. So eles dao qualidade "media" por manchete.
VEICULOS_MANCHETE = ["reuters", "bloomberg", "financial times", "ft.com", "wall street journal",
                     "wsj", "dow jones"]

MES_NOME = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
            7: "july", 8: "august", 9: "september", 10: "october", 11: "november",
            12: "december"}
MES_ABREV = {1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "may", 6: "jun", 7: "jul", 8: "aug",
             9: "sep", 10: "oct", 11: "nov", 12: "dec"}
# Codigo de mes dos futuros (mesma convencao da CME e da ASX)
MES_COD = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M", 7: "N", 8: "Q", 9: "U",
           10: "V", 11: "X", 12: "Z"}


# ------------------------------------------------------------------ utilidades minusculas
def _agora():
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _limita01(x):
    return max(0.0, min(1.0, x))


def _get_json(url, headers=None, timeout=25):
    """Baixa JSON. Devolve (dado, erro). Nunca inventa: erro vira texto no relatorio."""
    try:
        req = urllib.request.Request(url, headers=headers or UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, "HTTP %d" % e.code
    except urllib.error.URLError as e:
        return None, "rede: %s" % (getattr(e, "reason", e),)
    except (ValueError, TimeoutError) as e:
        return None, "%s: %s" % (type(e).__name__, e)


def _mes_seguinte(ano, mes):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def _reunioes_no_mes(reunioes, ano, mes):
    """Datas de reuniao que caem naquele mes civil."""
    return [d for d in reunioes if d.year == ano and d.month == mes]


def _direcao(implicito_bp):
    if implicito_bp is None:
        return None
    if implicito_bp > BANDA_MORTA_BP:
        return "alta"
    if implicito_bp < -BANDA_MORTA_BP:
        return "corte"
    return "manutencao"


# --------------------------------------------------------------------------- o cadastro
def le_cadastro():
    """Data da proxima reuniao, taxa vigente e calendario, de data/bancos_centrais.json."""
    with open(CADASTRO, encoding="utf-8") as f:
        j = json.load(f)
    out = {}
    for m in MOEDAS:
        b = (j.get("bancos") or {}).get(m) or {}
        reunioes = []
        for s in (b.get("reunioes") or []):
            try:
                reunioes.append(dt.date.fromisoformat(s))
            except ValueError:
                pass
        prox = None
        if b.get("proxima"):
            try:
                prox = dt.date.fromisoformat(b["proxima"])
            except ValueError:
                prox = None
        out[m] = {"banco": b.get("banco"), "sigla": b.get("sigla"), "taxa": b.get("taxa"),
                  "nome_taxa": b.get("nome_taxa"), "proxima": prox,
                  "reunioes": sorted(reunioes)}
    return out


# ------------------------------------------------- CAMADA A: futuro de taxa MEDIA MENSAL
def escolhe_contrato(reuniao, reunioes, precos, base, rotulo_fonte):
    """Aplica as tres regras do cabecalho e devolve taxa_pos + a conta por extenso.

    precos: funcao (ano, mes) -> {"sym", "preco", "hora"} ou None.
    base:   taxa overnight vigente hoje (EFFR nos EUA, alvo no resto).
    """
    ano_m, mes_m = reuniao.year, reuniao.month
    ano_s, mes_s = _mes_seguinte(ano_m, mes_m)
    n_dias = calendar.monthrange(ano_m, mes_m)[1]
    dias_antes = reuniao.day               # taxa nova vale a partir do dia seguinte
    dias_depois = n_dias - dias_antes
    no_mes = _reunioes_no_mes(reunioes, ano_m, mes_m)
    no_seg = _reunioes_no_mes(reunioes, ano_s, mes_s)

    c_mes = precos(ano_m, mes_m)
    c_seg = precos(ano_s, mes_s)
    passos = []

    # --- regra 1: mes seguinte limpo (sem reuniao) -> o contrato JA e a taxa pos-decisao
    if c_seg and not no_seg:
        taxa_pos = 100.0 - c_seg["preco"]
        passos.append(
            "regra 1 (preferida): %s nao tem reuniao deste banco, entao %s = %.4f e a taxa "
            "pos-decisao inteira -> taxa_pos = 100 - %.4f = %.4f."
            % (MES_NOME[mes_s], c_seg["sym"], c_seg["preco"], c_seg["preco"], taxa_pos))
        conta_mes = None
        if c_mes:
            tm = 100.0 - c_mes["preco"]
            conta_mes = round((tm * n_dias - base * dias_antes) / dias_depois, 4) if dias_depois else None
            # Se sobram poucos dias no mes da reuniao, esta segunda conta NAO e uma segunda
            # medida: e a primeira multiplicada por n_dias/dias_depois, ruido inclusive. Ela
            # fica no relatorio para mostrar que o mercado nao mexe ANTES da reuniao, e sai
            # rotulada — dois numeros diferentes aqui nao sao contradicao.
            fragil = dias_depois < MIN_DIAS_DEPOIS
            passos.append(
                "conferencia pelo mes da reuniao: %s = %.4f -> media do mes %.4f; "
                "%d dias a %.4f + %d dias a taxa_pos => taxa_pos = (%.4f*%d - %.4f*%d)/%d = %s.%s"
                % (c_mes["sym"], c_mes["preco"], tm, dias_antes, base, dias_depois,
                   tm, n_dias, base, dias_antes, dias_depois,
                   ("%.4f" % conta_mes) if conta_mes is not None else "indefinido (0 dias depois)",
                   ((" ATENCAO: so %d dia(s) depois da reuniao neste mes, entao esta conta "
                     "amplifica o ruido do preco em %.0fx e NAO vale como segunda medida — "
                     "o que ela mostra e que o mercado nao espera mudanca ANTES do dia %d."
                     % (dias_depois, n_dias / max(dias_depois, 1), dias_antes)) if fragil else "")))
            if fragil:
                conta_mes = None
        return {"taxa_pos": taxa_pos, "regra": "mes seguinte limpo",
                "contrato_usado": c_seg["sym"], "contrato_mes_reuniao": c_mes["sym"] if c_mes else None,
                "taxa_pos_conferencia": conta_mes, "dias_antes": dias_antes,
                "dias_depois": dias_depois, "dias_do_mes": n_dias,
                "conta": " ".join(passos), "fonte": rotulo_fonte}, None

    # --- regra 2: inversao no proprio mes da reuniao
    motivo_1 = ("contrato do mes seguinte indisponivel" if not c_seg else
                "mes seguinte tem reuniao em %s (contrato contaminado)"
                % ", ".join(d.isoformat() for d in no_seg))
    if not c_mes:
        return None, "%s; e o contrato do mes da reuniao tambem nao veio" % motivo_1
    if len(no_mes) > 1:
        return None, ("%s; e o mes da reuniao tem %d reunioes (%s), a inversao de um so "
                      "passo nao vale" % (motivo_1, len(no_mes),
                                          ", ".join(d.isoformat() for d in no_mes)))
    if dias_depois < MIN_DIAS_DEPOIS:
        return None, ("%s; e a reuniao cai no dia %d de %d, sobrando %d dia(s) — abaixo do "
                      "minimo PROVISORIO de %d, a inversao multiplicaria o ruido por %.0fx"
                      % (motivo_1, dias_antes, n_dias, dias_depois, MIN_DIAS_DEPOIS,
                         n_dias / max(dias_depois, 1)))
    taxa_mes = 100.0 - c_mes["preco"]
    taxa_pos = (taxa_mes * n_dias - base * dias_antes) / dias_depois
    passos.append(
        "regra 2 (%s): %s = %.4f -> taxa media do mes = 100 - %.4f = %.4f. "
        "O mes tem %d dias: %d antes do anuncio (dia %d, taxa nova so no dia seguinte) a "
        "%.4f, e %d depois a taxa_pos. Invertendo: taxa_pos = (%.4f*%d - %.4f*%d)/%d = %.4f."
        % (motivo_1, c_mes["sym"], c_mes["preco"], c_mes["preco"], taxa_mes, n_dias,
           dias_antes, dias_antes, base, dias_depois, taxa_mes, n_dias, base, dias_antes,
           dias_depois, taxa_pos))
    return {"taxa_pos": taxa_pos, "regra": "inversao no mes da reuniao",
            "contrato_usado": c_mes["sym"], "contrato_mes_reuniao": c_mes["sym"],
            "taxa_pos_conferencia": None, "dias_antes": dias_antes,
            "dias_depois": dias_depois, "dias_do_mes": n_dias,
            "conta": " ".join(passos), "fonte": rotulo_fonte}, None


def probabilidades(taxa_pos, base):
    """Passo de 25 bp. p_alta + p_corte + p_manutencao == 1 por construcao."""
    delta = taxa_pos - base
    p_alta = _limita01(delta / (PASSO_BP / 100.0))
    p_corte = _limita01(-delta / (PASSO_BP / 100.0))
    p_man = _limita01(1.0 - p_alta - p_corte)
    return round(delta * 100.0, 2), round(p_alta, 4), round(p_corte, 4), round(p_man, 4)


# ------------------------------------------------------------------------- USD (ZQ + EFFR)
def fed(cad):
    """Reaproveita fomc_precificacao.py: ZQ na API de grafico do Yahoo + EFFR do NY Fed.

    Diferenca deliberada: fomc_precificacao prefere sempre o contrato do mes SEGUINTE. Aqui
    esse atalho so vale se aquele mes nao tiver reuniao — e em outubro/2026 tem (dia 28).
    Por isso a taxa pos-decisao sai da INVERSAO no mes da reuniao (regra 2).
    """
    reuniao = cad["proxima"]
    if not reuniao:
        return None, "sem data de proxima reuniao no cadastro"
    e = FOMC.effr_atual()
    if not e:
        return None, "EFFR do NY Fed nao respondeu"
    base = e["taxa"]

    cache = {}

    def precos(ano, mes):
        sym = FOMC.simbolo_zq(ano, mes)
        if sym not in cache:
            q = FOMC.yahoo_ultimo(sym)
            cache[sym] = {"sym": sym, "preco": q["preco"], "hora": q["hora"]} if q else None
        return cache[sym]

    esc, erro = escolhe_contrato(reuniao, cad["reunioes"], precos, base,
                                "futuros de fed funds 30d (ZQ, CME) via API de grafico do "
                                "Yahoo + EFFR do NY Fed")
    if not esc:
        return None, erro
    imp, pa, pc, pm = probabilidades(esc["taxa_pos"], base)
    esc["conta"] = ("base = EFFR %.4f%% de %s (NY Fed). " % (base, e["data"])) + esc["conta"] + (
        " delta = %.4f - %.4f = %+.2f bp. Passo 25 bp: p_alta = %.4f, p_corte = %.4f, "
        "p_manutencao = %.4f." % (esc["taxa_pos"], base, imp, pa, pc, pm))
    esc.update({"base_taxa": base, "base_origem": "EFFR do NY Fed (%s)" % e["data"],
                "taxa_pos": round(esc["taxa_pos"], 4),
                "implicito_bp": imp, "p_alta": pa, "p_corte": pc, "p_manutencao": pm})
    return esc, None


# ------------------------------------------------------------------- ASX (RBA e RBNZ)
ASX_URL = ("https://asx.api.markitdigital.com/asx-research/1.0/derivatives/interest-rate/"
           "%s/futures?days=1&height=179&width=179")
ASX_HDR = dict(UA, **{"Referer": "https://www.asx.com.au/", "Accept-Language": "en-AU,en;q=0.9"})


def asx_cadeia(codigo):
    """Cadeia de um produto de juro da ASX. codigo: IB, IR ou BB.

    Os tres codigos vieram da propria pagina da ASX (atributo data-f2-context-code):
      IB = 30 day interbank cash rate | IR = 90 day bank bill | BB = New Zealand 90 day bank bill.
    Preco usado: pricePreviousSettlement (a marcacao oficial do dia; existe ate em mes sem
    negocio), com priceLastTrade de reserva.
    """
    j, erro = _get_json(ASX_URL % codigo, headers=ASX_HDR)
    if j is None:
        return None, "ASX %s: %s" % (codigo, erro)
    itens = ((j.get("data") or {}).get("items")) or []
    if not itens:
        return None, "ASX %s: cadeia vazia" % codigo
    out = []
    for x in itens:
        p = x.get("pricePreviousSettlement")
        origem = "settlement"
        if p is None:
            p = x.get("priceLastTrade")
            origem = "ultimo negocio"
        if p is None:
            continue
        try:
            venc = dt.date.fromisoformat(x["dateExpiry"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append({"sym": x.get("symbol"), "preco": float(p), "origem_preco": origem,
                    "vencimento": venc.isoformat(), "hora": x.get("datePreviousSettlement"),
                    "volume": x.get("volume")})
    if not out:
        return None, "ASX %s: nenhum contrato com preco" % codigo
    return out, None


def rba(cad):
    """RBA pelo IB — 30 Day Interbank Cash Rate, a media da taxa de caixa no mes civil.

    Base: o alvo do cadastro. O cash rate australiano negocia praticamente no alvo, e isso e
    CONFERIDO aqui mesmo contra o contrato do mes corrente (campo conferencia_base) — nao e
    suposicao cega.
    """
    reuniao = cad["proxima"]
    if not reuniao:
        return None, "sem data de proxima reuniao no cadastro"
    if cad.get("taxa") is None:
        return None, "sem taxa vigente no cadastro"
    base = float(cad["taxa"])
    cadeia, erro = asx_cadeia("IB")
    if cadeia is None:
        return None, erro
    # O simbolo da ASX e do tipo IBU2026 (produto + codigo de mes + ano com 4 digitos)
    por_mes = {}
    for c in cadeia:
        m = re.match(r"^IB([FGHJKMNQUVXZ])(\d{4})$", c["sym"] or "")
        if not m:
            continue
        mes = [k for k, v in MES_COD.items() if v == m.group(1)][0]
        por_mes[(int(m.group(2)), mes)] = c

    def precos(ano, mes):
        return por_mes.get((ano, mes))

    esc, erro = escolhe_contrato(reuniao, cad["reunioes"], precos, base,
                                "futuros IB (30 Day Interbank Cash Rate, ASX) via "
                                "asx.api.markitdigital.com — a API do ASX RBA Rate Tracker")
    if not esc:
        return None, erro
    imp, pa, pc, pm = probabilidades(esc["taxa_pos"], base)

    # conferencia da base contra o mercado, para nao usar o alvo no escuro
    hoje = dt.date.today()
    c_hoje = por_mes.get((hoje.year, hoje.month))
    conf = None
    if c_hoje:
        taxa_hoje = 100.0 - c_hoje["preco"]
        n = calendar.monthrange(hoje.year, hoje.month)[1]
        r_no_mes = _reunioes_no_mes(cad["reunioes"], hoje.year, hoje.month)
        if r_no_mes:
            d_depois = n - r_no_mes[0].day
            conf = ("%s implica media de %.4f%% no mes; com a reuniao no dia %d sobram %d "
                    "dia(s) de taxa nova, entao os outros %d dias correm na base — a base do "
                    "cadastro (%.4f%%) fecha com o mercado dentro de %.1f bp."
                    % (c_hoje["sym"], taxa_hoje, r_no_mes[0].day, d_depois, n - d_depois,
                       base, abs(taxa_hoje - base) * 100.0 * n / max(n - d_depois, 1)))
        else:
            conf = ("%s implica media de %.4f%% num mes sem reuniao: e a propria taxa de "
                    "caixa. Base do cadastro = %.4f%%, diferenca %.1f bp."
                    % (c_hoje["sym"], taxa_hoje, base, (taxa_hoje - base) * 100.0))
    esc["conta"] = ("base = alvo vigente do RBA %.4f%% (data/bancos_centrais.json). "
                    % base) + esc["conta"] + (
        " delta = %.4f - %.4f = %+.2f bp. Passo 25 bp: p_alta = %.4f, p_corte = %.4f, "
        "p_manutencao = %.4f." % (esc["taxa_pos"], base, imp, pa, pc, pm))
    esc.update({"base_taxa": base, "base_origem": "alvo vigente no cadastro do radar",
                "conferencia_base": conf, "taxa_pos": round(esc["taxa_pos"], 4),
                "implicito_bp": imp, "p_alta": pa, "p_corte": pc, "p_manutencao": pm,
                "cadeia": [{k: c[k] for k in ("sym", "preco", "vencimento", "volume")}
                           for c in cadeia[:6]]})
    return esc, None


def rbnz(cad):
    """RBNZ pelo BB — New Zealand 90 Day Bank Bill. SO DIRECAO, e o motivo esta escrito.

    BB e taxa a TERMO de 90 dias: carrega premio de prazo e de credito sobre a OCR e cobre
    uma janela que atravessa mais de uma reuniao. Tirar nivel dela exigiria arbitrar o spread
    bank bill x OCR — estimativa disfarcada, proibida. O que sobra sem suposicao nenhuma e a
    INCLINACAO entre dois vencimentos: se o spread for constante, ele se cancela na subtracao
    e o que resta e a mudanca de politica esperada entre as duas janelas.
    """
    cadeia, erro = asx_cadeia("BB")
    if cadeia is None:
        return None, erro
    cadeia = sorted(cadeia, key=lambda c: c["vencimento"])
    hoje = dt.date.today().isoformat()
    frente = [c for c in cadeia if c["vencimento"] >= hoje]
    if len(frente) < 2:
        return None, "ASX BB: menos de dois vencimentos futuros na cadeia"
    c1, c2 = frente[0], frente[1]
    r1, r2 = 100.0 - c1["preco"], 100.0 - c2["preco"]
    inclinacao_bp = round((r2 - r1) * 100.0, 2)
    return {"metodo": "futuros", "qualidade": "baixa",
            "fonte": ("futuros BB (New Zealand 90 Day Bank Bill, ASX) via "
                      "asx.api.markitdigital.com"),
            "implicito_bp": None, "p_alta": None, "p_corte": None, "p_manutencao": None,
            "direcao_mercado": _direcao(inclinacao_bp),
            "inclinacao_bp": inclinacao_bp,
            "motivo_sem_probabilidade": (
                "BB e taxa a TERMO de 90 dias, nao media mensal da OCR: carrega premio de "
                "prazo e de credito e cobre uma janela que atravessa mais de uma reuniao. "
                "Converter em probabilidade da proxima reuniao exigiria arbitrar o spread "
                "bank bill x OCR, que seria estimativa sem fonte. Fica so a direcao."),
            "conta": ("%s (vence %s) = %.4f -> taxa 90d implicita %.4f%%; %s (vence %s) = "
                      "%.4f -> %.4f%%. Inclinacao = %+.2f bp entre as duas janelas de 90 "
                      "dias. Como o spread bank bill x OCR entra igual nas duas, ele se "
                      "cancela na subtracao e o sinal da inclinacao e a direcao esperada da "
                      "politica. O NIVEL nao sobrevive a essa conta."
                      % (c1["sym"], c1["vencimento"], c1["preco"], r1,
                         c2["sym"], c2["vencimento"], c2["preco"], r2, inclinacao_bp)),
            "cadeia": [{k: c[k] for k in ("sym", "preco", "vencimento", "volume")}
                       for c in frente[:4]]}, None


# --------------------------------------------------- CAMADA C: extracao por MANCHETE
# Numero + tipo de movimento. Dois formatos, os dois nomeados pelo dono.
RX_PCT = re.compile(
    r"(\d{1,3}(?:\.\d)?)\s*(?:%|per\s*cent|percent)\s*(?:\w+\s+){0,3}?"
    r"(?:chance|probability|odds|likelihood|priced|prob)", re.I)
RX_PCT2 = re.compile(
    r"(?:chance|probability|odds|likelihood)\s+(?:\w+\s+){0,3}?of\s+(?:about\s+|around\s+)?"
    r"(\d{1,3}(?:\.\d)?)\s*(?:%|per\s*cent|percent)", re.I)
RX_BP = re.compile(r"(\d{1,3})\s*(?:bp|bps|basis\s*points?)\b", re.I)

RX_ALTA = re.compile(r"\b(hike|hikes|hiking|raise|raises|raising|increase|increases|"
                     r"tighten|tightening|higher rates?)\b", re.I)
RX_CORTE = re.compile(r"\b(cut|cuts|cutting|reduction|reductions|lower|lowering|ease|"
                      r"easing|loosen|loosening)\b", re.I)

# Termos que denunciam numero ACUMULADO ate um horizonte: motivo de descarte automatico.
RX_HORIZONTE = re.compile(
    r"\b(year[- ]end|end of (?:the )?year|by the end of|cumulative|cumulatively|in total|"
    r"over the (?:next|coming)|through(?:out)? (?:the )?(?:rest|end)|next year|"
    r"by mid[- ]|over the year|full year|this year|by 20\d\d|in 20\d\d)\b", re.I)
RX_PROXIMA_GENERICA = re.compile(
    r"\b(next meeting|this meeting|upcoming meeting|next week(?:'s)? meeting|"
    r"this week(?:'s)? meeting|next policy meeting|this month(?:'s)? meeting)\b", re.I)

CONSULTAS_PRECO = {
    "EUR": ['"European Central Bank" markets price rate decision probability',
            'ECB traders price basis points next meeting'],
    "GBP": ['"Bank of England" markets price rate decision probability',
            'BoE traders price basis points next meeting'],
    "JPY": ['"Bank of Japan" markets price rate decision probability',
            'BOJ traders price basis points next meeting'],
    "CAD": ['"Bank of Canada" markets price rate decision probability',
            'BoC traders price basis points next meeting'],
    "CHF": ['"Swiss National Bank" markets price rate decision probability',
            'SNB traders price basis points next meeting'],
    "NZD": ['"Reserve Bank of New Zealand" markets price OCR probability',
            'RBNZ traders price basis points next meeting'],
    "AUD": ['"Reserve Bank of Australia" markets price cash rate probability'],
    "USD": ['"Federal Reserve" markets price rate decision probability'],
}


def _veiculo_vale(fonte):
    f = NOT.sem_acento(fonte or "").lower()
    return any(v in f for v in VEICULOS_MANCHETE)


def ancora_proxima_reuniao(texto, reuniao):
    """A regra mais dura daqui. Devolve (ok, motivo).

    Aceita so se o texto amarrar o numero a PROXIMA reuniao: o nome (ou abreviacao) do mes
    dela, ou uma expressao generica de proximidade. E REJEITA se aparecer qualquer outro
    nome de mes, ou qualquer termo de horizonte acumulado. Na duvida, descarta — um numero
    de fim de ano lido como probabilidade da proxima decisao inverte a leitura.
    """
    t = NOT.sem_acento(texto or "").lower()
    if RX_HORIZONTE.search(t):
        return False, "traz termo de horizonte acumulado (%s)" % RX_HORIZONTE.search(t).group(0)
    mes_ok = MES_NOME[reuniao.month]
    abrev_ok = MES_ABREV[reuniao.month]
    outros = []
    for k in range(1, 13):
        if k == reuniao.month:
            continue
        if re.search(r"\b%s\b" % MES_NOME[k], t) or re.search(r"\b%s\.?\b" % MES_ABREV[k], t):
            outros.append(MES_NOME[k])
    if outros:
        return False, "cita outro(s) mes(es) alem do da proxima reuniao: %s" % ", ".join(outros)
    tem_mes = bool(re.search(r"\b%s\b" % mes_ok, t) or re.search(r"\b%s\.?\b" % abrev_ok, t))
    tem_gen = bool(RX_PROXIMA_GENERICA.search(t))
    if not (tem_mes or tem_gen):
        return False, "nao amarra o numero a proxima reuniao (sem mes e sem 'next meeting')"
    return True, ("ancora: %s" % (mes_ok if tem_mes else RX_PROXIMA_GENERICA.search(t).group(0)))


def le_numero(texto):
    """Extrai (tipo, valor) do texto. tipo em {"pct", "bp"}; None se nao houver."""
    m = RX_PCT.search(texto) or RX_PCT2.search(texto)
    if m:
        v = float(m.group(1))
        if 0.0 <= v <= 100.0:
            return "pct", v, m.group(0)
    m = RX_BP.search(texto)
    if m:
        v = float(m.group(1))
        if 0.0 < v <= 200.0:
            return "bp", v, m.group(0)
    return None, None, None


def manchete(moeda, cad):
    """Camada C. Devolve (dado, motivo_de_nao_ter). Silencio nao e voto."""
    reuniao = cad["proxima"]
    if not reuniao:
        return None, "sem data de proxima reuniao no cadastro"
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=JANELA_MANCHETE_D)
    brutos, vistos = [], 0
    for q in CONSULTAS_PRECO.get(moeda, []):
        u = ("https://news.google.com/rss/search?q=%s&hl=en-US&gl=US&ceid=US:en"
             % urllib.parse.quote(q))
        try:
            itens = NOT.itens_rss(NOT.busca(u))
        except Exception:
            continue
        vistos += len(itens)
        for it in itens:
            d = NOT.data_de(it.get("publicado"))
            if not d or d < limite:
                continue                       # regua do dono: mais de 7 dias, descarta
            if not _veiculo_vale(it.get("fonte")):
                continue                       # so Reuters, Bloomberg, FT e WSJ
            brutos.append(dict(it, quando=d))
        time.sleep(PAUSA_S)

    if not brutos:
        return None, ("nenhum item de Reuters/Bloomberg/FT/WSJ com ate %d dias entre os %d "
                      "resultados lidos" % (JANELA_MANCHETE_D, vistos))

    # republicacao conta uma vez: mesma deduplicacao declarada em noticias.py
    grupos = []
    for it in sorted(brutos, key=lambda x: x["quando"], reverse=True):
        pal = set(NOT.palavras_de(it["titulo"], it.get("fonte")))
        for g in grupos:
            if NOT.jaccard(pal, g["palavras"]) >= JACCARD_DEDUP:
                g["copias"] += 1
                break
        else:
            grupos.append({"item": it, "palavras": pal, "copias": 1})

    recusados = []
    for g in grupos:
        it = g["item"]
        texto = "%s. %s" % (it["titulo"], it.get("resumo") or "")
        tipo, valor, trecho = le_numero(texto)
        if tipo is None:
            recusados.append({"titulo": it["titulo"][:120], "motivo": "sem numero"})
            continue
        alta = bool(RX_ALTA.search(texto))
        corte = bool(RX_CORTE.search(texto))
        if alta == corte:
            recusados.append({"titulo": it["titulo"][:120],
                              "motivo": "nao diz se e alta ou corte (ou diz os dois)"})
            continue
        ok, porque = ancora_proxima_reuniao(texto, reuniao)
        if not ok:
            recusados.append({"titulo": it["titulo"][:120], "motivo": porque})
            continue
        sinal = 1.0 if alta else -1.0
        nota = None
        if tipo == "pct":
            p = _limita01(valor / 100.0)
            imp = round(sinal * PASSO_BP * p, 2)
        else:
            imp = round(sinal * valor, 2)
            p = _limita01(valor / PASSO_BP)
            if valor > PASSO_BP:
                nota = ("o texto traz %d bp, mais que um passo de %d: a escada de um passo "
                        "so satura em 100%% e nao separa a chance de um movimento duplo."
                        % (valor, int(PASSO_BP)))
        p_alta = round(p if alta else 0.0, 4)
        p_corte = round(p if corte else 0.0, 4)
        return {"metodo": "manchete", "qualidade": "media",
                "fonte": "%s (manchete)" % (it.get("fonte") or "?"),
                "implicito_bp": imp, "p_alta": p_alta, "p_corte": p_corte,
                "p_manutencao": round(_limita01(1.0 - p_alta - p_corte), 4),
                "direcao_mercado": _direcao(imp),
                "texto": it["titulo"], "link": it.get("link"),
                "publicado": it["quando"].isoformat(),
                "veiculo": it.get("fonte"), "republicacoes": g["copias"] - 1,
                "trecho_lido": trecho, "ancora": porque, "nota": nota,
                "conta": ("%s: \"%s\" -> le-se %s = %s, movimento de %s, %s. "
                          "implicito = %+.2f bp; p_%s = %.4f, p_manutencao = %.4f."
                          % (it.get("fonte"), it["titulo"][:150],
                             "porcentagem" if tipo == "pct" else "pontos-base",
                             ("%.1f%%" % valor) if tipo == "pct" else ("%d bp" % valor),
                             "alta" if alta else "corte", porque, imp,
                             "alta" if alta else "corte", p, _limita01(1.0 - p_alta - p_corte))),
                "recusados": recusados[:6]}, None

    return None, ("%d manchete(s) de veiculo aceito na janela, nenhuma passou na regua da "
                  "proxima reuniao: %s" % (len(grupos),
                                           "; ".join("%s (%s)" % (r["titulo"][:60], r["motivo"])
                                                     for r in recusados[:4])))


# --------------------------------------------------------------- CAD: porta fechada, medida
def boc_tenta_futuro():
    """Tentativa real, para que o motivo do None seja MEDIDO e nao lembrado.

    COA (One-Month CORRA Futures) e o contrato certo — media do CORRA no mes civil, o ZQ
    canadense. A Bolsa de Montreal serve o preco por widget da QuoteMedia, que exige sessao
    presa ao dominio. Aqui a porta e batida uma vez por execucao e o codigo do erro entra no
    JSON.
    """
    W = "101020"   # webmasterId publicado no HTML de m-x.ca (data-qmod-wmid)
    tentativas = []
    for u in ["https://app.quotemedia.com/data/getFuturesChain.json?webmasterId=%s&symbol=COA" % W,
              "https://app.quotemedia.com/data/getEnhancedQuotes.json?webmasterId=%s&symbols=COA" % W]:
        j, erro = _get_json(u, headers=dict(UA, **{"Referer": "https://www.m-x.ca/"}))
        if j is not None:
            err = ((j.get("results") or {}).get("error") or {})
            if err:
                tentativas.append("%s -> %s" % (u.split("?")[0].rsplit("/", 1)[1],
                                                err.get("faultstring")))
                continue
            return j, None
        tentativas.append("%s -> %s" % (u.split("?")[0].rsplit("/", 1)[1], erro))
    return None, ("Bolsa de Montreal (COA, One-Month CORRA Futures) serve preco por widget "
                  "QuoteMedia com sessao presa ao dominio: " + "; ".join(tentativas))


# ----------------------------------------------------------------------------- montagem
def linha_vazia(moeda, cad, motivo):
    return {"moeda": moeda, "banco": cad.get("banco"), "sigla": cad.get("sigla"),
            "proxima": cad["proxima"].isoformat() if cad.get("proxima") else None,
            "taxa_atual": cad.get("taxa"), "nome_taxa": cad.get("nome_taxa"),
            "implicito_bp": None, "p_alta": None, "p_corte": None, "p_manutencao": None,
            "direcao_mercado": None, "fonte": None, "metodo": None, "qualidade": "sem fonte",
            "coletado_em": _agora(), "detalhe": {"motivo": motivo}}


def monta():
    cadastro = le_cadastro()
    saida = {"gerado_em": _agora(),
             "lei": ("A precificacao NUNCA entra no sentimento. E a coluna de comparacao "
                     "contra a leitura do HCI; a divergencia entre as duas e o produto."),
             "regua": {
                 "passo_bp": PASSO_BP,
                 "min_dias_depois": MIN_DIAS_DEPOIS,
                 "banda_morta_bp": BANDA_MORTA_BP,
                 "janela_manchete_dias": JANELA_MANCHETE_D,
                 "jaccard_dedup": JACCARD_DEDUP,
                 "veiculos_manchete": VEICULOS_MANCHETE,
                 "provisorio": ("min_dias_depois, banda_morta_bp e a escada de qualidade sao "
                                "PROVISORIOS — sem backtest que os calibre."),
                 "qualidade": {
                     "alta": "probabilidade tirada de futuro de taxa MEDIA MENSAL da propria "
                             "taxa de politica (ZQ, IB, COA)",
                     "media": "manchete de Reuters/Bloomberg/FT/WSJ com numero amarrado a "
                              "PROXIMA reuniao",
                     "baixa": "so direcao, de futuro de taxa a TERMO de 3 meses (BB)",
                     "sem fonte": "None com o motivo escrito"}},
             "moedas": {}}
    falhas_duras = 0

    for m in MOEDAS:
        cad = cadastro.get(m) or {}
        linha = linha_vazia(m, cad, "nao coletado")
        motivos = []

        dado, erro = (None, None)
        if m == "USD":
            dado, erro = fed(cad)
        elif m == "AUD":
            dado, erro = rba(cad)
        elif m == "NZD":
            dado, erro = rbnz(cad)
        elif m == "CAD":
            _, erro = boc_tenta_futuro()
        if erro:
            motivos.append("futuros: %s" % erro)

        if dado and dado.get("p_alta") is not None:
            linha.update({
                "implicito_bp": dado["implicito_bp"], "p_alta": dado["p_alta"],
                "p_corte": dado["p_corte"], "p_manutencao": dado["p_manutencao"],
                "direcao_mercado": _direcao(dado["implicito_bp"]),
                "fonte": dado["fonte"], "metodo": "futuros", "qualidade": "alta",
                "coletado_em": _agora(),
                "detalhe": {k: v for k, v in dado.items()
                            if k not in ("implicito_bp", "p_alta", "p_corte", "p_manutencao",
                                         "fonte")}})
            saida["moedas"][m] = linha
            continue

        if dado and dado.get("qualidade") == "baixa":
            # tem futuro, mas so direcao (NZD). Uma manchete boa e MELHOR: tenta subir.
            mh, erro_mh = manchete(m, cad)
            if mh:
                linha.update({
                    "implicito_bp": mh["implicito_bp"], "p_alta": mh["p_alta"],
                    "p_corte": mh["p_corte"], "p_manutencao": mh["p_manutencao"],
                    "direcao_mercado": mh["direcao_mercado"], "fonte": mh["fonte"],
                    "metodo": "manchete", "qualidade": "media", "coletado_em": _agora(),
                    "detalhe": {"manchete": mh, "futuro_so_direcao": dado}})
                saida["moedas"][m] = linha
                continue
            linha.update({
                "implicito_bp": None, "p_alta": None, "p_corte": None, "p_manutencao": None,
                "direcao_mercado": dado["direcao_mercado"], "fonte": dado["fonte"],
                "metodo": "futuros", "qualidade": "baixa", "coletado_em": _agora(),
                "detalhe": dict(dado, manchete_tentada=erro_mh)})
            saida["moedas"][m] = linha
            continue

        mh, erro_mh = manchete(m, cad)
        if mh:
            linha.update({
                "implicito_bp": mh["implicito_bp"], "p_alta": mh["p_alta"],
                "p_corte": mh["p_corte"], "p_manutencao": mh["p_manutencao"],
                "direcao_mercado": mh["direcao_mercado"], "fonte": mh["fonte"],
                "metodo": "manchete", "qualidade": "media", "coletado_em": _agora(),
                "detalhe": dict(mh, futuros=motivos or None)})
            saida["moedas"][m] = linha
            continue

        motivos.append("manchete: %s" % erro_mh)
        linha["detalhe"] = {"motivo": " | ".join(motivos)}
        saida["moedas"][m] = linha
        falhas_duras += 1

    return saida, falhas_duras


def grava_historico(saida):
    """Append-only: uma linha por execucao, com p_alta, p_corte e implicito_bp por moeda.

    E o que permite mostrar depois 'probabilidade antes e depois do dado'.
    """
    linha = {"em": saida["gerado_em"], "moedas": {}}
    for m, v in saida["moedas"].items():
        linha["moedas"][m] = {"p_alta": v["p_alta"], "p_corte": v["p_corte"],
                              "implicito_bp": v["implicito_bp"], "qualidade": v["qualidade"],
                              "proxima": v["proxima"]}
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def main():
    try:
        saida, falhas = monta()
    except Exception as e:                                     # coleta quebrada
        print("FALHOU sem gravar nada (o arquivo anterior fica intacto): %s: %s"
              % (type(e).__name__, e))
        return 1

    com_numero = [m for m, v in saida["moedas"].items() if v["p_alta"] is not None]
    if not com_numero:
        print("Nenhuma moeda com probabilidade. Preservo o arquivo anterior e saio com 1.")
        for m, v in saida["moedas"].items():
            print("  %s  %s" % (m, (v["detalhe"] or {}).get("motivo", "")[:150]))
        return 1

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    grava_historico(saida)

    print("PRECIFICACAO — o que o mercado cobra pela proxima decisao   (%s)"
          % saida["gerado_em"])
    print("A precificacao NAO entra no sentimento: e a coluna de comparacao.")
    print("-" * 100)
    print("%-5s %-7s %-11s %8s %8s %8s %8s  %-6s %-9s %s"
          % ("moeda", "banco", "proxima", "atual", "impl_bp", "p_alta", "p_corte",
             "metodo", "qualidade", "direcao"))
    for m in MOEDAS:
        v = saida["moedas"][m]
        f = lambda x, n=2: ("%.*f" % (n, x)) if isinstance(x, (int, float)) else "-"
        print("%-5s %-7s %-11s %8s %8s %8s %8s  %-6s %-9s %s"
              % (m, v["sigla"] or "-", v["proxima"] or "-", f(v["taxa_atual"], 3),
                 f(v["implicito_bp"]), f(v["p_alta"], 3), f(v["p_corte"], 3),
                 v["metodo"] or "-", v["qualidade"], v["direcao_mercado"] or "-"))
    print("-" * 100)
    for m in MOEDAS:
        v = saida["moedas"][m]
        d = v["detalhe"] or {}
        if d.get("conta"):
            print("\n[%s] %s" % (m, d["conta"]))
        elif d.get("motivo"):
            print("\n[%s] SEM FONTE: %s" % (m, d["motivo"]))
    print("\n  gravado: %s" % SAIDA)
    print("  historico (append): %s" % HIST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
