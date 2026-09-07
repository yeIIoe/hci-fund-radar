# -*- coding: utf-8 -*-
"""LINHA DE BASE DA REGRA — quanto o leitor_falas.py devolve de "indeterminado".

POR QUE ISTO E CODIGO, E NAO CONTA DA IA
    Lei da casa (ARQUITETURA_AGENTES.md, secao 1): numero medido e codigo, julgamento e IA.
    A linha de base que o agente `fala` precisa BATER e um numero que entra em conta, entao
    ela e medida aqui, gravada em agentes/fala/linha_de_base.json, e o agente apenas CITA.
    O agente NUNCA recalcula esta contagem de cabeca.

O QUE MEDE
    1. ARQUIVO HISTORICO (data/bis_discursos_historico.jsonl): 1.319 falas de 2009 a 2026.
       ATENCAO: esse arquivo NAO tem o corpo do discurso — so titulo e `resumo_bis`, que e a
       linha bibliografica do BIS ("Speech by Mr X, Governor of Y, at Z, cidade, data").
       Medir a regra ali mede o TETO DA ENTRADA, nao a qualidade da regra.
    2. ARQUIVOS VIVOS (data/bc_discursos.json e data/bis_discursos.json), onde existem frases
       extraidas do corpo — e onde a regra realmente tem chance.

COMO RODAR
    python agentes/fala/mede_linha_de_base.py            # mede e grava o JSON
    python agentes/fala/mede_linha_de_base.py --amostra 300   # so uma amostra do historico

A amostra e deterministica (as N primeiras linhas por data crescente), para o numero ser
recalculavel igual daqui a tres meses — que e a razao de existir da linha dura.
"""
from __future__ import annotations

import collections
import datetime as dt
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import leitor_falas as LF  # noqa: E402

HISTORICO = os.path.join(RAIZ, "data", "bis_discursos_historico.jsonl")
VIVOS = [os.path.join(RAIZ, "data", "bc_discursos.json"),
         os.path.join(RAIZ, "data", "bis_discursos.json")]
SAIDA = os.path.join(AQUI, "linha_de_base.json")


def _frases(texto: str) -> list:
    t = re.sub(r"\s+", " ", texto or "").strip()
    return [f for f in re.split(r"(?<=[.!?]) ", t) if len(f) >= 12]


def mede_historico(caminho: str, amostra: int | None = None) -> dict:
    linhas = []
    with io.open(caminho, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                linhas.append(json.loads(l))
    linhas.sort(key=lambda d: (d.get("data") or "", d.get("link") or ""))
    if amostra:
        linhas = linhas[:amostra]

    cont = collections.Counter()
    cont_pm = collections.Counter()
    por_moeda = collections.defaultdict(collections.Counter)
    achados = []
    for d in linhas:
        res = []
        for i, f in enumerate(_frases(d.get("titulo")) + _frases(d.get("resumo_bis"))):
            r = LF.classifica_frase(f)
            r["_i"] = i
            r["data"] = d.get("data")
            r["link"] = d.get("link")
            res.append(r)
        v = LF._agrega(res)
        cont[v["veredito"]] += 1
        por_moeda[d.get("moeda")][v["veredito"]] += 1
        if d.get("assunto") == "politica_monetaria":
            cont_pm[v["veredito"]] += 1
        if v["veredito"] != "indeterminado":
            achados.append({"moeda": d.get("moeda"), "orador": d.get("orador"),
                            "data": d.get("data"), "veredito": v["veredito"],
                            "trecho": (v.get("trecho") or "")[:200], "link": d.get("link")})

    n = len(linhas)
    n_pm = sum(cont_pm.values())
    return {
        "arquivo": "data/bis_discursos_historico.jsonl",
        "n": n,
        "amostra": ("as %d primeiras por data crescente" % amostra) if amostra else "todas",
        "corpo_disponivel": False,
        "corpo_nota": ("o historico guarda titulo e resumo_bis (linha bibliografica do BIS), "
                       "nunca o corpo do discurso — o teto da entrada e baixo por construcao"),
        "tamanho_mediano_do_resumo": (sorted(len(d.get("resumo_bis") or "") for d in linhas)[n // 2]
                                      if n else 0),
        "vereditos": dict(cont),
        "indeterminado_pct": round(100.0 * cont["indeterminado"] / n, 2) if n else None,
        "so_politica_monetaria": {"n": n_pm, "vereditos": dict(cont_pm),
                                  "indeterminado_pct": (round(100.0 * cont_pm["indeterminado"] / n_pm, 2)
                                                        if n_pm else None)},
        "por_moeda": {m: dict(c) for m, c in sorted(por_moeda.items())},
        "os_que_sairam_com_direcao": achados,
    }


def mede_vivos() -> list:
    saida = []
    for caminho in VIVOS:
        if not os.path.exists(caminho):
            continue
        with io.open(caminho, encoding="utf-8") as f:
            bruto = json.load(f)
        v = LF.vereditos_por_moeda(bruto, anotar_itens=False)
        linhas = [l for m in v for l in v[m]]
        itens = bruto.get("itens") or []
        saida.append({
            "arquivo": "data/" + os.path.basename(caminho),
            "gerado_em": bruto.get("gerado_em"),
            "n_itens": len(itens),
            "itens_sem_frase_extraida": sum(1 for i in itens if not (i.get("frases") or [])),
            "n_oradores": len(linhas),
            "vereditos": dict(collections.Counter(l["veredito"] for l in linhas)),
            "indeterminado_pct": (round(100.0 * sum(1 for l in linhas
                                                    if l["veredito"] == "indeterminado")
                                        / len(linhas), 2) if linhas else None),
        })
    return saida


def main():
    amostra = None
    if "--amostra" in sys.argv:
        amostra = int(sys.argv[sys.argv.index("--amostra") + 1])
    rel = {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(),
        "versao_regra": LF.VERSAO,
        "o_que_e": ("linha de base do classificador POR REGRA (leitor_falas.py). E o numero que "
                    "o agente `fala` tem de bater, e ele so CITA — nunca recalcula."),
        "historico": mede_historico(HISTORICO, amostra),
        "vivos": mede_vivos(),
    }
    with io.open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=1)
    h = rel["historico"]
    print("HISTORICO  n=%d  indeterminado=%.1f%%  (so politica monetaria: n=%d, %.1f%%)"
          % (h["n"], h["indeterminado_pct"], h["so_politica_monetaria"]["n"],
             h["so_politica_monetaria"]["indeterminado_pct"]))
    for v in rel["vivos"]:
        print("VIVO  %-28s oradores=%d  indeterminado=%.1f%%  itens sem frase=%d/%d"
              % (v["arquivo"], v["n_oradores"], v["indeterminado_pct"],
                 v["itens_sem_frase_extraida"], v["n_itens"]))
    print("gravado em agentes/fala/linha_de_base.json")


if __name__ == "__main__":
    main()
