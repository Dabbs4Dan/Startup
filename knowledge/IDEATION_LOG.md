# Ideation Log — Live Threads

> Lightweight running log of in-flight ideation threads. Different from `THESIS.md` (commitments) and `knowledge/sessions/` (post-decision capture). This is the **journey**, not the destination — what we're exploring, what angles we've tried, where we left off.
>
> The agent reads this **at every session start** so live threads stay alive across sessions instead of being re-discovered each time.

**Last updated:** 2026-04-27
**Active threads:** 1

---

## How this file works

- **One H2 section per active thread.** Title is a short noun phrase for the idea.
- **Status:** one of `🟢 exploring` · `🟡 leaning toward` · `🔴 leaning against` · `⏸️ shelved`
- **Last touched:** date of last meaningful exchange on this thread
- **Angles explored:** bulleted list, append-only — what lenses we've already tried
- **Open questions:** what we haven't resolved yet
- **Where we left off:** 1–2 sentences — the cliffhanger so next session picks up cleanly

### Promotion rules

When a thread reaches a decision, it leaves this file:
- **Committed** → moves to `THESIS.md → Decided`
- **Killed** → moves to `THESIS.md → Ruled out` (with the why-killed)
- **Shelved indefinitely** → stays here with `⏸️ shelved` status; revisited only if founder brings it up
- **Generated reusable insight** → also gets a `knowledge/sessions/{date}_{topic}.md` capture

### Update triggers

- **Within session, every time a new angle surfaces or we explore a new lens** — append to "Angles explored" the same turn.
- **At natural pause points** — update "Where we left off" so next session has a clean handoff.
- **At `/end-session`** — sweep all live threads, ensure each has an up-to-date "Last touched" and "Where we left off."

---

## Active threads

### Finding the problem space (the meta-thread)

- **Status:** 🟡 leaning toward — *B2B SaaS sales-org tooling*, mid-market+, sub-candidate TBD
- **Last touched:** 2026-04-27
- **The honest framing:** Founder is an enterprise AE at a slower-growth B2B SaaS — has domain expertise, network access via CRM, and personal pain. Domain is locked in; specific problem within domain is being narrowed.

**Angles explored:**
- 🔴 *AI agents for GTM orgs → SMB cascading-campaign re-engagement agent* — original proposed framing. Stress-tested with Rob Snyder's 6-part lens; demand cells hollow. Reverse-engineered from a hot category. **Founder reframed away from this** when asked about his actual life — SMB target was chosen because AI-agent selling is easier there, not because that's where his pain or expertise lives. **Effectively superseded** by the domain-grounded reframe below.
- 🔴 *SEO / Reddit search-monitoring tool to find unaddressed problems* — flagged as second-order tool-over-customer anti-pattern (build a system to find problems vs go find them). Founder did not push back; deprioritized.
- 🟢 *Domain-grounded reframe: B2B SaaS sales-org tooling at mid-market+* — surfaced when founder answered the 4 founder-network questions. He IS a B2B SaaS enterprise AE, sees the pain daily, has CRM-based prospect access. Four sub-candidate problems within this domain (see below).

**Sub-candidates (B2B SaaS sales-org tooling, mid-market+):**

- **Candidate A — Outbound seller pain at slower-growth SaaS.** Founder IS this customer. Project: "hit my number this quarter despite a low-demand product." Strong daily forcing function. Buyer (sales leader / VP / CRO) is hard but proven (Outreach, Apollo, Clay). Highest founder conviction. **Currently leaning toward this.**
- **Candidate B — Sales leader CRM grip.** Founder observes second-hand. Crowded (Gong, Clari, Salesforce). Periodic pain (board cycle).
- **Candidate C — Sellers using web Claude bots, not integrated AI in motion.** Founder lives this. Pull rising. Crowded (100+ funded AI-sales startups).
- **Candidate D — Procurement timing + forecasting.** Founder talks to them; doesn't live their pain. Different lane (selling to procurement vs to sellers).

**Important counter-case (acknowledged):** Selling to sales leaders / sales orgs is the most NPS-hostile, most legacy-contract-laden, most crowded buyer category in B2B SaaS. Companies in the most pain (older SaaS) are slowest to buy. Not a layup — known difficulty mode.

**Founder's pushback that landed:**
- He has more grounding than the agent initially credited — domain expertise + CRM access + personal pain.
- Rob Snyder's sell-to-learn IS the problem-discovery method, not just demand-validation. SendBlue (YC) cited as proof — they found PMF only after working with clients, honing on the one valued feature.

**Open questions:**
- Of Candidates A–D, which does the founder feel the *deepest* gut pull toward? (Asked, awaiting answer.)
- For the chosen candidate: who's the most painful version of "Melissa" the founder can name from his CRM/network this week?
- Does the slow-buyer / hostile-buyer counter-case change the calculus, or is the personal-conviction edge enough to overcome it?

**Where we left off:**
Founder pulled back from Candidate A (and the "AE rabbit hole" generally) — *"I wanna focus a bit more on an approachable sales segment vs. enterprise reps at similar sized companies. At profitable companies, a lot of the stuff I'm raising goes out of the window methodology-wise."* Real read: companies in the most pain are the worst buyers; companies that'd be good buyers don't have this pain. Domain still B2B SaaS sales-org tooling, but pivoting to a more accessible *who*.

Founder proposed a methodology variant: **use Rob Snyder's framework but run paid Instagram/LinkedIn ads for first-pass case-study testing instead of cold outbound.** Said *"otherwise I might be still most interested in Rob's methodology."* → 🟡 **methodology near-commit** to Rob's sell-to-learn engine.

Agent ingested the r/SaaS jottrled idea-mining post (founder request) and upgraded the demand-discovery TENSION to 3-pole (Empathy interviews / Sell to learn / Mine signals). Reconciliation drafted: **Mine → Interview lightly → Sell to learn.**

Agent's response on the paid-ads variant: partially consistent with Rob (Rob requires 5-10 1:1 conversations/wk, doesn't mandate cold outbound specifically), partially a deviation (inbound surfaces different signal than outbound; channel-before-case-study is cart-before-horse; ad infrastructure is a tooling-project-in-disguise). Counter-case acknowledged: ad creative IS the case-study pitch; capped spend can work.

**Synthesis proposed:** test BOTH channels for 2 weeks at tiny scale ($200–500 ad cap + 5 LinkedIn DMs/week). Compare what each surfaces. Whichever sharpens the case-study debugging wins.

**The actually-load-bearing gap surfaced:** founder still hasn't picked a *who* (Melissa) or a *what* (draft case study). Without those, the channel question is premature. Agent surfaced 4 "approachable segment" candidates within the domain:
- Solo AEs at growing startups (1–3 reps)
- Sales consultancies / fractional VP-Sales
- Sales-first founders (technical founders who hate selling)
- Specific job-titles inside sales orgs that aren't VP-Sales (RevOps, sales engineers, sales enablement)

**Update — founder pivoted segment hypothesis to SMBs:** Cited "ripe segment" (decision-maker = user, AI democratization, fast yeses). Agent's earlier "SMB tar pit" pushback acknowledged as default-not-law; counter-case stands (indie hackers like Levels + Square/Toast/Gusto). Real bottleneck named by founder: *"struggling to find a worthy Melissa expanding beyond what I immediately know."*

**Founder's research-method use is now correctly shaped:** asking how to use search-backwards (Google autocomplete, Ahrefs, Reddit, G2 reviews, Acquire.com) to *back-validate* a Melissa hypothesis, not to substitute for talking to people. Promotion: this is candidate-refinement, not avoidance pattern.

**Search-backwards toolkit surfaced** (for refining a Melissa once hypothesized):
- Search-data: Google autocomplete, "People also ask," Ahrefs free keyword generator
- Community: Reddit niche subs, Indie Hackers, FB/LinkedIn groups, YouTube comments
- Incumbent-review: G2/Capterra 2-3⭐ reviews, Acquire.com $100k+ listings
- **Discipline:** don't let search data PICK the Melissa (reverse-engineering trap); let it REFINE her Project + Context cells and surface her vocabulary

**Sharpened narrowing question:** *"Who's the most specific SMB-shaped person in your actual life — friend, family, past customer — whose work you've heard them complain about?"* Even thin first-person contact gives a starting Melissa; toolkit deepens her.

Awaiting founder's named real-life SMB candidate (or alternative direction).



---

## Archived

*(threads that ended without a clean THESIS.md decision but aren't worth keeping live — keep here for searchability)*
