#!/usr/bin/env python3
"""Build safe lm-eval commands and optional YAML configs.

This helper performs argument assembly only. It does not import lm_eval, load
models, access datasets, or run evaluations.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any


def parse_key_value(values: list[str] | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in values or []:
        pieces = []
        for chunk in item.split(","):
            chunk = chunk.strip()
            if chunk:
                pieces.append(chunk)
        for piece in pieces:
            if "=" not in piece:
                raise argparse.ArgumentTypeError(f"expected key=value, got {piece!r}")
            key, value = piece.split("=", 1)
            key = key.strip()
            if not key:
                raise argparse.ArgumentTypeError(f"empty key in {piece!r}")
            parsed[key] = coerce_scalar(value.strip())
    return parsed


def coerce_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "none" or lowered == "null":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_tasks(raw_tasks: str | None) -> list[str]:
    if not raw_tasks:
        return []
    tasks: list[str] = []
    for item in raw_tasks.replace(",", " ").split():
        if item:
            tasks.append(item)
    return tasks


def parse_samples(raw_samples: str | None) -> dict[str, list[int]] | None:
    if raw_samples is None:
        return None
    try:
        data = json.loads(raw_samples)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--samples must be JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("--samples must be a JSON object mapping task names to index lists")
    for task, indices in data.items():
        if not isinstance(task, str) or not isinstance(indices, list):
            raise SystemExit("--samples must map string task names to lists of integers")
        if not all(isinstance(index, int) for index in indices):
            raise SystemExit("--samples index lists must contain only integers")
    return data


def parse_seed(raw_seed: str | None) -> int | list[int | None] | None:
    if raw_seed is None:
        return None
    parts = [part.strip() for part in raw_seed.split(",")]
    if len(parts) == 1:
        return None if parts[0].lower() == "none" else int(parts[0])
    if len(parts) not in (3, 4):
        raise SystemExit("--seed must be a single integer/None or 3-4 comma-separated values")
    parsed: list[int | None] = []
    for part in parts:
        parsed.append(None if part.lower() == "none" else int(part))
    return parsed


def yaml_quote(value: str) -> str:
    return json.dumps(value)


def dump_yaml(data: dict[str, Any]) -> str:
    lines: list[str] = []

    def emit(key: str, value: Any, indent: int = 0) -> None:
        prefix = " " * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            for child_key, child_value in value.items():
                emit(str(child_key), child_value, indent + 2)
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}  - {json.dumps(item)}")
                elif isinstance(item, str):
                    lines.append(f"{prefix}  - {yaml_quote(item)}")
                elif item is None:
                    lines.append(f"{prefix}  - null")
                elif isinstance(item, bool):
                    lines.append(f"{prefix}  - {str(item).lower()}")
                else:
                    lines.append(f"{prefix}  - {item}")
        elif isinstance(value, str):
            lines.append(f"{prefix}{key}: {yaml_quote(value)}")
        elif value is None:
            lines.append(f"{prefix}{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {str(value).lower()}")
        else:
            lines.append(f"{prefix}{key}: {value}")

    for top_key, top_value in data.items():
        emit(top_key, top_value)
    return "\n".join(lines) + "\n"


def cache_requests_config(value: str | None) -> dict[str, bool] | None:
    if value is None:
        return None
    return {
        "cache_requests": value in {"true", "refresh"},
        "rewrite_requests_cache": value == "refresh",
        "delete_requests_cache": value == "delete",
    }


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    tasks = parse_tasks(args.tasks)
    samples = parse_samples(args.samples)
    if args.limit is not None and samples is not None:
        raise SystemExit("--limit and --samples are mutually exclusive")
    if (args.log_samples or args.predict_only) and not args.output_path:
        raise SystemExit("--output-path is required with --log-samples or --predict-only")
    if args.fewshot_as_multiturn and not args.apply_chat_template:
        raise SystemExit("--fewshot-as-multiturn requires --apply-chat-template")
    if not tasks and not args.config:
        raise SystemExit("provide --tasks or --config")

    config: dict[str, Any] = {}
    if args.model:
        config["model"] = args.model
    model_args = parse_key_value(args.model_arg)
    if model_args:
        config["model_args"] = model_args
    if tasks:
        config["tasks"] = tasks
    if args.num_fewshot is not None:
        config["num_fewshot"] = args.num_fewshot
    if args.batch_size is not None:
        config["batch_size"] = coerce_scalar(args.batch_size)
    if args.max_batch_size is not None:
        config["max_batch_size"] = args.max_batch_size
    if args.device:
        config["device"] = args.device
    if args.limit is not None:
        config["limit"] = args.limit
    if samples is not None:
        config["samples"] = samples
    if args.use_cache:
        config["use_cache"] = args.use_cache
    cache_config = cache_requests_config(args.cache_requests)
    if cache_config:
        config["cache_requests"] = cache_config
    if args.output_path:
        config["output_path"] = args.output_path
    if args.log_samples:
        config["log_samples"] = True
    if args.predict_only:
        config["predict_only"] = True
    if args.apply_chat_template is not None:
        config["apply_chat_template"] = args.apply_chat_template
    if args.system_instruction:
        config["system_instruction"] = args.system_instruction
    if args.fewshot_as_multiturn:
        config["fewshot_as_multiturn"] = True
    if args.include_path:
        config["include_path"] = args.include_path
    gen_kwargs = parse_key_value(args.gen_kwarg)
    if gen_kwargs:
        config["gen_kwargs"] = gen_kwargs
    if args.wandb_arg:
        config["wandb_args"] = parse_key_value(args.wandb_arg)
    if args.hf_hub_log_arg:
        config["hf_hub_log_args"] = parse_key_value(args.hf_hub_log_arg)
    seed = parse_seed(args.seed)
    if seed is not None:
        config["seed"] = seed
    if args.trust_remote_code:
        config["trust_remote_code"] = True
    if args.confirm_run_unsafe_code:
        config["confirm_run_unsafe_code"] = True
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--metadata must be JSON: {exc}") from exc
        if not isinstance(metadata, dict):
            raise SystemExit("--metadata must be a JSON object")
        config["metadata"] = metadata
    return config


def build_command(args: argparse.Namespace) -> list[str]:
    command = [args.executable, "run"]
    if args.config:
        command.extend(["--config", args.config])
    config = build_config(args)
    if args.config and not args.include_cli_overrides:
        return command
    cli_cache_requests = args.cache_requests
    if "model" in config:
        command.extend(["--model", str(config["model"])])
    if "model_args" in config:
        command.append("--model_args")
        command.extend(f"{key}={value}" for key, value in config["model_args"].items())
    if "tasks" in config:
        command.extend(["--tasks", ",".join(config["tasks"])])
    scalar_flags = [
        ("num_fewshot", "--num_fewshot"),
        ("batch_size", "--batch_size"),
        ("max_batch_size", "--max_batch_size"),
        ("device", "--device"),
        ("limit", "--limit"),
        ("use_cache", "--use_cache"),
        ("output_path", "--output_path"),
        ("system_instruction", "--system_instruction"),
        ("include_path", "--include_path"),
        ("seed", "--seed"),
        ("metadata", "--metadata"),
    ]
    for key, flag in scalar_flags:
        if key not in config:
            continue
        value = config[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        command.extend([flag, str(value)])
    if cli_cache_requests:
        command.extend(["--cache_requests", cli_cache_requests])
    if "samples" in config:
        command.extend(["--samples", json.dumps(config["samples"])])
    if config.get("log_samples"):
        command.append("--log_samples")
    if config.get("predict_only"):
        command.append("--predict_only")
    if "apply_chat_template" in config:
        value = config["apply_chat_template"]
        if value is True:
            command.append("--apply_chat_template")
        else:
            command.extend(["--apply_chat_template", str(value)])
    if config.get("fewshot_as_multiturn"):
        command.extend(["--fewshot_as_multiturn", "true"])
    if "gen_kwargs" in config:
        command.append("--gen_kwargs")
        command.extend(f"{key}={value}" for key, value in config["gen_kwargs"].items())
    if "wandb_args" in config:
        command.append("--wandb_args")
        command.extend(f"{key}={value}" for key, value in config["wandb_args"].items())
    if "hf_hub_log_args" in config:
        command.append("--hf_hub_log_args")
        command.extend(f"{key}={value}" for key, value in config["hf_hub_log_args"].items())
    if config.get("trust_remote_code"):
        command.append("--trust_remote_code")
    if config.get("confirm_run_unsafe_code"):
        command.append("--confirm_run_unsafe_code")
    return command


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", default="lm-eval", help="CLI executable to use")
    parser.add_argument("--config", help="Existing config path to pass to lm-eval run")
    parser.add_argument("--include-cli-overrides", action="store_true", help="Keep generated CLI flags even when --config is supplied")
    parser.add_argument("--write-config", help="Write a YAML config file built from the provided options")
    parser.add_argument("--model", default="hf")
    parser.add_argument("--model-arg", action="append", help="Model argument key=value; may be repeated")
    parser.add_argument("--tasks", help="Comma- or space-separated task names")
    parser.add_argument("--num-fewshot", type=int)
    parser.add_argument("--batch-size")
    parser.add_argument("--max-batch-size", type=int)
    parser.add_argument("--device")
    parser.add_argument("--limit", type=float)
    parser.add_argument("--samples", help="JSON mapping task names to sample index lists")
    parser.add_argument("--use-cache")
    parser.add_argument("--cache-requests", choices=["true", "refresh", "delete"])
    parser.add_argument("--output-path")
    parser.add_argument("--log-samples", action="store_true")
    parser.add_argument("--predict-only", action="store_true")
    parser.add_argument("--apply-chat-template", nargs="?", const=True)
    parser.add_argument("--system-instruction")
    parser.add_argument("--fewshot-as-multiturn", action="store_true")
    parser.add_argument("--include-path")
    parser.add_argument("--gen-kwarg", action="append", help="Generation argument key=value; may be repeated")
    parser.add_argument("--wandb-arg", action="append", help="W&B argument key=value; may be repeated")
    parser.add_argument("--hf-hub-log-arg", action="append", help="HF Hub logging argument key=value; may be repeated")
    parser.add_argument("--seed")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--confirm-run-unsafe-code", action="store_true")
    parser.add_argument("--metadata", help="JSON object for task metadata")
    parser.add_argument("--json", action="store_true", help="Print JSON with argv and shell command")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    config = build_config(args)
    if args.write_config:
        path = Path(args.write_config)
        path.write_text(dump_yaml(config), encoding="utf-8")
    command = build_command(args)
    if args.json:
        print(json.dumps({"argv": command, "shell": shlex.join(command)}, indent=2))
    else:
        print(shlex.join(command))
        if args.write_config:
            print(f"Wrote config: {args.write_config}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
