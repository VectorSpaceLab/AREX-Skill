#!/usr/bin/env python3
"""Preflight or launch pytorch-yolo-v3 still-image detection through a bundled wrapper.

Default mode is dry-run: validate paths/options and print the command that would
run the repository entrypoint in a user's checkout. Add --execute only after the
user approves loading local weights and writing annotated images.

Examples:
  python scripts/run_image_detection.py --repo-root <repo-root> --images imgs --det det --weights yolov3.weights
  python scripts/run_image_detection.py --repo-root <repo-root> --images image.jpg --det detections --weights weights/yolov3.weights --execute
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import List, Sequence

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class PreflightError(RuntimeError):
    """Raised for actionable preflight failures."""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate and optionally launch pytorch-yolo-v3 detect.py without downloading weights."
    )
    p.add_argument("--repo-root", default=".", help="User checkout/source tree containing detect.py, cfg/, data/, and pallete.")
    p.add_argument("--images", required=True, help="Image file or image directory, absolute or relative to --repo-root.")
    p.add_argument("--det", required=True, help="Detection output directory, absolute or relative to --repo-root.")
    p.add_argument("--cfg", default="cfg/yolov3.cfg", help="Cfg path, absolute or relative to --repo-root.")
    p.add_argument("--weights", default="yolov3.weights", help="Local weights path, absolute or relative to --repo-root.")
    p.add_argument("--bs", type=int, default=1, help="Batch size for detect.py. Default: 1.")
    p.add_argument("--confidence", type=float, default=0.5, help="Object confidence threshold. Default: 0.5.")
    p.add_argument("--nms-thresh", type=float, default=0.4, help="NMS IoU threshold passed to --nms_thresh. Default: 0.4.")
    p.add_argument("--reso", type=int, default=416, help="Network resolution; must be >32 and divisible by 32. Default: 416.")
    p.add_argument("--scales", default="1,2,3", help="Value passed to detect.py --scales; scale filtering is disabled in the original script.")
    p.add_argument("--python", default=sys.executable, help="Python executable used when --execute is set. Default: current Python.")
    p.add_argument("--execute", action="store_true", help="Actually run detect.py after preflight. Without this flag, only print the command.")
    return p


def resolve(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def shell_join(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def validate(args: argparse.Namespace) -> tuple[Path, Path, Path, Path, Path, List[str]]:
    warnings: List[str] = []
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise PreflightError(f"--repo-root is not a directory: {repo_root}")
    detect_py = repo_root / "detect.py"
    if not detect_py.is_file():
        raise PreflightError("detect.py was not found under --repo-root")

    cfg = resolve(repo_root, args.cfg).resolve()
    weights = resolve(repo_root, args.weights).resolve()
    images = resolve(repo_root, args.images).resolve()
    det = resolve(repo_root, args.det).resolve()

    if not cfg.is_file():
        raise PreflightError(f"cfg file does not exist: {cfg}")
    if not weights.is_file():
        raise PreflightError(f"weights file does not exist: {weights}; provide a local file or run dry checks instead")
    if not images.exists():
        raise PreflightError(f"--images path does not exist: {images}")
    if images.is_dir():
        supported = [p for p in images.iterdir() if p.is_file() and p.suffix in IMAGE_EXTENSIONS]
        uppercase = [p.name for p in images.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS and p.suffix not in IMAGE_EXTENSIONS]
        if not supported:
            warnings.append("image directory contains no lowercase .jpg/.jpeg/.png files detectable by detect.py")
        if uppercase:
            warnings.append("detect.py directory mode ignores uppercase image extensions: " + ", ".join(sorted(uppercase)[:5]))
    elif images.suffix.lower() not in IMAGE_EXTENSIONS:
        warnings.append("single-file mode bypasses directory extension filtering, but OpenCV must still read the image")

    if args.bs < 1:
        raise PreflightError("--bs must be >= 1")
    if args.reso <= 32 or args.reso % 32 != 0:
        raise PreflightError("--reso must be greater than 32 and divisible by 32")
    if not (0.0 <= args.confidence < 1.0):
        raise PreflightError("--confidence must be >= 0 and < 1")
    if not (0.0 <= args.nms_thresh <= 1.0):
        raise PreflightError("--nms-thresh must be between 0 and 1")

    return repo_root, detect_py, cfg, weights, images, warnings


def rel_or_abs(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        repo_root, detect_py, cfg, weights, images, warnings = validate(args)
    except PreflightError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2

    det_path = resolve(repo_root, args.det).resolve()
    command = [
        args.python,
        str(detect_py),
        "--images",
        rel_or_abs(repo_root, images),
        "--det",
        rel_or_abs(repo_root, det_path),
        "--cfg",
        rel_or_abs(repo_root, cfg),
        "--weights",
        rel_or_abs(repo_root, weights),
        "--reso",
        str(args.reso),
        "--confidence",
        str(args.confidence),
        "--nms_thresh",
        str(args.nms_thresh),
        "--bs",
        str(args.bs),
        "--scales",
        args.scales,
    ]

    print("pytorch-yolo-v3 image detection wrapper")
    print("mode:", "execute" if args.execute else "dry-run")
    print("preflight: ok")
    for warning in warnings:
        print("WARNING:", warning)
    print("command:")
    print("  " + shell_join(command))
    print("working_directory:", repo_root)
    print("notes: no weights were downloaded; detect.py will create the output directory if execution is enabled")

    if not args.execute:
        print("dry-run complete; add --execute only after the user approves running inference and writing outputs")
        return 0

    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    completed = subprocess.run(command, cwd=str(repo_root), env=env, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
