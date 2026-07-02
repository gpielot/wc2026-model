# Methodology

## Objective

Build the best **publicly reproducible** World Cup prediction model from player interactions and playing styles — not merely another Elo spreadsheet. Secondary goal: calibrated probabilities with an honest betting-edge appendix.

## 1. Data

### Match history
All men's full internationals from martj42 (1872–2026). Country names harmonized via `former_names.csv`. Outcomes: home win / draw / away win.

### Event data
StatsBomb Open Data for FIFA World Cup 2018/2022 and UEFA Euro 2020/2024. Every pass, shot, pressure, carry, duel with xG and location where available.

### Elo prior
Snapshot from eloratings.net as sanity check; we compute our own dynamic Elo walk-forward.

## 2. Player skill model

From StatsBomb events we compute simplified action-value aggregates (VAEP-inspired):

| Skill | Derived from |
|-------|-------------|
| Offense | Shots, xG, attacking actions per 90 |
| Defense | Pressures, interceptions, blocks, duels |
| Passing | Pass volume and completion proxy |
| Press resistance | Pressures received |
| Transition | Combined offensive + defensive action rate |
| Decision | xG per shot |

Skills are aggregated per player, then decay-weighted (half-life ~12 months) and rolled up to team level via minutes-weighted mean.

**Transfer learning:** Skills learned from club + international tournaments transfer to WC 2026 squads.

## 3. Tactical style embeddings

Eight interpretable dimensions per team:

1. High press — pressures per event
2. Possession — pass rate
3. Directness — long ball ratio
4. Width — carry rate
5. Tempo — events per minute
6. Counter-attack — shot/pass ratio
7. Aerial reliance — duel rate
8. Verticality — forward pass ratio

Reduced to 5 PCA components. A **style matchup matrix W** is learned via ridge regression on 2018+ international results — this is the emergent "rock-paper-scissors" structure.

## 4. Squad chemistry

Pairwise features between projected starting XI:

- Caps together (from StatsBomb lineups)
- Pass chain frequency (consecutive passes between pair)
- Team chemistry score = mean pair cohesion, boosted for central midfield and striker-creator pairs

Chemistry differential (`home - away`) adjusts match probabilities by up to ±6%.

## 5. Match outcome ensemble

### Dixon-Coles Poisson (45% weight)
Attack/defense parameters fitted via MLE on 2010+ internationals. Low-score correlation parameter ρ adjusts 0-0, 1-0, 0-1, 1-1 cells.

### LightGBM multiclass (55% weight)
Features: Elo diff, Elo expected home win, form (5-match points), knockout flag. Isotonic calibration on 3-fold CV.

### Adjustments
- Style matchup boost: `clip(h_style @ W @ a_style × 0.05, ±0.08)`
- Chemistry boost: `clip(chem_diff × 0.06, ±0.06)`

## 6. Monte Carlo simulation

100,000 bracket simulations from R32 through Final:
- Draws in knockout resolved as 50/50 penalty shootout
- Output: champion probabilities, QF/SF advancement rates, per-match win rates

## 7. Validation

| Holdout | Purpose |
|---------|---------|
| 2018 calendar year | Euro + WC qualifiers |
| 2022 calendar year | WC Qatar |

Metrics: multiclass log loss, Brier score per class, calibration bins.

**Leakage prevention:** Features computed only from matches strictly before prediction date. No future results in training folds.

## 8. Betting appendix

Model probabilities compared to normalized market implied probabilities (decimal odds). "Value" flagged when model exceeds market by >5%. Historical backtest ROI reported honestly — expect ~0%.

## 9. Limitations

- Started after 2026 group stage; no group-stage pre-registration
- Small international sample (~15k matches vs millions of club games)
- No injury API integration (manual squad updates recommended)
- FBref not used (Sports Reference prohibits bulk ML training on scraped data)
- Illustrative market odds in betting report; replace with live API for production

## 10. Reproducibility

```bash
make ingest && make train && make predict ROUND=r32
```

All prediction JSON files include `locked_at` UTC timestamp and `model_version`.
