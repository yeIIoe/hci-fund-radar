# -*- coding: utf-8 -*-
"""Prova de fogo do arquivador point-in-time (calendario_arquivo.py).

Tres coisas precisam ser PROVADAS, nao alegadas:
  1. rodar de novo sem novidade nao duplica nada;
  2. consenso que muda gera linha NOVA, sem apagar a antiga;
  3. reconstroi() nao enxerga leitura posterior a data pedida.
E de brinde: hash e cadeia pegam edicao a mao.

Roda sozinho: python tests/teste_calendario_arquivo.py
"""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import calendario_arquivo as ca  # noqa: E402

FALHAS = []


def confere(condicao, descricao):
    print("  [%s] %s" % ("OK " if condicao else "FALHOU", descricao))
    if not condicao:
        FALHAS.append(descricao)


def fonte(caminho, eventos, gerado_em):
    with io.open(caminho, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": gerado_em, "fonte": "teste", "eventos": eventos},
                  f, ensure_ascii=False, indent=1)


def main():
    base = tempfile.mkdtemp(prefix="teste_arquivo_")
    cal = os.path.join(base, "calendario_resultado.json")
    evt = os.path.join(base, "macro_eventos.json")
    arq = os.path.join(base, "calendario_arquivo")

    eventos = [
        {"id": "aaa-111", "moeda": "USD", "pais": "US", "titulo": "Nonfarm Payrolls",
         "quando_utc": "2026-09-04T12:30:00+00:00", "impacto": "HIGH",
         "consenso": 75.0, "anterior": 73.0, "divulgado": None, "revisado": None,
         "unidade": "K"},
        {"id": "bbb-222", "moeda": "EUR", "pais": "DE", "titulo": "Factory Orders",
         "quando_utc": "2026-09-05T06:00:00+00:00", "impacto": "MEDIUM",
         "consenso": -0.5, "anterior": 1.2, "divulgado": None, "revisado": None,
         "unidade": "%"},
        {"id": "ccc-333", "moeda": "GBP", "pais": "GB", "titulo": "BoE Rate Decision",
         "quando_utc": "2026-09-17T11:00:00+00:00", "impacto": "HIGH",
         "consenso": 4.0, "anterior": 4.0, "divulgado": None, "revisado": None,
         "unidade": "%"},
    ]
    sem_id = [{"titulo": e["titulo"], "moeda": e["moeda"], "impacto": e["impacto"],
               "quando_utc": e["quando_utc"], "previsao": e["consenso"],
               "anterior": e["anterior"], "resultado": e["divulgado"],
               "revisado": None, "unidade": e["unidade"]} for e in eventos]

    print("=" * 72)
    print("TESTE 1 — tres execucoes seguidas: a 2a e a 3a nao podem duplicar")
    print("=" * 72)
    fonte(cal, eventos, "2026-09-06T10:00:00+00:00")
    fonte(evt, sem_id, "2026-09-06T10:00:00+00:00")
    r1 = ca.arquiva(arq, cal, evt, quando_li_utc="2026-09-06T10:00:00+00:00", silencioso=True)
    r2 = ca.arquiva(arq, cal, evt, quando_li_utc="2026-09-06T10:15:00+00:00", silencioso=True)
    r3 = ca.arquiva(arq, cal, evt, quando_li_utc="2026-09-06T10:30:00+00:00", silencioso=True)
    print("  rodada 1: %d linhas | rodada 2: %d | rodada 3: %d"
          % (r1["linhas_gravadas"], r2["linhas_gravadas"], r3["linhas_gravadas"]))
    total = sum(1 for _ in ca._linhas(os.path.join(arq, "2026-09.jsonl")))
    print("  total de linhas no arquivo: %d" % total)
    confere(r1["linhas_gravadas"] == 3, "1a execucao gravou os 3 eventos")
    confere(r2["linhas_gravadas"] == 0, "2a execucao gravou ZERO")
    confere(r3["linhas_gravadas"] == 0, "3a execucao gravou ZERO")
    confere(total == 3, "arquivo tem 3 linhas, sem duplicata")

    print()
    print("=" * 72)
    print("TESTE 2 — consenso muda: tem que sair linha NOVA, sem apagar a velha")
    print("=" * 72)
    eventos[0]["consenso"] = 90.0
    sem_id[0]["previsao"] = 90.0
    fonte(cal, eventos, "2026-09-06T14:00:00+00:00")
    fonte(evt, sem_id, "2026-09-06T14:00:00+00:00")
    r4 = ca.arquiva(arq, cal, evt, quando_li_utc="2026-09-06T14:00:00+00:00", silencioso=True)
    linhas = [x for x in ca._linhas(os.path.join(arq, "2026-09.jsonl"))]
    nfp = [x for x in linhas if x["evento_id"] == "aaa-111"]
    print("  linhas gravadas nesta rodada: %d  (motivos: %s)" % (r4["linhas_gravadas"], r4["motivos"]))
    for x in nfp:
        print("    seq=%d  quando_li=%s  consenso=%s  mudou=%s  hash=%s"
              % (x["seq"], x["quando_li_utc"], x["consenso"], x["mudou"], x["hash_valores"]))
    confere(r4["linhas_gravadas"] == 1, "so o evento alterado gerou linha")
    confere(len(nfp) == 2, "o NFP tem 2 linhas (historico preservado)")
    confere(nfp[0]["consenso"] == 75.0 and nfp[1]["consenso"] == 90.0,
            "a linha antiga continua com 75.0 e a nova traz 90.0")
    confere(nfp[1]["mudou"] == ["consenso"], "a linha nova diz o que mudou")

    # e a re-execucao logo depois da mudanca tambem nao pode gravar nada
    r5 = ca.arquiva(arq, cal, evt, quando_li_utc="2026-09-06T14:15:00+00:00", silencioso=True)
    confere(r5["linhas_gravadas"] == 0, "re-execucao apos a mudanca grava ZERO")

    print()
    print("=" * 72)
    print("TESTE 3 — reconstroi() nao pode olhar leitura posterior a data pedida")
    print("=" * 72)
    antes = ca.reconstroi("2026-09-06T12:00:00+00:00", arq)
    depois = ca.reconstroi("2026-09-06T23:00:00+00:00", arq)
    print("  pedido 12:00Z -> usadas %d | ignoradas do futuro %d | consenso NFP = %s"
          % (antes["linhas_usadas"], antes["linhas_ignoradas_futuro"],
             antes["eventos"]["aaa-111"]["consenso"]))
    print("  pedido 23:00Z -> usadas %d | ignoradas do futuro %d | consenso NFP = %s"
          % (depois["linhas_usadas"], depois["linhas_ignoradas_futuro"],
             depois["eventos"]["aaa-111"]["consenso"]))
    confere(antes["eventos"]["aaa-111"]["consenso"] == 75.0,
            "as 12:00Z o consenso conhecido era 75.0 (a revisao das 14:00Z nao vazou)")
    confere(antes["linhas_ignoradas_futuro"] == 1, "a leitura das 14:00Z foi contada como ignorada")
    confere(depois["eventos"]["aaa-111"]["consenso"] == 90.0, "as 23:00Z o consenso ja e 90.0")
    confere(all(ca._instante(l["quando_li_utc"]) <= ca._instante("2026-09-06T12:00:00+00:00")
                for l in antes["eventos"].values()),
            "nenhuma linha devolvida tem quando_li_utc no futuro do pedido")

    # data anterior a qualquer leitura: tem que vir vazio, nao 'quase certo'
    vazio = ca.reconstroi("2026-09-01", arq)
    print("  pedido 2026-09-01 -> arquivos lidos %s | eventos %d"
          % (vazio["arquivos_lidos"], len(vazio["eventos"])))
    confere(len(vazio["eventos"]) == 0, "antes da 1a leitura o arquivo nao sabe nada")

    print()
    print("=" * 72)
    print("TESTE 4 — integridade: edicao a mao tem que ser detectada")
    print("=" * 72)
    ok, det = ca.verifica(arq)
    print("  verificacao antes de mexer: ok=%s linhas=%d problemas=%s" % (ok, det["linhas"], det["problemas"]))
    confere(ok, "arquivo intacto passa na verificacao")

    caminho = os.path.join(arq, "2026-09.jsonl")
    cru = io.open(caminho, "r", encoding="utf-8").read().splitlines()
    adulterada = json.loads(cru[1])
    adulterada["consenso"] = 999.0          # alguem "melhorando" o passado
    cru[1] = json.dumps(adulterada, ensure_ascii=False, sort_keys=True)
    io.open(caminho, "w", encoding="utf-8", newline="\n").write("\n".join(cru) + "\n")
    ok2, det2 = ca.verifica(arq)
    print("  verificacao depois de editar a linha 2: ok=%s" % ok2)
    for p in det2["problemas"]:
        print("    -> %s" % p)
    confere(not ok2, "a edicao a mao foi PEGA pelo hash")

    shutil.rmtree(base, ignore_errors=True)

    print()
    print("=" * 72)
    print("TESTE 5 — arquivo REAL do repositorio")
    print("=" * 72)
    ok3, det3 = ca.verifica()
    print("  verificacao do arquivo real: ok=%s linhas=%d" % (ok3, det3["linhas"]))
    confere(ok3, "arquivo real integro")
    passado = ca.reconstroi("2026-09-01")
    hoje = ca.reconstroi("2026-12-31")
    print("  reconstroi 2026-09-01 -> eventos %d | ignoradas do futuro %d"
          % (len(passado["eventos"]), passado["linhas_ignoradas_futuro"]))
    print("  reconstroi 2026-12-31 -> eventos %d | ignoradas do futuro %d"
          % (len(hoje["eventos"]), hoje["linhas_ignoradas_futuro"]))
    confere(len(passado["eventos"]) == 0 and passado["linhas_ignoradas_futuro"] == det3["linhas"],
            "no passado o arquivo real nao sabe nada e conta as linhas do futuro")
    confere(len(hoje["eventos"]) > 0, "no futuro ele devolve o estado conhecido")

    print()
    if FALHAS:
        print("RESULTADO: %d FALHA(S) — %s" % (len(FALHAS), "; ".join(FALHAS)))
        return 1
    print("RESULTADO: todas as provas passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
