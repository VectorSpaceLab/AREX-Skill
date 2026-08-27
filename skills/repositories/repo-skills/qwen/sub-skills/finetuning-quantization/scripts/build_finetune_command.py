#!/usr/bin/env python3
"""Build a dry-run Qwen fine-tuning or Q-LoRA command without training."""
from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="Build a Qwen fine-tuning command plan.")
    p.add_argument("--mode", choices=["full", "lora", "qlora"], required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--output", default="output_qwen")
    p.add_argument("--deepspeed")
    p.add_argument("--distributed", action="store_true")
    p.add_argument("--max-length", type=int, default=512)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    common = [
        "python finetune.py",
        f"--model_name_or_path {args.model}",
        f"--data_path {args.data}",
        f"--output_dir {args.output}",
        "--num_train_epochs 5",
        "--per_device_train_batch_size 2",
        "--per_device_eval_batch_size 1",
        "--gradient_accumulation_steps 8",
        "--evaluation_strategy \"no\"",
        "--save_strategy \"steps\"",
        "--save_steps 1000",
        "--save_total_limit 10",
        "--learning_rate 3e-4",
        "--weight_decay 0.1",
        "--adam_beta2 0.95",
        "--warmup_ratio 0.01",
        "--lr_scheduler_type \"cosine\"",
        "--logging_steps 1",
        "--report_to \"none\"",
        f"--model_max_length {args.max_length}",
        "--lazy_preprocess True",
        "--gradient_checkpointing",
    ]
    if args.mode == "full":
        extras = ["--bf16 True"]
        if args.distributed:
            extras.insert(0, "torchrun --nproc_per_node 1 --nnodes 1 --node_rank 0 --master_addr localhost --master_port 12345")
        if args.deepspeed:
            extras.append(f"--deepspeed {args.deepspeed}")
    elif args.mode == "lora":
        extras = ["--bf16 True", "--use_lora"]
        if args.deepspeed:
            extras.append(f"--deepspeed {args.deepspeed}")
    else:
        extras = ["--fp16 True", "--use_lora", "--q_lora", "--deepspeed finetune/ds_config_zero2.json"]
        if args.deepspeed:
            extras[-1] = f"--deepspeed {args.deepspeed}"
    command = " ".join(common + extras)
    if args.json:
        import json
        print(json.dumps({"mode": args.mode, "command": command}, indent=2))
    else:
        print("DRY RUN (not executed):")
        print(command)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
