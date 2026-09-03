# Contributing to the OSTA Exhibition Knowledge Base

This repository is a controlled, source-grounded knowledge base for the future OSTA exhibition assistant. Contributions must preserve factual accuracy, traceability, review status, language quality, privacy, and safe public-display rules.

Start with the [README](README.md). Its [folder map](README.md#folder-map), [content relationships](README.md#content-relationships), and [common workflows](README.md#contribution-workflows) explain the repository model in detail.

## Contribution Principles

1. **Use authorized evidence.** Every organizational claim and KPI result must resolve to exact source evidence.
2. **Never invent a fact or value.** If evidence is missing, keep the record draft and use the schema's unknown/null representation plus a limitation or clearly scoped draft note.
3. **Separate lifecycle states.** A stored source is not automatically extracted, reviewed, verified, approved, or published.
4. **Store changing numbers once.** KPI values belong in KPI observations; systems, stories, FAQs, dashboards, and avatar facts reference observation IDs.
5. **Preserve history.** A new reporting period gets a new observation. A correction supersedes an earlier observation without rewriting its accepted history.
6. **Keep review roles independent.** Fact, KPI, language, media-rights, privacy, and publication approval are distinct decisions.
7. **Publish conservatively.** Draft, conflicting, unsupported, unverified, private, personal, ambiguous, or display-unapproved material must not enter public output.
8. **Do not weaken contracts for one record.** Correct invalid content instead of relaxing a schema or validator around it.

## Choose the Correct Location

| Contribution | Current location | Starting point |
| --- | --- | --- |
| Digital-system identity and metadata | [`content/digital-systems/`](content/digital-systems/) | [`templates/digital-system.template.yml`](templates/digital-system.template.yml) |
| KPI meaning and aggregation contract | [`content/kpi-definitions/`](content/kpi-definitions/) | [`templates/kpi-definition.template.yml`](templates/kpi-definition.template.yml) |
| KPI result for one system/scope/period | [`content/kpi-observations/`](content/kpi-observations/) | [`templates/kpi-observation.template.yml`](templates/kpi-observation.template.yml) |
| Portfolio-dashboard derivation | [`content/portfolio-kpis/`](content/portfolio-kpis/) | [`templates/portfolio-kpi.template.yml`](templates/portfolio-kpi.template.yml) |
| Before-and-after transformation narrative | [`content/transformation-stories/`](content/transformation-stories/) | [`templates/transformation-story.template.yml`](templates/transformation-story.template.yml) |
| FAQ answer and KPI references | [`content/faqs/`](content/faqs/) | [`templates/faq.template.yml`](templates/faq.template.yml) |
| Authorized local source binary | [`source-materials/`](source-materials/) | [Source-evidence guidance](README.md#source-evidence) |
| Schema or validation behavior | [`schemas/`](schemas/), [`scripts/`](scripts/), and [`tests/`](tests/) | Existing adjacent schema, implementation, and tests |

Organization, service, training-program, achievement, glossary, standalone source-claim, conflict, workbench, reusable `src/`, and `.github/` models are not currently implemented. Do not create an ad hoc structure for them. A contribution that introduces one of those models must include its schema, template, validation, relationships, migration reasoning, tests, and README updates in the same reviewed change.

## Standard Contribution Workflow

1. Read the relevant [folder guide](README.md#folder-responsibilities), schema, template, and detailed guide before editing.
2. Obtain the authorized source through an approved channel and place it locally under [`source-materials/`](source-materials/). PowerPoint files under `source-materials/presentations/` are Git-ignored and must never be staged or pushed.
3. Create or update the normalized record. Preserve exact names, operators, units, dates, periods, scope, and uncertainty from the source.
4. Add an exact inline `source_refs` entry. Keep verification and display approval false or pending until the responsible reviewers complete their work.
5. Keep new facts and translations draft. Repository presence is not publication approval.
6. Run validation and the behavioral test suite.
7. Request the applicable fact, KPI, language, media-rights, privacy, and publication reviews.
8. Run the production build only after validation and tests pass. Inspect generated output for unintended disclosure.
9. In a Git-enabled checkout, inspect the diff, stage only intentional files, and submit one focused change.

## Source References

A locator must let another reviewer find the same evidence without guessing.

| Source type | Required locator quality |
| --- | --- |
| PowerPoint | Exact deck filename and slide number; add the chart, shape, or visual region when needed. |
| Document or PDF | Exact filename, page number, and section or heading. |
| Spreadsheet | Exact filename, worksheet, and cell, range, or row. |
| Email | Exact subject/title, sender, and date; store the message only when authorized. |
| Webpage or API documentation | Full URL, page title, and access date. |

Do not mark a source reference verified merely because the file exists. Compare the normalized claim with the exact cited evidence, including surrounding context and limitations.

Presentation binaries are intentionally excluded from GitHub. Do not bypass [`.gitignore`](.gitignore) with `git add -f`. A fresh clone must obtain the authorized local files separately before source-existence validation can pass.

## KPI Contributions

Before adding a result, find the existing KPI definition in [`content/kpi-definitions/kpi-catalog.yml`](content/kpi-definitions/kpi-catalog.yml). Add a reviewed definition first if no existing definition describes the exact measured concept.

Each observation must keep these fields conceptually separate:

- `actual`: the reported or measured result;
- `baseline`: the starting or comparison value;
- `target`: the intended result;
- `achievement`: an assessment against a valid target, not a replacement for the actual value.

Preserve source operators such as exact, greater-than, approximate, range, or not-specified. Never convert a bound or approximation into an exact value. Reporting period, unit, system, measurement scope, method, dimensions, source, quality, review, classification, and display state travel with the observation.

Do not conflate registered users with active users, beneficiaries with accounts, scanned files with uploaded files, records with transactions, implementation progress with availability, or applications with digital services. Follow the [KPI authoring guide](docs/kpi-authoring-guide.md), [data dictionary](docs/kpi-data-dictionary.md), and [aggregation rules](docs/kpi-aggregation-rules.md).

New observation IDs are appended to [`observation-history.json`](content/kpi-observations/observation-history.json) only after review:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/kpi_pipeline.py accept-new-observations
```

Never use this command to conceal an unauthorized modification to an accepted observation.

## Translation and Visitor-Facing Content

Current translation maps use `om` for Afaan Oromo and `am` for Amharic. Downstream consumers map them to `om-ET` and `am-ET`.

- Do not publish machine-generated Afaan Oromo or Amharic as approved content.
- Afaan Oromo requires approved-source or appropriate human-review evidence.
- Amharic requires approved-source evidence or approval by the human Amharic reviewer recognized by current validation.
- Review meaning, approved terminology, spelling, natural spoken delivery, and every number.
- Keep unapproved translations absent from public/avatar output.
- `short_text`, `spoken_text`, `detailed_text`, aliases, pronunciation hints, and gesture cues are planned fields, not current schema fields.

## Security, Privacy, and Media

Never add or expose:

- passwords, API keys, tokens, private keys, or production database URLs;
- internal IP addresses, private endpoints, or confidential infrastructure details;
- citizen IDs, phone numbers, employee records, individual prison records, or other personal data;
- confidential screenshots, source code, vulnerability details, or unauthorized source binaries;
- photographs, video, logos, or other media without documented display and reuse rights.

Public content must be public-classified, non-personal, verified, reviewed, and explicitly approved for display. Source files may contain information that must never appear in generated output.

No open-source licence is currently declared. Do not copy, redistribute, or reuse repository content outside the authorized OSTA workflow without organizational approval.

## Validation and Build Commands

Requirements are Python 3.11 or newer and PyYAML 6.x, as declared in [`pyproject.toml`](pyproject.toml). The repository has no Makefile, dedicated lint command, or `osta-kb` executable.

Run validation after every content or tooling change:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/kpi_pipeline.py validate
```

Run the behavioral suite before submitting a change:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Build disclosure-safe production output after validation and tests pass:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/kpi_pipeline.py build
```

The builder writes the four files under [`dist/`](dist/). Never edit generated JSON directly. There is no reviewer-build command; reviewers inspect source YAML and validation/test output.

## Schema and Tooling Changes

A permanent model change must update every affected surface together:

- schema definitions and enums;
- templates;
- current records or an explicit migration;
- Python validation/build behavior;
- all affected references and generated contracts;
- behavioral tests for new observable rules;
- README and detailed guides.

Prefer backward-compatible additions when they preserve a coherent model. If a clean cutover is required, migrate every caller and remove the obsolete path rather than leaving aliases or two competing conventions.

## Git and Review Checklist

The current directory may be distributed without Git metadata. Do not initialize a repository, configure a remote, create a branch, commit, or push unless the task and environment authorize it.

When working in an existing Git checkout:

1. inspect status before editing and preserve unrelated user changes;
2. create a focused branch such as `content/...`, `kpi/...`, `translation/...`, `fix/...`, `docs/...`, or `tooling/...`;
3. stage only the files required for the contribution;
4. run `git diff --check` and review the complete diff;
5. use a concise commit prefix such as `content:`, `kpi:`, `translation:`, `fix:`, `docs:`, `test:`, or `chore:`;
6. do not push directly to a protected/default branch or force-push without explicit authorization.

Before requesting review, confirm:

- [ ] every factual claim has precise source evidence;
- [ ] missing information remains explicitly draft rather than invented;
- [ ] IDs and accepted observation history remain stable;
- [ ] references resolve to existing records;
- [ ] KPI scope, period, operator, unit, and aggregation are valid;
- [ ] translation, privacy, media-rights, and display states reflect completed reviews only;
- [ ] no secret, personal data, or internal infrastructure detail was added;
- [ ] validation and tests pass;
- [ ] generated output was not edited manually;
- [ ] the change contains no unrelated formatting or content edits.
