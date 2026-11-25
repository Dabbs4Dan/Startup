"""Tap-test Daily Bread at iPhone size. Usage: python3 test/phone-test.py [dist-web dir] [screenshot dir]"""
import sys, threading, http.server, functools, os
from playwright.sync_api import sync_playwright

dist = sys.argv[1] if len(sys.argv) > 1 else "dist-web"
out = sys.argv[2] if len(sys.argv) > 2 else "test/shots"
os.makedirs(out, exist_ok=True)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=dist)
handler.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

errors, results = [], []
def check(name, ok):
    results.append((name, ok)); print(("PASS " if ok else "FAIL ") + name)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(**p.devices["iPhone 15 Pro"])
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.goto("http://127.0.0.1:8765/"); pg.wait_for_timeout(1500)
    pg.screenshot(path=f"{out}/1-home.png")
    check("verse shows", pg.get_by_text("Verse of the day").is_visible())
    check("empty state shows", pg.get_by_text("A fresh page").is_visible())

    pg.get_by_label("Add a note").click(); pg.wait_for_timeout(700)
    box = pg.get_by_placeholder("What's on your heart today?")
    check("note box opens with keyboard focus", box.evaluate("e => document.activeElement === e"))
    box.type("Pitch Toast lunch-and-learn follow up\nRead Proverbs 3 tonight")
    pg.get_by_text("💡 Guide  ▾").click(); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{out}/2-label-menu.png")
    pg.get_by_text("💲 Business", exact=True).last.click(); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{out}/3-writing.png")
    pg.get_by_text("Save", exact=True).click(); pg.wait_for_timeout(700)
    check("note saved with Business label", pg.get_by_text("Pitch Toast", exact=False).is_visible() and pg.get_by_text("💲 Business").first.is_visible())

    pg.get_by_label("Add a note").click(); pg.wait_for_timeout(500)
    pg.get_by_placeholder("What's on your heart today?").type("Sketch the cymatic table")
    pg.get_by_text("💡 Guide  ▾").click(); pg.get_by_text("🌈 Art", exact=True).last.click()
    pg.get_by_text("Save", exact=True).click(); pg.wait_for_timeout(600)
    pg.screenshot(path=f"{out}/4-two-notes.png")

    pg.get_by_label("Mark done").first.click(); pg.wait_for_timeout(400)
    check("check-off moves note to Done", pg.get_by_text("Done ✔︎", exact=False).is_visible())

    pg.reload(); pg.wait_for_timeout(1500)
    check("notes survive app restart", pg.get_by_text("Pitch Toast", exact=False).count() + pg.get_by_text("Sketch the cymatic", exact=False).count() >= 1)
    pg.get_by_text("🌈 Art").first.click(); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{out}/5-filter-art.png")

    ctx2 = b.new_context(**p.devices["iPhone 15 Pro"], color_scheme="dark")
    pg2 = ctx2.new_page(); pg2.goto("http://127.0.0.1:8765/"); pg2.wait_for_timeout(1500)
    pg2.screenshot(path=f"{out}/6-dark.png")
    b.close()

check("no app errors", not errors)
for e in errors[:10]: print("  ERROR:", e[:300])
print(f"\n{sum(ok for _, ok in results)}/{len(results)} passed")
srv.shutdown()
sys.exit(0 if all(ok for _, ok in results) else 1)
