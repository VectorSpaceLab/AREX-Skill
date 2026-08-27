#!/usr/bin/env python3
"""Build a LoRA-aware GLUE command without assuming a repository checkout.

This is a command builder, not a trainer. It prints a command for an existing
LoRA-aware `run_glue.py`-compatible script and never downloads data or starts a
process.
"""

from __future__ import annotations

import argparse
import shlex


DEFAULTS = {
    "roberta-base": {"model_id": "roberta-base", "seq": 512, "batch": 16, "lr": "5e-4", "epochs": "30", "r": 8, "alpha": 16},
    "roberta-large": {"model_id": "roberta-large", "seq": 512, "batch": 16, "lr": "5e-4", "epochs": "30", "r": 8, "alpha": 16},
    "deberta-v2-xxlarge": {"model_id": "microsoft/deberta-v2-xxlarge", "seq": 256, "batch": 8, "lr": "1e-4", "epochs": "5", "r": 16, "alpha": 32},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(DEFAULTS), default="roberta-base")
    parser.add_argument("--task", default="mnli", help="GLUE task or a task understood by the runner.")
    parser.add_argument("--script", default="run_glue.py", help="Path/name of a compatible runner.")
    parser.add_argument("--output-dir", default="./lora-glue-output")
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--seq-length", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--learning-rate")
    parser.add_argument("--epochs")
    parser.add_argument("--lora-r", type=int)
    parser.add_argument("--lora-alpha", type=int)
    parser.add_argument("--lora-path")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--overwrite-output-dir", action="store_true")
    parser.add_argument("--use-deterministic-algorithms", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.num_gpus < 1:
        raise SystemExit("--num-gpus must be at least 1")
    defaults = DEFAULTS[args.model]
    seq = args.seq_length or defaults["seq"]
    batch = args.batch_size or defaults["batch"]
    lr = args.learning_rate or defaults["lr"]
    epochs = args.epochs or defaults["epochs"]
    rank = args.lora_r or defaults["r"]
    alpha = args.lora_alpha or defaults["alpha"]
    if rank < 1 or alpha < 1:
        raise SystemExit("--lora-r and --lora-alpha must be positive")

    runner = ["python"]
    if args.num_gpus > 1:
        runner += ["-m", "torch.distributed.launch", "--nproc_per_node", str(args.num_gpus)]
    runner.append(args.script)
    runner += [
        "--model_name_or_path", defaults["model_id"],
        "--task_name", args.task,
        "--max_seq_length", str(seq),
        "--per_device_train_batch_size", str(batch),
        "--learning_rate", str(lr),
        "--num_train_epochs", str(epochs),
        "--output_dir", args.output_dir,
        "--apply_lora",
        "--lora_r", str(rank),
        "--lora_alpha", str(alpha),
    ]
    if not args.eval_only:
        runner += ["--do_train"]
    runner += ["--do_eval"]
    if args.lora_path:
        runner += ["--lora_path", args.lora_path]
    if args.fp16:
        runner.append("--fp16")
    if args.overwrite_output_dir:
        runner.append("--overwrite_output_dir")
    if args.use_deterministic_algorithms:
        runner.append("--use_deterministic_algorithms")

    print(" \\\n    ".join(shlex.quote(part) for part in runner))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
