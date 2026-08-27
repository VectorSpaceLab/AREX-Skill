#!/usr/bin/env python3
"""Preflight TotalSegmentator NIfTI/DICOM input and output-type choices.

This helper is intentionally safe: it does not import TotalSegmentator, load model
weights, run inference, convert DICOM, or modify files. If pydicom is installed it
uses stop-before-pixels probes to summarize DICOM tags.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DICOM_OUTPUT_TYPES = {"dicom_seg", "dicom_rtstruct"}
VALID_OUTPUT_TYPES = {"nifti", "dicom_seg", "dicom_rtstruct"}


def normalize_output_types(values: list[str] | None) -> list[str]:
    if not values:
        return ["nifti"]
    normalized: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            if part == "dicom":
                part = "dicom_rtstruct"
            normalized.append(part)
    invalid = [item for item in normalized if item not in VALID_OUTPUT_TYPES]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"invalid output type(s): {invalid}; allowed: {sorted(VALID_OUTPUT_TYPES)}"
        )
    return normalized or ["nifti"]


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def classify_path(path: Path) -> str:
    if not path.exists():
        return "missing"
    path_text = str(path).lower()
    if path.is_file() and (path_text.endswith(".nii") or path_text.endswith(".nii.gz")):
        return "nifti"
    if path.is_dir():
        return "dicom-dir"
    if path.is_file() and zipfile.is_zipfile(path):
        return "dicom-zip"
    return "unsupported"


def iter_candidate_files(path: Path, limit: int) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    preferred = sorted(path.rglob("*.dcm"))
    candidates = preferred if preferred else sorted(item for item in path.rglob("*") if item.is_file())
    return candidates[:limit]


def inspect_dicom_files(path: Path, limit: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "pydicom_available": has_module("pydicom"),
        "checked_files": 0,
        "readable_files": 0,
        "modalities": {},
        "series_instance_uids": {},
        "sop_class_uids": {},
        "warnings": [],
    }
    if not result["pydicom_available"]:
        result["warnings"].append("pydicom is not importable; DICOM tags were not probed")
        return result

    import pydicom  # type: ignore[import-not-found]

    files = iter_candidate_files(path, limit)
    modality_counts: Counter[str] = Counter()
    series_counts: Counter[str] = Counter()
    sop_counts: Counter[str] = Counter()
    unreadable = 0

    for file_path in files:
        result["checked_files"] += 1
        try:
            dataset = pydicom.dcmread(str(file_path), stop_before_pixels=True)
        except Exception:
            unreadable += 1
            continue
        result["readable_files"] += 1
        modality = getattr(dataset, "Modality", None)
        series_uid = getattr(dataset, "SeriesInstanceUID", None)
        sop_uid = getattr(dataset, "SOPClassUID", None)
        if modality:
            modality_counts[str(modality)] += 1
        if series_uid:
            series_counts[str(series_uid)] += 1
        if sop_uid:
            sop_counts[str(sop_uid)] += 1

    result["modalities"] = dict(modality_counts)
    result["series_instance_uids"] = dict(series_counts)
    result["sop_class_uids"] = dict(sop_counts)
    if unreadable:
        result["warnings"].append(f"{unreadable} sampled file(s) could not be read as DICOM")
    if result["readable_files"] == 0:
        result["warnings"].append("no sampled files were readable as DICOM")
    if len(modality_counts) > 1:
        result["warnings"].append("multiple DICOM modalities found; split CT/MR or other modalities before running")
    if len(series_counts) > 1:
        result["warnings"].append("multiple SeriesInstanceUID values found; use one coherent series per input")
    return result


def inspect_zip(path: Path, limit: int) -> dict[str, Any]:
    result: dict[str, Any] = {"member_count": 0, "sample_members": [], "warnings": []}
    try:
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            result["member_count"] = len(members)
            result["sample_members"] = members[:limit]
            nested_archives = [name for name in members if name.lower().endswith((".zip", ".tar", ".tar.gz"))]
            if nested_archives:
                result["warnings"].append("zip appears to contain nested archives; TotalSegmentator expects DICOM slices")
            if not members:
                result["warnings"].append("zip contains no files")
    except Exception as exc:
        result["warnings"].append(f"could not inspect zip: {exc}")
    return result


def build_findings(args: argparse.Namespace) -> dict[str, Any]:
    input_path = Path(args.input)
    path_type = classify_path(input_path)
    output_types = normalize_output_types(args.output_type)
    optional = {
        "pydicom": has_module("pydicom"),
        "dicom2nifti": has_module("dicom2nifti"),
        "highdicom": has_module("highdicom"),
        "rt_utils": has_module("rt_utils"),
    }
    findings: dict[str, Any] = {
        "input": str(input_path),
        "classification": path_type,
        "task": args.task,
        "output_types": output_types,
        "save_lowres": bool(args.save_lowres),
        "optional_modules": optional,
        "warnings": [],
        "errors": [],
    }

    if path_type == "missing":
        findings["errors"].append("input path does not exist")
    elif path_type == "unsupported":
        findings["errors"].append("input is not .nii/.nii.gz, a directory, or a zip file")
    elif path_type == "dicom-dir":
        findings["dicom_probe"] = inspect_dicom_files(input_path, args.sample_limit)
    elif path_type == "dicom-zip":
        findings["zip_probe"] = inspect_zip(input_path, args.sample_limit)
        findings["warnings"].append("zip DICOM tags are not probed without extraction; validate series contents before long runs")

    if any(item in DICOM_OUTPUT_TYPES for item in output_types) and path_type == "nifti":
        findings["errors"].append("DICOM SEG/RTSTRUCT output requires DICOM input, not NIfTI input")
    if args.save_lowres and any(item in DICOM_OUTPUT_TYPES for item in output_types):
        findings["errors"].append("save_lowres only supports NIfTI output")
    if args.save_lowres and not (args.fast or args.fastest):
        findings["errors"].append("save_lowres only works with fast or fastest mode")

    if "dicom_seg" in output_types and not optional["highdicom"]:
        message = "highdicom is not importable; required for output_type=dicom_seg"
        (findings["errors"] if args.require_optional else findings["warnings"]).append(message)
    if "dicom_rtstruct" in output_types and not optional["rt_utils"]:
        message = "rt_utils is not importable; required for output_type=dicom_rtstruct"
        (findings["errors"] if args.require_optional else findings["warnings"]).append(message)
    if path_type in {"dicom-dir", "dicom-zip"} and not optional["dicom2nifti"]:
        message = "dicom2nifti is not importable in this runtime; TotalSegmentator DICOM conversion needs it"
        (findings["errors"] if args.require_optional else findings["warnings"]).append(message)

    dicom_probe = findings.get("dicom_probe")
    if isinstance(dicom_probe, dict):
        findings["warnings"].extend(dicom_probe.get("warnings", []))
        modalities = {key.upper(): value for key, value in dicom_probe.get("modalities", {}).items()}
        if modalities.get("CT") and args.task == "total_mr":
            findings["warnings"].append("DICOM Modality=CT with task=total_mr; CLI would auto-switch to total")
        if modalities.get("MR") and args.task == "total":
            findings["warnings"].append("DICOM Modality=MR with task=total; CLI would auto-switch to total_mr")
        if args.strict and dicom_probe.get("readable_files", 0) == 0:
            findings["errors"].append("strict mode requires at least one readable DICOM file")
        if args.strict and len(dicom_probe.get("series_instance_uids", {})) > 1:
            findings["errors"].append("strict mode rejects mixed SeriesInstanceUID values")
        if args.strict and len(dicom_probe.get("modalities", {})) > 1:
            findings["errors"].append("strict mode rejects mixed DICOM modalities")

    zip_probe = findings.get("zip_probe")
    if isinstance(zip_probe, dict):
        findings["warnings"].extend(zip_probe.get("warnings", []))
        if args.strict and zip_probe.get("member_count", 0) == 0:
            findings["errors"].append("strict mode rejects empty zip input")

    return findings


def print_text(findings: dict[str, Any]) -> None:
    print(f"input: {findings['input']}")
    print(f"classification: {findings['classification']}")
    print(f"output_types: {', '.join(findings['output_types'])}")
    print("optional_modules:")
    for name, available in findings["optional_modules"].items():
        print(f"  {name}: {'yes' if available else 'no'}")

    if "dicom_probe" in findings:
        probe = findings["dicom_probe"]
        print("dicom_probe:")
        print(f"  checked_files: {probe['checked_files']}")
        print(f"  readable_files: {probe['readable_files']}")
        print(f"  modalities: {probe['modalities']}")
        print(f"  series_count: {len(probe['series_instance_uids'])}")
    if "zip_probe" in findings:
        probe = findings["zip_probe"]
        print("zip_probe:")
        print(f"  member_count: {probe['member_count']}")
        print(f"  sample_members: {probe['sample_members']}")

    for warning in findings["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    for error in findings["errors"]:
        print(f"error: {error}", file=sys.stderr)
    print("status: ok" if not findings["errors"] else "status: failed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely classify a TotalSegmentator input and check DICOM/NIfTI output-type compatibility."
    )
    parser.add_argument("input", help="Candidate .nii/.nii.gz file, DICOM directory, or DICOM zip")
    parser.add_argument(
        "--output-type",
        nargs="+",
        default=None,
        help="Planned output type(s): nifti, dicom_seg, dicom_rtstruct; comma-separated values are accepted",
    )
    parser.add_argument("--task", default="total", help="Planned task, used only for DICOM CT/MR default-task warnings")
    parser.add_argument("--fast", action="store_true", help="Declare that the planned run includes --fast")
    parser.add_argument("--fastest", action="store_true", help="Declare that the planned run includes --fastest")
    parser.add_argument("--save-lowres", action="store_true", help="Check save_lowres compatibility with the planned outputs")
    parser.add_argument("--require-optional", action="store_true", help="Treat missing optional DICOM packages as errors")
    parser.add_argument("--strict", action="store_true", help="Treat mixed/unreadable sampled DICOM metadata as errors")
    parser.add_argument("--sample-limit", type=int, default=50, help="Maximum DICOM files or zip members to sample")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    try:
        findings = build_findings(args)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(findings, indent=2, sort_keys=True))
    else:
        print_text(findings)
    return 1 if findings["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
