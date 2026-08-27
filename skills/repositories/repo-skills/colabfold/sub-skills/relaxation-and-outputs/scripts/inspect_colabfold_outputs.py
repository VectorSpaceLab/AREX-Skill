#!/usr/bin/env python3
"""Inspect ColabFold output directories without importing ColabFold or modifying files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

RANK_RE = re.compile(r"rank_(\d{3})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize and sanity-check a ColabFold result directory. "
            "The script is read-only and performs no downloads or imports of heavy optional packages."
        )
    )
    parser.add_argument("result_dir", type=Path, help="Directory containing ColabFold output files")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print a JSON report instead of a human-readable summary",
    )
    parser.add_argument(
        "--warn-exit-code",
        action="store_true",
        help="Exit with status 2 when warnings are found",
    )
    parser.add_argument(
        "--max-json-bytes",
        type=int,
        default=20_000_000,
        help="Maximum JSON file size to parse; larger files are reported but skipped (default: 20000000)",
    )
    return parser.parse_args()


def safe_json_load(path: Path, max_bytes: int) -> tuple[Any | None, str | None]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        return None, f"cannot stat JSON file: {exc}"
    if size > max_bytes:
        return None, f"skipped JSON parse because file is {size} bytes (> {max_bytes})"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except UnicodeDecodeError as exc:
        return None, f"cannot decode JSON as UTF-8: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: line {exc.lineno} column {exc.colno}: {exc.msg}"
    except OSError as exc:
        return None, f"cannot read JSON file: {exc}"


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def matrix_shape(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, list):
        return None
    rows = len(value)
    if rows == 0:
        return (0, 0)
    if not all(isinstance(row, list) for row in value):
        return None
    widths = {len(row) for row in value}
    if len(widths) != 1:
        return None
    return (rows, widths.pop())


def classify_json(path: Path) -> str:
    name = path.name.lower()
    if "scores" in name:
        return "scores"
    if "predicted_aligned_error" in name or name.endswith("pae.json"):
        return "pae"
    if name == "config.json":
        return "config"
    return "other"


def rank_number(path: Path) -> int | None:
    match = RANK_RE.search(path.name)
    if not match:
        return None
    return int(match.group(1))


def inspect_scores(path: Path, data: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {
        "file": path.name,
        "rank": rank_number(path),
        "keys": [],
        "plddt_count": None,
        "plddt_min": None,
        "plddt_max": None,
        "pae_shape": None,
        "metrics": {},
        "extra_metrics_present": [],
    }
    warnings: list[str] = []

    if not isinstance(data, dict):
        warnings.append(f"{path.name}: score JSON is not an object")
        return info, warnings

    info["keys"] = sorted(str(key) for key in data.keys())

    plddt = data.get("plddt")
    if isinstance(plddt, list) and plddt and all(is_number(item) for item in plddt):
        info["plddt_count"] = len(plddt)
        info["plddt_min"] = round(float(min(plddt)), 3)
        info["plddt_max"] = round(float(max(plddt)), 3)
        if info["plddt_min"] < 0 or info["plddt_max"] > 100:
            warnings.append(f"{path.name}: pLDDT values are outside the expected 0-100 range")
    elif plddt is None:
        warnings.append(f"{path.name}: missing plddt list")
    else:
        warnings.append(f"{path.name}: plddt is not a non-empty numeric list")

    pae_shape = matrix_shape(data.get("pae"))
    if pae_shape is not None:
        info["pae_shape"] = list(pae_shape)
        plddt_count = info["plddt_count"]
        if pae_shape[0] != pae_shape[1]:
            warnings.append(f"{path.name}: pae matrix is not square ({pae_shape[0]}x{pae_shape[1]})")
        if isinstance(plddt_count, int) and plddt_count and pae_shape[0] != plddt_count:
            warnings.append(f"{path.name}: pae size {pae_shape[0]} does not match plddt length {plddt_count}")
    elif "pae" in data:
        warnings.append(f"{path.name}: pae is present but not a rectangular matrix")

    for metric in ("ptm", "iptm", "max_pae", "actifptm"):
        if metric in data:
            info["metrics"][metric] = data[metric]

    for metric in ("pairwise_actifptm", "pairwise_iptm", "per_chain_ptm", "actifptm"):
        if metric in data:
            info["extra_metrics_present"].append(metric)

    return info, warnings


def inspect_pae_json(path: Path, data: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {"file": path.name, "pae_shape": None, "max_predicted_aligned_error": None}
    warnings: list[str] = []
    if not isinstance(data, dict):
        warnings.append(f"{path.name}: PAE JSON is not an object")
        return info, warnings
    pae = data.get("predicted_aligned_error", data.get("pae"))
    shape = matrix_shape(pae)
    if shape is None:
        warnings.append(f"{path.name}: no rectangular predicted_aligned_error matrix found")
    else:
        info["pae_shape"] = list(shape)
        if shape[0] != shape[1]:
            warnings.append(f"{path.name}: predicted aligned error matrix is not square")
    if "max_predicted_aligned_error" in data:
        info["max_predicted_aligned_error"] = data["max_predicted_aligned_error"]
    return info, warnings


def inspect_config(path: Path, data: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {"file": path.name, "selected": {}}
    warnings: list[str] = []
    if not isinstance(data, dict):
        warnings.append(f"{path.name}: config JSON is not an object")
        return info, warnings
    for key in (
        "model_type",
        "rank_by",
        "num_relax",
        "use_gpu_relax",
        "calc_extra_ptm",
        "use_templates",
        "use_amber",
        "skip_output",
    ):
        if key in data:
            info["selected"][key] = data[key]
    return info, warnings


def read_citations(path: Path) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {"file": path.name, "entries": [], "has_openmm": False}
    warnings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(f"{path.name}: cannot read BibTeX file: {exc}")
        return info, warnings
    entries = re.findall(r"@\w+\{([^,\s]+)", text)
    info["entries"] = entries
    lowered = text.lower()
    info["has_openmm"] = "openmm" in lowered or "eastman" in lowered
    if not entries:
        warnings.append(f"{path.name}: no BibTeX entries detected")
    return info, warnings


def inspect_directory(result_dir: Path, max_json_bytes: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "result_dir": str(result_dir),
        "ok": False,
        "counts": {},
        "structures": {},
        "json_files": [],
        "score_files": [],
        "pae_json_files": [],
        "config": None,
        "plots": {},
        "citations": None,
        "warnings": [],
    }

    if not result_dir.exists():
        report["warnings"].append("result directory does not exist")
        return report
    if not result_dir.is_dir():
        report["warnings"].append("result path is not a directory")
        return report

    try:
        files = sorted(path for path in result_dir.iterdir() if path.is_file())
    except OSError as exc:
        report["warnings"].append(f"cannot list result directory: {exc}")
        return report

    pdb_files = [path for path in files if path.suffix.lower() == ".pdb"]
    cif_files = [path for path in files if path.suffix.lower() == ".cif"]
    json_files = [path for path in files if path.suffix.lower() == ".json"]
    png_files = [path for path in files if path.suffix.lower() == ".png"]
    bib_files = [path for path in files if path.suffix.lower() in {".bib", ".bibtex"} or path.name == "cite.bibtex"]

    relaxed_pdb = [path.name for path in pdb_files if "relaxed" in path.name and "unrelaxed" not in path.name]
    unrelaxed_pdb = [path.name for path in pdb_files if "unrelaxed" in path.name]
    ranked_pdb = [path.name for path in pdb_files if "rank_" in path.name]

    report["counts"] = {
        "files": len(files),
        "pdb": len(pdb_files),
        "cif": len(cif_files),
        "json": len(json_files),
        "png": len(png_files),
        "bibtex": len(bib_files),
    }
    report["structures"] = {
        "relaxed_pdb": relaxed_pdb,
        "unrelaxed_pdb": unrelaxed_pdb,
        "ranked_pdb": ranked_pdb,
        "cif": [path.name for path in cif_files],
    }
    report["json_files"] = [path.name for path in json_files]

    plot_patterns = {
        "coverage": "coverage",
        "pae": "pae",
        "plddt": "plddt",
        "extra_metrics": "ext_metrics",
    }
    for key, token in plot_patterns.items():
        report["plots"][key] = [path.name for path in png_files if token in path.name.lower()]

    for path in json_files:
        kind = classify_json(path)
        data, error = safe_json_load(path, max_json_bytes)
        if error:
            report["warnings"].append(f"{path.name}: {error}")
            continue
        if kind == "scores":
            info, warnings = inspect_scores(path, data)
            report["score_files"].append(info)
            report["warnings"].extend(warnings)
        elif kind == "pae":
            info, warnings = inspect_pae_json(path, data)
            report["pae_json_files"].append(info)
            report["warnings"].extend(warnings)
        elif kind == "config":
            info, warnings = inspect_config(path, data)
            report["config"] = info
            report["warnings"].extend(warnings)

    if bib_files:
        citation_info, warnings = read_citations(bib_files[0])
        report["citations"] = citation_info
        report["warnings"].extend(warnings)
    else:
        report["warnings"].append("missing cite.bibtex or other BibTeX citation file")

    if not pdb_files and not cif_files and not json_files:
        report["warnings"].append("no PDB, CIF, or JSON outputs found")
    if not report["score_files"]:
        report["warnings"].append("no score JSON files detected")
    if report["score_files"] and not report["plots"].get("plddt"):
        report["warnings"].append("score JSON exists but no pLDDT plot PNG detected")
    if any(item.get("pae_shape") for item in report["score_files"]) and not report["plots"].get("pae"):
        report["warnings"].append("PAE data exists in score JSON but no PAE plot PNG detected")
    if relaxed_pdb and not report["citations"]:
        report["warnings"].append("relaxed PDB files exist but citation file is missing")
    if relaxed_pdb and report["citations"] and not report["citations"].get("has_openmm"):
        report["warnings"].append("relaxed PDB files exist but OpenMM/Amber citation was not detected")

    report["ok"] = not report["warnings"]
    return report


def print_text_report(report: dict[str, Any]) -> None:
    print(f"ColabFold output inspection: {report['result_dir']}")
    print(f"Status: {'OK' if report['ok'] else 'WARNINGS'}")

    counts = report.get("counts", {})
    if counts:
        print("\nCounts:")
        for key in ("files", "pdb", "cif", "json", "png", "bibtex"):
            print(f"  {key}: {counts.get(key, 0)}")

    structures = report.get("structures", {})
    if structures:
        print("\nStructures:")
        print(f"  ranked PDBs: {len(structures.get('ranked_pdb', []))}")
        print(f"  unrelaxed PDBs: {len(structures.get('unrelaxed_pdb', []))}")
        print(f"  relaxed PDBs: {len(structures.get('relaxed_pdb', []))}")
        print(f"  CIF files: {len(structures.get('cif', []))}")

    score_files = report.get("score_files", [])
    print("\nScores:")
    if not score_files:
        print("  none detected")
    for score in score_files:
        rank = score.get("rank")
        rank_text = f"rank {rank:03d}" if isinstance(rank, int) else "unranked"
        print(
            "  "
            f"{score['file']} ({rank_text}): "
            f"pLDDT n={score.get('plddt_count')} "
            f"range={score.get('plddt_min')}..{score.get('plddt_max')} "
            f"PAE={score.get('pae_shape')}"
        )
        metrics = score.get("metrics") or {}
        if metrics:
            print(f"    metrics: {metrics}")
        extra = score.get("extra_metrics_present") or []
        if extra:
            print(f"    extra metrics: {', '.join(extra)}")

    plots = report.get("plots", {})
    print("\nPlots:")
    for key in ("coverage", "pae", "plddt", "extra_metrics"):
        print(f"  {key}: {len(plots.get(key, []))}")

    citations = report.get("citations")
    print("\nCitations:")
    if citations:
        print(f"  entries: {len(citations.get('entries', []))}")
        print(f"  OpenMM/Amber citation detected: {citations.get('has_openmm')}")
    else:
        print("  none detected")

    warnings = report.get("warnings", [])
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")


def main() -> int:
    args = parse_args()
    report = inspect_directory(args.result_dir, args.max_json_bytes)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    if args.warn_exit_code and report.get("warnings"):
        return 2
    return 0 if report.get("result_dir") else 1


if __name__ == "__main__":
    sys.exit(main())
