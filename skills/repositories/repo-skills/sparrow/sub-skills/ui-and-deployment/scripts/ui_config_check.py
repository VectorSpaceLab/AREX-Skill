#!/usr/bin/env python3
"""Validate Sparrow Next UI package metadata without installing npm packages.

The checker is intentionally static: it parses package.json and compares scripts,
runtime dependencies, development dependencies, and selected allowScripts entries
against the expectations embedded in this generated skill.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

EXPECTED_SCRIPTS: dict[str, str] = {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
}

REQUIRED_RUNTIME_DEPS: dict[str, str] = {
    "next": "Next app router, server routes, and build/start commands",
    "react": "process, dashboard, and feedback UI components",
    "react-dom": "React DOM runtime for Next",
    "pdfjs-dist": "client-side PDF page-count detection before protected-access checks",
    "oracledb": "optional Oracle-backed dashboard, feedback, and Sparrow key flows",
    "maxmind": "optional GeoIP country lookup for logging/dashboard context",
    "undici": "extended-timeout fetch dispatcher for long backend inference calls",
    "react-markdown": "render result summaries in the process page",
    "recharts": "dashboard chart rendering",
}

RECOMMENDED_RUNTIME_DEPS: dict[str, str] = {
    "lucide-react": "icon components used by the UI dependency set",
    "next-themes": "theme support in the dependency set",
    "react-dropzone": "upload/dropzone dependency present in the UI package metadata",
    "react-syntax-highlighter": "syntax-highlight dependency present for response rendering",
    "tailwind-merge": "class merge helper used by UI utility patterns",
}

REQUIRED_DEV_DEPS: dict[str, str] = {
    "eslint": "lint script executable",
    "eslint-config-next": "Next lint rules",
    "typescript": "TypeScript compile/build support",
    "@types/node": "Node type declarations",
    "@types/react": "React type declarations",
    "@types/react-dom": "React DOM type declarations",
}

RECOMMENDED_ALLOW_SCRIPTS: dict[str, str] = {
    "oracledb": "native/binary setup for Oracle driver in package-manager policies",
    "sharp": "Next image optimization dependency often gated by package-manager policies",
}


def load_package(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"ERROR: package file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: top-level package JSON must be an object: {path}")
    return data


def as_mapping(obj: Any, field: str) -> Mapping[str, Any]:
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        raise SystemExit(f"ERROR: package field {field!r} must be an object when present")
    return obj


def collect_dependency_versions(pkg: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    """Return dependency name -> (group, version) across package groups."""
    result: dict[str, tuple[str, str]] = {}
    for group in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        deps = as_mapping(pkg.get(group), group)
        for name, version in deps.items():
            result[str(name)] = (group, str(version))
    return result


def check_package(pkg: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    scripts = as_mapping(pkg.get("scripts"), "scripts")
    for name, expected in EXPECTED_SCRIPTS.items():
        actual = scripts.get(name)
        if actual is None:
            errors.append(f"missing script {name!r}; expected {expected!r}")
        elif str(actual).strip() != expected:
            warnings.append(f"script {name!r} is {actual!r}; expected {expected!r}")
        else:
            info.append(f"script {name}: {expected}")

    deps = collect_dependency_versions(pkg)
    runtime_deps = as_mapping(pkg.get("dependencies"), "dependencies")
    dev_deps = as_mapping(pkg.get("devDependencies"), "devDependencies")

    for name, why in REQUIRED_RUNTIME_DEPS.items():
        if name not in runtime_deps:
            errors.append(f"missing runtime dependency {name!r}: {why}")
        else:
            info.append(f"runtime dependency {name}: {runtime_deps[name]}")

    for name, why in RECOMMENDED_RUNTIME_DEPS.items():
        if name not in deps:
            warnings.append(f"recommended dependency {name!r} not found: {why}")
        else:
            group, version = deps[name]
            info.append(f"recommended dependency {name}: {version} ({group})")

    for name, why in REQUIRED_DEV_DEPS.items():
        if name not in dev_deps:
            errors.append(f"missing dev dependency {name!r}: {why}")
        else:
            info.append(f"dev dependency {name}: {dev_deps[name]}")

    allow_scripts = as_mapping(pkg.get("allowScripts"), "allowScripts")
    for stem, why in RECOMMENDED_ALLOW_SCRIPTS.items():
        present = any(str(key).split("@", 1)[0] == stem for key in allow_scripts)
        if not present:
            warnings.append(f"allowScripts has no entry for {stem!r}: {why}")
        else:
            info.append(f"allowScripts includes {stem}")

    if pkg.get("private") is not True:
        warnings.append("package is not marked private=true; verify publication policy before deployment")

    return errors, warnings, info


def embedded_summary() -> dict[str, Any]:
    return {
        "scripts": EXPECTED_SCRIPTS,
        "requiredRuntimeDependencies": REQUIRED_RUNTIME_DEPS,
        "recommendedRuntimeDependencies": RECOMMENDED_RUNTIME_DEPS,
        "requiredDevDependencies": REQUIRED_DEV_DEPS,
        "recommendedAllowScripts": RECOMMENDED_ALLOW_SCRIPTS,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static Sparrow Next UI package metadata checker; does not install npm packages."
    )
    parser.add_argument(
        "--package-json",
        type=Path,
        help="Path to package.json to validate. If omitted, use --embedded to print expectations.",
    )
    parser.add_argument(
        "--embedded",
        action="store_true",
        help="Print embedded expected scripts/dependencies and exit successfully.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON result.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress OK/info lines in text output.",
    )
    args = parser.parse_args(argv)

    if args.embedded or not args.package_json:
        summary = embedded_summary()
        if args.json:
            print(json.dumps({"status": "embedded", "expectations": summary}, indent=2, sort_keys=True))
        else:
            print("Embedded Sparrow Next UI package expectations:")
            print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    pkg = load_package(args.package_json)
    errors, warnings, info = check_package(pkg)
    status = "ok" if not errors else "failed"

    if args.json:
        print(json.dumps({"status": status, "errors": errors, "warnings": warnings, "info": info}, indent=2, sort_keys=True))
    else:
        print(f"Sparrow Next UI package check: {status.upper()}")
        if not args.quiet:
            for line in info:
                print(f"OK: {line}")
        for line in warnings:
            print(f"WARN: {line}")
        for line in errors:
            print(f"ERROR: {line}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
