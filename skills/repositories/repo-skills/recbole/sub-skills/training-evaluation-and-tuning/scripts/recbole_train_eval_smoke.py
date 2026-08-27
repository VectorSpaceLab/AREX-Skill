#!/usr/bin/env python3
"""CPU-first RecBole train/evaluate smoke wrapper.

Default behavior is safe: print the effective config and exit. Pass --run to
launch RecBole training/evaluation. This script imports an installed RecBole
package from the active Python environment and does not depend on a source
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


def _friendly_import():
    try:
        from recbole.quick_start import run, run_recbole
    except ImportError as exc:  # pragma: no cover - environment dependent
        message = (
            "Unable to import RecBole. Install RecBole in the active Python "
            "environment before running this helper. Original import error: "
            f"{exc}"
        )
        raise SystemExit(message) from exc
    return run, run_recbole


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


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    config: dict[str, Any] = {
        "use_gpu": bool(args.use_gpu),
        "epochs": args.epochs,
        "show_progress": bool(args.show_progress),
        "log_wandb": False,
    }

    if args.seed is not None:
        config["seed"] = args.seed
    if args.data_path:
        config["data_path"] = str(Path(args.data_path).expanduser().resolve())
    if args.eval_mode:
        config["eval_args"] = {"mode": args.eval_mode}
    if args.metrics:
        config["metrics"] = [metric.strip() for metric in args.metrics.split(",") if metric.strip()]
    if args.topk:
        config["topk"] = _parse_value(args.topk)
    if args.valid_metric:
        config["valid_metric"] = args.valid_metric

    if args.save or args.save_dataset or args.save_dataloaders:
        if not args.checkpoint_dir:
            raise SystemExit(
                "Saving model/data artifacts requires an explicit --checkpoint-dir. "
                "For no-checkpoint smoke tests, omit --save/--save-dataset/--save-dataloaders."
            )
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
            "Print or run a bounded RecBole train/evaluate smoke test. "
            "Training only happens with --run."
        )
    )
    parser.add_argument("--model", "-m", default="BPR", help="RecBole model name, e.g. BPR")
    parser.add_argument("--dataset", "-d", default="ml-100k", help="RecBole dataset name")
    parser.add_argument(
        "--config-files",
        "--config_files",
        nargs="*",
        default=None,
        help="Optional config file paths. Multiple args or a single space-separated string are accepted.",
    )
    parser.add_argument("--api", choices=["run", "run_recbole"], default="run", help="Public API route to call")
    parser.add_argument("--epochs", type=int, default=1, help="Bounded epoch count for smoke runs")
    parser.add_argument("--seed", type=int, default=None, help="Optional RecBole random seed")
    parser.add_argument("--data-path", "--data_path", default=None, help="Optional dataset root; converted to an absolute path")
    parser.add_argument("--eval-mode", "--eval_mode", default=None, help="Optional eval_args.mode override, e.g. full, uni100, pop100, labeled")
    parser.add_argument("--metrics", default=None, help="Comma-separated metric names, e.g. Recall,MRR,NDCG,Hit,Precision")
    parser.add_argument("--topk", default=None, help="Top-k value or list, e.g. 10 or [5,10]")
    parser.add_argument("--valid-metric", "--valid_metric", default=None, help="Validation metric for early stopping, e.g. MRR@10")
    parser.add_argument("--use-gpu", "--use_gpu", action="store_true", help="Opt in to GPU use. Default is CPU.")
    parser.add_argument("--show-progress", "--show_progress", action="store_true", help="Show tqdm progress bars. Default is off.")
    parser.add_argument("--save", action="store_true", help="Save the best model checkpoint. Requires --checkpoint-dir.")
    parser.add_argument("--checkpoint-dir", "--checkpoint_dir", default=None, help="Checkpoint/data artifact directory, explicit when saving")
    parser.add_argument("--save-dataset", "--save_dataset", action="store_true", help="Ask RecBole to save the filtered dataset. Requires --checkpoint-dir.")
    parser.add_argument("--save-dataloaders", "--save_dataloaders", action="store_true", help="Ask RecBole to save split dataloaders. Requires --checkpoint-dir.")
    parser.add_argument("--config-json", "--config_json", default=None, help="JSON object merged into config_dict after safe defaults")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="Additional config override; repeatable")
    parser.add_argument("--nproc", type=int, default=1, help="Processes on current node for run(...)")
    parser.add_argument("--world-size", "--world_size", type=int, default=-1, help="Total distributed ranks for run(...)")
    parser.add_argument("--ip", default="localhost", help="Distributed master IP for run(...)")
    parser.add_argument("--port", default="5678", help="Distributed master port for run(...)")
    parser.add_argument("--group-offset", "--group_offset", type=int, default=0, help="Distributed rank offset for current group")
    parser.add_argument("--work-dir", "--work_dir", default=".", help="Working directory for RecBole relative outputs when --run is used")
    parser.add_argument("--dry-run-config", "--dry_run_config", action="store_true", help="Print effective call/config and exit")
    parser.add_argument("--run", action="store_true", help="Actually execute RecBole training/evaluation")
    args = parser.parse_args(argv)

    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    if args.api == "run_recbole" and (args.nproc != 1 or args.world_size > 0):
        parser.error("run_recbole is single-process; use --api run for nproc/world_size")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_file_list = _normalize_config_files(args.config_files)
    config_dict = build_config(args)
    saved = bool(args.save)

    call_preview = {
        "api": args.api,
        "model": args.model,
        "dataset": args.dataset,
        "config_file_list": config_file_list,
        "config_dict": config_dict,
        "saved": saved,
        "distributed": {
            "nproc": args.nproc,
            "world_size": args.world_size,
            "ip": args.ip,
            "port": args.port,
            "group_offset": args.group_offset,
        },
        "work_dir": str(Path(args.work_dir).expanduser()),
    }
    print(json.dumps(call_preview, indent=2, sort_keys=True))

    if args.dry_run_config or not args.run:
        if not args.run:
            print("\nDry run only. Pass --run to execute RecBole training/evaluation.")
        return 0

    work_dir = Path(args.work_dir).expanduser()
    work_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)
    os.environ.setdefault("WANDB_DISABLED", "true")

    run, run_recbole = _friendly_import()

    original_argv = sys.argv[:]
    try:
        # RecBole's Config reads sys.argv for user overrides. Hide this helper's
        # own flags so RecBole does not warn that helper-only arguments such as
        # --work-dir or --run are unused command-line config keys.
        sys.argv = [sys.argv[0]]
        if args.api == "run":
            result = run(
                args.model,
                args.dataset,
                config_file_list=config_file_list,
                config_dict=config_dict,
                saved=saved,
                nproc=args.nproc,
                world_size=args.world_size,
                ip=args.ip,
                port=args.port,
                group_offset=args.group_offset,
            )
        else:
            result = run_recbole(
                model=args.model,
                dataset=args.dataset,
                config_file_list=config_file_list,
                config_dict=config_dict,
                saved=saved,
            )
    finally:
        sys.argv = original_argv

    print("\nRecBole result:")
    print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
