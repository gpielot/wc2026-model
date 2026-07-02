"""Feature engineering for match prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED


class DynamicElo:
    """Simple dynamic Elo with home/neutral adjustment."""

    def __init__(self, k: float = 20.0, home_adv: float = 100.0, initial: float = 1500.0):
        self.k = k
        self.home_adv = home_adv
        self.initial = initial
        self.ratings: dict[str, float] = {}

    def _get(self, team: str) -> float:
        return self.ratings.get(team, self.initial)

    def expected(self, home: str, away: str, neutral: bool) -> float:
        rh = self._get(home) + (0 if neutral else self.home_adv)
        ra = self._get(away)
        return 1.0 / (1.0 + 10 ** ((ra - rh) / 400))

    def update(self, home: str, away: str, result: str, neutral: bool) -> None:
        if home not in self.ratings:
            self.ratings[home] = self.initial
        if away not in self.ratings:
            self.ratings[away] = self.initial

        exp = self.expected(home, away, neutral)
        actual = {"H": 1.0, "D": 0.5, "A": 0.0}[result]
        delta = self.k * (actual - exp)
        self.ratings[home] += delta
        self.ratings[away] -= delta

    def fit_history(self, matches: pd.DataFrame) -> pd.DataFrame:
        """Walk forward through matches, return per-match Elo features."""
        rows = []
        for _, m in matches.iterrows():
            rh = self._get(m["home"])
            ra = self._get(m["away"])
            exp = self.expected(m["home"], m["away"], m["neutral"])
            rows.append(
                {
                    "match_id": m["match_id"],
                    "date": m["date"],
                    "home": m["home"],
                    "away": m["away"],
                    "home_elo": rh,
                    "away_elo": ra,
                    "elo_diff": rh - ra + (0 if m["neutral"] else self.home_adv),
                    "elo_exp_home": exp,
                    "result": m["result"],
                    "neutral": m["neutral"],
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                    "tournament": m.get("tournament", ""),
                }
            )
            self.update(m["home"], m["away"], m["result"], m["neutral"])
        return pd.DataFrame(rows)


def add_form_features(df: pd.DataFrame, matches: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Add rolling form (points per game) for each team before each match."""
    team_history: dict[str, list[tuple[pd.Timestamp, float]]] = {}

    def points(result: str, is_home: bool) -> float:
        if result == "D":
            return 1.0
        if (result == "H" and is_home) or (result == "A" and not is_home):
            return 3.0
        return 0.0

    form_home, form_away = [], []
    for _, m in matches.iterrows():
        h_hist = team_history.get(m["home"], [])
        a_hist = team_history.get(m["away"], [])
        h_pts = [p for d, p in h_hist if d < m["date"]][-window:]
        a_pts = [p for d, p in a_hist if d < m["date"]][-window:]
        form_home.append(np.mean(h_pts) if h_pts else 1.0)
        form_away.append(np.mean(a_pts) if a_pts else 1.0)

        team_history.setdefault(m["home"], []).append((m["date"], points(m["result"], True)))
        team_history.setdefault(m["away"], []).append((m["date"], points(m["result"], False)))

    out = df.copy()
    out["home_form"] = form_home
    out["away_form"] = form_away
    out["form_diff"] = out["home_form"] - out["away_form"]
    return out


def build_match_features(matches: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build full feature table from match history."""
    if matches is None:
        matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")

    elo = DynamicElo()
    feat = elo.fit_history(matches)
    feat = add_form_features(feat, matches)

    feat["is_knockout"] = feat["tournament"].str.contains(
        "World Cup|European Championship|Copa América|Nations League",
        case=False,
        na=False,
    ).astype(int)

    feat["days_since_last_home"] = 7.0  # placeholder; refined with rest calc
    feat["days_since_last_away"] = 7.0

    feat.to_parquet(DATA_PROCESSED / "match_features.parquet", index=False)
    return feat


def get_team_ratings_at_date(feat: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
    """Return latest Elo per team before a given date."""
    past = feat[feat["date"] < as_of]
    ratings = {}
    for _, row in past.iterrows():
        ratings[row["home"]] = row["home_elo"]
        ratings[row["away"]] = row["away_elo"]
    return ratings
