"""Betting edge analysis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DOCS, PREDICTIONS


# Illustrative market odds (decimal) for R32 — replace with live API when available
SAMPLE_MARKET_ODDS = {
    "r32_1": {"home": 1.85, "draw": 3.40, "away": 4.50},  # Netherlands vs Japan
    "r32_2": {"home": 1.45, "draw": 4.20, "away": 7.00},  # Argentina vs Senegal
    "r32_3": {"home": 1.55, "draw": 3.80, "away": 6.00},  # France vs Mexico
    "r32_4": {"home": 1.70, "draw": 3.60, "away": 5.00},  # England vs Colombia
    "r32_5": {"home": 1.35, "draw": 4.80, "away": 9.00},  # Brazil vs Ecuador
    "r32_6": {"home": 1.90, "draw": 3.30, "away": 4.20},  # Germany vs USA
    "r32_7": {"home": 1.50, "draw": 4.00, "away": 6.50},  # Spain vs Morocco
    "r32_8": {"home": 1.75, "draw": 3.50, "away": 4.80},  # Portugal vs Uruguay
    "r32_9": {"home": 2.10, "draw": 3.20, "away": 3.60},  # Belgium vs Switzerland
    "r32_10": {"home": 2.00, "draw": 3.25, "away": 3.80},  # Croatia vs Denmark
    "r32_11": {"home": 1.65, "draw": 3.70, "away": 5.20},  # Italy vs Austria
    "r32_12": {"home": 2.20, "draw": 3.10, "away": 3.40},  # Poland vs South Korea
}


def odds_to_implied_probs(odds: dict) -> dict:
    """Convert decimal odds to normalized implied probabilities."""
    raw = {k: 1 / v for k, v in odds.items()}
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def compute_edges(model_probs: dict, market_probs: dict, threshold: float = 0.05) -> list[dict]:
    """Find value bets where model exceeds market by threshold."""
    edges = []
    for outcome in ["home", "draw", "away"]:
        mp = model_probs.get(f"p_{outcome}", 0)
        mk = market_probs.get(outcome, 0)
        edge = mp - mk
        if edge > threshold:
            edges.append(
                {
                    "outcome": outcome,
                    "model_prob": round(mp, 4),
                    "market_prob": round(mk, 4),
                    "edge": round(edge, 4),
                    "flag": "VALUE" if edge > threshold else "",
                }
            )
    return edges


def historical_calibration_report() -> dict:
    """Report backtest calibration from saved metrics."""
    from src.config import MODELS_DIR

    path = MODELS_DIR / "backtest_metrics.json"
    if not path.exists():
        return {"note": "Run train first for backtest metrics"}
    return json.loads(path.read_text())


def write_betting_report(prediction_file: Path | None = None) -> Path:
    """Generate betting_edge_report.md."""
    pred_file = prediction_file or PREDICTIONS / "r32_2026-06-30.json"
    if not pred_file.exists():
        raise FileNotFoundError(f"Predictions not found: {pred_file}")

    preds = json.loads(pred_file.read_text())
    cal = historical_calibration_report()

    lines = [
        "# Betting Edge Report",
        "",
        "> **Disclaimer:** This is not financial advice. Markets are efficient.",
        "> Historical backtests on international football rarely show sustained positive ROI.",
        "> Use this for entertainment and model calibration assessment only.",
        "",
        f"**Generated from:** `{pred_file.name}`",
        f"**Locked at:** {preds.get('locked_at', 'N/A')}",
        "",
        "## Historical Calibration (Backtest)",
        "",
    ]

    if "folds" in cal:
        for fold in cal["folds"]:
            lines.append(
                f"- **{fold['year']}**: log_loss={fold['log_loss']:.4f}, "
                f"brier={fold['brier']:.4f}, n={fold['n_matches']}"
            )
    else:
        lines.append(f"- {cal.get('note', 'No metrics')}")

    lines.extend(["", "## Round of 32 — Model vs Market", ""])
    lines.append("| Match | Outcome | Model | Market | Edge | Flag |")
    lines.append("|-------|---------|-------|--------|------|------|")

    value_count = 0
    for mid, match in preds.get("match_predictions", {}).items():
        home = match["home"]
        away = match["away"]
        model_p = {"p_home": match["p_home"], "p_draw": match["p_draw"], "p_away": match["p_away"]}
        odds = SAMPLE_MARKET_ODDS.get(mid, {"home": 2.0, "draw": 3.2, "away": 3.5})
        market_p = odds_to_implied_probs(odds)
        market_named = {"p_home": market_p["home"], "p_draw": market_p["draw"], "p_away": market_p["away"]}

        for outcome, label in [("home", home), ("draw", "Draw"), ("away", away)]:
            mp = model_p[f"p_{outcome}"]
            mk = market_named[f"p_{outcome}"]
            edge = mp - mk
            flag = "**VALUE**" if edge > 0.05 else ""
            if flag:
                value_count += 1
            lines.append(
                f"| {home} vs {away} | {label} | {mp:.1%} | {mk:.1%} | {edge:+.1%} | {flag} |"
            )

    lines.extend(
        [
            "",
            f"**Value flags (edge > 5%):** {value_count}",
            "",
            "## Honest Assessment",
            "",
            "- Bookmakers incorporate injury news, insider squad info, and sharper closing lines.",
            "- Our model uses public data only; expect **zero or negative long-run ROI** if blindly betting value flags.",
            "- The primary value of this report is **calibration checking**: do 60% predictions win ~60% of the time?",
            "- Recommended use: share probabilities with friends, compare against your own intuition.",
            "",
            "## Champion Odds (Model Simulation)",
            "",
        ]
    )

    champ = preds.get("simulation", {}).get("champion_probs", {})
    for team, prob in list(champ.items())[:10]:
        lines.append(f"- **{team}**: {prob:.1%}")

    DOCS.mkdir(parents=True, exist_ok=True)
    out = DOCS / "betting_edge_report.md"
    out.write_text("\n".join(lines))
    return out
