"""Monte Carlo tournament bracket simulation."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.config import PREDICTIONS, R16_BRACKET, R32_FIXTURES
from src.models import EnsembleModel


def simulate_match(probs: dict, rng: np.random.Generator) -> str:
    """Return 'home' or 'away' winner; handle draw via coin flip."""
    r = rng.random()
    if r < probs["p_home"]:
        return "home"
    if r < probs["p_home"] + probs["p_draw"]:
        return "draw"
    return "away"


def resolve_winner(home: str, away: str, probs: dict, rng: np.random.Generator) -> str:
    outcome = simulate_match(probs, rng)
    if outcome == "home":
        return home
    if outcome == "away":
        return away
    # Draw in knockout -> penalties (50/50)
    return home if rng.random() < 0.5 else away


def _default_probs() -> dict:
    return {"p_home": 0.45, "p_draw": 0.25, "p_away": 0.30}


def _advance_round(teams: list[str], match_probs: dict, rng: np.random.Generator, prefix: str) -> dict[str, str]:
    """Pair teams for knockout round; odd team out receives a bye."""
    winners: dict[str, str] = {}
    i = 0
    match_num = 1
    while i < len(teams):
        if i + 1 < len(teams):
            home, away = teams[i], teams[i + 1]
            probs = match_probs.get(f"{home}_vs_{away}", _default_probs())
            winners[f"{prefix}_{match_num}"] = resolve_winner(home, away, probs, rng)
            i += 2
        else:
            winners[f"{prefix}_{match_num}"] = teams[i]
            i += 1
        match_num += 1
    return winners


def run_bracket_sim(
    match_probs: dict[str, dict],
    n_sims: int = 100_000,
    seed: int = 42,
) -> dict:
    """Simulate R32 through Final."""
    rng = np.random.default_rng(seed)
    r32_winners = {f["id"]: [] for f in R32_FIXTURES}
    champion_counts: dict[str, int] = {}
    qf_counts: dict[str, int] = {}
    sf_counts: dict[str, int] = {}

    for _ in range(n_sims):
        winners = {}
        for fix in R32_FIXTURES:
            fid = fix["id"]
            probs = match_probs[fid]
            w = resolve_winner(fix["home"], fix["away"], probs, rng)
            winners[fid] = w
            r32_winners[fid].append(w)

        r16_winners = {}
        for rid, h_id, a_id in R16_BRACKET:
            home, away = winners[h_id], winners[a_id]
            probs = match_probs.get(f"{home}_vs_{away}", _default_probs())
            r16_winners[rid] = resolve_winner(home, away, probs, rng)

        r16_teams = list(r16_winners.values())
        qf_winners = _advance_round(r16_teams, match_probs, rng, "qf")
        for w in qf_winners.values():
            qf_counts[w] = qf_counts.get(w, 0) + 1

        qf_teams = list(qf_winners.values())
        sf_winners = _advance_round(qf_teams, match_probs, rng, "sf")
        for w in sf_winners.values():
            sf_counts[w] = sf_counts.get(w, 0) + 1

        finalists = list(sf_winners.values())
        if len(finalists) >= 2:
            h, a = finalists[0], finalists[1]
            probs = match_probs.get(f"{h}_vs_{a}", _default_probs())
            champ = resolve_winner(h, a, probs, rng)
            champion_counts[champ] = champion_counts.get(champ, 0) + 1
        elif len(finalists) == 1:
            champion_counts[finalists[0]] = champion_counts.get(finalists[0], 0) + 1

    def normalize(counts: dict, n: int) -> dict:
        return {k: v / n for k, v in sorted(counts.items(), key=lambda x: -x[1])}

    return {
        "n_sims": n_sims,
        "champion_probs": normalize(champion_counts, n_sims),
        "qf_probs": normalize(qf_counts, n_sims * 3),
        "sf_probs": normalize(sf_counts, n_sims * 2),
        "r32_win_probs": {
            fid: normalize({t: ws.count(t) for t in set(ws)}, len(ws))
            for fid, ws in r32_winners.items()
        },
    }


def build_match_probs_for_round(model: EnsembleModel, feat: pd.DataFrame, round_name: str) -> dict:
    """Generate probabilities for all fixtures in a round."""
    from src.features import DynamicElo

    elo = DynamicElo()
    for _, m in feat.iterrows():
        elo.update(m["home"], m["away"], m["result"], m["neutral"])

    ratings = elo.ratings
    probs = {}

    fixtures = R32_FIXTURES if round_name == "r32" else []
    for fix in fixtures:
        home, away = fix["home"], fix["away"]
        rh = ratings.get(home, 1500)
        ra = ratings.get(away, 1500)
        exp = elo.expected(home, away, neutral=True)
        feat_row = {
            "elo_diff": rh - ra,
            "elo_exp_home": exp,
            "form_diff": 0.0,
            "home_form": 1.5,
            "away_form": 1.5,
            "is_knockout": 1,
        }
        probs[fix["id"]] = model.predict_match(home, away, feat_row, neutral=True)
        probs[f"{home}_vs_{away}"] = probs[fix["id"]]

    return probs


def publish_predictions(round_name: str, match_probs: dict, sim_results: dict, version: str = "v0") -> Path:
    """Write locked prediction JSON."""
    payload = {
        "round": round_name,
        "model_version": version,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Late entry — published after group stage. Predictions frozen at locked_at.",
        "match_predictions": {},
        "simulation": sim_results,
    }

    for fix in R32_FIXTURES if round_name == "r32" else []:
        fid = fix["id"]
        p = match_probs.get(fid, {})
        payload["match_predictions"][fid] = {
            "home": fix["home"],
            "away": fix["away"],
            "date": fix["date"],
            "p_home": round(p.get("p_home", 0.33), 4),
            "p_draw": round(p.get("p_draw", 0.25), 4),
            "p_away": round(p.get("p_away", 0.33), 4),
            "exp_home_goals": round(p.get("exp_home_goals", 1.2), 2),
            "exp_away_goals": round(p.get("exp_away_goals", 1.0), 2),
        }

    out = PREDICTIONS / f"{round_name}_2026-06-30.json"
    PREDICTIONS.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    return out
