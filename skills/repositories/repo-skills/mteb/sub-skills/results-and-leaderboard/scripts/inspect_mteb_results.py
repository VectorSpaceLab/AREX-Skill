#!/usr/bin/env python3
"""Inspect an MTEB result cache or results folder without network access.

The script intentionally avoids importing mteb so it can run in lightweight CI or
on partially broken environments. It validates folder shape and basic JSON fields;
it does not verify scores against live task metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TaskFileSummary:
    path: str
    task_name: str | None
    splits: list[str]
    score_entries: int
    main_score_entries: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class RevisionSummary:
    source: str
    model_folder: str
    revision: str
    path: str
    has_model_meta: bool
    model_name: str | None
    model_revision: str | None
    task_files: list[TaskFileSummary] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect an MTEB ResultCache root, results directory, or one model/revision result folder."
    )
    parser.add_argument("path", type=Path, help="Cache root or result folder to inspect")
    parser.add_argument(
        "--require-model-meta",
        action="store_true",
        help="Report missing model_meta.json as an error condition",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary",
    )
    parser.add_argument(
        "--max-task-files",
        type=int,
        default=20,
        help="Maximum task files to print per revision in text mode",
    )
    return parser.parse_args()


def load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should keep scanning
        return None, f"{type(exc).__name__}: {exc}"


def candidate_result_roots(path: Path) -> list[tuple[str, Path]]:
    roots: list[tuple[str, Path]] = []
    if (path / "results").is_dir():
        roots.append(("local", path / "results"))
    if (path / "remote" / "results").is_dir():
        roots.append(("remote", path / "remote" / "results"))
    if path.name == "results" and path.is_dir():
        roots.append(("results", path))
    if any(path.glob("*.json")):
        roots.append(("single-revision", path.parent.parent if path.parent.parent.exists() else path))
    if not roots and path.is_dir():
        roots.append(("given", path))
    return roots


def revision_dirs(root: Path) -> list[Path]:
    if (root / "model_meta.json").is_file() or any(
        child.suffix == ".json" and child.name != "model_meta.json" for child in root.iterdir() if child.is_file()
    ):
        return [root]

    revisions: list[Path] = []
    for model_dir in sorted(child for child in root.iterdir() if child.is_dir()):
        for rev_dir in sorted(child for child in model_dir.iterdir() if child.is_dir()):
            if (rev_dir / "model_meta.json").is_file() or any(
                item.suffix == ".json" and item.name != "model_meta.json" for item in rev_dir.iterdir() if item.is_file()
            ):
                revisions.append(rev_dir)
            experiments_dir = rev_dir / "experiments"
            if experiments_dir.is_dir():
                for experiment_dir in sorted(child for child in experiments_dir.iterdir() if child.is_dir()):
                    if any(item.suffix == ".json" for item in experiment_dir.iterdir() if item.is_file()):
                        revisions.append(experiment_dir)
    return revisions


def inspect_task_file(path: Path) -> TaskFileSummary:
    data, error = load_json(path)
    if error is not None:
        return TaskFileSummary(
            path=str(path),
            task_name=None,
            splits=[],
            score_entries=0,
            main_score_entries=0,
            warnings=[f"invalid JSON: {error}"],
        )

    warnings: list[str] = []
    if not isinstance(data, dict):
        return TaskFileSummary(
            path=str(path),
            task_name=None,
            splits=[],
            score_entries=0,
            main_score_entries=0,
            warnings=["top-level JSON is not an object"],
        )

    task_name = data.get("task_name")
    if not isinstance(task_name, str):
        warnings.append("missing or non-string task_name")
    elif task_name != path.stem:
        warnings.append(f"filename task {path.stem!r} differs from task_name {task_name!r}")

    if "dataset_revision" not in data:
        warnings.append("missing dataset_revision")
    if "mteb_version" not in data:
        warnings.append("missing mteb_version")

    scores = data.get("scores")
    if not isinstance(scores, dict):
        return TaskFileSummary(
            path=str(path),
            task_name=task_name if isinstance(task_name, str) else None,
            splits=[],
            score_entries=0,
            main_score_entries=0,
            warnings=warnings + ["missing or non-object scores"],
        )

    splits = sorted(str(split) for split in scores.keys())
    score_entries = 0
    main_score_entries = 0
    for split, entries in scores.items():
        if not isinstance(entries, list):
            warnings.append(f"split {split!r} scores is not a list")
            continue
        if not entries:
            warnings.append(f"split {split!r} has no score entries")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                warnings.append(f"split {split!r} entry {index} is not an object")
                continue
            score_entries += 1
            if "main_score" in entry:
                main_score_entries += 1
            else:
                warnings.append(f"split {split!r} entry {index} missing main_score")
            if "hf_subset" not in entry:
                warnings.append(f"split {split!r} entry {index} missing hf_subset")
            if "languages" not in entry:
                warnings.append(f"split {split!r} entry {index} missing languages")

    return TaskFileSummary(
        path=str(path),
        task_name=task_name if isinstance(task_name, str) else None,
        splits=splits,
        score_entries=score_entries,
        main_score_entries=main_score_entries,
        warnings=warnings,
    )


def inspect_revision(source: str, rev_dir: Path, require_model_meta: bool) -> RevisionSummary:
    meta_path = rev_dir / "model_meta.json"
    has_model_meta = meta_path.is_file()
    model_name = None
    model_revision = None
    warnings: list[str] = []

    if has_model_meta:
        data, error = load_json(meta_path)
        if error is not None:
            warnings.append(f"invalid model_meta.json: {error}")
        elif not isinstance(data, dict):
            warnings.append("model_meta.json top-level JSON is not an object")
        else:
            raw_name = data.get("name")
            raw_revision = data.get("revision")
            if isinstance(raw_name, str):
                model_name = raw_name
            else:
                warnings.append("model_meta.json missing string name")
            if isinstance(raw_revision, str) or raw_revision is None:
                model_revision = raw_revision
            else:
                warnings.append("model_meta.json revision is not a string or null")
    elif require_model_meta:
        warnings.append("missing model_meta.json")

    task_files = [
        inspect_task_file(path)
        for path in sorted(rev_dir.glob("*.json"))
        if path.name != "model_meta.json"
    ]
    if not task_files:
        warnings.append("no task JSON files found")

    if rev_dir.parent.name == "experiments" and rev_dir.parent.parent.exists():
        model_folder = rev_dir.parent.parent.parent.name
        revision = f"{rev_dir.parent.parent.name}/experiments/{rev_dir.name}"
    elif rev_dir.parent.exists():
        model_folder = rev_dir.parent.name
        revision = rev_dir.name
    else:
        model_folder = "unknown"
        revision = rev_dir.name

    return RevisionSummary(
        source=source,
        model_folder=model_folder,
        revision=revision,
        path=str(rev_dir),
        has_model_meta=has_model_meta,
        model_name=model_name,
        model_revision=model_revision,
        task_files=task_files,
        warnings=warnings,
    )


def as_dict(summary: RevisionSummary) -> dict[str, Any]:
    return {
        "source": summary.source,
        "model_folder": summary.model_folder,
        "revision": summary.revision,
        "path": summary.path,
        "has_model_meta": summary.has_model_meta,
        "model_name": summary.model_name,
        "model_revision": summary.model_revision,
        "task_count": len(summary.task_files),
        "score_entries": sum(task.score_entries for task in summary.task_files),
        "warnings": summary.warnings,
        "task_files": [task.__dict__ for task in summary.task_files],
    }


def print_text(summaries: list[RevisionSummary], max_task_files: int) -> None:
    total_tasks = sum(len(summary.task_files) for summary in summaries)
    total_warnings = sum(len(summary.warnings) for summary in summaries) + sum(
        len(task.warnings) for summary in summaries for task in summary.task_files
    )
    print(f"MTEB result folders: {len(summaries)}")
    print(f"Task JSON files: {total_tasks}")
    print(f"Warnings: {total_warnings}")

    for summary in summaries:
        model_label = summary.model_name or summary.model_folder
        revision_label = summary.model_revision or summary.revision
        print(f"\n[{summary.source}] {model_label} @ {revision_label}")
        print(f"  path: {summary.path}")
        print(f"  model_meta: {'yes' if summary.has_model_meta else 'no'}")
        print(f"  task_files: {len(summary.task_files)}")
        for warning in summary.warnings:
            print(f"  warning: {warning}")

        for task in summary.task_files[:max_task_files]:
            task_name = task.task_name or Path(task.path).stem
            split_text = ",".join(task.splits) if task.splits else "none"
            print(
                f"  - {task_name}: splits={split_text}; "
                f"scores={task.score_entries}; main_scores={task.main_score_entries}"
            )
            for warning in task.warnings[:5]:
                print(f"    warning: {warning}")
            if len(task.warnings) > 5:
                print(f"    warning: ... {len(task.warnings) - 5} more")
        hidden = len(summary.task_files) - max_task_files
        if hidden > 0:
            print(f"  ... {hidden} more task files")


def main() -> int:
    args = parse_args()
    target = args.path.expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {args.path}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"error: path is not a directory: {args.path}", file=sys.stderr)
        return 2

    summaries: list[RevisionSummary] = []
    for source, root in candidate_result_roots(target):
        for rev_dir in revision_dirs(root):
            summaries.append(inspect_revision(source, rev_dir, args.require_model_meta))

    summaries.sort(key=lambda item: (item.source, item.model_folder, item.revision, item.path))

    if args.json:
        print(json.dumps([as_dict(summary) for summary in summaries], indent=2, sort_keys=True))
    else:
        print_text(summaries, args.max_task_files)

    blocking_warnings = [
        warning
        for summary in summaries
        for warning in summary.warnings
        if args.require_model_meta and warning == "missing model_meta.json"
    ]
    invalid_json_warnings = [
        warning
        for summary in summaries
        for task in summary.task_files
        for warning in task.warnings
        if warning.startswith("invalid JSON")
    ]
    if not summaries:
        return 1
    if blocking_warnings or invalid_json_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
