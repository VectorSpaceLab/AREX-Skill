#!/usr/bin/env python3
"""Build safe RL Baselines3 Zoo training commands without launching training.

This helper is intentionally non-executing. It prints a shell-quoted command for
`python -m rl_zoo3.train` or `rl_zoo3 train` and validates the most common
unsafe combinations before returning.

Examples:
    python scripts/train_command_builder.py --algo ppo --env CartPole-v1 \
      --log-folder ./runs/rl-zoo-smoke --n-timesteps 1000 --eval-freq 500 \
      --save-freq 500 --seed 123 --device cpu --progress

    python scripts/train_command_builder.py --command-style console \
      --algo sac --env Pendulum-v1 --log-folder ./runs/sac-buffer \
      --trained-agent ./runs/sac-buffer/sac/Pendulum-v1_1/Pendulum-v1.zip \
      --allow-missing-files --expect-replay-buffer --save-replay-buffer
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Iterable

ALGOS = [
    "a2c",
    "ars",
    "crossq",
    "ddpg",
    "dqn",
    "ppo",
    "ppo_lstm",
    "qrdqn",
    "sac",
    "td3",
    "tqc",
    "trpo",
]
ON_POLICY = {"a2c", "ars", "ppo", "ppo_lstm", "trpo"}
OFF_POLICY = {"crossq", "ddpg", "dqn", "qrdqn", "sac", "td3", "tqc"}


def add_flag(command: list[str], flag: str, value: str | None) -> None:
    if value not in (None, ""):
        command.extend([flag, value])


def extend_tokens(command: list[str], flag: str, values: Iterable[str] | None) -> None:
    if values:
        command.append(flag)
        command.extend(values)


def build_command(args: argparse.Namespace) -> tuple[list[str], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    if args.command_style == "module":
        command = ["python", "-m", "rl_zoo3.train"]
    else:
        command = ["rl_zoo3", "train"]
        warnings.append(
            "console style may fail unless the rl_zoo3 console router imports successfully; use the module style for base installs"
        )

    command.extend(["--algo", args.algo, "--env", args.env])

    add_flag(command, "--n-timesteps", args.n_timesteps)
    add_flag(command, "--log-folder", args.log_folder)
    add_flag(command, "--eval-freq", args.eval_freq)
    add_flag(command, "--eval-episodes", args.eval_episodes)
    add_flag(command, "--n-eval-envs", args.n_eval_envs)
    add_flag(command, "--save-freq", args.save_freq)
    add_flag(command, "--trained-agent", args.trained_agent)
    add_flag(command, "--vec-env", args.vec_env)
    add_flag(command, "--device", args.device)
    add_flag(command, "--seed", args.seed)
    add_flag(command, "--num-threads", args.num_threads)
    add_flag(command, "--conf-file", args.conf_file)

    if args.save_replay_buffer:
        command.append("--save-replay-buffer")
        if args.algo in ON_POLICY:
            warnings.append(f"--save-replay-buffer has no effect for on-policy algo {args.algo}")
    if args.progress:
        command.append("--progress")
    if args.uuid:
        command.append("--uuid")
    if args.track:
        command.append("--track")
        if args.wandb_project_name:
            add_flag(command, "--wandb-project-name", args.wandb_project_name)
        add_flag(command, "--wandb-entity", args.wandb_entity)
        add_flag(command, "--wandb-group", args.wandb_group)
        extend_tokens(command, "--wandb-tags", args.wandb_tags)
    elif any([args.wandb_project_name, args.wandb_entity, args.wandb_group, args.wandb_tags]):
        warnings.append("W&B flags were provided without --track; they will be ignored by the real CLI")

    extend_tokens(command, "--gym-packages", args.gym_packages)
    extend_tokens(command, "--env-kwargs", args.env_kwargs)
    extend_tokens(command, "--eval-env-kwargs", args.eval_env_kwargs)
    extend_tokens(command, "--hyperparams", args.hyperparams)

    if args.trained_agent:
        trained_agent = Path(args.trained_agent)
        if trained_agent.suffix != ".zip":
            errors.append("--trained-agent must end in .zip")
        if not args.allow_missing_files and not trained_agent.is_file():
            errors.append(f"trained agent file not found: {trained_agent}")
        if args.expect_replay_buffer:
            replay_buffer = trained_agent.with_name("replay_buffer.pkl")
            if not args.allow_missing_files and not replay_buffer.is_file():
                errors.append(f"expected replay buffer not found next to trained agent: {replay_buffer}")
            elif args.allow_missing_files and not replay_buffer.is_file():
                warnings.append(f"replay buffer not present yet: {replay_buffer}")
    elif args.expect_replay_buffer:
        warnings.append("--expect-replay-buffer was set without --trained-agent")

    if args.save_replay_buffer and args.algo not in OFF_POLICY:
        warnings.append(
            f"--save-replay-buffer is usually meaningful for off-policy algorithms; {args.algo} is not in the off-policy set"
        )

    if not args.log_folder:
        errors.append("--log-folder is required for a safe training command plan")

    return command, warnings, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command-style", choices=["module", "console"], default="module")
    parser.add_argument("--algo", choices=ALGOS, required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--n-timesteps")
    parser.add_argument("--log-folder", required=True)
    parser.add_argument("--eval-freq")
    parser.add_argument("--eval-episodes")
    parser.add_argument("--n-eval-envs")
    parser.add_argument("--save-freq")
    parser.add_argument("--trained-agent")
    parser.add_argument("--save-replay-buffer", action="store_true")
    parser.add_argument("--expect-replay-buffer", action="store_true")
    parser.add_argument("--vec-env", choices=["dummy", "subproc"])
    parser.add_argument("--device")
    parser.add_argument("--seed")
    parser.add_argument("--num-threads")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--gym-packages", nargs="+")
    parser.add_argument("--env-kwargs", nargs="+")
    parser.add_argument("--eval-env-kwargs", nargs="+")
    parser.add_argument("--hyperparams", nargs="+")
    parser.add_argument("--conf-file")
    parser.add_argument("--uuid", action="store_true")
    parser.add_argument("--track", action="store_true")
    parser.add_argument("--wandb-project-name")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-group")
    parser.add_argument("--wandb-tags", nargs="+")
    parser.add_argument("--allow-missing-files", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a shell command")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command, warnings, errors = build_command(args)
    payload = {
        "command": shlex.join(command),
        "argv": command,
        "warnings": warnings,
        "errors": errors,
        "command_style": args.command_style,
        "algo": args.algo,
        "env": args.env,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["command"])
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
