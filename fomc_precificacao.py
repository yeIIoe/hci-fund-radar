# -*- coding: utf-8 -*-
"""
Precificação implícita da próxima decisão do FOMC (método do FedWatch, feito em casa).

Fontes (sem chave, sem cadastro):
  - Futuros de fed funds de 30 dias (ZQ) e SOFR 3m (SR3): API de gráfico do Yahoo
    (a mesma que correlacao_juros.py já usa no GitHub Actions).
  - EFFR (taxa efetiva do dia anterior): API pública do NY Fed.

Método:
  taxa implícita do contrato = 100 − preço.
  O contrato do MÊS DA REUNIÃO é a média do mês: dias antes da decisão valem a EFFR
  de hoje, dias depois valem a taxa pós-decisão (a nova faixa vale a partir do dia
  seguinte ao anúncio). Quando existe o contrato do MÊS SEGUINTE, ele é usado direto
  como taxa pós-decisão (é o que o FedWatch faz).
  P(corte 25bp) = (EFFR − taxa_pos) / 0,25, limitada a [0, 1]; P(alta) é simétrica;
  P(manter) = 1 − P(corte) − P(alta).

LEI DO DONO: este número é DADO DE MERCADO. Ele não entra no sentimento (sentimento.py);
serve só para a coluna "Mercado precifica" ao lado da Leitura HCI.
Honestidade: se uma fonte falhar, o campo fica None e a interface escreve "sem fonte".
"""
import json
import calendar
import datetime as dt
import urllib.request
import urllib.error

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0",
      "Accept": "application/json,*/*"}

# Próxima reunião (data do anúncio) e a faixa vigente. Atualizar a cada reunião.
REUNIAO = dt.date(2026, 9, 16)
FAIXA_ATUAL = (3.50, 3.75)

# Códigos de mês dos futuros da CME
MES_COD = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M", 7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}


def _get_json(url, timeout=20):
    """Baixa JSON; devolve None em qualquer falha (nunca inventa)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return None


def yahoo_ultimo(sym):
    """Último preço e horário (UTC) de um símbolo na API de gráfico do Yahoo."""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%s?range=5d&interval=1d" % sym.replace("=", "%3D")
    j = _get_json(url)
    try:
        meta = j["chart"]["result"][0]["meta"]
        hora = dt.datetime.fromtimestamp(meta["regularMarketTime"], dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
        return {"preco": float(meta["regularMarketPrice"]), "hora": hora, "nome": meta.get("longName") or meta.get("shortName")}
    except (TypeError, KeyError, IndexError, ValueError):
        return None


def effr_atual():
    """EFFR publicada pelo NY Fed (último dia disponível)."""
    j = _get_json("https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json")
    try:
        r = j["refRates"][0]
        return {"taxa": float(r["percentRate"]), "data": r["effectiveDate"],
                "faixa": (float(r["targetRateFrom"]), float(r["targetRateTo"]))}
    except (TypeError, KeyError, IndexError, ValueError):
        return None


def simbolo_zq(ano, mes):
    return "ZQ%s%02d.CBT" % (MES_COD[mes], ano % 100)


def _clamp01(x):
    return max(0.0, min(1.0, x))


def precificacao(reuniao=REUNIAO):
    """Monta o dicionário completo com a conta aberta. Campos None = sem fonte."""
    out = {"reuniao": reuniao.isoformat(), "faixa_atual": FAIXA_ATUAL, "coletado_em": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")}
    e = effr_atual()
    out["effr"] = e
    # contrato do mês da reunião e do mês seguinte
    ano_m, mes_m = reuniao.year, reuniao.month
    ano_s, mes_s = (ano_m + 1, 1) if mes_m == 12 else (ano_m, mes_m + 1)
    c_mes = yahoo_ultimo(simbolo_zq(ano_m, mes_m))
    c_seg = yahoo_ultimo(simbolo_zq(ano_s, mes_s))
    out["contrato_mes"] = {"sym": simbolo_zq(ano_m, mes_m), **(c_mes or {})} if c_mes else None
    out["contrato_seguinte"] = {"sym": simbolo_zq(ano_s, mes_s), **(c_seg or {})} if c_seg else None
    # curva curta para exibição (dado de mercado)
    curva = []
    for k in range(0, 6):
        a, m = ano_m + (mes_m - 1 + k) // 12, (mes_m - 1 + k) % 12 + 1
        q = yahoo_ultimo(simbolo_zq(a, m))
        curva.append({"sym": simbolo_zq(a, m), "preco": q["preco"] if q else None,
                      "taxa_implicita": round(100 - q["preco"], 3) if q else None, "hora": q["hora"] if q else None})
    out["curva_zq"] = curva

    if not e or not c_mes:
        out.update({"taxa_pos": None, "p_corte": None, "p_manter": None, "p_alta": None, "conta": "sem fonte"})
        return out

    effr = e["taxa"]
    n_dias = calendar.monthrange(ano_m, mes_m)[1]
    dias_antes = reuniao.day            # a nova taxa vale a partir do dia seguinte ao anúncio
    dias_depois = n_dias - dias_antes
    taxa_mes = 100 - c_mes["preco"]
    # taxa pós-decisão extraída do próprio contrato do mês (só EFFR + contrato do mês)
    taxa_pos_mes = (taxa_mes * n_dias - effr * dias_antes) / dias_depois
    # taxa pós-decisão pelo contrato do mês seguinte (preferida, é o que o FedWatch usa)
    taxa_pos_seg = (100 - c_seg["preco"]) if c_seg else None
    taxa_pos = taxa_pos_seg if taxa_pos_seg is not None else taxa_pos_mes
    delta = taxa_pos - effr
    p_corte = _clamp01(-delta / 0.25)
    p_alta = _clamp01(delta / 0.25)
    p_manter = _clamp01(1 - p_corte - p_alta)
    out.update({
        "taxa_mes_reuniao": round(taxa_mes, 4),
        "dias_antes": dias_antes, "dias_depois": dias_depois,
        "taxa_pos_via_contrato_mes": round(taxa_pos_mes, 4),
        "taxa_pos_via_mes_seguinte": round(taxa_pos_seg, 4) if taxa_pos_seg is not None else None,
        "taxa_pos": round(taxa_pos, 4), "delta_bp": round(delta * 100, 1),
        "p_corte": round(p_corte, 3), "p_manter": round(p_manter, 3), "p_alta": round(p_alta, 3),
        "fonte_taxa_pos": "contrato do mês seguinte" if taxa_pos_seg is not None else "contrato do mês da reunião",
        "conta": (
            "EFFR %.2f (%s). %s = %.3f -> taxa media do mes %.3f. "
            "%d dias a EFFR + %d dias a taxa_pos => taxa_pos(via mes) = (%.3f*%d - %.2f*%d)/%d = %.3f. "
            "%s => taxa_pos = %.3f. delta = %+.1f bp. P(alta) = %.3f, P(corte) = %.3f, P(manter) = %.3f."
        ) % (effr, e["data"], c_mes and simbolo_zq(ano_m, mes_m), c_mes["preco"], taxa_mes,
             dias_antes, dias_depois, taxa_mes, n_dias, effr, dias_antes, dias_depois, taxa_pos_mes,
             ("%s = %.3f" % (simbolo_zq(ano_s, mes_s), c_seg["preco"])) if c_seg else "sem contrato seguinte",
             taxa_pos, delta * 100, p_alta, p_corte, p_manter),
    })
    return out


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # console do Windows
    except AttributeError:
        pass
    r = precificacao()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
