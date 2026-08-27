#!/usr/bin/env python3
"""Generate, validate, and optionally run a tiny RecBole HyperTuning search.

Default behavior has no training side effects. Pass --run to launch HyperTuning.
The script imports installed RecBole only for --run and does not require a source
checkout.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

TEMPLATE = """# RecBole HyperTuning parameter file
# Format: parameter_name range_type range_value
# Range types: choice, uniform, loguniform, quniform
learning_rate loguniform -8,0
embedding_size choice [32,64]
train_batch_size choice [256,512]
"""

RAY_SKELETON = """# Ray Tune sketch for RecBole objective_function
# Use absolute config paths and absolute data_path in the fixed config because
# Ray changes each trial's working directory under local_dir.
import math
import ray
from ray import tune
from ray.tune.schedulers import ASHAScheduler
from recbole.quick_start import objective_function

ray.init()
config = {
    "learning_rate": tune.loguniform(math.exp(-8), math.exp(0)),
    "embedding_size": tune.choice([32, 64]),
}
scheduler = ASHAScheduler(metric="recall@10", mode="max", max_t=10, grace_period=1)
result = tune.run(
    tune.with_parameters(objective_function, config_file_list=["/absolute/fixed.yaml"]),
    config=config,
    num_samples=2,
    scheduler=scheduler,
    local_dir="./ray_log",
    resources_per_trial={"gpu": 1},
)
"""


def _friendly_import():
    try:
        from recbole.quick_start import objective_function
        from recbole.trainer import HyperTuning
    except ImportError as exc:  # pragma: no cover - environment dependent
        message = (
            "Unable to import RecBole HyperTuning dependencies. Install RecBole "
            "and Hyperopt in the active Python environment before --run. "
            f"Original import error: {exc}"
        )
        raise SystemExit(message) from exc
    return HyperTuning, objective_function


def _parse_value(raw: str) -> Any:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return raw


def _parse_key_value(items: Iterable[str] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--set expects KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"--set has an empty key in {item!r}")
        result[key] = _parse_value(value)
    return result


def _normalize_config_files(raw: list[str] | None) -> list[str] | None:
    if not raw:
        return None
    pieces: list[str] = []
    for token in raw:
        pieces.extend(part for part in token.split() if part)
    if not pieces:
        return None
    return [str(Path(piece).expanduser().resolve()) for piece in pieces]


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    if hasattr(obj, "tolist"):
        try:
            return obj.tolist()
        except Exception:
            pass
    return obj


def _validate_param_line(line: str, line_no: int) -> tuple[str, str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = stripped.split(maxsplit=2)
    if len(parts) != 3:
        raise ValueError(f"line {line_no}: expected 3 fields: name type value")
    name, range_type, value = parts
    if range_type == "choice":
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(f"line {line_no}: choice value must be a Python-like list") from exc
        if not isinstance(parsed, (list, tuple)) or not parsed:
            raise ValueError(f"line {line_no}: choice value must be a non-empty list")
    elif range_type in {"uniform", "loguniform"}:
        bounds = [piece.strip() for piece in value.split(",")]
        if len(bounds) != 2:
            raise ValueError(f"line {line_no}: {range_type} expects low,high")
        float(bounds[0]); float(bounds[1])
    elif range_type == "quniform":
        bounds = [piece.strip() for piece in value.split(",")]
        if len(bounds) != 3:
            raise ValueError(f"line {line_no}: quniform expects low,high,q")
        float(bounds[0]); float(bounds[1]); float(bounds[2])
    else:
        raise ValueError(
            f"line {line_no}: illegal range type {range_type!r}; "
            "use choice, uniform, loguniform, or quniform"
        )
    return name, range_type, value


def validate_params_file(path: Path) -> list[tuple[str, str, str]]:
    if not path.is_file():
        raise SystemExit(f"Parameter file does not exist: {path}")
    entries: list[tuple[str, str, str]] = []
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        try:
            parsed = _validate_param_line(line, line_no)
            if parsed is not None:
                entries.append(parsed)
        except Exception as exc:  # collect all validation issues
            errors.append(str(exc))
    if errors:
        raise SystemExit("Parameter file validation failed:\n" + "\n".join(errors))
    if not entries:
        raise SystemExit("Parameter file has no active parameter entries")
    return entries


def write_template(path_text: str, force: bool) -> None:
    if path_text == "-":
        print(TEMPLATE)
        return
    path = Path(path_text).expanduser()
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE)
    print(f"Wrote template: {path}")


def build_fixed_config(args: argparse.Namespace) -> dict[str, Any]:
    config: dict[str, Any] = {
        "model": args.model,
        "dataset": args.dataset,
        "use_gpu": bool(args.use_gpu),
        "epochs": args.epochs,
        "show_progress": bool(args.show_progress),
        "log_wandb": False,
    }
    if args.seed is not None:
        config["seed"] = args.seed
    if args.data_path:
        config["data_path"] = str(Path(args.data_path).expanduser().resolve())
    if args.save or args.save_dataset or args.save_dataloaders:
        if not args.checkpoint_dir:
            raise SystemExit("Saving during HPO requires an explicit --checkpoint-dir")
        config["checkpoint_dir"] = args.checkpoint_dir
    elif args.checkpoint_dir:
        config["checkpoint_dir"] = args.checkpoint_dir
    if args.save_dataset:
        config["save_dataset"] = True
    if args.save_dataloaders:
        config["save_dataloaders"] = True
    if args.config_json:
        try:
            config.update(json.loads(args.config_json))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--config-json is not valid JSON: {exc}") from exc
    config.update(_parse_key_value(args.set))
    return config


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate/validate RecBole HyperTuning parameter files and optionally "
            "run a tiny bounded search with --run."
        )
    )
    parser.add_argument("--write-template", metavar="PATH", help="Write a template parameter file; use '-' for stdout")
    parser.add_argument("--force", action="store_true", help="Allow --write-template to overwrite an existing file")
    parser.add_argument("--params-file", "--params_file", help="HyperTuning parameter file to validate or run")
    parser.add_argument("--validate", action="store_true", help="Validate --params-file and exit unless --run is also supplied")
    parser.add_argument("--print-ray-skeleton", "--print_ray_skeleton", action="store_true", help="Print a Ray Tune skeleton and exit unless --run is supplied")
    parser.add_argument("--config-files", "--config_files", nargs="*", default=None, help="Fixed RecBole config file paths")
    parser.add_argument("--model", default="BPR", help="Fixed model name for the bounded objective")
    parser.add_argument("--dataset", default="ml-100k", help="Fixed dataset name for the bounded objective")
    parser.add_argument("--epochs", type=int, default=1, help="Bounded epoch count for tuning smoke runs")
    parser.add_argument("--seed", type=int, default=None, help="Optional fixed RecBole seed")
    parser.add_argument("--data-path", "--data_path", default=None, help="Optional dataset root; converted to an absolute path")
    parser.add_argument("--use-gpu", "--use_gpu", action="store_true", help="Opt in to GPU use. Default is CPU.")
    parser.add_argument("--show-progress", "--show_progress", action="store_true", help="Show tqdm progress bars. Default is off.")
    parser.add_argument("--algo", choices=["exhaustive", "random", "bayes"], default="random", help="HyperTuning algorithm")
    parser.add_argument("--max-evals", "--max_evals", type=int, default=2, help="Maximum trials for random/bayes; exhaustive computes its own size")
    parser.add_argument("--early-stop", "--early_stop", type=int, default=2, help="Hyperopt no-progress early stop patience")
    parser.add_argument("--output-file", "--output_file", default=None, help="Optional HyperTuning export result file")
    parser.add_argument("--display-file", "--display_file", default=None, help="Optional HyperTuning display output file")
    parser.add_argument("--save", action="store_true", help="Save model checkpoints during tuning. Requires --checkpoint-dir.")
    parser.add_argument("--checkpoint-dir", "--checkpoint_dir", default=None, help="Checkpoint/data artifact directory when saving")
    parser.add_argument("--save-dataset", "--save_dataset", action="store_true", help="Save filtered datasets during tuning. Requires --checkpoint-dir.")
    parser.add_argument("--save-dataloaders", "--save_dataloaders", action="store_true", help="Save split dataloaders during tuning. Requires --checkpoint-dir.")
    parser.add_argument("--config-json", "--config_json", default=None, help="JSON object merged into fixed config")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="Additional fixed config override; repeatable")
    parser.add_argument("--work-dir", "--work_dir", default=".", help="Working directory for RecBole relative outputs when --run is used")
    parser.add_argument("--run", action="store_true", help="Actually execute HyperTuning")
    args = parser.parse_args(argv)
    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    if args.max_evals < 1:
        parser.error("--max-evals must be >= 1")
    if args.early_stop < 1:
        parser.error("--early-stop must be >= 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.write_template:
        write_template(args.write_template, args.force)

    if args.print_ray_skeleton:
        print(RAY_SKELETON)

    params_path = Path(args.params_file).expanduser().resolve() if args.params_file else None
    entries: list[tuple[str, str, str]] | None = None
    if params_path:
        entries = validate_params_file(params_path)
        print(f"Validated {len(entries)} active parameter entries in {params_path}")
    elif args.validate or args.run:
        raise SystemExit("--params-file is required for --validate or --run")

    fixed_config = build_fixed_config(args)
    config_file_list = _normalize_config_files(args.config_files)
    preview = {
        "params_file": str(params_path) if params_path else None,
        "entries": entries,
        "fixed_config_file_list": config_file_list,
        "fixed_config_dict": fixed_config,
        "algo": args.algo,
        "max_evals": args.max_evals,
        "early_stop": args.early_stop,
        "saved": bool(args.save),
        "work_dir": str(Path(args.work_dir).expanduser()),
    }
    print(json.dumps(preview, indent=2, sort_keys=True))

    if not args.run:
        print("\nNo tuning launched. Pass --run to execute HyperTuning.")
        return 0

    assert params_path is not None
    work_dir = Path(args.work_dir).expanduser()
    work_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)
    os.environ.setdefault("WANDB_DISABLED", "true")

    HyperTuning, objective_function = _friendly_import()
    saved = bool(args.save)

    def bounded_objective(config_dict=None, config_file_list=None):
        merged = dict(fixed_config)
        if config_dict:
            merged.update(config_dict)
        return objective_function(config_dict=merged, config_file_list=config_file_list, saved=saved)

    original_argv = sys.argv[:]
    try:
        # RecBole's Config reads sys.argv for config overrides. Hide this
        # helper's own CLI flags from inner objective_function calls.
        sys.argv = [sys.argv[0]]
        hp = HyperTuning(
            bounded_objective,
            algo=args.algo,
            early_stop=args.early_stop,
            max_evals=args.max_evals,
            params_file=str(params_path),
            fixed_config_file_list=config_file_list,
            display_file=args.display_file,
        )
        hp.run()
    finally:
        sys.argv = original_argv
    if args.output_file:
        hp.export_result(output_file=args.output_file)
        print(f"Exported result: {args.output_file}")
    best_key = hp.params2str(hp.best_params)
    print("best params:")
    print(json.dumps(_jsonable(hp.best_params), indent=2, sort_keys=True))
    print("best result:")
    print(json.dumps(_jsonable(hp.params2result.get(best_key)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
