# -*- coding: utf-8 -*-
"""CRONOMETRO DE RELEASE — mede, com numero, quanto tempo o dado leva para chegar.

A PERGUNTA QUE ISTO RESPONDE
    O BLS publica o Nonfarm Payrolls as 08:30:00 ET, cravado. Em que instante esse numero
    esta AQUI? Segundos? Um minuto? Dez?
    Ninguem publica isso. Os relatos de forum sobre o MT5 vao de 15 s a mais de 2 minutos, e a
    API do BLS nao promete nada. Enquanto for palpite, nao da para decidir se a leitura serve
    para entrar numa vela de 1 minuto ou so para arquivar.

    O Eduardo entra em estrutura de 1 e 5 minutos. Trinta minutos de atraso sao trinta velas:
    o rompimento ja aconteceu e a zona ja foi tocada. Por isso o numero importa.

COMO ELE MEDE
    Fotografa o estado ANTES do release e depois fica olhando as duas fontes ate o valor mudar.
    O instante da mudanca menos o instante do release e a latencia. Nao ha inferencia: e
    cronometro.

      · ponte MT5   -> arquivo local, sem rede, sem cota. Pode olhar a cada 250 ms.
      · API do BLS  -> tem COTA DIARIA, e ela e o portao de verdade:
                          sem chave      25 chamadas/dia
                          com chave      500 chamadas/dia   (registro gratuito)
                       Medido em 02/set: 8 chamadas seguidas passam sem atraso nenhum, entao o
                       limite nao e por segundo. Mas 25/dia significa que sem chave so da para
                       espiar ~20 vezes numa janela. Por isso o cronograma abaixo e denso no
                       comeco e vai rareando — e onde a informacao esta.

    ⚠️ A COTA E O ACHADO. Mesmo que a API atualizasse instantaneamente, sem chave nao da para
    perguntar rapido o bastante para perceber. Registrar a chave gratuita nao e comodidade, e
    pre-requisito. Registro: https://data.bls.gov/registrationEngine/  (a pagina responde 200,
    ao contrario do resto do site do BLS, que devolve 403 ate no RSS)

USO
    python cronometro_release.py                 espera o proximo NFP e mede
    python cronometro_release.py --agora         mede ja, para testar o mecanismo
    python cronometro_release.py --em 2026-09-10T12:30:00Z
    BLS_API_KEY=...  no ambiente, se ja houver chave registrada
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "latencia_release.json")
BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
CHAVE = os.environ.get("BLS_API_KEY", "").strip()

SERIE_NFP = "CES0000000001"
COMUM = os.path.join(os.environ.get("APPDATA", ""), "MetaQuotes", "Terminal", "Common", "Files")

# Cronograma de espiadas na API, em segundos APOS o release. Denso onde a resposta mora,
# esparso depois. Sem chave sao 25/dia no total, entao esta lista ja e quase todo o orcamento.
ESPIADAS_SEM_CHAVE = [0, 3, 6, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 420, 600, 900]
ESPIADAS_COM_CHAVE = ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9] + list(range(10, 61, 2)) +
                      list(range(65, 181, 5)) + list(range(190, 601, 15)) +
                      list(range(630, 1801, 60)))


def agora() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def proximo_nfp() -> dt.datetime:
    """Primeira sexta-feira do mes, 08:30 America/New_York -> UTC.

    O relogio e declarado, nunca fixado: 08:30 ET e -4 no horario de verao e -5 fora dele, e
    esse foi exatamente o bug que ja custou caro duas vezes neste projeto.
    """
    hoje = agora()
    for mes_a_frente in (0, 1):
        y = hoje.year + (hoje.month + mes_a_frente - 1) // 12
        m = (hoje.month + mes_a_frente - 1) % 12 + 1
        d = dt.date(y, m, 1)
        while d.weekday() != 4:                      # 4 = sexta
            d += dt.timedelta(days=1)
        if ZoneInfo:
            local = dt.datetime(d.year, d.month, d.day, 8, 30, tzinfo=ZoneInfo("America/New_York"))
            utc = local.astimezone(dt.timezone.utc)
        else:                                        # sem tzdata: assume EDT e AVISA
            print("  ! zoneinfo indisponivel — assumindo EDT (-4). Confira em novembro.")
            utc = dt.datetime(d.year, d.month, d.day, 12, 30, tzinfo=dt.timezone.utc)
        if utc > hoje:
            return utc
    raise RuntimeError("nao achei o proximo NFP")


def bls_ultimo() -> tuple:
    """(periodo, valor, ms_da_chamada) do ponto mais novo do NFP. (None, None, ms) se falhar."""
    t0 = time.time()
    corpo = {"seriesid": [SERIE_NFP], "startyear": str(agora().year - 1),
             "endyear": str(agora().year)}
    if CHAVE:
        corpo["registrationkey"] = CHAVE
    try:
        req = urllib.request.Request(BLS_API, data=json.dumps(corpo).encode(),
                                     headers={"Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req, timeout=25))
        ms = (time.time() - t0) * 1000
        if d.get("status") != "REQUEST_SUCCEEDED":
            return (None, None, ms)
        pts = d["Results"]["series"][0]["data"]
        if not pts:
            return (None, None, ms)
        # o BLS devolve do mais novo para o mais velho
        p = pts[0]
        return ("%s-%s" % (p["year"], p["periodName"]), p["value"], ms)
    except Exception:
        return (None, None, (time.time() - t0) * 1000)


def mt5_estado() -> dict:
    """Quantas linhas com valor divulgado a ponte ja escreveu, e qual foi a ultima."""
    fn = os.path.join(COMUM, "hci_calendar.ndjson")
    if not os.path.exists(fn):
        return {"existe": False, "linhas": 0, "ultima": None}
    try:
        linhas = io.open(fn, encoding="utf-8", errors="replace").read().splitlines()
    except Exception as e:
        return {"existe": True, "erro": str(e), "linhas": 0, "ultima": None}
    com = []
    for L in linhas:
        L = L.strip()
        if not L:
            continue
        try:
            o = json.loads(L)
        except Exception:
            continue
        if o.get("has_actual"):
            com.append(o)
    return {"existe": True, "linhas": len(linhas), "com_actual": len(com),
            "ultima": com[-1] if com else None}


def medir(alvo: dt.datetime, rotulo: str) -> dict:
    espiadas = ESPIADAS_COM_CHAVE if CHAVE else ESPIADAS_SEM_CHAVE
    print("=" * 86)
    print("CRONOMETRO DE RELEASE — %s" % rotulo)
    print("=" * 86)
    print("  release em: %s UTC" % alvo.isoformat()[:19])
    print("  chave do BLS: %s" % ("registrada — %d espiadas programadas" % len(espiadas)
                                  if CHAVE else
                                  "AUSENTE — so %d espiadas (cota de 25/dia). "
                                  "Registre em data.bls.gov/registrationEngine/" % len(espiadas)))

    # --- foto do ANTES. Sem ela nao ha como saber que algo mudou.
    base_periodo, base_valor, ms = bls_ultimo()
    base_mt5 = mt5_estado()
    print()
    print("  ANTES do release:")
    print("    BLS: ultimo ponto = %s, valor %s  (resposta em %.0f ms)"
          % (base_periodo, base_valor, ms))
    if base_mt5["existe"]:
        print("    MT5: ponte presente, %d linhas, %d com valor divulgado"
              % (base_mt5["linhas"], base_mt5.get("com_actual", 0)))
    else:
        print("    MT5: ponte AUSENTE — o Service nao esta rodando, essa metade nao sera medida")

    espera = (alvo - agora()).total_seconds()
    if espera > 0:
        print()
        print("  faltam %.0f min. Aguardando..." % (espera / 60.0))
        while (alvo - agora()).total_seconds() > 1:
            time.sleep(min(30, max(0.5, (alvo - agora()).total_seconds() - 0.5)))

    print()
    print("  --- RELEASE ---")
    t_release = agora()
    achou_bls = None
    achou_mt5 = None
    amostras = []
    proxima = 0

    # A ponte e local: olhar a cada 250 ms nao custa nada. A API tem cota: so nos marcos.
    while True:
        decorrido = (agora() - t_release).total_seconds()
        if decorrido > (espiadas[-1] + 30):
            break

        if achou_mt5 is None and base_mt5["existe"]:
            m = mt5_estado()
            if m.get("com_actual", 0) > base_mt5.get("com_actual", 0):
                achou_mt5 = {"segundos": round(decorrido, 2), "evento": m.get("ultima")}
                print("  [%7.2fs] MT5  -> valor novo na ponte: %s"
                      % (decorrido, (m.get("ultima") or {}).get("name", "?")))

        if achou_bls is None and proxima < len(espiadas) and decorrido >= espiadas[proxima]:
            per, val, ms = bls_ultimo()
            amostras.append({"t_s": round(decorrido, 2), "periodo": per, "valor": val,
                             "resposta_ms": round(ms)})
            mudou = per and per != base_periodo
            print("  [%7.2fs] BLS  -> %s = %s  (%.0f ms)%s"
                  % (decorrido, per, val, ms, "   <<< MUDOU" if mudou else ""))
            if mudou:
                achou_bls = {"segundos": round(decorrido, 2), "periodo": per, "valor": val}
            proxima += 1

        if achou_bls and (achou_mt5 or not base_mt5["existe"]):
            break
        time.sleep(0.25)

    print()
    print("  " + "=" * 82)
    print("  RESULTADO")
    print("  " + "=" * 82)
    if achou_mt5:
        print("    ponte MT5: %.2f s apos o release" % achou_mt5["segundos"])
    elif base_mt5["existe"]:
        print("    ponte MT5: NADA em %d s de observacao" % espiadas[-1])
    else:
        print("    ponte MT5: nao medida (Service parado)")
    if achou_bls:
        s = achou_bls["segundos"]
        print("    API BLS:   %.2f s apos o release  (%s = %s)"
              % (s, achou_bls["periodo"], achou_bls["valor"]))
        velas = s / 60.0
        print()
        print("    ➜ %.1f vela(s) de 1 minuto. %s"
              % (velas, "Serve para decidir na estrutura." if velas <= 2 else
                        "NAO serve para entrada de 1min — o movimento ja aconteceu."))
    else:
        print("    API BLS:   NADA mudou em %d s de observacao" % espiadas[-1])
        if not CHAVE:
            print("               (so %d espiadas disponiveis sem chave — pode ter passado no meio)"
                  % len(espiadas))

    rel = {"medido_em": t_release.isoformat(), "alvo": alvo.isoformat(), "rotulo": rotulo,
           "tinha_chave_bls": bool(CHAVE), "espiadas_programadas": len(espiadas),
           "antes": {"bls_periodo": base_periodo, "bls_valor": base_valor,
                     "mt5_com_actual": base_mt5.get("com_actual"), "mt5_presente": base_mt5["existe"]},
           "latencia_mt5_s": achou_mt5["segundos"] if achou_mt5 else None,
           "latencia_bls_s": achou_bls["segundos"] if achou_bls else None,
           "amostras_bls": amostras,
           "nota": "latencia de ENTREGA: do release ate o valor estar aqui. Nao confundir com a "
                   "defasagem de REFERENCIA (o mes que o dado descreve), que e universal."}

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    hist = []
    if os.path.exists(SAIDA):
        try:
            hist = json.load(io.open(SAIDA, encoding="utf-8")).get("medicoes", [])
        except Exception:
            hist = []
    hist.append(rel)
    json.dump({"atualizado_em": agora().isoformat(), "medicoes": hist},
              io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s  (%d medicao(oes) no historico)" % (SAIDA, len(hist)))
    return rel


def main():
    arg = sys.argv[1:]
    if "--agora" in arg:
        medir(agora() + dt.timedelta(seconds=3), "teste do mecanismo (sem release real)")
        return
    if "--em" in arg:
        t = arg[arg.index("--em") + 1].replace("Z", "+00:00")
        medir(dt.datetime.fromisoformat(t), "release informado na linha de comando")
        return
    alvo = proximo_nfp()
    faltam = (alvo - agora()).total_seconds() / 3600.0
    print("  proximo NFP: %s UTC (faltam %.1f h)" % (alvo.isoformat()[:19], faltam))
    if faltam > 26:
        print("  ! mais de um dia de espera. Rode no dia, ou use --em para outra data.")
        return
    medir(alvo, "Nonfarm Payrolls")


if __name__ == "__main__":
    main()
