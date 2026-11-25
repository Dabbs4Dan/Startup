"""Shared paths + time helpers."""
import datetime
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[2]          # repo root (kalshi-twins branch)
DB = ROOT / "data" / "kalshi_twins.db"
LIVE = ROOT / "data" / "live"
CATALOG = ROOT / "data" / "nautilus_catalog"                 # gitignored, rebuilt on demand
REPORTS = ROOT / "nautilus" / "reports"


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def iso_to_ns(s):
    """'2026-11-25T13:00:00Z' or '2026-11-25T13:00:00.123456Z' -> unix nanoseconds."""
    if not s:
        return 0
    s = s.strip().replace("Z", "+00:00")
    dt = datetime.datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def sec_to_ns(x):
    return int(x) * 1_000_000_000
