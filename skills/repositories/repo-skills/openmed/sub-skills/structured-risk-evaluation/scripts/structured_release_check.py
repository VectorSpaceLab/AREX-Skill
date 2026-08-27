#!/usr/bin/env python3
"""Synthetic structured release-risk smoke check.

The helper keeps all records synthetic and local. It writes a discovery
manifest, raw assessment, transformed release, reread validation, and aggregate
expert-review evidence. It is designed to surface a too-small equivalence class
before or during remediation, then emit a clear summary of the final result.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from openmed.compliance import (
    ExpertReviewEvidenceReport,
    ReleaseAssumptions,
    build_release_expert_review_evidence,
)
from openmed.core.audit import stable_hash
from openmed.risk import (
    AnonymityPolicy,
    assess_release,
    anonymize_release,
    validate_released_output,
)
from openmed.structured import read_table, scan_table, write_table

SYNTHETIC_ROWS: tuple[dict[str, Any], ...] = (
    {
        "patient_id": "synthetic-patient-001",
        "encounter_id": "synthetic-encounter-001",
        "full_name": "Avery Example",
        "age": 31,
        "zip": "10001",
        "visit_date": "2024-01-01",
        "disease": "influenza",
    },
    {
        "patient_id": "synthetic-patient-002",
        "encounter_id": "synthetic-encounter-002",
        "full_name": "Blair Example",
        "age": 32,
        "zip": "10002",
        "visit_date": "2024-01-02",
        "disease": "common-cold",
    },
    {
        "patient_id": "synthetic-patient-003",
        "encounter_id": "synthetic-encounter-003",
        "full_name": "Casey Example",
        "age": 41,
        "zip": "20001",
        "visit_date": "2024-01-03",
        "disease": "influenza",
    },
    {
        "patient_id": "synthetic-patient-004",
        "encounter_id": "synthetic-encounter-004",
        "full_name": "Devon Example",
        "age": 42,
        "zip": "20002",
        "visit_date": "2024-01-04",
        "disease": "common-cold",
    },
)


def _resolve_artifact_dir(value: Path | None) -> Path:
    if value is None:
        return Path(tempfile.mkdtemp(prefix="openmed-structured-release-"))
    value.mkdir(parents=True, exist_ok=True)
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_workflow(artifact_dir: Path, min_group_size: int) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    source_path = artifact_dir / "synthetic-cohort.jsonl"
    discovery_path = artifact_dir / "qi-discovery.json"
    assessment_path = artifact_dir / "pre-release-assessment.json"
    release_path = artifact_dir / "validated-release.jsonl"
    validation_path = artifact_dir / "release-validation.json"
    evidence_path = artifact_dir / "expert-review-evidence.json"
    evidence_md_path = artifact_dir / "expert-review-evidence.md"

    write_table(source_path, SYNTHETIC_ROWS)

    discovery = scan_table(
        source_path,
        privacy_unit="patient_id",
        quasi_identifier_columns=("age", "zip", "visit_date"),
        sensitive_columns=("disease",),
        role_overrides={
            "encounter_id": ("direct-id", "internal-linkage"),
            "full_name": "direct-id",
        },
    )
    _write_json(discovery_path, discovery)

    # The l/t thresholds stay synthetic and explicit; only k is parameterized.
    policy = AnonymityPolicy(
        quasi_identifiers=("age", "zip", "visit_date"),
        sensitive_attributes=("disease",),
        direct_identifiers=("encounter_id", "full_name"),
        privacy_unit="patient_id",
        target_k=min_group_size,
        target_l=2,
        l_metric="distinct",
        target_t=0.0,
        suppression_rate=0.0,
        max_lattice_nodes=100_000,
        max_suppression_subsets=100_000,
    )

    source_rows = read_table(source_path)
    assessment = assess_release(source_rows, policy)
    _write_json(assessment_path, assessment.to_dict())

    result = anonymize_release(source_rows, policy)
    write_table(release_path, result.records)

    reread_rows = read_table(release_path)
    validation = validate_released_output(reread_rows, result)
    _write_json(validation_path, validation.to_dict())

    assumptions = ReleaseAssumptions(
        privacy_unit="patient",
        population_scope="release_cohort",
        release_model="restricted",
        recipient_model="named_researchers",
        auxiliary_data_model="reasonably_available",
        notes_digest=stable_hash(
            {
                "kind": "synthetic-release-assumptions",
                "min_group_size": min_group_size,
                "purpose": "structured release smoke",
            }
        ),
    )
    evidence = build_release_expert_review_evidence(
        result,
        validation=validation,
        assumptions=assumptions,
    )
    evidence_path.write_text(evidence.to_json() + "\n", encoding="utf-8")
    evidence_md_path.write_text(evidence.to_markdown(), encoding="utf-8")

    evidence_report = ExpertReviewEvidenceReport.from_json(
        evidence_path.read_text(encoding="utf-8")
    )
    evidence_verified = evidence_report.verify()

    raw_equivalence_class_too_small = assessment.achieved_k < min_group_size
    pre_release_needs_remediation = not assessment.meets_policy
    final_ok = (
        validation.passed
        and result.after.meets_policy
        and result.after.achieved_k >= min_group_size
        and evidence_verified
    )
    if final_ok and pre_release_needs_remediation:
        final_status = "remediated"
    elif final_ok:
        final_status = "validated"
    else:
        final_status = "blocked"

    return {
        "artifact_dir": str(artifact_dir),
        "source_path": str(source_path),
        "discovery_path": str(discovery_path),
        "assessment_path": str(assessment_path),
        "release_path": str(release_path),
        "validation_path": str(validation_path),
        "evidence_path": str(evidence_path),
        "evidence_markdown_path": str(evidence_md_path),
        "discovery_status": discovery.get("discovery", {}).get("status"),
        "discovery_advisory": discovery.get("discovery", {}).get("advisory"),
        "min_group_size": min_group_size,
        "raw_equivalence_class_too_small": raw_equivalence_class_too_small,
        "pre_release_needs_remediation": pre_release_needs_remediation,
        "raw_release_meets_policy": assessment.meets_policy,
        "post_release_meets_policy": result.after.meets_policy,
        "final_ok": final_ok,
        "final_status": final_status,
        "policy": policy.to_dict(),
        "raw_assessment": assessment.to_dict(),
        "anonymization": result.to_safe_dict(),
        "validation": validation.to_dict(),
        "evidence_verified": evidence_verified,
        "artifact_files": [
            str(discovery_path),
            str(assessment_path),
            str(release_path),
            str(validation_path),
            str(evidence_path),
            str(evidence_md_path),
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-group-size",
        type=int,
        default=2,
        help="Minimum equivalence-class size to require in the release policy.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help=(
            "Directory for synthetic release artifacts. When omitted, a private "
            "temporary directory is created and retained."
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help=(
            "Write the aggregate summary JSON here. Defaults to "
            "<artifact-dir>/structured_release_summary.json when omitted."
        ),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    artifact_dir = _resolve_artifact_dir(args.artifact_dir)
    summary = run_workflow(artifact_dir, args.min_group_size)
    output_json = args.output_json or artifact_dir / "structured_release_summary.json"
    summary["output_json_path"] = str(output_json)
    _write_json(output_json, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["final_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
