#!/usr/bin/env python3
"""Check the bundled ScaledYOLOv4 public CLI parsers.

By default this helper runs against the skill-owned ``runtime/`` mirror that is
packaged beside this script. Use ``--runtime-root`` only when intentionally
checking a different ScaledYOLOv4 source tree.

The training entry point imports ``torch.utils.tensorboard`` at module import
time. Some mixed TensorFlow/TensorBoard installations can crash during a
help-only check, so this diagnostic shadows TensorFlow with an ImportError-only
stub for that one subprocess. It does not alter the runtime mirror or the
user's environment.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def default_runtime_root() -> Path:
    """Locate the packaged runtime mirror from inside the generated skill tree."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "detect.py").is_file() and (candidate / "models" / "yolo.py").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing detect.py and models/yolo.py")


def _first_nonempty(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "(no output)"


def _run(label: str, command: list[str], runtime_root: Path, env: dict[str, str]) -> bool:
    result = subprocess.run(
        command,
        cwd=runtime_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        print(f"OK   {label}: {_first_nonempty(result.stdout)}")
        return True

    print(f"FAIL {label}: exit {result.returncode}")
    detail = result.stderr.strip() or result.stdout.strip()
    if detail:
        print("     " + "\n     ".join(detail.splitlines()[-8:]))
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="optional ScaledYOLOv4 source root; defaults to this skill's bundled runtime/ mirror",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="deprecated alias for --runtime-root, kept for compatibility with older checks",
    )
    args = parser.parse_args()

    runtime_root = (args.runtime_root or args.repo_root or default_runtime_root()).expanduser().resolve()
    required = [
        runtime_root / "detect.py",
        runtime_root / "test.py",
        runtime_root / "train.py",
        runtime_root / "models" / "export.py",
        runtime_root / "models" / "yolo.py",
        runtime_root / "models" / "yolov4-p5.yaml",
        runtime_root / "data" / "coco.yaml",
    ]
    missing = [str(path.relative_to(runtime_root)) for path in required if not path.is_file()]
    if missing:
        parser.error("runtime root is incomplete; missing: " + ", ".join(missing))

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    old_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(runtime_root) + (os.pathsep + old_pythonpath if old_pythonpath else "")
    results: list[bool] = []
    python = sys.executable

    results.append(_run("detect.py", [python, "detect.py", "--help"], runtime_root, env))
    results.append(_run("test.py", [python, "test.py", "--help"], runtime_root, env))

    with tempfile.TemporaryDirectory(prefix="scaled-yolov4-no-tensorflow-") as stub:
        tensorflow_dir = Path(stub) / "tensorflow"
        tensorflow_dir.mkdir()
        (tensorflow_dir / "__init__.py").write_text(
            "raise ImportError('TensorFlow disabled for CLI inspection')\n",
            encoding="utf-8",
        )
        train_env = env.copy()
        train_env["PYTHONPATH"] = str(Path(stub)) + os.pathsep + train_env["PYTHONPATH"]
        results.append(_run("train.py", [python, "train.py", "--help"], runtime_root, train_env))

    results.append(_run("models.export", [python, "-m", "models.export", "--help"], runtime_root, env))
    results.append(_run("models.yolo", [python, "-m", "models.yolo", "--help"], runtime_root, env))

    print(f"runtime_root={runtime_root}")
    print(f"CLI checks: {sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
