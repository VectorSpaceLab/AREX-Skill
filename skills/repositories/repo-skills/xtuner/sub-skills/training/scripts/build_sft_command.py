#!/usr/bin/env python3
"""Build a safe XTuner V1 SFT/pretraining torchrun command.

The script prints a command; it never launches training. It is a self-contained
replacement for environment-specific XTuner example launch shells.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

CHAT_TEMPLATES = ("internlm2", "qwen3", "gpt-oss", "deepseek-v3", "glm5.2")
TOKENIZE_FNS = ("openai", "ftdp")
OPTIMS = ("AdamW", "Muon")
SCHEDULERS = ("cosine", "linear", "constant")
LOSS_MODES = ("eager", "chunk", "liger")
PACK_LEVELS = ("soft", "none", "__legacy", "hard", "mllm_hybrid", "preset")


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - argparse displays this
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def _env_assignment(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("environment entries must be KEY=VALUE")
    key, val = value.split("=", 1)
    if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
        raise argparse.ArgumentTypeError(f"invalid environment variable name: {key!r}")
    return key, val


def _existing_or_glob_jsonl(path_text: str) -> list[Path]:
    path = Path(path_text)
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(p for p in path.iterdir() if p.suffix == ".jsonl")
    matches = [Path(p) for p in glob.glob(path_text)]
    return sorted(p for p in matches if p.suffix == ".jsonl" and p.exists())


def _path_has_config_json(path_text: str | None) -> bool | None:
    if not path_text:
        return None
    path = Path(path_text)
    if not path.exists():
        return None  # may be a model id or a path available only on worker nodes
    return (path / "config.json").is_file()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a dry torchrun command for XTuner V1 SFT/pretraining. "
            "Use either --config or direct TrainingArguments; never both."
        )
    )

    launch = parser.add_argument_group("torchrun resources")
    launch.add_argument("--nproc-per-node", default=os.environ.get("NPROC_PER_NODE", "1"))
    launch.add_argument("--nnodes", default=os.environ.get("NNODES", os.environ.get("NODE_COUNT", "1")))
    launch.add_argument("--node-rank", default=os.environ.get("NODE_RANK", "0"))
    launch.add_argument("--master-addr", default=os.environ.get("MASTER_ADDR", "127.0.0.1"))
    launch.add_argument("--master-port", default=os.environ.get("MASTER_PORT", "6000"))
    launch.add_argument("--tee", default="3", help="torchrun --tee value; use --no-torchrun-tee to omit")
    launch.add_argument("--no-torchrun-tee", action="store_true", help="omit torchrun --tee")
    launch.add_argument(
        "--module",
        default="xtuner.v1.train.cli.sft",
        help="Python module passed to torchrun -m (default: installed XTuner SFT entrypoint)",
    )

    mode = parser.add_argument_group("launch mode")
    mode.add_argument("--config", help="Python config file containing top-level trainer = TrainerConfig(...)")

    direct = parser.add_argument_group("direct TrainingArguments")
    direct.add_argument("--load-from", help="HF model snapshot/id or supported checkpoint source")
    direct.add_argument("--model-cfg", help="model alias or Python config file exposing top-level model")
    direct.add_argument("--chat-template", choices=CHAT_TEMPLATES)
    direct.add_argument("--tokenize-fn", choices=TOKENIZE_FNS, default=None)
    direct.add_argument("--tokenizer-path")
    direct.add_argument("--dataset", help="dataset config .py, JSONL file, directory, or glob")
    direct.add_argument("--cache-dir")
    direct.add_argument("--cache-tag")
    direct.add_argument("--max-length", type=_positive_int)
    direct.add_argument("--lr", type=float)
    direct.add_argument("--optim", choices=OPTIMS)
    direct.add_argument("--lr-min", type=float)
    direct.add_argument("--scheduler-type", choices=SCHEDULERS)
    direct.add_argument("--warmup-ratio", type=float)
    direct.add_argument("--loss-mode", choices=LOSS_MODES, help="emits --loss-config.mode")
    direct.add_argument("--loss-chunk-size", type=_positive_int, help="emits --loss-config.chunk-size")
    direct.add_argument("--total-step", type=_positive_int)
    direct.add_argument("--epoch-num", type=_positive_int)
    direct.add_argument("--work-dir", help="Trainer work directory; also used for --tee-log default")
    direct.add_argument("--global-batch-size", type=_positive_int)
    direct.add_argument("--pack-level", choices=PACK_LEVELS)
    direct.add_argument("--pack-max-length", type=_positive_int)
    direct.add_argument("--pack-workers", type=_non_negative_int)
    direct.add_argument("--num-workers", type=_non_negative_int)
    direct.add_argument("--no-pack-to-max-length", action="store_true")
    direct.add_argument("--no-global-pack", action="store_true")
    direct.add_argument("--no-group-by-length", action="store_true")
    direct.add_argument("--pack-config-path")
    direct.add_argument("--sampler-config-path")
    direct.add_argument("--async-checkpoint", action="store_true")
    direct.add_argument("--fsdp-tp-size", type=_positive_int, help="emits --fsdp-config.tp-size")
    direct.add_argument("--fsdp-ep-size", type=_positive_int, help="emits --fsdp-config.ep-size")
    direct.add_argument("--fsdp-hsdp-sharding-size", type=_positive_int, help="emits --fsdp-config.hsdp-sharding-size")
    direct.add_argument("--fsdp-recompute-ratio", type=float, help="emits --fsdp-config.recompute-ratio")
    direct.add_argument("--fsdp-vision-recompute-ratio", type=float, help="emits --fsdp-config.vision-recompute-ratio")
    direct.add_argument("--fsdp-cpu-offload", action="store_true", help="emits --fsdp-config.cpu-offload")
    direct.add_argument("--fsdp-no-torch-compile", action="store_true", help="emits --fsdp-config.no-torch-compile")
    direct.add_argument(
        "--sft-arg",
        action="append",
        default=[],
        help=(
            "append one literal extra XTuner CLI token. For option-looking values use "
            "--sft-arg=--flag or repeat as --sft-arg=--flag --sft-arg=value."
        ),
    )

    env = parser.add_argument_group("environment")
    env.add_argument("--env", action="append", type=_env_assignment, default=[], help="add KEY=VALUE before torchrun")
    env.add_argument(
        "--run-sft-default-env",
        action="store_true",
        help="add safe defaults adapted from XTuner run_sft.sh (GC, allocator, FA3 toggle)",
    )
    env.add_argument("--use-fa3", choices=("0", "1"), help="set XTUNER_USE_FA3")
    env.add_argument("--activation-offload", choices=("0", "1"), help="set XTUNER_ACTIVATION_OFFLOAD")
    env.add_argument("--deterministic", choices=("true", "false"), help="set XTUNER_DETERMINISTIC")
    env.add_argument("--torch-logs", help="set TORCH_LOGS, for example recompiles")
    env.add_argument("--cuda-alloc-conf", help="set PYTORCH_CUDA_ALLOC_CONF")

    output = parser.add_argument_group("output")
    output.add_argument("--tee-log", action="store_true", help="append shell pipeline to tee output into a node log")
    output.add_argument("--log-file", help="explicit log file for --tee-log")
    output.add_argument("--no-path-checks", action="store_true", help="skip local path sanity checks")
    output.add_argument("--format", choices=("shell", "argv", "json"), default="shell")
    return parser


DIRECT_FIELDS = {
    "load_from",
    "model_cfg",
    "chat_template",
    "tokenize_fn",
    "tokenizer_path",
    "dataset",
    "cache_dir",
    "cache_tag",
    "max_length",
    "lr",
    "optim",
    "lr_min",
    "scheduler_type",
    "warmup_ratio",
    "loss_mode",
    "loss_chunk_size",
    "total_step",
    "epoch_num",
    "global_batch_size",
    "pack_level",
    "pack_max_length",
    "pack_workers",
    "num_workers",
    "pack_config_path",
    "sampler_config_path",
    "fsdp_tp_size",
    "fsdp_ep_size",
    "fsdp_hsdp_sharding_size",
    "fsdp_recompute_ratio",
    "fsdp_vision_recompute_ratio",
}

DIRECT_BOOL_FIELDS = {
    "no_pack_to_max_length",
    "no_global_pack",
    "no_group_by_length",
    "async_checkpoint",
    "fsdp_cpu_offload",
    "fsdp_no_torch_compile",
}


def has_direct_arguments(args: argparse.Namespace) -> bool:
    for name in DIRECT_FIELDS:
        if getattr(args, name) is not None:
            return True
    for name in DIRECT_BOOL_FIELDS:
        if getattr(args, name):
            return True
    if args.sft_arg:
        return True
    return False


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    direct_present = has_direct_arguments(args)
    if args.config and direct_present:
        parser.error(
            "XTuner V1 accepts either --config or direct TrainingArguments, not both. "
            "Move model/dataset/training flags into the config file or remove --config."
        )
    if not args.config and not direct_present:
        parser.error("provide --config or direct TrainingArguments")

    if args.total_step is not None and args.epoch_num is not None:
        parser.error("--total-step and --epoch-num are mutually exclusive")

    if not args.config:
        missing = []
        if not args.dataset:
            missing.append("--dataset")
        if not args.chat_template:
            missing.append("--chat-template")
        if not (args.load_from or args.model_cfg):
            missing.append("--load-from or --model-cfg")
        if missing:
            parser.error("direct mode is missing: " + ", ".join(missing))

    if args.pack_level == "preset":
        if not args.pack_config_path or not args.sampler_config_path:
            parser.error("--pack-level preset requires --pack-config-path and --sampler-config-path")

    if args.no_path_checks:
        return

    if args.config:
        cfg = Path(args.config)
        if cfg.exists() and not cfg.is_file():
            parser.error(f"--config exists but is not a file: {args.config}")
        if cfg.exists() and cfg.suffix != ".py":
            parser.error("--config should be a Python file containing top-level trainer")

    if args.model_cfg and args.model_cfg.endswith(".py"):
        model_cfg = Path(args.model_cfg)
        if model_cfg.exists() and not model_cfg.is_file():
            parser.error(f"--model-cfg exists but is not a file: {args.model_cfg}")

    if args.dataset and not args.dataset.endswith(".py"):
        matches = _existing_or_glob_jsonl(args.dataset)
        dataset_path = Path(args.dataset)
        if dataset_path.exists() and dataset_path.is_dir() and not matches:
            parser.error(f"--dataset directory contains no .jsonl files: {args.dataset}")
        if any(ch in args.dataset for ch in "*?[") and not matches:
            parser.error(f"--dataset glob matched no existing .jsonl files: {args.dataset}")
        if dataset_path.exists() and dataset_path.is_file() and dataset_path.suffix != ".jsonl":
            parser.error("--dataset direct file should have .jsonl suffix unless using a .py dataset config")

    hf_check = _path_has_config_json(args.load_from)
    if hf_check is False and args.tokenizer_path is None and args.model_cfg is None:
        parser.error(
            "local --load-from path exists but has no config.json. Point to the HF snapshot directory "
            "or pass --tokenizer-path and --model-cfg explicitly."
        )


def build_env(args: argparse.Namespace) -> dict[str, str]:
    env: dict[str, str] = {}
    if args.run_sft_default_env:
        env.update(
            {
                "XTUNER_ACTIVATION_OFFLOAD": "0",
                "XTUNER_GC_ENABLE": "1",
                "XTUNER_USE_FA3": "1",
                "TORCH_LOGS": "recompiles",
                "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
            }
        )
        if args.deterministic is None:
            env["XTUNER_DETERMINISTIC"] = "false"
    if args.use_fa3 is not None:
        env["XTUNER_USE_FA3"] = args.use_fa3
    if args.activation_offload is not None:
        env["XTUNER_ACTIVATION_OFFLOAD"] = args.activation_offload
    if args.deterministic is not None:
        env["XTUNER_DETERMINISTIC"] = args.deterministic
    if args.torch_logs is not None:
        env["TORCH_LOGS"] = args.torch_logs
    if args.cuda_alloc_conf is not None:
        env["PYTORCH_CUDA_ALLOC_CONF"] = args.cuda_alloc_conf
    for key, val in args.env:
        env[key] = val
    return env


def add_option(argv: list[str], flag: str, value: Any) -> None:
    if value is not None:
        argv.extend([flag, str(value)])


def build_torchrun_argv(args: argparse.Namespace) -> list[str]:
    argv = ["torchrun"]
    add_option(argv, "--nproc-per-node", args.nproc_per_node)
    add_option(argv, "--nnodes", args.nnodes)
    add_option(argv, "--node-rank", args.node_rank)
    add_option(argv, "--master-addr", args.master_addr)
    add_option(argv, "--master-port", args.master_port)
    if not args.no_torchrun_tee and args.tee:
        add_option(argv, "--tee", args.tee)
    argv.extend(["-m", args.module])
    return argv


def build_xtuner_argv(args: argparse.Namespace) -> list[str]:
    argv: list[str] = []
    if args.config:
        argv.extend(["--config", args.config])
        return argv

    add_option(argv, "--load-from", args.load_from)
    add_option(argv, "--model-cfg", args.model_cfg)
    add_option(argv, "--chat-template", args.chat_template)
    add_option(argv, "--tokenize-fn", args.tokenize_fn)
    add_option(argv, "--tokenizer-path", args.tokenizer_path)
    add_option(argv, "--dataset", args.dataset)
    add_option(argv, "--cache-dir", args.cache_dir)
    add_option(argv, "--cache-tag", args.cache_tag)
    add_option(argv, "--max-length", args.max_length)
    add_option(argv, "--lr", args.lr)
    add_option(argv, "--optim", args.optim)
    add_option(argv, "--lr-min", args.lr_min)
    add_option(argv, "--scheduler-type", args.scheduler_type)
    add_option(argv, "--warmup-ratio", args.warmup_ratio)
    add_option(argv, "--loss-config.mode", args.loss_mode)
    add_option(argv, "--loss-config.chunk-size", args.loss_chunk_size)
    add_option(argv, "--total-step", args.total_step)
    add_option(argv, "--epoch-num", args.epoch_num)
    add_option(argv, "--work-dir", args.work_dir)
    add_option(argv, "--global-batch-size", args.global_batch_size)
    add_option(argv, "--pack-level", args.pack_level)
    add_option(argv, "--pack-max-length", args.pack_max_length)
    add_option(argv, "--pack-workers", args.pack_workers)
    add_option(argv, "--num-workers", args.num_workers)
    add_option(argv, "--pack-config-path", args.pack_config_path)
    add_option(argv, "--sampler-config-path", args.sampler_config_path)

    if args.no_pack_to_max_length:
        argv.append("--no-pack-to-max-length")
    if args.no_global_pack:
        argv.append("--no-global-pack")
    if args.no_group_by_length:
        argv.append("--no-group-by-length")
    if args.async_checkpoint:
        argv.append("--async-checkpoint")

    add_option(argv, "--fsdp-config.tp-size", args.fsdp_tp_size)
    add_option(argv, "--fsdp-config.ep-size", args.fsdp_ep_size)
    add_option(argv, "--fsdp-config.hsdp-sharding-size", args.fsdp_hsdp_sharding_size)
    add_option(argv, "--fsdp-config.recompute-ratio", args.fsdp_recompute_ratio)
    add_option(argv, "--fsdp-config.vision-recompute-ratio", args.fsdp_vision_recompute_ratio)
    if args.fsdp_cpu_offload:
        argv.append("--fsdp-config.cpu-offload")
    if args.fsdp_no_torch_compile:
        argv.append("--fsdp-config.no-torch-compile")

    argv.extend(args.sft_arg)
    return argv


def shell_for_command(env: dict[str, str], argv: list[str], args: argparse.Namespace) -> str:
    env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
    command = shlex.join(argv)
    if env_prefix:
        command = env_prefix + " " + command

    if not args.tee_log:
        return command

    if args.log_file:
        log_file = Path(args.log_file)
    else:
        base = Path(args.work_dir) if args.work_dir else Path(".")
        log_file = base / f"node_{args.node_rank}.txt"
    mkdir = f"mkdir -p {shlex.quote(str(log_file.parent))}"
    return f"{mkdir}\n{command} 2>&1 | tee -a {shlex.quote(str(log_file))}"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    env = build_env(args)
    command_argv = build_torchrun_argv(args) + build_xtuner_argv(args)
    shell = shell_for_command(env, command_argv, args)

    if args.format == "shell":
        print(shell)
    elif args.format == "argv":
        for token in command_argv:
            print(token)
    else:
        print(
            json.dumps(
                {
                    "env": env,
                    "argv": command_argv,
                    "shell": shell,
                    "launch_mode": "config" if args.config else "direct",
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
