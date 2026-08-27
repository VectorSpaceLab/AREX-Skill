#!/usr/bin/env python3
"""Resolve PPO training presets, logs, and checkpoint paths safely.

This helper mirrors the repository's native `train.py` preset and path logic
without importing Gym or starting a long training run by default.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


PRESETS: Dict[str, Dict[str, Any]] = {
    "CartPole-v1": {
        "continuous": False,
        "max_ep_len": 400,
        "max_training_timesteps": 1e5,
        "print_freq": 1600,
        "log_freq": 800,
        "save_model_freq": 20000,
        "action_std": None,
        "action_std_decay_rate": None,
        "min_action_std": None,
        "action_std_decay_freq": None,
        "update_timestep": 1600,
        "K_epochs": 40,
        "eps_clip": 0.2,
        "gamma": 0.99,
        "lr_actor": 0.0003,
        "lr_critic": 0.001,
        "notes": "Discrete classic-control preset.",
    },
    "LunarLander-v2": {
        "continuous": False,
        "max_ep_len": 300,
        "max_training_timesteps": 1e6,
        "print_freq": 2400,
        "log_freq": 600,
        "save_model_freq": 50000,
        "action_std": None,
        "action_std_decay_rate": None,
        "min_action_std": None,
        "action_std_decay_freq": None,
        "update_timestep": 900,
        "K_epochs": 30,
        "eps_clip": 0.2,
        "gamma": 0.99,
        "lr_actor": 0.0003,
        "lr_critic": 0.001,
        "notes": "Discrete Box2D preset.",
    },
    "BipedalWalker-v2": {
        "continuous": True,
        "max_ep_len": 1500,
        "max_training_timesteps": 3e6,
        "print_freq": 6000,
        "log_freq": 3000,
        "save_model_freq": 100000,
        "action_std": 0.6,
        "action_std_decay_rate": 0.05,
        "min_action_std": 0.1,
        "action_std_decay_freq": 250000,
        "update_timestep": 6000,
        "K_epochs": 80,
        "eps_clip": 0.2,
        "gamma": 0.99,
        "lr_actor": 0.0003,
        "lr_critic": 0.001,
        "notes": "Continuous Box2D preset.",
    },
    "RoboschoolHalfCheetah-v1": {
        "continuous": True,
        "max_ep_len": 1000,
        "max_training_timesteps": 3e6,
        "print_freq": 10000,
        "log_freq": 2000,
        "save_model_freq": 100000,
        "action_std": 0.6,
        "action_std_decay_rate": 0.05,
        "min_action_std": 0.1,
        "action_std_decay_freq": 250000,
        "update_timestep": 4000,
        "K_epochs": 80,
        "eps_clip": 0.2,
        "gamma": 0.99,
        "lr_actor": 0.0003,
        "lr_critic": 0.001,
        "notes": "Legacy Roboschool locomotion preset.",
    },
    "RoboschoolHopper-v1": {
        "continuous": True,
        "max_ep_len": 1000,
        "max_training_timesteps": 3e6,
        "print_freq": 10000,
        "log_freq": 2000,
        "save_model_freq": 100000,
        "action_std": 0.6,
        "action_std_decay_rate": 0.05,
        "min_action_std": 0.1,
        "action_std_decay_freq": 250000,
        "update_timestep": 4000,
        "K_epochs": 80,
        "eps_clip": 0.2,
        "gamma": 0.99,
        "lr_actor": 0.0003,
        "lr_critic": 0.001,
        "notes": "Legacy Roboschool locomotion preset.",
    },
    "RoboschoolWalker2d-v1": {
        "continuous": True,
        "max_ep_len": 1000,
        "max_training_timesteps": 3e6,
        "print_freq": 10000,
        "log_freq": 2000,
        "save_model_freq": 100000,
        "action_std": 0.6,
        "action_std_decay_rate": 0.05,
        "min_action_std": 0.1,
        "action_std_decay_freq": 250000,
        "update_timestep": 4000,
        "K_epochs": 80,
        "eps_clip": 0.2,
        "gamma": 0.99,
        "lr_actor": 0.0003,
        "lr_critic": 0.001,
        "notes": "Default native training preset in train.py.",
    },
}


@dataclass
class TrainingResolution:
    env_name: Optional[str]
    log_root: str
    checkpoint_root: str
    random_seed: int
    run_num: int
    log_dir: Optional[str]
    checkpoint_dir: Optional[str]
    log_file: Optional[str]
    checkpoint_path: Optional[str]
    create_dirs: bool
    preset: Optional[Dict[str, Any]]
    warnings: List[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve PPO training presets and output paths safely.")
    parser.add_argument("--env-name", help="Training environment name such as RoboschoolWalker2d-v1.")
    parser.add_argument("--log-root", default="PPO_logs", help="Root directory for CSV logs.")
    parser.add_argument("--checkpoint-root", default="PPO_preTrained", help="Root directory for checkpoints.")
    parser.add_argument("--random-seed", type=int, default=0, help="Random seed component in the checkpoint name.")
    parser.add_argument("--run-num", type=int, default=0, help="Run index component in the checkpoint name.")
    parser.add_argument("--create-dirs", action="store_true", help="Create the resolved log and checkpoint directories.")
    parser.add_argument("--list-presets", action="store_true", help="List the built-in training presets.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser


def resolve(args: argparse.Namespace) -> TrainingResolution:
    warnings: List[str] = []
    preset = PRESETS.get(args.env_name) if args.env_name else None
    if args.env_name and preset is None:
        warnings.append(f"No built-in preset exists for {args.env_name!r}; provide explicit overrides if you continue.")

    log_dir = str(Path(args.log_root) / args.env_name) if args.env_name else None
    checkpoint_dir = str(Path(args.checkpoint_root) / args.env_name) if args.env_name else None
    log_file = str(Path(log_dir) / f"PPO_{args.env_name}_log_{args.run_num}.csv") if log_dir else None
    checkpoint_path = (
        str(Path(checkpoint_dir) / f"PPO_{args.env_name}_{args.random_seed}_{args.run_num}.pth")
        if checkpoint_dir
        else None
    )

    if preset is not None:
        if preset["continuous"] and preset["action_std"] is None:
            warnings.append("Continuous preset is missing action_std; this should not happen in the bundled presets.")
        if not preset["continuous"] and preset["action_std"] is not None:
            warnings.append("Discrete preset unexpectedly has an action_std; this should not happen in the bundled presets.")

    return TrainingResolution(
        env_name=args.env_name,
        log_root=args.log_root,
        checkpoint_root=args.checkpoint_root,
        random_seed=args.random_seed,
        run_num=args.run_num,
        log_dir=log_dir,
        checkpoint_dir=checkpoint_dir,
        log_file=log_file,
        checkpoint_path=checkpoint_path,
        create_dirs=bool(args.create_dirs),
        preset=preset,
        warnings=warnings,
    )


def emit_presets() -> int:
    for env_name, preset in PRESETS.items():
        continuous = "continuous" if preset["continuous"] else "discrete"
        print(
            f"{env_name}\t{continuous}\tmax_ep_len={preset['max_ep_len']}\t"
            f"max_training_timesteps={preset['max_training_timesteps']}\t"
            f"update_timestep={preset['update_timestep']}\tK_epochs={preset['K_epochs']}"
        )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_presets:
        return emit_presets()
    if not args.env_name:
        parser.error("--env-name is required unless --list-presets is used")

    resolution = resolve(args)

    if resolution.create_dirs:
        if resolution.log_dir:
            Path(resolution.log_dir).mkdir(parents=True, exist_ok=True)
        if resolution.checkpoint_dir:
            Path(resolution.checkpoint_dir).mkdir(parents=True, exist_ok=True)

    payload = asdict(resolution)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("PPO training config resolution")
        print("=" * 79)
        for key in [
            "env_name",
            "log_root",
            "checkpoint_root",
            "random_seed",
            "run_num",
            "log_dir",
            "checkpoint_dir",
            "log_file",
            "checkpoint_path",
            "create_dirs",
        ]:
            print(f"{key}: {getattr(resolution, key)}")
        if resolution.preset is not None:
            print("preset:")
            for key, value in resolution.preset.items():
                print(f"  {key}: {value}")
        if resolution.warnings:
            print("warnings:")
            for warning in resolution.warnings:
                print(f"  - {warning}")
        print("=" * 79)
        print("This helper does not start the long training loop.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
