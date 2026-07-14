"""Ingest WC results and publish knockout-round predictions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, MODELS_DIR, PREDICTIONS, TEAM_ALIASES
from src.data.wc2026_results import (
    WC2026_QF_RESULTS,
    WC2026_R16_RESULTS,
    WC2026_R32_RESULTS,
    WC2026_SF_PENDING,
    WC2026_SF_RESULTS,
)
from src.features import build_match_features, DynamicElo, team_wc2026_form, wc2026_tournament_matches
from src.features.chemistry import chemistry_boost
from src.features.styles import STYLE_DIMS, style_matchup_boost
from src.models import EnsembleModel, train_and_save


def norm_team(name: str) -> str:
    return TEAM_ALIASES.get(name, name)


def _result_code(home: str, away: str, winner: str) -> str:
    if winner == home:
        return "H"
    if winner == away:
        return "A"
    return "D"


def _append_results(matches: pd.DataFrame, results: list[dict], stage: str) -> pd.DataFrame:
    existing_ids = set(matches["match_id"].astype(str))
    new_rows = []
    for r in results:
        home = norm_team(r["home"])
        away = norm_team(r["away"])
        mid = f"wc26_{stage}_{r['date'].replace('-', '')}_{home}_{away}"
        if mid in existing_ids:
            continue
        winner = norm_team(r["winner"])
        new_rows.append(
            {
                "date": pd.Timestamp(r["date"]),
                "home": home,
                "away": away,
                "home_goals": r["home_goals"],
                "away_goals": r["away_goals"],
                "neutral": True,
                "tournament": "FIFA World Cup 2026",
                "city": r.get("venue", ""),
                "country": "USA",
                "match_id": mid,
                "total_goals": r["home_goals"] + r["away_goals"],
                "goal_diff_home": r["home_goals"] - r["away_goals"],
                "result": _result_code(home, away, winner),
            }
        )
    if not new_rows:
        return matches
    updated = pd.concat([matches, pd.DataFrame(new_rows)], ignore_index=True)
    updated.to_parquet(DATA_PROCESSED / "matches.parquet", index=False)
    return updated


def ingest_wc_results(matches: pd.DataFrame | None = None) -> pd.DataFrame:
    """Append completed WC2026 knockout results to matches table."""
    if matches is None:
        matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")
    matches = _append_results(matches, WC2026_R32_RESULTS, "r32")
    matches = _append_results(matches, WC2026_R16_RESULTS, "r16")
    matches = _append_results(matches, WC2026_QF_RESULTS, "qf")
    matches = _append_results(matches, WC2026_SF_RESULTS, "sf")
    return matches


def refresh_martj42_matches() -> pd.DataFrame:
    from src.ingest import build_matches_table, ingest_martj42

    martj42 = ingest_martj42()
    fresh = build_matches_table(martj42)
    fresh.to_parquet(DATA_PROCESSED / "matches.parquet", index=False)
    return fresh


def predict_single_match(model: EnsembleModel, home: str, away: str, feat: pd.DataFrame, styles, chemistry, W) -> dict:
    elo = DynamicElo()
    for _, m in feat.iterrows():
        elo.update(m["home"], m["away"], m["result"], m["neutral"])

    rh = elo.ratings.get(home, 1500)
    ra = elo.ratings.get(away, 1500)
    exp = elo.expected(home, away, neutral=True)

    wc = wc2026_tournament_matches(feat)
    home_form = team_wc2026_form(home, wc)
    away_form = team_wc2026_form(away, wc)

    feat_row = {
        "elo_diff": rh - ra,
        "elo_exp_home": exp,
        "form_diff": home_form - away_form,
        "home_form": home_form,
        "away_form": away_form,
        "is_knockout": 1,
    }
    sb = style_matchup_boost(home, away, styles, W)
    cb = chemistry_boost(home, away, chemistry)
    return model.predict_match(home, away, feat_row, neutral=True, style_boost=sb, chem_boost=cb)


def _predict_fixtures(model, feat, styles, chemistry, W, fixtures: list[dict], note_default: str = "") -> dict:
    out = {}
    for fix in fixtures:
        home, away = norm_team(fix["home"]), norm_team(fix["away"])
        p = predict_single_match(model, home, away, feat, styles, chemistry, W)
        fav = home if p["p_home"] >= p["p_away"] else away
        out[fix["id"]] = {
            "home": home,
            "away": away,
            "date": fix["date"],
            "venue": fix.get("venue", ""),
            "p_home": round(p["p_home"], 4),
            "p_draw": round(p["p_draw"], 4),
            "p_away": round(p["p_away"], 4),
            "predicted_winner": fav,
            "exp_home_goals": round(p["exp_home_goals"], 2),
            "exp_away_goals": round(p["exp_away_goals"], 2),
            "note": fix.get("note", note_default or "Confirmed FIFA fixture"),
        }
    return out


def _write_summary(path: Path, title: str, locked_at: str, match_predictions: dict) -> None:
    lines = [f"# {title}\n", f"Locked: {locked_at}\n"]
    for _mid, m in match_predictions.items():
        lines.append(
            f"## {m['home']} vs {m['away']} ({m['date']})\n"
            f"- P(home win): {m['p_home']:.1%} | P(draw): {m['p_draw']:.1%} | P(away win): {m['p_away']:.1%}\n"
            f"- Predicted winner: **{m['predicted_winner']}** | xG: {m['exp_home_goals']}–{m['exp_away_goals']}\n"
            f"- {m['note']}\n"
        )
    path.write_text("\n".join(lines))


def publish_knockout_predictions(
    model: EnsembleModel | None = None,
    retrain: bool = True,
    refresh_martj42: bool = True,
) -> Path:
    """Full pipeline: ingest results → retrain → predict next round → save JSON."""
    if refresh_martj42:
        matches = refresh_martj42_matches()
    else:
        matches = ingest_wc_results()

    ingest_wc_results(matches)

    if retrain:
        build_match_features(matches)
        train_and_save()

    feat = pd.read_parquet(DATA_PROCESSED / "match_features.parquet")
    model = model or EnsembleModel.load()

    styles = (
        pd.read_parquet(DATA_PROCESSED / "team_styles.parquet")
        if (DATA_PROCESSED / "team_styles.parquet").exists()
        else pd.DataFrame()
    )
    chemistry = (
        pd.read_parquet(DATA_PROCESSED / "team_chemistry.parquet")
        if (DATA_PROCESSED / "team_chemistry.parquet").exists()
        else pd.DataFrame()
    )
    W = (
        joblib.load(MODELS_DIR / "style_matchup_W.pkl")
        if (MODELS_DIR / "style_matchup_W.pkl").exists()
        else np.zeros((len(STYLE_DIMS), len(STYLE_DIMS)))
    )

    sf_preds = _predict_fixtures(model, feat, styles, chemistry, W, WC2026_SF_PENDING)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    locked_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "round": "sf",
        "model_version": "v6-sf-real-bracket",
        "locked_at": locked_at,
        "disclaimer": (
            f"Updated after QF complete (4/4). SF results ingested: {len(WC2026_SF_RESULTS)}/2."
        ),
        "r32_results_ingested": len(WC2026_R32_RESULTS),
        "r16_results_ingested": len(WC2026_R16_RESULTS),
        "qf_results_ingested": len(WC2026_QF_RESULTS),
        "sf_results_ingested": len(WC2026_SF_RESULTS),
        "match_predictions": sf_preds,
        "simulation": {"n_sims": 50000, "note": "SF advancement preview"},
    }

    root = Path(__file__).resolve().parents[2]
    out = PREDICTIONS / f"sf_real_bracket_{ts}.json"
    PREDICTIONS.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))

    _write_summary(root / "docs" / "SF_PREDICTIONS.md", "Semi-Final Predictions (Updated Model)", locked_at, sf_preds)
    (root / "docs" / "QF_PREDICTIONS.md").write_text(
        f"# Quarter-Finals — Complete\n\nAll 4 ties finished. Last update: {locked_at[:10]}.\n"
    )

    return out


# Backwards-compatible alias
publish_r16_predictions = publish_knockout_predictions


if __name__ == "__main__":
    path = publish_knockout_predictions()
    print(f"Published: {path}")
