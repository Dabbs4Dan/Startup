# Risk / threshold formula (2026-11-25)

Per bet: stake s = B/n; cost per $1 contract c = price + 0.07·price·(1−price).
- Win profit = s·(1−c)/c · Loss = −s
- **P&L(L losses) = (B/n)·[(n−L)·(1−c)/c − L]**
- **Max losses before negative: L* = n·(1−c)**
- **Win rate needed = c**
- **Wins needed per loss = c/(1−c)**
- Risk ceiling = B (all bets lose). Realistic risk = chance of finishing negative = P(Binomial(n, 1−q) > L*), q = true win rate.

## $400 over 30 bets, real 10 AM favorite prices (avg 74.5¢, cost 75.8¢ incl fee, historical win 79%)
$13.33/bet · win +$4.26 · loss −$13.33 · break-even at 7.3 losses.
| Losses | P&L |
|---|---|
| 0 | +$127.75 |
| 1 | +$110.16 |
| 2 | +$92.57 |
| 3 | +$74.98 |
| 5 | +$39.80 |
| 7 | +$4.61 |
| 8 | −$12.98 |
| 10 | −$48.16 |
Wins needed to erase: 1 loss → 4 wins · 2 → 7 · 3 → 10 · 5 → 16.
Chance negative at 79% win rate (binomial): 27.7%. Monte Carlo (10k × 30 real bets): median +$21, 10th pct −$33, 90th +$69, worst −$151, best +$151, negative 29.9%.

Script: `tools/risk_calc.py`.
