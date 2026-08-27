#!/usr/bin/env python3
"""Inspect the live SMARTS interface, controller, and environment contracts.

This helper is read-only, works from an arbitrary current directory, and does
not require a scenario. It is intentionally limited to imports, signatures,
enums, and formatted action spaces.
"""

from __future__ import annotations

import argparse
import inspect
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _space_text(space: Any) -> str:
    return repr(space).replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect installed SMARTS interfaces without running a scenario."
    )
    parser.add_argument(
        "--preset",
        choices=("all", "Buddha", "Full", "Standard", "Laner", "Loner", "Tagger", "StandardWithAbsoluteSteering", "LanerWithSpeed", "Tracker", "Boid", "MPCTracker", "TrajectoryInterpolator", "Direct"),
        default="all",
        help="Print one AgentType preset or all presets (default: all).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a compact JSON report instead of the human-readable report.",
    )
    args = parser.parse_args()

    try:
        distribution = version("smarts")
    except PackageNotFoundError:
        distribution = "not-installed"

    from smarts.core.agent_interface import AgentInterface, AgentType
    from smarts.core.controllers import ActionSpaceType, Controllers
    from smarts.env.configs.base_config import EnvironmentConfiguration
    from smarts.env.configs.hiway_env_configs import (
        EnvReturnMode,
        HiWayEnvV1Configuration,
        ScenarioOrder,
        SumoOptions,
    )
    from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1
    from smarts.env.utils.action_conversion import ActionOptions, get_formatters

    selected = list(AgentType) if args.preset == "all" else [AgentType[args.preset]]
    presets = []
    for preset in selected:
        interface = AgentInterface.from_type(preset)
        action_type = interface.action
        presets.append(
            {
                "name": preset.name,
                "value": preset.value,
                "action": action_type.name if action_type else None,
                "requires_rendering": interface.requires_rendering,
                "action_shape": repr(Controllers.get_action_shape(action_type))
                if action_type is not None
                else None,
                "formatted_space": _space_text(get_formatters()[action_type].space)
                if action_type is not None
                else None,
            }
        )

    report = {
        "distribution": distribution,
        "signatures": {
            "AgentInterface": str(inspect.signature(AgentInterface)),
            "AgentInterface.from_type": str(inspect.signature(AgentInterface.from_type)),
            "HiWayEnvV1": str(inspect.signature(HiWayEnvV1)),
            "EnvironmentConfiguration": str(inspect.signature(EnvironmentConfiguration)),
            "HiWayEnvV1Configuration": str(inspect.signature(HiWayEnvV1Configuration)),
            "SumoOptions": str(inspect.signature(SumoOptions)),
        },
        "enums": {
            "AgentType": [(item.name, item.value) for item in AgentType],
            "ActionSpaceType": [(item.name, item.value) for item in ActionSpaceType],
            "ScenarioOrder": [(item.name, item.value) for item in ScenarioOrder],
            "EnvReturnMode": [(item.name, item.value) for item in EnvReturnMode],
            "ActionOptions": [(item.name, item.value) for item in ActionOptions],
        },
        "presets": presets,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"SMARTS distribution: {report['distribution']}")
    for name, signature in report["signatures"].items():
        print(f"{name}: {signature}")
    for name, members in report["enums"].items():
        print(f"{name}: " + ", ".join(f"{key}={value}" for key, value in members))
    print("AgentType presets:")
    for preset in presets:
        print(
            f"  {preset['name']}: action={preset['action']}, "
            f"rendering={preset['requires_rendering']}, "
            f"space={preset['formatted_space']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
