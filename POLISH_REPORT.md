# Barni Polish Sprint Report

## Scope

This sprint refined Barni's presentation only. OCR, database schema, stored data,
and purchasing calculations were left unchanged. The product was reviewed from
the perspective of a restaurant owner opening each primary screen for the first
time.

## UI improvements made

### Product-wide visual system

- Added one shared warm beige and green visual foundation for page backgrounds,
  typography, controls, tables, alerts, expanders, and neutral empty states.
- Standardized rounded corners, subtle borders, content width, vertical rhythm,
  button height, and input styling.
- Removed the duplicated global page title so each screen now owns one clear
  heading and purpose.
- Reduced icon repetition in navigation and made internal tools quieter and
  secondary.
- Reworked the entry screen from a dark, glowing treatment to a calm Barni
  welcome with one clear action.

### Home

- Established a clear cockpit sequence: hero, Business Snapshot, Barni Today,
  Ask Barni, Quick Actions, and Recent Activity.
- Made **Feed Barni** the single primary action.
- Replaced introductory paragraphs with concise cards and a short, data-backed
  status sentence.
- Consolidated current business information into four scannable metric cards.
- Reduced emoji use and moved supporting activity below the decision-making
  content.

### Feed Barni

- Turned the uploader into a large, calm drop zone with concise instructions.
- Moved model selection into advanced settings so it does not compete with the
  upload task.
- Clarified reading, review, duplicate, saving, and learning progress.
- Added consistent summary, confidence, duplicate-warning, and completion cards.
- Replaced developer-facing processing errors with helpful language; technical
  details remain available in a collapsed disclosure.
- Removed the unfinished "module is being migrated" placeholder by routing the
  Feed component to the existing production workflow.

### Search

- Made the search field the visual focus, with immediate results and advanced
  filters kept in a disclosure.
- Added compact result metrics and supplier-grouped result sections.
- Standardized date and currency presentation in result tables.
- Replaced the dead-end no-results caption with a calm, useful empty state.
- Replaced raw preview failures with human language and optional technical
  details.

### Knowledge

- Strengthened the order of supplier header, snapshot, insights,
  recommendations, products, and history.
- Applied consistent metric, insight, recommendation, product, chart, and table
  card treatments.
- Kept detailed invoice data secondary in an expander.
- Improved the no-supplier state with a clear next step.
- Preserved all supplier and price calculations.

### Insights

- Replaced the flat metric-and-table opening with a concise, data-backed hero and
  four-card business snapshot.
- Paired the key purchasing charts in a balanced layout.
- Moved category and document-type details into tabs below the overview.
- Moved classification maintenance into a collapsed internal section and
  removed raw JSON from the normal experience.

### Business Memory

- Retained the learning-first hierarchy and card-based overview.
- Kept detailed knowledge growth and recent learning below the primary memory
  summary.
- Used calm empty-state language when stored history is not yet available.

### Recipes

- Removed the hard-coded sample recipe and costs from the visible experience.
- Replaced it with an intentional, trustworthy empty state that does not present
  invented business data as fact.

### Accountant Workspace and Pilot Dashboard

- Kept their existing workflows and data sources intact.
- Aligned cards, metrics, status language, loading feedback, and section spacing
  with the shared Barni system.
- Kept operational detail below the primary readiness and health summaries.

## Before / after

| Area | Before | After |
| --- | --- | --- |
| First impression | Competing titles and inconsistent page treatments | One page purpose, one visual hierarchy, one warm system |
| Actions | Several controls carried similar visual weight | One obvious primary action; secondary controls are quieter |
| Information density | Metrics, tables, and technical detail appeared early | Summary cards first; detail lower or collapsed |
| Feedback | Mixed alerts, raw errors, and unfinished placeholders | Calm empty states, professional progress, optional technical detail |
| Consistency | Page-specific spacing, borders, colors, and controls | Shared spacing, typography, cards, controls, and color semantics |
| Trust | A sample recipe could look like stored business data | Unsupported sample values are no longer presented as business facts |

## Remaining UI issues

- Several legacy diagnostic pages still use older Hebrew-first layouts and raw
  developer language. They are currently confined to the collapsed Internal
  tools area; role-based visibility would be the safest later improvement.
- Some primary screens mix Hebrew and English. A deliberate localization policy
  is needed before standardizing copy, because automatic translation could alter
  the product's intended language.
- Streamlit tables remain appropriate for detailed records but offer limited
  responsive control on narrow screens.
- Some known data-state wording can only be improved by changing how comparison
  eligibility is represented. That is business logic and was intentionally not
  changed in this UI-only sprint.
- A browser-based visual regression suite does not yet exist, so spacing and
  responsive behavior still require a short manual review at desktop and tablet
  widths before a live pilot.

## Recommendations for the next polish sprint

1. Run a focused bilingual copy audit and define one language rule per screen.
2. Add screenshot-based visual regression checks for the nine primary routes.
3. Test desktop, tablet, and small-laptop widths with real pilot data.
4. Add role-based separation for Internal tools without changing their behavior.
5. Create one reusable page-header and empty-state component after the current
   visual patterns have been validated with the pilot restaurant.

## Verification

- Compiled every edited Python module with `python3 -m py_compile` successfully.
- Ran `init_database()` against the existing database successfully.
- Verified SQLite integrity before and after initialization: `ok`.
- Verified stored counts remained unchanged: 65 invoices and 222 invoice items.
- Started the real Streamlit application and received `ok` from
  `/_stcore/health`.

