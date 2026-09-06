# Chatbot implementation handoff — 6 September 2026

The application lives in the separate sibling [osta-exhibition-chatbot repository](../../osta-exhibition-chatbot/README.md).
It has a FastAPI backend, a React touch interface, reviewed-answer retrieval,
offline topic browsing, bounded session memory, feedback, release checks, tests,
Docker packaging, and staging/production deployment configuration.

## Knowledge changes

- Translated FAQs support authoritative KPI references, including number-only
  insertion when approved prose already states the unit. The WoredaNet migration
  preserves the rendered numbers and wording.
- The versioned chatbot export preserves source labels, KPI operators and periods,
  language approval, record references, and checksum/commit provenance. Its public
  official-name/acronym aliases do not create new authoring fields.
- 108 generated FAQs cover 38 of 39 published systems, including six Abbooti
  Kallaqaa FAQs for Smart AC Generator and Electric + Solar Bajaj. Afaan Oromo and
  Amharic translations were reviewed and approved by native-language reviewers,
  and the FAQ workflows are approved for chatbot release.
- A coverage report, export schema, authoring documentation, and manual private-runner
  release workflow are supplied. Administrator configuration remains necessary.

## Verification

| Check | Result |
| --- | --- |
| New knowledge-release unit tests | 13 passed |
| Full knowledge-base unit suite | 41 passed |
| Knowledge validation | Passed: 39 systems and 94 observations, with exact M-MESOB and Abbooti source exceptions |
| Public export disclosure check | Passed for rebuilt artifacts |
| Application API/retrieval/evaluation tests | 15 passed |
| Frontend type check and production asset build | Passed |
| Browser journeys | 6 passed: answers/citations/reset, Ethiopic input, offline reload/reconnect, delayed responses, inactivity reset, responsive layout |
| Production startup check with synthetic demo | Correctly refused |
| Docker image build | Not completed: daemon permission denied; passwordless sudo unavailable |
| Hosted deployment and venue/language acceptance | Not performed |

Production artifacts were rebuilt after validation; no presentation or video binary
was committed, and no factual approval was fabricated. The generated FAQ translation
approvals recorded in this handoff reflect the user's confirmation of native-speaker
review. The external Abbooti video path remains a source-owner environment detail
and is not emitted in the public chatbot bundle.

## Remaining release prerequisites

1. Review localized KPI unit labels and interface messages. Run
   `python -m scripts.chatbot_release coverage` to identify any remaining gaps.
2. Supply and evaluate the held-out bilingual question sets, complete the visitor
   pilot and hardware/network checks, and record publisher/operator signoffs.
3. Configure Docker access, the organization's Render workspace, private registry,
   DNS, private runners, and protected publisher environments. Build and promote
   the reviewed image, then rehearse rollback.

Application [evaluation](../../osta-exhibition-chatbot/docs/evaluation.md) and
[deployment instructions](../../osta-exhibition-chatbot/docs/deployment.md) provide
the exact commands and evidence contracts. Software verification does not replace
organizational publication decisions or native-speaker evaluation.
