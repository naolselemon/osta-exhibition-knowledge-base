# KPI authoring guide

## Record model

KPIs are not narrative attributes of a system. The catalog in `content/kpi-definitions/` defines each indicator. Each measured result is an immutable record in `content/kpi-observations/`. A digital system references observation IDs through `headline_kpi_refs`; an FAQ references them through `kpi_observation_refs` and renders a value with `{{kpi:observation-id}}`.

The structured `actual` object is the authoritative value. Do not repeat that number in a system purpose, service description, FAQ answer, or transformation narrative. Leave `display_value` null while authoring; the build derives a canonical display value from `actual` and the KPI definition.

## Authoring a KPI definition

1. Copy `templates/kpi-definition.template.yml` into `content/kpi-definitions/`.
2. Assign a stable lowercase `kpi_code`. A code is an identity, not a display label.
3. Define the counted population, inclusion rule, exclusions, scope, and timing in `description`.
4. Select one supported measurement type and canonical units.
5. Choose the safest catalog aggregation. Use `not-aggregatable` when overlap cannot be ruled out.
6. Set every reporting requirement needed to interpret the value.
7. Keep `status: draft` until the definition and aggregation rule are reviewed.

Changing the meaning of an active KPI requires a new KPI code. A `record_version` change may clarify presentation or metadata, but must not silently redefine the measured population.

## Authoring a KPI observation

1. Copy `templates/kpi-observation.template.yml` into `content/kpi-observations/`.
2. Create an immutable, descriptive `id`. Include enough scope and period information to distinguish later observations.
3. Use an existing `system_id` and `kpi_code`.
4. Set `actual`, `baseline`, and `target` as three separate objects. Use `operator: not-specified` with a null value when a baseline or target is absent.
5. Use only a unit permitted by the KPI definition.
6. Record a reporting period. If a draft source is imprecise, retain its wording in `reporting_date_text`, use `type: unknown`, and do not publish.
7. Define the measurement method, owner, and update frequency. Do not infer these from a display claim.
8. Add source references with exact locators. `verification_status: verified` means a reviewer checked the value, context, scope, unit, and period against that source.
9. Document uncertainty in `data_quality.limitations`; never improve or reconcile a claim automatically.
10. Keep source-derived candidates at `publication_status: draft`, `verification_status: needs-review`, and `public_display_approved: false`.

After reviewing a new observation, append its immutable hash to the history lock:

```sh
python scripts/kpi_pipeline.py accept-new-observations
```

That command accepts new IDs only. It rejects an edited or removed historical observation. To correct or promote a locked draft, create a new observation ID and set `supersedes_observation_id` to the old ID. Update the system headline reference after the replacement has passed review.

## Publication gate

A published observation must have all of the following:

- a real system and KPI definition;
- a non-null actual value and allowed unit;
- a known reporting period;
- `verification_status: verified`;
- at least one source reference marked `verified`;
- `data_quality.accuracy_status: verified` and no unresolved conflict;
- no `XX`, `TODO`, `TBD`, template token, or placeholder text;
- values within KPI bounds;
- required activity, monitoring, or statistic dimensions;
- for exhibition display, `data_classification: public`, `contains_personal_data: false`, `public_display_approved: true`, and `exhibition.public_display_status: approved`.

A source label appears publicly only when that source reference also has `public_display_approved: true`.

A published digital system must reference at least one verified public headline observation. The only alternative is a time-bounded `kpi_data_unavailable_exception` explicitly approved by a publisher role. An exception is not a KPI and never supplies a dashboard value.

## KPI-specific context

- `active-users`, `mobile-active-users`, and `web-active-users` require `dimensions.activity_window`. State the dates or duration and the activity rule in the measurement-method description.
- `response-time` requires a duration unit and `dimensions.statistic` such as `median` or `p95`. Also define the request measured.
- `availability-percent` requires `dimensions.monitoring_period` and the uptime/exclusion rule.
- Count-unique portfolio metrics require stable, non-personal `dimensions.entity_ids`. The exact observation count must match the number of IDs.
- Sum and weighted-average metrics require non-overlapping `dimensions.aggregation_partition` values and aligned reporting periods. Weighted averages also require a positive `dimensions.aggregation_weight`.

## FAQ values

List every referenced observation in `kpi_observation_refs`. Insert its value in an answer with a token:

```yaml
answer: The verified result is {{kpi:example-observation-id}}.
kpi_observation_refs: [example-observation-id]
```

The public build resolves the token from the structured observation. Literal numeric claims in FAQ text, including translated FAQ text, are rejected. Translations can use `{{kpi:observation-id|number}}` when approved surrounding prose supplies the unit. Full tokens require reviewed `kpi_unit_labels` for the chatbot export. See the [chatbot release guide](chatbot-release-guide.md).

## Translation approval

Generated translation text may be staged for native-speaker review, but it must remain `status: needs-review` with `human_reviewed: false`; it is not approved language content. An Amharic translation enters a release only when it is traceable to an approved source or has `status: approved`, `human_reviewed: true`, and `reviewer_role: human-amharic-reviewer`. Approved Afaan Oromo content follows the equivalent human-review or approved-source rule. Draft and unapproved translations never enter `dist/avatar-facts.json`.

## Commands

```sh
# Validate records, history immutability, references, publication, and disclosure rules.
python scripts/kpi_pipeline.py validate

# Generate all public distribution artifacts after validation.
python scripts/kpi_pipeline.py build

# Run behavioral coverage.
python -m unittest discover -s tests -v
```
