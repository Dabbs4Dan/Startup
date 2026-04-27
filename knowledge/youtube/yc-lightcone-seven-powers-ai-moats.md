---
title: The 7 Most Powerful Moats For AI Startups
speaker: Gary Tan, Jared Friedman, Diana Hu, Harj Taggar (YC Lightcone)
publisher: Y Combinator
source_type: youtube
url: https://www.youtube.com/watch?v=bxBzsSsqQAM
date_published: 2025-10-03
date_extracted: 2026-04-27
tags: [yc, moats, ai-native, founder-mindset, pmf, pricing, distribution, b2b]
---

# The 7 Most Powerful Moats For AI Startups

> **Caveat:** Transcript is YouTube auto-captions. Proper nouns may be misheard (e.g. "mote" for "moat", "Light Cone" / "Lightcone", and one apparent mistranscription of "Diana" as "Tatiana"). Speaker attribution within the panel is approximate where the source doesn't make it explicit.

## Core thesis
Hamilton Helmer's *Seven Powers* framework still maps cleanly onto AI startups — but at the early stage the only mote that matters is **speed**, and using long-term moat forecasts to choose between startup ideas is exactly backwards. Find a painful problem first; the moat shows up while you're solving it.

## Frameworks

### Hamilton Helmer's Seven Powers (the spine of the episode)
- **What:** A taxonomy of the only durable defensive positions a business can build, originally aimed at internet-era companies but the categories still hold for AI.
- **Steps / parts:** Process Power · Cornered Resources · Switching Costs · Counter-Positioning · Branding · Network Economies · Scale Economies.
- **Reframe (Jared):** "It would make a lot more sense if you just called it The Seven *Moats* — that's really what he's talking about."
- **YC's addendum:** *Speed* is the implicit 8th — it's the only mote a startup actually has at the beginning. Quoted from Varun (Windsurf): "the only mote startups have at the beginning is really just speed."

### Process Power
- **What:** You've built something so operationally complex it's expensive to replicate even when the surface looks copyable.
- **AI-era examples:**
  - Case Text (Jake Heller) — original AI-agent example.
  - Greenlight (KYC for banks), Casca (loan origination for banks) — mission-critical, "if it fails, the bank loses millions."
  - Plaid — supports thousands–tens of thousands of financial institutions; the CI/CD and crawler infra is the moat.
- **SaaS-era proof point:** Stripe, Rippling, Gusto — defensibility is "they've just built a lot of software and the back-end logic is super deep."
- **Founder takeaway:** The hackathon version takes a weekend; the production version takes the last 10% that nobody wants to do. Schlepp blindness is your friend.

### Cornered Resources
- **What:** A coveted, non-arbitrageable asset (or access point) that competitors structurally can't get.
- **Classic:** Pharma patents + FDA approval.
- **AI-era examples:**
  - Scale AI, Palantir — cornered the *brain space* of people inside DOD / Langley. The cornered resource isn't the diamond mine; it's the diamond mine in your customer's heads.
  - Character AI — fine-tuned models to bring serving cost down 10x (their own model = cornered resource).
  - Forward-Deployed Engineer (FDE) playbook — sit with a customer nobody else will, capture their workflow, turn it into prompts → evals → datasets → tuned model. The cornered resource is *real workflow data*.

### Switching Costs
- **What:** Customers are trapped because moving costs more (in money, time, or operational pain) than tolerating an inferior product.
- **Classic:** Oracle (database migrations don't happen), Salesforce (re-training a sales team is a year of lost productivity).
- **AI-era new flavor — *deep customization* as a switching cost:**
  - Happy Robot (DHL logistics), Salient (bank voice agents) — 6–12 month FDE pilots → seven-figure contracts. Once embedded into a bank's loan-consolidation / debt-recovery / fraud workflows, they're locked in.
  - "It's not just data lock-in like SaaS — it's *logic* lock-in. You customized your Zendesk a little. You don't customize Zendesk like this."
- **Counter-current:** AI also *reduces* switching costs in the other direction — LLMs can morph data from old schema to new, browser automation can extract from systems that don't let you export.
- **Consumer flavor:** Memory as switching cost. ChatGPT's accumulated personalization is becoming sticky; Claude was "way behind on memory."

### Counter-Positioning
- **What:** Doing something the incumbent literally cannot copy because it would cannibalize their own business.
- **The big AI-era story — per-seat pricing is the SaaS Achilles heel:**
  - Zendesk, Intercom, Front charge per seat → if their AI agents work, customers need fewer seats → their own success kills their revenue.
  - AI-native startups (Decagon, Sierra, Giga ML, etc.) charge **per task / per work delivered** — pricing aligned with the new product reality.
  - Founder-controlled incumbents (e.g. Intercom) *might* cannibalize themselves in time. Non-founder-controlled ones probably won't.
- **Second-mover advantage examples (counter-positioning against an early winner):**
  - Stripe vs Braintree / Authorize.net.
  - DoorDash vs Grubhub / Postmates.
  - Legora vs Harvey (legal) — Harvey bet on fine-tuning; Legora focused on the application layer and is winning.
  - Giga ML vs Sierra (customer support) — Giga's product "just works out of the box," so faster sales + onboarding.
  - Speak vs Duolingo (language) — Speak competes on "actually learn to speak"; Duolingo is "really a gaming app."
- **Vertical wallet-share unlock (Avoca):** SaaS vendors (e.g. ServiceTitan) capture ~1% of an HVAC company's spend. Avoca, by *doing the customer support work*, gets 4–10%. → "Vertical AI SaaS will be at least 10x bigger than SaaS" because you're tapping non-software budget.

### Branding
- **What:** The brand itself is so dominant that consumers pick you over an equivalent product.
- **AI-era proof:** ChatGPT has more daily users than Google Gemini, despite Google having every internet user already + a comparable model (Gemini Pro 2.5). "If you'd told me in 2022 it would play out this way I'd have been incredulous." (And it's *also* a counter-positioning case — Google couldn't disrupt its own search ad cash cow.)
- **Caveat:** Brand takes time. Hard to manufacture deliberately as a startup; usually a consequence of being early + winning.

### Network Economies
- **What:** Each new user makes the product more valuable to every other user.
- **Classic:** Facebook, Visa.
- **AI-era reshape — networks of *data*, not users:**
  - ChatGPT logs feed the next-gen training run.
  - Cursor: every keystroke and mouse click from free users feeds the tab-autocomplete model. Best-in-class because of scale of usage.
  - Enterprise version: Salient / Happy Robot accumulating private workflow data + **evals** that compound the agent's reliability. Evals are the flywheel.

### Scale Economies
- **What:** Massive fixed-cost infrastructure → lower unit cost than any smaller competitor.
- **Classic:** UPS / FedEx / Amazon delivery.
- **AI-era reality:** Mostly plays out at the *model layer* (training a frontier LLM is capital-intensive). DeepSeek's announcement was earth-shattering precisely because it threatened to collapse this moat — though the panel notes DeepSeek's RL trick still rides on top of an expensive base model.
- **Application-layer example:** Exa (search-for-AI-agents) — investment in crawling the web is fixed-cost, amortized across all customers. Channel 3 and Orange Slice from the most recent YC batch are running the same play.

## Mental models / principles
- **"A moat is inherently a defensive thing — you have to have something to defend."** If you don't, your moat is "just a puddle in a field." — *Jared*
- **The graveyard of startups isn't full of bad ideas — it's full of products with no defensible position. But that's a one-to-a-billion problem, not a zero-to-one problem.** — *Gary*
- **Speed is the only mote that exists at the beginning.** Big companies have PRDs, PMs, and committees. Cursor shipped on **1-day sprint cycles** in 2023–2024. — *Diana / Varun*
- **The Pareto trap in AI products:** 80% of the product with 20% of the effort. The 99% reliability that makes it actually work takes 10–100x more. That last mile *is* the moat. — *Diana*
- **"Don't use frameworks to count yourself out prematurely."** Cursor didn't start with full-parameter fine-tunes. Context engineering gets you 80–90% for the first two years. — *Gary*
- **The cornered resource can be in your customer's head.** (Palantir/Scale in the DOD.) — *Gary*
- **AI-native startups effectively become forward-deployed engineering teams *for the labs*.** They figure out which verticals are valuable; the labs absorb the lessons later. — *Bob McGrew, via Jared*

## Tactics & playbooks
- Find a person with **existential pain** ("I'm not getting promoted, I might get fired, I don't want to go to work today") and solve their problem first. Moats come later.
- Ship in days, not sprints. If you're a small team and your release cycle isn't measured in days, you're handing your only moat back to the incumbent.
- Price per **work delivered / tasks completed**, not per seat. Per-seat pricing only makes sense in a world where humans do the work.
- For B2B AI agents, accept **6–12 month pilots** if they convert into seven-figure contracts and deep workflow lock-in.
- Build the **eval flywheel** as a first-class system — it's how usage compounds into a real moat in the AI era.
- Be willing to be the **second mover** if the first mover bet on the wrong axis (e.g. Harvey on fine-tuning, Duolingo on gamification).
- Don't try to train your own foundation model on day one. Context engineering first; data + evals build the case for fine-tuning later.
- If you're entering vertical SaaS, look for places where you can expand from software-budget (~1%) into operations-budget (4–10%+) by doing the work, not just enabling it.

## Counterintuitive claims
- **Speed > all seven of Helmer's powers, at the start.** Conventional view: pick an idea with strong long-term defensibility. Their argument: that's a one-to-a-billion concern; if you don't get to one, the moat is irrelevant.
- **Picking startup ideas based on which has the better future moat is "literally the wrong way to do it."** — *Jared / Gary*
- **AI can be a *switching-cost destroyer*, not just a creator.** LLMs make data migration cheap, browser agents extract from locked-down systems. Old SaaS lock-ins are softer than they look.
- **Per-seat pricing is an Achilles heel for SaaS incumbents in the agent era.** Their growth model and their AI roadmap are in direct conflict.
- **Founder-controlled incumbents will cannibalize themselves; non-founder-controlled ones won't.** Public/PE-controlled SaaS will likely lose the agent transition. (*Gary's prediction.*)
- **Vertical AI SaaS will be at least 10x bigger than vertical SaaS.** Because the wallet you're competing for isn't software — it's the labor budget. (Avoca's HVAC trajectory: 1% → 4–10% wallet share.)
- **The "AI is taking jobs" narrative is overblown for high-churn roles.** Customer-support roles already have 50–80% annual attrition because people hate the work. The remaining humans get *more* interesting jobs (managing agents, editing prompts, handling edge cases). — *Gary, on Avoca*
- **Brand can be built faster than you'd think — and against an incumbent that owns every distribution channel.** ChatGPT vs Gemini is the case study.

## Open questions
- Will the foundation labs eventually treat their models as a cornered resource and restrict access? If so, when?
- Per vertical, who wins the *AI-incumbent vs AI-native* war? (Zendesk's AI agent vs the AI-native customer-support startup.) "Could be a whole episode."
- How sustainable is consumer memory as a switching cost? Or will it commoditize the moment every model has it?
- DeepSeek showed RL on top of a base model is cheap — but the base model is still expensive. Does that genuinely erode scale economies for foundation labs, or just shift them?
- Will the second-mover advantage pattern keep holding in AI verticals, or is the speed of category formation now too fast for first-mover mistakes to be exploitable?

## Source info
- **Title:** The 7 Most Powerful Moats For AI Startups
- **Speakers:** Gary Tan, Jared Friedman, Diana Hu, Harj Taggar (Y Combinator — *The Lightcone* podcast)
- **URL:** https://www.youtube.com/watch?v=bxBzsSsqQAM
- **Published:** 2025-10-03
- **Length / format:** 45:06 video podcast, YouTube auto-captioned
- **Referenced book:** *The Seven Powers* — Hamilton Helmer (2016)
