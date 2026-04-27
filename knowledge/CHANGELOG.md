# System Changelog

> Every meaningful change to how the agent works — CLAUDE.md edits, new commands, new schema fields, new files, new routines. Reverse chronological.

---

## 2026-04-27 — Dedupe + IDEATION_LOG + end-of-session pattern sweep

**What:** Three structural additions in response to founder ask about (a) flagging duplicate sources, (b) capturing how agent-mode discussion weights into learning.

**Files added:**
- `knowledge/IDEATION_LOG.md` — running log of in-flight ideation threads (the journey, not the destination). Distinct from THESIS (commitments) and `sessions/` (post-decision capture).

**CLAUDE.md changes:**
- Job 1: new Step 2 — dedupe check before fetch (extract YouTube video ID / Reddit submission ID / article host+path, grep across `knowledge/`, surface existing note + A/B/C options if found)
- Job 2: step 7 added — update IDEATION_LOG.md the same turn when new angles surface
- Wake-up routine: now also reads IDEATION_LOG.md
- Knowledge files section: documented IDEATION_LOG.md
- Proactive saves: new "End-of-session pattern sweep" rule — mandatory after ideation. Captures how the founder thinks (not just what they decide), saves 0–3 salient observations to auto-memory.

**Commands changed:**
- `/start-session`: now reads + reports live thread count
- `/end-session`: new STEP 2.5 — pattern sweep + IDEATION_LOG promotion
- agent skill: wake-up reads IDEATION_LOG.md

---

## 2026-04-27 — Ingest: Sam Altman on startup ideas + Great Wave (test of new system)

**What:** Added [Sam Altman — Startup Idea + Great Wave](knowledge/youtube/sam-altman-startup-idea-and-the-great-wave.md). 3:21 curated clip.

**Cascading updates done in same turn (per new auto-write policy):**
- INDEX.md — top entry
- TAGS.md — added under `founder-mindset` (now 3), `pmf` (now 2), `ideation` (new section, 1)
- THEMES.md — added new theme **"Origins matter — real problems, not crowded markets"** (Altman + Lightcone). Total themes now 4.
- TENSIONS.md — no new tension (Altman doesn't contradict existing notes).
- CLAUDE.md — bumped YouTube count, latest extraction, theme/tag counts.
- THESIS.md — no change (founder still pre-ideation).

**Test result:** First end-to-end run of the auto-write + auto-push routine. Everything cascaded in the same turn. The new theme bridge between Altman and Lightcone happened automatically because Job 1 step 5 now requires it.

---

## 2026-04-27 — Auto-push + auto-refresh policy (durable authorization)

**Founder authorized:** auto-commit + auto-push on every assistant turn that touches tracked files. No more waiting for `/end-session`. No more user having to remember to push.

**Rule (now in CLAUDE.md → Proactive saves):**
- Any turn that creates/modifies CLAUDE.md, knowledge files, commands, or skills → commit + push to remote main before yielding
- Stage explicit files only, never `git add -A`
- Push via `git push origin HEAD:main` (fast-forward from worktree branch)
- Surface push failures clearly, no blind retry, no `--force-push`

**Plus auto-refresh:** when re-using a meta-file edited earlier in a session, re-read from disk — don't trust in-memory state.

**Why:** keeping work safe is the system's job, not the founder's. The founder ingests and thinks; the agent persists.

---

## 2026-04-27 — Architecture rev: agent compounding loop

**Context:** Founder asked whether file-based architecture would actually make the agent measurably smarter session-to-session, or if we should fine-tune a model instead. Decision: stay file-based, no fine-tuning. Architecture decision documented in [knowledge/sessions/2026-04-27_agent-architecture.md](knowledge/sessions/2026-04-27_agent-architecture.md).

**Files added:**
- `knowledge/THEMES.md` — cross-source pattern synthesis (seeded with 3 themes from Diana + Lightcone)
- `knowledge/TENSIONS.md` — disagreements between sources (seeded with 1 active tension)
- `knowledge/TAGS.md` — tag-to-notes index (auto-populated from existing notes)
- `knowledge/THESIS.md` — founder's living thesis (scaffold, empty until founder commits)
- `knowledge/CHANGELOG.md` — this file
- `knowledge/SUGGESTIONS.md` — pending system upgrades

**CLAUDE.md changes:**
- Job 2 (Ideation Partner) routine: now reads THEMES + TENSIONS + THESIS before responding, not just INDEX
- Job 1 (Knowledge Builder) routine: now updates TAGS + THEMES + TENSIONS in the same turn as the new note
- Wake-up routine documented (which files load at session start)
- "Save the moment it crystallizes" rule tightened (was vague)
- Every-5-sessions self-check rule added
- Knowledge architecture sub-section added to Current state

**Commands changed:**
- `/start-session` — now surfaces theme/tension counts and a "prove it" demonstration line
- `/end-session` — now also stages new meta files (TAGS, THEMES, TENSIONS, THESIS, CHANGELOG, SUGGESTIONS) on commit

**The test (founder will run this):** Open a fresh session a month from now. Type `/agent`. Ask a synthesis question that requires multiple sources. If answered in seconds with named citations and surfaced disagreements — system worked. If generic — fix the broken leg.
