# -*- coding: utf-8 -*-
"""Le o que a ponte MQL5 escreve e entrega ao MACRO DIRECTION.

O PROBLEMA QUE ISTO RESOLVE
    O leitor precisa do valor DIVULGADO no instante em que sai. O feed do Forex Factory da
    previsao e anterior, nunca o resultado — conferido tres vezes em 01 e 02/set.
    O MetaTrader tem o calendario completo, mas o pacote Python dele NAO expoe funcao
    nenhuma de calendario (verificado: MetaTrader5 5.0.5735, zero funcoes com "calendar").
    Entao a leitura acontece do lado MQL5, num Service, e chega aqui por arquivo.

O QUE ESTE MODULO FAZ
    1. acha a pasta comum do MetaTrader sozinho
    2. le os tres arquivos que a ponte escreve
    3. diz se a ponte esta VIVA (batimento recente) ou parada
    4. mede a LATENCIA REAL, que ninguem comprovou ate agora
    5. entrega os eventos ja normalizados, prontos para o leitor_regras

⚠️ LATENCIA: relatos de forum MQL5 vao de 15 segundos a mais de 2 minutos, e um moderador da
   propria MetaQuotes escreveu que "atraso dentro de 1 minuto e normal". A alegacao de
   "dezenas de milissegundos" e material de venda. Por isso `latencia_ms` vem MEDIDO no proprio
   arquivo — intervalo entre o horario do evento e o momento em que o valor apareceu na ponte.
   Depois de alguns dias de coleta a distribuicao responde, e a gente para de adivinhar.

⚠️ RELOGIO: os horarios da ponte vem em hora do SERVIDOR do broker, nao em UTC. A FTMO opera
   em GMT+2/+3 conforme o horario de verao europeu. `offset_servidor_h` existe para declarar
   isso; sem ele o evento entra com ate 3 horas de erro, que e o tipo de bug que ja nos custou
   caro duas vezes.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "mt5_calendario.json")

# A ponte grava com FILE_COMMON, entao cai na pasta comum, visivel a qualquer terminal.
COMUM_PADRAO = os.path.join(
    os.environ.get("APPDATA", ""), "MetaQuotes", "Terminal", "Common", "Files")

VIVO_SEGUNDOS = 120          # sem batimento por mais que isto, a ponte esta parada
OFFSET_SERVIDOR_H = 3        # FTMO = GMT+3 no horario de verao europeu; conferir em outubro


def pasta_comum() -> str | None:
    """Acha a pasta comum do MetaTrader. Tenta o padrao, depois procura."""
    if os.path.isdir(COMUM_PADRAO):
        return COMUM_PADRAO
    base = os.path.join(os.environ.get("APPDATA", ""), "MetaQuotes", "Terminal")
    if os.path.isdir(base):
        for d in os.listdir(base):
            p = os.path.join(base, d, "Files")
            if os.path.isdir(p) and any(f.startswith("hci_") for f in os.listdir(p)):
                return p
    return None


def _le(pasta: str, nome: str):
    fn = os.path.join(pasta, nome)
    if not os.path.exists(fn):
        return None
    try:
        return json.load(io.open(fn, encoding="utf-8", errors="replace"))
    except Exception as e:
        print("  !! %s ilegivel: %s" % (nome, e))
        return None


def _hora(txt: str, offset_h: int = OFFSET_SERVIDOR_H):
    """Hora do servidor do broker -> UTC. Declarado, nunca assumido."""
    if not txt:
        return None
    for f in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            t = dt.datetime.strptime(txt, f)
            return (t - dt.timedelta(hours=offset_h)).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def estado(pasta: str | None = None) -> dict:
    """A ponte esta viva? Ha quanto tempo? Quantas mudancas ja passaram?"""
    p = pasta or pasta_comum()
    if not p:
        return {"viva": False, "motivo": "pasta comum do MetaTrader nao encontrada"}
    st = _le(p, "hci_bridge_status.json")
    if not st:
        return {"viva": False, "motivo": "hci_bridge_status.json ausente — o Service nao rodou",
                "pasta": p}
    bat = _hora(st.get("vivo_em", ""))
    if not bat:
        return {"viva": False, "motivo": "batimento sem hora legivel", "pasta": p}
    idade = (dt.datetime.now(dt.timezone.utc) - bat).total_seconds()
    return {
        "viva": idade <= VIVO_SEGUNDOS,
        "idade_s": round(idade),
        "batimento_utc": bat.isoformat(),
        "voltas": st.get("voltas"),
        "mudancas_total": st.get("mudancas_total"),
        "servidor": st.get("servidor"),
        "conta": st.get("conta"),
        "pasta": p,
        "motivo": "" if idade <= VIVO_SEGUNDOS else "batimento de %d s atras" % idade,
    }


def normaliza(e: dict) -> dict:
    """Um evento da ponte no formato que o leitor consome."""
    q = _hora(e.get("quando", ""))
    return {
        "titulo": e.get("nome"),
        "moeda": e.get("moeda"),
        "pais": e.get("pais"),
        "impacto": e.get("importancia"),
        "quando_utc": q.isoformat() if q else None,
        "periodo": e.get("periodo"),
        "revisao": e.get("revisao"),
        "resultado": e.get("actual"),
        "previsao": e.get("forecast"),
        "anterior": e.get("previous"),
        "anterior_revisado": e.get("previous_revisado"),
        "tem_resultado": bool(e.get("tem_actual")),
        "latencia_ms": e.get("latencia_ms"),
        "fonte": "MT5",
    }


def eventos(pasta: str | None = None, so_com_resultado: bool = False) -> list:
    p = pasta or pasta_comum()
    if not p:
        return []
    full = _le(p, "hci_calendar_full.json") or {}
    live = _le(p, "hci_calendar_live.json") or {}
    por_id = {}
    for bloco in (full, live):                    # o live vem DEPOIS: sobrescreve o antigo
        for e in bloco.get("eventos", []):
            n = normaliza(e)
            if so_com_resultado and not n["tem_resultado"]:
                continue
            por_id[e.get("id")] = n
    return sorted(por_id.values(), key=lambda x: x["quando_utc"] or "")


def main():
    st = estado()
    print("=" * 78)
    print("PONTE MT5 -> MACRO DIRECTION")
    print("=" * 78)
    if not st.get("pasta"):
        print("  ❌ %s" % st["motivo"])
        print()
        print("  Instale o Service: veja mt5/INSTALAR.md")
        return
    print("  pasta comum: %s" % st["pasta"])
    if st["viva"]:
        print("  ✅ ponte VIVA — batimento de %d s atras" % st["idade_s"])
        print("     servidor %s · conta %s · %s voltas · %s mudancas ja vistas"
              % (st.get("servidor"), st.get("conta"), st.get("voltas"), st.get("mudancas_total")))
    else:
        print("  ⚠️ ponte PARADA — %s" % st["motivo"])

    ev = eventos()
    print()
    print("  eventos lidos: %d" % len(ev))
    com = [e for e in ev if e["tem_resultado"]]
    print("  ja divulgados (com resultado): %d" % len(com))

    lat = [int(e["latencia_ms"]) for e in com
           if e.get("latencia_ms") not in (None, "null") and str(e["latencia_ms"]).lstrip("-").isdigit()]
    if lat:
        lat = sorted(x/1000.0 for x in lat if 0 <= x < 3600_000)
        if lat:
            print()
            print("  LATENCIA MEDIDA (evento -> valor na ponte), em segundos:")
            print("    minimo %.0f · mediana %.0f · p90 %.0f · maximo %.0f   (n=%d)"
                  % (lat[0], lat[len(lat)//2], lat[int(len(lat)*0.9)], lat[-1], len(lat)))
            print("    ➜ este e o numero que ninguem tinha. Ele decide se a ponte serve")
            print("      para disparar na noticia ou so para arquivar.")

    if ev:
        print()
        print("  proximos e recentes:")
        for e in ev[:10]:
            q = e["quando_utc"][:16].replace("T", " ") if e["quando_utc"] else "?"
            print("    %s UTC  %-4s %-9s %-34s A=%-9s F=%-9s P=%s"
                  % (q, e["moeda"], e["impacto"], (e["titulo"] or "")[:34],
                     e["resultado"], e["previsao"], e["anterior"]))

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump({"gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(),
               "ponte": st, "total": len(ev), "eventos": ev},
              io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
