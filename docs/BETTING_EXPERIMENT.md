# Betting Experiment — World Cup 2026 Knockouts

A small, research-only bankroll run against Superbet during the 2026 knockouts. Stakes were chosen roughly by gut (usually flat **5 PLN**, sometimes **2–6 PLN**). This write-up compares every slip to the model’s locked probabilities and asks what **Kelly sizing** would have recommended.

**Disclaimer:** entertainment / process review only. Past results ≠ future edge. Polish licensed books deduct a **12% stake tax** before odds apply (`wypłata ≈ stawka × 0.88 × kurs`).

---

## Summary

| Metric | Value |
|--------|------:|
| Bets | **31** |
| Record | **18–13** (58% hit rate) |
| Staked | **140.00 PLN** |
| Returned | **134.99 PLN** |
| Net P&L | **−5.01 PLN** |
| ROI | **−3.6%** |

Roughly break-even. Good enough to learn from; not evidence of a sustainable edge.

Raw ledger: [`betting_ledger.json`](betting_ledger.json)

---

## Two markets we mixed

| Slip label | Meaning | Model column |
|------------|---------|--------------|
| **Mecz 1/2/X** | Result after **90 minutes** | Regulation W/D/L |
| **Awans / Finał–zwycięzca / 3.miejsce** | Who progresses / lifts the cup (**ET + pens**) | Advancement (no draw) |

Default habit: **same stake on Mecz and Awans** for the same team. That is a soft hedge, not optimal sizing — it **doubles exposure** to one side.

### How the dual pattern played out

| Match | Mecz | Awans / to-win | Pair P&L |
|-------|------|----------------|---------:|
| USA–Belgium | Belgium W | Belgium W | **+10.42** |
| England–Argentina | Argentina W | Argentina W | **+9.61** |
| Mexico–England | England W | England W | **+8.44** |
| Portugal–Spain | Spain W | Spain W | **+5.14** |
| Portugal–Croatia | Portugal W | Portugal W | **+3.47** |
| Spain–Belgium | Spain W | Spain W | **+2.98** |
| France–Morocco | France W | France W | **+2.63** |
| Norway–England | England L (ET) | England W | **−1.36** |
| Spain–Argentina Final | Spain L (90) | Spain W | **−3.18** |
| Argentina–Switzerland | Argentina L (ET) | Argentina W | **−4.10** |
| Brazil–Norway | Brazil L | Brazil L | **−10.00** |
| Switzerland–Colombia | Colombia L | Colombia L | **−10.00** |
| France–England 3rd | France L | France L | **−12.00** |

**Best case:** win both in 90. **Middle:** advance only via ET/pens (lose Mecz, win Awans). **Worst:** both lose → −2× stake.

---

## Kelly criterion (and why it “never worked”)

Kelly fraction of bankroll for a decimal price after tax:

\[
b = o \times 0.88 - 1,\quad
f^* = \frac{b\,p - (1-p)}{b}
\]

Bet only if \(f^* > 0\). Use **half-Kelly** in practice.

### Why short favourites fail Kelly

For kurs **1.40**, taxed \(b = 1.40\times0.88 - 1 = 0.232\). You need

\[
p > \frac{1}{1+b} \approx 81\%
\]

just to clear Kelly. Our model rarely prices knockout favourites that high versus the book **after tax**. So:

- Many bets that *look* slightly +EV vs raw `1/odds` still have **Kelly = 0** once tax is included.
- Only **7 of 31** slips had Kelly &gt; 0 in the audit.
- Wins on France @ 1.28 or Spain @ 1.31 do **not** prove +EV — they can be −EV luck.

That matches the feel that “the book’s premium never covers the risk”: on short prices, it usually doesn’t.

---

## Model edge vs book (this sample)

| Bucket | N | Staked | Returned | Net | ROI |
|--------|--:|-------:|---------:|----:|----:|
| Model **+edge** (p &gt; 1/odds) | 13 | 55.00 | 47.57 | **−7.43** | −13.5% |
| Model **−edge** | 18 | 85.00 | 87.42 | **+2.42** | +2.8% |

Small-sample irony: −edge finished ahead, +edge behind — driven by **Brazil–Norway** (model overconfident; see [PREDICTION_STORY.md](PREDICTION_STORY.md) Chapter 9) and variance. Process still matters more than one tournament’s P&L.

### Bets with Kelly &gt; 0 (taxed)

| Match | Market | Odds | Model p | Kelly | Result | Actual stake |
|-------|--------|-----:|--------:|------:|:------:|-------------:|
| Australia–Egypt | Mecz Australia | 8.75 | 35% | 26% | L | 2 |
| Brazil–Norway | Mecz Brazil | 1.78 | 67% | 10% | L | 5 |
| USA–Belgium | Awans Belgium | 1.92 | 72% | 30% | W | 5 |
| USA–Belgium | Mecz Belgium | 2.72 | 57% | 26% | W | 5 |
| Argentina–Switzerland | Mecz Argentina | 1.75 | 70% | 15% | L | 5 |
| England–Argentina | Awans Argentina | 2.00 | 64% | 17% | W | 6 |
| England–Argentina | Mecz Argentina | 3.05 | 43% | 9% | W | 3 |

Best real edges that paid: **Belgium** and **Argentina SF**. Worst “edge”: **Brazil** (pedigree miss) and longshot **Australia** (right to stake small).

---

## Counterfactual: half-Kelly only

Assume start bank **100 PLN**, bet only when Kelly &gt; 0, stake = half-Kelly capped at 10% of bank:

| Result | Value |
|--------|------:|
| Final bank | **≈ 110 PLN** |
| Net | **≈ +10 PLN** |

Still a toy sample — but the *process* (skip tax-dead shorties, size up real edges) is the takeaway.

---

## What should have been done better

### 1. Size each market on its own edge
Do **not** default to equal PLN on Mecz and Awans.  
- If the edge is on **advancement**, bet Awans only (or smaller Mecz).  
- If 90-min odds are long vs the model (Belgium 2.72, Argentina 3.05), Mecz is the value leg.

### 2. Use half-Kelly after the 12% tax
Skip when \(f^* = 0\). Cap ~5–10% of bank. Flat 5 PLN ignored bankroll and edge entirely.

### 3. Skip most short favourites after tax
France 1.28 awans, Spain 1.31, Portugal 1.34 — typically −EV in our sheet even when they won. Reducing stakes to 2 PLN on France–Spain was the right *direction*.

### 4. Trust measured edges, not pedigree
Size up: Belgium R16, Argentina SF.  
Size down / skip: Brazil (see post-mortem), thin Colombia “edges”, speculative Australia longs (tiny stake only).

### 5. Separate gut from model
Gut stake cuts were sometimes correct (France–Spain cluster) and sometimes just noise. Rule: **no bet unless model edge clears tax**; gut only adjusts *within* that filter (e.g. half vs quarter Kelly).

---

## Full ledger

| Date | Match | Market | Pick | Stake | Odds | Model | Edge | Kelly | Res | P&L |
|------|-------|--------|------|------:|-----:|------:|-----:|------:|:---:|----:|
| 03 Jul | Portugal–Croatia | Awans | Portugal | 5 | 1.34 | 68% | −7% | — | W | +0.90 |
| 03 Jul | Portugal–Croatia | Mecz | Portugal | 5 | 1.72 | 55% | −4% | — | W | +2.57 |
| 03 Jul | Australia–Egypt | Mecz | Australia | 2 | 8.75 | 35% | +24% | 26% | L | −2.00 |
| 06 Jul | Brazil–Norway | Awans | Brazil | 5 | 1.39 | 77% | +5% | — | L | −5.00 |
| 06 Jul | Brazil–Norway | Mecz | Brazil | 5 | 1.78 | 67% | +11% | 10% | L | −5.00 |
| 06 Jul | Portugal–Spain | Awans | Spain | 5 | 1.49 | 56% | −11% | — | W | +1.56 |
| 06 Jul | Portugal–Spain | Mecz | Spain | 5 | 1.95 | 41% | −11% | — | W | +3.58 |
| 06 Jul | Mexico–England | Awans | England | 5 | 1.74 | 52% | −5% | — | W | +2.66 |
| 06 Jul | Mexico–England | Mecz | England | 5 | 2.45 | 37% | −4% | — | W | +5.78 |
| 07 Jul | USA–Belgium | Awans | Belgium | 5 | 1.92 | 72% | +19% | 30% | W | +3.45 |
| 07 Jul | USA–Belgium | Mecz | Belgium | 5 | 2.72 | 57% | +20% | 26% | W | +6.97 |
| 07 Jul | Argentina–Egypt | Mecz | Argentina | 5 | 1.35 | 70% | −4% | — | W | +0.94 |
| 07 Jul | Switzerland–Colombia | Mecz | Colombia | 5 | 2.25 | 50% | +5% | — | L | −5.00 |
| 08 Jul | Switzerland–Colombia | Awans | Colombia | 5 | 1.61 | 63% | +1% | — | L | −5.00 |
| 10 Jul | France–Morocco | Awans | France | 5 | 1.28 | 72% | −6% | — | W | +0.63 |
| 10 Jul | France–Morocco | Mecz | France | 5 | 1.59 | 58% | −5% | — | W | +2.00 |
| 10 Jul | Spain–Belgium | Mecz | Spain | 5 | 1.64 | 59% | −2% | — | W | +2.22 |
| 10 Jul | Spain–Belgium | Awans | Spain | 5 | 1.31 | 71% | −6% | — | W | +0.76 |
| 12 Jul | Argentina–Switzerland | Mecz | Argentina | 5 | 1.75 | 70% | +13% | 15% | L | −5.00 |
| 12 Jul | Argentina–Switzerland | Awans | Argentina | 5 | 1.34 | 82% | +7% | — | W | +0.90 |
| 12 Jul | Norway–England | Awans | England | 2 | 1.50 | 71% | +5% | — | W | +0.64 |
| 12 Jul | Norway–England | Mecz | England | 2 | 1.97 | 56% | +6% | — | L | −2.00 |
| 14 Jul | France–Spain | Awans | France | 2 | 1.75 | 48% | −9% | — | L | −2.00 |
| 14 Jul | France–Spain | 1X | France/Draw | 2 | 1.40 | 68% | −3% | — | L | −2.00 |
| 14 Jul | France–Spain | Mecz | Draw | 2 | 3.25 | 29% | −2% | — | L | −2.00 |
| 15 Jul | England–Argentina | Awans | Argentina | 6 | 2.00 | 64% | +14% | 17% | W | +4.56 |
| 15 Jul | England–Argentina | Mecz | Argentina | 3 | 3.05 | 43% | +10% | 9% | W | +5.05 |
| 19 Jul | France–England 3rd | To win | France | 6 | 1.44 | 63% | −7% | — | L | −6.00 |
| 19 Jul | France–England 3rd | Mecz | France | 6 | 1.82 | 49% | −6% | — | L | −6.00 |
| 19 Jul | Spain–Argentina Final | To win | Spain | 6 | 1.67 | 53% | −7% | — | W | +2.82 |
| 19 Jul | Spain–Argentina Final | Mecz | Spain | 6 | 2.42 | 39% | −2% | — | L | −6.00 |

*Edge = model probability − 1/odds. Kelly uses taxed odds. Model probs from locked prediction JSON (regulation for Mecz; advancement for Awans / to-win).*

---

## Playbook for a next tournament

1. Lock model probs **before** kickoff (already doing this).  
2. For each market, compute edge and **taxed Kelly**.  
3. Bet **only** if Kelly &gt; 0; stake = half-Kelly × bank (cap 10%).  
4. Prefer the market where the edge lives (90 vs to-win).  
5. Log every slip next to the lock file — same format as `betting_ledger.json`.

See also: [betting_edge_report.md](betting_edge_report.md) · [PREDICTION_STORY.md](PREDICTION_STORY.md) · [FINAL_PREDICTIONS.md](FINAL_PREDICTIONS.md)
