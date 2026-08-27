#!/usr/bin/env python3
"""Dry-run an OpenFold alignment DB sharding plan without creating DB files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

COMMON_ALIGNMENT_NAMES = {
    "bfd_uniclust_hits.a3m",
    "mgnify_hits.a3m",
    "mgnify_hits.sto",
    "uniref90_hits.a3m",
    "uniref90_hits.sto",
    "pdb70_hits.hhr",
    "hhsearch_output.hhr",
    "hmm_output.sto",
    "hmmsearch_output.sto",
    "uniprot_hits.sto",
}
QUERY_A3M_PRIORITY = [
    "mgnify_hits.a3m",
    "uniref90_hits.a3m",
    "bfd_uniclust_hits.a3m",
]
CHAIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*_[A-Za-z0-9][A-Za-z0-9_.-]*$")


def issue(severity: str, message: str, path: Path | None = None) -> dict[str, str]:
    item = {"severity": severity, "message": message}
    if path is not None:
        item["path"] = str(path)
    return item


def read_duplicate_groups(path: Path | None) -> list[list[str]]:
    if path is None:
        return []
    groups: list[list[str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                groups.append(stripped.split())
    return groups


def is_ordinary_msa_name(name: str) -> bool:
    suffix = Path(name).suffix.lower()
    stem = Path(name).stem
    if suffix == ".a3m":
        return True
    if suffix == ".sto" and stem not in {"uniprot_hits", "hmm_output"}:
        return True
    return False


def is_template_name(name: str) -> bool:
    return Path(name).suffix.lower() == ".hhr" or name in {"hmm_output.sto", "hmmsearch_output.sto"}


def read_query_sequence_from_a3m(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]
    except OSError:
        return None
    for index, line in enumerate(lines):
        if line.startswith(">") and index + 1 < len(lines):
            return lines[index + 1]
    return None


def inspect_chain_dir(path: Path, sample_query_sequences: bool) -> dict[str, Any]:
    files = [child for child in sorted(path.iterdir()) if child.is_file()]
    total_bytes = sum(child.stat().st_size for child in files)
    file_names = [child.name for child in files]
    msa_files = [name for name in file_names if is_ordinary_msa_name(name)]
    template_files = [name for name in file_names if is_template_name(name)]
    empty_files = [child.name for child in files if child.stat().st_size == 0]
    query_source = None
    query_sequence_length = None
    if sample_query_sequences:
        for candidate in QUERY_A3M_PRIORITY:
            candidate_path = path / candidate
            if candidate_path.exists() and candidate_path.is_file():
                sequence = read_query_sequence_from_a3m(candidate_path)
                query_source = candidate
                query_sequence_length = len(sequence) if sequence else None
                break
    return {
        "name": path.name,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "file_names": file_names,
        "msa_files": msa_files,
        "template_files": template_files,
        "empty_files": empty_files,
        "query_source": query_source,
        "query_sequence_length": query_sequence_length,
    }


def choose_shard_entries(chain_infos: list[dict[str, Any]], n_shards: int, strategy: str) -> list[list[dict[str, Any]]]:
    shard_entries: list[list[dict[str, Any]]] = [[] for _ in range(n_shards)]
    if strategy == "round-robin":
        for index, info in enumerate(chain_infos):
            shard_entries[index % n_shards].append(info)
        return shard_entries
    shard_sizes = [0] * n_shards
    for info in sorted(chain_infos, key=lambda item: int(item["total_bytes"]), reverse=True):
        shard_index = min(range(n_shards), key=lambda idx: shard_sizes[idx])
        shard_entries[shard_index].append(info)
        shard_sizes[shard_index] += int(info["total_bytes"])
    return shard_entries


def analyze_duplicates(groups: list[list[str]], chain_names: set[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "duplicate_group_count": len(groups),
        "duplicate_aliases_possible": 0,
        "duplicate_groups_without_representative": 0,
        "duplicate_groups_partially_present": 0,
        "warnings": [],
    }
    if not groups:
        return result
    chain_names_upper = {name.upper(): name for name in chain_names}
    missing_representative_groups: list[str] = []
    partial_groups: list[str] = []
    aliases_possible = 0
    for group in groups:
        present = [chain for chain in group if chain in chain_names or chain.upper() in chain_names_upper]
        if not present:
            missing_representative_groups.append(" ".join(group))
        else:
            aliases_possible += max(0, len(group) - 1)
            if len(present) != len(group):
                partial_groups.append(" ".join(group))
    result["duplicate_aliases_possible"] = aliases_possible
    result["duplicate_groups_without_representative"] = len(missing_representative_groups)
    result["duplicate_groups_partially_present"] = len(partial_groups)
    if missing_representative_groups:
        result["warnings"].append(issue("warning", "Duplicate groups without representative alignment: " + "; ".join(missing_representative_groups[:10])))
    if partial_groups:
        result["warnings"].append(issue("warning", "Duplicate groups partially represented by alignment directories: " + "; ".join(partial_groups[:10])))
    return result


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "alignment_dir": str(args.alignment_dir),
        "output_db_name": args.output_db_name,
        "n_shards": args.n_shards,
        "shard_strategy": args.shard_strategy,
        "errors": [],
        "warnings": [],
    }
    if args.n_shards < 1:
        report["errors"].append(issue("error", "--n-shards must be at least 1"))
        return report
    if not args.alignment_dir.is_dir():
        report["errors"].append(issue("error", "Alignment directory does not exist or is not a directory", args.alignment_dir))
        return report

    chain_dirs = [child for child in sorted(args.alignment_dir.iterdir()) if child.is_dir()]
    report["chain_dir_count"] = len(chain_dirs)
    if not chain_dirs:
        report["errors"].append(issue("error", "No chain directories found", args.alignment_dir))
        return report

    if args.n_shards > len(chain_dirs):
        report["warnings"].append(issue("warning", "Requested more shards than chain directories; some shards will be empty"))

    chain_infos = [inspect_chain_dir(chain_dir, args.sample_query_sequences) for chain_dir in chain_dirs]
    report["total_alignment_bytes"] = sum(int(info["total_bytes"]) for info in chain_infos)
    report["observed_filenames"] = dict(sorted(Counter(name for info in chain_infos for name in info["file_names"]).items()))
    report["chains_with_msa"] = sum(1 for info in chain_infos if info["msa_files"])
    report["chains_with_template"] = sum(1 for info in chain_infos if info["template_files"])
    report["chains_with_uniprot"] = sum(1 for info in chain_infos if "uniprot_hits.sto" in info["file_names"])
    report["chains_with_query_a3m"] = sum(1 for info in chain_infos if info["query_source"])

    for info in chain_infos:
        chain_path = args.alignment_dir / str(info["name"])
        if not CHAIN_ID_RE.match(str(info["name"])):
            report["warnings"].append(issue("warning", "Chain directory name does not look like <pdb_id>_<chain_id>", chain_path))
        if not info["msa_files"]:
            report["warnings"].append(issue("warning", "Chain directory has no ordinary MSA files", chain_path))
        if args.require_template and not info["template_files"]:
            report["warnings"].append(issue("warning", "Chain directory has no template hit files", chain_path))
        if args.require_uniprot and "uniprot_hits.sto" not in info["file_names"]:
            report["warnings"].append(issue("warning", "Chain directory has no uniprot_hits.sto", chain_path))
        if args.sample_query_sequences and info["query_source"] is None:
            report["warnings"].append(issue("warning", "No priority A3M file found for alignment-to-FASTA query extraction", chain_path))
        if args.sample_query_sequences and info["query_source"] is not None and info["query_sequence_length"] in {None, 0}:
            report["warnings"].append(issue("warning", f"Could not read query sequence from {info['query_source']}", chain_path))
        if info["empty_files"]:
            report["warnings"].append(issue("warning", f"Empty files: {', '.join(info['empty_files'])}", chain_path))
        uncommon = sorted(set(info["file_names"]) - COMMON_ALIGNMENT_NAMES)
        if uncommon and args.warn_uncommon_files:
            report["warnings"].append(issue("warning", f"Uncommon alignment filenames: {', '.join(uncommon)}", chain_path))
        if "hmm_output.sto" in info["file_names"]:
            report["warnings"].append(issue("warning", "Directory-backed hmm_output.sto should be renamed or converted to hmmsearch_output.sto for index-backed template parsing", chain_path))

    shard_entries = choose_shard_entries(chain_infos, args.n_shards, args.shard_strategy)
    shards = []
    for shard_index, entries in enumerate(shard_entries):
        shard_name = f"{args.output_db_name}_{shard_index}.db"
        shards.append({
            "shard": shard_index,
            "db_file": shard_name,
            "chain_count": len(entries),
            "estimated_bytes": sum(int(entry["total_bytes"]) for entry in entries),
            "first_chains": [entry["name"] for entry in entries[:5]],
        })
        if not entries:
            report["warnings"].append(issue("warning", f"Shard {shard_index} would be empty"))
    report["proposed_shards"] = shards
    report["proposed_index_file"] = f"{args.output_db_name}.index"

    duplicate_groups = read_duplicate_groups(args.duplicate_chains_file)
    if args.duplicate_chains_file is not None:
        report["duplicate_chains_file"] = str(args.duplicate_chains_file)
        duplicate_result = analyze_duplicates(duplicate_groups, {str(info["name"]) for info in chain_infos})
        report.update({key: value for key, value in duplicate_result.items() if key != "warnings"})
        report["warnings"].extend(duplicate_result.get("warnings", []))
    return report


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"alignment_dir: {report.get('alignment_dir')}")
    print(f"chain_dir_count: {report.get('chain_dir_count', 0)}")
    print(f"total_alignment_bytes: {report.get('total_alignment_bytes', 0)}")
    print(f"chains_with_msa: {report.get('chains_with_msa', 0)}")
    print(f"chains_with_template: {report.get('chains_with_template', 0)}")
    print(f"chains_with_uniprot: {report.get('chains_with_uniprot', 0)}")
    if "chains_with_query_a3m" in report:
        print(f"chains_with_query_a3m: {report['chains_with_query_a3m']}")
    print(f"output_db_name: {report.get('output_db_name')}")
    print(f"n_shards: {report.get('n_shards')}")
    print(f"shard_strategy: {report.get('shard_strategy')}")
    if "duplicate_group_count" in report:
        print(f"duplicate_group_count: {report['duplicate_group_count']}")
        print(f"duplicate_aliases_possible: {report.get('duplicate_aliases_possible', 0)}")
        print(f"duplicate_groups_without_representative: {report.get('duplicate_groups_without_representative', 0)}")
    print("proposed_shards:")
    for shard in report.get("proposed_shards", []):
        print(
            f"  {shard['db_file']}: chains={shard['chain_count']} "
            f"estimated_bytes={shard['estimated_bytes']}"
        )
    observed = report.get("observed_filenames", {})
    if observed:
        print("observed_filenames:")
        for name, count in observed.items():
            print(f"  {name}: {count}")
    for warning in report.get("warnings", []):
        print(f"WARNING: {warning['message']}" + (f" [{warning['path']}]" if "path" in warning else ""))
    for error in report.get("errors", []):
        print(f"ERROR: {error['message']}" + (f" [{error['path']}]" if "path" in error else ""))
    if not report.get("errors"):
        print("plan: ok")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alignment-dir", type=Path, required=True, help="Flattened alignment directory with one subdirectory per chain")
    parser.add_argument("--output-db-name", default="alignment_db", help="Base name for planned DB shards and index")
    parser.add_argument("--n-shards", type=int, default=10, help="Number of planned shard files")
    parser.add_argument("--shard-strategy", choices=["round-robin", "balanced-by-size"], default="round-robin", help="Dry-run assignment strategy for estimating shard contents")
    parser.add_argument("--duplicate-chains-file", type=Path, help="Optional duplicate_pdb_chains.txt to assess representative coverage")
    parser.add_argument("--require-template", action="store_true", help="Warn when a chain directory lacks template hit files")
    parser.add_argument("--require-uniprot", action="store_true", help="Warn when a chain directory lacks uniprot_hits.sto")
    parser.add_argument("--sample-query-sequences", action="store_true", help="Read priority A3M files to estimate alignment-to-FASTA query sequence availability")
    parser.add_argument("--warn-uncommon-files", action="store_true", help="Warn about filenames outside common OpenFold alignment names")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    try:
        report = build_plan(args)
    except OSError as exc:
        report = {"errors": [issue("error", f"Filesystem error: {exc}")], "warnings": []}
    print_report(report, args.json)
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
