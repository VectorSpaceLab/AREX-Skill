#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR = SCRIPT_DIR / "validate_pair_file.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a bounded SuperGlue pair-matching smoke test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the source repository root that contains match_pairs.py",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for smoke outputs; relative paths are resolved under --repo-root",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device policy for the smoke run",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=1,
        help="Maximum number of pairs to process in the smoke run",
    )
    parser.add_argument(
        "--resize",
        nargs="+",
        type=int,
        default=[320, 240],
        help="Resize passed through to match_pairs.py; use one or two integers",
    )
    parser.add_argument(
        "--input-pairs",
        type=Path,
        default=None,
        help="Optional pair manifest; relative paths are resolved under --repo-root",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Optional image directory; relative paths are resolved under --repo-root",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run pose evaluation in addition to matching",
    )
    parser.add_argument(
        "--viz",
        action="store_true",
        help="Save visualization images",
    )
    parser.add_argument(
        "--fast-viz",
        action="store_true",
        help="Use the OpenCV renderer for visualization",
    )
    parser.add_argument(
        "--opencv-display",
        action="store_true",
        help="Preview visualizations in an OpenCV window",
    )
    parser.add_argument(
        "--viz-extension",
        choices=("png", "pdf"),
        default="png",
        help="Visualization output extension",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Reuse existing match/evaluation outputs when present",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Deterministically shuffle the pair order before running",
    )
    parser.add_argument(
        "--show-keypoints",
        action="store_true",
        help="Include keypoints in visualization outputs",
    )
    parser.add_argument(
        "--resize-float",
        action="store_true",
        help="Pass --resize_float through to match_pairs.py",
    )
    parser.add_argument(
        "--superglue",
        choices=("indoor", "outdoor"),
        default="indoor",
        help="Select the indoor or outdoor pretrained weights",
    )
    parser.add_argument(
        "--max-keypoints",
        type=int,
        default=1024,
        help="SuperPoint keypoint cap",
    )
    parser.add_argument(
        "--keypoint-threshold",
        type=float,
        default=0.005,
        help="SuperPoint keypoint threshold",
    )
    parser.add_argument(
        "--nms-radius",
        type=int,
        default=4,
        help="SuperPoint NMS radius",
    )
    parser.add_argument(
        "--sinkhorn-iterations",
        type=int,
        default=20,
        help="SuperGlue Sinkhorn iterations",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.2,
        help="SuperGlue match threshold",
    )
    return parser.parse_args()


def resolve_under_repo_root(path: Path | None, repo_root: Path, default_relative: str | None = None) -> Path:
    if path is None:
        if default_relative is None:
            raise ValueError("default_relative must be provided when path is None")
        return (repo_root / default_relative).resolve()
    path = path.expanduser()
    return path if path.is_absolute() else (repo_root / path).resolve()


def torch_cuda_available() -> bool:
    try:
        import torch  # type: ignore
    except Exception:
        return False
    return bool(torch.cuda.is_available())


def validate_wrapper_args(args: argparse.Namespace) -> None:
    repo_root = args.repo_root.expanduser()
    if not repo_root.exists() or not repo_root.is_dir():
        raise SystemExit(f"Repository root does not exist or is not a directory: {repo_root}")
    match_pairs_script = repo_root / "match_pairs.py"
    if not match_pairs_script.is_file():
        raise SystemExit(f"match_pairs.py not found under repository root: {match_pairs_script}")
    if not VALIDATOR.is_file():
        raise SystemExit(f"Pair-file validator not found: {VALIDATOR}")
    if args.max_length < 1:
        raise SystemExit("--max-length must be at least 1 for the bounded smoke wrapper")
    if len(args.resize) not in (1, 2):
        raise SystemExit("--resize must contain one or two integers")
    if args.fast_viz and not args.viz:
        raise SystemExit("--fast-viz requires --viz")
    if args.opencv_display and not args.viz:
        raise SystemExit("--opencv-display requires --viz")
    if args.opencv_display and not args.fast_viz:
        raise SystemExit("--opencv-display requires --fast-viz")
    if args.fast_viz and args.viz_extension == "pdf":
        raise SystemExit("--fast-viz cannot be combined with --viz-extension pdf")
    if args.device == "cuda" and not torch_cuda_available():
        raise SystemExit("--device cuda was requested, but CUDA is not available in this interpreter")


def build_match_pairs_command(args: argparse.Namespace, repo_root: Path, output_dir: Path, input_pairs: Path, input_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(repo_root / "match_pairs.py"),
        "--input_pairs",
        str(input_pairs),
        "--input_dir",
        str(input_dir),
        "--output_dir",
        str(output_dir),
        "--max_length",
        str(args.max_length),
        "--resize",
    ]
    command.extend(str(value) for value in args.resize)
    if args.resize_float:
        command.append("--resize_float")
    command.extend([
        "--superglue",
        args.superglue,
        "--max_keypoints",
        str(args.max_keypoints),
        "--keypoint_threshold",
        str(args.keypoint_threshold),
        "--nms_radius",
        str(args.nms_radius),
        "--sinkhorn_iterations",
        str(args.sinkhorn_iterations),
        "--match_threshold",
        str(args.match_threshold),
    ])
    if args.eval:
        command.append("--eval")
    if args.viz:
        command.append("--viz")
    if args.fast_viz:
        command.append("--fast_viz")
    if args.cache:
        command.append("--cache")
    if args.show_keypoints:
        command.append("--show_keypoints")
    if args.viz_extension:
        command.extend(["--viz_extension", args.viz_extension])
    if args.opencv_display:
        command.append("--opencv_display")
    if args.shuffle:
        command.append("--shuffle")
    if args.device == "cpu":
        command.append("--force_cpu")
    return command


def main() -> int:
    args = parse_args()
    args.repo_root = args.repo_root.expanduser()
    validate_wrapper_args(args)

    repo_root = args.repo_root.resolve()
    input_pairs = resolve_under_repo_root(
        args.input_pairs,
        repo_root,
        "assets/scannet_sample_pairs_with_gt.txt",
    )
    input_dir = resolve_under_repo_root(
        args.input_dir,
        repo_root,
        "assets/scannet_sample_images",
    )
    output_dir = resolve_under_repo_root(args.output_dir, repo_root)

    if not input_pairs.is_file():
        raise SystemExit(f"Pair file does not exist: {input_pairs}")
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    validator_args = [
        sys.executable,
        str(VALIDATOR),
        "--pair-file",
        str(input_pairs),
        "--input-dir",
        str(input_dir),
    ]
    if args.eval:
        validator_args.append("--require-gt")
    subprocess.run(validator_args, check=True)

    command = build_match_pairs_command(args, repo_root, output_dir, input_pairs, input_dir)
    print("Running:", flush=True)
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=str(repo_root), check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
