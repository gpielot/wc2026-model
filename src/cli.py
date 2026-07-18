"""CLI entry point."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import pandas as pd

from src.config import DATA_PROCESSED, MODELS_DIR, PREDICTIONS


def cmd_ingest(_args):
    from src.ingest import run_all_ingest

    run_all_ingest()


def cmd_train(_args):
    import sys
    from src.features import build_match_features
    from src.features.player_skills import build_player_skills
    from src.features.styles import build_team_styles
    from src.features.chemistry import build_chemistry_features
    from src.models import train_and_save

    def log(msg):
        print(msg, flush=True)

    log("Building match features...")
    build_match_features()
    log("Building player skills...")
    build_player_skills()
    log("Building team styles...")
    build_team_styles()
    log("Building chemistry...")
    build_chemistry_features()
    log("Training ensemble...")
    metrics = train_and_save()
    log(f"Backtest metrics: {json.dumps(metrics, indent=2)}")


def cmd_train_models(_args):
    from src.models import train_and_save
    metrics = train_and_save()
    print(json.dumps(metrics, indent=2), flush=True)


def cmd_predict(args):
    from src.models import EnsembleModel
    from src.features.styles import style_matchup_boost, STYLE_DIMS
    from src.features.chemistry import chemistry_boost
    from src.simulate import build_match_probs_for_round, publish_predictions, run_bracket_sim
    import joblib
    import numpy as np

    feat = pd.read_parquet(DATA_PROCESSED / "match_features.parquet")
    model = EnsembleModel.load()

    styles = pd.read_parquet(DATA_PROCESSED / "team_styles.parquet") if (DATA_PROCESSED / "team_styles.parquet").exists() else pd.DataFrame()
    chemistry = pd.read_parquet(DATA_PROCESSED / "team_chemistry.parquet") if (DATA_PROCESSED / "team_chemistry.parquet").exists() else pd.DataFrame()

    W = np.zeros((len(STYLE_DIMS), len(STYLE_DIMS)))
    w_path = MODELS_DIR / "style_matchup_W.pkl"
    if w_path.exists():
        W = joblib.load(w_path)

    base_probs = build_match_probs_for_round(model, feat, args.round)

    # Enrich with style + chemistry
    from src.config import R32_FIXTURES
    enriched = {}
    for fix in R32_FIXTURES:
        fid = fix["id"]
        home, away = fix["home"], fix["away"]
        sb = style_matchup_boost(home, away, styles, W)
        cb = chemistry_boost(home, away, chemistry)
        base = base_probs[fid]
        enriched[fid] = model.predict_match(home, away, None, neutral=True, style_boost=sb, chem_boost=cb)
        enriched[f"{home}_vs_{away}"] = enriched[fid]

    sim = run_bracket_sim(enriched, n_sims=50_000)
    version = "v1" if args.round == "r16" else "v0"
    path = publish_predictions(args.round, enriched, sim, version=version)
    print(f"Published predictions to {path}")


def cmd_simulate(args):
    pred_file = PREDICTIONS / f"{args.round}_2026-06-30.json"
    if not pred_file.exists():
        print(f"No predictions found at {pred_file}. Run predict first.")
        return
    data = json.loads(pred_file.read_text())
    print(json.dumps(data.get("simulation", {}), indent=2))


def cmd_publish_round(args):
    """Publish predictions for r16, qf, sf, final."""
    from src.models import EnsembleModel
    from src.simulate import run_bracket_sim, build_match_probs_for_round
    from src.features.styles import style_matchup_boost, STYLE_DIMS
    from src.features.chemistry import chemistry_boost
    import joblib
    import numpy as np

    round_name = args.round
    model = EnsembleModel.load()
    feat = pd.read_parquet(DATA_PROCESSED / "match_features.parquet")
    styles = pd.read_parquet(DATA_PROCESSED / "team_styles.parquet") if (DATA_PROCESSED / "team_styles.parquet").exists() else pd.DataFrame()
    chemistry = pd.read_parquet(DATA_PROCESSED / "team_chemistry.parquet") if (DATA_PROCESSED / "team_chemistry.parquet").exists() else pd.DataFrame()
    W = joblib.load(MODELS_DIR / "style_matchup_W.pkl") if (MODELS_DIR / "style_matchup_W.pkl").exists() else np.zeros((len(STYLE_DIMS), len(STYLE_DIMS)))

    probs = build_match_probs_for_round(model, feat, "r32")

    for fix in __import__("src.config", fromlist=["R32_FIXTURES"]).R32_FIXTURES:
        home, away = fix["home"], fix["away"]
        sb = style_matchup_boost(home, away, styles, W)
        cb = chemistry_boost(home, away, chemistry)
        probs[fix["id"]] = model.predict_match(home, away, None, neutral=True, style_boost=sb, chem_boost=cb)

    sim = run_bracket_sim(probs, n_sims=100_000)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = PREDICTIONS / f"{round_name}_{ts}.json"
    payload = {
        "round": round_name,
        "model_version": "v2",
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "simulation": sim,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"Published {round_name} to {out}")


def cmd_betting(_args):
    from src.publish.betting import write_betting_report

    path = write_betting_report()
    print(f"Betting report written to {path}", flush=True)


def cmd_update_r16(_args):
    from src.publish.predict_r16 import publish_r16_predictions

    path = publish_r16_predictions(retrain=True, refresh_martj42=True)
    print(f"Knockout predictions published to {path}", flush=True)
    print(f"Summary: docs/SF_PREDICTIONS.md or docs/QF_PREDICTIONS.md", flush=True)


def cmd_final(_args):
    from src.publish.live_update import generate_final_writeup, publish_next_round

    for rnd in ("qf", "sf", "final"):
        publish_next_round(rnd)
    path = generate_final_writeup()
    print(f"Final writeup: {path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="WC2026 Prediction Model")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ingest", help="Download and process raw data")
    sub.add_parser("train", help="Train all models")
    sub.add_parser("train-models", help="Train ensemble only (features must exist)")
    p_pred = sub.add_parser("predict", help="Generate predictions for a round")
    p_pred.add_argument("--round", default="r32", choices=["r32", "r16", "qf", "sf", "final"])
    p_sim = sub.add_parser("simulate", help="Run bracket simulation")
    p_sim.add_argument("--round", default="r32")
    p_pub = sub.add_parser("publish", help="Publish round predictions")
    p_pub.add_argument("--round", default="r16", choices=["r16", "qf", "sf", "final"])
    sub.add_parser("betting", help="Generate betting edge report")
    sub.add_parser("final", help="Publish QF/SF/Final and write final summary")
    sub.add_parser("update-r16", help="Ingest knockout results, retrain, publish next round")
    sub.add_parser("update-qf", help="Alias for update-r16")
    sub.add_parser("update-sf", help="Alias for update-r16")
    sub.add_parser("update-final", help="Alias for update-r16")

    args = parser.parse_args()
    cmds = {
        "ingest": cmd_ingest,
        "train": cmd_train,
        "train-models": cmd_train_models,
        "predict": cmd_predict,
        "simulate": cmd_simulate,
        "publish": cmd_publish_round,
        "betting": cmd_betting,
        "update-r16": cmd_update_r16,
        "update-qf": cmd_update_r16,
        "update-sf": cmd_update_r16,
        "update-final": cmd_update_r16,
        "final": cmd_final,
    }
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
