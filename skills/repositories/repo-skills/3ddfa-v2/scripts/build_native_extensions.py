#!/usr/bin/env python3
"""Build the repo's native extensions in the supported order."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from bootstrap_runtime import ensure_repo_root  # noqa: E402


def run_step(title: str, command: list[str], cwd: Path) -> None:
    print(f"==> {title}")
    print("    "+" ".join(command))
    subprocess.run(command, cwd=str(cwd), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path.cwd(), help="Path to the 3DDFA_V2 checkout")
    args = parser.parse_args()

    repo_root = ensure_repo_root(args.repo_root)

    run_step(
        "Build FaceBoxes NMS",
        [sys.executable, "build.py", "build_ext", "--inplace"],
        repo_root / "FaceBoxes" / "utils",
    )
    run_step(
        "Build Sim3DR",
        [sys.executable, "setup.py", "build_ext", "--inplace"],
        repo_root / "Sim3DR",
    )
    run_step(
        "Build render.so",
        ["gcc", "-shared", "-Wall", "-O3", "render.c", "-o", "render.so", "-fPIC"],
        repo_root / "utils" / "asset",
    )

    expected_patterns = [
        repo_root / "FaceBoxes" / "utils" / "nms" / "cpu_nms*.so",
        repo_root / "Sim3DR" / "Sim3DR_Cython*.so",
        repo_root / "utils" / "asset" / "render.so",
    ]
    for pattern in expected_patterns:
        matches = list(pattern.parent.glob(pattern.name))
        if not matches:
            raise FileNotFoundError(f"missing build artifact matching: {pattern}")
        for path in matches:
            print(f"verified {path.relative_to(repo_root)}")

    print("native-build-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
