# Prediction Story — World Cup 2026

A running diary of what the model said **before** each round, what actually happened, and what we predict next. Every entry is timestamped and frozen in [`predictions/`](../predictions/) so nothing gets edited after kickoff.

---

## Chapter 0 — Late to the party (2 July 2026)

I started this project after the group stage had already finished. That means I missed the chance to pre-register group-stage picks — but I can still run an honest knockout diary from the Round of 32 onward.

First locked file: [`predictions/r32_2026-06-30.json`](../predictions/r32_2026-06-30.json) (synthetic bracket — see note below).

---

## Chapter 1 — Round of 32: the first real test

After training on 49,000+ international matches, player skills from StatsBomb, tactical styles, and squad chemistry, I ran the model on the **actual** World Cup fixtures (not just our simplified bracket).

### Brazil vs Japan — ✅ Got it right

| | Model | Reality |
|---|--------|---------|
| **Fixture** | Brazil vs Japan (R32, 29 Jun) | Brazil 2–1 Japan |
| **Our call** | **Brazil** to win (~58% win probability) | Brazil won in 90 minutes |

The model liked Brazil’s attack rating and recent form. Japan had pushed Netherlands to a draw in the group stage, but in a head-to-head projection Brazil were clear favourites. Football agreed.

### Germany vs Paraguay — ❌ Missed the upset

| | Model | Reality |
|---|--------|---------|
| **Fixture** | Germany vs Paraguay (R32, 29 Jun) | 1–1, **Paraguay** won 4–3 on penalties |
| **Our call** | **Germany** (~44% win probability) | Paraguay eliminated the four-time champions |

This is the kind of miss that keeps the project honest. The model gave Germany an edge, but not a landslide — Paraguay’s win probability was still around 26%, plus draw chance. An upset, not a miracle. Still: **wrong winner**.

Other R32 results the model would have leaned correctly on (post-hoc, same weights):

| Match | Result | Model lean |
|-------|--------|------------|
| France 3–0 Sweden | France win | ✅ France |
| Brazil 2–1 Japan | Brazil win | ✅ Brazil |
| Netherlands 1–1 Morocco (pens) | Morocco win | ❌ Netherlands |
| Belgium 3–2 Senegal (aet) | Belgium win | ✅ Belgium |
| Mexico 2–0 Ecuador | Mexico win | ✅ Mexico |
| England 2–1 DR Congo | England win | ✅ England |

**Scorecard after 10 completed R32 ties:** roughly **7–8 correct winners** depending on how you count tight calls and penalty shootouts — good, not magic.

---

## Chapter 2 — Model update (2 July 2026)

I fed all completed R32 results through July 1 into the pipeline, refreshed [martj42](https://github.com/martj42/international_results) data, and **retrained** the ensemble.

```bash
make update-r16
```

Locked output: [`predictions/r16_real_bracket_2026-07-02.json`](../predictions/r16_real_bracket_2026-07-02.json)

---

## Chapter 3 — Round of 16: my locked predictions (before kickoff)

These were published **before** the Round of 16 began (4 July 2026).

### Confirmed FIFA fixtures

| Date | Match | **Predicted winner** | P(win) | Result |
|------|-------|----------------------|--------|--------|
| **4 Jul** | Canada vs Morocco | **Morocco** | 40.9% | ✅ Morocco 3–0 |
| **4 Jul** | Paraguay vs France | **France** | 61.9% | ✅ France 1–0 |
| **5 Jul** | Brazil vs Norway | **Brazil** | 67.3% | ❌ Norway 2–1 |
| **5 Jul** | Mexico vs England | **England** | 36.8% | ✅ England 3–2 |
| **6 Jul** | USA vs Belgium | **Belgium** | 56.8% | ✅ Belgium 4–1 |
| **6 Jul** | Portugal vs Spain | **Spain** | 40.6% | ✅ Spain 1–0 |

**R16 scorecard (6/8 played): 5 correct, 1 wrong.** The Brazil miss hurt — Haaland’s late double sent Norway to their first World Cup quarter-final and ended Brazil’s earliest exit since 1990.

### Probable fixtures (pending final R32 results, 2–3 Jul)

| Pending R32 | Model pick | Actual | Correct? |
|-------------|------------|--------|----------|
| Spain vs Austria | **Spain** (64%) | Spain 3–0 | ✅ |
| Portugal vs Croatia | **Portugal** (55%) | Portugal 2–1 | ✅ |
| Switzerland vs Algeria | **Switzerland** (47%) | Switzerland 2–0 | ✅ |
| Australia vs Egypt | **Australia** (35%) | Egypt on pens | ❌ (coin flip) |
| Argentina vs Cape Verde | **Argentina** (77%) | Argentina 3–2 (aet) | ✅ |
| Colombia vs Ghana | **Colombia** (51%) | Colombia 1–0 | ✅ |

**Final R32 day: 5/6.** Egypt’s penalty shootout win over Australia was essentially a toss-up in the model (~35% vs ~35%).

---

## Chapter 4 — Round of 16: the big upset (5 July 2026)

### Brazil vs Norway — ❌ The one that stung

| | Model | Reality |
|---|--------|---------|
| **Fixture** | Brazil vs Norway (R16, 5 Jul) | **Norway 2–1 Brazil** |
| **Our call** | **Brazil** (67.3% win probability) | Haaland brace; Neymar’s late pen was only a consolation |

This was our highest-confidence R16 pick — and our worst miss of the tournament so far. The model saw Brazil’s attack and Norway’s thin squad history and backed the five-time champions comfortably. Erling Haaland had other ideas.

Everything else from the locked 2 July file held up: Morocco dismantled Canada, France edged Paraguay, England survived a thriller in Mexico City, Belgium routed the USA, and Spain beat Portugal in Dallas.

---

## Chapter 5 — Model update (7 July 2026)

All 16 Round of 32 ties are in. Six of eight Round of 16 matches are done. I ingested everything through July 6, refreshed martj42, and retrained:

```bash
make update-r16   # now publishes QF bracket + remaining R16
```

Locked output: [`predictions/qf_real_bracket_2026-07-07.json`](../predictions/qf_real_bracket_2026-07-07.json)

---

## Chapter 6 — Tonight’s R16 + next week’s quarter-finals

### Still to play tonight (7 July)

| Match | **Predicted winner** | P(win) | Notes |
|-------|----------------------|--------|-------|
| Argentina vs Egypt | **Argentina** | 70.5% | Defending champs after Cape Verde scare |
| Colombia vs Switzerland | **Colombia** | 49.9% | Essentially a coin flip |

### Quarter-finals — locked before kickoff

| Date | Match | **Predicted winner** | P(win) |
|------|-------|----------------------|--------|
| **9 Jul** | France vs Morocco | **France** | 57.4% |
| **10 Jul** | Spain vs Belgium | **Spain** | 60.6% |
| **11 Jul** | Norway vs England | **England** | 55.8% |
| **11 Jul** | Argentina vs Colombia* | **Argentina** | 43.5% |

\*Probable fixture — depends on tonight’s R16 results. If Egypt or Switzerland pull upsets, I’ll rerun `make update-r16` and push a corrected QF file.

Technical details: [`docs/QF_PREDICTIONS.md`](QF_PREDICTIONS.md) · [`docs/R16_PREDICTIONS.md`](R16_PREDICTIONS.md)

---

## Running scorecard

| Round | Picks tracked | Correct | Hit rate |
|-------|---------------|---------|----------|
| R32 (first 10) | 10 | ~7–8 | ~75% |
| R32 (final 6) | 6 | 5 | 83% |
| R16 (played) | 6 | 5 | 83% |
| **Overall** | **22** | **~17–18** | **~77%** |

The model is useful, not clairvoyant. Paraguay over Germany, Norway over Brazil, and Egypt over Australia were all in the “possible but not likely” bucket — which is exactly where real World Cups live.

---

## How to follow along

1. **This file** — the narrative (`docs/PREDICTION_STORY.md`)
2. **Technical picks** — [`docs/QF_PREDICTIONS.md`](QF_PREDICTIONS.md) · [`docs/R16_PREDICTIONS.md`](R16_PREDICTIONS.md)
3. **Raw probabilities** — [`predictions/`](../predictions/) (JSON, timestamped)
4. **Full methodology** — [`docs/METHODOLOGY.md`](METHODOLOGY.md) and the [research paper](Who_Scores_WC2026_Research_Paper.docx)

---

## Chapters to come

- [x] **Round of 32 complete** — all 16 ties decided
- [x] **Round of 16 results (partial)** — Brazil upset logged
- [ ] **Round of 16 tonight** — Argentina/Egypt, Colombia/Switzerland
- [ ] **Quarter-finals** — France–Morocco kicks off 9 July
- [ ] **Semi-finals**
- [ ] **Final** — 19 July 2026, MetLife Stadium

---

*Last updated: 7 July 2026. Model version: `v4-qf-real-bracket`.*
