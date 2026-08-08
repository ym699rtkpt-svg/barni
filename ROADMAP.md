# Barni Roadmap

This document is the single source of truth for Barni's product direction and delivery status. Developers, designers, and future contributors should keep it current as work is planned, completed, or intentionally deferred.

# Vision

Barni is not an invoice OCR tool.

Barni is an AI-powered Business Memory and Operations Assistant for restaurants. Every approved invoice teaches Barni about the restaurant's suppliers, products, prices, purchasing patterns, and operating costs. Barni turns that stored history into clear context and conservative, traceable guidance.

**Mission:** Help restaurant owners save time, save money, and make better decisions.

---

# Product Principles

- Every feature must do at least one of the following:

  - Save time.
  - Save money.
  - Improve confidence.

- Simplicity over complexity.
- Reliability over novelty.
- Explain before recommending.
- Never invent business conclusions.
- Preserve existing data and working behavior.
- Make uncertainty visible when the stored data is insufficient.
- Keep important conclusions traceable to their source records.
- Design for a non-technical restaurant manager.

---

# Current Status

## Invoice Processing

- AI-assisted extraction for invoices and related supplier documents.
- Normalization and validation of invoice fields, VAT structure, totals, and line items.
- Human review before uncertain invoices enter Business Memory.
- Explicit duplicate handling: Replace, Skip, or Keep both.
- Data-preserving database migrations and invoice audit history.
- Product-line classification that excludes totals, VAT, payments, discounts, and notes from product analytics.

## Knowledge Engine

- Event-based learning after an invoice is approved.
- Stored supplier, product, pricing, and business-memory metrics.
- Business Memory page showing learned invoices, suppliers, products, price-history coverage, learning progress, and recent learning activity.
- Stored-data-first rules for facts, trends, and recommendations.

## Supplier Intelligence

- Supplier overview with invoice and purchase metrics.
- Grouped supplier product history.
- Price increases, decreases, and unchanged movements based on consecutive purchases.
- Potential extra-cost and savings summaries where quantity and price evidence are available.
- Natural-language insights and conservative purchasing recommendations.

## Product Intelligence

- Product purchase counts, quantities, and price summaries.
- Latest and previous price comparison.
- Price difference, percentage change, and trend status.
- Product detail view with price-history chart and source purchase table.
- Recommendations prioritized by supported price movement.

## Search

- Search across invoices, suppliers, product descriptions, invoice numbers, and dates.
- Grouped, compact results with direct access to invoice detail.
- Optional detailed filters for narrower searches.

## Home

- Premium business-cockpit hierarchy.
- Business Snapshot based on stored activity.
- Barni Today summaries based on available data.
- Ask Barni entry point.
- Quick Actions and Recent Activity.

## Upload

- Multi-file drag-and-drop upload.
- Visible reading, review, duplicate-check, saving, and learning progress.
- Review Queue with supplier, confidence, reason, and explicit decisions.
- OCR confidence shown from the existing extraction result.
- Supplier and product confidence shown as unavailable when the extractor does not provide them.
- Completion summaries describing what Business Memory learned.

## UI

- Warm beige and muted green visual identity.
- Premium card-based hierarchy on core screens.
- Calm empty states and concise, natural language.
- Consistent spacing, rounded surfaces, restrained colors, and human-friendly labels.
- Pilot Mode for feedback, debug export, current version, and local runtime-error logging.

---

# Current Sprint

## Sprint 1 — Trusted learning workflow

- [x] Redesign invoice upload as teaching Barni.
- [x] Create a Review Queue for uncertain invoices.
- [x] Require an explicit decision for suspected duplicates.
- [x] Expose available OCR confidence and highlight validation issues.
- [x] Add Pilot Mode for the first restaurant pilot.
- [ ] Complete manual browser testing of the full upload, review, duplicate, and feedback journeys.
- [ ] Record and triage feedback from the first restaurant.

---

# Next Sprint

## Pilot hardening

- Convert pilot findings into a prioritized issue list.
- Add automated end-to-end coverage for upload, review, duplicate resolution, and approval.
- Review runtime logs for recurring failures and address the highest-impact causes.
- Validate OCR confidence presentation with real pilot invoices.
- Review the debug export with the pilot operator and refine it without exposing business-sensitive data.
- Resolve remaining mixed-language and consistency issues in core workflows without changing business logic.

---

# Future Vision

## Phase 1 — Trustworthy Business Memory

- Complete the first-restaurant pilot and stabilize core workflows.
- Improve extraction quality using reviewed corrections as evidence.
- Strengthen source traceability from insights to invoices.
- Improve product identity and unit normalization while preserving original values.
- Establish reliable backup, recovery, and operational diagnostics.

## Phase 2 — Proactive Operations Assistant

- Cross-supplier comparisons only when products and units are genuinely comparable.
- Recurring purchasing-change summaries with clear supporting evidence.
- Review reminders and operational follow-ups based on explicit business rules.
- Recipe-cost and profitability workflows connected to validated product prices.
- Multi-location support with clear separation of restaurant data.

## Phase 3 — Restaurant Operations Intelligence

- Explainable forecasting based on sufficient historical data.
- Purchasing planning and supplier negotiation preparation.
- Broader operational memory across invoices, recipes, inventory, and recurring decisions.
- Role-aware collaboration for owners, managers, and operational teams.
- Integrations selected only when they reduce manual work and preserve auditability.

---

# Technical Debt

- Consolidate legacy and current upload/archive paths after compatibility is verified.
- Reduce top-level responsibilities in `app.py` and keep page routing separate from domain logic.
- Expand automated tests for migrations, database integrity, and approval workflows.
- Add automated Streamlit interaction tests for critical user journeys.
- Centralize shared UI tokens and reusable card components.
- Standardize Hebrew and English labels deliberately across each workflow.
- Define retention, redaction, and export policies for pilot feedback and runtime logs.
- Review remaining broad exception handlers and ensure important errors are logged without exposing sensitive data.
- Document recovery procedures for invoice archives and the primary database.

---

# Pilot Feedback

_No pilot notes recorded yet._

---

# Nice-to-have Ideas

- Configurable daily or weekly Barni briefing.
- Supplier meeting preparation view.
- Saved searches and pinned products.
- Lightweight annotations on invoices and insights.
- Exportable purchasing summaries.
- Accessibility and keyboard-navigation improvements.
- Optional notification channels for explicitly configured alerts.

Ideas in this section are not commitments. Move an idea into a sprint only after validating its user value, evidence requirements, and implementation cost.

---

# Changelog

## 2026-08 — Sprint 1: Trusted learning workflow

- Introduced the teaching-oriented Feed Barni workflow.
- Added Review Queue, confidence visibility, and field-level review cues.
- Added explicit Replace, Skip, and Keep both decisions for suspected duplicates.
- Added Pilot Mode, local feedback capture, privacy-conscious debug export, version display, and runtime-error logging.

## 2026-08 — Premium product foundation

- Established permanent engineering, design-system, business-intelligence, and product-vision guidance.
- Refined Home, Feed, Search, Knowledge, product history, supplier intelligence, and recommendations.
- Added Business Memory as a visible representation of what Barni has learned.

## Foundation

- Established invoice ingestion, storage, archive, search, supplier history, product history, and the Knowledge Engine.
