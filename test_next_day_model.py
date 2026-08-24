#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from datetime import date

import numpy as np

import next_day_model as model
import pre_fund_model


class NextDayModelTests(unittest.TestCase):
    def test_weight_schemes_are_valid(self) -> None:
        for weights in model.WEIGHT_SCHEMES.values():
            if weights is not None:
                self.assertAlmostEqual(float(np.sum(weights)), 1.0)
                self.assertTrue(bool(np.all(weights >= 0.0)))

    def test_top_fall_ignores_pairs_without_bearish_fund(self) -> None:
        rows = [
            {
                "date": date(2026, 1, 2), "target_up": 1,
                "next_return_pct": 1.0, "context": {"fund": 10.0},
            },
            {
                "date": date(2026, 1, 2), "target_up": 0,
                "next_return_pct": -0.5, "context": {"fund": -30.0},
            },
        ]
        accuracy, average_return = model._top_fall_accuracy(rows, np.array([-10.0, 1.0]))
        self.assertEqual(accuracy, 1.0)
        self.assertEqual(average_return, -0.5)

    def test_generated_snapshot_respects_house_rules(self) -> None:
        path = model.__file__.replace("next_day_model.py", "data\\fund_snapshot.json")
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)["next_day"]
        self.assertFalse(data["meta"]["lookahead"])
        self.assertEqual(data["meta"]["verdict"], "SEM_EDGE_VALIDADO")
        self.assertEqual(data["meta"]["models_compared"], 5)
        self.assertLessEqual(data["best_model"]["top1_ci95_low"], 50.0)
        self.assertTrue(all(row["fund"] <= -25.0 for row in data["observations"]))

    def test_pre_fund_snapshot_catches_january_examples(self) -> None:
        path = model.__file__.replace("next_day_model.py", "data\\fund_snapshot.json")
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)["pre_fund"]
        self.assertFalse(data["meta"]["lookahead"])
        self.assertGreater(
            data["best_model"]["top1_transition_rate"],
            data["best_model"]["baseline_transition_rate"] * 3.0,
        )
        audits = {row["pair"]: row for row in data["case_audits"]}
        self.assertEqual(audits["NZDJPY"]["rank"], 1)
        self.assertEqual(audits["EURJPY"]["rank"], 2)
        self.assertTrue(audits["NZDJPY"]["transition_happened"])
        self.assertTrue(audits["EURJPY"]["transition_happened"])
        self.assertTrue(all(row["fund"] > -25.0 for row in data["observations"]))

    def test_pre_fund_weight_schemes_are_valid(self) -> None:
        for weights in pre_fund_model.WEIGHT_SCHEMES.values():
            self.assertAlmostEqual(float(np.sum(weights)), 1.0)
            self.assertTrue(bool(np.all(weights >= 0.0)))


if __name__ == "__main__":
    unittest.main()
