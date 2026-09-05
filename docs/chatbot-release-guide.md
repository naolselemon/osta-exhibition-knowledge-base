# Chatbot release contract

The chatbot application belongs in the separate `osta-exhibition-chatbot` repository.
This repository owns facts, translation approval, source evidence, and sanitized releases.

## Build and coverage

```sh
python scripts/kpi_pipeline.py validate
python -m unittest discover -s tests -v
python -m scripts.chatbot_release coverage
python -m scripts.chatbot_release build --output releases
```

`coverage` is an authoring diagnostic, not a reviewer build or publication approval.
It identifies FAQ coverage and missing localized unit labels without manufacturing
questions, facts, translations, or approval. The target is three evidence-supported
FAQs per published system in each language. Beneficiary, capability, and transformation
questions need fact and language review; missing evidence must remain explicit.

`content/faqs/visitor-question-drafts.yml` contains 99 English starter questions
across 35 of the 36 currently published systems, assembled from existing purposes,
beneficiary lists, and service descriptions. Empty source fields and numeric prose
were omitted. All starters are internal drafts with empty translation maps and no
display approval. Reviewers must verify them against each system's linked evidence,
correct unsuitable wording, and supply approved translations before publication.

`build` first runs the full repository validator, including local-source existence
and immutable-observation checks. It creates an immutable directory named by the
SHA-256 of its artifact checksum map. It includes the four existing public files,
`chatbot-knowledge.json`, and `manifest.json`. The existing `kpi_pipeline.py build`
command still writes its four artifacts under `dist/`.

The manifest records the schema version, artifact hashes, build timestamp, knowledge
commit, and whether the working tree was dirty. The application refuses dirty or
synthetic releases in production. Commit reviewed changes before generating a
production release. A hash verifies integrity, not reviewer authority: release
artifacts must still travel through the authorized private build/promotion process.

## Localized KPI templates

`{{kpi:observation-id}}` inserts the operator, numeric value, and unit. For the
chatbot, a translated FAQ must supply `kpi_unit_labels` inside the translation,
mapping that observation ID to a reviewed unit label. Percent uses the `%` symbol.
The unit labels are part of the translation's approval; do not label new text approved.

`{{kpi:observation-id|number}}` inserts the operator and value without a unit. Use it
only when the existing approved surrounding prose already names the unit. The
WoredaNet migration replaces exactly the three literal values in each language;
rendered wording and values are unchanged. It does not assert a new language review.

All translated questions/answers reject literal numeric claims, unlisted references,
and malformed tokens. The legacy avatar export now resolves translated tokens;
its existing canonical unit fallback is retained for compatibility. The chatbot
export withholds FAQs whose localized units are missing and exposes that gap through
`coverage`. It never translates a unit at runtime or silently drops an operator.

## Consumer behavior

`schemas/chatbot-knowledge.schema.json` defines the public contract. Each answer
has a stable ID, locale, record/system references, verbatim approved wording, safe
source labels, and the actual measurement, scope, and reporting period for its
referenced KPIs. There are no source paths, raw evidence, or approval metadata.

System-answer `aliases` reuse only the existing public official name and acronym;
they help match visitors' familiar system names while answers remain in the selected
language. This adds no free-form alias fields to the authoring content model.

Only published systems with an approved workflow and correctly approved translations
are exported. FAQ workflows must also be approved; all referenced observations must
survive the existing public filter and supersession rules. A missing language is
absent, never filled from machine translation. Facts with no public citation retain
their knowledge-record reference. Reviewers should prioritize citation coverage.

## CI and evidence

Run source validation only on a private runner with the authorized local evidence
mounted under the repository's `source-materials/` hierarchy. Public/untrusted PR
jobs must not receive evidence or publication credentials. The manual workflow
requires a reviewed commit and a protected publisher environment. It verifies
read-only copies of source files, then publishes only the sanitized release artifact.

As of implementation, the local M-Mesob PDF is missing. Validation and production
build correctly remain blocked. Restore the actual authorized file or have the
content owner resolve the affected records; do not create placeholder evidence,
rewrite accepted observation history, or loosen the validator.
