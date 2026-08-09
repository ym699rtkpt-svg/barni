# BAR-012 — Product Simplicity Audit

## Audit Lens

This audit assumes Barni launches tomorrow and judges only what a first-time restaurant owner sees, understands, and must do. The standard is simple: every screen should reduce effort and move the owner from business data to business understanding.

Barni currently has the right ingredients, but too many places explain the same business in different ways. Home, Feed, Insights, and Business Memory compete to answer “What changed?” Search and Business Memory both act as ways to browse history. Invoice Review and Invoice Detail describe the same invoice with different priorities. The result feels broader than the product needs to be at launch.

The launch product should have four durable destinations:

1. **Today** — what changed and what needs attention.
2. **Search** — ask Barni what it remembers.
3. **Business Memory** — understand suppliers, products, and history.
4. **Accountant** — review readiness and export.

Uploading invoices should be the primary action inside Today, not a competing destination.

## Page-by-Page Review

### Landing

**Why does this page exist?**  
To introduce Barni and create a calm first moment before entering the product.

**Could it disappear?**  
For returning users, yes. It should be a first-launch or signed-out experience, not a repeated obstacle.

**What is confusing?**  
“Your Business Memory” and “Your business, remembered” communicate nearly the same promise. The user still does not know what the first useful action will be.

**What feels duplicated?**  
The product category and the tagline repeat one another.

**What should move somewhere else?**  
Any explanation of features belongs in onboarding after entry, only when needed.

**One premium improvement**  
Remember returning users and take them directly to Today. Premium software respects continuity.

### Home

**Why does this page exist?**  
To orient the owner and summarize the current state of the business.

**Could it disappear?**  
Yes, as a separate page. Its useful content should become the top of Today.

**What is confusing?**  
The owner must choose between Home, Feed, and Insights before understanding the difference. Counters, snapshots, priorities, and calls to upload compete for attention.

**What feels duplicated?**  
Business stories overlap with Feed. Metrics overlap with Business Memory. Calls to feed invoices overlap with Feed Barni.

**What should move somewhere else?**  
Business history belongs in Business Memory. Month-end readiness belongs in Accountant. Meaningful changes belong in Today.

**One premium improvement**  
Replace the dashboard with one sentence that answers “What changed?” and one primary action that answers “What should I do next?”

### Feed Barni

**Why does this page exist?**  
To show what changed and let the owner add today’s invoices.

**Could it disappear?**  
Not as an experience, but it should stop being a separate concept. It should become the default Today screen.

**What is confusing?**  
“Feed Barni” can mean both uploading documents and reading a business journal. The page is trying to be an inbox, an upload flow, and a news feed.

**What feels duplicated?**  
Its stories duplicate Home priorities and Insights conclusions. Its upload action is repeated elsewhere.

**What should move somewhere else?**  
Advanced upload settings should appear only inside the upload flow. Historical stories should remain searchable rather than extending the page indefinitely.

**One premium improvement**  
Rename the destination **Today** and let a single calm timeline lead naturally into **Add invoices**.

### Invoice Review

**Why does this page exist?**  
To help the owner correct only what Barni is unsure about and approve what the business should remember.

**Could it disappear?**  
No, but it should appear only when attention is genuinely required. Clear invoices should not feel like forms that demand inspection.

**What is confusing?**  
The page mixes Barni’s conclusion, editable fields, confidence, evidence, preview, products, and technical detail. The owner must work out which parts matter.

**What feels duplicated?**  
Supplier, invoice number, date, total, and products may appear in Barni’s explanation, editable fields, and the original invoice.

**What should move somewhere else?**  
Technical confidence and extraction detail should move behind Internal tools. The original document should remain available as evidence, not dominate the review.

**One premium improvement**  
Open with one plain-language conclusion and one recommended action, then reveal only the fields connected to that action.

### Approval Completion

**Why does this page exist?**  
To confirm that approval succeeded and make the value of learning visible.

**Could it disappear?**  
As a separate stopping page, yes. Completion should resolve back into Today.

**What is confusing?**  
Several next-step buttons force a decision immediately after the owner has completed the task.

**What feels duplicated?**  
“Find it in Search,” “Open Business Memory,” and similar routes all prove the same thing: Barni learned the invoice.

**What should move somewhere else?**  
The learning result should become the newest Today story. Search and Memory remain available in navigation.

**One premium improvement**  
Use a brief success transition: “Approved. Barni learned 3 products from Kitchenware,” then return to Today with that evidence visible at the top.

### Search

**Why does this page exist?**  
To let the owner retrieve anything Barni remembers without learning a database structure.

**Could it disappear?**  
No. It is one of the clearest expressions of Barni’s value.

**What is confusing?**  
Suggested searches, recent invoices, filters, grouped results, summaries, and detail states can make a simple search feel like several tools at once. Suggestions that cannot reliably produce meaningful answers weaken trust.

**What feels duplicated?**  
Recent invoices overlap with Today. Supplier and product browsing overlaps with Business Memory.

**What should move somewhere else?**  
Advanced filters should remain hidden until requested. Recent invoices should be a small starting aid, not a second archive.

**One premium improvement**  
Preserve the query and scroll position when returning from a result. Fast retrieval feels premium only when context is never lost.

### Invoice Detail

**Why does this page exist?**  
To explain a stored invoice, its meaning, and its evidence without putting it back into an editable workflow.

**Could it disappear?**  
Not entirely, but it should be the read-only state of one shared invoice experience rather than a separate product pattern.

**What is confusing?**  
Technical labels or a large document preview can make the page feel like an OCR inspector instead of business memory.

**What feels duplicated?**  
Its metadata, products, reasoning, evidence, and preview repeat the Invoice Review structure.

**What should move somewhere else?**  
Editing should be available only through an explicit correction action. Technical data belongs behind Internal tools.

**One premium improvement**  
Lead with “What this invoice changed in your business,” then show its evidence in a consistent, contained detail layout.

### Business Memory

**Why does this page exist?**  
To prove that Barni is building lasting knowledge about suppliers, products, prices, and relationships.

**Could it disappear?**  
No. It is the product’s durable value after invoices are approved.

**What is confusing?**  
Metrics, learning progress, categories, charts, recent learning, identity work, supplier lists, and product lists make the page feel like a dashboard and directory combined.

**What feels duplicated?**  
Recent learning duplicates Today. Invoice counts duplicate Home and Accountant. Insights duplicate the Insights page.

**What should move somewhere else?**  
Recent changes belong in Today. Items requiring confirmation belong in a contextual review queue. Accountant readiness belongs in Accountant.

**One premium improvement**  
Start with two confident choices—**Suppliers** and **Products**—and make each drill-down tell a coherent history rather than expose a wall of metrics.

### Identity Review

**Why does this page exist?**  
To let the owner teach Barni when two names, packages, or units may represent the same business identity.

**Could it disappear?**  
As a permanent navigation destination, yes. As a focused task, no.

**What is confusing?**  
Confidence percentages and actions such as merge, split, confirm, reject, rename, and undo can feel like data administration.

**What feels duplicated?**  
Identity questions can surface in Invoice Review, Business Memory, and a review queue.

**What should move somewhere else?**  
High-impact identity questions should appear in Today under “Barni needs your help.” Lower-impact corrections should live contextually inside the relevant supplier or product.

**One premium improvement**  
Ask one question at a time in natural language, show the two pieces of evidence, and promise: “Confirm this once and I’ll remember it.”

### Insights

**Why does this page exist?**  
To explain meaningful changes and patterns in the business.

**Could it disappear?**  
Yes, before launch. A standalone Insights destination is premature while the same conclusions already appear in Today, review, and memory.

**What is confusing?**  
The difference between a Feed story, a Home priority, a review insight, and an Insights item is unclear to the owner.

**What feels duplicated?**  
Price changes, unusual activity, supplier changes, and business summaries appear across several pages.

**What should move somewhere else?**  
Time-sensitive conclusions belong in Today. Supplier- or product-specific conclusions belong in Business Memory. Search should retrieve older conclusions.

**One premium improvement**  
Do not launch the page until Barni can consistently offer a small number of high-trust, longitudinal explanations worth revisiting.

### Accountant Workspace

**Why does this page exist?**  
To show what is ready, what still needs attention, and export a complete month for the accountant.

**Could it disappear?**  
No. It completes a concrete, high-value job.

**What is confusing?**  
Status explanations, counters, readiness checks, package coverage, and export controls can turn one task into a workflow dashboard.

**What feels duplicated?**  
Pending and approved counts repeat Home and Feed. Invoice lists may repeat Search.

**What should move somewhere else?**  
Invoice investigation belongs in Search or Invoice Detail. Only blockers to export should remain here.

**One premium improvement**  
Show one sentence—“July is ready” or “2 invoices need attention”—followed by one primary action: **Export July** or **Review 2 invoices**.

## Pages to Remove

1. **Standalone Home** — merge its useful orientation and priority content into Today.
2. **Standalone Insights for Alpha** — distribute trusted conclusions to Today and Business Memory until there is enough longitudinal value to justify a destination.
3. **Standalone approval completion page** — turn approval into a success transition that returns to Today.
4. **Identity Review as a permanent destination** — retain the workflow, but surface it only when Barni needs help or within the relevant memory record.
5. **Repeated landing page for returning users** — keep it for first launch, then remember the user.

## Pages to Merge

1. **Home + Feed Barni → Today**  
   One default destination for what changed, what needs attention, and adding invoices.

2. **Insights + Today stories + Memory observations → one conclusion model**  
   The destination depends on relevance: current changes in Today, durable history in Memory, older items through Search.

3. **Invoice Review + Invoice Detail → one invoice experience with two modes**  
   Review mode asks for necessary corrections. Read-only mode explains what Barni remembers. Layout and language remain consistent.

4. **Identity Queue + contextual identity prompts → one help workflow**  
   The same question pattern should open from Today, Invoice Review, or Business Memory without feeling like separate products.

## Buttons to Remove

1. Remove competing post-approval buttons such as **Find it in Search** and **Open Business Memory**; show the learning result in Today instead.
2. Remove duplicate **Feed Barni** buttons when **Add invoices** is already the page’s primary action.
3. Remove navigation-style buttons inside Business Memory that merely duplicate **Accountant** or **Search** in the sidebar.
4. Remove ordinary customer access to **Technical details**, confidence diagnostics, or extraction controls; keep them in Internal tools.
5. Remove a separate **View invoice** step when clicking an invoice result can safely open its contained detail directly.
6. Remove **Clear filters** until at least one filter is active.
7. Remove suggested-search chips that do not map to a reliably supported result. Keep no more than three strong examples.
8. Remove generic **Learn more**, **Explore**, or **View all** buttons that do not state the next destination or outcome.
9. Remove inactive or non-blocking identity actions from the primary review surface; reveal advanced correction choices only when needed.
10. Remove secondary export actions that compete with the one canonical monthly package.

## Sentences to Shorten

| Current pattern | Recommended language |
|---|---|
| “Your Business Memory” + “Your business, remembered.” | “Your business, remembered.” |
| “Every invoice makes Barni smarter.” | “Add today’s invoices.” |
| “Here are the latest changes supported by your business records.” | “Since you last checked.” |
| “Knowledge stored from approved business documents.” | “What Barni remembers.” |
| “Products with 2+ valid stored prices.” | “Products with price history.” |
| “Check the month and prepare one complete local package for your accountant.” | “Review the month and export for your accountant.” |
| “The package is generated locally. Barni will not send email automatically.” | “Nothing is sent automatically.” |
| “Some details still need a careful check before I learn this invoice.” | “Check one detail before Barni learns this invoice.” |
| “This conclusion is based on the following supporting evidence.” | “Why Barni thinks this.” |
| “No important insights were detected for this invoice.” | “Everything looks normal.” |
| “No matching search results were found.” | “I couldn’t find that yet.” |
| “Identity review items require user confirmation.” | “Barni needs your help with one detail.” |

Product language should avoid narrating the interface. State the conclusion, the action, or the outcome—then stop.

## Workflow Improvements

### Recommended Launch Journey

**First visit**  
Landing → Enter Barni → Today → Add invoices

**Daily visit**  
Today → See what changed → Add invoices → Review only what needs attention → Approve → See what Barni learned

**Retrieve knowledge**  
Search → Open one result → Review evidence → Return to the same search state

**Understand history**  
Business Memory → Supplier or Product → History, prices, and source invoices

**Finish the month**  
Accountant → Resolve blockers if any → Export month

### Specific Improvements

1. Make **Today** the default destination after the first visit.
2. Give every page one dominant question and one primary action.
3. Let invoice approval return to Today and insert the new learning event at the top.
4. Review only invoices that require a decision; group clean completions into one calm success state.
5. Preserve search query, filters, result position, and selected group after viewing an invoice.
6. Make every story and conclusion open the exact source invoice or memory record that supports it.
7. Surface identity questions only when they block a useful comparison or require an owner decision.
8. Keep advanced controls collapsed and remove technical terminology from the customer experience.
9. Use the same plain-language status everywhere: **Needs review**, **Approved**, **Duplicate**. Show counts only where they change the next action.
10. Standardize the language strategy: interface copy follows the user’s chosen language; Hebrew and English business data remain unchanged.
11. Replace long empty states with a next action: add an invoice, change the search, or choose another month.
12. Keep invoice evidence visually contained so the conclusion remains the focus.

## Top 10 Product Improvements Before Launch

### 1. Merge Home and Feed into Today

**Impact: Critical**  
This removes the biggest navigation ambiguity and gives Barni one obvious starting point.

### 2. Make the upload-to-learning loop one continuous journey

**Impact: Critical**  
Upload, progress, necessary review, approval, and visible learning should feel like one task—not a sequence of pages.

### 3. Show only invoices that need attention during review

**Impact: Critical**  
The owner should spend time making decisions, not validating fields Barni already understands.

### 4. Replace the completion menu with immediate visible value

**Impact: High**  
After approval, show exactly what Barni learned and place it at the top of Today. This is the launch magic moment.

### 5. Remove standalone Insights from Alpha navigation

**Impact: High**  
Trusted conclusions will feel more relevant inside Today and Business Memory, while eliminating a destination with unclear boundaries.

### 6. Simplify Business Memory to Suppliers and Products first

**Impact: High**  
Reduce dashboard density and make durable knowledge understandable through focused histories and source evidence.

### 7. Create one consistent invoice experience

**Impact: High**  
Review and read-only detail should share hierarchy, language, evidence, and navigation so an invoice never feels like a different object on different pages.

### 8. Reduce Accountant to readiness plus one action

**Impact: High**  
The owner needs to know whether the month is ready and what to do next. Everything else is supporting detail.

### 9. Remove customer-facing technical language and confidence mechanics

**Impact: Medium**  
Barni should say what it understands, what it does not, and why—not expose how document processing works.

### 10. Make navigation and return behavior preserve context

**Impact: Medium**  
Back from an invoice should restore the exact search, story, supplier, or month. Losing context makes the product feel slower and less trustworthy.

## Launch Recommendation

Barni should launch as a focused daily loop, not a suite of modules:

**Today → Add invoices → Review what matters → See what Barni learned → Find it later → Export the month.**

Anything that does not strengthen that loop should be hidden, merged, or postponed. The premium quality will come less from adding polish to every existing page and more from making the product feel inevitable: one place to start, one action at a time, and one trustworthy explanation of what changed.
