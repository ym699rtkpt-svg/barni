# Barni Alpha Readiness Audit

## Audit perspective

I evaluated Barni as a first-time restaurant owner, not as a developer. I began with the running product and did not inspect implementation before using it.

Audit date: 9 August 2026  
Build shown in the product: Alpha 0.3  
Pilot target: Thursday  
Overall readiness verdict: **No-go for an unassisted restaurant pilot**

The product contains a promising core idea and a calm visual foundation, but the primary promise does not survive the complete customer journey today. Ten real archived restaurant invoices were accepted and then all ten failed reading. Search could find a known invoice number, but the visible product and supplier examples returned nothing. Business Memory did not let me inspect supplier, product, or price history. Accountant export failed after preparation was requested.

The pilot should not proceed as an unassisted customer experience until the upload-reading-review path and accountant export pass with the exact pilot files and environment.

## Method and boundaries

I performed the following through the rendered application:

1. Entered Barni from the landing screen.
2. Uploaded ten existing restaurant invoice files as one batch.
3. Started invoice reading and waited for completion.
4. Entered the resulting review flow.
5. Assessed whether safe approval was possible.
6. Searched using the visible product and supplier suggestions.
7. Searched for a known invoice number.
8. Opened a past invoice from Recent Invoices.
9. Reviewed Business Memory.
10. Read Insights.
11. Opened Accountant Workspace and attempted to prepare an export.

I did not approve the ten unread invoices. Every extracted key field was blank, so approval would have taught Barni unsupported information and damaged trust. This was treated as a product-flow blocker, not as a completed approval.

No source code was changed during this audit.

## Task outcomes

| Customer task | Outcome | Result |
|---|---|---|
| Upload ten invoices | All ten files were accepted in one batch | Pass |
| Read ten invoices | All ten ended as “could not be read” | Fail |
| Review invoices | Review opened, but key fields were blank | Partial |
| Approve invoices | Unsafe because no reliable invoice data was available | Blocked |
| Search for products | “Milk” returned no matches; no real product names were exposed elsewhere for recovery | Fail |
| Search for suppliers | “Tnuva” and a visible stored Hebrew supplier returned no matches | Fail |
| Find a past invoice | Invoice number `841` returned results; Recent Invoices also opened invoice 841 | Pass |
| Check Business Memory | Overview loaded, but usable supplier/product/price histories were not exposed | Partial |
| Read Insights | One identity-review story appeared; most of the page was aggregate reporting | Partial |
| Export for accountant | Package preparation ended in a generic page error | Fail |

## First-time customer impression

The landing experience is calm and understandable. “Your Business Memory” creates the right expectation. Home then communicates that Barni already knows a substantial amount about the business and gives a clear route to Feed Barni.

Confidence drops quickly after that:

- Internal and pilot navigation is visible alongside customer pages.
- The product says it knows 189 products but cannot help me choose a real product to search for.
- Ten invoices all fail together without a useful diagnosis.
- Review asks me to complete blank records without enough guidance.
- Business Memory feels like a reporting dashboard rather than navigable memory.
- Accountant readiness contradicts itself and export fails.

As a restaurant owner, I would conclude that Barni looks thoughtful but is not yet safe enough for daily operational dependence.

## Hesitation log

Every item below caused more than five seconds of hesitation or prevented continuation.

### H1 — What is “Read invoices” going to do?

- **What happened:** After selecting ten files, the only primary action was “Read invoices.”
- **Why it is confusing:** I could not tell whether the files were already uploaded, whether this starts OCR, whether it saves them, or whether review begins automatically.
- **Severity:** Medium
- **Proposed UX fix:** Rename the action to “Upload and review 10 invoices.” Add one short line explaining the next state: “Barni will read them, then show anything that needs your review.”

### H2 — Batch processing gave no useful time expectation

- **What happened:** Reading ten invoices took roughly one minute before a final result appeared.
- **Why it is confusing:** I did not know whether Barni was still working, stuck, or processing one invoice at a time. The batch had no persistent progress such as `3 of 10`.
- **Severity:** High
- **Proposed UX fix:** Show per-file progress with completed, processing, and failed counts. Keep the user informed without technical OCR language.

### H3 — All ten invoices failed at once

- **What happened:** Barni reported “10 invoices could not be read.”
- **Why it is confusing:** These were ordinary archived restaurant documents in several supported formats. No file-specific reason or next step was shown before review.
- **Severity:** Critical
- **Proposed UX fix:** Validate the exact Thursday invoice set before the pilot. In the product, separate transient processing failure from low-confidence extraction, identify each affected file, offer a safe retry, and explain whether a clearer copy is required.

### H4 — “Barni learned something new” contradicted total failure

- **What happened:** The completion state was headed “Barni learned something new,” immediately followed by “10 invoices could not be read.”
- **Why it is confusing:** Failure is presented as learning. I cannot tell whether Business Memory changed despite the message that nothing enters memory before approval.
- **Severity:** High
- **Proposed UX fix:** Reserve learning language for successful, approved knowledge. Use a calm failure heading such as “I need your help with these invoices.”

### H5 — Review opened with every key field blank

- **What happened:** Supplier, date, invoice number, and total were empty. Products contained no useful extracted information.
- **Why it is confusing:** Barni asks me to review, but there is almost nothing to review. Completing ten invoices becomes manual data entry.
- **Severity:** Critical
- **Proposed UX fix:** Do not route a fully unread document into the normal review experience. Present recovery first: retry reading, replace the file, open the original beside a focused minimum-entry form, or defer it. Clearly distinguish “review Barni's understanding” from “enter the entire invoice manually.”

### H6 — Approval remained visually available despite insufficient evidence

- **What happened:** “Approve & Teach Barni” was visible on an invoice with blank identity, date, number, total, and products.
- **Why it is confusing:** The strongest action invites me to teach Barni information it does not have. I do not know whether blank data will enter memory.
- **Severity:** Critical
- **Proposed UX fix:** Disable approval until minimum trustworthy fields are present, or change the action to an explicit exception decision with a clear consequence. Never let the primary CTA imply safe learning when evidence is absent.

### H7 — Reviewing ten failed invoices felt like an unbounded queue

- **What happened:** Review showed “Invoice 1 of 10,” but no batch summary or quick classification of which files shared the same failure.
- **Why it is confusing:** I could not estimate whether each invoice would require the same full manual correction.
- **Severity:** High
- **Proposed UX fix:** Add a compact batch overview before review: ready, needs one detail, unread, duplicate. Let the owner address the highest-value recoverable items first.

### H8 — Suggested product and supplier searches were dead ends

- **What happened:** The visible chips “Milk” and “Tnuva” both produced “I couldn't find any matching invoices.”
- **Why it is confusing:** Suggested searches look like guaranteed examples. Their failure makes Search appear empty or broken, even though Barni says it knows 66 invoices, 42 suppliers, and 189 products.
- **Severity:** High
- **Proposed UX fix:** Generate suggestions from actual searchable memory. Never show an example as a clickable chip unless it returns a useful result in the current business.

### H9 — Searching a visible stored supplier returned no result

- **What happened:** Searching the exact supplier name shown on the newest recent invoice returned no matching invoices.
- **Why it is confusing:** The invoice is visibly present directly below Search, yet Barni says it cannot find that supplier.
- **Severity:** Critical
- **Proposed UX fix:** Treat exact stored supplier names and canonical aliases as a release-contract test. A supplier displayed anywhere in Barni must be searchable using the displayed text.

### H10 — Product search could not be recovered

- **What happened:** “Milk” failed, and Business Memory did not expose product names I could use to try a known real product.
- **Why it is confusing:** Barni reports 189 products but offers no path to see or search one confidently.
- **Severity:** High
- **Proposed UX fix:** Ensure at least the most recent real products are discoverable from Business Memory and use those same canonical names in Search suggestions.

### H11 — Invoice number search returned an unexplained extra match

- **What happened:** Searching `841` returned invoice `841` and invoice `48413`.
- **Why it is confusing:** A first-time user cannot see why `48413` is relevant. The summary only says two invoices matched.
- **Severity:** Medium
- **Proposed UX fix:** Show the matched field or snippet for non-obvious matches, such as “OCR text contains 841.” Rank the exact invoice-number match first and label it as exact.

### H12 — Past invoice detail lacked a real preview

- **What happened:** Opening invoice 841 showed metadata and a “Download PDF” action, but no contained preview was visible.
- **Why it is confusing:** I expected to verify the original without leaving or downloading from the current context.
- **Severity:** Medium
- **Proposed UX fix:** Show a contained first-page preview with an explicit full-document action. Keep Barni's conclusion primary while making evidence immediately verifiable.

### H13 — Approved invoice copy still sounded unresolved

- **What happened:** Invoice 841 was marked Approved, while Barni said some details still needed careful checking and that it had not seen a previous invoice from the supplier.
- **Why it is confusing:** I cannot tell whether Approved means trusted, stored, or still incomplete. “I haven't seen a previous invoice” is also not inherently a problem.
- **Severity:** High
- **Proposed UX fix:** Separate lifecycle status from current attention. State the concrete unresolved detail, or show a calm approved state. Do not frame ordinary first history as a warning.

### H14 — Business Memory presented scale, not usable memory

- **What happened:** Business Memory showed counts, charts, categories, and recent learning, but no visible supplier list, product list, or price-history drill-down.
- **Why it is confusing:** I came to understand who I buy from and what prices changed. The page tells me how much data exists instead.
- **Severity:** High
- **Proposed UX fix:** Make the first view answer practical memory questions: recent suppliers, recent products, price changes, and items needing identity help. Every summary should lead to supporting history.

### H15 — Ninety-eight identity questions felt overwhelming

- **What happened:** Business Memory announced 98 identity questions and offered “Help Barni learn.”
- **Why it is confusing:** The workload sounds enormous and undifferentiated. I cannot tell what blocks a useful comparison today.
- **Severity:** High
- **Proposed UX fix:** Surface only the highest-impact few, explain what each unlocks, and hide the backlog total from the default owner experience.

### H16 — Business Memory supplier counts contradicted Insights

- **What happened:** Business Memory said 42 suppliers; Insights showed 50 suppliers.
- **Why it is confusing:** I do not know which number represents my business. This directly undermines the claim of one trusted memory.
- **Severity:** Critical
- **Proposed UX fix:** Use one canonical supplier-count definition everywhere. If raw and canonical counts are both necessary, label them explicitly and never present them as the same concept.

### H17 — Insights was mostly another dashboard

- **What happened:** The only clear story was that two identity details needed help. The rest was invoice, supplier, VAT, spending, and top-supplier reporting.
- **Why it is confusing:** “What changed” does not answer what changed. I must interpret charts myself.
- **Severity:** High
- **Proposed UX fix:** Lead with one to three evidence-backed changes in plain language. Move aggregate reporting behind supporting context or omit it until it explains something meaningful.

### H18 — Accountant readiness contradicted itself

- **What happened:** Readiness said “No duplicate invoices,” then immediately said four duplicate invoices need attention. It also showed seven duplicates in the shared workflow counters.
- **Why it is confusing:** I cannot know whether the month is safe to export or which duplicate count applies.
- **Severity:** Critical
- **Proposed UX fix:** Create one unambiguous readiness verdict. Every check must use the same month scope and canonical status source, with consistent counts and direct links to blocking records.

### H19 — Month selection was unclear

- **What happened:** Accountant Workspace showed “Month” and “Selected Month,” but the selected value was not understandable in the rendered flow.
- **Why it is confusing:** I cannot confirm which accounting month contains the 34 included documents.
- **Severity:** High
- **Proposed UX fix:** Display the active month prominently in the heading and package filename. Make month selection explicit before calculating readiness.

### H20 — Export failed after the final action

- **What happened:** “Prepare Accountant Package” ended with “Barni ran into a problem on this page.” No package was available.
- **Why it is confusing:** This occurs at the moment of highest commitment, after Barni says 34 documents are ready.
- **Severity:** Critical
- **Proposed UX fix:** Treat package creation as a Thursday release blocker. Add an end-to-end test using the actual pilot month and files, preserve the page state on failure, and give a calm retry message without losing the readiness context.

### H21 — Customer navigation exposed internal product structure

- **What happened:** The sidebar included Knowledge, Recipes, Pilot Dashboard, and an Internal tools expander. The application shell also exposed “Deploy.”
- **Why it is confusing:** I am unsure which pages are for me and which are unfinished or operational. It makes Alpha feel like a development environment.
- **Severity:** Medium
- **Proposed UX fix:** Use a pilot-safe navigation profile containing only Home, Feed Barni, Search, Business Memory, Insights, and Accountant. Hide deployment and internal tools from restaurant owners.

## Issues ranked by Thursday pilot impact

### P0 — Must resolve before an unassisted pilot

1. **Ten of ten real invoices could not be read.** The primary workflow has a 0% success rate on the tested batch.
2. **Normal review cannot safely recover fully unread invoices.** Blank records still offer “Approve & Teach Barni.”
3. **Accountant export fails.** The final operational outcome cannot be completed.
4. **Accountant readiness contradicts itself about duplicates.** The owner cannot trust whether export is safe.
5. **Exact visible supplier search fails.** Barni cannot reliably retrieve memory it visibly displays.
6. **Supplier counts conflict between Business Memory and Insights.** The product presents multiple truths.

### P1 — Resolve before asking the owner to use Barni independently

7. **Suggested searches are not grounded in the restaurant's actual data.** The first Search interaction creates a false failure.
8. **Batch progress and failure recovery are inadequate.** The owner cannot understand or manage ten documents efficiently.
9. **Business Memory lacks usable supplier, product, and price-history paths.** It communicates volume rather than understanding.
10. **Identity Review announces 98 questions without prioritizing owner value.** The product creates perceived work instead of help.
11. **Insights does not answer “What changed?”** It falls back to dashboard interpretation.
12. **Approved invoice messaging remains ambiguous.** Status and attention are not reconciled in the customer's language.
13. **Accountant month context is unclear.** Package scope is not confidently understood.

### P2 — Important polish after the blockers

14. Clarify “Read invoices” and explain the next step.
15. Explain why non-obvious Search results matched.
16. Add a contained original-invoice preview.
17. Hide Internal tools, Pilot Dashboard, unfinished modules, and deployment chrome.
18. Ensure failure and success headings never contradict each other.

## What worked

- The landing page communicates “Business Memory” clearly.
- The visual language is calm, warm, and consistent.
- Ten files can be selected and accepted together.
- Shared invoice counters were consistent across Home, Feed, and Accountant during the observed flow: Pending Review 1, Learning 0, Approved 66, Needs Attention 13, Duplicates 7.
- The batch completion correctly stated that nothing enters Business Memory before approval.
- Invoice-number Search via Enter worked and produced a meaningful count summary.
- Recent Invoices showed five compact, readable cards with good missing-number language.
- Clicking a recent invoice replaced the list with a dedicated detail state.
- Invoice detail clearly displayed supplier, invoice number, date, total, and Approved status.
- Accountant Workspace explained that package generation is local and does not transmit data.

These strengths are worth preserving. They do not offset the P0 failures in ingestion, trust, Search, and export.

## Thursday pilot recommendation

### Recommended decision

**Do not run Thursday as an unassisted real-customer pilot on the current build.**

Use one of these two formats only:

1. Delay the pilot until every P0 passes with the exact restaurant files and month; or
2. Reframe Thursday as a supervised diagnostic session with explicit consent that invoice reading and export may fail.

Do not present the current build as ready for routine invoice handling.

### Minimum retest gate

Before the restaurant owner receives the build:

- Process the exact ten pilot invoices successfully or provide a proven recovery path for each failure.
- Demonstrate that an unread invoice cannot be approved into Business Memory accidentally.
- Approve at least five correctly extracted invoices end to end.
- Confirm immediate updates in Home, Search, Business Memory, and Accountant Workspace.
- Search successfully for one displayed supplier, one displayed product, one invoice number, and one date.
- Open supporting evidence from Search, Memory, and Insights.
- Produce and inspect a complete accountant ZIP for the selected month.
- Reconcile supplier and duplicate counts across all pages.
- Remove customer access to internal and deployment controls.

## Product readiness score

| Area | Score | Reason |
|---|---:|---|
| First impression | 7/10 | Calm and understandable, but development controls reduce confidence |
| Feed and processing | 2/10 | Batch selection works; all ten reads failed |
| Review and approval | 3/10 | Narrative is thoughtful; recovery and safe approval are inadequate |
| Search | 5/10 | Invoice-number retrieval works; supplier/product discovery does not |
| Business Memory | 4/10 | Strong data volume, weak navigable understanding |
| Insights | 4/10 | Evidence-oriented framing exists, but useful changes are scarce |
| Accountant Workspace | 2/10 | Readiness conflicts and export fails |
| Trust | 3/10 | Several good safeguards, but contradictory truths remain visible |

Overall Alpha pilot readiness: **35/100**

## Final owner judgment

I understand what Barni wants to become: a quiet memory that helps me understand my restaurant. I can already see moments of that product in the language, recent invoices, and evidence-oriented review.

Today, however, I would not trust it with Thursday's invoice workflow. The system asks me to trust learning after it fails to read the documents, shows different supplier truths in different places, and cannot complete the accountant export. The highest-value next step is not more intelligence or more pages. It is making one real batch complete the entire journey safely and predictably.
