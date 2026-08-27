#!/usr/bin/env python3
"""Bounded PettingZoo AEC/Parallel environment smoke loop.

The script intentionally has no default environment because many PettingZoo
families require optional dependencies. Pass an installed module and factory,
for example:

    python smoke_env_loop.py --module pettingzoo.classic.rps_v2 --factory env --api aec
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any, Optional


RENDER_MODES = ("none", "human", "rgb_array", "ansi")


class SmokeError(RuntimeError):
    """Expected user-facing smoke-check failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a bounded random PettingZoo AEC or Parallel environment loop.",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Import path for the environment module, such as pettingzoo.classic.rps_v2.",
    )
    parser.add_argument(
        "--factory",
        required=True,
        help="Factory attribute on the module, commonly env or parallel_env.",
    )
    parser.add_argument(
        "--api",
        choices=("aec", "parallel"),
        required=True,
        help="Interaction API to smoke test.",
    )
    parser.add_argument(
        "--cycles",
        type=positive_int,
        default=3,
        help="Bounded cycles to run; AEC uses cycles multiplied by possible live agents.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed passed to reset(seed=...) and action spaces when supported.",
    )
    parser.add_argument(
        "--render-mode",
        choices=RENDER_MODES,
        default="none",
        help="Render mode to pass at construction; none omits render_mode.",
    )
    return parser.parse_args()


def positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    if value > 10_000:
        raise argparse.ArgumentTypeError("must be <= 10000 for a bounded smoke run")
    return value


def import_factory(module_path: str, factory_name: str):
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown dependency"
        raise SmokeError(
            f"Could not import {module_path!r}; missing module {missing!r}. "
            "PettingZoo base installs do not include every optional family dependency. "
            "Install the matching optional extra or choose a module whose dependencies are installed."
        ) from exc
    except ImportError as exc:
        raise SmokeError(
            f"Could not import {module_path!r}: {exc}. This often means an optional "
            "environment-family dependency is missing."
        ) from exc

    try:
        factory = getattr(module, factory_name)
    except AttributeError as exc:
        raise SmokeError(
            f"Module {module_path!r} does not expose factory {factory_name!r}. "
            "Use the module's AEC factory, usually 'env', or Parallel factory, usually 'parallel_env'."
        ) from exc
    return factory


def make_env(factory, render_mode: str):
    kwargs = {}
    if render_mode != "none":
        kwargs["render_mode"] = render_mode
    try:
        return factory(**kwargs)
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown dependency"
        raise SmokeError(
            f"Factory failed because optional dependency {missing!r} is missing. "
            "Install the matching PettingZoo optional extra for this environment family."
        ) from exc
    except ImportError as exc:
        raise SmokeError(
            f"Factory failed during optional dependency import: {exc}. "
            "Install the matching PettingZoo optional extra for this environment family."
        ) from exc
    except TypeError as exc:
        raise SmokeError(
            f"Factory could not be called with arguments {kwargs}: {exc}. "
            "Check whether the selected factory needs environment-specific constructor parameters."
        ) from exc


def action_mask_from(observation: Any, info: Any) -> Optional[Any]:
    if isinstance(info, Mapping) and "action_mask" in info:
        return info["action_mask"]
    if isinstance(observation, Mapping) and "action_mask" in observation:
        return observation["action_mask"]
    return None


def mask_has_valid_action(mask: Any) -> bool:
    if mask is None:
        return True
    any_method = getattr(mask, "any", None)
    if callable(any_method):
        try:
            return bool(any_method())
        except Exception:
            pass
    if isinstance(mask, Mapping):
        return any(mask_has_valid_action(value) for value in mask.values())
    if isinstance(mask, Sequence) and not isinstance(mask, (str, bytes, bytearray)):
        return any(mask_has_valid_action(value) for value in mask)
    try:
        return bool(mask)
    except Exception:
        return True


def sample_action(action_space: Any, mask: Any, agent: Any) -> tuple[Any, bool]:
    if mask is not None and not mask_has_valid_action(mask):
        raise SmokeError(
            f"Action mask for live agent {agent!r} has no valid actions. "
            "Check whether the agent is actually terminated/truncated or whether the mask source is stale."
        )
    if mask is None:
        return action_space.sample(), False
    try:
        return action_space.sample(mask), True
    except TypeError:
        return action_space.sample(), False
    except Exception as exc:
        raise SmokeError(
            f"Masked sampling failed for agent {agent!r}: {exc}. "
            "Check the mask shape and type against the agent action space."
        ) from exc


def seed_action_spaces(env: Any, seed: int) -> int:
    agents = list(getattr(env, "possible_agents", []) or getattr(env, "agents", []))
    seeded = 0
    for index, agent in enumerate(agents):
        try:
            env.action_space(agent).seed(seed + index)
            seeded += 1
        except Exception:
            continue
    return seeded


def render_once(env: Any, render_mode: str) -> Optional[str]:
    if render_mode == "none":
        return None
    try:
        frame = env.render()
    except Exception as exc:
        raise SmokeError(
            f"render() failed in render_mode={render_mode!r}: {exc}. "
            "Use --render-mode none for headless smoke checks or choose a supported non-GUI mode."
        ) from exc
    if frame is None:
        return "None"
    if isinstance(frame, str):
        return f"str[{len(frame)}]"
    shape = getattr(frame, "shape", None)
    if shape is not None:
        return f"{type(frame).__name__}{tuple(shape)}"
    if isinstance(frame, list):
        return f"list[{len(frame)}]"
    return type(frame).__name__


def run_aec(env: Any, cycles: int, seed: int, render_mode: str) -> dict[str, Any]:
    env.reset(seed=seed)
    seeded_spaces = seed_action_spaces(env, seed)
    initial_agents = list(getattr(env, "agents", []))
    max_agents = max(1, len(getattr(env, "possible_agents", []) or initial_agents))
    max_iter = cycles * max_agents
    total_reward = 0.0
    agent_turns = 0
    none_actions = 0
    masked_actions = 0
    render_sample = render_once(env, render_mode)

    for agent in env.agent_iter(max_iter=max_iter):
        observation, reward, termination, truncation, info = env.last()
        total_reward += float(reward or 0.0)
        agent_turns += 1
        if termination or truncation:
            action = None
            none_actions += 1
        else:
            mask = action_mask_from(observation, info)
            action, used_mask = sample_action(env.action_space(agent), mask, agent)
            masked_actions += int(used_mask)
        env.step(action)

    return {
        "api": "aec",
        "cycles_requested": cycles,
        "max_agent_turns": max_iter,
        "agent_turns": agent_turns,
        "initial_agents": [str(agent) for agent in initial_agents],
        "remaining_agents": [str(agent) for agent in getattr(env, "agents", [])],
        "none_actions": none_actions,
        "masked_actions": masked_actions,
        "seeded_action_spaces": seeded_spaces,
        "total_reward": total_reward,
        "render_sample": render_sample,
    }


def run_parallel(env: Any, cycles: int, seed: int, render_mode: str) -> dict[str, Any]:
    observations, infos = env.reset(seed=seed)
    seeded_spaces = seed_action_spaces(env, seed)
    initial_agents = list(getattr(env, "agents", []))
    total_reward = 0.0
    parallel_steps = 0
    masked_actions = 0
    render_sample = render_once(env, render_mode)

    for _ in range(cycles):
        live_agents = list(getattr(env, "agents", []))
        if not live_agents:
            break
        actions = {}
        for agent in live_agents:
            observation = observations.get(agent) if isinstance(observations, Mapping) else None
            info = infos.get(agent, {}) if isinstance(infos, Mapping) else {}
            mask = action_mask_from(observation, info)
            action, used_mask = sample_action(env.action_space(agent), mask, agent)
            actions[agent] = action
            masked_actions += int(used_mask)
        observations, rewards, terminations, truncations, infos = env.step(actions)
        parallel_steps += 1
        if isinstance(rewards, Mapping):
            total_reward += sum(float(value or 0.0) for value in rewards.values())
        if render_sample is None:
            render_sample = render_once(env, render_mode)

    return {
        "api": "parallel",
        "cycles_requested": cycles,
        "parallel_steps": parallel_steps,
        "initial_agents": [str(agent) for agent in initial_agents],
        "remaining_agents": [str(agent) for agent in getattr(env, "agents", [])],
        "masked_actions": masked_actions,
        "seeded_action_spaces": seeded_spaces,
        "total_reward": total_reward,
        "render_sample": render_sample,
    }


def main() -> int:
    args = parse_args()
    env = None
    try:
        factory = import_factory(args.module, args.factory)
        env = make_env(factory, args.render_mode)
        if args.api == "aec":
            summary = run_aec(env, args.cycles, args.seed, args.render_mode)
        else:
            summary = run_parallel(env, args.cycles, args.seed, args.render_mode)
        summary.update(
            {
                "module": args.module,
                "factory": args.factory,
                "render_mode": args.render_mode,
                "status": "ok",
            }
        )
        print(json.dumps(summary, sort_keys=True))
        return 0
    except SmokeError as exc:
        print(f"smoke_env_loop: {exc}", file=sys.stderr)
        return 2
    finally:
        if env is not None:
            try:
                env.close()
            except Exception as exc:
                print(f"smoke_env_loop: close() raised {exc!r}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
