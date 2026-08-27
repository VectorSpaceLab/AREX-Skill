#!/usr/bin/env python3
"""Format sample ClinicalTrials.gov data without network access.

The script uses PaperQA's clinical-trial formatting helpers when available and
falls back to an equivalent local formatter for inspection environments that do
not have PaperQA installed. It verifies that an NCT identifier and citation
signals survive formatting.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

SAMPLE_TRIAL_DATA: dict[str, Any] = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT12345678",
            "briefTitle": "Test Clinical Trial",
            "organization": {"fullName": "Test Hospital"},
        },
        "sponsorCollaboratorsModule": {
            "responsibleParty": {"investigatorFullName": "Dr. John Doe"},
            "leadSponsor": {"name": "Test Organization"},
        },
        "statusModule": {
            "overallStatus": "RECRUITING",
            "startDateStruct": {"date": "2023-01"},
            "completionDateStruct": {"date": "2024-12"},
        },
        "descriptionModule": {
            "briefSummary": "This is a brief summary for a no-network formatting check.",
            "detailedDescription": "This is a detailed description.",
        },
        "designModule": {
            "studyType": "INTERVENTIONAL",
            "phases": ["PHASE1", "PHASE2"],
            "enrollmentInfo": {"count": 100},
        },
        "eligibilityModule": {"eligibilityCriteria": "Must be 18 or older."},
    }
}


@dataclass
class FallbackDocDetails:
    title: str
    docname: str
    dockey: str
    authors: list[str]
    year: int | None
    citation: str
    other: dict[str, Any]


def fallback_format_to_doc_details(trial_data: dict[str, Any]) -> FallbackDocDetails:
    protocol = trial_data.get("protocolSection", {})
    investigator = (
        protocol.get("sponsorCollaboratorsModule", {})
        .get("responsibleParty", {})
        .get("investigatorFullName", "")
    )
    title = protocol.get("identificationModule", {}).get("briefTitle", "")
    organization = (
        protocol.get("sponsorCollaboratorsModule", {})
        .get("leadSponsor", {})
        .get("name", "")
    )
    start_date = protocol.get("statusModule", {}).get("startDateStruct", {}).get(
        "date", ""
    )
    nct_id = protocol.get("identificationModule", {}).get("nctId", "")
    year_text = start_date.split("-")[0] if start_date else ""
    citation_parts: list[str] = []
    if investigator:
        citation_parts.append(f"{investigator}.")
    if title:
        citation_parts.append(f" {title}.")
    if organization:
        citation_parts.append(f" {organization}.")
    if year_text:
        citation_parts.append(f" {year_text}.")
    if nct_id:
        citation_parts.append(f" ClinicalTrials.gov Identifier: {nct_id}")
    return FallbackDocDetails(
        title=title,
        docname=nct_id,
        dockey=nct_id,
        authors=[investigator],
        year=int(year_text) if year_text.isdigit() else None,
        citation="".join(citation_parts),
        other={"client_source": ["clinicaltrials.gov"]},
    )


def fallback_parse_clinical_trial(json_data: dict[str, Any]) -> str:
    protocol = json_data.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    description = protocol.get("descriptionModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    design = protocol.get("designModule", {})
    sections = [
        "CLINICAL TRIAL INFORMATION",
        "=" * 25,
        f"NCT Number: {identification.get('nctId', 'Not provided')}",
        f"Title: {identification.get('briefTitle', 'Not provided')}",
        f"Organization: {identification.get('organization', {}).get('fullName', 'Not provided')}",
        "\nSTUDY STATUS",
        "=" * 13,
        f"Overall Status: {status.get('overallStatus', 'Not provided')}",
        f"Start Date: {status.get('startDateStruct', {}).get('date', 'Not provided')}",
        f"Completion Date: {status.get('completionDateStruct', {}).get('date', 'Not provided')}",
        "\nSTUDY DESCRIPTION",
        "=" * 17,
        description.get("briefSummary", "Not provided"),
        "\nSTUDY DESIGN",
        "=" * 13,
        f"Study Type: {design.get('studyType', 'Not provided')}",
        f"Phase: {', '.join(design.get('phases', ['Not provided']))}",
        f"Enrollment: {design.get('enrollmentInfo', {}).get('count', 'Not provided')} participants",
        "\nELIGIBILITY CRITERIA",
        "=" * 19,
        eligibility.get("eligibilityCriteria", "Not provided"),
    ]
    if description.get("detailedDescription"):
        sections[13:13] = [
            "\nDETAILED DESCRIPTION",
            "=" * 20,
            description["detailedDescription"],
        ]
    return "\n".join(sections)


def details_to_dict(details: Any) -> dict[str, Any]:
    if hasattr(details, "model_dump"):
        return details.model_dump(mode="json")
    if hasattr(details, "__dataclass_fields__"):
        return asdict(details)
    return dict(details)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON summary instead of a text report.",
    )
    args = parser.parse_args()

    formatter_source = "fallback"
    try:
        from paperqa.sources.clinical_trials import (  # type: ignore
            format_to_doc_details,
            parse_clinical_trial,
        )

        formatter_source = "paperqa.sources.clinical_trials"
    except Exception:  # pragma: no cover - fallback for bare environments
        format_to_doc_details = fallback_format_to_doc_details
        parse_clinical_trial = fallback_parse_clinical_trial

    details = format_to_doc_details(SAMPLE_TRIAL_DATA)
    readable_text = parse_clinical_trial(SAMPLE_TRIAL_DATA)
    details_dict = details_to_dict(details)

    citation = details_dict.get("citation", "") or ""
    nct_id = details_dict.get("docname") or details_dict.get("dockey") or ""
    checks = {
        "nct_in_doc_identity": str(nct_id).startswith("NCT"),
        "nct_in_citation": "NCT12345678" in citation,
        "clinicaltrials_signal": "ClinicalTrials.gov Identifier" in citation,
        "title_present": details_dict.get("title") == "Test Clinical Trial",
        "readable_text_has_sections": "CLINICAL TRIAL INFORMATION" in readable_text
        and "ELIGIBILITY CRITERIA" in readable_text,
    }
    ok = all(checks.values())

    report = {
        "network_calls_made": False,
        "formatter_source": formatter_source,
        "checks": checks,
        "details": {
            "title": details_dict.get("title"),
            "docname": details_dict.get("docname"),
            "dockey": details_dict.get("dockey"),
            "authors": details_dict.get("authors"),
            "year": details_dict.get("year"),
            "citation": citation,
            "other": details_dict.get("other"),
        },
        "readable_text_preview": readable_text.splitlines()[:12],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ClinicalTrials.gov sample formatting (no network)")
        print("=" * 54)
        print(f"Formatter source: {formatter_source}")
        print(f"Title: {report['details']['title']}")
        print(f"Doc identity: {report['details']['docname']}")
        print(f"Citation: {citation}")
        print("Checks:")
        for name, passed in checks.items():
            print(f"- {name}: {'ok' if passed else 'FAIL'}")
        print("Readable preview:")
        for line in report["readable_text_preview"]:
            print(line)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
