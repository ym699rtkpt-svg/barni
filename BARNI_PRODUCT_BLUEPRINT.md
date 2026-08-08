# Barni Vision

Barni is an AI business companion that remembers how a business operates and helps its people understand what matters. It learns from invoices, suppliers, products, prices, purchasing patterns, costs, and everyday business activity, then turns that memory into useful answers and clear next steps.

Barni is not an OCR application. OCR is one supporting capability that helps Barni learn from documents; it is not the product experience. The product should feel like a trusted colleague who knows the business, recalls evidence quickly, and makes information easier to understand and act on.

# Design Principles

- Calm
- Premium
- Fast
- Minimal
- Professional
- Every screen has one clear purpose.

# User Experience Rules

- Never overwhelm the user.
- Only one primary action per screen.
- Hide complexity until needed.
- Use progressive disclosure.
- Empty space is good.
- Information hierarchy is more important than adding features.

# Search Philosophy

Search is Barni's brain.

Search must feel like Spotlight on macOS. The user should never browse a database. The user simply asks a question or types what they remember, and Barni immediately narrows the results while they type.

Opening an invoice replaces the search results with a dedicated invoice view. The Search page should never become infinitely long.

Recent invoices are shown only when there is no active search. Suggestion chips appear only when there is no active search. Advanced filters stay collapsed by default.

# Design Rules

- No duplicated sections.
- No duplicated invoice lists.
- No endless scrolling.
- Every component must justify its existence.
- Every page should fit naturally on one screen before scrolling.

# Development Rules

- Never redesign the application without approval.
- Never change database logic unless requested.
- Never remove features without approval.
- Always preserve backwards compatibility.
- Always explain why a UI change improves usability.
- This document must be updated before implementing any major feature.

# Intelligence Architecture

Barni's intelligence must be independent from any individual screen. Intelligence services receive business facts and history, evaluate small evidence-based rules, and return structured insights. Rendering belongs to the UI; reasoning does not.

Every insight must include a clear title, natural description, severity, category, and confidence. Rules must be modular, conservatively ranked, and easy to extend without changing existing consumers. A rule should remain silent when the available evidence is insufficient.

Proactive intelligence extends this same engine across multiple records. Proactive results must also retain structured evidence, source record IDs, priority, and an optional proportionate next action. Experiences consume these results but never recreate their business rules. Strong signals may be surfaced in Invoice Review or Home; weak or redundant signals remain silent.

# Identity and Evidence Architecture

Barni's conclusions depend on a canonical Business Identity layer between stored source data and intelligence.

- A canonical supplier has one stable identity, one preferred name, an optional normalized VAT ID, and many source-backed aliases.
- A canonical product has one stable identity, one preferred name, many source-backed aliases, and normalized unit and packaging observations.
- Every stored invoice links to its canonical supplier.
- Every product line links to its canonical product and retains its normalized unit and packaging observation.
- Original supplier names and product descriptions remain unchanged as evidence.
- Automatic matching uses only strong deterministic evidence: normalized VAT IDs or exact normalized aliases for suppliers, and exact normalized descriptions for products.
- Ambiguous identities remain separate until the user explicitly confirms a merge.
- Canonical names may change without changing the evidence that taught Barni.
- Confirmed merges and renames are recorded as decisions.

Every structured insight must carry its evidence values and source record IDs. The evidence path must lead back to stored invoices and their original documents. Interfaces may keep evidence collapsed by default, but they must provide a way to explain a conclusion and open its sources.

Price and behavior comparisons must use canonical identities and only comparable normalized units and packaging. If comparability cannot be established, Barni stays silent.

Identity resolution, normalization, and evidence linking are shared services. Search, Invoice Review, Home, Business Memory, and future experiences consume the same identities and must never implement competing matching logic.

# Identity Review Experience

Identity Review is a focused learning workflow entered from Business Memory when Barni has a valuable unresolved identity question. It must never feel like a database administration or settings page.

The screen has one primary purpose: help Barni resolve the highest-impact uncertainty. It leads with one conversational statement, explains why Barni thinks it, shows confidence, and presents the original source invoices side by side. Detailed correction tools and previous decisions remain progressively disclosed.

The queue shows no more than five prioritized reviews. Confirming a match, keeping identities separate, acknowledging a meaningful variation, merging, splitting, renaming, and undoing are real actions backed by the same canonical identity service. Pages must not mutate identity tables directly.

User decisions are durable but reversible. Merges deactivate rather than delete canonical identities. Splits move selected evidence into a new identity. Renames preserve source text. Rejections use a stable candidate fingerprint so Barni does not repeat the same unsupported question. Undo restores the recorded previous state and never deletes evidence.

The customer sees natural language, evidence, and the next action. Internal IDs, matching algorithms, database fields, and decision snapshots remain hidden. Confidence percentages are shown only inside this explicit teaching context because the user is deciding whether Barni's proposed relationship is correct.

Identity Review is complete only when the resulting canonical truth is immediately reused by Business Memory, Search, Barni Thinking, proactive intelligence, and price comparisons.

# Business Facts Product Contract

Barni must never present a comparison as knowledge merely because two raw values exist. Comparable Business Facts sit between identity and intelligence and are the permanent source of truth for conclusions that require normalization.

For price facts, the product contract requires canonical supplier and product identities, normalized unit and package size, quantity, currency context, VAT basis, observation date, and invoice-line evidence. The shared ledger returns either a trusted comparable fact or a specific, explainable reason why comparison is unsafe.

The interface should expose conclusions in Barni's natural voice and keep technical confidence components progressively disclosed. It must never hide uncertainty, silently convert incompatible values, or ask the user to resolve low-value noise. Actionable identity, unit, package, VAT, and currency conflicts enter the existing Identity Review queue. Insufficient data stays quiet.

Every future intelligence feature that depends on comparable data must consume Business Facts. Duplicating normalization, evidence construction, or price compatibility inside a page or insight rule is a product-integrity defect.

# Business Story Architecture

Business Stories are Barni's shared explanation layer. They turn trusted facts, canonical memory changes, and explicit workflow outcomes into short answers to: “What happened since I last checked?” Home, Feed, Insights, and future notifications consume the same structured stories rather than composing their own summaries.

Every story contains a type, title, concise explanation, category, priority, tone, structured evidence values, source invoice evidence, and an optional proportionate action. Story generation does not introduce new inference. It narrates conclusions already supported by the Business Facts Engine, Business Memory, Identity Review, or an explicit approval outcome.

Meaningful changes rank above ordinary memory growth. Weak or unsupported conclusions stay silent. A quiet state may say “Everything looks good,” but it must not manufacture activity. Evidence is progressively disclosed and must lead back to the supporting invoice.
