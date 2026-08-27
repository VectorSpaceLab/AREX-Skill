#!/usr/bin/env python3
"""Read-only BiSheng repository surface inspector.

Example:
  python scripts/check_repo_surface.py --repo-root .

The helper checks for the main BiSheng source roots, metadata files, architecture
documents, frontend package manifests, and test/script directories without
importing application code or requiring services.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CHECKS = {
    "backend_source": "src/backend/bisheng",
    "langchain_extension": "src/backend/bisheng_langchain",
    "backend_metadata": "src/backend/pyproject.toml",
    "backend_lock": "src/backend/uv.lock",
    "backend_tests": "src/backend/test",
    "platform_package": "src/frontend/platform/package.json",
    "platform_source": "src/frontend/platform/src",
    "client_package": "src/frontend/client/package.json",
    "client_source": "src/frontend/client/src",
    "docker_compose": "docker/docker-compose.yml",
    "constitution": "docs/constitution.md",
    "architecture_docs": "docs/architecture",
    "root_rules": "AGENTS.md",
    "backend_rules": "src/backend/AGENTS.md",
    "platform_rules": "src/frontend/platform/AGENTS.md",
    "client_rules": "src/frontend/client/AGENTS.md",
    "arch_guard": "scripts/arch-guard.sh",
}

COUNT_DIRS = [
    "src/backend/bisheng",
    "src/backend/bisheng_langchain",
    "src/backend/test",
    "src/frontend/platform/src",
    "src/frontend/client/src",
    "docs/architecture",
    "src/backend/scripts",
]


def file_count(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    return sum(1 for child in path.rglob("*") if child.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a BiSheng checkout surface.")
    parser.add_argument("--repo-root", default=".", help="BiSheng checkout root")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    checks = {name: (repo / rel).exists() for name, rel in CHECKS.items()}
    counts = {rel: file_count(repo / rel) for rel in COUNT_DIRS}
    result = {"repo_root": str(repo), "checks": checks, "counts": counts, "ok": all(checks.values())}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("BiSheng repository surface")
        print("==========================")
        for name, rel in CHECKS.items():
            print(f"{name:24} {'OK' if checks[name] else 'MISSING'}  {rel}")
        print("\nfile counts:")
        for rel, count in counts.items():
            print(f"{rel:36} {count}")
        print(f"\nsummary: {'OK' if result['ok'] else 'CHECK missing required surfaces'}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
