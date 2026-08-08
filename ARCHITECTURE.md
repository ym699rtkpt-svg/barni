# Barni Architecture Blueprint

## Purpose

This document defines the long-term architecture of Barni as a modular AI business platform for restaurants. It is the target blueprint for developers, designers, and future contributors.

It does not claim that the current codebase already follows every boundary described here. Barni should move toward this architecture incrementally, with small, testable changes that preserve existing functionality and every stored record.

# Philosophy

Barni is a Business Memory.

Everything else is built on top of that.

Invoices, recipes, supplier conversations, product prices, corrections, and business decisions are learning events. Barni turns those events into durable, traceable knowledge. Intelligence is produced from that knowledge. Recommendations are produced from supported intelligence. Actions are taken only through explicit workflows.

Barni is not an OCR product with dashboards attached. OCR is one input. Barni is not accounting software. Accounting is one possible consumer of approved business facts. The platform exists to help restaurant owners save time, save money, reduce stress, and make better decisions.

The architecture must protect that promise:

- Memory before intelligence.
- Evidence before conclusions.
- Explanation before recommendation.
- Human approval before consequential action.
- Reliability before novelty.
- Simplicity before infrastructure.

# Core Engine

```text
Business Memory
      ↓
Knowledge Engine
      ↓
Business Intelligence
      ↓
Recommendations
      ↓
Actions
```

## Business Memory

Business Memory is the durable foundation. It stores approved facts, their source records, original values, normalized identities, history, and uncertainty. It answers: **What does Barni know, and where did it learn it?**

Business Memory must be auditable. An important fact should be traceable to an invoice, recipe, user correction, or another approved source. Missing data must remain missing; it must never be silently converted into invented knowledge.

## Knowledge Engine

The Knowledge Engine turns approved events into connected knowledge. It identifies suppliers and products conservatively, records price points, maintains histories, and updates coverage metrics. It answers: **How do these approved facts relate over time?**

The Knowledge Engine is the source of truth for learned business knowledge. It is not the source of truth for raw OCR candidates or unapproved uploads.

## Business Intelligence

Business Intelligence applies explainable rules to Business Memory. It produces facts, comparisons, and trends only when sufficient comparable evidence exists. It answers: **What changed, and what deserves attention?**

Intelligence results must include evidence, limitations, and source references. The same calculation must serve Home, Knowledge, Reports, Notifications, and AI Chat.

## Recommendations

Recommendations translate supported intelligence into conservative next steps. They answer: **What could the restaurant manager consider doing?**

A recommendation should contain the observation, current and reference values when available, the difference, the evidence boundary, and one suggested action. It must never introduce a claim that the intelligence did not establish.

## Actions

Actions are explicit workflows initiated or approved by a person or a defined policy. Examples include approving an invoice, replacing a duplicate, exporting a report, sending a notification, or accepting a product match.

Actions must be authorized, idempotent where practical, logged, and reversible when feasible. Recommendations do not execute themselves.

# Platform Layers

```text
Presentation
    ↓
Application Workflows
    ↓
Domain Modules and Business Services
    ↓
Knowledge and Repository Interfaces
    ↓
Data and External Provider Adapters
```

## Presentation

Streamlit pages and reusable UI components render results, collect input, and communicate progress. They own visual hierarchy, formatting, accessibility, and interaction state.

Presentation does not own SQL, business calculations, product matching, duplicate rules, recommendation thresholds, or OCR orchestration.

## Application Workflows

Application services coordinate complete user intentions such as Upload Invoice, Review Invoice, Resolve Duplicate, Search Memory, Generate Report, or Send Notification. They own workflow sequencing, permissions, transaction boundaries, and explicit outcomes.

They call domain services; they do not duplicate domain rules.

## Domain Modules and Business Services

Domain modules own Barni's reusable rules. They operate on domain records and repository interfaces rather than Streamlit state or SQLite rows. Their results should be deterministic, evidence-bearing, and independently testable.

## Knowledge and Repository Interfaces

This boundary defines how business services read and write durable knowledge. Interfaces isolate the domain from the current storage engine and make unit testing possible without the production database.

## Data and External Provider Adapters

Adapters implement repositories, file archives, OCR providers, AI providers, notification channels, and exports. SQLite is the primary database today. A future database should replace an adapter, not require rewriting intelligence or UI pages.

# Modules

Each module has one clear owner and a narrow public contract. Modules communicate through service interfaces, typed results, identifiers, and domain events—not by importing each other's internal implementation.

## OCR Engine

### Purpose

Convert PDFs, images, and supported documents into structured extraction candidates without claiming that extracted data is approved truth.

### Inputs

- Uploaded document and file metadata.
- Extraction schema and prompt version.
- OCR or AI provider configuration.
- Locale and document-language context.

### Outputs

- Candidate invoice fields and line items.
- Raw provider response reference where retention is permitted.
- Provider-supplied confidence values, if available.
- Extraction warnings, method, and provenance metadata.

### Dependencies

- File-storage adapter.
- OCR and AI provider adapters.
- Shared extraction contracts.
- No dependency on Streamlit, intelligence modules, or the production database implementation.

### Future expansion

- Multiple OCR providers behind one interface.
- Provider comparison and fallback.
- Page- and field-level confidence when genuinely supplied.
- Language and document-type specialization.
- Evaluation datasets based on approved corrections.

## Invoice Processing

### Purpose

Coordinate the trusted journey from upload to approved, archived invoice.

### Inputs

- Uploaded file.
- OCR extraction candidate.
- Normalization and validation rules.
- Human corrections and duplicate decisions.

### Outputs

- Review-queue record.
- Validation issues and review status.
- Explicit duplicate-resolution outcome.
- Approved invoice and `InvoiceApproved` event, or a rejected/skipped outcome.

### Dependencies

- OCR Engine.
- Invoice repository and archive adapter.
- Validation and line-classification services.
- Knowledge Engine through events after successful approval.

### Future expansion

- Background processing and resumable jobs.
- Configurable approval roles.
- Batch review tools.
- Stronger idempotency and recovery.
- Correction history usable for extraction evaluation.

## Knowledge Engine

### Purpose

Transform approved business events into durable, connected Business Memory.

### Inputs

- Approved invoice, recipe, correction, and business events.
- Existing supplier, product, category, and price identities.
- Explicit user-confirmed matches and corrections.

### Outputs

- Updated supplier and product knowledge.
- Purchase and price histories.
- Learning events and coverage metadata.
- Traceable relationships back to sources.

### Dependencies

- Business Memory repositories.
- Identity-resolution policies.
- Product-line classifier.
- Domain event contracts.

### Future expansion

- Idempotent event replay.
- Versioned identity resolution.
- Multi-location knowledge boundaries.
- Conflict detection and merge review.
- Broader operational event types beyond invoices.

## Supplier Intelligence

### Purpose

Explain supplier purchasing history, price movement, spend, and supported changes.

### Inputs

- Approved supplier invoices.
- Valid product purchases and quantities.
- Supplier identity and time period.
- Comparable price-history results.

### Outputs

- Supplier facts, trends, and evidence references.
- Counts of increases, decreases, and stable products.
- Supported extra-cost and savings calculations.
- Supplier-level attention items.

### Dependencies

- Business Memory.
- Product Intelligence for shared price comparisons.
- Cost and Purchasing Intelligence where relevant.
- No dependency on UI or Notifications.

### Future expansion

- Supplier reliability history.
- Contract and term tracking.
- Comparable cross-supplier analysis with unit normalization.
- Supplier meeting briefs.
- Multi-period purchasing summaries.

## Product Intelligence

### Purpose

Explain what the restaurant buys, how often it buys it, and how valid comparable prices change over time.

### Inputs

- Approved product lines only.
- Product identity and original descriptions.
- Quantity, unit, unit price, supplier, and purchase date.
- Product and unit compatibility rules.

### Outputs

- Purchase count and quantity history.
- Latest and previous valid price.
- Monetary and percentage change.
- Trend status, evidence, and insufficient-history result.

### Dependencies

- Business Memory.
- Shared product-line classifier.
- Product identity and unit-normalization services.
- Invoice repository source references.

### Future expansion

- Human-reviewed product matching.
- Pack-size and unit conversions.
- Comparable supplier prices.
- Seasonality and volatility analysis.
- Product substitution evidence.

## Recipe Intelligence

### Purpose

Connect recipes to validated product costs and explain dish economics.

### Inputs

- Recipe ingredients, quantities, units, yield, and portions.
- Product matches and latest valid costs.
- Waste or yield assumptions explicitly configured by the user.

### Outputs

- Ingredient and recipe cost.
- Cost per portion.
- Missing-price, stale-price, and ambiguous-unit warnings.
- Explainable profitability inputs.

### Dependencies

- Business Memory.
- Product Intelligence.
- Cost Intelligence.
- Unit-normalization service.

### Future expansion

- Menu price and margin analysis.
- Recipe versions and seasonal menus.
- Waste and preparation yields.
- Suggested costing reviews after material price changes.
- Location-specific recipe costs.

## Cost Intelligence

### Purpose

Provide reusable, explainable cost calculations across purchasing, products, recipes, and reports.

### Inputs

- Valid prices, quantities, units, taxes, yields, and time periods.
- Explicit reference values and calculation policy.
- Data-quality and comparability metadata.

### Outputs

- Monetary differences and cost breakdowns.
- Supported savings or extra-cost results.
- Cost coverage and limitation messages.
- Calculation evidence and formula metadata.

### Dependencies

- Business Memory.
- Unit and currency policies.
- Product-line classification.
- No dependency on presentation wording.

### Future expansion

- Cost allocation.
- Inflation-aware comparisons.
- Waste and yield models.
- Location and category cost views.
- Explainable scenario planning.

## Purchasing Intelligence

### Purpose

Help restaurant managers understand buying behavior and prepare practical purchasing decisions.

### Inputs

- Supplier, product, quantity, cost, frequency, and date histories.
- Supported Supplier, Product, and Cost Intelligence results.
- Explicit purchasing policies and thresholds.

### Outputs

- Purchasing changes that deserve attention.
- Negotiation and monitoring candidates.
- Order-history context.
- Conservative purchasing recommendations with evidence.

### Dependencies

- Supplier Intelligence.
- Product Intelligence.
- Cost Intelligence.
- Recommendations module.

### Future expansion

- Order planning.
- Contract renewal preparation.
- Purchasing consolidation analysis.
- Stock-aware recommendations when inventory data exists.
- Approval workflows for planned purchases.

## Business Intelligence

### Purpose

Combine domain intelligence into a coherent view of the restaurant's current operating state.

### Inputs

- Evidence-bearing results from supplier, product, recipe, cost, and purchasing modules.
- Approved Business Memory facts.
- Time period and restaurant context.

### Outputs

- Facts, trends, alerts, and business summaries.
- Clear evidence and uncertainty boundaries.
- Reusable results for Home, Reports, Notifications, and AI Chat.

### Dependencies

- Domain intelligence modules.
- Business Memory.
- Shared definitions for facts, trends, and alerts.
- No dependency on Streamlit components.

### Future expansion

- Cross-domain operational briefs.
- Explainable forecasting when enough history exists.
- Multi-location comparisons.
- Defined benchmarking with appropriate comparable evidence.
- Event-driven intelligence refresh.

## Recommendations

### Purpose

Convert supported intelligence into one clear, conservative next step.

### Inputs

- Facts and trends with evidence.
- Versioned recommendation policies.
- User preferences and explicit business thresholds.

### Outputs

- Recommendation type and priority.
- Explanation, reference values, and suggested action.
- Source identifiers and limitations.
- “No action recommended” when no rule is satisfied.

### Dependencies

- Business Intelligence and domain intelligence results.
- Policy configuration.
- Business Memory source references.
- No direct database queries or independent price calculations.

### Future expansion

- User feedback on recommendation usefulness.
- Policy tuning by restaurant.
- Recommendation lifecycle and resolution tracking.
- Carefully governed action proposals.
- Cross-module recommendation prioritization.

## Search Engine

### Purpose

Find trusted information across Barni quickly and consistently.

### Inputs

- Search text, dates, entities, filters, and restaurant scope.
- Searchable Business Memory records.
- Access permissions.

### Outputs

- Grouped invoice, supplier, product, recipe, and knowledge results.
- Ranking metadata and direct source references.
- Empty or ambiguous-result guidance.

### Dependencies

- Repository search interfaces.
- Business Memory identities.
- Authorization context when multi-user support exists.
- Presentation owns result layout, not retrieval rules.

### Future expansion

- Full-text indexing when scale requires it.
- Semantic retrieval with source citations.
- Saved searches.
- Natural-language query interpretation.
- Cross-location search with permissions.

## Reports

### Purpose

Produce repeatable, auditable operational summaries and exports.

### Inputs

- Approved facts and intelligence results.
- Period, filters, grouping, currency, and report definition.
- Restaurant identity and permissions.

### Outputs

- Structured report data.
- Human-readable and export formats.
- Totals, limitations, and source references.
- Report-generation audit metadata.

### Dependencies

- Business Intelligence.
- Domain services and repositories.
- Export adapters.
- Shared formatting policies outside calculation logic.

### Future expansion

- Scheduled reports.
- Custom report definitions.
- Multi-location reporting.
- Accountant-ready export packages.
- Report snapshots for historical reproducibility.

## Accountant

### Purpose

Make approved restaurant records easier to review and share with accounting professionals without turning Barni into accounting software.

### Inputs

- Approved invoices, classifications, tax fields, and source files.
- Reporting period and accountant requirements.
- Explicit compliance rules from authoritative sources.

### Outputs

- Reconciliation views and export packages.
- Missing-document and data-quality notices.
- Source-linked summaries.
- Clear statement of what Barni did and did not validate.

### Dependencies

- Invoice Processing records.
- Reports.
- Business Memory.
- Export adapters.

### Future expansion

- Accounting-system integrations.
- Accountant collaboration and comments.
- Reconciliation status.
- Configurable tax-jurisdiction adapters.
- Period-closing workflows with explicit approval.

## Notifications

### Purpose

Deliver important, supported information through user-approved channels without creating noise.

### Inputs

- Recommendation or operational events.
- Notification preferences, severity, schedule, and recipient permissions.
- Deduplication and quiet-hour policy.

### Outputs

- In-app, email, or messaging notifications.
- Delivery status and audit record.
- Deferred, grouped, or suppressed outcome.

### Dependencies

- Recommendations and Application workflows.
- Settings.
- Channel adapters.
- No independent intelligence calculations.

### Future expansion

- Daily and weekly briefings.
- Escalation policies.
- Team routing.
- Interactive notification actions with confirmation.
- Delivery analytics focused on usefulness rather than engagement.

## Settings

### Purpose

Manage restaurant configuration, user preferences, permissions, and integration choices.

### Inputs

- Restaurant identity and locale.
- User preferences and roles.
- Explicit thresholds, notification rules, and integration credentials.

### Outputs

- Versioned configuration available through a settings service.
- Validated preference changes.
- Audit records for consequential configuration changes.

### Dependencies

- Settings repository.
- Secret-storage adapter.
- Authorization service when multiple users exist.
- No hidden ownership of business rules.

### Future expansion

- Multi-location configuration inheritance.
- Role-based permissions.
- Feature flags for pilots.
- Integration management.
- Data retention and privacy controls.

## AI Chat

### Purpose

Provide a conversational interface to Barni's approved memory, intelligence, and workflows.

### Inputs

- User question and conversation context.
- Retrieved Business Memory evidence.
- Narrow, permission-aware service tools.
- Restaurant and user scope.

### Outputs

- Concise answers grounded in stored data.
- Source references and uncertainty statements.
- Proposed actions that require confirmation.
- Clarifying questions when evidence or intent is insufficient.

### Dependencies

- Search Engine.
- Business Intelligence.
- Recommendations.
- Application workflow interfaces and AI provider adapter.

### Future expansion

- Multilingual restaurant operations assistant.
- Voice interaction.
- Guided analysis and report creation.
- Permissioned workflow proposals.
- Evaluation and guardrails based on traceability and correctness.

## Business Memory

### Purpose

Provide the canonical, durable record of what Barni has learned and the evidence behind it.

### Inputs

- Approved domain events.
- Original source identifiers and normalized facts.
- Human corrections, merges, and explicit decisions.
- Provenance, timestamps, and real confidence metadata.

### Outputs

- Canonical suppliers, products, purchases, recipes, prices, and relationships.
- Historical events and source traceability.
- Coverage, freshness, and uncertainty information.
- Repository interfaces used by every intelligence module.

### Dependencies

- Domain models and event contracts.
- Repository and archive adapters.
- Migration, backup, and integrity services.
- It must not depend on UI, Recommendations, Notifications, or AI Chat.

### Future expansion

- Multi-restaurant tenant isolation.
- Versioned facts and temporal queries.
- Conflict resolution and knowledge merging.
- Broader operational memory beyond invoices.
- Governed data portability and deletion workflows.

# How Modules Communicate

## Commands, queries, and events

- **Commands** express an intention to change state, such as `ApproveInvoice` or `ReplaceDuplicateInvoice`.
- **Queries** request information without changing state, such as `GetProductPriceHistory`.
- **Events** record completed facts, such as `InvoiceApproved` or `PricePointRecorded`.

Expected flow:

```text
User
  → UI
  → Application command or query
  → Domain service
  → Repository/provider interface
  → Adapter
  → Structured result or domain event
  → UI
```

Events allow modules to learn from completed changes without importing one another's internals. They should contain stable identifiers and essential facts, not Streamlit session state or uncontrolled database rows.

## Contracts

Module contracts should use explicit domain models and result objects. Expected decisions—duplicate detected, review required, insufficient data, skipped, rejected—are structured outcomes, not generic exceptions.

Important intelligence results should carry:

- Fact, trend, or recommendation type.
- Current value and reference value when available.
- Calculation or rule identifier.
- Source invoice or record identifiers.
- Data-quality and uncertainty information.

## Dependency direction

- UI depends on Application interfaces.
- Application workflows coordinate domain modules.
- Intelligence modules depend on Business Memory interfaces.
- Data and external adapters implement interfaces defined above them.
- Business Memory never imports Streamlit, recommendations, notifications, or AI Chat.
- Provider SDKs never define Barni's domain models.

Mutual imports between modules are a design warning. Shared contracts belong in a small domain package, not a generic utility dumping ground.

# Architecture Principles

1. **Business logic never belongs inside Streamlit pages.** Pages collect input, invoke a workflow, and render its result.
2. **UI only renders.** Formatting and interaction are UI concerns; facts, trends, and recommendations are not.
3. **Database access goes through reusable services and repositories.** Pages and business rules never open direct connections.
4. **The Knowledge Engine is the source of truth for learned knowledge.** Raw OCR remains a candidate until approval.
5. **Business Memory is foundational.** Intelligence, recommendations, chat, reports, and notifications read from the same approved memory.
6. **Avoid duplicated calculations.** A rule has one owner and serves every consumer.
7. **Prefer reusable services.** Shared capabilities are exposed through narrow, documented contracts.
8. **Keep modules loosely coupled.** Communicate through interfaces, results, and events rather than internal imports.
9. **Dependencies flow in one direction.** Lower layers never depend on delivery or presentation layers.
10. **Every feature is modular.** It has a clear purpose, owner, inputs, outputs, and boundaries.
11. **Every feature is testable.** Core behavior runs without Streamlit, external AI, or the live database.
12. **Preserve auditability.** Important facts, recommendations, and mutations remain traceable to their sources and decisions.
13. **Represent uncertainty explicitly.** Missing history is not zero, and unavailable confidence is not a score.
14. **Never invent business conclusions.** Intelligence is constrained by stored, comparable evidence.
15. **Actions require authority.** AI may propose; consequential mutations require explicit policy or human confirmation.
16. **Migrations protect data.** Back up, migrate transactionally, verify counts and integrity, and preserve backward compatibility.
17. **External systems are adapters.** OCR, AI, messaging, accounting, storage, and databases remain replaceable.
18. **Avoid unnecessary dependencies.** Add infrastructure only for a demonstrated product or operational need.
19. **Security and privacy are defaults.** Minimize data exposure, isolate restaurants, protect secrets, and redact diagnostics.
20. **Observability never becomes user friction.** Log important failures safely and show calm, useful recovery guidance.

# Testing and Reliability

## Unit tests

Test normalization, classification, product matching, price comparison, recipe cost, intelligence, recommendation, and uncertainty rules without Streamlit or the live database.

## Workflow tests

Test upload, review, approval, rejection, duplicate resolution, learning, reports, and notification decisions using temporary repositories and files.

## Repository tests

Test migrations, transactions, backups, row mapping, constraints, foreign keys, and integrity against isolated databases or verified copies.

## Contract tests

Ensure OCR, AI, storage, notification, accounting, and database adapters meet stable platform contracts.

## UI tests

Test the critical five-second question, primary action, empty states, uncertainty, and successful workflow completion. Do not rely only on screenshots.

## End-to-end tests

Verify the complete path:

```text
Upload
  → Extract
  → Review
  → Approve
  → Learn
  → Search
  → Explain
  → Recommend
  → Confirm action
```

# Data and Scale

SQLite is appropriate while Barni serves local and small-scale restaurant installations. It is inspectable, portable, and reliable with disciplined transactions, migrations, backups, and integrity checks.

Barni should move to a managed relational database only when concurrent users, multiple restaurants, remote availability, or operational scale demonstrate the need. Repository interfaces must make that a Data Layer change rather than a product rewrite.

Before multi-restaurant deployment, durable records must have explicit restaurant ownership, permissions must be enforced at service boundaries, and diagnostics must avoid cross-tenant data exposure.

Search indexes, background workers, queues, caches, object storage, and event infrastructure should be introduced independently when measured needs justify them. The target is modularity, not premature distribution.

# Evolution Path

1. Protect existing behavior and data with tests.
2. Identify duplicated rules and assign each rule one module owner.
3. Move direct database access out of Streamlit pages into repositories and services.
4. Extract user journeys into Application workflows.
5. Replace page calculations with evidence-bearing Business Intelligence results.
6. Strengthen Business Memory identities, provenance, events, and uncertainty.
7. Add provider adapters and infrastructure only when real usage requires them.

This is an incremental evolution. Large rewrites are not the goal. Each architectural step must be modular, reviewable, backward-compatible, and verifiable against existing restaurant data.

# 5-Year Vision

In five years, Barni could become a complete Restaurant Operating System built around a trusted Business Memory.

Barni could understand each restaurant's suppliers, products, invoices, recipes, prices, purchasing rhythms, costs, operational decisions, and team context. It could connect everyday activity into a durable history that makes the business easier to run and less dependent on information held in one person's memory.

The platform could provide:

- A trusted operational cockpit for owners and managers.
- Evidence-based supplier and purchasing preparation.
- Continuously updated recipe and menu economics.
- Calm alerts when supported changes deserve attention.
- Search and AI Chat grounded in the restaurant's own approved records.
- Accountant-ready information without pretending to replace professional accounting.
- Permission-aware actions, reports, reminders, and collaboration.
- Multi-location intelligence with strict restaurant data isolation.
- Carefully governed integrations with inventory, point-of-sale, accounting, ordering, and communication systems.

Barni should not become a collection of disconnected tools. OCR, intelligence, chat, notifications, recipes, and reports should remain different views and capabilities built on one coherent Business Memory.

The technology may evolve beyond Streamlit and SQLite into multiple interfaces, managed infrastructure, background processing, and permissioned AI agents. The product promise must remain unchanged:

- Barni remembers reliably.
- Barni explains before recommending.
- Barni asks before acting.
- Barni never claims more than the evidence supports.
- Barni saves time, saves money, reduces stress, and improves confidence.

If Barni reaches that scale without losing its calm, simplicity, auditability, and human trust, it will feel less like software and more like an intelligent operations manager who truly understands the restaurant.
