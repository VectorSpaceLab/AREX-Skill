#!/usr/bin/env python3
"""Print safe UniLM/s2s-ft seq2seq command templates without executing them."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable

MODEL_TYPES = ("bert", "minilm", "roberta", "xlm-roberta", "unilm", "electra")
TASKS = ("xsum", "cnndm", "gigaword", "custom-json")
MODES = ("train", "decode", "eval", "all")


@dataclass(frozen=True)
class TaskPreset:
    split: str
    max_source_seq_length: int
    max_target_seq_length: int
    max_seq_length: int
    max_tgt_length: int
    per_gpu_train_batch_size: int
    gradient_accumulation_steps: int
    learning_rate: str
    num_warmup_steps: int
    num_training_steps: int
    save_steps: int
    batch_size: int
    beam_size: int
    length_penalty: str
    min_len: int | None
    forbid_ignore_word: str | None
    eval_script: str | None
    eval_trunc_len: int | None
    notes: tuple[str, ...]


PRESETS: dict[str, TaskPreset] = {
    "xsum": TaskPreset(
        split="validation",
        max_source_seq_length=464,
        max_target_seq_length=48,
        max_seq_length=512,
        max_tgt_length=48,
        per_gpu_train_batch_size=16,
        gradient_accumulation_steps=1,
        learning_rate="7e-5",
        num_warmup_steps=500,
        num_training_steps=32000,
        save_steps=1500,
        batch_size=32,
        beam_size=5,
        length_penalty="0",
        min_len=None,
        forbid_ignore_word=".",
        eval_script="evaluations/eval_for_xsum.py",
        eval_trunc_len=None,
        notes=(
            "XSum examples use short targets; UniLM2 variants may use longer source length and nonzero length penalty.",
        ),
    ),
    "cnndm": TaskPreset(
        split="dev",
        max_source_seq_length=608,
        max_target_seq_length=160,
        max_seq_length=768,
        max_tgt_length=160,
        per_gpu_train_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate="7e-5",
        num_warmup_steps=1000,
        num_training_steps=45000,
        save_steps=1500,
        batch_size=32,
        beam_size=5,
        length_penalty="0",
        min_len=None,
        forbid_ignore_word=".",
        eval_script="evaluations/eval_for_cnndm.py",
        eval_trunc_len=160,
        notes=(
            "CNN/DailyMail commands usually reserve a long target budget and evaluate with truncation.",
        ),
    ),
    "gigaword": TaskPreset(
        split="test",
        max_source_seq_length=128,
        max_target_seq_length=32,
        max_seq_length=192,
        max_tgt_length=32,
        per_gpu_train_batch_size=32,
        gradient_accumulation_steps=1,
        learning_rate="5e-5",
        num_warmup_steps=500,
        num_training_steps=30000,
        save_steps=1500,
        batch_size=64,
        beam_size=5,
        length_penalty="0",
        min_len=None,
        forbid_ignore_word=".",
        eval_script="evaluations/eval_for_gigaword.py",
        eval_trunc_len=None,
        notes=(
            "Gigaword in the legacy UniLM examples is short headline generation; adjust lengths from data histograms.",
        ),
    ),
    "custom-json": TaskPreset(
        split="test",
        max_source_seq_length=0,
        max_target_seq_length=0,
        max_seq_length=0,
        max_tgt_length=0,
        per_gpu_train_batch_size=8,
        gradient_accumulation_steps=1,
        learning_rate="5e-5",
        num_warmup_steps=0,
        num_training_steps=10000,
        save_steps=1500,
        batch_size=16,
        beam_size=5,
        length_penalty="0",
        min_len=None,
        forbid_ignore_word=None,
        eval_script=None,
        eval_trunc_len=None,
        notes=(
            "Custom JSONL requires explicit length budgets and a task-specific evaluator if ROUGE scripts do not apply.",
        ),
    ),
}


def parser() -> argparse.ArgumentParser:
    argp = argparse.ArgumentParser(
        description=(
            "Validate planning arguments and print safe s2s-ft train/decode/eval commands. "
            "This script never imports s2s-ft, trains, decodes, downloads, or runs subprocesses."
        )
    )
    argp.add_argument("--task", required=True, choices=TASKS, help="Seq2seq task preset to plan.")
    argp.add_argument("--mode", default="all", choices=MODES, help="Which command(s) to print.")
    argp.add_argument("--train-file", help="JSONL training file with src/tgt keys.")
    argp.add_argument("--input-file", help="JSONL decoding file with src keys.")
    argp.add_argument("--gold-file", help="Gold/reference file for evaluation.")
    argp.add_argument("--pred-file", help="Prediction file for evaluation; defaults to decode output or model_path.split.")
    argp.add_argument("--output-file", help="Explicit decode prediction output path.")
    argp.add_argument("--output-dir", help="Training output directory for checkpoints and caches.")
    argp.add_argument("--model-path", help="Fine-tuned checkpoint directory or glob for decoding.")
    argp.add_argument("--model-type", default="unilm", choices=MODEL_TYPES, help="s2s-ft model_type.")
    argp.add_argument("--model-name-or-path", help="Pretrained model shortcut or local model path for training/tokenizer fallback.")
    argp.add_argument("--tokenizer-name", help="Tokenizer shortcut/path for decoding or tokenizer override for training.")
    argp.add_argument("--config-name", help="Optional config name/path for training.")
    argp.add_argument("--config-path", help="Optional config path for decoding.")
    argp.add_argument("--cache-dir", help="Cache directory to pass to native s2s-ft commands.")
    argp.add_argument("--cached-train-features-file", help="Optional cached training features path.")
    argp.add_argument("--split", help="Decode/eval split name; defaults by task.")
    argp.add_argument("--gpus", help="CUDA_VISIBLE_DEVICES value to prefix on train/decode commands.")
    argp.add_argument("--nproc-per-node", type=int, help="Distributed train process count; defaults from --gpus.")
    argp.add_argument("--do-lower-case", action="store_true", help="Add --do_lower_case for uncased checkpoints/tokenizers.")
    argp.add_argument("--fp16", action="store_true", help="Add fp16/Apex flags to planned native commands.")
    argp.add_argument("--fp16-opt-level", default="O2", help="Apex AMP opt level for s2s-ft training when --fp16 is set.")
    argp.add_argument("--no-cuda", action="store_true", help="Add --no_cuda to native commands for CPU/debug planning.")
    argp.add_argument("--max-source-seq-length", type=int, help="Training max source WordPiece length.")
    argp.add_argument("--max-target-seq-length", type=int, help="Training max target WordPiece length.")
    argp.add_argument("--max-seq-length", type=int, help="Decoding total max sequence length.")
    argp.add_argument("--max-tgt-length", type=int, help="Decoding max target length.")
    argp.add_argument("--per-gpu-train-batch-size", type=int, help="Training batch size per visible GPU/process.")
    argp.add_argument("--gradient-accumulation-steps", type=int, help="Gradient accumulation steps.")
    argp.add_argument("--learning-rate", help="Training learning rate.")
    argp.add_argument("--num-warmup-steps", type=int, help="Warmup steps.")
    argp.add_argument("--num-training-steps", type=int, help="Total training updates.")
    argp.add_argument("--save-steps", type=int, help="Checkpoint interval.")
    argp.add_argument("--target-mask-prob", type=float, help="Optional target segment mask/drop probability.")
    argp.add_argument("--source-mask-prob", type=float, help="Optional source mask probability.")
    argp.add_argument("--num-max-mask-token", type=int, help="Optional maximum number of masked tokens.")
    argp.add_argument("--mask-way", choices=("v0", "v1", "v2"), help="s2s-ft masking mode override.")
    argp.add_argument("--batch-size", type=int, help="Decoding batch size.")
    argp.add_argument("--beam-size", type=int, help="Decoding beam size.")
    argp.add_argument("--length-penalty", help="Decoding length penalty.")
    argp.add_argument("--min-len", type=int, help="Minimum generated target length.")
    argp.add_argument("--forbid-ignore-word", help="Pipe-separated tokens ignored by duplicate-ngram blocking.")
    argp.add_argument("--allow-duplicate-ngrams", action="store_true", help="Omit --forbid_duplicate_ngrams.")
    argp.add_argument("--need-score-traces", action="store_true", help="Add --need_score_traces; requires beam size > 1.")
    argp.add_argument("--eval-script", help="Override evaluation script path for custom workflows.")
    argp.add_argument("--eval-trunc-len", type=int, help="Optional evaluation truncation length.")
    argp.add_argument("--eval-perl", action="store_true", help="Add --perl to ROUGE evaluation command.")
    argp.add_argument("--eval-processes", type=int, help="Evaluation worker process count.")
    argp.add_argument("--check-files", action="store_true", help="Require referenced input/gold/checkpoint files to exist.")
    return argp


def wants(mode: str, target: str) -> bool:
    return mode == "all" or mode == target


def choose(value, fallback):
    return fallback if value is None else value


def visible_gpu_count(gpus: str | None) -> int:
    if not gpus:
        return 0
    return len([part for part in gpus.split(",") if part.strip()])


def default_nproc(args: argparse.Namespace) -> int:
    if args.nproc_per_node:
        return args.nproc_per_node
    count = visible_gpu_count(args.gpus)
    return count if count > 1 else 1


def command_lines(parts: Iterable[str], env: dict[str, str] | None = None) -> str:
    env = env or {}
    quoted = [f"{key}={shlex.quote(value)}" for key, value in env.items()]
    quoted.extend(shlex.quote(str(part)) for part in parts)
    return " \\\n  ".join(quoted)


def add_optional(parts: list[str], flag: str, value) -> None:
    if value is not None:
        parts.extend([flag, str(value)])


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def check_path(errors: list[str], label: str, path: str | None, kind: str = "file") -> None:
    if not path:
        return
    exists = os.path.isdir(path) if kind == "dir" else os.path.exists(path)
    if not exists:
        errors.append(f"{label} does not exist: {path}")


def resolved(args: argparse.Namespace, preset: TaskPreset) -> dict[str, object]:
    max_source = choose(args.max_source_seq_length, preset.max_source_seq_length)
    max_target = choose(args.max_target_seq_length, preset.max_target_seq_length)
    max_seq = choose(args.max_seq_length, preset.max_seq_length)
    max_tgt = choose(args.max_tgt_length, preset.max_tgt_length)
    if args.task == "custom-json" and max_seq == 0 and max_source and max_target:
        max_seq = max_source + max_target
    return {
        "split": choose(args.split, preset.split),
        "max_source_seq_length": max_source,
        "max_target_seq_length": max_target,
        "max_seq_length": max_seq,
        "max_tgt_length": max_tgt,
        "per_gpu_train_batch_size": choose(args.per_gpu_train_batch_size, preset.per_gpu_train_batch_size),
        "gradient_accumulation_steps": choose(args.gradient_accumulation_steps, preset.gradient_accumulation_steps),
        "learning_rate": choose(args.learning_rate, preset.learning_rate),
        "num_warmup_steps": choose(args.num_warmup_steps, preset.num_warmup_steps),
        "num_training_steps": choose(args.num_training_steps, preset.num_training_steps),
        "save_steps": choose(args.save_steps, preset.save_steps),
        "batch_size": choose(args.batch_size, preset.batch_size),
        "beam_size": choose(args.beam_size, preset.beam_size),
        "length_penalty": choose(args.length_penalty, preset.length_penalty),
        "min_len": choose(args.min_len, preset.min_len),
        "forbid_ignore_word": choose(args.forbid_ignore_word, preset.forbid_ignore_word),
        "eval_script": choose(args.eval_script, preset.eval_script),
        "eval_trunc_len": choose(args.eval_trunc_len, preset.eval_trunc_len),
    }


def validate(args: argparse.Namespace, vals: dict[str, object]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    mode = args.mode

    if wants(mode, "train"):
        require(errors, bool(args.train_file), "train mode requires --train-file")
        require(errors, bool(args.output_dir), "train mode requires --output-dir")
        require(errors, bool(args.model_name_or_path), "train mode requires --model-name-or-path")
        require(errors, int(vals["max_source_seq_length"]) > 0, "train mode requires a positive source length")
        require(errors, int(vals["max_target_seq_length"]) > 0, "train mode requires a positive target length")

    if wants(mode, "decode"):
        require(errors, bool(args.input_file), "decode mode requires --input-file")
        require(errors, bool(args.model_path), "decode mode requires --model-path")
        require(errors, bool(args.tokenizer_name or args.model_name_or_path), "decode mode requires --tokenizer-name or --model-name-or-path")
        require(errors, int(vals["max_seq_length"]) > 0, "decode mode requires a positive --max-seq-length")
        require(errors, int(vals["max_tgt_length"]) > 0, "decode mode requires a positive --max-tgt-length")
        if int(vals["max_seq_length"]) > 0 and int(vals["max_tgt_length"]) >= int(vals["max_seq_length"]) - 2:
            errors.append("decode --max-tgt-length must be less than --max-seq-length - 2")
        if args.need_score_traces and int(vals["beam_size"]) <= 1:
            errors.append("--need-score-traces requires --beam-size greater than 1")

    if wants(mode, "eval"):
        pred = args.pred_file or args.output_file or (f"{args.model_path}.{vals['split']}" if args.model_path else None)
        require(errors, bool(args.gold_file), "eval mode requires --gold-file")
        require(errors, bool(pred), "eval mode requires --pred-file, --output-file, or --model-path plus --split")
        if not vals["eval_script"]:
            errors.append("eval mode for custom-json requires --eval-script or a task-specific external evaluator")

    if args.no_cuda and args.fp16:
        warnings.append("--no-cuda and --fp16 were both selected; native CPU runs should usually omit fp16/Apex flags.")

    gpu_count = visible_gpu_count(args.gpus)
    nproc = default_nproc(args)
    if args.gpus and nproc > gpu_count:
        warnings.append(f"--nproc-per-node={nproc} exceeds visible GPU count {gpu_count} from --gpus={args.gpus!r}.")
    if args.gpus and nproc < gpu_count and wants(mode, "train"):
        warnings.append(f"--gpus exposes {gpu_count} devices but training uses nproc_per_node={nproc}.")

    if args.check_files:
        check_path(errors, "--train-file", args.train_file)
        check_path(errors, "--input-file", args.input_file)
        check_path(errors, "--gold-file", args.gold_file)
        check_path(errors, "--pred-file", args.pred_file)
        check_path(errors, "--model-path", args.model_path)

    return errors, warnings


def train_command(args: argparse.Namespace, vals: dict[str, object]) -> str:
    nproc = default_nproc(args)
    parts = ["python"]
    if nproc > 1:
        parts.extend(["-m", "torch.distributed.launch", f"--nproc_per_node={nproc}"])
    parts.append("run_seq2seq.py")
    parts.extend([
        "--train_file", args.train_file,
        "--output_dir", args.output_dir,
        "--model_type", args.model_type,
        "--model_name_or_path", args.model_name_or_path,
        "--max_source_seq_length", str(vals["max_source_seq_length"]),
        "--max_target_seq_length", str(vals["max_target_seq_length"]),
        "--per_gpu_train_batch_size", str(vals["per_gpu_train_batch_size"]),
        "--gradient_accumulation_steps", str(vals["gradient_accumulation_steps"]),
        "--learning_rate", str(vals["learning_rate"]),
        "--num_warmup_steps", str(vals["num_warmup_steps"]),
        "--num_training_steps", str(vals["num_training_steps"]),
        "--save_steps", str(vals["save_steps"]),
    ])
    add_optional(parts, "--tokenizer_name", args.tokenizer_name)
    add_optional(parts, "--config_name", args.config_name)
    add_optional(parts, "--cache_dir", args.cache_dir)
    add_optional(parts, "--cached_train_features_file", args.cached_train_features_file)
    add_optional(parts, "--target_mask_prob", args.target_mask_prob)
    add_optional(parts, "--source_mask_prob", args.source_mask_prob)
    add_optional(parts, "--num_max_mask_token", args.num_max_mask_token)
    add_optional(parts, "--mask_way", args.mask_way)
    if args.do_lower_case:
        parts.append("--do_lower_case")
    if args.fp16:
        parts.extend(["--fp16", "--fp16_opt_level", args.fp16_opt_level])
    if args.no_cuda:
        parts.append("--no_cuda")
    env = {"CUDA_VISIBLE_DEVICES": args.gpus} if args.gpus else None
    return command_lines(parts, env=env)


def decode_command(args: argparse.Namespace, vals: dict[str, object]) -> str:
    tokenizer = args.tokenizer_name or args.model_name_or_path
    parts = [
        "python", "decode_seq2seq.py",
        "--model_type", args.model_type,
        "--tokenizer_name", tokenizer,
        "--input_file", args.input_file,
        "--split", str(vals["split"]),
        "--model_path", args.model_path,
        "--max_seq_length", str(vals["max_seq_length"]),
        "--max_tgt_length", str(vals["max_tgt_length"]),
        "--batch_size", str(vals["batch_size"]),
        "--beam_size", str(vals["beam_size"]),
        "--length_penalty", str(vals["length_penalty"]),
        "--mode", "s2s",
    ]
    add_optional(parts, "--config_path", args.config_path)
    add_optional(parts, "--cache_dir", args.cache_dir)
    add_optional(parts, "--output_file", args.output_file)
    add_optional(parts, "--min_len", vals["min_len"])
    if not args.allow_duplicate_ngrams:
        parts.append("--forbid_duplicate_ngrams")
    add_optional(parts, "--forbid_ignore_word", vals["forbid_ignore_word"])
    if args.do_lower_case:
        parts.append("--do_lower_case")
    if args.fp16:
        parts.append("--fp16")
    if args.no_cuda:
        parts.append("--no_cuda")
    if args.need_score_traces:
        parts.append("--need_score_traces")
    env = {"CUDA_VISIBLE_DEVICES": args.gpus.split(",")[0]} if args.gpus else None
    return command_lines(parts, env=env)


def eval_command(args: argparse.Namespace, vals: dict[str, object]) -> str:
    pred = args.pred_file or args.output_file or f"{args.model_path}.{vals['split']}"
    parts = [
        "python", str(vals["eval_script"]),
        "--pred", pred,
        "--gold", args.gold_file,
        "--split", str(vals["split"]),
    ]
    add_optional(parts, "--trunc_len", vals["eval_trunc_len"])
    add_optional(parts, "--processes", args.eval_processes)
    if args.eval_perl:
        parts.append("--perl")
    return command_lines(parts)


def main(argv: list[str] | None = None) -> int:
    argp = parser()
    args = argp.parse_args(argv)
    preset = PRESETS[args.task]
    vals = resolved(args, preset)
    errors, warnings = validate(args, vals)

    if errors:
        print("Cannot build command plan:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    print("# Safe UniLM/s2s-ft command plan")
    print("# These commands are printed only; this helper does not execute training, decoding, evaluation, or downloads.")
    print(f"# task={args.task} mode={args.mode} split={vals['split']} model_type={args.model_type}")
    for note in preset.notes:
        print(f"# note: {note}")
    for warning in warnings:
        print(f"# warning: {warning}")

    if wants(args.mode, "train"):
        print("\n## train")
        print(train_command(args, vals))
    if wants(args.mode, "decode"):
        print("\n## decode")
        print(decode_command(args, vals))
    if wants(args.mode, "eval"):
        print("\n## eval")
        print(eval_command(args, vals))

    print("\n# Review environment compatibility, data line counts, tokenizer casing, checkpoints, and GPU visibility before running anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
