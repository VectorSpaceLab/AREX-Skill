#!/usr/bin/env python3
"""Statically inspect SuperAGI Docker Compose files.

Example:
  python check_compose_files.py --repo-root /path/to/SuperAGI
  python check_compose_files.py --compose docker-compose-gpu.yml --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with `python -m pip install PyYAML`.", file=sys.stderr)
    raise SystemExit(2)

EXPECTED_DEFAULT = {"backend", "celery", "gui", "super__redis", "super__postgres", "proxy"}


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def inspect_compose(path: Path) -> dict:
    result = {"path": str(path), "exists": path.exists(), "errors": [], "warnings": [], "services": [], "gpu_services": []}
    if not path.exists():
        result["errors"].append("compose file not found")
        return result
    data = load_yaml(path)
    services = data.get("services") or {}
    if not isinstance(services, dict):
        result["errors"].append("services must be a mapping")
        return result
    result["services"] = sorted(services)
    missing = sorted(EXPECTED_DEFAULT - set(services))
    if missing:
        result["warnings"].append(f"missing expected SuperAGI services: {', '.join(missing)}")
    for name, spec in services.items():
        deploy = spec.get("deploy", {}) if isinstance(spec, dict) else {}
        resources = deploy.get("resources", {}) if isinstance(deploy, dict) else {}
        reservations = resources.get("reservations", {}) if isinstance(resources, dict) else {}
        devices = reservations.get("devices", []) if isinstance(reservations, dict) else []
        if devices:
            result["gpu_services"].append(name)
    if "backend" in services:
        command = services["backend"].get("command") if isinstance(services["backend"], dict) else None
        if command and "entrypoint.sh" not in " ".join(map(str, command)):
            result["warnings"].append("backend command does not reference entrypoint.sh")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect SuperAGI compose files without running Docker")
    parser.add_argument("--repo-root", default=".", help="Checkout root used to resolve default compose paths")
    parser.add_argument("--compose", action="append", help="Compose file path; can be repeated")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    paths = [Path(p) for p in args.compose] if args.compose else [root / "docker-compose.yaml", root / "docker-compose-gpu.yml"]
    paths = [p if p.is_absolute() else root / p for p in paths]
    report = {"repo_root": str(root), "files": [inspect_compose(p) for p in paths]}
    report["ok"] = all(not f["errors"] for f in report["files"])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["files"]:
            print(f"{item['path']}: {'OK' if not item['errors'] else 'NOT OK'}")
            print(f"  services: {', '.join(item['services']) or '(none)'}")
            if item["gpu_services"]:
                print(f"  gpu reservations: {', '.join(item['gpu_services'])}")
            for warning in item["warnings"]:
                print(f"  warning: {warning}")
            for error in item["errors"]:
                print(f"  error: {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
