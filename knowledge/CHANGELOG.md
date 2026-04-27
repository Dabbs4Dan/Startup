# System Changelog

> Every meaningful change to how the agent works — CLAUDE.md edits, new commands, new schema fields, new files, new routines. Reverse chronological.

---

## 2026-04-27 — Self-developing dimensions: PERSONA + STATE_OF_THE_AGENT + SELF_ASSESSMENT + stale-check + opposing-case + anecdote framing

**What:** Five new mechanisms responding to founder ask about (a) persona scaling automatically with corpus, (b) non-engineer founder-legibility, (c) auto stale-knowledge check, (d) verifying conversation-learning loop, (e) tracking self-critique over time.

**Files added:**
- `knowledge/PERSONA.md` — evolving voice + earned aesthetic, with three maturity tiers (🌱 Apprentice / 🌿 Developing / 🌳 Mature) that scale with note + ideation-session counts. Updates during pattern sweep + when stances earn validation.
- `knowledge/STATE_OF_THE_AGENT.md` — plain-English snapshot of what the agent knows/tracks/is uncertain about. Auto-updated at every `/end-session`. Founder reads in 2 minutes to spot drift.
- `knowledge/SELF_ASSESSMENT.md` — recurring honest critique on 8 mission-critical dimensions (sourcing diversity, anecdote framing, persona depth, founder legibility, discourse capture, knowledge freshness, opposing-case discipline, use-vs-build ratio). Trend table over time. First checkpoint seeded today.

**CLAUDE.md changes:**
- New rule: stale-knowledge auto-check at session start (180/365-day buckets, surfaced in boot output, parenthetical caveats when citing stale notes).
- New rule: persona-tier behavior scaling (counted from notes + sessions, governs how strongly to push earned stances).
- New rule: anecdote-vs-evidence framing discipline ("tends to" / "in this corpus" defaults; flag sourcing monoculture explicitly).
- New rule: opposing-case discipline (every recommendation includes "Counter-case:" or "I don't see a strong counter — here's why:").
- New rule: founder-legibility update at every `/end-session` refreshes STATE_OF_THE_AGENT.md.
- New rule: recurring self-assessment cadence (every 5 sessions or major milestone or on request).
- Wake-up routine: now reads PERSONA.md + SELF_ASSESSMENT.md.
- Knowledge files section: documented PERSONA, STATE_OF_THE_AGENT, SELF_ASSESSMENT.

**Commands changed:**
- `/start-session`: stale-check, persona tier, lowest-3 self-critique flags surfaced in boot output. Self-assessment cadence prompt fires at 5/10/15/...
- `/end-session`: STEP 2.4 added (refresh STATE_OF_THE_AGENT.md); STEP 2.5 expanded (PERSONA.md updates + SELF_ASSESSMENT checkpoint at 5-session intervals).
- agent skill: wake-up reads PERSONA + SELF_ASSESSMENT.

**Honest answer to founder's "did I add learning from our conversations":** Yes for capture (pattern sweep, auto-memory, IDEATION_LOG, PERSONA earned-aesthetic updates). Verification: still aspirational — none of these have actually fired in production yet. Auto-memory remains empty. The proof comes from running a real ideation session and watching the loops fire end-to-end.

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

## 2026-04-27 — Phase 2: Techstars Toolkit ingestion (13 notes covering all 20 modules)

**What:** Full ingestion of the Techstars Founders Toolkit. 20 modules fetched in parallel; triaged by depth into 13 notes — 12 standalone + 1 combined "shorter frameworks" note for the thinner pages.

**Notes added (all under `knowledge/articles/`):**
- techstars-lean-canvas
- techstars-customer-development (Empathy + JTBD)
- techstars-category-design (combined 2 modules)
- techstars-position-your-product
- techstars-brand-your-business
- techstars-master-your-pitch
- techstars-kpis-and-okrs (combined 3 modules: KPIs + Make Progress + Check Progress)
- techstars-cofounder-relationships
- techstars-engage-with-mentors
- techstars-investor-pipeline
- techstars-eq-for-entrepreneurs
- techstars-diverse-workforce
- techstars-shorter-frameworks (combined 5 thinner modules: Elevator Pitch + Get More Done + 21 Ways + W3 + Mental Health)

**THEMES updates:**
- "Origins matter" — extended with Techstars Customer Dev + Lean Canvas (now 4 sources, cross-publisher)
- NEW: "Founder must personally do the conviction work" (Diana + Altman + Techstars Customer Dev + Techstars EQ — cross-publisher)
- NEW: "Outcome measurement (not motion) is the discipline" (Diana + Lightcone + Techstars KPIs + Techstars Position — cross-publisher)
- Total themes: 4 → 6

**TENSIONS updates:**
- NEW: "Speed-first vs deliberate methodology (YC vs Techstars accelerator culture)" — first cross-publisher tension. Reconciliation: both right at different stages; Techstars-style for pre-PMF discovery, YC-style velocity for post-PMF execution.
- Total active tensions: 1 → 2

**TAGS updates:**
- Techstars publisher section added with 13 notes
- Existing publisher entries updated for sourcing-diversity tracker
- 14 new content tags introduced from Techstars: lean-canvas, customer-development, category-design, positioning, branding, cofounders, mentorship, kpis, goals, pitching, mental-health, diversity, fundraising, sales, retention, growth, community
- Tags in use: 13 → 31

**Sourcing diversity moved from 🔴 1/10 (YC monoculture) to 🟡 ~3/10 (still accelerator-dominant: Techstars 81% + YC 19%, no indie/bootstrapper/failure-archive yet).** Major step but not yet diverse — see SELF_ASSESSMENT Checkpoint #2.

---

## 2026-04-27 — Phase 1: publisher-tag scheme

Schema: publisher field now required in frontmatter; first tag in tags array mirrors it (yc / techstars / reddit / internal / etc). TAGS.md restructured to surface publisher distribution at the top. Backfilled 3 existing YC notes + the architecture session.

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
