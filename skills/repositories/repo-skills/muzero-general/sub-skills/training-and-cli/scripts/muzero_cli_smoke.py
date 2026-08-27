#!/usr/bin/env python3
"""
Safe MuZero General CLI/API smoke helper.

Purpose:
- Import the skill-bundled MuZero General source snapshot by default, or an optional --repo-root override.
- Apply CPU-safe config overrides by default.
- Construct MuZero and report key config/checkpoint facts.
- Optionally run a deliberately tiny training call only when --run-train is supplied.

Examples:
  python muzero_cli_smoke.py --game tictactoe --json
  python muzero_cli_smoke.py --game cartpole --training-steps 0
  python muzero_cli_smoke.py --repo-root /path/to/staged-muzero-source --game tictactoe --json

This script does not render, download data, prompt for input, or run real training by default.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

_SKILL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from _skill_runtime import RuntimeSourceError, add_source_to_syspath, resolve_source_root


class SmokeError(RuntimeError):
    """User-facing smoke failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe MuZero General constructor/CLI smoke check.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional MuZero General source root. Omit to use the bundled runtime/source snapshot.")
    parser.add_argument("--game", default="tictactoe", help="Game module name to pass to MuZero, for example tictactoe or cartpole.")
    parser.add_argument("--training-steps", type=int, default=0, help="training_steps override. Default 0 keeps the smoke non-training.")
    parser.add_argument("--num-simulations", type=int, default=1, help="num_simulations override for bounded MCTS setup. Default 1.")
    parser.add_argument("--max-moves", type=int, default=1, help="max_moves override for bounded test/train paths. Default 1.")
    parser.add_argument("--num-workers", type=int, default=1, help="num_workers override. Default 1.")
    parser.add_argument("--config-json", default=None, help="Additional JSON object merged after safe defaults.")
    parser.add_argument("--allow-gpu", action="store_true", help="Do not force CPU-safe GPU flags. Use only when GPU scheduling is intentional.")
    parser.add_argument("--run-train", action="store_true", help="Actually call MuZero.train(log_in_tensorboard=False). Default only constructs MuZero.")
    parser.add_argument("--log-in-tensorboard", action="store_true", help="If --run-train is used, pass log_in_tensorboard=True.")
    parser.add_argument("--keep-ray", action="store_true", help="Do not call ray.shutdown() at the end.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print traceback on unexpected failures.")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> str:
    source_root, source_kind = resolve_source_root(repo_root, start=Path(__file__))
    add_source_to_syspath(source_root)
    return source_kind


def load_extra_config(text: str | None) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SmokeError(f"--config-json is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SmokeError("--config-json must decode to a JSON object")
    return value


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
    summary: Dict[str, Any] = {}
    for field in fields:
        if hasattr(config, field):
            value = getattr(config, field)
            if field == "results_path":
                value = str(value)
            if field == "action_space":
                value = list(value)
            if field in {"observation_shape", "players"}:
                value = list(value)
            summary[field] = value
    return summary


def main() -> int:
    args = parse_args()
    ray = None
    try:
        source_kind = add_repo_root(args.repo_root)
        from muzero import MuZero  # type: ignore
        import ray as ray_module  # type: ignore

        ray = ray_module
        config: Dict[str, Any] = {
            "training_steps": args.training_steps,
            "num_simulations": args.num_simulations,
            "max_moves": args.max_moves,
            "num_workers": args.num_workers,
            "save_model": False,
        }
        if not args.allow_gpu:
            config.update(
                {
                    "max_num_gpus": 0,
                    "train_on_gpu": False,
                    "selfplay_on_gpu": False,
                    "reanalyse_on_gpu": False,
                }
            )
        config.update(load_extra_config(args.config_json))
        if config.get("training_steps", 0) < 0:
            raise SmokeError("training_steps must be >= 0")
        if args.run_train and config.get("training_steps", 0) > 100:
            raise SmokeError("This smoke helper refuses --run-train with training_steps > 100")

        muzero = MuZero(args.game, config)
        trained = False
        if args.run_train:
            muzero.train(log_in_tensorboard=args.log_in_tensorboard)
            trained = True
            muzero.terminate_workers()

        result = {
            "ok": True,
            "source": source_kind,
            "game": args.game,
            "constructed": True,
            "trained": trained,
            "num_gpus": muzero.num_gpus,
            "config": summarize_config(muzero.config),
            "checkpoint_keys": sorted(muzero.checkpoint.keys()),
            "weights_type": type(muzero.checkpoint.get("weights")).__name__,
            "replay_buffer_games": len(muzero.replay_buffer),
        }
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("MuZero constructor smoke OK")
            print(f"  game: {result['game']}")
            print(f"  trained: {result['trained']}")
            print(f"  num_gpus: {result['num_gpus']}")
            print(f"  config: {json.dumps(result['config'], sort_keys=True)}")
            print(f"  checkpoint_keys: {', '.join(result['checkpoint_keys'])}")
        return 0
    except (SmokeError, RuntimeSourceError) as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"muzero_cli_smoke failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except Exception as exc:
        payload = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"muzero_cli_smoke unexpected error: {exc!r}", file=sys.stderr)
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
