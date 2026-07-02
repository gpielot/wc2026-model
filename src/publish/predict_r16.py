"""Update model with R32 results and publish real Round of 16 predictions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, MODELS_DIR, PREDICTIONS, TEAM_ALIASES
from src.data.wc2026_results import (
    WC2026_R16_FIXTURES,
    WC2026_R16_PENDING,
    WC2026_R32_PENDING,
    WC2026_R32_RESULTS,
)
from src.features import build_match_features, DynamicElo
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


def ingest_r32_results(matches: pd.DataFrame | None = None) -> pd.DataFrame:
    """Append completed WC2026 R32 results to matches table."""
    if matches is None:
        matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")

    existing_ids = set(matches["match_id"].astype(str))
    new_rows = []

    for r in WC2026_R32_RESULTS:
        home = norm_team(r["home"])
        away = norm_team(r["away"])
        mid = f"wc26_{r['date'].replace('-', '')}_{home}_{away}"
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
                "city": "",
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


def refresh_martj42_matches() -> pd.DataFrame:
    """Re-download martj42 and merge into matches table."""
    from src.ingest import build_matches_table, ingest_martj42

    martj42 = ingest_martj42()
    fresh = build_matches_table(martj42)
    fresh.to_parquet(DATA_PROCESSED / "matches.parquet", index=False)
    return fresh


def predict_single_match(model: EnsembleModel, home: str, away: str, feat: pd.DataFrame, styles, chemistry, W) -> dict:
    """Predict one match with Elo features + style/chemistry."""
    elo = DynamicElo()
    for _, m in feat.iterrows():
        elo.update(m["home"], m["away"], m["result"], m["neutral"])

    rh = elo.ratings.get(home, 1500)
    ra = elo.ratings.get(away, 1500)
    exp = elo.expected(home, away, neutral=True)

    # Recent WC form
    wc = feat[(feat["tournament"].astype(str).str.contains("World Cup 2026", na=False))]
    def form(team):
        pts = []
        for _, m in wc.iterrows():
            if m["home"] == team:
                pts.append(3 if m["result"] == "H" else (1 if m["result"] == "D" else 0))
            elif m["away"] == team:
                pts.append(3 if m["result"] == "A" else (1 if m["result"] == "D" else 0))
        return np.mean(pts[-5:]) if pts else 1.5

    feat_row = {
        "elo_diff": rh - ra,
        "elo_exp_home": exp,
        "form_diff": form(home) - form(away),
        "home_form": form(home),
        "away_form": form(away),
        "is_knockout": 1,
    }
    sb = style_matchup_boost(home, away, styles, W)
    cb = chemistry_boost(home, away, chemistry)
    return model.predict_match(home, away, feat_row, neutral=True, style_boost=sb, chem_boost=cb)


def predict_pending_r32(model, feat, styles, chemistry, W) -> dict[str, dict]:
    """Model predictions for remaining R32 ties."""
    out = {}
    for fix in WC2026_R32_PENDING:
        home, away = norm_team(fix["home"]), norm_team(fix["away"])
        p = predict_single_match(model, home, away, feat, styles, chemistry, W)
        fav = home if p["p_home"] > p["p_away"] else away
        out[fix["id"]] = {
            "fixture": fix,
            "home": home,
            "away": away,
            "probabilities": p,
            "predicted_winner": fav,
            "p_home": round(p["p_home"], 4),
            "p_draw": round(p["p_draw"], 4),
            "p_away": round(p["p_away"], 4),
        }
        out[f"{home}_vs_{away}"] = p
    return out


def resolve_pending_r16(pending_r32_preds: dict) -> list[dict]:
    """Build probable R16 fixtures from pending R32 model winners."""
    id_to_winner = {
        fid: pending_r32_preds[fid]["predicted_winner"]
        for fid in pending_r32_preds
        if fid.startswith("r32_")
    }

    resolved = []
    for slot in WC2026_R16_PENDING:
        deps = slot["depends_on"]
        if len(deps) == 2:
            (id_a, _), (id_b, _) = deps
            # Match 93: Portugal/Croatia vs Spain/Austria — home is winner 14, away is winner 13 per FIFA bracket
            if slot["id"] == "r16_6":
                home, away = id_to_winner.get("r32_14", "Portugal"), id_to_winner.get("r32_13", "Spain")
            elif slot["id"] == "r16_7":
                home, away = id_to_winner.get("r32_17", "Argentina"), id_to_winner.get("r32_16", "Australia")
            elif slot["id"] == "r16_8":
                home, away = id_to_winner.get("r32_18", "Colombia"), id_to_winner.get("r32_15", "Switzerland")
            else:
                home, away = id_to_winner.get(deps[0][0], "TBD"), id_to_winner.get(deps[1][0], "TBD")
            resolved.append(
                {
                    "id": slot["id"],
                    "date": slot["date"],
                    "home": home,
                    "away": away,
                    "venue": slot["venue"],
                    "note": f"Probable — depends on R32 results ({slot['home_slot']} vs {slot['away_slot']})",
                }
            )
    return resolved


def publish_r16_predictions(
    model: EnsembleModel | None = None,
    retrain: bool = True,
    refresh_martj42: bool = True,
) -> Path:
    """Full pipeline: ingest R32 → retrain → predict R16 → save JSON."""
    if refresh_martj42:
        matches = refresh_martj42_matches()
    else:
        matches = ingest_r32_results()

    if retrain:
        build_match_features(matches)
        train_and_save()

    feat = pd.read_parquet(DATA_PROCESSED / "match_features.parquet")
    model = model or EnsembleModel.load()

    styles = pd.read_parquet(DATA_PROCESSED / "team_styles.parquet") if (DATA_PROCESSED / "team_styles.parquet").exists() else pd.DataFrame()
    chemistry = pd.read_parquet(DATA_PROCESSED / "team_chemistry.parquet") if (DATA_PROCESSED / "team_chemistry.parquet").exists() else pd.DataFrame()
    W = joblib.load(MODELS_DIR / "style_matchup_W.pkl") if (MODELS_DIR / "style_matchup_W.pkl").exists() else np.zeros((len(STYLE_DIMS), len(STYLE_DIMS)))

    pending_r32 = predict_pending_r32(model, feat, styles, chemistry, W)
    probable_r16 = resolve_pending_r16(pending_r32)
    all_r16 = WC2026_R16_FIXTURES + probable_r16

    match_predictions = {}
    for fix in all_r16:
        home, away = norm_team(fix["home"]), norm_team(fix["away"])
        p = predict_single_match(model, home, away, feat, styles, chemistry, W)
        fav = home if p["p_home"] >= p["p_away"] else away
        match_predictions[fix["id"]] = {
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
            "note": fix.get("note", "Confirmed FIFA fixture"),
        }

    # Simple R16 advancement sim
    champ_counts: dict[str, float] = {}
    for _ in range(50_000):
        winners = []
        for fix in all_r16:
            p = match_predictions[fix["id"]]
            probs = {"p_home": p["p_home"], "p_draw": p["p_draw"], "p_away": p["p_away"]}
            r = np.random.random()
            if r < probs["p_home"]:
                winners.append(fix["home"])
            elif r < probs["p_home"] + probs["p_draw"]:
                winners.append(fix["home"] if np.random.random() < 0.5 else fix["away"])
            else:
                winners.append(fix["away"])
        if winners:
            champ_counts[winners[0]] = champ_counts.get(winners[0], 0) + 1  # placeholder

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = {
        "round": "r16",
        "model_version": "v3-r16-real-bracket",
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Updated after R32 results through July 1. Remaining R32 ties use model-predicted winners for probable R16 slots.",
        "r32_results_ingested": len(WC2026_R32_RESULTS),
        "pending_r32_predictions": {k: v for k, v in pending_r32.items() if not k.endswith("_vs_")},
        "match_predictions": match_predictions,
        "simulation": {
            "n_sims": 50000,
            "note": "R16-only advancement preview",
        },
    }

    out = PREDICTIONS / f"r16_real_bracket_{ts}.json"
    PREDICTIONS.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))

    # Also write human-readable summary
    lines = ["# Round of 16 Predictions (Updated Model)\n", f"Locked: {payload['locked_at']}\n"]
    for mid, m in match_predictions.items():
        lines.append(
            f"## {m['home']} vs {m['away']} ({m['date']})\n"
            f"- P(home win): {m['p_home']:.1%} | P(draw): {m['p_draw']:.1%} | P(away win): {m['p_away']:.1%}\n"
            f"- Predicted winner: **{m['predicted_winner']}** | xG: {m['exp_home_goals']}–{m['exp_away_goals']}\n"
            f"- {m['note']}\n"
        )
    summary_path = Path(__file__).resolve().parents[2] / "docs" / "R16_PREDICTIONS.md"
    summary_path.write_text("\n".join(lines))

    return out


if __name__ == "__main__":
    path = publish_r16_predictions()
    print(f"Published: {path}")
