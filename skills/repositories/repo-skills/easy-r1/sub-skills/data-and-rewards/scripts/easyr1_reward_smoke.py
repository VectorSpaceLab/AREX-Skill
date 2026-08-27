#!/usr/bin/env python3
"""Deterministic EasyR1 reward and dataset-row contract smoke checks.

Default behavior is safe and local: it runs synthetic checks for distilled
math, R1-V, DAPO, Android GUI, mixed text/image row shape, and the expected
failure when a reward score omits the required ``overall`` key.

Optionally pass ``--target module.py:function`` to validate a custom EasyR1
reward function without importing the original repository checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping


RewardInput = dict[str, Any]
Score = dict[str, Any]


class ContractError(AssertionError):
    """Raised when an EasyR1 data/reward contract is violated."""


def _normalize_text(value: Any) -> str:
    return str(value).strip().replace(" ", "")


def _extract_boxed(response: str) -> str:
    match = re.findall(r"\\boxed\{([^{}]*)\}", response)
    return match[-1].strip() if match else ""


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def math_compute_score(reward_inputs: list[RewardInput], format_weight: float = 0.1) -> list[Score]:
    """Small pure-Python approximation of the EasyR1 math reward contract."""
    pattern = re.compile(r"<think>.*</think>.*\\boxed\{.*\}.*", re.DOTALL)
    scores: list[Score] = []
    for item in reward_inputs:
        response = re.sub(r"\s*(<|>|/)\s*", r"\1", item["response"])
        format_score = 1.0 if re.fullmatch(pattern, response) else 0.0
        accuracy_score = 1.0 if _normalize_text(_extract_boxed(response)) == _normalize_text(item["ground_truth"]) else 0.0
        scores.append(
            {
                "overall": (1.0 - format_weight) * accuracy_score + format_weight * format_score,
                "format": format_score,
                "accuracy": accuracy_score,
            }
        )
    return scores


def r1v_compute_score(reward_input: RewardInput, format_weight: float = 0.5) -> Score:
    """Small pure-Python approximation of the EasyR1 R1-V reward contract."""
    response = reward_input["response"]
    pattern = re.compile(r"<think>.*?</think>\s*<answer>.*?</answer>", re.DOTALL)
    format_score = 1.0 if re.fullmatch(pattern, response) else 0.0
    match = re.search(r"<answer>(.*?)</answer>", response, flags=re.DOTALL)
    answer = match.group(1).strip() if match else response.strip()
    accuracy_score = 1.0 if _normalize_text(answer) == _normalize_text(reward_input["ground_truth"]) else 0.0
    return {
        "overall": (1.0 - format_weight) * accuracy_score + format_weight * format_score,
        "format": format_score,
        "accuracy": accuracy_score,
    }


DAPO_SUBSTITUTIONS = [
    ("an ", ""),
    ("a ", ""),
    (".$", "$"),
    ("\\$", ""),
    (r"\ ", ""),
    (" ", ""),
    ("mbox", "text"),
    (",\\text{and}", ","),
    ("\\text{and}", ","),
    ("\\text{m}", "\\text{}"),
]

DAPO_REMOVED = [
    "square",
    "ways",
    "integers",
    "dollars",
    "mph",
    "inches",
    "hours",
    "km",
    "units",
    "\\ldots",
    "points",
    "feet",
    "minutes",
    "digits",
    "cents",
    "degrees",
    "cm",
    "gm",
    "pounds",
    "meters",
    "meals",
    "edges",
    "students",
    "multiples",
    "\\text{s}",
    "\\text{.}",
    "\\text{}^2",
    "\\text{}^3",
    "\\text{}",
    r"\mathrm{th}",
    r"^\circ",
    r"^{\circ}",
    r"\;",
    r",\!",
    "{,}",
    '"',
    "\\dots",
]


def dapo_normalize_final_answer(final_answer: str) -> str:
    final_answer = final_answer.split("=")[-1]
    for before, after in DAPO_SUBSTITUTIONS:
        final_answer = final_answer.replace(before, after)
    for expr in DAPO_REMOVED:
        final_answer = final_answer.replace(expr, "")
    final_answer = re.sub(r"(.*?)(\$)(.*?)(\$)(.*)", "$\\3$", final_answer)
    final_answer = re.sub(r"(\\text\{)(.*?)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(\\textbf\{)(.*?)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(\\overline\{)(.*?)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(\\boxed\{)(.*)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(frac)([^{])(.)", "frac{\\2}{\\3}", final_answer)
    final_answer = re.sub(r"(sqrt)([^{])", "sqrt{\\2}", final_answer)
    final_answer = final_answer.replace("$", "")
    if final_answer.replace(",", "").isdigit():
        final_answer = final_answer.replace(",", "")
    return final_answer.strip()


def dapo_accuracy_reward(response: str, ground_truth: str) -> float:
    match = re.findall(r"(?i)Answer\s*:\s*([^\n]+)", response)
    answer = match[-1] if match else "[INVALID]"
    return 1.0 if dapo_normalize_final_answer(answer) == dapo_normalize_final_answer(ground_truth) else -1.0


def dapo_soft_overlong_punishment(response_length: int, max_response_length: int, overlong_buffer_length: int) -> float:
    if overlong_buffer_length <= 0:
        raise ContractError("overlong_buffer_length must be positive")
    expected_len = max_response_length - overlong_buffer_length
    if response_length <= expected_len:
        return 0.0
    if response_length <= max_response_length:
        return (expected_len - response_length) / overlong_buffer_length
    return -1.0


def dapo_compute_score(
    reward_inputs: list[RewardInput],
    max_response_length: int,
    overlong_buffer_length: int,
    overlong_penalty_factor: float,
) -> list[Score]:
    scores: list[Score] = []
    for item in reward_inputs:
        response = item["response"][-300:]
        accuracy = dapo_accuracy_reward(response, item["ground_truth"])
        overlong = dapo_soft_overlong_punishment(
            int(item["response_length"]), int(max_response_length), int(overlong_buffer_length)
        )
        scores.append(
            {
                "overall": accuracy + overlong * float(overlong_penalty_factor),
                "accuracy": accuracy,
                "overlong": overlong,
                "accuracy_normalized": 0.5 * (accuracy + 1.0),
            }
        )
    return scores


def android_extract_answer(response: str) -> str:
    response = response.strip()
    if response in {"0", "1", "2"}:
        return response
    match = re.search(r"[012]", response)
    return match.group(0) if match else ""


def android_compute_score(reward_inputs: list[RewardInput]) -> list[Score]:
    scores: list[Score] = []
    for item in reward_inputs:
        pred = android_extract_answer(str(item.get("response", "")))
        truth = str(item.get("ground_truth", "")).strip()
        accuracy = 1.0 if pred == truth else 0.0
        scores.append({"overall": accuracy, "accuracy": accuracy})
    return scores


def broken_missing_overall(reward_inputs: list[RewardInput]) -> list[Score]:
    return [{"accuracy": 1.0} for _ in reward_inputs]


def default_samples() -> list[RewardInput]:
    return [
        {
            "response": "<think>2 + 2 = 4</think> Therefore \\boxed{4}.",
            "response_length": 12,
            "ground_truth": "4",
        },
        {
            "response": "Answer: $5",
            "response_length": 15,
            "ground_truth": "4",
        },
    ]


def android_samples() -> list[RewardInput]:
    return [
        {"response": "1", "response_length": 1, "ground_truth": "1"},
        {"response": "The answer is 2", "response_length": 5, "ground_truth": "0"},
    ]


def r1v_sample() -> RewardInput:
    return {"response": "<think>read image</think><answer>48</answer>", "response_length": 8, "ground_truth": "48"}


def validate_score(score: Any, *, label: str, expect_keys: Iterable[str]) -> list[str]:
    warnings: list[str] = []
    if not isinstance(score, Mapping):
        raise ContractError(f"{label}: score must be a dict, got {type(score).__name__}")
    missing = [key for key in expect_keys if key and key not in score]
    if missing:
        raise ContractError(f"{label}: score missing required key(s): {', '.join(missing)}")
    if "overall" not in score:
        raise ContractError(f"{label}: score missing required key: overall")
    if not _is_finite_number(score["overall"]):
        raise ContractError(f"{label}: overall must be a finite number, got {score['overall']!r}")
    for key, value in score.items():
        if value is None and key != "overall":
            warnings.append(f"{label}: metric {key!r} is None; EasyR1 will append it to metrics as-is")
        elif not _is_finite_number(value):
            raise ContractError(f"{label}: metric {key!r} must be finite numeric or None, got {value!r}")
    return warnings


def validate_batch_result(result: Any, *, expected_len: int, label: str, expect_keys: Iterable[str]) -> list[str]:
    if not isinstance(result, list):
        raise ContractError(f"{label}: batch reward must return a list, got {type(result).__name__}")
    if len(result) != expected_len:
        raise ContractError(f"{label}: batch result length {len(result)} != input length {expected_len}")
    warnings: list[str] = []
    for idx, score in enumerate(result):
        warnings.extend(validate_score(score, label=f"{label}[{idx}]", expect_keys=expect_keys))
    return warnings


def validate_sequential_result(result: Any, *, label: str, expect_keys: Iterable[str]) -> list[str]:
    return validate_score(result, label=label, expect_keys=expect_keys)


def validate_reward_callable(
    fn: Callable[..., Any],
    *,
    mode: str,
    samples: list[RewardInput],
    kwargs: dict[str, Any],
    label: str,
    expect_keys: Iterable[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    if mode == "batch":
        result = fn(samples, **kwargs)
        warnings.extend(validate_batch_result(result, expected_len=len(samples), label=label, expect_keys=expect_keys))
        scores = result
    elif mode == "sequential":
        scores = []
        for idx, sample in enumerate(samples):
            result = fn(sample, **kwargs)
            warnings.extend(validate_sequential_result(result, label=f"{label}[{idx}]", expect_keys=expect_keys))
            scores.append(result)
    else:
        raise ContractError(f"{label}: unsupported mode {mode!r}")
    return {"name": label, "mode": mode, "status": "ok", "num_scores": len(scores), "warnings": warnings}


def validate_dataset_rows(
    rows: list[dict[str, Any]],
    *,
    prompt_key: str = "problem",
    answer_key: str = "answer",
    image_key: str = "images",
    video_key: str = "videos",
) -> None:
    for idx, row in enumerate(rows):
        prefix = f"row[{idx}]"
        if not isinstance(row, dict):
            raise ContractError(f"{prefix}: row must be a dict")
        if prompt_key not in row:
            raise ContractError(f"{prefix}: missing prompt key {prompt_key!r}")
        if answer_key not in row:
            raise ContractError(f"{prefix}: missing answer key {answer_key!r}")
        prompt = row[prompt_key]
        if not isinstance(prompt, str):
            raise ContractError(f"{prefix}: prompt must be a string")
        image_count = prompt.count("<image>")
        video_count = prompt.count("<video>")
        if image_count and video_count:
            raise ContractError(f"{prefix}: do not mix <image> and <video> placeholders in one row")
        if image_key in row:
            images = [] if row[image_key] is None else row[image_key]
            if not isinstance(images, list):
                raise ContractError(f"{prefix}: {image_key!r} must be a list when present")
            if len(images) != image_count:
                raise ContractError(
                    f"{prefix}: {image_count} <image> placeholder(s) but {len(images)} image item(s)"
                )
        elif image_count:
            raise ContractError(f"{prefix}: prompt has <image> but row has no {image_key!r} list")
        if video_key in row:
            videos = [] if row[video_key] is None else row[video_key]
            if not isinstance(videos, list):
                raise ContractError(f"{prefix}: {video_key!r} must be a list when present")
            if len(videos) != video_count:
                raise ContractError(
                    f"{prefix}: {video_count} <video> placeholder(s) but {len(videos)} video item(s)"
                )
        elif video_count:
            raise ContractError(f"{prefix}: prompt has <video> but row has no {video_key!r} list")


def run_mixed_rows_check() -> dict[str, Any]:
    good_rows = [
        {"problem": "Solve 2 + 2.", "images": [], "answer": "4"},
        {"problem": "<image>\nChoose the largest number.", "images": ["round_001.png"], "answer": "2"},
    ]
    bad_rows = [{"problem": "<image>\nMissing media item.", "images": [], "answer": "0"}]
    validate_dataset_rows(good_rows)
    try:
        validate_dataset_rows(bad_rows)
    except ContractError as exc:
        return {"name": "mixed-rows", "status": "ok", "caught_expected_error": str(exc)}
    raise ContractError("mixed-rows: expected placeholder/media mismatch was not caught")


def run_missing_overall_guard() -> dict[str, Any]:
    try:
        validate_reward_callable(
            broken_missing_overall,
            mode="batch",
            samples=default_samples()[:1],
            kwargs={},
            label="missing-overall-guard",
            expect_keys=["overall"],
        )
    except ContractError as exc:
        return {"name": "missing-overall-guard", "status": "ok", "caught_expected_error": str(exc)}
    raise ContractError("missing-overall-guard: expected missing-overall failure was not caught")


BUILTIN_ORDER = ["math", "r1v", "dapo", "android", "mixed-rows", "missing-overall-guard"]


def run_builtin(name: str) -> dict[str, Any]:
    if name == "math":
        return validate_reward_callable(
            math_compute_score,
            mode="batch",
            samples=default_samples(),
            kwargs={},
            label="math-batch",
            expect_keys=["overall", "format", "accuracy"],
        )
    if name == "r1v":
        return validate_reward_callable(
            r1v_compute_score,
            mode="sequential",
            samples=[r1v_sample()],
            kwargs={},
            label="r1v-sequential",
            expect_keys=["overall", "format", "accuracy"],
        )
    if name == "dapo":
        return validate_reward_callable(
            dapo_compute_score,
            mode="batch",
            samples=default_samples(),
            kwargs={"max_response_length": 16, "overlong_buffer_length": 4, "overlong_penalty_factor": 1.0},
            label="dapo-batch",
            expect_keys=["overall", "accuracy", "overlong", "accuracy_normalized"],
        )
    if name == "android":
        return validate_reward_callable(
            android_compute_score,
            mode="batch",
            samples=android_samples(),
            kwargs={},
            label="android-batch",
            expect_keys=["overall", "accuracy"],
        )
    if name == "mixed-rows":
        return run_mixed_rows_check()
    if name == "missing-overall-guard":
        return run_missing_overall_guard()
    raise ContractError(f"unknown builtin check {name!r}; choose from {', '.join(BUILTIN_ORDER)}")


def parse_builtins(value: str) -> list[str]:
    value = value.strip()
    if value in {"", "none", "no"}:
        return []
    if value == "all":
        return BUILTIN_ORDER[:]
    names = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [name for name in names if name not in BUILTIN_ORDER]
    if unknown:
        raise ContractError(f"unknown builtin(s): {', '.join(unknown)}; choose from {', '.join(BUILTIN_ORDER)}")
    return names


def load_json_arg(value: str, *, default: Any) -> Any:
    if value is None:
        return default
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def load_target(target: str) -> tuple[ModuleType, Callable[..., Any], str, str]:
    if ":" in target:
        path_text, func_name = target.rsplit(":", maxsplit=1)
    else:
        path_text, func_name = target, "main"
    path = Path(path_text).expanduser()
    if not path.exists():
        raise ContractError(f"target module does not exist: {path}")
    spec = importlib.util.spec_from_file_location("easyr1_custom_reward", str(path))
    if spec is None or spec.loader is None:
        raise ContractError(f"could not create import spec for target module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["easyr1_custom_reward"] = module
    spec.loader.exec_module(module)
    if not hasattr(module, func_name):
        raise ContractError(f"target module has no function {func_name!r}")
    fn = getattr(module, func_name)
    if not callable(fn):
        raise ContractError(f"target attribute {func_name!r} is not callable")
    reward_type = str(getattr(module, "REWARD_TYPE", "batch"))
    return module, fn, func_name, reward_type


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic EasyR1 reward and dataset-row contract smoke checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--builtins",
        default="all",
        help="Comma-separated builtin checks to run, 'all', or 'none'. Builtins: " + ", ".join(BUILTIN_ORDER),
    )
    parser.add_argument("--list-builtins", action="store_true", help="Print builtin check names and exit.")
    parser.add_argument(
        "--target",
        help="Optional custom reward target as module.py:function. If ':function' is omitted, 'main' is used.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "batch", "sequential"],
        default="auto",
        help="Custom target call mode. Auto uses module REWARD_TYPE or defaults to batch.",
    )
    parser.add_argument(
        "--samples-json",
        help="JSON list of reward input dicts, JSON dict for one sample, or @file. Defaults to synthetic samples.",
    )
    parser.add_argument(
        "--kwargs-json",
        default="{}",
        help="JSON kwargs passed to the custom reward function, or @file.",
    )
    parser.add_argument(
        "--expect-keys",
        default="overall",
        help="Comma-separated score keys required for a custom target. 'overall' is always required.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures; suppress success JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_builtins:
        print("\n".join(BUILTIN_ORDER))
        return 0

    try:
        checks: list[dict[str, Any]] = []
        for name in parse_builtins(args.builtins):
            checks.append(run_builtin(name))

        if args.target:
            module, fn, func_name, module_reward_type = load_target(args.target)
            mode = module_reward_type if args.mode == "auto" else args.mode
            if mode not in {"batch", "sequential"}:
                raise ContractError(f"custom target REWARD_TYPE must be 'batch' or 'sequential', got {mode!r}")
            kwargs = load_json_arg(args.kwargs_json, default={})
            if not isinstance(kwargs, dict):
                raise ContractError("--kwargs-json must decode to a JSON object")
            samples_obj = load_json_arg(args.samples_json, default=default_samples()) if args.samples_json else default_samples()
            if isinstance(samples_obj, dict):
                samples = [samples_obj]
            elif isinstance(samples_obj, list) and all(isinstance(item, dict) for item in samples_obj):
                samples = samples_obj
            else:
                raise ContractError("--samples-json must decode to a reward input dict or a list of dicts")
            expect_keys = [item.strip() for item in args.expect_keys.split(",") if item.strip()]
            if "overall" not in expect_keys:
                expect_keys.insert(0, "overall")
            reward_name = getattr(module, "REWARD_NAME", "unknown")
            custom_check = validate_reward_callable(
                fn,
                mode=mode,
                samples=samples,
                kwargs=kwargs,
                label=f"custom:{func_name}",
                expect_keys=expect_keys,
            )
            custom_check["reward_name"] = reward_name
            custom_check["declared_reward_type"] = module_reward_type
            checks.append(custom_check)

        summary = {"status": "ok", "checks": checks}
        if not args.quiet:
            print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should return concise JSON for all failures.
        failure = {"status": "failed", "error_type": exc.__class__.__name__, "error": str(exc)}
        print(json.dumps(failure, indent=2, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
