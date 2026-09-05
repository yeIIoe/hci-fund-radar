# -*- coding: utf-8 -*-
"""Gera data/macro_eventos.json — o calendario de noticias JA INTERPRETADO.

Cada evento sai com a leitura do que ele empurra na decisao do banco central, para que o site
mostre a interpretacao no clique, e nao so o numero.

NAO USA YIELD. So o que foi divulgado, contra o que se esperava.

DUAS FONTES, UMA PRIMARIA
    FXStreet   data/calendario_resultado.json — divulgado + consenso + anterior + revisado,
               8 moedas, com o atraso de entrega MEDIDO por evento. E a primaria desde 02/set:
               foi a unica fonte, entre 40 varridas, com latencia medida (HIGH: mediana 44 s).
    ForexFactory data/raw/ff_calendar_thisweek.json — previsao e anterior, NUNCA o resultado
               (conferido quatro vezes). Fica como reserva: se o arquivo da FXStreet faltar ou
               vier vazio, o calendario continua existindo, so sem leitura do que saiu.
    ⚠️ As duas nunca sao misturadas. Titulos diferentes para o mesmo evento virariam
    duplicata, e duplicata em calendario e o tipo de erro que ninguem percebe.

TRES ESTADOS DE UM EVENTO
    AGENDADO   ainda nao saiu — mostra previsao, anterior e o que cada desfecho empurraria
    AGUARDANDO ja passou da hora e a fonte ainda nao trouxe o numero
    DIVULGADO  saiu — mostra o resultado, a classificacao e o empurrao medido
    SEM_BARRA  saiu mas nao havia previsao — nao da para classificar, e isso fica dito

A REGUA DA CLASSIFICACAO (decidida com o Eduardo em 01/set)
    Nao usamos surpresa padronizada, porque padronizar exige o desvio historico das surpresas
    por indicador — e isso depende de consenso point-in-time, que nao existe para tras.
    Usamos classificacao GROSSA em tres faixas. Grosso e honesto quando nao da para calibrar;
    fino sem calibracao e falsa precisao.
    A FXStreet manda a sua propria surpresa normalizada (`ratioDeviation`). Ela vai junto,
    rotulada como deles — nao substitui a regua, porque o criterio de normalizacao e da casa.
    Enquanto a regua da revisao (ALFRED) nao esta ligada, vale o piso declarado em CORTE_PADRAO.

🔴 ZERO NAO E AUSENCIA
    A versao anterior gravava `actual or None`. Com texto do Forex Factory isso passava; com
    numero da FXStreet um resultado legitimo de 0.0 viraria "nao saiu". O CPI mensal da Suica
    tem previsao de 0,0% nesta semana. Mesmo bug que ja foi consertado na ponte MQL5.
"""
from __future__ import annotations
import datetime as dt
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from leitor_regras import FAMILIAS, MODULADORES   # noqa: E402

RAW = os.path.join(AQUI, "data", "raw")
FXS = os.path.join(AQUI, "data", "calendario_resultado.json")
SAIDA = os.path.join(AQUI, "data", "macro_eventos.json")

# Piso enquanto a regua da revisao nao esta ligada. Fracao do |valor esperado|, com um minimo
# absoluto para nao explodir quando a previsao e perto de zero.
CORTE_PADRAO = {"fracao": 0.35, "minimo_abs": 0.1}

# Minimo de eventos para a FXStreet ser aceita como primaria. Abaixo disso o arquivo esta
# truncado ou a fonte bloqueou — e melhor cair na reserva do que publicar calendario capenga.
MINIMO_FXS = 20


def _casa(pad: str, t: str) -> bool:
    """Padrao curto (ate 4 letras) casa por PALAVRA, nao por substring.
    "ism" dentro de "Optimism" fazia o NFIB Business Optimism virar PMI (revisao de 03/set)."""
    if len(pad) <= 4:
        return re.search(r"\b" + re.escape(pad) + r"\b", t) is not None
    return pad in t


def familia_de(titulo: str):
    """Casa o titulo do evento com uma familia de indicador. Mais especifico primeiro."""
    t = (titulo or "").lower()
    # nucleo antes de cheia, senao "core cpi" cai em "cpi"
    # desemprego antes de emprego_criacao: "Unemployment Change" tem que ser desemprego
    # coletiva ANTES de decisao: "RBNZ Press Conference" tem que virar coletiva, nao decisao
    ordem = ["inflacao_nucleo", "expectativa_inflacao", "salarios", "desemprego",
             "auxilio_desemprego", "emprego_criacao", "inflacao_cheia", "coletiva", "decisao",
             "pmi", "pib", "varejo", "producao", "moradia", "confianca", "balanca"]
    for nome in ordem:
        for pad in FAMILIAS[nome]["padroes"]:
            if _casa(pad, t):
                return nome, FAMILIAS[nome]
    return None, None


def num(x):
    """Extrai numero de 3.5, '3.5%', '-13.8%', '47K', '2.75%', '-106.8B'. None continua None."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    t = str(x).strip().replace(",", "")
    if not t or t in ("-", "—"):
        return None
    m = re.search(r"-?\d+\.?\d*", t)
    if not m:
        return None
    v = float(m.group())
    if "K" in t.upper():
        v *= 1_000
    elif "B" in t.upper():
        v *= 1_000_000_000
    elif "M" in t.upper() and "%" not in t:
        v *= 1_000_000
    return v


# Para a DECISAO de juro a fracao de 35% nao serve: ECB 2,25 contra 2,50 esperado e uma
# surpresa de um quantum inteiro, mas 0,25 < 0,35 x 2,50 = 0,875 e sairia "em linha".
# Corte absoluto de 0,10 pp = menos de meio quantum de 25 bp. Achado da revisao de 03/set;
# a mesma duvida vale para taxa de desemprego e nivel de PMI — decisao do Eduardo, declarada.
CORTE_DECISAO_ABS = 0.10


def classifica(actual, forecast, corte_abs=None):
    """Tres faixas: MUITO_ABAIXO / EM_LINHA / MUITO_ACIMA."""
    a, f = num(actual), num(forecast)
    if a is None or f is None:
        return None, None
    d = a - f
    corte = corte_abs if corte_abs is not None else \
        max(abs(f) * CORTE_PADRAO["fracao"], CORTE_PADRAO["minimo_abs"])
    if d > corte:
        return "MUITO_ACIMA", d
    if d < -corte:
        return "MUITO_ABAIXO", d
    return "EM_LINHA", d


def empurrao(classe, fam):
    """Para que lado a surpresa empurra a decisao do BC, e com que forca."""
    if classe is None:
        return 0, "sem régua para medir — não há previsão publicada"
    if fam is None:
        # a barra existe (tem previsao e resultado); o que falta e a familia. Dizer "no bar"
        # aqui e mentira — e foi o que a tela mostrou para Nonfarm Productivity em 03/set.
        return 0, "fora da leitura — indicador sem família mapeada"
    if classe == "EM_LINHA":
        return 0, "veio como esperado — não muda o que já estava no preço"
    lado = +1 if classe == "MUITO_ACIMA" else -1
    lado *= fam["sinal"]
    forca = fam["peso"] * lado
    texto = ("empurra para APERTO" if lado > 0 else "empurra para ALÍVIO")
    return forca, texto


def cenarios(fam, forecast):
    """Para evento AGENDADO: o que cada desfecho empurraria. E o que o Eduardo quer ver ANTES.

    So para familia com peso: discurso, coletiva e a propria decisao tem peso 0 e nao tem
    "acima da previsao" — sao texto. Mostrar cenario numerico para um discurso e ruido.
    """
    if fam is None or not fam.get("peso"):
        return []
    s = fam["sinal"]
    acima = "APERTO" if s > 0 else "ALÍVIO"
    abaixo = "ALÍVIO" if s > 0 else "APERTO"
    return [
        {"caso": "acima da previsão", "empurra": acima, "peso": fam["peso"]},
        {"caso": "em linha", "empurra": "nada — já está no preço", "peso": 0},
        {"caso": "abaixo da previsão", "empurra": abaixo, "peso": fam["peso"]},
    ]


# ---------------------------------------------------------------------------------------
# FONTES — as duas saem no MESMO formato interno, para o laco de leitura nao saber de onde
# veio. So o campo `fonte` denuncia.
# ---------------------------------------------------------------------------------------

IMPACTO_FXS = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low", "NONE": "Low"}


def carrega_fxstreet():
    """Le o que fxstreet_calendario.py gravou. Devolve (eventos, latencia_medida, gerado_em)."""
    if not os.path.exists(FXS):
        return [], None, None
    try:
        D = json.load(io.open(FXS, encoding="utf-8"))
    except Exception as e:
        print("  ! calendario_resultado.json ilegivel: %s" % e)
        return [], None, None
    out = []
    for e in D.get("eventos", []):
        out.append({
            "title": e.get("titulo") or "",
            "country": e.get("moeda"),
            "impact": IMPACTO_FXS.get(str(e.get("impacto")).upper(), "Low"),
            "date": e.get("quando_utc"),
            "actual": e.get("divulgado"),
            "forecast": e.get("consenso"),
            "previous": e.get("anterior"),
            "revised": e.get("revisado"),
            "unit": e.get("unidade"),
            "atraso_s": e.get("atraso_s"),
            "surpresa_normalizada": e.get("surpresa_normalizada"),
            "melhor_que_esperado": e.get("melhor_que_esperado"),
            "discurso": bool(e.get("discurso")),
            "tentativa": bool(e.get("data_a_confirmar")),
            "preliminar": bool(e.get("preliminar")),
        })
    return out, D.get("latencia_medida"), D.get("gerado_em")


def carrega_ff():
    fn = os.path.join(RAW, "ff_calendar_thisweek.json")
    if not os.path.exists(fn):
        return []
    D = json.load(io.open(fn, encoding="utf-8"))
    bruto = D if isinstance(D, list) else D.get("events", [])
    out = []
    for e in bruto:
        out.append({
            "title": e.get("title", ""), "country": e.get("country"),
            "impact": e.get("impact"), "date": e.get("date"),
            "actual": e.get("actual") or None,       # FF manda texto; vazio e vazio mesmo
            "forecast": e.get("forecast") or None, "previous": e.get("previous") or None,
            "revised": None, "unit": None, "atraso_s": None, "surpresa_normalizada": None,
            "melhor_que_esperado": None, "discurso": False, "tentativa": False,
            "preliminar": False,
        })
    return out


def escolhe_fonte():
    fx, lat, fonte_em = carrega_fxstreet()
    if len(fx) >= MINIMO_FXS:
        return fx, lat, fonte_em, "fxstreet", (
            "FXStreet calendar backend: released value, consensus, previous and revision for "
            "the 8 majors, with the delivery delay measured per event. Widget backend, not a "
            "licensed product — no SLA. Fallback is the Forex Factory feed.")
    ff = carrega_ff()
    motivo = ("arquivo ausente" if not fx else "so %d eventos (minimo %d)" % (len(fx), MINIMO_FXS))
    print("  ! FXStreet indisponivel (%s) — usando a reserva do Forex Factory" % motivo)
    return ff, None, None, "forexfactory", (
        "Forex Factory weekly feed (FALLBACK): it never carries the released value, so events "
        "that already happened show no result. The FXStreet source was unavailable this run.")


def main():
    ev, latencia, fonte_em, fonte, aviso = escolhe_fonte()
    agora = dt.datetime.now(dt.timezone.utc)
    saida = []

    for e in ev:
        titulo = e["title"]
        nome_fam, fam = familia_de(titulo)
        try:
            t = dt.datetime.fromisoformat(str(e["date"]).replace("Z", "+00:00"))
        except Exception:
            continue
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)

        imp = str(e.get("impact", "")).lower()
        mod = MODULADORES.get("impacto_" + {"high": "alto", "medium": "medio"}.get(imp, "baixo"), 0.2)

        actual = e["actual"]
        classe, dif = classifica(actual, e["forecast"],
                                 CORTE_DECISAO_ABS if nome_fam == "decisao" else None)
        forca, texto = empurrao(classe, fam)

        # 🔴 `is None`, nunca `or`: 0.0 e um resultado, nao uma ausencia.
        if actual is None:
            estado = "AGENDADO" if t > agora else "AGUARDANDO"
        elif classe is None:
            estado = "SEM_BARRA"
        else:
            estado = "DIVULGADO"

        if e["discurso"]:
            texto = "é um discurso — não há número para medir; o texto é a divulgação"

        saida.append({
            "titulo": titulo,
            "moeda": e["country"],
            "impacto": e["impact"],
            "quando_utc": t.astimezone(dt.timezone.utc).isoformat(),
            "estado": estado,
            "previsao": e["forecast"],
            "anterior": e["previous"],
            "resultado": actual,
            "revisado": e["revised"],
            "unidade": e["unit"],
            "familia": nome_fam,
            "familia_peso": fam["peso"] if fam else None,
            "familia_sinal": fam["sinal"] if fam else None,
            "porque": fam["porque"] if fam else
                      "indicador sem família mapeada — não entra na leitura, e isso fica declarado",
            "classe": classe,
            "diferenca": round(dif, 4) if dif is not None else None,
            "surpresa_normalizada": e["surpresa_normalizada"],
            "melhor_que_esperado": e["melhor_que_esperado"],
            "empurrao": round(forca * mod, 2),
            "empurrao_texto": texto,
            "atraso_s": e["atraso_s"],
            "discurso": e["discurso"],
            "data_a_confirmar": e["tentativa"],
            "preliminar": e["preliminar"],
            "fonte": fonte,
            "cenarios": (cenarios(fam, e["forecast"])
                         if (estado in ("AGENDADO", "AGUARDANDO") and not e["discurso"]) else []),
        })

    saida.sort(key=lambda x: x["quando_utc"])
    # DOIS carimbos, de proposito: gerado_em e a hora do RELOGIO (esta rodada); fonte_gerado_em
    # e a hora do DADO (quando a FXStreet foi lida com sucesso). Se a fonte cair, a cadeia
    # continua rodando com o arquivo antigo — e o site tem que mostrar a idade do dado, nao a
    # do relogio. Achado da revisao de 03/set: "dado velho com carimbo novo".
    rel = {
        "gerado_em": agora.isoformat(),
        "fonte_gerado_em": fonte_em,
        "fonte": fonte,
        "aviso_fonte": aviso,
        "latencia_medida": latencia,
        "regua": {"tipo": "classificacao grossa em 3 faixas",
                  "corte": CORTE_PADRAO,
                  "nota": "corte por revisao tipica (ALFRED) ainda nao ligado; a surpresa "
                          "normalizada da FXStreet vai junto, rotulada como deles"},
        "total": len(saida),
        "eventos": saida,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, allow_nan=False)

    print("=" * 78)
    print("MACRO EVENTOS — %d eventos · fonte: %s" % (len(saida), fonte))
    print("=" * 78)
    por_estado = {}
    for x in saida:
        por_estado[x["estado"]] = por_estado.get(x["estado"], 0) + 1
    for k, v in sorted(por_estado.items()):
        print("  %-12s %d" % (k, v))
    mapeados = sum(1 for x in saida if x["familia"])
    altos = [x for x in saida if str(x["impacto"]).lower() == "high"]
    altos_map = sum(1 for x in altos if x["familia"])
    print("  mapeados numa familia: %d de %d  (HIGH: %d de %d)"
          % (mapeados, len(saida), altos_map, len(altos)))
    if latencia:
        print("  atraso de entrega medido: HIGH mediana %ss (n=%s) · p90 %ss"
              % (latencia.get("mediana_alta"), latencia.get("n_alta"), latencia.get("p90_alta")))
    print()
    print("  Ja divulgados com leitura:")
    for x in [y for y in saida if y["estado"] == "DIVULGADO"][-6:]:
        brt = dt.datetime.fromisoformat(x["quando_utc"]) - dt.timedelta(hours=3)
        print("    %s BRT  %-4s %-32s %-12s %s  (+%ss)"
              % (brt.strftime("%d/%m %H:%M"), x["moeda"], x["titulo"][:32], x["classe"],
                 x["empurrao_texto"][:34], x["atraso_s"] if x["atraso_s"] is not None else "?"))
    print()
    print("  Proximos de alto impacto:")
    for x in [y for y in altos if y["estado"] == "AGENDADO"][:8]:
        brt = dt.datetime.fromisoformat(x["quando_utc"]) - dt.timedelta(hours=3)
        print("    %s BRT  %-4s %-34s %-10s prev=%s"
              % (brt.strftime("%d/%m %H:%M"), x["moeda"], x["titulo"][:34],
                 x["familia"] or "—", x["previsao"] if x["previsao"] is not None else "—"))
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
