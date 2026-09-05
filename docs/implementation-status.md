# Chatbot implementation handoff — 5 September 2026

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
- 99 English starter FAQs cover 35 of 36 published systems. They are internal
  drafts assembled from existing records, with no translations or new approvals.
- A coverage report, export schema, authoring documentation, and manual private-runner
  release workflow are supplied. Administrator configuration remains necessary.

## Verification

| Check | Result |
| --- | --- |
| New knowledge-release unit tests | 7 passed |
| Full knowledge-base unit suite | 35 executed; 8 errors caused by the existing missing M-Mesob PDF |
| Knowledge validation | Blocked by the missing PDF |
| Public export JSON-schema check | Passed in memory; this is not a validated production release |
| Application API/retrieval/evaluation tests | 15 passed |
| Frontend type check and production asset build | Passed |
| Browser journeys | 6 passed: answers/citations/reset, Ethiopic input, offline reload/reconnect, delayed responses, inactivity reset, responsive layout |
| Production startup check with synthetic demo | Correctly refused |
| Docker image build | Not completed: daemon permission denied; passwordless sudo unavailable |
| Hosted deployment and venue/language acceptance | Not performed |

No production artifacts were rebuilt from unvalidated evidence, no presentation
binary was committed, and no factual or language approval was fabricated. Existing
`dist/` snapshots are unchanged. New workflows have not been pushed or run remotely.

## Remaining release prerequisites

1. Restore the actual authorized `source-materials/social-media/mmesob-facebook-post.pdf`
   or have the content owner resolve its affected records without changing accepted
   observation history or bypassing validation.
2. Review visitor FAQs, localized KPI unit labels, and all interface messages in both
   languages. Run `python -m scripts.chatbot_release coverage` to identify gaps.
3. Supply and evaluate the held-out bilingual question sets, complete the visitor
   pilot and hardware/network checks, and record publisher/operator signoffs.
4. Configure Docker access, the organization's Render workspace, private registry,
   DNS, private runners, and protected publisher environments. Build and promote
   the reviewed image, then rehearse rollback.

Application [evaluation](../../osta-exhibition-chatbot/docs/evaluation.md) and
[deployment instructions](../../osta-exhibition-chatbot/docs/deployment.md) provide
the exact commands and evidence contracts. Software verification does not replace
organizational publication decisions or native-speaker evaluation.
