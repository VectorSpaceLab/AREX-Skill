#!/usr/bin/env python3
"""Summarize an AlphaFold 3 output job directory.

This script uses only the Python standard library. It inventories expected
AlphaFold 3 output files, seed/sample directories, optional embedding and
distogram archives, ranking CSV rows, and summary confidence JSON keys.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import zipfile


EXPECTED_SUMMARY_KEYS = (
    "ptm",
    "iptm",
    "ranking_score",
    "fraction_disordered",
    "has_clash",
    "chain_pair_pae_min",
    "chain_pair_iptm",
    "chain_ptm",
    "chain_iptm",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect an AlphaFold 3 output job directory without importing alphafold3."
    )
    parser.add_argument(
        "job_dir",
        type=Path,
        help="Path to one sanitized AlphaFold 3 job output directory.",
    )
    parser.add_argument(
        "--job-prefix",
        help=(
            "Expected sanitized job prefix. Defaults to the job directory name; "
            "override when the directory has a timestamp/collision suffix."
        ),
    )
    return parser.parse_args()


def status_line(label: str, present: bool, detail: str = "") -> str:
    marker = "OK" if present else "MISSING"
    suffix = f" - {detail}" if detail else ""
    return f"  [{marker}] {label}{suffix}"


def file_variant(job_dir: Path, base_name: str, allow_zst: bool = False) -> tuple[bool, str]:
    direct = job_dir / base_name
    if direct.exists():
        return True, direct.name
    if allow_zst:
        compressed = job_dir / f"{base_name}.zst"
        if compressed.exists():
            return True, compressed.name
    return False, base_name


def read_json_keys(path: Path) -> tuple[list[str], str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        return [], f"could not read: {exc}"
    except json.JSONDecodeError as exc:
        return [], f"invalid JSON: {exc}"
    if isinstance(data, dict):
        return sorted(data.keys()), None
    return [], f"expected JSON object, got {type(data).__name__}"


def npz_members(path: Path) -> tuple[list[str], str | None]:
    try:
        with zipfile.ZipFile(path) as archive:
            members = sorted(
                member[:-4] if member.endswith(".npy") else member
                for member in archive.namelist()
                if not member.endswith("/")
            )
    except (OSError, zipfile.BadZipFile) as exc:
        return [], f"not a readable npz/zip archive: {exc}"
    return members, None


def summarize_ranking_csv(path: Path) -> list[str]:
    lines: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        return [f"  Could not read ranking CSV: {exc}"]

    lines.append(f"  Rows: {len(rows)}")
    if not rows:
        return lines

    missing_columns = {"seed", "sample", "ranking_score"} - set(rows[0])
    if missing_columns:
        lines.append(f"  Missing expected columns: {', '.join(sorted(missing_columns))}")
        return lines

    scored_rows = []
    for row in rows:
        try:
            scored_rows.append((float(row["ranking_score"]), row))
        except (TypeError, ValueError):
            lines.append(
                "  Non-numeric ranking_score for "
                f"seed={row.get('seed')} sample={row.get('sample')}: {row.get('ranking_score')}"
            )
    if scored_rows:
        best_score, best_row = max(scored_rows, key=lambda item: item[0])
        lines.append(
            "  Best row: "
            f"seed={best_row.get('seed')} sample={best_row.get('sample')} "
            f"ranking_score={best_score:g}"
        )
    return lines


def summarize_summary_json(path: Path, indent: str = "  ") -> list[str]:
    keys, error = read_json_keys(path)
    if error:
        return [f"{indent}{error}"]
    expected_present = [key for key in EXPECTED_SUMMARY_KEYS if key in keys]
    extra_count = len([key for key in keys if key not in EXPECTED_SUMMARY_KEYS])
    return [
        f"{indent}Keys: {', '.join(keys) if keys else '(none)'}",
        f"{indent}Expected metric keys present: {', '.join(expected_present) if expected_present else '(none)'}",
        f"{indent}Other keys: {extra_count}",
    ]


def summarize_top_level(job_dir: Path, job_prefix: str) -> None:
    print("Top-level expected files:")
    checks = [
        (f"{job_prefix}_model.cif", True),
        (f"{job_prefix}_confidences.json", True),
        (f"{job_prefix}_summary_confidences.json", False),
        (f"{job_prefix}_data.json", False),
        (f"{job_prefix}_ranking_scores.csv", False),
        ("TERMS_OF_USE.md", False),
    ]
    for file_name, allow_zst in checks:
        present, actual_name = file_variant(job_dir, file_name, allow_zst=allow_zst)
        detail = actual_name if actual_name != file_name else ""
        print(status_line(file_name, present, detail))

    ranking_path = job_dir / f"{job_prefix}_ranking_scores.csv"
    if ranking_path.exists():
        print("\nRanking scores:")
        for line in summarize_ranking_csv(ranking_path):
            print(line)

    summary_path = job_dir / f"{job_prefix}_summary_confidences.json"
    if summary_path.exists():
        print("\nTop-level summary confidences:")
        for line in summarize_summary_json(summary_path):
            print(line)


def summarize_sample_dir(sample_dir: Path, job_prefix: str) -> None:
    sample_label = sample_dir.name
    sample_prefix = f"{job_prefix}_{sample_label}"
    print(f"\nSample directory: {sample_label}")
    for file_name, allow_zst in (
        (f"{sample_prefix}_model.cif", True),
        (f"{sample_prefix}_confidences.json", True),
        (f"{sample_prefix}_summary_confidences.json", False),
    ):
        present, actual_name = file_variant(sample_dir, file_name, allow_zst=allow_zst)
        detail = actual_name if actual_name != file_name else ""
        print(status_line(file_name, present, detail))

    summary_path = sample_dir / f"{sample_prefix}_summary_confidences.json"
    if summary_path.exists():
        for line in summarize_summary_json(summary_path, indent="    "):
            print(line)


def summarize_npz_dir(directory: Path, expected_suffix: str) -> None:
    print(f"\nOptional directory: {directory.name}")
    npz_files = sorted(directory.glob("*.npz"))
    if not npz_files:
        print("  No .npz files found")
        return
    for npz_path in npz_files:
        members, error = npz_members(npz_path)
        if error:
            print(f"  {npz_path.name}: {error}")
        else:
            suffix_note = "expected suffix" if npz_path.name.endswith(expected_suffix) else "unexpected suffix"
            print(f"  {npz_path.name}: {suffix_note}; members={', '.join(members) if members else '(none)'}")


def main() -> int:
    args = parse_args()
    job_dir = args.job_dir
    if not job_dir.exists():
        print(f"Error: {job_dir} does not exist", file=sys.stderr)
        return 2
    if not job_dir.is_dir():
        print(f"Error: {job_dir} is not a directory", file=sys.stderr)
        return 2

    job_prefix = args.job_prefix or job_dir.name
    print(f"Job directory: {job_dir}")
    print(f"Assumed sanitized job prefix: {job_prefix}")

    summarize_top_level(job_dir, job_prefix)

    sample_dirs = sorted(
        path for path in job_dir.iterdir() if path.is_dir() and path.name.startswith("seed-") and "_sample-" in path.name
    )
    print(f"\nSeed/sample directories: {len(sample_dirs)}")
    for sample_dir in sample_dirs:
        summarize_sample_dir(sample_dir, job_prefix)

    embedding_dirs = sorted(
        path for path in job_dir.iterdir() if path.is_dir() and path.name.startswith("seed-") and path.name.endswith("_embeddings")
    )
    print(f"\nEmbedding directories: {len(embedding_dirs)}")
    for directory in embedding_dirs:
        summarize_npz_dir(directory, "_embeddings.npz")

    distogram_dirs = sorted(
        path for path in job_dir.iterdir() if path.is_dir() and path.name.startswith("seed-") and path.name.endswith("_distogram")
    )
    print(f"\nDistogram directories: {len(distogram_dirs)}")
    for directory in distogram_dirs:
        summarize_npz_dir(directory, "_distogram.npz")

    if not embedding_dirs:
        print("  No embeddings found; this is normal unless embeddings were requested at run time.")
    if not distogram_dirs:
        print("  No distograms found; this is normal unless distograms were requested at run time.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
