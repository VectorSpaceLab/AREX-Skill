# Copyright 2025 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Safe adapter for LlamaFactory's batch vLLM prediction flow.

By default this script only prints the parameters it would pass to a
LlamaFactory-compatible `vllm_infer` function. Add --execute and --module when
that function is available in the current Python environment.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from typing import Any


def _json_object(value: str) -> str:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"vLLM config must be a JSON object string: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("vLLM config must parse to a JSON object")
    return json.dumps(parsed, separators=(",", ":"))


def _load_callable(module_name: str, function_name: str) -> Callable[..., Any]:
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    if not callable(function):
        raise TypeError(f"{module_name}.{function_name} is not callable")
    return function


def build_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model_name_or_path": args.model_name_or_path,
        "adapter_name_or_path": args.adapter_name_or_path,
        "dataset": args.dataset,
        "dataset_dir": args.dataset_dir,
        "template": args.template,
        "cutoff_len": args.cutoff_len,
        "max_samples": args.max_samples,
        "vllm_config": args.vllm_config,
        "save_name": args.save_name,
        "matrix_save_name": args.matrix_save_name,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "max_new_tokens": args.max_new_tokens,
        "repetition_penalty": args.repetition_penalty,
        "skip_special_tokens": args.skip_special_tokens,
        "default_system": args.default_system,
        "enable_thinking": args.enable_thinking,
        "seed": args.seed,
        "pipeline_parallel_size": args.pipeline_parallel_size,
        "image_max_pixels": args.image_max_pixels,
        "image_min_pixels": args.image_min_pixels,
        "video_fps": args.video_fps,
        "video_maxlen": args.video_maxlen,
        "batch_size": args.batch_size,
    }
    if args.extra_json:
        extra = json.loads(args.extra_json)
        if not isinstance(extra, dict):
            raise ValueError("--extra-json must parse to an object")
        kwargs.update(extra)
    return kwargs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print or execute LlamaFactory batch vLLM prediction parameters.",
        epilog=(
            "Execution requires an environment where LlamaFactory, vLLM, datasets, and the selected model/data "
            "are installed. Without --execute this script performs no imports from LlamaFactory or vLLM."
        ),
    )
    parser.add_argument("--model-name-or-path", required=True, help="Base model id or local model path.")
    parser.add_argument("--adapter-name-or-path", default=None, help="Optional LoRA adapter path.")
    parser.add_argument("--dataset", default="alpaca_en_demo", help="LlamaFactory dataset name.")
    parser.add_argument("--dataset-dir", default="data", help="Directory containing dataset_info.json and data files.")
    parser.add_argument("--template", default="default", help="Prompt template name.")
    parser.add_argument("--cutoff-len", type=int, default=2048, help="Prompt cutoff length.")
    parser.add_argument("--max-samples", type=int, default=None, help="Optional maximum number of samples.")
    parser.add_argument("--vllm-config", type=_json_object, default="{}", help="JSON object string merged into vLLM args.")
    parser.add_argument("--save-name", default="generated_predictions.jsonl", help="Prediction JSONL output path.")
    parser.add_argument("--matrix-save-name", default=None, help="Optional aggregate metrics JSON output path.")
    parser.add_argument("--temperature", type=float, default=0.95, help="Sampling temperature.")
    parser.add_argument("--top-p", type=float, default=0.7, help="Top-p sampling value.")
    parser.add_argument("--top-k", type=int, default=50, help="Top-k sampling value.")
    parser.add_argument("--max-new-tokens", type=int, default=1024, help="Maximum generated tokens.")
    parser.add_argument("--repetition-penalty", type=float, default=1.0, help="Repetition penalty.")
    parser.add_argument("--skip-special-tokens", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--default-system", default=None, help="Optional default system prompt.")
    parser.add_argument("--enable-thinking", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--seed", type=int, default=None, help="Optional vLLM sampling seed.")
    parser.add_argument("--pipeline-parallel-size", type=int, default=1, help="vLLM pipeline parallel size.")
    parser.add_argument("--image-max-pixels", type=int, default=768 * 768)
    parser.add_argument("--image-min-pixels", type=int, default=32 * 32)
    parser.add_argument("--video-fps", type=float, default=2.0)
    parser.add_argument("--video-maxlen", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--extra-json", default=None, help="Optional JSON object of additional keyword arguments.")
    parser.add_argument("--module", default=None, help="Module containing a compatible vllm_infer function for --execute.")
    parser.add_argument("--function", default="vllm_infer", help="Function name inside --module.")
    parser.add_argument("--execute", action="store_true", help="Execute the function instead of only printing parameters.")
    args = parser.parse_args()

    try:
        kwargs = build_kwargs(args)
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("LlamaFactory batch vLLM parameters:")
    print(json.dumps(kwargs, indent=2, ensure_ascii=False))

    if not args.execute:
        print("\nDry run only. Re-run with --execute --module MODULE_NAME when a compatible vllm_infer function is installed.")
        return 0

    if not args.module:
        print("--execute requires --module MODULE_NAME", file=sys.stderr)
        return 2

    try:
        function = _load_callable(args.module, args.function)
        function(**kwargs)
    except Exception as exc:
        print(f"Execution failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
