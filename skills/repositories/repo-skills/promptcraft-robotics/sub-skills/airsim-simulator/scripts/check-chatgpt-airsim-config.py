#!/usr/bin/env python3
"""Validate the ChatGPT-AirSim sample config and related prompt files.

This script is intentionally read-only. It helps future agents confirm that a
user-supplied configuration pair looks consistent before they try to reason
about the AirSim sample runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_HELPER_NAMES = [
    "takeoff",
    "land",
    "get_drone_position",
    "fly_to",
    "fly_path",
    "set_yaw",
    "get_yaw",
    "get_position",
]

PLACEHOLDER_KEYS = {
    "",
    "api key goes here",
    "your api key here",
    "replace-me",
    "replace me",
    "changeme",
}


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}")


def check_config(path: Path) -> list[str]:
    data = read_json(path)
    issues: list[str] = []
    key = data.get("OPENAI_API_KEY")
    if key is None:
        issues.append("config missing OPENAI_API_KEY")
    elif str(key).strip().lower() in PLACEHOLDER_KEYS:
        issues.append("config still contains a placeholder OPENAI_API_KEY")
    return issues


def check_settings(path: Path, expect_mode: str | None) -> list[str]:
    data = read_json(path)
    issues: list[str] = []
    if "SettingsVersion" not in data:
        issues.append("settings missing SettingsVersion")
    if "SimMode" not in data:
        issues.append("settings missing SimMode")
    elif expect_mode and str(data.get("SimMode")).lower() != expect_mode.lower():
        issues.append(
            f"settings SimMode is {data.get('SimMode')!r}, expected {expect_mode!r}"
        )
    return issues


def check_prompt_contract(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    if not any(name in text for name in REQUIRED_HELPER_NAMES):
        issues.append("prompt does not mention the expected helper names")
    if not any(token in text.lower() for token in ["question", "clarification", "object", "allowed"]):
        issues.append("prompt does not mention the clarification or allowed-function contract")
    return issues


def check_system_prompt(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    if not any(token in text.lower() for token in ["assistant", "code", "allowed", "functions"]):
        issues.append("system prompt does not describe the assistant/function contract")
    return issues


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Path to config JSON")
    parser.add_argument("--settings", type=Path, required=True, help="Path to AirSim settings JSON")
    parser.add_argument("--prompt", type=Path, help="Optional prompt template to inspect")
    parser.add_argument("--system-prompt", type=Path, dest="system_prompt", help="Optional system prompt to inspect")
    parser.add_argument("--expect-sim-mode", default="Multirotor", help="Expected SimMode value")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if any issue is found")
    args = parser.parse_args(argv)

    issues: list[str] = []
    issues.extend(check_config(args.config))
    issues.extend(check_settings(args.settings, args.expect_sim_mode))

    if args.prompt:
        issues.extend(check_prompt_contract(args.prompt))
    if args.system_prompt:
        issues.extend(check_system_prompt(args.system_prompt))

    print("ChatGPT-AirSim preflight summary")
    print(f"- config: {args.config}")
    print(f"- settings: {args.settings}")
    print(f"- expect SimMode: {args.expect_sim_mode}")
    if args.prompt:
        print(f"- prompt: {args.prompt}")
    if args.system_prompt:
        print(f"- system prompt: {args.system_prompt}")

    if issues:
        print("- issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1 if args.strict else 0

    print("- status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
