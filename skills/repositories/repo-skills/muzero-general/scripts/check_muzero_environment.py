#!/usr/bin/env python3
"""Check bundled or staged MuZero General source and Python dependencies without training."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

from _skill_runtime import RuntimeSourceError, add_source_to_syspath, resolve_source_root

REQUIRED_DEPS = ["numpy", "torch", "ray", "gym", "tensorboard", "nevergrad", "seaborn", "matplotlib"]
CORE_MODULES = ["muzero", "models", "self_play", "replay_buffer", "trainer", "shared_storage", "diagnose_model", "games.abstract_game"]
OPTIONAL_GAME_MODULES = ["games.cartpole", "games.tictactoe", "games.connect4", "games.gomoku", "games.twentyone", "games.simple_grid", "games.lunarlander", "games.atari", "games.breakout", "games.gridworld", "games.spiel"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MuZero General imports, optional game modules, and safe CPU smokes.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional MuZero General source root. Omit to use the bundled runtime/source snapshot.")
    parser.add_argument("--smoke", action="store_true", help="Run small game/model/MCTS/Ray smokes in addition to import checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print tracebacks for unexpected errors.")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> str:
    source_root, source_kind = resolve_source_root(repo_root, start=Path(__file__))
    add_source_to_syspath(source_root)
    return source_kind


def import_status(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"name": name, "ok": True, "version": getattr(mod, "__version__", None), "has_file": bool(getattr(mod, "__file__", None))}
    except BaseException as exc:
        return {"name": name, "ok": False, "error_type": type(exc).__name__, "error": str(exc).splitlines()[0] if str(exc) else repr(exc)}


def run_smoke() -> Dict[str, Any]:
    import numpy  # type: ignore
    import torch  # type: ignore
    import ray  # type: ignore
    import models  # type: ignore
    from games import cartpole, tictactoe  # type: ignore
    from self_play import GameHistory, MCTS  # type: ignore

    fc = cartpole.MuZeroConfig()
    fc.max_num_gpus = 0
    fc.train_on_gpu = False
    fc.selfplay_on_gpu = False
    fc.reanalyse_on_gpu = False
    fc.num_simulations = 1
    fc.training_steps = 0
    model = models.MuZeroNetwork(fc)
    obs = torch.zeros((1,) + tuple(fc.observation_shape), dtype=torch.float32)
    value, reward, policy, hidden = model.initial_inference(obs)
    assert policy.shape == (1, len(fc.action_space))
    model.recurrent_inference(hidden, torch.tensor([[fc.action_space[0]]]))

    rc = tictactoe.MuZeroConfig()
    rc.max_num_gpus = 0
    rc.train_on_gpu = False
    rc.selfplay_on_gpu = False
    rc.reanalyse_on_gpu = False
    rmodel = models.MuZeroNetwork(rc)
    robs = torch.zeros((1,) + tuple(rc.observation_shape), dtype=torch.float32)
    rv, rr, rp, rh = rmodel.initial_inference(robs)
    assert rp.shape == (1, len(rc.action_space))

    history = GameHistory()
    history.observation_history = [numpy.zeros(fc.observation_shape, dtype="float32")]
    history.action_history = [0]
    stacked = history.get_stacked_observations(0, 0, len(fc.action_space))
    root, info = MCTS(fc).run(model, stacked, fc.action_space, 0, False)

    ray.init(num_cpus=1, num_gpus=0, ignore_reinit_error=True, include_dashboard=False, log_to_driver=False)
    @ray.remote
    def add_one(x: int) -> int:
        return x + 1
    ray_value = ray.get(add_one.remote(1))
    ray.shutdown()

    return {
        "torch_cuda_available": torch.cuda.is_available(),
        "torch_cuda_device_count": torch.cuda.device_count(),
        "cartpole_policy_shape": list(policy.shape),
        "tictactoe_policy_shape": list(rp.shape),
        "mcts_root_children": sorted(root.children.keys()),
        "mcts_info": info,
        "ray_task": ray_value,
    }


def print_text(payload: Dict[str, Any]) -> None:
    print("MuZero General environment check")
    print(f"  repo_root_ok: {payload['repo_root_ok']}")
    print("  dependencies:")
    for row in payload["dependencies"]:
        print(f"    {row['name']}: {'ok' if row['ok'] else 'missing'} {row.get('version') or row.get('error', '')}")
    print("  core modules:")
    for row in payload["core_modules"]:
        print(f"    {row['name']}: {'ok' if row['ok'] else 'failed'} {row.get('error', '')}")
    print("  game modules:")
    for row in payload["game_modules"]:
        print(f"    {row['name']}: {'ok' if row['ok'] else 'optional-missing'} {row.get('error', '')}")
    if "smoke" in payload:
        print(f"  smoke: {payload['smoke']}")


def main() -> int:
    args = parse_args()
    try:
        source_kind = add_repo_root(args.repo_root)
        payload: Dict[str, Any] = {
            "ok": True,
            "source": source_kind,
            "repo_root_ok": True,
            "dependencies": [import_status(name) for name in REQUIRED_DEPS],
            "core_modules": [import_status(name) for name in CORE_MODULES],
            "game_modules": [import_status(name) for name in OPTIONAL_GAME_MODULES],
        }
        required_failed = [row for row in payload["dependencies"] + payload["core_modules"] if not row["ok"]]
        if required_failed:
            payload["ok"] = False
            payload["required_failures"] = required_failed
        if args.smoke and payload["ok"]:
            payload["smoke"] = run_smoke()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print_text(payload)
        return 0 if payload["ok"] else 2
    except RuntimeSourceError as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"check_muzero_environment failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except Exception as exc:
        payload = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"check_muzero_environment failed: {exc!r}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
