"""Basic tests for WC2026 model."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_dynamic_elo():
    from src.features import DynamicElo

    elo = DynamicElo()
    matches = pd.DataFrame(
        [
            {"home": "A", "away": "B", "result": "H", "neutral": True, "date": pd.Timestamp("2020-01-01"), "match_id": "1", "home_goals": 2, "away_goals": 1, "tournament": ""},
            {"home": "B", "away": "C", "result": "A", "neutral": True, "date": pd.Timestamp("2020-02-01"), "match_id": "2", "home_goals": 0, "away_goals": 1, "tournament": ""},
        ]
    )
    feat = elo.fit_history(matches)
    assert len(feat) == 2
    assert feat.iloc[1]["home_elo"] != 1500  # B should have updated


def test_dixon_coles_probs_sum_to_one():
    from src.models import DixonColesModel

    dc = DixonColesModel()
    dc.attack = {"Home": 0.1, "Away": -0.1}
    dc.defense = {"Home": 0.0, "Away": 0.0}
    probs = dc.predict_probs("Home", "Away", neutral=True)
    assert abs(probs["p_home"] + probs["p_draw"] + probs["p_away"] - 1.0) < 0.01


def test_odds_to_implied():
    from src.publish.betting import odds_to_implied_probs

    probs = odds_to_implied_probs({"home": 2.0, "draw": 3.0, "away": 4.0})
    assert abs(sum(probs.values()) - 1.0) < 0.001


def test_monte_carlo_runs():
    from src.simulate import run_bracket_sim

    probs = {
        "r32_1": {"p_home": 0.5, "p_draw": 0.25, "p_away": 0.25},
    }
    # Need all r32 fixtures — use minimal mock
    from src.config import R32_FIXTURES

    match_probs = {}
    for fix in R32_FIXTURES:
        match_probs[fix["id"]] = {"p_home": 0.45, "p_draw": 0.25, "p_away": 0.30}

    result = run_bracket_sim(match_probs, n_sims=1000, seed=42)
    assert result["n_sims"] == 1000
    assert len(result["champion_probs"]) > 0
