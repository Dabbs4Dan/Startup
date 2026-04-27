---
title: Agent architecture decision — file-based "soft agent" over fine-tuning
speaker: Founder + YC Mentor agent
source_type: session
url: n/a
date_published: 2026-04-27
date_extracted: 2026-04-27
tags: [founder-mindset, ops, ai-native]
---

# Agent architecture — the decision and the build

## Core thesis
Build the YC Mentor as a **transparent, file-based "soft agent"** that grows by accumulating documents (knowledge base + meta-files + memory + routines) — not as a fine-tuned model. The agent-ness lives in the **architecture around the model**, not in the model itself. Compounding intelligence comes from a three-leg loop: **files + routines + founder feedback**.

## Frameworks

### The 3-leg compounding loop
- **What:** The mechanism by which the agent gets smarter session-to-session despite refreshing every time.
- **Parts:**
  - **Files** (`knowledge/`) — what the agent has learned about the world (sources, themes, tensions, thesis).
  - **Routines** (CLAUDE.md rules + slash commands) — when and how the agent reads + writes those files.
  - **Founder feedback** — corrections and validations that prune the system over time.
- **Failure modes:** Files without routines → dead weight. Routines without files → nothing to read. Both without feedback → drift.

### File-based vs fine-tuned (the decision matrix)

| Dimension | Fine-tuned model | File-based agent (chosen) |
|---|---|---|
| Training data needed | Thousands of examples | Works with 2 notes or 200 |
| Behavior update | Retrain (slow + expensive) | Edit a file (instant) |
| Cost | $100s–$1000s/run | Free |
| Vendor lock-in | High | Zero (markdown in git) |
| Model improvements | Lost on each retrain | Inherited free with every Claude upgrade |
| Transparency | Opaque weights | Every "weight" is a readable file |
| Fit for current goal | End-product engineering | Tool to start a company |

### The wake-up routine (the read side of the loop)

What the agent reads at every session start to "boot into the right state":
1. `CLAUDE.md` — instructions
2. `knowledge/INDEX.md` — what notes exist
3. `knowledge/THEMES.md` — synthesized cross-source patterns
4. `knowledge/TENSIONS.md` — unresolved disagreements between sources
5. `knowledge/THESIS.md` — what the founder is currently building/believing
6. `~/.claude/projects/.../memory/MEMORY.md` — auto-memory (founder profile + feedback)
7. Live counts via `ls`, git state, plus a "prove it" demonstration

### The proactive-save routine (the write side of the loop)

When the agent must save without being asked:
- **Every new extraction** → updates INDEX, TAGS, and (when applicable) THEMES + TENSIONS in the same turn.
- **Every committed thesis or ruled-out idea** → updates THESIS.md the same turn.
- **Every architectural change** → CHANGELOG entry the same turn.
- **Every system suggestion not immediately accepted/rejected** → SUGGESTIONS.md.
- **Every feedback pattern (corrections + validations)** → auto-memory the same turn.
- **Every meaningful ideation session** → session note in `knowledge/sessions/`.

## Mental models / principles
- **Knowledge in files, not in conversation.** Conversation evaporates with compression and new windows. Files survive everything.
- **The agent is the architecture around the model, not the model.** Swapping in a smarter Claude tomorrow makes the whole system better — for free.
- **Build for now, scale for success.** Same files at 2 notes or 200; only split into per-tag/per-theme directories when single files actually slow retrieval.
- **The test of compounding intelligence is answer quality on a hard cold question — not file counts or pretty indexes.**
- **Every leg of the loop must work.** Files + routines + feedback. Drop any one and the others stop compounding.

## Tactics & playbooks
- When ingesting a source, in the same turn: write the note + update INDEX + update TAGS + check THEMES + check TENSIONS. Never defer.
- When the founder commits to a direction, update THESIS.md in the same turn — do not wait for `/end-session`.
- When the founder corrects framing or validates an unusual choice, save it to auto-memory the same turn.
- At session start, surface a "prove it" line that demonstrates working memory of prior work (e.g. "dominant theme is X, active tension is Y, current thesis is Z").
- Every ~5 sessions, ask: "Is anything I'm doing across sessions feeling off?" Save the answer as feedback memory.

## Counterintuitive claims
- **Fine-tuning would make this *worse*, not better.** Conventional view: fine-tuning is the rigorous answer. Argument against: fine-tuning bakes behavior in at training time, costs money, locks to a vendor, and stops you from inheriting free model upgrades. For a tool that should grow weekly, fine-tuning is freezing.
- **The "agent" doesn't need an agent runtime.** A persistent Claude Code session reading the right files at the right moments *is* the agent. Adding a separate agent service is over-architecture for what we need.
- **Bigger context windows make file-based agents more powerful, not obsolete.** Every Claude context expansion lets us read more of the knowledge base per session for free.

## Open questions
- **Calibration:** how do we know the system is *actually* compounding intelligence vs. just accumulating files? Current answer: founder runs the cold-question test in 30 days.
- **Scaling threshold:** at what size does THEMES.md need splitting into themes/{slug}.md? Guess: ~50 themes. Don't pre-split.
- **Auto-memory hygiene:** how often should the founder review accumulated memory and prune? Probably needs its own routine eventually.
- **Mid-session compression:** even with proactive saves, a long ideation thread can compress mid-flight. Is the rule "save after every 10 exchanges" enough, or do we need something more aggressive?

## What got built today (the receipts)
- `knowledge/THEMES.md` (3 themes seeded from existing 2 notes)
- `knowledge/TENSIONS.md` (1 tension seeded — Diana vs Lightcone on architecture timing)
- `knowledge/TAGS.md` (10 tags indexed across 2 notes)
- `knowledge/THESIS.md` (scaffold; empty until founder commits)
- `knowledge/CHANGELOG.md` (this rev logged)
- `knowledge/SUGGESTIONS.md` (1 deferred item: stale-check routine)
- `knowledge/sessions/2026-04-27_agent-architecture.md` (this file)
- CLAUDE.md updated: ideation routine, extraction routine, wake-up routine, proactive saves, every-5-sessions check, current state
- `/start-session` updated: now reads + surfaces THEMES/TENSIONS/THESIS, includes "prove it" line
- `/end-session` updated: commits new meta files

## The test
30 days from now:
1. Open a fresh window
2. Type `/agent`
3. Ask a question requiring synthesis across multiple sources (e.g. *"what does our knowledge base say about pricing for AI products?"*)
4. **Pass:** Named citations + surfaced disagreement + recommendation in seconds.
5. **Fail:** Generic startup advice, missed connections. → Diagnose which leg of the loop broke.

## Source info
- **Type:** Architectural decision session
- **Date:** 2026-04-27
- **Participants:** Founder + YC Mentor agent
- **Driving question (founder):** *"Will this process actually make you smarter session-to-session, or are we kicking tires? Should we make a fully trained agent instead?"*
