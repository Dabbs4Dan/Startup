"""Strategy registry.

Every strategy = one file here + one row in the Google Sheet "Strategies" tab (same ID, e.g. S01).
Nothing trades yet: only the plumbing check (S00) is registered. To add a strategy:
  1. copy _template.py -> s01_<name>.py, fill in on_quote / on_trade
  2. add it to REGISTRY below with its sheet ID
  3. python3 nautilus/run_backtest.py --strategy S01
The same class later runs on the Kalshi demo via nautilus/live_demo_node.py (no code changes).
"""
from .replay_check import ReplayCheck

REGISTRY = {
    "S00": ReplayCheck,      # plumbing check: replays data, places NO orders
}
