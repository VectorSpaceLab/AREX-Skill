#!/usr/bin/env python3
"""Print safe ms-swift inference/deployment command skeletons.

The script never launches a model. It only renders a shell command for review.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Iterable, List, Optional

VALID_MODES = ("infer", "deploy", "app")
VALID_BACKENDS = ("transformers", "vllm", "sglang", "lmdeploy")


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None and str(part) != "")


def add_flag(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        value = str(value).lower()
    command.extend([flag, str(value)])


def add_repeated(command: List[str], flag: str, values: Optional[List[str]]) -> None:
    if not values:
        return
    command.append(flag)
    command.extend(values)


def validate_json_object(value: Optional[str], option_name: str) -> Optional[str]:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{option_name} must be a JSON object string: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"{option_name} must decode to a JSON object")
    return json.dumps(parsed, separators=(",", ":"))


def build_command(args: argparse.Namespace) -> List[str]:
    command = ["swift", args.mode]
    add_flag(command, "--model", args.model)
    add_repeated(command, "--adapters", args.adapters)
    add_flag(command, "--merge_lora", args.merge_lora)
    if not (args.mode == "app" and args.base_url):
        add_flag(command, "--infer_backend", args.backend)
    add_flag(command, "--stream", args.stream)
    add_flag(command, "--max_new_tokens", args.max_new_tokens)
    add_flag(command, "--temperature", args.temperature)
    add_flag(command, "--top_p", args.top_p)
    add_flag(command, "--result_path", args.result_path)
    add_flag(command, "--logprobs", args.logprobs)
    add_flag(command, "--top_logprobs", args.top_logprobs)

    if args.mode == "infer":
        add_flag(command, "--val_dataset", args.val_dataset)
        add_flag(command, "--max_batch_size", args.max_batch_size)
        add_flag(command, "--write_batch_size", args.write_batch_size)
        add_flag(command, "--metric", args.metric)
    elif args.mode == "deploy":
        add_flag(command, "--host", args.host)
        add_flag(command, "--port", args.port)
        add_flag(command, "--served_model_name", args.served_model_name)
        add_flag(command, "--api_key", args.api_key)
        add_flag(command, "--max_logprobs", args.max_logprobs)
    elif args.mode == "app":
        add_flag(command, "--base_url", args.base_url)
        add_flag(command, "--studio_title", args.studio_title)
        add_flag(command, "--is_multimodal", args.is_multimodal)
        add_flag(command, "--lang", args.lang)
        add_flag(command, "--server_name", args.server_name)
        add_flag(command, "--server_port", args.server_port)
        add_flag(command, "--share", args.share)

    if args.mode == "app" and args.base_url:
        return command

    if args.backend == "vllm":
        add_flag(command, "--vllm_gpu_memory_utilization", args.vllm_gpu_memory_utilization)
        add_flag(command, "--vllm_tensor_parallel_size", args.vllm_tensor_parallel_size)
        add_flag(command, "--vllm_pipeline_parallel_size", args.vllm_pipeline_parallel_size)
        add_flag(command, "--vllm_data_parallel_size", args.vllm_data_parallel_size)
        add_flag(command, "--vllm_max_model_len", args.vllm_max_model_len)
        add_flag(command, "--vllm_max_num_seqs", args.vllm_max_num_seqs)
        add_flag(command, "--vllm_enforce_eager", args.vllm_enforce_eager)
        add_flag(command, "--vllm_limit_mm_per_prompt", args.vllm_limit_mm_per_prompt)
        add_flag(command, "--vllm_max_lora_rank", args.vllm_max_lora_rank)
    elif args.backend == "sglang":
        add_flag(command, "--sglang_tp_size", args.sglang_tp_size)
        add_flag(command, "--sglang_pp_size", args.sglang_pp_size)
        add_flag(command, "--sglang_dp_size", args.sglang_dp_size)
        add_flag(command, "--sglang_context_length", args.sglang_context_length)
        add_flag(command, "--sglang_mem_fraction_static", args.sglang_mem_fraction_static)
    elif args.backend == "lmdeploy":
        add_flag(command, "--lmdeploy_tp", args.lmdeploy_tp)
        add_flag(command, "--lmdeploy_session_len", args.lmdeploy_session_len)
        add_flag(command, "--lmdeploy_cache_max_entry_count", args.lmdeploy_cache_max_entry_count)
        add_flag(command, "--lmdeploy_quant_policy", args.lmdeploy_quant_policy)
        add_flag(command, "--lmdeploy_vision_batch_size", args.lmdeploy_vision_batch_size)

    return command


def build_env(args: argparse.Namespace) -> List[str]:
    env_parts = []
    if args.cuda_visible_devices:
        env_parts.append(f"CUDA_VISIBLE_DEVICES={shlex.quote(args.cuda_visible_devices)}")
    if args.max_pixels:
        env_parts.append(f"MAX_PIXELS={shlex.quote(str(args.max_pixels))}")
    if args.video_max_pixels:
        env_parts.append(f"VIDEO_MAX_PIXELS={shlex.quote(str(args.video_max_pixels))}")
    if args.fps_max_frames:
        env_parts.append(f"FPS_MAX_FRAMES={shlex.quote(str(args.fps_max_frames))}")
    return env_parts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a safe ms-swift infer/deploy/app command skeleton.")
    parser.add_argument("mode", choices=VALID_MODES)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--backend", choices=VALID_BACKENDS, default="transformers")
    parser.add_argument("--adapters", nargs="*", help="Adapter paths or deploy mappings such as lora1=./adapter")
    parser.add_argument("--merge-lora", dest="merge_lora", action="store_true", default=None)
    parser.add_argument("--stream", choices=("true", "false"), default=None)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--result-path")
    parser.add_argument("--logprobs", choices=("true", "false"))
    parser.add_argument("--top-logprobs", type=int)

    parser.add_argument("--cuda-visible-devices")
    parser.add_argument("--max-pixels", type=int)
    parser.add_argument("--video-max-pixels", type=int)
    parser.add_argument("--fps-max-frames", type=int)

    parser.add_argument("--val-dataset")
    parser.add_argument("--max-batch-size", type=int)
    parser.add_argument("--write-batch-size", type=int)
    parser.add_argument("--metric", choices=("acc", "rouge"))

    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--served-model-name")
    parser.add_argument("--api-key")
    parser.add_argument("--max-logprobs", type=int)

    parser.add_argument("--base-url")
    parser.add_argument("--studio-title")
    parser.add_argument("--is-multimodal", choices=("true", "false"))
    parser.add_argument("--lang", choices=("en", "zh"))
    parser.add_argument("--server-name")
    parser.add_argument("--server-port", type=int)
    parser.add_argument("--share", choices=("true", "false"))

    parser.add_argument("--vllm-gpu-memory-utilization", type=float)
    parser.add_argument("--vllm-tensor-parallel-size", type=int)
    parser.add_argument("--vllm-pipeline-parallel-size", type=int)
    parser.add_argument("--vllm-data-parallel-size", type=int)
    parser.add_argument("--vllm-max-model-len", type=int)
    parser.add_argument("--vllm-max-num-seqs", type=int)
    parser.add_argument("--vllm-enforce-eager", choices=("true", "false"))
    parser.add_argument("--vllm-limit-mm-per-prompt")
    parser.add_argument("--vllm-max-lora-rank", type=int)

    parser.add_argument("--sglang-tp-size", type=int)
    parser.add_argument("--sglang-pp-size", type=int)
    parser.add_argument("--sglang-dp-size", type=int)
    parser.add_argument("--sglang-context-length", type=int)
    parser.add_argument("--sglang-mem-fraction-static", type=float)

    parser.add_argument("--lmdeploy-tp", type=int)
    parser.add_argument("--lmdeploy-session-len", type=int)
    parser.add_argument("--lmdeploy-cache-max-entry-count", type=float)
    parser.add_argument("--lmdeploy-quant-policy", type=int, choices=(0, 4, 8))
    parser.add_argument("--lmdeploy-vision-batch-size", type=int)

    args = parser.parse_args()
    args.vllm_limit_mm_per_prompt = validate_json_object(
        args.vllm_limit_mm_per_prompt, "--vllm-limit-mm-per-prompt")
    if args.mode == "app" and args.base_url:
        backend_specific = [
            name for name, value in vars(args).items()
            if (name.startswith("vllm_") or name.startswith("sglang_") or name.startswith("lmdeploy_"))
            and value is not None
        ]
        if backend_specific:
            parser.error("--base-url app mode connects to an existing service; omit backend-specific launch flags unless self-deploying")
    return args


def main() -> int:
    args = parse_args()
    env_parts = build_env(args)
    command = build_command(args)
    rendered = shell_join(command)
    if env_parts:
        rendered = " ".join(env_parts + [rendered])
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
