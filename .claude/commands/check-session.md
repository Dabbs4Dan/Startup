Assess session health and give a plain-English status. **Works regardless of mode.** Output adopts persona voice if `/agent` is active, otherwise default voice. Data is identical.

## Steps

1. **Estimate exchanges.** Count roughly how many user-assistant back-and-forth turns have happened in this session. Rough is fine — "approximately 12" is the right granularity.
2. **Check uncommitted changes.**
   - Run `git rev-parse --git-dir 2>/dev/null` to detect git.
   - If git: run `git status --short` and count modified/untracked entries (excluding `.DS_Store`).
   - If no git: report "n/a — no git repo".
3. **Check unsaved work.** Look for:
   - Active TodoWrite items not yet completed.
   - Knowledge extraction discussed this session but no file written to `knowledge/`.
   - Ideation decisions made but no `knowledge/sessions/` file saved.
   - **Current state** in CLAUDE.md drifted from real counts (use `ls knowledge/*/` to verify).
4. **Pick the recommendation** based on rough exchange count:
   - **🟢 under 15** — keep going
   - **🟡 15–25** — type `/compact` to compress history
   - **🔴 25+** — run `/end-session` then open a fresh window

## Output format

```
🧠 Session Health Check
─────────────────────
💬 Exchanges this session: ~{count}
💾 Uncommitted changes: {Yes — N files | No | n/a (no git)}
📋 Unfinished tasks: {bulleted list, or "none"}
📁 Files needing save: {list of unsaved insights/extractions, or "none"}

Recommendation: {🟢 / 🟡 / 🔴 line per rules above}
```

If "Files needing save" is non-empty, **also recommend the founder save now** before crossing thresholds. That's a Proactive saves trigger — don't just report it, act on it if they say go.

## CRITICAL
- Real exchange count (rough), real git status, real file scan. No fabrication.
- If the founder is mid-thought, don't interrupt with this check unless they typed `/check-session`. Slash command only.
