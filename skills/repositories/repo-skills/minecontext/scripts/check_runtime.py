#!/usr/bin/env python3
"""Safe MineContext/OpenContext runtime import and CLI smoke check.

This helper never starts the server, opens a browser, captures the screen, or
calls a model endpoint. It verifies package metadata, important imports, and
CLI help using the Python interpreter that runs the script.

Examples:
  python check_runtime.py
  python check_runtime.py --repo-root /path/to/MineContext --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, List


IMPORTANT_IMPORTS = [
    "opencontext",
    "opencontext.cli",
    "opencontext.server.opencontext",
    "opencontext.config.global_config",
    "opencontext.context_capture.folder_monitor",
    "opencontext.context_capture.screenshot",
    "opencontext.context_capture.web_link_capture",
    "opencontext.context_processing.processor.document_processor",
    "opencontext.context_processing.processor.screenshot_processor",
    "opencontext.storage.unified_storage",
    "opencontext.storage.backends.chromadb_backend",
    "opencontext.storage.backends.qdrant_backend",
    "opencontext.storage.backends.sqlite_backend",
    "opencontext.context_consumption.context_agent.agent",
    "opencontext.context_consumption.generation.smart_todo_manager",
    "opencontext.context_consumption.completion.completion_service",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MineContext/OpenContext runtime imports.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional MineContext checkout root to prepend to sys.path before imports.",
    )
    parser.add_argument("--skip-cli", action="store_true", help="Skip CLI help subprocess checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> None:
    if not repo_root:
        return
    repo_root = repo_root.expanduser().resolve()
    if not (repo_root / "opencontext").is_dir():
        raise SystemExit(f"--repo-root does not contain opencontext/: {repo_root}")
    sys.path.insert(0, str(repo_root))


def run_command(cmd: List[str], timeout: int = 20) -> Dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout_head": proc.stdout.splitlines()[:8],
            "stderr_head": proc.stderr.splitlines()[:8],
        }
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return {"command": cmd, "exit_code": None, "error": str(exc)}


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)

    report: Dict[str, Any] = {
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "metadata": {},
        "imports": {},
        "cli": [],
        "errors": [],
    }

    try:
        report["metadata"]["MineContext"] = version("MineContext")
    except PackageNotFoundError:
        report["metadata"]["MineContext"] = None
        report["errors"].append("Distribution metadata for MineContext was not found")

    for name in IMPORTANT_IMPORTS:
        try:
            module = importlib.import_module(name)
            report["imports"][name] = {"ok": True, "module": getattr(module, "__name__", name)}
        except Exception as exc:
            report["imports"][name] = {"ok": False, "error": repr(exc)}
            report["errors"].append(f"Import failed: {name}: {exc}")

    if not args.skip_cli:
        report["cli"].append(run_command([sys.executable, "-m", "opencontext.cli", "--help"]))
        entry = shutil.which("opencontext")
        if entry:
            report["cli"].append(run_command([entry, "--help"]))
        else:
            report["errors"].append("opencontext entry point was not found on PATH")

    cli_failures = [c for c in report["cli"] if c.get("exit_code") not in (0, None)]
    if cli_failures:
        report["errors"].append("One or more CLI help checks returned non-zero exit status")

    ok = not report["errors"]
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Python: {report['python']} ({report['python_version']})")
        print(f"MineContext distribution version: {report['metadata'].get('MineContext')}")
        for name, result in report["imports"].items():
            status = "OK" if result["ok"] else "FAIL"
            print(f"{status:4} import {name}")
            if not result["ok"]:
                print(f"     {result['error']}")
        for result in report["cli"]:
            cmd = " ".join(result["command"])
            print(f"CLI  {cmd}: exit={result.get('exit_code')}")
            for line in result.get("stdout_head", [])[:3]:
                print(f"     {line}")
            for line in result.get("stderr_head", [])[:3]:
                print(f"     stderr: {line}")
        if report["errors"]:
            print("Errors:")
            for err in report["errors"]:
                print(f"- {err}")
        print("PASS" if ok else "FAIL")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
