# BAR-ALPHA-01 — One Trusted Invoice Lifecycle

## Status

Implemented and validated as the canonical Barni Alpha invoice workflow foundation.

## Authoritative Model

An invoice lifecycle keeps separate concerns separate:

- `processing_state`: not started, processing, complete, or failed
- `review_state`: not required, pending, needs attention, or resolved
- `approval_state`: not approved, approved, rejected, or skipped
- `duplicate_state`: not checked, unique, needs a decision, or one of the resolved duplicate outcomes
- `accounting_readiness`: not applicable, blocked, or ready

The customer does not see these as competing statuses. The workflow service derives one customer-facing state:

- Pending Review
- Learning
- Approved
- Needs Attention
- Duplicate

Resolved rejected and skipped queue records do not appear as active work.

## Authoritative Approval Path

All Feed and Invoice Review approval calls route through `InvoiceWorkflowService`.

```text
Review record
→ durable approval operation key
→ duplicate decision
→ save or replace once
→ learn through Knowledge Engine
→ synchronize Comparable Price Ledger
→ record completed operation
→ expose the same result to every customer surface
```

The Feed retains presentation and queue orchestration. The review form retains editable evidence. Neither owns approval behavior.

## Idempotency

Each queue/review record receives one stable approval operation key. The database stores the operation and links the resulting invoice to that key.

- A completed approval retry returns the original outcome.
- A retry after invoice persistence but before learning resumes learning against the same invoice.
- Supplier memory ignores a repeated invoice event.
- Canonical identity and fact synchronization reuse their existing upsert behavior.
- Skipped duplicates complete without adding knowledge.
- Replace and keep-both decisions retain their explicit outcomes.

No retry may insert or learn the same approved record twice.

## Shared Counters

Feed, Home, and Accountant render `InvoiceWorkflowSnapshot` from the same workflow service. Month-scoped Accountant summaries use the same derivation rules and add only accounting-specific source-file and supplier requirements.

Business Memory and Home business metrics consume only canonically approved invoices. Search continues to use the existing search engine and sees the approved database row immediately.

## State Audit

### Consolidated

- Feed queue `processing`, `ready`, `review`, `error`, and resolved states now map through the canonical lifecycle model.
- Stored invoice statuses map through the same lifecycle model.
- Duplicate detection projects to the canonical duplicate dimension and one customer state.
- Feed, Home, and Accountant counters share one snapshot service.
- Invoice detail translates stored status through the shared service instead of printing a raw database value.
- Home, Business Memory, and Insights exclude non-approved records from learned-business metrics.
- Review approval no longer owns saving, duplicate resolution, learning, or fact refresh.

### Legitimate internal states retained

- Feed JSON queue status remains the persisted state of the local intake queue.
- The invoices table retains its legacy `status` column for backward compatibility.
- Approval operations use internal processing state for recovery and idempotency.
- Accountant readiness remains a derived dimension because approval alone does not guarantee an available source file or supplier identity.

These values are inputs to the workflow service, not independent customer truths.

## Remaining Legacy Dependencies

1. `app.py` still contains an internal legacy upload route backed by `data/invoices.db`. It is available only under Internal tools and does not feed the canonical customer workflow, Business Memory, Search, Home, or Accountant. It must not be promoted back into customer navigation.
2. Batch, AI, database, migration, diagnostics, and month-closing tools retain operational status vocabularies. They are internal tools and are not canonical customer counters.
3. `database.control_center_data()` and older analytics helpers still derive legacy review/duplicate metrics for internal or compatibility consumers. Customer Home, Feed, Invoice Detail, Business Memory, Insights, and Accountant no longer rely on those status calculations.
4. The local Feed queue remains a JSON file rather than a repository-backed queue. The workflow service is authoritative for interpretation, but concurrent writers and cross-device processing are not supported in Alpha.
5. Duplicate matching still uses the existing supplier ID, invoice number, and document type rule. BAR-ALPHA-01 consolidates its lifecycle meaning; it does not redesign duplicate intelligence.

## Contract Test

The automated lifecycle contract covers:

- new invoice entering pending review
- approval
- one-time learning
- trusted fact synchronization
- immediate Search visibility
- immediate Business Memory update
- Accountant readiness
- approval retry
- retry after interrupted learning
- duplicate decision state
- needs-review state
- processing failure state
- rerun after approval
- agreement between derived customer-facing counters

## Invariant

An invoice may have several internal lifecycle dimensions, but Barni has only one interpretation of what the owner needs to know or do next.
