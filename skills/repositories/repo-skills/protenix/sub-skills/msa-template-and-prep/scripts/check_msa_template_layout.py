#!/usr/bin/env python3
"""Check Protenix MSA/template/RNA-MSA path layouts without running searches."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

UNIREF_PATTERN = re.compile(r"^>UniRef100_[^_]+_[^_/]+")
UNIPROT_PATTERN = re.compile(r"^>(?:tr|sp)\|[A-Z0-9]{6,10}(?:_\d+)?\|[A-Z0-9]{1,10}_[A-Z0-9]{1,5}")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)


def first_header(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.startswith(">"):
                    return line.strip()
    except OSError:
        return None
    return None


def check_a3m(path: Path, label: str, report: Report, require_taxonomy: bool = False) -> None:
    if not path.exists():
        report.error(f"{label}: missing file {path}")
        return
    if not path.is_file():
        report.error(f"{label}: expected file, found directory {path}")
        return
    if path.stat().st_size == 0:
        report.error(f"{label}: file is empty {path}")
        return
    header = first_header(path)
    if not header:
        report.warn(f"{label}: no FASTA/A3M header line found in {path}")
    elif require_taxonomy and not (UNIREF_PATTERN.match(header) or UNIPROT_PATTERN.match(header)):
        report.warn(f"{label}: first header may not expose taxonomy ID for pairing: {header[:120]}")
    report.note(f"{label}: found {path}")


def check_directory(path: Path, report: Report) -> None:
    if not path.exists():
        report.error(f"MSA/template directory is missing: {path}")
        return
    if not path.is_dir():
        report.error(f"Expected directory, found file: {path}")
        return
    check_a3m(path / "pairing.a3m", "protein paired MSA", report, require_taxonomy=True)
    check_a3m(path / "non_pairing.a3m", "protein unpaired MSA", report)
    template = path / "hmmsearch.a3m"
    hhr = path / "hmmsearch.hhr"
    if template.exists():
        check_a3m(template, "template hits", report)
    elif hhr.exists():
        report.note(f"template hits: found {hhr}")
    else:
        report.warn(f"template hits: no hmmsearch.a3m or hmmsearch.hhr in {path}; inference can run without templates if --use_template false.")


def resolve_reference(value: str, base: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate


def iter_entities(data: Any) -> list[tuple[str, dict[str, Any]]]:
    entities: list[tuple[str, dict[str, Any]]] = []
    if not isinstance(data, list):
        return entities
    for job_index, job in enumerate(data):
        if not isinstance(job, dict):
            continue
        sequences = job.get("sequences", [])
        if not isinstance(sequences, list):
            continue
        for entity_index, wrapper in enumerate(sequences):
            if not isinstance(wrapper, dict) or len(wrapper) != 1:
                continue
            entity_type = next(iter(wrapper))
            payload = wrapper[entity_type]
            if isinstance(payload, dict):
                entities.append((f"jobs[{job_index}].sequences[{entity_index}].{entity_type}", payload))
    return entities


def check_json(path: Path, report: Report) -> None:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        report.error(f"Could not read/parse JSON {path}: {exc}")
        return
    base = path.parent
    for entity_path, entity in iter_entities(data):
        for field, label, taxonomy in [
            ("pairedMsaPath", "paired MSA path", True),
            ("unpairedMsaPath", "unpaired MSA path", False),
            ("templatesPath", "template path", False),
        ]:
            value = entity.get(field)
            if value:
                check_a3m(resolve_reference(str(value), base), f"{entity_path}.{label}", report, require_taxonomy=taxonomy)
        legacy = entity.get("msa")
        if isinstance(legacy, dict):
            report.warn(f"{entity_path}.msa: legacy MSA dictionary detected; prefer pairedMsaPath/unpairedMsaPath for current Protenix inputs.")
    if not report.info and not report.errors:
        report.warn(f"No MSA/template/RNA path fields found in {path}; this may be valid for no-MSA inference.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Protenix MSA/template layouts without running searches.")
    parser.add_argument("paths", nargs="+", help="MSA/template directories or Protenix input JSON files.")
    parser.add_argument("--json", action="store_true", help="Emit JSON diagnostics.")
    args = parser.parse_args()

    report = Report()
    for raw in args.paths:
        path = Path(raw)
        if path.suffix.lower() == ".json":
            check_json(path, report)
        else:
            check_directory(path, report)

    result = {"ok": not report.errors, "errors": report.errors, "warnings": report.warnings, "info": report.info}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for message in report.errors:
            print(f"ERROR: {message}")
        for message in report.warnings:
            print(f"WARNING: {message}")
        for message in report.info:
            print(f"INFO: {message}")
        if result["ok"]:
            print("OK: no blocking MSA/template layout errors found.")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
