# -*- coding: utf-8 -*-
"""backtest_bo_bd_fundamento.py — BO/BD com fundamento PONTO-NO-TEMPO (08/set/2026)

A ESTRATEGIA, nas palavras do Eduardo
--------------------------------------
"vamos testar uma estrategia de BO (breakout) e BD (break down), isso no grafico de dias,
 nos compramos se os fundamentos da empresa sao solidos e estao abaixo do nivel EMA 200, e
 vendemos se os fundamentos da empresa sao mais ou menos e esta acima do EMA 200"

  COMPRA (BO)  rompimento de alta  +  fundamento SOLIDO        +  preco ABAIXO da EMA 200
  VENDE  (BD)  rompimento de baixa +  fundamento MAIS OU MENOS +  preco ACIMA  da EMA 200

E uma ideia coerente e contraria: comprar empresa boa quando ela esta apanhando, e vender
empresa mediana quando ela esta esticada — em cada caso no momento em que o preco confirma.

O QUE TORNA ESTE TESTE HONESTO, E QUE NAO EXISTIA ATE HOJE
-----------------------------------------------------------
Classificar "fundamento solido" com o balanco de HOJE para decidir uma compra de 2019 e
look-ahead — e a miragem que matou o Deep Value (CAGR +36,5% que era so sobrevivencia).
Aqui a classificacao sai de `data/core/painel_fundamento_pit.json`, que carrega a DATA DE
PUBLICACAO de cada trimestre, vinda do SEC EDGAR. Em cada data o teste so enxerga o que ja
tinha sido PUBLICADO ate ali.

  ⚠️ O que isto resolve: ponto-no-tempo.
  ⚠️ O que isto NAO resolve: sobrevivencia. A lista de tickers foi escolhida hoje.
     Sao dois vieses diferentes; so um caiu. Por isso o teste principal e a DECOMPOSICAO
     e o embaralhamento do rotulo — os dois imunes a sobrevivencia, porque ela fica dos
     dois lados da comparacao.

CLASSIFICACAO DE FUNDAMENTO (declarada, nao otimizada)
------------------------------------------------------
Do trimestre mais recente JA PUBLICADO na data:
    +1  margem operacional > 0
    +1  margem de FCF > 0
    +1  ROIC >= 10 (ou ROE >= 10 quando o ROIC nao fecha)
    +1  receita YoY > 0
    -1  diluicao YoY > 1,0%   (o limiar da propria casa, LIM["diluicao_pct_ano"])
  SOLIDO >= 3 · MAIS OU MENOS 1 a 2 · FRACO <= 0
O corte do Eduardo VENDE o "mais ou menos". O "fraco" e medido a parte, de graca, porque
saber se vender o pior seria melhor que vender o mediano responde a pergunta dele por outro
lado.

GEOMETRIA (a da casa, adaptada ao diario)
------------------------------------------
A casa fechou em 29/ago: "entrada no fechamento da vela de rompimento; SL = close +- 1 x
ATR(14); TP 2R fixo" — e deixou UMA coisa em aberto: "falta so QUAL NIVEL e rompido".
Aqui o nivel adotado e o EXTREMO DAS 20 SESSOES ANTERIORES (sem contar a de hoje). Esta
escolha e minha, nao da casa, e esta declarada porque e o parametro mais facil de garimpar.

  BO: fechamento > maxima das 20 sessoes anteriores
  BD: fechamento < minima das 20 sessoes anteriores
  entrada no FECHAMENTO do dia do rompimento · SL = 1 x ATR(14) · TP = 2R
  saida por tempo em 60 sessoes (declarada; a geometria da casa nao tem prazo)
  quando maxima e minima do dia tocam alvo e stop, assume-se o STOP (conservador)
  uma posicao por nome de cada vez · resultado contado em R, a moeda da casa

Uso: python backtest_bo_bd_fundamento.py [--sims 2000]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

if getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
from backtest_momentum import baixa, serie  # noqa: E402

PAINEL = os.path.join(RAIZ, "data", "core", "painel_fundamento_pit.json")
SAIDA = os.path.join(RAIZ, "data", "backtest_bo_bd_fundamento.json")

N_NIVEL = 20          # sessoes do extremo rompido
N_ATR = 14
RR = 2.0
MAX_BARRAS = 60
EMA_LEN = 200
SLIPPAGE = 0.0005
DILUICAO_LIM = 1.0
SEMENTE = 20260908


# ------------------------------------------------------------------ fundamento PIT
def classifica(linha):
    """Nota de 0 a 4 (menos diluicao) a partir de UM trimestre ja publicado."""
    if linha is None:
        return None
    n = 0
    mo, mf = linha.get("margem_op"), linha.get("margem_fcf")
    roic, roe = linha.get("roic"), linha.get("roe")
    cr, dil = linha.get("cresc_receita_yoy"), linha.get("diluicao_yoy_pct")
    if mo is not None and mo > 0:
        n += 1
    if mf is not None and mf > 0:
        n += 1
    r = roic if roic is not None else roe
    if r is not None and r >= 10:
        n += 1
    if cr is not None and cr > 0:
        n += 1
    if dil is not None and dil > DILUICAO_LIM:
        n -= 1
    return n


def rotulo(n):
    if n is None:
        return None
    if n >= 3:
        return "solido"
    if n >= 1:
        return "mais_ou_menos"
    return "fraco"


def serie_rotulos(linhas, datas):
    """Para cada data do preco, o rotulo do ultimo trimestre PUBLICADO ate ali."""
    pub = [(pd.Timestamp(x["publicado_em"]), x) for x in linhas if x.get("publicado_em")]
    pub.sort(key=lambda z: z[0])
    if not pub:
        return [None] * len(datas)
    ds = np.array([p[0] for p in pub])
    out, j = [], 0
    for t in datas:
        while j + 1 < len(ds) and ds[j + 1] <= t:
            j += 1
        out.append(rotulo(classifica(pub[j][1])) if ds[j] <= t else None)
    return out


# ------------------------------------------------------------------ motor
def opera(d: pd.DataFrame, rots, usa_fund=True, usa_ema=True, rot_long="solido",
          rot_short="mais_ou_menos"):
    o = d["Open"].to_numpy(float); h = d["High"].to_numpy(float)
    lo = d["Low"].to_numpy(float); c = d["Close"].to_numpy(float)
    n = len(d)
    ema = pd.Series(c).ewm(span=EMA_LEN, adjust=False).mean().to_numpy()
    tr = np.maximum(h[1:] - lo[1:], np.maximum(abs(h[1:] - c[:-1]), abs(lo[1:] - c[:-1])))
    atr = np.concatenate([[np.nan], pd.Series(tr).rolling(N_ATR).mean().to_numpy()])
    hmax = pd.Series(h).rolling(N_NIVEL).max().shift(1).to_numpy()
    lmin = pd.Series(lo).rolling(N_NIVEL).min().shift(1).to_numpy()

    ops = []
    i = max(EMA_LEN, N_NIVEL, N_ATR) + 1
    while i < n:
        if np.isnan(atr[i]) or np.isnan(hmax[i]) or atr[i] <= 0:
            i += 1; continue
        rt = rots[i]
        bo = c[i] > hmax[i]
        bd = c[i] < lmin[i]
        lado = 0
        if bo and (not usa_ema or c[i] < ema[i]) and (not usa_fund or rt == rot_long):
            lado = 1
        elif bd and (not usa_ema or c[i] > ema[i]) and (not usa_fund or rt == rot_short):
            lado = -1
        if lado == 0:
            i += 1; continue

        ent = c[i] * (1 + SLIPPAGE) if lado > 0 else c[i] * (1 - SLIPPAGE)
        risco = atr[i]
        sl = ent - lado * risco
        tp = ent + lado * RR * risco
        saida, motivo, j = None, None, i
        for j in range(i + 1, min(i + 1 + MAX_BARRAS, n)):
            bate_sl = (lo[j] <= sl) if lado > 0 else (h[j] >= sl)
            bate_tp = (h[j] >= tp) if lado > 0 else (lo[j] <= tp)
            if bate_sl:                       # conservador: stop antes do alvo
                saida, motivo = sl, "stop"; break
            if bate_tp:
                saida, motivo = tp, "alvo"; break
        if saida is None:
            j = min(i + MAX_BARRAS, n - 1)
            saida, motivo = c[j], "tempo"
        saida = saida * (1 - SLIPPAGE) if lado > 0 else saida * (1 + SLIPPAGE)
        r = lado * (saida - ent) / risco
        ops.append({"entrada": str(d.index[i])[:10], "saida": str(d.index[j])[:10],
                    "lado": "compra" if lado > 0 else "venda", "motivo": motivo,
                    "R": float(r), "rotulo": rt, "barras": int(j - i)})
        i = j + 1
    return ops


def resume(ops, rot):
    if not ops:
        return {"celula": rot, "n": 0}
    r = np.array([x["R"] for x in ops])
    g = r[r > 0]; p = r[r <= 0]
    pf = (g.sum() / abs(p.sum())) if len(p) and p.sum() != 0 else np.inf
    return {"celula": rot, "n": len(r), "soma_R": round(float(r.sum()), 2),
            "media_R": round(float(r.mean()), 4),
            "WR_pct": round(float((r > 0).mean() * 100), 1),
            "PF": round(float(pf), 2) if np.isfinite(pf) else None,
            "compras": int(sum(1 for x in ops if x["lado"] == "compra")),
            "vendas": int(sum(1 for x in ops if x["lado"] == "venda"))}


def linha(b):
    if not b.get("n"):
        print("   %-40s  sem operacoes" % b["celula"]); return
    print("   %-40s %5d %9.2f %9.4f %7.1f%% %7s  %4dc/%4dv"
          % (b["celula"], b["n"], b["soma_R"], b["media_R"], b["WR_pct"],
             ("%.2f" % b["PF"]) if b["PF"] else "inf", b["compras"], b["vendas"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=2000)
    a = ap.parse_args()

    P = json.load(io.open(PAINEL, encoding="utf-8"))
    painel = P["painel"]
    print("BO/BD COM FUNDAMENTO PONTO-NO-TEMPO")
    print("=" * 104)
    print("painel: %d tickers · %d linhas · fonte %s" % (P["n_tickers"], P["n_linhas"], P["fonte"]))
    for lim in P["limites_declarados"]:
        print("   ! %s" % lim)
    print()

    tks = sorted(painel)
    g = baixa(sorted(json.load(io.open(os.path.join(RAIZ, "data", "empresas.json"),
                                       encoding="utf-8"))["empresas"]), 10)

    dados = {}
    for tk in tks:
        d = serie(g, tk)
        if d is None:
            continue
        rots = serie_rotulos(painel[tk], d.index)
        if sum(1 for x in rots if x) < 100:
            continue
        dados[tk] = (d, rots)
    print("nomes com preco E fundamento publicado: %d\n" % len(dados))

    # distribuicao dos rotulos, para o Eduardo ver o que a regra classifica
    conta = {}
    for tk, (d, rots) in dados.items():
        for x in rots:
            if x:
                conta[x] = conta.get(x, 0) + 1
    tot = sum(conta.values())
    print("dias por classe de fundamento: %s\n"
          % " · ".join("%s %.0f%%" % (k, 100 * v / tot) for k, v in sorted(conta.items())))

    # ------------------------------------------------------------------ decomposicao
    print("DECOMPOSICAO — qual peca carrega o resultado?\n")
    print("   %-40s %5s %9s %9s %8s %7s  %s"
          % ("célula", "n", "soma R", "média R", "WR", "PF", "compras/vendas"))
    print("   " + "-" * 96)
    celulas, ops_por_celula = [], {}
    for rot, kw in [
        ("1. BO/BD puro (sem filtro nenhum)", dict(usa_fund=False, usa_ema=False)),
        ("2. BO/BD + EMA200 (sem fundamento)", dict(usa_fund=False, usa_ema=True)),
        ("3. BO/BD + fundamento (sem EMA200)", dict(usa_fund=True, usa_ema=False)),
        ("4. A ESTRATEGIA (fundamento + EMA200)", dict(usa_fund=True, usa_ema=True)),
        ("5. idem, mas vendendo o FRACO", dict(usa_fund=True, usa_ema=True,
                                               rot_short="fraco")),
    ]:
        todas = []
        for tk, (d, rots) in dados.items():
            todas += opera(d, rots, **kw)
        b = resume(todas, rot); celulas.append(b); ops_por_celula[rot] = todas
        linha(b)

    alvo = "4. A ESTRATEGIA (fundamento + EMA200)"
    real = [x for x in celulas if x["celula"] == alvo][0]

    # ------------------------------------------------------------------ MC1 rotulo embaralhado
    print("\nMC1 — ROTULO DE FUNDAMENTO EMBARALHADO ENTRE OS NOMES (%d rodadas)" % min(a.sims, 300))
    print("   Cada nome recebe a SERIE de rotulos de outro nome. O gatilho de preco, a EMA200,")
    print("   o stop e o alvo ficam identicos; so o casamento entre a empresa e o proprio")
    print("   fundamento e destruido. Responde: o fundamento SELECIONA, ou e so um sorteio")
    print("   que reduz o numero de operacoes?\n")
    rng = np.random.default_rng(SEMENTE)
    nomes = sorted(dados)
    somas, medias, ns = [], [], []
    n_mc = min(a.sims, 300)
    for k in range(n_mc):
        perm = list(rng.permutation(nomes))
        todas = []
        for tk, outro in zip(nomes, perm):
            d, _ = dados[tk]
            _, rots_o = dados[outro]
            r2 = rots_o[:len(d)] + [None] * max(0, len(d) - len(rots_o))
            todas += opera(d, r2, usa_fund=True, usa_ema=True)
        if todas:
            r = np.array([x["R"] for x in todas])
            somas.append(r.sum()); medias.append(r.mean()); ns.append(len(r))
        if (k + 1) % max(1, n_mc // 6) == 0:
            print("   ... %d/%d · soma R embaralhada mediana %+.1f" % (k + 1, n_mc, np.median(somas)))

    somas = np.array(somas); medias = np.array(medias)
    pct_soma = float((somas < real["soma_R"]).mean() * 100)
    pct_media = float((medias < real["media_R"]).mean() * 100)
    print("\n   %-22s %10s %10s %10s %12s" % ("", "p05", "mediana", "p95", "REAL"))
    print("   " + "-" * 70)
    print("   %-22s %10.2f %10.2f %10.2f %12.2f"
          % ("soma R", np.quantile(somas, .05), np.median(somas), np.quantile(somas, .95),
             real["soma_R"]))
    print("   %-22s %10.4f %10.4f %10.4f %12.4f"
          % ("media R por op", np.quantile(medias, .05), np.median(medias),
             np.quantile(medias, .95), real["media_R"]))
    print("   %-22s %10d %10d %10d %12d"
          % ("n de operacoes", np.quantile(ns, .05), np.median(ns), np.quantile(ns, .95),
             real["n"]))
    print("\n   PERCENTIL DO REAL: soma %.1f · media por operacao %.1f" % (pct_soma, pct_media))
    if pct_media >= 95:
        print("   -> o fundamento SELECIONA: o real esta fora da nuvem do embaralhado.")
    else:
        print("   -> o real esta DENTRO da nuvem. O fundamento, como classificado aqui, nao")
        print("      esta escolhendo empresa melhor — esta so escolhendo MENOS operacoes.")

    # ------------------------------------------------------------------ MC2 bootstrap
    print("\nMC2 — BOOTSTRAP DAS OPERACOES (%d rodadas)" % a.sims)
    ops = ops_por_celula[alvo]
    if ops:
        r = np.array([x["R"] for x in ops])
        boot = np.array([rng.choice(r, size=len(r), replace=True).sum() for _ in range(a.sims)])
        print("   soma R  p05 %+.1f · mediana %+.1f · p95 %+.1f · chance de ficar NEGATIVO %.1f%%"
              % (np.quantile(boot, .05), np.median(boot), np.quantile(boot, .95),
                 float((boot < 0).mean() * 100)))

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": str(pd.Timestamp.now("UTC"))[:19] + "Z",
                   "natureza": "EXPLORACAO — nao e pre-registro",
                   "parametros": {"nivel_sessoes": N_NIVEL, "atr": N_ATR, "RR": RR,
                                  "max_barras": MAX_BARRAS, "ema": EMA_LEN,
                                  "slippage": SLIPPAGE, "diluicao_lim": DILUICAO_LIM},
                   "escolhas_minhas_declaradas": [
                       "o NIVEL rompido = extremo das 20 sessoes anteriores; a casa deixou "
                       "esse parametro em aberto ('falta so qual nivel e rompido')",
                       "saida por tempo em 60 sessoes; a geometria da casa nao tem prazo",
                       "quando alvo e stop cabem no mesmo dia, assume-se o stop",
                       "classificacao de fundamento com 4 criterios +1 e diluicao -1",
                   ],
                   "limites_do_painel": P["limites_declarados"],
                   "n_nomes": len(dados),
                   "distribuicao_rotulos_pct": {k: round(100 * v / tot, 1)
                                                for k, v in sorted(conta.items())},
                   "decomposicao": celulas,
                   "MC1_rotulo_embaralhado": {
                       "n_sims": int(len(somas)),
                       "soma_p05": round(float(np.quantile(somas, .05)), 2),
                       "soma_mediana": round(float(np.median(somas)), 2),
                       "soma_p95": round(float(np.quantile(somas, .95)), 2),
                       "percentil_real_soma": round(pct_soma, 1),
                       "percentil_real_media": round(pct_media, 1)}},
                  f, ensure_ascii=False, indent=1)
    print("\ngravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
