#!/usr/bin/env python3
"""Validate a local AppAgent checkout before running the agent loops.

This helper is intentionally read-only. It checks that the repository root,
required config keys, Python helper modules, and adb are available before a
human or agent starts an exploration/deployment session.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


REQUIRED_COMMON_KEYS = {
    "MODEL",
    "REQUEST_INTERVAL",
    "ANDROID_SCREENSHOT_DIR",
    "ANDROID_XML_DIR",
    "DOC_REFINE",
    "MAX_ROUNDS",
    "DARK_MODE",
    "MIN_DIST",
}

OPENAI_KEYS = {"OPENAI_API_BASE", "OPENAI_API_KEY", "OPENAI_API_MODEL", "TEMPERATURE", "MAX_TOKENS"}
QWEN_KEYS = {"DASHSCOPE_API_KEY", "QWEN_MODEL"}


def _load_modules(repo_root: Path):
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    old_cwd = Path.cwd()
    os.chdir(repo_root)
    try:
        import config as app_config  # type: ignore
        import utils as app_utils  # type: ignore
        import model as app_model  # type: ignore
        import and_controller as app_controller  # type: ignore
    finally:
        os.chdir(old_cwd)

    return app_config, app_utils, app_model, app_controller


def _missing_keys(config: dict[str, object], keys: set[str]) -> list[str]:
    return [key for key in sorted(keys) if key not in config or config[key] in (None, "")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the local AppAgent runtime prerequisites.")
    parser.add_argument("--repo-root", default=".", help="Path to the AppAgent checkout.")
    parser.add_argument("--config", default="config.yaml", help="Config path relative to the repo root.")
    parser.add_argument("--skip-adb", action="store_true", help="Do not fail when adb is missing.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    config_path = (repo_root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)

    problems: list[str] = []
    warnings: list[str] = []

    if not repo_root.exists():
        problems.append(f"repo root does not exist: {repo_root}")
        print("ERROR: repo root does not exist.")
        return 1

    if not config_path.exists():
        problems.append(f"config not found: {config_path}")
        print(f"ERROR: config file not found: {config_path}")
        return 1

    try:
        app_config, app_utils, app_model, app_controller = _load_modules(repo_root)
        # Exercise the import path only; the helpers should stay read-only.
        _ = (app_utils.print_with_color, app_model.parse_explore_rsp, app_controller.list_all_devices)
    except Exception as exc:  # pragma: no cover - direct runtime inspection only
        print(f"ERROR: failed to import AppAgent helper modules: {exc}")
        return 1

    try:
        loaded = app_config.load_config(str(config_path))
    except Exception as exc:
        print(f"ERROR: failed to load config: {exc}")
        return 1

    missing_common = _missing_keys(loaded, REQUIRED_COMMON_KEYS)
    if missing_common:
        problems.append(f"missing required config keys: {', '.join(missing_common)}")

    model_name = str(loaded.get("MODEL", "")).strip()
    if model_name == "OpenAI":
        missing_specific = _missing_keys(loaded, OPENAI_KEYS)
        if missing_specific:
            problems.append(f"missing OpenAI config keys: {', '.join(missing_specific)}")
    elif model_name == "Qwen":
        missing_specific = _missing_keys(loaded, QWEN_KEYS)
        if missing_specific:
            problems.append(f"missing Qwen config keys: {', '.join(missing_specific)}")
    else:
        problems.append(f"MODEL must be OpenAI or Qwen, got: {model_name!r}")

    adb_path = shutil.which("adb")
    if adb_path:
        print(f"adb: {adb_path}")
    else:
        msg = "adb not found on PATH"
        if args.skip_adb:
            warnings.append(msg)
        else:
            problems.append(msg)

    print(f"repo-root: {repo_root}")
    print(f"config: {config_path}")
    print(f"model: {loaded.get('MODEL')}")
    print(f"screenshot-dir-on-device: {loaded.get('ANDROID_SCREENSHOT_DIR')}")
    print(f"xml-dir-on-device: {loaded.get('ANDROID_XML_DIR')}")
    print(f"request-interval: {loaded.get('REQUEST_INTERVAL')}")
    print(f"max-rounds: {loaded.get('MAX_ROUNDS')}")
    print(f"docs-refine: {loaded.get('DOC_REFINE')}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for problem in problems:
        print(f"ERROR: {problem}")

    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
