# Component map: Formula N (bet cost) vs Formula F (settlement) — 2026-11-25

**Big picture:** F is 100% external (Kalshi reads AAA/OPIS's number; payout rule published). N is the crowd's belief
(built from external data) + Kalshi's published mechanics (fee, order book). Unknowns cluster in (a) how OPIS builds AAA,
(b) intraday station/rack info, (c) private market-maker models.

| # | Item (part of formula) | In N / F / Both | Sourcing | Status |
|---|---|---|---|---|
| 1 | AAA today (anchor) | Both | External: AAA site; Kalshi settlements | ✅ Have |
| 2 | Win $1 if AAA > line | F (defines N's question) | External: Kalshi rule | ✅ Have |
| 3 | Taker fee 0.07·P·(1−P) | N | External: Kalshi fee schedule | ✅ Have |
| 4 | Bid/ask spread | N | External: Kalshi order book API | ✅ Have (hourly) |
| 5 | Slippage / book depth | N | External: Kalshi order book API | ◐ Snapshot only |
| 6 | Chance math (bell curve) | N | Internal math | ✅ Have |
| 7 | Crowd wiggle σ | N | Internal math on Kalshi candles | ◐ Measured; why it shrinks unknown |
| 8 | Crowd bias (long shots overpriced) | N | Internal math on 68 days | ◐ Measured; small sample |
| 9 | Delivery squeeze −6.72%×(Delivery−$0.90) | Both | Internal math (fit) on AAA + HO + taxes | ◐ 67-day fit |
| 10 | Oil pass-through (HO futures moves) | Both | External: Yahoo HO=F (proxy) | ◐ Daily close only, no intraday |
| 11 | Brent crude | Both (crude slice) | External: Yahoo BZ=F | ✅ Have |
| 12 | Taxes 60.26¢ | Both | External: EIA | ✅ Have (Jan 2026 avg) |
| 13 | Momentum (yesterday's move) | N (crowd uses it) | Internal math | ◐ Weak; fails after big oil moves |
| 14 | Rack (terminal wholesale) prices | F (likely N via traders) | External: OPIS (paid) | ❌ Missing |
| 15 | Truckstop pump prices (AAA's real input) | F (N via informed traders) | External: OPIS / fuel cards / chain websites | ❌ Missing |
| 16 | Noon mystery move | N | Unknown (rack 11 AM snapshot?) | ❌ Missing |
| 17 | Night confidence boost (8–11 PM) | N | Unknown | ❌ Missing |
| 18 | OPIS time window (which hours count) | F | External, unpublished | ❌ Missing |
| 19 | OPIS weighting (stations vs volume) | F | External, unpublished | ❌ Missing |
| 20 | State → national roll-up | F | External, unpublished | ❌ Missing |
| 21 | Daily KXDIESELD rulebook (exact definition) | F | External: Kalshi CFTC filing | ❌ Not found |
| 22 | Market-maker quoting models | N | Private | ❌ Infer from order book |
| 23 | Up vs down speed (rockets & feathers) | F | Internal math + academic | ⬜ Untested (only falling prices) |
| 24 | Weekend / holiday effects | F | Internal math | ⬜ Untested |
