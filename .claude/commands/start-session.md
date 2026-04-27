Run the start-of-session orientation. **Works regardless of mode** — if persona (`/agent`) is active, output adopts the YC-mentor voice and emoji style; otherwise default Claude Code voice. Underlying steps and data are identical.

## Steps (use real data only — read every file explicitly, do not assume from prior context)

1. **Read `CLAUDE.md`** with the Read tool. Do not rely on auto-injected context.
2. **Read `knowledge/INDEX.md`.** If it doesn't exist, create it with the standard header (see CLAUDE.md → "The index file").
3. **Check auto-memory.** Try to read `~/.claude/projects/-Users-danielstarr-Desktop-Startup-Ideation/memory/MEMORY.md`. If it doesn't exist, treat founder context as "none saved yet" — don't error.
4. **Compute live knowledge counts** by listing each subdirectory:
   ```
   ls knowledge/youtube/ | grep -c '\.md$'
   ls knowledge/reddit/ | grep -c '\.md$'
   ls knowledge/articles/ | grep -c '\.md$'
   ls knowledge/sessions/ | grep -c '\.md$'
   ```
   Use the real counts, not numbers from CLAUDE.md (they may be stale).
5. **Check git state.** Run `git rev-parse --git-dir 2>/dev/null`. If exit 0, also run `git log -1 --oneline`. If non-zero, mark git as "not initialized" — don't error.
6. **Reconcile.** If the live counts differ from CLAUDE.md's **Current state**, that's drift. Update CLAUDE.md's Current state in the same turn (this is a Proactive save trigger).

## Output format

```
📦 Project: Startup Ideation Partner
🧠 Mode: {Default Claude Code | YC Mentor (persona active)}

📚 Knowledge base
─────────────────
YouTube: {n}  ·  Reddit: {n}  ·  Articles: {n}  ·  Sessions: {n}
Latest: {most recent INDEX.md entry, or "no notes yet"}

🧠 Founder context
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

## Voice adaptation
- **Default mode:** the format above as-is, terse, no extra emojis.
- **Persona mode:** same data, but warmer phrasing around it ("Welcome back 👋 — here's where we are…"), and the closing question in mentor voice with an A/B/C if the founder seems to need a nudge.

## CRITICAL
- Real `ls` counts. Real `git` output. Real INDEX.md content. No fabrication.
- If something doesn't exist (no MEMORY.md, no git repo, no notes), say so plainly. Don't make up state.
