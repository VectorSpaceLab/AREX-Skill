#!/usr/bin/env python3
"""Print Tevatron training command plans without running training."""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List

ROUTES = (
    "dense",
    "distil",
    "lora",
    "gradcache",
    "deepspeed-lora",
    "jax",
    "tevax-lora",
    "splade",
    "unicoil",
)

DEFAULT_LORA_TARGETS = "q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj"


def add_flag(command: List[str], flag: str, value) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        if value:
            command.append(flag)
        return
    command.extend([flag, str(value)])


def add_optional_flag(command: List[str], flag: str, value) -> None:
    if value in (None, ""):
        return
    add_flag(command, flag, value)


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def base_hf_args(args: argparse.Namespace, *, output_flag: str = "--output_dir") -> List[str]:
    command: List[str] = []
    add_flag(command, output_flag, args.output_dir)
    add_flag(command, "--model_name_or_path", args.model_name_or_path)
    add_optional_flag(command, "--tokenizer_name", args.tokenizer_name)
    add_flag(command, "--dataset_name", args.dataset_name)
    add_optional_flag(command, "--dataset_config", args.dataset_config)
    add_optional_flag(command, "--dataset_path", args.dataset_path)
    add_flag(command, "--dataset_split", args.dataset_split)
    add_optional_flag(command, "--corpus_name", args.corpus_name)
    add_optional_flag(command, "--corpus_path", args.corpus_path)
    add_optional_flag(command, "--query_prefix", args.query_prefix)
    add_optional_flag(command, "--passage_prefix", args.passage_prefix)
    add_optional_flag(command, "--pooling", args.pooling)
    add_flag(command, "--normalize", args.normalize)
    add_optional_flag(command, "--temperature", args.temperature)
    add_flag(command, "--per_device_train_batch_size", args.batch_size)
    add_flag(command, "--train_group_size", args.train_group_size)
    add_flag(command, "--learning_rate", args.learning_rate)
    add_flag(command, "--query_max_len", args.query_max_len)
    add_flag(command, "--passage_max_len", args.passage_max_len)
    add_flag(command, "--num_train_epochs", args.epochs)
    add_flag(command, "--save_steps", args.save_steps)
    add_flag(command, "--logging_steps", args.logging_steps)
    add_flag(command, "--gradient_accumulation_steps", args.gradient_accumulation_steps)
    add_flag(command, "--gradient_checkpointing", args.gradient_checkpointing)
    add_optional_flag(command, "--attn_implementation", args.attn_implementation)
    add_flag(command, "--append_eos_token", args.append_eos_token)
    add_optional_flag(command, "--pad_to_multiple_of", args.pad_to_multiple_of)
    add_flag(command, "--overwrite_output_dir", args.overwrite_output_dir)
    if args.precision != "none":
        command.append(f"--{args.precision}")
    return command


def add_lora_args(command: List[str], args: argparse.Namespace) -> None:
    add_flag(command, "--lora", True)
    add_optional_flag(command, "--lora_name_or_path", args.lora_name_or_path)
    add_flag(command, "--lora_target_modules", args.lora_target_modules)
    add_flag(command, "--lora_r", args.lora_r)
    add_flag(command, "--lora_alpha", args.lora_alpha)
    add_flag(command, "--lora_dropout", args.lora_dropout)


def add_gradcache_args(command: List[str], args: argparse.Namespace) -> None:
    add_flag(command, "--grad_cache", True)
    add_flag(command, "--gc_q_chunk_size", args.gc_q_chunk_size)
    add_flag(command, "--gc_p_chunk_size", args.gc_p_chunk_size)


def python_module(module: str) -> List[str]:
    return ["python", "-m", module]


def torchrun_module(args: argparse.Namespace, module: str) -> List[str]:
    return ["torchrun", f"--nproc_per_node={args.nproc_per_node}", "-m", module]


def deepspeed_module(args: argparse.Namespace, module: str) -> List[str]:
    command = ["deepspeed"]
    add_optional_flag(command, "--include", args.include)
    add_optional_flag(command, "--master_port", args.master_port)
    command.extend(["--module", module])
    return command


def choose_launcher(args: argparse.Namespace, module: str) -> List[str]:
    if args.launcher == "torchrun":
        return torchrun_module(args, module)
    if args.launcher == "deepspeed":
        return deepspeed_module(args, module)
    return python_module(module)


def build_dense(args: argparse.Namespace) -> List[str]:
    command = choose_launcher(args, "tevatron.retriever.driver.train")
    if args.launcher == "deepspeed" or args.deepspeed_config:
        add_flag(command, "--deepspeed", args.deepspeed_config)
    command.append("--do_train")
    command.extend(base_hf_args(args))
    return command


def build_distil(args: argparse.Namespace) -> List[str]:
    command = choose_launcher(args, "tevatron.retriever.driver.train_distil")
    if args.launcher == "deepspeed" or args.deepspeed_config:
        add_flag(command, "--deepspeed", args.deepspeed_config)
    command.append("--do_train")
    command.extend(base_hf_args(args))
    add_flag(command, "--distil_temperature", args.distil_temperature)
    return command


def build_lora(args: argparse.Namespace) -> List[str]:
    command = choose_launcher(args, "tevatron.retriever.driver.train")
    if args.launcher == "deepspeed" or args.deepspeed_config:
        add_flag(command, "--deepspeed", args.deepspeed_config)
    command.append("--do_train")
    command.extend(base_hf_args(args))
    add_lora_args(command, args)
    return command


def build_gradcache(args: argparse.Namespace) -> List[str]:
    command = build_dense(args)
    add_gradcache_args(command, args)
    return command


def build_deepspeed_lora(args: argparse.Namespace) -> List[str]:
    args.launcher = "deepspeed"
    command = build_lora(args)
    return command


def build_jax(args: argparse.Namespace) -> List[str]:
    command = python_module("tevatron.retriever.driver.jax_train")
    command.append("--do_train")
    command.extend(base_hf_args(args))
    add_optional_flag(command, "--dtype", args.jax_dtype)
    add_flag(command, "--untie_encoder", args.untie_encoder)
    if args.grad_cache:
        add_gradcache_args(command, args)
    return command


def build_tevax_lora(args: argparse.Namespace) -> List[str]:
    command = python_module("tevatron.tevax.experimental.mp.train_lora")
    add_flag(command, "--checkpoint_dir", args.output_dir)
    add_flag(command, "--train_file", args.dataset_path or args.dataset_name)
    add_flag(command, "--model_name", args.model_name_or_path)
    add_flag(command, "--model_type", args.model_type)
    command.extend(["--mesh_shape", *args.mesh_shape])
    add_flag(command, "--batch_size", args.batch_size)
    add_flag(command, "--num_target_passages", args.train_group_size)
    add_flag(command, "--learning_rate", args.learning_rate)
    add_flag(command, "--weight_decay", args.weight_decay)
    add_flag(command, "--num_epochs", args.epochs)
    add_flag(command, "--max_query_length", args.query_max_len)
    add_flag(command, "--max_passage_length", args.passage_max_len)
    add_flag(command, "--pooling", args.pooling or "eos")
    add_flag(command, "--scale_by_dim", str(args.scale_by_dim))
    add_flag(command, "--seed", args.seed)
    if args.grad_cache:
        add_flag(command, "--grad_cache", True)
        add_flag(command, "--query_num_chunks", args.query_num_chunks)
        add_flag(command, "--passage_num_chunks", args.passage_num_chunks)
    return command


def build_splade(args: argparse.Namespace) -> List[str]:
    command = ["python", "train_splade.py", "--do_train"]
    command.extend(base_hf_args(args))
    add_flag(command, "--q_flops_loss_factor", args.q_flops_loss_factor)
    add_flag(command, "--p_flops_loss_factor", args.p_flops_loss_factor)
    return command


def build_unicoil(args: argparse.Namespace) -> List[str]:
    command = ["python", "train_unicoil.py", "--do_train"]
    command.extend(base_hf_args(args))
    return command


def validate(args: argparse.Namespace) -> None:
    errors: List[str] = []
    if args.train_group_size < 1:
        errors.append("--train-group-size must be at least 1")
    if args.batch_size < 1:
        errors.append("--batch-size must be at least 1")
    if args.query_max_len < 1 or args.passage_max_len < 1:
        errors.append("sequence lengths must be positive")
    if args.route in {"lora", "deepspeed-lora", "tevax-lora"} and not args.pooling:
        args.pooling = "eos"
    if args.route in {"lora", "deepspeed-lora"} and not args.append_eos_token:
        args.append_eos_token = True
    if args.route == "gradcache":
        args.grad_cache = True
    if args.route in {"gradcache", "jax", "tevax-lora"} and args.grad_cache:
        if args.gc_q_chunk_size < 1 or args.gc_p_chunk_size < 1:
            errors.append("GradCache chunk sizes must be positive")
        if args.route == "jax":
            if args.gc_q_chunk_size > args.batch_size:
                errors.append("--gc-q-chunk-size should not exceed --batch-size for the HF-style JAX route")
            if args.gc_p_chunk_size > args.batch_size * args.train_group_size:
                errors.append("--gc-p-chunk-size should not exceed --batch-size * --train-group-size for the HF-style JAX route")
    if args.route == "deepspeed-lora" and not args.deepspeed_config:
        args.deepspeed_config = "ds_zero3_config.json"
    if args.launcher == "deepspeed" and not args.deepspeed_config:
        args.deepspeed_config = "ds_zero3_config.json"
    if args.route == "distil" and args.distil_temperature <= 0:
        errors.append("--distil-temperature must be positive")
    if args.route in {"splade", "unicoil"} and args.launcher != "python":
        errors.append("Sparse routes print example-driver commands; use --launcher python")
    if args.route == "tevax-lora" and len(args.mesh_shape) < 2:
        errors.append("--mesh-shape must include at least two dimensions, for example: --mesh-shape 1 -1")
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a Tevatron training command plan. The script never executes training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--route", choices=ROUTES, default="dense", help="Training workflow to plan.")
    parser.add_argument("--launcher", choices=("python", "torchrun", "deepspeed"), default="python", help="Launcher for HF-style PyTorch routes.")
    parser.add_argument("--nproc-per-node", type=int, default=1, help="torchrun process count.")
    parser.add_argument("--include", default=None, help="DeepSpeed include string, such as localhost:0,1.")
    parser.add_argument("--master-port", default=None, help="DeepSpeed master port.")
    parser.add_argument("--deepspeed-config", default=None, help="Path to a user-created DeepSpeed JSON config.")

    parser.add_argument("--output-dir", default="model_out", help="Output/checkpoint directory.")
    parser.add_argument("--model-name-or-path", default="bert-base-uncased", help="Backbone model id or local pretrained directory.")
    parser.add_argument("--tokenizer-name", default=None, help="Tokenizer name/path when it differs from the model; useful for adapted sparse drivers.")
    parser.add_argument("--dataset-name", default="Tevatron/wikipedia-nq", help="HF dataset name or loader such as json.")
    parser.add_argument("--dataset-config", default=None, help="Dataset config/subset.")
    parser.add_argument("--dataset-path", default=None, help="Local dataset path, often JSONL.")
    parser.add_argument("--dataset-split", default="train", help="Dataset split.")
    parser.add_argument("--corpus-name", default=None, help="Corpus dataset name for ID-to-corpus training.")
    parser.add_argument("--corpus-path", default=None, help="Local corpus path for ID-to-corpus training.")
    parser.add_argument("--query-prefix", default=None, help="Prefix prepended to query text.")
    parser.add_argument("--passage-prefix", default=None, help="Prefix prepended to passage text.")
    parser.add_argument("--pooling", default=None, help="Pooling method; LoRA routes default to eos when omitted.")
    parser.add_argument("--normalize", action="store_true", help="Add --normalize.")
    parser.add_argument("--temperature", type=float, default=None, help="Contrastive temperature.")
    parser.add_argument("--batch-size", type=int, default=8, help="Per-device batch size for HF routes; global batch size for Tevax MP.")
    parser.add_argument("--train-group-size", type=int, default=2, help="Passages per query.")
    parser.add_argument("--learning-rate", default="1e-5", help="Learning rate string.")
    parser.add_argument("--query-max-len", type=int, default=32, help="Maximum query tokens.")
    parser.add_argument("--passage-max-len", type=int, default=128, help="Maximum passage tokens.")
    parser.add_argument("--epochs", type=float, default=1, help="Training epochs.")
    parser.add_argument("--save-steps", type=int, default=1000, help="Checkpoint save interval.")
    parser.add_argument("--logging-steps", type=int, default=10, help="Logging interval.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1, help="Gradient accumulation steps.")
    parser.add_argument("--gradient-checkpointing", action="store_true", help="Add --gradient_checkpointing.")
    parser.add_argument("--precision", choices=("none", "fp16", "bf16"), default="none", help="Mixed precision flag.")
    parser.add_argument("--attn-implementation", default=None, help="Attention backend: eager, sdpa, or flash_attention_2.")
    parser.add_argument("--append-eos-token", action="store_true", help="Add --append_eos_token.")
    parser.add_argument("--pad-to-multiple-of", type=int, default=None, help="Padding multiple.")
    parser.add_argument("--overwrite-output-dir", action="store_true", help="Add --overwrite_output_dir.")

    parser.add_argument("--lora-name-or-path", default=None, help="Existing LoRA adapter path/name.")
    parser.add_argument("--lora-target-modules", default=DEFAULT_LORA_TARGETS, help="Comma-separated target modules.")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank.")
    parser.add_argument("--lora-alpha", type=int, default=64, help="LoRA alpha.")
    parser.add_argument("--lora-dropout", type=float, default=0.1, help="LoRA dropout.")

    parser.add_argument("--grad-cache", action="store_true", help="Add GradCache flags for compatible routes.")
    parser.add_argument("--gc-q-chunk-size", type=int, default=4, help="HF-style GradCache query chunk size.")
    parser.add_argument("--gc-p-chunk-size", type=int, default=32, help="HF-style GradCache passage chunk size.")
    parser.add_argument("--distil-temperature", type=float, default=0.02, help="Distillation temperature.")

    parser.add_argument("--jax-dtype", default=None, help="JAX dtype such as float32, float16, or bfloat16.")
    parser.add_argument("--untie-encoder", action="store_true", help="JAX dual-encoder separate-parameter route.")
    parser.add_argument("--model-type", default="mistral", help="Tevax MP model type.")
    parser.add_argument("--mesh-shape", nargs="+", default=["1", "-1"], help="Tevax MP mesh shape tokens.")
    parser.add_argument("--weight-decay", default="0.00001", help="Tevax MP weight decay.")
    parser.add_argument("--scale-by-dim", default="True", help="Tevax MP scale_by_dim value.")
    parser.add_argument("--seed", type=int, default=42, help="Tevax MP seed.")
    parser.add_argument("--query-num-chunks", type=int, default=4, help="Tevax MP GradCache query chunks.")
    parser.add_argument("--passage-num-chunks", type=int, default=32, help="Tevax MP GradCache passage chunks.")

    parser.add_argument("--q-flops-loss-factor", default="0.01", help="SPLADE query FLOPS loss factor.")
    parser.add_argument("--p-flops-loss-factor", default="0.01", help="SPLADE passage FLOPS loss factor.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate(args)
    builders = {
        "dense": build_dense,
        "distil": build_distil,
        "lora": build_lora,
        "gradcache": build_gradcache,
        "deepspeed-lora": build_deepspeed_lora,
        "jax": build_jax,
        "tevax-lora": build_tevax_lora,
        "splade": build_splade,
        "unicoil": build_unicoil,
    }
    print(quote_command(builders[args.route](args)))


if __name__ == "__main__":
    main()
