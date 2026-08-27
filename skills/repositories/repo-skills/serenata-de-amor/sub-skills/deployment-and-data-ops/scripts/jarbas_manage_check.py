#!/usr/bin/env python3
"""Safe wrapper for Jarbas ``python manage.py check``.

The wrapper prepares only the child process environment needed for a Django
system-check/import preflight. It does not run migrations, start services,
fetch network data, or mutate the caller's shell environment.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

SAFE_DEFAULTS = {
    "SECRET_KEY": "jarbas-local-check-only-secret",
    "DATABASE_URL": "sqlite:///{}".format(
        Path(tempfile.gettempdir(), "jarbas-manage-check.sqlite3").as_posix()
    ),
    "CACHE_BACKEND": "django.core.cache.backends.dummy.DummyCache",
    "CELERY_BROKER_URL": "memory://",
    "DJANGO_SETTINGS_MODULE": "jarbas.settings",
}

SENSITIVE_KEYS = {
    "SECRET_KEY",
    "DATABASE_URL",
    "CELERY_BROKER_URL",
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_SECRET",
    "DO_API_TOKEN",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Jarbas 'python manage.py check' with safe child-process "
            "defaults for missing settings. This is an import/configuration "
            "preflight only; it avoids migrations, network calls, and service startup."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a Serenata de Amor checkout containing manage.py (default: current directory).",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used for the child process (default: this interpreter).",
    )
    parser.add_argument(
        "--django-settings-module",
        default=None,
        help="Override DJANGO_SETTINGS_MODULE for the child process (default: jarbas.settings when unset).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override DATABASE_URL for the child process. Omit for existing env or safe SQLite check default.",
    )
    parser.add_argument(
        "--secret-key",
        default=None,
        help="Override SECRET_KEY for the child process. Omit for existing env or safe dummy check default.",
    )
    parser.add_argument(
        "--cache-backend",
        default=None,
        help="Override CACHE_BACKEND for the child process. Omit for existing env or dummy cache default.",
    )
    parser.add_argument(
        "--celery-broker-url",
        default=None,
        help="Override CELERY_BROKER_URL for the child process. Omit for existing env or memory broker default.",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Include Django deployment checks by passing --deploy to manage.py check.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Seconds before terminating the check process (default: 60).",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Print the resolved command and injected/defaulted env keys, but do not invoke Django.",
    )
    parser.add_argument(
        "extra_check_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments for 'manage.py check'. Prefix with -- to separate wrapper args.",
    )
    return parser


def normalize_extra(args: List[str]) -> List[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def child_environment(args: argparse.Namespace) -> Tuple[Dict[str, str], List[str], List[str]]:
    env = os.environ.copy()
    injected: List[str] = []
    overridden: List[str] = []

    explicit = {
        "SECRET_KEY": args.secret_key,
        "DATABASE_URL": args.database_url,
        "CACHE_BACKEND": args.cache_backend,
        "CELERY_BROKER_URL": args.celery_broker_url,
        "DJANGO_SETTINGS_MODULE": args.django_settings_module,
    }

    for key, value in explicit.items():
        if value is not None:
            env[key] = value
            overridden.append(key)

    for key, value in SAFE_DEFAULTS.items():
        if not env.get(key):
            env[key] = value
            injected.append(key)

    return env, injected, overridden


def redacted_environment_view(env: Dict[str, str], keys: List[str]) -> Dict[str, str]:
    view: Dict[str, str] = {}
    for key in keys:
        if key in SENSITIVE_KEYS:
            view[key] = "<redacted>"
        else:
            view[key] = env.get(key, "")
    return view


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    manage_py = repo_root / "manage.py"
    if not manage_py.is_file():
        parser.error("--repo-root must contain manage.py")

    env, injected, overridden = child_environment(args)

    command = [args.python, "manage.py", "check"]
    if args.deploy:
        command.append("--deploy")
    command.extend(normalize_extra(args.extra_check_args))

    preview_keys = sorted(set(injected + overridden + list(SAFE_DEFAULTS)))
    preview = {
        "cwd": str(repo_root),
        "command": command,
        "injected_default_keys": injected,
        "overridden_keys": overridden,
        "environment_preview": redacted_environment_view(env, preview_keys),
        "side_effect_boundary": "Django system check only; no migrations, network fetches, or service startup requested by this wrapper.",
    }

    if args.no_run:
        print(json.dumps(preview, indent=2, sort_keys=True))
        return 0

    print("Running Jarbas Django system check...", flush=True)
    print(
        json.dumps(
            {k: preview[k] for k in ("command", "injected_default_keys", "overridden_keys", "side_effect_boundary")},
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )

    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            env=env,
            text=True,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("ERROR: manage.py check timed out after {:.1f}s".format(args.timeout), file=sys.stderr)
        return 124

    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
