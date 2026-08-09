# BAR-ALPHA-P0-002 — Dependency & Fragility Audit

## Scope and Method

This audit reviewed the stability of the Thursday pilot path across Feed, Review, Home, Business Memory, Search, and Accountant Workspace. It traced queue state, invoice lifecycle state, database reads, session state, approval side effects, page-level calculations, exception handling, and Streamlit rerun behavior.

No product feature or visual design was changed. Only the highest-impact stability issue was fixed.

## Executive Finding

The core Happy Path works, but the application is still held together by a small number of broad modules and repeated read models. The most immediate pilot risk was a split implementation for reading the intake queue: Feed could recover a backup while Home and Accountant silently treated the same damaged queue as empty. This could make an invoice disappear between screens after an interrupted queue write.

The queue now has one canonical reader with the same recovery behavior for Feed, Home, workflow counters, and Accountant Workspace.

## Fragility Register

### P0-002-01 — Conflicting intake queue readers — Fixed

- **Severity:** Critical
- **Why it was fragile:** Feed and the shared invoice workflow parsed the same `queue.json` independently. Feed recovered `queue.json.backup`; workflow consumers returned an empty queue when the primary file was malformed. A single interrupted write could therefore hide pending reviews from Home or Accountant while they remained visible in Feed.
- **Probability of affecting Thursday's pilot:** Medium. Atomic writes reduce the likelihood, but a browser/process interruption during a ten-invoice batch remains realistic.
- **Recommended fix:** Make `services.invoice_workflow.load_queue_records` the canonical resilient reader and have Feed delegate to it.
- **Estimated effort:** Small
- **Status:** Implemented and regression-tested.

### P0-002-02 — Feed and Review are one oversized workflow/UI module

- **Severity:** High
- **Why it is fragile:** `daily_intake.py` owns upload persistence, parsing orchestration, queue persistence, status decisions, duplicate handling, approval coordination, review presentation, navigation, completion summaries, and session state. A small workflow change can unintentionally affect rendering or recovery several states later.
- **Probability of affecting Thursday's pilot:** Medium–High, especially during last-minute fixes.
- **Recommended fix:** After the pilot, extract a small, tested intake coordinator around the existing functions. Do not rewrite the workflow before Thursday.
- **Estimated effort:** Large

### P0-002-03 — Resolved records remain in the active queue

- **Severity:** High
- **Why it is fragile:** Approval changes a queue record to `approved` instead of removing or archiving it. The database and queue therefore both retain lifecycle representations of the same invoice. Current projections avoid double-counting the approved customer status, but accounting readiness already sees both representations internally, and the queue grows indefinitely.
- **Probability of affecting Thursday's pilot:** Medium. Ten invoices are unlikely to create a performance failure, but stale resolved records increase the chance of inconsistent counters and recovery behavior.
- **Recommended fix:** Define active versus historical queue storage explicitly. Move resolved records to an append-only history file/table, then keep only actionable records in the active queue.
- **Estimated effort:** Medium

### P0-002-04 — Approval spans several independently committed side effects

- **Severity:** High
- **Why it is fragile:** Invoice storage, supplier memory, canonical identity learning, comparable price ledger synchronization, approval-operation status, and queue resolution do not share one transaction. Idempotency reduces duplicate work, but a mid-sequence failure can leave an approved invoice stored while the review queue still asks the user to retry.
- **Probability of affecting Thursday's pilot:** Low–Medium. It depends on a database or normalization failure during approval, but the impact is highly visible.
- **Recommended fix:** Add an explicit recoverable approval checkpoint contract and a reconciliation test for failure after each side effect. Avoid a large transaction spanning file operations.
- **Estimated effort:** Medium

### P0-002-05 — Home reconstructs Business Memory locally

- **Severity:** High
- **Why it is fragile:** Home calls `dashboard_data`, `invoice_workflow_snapshot`, `approved_documents`, and the story engine, then independently filters items and calculates monthly supplier/product metrics. Business Memory computes related values through a different path. The same concept can drift between pages.
- **Probability of affecting Thursday's pilot:** Medium. A newly approved invoice can expose differing definitions immediately.
- **Recommended fix:** Introduce one read-only pilot snapshot assembled from existing canonical services. Home should render it rather than recompute business definitions.
- **Estimated effort:** Medium

### P0-002-06 — Business Memory performs a wide synchronous rebuild on every rerun

- **Severity:** Medium
- **Why it is fragile:** `business_memory_data()` reads identity health, dashboard documents/items, approved documents, product classifications, growth history, and recent learning on every Streamlit rerun. As invoice volume grows, one click can repeat several full-table operations.
- **Probability of affecting Thursday's pilot:** Low with ten invoices; Medium with the existing archive or repeated reruns.
- **Recommended fix:** Measure first, then cache a versioned read model invalidated only after approval or identity decisions.
- **Estimated effort:** Medium

### P0-002-07 — Search issues repeated broad and per-result queries

- **Severity:** Medium
- **Why it is fragile:** Search loads all invoices for date parsing/detail resolution, runs the filtered search, and issues an additional supplier query for each matching supplier. Live typing causes full Streamlit reruns, multiplying this work.
- **Probability of affecting Thursday's pilot:** Medium if the pilot uses the full archive; Low in a fresh ten-invoice dataset.
- **Recommended fix:** Reuse one result snapshot per submitted query and aggregate supplier metadata in one service query.
- **Estimated effort:** Medium

### P0-002-08 — Search presentation knows database and OCR implementation details

- **Severity:** Medium
- **Why it is fragile:** `smart_archive.py` directly calls database queries, identity repositories, raw OCR text fields, lifecycle labels, and invoice-item structures. Changes to storage shape can break result grouping or invoice detail without a service contract failure.
- **Probability of affecting Thursday's pilot:** Low–Medium.
- **Recommended fix:** After Alpha, define a read-only Search result contract. Preserve the current backend search behavior while moving result assembly out of Streamlit.
- **Estimated effort:** Large

### P0-002-09 — Accountant readiness performs repeated reads and synchronous file checks

- **Severity:** Medium
- **Why it is fragile:** Accountant status independently queries all documents, approved monthly documents, and the queue, then checks each archived file on disk. Export builds the ZIP synchronously inside a UI interaction and stores the complete package in session state.
- **Probability of affecting Thursday's pilot:** Low for ten invoices; Medium for a large month or slow storage.
- **Recommended fix:** Keep for Alpha, add timing/error tests, and later generate from one monthly readiness snapshot.
- **Estimated effort:** Medium

### P0-002-10 — Session state duplicates durable workflow state

- **Severity:** Medium
- **Why it is fragile:** Feed keeps batch IDs, review IDs, duplicate decisions, completion deltas, last search, flow state, and stories in Streamlit session state while durable truth lives in the queue and database. A refresh or new session can lose the navigation state even though the invoice remains recoverable.
- **Probability of affecting Thursday's pilot:** Medium; browser refreshes are common during demos.
- **Recommended fix:** Reconstruct the current actionable step from canonical queue/database state when session keys are absent. Keep session state only for transient presentation.
- **Estimated effort:** Medium

### P0-002-11 — Invalid queue state can still fail silently when all snapshots are damaged

- **Severity:** Medium
- **Why it is fragile:** The fixed reader recovers the last valid backup, but if both primary and backup are unreadable it returns an empty list. Pages cannot distinguish “no pending invoices” from “queue unavailable.”
- **Probability of affecting Thursday's pilot:** Low.
- **Recommended fix:** Return a typed queue load result or emit a visible operational health condition while keeping customer-facing language calm.
- **Estimated effort:** Small–Medium

### P0-002-12 — Database availability is a shared cascade point

- **Severity:** High
- **Why it is fragile:** Home, Search, Business Memory, Accountant Workspace, stories, identities, and workflow snapshots all depend directly or indirectly on the same SQLite database and automatic schema initialization. A lock, migration failure, or inaccessible database can take down several pages together.
- **Probability of affecting Thursday's pilot:** Low, but impact is product-wide.
- **Recommended fix:** Add startup/readiness checks and a tested read-only recovery state. Do not redesign storage before the pilot.
- **Estimated effort:** Medium

### P0-002-13 — Resource ownership is inconsistent

- **Severity:** Medium
- **Why it is fragile:** The test suite repeatedly reports unclosed SQLite connection warnings. These can become file-descriptor or locking pressure during a long Streamlit session with frequent reruns.
- **Probability of affecting Thursday's pilot:** Low–Medium on a single-user short pilot.
- **Recommended fix:** Trace the warnings to connection factories and repository construction, then enforce context-managed ownership in tests and services.
- **Estimated effort:** Medium

### P0-002-14 — Some secondary failures are intentionally silent

- **Severity:** Low–Medium
- **Why it is fragile:** Story generation, telemetry, local PDF-text fallback, pilot log parsing, and selected detail helpers suppress failures. This protects the customer workflow, but the pilot operator may have no indication that supporting behavior degraded.
- **Probability of affecting Thursday's pilot:** Medium for at least one secondary service; Low impact on completion.
- **Recommended fix:** Keep graceful customer behavior but record structured operational errors consistently for the pilot operator.
- **Estimated effort:** Small

## Services With Too Many Responsibilities

1. **`daily_intake.py`** — upload, extraction orchestration, queue infrastructure, review UI, approval workflow, duplicate resolution, progress, navigation, and completion messaging.
2. **`database.py`** — schema migration, archive file movement, persistence, search, reporting queries, tags, duplicate handling, and health checks.
3. **`smart_archive.py`** — Search UI, query interpretation, result assembly, OCR grouping, details, PDF presentation, identity access, and navigation.
4. **`services.business_memory`** — joins several read models and calculates counts, growth, recent learning, supplier history, and product history.

These should not be redesigned before Thursday. The immediate safety strategy is stronger contracts and regression tests at existing boundaries.

## Duplicate Logic and State

- Queue parsing existed separately in Feed, workflow services, and pilot support. Feed/workflow duplication was fixed; pilot support remains.
- Home and Business Memory calculate overlapping product and supplier knowledge through different paths.
- Search and Business Memory both assemble supplier/product histories directly.
- Durable lifecycle state is represented in both database records and retained queue records.
- Batch/review progress is represented in both durable queue state and Streamlit session state.
- Source-file availability is checked in workflow lifecycle and Accountant status paths.

## Expensive Reruns

- Home rebuilds dashboard data, workflow counts, approved documents, item filtering, and stories on each rerun.
- Business Memory rebuilds identities, dashboard data, approved filtering, growth, and recent learning on each rerun.
- Search performs database work while typing and additional per-supplier queries after a match.
- Accountant status scans documents and filesystem paths; package creation is synchronous.
- Database initialization/migration checks are reached through normal connection-path resolution.

## Cascading Failure Paths

- **SQLite unavailable or locked:** affects Home, Search, Business Memory, Insights/story generation, and Accountant Workspace.
- **Canonical identity learning failure during approval:** can delay completion and every downstream knowledge surface.
- **Comparable Price Ledger synchronization failure:** can make approval appear unfinished even after the invoice record was stored.
- **Queue unreadable:** affects Feed recovery, Home workflow counters, and Accountant readiness. The valid-backup case is now fixed.
- **Missing archived source:** Review preview, Search detail, evidence opening, and Accountant export all degrade from the same missing file.

## Root Cause

The highest-impact issue was not queue persistence itself; atomic writes and a backup already existed. The root cause was that recovery behavior was owned by Feed rather than the shared workflow boundary. Other pages read the queue through a second implementation that silently converted corruption into an empty queue.

This violated one source of truth and made application state depend on which page read it.

## Fix Applied

- `services.invoice_workflow.load_queue_records()` now reads the primary queue and falls back to `queue.json.backup` when the primary snapshot is missing, malformed, unreadable, or not a list.
- Feed's existing `_load_queue()` is retained as a compatibility wrapper but delegates to the canonical workflow reader.
- The existing atomic writer remains unchanged.
- A regression test corrupts the primary queue and verifies that both Feed and shared workflow consumers recover the same valid snapshot.

## Verification

### Automated

- Targeted Alpha and invoice lifecycle tests passed.
- Full suite: **86 tests passed**.
- Python compile checks passed.
- `git diff --check` passed.

The full suite continues to emit pre-existing unclosed SQLite connection warnings; these are recorded above as a remaining risk.

### Manual Happy Path

The application was run with a fresh isolated data root and a real PDF invoice:

1. Entered Barni.
2. Opened Feed Barni.
3. Uploaded `3802.pdf`.
4. Processing completed with 1 supplier, 3 products, and 3 price points.
5. Review loaded supplier, date, invoice number, and total correctly.
6. Approved and taught Barni.
7. Completion showed 1 invoice, 1 supplier, 3 products, and 3 price points learned.
8. Opened Business Memory.
9. Business Memory immediately showed 1 invoice, 1 supplier, and 3 products.
10. The isolated database contained one approved invoice and three item rows.

The complete Happy Path succeeded.

## Remaining Fragile Areas

The most important remaining risks are:

1. Approval side effects are recoverable but not one atomic lifecycle transition.
2. Resolved records accumulate in the active queue.
3. Home and Business Memory maintain overlapping read calculations.
4. Session state duplicates durable workflow navigation state.
5. SQLite connection warnings indicate unresolved resource ownership.
6. Search and Business Memory reruns perform broad repeated queries.
7. If both queue snapshots are damaged, the failure is still indistinguishable from an empty queue.

No lower-priority issue was changed in this task.

## Recommendation for Tomorrow

Harden approval recovery before changing architecture or UI.

Add fault-injection tests at each existing approval checkpoint—invoice stored, supplier memory updated, identity learned, price ledger synchronized, operation completed, and queue resolved. Confirm that retry always converges to exactly one approved invoice, one set of Business Memory facts, and no actionable queue record.

This is the smallest next investment that protects the moment the restaurant owner decides to trust Barni.
