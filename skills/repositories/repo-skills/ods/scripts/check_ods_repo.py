#!/usr/bin/env python3
"""Read-only ODS repository layout checker.

This helper is bundled with the generated ODS repo skill. It checks whether a
supplied ODS checkout still has the major files and directories expected by the
skill. It does not install packages, start Docker, modify files, or run native
ODS tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

REQUIRED_PATHS = [
    "README.md",
    "install.sh",
    "install.ps1",
    "ods/README.md",
    "ods/manifest.json",
    "ods/Makefile",
    "ods/ods-cli",
    "ods/install.sh",
    "ods/install-core.sh",
    "ods/installers/lib/detection.sh",
    "ods/installers/lib/tier-map.sh",
    "ods/installers/phases/01-preflight.sh",
    "ods/installers/phases/13-summary.sh",
    "ods/installers/macos/install-macos.sh",
    "ods/installers/windows/install-windows.ps1",
    "ods/extensions/services/dashboard-api/main.py",
    "ods/extensions/services/dashboard/package.json",
    "ods/scripts/resolve-compose-stack.sh",
    "ods/scripts/audit-extensions.py",
    "ods/scripts/select-model.py",
    "ods/docker-compose.base.yml",
    "ods/config/model-library.json",
    "ods/config/backends/nvidia.json",
    "ods/config/backends/amd.json",
    "ods/tests/test-tier-map.sh",
    "ods/tests/contracts/test-installer-contracts.sh",
]

EXPECTED_SUBSKILL_HINTS = {
    "installers-and-platforms": [
        "ods/install-core.sh",
        "ods/installers/phases",
        "ods/installers/windows",
        "ods/installers/macos",
    ],
    "hardware-and-models": [
        "ods/config/model-library.json",
        "ods/config/backends",
        "ods/scripts/select-model.py",
    ],
    "services-and-extensions": [
        "ods/extensions/services",
        "ods/extensions/library",
        "ods/scripts/resolve-compose-stack.sh",
    ],
    "dashboard-and-api": [
        "ods/extensions/services/dashboard-api",
        "ods/extensions/services/dashboard",
    ],
    "ops-cli-and-host-tools": [
        "ods/ods-cli",
        "ods/bin/ods-host-agent.py",
        "ods/scripts/ods-doctor.sh",
    ],
    "testing-and-release": [
        "ods/Makefile",
        "ods/tests",
        ".github/workflows",
    ],
}


def existing(paths: Iterable[str], root: Path) -> list[str]:
    return [p for p in paths if (root / p).exists()]


def missing(paths: Iterable[str], root: Path) -> list[str]:
    return [p for p in paths if not (root / p).exists()]


def build_report(root: Path) -> dict[str, object]:
    report: dict[str, object] = {
        "root": str(root),
        "required_present": existing(REQUIRED_PATHS, root),
        "required_missing": missing(REQUIRED_PATHS, root),
        "subskill_hints": {},
    }
    hints: dict[str, object] = {}
    for subskill, paths in EXPECTED_SUBSKILL_HINTS.items():
        present = existing(paths, root)
        hints[subskill] = {
            "present": present,
            "missing": missing(paths, root),
            "status": "ok" if len(present) == len(paths) else "stale-or-partial",
        }
    report["subskill_hints"] = hints
    manifest_count = len(list((root / "ods/extensions/services").glob("*/manifest.yaml")))
    report["service_manifest_count"] = manifest_count
    phase_count = len(list((root / "ods/installers/phases").glob("*.sh")))
    report["linux_phase_count"] = phase_count
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an ODS checkout against the generated repo-skill layout assumptions.")
    parser.add_argument("--root", default=".", help="Path to an ODS repository checkout. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human summary.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        missing_required = report["required_missing"]
        print(f"ODS layout check for: {root}")
        print(f"required paths present: {len(report['required_present'])}/{len(REQUIRED_PATHS)}")
        print(f"service manifests found: {report['service_manifest_count']}")
        print(f"Linux installer phases found: {report['linux_phase_count']}")
        if missing_required:
            print("missing required paths:")
            for item in missing_required:
                print(f"  - {item}")
        for subskill, detail in report["subskill_hints"].items():
            print(f"{subskill}: {detail['status']}")
    return 1 if report["required_missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
