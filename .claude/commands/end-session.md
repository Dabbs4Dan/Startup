Run the end-of-session checklist. **Works regardless of mode.** Output adopts persona voice if `/agent` is active.

## STEP 1 — Update CLAUDE.md (always required)

Read `CLAUDE.md` first, then edit:

**Current state section:**
- Update per-type counts using real `ls knowledge/*/` output (not stale numbers).
- Update "Latest extraction" if a new note was added this session — pull from `knowledge/INDEX.md` top entry.
- Update "Last ideation session" line if any ideation happened (date + 1-line topic).
- Update "Active threads" — what's in flight; remove threads that closed this session.
- Add a milestone line if something structurally meaningful shipped (new tool, new schema field, new command).

**Open items section:**
- Mark completed items as ✅ Done and remove (or move to a "Recently completed" sub-list if the founder wants history).
- Add new 🔴 Next items raised this session.
- Promote 🗺️ Future items to 🔴 Next if the founder committed to them.

**Other sections** (Architecture, Tags, Schema): only edit if a structural change happened this session.

## STEP 2 — Save unsaved session insights

If meaningful ideation happened this session and no file was written to `knowledge/sessions/`:
- Create `knowledge/sessions/{YYYY-MM-DD}_{topic}.md` using the standard extraction schema (with `source_type: session` and `url: n/a`).
- Append the entry to `knowledge/INDEX.md`.

If a knowledge extraction was started but not finalized (e.g., the founder paused mid-fetch), ask whether to finalize it or skip — don't silently drop it.

## STEP 3 — Commit (if git repo)

Run `git rev-parse --git-dir 2>/dev/null`:

**If git initialized:**
1. Run `git status` to confirm what's changing.
2. Stage explicit files only — never `git add -A`. Always include (when modified or new):
   - `CLAUDE.md`
   - `knowledge/INDEX.md`
   - `knowledge/THEMES.md`
   - `knowledge/TENSIONS.md`
   - `knowledge/TAGS.md`
   - `knowledge/THESIS.md`
   - `knowledge/CHANGELOG.md`
   - `knowledge/SUGGESTIONS.md`
   - Any new/modified files under `knowledge/youtube/`, `/reddit/`, `/articles/`, `/sessions/`
   - Any new/modified files under `.claude/commands/` or `.claude/skills/`
3. Commit with a short plain-English message describing what shipped this session (e.g. `"Add Diana Hu extraction; update themes + tags"`).
4. **Auto-push to origin/main.** Run `git push`. The remote is `git@github.com:Dabbs4Dan/Startup.git` (SSH, no prompts). If push fails for any reason (network, auth, conflict), surface the error in the summary — don't retry blindly and don't force-push.

**If no git:**
- Skip silently. Note in the summary that source control isn't set up.

## STEP 4 — Print summary

```
✅ CLAUDE.md updated: {1-line list of what changed — counts? new feature docs? open items?}
✅ Session insights saved: {filename, or "n/a — no ideation this session"}
✅ Committed: {commit hash and message, or "no git repo — knowledge saved locally to disk"}
📋 Open items remaining: {🔴 Next items, or "none"}
👋 Safe to close this window
```

If in persona mode, soften the tone: "Great session 👋 — here's where we landed…" but keep all 5 lines and real data.

## CRITICAL
- Read CLAUDE.md before editing it. Use Edit, not Write — preserve everything you didn't intend to change.
- Real `ls` counts. Real INDEX.md state. Real git output.
- Never push to a remote without an explicit user instruction this session.
- Never `git add -A`. Stage explicit files only.
