# -*- coding: utf-8 -*-
"""TESTE DO LEITOR DE FALAS — os tres casos do dono mais negacao, condicao, passado e sujeito.

Roda sozinho, sem pytest:   python tests/teste_leitor_falas.py

Os tres casos que motivaram o modulo (frases REAIS de data/bc_discursos.json, 05/set/2026):
    Waller  -> manutenção        (a contagem de palavras marcava "hawkish")
    Barr    -> alta condicional  (a contagem marcava alta firme)
    Warsh   -> indeterminado     (a contagem marcava "hawkish")

Nao ha rede aqui: as frases reais estao coladas no arquivo e o teste do arquivo inteiro le
data/bc_discursos.json do disco. Nada e gravado.
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from leitor_falas import (SELO, VOTA, VEREDITOS, classifica_fala, classifica_frase,  # noqa: E402
                          vereditos_do_arquivo)

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

# ------------------------------------------------------------------ frases REAIS do arquivo
WALLER_MANTER = ("If this continues in the data due over the next two weeks, I would be inclined "
                 "to support holding the target for the federal funds rate at its current setting.")
WALLER_COND_1 = ("If the incoming data for August show this improvement has been fleeting, then it "
                 "may be appropriate to raise the policy rate when the FOMC meets on September 15 "
                 "and 16.")
WALLER_COND_2 = "But if inflation comes in hot, I would consider a rate hike."
WALLER_PASSADO = ("But as this would only happen after asset purchases had stopped, I supported "
                  "forward guidance that strongly signaled the end of those purchases, setting the "
                  "stage for rate increases in 2022.")
BARR = ("However, if inflation appears not to be moderating sufficiently, then I think we should "
        "act decisively to raise rates.")
WARSH = ("7 And I believe when policymakers make quasi-commitments on interest rates through the "
         "cycle, we inhibit our own freedom to make the right calls when it's time to decide.")
PILL_MERCADO = ("Just as we the MPC was wary of allowing markets to 'get-ahead-of-themselves' with "
                "respect to prospective Bank Rate hikes in the immediate after math of hostilities "
                "breaking out in the Gulf, we should also recognise that markets may have already "
                "'gotten-ahead-of-themselves' with respect to prospective Bank Rate cuts before the "
                "energy price shock.")
PILL_HOLD = ("Whether implicitly or explicitly, it is natural for market participants to interpret "
             "this set of scenarios as suggesting the MPC is seeking to keep rates on hold but "
             "would raise rates aggressively if the inflation outlook were to deteriorate "
             "significantly.")
BOJ = ("As for the conduct of monetary policy, the Bank will continue to raise the policy interest "
       "rate and adjust the degree of monetary accommodation, in response to developments in "
       "economic activity and prices as well as financial conditions.")

# --------------------------------------------------------------------------------- os casos
# (numero, o que o caso prova, entrada, veredito esperado)
CASOS_FRASE = [
    (1, "Waller: apoia MANTER — a contagem chamava de hawkish",
     WALLER_MANTER, "manutenção"),
    (2, "Barr: hawkish mas CONDICIONAL ('se a inflacao nao moderar')",
     BARR, "alta condicional"),
    (3, "Warsh: liberdade para decidir nao e alta nem corte",
     WARSH, "indeterminado"),
    (4, "PASSADO: 'I supported ... rate increases in 2022' nao e o proximo passo",
     WALLER_PASSADO, "indeterminado"),
    (5, "CONDICAO em ingles: 'should inflation persist'",
     "Should inflation persist above target, we would need to raise the policy rate.",
     "alta condicional"),
    (6, "CONDICAO em portugues: 'caso os dados piorem'",
     "Caso os dados piorem, seria apropriado cortar os juros na próxima reunião.",
     "corte condicional"),
    (7, "NEGACAO em portugues: 'nao vejo necessidade de subir'",
     "Não vejo necessidade de subir os juros neste momento.", "manutenção"),
    (8, "NEGACAO em ingles: 'would not support' anula o corte",
     "I would not support a rate cut at the September meeting.", "manutenção"),
    (9, "NEGACAO: 'sem pressa para cortar' e ficar parado, nao e corte",
     "We are in no rush to cut rates.", "manutenção"),
    (10, "PASSADO explicito: 'we raised ... in 2022'",
     "We raised the policy rate by 425 basis points in 2022 and the economy is still adjusting.",
     "indeterminado"),
    (11, "PASSADO: 'the tightening we delivered' e recibo, nao postura",
     "The tightening we delivered last year is still working through the economy.",
     "indeterminado"),
    (12, "SUJEITO: cedula nao e politica de juros",
     "The new vertical polymer bank note will enter circulation in October.", "indeterminado"),
    (13, "SUJEITO: pagamentos nao e politica de juros",
     "Our work on the payment system and instant payments continues to expand this year.",
     "indeterminado"),
    (14, "ALTA firme: comunicado do BoJ diz que vai continuar subindo",
     BOJ, "alta"),
    (15, "CORTE firme: 'appropriate to lower the policy rate'",
     "It is appropriate to lower the policy rate at the next meeting.", "corte"),
    (16, "MANUTENCAO firme em ingles: 'comfortable holding'",
     "I am comfortable holding rates where they are for now.", "manutenção"),
    (17, "TERCEIROS: 'prospective hikes/cuts' e expectativa de MERCADO, nao postura",
     PILL_MERCADO, "indeterminado"),
    (18, "MANUTENCAO com alta condicional na mesma frase: manda a firme",
     PILL_HOLD, "manutenção"),
    (19, "CONTRADICAO: duas posturas firmes na mesma frase nao dao direcao",
     "We will raise the policy rate in September and cut the policy rate in December.",
     "indeterminado"),
    (20, "CONDICAO nao rebaixa MANUTENCAO: manter sob condicao continua manter",
     "If the data cooperate, I would be comfortable holding rates at the current setting.",
     "manutenção"),
]

# Agregacao: varias frases do MESMO orador (o item real do Waller tem quatro)
CASOS_FALA = [
    (21, "Waller inteiro: 1 manutencao firme + 2 altas condicionais + 1 passado -> manutenção",
     {"data": "2026-09-03", "link": "https://www.federalreserve.gov/waller",
      "titulo": "Waller, The Economic Outlook",
      "frases": [{"frase": WALLER_MANTER}, {"frase": WALLER_COND_1},
                 {"frase": WALLER_COND_2}, {"frase": WALLER_PASSADO}]},
     "manutenção"),
    (22, "Barr inteiro: uma unica frase, condicional",
     {"data": "2026-09-01", "link": "https://www.federalreserve.gov/barr",
      "titulo": "Barr, Unlocking Opportunities", "frases": [{"frase": BARR}]},
     "alta condicional"),
    (23, "Fala sem nenhuma frase de postura -> indeterminado, com motivo",
     {"data": "2026-09-04", "link": "https://www.bankofengland.co.uk/bailey",
      "titulo": "Bailey, institutional form", "frases": []},
     "indeterminado"),
]


def roda():
    falhas, n = [], 0
    print("=" * 92)
    print("TESTE DO LEITOR DE FALAS  ·  %s" % SELO)
    print("=" * 92)

    print("\n-- FRASE A FRASE " + "-" * 74)
    for num, oque, frase, esperado in CASOS_FRASE:
        n += 1
        r = classifica_frase(frase)
        ok = r["veredito"] == esperado
        if not ok:
            falhas.append((num, oque, esperado, r["veredito"]))
        print("  [%s] %2d %s" % ("ok " if ok else "FALHA", num, oque))
        print("        esperado: %-18s obtido: %s" % (esperado, r["veredito"]))
        print("        motivo:   %s" % r["motivo"])
        if r["veredito"] not in VEREDITOS:
            falhas.append((num, "veredito fora da lista oficial", "um de %s" % (VEREDITOS,),
                           r["veredito"]))
        if r["selo"] != SELO or r["vota"] is not False:
            falhas.append((num, "selo/vota ausentes no resultado", "%s / False" % SELO,
                           "%s / %s" % (r["selo"], r["vota"])))

    print("\n-- FALA INTEIRA (agrega varias frases do mesmo orador) " + "-" * 37)
    for num, oque, item, esperado in CASOS_FALA:
        n += 1
        r = classifica_fala(item)
        ok = r["veredito"] == esperado
        if not ok:
            falhas.append((num, oque, esperado, r["veredito"]))
        print("  [%s] %2d %s" % ("ok " if ok else "FALHA", num, oque))
        print("        esperado: %-18s obtido: %s" % (esperado, r["veredito"]))
        print("        motivo:   %s" % r["motivo"])
        print("        trecho:   %s" % (r["trecho"][:100] or "(sem trecho)"))
        print("        link:     %s" % r["link"])

    print("\n-- ARQUIVO REAL data/bc_discursos.json " + "-" * 53)
    caminho = os.path.join(RAIZ, "data", "bc_discursos.json")
    v = vereditos_do_arquivo(caminho)
    esperado_usd = {"Waller": "manutenção", "Barr": "alta condicional", "Warsh": "indeterminado"}
    obtido_usd = {l["orador"]: l["veredito"] for l in v.get("USD", [])}
    n += 1
    ok = all(obtido_usd.get(k) == e for k, e in esperado_usd.items())
    if not ok:
        falhas.append((24, "USD no arquivo real", str(esperado_usd), str(obtido_usd)))
    print("  [%s] 24 os tres casos do dono, lidos do arquivo real" % ("ok " if ok else "FALHA"))
    for l in v.get("USD", []):
        print("        %-10s %-18s %s" % (l["orador"], l["veredito"], (l["data"] or "-")))

    n += 1
    faltando = [(m, l["orador"]) for m in v for l in v[m]
                if l.get("selo") != SELO or l.get("vota") is not False
                or not l.get("link") or not l.get("data")]
    if faltando:
        falhas.append((25, "selo/vota/link/data em toda linha", "todas completas", str(faltando)))
    print("  [%s] 25 toda linha sai com selo, vota=false, data e link (fonte a um clique)"
          % ("ok " if not faltando else "FALHA"))

    n += 1
    if VOTA is not False:
        falhas.append((26, "REGRA DURA: o classificador nao vota", "VOTA=False", str(VOTA)))
    print("  [%s] 26 REGRA DURA: VOTA=False e selo “%s”" % ("ok " if VOTA is False else "FALHA",
                                                            SELO))

    print("\n" + "=" * 92)
    print("  %d casos  ·  %d passaram  ·  %d falharam" % (n, n - len(falhas), len(falhas)))
    for f in falhas:
        print("  FALHA %s: %s | esperado=%s obtido=%s" % f)
    print("=" * 92)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(roda())
