#!/usr/bin/env python3
"""Safely summarize a SuperAGI checkout using static file inspection.

This helper does not import SuperAGI, start services, read secrets, run Docker,
or contact providers. It accepts an explicit checkout path from the downstream
user and reports which expected runtime surfaces are present.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED = {
    "source_root": ["superagi/__init__.py"],
    "api_entry": ["main.py"],
    "config": ["config_template.yaml"],
    "docker": ["Dockerfile", "docker-compose.yaml", "docker-compose-gpu.yml"],
    "worker": ["superagi/worker.py", "entrypoint_celery.sh"],
    "gui": ["gui/package.json", "nginx/default.conf"],
    "tests": ["tests/unit_tests", "tests/integration_tests"],
}


def count_files(root: Path, subdir: str, pattern: str = "*.py") -> int:
    base = root / subdir
    if not base.exists():
        return 0
    return sum(1 for _ in base.rglob(pattern))


def main() -> int:
    parser = argparse.ArgumentParser(description="Static SuperAGI checkout summary")
    parser.add_argument("--repo-root", default=".", help="Path to a SuperAGI checkout")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()

    summary = {
        "repo_root": str(root),
        "is_probable_superagi": False,
        "expected_paths": {},
        "counts": {},
        "warnings": [],
    }
    for group, paths in EXPECTED.items():
        summary["expected_paths"][group] = {p: (root / p).exists() for p in paths}
    summary["counts"] = {
        "controllers_py": count_files(root, "superagi/controllers"),
        "models_py": count_files(root, "superagi/models"),
        "agent_py": count_files(root, "superagi/agent"),
        "tools_py": count_files(root, "superagi/tools"),
        "unit_tests_py": count_files(root, "tests/unit_tests"),
    }
    required = [
        summary["expected_paths"]["source_root"].get("superagi/__init__.py"),
        summary["expected_paths"]["api_entry"].get("main.py"),
        summary["expected_paths"]["config"].get("config_template.yaml"),
    ]
    summary["is_probable_superagi"] = all(required)
    if not summary["is_probable_superagi"]:
        summary["warnings"].append("missing one or more core SuperAGI markers: superagi/__init__.py, main.py, config_template.yaml")
    if not summary["expected_paths"]["docker"].get("docker-compose.yaml"):
        summary["warnings"].append("default docker-compose.yaml not found; deployment guidance may need refresh")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Repo root: {root}")
        print(f"Probable SuperAGI checkout: {summary['is_probable_superagi']}")
        print("Counts:")
        for key, value in summary["counts"].items():
            print(f"- {key}: {value}")
        if summary["warnings"]:
            print("Warnings:")
            for warning in summary["warnings"]:
                print(f"- {warning}")
    return 0 if summary["is_probable_superagi"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
