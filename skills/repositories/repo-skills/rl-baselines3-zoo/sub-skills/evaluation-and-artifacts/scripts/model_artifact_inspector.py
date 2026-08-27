#!/usr/bin/env python3
"""Inspect RL Baselines3 Zoo artifact layouts without executing models.

This helper is intentionally read-only and dependency-free. It does not import
rl_zoo3, Stable-Baselines3, Gym/Gymnasium, torch, numpy, or any source checkout;
it only checks paths and small text metadata files.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

CHECKPOINT_RE = re.compile(r"^rl_model_(\d+)_steps\.zip$")
CONFIG_READ_LIMIT = 64 * 1024


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect a local RL Baselines3 Zoo log/model folder layout "
            "without importing RL Zoo, loading model zip files, rendering, "
            "network access, or filesystem mutation."
        )
    )
    parser.add_argument(
        "-f",
        "--folder",
        "--log-root",
        dest="folder",
        required=True,
        help="Log root containing algorithm subdirectories, for example: logs",
    )
    parser.add_argument("--algo", required=True, help="RL Zoo algorithm id, for example: ppo")
    parser.add_argument("--env", required=True, help="Environment id, for example: CartPole-v1")
    parser.add_argument(
        "--exp-id",
        type=int,
        default=0,
        help="Experiment id. 0 means latest numeric <env>_<N>; -1 means no experiment subfolder.",
    )
    parser.add_argument("--load-best", action="store_true", help="Inspect best_model.zip as the selected model")
    parser.add_argument(
        "--load-checkpoint",
        type=int,
        metavar="INT",
        help="Inspect rl_model_<INT>_steps.zip as the selected model",
    )
    parser.add_argument(
        "--load-last-checkpoint",
        action="store_true",
        help="Inspect the checkpoint with the highest numeric step count as the selected model",
    )
    parser.add_argument("--json", action="store_true", help="Emit the full report as deterministic JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when required selected artifacts or required VecNormalize stats are missing",
    )
    return parser


def as_text_path(path: Path | None) -> str | None:
    return None if path is None else str(path)


def file_record(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.is_file()}


def dir_record(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.is_dir()}


def scan_latest_runs(algo_dir: Path, env_name: str) -> list[dict[str, Any]]:
    """Mimic RL Zoo's get_latest_run_id naming convention using stdlib glob."""
    if not algo_dir.is_dir():
        return []

    runs: list[dict[str, Any]] = []
    pattern = str(algo_dir / f"{env_name}_[0-9]*")
    for raw_path in sorted(glob.glob(pattern)):
        run_id_text = raw_path.split("_")[-1]
        path_without_run_id = raw_path[: -len(run_id_text) - 1]
        path = Path(raw_path)
        if path.is_dir() and path_without_run_id.endswith(env_name) and run_id_text.isdigit():
            runs.append({"id": int(run_id_text), "name": path.name, "path": str(path)})
    runs.sort(key=lambda item: (item["id"], item["name"], item["path"]))
    return runs


def scan_checkpoints(log_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    checkpoints: list[dict[str, Any]] = []
    ignored: list[str] = []
    if not log_path.is_dir():
        return checkpoints, ignored

    for path in sorted(log_path.glob("rl_model_*_steps.zip"), key=lambda p: p.name):
        if not path.is_file():
            continue
        match = CHECKPOINT_RE.match(path.name)
        if match is None:
            ignored.append(path.name)
            continue
        checkpoints.append({"steps": int(match.group(1)), "name": path.name, "path": str(path)})
    checkpoints.sort(key=lambda item: (item["steps"], item["name"]))
    ignored.sort()
    return checkpoints, ignored


def read_small_text(path: Path, warnings: list[str]) -> str | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(CONFIG_READ_LIMIT)
    except OSError as exc:
        warnings.append(f"Could not read {path}: {exc}")
        return None


def normalize_hint_from_config(config_path: Path, warnings: list[str]) -> bool | None:
    """Return True/False when a simple top-level normalize: line is visible."""
    if not config_path.is_file():
        return None

    text = read_small_text(config_path, warnings)
    if text is None:
        return None

    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped.startswith("normalize:"):
            continue
        value = stripped.split(":", 1)[1].strip().strip('"\'').lower()
        if value in {"", "false", "no", "off", "0", "none", "null", "~", "{}", "[]"}:
            return False
        return True
    return None


def selector_flags(args: argparse.Namespace) -> list[str]:
    flags: list[str] = []
    if args.load_best:
        flags.append("--load-best")
    if args.load_checkpoint is not None:
        flags.append("--load-checkpoint")
    if args.load_last_checkpoint:
        flags.append("--load-last-checkpoint")
    return flags


def effective_selector(args: argparse.Namespace, checkpoints: list[dict[str, Any]]) -> tuple[str, Path | None, int | None]:
    """Mimic RL Zoo selector precedence from rl_zoo3.utils.get_model_path."""
    log_path: Path = args._log_path
    if args.load_best:
        return "best", log_path / "best_model.zip", None
    if args.load_checkpoint is not None:
        return "checkpoint", log_path / f"rl_model_{args.load_checkpoint}_steps.zip", args.load_checkpoint
    if args.load_last_checkpoint:
        if checkpoints:
            latest = checkpoints[-1]
            return "last-checkpoint", Path(latest["path"]), int(latest["steps"])
        return "last-checkpoint", None, None
    return "final", log_path / f"{args.env}.zip", None


def build_enjoy_command(args: argparse.Namespace, selector_kind: str, selector_steps: int | None) -> str:
    exp_id_for_command = args._effective_exp_id
    if args.exp_id < 0:
        exp_id_for_command = args.exp_id
    parts = [
        "python",
        "-m",
        "rl_zoo3.enjoy",
        "--algo",
        args.algo,
        "--env",
        args.env,
        "-f",
        str(args.folder),
        "--exp-id",
        str(exp_id_for_command),
    ]
    if selector_kind == "best":
        parts.append("--load-best")
    elif selector_kind in {"checkpoint", "last-checkpoint"} and selector_steps is not None:
        # Pin latest-checkpoint selections to the discovered step for repeatability.
        parts.extend(["--load-checkpoint", str(selector_steps)])
    elif selector_kind == "last-checkpoint":
        parts.append("--load-last-checkpoint")
    parts.extend(["--no-render", "-n", "1000"])
    return " ".join(shlex.quote(part) for part in parts)


def inspect_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    notes: list[str] = []

    folder = Path(args.folder)
    algo_dir = folder / args.algo

    if not folder.exists():
        errors.append(f"Folder does not exist: {folder}")
    elif not folder.is_dir():
        errors.append(f"Folder is not a directory: {folder}")

    if folder.is_dir() and not algo_dir.exists():
        errors.append(f"Algorithm directory does not exist: {algo_dir}")
    elif algo_dir.exists() and not algo_dir.is_dir():
        errors.append(f"Algorithm path is not a directory: {algo_dir}")

    numeric_runs = scan_latest_runs(algo_dir, args.env)
    latest_run_id = numeric_runs[-1]["id"] if numeric_runs else 0

    if args.exp_id == 0:
        effective_exp_id = latest_run_id
        if latest_run_id == 0:
            warnings.append(
                f"No positive numeric run directory matching {args.env}_<N> was found under {algo_dir}; "
                f"RL Zoo will use the no-experiment layout {algo_dir}."
            )
        else:
            notes.append(
                f"--exp-id 0 resolves to latest numeric run id {latest_run_id}; "
                "the suggested command pins that id for repeatability."
            )
    else:
        effective_exp_id = args.exp_id

    if effective_exp_id > 0:
        log_path = algo_dir / f"{args.env}_{effective_exp_id}"
    else:
        log_path = algo_dir

    args._log_path = log_path
    args._effective_exp_id = effective_exp_id

    if not log_path.exists():
        errors.append(f"Selected log_path does not exist: {log_path}")
    elif not log_path.is_dir():
        errors.append(f"Selected log_path is not a directory: {log_path}")

    flags = selector_flags(args)
    if len(flags) > 1:
        warnings.append(
            "Multiple model selector flags were supplied; RL Zoo precedence is "
            "--load-best, then --load-checkpoint, then --load-last-checkpoint. "
            "This report uses that effective target."
        )
    if args.load_checkpoint is not None and args.load_checkpoint < 0:
        errors.append(f"--load-checkpoint must be a non-negative integer, got {args.load_checkpoint}")

    checkpoints, ignored_checkpoints = scan_checkpoints(log_path)
    if ignored_checkpoints:
        warnings.append(
            "Ignored checkpoint-like files with non-integer step counts: " + ", ".join(ignored_checkpoints)
        )

    selector_kind, selected_model_path, selector_steps = effective_selector(args, checkpoints)

    final_model = log_path / f"{args.env}.zip"
    best_model = log_path / "best_model.zip"
    selected_exists = selected_model_path.is_file() if selected_model_path is not None else False

    if selector_kind == "last-checkpoint" and selected_model_path is None:
        errors.append(f"No checkpoint found for {args.algo} on {args.env}, path: {log_path}")
    elif selected_model_path is not None and not selected_exists:
        errors.append(f"No model found for {args.algo} on {args.env}, path: {selected_model_path}")

    if selector_kind != "final" and log_path.is_dir() and not final_model.is_file():
        warnings.append(f"Final model is missing; default enjoy would fail without a selector: {final_model}")

    config_dir = log_path / args.env
    config_files = {
        "args.yml": file_record(config_dir / "args.yml"),
        "config.yml": file_record(config_dir / "config.yml"),
        "env_kwargs.yml": file_record(config_dir / "env_kwargs.yml"),
        "vecnormalize.pkl": file_record(config_dir / "vecnormalize.pkl"),
    }

    if log_path.is_dir() and not config_dir.exists():
        warnings.append(f"Config directory is missing: {config_dir}")
    elif config_dir.exists() and not config_dir.is_dir():
        errors.append(f"Config path exists but is not a directory: {config_dir}")
    elif config_dir.is_dir():
        if not config_files["config.yml"]["exists"]:
            warnings.append(f"Saved config.yml is missing: {config_dir / 'config.yml'}")
        if not config_files["args.yml"]["exists"]:
            warnings.append(f"Saved args.yml is missing: {config_dir / 'args.yml'}")
        if not config_files["env_kwargs.yml"]["exists"]:
            notes.append(f"env_kwargs.yml is absent; this is common for local training but useful for exported artifacts: {config_dir / 'env_kwargs.yml'}")

    normalize_hint = normalize_hint_from_config(config_dir / "config.yml", warnings)
    if normalize_hint is True and not config_files["vecnormalize.pkl"]["exists"]:
        errors.append(f"config.yml appears to enable normalization, but vecnormalize.pkl is missing: {config_dir / 'vecnormalize.pkl'}")
    elif normalize_hint is False and not config_files["vecnormalize.pkl"]["exists"]:
        notes.append("config.yml appears to disable normalization; missing vecnormalize.pkl is expected.")
    elif normalize_hint is None and not config_files["vecnormalize.pkl"]["exists"]:
        notes.append("No normalize setting was detected; vecnormalize.pkl is required only for normalized models.")

    reward_log_candidates: list[dict[str, Any]] = []
    if log_path.is_dir():
        for child in sorted(log_path.iterdir(), key=lambda p: p.name):
            if child.is_file() and (child.name.endswith(".monitor.csv") or child.suffix == ".csv"):
                reward_log_candidates.append({"name": child.name, "path": str(child), "kind": "csv"})
            elif child.is_dir() and any(token in child.name.lower() for token in ("reward", "monitor")):
                reward_log_candidates.append({"name": child.name, "path": str(child), "kind": "directory"})

    enjoy_command = build_enjoy_command(args, selector_kind, selector_steps)

    return {
        "inputs": {
            "folder": str(folder),
            "algo": args.algo,
            "env": args.env,
            "requested_exp_id": args.exp_id,
            "load_best": bool(args.load_best),
            "load_checkpoint": args.load_checkpoint,
            "load_last_checkpoint": bool(args.load_last_checkpoint),
            "strict": bool(args.strict),
        },
        "run_selection": {
            "latest_run_id": latest_run_id,
            "effective_exp_id": effective_exp_id,
            "numeric_runs": numeric_runs,
        },
        "paths": {
            "folder": str(folder),
            "algo_dir": str(algo_dir),
            "log_path": str(log_path),
            "config_dir": str(config_dir),
        },
        "selector": {
            "kind": selector_kind,
            "steps": selector_steps,
            "selected_model": as_text_path(selected_model_path),
            "selected_model_exists": selected_exists,
        },
        "artifacts": {
            "final_model": file_record(final_model),
            "best_model": file_record(best_model),
            "checkpoints": checkpoints,
            "ignored_checkpoint_names": ignored_checkpoints,
            "config_dir": dir_record(config_dir),
            "config_files": config_files,
            "normalize_hint": normalize_hint,
            "evaluations_npz": file_record(log_path / "evaluations.npz"),
            "reward_log_candidates": reward_log_candidates,
        },
        "suggested_enjoy_command": enjoy_command,
        "warnings": warnings,
        "errors": errors,
        "notes": notes,
    }


def print_human_report(report: dict[str, Any]) -> None:
    selector = report["selector"]
    artifacts = report["artifacts"]
    run_selection = report["run_selection"]
    inputs = report["inputs"]

    print("RL Zoo artifact inspection")
    print(f"  folder: {inputs['folder']}")
    print(f"  algo/env: {inputs['algo']} / {inputs['env']}")
    print(
        f"  exp-id: requested {inputs['requested_exp_id']}, "
        f"effective {run_selection['effective_exp_id']} "
        f"(latest numeric run id: {run_selection['latest_run_id']})"
    )
    print(f"  log_path: {report['paths']['log_path']}")
    print(f"  selector: {selector['kind']}")
    print(f"  selected model: {selector['selected_model']} ({'found' if selector['selected_model_exists'] else 'missing'})")
    print("")
    print("Artifacts")
    print(f"  final model: {'found' if artifacts['final_model']['exists'] else 'missing'} - {artifacts['final_model']['path']}")
    print(f"  best model: {'found' if artifacts['best_model']['exists'] else 'missing'} - {artifacts['best_model']['path']}")
    if artifacts["checkpoints"]:
        steps = ", ".join(str(item["steps"]) for item in artifacts["checkpoints"])
        print(f"  checkpoints: {len(artifacts['checkpoints'])} ({steps})")
    else:
        print("  checkpoints: none")
    print(f"  config dir: {'found' if artifacts['config_dir']['exists'] else 'missing'} - {artifacts['config_dir']['path']}")
    for name, record in artifacts["config_files"].items():
        print(f"    {name}: {'found' if record['exists'] else 'missing'}")
    print(f"  normalize hint from config.yml: {artifacts['normalize_hint']}")
    print(f"  evaluations.npz: {'found' if artifacts['evaluations_npz']['exists'] else 'missing'}")
    if artifacts["reward_log_candidates"]:
        names = ", ".join(item["name"] for item in artifacts["reward_log_candidates"])
        print(f"  reward log candidates: {names}")
    else:
        print("  reward log candidates: none")
    print("")
    print("Suggested no-render enjoy command")
    print(f"  {report['suggested_enjoy_command']}")

    if report["errors"]:
        print("")
        print("Errors")
        for item in report["errors"]:
            print(f"  - {item}")
    if report["warnings"]:
        print("")
        print("Warnings")
        for item in report["warnings"]:
            print(f"  - {item}")
    if report["notes"]:
        print("")
        print("Notes")
        for item in report["notes"]:
            print(f"  - {item}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = inspect_artifacts(args)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human_report(report)

    if args.strict and report["errors"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
