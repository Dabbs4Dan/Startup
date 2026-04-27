# Tensions — Where Sources Disagree

> Disagreements between sources are gold for ideation. The agent reads this **before answering any ideation question** so it can surface the right fork in the road instead of presenting false consensus.

**Last updated:** 2026-04-27 (post-Rob Snyder)
**Active tensions:** 3 · **Resolved:** 0

---

## How this file works

- **Active tensions** = unresolved disagreements between sources. Each one is an H3 with: the disagreement, named positions, reconciliation guidance, and the founder's current posture (if known).
- **Resolved tensions** = the founder has chosen a side (or the field has). Move them down once that happens, with a note on what tipped it.
- **Update trigger:** every new extraction must be checked against existing notes for contradictions. If found, log it here in the same turn.
- A "tension" is not just two people saying different things — it's two credible sources pointing at the **same decision** with **different prescriptions**.

---

## Active tensions

### When does architecture investment start? (Diana Hu vs YC Lightcone)

**Diana Hu's position** ([source](knowledge/youtube/diana-hu-ai-native-company.md)): Build the AI-native architecture from **day one** — queryable org, software factory, agents in every workflow, dashboards across every function. The leverage compounds, and incumbents can't catch up.

**YC Lightcone's position** ([source](knowledge/youtube/yc-lightcone-seven-powers-ai-moats.md)): **Find a person with existential pain first.** Architecture and moats come later. Picking ideas or designs based on long-term defensibility is "literally the wrong way to do it." The hackathon version isn't useful, but the production polish only makes sense once you've proven the problem.

**Why this matters:** A founder reading only Diana could over-engineer the org before validating PMF — premature optimization with infrastructure they don't yet need. A founder reading only Lightcone could under-invest in the systems that *produce* the speed everyone agrees is the only early moat.

**Reconciliation (working hypothesis):** **Validate problem → adopt minimum AI-native posture → scale architecture only when usage demands it.** Concretely:
- Day 1: founder personally uses coding agents (per Diana — "you cannot outsource conviction") + ships a thing painful customers want (per Lightcone)
- Pre-PMF: do not build queryable-org infrastructure, dashboards, or sprint-planning agents. They're tools for a company that exists.
- Post-PMF (real revenue, real customers): start adopting Diana's architecture aggressively, because now you have something to compound.

**Founder's current posture:** Not yet defined — founder is pre-ideation.

**What would resolve this:** Either (a) a counter-example of an early-stage startup that was killed by *not* having queryable infrastructure, or (b) a clear statement from the founder about which side of the trade-off feels right for what they're building.

---

### Speed-first vs deliberate methodology (YC vs Techstars accelerator culture)

**YC's posture** (across [Diana](knowledge/youtube/diana-hu-ai-native-company.md), [Lightcone](knowledge/youtube/yc-lightcone-seven-powers-ai-moats.md), [Altman](knowledge/youtube/sam-altman-startup-idea-and-the-great-wave.md)): **Ship, iterate, ship faster.** Speed is the only mote that matters early. Cursor's 1-day sprint cycles are the model. Pre-PMF, don't build infrastructure — find existential pain and run at it. Diana frames the WHY (architecture-driven speed); Lightcone frames the WHAT (don't pre-optimize for moats); Altman frames the WHEN (jump on a wave others miss).

**Techstars' posture** (across the toolkit): **Prepare deliberately, build methodically.** Lean Canvas before solution. Empathy interviews before product. Mise en Place (full investor materials) before fundraising. Master Pitch with 75% of prep on the intro alone. The implicit message: **methodology compounds; rushed fundamentals don't.**

**Why this matters:** A founder reading both gets whiplash. *"Should I ship daily like Cursor or run empathy interviews and complete the canvas first?"* Both are right at different moments — but the framing collision is real and worth surfacing.

**Reconciliation (working hypothesis):** The two are about **different stages and different objects**:
- **Pre-PMF discovery work** → Techstars-style deliberate methodology. Empathy interviews, Lean Canvas, JTBD analysis. Speed of *learning*, not speed of *shipping*.
- **Post-PMF execution** → YC-style velocity. Once you have a real problem and a real customer, ship daily. Speed of *shipping*, not speed of *deciding what to ship*.
- **The trap:** treating either as universal. Pure-Techstars at the post-PMF stage = over-planning theater. Pure-YC at the pre-ideation stage = building the wrong thing very fast.

**Founder's current posture:** Pre-ideation as of 2026-04-27. Default toward Techstars-style customer-development methodology until you have a problem to ship against; then flip to YC-style velocity.

**What would resolve this:** A specific worked example of a founder who tried both sequences and reported what worked when. Or a clear statement from the founder about which stage they're optimizing for.

---

### How do you find demand? — A 3-pole tension on discovery method

**Pole 1 — Empathy interviews** ([Techstars Customer Development](knowledge/articles/techstars-customer-development.md)): Find demand through **empathy interviews + Jobs To Be Done analysis**. Get out of the building. Capture the functional + social + emotional dimensions of the customer's job. Then design the solution. **Implicit assumption:** customers can articulate (or be guided to articulate) what they want, and that's a reliable input. **Strength:** systematic, teachable, low-cost. **Weakness:** social-transaction bias (per Rob); customers say what they think you want to hear.

**Pole 2 — Sell to learn** ([Rob Snyder — Path to PMF](knowledge/articles/rob-snyder-path-to-pmf.md)): **Customer interviews are insufficient.** Despite "doing a bunch of customer research, interviews, discovery" → founders still build things people don't want. The mechanism (citing Parker Ence): interviews are **social transactions** — humans are generous, encouraging, less discerning when no money is at stake. Only the **economic transaction** of being asked for money lights up the evaluative part of the brain. So: draft a *theoretical* case study, **try to sell it**, debug what causes "hell yes" vs drop-off, unfold from there. **Strength:** real-money signal can't lie; forces founder to a real ICP fast. **Weakness:** assumes you have a *plausible* case study to start with — doesn't help the founder who has zero starting point.

**Pole 3 — Mine existing dissatisfaction signals** ([r/SaaS — u/jottrled](knowledge/reddit/r-saas-jottrled-find-startup-ideas.md)): **Don't wait for inspiration; systematically mine where dissatisfaction is already articulated.** Trustpilot 2–3 star reviews (people describing what's broken). Acquire.com $100k+ listings (find missing features in already-monetizing categories). Ahrefs low-KD keywords (search demand with winnable distribution). Then build, then market via SEO. **Strength:** breaks the "I have no idea what to start on" blank-page problem; real-revenue and real-search-traffic are real signal. **Weakness:** all three methods point at supply-side categories more than at demand-pulls; "build it in 1 month max" assumes indie-scale economics; build-then-market is exactly the sequencing Rob says causes the pain cave. Also: jottrled's keyword-rank tactic is materially weaker post-AI-overview-Google (2026 reality vs 2024 advice).

**Why this matters:** A founder picking among the three gets very different first-90-days behavior. Techstars: weeks of interviews + canvas work. Rob: theoretical case study + sales calls. jottrled: hours on Trustpilot/Acquire/Ahrefs + a 1-month build sprint. **The methodology you choose is upstream of everything else.**

**Reconciliation (working hypothesis):**
- **Use jottrled-style mining to *populate* a list of candidate problem spaces** — especially if you have no starting hypothesis. Mining is a candidate-generator, not a decider.
- **Use Techstars-style empathy interviews on a SMALL scale** (~20–30 light conversations per Parker Ence's framing quoted in Rob's deck) — to ground the candidate in real human language and confirm the problem is articulated.
- **Then switch to Rob's sell-to-learn** — draft the theoretical case study, take it to sales calls, debug toward "hell yes." This is where real demand surfaces.

The integrated sequence: **Mine → Interview lightly → Sell to learn.** Each pole is right for one phase; the trap is treating any single pole as the whole game.

**Founder's current posture:** Founder has domain (B2B SaaS sales-org tooling, mid-market+) but has pulled back from his personal-pain candidate (Candidate A) for buyer-segment reasons. Currently leaning toward jottrled-style research-first to find a more approachable segment. **This is the live decision in [IDEATION_LOG.md](knowledge/IDEATION_LOG.md).**

**What would resolve this:** A 4th source from a known PMF-found founder (e.g. failure-archive post-mortem or successful indie-hacker memoir) describing which sequence they actually ran. Or the founder running the integrated sequence above on a real idea and reporting back.

---

## Resolved tensions

*(none yet)*
