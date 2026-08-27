#!/usr/bin/env python3
"""Build safe Axolotl CLI command strings without executing them."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

LAUNCHER_COMMANDS = {"train", "evaluate", "inference", "merge-sharded-fsdp-weights"}
DIRECT_CONFIG_COMMANDS = {"preprocess", "merge-lora", "lm-eval", "vllm-serve", "quantize"}
NO_CONFIG_COMMANDS = {"fetch", "agent-docs", "config-schema"}
ALL_COMMANDS = LAUNCHER_COMMANDS | DIRECT_CONFIG_COMMANDS | NO_CONFIG_COMMANDS
FETCH_TARGETS = {"examples", "deepspeed_configs", "docs"}
LAUNCHERS = {"accelerate", "torchrun", "python"}


def parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError(f"{label} must be a JSON object")
    return value


def parse_json_list(raw: str, label: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise argparse.ArgumentTypeError(f"{label} must be a JSON array of strings")
    return value


def option_name(key: str) -> str:
    normalized = key.strip().replace("_", "-")
    if not normalized:
        raise ValueError("option names cannot be empty")
    if normalized.startswith("-"):
        raise ValueError(f"option name {key!r} must not include leading dashes")
    return f"--{normalized}"


def append_options(argv: list[str], options: dict[str, Any]) -> None:
    for key, value in options.items():
        flag = option_name(str(key))
        if value is None or value is False:
            continue
        if value is True:
            argv.append(flag)
        elif isinstance(value, (str, int, float)):
            argv.extend([flag, str(value)])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (str, int, float)):
                    argv.extend([flag, str(item)])
                else:
                    raise ValueError(
                        f"option {key!r} list values must be strings or numbers"
                    )
        else:
            raise ValueError(
                f"option {key!r} value must be null, bool, string, number, or list"
            )


def add_config(argv: list[str], config: str | None, command: str, skip_exists: bool) -> None:
    if command in NO_CONFIG_COMMANDS:
        return
    if not config:
        raise ValueError(f"{command!r} requires a config path")
    if not skip_exists and not Path(config).exists():
        raise FileNotFoundError(
            f"config path does not exist: {config}. Pass --skip-config-exists-check "
            "only when constructing a command for a different machine."
        )
    argv.append(config)


def build_command(args: argparse.Namespace) -> list[str]:
    command = args.command
    if command not in ALL_COMMANDS:
        raise ValueError(f"unsupported command {command!r}; choose one of {sorted(ALL_COMMANDS)}")

    options = parse_json_object(args.options_json, "--options-json")
    launcher_args = parse_json_list(args.launcher_args_json, "--launcher-args-json")
    trailing_args = parse_json_list(args.trailing_args_json, "--trailing-args-json")

    if launcher_args and command not in LAUNCHER_COMMANDS:
        raise ValueError(f"{command!r} does not accept launcher args after --")
    if args.launcher and command not in LAUNCHER_COMMANDS:
        raise ValueError(f"{command!r} does not support --launcher")
    if args.launcher and args.launcher not in LAUNCHERS:
        raise ValueError(f"unsupported launcher {args.launcher!r}; choose one of {sorted(LAUNCHERS)}")
    if command == "inference" and options.get("chat") and options.get("gradio"):
        raise ValueError("axolotl inference cannot combine --chat and --gradio")
    if command == "fetch" and args.config and args.config not in FETCH_TARGETS:
        raise ValueError(f"fetch target must be one of {sorted(FETCH_TARGETS)}")
    if command == "agent-docs" and args.config and args.config.startswith("--"):
        raise ValueError("agent-docs topic must not start with --; use options JSON for flags")

    argv = ["axolotl", command]

    if command == "fetch":
        if not args.config:
            raise ValueError("fetch requires one target: examples, deepspeed_configs, or docs")
        argv.append(args.config)
    elif command == "agent-docs":
        if args.config:
            argv.append(args.config)
    elif command == "config-schema":
        if args.config:
            raise ValueError("config-schema does not accept a config path")
    else:
        add_config(argv, args.config, command, args.skip_config_exists_check)

    if args.launcher:
        argv.extend(["--launcher", args.launcher])

    append_options(argv, options)

    if launcher_args:
        argv.append("--")
        argv.extend(launcher_args)

    argv.extend(trailing_args)
    return argv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an Axolotl CLI argv and safely quoted shell command without executing it."
    )
    parser.add_argument("config", nargs="?", help="Config path, fetch target, or agent-docs topic depending on command")
    parser.add_argument("--command", default="train", choices=sorted(ALL_COMMANDS))
    parser.add_argument("--launcher", choices=sorted(LAUNCHERS), help="Launcher for train/evaluate/inference/merge-sharded-fsdp-weights")
    parser.add_argument("--options-json", default="{}", help="JSON object of Axolotl CLI options, using snake_case or dash-case keys")
    parser.add_argument("--launcher-args-json", default="[]", help="JSON array of launcher args to place after the standalone --")
    parser.add_argument("--trailing-args-json", default="[]", help="JSON array appended at the end for rare command-specific positional needs")
    parser.add_argument("--skip-config-exists-check", action="store_true", help="Allow building a command for a config path that does not exist on this machine")
    parser.add_argument("--json", action="store_true", help="Print only the argv JSON array")
    args = parser.parse_args()

    try:
        argv = build_command(args)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(argv, indent=2))
    else:
        print("argv:")
        print(json.dumps(argv, indent=2))
        print("shell:")
        print(shlex.join(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
