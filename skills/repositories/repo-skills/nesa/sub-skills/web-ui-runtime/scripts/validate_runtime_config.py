#!/usr/bin/env python3
"""Read-only validator for Nesa web UI settings and command flags."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Missing dependency pyyaml: {type(exc).__name__}: {exc}") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("settings file must parse to a mapping")
    return data


def parse_flags(path: Path | None) -> list[str]:
    if path is None:
        return []
    flags: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().rstrip("\\").strip()
        if not line or line.startswith("#"):
            continue
        flags.extend(shlex.split(line))
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Nesa encrypted web UI settings without launching the service.")
    parser.add_argument("--settings", type=Path, required=True, help="YAML settings file to inspect.")
    parser.add_argument("--cmd-flags", type=Path, help="Optional CMD_FLAGS-style file.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    settings = load_yaml(args.settings)
    flags = parse_flags(args.cmd_flags)
    warnings: list[str] = []
    errors: list[str] = []

    if settings.get("mode") != "equivariant-encrypt":
        errors.append("settings.mode should be 'equivariant-encrypt' for Nesa encrypted workflows")
    if not settings.get("equivariant-encrypt_command"):
        errors.append("missing or empty equivariant-encrypt_command")
    if settings.get("autoload_model") is True:
        warnings.append("autoload_model is true; disable it while debugging model paths or downloads")

    risky_exposure = any(flag in flags for flag in ["--listen", "--share"])
    has_auth = any(flag.startswith("--gradio-auth") or flag.startswith("--gradio-auth-path") for flag in flags)
    if risky_exposure and not has_auth:
        warnings.append("public/LAN exposure flag present without gradio auth flag")
    if "--cpu" in flags:
        warnings.append("--cpu flag present; GPU will not be used unless flags are changed")
    if "--trust-remote-code" in flags:
        warnings.append("--trust-remote-code present; use only for trusted model sources")

    result = {
        "settings_file": str(args.settings),
        "cmd_flags_file": str(args.cmd_flags) if args.cmd_flags else None,
        "mode": settings.get("mode"),
        "autoload_model": settings.get("autoload_model"),
        "flags": flags,
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"mode: {result['mode']}")
        print(f"autoload_model: {result['autoload_model']}")
        print(f"flags: {' '.join(flags) if flags else '(none)'}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print(f"OK: {result['ok']}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
