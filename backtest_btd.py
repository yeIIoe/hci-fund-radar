# -*- coding: utf-8 -*-
"""backtest_btd.py — O GATILHO DO BTD VALE ALGUMA COISA? (08/set/2026)

PERGUNTA DO EDUARDO, literal: "por que nao rodamos um backtest do DEEPVALUE e do BTD,
quero saber o retorno dele e se podemos confiar nos cards que ele da".

O QUE DA PARA TESTAR, E O QUE NAO DA
------------------------------------
O `btd_hold_scan.py` tem tres partes e elas NAO tem a mesma testabilidade:

  1. UNIVERSO   20 mega caps americanas + 12 blue chips da B3 + 3 ETFs, escritos a mao.
                Escolhidos porque sao grandes HOJE. Sobrevivencia por construcao.
  2. QUALIDADE  ROE >= 15%, D/E <= 150%, P/E <= 45 — vem de `yf.Ticker().info`, que devolve
                SO o valor de hoje. Nao existe o ROE que a empresa tinha em 2018 nessa
                chamada. Esta peneira NAO e testavel com o dado que temos.
  3. GATILHO    queda de 3% (ou 5%) no dia. E PRECO. Isto e testavel em qualquer data.

Entao este arquivo testa a PARTE 3, que e a unica honesta — e a mais importante, porque e
ela que decide QUANDO o cartao aparece na tela.

POR QUE O CONTROLE ALEATORIO E O CORACAO DISTO
-----------------------------------------------
Medir "comprei a queda da NVDA e ganhei 12% em 60 dias" nao prova nada: a NVDA subiu quase
todo mes da amostra. Qualquer dia de compra teria ganhado. E a sobrevivencia do universo
piora isso — a lista so tem quem deu certo.

A sobrevivencia se cancela quando as DUAS pernas a carregam. Entao a pergunta vira:

    comprar NA QUEDA bate comprar em um dia QUALQUER do mesmo papel, no mesmo periodo?

O controle e o sorteio PAREADO (lei da casa, escrita depois do AEGH): para cada papel,
sorteia-se o MESMO numero de entradas que o gatilho deu, no mesmo historico, com o mesmo
prazo de saida, 2.000 vezes. O gatilho so vale se ficar fora da nuvem do sorteio.

Isto NAO e um pre-registro: e exploracao declarada como tal, para responder a pergunta.
Se der positivo, o proximo passo e um PREREG em janela separada.

Uso:  python backtest_btd.py            (10 anos, prazos 5/20/60/120)
      python backtest_btd.py 5          (5 anos)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import yfinance as yf

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "data" / "backtest_btd.json"

# O universo EXATO do btd_hold_scan.py. Nao aumentar nem "melhorar": o que se mede aqui e
# o cartao que o site mostra, nao uma estrategia idealizada.
US = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "V", "UNH",
      "XOM", "LLY", "COST", "MA", "HD", "ORCL", "NFLX", "AMD", "CRM"]
B3 = ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "BBAS3.SA",
      "B3SA3.SA", "RENT3.SA", "SUZB3.SA", "PRIO3.SA", "RADL3.SA"]
REF = {"US": "SPY", "B3": "BOVA11.SA"}     # a referencia que separa MEDO de IDIOSSINCRATICA

DIP1, DIP2 = -0.03, -0.05                  # os mesmos gatilhos do scanner
PRAZOS = [5, 20, 60, 120]                  # pregoes ate a saida
N_SORTEIOS = 2000
SEMENTE = 20260908                         # declarada, para a rodada ser reproduzivel


def baixa(tickers, anos):
    px = yf.download(tickers, period=f"{anos}y", interval="1d",
                     auto_adjust=True, progress=False)["Close"]
    if isinstance(px, pd.Series):
        px = px.to_frame()
    return px.dropna(how="all")


def frente(serie: np.ndarray, idx: np.ndarray, h: int) -> np.ndarray:
    """Retorno de `h` pregoes a frente, entrando no FECHAMENTO do dia idx.
    Entradas sem h pregoes a frente sao descartadas — nunca extrapoladas."""
    fim = idx + h
    ok = fim < len(serie)
    idx, fim = idx[ok], fim[ok]
    if not len(idx):
        return np.array([])
    return serie[fim] / serie[idx] - 1.0


def sorteio_pareado(serie: np.ndarray, n: int, h: int, rng) -> np.ndarray:
    """n entradas aleatorias no MESMO papel, MESMO prazo. Devolve a media de cada rodada."""
    validos = np.arange(len(serie) - h)
    if len(validos) < n or n == 0:
        return np.array([])
    fut = serie[validos + h] / serie[validos] - 1.0
    # amostragem sem reposicao dentro de cada rodada, como o gatilho (que nao repete dia)
    medias = np.empty(N_SORTEIOS)
    for i in range(N_SORTEIOS):
        medias[i] = fut[rng.choice(len(validos), size=n, replace=False)].mean()
    return medias


def main():
    anos = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"BTD — teste do GATILHO, {anos} anos, sorteio pareado com {N_SORTEIOS} rodadas")
    print("=" * 92)

    todos = US + B3 + list(REF.values())
    px = baixa(todos, anos)
    print(f"baixados {px.shape[1]} papeis · {px.shape[0]} pregoes · "
          f"{str(px.index[0])[:10]} -> {str(px.index[-1])[:10]}\n")

    rng = np.random.default_rng(SEMENTE)
    linhas = []

    for tk in US + B3:
        if tk not in px.columns:
            continue
        mercado = REF["B3"] if tk.endswith(".SA") else REF["US"]
        if mercado not in px.columns:
            continue
        par = px[[tk, mercado]].dropna()
        if len(par) < 400:
            continue
        s = par[tk].to_numpy(dtype=float)
        m = par[mercado].to_numpy(dtype=float)
        rs = np.concatenate([[np.nan], s[1:] / s[:-1] - 1.0])
        rm = np.concatenate([[np.nan], m[1:] / m[:-1] - 1.0])

        for rot, corte in (("dip 3%", DIP1), ("dip 5%", DIP2)):
            gat = np.where(rs <= corte)[0]
            if len(gat) < 15:                      # n minimo declarado
                continue
            # a separacao que o proprio cartao faz
            medo = gat[rm[gat] <= corte / 2]       # o mercado tambem caiu
            idio = gat[rm[gat] > 0]                # o papel caiu com o mercado SUBINDO

            for h in PRAZOS:
                r_gat = frente(s, gat, h)
                if len(r_gat) < 15:
                    continue
                # controle 1: o retorno INCONDICIONAL de h pregoes no mesmo papel
                base = np.arange(len(s) - h)
                r_inc = s[base + h] / s[base] - 1.0
                # controle 2: sorteio pareado, mesmo n
                nuvem = sorteio_pareado(s, len(r_gat), h, rng)
                pct = float((nuvem < r_gat.mean()).mean() * 100) if len(nuvem) else float("nan")

                linhas.append({
                    "ticker": tk, "gatilho": rot, "prazo_pregoes": h,
                    "n_entradas": int(len(r_gat)),
                    "media_gatilho_pct": round(float(r_gat.mean()) * 100, 2),
                    "media_incondicional_pct": round(float(r_inc.mean()) * 100, 2),
                    "excesso_pp": round(float(r_gat.mean() - r_inc.mean()) * 100, 2),
                    "percentil_vs_sorteio": round(pct, 1),
                    "acerto_gatilho_pct": round(float((r_gat > 0).mean()) * 100, 1),
                    "acerto_incondicional_pct": round(float((r_inc > 0).mean()) * 100, 1),
                    "n_medo": int(len(medo)), "n_idiossincratica": int(len(idio)),
                    "media_medo_pct": round(float(frente(s, medo, h).mean()) * 100, 2)
                        if len(frente(s, medo, h)) >= 10 else None,
                    "media_idio_pct": round(float(frente(s, idio, h).mean()) * 100, 2)
                        if len(frente(s, idio, h)) >= 10 else None,
                })

    df = pd.DataFrame(linhas)
    if df.empty:
        print("nenhum papel produziu n suficiente — nada a concluir.")
        return

    # ------------------------------------------------------------------ o veredito
    print("AGREGADO — a pergunta que interessa: o gatilho bate o dia qualquer?\n")
    print(f"{'gatilho':9} {'prazo':>6} {'papeis':>7} {'entradas':>9} "
          f"{'gatilho':>9} {'qualquer':>9} {'excesso':>9} {'p50 sorteio':>12} {'acima de p95':>13}")
    print("-" * 92)
    resumo = []
    for rot in ("dip 3%", "dip 5%"):
        for h in PRAZOS:
            g = df[(df.gatilho == rot) & (df.prazo_pregoes == h)]
            if g.empty:
                continue
            acima = int((g.percentil_vs_sorteio >= 95).sum())
            r = {
                "gatilho": rot, "prazo": h, "papeis": int(len(g)),
                "entradas": int(g.n_entradas.sum()),
                "media_gatilho_pct": round(float(g.media_gatilho_pct.mean()), 2),
                "media_incondicional_pct": round(float(g.media_incondicional_pct.mean()), 2),
                "excesso_pp": round(float(g.excesso_pp.mean()), 2),
                "percentil_mediano": round(float(g.percentil_vs_sorteio.median()), 1),
                "papeis_acima_p95": acima,
                "papeis_acima_p95_esperado_por_acaso": round(len(g) * 0.05, 1),
            }
            resumo.append(r)
            print(f"{rot:9} {h:>6} {len(g):>7} {int(g.n_entradas.sum()):>9} "
                  f"{r['media_gatilho_pct']:>8.2f}% {r['media_incondicional_pct']:>8.2f}% "
                  f"{r['excesso_pp']:>+8.2f} {r['percentil_mediano']:>11.1f} "
                  f"{acima:>6} de {len(g):<4}")

    print("\nMEDO x IDIOSSINCRATICA — a separacao que o cartao afirma fazer\n")
    print(f"{'gatilho':9} {'prazo':>6} {'n medo':>8} {'medo':>9} "
          f"{'n idio':>8} {'idio':>9} {'diferenca':>11}")
    print("-" * 92)
    for rot in ("dip 3%", "dip 5%"):
        for h in PRAZOS:
            g = df[(df.gatilho == rot) & (df.prazo_pregoes == h)]
            gm = g.dropna(subset=["media_medo_pct"])
            gi = g.dropna(subset=["media_idio_pct"])
            if gm.empty or gi.empty:
                continue
            dm, di = float(gm.media_medo_pct.mean()), float(gi.media_idio_pct.mean())
            print(f"{rot:9} {h:>6} {int(gm.n_medo.sum()):>8} {dm:>8.2f}% "
                  f"{int(gi.n_idiossincratica.sum()):>8} {di:>8.2f}% {di - dm:>+10.2f}pp")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({
            "gerado_em": str(pd.Timestamp.utcnow())[:19] + "Z",
            "natureza": "EXPLORACAO — nao e pre-registro",
            "anos": anos, "semente": SEMENTE, "n_sorteios": N_SORTEIOS,
            "universo": {"US": US, "B3": B3, "referencia": REF},
            "limites_declarados": [
                "universo escrito a mao com nomes grandes HOJE — sobrevivencia por construcao",
                "a peneira de qualidade (ROE, D/E, P/E) NAO foi testada: yfinance so devolve o valor de hoje",
                "a sobrevivencia se cancela na comparacao contra o sorteio pareado, que roda no MESMO papel",
                "custo de corretagem e spread nao entram; o efeito seria contra o gatilho",
            ],
            "resumo": resumo,
            "por_papel": linhas,
        }, f, ensure_ascii=False, indent=1)
    print(f"\ngravado: {SAIDA}")


if __name__ == "__main__":
    main()
