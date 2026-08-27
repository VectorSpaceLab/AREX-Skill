#!/usr/bin/env python3
"""Validate OpenFold precomputed alignment directories and alignment DB indexes."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ORDINARY_MSA_EXTENSIONS = {".a3m", ".sto"}
TEMPLATE_EXTENSIONS = {".hhr"}
ORDINARY_STO_EXCLUSIONS = {"uniprot_hits", "hmm_output"}
COMMON_MSA_NAMES = {
    "bfd_uniclust_hits.a3m",
    "mgnify_hits.a3m",
    "mgnify_hits.sto",
    "uniref90_hits.a3m",
    "uniref90_hits.sto",
}
COMMON_TEMPLATE_NAMES = {
    "pdb70_hits.hhr",
    "hhsearch_output.hhr",
    "hmm_output.sto",
    "hmmsearch_output.sto",
}
MULTIMER_EXTRA_NAMES = {"uniprot_hits.sto"}
CHAIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*_[A-Za-z0-9][A-Za-z0-9_.-]*$")
PROTEIN_SEQUENCE_RE = re.compile(r"^[A-Za-z*.-]+$")


def issue(severity: str, message: str, path: Path | None = None) -> dict[str, str]:
    item = {"severity": severity, "message": message}
    if path is not None:
        item["path"] = str(path)
    return item


def parse_fasta_records(path: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(">"):
                description = line[1:].strip()
                if not description:
                    raise ValueError(f"Empty FASTA header at line {line_number} in {path}")
                current = {"description": description, "sequence": ""}
                records.append(current)
                continue
            if current is None:
                raise ValueError(f"Sequence data appears before first FASTA header at line {line_number} in {path}")
            current["sequence"] += line
    if not records:
        raise ValueError(f"No FASTA records found in {path}")
    return records


def fasta_key(description: str, key_mode: str) -> str:
    if key_mode == "first-token":
        return description.split()[0]
    return description


def is_ordinary_msa_name(name: str) -> bool:
    path = Path(name)
    suffix = path.suffix.lower()
    stem = path.stem
    if suffix == ".a3m":
        return True
    if suffix == ".sto" and stem not in ORDINARY_STO_EXCLUSIONS:
        return True
    return False


def is_template_name(name: str, index_backed: bool | None = None) -> bool:
    suffix = Path(name).suffix.lower()
    if suffix in TEMPLATE_EXTENSIONS:
        return True
    if index_backed is True:
        return name == "hmmsearch_output.sto"
    if index_backed is False:
        return name == "hmm_output.sto"
    return name in COMMON_TEMPLATE_NAMES


def is_alignment_related_name(name: str) -> bool:
    suffix = Path(name).suffix.lower()
    return suffix in {".a3m", ".sto", ".hhr", ".pt"}


def sniff_alignment_file(path: Path) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    if path.stat().st_size == 0:
        warnings.append(issue("warning", "Alignment-related file is empty", path))
        return warnings
    try:
        with path.open("rb") as handle:
            sample = handle.read(4096).decode("utf-8", errors="replace")
    except OSError as exc:
        warnings.append(issue("warning", f"Could not read file sample: {exc}", path))
        return warnings
    stripped = sample.lstrip()
    suffix = path.suffix.lower()
    if suffix == ".a3m" and not stripped.startswith(">"):
        warnings.append(issue("warning", "A3M file sample does not start with a FASTA-style header", path))
    if suffix == ".sto":
        has_pair_line = any(
            line.strip()
            and not line.lstrip().startswith(("#", "//"))
            and len(line.split()) >= 2
            for line in sample.splitlines()
        )
        if not has_pair_line:
            warnings.append(issue("warning", "Stockholm file sample has no sequence rows", path))
    if suffix == ".hhr" and "No " not in sample and "Hit" not in sample and "Query" not in sample:
        warnings.append(issue("warning", "HHR file sample lacks common HHsearch markers", path))
    return warnings


def inspect_alignment_dir(
    path: Path,
    allow_empty_msa: bool,
    require_seqemb: bool,
    require_uniprot: bool,
    sniff_files: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "files": [],
        "msa_files": [],
        "template_files": [],
        "seqemb_files": [],
        "warnings": [],
        "errors": [],
    }
    if not path.exists():
        result["errors"].append(issue("error", "Alignment directory does not exist", path))
        return result
    if not path.is_dir():
        result["errors"].append(issue("error", "Alignment path is not a directory", path))
        return result

    for child in sorted(path.iterdir()):
        if not child.is_file():
            continue
        result["files"].append(child.name)
        if is_ordinary_msa_name(child.name):
            result["msa_files"].append(child.name)
        elif is_template_name(child.name, index_backed=False):
            result["template_files"].append(child.name)
        elif child.suffix.lower() == ".pt":
            result["seqemb_files"].append(child.name)
        if is_alignment_related_name(child.name):
            if child.stat().st_size == 0:
                result["warnings"].append(issue("warning", "Alignment-related file is empty", child))
            elif sniff_files:
                result["warnings"].extend(sniff_alignment_file(child))

    if not result["msa_files"] and not allow_empty_msa:
        result["errors"].append(issue("error", "No supported ordinary MSA files found", path))
    if require_seqemb and not result["seqemb_files"]:
        result["errors"].append(issue("error", "Sequence-embedding mode requested but no .pt files found", path))
    if require_uniprot and "uniprot_hits.sto" not in result["files"]:
        result["errors"].append(issue("error", "Heteromeric multimer validation requires uniprot_hits.sto", path))
    if not any(name in result["files"] for name in COMMON_MSA_NAMES | COMMON_TEMPLATE_NAMES | MULTIMER_EXTRA_NAMES):
        result["warnings"].append(issue("warning", "No common OpenFold alignment filenames found", path))
    if not result["template_files"]:
        result["warnings"].append(issue("warning", "No template hit files found; template features may be empty", path))
    if "hmmsearch_output.sto" in result["files"]:
        result["warnings"].append(issue("warning", "Directory-backed HMMsearch templates are expected as hmm_output.sto, not hmmsearch_output.sto", path))
    return result


def add_fasta_report(report: dict[str, Any], fasta_path: Path, key_mode: str) -> list[dict[str, str]]:
    records = parse_fasta_records(fasta_path)
    report["fasta_records"] = len(records)
    report["fasta_descriptions"] = [record["description"] for record in records]
    report["fasta_keys"] = [fasta_key(record["description"], key_mode) for record in records]
    for record in records:
        if not record["sequence"]:
            report["errors"].append(issue("error", f"Empty FASTA sequence for {record['description']}", fasta_path))
        elif not PROTEIN_SEQUENCE_RE.match(record["sequence"]):
            report["warnings"].append(issue("warning", f"FASTA sequence has unusual characters for {record['description']}", fasta_path))
        if " " in record["description"] or "\t" in record["description"]:
            report["warnings"].append(issue("warning", f"FASTA description contains whitespace: {record['description']!r}", fasta_path))
    if len(set(report["fasta_keys"])) != len(report["fasta_keys"]):
        report["errors"].append(issue("error", "FASTA keys are not unique after applying --fasta-key-mode", fasta_path))
    return records


def is_heteromer(records: list[dict[str, str]]) -> bool:
    return len(records) > 1 and len({record["sequence"] for record in records}) > 1


def validate_monomer(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"mode": args.mode, "errors": [], "warnings": [], "directories": []}
    if args.fasta:
        try:
            records = add_fasta_report(report, args.fasta, args.fasta_key_mode)
        except (OSError, ValueError) as exc:
            records = []
            report["errors"].append(issue("error", str(exc), args.fasta))
        if records and len(records) != 1:
            report["errors"].append(issue("error", "Monomer mode expects exactly one FASTA record", args.fasta))
    directory_report = inspect_alignment_dir(
        args.alignment_dir,
        args.allow_empty_msa,
        args.require_seqemb,
        require_uniprot=False,
        sniff_files=args.sniff_files,
    )
    report["directories"].append(directory_report)
    report["errors"].extend(directory_report["errors"])
    report["warnings"].extend(directory_report["warnings"])
    return report


def validate_multimer_like(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"mode": args.mode, "errors": [], "warnings": [], "directories": []}
    if not args.fasta:
        report["errors"].append(issue("error", f"{args.mode} mode requires --fasta"))
        return report
    try:
        records = add_fasta_report(report, args.fasta, args.fasta_key_mode)
    except (OSError, ValueError) as exc:
        report["errors"].append(issue("error", str(exc), args.fasta))
        return report

    if len(records) < 2 and args.mode == "multimer":
        report["warnings"].append(issue("warning", "Multimer mode usually has two or more FASTA records", args.fasta))
    heteromer = is_heteromer(records)
    report["heteromeric_sequences"] = heteromer
    require_uniprot = heteromer and args.mode == "multimer" and not args.allow_missing_uniprot

    for key in report["fasta_keys"]:
        chain_dir = args.alignment_dir / key
        directory_report = inspect_alignment_dir(
            chain_dir,
            args.allow_empty_msa,
            args.require_seqemb,
            require_uniprot=require_uniprot,
            sniff_files=args.sniff_files,
        )
        if directory_report["exists"] and args.mode == "multimer" and "uniprot_hits.sto" not in directory_report["files"]:
            directory_report["warnings"].append(issue("warning", "No uniprot_hits.sto found for multimer all-sequence pairing", chain_dir))
        report["directories"].append(directory_report)
        report["errors"].extend(directory_report["errors"])
        report["warnings"].extend(directory_report["warnings"])
    return report


def validate_training_dir(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"mode": args.mode, "errors": [], "warnings": [], "directories": []}
    if not args.alignment_dir.exists() or not args.alignment_dir.is_dir():
        report["errors"].append(issue("error", "Training alignment directory does not exist or is not a directory", args.alignment_dir))
        return report
    chain_dirs = [child for child in sorted(args.alignment_dir.iterdir()) if child.is_dir()]
    report["chain_dir_count"] = len(chain_dirs)
    if not chain_dirs:
        report["errors"].append(issue("error", "No chain subdirectories found", args.alignment_dir))
    limit = args.max_chains if args.max_chains and args.max_chains > 0 else len(chain_dirs)
    for chain_dir in chain_dirs[:limit]:
        if not CHAIN_ID_RE.match(chain_dir.name):
            report["warnings"].append(issue("warning", "Chain directory name does not look like <pdb_id>_<chain_id>", chain_dir))
        directory_report = inspect_alignment_dir(
            chain_dir,
            args.allow_empty_msa,
            args.require_seqemb,
            require_uniprot=False,
            sniff_files=args.sniff_files,
        )
        report["directories"].append(directory_report)
        report["errors"].extend(directory_report["errors"])
        report["warnings"].extend(directory_report["warnings"])
    if limit < len(chain_dirs):
        report["warnings"].append(issue("warning", f"Checked first {limit} of {len(chain_dirs)} chain directories"))
    duplicate_result = validate_duplicate_groups(args.duplicate_chains_file, {path.name for path in chain_dirs}, "alignment directory")
    absorb_duplicate_result(report, duplicate_result)
    return report


def load_index(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Alignment index must be a JSON object")
    return data


def validate_index_entry(
    chain_id: str,
    entry: Any,
    args: argparse.Namespace,
    shard_sizes: dict[str, int | None],
    report: dict[str, Any],
    require_uniprot: bool,
) -> None:
    if not isinstance(entry, dict):
        report["errors"].append(issue("error", f"Index entry for {chain_id} is not an object", args.alignment_index))
        return
    db_name = entry.get("db")
    files = entry.get("files")
    if not isinstance(db_name, str) or not db_name:
        report["errors"].append(issue("error", f"Index entry for {chain_id} has invalid db field", args.alignment_index))
        return
    if os.path.isabs(db_name):
        report["errors"].append(issue("error", f"Index entry for {chain_id} uses an absolute shard path", args.alignment_index))
    db_path = args.alignment_dir / db_name
    if db_name not in shard_sizes:
        shard_sizes[db_name] = db_path.stat().st_size if db_path.exists() and db_path.is_file() else None
    shard_size = shard_sizes[db_name]
    if shard_size is None:
        report["errors"].append(issue("error", f"Shard file {db_name} is missing", db_path))
    if not isinstance(files, list) or not files:
        report["errors"].append(issue("error", f"Index entry for {chain_id} has no files list", args.alignment_index))
        return
    has_msa = False
    has_uniprot = False
    has_template = False
    for file_record in files:
        if not (isinstance(file_record, list) and len(file_record) == 3):
            report["errors"].append(issue("error", f"Invalid file record for {chain_id}: {file_record!r}", args.alignment_index))
            continue
        name, start, size = file_record
        if not isinstance(name, str):
            report["errors"].append(issue("error", f"Invalid filename in index entry for {chain_id}", args.alignment_index))
            continue
        if is_ordinary_msa_name(name):
            has_msa = True
        if name == "uniprot_hits.sto":
            has_uniprot = True
        if is_template_name(name, index_backed=True):
            has_template = True
        if name == "hmm_output.sto":
            report["warnings"].append(issue("warning", f"Index entry for {chain_id} uses hmm_output.sto; index-backed HMMsearch templates are expected as hmmsearch_output.sto", args.alignment_index))
        if not isinstance(start, int) or not isinstance(size, int) or start < 0 or size < 0:
            report["errors"].append(issue("error", f"Invalid byte range for {chain_id}:{name}", args.alignment_index))
            continue
        if shard_size is not None and start + size > shard_size:
            report["errors"].append(issue("error", f"Byte range for {chain_id}:{name} exceeds shard size", db_path))
        if size == 0:
            report["warnings"].append(issue("warning", f"Zero-length alignment record for {chain_id}:{name}", args.alignment_index))
    if not has_msa and not args.allow_empty_msa:
        report["errors"].append(issue("error", f"Index entry for {chain_id} has no supported ordinary MSA records", args.alignment_index))
    if require_uniprot and not has_uniprot:
        report["errors"].append(issue("error", f"Index entry for {chain_id} lacks uniprot_hits.sto required for heteromeric multimer pairing", args.alignment_index))
    if not has_template:
        report["warnings"].append(issue("warning", f"Index entry for {chain_id} has no recognized template hit records", args.alignment_index))
    if not CHAIN_ID_RE.match(str(chain_id)):
        report["warnings"].append(issue("warning", f"Index key {chain_id!r} does not look like <pdb_id>_<chain_id>", args.alignment_index))


def validate_index(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"mode": args.mode, "errors": [], "warnings": [], "entries_checked": 0, "entries_total": 0}
    if args.alignment_index is None:
        report["errors"].append(issue("error", "Index mode requires --alignment-index"))
        return report
    try:
        index = load_index(args.alignment_index)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report["errors"].append(issue("error", f"Could not load alignment index: {exc}", args.alignment_index))
        return report

    records: list[dict[str, str]] = []
    fasta_keys: list[str] = []
    if args.fasta:
        try:
            records = add_fasta_report(report, args.fasta, args.fasta_key_mode)
            fasta_keys = report["fasta_keys"]
        except (OSError, ValueError) as exc:
            report["errors"].append(issue("error", str(exc), args.fasta))
    heteromer = is_heteromer(records) if records else False
    report["heteromeric_sequences"] = heteromer
    require_uniprot = heteromer and not args.allow_missing_uniprot

    report["entries_total"] = len(index)
    if not index:
        report["errors"].append(issue("error", "Alignment index is empty", args.alignment_index))
        return report
    if fasta_keys:
        missing = [key for key in fasta_keys if key not in index]
        if missing:
            report["errors"].append(issue("error", "FASTA keys missing from alignment index: " + ", ".join(missing), args.alignment_index))
        items = [(key, index[key]) for key in fasta_keys if key in index]
    else:
        items = list(index.items())
    limit = args.max_chains if args.max_chains and args.max_chains > 0 else len(items)
    shard_sizes: dict[str, int | None] = {}
    for chain_id, entry in items[:limit]:
        report["entries_checked"] += 1
        validate_index_entry(str(chain_id), entry, args, shard_sizes, report, require_uniprot)
    if limit < len(items):
        report["warnings"].append(issue("warning", f"Checked first {limit} of {len(items)} selected index entries"))
    report["shards_seen"] = sorted(shard_sizes)
    duplicate_result = validate_duplicate_groups(args.duplicate_chains_file, {str(key) for key in index}, "alignment index")
    absorb_duplicate_result(report, duplicate_result)
    return report


def read_duplicate_groups(path: Path | None) -> list[list[str]]:
    if path is None:
        return []
    groups: list[list[str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if stripped and not stripped.startswith("#"):
                groups.append(stripped.split())
    return groups


def validate_duplicate_groups(path: Path | None, present_ids: set[str], present_label: str) -> dict[str, Any]:
    result: dict[str, Any] = {"duplicate_group_count": 0, "duplicate_groups_without_representative": 0, "duplicate_aliases_present": 0}
    if path is None:
        return result
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    try:
        groups = read_duplicate_groups(path)
    except OSError as exc:
        result["errors"] = [issue("error", f"Could not read duplicate-chain file: {exc}", path)]
        result["warnings"] = []
        return result
    result["duplicate_group_count"] = len(groups)
    present_upper = {chain.upper(): chain for chain in present_ids}
    missing_representative: list[str] = []
    aliases_present = 0
    for group in groups:
        if not group:
            continue
        present = [chain for chain in group if chain in present_ids or chain.upper() in present_upper]
        if not present:
            missing_representative.append(" ".join(group))
        else:
            aliases_present += max(0, len(present) - 1)
    result["duplicate_groups_without_representative"] = len(missing_representative)
    result["duplicate_aliases_present"] = aliases_present
    if missing_representative:
        warnings.append(issue("warning", f"Duplicate groups without any representative in {present_label}: " + "; ".join(missing_representative[:10]), path))
    result["warnings"] = warnings
    result["errors"] = errors
    return result



def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"mode: {report.get('mode')}")
    if "fasta_records" in report:
        print(f"fasta_records: {report['fasta_records']}")
        print("fasta_keys: " + ", ".join(report.get("fasta_keys", [])))
    if "chain_dir_count" in report:
        print(f"chain_dir_count: {report['chain_dir_count']}")
    if "entries_total" in report:
        print(f"index_entries: {report['entries_checked']}/{report['entries_total']}")
    if "duplicate_group_count" in report and report["duplicate_group_count"]:
        print(f"duplicate_group_count: {report['duplicate_group_count']}")
        print(f"duplicate_groups_without_representative: {report.get('duplicate_groups_without_representative', 0)}")
    for directory in report.get("directories", []):
        print(f"directory: {directory['path']}")
        print(f"  msa_files: {', '.join(directory['msa_files']) or '-'}")
        print(f"  template_files: {', '.join(directory['template_files']) or '-'}")
        print(f"  seqemb_files: {', '.join(directory['seqemb_files']) or '-'}")
    for warning in report.get("warnings", []):
        print(f"WARNING: {warning['message']}" + (f" [{warning['path']}]" if "path" in warning else ""))
    for error in report.get("errors", []):
        print(f"ERROR: {error['message']}" + (f" [{error['path']}]" if "path" in error else ""))
    if not report.get("errors"):
        print("validation: ok")


def absorb_duplicate_result(report: dict[str, Any], duplicate_result: dict[str, Any]) -> None:
    report["duplicate_group_count"] = duplicate_result.get("duplicate_group_count", 0)
    report["duplicate_groups_without_representative"] = duplicate_result.get("duplicate_groups_without_representative", 0)
    report["duplicate_aliases_present"] = duplicate_result.get("duplicate_aliases_present", 0)
    report.setdefault("errors", []).extend(duplicate_result.get("errors", []))
    report.setdefault("warnings", []).extend(duplicate_result.get("warnings", []))



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["monomer", "multimer", "multiseq", "training-dir", "index"], required=True)
    parser.add_argument("--alignment-dir", type=Path, required=True, help="Alignment directory or alignment DB shard directory")
    parser.add_argument("--alignment-index", type=Path, help="Path to alignment_db.index for --mode index")
    parser.add_argument("--fasta", type=Path, help="FASTA file for monomer, multimer, multiseq, or index key validation")
    parser.add_argument("--fasta-key-mode", choices=["full", "first-token"], default="full", help="How FASTA descriptions map to alignment keys")
    parser.add_argument("--duplicate-chains-file", type=Path, help="Optional duplicate_pdb_chains.txt coverage check")
    parser.add_argument("--allow-empty-msa", action="store_true", help="Do not fail when no ordinary MSA files are present")
    parser.add_argument("--allow-missing-uniprot", action="store_true", help="Warn instead of failing when heteromer multimer inputs lack uniprot_hits.sto")
    parser.add_argument("--require-seqemb", action="store_true", help="Require at least one .pt sequence embedding file")
    parser.add_argument("--sniff-files", action="store_true", help="Read small file samples for lightweight format sanity warnings")
    parser.add_argument("--max-chains", type=int, default=0, help="Limit chain/index entries checked for large datasets; 0 checks all selected entries")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    if args.mode == "monomer":
        report = validate_monomer(args)
    elif args.mode in {"multimer", "multiseq"}:
        if args.mode == "multiseq" and args.fasta_key_mode == "full":
            args.fasta_key_mode = "first-token"
        report = validate_multimer_like(args)
    elif args.mode == "training-dir":
        report = validate_training_dir(args)
    else:
        report = validate_index(args)

    print_report(report, args.json)
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
