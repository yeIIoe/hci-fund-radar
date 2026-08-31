# -*- coding: utf-8 -*-
"""hci_research_agent.py — AGENTE DE RESEARCH DIARIO da fabrica HCI (Eduardo, 09-jul-2026).
Roda 1x/dia (schtasks). Para cada nome do universo:
  1. Puxa dados vivos (yfinance) e compara com o snapshot do ULTIMO relatorio (state json).
  2. REGENERA o relatorio quando os dados que o compoem mudam de verdade:
     preco +/-3% | fwd P/E +/-10% | earnings passou | regime SPY x MM200 virou | >5 pregoes.
  3. Relatorio (txt em hci-hedge/reports/) com as ABAS pedidas:
     EXPECTATIVA DE PRECO (TP auditavel) | POSICAO A ARMAR | COMO ARMAR/EXECUTAR |
     POR QUE PODE DAR CERTO | O QUE PODE IMPEDIR (estatico do research + flags DINAMICAS).
  4. Grava data/equities_research.json para o site (o Discord saiu em 31-ago-2026).
Metodo: METODO_PESQUISA_EQUITIES_HCI_v1 (F2 - coletores automatizados; valuation = multiplo
alvo pre-registrado por nome × EPS forward; tese/riscos = blocos do research revisados por humano).
Uso: python hci_research_agent.py [--force]"""
from __future__ import annotations
import json, os, sys
from datetime import date, datetime
from pathlib import Path
import numpy as np
import requests
import yfinance as yf
try:                      # so existe na maquina local; na nuvem nao ha janela para esconder
    import hci_silent; hci_silent.log_se_sem_console("research")
except Exception:
    pass

# Portado para o repo do radar em 31-ago-2026 (decisao do Eduardo: nada roda na maquina dele).
# Os caminhos eram fixos em C:/Trading e so funcionavam naquela maquina.
AQUI = Path(__file__).resolve().parent
OUT = AQUI / 'data'
REP = AQUI / 'data' / 'equities_reports'
OUT.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)
STATE = OUT / 'research_agent_state.json'
SAIDA_SITE = OUT / 'equities_research.json'
# Discord removido em 31-ago-2026 por decisao do Eduardo: tudo no site.

# ---- UNIVERSO + config pre-registrada por nome (multiplo-alvo e blocos de tese vem do research
#      humano; o agente ATUALIZA numeros, nao inventa teses) ----
CFG = {
 "TSM": dict(bdr="TSMC34", mult=24.0, nota="A (monopolio pratico; ja em carteira)",
   tese="Pedagio de 67% da era da IA: >90% dos chips avancados; fwd P/E em linha com o setor sendo O monopolio.",
   certo=["capex IA dos hyperscalers $416bn->$925bn (27E) passa por ela",
          "guidance AI CAGR mid-40s%; EPS 16%/ano ha 12 anos sem queda",
          "margens 2x os peers (GM 62%) = poder de preco de monopolio"],
   impede=["Taiwan/geopolitica (risco de cauda permanente)",
           "corte coordenado de capex IA (FCF dos hyperscalers ja caiu 240->73bn)",
           "energia de Taiwan (+25% na eletricidade = -50bps margem)",
           "concentracao: Apple >20% da receita, top-4 = 50%"]),
 "MU": dict(bdr="MUTC34", mult=10.0, nota="B+ (ciclica de memoria em ciclo bom; ja em carteira)",
   tese="O gargalo do buildout de IA migrou de GPU para HBM; LTAs de 3-5 anos deram poder de preco estrutural.",
   certo=["HBM3E lider (+50% capacidade, -20% consumo vs peers)",
          "oferta de HBM apertada ate 2026+; contratos longos",
          "P/E baixo mesmo apos rally (mas ver risco de ciclo)"],
   impede=["CICLO: P/E baixo de ciclica no TOPO e armadilha classica (lucro +1368% = pico?)",
           "capacidade nova (fab $24bn Singapura) chegando = risco de glut 2027+",
           "ASP de DRAM/NAND despenca rapido em virada de ciclo"]),
 "ASML": dict(bdr="ASML34", mult=30.0, nota="A+ qualidade / D valuation (gatilho armado, fora por P/E>45)",
   tese="Monopolio literal (100% EUV). Bloqueada pela guarda de valuation; entra por gatilho.",
   certo=["ninguem fabrica chip <7nm sem ela; backlog em conversao",
          "roadmap High-NA = novo ciclo de upgrade obrigatorio"],
   impede=["P/E ~59 >> guarda 45: pagar perfeicao em tese sob ataque",
           "China = 33% da receita e proibida de comprar EUV",
           "compressao de multiplo come o crescimento (Cisco 2000)"]),
 "AMAT": dict(bdr="A1MT34", mult=24.0, nota="A qualidade / D valuation (gatilho armado)",
   tese="Oligopolio de equipamento de fab; o mais proximo da guarda de valuation (P/E ~50).",
   certo=["todo fab novo (CHIPS Act, de-globalizacao) compra dela",
          "oligopolio de 4 com pricing power"],
   impede=["P/E 50 > guarda 45", "ciclo de equipamento e violento nas viradas",
           "export controls China"]),
 "KLAC": dict(bdr="K1LA34", mult=28.0, nota="A+ qualidade (ROE 95%!) / D valuation (gatilho armado)",
   tese="Oligopolio de inspecao: quanto menor o node, mais inspecao por wafer.",
   certo=["ROE ~95%, o melhor negocio do grupo", "conteudo de inspecao CRESCE com a complexidade"],
   impede=["P/E ~61, o mais esticado do grupo", "mesmos riscos de ciclo/China"]),
 "LRCX": dict(bdr="L1RC34", mult=25.0, nota="A qualidade / D valuation (gatilho armado)",
   tese="Oligopolio etch/deposicao; alavancada a NAND/DRAM capex.",
   certo=["recuperacao de capex de memoria = alavanca dupla (equip + HBM)"],
   impede=["P/E ~60 > guarda", "exposicao a memoria = mais ciclica que AMAT/KLAC"]),
}
GATILHO_DELTA_PX = 0.03
GATILHO_DELTA_PE = 0.10
GATILHO_DIAS = 5
PEERS = {"TSM": ["UMC", "GFS"], "MU": ["WDC", "STX"], "ASML": ["AMAT", "LRCX"],
         "AMAT": ["LRCX", "KLAC"], "KLAC": ["AMAT", "LRCX"], "LRCX": ["AMAT", "KLAC"]}
GATILHOS_PX = {"ASML": 1549.86, "AMAT": 477.39, "KLAC": 191.29, "LRCX": 284.24}  # opcao B (semicap)


def zona_diaria_viva(tk):
    """CAMADA DE TIMING (CESTA v1.1): zona de COMPRA diaria validada (H2 canonico) mais proxima
    ABAIXO do preco, VIVA (nao consumida) e FRESCA (nao testada). Retorna (zlo, zhi) ou None."""
    d = yf.download(tk, period="2y", interval="1d", auto_adjust=True, progress=False)
    d = d.dropna()
    if len(d) < 250:
        return None
    O = d["Open"].values.ravel(); H = d["High"].values.ravel()
    L = d["Low"].values.ravel(); C = d["Close"].values.ravel()
    n = len(d); K = 3
    ph, pl = [], []
    for i in range(K, n - K):
        if H[i] == max(H[i - K:i + K + 1]): ph.append((H[i], i))
        if L[i] == min(L[i - K:i + K + 1]): pl.append((L[i], i))
    zonas = []
    for (lvl, i) in pl:
        prev = [p for p in ph if p[1] < i]
        if not prev: continue
        ref = prev[-1][0]
        for j in range(i + 1, n):
            if C[j] > ref:
                zlo, zhi = L[i], min(O[i], C[i])
                if C[i] >= O[i] and i > 0 and C[i - 1] < O[i - 1]:
                    zlo = min(zlo, L[i - 1]); zhi = max(zhi, min(O[i - 1], C[i - 1]))
                elif C[i] < O[i] and i + 1 < n and C[i + 1] >= O[i + 1]:
                    zlo = min(zlo, L[i + 1]); zhi = max(zhi, min(O[i + 1], C[i + 1]))
                zonas.append([zlo, zhi, j])
                break
    px = C[-1]
    vivas = []
    for (zlo, zhi, born) in zonas:
        morta = testada = False
        for u in range(born, n):
            if C[u] < zlo: morta = True; break
            if u > born and L[u] <= zhi: testada = True
        if not morta and not testada and zhi < px:
            vivas.append((zlo, zhi))
    return max(vivas, key=lambda z: z[1]) if vivas else None


def series_para_charts(tk):
    """Series p/ os 3 graficos do PDF: preco 1y + MM200 do ativo + relativo (tk/SPY/peers) + metricas."""
    peers = PEERS.get(tk, [])
    ticks = [tk, "SPY"] + peers
    px2y = yf.download(ticks, period="2y", interval="1d", auto_adjust=True, progress=False)["Close"].dropna(how="all")
    px1y = px2y.tail(252)
    mm200 = px2y[tk].rolling(200).mean().tail(252)
    rel = {t: px1y[t] for t in ticks if t in px1y}
    met = {}
    for t in [tk] + peers:
        try:
            ii = yf.Ticker(t).info
            met[t] = dict(roe=ii.get("returnOnEquity"), gm=ii.get("grossMargins"), revg=ii.get("revenueGrowth"))
        except Exception:
            met[t] = dict(roe=None, gm=None, revg=None)
    return px1y[tk].dropna(), mm200, rel, met


def snapshot(tk):
    t = yf.Ticker(tk)
    i = t.info
    px5 = yf.download([tk, "SPY"], period="1y", interval="1d", auto_adjust=True, progress=False)["Close"].dropna()
    spy = yf.download("SPY", period="2y", interval="1d", auto_adjust=True, progress=False)["Close"].dropna()
    spys = spy.iloc[:, 0] if hasattr(spy, "columns") else spy
    mm200 = float(spys.rolling(200).mean().iloc[-1])
    regime_ok = float(spys.iloc[-1]) > mm200
    p = float(px5[tk].iloc[-1])
    hi52 = float(px5[tk].max())
    fpe = i.get("forwardPE")
    eps_f = p / fpe if fpe else None
    edate = None
    try:
        cal = t.calendar
        ed = cal.get("Earnings Date") if isinstance(cal, dict) else None
        if ed:
            edate = str(ed[0]) if isinstance(ed, (list, tuple)) else str(ed)
    except Exception:
        pass
    return dict(px=p, fpe=fpe, eps_f=eps_f, hi52=hi52, roe=i.get("returnOnEquity"),
                gm=i.get("grossMargins"), revg=i.get("revenueGrowth"), tpe=i.get("trailingPE"),
                regime_ok=regime_ok, earnings=edate, dia=str(date.today()))


def precisa_regen(tk, novo, st):
    old = st.get(tk)
    if old is None:
        return "primeiro relatorio"
    m = []
    if old.get("px") and abs(novo["px"] / old["px"] - 1) >= GATILHO_DELTA_PX:
        m.append(f"preco {novo['px']/old['px']-1:+.1%}")
    if old.get("fpe") and novo.get("fpe") and abs(novo["fpe"] / old["fpe"] - 1) >= GATILHO_DELTA_PE:
        m.append(f"fwd P/E {novo['fpe']/old['fpe']-1:+.1%}")
    if old.get("regime_ok") != novo["regime_ok"]:
        m.append("REGIME VIROU")
    if old.get("earnings") and old["earnings"] != novo.get("earnings"):
        m.append("earnings atualizado")
    dias = (date.today() - date.fromisoformat(old["dia"])).days
    if dias >= GATILHO_DIAS + 2:
        m.append(f"{dias}d desde o ultimo")
    return ", ".join(m) if m else None


def gera_relatorio(tk, s, motivo):
    c = CFG[tk]
    tp = round(s["eps_f"] * c["mult"], 0) if s.get("eps_f") else None
    up = (tp / s["px"] - 1) if tp else None
    vs_hi = s["px"] / s["hi52"] - 1
    # ---- POSICAO A ARMAR (regra pre-registrada) ----
    if not s["regime_ok"]:
        pos = "NAO ARMAR NADA NOVO (regime SPY<MM200: a casa hiberna compras; manter posicoes por tese)"
    elif up is not None and up >= 0.10 and "D valuation" not in c["nota"]:
        pos = f"COMPRA/MANTER — upside {up:+.0%} >= +10% pela regua"
    elif up is not None and up >= 0.10:
        pos = f"AGUARDAR GATILHO — upside {up:+.0%} MAS bloqueada pela guarda de valuation (gatilhos ja armados no sentinela)"
    elif up is not None and up > -0.10:
        pos = f"MANTER (sem reforco) — upside {up:+.0%} entre -10% e +10%; armar reforco apenas em dip >=5% com tese intacta"
    else:
        pos = f"REDUZIR/EVITAR — upside {up:+.0%} <= -10%: preco ja passou do valor"
    flags = []
    if s.get("earnings"):
        flags.append(f"EARNINGS proximo: {s['earnings'][:10]} — risco de evento binario; nao armar posicao nova <5 dias antes")
    if vs_hi > -0.03:
        flags.append(f"preco a {vs_hi:+.0%} da maxima 52s — comprar topo exige tese forte (chase warning)")
    if not s["regime_ok"]:
        flags.append("REGIME CONTRA (SPY < MM200)")
    L = []
    L.append(f"{'='*72}")
    L.append(f"HCI RESEARCH — {tk} ({c['bdr']}) — {date.today()} — regen: {motivo}")
    L.append(f"{'='*72}")
    L.append(f"TESE: {c['tese']}")
    L.append(f"DADOS: preco {s['px']:.2f} | fwd P/E {s['fpe']:.1f} | trailing {s.get('tpe') or 'n/a'} | "
             f"ROE {(s.get('roe') or 0)*100:.0f}% | GM {(s.get('gm') or 0)*100:.0f}% | rec y/y {(s.get('revg') or 0)*100:+.0f}% | vs max52s {vs_hi:+.0%}")
    L.append("")
    L.append(f"[EXPECTATIVA DE PRECO] TP = EPS fwd {s['eps_f']:.2f} x {c['mult']:.0f}x (multiplo pre-registrado) = "
             f"USD {tp:.0f}  ->  upside {up:+.0%} | prazo 12m | nota: {c['nota']}")
    L.append("")
    L.append(f"[POSICAO A ARMAR] {pos}")
    L.append("")
    L.append(f"[COMO ARMAR E EXECUTAR]  (CESTA v1.1: timing por zona diaria)")
    L.append(f"  - Veiculo: {c['bdr']} (B3, a vista, SEM alavanca) ou acao US via conta internacional")
    L.append(f"  - Ordem: LIMITADA sempre (BDR fino = spread 0,5-1,5%)")
    zona = s.get("zona_timing")
    if zona:
        L.append(f"  - Tranche 1: 50% a mercado | Tranche 2: 50% no teste da ZONA DIARIA {zona[0]:.2f}-{zona[1]:.2f}"
                 f" (ou -5% = {s['px']*0.95:.2f}, ou a mercado no 10o pregao — o que vier primeiro)")
    else:
        L.append(f"  - Tranche: 50% a mercado + 50% em gatilho a {s['px']*0.95:.2f} (-5%) [sem zona diaria fresca no momento]")
    L.append(f"  - Sizing: ticket do sleeve pela nota (A/A+ cheio; B+ reduzido; bloqueada = so gatilho)")
    L.append(f"  - Saida: por TESE (nunca stop de preco em hold); revisao pos-earnings e mensal")
    L.append("")
    L.append("[POR QUE PODE DAR CERTO]")
    for x in c["certo"]:
        L.append(f"  + {x}")
    L.append("")
    L.append("[O QUE PODE IMPEDIR]")
    for x in c["impede"]:
        L.append(f"  - {x}")
    for x in flags:
        L.append(f"  ! DINAMICO: {x}")
    L.append("")
    txt = "\n".join(L)
    f = REP / f"{tk}_{date.today()}.txt"
    f.write_text(txt, encoding="utf-8")
    return txt, tp, up, pos


def main():
    force = "--force" in sys.argv
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    resumo = []
    pdfs = []
    for tk in CFG:
        try:
            s = snapshot(tk)
        except Exception as e:
            print(f"[{tk}] snapshot falhou: {e}")
            continue
        motivo = "forcado" if force else precisa_regen(tk, s, st)
        if not motivo:
            print(f"[{tk}] sem mudanca material — relatorio mantido")
            continue
        try:
            s["zona_timing"] = zona_diaria_viva(tk)
        except Exception:
            s["zona_timing"] = None
        txt, tp, up, pos = gera_relatorio(tk, s, motivo)
        # guarda a decisao no estado: sem isto o site so recebe o preco, sem alvo nem leitura
        s["tp"], s["upside"], s["posicao"], s["regen_motivo"] = tp, up, pos, motivo
        st[tk] = s
        resumo.append(f"{tk}: TP {tp:.0f} ({up:+.0%}) | {pos[:80]} | regen: {motivo}")
        print(f"[{tk}] REGENERADO ({motivo})")
        # ---- PDF RICO (graficos + decisao completa) ----
        try:
            import hci_research_pdf as RP
            px1y, mm200, rel, met = series_para_charts(tk)
            flags = []
            if s.get("earnings"):
                flags.append(f"EARNINGS proximo: {s['earnings'][:10]} — nao armar posicao nova <5 dias antes")
            if s["px"] / s["hi52"] - 1 > -0.03:
                flags.append("preco colado na maxima 52s (chase warning)")
            if not s["regime_ok"]:
                flags.append("REGIME CONTRA (SPY < MM200)")
            pdf = RP.build_pdf(tk, CFG[tk], s, motivo, tp, up, pos, flags, px1y, mm200, rel, met,
                               gatilho=GATILHOS_PX.get(tk))
            pdfs.append(pdf)
            print(f"[{tk}] PDF: {pdf}")
        except Exception as e:
            print(f"[{tk}] PDF falhou: {e}")
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- SAIDA PARA O SITE (substituiu o post no Discord) ----
    linhas = []
    for tk in CFG:
        v = st.get(tk)
        if not v:
            continue
        linhas.append(dict(
            ticker=tk, preco=v.get("px"), tp=v.get("tp"), upside=v.get("upside"),
            posicao=v.get("posicao"), regime_ok=v.get("regime_ok"),
            earnings=v.get("earnings"), hi52=v.get("hi52"),
            regenerado=tk in [r.split(":")[0] for r in resumo],
            tese=(CFG[tk].get("tese") if isinstance(CFG[tk], dict) else None),
        ))
    doc = dict(
        gerado_em=datetime.now().strftime("%Y-%m-%d %H:%M"),
        escopo="EQUITIES — unidade e a EMPRESA. Nao usa FUND nem par de moeda.",
        metodo="METODO_PESQUISA_EQUITIES_HCI_v1: multiplo alvo pre-registrado x lucro projetado.",
        limite="Leitura fundamental. Nao e ordem nem gatilho de entrada.",
        regenera_quando="preco 3% | projecao de lucro 10% | resultado divulgado | virada de regime | 5 pregoes",
        regenerados=resumo, nomes=linhas)
    SAIDA_SITE.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print("site: %s (%d nomes, %d regenerados)" % (SAIDA_SITE.name, len(linhas), len(resumo)))

    print(f"research agent ok: {len(resumo)} relatorio(s) regenerado(s)")


if __name__ == "__main__":
    main()
