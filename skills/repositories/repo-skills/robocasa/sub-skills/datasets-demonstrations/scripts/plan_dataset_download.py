#!/usr/bin/env python3
"""Resolve RoboCasa dataset registry entries without downloading or writing data.

This planner imports the installed RoboCasa registry, reports expected local
paths, and prints explicit dry-run/real commands for the package downloader.
It never executes those commands and never contacts the network.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


class PlanningError(RuntimeError):
    """Raised for invalid or unavailable registry selections."""


def _import_registry(dataset_base_path: Path | None):
    try:
        import robocasa.macros as macros

        if dataset_base_path is not None:
            # Process-local override only; no configuration file is modified.
            macros.DATASET_BASE_PATH = str(dataset_base_path.expanduser().resolve())

        from robocasa.utils.dataset_registry import (
            DATASET_SOUP_REGISTRY,
            TASK_SET_REGISTRY,
        )
        from robocasa.utils.dataset_registry_utils import get_ds_meta, get_ds_soup
    except Exception as exc:
        raise PlanningError(
            "cannot import the installed RoboCasa dataset registry: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return TASK_SET_REGISTRY, DATASET_SOUP_REGISTRY, get_ds_meta, get_ds_soup


def _registry_source(source: str) -> str:
    return "mg" if source == "mimicgen" else source


def _download_source(source: str) -> str | None:
    # The native CLI only exposes the main human and MimicGen variants. Do not
    # silently map co-training camera or ablation entries to a different archive.
    if source == "human":
        return "human"
    if source == "mg":
        return "mimicgen"
    return None


def _normalize_meta(meta: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(meta)
    path = Path(normalized["path"]).expanduser()
    normalized["path"] = str(path)
    normalized["local_exists"] = path.is_dir()
    return normalized


def _select_entries(args: argparse.Namespace, task_sets, soups, get_ds_meta, get_ds_soup):
    if args.soup is not None:
        if args.soup not in soups:
            raise PlanningError(
                f"unknown soup {args.soup!r}; use --list-soups to inspect registered names"
            )
        if args.demo_fraction != 1.0:
            raise PlanningError(
                "--demo-fraction cannot rewrite a pre-registered soup; use --task-set instead"
            )
        return [dict(meta) for meta in soups[args.soup]], {"soup": args.soup}

    source = _registry_source(args.source)
    if args.task_set is not None:
        if args.task_set not in task_sets:
            raise PlanningError(
                f"unknown task set {args.task_set!r}; use --list-task-sets to inspect names"
            )
        entries = get_ds_soup(
            split=args.split,
            task_set=args.task_set,
            source=source,
            demo_fraction=args.demo_fraction,
        )
        return entries, {
            "task_set": args.task_set,
            "split": args.split,
            "source": source,
            "demo_fraction": args.demo_fraction,
        }

    if args.tasks is None:
        raise PlanningError("select --tasks, --task-set, or --soup")

    sources = ("human", "mg") if source == "all" else (source,)
    entries = []
    unknown_tasks = []
    for task in args.tasks:
        recognized = False
        for one_source in sources:
            try:
                meta = get_ds_meta(
                    task=task,
                    split=args.split,
                    source=one_source,
                    demo_fraction=args.demo_fraction,
                )
            except ValueError:
                meta = None
            except AssertionError as exc:
                raise PlanningError(
                    f"invalid registry combination for task={task!r}, split={args.split!r}, "
                    f"source={one_source!r}: {exc}"
                ) from exc
            if meta is not None:
                recognized = True
                entries.append(meta)
        if not recognized:
            unknown_tasks.append(task)
    if unknown_tasks:
        raise PlanningError(
            "no matching registered dataset for task(s): " + ", ".join(unknown_tasks)
        )
    return entries, {
        "tasks": args.tasks,
        "split": args.split,
        "source": source,
        "demo_fraction": args.demo_fraction,
    }


def _commands(entries: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    unsupported = []
    for entry in entries:
        split = entry.get("split")
        download_source = _download_source(entry.get("source", ""))
        if split not in {"pretrain", "target"} or download_source is None:
            unsupported.append(
                f"{entry.get('task')} ({entry.get('split')}/{entry.get('source')})"
            )
            continue
        grouped[(split, download_source)].add(entry["task"])

    commands = []
    for (split, source), tasks in sorted(grouped.items()):
        command = [
            "python",
            "-m",
            "robocasa.scripts.download_datasets",
            "--tasks",
            *sorted(tasks),
            "--split",
            split,
            "--source",
            source,
            "--dryrun",
        ]
        commands.append(shlex.join(command))
    return commands, unsupported


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plan RoboCasa dataset locations and opt-in downloader commands. "
            "This command performs no network or filesystem writes."
        )
    )
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--tasks", nargs="+", help="one or more exact registry task names")
    selector.add_argument("--task-set", help="registered task_set passed to get_ds_soup")
    selector.add_argument("--soup", help="pre-registered DATASET_SOUP_REGISTRY name")
    parser.add_argument(
        "--split",
        choices=("pretrain", "target", "real"),
        default="target",
        help="registry split for --tasks or --task-set",
    )
    parser.add_argument(
        "--source",
        choices=("human", "mimicgen", "all"),
        default="human",
        help="main dataset source; mimicgen is mapped to the registry's 'mg' token",
    )
    parser.add_argument(
        "--demo-fraction",
        type=float,
        default=1.0,
        help="fraction used to derive filter_key; must be in (0, 1]",
    )
    parser.add_argument(
        "--dataset-base-path",
        type=Path,
        default=None,
        help="process-local DATASET_BASE_PATH override used only for this plan",
    )
    parser.add_argument("--list-task-sets", action="store_true")
    parser.add_argument("--list-soups", action="store_true")
    parser.add_argument(
        "--require-local",
        action="store_true",
        help="exit 2 when any selected registered path is absent locally",
    )
    parser.add_argument("--json", action="store_true", help="emit compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0.0 < args.demo_fraction <= 1.0:
        print("ERROR: --demo-fraction must be in (0, 1]", file=sys.stderr)
        return 2

    try:
        task_sets, soups, get_ds_meta, get_ds_soup = _import_registry(
            args.dataset_base_path
        )
        if args.list_task_sets or args.list_soups:
            listing = {}
            if args.list_task_sets:
                listing["task_sets"] = {
                    name: len(tasks) for name, tasks in sorted(task_sets.items())
                }
            if args.list_soups:
                listing["soups"] = {
                    name: len(entries) for name, entries in sorted(soups.items())
                }
            print(json.dumps(listing, indent=None if args.json else 2, sort_keys=True))
            return 0

        entries, selection = _select_entries(
            args, task_sets, soups, get_ds_meta, get_ds_soup
        )
        normalized = [_normalize_meta(meta) for meta in entries]
        dryrun_commands, unsupported = _commands(entries)
    except PlanningError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (AssertionError, ValueError) as exc:
        print(f"ERROR: invalid registry query: {exc}", file=sys.stderr)
        return 2

    missing = [entry["path"] for entry in normalized if not entry["local_exists"]]
    result = {
        "network_or_writes_performed": False,
        "selection": selection,
        "entries": normalized,
        "summary": {
            "registered": len(normalized),
            "local": len(normalized) - len(missing),
            "missing": len(missing),
        },
        "opt_in_download": {
            "dryrun_commands": dryrun_commands,
            "real_command_rule": "remove --dryrun only after approving network use, storage, and destination",
            "unsupported_registry_entries": unsupported,
            "notes": [
                "The package downloader prompts before both dry-run and real modes.",
                "A process-local --dataset-base-path override is not inherited by a later downloader process; configure DATASET_BASE_PATH there too.",
                "The downloader can fetch several GB and extracts archives into the configured dataset root.",
            ],
        },
    }
    print(json.dumps(result, indent=None if args.json else 2, sort_keys=True))

    if args.require_local and missing:
        print(
            "ERROR: registry entries were found but local dataset paths are absent; no download was attempted.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
