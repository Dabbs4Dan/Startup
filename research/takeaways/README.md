# Takeaways — per-chat snapshots + rolling master

Two layers, same columns in GitHub and in the Build Board sheet (Drive → Kalshi Diesel → "Kalshi Diesel – Build Board",
tabs **Takeaways – master** and **Takeaways – by chat**).

| File | What it is | Rule |
|---|---|---|
| `by_chat.csv` | Frozen copy of each chat's closing takeaway table. IDs `C<chat>-<nn>`. | Append new chats at the bottom. On old rows only change `status` (Current / Superseded / Open) and `superseded_by`. |
| `master.csv` | One current list across all chats. IDs `M<nn>`. `source_chats` says where each item came from. | Edit freely; newest evidence wins. When a by-chat row is superseded, update the master row too. |
| `build_takeaways.py` | Source of truth that writes both CSVs. | Edit the lists in it, run `python3 research/takeaways/build_takeaways.py`, then mirror to the two sheet tabs. |

How a new session should use this: read `master.csv` for what is true now; read `by_chat.csv` to see what a given chat concluded and what later replaced it.

Chats so far: 1 Setup & core research · 2 OPIS & 60 day excel · 3 Initial excel · 4 Nautilus Trader · 5 Sample models & backtest.
