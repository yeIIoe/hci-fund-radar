#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor experimental e causal para OBSERVACOES do proximo fixing FX.

O alvo deste modulo e diferente do backtest HOLD do FUND. Para cada data D,
as variaveis usam apenas FUND e precos conhecidos ate D; o gabarito e o sinal
do retorno entre o fixing de D e o proximo fixing do ECB. A validacao e anual,
expansiva e fora da amostra.

O modelo nao gera entrada. Ele ordena pares que merecem observacao para uma
possivel queda na sessao seguinte; BO, REGIAO, ZOI e decisao continuam manuais.
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


GROUPS = {
    "fund_state": (0, 1, 2),
    "fund_change": (3, 4, 5),
    "price_action": (6, 7, 8, 9),
    "relation": (10, 11, 12),
}

GROUP_LABELS = {
    "fund_state": "FUND state",
    "fund_change": "Mudanca do FUND",
    "price_action": "Acao do preco",
    "relation": "Relacao FUND x preco",
}

WEIGHT_SCHEMES = {
    "FUND_ATUAL": None,
    "FUND_PESADO": np.array([0.40, 0.35, 0.15, 0.10], dtype=float),
    "IGUAL": np.array([0.25, 0.25, 0.25, 0.25], dtype=float),
    "PRECO_PESADO": np.array([0.10, 0.10, 0.55, 0.25], dtype=float),
}

MIN_TRAIN_YEARS = 3
MIN_TRAIN_ROWS = 4_000
GRID_STEP = 0.10


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-min(value, 40.0)))
    exp_value = math.exp(max(value, -40.0))
    return exp_value / (1.0 + exp_value)


def _log_returns(values: list[float]) -> list[float]:
    return [math.log(values[index] / values[index - 1]) for index in range(1, len(values))]


def _sample_features(
    fund_values: list[float],
    price_values: list[float],
) -> tuple[list[float], dict[str, float]] | None:
    if len(fund_values) < 7 or len(price_values) < 22:
        return None
    recent_returns = _log_returns(price_values[-22:])
    if len(recent_returns) < 20:
        return None
    volatility = statistics.stdev(recent_returns[-20:])
    volatility = max(volatility, 0.0001)

    fund = fund_values[-1]
    fund_d1 = fund - fund_values[-2]
    fund_d5 = fund - fund_values[-6]
    fund_accel = (fund - fund_values[-2]) - (fund_values[-2] - fund_values[-3])
    persistence = statistics.mean(1.0 if value > 0 else -1.0 if value < 0 else 0.0 for value in fund_values[-5:])
    fund_curve = fund_values[-1] - 2.0 * fund_values[-3] + fund_values[-6]

    ret1 = math.log(price_values[-1] / price_values[-2]) / volatility
    ret3 = math.log(price_values[-1] / price_values[-4]) / (volatility * math.sqrt(3.0))
    ret5 = math.log(price_values[-1] / price_values[-6]) / (volatility * math.sqrt(5.0))
    ret20 = math.log(price_values[-1] / price_values[-21]) / (volatility * math.sqrt(20.0))

    level = fund / 100.0
    slope1 = fund_d1 / 50.0
    slope5 = fund_d5 / 100.0
    accel = fund_accel / 50.0
    curve = fund_curve / 100.0
    divergence = level - math.tanh(ret20 / 3.0)
    agreement = level * math.tanh(ret5 / 3.0)
    impulse_agreement = slope5 * math.tanh(ret1 / 2.0)

    features = [
        level,
        persistence,
        math.copysign(abs(level) ** 1.5, level),
        slope1,
        slope5,
        accel + curve,
        max(-6.0, min(6.0, ret1)),
        max(-6.0, min(6.0, ret3)),
        max(-6.0, min(6.0, ret5)),
        max(-6.0, min(6.0, ret20)),
        divergence,
        agreement,
        impulse_agreement,
    ]
    context = {
        "fund": fund,
        "fund_d1": fund_d1,
        "fund_d5": fund_d5,
        "persistence": persistence,
        "price_ret1_pct": (math.exp(recent_returns[-1]) - 1.0) * 100.0,
        "price_ret5_pct": (price_values[-1] / price_values[-6] - 1.0) * 100.0,
        "price_ret20_pct": (price_values[-1] / price_values[-21] - 1.0) * 100.0,
        "volatility_pct": volatility * 100.0,
    }
    return features, context


def _build_samples(pairs: list[dict], prices_by_pair: dict[str, dict[date, float]]) -> tuple[list[dict], list[dict]]:
    labelled: list[dict] = []
    latest: list[dict] = []
    for pair in pairs:
        name = pair["pair"]
        history = sorted(
            (date.fromisoformat(row["date"]), float(row["fund"]))
            for row in pair["_fund_history"]
        )
        prices = prices_by_pair[name]
        price_days = sorted(prices)
        if not history or len(price_days) < 23:
            continue

        fund_days: list[date] = []
        fund_values: list[float] = []
        price_index = 0
        for signal_day, fund_value in history:
            fund_days.append(signal_day)
            fund_values.append(fund_value)
            while price_index + 1 < len(price_days) and price_days[price_index + 1] <= signal_day:
                price_index += 1
            if price_days[price_index] > signal_day:
                continue
            price_slice = [
                prices[day]
                for day in price_days[max(0, price_index - 21):price_index + 1]
            ]
            built = _sample_features(fund_values, price_slice)
            if built is None:
                continue
            features, context = built
            common = {
                "date": signal_day,
                "pair": name,
                "features": features,
                "context": context,
                "price_as_of": price_days[price_index],
                "validation": "PROVISIONAL_PIT" if any(code in name for code in ("AUD", "CHF")) else "PIT_CAUSAL",
            }
            if signal_day in prices and price_index + 1 < len(price_days):
                next_day = price_days[price_index + 1]
                next_return = math.log(prices[next_day] / prices[signal_day])
                labelled.append({
                    **common,
                    "next_date": next_day,
                    "target_up": 1 if next_return > 0 else 0,
                    "next_return_pct": (math.exp(next_return) - 1.0) * 100.0,
                })

        signal_day, fund_value = history[-1]
        valid_prices = [day for day in price_days if day <= signal_day]
        if valid_prices:
            latest_price_index = price_days.index(valid_prices[-1])
            built = _sample_features(
                [value for day, value in history if day <= signal_day],
                [prices[day] for day in price_days[:latest_price_index + 1]],
            )
            if built is not None:
                features, context = built
                latest.append({
                    "date": signal_day,
                    "pair": name,
                    "features": features,
                    "context": context,
                    "price_as_of": valid_prices[-1],
                    "validation": "PROVISIONAL_PIT"
                    if any(code in name for code in ("AUD", "CHF"))
                    else "PIT_CAUSAL",
                    "operational": bool(pair.get("operational", True)),
                    "data_status": pair.get("data_status", "CURRENT"),
                })
    labelled.sort(key=lambda row: (row["date"], row["pair"]))
    latest.sort(key=lambda row: row["pair"])
    return labelled, latest


def _fit_group_models(rows: list[dict]) -> list:
    x = np.asarray([row["features"] for row in rows], dtype=float)
    y = np.asarray([row["target_up"] for row in rows], dtype=int)
    models = []
    for columns in GROUPS.values():
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.35, class_weight="balanced", max_iter=1_000, random_state=41),
        )
        model.fit(x[:, columns], y)
        models.append(model)
    return models


def _group_logits(models: list, rows: list[dict]) -> np.ndarray:
    x = np.asarray([row["features"] for row in rows], dtype=float)
    return np.column_stack([
        model.decision_function(x[:, columns])
        for model, columns in zip(models, GROUPS.values())
    ])


def _grid_weights() -> list[np.ndarray]:
    units = round(1.0 / GRID_STEP)
    output: list[np.ndarray] = []
    for first in range(units + 1):
        for second in range(units - first + 1):
            for third in range(units - first - second + 1):
                fourth = units - first - second - third
                output.append(np.array([first, second, third, fourth], dtype=float) / units)
    return output


WEIGHT_GRID = _grid_weights()


def _top_fall_accuracy(rows: list[dict], scores: np.ndarray) -> tuple[float, float]:
    by_day: dict[date, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        fund = row.get("context", {}).get("fund")
        eligible = row.get("eligible_short", fund is not None and fund <= -25.0)
        if eligible:
            by_day[row["date"]].append(index)
    hits: list[int] = []
    returns: list[float] = []
    for indexes in by_day.values():
        chosen = min(indexes, key=lambda index: float(scores[index]))
        hits.append(1 if rows[chosen]["target_up"] == 0 else 0)
        returns.append(float(rows[chosen]["next_return_pct"]))
    return statistics.mean(hits), statistics.mean(returns)


def _choose_weights(train_rows: list[dict]) -> np.ndarray:
    dates = sorted({row["date"] for row in train_rows})
    split_year = dates[-1].year - 1
    inner_train = [row for row in train_rows if row["date"].year < split_year]
    validation = [row for row in train_rows if row["date"].year >= split_year]
    if len(inner_train) < 2_000 or len(validation) < 500:
        return WEIGHT_SCHEMES["IGUAL"].copy()
    models = _fit_group_models(inner_train)
    logits = _group_logits(models, validation)
    best = WEIGHT_SCHEMES["IGUAL"].copy()
    best_key = (-1.0, -999.0, -999.0)
    for weights in WEIGHT_GRID:
        scores = logits @ weights
        accuracy, average_return = _top_fall_accuracy(validation, scores)
        # Desempate favorece queda media maior e pesos menos concentrados.
        concentration = -float(np.sum(np.square(weights)))
        key = (accuracy, -average_return, concentration)
        if key > best_key:
            best_key = key
            best = weights.copy()
    return best


def _prediction_rows(rows: list[dict], scores: np.ndarray, scheme: str, fold: int) -> list[dict]:
    return [
        {
            "date": row["date"],
            "pair": row["pair"],
            "target_up": row["target_up"],
            "next_return_pct": row["next_return_pct"],
            "score": float(score),
            "scheme": scheme,
            "fold": fold,
            "eligible_short": bool(row["context"]["fund"] <= -25.0),
        }
        for row, score in zip(rows, scores)
    ]


def _summarize_predictions(rows: list[dict]) -> dict:
    rows = [row for row in rows if row.get("eligible_short", False)]
    if not rows:
        return {}
    by_day: dict[date, list[dict]] = defaultdict(list)
    for row in rows:
        by_day[row["date"]].append(row)
    rank_hits: dict[int, list[int]] = defaultdict(list)
    rank_returns: dict[int, list[float]] = defaultdict(list)
    top1_records: list[dict] = []
    for day_rows in by_day.values():
        for rank, row in enumerate(sorted(day_rows, key=lambda item: item["score"])[:5], 1):
            rank_hits[rank].append(1 if row["target_up"] == 0 else 0)
            rank_returns[rank].append(float(row["next_return_pct"]))
            if rank == 1:
                top1_records.append(row)
    all_hits = [1 if (row["score"] >= 0) == bool(row["target_up"]) else 0 for row in rows]
    top1_hits = rank_hits[1]
    top3_hits = [hit for rank in (1, 2, 3) for hit in rank_hits[rank]]
    top1_accuracy = statistics.mean(top1_hits)
    standard_error = math.sqrt(max(top1_accuracy * (1.0 - top1_accuracy), 0.0) / len(top1_hits))
    ci95 = (
        max(0.0, top1_accuracy - 1.96 * standard_error),
        min(1.0, top1_accuracy + 1.96 * standard_error),
    )
    selective = []
    strongest_first = sorted(top1_records, key=lambda row: row["score"])
    for coverage in (10, 20, 30, 50, 100):
        count = max(1, round(len(strongest_first) * coverage / 100.0))
        selected = strongest_first[:count]
        selective.append({
            "coverage_pct": coverage,
            "samples": len(selected),
            "accuracy": round(
                statistics.mean(1 if row["target_up"] == 0 else 0 for row in selected) * 100.0,
                2,
            ),
            "avg_return_pct": round(statistics.mean(row["next_return_pct"] for row in selected), 4),
        })
    years = sorted({row["date"].year for row in rows})
    positive_years = 0
    year_detail = []
    for year in years:
        year_rows = [row for row in rows if row["date"].year == year]
        accuracy, average_return = _top_fall_accuracy(
            year_rows, np.asarray([row["score"] for row in year_rows], dtype=float)
        )
        if accuracy > 0.5:
            positive_years += 1
        year_detail.append({
            "year": year,
            "top1_accuracy": round(accuracy * 100.0, 2),
            "top1_avg_return_pct": round(average_return, 4),
        })
    rank_stats = {
        str(rank): {
            "accuracy": round(statistics.mean(rank_hits[rank]) * 100.0, 2),
            "samples": len(rank_hits[rank]),
            "avg_return_pct": round(statistics.mean(rank_returns[rank]), 4),
        }
        for rank in sorted(rank_hits)
    }
    return {
        "rows": len(rows),
        "days": len(by_day),
        "directional_accuracy": round(statistics.mean(all_hits) * 100.0, 2),
        "top1_fall_accuracy": round(top1_accuracy * 100.0, 2),
        "top1_ci95_low": round(ci95[0] * 100.0, 2),
        "top1_ci95_high": round(ci95[1] * 100.0, 2),
        "top3_fall_accuracy": round(statistics.mean(top3_hits) * 100.0, 2),
        "top1_avg_return_pct": round(statistics.mean(rank_returns[1]), 4),
        "positive_years": positive_years,
        "tested_years": len(years),
        "rank_stats": rank_stats,
        "selective": selective,
        "year_detail": year_detail,
    }


def _walk_forward(labelled: list[dict]) -> tuple[dict[str, dict], list[dict], list[np.ndarray]]:
    years = sorted({row["date"].year for row in labelled})
    first_year = years[0] + MIN_TRAIN_YEARS
    predictions: dict[str, list[dict]] = defaultdict(list)
    learned_weights: list[np.ndarray] = []
    for test_year in [year for year in years if year >= first_year]:
        train = [row for row in labelled if row["date"].year < test_year]
        test = [row for row in labelled if row["date"].year == test_year]
        if len(train) < MIN_TRAIN_ROWS or not test:
            continue
        models = _fit_group_models(train)
        logits = _group_logits(models, test)
        learned = _choose_weights(train)
        learned_weights.append(learned)
        for scheme, weights in WEIGHT_SCHEMES.items():
            scores = np.asarray([row["features"][0] for row in test]) if weights is None else logits @ weights
            predictions[scheme].extend(_prediction_rows(test, scores, scheme, test_year))
        learned_scores = logits @ learned
        predictions["APRENDIDO"].extend(_prediction_rows(test, learned_scores, "APRENDIDO", test_year))
    summaries = {scheme: _summarize_predictions(rows) for scheme, rows in predictions.items()}
    return summaries, predictions.get("APRENDIDO", []), learned_weights


def _reason_text(group: str, context: dict, contribution: float) -> str:
    supports = contribution < 0
    if group == "fund_state":
        if supports and context["fund"] < 0:
            ending = "fraqueza favorece queda"
        elif supports:
            ending = "o modelo le como possivel reversao curta"
        elif context["fund"] > 0:
            ending = "strength argues against a fall"
        else:
            ending = "o modelo le como possivel reversao para cima"
        return f"FUND {context['fund']:+.1f}, persistence {context['persistence']:+.1f}: {ending}."
    if group == "fund_change":
        ending = "pressiona para baixo" if supports else "ainda sustenta o par"
        return f"FUND mudou {context['fund_d1']:+.1f} em 1d e {context['fund_d5']:+.1f} em 5d: {ending}."
    if group == "price_action":
        if supports and context["price_ret1_pct"] > 0:
            ending = "o modelo procura reversao da alta recente"
        elif supports:
            ending = "a pressao recente ainda favorece queda"
        elif context["price_ret1_pct"] > 0:
            ending = "the recent rally still argues against a fall"
        else:
            ending = "o modelo procura reversao para cima"
        return f"Preco {context['price_ret1_pct']:+.2f}% em 1d e {context['price_ret5_pct']:+.2f}% em 5d: {ending}."
    ending = "padrao combinado favorece queda" if supports else "divergencia pede cautela"
    return f"Relacao entre FUND e preco recente: {ending}."


def build_next_day_observations(
    pairs: list[dict],
    prices_by_pair: dict[str, dict[date, float]],
    generated_on: date,
) -> dict:
    all_labelled, latest = _build_samples(pairs, prices_by_pair)
    labelled = [row for row in all_labelled if row["validation"] == "PIT_CAUSAL"]
    if not labelled or not latest:
        raise RuntimeError("historico insuficiente para o modelo do proximo dia")

    summaries, learned_oos, fold_weights = _walk_forward(labelled)
    best_scheme = max(
        summaries,
        key=lambda scheme: summaries[scheme].get("top1_fall_accuracy", -1.0),
    )
    best_summary = summaries[best_scheme]
    final_weights = _choose_weights(labelled)
    final_models = _fit_group_models(labelled)
    current_rows = [
        row for row in latest
        if row["operational"] and row["context"]["fund"] <= -25.0
    ]
    current_logits = _group_logits(final_models, current_rows)
    if best_scheme == "FUND_ATUAL":
        observation_weights = np.array([1.0, 0.0, 0.0, 0.0])
        current_scores = np.asarray([row["features"][0] for row in current_rows], dtype=float)
        current_contributions = np.column_stack([
            current_scores,
            np.zeros((len(current_rows), 3), dtype=float),
        ])
    else:
        observation_weights = (
            final_weights if best_scheme == "APRENDIDO"
            else WEIGHT_SCHEMES[best_scheme]
        )
        current_scores = current_logits @ observation_weights
        current_contributions = current_logits * observation_weights

    learned_summary = summaries["APRENDIDO"]
    rank_stats = best_summary["rank_stats"]
    observations = []
    ordered = sorted(range(len(current_rows)), key=lambda index: float(current_scores[index]))
    for rank, index in enumerate(ordered[:5], 1):
        row = current_rows[index]
        group_contributions = current_contributions[index]
        reasons = []
        for group_index in np.argsort(group_contributions):
            group = list(GROUPS)[int(group_index)]
            if observation_weights[group_index] <= 0:
                continue
            reasons.append({
                "factor": GROUP_LABELS[group],
                "supports_fall": bool(group_contributions[group_index] < 0),
                "contribution": round(float(group_contributions[group_index]), 4),
                "text": _reason_text(group, row["context"], float(group_contributions[group_index])),
            })
        rank_history = rank_stats.get(str(rank), {})
        down_score = _sigmoid(-float(current_scores[index])) * 100.0
        observations.append({
            "rank": rank,
            "pair": row["pair"],
            "direction": "CAIR",
            "model": best_scheme,
            "signal_date": row["date"].isoformat(),
            "price_as_of": row["price_as_of"].isoformat(),
            "model_down_score": round(down_score, 1),
            "status": "SEM_EDGE_VALIDADO",
            "historical_accuracy": rank_history.get("accuracy"),
            "historical_samples": rank_history.get("samples"),
            "historical_avg_return_pct": rank_history.get("avg_return_pct"),
            "validation": row["validation"],
            "data_status": row["data_status"],
            "fund": round(row["context"]["fund"], 2),
            "fund_d1": round(row["context"]["fund_d1"], 2),
            "fund_d5": round(row["context"]["fund_d5"], 2),
            "price_ret1_pct": round(row["context"]["price_ret1_pct"], 3),
            "price_ret5_pct": round(row["context"]["price_ret5_pct"], 3),
            "reasons": reasons,
        })

    comparison = []
    for scheme in ("FUND_ATUAL", "FUND_PESADO", "IGUAL", "PRECO_PESADO", "APRENDIDO"):
        summary = summaries.get(scheme, {})
        weights = (
            final_weights if scheme == "APRENDIDO"
            else WEIGHT_SCHEMES.get(scheme)
        )
        comparison.append({
            "model": scheme,
            "weights": None if weights is None else {
                group: round(float(weight), 2)
                for group, weight in zip(GROUPS, weights)
            },
            **{key: value for key, value in summary.items() if key != "year_detail" and key != "rank_stats"},
        })

    median_weights = np.median(np.vstack(fold_weights), axis=0) if fold_weights else final_weights
    median_weights = median_weights / max(float(np.sum(median_weights)), 0.0001)
    first_label = min(row["date"] for row in labelled)
    last_label = max(row["date"] for row in labelled)
    return {
        "meta": {
            "status": "EXPERIMENT",
            "generated_on": generated_on.isoformat(),
            "target": "direction of the next daily ECB fixing",
            "signal_timing": "information available up to the close of D; target D for the next fixing",
            "lookahead": False,
            "selection": "the five lowest scores among operational pairs with FUND <= -25 (sell side)",
            "history_start": first_label.isoformat(),
            "history_end": last_label.isoformat(),
            "labelled_rows": len(labelled),
            "all_labelled_rows": len(all_labelled),
            "training_scope": "PIT_CAUSAL pairs only; AUD/CHF may be displayed, but they neither train nor validate the model",
            "validation": "walk-forward anual expansivo; pesos APRENDIDO escolhidos dentro de cada treino",
            "warning": "An OBSERVATION is not an entry. Confirm FUND, BO, REGION and ZOI; no direction is guaranteed.",
            "best_observed_model": best_scheme,
            "models_compared": len(summaries),
            "promotion_rule": "o limite inferior do IC 95% do melhor modelo deve superar 50%; depois aplicar nulo-do-maximo",
            "verdict": "SEM_EDGE_VALIDADO"
            if best_summary["top1_ci95_low"] <= 50.0
            else "EDGE_PROVISIONAL",
        },
        "weights": {
            "current": {group: round(float(weight), 2) for group, weight in zip(GROUPS, final_weights)},
            "walk_forward_median": {group: round(float(weight), 2) for group, weight in zip(GROUPS, median_weights)},
        },
        "comparison": comparison,
        "best_model": {"model": best_scheme, **best_summary},
        "observation_model": {"model": best_scheme, **best_summary},
        "observations": observations,
    }


def main() -> None:
    """Executa um relatorio local usando os mesmos dados do HCI FUND Radar."""
    import json
    import update_fund

    series = update_fund.read_all_yields()
    pit = {currency: update_fund.shift_pit(values) for currency, values in series.items()}
    rates = update_fund.read_fx_rates()
    pairs = []
    prices_by_pair = {}
    for name in update_fund.PAIR_ORDER:
        pair = update_fund.compute_pair(name, pit[name[:3]], pit[name[3:]])
        pair["operational"] = True
        pair["data_status"] = "CURRENT"
        pairs.append(pair)
        prices_by_pair[name] = update_fund.derive_pair_prices(name, rates)
    result = build_next_day_observations(pairs, prices_by_pair, date.today())
    compact = {
        "meta": result["meta"],
        "weights": result["weights"],
        "comparison": result["comparison"],
        "observations": result["observations"],
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
