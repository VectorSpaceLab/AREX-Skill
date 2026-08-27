#!/usr/bin/env python3
"""Recommend focused ODS validation lanes from changed paths.

This helper is intentionally read-only. It does not inspect the filesystem,
start Docker, install dependencies, run tests, or edit files. It prints source-
backed commands a future agent can choose from after reviewing safety/cost.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict, dataclass, replace
from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Lane:
    id: str
    title: str
    owner: str
    safety: str
    cost: str
    commands: tuple[str, ...]
    evidence: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Rule:
    id: str
    patterns: tuple[str, ...]
    lanes: tuple[str, ...]
    reason: str


LANES: dict[str, Lane] = {
    "quick-baseline": Lane(
        id="quick-baseline",
        title="Quick static baseline",
        owner="testing-and-release",
        safety="read-only/static",
        cost="low",
        commands=(
            "cd ods && make lint",
            "cd ods && bash tests/test-doc-links.sh",
        ),
        evidence=("ods/Makefile", "ods/tests/test-doc-links.sh"),
        notes=("Use when changed paths do not map cleanly to a more specific lane.",),
    ),
    "docs": Lane(
        id="docs",
        title="Documentation checks",
        owner="testing-and-release plus owning implementation area",
        safety="read-only/static",
        cost="low",
        commands=(
            "cd ods && bash tests/test-doc-links.sh",
            "cd ods && bash tests/test-install-docs.sh",
        ),
        evidence=("ods/docs/TESTING.md", "ods/tests/test-doc-links.sh", "ods/tests/test-install-docs.sh"),
        notes=("Add release-claim checks when support, validation, or launch-claim wording changed.",),
    ),
    "release-claims": Lane(
        id="release-claims",
        title="Release and support claim checks",
        owner="testing-and-release",
        safety="read-only/static",
        cost="low-to-moderate",
        commands=(
            "cd ods && bash scripts/check-release-claims.sh",
            "cd ods && python3 scripts/check-version-consistency.py",
            "cd ods && python3 scripts/validate-golden-paths.py",
            "cd ods && python3 scripts/validate-generated-configs.py",
            "cd ods && python3 scripts/check-dependency-pins.py",
        ),
        evidence=(
            "ods/docs/RELEASE_VALIDATION.md",
            "ods/docs/VALIDATION-MATRIX.md",
            "ods/docs/SUPPORT-MATRIX.md",
            "ods/docs/PLATFORM-TRUTH-TABLE.md",
            "ods/scripts/check-release-claims.sh",
            "ods/scripts/release-gate.sh",
        ),
        notes=("A source-level pass is not User Green; release notes still need a sanitized current evidence receipt.",),
    ),
    "shell-lint": Lane(
        id="shell-lint",
        title="Shell syntax and ShellCheck parity",
        owner="testing-and-release",
        safety="read-only/static",
        cost="low",
        commands=(
            "cd ods && make lint",
            "# For ShellCheck CI parity, run shellcheck with lint-shell.yml excludes and severity for changed files.",
        ),
        evidence=("ods/Makefile", ".github/workflows/lint-shell.yml", ".pre-commit-config.yaml"),
        notes=("Makefile lint is syntax-only for shell; CI also runs ShellCheck and localhost curl guards.",),
    ),
    "python-lint": Lane(
        id="python-lint",
        title="Python lint/compile/type-check focus",
        owner="testing-and-release plus Python-owning sub-skill",
        safety="read-only/static",
        cost="low-to-moderate",
        commands=(
            "cd ods && python3 -m py_compile extensions/services/dashboard-api/main.py extensions/services/dashboard-api/agent_monitor.py",
            "ruff check ods/ --select E,F,W --ignore E501,E701,E731,E741,E402",
            "# For type-check parity, reproduce the changed service step from .github/workflows/type-check-python.yml.",
        ),
        evidence=("ods/Makefile", ".github/workflows/lint-python.yml", ".github/workflows/type-check-python.yml"),
        notes=("mypy workflow steps are continue-on-error but are still useful quality signals.",),
    ),
    "powershell": Lane(
        id="powershell",
        title="PowerShell installer and Windows contract checks",
        owner="installers-and-platforms",
        safety="safe-runnable; Windows-specific parts need matching runner",
        cost="moderate",
        commands=(
            "cd ods && pwsh -Command 'Invoke-ScriptAnalyzer -Path installers -Settings ./PSScriptAnalyzerSettings.psd1 -Severity Error,Warning'",
            "cd ods && pwsh ./tests/contracts/test-windows-lemonade-task-cleanup.ps1",
            "cd ods && pwsh ./tests/test-windows-model-activation.ps1",
            "cd ods && pwsh ./tests/test-windows-catalog-selector.ps1",
        ),
        evidence=(".github/workflows/lint-powershell.yml", "ods/PSScriptAnalyzerSettings.psd1"),
        notes=("Windows-only installed-footprint tests require a Windows runner and should not be inferred from Linux.",),
    ),
    "installer-contracts": Lane(
        id="installer-contracts",
        title="Installer contracts and preflight fixtures",
        owner="installers-and-platforms",
        safety="safe-runnable",
        cost="low-to-moderate",
        commands=(
            "cd ods && bash tests/contracts/test-installer-contracts.sh",
            "cd ods && bash tests/contracts/test-preflight-fixtures.sh",
            "cd ods && bash tests/test-linux-install-preflight.sh",
            "cd ods && bash tests/test-install-docs.sh",
        ),
        evidence=("ods/install-core.sh", "ods/installers/", "ods/tests/contracts/", "ods/Makefile"),
        notes=("Use dry-run, syntax, contract, smoke, and simulation before any real installer.",),
    ),
    "smoke-simulate": Lane(
        id="smoke-simulate",
        title="Platform smoke and installer simulation",
        owner="installers-and-platforms plus testing-and-release",
        safety="moderate; writes local simulation artifacts",
        cost="moderate/expensive",
        commands=(
            "cd ods && bash tests/smoke/linux-amd.sh",
            "cd ods && bash tests/smoke/linux-nvidia.sh",
            "cd ods && bash tests/smoke/wsl-logic.sh",
            "cd ods && bash tests/smoke/macos-dispatch.sh",
            "cd ods && bash scripts/simulate-installers.sh",
        ),
        evidence=("ods/tests/smoke/", "ods/scripts/simulate-installers.sh", "ods/docs/TESTING.md"),
        notes=("Simulation is broader than focused contracts but still not a real full install.",),
    ),
    "hardware-models": Lane(
        id="hardware-models",
        title="Hardware, backend, tier, and model catalog contracts",
        owner="hardware-and-models",
        safety="safe-runnable/static",
        cost="low-to-moderate",
        commands=(
            "cd ods && bash tests/test-tier-map.sh",
            "cd ods && bash tests/test-tier-map-parity.sh",
            "cd ods && python3 tests/test-model-library-coverage.py",
            "cd ods && python3 tests/test-model-library-verdicts.py",
            "cd ods && bash tests/contracts/test-overlay-map-coherence.sh",
            "cd ods && python3 tests/contracts/test-llama-runtime-tunables.py",
        ),
        evidence=("ods/installers/lib/tier-map.sh", "ods/config/model-library.json", "ods/tests/test-tier-map.sh"),
        notes=("These checks do not prove live GPU runtime; use matching hardware evidence for accelerator claims.",),
    ),
    "compose": Lane(
        id="compose",
        title="Compose resolver and overlay validation",
        owner="services-and-extensions plus hardware-and-models",
        safety="needs-docker-config",
        cost="low-to-moderate",
        commands=(
            "cd ods && bash tests/test-resolve-compose-resilient.sh",
            "cd ods && bash tests/contracts/test-overlay-map-coherence.sh",
            "cd ods && bash scripts/validate-compose-stack.sh --compose-flags \"-f docker-compose.base.yml -f <overlay>\"",
            "cd ods && docker compose -f docker-compose.base.yml config --quiet",
        ),
        evidence=("ods/scripts/resolve-compose-stack.sh", "ods/scripts/validate-compose-stack.sh", ".github/workflows/validate-compose.yml"),
        notes=("Use CI placeholder env values for compose variables; do not use real secrets.",),
    ),
    "extensions": Lane(
        id="extensions",
        title="Extension manifest, audit, and catalog validation",
        owner="services-and-extensions",
        safety="safe-runnable; optional Docker/Schema deps",
        cost="low-to-moderate",
        commands=(
            "cd ods && python3 scripts/audit-extensions.py --project-dir .",
            "cd ods && bash tests/test-extension-audit.sh",
            "cd ods && bash scripts/validate-manifests.sh",
            "cd ods && bash tests/test-validate-manifests.sh",
            "python ods/scripts/generate-extensions-catalog.py",
        ),
        evidence=("ods/extensions/services/", "ods/extensions/library/", "ods/scripts/audit-extensions.py", "ods/scripts/validate-manifests.sh"),
        notes=("Install PyYAML/jsonschema for strict schema validation.",),
    ),
    "dashboard-api": Lane(
        id="dashboard-api",
        title="Dashboard API tests",
        owner="dashboard-and-api",
        safety="safe-runnable; service deps required",
        cost="moderate",
        commands=(
            "cd ods/extensions/services/dashboard-api && pytest tests/ -q",
            "cd ods && python3 -m py_compile extensions/services/dashboard-api/main.py extensions/services/dashboard-api/agent_monitor.py",
        ),
        evidence=("ods/extensions/services/dashboard-api/", ".github/workflows/dashboard.yml"),
        notes=("Run from the dashboard-api service directory after installing its requirements.",),
    ),
    "dashboard-ui": Lane(
        id="dashboard-ui",
        title="Dashboard frontend lint/test/build",
        owner="dashboard-and-api",
        safety="safe-runnable; Node deps required",
        cost="moderate",
        commands=(
            "cd ods/extensions/services/dashboard && npm ci",
            "cd ods/extensions/services/dashboard && npm run lint",
            "cd ods/extensions/services/dashboard && npm run test",
            "cd ods/extensions/services/dashboard && npm run build",
        ),
        evidence=("ods/extensions/services/dashboard/", ".github/workflows/dashboard.yml"),
        notes=("Node dependency installation may be time/network heavy but is not a product install.",),
    ),
    "ops-cli": Lane(
        id="ops-cli",
        title="ODS CLI, host tools, and diagnostics contracts",
        owner="ops-cli-and-host-tools",
        safety="safe-runnable/help-oriented by default",
        cost="low-to-moderate",
        commands=(
            "cd ods && bash tests/run-bats.sh",
            "cd ods && bash tests/test-ods-cli-pipefail-tolerance.sh",
            "cd ods && bash tests/test-ods-doctor.sh",
            "cd ods && bash tests/test-cli-update-verification.sh",
            "cd ods && bash tests/test-support-bundle.sh",
        ),
        evidence=("ods/ods-cli", "ods/scripts/ods-doctor.sh", "ods/tests/run-bats.sh", "ods/Makefile"),
        notes=("Lifecycle or stack-mutating commands need explicit user intent.",),
    ),
    "env-config": Lane(
        id="env-config",
        title="Environment schema and generated config contracts",
        owner="testing-and-release plus owning implementation area",
        safety="safe-runnable/static",
        cost="low-to-moderate",
        commands=(
            "cd ods && bash tests/test-validate-env.sh",
            "cd ods && bash tests/test-generated-config-contracts.sh",
            "cd ods && bash tests/test-golden-paths.sh",
            "cd ods && python3 scripts/validate-generated-configs.py",
            "cd ods && python3 scripts/validate-golden-paths.py",
        ),
        evidence=("ods/.env.schema.json", "ods/scripts/validate-env.sh", "ods/config/golden-paths.json"),
        notes=("validate-env.sh needs Bash 4+ and jq and parses rather than sources .env.",),
    ),
    "ci-workflow": Lane(
        id="ci-workflow",
        title="CI workflow command parity",
        owner="testing-and-release",
        safety="read-only/static to moderate",
        cost="varies by workflow",
        commands=(
            "# Reproduce the failing workflow step command from .github/workflows/<workflow>.yml.",
            "cd ods && make lint",
            "cd ods && bash tests/run-bats.sh",
            "cd ods && bash scripts/simulate-installers.sh  # only if the workflow or step requires simulation",
        ),
        evidence=(".github/workflows/", "ods/docs/TESTING.md"),
        notes=("Some YAML/action behavior needs GitHub-side confirmation; document what cannot be reproduced locally.",),
    ),
    "security-scan": Lane(
        id="security-scan",
        title="Pre-commit and secret scan checks",
        owner="testing-and-release",
        safety="read-only/static",
        cost="low-to-moderate",
        commands=(
            "pre-commit run --all-files",
            "gitleaks detect --redact --source .",
            "cd ods && bash tests/test-issue-to-pr-security.sh",
        ),
        evidence=(".pre-commit-config.yaml", ".gitleaks.toml", ".github/workflows/secret-scan.yml"),
        notes=("Prefer redaction/removal over allowlists. Allowlist only documented non-secret templates.",),
    ),
    "dependency": Lane(
        id="dependency",
        title="Dependency and package lock checks",
        owner="owning service plus testing-and-release",
        safety="safe-runnable; dependency installs may need network",
        cost="moderate",
        commands=(
            "cd ods && python3 scripts/check-dependency-pins.py",
            "# Also run the owning service lane, e.g. dashboard API pytest or dashboard UI npm checks.",
        ),
        evidence=("ods/config/dependency-lock.json", "ods/scripts/check-dependency-pins.py", ".github/workflows/dashboard.yml"),
        notes=("Small dependency diffs can have release risk when they affect runtime images or startup paths.",),
    ),
    "changed-tests": Lane(
        id="changed-tests",
        title="Run changed tests directly",
        owner="testing-and-release plus owning implementation area",
        safety="safe-runnable; depends on changed test",
        cost="low-to-moderate",
        commands=("# Dynamic commands are generated from changed test paths.",),
        evidence=("ods/tests/", "ods/extensions/services/dashboard-api/tests/", "ods/extensions/services/dashboard/src/"),
        notes=("Run changed tests first, then the smallest owning surface lane.",),
    ),
}

ESCALATION_LANES: tuple[Lane, ...] = (
    Lane(
        id="make-gate",
        title="Makefile full pre-release gate",
        owner="testing-and-release",
        safety="expensive",
        cost="high",
        commands=("cd ods && make gate",),
        evidence=("ods/Makefile",),
        notes=("Runs lint, test, BATS, smoke, and installer simulation; not default for small changes.",),
    ),
    Lane(
        id="release-gate-script",
        title="Release checklist script",
        owner="testing-and-release",
        safety="expensive",
        cost="high",
        commands=("cd ods && bash scripts/release-gate.sh",),
        evidence=("ods/scripts/release-gate.sh",),
        notes=("Separate from make gate; includes release claims, selected contracts, smoke, simulation, and update rollback.",),
    ),
    Lane(
        id="fleet-distros",
        title="Docker multi-distro fleet",
        owner="testing-and-release",
        safety="expensive; needs Docker daemon and host lock",
        cost="very high",
        commands=("cd ods && make fleet-distros", "cd ods && bash tests/fleet-multi-distro.sh <distro>"),
        evidence=("ods/tests/fleet-multi-distro.sh", "ods/docs/TESTING.md"),
        notes=("Use for Linux package-manager/distro breadth and release-risk installer changes.",),
    ),
    Lane(
        id="fleet-vms",
        title="Incus VM fleet",
        owner="testing-and-release",
        safety="expensive; needs Incus/KVM/systemd VM images and host lock",
        cost="very high",
        commands=("cd ods && make fleet-vms", "cd ods && bash tests/fleet-incus-vm.sh <distro>"),
        evidence=("ods/tests/fleet-incus-vm.sh", "ods/docs/TESTING.md"),
        notes=("Use for systemd and Docker-daemon realism that containers cannot prove.",),
    ),
    Lane(
        id="post-install-validation",
        title="Post-install stack validation",
        owner="testing-and-release plus ops-cli-and-host-tools",
        safety="post-install; host/runtime dependent",
        cost="high",
        commands=("cd ods && bash scripts/validate.sh", "cd ods && bash scripts/ods-test.sh --quick"),
        evidence=("ods/scripts/validate.sh", "ods/scripts/README.md"),
        notes=("Requires a running/installed ODS stack; not a source-only check.",),
    ),
    Lane(
        id="real-hardware-fleet",
        title="Release-grade real-hardware fleet",
        owner="release operator",
        safety="expensive; host-mutating release evidence",
        cost="very high",
        commands=("No public one-size command; run the authorized release fleet harness and publish a sanitized receipt.",),
        evidence=("ods/docs/RELEASE_VALIDATION.md", "ods/docs/VALIDATION-MATRIX.md"),
        notes=("Required for User Green and live accelerator/product claims; CI/focused tests are not enough.",),
    ),
)

RULES: tuple[Rule, ...] = (
    Rule(
        id="release-docs",
        patterns=(
            "ods/docs/RELEASE_VALIDATION.md",
            "ods/docs/VALIDATION-MATRIX.md",
            "ods/docs/SUPPORT-MATRIX.md",
            "ods/docs/PLATFORM-TRUTH-TABLE.md",
            "ods/docs/RELEASE_CHANNELS.md",
            "ods/manifest.json",
            "ods/CHANGELOG.md",
        ),
        lanes=("docs", "release-claims"),
        reason="release, support, version, or validation claim changed",
    ),
    Rule(
        id="docs",
        patterns=("README.md", "CONTRIBUTING.md", "SECURITY.md", "ods/README.md", "ods/QUICKSTART.md", "ods/FAQ.md", "ods/docs/**"),
        lanes=("docs",),
        reason="documentation changed",
    ),
    Rule(
        id="ci",
        patterns=(".github/workflows/**",),
        lanes=("ci-workflow",),
        reason="GitHub Actions workflow changed",
    ),
    Rule(
        id="security",
        patterns=(".pre-commit-config.yaml", ".gitleaks.toml", ".gitleaksignore", ".github/workflows/secret-scan.yml", "ods/scripts/check-heredoc-backticks.awk"),
        lanes=("security-scan",),
        reason="secret scan or local pre-commit policy changed",
    ),
    Rule(
        id="shell",
        patterns=("*.sh", "ods/*.sh", "ods/**/*.sh", "ods/ods-cli", "ods/get-ods.sh"),
        lanes=("shell-lint",),
        reason="shell script or shell entrypoint changed",
    ),
    Rule(
        id="python",
        patterns=("ods/*.py", "ods/**/*.py"),
        lanes=("python-lint",),
        reason="Python file changed",
    ),
    Rule(
        id="powershell",
        patterns=("*.ps1", "ods/*.ps1", "ods/**/*.ps1", "ods/*.psd1", "ods/**/*.psd1"),
        lanes=("powershell",),
        reason="PowerShell file changed",
    ),
    Rule(
        id="installer",
        patterns=(
            "install.sh",
            "install.ps1",
            "ods/install.sh",
            "ods/install-core.sh",
            "ods/get-ods.sh",
            "ods/installers/**",
            "ods/ods-preflight.sh",
            "ods/docs/INSTALL*",
            "ods/docs/PREFLIGHT*",
            "ods/docs/WINDOWS*",
            "ods/docs/MACOS*",
        ),
        lanes=("installer-contracts", "smoke-simulate"),
        reason="installer, preflight, or platform install surface changed",
    ),
    Rule(
        id="hardware-models",
        patterns=(
            "ods/installers/lib/detection.sh",
            "ods/installers/lib/tier-map.sh",
            "ods/installers/macos/lib/tier-map.sh",
            "ods/installers/windows/lib/tier-map.ps1",
            "ods/config/backends/**",
            "ods/config/model-library.json",
            "ods/config/hardware-classes.json",
            "ods/config/gpu-database.json",
            "ods/scripts/select-model.py",
            "ods/scripts/detect-hardware.sh",
            "ods/scripts/classify-hardware.sh",
            "ods/scripts/load-backend-contract.sh",
            "ods/docker-compose.*.yml",
        ),
        lanes=("hardware-models",),
        reason="hardware/backend/tier/model selection surface changed",
    ),
    Rule(
        id="compose",
        patterns=(
            "ods/docker-compose*.yml",
            "ods/extensions/services/**/compose*.yaml",
            "ods/extensions/services/**/compose*.yml",
            "ods/scripts/resolve-compose-stack.sh",
            "ods/scripts/validate-compose-stack.sh",
        ),
        lanes=("compose",),
        reason="compose, overlay, or resolver surface changed",
    ),
    Rule(
        id="extensions",
        patterns=(
            "ods/extensions/services/**/manifest.yaml",
            "ods/extensions/services/**/manifest.yml",
            "ods/extensions/schema/**",
            "ods/extensions/library/**",
            "ods/scripts/audit-extensions.py",
            "ods/scripts/validate-manifests.sh",
            "ods/scripts/validate-manifest-schema.sh",
            "ods/scripts/generate-extensions-catalog.py",
            "ods/config/extensions-catalog.json",
        ),
        lanes=("extensions",),
        reason="extension manifest, schema, library, audit, or catalog surface changed",
    ),
    Rule(
        id="dashboard-api",
        patterns=("ods/extensions/services/dashboard-api/**",),
        lanes=("dashboard-api",),
        reason="dashboard API surface changed",
    ),
    Rule(
        id="dashboard-ui",
        patterns=("ods/extensions/services/dashboard/**",),
        lanes=("dashboard-ui",),
        reason="dashboard frontend surface changed",
    ),
    Rule(
        id="ops-cli",
        patterns=(
            "ods/ods-cli",
            "ods/ods-*.sh",
            "ods/bin/**",
            "ods/lib/**",
            "ods/completions/**",
            "ods/memory-shepherd/**",
            "ods/scripts/ods-doctor.sh",
            "ods/scripts/ods-support-bundle.sh",
            "ods/scripts/session-cleanup.sh",
            "ods/scripts/migrate-config.sh",
        ),
        lanes=("ops-cli",),
        reason="operator CLI, host tool, diagnostics, migration, or shared lib changed",
    ),
    Rule(
        id="env-config",
        patterns=(
            "ods/.env.schema.json",
            "ods/.env.example",
            "ods/config/*.json",
            "ods/config/**/*.json",
            "ods/scripts/validate-env.sh",
            "ods/scripts/render-runtime-configs.py",
            "ods/scripts/validate-generated-configs.py",
            "ods/scripts/validate-golden-paths.py",
        ),
        lanes=("env-config",),
        reason="environment schema, config JSON, or generated config validator changed",
    ),
    Rule(
        id="dependencies",
        patterns=("ods/**/requirements*.txt", "ods/**/package.json", "ods/**/package-lock.json", "ods/**/Dockerfile", "ods/config/dependency-lock.json"),
        lanes=("dependency",),
        reason="dependency, lockfile, package, or image build input changed",
    ),
    Rule(
        id="tests",
        patterns=("ods/tests/**", "ods/extensions/services/dashboard-api/tests/**", "ods/extensions/services/dashboard/src/**/*.test.*"),
        lanes=("changed-tests",),
        reason="test file or test fixture changed",
    ),
)

ORDER: tuple[str, ...] = (
    "changed-tests",
    "docs",
    "release-claims",
    "security-scan",
    "shell-lint",
    "python-lint",
    "powershell",
    "installer-contracts",
    "hardware-models",
    "compose",
    "extensions",
    "dashboard-api",
    "dashboard-ui",
    "ops-cli",
    "env-config",
    "dependency",
    "ci-workflow",
    "smoke-simulate",
    "quick-baseline",
)


def normalize_path(raw: str) -> str | None:
    """Accept plain paths and common `git diff --name-status` lines."""
    text = raw.strip()
    if not text or text.startswith("#"):
        return None
    if " -> " in text:
        text = text.split(" -> ", 1)[1]
    pieces = text.split()
    if len(pieces) > 1:
        status = pieces[0]
        looks_like_name_status = status[0].isalpha() and all(ch.isalpha() or ch.isdigit() for ch in status)
        if looks_like_name_status:
            text = pieces[-1]
    text = text.strip("'\"").replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text or None


def path_variants(path: str) -> set[str]:
    variants = {path}
    if path.startswith("ods/"):
        variants.add(path[4:])
    else:
        variants.add(f"ods/{path}")
    return variants


def matches(pattern: str, path: str) -> bool:
    for variant in path_variants(path):
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if variant == prefix or variant.startswith(prefix + "/"):
                return True
        if fnmatch(variant, pattern):
            return True
    return False


def collect_paths(args: argparse.Namespace) -> list[str]:
    raw_items: list[str] = []
    for item in args.paths:
        raw_items.append(item)
    for file_name in args.paths_from:
        with open(file_name, "r", encoding="utf-8") as handle:
            raw_items.extend(handle.readlines())
    if args.stdin or (not args.paths and not args.paths_from and not sys.stdin.isatty()):
        raw_items.extend(sys.stdin.readlines())

    paths: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        path = normalize_path(raw)
        if path and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def dynamic_test_commands(paths: Iterable[str]) -> tuple[str, ...]:
    commands: list[str] = []
    seen: set[str] = set()
    for path in paths:
        inner = path[4:] if path.startswith("ods/") else path
        command: str | None = None
        quoted_inner = shlex.quote(inner)
        if inner.startswith("tests/"):
            if inner.endswith(".bats"):
                command = f"cd ods && bash tests/run-bats.sh {quoted_inner}"
            elif inner.endswith(".sh"):
                command = f"cd ods && bash {quoted_inner}"
            elif inner.endswith(".ps1"):
                command = f"cd ods && pwsh ./{quoted_inner}"
            elif inner.endswith(".py"):
                command = f"cd ods && python3 -m pytest {quoted_inner} -q"
        elif inner.startswith("extensions/services/dashboard-api/tests/") and inner.endswith(".py"):
            service_rel = inner.removeprefix("extensions/services/dashboard-api/")
            command = f"cd ods/extensions/services/dashboard-api && pytest {shlex.quote(service_rel)} -q"
        elif inner.startswith("extensions/services/dashboard/src/") and ".test." in PurePosixPath(inner).name:
            service_rel = inner.removeprefix("extensions/services/dashboard/")
            command = f"cd ods/extensions/services/dashboard && npm run test -- --run {shlex.quote(service_rel)}"
        if command and command not in seen:
            seen.add(command)
            commands.append(command)
    return tuple(commands)


def recommend(paths: list[str], include_expensive: bool = False) -> dict[str, object]:
    lane_reasons: dict[str, list[str]] = {}
    matched_rules: list[dict[str, str]] = []

    for path in paths:
        for rule in RULES:
            if any(matches(pattern, path) for pattern in rule.patterns):
                matched_rules.append({"path": path, "rule": rule.id, "reason": rule.reason})
                for lane_id in rule.lanes:
                    lane_reasons.setdefault(lane_id, []).append(f"{path}: {rule.reason}")

    if not paths:
        lane_reasons.setdefault("quick-baseline", []).append("No changed paths supplied; use a conservative static baseline or pass paths from git diff.")
    elif not lane_reasons:
        lane_reasons.setdefault("quick-baseline", []).append("No specific rule matched; use a conservative static baseline and inspect changed paths manually.")

    dynamic_commands = dynamic_test_commands(paths)
    lane_objects: list[dict[str, object]] = []
    for lane_id in ORDER:
        if lane_id not in lane_reasons:
            continue
        lane = LANES[lane_id]
        if lane_id == "changed-tests" and dynamic_commands:
            lane = replace(lane, commands=dynamic_commands)
        entry = asdict(lane)
        entry["reasons"] = lane_reasons[lane_id]
        lane_objects.append(entry)

    escalation = [asdict(lane) for lane in ESCALATION_LANES]
    notes = [
        "Commands are recommendations only; review safety before running.",
        "Commands that start with `cd ods &&` assume the outer ODS repository root as the current directory.",
        "Full gate, fleet, post-install, and real-hardware lanes are expensive or host-dependent and are not default checks.",
    ]
    if include_expensive:
        notes.append("--include-expensive was set, so escalation lanes are printed with full commands; still require user intent before host-mutating runs.")

    return {
        "input_paths": paths,
        "matched_rules": matched_rules,
        "recommended_lanes": lane_objects,
        "escalation_lanes": escalation,
        "notes": notes,
    }


def print_lane(lane: dict[str, object], index: int | None = None) -> None:
    prefix = f"{index}. " if index is not None else "- "
    print(f"{prefix}{lane['title']} [{lane['id']}]")
    print(f"   owner: {lane['owner']}")
    print(f"   safety/cost: {lane['safety']} / {lane['cost']}")
    reasons = lane.get("reasons") or []
    if reasons:
        print("   why:")
        for reason in reasons:
            print(f"     - {reason}")
    print("   commands:")
    for command in lane["commands"]:  # type: ignore[index]
        print(f"     {command}")
    notes = lane.get("notes") or []
    if notes:
        print("   notes:")
        for note in notes:
            print(f"     - {note}")
    evidence = lane.get("evidence") or []
    if evidence:
        print("   evidence:")
        for item in evidence:
            print(f"     - {item}")


def print_report(payload: dict[str, object], include_expensive: bool = False) -> None:
    paths = payload["input_paths"]  # type: ignore[index]
    print("ODS validation lane recommendation")
    print("=" * 34)
    if paths:
        print("\nChanged paths:")
        for path in paths:  # type: ignore[assignment]
            print(f"- {path}")
    else:
        print("\nNo changed paths supplied. Example:")
        print("  git diff --name-only main...HEAD | python3 scripts/select_validation_lane.py --stdin")

    print("\nRecommended focused lanes:")
    lanes = payload["recommended_lanes"]  # type: ignore[index]
    for idx, lane in enumerate(lanes, start=1):  # type: ignore[assignment]
        print_lane(lane, idx)

    print("\nEscalation lanes (expensive or host-dependent; not default):")
    for lane in payload["escalation_lanes"]:  # type: ignore[index]
        if include_expensive:
            print_lane(lane)
        else:
            print(f"- {lane['title']} [{lane['id']}]: {lane['safety']} / {lane['cost']}")
            first_command = lane["commands"][0]  # type: ignore[index]
            print(f"  command: {first_command}")

    print("\nNotes:")
    for note in payload["notes"]:  # type: ignore[index]
        print(f"- {note}")


def list_lanes() -> None:
    print("Focused lanes:")
    for lane_id in ORDER:
        lane = LANES[lane_id]
        print_lane(asdict(lane))
    print("\nEscalation lanes:")
    for lane in ESCALATION_LANES:
        print_lane(asdict(lane))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recommend focused ODS validation lanes from changed paths without running tests.",
        epilog="Example: git diff --name-only main...HEAD | python3 select_validation_lane.py --stdin",
    )
    parser.add_argument("paths", nargs="*", help="Changed paths, relative to the outer repo root or inner ods/ root")
    parser.add_argument("--paths-from", action="append", default=[], help="Read changed paths from a file (one per line); may be repeated")
    parser.add_argument("--stdin", action="store_true", help="Read changed paths from stdin")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--include-expensive", action="store_true", help="Print full details for expensive escalation lanes")
    parser.add_argument("--list-lanes", action="store_true", help="List all known lanes and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.list_lanes:
        list_lanes()
        return 0
    paths = collect_paths(args)
    payload = recommend(paths, include_expensive=args.include_expensive)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_report(payload, include_expensive=args.include_expensive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
