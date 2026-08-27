#!/usr/bin/env python3
"""Safely inspect local CleanRL saved-model artifacts.

This checker performs local filesystem inspection only. It does not import
CleanRL, does not import Hugging Face libraries, and does not use the network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ENJOY_MODELS = {
    "dqn",
    "dqn_atari",
    "dqn_jax",
    "dqn_atari_jax",
    "c51",
    "c51_atari",
    "c51_jax",
    "c51_atari_jax",
    "ppo_atari_envpool_xla_jax_scan",
}

STANDALONE_EVAL_MODULES = {
    "ddpg_continuous_action": "cleanrl_utils.evals.ddpg_eval",
    "ddpg_continuous_action_jax": "cleanrl_utils.evals.ddpg_jax_eval",
    "td3_continuous_action": "cleanrl_utils.evals.td3_eval",
    "td3_continuous_action_jax": "cleanrl_utils.evals.td3_jax_eval",
    "ppo_continuous_action": "cleanrl_utils.evals.ppo_eval",
}

RUN_NAME_PATTERN = re.compile(
    r"^(?P<env_id>.+)__(?P<exp_name>.+)__(?P<seed>\d+)__(?P<timestamp>\d+)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"), help="CleanRL runs directory to search")
    parser.add_argument("--run-dir", type=Path, help="Specific CleanRL run directory to inspect")
    parser.add_argument("--model-file", type=Path, help="Specific .cleanrl_model file to inspect")
    parser.add_argument("--exp-name", required=True, help="CleanRL experiment name, e.g. dqn or c51_jax")
    parser.add_argument("--env-id", help="Expected environment id, e.g. CartPole-v1")
    parser.add_argument("--seed", type=int, help="Expected seed embedded in run and repository names")
    parser.add_argument("--hf-entity", default="cleanrl", help="Hugging Face owner/org used for derived repository hints")
    parser.add_argument("--hf-repository", help="Explicit Hugging Face repository id to compare with derived hints")
    parser.add_argument("--videos-dir", type=Path, default=Path("videos"), help="CleanRL videos directory to inspect")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a nonzero exit")
    return parser.parse_args()


def parse_run_name(run_dir: Path) -> dict[str, Any]:
    match = RUN_NAME_PATTERN.match(run_dir.name)
    if not match:
        return {"parsed": False, "raw": run_dir.name}
    result: dict[str, Any] = match.groupdict()
    result["parsed"] = True
    result["seed"] = int(result["seed"])
    return result


def find_candidate_run_dirs(args: argparse.Namespace) -> list[Path]:
    if args.run_dir:
        return [args.run_dir]
    if args.model_file:
        return [args.model_file.parent]
    if not args.runs_dir.exists():
        return []

    candidates: list[Path] = []
    for child in sorted(args.runs_dir.iterdir()):
        if not child.is_dir():
            continue
        parsed = parse_run_name(child)
        if parsed.get("parsed"):
            if parsed.get("exp_name") != args.exp_name:
                continue
            if args.env_id and parsed.get("env_id") != args.env_id:
                continue
            if args.seed is not None and parsed.get("seed") != args.seed:
                continue
        elif args.exp_name not in child.name:
            continue
        candidates.append(child)
    return candidates


def list_relative_files(root: Path, pattern: str) -> list[str]:
    if not root.exists():
        return []
    return [str(path.relative_to(root)) for path in sorted(root.glob(pattern)) if path.is_file()]


def inspect_run_dir(run_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    expected_model = run_dir / f"{args.exp_name}.cleanrl_model"
    model_file = args.model_file or expected_model
    parsed = parse_run_name(run_dir)
    event_files = list_relative_files(run_dir, "*tfevents*")
    model_files = list_relative_files(run_dir, "*.cleanrl_model")
    train_video_dir = args.videos_dir / run_dir.name
    eval_video_dir = args.videos_dir / f"{run_dir.name}-eval"

    warnings: list[str] = []
    errors: list[str] = []

    if not run_dir.exists():
        errors.append(f"Run directory does not exist: {run_dir}")
    elif not run_dir.is_dir():
        errors.append(f"Run path is not a directory: {run_dir}")

    if not model_file.exists():
        errors.append(f"Expected model file is missing: {model_file}")
        if model_files:
            warnings.append(f"Other .cleanrl_model files found: {', '.join(model_files)}")
        else:
            warnings.append("No .cleanrl_model files found; confirm training used --save-model")
    elif model_file.suffix != ".cleanrl_model":
        warnings.append(f"Model file does not use .cleanrl_model suffix: {model_file}")

    if parsed.get("parsed"):
        if parsed.get("exp_name") != args.exp_name:
            errors.append(f"Run exp_name {parsed.get('exp_name')} does not match requested {args.exp_name}")
        if args.env_id and parsed.get("env_id") != args.env_id:
            errors.append(f"Run env_id {parsed.get('env_id')} does not match requested {args.env_id}")
        if args.seed is not None and parsed.get("seed") != args.seed:
            errors.append(f"Run seed {parsed.get('seed')} does not match requested {args.seed}")
    else:
        warnings.append("Run directory name does not match <env_id>__<exp_name>__<seed>__<timestamp>")

    if not event_files:
        warnings.append("No TensorBoard event files found in the run directory")

    video_status = {
        "training_video_dir": str(train_video_dir),
        "training_video_exists": train_video_dir.exists(),
        "eval_video_dir": str(eval_video_dir),
        "eval_video_exists": eval_video_dir.exists(),
    }

    return {
        "run_dir": str(run_dir),
        "parsed_run_name": parsed,
        "expected_model": str(expected_model),
        "inspected_model": str(model_file),
        "model_exists": model_file.exists(),
        "model_size_bytes": model_file.stat().st_size if model_file.exists() else None,
        "model_files": model_files,
        "tensorboard_event_files": event_files,
        "video_status": video_status,
        "warnings": warnings,
        "errors": errors,
    }


def derive_hf_repository(args: argparse.Namespace) -> dict[str, Any]:
    if args.env_id and args.seed is not None:
        repo_name = f"{args.env_id}-{args.exp_name}-seed{args.seed}"
        derived = f"{args.hf_entity}/{repo_name}" if args.hf_entity else repo_name
    else:
        repo_name = None
        derived = None

    warnings: list[str] = []
    if args.hf_repository and derived and args.hf_repository != derived:
        warnings.append(f"Provided repository differs from derived default: {derived}")
    if args.hf_repository and "/" not in args.hf_repository:
        warnings.append("Hugging Face repository override is not owner/repo; enjoy examples use a full owner/repo id")

    return {
        "derived_repository": derived,
        "provided_repository": args.hf_repository,
        "expected_filename": f"{args.exp_name}.cleanrl_model",
        "warnings": warnings,
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    candidate_run_dirs = find_candidate_run_dirs(args)
    inspected_runs = [inspect_run_dir(run_dir, args) for run_dir in candidate_run_dirs]
    hf_repository = derive_hf_repository(args)

    warnings: list[str] = []
    errors: list[str] = []

    if not candidate_run_dirs:
        errors.append("No matching run directories found")
        if not args.runs_dir.exists() and not args.run_dir and not args.model_file:
            warnings.append(f"Runs directory does not exist: {args.runs_dir}")

    if args.exp_name not in ENJOY_MODELS:
        module_hint = STANDALONE_EVAL_MODULES.get(args.exp_name)
        if module_hint:
            warnings.append(f"{args.exp_name} is not routed by cleanrl_utils.enjoy; use {module_hint}.evaluate for local evaluation")
        else:
            warnings.append(f"{args.exp_name} is not in the observed cleanrl_utils.evals.MODELS router")

    for run_report in inspected_runs:
        warnings.extend(run_report["warnings"])
        errors.extend(run_report["errors"])
    warnings.extend(hf_repository["warnings"])

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"

    hints = [
        "Local model path should usually be runs/<env_id>__<exp_name>__<seed>__<timestamp>/<exp_name>.cleanrl_model.",
        "If the model is missing, rerun training with --save-model; add --upload-model only after explicit sharing approval.",
        "Use direct cleanrl_utils.evals calls for local files; cleanrl_utils.enjoy downloads from Hugging Face.",
        "Use capture_video=False while debugging model/env/dependency mismatches.",
    ]

    return {
        "status": status,
        "query": {
            "runs_dir": str(args.runs_dir),
            "run_dir": str(args.run_dir) if args.run_dir else None,
            "model_file": str(args.model_file) if args.model_file else None,
            "exp_name": args.exp_name,
            "env_id": args.env_id,
            "seed": args.seed,
        },
        "enjoy_routed": args.exp_name in ENJOY_MODELS,
        "hf_repository": hf_repository,
        "runs": inspected_runs,
        "warnings": warnings,
        "errors": errors,
        "hints": hints,
    }


def print_text(result: dict[str, Any]) -> None:
    print(f"CleanRL artifact check: {result['status'].upper()}")
    print(f"exp_name: {result['query']['exp_name']}")
    print(f"enjoy routed: {result['enjoy_routed']}")

    hf_repository = result["hf_repository"]
    if hf_repository["derived_repository"]:
        print(f"derived HF repo: {hf_repository['derived_repository']}")
    if hf_repository["provided_repository"]:
        print(f"provided HF repo: {hf_repository['provided_repository']}")
    print(f"expected HF/model filename: {hf_repository['expected_filename']}")

    for run_report in result["runs"]:
        print(f"\nrun: {run_report['run_dir']}")
        print(f"  parsed: {run_report['parsed_run_name']}")
        print(f"  model: {run_report['inspected_model']}")
        print(f"  model exists: {run_report['model_exists']}")
        if run_report["model_size_bytes"] is not None:
            print(f"  model size bytes: {run_report['model_size_bytes']}")
        print(f"  TensorBoard event files: {len(run_report['tensorboard_event_files'])}")
        print(f"  training videos dir exists: {run_report['video_status']['training_video_exists']}")
        print(f"  eval videos dir exists: {run_report['video_status']['eval_video_exists']}")

    if result["warnings"]:
        print("\nwarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    if result["errors"]:
        print("\nerrors:")
        for error in result["errors"]:
            print(f"  - {error}")

    print("\nhints:")
    for hint in result["hints"]:
        print(f"  - {hint}")


def main() -> int:
    args = parse_args()
    result = build_result(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)

    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
