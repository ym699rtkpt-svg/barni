# BAR-013 — Barni Attention Engine

## Purpose

The Attention Engine decides which supported business observations deserve the restaurant owner's attention, when they deserve it, and where they should appear.

This is not a notification system.

It does not send messages, create badges, interrupt the user, or generate new business conclusions. It sits between trusted intelligence and the product experience:

```text
Trusted Business Facts
→ supported observations and Business Stories
→ Attention Engine
→ ranked attention decisions
→ Home, Feed, Insights, Search, or silence
```

Its central question is:

> Does this observation help the owner understand or act right now?

If the answer is no, the observation remains available in Business Memory and Search but stays out of the owner's way.

# Product Principles

## Trust is a gate, not a score bonus

An observation with weak evidence cannot earn attention merely because its possible impact appears large.

Before ranking, every observation must pass the evidence policy for its type. An unsupported price comparison, uncertain supplier identity, or incomplete historical baseline is blocked or routed to an appropriate review workflow.

## Silence is the default

Data existing is not a reason to surface it.

Ordinary purchases, small price movement, repeated low-value facts, and observations without a useful next step should remain silent.

## Attention is contextual

The same observation may deserve different treatment in different contexts:

- A duplicate discovered during Feed requires an immediate decision.
- A confirmed price increase may belong on Home today and remain in Insights historically.
- A normal invoice remains searchable but does not deserve Home attention.
- An identity conflict belongs in Identity Review and may warrant one calm Home prompt when it blocks meaningful understanding.

## Attention must explain itself

Every surfaced decision must include a concise reason:

> This deserves attention because the price increased 18%, the comparison is supported by two invoices, and the latest purchase is recent.

The customer receives natural language. Internal tools may expose component scores and policy decisions.

## Attention expires

An observation should not remain prominent forever. Attention state must account for recency, user decisions, superseding evidence, and whether the issue was resolved.

# What the Engine Receives

The Attention Engine consumes structured observations. It never reads Streamlit state, renders components, parses invoice text, or reconstructs business rules.

An observation contains:

- Observation type
- Title and explanation
- Category
- Occurrence date or period
- Canonical supplier and product IDs where applicable
- Structured business values
- Trust status
- Business confidence
- Evidence quality
- Source fact IDs
- Source record IDs
- Optional recommended action
- Resolution state
- Previous attention decisions for the same subject

Valid sources include:

- Business Facts Engine
- Comparable Price Ledger
- Existing Invoice Intelligence
- Business Story Engine
- Identity Review queue
- Shared invoice workflow and duplicate outcomes
- Future trusted fact ledgers

# Attention Decision Contract

Every evaluated observation returns a UI-independent decision:

```text
AttentionDecision
  observation_id
  observation_type
  subject
  importance
  confidence
  novelty
  business_impact
  urgency
  evidence_quality
  raw_score
  policy_adjustments
  final_score
  attention_tier
  recommended_destination
  reason
  recommended_action (optional)
  evidence
  source_record_ids
  expires_at (optional)
  suppression_reason (optional)
```

The decision explains both positive and negative outcomes. Internal diagnostics should be able to answer:

- Why did this reach Home?
- Why did this remain in Insights?
- Why was this suppressed?
- Which evidence changed the decision?

# Trust Gates

Scoring begins only after the observation passes its type-specific trust gate.

## Gate 1 — Supported source

The observation must originate from a registered intelligence rule, trusted Business Fact, explicit workflow event, or confirmed memory relationship.

## Gate 2 — Canonical identity

Identity-dependent observations require the relevant canonical supplier or product. Unresolved aliases cannot support historical conclusions.

## Gate 3 — Required evidence

Every factual claim must retain source evidence. The required number and type of sources depend on the observation.

Examples:

- Price change: two trusted comparable price facts and both invoices
- Duplicate: both invoice identities and matching fields
- New supplier: canonical supplier and its first approved invoice
- Unusual spending: current observation and a sufficient trusted baseline

## Gate 4 — Comparability

Comparative observations must use the correct shared fact ledger. Unit, package, VAT, currency, date, and inclusion policies must be compatible.

## Gate 5 — Minimum history

Pattern observations require enough history for their registered rule. A seasonal pattern cannot be inferred from two purchases. A disappeared product cannot be claimed without a stable previous cadence and enough elapsed time.

## Gate 6 — Action proportionality

A recommended action may not exceed the evidence. A supported price increase can recommend review. It cannot recommend switching suppliers without trusted supplier alternatives.

Failed gates result in one of three outcomes:

- **Blocked:** the conclusion cannot be treated as true.
- **Review:** a valuable uncertainty enters Identity Review or invoice review.
- **Silent:** insufficient information remains stored without interrupting the user.

# Scoring Dimensions

Each dimension uses a discrete 0–5 rubric. Scores support consistent policy; they must not be presented to normal users as scientific precision.

## Importance

How closely does this observation relate to a decision the owner is responsible for?

- **0:** No meaningful owner decision
- **1:** Background context
- **2:** Useful during occasional review
- **3:** Relevant operational change
- **4:** Meaningful financial or workflow decision
- **5:** Immediate risk of loss, duplicate action, or incorrect business knowledge

## Confidence

How completely are the observation's required factual conditions satisfied?

This is Business Confidence, not AI confidence.

- **0:** Unsupported
- **1:** Material conflict
- **2:** Important evidence missing
- **3:** Supported with a declared limitation
- **4:** Strong factual support
- **5:** Complete deterministic support

Observations below their type-specific minimum confidence cannot surface, regardless of total score.

## Novelty

How new is this information to the owner and to the current attention cycle?

- **0:** Already resolved or repeatedly shown without new evidence
- **1:** Repeated ordinary event
- **2:** Known pattern with a small update
- **3:** New occurrence or material update
- **4:** First meaningful recurrence or new business relationship
- **5:** First occurrence with significant consequence

Novelty decreases when the same observation is acknowledged. It increases again only when new evidence materially changes the conclusion.

## Business Impact

What supported operational or financial consequence does the observation have?

- **0:** No measurable consequence
- **1:** Negligible effect
- **2:** Small but useful context
- **3:** Noticeable product, supplier, or workflow effect
- **4:** Material supported cost, risk, or blocked understanding
- **5:** High supported financial exposure or serious workflow risk

Impact values must be derived from trusted facts. When financial impact cannot be measured, the engine uses the registered qualitative rubric rather than inventing an amount.

## Urgency

How quickly would delayed attention reduce the owner's ability to act?

- **0:** Historical reference only
- **1:** Useful at the next periodic review
- **2:** Useful this month
- **3:** Useful this week
- **4:** Useful today
- **5:** Requires a decision in the current workflow

## Evidence Quality

How strong, complete, and traceable is the supporting evidence?

- **0:** No accessible evidence
- **1:** Raw or conflicting evidence
- **2:** Partial evidence with a material gap
- **3:** Traceable evidence with a disclosed limitation
- **4:** Trusted facts with complete source links
- **5:** Multiple mutually supporting trusted sources or an exact deterministic match

# Base Scoring Model

After trust gates pass:

```text
Base score =
  Importance       × 0.24
  Business impact  × 0.24
  Urgency          × 0.18
  Novelty          × 0.14
  Confidence       × 0.10
  Evidence quality × 0.10
```

The weighted result is normalized to 0–100.

Importance and impact lead because attention should serve decisions. Urgency determines placement timing. Novelty prevents repetition. Confidence and evidence quality remain hard gates first and ranking inputs second.

The formula is a starting policy, not a permanent truth. Changes require evaluation against real owner decisions and false-positive review.

# Policy Adjustments

Deterministic adjustments apply after the base score.

## Positive adjustments

- **Current workflow decision:** +15
- **Possible duplicate with exact deterministic evidence:** +12
- **Supported material financial effect:** up to +10
- **Blocks an approved comparison or export:** +8
- **First trusted occurrence:** +5

## Suppression adjustments

- **Already acknowledged without new evidence:** suppress
- **Resolved or superseded:** suppress
- **Same underlying change already represented by a higher-ranked observation:** suppress
- **Ordinary repeat event:** −20
- **Outside the useful action window:** −15
- **No proportionate action and low impact:** −10
- **Recently surfaced equivalent observation:** −10 to suppress

Adjustments must be recorded in the decision explanation.

# Attention Tiers

## Act now

Typical final score: 80–100, plus required urgency and confidence gates.

Use for a current decision such as an exact duplicate during Feed or a critical missing detail blocking approval.

Destinations:

- Feed
- Home only when unresolved after leaving the workflow

## Know today

Typical final score: 65–79.

Use for meaningful supported changes such as a significant price increase or a high-impact identity conflict.

Destinations:

- Home
- Insights

## Review later

Typical final score: 45–64.

Use for supported context that matters during intentional analysis but does not deserve today's attention.

Destinations:

- Insights
- Business Memory detail

## Searchable memory

Typical final score: 20–44.

The observation remains useful when requested but should not be proactively surfaced.

Destination:

- Search only

## Silent

Typical final score below 20, failed value policy, duplicate information, or insufficient evidence.

Destination:

- Silent

Silent does not mean deleted. Facts remain in Business Memory and may contribute to future supported patterns.

# Destination Policy

The destination is selected independently from visual rendering.

## Home

Home answers: What should I know or do right now?

Requirements:

- Know today or Act now tier
- Current or recently unresolved
- Strong evidence
- Not already acknowledged
- Maximum three items, usually one strong item

## Feed

Feed answers: What do I need to decide while teaching Barni?

Requirements:

- Directly related to the current invoice or batch
- Action required before workflow completion
- Clear recommendation
- Evidence available in the review context

## Insights

Insights answers: What changed, why does it matter, and what supports it?

Requirements:

- Supported historical or current meaning
- Review later, Know today, or retained resolved insight
- Evidence and period visible

## Search only

Search answers requested questions about remembered facts.

Use when the observation is reliable but not important enough to surface proactively.

## Silent

Use when an observation is ordinary, redundant, expired, weak, unsupported, or not useful to understand or act.

# Observation Policies

The examples below define initial policies, not invented conclusions. An observation is evaluated only when its existing intelligence rule or fact service supports it.

## Supplier price increase

### Required evidence

- Two trusted Comparable Price Facts
- Same canonical product
- Same canonical supplier for supplier-specific wording
- Compatible normalized unit, package, VAT basis, and currency
- Both source invoices

### Typical scoring

- Importance: 3–5 based on magnitude and purchase relevance
- Confidence: 5 when fully comparable
- Novelty: 3 for a new increase, lower if repeatedly shown
- Business impact: based on supported percentage and line impact
- Urgency: 3–4 when recently approved
- Evidence quality: 4–5

### Destination

- Home for a significant recent increase
- Insights for lower-impact supported movement
- Search only below materiality threshold
- Silent for weak or non-comparable movement

### Why it deserves attention

> The price increased materially, the comparison uses the same normalized basis, and the supplier conversation is still timely.

## New supplier

### Required evidence

- Canonical supplier
- First approved linked invoice
- No previous invoice linked to that canonical supplier

### Typical scoring

- Importance: 2–3
- Confidence: 5
- Novelty: 5
- Business impact: 1–3
- Urgency: 1–2
- Evidence quality: 4

### Destination

- Feed completion as a learning moment
- Home only when useful context accompanies it
- Business Memory and Search otherwise

### Why it deserves attention

> This is a genuinely new supplier relationship, but it does not automatically require action.

## Duplicate invoice

### Required evidence

- Canonical or strongly deterministic supplier identity
- Matching invoice number and document type
- Both source records
- Near-duplicate rules require their full registered evidence policy

### Typical scoring

- Importance: 5
- Confidence: 5 for exact duplicates
- Novelty: 4
- Business impact: 4–5
- Urgency: 5 during approval
- Evidence quality: 5

### Destination

- Feed during the current decision
- Home if unresolved
- Insights after resolution only as historical evidence when useful

### Why it deserves attention

> Acting now may prevent duplicate memory or payment, and the matching evidence is exact.

## Missing invoice number

### Required evidence

- Current invoice lacks a recognized number
- Document type policy says a number is relevant
- Current source invoice

### Typical scoring

- Importance: 3–4
- Confidence: 5 that the field is missing, not that the source lacks it
- Novelty: 2
- Business impact: 2–4 depending on workflow
- Urgency: 5 before approval, 2 after approval
- Evidence quality: 3–4

### Destination

- Feed during review
- Home only if unresolved and materially blocks readiness
- Search only after acknowledgment

### Why it deserves attention

> The missing number may prevent reliable duplicate detection or accountant readiness, and the user can correct it now.

## Product disappeared

### Required evidence

- Canonical product
- Trusted recurring purchase baseline
- Enough historical cadence observations
- Meaningfully overdue interval
- No conflicting aliases or missing period evidence

### Typical scoring

- Importance: 2–4
- Confidence: dependent on cadence stability
- Novelty: 3
- Business impact: unknown unless separately supported
- Urgency: 1–3
- Evidence quality: 3–4

### Destination

- Insights initially
- Home only when a strong stable pattern and useful action exist
- Silent when history is sparse

### Why it deserves attention

> The product has not appeared within its established purchasing rhythm, which may indicate a meaningful operational change.

This signal must remain postponed until a trusted behavior-fact model exists.

## Seasonal purchasing pattern

### Required evidence

- Canonical product or category
- Multiple comparable seasonal periods
- Sufficient repeated observations
- Explicit seasonality rule

### Typical scoring

- Importance: 1–3
- Confidence: 3–5 depending on history length
- Novelty: 1–3
- Business impact: requires separate evidence
- Urgency: 0–2
- Evidence quality: 3–4

### Destination

- Insights
- Search only for weak but supported patterns
- Never Home without timely action

### Why it deserves attention

> The pattern may explain purchasing behavior, but it is usually context rather than an interruption.

This signal remains postponed until trusted seasonal facts exist.

## Abnormal spending

### Required evidence

- Trusted current spend fact
- Trusted comparable baseline
- Consistent inclusion, credit-note, VAT, and currency policies
- Explicit abnormality rule
- Contribution evidence when explaining causes

### Typical scoring

- Importance: 3–5
- Confidence: 3–5
- Novelty: 3–4
- Business impact: 3–5
- Urgency: 2–4
- Evidence quality: 3–5

### Destination

- Home for a large recent supported change
- Insights for historical analysis
- Silent with insufficient baseline

### Why it deserves attention

> Spending moved outside its supported normal range and the difference is large enough to affect a decision.

This signal remains postponed until trusted spend facts exist.

## Unit mismatch

### Required evidence

- Canonical product or product candidate
- Conflicting normalized unit observations
- Source invoice lines
- A blocked comparison or meaningful identity impact

### Typical scoring

- Importance: 2–4
- Confidence: 5 that the units conflict
- Novelty: 2–3
- Business impact: based on blocked comparisons
- Urgency: 2–4
- Evidence quality: 4

### Destination

- Identity Review
- Home only when high-impact and unresolved
- Silent when low-value or already queued

### Why it deserves attention

> The mismatch prevents Barni from comparing prices safely, and one user decision can improve future understanding.

## Identity conflict

### Required evidence

- Conflicting or ambiguous canonical candidates
- Deterministic reasons and source evidence
- A real effect on search, history, comparison, or memory

### Typical scoring

- Importance: 2–5
- Confidence: confidence in the existence of ambiguity, not in a proposed merge
- Novelty: 3
- Business impact: based on affected facts and records
- Urgency: 2–4
- Evidence quality: 3–5

### Destination

- Identity Review
- Home only for the highest-impact unresolved questions
- Silent for weak or low-value similarity

### Why it deserves attention

> The unresolved identity affects business understanding, but Barni will not silently choose an answer.

# Deduplication and Attention Memory

The engine needs memory of its own decisions without creating a second business truth.

Attention memory records presentation state only:

- Observation fingerprint
- First evaluated
- Last evaluated
- First surfaced
- Last surfaced
- Destinations used
- Acknowledged by whom and when
- Resolved or superseded state
- Evidence fingerprint at the time

It never changes the underlying Business Fact.

Two observations are considered equivalent when they describe the same canonical subject, rule, comparison period, and materially unchanged evidence. Equivalent observations should merge into one current attention decision.

New evidence may reopen attention when it materially changes:

- Direction
- Magnitude
- Required action
- Confidence
- Business impact
- Resolution state

# UX Implications

## Home becomes calmer

Home consumes only the highest-ranked current decisions. It should usually show one meaningful story and never more than three.

Home should not fill empty space with ordinary success states, zero-count cards, or low-value observations.

When nothing qualifies:

> Everything looks good.

## Feed stays focused on the current invoice

Feed receives only decisions tied to the current invoice or batch. Historical observations may provide explanation, but unrelated business attention must not interrupt approval.

## Insights becomes the durable meaning layer

Insights retains supported observations after they leave Home. It explains what changed, why it mattered, and which evidence supported it.

## Search remains complete

Search can retrieve reliable observations regardless of attention tier. Silence means “do not interrupt,” not “hide knowledge.”

## Evidence remains progressively disclosed

The user sees:

1. What happened
2. Why it deserves attention
3. What to do, when appropriate
4. Evidence on request

Raw component scores, thresholds, and rule IDs remain internal.

# Reusable Architecture

## Observation

A shared structured input from intelligence and fact services.

## AttentionPolicy

Defines trust gates, minimum thresholds, dimension rubrics, destination constraints, expiry, and suppression rules for one observation type.

## AttentionEvaluator

Applies one policy to one observation and returns an explainable decision.

## AttentionRanker

Ranks eligible decisions within a requested surface and context.

## AttentionDeduplicator

Collapses overlapping or redundant decisions without deleting their evidence.

## AttentionMemory

Records presentation, acknowledgement, expiry, and supersession state.

## AttentionDecision

The UI-independent output consumed by Business Stories and product surfaces.

## AttentionExplanation

Produces the customer-facing reason and the internal audit explanation from the same decision components.

# Extension Model

New fact types do not require redesigning the Attention Engine.

To add a signal:

1. Create or reuse a trusted observation from the correct fact service.
2. Register its evidence policy and trust gates.
3. Define dimension rubrics.
4. Define allowed destinations and minimum tiers.
5. Define expiry and deduplication behavior.
6. Define proportionate actions.
7. Add real-data evaluations and false-positive cases.

Future observation families may include:

- Cash-flow risk
- Inventory shortages
- Contract changes
- Payroll exceptions
- Tax deadlines
- Supplier reliability
- Recipe cost movement
- Sales and margin changes

Each future source uses the same attention contract. No page may invent its own priority score.

# Evaluation Framework

The engine should be evaluated against real owner judgment, not only technical correctness.

For each candidate observation record:

- Was the underlying conclusion supported?
- Would the owner want to know now, later, only when searching, or never?
- Was the stated reason clear?
- Was the recommended action proportionate?
- Was the observation repeated unnecessarily?
- Did a more important observation get displaced?
- Could the owner open sufficient evidence?

Core quality metrics:

- Unsupported surfaced observations: target zero
- High-value observations incorrectly silenced
- Low-value observations reaching Home
- Repeated observations without new evidence
- Evidence-open success rate
- Owner agreement with destination
- Owner agreement with recommended action

Engagement and click-through are not primary success measures. Quiet correctness is more important than interaction volume.

# Implementation Roadmap

## Phase 0 — Observation contract and policy registry

- Define shared Observation and AttentionDecision contracts.
- Define destination and tier enums.
- Establish evidence gates and audit explanations.
- Create a real-data evaluation set.

## Phase 1 — Existing supported signals

Register policies for:

- Trusted price movement
- Exact duplicate
- Missing invoice number
- New supplier
- Current Identity Review conflicts

Run in shadow mode without changing UI. Compare decisions with existing Home, Feed, and Insights behavior.

## Phase 2 — Shared ranking integration

- Make Business Stories consume Attention Decisions.
- Make Home request only Home-eligible decisions.
- Make Feed request current-invoice decisions.
- Make Insights retain supported historical decisions.
- Remove page-local ranking and filler priorities.

## Phase 3 — Attention memory

- Add acknowledgement, expiry, deduplication, and supersession state.
- Prevent repeated Home stories without new evidence.
- Preserve full auditability.

## Phase 4 — Trusted behavior and spend policies

After the relevant Business Facts exist, add:

- Product disappearance
- Seasonal patterns
- Abnormal spending
- Supplier inactivity
- Supplier dependency

## Phase 5 — Calibration with restaurant owners

- Review real decisions with pilot owners.
- Tune policy thresholds and destinations.
- Measure false attention before adding more signals.
- Keep scoring explainable and deterministic.

# Definition of Done

The Attention Engine is complete when:

- Every observation passes an explicit trust gate before scoring.
- Every decision contains all six required dimensions.
- Every surfaced decision explains why it deserves attention.
- Every decision retains source evidence.
- Home, Feed, Insights, and Search use one destination policy.
- Pages do not rank observations independently.
- Duplicate observations are suppressed without deleting evidence.
- Acknowledged and resolved attention does not repeatedly return unchanged.
- Weak or unsupported observations remain silent.
- High-value current decisions reliably reach Home or Feed.
- New observation types can register policies without changing the engine core.

# Golden Rule

Attention is earned by evidence and usefulness.

If an observation does not help the owner understand or act, Barni stays quiet.
