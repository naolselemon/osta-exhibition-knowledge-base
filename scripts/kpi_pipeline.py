#!/usr/bin/env python3
"""Validate KPI records and build disclosure-safe exhibition artifacts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

SCHEMA_VERSION = "1.0.0"

KPI_CATEGORIES = {
    "digitization-output",
    "service-delivery",
    "adoption",
    "usage",
    "coverage",
    "integration",
    "performance",
    "efficiency",
    "quality",
    "implementation",
    "impact",
    "financial-impact",
    "ai-and-automation",
}
MEASUREMENT_TYPES = {
    "cumulative",
    "periodic",
    "point-in-time",
    "percentage",
    "duration",
    "currency",
    "ratio",
    "boolean",
    "qualitative",
}
AGGREGATION_METHODS = {
    "sum",
    "count-unique",
    "latest",
    "average",
    "weighted-average",
    "minimum",
    "maximum",
    "not-aggregatable",
}
OPERATORS = {
    "equal",
    "greater-than",
    "greater-than-or-equal",
    "less-than",
    "less-than-or-equal",
    "approximate",
    "range",
    "not-specified",
}
REPORTING_PERIOD_TYPES = {
    "as-of-date",
    "day",
    "week",
    "month",
    "quarter",
    "year",
    "date-range",
    "lifetime",
    "unknown",
}
DATA_QUALITY_VALUES = {
    "complete",
    "partial",
    "unknown",
    "needs-review",
    "verified",
    "conflicting",
}
DURATION_UNITS = {"millisecond", "second", "minute", "hour"}
ACTIVE_USER_CODES = {"active-users", "mobile-active-users", "web-active-users"}
# The M-MESOB source PDF is intentionally not mounted in this checkout. Keep this
# exception exact: it applies only to the named source/path pair and never creates
# evidence or changes a source's review state.
INTENTIONALLY_MISSING_SOURCE_PATHS = {
    ("osta-facebook-mmesob-2026", "source-materials/social-media/mmesob-facebook-post.pdf"),
}
REQUIRED_KPI_CODES = {
    "applications-developed",
    "services-digitized",
    "systems-integrated",
    "services-offered",
    "institutions-served",
    "registered-users",
    "active-users",
    "mobile-downloads",
    "mobile-active-users",
    "web-active-users",
    "beneficiaries-served",
    "workflows-automated",
    "digital-transactions",
    "reports-generated",
    "dashboards-available",
    "ai-solutions",
    "records-registered",
    "records-digitized",
    "files-scanned",
    "files-uploaded",
    "metadata-completion-percent",
    "service-coverage-percent",
    "locations-covered",
    "implementation-progress-percent",
    "availability-percent",
    "response-time",
    "processing-time-reduction",
    "office-visits-reduced",
    "paper-records-reduced",
    "cost-savings",
}
REQUIRED_PORTFOLIO_IDS = {
    "dashboard-applications-developed",
    "dashboard-digital-services",
    "dashboard-institutions-served",
    "dashboard-active-users",
    "dashboard-mobile-applications",
    "dashboard-web-applications",
    "dashboard-systems-integrated",
    "dashboard-automated-workflows",
    "dashboard-digital-transactions",
    "dashboard-ai-solutions",
    "dashboard-system-availability",
}
TRANSFORMATION_DIMENSIONS = {
    "paper-application-to-online-application",
    "physical-queue-to-digital-queue",
    "manual-verification-to-automated-validation",
    "paper-file-to-digital-record",
    "multiple-office-visits-to-remote-access",
    "manual-reporting-to-real-time-dashboard",
    "long-processing-time-to-faster-processing",
    "difficult-tracking-to-end-to-end-tracking",
}
PLACEHOLDER_RE = re.compile(r"(?:\bXX\b|\bTODO\b|\bTBD\b|replace-with|<[^>]+>)", re.IGNORECASE)
KPI_TOKEN_RE = re.compile(r"\{\{kpi:([a-z0-9]+(?:-[a-z0-9]+)*)\}\}")
LOCALIZED_KPI_TOKEN_RE = re.compile(r"\{\{kpi:([a-z0-9]+(?:-[a-z0-9]+)*)(\|number)?\}\}")
NUMBER_RE = re.compile(r"(?<![a-z0-9])(?:\d[\d,]*(?:\.\d+)?)(?:\s*%|\s+(?:thousand|million|billion))?(?![a-z0-9])", re.IGNORECASE)

SYSTEM_REQUIRED = {
    "schema_version",
    "id",
    "slug",
    "official_name",
    "acronym",
    "category",
    "subcategories",
    "lifecycle_status",
    "publication_status",
    "organization",
    "system_classification",
    "purpose",
    "beneficiaries",
    "services_digitized",
    "integrations",
    "geographic_coverage",
    "headline_kpi_refs",
    "transformation_story_refs",
    "faq_refs",
    "media",
    "translations",
    "workflow",
}
DEFINITION_REQUIRED = {
    "schema_version",
    "record_version",
    "kpi_code",
    "name",
    "description",
    "kpi_category",
    "applicable_system_types",
    "measurement_type",
    "value_type",
    "allowed_operators",
    "allowed_units",
    "direction_of_improvement",
    "aggregation",
    "reporting_requirements",
    "display",
    "status",
}
OBSERVATION_REQUIRED = {
    "schema_version",
    "record_version",
    "id",
    "system_id",
    "kpi_code",
    "measurement_scope",
    "achievement_type",
    "actual",
    "baseline",
    "target",
    "achievement",
    "reporting_period",
    "dimensions",
    "measurement_method",
    "display_value",
    "source_refs",
    "data_quality",
    "exhibition",
    "workflow",
    "publication_status",
    "verification_status",
    "data_classification",
    "contains_personal_data",
    "public_display_approved",
}
PORTFOLIO_REQUIRED = {
    "schema_version",
    "record_version",
    "id",
    "name",
    "kpi_code",
    "filters",
    "aggregation_method",
    "deduplication",
    "observation_selection",
    "display",
    "status",
}
STORY_REQUIRED = {
    "schema_version",
    "record_version",
    "id",
    "system_id",
    "title",
    "summary",
    "transformation_dimensions",
    "before",
    "after",
    "user_impact",
    "kpi_observation_refs",
    "source_refs",
    "translations",
    "publication_status",
    "verification_status",
    "public_display_approved",
    "workflow",
}
FAQ_REQUIRED = {
    "schema_version",
    "record_version",
    "id",
    "system_id",
    "question",
    "answer",
    "kpi_observation_refs",
    "translations",
    "publication_status",
    "data_classification",
    "contains_personal_data",
    "public_display_approved",
    "workflow",
}


class ValidationFailure(Exception):
    """Raised with every deterministic validation error found in one pass."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


@dataclass
class RepositoryData:
    systems: list[dict[str, Any]]
    definitions: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    portfolio_kpis: list[dict[str, Any]]
    stories: list[dict[str, Any]]
    faqs: list[dict[str, Any]]


def _load_yaml_records(directory: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not directory.exists():
        return records
    for path in sorted((*directory.glob("*.yml"), *directory.glob("*.yaml"))):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if payload is None:
            continue
        if isinstance(payload, dict) and "records" in payload:
            payload = payload["records"]
        elif isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            raise ValidationFailure([f"{path}: expected a record, a list, or a records list"])
        for offset, record in enumerate(payload, start=1):
            if not isinstance(record, dict):
                raise ValidationFailure([f"{path}: record {offset} is not an object"])
            records.append(record)
    return records


def load_repository(root: Path) -> RepositoryData:
    content = root / "content"
    return RepositoryData(
        systems=_load_yaml_records(content / "digital-systems"),
        definitions=_load_yaml_records(content / "kpi-definitions"),
        observations=_load_yaml_records(content / "kpi-observations"),
        portfolio_kpis=_load_yaml_records(content / "portfolio-kpis"),
        stories=_load_yaml_records(content / "transformation-stories"),
        faqs=_load_yaml_records(content / "faqs"),
    )


def _record_label(kind: str, record: dict[str, Any], key: str) -> str:
    return f"{kind} {record.get(key, '<missing>')}"


def _require(record: dict[str, Any], fields: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(fields - record.keys())
    if missing:
        errors.append(f"{label}: missing required fields: {', '.join(missing)}")


def _index(records: list[dict[str, Any]], key: str, kind: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        value = record.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{kind}: missing or invalid {key}")
            continue
        if value in result:
            errors.append(f"duplicate {kind} {key}: {value}")
        else:
            result[value] = record
    return result


def _numeric_values(measurement: Any) -> list[float]:
    if not isinstance(measurement, dict):
        return []
    value = measurement.get("value")
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, dict):
        return [float(item) for item in (value.get("minimum"), value.get("maximum")) if isinstance(item, (int, float)) and not isinstance(item, bool)]
    return []


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def observation_hash(observation: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(observation).encode("utf-8")).hexdigest()


def _has_window(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    has_dates = bool(value.get("start_date") and value.get("end_date"))
    has_duration = isinstance(value.get("value"), (int, float)) and value.get("unit") not in (None, "")
    return has_dates or has_duration


def _verified_source(observation: dict[str, Any]) -> bool:
    refs = observation.get("source_refs")
    return isinstance(refs, list) and any(isinstance(ref, dict) and ref.get("verification_status") == "verified" for ref in refs)


def is_verified_public_observation(observation: dict[str, Any]) -> bool:
    quality = observation.get("data_quality") or {}
    exhibition = observation.get("exhibition") or {}
    return (
        observation.get("publication_status") == "published"
        and observation.get("verification_status") == "verified"
        and quality.get("accuracy_status") == "verified"
        and observation.get("data_classification") == "public"
        and observation.get("contains_personal_data") is False
        and observation.get("public_display_approved") is True
        and exhibition.get("public_display_status") == "approved"
        and _verified_source(observation)
    )


def _validate_source_refs(record: dict[str, Any], root: Path, label: str, errors: list[str]) -> None:
    refs = record.get("source_refs", [])
    if not isinstance(refs, list):
        errors.append(f"{label}: source_refs must be a list")
        return
    for offset, ref in enumerate(refs, start=1):
        if not isinstance(ref, dict):
            errors.append(f"{label}: source_refs[{offset}] must be an object")
            continue
        missing = {"source_id", "label", "path", "locator", "verification_status", "public_display_approved"} - ref.keys()
        if missing:
            errors.append(f"{label}: source_refs[{offset}] missing {', '.join(sorted(missing))}")
            continue
        source_path = ref.get("path")
        intentionally_missing = (
            record.get("id") == "m-mesob"
            or record.get("system_id") == "m-mesob"
        ) and (ref.get("source_id"), source_path) in INTENTIONALLY_MISSING_SOURCE_PATHS
        if (
            not isinstance(source_path, str)
            or not (root / source_path).is_file()
        ) and not intentionally_missing:
            errors.append(f"{label}: source path does not exist: {source_path}")
        if ref.get("verification_status") not in {"needs-review", "verified", "conflicting"}:
            errors.append(f"{label}: invalid source verification_status")


def _validate_translation_map(
    translations: Any, label: str, errors: list[str], *, allow_review_drafts: bool = False,
) -> None:
    if not isinstance(translations, dict):
        errors.append(f"{label}: translations must be an object")
        return
    for language, translation in translations.items():
        if language not in {"om", "am"}:
            errors.append(f"{label}: unsupported translation language {language}")
            continue
        if not isinstance(translation, dict):
            errors.append(f"{label}: {language} translation must be an object")
            continue
        approval = translation.get("approval")
        if not isinstance(approval, dict):
            errors.append(f"{label}: {language} translation lacks approval metadata")
            continue
        approved_source = approval.get("approved_source") is True
        human_approved = (
            approval.get("status") == "approved"
            and approval.get("human_reviewed") is True
            and approval.get("reviewer_role") == ("human-amharic-reviewer" if language == "am" else "human-afaan-oromo-reviewer")
        )
        if language == "am" and not (approved_source or human_approved) and not (
            allow_review_drafts and approval.get("status") == "needs-review"
        ):
            errors.append(f"{label}: Amharic translation requires an approved source or an approving human Amharic reviewer")
        if approval.get("status") == "approved" and not (approved_source or human_approved):
            errors.append(f"{label}: approved {language} translation lacks valid approval evidence")


def _validate_definitions(definitions: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    definition_index = _index(definitions, "kpi_code", "KPI definition", errors)
    for definition in definitions:
        label = _record_label("KPI definition", definition, "kpi_code")
        _require(definition, DEFINITION_REQUIRED, label, errors)
        if definition.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label}: unsupported schema_version")
        if definition.get("kpi_category") not in KPI_CATEGORIES:
            errors.append(f"{label}: unsupported KPI category")
        if definition.get("measurement_type") not in MEASUREMENT_TYPES:
            errors.append(f"{label}: unsupported measurement type")
        allowed_operators = definition.get("allowed_operators")
        if not isinstance(allowed_operators, list) or not allowed_operators or set(allowed_operators) - OPERATORS:
            errors.append(f"{label}: invalid allowed_operators")
        allowed_units = definition.get("allowed_units")
        if not isinstance(allowed_units, list) or not allowed_units or any(not isinstance(unit, str) or not unit for unit in allowed_units):
            errors.append(f"{label}: allowed_units must contain canonical unit strings")
        aggregation = definition.get("aggregation")
        if not isinstance(aggregation, dict) or aggregation.get("method") not in AGGREGATION_METHODS:
            errors.append(f"{label}: unsupported aggregation method")
            continue
        method = aggregation["method"]
        if definition.get("measurement_type") == "percentage" and method == "sum":
            errors.append(f"{label}: percentage KPIs cannot use sum aggregation")
        if definition.get("kpi_code") in ACTIVE_USER_CODES and method != "not-aggregatable":
            errors.append(f"{label}: active-user KPIs must be not-aggregatable across systems")
        requirements = definition.get("reporting_requirements")
        if not isinstance(requirements, dict):
            errors.append(f"{label}: reporting_requirements must be an object")
        elif definition.get("kpi_code") in ACTIVE_USER_CODES and requirements.get("activity_window_required") is not True:
            errors.append(f"{label}: active-user KPI must require an activity window")
        elif definition.get("kpi_code") == "response-time" and requirements.get("statistic_required") is not True:
            errors.append(f"{label}: response-time KPI must require a statistic")
        elif definition.get("kpi_code") == "availability-percent" and requirements.get("monitoring_period_required") is not True:
            errors.append(f"{label}: availability KPI must require a monitoring period")
    missing_codes = sorted(REQUIRED_KPI_CODES - definition_index.keys())
    if missing_codes:
        errors.append(f"missing required KPI definitions: {', '.join(missing_codes)}")
    return definition_index


def _validate_measurement(
    observation: dict[str, Any],
    field: str,
    definition: dict[str, Any] | None,
    label: str,
    errors: list[str],
) -> None:
    measurement = observation.get(field)
    if not isinstance(measurement, dict):
        errors.append(f"{label}: {field} must be a separate measurement object")
        return
    missing = {"operator", "value", "unit"} - measurement.keys()
    if missing:
        errors.append(f"{label}: {field} missing {', '.join(sorted(missing))}")
        return
    operator = measurement.get("operator")
    value = measurement.get("value")
    if operator not in OPERATORS:
        errors.append(f"{label}: {field} has unsupported operator")
    if operator == "not-specified" and value is not None:
        errors.append(f"{label}: {field} not-specified operator requires a null value")
    if operator != "not-specified" and value is None:
        errors.append(f"{label}: {field} requires a value for operator {operator}")
    if operator == "range":
        if not isinstance(value, dict) or not isinstance(value.get("minimum"), (int, float)) or not isinstance(value.get("maximum"), (int, float)):
            errors.append(f"{label}: {field} range requires numeric minimum and maximum")
        elif value["minimum"] > value["maximum"]:
            errors.append(f"{label}: {field} range minimum exceeds maximum")
    elif isinstance(value, dict):
        errors.append(f"{label}: {field} object value requires range operator")
    if definition is None:
        return
    if operator not in definition.get("allowed_operators", []):
        errors.append(f"{label}: {field} operator is not allowed by {definition.get('kpi_code')}")
    unit = measurement.get("unit")
    if unit is not None and unit not in definition.get("allowed_units", []):
        errors.append(f"{label}: {field} unit {unit} is not allowed by {definition.get('kpi_code')}")
    numbers = _numeric_values(measurement)
    if definition.get("value_type") == "integer" and any(not number.is_integer() for number in numbers):
        errors.append(f"{label}: {field} requires integer values")
    if definition.get("value_type") == "integer" and any(number < 0 for number in numbers):
        errors.append(f"{label}: negative count in {field}")
    if definition.get("measurement_type") == "percentage" or unit == "percent":
        if any(number < 0 or number > 100 for number in numbers):
            errors.append(f"{label}: percentage in {field} must be between 0 and 100")


def _validate_observations(
    observations: list[dict[str, Any]],
    system_index: dict[str, dict[str, Any]],
    definition_index: dict[str, dict[str, Any]],
    root: Path,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    observation_index = _index(observations, "id", "KPI observation", errors)
    for observation in observations:
        label = _record_label("KPI observation", observation, "id")
        _require(observation, OBSERVATION_REQUIRED, label, errors)
        system_id = observation.get("system_id")
        kpi_code = observation.get("kpi_code")
        if system_id not in system_index:
            errors.append(f"{label}: unknown system_id {system_id}")
        definition = definition_index.get(kpi_code)
        if definition is None:
            errors.append(f"{label}: unknown kpi_code {kpi_code}")
        if observation.get("actual") is observation.get("baseline") or observation.get("actual") is observation.get("target") or observation.get("baseline") is observation.get("target"):
            errors.append(f"{label}: actual, baseline, and target must be separate objects")
        for field in ("actual", "baseline", "target"):
            _validate_measurement(observation, field, definition, label, errors)
        reporting_period = observation.get("reporting_period")
        if not isinstance(reporting_period, dict):
            errors.append(f"{label}: reporting_period must be an object")
        else:
            _require(reporting_period, {"type", "start_date", "end_date", "reporting_date_text", "calendar_type"}, f"{label} reporting_period", errors)
            if reporting_period.get("type") not in REPORTING_PERIOD_TYPES:
                errors.append(f"{label}: unsupported reporting-period type")
        measurement_method = observation.get("measurement_method")
        if not isinstance(measurement_method, dict):
            errors.append(f"{label}: measurement_method must be an object")
        else:
            _require(measurement_method, {"method", "description", "data_owner", "update_frequency"}, f"{label} measurement_method", errors)
        quality = observation.get("data_quality")
        if not isinstance(quality, dict):
            errors.append(f"{label}: data_quality must be an object")
        else:
            _require(quality, {"completeness", "accuracy_status", "duplicate_risk", "limitations"}, f"{label} data_quality", errors)
            for key in ("completeness", "accuracy_status", "duplicate_risk"):
                if quality.get(key) not in DATA_QUALITY_VALUES:
                    errors.append(f"{label}: unsupported data-quality value for {key}")
        exhibition = observation.get("exhibition")
        if not isinstance(exhibition, dict):
            errors.append(f"{label}: exhibition must be an object")
        else:
            _require(exhibition, {"headline", "display_priority", "public_display_status", "chart_type", "show_reporting_date", "show_source_label"}, f"{label} exhibition", errors)
        dimensions = observation.get("dimensions")
        if not isinstance(dimensions, dict):
            errors.append(f"{label}: dimensions must be an object")
            dimensions = {}
        _validate_source_refs(observation, root, label, errors)
        if kpi_code == "response-time":
            unit = (observation.get("actual") or {}).get("unit")
            if unit not in DURATION_UNITS:
                errors.append(f"{label}: response-time requires a duration unit")
            if not dimensions.get("statistic"):
                errors.append(f"{label}: response-time requires a statistic dimension")
        if kpi_code == "availability-percent" and not _has_window(dimensions.get("monitoring_period")):
            errors.append(f"{label}: availability requires a monitoring period")
        if kpi_code in ACTIVE_USER_CODES and not _has_window(dimensions.get("activity_window")):
            errors.append(f"{label}: active-user KPI requires an activity window")
        if definition and definition.get("aggregation", {}).get("method") == "count-unique":
            entity_ids = dimensions.get("entity_ids")
            actual = observation.get("actual") or {}
            if entity_ids is not None and actual.get("operator") == "equal" and isinstance(actual.get("value"), int) and actual.get("value") != len(entity_ids):
                errors.append(f"{label}: equal count does not match unique entity_ids")
        if observation.get("publication_status") == "published":
            if observation.get("verification_status") != "verified" or not _verified_source(observation):
                errors.append(f"{label}: published KPI requires a verified source")
            if (
                not isinstance(reporting_period, dict)
                or reporting_period.get("type") in (None, "unknown")
                or not any(
                    reporting_period.get(field)
                    for field in ("start_date", "end_date", "reporting_date_text")
                )
            ):
                errors.append(f"{label}: published KPI requires a reporting period")
            actual = observation.get("actual") or {}
            if actual.get("unit") in (None, ""):
                errors.append(f"{label}: published KPI requires a unit")
            if actual.get("operator") == "not-specified" or actual.get("value") is None:
                errors.append(f"{label}: published KPI requires an actual value")
            if PLACEHOLDER_RE.search(_canonical(observation)):
                errors.append(f"{label}: published KPI contains placeholder text")
            if observation.get("verification_status") == "conflicting" or (isinstance(quality, dict) and quality.get("accuracy_status") == "conflicting"):
                errors.append(f"{label}: published KPI cannot be marked conflicting")
        if observation.get("public_display_approved") is True or (isinstance(exhibition, dict) and exhibition.get("public_display_status") == "approved"):
            if observation.get("contains_personal_data") is not False:
                errors.append(f"{label}: public exhibition output cannot contain personal data")
            if observation.get("data_classification") != "public":
                errors.append(f"{label}: public exhibition output requires public data_classification")
            if (
                isinstance(exhibition, dict)
                and exhibition.get("show_source_label") is True
                and not any(
                    isinstance(ref, dict)
                    and ref.get("verification_status") == "verified"
                    and ref.get("public_display_approved") is True
                    for ref in observation.get("source_refs", [])
                )
            ):
                errors.append(f"{label}: public source label requires a verified, display-approved source")
        display_value = observation.get("display_value")
        if display_value is not None and definition is not None:
            expected = format_observation_value(observation, definition)
            if display_value != expected:
                errors.append(f"{label}: display_value must equal the canonical rendering or be null")
    for observation in observations:
        superseded_id = observation.get("supersedes_observation_id")
        if superseded_id is None:
            continue
        label = _record_label("KPI observation", observation, "id")
        superseded = observation_index.get(superseded_id)
        if superseded is None:
            errors.append(f"{label}: supersedes unknown observation {superseded_id}")
        elif superseded_id == observation.get("id"):
            errors.append(f"{label}: observation cannot supersede itself")
        elif (superseded.get("system_id"), superseded.get("kpi_code")) != (observation.get("system_id"), observation.get("kpi_code")):
            errors.append(f"{label}: superseded observation must use the same system_id and kpi_code")
    _validate_unresolved_conflicts(observations, errors)
    return observation_index


def _series_identity(observation: dict[str, Any]) -> str:
    return _canonical(
        {
            "system_id": observation.get("system_id"),
            "kpi_code": observation.get("kpi_code"),
            "measurement_scope": observation.get("measurement_scope"),
            "reporting_period": observation.get("reporting_period"),
            "dimensions": observation.get("dimensions"),
        }
    )


def _validate_unresolved_conflicts(observations: list[dict[str, Any]], errors: list[str]) -> None:
    eligible = [observation for observation in observations if is_verified_public_observation(observation)]
    superseded = {observation.get("supersedes_observation_id") for observation in eligible if observation.get("supersedes_observation_id")}
    groups: dict[str, list[dict[str, Any]]] = {}
    for observation in eligible:
        if observation.get("id") not in superseded:
            groups.setdefault(_series_identity(observation), []).append(observation)
    for group in groups.values():
        if len(group) > 1:
            ids = ", ".join(sorted(observation["id"] for observation in group))
            errors.append(f"unresolved conflicting observations require explicit supersession: {ids}")


def _validate_stories(
    stories: list[dict[str, Any]],
    system_index: dict[str, dict[str, Any]],
    observation_index: dict[str, dict[str, Any]],
    root: Path,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    story_index = _index(stories, "id", "transformation story", errors)
    for story in stories:
        label = _record_label("transformation story", story, "id")
        _require(story, STORY_REQUIRED, label, errors)
        if story.get("system_id") not in system_index:
            errors.append(f"{label}: unknown system_id {story.get('system_id')}")
        dimensions = story.get("transformation_dimensions")
        if not isinstance(dimensions, list) or not dimensions or set(dimensions) - TRANSFORMATION_DIMENSIONS:
            errors.append(f"{label}: unsupported transformation dimension")
        refs = story.get("kpi_observation_refs")
        if not isinstance(refs, list):
            errors.append(f"{label}: kpi_observation_refs must be a list")
        else:
            for ref in refs:
                observation = observation_index.get(ref)
                if observation is None:
                    errors.append(f"{label}: unknown KPI observation reference {ref}")
                elif observation.get("system_id") != story.get("system_id"):
                    errors.append(f"{label}: KPI observation {ref} belongs to a different system")
        _validate_source_refs(story, root, label, errors)
        _validate_translation_map(story.get("translations"), label, errors)
        _validate_numeric_narrative(story, refs or [], observation_index, label, errors, story_record=True)
    return story_index


def _validate_faqs(
    faqs: list[dict[str, Any]],
    system_index: dict[str, dict[str, Any]],
    observation_index: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    faq_index = _index(faqs, "id", "FAQ", errors)
    for faq in faqs:
        label = _record_label("FAQ", faq, "id")
        _require(faq, FAQ_REQUIRED, label, errors)
        if faq.get("system_id") not in system_index:
            errors.append(f"{label}: unknown system_id {faq.get('system_id')}")
        refs = faq.get("kpi_observation_refs")
        if not isinstance(refs, list):
            errors.append(f"{label}: kpi_observation_refs must be a list")
            refs = []
        for ref in refs:
            observation = observation_index.get(ref)
            if observation is None:
                errors.append(f"{label}: unknown KPI observation reference {ref}")
            elif observation.get("system_id") != faq.get("system_id"):
                errors.append(f"{label}: KPI observation {ref} belongs to a different system")
        answer = faq.get("answer")
        if isinstance(answer, str):
            tokens = set(KPI_TOKEN_RE.findall(answer))
            unknown_tokens = sorted(tokens - set(refs))
            if unknown_tokens:
                errors.append(f"{label}: answer uses unlisted KPI tokens: {', '.join(unknown_tokens)}")
        _validate_translation_map(faq.get("translations"), label, errors, allow_review_drafts=True)
        for language, translation in (faq.get("translations") or {}).items():
            if not isinstance(translation, dict):
                continue
            for field in ("question", "answer"):
                value = translation.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{label}: {language} {field} must be nonempty text")
                    continue
                tokens = {match.group(1) for match in LOCALIZED_KPI_TOKEN_RE.finditer(value)}
                if tokens - set(refs):
                    errors.append(f"{label}: {language} {field} uses unlisted KPI tokens")
                remainder = LOCALIZED_KPI_TOKEN_RE.sub("", value)
                if "{{" in remainder or "}}" in remainder:
                    errors.append(f"{label}: {language} {field} contains malformed KPI tokens")
                if NUMBER_RE.search(remainder):
                    errors.append(f"{label}: {language} numeric FAQ claims must use a KPI observation token")
            labels = translation.get("kpi_unit_labels", {})
            if not isinstance(labels, dict) or any(
                ref not in refs or not isinstance(value, str) or not value.strip()
                for ref, value in labels.items()
            ):
                errors.append(f"{label}: {language} kpi_unit_labels must map referenced observations to nonempty labels")
        _validate_numeric_narrative(faq, refs, observation_index, label, errors, faq_record=True)
        if faq.get("public_display_approved") is True:
            if faq.get("contains_personal_data") is not False:
                errors.append(f"{label}: public exhibition output cannot contain personal data")
            if faq.get("data_classification") != "public":
                errors.append(f"{label}: public exhibition output requires public data_classification")
            for ref in refs:
                observation = observation_index.get(ref)
                if observation is not None and not is_verified_public_observation(observation):
                    errors.append(f"{label}: public FAQ references non-public or unverified KPI observation {ref}")
    return faq_index


def _narrative_strings(record: dict[str, Any], *, faq_record: bool = False, story_record: bool = False) -> list[str]:
    if faq_record:
        return [str(record.get("question", "")), str(record.get("answer", ""))]
    if story_record:
        values = [record.get("title", ""), record.get("summary", "")]
        for key in ("before", "after", "user_impact"):
            section = record.get(key)
            if isinstance(section, dict):
                values.extend(value for value in section.values() if isinstance(value, str))
                values.extend(item for value in section.values() if isinstance(value, list) for item in value if isinstance(item, str))
        return [str(value) for value in values]
    values = [record.get("purpose", "")]
    for service in record.get("services_digitized", []):
        if isinstance(service, dict):
            values.extend([service.get("name", ""), service.get("description", "")])
    return [str(value) for value in values]


def _number_forms(value: float, unit: str | None) -> set[str]:
    forms: set[str] = set()
    if value.is_integer():
        integer = int(value)
        forms.update({str(integer), f"{integer:,}"})
    else:
        forms.add(str(value))
    if unit == "percent":
        forms.update({f"{form}%" for form in tuple(forms)})
    for divisor, suffix in ((1_000_000_000, "billion"), (1_000_000, "million"), (1_000, "thousand")):
        scaled = value / divisor
        if scaled >= 1 and math.isclose(scaled, round(scaled, 1)):
            forms.add(f"{scaled:g} {suffix}")
    return {form.lower() for form in forms if form}


def _validate_numeric_narrative(
    record: dict[str, Any],
    refs: list[str],
    observation_index: dict[str, dict[str, Any]],
    label: str,
    errors: list[str],
    *,
    faq_record: bool = False,
    story_record: bool = False,
) -> None:
    referenced_forms: set[str] = set()
    for ref in refs:
        observation = observation_index.get(ref)
        if observation is None:
            continue
        actual = observation.get("actual") or {}
        for value in _numeric_values(actual):
            referenced_forms.update(_number_forms(value, actual.get("unit")))
    for text in _narrative_strings(record, faq_record=faq_record, story_record=story_record):
        text_without_tokens = KPI_TOKEN_RE.sub("", text).lower()
        if referenced_forms and any(form in text_without_tokens for form in referenced_forms):
            message = (
                "numeric FAQ claims must use a KPI observation token"
                if faq_record
                else "narrative duplicates an authoritative KPI value; use an observation reference"
            )
            errors.append(f"{label}: {message}")
            break
        if faq_record and NUMBER_RE.search(text_without_tokens):
            errors.append(f"{label}: numeric FAQ claims must use a KPI observation token")
            break


def _validate_systems(
    systems: list[dict[str, Any]],
    observation_index: dict[str, dict[str, Any]],
    story_index: dict[str, dict[str, Any]],
    faq_index: dict[str, dict[str, Any]],
    root: Path,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    system_index = _index(systems, "id", "digital system", errors)
    for system in systems:
        label = _record_label("digital system", system, "id")
        _require(system, SYSTEM_REQUIRED, label, errors)
        headline_refs = system.get("headline_kpi_refs")
        if not isinstance(headline_refs, list):
            errors.append(f"{label}: headline_kpi_refs must be a list")
            headline_refs = []
        for ref in headline_refs:
            observation = observation_index.get(ref)
            if observation is None:
                errors.append(f"{label}: unknown headline KPI observation {ref}")
            elif observation.get("system_id") != system.get("id"):
                errors.append(f"{label}: headline KPI observation {ref} belongs to a different system")
        for field, index, kind in (
            ("transformation_story_refs", story_index, "transformation story"),
            ("faq_refs", faq_index, "FAQ"),
        ):
            refs = system.get(field)
            if not isinstance(refs, list):
                errors.append(f"{label}: {field} must be a list")
                continue
            for ref in refs:
                if ref not in index:
                    errors.append(f"{label}: unknown {kind} reference {ref}")
        _validate_source_refs(system, root, label, errors)
        _validate_translation_map(system.get("translations"), label, errors)
        system_observation_refs = [
            observation_id
            for observation_id, observation in observation_index.items()
            if observation.get("system_id") == system.get("id")
        ]
        _validate_numeric_narrative(system, system_observation_refs, observation_index, label, errors)
        if system.get("publication_status") == "published":
            has_verified = any(
                ref in observation_index and is_verified_public_observation(observation_index[ref])
                for ref in headline_refs
            )
            exception = system.get("kpi_data_unavailable_exception")
            exception_approved = (
                isinstance(exception, dict)
                and exception.get("approved") is True
                and isinstance(exception.get("approved_by_role"), str)
                and exception.get("approved_by_role")
                and exception.get("approval_date")
            )
            if not has_verified and not exception_approved:
                errors.append(f"{label}: published digital system requires a verified KPI or publisher-approved data-unavailable exception")
    return system_index


def _validate_portfolio(
    portfolio_kpis: list[dict[str, Any]],
    definition_index: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    portfolio_index = _index(portfolio_kpis, "id", "portfolio KPI", errors)
    for config in portfolio_kpis:
        label = _record_label("portfolio KPI", config, "id")
        _require(config, PORTFOLIO_REQUIRED, label, errors)
        definition = definition_index.get(config.get("kpi_code"))
        if definition is None:
            errors.append(f"{label}: unknown kpi_code {config.get('kpi_code')}")
            continue
        method = config.get("aggregation_method")
        if method not in AGGREGATION_METHODS:
            errors.append(f"{label}: unsupported aggregation method")
        if method != definition.get("aggregation", {}).get("method"):
            errors.append(f"{label}: aggregation method differs from KPI catalog")
        if definition.get("measurement_type") == "percentage" and method == "sum":
            errors.append(f"{label}: percentage KPIs cannot use sum aggregation")
        if config.get("kpi_code") in ACTIVE_USER_CODES and method != "not-aggregatable":
            errors.append(f"{label}: active-user values cannot be added across systems")
    missing = sorted(REQUIRED_PORTFOLIO_IDS - portfolio_index.keys())
    if missing:
        errors.append(f"missing required portfolio KPI configurations: {', '.join(missing)}")
    return portfolio_index


def validate_records(data: RepositoryData, root: Path) -> None:
    errors: list[str] = []
    definition_index = _validate_definitions(data.definitions, errors)
    provisional_system_index = _index(data.systems, "id", "digital system", errors)
    observation_index = _validate_observations(data.observations, provisional_system_index, definition_index, root, errors)
    story_index = _validate_stories(data.stories, provisional_system_index, observation_index, root, errors)
    faq_index = _validate_faqs(data.faqs, provisional_system_index, observation_index, errors)
    _validate_systems(data.systems, observation_index, story_index, faq_index, root, errors)
    _validate_portfolio(data.portfolio_kpis, definition_index, errors)
    for schema_name in (
        "digital-system.schema.json",
        "kpi-definition.schema.json",
        "kpi-observation.schema.json",
        "portfolio-kpi.schema.json",
        "transformation-story.schema.json",
        "faq.schema.json",
    ):
        path = root / "schemas" / schema_name
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"{path}: schema must declare JSON Schema draft 2020-12")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid or missing JSON schema: {exc}")
    if errors:
        raise ValidationFailure(errors)


def _history_path(root: Path) -> Path:
    return root / "content" / "kpi-observations" / "observation-history.json"


def _load_history(root: Path) -> dict[str, Any]:
    path = _history_path(root)
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "algorithm": "sha256-canonical-json", "observations": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("observations"), dict):
        raise ValidationFailure([f"{path}: invalid observation history lock"])
    return payload


def check_observation_history(data: RepositoryData, root: Path, *, accept_new: bool = False) -> dict[str, Any]:
    history = _load_history(root)
    locked = history["observations"]
    current = {observation["id"]: observation_hash(observation) for observation in data.observations if isinstance(observation.get("id"), str)}
    errors: list[str] = []
    for observation_id, expected_hash in locked.items():
        if observation_id not in current:
            errors.append(f"historical KPI observation was removed: {observation_id}")
        elif current[observation_id] != expected_hash:
            errors.append(f"historical KPI observation was overwritten: {observation_id}; add a new observation that explicitly supersedes it")
    new_ids = sorted(current.keys() - locked.keys())
    if new_ids and not accept_new:
        errors.append(f"new KPI observations are not history-locked: {', '.join(new_ids)}; run accept-new-observations after review")
    if errors:
        raise ValidationFailure(errors)
    if accept_new:
        updated = copy.deepcopy(history)
        updated["schema_version"] = SCHEMA_VERSION
        updated["algorithm"] = "sha256-canonical-json"
        for observation_id in new_ids:
            updated["observations"][observation_id] = current[observation_id]
        updated["observations"] = dict(sorted(updated["observations"].items()))
        return updated
    return history


def validate_repository(root: Path, *, check_history: bool = True) -> RepositoryData:
    data = load_repository(root)
    validate_records(data, root)
    if check_history:
        check_observation_history(data, root)
    return data


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _format_number(value: Any, decimals: int) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) or isinstance(value, float) and value.is_integer() and decimals == 0:
        return f"{int(value):,}"
    if isinstance(value, (int, float)):
        return f"{value:,.{decimals}f}"
    return str(value)


def format_observation_value(observation: dict[str, Any], definition: dict[str, Any]) -> str:
    actual = observation.get("actual") or {}
    operator = actual.get("operator")
    value = actual.get("value")
    unit = actual.get("unit")
    decimals = int((definition.get("display") or {}).get("decimal_places", 0))
    if operator == "not-specified" or value is None:
        return "Not specified"
    if operator == "range" and isinstance(value, dict):
        rendered = f"{_format_number(value.get('minimum'), decimals)}–{_format_number(value.get('maximum'), decimals)}"
    else:
        rendered = _format_number(value, decimals)
    prefix = {
        "equal": "",
        "greater-than": "> ",
        "greater-than-or-equal": "≥ ",
        "less-than": "< ",
        "less-than-or-equal": "≤ ",
        "approximate": "≈ ",
        "range": "",
    }.get(operator, "")
    if unit == "percent":
        return f"{prefix}{rendered}%"
    unit_label = (definition.get("display") or {}).get("unit_label") or unit or ""
    return f"{prefix}{rendered} {unit_label}".strip()


def render_localized_faq(
    translation: dict[str, Any], observations: dict[str, dict[str, Any]],
    definitions: dict[str, dict[str, Any]], *, require_localized_units: bool = False,
) -> dict[str, Any]:
    """Resolve approved templates, preserving their prose and exact KPI operators.

    A number token is appropriate only where approved prose already states the unit.
    Full tokens require an approved unit label in the chatbot export; the legacy
    avatar contract retains its canonical-unit fallback for compatibility.
    """
    result = copy.deepcopy(translation)

    def replace(match: re.Match[str]) -> str:
        ref, number_only = match.groups()
        observation = observations[ref]
        definition = copy.deepcopy(definitions[observation["kpi_code"]])
        actual = observation["actual"]
        if number_only:
            numeric = copy.deepcopy(observation)
            numeric["actual"]["unit"] = None
            definition.setdefault("display", {})["unit_label"] = ""
            return format_observation_value(numeric, definition)
        unit_label = translation.get("kpi_unit_labels", {}).get(ref)
        if unit_label:
            definition.setdefault("display", {})["unit_label"] = unit_label
        elif require_localized_units and actual.get("unit") != "percent":
            raise ValidationFailure([f"{ref}: approved localized KPI unit label required"])
        return format_observation_value(observation, definition)

    for field in ("question", "answer"):
        if field in result:
            result[field] = LOCALIZED_KPI_TOKEN_RE.sub(replace, result[field])
    result.pop("kpi_unit_labels", None)
    return result


def _public_source_labels(observation: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"source_id": ref["source_id"], "label": ref["label"], "locator": ref["locator"]}
        for ref in observation.get("source_refs", [])
        if ref.get("verification_status") == "verified" and ref.get("public_display_approved") is True
    ]


def _public_dimensions(dimensions: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "platform",
        "service_channel",
        "geography_level",
        "geography_name",
        "statistic",
        "activity_window",
        "monitoring_period",
    }
    return {key: copy.deepcopy(value) for key, value in dimensions.items() if key in allowed}


def _public_observation(observation: dict[str, Any], definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": observation["id"],
        "record_version": observation["record_version"],
        "system_id": observation["system_id"],
        "kpi_code": observation["kpi_code"],
        "kpi_name": definition["name"],
        "measurement_scope": copy.deepcopy(observation["measurement_scope"]),
        "actual": copy.deepcopy(observation["actual"]),
        "baseline": copy.deepcopy(observation["baseline"]),
        "target": copy.deepcopy(observation["target"]),
        "achievement": copy.deepcopy(observation["achievement"]),
        "reporting_period": copy.deepcopy(observation["reporting_period"]),
        "dimensions": _public_dimensions(observation.get("dimensions", {})),
        "display_value": format_observation_value(observation, definition),
        "source_labels": _public_source_labels(observation),
        "exhibition": copy.deepcopy(observation["exhibition"]),
    }


def _approved_translation_entries(record_type: str, record: dict[str, Any], language: str) -> list[dict[str, Any]]:
    translation = (record.get("translations") or {}).get(language)
    if not isinstance(translation, dict):
        return []
    approval = translation.get("approval") or {}
    if approval.get("status") != "approved":
        return []
    if not (approval.get("approved_source") is True or approval.get("human_reviewed") is True):
        return []
    content = {key: value for key, value in translation.items() if key != "approval"}
    return [{"record_type": record_type, "record_id": record["id"], "language": language, "content": content}]


def _public_system(
    system: dict[str, Any],
    safe_headlines: set[str],
    safe_story_ids: set[str],
    safe_faq_ids: set[str],
) -> dict[str, Any]:
    return {
        "id": system["id"],
        "slug": system["slug"],
        "official_name": system["official_name"],
        "acronym": system["acronym"],
        "category": system["category"],
        "subcategories": copy.deepcopy(system["subcategories"]),
        "lifecycle_status": system["lifecycle_status"],
        "organization": copy.deepcopy(system["organization"]),
        "system_classification": copy.deepcopy(system["system_classification"]),
        "purpose": system["purpose"],
        "beneficiaries": copy.deepcopy(system["beneficiaries"]),
        "services_digitized": copy.deepcopy(system["services_digitized"]),
        "integrations": [copy.deepcopy(item) for item in system["integrations"] if item.get("public_display_approved") is True],
        "geographic_coverage": copy.deepcopy(system["geographic_coverage"]),
        "headline_kpi_refs": [ref for ref in system["headline_kpi_refs"] if ref in safe_headlines],
        "transformation_story_refs": [ref for ref in system["transformation_story_refs"] if ref in safe_story_ids],
        "faq_refs": [ref for ref in system["faq_refs"] if ref in safe_faq_ids],
        "media": [copy.deepcopy(item) for item in system["media"] if item.get("public_display_approved") is True],
    }


def _period_key(observation: dict[str, Any]) -> str:
    return _canonical(observation.get("reporting_period"))


def _matches_config(observation: dict[str, Any], system: dict[str, Any], config: dict[str, Any]) -> bool:
    if observation.get("kpi_code") != config.get("kpi_code"):
        return False
    filters = config.get("filters") or {}
    categories = filters.get("system_categories") or []
    if categories and system.get("category") not in categories:
        return False
    system_types = filters.get("system_types") or []
    primary_type = (system.get("system_classification") or {}).get("primary_type")
    if system_types and primary_type not in system_types:
        return False
    dimensions = observation.get("dimensions") or {}
    return all(dimensions.get(key) == value for key, value in (filters.get("dimensions") or {}).items())


def _series_item(observation: dict[str, Any], definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "observation_id": observation["id"],
        "system_id": observation["system_id"],
        "actual": copy.deepcopy(observation["actual"]),
        "display_value": format_observation_value(observation, definition),
        "reporting_period": copy.deepcopy(observation["reporting_period"]),
    }


def _portfolio_metric(
    config: dict[str, Any],
    observations: list[dict[str, Any]],
    systems: dict[str, dict[str, Any]],
    definition: dict[str, Any],
) -> dict[str, Any] | None:
    selected = [
        observation
        for observation in observations
        if observation["system_id"] in systems and _matches_config(observation, systems[observation["system_id"]], config)
    ]
    if not selected:
        return None
    selected.sort(key=lambda item: item["id"])
    method = config["aggregation_method"]
    metric: dict[str, Any] = {
        "id": config["id"],
        "name": config["name"],
        "kpi_code": config["kpi_code"],
        "aggregation_method": method,
        "observation_ids": [item["id"] for item in selected],
        "series": [_series_item(item, definition) for item in selected],
    }
    exact = [item for item in selected if item["actual"].get("operator") == "equal" and isinstance(item["actual"].get("value"), (int, float)) and not isinstance(item["actual"].get("value"), bool)]
    if len(exact) != len(selected):
        metric["aggregation_status"] = "series-only-non-exact-values"
        return metric
    units = {item["actual"].get("unit") for item in exact}
    if len(units) != 1:
        metric["aggregation_status"] = "series-only-incompatible-units"
        return metric
    if method == "not-aggregatable" or method == "latest":
        metric["aggregation_status"] = "series-only"
        return metric
    if method == "count-unique":
        entity_lists = [(item.get("dimensions") or {}).get("entity_ids") for item in exact]
        if any(not isinstance(entity_ids, list) or not entity_ids for entity_ids in entity_lists):
            metric["aggregation_status"] = "series-only-missing-deduplication-keys"
            return metric
        value = len({entity_id for entity_ids in entity_lists for entity_id in entity_ids})
    else:
        periods = {_period_key(item) for item in exact}
        partitions = [(item.get("dimensions") or {}).get("aggregation_partition") for item in exact]
        if len(periods) != 1:
            metric["aggregation_status"] = "series-only-unaligned-periods"
            return metric
        if any(not partition for partition in partitions) or len(set(partitions)) != len(partitions):
            metric["aggregation_status"] = "series-only-unsafe-partitions"
            return metric
        values = [float(item["actual"]["value"]) for item in exact]
        if method == "sum":
            value = sum(values)
        elif method == "weighted-average":
            weights = [(item.get("dimensions") or {}).get("aggregation_weight") for item in exact]
            if any(not isinstance(weight, (int, float)) or weight <= 0 for weight in weights):
                metric["aggregation_status"] = "series-only-missing-weights"
                return metric
            value = sum(item * weight for item, weight in zip(values, weights, strict=True)) / sum(weights)
        elif method == "average":
            value = sum(values) / len(values)
        elif method == "minimum":
            value = min(values)
        elif method == "maximum":
            value = max(values)
        else:
            metric["aggregation_status"] = "series-only"
            return metric
    if definition.get("measurement_type") == "percentage" and method == "sum":
        raise AssertionError("percentage aggregation reached sum")
    decimals = int((definition.get("display") or {}).get("decimal_places", 0))
    if decimals == 0 and float(value).is_integer():
        value = int(value)
    metric.update(
        {
            "aggregation_status": "aggregated",
            "value": value,
            "unit": next(iter(units)),
            "display_value": format_observation_value(
                {"actual": {"operator": "equal", "value": value, "unit": next(iter(units))}},
                definition,
            ),
        }
    )
    return metric


def _current_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    superseded = {item.get("supersedes_observation_id") for item in observations if item.get("supersedes_observation_id")}
    return [item for item in observations if item.get("id") not in superseded]


def build_payloads(data: RepositoryData) -> dict[str, Any]:
    definitions = {item["kpi_code"]: item for item in data.definitions}
    published_systems = {item["id"]: item for item in data.systems if item.get("publication_status") == "published"}
    safe_observations = _current_observations(
        [
            item
            for item in data.observations
            if is_verified_public_observation(item) and item.get("system_id") in published_systems
        ]
    )
    safe_ids = {item["id"] for item in safe_observations}
    safe_story_ids = {
        story["id"]
        for story in data.stories
        if story.get("publication_status") == "published"
        and story.get("verification_status") == "verified"
        and story.get("public_display_approved") is True
        and story.get("system_id") in published_systems
        and all(ref in safe_ids for ref in story.get("kpi_observation_refs", []))
        and any(
            source.get("verification_status") == "verified"
            and source.get("public_display_approved") is True
            for source in story.get("source_refs", [])
        )
    }
    safe_faq_ids = {
        faq["id"]
        for faq in data.faqs
        if faq.get("publication_status") == "published"
        and faq.get("workflow", {}).get("state") == "approved"
        and faq.get("public_display_approved") is True
        and faq.get("data_classification") == "public"
        and faq.get("contains_personal_data") is False
        and faq.get("system_id") in published_systems
        and all(ref in safe_ids for ref in faq.get("kpi_observation_refs", []))
    }
    public_systems = [
        _public_system(system, safe_ids, safe_story_ids, safe_faq_ids)
        for system in sorted(published_systems.values(), key=lambda item: item["id"])
    ]
    public_observations = [
        _public_observation(item, definitions[item["kpi_code"]])
        for item in sorted(safe_observations, key=lambda item: item["id"])
    ]
    system_kpis = []
    for system in public_systems:
        observations = [item for item in public_observations if item["system_id"] == system["id"]]
        system_kpis.append({"system_id": system["id"], "headline_kpi_refs": system["headline_kpi_refs"], "observations": observations})
    supported_metrics = [
        {
            "id": config["id"],
            "name": config["name"],
            "kpi_code": config["kpi_code"],
            "aggregation_method": config["aggregation_method"],
            "display": copy.deepcopy(config["display"]),
        }
        for config in sorted(data.portfolio_kpis, key=lambda item: item["display"]["order"])
        if config.get("status") == "active"
    ]
    metrics = []
    for config in sorted(data.portfolio_kpis, key=lambda item: item["display"]["order"]):
        if config.get("status") != "active":
            continue
        metric = _portfolio_metric(config, safe_observations, published_systems, definitions[config["kpi_code"]])
        if metric is not None:
            metrics.append(metric)
    published_faqs: list[dict[str, Any]] = []
    for faq in sorted(data.faqs, key=lambda item: item["id"]):
        refs = faq.get("kpi_observation_refs", [])
        if (
            faq.get("publication_status") == "published"
            and faq.get("workflow", {}).get("state") == "approved"
            and faq.get("public_display_approved") is True
            and faq.get("data_classification") == "public"
            and faq.get("contains_personal_data") is False
            and faq.get("system_id") in published_systems
            and all(ref in safe_ids for ref in refs)
        ):
            answer = faq["answer"]
            for ref in refs:
                observation = next(item for item in safe_observations if item["id"] == ref)
                answer = answer.replace(f"{{{{kpi:{ref}}}}}", format_observation_value(observation, definitions[observation["kpi_code"]]))
            published_faqs.append(
                {
                    "id": faq["id"],
                    "system_id": faq["system_id"],
                    "question": faq["question"],
                    "answer": answer,
                    "kpi_observation_refs": copy.deepcopy(refs),
                }
            )
    om_content: list[dict[str, Any]] = []
    am_content: list[dict[str, Any]] = []
    for system in published_systems.values():
        om_content.extend(_approved_translation_entries("digital-system", system, "om"))
        am_content.extend(_approved_translation_entries("digital-system", system, "am"))
    for faq in data.faqs:
        if any(item["id"] == faq.get("id") for item in published_faqs):
            rendered_faq = copy.deepcopy(faq)
            for language, translation in faq.get("translations", {}).items():
                rendered_faq["translations"][language] = render_localized_faq(
                    translation, {item["id"]: item for item in safe_observations}, definitions,
                )
            om_content.extend(_approved_translation_entries("faq", rendered_faq, "om"))
            am_content.extend(_approved_translation_entries("faq", rendered_faq, "am"))
    reporting_dates = [
        {"observation_id": item["id"], "reporting_period": copy.deepcopy(item["reporting_period"])}
        for item in sorted(safe_observations, key=lambda item: item["id"])
        if item.get("exhibition", {}).get("show_reporting_date") is True
    ]
    source_labels: dict[tuple[str, str, str], dict[str, str]] = {}
    for observation in safe_observations:
        if observation.get("exhibition", {}).get("show_source_label") is not True:
            continue
        for source in _public_source_labels(observation):
            source_labels[(source["source_id"], source["label"], source["locator"])] = source
    headline_refs = [
        {"system_id": system["id"], "observation_id": ref}
        for system in public_systems
        for ref in system["headline_kpi_refs"]
    ]
    return {
        "digital-systems.json": {"schema_version": SCHEMA_VERSION, "digital_systems": public_systems},
        "system-kpis.json": {"schema_version": SCHEMA_VERSION, "systems": system_kpis},
        "portfolio-dashboard.json": {
            "schema_version": SCHEMA_VERSION,
            "supported_metrics": supported_metrics,
            "metrics": metrics,
            "source_observation_ids": sorted(safe_ids),
        },
        "avatar-facts.json": {
            "published_digital_systems": public_systems,
            "published_faqs": published_faqs,
            "verified_public_kpi_observations": public_observations,
            "approved_afaan_oromo_content": sorted(om_content, key=lambda item: (item["record_type"], item["record_id"])),
            "approved_amharic_content": sorted(am_content, key=lambda item: (item["record_type"], item["record_id"])),
            "reporting_dates": reporting_dates,
            "source_labels": [source_labels[key] for key in sorted(source_labels)],
            "headline_kpi_references": headline_refs,
        },
    }


def _assert_disclosure_safe(payloads: dict[str, Any]) -> None:
    avatar = payloads["avatar-facts.json"]
    allowed_avatar_keys = {
        "published_digital_systems",
        "published_faqs",
        "verified_public_kpi_observations",
        "approved_afaan_oromo_content",
        "approved_amharic_content",
        "reporting_dates",
        "source_labels",
        "headline_kpi_references",
    }
    if set(avatar) != allowed_avatar_keys:
        raise ValidationFailure(["avatar-facts.json contains fields outside the disclosure allowlist"])
    serialized = _canonical(payloads)
    if '"data_classification":"internal"' in serialized or '"data_classification":"confidential"' in serialized or '"data_classification":"restricted"' in serialized:
        raise ValidationFailure(["public build output contains non-public data classification"])
    if '"contains_personal_data":true' in serialized:
        raise ValidationFailure(["public build output contains personal data"])
    if "source-materials/" in serialized:
        raise ValidationFailure(["public build output exposes an internal source path"])


def build_repository(root: Path) -> dict[str, Any]:
    data = validate_repository(root)
    payloads = build_payloads(data)
    _assert_disclosure_safe(payloads)
    for filename, payload in payloads.items():
        _atomic_json(root / "dist" / filename, payload)
    return payloads


def accept_new_observations(root: Path) -> int:
    data = validate_repository(root, check_history=False)
    history = check_observation_history(data, root, accept_new=True)
    previous = _load_history(root)
    added = len(set(history["observations"]) - set(previous["observations"]))
    _atomic_json(_history_path(root), history)
    return added


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "accept-new-observations"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "accept-new-observations":
            added = accept_new_observations(root)
            print(f"accepted {added} new KPI observation(s)")
        elif args.command == "validate":
            data = validate_repository(root)
            print(
                f"validated {len(data.systems)} systems, {len(data.definitions)} KPI definitions, "
                f"and {len(data.observations)} observations"
            )
        else:
            payloads = build_repository(root)
            print(f"built {len(payloads)} disclosure-safe artifacts")
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
