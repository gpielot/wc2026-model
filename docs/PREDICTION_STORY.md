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

This is the kind of miss that keeps the project honest. The model gave Germany a edge, but not a landslide — Paraguay’s win probability was still around 26%, plus draw chance. An upset, not a miracle. Still: **wrong winner**.

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

## Chapter 3 — Round of 16: my next locked predictions

These are published **before** the Round of 16 kicks off (4 July 2026). I will not change them after kickoff.

### Confirmed FIFA fixtures

| Date | Match | **Predicted winner** | P(win) | Notes |
|------|-------|----------------------|--------|-------|
| **4 Jul** | Canada vs Morocco | **Morocco** | 40.9% | Co-host Canada, but model likes Morocco’s run |
| **4 Jul** | Paraguay vs France | **France** | 61.9% | Paraguay’s giant-killing run meets France |
| **5 Jul** | Brazil vs Norway | **Brazil** | 67.3% | Haaland vs Seleção — model backs Brazil |
| **5 Jul** | Mexico vs England | **England** | 36.8% | Very tight; slight edge to England |
| **6 Jul** | USA vs Belgium | **Belgium** | 56.8% | Belgium’s comeback spirit + squad depth |

### Probable fixtures (pending final R32 results, 2–3 Jul)

The model also projects winners for the remaining Round of 32 ties, then builds probable Round of 16 pairings:

| Pending R32 | Model pick | Probable R16 | Model pick |
|-------------|------------|--------------|------------|
| Spain vs Austria | **Spain** (64%) | Portugal vs Spain | **Spain** (41%) |
| Portugal vs Croatia | **Portugal** (55%) | | |
| Switzerland vs Algeria | **Switzerland** (47%) | Colombia vs Switzerland | **Colombia** (51%) |
| Australia vs Egypt | **Australia** (TBD%) | Argentina vs Australia | **Argentina** (77%) |
| Argentina vs Cape Verde | **Argentina** (77%) | | |
| Colombia vs Ghana | **Colombia** (51%) | | |

> When the last R32 matches finish, I'll run `make update-r16` again, update this diary, and push a new locked JSON.

---

## How to follow along

1. **This file** — the narrative (`docs/PREDICTION_STORY.md`)
2. **Technical picks** — [`docs/R16_PREDICTIONS.md`](R16_PREDICTIONS.md)
3. **Raw probabilities** — [`predictions/`](../predictions/) (JSON, timestamped)
4. **Full methodology** — [`docs/METHODOLOGY.md`](METHODOLOGY.md) and the [research paper](Who_Scores_WC2026_Research_Paper.docx)

---

## Chapters to come (I'll update as matches finish)

- [ ] **Round of 16 results** — did Morocco beat Canada? Did Brazil hold off Norway?
- [ ] **Quarter-finals** — `make update-r16` → new chapter
- [ ] **Semi-finals**
- [ ] **Final** — 19 July 2026, MetLife Stadium

---

*Last updated: 2 July 2026. Model version: `v3-r16-real-bracket`.*
