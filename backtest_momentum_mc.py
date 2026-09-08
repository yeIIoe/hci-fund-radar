# -*- coding: utf-8 -*-
"""backtest_momentum_mc.py — MONTE CARLO da estrategia de momentum (08/set/2026)

Roda DEPOIS de `backtest_momentum.py`. Tres perguntas diferentes, tres experimentos.

MC1 — SORTE DO CAMINHO (bootstrap de bloco)
    Reamostra blocos de 21 pregoes dos retornos diarios da carteira global e reconstroi a
    curva. Responde: "quanto do resultado e a ORDEM em que as coisas aconteceram?".
    Blocos, e nao dias soltos, porque retorno diario tem autocorrelacao e volatilidade
    aglomerada; sortear dia a dia inventaria uma serie mais mansa que a real e faria o
    drawdown parecer menor do que e.

MC2 — SINAL EMBARALHADO (o decisivo)
    Mantem TODO o motor — o mesmo dimensionamento por volatilidade, o mesmo stop de 5%, os
    mesmos custos, as mesmas datas — e troca so a SEQUENCIA das pontuacoes semanais por uma
    permutacao dela mesma. A distribuicao de pontuacoes fica identica; o que se destroi e o
    casamento entre a pontuacao e o que veio DEPOIS dela.
    Responde a unica pergunta que interessa: o momentum ACERTA o momento, ou o resultado e
    so o efeito de estar exposto com esse perfil de tamanho?
    Se a estrategia real nao ficar fora da nuvem do embaralhado, o sinal nao esta somando
    nada — e o que sobra e exposicao, que sai mais barato comprando e segurando.

MC3 — COMPRAR E SEGURAR
    O piso de comparacao. Uma estrategia comprada que nao bate comprar e segurar nao paga o
    proprio trabalho, nem o risco de estar vendido em algumas semanas.

Uso: python backtest_momentum_mc.py [sims_mc2] [sims_mc1]      (padrao 200 e 5000)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# envolver stdout DUAS vezes fecha o buffer do primeiro wrapper — e foi o que quebrou o
# Monte Carlo, que importa este modulo depois de ja ter envolvido. Envolve so uma vez.
if getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from backtest_momentum import (  # noqa: E402
    universo, baixa, serie, roda, metricas, CAPITAL, A_ANO, HORIZONTES, JANELA_VOL)

SAIDA = RAIZ / "data" / "backtest_momentum_mc.json"
SEMENTE = 20260908
BLOCO = 21


def bootstrap_bloco(r: np.ndarray, n_sims: int, rng) -> dict:
    n = len(r)
    nb = int(np.ceil(n / BLOCO))
    finais, mdds, cagrs = [], [], []
    anos = n / A_ANO
    for _ in range(n_sims):
        ini = rng.integers(0, max(1, n - BLOCO), size=nb)
        s = np.concatenate([r[i:i + BLOCO] for i in ini])[:n]
        v = np.cumprod(1 + s)
        finais.append(v[-1])
        mdds.append(float((v / np.maximum.accumulate(v) - 1).min()))
        cagrs.append(v[-1] ** (1 / anos) - 1)
    q = lambda a, p: float(np.quantile(a, p))  # noqa: E731
    return {"n_sims": n_sims,
            "CAGR_p05_pct": round(q(cagrs, .05) * 100, 2),
            "CAGR_p50_pct": round(q(cagrs, .50) * 100, 2),
            "CAGR_p95_pct": round(q(cagrs, .95) * 100, 2),
            "MDD_p05_pct": round(q(mdds, .05) * 100, 2),
            "MDD_p50_pct": round(q(mdds, .50) * 100, 2),
            "MDD_pior_pct": round(float(np.min(mdds)) * 100, 2),
            "prob_negativo_pct": round(float(np.mean(np.array(cagrs) < 0)) * 100, 1)}


def main():
    n2 = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    n1 = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    base = json.load(io.open(RAIZ / "data" / "backtest_momentum.json", encoding="utf-8"))
    anos = 10
    tks = universo()
    g = baixa(tks, anos)
    rng = np.random.default_rng(SEMENTE)

    print("MONTE CARLO — momentum de quatro horizontes")
    print("=" * 100)
    real = base["em_globo"]["com_custo"]
    print("real (com custo): CAGR %+.2f%% · MDD %.1f%% · Sharpe %.2f · %s a %s"
          % (real["CAGR_pct"], real["MDD_pct"], real["sharpe"], real["inicio"], real["fim"]))

    # ---------------------------------------------------------------- series por nome
    dados, curvas_real = {}, {}
    for tk in tks:
        d = serie(g, tk)
        if d is None:
            continue
        cv, _, sc = roda(d, com_custo=True)
        m = metricas(cv, d.index)
        if m is None:
            continue
        dados[tk] = (d, sc)
        curvas_real[tk] = pd.Series(cv, index=d.index).dropna()
    print("nomes no experimento: %d\n" % len(dados))

    def em_globo(curvas):
        # mesma correcao do backtest_momentum.py: carteira de peso igual e a media dos
        # RETORNOS DIARIOS dos nomes vivos, composta depois. Media de curvas normalizadas
        # cria um degrau falso toda vez que um nome novo entra valendo 1,0.
        R = pd.DataFrame({k: v.pct_change() for k, v in curvas.items()})
        r = R.mean(axis=1, skipna=True).dropna()
        return (1 + r).cumprod() * CAPITAL

    glob_real = em_globo(curvas_real)
    r_real = glob_real.pct_change().dropna().to_numpy()

    # ---------------------------------------------------------------- MC3 comprar e segurar
    print("MC3 — COMPRAR E SEGURAR (o piso de comparacao)\n")
    bh = {}
    for tk, (d, _) in dados.items():
        c = d["Close"]
        bh[tk] = (c / c.iloc[0]) * CAPITAL
    glob_bh = em_globo(bh)
    m_bh = metricas(glob_bh.to_numpy(), glob_bh.index)
    print("   comprar e segurar: CAGR %+.2f%% · MDD %.1f%% · Sharpe %.2f"
          % (m_bh["CAGR_pct"], m_bh["MDD_pct"], m_bh["sharpe"]))
    print("   momentum         : CAGR %+.2f%% · MDD %.1f%% · Sharpe %.2f"
          % (real["CAGR_pct"], real["MDD_pct"], real["sharpe"]))
    print("   diferenca        : %+.2f pp de CAGR · %+.1f pp de MDD · %+.2f de Sharpe"
          % (real["CAGR_pct"] - m_bh["CAGR_pct"], real["MDD_pct"] - m_bh["MDD_pct"],
             real["sharpe"] - m_bh["sharpe"]))

    # ---------------------------------------------------------------- MC1 bootstrap
    print("\nMC1 — SORTE DO CAMINHO (bootstrap de bloco de %d pregoes, %d rodadas)\n"
          % (BLOCO, n1))
    b = bootstrap_bloco(r_real, n1, rng)
    print("   CAGR   p05 %+.2f%% · mediana %+.2f%% · p95 %+.2f%%"
          % (b["CAGR_p05_pct"], b["CAGR_p50_pct"], b["CAGR_p95_pct"]))
    print("   MDD    mediana %.1f%% · p05 %.1f%% · pior de todas %.1f%%"
          % (b["MDD_p50_pct"], b["MDD_p05_pct"], b["MDD_pior_pct"]))
    print("   chance de terminar NEGATIVO reordenando os mesmos retornos: %.1f%%"
          % b["prob_negativo_pct"])

    # ---------------------------------------------------------------- MC2 sinal embaralhado
    print("\nMC2 — SINAL EMBARALHADO (%d rodadas, motor inteiro preservado)\n" % n2)
    cagrs, sharpes, mdds = [], [], []
    for k in range(n2):
        curvas = {}
        for tk, (d, sc) in dados.items():
            pos = np.where(~np.isnan(sc))[0]
            emb = np.full(len(sc), np.nan)
            emb[pos] = rng.permutation(sc[pos])
            cv, _, _ = roda(d, com_custo=True, scores_forcados=np.nan_to_num(emb))
            s = pd.Series(cv, index=d.index).dropna()
            if len(s) > 60 and s.iloc[0] > 0:
                curvas[tk] = s
        if not curvas:
            continue
        gl = em_globo(curvas)
        m = metricas(gl.to_numpy(), gl.index)
        if m:
            cagrs.append(m["CAGR_pct"]); sharpes.append(m["sharpe"]); mdds.append(m["MDD_pct"])
        if (k + 1) % max(1, n2 // 10) == 0:
            print("   ... %d/%d rodadas · CAGR embaralhado ate agora: mediana %+.2f%%"
                  % (k + 1, n2, float(np.median(cagrs))))

    cagrs = np.array(cagrs); sharpes = np.array(sharpes); mdds = np.array(mdds)
    pct_cagr = float((cagrs < real["CAGR_pct"]).mean() * 100)
    pct_sh = float((sharpes < real["sharpe"]).mean() * 100)
    print("\n   %-26s %10s %10s %10s %12s" % ("", "p05", "mediana", "p95", "REAL"))
    print("   " + "-" * 74)
    print("   %-26s %+9.2f%% %+9.2f%% %+9.2f%% %+11.2f%%"
          % ("CAGR", np.quantile(cagrs, .05), np.median(cagrs), np.quantile(cagrs, .95),
             real["CAGR_pct"]))
    print("   %-26s %10.2f %10.2f %10.2f %12.2f"
          % ("Sharpe", np.quantile(sharpes, .05), np.median(sharpes),
             np.quantile(sharpes, .95), real["sharpe"]))
    print("   %-26s %9.1f%% %9.1f%% %9.1f%% %11.1f%%"
          % ("MDD", np.quantile(mdds, .05), np.median(mdds), np.quantile(mdds, .95),
             real["MDD_pct"]))
    print("\n   PERCENTIL DO REAL na nuvem do embaralhado: CAGR %.1f · Sharpe %.1f"
          % (pct_cagr, pct_sh))
    if pct_cagr >= 95 and pct_sh >= 95:
        print("   -> o sinal ACERTA o momento: o real esta fora da nuvem nas duas medidas.")
    elif pct_cagr >= 95 or pct_sh >= 95:
        print("   -> passa em UMA medida so. Evidencia fraca; nao aprova sozinha.")
    else:
        print("   -> o real esta DENTRO da nuvem. O que a estrategia entrega e o perfil de")
        print("      EXPOSICAO, nao a leitura de momento — embaralhar as pontuacoes da o mesmo.")

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": str(pd.Timestamp.now("UTC"))[:19] + "Z",
                   "natureza": "EXPLORACAO — nao e pre-registro",
                   "semente": SEMENTE, "n_nomes": len(dados),
                   "real_em_globo": real,
                   "MC3_comprar_e_segurar": m_bh,
                   "MC1_bootstrap_bloco": b,
                   "MC2_sinal_embaralhado": {
                       "n_sims": int(len(cagrs)),
                       "CAGR_p05": round(float(np.quantile(cagrs, .05)), 2),
                       "CAGR_mediana": round(float(np.median(cagrs)), 2),
                       "CAGR_p95": round(float(np.quantile(cagrs, .95)), 2),
                       "Sharpe_mediana": round(float(np.median(sharpes)), 3),
                       "MDD_mediana": round(float(np.median(mdds)), 2),
                       "percentil_real_CAGR": round(pct_cagr, 1),
                       "percentil_real_Sharpe": round(pct_sh, 1)}},
                  f, ensure_ascii=False, indent=1)
    print("\ngravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
