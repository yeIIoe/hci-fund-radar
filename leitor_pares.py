# -*- coding: utf-8 -*-
"""LEITOR — a matriz dos pares. BULL / BEAR / NAO NEGOCIA, pela expectativa da PROXIMA decisao.

A regra do Eduardo, literal:
    os dois vao subir      -> NAO NEGOCIA (sem divergencia)
    um sobe, outro mantem  -> NEGOCIA, direcao de quem sobe
    um sobe, outro corta   -> NEGOCIA FORTE (divergencia de 2 graus)

FORCA
    Nao e so a diferenca de direcao. Duas moedas podem ambas "subir" e ainda haver divergencia
    se uma sobe muito mais que a outra. Por isso cada moeda carrega uma INTENSIDADE (0 a 3),
    e a forca do par e a diferenca das intensidades COM SINAL.

NENHUM YIELD ENTRA AQUI. A leitura por moeda vem da expectativa para a proxima reuniao —
seja a que o leitor derivou do fluxo de dados, seja a precificada pelo mercado, seja as duas
lado a lado. O campo 'origem' diz de onde veio, sempre.
"""
from __future__ import annotations
import sys
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MOEDAS = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]

# Pares que a FTMO oferece e que o Eduardo pode operar. Ordem base/cotada como no MT5.
PARES = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCAD", "USDCHF",
    "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCAD", "EURCHF",
    "GBPJPY", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF",
    "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "CADJPY", "CADCHF", "CHFJPY",
]


@dataclass
class Leitura:
    """O que se espera do banco central desta moeda na PROXIMA reuniao."""
    moeda: str
    direcao: str            # SOBE | MANTEM | CORTA | SEM_DADO
    intensidade: int        # 0 a 3 — quanto de aperto/afrouxamento
    proxima: str            # data da reuniao
    origem: str             # de onde veio esta leitura
    nota: str = ""

    @property
    def valor(self) -> int:
        """Posicao na regua de politica monetaria, com sinal."""
        if self.direcao == "SEM_DADO":
            return None
        s = {"CORTA": -1, "MANTEM": 0, "SOBE": +1}[self.direcao]
        return s * max(self.intensidade, 1) if s else 0


def le_par(par: str, L: dict) -> dict:
    b, q = par[:3], par[3:]
    lb, lq = L.get(b), L.get(q)

    if lb is None or lq is None or lb.valor is None or lq.valor is None:
        falta = [m for m, x in ((b, lb), (q, lq)) if x is None or x.valor is None]
        return {"par": par, "sinal": "SEM_DADO", "forca": None,
                "motivo": "falta leitura de " + " e ".join(falta)}

    d = lb.valor - lq.valor
    if d == 0:
        return {"par": par, "sinal": "NAO NEGOCIA", "forca": 0,
                "motivo": "%s e %s na mesma posicao (%s) — sem divergencia"
                          % (b, q, lb.direcao)}

    sinal = "BULL" if d > 0 else "BEAR"
    forca = abs(d)
    rot = {1: "fraca", 2: "media", 3: "forte"}.get(forca, "muito forte")
    return {"par": par, "sinal": sinal, "forca": forca,
            "motivo": "%s %s x %s %s" % (b, lb.direcao, q, lq.direcao),
            "rotulo": rot,
            "quando": "%s / %s" % (lb.proxima, lq.proxima)}


def imprime(L: dict):
    print("=" * 86)
    print("LEITOR — expectativa para a PROXIMA decisao de cada banco central")
    print("=" * 86)
    print("  %-5s %-9s %-6s %-12s %s" % ("moeda", "direcao", "int.", "proxima", "origem"))
    print("  " + "-" * 80)
    for m in MOEDAS:
        x = L.get(m)
        if x is None:
            print("  %-5s %-9s %-6s %-12s %s" % (m, "SEM_DADO", "—", "—", "nao levantado"))
            continue
        print("  %-5s %-9s %-6s %-12s %s"
              % (m, x.direcao, x.intensidade if x.valor is not None else "—",
                 x.proxima, x.origem))
        if x.nota:
            print("        %s" % x.nota)

    res = [le_par(p, L) for p in PARES]
    neg = [r for r in res if r["sinal"] in ("BULL", "BEAR")]
    nao = [r for r in res if r["sinal"] == "NAO NEGOCIA"]
    sem = [r for r in res if r["sinal"] == "SEM_DADO"]

    print()
    print("=" * 86)
    print("PARES COM DIVERGENCIA — %d de %d" % (len(neg), len(PARES)))
    print("=" * 86)
    for r in sorted(neg, key=lambda x: -x["forca"]):
        print("  %-8s %-5s forca %d (%-11s) | %-28s | reunioes %s"
              % (r["par"], r["sinal"], r["forca"], r["rotulo"], r["motivo"], r["quando"]))

    print()
    print("  NAO NEGOCIA (%d): %s" % (len(nao), ", ".join(r["par"] for r in nao) or "—"))
    print()
    print("  SEM DADO (%d): %s" % (len(sem), ", ".join(r["par"] for r in sem) or "—"))
    print()
    print("  ⚠️ 'SEM DADO' NAO e neutro — e buraco. O leitor nao opina sobre esses pares.")


# ---------------------------------------------------------------------------------------
# ESTADO DE HOJE — 01/set/2026
# So entra moeda com fonte defensavel. O resto fica SEM_DADO, visivel.
# ---------------------------------------------------------------------------------------
HOJE = {
    "JPY": Leitura("JPY", "SOBE", 2, "18/set",
                   "mercado: ~80% de alta precificada",
                   "BoJ em 1,00%. Saiu do juro zero e o mercado ve continuidade."),
    "EUR": Leitura("EUR", "SOBE", 2, "10/set",
                   "mercado: alta para 2,50% quase certa + ~80% de uma 2a ate dezembro",
                   "⚠️ assimetria: membros do conselho com pouco apetite alem de setembro — "
                   "o risco e o mercado ter de RETIRAR altas."),
    "NZD": Leitura("NZD", "SOBE", 2, "HOJE 23:00",
                   "calendario: previsao 2,75% (anterior 2,50%)",
                   "⚠️ a alta ja esta no preco. O que decide e a TRAJETORIA projetada — "
                   "em 08/jul foi ela que organizou o mes, nao a alta."),
    "AUD": Leitura("AUD", "MANTEM", 0, "29/set",
                   "mercado: 88% de manutencao",
                   "RBA em 4,35%, hawkish hold. Bancos projetam +25 pb em novembro; "
                   "CPI de julho veio 3,5% contra 3,2% esperado."),
    "CHF": Leitura("CHF", "MANTEM", 0, "24/set",
                   "mercado: ~97% de manutencao",
                   "SNB em 0% desde jun/2025. Decide TRIMESTRALMENTE."),
    # Buracos declarados — em levantamento
    "USD": None,
    "GBP": None,
    "CAD": None,
}

if __name__ == "__main__":
    imprime(HOJE)
