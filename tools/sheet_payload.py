#!/usr/bin/env python3
"""Build the exact cell blocks for the Google Sheets "Engine Room" tabs (mobile-first: no IMPORTDATA, no
"Allow access" tap). A Claude session (or the daily scheduled task) runs this and writes each block with the
Sheets connector: update_values(spreadsheetId, range, values).

  python3 tools/sheet_payload.py            -> prints JSON: [{"spreadsheetId", "range", "values"}, ...]
"""
import csv, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOKS = {
    "diesel": ("19Mae6DB3CaY4ydLvy7R_JtGYxPv7KGYfQf0JpaD5ggw", ROOT / "data" / "exports"),
    "gas": ("1aeZ0HNj0iilqitcRavdKVoWyeLOOE9kkk5g2bXCykO4", ROOT / "data" / "gas" / "exports"),
}
SCORE_ROWS, POINT_ROWS = 12, 60          # fixed block sizes so old rows get blanked
WIDTH = 10


def block(path, rows, width=WIDTH):
    data = []
    if path.exists():
        data = [r[:width] for r in csv.reader(path.open())]
    data = data[:rows] + [[""] * width for _ in range(max(0, rows - len(data)))]
    return [r + [""] * (width - len(r)) for r in data]


def main():
    out = []
    for name, (sid, exp) in BOOKS.items():
        last = ""
        sc = exp / "engine_room_scorecard.csv"
        if sc.exists():
            import datetime
            last = datetime.datetime.fromtimestamp(sc.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        out.append({"spreadsheetId": sid, "range": "Engine Room!A13:J13",
                    "values": [[f"🔄 LIVE SCORECARD ({name}) — written automatically by Claude after each data run. Source: "
                                f"data/{'gas/' if name == 'gas' else ''}exports/engine_room_scorecard.csv", "", "", "", "", "", "",
                                "", "Updated:", last or "waiting for first run"]]})
        out.append({"spreadsheetId": sid, "range": f"Engine Room!A14:J{13 + SCORE_ROWS}", "values": block(sc, SCORE_ROWS)})
        out.append({"spreadsheetId": sid, "range": f"Engine Room!A{14 + SCORE_ROWS}:J{14 + SCORE_ROWS}",
                    "values": [["🔄 L2 POINTS — our state blend vs AAA's real national number, newest first", "", "", "", "", "", "", "", "", ""]]})
        out.append({"spreadsheetId": sid, "range": f"Engine Room!A{15 + SCORE_ROWS}:J{14 + SCORE_ROWS + POINT_ROWS}",
                    "values": block(exp / "engine_room_l2_points.csv", POINT_ROWS)})
    # Warehouse tab (diesel workbook): catalog + feed health, written from data/*.csv (tools/warehouse.py catalog)
    import datetime
    wh_sid = BOOKS["diesel"][0]
    cat, fh = ROOT / "data" / "warehouse_catalog.csv", ROOT / "data" / "feed_health.csv"
    stamp = datetime.datetime.fromtimestamp(cat.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if cat.exists() else "waiting"
    out.append({"spreadsheetId": wh_sid, "range": "Warehouse!A3:H3", "values": [[f"Updated: {stamp} (written by Claude after each warehouse run)", "", "", "", "", "", "", ""]]})
    out.append({"spreadsheetId": wh_sid, "range": "Warehouse!A4:H53", "values": block(cat, 50, 8)})
    out.append({"spreadsheetId": wh_sid, "range": "Warehouse!A55:E55", "values": [["FEED HEALTH: is every recorder still on point? (OK = on time; live feeds save to GitHub hourly, so up to ~75 min old is normal; STALE = late)", "", "", "", ""]]})
    out.append({"spreadsheetId": wh_sid, "range": "Warehouse!A56:E70", "values": block(fh, 15, 5)})
    print(json.dumps(out))


if __name__ == "__main__":
    main()
