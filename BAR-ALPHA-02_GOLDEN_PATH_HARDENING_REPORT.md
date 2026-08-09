# BAR-ALPHA-02 — Golden Path Hardening Report

## Scope

Feature development was frozen for this task. The audited journey was:

> Feed Barni → Upload invoice → Read document → Review → Approve → Business Memory → Search → Insights → Accountant export

The work changed recovery, feedback, navigation, empty states, and verification only. It did not add intelligence, alter extraction rules, change the database schema, or introduce a parallel workflow.

## Hardening Completed

### Customer navigation

The default customer navigation now contains only:

- Home
- Feed Barni
- Search Invoices
- Business Memory
- Insights
- Accountant Workspace

Legacy Knowledge, the unfinished Recipes preview, Pilot Dashboard, migrations, diagnostics, legacy upload, and other operator tools are no longer exposed to restaurant owners. They remain available only when `BARNI_INTERNAL_TOOLS=1` is deliberately enabled.

### Page recovery

The previous generic message—“Barni ran into a problem on this page”—was removed.

Each Golden Path page now has a calm recovery state explaining:

- what Barni could not prepare;
- that invoices or files remain safe;
- whether anything changed;
- the next recovery action.

Runtime details continue to be logged for internal review and are not shown to restaurant owners.

### Document-reading recovery

Document-reading exceptions no longer become customer-facing stack, command, provider, or parser messages.

The queue retains:

- a calm recovery message for the owner;
- the original uploaded file;
- the review/edit path;
- a separate internal technical error for diagnosis.

The owner is told to upload a clearer copy or complete the visible details manually. Existing failed queue records also receive this recovery treatment rather than exposing their historical raw error.

### Approval recovery

Approval failures no longer return raw database or service exceptions to Feed.

The canonical workflow now says:

> I couldn't finish updating Business Memory. Your invoice is safe in review. Please try again.

The internal approval operation still records the actual failure for recovery and diagnostics. Idempotent retry behavior is unchanged.

### Completed-action feedback

The journey now confirms:

- invoice files were read;
- which invoices are clear and which need attention;
- edits were saved;
- approval updated Business Memory;
- what Barni learned;
- Search match counts;
- identity decisions and reversals;
- accountant readiness;
- package preparation and local download availability.

### Empty and dead states

- Empty Insights now leads to Feed Barni.
- Empty Business Memory now leads to Feed Barni rather than an empty accountant workspace.
- An empty accounting month now offers Feed Barni instead of a disabled export button.
- A stale accountant package is not offered for a month containing no approved documents.
- Insights no longer exposes the internal category-maintenance control.
- PDF preview failure calmly directs the owner to the existing Download PDF action and does not reveal technical details.
- Identity Review failures now explain which decision was not saved and confirm that nothing changed.

## Immediate Propagation Contract

The lifecycle integration test now approves one isolated invoice and proves, in the same workflow:

1. The canonical invoice state changes from Pending Review to Approved.
2. Search immediately finds the approved invoice by product.
3. Business Memory immediately increases invoice, supplier, and product knowledge.
4. The approved invoice appears in Recent things Barni learned.
5. The supplier memory event is stored once.
6. A comparable Business Fact exists for the invoice line.
7. The Insights context used by the real page produces an evidence-backed story linked to the approved invoice.
8. Accountant readiness immediately includes the invoice.
9. The generated ZIP opens and contains the source invoice, Summary CSV, Summary PDF, and Metadata JSON.

The retry test also proves a failed learning pass does not expose its internal exception, insert a second invoice, or relearn the same invoice.

## Runtime Verification

Verified on 9 August 2026 in the real localhost Streamlit application using the existing business history.

### Home

- Six customer destinations were visible.
- Knowledge, Recipes, Pilot Dashboard, and Internal tools were absent.
- Current pending work produced one `Continue invoice review` action.

### Feed and Review

- Existing unfinished work appeared immediately.
- Review opened without a generic error.
- The visible order was Barni's conclusion → next action → supporting evidence → original invoice → approval.
- No approval or duplicate decision was made on the restaurant owner's behalf.

### Search

- A real suggested search for `BIAFIN CREAM GSL 9` executed successfully.
- Search returned one supported purchase, its source invoice, latest stored price, and supplier.
- The Business Memory continuation was visible.

### Insights

- The page rendered evidence-backed Business Stories and supporting overview data.
- No internal maintenance control or generic error was visible.

### Business Memory

- Learned invoices, suppliers, products, price coverage, supplier history, product history, recent learning, and evidence drill-down rendered.
- The accountant continuation was visible.

### Accountant export

- Readiness checks rendered using the canonical workflow.
- `Prepare Accountant Package` completed.
- `Download Accountant Package` appeared with explicit local success feedback.

### Automated verification

- Python compilation: passed.
- Full test suite: 80 tests passed.
- Repository whitespace validation: passed.

## Remaining Blockers, Ordered by Severity

### Critical

No unresolved Critical software blocker was found in the implemented Golden Path.

### High — H-01: Existing pilot queue requires owner decisions

The current real dataset contains 18 unresolved queue records. Current global workflow counts include 13 Needs Attention records and 17 duplicate groups; these categories can overlap and should not be added together.

Why it blocks the pilot:

- Feed correctly asks the owner to finish existing decisions before adding more work.
- The accountant month cannot be declared fully ready while genuine duplicates and undated open records remain.
- Barni must not automatically choose Replace, Keep both, Skip, edit, or reject.

Resolution:

The restaurant owner must review these records, or the pilot must begin from a clean, backed-up business workspace with genuinely new invoices.

Acceptance test:

- Golden Path counters show no unintended open work.
- Accountant readiness contains no unresolved duplicate or undated-review issue.

### High — H-02: Unseen-invoice OCR coverage is not yet proven

The earlier ten-file verification batch consisted of exact copies of already approved documents, so populated review data could safely reuse stored evidence. This proves duplicate handling and recovery, but not reading quality for ten genuinely unseen restaurant invoices across all target layouts.

Why it blocks the pilot:

Invoice reading is the first trust event. A first restaurant pilot should not depend only on known-document reuse.

Resolution:

Run a clean acceptance batch of new invoices representing scanned PDFs, phone photos, Hebrew, English, multi-page invoices, and poor-but-realistic lighting. Measure required corrections without changing extraction logic during the run.

Acceptance test:

- Every file reaches a usable review or a calm recoverable state.
- No raw provider, OCR, command, or parser error is visible.
- Required supplier, date, total, invoice number, and product corrections are recorded.

### Medium — M-01: The Feed queue is a local JSON file

The canonical workflow interprets the queue consistently, but queue persistence is still a single local JSON file.

Risk:

- Concurrent browser sessions or interrupted writes are not a supported Alpha workflow.
- Cross-device processing is not supported.

Pilot posture:

Use one Barni device and one active operator during Alpha. This does not block a controlled single-restaurant pilot.

### Medium — M-02: Identity-review backlog reduces comparison coverage

Business Memory currently reports many unresolved identity questions and limited repeated-price coverage.

Risk:

Barni correctly remains silent on comparisons that cannot be trusted, so the first pilot may produce fewer price insights than expected.

Pilot posture:

Set expectations that silence reflects trust, not failure. Resolve only high-impact identity questions during the pilot.

### Medium — M-03: Month readiness depends on invoice dates

Open invoices without dates cannot be assigned to an accounting month. Accountant Workspace reports them, but cannot infer their month safely.

Risk:

The owner may expect a month to be complete while undated invoices still await review.

Acceptance test:

- All pilot invoices have a confirmed date before the monthly export is declared ready.

### Low — L-01: SQLite connection warnings remain in tests

The suite passes, but existing services emit `ResourceWarning`s for connections not explicitly closed by some legacy read paths.

Risk:

Low for a single-user Alpha session, but undesirable for long-running reliability and future concurrency.

Resolution:

Audit connection ownership separately without mixing it into Golden Path behavior changes.

### Low — L-02: Internal legacy code still exists

Legacy upload, Knowledge, Recipes preview, migration, diagnostics, and other operational implementations remain in the repository.

Risk:

They are hidden from customers but continue to increase maintenance surface and architectural ambiguity.

Resolution:

After Alpha stabilization, inventory consumers and retire unused paths through a separate approved cleanup with compatibility checks.

## Final Assessment

The implemented Golden Path now fails safely, explains success, and moves approved information through one trusted lifecycle into Memory, Search, Insights, and Export.

The next pilot action should not be another feature sprint. It should be:

1. resolve or isolate the existing open pilot queue;
2. run genuinely unseen restaurant invoices;
3. complete the full flow with the restaurant owner;
4. record corrections, hesitation, and export readiness.

Only evidence from that clean real-world pass should decide whether Barni Alpha is ready for unattended restaurant use.
