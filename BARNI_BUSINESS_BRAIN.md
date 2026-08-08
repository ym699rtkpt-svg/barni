# Barni Business Brain

Barni understands a business as connected, evolving knowledge. Documents provide evidence, but the business itself is made of suppliers, products, prices, purchasing behavior, relationships, and changes over time.

# Suppliers

Barni learns:

- Supplier names
- Aliases
- VAT IDs
- Payment habits
- Average spend
- Purchase frequency
- First seen
- Last seen
- Missing invoices
- Unusual activity

Supplier knowledge should become more reliable as Barni observes additional evidence. Names and aliases should resolve to the same supplier only when the available evidence supports that relationship.

# Products

Barni learns:

- Products
- Categories
- Units
- Normal prices
- Seasonal prices
- Price trends
- Substitute products
- Preferred suppliers

Product knowledge should connect descriptions that refer to the same real product while preserving meaningful differences in size, unit, quality, and packaging.

# Prices

Barni continuously remembers:

- Lowest price
- Highest price
- Current average
- Last purchase price
- Price increases
- Price decreases
- Inflation over time

Every price observation must retain its context: product, supplier, unit, quantity, date, currency, and source evidence. Barni should compare prices only when the underlying products and units are genuinely comparable.

# Business Behaviour

Barni understands:

- Weekly spending
- Monthly spending
- Supplier dependency
- New suppliers
- Missing suppliers
- Abnormal purchases
- Duplicate invoices
- Seasonality

Business behavior is learned over time. Barni should distinguish meaningful changes from ordinary variation and remain quiet when an event does not help the user understand or act.

# Knowledge Graph

Barni's knowledge graph connects suppliers, invoices, products, categories, and prices.

- A supplier sells products.
- A product belongs to one or more useful business categories.
- An invoice provides dated evidence of a purchase from a supplier.
- An invoice line connects a product, quantity, unit, and observed price.
- A price belongs to a product, supplier, unit, date, and source.
- Repeated purchases create product, price, supplier, and spending histories.
- Histories reveal patterns such as frequency, seasonality, dependency, and change.
- Categories connect related products and support broader cost understanding.
- Source invoices remain attached to learned facts so Barni can explain where its knowledge came from.

The graph should preserve uncertainty. A suspected relationship must not become a fact until sufficient evidence or user confirmation supports it.

# Questions Barni Should Answer

Barni should answer practical questions such as:

- Who sells tomatoes cheapest?
- Which supplier became more expensive?
- Show invoices from July.
- When did I last buy Coca Cola?
- How much did milk cost six months ago?
- Which supplier do I buy meat from most often?
- What products have increased the most?
- What invoices need review?

Answers should be concise, evidence-based, and connected to their source records. When the available knowledge is incomplete, Barni should say so clearly.

# Barni Thinking

Barni Thinking is the interpretation layer that begins every invoice review. Its purpose is to help the user understand the document before asking them to inspect or edit fields.

The review sequence is:

```text
Invoice
→ Barni thinks
→ Barni explains
→ User checks or corrects the evidence
→ User approves
→ Business Memory grows
```

Barni Thinking is not a second intelligence engine. It organizes existing, evidence-backed business knowledge and structured insights into one conversational explanation.

Every Thinking view contains five parts:

## Identity

Answers: What is this document?

Barni explains the supplier and document type it believes it sees. When either identity is missing or uncertain, Barni asks for help without exposing extraction terminology or technical confidence values.

## Memory

Answers: What does Barni already know?

Barni connects the invoice to existing supplier history and states the number of previous invoices supported by stored records. If the supplier is new, Barni says so. If supplier identity is not reliable enough, Barni does not imply a relationship.

## Observations

Answers: What changed?

Barni surfaces only meaningful observations returned by the shared intelligence engine, including supported price movements, new products, possible duplicates, unusual totals, and validated tax concerns. When history does not support an important change, Barni says that calmly instead of inventing one.

## Confidence

Answers: What is Barni unsure about?

Barni names the business detail that needs help, such as the supplier, invoice number, date, or total. Normal users receive qualitative guidance rather than raw confidence percentages, OCR language, parser terminology, or internal issue codes.

## Recommendation

Answers: What should the user do next?

Barni recommends one proportionate action: compare a possible duplicate, check a flagged detail, or approve the invoice when it looks correct. Approval remains a human decision.

After Barni Thinking, the editable invoice is shown as evidence. Reasoning leads; fields support the reasoning.

Barni Thinking follows these rules:

- Every statement must be traceable to the current invoice or existing Business Memory.
- It must reuse the shared intelligence service rather than duplicate rules in the interface.
- It must never invent patterns, confidence, comparisons, or recommendations.
- Missing evidence must be acknowledged explicitly.
- Language must remain conversational, calm, concise, and professional.
- Technical details remain hidden unless deliberately requested.
- The component should become more capable as Business Memory grows without becoming noisier.

Barni Thinking is the foundation for future reasoning across other business signals. The same structure can later explain sales, transactions, inventory changes, employee documents, supplier conversations, and other evidence while relying on the same canonical Business Memory.

# Proactive Barni

Proactive Barni compares new evidence with Business Memory and speaks only when a supported pattern is meaningful enough to help the user understand or act.

Proactive intelligence is part of the shared Barni Intelligence engine. It is not a separate reasoning system and does not belong to any individual page. Invoice Review, Home, Business Memory, Search, and future notification experiences may request the same structured proactive insights.

Every proactive insight contains:

- A short title
- A conversational explanation
- A category
- A priority
- Structured evidence
- Source record IDs
- An optional recommended next action

Initial supported signals include:

- A first invoice from a supplier
- A significant price movement against the previous comparable purchase
- A price that increased across three comparable purchases
- A product that is new to a known supplier relationship
- An invoice total that differs meaningfully from sufficient recent, comparable supplier history
- An exact duplicate supported by supplier identity, invoice number, and document type
- A possible near-duplicate only when supplier, date, total, document type, and reordered invoice-number parts all match
- A recurring supplier-product purchase cadence supported by at least five consistent dated purchases

Proactive signals are ranked by financial impact, required user action, unusualness, and evidence quality. A maximum of three may be returned, and redundant explanations of the same change are suppressed.

Weak price movements, sparse history, incompatible units, non-positive invoice totals, uncertain supplier relationships, and irregular purchase dates remain silent. Silence is the correct result when the evidence does not justify interruption.

Recommendations must remain proportionate to their evidence. A price increase may justify reviewing the latest price. It does not justify recommending another supplier unless real comparable supplier evidence exists.

# Business Identity and Evidence Trust Layer

Business Memory distinguishes the real business entity from the words printed on a document. Raw invoice values remain immutable evidence; canonical identities provide the stable knowledge layer used to connect that evidence over time.

## Canonical Suppliers

A canonical supplier represents one real supplier and contains a stable internal identity, a preferred display name, a normalized VAT ID when available, and all observed aliases. VAT ID is the strongest automatic identity key. Without it, Barni may automatically reuse only an exact normalized alias. Similar-looking names must remain separate until the user confirms they are the same supplier.

Each invoice links to one canonical supplier with its matching method. Renaming or merging a canonical supplier never rewrites the supplier text stored on the source invoice.

## Canonical Products

A canonical product represents one business product across the descriptions that suppliers use for it. It contains a stable internal identity, a preferred display name, aliases, a normalized unit, and observed packaging quantity and unit.

Automatic product identity is intentionally conservative: only exact normalized descriptions are joined. Spelling variants, translations, supplier codes, and similar descriptions remain separate until a person confirms the relationship. A confirmed merge joins future history while preserving every original line description.

## Units and Packaging

Units are normalized into stable business units such as kilograms, grams, litres, millilitres, units, and packages. Packaging is recorded separately from product identity as a quantity and unit observation, for example `750 ml`.

Price conclusions may compare records only when their normalized units and packaging are compatible. Unknown units remain explicit. Barni must never silently convert or compare incompatible quantities.

## Evidence Chain

Every insight must retain a traceable path:

```text
Insight
→ structured evidence values
→ canonical supplier and product identities
→ source invoice and invoice-item IDs
→ original stored document
```

The interface may translate this into calm human language, but it must not discard the source record IDs. Users can open the invoices supporting a conclusion from the collapsed evidence view. The current invoice is also evidence and must be linked when it has been stored.

## Identity Decisions

Confirmed merges and canonical-name changes are recorded as identity decisions. Automatic rules must favor false separation over false combination: two identities can be safely joined later, while an incorrect merge can contaminate price history and future conclusions.

Canonical identities, aliases, unit observations, packaging observations, match methods, and source links belong to Business Memory. Intelligence services consume this shared layer; pages must not recreate identity logic.

# Identity Review and Reversible Learning

Identity Review is Barni's learning classroom. It is not a settings area and it is not another intelligence engine. It turns an unresolved knowledge gap into one calm, evidence-backed question that the business owner can answer once.

The canonical learning flow is:

```text
Stored evidence
→ conservative identity resolution
→ unresolved high-value relationship
→ Identity Review Queue
→ user reviews Barni's reasoning and source invoices
→ confirm, reject, merge, split, rename, or undo
→ canonical Business Memory updates
→ Search, Thinking, insights, and comparisons reuse the decision
```

Barni never silently merges uncertain identities. Automatic identity reuse remains limited to strong deterministic evidence. Similar names, OCR variants, translations, packaging differences, inconsistent units, VAT behavior, and currency differences may create review candidates, but they do not become canonical truth without a user decision.

## Review Candidate

Every candidate contains:

- The identities or observations under review
- What Barni thinks
- A natural-language explanation
- A confidence value intended specifically for the review workflow
- The evidence signals that contributed to the suggestion
- Source invoice and item IDs
- A stable fingerprint so a rejected question does not silently return
- Priority, status, creation time, and resolution

Candidate generation is deterministic and independent from the UI. Conflicting strong identifiers, such as different product barcodes or supplier VAT IDs, veto an automatic match suggestion. Weak candidates remain silent.

## Queue Prioritization

The queue ranks only the most valuable unresolved questions. Priority is based on:

1. Conflicting VAT evidence
2. Unit or package uncertainty that blocks safe price comparison
3. Frequently purchased duplicate product identities
4. Duplicate supplier identities affecting multiple invoices
5. Currency differences requiring contextual review
6. Low-impact naming or OCR variations

Only five reviews are exposed at once. Resolving one advances the next most valuable question.

## Reversibility Model

Canonical identities are never destroyed by a decision. A merge marks the source identity inactive and redirects its aliases and evidence links to the chosen canonical identity. A split creates a new canonical identity and moves only the selected source records. A rename changes the preferred display name while leaving raw evidence untouched.

Every decision records:

- Previous identity state
- Resulting identity state
- Acting user
- Decision time
- Human reason
- Supporting evidence
- A link to any reversal

Undo restores the prior aliases and evidence links. Evidence observed after a merge follows the restored alias when its normalized alias belongs to the reversed source. Rejections and acknowledged variations can also be undone and returned to review.

No source invoice, item description, or document is deleted or rewritten by identity teaching.

## BARFI — Barni Feedback Intelligence

Each confirmed correction becomes shared Business Memory, not page-local feedback. Search resolves aliases through the canonical identity. Thinking and proactive intelligence use the corrected history. Price comparisons gain or lose comparable evidence immediately. Rejected matches remain separate and are not asked again unless the evidence fingerprint changes because genuinely conflicting or new information appears.

# Golden Rule

Barni stores knowledge.

Invoices are only one source of knowledge.

# Trusted Business Facts

Barni reasons over facts, not invoice fields. A source line first resolves to canonical supplier and product identities, then passes through the shared unit, package, currency, VAT, and quantity normalization flow. The result is an evidence-bound Business Fact with a trust status and an explanation.

## Comparable Price Fact

Each price fact records the canonical product and supplier, invoice and invoice-line IDs, observed price, normalized price and unit, package quantity, purchase quantity, VAT basis, currency, observation date, document type, confidence components, and links to the archived source.

A trusted price means every required basis is supported. Missing or conflicting inputs do not produce a weaker comparison: they produce a specific rejection status. Barni explains the missing basis and, when a user decision could resolve it, sends the question to Identity Review. Raw descriptions and values remain immutable evidence.

All price history, price movement, and future supplier-price reasoning must consume this ledger. Interfaces may show a friendly summary, but may not normalize or decide comparability themselves. Future fact types follow the same builder → status → evidence → typed-ledger lifecycle.

# Business Stories

The Business Story Engine explains trusted knowledge in Barni's voice. It is not a second intelligence engine. It receives a time or invoice context, selects already-supported changes, ranks them by usefulness, and returns reusable story objects.

Initial stories cover trusted price movements, explicit duplicate outcomes, canonical supplier or product learning, successfully approved invoices, and valuable unresolved Identity Review questions. Every factual story retains the invoice evidence and structured values behind its wording. Price stories are produced only from trusted Comparable Price Facts.

Story selection favors clarity over completeness. A restaurant owner usually sees one strong story rather than several weak observations. Feed uses the current approved invoice as context; Home and Insights use a time context. The same story wording and evidence travel between experiences.
