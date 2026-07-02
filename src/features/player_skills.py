"""Player skill ratings from event data (VAEP-style aggregates)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, DATA_RAW

_EVENTS_CACHE: dict[tuple[int, int], pd.DataFrame | None] = {}


def load_statsbomb_events_cached(competition_id: int, season_id: int) -> pd.DataFrame | None:
    """Load StatsBomb events with in-memory cache."""
    key = (competition_id, season_id)
    if key not in _EVENTS_CACHE:
        _EVENTS_CACHE[key] = _load_statsbomb_events(competition_id, season_id)
    return _EVENTS_CACHE[key]


def load_best_statsbomb_events() -> pd.DataFrame | None:
    """Load best available international tournament events."""
    for comp, seasons in [(43, [106, 3, 282]), (55, [316, 4])]:
        for s in seasons:
            events = load_statsbomb_events_cached(comp, s)
            if events is not None and len(events) > 0:
                return events
    return None


def _load_statsbomb_events(competition_id: int, season_id: int, max_matches: int = 64) -> pd.DataFrame | None:
    """Load StatsBomb events for a competition season (lightweight extraction)."""
    sb_root = DATA_RAW / "statsbomb" / "open-data" / "data"
    matches_file = sb_root / "matches" / str(competition_id) / f"{season_id}.json"
    events_path = sb_root / "events"

    if not matches_file.exists():
        return None

    with open(matches_file) as f:
        matches = json.load(f)
    if not isinstance(matches, list):
        matches = [matches]

    rows = []
    for match_meta in matches[:max_matches]:
        match_id = match_meta.get("match_id")
        if match_id is None:
            continue
        events_file = events_path / f"{match_id}.json"
        if not events_file.exists():
            continue
        with open(events_file) as f:
            events = json.load(f)
        for ev in events:
            etype = ev.get("type", {})
            etype_name = etype.get("name") if isinstance(etype, dict) else str(etype)
            player = ev.get("player", {})
            pname = player.get("name") if isinstance(player, dict) else None
            team = ev.get("team", {})
            tname = team.get("name") if isinstance(team, dict) else None
            shot = ev.get("shot", {}) or {}
            pas = ev.get("pass", {}) or {}
            rows.append(
                {
                    "match_id": match_id,
                    "competition_id": competition_id,
                    "type.name": etype_name,
                    "player.name": pname,
                    "team.name": tname,
                    "shot.statsbomb_xg": shot.get("statsbomb_xg"),
                    "pass.length": pas.get("length"),
                    "pass.angle": pas.get("angle"),
                }
            )

    if not rows:
        return None
    return pd.DataFrame(rows)


def compute_player_action_values(events: pd.DataFrame) -> pd.DataFrame:
    """Compute simplified VAEP-like action values from StatsBomb events."""
    if events is None or len(events) == 0:
        return _fallback_player_skills()

    type_col = "type.name" if "type.name" in events.columns else "type"
    player_col = "player.name" if "player.name" in events.columns else "player_id"
    team_col = "team.name" if "team.name" in events.columns else "team"

    offensive_types = {"Pass", "Shot", "Dribble", "Carry"}
    defensive_types = {"Pressure", "Interception", "Block", "Duel", "Clearance"}

    rows = []
    for player, grp in events.groupby(player_col):
        if pd.isna(player):
            continue
        types = grp[type_col].astype(str) if type_col in grp.columns else pd.Series(dtype=str)

        off_count = types.isin(offensive_types).sum()
        def_count = types.isin(defensive_types).sum()
        pass_count = (types == "Pass").sum()
        shot_count = (types == "Shot").sum()
        pressure_count = (types == "Pressure").sum()

        # xG from shots
        xg = 0.0
        if "shot.statsbomb_xg" in grp.columns:
            xg = grp["shot.statsbomb_xg"].fillna(0).sum()

        minutes_proxy = max(len(grp) / 90, 1)

        rows.append(
            {
                "player": player,
                "team": grp[team_col].iloc[0] if team_col in grp.columns else "",
                "offense": (off_count + 2 * shot_count + 3 * xg) / minutes_proxy,
                "defense": def_count / minutes_proxy,
                "passing": pass_count / minutes_proxy,
                "press_resist": pressure_count / minutes_proxy,
                "transition": (off_count + def_count) / minutes_proxy,
                "decision": xg / max(shot_count, 1),
                "n_events": len(grp),
            }
        )

    return pd.DataFrame(rows)


def _fallback_player_skills() -> pd.DataFrame:
    """Generate placeholder skills from Elo when event data unavailable."""
    elo_path = DATA_PROCESSED / "elo_snapshot.parquet"
    if elo_path.exists():
        elo = pd.read_parquet(elo_path)
        team_col = next((c for c in elo.columns if c in ("team", "country", "name")), elo.columns[1])
        rating_col = next(
            (c for c in elo.columns if "elo" in c.lower() or c.lower() == "rating"),
            None,
        )
        rows = []
        for _, r in elo.iterrows():
            team = r[team_col]
            if rating_col and rating_col in r.index:
                try:
                    base = float(r[rating_col]) / 1500
                except (ValueError, TypeError):
                    continue
            else:
                # Try last numeric column
                nums = [r[c] for c in elo.columns if c != team_col]
                base = None
                for v in nums:
                    try:
                        base = float(v) / 1500
                        break
                    except (ValueError, TypeError):
                        continue
                if base is None:
                    continue
            rows.append(
                {
                    "player": f"{team}_squad",
                    "team": team,
                    "offense": base * 1.1,
                    "defense": base * 0.9,
                    "passing": base,
                    "press_resist": base * 0.95,
                    "transition": base,
                    "decision": base,
                    "n_events": 0,
                }
            )
        if rows:
            return pd.DataFrame(rows)
    return _fallback_from_teams()


def _fallback_from_teams() -> pd.DataFrame:
    """Minimal fallback from WC2026 R32 teams."""
    from src.config import R32_FIXTURES

    teams = sorted({t for f in R32_FIXTURES for t in (f["home"], f["away"])})
    rows = []
    for i, team in enumerate(teams):
        base = 0.7 + (len(teams) - i) / len(teams) * 0.5
        rows.append(
            {
                "player": f"{team}_squad",
                "team": team,
                "offense": base * 1.1,
                "defense": base * 0.9,
                "passing": base,
                "press_resist": base * 0.95,
                "transition": base,
                "decision": base,
                "n_events": 0,
            }
        )
    return pd.DataFrame(rows)


def apply_time_decay(skills: pd.DataFrame, half_life_days: float = 365.0) -> pd.DataFrame:
    """Apply exponential decay (placeholder — uses uniform decay factor)."""
    decay = np.exp(-np.log(2) / half_life_days * 180)  # ~6 month effective window
    skill_cols = ["offense", "defense", "passing", "press_resist", "transition", "decision"]
    out = skills.copy()
    for col in skill_cols:
        if col in out.columns:
            out[col] = out[col] * decay
    return out


def aggregate_team_skills(skills: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player skills to team level."""
    if "team" not in skills.columns:
        return pd.DataFrame()

    skill_cols = ["offense", "defense", "passing", "press_resist", "transition", "decision"]
    agg = skills.groupby("team")[skill_cols].mean().reset_index()
    agg["overall"] = agg[skill_cols].mean(axis=1)
    return agg


def build_player_skills() -> pd.DataFrame:
    """Full player skills pipeline."""
    events = load_best_statsbomb_events()
    skills = compute_player_action_values(events)
    skills = apply_time_decay(skills)
    skills.to_parquet(DATA_PROCESSED / "player_skills.parquet", index=False)

    team_skills = aggregate_team_skills(skills)
    team_skills.to_parquet(DATA_PROCESSED / "team_skills.parquet", index=False)

    return skills
