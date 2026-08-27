#!/usr/bin/env python3
"""Validate a DiscoArt config and optional prompt planner without generation.

The helper intentionally avoids calling discoart.create(), starting servers,
writing outputs, downloading models, or making network calls. It imports the
DiscoArt config/prompt modules only after parsing CLI args, so --help remains
available even in an environment where DiscoArt is not installed.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Tuple

SCHEDULE_FIELDS: Tuple[str, ...] = (
    "cut_overview",
    "cut_innercut",
    "cut_icgray_p",
    "cut_ic_pow",
    "use_secondary_model",
    "cutn_batches",
    "clip_guidance_scale",
    "tv_scale",
    "range_scale",
    "sat_scale",
    "init_scale",
    "clamp_grad",
    "clamp_max",
)


class _FakeUrlOpenResponse(io.BytesIO):
    """Small context-manager response used to block import-time URL access."""

    def __init__(self) -> None:
        # Satisfy discoart.helper._version_check without reaching PyPI.
        super().__init__(b'{"releases":{"0.0.0":[]}}')

    def __enter__(self) -> "_FakeUrlOpenResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False


class _DiscoArtModules(SimpleNamespace):
    load_config: Any
    default_args: Dict[str, Any]
    eval_schedule: Any
    PromptPlanner: Any
    max_steps: int


def _fake_urlopen(*args, **kwargs) -> _FakeUrlOpenResponse:
    return _FakeUrlOpenResponse()


def _import_discoart_modules() -> _DiscoArtModules:
    """Import required DiscoArt helpers while preventing network access."""

    os.environ.setdefault("DISCOART_DISABLE_REMOTE_MODELS", "1")
    os.environ.setdefault("DISCOART_DISABLE_IPYTHON", "1")

    old_urlopen = urllib.request.urlopen
    urllib.request.urlopen = _fake_urlopen
    try:
        from discoart.config import default_args, load_config  # type: ignore
        from discoart.helper import (  # type: ignore
            _MAX_DIFFUSION_STEPS,
            _eval_scheduling_str,
        )
        from discoart.prompt import PromptPlanner  # type: ignore
    finally:
        urllib.request.urlopen = old_urlopen

    return _DiscoArtModules(
        load_config=load_config,
        default_args=default_args,
        eval_schedule=_eval_scheduling_str,
        PromptPlanner=PromptPlanner,
        max_steps=int(_MAX_DIFFUSION_STEPS),
    )


def _parse_steps(raw: str, max_steps: int) -> Tuple[List[int], List[str]]:
    steps: List[int] = []
    warnings: List[str] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            step = int(chunk)
        except ValueError:
            warnings.append(f"ignored non-integer prompt step {chunk!r}")
            continue
        if not 0 <= step < max_steps:
            warnings.append(
                f"ignored prompt step {step}; valid internal steps are 0..{max_steps - 1}"
            )
            continue
        steps.append(step)
    if not steps:
        steps = [0, max_steps // 2, max_steps - 1]
    return sorted(dict.fromkeys(steps)), warnings


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return repr(value)


def _summarize_schedule(values: Iterable[Any]) -> Dict[str, Any]:
    seq = list(values)
    transitions = 0
    last = object()
    for item in seq:
        if item != last:
            transitions += 1
            last = item
    return {
        "length": len(seq),
        "first": _jsonable(seq[:5]),
        "last": _jsonable(seq[-5:]),
        "truthy_count": sum(bool(v) for v in seq),
        "transition_count": transitions,
    }


def _validate_schedules(cfg: Dict[str, Any], modules: _DiscoArtModules) -> Tuple[Dict[str, Any], List[str], List[str]]:
    schedules: Dict[str, Any] = {}
    warnings: List[str] = []
    errors: List[str] = []

    for field in SCHEDULE_FIELDS:
        if field not in cfg:
            continue
        try:
            expanded = modules.eval_schedule(cfg[field])
            schedules[field] = _summarize_schedule(expanded)
        except Exception as exc:  # noqa: BLE001 - safe user-facing error collection
            errors.append(f"{field}: {type(exc).__name__}: {exc}")

    clip_model_names = set(cfg.get("clip_models") or [])
    clip_schedules = cfg.get("clip_models_schedules")
    if clip_schedules:
        if not isinstance(clip_schedules, dict):
            errors.append(
                "clip_models_schedules: expected a mapping from CLIP model name to schedule"
            )
        else:
            schedules["clip_models_schedules"] = {}
            for model_name, schedule in sorted(clip_schedules.items()):
                if model_name not in clip_model_names:
                    warnings.append(
                        f"clip_models_schedules[{model_name!r}] is ignored unless the model is also in clip_models"
                    )
                try:
                    expanded = modules.eval_schedule(schedule)
                    schedules["clip_models_schedules"][model_name] = _summarize_schedule(
                        expanded
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(
                        f"clip_models_schedules[{model_name!r}]: {type(exc).__name__}: {exc}"
                    )

    return schedules, warnings, errors


def _non_defaults(cfg: Dict[str, Any], default_args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: _jsonable(value)
        for key, value in sorted(cfg.items())
        if not str(key).startswith("_") and default_args.get(key) != value
    }


def _prompt_schema_hints(cfg: Dict[str, Any]) -> List[str]:
    hints: List[str] = []
    prompts = cfg.get("text_prompts")
    if isinstance(prompts, dict):
        version = prompts.get("version")
        if version != "1":
            hints.append(
                "text_prompts.version should be the string '1' for this runtime; quote it in YAML as version: \"1\""
            )
        if "prompts" not in prompts:
            hints.append("text_prompts schema v1 requires a prompts list")
        elif not prompts.get("prompts"):
            hints.append("text_prompts.prompts is empty; PromptPlanner requires at least one prompt")
    return hints


def _check_prompts(
    cfg: Dict[str, Any],
    modules: _DiscoArtModules,
    requested_steps: List[int],
    requested_clip_models: List[str] | None,
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = _prompt_schema_hints(cfg)
    errors: List[str] = []
    report: Dict[str, Any] = {}

    try:
        planner = modules.PromptPlanner(SimpleNamespace(**cfg))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"PromptPlanner: {type(exc).__name__}: {exc}")
        return report, warnings, errors

    configured_clips = list(cfg.get("clip_models") or [])
    clip_models = requested_clip_models or configured_clips[:1]
    if not clip_models and configured_clips:
        clip_models = [configured_clips[0]]

    configured_clip_set = set(configured_clips)
    for model_name in clip_models:
        if model_name not in configured_clip_set:
            warnings.append(
                f"requested --clip-model {model_name!r} is not present in clip_models"
            )

    report["prompt_count"] = len(list(planner))
    report["activity"] = []
    for model_name in clip_models:
        for step in requested_steps:
            active = planner.get_prompt_ids(model_name, step)
            if active:
                prompt_ids, weights = active
            else:
                prompt_ids, weights = (), ()
            report["activity"].append(
                {
                    "clip_model": model_name,
                    "step": step,
                    "prompt_ids": list(prompt_ids),
                    "weights": _jsonable(list(weights)),
                }
            )

    return report, warnings, errors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a DiscoArt YAML config, expand schedules, and optionally "
            "check PromptPlanner activity without running discoart.create()."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to a DiscoArt YAML config to validate through load_config().",
    )
    parser.add_argument(
        "--check-prompts",
        action="store_true",
        help="Build PromptPlanner and report active prompt ids/weights for selected steps.",
    )
    parser.add_argument(
        "--show-non-default",
        action="store_true",
        help="Include normalized values that differ from DiscoArt defaults.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit a JSON report instead of human-readable text.",
    )
    parser.add_argument(
        "--prompt-steps",
        default="0,500,999",
        help="Comma-separated internal 0..999 steps for --check-prompts (default: 0,500,999).",
    )
    parser.add_argument(
        "--clip-model",
        action="append",
        default=None,
        help=(
            "CLIP model to inspect for --check-prompts. Repeat for multiple models. "
            "Defaults to the first configured clip_models entry."
        ),
    )
    return parser


def _print_text(report: Dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"DiscoArt config validation: {status}")
    print(f"Config: {report['config_path']}")

    summary = report.get("summary") or {}
    if summary:
        print("\nSummary:")
        for key in ("steps", "seed", "name_docarray", "width_height", "clip_models", "cut_schedules_group"):
            if key in summary:
                print(f"  {key}: {summary[key]!r}")

    if report.get("non_default") is not None:
        print("\nNon-default normalized values:")
        non_default = report["non_default"]
        if non_default:
            for key, value in non_default.items():
                print(f"  {key}: {value!r}")
        else:
            print("  <none>")

    schedules = report.get("schedules") or {}
    if schedules:
        print("\nSchedule checks:")
        for key, value in schedules.items():
            if key == "clip_models_schedules" and isinstance(value, dict):
                print("  clip_models_schedules:")
                for model_name, model_summary in value.items():
                    print(f"    {model_name}: {model_summary}")
            else:
                print(f"  {key}: {value}")

    prompt_report = report.get("prompt_report") or {}
    if prompt_report:
        print("\nPrompt activity:")
        print(f"  prompt_count: {prompt_report.get('prompt_count')}")
        for item in prompt_report.get("activity", []):
            print(
                "  step={step} clip={clip_model!r} ids={prompt_ids} weights={weights}".format(
                    **item
                )
            )

    if report.get("warnings"):
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if report.get("errors"):
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")


def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    report: Dict[str, Any] = {
        "ok": False,
        "config_path": str(args.config),
        "summary": {},
        "schedules": {},
        "non_default": None,
        "prompt_report": None,
        "warnings": [],
        "errors": [],
    }

    if not args.config.exists():
        report["errors"].append(f"config file does not exist: {args.config}")
        if args.json_output:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            _print_text(report)
        return 2

    try:
        modules = _import_discoart_modules()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"failed to import DiscoArt helpers: {type(exc).__name__}: {exc}")
        if args.json_output:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            _print_text(report)
        return 2

    try:
        cfg = modules.load_config(str(args.config))
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"load_config: {type(exc).__name__}: {exc}")
        if args.json_output:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            _print_text(report)
        return 2

    report["summary"] = {
        "steps": _jsonable(cfg.get("steps")),
        "seed": _jsonable(cfg.get("seed")),
        "name_docarray": _jsonable(cfg.get("name_docarray")),
        "width_height": _jsonable(cfg.get("width_height")),
        "clip_models": _jsonable(cfg.get("clip_models")),
        "cut_schedules_group": _jsonable(cfg.get("cut_schedules_group")),
    }

    schedules, schedule_warnings, schedule_errors = _validate_schedules(cfg, modules)
    report["schedules"] = schedules
    report["warnings"].extend(schedule_warnings)
    report["errors"].extend(schedule_errors)

    if args.show_non_default:
        report["non_default"] = _non_defaults(cfg, modules.default_args)

    if args.check_prompts:
        steps, step_warnings = _parse_steps(args.prompt_steps, modules.max_steps)
        report["warnings"].extend(step_warnings)
        prompt_report, prompt_warnings, prompt_errors = _check_prompts(
            cfg, modules, steps, args.clip_model
        )
        report["prompt_report"] = prompt_report
        report["warnings"].extend(prompt_warnings)
        report["errors"].extend(prompt_errors)

    report["ok"] = not report["errors"]

    if args.json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
