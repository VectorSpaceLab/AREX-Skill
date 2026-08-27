#!/usr/bin/env python3
"""Read-only Open-Assistant checkout stack checker.

This helper validates the repository layout and high-level package/profile facts
used by the generated Open-Assistant skill. It does not start services, install
packages, connect to databases, download models, or mutate files.

Examples:
  python scripts/check_open_assistant_stack.py --repo-root /path/to/Open-Assistant
  python scripts/check_open_assistant_stack.py --repo-root /path/to/Open-Assistant --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_PATHS = [
    "README.md",
    "docker-compose.yaml",
    "pyproject.toml",
    "backend/main.py",
    "backend/oasst_backend/api/v1/api.py",
    "backend/oasst_backend/config.py",
    "backend/requirements.txt",
    "oasst-shared/pyproject.toml",
    "oasst-shared/oasst_shared/api_client.py",
    "oasst-shared/oasst_shared/schemas/protocol.py",
    "oasst-shared/oasst_shared/schemas/inference.py",
    "oasst-shared/oasst_shared/model_configs.py",
    "oasst-data/pyproject.toml",
    "oasst-data/oasst_data/schemas.py",
    "oasst-data/oasst_data/reader.py",
    "oasst-data/oasst_data/writer.py",
    "website/package.json",
    "website/src/lib/oasst_api_client.ts",
    "website/src/components/Tasks/TaskTypes.tsx",
    "website/src/components/Chat/ChatForm.tsx",
    "inference/server/main.py",
    "inference/server/oasst_inference_server/routes/chats.py",
    "inference/server/oasst_inference_server/routes/workers.py",
    "inference/worker/__main__.py",
    "inference/worker/settings.py",
    "inference/text-client/__main__.py",
]

OPTIONAL_OR_EXCLUDED_PATHS = [
    "model/",
    "deploy/",
    "ansible/",
    "notebooks/",
    "docs/",
    "scripts/backend-development/",
    "scripts/frontend-development/",
    "scripts/oasst-shared-development/",
]

EXPECTED_COMPOSE_PROFILES = {
    "backend-dev",
    "frontend-dev",
    "ci",
    "inference",
    "inference-dev",
    "inference-safety",
    "observability",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Open-Assistant layout and high-level stack facts safely.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Path to an Open-Assistant repository checkout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when optional evidence directories selected by this skill are missing.",
    )
    return parser.parse_args()


def read_text(path: Path, max_chars: int = 500_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except FileNotFoundError:
        return ""


def parse_project_metadata(pyproject: Path) -> dict[str, Any]:
    text = read_text(pyproject)
    result: dict[str, Any] = {"exists": pyproject.exists()}
    for key in ("name", "version", "description"):
        match = re.search(rf'^\s*{key}\s*=\s*["\']([^"\']+)["\']', text, flags=re.MULTILINE)
        if match:
            result[key] = match.group(1)
    deps_match = re.search(r"^\s*dependencies\s*=\s*\[(.*?)\]", text, flags=re.MULTILINE | re.DOTALL)
    if deps_match:
        result["dependency_count"] = len(re.findall(r"[\"']([^\"']+)[\"']", deps_match.group(1)))
    return result


def parse_website_package(package_json: Path) -> dict[str, Any]:
    if not package_json.exists():
        return {"exists": False}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - diagnostics should include parse class
        return {"exists": True, "error": f"{type(exc).__name__}: {exc}"}
    scripts = data.get("scripts") or {}
    wanted = [
        "dev",
        "build",
        "lint",
        "typecheck",
        "jest",
        "cypress:run",
        "cypress:run:contract",
        "cypress:component",
        "build-storybook",
        "inlang:lint",
    ]
    return {
        "exists": True,
        "name": data.get("name"),
        "version": data.get("version"),
        "scripts_present": [name for name in wanted if name in scripts],
        "scripts_missing": [name for name in wanted if name not in scripts],
    }


def parse_compose_profiles(compose_file: Path) -> dict[str, Any]:
    text = read_text(compose_file)
    found = set(re.findall(r"profiles:\s*\[([^\]]+)\]", text))
    profiles: set[str] = set()
    for group in found:
        profiles.update(part.strip().strip('"\'') for part in group.split(",") if part.strip())
    return {
        "exists": compose_file.exists(),
        "profiles": sorted(profiles),
        "expected_present": sorted(EXPECTED_COMPOSE_PROFILES & profiles),
        "expected_missing": sorted(EXPECTED_COMPOSE_PROFILES - profiles),
    }


def classify_layout(repo_root: Path) -> dict[str, Any]:
    required = {rel: (repo_root / rel).exists() for rel in REQUIRED_PATHS}
    optional = {rel: (repo_root / rel).exists() for rel in OPTIONAL_OR_EXCLUDED_PATHS}
    subskill_routes = {
        "backend": [rel for rel in REQUIRED_PATHS if rel.startswith(("backend/", "oasst-shared/", "oasst-data/"))],
        "website": [rel for rel in REQUIRED_PATHS if rel.startswith("website/")],
        "inference": [rel for rel in REQUIRED_PATHS if rel.startswith("inference/")],
    }
    return {
        "required_paths": required,
        "missing_required_paths": [rel for rel, ok in required.items() if not ok],
        "optional_or_excluded_paths": optional,
        "subskill_route_evidence": subskill_routes,
    }


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    return {
        "schema": "open-assistant.stack-check.v1",
        "repo_root_exists": repo_root.is_dir(),
        "layout": classify_layout(repo_root),
        "packages": {
            "oasst_shared": parse_project_metadata(repo_root / "oasst-shared" / "pyproject.toml"),
            "oasst_data": parse_project_metadata(repo_root / "oasst-data" / "pyproject.toml"),
            "website": parse_website_package(repo_root / "website" / "package.json"),
        },
        "docker_compose": parse_compose_profiles(repo_root / "docker-compose.yaml"),
        "notes": [
            "This checker is read-only and does not install dependencies or start Docker services.",
            "Route backend/API/data questions to sub-skills/backend, website questions to sub-skills/website, and inference questions to sub-skills/inference.",
            "model/ training and deployment/infrastructure are intentionally outside this generated skill scope.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    print("Open-Assistant stack layout check")
    print(f"repo root exists: {report['repo_root_exists']}")
    missing = report["layout"]["missing_required_paths"]
    if missing:
        print("missing required paths:")
        for rel in missing:
            print(f"- {rel}")
    else:
        print("required path check: OK")

    print("compose profiles:")
    for profile in report["docker_compose"]["profiles"]:
        print(f"- {profile}")
    if report["docker_compose"]["expected_missing"]:
        print("missing expected compose profiles:")
        for profile in report["docker_compose"]["expected_missing"]:
            print(f"- {profile}")

    print("package/workspace facts:")
    for name, facts in report["packages"].items():
        print(f"- {name}: {facts}")

    print("route evidence:")
    for route, paths in report["layout"]["subskill_route_evidence"].items():
        present = sum(1 for rel in paths if report["layout"]["required_paths"].get(rel))
        print(f"- {route}: {present}/{len(paths)} expected evidence paths present")

    for note in report["notes"]:
        print(f"note: {note}")


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    missing_required = bool(report["layout"]["missing_required_paths"])
    missing_optional = any(not ok for ok in report["layout"]["optional_or_excluded_paths"].values())
    if not report["repo_root_exists"] or missing_required or (args.strict and missing_optional):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
