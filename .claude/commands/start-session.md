Run the start-of-session orientation. **Works regardless of mode** — if persona (`/agent`) is active, output adopts the YC-mentor voice and emoji style; otherwise default Claude Code voice. Underlying steps and data are identical.

## Steps (use real data only — read every file explicitly, do not assume from prior context)

1. **Read `CLAUDE.md`** with the Read tool. Do not rely on auto-injected context.
2. **Read the compounding-loop files** (the agent's persistent state — these are what make the agent measurably smarter session-to-session):
   - `knowledge/INDEX.md` — what notes exist. If missing, create with the standard header (see CLAUDE.md → "Knowledge files").
   - `knowledge/THEMES.md` — synthesized cross-source patterns. If missing, treat as "no themes yet."
   - `knowledge/TENSIONS.md` — disagreements between sources. If missing, treat as "no tensions yet."
   - `knowledge/THESIS.md` — founder's current bet. If missing, treat as "not yet defined."
3. **Check auto-memory.** Try to read `~/.claude/projects/-Users-danielstarr-Desktop-Startup-Ideation/memory/MEMORY.md`. If it doesn't exist, treat founder context as "none saved yet" — don't error.
4. **Compute live knowledge counts** by listing each subdirectory:
   ```
   ls knowledge/youtube/ | grep -c '\.md$'
   ls knowledge/reddit/ | grep -c '\.md$'
   ls knowledge/articles/ | grep -c '\.md$'
   ls knowledge/sessions/ | grep -c '\.md$'
   ```
   Use the real counts, not numbers from CLAUDE.md (they may be stale).
5. **Count themes, tensions, and tags.** From the files just read:
   - Themes = number of H2 sections under "## " in THEMES.md (excluding the "How this file works" header)
   - Active tensions = number of H3 sections under `## Active tensions`
   - Tags in use = number of H2 sections in TAGS.md
6. **Check git state.** Run `git rev-parse --git-dir 2>/dev/null`. If exit 0, also run `git log -1 --oneline`. If non-zero, mark git as "not initialized" — don't error.
7. **Reconcile.** If the live counts differ from CLAUDE.md's **Current state**, that's drift. Update CLAUDE.md's Current state in the same turn (this is a Proactive save trigger).
8. **Build the "prove it" line.** A single sentence that demonstrates working memory of prior work — the visible proof that the system is compounding. Format: `Dominant theme: {top theme from THEMES.md, or "none yet"}. Active tension: {top tension from TENSIONS.md, or "none"}. Current thesis: {from THESIS.md, or "not yet defined"}.`
9. **Every-5-sessions self-check.** If the sessions count is a multiple of 5 (5, 10, 15, …), append the self-check question to the end of the boot output (see CLAUDE.md → Proactive saves → Every-5-sessions self-check).

## Output format

```
📦 Project: Startup Ideation Partner
🧠 Mode: {Default Claude Code | YC Mentor (persona active)}

📚 Knowledge base
─────────────────
YouTube: {n}  ·  Reddit: {n}  ·  Articles: {n}  ·  Sessions: {n}
Themes: {n}  ·  Active tensions: {n}  ·  Tags in use: {n}
Latest: {most recent INDEX.md entry, or "no notes yet"}

🧠 Working memory (prove it)
────────────────────────────
{the "prove it" line built in Step 8}

👤 Founder context
─────────────────
{1-line summary from MEMORY.md, or "no saved context yet — will build it as we go"}

🔨 Last commit
──────────────
{git log output, or "no git repo (run `git init` to enable /end-session commits)"}

📋 Open items
─────────────
{🔴 Next items from CLAUDE.md → Open items, or "none — pick something or paste a source"}

✅ Ready
```

Then ask: **"What do you want to tackle first?"**

If the every-5-sessions self-check fired (Step 9), append that question after the "What do you want to tackle first?" line — a brief check-in, not a blocker.

## Voice adaptation
- **Default mode:** the format above as-is, terse, no extra emojis.
- **Persona mode:** same data, but warmer phrasing around it ("Welcome back 👋 — here's where we are…"), and the closing question in mentor voice with an A/B/C if the founder seems to need a nudge.

## CRITICAL
- Real `ls` counts. Real `git` output. Real INDEX.md content. No fabrication.
- If something doesn't exist (no MEMORY.md, no git repo, no notes), say so plainly. Don't make up state.
