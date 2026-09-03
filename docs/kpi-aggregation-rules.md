# KPI aggregation rules

## Governing principle

The KPI definition controls aggregation. A portfolio configuration must use the same method as the catalog; it cannot make a non-additive KPI additive. The build uses only current, published, verified, public-display-approved observations belonging to published systems. Draft, conflicting, superseded, personal, internal, confidential, restricted, or unapproved records are excluded before any calculation.

No dashboard value is inferred when safe aggregation inputs are missing. The metric remains a source-supported series or is absent; the build never inserts a placeholder number.

## Selection before aggregation

1. Filter by the portfolio KPI code, system classification/category, and declared dimensions.
2. Exclude observations that fail any publication or disclosure gate.
3. Remove an older observation only when a current eligible observation explicitly names it in `supersedes_observation_id`.
4. Treat two eligible observations with the same system, KPI, scope, reporting period, and dimensions as an unresolved conflict unless explicit supersession relates them. Validation fails rather than selecting one.
5. For an aggregate requiring a common period, compare the complete structured `reporting_period`; textually or temporally different periods are not aligned.
6. Require identical canonical units. Currency values are never converted automatically.

## Methods

| Method | Calculation | Mandatory safeguards |
| --- | --- | --- |
| `sum` | Add exact values. | Same unit and reporting period; every observation has a unique non-empty `dimensions.aggregation_partition`. Approximate, bounded, or range values remain series-only. |
| `count-unique` | Size of the union of `dimensions.entity_ids`. | Every input supplies stable non-personal IDs; an equal observation count matches its own list length. Missing IDs cause series-only output. |
| `latest` | Present latest observations as a series. | No cross-system total is produced. An explicit reporting date is required for published values. |
| `average` | Arithmetic mean of exact values. | Same unit/period and unique non-overlapping partitions. Use only when the catalog defines an unweighted population. |
| `weighted-average` | Sum of value × weight divided by sum of weights. | Same unit/period, unique partitions, and a positive `dimensions.aggregation_weight` for every input. |
| `minimum` | Lowest exact comparable value. | Same unit/period and unique partitions. |
| `maximum` | Highest exact comparable value. | Same unit/period and unique partitions. |
| `not-aggregatable` | No portfolio total. | Show a labeled system-level series only. |

## Prohibited calculations

- Never sum a percentage. Coverage, metadata completion, availability, and other percentages use a weighted average only when their denominator weights and periods align; otherwise they remain separate.
- Never automatically add `active-users`, `mobile-active-users`, or `web-active-users` across systems. Identity sets and activity windows can overlap.
- Never add registered-user or beneficiary counts across systems without a separately approved privacy-safe unique-person method. The initial catalog marks these non-aggregatable.
- Never add registered, digitized, scanned, uploaded, and paper-reduction values together. They describe different processing states and may refer to the same source record.
- Never count one service, institution, system integration, workflow, location, application, dashboard, or AI solution more than once. These KPIs require canonical entity IDs and set union.
- Never add transaction, download, report, or financial values when partitions overlap, periods differ, units differ, or an operator is non-exact.
- Never reconcile conflicting claims by averaging, choosing the largest, choosing the newest, or preferring one source. A reviewer must create an explicit superseding observation or retain the conflict outside public output.

## Dashboard-specific mappings

| Dashboard measure | KPI and rule |
| --- | --- |
| Applications developed | `applications-developed`; unique application IDs. |
| Digital services | `services-digitized`; unique service IDs. |
| Institutions served | `institutions-served`; unique institution IDs. |
| Active users | `active-users`; system-level series only. |
| Mobile applications | `applications-developed` filtered by `dimensions.platform: mobile`; unique application IDs. |
| Web applications | `applications-developed` filtered by `dimensions.platform: web`; unique application IDs. |
| Systems integrated | `systems-integrated`; unique integrated-system IDs. |
| Automated workflows | `workflows-automated`; unique workflow IDs. |
| Digital transactions | `digital-transactions`; exact values from aligned, non-overlapping partitions. |
| AI solutions | `ai-solutions`; unique solution IDs. |
| System availability | `availability-percent`; monitored-duration weighted average for aligned monitoring periods. |

## Output interpretation

An aggregated metric has `aggregation_status: aggregated`, a structured `value` and `unit`, and the observation IDs that produced it. When inputs are verified but unsafe to combine, the metric retains its `series` and an explicit `series-only-*` status. This is not missing-value substitution; it is a refusal to assert an unsupported portfolio total.

`source_observation_ids` in `dist/portfolio-dashboard.json` is the complete provenance set used by the dashboard build. Every displayed result can therefore be traced back to immutable observations and their verified sources.
