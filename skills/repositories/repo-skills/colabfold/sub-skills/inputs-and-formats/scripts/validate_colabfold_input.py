#!/usr/bin/env python3
"""Safely validate how ColabFold will parse FASTA/CSV/A3M inputs.

This script performs read-only local checks. It does not run MSA search,
prediction, relaxation, downloads, database setup, or GPU work.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight ColabFold FASTA/CSV/TSV/A3M/directory inputs without network or prediction work."
    )
    parser.add_argument("input_path", type=Path, help="Input FASTA, CSV, TSV, A3M, PDB/mmCIF file, or directory.")
    parser.add_argument(
        "--sort",
        choices=("length", "msa_depth", "random", "none"),
        default="length",
        help="Query sorting to request from ColabFold. Use 'none' to preserve parser order where supported by current code.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON summary.")
    parser.add_argument(
        "--allow-random-sort",
        action="store_true",
        help="Permit ColabFold random sorting. Disabled by default for deterministic validation.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="For CSV/TSV a3mpath/templatepath columns, report whether referenced local files exist.",
    )
    return parser


def _load_colabfold_input():
    try:
        from colabfold.input import classify_molecules, get_queries, parse_fasta, safe_filename
    except Exception as exc:  # pragma: no cover - message is the point for end users
        raise RuntimeError(
            "Could not import lightweight ColabFold input helpers. Activate an environment with "
            "the base 'colabfold' package installed; do not import colabfold.batch for input-only checks. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc
    return classify_molecules, get_queries, parse_fasta, safe_filename


def _as_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _as_jsonable(item) for key, item in value.items()}
    return str(value)


def _read_csv_like(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def _precheck_text_records(path: Path, parse_fasta) -> list[str]:
    warnings: list[str] = []
    suffix = path.suffix.lower()
    if suffix not in {".fasta", ".faa", ".fa", ".a3m"}:
        return warnings
    text = path.read_text(errors="replace")
    sequences, descriptions = parse_fasta(text)
    if not sequences:
        warnings.append(f"{path}: no FASTA/A3M records found")
    if text.strip() and not text.lstrip().startswith((">", "#")):
        warnings.append(f"{path}: content appears before the first FASTA header")
    for index, sequence in enumerate(sequences, start=1):
        if not sequence:
            label = descriptions[index - 1] if index - 1 < len(descriptions) else index
            warnings.append(f"{path}: record {label!r} has an empty sequence")
        if "smiles|" in sequence.lower() and ":" in sequence:
            warnings.append(
                f"{path}: SMILES-like entry contains ':'; use ';' for aromatic SMILES colons in ColabFold FASTA"
            )
    if suffix in {".fasta", ".faa", ".fa"} and len(sequences) > 1:
        warnings.append(f"{path}: directory parsing keeps only the first FASTA record per file")
    return warnings


def _collect_candidate_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return [path for path in sorted(input_path.iterdir()) if path.is_file()]
    return []


def _csv_warnings(path: Path, check_files: bool) -> list[str]:
    warnings: list[str] = []
    if path.suffix.lower() not in {".csv", ".tsv"}:
        return warnings
    try:
        fields, rows = _read_csv_like(path)
    except Exception as exc:
        return [f"{path}: could not read delimited file: {type(exc).__name__}: {exc}"]
    missing = [name for name in ("id", "sequence") if name not in fields]
    if missing:
        warnings.append(f"{path}: missing required column(s): {', '.join(missing)}")
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        row_id = row.get("id", "")
        sequence = row.get("sequence", "")
        if not row_id:
            warnings.append(f"{path}: row {row_number} has an empty id")
        elif row_id in seen_ids:
            warnings.append(f"{path}: duplicate id {row_id!r}")
        seen_ids.add(row_id)
        if not sequence:
            warnings.append(f"{path}: row {row_number} has an empty sequence")
        if "smiles|" in sequence.lower() and ":" in sequence:
            warnings.append(
                f"{path}: row {row_number} has SMILES-like ':'; use ';' inside SMILES components"
            )
        if check_files:
            for column in ("a3mpath", "templatepath"):
                value = row.get(column)
                if value and not Path(value).expanduser().exists():
                    warnings.append(f"{path}: row {row_number} {column} does not exist: {value}")
    return warnings


def _summarize_query(query: tuple[Any, Any, Any, Any], safe_filename) -> dict[str, Any]:
    job_name, sequence, a3m, extra = query
    if isinstance(sequence, list):
        sequence_kind = "complex"
        chain_lengths = [len(chain) for chain in sequence]
        total_length = sum(chain_lengths)
    else:
        sequence_kind = "monomer"
        chain_lengths = [len(sequence)]
        total_length = len(sequence)
    return {
        "job_name": job_name,
        "safe_job_name": safe_filename(str(job_name)),
        "sequence_kind": sequence_kind,
        "chain_count": len(chain_lengths),
        "chain_lengths": chain_lengths,
        "total_length": total_length,
        "has_a3m": a3m is not None,
        "a3m_type": type(a3m).__name__ if a3m is not None else None,
        "has_extra": extra is not None,
        "extra": _as_jsonable(extra),
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.sort == "random" and not args.allow_random_sort:
        parser.error("--sort random is nondeterministic; pass --allow-random-sort to use it intentionally")

    input_path = args.input_path.expanduser()
    if not input_path.exists():
        print(f"ERROR: input path does not exist: {input_path}", file=sys.stderr)
        return 2

    try:
        _classify_molecules, get_queries, parse_fasta, safe_filename = _load_colabfold_input()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    warnings: list[str] = []
    for candidate in _collect_candidate_files(input_path):
        warnings.extend(_precheck_text_records(candidate, parse_fasta))
        warnings.extend(_csv_warnings(candidate, args.check_files))

    sort_value = "" if args.sort == "none" else args.sort
    captured_logs: list[str] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_logs.append(record.getMessage())

    logger = logging.getLogger("colabfold.input")
    handler = _ListHandler()
    logger.addHandler(handler)
    try:
        queries, is_complex = get_queries(input_path, sort_queries_by=sort_value)
    except Exception as exc:
        logger.removeHandler(handler)
        result = {
            "ok": False,
            "input_path": str(input_path),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "warnings": warnings,
            "logs": captured_logs,
        }
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
            for warning in warnings:
                print(f"WARNING: {warning}", file=sys.stderr)
            for message in captured_logs:
                print(f"LOG: {message}", file=sys.stderr)
        return 1
    finally:
        if handler in logger.handlers:
            logger.removeHandler(handler)

    summaries = [_summarize_query(query, safe_filename) for query in queries]
    safe_names: dict[str, list[str]] = {}
    for summary in summaries:
        safe_names.setdefault(summary["safe_job_name"], []).append(summary["job_name"])
    for safe_name, raw_names in safe_names.items():
        if len(raw_names) > 1:
            warnings.append(f"sanitized job name {safe_name!r} is shared by {raw_names!r}")

    result = {
        "ok": True,
        "input_path": str(input_path),
        "sort": args.sort,
        "query_count": len(summaries),
        "is_complex": is_complex,
        "queries": summaries,
        "warnings": warnings,
        "logs": captured_logs,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"OK: parsed {len(summaries)} quer{'y' if len(summaries) == 1 else 'ies'}; is_complex={is_complex}")
        for summary in summaries:
            print(
                "- {job_name} -> safe={safe_job_name} kind={sequence_kind} "
                "chains={chain_count} lengths={chain_lengths} has_a3m={has_a3m}".format(**summary)
            )
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for message in captured_logs:
            print(f"LOG: {message}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
