# Barni Pilot Readiness Checklist

## Purpose

This checklist records trust risks found during a read-only review of Barni before its first live restaurant pilot. It covers every routed product page, the landing experience, shared navigation, upload and review workflows, empty and loading states, wording, spacing, typography, and unfinished UI.

No application behavior was changed during this audit.

## Severity and effort

- **Critical:** Can show unsupported information, permit an unsafe workflow, expose unfinished product behavior, or materially damage trust during the pilot.
- **High:** Likely to confuse the restaurant manager, expose internal implementation, or make a core workflow feel unreliable.
- **Medium:** Noticeable inconsistency or friction that weakens clarity and perceived quality.
- **Low:** Polish or maintainability issue unlikely to block the pilot by itself.

Estimated implementation effort assumes one developer familiar with the codebase:

- **XS:** Less than half a day.
- **S:** Approximately half to one day.
- **M:** Approximately two to three days.
- **L:** More than three days or requiring coordinated workflow changes and testing.

# Critical

## C-01 — Recipes displays hard-coded example data as if it were real

- **Description:** The main Recipes page constructs a fixed Mozzarella, Tomato, and Burger Bun recipe and displays a calculated cost without identifying it as sample data or letting the user choose a stored recipe. There is no intentional empty state.
- **Why it matters:** A pilot restaurant can reasonably interpret the displayed cost as knowledge learned from its own business. That violates Barni's evidence-first promise and can immediately undermine trust.
- **Suggested improvement:** Do not expose the page in primary navigation until it uses stored recipe data. If the route must remain available, replace the example with a calm “Recipes are not available in this pilot yet” state. Never present sample costs as business facts.
- **Estimated implementation effort:** S.

## C-02 — Missing price history is labeled “unchanged” on Knowledge

- **Description:** Supplier product rows default to `⚪ unchanged` before checking whether a previous valid purchase exists. Products with one purchase or incomplete price data can therefore look stable.
- **Why it matters:** “Unchanged” is a business conclusion. A first purchase is not a trend, and BAR-003 explicitly requires Barni to distinguish no change from no comparable history.
- **Suggested improvement:** Add an explicit neutral state such as “Not enough history.” Assign “unchanged” only when two valid comparable prices exist and the calculated difference is zero. Verify summary counts exclude products without a comparison.
- **Estimated implementation effort:** S.

## C-03 — Knowledge can display a 0.00% average change without comparable history

- **Description:** When no valid price changes exist, the Products summary displays `Average Change 0.00%` rather than an unavailable or insufficient-history state.
- **Why it matters:** This creates false precision and implies stable pricing when Barni may only lack history.
- **Suggested improvement:** Display “Unavailable” or “Not enough history” until at least one valid comparison exists. Keep missing comparisons out of the average and explain the coverage basis.
- **Estimated implementation effort:** XS.

## C-04 — Home can say “Everything looks calm” while also saying history is insufficient

- **Description:** When approved invoices exist but there are no valid comparable product movements, the hero can state that everything looks calm while Barni Today states that more repeat purchases are needed.
- **Why it matters:** The two messages contradict each other. Absence of comparable evidence does not prove that the business is calm.
- **Suggested improvement:** Use one shared, evidence-aware status result. When comparison coverage is insufficient, say Barni has stored activity but needs more history before assessing price movement.
- **Estimated implementation effort:** S.

## C-05 — Edited uncertain invoices become “ready” without revalidation

- **Description:** Saving edits in Review Queue changes the queue status to ready without rerunning normalization, validation, and confidence/review checks on the edited document.
- **Why it matters:** A required field can remain missing or totals can remain inconsistent while the UI signals that the invoice is ready. This weakens the core human-approval safety boundary.
- **Suggested improvement:** Revalidate the edited document before changing status. Keep it in Needs Review while supported validation issues remain, update the visible reasons, and show what still needs attention.
- **Estimated implementation effort:** M.

## C-06 — Processing-error records still expose the approval action

- **Description:** Queue records with `error` status remain selectable and share the same Approve and teach Barni action as successfully extracted records, even when their document payload may be empty or incomplete.
- **Why it matters:** A failed extraction should never look approvable. Accidentally saving an empty or malformed invoice would directly damage Business Memory.
- **Suggested improvement:** Disable approval for processing errors. Offer Retry processing, Replace upload, or Reject. Independently validate at the application-service boundary before any database write.
- **Estimated implementation effort:** M.

## C-07 — Developer and legacy workflows are visible in the pilot sidebar

- **Description:** The main sidebar exposes a Developer expander with dataset scanning, AI experiments, migrations, database health, month closing, legacy upload, and legacy archive pages.
- **Why it matters:** These screens contain file paths, model settings, raw technical output, and state-changing controls. They make the product feel unfinished and create opportunities for accidental data changes during a demo.
- **Suggested improvement:** Hide developer routes behind an explicit development/pilot-admin flag and keep them out of restaurant-manager navigation. Confirm direct route access is also controlled.
- **Estimated implementation effort:** S.

## C-08 — The application exposes two invoice experiences and two storage paths

- **Description:** The current Feed/Search workflow coexists with legacy upload/archive code in `app.py`, including a separate `data/invoices.db` path and different field handling. Both are reachable through the Developer menu.
- **Why it matters:** A pilot operator can upload into the wrong system and then fail to find the invoice in Business Memory. This looks like data loss even when the file was stored elsewhere.
- **Suggested improvement:** Remove legacy routes from pilot access immediately. After compatibility and data ownership are verified, retire or clearly isolate the legacy workflow. Document one canonical upload, archive, and database path.
- **Estimated implementation effort:** M for pilot isolation; L for full consolidation.

# High

## H-01 — Language switches repeatedly within the same workflow

- **Description:** Navigation is mostly English, while Feed, Search, and invoice editing mix Hebrew and English in adjacent titles, actions, table columns, progress messages, and outcomes. Knowledge and Home are mostly English but retain Hebrew captions or invoice metadata.
- **Why it matters:** Mixed language increases scan time and makes the product feel assembled from unfinished parts. It is especially distracting during a guided pilot demonstration.
- **Suggested improvement:** Choose a deliberate pilot language strategy per screen and apply it end to end. Preserve business-source text, but standardize navigation, headings, actions, statuses, validation messages, and table labels.
- **Estimated implementation effort:** M.

## H-02 — Raw validation codes and exception messages are user-facing

- **Description:** Review reasons can expose strings such as `missing_invoice_number`, `amount_mismatch`, provider notes, or raw processing exceptions. Search and Feed can also display exception text directly.
- **Why it matters:** Internal codes do not tell a restaurant manager what to do and can expose implementation details or file paths.
- **Suggested improvement:** Map known validation codes to concise natural-language messages and a specific field. Log raw exceptions in Pilot Mode, while the UI shows a calm explanation and recovery action.
- **Estimated implementation effort:** S.

## H-03 — AI model configuration is exposed in the primary upload flow

- **Description:** Feed includes an “AI model” text input under processing settings, currently populated with a model identifier.
- **Why it matters:** The restaurant manager should not need to choose or understand an AI model. Changing the value can break extraction and makes Barni feel like a developer tool rather than an operations assistant.
- **Suggested improvement:** Remove model selection from the restaurant-facing workflow. Keep provider configuration in protected settings or environment configuration and show only user-relevant processing choices.
- **Estimated implementation effort:** XS.

## H-04 — Duplicate replacement is the visually primary destructive choice

- **Description:** In the duplicate warning card, Replace uses the primary button style while Skip and Keep both are secondary. There is no confirmation step describing what will be replaced.
- **Why it matters:** Visual hierarchy encourages the most destructive option. A mistaken click changes an approved invoice and its product history.
- **Suggested improvement:** Use a neutral decision layout, make Skip the safest default, and require a concise confirmation before Replace. Show the existing and uploaded invoice identifiers, dates, totals, and the exact consequence.
- **Estimated implementation effort:** S.

## H-05 — Landing experience conflicts with the permanent design system

- **Description:** The landing screen uses a dark background, bright orange gradient, glow, hover movement, oversized Enter control, and a full-screen gate. This conflicts with the warm beige/green, no-gradient, no-animation design used after entry.
- **Why it matters:** The first impression feels like a different product and creates an unnecessary step before the manager sees business value.
- **Suggested improvement:** Align the landing experience with the product cockpit or remove the gate for the pilot. Lead directly to the current business state and primary Feed Barni action.
- **Estimated implementation effort:** M.

## H-06 — Missing landing artwork exposes a file-system error

- **Description:** If the hero asset is unavailable, the user sees `assets/barni_landing.png` in an error alert.
- **Why it matters:** A missing decorative asset should not make the product appear broken or expose a developer path during a demo.
- **Suggested improvement:** Provide a resilient branded fallback without an error alert. Log the missing asset for pilot diagnostics.
- **Estimated implementation effort:** XS.

## H-07 — Every page receives a second global Barni title and caption

- **Description:** `app.py` renders a global Barni title and Hebrew caption before page-specific heroes such as Welcome back, Feed Barni, Search, Knowledge, Business Memory, and Pilot Mode.
- **Why it matters:** Duplicate titles weaken the five-second hierarchy, waste vertical space, and produce inconsistent heading levels.
- **Suggested improvement:** Keep brand identity in the sidebar. Let each page own one hero/title and one purpose statement.
- **Estimated implementation effort:** XS.

## H-08 — Insights is visually and linguistically a developer dashboard

- **Description:** The primary Insights route opens “Control Center” with six flat metrics, raw charts/tables, an auto-classify-all button, JSON output, and Hebrew developer-oriented labels.
- **Why it matters:** The screen does not clearly answer “What deserves my attention?” and exposes a bulk mutation alongside insights. It conflicts with the premium cockpit and recommendation patterns used elsewhere.
- **Suggested improvement:** For the pilot, remove the bulk categorization control from the primary Insights page. Lead with at most three evidence-based attention items, then supporting metrics and details. Move maintenance actions behind pilot-admin access.
- **Estimated implementation effort:** M.

## H-09 — Search combines finding information with unrestricted record editing

- **Description:** The Search result screen immediately exposes edit fields and tag mutations alongside the original document, with no clear transition into an edit mode or explanation of audit consequences.
- **Why it matters:** Search is expected to answer “Where is the information I need?” Accidental edits in the same context reduce confidence in stored records.
- **Suggested improvement:** Make document viewing the default. Put editing behind an explicit Edit invoice action, clearly label saved changes, and preserve the visible history/source relationship.
- **Estimated implementation effort:** M.

## H-10 — Pilot feedback wording implies delivery to a team, but storage is local

- **Description:** After submission, Pilot Mode says feedback “was saved for the Barni team,” while the implementation writes to a local JSONL file and does not transmit it.
- **Why it matters:** The restaurant may believe the issue has been received when nobody has collected the local file.
- **Suggested improvement:** State exactly where feedback is stored and define the pilot collection procedure. If automatic delivery is not implemented, say “Saved on this Barni device for the pilot review.”
- **Estimated implementation effort:** XS for wording; M for a reliable collection workflow.

## H-11 — Core data-heavy pages have no intentional loading state

- **Description:** Home, Knowledge, Business Memory, Search, and Ask Barni perform database queries and repeated price-history work without a consistent loading state. Knowledge and Home may run many per-product queries.
- **Why it matters:** During a live demo, an empty or frozen-looking screen can be mistaken for a failure. Repeated reruns amplify this uncertainty.
- **Suggested improvement:** Add concise page-level loading states around application-service calls, cache safe read-only summaries where appropriate, and avoid per-row query patterns. Use natural messages such as “Barni is checking recent purchases.”
- **Estimated implementation effort:** M.

# Medium

## M-01 — Navigation labels and icons are not semantically distinct

- **Description:** Knowledge and Business Memory both use the brain icon. Pilot Mode has no icon. Recipes uses different spacing. “Knowledge” and “Business Memory” are adjacent concepts without supporting distinction.
- **Why it matters:** The manager has to learn product terminology before knowing where to go.
- **Suggested improvement:** Use one consistent label/icon format and clarify purposes: Knowledge for supplier/product history; Business Memory for what Barni has learned. Add brief tooltips only if they reduce ambiguity.
- **Estimated implementation effort:** XS.

## M-02 — Pilot Mode has no clear return path

- **Description:** Pilot Mode records the source page internally but does not show a Back or Return action.
- **Why it matters:** Reporting a problem interrupts the active task and forces the manager to rediscover the previous page in navigation.
- **Suggested improvement:** Add a quiet “Return to [page]” action after submission and near the page header without changing the underlying workflow.
- **Estimated implementation effort:** XS.

## M-03 — Heading hierarchy varies across pages

- **Description:** Pages use a mixture of `st.title`, `st.header`, `st.subheader`, Markdown `##`, `###`, `####`, and `#####`. Similar sections therefore render at different visual weights.
- **Why it matters:** Inconsistent typography makes the application harder to scan and weakens the premium SaaS feel.
- **Suggested improvement:** Define one page-title level, one section-title level, one subsection level, and one caption pattern. Apply them to all pilot-visible pages.
- **Estimated implementation effort:** S.

## M-04 — Reusable card styling is duplicated across pages

- **Description:** Home, Feed, Knowledge, Business Memory, and Search each embed similar CSS with slightly different padding, border, radius, and background values.
- **Why it matters:** Small differences create visible drift, and every polish pass must be repeated in several files.
- **Suggested improvement:** Centralize the approved design tokens and a small set of reusable visual components. Keep page-specific CSS only when a real layout need exists.
- **Estimated implementation effort:** M.

## M-05 — Empty-state treatment varies between captions, info boxes, and bare headings

- **Description:** Empty states use `st.caption`, `st.info`, return early, or leave section headings with no content. Examples include Search results, invoice items/history, Insights charts, Knowledge products, Business Memory, and database pages.
- **Why it matters:** The same absence of data can look informational, broken, or alarming depending on the page.
- **Suggested improvement:** Adopt one calm empty-state component with a short explanation and an optional relevant next action. Avoid alert styling when nothing is wrong.
- **Estimated implementation effort:** S.

## M-06 — Insights can render empty chart sections

- **Description:** The Insights page prints headings for monthly spend, suppliers, categories, and document types even when an individual dataset is empty; some headings can be followed by nothing.
- **Why it matters:** Blank sections look unfinished and make the user question whether data failed to load.
- **Suggested improvement:** Render each section only when data exists. Otherwise show one intentional, section-specific empty message or omit secondary sections entirely.
- **Estimated implementation effort:** XS.

## M-07 — Search statuses and history fields remain developer-facing

- **Description:** Search tables show raw statuses such as `approved`, `review`, and `rejected`. The history tab displays repository column names and raw values without human-friendly formatting.
- **Why it matters:** These labels reveal implementation vocabulary and slow comprehension.
- **Suggested improvement:** Map statuses and history fields to natural language, format dates and money consistently, and explain changes as “Total changed from … to …”.
- **Estimated implementation effort:** S.

## M-08 — Search result interaction requires two separate representations

- **Description:** Results are first grouped into read-only supplier tables, then the user must choose the invoice again from a separate “Open document” selector.
- **Why it matters:** The duplication adds scanning and selection work, especially when invoice labels are similar.
- **Suggested improvement:** Provide one clear result-card or row-selection interaction that opens the chosen document. Keep grouping if useful, but avoid presenting a second unrelated selector.
- **Estimated implementation effort:** M.

## M-09 — Feed rejection uses warning styling after an intentional decision

- **Description:** Rejecting a document shows a warning alert even though the requested action succeeded.
- **Why it matters:** Orange warning treatment suggests something went wrong and makes routine queue cleanup feel risky.
- **Suggested improvement:** Use a calm neutral confirmation such as “Invoice rejected and removed from the review queue,” with recovery information if rejection is reversible.
- **Estimated implementation effort:** XS.

## M-10 — Confidence presentation lacks concise methodology context

- **Description:** OCR Confidence is displayed as a precise percentage, while Supplier and Products Confidence show Unavailable. The screen says the value comes from extraction but does not explain what the overall score covers or that it is provider-reported.
- **Why it matters:** Users may interpret the number as an independently verified probability for every field.
- **Suggested improvement:** Label it “Overall extraction confidence” if that matches the provider meaning and add one short tooltip/caption explaining its scope. Keep unavailable field confidence explicit.
- **Estimated implementation effort:** XS.

## M-11 — Home’s tracked-price footer is dense and technical

- **Description:** Barni Today ends with a single caption containing four counts separated by dots, including “need attention.”
- **Why it matters:** It competes with the insight cards and reads like instrumentation rather than a calm assistant summary.
- **Suggested improvement:** Move the counts into Purchasing Health cards or omit them when they do not change the user's next action. Keep Barni Today focused on at most three useful messages.
- **Estimated implementation effort:** S.

## M-12 — Ask Barni is named like conversational AI but behaves like a narrow query parser

- **Description:** Home presents “Ask Barni,” while the underlying component is named AI Accountant and supports a limited set of database-query patterns. There is no loading state or visible explanation of the supported scope in compact mode.
- **Why it matters:** The interaction can create expectations of a general intelligent assistant and make valid natural-language questions appear to fail unpredictably.
- **Suggested improvement:** Set concise expectations beside the input, provide a few pilot-relevant example prompts, show a short searching state, and use a calm unsupported-question response rather than a generic no-results message.
- **Estimated implementation effort:** S.

## M-13 — Stable supplier status has no visible explanation

- **Description:** The Knowledge header can show a Stable chip when all comparable changes are within a code-defined threshold, but the UI does not explain the period, products included, or threshold.
- **Why it matters:** A status chip can be interpreted as a broad assessment of supplier reliability rather than a narrow price observation.
- **Suggested improvement:** Rename it to “Prices stable” and provide a short explanation such as “All comparable latest price changes are within 2%.” Hide it when comparison coverage is insufficient.
- **Estimated implementation effort:** XS.

## M-14 — Date and money formatting is not consistent everywhere

- **Description:** Some tables use `DD MMM YYYY`, others show source strings, monthly values, or ISO dates. Money appears as `₪1,000.00`, `1,000.00 ₪`, and `₪ 1,000` depending on the screen.
- **Why it matters:** Financial software earns trust through consistency. Mixed formats make comparisons harder and look unfinished.
- **Suggested improvement:** Use shared display helpers for currency, dates, percentages, and unavailable values. Preserve original data underneath but render one pilot standard.
- **Estimated implementation effort:** S.

# Low

## L-01 — Emoji usage is inconsistent and occasionally excessive

- **Description:** Some titles include emojis, some use text-only labels, product trends contain colored emoji plus text, and multiple navigation items repeat the same icon.
- **Why it matters:** Inconsistent decoration weakens the restrained, premium visual language, although text labels usually preserve meaning.
- **Suggested improvement:** Define a small icon vocabulary for navigation and status. Remove title emojis that do not improve recognition and retain text alongside every status signal.
- **Estimated implementation effort:** XS.

## L-02 — Several pages rely on repeated blank `st.write("")` calls for spacing

- **Description:** Vertical rhythm is created through ad hoc empty writes mixed with CSS padding and Streamlit defaults.
- **Why it matters:** Spacing can drift across Streamlit versions and varies between otherwise similar sections.
- **Suggested improvement:** Define consistent section wrappers or spacing tokens and reduce manual blank elements.
- **Estimated implementation effort:** S.

## L-03 — Product and invoice tables can become visually dense on narrow screens

- **Description:** Knowledge, Search, and history tables expose many columns and depend on horizontal scrolling. Some surrounding cards also use four or six columns.
- **Why it matters:** Laptop-sized pilot screens may make important values harder to compare.
- **Suggested improvement:** Verify the pilot device width, prioritize essential columns, move secondary details into expansion or selection, and stack metric cards where supported.
- **Estimated implementation effort:** M.

## L-04 — Unused placeholder page remains in the repository

- **Description:** `ui/feed.py` still contains “Feed module is being migrated...” even though the active route renders `daily_intake.py`.
- **Why it matters:** It does not currently appear in the main workflow, but it can confuse contributors and could reappear through a future routing mistake.
- **Suggested improvement:** Remove the unused placeholder after verifying imports, or convert it into the canonical Feed page wrapper with no placeholder copy.
- **Estimated implementation effort:** XS.

## L-05 — Legacy and current sidebar implementations coexist

- **Description:** `ui/sidebar.py` defines a separate radio-based navigation that is not the sidebar currently rendered by `app.py`.
- **Why it matters:** Contributors can edit the wrong navigation implementation, creating future inconsistency.
- **Suggested improvement:** Choose one sidebar owner, migrate the active implementation into it, and remove or clearly deprecate the unused version after verification.
- **Estimated implementation effort:** S.

## L-06 — Pilot debug export lacks a visible generated-at summary

- **Description:** The exported JSON includes generation time and health metadata, but the page does not preview what was collected or when.
- **Why it matters:** Users may hesitate to download diagnostic information they cannot inspect at a glance.
- **Suggested improvement:** Show a concise list of included categories and the generation time, with the existing privacy statement retained.
- **Estimated implementation effort:** XS.

## L-07 — Global error recovery offers no next step

- **Description:** The page-level error boundary says the details were logged but provides no Retry, Return Home, or Report Problem action.
- **Why it matters:** The calm wording is appropriate, but the manager can still feel stranded during the pilot.
- **Suggested improvement:** Add a retry action and a direct Report Problem route that preserves the source page. Keep technical details in the local log.
- **Estimated implementation effort:** S.

# Recommended Pilot Sequence

Complete work in this order to reduce risk fastest:

1. Resolve C-02 through C-06 so the UI never overstates knowledge or approves invalid data.
2. Hide C-01, C-07, and C-08 from the pilot until those workflows are genuinely ready.
3. Address H-01 through H-04 to make Feed and Review clear, safe, and manager-facing.
4. Resolve H-07 through H-12 so the primary cockpit, Insights, Search, and Ask Barni feel coherent.
5. Standardize empty states, typography, formatting, spacing, and navigation.
6. Run a complete pilot-device walkthrough using real but non-destructive test documents.

# Pilot Exit Criteria

Before the first restaurant session:

- [ ] No visible page presents sample or placeholder business data as real.
- [ ] No product without valid comparison history is labeled increased, decreased, stable, or unchanged.
- [ ] Uncertain or failed invoices cannot enter Business Memory without valid review and approval.
- [ ] Duplicate Replace, Skip, and Keep both choices are explicit and safely confirmed.
- [ ] Developer, migration, legacy, and bulk-maintenance tools are hidden from restaurant-manager navigation.
- [ ] Every primary page uses one language strategy and one clear heading hierarchy.
- [ ] Every empty state explains what is missing and, when useful, the next action.
- [ ] Every long-running core workflow shows a concise professional loading state.
- [ ] Raw exceptions, file paths, model identifiers, and validation codes are absent from restaurant-facing UI.
- [ ] Money, dates, percentages, statuses, and unavailable values use consistent display rules.
- [ ] The complete Upload → Review → Duplicate decision → Approval → Business Memory → Search journey is manually verified.
- [ ] Report Problem, Suggest Improvement, and Debug Export are tested on the pilot device.
- [ ] Database counts and integrity are verified before and after the rehearsal.
- [ ] A named person and procedure exist for collecting locally stored pilot feedback and runtime logs.
