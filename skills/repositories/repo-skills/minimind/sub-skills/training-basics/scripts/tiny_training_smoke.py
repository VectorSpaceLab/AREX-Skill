#!/usr/bin/env python3
"""Run a bounded MiniMind model training smoke on random tensors.

This helper imports MiniMind modules from the active package/source environment
or the current working directory, constructs a tiny model config, runs
forward/backward/one optimizer step, and optionally runs short generation. It
reads no datasets, downloads nothing, and writes no checkpoints.
"""
from __future__ import annotations

import argparse
import contextlib
import random
import sys
from pathlib import Path
from typing import Iterable, List, Optional


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny MiniMind random-tensor training smoke.")
    parser.add_argument("--module-root", type=Path, help="Optional directory to prepend to sys.path when MiniMind modules are not already importable.")
    parser.add_argument("--device", default="auto", help="Device: auto, cpu, cuda, cuda:0, etc. Default chooses CUDA when available.")
    parser.add_argument("--dtype", choices=["auto", "float32", "float16", "bfloat16"], default="auto", help="Autocast dtype for CUDA. CPU uses float32.")
    parser.add_argument("--hidden-size", type=int, default=32, help="Tiny model hidden size.")
    parser.add_argument("--num-hidden-layers", type=int, default=2, help="Tiny model layer count.")
    parser.add_argument("--num-attention-heads", type=int, default=4, help="Tiny model query head count.")
    parser.add_argument("--num-key-value-heads", type=int, default=2, help="Tiny model key/value head count.")
    parser.add_argument("--vocab-size", type=int, default=128, help="Random vocabulary size for smoke-only model.")
    parser.add_argument("--seq-len", type=int, default=16, help="Random sequence length.")
    parser.add_argument("--batch-size", type=int, default=2, help="Random batch size.")
    parser.add_argument("--use-moe", action="store_true", help="Use the MoE MLP path in the tiny config.")
    parser.add_argument("--num-experts", type=int, default=4, help="MoE expert count when --use-moe is enabled.")
    parser.add_argument("--num-experts-per-tok", type=int, default=1, help="MoE top-k experts per token when --use-moe is enabled.")
    parser.add_argument("--lora", action="store_true", help="Apply MiniMind LoRA and verify only LoRA params are trainable.")
    parser.add_argument("--lora-rank", type=int, default=4, help="LoRA rank for the smoke.")
    parser.add_argument("--learning-rate", type=float, default=1e-3, help="Optimizer learning rate for the one-step smoke.")
    parser.add_argument("--seed", type=int, default=1234, help="Deterministic seed.")
    parser.add_argument("--max-new-tokens", type=int, default=3, help="Short generation length.")
    parser.add_argument("--skip-generate", action="store_true", help="Skip generation and only run forward/backward/optimizer.")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    positive_ints = [
        "hidden_size",
        "num_hidden_layers",
        "num_attention_heads",
        "num_key_value_heads",
        "vocab_size",
        "seq_len",
        "batch_size",
        "num_experts",
        "num_experts_per_tok",
        "lora_rank",
    ]
    for name in positive_ints:
        if getattr(args, name) <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} must be positive")
    if args.hidden_size % args.num_attention_heads != 0:
        raise SystemExit("--hidden-size must be divisible by --num-attention-heads")
    if args.num_attention_heads % args.num_key_value_heads != 0:
        raise SystemExit("--num-attention-heads must be divisible by --num-key-value-heads")
    if args.num_experts_per_tok > args.num_experts:
        raise SystemExit("--num-experts-per-tok cannot exceed --num-experts")
    if args.vocab_size < 8:
        raise SystemExit("--vocab-size should be at least 8 for generation/loss smoke")
    if args.learning_rate <= 0:
        raise SystemExit("--learning-rate must be positive")
    if args.max_new_tokens < 0:
        raise SystemExit("--max-new-tokens must be non-negative")


def import_minimind(args: argparse.Namespace):
    candidate_roots = []
    if args.module_root:
        candidate_roots.append(args.module_root)
    candidate_roots.append(Path.cwd())
    for root in reversed(candidate_roots):
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
    try:
        from model.model_minimind import MiniMindConfig, MiniMindForCausalLM
    except Exception as exc:
        raise SystemExit(
            "Could not import MiniMind model modules. Run inside an environment where "
            "MiniMind packages are importable, or pass --module-root. Original error: "
            f"{exc}"
        ) from exc
    return MiniMindConfig, MiniMindForCausalLM


def choose_device(torch, requested: str):
    if requested == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA device requested but torch.cuda.is_available() is false")
    return device


def choose_dtype(torch, device, requested: str):
    if device.type != "cuda":
        return torch.float32
    if requested == "float32":
        return torch.float32
    if requested == "float16":
        return torch.float16
    if requested == "bfloat16":
        return torch.bfloat16
    if torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def autocast_context(torch, device, dtype):
    if device.type == "cuda" and dtype in {torch.float16, torch.bfloat16}:
        return torch.cuda.amp.autocast(dtype=dtype)
    return contextlib.nullcontext()


def trainable_parameter_names(model) -> List[str]:
    return [name for name, param in model.named_parameters() if param.requires_grad]


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    validate_args(args)

    try:
        import torch
    except Exception as exc:
        raise SystemExit(f"PyTorch is required for this smoke: {exc}") from exc

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    MiniMindConfig, MiniMindForCausalLM = import_minimind(args)
    device = choose_device(torch, args.device)
    dtype = choose_dtype(torch, device, args.dtype)

    config = MiniMindConfig(
        hidden_size=args.hidden_size,
        num_hidden_layers=args.num_hidden_layers,
        vocab_size=args.vocab_size,
        use_moe=args.use_moe,
        num_attention_heads=args.num_attention_heads,
        num_key_value_heads=args.num_key_value_heads,
        max_position_embeddings=max(args.seq_len + args.max_new_tokens + 8, 64),
        flash_attn=True,
        num_experts=args.num_experts,
        num_experts_per_tok=args.num_experts_per_tok,
    )
    model = MiniMindForCausalLM(config).to(device)

    if args.lora:
        try:
            from model.model_lora import apply_lora
        except Exception as exc:
            raise SystemExit(f"Could not import MiniMind LoRA helper: {exc}") from exc
        apply_lora(model, rank=args.lora_rank)
        for name, param in model.named_parameters():
            param.requires_grad = "lora" in name
        bad_trainable = [name for name in trainable_parameter_names(model) if "lora" not in name]
        if bad_trainable:
            raise SystemExit(f"LoRA smoke expected only LoRA trainables, found: {bad_trainable[:5]}")

    params = [param for param in model.parameters() if param.requires_grad]
    if not params:
        raise SystemExit("No trainable parameters found")

    optimizer = torch.optim.AdamW(params, lr=args.learning_rate)
    input_ids = torch.randint(0, args.vocab_size, (args.batch_size, args.seq_len), device=device)
    labels = input_ids.clone()

    model.train()
    optimizer.zero_grad(set_to_none=True)
    with autocast_context(torch, device, dtype):
        outputs = model(input_ids=input_ids, labels=labels)
        aux_loss = outputs.aux_loss if outputs.aux_loss is not None else torch.zeros((), device=device)
        loss = outputs.loss + aux_loss

    if not torch.isfinite(loss.detach()):
        raise SystemExit(f"Non-finite loss: {loss.detach().item()}")

    loss.backward()
    grad_norm_sq = torch.zeros((), device=device)
    for param in params:
        if param.grad is not None:
            grad_norm_sq = grad_norm_sq + param.grad.detach().float().pow(2).sum()
    grad_norm = float(torch.sqrt(grad_norm_sq).detach().cpu())
    if grad_norm <= 0.0:
        raise SystemExit("Gradient norm is zero; backward did not exercise trainable parameters")

    optimizer.step()

    generated_shape = None
    if not args.skip_generate and args.max_new_tokens > 0:
        model.eval()
        prompt = input_ids[:, : min(args.seq_len, 4)]
        attention_mask = torch.ones_like(prompt)
        with torch.inference_mode():
            generated = model.generate(
                input_ids=prompt,
                attention_mask=attention_mask,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                top_k=0,
                top_p=1.0,
                temperature=1.0,
                eos_token_id=None,
            )
        generated_shape = tuple(generated.shape)
        expected_len = prompt.shape[1] + args.max_new_tokens
        if generated.shape != (args.batch_size, expected_len):
            raise SystemExit(f"Unexpected generated shape {generated_shape}; expected {(args.batch_size, expected_len)}")

    total_params = sum(param.numel() for param in model.parameters())
    trainable_params = sum(param.numel() for param in params)
    print("MiniMind tiny training smoke passed")
    print(f"  device: {device}")
    print(f"  dtype: {dtype}")
    print(f"  hidden_size: {args.hidden_size}")
    print(f"  layers: {args.num_hidden_layers}")
    print(f"  use_moe: {args.use_moe}")
    print(f"  lora: {args.lora}")
    print(f"  total_params: {total_params}")
    print(f"  trainable_params: {trainable_params}")
    print(f"  loss: {float(loss.detach().cpu()):.6f}")
    print(f"  grad_norm: {grad_norm:.6f}")
    if generated_shape is not None:
        print(f"  generated_shape: {generated_shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
