#!/usr/bin/env python3
"""Self-contained MuZero General entry point backed by the bundled source snapshot.

Omit --repo-root to use runtime/source inside this generated skill. Pass
--repo-root only when intentionally validating a staged editable copy or a
separate target checkout.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import importlib
import json
import pathlib
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

from _skill_runtime import RuntimeSourceError, add_source_to_syspath, resolve_source_root


class EntrypointError(RuntimeError):
    """User-facing MuZero entry point failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MuZero General from the skill-bundled source snapshot or an optional staged source root."
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional MuZero General source root. Omit to use the bundled runtime/source snapshot.")
    parser.add_argument("--game", required=True, help="Game module short name, for example tictactoe or cartpole.")
    parser.add_argument("--config-json", default=None, help="JSON object of MuZeroConfig overrides.")
    parser.add_argument("--mode", choices=["construct", "train", "test"], default="construct", help="Action to run. Default construct avoids training side effects.")
    parser.add_argument("--safe-smoke", action="store_true", help="Apply CPU-only smoke overrides: training_steps=0, num_simulations=1, max_moves=1, num_workers=1, save_model=false, GPU flags false.")
    parser.add_argument("--force-cpu", action="store_true", help="Set max_num_gpus=0 and all MuZero GPU flags false.")
    parser.add_argument("--results-path", type=Path, default=None, help="Directory for train-mode checkpoints/TensorBoard logs. Train mode defaults to ./muzero-results/<game>/<timestamp> to avoid mutating the bundled source.")
    parser.add_argument("--log-in-tensorboard", action="store_true", help="In train mode, pass log_in_tensorboard=True. Default false keeps zero-step smokes quiet.")
    parser.add_argument("--render", action="store_true", help="In test mode, render the environment. Avoid on headless servers unless intended.")
    parser.add_argument("--opponent", default="self", help="Opponent passed to MuZero.test in test mode. Default self.")
    parser.add_argument("--muzero-player", type=int, default=None, help="MuZero player index passed to MuZero.test in test mode.")
    parser.add_argument("--keep-ray", action="store_true", help="Do not call ray.shutdown() at process exit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print tracebacks for unexpected errors.")
    return parser.parse_args()


def load_json_object(text: str | None) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EntrypointError(f"--config-json is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise EntrypointError("--config-json must decode to a JSON object")
    return obj


def apply_override(config: Any, game: str, name: str, value: Any) -> None:
    if not hasattr(config, name):
        raise EntrypointError(
            f"{game} config has no attribute '{name}'. Check the config file for the complete list of parameters."
        )
    if name == "results_path":
        value = pathlib.Path(value).expanduser()
    setattr(config, name, value)


def build_config(game: str, overrides: Dict[str, Any], args: argparse.Namespace) -> Any:
    module = importlib.import_module("games." + game)
    if not hasattr(module, "MuZeroConfig"):
        raise EntrypointError(f"games.{game} does not expose MuZeroConfig")
    config = module.MuZeroConfig()
    for name, value in overrides.items():
        apply_override(config, game, name, value)
    if args.safe_smoke:
        for name, value in {
            "training_steps": 0,
            "num_simulations": 1,
            "max_moves": 1,
            "num_workers": 1,
            "save_model": False,
            "max_num_gpus": 0,
            "train_on_gpu": False,
            "selfplay_on_gpu": False,
            "reanalyse_on_gpu": False,
        }.items():
            if hasattr(config, name):
                setattr(config, name, value)
    if args.force_cpu:
        for name, value in {
            "max_num_gpus": 0,
            "train_on_gpu": False,
            "selfplay_on_gpu": False,
            "reanalyse_on_gpu": False,
        }.items():
            if hasattr(config, name):
                setattr(config, name, value)
    if args.results_path is not None:
        config.results_path = args.results_path.expanduser().resolve()
    elif args.mode == "train":
        timestamp = _datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        config.results_path = (Path.cwd() / "muzero-results" / game / timestamp).resolve()
    return config


def summarize_config(config: Any) -> Dict[str, Any]:
    fields = [
        "seed",
        "max_num_gpus",
        "num_workers",
        "selfplay_on_gpu",
        "train_on_gpu",
        "reanalyse_on_gpu",
        "training_steps",
        "max_moves",
        "num_simulations",
        "save_model",
        "network",
        "observation_shape",
        "action_space",
        "players",
        "opponent",
        "results_path",
    ]
    out: Dict[str, Any] = {}
    for field in fields:
        if hasattr(config, field):
            value = getattr(config, field)
            if field == "results_path":
                value = str(value)
            elif field in {"action_space", "observation_shape", "players"}:
                value = list(value)
            out[field] = value
    return out


def main() -> int:
    args = parse_args()
    ray = None
    try:
        source_root, source_kind = resolve_source_root(args.repo_root, start=Path(__file__))
        add_source_to_syspath(source_root)
        overrides = load_json_object(args.config_json)
        config = build_config(args.game, overrides, args)

        from muzero import MuZero  # type: ignore
        import ray as ray_module  # type: ignore

        ray = ray_module
        muzero = MuZero(args.game, config)
        action = "constructed"
        if args.mode == "train":
            muzero.train(log_in_tensorboard=args.log_in_tensorboard)
            muzero.terminate_workers()
            action = "trained"
        elif args.mode == "test":
            muzero.test(render=args.render, opponent=args.opponent, muzero_player=args.muzero_player)
            action = "tested"

        payload = {
            "ok": True,
            "source": source_kind,
            "game": args.game,
            "mode": args.mode,
            "action": action,
            "num_gpus": muzero.num_gpus,
            "config": summarize_config(muzero.config),
            "checkpoint_keys": sorted(muzero.checkpoint.keys()),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print("MuZero General entry point OK")
            print(f"  source: {source_kind}")
            print(f"  game: {args.game}")
            print(f"  mode: {args.mode}")
            print(f"  action: {action}")
            print(f"  config: {json.dumps(payload['config'], sort_keys=True)}")
        return 0
    except (EntrypointError, RuntimeSourceError) as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"run_muzero failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except BaseException as exc:
        payload = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"run_muzero unexpected error: {exc!r}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1
    finally:
        if ray is not None and not args.keep_ray:
            try:
                ray.shutdown()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
