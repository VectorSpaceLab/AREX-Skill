#!/usr/bin/env python3
"""Build conservative CleanRL tiny-run commands.

The helper prints command templates only; it never imports CleanRL and never
runs training. Use it to avoid accidentally launching long default RL runs.
"""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass, replace
from typing import Sequence


@dataclass(frozen=True)
class TinyRun:
    key: str
    label: str
    script: str
    args: tuple[str, ...]
    extras: tuple[str, ...]
    notes: tuple[str, ...]

    def command_parts(self, python: str, script_override: str | None = None, extra_args: Sequence[str] = ()) -> list[str]:
        return [python, script_override or self.script, *self.args, *extra_args]


RUNS: dict[str, TinyRun] = {
    "classic-ppo": TinyRun(
        key="classic-ppo",
        label="CPU classic-control PPO smoke",
        script="cleanrl/ppo.py",
        args=("--num-envs", "1", "--num-steps", "64", "--total-timesteps", "256", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=(),
        notes=(
            "Base install candidate; representative ppo.py --help passed with CPU torch during extraction.",
            "Keep total_timesteps at least num_envs * num_steps so an update can occur.",
        ),
    ),
    "replay-classic": TinyRun(
        key="replay-classic",
        label="CPU classic-control replay smoke for DQN/C51",
        script="cleanrl/dqn.py",
        args=("--learning-starts", "10", "--total-timesteps", "16", "--buffer-size", "10", "--batch-size", "4", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=(),
        notes=(
            "Use --script cleanrl/c51.py for C51; keep learning-starts below total timesteps.",
            "The same shape is adapted from native classic-control smoke tests.",
        ),
    ),
    "classic-pqn": TinyRun(
        key="classic-pqn",
        label="CPU PQN classic-control smoke",
        script="cleanrl/pqn.py",
        args=("--num-envs", "1", "--num-steps", "64", "--total-timesteps", "256", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=(),
        notes=("PQN is on-policy-ish in shape; use small rollout settings like PPO.",),
    ),
    "atari-ppo": TinyRun(
        key="atari-ppo",
        label="Atari PPO smoke",
        script="cleanrl/ppo_atari.py",
        args=("--num-envs", "1", "--num-steps", "64", "--total-timesteps", "256", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("atari",),
        notes=(
            "Requires Atari dependencies and ROM/license setup before execution.",
            "Use NoFrameskip-v4 env ids for non-EnvPool Atari scripts.",
        ),
    ),
    "atari-replay": TinyRun(
        key="atari-replay",
        label="Atari replay smoke for DQN/C51/Rainbow/SAC/QDagger",
        script="cleanrl/dqn_atari.py",
        args=("--learning-starts", "10", "--total-timesteps", "16", "--buffer-size", "10", "--batch-size", "4", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("atari",),
        notes=(
            "Use --script for c51_atari.py, rainbow_atari.py, sac_atari.py, or qdagger variants.",
            "Requires Atari dependencies and ROM/license setup; keep replay warmup below total timesteps.",
        ),
    ),
    "jax-classic-replay": TinyRun(
        key="jax-classic-replay",
        label="JAX classic-control replay smoke",
        script="cleanrl/dqn_jax.py",
        args=("--learning-starts", "10", "--total-timesteps", "16", "--buffer-size", "10", "--batch-size", "4", "--no-track", "--no-capture-video"),
        extras=("jax",),
        notes=(
            "Requires JAX/Flax/Optax/Chex; use --script cleanrl/c51_jax.py for C51.",
            "JAX wheels are platform and accelerator specific; verify import/help before execution.",
        ),
    ),
    "continuous-ppo": TinyRun(
        key="continuous-ppo",
        label="MuJoCo continuous-control PPO smoke",
        script="cleanrl/ppo_continuous_action.py",
        args=("--env-id", "Hopper-v4", "--num-envs", "1", "--num-steps", "64", "--total-timesteps", "128", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("mujoco",),
        notes=(
            "Requires MuJoCo dependencies for Hopper-v4; use dm_control extra for dm_control/... ids.",
            "Use --script cleanrl/rpo_continuous_action.py for RPO with the same smoke shape.",
        ),
    ),
    "continuous-replay": TinyRun(
        key="continuous-replay",
        label="MuJoCo DDPG/TD3 replay smoke",
        script="cleanrl/ddpg_continuous_action.py",
        args=("--env-id", "Hopper-v4", "--learning-starts", "100", "--batch-size", "32", "--total-timesteps", "105", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("mujoco",),
        notes=(
            "Use --script cleanrl/td3_continuous_action.py or JAX variants when matching dependencies exist.",
            "This follows native smoke-test shape: warmup is just below total timesteps.",
        ),
    ),
    "continuous-sac": TinyRun(
        key="continuous-sac",
        label="MuJoCo SAC smoke",
        script="cleanrl/sac_continuous_action.py",
        args=("--env-id", "Hopper-v4", "--batch-size", "128", "--total-timesteps", "135", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("mujoco",),
        notes=("Requires MuJoCo dependencies; start without video/rendering.",),
    ),
    "procgen-ppo": TinyRun(
        key="procgen-ppo",
        label="Procgen PPO smoke",
        script="cleanrl/ppo_procgen.py",
        args=("--num-envs", "1", "--num-steps", "64", "--total-timesteps", "256", "--num-minibatches", "2", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("procgen",),
        notes=("Requires Procgen/gym3 dependencies; use --script cleanrl/ppg_procgen.py and add --n-iteration 1 for PPG.",),
    ),
    "procgen-ppg": TinyRun(
        key="procgen-ppg",
        label="Procgen PPG smoke",
        script="cleanrl/ppg_procgen.py",
        args=("--num-envs", "1", "--num-steps", "64", "--total-timesteps", "256", "--num-minibatches", "2", "--n-iteration", "1", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("procgen",),
        notes=("Requires Procgen/gym3 dependencies; reduced PPG iteration count is important for smoke runs.",),
    ),
    "envpool-ppo": TinyRun(
        key="envpool-ppo",
        label="EnvPool Atari PPO smoke",
        script="cleanrl/ppo_atari_envpool.py",
        args=("--num-envs", "8", "--num-steps", "32", "--total-timesteps", "256", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("envpool",),
        notes=(
            "Requires EnvPool; use EnvPool Atari v5 ids such as Breakout-v5.",
            "For RND, use --script cleanrl/ppo_rnd_envpool.py and add --num-iterations-obs-norm-init 1.",
        ),
    ),
    "envpool-rnd": TinyRun(
        key="envpool-rnd",
        label="EnvPool RND smoke",
        script="cleanrl/ppo_rnd_envpool.py",
        args=("--num-envs", "8", "--num-steps", "32", "--num-iterations-obs-norm-init", "1", "--total-timesteps", "256", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("envpool",),
        notes=("RND defaults are extremely large; never run defaults as a smoke test.",),
    ),
    "envpool-xla": TinyRun(
        key="envpool-xla",
        label="EnvPool XLA/JAX Atari smoke",
        script="cleanrl/ppo_atari_envpool_xla_jax.py",
        args=("--num-envs", "8", "--num-steps", "6", "--update-epochs", "1", "--num-minibatches", "1", "--total-timesteps", "256", "--no-track", "--no-capture-video"),
        extras=("envpool", "jax"),
        notes=(
            "Requires both EnvPool and JAX; diagnose missing extras before changing flags.",
            "Use --script cleanrl/ppo_atari_envpool_xla_jax_scan.py for the scan variant.",
        ),
    ),
    "pettingzoo": TinyRun(
        key="pettingzoo",
        label="PettingZoo multi-agent Atari smoke",
        script="cleanrl/ppo_pettingzoo_ma_atari.py",
        args=("--num-steps", "32", "--num-envs", "6", "--total-timesteps", "256", "--cuda", "False", "--track", "False", "--capture_video", "False"),
        extras=("pettingzoo",),
        notes=(
            "This script uses argparse booleans, so use --cuda False rather than --no-cuda.",
            "Requires PettingZoo, SuperSuit, and multi-agent ALE dependencies.",
        ),
    ),
    "ppo-trxl": TinyRun(
        key="ppo-trxl",
        label="PPO-TrXL memory-task smoke template",
        script="cleanrl/ppo_trxl/ppo_trxl.py",
        args=("--num-envs", "1", "--num-steps", "64", "--total-timesteps", "256", "--no-cuda", "--no-track", "--no-capture-video"),
        extras=("memory_gym",),
        notes=(
            "Requires PPO-TrXL nested dependencies such as memory-gym, minigrid, and einops.",
            "Start with --help if the memory-gym stack is not known to be installed.",
        ),
    ),
    "isaacgym-ppo": TinyRun(
        key="isaacgym-ppo",
        label="IsaacGym PPO bounded template",
        script="cleanrl/ppo_continuous_action_isaacgym/ppo_continuous_action_isaacgym.py",
        args=("--num-envs", "64", "--num-steps", "16", "--total-timesteps", "1024", "--no-track", "--no-capture-video"),
        extras=("isaacgym",),
        notes=(
            "Requires IsaacGym simulator stack and typically NVIDIA GPU/CUDA; do not present as CPU smoke.",
            "Verify simulator install and task assets before execution.",
        ),
    ),
}


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def list_runs() -> None:
    width = max(len(key) for key in RUNS)
    for key in sorted(RUNS):
        run = RUNS[key]
        extras = ", ".join(run.extras) if run.extras else "base"
        print(f"{key:<{width}}  {run.label}  [extras: {extras}]")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print conservative CleanRL tiny-run command templates.")
    parser.add_argument("family", nargs="?", choices=sorted(RUNS), help="Script family template to print")
    parser.add_argument("--list", action="store_true", help="List available family templates")
    parser.add_argument("--script", help="Override the script path while keeping the selected family's flags")
    parser.add_argument("--python", default="python", help="Python executable token to place at the start of the command")
    parser.add_argument("--extra-arg", action="append", default=[], help="Append one extra argument token; repeat for multiple tokens")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--command-only", action="store_true", help="Print only the shell command")
    args = parser.parse_args()

    if args.list:
        list_runs()
        return 0
    if not args.family:
        parser.error("family is required unless --list is used")

    run = RUNS[args.family]
    command_parts = run.command_parts(args.python, args.script, args.extra_arg)
    payload = {
        "family": run.key,
        "label": run.label,
        "command": shell_join(command_parts),
        "parts": command_parts,
        "extras": list(run.extras),
        "notes": list(run.notes),
        "does_not_execute": True,
    }

    if args.command_only:
        print(payload["command"])
    elif args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Family: {payload['family']} - {payload['label']}")
        print(f"Command: {payload['command']}")
        print("Required extras: " + (", ".join(payload["extras"]) if payload["extras"] else "base install only"))
        print("Notes:")
        for note in payload["notes"]:
            print(f"- {note}")
        print("This helper only prints a command; review dependencies and user intent before running it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
