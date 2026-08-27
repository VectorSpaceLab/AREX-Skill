#!/usr/bin/env python3
"""Validate AlphaFold FASTA inputs without importing AlphaFold or running tools."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

STANDARD_AAS = set("ACDEFGHIKLMNPQRSTVWY")
PDB_CHAIN_IDS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
PDB_MAX_CHAINS = len(PDB_CHAIN_IDS)


class FastaError(ValueError):
    """Raised when FASTA text cannot be parsed."""


def parse_fasta(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            current = {"description": line[1:].strip(), "sequence_lines": [], "line": line_number}
            records.append(current)
            continue
        if current is None:
            raise FastaError(f"sequence data before first FASTA header at line {line_number}")
        current["sequence_lines"].append(line)
    if not records:
        raise FastaError("no FASTA records found")
    return records


def clean_sequence(sequence_lines: list[str]) -> str:
    raw_sequence = "".join(sequence_lines)
    return raw_sequence.translate(str.maketrans("", "", " \n\t\r")).upper()


def classify_chains(sequences: list[str]) -> str:
    if len(sequences) == 1:
        return "monomer"
    unique_count = len(set(sequences))
    if unique_count == 1:
        return "homomer"
    if unique_count < len(sequences):
        return "heteromer_with_repeated_chains"
    return "heteromer"


def validate_records(
    records: list[dict[str, Any]],
    *,
    min_length: int,
    max_length: int,
    mode: str,
    max_chains: int,
    fail_on_duplicate_descriptions: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    validated_records: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        description = record["description"]
        sequence = clean_sequence(record["sequence_lines"])
        invalid = sorted(set(sequence) - STANDARD_AAS)
        if not description:
            warnings.append(f"record {index} has an empty description")
        if not sequence:
            errors.append(f"record {index} ({description or 'no description'}) has an empty sequence")
        if invalid:
            errors.append(
                f"record {index} ({description or 'no description'}) contains non-standard amino-acid letters: "
                + ",".join(invalid)
            )
        if sequence and len(sequence) < min_length:
            errors.append(
                f"record {index} ({description or 'no description'}) is too short: {len(sequence)} < {min_length}"
            )
        if sequence and len(sequence) > max_length:
            errors.append(
                f"record {index} ({description or 'no description'}) is too long: {len(sequence)} > {max_length}"
            )
        validated_records.append(
            {
                "index": index,
                "description": description,
                "length": len(sequence),
                "sequence": sequence,
                "line": record["line"],
            }
        )

    descriptions = [record["description"] for record in validated_records]
    duplicate_descriptions = sorted(
        description for description, count in Counter(descriptions).items() if description and count > 1
    )
    if duplicate_descriptions:
        message = "duplicate FASTA descriptions: " + ", ".join(duplicate_descriptions)
        if fail_on_duplicate_descriptions:
            errors.append(message)
        else:
            warnings.append(message)

    chain_count = len(validated_records)
    if mode == "monomer" and chain_count != 1:
        errors.append(f"monomer mode expects exactly 1 FASTA record, found {chain_count}")
    if mode == "multimer" and chain_count < 2:
        errors.append(f"multimer mode expects at least 2 FASTA records, found {chain_count}")
    if chain_count > max_chains:
        errors.append(f"chain count {chain_count} exceeds configured maximum {max_chains}")
    if max_chains > PDB_MAX_CHAINS:
        warnings.append(f"configured max chains {max_chains} exceeds PDB format limit {PDB_MAX_CHAINS}")
    if chain_count > PDB_MAX_CHAINS:
        errors.append(f"chain count {chain_count} exceeds AlphaFold PDB chain limit {PDB_MAX_CHAINS}")

    sequences = [record["sequence"] for record in validated_records]
    sequence_counts = Counter(sequences)
    repeated_chain_groups = [
        {"sequence_index": sequences.index(sequence) + 1, "copies": count, "length": len(sequence)}
        for sequence, count in sequence_counts.items()
        if count > 1
    ]
    chain_type = classify_chains(sequences) if sequences else "none"

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "records": chain_count,
            "unique_sequences": len(sequence_counts),
            "chain_type": chain_type,
            "total_residues": sum(len(sequence) for sequence in sequences),
            "min_length": min((len(sequence) for sequence in sequences), default=0),
            "max_length": max((len(sequence) for sequence in sequences), default=0),
            "duplicate_descriptions": duplicate_descriptions,
            "repeated_chain_groups": repeated_chain_groups,
            "pdb_chain_limit": PDB_MAX_CHAINS,
        },
        "records": [
            {
                "index": record["index"],
                "description": record["description"],
                "length": record["length"],
                "pdb_chain_id": PDB_CHAIN_IDS[record["index"] - 1]
                if record["index"] <= PDB_MAX_CHAINS
                else None,
                "line": record["line"],
            }
            for record in validated_records
        ],
    }


def format_text(path: Path, result: dict[str, Any]) -> str:
    status = "OK" if result["ok"] else "FAILED"
    summary = result["summary"]
    lines = [f"{status}: {path}"]
    if not summary:
        if result["warnings"]:
            lines.append("warnings:")
            lines.extend(f"  - {warning}" for warning in result["warnings"])
        if result["errors"]:
            lines.append("errors:")
            lines.extend(f"  - {error}" for error in result["errors"])
        return "\n".join(lines)
    lines.extend(
        [
            f"records: {summary['records']}",
            f"unique_sequences: {summary['unique_sequences']}",
            f"chain_type: {summary['chain_type']}",
            f"total_residues: {summary['total_residues']}",
            f"length_range: {summary['min_length']}..{summary['max_length']}",
        ]
    )
    if summary["duplicate_descriptions"]:
        lines.append("duplicate_descriptions: " + ", ".join(summary["duplicate_descriptions"]))
    if summary["repeated_chain_groups"]:
        groups = ", ".join(
            f"record {group['sequence_index']} x{group['copies']} ({group['length']} aa)"
            for group in summary["repeated_chain_groups"]
        )
        lines.append("repeated_chain_groups: " + groups)
    if result["records"]:
        lines.append("records_detail:")
        for record in result["records"]:
            description = record["description"] or "<empty description>"
            lines.append(
                f"  - #{record['index']} chain={record['pdb_chain_id']} length={record['length']} description={description}"
            )
    if result["warnings"]:
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in result["warnings"])
    if result["errors"]:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in result["errors"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate AlphaFold FASTA inputs without running alignment, template, or prediction tools."
    )
    parser.add_argument("fasta", nargs="+", type=Path, help="FASTA file(s) to validate")
    parser.add_argument("--min-length", type=int, default=1, help="minimum cleaned sequence length per record")
    parser.add_argument("--max-length", type=int, default=10000, help="maximum cleaned sequence length per record")
    parser.add_argument(
        "--mode",
        choices=("auto", "monomer", "multimer"),
        default="auto",
        help="target mode constraint to enforce",
    )
    parser.add_argument(
        "--max-chains",
        type=int,
        default=PDB_MAX_CHAINS,
        help="maximum FASTA records allowed for multimer validation",
    )
    parser.add_argument(
        "--fail-on-duplicate-descriptions",
        action="store_true",
        help="treat repeated non-empty FASTA descriptions as errors instead of warnings",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.min_length < 0:
        parser.error("--min-length must be non-negative")
    if args.max_length < args.min_length:
        parser.error("--max-length must be greater than or equal to --min-length")
    if args.max_chains < 1:
        parser.error("--max-chains must be at least 1")

    results = []
    exit_code = 0
    for fasta_path in args.fasta:
        try:
            text = fasta_path.read_text(encoding="utf-8")
            records = parse_fasta(text)
            result = validate_records(
                records,
                min_length=args.min_length,
                max_length=args.max_length,
                mode=args.mode,
                max_chains=args.max_chains,
                fail_on_duplicate_descriptions=args.fail_on_duplicate_descriptions,
            )
        except OSError as exc:
            result = {"ok": False, "errors": [str(exc)], "warnings": [], "summary": {}, "records": []}
        except FastaError as exc:
            result = {"ok": False, "errors": [str(exc)], "warnings": [], "summary": {}, "records": []}
        result["path"] = str(fasta_path)
        results.append(result)
        if not result["ok"]:
            exit_code = 1

    if args.json:
        print(json.dumps({"ok": exit_code == 0, "files": results}, indent=2, sort_keys=True))
    else:
        for index, result in enumerate(results):
            if index:
                print()
            print(format_text(Path(result["path"]), result))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
