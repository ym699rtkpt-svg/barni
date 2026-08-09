# BAR-ALPHA-P0-003 — Recovery & Error Handling Report

## Executive Summary

The Alpha workflow now contains customer-facing failures without exposing Python exceptions, preserves retryable work, and keeps each affected page usable.

This sprint did not change invoice decisions, OCR behavior, identity rules, Business Memory logic, or product design. It strengthened existing recovery boundaries and verified them with failure injection plus a real browser workflow.

**Recovery confidence: 91 / 100**

The remaining nine points primarily reflect infrastructure limits: SQLite resource warnings, no customer repair flow for a permanently missing source document, and the inability to distinguish an empty intake queue from the rare case where both queue snapshots are unreadable.

## Recovery Contract

Every customer-facing recovery now aims to answer:

1. **What happened?** A short description in Barni's language.
2. **What is Barni doing?** Whether the file, invoice, decision, or stored knowledge remains safe.
3. **What should happen next?** Retry, complete Review manually, skip, upload again, return to results, or check source files.

Technical exception text is retained only in operational logs or internal queue diagnostics. It is not rendered in the normal customer experience.

## Failures Tested

| Failure | Test method | Recovery verified | Result |
|---|---|---|---|
| Upload persistence failure | Injected `OSError` while reading uploaded bytes | An error review record is retained; customer text asks for a fresh upload; private error text is not exposed | Pass |
| OCR timeout | Injected `subprocess.TimeoutExpired` | Original file remains stored; invoice enters Review; customer can complete details or skip | Pass |
| General processing failure | Audited per-file exception boundary and error-record flow | One failed invoice does not discard other queued work; failure remains actionable in Review | Pass |
| Identity Review interruption | Existing identity decision and reversal tests plus page recovery audit | Failed decisions change nothing; queue remains durable; page offers retry | Pass |
| Duplicate resolution interruption | Lifecycle fault/retry tests | Repeating approval safely returns the duplicate decision; replace, keep both, and skip remain idempotent | Pass |
| Business Memory update failure | Injected failing Knowledge Engine | Invoice is not inserted twice; Review remains retryable; the next attempt resumes learning and converges | Pass |
| Search with no results | Real browser search for `NoSuchSupplier` | Calm summary and concrete search alternatives appear; Search remains active | Pass |
| Empty Business Memory | Real browser against a fresh isolated database | Zero state explains Barni is ready to learn and provides a Feed action | Pass |
| Export failure | Injected package-builder `OSError` | No exception escapes; stale package state is cleared; customer is told nothing was exported and can retry | Pass |
| Missing PDF | Temporarily moved an isolated archived PDF, opened its Search detail, then restored it | Stored metadata and products remain visible; page states the original is unavailable; no page crash | Pass |
| Unexpected page exception | Audited application-level page boundary | Error is logged internally; each primary page renders a safe destination and retry action | Pass |

## Failures Fixed

### 1. Business Memory failure feedback disappeared

**Previous behavior:** The approval service correctly returned a safe retry result, but Review immediately reran. The error message rendered during the failed call disappeared before the customer could read it.

**Fix:** Approval recovery text is persisted through the Streamlit rerun and rendered at the top of Feed. A successful retry clears the stale recovery message. The existing idempotent approval operation remains the source of retry safety.

**Customer outcome:** The customer sees that Business Memory was not fully updated, that the invoice remains safe in Review, and that pressing approval again is the correct next action.

### 2. Upload byte failures escaped the per-file recovery boundary

**Previous behavior:** Writing uploaded bytes happened before the per-file `try` block. A storage/read failure could abort the page instead of creating an actionable failed record.

**Fix:** Upload persistence now occurs inside the existing per-file recovery boundary. Failure records use calm customer copy while technical details remain internal.

**Customer outcome:** The batch remains usable. If the original was not stored, Review explicitly tells the customer to skip that record and upload the file again.

### 3. OCR timeout recovery lacked explicit retained-state language

**Previous behavior:** Timeouts already entered Review, but the recovery text did not clearly distinguish a retained file from a failed upload.

**Fix:** Review checks whether the source actually exists. When it does, Barni says it kept the file in Review and offers manual completion or a clearer upload. When it does not, Barni asks the customer to skip and upload again.

### 4. Accountant export failure replaced the whole page

**Previous behavior:** Package-generation exceptions reached the application page guard. The entire Accountant Workspace was replaced by a generic retry screen.

**Fix:** Export generation has a localized recovery boundary. Failed package bytes and month state are cleared, operational details are logged, and the rest of the Accountant Workspace remains usable.

**Customer outcome:** The customer learns that nothing was exported, invoices were unchanged, source files should be checked, and the same button can be tried safely again.

### 5. Identity Review used only the generic page recovery

**Previous behavior:** An unexpected Identity Review page exception fell back to Home-oriented generic recovery.

**Fix:** Identity Review now has a dedicated page recovery message and retry destination.

**Customer outcome:** Barni states that no identity decision changed and the question remains safely waiting.

### 6. Legacy upload exposed exception text

**Previous behavior:** The internal legacy upload surface interpolated the Python exception into customer-visible text.

**Fix:** It now logs the technical failure and displays calm recovery guidance without the exception string.

### 7. PDF reads could fail between availability check and rendering

**Previous behavior:** Search checked that the source existed and then read it outside the preview exception boundary. A file disappearing at that moment could replace the page with generic recovery.

**Fix:** PDF byte reading is now contained. Stored invoice details remain available and the customer can return to results or retry.

## Retry Safety

- Upload/processing failures do not enter Business Memory.
- Failed OCR records remain reviewable or skippable.
- Invoice approval uses a stable operation key.
- A Business Memory retry reuses the stored invoice instead of inserting another copy.
- Supplier learning and Business Fact generation remain idempotent under approval retry.
- Duplicate decisions can be requested again after session interruption.
- Failed identity decisions do not partially apply.
- Failed exports do not modify invoices, workflow state, or source files.
- Search and missing-document retries are read-only.

## Normal Workflow Regression

The application was run with a fresh isolated data root and a real invoice PDF.

Verified in the browser:

1. Upload completed.
2. Processing found one supplier, three products, and three price points.
3. Review loaded the supplier, invoice date, invoice number, total, and products.
4. Approval completed.
5. Business Memory immediately showed one invoice, one supplier, and three products.
6. Search invoice detail remained usable with the source PDF temporarily unavailable.
7. Accountant Workspace showed one ready document.
8. Accountant package generation completed and exposed the download action.

The isolated PDF was restored after the missing-source test.

## Automated Verification

- **89 tests passed.**
- Targeted Alpha blocker, lifecycle, and Identity Review tests passed.
- Python compile checks passed.
- `git diff --check` passed.

New regression coverage includes:

- Upload persistence failure containment.
- OCR timeout retention and customer-safe messaging.
- Export failure containment without exception leakage.
- Canonical queue backup recovery.

Existing lifecycle coverage verifies interrupted Business Memory learning, approval retry, duplicate decisions, identity reversibility, and no duplicate invoice insertion.

## Remaining Known Limitations

### Both intake queue snapshots can fail closed as empty

The primary queue recovers from its last valid backup. If both files are damaged, consumers currently receive an empty queue rather than a typed “queue unavailable” condition.

**Pilot risk:** Low probability, high impact.

### Permanently missing PDFs cannot be relinked

Search, Business Memory, and Accountant Workspace degrade gracefully and preserve extracted knowledge, but the customer cannot attach a replacement source file to the existing invoice.

**Pilot risk:** Low if archive storage remains local and stable.

### SQLite connection warnings remain

The test suite reports pre-existing unclosed SQLite connection warnings. They do not fail current tests, but long sessions and repeated Streamlit reruns may increase locking or resource pressure.

**Pilot risk:** Low–Medium.

### Approval is recoverable rather than fully atomic

Invoice storage, knowledge learning, identity learning, Business Facts, and queue resolution span several commits. Idempotent retry converges in tested cases, but fault injection does not yet cover every individual checkpoint.

**Pilot risk:** Low–Medium.

### Export is synchronous

Large months can keep the UI waiting while ZIP generation runs. Failure is now contained, but there is no resumable background export.

**Pilot risk:** Low for the Alpha dataset.

### Operational logging is best-effort

Customer recovery does not depend on logging. If the log destination itself is unavailable, the page still recovers, but the operator may lose diagnostic evidence.

**Pilot risk:** Low.

## Recovery Confidence

**91 / 100**

The customer workflow is strongly recoverable for the failures most likely during the Alpha pilot. The most valuable next reliability work is checkpoint-level approval fault injection followed by cleanup of SQLite connection ownership. Neither requires new product functionality.
