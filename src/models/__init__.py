"""Match outcome models: Dixon-Coles, gradient boosting, ensemble."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.preprocessing import LabelEncoder

from src.config import DATA_PROCESSED, MODELS_DIR

try:
    import lightgbm as lgb

    _HAS_LGBM = True
except OSError:
    _HAS_LGBM = False


def dixon_coles_tau(i: int, j: int, rho: float, lam_h: float, lam_a: float) -> float:
    """Dixon-Coles adjustment factor for low scores."""
    if i == 0 and j == 0:
        return 1 - lam_h * lam_a * rho
    if i == 0 and j == 1:
        return 1 + lam_h * rho
    if i == 1 and j == 0:
        return 1 + lam_a * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


class DixonColesModel:
    """Dixon-Coles Poisson model for match scores."""

    def __init__(self):
        self.attack: dict[str, float] = {}
        self.defense: dict[str, float] = {}
        self.home_adv = 0.25
        self.rho = -0.05
        self.teams: list[str] = []

    def _params(self, teams: list[str]) -> np.ndarray:
        n = len(teams)
        idx = {t: i for i, t in enumerate(teams)}
        return np.zeros(2 * n + 2), idx

    def fit(self, matches: pd.DataFrame, max_iter: int = 200) -> "DixonColesModel":
        """Fit attack/defense parameters via MLE."""
        recent = matches[matches["date"] >= "2010-01-01"].copy()
        recent = recent.dropna(subset=["home_goals", "away_goals"])
        recent = recent[(recent["home_goals"] >= 0) & (recent["away_goals"] >= 0)]

        # Keep teams with enough matches for stable estimates
        team_counts = pd.concat([recent["home"], recent["away"]]).value_counts()
        teams = sorted(team_counts[team_counts >= 15].index.tolist())
        if len(teams) < 20:
            teams = sorted(set(recent["home"]) | set(recent["away"]))

        recent = recent[recent["home"].isin(teams) & recent["away"].isin(teams)]
        self.teams = teams
        n = len(teams)
        idx = {t: i for i, t in enumerate(teams)}

        home_idx = recent["home"].map(idx).values.astype(int)
        away_idx = recent["away"].map(idx).values.astype(int)
        hg = recent["home_goals"].values.astype(int)
        ag = recent["away_goals"].values.astype(int)
        neutral = recent["neutral"].values.astype(float)

        # Pre-index scorelines for vectorized likelihood
        score_masks = {}
        for i in range(7):
            for j in range(7):
                mask = (hg == i) & (ag == j)
                if mask.any():
                    score_masks[(i, j)] = mask

        def neg_ll(params):
            attack = params[:n]
            defense = params[n : 2 * n]
            home_adv = params[2 * n]
            rho = params[2 * n + 1]

            lam_h = np.exp(attack[home_idx] - defense[away_idx] + home_adv * (1 - neutral))
            lam_a = np.exp(attack[away_idx] - defense[home_idx])

            ll = 0.0
            for (i, j), mask in score_masks.items():
                lh = lam_h[mask]
                la = lam_a[mask]
                p_h = poisson.pmf(i, lh)
                p_a = poisson.pmf(j, la)
                tau = np.array([dixon_coles_tau(i, j, rho, lhi, laj) for lhi, laj in zip(lh, la)])
                prob = np.clip(p_h * p_a * tau, 1e-12, None)
                ll -= np.log(prob).sum()
            return ll

        x0 = np.zeros(2 * n + 2)
        x0[2 * n] = 0.25
        x0[2 * n + 1] = -0.05
        res = minimize(neg_ll, x0, method="L-BFGS-B", options={"maxiter": max_iter, "ftol": 1e-4})

        params = res.x
        self.attack = {t: params[idx[t]] for t in teams}
        self.defense = {t: params[n + idx[t]] for t in teams}
        self.home_adv = params[2 * n]
        self.rho = params[2 * n + 1]
        return self

    def predict_probs(self, home: str, away: str, neutral: bool = True, max_goals: int = 8) -> dict:
        """Return W/D/L probabilities from score matrix."""
        ah = self.attack.get(home, 0.0)
        aa = self.attack.get(away, 0.0)
        dh = self.defense.get(home, 0.0)
        da = self.defense.get(away, 0.0)
        ha = self.home_adv if not neutral else 0.0

        lam_h = np.exp(ah - da + ha)
        lam_a = np.exp(aa - dh)

        p_home, p_draw, p_away = 0.0, 0.0, 0.0
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = poisson.pmf(i, lam_h) * poisson.pmf(j, lam_a)
                p *= dixon_coles_tau(i, j, self.rho, lam_h, lam_a)
                if i > j:
                    p_home += p
                elif i == j:
                    p_draw += p
                else:
                    p_away += p

        total = p_home + p_draw + p_away
        return {
            "p_home": p_home / total,
            "p_draw": p_draw / total,
            "p_away": p_away / total,
            "exp_home_goals": lam_h,
            "exp_away_goals": lam_a,
        }


class LightGBMMatchModel:
    """Multiclass gradient boosting for W/D/L (LightGBM if available, else sklearn)."""

    FEATURE_COLS = [
        "elo_diff",
        "elo_exp_home",
        "form_diff",
        "home_form",
        "away_form",
        "is_knockout",
    ]

    def __init__(self):
        self.model = None
        self.calibrator: CalibratedClassifierCV | None = None
        self.le = LabelEncoder()
        self.le.fit(["A", "D", "H"])

    def _make_base_estimator(self):
        if _HAS_LGBM:
            return lgb.LGBMClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                num_class=3,
                objective="multiclass",
                random_state=42,
                verbose=-1,
            )
        return HistGradientBoostingClassifier(
            max_iter=200,
            max_depth=5,
            learning_rate=0.05,
            random_state=42,
        )

    def fit(self, feat: pd.DataFrame) -> "LightGBMMatchModel":
        train = feat[feat["date"] >= "2010-01-01"].dropna(subset=self.FEATURE_COLS)
        X = train[self.FEATURE_COLS].values
        y = self.le.transform(train["result"].values)

        base = self._make_base_estimator()
        self.calibrator = CalibratedClassifierCV(base, cv=3, method="isotonic")
        self.calibrator.fit(X, y)
        self.model = base
        return self

    def predict_proba(self, row: dict) -> dict:
        X = np.array([[row[c] for c in self.FEATURE_COLS]])
        probs = self.calibrator.predict_proba(X)[0]
        # LabelEncoder order: A, D, H
        return {"p_home": probs[2], "p_draw": probs[1], "p_away": probs[0]}

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df[self.FEATURE_COLS].values
        probs = self.calibrator.predict_proba(X)
        return pd.DataFrame(
            {"p_home": probs[:, 2], "p_draw": probs[:, 1], "p_away": probs[:, 0]}
        )


class EnsembleModel:
    """Stack Dixon-Coles + LightGBM with simple average + calibration."""

    def __init__(self):
        self.dc = DixonColesModel()
        self.lgbm = LightGBMMatchModel()
        self.team_style: pd.DataFrame | None = None
        self.chemistry: pd.DataFrame | None = None

    def fit(self, matches: pd.DataFrame, feat: pd.DataFrame) -> "EnsembleModel":
        self.dc.fit(matches)
        self.lgbm.fit(feat)
        return self

    def predict_match(
        self,
        home: str,
        away: str,
        feat_row: dict | None = None,
        neutral: bool = True,
        style_boost: float = 0.0,
        chem_boost: float = 0.0,
    ) -> dict:
        dc_probs = self.dc.predict_probs(home, away, neutral=neutral)

        if feat_row is None:
            lgbm_probs = {"p_home": 0.33, "p_draw": 0.34, "p_away": 0.33}
        else:
            lgbm_probs = self.lgbm.predict_proba(feat_row)

        w_dc, w_lgbm = 0.45, 0.55
        p_home = w_dc * dc_probs["p_home"] + w_lgbm * lgbm_probs["p_home"]
        p_draw = w_dc * dc_probs["p_draw"] + w_lgbm * lgbm_probs["p_draw"]
        p_away = w_dc * dc_probs["p_away"] + w_lgbm * lgbm_probs["p_away"]

        # Apply style/chemistry adjustments
        adj = style_boost + chem_boost
        p_home = np.clip(p_home + adj, 0.01, 0.98)
        p_away = np.clip(p_away - adj, 0.01, 0.98)
        p_draw = np.clip(1 - p_home - p_away, 0.01, 0.98)
        total = p_home + p_draw + p_away

        return {
            "p_home": p_home / total,
            "p_draw": p_draw / total,
            "p_away": p_away / total,
            "exp_home_goals": dc_probs["exp_home_goals"],
            "exp_away_goals": dc_probs["exp_away_goals"],
            "dc_probs": dc_probs,
            "lgbm_probs": lgbm_probs,
        }

    def save(self, path: Path | None = None) -> None:
        path = path or MODELS_DIR
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump({"dc": self.dc, "lgbm": self.lgbm}, path / "ensemble.pkl")

    @classmethod
    def load(cls, path: Path | None = None) -> "EnsembleModel":
        path = path or MODELS_DIR
        data = joblib.load(path / "ensemble.pkl")
        m = cls()
        m.dc = data["dc"]
        m.lgbm = data["lgbm"]
        return m


def backtest(feat: pd.DataFrame, holdout_years: list[int] | None = None) -> dict:
    """Rolling backtest on holdout tournaments (GBM only for speed)."""
    holdout_years = holdout_years or [2018, 2022]
    results = []

    for year in holdout_years:
        train = feat[feat["date"].dt.year < year]
        test = feat[feat["date"].dt.year == year]
        if len(test) == 0 or len(train) < 100:
            continue

        gbm = LightGBMMatchModel()
        gbm.fit(train)
        probs = gbm.predict_batch(test)

        y_true = test["result"].map({"H": 0, "D": 1, "A": 2}).values
        y_pred = probs[["p_home", "p_draw", "p_away"]].values
        y_pred = y_pred[:, [2, 1, 0]]

        ll = log_loss(y_true, y_pred, labels=[0, 1, 2])
        brier = np.mean(
            [brier_score_loss((y_true == i).astype(int), y_pred[:, i]) for i in range(3)]
        )
        results.append({"year": year, "log_loss": float(ll), "brier": float(brier), "n_matches": len(test)})

    return {"folds": results}


def train_and_save() -> dict:
    """Full training pipeline."""
    matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")
    feat_path = DATA_PROCESSED / "match_features.parquet"
    if feat_path.exists():
        feat = pd.read_parquet(feat_path)
    else:
        from src.features import build_match_features
        feat = build_match_features(matches)

    ens = EnsembleModel()
    ens.fit(matches, feat)
    ens.save()

    bt = backtest(feat)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (MODELS_DIR / "backtest_metrics.json").write_text(json.dumps(bt, indent=2))
    return bt
