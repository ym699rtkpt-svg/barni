# Barni Engineering Playbook

## Status and Authority

This document defines how Barni is engineered. It is the engineering operating system for everyone who contributes to the product, not a coding style guide.

Read this playbook before designing or implementing any change. Use it together with the Barni Constitution, Product Blueprint, Business Brain, Operating System, User Journeys, and active canonical architecture contracts. When implementation and canonical documentation disagree, stop and resolve the disagreement before proceeding.

## Mission

Barni is not an invoice application.

Barni is a Business Understanding Platform.

Every engineering decision should move the product closer to its company mission:

> From data to understanding.

If a feature does not increase understanding, reconsider building it.

## Engineering Philosophy

Optimize for:

- Truth over convenience.
- Understanding over dashboards.
- Evidence over assumptions.
- Trust over cleverness.
- Consistency over speed.
- Simple architecture over premature optimization.
- Reusable business models over duplicated logic.

These are decision priorities. When two reasonable approaches conflict, choose the one that ranks higher in this list unless a documented product requirement establishes a stronger constraint.

## The Golden Rules

1. **One source of truth.** A business concept, workflow state, calculation, or contract has one canonical owner.
2. **Business rules never live inside UI.** Presentation renders decisions made by domain services; it does not recreate them.
3. **Every important decision must be explainable.** Barni must be able to describe what it concluded and why.
4. **Every insight must be backed by evidence.** Unsupported conclusions remain silent.
5. **Every Business Fact has an owner.** Its producing service defines its lifecycle, validation, and contract.
6. **Every workflow has one canonical implementation.** Pages and integrations consume the workflow; they do not invent local variants.
7. **Every migration must be reversible.** Preserve data, define rollback or recovery, and avoid destructive transformation without an explicit plan.
8. **Every public behavior must be testable.** If behavior cannot be verified reliably, its contract is incomplete.
9. **Prefer composition over duplication.** Assemble established capabilities instead of recreating their logic.
10. **If something feels clever, simplify it.** Clarity is an architectural property.

## Architecture Decision Flow

Before writing code, classify the responsibility.

### UI

Presentation, interaction, layout, and navigation. UI may format domain output and collect user intent. It must not determine identity, lifecycle state, Business Facts, evidence validity, insight meaning, or workflow outcomes.

### Business logic

Rules that determine what business data means. Business logic belongs in reusable domain services and must be independent of a specific page.

### Domain model

Canonical language and invariants for business entities, value objects, claims, facts, decisions, and states. Domain models should express meaning without depending on Streamlit, database rows, or transport formats.

### Infrastructure

Persistence, file storage, OCR adapters, external APIs, queues, and delivery mechanisms. Infrastructure implements domain-facing contracts without becoming the owner of business meaning.

### Evidence

Traceable references connecting a claim to its source. Use the canonical Evidence Contract. Never introduce a producer-specific substitute when `EvidenceRef` applies.

### Identity

Canonical suppliers, products, aliases, units, packages, and reversible user decisions. Uncertain identities enter the Identity Review workflow; they are never merged silently.

### Business Fact

An immutable, normalized, evidence-bound observation that the business can safely reason over. Facts are produced by the Business Facts Engine, not inferred in UI.

### Workflow

A coordinated lifecycle with canonical states, transitions, side effects, idempotency, and recovery behavior. A workflow must have one implementation shared by every consumer.

If a change crosses several categories, define the boundaries and data flow first. Never solve a business problem inside presentation code because that is the shortest route to visible output.

## Required Pre-Implementation Review

Before implementation:

1. State the user outcome and how it increases understanding.
2. Identify the canonical model or service that owns the behavior.
3. Search for existing implementations and contracts.
4. Trace required input data to its authoritative source.
5. Define evidence and confidence requirements.
6. Identify workflow, migration, compatibility, privacy, and failure risks.
7. Define observable acceptance criteria and tests.
8. Update canonical documentation before a major architectural feature when required by the Constitution.

Do not begin by choosing a component, database table, or framework technique. Begin by establishing ownership and truth.

## When to Create a New Service

Create a service only when all of the following are true:

- It owns one coherent responsibility.
- It has a clear domain boundary.
- No existing service should own that responsibility.
- Its public contract improves architectural clarity.
- It can be tested independently of UI.
- Its inputs, outputs, evidence responsibilities, and failure behavior are defined.

Never create a service merely to reduce file size, rename a function group, or hide duplication behind another interface.

A new service proposal should answer:

- What truth does it own?
- What does it explicitly not own?
- Who produces its inputs?
- Who consumes its outputs?
- How is it versioned and tested?
- How does it fail safely?

## When to Modify Existing Code

Prefer extending an existing coherent model over introducing parallel logic.

Before adding code:

- Search for existing rules, queries, models, normalization, evidence construction, and workflow transitions.
- Use the existing owner when its responsibility already covers the requirement.
- Strengthen a weak contract instead of bypassing it.
- Preserve backwards compatibility unless an approved migration explicitly changes public behavior.
- Avoid convenience helpers that become alternative sources of truth.

If two implementations already exist, do not add a third. Identify the canonical owner, define compatibility behavior, migrate consumers, test parity, and retire the duplicate safely.

## Business Facts

Business Facts are immutable observations.

They are not UI models. They are not AI outputs. They are not narrative copy. They are trusted representations of the business.

Every Business Fact must include or resolve:

- Business scope.
- Fact type and canonical subject.
- Normalized value and comparison basis where applicable.
- Trust status and reason.
- Typed confidence appropriate to fact trust.
- Supporting evidence.
- Observation time.
- Producing service and version.

Every future intelligence feature must consume Business Facts rather than raw invoice lines whenever the required fact type exists. If the required fact does not exist, extend the Business Facts Engine deliberately; do not reproduce normalization inside an insight rule or page.

Facts that cannot be trusted must fail closed. Preserve the source observation, explain the conflict, and route appropriate uncertainty into Identity Review.

## Evidence

Every claim must be traceable. There are no exceptions for convenient copy, quiet summaries, positive messages, or internally generated conclusions.

Use the canonical `EvidenceRef` and Claim contract. Evidence must identify:

- The business.
- Source type and stable source record.
- Relevant subrecord when applicable.
- Observed value and field when useful.
- Capture time and source location when available.
- Integrity reference when supported.

Evidence should be reusable across:

- Invoices.
- Search.
- Narrative.
- Attention.
- Business Memory.
- Identity Review.
- Accountant workflows.
- Future integrations.

Presentation may summarize evidence, but it must never replace or mutate the structured evidence chain. A user-facing source action must resolve through the shared evidence contract and open the correct record.

## Confidence

Never mix:

- Extraction confidence.
- Identity confidence.
- Fact trust.
- Observation confidence.
- Answer confidence.

Each answers a different question:

| Confidence type | Question answered |
|---|---|
| Extraction | How reliably was a source value read? |
| Identity | How strongly does evidence support an entity match? |
| Fact trust | Is the normalized Business Fact safe to use? |
| Observation | How strongly do trusted facts support the detected condition? |
| Answer | How well is the user-facing conclusion grounded? |

Do not average these types or use one as a substitute for another. Cross-layer reasoning must retain separate assessments or use an explicit, documented policy. Normal users should receive calm qualitative language, not raw confidence values, unless they request technical details.

## Workflows and State

Each workflow must define:

- Canonical states.
- Legal transitions.
- Transition ownership.
- Idempotency rules.
- Side effects and their order.
- Retry and recovery behavior.
- Audit information.
- Consumer-visible snapshots and counters.

No page may infer workflow state from ad hoc fields when a canonical workflow contract exists. The trusted invoice lifecycle owns invoice status and readiness. Feed, Home, Search, Business Memory, and Accountant Workspace must consume the same lifecycle interpretation.

## Identity and Reversibility

Future intelligence reasons over canonical identities. Alias and normalization decisions therefore require evidence, clear ownership, and reversibility.

- Never silently merge uncertain identities.
- Preserve original source observations.
- Record who made a decision, when, why, and from which evidence.
- Make confirmation, rejection, merge, split, rename, and undo coherent operations.
- Ensure confirmed identity knowledge propagates consistently to Search, Memory, Facts, and intelligence.
- Reopen a settled question only when genuinely conflicting evidence appears.

Reversibility does not mean destructive rollback. It means adding a traceable corrective decision while retaining history.

## Migrations and Compatibility

Every migration must define:

- The existing data shape.
- The target data shape.
- Forward transformation.
- Rollback or recovery path.
- Compatibility window.
- Backfill strategy where required.
- Idempotency behavior.
- Verification queries or tests.
- Failure handling and backup requirements.

Migrations must preserve customer data and established public behavior unless an approved specification says otherwise. Prefer additive evolution, compatibility readers, and controlled retirement over flag-day replacement.

Do not ship an undocumented schema or semantic migration.

## Testing

Every implementation should answer:

- Can this be tested?
- Can it fail safely?
- Can it be explained?
- Can another developer understand it six months from now?

### Minimum testing expectations

- Domain invariants have focused unit tests.
- Workflow transitions have integration tests, including retries and repeated execution.
- Evidence resolves to the correct business and source.
- Supported claims fail when required evidence is absent.
- Confidence types cannot be mixed accidentally.
- Business Facts test accepted and rejected normalization cases.
- Database migrations test clean installation, upgrade, idempotency, and preservation.
- Public UI behavior has proportional runtime or interaction verification.
- Existing regression suites pass.
- Real representative data validates important business conclusions without fabricated history.

Tests should verify behavior rather than implementation details wherever possible. A test suite is part of the product contract, not a final ceremony after coding.

## Safe Failure

When Barni lacks evidence, identity, normalization, or comparable history:

- Preserve the source data.
- Do not promote the conclusion to trusted.
- Explain the limitation calmly.
- Route resolvable uncertainty to the correct review workflow.
- Avoid side effects that imply success.
- Make retry safe.

Silence is better than a weak insight. An explicit unknown is better than false certainty.

## Stop Conditions

Stop implementation if you discover:

- Duplicate business logic.
- A conflicting workflow.
- A hidden source of truth.
- A circular dependency.
- Evidence that cannot be traced.
- A business rule inside UI.
- An architecture conflict.
- An undocumented migration.
- Missing tests for public behavior.

When a stop condition appears:

1. Do not work around it silently.
2. Document the conflicting implementations, affected consumers, and user risk.
3. Identify the canonical owner or record the missing decision.
4. Propose the smallest safe unification or migration.
5. Continue only when the conflict is resolved or explicitly accepted with scope and rationale.

Stop conditions protect product trust. They are not invitations to broaden an implementation without approval.

## Code Review Checklist

Every pull request should verify the following.

### Architecture

- [ ] Responsibility is in the correct layer.
- [ ] A canonical owner is identified.
- [ ] No parallel service or hidden source of truth was introduced.
- [ ] Dependencies point in a clear direction without cycles.

### Business correctness

- [ ] Rules match the approved product contract.
- [ ] Edge cases and insufficient-data behavior are defined.
- [ ] Workflow state and counters use canonical definitions.

### Evidence and trust

- [ ] Every important claim is evidence-backed.
- [ ] Evidence is business-scoped and opens the correct source.
- [ ] Confidence uses the correct type.
- [ ] Unsupported conclusions fail closed.
- [ ] User-facing language does not exaggerate certainty.

### Performance

- [ ] The implementation avoids unnecessary repeated queries or materialization.
- [ ] Expected data volume and latency are understood.
- [ ] Optimization does not obscure correctness or duplicate truth.

### Readability

- [ ] Public contracts and ownership are clear.
- [ ] Names express business meaning.
- [ ] Complex decisions explain why, not merely how.
- [ ] Another developer can extend the solution safely.

### Test coverage

- [ ] New public behavior is tested.
- [ ] Failure, retry, and compatibility paths are covered.
- [ ] The full relevant regression suite passes.
- [ ] Meaningful conclusions are validated against real or representative evidence.

### Migration safety

- [ ] Migration and rollback or recovery are documented.
- [ ] Existing data and public behavior are preserved.
- [ ] Repeated execution is safe.

### User experience

- [ ] The change increases understanding or reduces effort.
- [ ] The primary action remains clear.
- [ ] Empty, loading, and error states are calm and useful.
- [ ] Technical implementation language stays out of normal UI.

### Future extensibility

- [ ] The design composes with canonical Identity, Facts, Evidence, Workflow, and Memory contracts.
- [ ] Extension points are deliberate rather than speculative.
- [ ] The change does not prematurely turn Barni into an ERP, accounting package, or dashboard collection.

## Operating Roles

Barni uses seven permanent operating roles. A role is a decision responsibility, not necessarily a dedicated person. One contributor may perform several roles when the team is small, but each role must produce its own explicit result. No role may approve on behalf of another without performing that role's review.

The roles are:

1. Builder.
2. QA Lead.
3. Customer Success.
4. Product Critic.
5. Restaurant Owner.
6. Ship Check.
7. Release Manager.

## Role Contracts

### Builder

**Mission**

Turn an approved product outcome into the smallest coherent implementation that satisfies Barni's existing contracts.

**Inputs**

- Approved user outcome and acceptance criteria.
- Canonical product, architecture, workflow, evidence, and design documents.
- Existing implementation, tests, migrations, and known constraints.
- Findings returned by later operating roles.

**Outputs**

- Focused implementation and migrations when required.
- Tests and verification evidence proportional to risk.
- Updated canonical documentation when behavior or contracts change.
- A concise handoff describing changes, verification, and remaining risk.

**Success Criteria**

- The requested outcome works without introducing parallel truth or unrelated scope.
- Business behavior remains explainable, evidence-backed, safe to retry, and testable.
- Relevant automated checks pass before QA handoff.

**Never Do**

- Invent product scope or unsupported business conclusions.
- Hide business rules in UI or introduce a second implementation of an owned concept.
- Bypass a stop condition, failed test, migration risk, or unresolved review finding.
- Declare the feature released.

### QA Lead

**Mission**

Determine whether the implementation satisfies its acceptance contract reliably, including failure, retry, compatibility, and regression behavior.

**Inputs**

- Builder handoff and changed behavior.
- Acceptance criteria, tests, risk assessment, and representative data.
- Canonical workflow, evidence, confidence, and migration contracts.

**Outputs**

- QA approval or a prioritized defect report.
- Reproducible evidence for the paths tested.
- Regression, recovery, performance, and data-integrity findings.
- Explicit untested areas and residual risk.

**Success Criteria**

- Public behavior is verified against requirements rather than implementation assumptions.
- Critical paths, expected failures, and safe retries are exercised proportionally to risk.
- Approval is supported by reproducible evidence with no unresolved release-blocking defect.

**Never Do**

- Approve because the happy path worked once.
- Treat a passing unit suite as complete product verification.
- Rewrite the acceptance criteria to match the implementation.
- Conceal intermittent, environmental, or untested risk.

### Customer Success

**Mission**

Verify that a customer can understand, recover from, and complete the changed workflow without expert assistance.

**Inputs**

- QA-approved build and known limitations.
- Target customer journey and representative restaurant context.
- Customer-facing language, loading, empty, success, and recovery states.

**Outputs**

- Customer Success approval or a friction report.
- Observed hesitations, dead ends, support dependencies, and recovery gaps.
- Required customer guidance and pilot-operational notes.

**Success Criteria**

- The next action is clear throughout the workflow.
- Normal users are not exposed to technical terminology or internal recovery work.
- Failures explain what happened and provide a safe next step.
- The change does not create avoidable support burden.

**Never Do**

- Assume customers understand Barni's internal models or implementation language.
- Approve a workflow that requires undocumented staff intervention.
- Replace direct observation with intended UX behavior.
- Turn product defects into training material instead of reporting them.

### Product Critic

**Mission**

Challenge whether the change deserves to exist and whether it improves Barni without adding avoidable complexity.

**Inputs**

- Customer Success-approved experience.
- Original user problem, acceptance criteria, and product documents.
- Before-and-after behavior and any added concepts, controls, or screens.

**Outputs**

- Product Critic approval or a focused critique.
- Findings on hierarchy, duplication, cognitive load, language, and scope.
- A recommendation to keep, simplify, remove, or return the change.

**Success Criteria**

- The change strengthens the core customer journey and company mission.
- Every visible element has a justified purpose.
- The result is simpler to understand than the problem it solves.
- Product value is not dependent on novelty, decoration, or speculative capability.

**Never Do**

- Protect an earlier decision from valid criticism.
- Approve complexity because implementation effort has already been spent.
- Expand the feature during review.
- Prioritize internal elegance over customer understanding.

### Restaurant Owner

**Mission**

Confirm that the change creates recognizable business value in a real restaurant workflow.

**Inputs**

- Product Critic-approved experience.
- A realistic business scenario and representative data.
- The task the feature claims to improve and its expected time or decision benefit.

**Outputs**

- Confirmation of business value or a clear rejection.
- Observed completion result, time, hesitation, and trust concerns.
- Plain-language explanation of whether the change would be used in practice.

**Success Criteria**

- The owner understands what happened, what matters, and what to do next.
- The feature measurably reduces effort or supports a better business decision.
- The owner trusts the result and can reach its evidence when needed.

**Never Do**

- Confirm value based only on a product demonstration or explanation.
- Represent internal team preference as restaurant-owner evidence.
- Accept unsupported claims, unclear status, or hidden manual work.
- Approve a feature merely because it works technically.

### Ship Check

**Mission**

Make an independent release recommendation using the complete evidence from every prior role.

**Inputs**

- Builder, QA, Customer Success, Product Critic, and Restaurant Owner outputs.
- Test results, acceptance evidence, migration and rollback plans, operational readiness, and known risks.
- Release scope and target environment.

**Outputs**

- A recommendation of `SHIP`, `CONDITIONAL SHIP`, or `DO NOT SHIP`.
- Exact evidence supporting the recommendation.
- Any unmet gate, release condition, monitoring need, or rollback trigger.

**Success Criteria**

- Every required gate is evaluated explicitly.
- The recommendation reflects verified evidence rather than schedule pressure.
- Residual risks have an owner, containment plan, and acceptable consequence.

**Never Do**

- Resolve product or technical defects by lowering a gate.
- Infer approval from silence or incomplete evidence.
- Hide conditions inside a positive recommendation.
- Make the final release decision.

### Release Manager

**Mission**

Own the final release decision and ensure an approved build can be released, observed, and recovered safely.

**Inputs**

- Ship Check recommendation and the complete release evidence record.
- Release gates, target environment, deployment plan, rollback or recovery plan, and accountable owners.
- Any explicit conditions attached to prior approvals.

**Outputs**

- A recorded decision of `RELEASE`, `HOLD`, or `REJECT`.
- Release version, scope, timing, conditions, and responsible operator.
- Post-release verification and rollback expectations.

**Success Criteria**

- Only the reviewed artifact and approved scope are released.
- Every mandatory gate is satisfied and every condition is closed before release.
- The release can be verified and recovered without ambiguity.
- The decision and its evidence remain auditable.

**Never Do**

- Override a failed mandatory gate because of a deadline, sunk cost, or stakeholder pressure.
- Release an artifact different from the one reviewed.
- Accept an unknown owner for a material risk or recovery action.
- Treat deployment completion as proof of release success.

## Build Pipeline

Every releasable change moves through the following sequence:

```text
Builder
  ↓
QA Lead
  ↓
Customer Success
  ↓
Product Critic
  ↓
Restaurant Owner
  ↓
Ship Check
  ↓
Release Manager
  ↓
Release Decision
```

Each stage receives the approved output of the previous stage. A rejection returns the change to the Builder with the finding and required acceptance condition. After the Builder responds, the pipeline resumes at the rejecting role and repeats any later checks invalidated by the change.

Handoffs must identify the exact artifact, scope, evidence, unresolved risk, and decision. Verbal confidence, partial progress, or an unrecorded demonstration is not a handoff.

## Release Gates

A change may advance only when the current gate produces explicit evidence.

| Gate | Owner | Required evidence | Failure result |
|---|---|---|---|
| Build | Builder | Scoped implementation, passing relevant checks, migration safety where applicable, and implementation handoff | Return to implementation |
| Quality | QA Lead | Acceptance, regression, failure, retry, and integrity results proportional to risk | Defect returned to Builder |
| Customer usability | Customer Success | Assisted and unassisted workflow observations, understandable recovery, and no unresolved dead end | Friction returned to Builder |
| Product quality | Product Critic | Clear purpose, justified complexity, coherent hierarchy, and alignment with canonical product rules | Simplify, remove, or return |
| Business value | Restaurant Owner | Realistic task completion and observable time, confidence, or decision value | Reject or redefine the outcome |
| Ship readiness | Ship Check | Complete prior approvals, operational readiness, known-risk review, and recoverability | `CONDITIONAL SHIP` or `DO NOT SHIP` |
| Release authorization | Release Manager | Closed conditions, exact reviewed artifact, release plan, ownership, and rollback or recovery plan | `HOLD` or `REJECT` |

Mandatory gates cannot be waived. A conditional result is not approval; it records work that must close before the next stage. Evidence must identify the build or revision reviewed so that later code changes cannot inherit stale approval.

## Release Decision Process

1. **Assemble the release record.** The Release Manager collects the exact artifact identifier, intended scope, all role outputs, test and acceptance evidence, migration and recovery plans, operational configuration, known limitations, and Ship Check recommendation.
2. **Validate gate completion.** Every mandatory gate must show explicit approval for the same artifact. Missing, conditional, stale, or contradictory evidence keeps the release on hold.
3. **Assess residual risk.** Remaining non-blocking risks must have a documented consequence, probability, owner, containment, and post-release verification method. Release pressure does not change severity.
4. **Choose one decision.** `RELEASE` means every gate passed and operations are ready. `HOLD` means the build may become releasable after named conditions close. `REJECT` means the scope or implementation must return through the pipeline.
5. **Record the decision.** Capture who decided, when, which artifact and scope were evaluated, the evidence used, remaining risk, release conditions, and rollback or recovery trigger.
6. **Release and verify.** Release only the approved artifact. Perform the documented post-release checks immediately and record their result.
7. **Recover when necessary.** If a release condition, trust invariant, data-integrity check, or critical customer path fails, stop expansion and execute the documented rollback or recovery plan.

Evidence beats opinion at every step. No deadline, demonstration, or stakeholder preference can substitute for a missing gate.

## Product Thinking

Always remember:

Users do not buy OCR.

Users do not buy dashboards.

Users buy understanding.

Every line of code should help Barni explain a business more clearly. Infrastructure is valuable when it makes that explanation more truthful, timely, or useful. Features are valuable when they reduce effort or improve a decision.

Before approving a technical solution, ask:

> Does this help a business owner understand or act?

If the answer is no, Barni should remain quiet and the team should reconsider the work.

## Expanded Definition of Done

A task is complete only when:

- Architecture is consistent.
- Business rules are correct.
- Evidence exists.
- Confidence is correctly typed.
- Failure is safe.
- Tests pass.
- Migration and compatibility are verified when applicable.
- Documentation is updated.
- User experience improved.
- Future developers can understand the solution.

A feature is Done only when the operating pipeline also records:

- [ ] Tests pass.
- [ ] QA Lead approves.
- [ ] Customer Success approves.
- [ ] Product Critic approves.
- [ ] Restaurant Owner confirms business value.
- [ ] Ship Check recommends release.
- [ ] Release Manager approves.

Passing tests alone is not completion. Visible UI alone is not completion. Documentation alone is not completion. Done means the full behavior is coherent, trustworthy, explainable, and maintainable.

## Final Principle

Build Barni so that every new feature makes the product feel smarter,

not bigger.
