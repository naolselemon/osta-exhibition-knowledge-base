"""Build immutable chatbot releases from validated, approved knowledge only.

Run as python -m scripts.chatbot_release {build,coverage}. Coverage is an
authoring diagnostic, not a release, and deliberately works with missing evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.kpi_pipeline import (
    LOCALIZED_KPI_TOKEN_RE, RepositoryData, ValidationFailure, _assert_disclosure_safe,
    _public_source_labels, build_payloads, load_repository, render_localized_faq,
    validate_repository,
)

VERSION = "1.0.0"
LOCALES = {"om": "om-ET", "am": "am-ET"}


def approved_translation(record: dict, language: str) -> dict | None:
    translation = record.get("translations", {}).get(language, {})
    approval = translation.get("approval", {})
    role = "human-amharic-reviewer" if language == "am" else "human-afaan-oromo-reviewer"
    if approval.get("status") == "approved" and (
        approval.get("approved_source") is True or (
            approval.get("human_reviewed") is True and approval.get("reviewer_role") == role
        )
    ):
        return translation
    return None


def safe_system(system: dict) -> bool:
    return system.get("publication_status") == "published" and system.get("workflow", {}).get("review_status") == "approved"


def build_chatbot_payload(data: RepositoryData, public: dict) -> dict:
    """Pure builder for already validated records; release() owns validation."""
    facts = public["avatar-facts.json"]
    observations = {item["id"]: item for item in facts["verified_public_kpi_observations"]}
    raw_observations = {item["id"]: item for item in data.observations}
    definitions = {item["kpi_code"]: item for item in data.definitions}
    safe_faq_ids = {item["id"] for item in facts["published_faqs"]}
    topics, answers = [], []
    for system in sorted(data.systems, key=lambda item: item["id"]):
        if not safe_system(system):
            continue
        for language, locale in LOCALES.items():
            translated = approved_translation(system, language)
            if not translated or not all(isinstance(translated.get(key), str) and translated[key].strip() for key in ("official_name", "purpose")):
                continue
            answer_id = f"system:{system['id']}:{language}"
            topics.append({"id": system["id"], "locale": locale, "name": translated["official_name"], "answer_id": answer_id})
            answers.append({
                "id": answer_id, "record_id": system["id"], "system_id": system["id"],
                "kind": "system", "locale": locale, "question": translated["official_name"],
                "aliases": list(dict.fromkeys(value for value in (system.get("official_name"), system.get("acronym")) if value)),
                "answer": translated["purpose"], "kpis": [],
                "sources": _public_source_labels(system),
            })
            for faq in sorted(data.faqs, key=lambda item: item["id"]):
                if faq["id"] not in safe_faq_ids or faq["system_id"] != system["id"] or faq.get("workflow", {}).get("state") != "approved":
                    continue
                translation = approved_translation(faq, language)
                if not translation:
                    continue
                try:
                    rendered = render_localized_faq(translation, raw_observations, definitions, require_localized_units=True)
                except ValidationFailure:
                    # Coverage identifies these gaps; never improvise a localized unit.
                    continue
                kpis = []
                sources = []
                for ref in faq["kpi_observation_refs"]:
                    observation = observations[ref]
                    kpis.append({
                        "observation_id": ref, "actual": observation["actual"],
                        "reporting_period": observation["reporting_period"],
                        "measurement_scope": observation["measurement_scope"],
                    })
                    sources.extend(observation["source_labels"])
                # Every sentence and limitation remains verbatim approved wording.
                answers.append({
                    "id": f"faq:{faq['id']}:{language}", "record_id": faq["id"],
                    "system_id": system["id"], "kind": "faq", "locale": locale,
                    "question": rendered["question"], "answer": rendered["answer"],
                    "aliases": [],
                    "kpis": kpis, "sources": list({json.dumps(s, sort_keys=True): s for s in sources}.values()),
                })
    payload = {"schema_version": VERSION, "locales": list(LOCALES.values()), "topics": topics, "answers": answers}
    serialized = json.dumps(payload, ensure_ascii=False)
    if "source-materials/" in serialized or "{{" in serialized:
        raise ValidationFailure(["chatbot export contains private paths or unresolved tokens"])
    return payload


def coverage(data: RepositoryData) -> dict:
    """No publication side effects; surface authoring work without inventing claims."""
    rows = []
    for system in sorted(data.systems, key=lambda item: item["id"]):
        if system.get("publication_status") != "published":
            continue
        faqs = [faq for faq in data.faqs if faq["system_id"] == system["id"]]
        for language, locale in LOCALES.items():
            gaps = []
            approved = [
                faq for faq in faqs
                if faq.get("publication_status") == "published"
                and faq.get("workflow", {}).get("state") == "approved"
                and approved_translation(faq, language)
            ]
            for faq in approved:
                translation = faq["translations"][language]
                for ref, number_only in LOCALIZED_KPI_TOKEN_RE.findall(translation["answer"]):
                    observation = next(item for item in data.observations if item["id"] == ref)
                    if not number_only and observation["actual"].get("unit") != "percent" and ref not in translation.get("kpi_unit_labels", {}):
                        gaps.append(f"{faq['id']}: localized unit label required for {ref}")
            rows.append({
                "system_id": system["id"], "locale": locale,
                "approved_purpose": bool(approved_translation(system, language)),
                "approved_faq_count": len(approved), "faq_target": 3,
                "draft_faq_count": sum(faq.get("publication_status") == "draft" for faq in faqs),
                "faq_needs_review_count": sum(
                    faq.get("publication_status") == "published"
                    and faq.get("workflow", {}).get("state") != "approved"
                    for faq in faqs
                ),
                "review_gaps": gaps,
                "beneficiaries": "needs-question-and-language-review",
                "capabilities": "needs-question-and-language-review",
                "transformation": "needs-evidence-and-language-review",
            })
    return {"release_ready": False, "description": "Authoring diagnostic; not a release or factual approval", "rows": rows}


def encode(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def release(root: Path, output: Path) -> Path:
    data = validate_repository(root)
    public = build_payloads(data)
    _assert_disclosure_safe(public)
    public["chatbot-knowledge.json"] = build_chatbot_payload(data, public)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=root, text=True).strip())
    artifacts = {name: encode(payload) for name, payload in public.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in artifacts.items()}
    version = hashlib.sha256(encode(hashes)).hexdigest()
    manifest = {
        "schema_version": VERSION, "knowledge_version": version, "knowledge_commit": commit,
        "working_tree_dirty": dirty, "built_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": hashes,
    }
    output.mkdir(parents=True, exist_ok=True)
    target = output / version
    if target.exists():
        raise ValidationFailure([f"immutable release already exists: {target}"])
    # Directory rename publishes all artifacts together; errors leave no partial release.
    with tempfile.TemporaryDirectory(prefix=".chatbot-build-", dir=output) as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        for filename, content in artifacts.items():
            (staging / filename).write_bytes(content)
        (staging / "manifest.json").write_bytes(encode(manifest))
        os.rename(staging, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "coverage"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("releases"))
    args = parser.parse_args()
    try:
        if args.command == "coverage":
            print(json.dumps(coverage(load_repository(args.root)), ensure_ascii=False, indent=2))
        else:
            print(release(args.root.resolve(), args.output.resolve()))
    except (ValidationFailure, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
