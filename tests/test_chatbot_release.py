"""Contract tests use isolated synthetic records, never fabricated source files."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.chatbot_release import approved_translation, build_chatbot_payload, release
from scripts.kpi_pipeline import RepositoryData, ValidationFailure, _validate_faqs, render_localized_faq


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
