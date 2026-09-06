"""Contract tests use isolated synthetic records, never fabricated source files."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.chatbot_release import approved_translation, build_chatbot_payload, release
from scripts.kpi_pipeline import RepositoryData, ValidationFailure, _validate_faqs, build_payloads, load_repository, render_localized_faq


class ChatbotReleaseTests(unittest.TestCase):
    def setUp(self):
        self.observation = {"id": "test-count", "kpi_code": "count", "system_id": "test-system", "actual": {"operator": "approximate", "value": 120, "unit": "record"}}
        self.definition = {"kpi_code": "count", "display": {"unit_label": "records", "decimal_places": 0}}
        self.translation = {"question": "Synthetic question", "answer": "Synthetic {{kpi:test-count|number}} records.", "approval": {"status": "approved", "human_reviewed": True, "reviewer_role": "human-afaan-oromo-reviewer"}}

    def render(self, translation, **kwargs):
        return render_localized_faq(translation, {"test-count": self.observation}, {"count": self.definition}, **kwargs)

    def test_number_template_preserves_operator_and_prose(self):
        self.assertEqual("Synthetic ≈ 120 records.", self.render(self.translation)["answer"])
        self.observation["actual"] = {"operator": "greater-than", "value": 121, "unit": "record"}
        self.assertEqual("Synthetic > 121 records.", self.render(self.translation)["answer"])

    def test_range_and_percent(self):
        self.observation["actual"] = {"operator": "range", "value": {"minimum": 1, "maximum": 3}, "unit": "record"}
        self.assertEqual("Synthetic 1–3 records.", self.render(self.translation)["answer"])
        self.translation["answer"] = "{{kpi:test-count}}"
        self.observation["actual"] = {"operator": "less-than", "value": 20, "unit": "percent"}
        self.assertEqual("< 20%", self.render(self.translation, require_localized_units=True)["answer"])

    def test_full_token_requires_reviewed_unit_for_chatbot(self):
        self.translation["answer"] = "{{kpi:test-count}}"
        with self.assertRaisesRegex(ValidationFailure, "localized KPI unit"):
            self.render(self.translation, require_localized_units=True)
        self.translation["kpi_unit_labels"] = {"test-count": "synthetic-unit"}
        self.assertEqual("≈ 120 synthetic-unit", self.render(self.translation, require_localized_units=True)["answer"])

    def test_translation_approval_is_language_specific(self):
        record = {"translations": {"om": self.translation, "am": self.translation}}
        self.assertIsNotNone(approved_translation(record, "om"))
        self.assertIsNone(approved_translation(record, "am"))
        self.translation["approval"]["status"] = "needs-review"
        self.assertIsNone(approved_translation(record, "om"))

    def test_generated_faq_translations_are_human_approved(self):
        faq = next(item for item in load_repository(Path(__file__).resolve().parents[1]).faqs if item["id"] == "prms-purpose-faq")
        self.assertEqual("published", faq["publication_status"])
        self.assertEqual("approved", faq["workflow"]["state"])
        for language, role in (("om", "human-afaan-oromo-reviewer"), ("am", "human-amharic-reviewer")):
            translation = faq["translations"][language]
            self.assertEqual("approved", translation["approval"]["status"])
            self.assertTrue(translation["approval"]["human_reviewed"])
            self.assertEqual(role, translation["approval"]["reviewer_role"])
            self.assertIsNotNone(approved_translation(faq, language))

    def test_reviewed_generated_faq_enters_chatbot_bundle(self):
        system = {
            "id": "test-system", "publication_status": "published",
            "workflow": {"review_status": "approved"},
            "translations": {
                language: {
                    "official_name": f"Synthetic {language}", "purpose": "Synthetic purpose",
                    "approval": {
                        "status": "approved", "human_reviewed": True,
                        "reviewer_role": f"human-{'amharic' if language == 'am' else 'afaan-oromo'}-reviewer",
                    },
                }
                for language in ("om", "am")
            },
        }
        faq = {
            "id": "test-purpose-faq", "system_id": "test-system", "kpi_observation_refs": [],
            "publication_status": "published", "public_display_approved": True,
            "data_classification": "public", "contains_personal_data": False,
            "workflow": {"state": "approved"},
            "translations": {
                language: {
                    "question": f"Synthetic question {language}", "answer": f"Synthetic answer {language}",
                    "approval": {
                        "status": "approved", "human_reviewed": True,
                        "reviewer_role": f"human-{'amharic' if language == 'am' else 'afaan-oromo'}-reviewer",
                    },
                }
                for language in ("om", "am")
            },
        }
        data = RepositoryData([system], [], [], [], [], [faq])
        public = {"avatar-facts.json": {"verified_public_kpi_observations": [], "published_faqs": [{"id": faq["id"]}]}}
        payload = build_chatbot_payload(data, public)
        self.assertEqual({"system:test-system:om", "system:test-system:am", "faq:test-purpose-faq:om", "faq:test-purpose-faq:am"}, {item["id"] for item in payload["answers"]})

    def test_approved_m_mesob_is_in_chatbot_bundle(self):
        root = Path(__file__).resolve().parents[1]
        data = load_repository(root)
        public = build_payloads(data)
        payload = build_chatbot_payload(data, public)
        self.assertEqual(
            {
                "system:m-mesob:om", "system:m-mesob:am",
                "faq:m-mesob-purpose-faq:om", "faq:m-mesob-purpose-faq:am",
                "faq:m-mesob-beneficiaries-faq:om", "faq:m-mesob-beneficiaries-faq:am",
                "faq:m-mesob-capabilities-faq:om", "faq:m-mesob-capabilities-faq:am",
            },
            {item["id"] for item in payload["answers"] if item["system_id"] == "m-mesob"},
        )

    def test_translated_literals_and_unlisted_tokens_are_rejected(self):
        faq = {"id": "test-faq", "system_id": "test-system", "kpi_observation_refs": ["test-count"], "question": "Synthetic question", "answer": "{{kpi:test-count}}", "translations": {"om": self.translation}}
        for text, message in [("120 records", "numeric FAQ"), ("{{kpi:unknown|number}}", "unlisted"), ("{{kpi:test-count|invalid}}", "malformed")]:
            with self.subTest(text=text):
                self.translation["answer"] = text
                errors = []
                _validate_faqs([faq], {"test-system": {}}, {"test-count": self.observation}, errors)
                self.assertTrue(any(message in error for error in errors), errors)

    def test_unapproved_system_never_reaches_chatbot(self):
        system = {"id": "test-system", "publication_status": "published", "workflow": {"review_status": "needs-review"}, "translations": {"om": {**self.translation, "official_name": "Synthetic system", "purpose": "Synthetic purpose"}}}
        data = RepositoryData([system], [], [], [], [], [])
        public = {"avatar-facts.json": {"verified_public_kpi_observations": [], "published_faqs": []}}
        self.assertEqual([], build_chatbot_payload(data, public)["answers"])
        system["workflow"]["review_status"] = "approved"
        self.assertEqual(1, len(build_chatbot_payload(data, public)["answers"]))

    def test_failed_validation_creates_no_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "releases"
            with patch("scripts.chatbot_release.validate_repository", side_effect=ValidationFailure(["missing evidence"])):
                with self.assertRaises(ValidationFailure):
                    release(Path(temporary), output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
