# Copyright 2025 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Lightweight LLaMA Factory installation and Web UI sanity checks."""

from __future__ import annotations

import importlib
import importlib.metadata
import shutil
import sys
from dataclasses import dataclass


MIN_PYTHON = (3, 11)
CORE_PACKAGES = ("torch", "transformers", "datasets", "accelerate", "peft", "trl")
WEB_PACKAGES = ("gradio", "matplotlib")
API_PACKAGES = ("fastapi", "uvicorn", "sse_starlette")
CLI_NAMES = ("llamafactory-cli", "lmf")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def package_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure
        return CheckResult(module_name, False, f"import failed: {exc.__class__.__name__}: {exc}")

    version = getattr(module, "__version__", None) or package_version(module_name.replace("_", "-")) or "version unknown"
    return CheckResult(module_name, True, str(version))


def print_result(result: CheckResult) -> None:
    status = "OK" if result.ok else "MISSING"
    print(f"[{status}] {result.name}: {result.detail}")


def main() -> int:
    failures: list[str] = []
    print("LLaMA Factory sanity check")
    print(f"Python: {sys.version.split()[0]}")

    if sys.version_info < MIN_PYTHON:
        failures.append("Python 3.11 or newer is required by LLaMA Factory metadata.")
        print("[MISSING] python-version: expected >=3.11")
    else:
        print("[OK] python-version: >=3.11")

    metadata_version = package_version("llamafactory")
    if metadata_version is None:
        failures.append("Package metadata for 'llamafactory' was not found. Install with 'pip install -e .' or an appropriate package build.")
        print("[MISSING] package-metadata: llamafactory distribution not found")
    else:
        print(f"[OK] package-metadata: llamafactory {metadata_version}")

    package_result = import_status("llamafactory")
    print_result(package_result)
    if not package_result.ok:
        failures.append("Cannot import 'llamafactory'. Check that the active environment is the one where LLaMA Factory is installed.")

    for cli_name in CLI_NAMES:
        path = shutil.which(cli_name)
        if path:
            print(f"[OK] cli: {cli_name} available")
        else:
            failures.append(f"CLI '{cli_name}' is not on PATH. Reinstall the package or activate the environment that owns the entry point.")
            print(f"[MISSING] cli: {cli_name} not found on PATH")

    print("\nCore dependency imports:")
    for module_name in CORE_PACKAGES:
        result = import_status(module_name)
        print_result(result)
        if not result.ok:
            failures.append(f"Install or repair core dependency '{module_name}'.")

    print("\nWeb UI dependency imports:")
    for module_name in WEB_PACKAGES:
        result = import_status(module_name)
        print_result(result)
        if not result.ok:
            failures.append(f"Install GUI dependency '{module_name}' before using 'llamafactory-cli webui' or 'webchat'.")

    print("\nAPI dependency imports:")
    for module_name in API_PACKAGES:
        result = import_status(module_name)
        print_result(result)
        if not result.ok:
            failures.append(f"Install API dependency '{module_name}' before using 'llamafactory-cli api'.")

    print("\nSuggested next commands when checks pass:")
    print("  llamafactory-cli help")
    print("  llamafactory-cli version")
    print("  llamafactory-cli env")
    print("  GRADIO_SERVER_NAME=0.0.0.0 llamafactory-cli webui")

    if failures:
        print("\nActionable issues:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nAll lightweight checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
