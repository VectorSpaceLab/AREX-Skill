#!/usr/bin/env python3
"""Validate REINVENT4 enumeration and seed files without running REINVENT4."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]

ATTACHMENT_RE = re.compile(r"\[\*:?\d*\]|\*")
RESERVED_SMILES_COLUMN = "RDKit_SMILES (REINVENT)"
CURRENT_ENUM_KEYS = {
    "smiles_file",
    "output_csv",
    "amino_acid_library_file",
    "smiles_column",
    "aa_names_column",
    "batch_size",
}
LEGACY_ENUM_KEY_HINTS = {
    "amino_acid_library": "amino_acid_library_file",
    "amino_acid_name_column": "aa_names_column",
}


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "message": self.message}


class Validator:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, message: str) -> None:
        self.findings.append(Finding("ERROR", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    def info(self, message: str) -> None:
        self.findings.append(Finding("INFO", message))

    @property
    def has_errors(self) -> bool:
        return any(finding.level == "ERROR" for finding in self.findings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely validate REINVENT4 enumeration configs and seed files without running jobs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="Config or seed file to validate.")
    parser.add_argument(
        "--kind",
        choices=("auto", "enumeration", "scaffolds", "warheads", "mol2mol", "pepinvent", "amino-acid-library"),
        default="auto",
        help="Input kind; auto treats TOML/JSON/YAML as enumeration config and .smi as generic seed files.",
    )
    parser.add_argument(
        "--config-format",
        choices=("auto", "toml", "json", "yaml", "yml"),
        default="auto",
        help="Force config format when validating an enumeration config.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Resolve relative paths against this directory; config validation defaults to the config parent.",
    )
    parser.add_argument(
        "--smiles-column",
        default="SMILES",
        help="SMILES column to check when --kind amino-acid-library is used directly.",
    )
    parser.add_argument(
        "--name-column",
        default="Name",
        help="Amino-acid name column to check when --kind amino-acid-library is used directly.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary.",
    )
    return parser.parse_args()


def infer_kind(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if path.suffix.lower() in {".toml", ".json", ".yaml", ".yml"}:
        return "enumeration"
    name = path.name.lower()
    if "scaffold" in name:
        return "scaffolds"
    if "warhead" in name:
        return "warheads"
    if "mol2mol" in name or "m2m" in name:
        return "mol2mol"
    if "pepinvent" in name or "peptide" in name:
        return "pepinvent"
    if path.suffix.lower() == ".csv":
        return "amino-acid-library"
    return "pepinvent"


def load_config(path: Path, config_format: str) -> dict[str, Any]:
    fmt = config_format
    if fmt == "auto":
        fmt = path.suffix.lower().lstrip(".") or "toml"
    if fmt == "yml":
        fmt = "yaml"
    if fmt == "toml":
        if tomllib is None:
            raise RuntimeError("TOML parsing requires Python 3.11+ tomllib")
        with path.open("rb") as handle:
            return tomllib.load(handle)
    if fmt == "json":
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if fmt == "yaml":
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise RuntimeError("YAML parsing requires PyYAML; use TOML/JSON or install PyYAML") from exc
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
            return loaded or {}
    raise RuntimeError(f"Unsupported config format: {fmt}")


def resolve_path(value: Any, base_dir: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def read_seed_rows(path: Path, validator: Validator) -> list[tuple[int, str]]:
    if not path.exists():
        validator.error(f"File does not exist: {path}")
        return []
    if not path.is_file():
        validator.error(f"Path is not a file: {path}")
        return []

    rows: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append((line_number, line))
    if not rows:
        validator.error(f"No non-comment rows found in {path}")
    return rows


def first_field(row: str) -> str:
    for delimiter in ("\t", ",", " "):
        if delimiter in row:
            return row.split(delimiter, 1)[0].strip()
    return row.strip()


def count_attachment_points(text: str) -> int:
    return len(ATTACHMENT_RE.findall(text))


def rdkit_mol_from_smiles(smiles: str) -> tuple[bool | None, str | None]:
    try:
        from rdkit import Chem  # type: ignore[import-not-found]
    except Exception:
        return None, "RDKit not available; skipped molecule parse"
    try:
        mol = Chem.MolFromSmiles(smiles)
    except Exception as exc:  # pragma: no cover - defensive around RDKit internals
        return False, f"RDKit parse raised {exc.__class__.__name__}: {exc}"
    if mol is None:
        return False, "RDKit returned no molecule"
    return True, None


def strip_attachment_markers(smiles: str) -> str:
    stripped = re.sub(r"\[\*:?[0-9]*\]", "", smiles)
    stripped = stripped.replace("*", "")
    return stripped or smiles


def validate_scaffolds(path: Path, validator: Validator) -> dict[str, Any]:
    rows = read_seed_rows(path, validator)
    summaries: list[dict[str, Any]] = []
    rdkit_skip_note: str | None = None
    for line_number, row in rows:
        scaffold = first_field(row)
        attachments = count_attachment_points(scaffold)
        if attachments == 0:
            validator.error(f"line {line_number}: scaffold has no attachment point marker")
        elif attachments == 1:
            validator.warn(f"line {line_number}: scaffold has one attachment point; many LibInvent scaffolds use two")
        parse_target = strip_attachment_markers(scaffold)
        parsed, note = rdkit_mol_from_smiles(parse_target)
        if parsed is False:
            validator.warn(f"line {line_number}: RDKit could not parse scaffold after removing attachment markers: {note}")
        elif parsed is None and note and rdkit_skip_note is None:
            rdkit_skip_note = note
        summaries.append({"line": line_number, "attachments": attachments})
    if rdkit_skip_note:
        validator.info(rdkit_skip_note)
    validator.info(f"Checked {len(rows)} scaffold row(s)")
    return {"rows": len(rows), "row_summaries": summaries}


def validate_warheads(path: Path, validator: Validator) -> dict[str, Any]:
    rows = read_seed_rows(path, validator)
    summaries: list[dict[str, Any]] = []
    rdkit_skip_note: str | None = None
    for line_number, row in rows:
        if row.count("|") != 1:
            validator.error(f"line {line_number}: warhead row must contain exactly one '|' separator")
            parts = row.split("|")
        else:
            parts = row.split("|")
        part_counts: list[int] = []
        for index, part in enumerate(parts, start=1):
            part = part.strip()
            attachments = count_attachment_points(part)
            part_counts.append(attachments)
            if not part:
                validator.error(f"line {line_number}: warhead side {index} is empty")
            if attachments == 0:
                validator.error(f"line {line_number}: warhead side {index} has no attachment point")
            elif attachments > 1:
                validator.warn(f"line {line_number}: warhead side {index} has {attachments} attachment points; expected one")
            parse_target = strip_attachment_markers(part)
            parsed, note = rdkit_mol_from_smiles(parse_target)
            if parsed is False:
                validator.warn(f"line {line_number}: RDKit could not parse warhead side {index}: {note}")
            elif parsed is None and note and rdkit_skip_note is None:
                rdkit_skip_note = note
        summaries.append({"line": line_number, "attachment_counts": part_counts})
    if rdkit_skip_note:
        validator.info(rdkit_skip_note)
    validator.info(f"Checked {len(rows)} warhead row(s)")
    return {"rows": len(rows), "row_summaries": summaries}


def validate_mol2mol(path: Path, validator: Validator) -> dict[str, Any]:
    rows = read_seed_rows(path, validator)
    parsed_count = 0
    rdkit_skip_note: str | None = None
    for line_number, row in rows:
        smiles = first_field(row)
        if not smiles:
            validator.error(f"line {line_number}: first column is empty")
            continue
        parsed, note = rdkit_mol_from_smiles(smiles)
        if parsed is False:
            validator.error(f"line {line_number}: RDKit could not parse first-column molecule: {note}")
        elif parsed is True:
            parsed_count += 1
        elif note and rdkit_skip_note is None:
            rdkit_skip_note = note
    if len(rows) > 1000:
        validator.warn(f"Mol2Mol seed file has {len(rows)} rows; large seed sets can be memory-heavy")
    if rdkit_skip_note:
        validator.info(rdkit_skip_note)
    validator.info(f"Checked {len(rows)} Mol2Mol row(s)")
    return {"rows": len(rows), "rdkit_parsed_rows": parsed_count}


def validate_pepinvent(path: Path, validator: Validator, *, enumeration: bool = False) -> dict[str, Any]:
    rows = read_seed_rows(path, validator)
    mask_counts: list[int] = []
    for line_number, row in rows:
        peptide = first_field(row)
        mask_count = peptide.count("?")
        mask_counts.append(mask_count)
        if mask_count == 0:
            validator.error(f"line {line_number}: peptide row has no '?' mask")
        if enumeration and mask_count > 2:
            validator.error(f"line {line_number}: enumeration supports at most two '?' masks")
        if "|" not in peptide:
            validator.warn(f"line {line_number}: peptide row has no '|' fragment separator")
        if peptide.count("||"):
            validator.warn(f"line {line_number}: peptide row contains an empty fragment between '|' separators")
        if "*" in peptide:
            validator.warn(f"line {line_number}: peptide row contains '*'; PepInvent/enumeration masks should use '?'")
    if enumeration and len(rows) > 1:
        first_masks = mask_counts[0] if mask_counts else 0
        different = [count for count in mask_counts if count != first_masks]
        validator.warn(
            "enumeration iterator is built from the first parsed template; multiple template rows should be smoke-tested carefully"
        )
        if different:
            validator.error("not all peptide template rows have the same '?' mask count as the first row")
    validator.info(f"Checked {len(rows)} peptide row(s)")
    return {"rows": len(rows), "mask_counts": mask_counts}


def validate_amino_acid_library(path: Path, validator: Validator, name_column: str, smiles_column: str) -> dict[str, Any]:
    if not path.exists():
        validator.error(f"Amino-acid library does not exist: {path}")
        return {"rows": 0}
    if smiles_column == RESERVED_SMILES_COLUMN:
        validator.error(f"smiles_column {RESERVED_SMILES_COLUMN!r} is reserved by REINVENT4 scoring output")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if name_column not in fieldnames:
            validator.error(f"amino-acid library missing name column {name_column!r}; columns are {fieldnames}")
        if smiles_column not in fieldnames:
            validator.error(f"amino-acid library missing SMILES column {smiles_column!r}; columns are {fieldnames}")
        if name_column not in fieldnames or smiles_column not in fieldnames:
            return {"rows": 0, "columns": fieldnames}

        names_seen: set[str] = set()
        duplicate_names: set[str] = set()
        row_count = 0
        parsed_count = 0
        rdkit_skip_note: str | None = None
        for row_number, row in enumerate(reader, start=2):
            row_count += 1
            name = (row.get(name_column) or "").strip()
            smiles = (row.get(smiles_column) or "").strip()
            if not name:
                validator.error(f"library row {row_number}: empty amino-acid name")
            elif name in names_seen:
                duplicate_names.add(name)
            names_seen.add(name)
            if not smiles:
                validator.error(f"library row {row_number}: empty amino-acid SMILES")
                continue
            parsed, note = rdkit_mol_from_smiles(smiles)
            if parsed is False:
                validator.warn(f"library row {row_number}: RDKit could not parse amino-acid SMILES: {note}")
            elif parsed is True:
                parsed_count += 1
            elif note and rdkit_skip_note is None:
                rdkit_skip_note = note

    if rdkit_skip_note:
        validator.info(rdkit_skip_note)
    for name in sorted(duplicate_names):
        validator.warn(f"duplicate amino-acid name {name!r}; runtime dictionary keeps the last value")
    if row_count == 0:
        validator.error("amino-acid library has no data rows")
    validator.info(f"Checked {row_count} amino-acid library row(s)")
    return {"rows": row_count, "columns": fieldnames, "unique_names": len(names_seen), "rdkit_parsed_rows": parsed_count}


def validate_enumeration_config(path: Path, validator: Validator, config_format: str, base_dir_arg: Path | None) -> dict[str, Any]:
    if not path.exists():
        validator.error(f"Config file does not exist: {path}")
        return {}
    config = load_config(path, config_format)
    if not isinstance(config, dict):
        validator.error("Config root must be a mapping/object")
        return {}

    base_dir = (base_dir_arg or path.parent).resolve()
    run_type = config.get("run_type")
    if run_type != "enumeration":
        validator.error(f"run_type must be 'enumeration', found {run_type!r}")

    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        validator.error("Config must contain a [parameters] mapping")
        return {"run_type": run_type}

    for legacy_key, current_key in LEGACY_ENUM_KEY_HINTS.items():
        if legacy_key in parameters:
            validator.error(f"[parameters].{legacy_key} is not the current runtime key; use {current_key}")

    unknown = sorted(set(parameters) - CURRENT_ENUM_KEYS - set(LEGACY_ENUM_KEY_HINTS))
    if unknown:
        validator.warn(f"Unknown enumeration [parameters] keys: {', '.join(unknown)}")

    smiles_path = resolve_path(parameters.get("smiles_file"), base_dir)
    library_path = resolve_path(parameters.get("amino_acid_library_file"), base_dir)
    output_path = resolve_path(parameters.get("output_csv", "score_results.csv"), base_dir)
    name_column = str(parameters.get("aa_names_column", "Name"))
    smiles_column = str(parameters.get("smiles_column", "SMILES"))
    batch_size = parameters.get("batch_size", 100)

    if smiles_path is None:
        validator.error("[parameters].smiles_file is required")
    if library_path is None:
        validator.error("[parameters].amino_acid_library_file is required")
    if not isinstance(batch_size, int) or batch_size < 1:
        validator.error("[parameters].batch_size must be a positive integer")
    if output_path is not None and output_path.exists():
        validator.warn(f"output_csv already exists and enumeration appends after the first batch: {output_path}")

    scoring = config.get("scoring")
    if not isinstance(scoring, dict):
        validator.error("Enumeration config must contain a [scoring] mapping")
    elif not scoring.get("type"):
        validator.warn("[scoring] has no aggregation type")

    seed_summary: dict[str, Any] = {}
    library_summary: dict[str, Any] = {}
    if smiles_path is not None:
        seed_summary = validate_pepinvent(smiles_path, validator, enumeration=True)
    if library_path is not None:
        library_summary = validate_amino_acid_library(library_path, validator, name_column, smiles_column)

    masks = seed_summary.get("mask_counts") or []
    library_rows = int(library_summary.get("unique_names") or 0)
    if masks and library_rows:
        combinations = library_rows ** int(masks[0])
        validator.info(f"Estimated combinations from first template: {library_rows}^{int(masks[0])} = {combinations}")
        if isinstance(batch_size, int) and batch_size > combinations and combinations > 0:
            validator.warn("batch_size is larger than estimated combinations; this is allowed but unnecessary")

    return {
        "run_type": run_type,
        "base_dir": str(base_dir),
        "parameters": {
            "smiles_file": str(smiles_path) if smiles_path else None,
            "amino_acid_library_file": str(library_path) if library_path else None,
            "aa_names_column": name_column,
            "smiles_column": smiles_column,
            "batch_size": batch_size,
            "output_csv": str(output_path) if output_path else None,
        },
        "seed_summary": seed_summary,
        "library_summary": library_summary,
    }


def print_text(payload: dict[str, Any]) -> None:
    print(f"Input: {payload['input']}")
    print(f"Kind: {payload['kind']}")
    summary = payload.get("summary") or {}
    if summary:
        print("Summary:")
        for key, value in summary.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                print(f"  {key}: {value}")
    print("Findings:")
    for finding in payload["findings"]:
        print(f"  {finding['level']}: {finding['message']}")
    print(f"Result: {'FAIL' if payload['has_errors'] else 'PASS'}")


def main() -> int:
    args = parse_args()
    validator = Validator()
    kind = infer_kind(args.path, args.kind)
    summary: dict[str, Any]

    try:
        if kind == "enumeration":
            summary = validate_enumeration_config(args.path, validator, args.config_format, args.base_dir)
        elif kind == "scaffolds":
            summary = validate_scaffolds(args.path, validator)
        elif kind == "warheads":
            summary = validate_warheads(args.path, validator)
        elif kind == "mol2mol":
            summary = validate_mol2mol(args.path, validator)
        elif kind == "pepinvent":
            summary = validate_pepinvent(args.path, validator)
        elif kind == "amino-acid-library":
            summary = validate_amino_acid_library(args.path, validator, args.name_column, args.smiles_column)
        else:  # pragma: no cover - argparse prevents this
            validator.error(f"Unsupported kind: {kind}")
            summary = {}
    except Exception as exc:
        validator.error(f"Validation failed: {exc}")
        summary = {}

    payload = {
        "input": str(args.path),
        "kind": kind,
        "summary": summary,
        "findings": [finding.as_dict() for finding in validator.findings],
        "has_errors": validator.has_errors,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)

    return 1 if validator.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
