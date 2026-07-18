# World Cup 2026 Prediction Model

A reproducible international football prediction system built from **player skills**, **tactical style embeddings**, **squad chemistry**, and a **calibrated ensemble** (Dixon-Coles + LightGBM).

> **Pre-registration note:** Predictions are locked in timestamped JSON files under `predictions/`. This v0 release is a late entry published after the group stage (disclaimer included in each file).

## Quick start

```bash
# Install
pip install -e .

# Full pipeline
make ingest    # Download martj42, Elo, StatsBomb, fixtures
make train     # Features + player skills + styles + chemistry + ensemble
make predict ROUND=r32   # Generate R32 predictions + Monte Carlo sim

# Dashboard
make dashboard
# or: streamlit run src/publish/dashboard.py
```

## Model architecture

```
Club + international event data (StatsBomb)
    → Player skill vectors (offense, defense, passing, press, transition)
    → Tactical style embeddings (PCA on 8 style dimensions)
    → Pairwise chemistry (caps together, pass chains)
    → Ensemble: Dixon-Coles (45%) + LightGBM (55%) + style/chemistry adjustments
    → Monte Carlo bracket simulation (100k runs)
```

## Data sources

| Source | License | Use |
|--------|---------|-----|
| [martj42/international_results](https://github.com/martj42/international_results) | Open | Match history 1872–2026 |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Research | Event-level WC/Euro data |
| [eloratings.net](https://www.eloratings.net) | Open | Elo sanity check |
| Wyscout open (via kloppy) | CC BY 4.0 | Club event data (optional) |

## Predictions

**[📖 Prediction Story](docs/PREDICTION_STORY.md)** — running diary: Brazil ✅, Paraguay upset ❌, Norway shock ❌, and locked QF picks.

Locked prediction files:

- `predictions/r32_2026-06-30.json` — Round of 32 (original lock)
- `predictions/r16_real_bracket_2026-07-02.json` — Round of 16 after ingesting R32 results through Jul 1
- `predictions/final_real_bracket_2026-07-18.json` — Final (Spain vs Argentina) + fair odds 90/to-win

After each knockout round, add results to `src/data/wc2026_results.py` and run:

```bash
make update-final   # ingest results → retrain → publish next round
```

Then update `docs/PREDICTION_STORY.md` with what happened and push.

- See `docs/betting_edge_report.md` for model vs market comparison

## Project structure

```
wc2026-model/
├── src/
│   ├── ingest/       # Data download & normalization
│   ├── features/     # Elo, player skills, styles, chemistry
│   ├── models/       # Dixon-Coles, LightGBM, ensemble
│   ├── simulate/     # Monte Carlo bracket
│   └── publish/      # Dashboard + betting report
├── predictions/      # Locked forecast JSON (committed)
├── docs/             # Methodology + betting appendix
└── data/processed/   # Parquet feature store (gitignored raw/)
```

## Backtest

Rolling holdout on 2018 and 2022 international matches. Metrics saved to `models/backtest_metrics.json` after training.

## Disclaimer

This project is for **research and entertainment**. Betting markets are efficient; do not expect sustained positive ROI. See `docs/betting_edge_report.md`.

## License

MIT. StatsBomb data subject to [StatsBomb terms](https://github.com/statsbomb/open-data).
