Run the start-of-session orientation. **Works regardless of mode** — if persona (`/agent`) is active, output adopts the YC-mentor voice and emoji style; otherwise default Claude Code voice. Underlying steps and data are identical.

## Steps (use real data only — read every file explicitly, do not assume from prior context)

1. **Read `CLAUDE.md`** with the Read tool. Do not rely on auto-injected context.
2. **Read the compounding-loop files** (the agent's persistent state — these are what make the agent measurably smarter session-to-session):
   - `knowledge/INDEX.md` — what notes exist. If missing, create with the standard header (see CLAUDE.md → "Knowledge files").
   - `knowledge/THEMES.md` — synthesized cross-source patterns. If missing, treat as "no themes yet."
   - `knowledge/TENSIONS.md` — disagreements between sources. If missing, treat as "no tensions yet."
   - `knowledge/THESIS.md` — founder's current bet. If missing, treat as "not yet defined."
   - `knowledge/IDEATION_LOG.md` — live exploration threads. If missing, treat as "no live threads."
   - `knowledge/PERSONA.md` — evolving voice + earned aesthetic + maturity tier. If missing, treat as "🌱 Apprentice tier, default archetype only."
   - `knowledge/SELF_ASSESSMENT.md` — known weaknesses (so they aren't silently repeated). If missing, treat as "no critique baseline yet."
3. **Check auto-memory.** Try to read `~/.claude/projects/-Users-danielstarr-Desktop-Startup-Ideation/memory/MEMORY.md`. If it doesn't exist, treat founder context as "none saved yet" — don't error.
4. **Compute live knowledge counts** by listing each subdirectory:
   ```
   ls knowledge/youtube/ | grep -c '\.md$'
   ls knowledge/reddit/ | grep -c '\.md$'
   ls knowledge/articles/ | grep -c '\.md$'
   ls knowledge/sessions/ | grep -c '\.md$'
   ```
   Use the real counts, not numbers from CLAUDE.md (they may be stale).
5. **Count themes, tensions, tags, and live threads.** From the files just read:
   - Themes = number of H2 sections under "## " in THEMES.md (excluding the "How this file works" header)
   - Active tensions = number of H3 sections under `## Active tensions`
   - Tags in use = number of H2 sections in TAGS.md
   - Live threads = number of H2 sections under `## Active threads` in IDEATION_LOG.md
6. **Inbox scan.** Run `ls inbox/` and count files (excluding `README.md` and the `processed/` subdir). If any unprocessed files are present, surface them in the boot output as `📥 Inbox: N file(s) waiting to ingest — {filenames}`. The founder may have dropped something between sessions.

7. **Stale-knowledge auto-check.** For every note in `knowledge/youtube/`, `/reddit/`, `/articles/`, `/sessions/`, read its `date_extracted` frontmatter and bucket:
   - `< 180 days` → 🟢 fresh (no flag)
   - `180–365 days` → 🟡 freshness check
   - `> 365 days` → 🔴 likely stale (also list filenames)

   Compute counts per bucket. Surface in boot output.
8. **Determine persona maturity tier** from PERSONA.md's counters + the live counts. Surface in boot output: `🌱 Apprentice` / `🌿 Developing` / `🌳 Mature`.
9. **Check git state.** Run `git rev-parse --git-dir 2>/dev/null`. If exit 0, also run `git log -1 --oneline`. If non-zero, mark git as "not initialized" — don't error.
10. **Reconcile.** If the live counts differ from CLAUDE.md's **Current state**, that's drift. Update CLAUDE.md's Current state in the same turn (this is a Proactive save trigger).
11. **Build the "prove it" line.** A single sentence that demonstrates working memory of prior work — the visible proof that the system is compounding. Format: `Dominant theme: {top theme from THEMES.md, or "none yet"}. Active tension: {top tension from TENSIONS.md, or "none"}. Current thesis: {from THESIS.md, or "not yet defined"}. Live threads: {count from IDEATION_LOG.md, or "none"}. Persona tier: {tier emoji + name}.`
12. **Surface latest 3 self-critique flags.** From SELF_ASSESSMENT.md most recent checkpoint, surface the 3 lowest-scoring (or most concerning) dimensions in boot output as `⚠️ Known weaknesses` so they're top-of-mind for the session.
13. **Self-assessment cadence check.** If sessions count is a multiple of 5 (5, 10, 15, …) AND no checkpoint has been added today, surface a recommendation in boot output: *"📊 Time for a SELF_ASSESSMENT.md checkpoint — type `/check-session` or just ask."*
14. **Every-5-sessions self-check** (founder pruning question). Same trigger as above; append the question to the end of the boot output.

## Output format

```
📦 Project: Startup Ideation Partner
🧠 Mode: {Default Claude Code | YC Mentor (persona active)}

📚 Knowledge base
─────────────────
YouTube: {n}  ·  Reddit: {n}  ·  Articles: {n}  ·  Sessions: {n}
Themes: {n}  ·  Active tensions: {n}  ·  Tags in use: {n}  ·  Live threads: {n}
Freshness: 🟢 {n} fresh  ·  🟡 {n} check  ·  🔴 {n} likely stale {list filenames if any 🔴}
Latest: {most recent INDEX.md entry, or "no notes yet"}

📥 Inbox
────────
{if any unprocessed files: "N file(s) waiting to ingest — {filenames}"; else: "empty"}

🧠 Working memory (prove it)
────────────────────────────
{the "prove it" line built in Step 11}

⚠️ Known weaknesses (from latest self-assessment)
─────────────────────────────────────────────────
{top 3 lowest-scoring or most-concerning dimensions from SELF_ASSESSMENT.md, with score + 1-line note}

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
