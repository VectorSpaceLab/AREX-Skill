#!/usr/bin/env python3
"""Inspect BiSheng frontend package metadata without importing app code.

The helper reads the Platform and Client package.json files, prints scripts and
frontend dependencies, and reports whether the expected two-app stack split is
present. Run from a BiSheng checkout root, or pass --repo-root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

APP_SPECS = {
    "platform": {
        "package_path": Path("src/frontend/platform/package.json"),
        "expected": {
            "vite_major": 5,
            "state": "zustand",
            "query": "react-query",
            "query_major": 3,
            "forbid_query": "@tanstack/react-query",
            "forbid_state": "recoil",
            "react_major": 18,
        },
        "local_probes": {
            "bs-ui": Path("src/frontend/platform/src/components/bs-ui"),
            "request-wrapper": Path("src/frontend/platform/src/controllers/request.ts"),
            "routes": Path("src/frontend/platform/src/routes/index.tsx"),
        },
    },
    "client": {
        "package_path": Path("src/frontend/client/package.json"),
        "expected": {
            "vite_major": 6,
            "state": "recoil",
            "query": "@tanstack/react-query",
            "query_major": 4,
            "forbid_query": "react-query",
            "forbid_state": "zustand",
            "react_major": 18,
        },
        "local_probes": {
            "shadcn-ui-dir": Path("src/frontend/client/src/components/ui"),
            "request-wrapper": Path("src/frontend/client/src/api/request.ts"),
            "routes": Path("src/frontend/client/src/routes/index.tsx"),
        },
    },
}

DISPLAY_DEP_ORDER = [
    "react",
    "react-dom",
    "vite",
    "@vitejs/plugin-react",
    "@vitejs/plugin-react-swc",
    "typescript",
    "react-router-dom",
    "react-query",
    "@tanstack/react-query",
    "zustand",
    "recoil",
    "axios",
    "i18next",
    "react-i18next",
    "i18next-http-backend",
    "i18next-browser-languagedetector",
    "@xyflow/react",
    "bisheng-icons",
    "lucide-react",
    "tailwindcss",
    "vite-plugin-pwa",
    "vitest",
    "jest",
]


def parse_major(version: str | None) -> int | None:
    if not version:
        return None
    match = re.search(r"(\d+)", version)
    return int(match.group(1)) if match else None


def combined_deps(package: Mapping[str, Any]) -> Dict[str, str]:
    deps: Dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        raw = package.get(section, {})
        if isinstance(raw, dict):
            deps.update({str(k): str(v) for k, v in raw.items()})
    return deps


def read_package(repo_root: Path, rel_path: Path) -> Mapping[str, Any]:
    path = repo_root / rel_path
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"missing package file: {rel_path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {rel_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"package file is not a JSON object: {rel_path}")
    return data


def detect_app(repo_root: Path, app_id: str, package: Mapping[str, Any]) -> Dict[str, Any]:
    spec = APP_SPECS[app_id]
    expected = spec["expected"]
    deps = combined_deps(package)
    state_pkg = expected["state"]
    query_pkg = expected["query"]
    forbid_state = expected["forbid_state"]
    forbid_query = expected["forbid_query"]

    vite_version = deps.get("vite")
    react_version = deps.get("react")
    query_version = deps.get(query_pkg)

    checks = {
        "vite_expected_major": parse_major(vite_version) == expected["vite_major"],
        "react_expected_major": parse_major(react_version) == expected["react_major"],
        "state_expected_package": state_pkg in deps,
        "query_expected_package": query_pkg in deps,
        "query_expected_major": parse_major(query_version) == expected["query_major"],
        "forbidden_state_absent": forbid_state not in deps,
        "forbidden_query_absent": forbid_query not in deps,
    }

    probes = {
        name: (repo_root / rel_path).exists()
        for name, rel_path in spec["local_probes"].items()
    }

    return {
        "id": app_id,
        "name": package.get("name"),
        "version": package.get("version"),
        "package_path": str(spec["package_path"]),
        "scripts": package.get("scripts", {}),
        "dependencies": package.get("dependencies", {}),
        "devDependencies": package.get("devDependencies", {}),
        "detected": {
            "react": react_version,
            "vite": vite_version,
            state_pkg: deps.get(state_pkg),
            query_pkg: query_version,
            "axios": deps.get("axios"),
            "react-router-dom": deps.get("react-router-dom"),
            "i18next": deps.get("i18next"),
            "tailwindcss": deps.get("tailwindcss"),
        },
        "checks": checks,
        "local_probes": probes,
        "ok": all(checks.values()) and all(probes.values()),
    }


def print_mapping(title: str, mapping: Mapping[str, Any], names: Iterable[str] | None = None) -> None:
    print(f"  {title}:")
    if not isinstance(mapping, Mapping) or not mapping:
        print("    (none)")
        return
    keys = list(names) if names is not None else sorted(mapping)
    printed = False
    for key in keys:
        if key in mapping:
            print(f"    {key}: {mapping[key]}")
            printed = True
    if names is not None:
        for key in sorted(k for k in mapping if k not in set(keys)):
            print(f"    {key}: {mapping[key]}")
            printed = True
    if not printed:
        print("    (none)")


def print_text(results: Mapping[str, Any], all_deps: bool) -> None:
    print("BiSheng frontend package split")
    print("================================")
    for app_id in ("platform", "client"):
        result = results[app_id]
        status = "OK" if result["ok"] else "CHECK"
        print(f"\n[{app_id}] {status}")
        print(f"  package: {result['package_path']}")
        print(f"  name/version: {result.get('name')} / {result.get('version')}")
        print_mapping("scripts", result["scripts"])
        dep_names = None if all_deps else DISPLAY_DEP_ORDER
        print_mapping("dependencies", result["dependencies"], dep_names)
        print_mapping("devDependencies", result["devDependencies"], dep_names)
        print_mapping("detected stack", result["detected"])
        print_mapping("stack checks", {k: "yes" if v else "NO" for k, v in result["checks"].items()})
        print_mapping("local probes", {k: "yes" if v else "NO" for k, v in result["local_probes"].items()})

    split_ok = results["platform"]["ok"] and results["client"]["ok"]
    print("\nsummary:")
    print(f"  expected two-app stack split detected: {'yes' if split_ok else 'NO'}")
    print("  platform expected: Vite 5 + Zustand + react-query v3 + bs-ui")
    print("  client expected: Vite 6 + Recoil + @tanstack/react-query v4 + shadcn/Radix UI")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect BiSheng frontend package metadata.")
    parser.add_argument("--repo-root", default=".", help="BiSheng repository root; defaults to current directory")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--all-deps", action="store_true", help="print every dependency instead of the curated frontend stack list")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when the expected split is not detected")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    results = {}
    for app_id, spec in APP_SPECS.items():
        package = read_package(repo_root, spec["package_path"])
        results[app_id] = detect_app(repo_root, app_id, package)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(results, all_deps=args.all_deps)

    split_ok = results["platform"]["ok"] and results["client"]["ok"]
    return 0 if split_ok or not args.strict else 1


if __name__ == "__main__":
    sys.exit(main())
