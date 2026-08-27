#!/usr/bin/env python3
"""Plan a MOSS SFT fine-tuning launch without running training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

DEFAULT_ACCELERATE_YAML = """command_file: null
commands: null
compute_environment: LOCAL_MACHINE
deepspeed_config:
  gradient_accumulation_steps: 1
  gradient_clipping: 1.0
  offload_optimizer_device: none
  offload_param_device: none
  zero3_init_flag: true
  zero3_save_16bit_model: true
  zero_stage: 3
distributed_type: DEEPSPEED
downcast_bf16: 'no'
dynamo_backend: 'NO'
fsdp_config: {{}}
gpu_ids: null
machine_rank: 0
main_process_ip: null
main_process_port: null
main_training_function: main
megatron_lm_config: {{}}
mixed_precision: fp16
num_machines: 1
num_processes: {num_processes}
rdzv_backend: static
same_network: true
tpu_name: null
tpu_zone: null
use_cpu: false
"""


def path_status(path: str, expect_dir: bool = False) -> Dict[str, object]:
    p = Path(path).expanduser()
    return {"path": str(p), "exists": p.exists(), "is_dir": p.is_dir(), "ok": p.exists() and (p.is_dir() if expect_dir else True)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a MOSS SFT training launch and optionally write an Accelerate config.")
    parser.add_argument("--model-name-or-path", required=True, help="Base MOSS checkpoint id or local checkpoint directory.")
    parser.add_argument("--data-dir", required=True, help="Directory expected to contain train.jsonl and val.jsonl or cached tensors.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--num-processes", type=int, default=8)
    parser.add_argument("--train-bsz-per-gpu", type=int, default=4)
    parser.add_argument("--eval-bsz-per-gpu", type=int, default=4)
    parser.add_argument("--learning-rate", default="9e-6")
    parser.add_argument("--n-epochs", type=int, default=2)
    parser.add_argument("--write-config", help="Optional path where the generated Accelerate/DeepSpeed YAML should be written.")
    parser.add_argument("--training-script", default="train_moss_sft_template.py", help="Training script to place in the command; use this skill's bundled template or a reviewed project copy.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    checks = {
        "data_dir": path_status(args.data_dir, expect_dir=True),
        "train_jsonl": path_status(str(data_dir / "train.jsonl")),
        "val_jsonl": path_status(str(data_dir / "val.jsonl")),
    }
    config_path = args.write_config
    if config_path:
        target = Path(config_path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(DEFAULT_ACCELERATE_YAML.format(num_processes=args.num_processes), encoding="utf-8")
    else:
        config_path = "moss_sft_accelerate.yaml"
    command = (
        f"accelerate launch --config_file {config_path} {args.training_script} "
        f"--model_name_or_path {args.model_name_or_path} --data_dir {args.data_dir} "
        f"--output_dir {args.output_dir} --log_dir {args.log_dir} "
        f"--train_bsz_per_gpu {args.train_bsz_per_gpu} --eval_bsz_per_gpu {args.eval_bsz_per_gpu} "
        f"--learning_rate {args.learning_rate} --n_epochs {args.n_epochs}"
    )
    report = {
        "ok_to_plan": True,
        "checks": checks,
        "config_written": bool(args.write_config),
        "config_path": config_path,
        "command": command,
        "warnings": [
            "This is a training plan only; full MOSS SFT is a multi-GPU, checkpoint-dependent workload.",
            "Validate train.jsonl and val.jsonl with validate_sft_json.py before launching.",
            "Ensure DeepSpeed is installed and num_processes matches available GPUs.",
        ],
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
