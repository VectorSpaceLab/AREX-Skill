#!/usr/bin/env python3
"""Validate a MuZero General game module without rendering or training."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

_SKILL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from _skill_runtime import RuntimeSourceError, add_source_to_syspath, resolve_source_root


class ValidationError(RuntimeError):
    """User-facing game validation failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MuZeroConfig/Game reset, legal_actions, and one step.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional MuZero General source root. Omit to use the bundled runtime/source snapshot.")
    parser.add_argument("--module", default="games.tictactoe", help="Game module import path, for example games.tictactoe.")
    parser.add_argument("--action", type=int, default=None, help="Action to step; default uses first legal action.")
    parser.add_argument("--skip-step", action="store_true", help="Only validate import/config/reset/legal actions.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print traceback on unexpected errors.")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> str:
    source_root, source_kind = resolve_source_root(repo_root, start=Path(__file__), required_markers=("games", "muzero.py"))
    add_source_to_syspath(source_root)
    return source_kind


def as_shape(value: Any) -> List[int]:
    import numpy  # type: ignore

    return list(numpy.array(value).shape)


def validate_module(module_name: str, action_override: int | None, skip_step: bool) -> Dict[str, Any]:
    module = importlib.import_module(module_name)
    if not hasattr(module, "MuZeroConfig"):
        raise ValidationError(f"{module_name} does not expose MuZeroConfig")
    if not hasattr(module, "Game"):
        raise ValidationError(f"{module_name} does not expose Game")
    cfg = module.MuZeroConfig()
    for attr in ["observation_shape", "action_space", "players"]:
        if not hasattr(cfg, attr):
            raise ValidationError(f"MuZeroConfig missing required field {attr}")
    expected_shape = tuple(cfg.observation_shape)
    if len(expected_shape) != 3:
        raise ValidationError(f"config.observation_shape must be rank 3; got {expected_shape}")
    action_space = list(cfg.action_space)
    if not action_space:
        raise ValidationError("config.action_space is empty")

    try:
        game = module.Game(seed=getattr(cfg, "seed", None))
    except TypeError:
        game = module.Game()
    try:
        obs = game.reset()
        reset_shape = tuple(as_shape(obs))
        if reset_shape != expected_shape:
            raise ValidationError(f"reset observation shape {reset_shape} does not match config.observation_shape {expected_shape}")
        legal = list(game.legal_actions())
        if not legal:
            raise ValidationError("game.legal_actions() returned an empty list at reset")
        if not set(legal).issubset(set(action_space)):
            raise ValidationError(f"legal actions {legal} are not a subset of config.action_space {action_space}")
        bad_indexes = [a for a in legal if a < 0 or a >= len(action_space)]
        if bad_indexes:
            raise ValidationError(f"legal actions must be contiguous tensor indexes in [0, {len(action_space)-1}], got {bad_indexes}")
        to_play = game.to_play() if hasattr(game, "to_play") else 0
        if to_play not in list(cfg.players):
            raise ValidationError(f"Game.to_play() returned {to_play}, not in config.players {list(cfg.players)}")
        result: Dict[str, Any] = {
            "module": module_name,
            "observation_shape": list(expected_shape),
            "action_space": action_space,
            "players": list(cfg.players),
            "network": getattr(cfg, "network", None),
            "opponent": getattr(cfg, "opponent", None),
            "reset_shape": list(reset_shape),
            "legal_actions": legal,
            "to_play": to_play,
        }
        if not skip_step:
            action = legal[0] if action_override is None else action_override
            if action not in legal:
                raise ValidationError(f"requested action {action} is not legal at reset; legal actions: {legal}")
            step_result = game.step(action)
            if not isinstance(step_result, tuple) or len(step_result) != 3:
                raise ValidationError("Game.step(action) must return (observation, reward, done)")
            next_obs, reward, done = step_result
            step_shape = tuple(as_shape(next_obs))
            if step_shape != expected_shape:
                raise ValidationError(f"step observation shape {step_shape} does not match config.observation_shape {expected_shape}")
            result.update({"step_action": action, "step_shape": list(step_shape), "reward_type": type(reward).__name__, "done_type": type(done).__name__})
        close = getattr(game, "close", None)
        if callable(close):
            close()
        return result
    finally:
        pass


def main() -> int:
    args = parse_args()
    try:
        source_kind = add_repo_root(args.repo_root)
        result = validate_module(args.module, args.action, args.skip_step)
        payload = {"ok": True, "source": source_kind, "result": result}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("MuZero game module validation OK")
            for key, value in result.items():
                print(f"  {key}: {value}")
        return 0
    except (ValidationError, RuntimeSourceError) as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"validate_game_module failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except BaseException as exc:
        payload = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"validate_game_module unexpected error: {exc!r}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
