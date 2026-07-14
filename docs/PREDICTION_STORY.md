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

### Australia vs Egypt — ❌ Missed, and it changed tonight’s fixture

| | Model | Reality |
|---|--------|---------|
| **Fixture** | Australia vs Egypt (R32, 3 Jul) | 1–1, **Egypt** won 4–2 on penalties |
| **Our call** | **Australia** (~35% win probability) | Egypt advanced; Mohamed Salah’s panenka in the shootout |

The model had this as a coin flip — Australia 35%, Egypt 35%, draw ~30% — but it still leaned **Australia**. Egypt’s win matters beyond the scorecard: our 2 July R16 lock assumed Australia would beat Egypt and face Argentina. **That bracket path was wrong.** Egypt are through instead, so tonight’s Round of 16 tie is **Argentina vs Egypt** — not Argentina vs Australia.

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

**Final R32 day: 5/6.** Egypt’s penalty shootout win over Australia was essentially a toss-up in the model (~35% vs ~35%) — but picking Australia meant we projected the wrong Round of 16 pairing (see below).

---

## Chapter 3b — The bracket miss: Argentina vs Australia (that never was)

When we locked R16 predictions on **2 July**, six Round of 32 ties were still unplayed. The model filled in probable winners — including **Australia over Egypt** — and built the bracket from there.

That produced this **wrong** probable fixture in [`predictions/r16_real_bracket_2026-07-02.json`](../predictions/r16_real_bracket_2026-07-02.json):

| What we projected (2 Jul) | What actually happened |
|---------------------------|------------------------|
| Australia beats Egypt | ❌ Egypt won on penalties (3 Jul) |
| **Argentina vs Australia** in R16 | **Argentina vs Egypt** in R16 |

So we never “predicted Australia would win tonight” — we predicted Australia would win **last Friday** in the Round of 32. They didn’t. Egypt did. That’s why today’s match is **Egypt vs Argentina** in Atlanta, not the Socceroos.

After ingesting the real results on 7 July, the updated lock has the correct pairings. See [`predictions/qf_real_bracket_2026-07-07.json`](../predictions/qf_real_bracket_2026-07-07.json).

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

## Chapter 6 — Round of 16 finale (7 July 2026)

Two ties closed out the Round of 16. Both were locked in [`predictions/qf_real_bracket_2026-07-07.json`](../predictions/qf_real_bracket_2026-07-07.json) before kickoff.

| Match | **Predicted winner** | P(win) | Result | Correct? |
|-------|----------------------|--------|--------|------------|
| Argentina vs Egypt | **Argentina** | 70.5% | Argentina **3–2** | ✅ |
| Colombia vs Switzerland | **Colombia** | 49.9% | 0–0, **Switzerland** 4–3 pens | ❌ |

Argentina trailed 2–0 and rallied with goals from Romero, Messi, and Fernández in the final 13 minutes — another escape act for the defending champions. Switzerland held Colombia goalless for 120 minutes and won the shootout, booking their first World Cup quarter-final since 1954.

That Switzerland upset also fixed the bracket: our 7 July file wrongly projected **Argentina vs Colombia** in the quarters. The real QF is **Argentina vs Switzerland**.

---

## Chapter 7 — Model update (9 July 2026)

All Round of 32 and Round of 16 ties are now ingested (24 knockout matches). Retrained on fresh martj42 data:

```bash
make update-r16
```

Locked output: [`predictions/qf_real_bracket_2026-07-09.json`](../predictions/qf_real_bracket_2026-07-09.json)

---

## Chapter 8 — Quarter-finals: locked predictions

| Date | Match | **Predicted winner** | P(win) | Status |
|------|-------|----------------------|--------|--------|
| **9 Jul** | France vs Morocco | **France** | 57.4% | Tonight — kicks off ~10pm CET |
| **10 Jul** | Spain vs Belgium | **Spain** | 60.6% | |
| **11 Jul** | Norway vs England | **England** | 56.4% | See Chapter 9 post-mortem |
| **11 Jul** | Argentina vs Switzerland | **Argentina** | 68.5% | Corrected from Argentina–Colombia |

Technical details: [`docs/QF_PREDICTIONS.md`](QF_PREDICTIONS.md)

---

## Chapter 9 — Post-mortem: why we picked Brazil over Norway

Before **Norway vs England** (11 Jul), it is worth dissecting our worst Round of 16 miss — Brazil at **67.3%** when Norway won **2–1**.

### What we said vs what happened

| | Model (locked 2 Jul) | Reality (5 Jul) |
|---|---------------------|-----------------|
| Brazil win | **67.3%** | Lost 1–2 |
| Norway win | 11.1% | Haaland brace |
| Expected goals | Brazil **2.12** – Norway **0.50** | Actual: **1–2** |

### Root cause 1 — Historical pedigree dominated

| Signal | Brazil | Norway |
|--------|--------|--------|
| Dynamic Elo (pre-match) | ~1,944 | ~1,771 (**+173**) |
| Dixon–Coles home win | **73.0%** | 7.9% |
| Dixon–Coles xG | **2.05** | **0.52** |

Dixon–Coles learns from decades of internationals. Brazil are a perennial top side; Norway are mid-tier historically. That prior alone drove most of the 67% figure. **Tournament Norway** (7 goals in two group games, R32 win over Ivory Coast) were not priced as a hot team — only as “Norway.”

### Root cause 2 — No player-level signal for Norway (Haaland blind spot)

| Team | Players in skill model |
|------|------------------------|
| Brazil | 26 |
| England | 21 |
| **Norway** | **0** |

Player skills come from StatsBomb events. Norway’s squad is outside that pipeline, so **Erling Haaland’s tournament form never entered the model**. We priced Norway at 0.5 xG; Haaland scored twice.

### Root cause 3 — World Cup form bug (now fixed)

The gradient-boosting leg uses `home_form` / `away_form` from recent World Cup matches. Those features queried tournament name `"FIFA World Cup 2026"`, but **group-stage games in martj42 are stored as `"FIFA World Cup"`**. Both teams defaulted to **1.5 PPG** even though actual 2026 form was:

| Team | Group PPG (actual) |
|------|-------------------|
| Norway | **3.00** |
| Brazil | **2.33** |
| England | **2.00** |

Even with Norway at 3.0 PPG manually, Brazil win probability only moved **66.5% → ~70%** — form alone would not have flipped the pick. **Fix applied in v5.1:** `team_wc2026_form()` now merges both tournament labels.

### Root cause 4 — Both sub-models agreed

| Component | Brazil win |
|-----------|------------|
| Dixon–Coles (45%) | 73.0% |
| Gradient boosting (55%) | 61.2% |
| Style / chemistry | 0.0 (neutral) |

No internal disagreement. The ensemble was confidently wrong, not split.

### Root cause 5 — Football variance

Brazil missed a penalty; Endrick and Vinícius Jr had clear chances; **Nyland** (Norway GK) was excellent. Norway scored twice from fewer chances — a high-variance knockout where the favourite created more but converted less. The model predicts **average team strength**; upsets still happen (~11% is not 0%).

### Implications for Norway vs England (11 Jul)

Current lock (v5.1, form fix): **England 56.4%** | Draw 27.7% | Norway **15.9%** | xG 0.68 – 1.56

**What is better than Brazil–Norway:** the Elo gap is smaller (~−106 vs +173), and England is **56%** not 67% — less overconfidence.

**What still applies:** no Haaland in player skills; Dixon–Coles still underrates Norway attack; post-Brazil momentum is only partially captured via Elo.

**Honest read:** 16% on Norway may still be low in spirit (same blind spots), but England are rightly favourites — deeper squad, player skills in the model, higher Elo. **Trust England as lean favourite, not a lock.** If Haaland gets 2–3 chances, that may be enough again.

---

## Chapter 10 — Quarter-finals: our best round yet

All four quarter-finals locked in [`predictions/qf_real_bracket_2026-07-09.json`](../predictions/qf_real_bracket_2026-07-09.json) (v5.1) before kickoff.

| Match | **Our pick** | P(win) | Result | Correct? |
|-------|--------------|--------|--------|----------|
| France vs Morocco | **France** | 58.1% | France **2–0** | ✅ |
| Spain vs Belgium | **Spain** | 58.5% | Spain **2–1** | ✅ |
| Norway vs England | **England** | 56.4% | England **2–1** (aet) | ✅ |
| Argentina vs Switzerland | **Argentina** | 70.3% | Argentina **3–1** (aet) | ✅ |

**Quarter-final scorecard: 4/4 — 100%.** Mbappé (pen miss, then goal + assist) sent France through; Merino’s 88th-minute winner kept Spain’s clean-sheet run alive until Belgium scored; Bellingham’s brace rescued England after Norway led; Álvarez’s extra-time stunner settled Argentina–Switzerland.

On **Norway at 4.63**: the market implied ~22% Norway; we had ~16%. England won — so neither our model nor a “Norway may win” hunch paid off. Chapter 9’s read held: lean England favourite, not a lock, but Norway didn’t repeat the Brazil upset.

---

## Chapter 11 — Model update + semi-finals (14 July 2026)

All quarter-finals ingested. Retrained on fresh martj42 data:

```bash
make update-sf
```

Locked output: [`predictions/sf_real_bracket_2026-07-14.json`](../predictions/sf_real_bracket_2026-07-14.json)

### Semi-finals — locked before kickoff

| Date | Match | **Predicted winner** | P(win) | Notes |
|------|-------|----------------------|--------|-------|
| **14 Jul** (today) | France vs Spain | **Spain** (advance) | 52.3% | Coin flip at 90 min; see draw note below |
| **15 Jul** | England vs Argentina | **Argentina** (advance) | 64.1% | 2022 final rematch |

**Knockout breakdown** (new in v6.1): we now split **90-minute result** vs **to advance** (includes ET + pens). France–Spain at 90 min: **39% / 29% draw / 32%** — but **Spain to advance 52%** once tiebreaks are included.

**Draw bet @ 3.25?** The market implies **30.8%** draw at 90 minutes. Our model: **29.1%** → EV ≈ **−5%** per €1. Not +EV on our numbers. Breakeven needs ~**31%** draw at 90. Worth noting: neither France nor Spain has trailed at this World Cup, so a tight chess match is plausible — but the price already reflects that.

Technical details: [`docs/SF_PREDICTIONS.md`](SF_PREDICTIONS.md)

---

## Running scorecard

| Round | Picks tracked | Correct | Hit rate |
|-------|---------------|---------|----------|
| R32 (first 10) | 10 | ~7–8 | ~75% |
| R32 (final 6) | 6 | 5 | 83% |
| R16 (all 8) | 8 | 6 | 75% |
| **QF (all 4)** | **4** | **4** | **100%** |
| **Overall** | **28** | **~22** | **~79%** |

The model is useful, not clairvoyant. Paraguay over Germany, Norway over Brazil, Egypt over Australia, and Switzerland over Colombia were all in the “possible but not likely” bucket — which is exactly where real World Cups live.

---

## How to follow along

1. **This file** — the narrative (`docs/PREDICTION_STORY.md`)
2. **Technical picks** — [`docs/SF_PREDICTIONS.md`](SF_PREDICTIONS.md) · [`docs/QF_PREDICTIONS.md`](QF_PREDICTIONS.md)
3. **Raw probabilities** — [`predictions/`](../predictions/) (JSON, timestamped)
4. **Full methodology** — [`docs/METHODOLOGY.md`](METHODOLOGY.md) and the [research paper](Who_Scores_WC2026_Research_Paper.docx)

---

## Chapters to come

- [x] **Round of 16 complete** — all 8 ties decided
- [x] **Quarter-finals locked** — France–Morocco tonight (9 Jul)
- [x] **Brazil–Norway post-mortem** — Chapter 9
- [x] **Quarter-final results** — 4/4 correct
- [x] **Semi-finals locked** — France–Spain today (14 Jul)
- [ ] **Semi-final results**
- [ ] **Final** — 19 July 2026, MetLife Stadium

---

*Last updated: 14 July 2026. Model version: `v6.1-sf-knockout-breakdown`.*
