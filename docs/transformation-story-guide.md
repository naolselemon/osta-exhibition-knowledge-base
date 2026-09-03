# Transformation story guide

## Purpose

A transformation story explains a sourced before-versus-after change around one digital system. It is not a place to restate KPI values. Quantitative evidence belongs once in immutable KPI observations and is connected through `kpi_observation_refs`.

Use `templates/transformation-story.template.yml` and validate against `schemas/transformation-story.schema.json`.

## Supported dimensions

| Dimension code | Before | After |
| --- | --- | --- |
| `paper-application-to-online-application` | Applicant submits a paper form. | Applicant submits through a digital channel. |
| `physical-queue-to-digital-queue` | User waits in a physical queue. | User receives a digital place, appointment, or service sequence. |
| `manual-verification-to-automated-validation` | Staff manually inspect or cross-check inputs. | Defined rules or trusted integrations validate inputs automatically. |
| `paper-file-to-digital-record` | Service depends on a physical file. | Managed digital record supports storage and retrieval. |
| `multiple-office-visits-to-remote-access` | User must return to one or more offices. | User can complete or track eligible steps remotely. |
| `manual-reporting-to-real-time-dashboard` | Reports are manually compiled after the fact. | Dashboard updates from operational data under a defined refresh rule. |
| `long-processing-time-to-faster-processing` | Baseline process has documented elapsed time. | Comparable digital process has documented lower elapsed time. |
| `difficult-tracking-to-end-to-end-tracking` | Users or staff cannot reliably follow case status. | Defined stages and status events provide end-to-end tracking. |

These labels describe comparison dimensions, not claims that every system achieved the after state. A story may use several dimensions only when its sources support each one.

## Authoring steps

1. Assign a stable story `id` and reference one existing `system_id`.
2. Write a title and summary limited to source-supported change.
3. Select the applicable transformation dimensions.
4. Describe the before and after states independently. Include service steps only when supported.
5. Identify beneficiary groups and state observed user impact. Do not convert an intended benefit into an achieved result.
6. Reference each quantitative result through `kpi_observation_refs`; do not type the value into the narrative.
7. Cite source locators that support both states. If evidence supports only the after state, keep the story draft and record the limitation.
8. Keep `verification_status: needs-review` and `public_display_approved: false` until a reviewer verifies the comparison, sources, and public suitability.

## Evidence standard

A publishable story needs evidence for:

- the former process or condition;
- the implemented digital process or condition;
- the affected users or service scope;
- every claimed impact;
- every quantitative result, through a verified KPI observation;
- the reporting period relevant to each quantitative result.

Screenshots can establish that a screen existed, but not adoption, performance, coverage, or impact. A planned workflow does not establish operational use. Words such as “faster,” “real-time,” “automated,” and “end-to-end” require a definition or evidence appropriate to the claim.

## Before and after fields

Both `before` and `after` contain:

- `label`: concise state name;
- `description`: evidence-backed state description;
- `service_steps`: ordered actions when known;
- `evidence_notes`: what the source establishes and what remains uncertain.

`user_impact` contains beneficiary groups and a factual impact description. If the source establishes only intended impact, say so explicitly and leave the story unpublished.

## KPI links

Choose KPIs that test the stated transformation. Examples:

- online application: `services-digitized`, `digital-transactions`, `office-visits-reduced`;
- automated validation: `workflows-automated`, `processing-time-reduction`, quality KPIs;
- digital record: `records-digitized`, `files-scanned`, `files-uploaded`, `metadata-completion-percent`, `paper-records-reduced`;
- remote access: `active-users`, `service-coverage-percent`, `locations-covered`, `office-visits-reduced`;
- dashboards: `dashboards-available`, `reports-generated`, response or freshness measures;
- faster processing: `processing-time-reduction` with a documented baseline and statistic;
- end-to-end tracking: service-specific completion, quality, or user-impact observations.

The build validates that every KPI reference exists and belongs to the same system. Referenced draft observations keep the story draft; they are not exposed through avatar or public KPI outputs.

## Translation and publication

Do not infer or machine-author Amharic content. Amharic text needs an approved source or approval by a human Amharic reviewer. Afaan Oromo and Amharic translations appear in avatar facts only after explicit approval metadata passes validation.

Before publication, remove security-sensitive implementation details, internal network information, personal information, and unapproved source material. Public stories and their referenced observations must use public classification and explicit display approval.
