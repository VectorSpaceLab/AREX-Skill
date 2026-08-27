#!/usr/bin/env python3
"""Dry-run validators for UniLM architecture/training command plans.

This helper never launches training, evaluation, downloads, or credentialed services.
It validates required arguments, prints warnings, and emits a command template that
can be adapted in a prepared environment.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable


def path_status(value: str | None, expect: str) -> str:
    if not value:
        return "missing"
    path = Path(value).expanduser()
    if expect == "file":
        return "ok" if path.is_file() else "not found as file"
    if expect == "dir":
        return "ok" if path.is_dir() else "not found as directory"
    if expect == "parent":
        parent = path.parent if path.suffix else path
        return "ok" if parent.exists() else "parent not found"
    return "unknown expectation"


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def print_checks(checks: Iterable[tuple[str, str, str]]) -> None:
    print_header("Checks")
    for label, value, status in checks:
        print(f"- {label}: {value or '<missing>'} [{status}]")


def warn(message: str) -> None:
    print(f"WARNING: {message}")


def info(message: str) -> None:
    print(f"INFO: {message}")


def visible_gpu_count() -> int | None:
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cuda_visible is None or cuda_visible.strip() == "":
        return None
    if cuda_visible.strip() == "-1":
        return 0
    return len([item for item in cuda_visible.split(",") if item.strip()])


def check_process_count(nproc_per_node: int) -> None:
    if nproc_per_node < 1:
        warn("nproc-per-node must be positive before launch.")
    visible = visible_gpu_count()
    if visible is not None and nproc_per_node > visible:
        warn(f"nproc-per-node={nproc_per_node} exceeds CUDA_VISIBLE_DEVICES count {visible}.")
    if visible == 0:
        warn("CUDA_VISIBLE_DEVICES disables GPUs; GPU-only native commands should not be launched.")


def check_json_like(path: str | None) -> None:
    if not path or not Path(path).is_file():
        return
    suffix = Path(path).suffix.lower()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            if suffix == ".jsonl":
                first = handle.readline()
                if first.strip():
                    json.loads(first)
                    info("First JSONL record parses successfully.")
                else:
                    warn("JSONL file is empty.")
            elif suffix == ".json":
                json.load(handle)
                info("JSON file parses successfully.")
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic helper
        warn(f"Could not parse {path} as {suffix or 'JSON-like'}: {exc}")


def cmd_yoco_needle(args: argparse.Namespace) -> None:
    print_header("YOCO Needle Dry Run")
    checks = [
        ("checkpoint", args.checkpoint, path_status(args.checkpoint, "file")),
        ("model-dir", args.model_dir, path_status(args.model_dir, "dir")),
    ]
    print_checks(checks)
    check_process_count(args.nproc_per_node)
    if args.tokens_per_sample <= 0 or args.interval <= 0:
        warn("tokens-per-sample and interval must be positive.")
    if args.tokens_per_sample != args.interval:
        warn("YOCO needle examples normally set interval equal to tokens-per-sample.")
    if args.tokens_per_sample >= 1_000_000:
        warn("1M-token evaluation is benchmark-scale; confirm GPU memory, kernels, and wall time.")
    if args.batch_size != 1:
        warn("Source needle examples use batch-size 1; larger batches are high OOM risk.")
    criterion = "multi_needle" if args.needle_num and args.needle_num > 1 else "needle_haystack"
    needle_part = f" --needle-num {args.needle_num}" if criterion == "multi_needle" else ""
    print_header("Safe Template")
    print(
        "torchrun --master-port PORT --nproc_per_node "
        f"{args.nproc_per_node} validate.py \\\n"
        "  --task pseudo \\\n"
        f"  --criterion {criterion}{needle_part} \\\n"
        f"  --batch-size {args.batch_size} --max-epoch 1 --no-save \\\n"
        "  --tiktoken-model cl100k_base --bf16 \\\n"
        "  --arch yoco_3b_new \\\n"
        "  --load-ckpt CHECKPOINT_PTH --yoco-model YOCO_MODEL_DIR \\\n"
        f"  --tokens-per-sample {args.tokens_per_sample} --interval {args.interval}"
    )


def cmd_yoco_task(args: argparse.Namespace) -> None:
    print_header("YOCO Harness Task Dry Run")
    checks = [
        ("checkpoint", args.checkpoint, path_status(args.checkpoint, "file")),
        ("model-dir", args.model_dir, path_status(args.model_dir, "dir")),
        ("data-dir", args.data_dir, path_status(args.data_dir, "dir")),
    ]
    print_checks(checks)
    check_process_count(args.nproc_per_node)
    if not args.eval_data:
        warn("eval-data task name is required for harness_eval.")
    if args.tokens_per_sample > 8192:
        warn("Harness tasks usually do not need extreme context lengths; confirm memory.")
    print_header("Safe Template")
    print(
        "torchrun --master-port PORT --nproc_per_node "
        f"{args.nproc_per_node} validate.py \\\n"
        "  --data-dir HARNESS_DATA_DIR --criterion harness_eval --task harness_eval \\\n"
        f"  --batch-size {args.batch_size} --eval-data {args.eval_data or 'TASK'} \\\n"
        "  --log-format simple --log-interval 10 --bf16 --tokenizer-pad-to-multiple 8 \\\n"
        "  --arch yoco_3b_new --tiktoken-model cl100k_base \\\n"
        "  --load-ckpt CHECKPOINT_PTH --yoco-model YOCO_MODEL_DIR \\\n"
        f"  --tokens-per-sample {args.tokens_per_sample}"
    )


def cmd_diff_transformer(args: argparse.Namespace) -> None:
    print_header("Diff-Transformer Module Dry Run")
    if args.embed_dim <= 0 or args.num_heads <= 0:
        warn("embed-dim and num-heads must be positive.")
    if args.embed_dim % args.num_heads != 0:
        warn("embed-dim should divide evenly by num-heads for standard attention layouts.")
    if args.depth < 0:
        warn("depth should be non-negative because lambda initialization is layer-depth dependent.")
    if args.sequence_length <= 0:
        warn("sequence-length must be positive.")
    if args.use_flash:
        warn("Flash/diff kernels require runtime-specific flash-attention or custom kernel compatibility.")
    print_header("Inspection Template")
    print("from multihead_diffattn import MultiheadDiffAttn")
    print(f"module = MultiheadDiffAttn(embed_dim={args.embed_dim}, depth={args.depth}, num_heads={args.num_heads})")
    print(f"# Feed a tensor shaped [batch, {args.sequence_length}, {args.embed_dim}] in the prepared project runtime.")


def cmd_gad_decoding(args: argparse.Namespace) -> None:
    print_header("GAD Decoding Dry Run")
    checks = [
        ("data-dir", args.data_dir, path_status(args.data_dir, "dir")),
        ("checkpoint", args.checkpoint, path_status(args.checkpoint, "file")),
        ("ar-checkpoint", args.ar_checkpoint, path_status(args.ar_checkpoint, "file")),
        ("input-file", args.input_file, path_status(args.input_file, "file")),
        ("output-file", args.output_file, path_status(args.output_file, "parent")),
    ]
    print_checks(checks)
    if args.block_size < 1:
        warn("block-size must be positive.")
    if args.beta < 1:
        warn("beta must be at least 1 for top-k verifier candidates.")
    if args.tau < 0:
        warn("tau should be non-negative.")
    if args.batch_size < 1:
        warn("batch-size must be positive.")
    print_header("Safe Template")
    print(
        "python inference.py DATA_DIR --path NAT_DRAFTER_CKPT \\\n"
        "  --user-dir block_plugins --task translation_lev_modified --remove-bpe \\\n"
        f"  --max-sentences {args.batch_size} --source-lang {args.source_lang} --target-lang {args.target_lang} \\\n"
        "  --iter-decode-max-iter 0 --iter-decode-eos-penalty 0 --iter-decode-with-beam 1 \\\n"
        "  --gen-subset test --AR-path AR_VERIFIER_CKPT \\\n"
        "  --input-path INPUT_TXT --output-path OUTPUT_TXT \\\n"
        f"  --block-size {args.block_size} --beta {args.beta} --tau {args.tau} --batch {args.batch_size} --beam {args.beam} --strategy gad"
    )


def cmd_pfpo_offline_eval(args: argparse.Namespace) -> None:
    print_header("PFPO Offline Eval Dry Run")
    checks = [
        ("input-file", args.input_file, path_status(args.input_file, "file")),
        ("output-file", args.output_file, path_status(args.output_file, "parent")),
    ]
    print_checks(checks)
    check_json_like(args.input_file)
    check_process_count(args.nproc_per_node)
    if args.call_credentials:
        warn("Credentialed PFPO OpenAI/service callers are not launched by this helper; confirm credentials, endpoint, and cost separately.")
    if args.deepspeed_config and "zero3" in args.deepspeed_config.lower():
        warn("ZeRO-3 checkpoints are sharded; plan save/load and conversion explicitly.")
    if args.task not in {"math", "coding", "mbpp", "apps", "generic"}:
        warn("Unknown task label; verify expected JSON keys before evaluation.")
    print_header("Offline Alternatives")
    print("- Parse JSON/JSONL inputs and inspect representative keys.")
    print("- Construct preference pairs from existing predictions instead of calling external services.")
    print("- Run MBPP-style test-case checks only in a sandboxed local environment.")
    print_header("Safe Template")
    print(
        "python scripts/math_scale/construct_prefer_pair.py \\\n"
        "  --input_file INPUT_GLOB --output_file PREFERENCE_PAIRS_JSON"
    )


def cmd_resa_math_eval(args: argparse.Namespace) -> None:
    print_header("ReSA Math Eval Dry Run")
    checks = [
        ("checkpoint", args.checkpoint, path_status(args.checkpoint, "dir")),
        ("output-dir", args.output_dir, path_status(args.output_dir, "parent")),
    ]
    print_checks(checks)
    check_process_count(args.nproc_per_node)
    if args.resa_sparse_ratio <= 0 or args.resa_sparse_ratio > 1:
        warn("resa-sparse-ratio should be in (0, 1].")
    if args.resa_rec_freq < 0:
        warn("resa-rec-freq must be non-negative.")
    if args.limit > 512:
        warn("Large math limits can be benchmark-scale; use a smaller smoke test first.")
    if args.batch_size > 4:
        warn("Source local eval uses batch_size 4; larger batches increase OOM risk.")
    print_header("Safe Template")
    print(
        "TORCH_IND_SYM_NODE_NO_SYMPY=1 torchrun "
        f"--nproc_per_node={args.nproc_per_node} --nnodes=1 --master_port=PORT eval.py \\\n"
        f"  --limit {args.limit} --batch_size {args.batch_size} \\\n"
        "  --checkpoint_dir CHECKPOINT_DIR --downstream_task math \\\n"
        f"  --save_feature resa_{args.resa_sparse_ratio}_{args.resa_rec_freq} \\\n"
        "  --output_folder OUTPUT_DIR \\\n"
        f"  --resa_rec_freq {args.resa_rec_freq} --resa_sparse_ratio {args.resa_sparse_ratio}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run UniLM architecture/training plan validator. Does not launch native jobs."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    yoco_needle = subparsers.add_parser("yoco-needle", help="Validate YOCO needle or multi-needle evaluation plan.")
    yoco_needle.add_argument("--checkpoint", required=True)
    yoco_needle.add_argument("--model-dir", required=True)
    yoco_needle.add_argument("--tokens-per-sample", type=int, required=True)
    yoco_needle.add_argument("--interval", type=int, required=True)
    yoco_needle.add_argument("--nproc-per-node", type=int, default=1)
    yoco_needle.add_argument("--batch-size", type=int, default=1)
    yoco_needle.add_argument("--needle-num", type=int, default=1)
    yoco_needle.set_defaults(func=cmd_yoco_needle)

    yoco_task = subparsers.add_parser("yoco-task", help="Validate YOCO harness task evaluation plan.")
    yoco_task.add_argument("--checkpoint", required=True)
    yoco_task.add_argument("--model-dir", required=True)
    yoco_task.add_argument("--data-dir", required=True)
    yoco_task.add_argument("--eval-data", required=True)
    yoco_task.add_argument("--tokens-per-sample", type=int, default=4096)
    yoco_task.add_argument("--nproc-per-node", type=int, default=1)
    yoco_task.add_argument("--batch-size", type=int, default=4)
    yoco_task.set_defaults(func=cmd_yoco_task)

    diff = subparsers.add_parser("diff-transformer", help="Validate a Diff-Transformer attention module inspection plan.")
    diff.add_argument("--embed-dim", type=int, required=True)
    diff.add_argument("--num-heads", type=int, required=True)
    diff.add_argument("--depth", type=int, default=0)
    diff.add_argument("--sequence-length", type=int, default=16)
    diff.add_argument("--use-flash", action="store_true")
    diff.set_defaults(func=cmd_diff_transformer)

    gad = subparsers.add_parser("gad-decoding", help="Validate GAD decoding acceleration plan.")
    gad.add_argument("--data-dir", required=True)
    gad.add_argument("--checkpoint", required=True)
    gad.add_argument("--ar-checkpoint", required=True)
    gad.add_argument("--input-file", required=True)
    gad.add_argument("--output-file", required=True)
    gad.add_argument("--source-lang", default="en")
    gad.add_argument("--target-lang", default="de")
    gad.add_argument("--block-size", type=int, default=4)
    gad.add_argument("--beta", type=int, default=1)
    gad.add_argument("--tau", type=float, default=0.0)
    gad.add_argument("--batch-size", type=int, default=20)
    gad.add_argument("--beam", type=int, default=1)
    gad.set_defaults(func=cmd_gad_decoding)

    pfpo = subparsers.add_parser("pfpo-offline-eval", help="Validate PFPO offline evaluation or preference-data plan.")
    pfpo.add_argument("--input-file", required=True)
    pfpo.add_argument("--output-file", required=True)
    pfpo.add_argument("--task", default="generic")
    pfpo.add_argument("--deepspeed-config", default="")
    pfpo.add_argument("--nproc-per-node", type=int, default=1)
    pfpo.add_argument("--call-credentials", action="store_true")
    pfpo.set_defaults(func=cmd_pfpo_offline_eval)

    resa = subparsers.add_parser("resa-math-eval", help="Validate ReSA local math evaluation plan.")
    resa.add_argument("--checkpoint", required=True)
    resa.add_argument("--output-dir", required=True)
    resa.add_argument("--limit", type=int, default=512)
    resa.add_argument("--batch-size", type=int, default=4)
    resa.add_argument("--resa-rec-freq", type=int, default=32)
    resa.add_argument("--resa-sparse-ratio", type=float, default=0.1)
    resa.add_argument("--nproc-per-node", type=int, default=1)
    resa.set_defaults(func=cmd_resa_math_eval)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    print("\nDry run only: no training, evaluation, download, or service call was launched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
