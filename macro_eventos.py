# -*- coding: utf-8 -*-
"""Gera data/macro_eventos.json — o calendario de noticias JA INTERPRETADO.

Cada evento sai com a leitura do que ele empurra na decisao do banco central, para que o site
mostre a interpretacao no clique, e nao so o numero.

NAO USA YIELD. So o que foi divulgado, contra o que se esperava.

TRES ESTADOS DE UM EVENTO
    AGENDADO   ainda nao saiu — mostra previsao, anterior e o que cada desfecho empurraria
    DIVULGADO  saiu — mostra o resultado, a classificacao e o empurrao medido
    SEM_BARRA  saiu mas nao havia previsao — nao da para classificar, e isso fica dito

A REGUA DA CLASSIFICACAO (decidida com o Eduardo em 01/set)
    Nao usamos surpresa padronizada, porque padronizar exige o desvio historico das surpresas
    por indicador — e isso depende de consenso point-in-time, que nao existe para tras
    (levantamento de 01/set: nenhum fornecedor comprovou entregar).
    Usamos classificacao GROSSA em tres faixas. Grosso e honesto quando nao da para calibrar;
    fino sem calibracao e falsa precisao.
    O corte sai de duas reguas que TEMOS:
      (a) a volatilidade do proprio indicador — quanto ele costuma andar de um mes para outro
      (b) o tamanho tipico da REVISAO daquele indicador (ALFRED / Philadelphia Fed)
          ⚠️ erro menor que a revisao tipica e RUIDO: o proprio instituto muda o numero mais
          que isso depois. Esta e a regua mais honesta e nao depende de consenso.
    Enquanto (b) nao esta ligado, vale o piso declarado em CORTE_PADRAO.
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
SAIDA = os.path.join(AQUI, "data", "macro_eventos.json")

# Piso enquanto a regua da revisao nao esta ligada. Fracao do |valor esperado|, com um minimo
# absoluto para nao explodir quando a previsao e perto de zero.
CORTE_PADRAO = {"fracao": 0.35, "minimo_abs": 0.1}


def familia_de(titulo: str):
    """Casa o titulo do evento com uma familia de indicador. Mais especifico primeiro."""
    t = (titulo or "").lower()
    # nucleo antes de cheia, senao "core cpi" cai em "cpi"
    # coletiva ANTES de decisao: "RBNZ Press Conference" tem que virar coletiva, nao decisao
    ordem = ["inflacao_nucleo", "expectativa_inflacao", "salarios", "desemprego",
             "auxilio_desemprego", "emprego_criacao", "inflacao_cheia", "coletiva", "decisao",
             "pmi", "pib", "varejo", "producao", "moradia", "confianca", "balanca"]
    for nome in ordem:
        for pad in FAMILIAS[nome]["padroes"]:
            if pad in t:
                return nome, FAMILIAS[nome]
    return None, None


def num(x):
    """Extrai numero de '3.5%', '-13.8%', '47K', '2.75%', '-106.8B'."""
    if x is None:
        return None
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


def classifica(actual, forecast):
    """Tres faixas: MUITO_ABAIXO / EM_LINHA / MUITO_ACIMA."""
    a, f = num(actual), num(forecast)
    if a is None or f is None:
        return None, None
    d = a - f
    corte = max(abs(f) * CORTE_PADRAO["fracao"], CORTE_PADRAO["minimo_abs"])
    if d > corte:
        return "MUITO_ACIMA", d
    if d < -corte:
        return "MUITO_ABAIXO", d
    return "EM_LINHA", d


def empurrao(classe, fam):
    """Para que lado a surpresa empurra a decisao do BC, e com que forca."""
    if classe is None or fam is None:
        return 0, "no bar to measure against"
    if classe == "EM_LINHA":
        return 0, "came in as expected — does not change what was already priced"
    lado = +1 if classe == "MUITO_ACIMA" else -1
    lado *= fam["sinal"]
    forca = fam["peso"] * lado
    texto = ("pushes toward TIGHTENING" if lado > 0 else "pushes toward EASING")
    return forca, texto


def cenarios(fam, forecast):
    """Para evento AGENDADO: o que cada desfecho empurraria. E o que o Eduardo quer ver ANTES."""
    if fam is None:
        return []
    s = fam["sinal"]
    acima = "TIGHTENING" if s > 0 else "EASING"
    abaixo = "EASING" if s > 0 else "TIGHTENING"
    return [
        {"caso": "above forecast", "empurra": acima, "peso": fam["peso"]},
        {"caso": "in line", "empurra": "nothing — already in the price", "peso": 0},
        {"caso": "below forecast", "empurra": abaixo, "peso": fam["peso"]},
    ]


def carrega_eventos():
    fn = os.path.join(RAW, "ff_calendar_thisweek.json")
    if not os.path.exists(fn):
        return []
    D = json.load(io.open(fn, encoding="utf-8"))
    return D if isinstance(D, list) else D.get("events", [])


def main():
    ev = carrega_eventos()
    agora = dt.datetime.now(dt.timezone.utc)
    saida = []

    for e in ev:
        titulo = e.get("title", "")
        nome_fam, fam = familia_de(titulo)
        try:
            t = dt.datetime.fromisoformat(e["date"])
        except Exception:
            continue

        imp = str(e.get("impact", "")).lower()
        mod = MODULADORES.get("impacto_" + {"high": "alto", "medium": "medio"}.get(imp, "baixo"), 0.2)

        actual = e.get("actual")
        classe, dif = classifica(actual, e.get("forecast"))
        forca, texto = empurrao(classe, fam)

        if actual in (None, ""):
            estado = "AGENDADO" if t > agora else "AGUARDANDO"
        elif classe is None:
            estado = "SEM_BARRA"
        else:
            estado = "DIVULGADO"

        saida.append({
            "titulo": titulo,
            "moeda": e.get("country"),
            "impacto": e.get("impact"),
            "quando_utc": t.astimezone(dt.timezone.utc).isoformat(),
            "estado": estado,
            "previsao": e.get("forecast") or None,
            "anterior": e.get("previous") or None,
            "resultado": actual or None,
            "familia": nome_fam,
            "familia_peso": fam["peso"] if fam else None,
            "familia_sinal": fam["sinal"] if fam else None,
            "porque": fam["porque"] if fam else
                      "indicador nao mapeado — nao entra na leitura, e isso fica declarado",
            "classe": classe,
            "diferenca": round(dif, 4) if dif is not None else None,
            "empurrao": round(forca * mod, 2),
            "empurrao_texto": texto,
            "cenarios": cenarios(fam, e.get("forecast")) if estado in ("AGENDADO", "AGUARDANDO") else [],
        })

    saida.sort(key=lambda x: x["quando_utc"])
    rel = {
        "gerado_em": agora.isoformat(),
        "fonte": "Forex Factory weekly feed",
        "aviso_fonte": "o feed semanal NAO traz o campo do resultado — eventos ja ocorridos "
                       "aparecem sem valor divulgado ate ligarmos a fonte ao vivo",
        "regua": {"tipo": "classificacao grossa em 3 faixas",
                  "corte": CORTE_PADRAO,
                  "nota": "corte por revisao tipica (ALFRED) ainda nao ligado"},
        "total": len(saida),
        "eventos": saida,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, allow_nan=False)

    print("=" * 78)
    print("MACRO EVENTOS — %d eventos" % len(saida))
    print("=" * 78)
    por_estado = {}
    for x in saida:
        por_estado[x["estado"]] = por_estado.get(x["estado"], 0) + 1
    for k, v in sorted(por_estado.items()):
        print("  %-12s %d" % (k, v))
    mapeados = sum(1 for x in saida if x["familia"])
    print("  mapeados numa familia: %d de %d" % (mapeados, len(saida)))
    print()
    print("  Proximos de alto impacto:")
    for x in saida:
        if str(x["impacto"]).lower() == "high":
            brt = dt.datetime.fromisoformat(x["quando_utc"]) - dt.timedelta(hours=3)
            print("    %s BRT  %-4s %-34s %-10s prev=%s"
                  % (brt.strftime("%d/%m %H:%M"), x["moeda"], x["titulo"][:34],
                     x["familia"] or "—", x["previsao"] or "—"))
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
