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
FAQs per published system in each language. New beneficiary, capability, and
transformation questions need fact and language review; missing evidence must remain
explicit.

`content/faqs/visitor-question-drafts.yml` contains 102 generated FAQ records across
36 of the 37 currently published systems, assembled from existing purposes,
beneficiary lists, and service descriptions. Each record has Afaan Oromo and
Amharic text reviewed and approved by native-language reviewers. The records have
`publication_status: published`, `workflow.state: approved`, and the exact
language-specific reviewer roles required by the release contract, so they are
eligible for the public and chatbot bundles.

For future generated FAQs, the Afaan Oromo reviewer must set the `om` approval to
`status: approved`, `human_reviewed: true`, and
`reviewer_role: human-afaan-oromo-reviewer`; the Amharic reviewer must do the same
for `am` with `human-amharic-reviewer`. After both language reviews and the
relevant fact/privacy checks, set the FAQ workflow `state` to `approved`. The
release builder then includes the record in `chatbot-knowledge.json` for each
approved locale.

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
survive the existing public filter and supersession rules. A missing or needs-review
language is absent, never filled from machine translation. Facts with no public citation retain
their knowledge-record reference. Reviewers should prioritize citation coverage.

## CI and evidence

Run source validation only on a private runner with the authorized local evidence
mounted under the repository's `source-materials/` hierarchy. Public/untrusted PR
jobs must not receive evidence or publication credentials. The manual workflow
requires a reviewed commit and a protected publisher environment. It verifies
read-only copies of source files, then publishes only the sanitized release artifact.

The local M-Mesob PDF is intentionally absent in this checkout. The validator has
an exact source-ID/path exception for this approved M-MESOB case, and the public
build suppresses source labels for the affected observations; no substitute
evidence is created. Do not broaden the exception, rewrite accepted observation
history, or add a placeholder PDF.
