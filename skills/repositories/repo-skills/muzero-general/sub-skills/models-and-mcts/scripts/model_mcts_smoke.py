#!/usr/bin/env python3
"""
Safe MuZero General model/MCTS smoke checker.

Purpose:
- Import the skill-bundled MuZero General source snapshot by default, or an optional --repo-root override.
- Instantiate MuZeroNetwork for verified FC/ResNet cases or a custom game module.
- Check initial_inference, recurrent_inference, support transforms, GameHistory
  stacking, legal-action validation, and a tiny MCTS root expansion.

Examples:
  python model_mcts_smoke.py --case both --num-simulations 1
  python model_mcts_smoke.py --case custom --game-module games.tictactoe --network fullyconnected --json
  python model_mcts_smoke.py --repo-root /path/to/staged-muzero-source --case both --num-simulations 1

This script does not train, save checkpoints, download data, render, or start Ray.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_SKILL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from _skill_runtime import RuntimeSourceError, add_source_to_syspath, resolve_source_root


class SmokeError(RuntimeError):
    """A user-facing smoke-check failure with an actionable message."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe MuZero General network/MCTS tensor smoke check."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional MuZero General source root. Omit to use the bundled runtime/source snapshot.",
    )
    parser.add_argument(
        "--case",
        choices=["cartpole-fc", "tictactoe-resnet", "both", "custom"],
        default="both",
        help="Verified built-in case(s), or custom for --game-module. Default: both.",
    )
    parser.add_argument(
        "--game-module",
        default=None,
        help="Import path for a module exposing MuZeroConfig and optionally Game, used with --case custom (example: games.tictactoe).",
    )
    parser.add_argument(
        "--network",
        choices=["config", "fullyconnected", "resnet"],
        default="config",
        help="Network override for --case custom; config keeps module MuZeroConfig.network.",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "auto"],
        default="cpu",
        help="Device for model/tensors. Default cpu avoids accidental GPU use.",
    )
    parser.add_argument(
        "--num-simulations",
        type=int,
        default=2,
        help="Tiny MCTS simulation count. Use 0 to skip MCTS. Default: 2.",
    )
    parser.add_argument(
        "--stacked-observations",
        type=int,
        default=None,
        help="Override config.stacked_observations for the smoke shape check.",
    )
    parser.add_argument(
        "--legal-actions",
        default=None,
        help="Comma-separated legal actions for MCTS root expansion; default uses Game.legal_actions() or config.action_space.",
    )
    parser.add_argument(
        "--add-exploration-noise",
        action="store_true",
        help="Enable root Dirichlet exploration noise during MCTS.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print tracebacks for unexpected exceptions.",
    )
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> str:
    source_root, source_kind = resolve_source_root(repo_root, start=Path(__file__), required_markers=("models.py", "self_play.py", "games"))
    add_source_to_syspath(source_root)
    return source_kind


def parse_action_csv(text: Optional[str]) -> Optional[List[int]]:
    if text is None:
        return None
    if text.strip() == "":
        return []
    try:
        return [int(part.strip()) for part in text.split(",") if part.strip() != ""]
    except ValueError as exc:
        raise SmokeError("--legal-actions must be a comma-separated list of integers") from exc


def choose_cases(args: argparse.Namespace) -> List[Tuple[str, str, str]]:
    if args.case == "both":
        return [
            ("cartpole-fc", "games.cartpole", "fullyconnected"),
            ("tictactoe-resnet", "games.tictactoe", "resnet"),
        ]
    if args.case == "cartpole-fc":
        return [("cartpole-fc", "games.cartpole", "fullyconnected")]
    if args.case == "tictactoe-resnet":
        return [("tictactoe-resnet", "games.tictactoe", "resnet")]
    if not args.game_module:
        raise SmokeError("--case custom requires --game-module")
    return [("custom", args.game_module, args.network)]


def resolve_device(torch_module: Any, requested: str):
    if requested == "auto":
        return torch_module.device("cuda" if torch_module.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch_module.cuda.is_available():
        raise SmokeError("--device cuda was requested but torch.cuda.is_available() is false")
    return torch_module.device(requested)


def make_config(module: Any, network: str, args: argparse.Namespace) -> Any:
    if not hasattr(module, "MuZeroConfig"):
        raise SmokeError("game module must expose MuZeroConfig")
    config = module.MuZeroConfig()
    if network != "config":
        config.network = network
    if args.stacked_observations is not None:
        if args.stacked_observations < 0:
            raise SmokeError("--stacked-observations must be >= 0")
        config.stacked_observations = args.stacked_observations
    if args.num_simulations < 0:
        raise SmokeError("--num-simulations must be >= 0")
    config.num_simulations = args.num_simulations
    return config


def instantiate_game(module: Any, config: Any):
    if not hasattr(module, "Game"):
        return None, None, list(config.action_space), config.players[0] if config.players else 0
    game = module.Game(seed=getattr(config, "seed", None))
    observation = game.reset()
    legal_actions = list(game.legal_actions())
    to_play = game.to_play() if hasattr(game, "to_play") else (config.players[0] if config.players else 0)
    return game, observation, legal_actions, to_play


def fallback_observation(numpy_module: Any, config: Any):
    return numpy_module.zeros(tuple(config.observation_shape), dtype="float32")


def validate_base_observation(numpy_module: Any, observation: Any, config: Any) -> Tuple[int, ...]:
    shape = tuple(numpy_module.array(observation).shape)
    expected = tuple(config.observation_shape)
    if len(shape) != 3:
        raise SmokeError(f"base observation must be rank 3 before stacking; got shape {shape}")
    if shape != expected:
        raise SmokeError(f"base observation shape {shape} does not match config.observation_shape {expected}")
    return shape


def validate_legal_actions(legal_actions: Iterable[int], config: Any) -> List[int]:
    actions = list(legal_actions)
    if not actions:
        raise SmokeError("legal actions are empty; MCTS.run asserts legal_actions is non-empty")
    action_space = list(config.action_space)
    if not set(actions).issubset(set(action_space)):
        raise SmokeError(
            f"legal actions {actions} must be a subset of config.action_space {action_space}"
        )
    action_space_size = len(action_space)
    bad_indexes = [a for a in actions if a < 0 or a >= action_space_size]
    if bad_indexes:
        raise SmokeError(
            "MuZero General uses action integers as policy/action-one-hot indexes; "
            f"actions must be in [0, {action_space_size - 1}], got {bad_indexes}"
        )
    return actions


def build_stacked_observation(numpy_module: Any, GameHistory: Any, base_observation: Any, config: Any):
    base = numpy_module.array(base_observation).copy()
    history = GameHistory()
    count = int(config.stacked_observations) + 1
    history.observation_history = [base.copy() for _ in range(count)]
    first_action = list(config.action_space)[0] if list(config.action_space) else 0
    history.action_history = [first_action for _ in range(count)]
    return history.get_stacked_observations(
        count - 1,
        int(config.stacked_observations),
        len(config.action_space),
    )


def tensor_shape(tensor: Any) -> List[int]:
    return list(tensor.detach().shape)


def run_one_case(label: str, module_name: str, network: str, args: argparse.Namespace, libs: Dict[str, Any]) -> Dict[str, Any]:
    numpy = libs["numpy"]
    torch = libs["torch"]
    models = libs["models"]
    GameHistory = libs["GameHistory"]
    MCTS = libs["MCTS"]

    module = importlib.import_module(module_name)
    config = make_config(module, network, args)
    device = resolve_device(torch, args.device)

    game = None
    try:
        game, base_observation, legal_actions, to_play = instantiate_game(module, config)
        if base_observation is None:
            base_observation = fallback_observation(numpy, config)
    except Exception as exc:
        raise SmokeError(f"failed to instantiate/reset Game from {module_name}: {exc}") from exc

    requested_legal = parse_action_csv(args.legal_actions)
    if requested_legal is not None:
        legal_actions = requested_legal
    base_shape = validate_base_observation(numpy, base_observation, config)
    legal_actions = validate_legal_actions(legal_actions, config)
    stacked_observation = build_stacked_observation(numpy, GameHistory, base_observation, config)

    model = models.MuZeroNetwork(config).to(device)
    model.eval()

    obs_tensor = torch.tensor(stacked_observation).float().unsqueeze(0).to(device)
    with torch.no_grad():
        value, reward, policy_logits, hidden_state = model.initial_inference(obs_tensor)
        recurrent_action = torch.tensor([[legal_actions[0]]], device=device)
        next_value, next_reward, next_policy_logits, next_hidden_state = model.recurrent_inference(
            hidden_state, recurrent_action
        )
        decoded_value = models.support_to_scalar(value, config.support_size)
        zero_support = models.scalar_to_support(torch.zeros((1, 1), device=device), config.support_size)

    result: Dict[str, Any] = {
        "case": label,
        "module": module_name,
        "network": config.network,
        "device": str(device),
        "base_observation_shape": list(base_shape),
        "stacked_observation_shape": list(numpy.array(stacked_observation).shape),
        "action_space": list(config.action_space),
        "legal_actions": legal_actions,
        "to_play": to_play,
        "support_size": config.support_size,
        "initial_shapes": {
            "value": tensor_shape(value),
            "reward": tensor_shape(reward),
            "policy_logits": tensor_shape(policy_logits),
            "hidden_state": tensor_shape(hidden_state),
        },
        "recurrent_shapes": {
            "value": tensor_shape(next_value),
            "reward": tensor_shape(next_reward),
            "policy_logits": tensor_shape(next_policy_logits),
            "hidden_state": tensor_shape(next_hidden_state),
        },
        "support_shapes": {
            "support_to_scalar_value": tensor_shape(decoded_value),
            "scalar_to_support_zero": tensor_shape(zero_support),
        },
    }

    if args.num_simulations > 0:
        with torch.no_grad():
            root, info = MCTS(config).run(
                model,
                stacked_observation,
                legal_actions,
                to_play,
                args.add_exploration_noise,
            )
        result["mcts"] = {
            "root_children": sorted(root.children.keys()),
            "root_visit_count": root.visit_count,
            "child_visit_counts": {str(a): child.visit_count for a, child in root.children.items()},
            "child_priors": {str(a): child.prior for a, child in root.children.items()},
            "root_value": root.value(),
            "extra_info": info,
        }
    else:
        result["mcts"] = "skipped"

    if game is not None and hasattr(game, "close"):
        try:
            game.close()
        except Exception:
            pass
    return result


def print_text(results: List[Dict[str, Any]]) -> None:
    print("MuZero General model/MCTS smoke OK")
    for result in results:
        print(f"\n[{result['case']}] {result['module']} network={result['network']} device={result['device']}")
        print(f"  base_observation_shape: {result['base_observation_shape']}")
        print(f"  stacked_observation_shape: {result['stacked_observation_shape']}")
        print(f"  action_space: {result['action_space']} legal_actions: {result['legal_actions']}")
        print(f"  initial_shapes: {result['initial_shapes']}")
        print(f"  recurrent_shapes: {result['recurrent_shapes']}")
        print(f"  support_shapes: {result['support_shapes']}")
        print(f"  mcts: {result['mcts']}")


def main() -> int:
    args = parse_args()
    try:
        source_kind = add_repo_root(args.repo_root)
        # Import heavy/repo modules only after parsing, so --help works without dependencies.
        import numpy  # type: ignore
        import torch  # type: ignore
        import models  # type: ignore
        from self_play import GameHistory, MCTS  # type: ignore

        libs = {
            "numpy": numpy,
            "torch": torch,
            "models": models,
            "GameHistory": GameHistory,
            "MCTS": MCTS,
        }
        results = [run_one_case(label, module_name, network, args, libs) for label, module_name, network in choose_cases(args)]
        if args.json:
            print(json.dumps({"ok": True, "source": source_kind, "results": results}, indent=2, sort_keys=True))
        else:
            print_text(results)
        return 0
    except (SmokeError, RuntimeSourceError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"model_mcts_smoke failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2
    except Exception as exc:  # Keep unexpected dependency/API errors readable.
        if args.json:
            print(json.dumps({"ok": False, "error": repr(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"model_mcts_smoke unexpected error: {exc!r}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
