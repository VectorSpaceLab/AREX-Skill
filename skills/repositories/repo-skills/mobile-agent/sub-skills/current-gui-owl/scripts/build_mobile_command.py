#!/usr/bin/env python3
"""Build a safe Mobile-Agent-v3.5 / GUI-Owl mobile command.

The script prints a command template only. It does not invoke ADB, connect to a
phone, or call a model API.
"""
from __future__ import annotations

import argparse
import shlex


def env_ref(name: str) -> str:
    if not name or not name.replace("_", "").replace("-", "").isalnum():
        raise SystemExit(f"invalid environment variable name: {name!r}")
    return f'"${{{name}}}"'


def value_or_env(value: str | None, env: str | None, label: str) -> str:
    if value is not None:
        return shlex.quote(value)
    if env:
        return env_ref(env)
    raise SystemExit(f"missing --{label} or --{label}-env")


def main() -> int:
    p = argparse.ArgumentParser(description="Print a safe GUI-Owl v3.5 Android command template.")
    p.add_argument("--repo-root", help="Prepared MobileAgent runtime checkout root. If omitted, uses --repo-root-env.")
    p.add_argument("--repo-root-env", default="MOBILE_AGENT_REPO", help="Environment variable containing the runtime checkout root.")
    p.add_argument("--adb-path")
    p.add_argument("--adb-path-env")
    p.add_argument("--device", help="Optional adb device serial, e.g. emulator-5554.")
    p.add_argument("--api-key")
    p.add_argument("--api-key-env", default="GUI_OWL_API_KEY")
    p.add_argument("--base-url")
    p.add_argument("--base-url-env", default="GUI_OWL_BASE_URL")
    p.add_argument("--model")
    p.add_argument("--model-env", default="GUI_OWL_MODEL")
    p.add_argument("--instruction", required=True)
    p.add_argument("--add-info", default="")
    p.add_argument("--max-steps", type=int, default=50)
    p.add_argument("--app-resolver-api-key-env")
    p.add_argument("--app-resolver-base-url-env")
    p.add_argument("--app-resolver-model", default="qwen-plus")
    p.add_argument("--one-line", action="store_true", help="Print only the command.")
    args = p.parse_args()

    repo = shlex.quote(args.repo_root) if args.repo_root else env_ref(args.repo_root_env)
    adb = value_or_env(args.adb_path, args.adb_path_env, "adb-path")
    api_key = value_or_env(args.api_key, args.api_key_env, "api-key")
    base_url = value_or_env(args.base_url, args.base_url_env, "base-url")
    model = value_or_env(args.model, args.model_env, "model")

    parts = [
        "cd", f"{repo}/Mobile-Agent-v3.5/mobile_use", "&&", "python", "run_gui_owl_1_5_for_mobile.py",
        "--adb_path", adb,
        "--api_key", api_key,
        "--base_url", base_url,
        "--model", model,
        "--instruction", shlex.quote(args.instruction),
        "--max_steps", str(args.max_steps),
    ]
    if args.device:
        parts += ["--device", shlex.quote(args.device)]
    if args.add_info:
        parts += ["--add_info", shlex.quote(args.add_info)]
    if args.app_resolver_api_key_env:
        parts += ["--app_resolver_api_key", env_ref(args.app_resolver_api_key_env)]
    if args.app_resolver_base_url_env:
        parts += ["--app_resolver_base_url", env_ref(args.app_resolver_base_url_env)]
    if args.app_resolver_model:
        parts += ["--app_resolver_model", shlex.quote(args.app_resolver_model)]

    command = " ".join(parts)
    if args.one_line:
        print(command)
    else:
        print("# Safe template only: verify adb devices, USB debugging, ADB Keyboard, and model API before running.")
        print("# GUI-Owl mobile actions use normalized 0..1000 coordinates that the launcher rescales.")
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
