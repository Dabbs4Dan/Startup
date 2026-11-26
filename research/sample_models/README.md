# Sample models — outside Kalshi bots we study

Outside code we keep next to our own research, to learn from and borrow ideas.
**Only MIT/open-licensed code is copied into this (public) repo.** Unlicensed bots are linked and summarized, never copied.

| # | Model | License | In repo? | Why it matters to us |
|---|---|---|---|---|
| 1 | [ryanfrigo/kalshi-ai-trading-bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot) | MIT | ✅ full copy in `kalshi-ai-trading-bot/` (commit `5d7b70a`, 2026-11-08) | Has its **own AAA diesel/gas model** (`scripts/aaa_*.py`, `docs/AAA.md`) + an honest edge-measurement harness (`src/agent/edge.py`). Analysis: `kalshi-ai-trading-bot_ANALYSIS.md` |
| 2 | [suislanchez/polymarket-kalshi-weather-bot](https://github.com/suislanchez/polymarket-kalshi-weather-bot) | none | ❌ link only (copy in Dan's Google Drive "Sample Kalshi Models") | Clean example of fair value → edge rule (8%) → fractional Kelly → Brier report card |
| 3 | [mmoore07129/mlb-kalshi-bot](https://github.com/mmoore07129/mlb-kalshi-bot) | none | ❌ link only (copy in Drive) | Live-bot plumbing: net-of-fee EV, rising threshold when sources disagree, decision log with skip reasons, closing-line value, order watcher, depth cap |

Notes for the copied repo:
- Its `.claude/` and `.github/` folders were renamed `_dot_claude/` and `_dot_github/` so they don't load as live skills/workflows here.
- Nothing in it runs from our jobs. Treat it as read-only reference; if we reuse a function, copy it into `tools/` with a comment crediting the source and keep the MIT notice.
