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

O QUE FALTAVA ERA A PONTE DO CONSENSO — E ELA ENTROU EM 05/set
    O BLS **nunca publica consenso**. Surpresa = divulgado - previsto, e o previsto so existe
    em calendario de vendor. A ponte agora e a FXStreet, que ja esta em casa:
    data/calendario_resultado.json (e o mesmo material ja interpretado em macro_eventos.json)
    trazem consenso, anterior e revisado por evento.

    O CASAMENTO e por FAMILIA + MES DE REFERENCIA, com tolerancias declaradas em TOLERANCIAS,
    e cada indicador grava `casado_com` (titulo e hora do evento usado) para a leitura ser
    auditavel. Quando nao ha consenso, grava `sem_consenso: true` e null nos campos —
    ⚠️ NUNCA se inventa previsao, e nunca se usa o "anterior" como se fosse consenso.

🔴 O NUMERO QUE VAI PARA A TELA NAO E SEMPRE O `valor` DO BLS
    O BLS devolve NIVEL de serie. Quem le painel quer a variacao:
      · payroll  -> o "atual" e a VARIACAO mensal (+162 mil vagas). O nivel 159.075 mil e
                    secundario e vai para `nivel`. Trocar os dois e o erro classico.
      · CPI      -> o destaque e a variacao ANUAL (3,54%). O indice 332,813 vai para `nivel`.
      · taxas    -> desemprego e participacao SAO niveis; ali o "atual" e o proprio nivel.
    O campo `destaque` de cada serie diz qual dos tres foi escolhido, e `destaque_texto`
    escreve isso em portugues.

A REGUA DA SURPRESA E A MESMA DO RESTO DA CASA — nao ha segunda regua
    `classifica()` e `FAMILIAS` sao importados de macro_eventos.py e leitor_regras.py.
    hawkish quando a surpresa empurra para juro mais alto (sinal +1 da familia com o dado
    acima do esperado; desemprego tem sinal -1, entao ABAIXO do esperado e que e hawkish),
    dovish no contrario, neutra dentro do corte PROVISORIO de CORTE_PADRAO.

O QUE ELE NAO FAZ
    Nao le o texto do comunicado — isso e a camada de interpretacao, que entra depois e nasce
    marcada como interpretacao. Aqui e so o mecanico: numero, variacao, surpresa e calendario.
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
sys.path.insert(0, AQUI)

# ⚠️ REGUA UNICA. `classifica` e `familia_de` vem de macro_eventos.py e `FAMILIAS` de
# leitor_regras.py de proposito: duas reguas divergentes para a mesma pergunta ("essa surpresa
# e hawkish?") e como ter dois relogios em casa — nunca se sabe qual esta certo.
from macro_eventos import CORTE_PADRAO, classifica, familia_de   # noqa: E402
from leitor_regras import FAMILIAS                                # noqa: E402

SAIDA = os.path.join(AQUI, "data", "eua_leitura.json")
CAL_FXS = os.path.join(AQUI, "data", "calendario_resultado.json")
CAL_MEV = os.path.join(AQUI, "data", "macro_eventos.json")
# Copia crua da ultima resposta do BLS. Existe para o enriquecimento (casamento, media de 3
# meses) poder rodar de novo SEM gastar cota quando o cache de 60 min ainda vale.
BRUTO = os.path.join(AQUI, "data", "raw", "bls_series.json")

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
# `familia`  liga cada uma a leitura de leitor_regras.py — peso e sinal vem de la, nao daqui.
# `destaque` diz QUAL numero e o "atual" que vai para a tela:
#     "mm"    variacao mensal   — payroll: +162 mil vagas, e nao o nivel de 159.075 mil
#     "aa"    variacao anual    — indice de preco e de salario se le em ritmo anual
#     "nivel" o proprio nivel   — taxa de desemprego e de participacao JA sao nivel
# `titulo_ancora` tem DOIS usos, e so o segundo mexe no casamento:
#     1. achar a PROXIMA divulgacao deste mesmo indicador. Aqui a familia e grossa demais:
#        CPI e PPI sao os dois `inflacao_cheia`, e "a proxima atualizacao do CPI e o PPI"
#        seria falso. A ancora e o titulo exato do evento na FXStreet.
#     2. so quando a serie NAO tem familia mapeada (participacao), a ancora substitui a
#        familia no casamento — e isso fica gravado em `casado_com.criterio`.
SERIES = {
    "CUSR0000SA0":    {"nome": "Inflação ao consumidor (CPI)", "sigla": "CPI",
                       "familia": "inflacao_cheia",  "tipo": "indice",    "destaque": "aa",
                       "titulo_ancora": r"^consumer price index \(yoy\)$"},
    "CUSR0000SA0L1E": {"nome": "Inflação núcleo (CPI núcleo)", "sigla": "CPI núcleo",
                       "familia": "inflacao_nucleo", "tipo": "indice",    "destaque": "aa",
                       "titulo_ancora": r"^consumer price index ex food & energy \(yoy\)$"},
    "CES0000000001":  {"nome": "Criação de vagas (NFP)",       "sigla": "NFP",
                       "familia": "emprego_criacao", "tipo": "nivel_mil", "destaque": "mm",
                       "titulo_ancora": r"^nonfarm payrolls$"},
    "LNS14000000":    {"nome": "Taxa de desemprego",           "sigla": "Desemprego",
                       "familia": "desemprego",      "tipo": "taxa",      "destaque": "nivel",
                       "titulo_ancora": r"^unemployment rate$"},
    "CES0500000003":  {"nome": "Salário médio por hora",       "sigla": "Salários",
                       "familia": "salarios",        "tipo": "indice",    "destaque": "aa",
                       "titulo_ancora": r"^average hourly earnings \(yoy\)$"},
    "LNS11300000":    {"nome": "Taxa de participação",         "sigla": "Participação",
                       "familia": None,              "tipo": "taxa",      "destaque": "nivel",
                       "titulo_ancora": r"participation rate"},
}

DESTAQUE_TEXTO = {"mm": "variação mensal", "aa": "variação anual", "nivel": "nível"}

# ---------------------------------------------------------------------------------------
# TOLERANCIAS DO CASAMENTO — todas PROVISORIAS e declaradas, nunca escondidas no meio do codigo.
#
# `dia_de_corte_do_mes` resolve o mes de referencia do evento a partir da hora do release:
# indicador mensal americano divulgado ate o dia 25 descreve o mes ANTERIOR (o payroll de
# agosto sai na 1a sexta de setembro; o CPI de agosto sai por volta do dia 11 de setembro).
#
# `conferencia_do_valor` e a trava contra casamento errado: se o numero da FXStreet nao bate
# com o do BLS dentro da folga de arredondamento, o casamento e RECUSADO. Sem essa trava o
# NFP (+162 mil) poderia casar com o ADP (+38 mil), que e da mesma familia e do mesmo mes.
# ---------------------------------------------------------------------------------------
TOLERANCIAS = {
    "meses_de_referencia": 0,
    "dia_de_corte_do_mes": 25,
    "conferencia_do_valor_fracao": 0.02,
    "conferencia_do_valor_minimo": 0.15,
    "nota": "PROVISORIAS. A folga do valor existe so por ARREDONDAMENTO (a FXStreet publica "
            "3,1% onde o BLS calcula 3,086%), nunca para forcar um casamento duvidoso.",
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
    cru = {s["seriesID"]: s.get("data", []) for s in d.get("Results", {}).get("series", [])}
    guarda_bruto(cru)
    return cru


def guarda_bruto(cru: dict) -> None:
    """Copia crua da serie, para o enriquecimento rodar de novo sem gastar cota.

    Sem isto, toda vez que o cache de 60 min valesse a media de 3 meses sairia vazia — e o
    painel mostraria um buraco por economia de cota, que e o pior dos dois mundos.
    """
    try:
        os.makedirs(os.path.dirname(BRUTO), exist_ok=True)
        json.dump({"gravado_em": dt.datetime.now(dt.timezone.utc).isoformat(), "series": cru},
                  io.open(BRUTO, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as e:
        print("  ! copia crua do BLS nao gravada (%s) — nao e fatal" % e)


def le_bruto() -> dict | None:
    """A copia crua da ultima resposta do BLS, quando existe."""
    if not os.path.exists(BRUTO):
        return None
    try:
        return json.load(io.open(BRUTO, encoding="utf-8")).get("series") or None
    except Exception:
        return None


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


def recua_meses(d, n: int):
    """A data do mes de referencia n meses ANTES de `d`, sempre no dia 1."""
    ano = d.year + (d.month - 1 - n) // 12
    mes = (d.month - 1 - n) % 12 + 1
    return dt.date(ano, mes, 1)


def valor_no_mes(pontos: list, alvo) -> float | None:
    """O valor da observacao cujo mes de referencia e EXATAMENTE `alvo`. None se nao houver.

    Existe porque a serie do BLS TEM BURACO: quando um mes vem como "-" (2025-10 no CPI, no
    desemprego e na participacao, hoje), `serie_ordenada` descarta a linha e a lista encolhe.
    Contar POSICAO na lista encolhida — pontos[-13] para o ano, pontos[-2] para o mes —
    compara com o mes ERRADO: o CPI de 2026-07 saia comparado com 2025-06 (13 meses) e a
    variacao anual do painel dava +3,54% quando a verdadeira era +3,30%. Aqui a busca e por
    DATA, e mes que falta vira None em vez de virar o mes vizinho.
    """
    for d, v, _ in reversed(pontos):
        if d == alvo:
            return v
    return None


def variacoes(pontos: list, tipo: str) -> dict:
    """m/m e a/a. Indice vira percentual; taxa e nivel ficam em diferenca absoluta.

    A base de comparacao e casada por DATA (mes anterior e mesmo mes do ano anterior), nunca
    por posicao na lista — ver `valor_no_mes`.
    """
    if len(pontos) < 2:
        return {}
    data_atual = pontos[-1][0]
    atual = pontos[-1][1]
    ant = valor_no_mes(pontos, recua_meses(data_atual, 1))
    doze = valor_no_mes(pontos, recua_meses(data_atual, 12))

    if tipo == "indice":
        mm = 100 * (atual / ant - 1) if ant else None
        aa = 100 * (atual / doze - 1) if doze else None
        un = "%"
    elif tipo == "nivel_mil":
        mm = atual - ant if ant is not None else None   # variacao em MILHARES de vagas
        aa = atual - doze if doze is not None else None
        un = "mil"
    else:                                     # taxa
        mm = atual - ant if ant is not None else None
        aa = atual - doze if doze is not None else None
        un = "pp"
    return {"mm": round(mm, 3) if mm is not None else None,
            "aa": round(aa, 3) if aa is not None else None, "unidade": un}


# =======================================================================================
# O "ATUAL" E A MEDIA DE 3 MESES — a serie convertida para a unidade que vai para a tela
# =======================================================================================

def serie_no_destaque(pontos: list, tipo: str, destaque: str) -> list:
    """Reescreve a serie inteira na MESMA unidade do "atual".

    E o que torna a media de 3 meses honesta: media de payroll tem que ser media de VARIACAO
    mensal (+64 mil vagas por mes), nunca media do nivel (159 milhoes de empregados), que nao
    quer dizer nada. Sai uma lista de (data, valor_no_destaque).
    """
    out = []
    for i, (data, v, _prelim) in enumerate(pontos):
        if destaque == "nivel":
            out.append((data, v))
            continue
        passo = 1 if destaque == "mm" else 12
        # base casada por DATA, nao por posicao: com um mes faltando na serie do BLS a
        # contagem por posicao compararia com o mes errado (ver `valor_no_mes`).
        base = valor_no_mes(pontos, recua_meses(data, passo))
        if base is None:
            continue
        if tipo == "indice":
            if not base:
                continue
            out.append((data, 100.0 * (v / base - 1.0)))
        else:
            out.append((data, v - base))
    return out


def media_de_3(serie: list):
    """Media das TRES ultimas observacoes da propria serie do BLS, ja na unidade do "atual"."""
    if len(serie) < 3:
        return None, 0
    ult = [x[1] for x in serie[-3:]]
    return sum(ult) / 3.0, 3


# =======================================================================================
# O CASAMENTO COM O CALENDARIO — de onde vem consenso, anterior e revisado
# =======================================================================================

def carrega_calendario() -> list:
    """Junta os eventos dos dois arquivos da FXStreet num formato unico.

    calendario_resultado.json e a fonte crua; macro_eventos.json e a MESMA fonte ja
    interpretada. Sao lidos os dois porque um pode estar mais novo que o outro — a chave e
    (titulo, hora) e vence quem tiver mais campo preenchido. Nada de misturar fontes
    diferentes: aqui as duas sao FXStreet.
    """
    juntos = {}

    def poe(titulo, quando, impacto, divulgado, consenso, anterior, revisado, moeda, arquivo):
        if not titulo or not quando or moeda != "USD":
            return
        chave = (titulo.strip().lower(), str(quando)[:16])
        cheio = sum(1 for x in (divulgado, consenso, anterior) if x is not None)
        velho = juntos.get(chave)
        if velho and velho["_cheio"] >= cheio:
            return
        juntos[chave] = {"titulo": titulo.strip(), "quando_utc": str(quando),
                         "impacto": str(impacto or "").upper(), "divulgado": divulgado,
                         "consenso": consenso, "anterior": anterior, "revisado": revisado,
                         "arquivo": arquivo, "_cheio": cheio}

    try:
        for e in json.load(io.open(CAL_FXS, encoding="utf-8")).get("eventos", []):
            poe(e.get("titulo"), e.get("quando_utc"), e.get("impacto"), e.get("divulgado"),
                e.get("consenso"), e.get("anterior"), e.get("revisado"), e.get("moeda"),
                "calendario_resultado.json")
    except Exception as erro:
        print("  ! calendario_resultado.json nao lido: %s" % erro)
    try:
        for e in json.load(io.open(CAL_MEV, encoding="utf-8")).get("eventos", []):
            poe(e.get("titulo"), e.get("quando_utc"), e.get("impacto"), e.get("resultado"),
                e.get("previsao"), e.get("anterior"), e.get("revisado"), e.get("moeda"),
                "macro_eventos.json")
    except Exception as erro:
        print("  ! macro_eventos.json nao lido: %s" % erro)

    return sorted(juntos.values(), key=lambda x: x["quando_utc"])


def referencia_do_evento(quando_utc: str):
    """De que MES o evento fala, a partir da hora do release. Devolve 'AAAA-MM' ou None.

    Regra provisoria, com o corte em TOLERANCIAS["dia_de_corte_do_mes"]: indicador mensal
    americano divulgado ate o dia 25 descreve o mes que acabou de terminar.
    """
    try:
        t = dt.datetime.fromisoformat(str(quando_utc).replace("Z", "+00:00"))
    except Exception:
        return None
    ano, mes = t.year, t.month
    if t.day <= TOLERANCIAS["dia_de_corte_do_mes"]:
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
    return "%04d-%02d" % (ano, mes)


# Desempate quando dois eventos da mesma familia batem igualmente bem: vence o de impacto
# mais alto, que e o que a fonte considera o numero de referencia daquela familia.
PESO_IMPACTO = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}


def casa_evento(meta: dict, atual, referencia: str, eventos: list):
    """Acha o evento do calendario que corresponde a esta serie do BLS.

    TRES filtros, nesta ordem, e todos declarados:
      1. FAMILIA        — o titulo do evento tem que cair na mesma familia da serie
                          (ou no `titulo_ancora`, quando a serie nao tem familia mapeada)
      2. REFERENCIA     — o mes que o evento descreve tem que ser o mes da serie
      3. VALOR          — o divulgado tem que bater com o "atual" do BLS dentro da folga de
                          arredondamento. E esta trava que impede o NFP de casar com o ADP.
    Devolve (evento, criterio) ou (None, motivo_da_recusa).
    """
    if atual is None:
        return None, "sem valor atual para conferir"
    fam = meta.get("familia")
    ancora = meta.get("titulo_ancora")
    criterio = "familia + referencia + conferencia do valor" if fam else \
               "titulo âncora + referência + conferência do valor"

    if not fam and not ancora:
        return None, "série sem família e sem título âncora — não há por onde casar"

    candidatos = []
    da_familia = []          # todos os da familia, divulgados ou nao — serve para o diagnostico
    for e in eventos:
        if fam:
            nome_fam, _ = familia_de(e["titulo"])
            if nome_fam != fam:
                continue
        elif not re.search(ancora, e["titulo"].lower()):
            continue
        da_familia.append(e)
        if e["divulgado"] is None:
            continue
        if referencia_do_evento(e["quando_utc"]) != referencia:
            continue
        folga = max(abs(e["divulgado"]) * TOLERANCIAS["conferencia_do_valor_fracao"],
                    TOLERANCIAS["conferencia_do_valor_minimo"])
        dist = abs(atual - e["divulgado"])
        if dist > folga:
            continue
        candidatos.append((dist, -PESO_IMPACTO.get(e["impacto"], 0), e))

    if candidatos:
        # Menor distancia primeiro; empate desempata pelo impacto mais alto. E isto que separa
        # o "Nonfarm Payrolls" (+162 mil) do "ADP Employment Change" (+38 mil), que sao a mesma
        # familia, o mesmo mes e sairiam os dois se so a familia mandasse.
        candidatos.sort(key=lambda x: (x[0], x[1]))
        return candidatos[0][2], criterio

    if not da_familia:
        return None, "a família não aparece no calendário carregado"
    janela = "%s a %s" % (min(e["quando_utc"][:10] for e in da_familia),
                          max(e["quando_utc"][:10] for e in da_familia))
    if not any(e["divulgado"] is not None for e in da_familia):
        return None, ("a família está no calendário (janela %s) mas nenhum evento dela já foi "
                      "divulgado — o release de %s está fora da janela carregada"
                      % (janela, referencia))
    return None, ("nenhum evento divulgado da mesma família descreve %s — a janela do "
                  "calendário carregado vai de %s" % (referencia, janela))


def proximo_do_indicador(meta: dict, eventos: list, agora):
    """A proxima divulgacao DESTE MESMO indicador — quando este numero vai ser atualizado.

    E o que responde "ate quando esta leitura vale": o CPI de julho so muda quando o CPI de
    agosto sair. Nao vota em nada, e so o relogio do indicador.

    ⚠️ Aqui manda a ANCORA, nao a familia. Pela familia, o proximo `inflacao_cheia` depois do
    CPI e o PPI — e escrever "a próxima atualização do CPI é o PPI" seria simplesmente falso.
    """
    ancora, fam = meta.get("titulo_ancora"), meta.get("familia")
    melhor = None
    for e in eventos:
        if e["divulgado"] is not None:
            continue
        if ancora:
            if not re.search(ancora, e["titulo"].lower()):
                continue
        elif fam:
            nome_fam, _ = familia_de(e["titulo"])
            if nome_fam != fam:
                continue
        else:
            continue
        try:
            t = dt.datetime.fromisoformat(e["quando_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        if t <= agora:
            continue
        if melhor is None or t < melhor[0]:
            melhor = (t, e)
    if not melhor:
        return None
    t, e = melhor
    brt = t - dt.timedelta(hours=3)
    falta = t - agora
    return {"titulo": e["titulo"], "quando_utc": t.isoformat(),
            "quando_brt": brt.strftime("%d/%m %H:%M"), "impacto": e["impacto"],
            "consenso": e["consenso"], "anterior": e["anterior"],
            "dias": falta.days, "horas": int(falta.total_seconds() // 3600)}


def rotulo_da_surpresa(atual, esperado, familia):
    """hawkish / dovish / neutra — pela MESMA regua de macro_eventos.py.

    hawkish = a surpresa empurra para juro mais alto. Emprego e inflacao acima do esperado
    sao hawkish (sinal +1 da familia); desemprego ABAIXO do esperado e que e hawkish, porque
    a familia `desemprego` tem sinal -1. Dentro do corte de CORTE_PADRAO o rotulo e "neutra":
    e um limiar PROVISORIO, o mesmo que classifica o calendario inteiro.
    """
    classe, dif = classifica(atual, esperado)
    if classe is None:
        return None, None, None
    corte = max(abs(esperado) * CORTE_PADRAO["fracao"], CORTE_PADRAO["minimo_abs"])
    if classe == "EM_LINHA":
        return "neutra", classe, round(corte, 4)
    if not familia or familia not in FAMILIAS:
        return None, classe, round(corte, 4)
    lado = (+1 if classe == "MUITO_ACIMA" else -1) * FAMILIAS[familia]["sinal"]
    return ("hawkish" if lado > 0 else "dovish"), classe, round(corte, 4)


# =======================================================================================
# FORMATACAO — numero em portugues, com virgula decimal, do jeito que vai para a tela
# =======================================================================================

def _pt(txt: str) -> str:
    """Ponto decimal vira virgula. Nada de '3.54%' num painel em portugues."""
    return txt.replace(".", ",")


def texto_do_numero(v, tipo: str, destaque: str, com_sinal: bool = None) -> str:
    """Escreve o numero na unidade do destaque: '+162k', '+3,54%', '4,1%', '+0,20 pp'.

    O sinal explicito so aparece em VARIACAO. Nivel nao leva sinal: '4,1%' de desemprego com
    um '+' na frente pareceria uma alta de 4,1 pontos.
    """
    if v is None:
        return "—"
    if com_sinal is None:
        com_sinal = destaque != "nivel"
    if destaque == "nivel":
        # ⚠️ NIVEL nao e variacao e cada tipo tem a sua cara:
        #   nivel_mil  159.075 mil empregados   (separador de milhar em ponto, como se le aqui)
        #   taxa       4,1%
        #   indice     332,813  — indice de preco NAO leva %; escrever "332,8%" seria absurdo
        if tipo == "nivel_mil":
            return "%s mil" % format(round(v), ",").replace(",", ".")
        if tipo == "taxa":
            return _pt("%.1f%%" % v)
        return _pt("%.3f" % v)
    if tipo == "nivel_mil":
        return _pt(("%+.0fk" if com_sinal else "%.0fk") % v)
    if tipo == "indice":
        return _pt(("%+.2f%%" if com_sinal else "%.2f%%") % v)
    return _pt(("%+.2f pp" if com_sinal else "%.2f pp") % v)


# =======================================================================================
# O MONTADOR — junta BLS + calendario num indicador so
# =======================================================================================

def monta_indicador(sid: str, meta: dict, base: dict, serie_destaque, eventos: list,
                    agora=None) -> dict:
    """Um indicador pronto para a tela: atual, esperado, anterior, surpresa e media de 3 meses.

    `base` traz o que veio do BLS (valor, mm, aa, referencia, unidade...). `serie_destaque` e a
    serie inteira ja convertida para a unidade do "atual" — e None quando so restou o cache
    resumido, e ai a media de 3 meses sai null COM MOTIVO, nunca inventada.
    """
    destaque = meta["destaque"]
    tipo = meta["tipo"]
    atual = base["valor"] if destaque == "nivel" else base.get(destaque)

    if serie_destaque is not None:
        media, n_media = media_de_3(serie_destaque)
        motivo_media = None if media is not None else \
            "a série do BLS tem menos de três observações nesta unidade"
    else:
        media, n_media = None, 0
        motivo_media = ("a cópia crua da série do BLS não estava em disco nesta rodada — "
                        "a média volta na próxima busca, sem gastar cota extra")

    evento, criterio = casa_evento(meta, atual, base["referencia"], eventos)
    esperado = anterior = surpresa = rotulo = None
    classe = corte = None
    surpresa_da_fonte = None
    casado = None
    motivo_sem_casamento = None

    anterior_publicado = None
    anterior_e_revisado = False
    if evento is not None:
        esperado = evento["consenso"]
        # O revisado MANDA no anterior: o proprio BLS ja reescreveu aquele mes, e comparar com
        # o numero velho e comparar com um dado que nao existe mais. O publicado original vai
        # junto em `anterior_publicado`, porque a revisao as vezes E a noticia (o payroll de
        # julho saiu -23 mil e foi reescrito para +21 mil).
        anterior_publicado = evento["anterior"]
        anterior_e_revisado = evento["revisado"] is not None
        anterior = evento["revisado"] if anterior_e_revisado else evento["anterior"]
        casado = {"titulo": evento["titulo"], "quando_utc": evento["quando_utc"],
                  "impacto": evento["impacto"], "arquivo": evento["arquivo"],
                  "divulgado_na_fonte": evento["divulgado"],
                  "anterior_publicado": evento["anterior"], "revisado": evento["revisado"],
                  "criterio": criterio}
        if esperado is not None:
            # A surpresa sai do numero CHEIO do BLS contra o consenso da FXStreet. A da fonte
            # vai junto para conferencia: as duas so diferem por arredondamento do vendor.
            surpresa = round(atual - esperado, 3)
            surpresa_da_fonte = round(evento["divulgado"] - esperado, 3)
            rotulo, classe, corte = rotulo_da_surpresa(atual, esperado, meta.get("familia"))
    else:
        motivo_sem_casamento = criterio

    r = dict(base)
    r.update({
        "nome": meta["nome"],
        "sigla": meta["sigla"],
        "familia": meta.get("familia"),
        "destaque": destaque,
        "destaque_texto": DESTAQUE_TEXTO[destaque],
        "atual": round(atual, 3) if atual is not None else None,
        "atual_texto": texto_do_numero(atual, tipo, destaque),
        "esperado": esperado,
        "esperado_texto": texto_do_numero(esperado, tipo, destaque),
        "anterior": anterior,
        "anterior_texto": texto_do_numero(anterior, tipo, destaque),
        "anterior_publicado": anterior_publicado,
        "anterior_e_revisado": anterior_e_revisado,
        "surpresa": surpresa,
        "surpresa_texto": texto_do_numero(surpresa, tipo, "variacao" if destaque == "nivel"
                                          else destaque, com_sinal=True),
        "surpresa_rotulo": rotulo,
        "surpresa_classe": classe,
        "surpresa_corte_provisorio": corte,
        "surpresa_da_fonte": surpresa_da_fonte,
        "media_3m": round(media, 3) if media is not None else None,
        "media_3m_texto": texto_do_numero(media, tipo, destaque),
        "media_3m_n": n_media,
        "media_3m_motivo": motivo_media,
        # O NIVEL e sempre secundario: 159.075 mil empregados, 332,813 de indice de preco.
        "nivel": base["valor"],
        "nivel_texto": texto_do_numero(base["valor"], tipo, "nivel"),
        "casado_com": casado,
        "proximo_evento_do_indicador": proximo_do_indicador(
            meta, eventos, agora or dt.datetime.now(dt.timezone.utc)),
        "sem_consenso": esperado is None,
        "sem_consenso_motivo": (None if esperado is not None else
                                (motivo_sem_casamento or
                                 "o evento casou, mas a FXStreet não publicou consenso para ele")),
    })
    # A frase pronta, na forma exata que o dono escreveu na revisao de 05/set. Existe para que
    # a tela nao precise remontar a leitura — e para que o que aparece no painel e o que sai no
    # terminal sejam a MESMA frase, nunca duas versoes que podem divergir.
    r["resumo_texto"] = (
        "%s — Atual %s · Esperado %s · Anterior %s · Surpresa: %s · Média de 3 meses: %s"
        % (meta["sigla"], r["atual_texto"],
           r["esperado_texto"] if not r["sem_consenso"] else "não publicado",
           r["anterior_texto"],
           r["surpresa_rotulo"] or "sem consenso para medir",
           r["media_3m_texto"]))
    return r


# =======================================================================================


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


def escreve(agora, guardado, atraso, leitura, fomc, fed, eventos):
    """Grava data/eua_leitura.json.

    🔴 DOIS CARIMBOS, de proposito. `gerado_em` continua sendo a hora em que o BLS foi lido —
    e NAO a hora desta rodada — senao a rodada que so refez o casamento reiniciaria o cache de
    60 min e o programa passaria a bater no BLS a cada 15 minutos de novo, estourando a cota.
    `recalculado_em` e a hora do relogio desta rodada. Dado velho com carimbo novo e
    exatamente a falha que a revisao de 03/set mandou nunca mais repetir.
    """
    rel = {
        "gerado_em": (guardado or {}).get("gerado_em") or agora.isoformat(),
        "recalculado_em": agora.isoformat(),
        "reaproveitado_do_cache": bool(guardado),
        "fonte_dado": "BLS public API v2 (sem chave; o SITE do BLS devolve 403, a API nao)",
        "fonte_consenso": "FXStreet, via data/calendario_resultado.json e data/macro_eventos.json",
        "fonte_comunicado": FED_RSS,
        "fonte_calendario": FED_CAL,
        "defasagem_referencia_meses": atraso,
        "defasagem_entrega_ms": None,
        "aviso_defasagem": "sao DUAS coisas distintas. referencia = o mes que o dado descreve, "
                           "universal e inevitavel. entrega = do release ate aqui: MEDIDA por "
                           "evento na fonte do calendario (FXStreet, campo atraso_s); NAO medida "
                           "para a API do BLS, que exige a chave registrada para ser cronometrada.",
        "aviso_consenso": "o BLS NUNCA publica previsao. o consenso e o anterior deste arquivo "
                          "vem do calendario da FXStreet, casados por familia e mes de "
                          "referencia. onde nao ha consenso publicado, o indicador sai com "
                          "sem_consenso=true e null nos campos — previsao nunca e inventada, e "
                          "o 'anterior' JAMAIS e usado no lugar do consenso.",
        "aviso_destaque": "o 'atual' nem sempre e o valor bruto do BLS: no payroll e a VARIACAO "
                          "mensal (+162 mil vagas) e nao o nivel (159.075 mil); no CPI e a "
                          "variacao ANUAL (3,54%) e nao o indice (332,813). o nivel fica em "
                          "'nivel', como numero secundario. veja o campo 'destaque'.",
        "aviso_media_3m": "media das TRES ultimas observacoes da propria serie do BLS, ja "
                          "convertida para a mesma unidade do 'atual'. media de payroll e media "
                          "de variacao mensal, nunca media de nivel.",
        "regua_da_surpresa": {
            "de_onde_vem": "macro_eventos.classifica + leitor_regras.FAMILIAS — a MESMA regua do "
                           "calendario. nao existe segunda regua nesta casa.",
            "corte_provisorio": dict(CORTE_PADRAO),
            "provisorio": True,
            "como_ler": "hawkish = a surpresa empurra para juro mais alto. emprego e inflacao "
                        "ACIMA do esperado sao hawkish (familia com sinal +1); desemprego "
                        "ABAIXO do esperado e que e hawkish (familia com sinal -1). dentro do "
                        "corte o rotulo e 'neutra'.",
            "limitacao_conhecida": "o corte de 35% do valor esperado e grosso demais para "
                                   "INDICADOR DE NIVEL: desemprego a 3,9% contra 4,1% esperados "
                                   "e uma surpresa de meio ponto de aperto, mas 0,2 < 0,35 x "
                                   "4,1 e sai 'neutra'. macro_eventos.py ja resolveu isso para a "
                                   "DECISAO de juro (CORTE_DECISAO_ABS = 0,10 pp) e deixou "
                                   "escrito que a mesma duvida vale para taxa de desemprego e "
                                   "nivel de PMI — decisao do Eduardo, ainda em aberto. Ate ela "
                                   "sair, este arquivo usa a regua IGUAL a do calendario de "
                                   "proposito: um mesmo dado nao pode sair 'em linha' numa tela "
                                   "e 'hawkish' na outra.",
        },
        "tolerancias_do_casamento": dict(TOLERANCIAS),
        "eventos_do_calendario_lidos": len(eventos),
        "aviso": "leitura MECANICA: numero, variacao e surpresa contra consenso publicado. O "
                 "texto do comunicado nao e interpretado aqui - essa camada entra depois e "
                 "nasce marcada como interpretacao.",
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


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    forcar = "--forcar" in sys.argv
    print("=" * 86)
    print("LEITOR DOS ESTADOS UNIDOS")
    print("=" * 86)
    print("  chave do BLS: %s" % ("registrada (500 chamadas/dia)" if CHAVE else
                                  "AUSENTE — 25 chamadas/dia. Registre em "
                                  "data.bls.gov/registrationEngine/"))

    # ------------------------------------------------------------------------------------
    # DE ONDE VEM A SERIE NESTA RODADA
    # O casamento com o calendario e a media de 3 meses NAO custam cota — sao aritmetica em
    # cima de arquivo local. Por isso o enriquecimento roda SEMPRE, inclusive quando o cache
    # de 60 min poupa a chamada ao BLS: o que o cache dispensa e a viagem ate a API, nao a
    # leitura. Antes desta revisao o programa simplesmente devolvia e nao reescrevia nada.
    # ------------------------------------------------------------------------------------
    guardado = cache_ainda_serve(forcar)
    cru = None
    if guardado:
        cru = le_bruto()
        print("  leitura de %.0f min atras ainda vale (dado do BLS e MENSAL) — cota poupada."
              % guardado["idade_min"])
        print("  a cópia crua da série %s — o casamento com o calendário roda de novo de graça."
              % ("está em disco" if cru else "NAO está em disco: média de 3 meses fica null"))
        print("  Use --forcar para buscar no BLS mesmo assim.")
    else:
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

    eventos = carrega_calendario()
    print("  calendário da FXStreet: %d eventos dos EUA carregados (consenso, anterior, "
          "revisado)." % len(eventos))

    # ------------------------------------------------------------------------------------
    # MONTAGEM
    # ------------------------------------------------------------------------------------
    leitura = {}
    anteriores = (guardado or {}).get("indicadores", {}) if guardado else {}
    for sid, meta in SERIES.items():
        pontos = serie_ordenada(cru.get(sid, [])) if cru else []
        if pontos:
            v = variacoes(pontos, meta["tipo"])
            d, val, prelim = pontos[-1]
            base = {"referencia": d.isoformat()[:7], "valor": val,
                    "preliminar": prelim, "n_obs": len(pontos), **v}
            serie_destaque = serie_no_destaque(pontos, meta["tipo"], meta["destaque"])
        elif anteriores.get(sid):
            # Cache resumido sem copia crua: da para refazer o casamento (o "atual" ja esta
            # gravado), mas NAO da para refazer a media de 3 meses. Ela sai null com motivo.
            velho = anteriores[sid]
            base = {k: velho.get(k) for k in
                    ("referencia", "valor", "preliminar", "n_obs", "mm", "aa", "unidade")}
            serie_destaque = None
        else:
            print("  %-28s  sem dado" % meta["nome"])
            continue
        leitura[sid] = monta_indicador(sid, meta, base, serie_destaque, eventos, agora)

    # ------------------------------------------------------------------------------------
    # A TABELA QUE O DONO PEDIU: atual, esperado, anterior, surpresa e media de 3 meses
    # ------------------------------------------------------------------------------------
    print()
    print("  %-14s %-12s %-12s %-12s %-11s %-9s %-11s %s"
          % ("indicador", "atual", "esperado", "anterior", "surpresa", "rótulo",
             "média 3m", "ref"))
    print("  " + "-" * 100)
    for sid, r in leitura.items():
        print("  %-14s %-12s %-12s %-12s %-11s %-9s %-11s %s%s"
              % (r["sigla"], r["atual_texto"], r["esperado_texto"], r["anterior_texto"],
                 r["surpresa_texto"], r["surpresa_rotulo"] or "—", r["media_3m_texto"],
                 r["referencia"], "  prelim" if r.get("preliminar") else ""))
    print()
    for sid, r in leitura.items():
        if r["casado_com"]:
            c = r["casado_com"]
            brt = ""
            try:
                brt = (dt.datetime.fromisoformat(c["quando_utc"]) - dt.timedelta(hours=3)
                       ).strftime(" (%d/%m %H:%M BRT)")
            except Exception:
                pass
            print("  %-14s casado com \"%s\" %s%s  [%s]"
                  % (r["sigla"], c["titulo"], c["quando_utc"][:16], brt, c["criterio"]))
        else:
            print("  %-14s SEM CONSENSO — %s" % (r["sigla"], r["sem_consenso_motivo"]))
    print()
    print("  nível (secundário, não é o destaque): " + " · ".join(
        "%s %s" % (r["sigla"], r["nivel_texto"]) for r in leitura.values()))
    print()
    print("  A FRASE QUE VAI PARA O PAINEL (campo resumo_texto)")
    for sid, r in leitura.items():
        print("    " + r["resumo_texto"])
    print()
    print("  PRÓXIMA ATUALIZAÇÃO DE CADA UM (é até quando esta leitura vale)")
    for sid, r in leitura.items():
        p = r["proximo_evento_do_indicador"]
        print("    %-14s %s" % (r["sigla"], "—  nada agendado no calendário carregado" if not p
              else "%s · %s BRT · impacto %s · em %d dia(s) · consenso %s"
                   % (p["titulo"], p["quando_brt"], p["impacto"], p["dias"],
                      p["consenso"] if p["consenso"] is not None else "ainda não publicado")))

    # DEFASAGEM (1): de REFERENCIA. O dado descreve um mes que ja acabou. Universal.
    refs = {x["referencia"] for x in leitura.values() if x.get("referencia")}
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
    # Na rodada de cache o Fed nao e consultado de novo: o calendario do FOMC e o feed de
    # comunicados sao os mesmos que ja estao em disco, e bater no site do Fed a cada 15 minutos
    # para reler as mesmas 55 reunioes nao acrescenta nada.
    if guardado and (guardado.get("fomc") or {}).get("proximas"):
        fomc = dict(guardado["fomc"], reaproveitado=True)
        fed = dict(guardado.get("fed") or {}, reaproveitado=True)
        print()
        print("  CALENDARIO DO FOMC e COMUNICADOS DO FED: reaproveitados da leitura em cache.")
        f = fomc.get("proxima")
        if f:
            faltam = (dt.date.fromisoformat(f["data"]) - dt.date.today()).days
            print("    proxima reuniao %s em %d dias   %s%s"
                  % (f["data"], faltam, f["rotulo"],
                     "  COM projecoes (dot plot)" if f.get("com_projecoes") else ""))
        escreve(agora, guardado, atraso, leitura, fomc, fed, eventos)
        return

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

    escreve(agora, guardado, atraso, leitura, fomc, fed, eventos)


if __name__ == "__main__":
    main()
