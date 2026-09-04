# -*- coding: utf-8 -*-
"""SENTIMENTO — a leitura PARA FRENTE, por moeda e por par.

A PERGUNTA QUE ISTO RESPONDE
    "O que este banco central vai fazer na PROXIMA reuniao?" — e, com as duas pernas lidas,
    "este par tem tese fundamental ou nao?". E leitor, nao estrategia: ele da o lado
    fundamental de cada perna; a entrada continua sendo do Eduardo.

QUATRO DIMENSOES, 25% CADA — a convencao do Eduardo
    dados    surpresas acumuladas desde a ultima decisao do banco (ou 42 dias), cada evento
             pesado pela familia (leitor_regras), pelo impacto e por uma meia-vida de 21 dias.
             Um empurrao de 30 dias atras vale ~37% de um de hoje.
    texto    o que os dirigentes DISSERAM — contagem de marcadores hawkish/dovish dos discursos
             e do comunicado. ⚠️ So o Fed esta ligado (fed_discursos.py). As outras sete moedas
             saem "not connected" — buraco declarado, nunca zero.
    ciclo    a direcao do ultimo movimento de juro. Movimento com mais de 180 dias le como
             MANUTENCAO: um banco parado ha meio ano esta em hold, nao em ciclo.
    mercado  a probabilidade implicita para a proxima reuniao. ⚠️ Nao conectada — nao ha
             fonte gratuita de OIS/futuros, e yield nao entra por decisao de projeto.

    Direcao da moeda = a mais votada entre as dimensoes DISPONIVEIS; empate = MANTEM.
    Conviccao = 25% por dimensao disponivel que concorda. Com duas dimensoes ligadas o teto e
    50%, e isso aparece na tela: "50% — 2 of 4 dimensions connected". Buraco nao vira zero.

A REGRA DO PAR (leitor_regras.veredito_do_par / leitor_pares.le_par)
    os dois na mesma posicao -> NAO NEGOCIA. Um sobe e o outro mantem -> negocia, lado de quem
    sobe. Sobe x corta -> divergencia de 2 graus. A intensidade vem da conviccao.

A LEI DAS DUAS PERNAS
    Par nao e ativo, sao duas moedas. Cada par sai com "a razao esta na perna X", e a lista de
    pares que compartilham essa perna — dois deles nao diversificam, dobram.

REGUAS DECLARADAS (grossas de proposito — fino sem calibracao e falsa precisao)
    LIMIAR_DADOS = 5.0 na soma decaida: abaixo disso o fluxo de dados le MANTEM.
    Uma DECISAO dentro da janela zera o acumulado: so contam eventos depois dela.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from leitor_regras import MODULADORES                                    # noqa: E402
from macro_eventos import familia_de, classifica, empurrao, IMPACTO_FXS  # noqa: E402
from fxstreet_calendario import buscar, normaliza                        # noqa: E402
from leitor_pares import PARES, MOEDAS, Leitura, le_par                   # noqa: E402

SAIDA = os.path.join(AQUI, "data", "sentimento.json")
BANCOS = os.path.join(AQUI, "data", "bancos_centrais.json")
DISCURSOS = os.path.join(AQUI, "data", "bc_discursos.json")      # todas as moedas conectadas
DISCURSOS_FED = os.path.join(AQUI, "data", "fed_discursos.json")  # reserva, so o Fed
CAL_LOCAL = os.path.join(AQUI, "data", "calendario_resultado.json")

JANELA_DIAS = 42
MEIA_VIDA = float(MODULADORES.get("meia_vida_dias", 21))
LIMIAR_DADOS = 5.0
CICLO_VALIDADE_DIAS = 180
PESO_DIM = 25


def carrega_json(fn):
    try:
        return json.load(io.open(fn, encoding="utf-8"))
    except Exception:
        return None


def eventos_janela(agora):
    """Busca 42 dias da FXStreet direto (o calendario do site so guarda ±8 dias). Se a fonte
    falhar, usa o arquivo local — janela curta, mas declarada na saida."""
    try:
        cru = buscar(dias_atras=JANELA_DIAS, dias_frente=1)
        ev = [x for x in (normaliza(e) for e in cru) if x]
        return ev, "fxstreet %d dias" % JANELA_DIAS
    except Exception as e:
        print("  ! FXStreet indisponivel para a janela longa (%s) — usando o arquivo local" % e)
        loc = carrega_json(CAL_LOCAL) or {}
        return loc.get("eventos", []), "arquivo local (janela curta)"


def dimensao_dados(ev, moeda, agora):
    meus = [e for e in ev if e.get("moeda") == moeda and e.get("divulgado") is not None
            and e.get("quando_utc")]
    inicio = (agora - dt.timedelta(days=JANELA_DIAS)).isoformat()
    meus = [e for e in meus if e["quando_utc"] >= inicio and e["quando_utc"] <= agora.isoformat()]

    # a DECISAO zera o ciclo: so conta o que saiu depois da ultima
    decisoes = [e["quando_utc"] for e in meus if familia_de(e.get("titulo"))[0] == "decisao"]
    corte = max(decisoes) if decisoes else None

    soma, n, n_alto, itens = 0.0, 0, 0, []
    for e in meus:
        if corte and e["quando_utc"] <= corte:
            continue
        nome, fam = familia_de(e.get("titulo"))
        if not fam or not fam.get("peso"):
            continue
        classe, dif = classifica(e.get("divulgado"), e.get("consenso"))
        if classe is None:
            continue
        forca, texto = empurrao(classe, fam)
        imp = IMPACTO_FXS.get(str(e.get("impacto")).upper(), "Low").lower()
        mod = MODULADORES.get("impacto_" + {"high": "alto", "medium": "medio"}.get(imp, "baixo"), 0.2)
        try:
            quando = dt.datetime.fromisoformat(e["quando_utc"])
        except ValueError:
            continue
        idade = max(0.0, (agora - quando).total_seconds() / 86400.0)
        decai = 0.5 ** (idade / MEIA_VIDA)
        contrib = forca * mod * decai
        n += 1
        n_alto += (imp == "high")
        soma += contrib
        if contrib:
            itens.append({"quando_utc": e["quando_utc"], "titulo": e.get("titulo"),
                          "familia": nome, "classe": classe, "impacto": e.get("impacto"),
                          "divulgado": e.get("divulgado"), "consenso": e.get("consenso"),
                          "contribuicao": round(contrib, 2), "idade_dias": round(idade, 1)})
    itens.sort(key=lambda x: -abs(x["contribuicao"]))
    direcao = "SOBE" if soma >= LIMIAR_DADOS else "CORTA" if soma <= -LIMIAR_DADOS else "MANTEM"
    return {"direcao": direcao, "soma": round(soma, 2), "n": n, "n_alto": n_alto,
            "desde": corte or inicio[:10], "zerado_por_decisao": bool(corte),
            "limiar": LIMIAR_DADOS, "meia_vida_dias": MEIA_VIDA, "principais": itens[:6]}


def dimensao_texto(moeda, discursos, agora):
    """Falas dos dirigentes desta moeda. So conta se o feed do banco estiver conectado —
    AUD, NZD e CHF saem None (buraco declarado), nunca zero."""
    D = discursos or {}
    status = (D.get("status_fontes") or {}).get(moeda)
    itens = [x for x in D.get("itens", []) if (x.get("moeda") or "USD") == moeda]
    if status and str(status).startswith("not connected"):
        return None
    if not itens and moeda != "USD" and not status:
        return None                                   # feed nem tentado — nao conectado
    inicio = (agora - dt.timedelta(days=JANELA_DIAS)).date().isoformat()
    itens = [x for x in itens if (x.get("data") or "") >= inicio]
    if not itens:
        # silencio nao e voto: sem fala na janela, a dimensao nao conta — nem para MANTEM.
        # Antes contava, e o GBP saia com "75% em manutencao" tendo zero discursos lidos.
        return None
    h = sum(int(x.get("marcadores_hawkish") or 0) for x in itens)
    d = sum(int(x.get("marcadores_dovish") or 0) for x in itens)
    if h == 0 and d == 0:
        return None                                   # falas sem marcador de politica: idem
    direcao = "SOBE" if h > d else "CORTA" if d > h else "MANTEM"
    return {"direcao": direcao, "hawkish": h, "dovish": d, "n": len(itens),
            "oradores": [x.get("orador") for x in itens][:6],
            "nota": "expression count over speeches and the statement — a pointer, not a reading"}


def dimensao_ciclo(b, agora):
    bp, data = b.get("ultima_mudanca_bp"), b.get("ultima_mudanca")
    try:
        idade = (agora.date() - dt.date.fromisoformat(data)).days
    except Exception:
        idade = None
    if bp is None or idade is None:
        return {"direcao": "MANTEM", "bp": bp, "idade_dias": idade, "nota": "no last move on file"}
    if idade > CICLO_VALIDADE_DIAS:
        return {"direcao": "MANTEM", "bp": bp, "idade_dias": idade,
                "nota": "last move %d days ago — reads as hold" % idade}
    return {"direcao": "SOBE" if bp > 0 else "CORTA", "bp": bp, "idade_dias": idade,
            "nota": "last move %+d bp, %d days ago" % (bp, idade)}


def le_moeda(m, ev, bancos, discursos, agora):
    b = (bancos or {}).get("bancos", {}).get(m, {})
    dims = {
        "dados": dimensao_dados(ev, m, agora),
        "texto": dimensao_texto(m, discursos, agora),
        "ciclo": dimensao_ciclo(b, agora),
        "mercado": None,
    }
    disponiveis = {k: v for k, v in dims.items() if v}
    votos = Counter(v["direcao"] for v in disponiveis.values())
    if not votos:
        direcao, concordam = "MANTEM", 0
    else:
        top = votos.most_common()
        if len(top) > 1 and top[0][1] == top[1][1]:
            direcao = "MANTEM"                    # empate nao e leitura
            concordam = votos.get("MANTEM", 0)
        else:
            direcao, concordam = top[0]
    conv = PESO_DIM * concordam
    teto = PESO_DIM * len(disponiveis)
    intensidade = 0 if direcao == "MANTEM" else (1 if conv <= 25 else 2 if conv <= 50 else 3)
    return {
        "moeda": m, "direcao": direcao, "intensidade": intensidade,
        "conviccao_pct": conv, "conviccao_teto_pct": teto,
        "dimensoes_ligadas": len(disponiveis), "dimensoes_total": len(dims),
        "concordam": {k: (v["direcao"] == direcao) for k, v in disponiveis.items()},
        "dimensoes": dims,
        "taxa_texto": b.get("taxa_texto"), "proxima": b.get("proxima"), "dias_ate": b.get("dias_ate"),
    }


def le_pares(leituras):
    L = {m: Leitura(m, x["direcao"], x["intensidade"], x.get("proxima") or "—",
                    "sentimento %d%%" % x["conviccao_pct"]) for m, x in leituras.items()}
    saida = []
    for par in PARES:
        r = le_par(par, L)
        b, q = par[:3], par[3:]
        lb, lq = leituras[b], leituras[q]
        vb, vq = L[b].valor or 0, L[q].valor or 0
        if abs(vb) == abs(vq):
            perna = None if vb == 0 else "ambas"
        else:
            perna = b if abs(vb) > abs(vq) else q
        r.update({
            "base": b, "cotada": q,
            "conviccao_pct": round((lb["conviccao_pct"] + lq["conviccao_pct"]) / 2)
                             if r["sinal"] in ("BULL", "BEAR") else 0,
            "perna_motivo": perna,
            "leitura_base": {"direcao": lb["direcao"], "conviccao_pct": lb["conviccao_pct"]},
            "leitura_cotada": {"direcao": lq["direcao"], "conviccao_pct": lq["conviccao_pct"]},
        })
        saida.append(r)

    # a lei das duas pernas: quem compartilha a perna que da o motivo e a MESMA aposta
    por_perna = {}
    for r in saida:
        if r["sinal"] in ("BULL", "BEAR") and r.get("perna_motivo") not in (None, "ambas"):
            por_perna.setdefault(r["perna_motivo"], []).append(r["par"])
    for r in saida:
        p = r.get("perna_motivo")
        r["mesma_aposta"] = [x for x in por_perna.get(p, []) if x != r["par"]] if p in por_perna else []
    return saida


def le_instrumentos(leituras):
    """XAUUSD, NQ e ES — os tres respondem ao juro americano, e so a perna do USD conta.

    O Eduardo apontou (02/set): "eles tem correlacao estreitamente ligada com os juros dos
    USA". O que esta MEDIDO em casa e so o ouro: juro real de 10 anos x ouro = -0,684
    contemporaneo em 60 pregoes (n=18, janelas sem sobreposicao); a preditiva morre no ruido
    (-0,132). NQ e ES entram pelo canal de livro-texto (taxa de desconto comprime multiplo,
    NQ mais que ES por ter duracao maior) — NAO medido em casa, e sai declarado assim.

    ⚠️ Direcao de LEITURA, nao de entrada: nas 88 operacoes manuais do Eduardo o dolar no
    minuto correlacionou +0,26 com o ouro e quebrou 41% das vezes (filtro do DXY reprovado).
    Isto aqui e o lado fundamental do mes, nunca a vela.
    """
    u = leituras.get("USD") or {}
    d = u.get("direcao", "MANTEM")
    conv = u.get("conviccao_pct", 0)
    inverso = {"SOBE": "BEAR", "CORTA": "BULL", "MANTEM": "NAO NEGOCIA"}
    sinal = inverso.get(d, "NAO NEGOCIA")
    motivos = ((u.get("dimensoes") or {}).get("dados") or {}).get("principais", [])[:4]

    # As correlacoes MEDIDAS (correlacao_juros.py): 5 anos, blocos sem sobreposicao, com a
    # preditiva ao lado. Se o arquivo faltar, o cartao diz "not measured" — nunca um numero
    # de memoria.
    corr = carrega_json(os.path.join(AQUI, "data", "correlacao_juros.json")) or {}
    corr_inst = corr.get("instrumentos", {})

    def medido_de(sym):
        c = corr_inst.get(sym)
        if not c or not c.get("series"):
            return None, "NOT measured in-house yet — correlacao_juros.py has not run"
        s = c["series"]
        real = s.get("real10y") or {}
        nom2 = s.get("nominal2y") or {}
        txt = ("5 years of daily data, non-overlapping blocks: 10y real yield %s same day, %s over 20 sessions "
               "(n=%s), %s over 60 sessions (n=%s); 2y nominal %s over 60 sessions. Predictive (rates today → "
               "price tomorrow / next 5 days): %s / %s — inside noise. Micro contract tracks the big one at %s."
               % (real.get("contemp_1d"), real.get("contemp_20d"), real.get("n_20d"),
                  real.get("contemp_60d"), real.get("n_60d"), nom2.get("contemp_60d"),
                  real.get("pred_1d"), real.get("pred_5d"), c.get("micro_vs_grande_corr")))
        return {"series": s, "micro_vs_grande": c.get("micro_vs_grande_corr"),
                "simbolo_micro": c.get("simbolo_micro"), "gerado_em": corr.get("gerado_em"),
                "nota": corr.get("nota")}, txt
    base = {
        "perna": "USD", "leitura_usd": {"direcao": d, "conviccao_pct": conv,
                                        "teto_pct": u.get("conviccao_teto_pct")},
        "sinal": sinal, "conviccao_pct": conv if d != "MANTEM" else 0,
        "motivos": motivos,
        "aviso": "a reading of the fundamental side over weeks, not an entry rule: on 88 manual "
                 "trades the dollar at the minute correlated +0.26 with gold and broke 41% of "
                 "the time (DXY filter reproved).",
    }
    out = []
    for sym, nome, canal in (
        ("XAUUSD", "Gold",
         "real rates: a hawkish USD reading lifts real yields and gold falls; a dovish one does the opposite"),
        ("NQ", "Nasdaq 100",
         "discount rate: a higher expected policy rate compresses equity multiples, and long-duration tech most of all"),
        ("ES", "S&P 500",
         "discount rate: same channel as NQ, with less duration and more earnings sensitivity to growth"),
    ):
        correl, medido = medido_de(sym)
        out.append(dict(base, simbolo=sym, nome=nome, canal=canal, medido=medido, correlacoes=correl))
    return out


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 88)
    print("SENTIMENTO — leitura para frente, por moeda e por par")
    print("=" * 88)
    ev, origem = eventos_janela(agora)
    bancos = carrega_json(BANCOS)
    discursos = carrega_json(DISCURSOS) or carrega_json(DISCURSOS_FED)
    print("  eventos na janela: %d  (%s)" % (len(ev), origem))

    leituras = {m: le_moeda(m, ev, bancos, discursos, agora) for m in MOEDAS}
    print()
    print("  %-4s %-7s %-5s %-6s  %-22s %-22s %-24s %s"
          % ("ccy", "lean", "conv", "teto", "dados", "texto", "ciclo", "mercado"))
    print("  " + "-" * 100)
    for m in MOEDAS:
        x = leituras[m]
        D = x["dimensoes"]
        dd = D["dados"]; tt = D["texto"]; cc = D["ciclo"]
        print("  %-4s %-7s %3d%%  %3d%%   %-22s %-22s %-24s %s"
              % (m, x["direcao"], x["conviccao_pct"], x["conviccao_teto_pct"],
                 "%s (%+.1f, n=%d)" % (dd["direcao"], dd["soma"], dd["n"]),
                 ("%s (%dh/%dd)" % (tt["direcao"], tt["hawkish"], tt["dovish"])) if tt else "not connected",
                 "%s (%s)" % (cc["direcao"], cc["nota"][:18]),
                 "not connected"))

    pares = le_pares(leituras)
    neg = [r for r in pares if r["sinal"] in ("BULL", "BEAR")]
    print()
    print("  PARES COM TESE — %d de %d" % (len(neg), len(pares)))
    for r in sorted(neg, key=lambda x: (-x["forca"], -x["conviccao_pct"])):
        print("    %-7s %-4s forca %d  conv %2d%%  %-26s razao: %-5s  mesma aposta: %s"
              % (r["par"], r["sinal"], r["forca"], r["conviccao_pct"], r["motivo"][:26],
                 r.get("perna_motivo") or "—", ", ".join(r["mesma_aposta"][:5]) or "—"))
    print("  NAO NEGOCIA: %d" % sum(1 for r in pares if r["sinal"] == "NAO NEGOCIA"))

    instrumentos = le_instrumentos(leituras)
    print()
    print("  INSTRUMENTOS PELA PERNA DO USD (%s %d%%):" % (leituras["USD"]["direcao"], leituras["USD"]["conviccao_pct"]))
    for i in instrumentos:
        print("    %-7s %-12s %s" % (i["simbolo"], i["sinal"], i["canal"][:70]))

    rel = {
        "gerado_em": agora.isoformat(),
        "origem_eventos": origem,
        "regua": {"dimensoes": ["dados", "texto", "ciclo", "mercado"], "peso_por_dimensao_pct": PESO_DIM,
                  "janela_dias": JANELA_DIAS, "meia_vida_dias": MEIA_VIDA, "limiar_dados": LIMIAR_DADOS,
                  "ciclo_validade_dias": CICLO_VALIDADE_DIAS,
                  "nao_conectado": {"texto": "only the Fed is wired (fed_discursos.py)",
                                    "mercado": "no free OIS/futures source; yields excluded by design"}},
        "aviso": "a READING of the fundamental side of each leg, not a signal. Conviction is the "
                 "share of connected dimensions that agree; a missing dimension lowers the ceiling, "
                 "it never counts as zero. FUND v0.1 was closed as an entry rule after 15 null tests.",
        "moedas": leituras,
        "pares": pares,
        "instrumentos": instrumentos,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
