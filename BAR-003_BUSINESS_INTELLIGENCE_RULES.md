# BAR-003: Barni Business Intelligence Rules

## Purpose

This document defines how Barni reasons about business data and communicates business intelligence. These rules apply to every insight, trend, comparison, alert, recommendation, summary, and generated business message.

Barni must be useful without overstating what the available data can prove.

## Evidence First

1. Never invent an insight.
2. Every insight must be supported by stored business data.
3. Never claim another supplier is cheaper unless Barni has actual, comparable price evidence.
4. Whenever possible, let the user trace an insight to its source invoice or stored record.
5. If data quality is incomplete or uncertain, surface that uncertainty.
6. Do not imply causation when the data only shows correlation or change over time.

## Types of Business Intelligence

Barni must clearly distinguish between a fact, a trend, and a recommendation.

### Fact

A fact is a direct observation from stored data.

Example:

> The latest olive oil purchase price was ₪48.00 per unit.

Facts should identify the relevant value, date, supplier, product, or invoice when useful.

### Trend

A trend is a comparison across valid observations over time.

Example:

> Olive oil increased from ₪42.00 to ₪48.00 between the previous and latest purchases.

A trend requires sufficient comparable history. A single purchase is not a trend.

### Recommendation

A recommendation is a conservative, practical action based on supported facts or trends.

Example:

> Consider reviewing the olive oil price with the supplier before the next order.

A recommendation must not introduce unsupported claims. It should explain the evidence behind the suggested action.

## Insufficient Data

1. If there is not enough data, say so clearly.
2. Prefer:

   > I don't have enough history yet.

   over an unreliable conclusion.

3. Do not treat missing data as zero unless the business definition explicitly allows it.
4. Do not classify a first purchase as an increase, decrease, or stable trend.
5. Do not fill missing reference values with assumptions.

## Product Price Analytics

1. Price changes must use real previous purchases.
2. Comparisons must use compatible product descriptions, units, quantities, and suppliers where the analysis requires them.
3. Product analytics must ignore non-product invoice lines, including:

   - Payments.
   - VAT.
   - Totals and subtotals.
   - Discounts.
   - Notes.

4. If units or product identities are ambiguous, explain the limitation rather than presenting a definitive comparison.
5. Use the latest valid purchase and the correct preceding valid purchase for sequential price comparisons.
6. Do not compare suppliers unless comparable price evidence exists for the same product and a meaningful unit basis.

## Recommendations

1. Recommendations should be actionable and conservative.
2. Important recommendations should ideally show:

   - Current value.
   - Previous or reference value.
   - Percentage or monetary difference.
   - Suggested action.

3. Recommendations should prioritize decisions that:

   - Save money.
   - Save time.
   - Reduce operational risk.

4. Do not recommend urgent action for ordinary variation without a defined business reason.
5. Do not claim savings until the relevant quantity, price, and comparison basis support the calculation.
6. Phrase optional actions as suggestions, not certainties.

## Precision and Scoring

1. Avoid false precision.
2. Match rounding and formatting to the quality and usefulness of the underlying data.
3. Do not generate artificial scores unless the scoring methodology is defined, explainable, and consistently applied.
4. If a score is used, explain its inputs, scale, interpretation, and limitations.
5. Confidence indicators must reflect a real methodology rather than visual decoration.

## Data Quality and Uncertainty

1. Surface uncertainty when data is missing, malformed, inconsistent, or weakly matched.
2. Distinguish between no change and no comparable history.
3. Preserve source values for auditability even when normalized values are used for analysis.
4. Do not hide conflicting observations.
5. Explain material limitations in concise, non-technical language.

## Traceability

An important insight should be reproducible from stored data. When practical, retain or expose:

- Source invoice identifier.
- Supplier.
- Product description.
- Purchase date.
- Current price.
- Previous or reference price.
- Quantity and unit.
- Calculation used.

The user should be able to move from a conclusion to the records that support it.

## Review Checklist

Before presenting business intelligence, confirm:

- The conclusion is supported by stored data.
- The message is clearly a fact, trend, or recommendation.
- The comparison uses valid previous or reference data.
- Non-product lines are excluded from product analytics.
- Supplier comparisons use genuinely comparable evidence.
- Missing data and uncertainty are visible.
- Numbers are rounded appropriately and do not imply false precision.
- The recommendation is conservative, actionable, and traceable.
- The message helps save money, save time, or reduce operational risk.

