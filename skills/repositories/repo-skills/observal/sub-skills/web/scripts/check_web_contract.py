#!/usr/bin/env python3
"""Static contract check for the Observal web sub-skill.

This helper is intentionally read-only and dependency-free. It validates a
small set of frontend contracts that the web sub-skill depends on:
package scripts, route files, hook barrels, harness query helpers, and the
OKLCH token stylesheet.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_PACKAGE_SCRIPTS = {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "lint": "eslint",
    "typecheck": "tsc --noEmit",
    "e2e": "playwright test",
    "e2e:kiro": "playwright test --grep kiro",
    "e2e:ui": "playwright test --ui",
}

EXPECTED_ROUTE_FILES = {
    "web/src/routes/__root.tsx": ["createRootRoute", "QueryClientProvider", "ThemeProvider"],
    "web/src/routes/_authed.tsx": ["createFileRoute", "AuthGuard", "RegistrySidebar"],
    "web/src/routes/(auth)/login.tsx": ["createFileRoute"],
    "web/src/routes/(auth)/register.tsx": ["createFileRoute"],
    "web/src/routes/(auth)/device.tsx": ["createFileRoute"],
    "web/src/routes/_authed/index.tsx": ["createFileRoute"],
    "web/src/routes/_authed/leaderboard.tsx": ["createFileRoute"],
    "web/src/routes/_authed/components/index.tsx": ["createFileRoute"],
    "web/src/routes/_authed/agents/index.tsx": ["createFileRoute"],
    "web/src/routes/_authed/agents/builder.tsx": ["createFileRoute"],
    "web/src/routes/_authed/_admin/review.tsx": ["createFileRoute"],
    "web/src/routes/_authed/_admin/dashboard.tsx": ["createFileRoute"],
    "web/src/routes/_authed/_user/traces/index.tsx": ["createFileRoute"],
    "web/src/routes/_authed/_user/traces/$traceId.tsx": ["createFileRoute"],
    "web/src/routes/_authed/insights/$reportId.tsx": ["createFileRoute"],
}

EXPECTED_USE_API_EXPORTS = [
    'export * from "./use-dashboard-api";',
    'export * from "./use-traces-api";',
    'export * from "./use-review-api";',
    'export * from "./use-insights-api";',
    'export * from "./use-admin-api";',
    'export * from "./use-sessions-api";',
    'export * from "./use-agents-api";',
    'export * from "./use-registry-api";',
    'export * from "./use-user-search";',
    'export * from "./use-teams-api";',
]

EXPECTED_HARNESS_SNIPPETS = [
    'queryKey: ["config", "harnesses"]',
    'config.harnesses',
    'defaultHarness',
]

EXPECTED_API_SNIPPETS = [
    'const API = "/api/v1";',
    'const STORAGE_KEY_ACCESS_TOKEN = "observal_access_token";',
    'const STORAGE_KEY_REFRESH_TOKEN = "observal_refresh_token";',
    'harnesses: () => get<HarnessesResponse>("/config/harnesses")',
]

EXPECTED_APP_CSS_SNIPPETS = [
    '@theme inline',
    'oklch(var(--bg))',
    '--color-background:',
    '--color-foreground:',
    '--color-card:',
    '--color-border:',
    '--color-primary:',
    '--color-destructive:',
    '--color-success:',
    '--color-warning:',
    '--color-info:',
    '.dark {',
    '.midnight {',
    '.forest {',
    '.sunset {',
    '.solarized-dark {',
    '.solarized-light {',
    '.dracula {',
    '.nord {',
    '.monokai {',
    '.gruvbox {',
    '.catppuccin {',
    '.tokyo-night {',
    '.one-dark {',
    '.rose-pine {',
]

EXPECTED_VITE_SNIPPETS = [
    'TanStackRouterVite({ routesDirectory: "./src/routes" })',
    'alias: {',
    '"@": resolve(__dirname, "src")',
    'port: 3000',
    '"/api": {',
    '"/health": {',
]


@dataclass
class CheckResult:
    ok: bool
    label: str
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def check_contains(text: str, snippets: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for snippet in snippets:
        if snippet not in text:
            missing.append(snippet)
    return missing


def record(results: list[CheckResult], ok: bool, label: str, detail: str) -> None:
    results.append(CheckResult(ok=ok, label=label, detail=detail))


def check_package_json(root: Path, results: list[CheckResult]) -> None:
    pkg_path = root / "web" / "package.json"
    if not pkg_path.is_file():
        record(results, False, "web/package.json", "missing")
        return

    try:
        pkg = read_json(pkg_path)
    except json.JSONDecodeError as exc:
        record(results, False, "web/package.json", f"invalid JSON: {exc}")
        return

    if pkg.get("name") != "web":
        record(results, False, "web/package.json", f'name is {pkg.get("name")!r}, expected "web"')
    else:
        record(results, True, "web/package.json", 'package name is "web"')

    scripts = pkg.get("scripts", {})
    missing = []
    mismatched = []
    for key, expected in EXPECTED_PACKAGE_SCRIPTS.items():
        actual = scripts.get(key)
        if actual is None:
            missing.append(key)
        elif actual != expected:
            mismatched.append(f"{key}={actual!r}")
    if missing or mismatched:
        detail_parts = []
        if missing:
            detail_parts.append(f"missing scripts: {', '.join(missing)}")
        if mismatched:
            detail_parts.append(f"mismatched scripts: {', '.join(mismatched)}")
        record(results, False, "web/package.json scripts", "; ".join(detail_parts))
    else:
        record(results, True, "web/package.json scripts", "expected frontend scripts present")

    if pkg.get("packageManager") != "pnpm@10.34.4":
        record(results, False, "web/package.json packageManager", f'expected "pnpm@10.34.4", found {pkg.get("packageManager")!r}')
    else:
        record(results, True, "web/package.json packageManager", 'pnpm workspace version matches')


def check_file_snippets(results: list[CheckResult], path: Path, snippets: list[str], label: str | None = None) -> None:
    label = label or str(path)
    if not path.is_file():
        record(results, False, label, "missing")
        return
    text = read_text(path)
    missing = check_contains(text, snippets)
    if missing:
        record(results, False, label, f"missing snippets: {', '.join(missing)}")
    else:
        record(results, True, label, "expected markers present")


def check_expected_files(root: Path, results: list[CheckResult]) -> None:
    for rel, snippets in EXPECTED_ROUTE_FILES.items():
        check_file_snippets(results, root / rel, snippets, rel)

    check_file_snippets(results, root / "web" / "src" / "hooks" / "use-api.ts", EXPECTED_USE_API_EXPORTS, "web/src/hooks/use-api.ts")
    check_file_snippets(results, root / "web" / "src" / "hooks" / "use-harnesses.ts", EXPECTED_HARNESS_SNIPPETS, "web/src/hooks/use-harnesses.ts")
    check_file_snippets(results, root / "web" / "src" / "lib" / "api.ts", EXPECTED_API_SNIPPETS, "web/src/lib/api.ts")
    check_file_snippets(results, root / "web" / "src" / "lib" / "types.ts", [
        'export * from "./types/dashboard";',
        'export * from "./types/sessions";',
        'export * from "./types/registry";',
        'export * from "./types/admin";',
        'export * from "./types/team";',
        'export * from "./types/inbox";',
    ], "web/src/lib/types.ts")
    check_file_snippets(results, root / "web" / "src" / "lib" / "theme.tsx", ["observal-theme", "ThemeProvider"], "web/src/lib/theme.tsx")
    check_file_snippets(results, root / "web" / "src" / "app.css", EXPECTED_APP_CSS_SNIPPETS, "web/src/app.css")
    check_file_snippets(results, root / "web" / "vite.config.ts", EXPECTED_VITE_SNIPPETS, "web/vite.config.ts")
    check_file_snippets(results, root / "web" / "src" / "main.tsx", ["routeTree.gen", "RouterProvider"], "web/src/main.tsx")


def print_result(result: CheckResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"{status} {result.label}: {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Observal web frontend contract.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Path to the Observal repository root")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    results: list[CheckResult] = []

    if not root.exists():
        print(f"FAIL repo root: {root} does not exist")
        return 1

    check_package_json(root, results)
    check_expected_files(root, results)

    failures = [result for result in results if not result.ok]
    for result in results:
        print_result(result)

    if failures:
        print(f"\nSUMMARY: {len(failures)} checks failed")
        return 1

    print(f"\nSUMMARY: {len(results)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
