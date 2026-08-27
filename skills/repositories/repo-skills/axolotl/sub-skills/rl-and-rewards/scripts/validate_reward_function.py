#!/usr/bin/env python3
"""Safely validate the shape of a local Axolotl GRPO reward function."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import math
import numbers
import sys
import traceback
from pathlib import Path
from typing import Any

SAMPLE_TEXTS = [
    "<think>2 + 2 = 4</think><answer>4</answer>",
    "Reasoning complete. Final answer: 7",
]
SAMPLE_PROMPTS = [
    [{"role": "user", "content": "What is 2 + 2?"}],
    [{"role": "user", "content": "Return the number seven."}],
]


class ValidationError(Exception):
    """A user-facing validation error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import a reward function from a local Python file and verify that it "
            "returns one finite numeric reward per tiny sample completion."
        )
    )
    parser.add_argument(
        "target",
        help="Local target in the form path/to/rewards.py:function_name",
    )
    parser.add_argument(
        "--completion-style",
        choices=("messages", "strings"),
        default="messages",
        help="Pass completions as chat-message lists or plain strings (default: messages).",
    )
    parser.add_argument(
        "--answer",
        action="append",
        dest="answers",
        help="Gold answer value. May be repeated; defaults to two tiny answers.",
    )
    parser.add_argument(
        "--extra-json",
        default="{}",
        help="Extra keyword data as a JSON object, for example '{\"difficulty\": [\"easy\", \"hard\"]}'.",
    )
    parser.add_argument(
        "--allow-none",
        action="store_true",
        help="Allow None reward elements for trainer paths that intentionally drop samples.",
    )
    parser.add_argument(
        "--allow-nondeterministic",
        action="store_true",
        help="Do not fail if two identical calls return different values.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human summary.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Show a Python traceback when the reward function raises.",
    )
    return parser.parse_args()


def load_target(target: str) -> tuple[Path, Any]:
    if ":" not in target:
        raise ValidationError("Target must use the form path/to/rewards.py:function_name")

    file_part, func_name = target.rsplit(":", 1)
    if not file_part or not func_name:
        raise ValidationError("Target must include both a Python file and a function name")

    file_path = Path(file_part).expanduser()
    if not file_path.exists():
        raise ValidationError(f"Reward file does not exist: {file_path}")
    if not file_path.is_file():
        raise ValidationError(f"Reward target is not a file: {file_path}")
    if file_path.suffix != ".py":
        raise ValidationError(f"Reward file must end in .py: {file_path}")

    module_name = f"_axolotl_reward_check_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"Could not import Python file: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(file_path.parent.resolve()))
    try:
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(file_path.parent.resolve()))
        except ValueError:
            pass

    reward_func = getattr(module, func_name, None)
    if reward_func is None:
        raise ValidationError(f"Function {func_name!r} was not found in {file_path}")
    if not callable(reward_func):
        raise ValidationError(f"Target {func_name!r} exists but is not callable")
    return file_path, reward_func


def build_samples(args: argparse.Namespace) -> dict[str, Any]:
    completions: list[Any]
    if args.completion_style == "messages":
        completions = [[{"role": "assistant", "content": text}] for text in SAMPLE_TEXTS]
    else:
        completions = list(SAMPLE_TEXTS)

    answers = args.answers or ["4", "7"]
    if len(answers) == 1:
        answers = answers * len(SAMPLE_TEXTS)
    if len(answers) != len(SAMPLE_TEXTS):
        raise ValidationError(
            f"Expected 1 or {len(SAMPLE_TEXTS)} --answer values, got {len(answers)}"
        )

    try:
        extra = json.loads(args.extra_json)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"--extra-json is not valid JSON: {exc}") from exc
    if not isinstance(extra, dict):
        raise ValidationError("--extra-json must decode to a JSON object")

    sample_data = {
        "prompts": SAMPLE_PROMPTS,
        "completions": completions,
        "answer": answers,
        "answers": answers,
    }
    sample_data.update(extra)
    return sample_data


def call_reward(reward_func: Any, sample_data: dict[str, Any]) -> Any:
    signature = inspect.signature(reward_func)
    parameters = signature.parameters
    accepts_kwargs = any(
        param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values()
    )

    positional_args: list[Any] = []
    keyword_args: dict[str, Any] = {}
    missing_required: list[str] = []

    for name, param in parameters.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            continue

        if name in sample_data:
            if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                positional_args.append(sample_data[name])
            else:
                keyword_args[name] = sample_data[name]
        elif param.default is inspect.Parameter.empty:
            missing_required.append(name)

    if accepts_kwargs:
        for key, value in sample_data.items():
            keyword_args.setdefault(key, value)

    if missing_required:
        available = ", ".join(sorted(sample_data))
        missing = ", ".join(missing_required)
        raise ValidationError(
            f"Cannot satisfy required parameter(s): {missing}. Available sample keys: {available}. "
            "Use --extra-json to provide additional keyword data."
        )

    return reward_func(*positional_args, **keyword_args)


def validate_rewards(result: Any, expected_len: int, allow_none: bool) -> list[float | None]:
    if isinstance(result, (str, bytes)) or not isinstance(result, (list, tuple)):
        raise ValidationError(
            f"Reward function must return a list or tuple, got {type(result).__name__}"
        )
    if len(result) != expected_len:
        raise ValidationError(
            f"Reward function returned {len(result)} value(s), expected {expected_len}"
        )

    normalized: list[float | None] = []
    for index, value in enumerate(result):
        if value is None:
            if allow_none:
                normalized.append(None)
                continue
            raise ValidationError(
                f"Reward value at index {index} is None; pass --allow-none only if this trainer path supports it"
            )
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValidationError(
                f"Reward value at index {index} must be a finite int or float, got {type(value).__name__}"
            )
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise ValidationError(f"Reward value at index {index} is not finite: {value!r}")
        normalized.append(numeric_value)
    return normalized


def emit(args: argparse.Namespace, payload: dict[str, Any], exit_code: int) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    status = "OK" if exit_code == 0 else "ERROR"
    print(f"{status}: {payload['message']}")
    if "target" in payload:
        print(f"target: {payload['target']}")
    if "rewards" in payload:
        print(f"rewards: {payload['rewards']}")


def main() -> int:
    args = parse_args()
    try:
        file_path, reward_func = load_target(args.target)
        sample_data = build_samples(args)
        expected_len = len(sample_data["completions"])

        first = validate_rewards(
            call_reward(reward_func, sample_data), expected_len, args.allow_none
        )
        second = validate_rewards(
            call_reward(reward_func, sample_data), expected_len, args.allow_none
        )

        if first != second and not args.allow_nondeterministic:
            raise ValidationError(
                "Reward function returned different values on identical inputs; remove randomness or pass --allow-nondeterministic"
            )

        emit(
            args,
            {
                "ok": True,
                "message": "reward function returned one finite reward per sample",
                "target": f"{file_path}:{reward_func.__name__}",
                "completion_style": args.completion_style,
                "rewards": first,
            },
            0,
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - user-facing CLI boundary
        if args.show_traceback:
            traceback.print_exc()
        emit(
            args,
            {
                "ok": False,
                "message": str(exc),
                "error_type": type(exc).__name__,
            },
            1,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
