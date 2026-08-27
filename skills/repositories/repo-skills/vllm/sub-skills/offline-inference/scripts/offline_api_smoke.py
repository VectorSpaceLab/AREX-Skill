#!/usr/bin/env python3
"""Safe vLLM offline API smoke-check helper.

By default this script prints a plan and exits without loading a model. It only
constructs ``vllm.LLM`` and runs inference when the caller supplies ``--model``
and does not pass ``--skip-run``.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or run a short vLLM offline LLM.generate/LLM.chat smoke check."
    )
    parser.add_argument(
        "--model",
        help=(
            "User-supplied Hugging Face model id or local model path. If omitted, "
            "the script prints the plan and does not load a model."
        ),
    )
    parser.add_argument(
        "--prompt",
        default="The capital of France is",
        help="Prompt or user message for the smoke check.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8,
        help="Maximum generated tokens for a short smoke check.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature; 0.0 is deterministic/greedy.",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Use LLM.chat with OpenAI-style messages instead of raw LLM.generate.",
    )
    parser.add_argument(
        "--runner",
        default="auto",
        help="LLM runner value; keep auto for generation, use pooling for pooling models.",
    )
    parser.add_argument(
        "--dtype",
        default="auto",
        help="Model dtype passed to LLM, for example auto, float16, bfloat16, or float32.",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Allow execution of model repository code. Use only for trusted models.",
    )
    parser.add_argument(
        "--enforce-eager",
        action="store_true",
        help="Disable CUDA graph execution; useful for small debug runs on some backends.",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Print the validated plan but do not import vLLM or load a model.",
    )
    parser.add_argument(
        "--print-plan",
        action="store_true",
        help="Print the validated plan. This is the default behavior when --model is omitted.",
    )
    return parser


def print_plan(args: argparse.Namespace) -> None:
    mode = "LLM.chat" if args.chat else "LLM.generate"
    print("vLLM offline API smoke plan")
    print(f"  mode: {mode}")
    print(f"  model: {args.model or '<not supplied; no model will be loaded>'}")
    print(f"  prompt: {args.prompt!r}")
    print(f"  max_tokens: {args.max_tokens}")
    print(f"  temperature: {args.temperature}")
    print(f"  runner: {args.runner}")
    print(f"  dtype: {args.dtype}")
    print(f"  trust_remote_code: {args.trust_remote_code}")
    print(f"  enforce_eager: {args.enforce_eager}")


def run_smoke(args: argparse.Namespace) -> int:
    try:
        import vllm
        from vllm import LLM, SamplingParams
    except Exception as exc:  # pragma: no cover - depends on caller env
        print(f"ERROR: failed to import vLLM: {exc}", file=sys.stderr)
        return 2

    print(f"Imported vLLM version: {getattr(vllm, '__version__', 'unknown')}")
    sampling_params = SamplingParams(
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    llm_kwargs: dict[str, Any] = {
        "model": args.model,
        "runner": args.runner,
        "dtype": args.dtype,
        "trust_remote_code": args.trust_remote_code,
        "enforce_eager": args.enforce_eager,
    }

    try:
        llm = LLM(**llm_kwargs)
        if args.chat:
            messages = [{"role": "user", "content": args.prompt}]
            outputs = llm.chat(messages, sampling_params=sampling_params, use_tqdm=False)
        else:
            outputs = llm.generate([args.prompt], sampling_params, use_tqdm=False)
    except Exception as exc:  # pragma: no cover - depends on model/backend
        print(f"ERROR: vLLM smoke run failed: {exc}", file=sys.stderr)
        return 1

    for index, output in enumerate(outputs):
        completions = getattr(output, "outputs", [])
        text = completions[0].text if completions else ""
        print(f"RESULT {index}: {text!r}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.max_tokens < 1:
        parser.error("--max-tokens must be >= 1")

    should_only_plan = args.skip_run or args.print_plan or not args.model
    if should_only_plan:
        print_plan(args)
        if not args.model:
            print("No --model supplied; exiting without importing vLLM or loading weights.")
        elif args.skip_run:
            print("--skip-run supplied; exiting without importing vLLM or loading weights.")
        return 0

    print_plan(args)
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
