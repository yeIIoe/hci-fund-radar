# -*- coding: utf-8 -*-
"""equities_sentinela.py — SENTINELA de equities. Roda os scans e grava para o SITE.

Portado em 31-ago-2026 da schtask HCI_Sentinela (manha 09:00 / fechamento 18:30), que
rodava na maquina do Eduardo e postava no Discord. Decisao dele: nada na maquina, nada
no Discord. A saida agora e data/sentinela.json, que o site le.

Nao precisa de chave: usa yfinance.
Uso: python sentinela.py manha   (watchlist fornecedores + deep value)
     python sentinela.py fechamento (BTD+HOLD)"""
from __future__ import annotations
import os, sys, subprocess, io
try:                      # so existe na maquina local
    import hci_silent; hci_silent.log_se_sem_console("sentinela")
except Exception:
    pass
try:  # com pythonw o sys.stdout e None -> .buffer quebraria o agente
    if sys.stdout is not None and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass
from pathlib import Path
import requests
import yfinance as yf

# Discord removido: os blocos vao para data/sentinela.json.
HOOK_GAP = HOOK_DV = HOOK_BTD = HOOK = None
HERE = Path(__file__).resolve().parent
OUT = HERE / "data"
OUT.mkdir(parents=True, exist_ok=True)
SAIDA_SITE = OUT / "sentinela.json"
BLOCOS = []                # cada post virou um bloco do site
TESE = {"ASML": "monopolio litografia EUV (ninguem faz chip sem ela)", "AMAT": "oligopolio equipamento de fab",
        "LRCX": "oligopolio etch/deposicao", "KLAC": "oligopolio inspecao de chips", "TER": "teste de chips",
        "TSM": "a fabrica do mundo", "MU": "memoria HBM p/ IA (ciclica)", "AMKR": "packaging avancado barato",
        "ENTG": "materiais/filtragem de fab", "APH": "conectores de tudo", "MPWR": "power semis",
        "COHR": "optica de datacenter", "FN": "manufatura optica", "MRVL": "interconexao de IA",
        "VRT": "cooling/power de datacenter", "ETN": "eletrica de datacenter", "PWR": "constroi o grid",
        "GEV": "turbinas/energia", "CEG": "geracao nuclear p/ datacenters", "VST": "geracao p/ datacenters",
        "MOD": "cooling", "WEGE3.SA": "motores/eletrica global (B3)",
        # ESSENCIAIS A VIDA (Eduardo 04-jul): comida, agua, saude, defesa, residuos
        "ADM": "processa a comida do mundo", "BG": "graos/oleos globais", "CTVA": "sementes/defensivos",
        "NTR": "fertilizante (potassa)", "DE": "maquinas agricolas", "XYL": "infra de AGUA",
        "AWK": "utility de agua US", "TMO": "equipamento de laboratorio/diagnostico (pas da biotech)",
        "DHR": "instrumentos de saude/diagnostico", "WST": "frascos/injetaveis (toda vacina passa aqui)",
        "STE": "esterilizacao hospitalar", "WM": "residuos (ninguem cancela lixo)",
        "RSG": "residuos #2", "LMT": "defesa (misseis)", "RTX": "defesa/aeroespacial",
        "NOC": "defesa (B-21/nuclear)", "SLC": "SLCE3 proxy agro BR" if False else "agro BR",
        "SLCE3.SA": "agro brasileiro (soja/algodao)", "SBSP3.SA": "saneamento SP (agua B3)"}
TESE.pop("SLC", None)
WATCH = list(TESE)


def post(title, text, hook=None):
    """Era o post no Discord; agora acumula um bloco para o site."""
    BLOCOS.append({"titulo": title, "texto": text or ""})
    print("[bloco] %s (%d chars)" % (title, len(text or "")))


def watchlist():
    px = yf.download(WATCH, period="10d", interval="1d", auto_adjust=True, progress=False)["Close"]
    r1 = px.pct_change().iloc[-1]
    hi52 = px.max()
    lines = []
    for t in WATCH:
        ret = r1.get(t)
        if ret is None:
            continue
        vs = (px[t].iloc[-1] / hi52[t] - 1) * 100
        flag = "🔥 DIP" if ret <= -0.03 else ("👀" if ret <= -0.015 else "")
        if flag:
            lines.append(f"{flag} {t:8} {ret*100:+.1f}% hoje | {vs:+.0f}% vs max | TESE: {TESE.get(t, '')}")
            if ret <= -0.03:
                lines.append("   -> dip>=3% em fornecedor de NECESSIDADE: aplicar regra BTD (qualidade+medo-vs-idio) e assinar. Conf ~65-75% (backtest BTD).")
    return "\n".join(lines) if lines else "Fornecedores: sem dips relevantes hoje. (paciencia = parte do metodo)"


def run(script):
    subprocess.run([sys.executable, str(HERE / script)], timeout=600,
                   capture_output=True)


def check_gatilhos(dry=False):
    """GATILHOS BTD da Opcao B (Eduardo, 07-jul-2026): os 4 oligopolios de semicap entram
    quando (a) CAPITULACAO: preco cai ~10% do close de referencia, ou (b) VALUATION: preco
    no nivel de P/E<=45 (guarda da peneira). Cada gatilho alerta UMA vez no canal BTD."""
    import json
    gf = OUT / "gatilhos_btd.json"
    if not gf.exists():
        return ""
    g = json.loads(gf.read_text(encoding="utf-8"))
    ticks = [t for t in g if not t.startswith("_")]
    if not ticks:
        return ""
    from datetime import date
    px = yf.download(ticks, period="5d", interval="1d", auto_adjust=True, progress=False)["Close"]
    alerts = []
    for t in ticks:
        p = float(px[t].dropna().iloc[-1]) if t in px else None
        if p is None:
            continue
        cfg = g[t]
        if cfg.get("fired_capit") is None and p <= cfg["capitulacao"]:
            cfg["fired_capit"] = str(date.today())
            alerts.append(f"🔔 GATILHO CAPITULACAO: {t} @ {p:.2f} (<= {cfg['capitulacao']:.2f}, -10% da referencia)\n"
                          f"   -> Opcao B: 1a janela de compra do {cfg['bdr']} (R${cfg['ticket_brl']}). "
                          f"Ordem LIMITADA. Assinar: a queda e medo ou quebra de tese?")
        if cfg.get("fired_val") is None and p <= cfg["valuation_pe45"]:
            cfg["fired_val"] = str(date.today())
            alerts.append(f"🔔🔔 GATILHO VALUATION: {t} @ {p:.2f} (<= {cfg['valuation_pe45']:.2f} = P/E ~45)\n"
                          f"   -> Opcao B: o monopolio chegou na GUARDA. Janela cheia do {cfg['bdr']} (R${cfg['ticket_brl']}). "
                          f"Re-checar P/E real no dia (lucro pode ter mudado).")
    if alerts:
        gf.write_text(json.dumps(g, indent=2, ensure_ascii=False), encoding="utf-8")
        txt = "\n".join(alerts)
        if dry:
            print(txt)
        else:
            post("🎯 GATILHOS BTD — Opcao B (semicap)", txt, HOOK_BTD)
        return txt
    return ""


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "manha"
    if modo == "manha":
        post("🎯 HCI RADAR — Fornecedores das Gigantes", watchlist(), HOOK_BTD)
        check_gatilhos()
        run("deep_value_scan.py")
        f = OUT / "deep_value_scan.txt"
        if f.exists():
            post("💎 HCI DEEP VALUE", f.read_text(encoding="utf-8")[:3500], HOOK_DV)
    elif modo == "teste":
        post("✅ HCI GAP — canal conectado (sentinela online)", "aguardando gappers do pré-market", HOOK_GAP)
        post("✅ HCI DEEP VALUE — canal conectado", "scan diário ~09:00", HOOK_DV)
        post("✅ HCI BTD/HOLD + Fornecedores — canal conectado", "radar ~09:00 · BTD pós-fechamento", HOOK_BTD)
    else:
        run("btd_hold_scan.py")
        fs = sorted(OUT.glob("btd_scan_*.txt"))
        if fs:
            post("📉 HCI BTD+HOLD (fechamento)", fs[-1].read_text(encoding="utf-8")[:3500], HOOK_BTD)
        check_gatilhos()
    # ---- SAIDA PARA O SITE (substituiu os posts no Discord) ----
    import json as _json
    from datetime import datetime as _dt
    anterior = {}
    if SAIDA_SITE.exists():
        try:
            anterior = _json.loads(SAIDA_SITE.read_text(encoding="utf-8"))
        except Exception:
            anterior = {}
    # cada modo escreve so a sua metade; o outro turno e preservado
    doc = {"gerado_em": _dt.now().strftime("%Y-%m-%d %H:%M"),
           "escopo": "EQUITIES — varredura diaria. Nao e ordem nem gatilho de entrada.",
           "manha": anterior.get("manha"), "fechamento": anterior.get("fechamento")}
    chave = "manha" if modo == "manha" else "fechamento"
    doc[chave] = {"quando": _dt.now().strftime("%Y-%m-%d %H:%M"), "blocos": BLOCOS}
    SAIDA_SITE.write_text(_json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print("site: %s (%s, %d blocos)" % (SAIDA_SITE.name, chave, len(BLOCOS)))
    print("sentinela ok:", modo)


if __name__ == "__main__":
    main()
