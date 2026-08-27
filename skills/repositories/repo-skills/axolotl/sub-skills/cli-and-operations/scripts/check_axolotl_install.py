#!/usr/bin/env python3
"""Check whether Axolotl is importable and its CLI help is reachable."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def package_metadata() -> CheckResult:
    try:
        version = importlib.metadata.version("axolotl")
    except importlib.metadata.PackageNotFoundError:
        return CheckResult(
            "package_metadata",
            False,
            "No installed distribution named 'axolotl' was found for this Python.",
        )
    return CheckResult("package_metadata", True, f"Installed distribution version: {version}")


def import_namespace() -> CheckResult:
    try:
        module = importlib.import_module("axolotl")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("import_axolotl", False, f"Failed to import axolotl: {exc}")
    version = getattr(module, "__version__", "unknown")
    return CheckResult("import_axolotl", True, f"Imported axolotl namespace; __version__={version}")


def cli_on_path() -> tuple[CheckResult, str | None]:
    executable = shutil.which("axolotl")
    if not executable:
        return (
            CheckResult(
                "cli_on_path",
                False,
                "No 'axolotl' executable was found on PATH for this process.",
            ),
            None,
        )
    return CheckResult("cli_on_path", True, f"Found executable: {executable}"), executable


def cli_help(executable: str | None, timeout: float) -> CheckResult:
    if not executable:
        return CheckResult("cli_help", False, "Skipped because 'axolotl' is not on PATH.")
    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult("cli_help", False, f"Timed out after {timeout:g}s running axolotl --help.")
    except OSError as exc:
        return CheckResult("cli_help", False, f"Could not execute axolotl --help: {exc}")

    output = (completed.stdout or completed.stderr).strip().splitlines()
    first_line = output[0] if output else "no output"
    if completed.returncode == 0:
        return CheckResult("cli_help", True, f"axolotl --help succeeded: {first_line}")
    return CheckResult(
        "cli_help",
        False,
        f"axolotl --help exited {completed.returncode}: {first_line}",
    )


def module_help(timeout: float) -> CheckResult:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "axolotl.cli.main", "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            "module_help",
            False,
            f"Timed out after {timeout:g}s running python -m axolotl.cli.main --help.",
        )
    except OSError as exc:
        return CheckResult("module_help", False, f"Could not execute module help: {exc}")

    output = (completed.stdout or completed.stderr).strip().splitlines()
    first_line = output[0] if output else "no output"
    if completed.returncode == 0:
        return CheckResult("module_help", True, f"python -m axolotl.cli.main --help succeeded: {first_line}")
    return CheckResult(
        "module_help",
        False,
        f"python -m axolotl.cli.main --help exited {completed.returncode}: {first_line}",
    )


def suggestions(results: list[CheckResult]) -> list[str]:
    by_name = {result.name: result for result in results}
    advice: list[str] = []
    if not by_name["package_metadata"].ok:
        advice.append("Install Axolotl into the active Python environment before using the CLI.")
    elif not by_name["import_axolotl"].ok:
        advice.append("Repair the Python environment; package metadata exists but importing axolotl fails.")
    if by_name["import_axolotl"].ok and not by_name["cli_on_path"].ok:
        advice.append("The package imports, but the console script is missing from PATH; activate the environment or reinstall the entry point.")
    if by_name["cli_on_path"].ok and not by_name["cli_help"].ok:
        advice.append("The console script exists but cannot show help; inspect the CLI traceback for missing dependencies or version conflicts.")
    if by_name["module_help"].ok and not by_name["cli_help"].ok:
        advice.append("Module help works while the console script fails; PATH may point to a stale executable.")
    if not advice:
        advice.append("Basic install checks passed. This does not verify GPUs, model files, datasets, optional kernels, vLLM, or training runtime health.")
    return advice


def print_text(results: list[CheckResult], advice: list[str]) -> None:
    for result in results:
        status = "ok" if result.ok else "fail"
        print(f"[{status}] {result.name}: {result.detail}")
    print("suggestions:")
    for item in advice:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Axolotl package metadata, namespace import, PATH entry point, and CLI help without running training."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--timeout", type=float, default=15.0, help="Timeout in seconds for help commands")
    args = parser.parse_args()

    metadata_result = package_metadata()
    import_result = import_namespace()
    path_result, executable = cli_on_path()
    help_result = cli_help(executable, args.timeout)
    module_result = module_help(args.timeout)
    results = [metadata_result, import_result, path_result, help_result, module_result]
    advice = suggestions(results)

    if args.json:
        payload: dict[str, Any] = {
            "ok": all(result.ok for result in results),
            "checks": [asdict(result) for result in results],
            "suggestions": advice,
            "python": sys.executable,
        }
        print(json.dumps(payload, indent=2))
    else:
        print_text(results, advice)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
