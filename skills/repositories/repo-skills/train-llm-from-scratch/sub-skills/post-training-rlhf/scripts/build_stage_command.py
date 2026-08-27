#!/usr/bin/env python3
"""Dry-run command builder for train-llm-from-scratch post-training stages.

The script prints a shell command only. It never imports the repo package, reads configs,
launches training, downloads data, or writes files.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from collections.abc import Iterable

STAGE_TO_SCRIPT = {
    "sft": "scripts/train_sft.py",
    "reward": "scripts/train_reward.py",
    "dpo": "scripts/train_dpo.py",
    "ppo": "scripts/train_ppo.py",
    "grpo": "scripts/train_grpo.py",
}

# Config fields accepted by each stage. The helper maps dashed helper flags to
# the repo's underscore-style CLI fields.
STAGE_FIELDS = {
    "sft": {
        "pretrained_ckpt", "data_path", "out_ckpt", "batch_size", "grad_accum",
        "epochs", "max_steps", "lr", "min_lr", "grad_clip", "device", "amp_dtype",
        "log_dir", "use_wandb",
    },
    "reward": {
        "sft_ckpt", "pref_path", "out_ckpt", "batch_size", "epochs", "lr",
        "max_len", "grad_clip", "device", "amp_dtype", "log_dir", "use_wandb",
    },
    "dpo": {
        "sft_ckpt", "pref_path", "out_ckpt", "loss_type", "beta", "orpo_lambda",
        "batch_size", "epochs", "lr", "max_len", "grad_clip", "device", "amp_dtype",
        "log_dir", "use_wandb",
    },
    "ppo": {
        "sft_ckpt", "reward_ckpt", "prompt_path", "eval_prompt_path", "out_ckpt",
        "reward_source", "iterations", "prompts_per_iter", "rollout_len", "temperature",
        "top_p", "ppo_epochs", "minibatch_size", "clip", "vf_clip", "vf_coef",
        "gamma", "gae_lambda", "kl_coef", "lr", "grad_clip", "device", "amp_dtype",
        "log_dir", "use_wandb",
    },
    "grpo": {
        "sft_ckpt", "prompt_path", "eval_prompt_path", "curriculum_path",
        "curriculum_iters", "out_ckpt", "iterations", "prompts_per_iter", "group_size",
        "rollout_len", "temperature", "top_p", "grpo_epochs", "clip", "kl_coef",
        "lr", "grad_clip", "device", "amp_dtype", "log_dir", "use_wandb",
    },
}

FLAG_TO_FIELD = {
    "pretrained_ckpt": "pretrained_ckpt",
    "sft_ckpt": "sft_ckpt",
    "reward_ckpt": "reward_ckpt",
    "data_path": "data_path",
    "pref_path": "pref_path",
    "prompt_path": "prompt_path",
    "eval_prompt_path": "eval_prompt_path",
    "curriculum_path": "curriculum_path",
    "out_ckpt": "out_ckpt",
    "loss_type": "loss_type",
    "reward_source": "reward_source",
    "group_size": "group_size",
    "beta": "beta",
    "orpo_lambda": "orpo_lambda",
    "kl_coef": "kl_coef",
    "iterations": "iterations",
    "epochs": "epochs",
    "max_steps": "max_steps",
    "batch_size": "batch_size",
    "lr": "lr",
    "device": "device",
    "amp_dtype": "amp_dtype",
    "log_dir": "log_dir",
    "use_wandb": "use_wandb",
}


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def add_if_applicable(args: argparse.Namespace, stage: str, cmd: list[str]) -> None:
    allowed = STAGE_FIELDS[stage]
    for attr, field in FLAG_TO_FIELD.items():
        value = getattr(args, attr, None)
        if value is None:
            continue
        if field not in allowed:
            raise SystemExit(f"--{attr.replace('_', '-')} is not valid for stage '{stage}'")
        cmd.extend([f"--{field}", str(value)])


def build_command(args: argparse.Namespace) -> list[str]:
    stage = args.stage
    if args.nproc < 1:
        raise SystemExit("--nproc must be >= 1")

    if args.nproc > 1:
        cmd = [args.torchrun, "--standalone", f"--nproc_per_node={args.nproc}", STAGE_TO_SCRIPT[stage]]
    else:
        cmd = [args.python, STAGE_TO_SCRIPT[stage]]

    if args.config:
        cmd.extend(["--config", args.config])

    add_if_applicable(args, stage, cmd)

    for token in args.extra or []:
        if not token:
            continue
        cmd.append(token)

    return cmd


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Print a dry-run post-training stage command; does not execute it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("stage", choices=sorted(STAGE_TO_SCRIPT), help="post-training stage to build")
    p.add_argument("--config", help="stage JSON config to pass through")
    p.add_argument("--nproc", type=int, default=1, help="number of processes; >1 uses torchrun")
    p.add_argument("--python", default="python", help="Python executable for single-process commands")
    p.add_argument("--torchrun", default="torchrun", help="torchrun executable for multi-process commands")
    p.add_argument(
        "--extra",
        action="append",
        default=[],
        help="append one raw argument token; repeat as --extra=--lr --extra=1e-6",
    )

    # Common path/config flags. They are validated against the selected stage.
    p.add_argument("--pretrained-ckpt", dest="pretrained_ckpt")
    p.add_argument("--sft-ckpt", dest="sft_ckpt")
    p.add_argument("--reward-ckpt", dest="reward_ckpt")
    p.add_argument("--data-path", dest="data_path")
    p.add_argument("--pref-path", dest="pref_path")
    p.add_argument("--prompt-path", dest="prompt_path")
    p.add_argument("--eval-prompt-path", dest="eval_prompt_path")
    p.add_argument("--curriculum-path", dest="curriculum_path")
    p.add_argument("--out-ckpt", dest="out_ckpt")
    p.add_argument("--log-dir", dest="log_dir")

    # Common algorithm knobs.
    p.add_argument("--loss-type", dest="loss_type", choices=("dpo", "orpo", "kto"))
    p.add_argument("--reward-source", dest="reward_source", choices=("verifier", "rm"))
    p.add_argument("--group-size", dest="group_size", type=int)
    p.add_argument("--beta", type=float)
    p.add_argument("--orpo-lambda", dest="orpo_lambda", type=float)
    p.add_argument("--kl-coef", dest="kl_coef", type=float)
    p.add_argument("--iterations", type=int)
    p.add_argument("--epochs", type=int)
    p.add_argument("--max-steps", dest="max_steps", type=int)
    p.add_argument("--batch-size", dest="batch_size", type=int)
    p.add_argument("--lr", type=float)
    p.add_argument("--device")
    p.add_argument("--amp-dtype", dest="amp_dtype")
    p.add_argument("--use-wandb", dest="use_wandb", choices=("true", "false"))
    p.add_argument("--no-env", action="store_true", help="omit the PYTHONPATH=. prefix")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    cmd = build_command(args)
    if args.no_env:
        print(shell_join(cmd))
    else:
        print("PYTHONPATH=. " + shell_join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
