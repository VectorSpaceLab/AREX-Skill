#!/usr/bin/env python3
"""Build a safe easy-MARL training command without running training.

The helper validates the inspected AI-Optimizer easy-MARL algorithm/environment
compatibility matrix, requires explicit scenario names for scenario-aware
families, and prints one shell-quoted command. It intentionally does not import
PyTorch, Gym, tensorboardX, or the source package.

Examples:
  python scripts/build_easy_marl_command.py --agent-name IDQN --env-name discrete_meeting
  python scripts/build_easy_marl_command.py --agent-name MAPPO --env-name continuous_mpe --scenario-name simple_tag
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Dict, Iterable, List, Mapping, Sequence, Set


FAMILY_BY_AGENT: Mapping[str, str] = {
    "IDQN": "dqn",
    "VDN": "dqn",
    "QMIX": "dqn",
    "CommNet": "dqn",
    "IDDPG": "ddpg",
    "MADDPG": "ddpg",
    "IPPO": "ppo",
    "MAPPO": "ppo",
}

ENTRY_BY_FAMILY: Mapping[str, str] = {
    "dqn": "main_dqn.py",
    "ddpg": "main_ddpg.py",
    "ppo": "main_ppo.py",
}

ALLOWED_ENVIRONMENTS_BY_FAMILY: Mapping[str, Set[str]] = {
    "dqn": {"discrete_meeting", "discrete_magym"},
    "ddpg": {"continuous_meeting", "continuous_mpe"},
    "ppo": {"discrete_meeting", "discrete_magym", "continuous_meeting", "continuous_mpe"},
}

SCENARIO_SUGGESTIONS: Mapping[str, Sequence[str]] = {
    "discrete_magym": ("Switch4-v0", "Combat-v0"),
    "continuous_mpe": ("simple_tag", "simple_spread"),
}

ALL_ENVIRONMENTS: Sequence[str] = (
    "discrete_meeting",
    "discrete_magym",
    "continuous_meeting",
    "continuous_mpe",
)

PARTIALLY_WIRED_AGENTS: Mapping[str, str] = {
    "CommNet": (
        "CommNet has a DQN entry-script branch and source class, but the inspected "
        "hyperparameter dispatcher lacks CommNet modules and its train method needs "
        "alignment with the current Buffer.sample() dictionary contract."
    )
}


def _format_choices(values: Iterable[str]) -> str:
    return ", ".join(sorted(values))


def build_command(python_executable: str, agent_name: str, env_name: str, scenario_name: str | None) -> List[str]:
    family = FAMILY_BY_AGENT[agent_name]
    allowed_envs = ALLOWED_ENVIRONMENTS_BY_FAMILY[family]
    if env_name not in allowed_envs:
        raise ValueError(
            f"{agent_name} ({family}) is not compatible with {env_name}. "
            f"Allowed environments for this family: {_format_choices(allowed_envs)}."
        )

    if env_name in SCENARIO_SUGGESTIONS and not scenario_name:
        suggestions = ", ".join(SCENARIO_SUGGESTIONS[env_name])
        raise ValueError(
            f"--scenario-name is required for {env_name}. "
            f"Examples from the easy-MARL README/source: {suggestions}."
        )

    command = [python_executable, ENTRY_BY_FAMILY[family], "--agent-name", agent_name, "--env-name", env_name]
    if scenario_name:
        command.extend(["--scenario-name", scenario_name])
    return command


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted AI-Optimizer easy-MARL command after validating agent/env/scenario compatibility."
    )
    parser.add_argument("--agent-name", required=True, choices=sorted(FAMILY_BY_AGENT), help="easy-MARL agent name")
    parser.add_argument("--env-name", required=True, choices=ALL_ENVIRONMENTS, help="easy-MARL environment family")
    parser.add_argument("--scenario-name", default=None, help="required for discrete_magym and continuous_mpe")
    parser.add_argument("--python", default="python", help="Python executable to place at the start of the printed command")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    parser_args = parse_args(argv)
    scenario_name = parser_args.scenario_name
    if scenario_name is not None and scenario_name.strip() == "":
        scenario_name = None

    try:
        command = build_command(parser_args.python, parser_args.agent_name, parser_args.env_name, scenario_name)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if parser_args.env_name not in SCENARIO_SUGGESTIONS and scenario_name:
        print(
            f"warning: {parser_args.env_name} does not use scenario names; the source parser accepts the option, "
            "but the meeting hyperparameter path ignores it.",
            file=sys.stderr,
        )

    if parser_args.agent_name in PARTIALLY_WIRED_AGENTS:
        print(f"warning: {PARTIALLY_WIRED_AGENTS[parser_args.agent_name]}", file=sys.stderr)

    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
