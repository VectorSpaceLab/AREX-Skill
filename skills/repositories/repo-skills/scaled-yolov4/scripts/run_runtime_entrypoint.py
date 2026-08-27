#!/usr/bin/env python3
"""Run a concrete entrypoint from the bundled ScaledYOLOv4 runtime mirror.

Examples:
    python scripts/run_runtime_entrypoint.py --dry-run detect -- --weights weights.pt --source images/
    python scripts/run_runtime_entrypoint.py test -- --weights weights.pt --data data/custom.yaml
    python scripts/run_runtime_entrypoint.py export -- --weights weights.pt --img-size 640 640

The helper sets the working directory and ``PYTHONPATH`` to the skill-owned
``runtime/`` mirror so the command does not require the original source
checkout. Use ``--dry-run`` to print the command without executing it.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ENTRYPOINTS = {
    "detect": ["detect.py"],
    "test": ["test.py"],
    "train": ["train.py"],
    "export": ["-m", "models.export"],
    "yolo": ["-m", "models.yolo"],
}

REQUIRED_FILES = {
    "detect": ["detect.py", "models/yolo.py", "models/common.py", "utils/datasets.py"],
    "test": ["test.py", "models/yolo.py", "models/common.py", "utils/datasets.py", "utils/general.py"],
    "train": ["train.py", "test.py", "models/yolo.py", "models/common.py", "utils/datasets.py", "data/hyp.scratch.yaml", "data/hyp.finetune.yaml"],
    "export": ["models/export.py", "models/yolo.py", "models/common.py"],
    "yolo": ["models/yolo.py", "models/common.py", "models/yolov4-p5.yaml"],
}


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "detect.py").is_file() and (candidate / "models" / "yolo.py").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing detect.py and models/yolo.py")


def validate_runtime(runtime_root: Path, entrypoint: str) -> None:
    missing = [rel for rel in REQUIRED_FILES[entrypoint] if not (runtime_root / rel).is_file()]
    if missing:
        raise FileNotFoundError("runtime mirror is incomplete; missing: " + ", ".join(missing))


def build_env(runtime_root: Path, disable_tensorflow: bool) -> tuple[dict[str, str], tempfile.TemporaryDirectory[str] | None]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    old_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(runtime_root) + (os.pathsep + old_pythonpath if old_pythonpath else "")
    tempdir: tempfile.TemporaryDirectory[str] | None = None
    if disable_tensorflow:
        tempdir = tempfile.TemporaryDirectory(prefix="scaled-yolov4-no-tensorflow-")
        tensorflow_dir = Path(tempdir.name) / "tensorflow"
        tensorflow_dir.mkdir()
        (tensorflow_dir / "__init__.py").write_text(
            "raise ImportError('TensorFlow disabled for ScaledYOLOv4 runtime entrypoint')\n",
            encoding="utf-8",
        )
        env["PYTHONPATH"] = str(Path(tempdir.name)) + os.pathsep + env["PYTHONPATH"]
    return env, tempdir


def shell_command(runtime_root: Path, python: str, entrypoint: str, entrypoint_args: list[str]) -> str:
    cmd = [python, *ENTRYPOINTS[entrypoint], *entrypoint_args]
    return "cd " + shlex.quote(str(runtime_root)) + " && " + " ".join(shlex.quote(part) for part in cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, default=None, help="override the bundled runtime root")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use for the runtime command")
    parser.add_argument("--dry-run", action="store_true", help="print the command without running it")
    parser.add_argument("--no-tensorflow-stub", action="store_true", help="do not shadow TensorFlow for train.py imports")
    parser.add_argument("entrypoint", choices=sorted(ENTRYPOINTS), help="runtime entrypoint to execute")
    parser.add_argument("entrypoint_args", nargs=argparse.REMAINDER, help="arguments passed to the selected entrypoint; use -- before entrypoint flags")
    args = parser.parse_args()

    runtime_root = (args.runtime_root or default_runtime_root()).expanduser().resolve()
    try:
        validate_runtime(runtime_root, args.entrypoint)
    except FileNotFoundError as exc:
        parser.error(str(exc))

    entrypoint_args = list(args.entrypoint_args)
    if entrypoint_args and entrypoint_args[0] == "--":
        entrypoint_args = entrypoint_args[1:]

    command_preview = shell_command(runtime_root, args.python, args.entrypoint, entrypoint_args)
    if args.dry_run:
        print(command_preview)
        return 0

    disable_tensorflow = args.entrypoint == "train" and not args.no_tensorflow_stub
    env, tempdir = build_env(runtime_root, disable_tensorflow)
    try:
        print(command_preview)
        result = subprocess.run(
            [args.python, *ENTRYPOINTS[args.entrypoint], *entrypoint_args],
            cwd=runtime_root,
            env=env,
            check=False,
        )
        return int(result.returncode)
    finally:
        if tempdir is not None:
            tempdir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
