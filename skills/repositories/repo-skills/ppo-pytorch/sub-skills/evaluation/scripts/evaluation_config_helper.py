#!/usr/bin/env python3
"""Resolve PPO evaluation checkpoints and configuration safely.

This helper mirrors the repository's `test.py` path and configuration logic
without importing Gym, Roboschool, or running environment rollouts by default.
It is intended for path validation, preset discovery, and optional trusted
checkpoint inspection.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


PRESETS: Dict[str, Dict[str, Any]] = {
    "CartPole-v1": {
        "continuous": False,
        "max_ep_len": 400,
        "action_std": None,
        "dependency_family": "Gym classic control",
        "notes": "Discrete policy; `action_std` should stay None.",
    },
    "LunarLander-v2": {
        "continuous": False,
        "max_ep_len": 300,
        "action_std": None,
        "dependency_family": "Gym Box2D / gym[box2d]",
        "notes": "Discrete policy; requires a Box2D-capable installation.",
    },
    "BipedalWalker-v2": {
        "continuous": True,
        "max_ep_len": 1500,
        "action_std": 0.1,
        "dependency_family": "Gym Box2D / gym[box2d]",
        "notes": "Continuous pretrained policy; use the saved-run action_std.",
    },
    "RoboschoolHalfCheetah-v1": {
        "continuous": True,
        "max_ep_len": 1000,
        "action_std": 0.1,
        "dependency_family": "legacy Gym + Roboschool",
        "notes": "Legacy Roboschool environment; import/register the package before gym.make.",
    },
    "RoboschoolHopper-v1": {
        "continuous": True,
        "max_ep_len": 1000,
        "action_std": 0.1,
        "dependency_family": "legacy Gym + Roboschool",
        "notes": "Legacy Roboschool environment; import/register the package before gym.make.",
    },
    "RoboschoolWalker2d-v1": {
        "continuous": True,
        "max_ep_len": 1000,
        "action_std": 0.1,
        "dependency_family": "legacy Gym + Roboschool",
        "notes": "Default native evaluation target in test.py.",
    },
}

CHECKPOINT_NAME_RE = re.compile(
    r"^PPO_(?P<env>.+)_(?P<seed>\d+)_(?P<run>\d+)\.pth$"
)


@dataclass
class Resolution:
    env_name: Optional[str]
    checkpoint_root: Optional[str]
    checkpoint_path: Optional[str]
    checkpoint_exists: bool
    random_seed: int
    run_num: int
    continuous: Optional[bool]
    action_std: Optional[float]
    max_ep_len: Optional[int]
    episodes: int
    render: bool
    frame_delay: float
    warnings: List[str]
    preset: Optional[Dict[str, Any]] = None
    inferred_from_checkpoint: Optional[Dict[str, Any]] = None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve PPO evaluation checkpoint paths and configuration safely.",
    )
    parser.add_argument("--env-name", help="Environment name such as RoboschoolWalker2d-v1.")
    parser.add_argument("--checkpoint-root", default="PPO_preTrained", help="Root directory containing env subfolders.")
    parser.add_argument("--checkpoint-path", help="Explicit checkpoint path, bypassing the default naming convention.")
    parser.add_argument("--random-seed", type=int, default=0, help="Random seed component in the native checkpoint name.")
    parser.add_argument("--run-num", type=int, default=0, help="Run index component in the native checkpoint name.")
    parser.add_argument(
        "--continuous",
        choices=["auto", "true", "false"],
        default="auto",
        help="Override the action-space class when the preset is not enough.",
    )
    parser.add_argument("--action-std", type=float, help="Continuous action_std value for policy construction.")
    parser.add_argument("--max-ep-len", type=int, help="Maximum steps per evaluation episode.")
    parser.add_argument("--episodes", type=int, default=10, help="Number of evaluation episodes to average.")
    parser.add_argument("--render", action="store_true", help="Request human rendering in the rollout plan.")
    parser.add_argument("--frame-delay", type=float, default=0.0, help="Delay between frames when rendering.")
    parser.add_argument("--check-file", action="store_true", help="Require the resolved checkpoint file to exist.")
    parser.add_argument("--inspect-checkpoint", action="store_true", help="Inspect a trusted checkpoint state dict with torch.load.")
    parser.add_argument("--list-presets", action="store_true", help="List the built-in pretrained environment presets.")
    parser.add_argument("--json", action="store_true", help="Emit the resolution as JSON only.")
    return parser


def _bool_from_choice(value: str) -> Optional[bool]:
    if value == "auto":
        return None
    return value == "true"


def _default_checkpoint_path(checkpoint_root: Optional[str], env_name: Optional[str], seed: int, run_num: int) -> Optional[str]:
    if not env_name:
        return None
    root = Path(checkpoint_root or "PPO_preTrained")
    return str(root / env_name / f"PPO_{env_name}_{seed}_{run_num}.pth")


def _parse_checkpoint_name(path: Path) -> Dict[str, Any]:
    match = CHECKPOINT_NAME_RE.match(path.name)
    if not match:
        return {}
    return {
        "env_name": match.group("env"),
        "random_seed": int(match.group("seed")),
        "run_num": int(match.group("run")),
    }


def _load_torch_state_dict(path: Path) -> Dict[str, Any]:
    import torch

    try:
        state = torch.load(path, map_location=lambda storage, loc: storage, weights_only=False)
    except TypeError:
        state = torch.load(path, map_location=lambda storage, loc: storage)
    if not isinstance(state, dict):
        raise TypeError(f"expected a state-dict-like mapping, got {type(state).__name__}")
    return state


def _inspect_state_dict(path: Path) -> Dict[str, Any]:
    state = _load_torch_state_dict(path)
    report: Dict[str, Any] = {
        "key_count": len(state),
        "keys": sorted(state.keys()),
        "path": str(path),
    }
    actor0 = state.get("actor.0.weight")
    actor4 = state.get("actor.4.weight")
    critic0 = state.get("critic.0.weight")
    if actor0 is not None:
        report["state_dim"] = int(actor0.shape[1])
    if actor4 is not None:
        report["action_dim"] = int(actor4.shape[0])
    if critic0 is not None:
        report["critic_state_dim"] = int(critic0.shape[1])
    report["has_action_var"] = any(key.startswith("action_var") for key in state)
    return report


def resolve(args: argparse.Namespace) -> Resolution:
    warnings: List[str] = []
    preset = PRESETS.get(args.env_name) if args.env_name else None

    continuous = _bool_from_choice(args.continuous)
    if continuous is None and preset is not None:
        continuous = bool(preset["continuous"])
    elif continuous is None and preset is None and args.env_name is not None:
        warnings.append(f"No built-in preset for {args.env_name!r}; supply --continuous, --action-std, and --max-ep-len explicitly.")

    action_std = args.action_std
    if action_std is None and preset is not None:
        action_std = preset["action_std"]
    if continuous is True and action_std is None:
        warnings.append("Continuous policies need an action_std float at construction time; the pretrained runs in this repo usually use 0.1.")
    if continuous is False and action_std is not None:
        warnings.append("action_std is ignored for discrete policies.")

    max_ep_len = args.max_ep_len
    if max_ep_len is None and preset is not None:
        max_ep_len = int(preset["max_ep_len"])

    checkpoint_path = args.checkpoint_path
    if checkpoint_path is None and args.env_name is not None:
        checkpoint_path = _default_checkpoint_path(args.checkpoint_root, args.env_name, args.random_seed, args.run_num)
    elif checkpoint_path is not None and args.env_name is None:
        parsed = _parse_checkpoint_name(Path(checkpoint_path))
        if parsed.get("env_name"):
            args.env_name = parsed["env_name"]
            if args.random_seed == 0:
                args.random_seed = parsed["random_seed"]
            if args.run_num == 0:
                args.run_num = parsed["run_num"]
            preset = PRESETS.get(args.env_name)
            if continuous is None and preset is not None:
                continuous = bool(preset["continuous"])
            if max_ep_len is None and preset is not None:
                max_ep_len = int(preset["max_ep_len"])
            if action_std is None and preset is not None:
                action_std = preset["action_std"]
        else:
            warnings.append("Could not infer env name from checkpoint filename; pass --env-name explicitly.")

    resolved_path = Path(checkpoint_path) if checkpoint_path else None
    exists = resolved_path.is_file() if resolved_path else False
    if args.check_file and not exists:
        warnings.append(f"Checkpoint file not found: {checkpoint_path}")

    if resolved_path is not None and args.env_name:
        parsed = _parse_checkpoint_name(resolved_path)
        if parsed.get("env_name") and parsed["env_name"] != args.env_name:
            warnings.append(
                f"Checkpoint filename names {parsed['env_name']!r} but --env-name is {args.env_name!r}."
            )
        elif parsed.get("random_seed") is not None and parsed["random_seed"] != args.random_seed:
            warnings.append(
                f"Checkpoint filename seed is {parsed['random_seed']} but --random-seed is {args.random_seed}."
            )
        elif parsed.get("run_num") is not None and parsed["run_num"] != args.run_num:
            warnings.append(
                f"Checkpoint filename run number is {parsed['run_num']} but --run-num is {args.run_num}."
            )

    return Resolution(
        env_name=args.env_name,
        checkpoint_root=args.checkpoint_root,
        checkpoint_path=str(resolved_path) if resolved_path else None,
        checkpoint_exists=exists,
        random_seed=args.random_seed,
        run_num=args.run_num,
        continuous=continuous,
        action_std=action_std,
        max_ep_len=max_ep_len,
        episodes=args.episodes,
        render=bool(args.render),
        frame_delay=args.frame_delay,
        warnings=warnings,
        preset=preset,
    )


def emit_preset_list() -> int:
    for env_name, preset in PRESETS.items():
        continuous = "continuous" if preset["continuous"] else "discrete"
        print(f"{env_name}\t{continuous}\tmax_ep_len={preset['max_ep_len']}\taction_std={preset['action_std']}\t{preset['dependency_family']}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.list_presets:
        return emit_preset_list()

    resolution = resolve(args)

    if args.inspect_checkpoint:
        if not resolution.checkpoint_path:
            parser.error("--inspect-checkpoint requires --checkpoint-path or --env-name")
        path = Path(resolution.checkpoint_path)
        if not path.is_file():
            parser.error(f"checkpoint file does not exist: {path}")
        resolution.inferred_from_checkpoint = _inspect_state_dict(path)
        if resolution.env_name is None:
            resolution.env_name = resolution.inferred_from_checkpoint.get("env_name")

    output = asdict(resolution)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print("PPO evaluation config resolution")
        print("=" * 79)
        for key in [
            "env_name",
            "checkpoint_root",
            "checkpoint_path",
            "checkpoint_exists",
            "random_seed",
            "run_num",
            "continuous",
            "action_std",
            "max_ep_len",
            "episodes",
            "render",
            "frame_delay",
        ]:
            print(f"{key}: {getattr(resolution, key)}")
        if resolution.preset is not None:
            print(f"preset_dependency_family: {resolution.preset['dependency_family']}")
            print(f"preset_notes: {resolution.preset['notes']}")
        if resolution.inferred_from_checkpoint is not None:
            print("checkpoint_inspection:")
            for key, value in resolution.inferred_from_checkpoint.items():
                print(f"  {key}: {value}")
        if resolution.warnings:
            print("warnings:")
            for warning in resolution.warnings:
                print(f"  - {warning}")
        print("=" * 79)
        print("This helper does not run episodes, import Gym, or render frames.")

    if args.check_file and not resolution.checkpoint_exists:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
