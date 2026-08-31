# -*- coding: utf-8 -*-
"""FICHA DO PAR — o upgrade do FUND, conforme o Volume I do AEGH.

POR QUE ESTE ARQUIVO EXISTE
O FUND V0.1 foi congelado em 31/ago como versao experimental reprovada: 15 pre-registros
como preditor direcional, e o Teste 1 como filtro de entrada (0 de 9 celulas acima do
controle aleatorio pareado). O que morreu foi o Score como DECISAO.

O Volume I nunca pediu decisao. Ele pede, por candidato:
  "causa dominante, score por moeda, diferencial estrutural e momento"
  "por que entrou, por que saiu e qual condicao falta"
  "cada mudanca material deve apontar evento, surpresa, mecanismo, horizonte,
   evidencias contrarias e alternativas plausiveis"
  e PROIBE "indicacao automatica de entrada".

E a secao 05 separa QUATRO saidas que o painel hoje colapsa num numero so:
  1. Conviccao fundamental   coerencia da tese com seus fundamentos — NAO e probabilidade de lucro
  2. Saude da tese           fortalecendo / estavel / enfraquecendo
  3. Confirmacao de mercado  confirmada / parcial / divergente / sem dados
  4. Confianca analitica     qualidade, cobertura, atualidade e concordancia da evidencia

Este modulo produz as quatro, separadas, com fonte e data — nunca um lado a operar.

⚠️ REGRAS QUE ESTE CODIGO NAO PODE VIOLAR
- Nao emite direcao, ordem, alvo nem "compre/venda".
- A saude da tese e medida no DIFERENCIAL CRU, nao no Score. O proprio Score seguir alto
  NAO e prova de persistencia (decisao do Eduardo, 31/ago).
- A confirmacao de mercado e CONTEMPORANEA, e e rotulada como tal. A transmissao
  juro->preco que medimos e +0,430 contemporanea e -0,046 preditiva: ela descreve o que
  ja aconteceu, nao antecipa.
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "data")
SAIDA = os.path.join(D, "fund_fichas.json")


def le(nome, padrao=None):
    p = os.path.join(D, nome)
    if not os.path.exists(p):
        return padrao
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return padrao


# ----------------------------------------------------------------- 1. causa dominante
def causa_dominante(base, quote, Y):
    """Qual perna moveu, quanto, e em quantos desvios. O 'por que' comeca aqui."""
    b, q = Y.get(base), Y.get(quote)
    if not b or not q:
        return None
    def mov(c, janela):
        v = c.get(janela)
        s = c.get("sigma_bp") or 0
        return {"bp": v, "sigmas": round(v / s, 1) if (v is not None and s) else None}
    mb, mq = mov(b, "d5"), mov(q, "d5")
    ab = abs(mb["bp"] or 0); aq = abs(mq["bp"] or 0)
    perna = base if ab >= aq else quote
    c = b if ab >= aq else q
    m = mb if ab >= aq else mq
    sentido = "rose" if (m["bp"] or 0) > 0 else "fell"
    return {
        "perna": perna, "sentido": sentido,
        "bp_5d": m["bp"], "sigmas_5d": m["sigmas"],
        "bp_1d": (b if perna == base else q).get("d1"),
        "bp_20d": (b if perna == base else q).get("d20"),
        "yield": c.get("yield"),
        "banco_central": c.get("central_bank"), "bc_url": c.get("central_bank_url"),
        "fonte": c.get("source"), "fonte_url": c.get("source_url"),
        "lido_em": c.get("as_of"),
        "frase": "The %s leg moved: %s 2y %s %s bp over 5 sessions (%s sigma)."
                 % (perna, perna, sentido, abs(m["bp"] or 0), m["sigmas"]),
    }


# ------------------------------------------------------- 2. conviccao fundamental
def conviccao(par, Y):
    """Coerencia da tese com seus fundamentos. NAO e probabilidade de lucro.

    Coerente quando NIVEL e MOMENTO apontam junto: o diferencial ja e favoravel a uma
    perna E vem se movendo na mesma direcao. Contraditoria quando divergem.
    """
    b, q = Y.get(par["base"]), Y.get(par["quote"])
    if not b or not q:
        return {"estado": "sem dados", "porque": "one leg missing."}
    nivel = (b.get("yield") or 0) - (q.get("yield") or 0)
    momento = (b.get("d20") or 0) - (q.get("d20") or 0)       # em bp
    if abs(nivel) < 0.15:
        return {"estado": "sem base", "nivel": round(nivel, 3), "momento_bp": round(momento, 1),
                "porque": "Rate differential is near zero (%.2f pp): there is no level for a "
                          "thesis to rest on." % nivel}
    if abs(momento) < 3:
        return {"estado": "parcial", "nivel": round(nivel, 3), "momento_bp": round(momento, 1),
                "porque": "Level favours %s (%.2f pp) but the differential is not moving "
                          "(%.1f bp in 20 sessions): a standing level, not a live revision."
                          % (par["base"] if nivel > 0 else par["quote"], nivel, momento)}
    junto = (nivel > 0) == (momento > 0)
    return {"estado": "coerente" if junto else "contraditoria",
            "nivel": round(nivel, 3), "momento_bp": round(momento, 1),
            "porque": ("Level and 20-session momentum point the same way: differential at %.2f pp, "
                       "moving %+.1f bp." % (nivel, momento)) if junto else
                      ("Level and 20-session momentum disagree: differential at %.2f pp but moving "
                       "%+.1f bp the other way — the standing level is being eroded."
                       % (nivel, momento))}


# ------------------------------------------------------------- 3. saude da tese
def saude(par, Y):
    """Fortalecendo / estavel / enfraquecendo — medida no DIFERENCIAL CRU.

    ⚠️ Nao usa o Score. O Score seguir alto nao e prova de persistencia.
    """
    b, q = Y.get(par["base"]), Y.get(par["quote"])
    if not b or not q:
        return {"estado": "sem dados"}
    nivel = (b.get("yield") or 0) - (q.get("yield") or 0)
    d5 = (b.get("d5") or 0) - (q.get("d5") or 0)
    if abs(d5) < 2:
        est, txt = "estavel", "Differential barely moved over 5 sessions (%+.1f bp)." % d5
    elif (nivel > 0) == (d5 > 0):
        est, txt = "fortalecendo", "Differential widened %+.1f bp in 5 sessions, in the same " \
                                   "direction as the level." % d5
    else:
        est, txt = "enfraquecendo", "Differential moved %+.1f bp AGAINST the standing level in " \
                                    "5 sessions." % d5
    return {"estado": est, "delta_5d_bp": round(d5, 1), "porque": txt,
            "invalidaria": "The differential crossing zero, or giving back 50%% of the move that "
                           "created the thesis. Today it sits at %.2f pp." % nivel}


# --------------------------------------------------- 4. confirmacao de mercado
def confirmacao(par):
    """O preco acompanhou? ⚠️ CONTEMPORANEO, nao preditivo — e rotulado assim."""
    h = par.get("history") or []
    if len(h) < 6:
        return {"estado": "sem dados", "porque": "not enough history."}
    return {"estado": "nao avaliada",
            "porque": "Price confirmation is measured contemporaneously, never as anticipation. "
                      "The transmission we measured is +0.430 contemporaneous and -0.046 "
                      "predictive at 120 sessions: rates MOVE the price, they do not LEAD it. "
                      "This box stays empty until a confirmation layer is tested on its own."}


# ------------------------------------------------------- 5. confianca analitica
def confianca(par, Y):
    """Qualidade, cobertura, atualidade e concordancia da evidencia."""
    b, q = Y.get(par["base"]), Y.get(par["quote"])
    if not b or not q:
        return {"estado": "insuficiente", "porque": "one leg missing."}
    sb, sq = b.get("stale_days") or 0, q.get("stale_days") or 0
    pior = max(sb, sq)
    semanal = [c for c in (par["base"], par["quote"])
               if (Y.get(c) or {}).get("cadence", "").startswith("weekly")]
    notas = []
    if pior > 0:
        notas.append("worst leg is %d day(s) stale" % pior)
    if semanal:
        notas.append("%s publishes weekly — the reading can be up to 7 days old" % ", ".join(semanal))
    est = "alta" if (pior == 0 and not semanal) else ("media" if pior <= 2 else "baixa")
    return {"estado": est, "stale_base": sb, "stale_quote": sq,
            "cadencia_base": b.get("cadence"), "cadencia_quote": q.get("cadence"),
            "porque": "; ".join(notas) if notas else "both legs current, daily cadence."}


# ------------------------------------------------------------------ 6. evidencia
def eventos_do_par(par, EV, limite=4):
    """Eventos agendados que podem reprecificar a trajetoria de juro de cada perna."""
    if not EV:
        return []
    agora = datetime.now(timezone.utc)
    moedas = {par["base"], par["quote"]}
    out = []
    for e in EV.get("events", []):
        if e.get("country") not in moedas:
            continue
        try:
            ts = datetime.fromisoformat(e["ts_utc"])
        except Exception:
            continue
        if ts < agora:
            continue
        out.append({"quando": e["ts_utc"][:16].replace("T", " "), "moeda": e["country"],
                    "titulo": e.get("title"), "impacto": e.get("impact"),
                    "fonte": e.get("source"), "url": e.get("url")})
    return sorted(out, key=lambda x: x["quando"])[:limite]


if __name__ == "__main__":
    S = le("fund_snapshot.json"); Yj = le("yields.json"); EV = le("calendar_events.json")
    if not S:
        print("fund_snapshot.json ausente"); sys.exit(1)
    Y = {c["currency"]: c for c in (Yj or {}).get("currencies", [])}

    fichas = {}
    for par in S.get("pairs", []):
        p = par["pair"]
        fichas[p] = {
            "par": p, "base": par["base"], "quote": par["quote"], "as_of": par.get("as_of"),
            "fund": par.get("fund"), "banda": par.get("strength"),
            "dias_na_banda": par.get("days_in_band"),
            "causa_dominante": causa_dominante(par["base"], par["quote"], Y),
            "conviccao_fundamental": conviccao(par, Y),
            "saude_da_tese": saude(par, Y),
            "confirmacao_de_mercado": confirmacao(par),
            "confianca_analitica": confianca(par, Y),
            "evidencia": eventos_do_par(par, EV),
            "contradiz": None,
        }
        c = fichas[p]["conviccao_fundamental"]
        s = fichas[p]["saude_da_tese"]
        contra = []
        if c.get("estado") == "contraditoria":
            contra.append(c["porque"])
        if s.get("estado") == "enfraquecendo":
            contra.append(s["porque"])
        if fichas[p]["confianca_analitica"].get("estado") == "baixa":
            contra.append("Evidence quality is low: " + fichas[p]["confianca_analitica"]["porque"])
        fichas[p]["contradiz"] = contra or None

    doc = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "o_que_e": "Pair file: the four outputs Volume I keeps separate — fundamental conviction, "
                   "thesis health, market confirmation and analytical confidence — each with its "
                   "source and date.",
        "o_que_nao_e": "Not a direction, not an order, not a target. FUND V0.1 is frozen as an "
                       "experimental version that failed the directional tests (15 pre-registrations "
                       "as a predictor; 0 of 9 cells as an entry filter). What is shown here is "
                       "evidence for you to read, not an edge.",
        "regra_de_leitura": "Conviction is coherence with the fundamentals — it is NOT a probability "
                            "of profit. Thesis health is measured on the raw differential, never on "
                            "the Score: a Score staying high is not proof of persistence.",
        "fichas": fichas,
    }
    json.dump(doc, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=" * 96)
    print("FICHA DO PAR — as quatro saidas que o Volume I separa")
    print("=" * 96)
    from collections import Counter
    for campo in ("conviccao_fundamental", "saude_da_tese", "confianca_analitica"):
        c = Counter(f[campo].get("estado") for f in fichas.values())
        print("  %-24s %s" % (campo, " · ".join("%s %d" % (k, v) for k, v in c.most_common())))
    comev = sum(1 for f in fichas.values() if f["evidencia"])
    comcontra = sum(1 for f in fichas.values() if f["contradiz"])
    print("  %-24s %d pares com evento agendado | %d com contradicao registrada"
          % ("evidencia", comev, comcontra))
    print()
    print("  gravado: data/fund_fichas.json  (%d pares)" % len(fichas))
