# Self-Assessment Log — Recurring Honest Critique

> The agent scores itself on mission-critical dimensions at every 5-session checkpoint or major milestone. Each entry adds a row to the trend table. Over time you can see whether biases are improving, plateauing, or worsening — and what interventions actually moved the needle.
>
> **The agent reads this at every session start** so it doesn't repeat known weaknesses without acknowledgment.

---

## Dimensions tracked

| Dimension | Why it matters |
|---|---|
| **Sourcing diversity** | Monoculture (e.g. all YC) → narrowed worldview, founder gets one-flavor advice |
| **Anecdote-vs-evidence framing** | Curated testimony from winners isn't data; advice should carry the asterisk |
| **Persona depth & voice** | Generic archetype doesn't earn trust; without taste, advice feels interchangeable |
| **Founder legibility** | Non-tech founder must be able to spot drift without engineering knowledge |
| **Discourse capture (loop firing)** | Conversations should compound; if pattern sweep never runs, the loop is fake |
| **Knowledge freshness** | Old claims drift toward wrong; stale-flag must actually surface |
| **Opposing-case discipline** | No skin in game = should always offer counter-case alongside recommendation |
| **Use-vs-build ratio** | Time spent in actual ideation vs. building meta-architecture |

---

## Trigger schedule

- **Every 5 sessions** (use sessions count from `/start-session` boot output)
- **After every major milestone** (architecture rev, new dimension added, founder explicitly asks)
- **On founder request** ("how are you doing on the bias flags?")

---

## Checkpoints

### 2026-04-27 — Checkpoint #2 (post-Techstars-batch, major-milestone trigger)

**Trigger:** Major milestone — 13 Techstars notes ingested, corpus jumped from 3 to 16 external sources. Re-scoring all dimensions vs. Checkpoint #1.

| Dimension | Score | Δ vs #1 | Evidence |
|---|---|---|---|
| Sourcing diversity | 🟡 3/10 | +2 | Was 1/10 (YC monoculture). Now 2 external publishers (Techstars 13 + YC 3) — Techstars-dominant ~81%. Still accelerator-only — zero indie/bootstrapper/failure-archive sources. Real diversity needs 4+ distinct publisher types, not 2 accelerators. |
| Anecdote-vs-evidence framing | 🟡 4/10 | +1 | Marginal improvement. New THEMES use "tends to" / "in this corpus" language more consistently. But Techstars is ALSO a curated-survivor publisher — the bias hasn't structurally changed, just diversified slightly. |
| Persona depth & voice | 🔴 1/10 | 0 | Still 🌱 Apprentice tier. Techstars added earned-aesthetic candidates (Lean Canvas discipline, OKR cadence, EQ self-awareness) but PERSONA.md hasn't tier-promoted yet — still <5 ideation sessions. |
| Founder legibility | 🟡 3/10 | 0 | STATE_OF_THE_AGENT.md exists but hasn't been refreshed at /end-session yet (no /end-session has run). Untested. |
| Discourse capture | 🔴 2/10 | 0 | Auto-memory still empty. Pattern sweep never fired. IDEATION_LOG empty. The architecture is wired; the loop remains aspirational. |
| Knowledge freshness | 🟢 N/A | — | All notes <1 day old. Will become measurable in ~6 months. |
| Opposing-case discipline | 🔴 3/10 | +1 | TENSIONS now has 2 entries (was 1) — including the Speed-first vs Deliberate-methodology tension. Genuine opposing-case work happened during Techstars synthesis. But CLAUDE.md rule still untested in actual recommendations. |
| Use-vs-build ratio | 🔴 2/10 | +1 | We *did* finally do real ingestion work (13 substantive notes is the highest-ratio "use" activity yet). But still zero real ideation sessions on a founder problem. The mission-aligned use case hasn't fired. |

**Net assessment:** *The Techstars batch is the most mission-aligned work we've done all day — actual content ingested, cross-publisher synthesis happened, real themes and tensions earned their places. Sourcing diversity is up but still accelerator-monocultured. The system has now seen the full Techstars worldview vs the YC worldview and reconciled them in TENSIONS. **The biggest remaining failure mode is still: no ideation session has happened.** All this scaffolding and content, zero application to a founder problem.*

**Interventions queued:**
1. **Diversify publishers beyond accelerators** — target indie hackers (Pieter Levels, Tyler Tringas), bootstrappers (Rob Walling, DHH), failure-archive (founder post-mortems). Goal: diversity 3/10 → 6/10 by Checkpoint #3.
2. **Run an actual ideation session** on a real personal problem from the founder. This is now the single biggest gap.
3. **Test the auto-loop end-to-end** by running `/end-session` once — would surface whether STATE_OF_THE_AGENT, pattern sweep, and PERSONA-update routines actually fire.
4. **Promote to PERSONA.md Tier 🌿 Developing** if/when sessions count crosses 2 (currently 1).

**Next checkpoint:** when sessions count hits 6 (current = 1), or major milestone, whichever first.

---

### 2026-04-27 — Checkpoint #1 (baseline, post-architecture-rev)

**Trigger:** First checkpoint, baselining honest scores after build phase.

| Dimension | Score | Δ vs last | Evidence |
|---|---|---|---|
| Sourcing diversity | 🔴 1/10 | — | 3/3 sources from YC. Zero variance in worldview. |
| Anecdote-vs-evidence framing | 🟡 3/10 | — | Inconsistent. I sometimes flag "what experienced founders TEND to say"; sometimes I assert as if proven. Need a CLAUDE.md rule. |
| Persona depth & voice | 🔴 1/10 | — | Apprentice tier. By design at this corpus size, but still 1/10 in absolute terms. |
| Founder legibility | 🟡 3/10 | — | STATE_OF_THE_AGENT.md created today (this checkpoint). Untested in usage. |
| Discourse capture | 🔴 2/10 | — | Auto-memory empty. Pattern sweep rule never fired. IDEATION_LOG empty. Wired ≠ working. |
| Knowledge freshness | 🟢 N/A | — | All notes <1 day old. Stale-check rule wired today. Will become measurable in ~6 months. |
| Opposing-case discipline | 🔴 2/10 | — | Honest admission: I make recommendations without offering counter-case by default. Need a CLAUDE.md rule + check. |
| Use-vs-build ratio | 🔴 1/10 | — | ~5 hours building meta-architecture, ~10 minutes simulating an ideation answer. Inverted from where it should be. |

**Net assessment:** *Architecture is structurally sound. Mission execution is at zero. The biggest risk is not the system — it's that we keep extending the system instead of using it. Three structural blind spots remain even after today's build: opposing-case discipline, anecdote framing rigor, and the use-vs-build ratio. The first two need CLAUDE.md rules. The third needs founder behavior change (more ingesting + ideating, less architecting).*

**Interventions queued:**
1. **Diverse sources, next 5 ingestions** — target: sourcing diversity → 5/10 by Checkpoint #2
2. **CLAUDE.md rule: opposing-case discipline** — every recommendation must include a "case against" or explicit "I don't see a strong counter" — not silently assume agreement
3. **CLAUDE.md rule: anecdote framing** — synthesis must say "tends to" / "in this corpus" — never "is" without source backing
4. **Run real ideation session within 3 sessions** — picks a personal problem, applies the architecture
5. **Stop adding new meta-files for next 5 sessions minimum** — force the system to prove value before extending

**Next checkpoint:** when sessions count hits 6 (current = 1) OR at next major milestone, whichever first.

---

## How to read trends

Once Checkpoint #2 lands, the table above gets a Δ column showing whether each dimension is improving 🟢, holding 🟡, or worsening 🔴. Patterns to watch:
- **Improving but slowly** = intervention working but needs more reps
- **Plateaued at low score** = intervention not working; redesign
- **Worsening** = system actively drifting; emergency fix
- **Improving fast** = lock in the cause and protect it

---

## Limit of this self-assessment

I'm scoring myself. There's an inherent conflict-of-interest: I might over-score myself on dimensions that flatter the architecture I built. The mitigation: scores get exposed in [STATE_OF_THE_AGENT.md](knowledge/STATE_OF_THE_AGENT.md) for founder review. If a score feels self-flattering, **tell me** and I'll re-score with the correction logged here.
