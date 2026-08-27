#!/usr/bin/env python3
"""Safe mAP input checker for ground-truth / detection-result folders.

This bundled helper adapts the legacy class lookup and GT/DR intersection
repair workflows into one explicit-path, report-first command. By default it
only reports readiness problems. It moves files only when both a backup target
and --confirm-move are supplied.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


TXT_SUFFIX = ".txt"
GT_LABEL = "ground-truth"
DR_LABEL = "detection-results"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report class membership and basename intersections for mAP "
            "ground-truth and detection-result .txt folders."
        )
    )
    parser.add_argument(
        "--gt-dir",
        required=True,
        type=Path,
        help="Ground-truth folder containing one .txt file per image.",
    )
    parser.add_argument(
        "--dr-dir",
        required=True,
        type=Path,
        help="Detection-results folder containing matching .txt files.",
    )
    parser.add_argument(
        "--class-name",
        help=(
            "Optional class name to find. The helper checks the first "
            "whitespace-separated token of every non-blank line."
        ),
    )
    parser.add_argument(
        "--move-extra-to",
        type=Path,
        help=(
            "Backup root for non-intersecting files. Without --confirm-move, "
            "this is reported as a dry-run plan only."
        ),
    )
    parser.add_argument(
        "--confirm-move",
        action="store_true",
        help=(
            "Actually move GT-only and DR-only .txt files into the backup root. "
            "Requires --move-extra-to and refuses empty intersections."
        ),
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="Optional path for a machine-readable JSON report.",
    )
    parser.add_argument(
        "--max-list",
        type=int,
        default=40,
        help="Maximum filenames to print per list in the text report (default: 40).",
    )
    args = parser.parse_args(argv)
    if args.confirm_move and not args.move_extra_to:
        parser.error("--confirm-move requires --move-extra-to BACKUP_ROOT")
    if args.max_list < 1:
        parser.error("--max-list must be at least 1")
    return args


def resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def scan_txt_dir(folder: Path) -> Tuple[Dict[str, Path], List[str]]:
    """Return top-level .txt files keyed by filename and non-.txt filenames."""
    if not folder.exists():
        raise ValueError(f"folder does not exist: {folder}")
    if not folder.is_dir():
        raise ValueError(f"path is not a folder: {folder}")

    txt_files: Dict[str, Path] = {}
    non_txt: List[str] = []
    for item in sorted(folder.iterdir(), key=lambda p: p.name):
        if not item.is_file():
            continue
        if item.suffix == TXT_SUFFIX:
            txt_files[item.name] = item
        else:
            non_txt.append(item.name)
    return txt_files, non_txt


def compare_sets(gt_files: Dict[str, Path], dr_files: Dict[str, Path]) -> Dict[str, object]:
    gt_names = set(gt_files)
    dr_names = set(dr_files)
    gt_only = sorted(gt_names - dr_names)
    dr_only = sorted(dr_names - gt_names)
    intersection = sorted(gt_names & dr_names)
    return {
        "gt_count": len(gt_names),
        "dr_count": len(dr_names),
        "intersection_count": len(intersection),
        "gt_only": gt_only,
        "dr_only": dr_only,
        "intersection": intersection,
        "same_count": len(gt_names) == len(dr_names),
        "ready_for_evaluation": bool(gt_names)
        and bool(dr_names)
        and not gt_only
        and not dr_only,
    }


def find_class(files: Dict[str, Path], class_name: str) -> List[Dict[str, object]]:
    matches: List[Dict[str, object]] = []
    for filename, path in sorted(files.items()):
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    stripped = raw_line.strip()
                    if not stripped:
                        continue
                    first_token = stripped.split(maxsplit=1)[0]
                    if first_token == class_name:
                        matches.append({"file": filename, "line": line_number})
                        break
        except OSError as exc:
            matches.append({"file": filename, "line": None, "error": str(exc)})
    return matches


def ensure_safe_backup_root(backup_root: Path, gt_dir: Path, dr_dir: Path) -> Path:
    backup_root = resolve_path(backup_root)
    if backup_root == gt_dir or backup_root == dr_dir:
        raise ValueError("backup root must not be the GT or DR folder itself")
    if is_relative_to(backup_root, gt_dir) or is_relative_to(backup_root, dr_dir):
        raise ValueError(
            "backup root must be outside the GT and DR folders to avoid hiding "
            "moved files inside evaluator input directories"
        )
    return backup_root


def plan_move_targets(
    files: Dict[str, Path], filenames: Iterable[str], backup_root: Path, side: str
) -> List[Dict[str, str]]:
    targets: List[Dict[str, str]] = []
    for filename in sorted(filenames):
        source = files[filename]
        destination = backup_root / side / filename
        targets.append({"source": str(source), "destination": str(destination)})
    return targets


def perform_moves(move_plan: List[Dict[str, str]]) -> List[Dict[str, str]]:
    moved: List[Dict[str, str]] = []
    for item in move_plan:
        source = Path(item["source"])
        destination = Path(item["destination"])
        if destination.exists():
            raise ValueError(f"backup target already exists: {destination}")
    for item in move_plan:
        source = Path(item["source"])
        destination = Path(item["destination"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        moved.append({"source": str(source), "destination": str(destination)})
    return moved


def summarize_status(report: Dict[str, object], compare_key: str = "final") -> int:
    """Return process exit code: 0 ready, 1 readiness issue, 2 command/path error."""
    if report["errors"]:
        return 2
    compare = report[compare_key]
    readiness_issue = False
    if compare["gt_count"] == 0 or compare["dr_count"] == 0:
        readiness_issue = True
    if compare["gt_only"] or compare["dr_only"]:
        readiness_issue = True
    if compare["intersection_count"] == 0:
        readiness_issue = True
    lookup = report.get("class_lookup")
    if lookup:
        gt_matches = lookup[GT_LABEL]
        dr_matches = lookup[DR_LABEL]
        if not gt_matches and not dr_matches:
            readiness_issue = True
    return 1 if readiness_issue else 0


def limited(names: Iterable[str], max_items: int) -> Tuple[List[str], int]:
    names = list(names)
    return names[:max_items], max(0, len(names) - max_items)


def print_name_list(title: str, names: Iterable[str], max_items: int) -> None:
    shown, remaining = limited(names, max_items)
    if not shown:
        print(f"  {title}: none")
        return
    print(f"  {title}:")
    for name in shown:
        print(f"    - {name}")
    if remaining:
        print(f"    ... {remaining} more")


def render_report(report: Dict[str, object], max_list: int) -> None:
    print("mAP input validation report")
    print(f"  ground-truth folder: {report['gt_dir']}")
    print(f"  detection-results folder: {report['dr_dir']}")
    print()

    for message in report["errors"]:
        print(f"ERROR: {message}")
    for message in report["warnings"]:
        print(f"WARNING: {message}")
    if report["errors"] or report["warnings"]:
        print()

    initial = report["initial"]
    print("Initial file-set summary")
    print(f"  total ground-truth .txt files: {initial['gt_count']}")
    print(f"  total detection-results .txt files: {initial['dr_count']}")
    print(f"  intersecting filenames: {initial['intersection_count']}")
    if initial["same_count"] and (initial["gt_only"] or initial["dr_only"]):
        print("  note: folders have the same count but different basenames")
    print_name_list("GT-only files", initial["gt_only"], max_list)
    print_name_list("DR-only files", initial["dr_only"], max_list)
    print()

    move_plan = report.get("move_plan", [])
    if move_plan:
        print("Move plan for non-intersecting files")
        for item in move_plan[:max_list]:
            print(f"  {item['source']} -> {item['destination']}")
        if len(move_plan) > max_list:
            print(f"  ... {len(move_plan) - max_list} more")
        if report.get("moved"):
            print(f"  moved files: {len(report['moved'])}")
        else:
            print("  dry-run only: no files moved")
        print()

    if report["final"] != report["initial"]:
        final = report["final"]
        print("Final file-set summary")
        print(f"  total ground-truth .txt files: {final['gt_count']}")
        print(f"  total detection-results .txt files: {final['dr_count']}")
        print(f"  intersecting filenames: {final['intersection_count']}")
        print_name_list("remaining GT-only files", final["gt_only"], max_list)
        print_name_list("remaining DR-only files", final["dr_only"], max_list)
        print()

    lookup = report.get("class_lookup")
    if lookup:
        print(f"Class lookup: {lookup['class_name']}")
        for side in (GT_LABEL, DR_LABEL):
            matches = lookup[side]
            if matches:
                print(f"  {side} files containing class:")
                for item in matches[:max_list]:
                    line = item.get("line")
                    suffix = f" line {line}" if line else ""
                    print(f"    - {item['file']}{suffix}")
                if len(matches) > max_list:
                    print(f"    ... {len(matches) - max_list} more")
            else:
                print(f"  {side} files containing class: none")
        print()

    status = "READY" if summarize_status(report) == 0 else "NOT READY"
    print(f"Status: {status}")
    if status != "READY":
        print(
            "Next action: fix empty folders, mismatched basenames, or missing class "
            "evidence before running mAP evaluation."
        )


def build_report(args: argparse.Namespace) -> Dict[str, object]:
    gt_dir = resolve_path(args.gt_dir)
    dr_dir = resolve_path(args.dr_dir)
    report: Dict[str, object] = {
        "gt_dir": str(gt_dir),
        "dr_dir": str(dr_dir),
        "errors": [],
        "warnings": [],
        "move_plan": [],
        "moved": [],
    }

    if gt_dir == dr_dir:
        report["errors"].append("GT and DR paths are identical; choose separate folders")

    try:
        gt_files, gt_non_txt = scan_txt_dir(gt_dir)
        dr_files, dr_non_txt = scan_txt_dir(dr_dir)
    except ValueError as exc:
        report["errors"].append(str(exc))
        report["initial"] = compare_sets({}, {})
        report["final"] = report["initial"]
        return report

    if gt_non_txt:
        report["warnings"].append(
            f"{GT_LABEL} folder contains {len(gt_non_txt)} non-.txt top-level files; "
            "mAP matching uses .txt files"
        )
    if dr_non_txt:
        report["warnings"].append(
            f"{DR_LABEL} folder contains {len(dr_non_txt)} non-.txt top-level files; "
            "mAP matching uses .txt files"
        )

    initial = compare_sets(gt_files, dr_files)
    report["initial"] = initial

    if args.move_extra_to:
        try:
            backup_root = ensure_safe_backup_root(args.move_extra_to, gt_dir, dr_dir)
            report["backup_root"] = str(backup_root)
            move_plan = plan_move_targets(gt_files, initial["gt_only"], backup_root, GT_LABEL)
            move_plan.extend(plan_move_targets(dr_files, initial["dr_only"], backup_root, DR_LABEL))
            report["move_plan"] = move_plan
            if args.confirm_move:
                if not move_plan:
                    report["warnings"].append("no non-intersecting .txt files require moving")
                elif initial["intersection_count"] == 0:
                    report["errors"].append(
                        "refusing to move because the GT/DR intersection is empty; "
                        "this usually indicates wrong paths or incompatible naming"
                    )
                else:
                    report["moved"] = perform_moves(move_plan)
                    gt_files, gt_non_txt = scan_txt_dir(gt_dir)
                    dr_files, dr_non_txt = scan_txt_dir(dr_dir)
            else:
                report["warnings"].append(
                    "--move-extra-to was supplied without --confirm-move; reporting "
                    "the move plan only"
                )
        except ValueError as exc:
            report["errors"].append(str(exc))

    final = compare_sets(gt_files, dr_files)
    report["final"] = final

    if args.class_name:
        report["class_lookup"] = {
            "class_name": args.class_name,
            GT_LABEL: find_class(gt_files, args.class_name),
            DR_LABEL: find_class(dr_files, args.class_name),
        }

    if initial["gt_count"] == 0:
        report["warnings"].append("ground-truth folder has no top-level .txt files")
    if initial["dr_count"] == 0:
        report["warnings"].append("detection-results folder has no top-level .txt files")
    if initial["intersection_count"] == 0 and initial["gt_count"] and initial["dr_count"]:
        report["warnings"].append(
            "ground-truth and detection-results folders have no matching .txt filenames"
        )

    return report


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    report = build_report(args)
    render_report(report, args.max_list)
    if args.json_report:
        json_path = resolve_path(args.json_report)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"JSON report written to: {json_path}")
    return summarize_status(report)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
