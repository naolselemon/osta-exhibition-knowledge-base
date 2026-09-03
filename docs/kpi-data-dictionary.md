# KPI data dictionary

All source records use schema version `1.0.0`. JSON Schemas in `schemas/` are normative for structure; the build pipeline adds cross-record, semantic, immutability, aggregation, and disclosure checks.

## Digital system

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | slug string | Stable system identity used by every reference. |
| `slug` | slug string | Public URL or UI slug. |
| `official_name` | string | Source-supported official name. |
| `acronym` | string or null | Approved acronym. |
| `category` | string | Portfolio or service-domain category. |
| `subcategories` | unique string array | More specific domains or capabilities. |
| `lifecycle_status` | enum | `planned`, `in-development`, `pilot`, `operational`, `suspended`, `retired`, or `unknown`. |
| `publication_status` | enum | `draft`, `in-review`, `published`, or `archived`. |
| `organization` | object | Owning/operating organization name, type, and ownership role. |
| `system_classification` | object | Primary system type, delivery channels, and deployment scope. |
| `purpose` | string | Non-numeric, source-supported purpose statement. |
| `beneficiaries` | string array | Beneficiary groups, never person-level records. |
| `services_digitized` | object array | Stable service IDs, names, and descriptions. |
| `integrations` | object array | Integration IDs, types, status, and display approval. |
| `geographic_coverage` | object | Coverage levels, named public areas, and notes. |
| `headline_kpi_refs` | observation-ID array | Authoritative headline KPI references. |
| `transformation_story_refs` | story-ID array | Related before-versus-after stories. |
| `faq_refs` | FAQ-ID array | Related FAQs. |
| `media` | object array | Media metadata and public-display approval. |
| `translations` | language map | Reviewed `om` and `am` content with approval evidence. |
| `workflow` | object | Record version, review status, dates, and approval role. |
| `source_refs` | source-reference array | Source evidence for the system description. |
| `kpi_data_unavailable_exception` | object or null | Publisher-approved, dated exception for a published system without a verified KPI. |

## KPI definition

| Field | Type | Meaning |
| --- | --- | --- |
| `kpi_code` | slug string | Stable indicator identity. |
| `name` | string | Full human-readable name. |
| `description` | string | Measured population, event, or condition. |
| `kpi_category` | enum | Catalog grouping listed below. |
| `applicable_system_types` | string array | System types for which the metric is meaningful. |
| `measurement_type` | enum | Temporal or semantic measurement behavior. |
| `value_type` | enum | `integer`, `number`, `string`, `boolean`, or `range`. |
| `allowed_operators` | enum array | Operators accepted in measurement objects. |
| `allowed_units` | string array | Canonical units accepted for this KPI. |
| `direction_of_improvement` | enum | `increase`, `decrease`, `maintain`, or `contextual`. |
| `aggregation` | object | Method, deduplication key, selection rule, and safety notes. |
| `reporting_requirements` | object | Required period, activity window, monitoring window, statistic, source review, and allowed period types. |
| `display` | object | Labels, format, precision, unit label, and chart choices. |
| `status` | enum | `draft`, `active`, `deprecated`, or `retired`. |

Supported KPI categories are `digitization-output`, `service-delivery`, `adoption`, `usage`, `coverage`, `integration`, `performance`, `efficiency`, `quality`, `implementation`, `impact`, `financial-impact`, and `ai-and-automation`.

Supported measurement types are `cumulative`, `periodic`, `point-in-time`, `percentage`, `duration`, `currency`, `ratio`, `boolean`, and `qualitative`.

Supported aggregation methods are `sum`, `count-unique`, `latest`, `average`, `weighted-average`, `minimum`, `maximum`, and `not-aggregatable`.

## Initial KPI catalog

| KPI code | Category | Measurement | Aggregation | Required context |
| --- | --- | --- | --- | --- |
| `applications-developed` | digitization-output | cumulative | count-unique | Application IDs |
| `services-digitized` | digitization-output | cumulative | count-unique | Service IDs |
| `systems-integrated` | integration | cumulative | count-unique | Integrated-system IDs |
| `services-offered` | service-delivery | point-in-time | count-unique | Service IDs and as-of date |
| `institutions-served` | coverage | cumulative | count-unique | Institution IDs |
| `registered-users` | adoption | cumulative | not-aggregatable | Registration rule and as-of date |
| `active-users` | usage | periodic | not-aggregatable | Activity rule and window |
| `mobile-downloads` | adoption | cumulative | sum | Store partition and aligned period |
| `mobile-active-users` | usage | periodic | not-aggregatable | Mobile activity rule and window |
| `web-active-users` | usage | periodic | not-aggregatable | Web activity rule and window |
| `beneficiaries-served` | impact | cumulative | not-aggregatable | Beneficiary definition and scope |
| `workflows-automated` | efficiency | cumulative | count-unique | Workflow IDs |
| `digital-transactions` | usage | periodic | sum | Non-overlapping partition and period |
| `reports-generated` | digitization-output | periodic | sum | Non-overlapping partition and period |
| `dashboards-available` | digitization-output | point-in-time | count-unique | Dashboard IDs and as-of date |
| `ai-solutions` | ai-and-automation | cumulative | count-unique | Solution IDs |
| `records-registered` | digitization-output | cumulative | not-aggregatable | Record rule and system scope |
| `records-digitized` | digitization-output | cumulative | not-aggregatable | Digitization and uniqueness rule |
| `files-scanned` | digitization-output | cumulative | not-aggregatable | File and rescan rule |
| `files-uploaded` | digitization-output | cumulative | not-aggregatable | File/version rule |
| `metadata-completion-percent` | quality | percentage | weighted-average | Required fields, denominator, and weight |
| `service-coverage-percent` | coverage | percentage | weighted-average | Eligible denominator and weight |
| `locations-covered` | coverage | cumulative | count-unique | Canonical location IDs |
| `implementation-progress-percent` | implementation | percentage | not-aggregatable | Plan scope and denominator |
| `availability-percent` | performance | percentage | weighted-average | Monitoring period, rule, and duration weight |
| `response-time` | performance | duration | weighted-average | Request definition, duration unit, statistic, and weight |
| `processing-time-reduction` | efficiency | percentage | not-aggregatable | Baseline and matching process statistic |
| `office-visits-reduced` | efficiency | periodic | not-aggregatable | Baseline and service scope |
| `paper-records-reduced` | efficiency | cumulative | not-aggregatable | Baseline and record rule |
| `cost-savings` | financial-impact | currency | sum | Currency, cost category, partition, and aligned period |

The software-development terms “system uptime” and “system response time” map to `availability-percent` and `response-time`. Mobile and web application dashboard counts use `applications-developed` with the `dimensions.platform` filter.

## KPI observation

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | slug string | Immutable observation identity. |
| `system_id` | system ID | System measured. |
| `kpi_code` | KPI code | Catalog definition applied. |
| `measurement_scope` | object | Scope type, stable scope ID, and description. |
| `achievement_type` | enum | Actual, reported progress, target achievement, milestone, or qualitative result. |
| `actual` | measurement object | Authoritative observed value. |
| `baseline` | measurement object | Separate comparison value or explicit not-specified object. |
| `target` | measurement object | Separate target value or explicit not-specified object. |
| `achievement` | object or null | Target-assessment metadata; it does not replace actual, baseline, or target. |
| `reporting_period` | object | Period type, dates/text, and calendar. |
| `dimensions` | object | Disaggregation and required context. |
| `measurement_method` | object | Method, description, data owner, and update frequency. |
| `display_value` | string or null | Canonical rendering only; normally generated from `actual`. |
| `source_refs` | source-reference array | Evidence with locator and review status. |
| `data_quality` | object | Completeness, accuracy, duplicate risk, and limitations. |
| `exhibition` | object | Headline, priority, display approval, chart, date, and source-label controls. |
| `workflow` | object | State, author/reviewer roles, dates, and notes. |
| `publication_status` | enum | Draft/review/published/archive state. |
| `verification_status` | enum | `needs-review`, `verified`, or `conflicting`. |
| `data_classification` | enum | `public`, `internal`, `confidential`, or `restricted`. |
| `contains_personal_data` | boolean | Mandatory disclosure guard. |
| `public_display_approved` | boolean | Explicit approval for public output. |
| `supersedes_observation_id` | observation ID or null | Explicit replacement of an immutable historical record. |

### Measurement object

`actual`, `baseline`, and `target` each contain `operator`, `value`, and `unit`. Operators are `equal`, `greater-than`, `greater-than-or-equal`, `less-than`, `less-than-or-equal`, `approximate`, `range`, and `not-specified`. A range value has numeric `minimum` and `maximum`. `not-specified` requires a null value.

### Reporting period

`type` is one of `as-of-date`, `day`, `week`, `month`, `quarter`, `year`, `date-range`, `lifetime`, or `unknown`. `start_date` and `end_date` are Gregorian ISO dates when known. `reporting_date_text` preserves source wording when exact conversion is unavailable. `calendar_type` is `gregorian`, `ethiopian`, `mixed`, or `unknown`.

### Data quality

`completeness`, `accuracy_status`, and `duplicate_risk` use `complete`, `partial`, `unknown`, `needs-review`, `verified`, or `conflicting`. `limitations` is a list of factual qualification statements. A published observation cannot be conflicting.

### Common dimensions

| Dimension | Use |
| --- | --- |
| `platform` | Mobile, web, desktop, API, all, or unknown channel. |
| `statistic` | Mean, median, percentile, minimum, or maximum for performance values. |
| `activity_window` | Dates or duration over which a user must be active. |
| `monitoring_period` | Dates or duration observed for availability. |
| `entity_ids` | Stable non-personal IDs used only for count-unique aggregation. |
| `aggregation_partition` | Non-overlapping source partition for safe summation/averaging. |
| `aggregation_weight` | Positive denominator or monitored quantity for weighted averages. |

## Source reference

A source reference contains `source_id`, public-facing `label`, repository-relative `path`, precise `locator`, `verification_status`, and `public_display_approved`. Verification applies to the cited claim, not merely the existence of the file.

## Portfolio KPI

A portfolio record selects one `kpi_code`, optional system/dimension filters, a catalog-matching `aggregation_method`, deduplication behavior, observation selection, display configuration, and status. It contains no manually authored result. `dist/portfolio-dashboard.json` is computed exclusively from eligible observations.

## Transformation story

A story contains a stable ID, system reference, supported transformation dimensions, explicit before and after states, user impact, KPI observation references, source references, translation metadata, publication controls, and workflow metadata. Numeric evidence remains in the referenced observations.
