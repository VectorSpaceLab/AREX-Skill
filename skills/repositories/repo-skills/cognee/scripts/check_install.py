#!/usr/bin/env python3
"""Safe Cognee install checker.

This script verifies the public package import, selected API signatures, SearchType
availability, and the `cognee-cli` help/version surface when the entry point is
on PATH. It does not call LLMs, databases, MCP, Docker, or long-running services.
"""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field


@dataclass
class CheckResult:
    package_importable: bool = False
    version: str | None = None
    api_signatures: dict[str, str] = field(default_factory=dict)
    search_type_count: int | None = None
    cli_available: bool = False
    cli_version_ok: bool = False
    cli_help_ok: bool = False
    errors: list[str] = field(default_factory=list)


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)


def build_result() -> CheckResult:
    result = CheckResult()
    try:
        import cognee
        from cognee import SearchType

        result.package_importable = True
        result.version = getattr(cognee, "__version__", None)
        for name in ["remember", "recall", "add", "cognify", "search", "improve", "forget"]:
            result.api_signatures[name] = str(inspect.signature(getattr(cognee, name)))
        result.search_type_count = len(list(SearchType))
    except Exception as exc:  # pragma: no cover - diagnostic path
        result.errors.append(f"package import/signature check failed: {exc}")

    cli = shutil.which("cognee-cli")
    result.cli_available = cli is not None
    if cli:
        version = run([cli, "--version"])
        result.cli_version_ok = version.returncode == 0 and "cognee" in (version.stdout or "").lower()
        help_result = run([cli, "--help"])
        result.cli_help_ok = help_result.returncode == 0 and "Available commands" in (help_result.stdout or "")
        if not result.cli_version_ok:
            result.errors.append("cognee-cli --version failed or did not mention cognee")
        if not result.cli_help_ok:
            result.errors.append("cognee-cli --help failed or did not show command catalog")
    else:
        result.errors.append("cognee-cli entry point is not on PATH")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Cognee package and CLI surfaces safely.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()

    result = build_result()
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(f"package_importable={result.package_importable}")
        print(f"version={result.version}")
        print(f"search_type_count={result.search_type_count}")
        print(f"cli_available={result.cli_available}")
        print(f"cli_version_ok={result.cli_version_ok}")
        print(f"cli_help_ok={result.cli_help_ok}")
        if result.errors:
            print("errors:")
            for error in result.errors:
                print(f"- {error}")
    return 0 if result.package_importable and not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
