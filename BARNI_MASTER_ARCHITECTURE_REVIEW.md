# Barni Master Architecture Review

## Canonical Assessment for Barni Alpha

**Review date:** 9 August 2026  
**Review perspective:** CTO design review before hiring the first engineering team  
**Mission test:** From data to understanding  
**Scope:** Product doctrine, system architecture, intelligence architecture, trust model, experience model, delivery roadmap, and their relationship to the current project structure.

This review treats Barni's specifications as one product. It does not replace the Constitution, Company Manifesto, or detailed technical specifications. It identifies where those documents agree, where their contracts overlap, and what must become canonical before the architecture is safe to scale.

No application behavior was changed as part of this review.

# Executive Summary

Barni has an unusually coherent product thesis for an Alpha-stage product:

> Business evidence becomes trusted memory. Trusted memory becomes understanding. Understanding becomes proportionate action.

The documents consistently reject the wrong product categories—OCR tool, archive, ERP, accounting replacement, dashboard collection, and generic chatbot—and consistently prioritize evidence, calm, trust, progressive disclosure, and human control.

The principal risk is not lack of vision. It is lack of subtraction and enforcement. The vision has been expressed repeatedly through partially overlapping architectures, while the repository still carries the earlier invoice viewer, multiple dashboards, archive-shaped workflows, internal tools, experimental intelligence surfaces, and newer trust services at the same time. Several layers claim responsibility for interpreting, ranking, explaining, or presenting the same observation. The intended system is sound, but the actual product boundary and service contracts are not yet singular enough for a growing team.

Barni Alpha should therefore avoid expanding intelligence breadth for the next phase. The highest-value architectural work is consolidation: one domain vocabulary, one fact lifecycle, one evidence contract, one attention policy, one operational status model, one customer experience, and one authoritative roadmap. This is not housekeeping. It is the work that determines whether users will trust Barni and whether the first engineers can extend it without creating contradictory truths.

The brutally honest conclusion is:

> Barni currently has the product doctrine of a world-class company, the architectural ambition of a platform, and the implementation shape of an evolving prototype.

That is acceptable for Alpha only if the company stops adding conceptual layers and proves one narrow loop end to end. If Barni continues adding engines, surfaces, and future capabilities before consolidating them, the sophistication of the documentation will conceal rather than reduce product risk.

## Scorecard

| Dimension | Score | Assessment |
| --- | ---: | --- |
| **Overall architecture** | **78/100** | Strong product doctrine and promising domain services; weakened by overlapping ownership, legacy paths, and incomplete system contracts. |
| **Product coherence** | **88/100** | The mission and product boundaries are repeated consistently. Milestone naming and surface responsibilities need consolidation. |
| **Trust** | **82/100** | Evidence-first rules, conservative identity, reversibility, and comparable facts are excellent foundations. End-to-end provenance and trust-state enforcement remain incomplete. |
| **UX coherence** | **79/100** | One-screen/one-job, answer-first hierarchy, quiet states, and voice are clear. Home, Feed, Insights, Search, and review still have conceptual overlap. |
| **Scalability** | **66/100** | The target layering is appropriate, but current direct database access, Streamlit coupling, SQLite-era assumptions, missing tenancy, and absent event lifecycle limit safe scale. |
| **Maintainability** | **61/100** | Modular services and tests are emerging, but large page modules, parallel legacy systems, direct data access, duplicated documents, and unclear service ownership make change risky. |

## Why the Overall Score Is Not Higher

The architecture documents describe a mature target, while the repository still contains both target services and legacy page-shaped systems. The architecture cannot be scored only on aspiration. It must also account for whether a new engineer can identify one owner for a rule, one contract for evidence, and one safe path for state changes. Today, that answer is often “probably,” not “yes.”

## Review Coverage and Source Integrity

This assessment reviewed every Markdown architecture, product, vision, journey, roadmap, design, intelligence, pilot, and review document present in the repository. It also inspected the project structure and the active service/UI boundaries to test whether the written architecture maps to real ownership.

The requested `BAR-003_BUSINESS_INTELLIGENCE.md` does not exist under that exact name; the repository contains `BAR-003_BUSINESS_INTELLIGENCE_RULES.md`, which was treated as the intended document.

Only these numbered BAR specifications exist as standalone files:

- BAR-001 Engineering Guidelines
- BAR-002 Design System
- BAR-003 Business Intelligence Rules
- BAR-004 Product Vision
- BAR-011 Conversation Layer
- BAR-013 Attention Engine

BAR-005 through BAR-010 and BAR-012 do not exist as standalone documents. Their concepts are distributed through the Blueprint, Business Brain, OS, services, tests, and historical requests. This review does not pretend those missing files were available. Their absence is itself a material architecture-governance finding.

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

# Biggest Strengths

## 1. The company knows what product it does not want to become

The rejection of OCR-as-product, ERP density, accounting replacement, generic dashboards, fake AI, gamification, and noisy notifications is strategically valuable. Many startups discover these boundaries only after years of feature accumulation.

## 2. Trust is designed as architecture, not copywriting

Canonical identity, reversible decisions, source evidence, comparable facts, calm uncertainty, conservative recommendations, and explicit refusal form a credible trust foundation. This is Barni's strongest potential competitive advantage.

## 3. The value chain is directionally correct

Data → identity → normalization → facts → understanding → action is the right abstraction for a multi-source business-memory product. It can outlive invoices, Streamlit, SQLite, and any specific AI model.

## 4. Product and voice principles reinforce each other

“Meaning before metrics,” “silence is a feature,” one primary action, progressive disclosure, and Barni's quiet confidence describe one coherent experience rather than separate brand and UX systems.

## 5. Human correction is treated as durable knowledge

Identity Review and reversibility recognize that the owner is not merely correcting a form. The owner is teaching the system. Preserving evidence and decision history is the correct long-term model.

## 6. The architecture resists page-local intelligence

The repeated insistence that UI renders rather than reasons is correct. The newer fact, story, identity, workflow, and intelligence services show movement toward reusable domain boundaries.

## 7. Restaurants are a strong initial wedge

Frequent supplier invoices, volatile prices, recurring purchases, mixed naming, narrow margins, and time-poor owners create a real environment in which trusted memory can become visible value quickly.

# Biggest Weaknesses

## 1. Barni has too many names for its own thinking

Knowledge Engine, Business Brain, Business Intelligence, Invoice Intelligence, Proactive Intelligence, Thinking, Facts, Stories, Attention, Conversation, and Recommendations form a conceptual tax on every future engineer. Several are valid stages, but the documents do not enforce the boundary consistently.

## 2. The company has designed a platform before proving one indispensable behavior

The OS anticipates payroll, employees, CRM, bank data, WhatsApp, contracts, POS, inventory, and more. That vision is plausible, but the current product has not yet proven that one restaurant owner returns because Barni reliably notices and explains one important purchasing change.

## 3. The customer product still reflects its invoice-viewer ancestry

Archive logic, database dashboards, batch tools, raw statuses, large Streamlit pages, and multiple dashboard concepts remain close to the active product. The documentation says “one Barni”; the repository still says “many tools.”

## 4. Trust contracts are specified more completely than they are operationalized

Price facts are the strongest example. Other claims—unusual spending, supplier attention, inactivity, duplicate similarity, business completion, and period explanations—do not yet have equally mature typed fact and evidence contracts.

## 5. Documentation quantity is reducing clarity

There are multiple visions, roadmaps, architecture descriptions, journeys, and product-law documents. A new engineer can cite a correct sentence from the wrong authority and still create architectural drift.

## 6. The architecture underestimates lifecycle complexity

Facts, observations, stories, attention decisions, recommendations, and identity decisions all change over time. Versioning, invalidation, replay, expiry, supersession, and recovery are not yet first-class enough.

## 7. Scale risks are postponed rather than bounded

SQLite and Streamlit are reasonable Alpha choices. Missing business scoping, permissions, data retention, and event idempotency are not merely future scaling concerns; they shape every record created today.

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

# Technical Debt

## Critical debt

1. **Parallel status vocabularies.** Database status, queue status, batch states, duplicate state, learning state, and accountant readiness are not one explicit state model.
2. **Large UI/orchestration modules.** `daily_intake.py`, `smart_archive.py`, `app.py`, and other page-shaped modules combine interaction state, workflow sequencing, formatting, and data access.
3. **Direct persistence knowledge.** Several services and pages understand SQLite tables or general database helpers directly instead of stable repositories.
4. **Derived-data invalidation.** Identity reversal or source correction lacks a documented, comprehensive rebuild path for facts, observations, stories, Search, and counters.
5. **Legacy customer surfaces.** Older dashboards, archive views, diagnostics, and migration utilities remain in the same application architecture.

## High debt

1. **No shared evidence type across domains.** Each service invents evidence shape around invoice IDs and dictionaries.
2. **No stable domain event envelope.** Event version, business scope, causation ID, idempotency key, occurred time, actor, and replay behavior are not canonical.
3. **Inconsistent domain object strength.** Dataclasses and structured objects coexist with dictionaries and pandas rows, permitting silent shape drift.
4. **No enforced dependency boundaries.** The intended layering is documented but not protected by package structure or architecture tests.
5. **UI styling duplication.** The design system is strong on principles, but Streamlit limitations and page-specific CSS still make visual behavior expensive to maintain.
6. **Insufficient end-to-end tests.** Unit tests exist for newer services, but the defining loop is not yet protected as one repeatable contract test with real database and file behavior.

## Medium debt

1. **Historical names and files.** “Restaurant Invoice Viewer,” “Doctor Yoti OS,” AI Accountant, archive, and multiple dashboard names communicate obsolete mental models.
2. **Localization inconsistency.** English product copy, Hebrew operational copy, bidirectional business data, and formatting rules are not governed by one locale service.
3. **Operational tooling boundaries.** Pilot logs, diagnostics, migrations, and repair flows need an explicit operator application or protected mode.
4. **No documentation build or validation.** Broken links, duplicate milestone IDs, obsolete authority statements, and empty docs can enter the repository unnoticed.

# Product Risks

## 1. The owner may not experience value before being asked to maintain data

Identity review, invoice correction, approval, and evidence confirmation all demand work. If the immediate post-approval understanding is weak, Barni feels like data preparation software—the exact category it rejects.

## 2. “Business Memory” may remain an internal metaphor

The phrase is compelling to the company, but owners care about remembering a price, catching a duplicate, preparing a supplier conversation, or closing the month. Memory must be proven through outcomes, not explained as a feature.

## 3. Calmness can hide incompleteness

Silence is premium only when coverage is sufficient. Without coverage disclosure, a quiet Home can create false reassurance.

## 4. Evidence can become burdensome

Evidence links build trust, but exposing too much provenance turns every answer into an audit workflow. The default experience must remain conclusion-first with evidence one action away.

## 5. Conversation can overpromise intelligence

Even without chat bubbles, “Ask Barni anything” implies broad capability. A finite intent registry will feel broken unless supported scope, refusal, and suggested questions are designed with exceptional care.

## 6. Restaurant specificity can be diluted too soon

The OS is designed for many industries and data sources. Pursuing that breadth before restaurant purchasing is indispensable would sacrifice the domain depth that makes Barni defensible.

## 7. Too many top-level surfaces can recreate ERP navigation

Home, Feed, Search, Business Memory, Insights, Accountant, Recipes, Identity Review, and internal tools can easily become modules the user must learn. Barni should grow capabilities behind a simpler experience, not add destinations for every service.

# Areas That Are Over-Engineered

## 1. Long-term OS breadth

Employees, payroll, customers, bookings, CRM, contracts, government forms, email, WhatsApp, POS, inventory, and bank transactions are architecturally imaginable but premature. They should remain a one-page vision, not influence near-term abstractions beyond generic evidence and business scoping.

## 2. Number of conceptual engines

The system has designed separate named layers for facts, intelligence, proactive intelligence, thinking, stories, attention, conversation, recommendations, and a Business Brain. A smaller vocabulary could describe the same architecture more clearly.

Recommended simplification:

```text
Memory
→ Facts
→ Observations
→ Attention
→ Explanation
→ Action
```

Thinking, Stories, and Conversation become explanation modes, not independent truth-producing engines.

## 3. Conversation roadmap before trusted fact coverage

The Conversation document is thorough, but most valuable owner questions require period-spend and behavior facts that do not exist yet. The specification is ahead of the product foundation.

## 4. Extensive future module catalog

The target architecture enumerates Recipes, Reports, Notifications, Settings, AI Chat, and multiple intelligence modules before their user demand and contracts are proven. A modular monolith with fewer bounded packages is the better near-term architecture.

## 5. Attention precision before calibration data

BAR-013 defines detailed weights and thresholds. The dimensions are useful; the numeric model should be treated as a hypothesis until restaurant-owner ranking data exists. False precision in attention scoring would violate Barni's own intelligence rules.

# Areas That Are Under-Designed

## 1. The approval transaction

The most important product event must atomically or reliably coordinate invoice state, canonical links, fact construction, learning events, Search freshness, accountant readiness, and the completion story. Its failure and retry behavior needs a formal design.

## 2. Evidence as a platform primitive

Evidence should support any source type and every claim, correction, recommendation, and action. The current invoice-centric references are insufficient for the OS vision.

## 3. Fact and observation lifecycle

Facts need version, validity, supersession, builder version, and recomputation status. Observations need stable identity, first/last seen, resolved state, evidence revision, expiry, and reactivation rules.

## 4. Multi-business isolation

Business ownership must be part of identifiers, repositories, events, caches, files, and tests before remote deployment—not retrofitted afterward.

## 5. Permissions and accountability

Owner, manager, reviewer, accountant, and internal operator roles need explicit authority boundaries. “Who confirmed” is stored in places, but not governed as a system.

## 6. Privacy and AI provider boundaries

What is sent to extraction or language providers, how long it is retained, how users export/delete it, and how diagnostics are redacted need company-level policy and enforceable adapters.

## 7. Recovery and operations

Backup, restore, archive integrity, partial approval failure, stuck processing, event replay, and migration rollback are trust features for a product holding business evidence.

## 8. Outcome measurement

The product cannot optimize for “better decisions” without defining observable proxies: time to finish daily intake, corrections remembered, duplicate payments avoided, trusted answers delivered, attention accepted/dismissed, and evidence successfully traced.

## 9. Accessibility and bidirectional interaction

Keyboard search, focus management, screen reader semantics, RTL/LTR mixed content, responsive tables, and document review at narrow widths require deliberate component-level standards.

## 10. Developer onboarding and architectural enforcement

There is no concise “start here,” no authoritative system diagram tied to packages, no decision-record index, and no automated check preventing forbidden UI-to-database or cross-layer imports.

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

# What Should Not Be Built Yet

The following work should be explicitly deferred until the Barni Alpha definition below is proven with real restaurants.

1. **Open-ended chat or generative business advice.** The evidence and fact coverage are not broad enough, and the trust cost of one invented answer is too high.
2. **Predictions and forecasting.** Historical depth, seasonality policy, evaluation data, and uncertainty calibration are not mature.
3. **Automated supplier actions.** Barni should not contact suppliers, place orders, or negotiate until recommendations have been repeatedly validated and authorization is formalized.
4. **Cross-industry expansion.** Retail, clinics, construction, services, and manufacturing would dilute restaurant learning before product-market fit.
5. **Payroll, employee, CRM, bank, POS, email, WhatsApp, contract, or inventory ingestion.** The generic evidence contract should prepare for them; the product should not integrate them yet.
6. **Recipe profitability as a primary destination.** It depends on trustworthy product identity, conversions, yield, waste, menu price, and a validated owner workflow.
7. **Multi-location intelligence.** Business isolation may be designed now, but cross-location insights should wait for single-location trust and real customer demand.
8. **External notifications.** Email and messaging channels should wait until Attention has demonstrated low false-positive rates and stable acknowledgment semantics in-product.
9. **Custom dashboards and report builders.** These recreate the configuration burden Barni exists to remove.
10. **Autonomous agents.** The company does not yet need agents; it needs deterministic facts, explanations, and controlled workflows.
11. **Gamification or visible Barni evolution.** Memory maturity has no defensible measurement contract yet.
12. **A distributed-services rewrite.** A modular monolith is the correct architecture until scale and team topology prove otherwise.
13. **A database migration for its own sake.** SQLite is not the primary problem. Ownership, lifecycle, and contracts are.
14. **More top-level navigation destinations.** New capabilities should first strengthen Home, Feed, Search, Business Memory, Insights, or Accountant.

# Next Company Priorities

## Priority 1 — Make one trusted promise, not many plausible promises

Choose the promise:

> Approve an invoice, and Barni immediately remembers it, explains the most important supported change, and can prove why.

Every team decision should serve this loop until it is boringly reliable.

## Priority 2 — Establish one architecture authority

Create a small Architecture Council function, even if it is initially one technical founder and one product owner. It owns the glossary, decision records, service boundaries, document status, and exception process.

## Priority 3 — Build the trust platform beneath the experience

Finish operational state, business scoping, evidence references, confidence taxonomy, identity reversibility, fact recomputation, and event idempotency before broad intelligence.

## Priority 4 — Reduce the customer product

Hide legacy archives, generic dashboards, diagnostics, migrations, batch tooling, placeholder Recipes, and ambiguous AI surfaces. Make the product feel smaller while the architecture becomes stronger.

## Priority 5 — Validate owner value weekly

Observe restaurant owners completing real intake and answering real purchasing questions. Measure decisions improved, time saved, corrections repeated, and attention usefulness. Do not use feature engagement as the primary signal.

# Recommended Barni Alpha Definition

Alpha is not “all current features available.” Alpha is one trustworthy learning loop used by a small number of closely supported restaurants.

Barni Alpha is complete when:

- A restaurant can feed supported invoices, review uncertainty, handle duplicates, approve, and finish in under three minutes for an ordinary daily batch.
- Every page uses one invoice lifecycle and the same counters.
- Approval is idempotent and updates Business Memory, Search, Home, and Accountant reliably.
- Supplier and product identities are conservative, reviewable, evidence-backed, and reversible.
- Every price comparison shown to a user comes from the Comparable Price Ledger.
- The approval moment shows at most one strong supported story or an honest quiet/limited state.
- Every meaningful claim opens its source invoice evidence.
- Home shows only current actionable attention and one primary next step.
- Search finds approved invoices, suppliers, and products in Hebrew and English without exposing archive structure.
- Customer navigation excludes unfinished, diagnostic, migration, repair, and generic dashboard surfaces.
- Backup, restore, integrity checking, and failure recovery have been rehearsed.
- At least three pilot restaurants complete the core journey repeatedly without contradictory states or unsupported insights.

Alpha does **not** require open-ended conversation, predictive intelligence, external notifications, recipes, multi-location, or new data sources.

# Recommended Barni Beta Definition

Beta proves repeatable value and operating safety beyond founder-supervised use.

Barni Beta is complete when:

- Ten to twenty restaurants use the daily workflow with production-like data over multiple months.
- Business scoping, permissions, audit records, retention, export, deletion, and provider-data policies are enforced.
- Period-spend and supplier/product contribution facts reconcile to source evidence.
- Attention is shared across Home, Feed, and Insights, with measured false-positive and dismissal rates.
- Search supports a small deterministic set of evidence-backed business questions with calm refusal outside supported coverage.
- Identity corrections trigger deterministic recomputation and never leave stale conclusions.
- Accountant readiness and monthly export are trusted by real owner/accountant pairs.
- Monitoring, migration, backup, recovery, and support workflows operate without exposing internal tooling to customers.
- The company can demonstrate recurring value: time saved, avoided duplicate risk, trusted price changes found, or faster business answers.

Beta still does not require broad integrations, autonomous actions, or cross-industry expansion.

# Recommended Barni V1 Definition

V1 is the smallest product a restaurant can rely on without founder supervision and would be disappointed to lose.

Barni V1 is complete when:

- The Feed → understand → act → remember loop is fast, reliable, and self-explanatory.
- Home answers “What deserves my attention today?” with high precision.
- Search answers the most common purchasing-memory questions from trusted facts and source evidence.
- Business Memory provides reliable supplier, product, comparable price, and purchasing history without database-shaped browsing.
- Insights explains supported period changes and their contributors, not just charts.
- Accountant provides a dependable monthly readiness and export workflow without pretending to replace accounting software.
- Identity Review asks only valuable questions and remembers reversible decisions across the product.
- Privacy, tenancy, permissions, auditability, recovery, accessibility, and bilingual behavior meet a documented production standard.
- Product usefulness is validated across a meaningful restaurant cohort, with retention driven by recurring decisions rather than upload volume.
- The modular monolith has enforceable boundaries and can accept a second evidence source without redesigning Identity, Facts, Evidence, Attention, or Explanation.

V1 should still feel smaller than most business software. Its power should come from connected understanding, not module count.

# If OpenAI, Apple, or Linear Were Building Barni Today

## What OpenAI would simplify

OpenAI would likely reduce the architecture to a governed intelligence loop with strong evaluations:

- One tool-using question interface backed by typed facts and strict evidence retrieval.
- One shared evaluation suite for factuality, refusal, citation, and recommendation boundaries.
- Fewer hand-named intelligence engines; more explicit contracts between retrieval, reasoning, verification, and action.
- Model flexibility behind adapters, with deterministic verification controlling what reaches the user.

OpenAI would probably challenge the current amount of deterministic template architecture in Conversation once the claim verifier is mature—but it would also insist that natural-language flexibility never expand the supported fact set.

## What Apple would remove

Apple would remove most visible product architecture:

- No archive page as a primary concept.
- No separate dashboard family.
- No visible “engine,” “confidence,” “knowledge graph,” or “Business Facts” terminology.
- No empty Recipes destination.
- No developer, migration, pilot, or batch tools in the customer product.
- Fewer navigation items and fewer cards.

The likely Apple experience would be three dominant states:

1. **Today** — one thing worth knowing or doing.
2. **Feed Barni** — teach it new evidence.
3. **Ask/Search** — retrieve anything remembered.

Business Memory, Insights, and Accountant might remain as contextual destinations, but they would not compete equally in the first-level experience. Identity Review would appear only when Barni needs help, not as a place the user must discover.

Apple would also redesign invoice review around one sentence, one action, and one evidence affordance. The editable form would be visually subordinate.

## What Linear would redesign

Linear would enforce one domain model and make the workflow extremely fast:

- One command/query layer between UI and domain services.
- Keyboard-first Search and review.
- Stable, explicit workflow states with no page-specific naming.
- One component system and one owner per interaction pattern.
- Aggressive removal of legacy routes and duplicated components.
- Small, reversible migrations rather than permanent compatibility clutter.
- Product telemetry around completion speed, error recovery, and decision usefulness.

Linear would likely replace long specification documents with a concise product constitution, a technical architecture, a design system, a roadmap, and short decision records. It would treat the current documentation sprawl as a maintainability bug.

## The combined verdict

All three companies would simplify Barni more aggressively than the current plan.

They would keep:

- The mission
- Canonical memory
- Evidence-first trust
- Reversible identity
- Comparable facts
- Quiet attention
- Human control

They would remove or redesign:

- Multiple dashboards
- Archive-first navigation
- AI Accountant and generic chat framing
- Overlapping engine names
- Page-local intelligence
- Premature Recipes, Notifications, and multi-domain expansion
- Customer-visible technical confidence and architecture vocabulary
- Duplicate roadmaps, visions, and journey documents

Most importantly, they would not ask the customer to understand Barni's architecture. They would make the architecture disappear behind one immediate experience:

> Barni noticed what changed, explained why, and showed the evidence.

That is the product. Everything else is implementation.

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
