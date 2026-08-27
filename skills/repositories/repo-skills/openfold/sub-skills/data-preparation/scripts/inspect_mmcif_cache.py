#!/usr/bin/env python3
"""Inspect OpenFold mmCIF and chain cache JSON files for schema issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CHAIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*_[A-Za-z0-9][A-Za-z0-9_.-]*$")
STRUCTURE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROTEIN_SEQUENCE_RE = re.compile(r"^[A-Za-z*.-]+$")


def issue(severity: str, message: str, key: str | None = None) -> dict[str, str]:
    item = {"severity": severity, "message": message}
    if key is not None:
        item["key"] = key
    return item


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cluster_chains(path: Path | None) -> tuple[set[str], list[dict[str, str]], dict[str, int]]:
    chains: set[str] = set()
    warnings: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    if path is None:
        return chains, warnings, counts
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            members = stripped.split()
            if len(set(member.upper() for member in members)) != len(members):
                warnings.append(issue("warning", f"Cluster line {line_number} contains duplicate chain IDs", str(path)))
            for member in members:
                chains.add(member)
                counts[member.upper()] = counts.get(member.upper(), 0) + 1
    repeated = sorted(chain for chain, count in counts.items() if count > 1)
    if repeated:
        warnings.append(issue("warning", "Cluster chains appear in multiple clusters: " + ", ".join(repeated[:20]), str(path)))
    return chains, warnings, counts


def load_duplicate_groups(path: Path | None) -> tuple[list[list[str]], list[dict[str, str]]]:
    if path is None:
        return [], []
    groups: list[list[str]] = []
    warnings: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            group = stripped.split()
            if len(set(member.upper() for member in group)) != len(group):
                warnings.append(issue("warning", f"Duplicate-chain line {line_number} repeats a chain ID", str(path)))
            groups.append(group)
    return groups, warnings


def validate_release_date(value: Any, key: str, require_release_dates: bool, report: dict[str, Any]) -> None:
    if not isinstance(value, str):
        report["errors"].append(issue("error", "release_date must be a string", key))
        return
    if require_release_dates and not DATE_RE.match(value):
        report["warnings"].append(issue("warning", "release_date is not in YYYY-MM-DD form", key))


def validate_resolution(value: Any, key: str, report: dict[str, Any]) -> None:
    if not isinstance(value, (int, float)) and value is not None:
        report["warnings"].append(issue("warning", "resolution is not numeric or null", key))


def validate_sequence(value: Any, key: str, label: str, report: dict[str, Any]) -> None:
    if not isinstance(value, str) or not value:
        report["errors"].append(issue("error", f"{label} must be a non-empty string", key))
    elif not PROTEIN_SEQUENCE_RE.match(value):
        report["warnings"].append(issue("warning", f"{label} has unusual sequence characters", key))


def inspect_mmcif_cache(data: Any, args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"kind": "mmcif", "entries": 0, "errors": [], "warnings": []}
    if not isinstance(data, dict):
        report["errors"].append(issue("error", "Cache root must be a JSON object"))
        return report
    report["entries"] = len(data)
    required = {"release_date", "chain_ids", "seqs", "no_chains", "resolution"}
    all_full_chain_ids: set[str] = set()
    entries_missing_release = 0
    entries_with_obsolete_marker = 0

    for key, entry in data.items():
        key_str = str(key)
        if not STRUCTURE_ID_RE.match(key_str):
            report["warnings"].append(issue("warning", "Structure key has unusual characters", key_str))
        if not isinstance(entry, dict):
            report["errors"].append(issue("error", "Entry is not an object", key_str))
            continue
        missing = sorted(required - set(entry))
        if missing:
            report["errors"].append(issue("error", f"Missing required keys: {', '.join(missing)}", key_str))
        if "release_date" in entry:
            validate_release_date(entry.get("release_date"), key_str, args.require_release_dates, report)
            if not entry.get("release_date"):
                entries_missing_release += 1
        else:
            entries_missing_release += 1
        validate_resolution(entry.get("resolution"), key_str, report)
        if any(marker in entry for marker in ("is_obsolete", "obsolete", "replaced_by")):
            entries_with_obsolete_marker += 1

        chain_ids = entry.get("chain_ids")
        seqs = entry.get("seqs")
        no_chains = entry.get("no_chains")
        if not isinstance(chain_ids, list) or not all(isinstance(chain, str) for chain in chain_ids):
            report["errors"].append(issue("error", "chain_ids must be a list of strings", key_str))
            chain_ids = []
        if not isinstance(seqs, list) or not all(isinstance(seq, str) for seq in seqs):
            report["errors"].append(issue("error", "seqs must be a list of strings", key_str))
            seqs = []
        if isinstance(chain_ids, list) and isinstance(seqs, list) and len(chain_ids) != len(seqs):
            report["errors"].append(issue("error", "chain_ids and seqs lengths differ", key_str))
        if not isinstance(no_chains, int):
            report["errors"].append(issue("error", "no_chains must be an integer", key_str))
        elif isinstance(chain_ids, list) and no_chains != len(chain_ids):
            report["errors"].append(issue("error", "no_chains does not equal len(chain_ids)", key_str))
        for chain_id in chain_ids if isinstance(chain_ids, list) else []:
            full_chain_id = f"{key_str}_{chain_id}"
            all_full_chain_ids.add(full_chain_id)
        for seq_index, seq in enumerate(seqs if isinstance(seqs, list) else []):
            validate_sequence(seq, key_str, f"seqs[{seq_index}]", report)
        cluster_sizes = entry.get("cluster_sizes")
        if cluster_sizes is not None:
            if not isinstance(cluster_sizes, list) or len(cluster_sizes) != len(chain_ids):
                report["errors"].append(issue("error", "cluster_sizes must align with chain_ids", key_str))
            else:
                for index, cluster_size in enumerate(cluster_sizes):
                    if not isinstance(cluster_size, int):
                        report["errors"].append(issue("error", f"cluster_sizes[{index}] must be an integer", key_str))
                    elif cluster_size <= 0:
                        report["warnings"].append(issue("warning", f"cluster_sizes[{index}] is non-positive; chain may be absent from cluster file", key_str))

    if args.require_release_dates and entries_missing_release:
        report["errors"].append(issue("error", f"{entries_missing_release} entries lack release_date values"))
    if args.require_obsolete_metadata and entries_with_obsolete_marker == 0:
        report["warnings"].append(issue("warning", "No obsolete-entry metadata markers found; confirm this is acceptable for template filtering"))
    if args.mmcif_dir is not None:
        if not args.mmcif_dir.is_dir():
            report["errors"].append(issue("error", "--mmcif-dir is not a directory", str(args.mmcif_dir)))
        else:
            local_ids = {path.stem for path in args.mmcif_dir.iterdir() if path.suffix.lower() == ".cif"}
            cache_ids = {str(key) for key in data}
            missing_files = sorted(cache_ids - local_ids)
            missing_cache = sorted(local_ids - cache_ids)
            if missing_files:
                report["warnings"].append(issue("warning", "Cache entries without matching .cif files: " + ", ".join(missing_files[:20])))
            if missing_cache:
                report["warnings"].append(issue("warning", ".cif files missing from cache: " + ", ".join(missing_cache[:20])))
            report["mmcif_files"] = len(local_ids)
    apply_duplicate_checks(report, args.duplicate_chains_file, all_full_chain_ids)
    return report


def inspect_chain_cache(data: Any, args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"kind": "chain", "entries": 0, "errors": [], "warnings": []}
    if not isinstance(data, dict):
        report["errors"].append(issue("error", "Cache root must be a JSON object"))
        return report
    report["entries"] = len(data)
    required = {"release_date", "seq", "resolution"}
    try:
        cluster_chains, cluster_warnings, cluster_counts = load_cluster_chains(args.cluster_file)
    except OSError as exc:
        cluster_chains, cluster_warnings, cluster_counts = set(), [], {}
        report["errors"].append(issue("error", f"Could not read cluster file: {exc}", str(args.cluster_file)))
    report["warnings"].extend(cluster_warnings)
    cluster_chains_upper = {chain.upper() for chain in cluster_chains}
    cache_keys_upper: set[str] = set()
    entries_missing_release = 0
    entries_missing_cluster_size = 0
    entries_nonpositive_cluster_size = 0

    for key, entry in data.items():
        key_str = str(key)
        cache_keys_upper.add(key_str.upper())
        if not CHAIN_ID_RE.match(key_str):
            report["warnings"].append(issue("warning", "Chain key does not look like <pdb_id>_<chain_id>", key_str))
        if not isinstance(entry, dict):
            report["errors"].append(issue("error", "Entry is not an object", key_str))
            continue
        missing = sorted(required - set(entry))
        if missing:
            report["errors"].append(issue("error", f"Missing required keys: {', '.join(missing)}", key_str))
        if "release_date" in entry:
            validate_release_date(entry.get("release_date"), key_str, args.require_release_dates, report)
            if not entry.get("release_date"):
                entries_missing_release += 1
        else:
            entries_missing_release += 1
        validate_sequence(entry.get("seq"), key_str, "seq", report)
        validate_resolution(entry.get("resolution"), key_str, report)
        if "cluster_size" in entry:
            cluster_size = entry.get("cluster_size")
            if not isinstance(cluster_size, int):
                report["errors"].append(issue("error", "cluster_size must be an integer", key_str))
            elif cluster_size <= 0:
                entries_nonpositive_cluster_size += 1
                report["warnings"].append(issue("warning", "cluster_size is non-positive; chain may be absent from cluster file", key_str))
        elif args.cluster_file is not None or args.require_cluster_size:
            entries_missing_cluster_size += 1
            message = "cluster_file supplied but entry has no cluster_size" if args.cluster_file is not None else "entry has no cluster_size"
            report["warnings"].append(issue("warning", message, key_str))
        if args.cluster_file is not None and key_str.upper() not in cluster_chains_upper:
            report["warnings"].append(issue("warning", "Chain is absent from supplied cluster file", key_str))

    if args.require_release_dates and entries_missing_release:
        report["errors"].append(issue("error", f"{entries_missing_release} entries lack release_date values"))
    if args.require_cluster_size and entries_missing_cluster_size:
        report["errors"].append(issue("error", f"{entries_missing_cluster_size} entries lack cluster_size values"))
    if args.require_cluster_size and entries_nonpositive_cluster_size:
        report["warnings"].append(issue("warning", f"{entries_nonpositive_cluster_size} entries have non-positive cluster_size values"))
    if args.cluster_file is not None:
        extra_cluster = sorted(chain for chain in cluster_chains if chain.upper() not in cache_keys_upper)
        if extra_cluster:
            report["warnings"].append(issue("warning", "Cluster chains missing from cache: " + ", ".join(extra_cluster[:20])))
        report["cluster_chains"] = len(cluster_chains)
        report["cluster_chains_with_multiple_memberships"] = sum(1 for count in cluster_counts.values() if count > 1)
    apply_duplicate_checks(report, args.duplicate_chains_file, {str(key) for key in data})
    return report


def apply_duplicate_checks(report: dict[str, Any], duplicate_chains_file: Path | None, cache_ids: set[str]) -> None:
    if duplicate_chains_file is None:
        return
    try:
        groups, warnings = load_duplicate_groups(duplicate_chains_file)
    except OSError as exc:
        report["errors"].append(issue("error", f"Could not read duplicate-chain file: {exc}", str(duplicate_chains_file)))
        return
    report["warnings"].extend(warnings)
    report["duplicate_group_count"] = len(groups)
    cache_upper = {chain.upper() for chain in cache_ids}
    missing_groups: list[str] = []
    partial_groups: list[str] = []
    for group in groups:
        present = [chain for chain in group if chain.upper() in cache_upper]
        if not present:
            missing_groups.append(" ".join(group))
        elif len(present) != len(group):
            partial_groups.append(" ".join(group))
    report["duplicate_groups_absent_from_cache"] = len(missing_groups)
    report["duplicate_groups_partially_in_cache"] = len(partial_groups)
    if missing_groups:
        report["warnings"].append(issue("warning", "Duplicate groups absent from cache: " + "; ".join(missing_groups[:10]), str(duplicate_chains_file)))
    if partial_groups:
        report["warnings"].append(issue("warning", "Duplicate groups partially represented in cache: " + "; ".join(partial_groups[:10]), str(duplicate_chains_file)))


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"kind: {report.get('kind')}")
    print(f"entries: {report.get('entries', 0)}")
    if "mmcif_files" in report:
        print(f"mmcif_files: {report['mmcif_files']}")
    if "cluster_chains" in report:
        print(f"cluster_chains: {report['cluster_chains']}")
    if "duplicate_group_count" in report:
        print(f"duplicate_group_count: {report['duplicate_group_count']}")
        print(f"duplicate_groups_absent_from_cache: {report.get('duplicate_groups_absent_from_cache', 0)}")
        print(f"duplicate_groups_partially_in_cache: {report.get('duplicate_groups_partially_in_cache', 0)}")
    for warning in report.get("warnings", []):
        print(f"WARNING: {warning['message']}" + (f" [{warning['key']}]" if "key" in warning else ""))
    for error in report.get("errors", []):
        print(f"ERROR: {error['message']}" + (f" [{error['key']}]" if "key" in error else ""))
    if not report.get("errors"):
        print("validation: ok")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True, help="Path to mmcif_cache.json, chain_cache.json, or chain_data_cache.json")
    parser.add_argument("--kind", choices=["mmcif", "chain", "auto"], default="auto", help="Cache schema to validate")
    parser.add_argument("--mmcif-dir", type=Path, help="Optional directory of .cif files for mmCIF cache cross-checks")
    parser.add_argument("--cluster-file", type=Path, help="Optional cluster file for chain or mmCIF cache cross-checks")
    parser.add_argument("--duplicate-chains-file", type=Path, help="Optional duplicate_pdb_chains.txt coverage check")
    parser.add_argument("--require-release-dates", action="store_true", help="Fail when release_date is absent or empty and warn on non-YYYY-MM-DD dates")
    parser.add_argument("--require-obsolete-metadata", action="store_true", help="Warn when no obsolete-entry metadata marker exists in an mmCIF cache")
    parser.add_argument("--require-cluster-size", action="store_true", help="Fail when chain cache entries omit cluster_size")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    try:
        data = load_json(args.cache)
    except (OSError, json.JSONDecodeError) as exc:
        report = {"kind": args.kind, "entries": 0, "errors": [issue("error", f"Could not load cache JSON: {exc}", str(args.cache))], "warnings": []}
        print_report(report, args.json)
        return 1

    kind = args.kind
    if kind == "auto":
        if isinstance(data, dict) and data:
            first_value = next(iter(data.values()))
            if isinstance(first_value, dict) and "chain_ids" in first_value:
                kind = "mmcif"
            else:
                kind = "chain"
        else:
            kind = "mmcif"

    if kind == "mmcif":
        report = inspect_mmcif_cache(data, args)
    else:
        report = inspect_chain_cache(data, args)
    report["cache"] = str(args.cache)
    print_report(report, args.json)
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
