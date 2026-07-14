"""Break down knockout outcomes: 90 minutes, extra time, penalties."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.config import DATA_PROCESSED


@dataclass
class KnockoutRates:
    """Empirical tiebreak rates from recent World Cup knockouts."""

    # Share of level-at-90 games decided in extra time (vs going to pens still level)
    et_decision_share: float = 0.35
    # Home advantage in ET / pens conditional on reaching tiebreak
    home_et_win_share: float = 0.52
    home_pens_win_share: float = 0.50


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

    # martj42 marks shootouts separately; ingested rows use result H/A after pens
    pens = level[level["result"].isin(["H", "A"])]  # winner after level score
    # Heuristic: very low total goals at 90 often -> pens; we use all level-90 as tiebreak pool
    n_level = len(level)
    n_pens_style = len(pens)  # all level-at-90 in KO resolve via tiebreak

    et_share = max(0.25, min(0.55, 1.0 - (n_pens_style / max(n_level, 1)) * 0.65))
    home_wins = (level["result"] == "H").sum()
    home_pens_share = home_wins / max(len(pens), 1) if len(pens) else 0.5

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
    Expand regulation W/D/L into knockout paths.

    Regulation draw market (e.g. 1X2 "Draw") pays on level score at 90 minutes.
    Advancement includes wins in extra time or penalties.
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
    }


def format_knockout_summary(bd: dict) -> str:
    reg = bd["regulation"]
    tb = bd["tiebreak_given_draw_90"]
    adv = bd["advancement"]
    return (
        f"- **90 min:** {bd['home']} {reg['p_home_win']:.1%} | "
        f"Draw {reg['p_draw']:.1%} | {bd['away']} {reg['p_away_win']:.1%}\n"
        f"- **If draw at 90:** ET decides ~{tb['p_extra_time_decides']:.0%}, "
        f"pens ~{tb['p_penalties']:.0%}\n"
        f"- **To advance:** {bd['home']} {adv['p_home_advance']:.1%} | "
        f"{bd['away']} {adv['p_away_advance']:.1%} "
        f"(pick: **{adv['predicted_qualifier']}**)"
    )
