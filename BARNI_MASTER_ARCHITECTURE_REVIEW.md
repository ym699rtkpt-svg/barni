# Barni Master Architecture Review

## Canonical Assessment for Barni Alpha

**Review date:** 9 August 2026  
**Review perspective:** CTO design review before hiring the first engineering team  
**Mission test:** From data to understanding  
**Scope:** Product doctrine, system architecture, intelligence architecture, trust model, experience model, delivery roadmap, and their relationship to the current project structure.

This review treats Barni's specifications as one product. It does not replace the Constitution, Company Manifesto, or detailed technical specifications. It identifies where those documents agree, where their contracts overlap, and what must become canonical before the architecture is safe to scale.

No application behavior was changed as part of this review.

# Executive Assessment

Barni has an unusually coherent product thesis for an Alpha-stage product:

> Business evidence becomes trusted memory. Trusted memory becomes understanding. Understanding becomes proportionate action.

The documents consistently reject the wrong product categories—OCR tool, archive, ERP, accounting replacement, dashboard collection, and generic chatbot—and consistently prioritize evidence, calm, trust, progressive disclosure, and human control.

The principal risk is not lack of vision. It is that the vision has been expressed repeatedly through partially overlapping architectures. Several layers currently claim responsibility for interpreting, ranking, explaining, or presenting the same observation. The intended system is sound, but its contracts and document governance are not yet singular enough for a growing team.

Barni Alpha should therefore avoid expanding intelligence breadth for the next phase. The highest-value architectural work is consolidation: one domain vocabulary, one fact lifecycle, one evidence contract, one attention policy, one operational status model, and one authoritative roadmap.

## Scorecard

| Dimension | Score | Assessment |
| --- | ---: | --- |
| **Overall architecture** | **78/100** | Strong product doctrine and promising domain services; weakened by overlapping ownership, legacy paths, and incomplete system contracts. |
| **Product coherence** | **88/100** | The mission and product boundaries are repeated consistently. Milestone naming and surface responsibilities need consolidation. |
| **Trust** | **82/100** | Evidence-first rules, conservative identity, reversibility, and comparable facts are excellent foundations. End-to-end provenance and trust-state enforcement remain incomplete. |
| **UX coherence** | **79/100** | One-screen/one-job, answer-first hierarchy, quiet states, and voice are clear. Home, Feed, Insights, Search, and review still have conceptual overlap. |
| **Scalability** | **66/100** | The target layering is appropriate, but current direct database access, Streamlit coupling, SQLite-era assumptions, missing tenancy, and absent event lifecycle limit safe scale. |

## Why the Overall Score Is Not Higher

The architecture documents describe a mature target, while the repository still contains both target services and legacy page-shaped systems. The architecture cannot be scored only on aspiration. It must also account for whether a new engineer can identify one owner for a rule, one contract for evidence, and one safe path for state changes.

# What Is Coherent

The following principles are stable across the Constitution, Manifesto, Product Vision, OS, Business Brain, Blueprint, engineering guidance, intelligence rules, design system, journeys, and milestone documents:

1. **Understanding is the product.** OCR, invoices, dashboards, and AI are supporting mechanisms.
2. **Business Memory is foundational.** Experiences must consume one remembered business, not create page-local interpretations.
3. **Evidence precedes conclusions.** Important claims must trace back to stored sources.
4. **Identity precedes comparison.** Supplier and product resolution must be canonical and conservative.
5. **Normalization precedes reasoning.** Raw prices are not comparable facts.
6. **Meaning precedes metrics.** Conclusions appear before charts, fields, and records.
7. **Human control precedes consequential action.** Recommendations do not execute themselves.
8. **Silence is a valid result.** More data must not create more noise.
9. **One screen has one job.** Product surfaces are organized by owner intent.
10. **Restaurants come first.** Horizontal expansion follows deep domain competence.
11. **Calm is functional.** Voice and presentation reduce cognitive load and protect trust.
12. **The architecture is reusable.** Identity, facts, stories, attention, and conversation are not owned by one page.

These principles strongly support the company mission. They form the durable core of Barni and should not be reconsidered casually.

# Mission Trace: From Data to Understanding

The canonical value chain should be expressed once as follows:

```text
Source Evidence
→ Ingestion Candidate
→ Human-approved Business Event
→ Canonical Identity
→ Normalized, typed Business Fact
→ Supported Observation
→ Attention Decision
→ Business Story or Answer
→ Recommended Action
→ Human Decision
→ Memory and decision history
```

Each stage has one purpose:

| Stage | Creates | Must not do |
| --- | --- | --- |
| Source Evidence | Immutable source and provenance | Claim business meaning |
| Ingestion Candidate | Extracted possibilities | Become trusted memory automatically |
| Approved Event | A confirmed occurrence | Perform analytical comparison |
| Identity | Canonical entities and aliases | Infer trends or importance |
| Business Facts | Normalized, typed, trust-statused facts | Write customer-facing narratives |
| Observations | Supported changes or conditions | Decide presentation destination |
| Attention | Priority, urgency, destination, silence | Invent or recalculate the observation |
| Stories and Answers | Human-readable explanation | Increase the factual claim set |
| Recommendations | Proportionate next step | Execute without authority |
| Actions | Controlled state change | Erase evidence or audit history |

This chain resolves most current ownership ambiguity. No downstream layer may silently redo an upstream responsibility.

# Contradictions

## 1. “Knowledge Engine” and “Business Memory” both claim source-of-truth ownership

`ARCHITECTURE.md` calls the Knowledge Engine the source of truth for learned business knowledge, while the Constitution and Barni OS make Business Memory canonical. These are not equivalent responsibilities.

**Resolution:** Business Memory is the durable source of truth. The Knowledge Engine is an application/domain process that applies approved events to that memory. It owns transformation behavior, not truth itself.

## 2. AI Chat conflicts with the Conversation Layer

`ARCHITECTURE.md` defines an `AI Chat` module and a future conversational assistant. `BAR-011_CONVERSATION_LAYER.md` explicitly says the experience is not a chatbot and forbids endless conversational history and unrestricted answers.

**Resolution:** Retire “AI Chat” as an architectural noun. Rename the module `Conversation Interface` or `Business Question Engine`, governed by the finite intent, claim, evidence, and refusal contracts in BAR-011.

## 3. Invoice Thinking uses technical conceptual labels that Narrative Review rejects

The Business Brain defines `Identity`, `Memory`, `Observations`, `Confidence`, and `Recommendation` as visible Thinking sections. BAR-012 requires conclusions, action, reasons, evidence, and original invoice in natural language, explicitly replacing those technical section names.

**Resolution:** Keep the five concepts as an internal reasoning contract only. The experience contract is BAR-012's natural narrative order. Internal structure must not dictate customer labels.

## 4. Quiet-state language conflicts with silence

Some specifications prescribe “Everything looks good,” while Proactive Barni and the Attention Engine correctly permit no output. Both can be valid, but the conditions are undefined.

**Resolution:** Silence is the engine result. “Everything looks good” is a surface-level completion message allowed only when the user explicitly opened a status/review context and the system has sufficient coverage to support that reassurance. Absence of observations alone does not prove that everything is good.

## 5. The roadmap order is obsolete relative to implemented foundations

`BARNI_MVP_ROADMAP.md` places canonical identity and evidence after several P0 experience tasks, but BAR-007 through BAR-009 concepts and related services now exist because trustworthy insights depend on identity and comparable facts first.

**Resolution:** Rebase the roadmap around dependency order: operational truth → evidence/provenance → identity → typed facts → observations → attention → stories/conversation → experience expansion.

## 6. “Every invoice links to a canonical supplier” is stronger than the uncertainty policy

The Product Blueprint states that every stored invoice links to a canonical supplier, while the trust doctrine says uncertain identities must remain unresolved and never be silently learned.

**Resolution:** Every approved invoice must have an identity-link state, not necessarily a resolved canonical supplier. Valid states should include `RESOLVED`, `PROVISIONAL_SEPARATE`, `REVIEW_REQUIRED`, and `UNRESOLVED`. An unresolved link is honest data, not a failure.

## 7. The old product identity remains visible in project documentation

`README.md` describes a “Restaurant Invoice Viewer MVP,” and `docs/VISION.md` names “Doctor Yoti OS.” Both contradict Barni's permanent identity and would mislead a new engineer.

**Resolution:** Mark them as historical immediately in documentation governance, then archive or replace them in a separately approved documentation task. They must not be treated as active specifications.

## 8. Search has two competing interaction doctrines

The Blueprint and User Journeys describe live Spotlight-style narrowing, while later Search requirements introduced a primary Search button and Enter-to-submit flow. Both cannot be equally primary without a defined behavior.

**Resolution:** Define one canonical interaction: typing provides immediate retrieval suggestions; Enter or the attached button commits a search/question and produces the stable answer/results state. Live preview and committed search must use the same backend query contract.

## 9. “One primary action” is applied too literally across composite workflows

Invoice review legitimately requires correction, evidence inspection, duplicate resolution, and approval. Identity Review requires confirm, reject, merge, split, rename, and undo. The documents sometimes imply only one action may exist at all.

**Resolution:** One primary action means one visually dominant next action per state. Necessary secondary and recovery actions may exist with lower emphasis.

## 10. Current and target architecture are insufficiently separated

`ROADMAP.md` labels itself the single source of truth and reports features as present, while `BARNI_MVP_ROADMAP.md` also acts as authoritative prioritization. `ARCHITECTURE.md` mixes existing modules with five-year targets.

**Resolution:** Every architecture and roadmap document must declare one of: `Normative`, `Target`, `Current-state`, `Historical`, or `Exploratory`. Aspirations must not appear as shipped capability.

# Duplicated Concepts

## Vision and doctrine duplication

The following documents repeat substantially the same product thesis:

- `BAR-004_PRODUCT_VISION.md`
- `PRODUCT_VISION.md`
- `BARNI_PRODUCT_BLUEPRINT.md`
- `BARNI_COMPANY_MANIFESTO.md`
- `BARNI_CONSTITUTION.md`
- the philosophy sections of `ARCHITECTURE.md` and `BARNI_OS.md`

Repetition has helped establish culture, but it creates semantic drift. “AI business companion,” “Business Memory,” “Operations Assistant,” “operating system,” and “intelligent operations manager” are used as overlapping category definitions.

**Canonical direction:** The Manifesto owns why. The Constitution owns non-negotiable product law. The OS owns long-term platform layers. Other documents should reference these instead of restating them.

## Journey duplication

`BARNI_USER_JOURNEYS.md` and `CUSTOMER_JOURNEY.md` describe overlapping first-launch, upload, insight, daily-use, and monthly-close journeys.

**Canonical direction:** Merge them into one journey specification with concise canonical flows plus research detail in appendices.

## Roadmap duplication

`ROADMAP.md` and `BARNI_MVP_ROADMAP.md` both claim planning authority. Milestone roadmaps inside BAR-011 and BAR-013 add further ordering without a portfolio dependency map.

**Canonical direction:** One active product roadmap should reference milestone specifications. Detailed milestone phases remain in their own design documents.

## Intelligence terminology duplication

The project uses:

- Business Intelligence
- Invoice Intelligence
- Proactive Intelligence
- Barni Thinking
- Business Facts Engine
- Business Story Engine
- Attention Engine
- Conversation Layer
- Knowledge Engine
- Business Brain

These can coexist only if their roles are explicit. At present, several independently rank usefulness, produce recommendations, or compose human language.

**Canonical direction:** Adopt the lifecycle in this review and classify every service as `ingest`, `memory`, `fact`, `observation`, `attention`, `narrative`, `action`, or `experience`.

# Overlapping Responsibilities

## Business Stories versus Attention

The Story Engine currently selects and prioritizes supported changes. The Attention Engine also ranks observations and assigns destinations. Selection and destination belong to Attention; narration belongs to Stories.

**Boundary:** Attention decides whether, when, and where. Stories decide how a selected supported observation is explained in Barni's voice.

## Thinking versus Invoice Intelligence

Thinking organizes invoice understanding, while Invoice Intelligence generates structured insights. Thinking must never become a second rule engine.

**Boundary:** Invoice Intelligence creates supported observations. Attention ranks them in review context. Narrative Review composes one conclusion and one action. The Thinking service may remain as an orchestration contract but must not calculate facts.

## Conversation versus Search

Search retrieves remembered entities and records. Conversation answers governed business questions. Both accept natural language and appear in Search.

**Boundary:** A shared request interpreter chooses `RETRIEVAL`, `SUPPORTED_QUESTION`, or `CLARIFICATION`. Search owns retrieval; Conversation owns claim-based answers; neither owns identity resolution or fact calculations.

## Recommendations versus Attention

Both modules discuss priority and suggested action.

**Boundary:** A recommendation defines a supported optional action. Attention decides whether that recommendation deserves presentation now and on which surface.

## Business Memory versus Business Facts

Business Memory stores canonical knowledge and provenance. Business Facts represent typed, normalized propositions suitable for reasoning.

**Boundary:** Facts are versioned records within or backed by Business Memory, produced by fact builders. Memory is the system of record; a fact ledger is a typed read/reasoning model with explicit lifecycle.

## Home versus Insights

Home answers “What matters now?” and Insights answers “What changed and why?” Both currently consume stories and attention.

**Boundary:** Home is a short, current, action-oriented attention queue. Insights is the durable exploratory explanation of meaningful changes over a chosen period. Home links into Insights; it does not reproduce it.

## Feed versus Invoice Review

Feed owns intake and remaining work. Invoice Review owns one evidence-backed decision about one candidate.

**Boundary:** Feed orchestrates the queue. Review is a dedicated state that replaces the queue while active and returns a structured outcome to Feed.

# Missing Principles

The product principles are strong, but the following architectural principles are not yet explicit enough.

## 1. Temporal truth

Business knowledge changes. Canonical names, package interpretations, VAT bases, and fact statuses need `observed_at`, `effective_from`, `effective_to`, and version/revision semantics where applicable. “Current truth” must not erase what Barni believed at the time of a past decision.

## 2. Recomputability

When an identity decision is reversed or a normalization rule changes, all dependent facts, observations, stories, and attention decisions need deterministic invalidation and recomputation. “Immediately updates” is a product promise that requires a dependency graph or event-driven rebuild policy.

## 3. Data ownership and tenant isolation

The OS mentions future multi-restaurant support, but isolation is not a future-only concern. Every durable domain record, query, cache, evidence link, and event should be scoped to a business from the beginning.

## 4. Permission and authority

The user remains in control, but actor roles are underspecified. Approving an invoice, merging identities, exporting accounting packages, undoing decisions, and viewing technical evidence need an authority model.

## 5. Privacy and retention

Documents may contain commercially sensitive or personal information. The architecture needs explicit retention, deletion, export, redaction, provider-sharing, and diagnostic-data policies.

## 6. Model and rule governance

OCR prompts, identity rules, thresholds, fact builders, attention weights, and narrative templates influence business outcomes. Each needs versioning, evaluation, rollout, rollback, and provenance.

## 7. Idempotency as a product invariant

The architecture mentions idempotency where practical, but approval, learning, fact construction, story generation, and retries must guarantee that the same event cannot grow memory twice.

## 8. Coverage versus quietness

Silence can mean “nothing important happened” or “Barni lacks enough evidence.” The user experience needs a coverage contract so quiet states never imply knowledge the system does not possess.

## 9. Accessibility and localization as architecture

Hebrew and English are treated as voice concerns, but bidirectionality, locale-specific money/date formatting, search tokenization, alias matching, and evidence rendering require shared platform contracts.

## 10. Success telemetry without engagement incentives

The Manifesto defines better decisions as success, but the system lacks a privacy-conscious outcome model. Barni needs to measure answer usefulness, resolved uncertainty, time-to-completion, prevented errors, and trusted coverage—not clicks or notification opens.

# Architectural Gaps

## 1. No canonical domain contract package

Structured objects exist across services, but there is no documented, stable package owning shared identifiers, trust statuses, evidence references, observation contracts, attention decisions, stories, recommendations, and action outcomes.

**Impact:** Services can drift in field names, confidence semantics, and evidence guarantees.

## 2. No unified evidence graph

Evidence is specified repeatedly as source invoice IDs, line IDs, values, or document links. There is no generic evidence reference capable of supporting future bank transactions, messages, contracts, POS events, corrections, and user decisions.

**Required contract:** `EvidenceRef(source_type, source_id, subrecord_id, observed_value, location, captured_at, business_id, integrity_ref)` plus claim-to-evidence relationships.

## 3. No confidence taxonomy

The documents use at least four meanings:

- extraction/provider confidence
- identity match confidence
- Business Fact completeness/confidence
- answer/observation evidence confidence

BAR-013 additionally uses a 0–5 confidence dimension. These must never be presented or combined as if equivalent.

**Required taxonomy:** Name each confidence type, define its inputs, allowed consumers, customer presentation, and prohibition on cross-type arithmetic.

## 4. Only price has a mature typed fact contract

Spend, period comparison, purchase behavior, supplier dependency, unusual totals, inactivity, VAT, and duplicate status are described as future or are still calculated from raw invoice history.

**Impact:** Conversation and Attention specifications support more questions than the current trusted fact foundation can answer.

## 5. Observation lifecycle is missing

An observation needs stable identity, first/last seen, evidence version, status, supersession, resolution, and expiry. Without this, Attention cannot reliably deduplicate, acknowledge, or re-surface changed evidence.

## 6. Attention has no implemented shared authority

BAR-013 is a strong design, but current Home, Feed, stories, and invoice intelligence still make local selection decisions. Until Attention is shared, the same fact may be loud on one page and absent on another.

## 7. Operational status is not fully singular

The repository has a shared invoice workflow service, but page code still uses `queue_status`, database `status`, batch `pass/review/fail`, OCR queue states, accountant readiness, and duplicate outcomes. Some differences are legitimate lifecycle states; others remain page-local vocabularies.

**Required model:** Separate `processing_state`, `review_state`, `approval_state`, `duplicate_state`, and `accounting_readiness`, then derive customer-facing workflow status through one service.

## 8. Direct database and page logic remain widespread

The target architecture prohibits SQL and business calculations in presentation, yet active page modules and services still query shared database helpers or SQLite directly. `app.py`, `daily_intake.py`, and `smart_archive.py` remain large orchestration surfaces.

**Impact:** Rules are difficult to test, reuse, and migrate, and target boundaries are advisory rather than enforced.

## 9. Event architecture is aspirational

`InvoiceApproved` and event-driven learning are described, but there is no documented event envelope, outbox, versioning, replay policy, consumer idempotency key, or failure recovery contract.

## 10. Search indexing and freshness contracts are absent

The product promises that Search immediately reflects approval and identity corrections. The architecture needs explicit write-to-search consistency, alias invalidation, canonical redirect, and result provenance rules.

## 11. Action lifecycle is incomplete

Recommendations and actions are described, but there is no shared contract for proposed, authorized, executing, completed, failed, reversed, and expired actions.

## 12. Quality gates lack system-level acceptance datasets

There are tests for several emerging services, but no canonical real-data evaluation suite spanning extraction correction, identity, facts, observation, attention, narrative, evidence opening, and action outcome in Hebrew and English.

# Features That No Longer Fit the Company Vision

These capabilities should not necessarily be deleted immediately. They should be removed from the customer product, consolidated, or justified against the mission.

## Archive- and database-shaped experiences

`smart_archive.py`, database dashboards, migration dashboards, and raw record/history views reflect the former invoice-viewer identity. Search and Business Memory should make records reachable without asking owners to browse storage structure.

**Disposition:** Internal tools or compatibility layer only.

## Generic dashboards

Multiple dashboard modules (`ai_dashboard`, `business_dashboard`, `batch_dashboard`, `database_dashboard`, and `enhanced_dashboard`) conflict with “one Barni” and “not another dashboard.”

**Disposition:** Consolidate customer value into Home and Insights. Keep operational diagnostics internal.

## Generic AI Accountant / AI Chat naming

This creates expectations that Barni provides professional accounting advice or unrestricted chat, both explicitly rejected by the vision.

**Disposition:** Replace with governed business questions and accountant-package workflows.

## Recipe destination before trusted recipe facts

Recipes fit the restaurant vision eventually, but a customer-facing empty or disconnected Recipes module violates “no unfinished surfaces” and does not yet strengthen the proven core loop.

**Disposition:** Keep out of primary navigation until product identity, units, yields, and recipe evidence support a real decision.

## Notifications as an early product surface

Notifications are architecturally valid only after Attention is reliable, preferences exist, and usefulness is measured. Otherwise they turn observations into noise.

**Disposition:** Defer channels; build Attention and attention memory first.

## Decorative memory growth

Egg evolution is compatible only when tied to real, explainable knowledge maturity. Generic progress meters, XP, or celebratory activity counts would conflict with the Constitution.

**Disposition:** Defer until a defensible knowledge-coverage model exists.

## Pilot, migration, repair, batch, and diagnostics tooling in customer navigation

These are operational necessities, not Barni experiences.

**Disposition:** Move behind authenticated internal/operator boundaries.

# Biggest Architectural Risks

Ranked by combined likelihood and impact:

1. **Conflicting truth across services and surfaces.** The same invoice, identity, price, or attention state can be interpreted through different paths.
2. **False trust from raw-data intelligence.** Non-price rules may still reason over invoice fields without typed fact gates.
3. **Irreversible downstream contamination.** Identity or normalization changes may not deterministically invalidate all derived conclusions.
4. **Document governance failure.** New engineers may follow obsolete or contradictory “single source of truth” documents.
5. **Evidence fragmentation.** Invoice-specific evidence models will not generalize safely to future input types.
6. **Status drift.** Processing, review, approval, duplicate, and readiness states may continue to produce conflicting counters.
7. **UI-owned business rules.** Large Streamlit modules make reuse and migration harder and allow page-local calculations.
8. **Premature intelligence breadth.** Conversation and attention may expose intents for which trusted fact types do not yet exist.
9. **Missing business/tenant boundaries.** Retrofitting isolation after multi-business data exists is high risk.
10. **Unmeasured silence.** Barni may appear calm while actually lacking coverage, creating misplaced confidence.

# Biggest Opportunities

1. **Turn trust into the differentiator.** Evidence, reversible identity, typed facts, and calm uncertainty can make Barni more credible than generic AI tools.
2. **Create one reusable understanding pipeline.** Every new input source becomes more valuable when it feeds the same identity, fact, attention, story, and action layers.
3. **Make the approval moment memorable.** A single trusted story immediately after approval proves the full data-to-understanding loop.
4. **Own restaurant purchasing memory deeply.** Comparable prices, supplier/product history, and purchasing cadence solve frequent, concrete owner problems.
5. **Use Attention to make the product calmer as data grows.** This is a strong product moat, not merely ranking infrastructure.
6. **Make Search the universal access point.** Retrieval and governed questions can make modules recede while one Barni experience strengthens.
7. **Build an evidence graph before new sources.** This prepares Barni for transactions, POS, inventory, conversations, and contracts without redesign.

# Document Governance Recommendation

## Documents that should eventually merge

### Product vision family

Merge or retire into a compact hierarchy:

- `BAR-004_PRODUCT_VISION.md`
- `PRODUCT_VISION.md`
- vision portions of `BARNI_PRODUCT_BLUEPRINT.md`

The surviving product strategy document should reference, not repeat, the Manifesto and Constitution.

### Journey family

Merge:

- `BARNI_USER_JOURNEYS.md`
- `CUSTOMER_JOURNEY.md`

Use canonical flows in the main body and detailed friction/trust analysis in appendices.

### Roadmap family

Merge or establish one-way authority between:

- `ROADMAP.md`
- `BARNI_MVP_ROADMAP.md`
- milestone roadmaps embedded in BAR documents

One roadmap owns priority and status. Milestone documents own scope and definition of done.

### Architecture family

Reconcile into a single architecture set:

- `ARCHITECTURE.md`
- `BARNI_OS.md`
- architecture sections of `BARNI_BUSINESS_BRAIN.md`
- architecture sections of `BARNI_PRODUCT_BLUEPRINT.md`

Recommended result: Barni OS for long-term conceptual layers; one Technical Architecture for enforceable service boundaries and contracts; Business Brain for domain semantics only.

### Historical and empty documentation

- `docs/VISION.md` should be archived as historical because it names another product.
- Empty `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/PROJECT_PRINCIPLES.md`, and `docs/ROADMAP.md` should be removed or intentionally populated in a future approved documentation cleanup.
- `README.md` should eventually describe Barni rather than Restaurant Invoice Viewer MVP.

## Documents that should stay independent

- **`BARNI_COMPANY_MANIFESTO.md`** — company purpose and decision philosophy.
- **`BARNI_CONSTITUTION.md`** — permanent product laws and quality gate.
- **`BARNI_PERSONALITY.md`** — voice, behavior, uncertainty, and emotional standard.
- **`BAR-001_ENGINEERING_GUIDELINES.md`** — engineering invariants and verification.
- **`BAR-002_DESIGN_SYSTEM.md`** — visual and interaction system.
- **`BAR-003_BUSINESS_INTELLIGENCE_RULES.md`** — evidence and reasoning policy, after terminology alignment.
- **`MAGIC_MOMENTS.md`** — opportunity catalog, explicitly marked non-committed.
- **Milestone specifications** such as Conversation and Attention — bounded designs with status, dependencies, and supersession metadata.
- **This review** — canonical Alpha assessment, superseded only by a dated future architecture review.

## Missing milestone records

Standalone files for BAR-007, BAR-008, BAR-009, BAR-010, and BAR-012 were not present in the project root during this review. Their concepts exist across Business Brain, Product Blueprint, OS, services, tests, and product history, but the milestone audit trail is incomplete. BAR-011 is also historically ambiguous because “Business Story Engine” and “Conversation Layer” have both been called BAR-011 in product requests.

Future milestone governance should require:

- Unique milestone ID and title
- Status: proposed, approved, implemented, validated, superseded
- Owner
- Dependencies
- Canonical contracts changed
- Migration and compatibility implications
- Definition of done
- Links to tests and successor milestone

# Canonical Responsibility Map

| Capability | Canonical owner | Consumers |
| --- | --- | --- |
| Raw source retention | Evidence/Input adapters | Review, Memory, audit |
| Invoice lifecycle | Invoice Workflow | Feed, Review, Home, Accountant |
| Canonical identity | Identity service | Facts, Search, Memory, Questions |
| Human identity decisions | Identity Review + Action audit | Identity service, Memory |
| Unit/package normalization | Shared normalization service | Fact builders only |
| Comparable price truth | Comparable Price Fact builder/ledger | Intelligence, Stories, Questions |
| Other typed facts | Business Facts Engine | Observations and questions |
| Supported changes | Observation/rule services | Attention |
| Surface ranking and silence | Attention Engine | Home, Feed, Insights, Search |
| Human-readable narration | Story/Narrative composer | All customer surfaces |
| Natural-language questions | Conversation Layer | Search primarily; contextual surfaces secondarily |
| Recommendations | Recommendation policy | Attention and Action UX |
| Consequential changes | Action workflows | Memory and external adapters |
| Visual presentation | Shared UI/design system | Streamlit pages |

# Recommended 12-Month Execution Order

The order below prioritizes dependency integrity over feature visibility. Each phase should have explicit entry and exit criteria.

## Month 1 — Establish architectural authority

- Approve the canonical lifecycle and responsibility map in this review.
- Label every product document as normative, target, current-state, historical, or exploratory.
- Choose one active roadmap and milestone registry.
- Resolve milestone numbering collisions and missing records.
- Define a glossary for evidence, event, identity, fact, observation, insight, story, attention, recommendation, and action.

**Outcome:** The first engineers can determine which document and service owns each decision.

## Months 2–3 — Make operational truth singular

- Complete one invoice lifecycle model across Feed, Review, Home, Search, and Accountant.
- Separate internal processing states from customer workflow status.
- Centralize counters and readiness derivation.
- Add idempotent approval/learning boundaries and end-to-end workflow tests.
- Remove page-local status invention.

**Outcome:** Every surface gives the same answer about what happened and what remains.

## Months 3–4 — Standardize evidence and domain contracts

- Create the generic evidence-reference and claim-evidence contracts.
- Add business scope to every durable identity, fact, observation, and decision.
- Establish confidence taxonomy and customer exposure rules.
- Version fact builders, rules, and decisions.
- Define temporal and recomputation semantics.

**Outcome:** Every conclusion is traceable in one consistent way and ready for future data sources.

## Months 4–5 — Harden Identity and Business Facts

- Validate BAR-007/008 reversibility against real merges, splits, renames, and undo.
- Ensure uncertain identity remains unresolved rather than silently canonical.
- Make Comparable Price Ledger the sole price-comparison authority.
- Implement invalidation/rebuild after identity or normalization changes.
- Add real-data coverage for packages, units, VAT, currency, quantities, and credit notes.

**Outcome:** Price conclusions are trustworthy, explainable, and reversible.

## Months 5–6 — Complete the first Magic Moment

- Route approval through facts and one supported observation.
- Apply Attention policy in invoice context.
- Render one concise story with collapsed evidence after approval.
- Update Home, Business Memory, Search, and Accountant from the same completed event.
- Measure completion time and evidence opening.

**Outcome:** One invoice visibly becomes understanding without adding intelligence breadth.

## Months 6–7 — Implement shared Attention

- Define stable observation identity and lifecycle.
- Implement trust gates, scoring, destination policy, expiry, deduplication, and acknowledgment.
- Remove local ranking from Stories, Home, Feed, and Insights.
- Calibrate with real restaurant-owner judgments.

**Outcome:** Barni consistently decides what deserves attention and what stays quiet.

## Months 7–8 — Consolidate the experience layer

- Make Home the current attention/action surface.
- Make Insights the durable change-explanation surface.
- Keep Feed focused on teaching and remaining work.
- Make invoice review follow BAR-012's narrative order.
- Move archive, diagnostics, migration, batch, and pilot tooling behind internal access.
- Remove or hide unfinished customer destinations.

**Outcome:** One Barni replaces a collection of tools.

## Months 8–9 — Make Search the trusted memory interface

- Unify live retrieval and committed query behavior.
- Use canonical identities and evidence links everywhere.
- Implement only the deterministic Conversation intents supported by existing facts.
- Preserve visible context and calm refusal.
- Verify Hebrew, English, and mixed business data.

**Outcome:** Owners can find or ask for what Barni can prove without browsing a database.

## Months 9–10 — Add typed period and spend facts

- Define inclusion, VAT, currency, credit-note, and reconciliation policies.
- Build period-spend and contribution facts.
- Enable trustworthy month comparison and spending explanations.
- Extend Attention only after these facts pass real-data evaluation.

**Outcome:** Barni can explain purchasing changes, not merely show totals.

## Month 11 — Security, privacy, and operational readiness

- Enforce business scope and permission boundaries.
- Define retention, export, deletion, diagnostic redaction, and backup/recovery.
- Add migration rehearsal, event recovery, and audit tests.
- Establish provider and rule rollout/rollback procedures.

**Outcome:** The architecture is ready for more than a single trusted local operator.

## Month 12 — Alpha validation and roadmap reset

- Run complete journeys with representative restaurant history.
- Evaluate false insights, missed attention, evidence failures, and completion time.
- Validate narrow and desktop UX in Hebrew and English.
- Interview restaurant owners about decisions improved, not feature satisfaction.
- Publish the next dated architecture review and rebase the roadmap from evidence.

**Outcome:** Barni exits Alpha planning with a measured trust baseline and a defensible next investment.

# Three Highest-ROI Improvements Remaining

## 1. One truthful invoice lifecycle across every surface

**Why it is first:** Conflicting status or counters destroy trust faster than limited intelligence. This also unlocks reliable completion stories, Home attention, Search freshness, and accountant readiness.

**Mission contribution:** Converts source data into dependable operational understanding.

**Expected effort:** Medium  
**Expected impact:** Very high

## 2. One generic evidence and confidence contract

**Why it is second:** Evidence currently exists but is shaped around individual services and invoices. A shared contract makes every conclusion explainable, supports future sources, prevents confidence misuse, and reduces duplicated implementation.

**Mission contribution:** Makes the transition from data to understanding trustworthy and auditable.

**Expected effort:** Medium  
**Expected impact:** Very high

## 3. Shared Attention applied to the approval Magic Moment and Home

**Why it is third:** Barni already has Identity, comparable prices, stories, and invoice intelligence. The highest visible value now comes from selecting one genuinely useful conclusion and showing it consistently at the moment the owner teaches Barni.

**Mission contribution:** Turns existing trusted knowledge into immediate understanding without adding a new AI capability.

**Expected effort:** Medium  
**Expected impact:** Very high

# Final CTO Recommendation

Barni should not add another broad capability until the existing pipeline has one enforceable contract from approval to evidence-backed understanding.

The company has already made the most important strategic choice: understanding, not software activity, is the product. The next architectural choice is equally important: every layer must have one owner, and no experience may bypass trust for speed or spectacle.

The standard for the next year should be:

```text
One business.
One memory.
One fact lifecycle.
One evidence chain.
One attention policy.
Many calm ways to understand.
```

If Barni protects those invariants, it can expand from invoices to many business signals without becoming an ERP, a dashboard collection, or an unreliable AI assistant.

That is the architecture that fulfills the mission:

> From data to understanding.
