#!/usr/bin/env python3
"""Safe installation smoke checks for smolagents.

This helper performs import, metadata, signature, and CLI-help checks without
calling model providers, remote sandboxes, browsers, or network services.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_command(command: list[str], timeout: int = 20) -> CheckResult:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return CheckResult(command[0], False, "command not found")
    except subprocess.TimeoutExpired:
        return CheckResult(" ".join(command), False, f"timed out after {timeout}s")
    output = (completed.stdout or completed.stderr).strip().splitlines()
    detail = output[0] if output else f"exit {completed.returncode}"
    return CheckResult(" ".join(command), completed.returncode == 0, detail)


def check_imports() -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        import smolagents
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return [CheckResult("import smolagents", False, f"{type(exc).__name__}: {exc}")]

    results.append(CheckResult("import smolagents", True, getattr(smolagents, "__version__", "version unknown")))
    try:
        dist = metadata.distribution("smolagents")
        results.append(CheckResult("metadata smolagents", True, dist.version))
    except Exception as exc:  # pragma: no cover - diagnostic helper
        results.append(CheckResult("metadata smolagents", False, f"{type(exc).__name__}: {exc}"))

    for name in ["CodeAgent", "ToolCallingAgent", "InferenceClientModel", "Tool"]:
        obj = getattr(smolagents, name, None)
        if obj is None:
            results.append(CheckResult(f"export {name}", False, "missing"))
            continue
        try:
            signature = inspect.signature(obj.__init__ if inspect.isclass(obj) else obj)
        except Exception as exc:
            results.append(CheckResult(f"signature {name}", False, f"{type(exc).__name__}: {exc}"))
        else:
            results.append(CheckResult(f"signature {name}", True, str(signature)))
    return results


def check_cli(check_webagent: bool) -> list[CheckResult]:
    results: list[CheckResult] = []
    smolagent = shutil.which("smolagent")
    if smolagent:
        results.append(run_command([smolagent, "--help"]))
    else:
        results.append(run_command([sys.executable, "-m", "smolagents.cli", "--help"]))

    if check_webagent:
        webagent = shutil.which("webagent")
        if webagent:
            results.append(run_command([webagent, "--help"]))
        else:
            results.append(run_command([sys.executable, "-m", "smolagents.vision_web_browser", "--help"]))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe smolagents installation smoke checks.")
    parser.add_argument("--check-webagent", action="store_true", help="Also check webagent help; requires vision/browser dependencies.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    results = check_imports() + check_cli(args.check_webagent)
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
