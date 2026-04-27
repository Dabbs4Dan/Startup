# Pending System Suggestions

> Things the agent has proposed but the founder hasn't accepted or rejected yet. Survives across sessions so good ideas don't evaporate.

**Last updated:** 2026-04-27

---

## How this file works

- **Open** = proposed but undecided. Agent can re-surface these when relevant.
- **Recently accepted** = greenlit and built (or in progress). Move to changelog when shipped.
- **Rejected** = explicitly killed. Don't re-propose without new evidence.
- **Update trigger:** any time the agent suggests a system change AND the founder doesn't immediately accept/reject — log here.

---

## Open

### Agent-sourced content workflow (founder-authorized 2026-04-27)
**What:** Founder authorized the agent to proactively pull new sources between/within sessions when gaps are noticed. Needs a controlled-merge workflow:
- Agent fetches a candidate source → creates a note with status `pending-approval` (and tag `agent-sourced`)
- Notifies founder: *"I sourced X because Y — review?"*
- Founder approves → status flips to `approved`, `agent-sourced` tag removed, note merges into the regular corpus
- Founder rejects → note moves to `knowledge/rejected/` with a 1-line "why killed" so we don't re-propose
- Need: status frontmatter field; a `pending-approval` section in INDEX or its own staging file; the approval routine

**Why deferred:** Don't build during the build-fatigue moment. Construct after we've actually ideated — when the founder has a real reason to want a specific gap filled and the workflow's value is concrete rather than hypothetical.

### Stale-check routine
**Proposed:** 2026-04-27 (during architecture rev)
**What:** When citing a note >12 months old in an ideation answer, flag the age and ask whether to re-extract or supplement. Model/market context shifts fast in AI; stale claims can mislead.
**Why deferred:** Not built today because corpus is too young to test against. Revisit when first note crosses 12 months (April 2027) or when founder reports a stale citation.

### Persona-tier rule reconciliation
**Proposed:** 2026-04-27 (in pre-end-session audit)
**What:** PERSONA.md was promoted to 🌿 Developing tier today, but the rule says *"5-15 notes AND 2-5 ideation sessions."* We have 16 notes but only 1 session. Either the rule is wrong (sessions threshold too high for early phase) or the tier is wrong (should still be Apprentice). Reconcile next session — likely just adjust the rule to "5+ notes OR 2+ ideation sessions" since session count grows slower than note count for a founder still in heavy ingestion.

### Meta-file integrity check at session start
**Proposed:** 2026-04-27 (in pre-end-session audit)
**What:** No automated check that THEMES/TENSIONS/PERSONA/etc. haven't been accidentally truncated or corrupted. `/start-session` could verify "expected sections" exist (e.g. THEMES.md should have `## How this file works` + at least one theme H2). Cheap to add; would catch silent corruption.
**Why deferred:** Hasn't happened in practice. Add reactively if it ever does.

---

## Recently accepted
*(none — track here when items move from Open to Done)*

## Rejected
*(none yet — when something gets killed, log it with a 1-line reason so we don't re-propose)*
