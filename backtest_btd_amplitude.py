# -*- coding: utf-8 -*-
"""backtest_btd_amplitude.py — A REGRA QUE SOBROU (08/set/2026)

O QUE OS DOIS TESTES ANTERIORES DEIXARAM DE PE
----------------------------------------------
  backtest_btd.py            o gatilho de 5% rende +5,85pp acima do dia qualquer em 60
                             pregoes, com 19 de 31 papeis acima do p95 do proprio sorteio.
  backtest_btd_concentracao  tirando covid, o aperto de 2022 e abril/2025, o excesso cai
                             para +1,77pp e sobra 1 papel de 24 acima do p95 — o acaso da
                             1,2. Fora dos crashes, o gatilho NAO se distingue de sortear
                             um dia.

E a leitura MEDO x IDIOSSINCRATICA da primeira rodada aponta para o mesmo lugar: queda com
o mercado junto rende MUITO mais que queda do papel sozinho (+35,5% contra +21,0% em 120
pregoes, no gatilho de 5%).

Os tres achados dizem a mesma coisa por caminhos diferentes: o que paga nao e a queda do
PAPEL, e a queda de TODO MUNDO AO MESMO TEMPO.

A HIPOTESE, entao
-----------------
    o retorno da compra na queda cresce com a AMPLITUDE do dia — quantos papeis do universo
    cairam junto. Comprar a queda de um papel isolado nao e a mesma operacao que comprar a
    queda no dia em que metade da tela esta vermelha, e o cartao de hoje nao distingue as
    duas.

Se isso valer, a correcao do produto e direta e barata: o cartao deixa de aparecer por
papel e passa a aparecer por DIA, com a amplitude na frente.

Controle: o sorteio pareado continua, agora por FAIXA de amplitude — cada faixa e comparada
com o mesmo numero de entradas sorteadas nos mesmos papeis. Sem isso, faixas com poucas
entradas parecem melhores so por terem menos amostra.

Uso: python backtest_btd_amplitude.py [anos]
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
SAIDA = RAIZ / "data" / "backtest_btd_amplitude.json"

US = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "V", "UNH",
      "XOM", "LLY", "COST", "MA", "HD", "ORCL", "NFLX", "AMD", "CRM"]
B3 = ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "BBAS3.SA",
      "B3SA3.SA", "RENT3.SA", "SUZB3.SA", "PRIO3.SA", "RADL3.SA"]

DIP = -0.03            # o gatilho normal do cartao — o que aparece com mais frequencia
PRAZOS = [20, 60, 120]
N_SORTEIOS = 2000
SEMENTE = 20260908
# faixas de amplitude declaradas antes de olhar: 1 papel, poucos, muitos, quase todos
FAIXAS = [(1, 1, "1 papel — queda isolada"), (2, 3, "2 a 3 papeis"),
          (4, 7, "4 a 7 papeis"), (8, 14, "8 a 14 papeis"), (15, 99, "15+ papeis")]


def main():
    anos = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    px = yf.download(US + B3, period=f"{anos}y", interval="1d",
                     auto_adjust=True, progress=False)["Close"].dropna(how="all")
    tickers = [t for t in US + B3 if t in px.columns]
    ret = px[tickers].pct_change()

    # amplitude do dia = quantos papeis do universo cairam >= 3% naquele pregao
    caiu = ret <= DIP
    amplitude = caiu.sum(axis=1)

    print(f"BTD — AMPLITUDE DO DIA · gatilho {DIP:.0%} · {len(tickers)} papeis")
    print(f"{str(px.index[0])[:10]} -> {str(px.index[-1])[:10]} · "
          f"{int(caiu.to_numpy().sum())} entradas brutas")
    print("=" * 100)

    rng = np.random.default_rng(SEMENTE)
    arr = {t: px[t].to_numpy(dtype=float) for t in tickers}
    pos = {t: {d: i for i, d in enumerate(px[t].dropna().index)} for t in tickers}
    serie = {t: px[t].dropna().to_numpy(dtype=float) for t in tickers}

    # ------------------------------------------------------- coleta por faixa e prazo
    linhas = []
    for h in PRAZOS:
        # o retorno incondicional de h pregoes, por papel — a referencia do sorteio
        inc_por_papel, fut_por_papel = {}, {}
        for t in tickers:
            s = serie[t]
            base = np.arange(len(s) - h)
            fut_por_papel[t] = s[base + h] / s[base] - 1.0
            inc_por_papel[t] = float(fut_por_papel[t].mean())

        for lo, hi, rot in FAIXAS:
            dias = amplitude[(amplitude >= lo) & (amplitude <= hi)].index
            rs, quais = [], []
            for d in dias:
                for t in tickers:
                    if not bool(caiu.at[d, t]):
                        continue
                    i = pos[t].get(d)
                    if i is None or i + h >= len(serie[t]):
                        continue
                    rs.append(serie[t][i + h] / serie[t][i] - 1.0)
                    quais.append(t)
            if len(rs) < 30:
                continue
            rs = np.array(rs)
            # sorteio PAREADO: mesma composicao de papeis, mesmo n, mesmo prazo
            cont = np.array(quais)
            medias = np.empty(N_SORTEIOS)
            for k in range(N_SORTEIOS):
                acc = 0.0
                for t in np.unique(cont):
                    n_t = int((cont == t).sum())
                    f = fut_por_papel[t]
                    acc += f[rng.integers(0, len(f), n_t)].sum()
                medias[k] = acc / len(cont)
            inc = float(np.mean([inc_por_papel[t] for t in cont]))
            pct = float((medias < rs.mean()).mean() * 100)
            linhas.append({
                "prazo_pregoes": h, "faixa": rot, "faixa_lo": lo, "faixa_hi": hi,
                "n_dias": int(len(dias)), "n_entradas": int(len(rs)),
                "media_gatilho_pct": round(float(rs.mean()) * 100, 2),
                "media_incondicional_pct": round(inc * 100, 2),
                "excesso_pp": round(float(rs.mean() - inc) * 100, 2),
                "percentil_vs_sorteio": round(pct, 1),
                "acerto_pct": round(float((rs > 0).mean()) * 100, 1),
            })

    df = pd.DataFrame(linhas)
    for h in PRAZOS:
        g = df[df.prazo_pregoes == h]
        if g.empty:
            continue
        print(f"\nSAIDA EM {h} PREGOES\n")
        print(f"   {'faixa de amplitude':<26} {'dias':>6} {'entradas':>9} {'gatilho':>9} "
              f"{'qualquer':>9} {'excesso':>9} {'percentil':>10} {'acerto':>8}")
        print("   " + "-" * 92)
        for _, r in g.iterrows():
            marca = "  <<<" if r.percentil_vs_sorteio >= 95 else ""
            print(f"   {r.faixa:<26} {r.n_dias:>6} {r.n_entradas:>9} "
                  f"{r.media_gatilho_pct:>8.2f}% {r.media_incondicional_pct:>8.2f}% "
                  f"{r.excesso_pp:>+8.2f} {r.percentil_vs_sorteio:>9.1f} "
                  f"{r.acerto_pct:>7.1f}%{marca}")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": str(pd.Timestamp.now("UTC"))[:19] + "Z",
                   "natureza": "EXPLORACAO — nao e pre-registro",
                   "gatilho": DIP, "anos": anos, "semente": SEMENTE,
                   "n_sorteios": N_SORTEIOS, "faixas": [list(x) for x in FAIXAS],
                   "limites_declarados": [
                       "universo com sobrevivencia; ela se cancela contra o sorteio pareado",
                       "janelas sobrepostas: o n efetivo e menor que o nominal, os percentis sao otimistas",
                       "6 faixas x 3 prazos = 18 comparacoes; um p95 solto e esperado por acaso",
                       "custo de execucao nao entra",
                   ],
                   "linhas": linhas}, f, ensure_ascii=False, indent=1)
    print(f"\ngravado: {SAIDA}")


if __name__ == "__main__":
    main()
