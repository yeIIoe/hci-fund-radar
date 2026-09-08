# -*- coding: utf-8 -*-
"""painel_fundamento_pit.py — O PAINEL DE FUNDAMENTO PONTO-NO-TEMPO (08/set/2026)

O QUE ISTO DESTRAVA
-------------------
Esta escrito em tres documentos internos que o gargalo da casa e "falta fonte de fundamento
POINT-IN-TIME (nao o metodo)" — foi o que matou o backtest do Deep Value e o que fez a busca
por um fornecedor pago comecar.

Acontece que a casa JA TEM a fonte, de graca, e vinha usando so a ponta dela: o
`fundamento_ficha.py` le a API companyfacts do SEC EDGAR, que traz **a data de publicacao de
cada fato** (`publicado_em`). Isso e point-in-time de verdade: da para saber o que era
CONHECIDO em qualquer data passada, sem look-ahead.

O que faltava era so nao jogar fora a serie. A ficha guarda os ultimos 8 trimestres
(N_TEND=8) porque e o que o Eduardo le na tela. Aqui a serie INTEIRA e salva, que e o que
um backtest precisa.

O QUE ESTE ARQUIVO GERA
-----------------------
data/core/painel_fundamento_pit.json — por ticker, a lista de trimestres com:
    fim_trim · publicado_em · margem_bruta · margem_op · roe · roic · div_liq_ebitda
    cobertura_juros · margem_fcf · cresc_receita_yoy · diluicao_yoy_pct · acoes_diluidas_mm

LIMITES, DECLARADOS ANTES DE QUALQUER USO
------------------------------------------
  1. So EUA. O EDGAR nao cobre a B3 — as 12 brasileiras ficam de fora.
  2. O XBRL virou obrigatorio por fases entre 2009 e 2011. Empresa que abriu capital depois
     comeca quando abriu. Historico util comeca ~2010, nao 1995.
  3. SOBREVIVENCIA CONTINUA: o EDGAR guarda quem quebrou, mas a NOSSA LISTA
     (data/empresas.json) foi escolhida hoje. Isto resolve o ponto-no-tempo, NAO resolve a
     sobrevivencia. Sao dois vieses diferentes e so um caiu aqui.
  4. O valor e o ORIGINALMENTE reportado naquele arquivamento (o EDGAR guarda por
     accession). Reapresentacao posterior aparece como fato novo, com data nova.
  5. `div_liq_ebitda` as vezes vem do Yahoo na ficha (sem data) — aqui SO entra o que veio do
     EDGAR; o resto sai nulo, e nulo e melhor que numero sem data.

Uso: python painel_fundamento_pit.py [--limite N]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import fundamento_ficha as FF

RAIZ = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(RAIZ, "data", "core", "painel_fundamento_pit.json")

CAMPOS = ["fim_trim", "publicado_em", "margem_bruta", "margem_op", "roe", "roic",
          "div_liq_ebitda", "cobertura_juros", "margem_fcf", "cresc_receita_yoy",
          "diluicao_yoy_pct", "acoes_diluidas_mm"]


def universo_eua():
    d = json.load(io.open(os.path.join(RAIZ, "data", "empresas.json"), encoding="utf-8"))
    return sorted(t for t in d["empresas"] if not t.endswith(".SA"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0)
    a = ap.parse_args()

    ts = universo_eua()
    if a.limite:
        ts = ts[:a.limite]
    print("PAINEL DE FUNDAMENTO PONTO-NO-TEMPO — %d tickers dos EUA" % len(ts))
    print("fonte: SEC EDGAR companyfacts XBRL (gratuita, com data de publicacao)")
    print("=" * 96)

    cik = FF.mapa_cik()
    print("mapa CIK: %d tickers conhecidos\n" % len(cik))

    painel, erros, t0 = {}, {}, time.time()
    for i, t in enumerate(ts, 1):
        s = time.time()
        # o mapa devolve [cik, nome_da_empresa], nao a string do CIK
        reg = cik.get(t)
        c = reg[0] if isinstance(reg, (list, tuple)) and reg else reg
        if not c:
            erros[t] = "sem CIK no mapa do EDGAR"
            print("  %3d/%d %-7s -- %s" % (i, len(ts), t, erros[t]))
            continue
        try:
            # companyfacts devolve (dados, origem) — pegar a tupla inteira faz o
            # linhas_ttm receber uma tupla e morrer com 'tuple has no attribute get'
            cf, origem = FF.companyfacts(c)
            if not cf or "__erro__" in (cf or {}):
                erros[t] = "companyfacts nao respondeu: %s" % (cf or {}).get("__erro__", "sem resposta")
                print("  %3d/%d %-7s -- %s" % (i, len(ts), t, erros[t]))
                continue
            L, _ = FF.linhas_ttm(cf)
            linhas = [{k: x.get(k) for k in CAMPOS} for x in L
                      if x.get("publicado_em") and x.get("fim_trim")]
            if not linhas:
                erros[t] = "companyfacts sem TTM montavel"
                print("  %3d/%d %-7s -- %s" % (i, len(ts), t, erros[t]))
                continue
            painel[t] = linhas
            print("  %3d/%d %-7s ok  %3d trimestres  %s -> %s  %.1fs"
                  % (i, len(ts), t, len(linhas), linhas[0]["publicado_em"],
                     linhas[-1]["publicado_em"], time.time() - s))
        except Exception as e:
            erros[t] = "%s: %s" % (type(e).__name__, str(e)[:80])
            print("  %3d/%d %-7s -- %s" % (i, len(ts), t, erros[t]))

    n_lin = sum(len(v) for v in painel.values())
    prim = min((v[0]["publicado_em"] for v in painel.values()), default="?")
    print("\n" + "=" * 96)
    print("painel: %d tickers · %d linhas de trimestre · publicacao mais antiga %s"
          % (len(painel), n_lin, prim))
    print("sem painel: %d (%s)" % (len(erros), ", ".join(sorted(erros)[:12])))
    if painel:
        prof = sorted(len(v) for v in painel.values())
        print("profundidade por ticker: mediana %d trimestres · minimo %d · maximo %d"
              % (prof[len(prof) // 2], prof[0], prof[-1]))

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "fonte": "SEC EDGAR companyfacts XBRL — com data de publicacao",
                   "campos": CAMPOS,
                   "limites_declarados": [
                       "so EUA; a B3 nao esta no EDGAR",
                       "XBRL obrigatorio por fases 2009-2011; historico util comeca ~2010",
                       "ponto-no-tempo RESOLVIDO; SOBREVIVENCIA NAO — a lista de tickers "
                       "foi escolhida hoje, quem quebrou nao esta nela",
                       "valor originalmente reportado naquele arquivamento",
                   ],
                   "n_tickers": len(painel), "n_linhas": n_lin,
                   "sem_painel": erros,
                   "segundos": round(time.time() - t0, 1),
                   "painel": painel}, f, ensure_ascii=False)
    print("\ngravado: %s (%.1f MB)" % (SAIDA, os.path.getsize(SAIDA) / 1e6))


if __name__ == "__main__":
    main()
