# Betting Edge Report

> **Disclaimer:** This is not financial advice. Markets are efficient.
> Historical backtests on international football rarely show sustained positive ROI.
> Use this for entertainment and model calibration assessment only.

**Generated from:** `r32_2026-06-30.json`
**Locked at:** 2026-07-02T13:53:41.583142+00:00

## Historical Calibration (Backtest)

- **2018**: log_loss=1.5246, brier=0.2935, n=929
- **2022**: log_loss=1.5525, brier=0.3088, n=970

## Round of 32 — Model vs Market

| Match | Outcome | Model | Market | Edge | Flag |
|-------|---------|-------|--------|------|------|
| Netherlands vs Japan | Netherlands | 50.1% | 51.1% | -1.0% |  |
| Netherlands vs Japan | Draw | 30.3% | 27.8% | +2.5% |  |
| Netherlands vs Japan | Japan | 19.6% | 21.0% | -1.5% |  |
| Argentina vs Senegal | Argentina | 56.8% | 64.4% | -7.6% |  |
| Argentina vs Senegal | Draw | 29.0% | 22.2% | +6.8% | **VALUE** |
| Argentina vs Senegal | Senegal | 14.2% | 13.3% | +0.9% |  |
| France vs Mexico | France | 47.2% | 60.0% | -12.8% |  |
| France vs Mexico | Draw | 32.2% | 24.5% | +7.7% | **VALUE** |
| France vs Mexico | Mexico | 20.6% | 15.5% | +5.1% | **VALUE** |
| England vs Colombia | England | 30.7% | 55.2% | -24.4% |  |
| England vs Colombia | Draw | 33.7% | 26.1% | +7.6% | **VALUE** |
| England vs Colombia | Colombia | 35.6% | 18.8% | +16.8% | **VALUE** |
| Brazil vs Ecuador | Brazil | 52.9% | 69.9% | -16.9% |  |
| Brazil vs Ecuador | Draw | 30.3% | 19.7% | +10.6% | **VALUE** |
| Brazil vs Ecuador | Ecuador | 16.8% | 10.5% | +6.3% | **VALUE** |
| Germany vs USA | Germany | 43.5% | 49.3% | -5.8% |  |
| Germany vs USA | Draw | 29.4% | 28.4% | +1.0% |  |
| Germany vs USA | USA | 27.0% | 22.3% | +4.7% |  |
| Spain vs Morocco | Spain | 53.8% | 62.3% | -8.4% |  |
| Spain vs Morocco | Draw | 30.3% | 23.4% | +7.0% | **VALUE** |
| Spain vs Morocco | Morocco | 15.8% | 14.4% | +1.4% |  |
| Portugal vs Uruguay | Portugal | 42.5% | 53.6% | -11.1% |  |
| Portugal vs Uruguay | Draw | 32.3% | 26.8% | +5.5% | **VALUE** |
| Portugal vs Uruguay | Uruguay | 25.2% | 19.6% | +5.6% | **VALUE** |
| Belgium vs Switzerland | Belgium | 46.9% | 44.7% | +2.3% |  |
| Belgium vs Switzerland | Draw | 31.2% | 29.3% | +1.9% |  |
| Belgium vs Switzerland | Switzerland | 21.9% | 26.0% | -4.2% |  |
| Croatia vs Denmark | Croatia | 42.6% | 46.7% | -4.1% |  |
| Croatia vs Denmark | Draw | 32.8% | 28.7% | +4.0% |  |
| Croatia vs Denmark | Denmark | 24.6% | 24.6% | +0.1% |  |
| Italy vs Austria | Italy | 38.1% | 56.7% | -18.6% |  |
| Italy vs Austria | Draw | 32.4% | 25.3% | +7.1% | **VALUE** |
| Italy vs Austria | Austria | 29.5% | 18.0% | +11.5% | **VALUE** |
| Poland vs South Korea | Poland | 43.0% | 42.4% | +0.5% |  |
| Poland vs South Korea | Draw | 32.3% | 30.1% | +2.1% |  |
| Poland vs South Korea | South Korea | 24.8% | 27.5% | -2.7% |  |

**Value flags (edge > 5%):** 12

## Honest Assessment

- Bookmakers incorporate injury news, insider squad info, and sharper closing lines.
- Our model uses public data only; expect **zero or negative long-run ROI** if blindly betting value flags.
- The primary value of this report is **calibration checking**: do 60% predictions win ~60% of the time?
- Recommended use: share probabilities with friends, compare against your own intuition.

## Champion Odds (Model Simulation)

- **Belgium**: 8.5%
- **Netherlands**: 7.1%
- **Croatia**: 6.1%
- **Argentina**: 5.7%
- **Italy**: 5.7%
- **Brazil**: 5.5%
- **Switzerland**: 5.3%
- **France**: 5.2%
- **Austria**: 4.6%
- **Poland**: 4.6%