#!/usr/bin/env python3
"""Inspect PettingZoo tutorial integration requirement groups without installing anything."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RequirementGroup:
    summary: str
    requirements: tuple[str, ...]
    import_modules: tuple[str, ...]
    notes: tuple[str, ...]


GROUPS: dict[str, RequirementGroup] = {
    "cleanrl": RequirementGroup(
        summary="CleanRL-style PPO on Pistonball/Atari Parallel environments.",
        requirements=(
            "pettingzoo[butterfly,atari,testing]>=1.24.0",
            "SuperSuit>=3.9.0",
            "tensorboard>=2.11.2",
            "torch>=1.13.1",
            "imageio",
            "imageio-ffmpeg",
        ),
        import_modules=("pettingzoo", "supersuit", "torch", "tensorboard", "imageio"),
        notes=(
            "Training loops are compute-heavy and may write logs/checkpoints.",
            "WandB/video/GPU paths in advanced recipes require explicit opt-in.",
        ),
    ),
    "tianshou": RequirementGroup(
        summary="Tianshou DQN with PettingZoo AEC environments such as Tic-Tac-Toe.",
        requirements=(
            "numpy<2.0.0",
            "pettingzoo[classic]>=1.23.0",
            "packaging>=21.3",
            "tianshou==0.5.0",
        ),
        import_modules=("numpy", "pettingzoo", "packaging", "tianshou"),
        notes=(
            "Tutorial pins an older Tianshou release; wrapper APIs may differ in newer versions.",
            "Use import/wrapper smoke checks before training.",
        ),
    ),
    "sb3-action-mask": RequirementGroup(
        summary="Stable-Baselines3 MaskablePPO action masking for Connect Four.",
        requirements=(
            "pettingzoo[classic]>=1.24.0",
            "stable-baselines3>=2.0.0",
            "sb3-contrib>=2.0.0",
        ),
        import_modules=("pettingzoo", "stable_baselines3", "sb3_contrib"),
        notes=(
            "SB3 is single-agent; the recipe uses a custom current-agent adapter.",
            "The tutorial notes Gymnasium compatibility caveats for some versions.",
        ),
    ),
    "sb3-vector": RequirementGroup(
        summary="Stable-Baselines3 shared-policy vector recipe via SuperSuit.",
        requirements=(
            "pettingzoo[butterfly]>=1.24.0",
            "stable-baselines3>=2.0.0",
            "supersuit>=3.9.0",
        ),
        import_modules=("pettingzoo", "stable_baselines3", "supersuit"),
        notes=(
            "Use Parallel environments before SuperSuit vector conversion.",
            "The Pistonball vector tutorial is documented as fragile due to SuperSuit issues.",
        ),
    ),
    "rllib": RequirementGroup(
        summary="Ray/RLlib PPO or DQN for PettingZoo Parallel/AEC environments.",
        requirements=(
            "pettingzoo[classic,butterfly]>=1.24.0",
            "Pillow>=9.4.0",
            "ray[rllib]==2.55.0",
            "SuperSuit>=3.9.0",
            "torch>=1.13.1",
            "tensorflow-probability>=0.19.0",
        ),
        import_modules=("pettingzoo", "PIL", "ray", "supersuit", "torch", "tensorflow_probability"),
        notes=(
            "Ray startup, rollout workers, checkpoints, and storage paths are side-effectful.",
            "Use config review/import checks before launching training.",
        ),
    ),
    "agilerl": RequirementGroup(
        summary="AgileRL DQN curriculum/self-play, MADDPG, and MATD3 recipes.",
        requirements=(
            "agilerl==2.2.1; python_version >= '3.10' and python_version < '3.12'",
            "pettingzoo[classic,atari]>=1.23.1",
            "mpe2>=1.0.0",
            "AutoROM>=0.6.1",
            "SuperSuit>=3.9.0",
            "torch>=2.0.1",
            "numpy>=1.24.2",
            "tqdm>=4.65.0",
            "fastrand==1.3.0",
            "gymnasium>=0.28.1",
            "imageio>=2.31.1",
            "Pillow>=9.5.0",
            "PyYAML>=5.4.1",
        ),
        import_modules=(
            "agilerl",
            "pettingzoo",
            "mpe2",
            "AutoROM",
            "supersuit",
            "torch",
            "numpy",
            "tqdm",
            "fastrand",
            "gymnasium",
            "imageio",
            "PIL",
            "yaml",
        ),
        notes=(
            "AgileRL tutorial support is constrained to Python >=3.10,<3.12.",
            "Atari/AutoROM, pretrained weights, render scripts, and GPU use are opt-in.",
        ),
    ),
    "langchain": RequirementGroup(
        summary="LangChain LLM agents interacting through PettingZoo AEC loops.",
        requirements=(
            "pettingzoo[classic]",
            "langchain",
            "openai",
            "tenacity",
        ),
        import_modules=("pettingzoo", "langchain", "openai", "tenacity"),
        notes=(
            "Hosted LLM calls require user-approved credentials and network access.",
            "Use mocks or random masked fallback for local loop validation.",
        ),
    ),
}

ALIASES = {
    "sb3": "sb3-action-mask",
    "stable-baselines3": "sb3-action-mask",
    "ray": "rllib",
    "ray-rllib": "rllib",
    "clean-rl": "cleanrl",
}

EXTRA_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?")


def normalize_group(name: str) -> str:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in GROUPS:
        choices = ", ".join(sorted(GROUPS))
        raise SystemExit(f"Unknown group {name!r}. Choose one of: {choices}")
    return key


def selected_groups(names: Iterable[str] | None) -> dict[str, RequirementGroup]:
    if not names:
        return GROUPS
    normalized = []
    for name in names:
        if name.lower() == "all":
            return GROUPS
        normalized.append(normalize_group(name))
    return {name: GROUPS[name] for name in normalized}


def base_requirement_name(requirement: str) -> str:
    before_marker = requirement.split(";", 1)[0].strip()
    match = EXTRA_RE.match(before_marker)
    if not match:
        return before_marker
    return match.group(1)


def check_module(module: str) -> dict[str, object]:
    spec = importlib.util.find_spec(module)
    return {"module": module, "importable": spec is not None}


def group_payload(groups: dict[str, RequirementGroup], check_imports: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "python": {
            "version": sys.version.split()[0],
            "executable_hidden": True,
        },
        "groups": {},
        "side_effects": "none: this script does not install packages, run training, open network connections, or write files",
    }
    group_data = payload["groups"]
    assert isinstance(group_data, dict)
    for name, group in groups.items():
        entry: dict[str, object] = {
            "summary": group.summary,
            "requirements": list(group.requirements),
            "base_requirement_names": [base_requirement_name(req) for req in group.requirements],
            "import_modules": list(group.import_modules),
            "notes": list(group.notes),
        }
        if check_imports:
            entry["import_checks"] = [check_module(module) for module in group.import_modules]
        group_data[name] = entry
    return payload


def print_text(payload: dict[str, object], show_imports: bool) -> None:
    print("PettingZoo training integration requirement groups")
    print(f"Python: {payload['python']['version']}")
    print(f"Side effects: {payload['side_effects']}")
    print()
    groups = payload["groups"]
    assert isinstance(groups, dict)
    for name, entry_obj in groups.items():
        entry = entry_obj
        assert isinstance(entry, dict)
        print(f"[{name}] {entry['summary']}")
        print("  Requirements:")
        for requirement in entry["requirements"]:
            print(f"    - {requirement}")
        print("  Import modules:")
        for module in entry["import_modules"]:
            print(f"    - {module}")
        if show_imports:
            print("  Local import checks:")
            for check in entry.get("import_checks", []):
                status = "ok" if check["importable"] else "missing"
                print(f"    - {check['module']}: {status}")
        print("  Notes:")
        for note in entry["notes"]:
            print(f"    - {note}")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print known PettingZoo tutorial integration requirement groups and "
            "optionally check whether their import modules are available locally."
        )
    )
    parser.add_argument(
        "groups",
        nargs="*",
        help="Requirement groups to show: all, cleanrl, tianshou, sb3-action-mask, sb3-vector, rllib, agilerl, langchain.",
    )
    parser.add_argument(
        "--groups",
        action="store_true",
        dest="list_groups",
        help="List group names and exit.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check whether each group's known import modules can be found locally. This does not import or execute them.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_groups:
        for name, group in GROUPS.items():
            print(f"{name}: {group.summary}")
        return 0

    groups = selected_groups(args.groups)
    payload = group_payload(groups, args.check_imports)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload, args.check_imports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
