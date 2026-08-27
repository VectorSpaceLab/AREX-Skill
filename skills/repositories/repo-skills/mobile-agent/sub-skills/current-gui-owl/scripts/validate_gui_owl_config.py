#!/usr/bin/env python3
"""Validate common GUI-Owl v3.5 command inputs without live side effects."""
from __future__ import annotations

import argparse
import os
import sys


def env_status(name: str | None) -> tuple[bool, str]:
    if not name:
        return False, "not configured"
    return (name in os.environ and bool(os.environ.get(name)), name)


def main() -> int:
    p = argparse.ArgumentParser(description="Validate GUI-Owl config shape and warn about live prerequisites.")
    p.add_argument("--platform", choices=["mobile", "computer", "browser"], required=True)
    p.add_argument("--adb-path")
    p.add_argument("--adb-path-env")
    p.add_argument("--api-key-env", default="GUI_OWL_API_KEY")
    p.add_argument("--base-url")
    p.add_argument("--base-url-env", default="GUI_OWL_BASE_URL")
    p.add_argument("--model")
    p.add_argument("--model-env", default="GUI_OWL_MODEL")
    p.add_argument("--instruction")
    p.add_argument("--task")
    p.add_argument("--web")
    p.add_argument("--image-type", choices=["base64", "file", "oss"], default="base64")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--require-adb-keyboard", action="store_true")
    p.add_argument("--max-steps", type=int, default=50)
    args = p.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    if args.max_steps <= 0:
        errors.append("max steps/iterations must be positive")
    if args.platform in {"mobile", "computer"} and not args.instruction:
        errors.append("mobile/computer routes require --instruction")
    if args.platform == "browser" and not (args.task or args.web):
        errors.append("browser route should provide --task and usually --web")
    if args.platform == "mobile" and not (args.adb_path or args.adb_path_env):
        errors.append("mobile route requires --adb-path or --adb-path-env")
    if args.platform == "computer":
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            warnings.append("no DISPLAY/WAYLAND_DISPLAY detected; desktop live control needs an interactive GUI session")
    if args.platform == "browser":
        warnings.append("browser live control needs Playwright browser installation and website/API access")
        if args.image_type == "oss":
            warnings.append("image_type=oss needs private OSS credentials configured in the runtime environment")
    if args.platform == "mobile":
        warnings.append("live run still needs adb devices authorization, USB debugging, and ADB Keyboard for typing")
        if args.require_adb_keyboard:
            warnings.append("ADB Keyboard cannot be verified safely here; confirm it manually before text-entry tasks")

    ok, name = env_status(args.api_key_env)
    if not ok:
        warnings.append(f"API key env {name} is not currently exported")
    if not (args.base_url or (args.base_url_env and os.environ.get(args.base_url_env))):
        warnings.append(f"base URL not provided/exported via {args.base_url_env}")
    if not (args.model or (args.model_env and os.environ.get(args.model_env))):
        warnings.append(f"model not provided/exported via {args.model_env}")

    print(f"platform={args.platform}")
    print("coordinate_convention=normalized_0_to_1000_rescaled_by_launcher")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    return 2 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
