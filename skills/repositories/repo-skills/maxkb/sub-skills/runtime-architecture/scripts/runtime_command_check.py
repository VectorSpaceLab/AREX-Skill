#!/usr/bin/env python3
"""Static checker for MaxKB runtime entrypoints and command surfaces."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[6]

KEY_FILES = [
    "main.py",
    "apps/manage.py",
    "apps/maxkb/conf.py",
    "apps/maxkb/settings/base/web.py",
    "apps/maxkb/settings/base/model.py",
    "apps/maxkb/urls/web.py",
    "apps/maxkb/urls/model.py",
    "apps/ops/celery/__init__.py",
    "apps/ops/celery/hmac_signed_serializer.py",
    "apps/oss/tests.py",
]

KNOWN_COMMANDS = [
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
]


def main() -> int:
    report = {
        "repo_root": str(REPO_ROOT),
        "files": {path: (REPO_ROOT / path).exists() for path in KEY_FILES},
        "known_commands": KNOWN_COMMANDS,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
