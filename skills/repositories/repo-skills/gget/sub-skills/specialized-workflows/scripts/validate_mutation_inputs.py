#!/usr/bin/env python3
"""Read-only preflight for a mutation FASTA and CSV/TSV table.

The helper intentionally validates joins and basic annotation shape only. It
never applies mutations, writes files, installs packages, or uses a network.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# This accepts the notation forms parsed by gget_mutate, without claiming to
# prove biological validity or reference-base correctness.
ANNOTATION = re.compile(r"^(?:c|g)\.[0-9_]+(?:[A-Za-z>]+|delins[A-Za-z]+|del|ins[A-Za-z]+|dup|inv)$")


def normalize_id(title: str) -> str:
    """Match gget's FASTA join normalization."""
    return title.split()[0].split(".")[0]


def read_fasta(path: Path) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    errors: list[str] = []
    current: str | None = None
    sequence_parts: list[str] = []
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        return [], [f"cannot open FASTA: {exc}"]
    with handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current is not None and not sequence_parts:
                    errors.append(f"FASTA record {current!r} has no sequence")
                current = normalize_id(line[1:])
                if not current:
                    errors.append(f"FASTA header at line {line_number} has no identifier")
                ids.append(current)
                sequence_parts = []
            elif current is None:
                errors.append(f"sequence data before first FASTA header at line {line_number}")
            else:
                sequence_parts.append(line)
        if current is not None and not sequence_parts:
            errors.append(f"FASTA record {current!r} has no sequence")
    if len(ids) != len(set(ids)):
        errors.append("duplicate normalized FASTA identifiers detected")
    return ids, errors


def read_mutations(path: Path, mut_column: str, seq_id_column: str) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    try:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            fields = reader.fieldnames or []
            missing = [name for name in (mut_column, seq_id_column) if name not in fields]
            if missing:
                return [], [f"mutation table is missing required column(s): {', '.join(missing)}"]
            rows = list(reader)
    except OSError as exc:
        return [], [f"cannot open mutation table: {exc}"]
    for number, row in enumerate(rows, 2):
        mutation = (row.get(mut_column) or "").strip()
        seq_id = (row.get(seq_id_column) or "").strip()
        if not mutation:
            errors.append(f"row {number}: empty {mut_column!r}")
        elif not ANNOTATION.fullmatch(mutation):
            errors.append(f"row {number}: unsupported annotation shape {mutation!r}")
        if not seq_id:
            errors.append(f"row {number}: empty {seq_id_column!r}")
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only FASTA/mutation-table join preflight")
    parser.add_argument("--fasta", required=True, type=Path, help="FASTA file to inspect")
    parser.add_argument("--mutations", required=True, type=Path, help="CSV or TSV mutation table")
    parser.add_argument("--mut-column", default="mutation", help="Mutation column (default: mutation)")
    parser.add_argument("--seq-id-column", default="seq_ID", help="Sequence ID column (default: seq_ID)")
    args = parser.parse_args()

    fasta_ids, fasta_errors = read_fasta(args.fasta)
    rows, table_errors = read_mutations(args.mutations, args.mut_column, args.seq_id_column)
    fasta_set = set(fasta_ids)
    row_ids = [(row.get(args.seq_id_column) or "").strip() for row in rows]
    unmatched = sorted({identifier for identifier in row_ids if identifier and identifier not in fasta_set})
    report = {
        "fasta": str(args.fasta),
        "mutations": str(args.mutations),
        "fasta_record_count": len(fasta_ids),
        "mutation_row_count": len(rows),
        "matched_row_count": sum(identifier in fasta_set for identifier in row_ids if identifier),
        "unmatched_sequence_ids": unmatched,
        "errors": fasta_errors + table_errors,
        "read_only": True,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["errors"] or unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
