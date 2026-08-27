#!/usr/bin/env python3
"""Build and smoke-test a tracker toolkit region extension in a temp copy.

Usage requires an explicit source implementation root containing ``setup.py``:
``python build_region_extension.py --repo-root /path/to/implementation``.
The source tree is copied to a temporary directory and is never modified unless
``--in-place`` is explicitly supplied. No downloads or credentials are used.
Dangling dataset/result symlinks and large runtime artifacts are excluded from a
temporary copy because the region extension build does not need them.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Safely build a Cython region extension in an isolated copy.")
    p.add_argument("--repo-root", type=Path, required=True, help="implementation root containing setup.py")
    p.add_argument("--in-place", action="store_true", help="build in the explicit source root instead of a temporary copy")
    p.add_argument("--keep-copy", action="store_true", help="keep the temporary build copy and print its path")
    p.add_argument("--json", action="store_true", help="emit JSON")
    return p


def run(args: argparse.Namespace) -> int:
    source = args.repo_root.expanduser().resolve()
    result: dict[str, object] = {"source_root": str(source), "in_place": args.in_place, "status": "error"}
    if not source.is_dir():
        result["error"] = f"repo root is not a directory: {source}"
        return emit(result, args)
    setup = source / "setup.py"
    if not setup.is_file():
        result["error"] = f"setup.py not found below explicit repo root: {source}"
        return emit(result, args)

    temporary_root: Path | None = None
    build_root = source
    try:
        if not args.in_place:
            temporary_root = Path(tempfile.mkdtemp(prefix="siam-trackers-region-"))
            build_root = temporary_root / source.name
            shutil.copytree(
                source,
                build_root,
                symlinks=False,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo", "*.so", "*.zip", "*.mp4",
                    "datasets", "data", "results", ".vscode", "pretrained", "snapshot",
                ),
            )
        env = os.environ.copy()
        env.setdefault("PYTHONNOUSERSITE", "1")
        completed = subprocess.run(
            [sys.executable, "setup.py", "build_ext", "--inplace"],
            cwd=build_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        result["build_root"] = str(build_root)
        result["command"] = "python setup.py build_ext --inplace"
        result["returncode"] = completed.returncode
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
        if completed.returncode:
            result["error"] = "extension build failed; inspect stderr_tail for compiler/Cython details"
            return emit(result, args)
        candidates = sorted((build_root / "toolkit").rglob("region*.so")) if (build_root / "toolkit").exists() else []
        result["built_extensions"] = [str(p) for p in candidates]
        if not candidates:
            result["error"] = "build completed but no region*.so was found"
            return emit(result, args)
        sys.path.insert(0, str(build_root))
        importlib.import_module("toolkit.utils.region")
        result["import"] = "toolkit.utils.region passed"
        result["status"] = "ok"
        if temporary_root is not None and args.keep_copy:
            result["kept_copy"] = str(build_root)
            temporary_root = None
        return emit(result, args)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return emit(result, args)
    finally:
        if temporary_root is not None:
            shutil.rmtree(temporary_root, ignore_errors=True)


def emit(result: dict[str, object], args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result.get('status')}")
        for key, value in result.items():
            if key not in {"status"}:
                print(f"{key}: {value}")
    return 0 if result.get("status") == "ok" else 1


def main() -> int:
    return run(parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
