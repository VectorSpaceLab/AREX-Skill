#!/usr/bin/env python3
"""Validate ECCV2022-RIFE benchmark layouts without downloads or benchmark execution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

ALL_BENCHMARKS = [
    "testtime",
    "ucf101",
    "vimeo90k",
    "middlebury",
    "atd12k",
    "hd",
    "hd_multi_4x",
]

SCRIPT_PATHS = {
    "testtime": "benchmark/testtime.py",
    "ucf101": "benchmark/UCF101.py",
    "vimeo90k": "benchmark/Vimeo90K.py",
    "middlebury": "benchmark/MiddleBury_Other.py",
    "atd12k": "benchmark/ATD12K.py",
    "hd": "benchmark/HD.py",
    "hd_multi_4x": "benchmark/HD_multi_4X.py",
}

MIDDLEBURY_NAMES = [
    "Beanbags",
    "Dimetrodon",
    "DogDance",
    "Grove2",
    "Grove3",
    "Hydrangea",
    "MiniCooper",
    "RubberWhale",
    "Urban2",
    "Urban3",
    "Venus",
    "Walking",
]

HD_FILES: Sequence[Tuple[str, int, int]] = [
    ("HD_dataset/HD720p_GT/parkrun_1280x720_50.yuv", 720, 1280),
    ("HD_dataset/HD720p_GT/shields_1280x720_60.yuv", 720, 1280),
    ("HD_dataset/HD720p_GT/stockholm_1280x720_60.yuv", 720, 1280),
    ("HD_dataset/HD1080p_GT/BlueSky.yuv", 1080, 1920),
    ("HD_dataset/HD1080p_GT/Kimono1_1920x1080_24.yuv", 1080, 1920),
    ("HD_dataset/HD1080p_GT/ParkScene_1920x1080_24.yuv", 1080, 1920),
    ("HD_dataset/HD1080p_GT/sunflower_1080p25.yuv", 1080, 1920),
    ("HD_dataset/HD544p_GT/Sintel_Alley2_1280x544.yuv", 544, 1280),
    ("HD_dataset/HD544p_GT/Sintel_Market5_1280x544.yuv", 544, 1280),
    ("HD_dataset/HD544p_GT/Sintel_Temple1_1280x544.yuv", 544, 1280),
    ("HD_dataset/HD544p_GT/Sintel_Temple2_1280x544.yuv", 544, 1280),
]

Result = Dict[str, object]


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path)


def add(
    results: List[Result],
    level: str,
    benchmark: str,
    message: str,
    path: Optional[Path] = None,
    root: Optional[Path] = None,
    fix: Optional[str] = None,
) -> None:
    record: Result = {"level": level, "benchmark": benchmark, "message": message}
    if path is not None:
        record["path"] = relpath(path, root or Path.cwd())
    if fix:
        record["fix"] = fix
    results.append(record)


def resolve_under(root: Path, value: Optional[str], default: str) -> Path:
    path = Path(value).expanduser() if value else Path(default)
    if not path.is_absolute():
        path = root / path
    return path


def sample(items: Sequence[Path], max_samples: int) -> Sequence[Path]:
    if max_samples <= 0:
        return items
    return items[:max_samples]


def sample_strings(items: Sequence[str], max_samples: int) -> Sequence[str]:
    if max_samples <= 0:
        return items
    return items[:max_samples]


def check_file(
    results: List[Result],
    benchmark: str,
    root: Path,
    path: Path,
    description: str,
    fix: str,
) -> bool:
    if path.is_file():
        add(results, "OK", benchmark, f"found {description}", path, root)
        return True
    add(results, "MISSING", benchmark, f"missing {description}", path, root, fix)
    return False


def check_dir(
    results: List[Result],
    benchmark: str,
    root: Path,
    path: Path,
    description: str,
    fix: str,
) -> bool:
    if path.is_dir():
        add(results, "OK", benchmark, f"found {description}", path, root)
        return True
    add(results, "MISSING", benchmark, f"missing {description}", path, root, fix)
    return False


def check_script(results: List[Result], benchmark: str, root: Path) -> bool:
    return check_file(
        results,
        benchmark,
        root,
        root / SCRIPT_PATHS[benchmark],
        "source benchmark script",
        "Run the validator against an ECCV2022-RIFE checkout containing the benchmark/ directory.",
    )


def rife_checkpoint(args: argparse.Namespace, root: Path) -> Path:
    return resolve_under(root, args.checkpoint_dir, "train_log") / "flownet.pkl"


def rifem_checkpoint(args: argparse.Namespace, root: Path) -> Path:
    return resolve_under(root, args.rifem_checkpoint_dir, "RIFE_m_train_log") / "flownet.pkl"


def check_rife_checkpoint(results: List[Result], benchmark: str, root: Path, args: argparse.Namespace) -> bool:
    return check_file(
        results,
        benchmark,
        root,
        rife_checkpoint(args, root),
        "RIFE checkpoint file",
        "Provide the external RIFE evaluation checkpoint as train_log/flownet.pkl or pass --checkpoint-dir.",
    )


def check_rifem_checkpoint(results: List[Result], benchmark: str, root: Path, args: argparse.Namespace) -> bool:
    return check_file(
        results,
        benchmark,
        root,
        rifem_checkpoint(args, root),
        "RIFE_m checkpoint file",
        "Provide the external RIFE_m evaluation checkpoint as RIFE_m_train_log/flownet.pkl or pass --rifem-checkpoint-dir.",
    )


def check_testtime(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "testtime"
    check_script(results, benchmark, root)
    add(
        results,
        "INFO",
        benchmark,
        "no dataset or checkpoint required; this is random-tensor timing only, not PSNR/SSIM/IE verification",
    )


def check_ucf101(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "ucf101"
    check_script(results, benchmark, root)
    check_rife_checkpoint(results, benchmark, root, args)
    dataset = root / "UCF101" / "ucf101_interp_ours"
    if not check_dir(
        results,
        benchmark,
        root,
        dataset,
        "UCF101 interpolation dataset root",
        "Place UCF101/VoxelFlow interpolation cases under UCF101/ucf101_interp_ours/.",
    ):
        return
    case_dirs = sorted([p for p in dataset.iterdir() if p.is_dir()])
    if not case_dirs:
        add(results, "WARN", benchmark, "dataset root exists but contains no case directories", dataset, root)
        return
    add(results, "OK", benchmark, f"found {len(case_dirs)} case directories; checking sample", dataset, root)
    for case in sample(case_dirs, args.max_samples):
        for filename in ("frame_00.png", "frame_01_gt.png", "frame_02.png"):
            check_file(
                results,
                benchmark,
                root,
                case / filename,
                f"sample file {case.name}/{filename}",
                "Each UCF101 case must contain frame_00.png, frame_01_gt.png, and frame_02.png.",
            )


def read_nonblank_lines(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def check_vimeo90k(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "vimeo90k"
    check_script(results, benchmark, root)
    check_rife_checkpoint(results, benchmark, root, args)
    dataset = root / "vimeo_interp_test"
    if not check_dir(
        results,
        benchmark,
        root,
        dataset,
        "Vimeo90K interpolation test root",
        "Place the Vimeo90K interpolation test set under vimeo_interp_test/.",
    ):
        return
    list_file = dataset / "tri_testlist.txt"
    if not check_file(
        results,
        benchmark,
        root,
        list_file,
        "tri_testlist.txt",
        "Provide vimeo_interp_test/tri_testlist.txt from the Vimeo90K interpolation test set.",
    ):
        return
    try:
        entries = read_nonblank_lines(list_file)
    except UnicodeDecodeError as exc:
        add(results, "MISSING", benchmark, f"could not read tri_testlist.txt as UTF-8: {exc}", list_file, root)
        return
    if not entries:
        add(results, "WARN", benchmark, "tri_testlist.txt is empty", list_file, root)
        return
    add(results, "OK", benchmark, f"found {len(entries)} Vimeo90K list entries; checking sample", list_file, root)
    for entry in sample_strings(entries, args.max_samples):
        case = dataset / "target" / entry
        for filename in ("im1.png", "im2.png", "im3.png"):
            check_file(
                results,
                benchmark,
                root,
                case / filename,
                f"sample file target/{entry}/{filename}",
                "Each Vimeo90K list entry must map to target/<entry>/im1.png, im2.png, and im3.png.",
            )


def check_middlebury(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "middlebury"
    check_script(results, benchmark, root)
    check_rife_checkpoint(results, benchmark, root, args)
    data_root = root / "other-data"
    gt_root = root / "other-gt-interp"
    have_data = check_dir(
        results,
        benchmark,
        root,
        data_root,
        "MiddleBury OTHER data root",
        "Place MiddleBury OTHER input frames under other-data/<sequence>/.",
    )
    have_gt = check_dir(
        results,
        benchmark,
        root,
        gt_root,
        "MiddleBury OTHER ground-truth root",
        "Place MiddleBury OTHER ground truth under other-gt-interp/<sequence>/.",
    )
    if not (have_data and have_gt):
        return
    names = sample_strings(MIDDLEBURY_NAMES, args.max_samples)
    add(results, "OK", benchmark, f"checking {len(names)} fixed MiddleBury sequence names", data_root, root)
    for name in names:
        for path, description in (
            (data_root / name / "frame10.png", f"{name}/frame10.png"),
            (data_root / name / "frame11.png", f"{name}/frame11.png"),
            (gt_root / name / "frame10i11.png", f"{name}/frame10i11.png"),
        ):
            check_file(
                results,
                benchmark,
                root,
                path,
                f"MiddleBury file {description}",
                "MiddleBury benchmark requires frame10.png, frame11.png, and frame10i11.png for each fixed sequence.",
            )


def check_atd12k(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "atd12k"
    check_script(results, benchmark, root)
    check_rife_checkpoint(results, benchmark, root, args)
    dataset = root / "datasets" / "test_2k_540p"
    if not check_dir(
        results,
        benchmark,
        root,
        dataset,
        "ATD12K test_2k_540p root",
        "Place ATD12K test cases under datasets/test_2k_540p/.",
    ):
        return
    case_dirs = sorted([p for p in dataset.iterdir() if p.is_dir()])
    if not case_dirs:
        add(results, "WARN", benchmark, "dataset root exists but contains no case directories", dataset, root)
        return
    add(results, "OK", benchmark, f"found {len(case_dirs)} case directories; checking sample", dataset, root)
    for case in sample(case_dirs, args.max_samples):
        for filename in ("frame1.png", "frame2.png", "frame3.png"):
            check_file(
                results,
                benchmark,
                root,
                case / filename,
                f"sample file {case.name}/{filename}",
                "Each ATD12K case must contain frame1.png, frame2.png, and frame3.png.",
            )


def check_hd_files(results: List[Result], benchmark: str, root: Path, args: argparse.Namespace) -> None:
    add(
        results,
        "INFO",
        benchmark,
        "HD scripts require CUDA because they call .cuda(); they also require scikit-image/PIL for yuv_frame_io.py",
    )
    for rel, height, width in HD_FILES:
        path = root / rel
        if not check_file(
            results,
            benchmark,
            root,
            path,
            f"HD YUV file {rel}",
            "Place the HD YUV dataset files under the exact HD_dataset/*_GT/ paths expected by the source scripts.",
        ):
            continue
        if args.min_hd_frames > 0:
            frame_bytes = int(1.5 * height * width)
            required_bytes = frame_bytes * args.min_hd_frames
            actual_bytes = path.stat().st_size
            if actual_bytes < required_bytes:
                add(
                    results,
                    "WARN",
                    benchmark,
                    (
                        f"YUV file is smaller than {args.min_hd_frames} YUV420 frames "
                        f"for {height}x{width}: {actual_bytes} < {required_bytes} bytes"
                    ),
                    path,
                    root,
                    "Use the complete HD YUV dataset for official metrics, or report the run as a partial/custom smoke.",
                )
            else:
                add(
                    results,
                    "OK",
                    benchmark,
                    f"YUV file size supports at least {args.min_hd_frames} frames for {height}x{width}",
                    path,
                    root,
                )


def check_hd(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "hd"
    check_script(results, benchmark, root)
    check_rife_checkpoint(results, benchmark, root, args)
    check_hd_files(results, benchmark, root, args)


def check_hd_multi_4x(results: List[Result], root: Path, args: argparse.Namespace) -> None:
    benchmark = "hd_multi_4x"
    check_script(results, benchmark, root)
    check_rifem_checkpoint(results, benchmark, root, args)
    check_hd_files(results, benchmark, root, args)


def expand_benchmarks(values: Optional[Sequence[str]]) -> List[str]:
    if not values or "all" in values:
        return list(ALL_BENCHMARKS)
    expanded: List[str] = []
    for value in values:
        if value not in expanded:
            expanded.append(value)
    return expanded


def print_text(results: Sequence[Result], ok: bool, strict: bool) -> None:
    for record in results:
        path = f" ({record['path']})" if "path" in record else ""
        print(f"[{record['level']}] {record['benchmark']}: {record['message']}{path}")
        if record.get("fix"):
            print(f"  fix: {record['fix']}")
    missing = sum(1 for item in results if item["level"] == "MISSING")
    warnings = sum(1 for item in results if item["level"] == "WARN")
    print(f"Summary: {'OK' if ok else 'NOT READY'}; missing={missing}; warnings={warnings}; strict={strict}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check ECCV2022-RIFE benchmark script, dataset, and checkpoint layouts. "
            "This helper never downloads data and never executes benchmark scripts."
        )
    )
    parser.add_argument("--repo-root", default=".", help="ECCV2022-RIFE checkout root to inspect (default: current directory).")
    parser.add_argument(
        "--benchmark",
        action="append",
        choices=["all"] + ALL_BENCHMARKS,
        help="Benchmark layout to check. May be repeated. Default: all.",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=None,
        help="RIFE checkpoint directory for train_log-based benchmarks; must contain flownet.pkl. Default: train_log.",
    )
    parser.add_argument(
        "--rifem-checkpoint-dir",
        default=None,
        help="RIFE_m checkpoint directory for HD 4X; must contain flownet.pkl. Default: RIFE_m_train_log.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=5,
        help="Number of list/directory entries to inspect for large datasets; use 0 to inspect all entries. Default: 5.",
    )
    parser.add_argument(
        "--min-hd-frames",
        type=int,
        default=101,
        help="Minimum YUV420 frames expected for full HD source loops; use 0 to skip HD size checks. Default: 101.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat WARN results as non-ready.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


CHECKERS: Dict[str, Callable[[List[Result], Path, argparse.Namespace], None]] = {
    "testtime": check_testtime,
    "ucf101": check_ucf101,
    "vimeo90k": check_vimeo90k,
    "middlebury": check_middlebury,
    "atd12k": check_atd12k,
    "hd": check_hd,
    "hd_multi_4x": check_hd_multi_4x,
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.repo_root).expanduser().resolve()
    selected = expand_benchmarks(args.benchmark)
    results: List[Result] = []

    if not root.exists():
        add(
            results,
            "MISSING",
            "all",
            "repo root does not exist",
            root,
            root.parent,
            "Pass --repo-root pointing at an ECCV2022-RIFE checkout.",
        )
    elif not root.is_dir():
        add(results, "MISSING", "all", "repo root is not a directory", root, root.parent)
    else:
        for benchmark in selected:
            CHECKERS[benchmark](results, root, args)

    has_missing = any(item["level"] == "MISSING" for item in results)
    has_warnings = any(item["level"] == "WARN" for item in results)
    ok = not has_missing and not (args.strict and has_warnings)

    if args.json:
        payload = {
            "ok": ok,
            "repo_root": str(root),
            "selected": selected,
            "strict": args.strict,
            "results": results,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(results, ok, args.strict)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
