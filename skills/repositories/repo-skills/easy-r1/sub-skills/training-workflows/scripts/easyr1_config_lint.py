#!/usr/bin/env python3
"""Static linter for EasyR1 training YAML files.

The linter is deterministic and safe by default: it parses YAML and checks
configuration structure, selected enum values, batching constraints, DAPO-style
online filtering settings, LoRA/VL warnings, and full-training runtime caveats.
It does not import EasyR1, start Ray, allocate GPUs, download assets, or touch
checkpoints.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised only when PyYAML is absent
    yaml = None


MISSING = object()

TOP_LEVEL = {"data", "algorithm", "worker", "trainer"}
ADV_ESTIMATORS = {"gae", "grpo", "grpo_passk", "reinforce_plus_plus", "remax", "rloo"}
KL_PENALTIES = {"kl", "abs", "mse", "low_var_kl", "full"}
KL_TYPES = {"fixed", "adaptive"}
LOSS_TYPES = {"default", "gspo", "gspo_token", "cispo", "sapo"}
LOSS_AVG_MODES = {"token", "seq"}
OPTIM_STRATEGIES = {"adamw", "adamw_bf16"}
LR_SCHEDULERS = {"constant", "cosine"}
LOGGER_TYPES = {"console", "file", "mlflow", "swanlab", "tensorboard", "wandb"}
ROLLOUT_NAMES = {"vllm"}


@dataclass
class Issue:
    severity: str
    path: str
    message: str
    hint: str = ""

    def as_dict(self) -> dict[str, str]:
        data = {"severity": self.severity, "path": self.path, "message": self.message}
        if self.hint:
            data["hint"] = self.hint
        return data


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically lint an EasyR1 YAML config without importing EasyR1 or starting training."
    )
    parser.add_argument("config", type=Path, help="Path to an EasyR1-style YAML config file.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on warnings as well as errors. By default only errors fail.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--no-runtime-warning",
        action="store_true",
        help="Suppress the standard reminder that static lint does not prove full CUDA/Ray/vLLM training.",
    )
    return parser.parse_args(argv)


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is required to parse YAML configs. Install pyyaml or run inside the EasyR1 runtime.")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def get(mapping: Any, dotted: str, default: Any = MISSING) -> Any:
    cur = mapping
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def has(mapping: Any, dotted: str) -> bool:
    return get(mapping, dotted, MISSING) is not MISSING


def add(issues: list[Issue], severity: str, path: str, message: str, hint: str = "") -> None:
    issues.append(Issue(severity=severity.upper(), path=path, message=message, hint=hint))


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"[-+]?\d+", text):
            return int(text)
    return None


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    if isinstance(value, str):
        try:
            numeric = float(value.strip())
        except ValueError:
            return None
        return numeric if math.isfinite(numeric) else None
    return None


def as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "on"}:
            return True
        if lowered in {"false", "no", "0", "off"}:
            return False
    return None


def parse_logger_list(value: Any) -> list[str] | None:
    if value is MISSING:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)
            except Exception:
                return [value]
            if isinstance(parsed, (list, tuple)):
                return [str(item) for item in parsed]
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return None


def check_enum(
    cfg: dict[str, Any],
    issues: list[Issue],
    path: str,
    valid: set[str],
    *,
    missing_ok: bool = True,
    label: str | None = None,
) -> None:
    value = get(cfg, path, MISSING)
    if value is MISSING:
        if not missing_ok:
            add(issues, "WARN", path, f"Missing {label or path}; EasyR1 will use its dataclass default.")
        return
    if not isinstance(value, str):
        add(issues, "ERROR", path, f"Expected a string value for {label or path}.")
        return
    if value not in valid:
        add(issues, "ERROR", path, f"Unsupported value {value!r}.", f"Use one of: {', '.join(sorted(valid))}.")


def looks_like_vl_model(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in ("-vl", "_vl", "vl-", "qwen2.5-vl", "qwen3-vl", "vision"))


def validate(cfg: dict[str, Any], *, include_runtime_warning: bool) -> list[Issue]:
    issues: list[Issue] = []

    if include_runtime_warning:
        add(
            issues,
            "WARN",
            "runtime",
            "Static lint does not prove full EasyR1 training.",
            "Full training needs CUDA GPUs plus Ray, vLLM, flash-attn, compatible PyTorch/CUDA, model weights, dataset access, and enough GPU memory.",
        )

    for key in TOP_LEVEL:
        if key not in cfg:
            add(issues, "WARN", key, "Missing top-level section; dataclass defaults may fill it, but production configs should be explicit.")

    for key in sorted(set(cfg) - TOP_LEVEL):
        add(issues, "ERROR", key, "Unknown top-level section for EasyR1 PPOConfig.", "Expected only data, algorithm, worker, and trainer.")

    check_enum(cfg, issues, "algorithm.adv_estimator", ADV_ESTIMATORS, label="advantage estimator")
    check_enum(cfg, issues, "algorithm.kl_penalty", KL_PENALTIES, label="KL penalty")
    check_enum(cfg, issues, "algorithm.kl_type", KL_TYPES, label="KL controller type")
    check_enum(cfg, issues, "worker.actor.loss_type", LOSS_TYPES, label="actor loss type")
    check_enum(cfg, issues, "worker.actor.loss_avg_mode", LOSS_AVG_MODES, label="actor loss averaging mode")
    check_enum(cfg, issues, "worker.critic.loss_avg_mode", LOSS_AVG_MODES, label="critic loss averaging mode")
    check_enum(cfg, issues, "worker.actor.optim.strategy", OPTIM_STRATEGIES, label="actor optimizer strategy")
    check_enum(cfg, issues, "worker.critic.optim.strategy", OPTIM_STRATEGIES, label="critic optimizer strategy")
    check_enum(cfg, issues, "worker.actor.optim.lr_scheduler_type", LR_SCHEDULERS, label="actor LR scheduler")
    check_enum(cfg, issues, "worker.critic.optim.lr_scheduler_type", LR_SCHEDULERS, label="critic LR scheduler")
    check_enum(cfg, issues, "worker.rollout.name", ROLLOUT_NAMES, label="rollout backend")

    logger_value = get(cfg, "trainer.logger", MISSING)
    loggers = parse_logger_list(logger_value)
    if logger_value is not MISSING and loggers is None:
        add(issues, "ERROR", "trainer.logger", "Expected a logger string or list of logger strings.")
    elif loggers:
        for logger in loggers:
            if logger not in LOGGER_TYPES:
                add(issues, "ERROR", "trainer.logger", f"Unsupported logger {logger!r}.", f"Use one or more of: {', '.join(sorted(LOGGER_TYPES))}.")

    adv = get(cfg, "algorithm.adv_estimator", "grpo")
    rollout_n = as_int(get(cfg, "worker.rollout.n", 1))
    if adv in {"grpo", "grpo_passk", "rloo"} and rollout_n is not None and rollout_n <= 1:
        add(issues, "ERROR", "worker.rollout.n", f"{adv} requires grouped rollouts.", "Set worker.rollout.n > 1.")

    rollout_batch_size = as_int(get(cfg, "data.rollout_batch_size", MISSING))
    actor_global_batch = as_int(get(cfg, "worker.actor.global_batch_size", MISSING))
    actor_micro_experience = as_int(get(cfg, "worker.actor.micro_batch_size_per_device_for_experience", MISSING))
    critic_global_batch = as_int(get(cfg, "worker.critic.global_batch_size", MISSING))
    critic_micro_experience = as_int(get(cfg, "worker.critic.micro_batch_size_per_device_for_experience", MISSING))

    if rollout_batch_size is not None and actor_global_batch is not None and actor_global_batch > 0:
        if rollout_batch_size % actor_global_batch != 0:
            add(issues, "ERROR", "data.rollout_batch_size", "Rollout batch size must be divisible by actor global batch size.")

    if rollout_batch_size is not None and rollout_n is not None and actor_micro_experience is not None and actor_micro_experience > 0:
        if (rollout_batch_size * rollout_n) % actor_micro_experience != 0:
            add(
                issues,
                "ERROR",
                "worker.actor.micro_batch_size_per_device_for_experience",
                "data.rollout_batch_size * worker.rollout.n must be divisible by actor experience micro-batch size.",
            )

    if adv == "gae":
        if rollout_batch_size is not None and critic_global_batch is not None and critic_global_batch > 0:
            if rollout_batch_size % critic_global_batch != 0:
                add(issues, "ERROR", "worker.critic.global_batch_size", "GAE uses a critic, so rollout batch size must be divisible by critic global batch size.")
        if rollout_batch_size is not None and rollout_n is not None and critic_micro_experience is not None and critic_micro_experience > 0:
            if (rollout_batch_size * rollout_n) % critic_micro_experience != 0:
                add(
                    issues,
                    "ERROR",
                    "worker.critic.micro_batch_size_per_device_for_experience",
                    "GAE uses a critic, so rollout_batch_size * rollout.n must be divisible by critic experience micro-batch size.",
                )

    nnodes = as_int(get(cfg, "trainer.nnodes", 1))
    gpus_per_node = as_int(get(cfg, "trainer.n_gpus_per_node", 8))
    tensor_parallel_size = as_int(get(cfg, "worker.rollout.tensor_parallel_size", 1))
    if nnodes is not None and nnodes <= 0:
        add(issues, "ERROR", "trainer.nnodes", "Number of nodes must be positive.")
    if gpus_per_node is not None and gpus_per_node <= 0:
        add(issues, "ERROR", "trainer.n_gpus_per_node", "GPUs per node must be positive for full training.")
    if tensor_parallel_size is not None and tensor_parallel_size <= 0:
        add(issues, "ERROR", "worker.rollout.tensor_parallel_size", "Tensor parallel size must be positive.")
    if all(x is not None and x > 0 for x in (nnodes, gpus_per_node, tensor_parallel_size)):
        world_size = nnodes * gpus_per_node  # type: ignore[operator]
        if tensor_parallel_size > world_size:  # type: ignore[operator]
            add(issues, "ERROR", "worker.rollout.tensor_parallel_size", "Tensor parallel size exceeds configured world size.")
        elif world_size % tensor_parallel_size != 0:  # type: ignore[operator]
            add(issues, "ERROR", "worker.rollout.tensor_parallel_size", "Tensor parallel size must divide nnodes * n_gpus_per_node.")

    max_prompt = as_int(get(cfg, "data.max_prompt_length", MISSING))
    max_response = as_int(get(cfg, "data.max_response_length", MISSING))
    max_batched = as_int(get(cfg, "worker.rollout.max_num_batched_tokens", MISSING))
    if max_prompt is not None and max_response is not None and max_batched is not None:
        required = max_prompt + max_response
        if max_batched <= required:
            add(
                issues,
                "ERROR",
                "worker.rollout.max_num_batched_tokens",
                "vLLM requires max_num_batched_tokens greater than max_prompt_length + max_response_length.",
                f"Set it above {required}.",
            )

    online_filtering = as_bool(get(cfg, "algorithm.online_filtering", False))
    if online_filtering:
        filter_key = get(cfg, "algorithm.filter_key", "")
        if not isinstance(filter_key, str) or not filter_key.strip():
            add(issues, "ERROR", "algorithm.filter_key", "Online filtering needs a non-empty reward metric key.")
        low = as_float(get(cfg, "algorithm.filter_low", MISSING))
        high = as_float(get(cfg, "algorithm.filter_high", MISSING))
        if low is not None and high is not None and not low < high:
            add(issues, "ERROR", "algorithm.filter_low", "Online filter lower bound must be below upper bound.")
        max_try = as_int(get(cfg, "trainer.max_try_make_batch", 20))
        if max_try is not None and max_try <= 0:
            add(issues, "WARN", "trainer.max_try_make_batch", "Online filtering can regenerate indefinitely when max_try_make_batch <= 0.")
        if get(cfg, "data.mini_rollout_batch_size", MISSING) is MISSING:
            add(issues, "WARN", "data.mini_rollout_batch_size", "DAPO-style online filtering often uses a smaller mini rollout batch size.")
        reward_kwargs = get(cfg, "worker.reward.reward_function_kwargs", {})
        if isinstance(reward_kwargs, dict):
            kw_max_response = as_int(reward_kwargs.get("max_response_length", MISSING))
            if kw_max_response is not None and max_response is not None and kw_max_response != max_response:
                add(
                    issues,
                    "WARN",
                    "worker.reward.reward_function_kwargs.max_response_length",
                    "Reward kwargs max_response_length differs from data.max_response_length.",
                    "This is sometimes intentional, but DAPO overlong penalties usually expect matching lengths.",
                )

    lora_rank = as_int(get(cfg, "worker.actor.model.lora.rank", 0))
    model_path = get(cfg, "worker.actor.model.model_path", "")
    if lora_rank is not None and lora_rank > 0:
        lora_alpha = as_int(get(cfg, "worker.actor.model.lora.alpha", 64))
        if lora_alpha is not None and lora_alpha <= 0:
            add(issues, "ERROR", "worker.actor.model.lora.alpha", "LoRA alpha must be positive when LoRA is enabled.")
        target_modules = get(cfg, "worker.actor.model.lora.target_modules", "all-linear")
        exclude_modules = get(cfg, "worker.actor.model.lora.exclude_modules", None)
        if not isinstance(target_modules, str):
            add(issues, "ERROR", "worker.actor.model.lora.target_modules", "LoRA target_modules must be a string.")
        if exclude_modules is not None and not isinstance(exclude_modules, str):
            add(issues, "ERROR", "worker.actor.model.lora.exclude_modules", "LoRA exclude_modules must be a string or null.")
        if looks_like_vl_model(model_path):
            if not isinstance(exclude_modules, str) or "visual" not in exclude_modules.lower():
                add(
                    issues,
                    "WARN",
                    "worker.actor.model.lora.exclude_modules",
                    "VL LoRA launch should exclude the vision tower.",
                    "Use a pattern such as .*visual.* because vLLM does not support ViT LoRA in the distilled EasyR1 evidence.",
                )
        if tensor_parallel_size is not None and tensor_parallel_size > 1:
            add(
                issues,
                "WARN",
                "worker.rollout.tensor_parallel_size",
                "LoRA examples use conservative tensor_parallel_size=1.",
                "Verify vLLM LoRA compatibility before using higher tensor parallelism.",
            )

    ulysses_size = as_int(get(cfg, "worker.actor.ulysses_size", 1))
    if ulysses_size is not None and ulysses_size > 1 and looks_like_vl_model(model_path):
        add(
            issues,
            "WARN",
            "worker.actor.ulysses_size",
            "EasyR1 documents VLM incompatibility with Ulysses parallelism.",
            "Use ulysses_size=1 for VL models unless the runtime has a verified fix.",
        )

    loss_type = get(cfg, "worker.actor.loss_type", "default")
    loss_avg_mode = get(cfg, "worker.actor.loss_avg_mode", "token")
    if loss_type == "gspo_token" and loss_avg_mode != "seq":
        add(issues, "WARN", "worker.actor.loss_avg_mode", "GSPO token recipes commonly use sequence averaging.", "Set worker.actor.loss_avg_mode=seq unless intentionally experimenting.")

    return issues


def print_text(path: Path, issues: list[Issue], *, strict: bool) -> None:
    print(f"EasyR1 config lint: {path}")
    if not issues:
        print("OK: no issues found.")
        return
    for issue in issues:
        location = f" [{issue.path}]" if issue.path else ""
        print(f"{issue.severity}{location}: {issue.message}")
        if issue.hint:
            print(f"  hint: {issue.hint}")
    errors = sum(1 for issue in issues if issue.severity == "ERROR")
    warnings = sum(1 for issue in issues if issue.severity == "WARN")
    status = "FAIL" if errors or (strict and warnings) else "OK"
    print(f"{status}: {errors} error(s), {warnings} warning(s).")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        loaded = load_yaml(args.config)
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "errors": [{"message": str(exc)}]}, indent=2))
        else:
            print(f"ERROR: could not load config: {exc}", file=sys.stderr)
        return 1

    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        message = "Top-level YAML document must be a mapping."
        if args.json:
            print(json.dumps({"status": "FAIL", "errors": [{"message": message}]}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    issues = validate(loaded, include_runtime_warning=not args.no_runtime_warning)
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    warnings = [issue for issue in issues if issue.severity == "WARN"]
    exit_code = 1 if errors or (args.strict and warnings) else 0

    if args.json:
        print(
            json.dumps(
                {
                    "status": "FAIL" if exit_code else "OK",
                    "config": str(args.config),
                    "strict": bool(args.strict),
                    "errorCount": len(errors),
                    "warningCount": len(warnings),
                    "issues": [issue.as_dict() for issue in issues],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(args.config, issues, strict=args.strict)

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
