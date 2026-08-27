#!/usr/bin/env python3
"""Print a safe dry-run SFT -> Reward -> DPO -> PPO -> GRPO -> eval sequence.

No command is executed. Defaults use relative artifact directories and generic
`python`/`torchrun` executables so the plan can be adapted to the user's own workspace.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import PurePosixPath

TRAIN_ORDER = ["sft", "reward", "dpo", "ppo", "grpo"]
ALL_SKIPS = set(TRAIN_ORDER + ["eval"])


def q(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def run_prefix(args: argparse.Namespace, script: str) -> list[str]:
    if args.nproc > 1:
        return [args.torchrun, "--standalone", f"--nproc_per_node={args.nproc}", script]
    return [args.python, script]


def path_join(base: str, name: str) -> str:
    return str(PurePosixPath(base) / name)


def train_commands(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    cfg = args.config_dir
    ckpt = args.ckpt_dir
    data = args.data_dir
    log = args.log_dir
    commands: list[tuple[str, list[str]]] = []

    commands.append((
        "SFT: base checkpoint -> instruction policy",
        run_prefix(args, "scripts/train_sft.py") + [
            "--config", path_join(cfg, "sft.json"),
            "--pretrained_ckpt", path_join(ckpt, "base_pretrained.pt"),
            "--data_path", path_join(data, "sft_packed.h5"),
            "--out_ckpt", path_join(ckpt, "sft.pt"),
            "--log_dir", log,
        ],
    ))
    commands.append((
        "Reward model: SFT policy + preference pairs -> scalar reward model",
        run_prefix(args, "scripts/train_reward.py") + [
            "--config", path_join(cfg, "reward.json"),
            "--sft_ckpt", path_join(ckpt, "sft.pt"),
            "--pref_path", path_join(data, "preferences.jsonl"),
            "--out_ckpt", path_join(ckpt, "reward.pt"),
            "--log_dir", log,
        ],
    ))
    commands.append((
        f"DPO-family: SFT policy + preferences -> {args.loss_type} policy",
        run_prefix(args, "scripts/train_dpo.py") + [
            "--config", path_join(cfg, "dpo.json"),
            "--sft_ckpt", path_join(ckpt, "sft.pt"),
            "--pref_path", path_join(data, "preferences.jsonl"),
            "--out_ckpt", path_join(ckpt, "dpo.pt"),
            "--loss_type", args.loss_type,
            "--log_dir", log,
        ],
    ))
    commands.append((
        f"PPO: SFT policy + prompts -> PPO policy using {args.reward_source} reward",
        run_prefix(args, "scripts/train_ppo.py") + [
            "--config", path_join(cfg, "ppo.json"),
            "--sft_ckpt", path_join(ckpt, "sft.pt"),
            "--reward_ckpt", path_join(ckpt, "reward.pt"),
            "--prompt_path", path_join(data, "rl_prompts_train.jsonl"),
            "--eval_prompt_path", path_join(data, "rl_prompts_test.jsonl"),
            "--out_ckpt", path_join(ckpt, "ppo.pt"),
            "--reward_source", args.reward_source,
            "--log_dir", log,
        ],
    ))
    commands.append((
        "GRPO/RLVR: SFT policy + grouped verifier rollouts -> GRPO policy",
        run_prefix(args, "scripts/train_grpo.py") + [
            "--config", path_join(cfg, "grpo.json"),
            "--sft_ckpt", path_join(ckpt, "sft.pt"),
            "--prompt_path", path_join(data, "rl_prompts_train.jsonl"),
            "--eval_prompt_path", path_join(data, "rl_prompts_test.jsonl"),
            "--curriculum_path", path_join(data, "arithmetic_prompts.jsonl"),
            "--out_ckpt", path_join(ckpt, "grpo.pt"),
            "--group_size", str(args.group_size),
            "--log_dir", log,
        ],
    ))
    return commands


def eval_commands(args: argparse.Namespace, skipped: set[str]) -> list[tuple[str, list[str]]]:
    ckpt = args.ckpt_dir
    table = path_join(args.log_dir, args.eval_table)
    labels = ["base_pretrained", "sft", "dpo", "ppo", "grpo"]
    commands: list[tuple[str, list[str]]] = []
    for label in labels:
        stage = "sft" if label == "sft" else label
        if stage in skipped:
            continue
        commands.append((
            f"Eval append: {label}",
            [args.python, "scripts/eval_post_training.py", "--ckpt", path_join(ckpt, f"{label}.pt"),
             "--label", label, "--limit", str(args.eval_limit), "--append", table],
        ))
    commands.append((
        "Render eval table",
        [args.python, "scripts/eval_post_training.py", "--table", table],
    ))
    return commands


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Print a dry-run post-training command sequence; does not execute it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--nproc", type=int, default=1, help="number of processes; >1 uses torchrun")
    p.add_argument("--python", default="python", help="Python executable for single-process commands and eval")
    p.add_argument("--torchrun", default="torchrun", help="torchrun executable for multi-process training commands")
    p.add_argument("--config-dir", default="configs", help="directory containing stage JSON configs")
    p.add_argument("--ckpt-dir", default="ckpts", help="checkpoint directory to place in printed commands")
    p.add_argument("--data-dir", default="data", help="prepared data directory to place in printed commands")
    p.add_argument("--log-dir", default="logs", help="metrics/table directory to place in printed commands")
    p.add_argument("--skip", action="append", choices=sorted(ALL_SKIPS), default=[], help="skip a stage; repeatable")
    p.add_argument("--loss-type", choices=("dpo", "orpo", "kto"), default="dpo", help="DPO-family objective")
    p.add_argument("--reward-source", choices=("verifier", "rm"), default="verifier", help="PPO reward source")
    p.add_argument("--group-size", type=int, default=8, help="GRPO samples per prompt")
    p.add_argument("--eval-limit", type=int, default=200, help="evaluation examples per checkpoint")
    p.add_argument("--eval-table", default="stage_table.jsonl", help="JSONL table filename inside log-dir")
    p.add_argument("--no-env", action="store_true", help="omit PYTHONPATH=. prefixes")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.nproc < 1:
        raise SystemExit("--nproc must be >= 1")
    skipped = set(args.skip)
    env = "" if args.no_env else "PYTHONPATH=. "

    print("# Dry-run post-training plan. Review paths and hardware before executing.")
    print(f"# skipped: {', '.join(sorted(skipped)) if skipped else 'none'}")
    print("# Ensure prepared data, upstream checkpoints, and output directories exist.\n")

    for stage, (title, cmd) in zip(TRAIN_ORDER, train_commands(args)):
        if stage in skipped:
            print(f"# SKIP {stage}: {title}\n")
            continue
        print(f"# {title}")
        print(env + q(cmd) + "\n")

    if "eval" not in skipped:
        print("# Evaluation table commands (route detailed eval/chat questions to evaluation-chat).")
        for title, cmd in eval_commands(args, skipped):
            print(f"# {title}")
            print(env + q(cmd))
    else:
        print("# SKIP eval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
