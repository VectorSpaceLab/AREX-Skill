#!/usr/bin/env python3
"""Validate a BiRefNet dataset tree without importing project code."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

SUPPORTED_SUFFIXES = (".png", ".jpg", ".PNG", ".JPG", ".JPEG")


@dataclass
class PairReport:
    dataset: str
    im_dir_exists: bool
    gt_dir_exists: bool
    im_count: int = 0
    gt_count: int = 0
    matched_count: int = 0
    same_extension_pairs: int = 0
    mixed_extension_pairs: int = 0
    missing_in_gt: list[str] = None
    missing_in_im: list[str] = None
    duplicate_im_basenames: list[str] = None
    duplicate_gt_basenames: list[str] = None
    unsupported_im_files: list[str] = None
    unsupported_gt_files: list[str] = None
    aux_label_issues: list[str] = None
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self) -> None:
        for field_name in [
            "missing_in_gt",
            "missing_in_im",
            "duplicate_im_basenames",
            "duplicate_gt_basenames",
            "unsupported_im_files",
            "unsupported_gt_files",
            "aux_label_issues",
            "errors",
            "warnings",
        ]:
            if getattr(self, field_name) is None:
                setattr(self, field_name, [])


def has_supported_suffix(name: str) -> bool:
    return name.endswith(SUPPORTED_SUFFIXES)


def collect_supported_files(folder: Path) -> tuple[dict[str, list[Path]], list[str], list[str]]:
    by_basename: dict[str, list[Path]] = defaultdict(list)
    unsupported: list[str] = []
    ignored: list[str] = []
    if not folder.is_dir():
        return {}, [], []

    for item in sorted(folder.iterdir(), key=lambda p: p.name):
        if item.name.startswith("."):
            ignored.append(item.name)
            continue
        if item.is_file() and has_supported_suffix(item.name):
            by_basename[item.stem].append(item)
        elif item.is_file():
            unsupported.append(item.name)
        else:
            ignored.append(item.name)
    return dict(by_basename), unsupported, ignored


def check_auxiliary_filename(label_name: str) -> str | None:
    parts = label_name.split("#")
    if len(parts) < 4 or not parts[3]:
        return (
            f"label filename '{label_name}' does not expose a class name in the fourth '#'-separated field"
        )
    return None


def pair_dataset(data_root: Path, task: str, dataset: str, check_aux: bool) -> PairReport:
    base = data_root / task / dataset
    im_dir = base / "im"
    gt_dir = base / "gt"
    report = PairReport(
        dataset=dataset,
        im_dir_exists=im_dir.is_dir(),
        gt_dir_exists=gt_dir.is_dir(),
    )

    if not report.im_dir_exists:
        report.errors.append(f"missing image directory: {task}/{dataset}/im")
    if not report.gt_dir_exists:
        report.errors.append(f"missing label directory: {task}/{dataset}/gt")
    if report.errors:
        return report

    im_map, im_unsupported, im_ignored = collect_supported_files(im_dir)
    gt_map, gt_unsupported, gt_ignored = collect_supported_files(gt_dir)
    report.unsupported_im_files = im_unsupported
    report.unsupported_gt_files = gt_unsupported

    duplicate_im = [base for base, files in sorted(im_map.items()) if len(files) > 1]
    duplicate_gt = [base for base, files in sorted(gt_map.items()) if len(files) > 1]
    report.duplicate_im_basenames = duplicate_im
    report.duplicate_gt_basenames = duplicate_gt

    if im_ignored:
        report.warnings.append(f"ignored {len(im_ignored)} hidden or nested image entries")
    if gt_ignored:
        report.warnings.append(f"ignored {len(gt_ignored)} hidden or nested label entries")
    if im_unsupported:
        report.warnings.append(f"ignored {len(im_unsupported)} unsupported image files")
    if gt_unsupported:
        report.warnings.append(f"ignored {len(gt_unsupported)} unsupported label files")

    if duplicate_im:
        report.errors.append(
            "duplicate image basenames: " + ", ".join(duplicate_im[:8])
            + (" ..." if len(duplicate_im) > 8 else "")
        )
    if duplicate_gt:
        report.errors.append(
            "duplicate label basenames: " + ", ".join(duplicate_gt[:8])
            + (" ..." if len(duplicate_gt) > 8 else "")
        )

    im_basenames = set(im_map)
    gt_basenames = set(gt_map)
    missing_in_gt = sorted(im_basenames - gt_basenames)
    missing_in_im = sorted(gt_basenames - im_basenames)
    report.missing_in_gt = missing_in_gt
    report.missing_in_im = missing_in_im
    report.im_count = len(im_map)
    report.gt_count = len(gt_map)
    report.matched_count = len(im_basenames & gt_basenames)
    if missing_in_gt:
        report.errors.append(
            "missing labels for basenames: " + ", ".join(missing_in_gt[:8])
            + (" ..." if len(missing_in_gt) > 8 else "")
        )
    if missing_in_im:
        report.errors.append(
            "missing images for basenames: " + ", ".join(missing_in_im[:8])
            + (" ..." if len(missing_in_im) > 8 else "")
        )

    for basename in sorted(im_basenames & gt_basenames):
        im_path = im_map[basename][0]
        gt_path = gt_map[basename][0]
        if im_path.suffix == gt_path.suffix:
            report.same_extension_pairs += 1
        else:
            report.mixed_extension_pairs += 1
        if check_aux:
            issue = check_auxiliary_filename(gt_path.name)
            if issue:
                report.aux_label_issues.append(issue)

    if check_aux and report.aux_label_issues:
        report.errors.extend(report.aux_label_issues)

    if report.im_count != report.gt_count:
        report.errors.append(
            f"image/label counts differ after suffix filtering: im={report.im_count}, gt={report.gt_count}"
        )

    return report


def parse_dataset_spec(spec: str) -> list[str]:
    return [part for part in spec.split("+") if part]


def build_report(data_root: Path, task: str, dataset_spec: str, check_aux: bool) -> dict:
    datasets = parse_dataset_spec(dataset_spec)
    reports = [pair_dataset(data_root, task, dataset, check_aux) for dataset in datasets]
    all_errors: list[str] = []
    all_warnings: list[str] = []
    totals = {
        "datasets": len(reports),
        "image_files": sum(report.im_count for report in reports),
        "label_files": sum(report.gt_count for report in reports),
        "matched_basenames": sum(report.matched_count for report in reports),
        "same_extension_pairs": sum(report.same_extension_pairs for report in reports),
        "mixed_extension_pairs": sum(report.mixed_extension_pairs for report in reports),
    }
    for report in reports:
        all_errors.extend(report.errors)
        all_warnings.extend(report.warnings)

    return {
        "task": task,
        "datasets": dataset_spec,
        "report_ok": not all_errors,
        "totals": totals,
        "datasets_report": [asdict(report) for report in reports],
        "errors": all_errors,
        "warnings": all_warnings,
    }


def print_text(report: dict) -> None:
    print("BiRefNet dataset check")
    print(f"- task: {report['task']}")
    print(f"- datasets: {report['datasets']}")
    print(f"- ok: {report['report_ok']}")
    print(
        "- totals: "
        f"images={report['totals']['image_files']}, labels={report['totals']['label_files']}, "
        f"pairs={report['totals']['matched_basenames']}, same_ext={report['totals']['same_extension_pairs']}, "
        f"mixed_ext={report['totals']['mixed_extension_pairs']}"
    )
    for dataset_report in report["datasets_report"]:
        print(f"Dataset {dataset_report['dataset']}")
        print(f"  im_dir_exists: {dataset_report['im_dir_exists']}")
        print(f"  gt_dir_exists: {dataset_report['gt_dir_exists']}")
        print(f"  im_count: {dataset_report['im_count']}")
        print(f"  gt_count: {dataset_report['gt_count']}")
        print(f"  matched_count: {dataset_report['matched_count']}")
        print(f"  same_extension_pairs: {dataset_report['same_extension_pairs']}")
        print(f"  mixed_extension_pairs: {dataset_report['mixed_extension_pairs']}")
        if dataset_report["missing_in_gt"]:
            print("  missing_in_gt: " + ", ".join(dataset_report["missing_in_gt"]))
        if dataset_report["missing_in_im"]:
            print("  missing_in_im: " + ", ".join(dataset_report["missing_in_im"]))
        if dataset_report["duplicate_im_basenames"]:
            print("  duplicate_im_basenames: " + ", ".join(dataset_report["duplicate_im_basenames"]))
        if dataset_report["duplicate_gt_basenames"]:
            print("  duplicate_gt_basenames: " + ", ".join(dataset_report["duplicate_gt_basenames"]))
        if dataset_report["unsupported_im_files"]:
            print("  unsupported_im_files: " + ", ".join(dataset_report["unsupported_im_files"]))
        if dataset_report["unsupported_gt_files"]:
            print("  unsupported_gt_files: " + ", ".join(dataset_report["unsupported_gt_files"]))
        if dataset_report["aux_label_issues"]:
            print("  aux_label_issues: " + "; ".join(dataset_report["aux_label_issues"]))
        if dataset_report["warnings"]:
            print("  warnings: " + "; ".join(dataset_report["warnings"]))
        if dataset_report["errors"]:
            print("  errors: " + "; ".join(dataset_report["errors"]))

    if report["warnings"]:
        print("Warnings: " + "; ".join(report["warnings"]))
    if report["errors"]:
        print("Errors: " + "; ".join(report["errors"]))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a BiRefNet dataset tree and image/label basename pairing."
    )
    parser.add_argument("--data-root", required=True, type=Path, help="Root directory that contains task folders.")
    parser.add_argument("--task", required=True, help="Task folder name under the data root.")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset folder name under the task folder. Use '+' to check multiple datasets in one call.",
    )
    parser.add_argument(
        "--check-auxiliary-classification",
        action="store_true",
        help="Also validate the DIS-style class-label filename convention.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the validation report as JSON instead of text.",
    )
    args = parser.parse_args()

    report = build_report(args.data_root, args.task, args.dataset, args.check_auxiliary_classification)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["report_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
