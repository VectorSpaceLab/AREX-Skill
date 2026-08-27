#!/usr/bin/env python3
"""Dry-run planner for ModelScope legacy .pth checkpoint conversion.

The repository utility ``convert_ckpt.py`` iterates over direct ``*.pth`` files in
one directory, copies each original file to ``<name>.pth.legacy``, overwrites the
original ``.pth`` with the checkpoint state_dict, and writes a companion
``<stem>_trainer_state.pth`` file.

This planner is intentionally read-only: it never imports torch, never opens
checkpoint payloads, and never writes files. It reports path-level side effects
and file-size estimates so a caller can decide whether to run a destructive
conversion on a backed-up copy.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class PlannedCheckpoint:
    source: str
    size_bytes: int
    legacy_backup: str
    trainer_state: str
    source_will_be_overwritten: bool
    legacy_backup_exists: bool
    trainer_state_exists: bool
    notes: List[str]


@dataclass(frozen=True)
class Plan:
    directory: str
    checkpoint_count: int
    total_source_bytes: int
    estimated_min_extra_bytes: int
    has_collisions: bool
    checkpoints: List[PlannedCheckpoint]


def _human_size(num_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def _direct_pth_files(directory: Path) -> Iterable[Path]:
    # Match the source utility's non-recursive os.listdir(folder) + endswith('.pth')
    # behavior, but return a deterministic sorted order for review.
    for child in sorted(directory.iterdir(), key=lambda p: p.name):
        if child.is_file() and child.name.endswith(".pth"):
            yield child


def build_plan(directory: Path) -> Plan:
    directory = directory.expanduser().resolve()
    if not directory.exists():
        raise FileNotFoundError(f"directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"not a directory: {directory}")

    checkpoints: List[PlannedCheckpoint] = []
    total_source_bytes = 0
    estimated_min_extra_bytes = 0
    has_collisions = False

    for source in _direct_pth_files(directory):
        stat = source.stat()
        size = stat.st_size
        total_source_bytes += size
        # convert_ckpt.py copies /path/model.pth to /path/model.pth.legacy.
        legacy = Path(str(source) + ".legacy")
        # os.path.splitext('/path/model.pth') -> ('/path/model', '.pth')
        trainer_state = source.with_name(f"{source.stem}_trainer_state{source.suffix}")

        legacy_exists = legacy.exists()
        trainer_exists = trainer_state.exists()
        notes: List[str] = [
            "would copy source to legacy backup before conversion",
            "would overwrite source .pth in place with extracted state_dict/module data",
            "would write companion trainer_state file",
        ]
        if legacy_exists:
            notes.append("collision: legacy backup path already exists and would be overwritten by shutil.copy")
            has_collisions = True
        if trainer_exists:
            notes.append("collision: trainer_state path already exists and would be overwritten by torch.save")
            has_collisions = True
        if source.name.endswith("_trainer_state.pth"):
            notes.append("source itself looks like a trainer_state file; the converter would still process it because it ends with .pth")
        if source.name.endswith(".pth.legacy"):
            # Not reachable with endswith('.pth'), kept for clarity if suffix logic changes.
            notes.append("legacy-looking file detected")

        # Minimum extra disk: the full .legacy copy is guaranteed. The trainer
        # state size is unknowable without loading the checkpoint, so do not fake
        # precision; callers should budget more than this minimum.
        estimated_min_extra_bytes += size

        checkpoints.append(
            PlannedCheckpoint(
                source=str(source),
                size_bytes=size,
                legacy_backup=str(legacy),
                trainer_state=str(trainer_state),
                source_will_be_overwritten=True,
                legacy_backup_exists=legacy_exists,
                trainer_state_exists=trainer_exists,
                notes=notes,
            )
        )

    return Plan(
        directory=str(directory),
        checkpoint_count=len(checkpoints),
        total_source_bytes=total_source_bytes,
        estimated_min_extra_bytes=estimated_min_extra_bytes,
        has_collisions=has_collisions,
        checkpoints=checkpoints,
    )


def print_text(plan: Plan) -> None:
    print("ModelScope convert_ckpt dry-run plan")
    print(f"Directory: {plan.directory}")
    print(f"Direct .pth files: {plan.checkpoint_count}")
    print(f"Total source size: {_human_size(plan.total_source_bytes)}")
    print(
        "Estimated minimum extra disk for .legacy copies: "
        f"{_human_size(plan.estimated_min_extra_bytes)}"
    )
    print("Trainer-state output size is unknown until checkpoints are loaded.")
    print(f"Existing output collisions: {'yes' if plan.has_collisions else 'no'}")
    print()

    if not plan.checkpoints:
        print("No direct *.pth files found. The source utility would take no per-file actions.")
        return

    for index, item in enumerate(plan.checkpoints, start=1):
        print(f"[{index}] {item.source}")
        print(f"    size: {_human_size(item.size_bytes)}")
        print(f"    would create/overwrite legacy backup: {item.legacy_backup}")
        print(f"    would overwrite source in place: {item.source_will_be_overwritten}")
        print(f"    would create/overwrite trainer state: {item.trainer_state}")
        if item.legacy_backup_exists or item.trainer_state_exists:
            print("    collisions:")
            if item.legacy_backup_exists:
                print("      - legacy backup path already exists")
            if item.trainer_state_exists:
                print("      - trainer_state path already exists")
        print("    notes:")
        for note in item.notes:
            print(f"      - {note}")
        print()

    print("Safety gate: run the real converter only on a backed-up copy after reviewing this plan.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only dry-run planner for ModelScope convert_ckpt.py side effects. "
            "Scans only direct *.pth files in a directory and never writes files."
        )
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Directory containing direct *.pth files to plan for conversion.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = build_plan(Path(args.dir))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(plan), indent=2, sort_keys=True))
    else:
        print_text(plan)
    # Collisions make the plan risky, but the command itself succeeded. Return 0
    # so --help/automation can parse the report without treating this dry run as
    # a failed process.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
