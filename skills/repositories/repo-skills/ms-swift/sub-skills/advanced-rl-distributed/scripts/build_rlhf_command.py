#!/usr/bin/env python3
"""Build safe ms-swift RLHF/Ray/Megatron command skeletons.

This helper prints commands or Ray YAML templates. It never launches training.
Replace placeholder model, dataset, plugin, and output values before running.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def backslash_command(env: Iterable[str], command: List[str]) -> str:
    lines: List[str] = []
    for item in env:
        lines.append(f"{item} \\")
    for index, part in enumerate(command):
        suffix = " \\" if index < len(command) - 1 else ""
        if index == 0:
            lines.append(f"{part}{suffix}")
        elif part.startswith("--"):
            lines.append(f"  {part}{suffix}")
        else:
            lines.append(f"  {shlex.quote(str(part))}{suffix}")
    return "\n".join(lines)


def csv_devices(gpus: int, start: int = 0) -> str:
    return ",".join(str(i) for i in range(start, start + gpus))


def parse_reward_funcs(value: str) -> List[str]:
    return [item for item in value.replace(",", " ").split() if item]


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", required=True, choices=[
        "swift-grpo",
        "swift-gkd",
        "swift-rollout-server",
        "swift-sample",
        "megatron-grpo",
        "megatron-gkd",
        "ray-grpo-colocate",
        "ray-grpo-separate",
    ])
    parser.add_argument("--model", default="<model-id-or-path>")
    parser.add_argument("--teacher-model", default="<teacher-model-id-or-path>")
    parser.add_argument("--teacher-server", default="")
    parser.add_argument("--dataset", default="<dataset-id-or-path>")
    parser.add_argument("--output-dir", default="<output-dir>")
    parser.add_argument("--external-plugin", default="")
    parser.add_argument("--reward-funcs", default="accuracy format")
    parser.add_argument("--gpus", type=int, default=4)
    parser.add_argument("--rollout-gpus", type=int, default=2)
    parser.add_argument("--rollout-host", default="127.0.0.1")
    parser.add_argument("--rollout-port", type=int, default=8000)
    parser.add_argument("--num-generations", type=int, default=8)
    parser.add_argument("--steps-per-generation", type=int, default=4)
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--max-completion-length", type=int, default=1024)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--micro-batch-size", type=int, default=2)
    parser.add_argument("--global-batch-size", type=int, default=16)
    parser.add_argument("--tp", type=int, default=1, help="Megatron tensor parallel size")
    parser.add_argument("--pp", type=int, default=1, help="Megatron pipeline parallel size")
    parser.add_argument("--cp", type=int, default=1, help="Megatron context parallel size")
    parser.add_argument("--ep", type=int, default=1, help="Megatron expert parallel size")
    parser.add_argument("--vllm-tp", type=int, default=1)
    parser.add_argument("--vllm-gpu-memory-utilization", type=float, default=0.6)
    parser.add_argument("--vllm-max-model-len", type=int, default=8192)
    parser.add_argument("--loss-type", default="grpo")
    parser.add_argument("--beta", default="0.04")
    parser.add_argument("--temperature", default="1.0")
    parser.add_argument("--gkd-logits-topk", type=int, default=64)
    parser.add_argument("--lmbda", default="0.5")
    parser.add_argument("--sampler-engine", default="vllm")
    parser.add_argument("--num-return-sequences", type=int, default=8)
    parser.add_argument("--n-best-to-keep", type=int, default=2)


def maybe_plugin_args(args: argparse.Namespace) -> List[str]:
    return ["--external_plugins", args.external_plugin] if args.external_plugin else []


def reward_args(args: argparse.Namespace) -> List[str]:
    rewards = parse_reward_funcs(args.reward_funcs)
    return ["--reward_funcs", *rewards] if rewards else []


def swift_grpo(args: argparse.Namespace) -> str:
    command = [
        "swift", "rlhf",
        "--rlhf_type", "grpo",
        "--model", args.model,
        "--dataset", args.dataset,
        "--num_generations", args.num_generations,
        "--per_device_train_batch_size", args.per_device_train_batch_size,
        "--gradient_accumulation_steps", args.gradient_accumulation_steps,
        "--steps_per_generation", args.steps_per_generation,
        "--max_length", args.max_length,
        "--max_completion_length", args.max_completion_length,
        "--loss_type", args.loss_type,
        "--beta", args.beta,
        "--temperature", args.temperature,
        *maybe_plugin_args(args),
        *reward_args(args),
        "--use_vllm", "true",
        "--vllm_mode", "colocate",
        "--vllm_tensor_parallel_size", args.vllm_tp,
        "--vllm_gpu_memory_utilization", args.vllm_gpu_memory_utilization,
        "--sleep_level", "1",
        "--offload_model", "true",
        "--offload_optimizer", "true",
        "--output_dir", args.output_dir,
    ]
    env = [f"CUDA_VISIBLE_DEVICES={csv_devices(args.gpus)}"]
    return backslash_command(env, [str(x) for x in command])


def swift_gkd(args: argparse.Namespace) -> str:
    teacher = ["--teacher_model_server", args.teacher_server] if args.teacher_server else ["--teacher_model", args.teacher_model]
    command = [
        "swift", "rlhf",
        "--rlhf_type", "gkd",
        "--model", args.model,
        *teacher,
        "--dataset", args.dataset,
        "--gkd_logits_topk", args.gkd_logits_topk,
        "--beta", args.beta if args.beta != "0.04" else "0.5",
        "--lmbda", args.lmbda,
        "--temperature", args.temperature,
        "--max_length", args.max_length,
        "--max_completion_length", args.max_completion_length,
        "--use_vllm", "true",
        "--vllm_mode", "colocate",
        "--output_dir", args.output_dir,
    ]
    env = [f"CUDA_VISIBLE_DEVICES={csv_devices(args.gpus)}"]
    return backslash_command(env, [str(x) for x in command])


def swift_rollout_server(args: argparse.Namespace) -> str:
    command = [
        "swift", "rollout",
        "--model", args.model,
        "--vllm_tensor_parallel_size", args.vllm_tp,
        "--vllm_data_parallel_size", max(1, args.rollout_gpus // max(1, args.vllm_tp)),
        "--vllm_max_model_len", args.vllm_max_model_len,
        "--vllm_gpu_memory_utilization", args.vllm_gpu_memory_utilization,
        "--host", "0.0.0.0",
        "--port", args.rollout_port,
    ]
    env = [f"CUDA_VISIBLE_DEVICES={csv_devices(args.rollout_gpus)}"]
    return backslash_command(env, [str(x) for x in command])


def swift_sample(args: argparse.Namespace) -> str:
    command = [
        "swift", "sample",
        "--model", args.model,
        "--dataset", args.dataset,
        "--sampler_engine", args.sampler_engine,
        "--num_return_sequences", args.num_return_sequences,
        "--n_best_to_keep", args.n_best_to_keep,
        "--orm_model", parse_reward_funcs(args.reward_funcs)[0] if parse_reward_funcs(args.reward_funcs) else "<orm-name>",
        *maybe_plugin_args(args),
    ]
    env = [f"CUDA_VISIBLE_DEVICES={csv_devices(args.gpus)}"]
    return backslash_command(env, [str(x) for x in command])


def megatron_base(args: argparse.Namespace, rlhf_type: str) -> List[str]:
    command = [
        "megatron", "rlhf",
        "--rlhf_type", rlhf_type,
        "--model", args.model,
        "--dataset", args.dataset,
        "--tensor_model_parallel_size", args.tp,
        "--pipeline_model_parallel_size", args.pp,
        "--context_parallel_size", args.cp,
        "--expert_model_parallel_size", args.ep,
        "--micro_batch_size", args.micro_batch_size,
        "--global_batch_size", args.global_batch_size,
        "--steps_per_generation", args.steps_per_generation,
        "--max_length", args.max_length,
        "--max_completion_length", args.max_completion_length,
        "--bf16", "true",
        "--recompute_granularity", "selective",
        "--finetune", "true",
        "--save_safetensors", "true",
        "--output_dir", args.output_dir,
    ]
    return [str(x) for x in command]


def megatron_grpo(args: argparse.Namespace) -> str:
    command = megatron_base(args, "grpo") + [
        "--num_generations", str(args.num_generations),
        "--loss_type", args.loss_type,
        "--beta", args.beta,
        "--temperature", args.temperature,
        *maybe_plugin_args(args),
        *reward_args(args),
        "--use_vllm", "true",
        "--vllm_mode", "colocate",
        "--vllm_tensor_parallel_size", str(args.vllm_tp),
        "--vllm_gpu_memory_utilization", str(args.vllm_gpu_memory_utilization),
        "--sleep_level", "1",
        "--offload_model", "true",
        "--offload_optimizer", "true",
    ]
    env = [f"CUDA_VISIBLE_DEVICES={csv_devices(args.gpus)}", f"NPROC_PER_NODE={args.gpus}", "MASTER_PORT=29600"]
    return batch_notes(args) + "\n\n" + backslash_command(env, command)


def megatron_gkd(args: argparse.Namespace) -> str:
    teacher = ["--teacher_model_server", args.teacher_server] if args.teacher_server else ["--teacher_model", args.teacher_model]
    command = megatron_base(args, "gkd") + [
        *teacher,
        "--gkd_logits_topk", str(args.gkd_logits_topk),
        "--beta", args.beta if args.beta != "0.04" else "0.5",
        "--lmbda", args.lmbda,
        "--temperature", args.temperature,
        "--use_vllm", "true",
        "--vllm_mode", "colocate",
        "--vllm_tensor_parallel_size", str(args.vllm_tp),
        "--offload_teacher_model", "true",
    ]
    env = [f"CUDA_VISIBLE_DEVICES={csv_devices(args.gpus)}", f"NPROC_PER_NODE={args.gpus}", "MASTER_PORT=29600"]
    return batch_notes(args, gkd=True) + "\n\n" + backslash_command(env, command)


def batch_notes(args: argparse.Namespace, gkd: bool = False) -> str:
    denom = args.tp * args.pp * args.cp
    notes = ["# Megatron batch/parallel sanity notes"]
    if denom <= 0:
        notes.append("# Invalid TP/PP/CP product.")
        return "\n".join(notes)
    if args.gpus % denom != 0:
        notes.append(f"# WARNING: world_size {args.gpus} is not divisible by TP*PP*CP {denom}.")
        return "\n".join(notes)
    dp_size = args.gpus // denom
    generation_batch_size = args.global_batch_size * args.steps_per_generation
    notes.append(f"# dp_size = {args.gpus} / ({args.tp} * {args.pp} * {args.cp}) = {dp_size}")
    if not gkd:
        rollout_prompts = generation_batch_size // args.num_generations if args.num_generations else 0
        train_prompts = args.global_batch_size // args.num_generations if args.num_generations else 0
        notes.append(f"# generation_batch_size = {args.global_batch_size} * {args.steps_per_generation} = {generation_batch_size}")
        notes.append(f"# rollout_prompt_count = {generation_batch_size} / {args.num_generations} = {rollout_prompts}")
        notes.append(f"# train_prompt_count = {args.global_batch_size} / {args.num_generations} = {train_prompts}")
        if generation_batch_size % args.num_generations != 0:
            notes.append("# WARNING: generation_batch_size must be divisible by num_generations.")
        if rollout_prompts and rollout_prompts % dp_size != 0:
            notes.append("# WARNING: rollout_prompt_count must be divisible by dp_size.")
    return "\n".join(notes)


def yaml_list(values: Iterable[str]) -> str:
    return "[" + ", ".join(values) + "]"


def ray_grpo(args: argparse.Namespace, colocate: bool) -> str:
    rewards = parse_reward_funcs(args.reward_funcs)
    external = f"external_plugins: {args.external_plugin}\n" if args.external_plugin else ""
    colocate_block = "colocate_groups: [[train, rollout]]\noffload_model: true\noffload_optimizer: true\nsleep_level: 1\n" if colocate else ""
    rollout_memory = "0.4" if colocate else str(args.vllm_gpu_memory_utilization)
    return f"""# Save this template as a YAML file, then run:
# megatron rlhf --use_ray true --config <config.yaml>
rlhf_type: grpo
model: {args.model}
dataset: {args.dataset}
{external}reward_funcs: {yaml_list(rewards) if rewards else "[]"}

micro_batch_size: {args.micro_batch_size}
global_batch_size: {args.global_batch_size}
num_generations: {args.num_generations}
steps_per_generation: {args.steps_per_generation}
max_length: {args.max_length}
max_completion_length: {args.max_completion_length}
loss_type: {args.loss_type}
beta: {args.beta}
temperature: {args.temperature}
use_vllm: true
{colocate_block}train:
  gpus: {args.gpus}
  tensor_model_parallel_size: {args.tp}
  pipeline_model_parallel_size: {args.pp}
  context_parallel_size: {args.cp}
  expert_model_parallel_size: {args.ep}
  output_dir: {args.output_dir}
rollout:
  gpus: {args.gpus if colocate else args.rollout_gpus}
  vllm_tensor_parallel_size: {args.vllm_tp}
  vllm_gpu_memory_utilization: {rollout_memory}
  vllm_max_model_len: {args.vllm_max_model_len}
""".rstrip()


def build(args: argparse.Namespace) -> str:
    if args.mode == "swift-grpo":
        return swift_grpo(args)
    if args.mode == "swift-gkd":
        return swift_gkd(args)
    if args.mode == "swift-rollout-server":
        return swift_rollout_server(args)
    if args.mode == "swift-sample":
        return swift_sample(args)
    if args.mode == "megatron-grpo":
        return megatron_grpo(args)
    if args.mode == "megatron-gkd":
        return megatron_gkd(args)
    if args.mode == "ray-grpo-colocate":
        return ray_grpo(args, colocate=True)
    if args.mode == "ray-grpo-separate":
        return ray_grpo(args, colocate=False)
    raise ValueError(f"Unsupported mode: {args.mode}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    args = parser.parse_args(argv)
    print(build(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
