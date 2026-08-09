# BAR-ALPHA Pilot Checklist

## Purpose

This document defines the acceptance criteria Barni Alpha must satisfy before the first real restaurant pilot. The pilot build passes only when the core journey is trustworthy with real restaurant data:

`Upload → Review → Approve → Learn → Find → Understand → Export`

Record each check as **Pass**, **Fail**, **Blocked**, or **Not applicable**, with the date, tester, build identifier, restaurant dataset, and supporting evidence. A blocked item does not count as a pass.

## 1. Installation & Startup

### Checklist

- [ ] A clean installation completes using the documented setup process.
- [ ] The application starts without manual database repair or source-code changes.
- [ ] Database migrations complete successfully on a new database.
- [ ] Database migrations complete successfully on a copy of an existing Alpha database.
- [ ] Restarting the application does not rerun destructive or duplicate migrations.
- [ ] No critical exception appears during startup or first navigation.
- [ ] Existing invoices, suppliers, products, identity decisions, and approval states remain intact.
- [ ] The application clearly explains any recoverable configuration or startup problem.
- [ ] A failed startup does not partially corrupt the database.

### Evidence to record

- Build and database schema versions.
- Startup command and elapsed startup time.
- Migration log or result.
- Record counts before and after migration.
- Any warnings, errors, or manual intervention.

### Pass criteria

Pass when both a clean installation and an upgrade using representative existing data start successfully, preserve all existing records, and produce no critical runtime error.

## 2. Feed Barni

Test with clear invoices, imperfect scans, known suppliers, new suppliers, repeated products, and a duplicate document.

### Checklist

- [ ] A supported invoice file can be uploaded.
- [ ] Upload progress and processing state are understandable.
- [ ] OCR completes or fails calmly with a useful recovery message.
- [ ] A processed invoice enters the canonical review workflow exactly once.
- [ ] The review shows Barni's evidence-backed understanding before editable data.
- [ ] Extracted values remain editable where the current product allows editing.
- [ ] Exact duplicate detection identifies a previously stored invoice.
- [ ] Duplicate handling does not create conflicting invoices or business facts.
- [ ] Uncertain supplier, product, unit, or package identities enter Identity Review when appropriate.
- [ ] Barni does not silently merge uncertain identities.
- [ ] Identity confirmation, rejection, merge, split, rename, and undo behave as currently supported.
- [ ] Approval succeeds through the canonical invoice lifecycle.
- [ ] Repeating or retrying approval does not duplicate learning.
- [ ] The approved invoice leaves Pending Review.
- [ ] Business Memory updates immediately after approval.
- [ ] Search can find the approved invoice immediately.
- [ ] Accountant Workspace reflects the invoice's readiness immediately.

### Evidence to record

- Source filename and resulting invoice ID.
- Lifecycle state before and after approval.
- Duplicate outcome, when applicable.
- Identity Review candidate and decision IDs, when applicable.
- Business Memory changes caused by approval.
- Search and Accountant Workspace verification.

### Pass criteria

Pass when every test invoice follows one consistent lifecycle, failures are recoverable, approval is idempotent, and all dependent product surfaces reflect the same result without restarting or repairing data.

## 3. Search

Use both English and Hebrew queries where representative data exists.

### Checklist

- [ ] Search by exact supplier name returns the correct invoices.
- [ ] Search by a supplier alias returns results connected to the canonical supplier.
- [ ] Search by product name returns invoices containing that product.
- [ ] Search by product alias or language variation works when the identity is confirmed.
- [ ] Search by complete invoice number returns the correct invoice.
- [ ] Search by a meaningful partial invoice number behaves consistently.
- [ ] Search by supported date format returns the correct period or invoices.
- [ ] Search summaries accurately describe the returned results.
- [ ] A zero-result search produces a clear, calm empty state.
- [ ] Search does not claim a match that is absent from the results.
- [ ] The source invoice opens from a result or evidence link.
- [ ] Returning from invoice detail preserves a useful Search state.
- [ ] Advanced filters preserve all existing behavior.
- [ ] Recent invoices do not conflict with active search results.

### Evidence to record

- Query, filters, expected record IDs, and actual record IDs.
- Summary displayed for each query.
- Screenshot or recording of source opening.
- Any Hebrew, English, or mixed-language limitation.

### Pass criteria

Pass when all supported lookup types return the expected stored records, summaries match the result set, and every displayed source can be opened reliably.

## 4. Business Memory

### Checklist

- [ ] Each canonical supplier has a coherent invoice history.
- [ ] Supplier aliases resolve to the correct canonical supplier.
- [ ] Each canonical product has a coherent purchase history.
- [ ] Product aliases resolve to the correct canonical product.
- [ ] Price history uses comparable Business Facts rather than unsafe raw-line comparisons.
- [ ] Different units, packages, currencies, and VAT bases are compared only when supported.
- [ ] Rejected price comparisons explain why they are not comparable.
- [ ] Every displayed price conclusion links to its supporting invoice lines or invoices.
- [ ] Evidence links open the correct source invoice.
- [ ] Identity Review decisions are reflected throughout Business Memory.
- [ ] Undoing an identity decision restores the previous relationships without losing source records.
- [ ] No supplier or product appears duplicated because of a confirmed alias.

### Evidence to record

- Canonical entity IDs and aliases tested.
- Historical invoice and invoice-line IDs.
- Comparable and rejected price examples.
- Identity decision and undo results.

### Pass criteria

Pass when histories are internally consistent, comparisons are safe and explainable, and confirmed identity decisions produce the same identity across every relevant record.

## 5. Insights

### Checklist

- [ ] Every visible insight has a structured claim and supporting evidence.
- [ ] Every evidence reference belongs to the active business.
- [ ] No insight states a fact that cannot be traced to stored data.
- [ ] Price changes use trusted Comparable Price Facts.
- [ ] Price-change evidence includes both current and previous observations.
- [ ] Duplicate conclusions link to the relevant stored invoices.
- [ ] Identity uncertainty remains uncertainty and is not presented as fact.
- [ ] Extraction confidence is not presented as business certainty.
- [ ] Different confidence types are not silently averaged or mixed.
- [ ] Weak observations remain silent.
- [ ] No more than the intended number of useful insights appears.
- [ ] When nothing meaningful changed, the empty or quiet state is clear.
- [ ] Insight language is concise, calm, and free of OCR, parser, or database terminology.

### Evidence to record

- Claim type and producer version.
- Confidence type and qualitative status.
- Source invoice and line IDs.
- Data values supporting the conclusion.
- Reviewer assessment of usefulness and truthfulness.

### Pass criteria

Pass when every conclusion is supported, correctly scoped, understandable, and useful. Any unsupported financial or operational conclusion is a release blocker.

## 6. Accountant Workspace

Test at least one complete month and one incomplete month.

### Checklist

- [ ] Ready invoices match the canonical lifecycle definition.
- [ ] Pending invoices match the same definition used by Feed and Home.
- [ ] Needs Attention and Duplicate states are represented consistently.
- [ ] Monthly counts match the canonical workflow snapshot.
- [ ] Undated unresolved work remains visible and does not produce false readiness.
- [ ] A newly approved invoice appears in the correct month immediately.
- [ ] Export includes exactly the intended ready invoices.
- [ ] Export excludes unresolved invoices unless the existing workflow explicitly permits them.
- [ ] Exported invoice metadata matches the source records.
- [ ] Monthly readiness does not claim completion while blocking work remains.
- [ ] Repeating an export does not change invoice state or duplicate business knowledge.

### Evidence to record

- Month and expected status counts.
- Exported invoice IDs and filenames.
- Excluded invoice IDs and reasons.
- Readiness before and after resolving pending work.

### Pass criteria

Pass when status counts match every other page, export contents match readiness exactly, and a restaurant owner can distinguish complete from incomplete monthly work without interpretation.

## 7. UX

### Navigation

- [ ] The primary workflow is discoverable without explanation.
- [ ] Page names and destinations are consistent.
- [ ] Back and return actions behave predictably.
- [ ] No dead navigation item or placeholder is visible.

### Loading

- [ ] Operations longer than one second provide appropriate feedback.
- [ ] Loading does not create duplicate submissions.
- [ ] The interface does not appear frozen during OCR, approval, learning, Search, or export.

### Errors

- [ ] User-facing errors explain what happened and what to do next.
- [ ] Normal UI never exposes stack traces or implementation terminology.
- [ ] Retrying a recoverable failure is safe.

### Empty states

- [ ] Every core page has a purposeful empty state.
- [ ] Empty states contain no empty tables, fake data, or inactive controls.
- [ ] The next useful action is clear.

### Button consistency

- [ ] Each screen has one visually clear primary action.
- [ ] Identical actions use consistent labels and visual treatment.
- [ ] Destructive or consequential actions are distinguishable and reversible where required.
- [ ] Buttons cannot accidentally perform the same action twice.

### Language consistency

- [ ] Barni uses short, calm, professional language.
- [ ] The interface responds gracefully to Hebrew, English, and mixed business data.
- [ ] Technical confidence, OCR, parser, schema, and database terminology stay out of normal UI.
- [ ] Missing data uses meaningful language rather than symbols such as `Invoice #—`.

### Responsiveness

- [ ] Core workflows are usable on the supported desktop width.
- [ ] Narrow layouts do not overlap, clip, or hide required actions.
- [ ] Invoice preview and supporting data remain navigable at narrow widths.

### Performance

- [ ] Startup, navigation, Search, invoice opening, and approval meet the recorded Alpha performance budget.
- [ ] Search interaction feels immediate on the pilot dataset.
- [ ] No operation performs visibly repeated work without reason.
- [ ] Performance does not degrade materially after repeated uploads or page reruns.

### Pass criteria

Pass when a first-time restaurant owner completes the demo flow without product-team intervention, no critical content is inaccessible, and errors or delays never leave the user uncertain about system state.

## 8. Trust

### Checklist

- [ ] Feed, Home, Business Memory, Search, and Accountant Workspace show matching invoice counts.
- [ ] One invoice has one canonical customer-facing lifecycle state at a time.
- [ ] No page invents its own status interpretation.
- [ ] Approved invoices do not remain pending.
- [ ] No invoice exists without a reachable source record or deliberate documented reason.
- [ ] Every trusted claim contains evidence.
- [ ] Every evidence reference resolves to the correct business and source.
- [ ] No evidence from another business can be attached to a claim.
- [ ] Every trusted price comparison includes both relevant invoice lines.
- [ ] Business Fact fingerprints prevent duplicate materialization.
- [ ] Approval retries do not duplicate facts, memory, or stories.
- [ ] Identity decisions remain explainable and reversible.
- [ ] No uncertain identity is silently merged.
- [ ] Database backup and recovery procedures are tested on representative pilot data.

### Release blockers

Any of the following is an automatic failure:

- Data loss or corruption.
- Conflicting lifecycle states or counts.
- An unsupported financial conclusion.
- Evidence opening the wrong invoice.
- Duplicate learning caused by retry or rerun.
- A silent uncertain identity merge.
- Export omitting a ready invoice or including an unintended unresolved invoice.

## 9. Demo Flow

Conduct the test with a restaurant owner who has not previously used Barni. Use their own invoice where consent and handling requirements permit.

| Task | Expected outcome | Alpha time target |
|---|---|---:|
| Upload an invoice | The document is accepted and processing begins without assistance | 30 seconds of user effort |
| Review and approve | The owner understands Barni's conclusion, corrects any issue, and approves | 2 minutes |
| Find the invoice | Search returns the invoice and its source opens | 30 seconds |
| Understand a price change | The owner identifies what changed, by how much, and which invoices support it | 1 minute |
| Export for the accountant | The owner understands readiness and creates the correct export | 2 minutes |

Expected total active user time: **6 minutes or less** after OCR processing. The daily upload-review portion should remain within the existing goal of **less than 3 minutes**.

### Observation protocol

Record:

- Completion time for each task.
- Misclicks, backtracking, and requests for help.
- Any term the participant does not understand.
- Whether the participant verifies evidence voluntarily.
- Whether the displayed insight changes understanding or prompts a useful action.
- The participant's trust rating from 1 to 5 after the flow.
- The participant's answer to: “Would you use Barni again for your next invoices?”

Do not coach during the timed attempt unless continuation is impossible. Record any assistance as a failed independent-completion attempt.

## 10. Pilot Success Criteria

### Build-level acceptance

The Alpha build is eligible for a pilot only when:

- All release blockers are resolved.
- Every critical checklist item passes on a clean database and an upgraded representative database.
- The full automated regression suite passes.
- At least five representative real invoices complete the full lifecycle.
- At least one duplicate and one uncertain identity scenario are validated.
- Search passes supplier, product, invoice-number, and date scenarios.
- Every sampled insight is traceable to correct evidence.
- Accountant export contents match canonical readiness.
- No unresolved P0 defect remains.

### Participant-level acceptance

A pilot session passes when:

- The restaurant owner understands Barni's purpose without a verbal product explanation.
- The owner completes upload, review, approval, Search, evidence review, and export with no more than one minor prompt.
- The upload-review-learn loop feels natural to the participant.
- The owner correctly explains the invoice's final status.
- The owner trusts the Search result and can open its source.
- Business Memory is perceived as useful rather than as an archive.
- At least one genuine, evidence-backed business insight is discovered from the restaurant's data.
- The owner can explain why that insight is true by following its evidence.
- The complete demo flow takes six minutes or less of active user time.
- The owner gives trust a rating of at least 4 out of 5.
- The owner says they would continue using Barni.

### Pilot-level acceptance

The first pilot succeeds when:

- No participant experiences data loss, corrupted state, or an unsupported conclusion.
- At least 80% of participants pass the participant-level flow.
- At least 80% say they would continue using Barni.
- At least 70% discover one genuine useful insight using their own data.
- Median active completion time is six minutes or less.
- Search success is at least 95% across the agreed supported query set.
- All exported invoice sets match the expected canonical readiness set.
- Every trust-related defect is reviewed before adding more pilot restaurants.

If the sample contains fewer than five independent restaurant owners, report raw results and do not present percentages as statistically meaningful.

## Known Risks Before Alpha

- Alpha uses a local single-business scope; multi-tenant isolation is not yet proven.
- Historical evidence uses compatibility adapters until a controlled typed-evidence backfill exists.
- Archived-document integrity references are modeled but are not yet universally populated.
- OCR quality depends on source-document clarity and requires real Hebrew and mixed-language validation.
- Existing database-connection resource warnings require monitoring even when tests pass.
- Real-world units, package sizes, VAT treatments, credit notes, and supplier naming may exceed current normalization coverage.
- Pilot backup, recovery, privacy, retention, and access procedures must be operationally rehearsed.
- Performance limits must be measured against the pilot restaurant's actual invoice volume.

## Nice-to-Have Items After Alpha

- Faster batch review for repeated, high-confidence invoice patterns.
- Better evidence highlighting inside original documents.
- Controlled historical evidence backfill and integrity hashing.
- More refined Hebrew and mixed-language copy.
- Pilot analytics for workflow completion, errors, and abandonment.
- Improved accessibility testing and keyboard navigation.
- More convenient export history and audit presentation.

These items must not delay Alpha unless testing shows they block comprehension, trust, or the core workflow.

## Items Intentionally Postponed Until Beta

- Multi-tenant platform architecture and organization administration.
- New business data sources beyond invoices.
- Predictions and automated business actions.
- Proactive notifications across external channels.
- Full natural-language Conversation Layer.
- Broad Attention Engine distribution across the product.
- Automated supplier recommendations or switching advice.
- Inventory, payroll, cash-flow, CRM, POS, and banking integrations.
- Arbitrary dashboards, extensive customization, and ERP-style workflows.
- Gamification, artificial progress systems, or unsupported Barni evolution.

Beta work may begin only after Alpha proves that Barni can safely turn real invoice data into trusted understanding.
