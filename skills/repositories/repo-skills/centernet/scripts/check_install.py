#!/usr/bin/env python3
"""Check that a CenterNet checkout has its runtime imports, CUDA, and CLI help working.

Usage:
  python scripts/check_install.py --repo-root /path/to/CenterNet

This helper is safe to run from any working directory after the repo's compiled
extensions have been built in place or installed. It never trains, downloads, or
mutates the repository; it only imports modules, probes CUDA, and runs the
`--help` paths for `train.py` and `test.py`.
"""

from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_IMPORTS = [
    "torch",
    "numpy",
    "cv2",
    "matplotlib",
    "tqdm",
    "pycocotools._mask",
    "external.nms",
    "models.py_utils._cpools",
]
EXPECTED_CONFIGS = [
    "config/CenterNet-52.json",
    "config/CenterNet-104.json",
    "config/CenterNet-52-multi_scale.json",
    "config/CenterNet-104-multi_scale.json",
]
EXPECTED_CLIS = ["train.py", "test.py"]


def add_sys_paths(repo_root: Path) -> None:
    path = str(repo_root)
    if path not in sys.path:
        sys.path.insert(0, path)


def short_tail(text: str, limit: int = 12) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


def run_help(repo_root: Path, script_name: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, script_name, "--help"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def import_module(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", None)
        if version is not None:
            return True, f"{name} ({version})"
        return True, name
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return False, f"{name}: {type(exc).__name__}: {exc}"


def import_coco_mask(repo_root: Path) -> tuple[bool, str]:
    ok, message = import_module("pycocotools._mask")
    if ok:
        return ok, message

    coco_path = repo_root / "data" / "coco" / "PythonAPI"
    path = str(coco_path)
    if path not in sys.path:
        sys.path.insert(0, path)
    return import_module("pycocotools._mask")


def check_cuda() -> tuple[bool, str]:
    try:
        import torch

        if not torch.cuda.is_available():
            return False, "torch.cuda.is_available() == False"

        count = torch.cuda.device_count()
        name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        tiny = torch.empty((1,), device="cuda")
        return True, f"devices={count}, name={name}, capability={capability}, tensor={tuple(tiny.shape)}"
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return False, f"{type(exc).__name__}: {exc}"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a CenterNet checkout")
    parser.add_argument("--repo-root", default=".", help="Path to the CenterNet checkout")
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(args.repo_root).resolve()
    add_sys_paths(repo_root)

    print(f"repo_root: {repo_root}")
    print(f"python: {sys.executable}")

    failures: list[str] = []

    print("\n== imports ==")
    for name in REQUIRED_IMPORTS:
        if name == "pycocotools._mask":
            ok, message = import_coco_mask(repo_root)
        else:
            ok, message = import_module(name)
        print(f"{'OK' if ok else 'FAIL'} {message}")
        if not ok:
            failures.append(message)

    print("\n== configs ==")
    for rel in EXPECTED_CONFIGS:
        path = repo_root / rel
        ok = path.exists()
        print(f"{'OK' if ok else 'FAIL'} {rel}")
        if not ok:
            failures.append(f"missing config: {rel}")

    print("\n== cuda ==")
    ok, message = check_cuda()
    print(f"{'OK' if ok else 'FAIL'} {message}")
    if not ok:
        failures.append(message)

    print("\n== cli help ==")
    for script_name in EXPECTED_CLIS:
        code, stdout, stderr = run_help(repo_root, script_name)
        if code == 0:
            print(f"OK {script_name} --help")
            print(short_tail(stdout, 8))
        else:
            print(f"FAIL {script_name} --help (exit {code})")
            tail = short_tail(stderr or stdout, 8)
            if tail:
                print(tail)
            failures.append(f"{script_name} --help failed")

    print("\n== summary ==")
    if failures:
        for item in failures:
            print(f"- {item}")
        return 1

    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
