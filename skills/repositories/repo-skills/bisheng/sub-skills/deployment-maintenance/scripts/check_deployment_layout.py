#!/usr/bin/env python3
"""Inspect BiSheng deployment, script, and maintenance layout without starting services."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED = [
    "docker/docker-compose.yml",
    "docker/deploy.sh",
    "docker/bisheng/entrypoint.sh",
    "src/backend/pyproject.toml",
    "src/backend/uv.lock",
    "src/backend/scripts/README.md",
    "scripts/arch-guard.sh",
    "AGENTS.md",
    "docs/SDD-Guide.md",
    "docs/constitution.md",
]


def service_names(compose_text: str) -> list[str]:
    names = []
    in_services = False
    for line in compose_text.splitlines():
        if re.match(r"^services:\s*$", line):
            in_services = True
            continue
        if in_services:
            m = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
            if m:
                names.append(m.group(1))
            elif line and not line.startswith(" "):
                break
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect BiSheng deployment layout.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    checks = {rel: (repo / rel).exists() for rel in EXPECTED}
    compose = repo / "docker/docker-compose.yml"
    services = service_names(compose.read_text(encoding="utf-8", errors="replace")) if compose.exists() else []
    scripts = sorted(str(p.relative_to(repo / "src/backend")) for p in (repo / "src/backend/scripts").glob("*.py")) if (repo / "src/backend/scripts").exists() else []
    result = {"checks": checks, "compose_services": services, "backend_script_count": len(scripts), "sample_backend_scripts": scripts[:40]}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("BiSheng deployment layout")
        print("=========================")
        for rel, ok in checks.items():
            print(f"{rel:42} {'OK' if ok else 'MISSING'}")
        print("\ncompose services:", ", ".join(services) if services else "none")
        print("backend script count:", len(scripts))
        for script in scripts[:30]:
            print(f"  - {script}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
