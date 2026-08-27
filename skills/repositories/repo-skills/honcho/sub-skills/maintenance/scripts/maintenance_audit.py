#!/usr/bin/env python3
"""Non-mutating Honcho maintenance audit.

Run from or point at a Honcho checkout root. The audit checks that key
maintenance guardrails are present; it does not import Honcho or execute the
repo's tests/scripts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Finding:
    level: str
    message: str


class Audit:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.findings: list[Finding] = []

    def ok(self, message: str) -> None:
        self.findings.append(Finding("OK", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    def fail(self, message: str) -> None:
        self.findings.append(Finding("FAIL", message))

    def path(self, rel: str) -> Path:
        return self.root / rel

    def read_text(self, rel: str) -> str:
        try:
            return self.path(rel).read_text(encoding="utf-8")
        except FileNotFoundError:
            self.fail(f"missing required file: {rel}")
            return ""

    def require_file(self, rel: str) -> bool:
        if self.path(rel).is_file():
            self.ok(f"found {rel}")
            return True
        self.fail(f"missing required file: {rel}")
        return False

    def require_dir(self, rel: str) -> bool:
        if self.path(rel).is_dir():
            self.ok(f"found {rel}/")
            return True
        self.fail(f"missing required directory: {rel}/")
        return False

    def require_contains(
        self, rel: str, needle: str, description: str, *, regex: bool = False
    ) -> None:
        text = self.read_text(rel)
        if not text:
            return
        matched = re.search(needle, text, flags=re.MULTILINE) if regex else needle in text
        if matched:
            self.ok(description)
        else:
            self.fail(f"{description} not found in {rel}")

    def warn_contains(
        self, rel: str, needle: str, description: str, *, regex: bool = False
    ) -> None:
        text = self.read_text(rel)
        if not text:
            return
        matched = re.search(needle, text, flags=re.MULTILINE) if regex else needle in text
        if matched:
            self.ok(description)
        else:
            self.warn(f"{description} not found in {rel}")

    def audit_required_files(self) -> None:
        for rel in [
            "pyproject.toml",
            ".pre-commit-config.yaml",
            "tests/conftest.py",
            "tests/routes/test_auth_route_policy.py",
            "tests/sdk_typescript/test_sdk.py",
            "tests/llm/test_model_config.py",
            "tests/llm/test_tool_loop_truncation.py",
            "tests/dialectic/test_model_config_usage.py",
            "scripts/ensure_alembic_tests.py",
            "scripts/run_alembic_tests.py",
            "scripts/update_version.py",
            "sdks/typescript/package.json",
            "sdks/python/pyproject.toml",
        ]:
            self.require_file(rel)
        for rel in ["src", "tests", "migrations/versions", "tests/alembic/revisions"]:
            self.require_dir(rel)

    def audit_pyproject(self) -> None:
        text = self.read_text("pyproject.toml")
        if not text:
            return
        checks = [
            ("name = \"honcho\"", "root package is Honcho"),
            ("uv run", "pyproject should not contain uv run"),
        ]
        if checks[0][0] in text:
            self.ok(checks[0][1])
        else:
            self.fail("root package name is not recognizably Honcho")
        if "--ignore=tests/alembic" in text and "-n auto" in text:
            self.ok("pytest addopts keep xdist auto and exclude alembic by default")
        else:
            self.fail("pytest addopts should include -n auto and --ignore=tests/alembic")
        if "live_llm:" in text and "--live-llm" not in text:
            self.ok("live_llm marker is declared without forcing live tests")
        elif "live_llm:" in text:
            self.ok("live_llm marker is declared")
        else:
            self.warn("live_llm marker not found in pytest markers")
        for token in ["ruff", "basedpyright", "src", "tests", "sdks/python/src"]:
            if token in text:
                self.ok(f"pyproject mentions {token}")
            else:
                self.warn(f"pyproject does not mention {token}")

    def audit_precommit(self) -> None:
        text = self.read_text(".pre-commit-config.yaml")
        if not text:
            return
        for token, desc in [
            ("uv run basedpyright", "pre-commit typecheck uses uv run basedpyright"),
            ("uv run pytest -x tests/ --ignore=tests/alembic/", "pre-push main pytest excludes alembic"),
            ("scripts/run_alembic_tests.py", "pre-commit runs selective alembic tests"),
            ("scripts/ensure_alembic_tests.py", "pre-commit enforces alembic test coverage"),
            ("bun run typecheck", "pre-commit typechecks TypeScript SDK"),
            ("bun run build", "pre-commit builds TypeScript SDK"),
        ]:
            if token in text:
                self.ok(desc)
            else:
                self.warn(f"{desc} not found")

    def audit_typescript_sdk_guard(self) -> None:
        rel = "sdks/typescript/package.json"
        try:
            data = json.loads(self.path(rel).read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.fail(f"missing required file: {rel}")
            return
        except json.JSONDecodeError as exc:
            self.fail(f"{rel} is not valid JSON: {exc}")
            return
        scripts = data.get("scripts", {})
        test_script = str(scripts.get("test", ""))
        if "pytest" in test_script and "exit 1" in test_script:
            self.ok("TypeScript SDK direct bun test guard redirects to pytest")
        else:
            self.fail("TypeScript SDK test script should fail and direct users to pytest")
        for name in ["typecheck", "build", "lint:fix"]:
            if name in scripts:
                self.ok(f"TypeScript SDK has {name} script")
            else:
                self.warn(f"TypeScript SDK missing {name} script")

    def audit_auth_policy_test(self) -> None:
        rel = "tests/routes/test_auth_route_policy.py"
        text = self.read_text(rel)
        if not text:
            return
        required_tokens = [
            ("EXPECTED_MEMBER_READ_ROUTES", "explicit member-read allowlist exists"),
            ("allow_member_read", "auth dependency marker is inspected"),
            ("MUTATING_METHODS", "mutating method guard exists"),
            ("test_every_message_route_requires_auth", "messages route auth coverage exists"),
            ("POST is intentionally excluded", "POST is documented as not a write signal"),
        ]
        for token, desc in required_tokens:
            if token in text:
                self.ok(desc)
            else:
                self.fail(f"{desc} not found")
        if re.search(r'MUTATING_METHODS\s*=\s*\{\s*"PUT",\s*"PATCH",\s*"DELETE"\s*\}', text):
            self.ok("mutating method set is PUT/PATCH/DELETE")
        else:
            self.warn("mutating method set changed; verify POST read-route rationale")

    def audit_llm_regression_anchors(self) -> None:
        model_rel = "tests/llm/test_model_config.py"
        model_text = self.read_text(model_rel)
        if model_text:
            for token, desc in [
                ("test_fallback_config_is_independent", "fallback independence regression test exists"),
                ("structured_output_mode is only supported", "structured output transport validation exists"),
                ("test_config_toml_example_uses_nested_model_config_sections", "config.toml nested model-config sync test exists"),
                ("test_env_template_uses_nested_model_config_keys", "env template nested model-config sync test exists"),
                ("test_dialectic_settings_backfills_missing_levels", "dialectic level backfill regression exists"),
            ]:
                if token in model_text:
                    self.ok(desc)
                else:
                    self.warn(f"{desc} not found")
        trunc_rel = "tests/llm/test_tool_loop_truncation.py"
        trunc_text = self.read_text(trunc_rel)
        if trunc_text:
            if "hit_input_token_cap" in trunc_text and "single-message over-cap" in trunc_text:
                self.ok("tool-loop truncation tests cover token cap and oversized single message")
            else:
                self.warn("tool-loop truncation token-cap regression anchors may be missing")
        dialectic_rel = "tests/dialectic/test_model_config_usage.py"
        dialectic_text = self.read_text(dialectic_rel)
        if dialectic_text:
            if "settings.DIALECTIC.LEVELS" in dialectic_text and "model_config" in dialectic_text:
                self.ok("dialectic model-config usage tests inspect per-level config")
            else:
                self.warn("dialectic model-config usage test anchor may be missing")

    def audit_scripts(self) -> None:
        self.require_contains(
            "scripts/ensure_alembic_tests.py",
            "actively used within our precommit hooks",
            "ensure_alembic_tests documents pre-commit coupling",
        )
        self.require_contains(
            "scripts/run_alembic_tests.py",
            '"-n0"',
            "run_alembic_tests disables xdist for pipeline runs",
        )
        update = self.read_text("scripts/update_version.py")
        if update:
            for token in [
                "--api-version",
                "--python-version",
                "--typescript-version",
                "--api-changelog",
                "--python-changelog",
                "--typescript-changelog",
                "--yes",
            ]:
                if token in update:
                    self.ok(f"update_version supports {token}")
                else:
                    self.warn(f"update_version missing expected flag {token}")

    def audit_versions(self) -> None:
        roots = {
            "api": "pyproject.toml",
            "python_sdk": "sdks/python/pyproject.toml",
        }
        versions: dict[str, str] = {}
        for key, rel in roots.items():
            text = self.read_text(rel)
            match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
            if match:
                versions[key] = match.group(1)
                self.ok(f"read {key} version {versions[key]}")
            else:
                self.warn(f"could not read {key} version from {rel}")
        try:
            data = json.loads(self.path("sdks/typescript/package.json").read_text(encoding="utf-8"))
            version = str(data.get("version", ""))
            if version:
                versions["typescript_sdk"] = version
                self.ok(f"read typescript_sdk version {version}")
            else:
                self.warn("could not read TypeScript SDK version")
        except Exception as exc:  # noqa: BLE001 - report audit failure without crashing
            self.warn(f"could not read TypeScript SDK version: {exc}")
        if len(versions) >= 2 and len(set(versions.values())) > 1:
            self.ok("component versions differ; this is allowed when release plan says so")

    def audit_migration_coverage(self) -> None:
        migrations_dir = self.path("migrations/versions")
        tests_dir = self.path("tests/alembic/revisions")
        if not migrations_dir.is_dir() or not tests_dir.is_dir():
            self.fail("migration and alembic revision-test directories are required")
            return
        migration_basenames = {
            p.stem for p in migrations_dir.glob("*.py") if p.name != "__init__.py"
        }
        test_targets = {
            p.stem.removeprefix("test_")
            for p in tests_dir.glob("test_*.py")
            if p.name != "__init__.py"
        }
        missing = sorted(migration_basenames - test_targets)
        stale = sorted(test_targets - migration_basenames)
        if missing:
            self.fail(
                "missing Alembic revision tests: "
                + ", ".join(f"tests/alembic/revisions/test_{name}.py" for name in missing)
            )
        else:
            self.ok(f"all {len(migration_basenames)} migration revisions have tests")
        if stale:
            self.warn("stale Alembic tests without migration files: " + ", ".join(stale))

    def run(self) -> int:
        self.audit_required_files()
        self.audit_pyproject()
        self.audit_precommit()
        self.audit_typescript_sdk_guard()
        self.audit_auth_policy_test()
        self.audit_llm_regression_anchors()
        self.audit_scripts()
        self.audit_versions()
        self.audit_migration_coverage()
        return 1 if any(f.level == "FAIL" for f in self.findings) else 0

    def print_report(self, *, only_problem: bool = False) -> None:
        levels = ["FAIL", "WARN", "OK"]
        for level in levels:
            items = [f for f in self.findings if f.level == level]
            if only_problem and level == "OK":
                continue
            if not items:
                continue
            print(f"\n{level} ({len(items)})")
            print("-" * (len(level) + 4 + len(str(len(items)))))
            for item in items:
                print(f"[{item.level}] {item.message}")


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Honcho checkout root to audit (default: current directory).",
    )
    parser.add_argument(
        "--problems-only",
        action="store_true",
        help="Print only FAIL/WARN findings.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root)
    audit = Audit(root)
    print(f"Honcho maintenance audit root: {root.resolve()}")
    exit_code = audit.run()
    audit.print_report(only_problem=args.problems_only)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
