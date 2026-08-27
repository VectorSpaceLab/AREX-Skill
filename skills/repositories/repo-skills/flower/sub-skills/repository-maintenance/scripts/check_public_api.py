#!/usr/bin/env python3
# Copyright 2026 Flower Labs GmbH. All Rights Reserved.
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
# ==============================================================================
"""Check recursive ``__all__`` exports for Flower public API packages.

This script is intended for maintainer checks in an installed or editable
environment where ``flwr`` or ``flwr_datasets`` can already be imported.

Examples:
    python scripts/check_public_api.py flwr
    python scripts/check_public_api.py flwr_datasets --json
"""

from __future__ import annotations

import argparse
import importlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from types import ModuleType
from typing import Any


@dataclass(frozen=True)
class Finding:
    """Single public-API validation finding."""

    package: str
    module: str
    kind: str
    name: str
    message: str


@dataclass(frozen=True)
class PackageReport:
    """Summary for one checked package."""

    package: str
    modules_checked: int
    findings: list[Finding]


def _normalize_all(exports: Any) -> list[Any] | None:
    """Return ``__all__`` as a list when it is sequence-like."""

    if exports is None:
        return None
    if isinstance(exports, (list, tuple)):
        return list(exports)
    return None


def _check_module(
    module: ModuleType,
    *,
    root_package: str,
    findings: list[Finding],
    seen_modules: set[str],
    recursive: bool,
    check_sort: bool,
    is_root: bool,
) -> None:
    """Validate one module/package and optionally recurse into exported modules."""

    module_name = module.__name__
    if module_name in seen_modules:
        return
    seen_modules.add(module_name)

    exports_raw = getattr(module, "__all__", None)
    exports = _normalize_all(exports_raw)
    if exports is None:
        if is_root or hasattr(module, "__path__"):
            findings.append(
                Finding(
                    package=root_package,
                    module=module_name,
                    kind="missing_all",
                    name="__all__",
                    message="package does not define a sequence-like __all__",
                )
            )
        return

    if (
        check_sort
        and all(isinstance(name, str) for name in exports)
        and exports != sorted(exports)
    ):
        findings.append(
            Finding(
                package=root_package,
                module=module_name,
                kind="unsorted_all",
                name="__all__",
                message="__all__ is not sorted alphabetically",
            )
        )

    seen_names: set[str] = set()
    for name in exports:
        if not isinstance(name, str):
            findings.append(
                Finding(
                    package=root_package,
                    module=module_name,
                    kind="non_string_export",
                    name=repr(name),
                    message="__all__ contains a non-string entry",
                )
            )
            continue

        if name in seen_names:
            findings.append(
                Finding(
                    package=root_package,
                    module=module_name,
                    kind="duplicate_export",
                    name=name,
                    message="__all__ contains the same export more than once",
                )
            )
            continue
        seen_names.add(name)

        try:
            value = getattr(module, name)
        except Exception as exc:  # pragma: no cover - import failures are surfaced.
            findings.append(
                Finding(
                    package=root_package,
                    module=module_name,
                    kind="missing_export",
                    name=name,
                    message=f"export is not importable: {exc}",
                )
            )
            continue

        if recursive and isinstance(value, ModuleType):
            child_name = value.__name__
            if child_name == root_package or child_name.startswith(root_package + "."):
                _check_module(
                    value,
                    root_package=root_package,
                    findings=findings,
                    seen_modules=seen_modules,
                    recursive=recursive,
                    check_sort=check_sort,
                    is_root=False,
                )


def check_package(
    package_name: str,
    *,
    recursive: bool = True,
    check_sort: bool = True,
) -> PackageReport:
    """Check a package's public API exports."""

    module = importlib.import_module(package_name)
    findings: list[Finding] = []
    seen_modules: set[str] = set()
    _check_module(
        module,
        root_package=package_name,
        findings=findings,
        seen_modules=seen_modules,
        recursive=recursive,
        check_sort=check_sort,
        is_root=True,
    )
    return PackageReport(
        package=package_name,
        modules_checked=len(seen_modules),
        findings=findings,
    )


def _format_human_report(reports: Iterable[PackageReport]) -> str:
    """Format a human-readable report."""

    lines: list[str] = []
    all_findings: list[Finding] = []
    total_modules = 0
    for report in reports:
        total_modules += report.modules_checked
        all_findings.extend(report.findings)
        lines.append(
            f"{report.package}: checked {report.modules_checked} module(s), "
            f"{len(report.findings)} issue(s)"
        )
    if all_findings:
        lines.append("Problems:")
        for finding in all_findings:
            lines.append(
                f"- {finding.package}:{finding.module} "
                f"[{finding.kind}] {finding.name}: {finding.message}"
            )
    else:
        lines.append(
            f"No public API export issues found across {total_modules} module(s)."
        )
    return "\n".join(lines)


def main() -> int:
    """Run the public API validation."""

    parser = argparse.ArgumentParser(
        description="Check recursive __all__ public API exports for Flower packages."
    )
    parser.add_argument(
        "packages",
        nargs="+",
        help="Package names to check, such as flwr or flwr_datasets.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only check the top-level package instead of following exported modules.",
    )
    parser.add_argument(
        "--no-sort-check",
        action="store_true",
        help="Do not verify that __all__ entries are alphabetically sorted.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report.",
    )
    args = parser.parse_args()

    reports = [
        check_package(
            package_name,
            recursive=not args.no_recursive,
            check_sort=not args.no_sort_check,
        )
        for package_name in args.packages
    ]

    if args.json:
        payload = {
            "packages": [
                {
                    "package": report.package,
                    "modules_checked": report.modules_checked,
                    "findings": [asdict(finding) for finding in report.findings],
                }
                for report in reports
            ]
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_format_human_report(reports))

    if any(report.findings for report in reports):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
