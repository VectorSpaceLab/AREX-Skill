#!/usr/bin/env python3
"""Safe Serenata de Amor import and configuration preflight.

This helper is intentionally read-only: it imports Jarbas/Rosie modules and may
run Django setup, but it does not run migrations, download datasets, start
servers, enqueue Celery tasks, or call external APIs.

Examples:
  python scripts/check_serenata_imports.py --repo-root /path/to/serenata-de-amor
  python scripts/check_serenata_imports.py --skip-django --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_ENV = {
    "SECRET_KEY": "unsafe-check-only",
    "DATABASE_URL": "sqlite:////tmp/serenata-check.sqlite3",
    "CACHE_BACKEND": "django.core.cache.backends.dummy.DummyCache",
    "CELERY_BROKER_URL": "memory://",
    "DJANGO_SETTINGS_MODULE": "jarbas.settings",
}

JARBAS_MODULES = [
    "jarbas",
    "jarbas.settings",
    "jarbas.chamber_of_deputies.serializers",
    "jarbas.chamber_of_deputies.views",
    "jarbas.core.management.commands",
]

ROSIE_MODULES = [
    "rosie",
    "rosie.core",
    "rosie.core.classifiers.invalid_cnpj_cpf_classifier",
    "rosie.chamber_of_deputies.classifiers.traveled_speeds_classifier",
]


def add_repo_roots(repo_root: Optional[str]) -> None:
    if not repo_root:
        return
    root = Path(repo_root).resolve()
    candidates = [root, root / "rosie"]
    for candidate in reversed(candidates):
        text = str(candidate)
        if candidate.exists() and text not in sys.path:
            sys.path.insert(0, text)


def set_defaults(overrides: bool) -> Tuple[List[str], List[str]]:
    injected: List[str] = []
    overridden: List[str] = []
    for key, value in DEFAULT_ENV.items():
        if key not in os.environ:
            os.environ[key] = value
            injected.append(key)
        elif overrides:
            os.environ[key] = value
            overridden.append(key)
    return injected, overridden


def import_modules(names: Sequence[str]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for name in names:
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - diagnostic path
            rows.append({"module": name, "status": "failed", "error": f"{exc.__class__.__name__}: {exc}"})
        else:
            rows.append({"module": name, "status": "ok", "file": getattr(module, "__file__", "built-in") or "built-in"})
    return rows


def run_django_setup() -> Dict[str, str]:
    try:
        import django
        django.setup()
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "failed", "error": f"{exc.__class__.__name__}: {exc}"}
    return {"status": "ok"}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check Serenata de Amor Jarbas/Rosie imports without side effects.")
    parser.add_argument("--repo-root", help="Optional Serenata de Amor checkout root to add to sys.path.")
    parser.add_argument("--skip-django", action="store_true", help="Skip Django setup and Jarbas module imports.")
    parser.add_argument("--skip-rosie", action="store_true", help="Skip Rosie module imports.")
    parser.add_argument("--override-env", action="store_true", help="Override existing check-time env vars with safe defaults.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    add_repo_roots(args.repo_root)
    injected, overridden = set_defaults(args.override_env)

    result: Dict[str, object] = {
        "side_effect_boundary": "imports and optional django.setup only; no migrations, services, downloads, or external API calls",
        "injected_default_keys": injected,
        "overridden_keys": overridden,
        "django_setup": "skipped" if args.skip_django else None,
        "imports": [],
    }

    exit_code = 0
    if not args.skip_django:
        django_status = run_django_setup()
        result["django_setup"] = django_status
        if django_status.get("status") != "ok":
            exit_code = 1
        jarbas_rows = import_modules(JARBAS_MODULES)
        result["imports"].extend(jarbas_rows)  # type: ignore[index]
        if any(row["status"] != "ok" for row in jarbas_rows):
            exit_code = 1

    if not args.skip_rosie:
        rosie_rows = import_modules(ROSIE_MODULES)
        result["imports"].extend(rosie_rows)  # type: ignore[index]
        if any(row["status"] != "ok" for row in rosie_rows):
            exit_code = 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Serenata import preflight")
        print(f"Injected default env keys: {', '.join(injected) or 'none'}")
        print(f"Overridden env keys: {', '.join(overridden) or 'none'}")
        print(f"Django setup: {result['django_setup']}")
        for row in result["imports"]:  # type: ignore[index]
            if row["status"] == "ok":
                print(f"OK {row['module']}")
            else:
                print(f"FAIL {row['module']}: {row['error']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
