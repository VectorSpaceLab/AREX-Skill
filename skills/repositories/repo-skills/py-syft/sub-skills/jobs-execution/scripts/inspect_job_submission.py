#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

VALID = {"code", "run.sh", "config.yaml"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local PySyft job submission shape without executing it")
    parser.add_argument("submission_dir")
    parser.add_argument("--entrypoint")
    args = parser.parse_args()
    root = Path(args.submission_dir)
    ok = True
    if not root.is_dir():
        print("FAIL submission_dir is not a directory")
        return 1
    names = {p.name for p in root.iterdir() if p.name != "syft.pub.yaml"}
    if names != VALID:
        print(f"FAIL expected {sorted(VALID)}, got {sorted(names)}")
        ok = False
    code_dir = root / "code"
    if not code_dir.is_dir():
        print("FAIL code/ missing")
        ok = False
    if not (root / "run.sh").is_file():
        print("FAIL run.sh missing")
        ok = False
    if not (root / "config.yaml").is_file():
        print("FAIL config.yaml missing")
        ok = False
    py_files = list(code_dir.glob("*.py")) if code_dir.is_dir() else []
    entrypoint = args.entrypoint or ("main.py" if (code_dir / "main.py").exists() else (py_files[0].name if len(py_files) == 1 else None))
    if not entrypoint:
        print("FAIL ambiguous entrypoint; specify --entrypoint")
        ok = False
    elif not (code_dir / entrypoint).is_file():
        print(f"FAIL entrypoint {entrypoint} missing")
        ok = False
    if ok:
        print("OK submission shape")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
