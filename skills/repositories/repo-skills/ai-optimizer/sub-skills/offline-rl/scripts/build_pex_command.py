#!/usr/bin/env python3
"""Build AI-Optimizer PEX command recipes without running training."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import List, Optional


OFFLINE_SCRIPT = "offline-rl-algorithms/E2O/PEX-main/main_offline.py"
ONLINE_SCRIPT = "offline-rl-algorithms/E2O/PEX-main/main_online.py"
ONLINE_ALGORITHMS = ("scratch", "buffer", "direct", "pex")


def shell_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def join_script(root: str, rel: str) -> str:
    root = root.strip()
    if root in ("", "."):
        return rel
    return root.rstrip("/") + "/" + rel


def add_if_value(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted PEX offline or online command recipe. The command is not executed.",
    )
    parser.add_argument("mode", choices=("offline", "online"), help="PEX stage to build")
    parser.add_argument("--env-name", required=True, help="D4RL/Gym environment name for --env_name")
    parser.add_argument("--log-dir", required=True, help="run log directory for --log_dir")
    parser.add_argument("--algorithm", choices=ONLINE_ALGORITHMS, help="online algorithm: scratch, buffer, direct, or pex")
    parser.add_argument("--ckpt-path", help="offline checkpoint path for online --ckpt_path")
    parser.add_argument("--python", default="python", help="Python executable token to place at the front of the command")
    parser.add_argument("--script-root", default=".", help="optional prefix for a target checkout root; default emits relative paths")
    parser.add_argument("--cuda-visible-devices", help="optional CUDA_VISIBLE_DEVICES value to prefix in the printed command")

    # Common PEX flags.
    parser.add_argument("--seed", type=int, default=1, help="seed to include; default 1 for explicit reproducibility")
    parser.add_argument("--discount", type=float, help="discount factor")
    parser.add_argument("--hidden-dim", type=int, help="network hidden_dim")
    parser.add_argument("--hidden-num", type=int, help="network hidden_num")
    parser.add_argument("--batch-size", type=int, help="batch size")
    parser.add_argument("--learning-rate", type=float, help="learning rate")
    parser.add_argument("--target-update-rate", type=float, help="target update rate")
    parser.add_argument("--tau", type=float, default=0.7, help="IQL/PEX tau; default 0.7")
    parser.add_argument("--beta", type=float, default=10.0, help="IQL inverse temperature; default 10.0")
    parser.add_argument("--eval-period", type=int, default=1000, help="evaluation period; default 1000")
    parser.add_argument("--eval-episode-num", type=int, help="evaluation episode count; default depends on mode")
    parser.add_argument("--max-episode-steps", type=int, default=1000, help="max episode steps; default 1000")

    # Offline-only.
    parser.add_argument("--num-steps", type=int, help="offline maximum training steps")

    # Online-only.
    parser.add_argument("--replay-size", type=int, help="online replay size")
    parser.add_argument("--total-env-steps", type=int, help="online total environment steps")
    parser.add_argument("--initial-collection-steps", type=int, help="initial online collection steps")
    parser.add_argument("--updates-per-step", type=int, help="model updates per environment step")
    parser.add_argument("--inv-temperature", type=float, default=10.0, help="PEX action-selection inverse temperature; default 10.0")
    parser.add_argument("--eval", dest="eval_flag", choices=("True", "False"), help="online --eval flag string")

    parser.add_argument("--json", action="store_true", help="print JSON with command and metadata instead of only the command")
    return parser


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    args = build_parser().parse_args()

    if args.mode == "offline":
        if args.algorithm:
            fail("--algorithm is only valid for online mode")
        if args.ckpt_path:
            fail("--ckpt-path is only consumed by online mode")
        script = OFFLINE_SCRIPT
        eval_episode_num = args.eval_episode_num if args.eval_episode_num is not None else 100
    else:
        if not args.algorithm:
            fail("online mode requires --algorithm")
        if not args.ckpt_path:
            fail("online mode requires --ckpt-path for explicit offline-to-online handoff")
        script = ONLINE_SCRIPT
        eval_episode_num = args.eval_episode_num if args.eval_episode_num is not None else 10

    command: List[str] = []
    if args.cuda_visible_devices is not None:
        command.append(f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}")
    command.extend([args.python, join_script(args.script_root, script)])

    if args.mode == "online":
        command.extend(["--algorithm", args.algorithm])

    command.extend(["--env_name", args.env_name, "--log_dir", args.log_dir])
    command.extend(["--seed", str(args.seed), "--tau", str(args.tau), "--beta", str(args.beta)])
    command.extend(["--eval_period", str(args.eval_period), "--eval_episode_num", str(eval_episode_num)])
    command.extend(["--max_episode_steps", str(args.max_episode_steps)])

    add_if_value(command, "--discount", args.discount)
    add_if_value(command, "--hidden_dim", args.hidden_dim)
    add_if_value(command, "--hidden_num", args.hidden_num)
    add_if_value(command, "--batch_size", args.batch_size)
    add_if_value(command, "--learning_rate", args.learning_rate)
    add_if_value(command, "--target_update_rate", args.target_update_rate)

    if args.mode == "offline":
        add_if_value(command, "--num_steps", args.num_steps)
        notes = [
            "Offline PEX trains IQL and saves an offline_ckpt under the selected log directory.",
        ]
    else:
        command.extend(["--ckpt_path", args.ckpt_path])
        add_if_value(command, "--replay_size", args.replay_size)
        add_if_value(command, "--total_env_steps", args.total_env_steps)
        add_if_value(command, "--initial_collection_steps", args.initial_collection_steps)
        add_if_value(command, "--updates_per_step", args.updates_per_step)
        command.extend(["--inv_temperature", str(args.inv_temperature)])
        add_if_value(command, "--eval", args.eval_flag)
        notes = [
            "Online PEX consumes an offline checkpoint handoff; this builder requires --ckpt-path even for modes whose source code can start without one.",
        ]

    notes.append("This builder only prints a command recipe; it does not create log directories, run training, or validate dependencies.")
    notes.append("Use the standard CUDA_VISIBLE_DEVICES spelling if GPU selection is needed.")

    if args.json:
        print(json.dumps({"mode": args.mode, "command": command, "shell": shell_join(command), "notes": notes}, indent=2))
    else:
        print(shell_join(command))
        for note in notes:
            print(f"note: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
