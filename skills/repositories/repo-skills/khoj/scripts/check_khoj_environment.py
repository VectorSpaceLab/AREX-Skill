#!/usr/bin/env python3
"""Check a Khoj Python environment without starting the server."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from pathlib import Path
from typing import Any


def add_repo_src(repo_root: str | None) -> None:
    if not repo_root:
        return
    src = Path(repo_root) / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def check_distribution() -> dict[str, Any]:
    try:
        version = metadata.version("khoj")
        return {"ok": True, "version": version}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def import_module(name: str) -> dict[str, Any]:
    try:
        importlib.import_module(name)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_cli_parser() -> dict[str, Any]:
    try:
        from khoj.utils.cli import cli

        parsed = cli([])
        return {
            "ok": True,
            "host": parsed.host,
            "port": parsed.port,
            "log_file": str(parsed.log_file),
            "anonymous_mode": parsed.anonymous_mode,
            "non_interactive": parsed.non_interactive,
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_django_setup() -> dict[str, Any]:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "khoj.app.settings")
    try:
        import django
        from django.apps import apps

        if not apps.ready:
            django.setup()
        return {"ok": True, "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE")}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Khoj import metadata, safe parser defaults, and optional Django setup.")
    parser.add_argument("--repo-root", help="Optional local checkout root; adds <repo-root>/src to sys.path for editable inspection.")
    parser.add_argument("--django", action="store_true", help="Also run django.setup() after setting DJANGO_SETTINGS_MODULE if unset.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    add_repo_src(args.repo_root)
    result: dict[str, Any] = {
        "distribution": check_distribution(),
        "imports": {
            name: import_module(name)
            for name in [
                "khoj",
                "khoj.utils.cli",
                "khoj.utils.rawconfig",
            ]
        },
        "cli_parser": check_cli_parser(),
        "notes": [
            "This helper intentionally does not import khoj.main or start the server.",
            "If the real khoj console script fails before --help, inspect database/server setup with deployment-api troubleshooting.",
        ],
    }
    if args.django:
        result["django"] = check_django_setup()

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["imports"]["khoj"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
