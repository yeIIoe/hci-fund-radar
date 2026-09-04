# -*- coding: utf-8 -*-
"""CALENDARIO COM RESULTADO — a peca que faltava para existir SURPRESA.

O BURACO QUE ISTO TAPA
    surpresa = divulgado - previsto. Ate hoje nos tinhamos meio da conta:
      · feed do Forex Factory  -> previsao e anterior, mas ZERO tags <actual>. Conferido
        quatro vezes; ha issue de terceiro no GitHub afirmando que tem, e ela esta errada.
      · API do BLS             -> o valor oficial, mas NUNCA a previsao, e com cota de 25/dia
      · ponte MT5              -> tem os dois, mas exige a maquina ligada e o forum oficial da
        propria MetaQuotes tem duas medicoes de NFP em 2min43s e 3min50s
    Este backend fecha a conta: divulgado + consenso + anterior + revisado, das 8 moedas.

🔬 A LATENCIA, MEDIDA POR MIM EM 02/set/2026, NAO ALEGADA PELO FORNECEDOR
    239 eventos ja divulgados das 8 majors, dos ultimos 10 dias, comparando `lastUpdated`
    contra o horario agendado:

        so eventos HIGH (n=20)   p10 13s   p25 24s   MEDIANA 44s   p75 163s
        os que voce opera:       AUD PIB +10s · BoC juro +12s · RBNZ juro +13s
                                 ISM +13s · Core PCE +15s

    Ou seja: nos eventos que movem o seu book, o numero chega DENTRO DE UMA VELA DE 1 MINUTO.
    E teto estrito, nao subestimativa — `lastUpdated` e a ultima modificacao do registro, e o
    resultado nao pode ter sido escrito depois dela.

⚠️ A CAUDA E REAL E NAO PODE SER ESCONDIDA
    Contando TODOS os impactos, so 21% chega em ate 1 minuto e 54% em ate 5. Os piores casos
    passam de 18 horas — mas sao retoque em LOTE de revisao MEDIUM (Durable Goods, PCE
    revisado), nao a primeira impressao. Por isso `atraso_s` sai em cada evento: quem consome
    decide, em vez de confiar na media.

🔴 O QUE ISTO NAO E
    Nao e produto licenciado. E o backend do widget de calendario deles: sem contrato, sem SLA,
    sem suporte, e pode ser bloqueado por IP ou Referer sem aviso. Trate como instrumento de
    medicao e prototipo, com plano B pronto — a ponte MT5 continua sendo o plano B.

🔴 E O GARGALO NAO E ELE
    De nada adianta um feed de 12 segundos lido por um cron de 15 minutos. A documentacao do
    proprio GitHub diz que o evento `schedule` "can be delayed during periods of high loads" e
    que "some queued jobs may be dropped". Enquanto o relogio for o cron, a leitura e de 15+
    minutos, independentemente de quem entrega o dado. Essa decisao vem ANTES da escolha de
    fonte.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "calendario_resultado.json")

BASE = "https://calendar-api.fxstreet.com/en/api/v1/eventDates/%s/%s"
CAB = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0",
       "Origin": "https://www.fxstreet.com", "Referer": "https://www.fxstreet.com/",
       "Accept": "application/json"}

OITO = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]


def buscar(dias_atras: int = 3, dias_frente: int = 8) -> list:
    hoje = dt.datetime.now(dt.timezone.utc).date()
    de = (hoje - dt.timedelta(days=dias_atras)).isoformat() + "T00:00:00Z"
    ate = (hoje + dt.timedelta(days=dias_frente)).isoformat() + "T00:00:00Z"
    req = urllib.request.Request(BASE % (de, ate), headers=CAB)
    with urllib.request.urlopen(req, timeout=45) as r:
        if r.status != 200:
            raise RuntimeError("HTTP %s" % r.status)
        return json.loads(r.read())


def num(x):
    """O campo vem como numero, texto ou nulo. Nulo tem que continuar nulo — 0.0 nao serve.

    Foi exatamente esse o bug da ponte MQL5: campo vazio virando 0.0 fazia 'sem previsao' e
    'previsao de 0,0%' ficarem identicos. O CPI mensal da Suica tem previsao de 0,0% de
    verdade.
    """
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def normaliza(e: dict) -> dict | None:
    moeda = e.get("currencyCode")
    if moeda not in OITO:
        return None
    try:
        quando = dt.datetime.fromisoformat(str(e["dateUtc"]).replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return None

    a, c, p = num(e.get("actual")), num(e.get("consensus")), num(e.get("previous"))

    # A ESCALA vem separada da unidade: NFP e potency="K", unit=None; balanca e "B" + "$".
    # Descartar a potency fazia o consenso do NFP chegar ao site como "56" em vez de "56K"
    # (achado da revisao de 03/set). "ZERO" e a marca deles para "sem escala".
    pot = str(e.get("potency") or "").strip().upper()
    escala = pot if pot in ("K", "M", "B", "T") else ""
    unidade = (escala + str(e.get("unit") or "")).strip() or None

    # atraso MEDIDO: carimbo de atualizacao menos o horario agendado. So existe apos divulgar.
    atraso = None
    lu = e.get("lastUpdated")
    if a is not None and isinstance(lu, (int, float)):
        d = lu - quando.timestamp()
        if 0 <= d < 86400 * 3:
            atraso = round(d, 1)

    # A surpresa CRUA. `ratioDeviation` deles ja normaliza pelo desvio historico, e vem junto —
    # mas a conta simples fica explicita para nao depender do criterio da casa.
    surpresa = (a - c) if (a is not None and c is not None) else None

    return {
        "id": e.get("id"),
        "moeda": moeda,
        "pais": e.get("countryCode"),
        "titulo": e.get("name"),
        "quando_utc": quando.isoformat(),
        "impacto": e.get("volatility"),
        "unidade": unidade,
        "escala": escala or None,
        "divulgado": a,
        "consenso": c,
        "anterior": p,
        "revisado": num(e.get("revised")),
        "surpresa": round(surpresa, 6) if surpresa is not None else None,
        "surpresa_normalizada": num(e.get("ratioDeviation")),
        "melhor_que_esperado": e.get("isBetterThanExpected"),
        "preliminar": e.get("isPreliminary"),
        "discurso": e.get("isSpeech"),
        "data_a_confirmar": e.get("isTentative"),
        "atraso_s": atraso,
        "fonte": "fxstreet",
    }


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    print("=" * 88)
    print("CALENDARIO COM RESULTADO — divulgado, consenso e surpresa")
    print("=" * 88)
    try:
        cru = buscar()
    except Exception as e:
        print("  X falhou: %s" % e)
        print("  ! plano B: ponte MT5 (mt5_ponte.py). Nao sobrescrevi nada.")
        sys.exit(1)

    ev = [x for x in (normaliza(e) for e in cru) if x]
    ev.sort(key=lambda x: x["quando_utc"])
    passado = [e for e in ev if e["divulgado"] is not None]
    futuro = [e for e in ev if e["divulgado"] is None and e["quando_utc"] > agora.isoformat()]
    print("  %d eventos das 8 majors  ·  %d ja divulgados  ·  %d por vir"
          % (len(ev), len(passado), len(futuro)))

    # A latencia sai medida A CADA RODADA. Se o backend degradar, aparece aqui, nao num palpite.
    lat = sorted(e["atraso_s"] for e in passado if e["atraso_s"] is not None)
    alta = sorted(e["atraso_s"] for e in passado
                  if e["atraso_s"] is not None and str(e["impacto"]).upper() == "HIGH")
    resumo_lat = None
    if lat:
        q = lambda L, p: L[min(len(L) - 1, int(len(L) * p))]
        resumo_lat = {"n": len(lat), "p25": q(lat, .25), "mediana": q(lat, .50),
                      "p75": q(lat, .75), "p90": q(lat, .90),
                      "n_alta": len(alta),
                      "mediana_alta": q(alta, .50) if alta else None,
                      "p90_alta": q(alta, .90) if alta else None}
        print()
        print("  ATRASO MEDIDO nesta rodada (carimbo menos horario agendado):")
        print("     todos (n=%d):  p25 %.0fs · mediana %.0fs · p90 %.0fs"
              % (len(lat), q(lat, .25), q(lat, .50), q(lat, .90)))
        if alta:
            print("     HIGH  (n=%d):  p25 %.0fs · MEDIANA %.0fs · p90 %.0fs   <<< os que voce opera"
                  % (len(alta), q(alta, .25), q(alta, .50), q(alta, .90)))
            print("     ➜ mediana de %.1f vela(s) de 1 minuto" % (q(alta, .50) / 60.0))

    print()
    print("  PROXIMOS EVENTOS DE ALTO IMPACTO:")
    n = 0
    for e in futuro:
        if str(e["impacto"]).upper() != "HIGH":
            continue
        h = dt.datetime.fromisoformat(e["quando_utc"])
        faltam = (h - agora).total_seconds() / 3600.0
        print("     %s UTC  em %5.1fh  %-4s %-42s prev=%s ant=%s"
              % (e["quando_utc"][:16].replace("T", " "), faltam, e["moeda"],
                 (e["titulo"] or "")[:42],
                 e["consenso"] if e["consenso"] is not None else "-",
                 e["anterior"] if e["anterior"] is not None else "-"))
        n += 1
        if n >= 10:
            break

    print()
    print("  ULTIMAS SURPRESAS MEDIDAS:")
    for e in [x for x in passado if x["surpresa"] is not None][-6:]:
        print("     %s  %-4s %-38s div=%-9s prev=%-9s surpresa=%+.3f  (+%ss)"
              % (e["quando_utc"][:16].replace("T", " "), e["moeda"], (e["titulo"] or "")[:38],
                 e["divulgado"], e["consenso"], e["surpresa"],
                 int(e["atraso_s"]) if e["atraso_s"] is not None else "?"))

    rel = {
        "gerado_em": agora.isoformat(),
        "fonte": "backend do calendario da FXStreet (sem chave; exige Origin/Referer)",
        "aviso_fonte": "backend de widget, NAO produto licenciado: sem contrato, sem SLA, pode "
                       "ser bloqueado sem aviso. Plano B = ponte MT5.",
        "aviso_gargalo": "de nada adianta feed de 12s lido por cron de 15min. A doc do GitHub "
                         "diz que o schedule pode atrasar sob carga e que jobs na fila podem "
                         "ser descartados. O relogio decide antes da fonte.",
        "latencia_medida": resumo_lat,
        "total": len(ev), "divulgados": len(passado), "por_vir": len(futuro),
        "eventos": ev,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(rel, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              allow_nan=False)
    print()
    print("  gravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
