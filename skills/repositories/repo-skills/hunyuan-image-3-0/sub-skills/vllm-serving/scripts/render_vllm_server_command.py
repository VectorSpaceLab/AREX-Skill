#!/usr/bin/env python3
"""Render the HunyuanImage-3.0 vLLM server command.

This script mirrors the inspected shell wrapper in vllm_infer/run_vllm_server.sh
without starting a server. It is safe to run in a non-serving environment
because it only prints or writes the launch command.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

DEFAULT_ALIAS = "vllm_hunyuan_image3"
DEFAULT_SAVE_PATH = "/tmp/hunyuan_image3/png/"
DEFAULT_MAX_MODEL_LEN = 10000
DEFAULT_GPU_MEMORY_UTILIZATION = 0.6
DEFAULT_MAX_NUM_BATCHED_TOKENS = 10000
DEFAULT_MAX_NUM_SEQS = 1
DEFAULT_TP = 8


def shell_quote(value):
    return shlex.quote(str(value))


def render_script(args):
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Requires the custom vLLM branch feature/hunyuan_image_3.0.",
        "# Endpoint: http://localhost:8000/v1/chat/completions",
        f"export VLLM_ENABLE_HUNYUAN_IMAGE3_TASK=1",
        f"export MULTI_MODA_SAVE_PATH={shell_quote(args.save_path)}",
        "",
        f"vllm serve {shell_quote(args.model_path)} \\",
        "    --trust-remote-code \\",
        f"    --served-model-name {shell_quote(args.served_model_name)} \\",
        f"    --max-model-len {args.max_model_len} \\",
        f"    --gpu-memory-utilization {args.gpu_memory_utilization} \\",
        "    --no-enable-prefix-caching \\",
        "    --no-enable-chunked-prefill \\",
        f"    --max-num-batched-tokens {args.max_num_batched_tokens} \\",
        f"    --max-num-seqs {args.max_num_seqs} \\",
        "    --enforce-eager \\",
        "    --trust-request-chat-template \\",
        f"    -tp {args.tensor_parallel_size}",
    ]
    return "\n".join(lines) + "\n"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render a safe vLLM server command for HunyuanImage-3.0"
    )
    parser.add_argument(
        "model_path",
        help="Path to the mounted or local model checkpoint",
    )
    parser.add_argument(
        "--served-model-name",
        default=DEFAULT_ALIAS,
        help="Client-facing alias that should match the request model field",
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=int,
        default=DEFAULT_TP,
        help="Tensor parallel size used in the repo shell wrapper",
    )
    parser.add_argument(
        "--save-path",
        default=DEFAULT_SAVE_PATH,
        help="Value for MULTI_MODA_SAVE_PATH",
    )
    parser.add_argument(
        "--max-model-len",
        type=int,
        default=DEFAULT_MAX_MODEL_LEN,
        help="vLLM max model length",
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=DEFAULT_GPU_MEMORY_UTILIZATION,
        help="vLLM GPU memory utilization cap",
    )
    parser.add_argument(
        "--max-num-batched-tokens",
        type=int,
        default=DEFAULT_MAX_NUM_BATCHED_TOKENS,
        help="vLLM max number of batched tokens",
    )
    parser.add_argument(
        "--max-num-seqs",
        type=int,
        default=DEFAULT_MAX_NUM_SEQS,
        help="vLLM max number of sequences",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered shell script",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rendered = render_script(args)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    print(rendered, end="")


if __name__ == "__main__":
    main()
