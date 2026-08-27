#!/usr/bin/env python3
"""Inspect MuZero General checkpoint and replay-buffer files without running a model."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Iterable


class InspectError(RuntimeError):
    """User-facing checkpoint inspection failure."""


EXPECTED_CHECKPOINT_KEYS = [
    "weights",
    "optimizer_state",
    "total_reward",
    "muzero_reward",
    "opponent_reward",
    "episode_length",
    "mean_value",
    "training_step",
    "lr",
    "total_loss",
    "value_loss",
    "reward_loss",
    "policy_loss",
    "num_played_games",
    "num_played_steps",
    "num_reanalysed_games",
    "terminate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect MuZero General model.checkpoint / replay_buffer.pkl metadata.")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Path to model.checkpoint or model.weights.")
    parser.add_argument("--replay-buffer", type=Path, default=None, help="Optional path to replay_buffer.pkl.")
    parser.add_argument("--show-weight-keys", type=int, default=12, help="Number of state-dict weight keys to show. Default 12.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print traceback on unexpected errors.")
    return parser.parse_args()


def load_torch_file(path: Path) -> Any:
    if not path.is_file():
        raise InspectError(f"checkpoint file not found: {path}")
    import torch  # type: ignore

    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def summarize_weights(weights: Any, limit: int) -> Dict[str, Any]:
    if weights is None:
        return {"type": "NoneType", "num_keys": 0, "sample_keys": []}
    if isinstance(weights, dict):
        keys = list(weights.keys())
        shape_hints: Dict[str, Any] = {}
        for key in keys[:limit]:
            value = weights[key]
            shape = getattr(value, "shape", None)
            shape_hints[str(key)] = list(shape) if shape is not None else type(value).__name__
        return {"type": "dict", "num_keys": len(keys), "sample_keys": [str(k) for k in keys[:limit]], "sample_shapes": shape_hints}
    return {"type": type(weights).__name__, "repr": repr(weights)[:200]}


def summarize_checkpoint(obj: Any, weight_key_limit: int) -> Dict[str, Any]:
    if isinstance(obj, dict):
        keys = list(obj.keys())
        missing = [key for key in EXPECTED_CHECKPOINT_KEYS if key not in obj]
        counters = {key: obj.get(key) for key in ["training_step", "num_played_games", "num_played_steps", "num_reanalysed_games", "lr"] if key in obj}
        return {
            "type": "dict",
            "keys": [str(k) for k in keys],
            "expected_keys_present": [key for key in EXPECTED_CHECKPOINT_KEYS if key in obj],
            "expected_keys_missing": missing,
            "counters": counters,
            "weights": summarize_weights(obj.get("weights"), weight_key_limit),
            "optimizer_state_type": type(obj.get("optimizer_state")).__name__ if "optimizer_state" in obj else None,
        }
    return {"type": type(obj).__name__, "repr": repr(obj)[:500]}


def summarize_replay(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise InspectError(f"replay buffer file not found: {path}")
    with path.open("rb") as handle:
        obj = pickle.load(handle)
    if not isinstance(obj, dict):
        return {"type": type(obj).__name__, "repr": repr(obj)[:500]}
    summary: Dict[str, Any] = {"type": "dict", "keys": [str(k) for k in obj.keys()]}
    for key in ["num_played_games", "num_played_steps", "num_reanalysed_games"]:
        if key in obj:
            summary[key] = obj[key]
    buffer = obj.get("buffer")
    if isinstance(buffer, dict):
        summary["buffer_num_games"] = len(buffer)
        summary["buffer_sample_keys"] = [str(k) for k in list(buffer.keys())[:10]]
    else:
        summary["buffer_type"] = type(buffer).__name__
    return summary


def print_text(payload: Dict[str, Any]) -> None:
    print("MuZero checkpoint inspection")
    if "checkpoint" in payload:
        cp = payload["checkpoint"]
        print(f"  checkpoint type: {cp.get('type')}")
        print(f"  keys: {cp.get('keys')}")
        print(f"  missing expected keys: {cp.get('expected_keys_missing')}")
        print(f"  counters: {cp.get('counters')}")
        print(f"  weights: {cp.get('weights')}")
    if "replay_buffer" in payload:
        rb = payload["replay_buffer"]
        print(f"  replay buffer: {rb}")


def main() -> int:
    args = parse_args()
    if args.checkpoint is None and args.replay_buffer is None:
        print("inspect_checkpoint failed: provide --checkpoint and/or --replay-buffer", file=sys.stderr)
        return 2
    try:
        payload: Dict[str, Any] = {"ok": True}
        if args.checkpoint is not None:
            payload["checkpoint"] = summarize_checkpoint(load_torch_file(args.checkpoint.expanduser()), args.show_weight_keys)
        if args.replay_buffer is not None:
            payload["replay_buffer"] = summarize_replay(args.replay_buffer.expanduser())
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print_text(payload)
        return 0
    except InspectError as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"inspect_checkpoint failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except Exception as exc:
        payload = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"inspect_checkpoint unexpected error: {exc!r}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
