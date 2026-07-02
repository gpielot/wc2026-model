"""Pairwise player chemistry features."""

from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, DATA_RAW
from src.features.player_skills import load_best_statsbomb_events


def _load_statsbomb_lineups() -> pd.DataFrame:
    """Load lineup data from StatsBomb."""
    sb_root = DATA_RAW / "statsbomb" / "open-data" / "data" / "lineups"
    if not sb_root.exists():
        return pd.DataFrame()

    rows = []
    for lineup_file in sb_root.rglob("*.json"):
        with open(lineup_file) as f:
            data = json.load(f)
        match_id = lineup_file.stem
        for team_block in data:
            team = team_block.get("team_name", team_block.get("team", {}).get("name", ""))
            for player in team_block.get("lineup", []):
                pname = player.get("player_name", player.get("player", {}).get("name", ""))
                rows.append({"match_id": match_id, "team": team, "player": pname})

    return pd.DataFrame(rows)


def compute_caps_together(lineups: pd.DataFrame) -> pd.DataFrame:
    """Count how often player pairs appeared together."""
    if len(lineups) == 0:
        return pd.DataFrame()

    pair_counts: dict[tuple, int] = {}
    for (match_id, team), grp in lineups.groupby(["match_id", "team"]):
        players = grp["player"].dropna().unique().tolist()
        for p1, p2 in itertools.combinations(sorted(players), 2):
            key = (team, p1, p2)
            pair_counts[key] = pair_counts.get(key, 0) + 1

    rows = [
        {"team": k[0], "player_i": k[1], "player_j": k[2], "caps_together": v}
        for k, v in pair_counts.items()
    ]
    return pd.DataFrame(rows)


def compute_pass_chains(events: pd.DataFrame) -> pd.DataFrame:
    """Estimate pass chain chemistry from consecutive passes."""
    if events is None or len(events) == 0:
        return pd.DataFrame()

    type_col = "type.name" if "type.name" in events.columns else "type"
    player_col = "player.name" if "player.name" in events.columns else "player"
    team_col = "team.name" if "team.name" in events.columns else "team"

    passes = events[events[type_col].astype(str) == "Pass"].copy()
    if len(passes) == 0:
        return pd.DataFrame()

    pair_xt: dict[tuple, float] = {}
    prev_player = None
    prev_team = None

    for _, row in passes.iterrows():
        player = row.get(player_col)
        team = row.get(team_col)
        if pd.isna(player):
            continue
        if prev_team == team and prev_player and prev_player != player:
            key = (team, min(prev_player, player), max(prev_player, player))
            pair_xt[key] = pair_xt.get(key, 0) + 1
        prev_player = player
        prev_team = team

    rows = [
        {"team": k[0], "player_i": k[1], "player_j": k[2], "pass_chain_count": v}
        for k, v in pair_xt.items()
    ]
    return pd.DataFrame(rows)


def aggregate_team_chemistry(pairs: pd.DataFrame) -> pd.DataFrame:
    """Team-level chemistry score."""
    if len(pairs) == 0:
        return _fallback_chemistry()

    chem_col = "caps_together" if "caps_together" in pairs.columns else "pass_chain_count"
    agg = pairs.groupby("team").agg(
        mean_chemistry=(chem_col, "mean"),
        max_chemistry=(chem_col, "max"),
        n_pairs=(chem_col, "count"),
    ).reset_index()
    agg["chemistry_score"] = agg["mean_chemistry"] / (agg["mean_chemistry"].max() + 1e-6)
    return agg


def _fallback_chemistry() -> pd.DataFrame:
    """Fallback chemistry from team cohesion proxy."""
    path = DATA_PROCESSED / "team_skills.parquet"
    if not path.exists():
        teams = [
            "Netherlands", "Japan", "Argentina", "Senegal", "France", "Mexico",
            "England", "Colombia", "Brazil", "Ecuador", "Germany", "USA",
            "Spain", "Morocco", "Portugal", "Uruguay", "Belgium", "Switzerland",
            "Croatia", "Denmark", "Italy", "Austria", "Poland", "South Korea",
        ]
        return pd.DataFrame({"team": teams, "chemistry_score": np.linspace(0.9, 0.4, len(teams))})

    ts = pd.read_parquet(path)
    out = ts[["team"]].copy()
    out["chemistry_score"] = ts["overall"] / ts["overall"].max()
    out["mean_chemistry"] = out["chemistry_score"]
    out["max_chemistry"] = out["chemistry_score"] * 1.2
    out["n_pairs"] = 55
    return out


def chemistry_boost(home: str, away: str, chemistry: pd.DataFrame) -> float:
    """Chemistry differential boost for home team."""
    if len(chemistry) == 0:
        return 0.0
    cmap = chemistry.set_index("team")
    if home not in cmap.index or away not in cmap.index:
        return 0.0
    diff = cmap.loc[home, "chemistry_score"] - cmap.loc[away, "chemistry_score"]
    return np.clip(diff * 0.06, -0.06, 0.06)


def build_chemistry_features() -> pd.DataFrame:
    """Full chemistry pipeline."""
    lineups = _load_statsbomb_lineups()
    caps = compute_caps_together(lineups)

    events = load_best_statsbomb_events()
    chains = compute_pass_chains(events)

    if len(caps) > 0 and len(chains) > 0:
        pairs = caps.merge(chains, on=["team", "player_i", "player_j"], how="outer").fillna(0)
    elif len(caps) > 0:
        pairs = caps
    else:
        pairs = chains

    pairs.to_parquet(DATA_PROCESSED / "pair_chemistry.parquet", index=False)
    team_chem = aggregate_team_chemistry(pairs)
    team_chem.to_parquet(DATA_PROCESSED / "team_chemistry.parquet", index=False)
    return team_chem
