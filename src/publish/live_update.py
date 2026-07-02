"""Live update pipeline for knockout rounds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import DATA_PROCESSED, MODELS_DIR, PREDICTIONS


ROUND_SCHEDULE = {
    "r16": {"publish_by": "2026-07-03", "matches_start": "2026-07-04"},
    "qf": {"publish_by": "2026-07-08", "matches_start": "2026-07-09"},
    "sf": {"publish_by": "2026-07-13", "matches_start": "2026-07-14"},
    "final": {"publish_by": "2026-07-18", "matches_start": "2026-07-19"},
}


def update_after_round(completed_round: str, results: list[dict]) -> None:
    """
    Bayesian-style update after a round completes.
    results: [{"home": "...", "away": "...", "home_goals": 2, "away_goals": 1}, ...]
    """
    matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")
    new_rows = []
    for r in results:
        new_rows.append(
            {
                "date": pd.Timestamp.now(),
                "home": r["home"],
                "away": r["away"],
                "home_goals": r["home_goals"],
                "away_goals": r["away_goals"],
                "neutral": True,
                "tournament": "FIFA World Cup 2026",
                "city": r.get("city", ""),
                "country": "USA",
            }
        )
    new_df = pd.DataFrame(new_rows)

    def outcome(row):
        if row["home_goals"] > row["away_goals"]:
            return "H"
        if row["home_goals"] < row["away_goals"]:
            return "A"
        return "D"

    new_df["result"] = new_df.apply(outcome, axis=1)
    new_df["match_id"] = new_df.apply(
        lambda r: f"{r['date'].strftime('%Y%m%d')}_{r['home']}_{r['away']}", axis=1
    )
    new_df["total_goals"] = new_df["home_goals"] + new_df["away_goals"]
    new_df["goal_diff_home"] = new_df["home_goals"] - new_df["away_goals"]

    updated = pd.concat([matches, new_df], ignore_index=True)
    updated.to_parquet(DATA_PROCESSED / "matches.parquet", index=False)

    # Retrain
    from src.features import build_match_features
    from src.models import train_and_save

    build_match_features(updated)
    train_and_save()

    log = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_round": completed_round,
        "n_new_matches": len(new_rows),
    }
    log_path = PREDICTIONS / "update_log.json"
    existing = json.loads(log_path.read_text()) if log_path.exists() else []
    existing.append(log)
    log_path.write_text(json.dumps(existing, indent=2))


def publish_next_round(round_name: str) -> Path:
    """Retrain and publish predictions for the next knockout round."""
    from src.cli import cmd_publish_round
    import argparse

    args = argparse.Namespace(round=round_name)
    cmd_publish_round(args)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return PREDICTIONS / f"{round_name}_{ts}.json"


def generate_final_writeup() -> Path:
    """Compile final tournament writeup."""
    from src.publish.betting import write_betting_report

    write_betting_report()

    pred_files = sorted(PREDICTIONS.glob("*.json"))
    lines = [
        "# World Cup 2026 — Final Model Writeup",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Prediction Timeline",
        "",
    ]
    for pf in pred_files:
        if pf.name == "update_log.json":
            continue
        data = json.loads(pf.read_text())
        lines.append(f"- `{pf.name}` — locked {data.get('locked_at', '?')[:19]}, round={data.get('round', '?')}")

    lines.extend(["", "## Champion Probabilities (Latest)", ""])
    if pred_files:
        latest = json.loads(pred_files[-1].read_text())
        for team, prob in list(latest.get("simulation", {}).get("champion_probs", {}).items())[:8]:
            lines.append(f"- {team}: {prob:.1%}")

    lines.extend(["", "See [METHODOLOGY.md](METHODOLOGY.md) and [betting_edge_report.md](betting_edge_report.md)."])

    out = Path(__file__).resolve().parents[2] / "docs" / "FINAL_WRITEUP.md"
    out.write_text("\n".join(lines))
    return out
