# -*- coding: utf-8 -*-
"""Gera data/cot_snapshot.json para o painel, a partir da API publica da CFTC.

Fonte: https://publicreporting.cftc.gov/resource/72hh-3qpy.json (Socrata, Legacy
Futures Only). Sem chave, sem custo. Reusa a mesma serie que o cot_downloader.py
do hci-ea ja usava; aqui o recorte e por MOEDA, para casar com o FUND.

Nada disto entra no score FUND. O painel exibe posicionamento; a decisao segue
sendo do operador. Um teste preregistrado dira se COT extremo tem edge.
"""
from __future__ import annotations

import json
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "data" / "cot_snapshot.json"
BASE = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"  # Legacy, Futures Only

# codigo do contrato na CFTC -> moeda do painel.
# Filtrar por CODIGO e nao por nome: nomes mudam de grafia, codigos nao.
# Confirmados na propria API em 21/ago/2026 (relatorio de 2026-08-04).
MARKETS = {
    "USD": ("098662", "USD INDEX - ICE FUTURES U.S."),
    "EUR": ("099741", "EURO FX - CHICAGO MERCANTILE EXCHANGE"),
    "GBP": ("096742", "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE"),
    "JPY": ("097741", "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE"),
    "AUD": ("232741", "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE"),
    "CAD": ("090741", "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE"),
    "NZD": ("112741", "NZ DOLLAR - CHICAGO MERCANTILE EXCHANGE"),
    "CHF": ("092741", "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE"),
}
HEADERS = {"User-Agent": "Mozilla/5.0 (HCI FUND Radar)", "Accept": "application/json"}
WEEKS = 260  # ~5 anos para o percentil e o z-score


def _fetch(codigo: str, weeks: int = WEEKS) -> list[dict]:
    params = {
        "$select": "report_date_as_yyyy_mm_dd,noncomm_positions_long_all,"
                   "noncomm_positions_short_all,open_interest_all",
        "cftc_contract_market_code": codigo,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": str(weeks),
    }
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build() -> dict:
    saida = []
    report_date = None
    for moeda, (codigo, mercado) in MARKETS.items():
        try:
            linhas = _fetch(codigo)
        except Exception as erro:
            print(f"  {moeda}: FALHOU ({erro})")
            continue
        if not linhas:
            print(f"  {moeda}: sem dados")
            continue
        nets = [_num(r.get("noncomm_positions_long_all")) - _num(r.get("noncomm_positions_short_all"))
                for r in linhas]
        atual, anterior = nets[0], (nets[1] if len(nets) > 1 else nets[0])
        historico = nets[:]
        media = statistics.fmean(historico)
        desvio = statistics.pstdev(historico) if len(historico) > 1 else 0.0
        z = (atual - media) / desvio if desvio > 0 else 0.0
        pct = 100.0 * sum(1 for v in historico if v <= atual) / len(historico)
        data = linhas[0].get("report_date_as_yyyy_mm_dd", "")[:10]
        report_date = report_date or data
        # historico causal: para CADA semana, percentil e z-score calculados
        # SOMENTE com as semanas anteriores a ela (expanding). Sem isso, exibir
        # o percentil de uma semana antiga usaria dados do futuro dela.
        historico_out = []
        cronologico = list(reversed(nets))                      # antigo -> recente
        datas_cron = list(reversed([r.get("report_date_as_yyyy_mm_dd", "")[:10] for r in linhas]))
        for k in range(len(cronologico)):
            janela = cronologico[:k + 1]
            if len(janela) < 12:
                continue
            v = janela[-1]
            m = statistics.fmean(janela)
            d = statistics.pstdev(janela) if len(janela) > 1 else 0.0
            historico_out.append({
                "date": datas_cron[k],
                "net": round(v),
                "percentile": round(100.0 * sum(1 for x in janela if x <= v) / len(janela), 1),
                "zscore": round((v - m) / d, 2) if d > 0 else 0.0,
            })
        historico_out.reverse()                                  # recente -> antigo

        saida.append({
            "history": historico_out,
            "currency": moeda,
            "market": mercado,
            "code": codigo,
            "report_date": data,
            "net": round(atual),
            "change": round(atual - anterior),
            "long": round(_num(linhas[0].get("noncomm_positions_long_all"))),
            "short": round(_num(linhas[0].get("noncomm_positions_short_all"))),
            "open_interest": round(_num(linhas[0].get("open_interest_all"))),
            "zscore": round(z, 2),
            "percentile": round(pct, 1),
            "history_weeks": len(historico),
        })
        print(f"  {moeda}: net {atual:+,.0f} | semana {atual - anterior:+,.0f} | "
              f"pct {pct:.0f}% | z {z:+.2f} | {data}")
    return {
        "meta": {
            "source": "CFTC Commitments of Traders — Legacy, Futures Only (dataset 6dca-aqww)",
            "endpoint": BASE,
            "report_date": report_date,
            "released": "sexta 15:30 ET, referente a terca da mesma semana",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "history_weeks": WEEKS,
            "status": "EXIBICAO_APENAS",
            "warning": "COT nao entra no FUND. Exibicao para contexto; "
                       "o teste preregistrado dira se posicionamento extremo tem edge.",
        },
        "currencies": saida,
    }


if __name__ == "__main__":
    print("Baixando COT da CFTC...")
    payload = build()
    if not payload["currencies"]:
        print("Nenhuma moeda baixada. Snapshot preservado.")
        sys.exit(1)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nsnapshot salvo: {DEST} | {len(payload['currencies'])}/8 moedas "
          f"| relatorio de {payload['meta']['report_date']}")
