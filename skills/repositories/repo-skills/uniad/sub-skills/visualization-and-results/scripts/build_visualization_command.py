#!/usr/bin/env python3
"""Build a shell command for the UniAD visualization launcher.

This script does not run the renderer. It prints a copy-pasteable shell command
that invokes the bundled visualization runner from a UniAD checkout.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def detect_repo_root(start: Path | None = None) -> Path:
    """Find the UniAD repository root by walking upward from a path."""
    current = (start or Path(__file__).resolve()).resolve()
    for candidate in [current, *current.parents]:
        run_py = candidate / "tools" / "analysis_tools" / "visualize" / "run.py"
        if run_py.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not detect the UniAD repository root. Use --repo-root to set it explicitly."
    )


def build_shell_command(
    repo_root: Path,
    predroot: str,
    out_folder: str,
    demo_video: str,
    project_to_cam: bool,
    python_bin: str,
) -> str:
    """Create a shell command string for the visualization runner."""
    repo_root = repo_root.resolve()
    runner = [
        python_bin,
        "./tools/analysis_tools/visualize/run.py",
        "--predroot",
        predroot,
        "--out_folder",
        out_folder,
        "--demo_video",
        demo_video,
        "--project_to_cam",
        "True" if project_to_cam else "False",
    ]
    return " && ".join(
        [
            f"cd {shlex.quote(str(repo_root))}",
            'export PYTHONPATH="$(pwd):${PYTHONPATH:-}"',
            shlex.join(runner),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a UniAD visualization command from a results pickle."
    )
    parser.add_argument(
        "--predroot",
        required=True,
        help="Path to the UniAD results pickle that contains bbox_results.",
    )
    parser.add_argument(
        "--out-folder",
        required=True,
        help="Directory that will receive the rendered JPG frames and video.",
    )
    parser.add_argument(
        "--demo-video",
        default="mini_val_final.avi",
        help="Output video filename written by the visualizer.",
    )
    parser.add_argument(
        "--repo-root",
        help="Explicit UniAD repository root. If omitted, the script auto-detects it.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable or "python",
        help="Python executable to place in the rendered command.",
    )
    cam_group = parser.add_mutually_exclusive_group()
    cam_group.add_argument(
        "--project-to-cam",
        dest="project_to_cam",
        action="store_true",
        help="Include camera projection in the rendered output.",
    )
    cam_group.add_argument(
        "--no-project-to-cam",
        dest="project_to_cam",
        action="store_false",
        help="Request a BEV-only command.",
    )
    parser.set_defaults(project_to_cam=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else detect_repo_root()
    command = build_shell_command(
        repo_root=repo_root,
        predroot=args.predroot,
        out_folder=args.out_folder,
        demo_video=args.demo_video,
        project_to_cam=args.project_to_cam,
        python_bin=args.python,
    )
    if not args.project_to_cam:
        print(
            "NOTE: the stock visualization runner checks --project_to_cam as a raw truthy value; "
            "False is only informative unless the runner is wrapped or patched.",
            file=sys.stderr,
        )
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
