# -*- coding: utf-8 -*-
"""backtest_momentum.py — MOMENTUM DE QUATRO HORIZONTES, fiel a especificacao (08/set/2026)

Implementa `estrategia_momentum_backtest.pdf` sobre as 123 acoes de data/empresas.json.

O QUE A SPEC MANDA, E QUE ESTE ARQUIVO SEGUE LINHA A LINHA
-----------------------------------------------------------
  pontuacao   St = soma de sign(Ct/Ct-h - 1) para h em {5, 10, 21, 42}, no FECHAMENTO da
              ultima sessao da semana. Valores tipicos -4, -2, 0, +2, +4.
  volatilidade sigma = desvio-padrao AMOSTRAL de 30 retornos diarios x raiz(252)
  exposicao   Emax = V x min(1, 0,10/sigma) · Ealvo = (|St|/4) x Emax
              V e o patrimonio marcado a mercado NO FECHAMENTO que gerou o sinal, e Ealvo
              fica CONGELADO ate a execucao na abertura seguinte.
  execucao    sempre na ABERTURA da sessao seguinte
  1a entrada  Q = piso(Ealvo / Pexec)
  adicao      exige posicao, mesma direcao, |St| > |St-1 semanal| E Ealvo > Eexistente,
              com Eexistente medido a PRECO ATUAL (nao ao preco de entrada)
  reducao     em QUALQUER avaliacao, se Eexistente > Ealvo, corta o excedente
              (inclusive quando quem mudou foi a volatilidade, nao a pontuacao)
  zero        pontuacao 0 encerra tudo; pontuacao contraria encerra e abre invertido
  stop        SL = Pultima_entrada x (1 -+ d), d = 5%. Vale para a posicao INTEIRA, substitui
              o anterior, e NAO usa preco medio. Reducao NAO mexe na referencia do stop.
              Sem trava para a distancia aumentar.
  stop no dia comprado: abertura <= stop -> executa na ABERTURA; senao minima <= stop ->
              executa NO STOP. Vendido, espelhado. Slippage adverso nos dois.
              Stop tem PRIORIDADE sobre ordem semanal pendente, e a cancela.
              Entrada na abertura ja deixa o stop novo valendo para o resto da sessao.
              Depois de um stop, so entra na abertura POSTERIOR a proxima avaliacao semanal.

DUAS DECISOES QUE A SPEC NAO FIXA, DECLARADAS AQUI
--------------------------------------------------
  1. A spec e de UM ativo ("Limite de exposicao: 100% do patrimonio"). Rodar 123 nomes cada
     um a 100% do patrimonio seria 123x de alavancagem. Entao cada nome roda em conta
     PROPRIA e independente, e o resultado "em globo" e a carteira de peso igual dessas
     123 curvas — 1/123 do capital em cada. E a unica leitura honesta da spec como escrita.
  2. Custos: a spec manda cobrar, sem dizer quanto. Adotado e declarado:
     slippage 5 pontos-base ADVERSOS em toda execucao, corretagem 1 pb por perna, aluguel
     de 3% ao ano sobre o valor vendido. Roda tambem uma variante SEM custo, para o custo
     aparecer como numero e nao como suposicao.

Uso: python backtest_momentum.py [anos]        (padrao 10)
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
import yfinance as yf

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "data" / "backtest_momentum.json"
CACHE = RAIZ / "data" / "core" / "cache_momentum.pkl"

HORIZONTES = (5, 10, 21, 42)
JANELA_VOL = 30
VOL_ALVO = 0.10
A_ANO = 252
L_MAX = 1.0
DIST_STOP = 0.05
LOTE = 1.0
CAPITAL = 100_000.0        # por nome; grande o bastante para o piso de lote ser irrelevante

SLIPPAGE = 0.0005          # 5 pb adversos por execucao
CORRETAGEM = 0.0001        # 1 pb por perna
ALUGUEL_ANO = 0.03         # sobre o valor vendido, por dia util

MIN_BARRAS = 300           # nome com menos historico que isto nao entra, e e declarado


# --------------------------------------------------------------------------- dados
def universo():
    d = json.load(io.open(RAIZ / "data" / "empresas.json", encoding="utf-8"))
    return sorted(d["empresas"].keys())


def baixa(tickers, anos):
    if CACHE.exists():
        try:
            g = pd.read_pickle(CACHE)
            if g.attrs.get("anos") == anos and set(g.attrs.get("tickers", [])) == set(tickers):
                print("cache de precos reaproveitado: %s" % CACHE.name)
                return g
        except Exception:
            pass
    g = yf.download(tickers, period=f"{anos}y", interval="1d",
                    auto_adjust=True, progress=False, group_by="ticker")
    g.attrs["anos"] = anos
    g.attrs["tickers"] = list(tickers)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    g.to_pickle(CACHE)
    return g


def serie(g, tk):
    try:
        d = g[tk][["Open", "High", "Low", "Close"]].dropna()
    except Exception:
        return None
    return d if len(d) >= MIN_BARRAS else None


# --------------------------------------------------------------------------- motor
def roda(d: pd.DataFrame, com_custo=True, scores_forcados=None):
    """Devolve (curva de patrimonio diaria, lista de execucoes, serie de pontuacoes).

    `scores_forcados` troca a pontuacao real por outra sequencia — e o que permite o
    Monte Carlo de sinal embaralhado sem tocar em mais nada do motor.
    """
    o = d["Open"].to_numpy(float); h = d["High"].to_numpy(float)
    lo = d["Low"].to_numpy(float); c = d["Close"].to_numpy(float)
    idx = d.index
    n = len(d)

    ret = np.concatenate([[np.nan], c[1:] / c[:-1] - 1.0])
    sig = pd.Series(ret).rolling(JANELA_VOL).std(ddof=1).to_numpy() * np.sqrt(A_ANO)

    # ultima sessao de cada semana ISO
    sem = pd.Series(idx).dt.isocalendar()
    chave = (sem.year.astype(str) + "-" + sem.week.astype(str)).to_numpy()
    fim_semana = np.array([i == n - 1 or chave[i] != chave[i + 1] for i in range(n)])

    caixa = CAPITAL
    q = 0.0                 # quantidade com sinal (+ comprado, - vendido)
    stop = None
    pend = None             # {"Ealvo","dir","pode_add"}
    s_ant = 0               # pontuacao da avaliacao semanal anterior
    execs = []
    curva = np.full(n, np.nan)
    scores = np.full(n, np.nan)

    slp = SLIPPAGE if com_custo else 0.0
    cor = CORRETAGEM if com_custo else 0.0
    alu = ALUGUEL_ANO if com_custo else 0.0

    def negocia(i, dq, preco_base, motivo):
        """dq > 0 compra, dq < 0 vende. Preco com slippage ADVERSO e corretagem."""
        nonlocal caixa, q
        if dq == 0:
            return None
        p = preco_base * (1 + slp) if dq > 0 else preco_base * (1 - slp)
        caixa -= dq * p
        caixa -= abs(dq) * p * cor
        q += dq
        execs.append({"data": str(idx[i])[:10], "motivo": motivo, "dq": float(dq),
                      "preco": float(p), "q_depois": float(q)})
        return p

    inicio = max(max(HORIZONTES), JANELA_VOL) + 1
    for i in range(inicio, n):
        # ---------------------------------------------------------- 1. ABERTURA
        parou = False
        if q != 0 and stop is not None:
            if (q > 0 and o[i] <= stop) or (q < 0 and o[i] >= stop):
                negocia(i, -q, o[i], "stop na abertura")
                stop = None
                pend = None            # o stop tem PRIORIDADE e cancela a ordem semanal
                parou = True

        if pend is not None and not parou:
            P = o[i]
            direc = pend["dir"]
            if direc == 0:                                   # pontuacao zero: encerra tudo
                if q != 0:
                    negocia(i, -q, P, "pontuacao zero")
                    stop = None
            elif q != 0 and np.sign(q) != direc:             # inversao
                negocia(i, -q, P, "inversao: encerra")
                stop = None
                qa = np.floor(pend["Ealvo"] / P / LOTE) * LOTE
                if qa > 0:
                    p = negocia(i, direc * qa, P, "inversao: abre")
                    stop = p * (1 - DIST_STOP) if direc > 0 else p * (1 + DIST_STOP)
            elif q == 0:                                     # primeira entrada
                qa = np.floor(pend["Ealvo"] / P / LOTE) * LOTE
                if qa > 0:
                    p = negocia(i, direc * qa, P, "primeira entrada")
                    stop = p * (1 - DIST_STOP) if direc > 0 else p * (1 + DIST_STOP)
            else:                                            # mesma direcao
                e_exist = abs(q) * P
                if pend["pode_add"] and pend["Ealvo"] > e_exist:
                    q_add = np.floor(max(0.0, pend["Ealvo"] - e_exist) / P / LOTE) * LOTE
                    if q_add > 0:
                        p = negocia(i, direc * q_add, P, "adicao")
                        stop = p * (1 - DIST_STOP) if direc > 0 else p * (1 + DIST_STOP)
                elif e_exist > pend["Ealvo"]:
                    alvo_q = np.floor(pend["Ealvo"] / P / LOTE) * LOTE
                    q_red = max(0.0, abs(q) - alvo_q)
                    if q_red > 0:
                        negocia(i, -direc * q_red, P, "reducao")
                        if abs(q) < 1e-12:
                            stop = None
                        # reducao NAO altera a referencia do stop
            pend = None

        # ---------------------------------------------------------- 2. INTRADIA
        if q != 0 and stop is not None and not parou:
            if (q > 0 and lo[i] <= stop) or (q < 0 and h[i] >= stop):
                negocia(i, -q, stop, "stop intradia")
                stop = None

        # ---------------------------------------------------------- 3. MARCACAO
        if q < 0 and alu:
            caixa -= abs(q) * c[i] * alu / A_ANO
        patr = caixa + q * c[i]
        curva[i] = patr

        # ---------------------------------------------------------- 4. AVALIACAO SEMANAL
        if fim_semana[i]:
            if scores_forcados is not None:
                s = int(scores_forcados[i])
            else:
                s = int(sum(np.sign(c[i] / c[i - hh] - 1.0) for hh in HORIZONTES))
            scores[i] = s
            sg = sig[i]
            if not np.isnan(sg) and sg > 0 and patr > 0:
                emax = patr * min(L_MAX, VOL_ALVO / sg)
                ealvo = (abs(s) / 4.0) * emax
                pend = {"Ealvo": ealvo, "dir": int(np.sign(s)),
                        "pode_add": (s * s_ant > 0 and abs(s) > abs(s_ant))}
            else:
                pend = None
            s_ant = s

    return curva, execs, scores


# --------------------------------------------------------------------------- metricas
def metricas(curva, idx):
    v = pd.Series(curva, index=idx).dropna()
    if len(v) < 60:
        return None
    r = v.pct_change().dropna()
    anos = (v.index[-1] - v.index[0]).days / 365.25
    cagr = (v.iloc[-1] / v.iloc[0]) ** (1 / anos) - 1 if anos > 0 and v.iloc[0] > 0 else np.nan
    dd = (v / v.cummax() - 1).min()
    vol = r.std(ddof=1) * np.sqrt(A_ANO)
    sharpe = (r.mean() * A_ANO) / vol if vol > 0 else np.nan
    return {"inicio": str(v.index[0])[:10], "fim": str(v.index[-1])[:10], "anos": round(anos, 2),
            "final": round(float(v.iloc[-1]), 2),
            "retorno_total_pct": round(float(v.iloc[-1] / v.iloc[0] - 1) * 100, 2),
            "CAGR_pct": round(float(cagr) * 100, 2), "MDD_pct": round(float(dd) * 100, 2),
            "vol_anual_pct": round(float(vol) * 100, 2), "sharpe": round(float(sharpe), 3),
            "n_dias": int(len(v))}


def main():
    anos = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    tks = universo()
    print("MOMENTUM DE QUATRO HORIZONTES — backtest fiel a especificacao")
    print("=" * 100)
    print("universo: %d acoes de data/empresas.json · %d anos · capital %s por nome"
          % (len(tks), anos, f"US$ {CAPITAL:,.0f}"))
    print("custos: slippage %.0f pb · corretagem %.0f pb/perna · aluguel %.1f%%/ano"
          % (SLIPPAGE * 1e4, CORRETAGEM * 1e4, ALUGUEL_ANO * 100))
    g = baixa(tks, anos)

    curvas, linhas, curtos, execs_tot = {}, [], [], 0
    curvas_sc = {}
    for tk in tks:
        d = serie(g, tk)
        if d is None:
            curtos.append(tk)
            continue
        cv, ex, sc = roda(d, com_custo=True)
        m = metricas(cv, d.index)
        if m is None:
            curtos.append(tk); continue
        cv0, _, _ = roda(d, com_custo=False)
        m0 = metricas(cv0, d.index)
        curvas[tk] = pd.Series(cv, index=d.index).dropna()
        curvas_sc[tk] = pd.Series(cv0, index=d.index).dropna()
        execs_tot += len(ex)
        linhas.append({"ticker": tk, **m, "n_execucoes": len(ex),
                       "CAGR_sem_custo_pct": m0["CAGR_pct"] if m0 else None})

    print("\nrodaram %d nomes · %d descartados por historico curto (< %d barras)"
          % (len(linhas), len(curtos), MIN_BARRAS))
    if curtos:
        print("descartados: %s" % ", ".join(curtos))
    print("execucoes totais: %d\n" % execs_tot)

    df = pd.DataFrame(linhas).sort_values("CAGR_pct", ascending=False)

    # ------------------------------------------------------------------ EM GLOBO
    # 🔴 DEFEITO CORRIGIDO EM 08/set, antes de reportar.
    # A 1a versao fazia a media das CURVAS NORMALIZADAS. Como cada nome comeca numa data
    # diferente, o nome novo entra valendo 1,0 enquanto os antigos estao em 1,5 — e a media
    # cai num DEGRAU que nao existiu em carteira nenhuma. Isso inventava volatilidade: deu
    # 47% ao ano num conjunto cujo alvo e 10%.
    # A carteira de peso igual correta e a media dos RETORNOS DIARIOS dos nomes vivos
    # naquele dia, composta depois. Nome que nasce entra com retorno, nao com nivel.
    def em_globo(cs):
        R = pd.DataFrame({k: v.pct_change() for k, v in cs.items()})
        r = R.mean(axis=1, skipna=True).dropna()
        return (1 + r).cumprod() * CAPITAL

    glob = em_globo(curvas)
    glob0 = em_globo(curvas_sc)
    vivos = pd.DataFrame({k: v.notna() for k, v in curvas.items()}).sum(axis=1)
    print("")
    print("nomes vivos na carteira: %d no inicio -> %d no fim (mediana %d)"
          % (int(vivos.iloc[0]), int(vivos.iloc[-1]), int(vivos.median())))
    mg = metricas(glob.to_numpy(), glob.index)
    mg0 = metricas(glob0.to_numpy(), glob0.index)

    print("=" * 100)
    print("RESULTADO EM GLOBO — carteira de peso igual, 1/%d em cada nome" % len(curvas))
    print("=" * 100)
    for rot, mm in (("COM custo", mg), ("sem custo", mg0)):
        print("  %-10s %s a %s (%.1f anos) · final US$ %s · retorno %+.1f%% · CAGR %+.2f%% · "
              "MDD %.1f%% · vol %.1f%% · Sharpe %.2f"
              % (rot, mm["inicio"], mm["fim"], mm["anos"], f"{mm['final']:,.0f}",
                 mm["retorno_total_pct"], mm["CAGR_pct"], mm["MDD_pct"],
                 mm["vol_anual_pct"], mm["sharpe"]))
    print("  custo comeu %.2f pp de CAGR ao ano" % (mg0["CAGR_pct"] - mg["CAGR_pct"]))

    ganh = int((df.CAGR_pct > 0).sum())
    print("\n  nomes com CAGR positivo: %d de %d (%.0f%%)" % (ganh, len(df), 100 * ganh / len(df)))
    print("  CAGR por nome: mediana %+.2f%% · quartis %+.2f%% / %+.2f%%"
          % (df.CAGR_pct.median(), df.CAGR_pct.quantile(.25), df.CAGR_pct.quantile(.75)))

    print("\n  5 melhores: %s" % " · ".join(
        f"{r.ticker} {r.CAGR_pct:+.1f}%" for r in df.head(5).itertuples()))
    print("  5 piores  : %s" % " · ".join(
        f"{r.ticker} {r.CAGR_pct:+.1f}%" for r in df.tail(5).itertuples()))

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": str(pd.Timestamp.now("UTC"))[:19] + "Z",
                   "natureza": "BACKTEST — exploracao, nao e pre-registro",
                   "spec": "estrategia_momentum_backtest.pdf",
                   "parametros": {"horizontes": list(HORIZONTES), "janela_vol": JANELA_VOL,
                                  "vol_alvo": VOL_ALVO, "L_max": L_MAX, "dist_stop": DIST_STOP,
                                  "capital_por_nome": CAPITAL, "lote": LOTE},
                   "custos": {"slippage_pb": SLIPPAGE * 1e4, "corretagem_pb": CORRETAGEM * 1e4,
                              "aluguel_ano_pct": ALUGUEL_ANO * 100},
                   "decisoes_declaradas": [
                       "a spec e de UM ativo; cada nome roda em conta propria e o global e a "
                       "carteira de peso igual dessas contas (1/N), nao 100% em cada",
                       "custos adotados por nao virem na spec; roda tambem variante sem custo",
                       "historico do yfinance com auto_adjust (split e dividendo consistentes)",
                   ],
                   "universo": {"pedidos": len(tks), "rodaram": len(linhas),
                                "descartados_historico_curto": curtos},
                   "em_globo": {"com_custo": mg, "sem_custo": mg0},
                   "por_nome": df.to_dict("records")},
                  f, ensure_ascii=False, indent=1)
    pd.to_pickle({"curvas": curvas, "glob": glob}, RAIZ / "data" / "core" / "momentum_curvas.pkl")
    print("\ngravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
