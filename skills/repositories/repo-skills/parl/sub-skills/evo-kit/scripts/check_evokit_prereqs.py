#!/usr/bin/env python3
"""Check local prerequisites for PARL EvoKit without building or downloading.

The checker is intentionally read-only. It verifies command presence and, when a
project root is supplied, checks for local backend library directories commonly
used by EvoKit builds and demos.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    severity: str = "required"


def command_version(command: str) -> str:
    """Return a short version string for a local command, without failing hard."""
    try:
        completed = subprocess.run(
            [command, "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=3,
        )
    except Exception as exc:  # pragma: no cover - defensive for unusual systems
        return f"version unavailable: {exc}"
    first_line = completed.stdout.strip().splitlines()[0:1]
    return first_line[0] if first_line else "version unavailable"


def check_command(command: str, label: Optional[str] = None) -> CheckResult:
    label = label or command
    path = shutil.which(command)
    if not path:
        return CheckResult(label, False, f"{command!r} not found on PATH")
    return CheckResult(label, True, f"{path} ({command_version(command)})")


def any_existing_dir(paths: Iterable[Path]) -> Optional[Path]:
    for path in paths:
        if path.is_dir():
            return path
    return None


def check_backend_dirs(project_root: Path, backend: str) -> List[CheckResult]:
    results: List[CheckResult] = []
    torch_candidates = [project_root / "libtorch", project_root / "demo" / "torch" / "libtorch"]
    paddle_candidates = [project_root / "inference_lite_lib"]

    torch_found = any_existing_dir(torch_candidates)
    paddle_found = any_existing_dir(paddle_candidates)

    if backend == "torch":
        detail = (
            f"found {torch_found}"
            if torch_found
            else "expected local libtorch/ under project root or demo/torch/libtorch/"
        )
        results.append(CheckResult("Torch backend directory", bool(torch_found), detail))
    elif backend == "paddle":
        detail = (
            f"found {paddle_found}"
            if paddle_found
            else "expected local inference_lite_lib/ under project root"
        )
        results.append(CheckResult("PaddleLite backend directory", bool(paddle_found), detail))
    else:
        if torch_found or paddle_found:
            found = []
            if torch_found:
                found.append(f"Torch={torch_found}")
            if paddle_found:
                found.append(f"PaddleLite={paddle_found}")
            results.append(CheckResult("Backend directory", True, "; ".join(found)))
        else:
            results.append(
                CheckResult(
                    "Backend directory",
                    False,
                    "expected at least one of libtorch/, demo/torch/libtorch/, or inference_lite_lib/",
                )
            )
    return results


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only prerequisite checker for PARL EvoKit C++ builds.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help=(
            "Optional EvoKit project root. When supplied, the checker looks for "
            "local libtorch or inference_lite_lib backend directories."
        ),
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "torch", "paddle"],
        default="auto",
        help="Backend directory expectation when --project-root is supplied (default: auto).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    results: List[CheckResult] = [
        check_command("cmake"),
        check_command("protoc"),
        check_command("g++", "g++ C++ compiler"),
    ]

    notes: List[str] = [
        "EvoKit uses a proto2 schema; match protoc with the protobuf C++ runtime used for linking.",
        "This checker is read-only: it does not download, build, delete, install, or run demos.",
    ]

    project_root: Optional[Path] = None
    if args.project_root is not None:
        project_root = args.project_root.expanduser().resolve()
        if not project_root.is_dir():
            results.append(CheckResult("Project root", False, f"not a directory: {project_root}"))
        else:
            results.append(CheckResult("Project root", True, str(project_root), severity="info"))
            results.extend(check_backend_dirs(project_root, args.backend))
    else:
        notes.append("Backend directory checks skipped because --project-root was not supplied.")

    missing_required = [result for result in results if result.severity == "required" and not result.ok]

    if args.json:
        payload = {
            "backend": args.backend,
            "project_root": str(project_root) if project_root is not None else None,
            "results": [asdict(result) for result in results],
            "notes": notes,
            "ok": not missing_required,
            "missing_required": [result.name for result in missing_required],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("EvoKit prerequisite check")
        print(f"Backend expectation: {args.backend}")
        if project_root is not None:
            print(f"Project root: {project_root}")
        print("")
        for result in results:
            status = "OK" if result.ok else "MISSING"
            if result.severity == "info" and result.ok:
                status = "INFO"
            print(f"{status:8} {result.name}: {result.detail}")
        print("")
        for note in notes:
            print(f"NOTE     {note}")
        print("")
        if missing_required:
            print(f"Result: missing {len(missing_required)} required item(s).")
            return 1
        print("Result: all required checked items are present.")
    return 0 if not missing_required else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
