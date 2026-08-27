#!/usr/bin/env python3
"""Build a dry-run verl PPO/GRPO command without executing training."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


def add_override(overrides: list[str], key: str, value: object | None) -> None:
    if value is None:
        return
    overrides.append(f"{key}={value}")


def shell_join(parts: Iterable[str]) -> str:
    return " \\\n  ".join(shlex.quote(str(part)) for part in parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble a dry-run python -m verl.trainer.main_ppo command from common "
            "data/model/rollout/backend/batch/logger options. The command is printed only."
        )
    )
    parser.add_argument("--algorithm", choices=["ppo", "grpo"], default="ppo", help="Training recipe to assemble.")
    parser.add_argument("--train-files", required=True, help="Training parquet path or quoted Hydra list.")
    parser.add_argument("--val-files", required=True, help="Validation parquet path or quoted Hydra list.")
    parser.add_argument("--model", required=True, help="Actor/policy model path or Hugging Face name.")
    parser.add_argument("--critic-model", help="Critic model path/name for PPO; defaults to --model.")
    parser.add_argument("--rollout-backend", default="vllm", help="Rollout backend, for example vllm, sglang, trtllm, or hf.")
    parser.add_argument("--model-engine", choices=["dp", "megatron", "veomni", "torchtitan"], default="dp")
    parser.add_argument("--train-batch-size", type=int, default=256)
    parser.add_argument("--ppo-mini-batch-size", type=int, default=64)
    parser.add_argument("--micro-batch-size-per-gpu", type=int, help="Actor/critic/ref micro batch override.")
    parser.add_argument("--max-prompt-length", type=int, default=512)
    parser.add_argument("--max-response-length", type=int, default=512)
    parser.add_argument("--rollout-n", type=int, help="Number of responses per prompt; defaults to 1 for PPO, 5 for GRPO.")
    parser.add_argument("--rollout-tp", type=int, default=1, help="Rollout tensor model parallel size.")
    parser.add_argument("--rollout-gpu-memory-utilization", type=float, default=0.4)
    parser.add_argument("--actor-lr", default="1e-6")
    parser.add_argument("--critic-lr", default="1e-5")
    parser.add_argument("--kl-coef", default="0.001", help="KL coefficient for PPO reward KL or GRPO actor KL loss.")
    parser.add_argument("--logger", default="console", help="Hydra logger value, e.g. console or '[\"console\",\"wandb\"]'.")
    parser.add_argument("--project-name", default="verl_examples")
    parser.add_argument("--experiment-name", default="dry_run")
    parser.add_argument("--nnodes", type=int, default=1)
    parser.add_argument("--gpus-per-node", type=int, default=1)
    parser.add_argument("--total-epochs", type=int, default=1)
    parser.add_argument("--save-freq", type=int, default=-1)
    parser.add_argument("--test-freq", type=int, default=1)
    parser.add_argument("--filter-overlong-prompts", action="store_true")
    parser.add_argument("--truncation", default="error", choices=["error", "left", "right", "middle"])
    parser.add_argument("--val-before-train", choices=["True", "False"], default="False")
    parser.add_argument("--extra", action="append", default=[], help="Additional raw Hydra override. May be repeated.")
    return parser


def build_command(args: argparse.Namespace) -> list[str]:
    rollout_n = args.rollout_n if args.rollout_n is not None else (5 if args.algorithm == "grpo" else 1)
    critic_model = args.critic_model or args.model
    overrides: list[str] = []

    add_override(overrides, "algorithm.adv_estimator", "grpo" if args.algorithm == "grpo" else "gae")
    if args.algorithm == "grpo":
        add_override(overrides, "algorithm.use_kl_in_reward", "False")

    add_override(overrides, "data.train_files", args.train_files)
    add_override(overrides, "data.val_files", args.val_files)
    add_override(overrides, "data.train_batch_size", args.train_batch_size)
    add_override(overrides, "data.max_prompt_length", args.max_prompt_length)
    add_override(overrides, "data.max_response_length", args.max_response_length)
    add_override(overrides, "data.filter_overlong_prompts", str(args.filter_overlong_prompts))
    add_override(overrides, "data.truncation", args.truncation)

    add_override(overrides, "actor_rollout_ref.model.path", args.model)
    add_override(overrides, "actor_rollout_ref.model.use_remove_padding", "True")
    add_override(overrides, "actor_rollout_ref.model.enable_gradient_checkpointing", "True")
    add_override(overrides, "actor_rollout_ref.actor.optim.lr", args.actor_lr)
    add_override(overrides, "actor_rollout_ref.actor.ppo_mini_batch_size", args.ppo_mini_batch_size)
    add_override(overrides, "actor_rollout_ref.actor.use_dynamic_bsz", "True")
    if args.micro_batch_size_per_gpu is not None:
        add_override(overrides, "actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu", args.micro_batch_size_per_gpu)

    if args.algorithm == "grpo":
        add_override(overrides, "actor_rollout_ref.actor.use_kl_loss", "True")
        add_override(overrides, "actor_rollout_ref.actor.kl_loss_coef", args.kl_coef)
        add_override(overrides, "actor_rollout_ref.actor.kl_loss_type", "low_var_kl")
    else:
        add_override(overrides, "critic.model.path", critic_model)
        add_override(overrides, "critic.model.use_remove_padding", "True")
        add_override(overrides, "critic.model.enable_gradient_checkpointing", "True")
        add_override(overrides, "critic.optim.lr", args.critic_lr)
        if args.micro_batch_size_per_gpu is not None:
            add_override(overrides, "critic.ppo_micro_batch_size_per_gpu", args.micro_batch_size_per_gpu)
            add_override(overrides, "actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu", args.micro_batch_size_per_gpu)
        add_override(overrides, "algorithm.kl_ctrl.kl_coef", args.kl_coef)

    add_override(overrides, "actor_rollout_ref.rollout.name", args.rollout_backend)
    add_override(overrides, "actor_rollout_ref.rollout.tensor_model_parallel_size", args.rollout_tp)
    add_override(overrides, "actor_rollout_ref.rollout.gpu_memory_utilization", args.rollout_gpu_memory_utilization)
    add_override(overrides, "actor_rollout_ref.rollout.n", rollout_n)

    add_override(overrides, "trainer.logger", args.logger)
    add_override(overrides, "trainer.project_name", args.project_name)
    add_override(overrides, "trainer.experiment_name", args.experiment_name)
    add_override(overrides, "trainer.n_gpus_per_node", args.gpus_per_node)
    add_override(overrides, "trainer.nnodes", args.nnodes)
    add_override(overrides, "trainer.val_before_train", args.val_before_train)
    add_override(overrides, "trainer.save_freq", args.save_freq)
    add_override(overrides, "trainer.test_freq", args.test_freq)
    add_override(overrides, "trainer.total_epochs", args.total_epochs)

    if args.model_engine != "dp":
        add_override(overrides, "model_engine", args.model_engine)

    overrides.extend(args.extra)
    return ["python", "-m", "verl.trainer.main_ppo", *overrides]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = build_command(args)
    print(shell_join(command))


if __name__ == "__main__":
    main()
