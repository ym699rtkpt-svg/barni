# BAR-002: Barni Design System

## Purpose

This document defines Barni's permanent visual and user-experience language. It applies to every user-facing screen and component unless a task explicitly states otherwise.

Barni should feel:

- Premium.
- Calm.
- Warm.
- Modern.
- Trustworthy.
- Simple.
- Intelligent.
- Human.

## Core UX Principle

Every screen should answer one primary question within five seconds.

Content, hierarchy, actions, and visual styling should all support that question. Anything that competes with it should be simplified, deferred, or removed.

## Screen Purposes

| Screen | Primary question |
| --- | --- |
| Home | How is my business doing right now? |
| Feed | How do I teach Barni something new? |
| Search | Where is the information I need? |
| Knowledge | What has Barni learned about my business? |
| Insights | What deserves my attention? |
| Recipes | What does this dish cost and how profitable is it? |

## Design Rules

1. Prefer whitespace over borders.
2. Prefer cards over dense tables when summarizing information.
3. Use tables for detailed data, not as the first thing the user sees.
4. Use concise, natural language.
5. Avoid technical terminology in user-facing content.
6. Use consistent spacing and typography.
7. Use soft rounded cards with subtle borders.
8. Do not use gradients unless explicitly requested.
9. Do not use loud colors.
10. Preserve Barni's warm beige and green identity.
11. Use green for positive movement, savings, or healthy states.
12. Use orange when something needs attention.
13. Use red only for a real problem or negative movement.
14. Use neutral gray for informational or unchanged states.
15. Never use color as the only signal. Pair it with clear text, a number, a label, or an icon.
16. Use icons sparingly and consistently.
17. Barni should speak like a capable business assistant, not a robot.
18. Avoid excessive emojis in the product UI.
19. Make important actions visually obvious.
20. Make empty states feel calm, useful, and helpful rather than alarming.

## Information Hierarchy

A typical Barni screen should follow this order when applicable:

1. A clear title or hero that answers what the screen is for.
2. A concise current-state summary.
3. The most important metrics or insights.
4. One obvious primary action.
5. Secondary actions and supporting information.
6. Detailed tables, history, and technical context last.

Do not show every available fact at once. Use progressive disclosure for details that are useful but not immediately necessary.

## Visual Language

### Color

- Warm beige provides the product's calm foundation.
- Muted green expresses the Barni identity and positive states.
- Soft orange signals attention without creating alarm.
- Restrained red is reserved for genuine problems or negative movement.
- Neutral gray supports secondary text, unchanged states, and quiet metadata.

Colors should remain soft, accessible, and readable. Favor contrast and clarity over decoration.

### Typography

- Use a clear, consistent heading hierarchy.
- Keep headings short and descriptive.
- Use sentence case for English labels unless an established label requires otherwise.
- Use smaller, quieter text for context and metadata.
- Avoid long paragraphs. Prefer one useful sentence.

### Spacing

- Use generous vertical spacing between distinct sections.
- Keep related content close together.
- Use consistent internal padding within cards.
- Avoid stacking separators, borders, and headings when whitespace is sufficient.

### Icons and Status Signals

- Use one familiar icon when it improves recognition.
- Keep the same icon meaning throughout the product.
- Pair status icons and colors with explicit text.
- Do not decorate every title or metric with an icon.

## Barni's Voice

Barni communicates like a calm, capable business assistant.

- Be direct, warm, and concise.
- Explain what changed and why it matters.
- Suggest an action only when the available data supports it.
- Acknowledge uncertainty when data is incomplete.
- Avoid database terms, implementation details, and robotic phrasing.
- Never overstate confidence or invent a business conclusion.

Prefer:

> Olive oil increased by 8% since the previous purchase.

Avoid:

> A positive price delta was detected in the invoice-items dataset.

## Reusable Visual Concepts

### Hero Card

The Hero Card establishes the screen's purpose and current state.

- Contains a short title, one supporting line, and optionally one status message.
- May include one primary action.
- Should be visually calm and spacious.
- Avoid competing metrics, long instructions, or multiple calls to action.

### Metric Card

The Metric Card communicates one important number.

- Contains one natural label and one clearly formatted value.
- May include a short comparison or context line.
- Uses consistent money, percentage, count, and date formatting.
- Avoids decorative content and unsupported status colors.

### Insight Card

The Insight Card explains a meaningful observation supported by stored data.

- Uses one short natural-language message.
- States the relevant product, supplier, amount, or change when available.
- Can include a restrained status icon or color.
- Does not include an action unless action is the card's purpose.

### Recommendation Card

The Recommendation Card turns a supported insight into a practical next step.

- Explains what changed.
- Provides one concise suggested action.
- Makes uncertainty and evidence limits clear.
- Never claims savings, supplier superiority, or risk without supporting data.

### Action Card

The Action Card gives the user a clear route to complete a task.

- Contains a short action title and one line explaining the outcome.
- Uses a visually obvious control.
- Distinguishes the primary action from secondary actions.
- Avoids placing several equally prominent actions together.

### Table Card

The Table Card presents detailed records after the screen's summary.

- Shows only useful columns by default.
- Uses human-friendly labels and consistent formatting.
- Keeps dates, currency, percentages, and statuses easy to scan.
- Hides secondary or technical columns when cleanly supported.
- Uses filtering, selection, or expansion only when it reduces clutter.

## Empty States

An empty state should explain what is missing and, when useful, what the user can do next.

- Use calm, neutral language.
- Avoid warning or error styling when nothing is wrong.
- Keep the message brief.
- Offer an action only when there is a clear next step.

Example:

> No purchase history yet. Add another invoice to start tracking price changes.

## Review Checklist

Before completing a UI change, confirm:

- The screen's primary question is clear within five seconds.
- The most important information appears first.
- The primary action is visually obvious.
- Summaries use cards or concise messages rather than dense tables.
- Detailed information appears after the summary.
- Spacing, labels, currency, dates, and statuses are consistent.
- Color is restrained and never the only signal.
- Empty states are calm and helpful.
- Barni's language is natural, concise, and supported by data.
- Existing functionality and business logic remain intact.

