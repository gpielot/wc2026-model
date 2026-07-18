"""Break down knockout outcomes: 90 minutes, extra time, penalties + fair odds."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED


@dataclass
class KnockoutRates:
    """Empirical tiebreak rates from recent World Cup knockouts."""

    et_decision_share: float = 0.35
    home_et_win_share: float = 0.52
    home_pens_win_share: float = 0.50


def _fair_odds(p: float) -> float | None:
    """Decimal odds implied by probability (no bookmaker margin)."""
    if p is None or p <= 0:
        return None
    return round(1.0 / p, 2)


def _load_wc_knockout_rates() -> KnockoutRates:
    """Estimate tiebreak splits from martj42 + ingested WC 2026 knockouts."""
    try:
        matches = pd.read_parquet(DATA_PROCESSED / "matches.parquet")
    except FileNotFoundError:
        return KnockoutRates()

    wc = matches[
        matches["tournament"].astype(str).str.contains("FIFA World Cup", na=False)
        & matches["date"].dt.year.isin([2018, 2022, 2026])
        & (matches["date"].dt.month >= 6)
    ].dropna(subset=["home_goals", "away_goals"])

    level = wc[wc["home_goals"] == wc["away_goals"]]
    if len(level) < 5:
        return KnockoutRates()

    pens = level[level["result"].isin(["H", "A"])]
    n_level = len(level)
    n_pens_style = len(pens)

    et_share = max(0.25, min(0.55, 1.0 - (n_pens_style / max(n_level, 1)) * 0.65))
    home_wins = (level["result"] == "H").sum()
    home_pens_share = home_wins / max(len(pens), 1) if len(pens) else 0.5
    # Clamp — empirical sample is noisy; don't let it collapse to 0/1
    home_pens_share = float(np.clip(home_pens_share, 0.40, 0.60))

    return KnockoutRates(
        et_decision_share=round(et_share, 3),
        home_et_win_share=0.52,
        home_pens_win_share=round(home_pens_share, 3),
    )


def knockout_breakdown(
    p_home: float,
    p_draw: float,
    p_away: float,
    home: str,
    away: str,
    rates: KnockoutRates | None = None,
) -> dict:
    """
    Expand regulation W/D/L into knockout paths + fair decimal odds.

    - regulation / fair_odds_90: 1X2 at 90 minutes (draw pays if level at FT)
    - advancement / fair_odds_to_win: includes ET + penalties (no draw)
    """
    rates = rates or _load_wc_knockout_rates()
    p_home_90 = p_home
    p_draw_90 = p_draw
    p_away_90 = p_away

    p_et = p_draw_90 * rates.et_decision_share
    p_pens = p_draw_90 * (1.0 - rates.et_decision_share)

    p_home_et = p_et * rates.home_et_win_share
    p_away_et = p_et * (1.0 - rates.home_et_win_share)
    p_home_pens = p_pens * rates.home_pens_win_share
    p_away_pens = p_pens * (1.0 - rates.home_pens_win_share)

    p_home_advance = p_home_90 + p_home_et + p_home_pens
    p_away_advance = p_away_90 + p_away_et + p_away_pens

    return {
        "home": home,
        "away": away,
        "regulation": {
            "p_home_win": round(p_home_90, 4),
            "p_draw": round(p_draw_90, 4),
            "p_away_win": round(p_away_90, 4),
            "note": "90-minute result — matches typical 1X2 draw market in knockouts",
        },
        "fair_odds_90": {
            "home": _fair_odds(p_home_90),
            "draw": _fair_odds(p_draw_90),
            "away": _fair_odds(p_away_90),
            "note": "Model fair decimal odds for regulation (no bookmaker margin)",
        },
        "tiebreak_given_draw_90": {
            "p_extra_time_decides": round(rates.et_decision_share, 3),
            "p_penalties": round(1.0 - rates.et_decision_share, 3),
            "p_home_wins_et": round(p_home_et, 4),
            "p_away_wins_et": round(p_away_et, 4),
            "p_home_wins_pens": round(p_home_pens, 4),
            "p_away_wins_pens": round(p_away_pens, 4),
        },
        "advancement": {
            "p_home_advance": round(p_home_advance, 4),
            "p_away_advance": round(p_away_advance, 4),
            "predicted_qualifier": home if p_home_advance >= p_away_advance else away,
        },
        "fair_odds_to_win": {
            "home": _fair_odds(p_home_advance),
            "away": _fair_odds(p_away_advance),
            "note": "Model fair odds to win the tie (90 + ET + pens)",
        },
    }


def format_knockout_summary(bd: dict) -> str:
    reg = bd["regulation"]
    tb = bd["tiebreak_given_draw_90"]
    adv = bd["advancement"]
    o90 = bd.get("fair_odds_90", {})
    owin = bd.get("fair_odds_to_win", {})
    return (
        f"- **90 min:** {bd['home']} {reg['p_home_win']:.1%} | "
        f"Draw {reg['p_draw']:.1%} | {bd['away']} {reg['p_away_win']:.1%}\n"
        f"- **Fair odds (90 min):** {bd['home']} {o90.get('home')} | "
        f"Draw {o90.get('draw')} | {bd['away']} {o90.get('away')}\n"
        f"- **If draw at 90:** ET decides ~{tb['p_extra_time_decides']:.0%}, "
        f"pens ~{tb['p_penalties']:.0%}\n"
        f"- **To win (90+ET+pens):** {bd['home']} {adv['p_home_advance']:.1%} | "
        f"{bd['away']} {adv['p_away_advance']:.1%} "
        f"(pick: **{adv['predicted_qualifier']}**)\n"
        f"- **Fair odds (to win):** {bd['home']} {owin.get('home')} | "
        f"{bd['away']} {owin.get('away')}"
    )
