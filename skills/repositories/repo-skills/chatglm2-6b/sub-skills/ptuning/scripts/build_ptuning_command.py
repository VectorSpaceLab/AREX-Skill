#!/usr/bin/env python3
"""Print safe ChatGLM2-6B P-Tuning commands without executing them."""
from __future__ import annotations

import argparse
import shlex


def q(value: object) -> str:
    return shlex.quote(str(value))


def common_model_args(args: argparse.Namespace) -> list[str]:
    parts = ["--model_name_or_path", q(args.model_name_or_path), "--output_dir", q(args.output_dir), "--overwrite_output_dir"]
    if getattr(args, "pre_seq_len", None) is not None:
        parts += ["--pre_seq_len", q(args.pre_seq_len)]
    if getattr(args, "quantization_bit", None) is not None:
        parts += ["--quantization_bit", q(args.quantization_bit)]
    return parts


def torchrun_prefix(args: argparse.Namespace) -> list[str]:
    return ["torchrun", "--standalone", "--nnodes=1", f"--nproc-per-node={args.num_gpus}", q(args.runner_script)]


def build_train(args: argparse.Namespace, chat: bool = False) -> str:
    parts = torchrun_prefix(args)
    parts += ["--do_train", "--train_file", q(args.train_file), "--validation_file", q(args.validation_file)]
    parts += ["--prompt_column", q(args.prompt_column), "--response_column", q(args.response_column)]
    if chat and args.history_column:
        parts += ["--history_column", q(args.history_column)]
    parts += common_model_args(args)
    parts += [
        "--overwrite_cache",
        "--max_source_length", q(args.max_source_length),
        "--max_target_length", q(args.max_target_length),
        "--per_device_train_batch_size", q(args.per_device_train_batch_size),
        "--per_device_eval_batch_size", q(args.per_device_eval_batch_size),
        "--gradient_accumulation_steps", q(args.gradient_accumulation_steps),
        "--predict_with_generate",
        "--max_steps", q(args.max_steps),
        "--logging_steps", q(args.logging_steps),
        "--save_steps", q(args.save_steps),
        "--learning_rate", q(args.learning_rate),
    ]
    if args.preprocessing_num_workers is not None:
        parts += ["--preprocessing_num_workers", q(args.preprocessing_num_workers)]
    return " \\\n  ".join(parts)


def build_predict_prefix(args: argparse.Namespace) -> str:
    parts = torchrun_prefix(args)
    parts += ["--do_predict", "--validation_file", q(args.validation_file), "--test_file", q(args.test_file)]
    parts += ["--prompt_column", q(args.prompt_column), "--response_column", q(args.response_column)]
    if args.history_column:
        parts += ["--history_column", q(args.history_column)]
    parts += common_model_args(args)
    parts += ["--ptuning_checkpoint", q(args.ptuning_checkpoint), "--overwrite_cache", "--max_source_length", q(args.max_source_length), "--max_target_length", q(args.max_target_length), "--per_device_eval_batch_size", q(args.per_device_eval_batch_size), "--predict_with_generate"]
    return " \\\n  ".join(parts)


def build_predict_full(args: argparse.Namespace) -> str:
    args.model_name_or_path = args.checkpoint_path
    parts = torchrun_prefix(args)
    parts += ["--do_predict", "--validation_file", q(args.validation_file), "--test_file", q(args.test_file)]
    parts += ["--prompt_column", q(args.prompt_column), "--response_column", q(args.response_column)]
    parts += ["--model_name_or_path", q(args.model_name_or_path), "--output_dir", q(args.output_dir), "--overwrite_output_dir", "--overwrite_cache", "--max_source_length", q(args.max_source_length), "--max_target_length", q(args.max_target_length), "--per_device_eval_batch_size", q(args.per_device_eval_batch_size), "--predict_with_generate", "--fp16_full_eval"]
    return " \\\n  ".join(parts)


def build_web_demo(args: argparse.Namespace) -> str:
    parts = ["python", q(args.web_demo_script), "--model_name_or_path", q(args.model_name_or_path), "--ptuning_checkpoint", q(args.ptuning_checkpoint), "--pre_seq_len", q(args.pre_seq_len)]
    if args.quantization_bit is not None:
        parts += ["--quantization_bit", q(args.quantization_bit)]
    return " \\\n  ".join(parts)


def build_deepspeed(args: argparse.Namespace) -> str:
    parts = ["deepspeed", f"--num_gpus={args.num_gpus}", "--master_port", "${MASTER_PORT:-29500}", q(args.runner_script), "--deepspeed", q(args.deepspeed_config), "--do_train", "--train_file", q(args.train_file), "--test_file", q(args.validation_file), "--prompt_column", q(args.prompt_column), "--response_column", q(args.response_column), "--overwrite_cache", "--model_name_or_path", q(args.model_name_or_path), "--output_dir", q(args.output_dir), "--overwrite_output_dir", "--max_source_length", q(args.max_source_length), "--max_target_length", q(args.max_target_length), "--per_device_train_batch_size", q(args.per_device_train_batch_size), "--per_device_eval_batch_size", q(args.per_device_eval_batch_size), "--gradient_accumulation_steps", q(args.gradient_accumulation_steps), "--predict_with_generate", "--max_steps", q(args.max_steps), "--logging_steps", q(args.logging_steps), "--save_steps", q(args.save_steps), "--learning_rate", q(args.learning_rate), "--fp16"]
    return " \\\n  ".join(parts)


def add_common(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--model-name-or-path", default="THUDM/chatglm2-6b")
    sub.add_argument("--runner-script", default="sub-skills/ptuning/scripts/ptuning_runner/main.py", help="Bundled P-Tuning runner path, normally relative to the generated skill root")
    sub.add_argument("--output-dir", required=True)
    sub.add_argument("--num-gpus", type=int, default=1)
    sub.add_argument("--max-source-length", type=int, default=64)
    sub.add_argument("--max-target-length", type=int, default=128)
    sub.add_argument("--per-device-train-batch-size", type=int, default=1)
    sub.add_argument("--per-device-eval-batch-size", type=int, default=1)
    sub.add_argument("--gradient-accumulation-steps", type=int, default=16)
    sub.add_argument("--max-steps", type=int, default=3000)
    sub.add_argument("--logging-steps", type=int, default=10)
    sub.add_argument("--save-steps", type=int, default=1000)
    sub.add_argument("--learning-rate", default="2e-2")
    sub.add_argument("--pre-seq-len", type=int, default=128)
    sub.add_argument("--quantization-bit", type=int, default=4)
    sub.add_argument("--preprocessing-num-workers", type=int, default=10)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    train = commands.add_parser("train", help="Print a P-Tuning v2 train command")
    add_common(train)
    train.add_argument("--train-file", required=True)
    train.add_argument("--validation-file", required=True)
    train.add_argument("--prompt-column", default="content")
    train.add_argument("--response-column", default="summary")

    train_chat = commands.add_parser("train-chat", help="Print a multi-turn chat P-Tuning command")
    add_common(train_chat)
    train_chat.add_argument("--train-file", required=True)
    train_chat.add_argument("--validation-file", required=True)
    train_chat.add_argument("--prompt-column", default="prompt")
    train_chat.add_argument("--response-column", default="response")
    train_chat.add_argument("--history-column", default="history")
    train_chat.set_defaults(learning_rate="1e-2", max_source_length=256, max_target_length=256)

    predict_prefix = commands.add_parser("predict-prefix", help="Print prediction command for a prefix checkpoint")
    add_common(predict_prefix)
    predict_prefix.add_argument("--validation-file", required=True)
    predict_prefix.add_argument("--test-file", required=True)
    predict_prefix.add_argument("--ptuning-checkpoint", required=True)
    predict_prefix.add_argument("--prompt-column", default="content")
    predict_prefix.add_argument("--response-column", default="summary")
    predict_prefix.add_argument("--history-column", default=None)

    predict_full = commands.add_parser("predict-full", help="Print prediction command for a full fine-tuned checkpoint")
    add_common(predict_full)
    predict_full.add_argument("--checkpoint-path", required=True)
    predict_full.add_argument("--validation-file", required=True)
    predict_full.add_argument("--test-file", required=True)
    predict_full.add_argument("--prompt-column", default="content")
    predict_full.add_argument("--response-column", default="summary")

    web = commands.add_parser("web-demo-prefix", help="Print a prefix-checkpoint web demo command")
    web.add_argument("--model-name-or-path", default="THUDM/chatglm2-6b")
    web.add_argument("--web-demo-script", default="sub-skills/ptuning/scripts/ptuning_runner/web_demo.py", help="Bundled P-Tuning web demo path, normally relative to the generated skill root")
    web.add_argument("--ptuning-checkpoint", required=True)
    web.add_argument("--pre-seq-len", type=int, default=128)
    web.add_argument("--quantization-bit", type=int, default=None)
    web.add_argument("--output-dir", default="unused", help=argparse.SUPPRESS)

    ds = commands.add_parser("finetune-deepspeed", help="Print optional full fine-tune DeepSpeed command")
    add_common(ds)
    ds.set_defaults(num_gpus=4, learning_rate="1e-4", gradient_accumulation_steps=1, per_device_train_batch_size=4, max_target_length=64, quantization_bit=None, pre_seq_len=None)
    ds.add_argument("--train-file", required=True)
    ds.add_argument("--validation-file", required=True)
    ds.add_argument("--prompt-column", default="content")
    ds.add_argument("--response-column", default="summary")
    ds.add_argument("--deepspeed-config", default="sub-skills/ptuning/scripts/ptuning_runner/deepspeed.json")

    args = parser.parse_args()
    if args.command == "train":
        print(build_train(args))
    elif args.command == "train-chat":
        print(build_train(args, chat=True))
    elif args.command == "predict-prefix":
        print(build_predict_prefix(args))
    elif args.command == "predict-full":
        print(build_predict_full(args))
    elif args.command == "web-demo-prefix":
        print(build_web_demo(args))
    elif args.command == "finetune-deepspeed":
        print(build_deepspeed(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
