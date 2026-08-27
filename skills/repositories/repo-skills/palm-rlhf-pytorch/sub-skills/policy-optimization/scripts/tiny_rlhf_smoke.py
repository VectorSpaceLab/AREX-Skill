#!/usr/bin/env python3
"""Tiny PPO RLHF smoke test for palm_rlhf_pytorch.

This helper is safe to run from any working directory. It builds tiny PaLM and
RewardModel objects, creates the root PPO RLHFTrainer from prompt_token_ids,
and can either stop after construction or run one bounded training update.
"""
from __future__ import annotations

import argparse


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny PPO RLHF smoke check.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--num-tokens", type=int, default=32)
    parser.add_argument("--dim", type=int, default=16)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--heads", type=int, default=2)
    parser.add_argument("--dim-head", type=int, default=8)
    parser.add_argument("--prompt-len", type=int, default=4)
    parser.add_argument("--num-prompts", type=int, default=2)
    parser.add_argument("--num-episodes", type=int, default=1)
    parser.add_argument("--max-timesteps", type=int, default=1)
    parser.add_argument("--update-timesteps", type=int, default=1)
    parser.add_argument("--max-seq-len", type=int, default=16)
    parser.add_argument("--minibatch-size", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--train-smoke", action="store_true", help="Run the bounded one-step training path explicitly.")
    parser.add_argument("--construct-only", action="store_true", help="Only construct the trainer and skip the training step.")
    args = parser.parse_args()

    import torch
    from palm_rlhf_pytorch import PaLM, RewardModel, RLHFTrainer

    device = torch.device(choose_device(args.device))
    torch.manual_seed(0)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(0)

    palm = PaLM(
        num_tokens=args.num_tokens,
        dim=args.dim,
        depth=args.depth,
        heads=args.heads,
        dim_head=args.dim_head,
        flash_attn=False,
    ).to(device)

    reward_model = RewardModel(palm, num_binned_output=0, dropout=0.0, use_lora=True).to(device)
    prompt_token_ids = torch.randint(0, args.num_tokens, (args.num_prompts, args.prompt_len), device=device)

    trainer = RLHFTrainer(
        palm=palm,
        reward_model=reward_model,
        prompt_token_ids=prompt_token_ids,
        actor_lora=True,
        critic_lora=True,
        epochs=1,
        minibatch_size=args.minibatch_size,
        accelerate_kwargs=dict(),
    )

    print(f"trainer_device={trainer.device}")
    print(f"prompt_shape={tuple(trainer.prompt_token_ids.shape)}")

    if args.construct_only:
        print("construct_only=True")
        print("ok")
        return 0

    trainer.train(
        num_episodes=args.num_episodes,
        max_timesteps=args.max_timesteps,
        update_timesteps=args.update_timesteps,
        max_batch_size=1,
        max_seq_len=args.max_seq_len,
        eos_token=None,
        temperature=args.temperature,
    )

    prompt = trainer.prompt_token_ids[0]
    answer = trainer.generate(args.max_seq_len, prompt=prompt, num_samples=2)
    print(f"generated_shape={tuple(answer.shape)}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
