#!/usr/bin/env python3
"""Run bounded PettingZoo compliance checks for a module factory.

Examples:
    python run_compliance_checks.py --target my_pkg.my_env_v0:env --api aec --checks api,seed --cycles 50
    python run_compliance_checks.py --target my_pkg.my_env_v0:parallel_env --api parallel --checks api,seed --cycles 50
    python run_compliance_checks.py --target my_pkg.my_env_v0:env --api aec --checks render --no-render-human
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import traceback
from collections.abc import Callable, Mapping
from typing import Any

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

CHECKS = ("api", "seed", "render", "max-cycles")
MAX_CYCLES = 10_000
OMIT = object()

MISSING_PACKAGE_HINTS = {
    "numpy": "Install PettingZoo's base dependencies before running compliance checks.",
    "gymnasium": "Install PettingZoo's base dependencies before running compliance checks.",
    "pygame": "Install the smallest PettingZoo optional family extra needed by the target environment, or avoid GUI/render checks in base installs.",
    "rlcard": "Install the Classic extra for RLCard-backed Classic environments.",
    "multi_agent_ale_py": "Install the Atari extra and configure ROMs only if Atari validation is explicitly in scope.",
    "pymunk": "Install the Butterfly or SISL extra only if the target environment requires it.",
    "Box2D": "Install the SISL extra and any platform build prerequisites only if SISL validation is in scope.",
    "box2d": "Install the SISL extra and any platform build prerequisites only if SISL validation is in scope.",
    "shimmy": "Install the Classic extra for Shimmy/OpenSpiel-backed Classic environments.",
    "pyspiel": "Install the Classic extra for OpenSpiel-backed environments.",
}

HINT_PATTERNS = (
    (
        "exact same space object",
        "Cache observation_space/action_space objects with dictionaries or functools.lru_cache(maxsize=None).",
    ),
    (
        "agent cannot be revived",
        "Do not re-add a terminated/truncated agent name during the same episode; use a new unique generated name if needed.",
    ),
    (
        "resurect",
        "Do not re-add a terminated/truncated agent name during the same episode; use a new unique generated name if needed.",
    ),
    (
        "live agent was not given",
        "Parallel step outputs must include each currently live agent in the returned dictionaries.",
    ),
    (
        "dead last turn",
        "Remove dead agents from env.agents and do not keep returning values for agents that already terminated/truncated.",
    ),
    (
        "env.agents",
        "Keep env.agents synchronized with live agents after every step and reset.",
    ),
    (
        "rewards, terminations, truncations, infos and agents",
        "AEC bookkeeping dictionaries must have the same keys as env.agents after each step/reset.",
    ),
    (
        "step() must not return anything",
        "AECEnv.step(action) must mutate state and return None; only ParallelEnv.step(actions) returns observation/reward dictionaries.",
    ),
    (
        "out of bounds observation",
        "Return observations contained by observation_space(agent), including matching dict keys and dtypes.",
    ),
    (
        "incorrect observation",
        "Use reset(seed=...) to seed all environment randomness and rebuild deterministic episode state.",
    ),
    (
        "incorrect reward",
        "Use reset(seed=...) to seed all environment randomness and rebuild deterministic episode state.",
    ),
    (
        "incorrect termination",
        "Use reset(seed=...) to seed all environment randomness and rebuild deterministic episode state.",
    ),
    (
        "incorrect truncation",
        "Use reset(seed=...) to seed all environment randomness and rebuild deterministic episode state.",
    ),
    (
        "incorrect info",
        "Make info dictionaries deterministic under identical seeds.",
    ),
    (
        "incorrect action mask",
        "Make action masks deterministic, one-dimensional, boolean-like, and aligned with the discrete action count.",
    ),
    (
        "incorrect action seeding",
        "Keep action_space(agent) object identity stable so PettingZoo can seed spaces reproducibly.",
    ),
    (
        "action mask",
        "Expose masks consistently in observation['action_mask'] or info['action_mask'] and sample with the mask.",
    ),
    (
        "render_modes",
        "Set metadata['render_modes'] to the supported modes and return the correct type for each mode.",
    ),
    (
        "rgb_array mode",
        "Return a numpy uint8 image array with shape (height, width, 3) for rgb_array mode.",
    ),
    (
        "max_cycles",
        "Ensure both env(max_cycles=...) and parallel_env(max_cycles=...) use the same off-by-one semantics.",
    ),
    (
        "reset",
        "PettingZoo reset should accept seed=None and options=None and fully clear episode state.",
    ),
    (
        "instance of pettingzoo.aecenv",
        "Use --api aec with an env()/raw_env() factory, or validate a ParallelEnv with --api parallel.",
    ),
)


class UserFacingError(RuntimeError):
    """A validation setup error with a concise message."""


def positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    if value > MAX_CYCLES:
        raise argparse.ArgumentTypeError(f"must be <= {MAX_CYCLES} for a bounded validation run")
    return value


def parse_checks(raw: str) -> list[str]:
    checks = [part.strip() for part in raw.split(",") if part.strip()]
    if not checks:
        raise argparse.ArgumentTypeError("choose at least one check")
    unknown = [check for check in checks if check not in CHECKS]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown checks {unknown}; choose comma-separated values from {', '.join(CHECKS)}"
        )
    return checks


def parse_json_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("must be a JSON object")
    return value


def parse_target(raw: str) -> tuple[str, str]:
    if ":" not in raw:
        raise argparse.ArgumentTypeError("target must use module:factory syntax")
    module_path, factory_name = raw.split(":", 1)
    if not module_path or not factory_name:
        raise argparse.ArgumentTypeError("target must include both module and factory")
    return module_path, factory_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run bounded PettingZoo API, seed, render, and max-cycles compliance checks."
    )
    parser.add_argument(
        "--target",
        required=True,
        type=parse_target,
        metavar="MODULE:FACTORY",
        help="Factory to validate, such as my_pkg.my_env_v0:env or my_pkg.my_env_v0:parallel_env.",
    )
    parser.add_argument(
        "--api",
        choices=("aec", "parallel"),
        required=True,
        help="Expected PettingZoo API for the target factory.",
    )
    parser.add_argument(
        "--checks",
        type=parse_checks,
        default=parse_checks("api,seed"),
        help="Comma-separated checks: api,seed,render,max-cycles. Default: api,seed.",
    )
    parser.add_argument(
        "--cycles",
        type=positive_int,
        default=25,
        help="Cycle budget for API and seed checks. Default: 25; maximum: 10000.",
    )
    parser.add_argument(
        "--factory-kwargs",
        type=parse_json_object,
        default={},
        help='JSON object passed to the factory for api/seed checks, for example \'{"max_cycles": 20}\'.',
    )
    parser.add_argument(
        "--no-render-human",
        action="store_true",
        help="For render checks, skip human mode and validate only non-GUI modes found in metadata.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed check instead of reporting all selected checks.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Print Python tracebacks for failed checks.",
    )
    return parser.parse_args()


def import_target(module_path: str, factory_name: str) -> tuple[Any, Callable[..., Any]]:
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        hint = MISSING_PACKAGE_HINTS.get(exc.name or "")
        message = f"Could not import module {module_path!r}: missing {exc.name!r}."
        if hint:
            message += f" Hint: {hint}"
        raise UserFacingError(message) from exc
    except Exception as exc:
        raise UserFacingError(f"Could not import module {module_path!r}: {exc}") from exc

    try:
        factory = getattr(module, factory_name)
    except AttributeError as exc:
        raise UserFacingError(f"Module {module_path!r} has no factory {factory_name!r}.") from exc
    if not callable(factory):
        raise UserFacingError(f"Target {module_path}:{factory_name} is not callable.")
    return module, factory


def construct(factory: Callable[..., Any], kwargs: Mapping[str, Any], render_mode: Any = OMIT) -> Any:
    call_kwargs = dict(kwargs)
    if render_mode is not OMIT:
        call_kwargs["render_mode"] = render_mode
    try:
        return factory(**call_kwargs)
    except ModuleNotFoundError as exc:
        hint = MISSING_PACKAGE_HINTS.get(exc.name or "")
        message = f"Factory import dependency is missing: {exc.name!r}."
        if hint:
            message += f" Hint: {hint}"
        raise UserFacingError(message) from exc
    except TypeError as exc:
        if render_mode is not OMIT and "render_mode" in str(exc):
            raise UserFacingError(
                "Factory did not accept render_mode. Add render_mode=None to the environment factory or skip render checks."
            ) from exc
        raise


def close_env(env: Any) -> None:
    close = getattr(env, "close", None)
    if callable(close):
        close()


def make_constructor(factory: Callable[..., Any], kwargs: Mapping[str, Any]) -> Callable[[], Any]:
    def constructor() -> Any:
        return construct(factory, kwargs)

    return constructor


def make_render_constructor(factory: Callable[..., Any], kwargs: Mapping[str, Any]) -> Callable[..., Any]:
    def constructor(**extra_kwargs: Any) -> Any:
        call_kwargs = dict(kwargs)
        call_kwargs.update(extra_kwargs)
        return construct(factory, call_kwargs)

    return constructor


def sample_action(env: Any, agent: Any, observation: Any, info: Mapping[str, Any] | None = None) -> Any:
    info = info or {}
    if isinstance(observation, Mapping) and "action_mask" in observation:
        return env.action_space(agent).sample(observation["action_mask"])
    if "action_mask" in info:
        return env.action_space(agent).sample(info["action_mask"])
    return env.action_space(agent).sample()


def validate_render_result(mode: str, result: Any) -> None:
    if mode == "human":
        assert result is None, "human render mode must return None"
    elif mode == "ansi":
        assert isinstance(result, str), "ansi render mode must return a string"
    elif mode == "rgb_array":
        import numpy as np

        assert (
            isinstance(result, np.ndarray)
            and len(result.shape) == 3
            and result.shape[2] == 3
            and result.dtype == np.uint8
        ), f"rgb_array mode must return a uint8 image array with shape (height, width, 3), got {result!r}"


def discover_render_modes(factory: Callable[..., Any], kwargs: Mapping[str, Any]) -> list[str]:
    env = None
    try:
        try:
            env = construct(factory, kwargs, render_mode=None)
        except UserFacingError:
            raise
        except TypeError:
            env = construct(factory, kwargs)
        metadata = getattr(env, "metadata", {}) or {}
        modes = metadata.get("render_modes")
        assert modes is not None, "Environments that support rendering must define render_modes in metadata"
        return list(modes)
    finally:
        if env is not None:
            close_env(env)


def run_nonhuman_render_check(factory: Callable[..., Any], kwargs: Mapping[str, Any], api: str) -> None:
    modes = [mode for mode in discover_render_modes(factory, kwargs) if mode != "human"]
    if not modes:
        print("No non-human render modes declared; skipped render body after metadata check.")
        return

    for mode in modes:
        env = construct(factory, kwargs, render_mode=mode)
        try:
            reset_result = env.reset(seed=0)
            validate_render_result(mode, env.render())
            if api == "aec":
                max_turns = max(1, min(4, getattr(env, "num_agents", 1) + 1))
                for turn_index, agent in enumerate(env.agent_iter(max_turns)):
                    observation, _reward, terminated, truncated, info = env.last()
                    action = None if terminated or truncated else sample_action(env, agent, observation, info)
                    env.step(action)
                    validate_render_result(mode, env.render())
                    if turn_index + 1 >= max_turns:
                        break
            else:
                observations = reset_result[0] if isinstance(reset_result, tuple) else {}
                for _ in range(2):
                    actions = {
                        agent: sample_action(env, agent, observations.get(agent) if isinstance(observations, Mapping) else None)
                        for agent in getattr(env, "agents", [])
                    }
                    if not actions:
                        break
                    observations, _rewards, _terminations, _truncations, _infos = env.step(actions)
                    validate_render_result(mode, env.render())
        finally:
            close_env(env)


def run_api_check(factory: Callable[..., Any], kwargs: Mapping[str, Any], api: str, cycles: int) -> None:
    env = construct(factory, kwargs)
    try:
        if api == "aec":
            from pettingzoo.test import api_test

            api_test(env, num_cycles=cycles, verbose_progress=False)
        else:
            from pettingzoo.test import parallel_api_test

            parallel_api_test(env, num_cycles=cycles)
    finally:
        close_env(env)


def run_seed_check(factory: Callable[..., Any], kwargs: Mapping[str, Any], api: str, cycles: int) -> None:
    constructor = make_constructor(factory, kwargs)
    if api == "aec":
        from pettingzoo.test import seed_test

        seed_test(constructor, num_cycles=cycles)
    else:
        from pettingzoo.test import parallel_seed_test

        parallel_seed_test(constructor, num_cycles=cycles)


def run_render_check(factory: Callable[..., Any], kwargs: Mapping[str, Any], api: str, no_render_human: bool) -> None:
    if no_render_human:
        run_nonhuman_render_check(factory, kwargs, api)
        return
    from pettingzoo.test import render_test

    render_test(make_render_constructor(factory, kwargs))


def run_max_cycles_check(module: Any) -> None:
    from pettingzoo.test import max_cycles_test

    if not hasattr(module, "env") or not hasattr(module, "parallel_env"):
        raise UserFacingError("max-cycles check requires the target module to expose both env() and parallel_env().")
    max_cycles_test(module)


def hint_lines(exc: BaseException) -> list[str]:
    text = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}".lower()
    hints = []
    if isinstance(exc, ModuleNotFoundError):
        hint = MISSING_PACKAGE_HINTS.get(exc.name or "")
        if hint:
            hints.append(hint)
    for pattern, hint in HINT_PATTERNS:
        if pattern in text and hint not in hints:
            hints.append(hint)
    if not hints:
        hints.append("Read references/troubleshooting.md for contract-specific interpretation of this failure.")
    return hints


def run_check(check: str, module: Any, factory: Callable[..., Any], args: argparse.Namespace) -> None:
    if check == "api":
        run_api_check(factory, args.factory_kwargs, args.api, args.cycles)
    elif check == "seed":
        run_seed_check(factory, args.factory_kwargs, args.api, args.cycles)
    elif check == "render":
        run_render_check(factory, args.factory_kwargs, args.api, args.no_render_human)
    elif check == "max-cycles":
        run_max_cycles_check(module)
    else:
        raise UserFacingError(f"Unsupported check {check!r}.")


def main() -> int:
    args = parse_args()
    module_path, factory_name = args.target
    try:
        module, factory = import_target(module_path, factory_name)
    except Exception as exc:
        print(f"SETUP FAILED: {exc}", file=sys.stderr)
        for hint in hint_lines(exc):
            print(f"  hint: {hint}", file=sys.stderr)
        if args.show_traceback:
            traceback.print_exc()
        return 2

    failures: list[str] = []
    for check in args.checks:
        print(f"==> Running {check} check for {module_path}:{factory_name} ({args.api})")
        try:
            run_check(check, module, factory, args)
        except Exception as exc:
            failures.append(check)
            print(f"FAILED {check}: {type(exc).__name__}: {exc}", file=sys.stderr)
            for hint in hint_lines(exc):
                print(f"  hint: {hint}", file=sys.stderr)
            if args.show_traceback:
                traceback.print_exc()
            if args.fail_fast:
                break
        else:
            print(f"PASSED {check}")

    if failures:
        print(f"Compliance checks failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("All selected compliance checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
