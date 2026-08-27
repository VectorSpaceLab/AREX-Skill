#!/usr/bin/env python3
"""Read-only, deterministic preflight checks for AlphaFold 3 data layouts.

The validator checks explicitly supplied local paths, structure/MSA/template
extensions, lightweight CSV headers, cutoff-date syntax, and crop/config
consistency. It never imports alphafold3_pytorch, downloads or parses
biological data, writes or rewrites files, filters structures, clusters
sequences, starts workers or servers, runs Kalign, trains, or constructs a
sampler/dataset.

All paths are resolved relative to the caller's current working directory (or
as absolute paths), so the command is safe to invoke from any CWD. Exit status
is 0 when no errors are found and 1 when a supplied path or configuration is
invalid. Warnings, such as an intentionally empty optional MSA directory, do
not change the exit status unless the corresponding --require-* flag is used.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


STRUCTURE_SUFFIXES = (".cif", ".cif.gz")
MSA_SUFFIXES = (".a3m", ".a3m.gz")
TEMPLATE_SUFFIXES = (".m8", ".hhr")
CCD_SUFFIXES = (".cif", ".cif.gz", ".json")
CHAIN_COLUMNS = ("pdb_id", "chain_id", "molecule_id", "cluster_id")
INTERFACE_COLUMNS = (
    "pdb_id",
    "interface_chain_id_1",
    "interface_chain_id_2",
    "interface_molecule_id_1",
    "interface_molecule_id_2",
    "interface_chain_cluster_id_1",
    "interface_chain_cluster_id_2",
    "interface_cluster_id",
)
CROP_KEYS = (
    "contiguous_weight",
    "spatial_weight",
    "spatial_interface_weight",
    "n_res",
)


class Issues:
    """Collect stable, human-readable errors and warnings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def resolved(path_text: str) -> Path:
    """Resolve a user path without requiring it to exist."""
    return Path(path_text).expanduser().resolve(strict=False)


def has_suffix(path: Path, suffixes: Sequence[str]) -> bool:
    """Return whether a path has one of the supported compound suffixes."""
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in suffixes)


def strip_structure_suffix(path: Path) -> str:
    """Return the single-extension ID convention used by PDBDataset.

    The package calls ``os.path.splitext`` once. Consequently ``foo.cif``
    becomes ``foo`` but ``foo.cif.gz`` becomes ``foo.cif``; preserving this
    quirk prevents a preflight from approving a compressed layout that the
    sampler cannot match.
    """
    return os.path.splitext(path.name)[0]


def files_with_suffixes(path: Path, suffixes: Sequence[str]) -> list[Path]:
    """List matching files in deterministic order without changing the tree."""
    if path.is_file():
        return [path] if has_suffix(path, suffixes) else []
    if not path.is_dir():
        return []
    return sorted(
        (candidate for candidate in path.rglob("*") if candidate.is_file() and has_suffix(candidate, suffixes)),
        key=lambda item: item.as_posix(),
    )


def check_file_or_tree(
    issues: Issues,
    raw_path: str,
    label: str,
    suffixes: Sequence[str],
    *,
    allow_file: bool = True,
    require_match: bool = True,
    empty_is_warning: bool = False,
) -> tuple[Path | None, list[Path]]:
    """Check existence and extension conventions for a local file/tree."""
    path = resolved(raw_path)
    if not path.exists():
        issues.error(f"{label} does not exist: {path}")
        return path, []
    if path.is_file() and not allow_file:
        issues.error(f"{label} must be a directory, not a file: {path}")
        return path, []
    if path.is_file() and not has_suffix(path, suffixes):
        issues.error(
            f"{label} has unsupported extension: {path.name}; expected one of {', '.join(suffixes)}"
        )
        return path, []
    if not path.is_file() and not path.is_dir():
        issues.error(f"{label} is neither a regular file nor a directory: {path}")
        return path, []

    matches = files_with_suffixes(path, suffixes)
    if require_match and not matches:
        message = f"{label} contains no files with extensions {', '.join(suffixes)}: {path}"
        if empty_is_warning:
            issues.warning(message)
        else:
            issues.error(message)
    return path, matches


def check_csv_header(issues: Issues, raw_path: str, label: str, required: Sequence[str]) -> set[str]:
    """Read only the first CSV record and check required mapping columns."""
    path = resolved(raw_path)
    if not path.exists():
        issues.error(f"{label} does not exist: {path}")
        return set()
    if not path.is_file():
        issues.error(f"{label} must be a CSV file: {path}")
        return set()
    if path.suffix.lower() != ".csv":
        issues.error(f"{label} must use the .csv extension: {path}")
        return set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle), [])
    except (OSError, UnicodeError, csv.Error) as exc:
        issues.error(f"cannot read {label} header {path}: {exc}")
        return set()
    columns = {column.strip() for column in header if column.strip()}
    missing = [column for column in required if column not in columns]
    if missing:
        issues.error(f"{label} is missing required columns {', '.join(missing)}: {path}")
    return columns


def parse_crop_config(issues: Issues, value: str) -> dict[str, Any] | None:
    """Load a JSON object from an argument or a local @file reference."""
    source = value
    if value.startswith("@"):
        path = resolved(value[1:])
        if not path.is_file():
            issues.error(f"crop config file does not exist: {path}")
            return None
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.error(f"cannot read crop config file {path}: {exc}")
            return None
    try:
        config = json.loads(source)
    except json.JSONDecodeError as exc:
        issues.error(f"crop config must be a JSON object or @JSON_FILE: {exc.msg}")
        return None
    if not isinstance(config, dict):
        issues.error("crop config must decode to a JSON object")
        return None
    actual = set(config)
    expected = set(CROP_KEYS)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        issues.error("crop config keys are inconsistent: " + "; ".join(details))
        return None

    weights: list[float] = []
    for key in CROP_KEYS[:3]:
        value_at_key = config[key]
        if isinstance(value_at_key, bool) or not isinstance(value_at_key, (int, float)):
            issues.error(f"crop config {key} must be a finite number")
            continue
        number = float(value_at_key)
        if not math.isfinite(number):
            issues.error(f"crop config {key} must be finite")
        weights.append(number)
    n_res = config["n_res"]
    if isinstance(n_res, bool) or not isinstance(n_res, int) or n_res <= 0:
        issues.error("crop config n_res must be a positive integer")
    if len(weights) == 3 and sum(weights) != 1.0:
        issues.error(
            "crop config weights must sum exactly to 1.0, matching PDBInput validation"
        )
    return config


def check_iso_date(issues: Issues, raw_date: str | None, label: str) -> None:
    """Check the strict date spelling accepted by the documented contract."""
    if raw_date is None:
        return
    try:
        parsed = dt.datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        issues.error(f"{label} must use YYYY-MM-DD: {raw_date}")
        return
    if parsed.strftime("%Y-%m-%d") != raw_date:
        issues.error(f"{label} must use zero-padded YYYY-MM-DD: {raw_date}")


def positive_int_option(issues: Issues, value: int | None, label: str) -> None:
    """Check a positive integer CLI option."""
    if value is not None and value <= 0:
        issues.error(f"{label} must be greater than zero: {value}")


def structure_ids(structure_files: Iterable[Path]) -> set[str]:
    """Collect the basename IDs used by PDBDataset."""
    return {strip_structure_suffix(path) for path in structure_files}


def check_mapping_alignment(
    issues: Issues,
    mapping_paths: Sequence[str],
    structure_ids_seen: set[str],
    label: str,
) -> None:
    """Check mapping IDs against explicitly supplied local structures."""
    if not structure_ids_seen:
        return
    for raw_path in mapping_paths:
        path = resolved(raw_path)
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = csv.DictReader(handle)
                if rows.fieldnames is None or "pdb_id" not in rows.fieldnames:
                    continue
                missing: set[str] = set()
                for row in rows:
                    pdb_id = (row.get("pdb_id") or "").strip()
                    if pdb_id and pdb_id not in structure_ids_seen:
                        missing.add(pdb_id)
        except (OSError, UnicodeError, csv.Error) as exc:
            issues.error(f"cannot inspect {label} IDs {path}: {exc}")
            continue
        if missing:
            preview = ", ".join(sorted(missing)[:5])
            suffix = " ..." if len(missing) > 5 else ""
            issues.error(
                f"{label} references {len(missing)} PDB IDs absent from supplied mmCIF files "
                f"({preview}{suffix}): {path}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Perform deterministic, read-only checks for local AlphaFold 3 "
            "mmCIF/MSA/template/mapping paths and crop configuration."
        ),
        epilog=(
            "Examples: --mmcif-dir /data/pdb --msa-dir /data/msas "
            "--templates-dir /data/templates --crop-config '{\"contiguous_weight\":0.2,"
            "\"spatial_weight\":0.4,\"spatial_interface_weight\":0.4,\"n_res\":384}'"
        ),
    )
    parser.add_argument("--mmcif", action="append", default=[], metavar="PATH", help="A local .cif or .cif.gz structure file (repeatable).")
    parser.add_argument("--mmcif-dir", action="append", default=[], metavar="DIR", help="A local directory tree containing .cif/.cif.gz structures (repeatable).")
    parser.add_argument("--msa-dir", action="append", default=[], metavar="DIR", help="A local MSA directory containing .a3m/.a3m.gz files (repeatable).")
    parser.add_argument("--templates-dir", action="append", default=[], metavar="DIR", help="A local template directory containing .m8/.hhr files (repeatable).")
    parser.add_argument("--ccd-path", action="append", default=[], metavar="PATH", help="A local CCD .cif/.cif.gz or components_smiles.json path (repeatable).")
    parser.add_argument("--chain-mapping", action="append", default=[], metavar="CSV", help="A chain-cluster mapping CSV (repeatable).")
    parser.add_argument("--interface-mapping", metavar="CSV", help="The interface-cluster mapping CSV.")
    parser.add_argument("--crop-config", metavar="JSON_OR_@FILE", help="Four-key crop JSON, or @path to a local JSON file.")
    parser.add_argument("--cutoff-date", metavar="YYYY-MM-DD", help="A structure release cutoff date.")
    parser.add_argument("--template-cutoff-date", metavar="YYYY-MM-DD", help="A template release cutoff date.")
    parser.add_argument("--sample-type", choices=("default", "clustered"), default="default", help="PDBDataset sampling mode.")
    parser.add_argument("--filtered-pdb-clustering", action="store_true", help="Declare the one-based filtered-PDB clustering assumption.")
    parser.add_argument("--require-msa", action="store_true", help="Treat an empty MSA directory as an error instead of a query-only warning.")
    parser.add_argument("--require-templates", action="store_true", help="Treat an empty template directory as an error instead of a dummy-template warning.")
    parser.add_argument("--max-length", type=int, metavar="N", help="Configured PDBInput max_length.")
    parser.add_argument("--max-msas-per-chain", type=int, metavar="N", help="Configured MSA row cap.")
    parser.add_argument("--max-num-msa-tokens", type=int, metavar="N", help="Configured total MSA token cap.")
    parser.add_argument("--max-templates-per-chain", type=int, metavar="N", help="Configured template candidate cap.")
    parser.add_argument("--num-templates-per-chain", type=int, metavar="N", help="Configured template feature count.")
    parser.add_argument("--max-num-template-tokens", type=int, metavar="N", help="Configured total template token cap.")
    parser.add_argument("--batch-size", type=int, metavar="N", help="Weighted sampler batch size, if mapping files are supplied.")
    parser.add_argument("--json", action="store_true", help="Emit a deterministic JSON report instead of text.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    issues = Issues()

    all_structure_files: list[Path] = []
    for raw_path in args.mmcif:
        _, files = check_file_or_tree(
            issues, raw_path, "mmCIF path", STRUCTURE_SUFFIXES, allow_file=True, require_match=True
        )
        all_structure_files.extend(files)
    for raw_path in args.mmcif_dir:
        _, files = check_file_or_tree(
            issues, raw_path, "mmCIF directory", STRUCTURE_SUFFIXES, allow_file=False, require_match=True
        )
        all_structure_files.extend(files)

    # Repeatable feature directories are allowed to be empty only when the
    # operator has not requested those optional features as a requirement.
    for raw_path in args.msa_dir:
        check_file_or_tree(
            issues,
            raw_path,
            "MSA directory",
            MSA_SUFFIXES,
            allow_file=False,
            require_match=True,
            empty_is_warning=not args.require_msa,
        )
    for raw_path in args.templates_dir:
        check_file_or_tree(
            issues,
            raw_path,
            "template directory",
            TEMPLATE_SUFFIXES,
            allow_file=False,
            require_match=True,
            empty_is_warning=not args.require_templates,
        )
    for raw_path in args.ccd_path:
        check_file_or_tree(
            issues, raw_path, "CCD path", CCD_SUFFIXES, allow_file=True, require_match=True
        )

    for raw_path in args.chain_mapping:
        check_csv_header(issues, raw_path, "chain mapping", CHAIN_COLUMNS)
    if args.interface_mapping:
        check_csv_header(issues, args.interface_mapping, "interface mapping", INTERFACE_COLUMNS)
    if args.interface_mapping and not args.chain_mapping:
        issues.error("an interface mapping requires at least one chain mapping")
    if args.sample_type == "clustered" and not (args.chain_mapping and args.interface_mapping):
        issues.error("sample-type=clustered requires chain and interface mappings")
    if args.filtered_pdb_clustering and not args.mmcif_dir:
        issues.error("filtered-PDB clustering assumption requires --mmcif-dir")

    if args.crop_config:
        parse_crop_config(issues, args.crop_config)
    check_iso_date(issues, args.cutoff_date, "cutoff-date")
    check_iso_date(issues, args.template_cutoff_date, "template-cutoff-date")

    for value, label in (
        (args.max_length, "max-length"),
        (args.max_msas_per_chain, "max-msas-per-chain"),
        (args.max_num_msa_tokens, "max-num-msa-tokens"),
        (args.max_templates_per_chain, "max-templates-per-chain"),
        (args.num_templates_per_chain, "num-templates-per-chain"),
        (args.max_num_template_tokens, "max-num-template-tokens"),
        (args.batch_size, "batch-size"),
    ):
        positive_int_option(issues, value, label)
    if (
        args.max_templates_per_chain is not None
        and args.num_templates_per_chain is not None
        and args.num_templates_per_chain > args.max_templates_per_chain
    ):
        issues.warning(
            "num-templates-per-chain exceeds max-templates-per-chain; the loader will cap candidates before selection"
        )

    ids = structure_ids(all_structure_files)
    check_mapping_alignment(issues, args.chain_mapping, ids, "chain mapping")
    if args.interface_mapping:
        check_mapping_alignment(issues, [args.interface_mapping], ids, "interface mapping")

    # De-duplicate only for reporting. Input order remains deterministic and
    # the checks above never mutate a user path or data file.
    all_structure_files = sorted(set(all_structure_files), key=lambda item: item.as_posix())
    report: dict[str, Any] = {
        "status": "error" if issues.errors else "ok",
        "cwd": str(Path.cwd()),
        "structures_checked": len(all_structure_files),
        "errors": issues.errors,
        "warnings": issues.warnings,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"structures_checked: {report['structures_checked']}")
        for warning in issues.warnings:
            print(f"WARNING: {warning}")
        for error in issues.errors:
            print(f"ERROR: {error}")
        if not issues.errors and not issues.warnings:
            print("No errors or warnings.")
    return 1 if issues.errors else 0


if __name__ == "__main__":
    sys.exit(main())
