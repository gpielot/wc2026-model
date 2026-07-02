"""Streamlit dashboard for WC2026 predictions."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
PREDICTIONS = ROOT / "predictions"
DOCS = ROOT / "docs"
PROCESSED = ROOT / "data" / "processed"


@st.cache_data
def load_predictions():
    files = sorted(PREDICTIONS.glob("*.json"))
    if not files:
        return None, []
    latest = files[-1]
    return json.loads(latest.read_text()), [f.name for f in files]


@st.cache_data
def load_styles():
    path = PROCESSED / "team_styles.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


@st.cache_data
def load_chemistry():
    path = PROCESSED / "team_chemistry.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def explain_match(home: str, away: str, match_pred: dict, styles: pd.DataFrame, chemistry: pd.DataFrame):
    """Generate explainability card for a match."""
    st.subheader(f"{home} vs {away}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Home Win", f"{match_pred['p_home']:.1%}")
    col2.metric("Draw", f"{match_pred['p_draw']:.1%}")
    col3.metric("Away Win", f"{match_pred['p_away']:.1%}")

    st.write(f"Expected goals: **{home}** {match_pred.get('exp_home_goals', '?')} — "
             f"**{away}** {match_pred.get('exp_away_goals', '?')}")

    if len(styles) > 0:
        smap = styles.set_index("team")
        if home in smap.index and away in smap.index:
            st.write("**Tactical styles:**")
            style_cols = [c for c in styles.columns if c.startswith("high_") or c in ("possession", "tempo", "directness")]
            if style_cols:
                h_style = smap.loc[home, style_cols[:4]].to_dict() if home in smap.index else {}
                a_style = smap.loc[away, style_cols[:4]].to_dict() if away in smap.index else {}
                st.write(f"- {home}: {', '.join(f'{k}={v:.2f}' for k,v in list(h_style.items())[:3])}")
                st.write(f"- {away}: {', '.join(f'{k}={v:.2f}' for k,v in list(a_style.items())[:3])}")

    if len(chemistry) > 0:
        cmap = chemistry.set_index("team")
        if home in cmap.index and away in cmap.index:
            h_c = cmap.loc[home, "chemistry_score"]
            a_c = cmap.loc[away, "chemistry_score"]
            diff = h_c - a_c
            winner = home if diff > 0 else away
            st.write(f"**Chemistry edge:** {winner} (+{abs(diff):.2f} squad cohesion)")


def main():
    st.set_page_config(page_title="WC2026 Model", page_icon="⚽", layout="wide")
    st.title("World Cup 2026 — Prediction Model")
    st.caption("Player skills · Tactical styles · Squad chemistry · Calibrated probabilities")

    preds, pred_files = load_predictions()
    styles = load_styles()
    chemistry = load_chemistry()

    if preds is None:
        st.warning("No predictions found. Run: `make ingest && make train && make predict ROUND=r32`")
        return

    st.sidebar.header("Predictions")
    selected = st.sidebar.selectbox("Prediction file", pred_files, index=len(pred_files) - 1)
    preds = json.loads((PREDICTIONS / selected).read_text())

    st.sidebar.write(f"**Locked:** {preds.get('locked_at', 'N/A')[:19]}")
    st.sidebar.write(f"**Version:** {preds.get('model_version', '?')}")

    tab1, tab2, tab3, tab4 = st.tabs(["Match Predictions", "Bracket Sim", "Styles & Chemistry", "Betting Report"])

    with tab1:
        st.header(f"Round: {preds.get('round', 'unknown').upper()}")
        for mid, match in preds.get("match_predictions", {}).items():
            with st.expander(f"{match['home']} vs {match['away']} ({match.get('date', '')})"):
                explain_match(match["home"], match["away"], match, styles, chemistry)

    with tab2:
        st.header("Monte Carlo Simulation")
        sim = preds.get("simulation", {})
        st.subheader("Champion Probabilities")
        champ = sim.get("champion_probs", {})
        if champ:
            df = pd.DataFrame(list(champ.items()), columns=["Team", "Probability"])
            df = df.sort_values("Probability", ascending=False)
            st.bar_chart(df.set_index("Team"))
            st.dataframe(df.style.format({"Probability": "{:.1%}"}))

        st.subheader("Round of 32 Win Probabilities")
        r32 = sim.get("r32_win_probs", {})
        for fid, probs in r32.items():
            if probs:
                top = max(probs.items(), key=lambda x: x[1])
                st.write(f"**{fid}**: {top[0]} ({top[1]:.1%})")

    with tab3:
        st.header("Team Styles & Chemistry")
        col1, col2 = st.columns(2)
        with col1:
            if len(styles) > 0:
                st.subheader("Style Dimensions")
                style_cols = [c for c in styles.columns if c not in ("team",) and not c.startswith("style_")]
                if style_cols:
                    st.dataframe(styles[["team"] + style_cols[:6]].head(24))
        with col2:
            if len(chemistry) > 0:
                st.subheader("Squad Chemistry")
                st.dataframe(chemistry.sort_values("chemistry_score", ascending=False).head(24))

        matrix_path = PROCESSED / "style_matchup_matrix.parquet"
        if matrix_path.exists():
            st.subheader("Style Matchup Matrix (Rock-Paper-Scissors)")
            W = pd.read_parquet(matrix_path)
            st.dataframe(W.style.background_gradient(cmap="RdYlGn", axis=None))

    with tab4:
        report_path = DOCS / "betting_edge_report.md"
        if report_path.exists():
            st.markdown(report_path.read_text())
        else:
            st.info("Run betting report generation after predictions are published.")


if __name__ == "__main__":
    main()
