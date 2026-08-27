#!/usr/bin/env python3
"""Read-only inspection helper for local W&B CLI state.

The script reports selected environment variables, workspace settings files,
candidate run directories, and CLI availability. It does not upload, delete,
login, or print credential values.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "COOKIE")
INTERESTING_ENV = (
    "WANDB_API_KEY",
    "WANDB_BASE_URL",
    "WANDB_ENTITY",
    "WANDB_PROJECT",
    "WANDB_MODE",
    "WANDB_DIR",
    "WANDB_CONFIG_DIR",
    "WANDB_DATA_DIR",
    "WANDB_CACHE_DIR",
    "WANDB_ARTIFACT_DIR",
    "WANDB_RUN_DIR",
    "WANDB_RUN_ID",
    "WANDB_RESUME",
    "WANDB_RUN_GROUP",
    "WANDB_JOB_TYPE",
    "WANDB_TAGS",
    "WANDB_SILENT",
    "WANDB_QUIET",
    "WANDB_DISABLE_CODE",
    "WANDB_DISABLE_GIT",
    "WANDB_IGNORE_GLOBS",
    "WANDB_HTTP_TIMEOUT",
    "WANDB_INIT_TIMEOUT",
    "WANDB_INSECURE_DISABLE_SSL",
    "WANDB_IDENTITY_TOKEN_FILE",
    "WANDB_CREDENTIALS_FILE",
    "NETRC",
)


def redact(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    upper_name = name.upper()
    if any(marker in upper_name for marker in SECRET_MARKERS):
        return "<set:redacted>" if value else "<empty>"
    return value


def command_version(command: list[str]) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False}
    try:
        proc = subprocess.run(
            command + ["--version"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostics should not crash.
        return {"available": True, "path": executable, "error": str(exc)}
    output = (proc.stdout or proc.stderr).strip()
    return {
        "available": True,
        "path": executable,
        "returncode": proc.returncode,
        "version_output": output,
    }


def parse_settings(path: Path) -> dict[str, str]:
    parser = configparser.ConfigParser()
    try:
        parser.read(path)
    except configparser.Error as exc:
        return {"_parse_error": str(exc)}

    values: dict[str, str] = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            values[f"{section}.{key}"] = redact(key, value) or ""
    if not values:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"_read_error": str(exc)}
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(('#', ';')) or '=' not in stripped:
                continue
            key, value = stripped.split('=', 1)
            values[key.strip()] = redact(key.strip(), value.strip()) or ""
    return values


def run_info(run_dir: Path) -> dict[str, Any]:
    wandb_files = sorted(str(path) for path in run_dir.glob("*.wandb"))
    synced_markers = sorted(str(path) for path in run_dir.glob("*.synced"))
    return {
        "path": str(run_dir),
        "name": run_dir.name,
        "offline": run_dir.name.startswith("offline-"),
        "wandb_files": wandb_files,
        "synced_markers": synced_markers,
    }


def inspect_root(root: Path, max_runs: int) -> dict[str, Any]:
    root = root.resolve()
    candidate_wandb_dirs = []
    for dirname in ("wandb", ".wandb"):
        path = root / dirname
        if path.exists():
            candidate_wandb_dirs.append(path)

    settings_files = []
    runs = []
    for wandb_dir in candidate_wandb_dirs:
        settings_path = wandb_dir / "settings"
        if settings_path.exists():
            settings_files.append(
                {
                    "path": str(settings_path),
                    "values": parse_settings(settings_path),
                }
            )
        for child in sorted(wandb_dir.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith(("run-", "offline-run-")):
                runs.append(run_info(child))

    return {
        "root": str(root),
        "wandb_dirs": [str(path) for path in candidate_wandb_dirs],
        "settings_files": settings_files,
        "run_count": len(runs),
        "runs": runs[:max_runs],
        "run_output_truncated": len(runs) > max_runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only inspection of local W&B CLI state with secret redaction."
    )
    parser.add_argument("--root", default=".", help="Project root to inspect.")
    parser.add_argument(
        "--max-runs", type=int, default=25, help="Maximum candidate run directories to list."
    )
    args = parser.parse_args()

    env = {name: redact(name, os.environ.get(name)) for name in INTERESTING_ENV if name in os.environ}
    extra_wandb_env = {
        name: redact(name, value)
        for name, value in sorted(os.environ.items())
        if name.startswith("WANDB_") and name not in INTERESTING_ENV
    }

    report = {
        "python": sys.version.split()[0],
        "cli": {
            "wandb": command_version(["wandb"]),
            "wb": command_version(["wb"]),
        },
        "environment": env,
        "other_wandb_environment": extra_wandb_env,
        "workspace": inspect_root(Path(args.root), args.max_runs),
        "notes": [
            "Read-only inspection only; no login, upload, sync, or deletion was attempted.",
            "Credential-like values are redacted by variable or setting name.",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
