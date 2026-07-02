"""Tactical style embeddings from event aggregates."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.config import DATA_PROCESSED, MODELS_DIR
from src.features.player_skills import load_best_statsbomb_events


STYLE_DIMS = [
    "high_press",
    "possession",
    "directness",
    "width",
    "tempo",
    "counter_attack",
    "aerial_reliance",
    "verticality",
]


def compute_team_style_from_events(events: pd.DataFrame) -> pd.DataFrame:
    """Compute interpretable style dimensions per team."""
    if events is None or len(events) == 0:
        return _fallback_team_styles()

    type_col = "type.name" if "type.name" in events.columns else "type"
    team_col = "team.name" if "team.name" in events.columns else "team"
    loc_x = "location" if "location" in events.columns else None

    rows = []
    for team, grp in events.groupby(team_col):
        if pd.isna(team):
            continue
        n = max(len(grp), 1)
        types = grp[type_col].astype(str)

        pressures = (types == "Pressure").sum()
        passes = (types == "Pass").sum()
        shots = (types == "Shot").sum()
        carries = (types == "Carry").sum()
        long_balls = 0
        if "pass.length" in grp.columns:
            long_balls = (grp["pass.length"].fillna(0) > 30).sum()

        # Pressure in attacking third proxy
        high_press = pressures / n * 100

        possession = passes / n * 10
        directness = long_balls / max(passes, 1)
        width = carries / n * 20
        tempo = n / 90  # events per minute proxy
        counter = shots / max(passes, 1) * 10
        aerial = (types == "Duel").sum() / n * 5

        forward_passes = 0
        if "pass.angle" in grp.columns:
            forward_passes = (grp["pass.angle"].fillna(0).abs() < 45).sum()
        verticality = forward_passes / max(passes, 1)

        rows.append(
            {
                "team": team,
                "high_press": high_press,
                "possession": possession,
                "directness": directness,
                "width": width,
                "tempo": tempo,
                "counter_attack": counter,
                "aerial_reliance": aerial,
                "verticality": verticality,
            }
        )

    return pd.DataFrame(rows)


def _fallback_team_styles() -> pd.DataFrame:
    """Fallback styles from team skills."""
    path = DATA_PROCESSED / "team_skills.parquet"
    if not path.exists():
        return pd.DataFrame()
    ts = pd.read_parquet(path)
    rows = []
    for _, r in ts.iterrows():
        rows.append(
            {
                "team": r["team"],
                "high_press": r.get("press_resist", 1) * 10,
                "possession": r.get("passing", 1) * 10,
                "directness": 1 - r.get("passing", 1) * 0.3,
                "width": r.get("transition", 1) * 5,
                "tempo": r.get("offense", 1) * 8,
                "counter_attack": r.get("transition", 1) * 6,
                "aerial_reliance": r.get("defense", 1) * 3,
                "verticality": r.get("offense", 1) * 0.4,
            }
        )
    return pd.DataFrame(rows)


def embed_styles(styles: pd.DataFrame, n_components: int = 5) -> pd.DataFrame:
    """PCA embedding of style vectors."""
    if len(styles) == 0:
        return styles

    X = styles[STYLE_DIMS].fillna(0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    n_comp = min(n_components, len(styles), X.shape[1])
    pca = PCA(n_components=n_comp)
    emb = pca.fit_transform(Xs)

    out = styles[["team"]].copy()
    for i in range(n_comp):
        out[f"style_{i}"] = emb[:, i]
    out[STYLE_DIMS] = styles[STYLE_DIMS].values

    # Save PCA for matchup model
    import joblib
    from src.config import MODELS_DIR

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": scaler, "pca": pca}, MODELS_DIR / "style_pca.pkl")

    return out


def fit_style_matchup_matrix(styles: pd.DataFrame, matches: pd.DataFrame) -> np.ndarray:
    """Learn style interaction matrix W from match outcomes."""
    if len(styles) == 0:
        return np.zeros((len(STYLE_DIMS), len(STYLE_DIMS)))

    style_map = styles.set_index("team")
    recent = matches[matches["date"] >= "2018-01-01"]

    X_rows, y = [], []
    for _, m in recent.iterrows():
        if m["home"] not in style_map.index or m["away"] not in style_map.index:
            continue
        h_style = style_map.loc[m["home"], STYLE_DIMS].values.astype(float)
        a_style = style_map.loc[m["away"], STYLE_DIMS].values.astype(float)
        interaction = np.outer(h_style, a_style).flatten()
        X_rows.append(interaction)
        y.append(1 if m["result"] == "H" else (0.5 if m["result"] == "D" else 0))

    if len(X_rows) < 20:
        W = np.eye(len(STYLE_DIMS)) * 0.01
    else:
        X = np.array(X_rows)
        y = np.array(y)
        # Ridge regression on flattened interaction
        from sklearn.linear_model import Ridge

        reg = Ridge(alpha=1.0)
        reg.fit(X, y)
        W = reg.coef_[: len(STYLE_DIMS) ** 2].reshape(len(STYLE_DIMS), len(STYLE_DIMS))

    import joblib
    from src.config import MODELS_DIR

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(W, MODELS_DIR / "style_matchup_W.pkl")
    return W


def style_matchup_boost(home: str, away: str, styles: pd.DataFrame, W: np.ndarray) -> float:
    """Compute style-based probability boost for home team."""
    if len(styles) == 0:
        return 0.0
    smap = styles.set_index("team")
    if home not in smap.index or away not in smap.index:
        return 0.0
    h = smap.loc[home, STYLE_DIMS].values.astype(float)
    a = smap.loc[away, STYLE_DIMS].values.astype(float)
    score = float(h @ W @ a)
    return np.clip(score * 0.05, -0.08, 0.08)


def build_team_styles() -> pd.DataFrame:
    """Full style pipeline."""
    events = load_best_statsbomb_events()
    raw_styles = compute_team_style_from_events(events)
    embedded = embed_styles(raw_styles)

    matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")
    W = fit_style_matchup_matrix(raw_styles, matches)

    embedded.to_parquet(DATA_PROCESSED / "team_styles.parquet", index=False)
    pd.DataFrame(W, columns=STYLE_DIMS, index=STYLE_DIMS).to_parquet(
        DATA_PROCESSED / "style_matchup_matrix.parquet"
    )
    return embedded
