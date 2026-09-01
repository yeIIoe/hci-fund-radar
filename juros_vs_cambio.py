# -*- coding: utf-8 -*-
"""JUROS x CAMBIO — o painel especificado pelo Eduardo em 31/ago (v1.1).

Separa sempre tres coisas: OBSERVACAO, INTERPRETACAO e EXPECTATIVA FUTURA.

REGRAS QUE ESTE CODIGO NAO PODE VIOLAR
1. Sincronizacao ANTES de classificar. Mesmo numero de sessoes NAO e o mesmo intervalo.
   Quando os periodos nao batem, o estado cambial e "nao avaliavel", e o par sai da
   contagem agregada.
2. As DUAS pernas antes do diferencial. Alta isolada de um yield nao determina a direcao
   do diferencial.
3. Relevancia medida contra a HISTORIA DO PROPRIO DIFERENCIAL, com informacao anterior a
   leitura. Nunca limite universal em pontos-base.
4. Trajetoria separada do saldo: uma alta concentrada num dia nao e recuperacao sustentada.
5. Estado do diferencial NAO se transfere para o cambio.
"""
from __future__ import annotations
import glob, json, os, sys
from datetime import datetime
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "data")
SAIDA = os.path.join(D, "juros_vs_cambio.json")

H_CURTO, H_LONGO = 5, 20          # janelas propostas, nao parametros comprovados
JAN_HIST = 252                    # escala historica, so com informacao anterior
Q_RELEVANTE = 0.70                # acima deste quantil da |variacao| historica = relevante
Q_TRANSICAO = 0.60                # entre 0,60 e 0,70 = transicao / baixa definicao
CONC = 0.60                       # >60% do movimento num unico dia = concentrado

# CONGELADO em 31/ago/2026, com os quantis MEDIDOS em 28 pares x 24 anos e aprovados
# pelo Eduardo. Sao CONVENCAO documentada, nao verdade descoberta.
#
# ⚠️ POR QUE NAO USAR A RAZAO amplitude/|saldo|: ela explode quando o saldo vai a zero.
# Medido: p50=2,6 · p90=13,3 · p99=98 · maximo=3.973. Um corte em 3 pegaria 44,5% dos
# casos, e uma oscilacao de 1 bp com saldo de 0,3 bp daria razao 3,3. A razao fica como
# INFORMACAO exibida, nunca como criterio.
Q_AMPLITUDE = 0.70        # amplitude interna acima do p70 da propria historia = relevante
Q_SALDO = 0.50            # |saldo| abaixo do p50 da propria historia = pequeno


# ------------------------------------------------------------------ series
def serie_yields():
    """yield_2y por moeda por dia, do calendario (a serie que o painel ja guarda)."""
    L = []
    for fn in sorted(glob.glob(os.path.join(D, "calendar", "calendar_*.json"))):
        for d in json.load(open(fn, encoding="utf-8")).get("days", []):
            cs = d.get("currencies") or []
            if not cs:
                continue
            r = {c["currency"]: c.get("yield_2y") for c in cs}
            r["date"] = d["date"]
            L.append(r)
    Y = pd.DataFrame(L)
    Y["date"] = pd.to_datetime(Y.date)
    return Y.set_index("date").sort_index()


def serie_fx():
    """Carrega as series de cambio do BCE, conferindo a moeda DENTRO do arquivo.

    31-ago-2026: fx_ecb_usdeur.csv continha a serie da LIBRA (chave interna
    EXR.D.GBP.EUR.SP00.A). Como o carregador tirava a moeda do NOME do arquivo, dado da
    libra entrava rotulado como dolar e os cinco pares com USD do painel — EURUSD, USDJPY,
    USDCAD, GBPUSD, NZDUSD — sairam errados sem nenhum aviso. O GBPUSD dava exatamente
    1.00000, e nem isso disparou alarme.

    A defesa: o BCE grava a moeda na coluna CURRENCY. Conferimos contra o nome e
    ESTOURAMOS se divergir. Melhor o painel falhar do que publicar numero trocado.
    """
    T = {}
    for fn in glob.glob(os.path.join(D, "raw", "fx_ecb_*.csv")):
        m = os.path.basename(fn)[7:10].upper()
        d = pd.read_csv(fn, usecols=["TIME_PERIOD", "OBS_VALUE", "CURRENCY"])
        d = d.dropna(subset=["OBS_VALUE"])
        dentro = str(d.CURRENCY.iloc[-1]).strip().upper() if len(d) else ""
        if dentro and dentro != m:
            raise RuntimeError(
                "arquivo de cambio trocado: %s tem o nome de %s mas contem a serie de %s. "
                "Rebaixe o arquivo certo antes de rodar o painel."
                % (os.path.basename(fn), m, dentro)
            )
        d["TIME_PERIOD"] = pd.to_datetime(d.TIME_PERIOD, errors="coerce")
        d = d.dropna(subset=["TIME_PERIOD"]).set_index("TIME_PERIOD")
        d = d.OBS_VALUE.astype(float).sort_index()
        T[m] = d[d > 0]
    idx = sorted(set().union(*[set(v.index) for v in T.values()]))
    T["EUR"] = pd.Series(1.0, index=pd.DatetimeIndex(idx))
    return T


def preco(par, T):
    b, q = par[:3], par[3:]
    if b not in T or q not in T:
        return None
    idx = sorted(set(T[b].index) | set(T[q].index))
    pb = T[b].reindex(idx).ffill(limit=5)
    pq = T[q].reindex(idx).ffill(limit=5)
    return (pq / pb).dropna()


# ------------------------------------------------------- relevancia e trajetoria
def relevancia(delta, historico):
    """Relevante contra a propria historia, nao contra um limite universal em bp."""
    h = np.abs(historico.dropna().values)
    if len(h) < 60:
        return "indefinida", None
    q70, q60 = np.quantile(h, Q_RELEVANTE), np.quantile(h, Q_TRANSICAO)
    a = abs(delta)
    if a >= q70:
        return "relevante", round(float(q70), 2)
    if a >= q60:
        return "transicao", round(float(q70), 2)
    return "pequena", round(float(q70), 2)


def trajetoria(passos, hist_amp=None, hist_saldo=None):
    """DESCREVE o caminho, sem julgar tamanho.

    Correcao do Eduardo, 31/ago: o limiar de relevancia decide a MAGNITUDE, nao se o
    movimento existiu. Uma recuperacao seguida de recuo e um fato observado, mesmo que o
    saldo fique abaixo do limiar — e some se as duas coisas virarem um rotulo so.

    Devolve tambem a AMPLITUDE INTERNA: saldo pequeno com muita oscilacao NAO e
    estabilidade. Um diferencial que sobe, cai e volta ao ponto de partida oscilou.
    """
    p = np.asarray([x for x in passos if x == x], dtype=float)
    if len(p) < 3:
        return {"forma": "indefinida", "descricao": None, "amplitude_bp": None, "razao": None}
    total = float(p.sum())
    # ⚠️ CORRECAO DE BUG, 31/ago — o Eduardo pegou fazendo a conta na mao.
    # Eu calculava soma dos |passos| e chamava de AMPLITUDE. Isso e CAMINHO PERCORRIDO.
    # A definicao congelada e MAXIMO MENOS MINIMO dos niveis acumulados.
    # Para -1,+7,+6,-3,-3: niveis 0,-1,+6,+12,+9,+6 -> amplitude 13, caminho 20, saldo 6.
    # Nao e ajuste de corte olhando resultado: e a implementacao passando a cumprir a formula.
    niveis = np.concatenate([[0.0], np.cumsum(p)])
    amplitude = float(niveis.max() - niveis.min())
    caminho = float(np.abs(p).sum())
    razao = caminho / abs(total) if abs(total) > 1e-9 else None
    maior = p[np.argmax(np.abs(p))]
    conc = abs(maior) / caminho >= CONC if caminho > 0 else False
    mesmo = int(np.sum(np.sign(p) == np.sign(total))) if abs(total) > 1e-9 else 0

    # as duas ultimas sessoes devolveram parte do que foi ganho?
    virada = None
    if len(p) >= 3 and abs(total) > 1e-9:
        cauda = float(p[-2:].sum())
        if np.sign(cauda) != np.sign(total) and abs(cauda) >= 0.25 * caminho:
            virada = "a pullback in the last two sessions"

    if conc:
        forma = "concentrada"
    elif mesmo >= len(p) * 0.6:
        forma = "distribuida"
    else:
        forma = "oscilante"

    # ⚠️ Ponto 4 do Eduardo: "se alguma serie apenas repetiu um valor antigo".
    # Amplitude interna ZERO em 5 sessoes nao e estabilidade — e valor repetido.
    if caminho < 1e-9:
        # Tres estados possiveis (Eduardo, 31/ago), e so o primeiro seria dado valido:
        #   nova observacao com o mesmo valor  -> variacao zero legitima
        #   valor antigo arrastado             -> "sem nova observacao"
        #   nao sabemos qual dos dois          -> "update not verifiable"
        # ⚠️ LIMITE REAL: o calendario guarda o valor do dia sem dizer se foi OBSERVADO ou
        # arrastado. Para a serie historica so consigo o terceiro estado. Declarado, nao
        # disfarcado.
        return {"forma": "sem variacao", "classe": "update not verifiable",
                "amplitude_bp": 0.0, "saldo_bp": 0.0, "razao": None, "virada": None,
                "corte_amplitude_bp": None, "corte_saldo_bp": None,
                "descricao": "no change at all across five sessions. This can be new observations "
                             "carrying the same value, or an old value carried forward — the source "
                             "does not distinguish the two. Classifications that depend on those "
                             "sessions are suspended; this is NOT observed economic stability.",
                "suspeita_repeticao": True}
    if abs(total) < 1e-9:
        desc = "travelled %.1f bp and returned to the starting point — not stability" % caminho
    else:
        sentido = "rise" if total > 0 else "fall"
        base = {"concentrada": "%s concentrated in a few sessions" % sentido,
                "distribuida": "%s distributed across the sessions" % sentido,
                "oscilante": "%s with no consistency across sessions" % sentido}[forma]
        desc = base + (", with " + virada if virada else "")
    # ---- as DUAS condicoes, contra a historia do proprio par ----
    corte_amp = corte_sal = None
    classe = "indefinida"
    if hist_amp is not None and hist_saldo is not None and len(hist_amp) >= 60:
        corte_amp = float(np.quantile(np.abs(hist_amp), Q_AMPLITUDE))
        corte_sal = float(np.quantile(np.abs(hist_saldo), Q_SALDO))
        amp_rel = amplitude > corte_amp
        sal_peq = abs(total) < corte_sal
        # fronteira: dentro de 10% do corte, nao escolhe lado
        perto = (abs(amplitude - corte_amp) / corte_amp < 0.10) if corte_amp else False
        if perto:
            classe = "boundary of the amplitude cut"
        elif amp_rel and sal_peq:
            classe = "oscillation without net direction"
        elif amp_rel and not sal_peq:
            classe = "directional movement"
        elif not amp_rel and sal_peq:
            classe = "stability"          # exige AS DUAS: amplitude baixa E saldo pequeno
        else:
            # amplitude abaixo do p70 NAO e estabilidade por si so — e so "nao elevada".
            # Sem as duas condicoes, nao se inventa classe: fica intermediario.
            classe = "intermediate movement"
        if classe == "oscillation without net direction":
            desc += " — travelled %.1f bp (above the cut of %.1f) for a balance of %.1f "                     "(below the cut of %.1f): it oscillated, it did not stay flat."                     % (amplitude, corte_amp, total, corte_sal)
    return {"forma": forma, "descricao": desc, "classe": classe,
            "amplitude_bp": round(amplitude, 1), "caminho_bp": round(caminho, 1),
            "saldo_bp": round(total, 1),
            "corte_amplitude_bp": round(corte_amp, 1) if corte_amp else None,
            "corte_saldo_bp": round(corte_sal, 1) if corte_sal else None,
            "razao": round(razao, 2) if razao else None, "virada": virada,
            "suspeita_repeticao": False}


def estado_trajetoria(rel20, d20, rel5, d5, traj):
    """A tabela de estados do Eduardo, na letra."""
    amplo = rel20 == "relevante"
    recente = rel5 == "relevante"
    if rel5 == "transicao" or rel20 == "transicao":
        return "transicao / baixa definicao"
    if not recente:
        return ("estavel apos queda" if (amplo and d20 < 0)
                else "estavel apos alta" if (amplo and d20 > 0)
                else "estavel recentemente")
    if not amplo:
        return "movimento emergente de alta" if d5 > 0 else "movimento emergente de baixa"
    if d20 < 0 and d5 > 0:
        return "salto de recuperacao" if traj == "concentrada" else "em recuperacao"
    if d20 > 0 and d5 > 0:
        return "em fortalecimento"
    if d20 > 0 and d5 < 0:
        return "perdendo forca"
    return "em enfraquecimento"


def concordancia(d_dif, d_fx, rel_dif, rel_fx):
    """Direcao e magnitude SEPARADAS.

    Correcao do Eduardo: "sem alinhamento" escondia uma informacao verdadeira. Se os dois
    subiram, isso e observavel — o que falta e magnitude, e isso se diz em outro campo.
    """
    if d_fx is None:
        return {"direcao": None, "suficiencia": None,
                "frase": "comparison unavailable — different periods"}
    if abs(d_dif) < 1e-9 or abs(d_fx) < 1e-9:
        dir_ = "one of the two did not move"
    elif (d_dif > 0) == (d_fx > 0):
        dir_ = "same direction, both up" if d_dif > 0 else "same direction, both down"
    else:
        dir_ = "opposite directions"
    suf = "both relevant" if (rel_dif == "relevante" and rel_fx == "relevante") else           "magnitude insufficient by the adopted criterion"
    return {"direcao": dir_, "suficiencia": suf, "frase": "%s — %s" % (dir_, suf)}


# ------------------------------------------------------------------ execucao
if __name__ == "__main__":
    Y = serie_yields()
    T = serie_fx()
    MOEDAS = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "NZD", "CHF"]
    # 31-ago: AUDCHF e GBPNZD entram porque sao posicoes em avaliacao. O painel cobre o
    # par que estamos olhando, nao uma lista historica.
    PARES = ["USDCAD", "EURUSD", "USDJPY", "GBPUSD", "AUDNZD", "EURGBP", "AUDJPY",
             "NZDUSD", "AUDCHF", "GBPNZD"]

    ult_y = Y.dropna(how="all").index.max()
    # 31-ago: era max(). Quando UMA moeda vem mais fresca que as outras (o arquivo do USD
    # passou a chegar em D+0 e os demais em D-1), o max apontava para um dia em que quase
    # nenhum par tinha preco, e o painel devolvia "FX n/d" para a maioria. A janela comum e
    # o dia em que TODAS as moedas existem — portanto min().
    ult_fx = min(s.index.max() for s in T.values())
    comum = min(ult_y, ult_fx)

    print("=" * 96)
    print("JUROS x CAMBIO — janela comum")
    print("=" * 96)
    print("  ultima observacao de juro : %s" % ult_y.date())
    print("  ultima observacao de FX   : %s" % ult_fx.date())
    print("  JANELA COMUM usada        : ate %s  (%s)"
          % (comum.date(), "sincronizado" if ult_y == ult_fx else
             "NAO sincronizado — %d dia(s) de diferenca" % abs((ult_y - ult_fx).days)))
    print()

    fichas, comparaveis = [], 0
    for par in PARES:
        b, q = par[:3], par[3:]
        if b not in Y or q not in Y:
            continue
        p = preco(par, T)
        if p is None:
            continue

        # tudo na MESMA janela: ate a data comum
        yb = Y[b].dropna(); yq = Y[q].dropna()
        yb = yb[yb.index <= comum]; yq = yq[yq.index <= comum]
        px = p[p.index <= comum]
        if len(yb) < JAN_HIST + H_LONGO or len(yq) < 60 or len(px) < H_LONGO + 2:
            continue

        idx = yb.index.intersection(yq.index)
        dif = (yb.reindex(idx) - yq.reindex(idx)).dropna()
        if len(dif) < JAN_HIST + H_LONGO:
            continue

        d5 = 100 * (dif.iloc[-1] - dif.iloc[-1 - H_CURTO])       # em bp
        d20 = 100 * (dif.iloc[-1] - dif.iloc[-1 - H_LONGO])
        hist5 = 100 * dif.diff(H_CURTO).iloc[-JAN_HIST - 1:-1]
        hist20 = 100 * dif.diff(H_LONGO).iloc[-JAN_HIST - 1:-1]
        rel5, lim5 = relevancia(d5, hist5)
        rel20, lim20 = relevancia(d20, hist20)
        passos = (100 * dif.diff()).iloc[-H_CURTO:].tolist()
        # a historia da amplitude tem de usar a MESMA definicao: max - min da janela
        _niv = 100 * dif
        hist_amp = (_niv.rolling(H_CURTO + 1).max() - _niv.rolling(H_CURTO + 1).min())                      .dropna().iloc[-JAN_HIST - 1:-1].values
        hist_sal = (100 * dif.diff(H_CURTO)).dropna().iloc[-JAN_HIST - 1:-1].values
        traj = trajetoria(passos, hist_amp, hist_sal)
        est = estado_trajetoria(rel20, d20, rel5, d5, traj["forma"])

        # cambio na MESMA janela de datas, nao no mesmo numero de linhas
        ini5 = dif.index[-1 - H_CURTO]
        ini20 = dif.index[-1 - H_LONGO]
        px5 = px[px.index >= ini5]; px20 = px[px.index >= ini20]
        sincro = (abs((px.index[-1] - dif.index[-1]).days) <= 1
                  and len(px5) >= 2 and len(px20) >= 2)
        if sincro:
            fx5 = 100 * (px5.iloc[-1] / px5.iloc[0] - 1)
            fx20 = 100 * (px20.iloc[-1] / px20.iloc[0] - 1)
            hfx = 100 * (px / px.shift(H_CURTO) - 1).dropna().iloc[-JAN_HIST:]
            relfx, _ = relevancia(fx5, hfx)
            ec = concordancia(d5, fx5, rel5, relfx)
            if not traj.get("suspeita_repeticao"):
                comparaveis += 1
        else:
            fx5 = fx20 = None; relfx = None
            ec = concordancia(d5, None, rel5, None)

        fichas.append(dict(
            par=par, base=b, quote=q,
            janela_fim=str(dif.index[-1].date()),
            fx_fim=str(px.index[-1].date()), sincronizado=bool(sincro),
            yield_base=round(float(yb.iloc[-1]), 3), yield_quote=round(float(yq.iloc[-1]), 3),
            base_d5=round(100 * float(yb.iloc[-1] - yb.iloc[-1 - H_CURTO]), 1),
            quote_d5=round(100 * float(yq.iloc[-1] - yq.iloc[-1 - H_CURTO]), 1),
            base_d20=round(100 * float(yb.iloc[-1] - yb.iloc[-1 - H_LONGO]), 1),
            quote_d20=round(100 * float(yq.iloc[-1] - yq.iloc[-1 - H_LONGO]), 1),
            dif_nivel=round(float(dif.iloc[-1]), 3),
            dif_d5=round(float(d5), 1), dif_d20=round(float(d20), 1),
            rel5=rel5, rel20=rel20, limiar5_bp=lim5, limiar20_bp=lim20,
            trajetoria=traj, passos_bp=[round(x, 1) for x in passos],
            estado=est,
            # ⚠️ mesma data final NAO encerra a sincronizacao: o fixing do BCE e das 16h CET
            # e o yield e observado noutro horario. Ate conferir, isto fica declarado.
            sincronizacao="dates aligned; times to verify" if sincro
                          else "different periods — comparison unavailable",
            fx_d5=round(float(fx5), 2) if fx5 is not None else None,
            fx_d20=round(float(fx20), 2) if fx20 is not None else None,
            estado_cambial=ec,
        ))
        print("  %-8s dif %+7.1f bp/5s (%s) %+7.1f bp/20s (%s) | %-26s | traj %-12s | FX %s"
              % (par, d5, rel5[:4], d20, rel20[:4], est, traj,
                 ("%+.2f%%" % fx5) if fx5 is not None else "n/d"))

    doc = dict(
        gerado_em=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ultima_obs_juro=str(ult_y.date()), ultima_obs_fx=str(ult_fx.date()),
        janela_comum=str(comum.date()),
        sincronizado=bool(ult_y == ult_fx),
        metodo=dict(
            horizontes="5 e 20 sessoes — propostas iniciais, nao parametros comprovadamente superiores",
            relevancia="|variacao| comparada ao quantil %.0f%% das %d observacoes ANTERIORES do "
                       "proprio diferencial; entre %.0f%% e %.0f%% = transicao / baixa definicao"
                       % (Q_RELEVANTE * 100, JAN_HIST, Q_TRANSICAO * 100, Q_RELEVANTE * 100),
            trajetoria="concentrada quando um unico dia responde por >=%.0f%% do movimento" % (CONC * 100),
            diferencial="yield da moeda-base menos yield da moeda-cotada",
        ),
        comparaveis=comparaveis, total=len(fichas),
        pares=fichas,
    )
    json.dump(doc, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  pares com dados sincronizados: %d de %d" % (comparaveis, len(fichas)))
    print("  gravado: data/juros_vs_cambio.json")
