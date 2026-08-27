#!/usr/bin/env python3
"""Print a compact static snapshot of the MaxKB repo.

The script avoids live-service dependencies. It reads repository metadata and
known UI/backend command surfaces from source files.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None


REPO_ROOT = Path(__file__).resolve().parents[4]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def git_status() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def main() -> int:
    pyproject = {}
    if tomllib is not None:
        try:
            pyproject = tomllib.loads(read_text(REPO_ROOT / "pyproject.toml"))
        except Exception:
            pyproject = {}

    project = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
    ui_pkg = {}
    try:
        ui_pkg = json.loads(read_text(REPO_ROOT / "ui" / "package.json"))
    except Exception:
        ui_pkg = {}

    summary = {
        "repo_root": str(REPO_ROOT),
        "package_name": project.get("name", "maxkb"),
        "package_version": project.get("version", "unknown"),
        "ui_scripts": sorted((ui_pkg.get("scripts") or {}).keys()),
        "known_backend_commands": [
            "python main.py dev",
            "python main.py dev celery",
            "python main.py dev local_model",
            "python main.py start all -d",
            "python main.py start web -w 3",
            "python main.py start task",
            "python main.py stop all",
            "python main.py status",
            "python main.py upgrade_db",
            "python main.py collect_static",
        ],
        "known_prefixes": ["/admin", "/chat"],
        "status": git_status()[:20],
        "subskills": [
            "runtime-architecture",
            "workflow-chat-mcp",
            "knowledge-models",
            "frontend-integration",
            "admin-access",
        ],
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
