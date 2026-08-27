#!/usr/bin/env python3
"""Print a KAIR VRT/RVRT video restoration test command.

This helper is intentionally self-contained: it does not import KAIR, does not
check files, does not download checkpoints, and does not run inference. Run the
printed command from a KAIR checkout after reviewing compute and download risks.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class TaskInfo:
    task: str
    default_tile: Tuple[int, int, int]
    default_overlap: Tuple[int, int, int]
    default_sigma: Optional[int] = None


TASKS: Dict[str, Dict[str, TaskInfo]] = {
    "vrt": {
        "001": TaskInfo("001_VRT_videosr_bi_REDS_6frames", (40, 128, 128), (2, 20, 20)),
        "002": TaskInfo("002_VRT_videosr_bi_REDS_16frames", (40, 128, 128), (2, 20, 20)),
        "003": TaskInfo("003_VRT_videosr_bi_Vimeo_7frames", (32, 128, 128), (2, 20, 20)),
        "004": TaskInfo("004_VRT_videosr_bd_Vimeo_7frames", (32, 128, 128), (2, 20, 20)),
        "005": TaskInfo("005_VRT_videodeblurring_DVD", (12, 256, 256), (2, 20, 20)),
        "006": TaskInfo("006_VRT_videodeblurring_GoPro", (18, 192, 192), (2, 20, 20)),
        "007": TaskInfo("007_VRT_videodeblurring_REDS", (12, 256, 256), (2, 20, 20)),
        "008": TaskInfo("008_VRT_videodenoising_DAVIS", (12, 256, 256), (2, 20, 20), default_sigma=10),
        "009": TaskInfo("009_VRT_videofi_Vimeo_4frames", (0, 0, 0), (0, 0, 0)),
    },
    "rvrt": {
        "001": TaskInfo("001_RVRT_videosr_bi_REDS_30frames", (100, 128, 128), (2, 20, 20)),
        "002": TaskInfo("002_RVRT_videosr_bi_Vimeo_14frames", (0, 0, 0), (2, 20, 20)),
        "003": TaskInfo("003_RVRT_videosr_bd_Vimeo_14frames", (0, 0, 0), (2, 20, 20)),
        "004": TaskInfo("004_RVRT_videodeblurring_DVD_16frames", (0, 256, 256), (2, 20, 20)),
        "005": TaskInfo("005_RVRT_videodeblurring_GoPro_16frames", (0, 256, 256), (2, 20, 20)),
        "006": TaskInfo("006_RVRT_videodenoising_DAVIS_16frames", (0, 256, 256), (2, 20, 20), default_sigma=50),
    },
}


def normalize_task_id(family: str, raw: str) -> str:
    """Return canonical three-digit task ID for numeric or full task inputs."""
    raw = raw.strip()
    family_tasks = TASKS[family]
    if raw in family_tasks:
        return raw
    if raw.isdigit():
        padded = f"{int(raw):03d}"
        if padded in family_tasks:
            return padded
    for task_id, info in family_tasks.items():
        if raw == info.task:
            return task_id
    allowed = ", ".join(sorted(family_tasks))
    raise SystemExit(f"Unsupported {family.upper()} task-id {raw!r}. Allowed IDs: {allowed}")


def three_ints(values: Optional[Iterable[int]], name: str) -> Optional[Tuple[int, int, int]]:
    if values is None:
        return None
    items = tuple(values)
    if len(items) != 3:
        raise SystemExit(f"{name} requires exactly three integers")
    if any(v < 0 for v in items):
        raise SystemExit(f"{name} values must be non-negative")
    return items  # type: ignore[return-value]


def quote_command(parts: List[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a KAIR main_test_vrt.py or main_test_rvrt.py command without running it."
    )
    parser.add_argument("--family", required=True, choices=sorted(TASKS), help="Model family: vrt or rvrt.")
    parser.add_argument(
        "--task-id",
        required=True,
        help="Three-digit task ID such as 001, numeric ID such as 1, or the full KAIR task string.",
    )
    parser.add_argument("--folder-lq", required=True, help="Input low-quality video folder passed as --folder_lq.")
    parser.add_argument("--folder-gt", default=None, help="Optional ground-truth folder passed as --folder_gt.")
    parser.add_argument("--sigma", type=int, default=None, help="Noise level for denoising tasks.")
    parser.add_argument(
        "--tile",
        type=int,
        nargs=3,
        metavar=("T", "H", "W"),
        help="Tile triplet. Defaults to the KAIR example for the selected task.",
    )
    parser.add_argument(
        "--tile-overlap",
        type=int,
        nargs=3,
        metavar=("T", "H", "W"),
        help="Tile overlap triplet. Defaults to the KAIR example for the selected task.",
    )
    parser.add_argument("--num-workers", type=int, default=None, help="Optional --num_workers override.")
    parser.add_argument("--save-result", action="store_true", help="Append KAIR's --save_result flag.")
    parser.add_argument("--python", default="python", help="Python executable token to print. Default: python.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    family = args.family.lower()
    task_id = normalize_task_id(family, args.task_id)
    info = TASKS[family][task_id]

    tile = three_ints(args.tile, "--tile") or info.default_tile
    overlap = three_ints(args.tile_overlap, "--tile-overlap") or info.default_overlap

    if any(t and o >= t for t, o in zip(tile, overlap)):
        raise SystemExit("Each nonzero tile value must be greater than its corresponding overlap value")
    if tile[1] and tile[1] % 8 != 0:
        raise SystemExit("Spatial tile H should be a multiple of 8 for KAIR VRT/RVRT tasks")
    if tile[2] and tile[2] % 8 != 0:
        raise SystemExit("Spatial tile W should be a multiple of 8 for KAIR VRT/RVRT tasks")

    script_name = "main_test_vrt.py" if family == "vrt" else "main_test_rvrt.py"
    cmd = [
        args.python,
        script_name,
        "--task",
        info.task,
        "--folder_lq",
        args.folder_lq,
    ]
    if args.folder_gt:
        cmd.extend(["--folder_gt", args.folder_gt])

    sigma = args.sigma if args.sigma is not None else info.default_sigma
    if sigma is not None:
        if sigma < 0:
            raise SystemExit("--sigma must be non-negative")
        cmd.extend(["--sigma", str(sigma)])

    cmd.extend(["--tile", *(str(v) for v in tile)])
    cmd.extend(["--tile_overlap", *(str(v) for v in overlap)])

    if args.num_workers is not None:
        if args.num_workers < 0:
            raise SystemExit("--num-workers must be non-negative")
        cmd.extend(["--num_workers", str(args.num_workers)])

    if args.save_result:
        cmd.append("--save_result")

    print(quote_command(cmd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
