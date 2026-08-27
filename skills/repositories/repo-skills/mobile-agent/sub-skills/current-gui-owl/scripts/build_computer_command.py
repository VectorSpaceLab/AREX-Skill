#!/usr/bin/env python3
"""Build a safe Mobile-Agent-v3.5 / GUI-Owl desktop command."""
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
    p = argparse.ArgumentParser(description="Print a safe GUI-Owl v3.5 desktop command template.")
    p.add_argument("--repo-root")
    p.add_argument("--repo-root-env", default="MOBILE_AGENT_REPO")
    p.add_argument("--api-key")
    p.add_argument("--api-key-env", default="GUI_OWL_API_KEY")
    p.add_argument("--base-url")
    p.add_argument("--base-url-env", default="GUI_OWL_BASE_URL")
    p.add_argument("--model")
    p.add_argument("--model-env", default="GUI_OWL_MODEL")
    p.add_argument("--instruction", required=True)
    p.add_argument("--add-info", default="")
    p.add_argument("--max-steps", type=int, default=50)
    p.add_argument("--one-line", action="store_true")
    args = p.parse_args()

    repo = shlex.quote(args.repo_root) if args.repo_root else env_ref(args.repo_root_env)
    parts = [
        "cd", f"{repo}/Mobile-Agent-v3.5/computer_use", "&&", "python", "run_gui_owl_1_5_for_pc.py",
        "--api_key", value_or_env(args.api_key, args.api_key_env, "api-key"),
        "--base_url", value_or_env(args.base_url, args.base_url_env, "base-url"),
        "--model", value_or_env(args.model, args.model_env, "model"),
        "--instruction", shlex.quote(args.instruction),
        "--max_steps", str(args.max_steps),
    ]
    if args.add_info:
        parts += ["--add_info", shlex.quote(args.add_info)]
    command = " ".join(parts)
    if not args.one_line:
        print("# Safe template only: desktop control requires an unlocked GUI session, screenshot permission, accessibility control, and a model API.")
        print("# GUI-Owl desktop actions use normalized 0..1000 coordinates rescaled to screenshot size.")
    print(command)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
