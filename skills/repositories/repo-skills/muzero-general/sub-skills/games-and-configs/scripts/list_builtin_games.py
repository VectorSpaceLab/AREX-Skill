#!/usr/bin/env python3
"""List MuZero General built-in game modules and optional dependency status."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_SKILL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from _skill_runtime import RuntimeSourceError, add_source_to_syspath, resolve_source_root

KNOWN_GAME_MODULES = [
    "cartpole",
    "tictactoe",
    "connect4",
    "gomoku",
    "twentyone",
    "simple_grid",
    "lunarlander",
    "atari",
    "breakout",
    "gridworld",
    "spiel",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List MuZero General built-in games and config summaries.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional MuZero General source root. Omit to use the bundled runtime/source snapshot.")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format.")
    parser.add_argument("--include-abstract", action="store_true", help="Also report games.abstract_game.")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> str:
    source_root, source_kind = resolve_source_root(repo_root, start=Path(__file__), required_markers=("games", "muzero.py"))
    add_source_to_syspath(source_root)
    return source_kind


def safe_config_summary(module: Any) -> Dict[str, Any]:
    if not hasattr(module, "MuZeroConfig"):
        return {}
    cfg = module.MuZeroConfig()
    out: Dict[str, Any] = {}
    for name in [
        "observation_shape",
        "action_space",
        "players",
        "network",
        "opponent",
        "training_steps",
        "num_simulations",
        "num_workers",
        "stacked_observations",
        "train_on_gpu",
        "selfplay_on_gpu",
    ]:
        if hasattr(cfg, name):
            value = getattr(cfg, name)
            if name in {"observation_shape", "players", "action_space"}:
                value = list(value)
            out[name] = value
    return out


def inspect_module(short_name: str) -> Dict[str, Any]:
    module_name = "games." + short_name
    result: Dict[str, Any] = {"name": short_name, "module": module_name}
    try:
        module = importlib.import_module(module_name)
        result.update({"status": "ok", "config": safe_config_summary(module), "has_game": hasattr(module, "Game")})
    except BaseException as exc:
        result.update({"status": "unavailable", "error_type": type(exc).__name__, "error": str(exc).splitlines()[0] if str(exc) else repr(exc)})
    return result


def print_table(rows: List[Dict[str, Any]]) -> None:
    header = ["game", "status", "shape", "actions", "players", "network", "opponent", "note"]
    print("\t".join(header))
    for row in rows:
        cfg = row.get("config") or {}
        shape = tuple(cfg.get("observation_shape", [])) if cfg.get("observation_shape") is not None else ""
        actions = len(cfg.get("action_space", [])) if cfg.get("action_space") is not None else ""
        players = len(cfg.get("players", [])) if cfg.get("players") is not None else ""
        note = "" if row["status"] == "ok" else f"{row.get('error_type')}: {row.get('error')}"
        print(
            "\t".join(
                str(x)
                for x in [
                    row["name"],
                    row["status"],
                    shape,
                    actions,
                    players,
                    cfg.get("network", ""),
                    cfg.get("opponent", ""),
                    note,
                ]
            )
        )


def main() -> int:
    args = parse_args()
    try:
        source_kind = add_repo_root(args.repo_root)
    except RuntimeSourceError as exc:
        raise SystemExit(str(exc)) from exc
    modules = (["abstract_game"] if args.include_abstract else []) + KNOWN_GAME_MODULES
    rows = [inspect_module(name) for name in modules]
    if args.format == "json":
        print(json.dumps({"source": source_kind, "games": rows}, indent=2, sort_keys=True))
    else:
        print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
