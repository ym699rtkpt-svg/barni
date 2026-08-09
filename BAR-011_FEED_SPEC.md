# BAR-011 — Feed Barni MVP Specification

## Purpose

Feed Barni is the business journal and the beginning of Barni's daily learning workflow.

When the owner opens Feed, the page answers:

> What changed in my business since I last checked?

It then presents one clear next action:

> Feed today's invoices.

The journal never creates an observation. It narrates durable events and trusted Business Facts that already exist elsewhere in Barni.

## Product Boundaries

Feed is not:

- A dashboard.
- An analytics page.
- A notification center.
- A raw activity log.
- A replacement for Search or Business Memory.
- A source of business rules.

Feed remains the complete Alpha workflow:

```text
Upload
→ Read
→ Review uncertainty
→ Approve
→ Learn
→ Confirm what changed
```

If active invoices need a decision, finishing Review takes priority over the journal. The owner is not shown historical cards while an unfinished invoice is waiting.

## Story Model

Feed consumes the shared `BusinessStory` contract.

Every story contains:

- `story_type` — stable semantic type.
- `title` — one strong, natural sentence or phrase.
- `description` — an optional short explanation.
- `category` — memory, price, duplicate, review, or quiet.
- `priority` — usefulness within its event type.
- `tone` — neutral, positive, or attention.
- `occurred_at` — the durable event time when available.
- `evidence` — source invoice records.
- `evidence_values` — structured values supporting the statement.
- `claim` — the canonical evidence and answer-confidence contract.
- `recommended_action` and `action_target` — optional proportionate navigation.

The UI renders this model. It never calculates story meaning.

## Journal Window

The Feed records the timestamp only after a journal is generated successfully.

- A new visit reads the last successful visit timestamp.
- The window is frozen for the current Streamlit session so normal reruns do not make cards disappear.
- A successful render advances the durable cursor.
- A failed story render does not advance it.
- If no previous visit exists, the window starts at the beginning of the current business day.
- Cursor writes are atomic and retain the previous valid snapshot.

This timestamp is delivery state, not a Business Fact. It never changes invoice, identity, price, or memory data.

## Supported Story Types

### 1. New invoice approved

**Source:** Approved invoices and their approval timestamp.

**Statement:** Supplier invoice approved and added to Business Memory.

**Evidence:** The approved source invoice.

**Silence rule:** Rejected, pending, processing, and review invoices never produce this story.

### 2. New supplier learned

**Source:** Canonical supplier identity, invoice identity links, and the supplier's first approved invoice.

**Statement:** Barni learned the supplier and added it to Business Memory.

**Evidence:** The first approved invoice linked to that canonical supplier.

**Silence rule:** Existing suppliers and suppliers without approved source evidence do not produce this story.

### 3. Product seen again

**Source:** Canonical product identity links, canonical supplier identity links, and approved invoice lines.

**Statement:** Barni has now seen the canonical product from the canonical supplier in a precise number of purchases.

**Evidence:** Every approved source invoice included in the count.

**Silence rule:** The first observation is not described as “seen again.” Raw descriptions are never grouped without canonical identity.

### 4. Trusted price change

**Source:** BAR-009 Comparable Price Ledger only.

**Statement:** The normalized price increased or decreased versus the previous comparable purchase.

**Evidence:** Current and previous source invoices plus normalized comparison values.

**Silence rule:** Incompatible units, packaging, VAT basis, currency, missing identity, insufficient history, and changes below the established materiality threshold remain silent.

### 5. Duplicate resolved

**Source:** Completed canonical invoice approval operations with `skipped`, `replaced`, or `kept_both` outcomes.

**Statement:** The exact decision the owner made.

**Evidence:** The stored invoice referenced by the completed operation.

**Silence rule:** An unresolved duplicate is not described as resolved.

### 6. Identity Review completed

**Source:** Durable, unreversed merge, rename, or split decisions.

**Statement:** Barni now understands the supplier or product under the confirmed canonical identity.

**Evidence:** Source invoice IDs stored with the identity decision.

**Silence rule:** Decisions without source invoice evidence, rejected suggestions, reversed decisions, and pending candidates do not produce completion stories.

### Quiet state

If no supported story exists in the journal window:

> Everything looks good.

If Business Memory is empty:

> Business Memory is ready to grow.

The quiet state does not pretend that an event occurred.

## Ordering Rules

Stories are ordered by:

1. Newest event timestamp.
2. Story priority when events share a timestamp:
   1. Invoice approved.
   2. New supplier learned.
   3. Product seen again.
   4. Trusted price change.
   5. Duplicate resolved.
   6. Identity Review completed.
3. Existing story usefulness priority.

The Feed displays at most five stories.

Duplicate stories are removed using semantic type plus canonical product, action target, or source invoice set. The engine does not collapse distinct evidence into one unsupported summary.

## Event Sources

| Story | Canonical source |
|---|---|
| Invoice approved | `invoices` with canonical approved state |
| Supplier learned | Canonical suppliers and invoice identity links |
| Product seen again | Canonical products, product links, supplier links, approved invoice lines |
| Price change | Trusted Comparable Price Facts |
| Duplicate resolved | Completed invoice approval operation |
| Identity completed | Reversible identity decision with invoice evidence |
| Quiet state | Absence of supported stories in the requested window |

Search data is used only through the same approved invoice records. Raw Search presentation state is not a story source.

## Evidence Experience

Every non-quiet Feed story shows:

- A concise conclusion.
- A short explanation when useful.
- Event timestamp or invoice reference.
- A “View evidence” control.
- An “Open invoice” action for every supporting source invoice.

Opening evidence routes to the existing Search invoice detail. Feed does not create a parallel invoice viewer.

## Visual Rules

- One vertical journal column.
- Calm off-white cards with subtle borders.
- Restrained positive or attention tint only when meaning requires it.
- Minimal icons.
- No charts.
- No KPI blocks.
- No colorful badges.
- No animation required for journal stories.
- Generous spacing between journal and upload workflow.
- Upload remains the primary actionable control.

## Unsupported Stories

The MVP intentionally remains silent about:

- Business Memory milestones. No approved milestone thresholds exist yet; inventing thresholds would create arbitrary gamification.
- Recovery events. Current recovery handling is operational and idempotent, but there is no canonical durable “recovered” business event with an evidence contract.
- Primary or preferred supplier conclusions.
- Supplier quality or performance.
- Spending causes or anomalies.
- Missing or disappearing products.
- Seasonal patterns.
- Savings, recommendations, or supplier-switch advice.
- Predictions and future purchasing behavior.
- Any raw price comparison that is not trusted by BAR-009.

These omissions are trust decisions, not missing UI.

## Failure Behavior

If story generation fails:

- Feed remains usable.
- Upload and active Review are unaffected.
- The last-visit cursor is not advanced.
- The customer sees calm text explaining that the latest story could not be prepared and that invoices remain safe.
- Technical details are logged only for pilot operations.

## Future Extensions

Future story types may be added only when a canonical producer and evidence contract exist.

Potential extensions:

- Recovery stories from a durable workflow-recovery event.
- Memory milestones after product-approved milestone policy exists.
- Morning spending narratives from trusted aggregate Business Facts.
- Supplier behavior stories from evidence-backed frequency facts.
- Attention-ranked Feed delivery using BAR-013.
- Cross-device and multi-user read cursors when Barni gains authenticated business accounts.
- Natural-language summaries through the Conversation Layer, constrained to the same story evidence.

No future consumer should recreate story SQL or narration. Home, Feed, Insights, and notifications must continue consuming the shared Business Story Engine.
