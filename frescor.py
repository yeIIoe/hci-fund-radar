# -*- coding: utf-8 -*-
"""GUARDA DE FRESCOR — o dado nunca mais envelhece em silencio.

O QUE ACONTECEU EM 31/AGO/2026
Todos os arquivos-fonte estavam congelados desde 24-25/08: as curvas de 2 anos das oito
moedas, os precos do BCE, o calendario. Uma semana de dado velho, e nada reclamou. O
painel seguia mostrando numeros com cara de atuais.

A CAUSA
O download so refazia quando o arquivo estava mais velho que o TTL, medido pelo mtime.
Mas o `actions/checkout` REESCREVE todo arquivo a cada execucao, entao o mtime na nuvem e
sempre "agora" — o TTL dava sempre "fresco" e o download nunca acontecia. O bug so aparece
DEPOIS de migrar para CI: na maquina local o mtime era real e tudo funcionava.

Havia um segundo: o fallback do download chamava `curl.exe`, que nao existe em Linux.

AS DUAS DEFESAS DESTE ARQUIVO
1. CARIMBO PROPRIO  — grava a hora real do download num arquivo que E commitado, entao
                      sobrevive ao checkout. O TTL passa a ler dele, nao do mtime.
2. GUARDA DE FRESCOR — confere a ULTIMA DATA DENTRO de cada arquivo contra a cadencia
                      esperada. Se passou, FALHA a Action em vez de seguir calado.

A segunda e a que importa: mesmo que o download quebre de um jeito novo, o painel para de
publicar dado velho como se fosse novo.
"""
from __future__ import annotations
import csv, glob, io, json, os, re, sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(AQUI, "data", "raw")
CARIMBO = os.path.join(AQUI, "data", "raw", "_baixado_em.json")

# Tolerancia em dias UTEIS, por fonte. Generosa de proposito: o alarme e para dado
# ESQUECIDO, nao para atraso normal de publicacao.
TOLERANCIA = {
    "fx_ecb_": 3,          # BCE publica todo dia util as 16h CET
    "eur_ecb_2y": 4,
    "ust_cmt": 4,          # US Treasury, D+1
    "cad_boc": 4,
    "jpy_mof": 5,
    "chf_snb": 5,
    "aud_": 10,            # RBA publica SEMANALMENTE
    "nzd_": 6,
    "ff_calendar": 3,
    "tv_nowcast": 3,
}
PADRAO = 5


def carimbos():
    if os.path.exists(CARIMBO):
        try:
            return json.load(open(CARIMBO, encoding="utf-8"))
        except Exception:
            pass
    return {}


def grava_carimbo(nome):
    """Chamado pelo downloader quando um arquivo realmente e baixado."""
    c = carimbos()
    c[nome] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(CARIMBO), exist_ok=True)
    json.dump(c, open(CARIMBO, "w", encoding="utf-8"), indent=1, sort_keys=True)


def horas_desde_download(nome):
    """Idade REAL do download. Sobrevive ao checkout, ao contrario do mtime."""
    c = carimbos().get(nome)
    if not c:
        return None
    try:
        t = datetime.strptime(c, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return (datetime.now(timezone.utc) - t).total_seconds() / 3600.0


# ------------------------------------------------- a ultima data DENTRO do arquivo
DATA_RE = re.compile(r"(20\d{2})[-/](\d{2})[-/](\d{2})")


def ultima_data(caminho):
    """Le a maior data que aparece no conteudo. Funciona para csv, json e texto."""
    try:
        with io.open(caminho, encoding="utf-8", errors="replace") as f:
            texto = f.read(4_000_000)
    except Exception:
        return None
    achadas = DATA_RE.findall(texto)
    if not achadas:
        return None
    hoje = datetime.now().date()
    datas = []
    for a, m, d in achadas:
        try:
            x = datetime(int(a), int(m), int(d)).date()
        except ValueError:
            continue
        if x <= hoje:                      # ignora data futura (calendario de eventos)
            datas.append(x)
    return max(datas) if datas else None


def dias_uteis(de, ate):
    n, d = 0, de
    while d < ate:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def tolerancia_de(nome):
    for pref, t in TOLERANCIA.items():
        if nome.startswith(pref) or pref in nome:
            return t
    return PADRAO


if __name__ == "__main__":
    estrito = "--estrito" in sys.argv
    hoje = datetime.now().date()
    arquivos = sorted(glob.glob(os.path.join(RAW, "*")))
    # binario lido como texto devolve data falsa (o .xls do RBA dava 2003)
    BINARIO = (".xls", ".xlsx", ".zip", ".pdf", ".bi5")
    arquivos = [a for a in arquivos
                if os.path.isfile(a) and not a.endswith("_baixado_em.json")
                and not a.lower().endswith(BINARIO)]

    print("=" * 92)
    print("GUARDA DE FRESCOR — a ultima data DENTRO de cada fonte")
    print("=" * 92)
    print("  %-34s %12s %9s %10s  %s" % ("arquivo", "ultima data", "dias ut.", "tolerancia", ""))
    print("  " + "-" * 78)

    velhos, sem_data = [], []
    for a in arquivos:
        nome = os.path.basename(a)
        ud = ultima_data(a)
        tol = tolerancia_de(nome)
        if ud is None:
            sem_data.append(nome)
            print("  %-34s %12s %9s %10d  sem data legivel" % (nome[:34], "—", "—", tol))
            continue
        du = dias_uteis(ud, hoje)
        ruim = du > tol
        if ruim:
            velhos.append((nome, ud, du, tol))
        print("  %-34s %12s %9d %10d  %s"
              % (nome[:34], ud.isoformat(), du, tol, "🔴 VELHO" if ruim else "ok"))

    print()
    if velhos:
        print("=" * 92)
        print("🔴 %d FONTE(S) ALEM DA TOLERANCIA" % len(velhos))
        print("=" * 92)
        for nome, ud, du, tol in velhos:
            print("  %s: ultimo dado em %s, %d dias uteis atras (tolera %d)"
                  % (nome, ud.isoformat(), du, tol))
        print()
        print("  O painel NAO deve publicar isto como se fosse atual.")
        if estrito:
            print("  --estrito: falhando a execucao de proposito.")
            sys.exit(1)
    else:
        print("  ✅ todas as fontes dentro da tolerancia.")

    if sem_data:
        print("  (sem data legivel, nao avaliados: %s)" % ", ".join(sem_data[:6]))

    # relatorio para o site, para o frescor ficar visivel e nao so no log
    rel = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fontes": [
            {"arquivo": os.path.basename(a), "ultima_data": (ultima_data(a).isoformat()
                                                             if ultima_data(a) else None),
             "tolerancia_dias_uteis": tolerancia_de(os.path.basename(a))}
            for a in arquivos
        ],
        "fora_da_tolerancia": [n for n, _, _, _ in velhos],
    }
    json.dump(rel, open(os.path.join(AQUI, "data", "frescor.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print()
    print("  gravado: data/frescor.json")
