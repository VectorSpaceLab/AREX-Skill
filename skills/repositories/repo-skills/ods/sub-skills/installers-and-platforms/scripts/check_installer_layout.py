#!/usr/bin/env python3
"""Read-only ODS installer layout checker.

This helper validates expected installer entry points, phase files, platform
orchestrators, and key test/doc anchors in an ODS source checkout. It never
installs packages, starts Docker, downloads models, or edits files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


LINUX_LIBS = [
    "amd-topo.sh",
    "background-tasks.sh",
    "bootstrap-model.sh",
    "compose-failure-report.sh",
    "compose-images.sh",
    "compose-select.sh",
    "constants.sh",
    "detection.sh",
    "docker-images.sh",
    "external-services.sh",
    "host-arch.sh",
    "llama-memory-budget.sh",
    "logging.sh",
    "model-lifecycle-lock.sh",
    "nvidia-topo.sh",
    "packaging.sh",
    "path-utils.sh",
    "progress.sh",
    "python-runtime.sh",
    "readiness-summary.sh",
    "sudo.sh",
    "tier-map.sh",
    "ui.sh",
]

LINUX_PHASES = [
    "01-preflight.sh",
    "02-detection.sh",
    "02b-external-services.sh",
    "03-features.sh",
    "04-requirements.sh",
    "05-docker.sh",
    "06-directories.sh",
    "07-devtools.sh",
    "08-images.sh",
    "09-offline.sh",
    "10-amd-tuning.sh",
    "11-services.sh",
    "12-health.sh",
    "13-summary.sh",
]

LINUX_INSTALL_CORE_ORDER = [
    ("01-preflight", "installers/phases/01-preflight.sh"),
    ("02-detection", "installers/phases/02-detection.sh"),
    ("02b-external-services", "installers/phases/02b-external-services.sh"),
    ("03-features", "installers/phases/03-features.sh"),
    ("04-requirements", "installers/phases/04-requirements.sh"),
    ("05-docker", "installers/phases/05-docker.sh"),
    ("06-directories", "installers/phases/06-directories.sh"),
    ("07-devtools", "installers/phases/07-devtools.sh"),
    ("08-images", "installers/phases/08-images.sh"),
    ("09-offline", "installers/phases/09-offline.sh"),
    ("10-amd-tuning", "installers/phases/10-amd-tuning.sh"),
    ("11-services", "installers/phases/11-services.sh"),
    ("12-health", "installers/phases/12-health.sh"),
    ("13-summary", "installers/phases/13-summary.sh"),
]

MACOS_LIBS = [
    "bridge-manager.sh",
    "constants.sh",
    "detection.sh",
    "env-generator.sh",
    "installed-footprint.sh",
    "preflight-fs.sh",
    "tier-map.sh",
    "ui.sh",
]

WINDOWS_LIBS = [
    "backend-contract.ps1",
    "compose-diagnostics.ps1",
    "constants.ps1",
    "detection.ps1",
    "env-generator.ps1",
    "installed-footprint.ps1",
    "install-report.ps1",
    "llm-endpoint.ps1",
    "model-activation.ps1",
    "opencode-config.ps1",
    "readiness-summary.ps1",
    "service-plan.ps1",
    "tier-map.ps1",
    "ui.ps1",
]

WINDOWS_PHASES = [
    "01-preflight.ps1",
    "02-detection.ps1",
    "03-features.ps1",
    "04-requirements.ps1",
    "05-docker.ps1",
    "06-directories.ps1",
    "07-devtools.ps1",
]

DOC_ANCHORS = [
    "docs/INSTALLER-ARCHITECTURE.md",
    "docs/INSTALLER_PHASE_CONTRACTS.md",
    "docs/INSTALL-TROUBLESHOOTING.md",
    "docs/MACOS-QUICKSTART.md",
    "docs/WINDOWS-QUICKSTART.md",
    "docs/WINDOWS-TROUBLESHOOTING-GUIDE.md",
    "docs/LINUX-TROUBLESHOOTING-GUIDE.md",
]

TEST_ANCHORS = [
    "tests/contracts/test-installer-contracts.sh",
    "tests/contracts/test-preflight-fixtures.sh",
    "tests/smoke/linux-nvidia.sh",
    "tests/smoke/linux-amd.sh",
    "tests/smoke/macos-dispatch.sh",
    "tests/smoke/wsl-logic.sh",
    "tests/test-windows-installer-flags.sh",
]


@dataclass
class Finding:
    level: str
    check: str
    message: str
    path: str | None = None


class Checker:
    def __init__(self, source_root: Path, outer_root: Path | None = None) -> None:
        self.source_root = source_root
        self.outer_root = outer_root
        self.findings: list[Finding] = []

    def add(self, level: str, check: str, message: str, path: Path | str | None = None) -> None:
        self.findings.append(
            Finding(level=level, check=check, message=message, path=str(path) if path is not None else None)
        )

    def ok(self, check: str, message: str, path: Path | str | None = None) -> None:
        self.add("ok", check, message, path)

    def warn(self, check: str, message: str, path: Path | str | None = None) -> None:
        self.add("warn", check, message, path)

    def error(self, check: str, message: str, path: Path | str | None = None) -> None:
        self.add("error", check, message, path)

    def require_file(self, rel: str, check: str) -> None:
        path = self.source_root / rel
        if path.is_file():
            self.ok(check, f"found {rel}", path)
        else:
            self.error(check, f"missing required file: {rel}", path)

    def require_outer_file(self, rel: str, check: str) -> None:
        if self.outer_root is None:
            self.warn(check, f"outer checkout root unavailable; skipped {rel}")
            return
        path = self.outer_root / rel
        if path.is_file():
            self.ok(check, f"found outer {rel}", path)
        else:
            self.error(check, f"missing required outer file: {rel}", path)

    def read_text(self, rel: str) -> str:
        path = self.source_root / rel
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            self.error("read", f"cannot read missing file: {rel}", path)
            return ""


def detect_roots(repo: Path) -> tuple[Path, Path | None]:
    """Return (inner ods source root, outer checkout root if known)."""
    repo = repo.expanduser().resolve()

    if (repo / "install-core.sh").is_file() and (repo / "installers").is_dir():
        outer = repo.parent if (repo.parent / "install.sh").is_file() or (repo.parent / "install.ps1").is_file() else None
        return repo, outer

    inner = repo / "ods"
    if (inner / "install-core.sh").is_file() and (inner / "installers").is_dir():
        return inner.resolve(), repo

    raise SystemExit(
        f"Could not locate an ODS source root under {repo}. "
        "Pass the repository root containing ods/, or the inner ods/ directory."
    )


def compare_directory_files(checker: Checker, rel_dir: str, expected: Iterable[str], check_name: str) -> None:
    directory = checker.source_root / rel_dir
    expected_set = set(expected)
    if not directory.is_dir():
        checker.error(check_name, f"missing directory: {rel_dir}", directory)
        return

    actual_set = {p.name for p in directory.iterdir() if p.is_file()}
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)

    if missing:
        checker.error(check_name, f"missing files in {rel_dir}: {', '.join(missing)}", directory)
    else:
        checker.ok(check_name, f"all expected files present in {rel_dir}", directory)

    if extra:
        checker.warn(check_name, f"extra files in {rel_dir}: {', '.join(extra)}", directory)


def check_entrypoints(checker: Checker) -> None:
    checker.require_outer_file("install.sh", "entrypoints")
    checker.require_outer_file("install.ps1", "entrypoints")
    for rel in [
        "install.sh",
        "install-core.sh",
        "installers/dispatch.sh",
        "installers/common.sh",
        "installers/macos/install-macos.sh",
        "installers/macos/ods-macos.sh",
        "installers/macos.sh",
        "installers/windows/install-windows.ps1",
        "installers/windows/ods.ps1",
        "installers/windows.ps1",
    ]:
        checker.require_file(rel, "entrypoints")

    dispatch = checker.read_text("installers/dispatch.sh")
    expected_routes = {
        "linux|wsl": "install-core.sh",
        "macos": "installers/macos/install-macos.sh",
        "windows": "installers/windows/install-windows.ps1",
        "android-termux|ios-ashell": "installers/mobile/install-mobile.sh",
    }
    for case_label, target in expected_routes.items():
        if case_label in dispatch and target in dispatch:
            checker.ok("dispatch", f"dispatch includes {case_label} -> {target}")
        else:
            checker.error("dispatch", f"dispatch missing {case_label} -> {target}")


def check_linux_layout(checker: Checker, headers: bool) -> None:
    compare_directory_files(checker, "installers/lib", LINUX_LIBS, "linux-libs")
    compare_directory_files(checker, "installers/phases", LINUX_PHASES, "linux-phases")

    text = checker.read_text("install-core.sh")
    order: list[tuple[str, str]] = []
    pending_phase: str | None = None
    for line in text.splitlines():
        phase_match = re.search(r'INSTALL_PHASE="([^"]+)"', line)
        if phase_match:
            pending_phase = phase_match.group(1)
        source_match = re.search(r'source "\$SCRIPT_DIR/(installers/phases/[^"]+)"', line)
        if source_match and pending_phase:
            order.append((pending_phase, source_match.group(1)))
            pending_phase = None
    if order == LINUX_INSTALL_CORE_ORDER:
        checker.ok("linux-phase-order", "install-core.sh sources expected Linux phases in order")
    else:
        checker.error(
            "linux-phase-order",
            "install-core.sh phase source order differs from expected",
            checker.source_root / "install-core.sh",
        )
        checker.warn("linux-phase-order", f"observed order: {order}")

    for token in [
        'INSTALL_PHASE="model-lifecycle-lock"',
        "ods_model_lifecycle_lock_acquire",
        "ods_model_lifecycle_lock_release",
        'INSTALL_PHASE="13-summary"',
        "set +e",
    ]:
        if token in text:
            checker.ok("linux-orchestrator", f"found {token}")
        else:
            checker.error("linux-orchestrator", f"missing {token}", checker.source_root / "install-core.sh")

    if headers:
        for phase in LINUX_PHASES:
            rel = f"installers/phases/{phase}"
            body = checker.read_text(rel).splitlines()[:35]
            header = "\n".join(body)
            missing = [label for label in ["Purpose:", "Expects:", "Provides:", "Modder notes:"] if label not in header]
            if missing:
                checker.warn("phase-headers", f"{rel} missing header fields: {', '.join(missing)}", checker.source_root / rel)
            else:
                checker.ok("phase-headers", f"{rel} has standard header fields", checker.source_root / rel)


def check_macos_layout(checker: Checker) -> None:
    compare_directory_files(checker, "installers/macos/lib", MACOS_LIBS, "macos-libs")
    text = checker.read_text("installers/macos/install-macos.sh")
    for token in [
        "ODS macOS Installer -- Main Orchestrator",
        "--dry-run",
        "Bash 4+",
        "Apple Silicon",
        "PHASE 1 -- PREFLIGHT CHECKS",
        "PHASE 2 -- HARDWARE DETECTION",
        "PHASE 3 -- FEATURE SELECTION",
        "PHASE 4 -- SETUP",
        "PHASE 5 -- LAUNCH",
        "PHASE 6 -- VERIFICATION",
        "ComfyUI:",
    ]:
        if token in text:
            checker.ok("macos-installer", f"found {token}")
        else:
            checker.error("macos-installer", f"missing {token}", checker.source_root / "installers/macos/install-macos.sh")

    cli = checker.read_text("installers/macos/ods-macos.sh")
    for cmd in ["status", "start", "stop", "restart", "logs", "update"]:
        if re.search(rf"\b{re.escape(cmd)}\)", cli) or f"{cmd})" in cli:
            checker.ok("macos-cli", f"ods-macos.sh handles {cmd}")
        else:
            checker.warn("macos-cli", f"ods-macos.sh command not detected: {cmd}")


def check_windows_layout(checker: Checker) -> None:
    compare_directory_files(checker, "installers/windows/lib", WINDOWS_LIBS, "windows-libs")
    compare_directory_files(checker, "installers/windows/phases", WINDOWS_PHASES, "windows-phases")

    text = checker.read_text("installers/windows/install-windows.ps1")
    sourced = re.findall(r'Join-Path \$PhasesDir "([^"]+\.ps1)"', text)
    # Keep first occurrence order while ignoring duplicates, if any.
    seen: list[str] = []
    for item in sourced:
        if item not in seen:
            seen.append(item)
    if seen[: len(WINDOWS_PHASES)] == WINDOWS_PHASES:
        checker.ok("windows-phase-order", "Windows installer dot-sources phases 01-07 in order")
    else:
        checker.error("windows-phase-order", f"unexpected Windows phase order: {seen}")

    for token in [
        "PHASE 8 -- LAUNCH",
        "PHASE 9 -- VERIFY",
        "[switch]$DryRun",
        "[string]$InstallDir = \"\"",
        "ODS_INSTALL_ABORTED",
        "Get-UsableWindowsBash",
    ]:
        if token in text:
            checker.ok("windows-installer", f"found {token}")
        else:
            checker.error("windows-installer", f"missing {token}", checker.source_root / "installers/windows/install-windows.ps1")

    cli = checker.read_text("installers/windows/ods.ps1")
    for cmd in ["status", "start", "stop", "restart", "logs", "update", "uninstall", "report"]:
        if re.search(rf"\b{re.escape(cmd)}\b", cli, flags=re.IGNORECASE):
            checker.ok("windows-cli", f"ods.ps1 mentions/handles {cmd}")
        else:
            checker.warn("windows-cli", f"ods.ps1 command not detected: {cmd}")


def check_docs_and_tests(checker: Checker) -> None:
    for rel in DOC_ANCHORS:
        checker.require_file(rel, "docs")
    for rel in TEST_ANCHORS:
        checker.require_file(rel, "tests")

    contracts = checker.read_text("tests/contracts/test-installer-contracts.sh")
    for token in [
        "backend contract files",
        "cross-platform installed footprint",
        "canonical port contract parity",
        "Windows AMD local compose readiness",
        "bootstrap hot-swap",
    ]:
        if token in contracts:
            checker.ok("installer-contracts", f"contract includes {token}")
        else:
            checker.warn("installer-contracts", f"contract token not found: {token}")

    preflight = checker.read_text("tests/contracts/test-preflight-fixtures.sh")
    for fixture in ["linux-nvidia-good", "windows-mvp-good", "macos-mvp-good", "disk-blocker", "cloud-low-storage-good"]:
        if fixture in preflight:
            checker.ok("preflight-fixtures", f"fixture present: {fixture}")
        else:
            checker.error("preflight-fixtures", f"fixture missing: {fixture}")


def render_text(findings: list[Finding]) -> str:
    symbols = {"ok": "OK", "warn": "WARN", "error": "ERROR"}
    lines = []
    for finding in findings:
        prefix = symbols.get(finding.level, finding.level.upper())
        location = f" ({finding.path})" if finding.path else ""
        lines.append(f"[{prefix}] {finding.check}: {finding.message}{location}")
    counts = {level: sum(1 for f in findings if f.level == level) for level in ["ok", "warn", "error"]}
    lines.append(f"Summary: {counts['ok']} ok, {counts['warn']} warn, {counts['error']} error")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only static checker for ODS installer/platform layout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="ODS checkout root containing ods/, or the inner ods/ source directory.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--headers",
        action="store_true",
        help="Also inspect phase header fields. Missing fields are warnings unless --strict is set.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--no-fail", action="store_true", help="Always exit 0 after reporting findings.")
    args = parser.parse_args(argv)

    source_root, outer_root = detect_roots(Path(args.repo))
    checker = Checker(source_root=source_root, outer_root=outer_root)

    check_entrypoints(checker)
    check_linux_layout(checker, headers=args.headers)
    check_macos_layout(checker)
    check_windows_layout(checker)
    check_docs_and_tests(checker)

    payload = {
        "kind": "ods-installer-layout-check",
        "source_root": str(source_root),
        "outer_root": str(outer_root) if outer_root else None,
        "findings": [asdict(f) for f in checker.findings],
        "summary": {
            "ok": sum(1 for f in checker.findings if f.level == "ok"),
            "warn": sum(1 for f in checker.findings if f.level == "warn"),
            "error": sum(1 for f in checker.findings if f.level == "error"),
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(checker.findings))

    if args.no_fail:
        return 0
    if payload["summary"]["error"]:
        return 1
    if args.strict and payload["summary"]["warn"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
