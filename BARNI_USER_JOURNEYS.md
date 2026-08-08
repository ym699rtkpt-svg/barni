# Barni User Journeys

This document defines the ideal end-to-end experiences in Barni. Each journey should feel calm, focused, and faster than the process it replaces.

# First Launch

```text
Landing page
↓
Home
↓
Feed first invoice
↓
Barni learns
↓
Business Memory updates
↓
Home now contains first insights
```

## User's goal

Understand what Barni does, add the first real business document, and see immediate evidence that Barni learned from it.

## Single primary action

Feed Barni the first invoice.

## Information that should be visible

- A concise explanation that Barni remembers and understands the business.
- One obvious route to add the first invoice.
- The supplier, products, date, and total Barni learned.
- A clear confirmation that Business Memory has started growing.
- The first useful facts on Home after completion.

## Information that should stay hidden

- Empty dashboards and charts.
- Advanced upload settings.
- Database terminology.
- Raw confidence percentages.
- Features that require more history before they become useful.

## What Barni should say

> Feed me your first invoice, and I'll start learning how your business works.

After approval:

> Barni learned something new.

## What Barni should never say

> Database initialization complete.

> OCR extraction succeeded.

# Daily Use

```text
Open Barni
↓
See what changed today
↓
Feed today's invoices
↓
Review anything Barni is unsure about
↓
Done
```

**Time goal:** Less than 3 minutes.

## User's goal

Understand today's meaningful changes, add new invoices, resolve genuine uncertainty, and move on quickly.

## Single primary action

Feed today's invoices.

## Information that should be visible

- A short summary of what changed today.
- Items that genuinely need attention.
- Upload progress and clear review requests.
- A concise completion state.

## Information that should stay hidden

- Ordinary events that require no action.
- Historical detail unrelated to today.
- Technical processing stages.
- Completed tasks after the workflow ends.
- Excessive notifications.

## What Barni should say

> Two invoices need one detail from you.

When finished:

> Barni grew a little smarter today.

## What Barni should never say

> Seven records were processed successfully.

> Low supplier confidence detected.

# Search

```text
Open Search
↓
Type anything remembered
↓
Results appear instantly
↓
Open invoice
↓
Review details
↓
Return to search
```

## User's goal

Find a remembered supplier, product, invoice, date, or business fact without browsing an archive.

## Single primary action

Type into Search.

## Information that should be visible

- A prominent search field.
- A maximum of five recent invoices when Search is empty.
- Live, grouped results while typing.
- A clear explanation of why a result matched when useful.
- A dedicated detail view after opening a result.
- A clear path back to the previous search.

## Information that should stay hidden

- Recent invoices during an active search.
- Advanced filters until requested.
- Full document previews before a result is opened.
- Database tables and archive trees.
- Unrelated metrics and totals.

## What Barni should say

> I found three invoices from Tnuva in July.

When nothing matches:

> Barni couldn't find that yet.

## What Barni should never say

> Query returned zero rows.

> Search index has no matching documents.

# Business Memory

```text
Open Business Memory
↓
See suppliers
↓
Products
↓
Price history
↓
Relationships
↓
Knowledge growth
```

## User's goal

Understand what Barni has learned about the business and how suppliers, products, prices, and purchases relate over time.

## Single primary action

Explore a remembered supplier or product.

## Information that should be visible

- Known suppliers and products.
- Reliable purchasing and price history.
- Relationships supported by stored evidence.
- Clear indications of how Business Memory is growing.
- Source invoices behind important facts.

## Information that should stay hidden

- Unsupported conclusions.
- Raw database entities and identifiers.
- Empty relationship diagrams.
- Technical model details.
- Arbitrary scores or gamification.

## What Barni should say

> You last bought this product from Tnuva on 31 July.

When memory is limited:

> I need more purchase history before I can compare this reliably.

## What Barni should never say

> Supplier relationship node created.

> This supplier is best.

# Insights

```text
Open dashboard
↓
What changed?
↓
What costs increased?
↓
Any anomalies?
↓
Recommended actions
```

## User's goal

Understand what deserves attention and decide what to do next.

## Single primary action

Review the most important supported change.

## Information that should be visible

- The most meaningful change first.
- Significant cost increases.
- Genuine anomalies.
- The evidence and time period behind each insight.
- One proportionate recommended action.

## Information that should stay hidden

- Noise from ordinary activity.
- Unsupported predictions.
- Decorative charts without a decision-making purpose.
- Long lists of low-priority observations.
- Recommendations that lack comparable evidence.

## What Barni should say

> Olive oil increased 8% since your previous purchase.

When no action is needed:

> Everything looks good.

## What Barni should never say

> An anomalous price delta has been detected.

> Switch suppliers immediately.

# Accountant

```text
Monthly export
↓
Review
↓
Approve
↓
Send
```

## User's goal

Prepare a complete, reliable monthly package and send it to the accountant with confidence.

## Single primary action

Review the monthly export.

## Information that should be visible

- The selected month.
- Included documents and totals.
- Missing information, duplicates, or unresolved invoices.
- Export readiness.
- A clear approval and send step.

## Information that should stay hidden

- Internal storage paths.
- Processing logs.
- Irrelevant historical documents.
- Technical validation terminology.
- Send actions before the package is ready.

## What Barni should say

> July is ready for review.

When something is missing:

> One invoice needs your help before the export is ready.

## What Barni should never say

> Export validation failed with three exceptions.

> Archive generation completed.

---

Every screen must reduce effort, never increase it.
