#!/usr/bin/env python3
"""Validate Open Wearables frontend metadata and source inventory safely.

The checker is read-only by default: it parses package metadata, expected
frontend source files, runtime-config markers, route/query-key inventories, and
this sub-skill's frontmatter. It does not install packages, call the network, or
write application files.

Examples:
  python check_frontend_metadata.py --repo-root .
  python check_frontend_metadata.py --repo-root . --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


EXPECTED_SCRIPTS = {
    "dev": "vite dev --port 3000",
    "build": "vite build",
    "serve": "vite preview",
    "test": "vitest run",
    "lint": "oxlint -c .oxlintrc.json src",
    "lint:fix": "oxlint -c .oxlintrc.json --fix src",
    "format": 'prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"',
    "format:check": 'prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"',
}

EXPECTED_ENGINES = {"node": ">=22.0.0", "pnpm": ">=10.0.0"}
EXPECTED_PACKAGE_MANAGER_PREFIX = "pnpm@10.13.1"

EXPECTED_ROUTES = [
    "src/routes/__root.tsx",
    "src/routes/_authenticated.tsx",
    "src/routes/_authenticated/dashboard.tsx",
    "src/routes/_authenticated/users.tsx",
    "src/routes/_authenticated/users/index.tsx",
    "src/routes/_authenticated/users/$userId.tsx",
    "src/routes/_authenticated/webhooks.tsx",
    "src/routes/_authenticated/webhooks/index.tsx",
    "src/routes/_authenticated/webhooks/$endpointId.tsx",
    "src/routes/_authenticated/syncs.tsx",
    "src/routes/_authenticated/syncs/index.tsx",
    "src/routes/_authenticated/coverage.tsx",
    "src/routes/_authenticated/settings.tsx",
    "src/routes/login.tsx",
    "src/routes/register.tsx",
    "src/routes/forgot-password.tsx",
    "src/routes/reset-password.tsx",
    "src/routes/accept-invite.tsx",
    "src/routes/index.tsx",
    "src/routes/users/$userId/pair.tsx",
    "src/routes/users/$userId/pair.index.tsx",
    "src/routes/users/$userId/pair.success.tsx",
    "src/routes/users/$userId/pair.error.tsx",
    "src/routes/widget.connect.tsx",
]

EXPECTED_HOOKS = [
    "src/hooks/api/use-api-keys.ts",
    "src/hooks/api/use-applications.ts",
    "src/hooks/api/use-archival.ts",
    "src/hooks/api/use-automations.ts",
    "src/hooks/api/use-config.ts",
    "src/hooks/api/use-coverage.ts",
    "src/hooks/api/use-dashboard.ts",
    "src/hooks/api/use-developers.ts",
    "src/hooks/api/use-health.ts",
    "src/hooks/api/use-invitations.ts",
    "src/hooks/api/use-oauth-providers.ts",
    "src/hooks/api/use-priorities.ts",
    "src/hooks/api/use-seed-data.ts",
    "src/hooks/api/use-sync-status.ts",
    "src/hooks/api/use-users.ts",
    "src/hooks/api/use-webhooks.ts",
]

EXPECTED_SERVICES = [
    "src/lib/api/services/api-keys.service.ts",
    "src/lib/api/services/applications.service.ts",
    "src/lib/api/services/archival.service.ts",
    "src/lib/api/services/auth.service.ts",
    "src/lib/api/services/automations.service.ts",
    "src/lib/api/services/config.service.ts",
    "src/lib/api/services/dashboard.service.ts",
    "src/lib/api/services/developers.service.ts",
    "src/lib/api/services/health.service.ts",
    "src/lib/api/services/invitations.service.ts",
    "src/lib/api/services/meta.service.ts",
    "src/lib/api/services/oauth.service.ts",
    "src/lib/api/services/priority.service.ts",
    "src/lib/api/services/seed-data.service.ts",
    "src/lib/api/services/sync-status.service.ts",
    "src/lib/api/services/users.service.ts",
    "src/lib/api/services/webhooks.service.ts",
]

EXPECTED_CORE_FILES = [
    "src/lib/api/client.ts",
    "src/lib/api/config.ts",
    "src/lib/api/index.ts",
    "src/lib/api/runtime-config.ts",
    "src/lib/api/types.ts",
    "src/lib/auth/session.ts",
    "src/lib/constants/routes.ts",
    "src/lib/query/client.ts",
    "src/lib/query/keys.ts",
    "src/styles.css",
    "src/lib/utils/activity.test.ts",
    "src/lib/utils/format.test.ts",
    "vite.config.ts",
    "tsconfig.json",
]

EXPECTED_ROUTE_CONSTANTS = [
    "login",
    "register",
    "forgotPassword",
    "resetPassword",
    "acceptInvite",
    "dashboard",
    "users",
    "user",
    "webhooks",
    "syncs",
    "settings",
    "coverage",
    "widgetConnect",
]

EXPECTED_QUERY_FAMILIES = [
    "auth",
    "users",
    "dashboard",
    "apiKeys",
    "applications",
    "automations",
    "healthData",
    "health",
    "connections",
    "garmin",
    "requestLogs",
    "chat",
    "oauthProviders",
    "priorities",
    "archival",
    "developers",
    "invitations",
    "seedData",
    "webhooks",
    "meta",
    "config",
    "syncStatus",
]


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def read_text(path: Path, report: Report) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        report.error(f"missing file: {path}")
    except UnicodeDecodeError as exc:
        report.error(f"cannot decode {path}: {exc}")
    return ""


def load_json(path: Path, report: Report) -> dict[str, Any]:
    text = read_text(path, report)
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        report.error(f"invalid JSON in {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        report.error(f"expected object JSON in {path}")
        return {}
    return value


def require_files(base: Path, rel_paths: list[str], label: str, report: Report) -> None:
    missing = [rel for rel in rel_paths if not (base / rel).is_file()]
    if missing:
        report.error(f"missing {label} files: {', '.join(missing)}")
    report.info[f"{label}_expected"] = len(rel_paths)
    report.info[f"{label}_missing"] = missing


def check_package(frontend: Path, report: Report) -> None:
    package = load_json(frontend / "package.json", report)
    if not package:
        return

    report.info["package_name"] = package.get("name")
    report.info["package_version"] = package.get("version")
    report.info["package_manager"] = package.get("packageManager")

    if package.get("name") != "frontend-app":
        report.warn(f"package name changed: {package.get('name')!r}")

    engines = package.get("engines", {})
    for key, expected in EXPECTED_ENGINES.items():
        actual = engines.get(key)
        if actual != expected:
            report.error(f"engine {key} expected {expected!r}, got {actual!r}")

    package_manager = str(package.get("packageManager", ""))
    if not package_manager.startswith(EXPECTED_PACKAGE_MANAGER_PREFIX):
        report.error(
            "packageManager should start with "
            f"{EXPECTED_PACKAGE_MANAGER_PREFIX!r}, got {package_manager!r}"
        )

    scripts = package.get("scripts", {})
    for name, expected in EXPECTED_SCRIPTS.items():
        actual = scripts.get(name)
        if actual != expected:
            report.error(f"script {name!r} expected {expected!r}, got {actual!r}")

    deps = set(package.get("dependencies", {}))
    dev_deps = set(package.get("devDependencies", {}))
    required_deps = {
        "@tanstack/react-router",
        "@tanstack/react-query",
        "@tanstack/react-start",
        "react",
        "react-dom",
        "react-hook-form",
        "zod",
        "tailwindcss",
        "sonner",
    }
    missing_deps = sorted(required_deps - deps)
    if missing_deps:
        report.error(f"missing expected dependencies: {', '.join(missing_deps)}")

    required_dev = {"vitest", "vite", "typescript", "oxlint", "prettier"}
    missing_dev = sorted(required_dev - dev_deps)
    if missing_dev:
        report.error(f"missing expected devDependencies: {', '.join(missing_dev)}")


def check_env(frontend: Path, report: Report) -> None:
    env_text = read_text(frontend / ".env.example", report)
    if not env_text:
        return
    if "VITE_API_URL=http://localhost:8000" not in env_text:
        report.error(".env.example does not define VITE_API_URL=http://localhost:8000")
    if "NODE_ENV=development" not in env_text:
        report.warn(".env.example does not define NODE_ENV=development")


def check_source_markers(frontend: Path, report: Report) -> None:
    require_files(frontend, EXPECTED_ROUTES, "route", report)
    require_files(frontend, EXPECTED_HOOKS, "hook", report)
    require_files(frontend, EXPECTED_SERVICES, "service", report)
    require_files(frontend, EXPECTED_CORE_FILES, "core", report)

    runtime = read_text(frontend / "src/lib/api/runtime-config.ts", report)
    for marker in [
        "window.__APP_CONFIG__",
        "process.env",
        "import.meta.env.VITE_API_URL",
        "http://localhost:8000",
        "runtimeConfigScript",
        "replace(/</g",
    ]:
        if marker not in runtime:
            report.error(f"runtime-config marker missing: {marker}")

    root_route = read_text(frontend / "src/routes/__root.tsx", report)
    for marker in ["QueryClientProvider", "runtimeConfigScript", "Toaster", "Scripts"]:
        if marker not in root_route:
            report.error(f"root route marker missing: {marker}")

    auth_route = read_text(frontend / "src/routes/_authenticated.tsx", report)
    for marker in ["typeof window === 'undefined'", "isAuthenticated", "DEFAULT_REDIRECTS"]:
        if marker not in auth_route:
            report.error(f"authenticated route marker missing: {marker}")

    config = read_text(frontend / "src/lib/api/config.ts", report)
    for marker in ["resolveApiUrl", "API_CONFIG", "API_ENDPOINTS", "syncStatusStream"]:
        if marker not in config:
            report.error(f"API config marker missing: {marker}")

    client = read_text(frontend / "src/lib/api/client.ts", report)
    for marker in ["fetchWithRetry", "Authorization", "Bearer", "status === 401", "fetchRaw", "postMultipart"]:
        if marker not in client:
            report.error(f"apiClient marker missing: {marker}")

    routes = read_text(frontend / "src/lib/constants/routes.ts", report)
    for name in EXPECTED_ROUTE_CONSTANTS:
        if re.search(rf"\b{name}\s*:", routes) is None:
            report.error(f"ROUTES constant missing key: {name}")
    if "DEFAULT_REDIRECTS" not in routes:
        report.error("DEFAULT_REDIRECTS missing from route constants")

    keys = read_text(frontend / "src/lib/query/keys.ts", report)
    for family in EXPECTED_QUERY_FAMILIES:
        if re.search(rf"\b{family}\s*:", keys) is None:
            report.error(f"queryKeys missing family: {family}")

    styles = read_text(frontend / "src/styles.css", report)
    for marker in ["@import 'tailwindcss'", "@theme inline", "@custom-variant dark", "--primary:", "--color-primary"]:
        if marker not in styles:
            report.error(f"styles.css marker missing: {marker}")

    route_count = len(list((frontend / "src/routes").rglob("*.tsx")))
    hook_count = len(list((frontend / "src/hooks/api").glob("*.ts")))
    service_count = len(list((frontend / "src/lib/api/services").glob("*.service.ts")))
    test_count = len(list((frontend / "src").rglob("*.test.ts"))) + len(
        list((frontend / "src").rglob("*.test.tsx"))
    )
    report.info.update(
        {
            "route_files_found": route_count,
            "api_hook_files_found": hook_count,
            "service_files_found": service_count,
            "test_files_found": test_count,
        }
    )


def parse_frontmatter(skill_md: Path, report: Report) -> dict[str, str]:
    text = read_text(skill_md, report)
    if not text:
        return {}
    if not text.startswith("---\n"):
        report.error(f"{skill_md} missing YAML frontmatter start")
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        report.error(f"{skill_md} missing YAML frontmatter end")
        return {}
    front = text[4:end]
    values: dict[str, str] = {}
    for line in front.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
        elif line.strip().startswith("disco-role:"):
            _, value = line.strip().split(":", 1)
            values["metadata.disco-role"] = value.strip()
    desc = values.get("description", "")
    if not (desc.startswith('"') and desc.endswith('"')):
        report.error("SKILL.md description must be double-quoted")
    return values


def check_skill_frontmatter(skill_root: Path, report: Report) -> None:
    skill_md = skill_root / "SKILL.md"
    values = parse_frontmatter(skill_md, report)
    if not values:
        return
    expected = {
        "name": "frontend-portal",
        "disable-model-invocation": "true",
        "metadata.disco-role": "operating",
    }
    for key, expected_value in expected.items():
        actual = values.get(key)
        if actual != expected_value:
            report.error(f"SKILL.md frontmatter {key} expected {expected_value!r}, got {actual!r}")


def run(args: argparse.Namespace) -> Report:
    report = Report()
    repo_root = Path(args.repo_root).expanduser().resolve()
    frontend = repo_root / "frontend"
    skill_root = Path(args.skill_root).expanduser()
    if not skill_root.is_absolute():
        skill_root = (Path.cwd() / skill_root).resolve()

    report.info["repo_root"] = str(repo_root)
    report.info["frontend_root"] = str(frontend)
    report.info["skill_root"] = str(skill_root)

    if not frontend.is_dir():
        report.error(f"frontend directory not found: {frontend}")
        return report

    check_package(frontend, report)
    check_env(frontend, report)
    check_source_markers(frontend, report)
    if not args.skip_skill_frontmatter:
        check_skill_frontmatter(skill_root, report)
    return report


def default_skill_root() -> Path:
    # scripts/check_frontend_metadata.py -> frontend-portal
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only metadata/source checker for the Open Wearables frontend portal."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing the frontend/ directory (default: current directory).",
    )
    parser.add_argument(
        "--skill-root",
        default=str(default_skill_root()),
        help="frontend-portal sub-skill root for SKILL.md frontmatter checks.",
    )
    parser.add_argument(
        "--skip-skill-frontmatter",
        action="store_true",
        help="Skip validation of the generated sub-skill SKILL.md frontmatter.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable output.",
    )
    args = parser.parse_args(argv)

    report = run(args)
    payload = {
        "ok": report.ok,
        "errors": report.errors,
        "warnings": report.warnings,
        "info": report.info,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "OK" if report.ok else "FAILED"
        print(f"frontend metadata check: {status}")
        for key, value in sorted(report.info.items()):
            print(f"info: {key}: {value}")
        for warning in report.warnings:
            print(f"warning: {warning}")
        for error in report.errors:
            print(f"error: {error}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
