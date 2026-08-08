# BAR-011 — Barni Conversation Layer

## Purpose

The Conversation Layer allows a restaurant owner to ask a natural-language question about the business and receive one concise, evidence-backed answer.

This is not a chatbot. It is a governed interface to Business Memory.

Barni does not hold an open-ended conversation, improvise business advice, or answer from general knowledge. It interprets a business question, identifies the trusted facts required to answer it, and either returns a traceable answer or explains what evidence is missing.

The experience should feel like asking a careful colleague who remembers the business:

> What became more expensive?

> Olive oil increased from ₪42.00 to ₪48.00 per litre since the previous comparable purchase (+14.3%).

The conclusion appears first. Evidence and detail remain available underneath it.

# Product Principles

## Evidence before language

Natural language never increases what Barni knows. It only makes trusted knowledge easier to access.

Every factual statement must resolve to:

```text
Answer sentence
→ structured answer claim
→ trusted Business Fact or confirmed Business Memory relationship
→ canonical identities
→ evidence values
→ source invoice and invoice line
→ original stored document
```

If that path cannot be constructed, Barni must not make the statement.

## This is not a chatbot

The experience must avoid:

- Chat bubbles
- A fictional persona performing conversation
- Typing indicators
- Endless conversational history
- General business advice detached from stored evidence
- Answers based on plausible assumptions
- A model filling gaps in Business Memory
- Follow-up questions designed only to prolong engagement

The interface has one primary action: ask a question about the remembered business.

## Clarity over completeness

Barni should answer the most useful supported interpretation first. It should not dump every related metric, invoice, supplier, or product into the response.

A strong answer generally contains:

1. One direct conclusion
2. The relevant period or comparison basis
3. A concise explanation
4. A collapsed evidence view
5. Up to three useful follow-up questions

## Silence and refusal are product features

When evidence is insufficient, Barni should say exactly what is missing.

Prefer:

> I do not have enough comparable price history to answer that yet.

Avoid:

> Prices appear to be increasing.

# User Experience

## Core flow

```text
User asks one question
→ Barni identifies the business intent
→ required facts are checked
→ trusted facts are retrieved
→ claims are verified against evidence
→ one answer is presented
→ user may inspect evidence or choose a useful follow-up
```

## Default state

Show one prominent input:

> Ask Barni about your business…

Below it, show a small number of contextual examples such as:

- What became more expensive?
- Show Tnuva history.
- What changed this month?

Examples are invitations, not filters. They disappear after a question is asked.

## Answer state

The answer replaces the examples and becomes the center of attention.

Structure:

**Direct answer**

> Olive oil increased 14.3% since the previous comparable purchase.

**Explanation**

> The normalized price moved from ₪42.00 to ₪48.00 per litre between invoices #826 and #841.

**Evidence** — collapsed by default

- Previous invoice
- Current invoice
- Exact observed and normalized values
- Comparison basis
- Trust or limitation explanation

**Suggested next questions**

- Show the two invoices.
- Did anything else increase from this supplier?
- What was the latest quantity purchased?

## Continuity without chat

Follow-up questions may reuse the active answer context, such as the selected supplier, product, or period. This context must be visible and removable:

> Looking at: Tnuva · July 2026

Barni must not depend on hidden conversational memory. Every follow-up request is converted into a complete structured query before execution.

The interface may retain the current question and answer while the user stays on the screen. It should not become an infinite transcript.

# Conversation Architecture

## 1. Question Request

Every request contains:

- Original user text
- User language
- Calling surface
- Explicit visible context
- Optional time context
- Optional canonical supplier or product context

The calling surface may be Search, Home, Business Memory, or Insights. It must not change the factual answer.

## 2. Intent Registry

The Intent Registry contains a finite set of supported business questions. Each intent defines:

- Intent ID
- Supported language patterns
- Required entities
- Required Business Fact types
- Minimum evidence policy
- Query executor
- Deterministic answer template
- Follow-up question rules
- Safe insufficiency response

Adding a language phrase does not add business capability. A new intent is supported only when its required trusted facts and evidence policy exist.

Initial intents:

- Price changes
- Supplier history
- Period comparison
- Spending explanation
- Unusual purchases
- Supplier attention
- Changes over time
- Invoice retrieval
- Product purchase history

## 3. Language and Entity Resolution

The resolver identifies:

- Intent
- Canonical supplier
- Canonical product
- Date or period
- Comparison period
- Requested direction, such as increases or decreases

Entity resolution must use the existing canonical Identity layer and confirmed aliases. Similar names that have not been confirmed must not be silently combined.

Hebrew and English are normal. The resolver should interpret both while preserving mixed-language supplier and product names. The answer should use the language of the question.

Ambiguity produces one short clarification:

> I know two products called “Cream.” Which one do you mean?

The clarification presents canonical choices with source context. It does not expose internal IDs or matching scores.

## 4. Fact Requirement Planner

After resolving intent and entities, the planner creates a structured requirement plan.

Example:

```text
Intent: price_changes
Period: since previous purchase
Required facts:
  - two TRUSTED comparable price facts
  - same canonical product
  - compatible normalized unit
  - compatible VAT basis
  - same currency
Required evidence:
  - current invoice and line
  - previous invoice and line
```

The planner never falls back to raw invoice fields when a required Business Fact is unavailable.

## 5. Trusted Fact Retrieval

Facts are retrieved from shared services:

- Comparable Price Ledger
- Canonical Business Identity repository
- Business Memory
- Identity Review queue
- Shared invoice workflow status
- Business Story Engine
- Future typed fact ledgers

The Conversation Layer does not normalize units, calculate comparability, infer aliases, detect duplicates, or recreate insight rules.

## 6. Answer Claims

The engine builds structured claims before producing language.

Each claim contains:

- Subject
- Predicate
- Value
- Unit
- Time or period
- Comparison basis
- Fact IDs
- Source record IDs
- Trust status
- Evidence completeness

Only verified claims may enter an answer sentence.

## 7. Deterministic Answer Composer

The initial implementation should use controlled, bilingual answer templates. Templates transform verified claims into Barni's voice but cannot add facts.

An optional language model may later help classify phrasing or improve fluency, but only under a constrained contract:

- It receives structured claims, never unrestricted database content.
- It may not introduce a number, entity, relationship, cause, or recommendation absent from those claims.
- Its output is checked against the claim set before display.
- A deterministic template remains the fallback.

AI is not required for the first implementation.

## 8. Evidence Verifier

Before an answer is returned, the verifier confirms:

- Every factual sentence maps to at least one structured claim.
- Every claim references an allowed trusted fact or confirmed memory record.
- Every meaningful claim has source evidence.
- Comparison claims use compatible fact bases.
- Source invoices exist and are accessible.
- Recommendations do not exceed the evidence.

If verification fails, the answer is blocked and replaced with a calm insufficiency response.

## 9. Follow-up Generator

Follow-up questions come from the resolved intent and available evidence. They are not freely generated conversation prompts.

Rules:

- Maximum three
- Each question must be answerable or clearly lead to useful evidence
- Preserve visible entity and period context
- Prefer evidence, explanation, or a proportionate next action
- Never suggest an unsupported comparison

# Answer Contract

Every answer returns a UI-independent object:

```text
ConversationAnswer
  question
  normalized_intent
  direct_answer
  explanation
  confidence
  business_facts_required
  claims
  evidence
  source_invoices
  suggested_follow_ups
  recommended_action (optional)
  insufficiency_reason (optional)
  language
```

Every answer must define the following.

## User question

The original question and the normalized business intent.

## Business facts required

The precise fact types and minimum history required for the answer.

## Evidence chain

The links from answer claims through canonical identities and facts to original source records.

## Confidence

Confidence describes whether the factual requirements were satisfied. It is not conversational confidence or model confidence.

## Source invoices

Every invoice supporting the answer, including the relevant invoice lines where applicable.

## Suggested follow-up questions

Up to three useful questions supported by the active context.

# Trust Model

## Confidence levels

Customer-facing confidence should use qualitative states:

### Supported

All required facts are trusted, compatible, and linked to complete evidence.

Customer language:

> Based on two comparable purchases.

### Limited

The answer can state a narrow fact, but the broader requested conclusion is not supported.

Customer language:

> I can show the latest purchase, but I do not have enough comparable history to explain a trend.

### Unresolved

Identity, unit, package, VAT, currency, or another required basis is in conflict.

Customer language:

> I need your help confirming one product detail before I can compare these purchases.

### Unsupported

The required fact type, history, or source evidence does not exist.

Customer language:

> I do not know that yet.

Raw confidence percentages remain internal except inside the explicit Identity Review experience.

## Recommendation policy

A recommendation is allowed only when:

- The underlying answer is Supported.
- A useful action is proportionate to the evidence.
- The action does not imply an unsupported cause or alternative.

Allowed:

> This price increased 18%. You may want to review it with the supplier.

Not allowed:

> Switch suppliers.

The second statement requires trusted cross-supplier comparison and business context that may not exist.

## Cause policy

Barni must distinguish correlation from explanation.

“Why did spending increase?” cannot be answered merely because spending rose. Barni needs trusted contribution facts showing which suppliers, products, quantities, or prices explain the difference.

If those facts do not exist:

> Spending increased, but I cannot reliably explain why yet. I need trusted period and purchase-contribution facts.

# Initial Question Specifications

## What became more expensive?

### User question

> What became more expensive?

### Business facts required

- At least two trusted Comparable Price Facts per product
- Same canonical product
- Compatible normalized unit, package basis, VAT basis, and currency
- Previous and current observation dates
- A defined materiality threshold

### Evidence chain

```text
Price-change claim
→ Comparable Price Ledger comparison
→ current and previous price facts
→ canonical product and supplier
→ invoice-line IDs
→ source invoices
```

### Confidence

Supported only for products whose comparisons are trusted. Products with unresolved units or identities are excluded and may be summarized separately as a coverage limitation.

### Source invoices

Both invoices for every surfaced price movement.

### Suggested follow-up questions

- Show the largest increase.
- Did anything decrease?
- Show the supporting invoices.

## Why did spending increase?

### User question

> Why did spending increase?

### Business facts required

- Trusted period-spend facts for both periods
- Consistent document inclusion policy
- Canonical supplier and product contributions
- Trusted quantity and price components when attributing a cause
- Credit-note treatment

### Evidence chain

```text
Period difference
→ trusted spend facts
→ supported supplier/product contribution facts
→ included transactions or invoices
→ source documents
```

### Confidence

Not supported by the current Comparable Price Ledger alone. This intent must remain unavailable until trusted period-spend and contribution facts exist.

### Source invoices

All evidence contributing materially to the stated difference, with a visible inclusion policy.

### Suggested follow-up questions

- Compare the two periods.
- Which suppliers contributed most?
- Show the included invoices.

## Show supplier history

### User question

> Show Tnuva history.

### Business facts required

- One confirmed canonical supplier
- Approved invoices linked to that supplier
- Trusted price facts where price history is shown
- First and last observed dates

### Evidence chain

```text
Canonical supplier
→ confirmed aliases and invoice links
→ dated approved invoices
→ trusted price facts where applicable
→ source documents
```

### Confidence

Supported when supplier identity is canonical. Ambiguous supplier aliases require clarification or Identity Review.

### Source invoices

The invoices included in the requested period, ordered by date.

### Suggested follow-up questions

- What did I buy most recently from Tnuva?
- Which Tnuva prices changed?
- Show the latest invoice.

## Compare months

### User question

> Compare June and July.

### Business facts required

- Trusted period-spend facts
- Same inclusion and credit-note policy for both months
- Currency and VAT basis policy
- Supported supplier or product contributions when explaining differences

### Evidence chain

```text
Monthly comparison
→ two trusted period facts
→ included approved evidence
→ source invoices or transactions
```

### Confidence

Not supported until period facts exist. Raw totals must not be promoted directly into the Conversation Layer as trusted comparisons.

### Source invoices

Every included source record, with totals reconciling to each period fact.

### Suggested follow-up questions

- Which suppliers changed most?
- Which products explain the difference?
- Show July invoices.

## Find unusual purchases

### User question

> Find unusual purchases.

### Business facts required

- A trusted purchase fact model
- Sufficient comparable history
- Explicit unusualness policy
- Compatible document types, suppliers, currencies, and totals
- Source evidence for the baseline and current purchase

### Evidence chain

```text
Unusual-purchase claim
→ trusted purchase observation
→ trusted historical baseline
→ unusualness rule and threshold
→ source invoices
```

### Confidence

The existing invoice insight rule may inform future design, but the Conversation Layer should not expose this intent until unusual-purchase conclusions consume trusted Business Facts rather than raw totals.

### Source invoices

The current purchase and the historical records forming its baseline.

### Suggested follow-up questions

- Why is this purchase unusual?
- Show the comparison history.
- Does it need my attention?

## Which suppliers need attention?

### User question

> Which suppliers need attention?

### Business facts required

- Canonical suppliers
- Trusted price, duplicate, inactivity, dependency, or unresolved-evidence facts
- Explicit attention policy
- No unsupported supplier ranking

### Evidence chain

```text
Attention reason
→ supported story or trusted supplier-related fact
→ canonical supplier
→ triggering evidence
→ source invoices
```

### Confidence

Only suppliers with a concrete supported reason appear. A supplier is not labeled problematic merely because it has high spend or many invoices.

### Source invoices

The invoices supporting each specific reason for attention.

### Suggested follow-up questions

- Why does this supplier need attention?
- Show its recent price changes.
- Show unresolved identity details.

## What changed since last month?

### User question

> What changed since last month?

### Business facts required

- A defined current and previous period
- Trusted Business Stories generated from facts in both periods
- Supported price, supplier, product, review, and future spend facts
- Clear coverage disclosure

### Evidence chain

```text
Change summary
→ ranked Business Stories
→ trusted facts or explicit memory events
→ canonical identities
→ source invoices
```

### Confidence

Each included change carries its own confidence. Unsupported categories are omitted rather than inferred. The answer must disclose when only part of the requested business picture is covered.

### Source invoices

The source invoices attached to every included Business Story.

### Suggested follow-up questions

- Show the biggest price change.
- What still needs review?
- Compare the two months when spending facts are ready.

# Reusable Components

## ConversationEngine

Coordinates intent resolution, fact planning, retrieval, verification, composition, and follow-up selection. It returns structured answer objects and never renders UI.

## IntentDefinition

A declarative contract for one supported question type, including required facts, evidence policy, executor, templates, and insufficiency language.

## QuestionInterpreter

Maps Hebrew or English text to a supported intent and explicit entities. It cannot answer questions.

## ConversationContext

Carries visible supplier, product, period, language, and surface context. Context is explicit and serializable.

## FactRequirementPlan

Describes exactly which trusted facts and evidence must exist before an answer may be composed.

## Claim

Represents one atomic factual statement with its values, units, dates, fact IDs, and evidence.

## EvidenceVerifier

Blocks claims that lack trusted facts, compatible bases, or reachable source evidence.

## ConversationAnswer

The channel-independent response consumed by Search, Home, Business Memory, Insights, and future experiences.

## EvidenceDrawer

A shared, progressively disclosed component showing claim values and source invoices without exposing database terminology.

## FollowUpSuggestions

A shared component rendering no more than three context-aware, answerable next questions.

## ConversationInput

One consistent input and submit action. It adapts in size by surface but preserves the same behavior and supported intent registry.

# Surface Integration

## Search

Search is the primary Conversation Layer surface.

The input accepts direct questions and ordinary search terms. Question intents return an answer card. Retrieval intents continue returning grouped Search results. Opening evidence replaces results with the existing detail view.

Search should never show a conversational transcript. Returning to Search restores the last question and answer for the current session.

## Home

Home offers a compact “Ask Barni” input. The answer appears in place and may link to Search for deeper evidence exploration.

Home should favor questions about today and recent Business Stories. It must not create a second answer engine.

## Business Memory

Business Memory supplies visible entity context.

On a supplier detail:

> Ask about Tnuva…

On a product detail:

> Ask about olive oil…

The canonical entity is visible and passed explicitly to the same Conversation Engine.

## Insights

Insights supplies a time and change context. Questions should begin from a displayed Business Story or supported period.

Examples:

- Why does this matter?
- Show the evidence.
- What else changed in this period?

Insights must not calculate a separate answer from its charts.

# Prioritization and Answer Length

Answers should rank information by:

1. Required user attention
2. Financial impact supported by trusted facts
3. Meaningful change
4. Evidence quality
5. Recency

Default limits:

- One direct conclusion
- Up to three supporting claims
- Up to three follow-up questions
- Evidence collapsed by default
- No more than five surfaced source invoices before “Show all”

# Privacy and Safety Boundaries

The Conversation Layer answers only from the active business's permitted memory.

It must not:

- Mix evidence across businesses
- Reveal internal database paths
- Expose technical confidence or rule IDs
- Answer legal, tax, or accounting questions as professional advice
- Perform consequential external actions without explicit approval
- Treat an unsupported question as permission to search external sources

# Implementation Roadmap

## Phase 0 — Contracts and evaluation set

- Define `ConversationAnswer`, `Claim`, `FactRequirementPlan`, and evidence contracts.
- Create a bilingual evaluation set from real restaurant-owner questions.
- Label each question as supported, limited, unresolved, or unsupported using current facts.
- Establish the rule that no answer ships without source evidence.

Success gate: the system can explain why every evaluation question can or cannot be answered.

## Phase 1 — Deterministic trusted intents

Implement only intents fully supported today:

- What became more expensive?
- Show supplier history.
- Show product purchase history.
- Show invoices from a period.
- What identity details need review?
- What changed based on existing Business Stories?

Use deterministic bilingual patterns and templates. Integrate first in Search.

Success gate: every answer reconciles to trusted facts and opens its source invoices.

## Phase 2 — Shared surface integration

- Reuse the same ConversationInput, AnswerCard, EvidenceDrawer, and FollowUpSuggestions on Home, Business Memory, and Insights.
- Make entity and period context visible.
- Preserve one answer contract across all surfaces.

Success gate: the same question and context return the same claims and evidence everywhere.

## Phase 3 — Trusted spend and period facts

- Extend the Business Facts Engine with period-spend facts.
- Define document inclusion, credit-note, currency, and VAT policies.
- Add contribution facts for suppliers and products.
- Enable month comparison and supported spending explanations.

Success gate: every period total reconciles to its included evidence and every explanation reconciles to contribution facts.

## Phase 4 — Trusted behavior facts

- Add purchase-baseline and unusual-purchase facts.
- Add supplier-attention facts with explicit reason policies.
- Add inactivity and dependency facts only when history is sufficient.

Success gate: weak baselines remain silent and no supplier is ranked or labeled without a supported reason.

## Phase 5 — Constrained language interpretation

- Expand Hebrew and English phrasing coverage.
- Evaluate whether a constrained language model materially improves intent recognition.
- Keep deterministic plans, claims, verification, and answer fallback.
- Add adversarial tests for fabricated numbers, causes, entities, and recommendations.

Success gate: language flexibility increases without changing factual answers or weakening evidence requirements.

## Phase 6 — Durable continuity and future channels

- Add a durable, user-specific “last checked” checkpoint.
- Support morning briefings and future notifications using the same answers and Business Stories.
- Add permission-aware context for teams.
- Measure which questions resolve real owner decisions.

Success gate: continuity remains explicit, quiet, reversible, and consistent across surfaces.

# Evaluation and Definition of Done

The Conversation Layer is ready only when:

- Every answer is represented as structured claims before language generation.
- Every factual claim links to trusted facts or confirmed canonical memory.
- Every meaningful claim opens supporting evidence.
- Unsupported causes and recommendations are blocked.
- Hebrew and English questions preserve the same fact requirements.
- The same question returns the same claims across Search, Home, Business Memory, and Insights.
- Ambiguous entities produce a concise clarification.
- Insufficient evidence produces calm, specific language.
- No customer UI exposes rule IDs, database terms, or raw confidence percentages.
- The experience remains one answer at a time rather than becoming an endless chat.

# Golden Rule

Conversation does not give Barni permission to guess.

It gives the user a simpler way to reach what Barni can prove.
