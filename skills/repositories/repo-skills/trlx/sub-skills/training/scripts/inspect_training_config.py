#!/usr/bin/env python3
"""Inspect a trlX training config without launching training or downloading models."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Dict


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--default", choices=("ppo", "ilql", "sft"), help="Summarize a bundled default config.")
    group.add_argument("--yaml", type=Path, help="Load and summarize a TRLConfig YAML file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if hasattr(value, "__dict__"):
        return {str(k): jsonable(v) for k, v in value.__dict__.items()}
    return repr(value)


def section(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": obj}


def version(name: str) -> str | None:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def register_method(method_name: str | None) -> None:
    name = (method_name or "").lower()
    if "ppo" in name:
        import trlx.models.modeling_ppo  # noqa: F401
    elif "ilql" in name:
        import trlx.models.modeling_ilql  # noqa: F401
    elif "sft" in name:
        from trlx.trainer.accelerate_sft_trainer import SFTConfig  # noqa: F401
    elif "rft" in name:
        from trlx.trainer.accelerate_rft_trainer import RFTConfig  # noqa: F401
    else:
        import trlx.models.modeling_ilql  # noqa: F401
        import trlx.models.modeling_ppo  # noqa: F401
        from trlx.trainer.accelerate_sft_trainer import SFTConfig  # noqa: F401
        try:
            from trlx.trainer.accelerate_rft_trainer import RFTConfig  # noqa: F401
        except Exception:
            pass


def load_config(args: argparse.Namespace) -> tuple[Any, Dict[str, Any]]:
    if args.default:
        from trlx.data.default_configs import default_ilql_config, default_ppo_config, default_sft_config

        factories = {"ppo": default_ppo_config, "ilql": default_ilql_config, "sft": default_sft_config}
        return factories[args.default](), {"type": "default", "name": args.default}

    yaml_path = args.yaml.expanduser()
    if not yaml_path.is_file():
        raise FileNotFoundError(f"YAML config not found: {yaml_path}")

    import yaml

    with yaml_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    method_name = None
    if isinstance(raw, dict) and isinstance(raw.get("method"), dict):
        method_name = raw["method"].get("name")
    register_method(str(method_name) if method_name is not None else None)

    from trlx.data.configs import TRLConfig

    return TRLConfig.load_yaml(str(yaml_path)), {
        "type": "yaml",
        "path": str(yaml_path),
        "method_name_seen": method_name,
    }


def validate(config: Any) -> Dict[str, list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    train = config.train
    model = config.model
    tokenizer = config.tokenizer
    optimizer = config.optimizer
    scheduler = config.scheduler
    method = config.method

    trainer = str(train.trainer or "")
    trainer_l = trainer.lower()
    method_name = str(getattr(method, "name", "") or "")
    method_l = method_name.lower()
    model_arch = str(getattr(model, "model_arch_type", "") or "")

    expected = {
        "ppo": "accelerateppotrainer",
        "ilql": "accelerateilqltrainer",
        "sft": "acceleratesfttrainer",
        "rft": "acceleraterfttrainer",
    }
    for key, expected_trainer in expected.items():
        if key in method_l and trainer_l != expected_trainer:
            warnings.append(f"Method {method_name!r} usually pairs with trainer {expected_trainer}.")
        if trainer_l == expected_trainer and key not in method_l:
            warnings.append(f"Trainer {trainer!r} usually pairs with a {key.upper()} method config.")

    if str(train.pipeline).lower() != "promptpipeline":
        warnings.append("Stock trlX training normally uses train.pipeline='PromptPipeline'.")

    gen_kwargs = section(getattr(method, "gen_kwargs", {}))
    if hasattr(method, "gen_kwargs"):
        if "max_new_tokens" not in gen_kwargs:
            warnings.append("method.gen_kwargs lacks max_new_tokens; trlx.train uses it to compute max prompt length.")
        else:
            try:
                if int(train.seq_length) <= int(gen_kwargs["max_new_tokens"]):
                    errors.append("train.seq_length must be greater than method.gen_kwargs.max_new_tokens.")
            except Exception as exc:
                warnings.append(f"Could not compare seq_length and max_new_tokens: {exc}")

    if train.minibatch_size:
        try:
            if int(train.batch_size) % int(train.minibatch_size) != 0:
                errors.append("train.minibatch_size must divide train.batch_size.")
        except Exception as exc:
            warnings.append(f"Could not validate minibatch_size: {exc}")

    if train.tracker not in ("wandb", "tensorboard", None):
        errors.append("train.tracker must be 'wandb', 'tensorboard', or None.")
    if train.checkpoint_interval <= 0:
        errors.append("train.checkpoint_interval must be positive.")
    if train.eval_interval <= 0:
        errors.append("train.eval_interval must be positive.")

    if model_arch == "seq2seq" and trainer_l == "acceleratesfttrainer":
        errors.append("AccelerateSFTTrainer is causal-only in trlX 0.7.0; seq2seq SFT is not implemented.")
    if model_arch == "seq2seq" and trainer_l == "acceleraterfttrainer":
        warnings.append("AccelerateRFTTrainer uses AutoModelForCausalLM; treat RFT as causal-only.")
    if model_arch == "seq2seq" and getattr(method, "num_value_layers_unfrozen", 0):
        errors.append("Seq2seq value heads do not support num_value_layers_unfrozen > 0.")

    if model.peft_config is not None and model.num_layers_unfrozen >= 0:
        warnings.append("model.num_layers_unfrozen is ignored when model.peft_config is set.")
    if section(model.model_extra_configs).get("load_in_8bit"):
        warnings.append("trlX PPO/ILQL wrappers reject load_in_8bit; use PEFT or smaller batches instead.")

    if optimizer.name not in {"adam", "adamw", "sgd", "adam_8bit_bnb", "adamw_8bit_bnb"}:
        errors.append(f"Unsupported optimizer name {optimizer.name!r}.")
    if optimizer.name in {"adam_8bit_bnb", "adamw_8bit_bnb"}:
        warnings.append(f"Optimizer {optimizer.name!r} requires bitsandbytes.")
    if scheduler.name not in {"cosine_annealing", "linear"}:
        errors.append(f"Unsupported scheduler name {scheduler.name!r}.")
    if train.rollout_logging_dir and trainer_l != "accelerateppotrainer":
        warnings.append("train.rollout_logging_dir is only used by AcceleratePPOTrainer.")
    if tokenizer.padding_side not in {"left", "right"}:
        errors.append("tokenizer.padding_side must be 'left' or 'right'.")
    if tokenizer.truncation_side not in {"left", "right"}:
        errors.append("tokenizer.truncation_side must be 'left' or 'right'.")

    return {"warnings": warnings, "errors": errors}


def summarize(config: Any, source: Dict[str, Any]) -> Dict[str, Any]:
    method_fields = section(config.method)
    gen_kwargs = method_fields.pop("gen_kwargs", None)
    gen_experience_kwargs = method_fields.pop("gen_experience_kwargs", None)
    return jsonable(
        {
            "source": source,
            "package": {"trlx_version": version("trlx")},
            "trainer": config.train.trainer,
            "pipeline": config.train.pipeline,
            "method": {
                "name": getattr(config.method, "name", None),
                "class": config.method.__class__.__name__,
                "fields": method_fields,
                "gen_kwargs": gen_kwargs,
                "gen_experience_kwargs": gen_experience_kwargs,
            },
            "model": section(config.model),
            "tokenizer": section(config.tokenizer),
            "optimizer": section(config.optimizer),
            "scheduler": section(config.scheduler),
            "train": section(config.train),
            "validation": validate(config),
        }
    )


def print_text(summary: Dict[str, Any]) -> None:
    print("trlX training config summary")
    print("=============================")
    print(f"source: {summary['source']}")
    print(f"trlx_version: {summary['package'].get('trlx_version') or 'unknown'}")
    print(f"trainer: {summary['trainer']}")
    print(f"pipeline: {summary['pipeline']}")
    print(f"method: {summary['method'].get('name')} ({summary['method'].get('class')})")
    print(f"model: {summary['model'].get('model_path')} [{summary['model'].get('model_arch_type')}]")
    print(f"tokenizer: {summary['tokenizer'].get('tokenizer_path')}")
    print(f"optimizer: {summary['optimizer'].get('name')} {summary['optimizer'].get('kwargs')}")
    print(f"scheduler: {summary['scheduler'].get('name')} {summary['scheduler'].get('kwargs')}")
    print("\ntrain fields:")
    for key in [
        "seq_length",
        "epochs",
        "total_steps",
        "batch_size",
        "minibatch_size",
        "checkpoint_interval",
        "eval_interval",
        "checkpoint_dir",
        "save_best",
        "save_optimizer",
        "resume_from_checkpoint",
        "tracker",
        "logging_dir",
        "project_name",
        "run_name",
        "entity_name",
        "group_name",
        "tags",
        "seed",
        "trainer_kwargs",
    ]:
        if key in summary["train"]:
            print(f"  {key}: {summary['train'][key]}")
    print("\nmethod generation:")
    print(f"  gen_kwargs: {summary['method'].get('gen_kwargs')}")
    if summary["method"].get("gen_experience_kwargs") is not None:
        print(f"  gen_experience_kwargs: {summary['method'].get('gen_experience_kwargs')}")
    method_fields = summary["method"].get("fields") or {}
    if method_fields:
        print("\nmethod fields:")
        for key, value in method_fields.items():
            if key != "name":
                print(f"  {key}: {value}")
    validation = summary["validation"]
    if validation["warnings"]:
        print("\nwarnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    if validation["errors"]:
        print("\nerrors:")
        for error in validation["errors"]:
            print(f"  - {error}")
    if not validation["warnings"] and not validation["errors"]:
        print("\nvalidation: no warnings or errors from static config inspection")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        # Suppress optional dependency import logs so --json remains valid.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            config, source = load_config(args)
        summary = summarize(config, source)
    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 1 if summary.get("validation", {}).get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
