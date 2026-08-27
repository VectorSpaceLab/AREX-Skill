#!/usr/bin/env python3
"""Build a three-stage GPT-2 LoRA command plan for the repository examples.

This helper prints a safe, copyable set of commands for a chosen dataset.
It does not download data, launch training, or evaluate metrics.
"""

from __future__ import annotations

import argparse
import json
import shlex


DATASETS = {
    "e2e": {
        "path": "./data/e2e",
        "model_card": "gpt2.md",
        "seq_len": 512,
        "train_batch_size": 8,
        "valid_batch_size": 4,
        "lora_dim": 4,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "train_file": "train.jsonl",
        "valid_file": "valid.jsonl",
        "test_file": "test.jsonl",
        "ref_type": "e2e",
        "ref_num": 4,
    },
    "webnlg": {
        "path": "./data/webnlg_challenge_2017",
        "model_card": "gpt2.md",
        "seq_len": 512,
        "train_batch_size": 8,
        "valid_batch_size": 4,
        "lora_dim": 4,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "train_file": "train.jsonl",
        "valid_file": "valid.jsonl",
        "test_file": "test.jsonl",
        "ref_type": "webnlg",
        "ref_num": 6,
    },
    "dart": {
        "path": "./data/dart",
        "model_card": "gpt2.md",
        "seq_len": 512,
        "train_batch_size": 8,
        "valid_batch_size": 4,
        "lora_dim": 4,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "train_file": "train.jsonl",
        "valid_file": "valid.jsonl",
        "test_file": "test.jsonl",
        "ref_type": "dart",
        "ref_num": 6,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--work-dir", default="./gpt2-lora-work")
    parser.add_argument("--beam", type=int, default=10)
    parser.add_argument("--length-penalty", type=float, default=0.8)
    parser.add_argument("--no-repeat-ngram-size", type=int, default=4)
    parser.add_argument("--repetition-penalty", type=float, default=1.0)
    parser.add_argument("--eval-len", type=int, default=64)
    parser.add_argument("--init-checkpoint", default="./pretrained_checkpoints/gpt2-medium-pytorch_model.bin")
    parser.add_argument("--vocab", default="./vocab")
    parser.add_argument("--output-file", default="predict.jsonl")
    parser.add_argument("--train-script", default="gpt2_ft.py", help="Path/name of a compatible training script.")
    parser.add_argument("--beam-script", default="gpt2_beam.py", help="Path/name of a compatible beam-search script.")
    parser.add_argument("--decode-script", default="gpt2_decode.py", help="Path/name of a compatible decode script.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON object instead of formatted commands.")
    return parser.parse_args()


def as_cmd(parts: list[str]) -> str:
    return " \\\n    ".join(shlex.quote(part) for part in parts)


def main() -> int:
    args = parse_args()
    cfg = DATASETS[args.dataset]
    data_dir = cfg["path"]
    train_cmd = [
        "python", "-m", "torch.distributed.launch", "--nproc_per_node=1", args.train_script,
        "--train_data", f"{data_dir}/{cfg['train_file']}",
        "--valid_data", f"{data_dir}/{cfg['valid_file']}",
        "--train_batch_size", str(cfg["train_batch_size"]),
        "--grad_acc", "1",
        "--valid_batch_size", str(cfg["valid_batch_size"]),
        "--seq_len", str(cfg["seq_len"]),
        "--model_card", cfg["model_card"],
        "--init_checkpoint", args.init_checkpoint,
        "--platform", "local",
        "--clip", "0.0",
        "--lr", "0.0002",
        "--weight_decay", "0.01",
        "--correct_bias",
        "--adam_beta2", "0.999",
        "--scheduler", "linear",
        "--warmup_step", "500",
        "--max_epoch", "5",
        "--save_interval", "1000",
        "--lora_dim", str(cfg["lora_dim"]),
        "--lora_alpha", str(cfg["lora_alpha"]),
        "--lora_dropout", str(cfg["lora_dropout"]),
        "--label_smooth", "0.1",
        "--work_dir", f"{args.work_dir}/{args.dataset}",
        "--random_seed", "110",
    ]
    beam_cmd = [
        "python", "-m", "torch.distributed.launch", "--nproc_per_node=1", args.beam_script,
        "--data", f"{data_dir}/{cfg['test_file']}",
        "--batch_size", "1",
        "--seq_len", str(cfg["seq_len"]),
        "--eval_len", str(args.eval_len),
        "--model_card", cfg["model_card"],
        "--init_checkpoint", f"{args.work_dir}/{args.dataset}/model.26289.pt",
        "--platform", "local",
        "--lora_dim", str(cfg["lora_dim"]),
        "--lora_alpha", str(cfg["lora_alpha"]),
        "--beam", str(args.beam),
        "--length_penalty", str(args.length_penalty),
        "--no_repeat_ngram_size", str(args.no_repeat_ngram_size),
        "--repetition_penalty", str(args.repetition_penalty),
        "--eos_token_id", "628",
        "--work_dir", f"{args.work_dir}/{args.dataset}",
        "--output_file", args.output_file,
    ]
    decode_cmd = [
        "python", args.decode_script,
        "--vocab", args.vocab,
        "--sample_file", f"{args.work_dir}/{args.dataset}/{args.output_file}",
        "--input_file", f"{data_dir}/{cfg['test_file'].replace('.jsonl', '_formatted.jsonl')}",
        "--output_ref_file", f"{args.work_dir}/{args.dataset}/{args.dataset}_ref.txt" if cfg["ref_type"] == "e2e" else f"{args.work_dir}/{args.dataset}/references_{args.dataset}",
        "--output_pred_file", f"{args.work_dir}/{args.dataset}/{args.dataset}_pred.txt",
        "--ref_type", cfg["ref_type"],
        "--ref_num", str(cfg["ref_num"]),
    ]
    result = {
        "dataset": args.dataset,
        "train": as_cmd(train_cmd),
        "beam": as_cmd(beam_cmd),
        "decode": as_cmd(decode_cmd),
        "notes": [
            "The training and beam commands assume a local distributed launcher compatible with your PyTorch version.",
            "The decode command assumes the matching formatted input file already exists.",
        ],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("TRAIN:\n" + result["train"])
        print("\nBEAM:\n" + result["beam"])
        print("\nDECODE:\n" + result["decode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
