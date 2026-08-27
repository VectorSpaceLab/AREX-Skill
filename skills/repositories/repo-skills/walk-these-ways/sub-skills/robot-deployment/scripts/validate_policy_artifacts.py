#!/usr/bin/env python3
"""Read-only validator for a Walk-These-Ways deployment policy directory.

The validator checks names, regular-file status, non-empty sizes, and an optional
JSON config. It deliberately does not unpickle parameters.pkl, load TorchScript,
import the Unitree SDK/LCM, run inference, publish targets, or control a robot.
"""
from __future__ import annotations

import argparse
import json
import stat
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REQUIRED_FILES = (
    "parameters.pkl",
    "checkpoints/body_latest.jit",
    "checkpoints/adaptation_module_latest.jit",
)
REQUIRED_CONFIG_PATHS = (
    ("env", "num_observations"),
    ("env", "num_observation_history"),
    ("env", "num_actions"),
    ("control", "decimation"),
    ("sim", "dt"),
)


def regular_nonempty(path: Path) -> Tuple[bool, str]:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        return False, f"unreadable: {exc}"
    if not stat.S_ISREG(mode):
        return False, "not a regular file"
    if path.stat().st_size <= 0:
        return False, "empty file"
    return True, f"{path.stat().st_size} bytes"


def nested(config: Dict[str, Any], path: Iterable[str]) -> Tuple[bool, Any]:
    value: Any = config
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return False, None
        value = value[key]
    return True, value


def validate_config(path: Path, expected_actions: int | None, expected_history: int | None) -> List[str]:
    errors: List[str] = []
    try:
        if path.is_symlink() or not path.is_file():
            return [f"config is not a regular file: {path}"]
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON config {path}: {exc}"]
    if not isinstance(config, dict):
        return ["JSON config root must be an object"]

    for required in REQUIRED_CONFIG_PATHS:
        ok, value = nested(config, required)
        if not ok:
            errors.append("missing config field " + ".".join(required))
        elif not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append("config field " + ".".join(required) + " must be numeric")
        elif value <= 0:
            errors.append("config field " + ".".join(required) + " must be positive")

    ok, actions = nested(config, ("env", "num_actions"))
    if expected_actions is not None and ok and actions != expected_actions:
        errors.append(f"env.num_actions={actions} does not match --expected-actions={expected_actions}")
    ok, history = nested(config, ("env", "num_observation_history"))
    if expected_history is not None and ok and history != expected_history:
        errors.append(
            f"env.num_observation_history={history} does not match --expected-history={expected_history}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Go1 policy artifact validator")
    parser.add_argument("policy_dir", type=Path, help="run directory containing parameters.pkl and checkpoints/")
    parser.add_argument(
        "--config",
        type=Path,
        help="optional JSON config export to check required deployment fields; never loads parameters.pkl",
    )
    parser.add_argument("--expected-actions", type=int, help="optional expected action count")
    parser.add_argument("--expected-history", type=int, help="optional expected history-frame count")
    args = parser.parse_args()

    root = args.policy_dir.expanduser()
    errors: List[str] = []
    if not root.exists():
        errors.append(f"policy directory does not exist: {root}")
    elif not root.is_dir() or root.is_symlink():
        errors.append(f"policy path is not a non-symlink directory: {root}")

    print("Mode: READ-ONLY (no pickle load, TorchScript load, inference, LCM, or control loop)")
    print(f"Policy directory: {root}")
    for relative in REQUIRED_FILES:
        path = root / relative
        ok, detail = regular_nonempty(path) if path.exists() else (False, "missing")
        print(f"- {relative}: {'OK' if ok else 'FAIL'} ({detail})")
        if not ok:
            errors.append(f"{relative}: {detail}")

    if args.config is not None:
        config_errors = validate_config(args.config.expanduser(), args.expected_actions, args.expected_history)
        print(f"- JSON config: {'OK' if not config_errors else 'FAIL'} ({args.config})")
        errors.extend(config_errors)
    elif args.expected_actions is not None or args.expected_history is not None:
        print("- JSON config: FAIL (required when expected shape flags are used)")
        errors.append("--config is required with --expected-actions/--expected-history")

    if errors:
        print("RESULT: INVALID")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("RESULT: VALID STATIC ARTIFACT SET")
    print("Physical deployment remains BLOCKED_REQUIRED_BACKEND until hardware, SDK, and safety gates are approved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
