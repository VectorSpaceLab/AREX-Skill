#!/usr/bin/env python3
"""Build a conservative lerobot-train command without executing it."""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

POLICIES = {
    "act", "diffusion", "eo1", "evo1", "groot", "molmoact2", "fastwam", "gaussian_actor",
    "lingbot_va", "multi_task_dit", "pi0", "pi0_fast", "pi05", "smolvla", "tdmpc",
    "vla_jepa", "vqbet", "wall_x", "xvla",
}


def build(args: argparse.Namespace) -> tuple[list[str], list[str], list[str]]:
    command = ["lerobot-train", f"--dataset.repo_id={args.dataset}"]
    checks: list[str] = ["not launched: this builder only prints a command"]
    warnings: list[str] = []
    if args.checkpoint:
        command.append(f"--policy.path={args.checkpoint}")
        checks.append("pretrained fine-tune path supplied; this is not an optimizer/RNG resume")
    else:
        command.append(f"--policy.type={args.policy}")
        checks.append(f"policy choice is syntactically selected: {args.policy}")
    command.extend([
        f"--policy.device={args.device}",
        f"--policy.push_to_hub={'true' if args.push_to_hub else 'false'}",
        f"--batch_size={args.batch_size}",
        f"--steps={args.steps}",
        f"--save_checkpoint={'true' if args.save_checkpoint else 'false'}",
        f"--save_freq={args.save_freq}",
        f"--wandb.enable={'true' if args.wandb else 'false'}",
        f"--output_dir={args.output_dir}",
    ])
    if args.eval_split is not None:
        command.append(f"--dataset.eval_split={args.eval_split}")
    if args.eval_steps:
        command.append(f"--eval_steps={args.eval_steps}")
    if args.grad_accumulation != 1:
        command.append(f"--accelerator.gradient_accumulation.steps={args.grad_accumulation}")
    if args.mixed_precision != "no":
        command.append(f"--accelerator.mixed_precision={args.mixed_precision}")
    if args.resume_config:
        command.extend([f"--config_path={args.resume_config}", "--resume=true"])
        checks.append("resume requested; inspect checkpoint train_config.json and training state")
    if args.eval_steps and args.eval_split in (None, 0.0):
        warnings.append("eval_steps > 0 requires dataset.eval_split > 0; supply a held-out split")
    if args.wandb:
        warnings.append("W&B logging is enabled; confirm credentials/network and intended side effects")
    if args.push_to_hub:
        warnings.append("Hub push is enabled; provide policy.repo_id/credentials separately")
    if args.device.startswith("cuda"):
        checks.append("CUDA availability must be confirmed in the target environment; this builder does not probe it")
    if args.steps <= 100:
        checks.append("bounded smoke budget selected; scale only after a finite-loss/checkpoint load test")
    return command, checks, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="dataset repo identifier or approved local identifier")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--policy", choices=sorted(POLICIES), help="fresh policy type")
    group.add_argument("--checkpoint", help="pretrained policy path or approved Hub identifier")
    parser.add_argument("--device", default="cpu", help="cpu, cuda[:N], mps, or xpu")
    parser.add_argument("--output-dir", default="outputs/train/policy_smoke")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--save-freq", type=int, default=10)
    parser.add_argument("--eval-split", type=float, default=None)
    parser.add_argument("--eval-steps", type=int, default=0)
    parser.add_argument("--grad-accumulation", type=int, default=1)
    parser.add_argument("--mixed-precision", choices=("no", "fp16", "bf16"), default="no")
    parser.add_argument("--resume-config", help="approved resume config path; adds --resume=true")
    parser.add_argument("--save-checkpoint", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--push-to-hub", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--wandb", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()
    for name in ("steps", "batch_size", "grad_accumulation"):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be >= 1")
    if args.save_freq < 1:
        parser.error("--save-freq must be >= 1")
    if args.eval_split is not None and not 0.0 <= args.eval_split < 1.0:
        parser.error("--eval-split must be in [0, 1)")
    if args.eval_steps < 0:
        parser.error("--eval-steps must be >= 0")
    command, checks, warnings = build(args)
    print("Command (not executed):")
    print(shlex.join(command))
    print("\nValidation:")
    for item in checks:
        print(f"- {item}")
    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"- {item}")
    print("\nBefore launch: verify dataset features/stats, policy extra, device, checkpoint/processor contract, and output directory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
