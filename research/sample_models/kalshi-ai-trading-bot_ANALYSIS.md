# Analysis: ryanfrigo/kalshi-ai-trading-bot (MIT) — what it teaches the diesel bot

Read 2026-11-26. Source copy: `research/sample_models/kalshi-ai-trading-bot/` (upstream commit `5d7b70a`, 2026-11-08).

## 1. What it is

A Kalshi toolkit whose main feature is **measuring** edge, not claiming it. It trades a live account (LLM-driven and
rule-based example strategies) and publishes its own verdict, losses included:

- Live track record (2026-10-02, `docs/TRACK_RECORD.md`): **NO MEASURED EDGE**, n=55 forward trades, won 58% vs 60% implied (edge −1.9 pts), Brier 0.2356.
- Whole account: 200 settled markets, 62% win rate, **−$156.59**. NO side +$32 (78% win), YES side −$189 (44% win).
- Calibration: its 50–85% calls won only 44% → overconfident.

Lesson: a polished bot with an LLM and a dashboard still had no edge. Measurement first.

## 2. The part built for OUR market: its AAA diesel/gas model

`docs/AAA.md`, `scripts/aaa_data.py`, `aaa_futures.py`, `aaa_pricer.py`, `fee_backtest_aaa.py`, data in `data/aaa/`.
It covers KXDIESELD, KXAAAGASD, weekly/monthly diesel and gas.

| Their finding | Our status | What to do |
|---|---|---|
| Daily AAA change (20 months, n=294): mean +0.53¢, sd 2.53¢, median 0 | We have Aug→Nov (median move 1.43¢) | Use their `data/aaa/aaa_daily.csv` (Jan 2025→, diesel + regular) to lengthen our history |
| **Retail lags wholesale futures ~4–7 days** (lag-7 R² ≈ 0.42) | Our F formula uses HO today + prior 5 days | Test lags 1–7 explicitly (open question #2, rockets & feathers) |
| **Excess gap** = (retail − wholesale) vs its trailing baseline = pending retail move. Gap-closing episodes run **~2¢/day** (Apr 2026: 18¢/11d; May 2026: 49¢/23d) | Our "swollen delivery slice" ($1.50 vs $0.84) is the same idea | Add `excess_gap` + `days_to_close` columns; check whether the ladder prices the 2¢/day rate correctly |
| Streak model looked like a 40-pt edge on 2026-09-26 but was **wrong**: it ignored wholesale. Ladder was efficient | Matches our momentum-only failure on Nov 25 | Rule: never fade the ladder on retail history alone |
| "Genuine edge, if it exists, is more likely in (a) the **rate** of convergence and (b) the **multi-day path** (weekly/monthly ladders), not tomorrow's single print" | We only look at the daily | New idea card: test weekly/monthly diesel ladders |
| Market for day D closes ~1:59 AM ET, before the ~3–4 AM AAA update | Our notes: close 11:59 PM (Nov) / ~1:59 AM (Aug–Sep) | Re-check the close time when the AAA flip log has a week of data |
| AAA page sometimes serves **stale pairs** (CDN cache) → they use Current − Yesterday from the same page | Our recorder reads the page every 15 min | Check our flip log for stale reads |
| State model built on Wayback rows was broken (91% were national pages) | We hit the same archive traps | Good warning for our L2 state work |

## 3. Its edge-measurement harness (fits our cards 9, 10, 22, 23)

`src/agent/edge.py` (pure functions, unit-tested):
- `brier_score`, `log_loss` — is a "70%" really 70%?
- `edge_vs_book` = realized win rate − average price paid. Positive = beat the book.
- `forward_only` guard — only counts trades whose market resolved **after** the trade (no look-ahead).
- `edge_report` refuses to claim edge below 10 forward-settled trades.
- `src/agent/policy.py` — auto-blocks categories with ≥5 settled trades and negative P&L; shrinks overconfident probability bands.
- `scripts/fee_backtest_aaa.py` — fee-aware backtest with look-ahead guard and bootstrap CIs **clustered by print day** (same method as our `tools/edge_check.py`).

## 4. Mapping to our system

| Part | Their bot | Ours |
|---|---|---|
| Fair value | AAA change distribution + wholesale convergence gap | Engine Room L0–L3, F formula, truckstops |
| Market price | Ladder read through NO-bid complement | Live recorder, order book |
| Costs | Quadratic taker fee, per-order rounding | Same formula |
| Scale | Fee-aware edge per strike, alerts | Edge test #9 (not built) |
| Report card | Brier model vs book mid, `scores.jsonl` | Not built |
| Safety | Risk governor, edge policy blocks | Not built |

## 5. Next steps it suggests

1. Merge their `aaa_daily.csv` into our warehouse as a history source (credit + MIT notice).
2. Build `excess_gap` (retail − HO vs trailing baseline) and test whether it predicts tomorrow's AAA better than our F formula.
3. Port the `edge.py` scoring idea into our edge test: Brier model vs book, forward-only, clustered CIs.
4. Look at weekly/monthly diesel ladders as a second market (multi-day path).
