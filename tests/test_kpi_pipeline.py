from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.kpi_pipeline import (
    ACTIVE_USER_CODES,
    REQUIRED_KPI_CODES,
    REQUIRED_PORTFOLIO_IDS,
    RepositoryData,
    ValidationFailure,
    build_payloads,
    check_observation_history,
    is_verified_public_observation,
    load_repository,
    _validate_source_refs,
    validate_records,
)

ROOT = Path(__file__).resolve().parents[1]


def record(records: list[dict], key: str, value: str) -> dict:
    return next(item for item in records if item[key] == value)


def make_public_observation(observation: dict) -> dict:
    observation["publication_status"] = "published"
    observation["verification_status"] = "verified"
    observation["data_classification"] = "public"
    observation["contains_personal_data"] = False
    observation["public_display_approved"] = True
    observation["reporting_period"] = {
        "type": "as-of-date",
        "start_date": "2026-08-31",
        "end_date": "2026-08-31",
        "reporting_date_text": "As of 31 August 2026",
        "calendar_type": "gregorian",
    }
    observation["source_refs"][0]["verification_status"] = "verified"
    observation["source_refs"][0]["public_display_approved"] = True
    observation["data_quality"].update(
        {
            "completeness": "complete",
            "accuracy_status": "verified",
            "duplicate_risk": "verified",
            "limitations": [],
        }
    )
    observation["exhibition"]["public_display_status"] = "approved"
    observation["workflow"].update(
        {
            "state": "approved",
            "reviewed_by_role": "kpi-reviewer",
            "updated_at": "2026-09-03",
            "notes": "Source and public display reviewed.",
        }
    )
    return observation


def synthetic_public_observation(
    data: RepositoryData,
    *,
    observation_id: str,
    system_id: str,
    kpi_code: str,
    value: int | float,
    unit: str,
    dimensions: dict | None = None,
) -> dict:
    observation = copy.deepcopy(data.observations[0])
    observation.update(
        {
            "id": observation_id,
            "system_id": system_id,
            "kpi_code": kpi_code,
            "measurement_scope": {
                "scope_type": "system",
                "scope_id": system_id,
                "description": "Whole-system measurement",
            },
            "achievement_type": "actual",
            "actual": {"operator": "equal", "value": value, "unit": unit},
            "baseline": {"operator": "not-specified", "value": None, "unit": unit},
            "target": {"operator": "not-specified", "value": None, "unit": unit},
            "achievement": None,
            "dimensions": copy.deepcopy(dimensions or {}),
            "display_value": None,
            "supersedes_observation_id": None,
        }
    )
    return make_public_observation(observation)


def publish_system(data: RepositoryData, system_id: str, headline_refs: list[str]) -> dict:
    system = record(data.systems, "id", system_id)
    system["publication_status"] = "published"
    system["lifecycle_status"] = "operational"
    system["headline_kpi_refs"] = headline_refs
    system["workflow"].update(
        {
            "review_status": "approved",
            "updated_at": "2026-09-03",
            "approved_by_role": "publisher",
        }
    )
    return system


class KpiPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = load_repository(ROOT)

    def data(self) -> RepositoryData:
        return copy.deepcopy(self.base)

    def assert_invalid(self, data: RepositoryData, message: str) -> ValidationFailure:
        with self.assertRaises(ValidationFailure) as context:
            validate_records(data, ROOT)
        self.assertIn(message, str(context.exception))
        return context.exception

    def test_repository_records_are_valid(self) -> None:
        validate_records(self.data(), ROOT)
        self.assertTrue(REQUIRED_KPI_CODES.issubset({item["kpi_code"] for item in self.base.definitions}))
        self.assertEqual(REQUIRED_PORTFOLIO_IDS, {item["id"] for item in self.base.portfolio_kpis})

    def test_missing_m_mesob_pdf_exception_is_record_scoped(self) -> None:
        source_ref = {
            "source_id": "osta-facebook-mmesob-2026",
            "label": "M-MESOB source",
            "path": "source-materials/social-media/mmesob-facebook-post.pdf",
            "locator": "Page 1",
            "verification_status": "needs-review",
            "public_display_approved": False,
        }
        errors: list[str] = []
        _validate_source_refs({"id": "foreign", "system_id": "prms", "source_refs": [source_ref]}, ROOT, "foreign", errors)
        self.assertIn("source path does not exist", errors[0])
        errors = []
        _validate_source_refs({"id": "m-mesob", "source_refs": [source_ref]}, ROOT, "m-mesob", errors)
        self.assertEqual([], errors)

    def test_candidate_observations_remain_nonpublic_and_structured(self) -> None:
        candidates = [item for item in self.base.observations if item["id"].endswith("-deck")]
        self.assertEqual(9, len(candidates))
        for observation in candidates:
            with self.subTest(observation=observation["id"]):
                self.assertEqual("draft", observation["publication_status"])
                self.assertEqual("needs-review", observation["verification_status"])
                self.assertFalse(observation["public_display_approved"])
                self.assertIsInstance(observation["actual"], dict)
                self.assertIsInstance(observation["baseline"], dict)
                self.assertIsInstance(observation["target"], dict)
                self.assertIsNot(observation["actual"], observation["baseline"])
                self.assertIsNot(observation["actual"], observation["target"])

    def test_duplicate_primary_identifiers_are_rejected(self) -> None:
        cases = (
            ("systems", self.base.systems[0], "duplicate digital system id"),
            ("definitions", self.base.definitions[0], "duplicate KPI definition kpi_code"),
            ("observations", self.base.observations[0], "duplicate KPI observation id"),
        )
        for collection, duplicate, expected in cases:
            with self.subTest(collection=collection):
                data = self.data()
                getattr(data, collection).append(copy.deepcopy(duplicate))
                self.assert_invalid(data, expected)

    def test_unknown_system_reference_is_rejected(self) -> None:
        data = self.data()
        data.observations[0]["system_id"] = "unknown-system"
        self.assert_invalid(data, "unknown system_id unknown-system")

    def test_unknown_kpi_reference_is_rejected(self) -> None:
        data = self.data()
        data.observations[0]["kpi_code"] = "unknown-kpi"
        self.assert_invalid(data, "unknown kpi_code unknown-kpi")

    def test_published_kpi_requires_verified_source(self) -> None:
        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["source_refs"][0]["verification_status"] = "needs-review"
        self.assert_invalid(data, "published KPI requires a verified source")

    def test_published_kpi_requires_reporting_period(self) -> None:
        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["reporting_period"] = {
            "type": "unknown",
            "start_date": None,
            "end_date": None,
            "reporting_date_text": None,
            "calendar_type": "unknown",
        }
        self.assert_invalid(data, "published KPI requires a reporting period")

    def test_published_kpi_requires_unit(self) -> None:
        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["actual"]["unit"] = None
        self.assert_invalid(data, "published KPI requires a unit")

    def test_published_kpi_rejects_placeholder_text(self) -> None:
        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["workflow"]["notes"] = "TODO confirm"
        self.assert_invalid(data, "published KPI contains placeholder text")

    def test_percentage_bounds_are_rejected(self) -> None:
        for value in (-0.1, 100.1):
            with self.subTest(value=value):
                data = self.data()
                observation = record(data.observations, "id", "digital-kebele-implementation-progress-2018-deck")
                observation["actual"]["value"] = value
                self.assert_invalid(data, "percentage in actual must be between 0 and 100")

    def test_negative_counts_are_rejected(self) -> None:
        data = self.data()
        data.observations[0]["actual"]["value"] = -1
        self.assert_invalid(data, "negative count in actual")

    def test_response_time_requires_duration_unit_and_statistic(self) -> None:
        data = self.data()
        observation = copy.deepcopy(data.observations[0])
        observation.update(
            {
                "id": "response-time-invalid",
                "kpi_code": "response-time",
                "actual": {"operator": "equal", "value": 12, "unit": "record"},
                "baseline": {"operator": "not-specified", "value": None, "unit": "record"},
                "target": {"operator": "not-specified", "value": None, "unit": "record"},
                "dimensions": {},
            }
        )
        data.observations.append(observation)
        failure = self.assert_invalid(data, "response-time requires a duration unit")
        self.assertIn("response-time requires a statistic dimension", str(failure))

    def test_availability_requires_monitoring_period(self) -> None:
        data = self.data()
        observation = copy.deepcopy(data.observations[3])
        observation.update({"id": "availability-invalid", "kpi_code": "availability-percent", "dimensions": {}})
        data.observations.append(observation)
        self.assert_invalid(data, "availability requires a monitoring period")

    def test_active_users_require_activity_window(self) -> None:
        for kpi_code in sorted(ACTIVE_USER_CODES):
            with self.subTest(kpi_code=kpi_code):
                data = self.data()
                observation = copy.deepcopy(data.observations[1])
                observation.update(
                    {
                        "id": f"{kpi_code}-invalid",
                        "kpi_code": kpi_code,
                        "actual": {"operator": "equal", "value": 1, "unit": "user"},
                        "baseline": {"operator": "not-specified", "value": None, "unit": "user"},
                        "target": {"operator": "not-specified", "value": None, "unit": "user"},
                        "dimensions": {},
                    }
                )
                data.observations.append(observation)
                self.assert_invalid(data, "active-user KPI requires an activity window")

    def test_conflicting_published_kpi_is_rejected(self) -> None:
        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["verification_status"] = "conflicting"
        observation["data_quality"]["accuracy_status"] = "conflicting"
        self.assert_invalid(data, "published KPI cannot be marked conflicting")

    def test_public_kpi_rejects_personal_or_nonpublic_data(self) -> None:
        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["contains_personal_data"] = True
        self.assert_invalid(data, "public exhibition output cannot contain personal data")

        data = self.data()
        observation = make_public_observation(data.observations[0])
        observation["data_classification"] = "confidential"
        self.assert_invalid(data, "public exhibition output requires public data_classification")

    def test_published_system_requires_kpi_or_approved_exception(self) -> None:
        data = self.data()
        system = publish_system(data, "prms", ["prms-records-registered-2018-deck"])
        self.assert_invalid(data, "published digital system requires a verified KPI")

        data = self.data()
        system = publish_system(data, "prms", ["prms-records-registered-2018-deck"])
        system["kpi_data_unavailable_exception"] = {
            "reason": "Source-owner verification is pending.",
            "approved": True,
            "approved_by_role": "publisher",
            "approval_date": "2026-09-03",
            "expires_on": "2026-12-31",
        }
        validate_records(data, ROOT)

    def test_observation_history_is_append_only(self) -> None:
        data = self.data()
        check_observation_history(data, ROOT)

        changed = self.data()
        changed.observations[0]["actual"]["value"] += 1
        with self.assertRaisesRegex(ValidationFailure, "historical KPI observation was overwritten"):
            check_observation_history(changed, ROOT, accept_new=True)

        added = self.data()
        new_observation = copy.deepcopy(added.observations[0])
        new_observation["id"] = "new-reviewed-observation"
        added.observations.append(new_observation)
        with self.assertRaisesRegex(ValidationFailure, "not history-locked"):
            check_observation_history(added, ROOT)
        updated = check_observation_history(added, ROOT, accept_new=True)
        self.assertIn("new-reviewed-observation", updated["observations"])

    def test_unresolved_conflicts_require_explicit_supersession(self) -> None:
        data = self.data()
        first = synthetic_public_observation(
            data,
            observation_id="conflict-record-a",
            system_id="prms",
            kpi_code="records-registered",
            value=40000,
            unit="record",
        )
        second = copy.deepcopy(first)
        second["id"] = "conflict-record-b"
        second["actual"]["value"] = 41000
        data.observations.extend([first, second])
        self.assert_invalid(data, "unresolved conflicting observations require explicit supersession")

        data = self.data()
        first = synthetic_public_observation(
            data,
            observation_id="superseded-record-a",
            system_id="prms",
            kpi_code="records-registered",
            value=40000,
            unit="record",
        )
        second = copy.deepcopy(first)
        second["id"] = "superseding-record-b"
        second["actual"]["value"] = 41000
        second["supersedes_observation_id"] = first["id"]
        data.observations.extend([first, second])
        validate_records(data, ROOT)

    def test_catalog_blocks_active_user_and_percentage_sums(self) -> None:
        data = self.data()
        definition = record(data.definitions, "kpi_code", "active-users")
        definition["aggregation"]["method"] = "sum"
        self.assert_invalid(data, "active-user KPIs must be not-aggregatable")

        data = self.data()
        definition = record(data.definitions, "kpi_code", "availability-percent")
        definition["aggregation"]["method"] = "sum"
        self.assert_invalid(data, "percentage KPIs cannot use sum aggregation")

    def test_numeric_narratives_must_reference_observations(self) -> None:
        data = self.data()
        system = record(data.systems, "id", "prms")
        system["purpose"] = "Manage more than 39,800 registered records."
        self.assert_invalid(data, "narrative duplicates an authoritative KPI value")

        data = self.data()
        data.faqs.append(
            {
                "schema_version": "1.0.0",
                "record_version": 1,
                "id": "uemis-users-faq",
                "system_id": "uemis",
                "question": "How many users are registered?",
                "answer": "The platform has 3,987 registered users.",
                "kpi_observation_refs": ["uemis-registered-users-2018-deck"],
                "translations": {},
                "publication_status": "draft",
                "data_classification": "internal",
                "contains_personal_data": False,
                "public_display_approved": False,
                "workflow": {"state": "draft"},
            }
        )
        self.assert_invalid(data, "numeric FAQ claims must use a KPI observation token")

    def test_faq_token_references_authoritative_value(self) -> None:
        data = self.data()
        data.faqs.append(
            {
                "schema_version": "1.0.0",
                "record_version": 1,
                "id": "uemis-users-faq",
                "system_id": "uemis",
                "question": "What is the verified registration result?",
                "answer": "The verified result is {{kpi:uemis-registered-users-2018-deck}}.",
                "kpi_observation_refs": ["uemis-registered-users-2018-deck"],
                "translations": {},
                "publication_status": "draft",
                "data_classification": "internal",
                "contains_personal_data": False,
                "public_display_approved": False,
                "workflow": {"state": "draft"},
            }
        )
        validate_records(data, ROOT)

    def test_unapproved_amharic_translation_is_rejected(self) -> None:
        data = self.data()
        system = record(data.systems, "id", "prms")
        system["translations"]["am"] = {
            "official_name": "Unreviewed text",
            "purpose": "Unreviewed text",
            "approval": {
                "status": "needs-review",
                "human_reviewed": False,
                "reviewer_role": None,
                "approved_source": False,
                "reviewed_at": None,
            },
        }
        self.assert_invalid(data, "Amharic translation requires an approved source")

    def test_public_build_includes_published_systems_and_observations(self) -> None:
        data = self.data()
        payloads = build_payloads(data)
        expected_systems = {
            "prms",
            "uemis",
            "business-automation",
            "digital-kebele-government",
            "court-case-management-prosecutor-sims",
            "civil-registration-dms",
            "smart-ac-generator",
            "electric-solar-bajaj",
        }
        self.assertEqual(expected_systems, {item["id"] for item in payloads["digital-systems.json"]["digital_systems"]})
        self.assertEqual(expected_systems, {item["system_id"] for item in payloads["system-kpis.json"]["systems"]})
        avatar = payloads["avatar-facts.json"]
        self.assertEqual(9, len(avatar["verified_public_kpi_observations"]))
        self.assertEqual(8, len(avatar["approved_afaan_oromo_content"]))
        self.assertEqual(8, len(avatar["approved_amharic_content"]))
            item["id"] for item in data.systems if item.get("publication_status") == "published"
        }
        self.assertEqual(expected_systems, {item["id"] for item in payloads["digital-systems.json"]["digital_systems"]})
        self.assertEqual(expected_systems, {item["system_id"] for item in payloads["system-kpis.json"]["systems"]})

        expected_observations = {
            item["id"]
            for item in data.observations
            if is_verified_public_observation(item) and item.get("system_id") in expected_systems
        }
        self.assertEqual(
            expected_observations,
            {item["id"] for item in payloads["avatar-facts.json"]["verified_public_kpi_observations"]},
        )

        expected_translation_records = {
            ("digital-system", item["id"])
            for item in data.systems
            if item.get("publication_status") == "published"
        }
        expected_faqs = {
            item["id"]
            for item in data.faqs
            if (
                item.get("publication_status") == "published"
                and item.get("workflow", {}).get("state") == "approved"
                and item.get("public_display_approved") is True
                and item.get("data_classification") == "public"
                and item.get("contains_personal_data") is False
                and item.get("system_id") in expected_systems
                and all(ref in expected_observations for ref in item.get("kpi_observation_refs", []))
            )
        }
        expected_translation_records.update(("faq", faq_id) for faq_id in expected_faqs)
        self.assertEqual(
            expected_translation_records,
            {
                (item["record_type"], item["record_id"])
                for item in payloads["avatar-facts.json"]["approved_afaan_oromo_content"]
            },
        )

        generated_faqs = {
            item["id"]
            for item in data.faqs
            if item["id"].endswith("-faq") and item["id"] not in expected_faqs
        }
        self.assertFalse(generated_faqs)
        self.assertTrue(
            {item["id"] for item in data.faqs if item["id"].endswith("-faq")}
            <= {item["id"] for item in payloads["avatar-facts.json"]["published_faqs"]}
        )
        self.assertEqual(
            expected_translation_records,
            {
                (item["record_type"], item["record_id"])
                for item in payloads["avatar-facts.json"]["approved_amharic_content"]
            },
        )

        serialized = json.dumps(payloads)
        for observation in self.base.observations:
            if observation["id"].endswith("-deck"):
                self.assertNotIn(observation["id"], serialized)

    def test_verified_public_observation_reaches_system_and_avatar_outputs(self) -> None:
        data = self.data()
        observation = make_public_observation(record(data.observations, "id", "prms-records-registered-2018-verified"))
        publish_system(data, "prms", [observation["id"]])
        validate_records(data, ROOT)
        payloads = build_payloads(data)
        self.assertIn("prms", [item["id"] for item in payloads["digital-systems.json"]["digital_systems"]])
        prms_kpis = next(item for item in payloads["system-kpis.json"]["systems"] if item["system_id"] == "prms")
        self.assertEqual(observation["id"], prms_kpis["observations"][0]["id"])
        avatar = payloads["avatar-facts.json"]
        public_observation = next(item for item in avatar["verified_public_kpi_observations"] if item["id"] == observation["id"])
        self.assertEqual(observation["id"], public_observation["id"])
        self.assertEqual("> 39,800 records", public_observation["display_value"])
        self.assertNotIn("path", avatar["source_labels"][0])

    def test_count_unique_dashboard_deduplicates_entities(self) -> None:
        data = self.data()
        first = synthetic_public_observation(
            data,
            observation_id="applications-prms-2026",
            system_id="prms",
            kpi_code="applications-developed",
            value=2,
            unit="application",
            dimensions={"platform": "all", "entity_ids": ["app-a", "app-b"]},
        )
        second = synthetic_public_observation(
            data,
            observation_id="applications-uemis-2026",
            system_id="uemis",
            kpi_code="applications-developed",
            value=2,
            unit="application",
            dimensions={"platform": "all", "entity_ids": ["app-b", "app-c"]},
        )
        data.observations.extend([first, second])
        publish_system(data, "prms", [first["id"]])
        publish_system(data, "uemis", [second["id"]])
        validate_records(data, ROOT)
        metrics = build_payloads(data)["portfolio-dashboard.json"]["metrics"]
        metric = record(metrics, "id", "dashboard-applications-developed")
        self.assertEqual("aggregated", metric["aggregation_status"])
        self.assertEqual(3, metric["value"])
        self.assertEqual({first["id"], second["id"]}, set(metric["observation_ids"]))

    def test_active_user_dashboard_never_produces_cross_system_total(self) -> None:
        data = self.data()
        window = {
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "value": None,
            "unit": None,
            "description": "Users with a successful sign-in during the month.",
        }
        observations = [
            synthetic_public_observation(
                data,
                observation_id=f"active-{system_id}-2026-08",
                system_id=system_id,
                kpi_code="active-users",
                value=value,
                unit="user",
                dimensions={"activity_window": window},
            )
            for system_id, value in (("prms", 10), ("uemis", 20))
        ]
        data.observations.extend(observations)
        for observation in observations:
            publish_system(data, observation["system_id"], [observation["id"]])
        validate_records(data, ROOT)
        metrics = build_payloads(data)["portfolio-dashboard.json"]["metrics"]
        metric = record(metrics, "id", "dashboard-active-users")
        self.assertEqual("series-only", metric["aggregation_status"])
        self.assertNotIn("value", metric)
        self.assertEqual(2, len(metric["series"]))

    def test_weighted_availability_uses_monitoring_weights(self) -> None:
        data = self.data()
        monitoring_period = {
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "value": None,
            "unit": None,
            "description": "Whole calendar month excluding no intervals.",
        }
        observations = [
            synthetic_public_observation(
                data,
                observation_id=f"availability-{system_id}-2026-08",
                system_id=system_id,
                kpi_code="availability-percent",
                value=value,
                unit="percent",
                dimensions={
                    "monitoring_period": monitoring_period,
                    "aggregation_partition": system_id,
                    "aggregation_weight": 1,
                },
            )
            for system_id, value in (("prms", 99), ("uemis", 97))
        ]
        data.observations.extend(observations)
        for observation in observations:
            publish_system(data, observation["system_id"], [observation["id"]])
        validate_records(data, ROOT)
        metrics = build_payloads(data)["portfolio-dashboard.json"]["metrics"]
        metric = record(metrics, "id", "dashboard-system-availability")
        self.assertEqual("weighted-average", metric["aggregation_method"])
        self.assertEqual(98, metric["value"])
        self.assertEqual("98.00%", metric["display_value"])


if __name__ == "__main__":
    unittest.main()
