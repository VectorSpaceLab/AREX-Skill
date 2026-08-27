#!/usr/bin/env python3
"""Build AI-Optimizer offline-RL command recipes without running training.

The script prints one shell-quoted command to stdout. Warnings and caveats are
printed to stderr. It never executes the generated command.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AlgoSpec:
    script: str
    selector: str  # "dataset" or "env"
    default_selector_value: str
    default_seed: int
    gpu_kind: Optional[str] = None  # "int", "bool", or None
    default_gpu: Optional[str] = None
    notes: List[str] = field(default_factory=list)


SPECS: Dict[str, AlgoSpec] = {
    "bcq": AlgoSpec(
        script="offline-rl-algorithms/BCQ/bcq-train.py",
        selector="dataset",
        default_selector_value="halfcheetah-medium-v2",
        default_seed=0,
        gpu_kind="int",
        default_gpu="0",
    ),
    "bear": AlgoSpec(
        script="offline-rl-algorithms/BEAR/bear-train.py",
        selector="dataset",
        default_selector_value="halfcheetah-expert-v0",
        default_seed=0,
        gpu_kind="int",
        default_gpu="0",
    ),
    "cql": AlgoSpec(
        script="offline-rl-algorithms/CQL/cql-train.py",
        selector="dataset",
        default_selector_value="halfcheetah-random-v2",
        default_seed=0,
        gpu_kind="int",
        default_gpu="0",
    ),
    "awac": AlgoSpec(
        script="offline-rl-algorithms/AWAC/awac-train.py",
        selector="dataset",
        default_selector_value="halfcheetah-medium-v2",
        default_seed=0,
        gpu_kind="int",
        default_gpu="0",
    ),
    "redq": AlgoSpec(
        script="offline-rl-algorithms/REDQ/redq-train.py",
        selector="env",
        default_selector_value="HalfCheetah-v2",
        default_seed=1,
        gpu_kind="bool",
        default_gpu="False",
        notes=[
            "REDQ parser uses --env and fit_online_redq; do not treat it as a pure D4RL --dataset script.",
        ],
    ),
    "uwac": AlgoSpec(
        script="offline-rl-algorithms/UWAC/uwac-train.py",
        selector="dataset",
        default_selector_value="walker2d-random-v2",
        default_seed=0,
        gpu_kind="int",
        default_gpu="0",
        notes=[
            "UWAC class evidence exists, but some checkouts may not contain the documented uwac-train.py file.",
            "If the target trainer is missing, instantiate the UWAC class through the d3rlpy-style API instead.",
        ],
    ),
    "ispi": AlgoSpec(
        script="offline-rl-algorithms/ISPI/main.py",
        selector="env",
        default_selector_value="hopper-medium-v2",
        default_seed=0,
        gpu_kind=None,
        notes=[
            "ISPI has no explicit --gpu flag; it selects CUDA automatically when available.",
        ],
    ),
    "combo": AlgoSpec(
        script="offline-rl-algorithms/COMBO/combo_main.py",
        selector="dataset",
        default_selector_value="hopper-medium-v2",
        default_seed=1,
        gpu_kind="int",
        default_gpu="0",
        notes=[
            "COMBO recipe uses the COMBO-specific entry with --n_critics.",
            "A generic main file in the same family follows a MOPO-style path; prefer combo_main.py for COMBO.",
        ],
    ),
    "mopo": AlgoSpec(
        script="offline-rl-algorithms/MOPO/main.py",
        selector="dataset",
        default_selector_value="hopper-medium-v0",
        default_seed=1,
        gpu_kind="int",
        default_gpu="0",
        notes=[
            "MOPO fits a dynamics model before policy training; generated command can be very expensive to run.",
        ],
    ),
}


def shell_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def join_script(root: str, rel: str) -> str:
    root = root.strip()
    if root in ("", "."):
        return rel
    return root.rstrip("/") + "/" + rel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted AI-Optimizer offline-RL command recipe. The command is not executed.",
    )
    parser.add_argument("algorithm", choices=sorted(SPECS), help="algorithm recipe to build")
    parser.add_argument("--dataset", help="dataset name for algorithms whose parser uses --dataset")
    parser.add_argument("--env", help="environment name for algorithms whose parser uses --env")
    parser.add_argument("--seed", type=int, help="seed to include; defaults to the source parser default")
    parser.add_argument("--gpu", help="GPU value to include where supported; use --omit-gpu to suppress")
    parser.add_argument("--omit-gpu", action="store_true", help="do not include --gpu even if the algorithm supports it")
    parser.add_argument("--python", default="python", help="Python executable token to place at the front of the command")
    parser.add_argument("--script-root", default=".", help="optional prefix for a target checkout root; default emits relative paths")

    # Algorithm-specific optional flags.
    parser.add_argument("--n-critics", type=int, default=2, help="COMBO --n_critics value")
    parser.add_argument("--policy", default="ISPI", help="ISPI --policy value")
    parser.add_argument("--eval-freq", type=int, help="ISPI --eval_freq value")
    parser.add_argument("--max-timesteps", type=int, help="ISPI --max_timesteps value")
    parser.add_argument("--eval-episodes", type=int, help="ISPI --eval_episodes value")
    parser.add_argument("--save-model", action="store_true", help="include ISPI --save_model")
    parser.add_argument("--normalize", action="store_true", help="include ISPI --normalize")
    parser.add_argument("--reward-scale", type=float, help="ISPI --reward_scale value")
    parser.add_argument("--reward-bias", type=float, help="ISPI --reward_bias value")
    parser.add_argument("--reward-standardize", action="store_true", help="include ISPI --reward_standardize")
    parser.add_argument("--json", action="store_true", help="print JSON with command and metadata instead of only the command")
    return parser


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    args = build_parser().parse_args()
    spec = SPECS[args.algorithm]

    if spec.selector == "dataset":
        if args.env:
            fail(f"{args.algorithm} uses --dataset, not --env")
        selector_value = args.dataset or spec.default_selector_value
        selector_flag = "--dataset"
    elif spec.selector == "env":
        if args.dataset:
            fail(f"{args.algorithm} uses --env, not --dataset")
        selector_value = args.env or spec.default_selector_value
        selector_flag = "--env"
    else:  # defensive; no current recipe reaches this branch.
        fail(f"unsupported selector style {spec.selector!r}")

    if args.gpu is not None and spec.gpu_kind is None:
        fail(f"{args.algorithm} does not expose an explicit --gpu flag")

    command = [args.python, join_script(args.script_root, spec.script), selector_flag, selector_value]
    command += ["--seed", str(args.seed if args.seed is not None else spec.default_seed)]

    if spec.gpu_kind and not args.omit_gpu:
        gpu_value = args.gpu if args.gpu is not None else spec.default_gpu
        if gpu_value is not None:
            command += ["--gpu", str(gpu_value)]

    if args.algorithm == "combo":
        command += ["--n_critics", str(args.n_critics)]

    if args.algorithm == "ispi":
        # Reorder into the source parser's conventional shape.
        command = [args.python, join_script(args.script_root, spec.script), "--policy", args.policy, selector_flag, selector_value]
        command += ["--seed", str(args.seed if args.seed is not None else spec.default_seed)]
        if args.eval_freq is not None:
            command += ["--eval_freq", str(args.eval_freq)]
        if args.max_timesteps is not None:
            command += ["--max_timesteps", str(args.max_timesteps)]
        if args.eval_episodes is not None:
            command += ["--eval_episodes", str(args.eval_episodes)]
        if args.save_model:
            command += ["--save_model"]
        if args.normalize:
            command += ["--normalize"]
        if args.reward_scale is not None:
            command += ["--reward_scale", str(args.reward_scale)]
        if args.reward_bias is not None:
            command += ["--reward_bias", str(args.reward_bias)]
        if args.reward_standardize:
            command += ["--reward_standardize"]

    notes = list(spec.notes)
    if spec.gpu_kind:
        notes.append(f"GPU flag style for {args.algorithm}: --gpu expects {spec.gpu_kind}-style values.")
    notes.append("This builder only prints a command recipe; it does not run training or validate dependencies.")

    if args.json:
        print(json.dumps({"algorithm": args.algorithm, "selector": spec.selector, "command": command, "shell": shell_join(command), "notes": notes}, indent=2))
    else:
        print(shell_join(command))
        for note in notes:
            print(f"note: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
