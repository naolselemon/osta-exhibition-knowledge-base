# Agent Guidance for the OSTA Exhibition Knowledge Base

This file defines repository-specific operating rules for automated coding and content agents. It supplements the [README](README.md) and [contributor guide](contributing.md); it does not override a user's explicit instructions or the repository's schemas and tests.

## Mission and Boundary

Treat this repository as a controlled knowledge source, not as the exhibition application. Its job is to preserve sourced facts, review state, KPI semantics, translations, references, and disclosure-safe generated data.

Do not add chatbot servers, frontend code, 3D assets, speech engines, vector databases, deployment configuration, credentials, or production integrations unless the repository scope is explicitly changed by an authorized request.

## Required Inspection Before Editing

1. Read the relevant section of [`README.md`](README.md), especially the [folder map](README.md#folder-map) and [content relationships](README.md#content-relationships).
2. Read [`contributing.md`](contributing.md).
3. Read the exact schema, template, neighboring record, validator code, and detailed guide for the requested change.
4. Inspect referenced source material and exact locators before changing factual content.
5. If Git metadata exists, inspect status before editing and preserve unrelated user changes. If Git metadata does not exist, do not initialize a repository merely to perform branch or commit steps.
6. Determine every affected reference, test, generated contract, and document before changing an exported identifier or model field.

Do not open unrelated source files speculatively. Use the narrowest evidence needed to establish the current convention.

## Source-Grounding Rules

- Never invent or estimate an organizational fact, KPI value, date, scope, lifecycle state, translation, beneficiary group, service, integration, achievement, or outcome.
- Treat user-reported repository facts and supplied source evidence as authoritative inputs, while preserving any uncertainty they state.
- A source file's presence proves only that a file is stored. It does not prove that a claim was extracted, reviewed, verified, approved, or published.
- Preserve exact operators, units, dates, reporting periods, calendars, measurement scopes, methods, and limitations.
- Use a locator precise enough for an independent reviewer: deck and slide; document page and heading; spreadsheet sheet and cells/rows; email subject, sender, and date; or URL, page title, and access date.
- When evidence is missing or ambiguous, keep the record draft and use the supported unknown/null representation plus a limitation. Never fill a placeholder with a plausible value.
- Preserve conflicting evidence. Do not average claims, select the largest value, or silently prefer one source.

## Canonical Content Model

Use current repository locations only:

- systems: [`content/digital-systems/`](content/digital-systems/);
- KPI definitions: [`content/kpi-definitions/`](content/kpi-definitions/);
- KPI observations and immutable history: [`content/kpi-observations/`](content/kpi-observations/);
- dashboard derivation: [`content/portfolio-kpis/`](content/portfolio-kpis/);
- transformation stories: [`content/transformation-stories/`](content/transformation-stories/);
- FAQs: [`content/faqs/`](content/faqs/);
- authorized local evidence: [`source-materials/`](source-materials/); presentation binaries in `source-materials/presentations/` are Git-ignored and must be obtained outside GitHub;
- contracts and tooling: [`schemas/`](schemas/), [`scripts/`](scripts/), and [`tests/`](tests/);
- generated public artifacts: [`dist/`](dist/).

Do not create organization, service, training-program, achievement, glossary, standalone source-claim, conflict, workbench, reusable `src/`, or `.github/` structures unless the requested change explicitly introduces the complete model. A complete model includes schema, template, validation, relationships, migration, tests, and documentation.

## KPI Invariants

- A KPI definition describes meaning and legal representation; it does not store a result.
- A KPI observation stores one system/scope/period result and its evidence.
- `actual`, `baseline`, `target`, and `achievement` are independent concepts. Never derive one merely to fill another.
- A new reporting period receives a new observation ID.
- An accepted observation is immutable. A correction creates a new observation and uses explicit supersession when the system and KPI match.
- Changing values appear once in an observation. Other records reference its ID instead of copying the number into prose.
- `count-unique` requires stable non-personal entity IDs; `sum` requires aligned non-overlapping partitions; `weighted-average` requires aligned partitions and positive weights; `not-aggregatable` remains a series.
- A ratio is a measurement type, not a currently supported aggregation method. Do not synthesize a portfolio ratio without a reviewed numerator/denominator model.
- Never conflate registered and active users, beneficiaries and accounts, scanned and uploaded files, records and transactions, implementation progress and availability, or applications and services.

Use the [KPI authoring guide](docs/kpi-authoring-guide.md), [data dictionary](docs/kpi-data-dictionary.md), and [aggregation rules](docs/kpi-aggregation-rules.md) as the detailed contracts.

## Translation and Avatar Rules

- Current record keys are `om` for Afaan Oromo and `am` for Amharic; consumers map them to `om-ET` and `am-ET`.
- Never mark machine-generated text approved.
- Preserve the original fact, number, operator, unit, period, and uncertainty in every translation.
- Approval requires approved-source or appropriate human-review evidence under the current validator.
- Keep unapproved translations out of public and avatar outputs.
- Do not add planned `short_text`, `spoken_text`, `detailed_text`, alias, pronunciation, pace, emphasis, or gesture fields before schemas and tooling support them.
- Avatar animation, lip-sync, speech synthesis, and retrieval implementation belong outside this repository.

## Security and Disclosure Rules

Never write secrets or sensitive operational data into content, fixtures, logs, documentation, generated artifacts, or examples. This includes passwords, tokens, API keys, private keys, production database URLs, internal IP addresses, private endpoints, personal records, citizen identifiers, employee records, individual prison records, confidential screenshots/source code, and vulnerability details.

Do not expose source paths or source binaries through public artifacts. Do not approve media without documented display/reuse rights. Public output is limited to records that satisfy publication, verification, classification, privacy, conflict, and display-approval rules.

No open-source licence is currently declared. Do not copy or redistribute repository material outside the authorized OSTA workflow.

## Editing Discipline

- Make the smallest coherent change that satisfies the request.
- Reuse existing schemas, templates, vocabulary, and file organization. Do not introduce a second convention.
- Do not rename stable IDs or referenced source files for cosmetic reasons.
- Never force-add, commit, or push a presentation binary excluded by [`.gitignore`](.gitignore); keep the authorized copy local.
- Do not edit files under [`dist/`](dist/) manually; rebuild them from source records.
- Do not relax validation to accommodate an invalid record.
- For model changes, migrate every affected caller and remove obsolete fields, aliases, comments, and paths.
- Preserve record ordering and formatting conventions unless the requested change requires a deliberate migration.
- Do not make unrelated cleanup, formatting, telemetry, retries, abstractions, or fallback behavior.
- Do not add facts to tests merely to make a validator path pass. Tests may use synthetic data only when clearly isolated from production content.

## Required Commands

The repository requires Python 3.11 or newer and PyYAML 6.x. It has no Makefile, dedicated lint command, reviewer-build command, or `osta-kb` executable.

Validate content and contracts:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/kpi_pipeline.py validate
```

Run behavioral tests:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Build public artifacts when the task affects public source data or build behavior:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/kpi_pipeline.py build
```

Accept new observation hashes only after the new observations have been reviewed:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/kpi_pipeline.py accept-new-observations
```

A successful command is evidence only for the behavior it exercises. Report the exact command and result. Do not claim lint, CI, reviewer-build, Git, or visual verification that did not run.

## Completion Checklist

Before reporting completion, verify:

- [ ] the requested behavior or documentation is complete end to end;
- [ ] every changed fact is source-supported and accurately scoped;
- [ ] every relative link and record reference resolves;
- [ ] draft, review, verification, privacy, conflict, and publication states remain honest;
- [ ] no unauthorized translation, media, secret, personal data, or internal detail was introduced;
- [ ] all affected schemas, templates, callers, tests, docs, and generated contracts were updated or intentionally unchanged;
- [ ] repository validation passes;
- [ ] the relevant behavioral tests pass;
- [ ] public artifacts were rebuilt only when required and were inspected for disclosure;
- [ ] Git branch, diff, commit, and push claims match the actual repository state;
- [ ] the final report states any unavailable prerequisite without inventing a substitute result.
