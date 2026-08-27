#!/usr/bin/env python3
"""Create a tiny H2O LLM Studio training YAML and CSV fixture.

Safe by default: writes only under --output-dir and never launches training.
The generated config is intended for command construction and smoke planning;
actual execution depends on the installed package, model cache, and host backend.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - user-facing diagnostic
    raise SystemExit("PyYAML is required to write the config: pip install pyyaml") from exc


def build_config(args: argparse.Namespace, train_csv: Path, experiment_dir: Path) -> dict[str, Any]:
    gpus = [] if args.gpus == "none" else [item for item in args.gpus.split(",")]
    return {
        "architecture": {
            "backbone_dtype": args.backbone_dtype,
            "gradient_checkpointing": False,
            "intermediate_dropout": 0.0,
            "pretrained": True,
            "pretrained_weights": "",
        },
        "augmentation": {
            "random_parent_probability": 0.0,
            "skip_parent_probability": 0.0,
            "token_mask_probability": 0.0,
        },
        "dataset": {
            "add_eos_token_to_answer": True,
            "add_eos_token_to_prompt": True,
            "add_eos_token_to_system": True,
            "answer_column": "output",
            "chatbot_author": "H2O.ai",
            "chatbot_name": "h2oGPT",
            "data_sample": 1.0,
            "data_sample_choice": ["Train", "Validation"],
            "limit_chained_samples": False,
            "mask_prompt_labels": True,
            "only_last_answer": False,
            "parent_id_column": "None",
            "personalize": False,
            "prompt_column": ["instruction"],
            "system_column": "None",
            "text_answer_separator": "<|answer|>",
            "text_prompt_start": "<|prompt|>",
            "text_system_start": "<|system|>",
            "train_dataframe": str(train_csv),
            "validation_dataframe": "None",
            "validation_size": args.validation_size,
            "validation_strategy": "automatic",
        },
        "environment": {
            "compile_model": False,
            "find_unused_parameters": False,
            "gpus": gpus,
            "huggingface_branch": "main",
            "mixed_precision": False,
            "number_of_workers": args.workers,
            "seed": args.seed,
            "trust_remote_code": True,
            "use_deepspeed": False,
        },
        "experiment_name": args.experiment_name,
        "llm_backbone": args.backbone,
        "logging": {"logger": "None"},
        "output_directory": str(experiment_dir),
        "prediction": {
            "batch_size_inference": 0,
            "do_sample": False,
            "max_length_inference": 16,
            "max_time": 0.0,
            "metric": args.metric,
            "metric_gpt_model": "gpt-3.5-turbo-0301",
            "metric_gpt_template": "general",
            "min_length_inference": 1,
            "num_beams": 1,
            "num_history": 4,
            "repetition_penalty": 1.2,
            "stop_tokens": "",
            "temperature": 0.0,
            "top_k": 0,
            "top_p": 1.0,
        },
        "problem_type": "text_causal_language_modeling",
        "tokenizer": {
            "add_prompt_answer_tokens": False,
            "max_length": args.max_length,
            "padding_quantile": 1.0,
            "tokenizer_kwargs": json.dumps({"use_fast": True, "add_prefix_space": False}),
        },
        "training": {
            "batch_size": args.batch_size,
            "differential_learning_rate": 1.0e-5,
            "differential_learning_rate_layers": [],
            "drop_last_batch": False,
            "epochs": args.epochs,
            "evaluate_before_training": args.evaluate_before_training,
            "evaluation_epochs": 1.0,
            "grad_accumulation": 1,
            "gradient_clip": 0.0,
            "learning_rate": args.learning_rate,
            "lora": True,
            "use_dora": False,
            "lora_alpha": 16,
            "lora_dropout": 0.05,
            "lora_r": 4,
            "lora_target_modules": "",
            "loss_function": "TokenAveragedCrossEntropy",
            "optimizer": "AdamW",
            "save_checkpoint": args.save_checkpoint,
            "schedule": "Cosine",
            "train_validation_data": False,
            "warmup_epochs": 0.0,
            "weight_decay": 0.0,
        },
    }


def write_csv(path: Path) -> None:
    rows = [
        {"instruction": "Say hello in one short sentence.", "output": "Hello!"},
        {"instruction": "Name one color of the sky.", "output": "Blue."},
        {"instruction": "Answer with the word yes.", "output": "yes"},
        {"instruction": "What is 1 plus 1?", "output": "2"},
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        # H2O LLM Studio reads CSV with lineterminator="\n"; force Unix line endings
        # so the last header is not parsed as "output\r" on platforms that default to CRLF.
        writer = csv.DictWriter(handle, fieldnames=["instruction", "output"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="llmstudio-minimal-smoke", help="Directory to create or reuse.")
    parser.add_argument("--config-name", default="minimal_causal_lm.yaml", help="YAML filename inside --output-dir.")
    parser.add_argument("--csv-name", default="tiny_train.csv", help="CSV filename inside --output-dir.")
    parser.add_argument("--experiment-name", default="minimal-causal-lm-smoke", help="Experiment name stored in YAML.")
    parser.add_argument("--backbone", default="h2oai/llama2-0b-unit-test", help="Backbone name/path for the YAML.")
    parser.add_argument("--backbone-dtype", default="float32", choices=["float32", "float16", "bfloat16", "int8", "int4"], help="Backbone dtype.")
    parser.add_argument("--gpus", default="", help="Comma list for environment.gpus. Default matches tiny CPU-like configs with one empty entry; use 'none' for [].")
    parser.add_argument("--epochs", type=int, default=0, help="Training epochs. 0 performs evaluation-style smoke if execution succeeds.")
    parser.add_argument("--batch-size", type=int, default=1, help="Per-GPU batch size.")
    parser.add_argument("--max-length", type=int, default=32, help="Tokenizer max length.")
    parser.add_argument("--learning-rate", type=float, default=1.0e-4, help="Training learning rate.")
    parser.add_argument("--validation-size", type=float, default=0.5, help="Automatic validation split fraction.")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader worker count.")
    parser.add_argument("--seed", type=int, default=1, help="Environment seed.")
    parser.add_argument("--metric", default="BLEU", help="Prediction metric.")
    parser.add_argument("--save-checkpoint", default="disable", choices=["last", "best", "each_evaluation_epoch", "disable"], help="Checkpoint mode.")
    parser.add_argument("--evaluate-before-training", action="store_true", help="Set training.evaluate_before_training true.")
    parser.add_argument("--print-command", action="store_true", help="Print a training command after writing files.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing YAML/CSV. By default existing files are preserved.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    train_csv = out_dir / args.csv_name
    cfg_path = out_dir / args.config_name
    experiment_dir = out_dir / "output"

    for path in (train_csv, cfg_path):
        if path.exists() and not args.overwrite:
            raise SystemExit(f"Refusing to overwrite existing file without --overwrite: {path}")

    write_csv(train_csv)
    cfg = build_config(args, train_csv=train_csv, experiment_dir=experiment_dir)
    with cfg_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(cfg, handle, sort_keys=False)

    print(f"wrote CSV: {train_csv}")
    print(f"wrote YAML: {cfg_path}")
    print("safe: no training command was executed")
    if args.print_command:
        print(f"command: python llm_studio/train.py -Y {cfg_path}")
        print("optional dry-run wrapper: sub-skills/training-and-experiments/scripts/distributed_train_wrapper.sh --num-gpus 1 --yaml " + str(cfg_path))
    if args.gpus in ("", "none"):
        print("note: this is a CPU-like construction smoke. Verify current package GPU validation before treating it as an end-to-end CPU training proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
