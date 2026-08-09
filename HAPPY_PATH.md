# Barni Alpha Happy Path

## Purpose

The first five minutes should feel like one continuous act of teaching Barni:

> Open Barni → Feed invoices → Review exceptions → Approve → See what Barni learned → Find it → Understand Business Memory → Prepare the accountant package

This work changes presentation, prioritization, and navigation only. It does not add a product capability or change extraction, identity, invoice lifecycle, Business Facts, or database rules.

## Before

- Home offered several competing actions before making pending invoice work clear.
- Feed placed shared counters before the task the owner came to complete.
- Earlier unfinished reviews were hidden inside Advanced settings.
- One uncertain invoice caused every invoice in the batch to enter manual review.
- The post-processing action did not distinguish safe invoices from exceptions.
- The completion action opened the legacy Knowledge page instead of continuing through Search and Business Memory.
- Batch completion showed aggregate growth but did not retain the existing evidence-backed learning stories generated during approval.
- Search had no explicit continuation into Business Memory.
- Business Memory led with identity-maintenance work before showing what the business had learned.
- Business Memory did not make the accountant handoff an obvious next step.
- A long numeric queue identifier could be interpreted as a database invoice ID and crash Invoice Review.
- Search could present unusably long suggestion chips and grammatically incorrect result counts.

## After

### 1. Open Barni

Home states the most important current condition and presents one primary action:

- `Continue invoice review` when work is open.
- `Feed Barni` when no invoice decision is waiting.

The competing Ask Barni interaction was removed from the hero. Existing conversation capabilities remain available elsewhere; Home now answers what to do next.

### 2. Upload invoices

Feed opens directly on either:

- the upload action, or
- a visible `Continue review` action when prior work is unfinished.

An unfinished review no longer hides inside Advanced settings, and additional uploads wait until the current decision is completed.

### 3. See processing progress

The existing staged progress remains visible for reading, supplier recognition, product learning, and per-file completion. The result state states how many invoices were read and whether anything requires attention.

### 4. Review only exceptions

After processing, Barni separates the batch into clear invoices and invoices requiring attention.

The primary action explains exactly what will happen, for example:

> Approve 4 clear and review 1

Clear invoices use the existing approval workflow. Only uncertain, failed, duplicate, or otherwise unresolved records enter manual review. If a supposedly clear invoice encounters a duplicate or approval failure, processing stops safely and that invoice plus all unprocessed records remain available for review.

### 5. Approve with confidence

Invoice Review continues to lead with:

1. Barni's conclusion.
2. What the owner should do.
3. Why Barni reached the conclusion.
4. Supporting evidence.
5. The original invoice and editable data.

Technical confidence remains collapsed. Unsupported queue evidence stays as current-invoice evidence instead of being queried as a database invoice ID.

### 6. See what Barni learned

The success state explicitly says the review is complete, shows the exact aggregate Business Memory growth, and retains up to three evidence-backed stories already produced by the Business Story Engine during approval.

If nothing meaningful changed, Barni calmly says Business Memory is up to date. Skipped invoices and resolved duplicates remain explicit.

### 7. Find the learned information

The primary completion action is now `Find it in Search`. It opens Search with the latest approved supplier or invoice reference already populated when available.

Search continues to use the existing backend logic. Suggested searches are drawn from real Business Memory, exclude labels too long to scan, and successful results offer `Open Business Memory` as the next secondary step.

### 8. Understand Business Memory

Business Memory now leads with what Barni knows, then lets the owner explore supplier, product, and price evidence. Identity questions remain available later on the page and no longer compete as the primary action.

Recent learned invoices remain visible, and the page ends with one primary next step: `Prepare for accountant`.

### 9. Export for the accountant

Accountant Workspace retains the existing readiness checks and package builder. The owner sees what is ready, what still needs attention, and one primary `Prepare Accountant Package` action. Once prepared, the existing download action appears.

## UX Decisions

### One decision at a time

Each happy-path screen now has one visually primary action. Secondary navigation remains available without competing with the task.

### Review is exception handling

Barni should do the routine work and ask the owner only when a business decision or correction is genuinely required. The owner still explicitly authorizes approval through a clearly labelled batch action.

### Progress is part of trust

Waiting states describe current work and file progress. Barni never implies Business Memory has changed before approval succeeds.

### Success must explain value

Completion is not merely “saved.” It states what entered Business Memory and preserves the engine's existing evidence-backed explanation.

### Navigation follows the customer story

The completion path is Search → Business Memory → Accountant Workspace. The legacy Knowledge route is no longer used by Feed completion.

### Fail closed

Duplicates, approval failures, unsupported evidence identifiers, and missing required data never pass silently. They remain reviewable without breaking the page.

### Remove before adding

The Home conversation block and Feed's leading status strip were removed from this journey. No new feature, dashboard, intelligence rule, or database field was introduced.

## Remaining Friction

- The current pilot dataset contains 18 unresolved queue records, including exact duplicates. Their Replace, Keep both, Skip, edit, or reject decisions require the restaurant owner and were intentionally not automated during verification.
- Accountant readiness correctly reports existing duplicate groups and undated open invoices. The package can still be prepared, but the month cannot be declared fully ready until those real data decisions are resolved.
- Business Memory currently contains 98 identity questions. They are demoted from the primary journey, but the underlying review workload remains.
- Some historical product names are long and source-like. Search suggestions now suppress overlong labels, while canonical cleanup remains an Identity Review responsibility.
- Existing test output reports SQLite connection `ResourceWarning`s. Tests pass, but connection ownership should be tightened in a separate maintainability task.

## Acceptance Checklist

- [x] Landing page clearly introduces Barni as Business Memory.
- [x] Home shows one primary next action.
- [x] Pending review is visible without opening Advanced settings.
- [x] Upload accepts multiple invoices using the existing workflow.
- [x] Processing reports staged, per-file progress.
- [x] Result state distinguishes clear invoices from exceptions.
- [x] Only records requiring attention enter normal manual review.
- [x] A newly discovered duplicate safely enters review.
- [x] Approval still uses the canonical invoice lifecycle.
- [x] Review begins with Barni's conclusion and recommendation.
- [x] Original invoice and editable data remain available.
- [x] Technical confidence stays collapsed.
- [x] Unsupported queue identifiers cannot crash evidence lookup.
- [x] Successful completion explicitly confirms that review is finished.
- [x] Completion shows Business Memory growth and existing evidence-backed stories.
- [x] Completion's primary action opens Search rather than legacy Knowledge.
- [x] Search finds a real stored supplier and its source invoice.
- [x] Search provides a direct continuation into Business Memory.
- [x] Business Memory shows learned invoices, suppliers, products, and price coverage first.
- [x] Supplier and product histories retain source-invoice drill-down.
- [x] Business Memory leads to Accountant Workspace.
- [x] Accountant package generation completes and exposes the download action.
- [x] Customer-facing pages render without technical exception text after the evidence fix.
- [x] Desktop runtime flow was inspected in the running Streamlit application.
- [x] Python compilation succeeds.
- [x] Full automated suite passes.

## Verification Record

Verified on 9 August 2026 using the real local Barni application and stored business history.

- Home rendered the current canonical workflow and `Continue invoice review` as its primary action.
- Feed exposed unfinished work immediately.
- Invoice Review opened a real duplicate invoice, explained the duplicate, recommended comparison, and showed supporting evidence before the editable invoice.
- Search for `KITCHENWARE - Kitch & Design` returned one supported invoice and the correct supplier history.
- Search opened Business Memory through the new continuation.
- Business Memory rendered 66 learned invoices, 42 suppliers, 189 products, price-history coverage, evidence drill-down, and the accountant continuation.
- Accountant Workspace prepared a package containing 34 source documents and exposed `Download Accountant Package`.
- No duplicate resolution or approval was chosen on the owner's behalf.
- The automated suite completed with 80 passing tests.

The presentation path is complete. Final business readiness still depends on the restaurant owner resolving the genuine duplicate and attention decisions already present in the pilot data.
