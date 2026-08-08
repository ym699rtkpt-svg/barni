# Barni OS

Barni is a long-term operating system for small-business understanding. It is not defined by invoices, screens, or isolated features. It is defined by its ability to turn many forms of business evidence into trustworthy memory, useful understanding, and clear action.

# Mission

Barni helps businesses understand themselves.

Small-business owners carry an enormous amount of operational knowledge in their heads, messages, documents, systems, and routines. That knowledge is fragmented, difficult to compare, and easy to lose. Barni brings it together, remembers how the business works, notices what matters, and helps the owner act with confidence.

Invoices are Barni's first data source, not its identity. Every future capability should expand Barni's understanding of the business rather than turn it into another disconnected tool.

# Core Philosophy

Barni follows one continuous value chain:

```text
Business data
→ Knowledge
→ Understanding
→ Recommendations
→ Actions
→ A better business
```

Business data is raw evidence. On its own, it creates work rather than clarity.

Knowledge gives that evidence identity, context, relationships, and history.

Understanding explains what changed, why it matters, and how certain Barni can be.

Recommendations identify a proportionate next step when action would genuinely help.

Actions turn understanding into progress while keeping the owner in control.

The outcome is not more software activity. The outcome is a business that is easier to understand and improve.

# Input Layer

The Input Layer receives business signals from every place where useful evidence is created. Over time, these sources may include:

- Invoices
- Sales
- Bank transactions
- Employees
- Payroll
- Inventory
- Suppliers
- Customer CRM
- Bookings
- POS
- Accounting software
- Email
- WhatsApp supplier conversations
- Contracts
- Government forms
- Documents
- Photos
- Manual notes
- Future APIs

Every source feeds the same brain.

Inputs may differ in format, frequency, reliability, and completeness, but they must not create separate versions of the business. Barni preserves where each fact came from, when it was observed, and how reliable it appears to be.

New sources should deepen existing memory whenever possible. A bank transaction may support an invoice payment. A supplier conversation may explain a price change. A POS sale may connect demand to an inventory movement. A contract may provide context for a recurring cost.

The Input Layer must preserve uncertainty. Receiving data does not automatically make it true, complete, or understood.

# Memory Layer

The Memory Layer is Barni's canonical business memory. It turns fragmented inputs into one connected, evolving representation of the business.

It stores and relates:

- Suppliers
- Products
- Employees
- Customers
- Documents
- Transactions
- Prices
- Relationships
- History
- Confidence
- Evidence

Memory is organized around real business concepts, not around the systems that supplied them. A supplier remains the same business entity whether Barni encounters it in an invoice, bank transaction, email, contract, or manual note.

Every remembered fact should retain:

- Its business meaning
- Its source evidence
- Its relevant date or period
- Its relationship to other knowledge
- Its current level of certainty
- Any confirmation or correction supplied by the user

The Memory Layer is cumulative but not careless. It must reconcile aliases, preserve meaningful differences, retain history, and avoid turning uncertain relationships into facts. Corrections should improve future understanding without erasing the evidence that explains how Barni learned.

There is one canonical memory. Individual experiences may present different views of it, but they must never create conflicting truths.

## Identity Review Architecture

The Memory Layer includes a shared Identity Review service for knowledge that cannot be resolved safely from deterministic evidence alone.

```text
Evidence observations
→ canonical identity resolver
→ high-value unresolved candidate
→ prioritized review queue
→ human decision
→ reversible memory mutation
→ all intelligence consumers refresh from canonical memory
```

Review candidates are proposals, never facts. They contain structured reasons, confidence, priority, source record IDs, and a stable evidence fingerprint. Candidate generation may use name similarity, shared supplier relationships, compatible units, package size, price proximity, VAT behavior, currency, language variation, and OCR variation. Strong conflicts veto a proposed merge.

Identity decisions form an append-only trust history. Each record preserves the previous state, resulting state, actor, time, reason, and evidence. Canonical entities are deactivated rather than deleted during merges. Split and undo operations restore or redirect evidence links without rewriting the original inputs.

This review service belongs to the Memory and Action layers. The Experience Layer presents it as Barni asking one useful question, while Search, insights, Thinking, and future capabilities consume only the resulting canonical truth. Future input sources must use the same review and reversibility model rather than creating source-specific identity systems.

# Intelligence Layer

The Intelligence Layer transforms remembered evidence into useful understanding. It may produce:

- Insights
- Predictions
- Risk detection
- Trend detection
- Duplicate detection
- Missing information
- Recommendations
- Knowledge gaps

Intelligence is evidence-bound. Every conclusion must be traceable to the memory that supports it. When evidence is weak, incomplete, contradictory, or insufficient, Barni must say so or remain silent.

The Intelligence Layer should distinguish among:

- What happened
- What changed
- Why it may matter
- How certain the conclusion is
- What evidence supports it
- Whether any action is useful now

Not every observation deserves to become an insight. Not every insight deserves a recommendation. Not every recommendation deserves an interruption.

Barni should rank understanding by usefulness, importance, and urgency. Ordinary events remain quiet. Significant changes become concise explanations. Predictions and risk signals require stronger safeguards than simple historical facts.

Knowledge gaps are part of intelligence. Recognizing what Barni does not yet know allows it to ask one useful question instead of making an unsupported assumption.

# Action Layer

The Action Layer turns supported understanding into clear, controlled next steps. Actions may include:

- Approve
- Review
- Export
- Contact supplier
- Prepare accountant package
- Prepare employee document
- Create reminder
- Generate report
- Create task

Every action should have a clear reason, expected outcome, and visible relationship to the evidence that prompted it.

Barni should recommend the smallest useful action. It must not automate consequential decisions merely because automation is possible. The user remains in control of approvals, communication, commitments, and other meaningful external changes.

Actions should close the learning loop. A review can correct memory. An approval can establish trust. A completed task can confirm that a recommendation was useful. The result should improve Barni's future understanding without creating noise or unnecessary administration.

# Experience Layer

One Barni. Many capabilities.

The user never needs to think about modules, data pipelines, integrations, or system boundaries. The user simply asks Barni, feeds Barni new information, reviews what deserves attention, and acts.

The Experience Layer should organize itself around user intent:

- What matters now?
- What does Barni need from me?
- What does Barni remember?
- What changed?
- What should I do next?

Capabilities may grow behind the experience, but the product should feel simpler as Barni becomes more capable. Context should follow the user. Evidence should appear when needed. Complexity and technical detail should remain hidden until explicitly requested.

Barni should speak with one calm, concise, professional voice across every capability. It should respond in the user's language, preserve continuity, and never expose the organizational structure of the underlying software as a burden the user must understand.

# Design Principles

## Every new feature must strengthen the operating system

A feature should improve at least one part of the shared loop: input, memory, intelligence, action, or experience. It should also make the other layers more valuable where possible. Features that create isolated data, duplicated truth, or disconnected workflows weaken Barni OS.

## Never become ERP

Barni should not reproduce dense administrative systems, endless configuration, or database-shaped workflows. It should reduce operational complexity by interpreting the business, not transfer that complexity into a new interface.

## Never become accounting software

Barni may understand financial evidence, prepare reliable information, and collaborate with accounting workflows. It should not replace the specialist systems responsible for bookkeeping, compliance, tax, or statutory accounting.

## Never duplicate functionality already solved by another product

When a trusted system already performs a task well, Barni should connect to it, understand its signals, and help the user act across it. Barni earns its place by creating context and understanding, not by rebuilding every business tool.

## Barni's value is understanding

The product should lead with meaning rather than records, recommendations rather than dashboards, and evidence rather than claims. Its advantage is the connected memory of how a specific business works.

## Trust grows before autonomy

Barni should earn permission through accurate memory, clear evidence, honest uncertainty, and reliable recommendations. Greater autonomy may follow proven trust; it must never precede it.

## One business, one memory

Every capability must contribute to and rely on the same canonical understanding. Conflicting identities, histories, totals, or operational states are critical defects.

## Silence remains part of the system

More inputs must not produce more noise. As Barni learns more, it should become better at deciding what not to surface.

# Long-term Vision

Barni becomes the business operating system for restaurants first.

Restaurants provide the right starting environment: many suppliers, changing prices, recurring purchases, operational documents, narrow margins, and owners who need fast answers without another complex system. Barni should first become exceptional at understanding this world.

Over time, the same architecture may serve:

- Retail
- Clinics
- Construction
- Professional services
- Small manufacturers

Expansion should follow proven understanding, not market breadth alone. Each industry has distinct language, relationships, risks, workflows, and evidence. Barni should enter a new vertical only when it can offer a coherent memory model and genuinely useful understanding for that business.

The long-term experience remains simple: a business owner can ask Barni what is happening, understand why it matters, see the evidence, and take the right next action.

Barni succeeds when the business feels understood.

# Business Facts Engine

The Business Facts Engine is the trust boundary between canonical memory and intelligence. The mandatory flow is:

`raw evidence → canonical identity → normalization → comparable fact → reasoning → insight → recommendation → action`

No intelligence service may bypass this boundary for a conclusion that depends on comparability. Fact builders are registered by fact type, so prices are the first implementation rather than a special-case architecture. VAT, cash flow, payroll, inventory, contracts, tax, and supplier-performance facts can add builders and typed ledgers without changing the lifecycle.

Each fact preserves its source, canonical identities, normalized values, evidence, component-level Business Confidence, trust status, and a plain-language status explanation. Business Confidence describes completeness of the factual basis; it is not model or AI confidence.

## Comparable Price Ledger

A price observation is trusted only when Barni can establish a canonical supplier, canonical product, normalized unit and package basis, positive quantity and price, currency, VAT basis, date, and source invoice and line. Package prices are converted to a shared base unit where the evidence supports that conversion. Credit notes remain evidence but are not purchase-price observations.

The ledger is the only shared authority for price compatibility. It rejects comparisons across products, normalized units, currencies, or VAT bases, and it never treats two lines from the same invoice as historical purchases. Every accepted or rejected comparison retains the two source invoice IDs and a human-readable reason.

Fact statuses are `TRUSTED`, `PARTIALLY TRUSTED`, `INSUFFICIENT DATA`, `IDENTITY CONFLICT`, `UNIT CONFLICT`, `PACKAGE CONFLICT`, `VAT CONFLICT`, `CURRENCY CONFLICT`, and `NOT COMPARABLE`. Conflicts that a person can resolve enter Identity Review; incomplete observations stay silent until better evidence exists.

## Business Story Engine

The Business Story Engine sits between intelligence and experience. It converts supported facts and explicit memory events into concise, evidence-linked explanations without changing their underlying meaning.

```text
Trusted facts and memory events
→ story selection and prioritization
→ one structured story contract
→ Home, Feed, Insights, and future notifications
```

Stories are channel-independent. Rendering, navigation, and visual treatment remain responsibilities of the Experience Layer. New story types register another evidence-backed interpretation of an existing fact or event; they must not add speculative reasoning inside templates.
