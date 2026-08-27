#!/usr/bin/env python3
"""Safe CoRAG service-plan generator.

This script prints a checklist and command concepts for a CoRAG multihop QA run.
It does not download embeddings, start servers, probe ports, import repository code,
load models, or run evaluation.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Dict, Iterable, List, Tuple

DEFAULT_TASKS: Dict[str, str] = {
    "2wikimultihopqa": "validation",
    "bamboogle": "test",
    "hotpotqa": "validation",
    "musique": "validation",
}


def _positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {text!r}") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return value


def _port(text: str) -> int:
    value = _positive_int(text)
    if value > 65535:
        raise argparse.ArgumentTypeError("port must be <= 65535")
    return value


def _gpu_count(text: str) -> str:
    if text == "auto":
        return text
    value = _positive_int(text)
    return str(value)


def _split_csv(text: str) -> List[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def _parse_tasks(tasks_text: str, custom_split: str) -> List[Tuple[str, str]]:
    names = _split_csv(tasks_text)
    if not names or names == ["all"]:
        return list(DEFAULT_TASKS.items())
    if "all" in names and len(names) > 1:
        raise ValueError("use either --tasks all or a comma-separated task list, not both")
    parsed: List[Tuple[str, str]] = []
    for name in names:
        parsed.append((name, DEFAULT_TASKS.get(name, custom_split)))
    return parsed


def _quote_env(name: str, value: object) -> str:
    return f"{name}={shlex.quote(str(value))}"


def _join(parts: Iterable[object]) -> str:
    return shlex.join([str(part) for part in parts])


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    if args.e5_port == args.vllm_port:
        raise ValueError("E5 and vLLM ports must be different")

    tasks = _parse_tasks(args.tasks, args.custom_split)
    tp_value = "$(nvidia-smi --list-gpus | wc -l)" if args.gpu_count == "auto" else args.gpu_count

    download_command = _join(
        [
            "huggingface-cli",
            "download",
            "corag/kilt-corpus-embeddings",
            "--repo-type",
            "dataset",
            "--include",
            "e5-large-shard-*.pt",
            "--local-dir",
            args.embedding_dir,
        ]
    )

    e5_command = " ".join(
        [
            _quote_env("INDEX_DIR", args.embedding_dir),
            _quote_env("E5_MODEL_NAME_OR_PATH", args.e5_model),
            _quote_env("TOP_K", args.top_k),
            _quote_env("PYTHONPATH", "src"),
            _join(
                [
                    "uvicorn",
                    "src.search.start_e5_server_main:app",
                    "--host",
                    args.host,
                    "--port",
                    args.e5_port,
                ]
            ),
            ">",
            shlex.quote(args.e5_log),
            "2>&1 &",
        ]
    )

    if args.gpu_count == "auto":
        vllm_prefix = "TP_SIZE=$(nvidia-smi --list-gpus | wc -l); "
        tensor_parallel_value = "$TP_SIZE"
    else:
        vllm_prefix = ""
        tensor_parallel_value = tp_value
    vllm_parts = [
        "vllm",
        "serve",
        args.model,
        "--host",
        args.host,
        "--port",
        args.vllm_port,
        "--dtype",
        "auto",
        "--disable-log-requests",
        "--disable-custom-all-reduce",
        "--enable_chunked_prefill",
        "--max_num_batched_tokens",
        args.max_num_batched_tokens,
        "--tensor-parallel-size",
        tensor_parallel_value,
        "--max-model-len",
        args.max_model_len,
        "--gpu_memory_utilization",
        args.gpu_memory_utilization,
        "--api-key",
        args.api_key,
    ]
    vllm_command = vllm_prefix + _join(vllm_parts) + " > " + shlex.quote(args.vllm_log) + " 2>&1 &"

    eval_jobs: List[Dict[str, object]] = []
    for task_name, split in tasks:
        output_subdir = f"{args.output_dir.rstrip('/')}/{args.max_path_length}"
        command_parts: List[object] = [
            "torchrun",
            "--nproc_per_node",
            1,
            "src/inference/run_inference.py",
            "--eval_task",
            task_name,
            "--eval_split",
            split,
            "--max_path_length",
            args.max_path_length,
            "--output_dir",
            output_subdir,
            "--do_eval",
            "--num_threads",
            args.num_threads,
            "--overwrite_output_dir",
            "--disable_tqdm",
            "True",
            "--report_to",
            "none",
            "--decode_strategy",
            args.decode_strategy,
            "--context_placement",
            args.context_placement,
            "--num_contexts",
            args.num_contexts,
        ]
        if args.decode_strategy == "best_of_n":
            command_parts += ["--best_n", args.best_n]
        if args.dry_run:
            command_parts += ["--dry_run", "True"]
        command = " ".join([_quote_env("OUTPUT_DIR", args.output_dir), _quote_env("PYTHONPATH", "src"), _join(command_parts)])
        eval_jobs.append(
            {
                "task": task_name,
                "split": split,
                "command_concept": command,
                "expected_prediction_file": f"{output_subdir}/preds_{args.decode_strategy}_{task_name}_{split}.jsonl",
                "expected_metrics_file": f"{output_subdir}/metrics_{task_name}_{split}_{args.decode_strategy}.json",
            }
        )

    plan: Dict[str, object] = {
        "script_mode": "planning_only_no_execution",
        "safety": [
            "Review this plan before running any external command.",
            "The script did not check ports, start services, download files, load models, or run evaluation.",
            "Treat command_concept values as templates to adapt in a prepared CoRAG checkout.",
        ],
        "resources": {
            "embedding_dataset": "corag/kilt-corpus-embeddings",
            "corpus_dataset": "corag/kilt-corpus",
            "eval_dataset": "corag/multihopqa",
            "e5_model": args.e5_model,
            "generator_model": args.model,
        },
        "required_ports": [
            {"service": "E5 search", "host": args.host, "port": args.e5_port, "log": args.e5_log},
            {"service": "vLLM OpenAI API", "host": args.host, "port": args.vllm_port, "log": args.vllm_log},
        ],
        "preflight_checklist": [
            "Confirm CUDA GPUs are available; public CoRAG recipe used 8x A100 40GB.",
            "Confirm the embedding directory will contain forty e5-large shard files before starting E5.",
            "Confirm model and dataset access in the local Hugging Face cache or network policy.",
            "Confirm ports are free or are already occupied by the intended services.",
            "Start the E5 search service before the vLLM service, and start evaluation last.",
        ],
        "steps": [
            {
                "id": "stage_embeddings",
                "objective": "Stage E5 corpus embedding shards.",
                "required_evidence": ["forty e5-large-shard-*.pt files", f"embedding_dir={args.embedding_dir}"],
                "command_concept": download_command,
                "notes": ["Skip only if all shards are already present and readable."],
            },
            {
                "id": "start_e5_search_server",
                "objective": "Serve dense retrieval over the staged embeddings.",
                "port": args.e5_port,
                "log": args.e5_log,
                "command_concept": e5_command,
                "notes": ["Requires CUDA in the inspected implementation.", "Uses INDEX_DIR, E5_MODEL_NAME_OR_PATH, and TOP_K."],
            },
            {
                "id": "start_vllm_server",
                "objective": "Serve the CoRAG generator through an OpenAI-compatible vLLM endpoint.",
                "port": args.vllm_port,
                "log": args.vllm_log,
                "command_concept": vllm_command,
                "notes": [
                    "The CoRAG client discovers the served model id through the models endpoint.",
                    "Tensor parallelism should match the real GPU allocation, not merely the host GPU count, when using schedulers.",
                ],
            },
            {
                "id": "run_multihopqa_inference",
                "objective": "Run CoRAG inference after both services are ready.",
                "jobs": eval_jobs,
            },
        ],
        "settings": {
            "max_path_length": args.max_path_length,
            "decode_strategy": args.decode_strategy,
            "num_threads": args.num_threads,
            "num_contexts": args.num_contexts,
            "context_placement": args.context_placement,
            "dry_run": args.dry_run,
        },
        "expected_metric_fields": [
            "em",
            "f1",
            "num_samples",
            "eval_task",
            "eval_split",
            "max_path_length",
            "decode_strategy",
            "token_consumed",
            "average_token_consumed_per_sample",
        ],
        "warnings": [
            "End-to-end CoRAG is GPU/server heavy and was not run by this planner.",
            "Increasing max_path_length, tree_search, or best_of_n can multiply retriever and model calls.",
            "A port-open check alone does not prove the correct model or index is being served.",
        ],
    }
    return plan


def print_markdown(plan: Dict[str, object]) -> None:
    print("# CoRAG service plan")
    print()
    print(f"Mode: `{plan['script_mode']}`")
    print()

    print("## Safety")
    for item in plan["safety"]:  # type: ignore[index]
        print(f"- {item}")
    print()

    print("## Resources")
    for key, value in plan["resources"].items():  # type: ignore[union-attr]
        print(f"- `{key}`: `{value}`")
    print()

    print("## Required ports and logs")
    for entry in plan["required_ports"]:  # type: ignore[index]
        print(f"- {entry['service']}: {entry['host']}:{entry['port']} -> `{entry['log']}`")
    print()

    print("## Preflight checklist")
    for item in plan["preflight_checklist"]:  # type: ignore[index]
        print(f"- [ ] {item}")
    print()

    print("## Steps")
    for step in plan["steps"]:  # type: ignore[index]
        print(f"### {step['id']}")
        print(step["objective"])
        if "port" in step:
            print(f"- Port: `{step['port']}`")
        if "log" in step:
            print(f"- Log: `{step['log']}`")
        if "required_evidence" in step:
            print("- Required evidence:")
            for item in step["required_evidence"]:
                print(f"  - {item}")
        if "command_concept" in step:
            print("- Command concept:")
            print("```bash")
            print(step["command_concept"])
            print("```")
        if "jobs" in step:
            print("- Evaluation jobs:")
            for job in step["jobs"]:
                print(f"  - `{job['task']}` / `{job['split']}`")
                print("    - Command concept:")
                print("      ```bash")
                print("      " + job["command_concept"])
                print("      ```")
                print(f"    - Predictions: `{job['expected_prediction_file']}`")
                print(f"    - Metrics: `{job['expected_metrics_file']}`")
        if "notes" in step:
            print("- Notes:")
            for item in step["notes"]:
                print(f"  - {item}")
        print()

    print("## Settings")
    for key, value in plan["settings"].items():  # type: ignore[union-attr]
        print(f"- `{key}`: `{value}`")
    print()

    print("## Expected metric fields")
    for item in plan["expected_metric_fields"]:  # type: ignore[index]
        print(f"- `{item}`")
    print()

    print("## Warnings")
    for item in plan["warnings"]:  # type: ignore[index]
        print(f"- {item}")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a safe CoRAG service/evaluation checklist; execute nothing.")
    parser.add_argument("--tasks", default="all", help="Comma-separated task names or 'all'.")
    parser.add_argument("--custom-split", default="validation", help="Split to use for task names not in the built-in table.")
    parser.add_argument("--embedding-dir", default="data/e5-large-index", help="Relative or user-approved embedding directory.")
    parser.add_argument("--output-dir", default="tmp", help="Relative or user-approved output directory.")
    parser.add_argument("--e5-model", default="intfloat/e5-large-v2", help="E5 model id or prepared local model name.")
    parser.add_argument("--model", default="corag/CoRAG-Llama3.1-8B-MultihopQA", help="CoRAG generator model id or prepared local model name.")
    parser.add_argument("--host", default="localhost", help="Host interface for service command concepts.")
    parser.add_argument("--e5-port", type=_port, default=8090, help="E5 search server port.")
    parser.add_argument("--vllm-port", type=_port, default=8000, help="vLLM OpenAI API port.")
    parser.add_argument("--e5-log", default="e5_server.log", help="E5 server log filename.")
    parser.add_argument("--vllm-log", default="vllm_server.log", help="vLLM server log filename.")
    parser.add_argument("--top-k", type=_positive_int, default=5, help="Retriever top-k used by the E5 service.")
    parser.add_argument("--gpu-count", type=_gpu_count, default="auto", help="Positive integer tensor-parallel size or 'auto'.")
    parser.add_argument("--max-path-length", type=_positive_int, default=6, help="CoRAG maximum retrieval-chain length.")
    parser.add_argument("--decode-strategy", choices=["greedy", "tree_search", "best_of_n"], default="greedy")
    parser.add_argument("--best-n", type=_positive_int, default=4, help="Number of paths for best_of_n.")
    parser.add_argument("--sample-temperature", default="0.7", help="Recorded planning value for non-greedy path search.")
    parser.add_argument("--num-threads", type=_positive_int, default=32)
    parser.add_argument("--num-contexts", type=_positive_int, default=20)
    parser.add_argument("--context-placement", choices=["forward", "backward", "random"], default="backward")
    parser.add_argument("--max-model-len", type=_positive_int, default=8192)
    parser.add_argument("--max-num-batched-tokens", type=_positive_int, default=2048)
    parser.add_argument("--gpu-memory-utilization", default="0.5")
    parser.add_argument("--api-key", default="token-123")
    parser.add_argument("--dry-run", action="store_true", help="Plan a tiny debug evaluation subset.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_markdown(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
