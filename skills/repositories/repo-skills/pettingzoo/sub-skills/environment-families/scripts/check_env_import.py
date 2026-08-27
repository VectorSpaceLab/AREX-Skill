#!/usr/bin/env python3
"""Safely probe PettingZoo family module imports and optional constructors."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import traceback
from types import ModuleType
from typing import Any

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

FAMILY_EXTRAS = {
    "classic": "pettingzoo[classic]",
    "butterfly": "pettingzoo[butterfly]",
    "atari": "pettingzoo[atari] plus Atari ROM files",
    "sisl": "pettingzoo[sisl]",
    "magent": "magent2 (Magent moved out of PettingZoo)",
}

MISSING_PACKAGE_HINTS = {
    "numpy": "Install the base PettingZoo requirements first. Base PettingZoo depends on numpy and gymnasium before any family extra can work.",
    "gymnasium": "Install the base PettingZoo requirements first. Family extras add environment dependencies but do not replace the base install.",
    "pygame": "Install the matching PettingZoo family extra. Classic, Butterfly, Atari, and SISL can all require pygame-ce; choose the smallest extra for the target module.",
    "rlcard": "Install pettingzoo[classic] for RLCard-backed Classic card environments.",
    "multi_agent_ale_py": "Install pettingzoo[atari]. If construction later fails, install or point to Atari ROMs separately.",
    "pymunk": "Install pettingzoo[butterfly] for Butterfly or pettingzoo[sisl] for SISL, depending on the target module.",
    "Box2D": "Install pettingzoo[sisl]. If the build fails, install platform build prerequisites such as SWIG first.",
    "box2d": "Install pettingzoo[sisl]. If the build fails, install platform build prerequisites such as SWIG first.",
    "shimmy": "Install pettingzoo[classic] for OpenSpiel-backed Classic environments.",
    "pyspiel": "Install pettingzoo[classic]; the Classic extra includes shimmy[openspiel].",
    "chess": "Install pettingzoo[classic] for chess-backed Classic environments.",
    "PIL": "Install pettingzoo[other] if image support is the missing capability.",
}

ROM_ERROR_MARKERS = (
    "rom ",
    "roms",
    "AutoROM",
    "auto_rom_install_path",
    "is not installed",
    "loadROM",
)

DISPLAY_ERROR_MARKERS = (
    "No available video device",
    "video system not initialized",
    "display",
    "pygame.error",
    "SDL",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import a PettingZoo environment module and optionally construct/reset "
            "env() or parallel_env() without downloads, training, rendering, or writes."
        )
    )
    parser.add_argument(
        "module",
        help="Module path such as pettingzoo.classic.rps_v2 or pettingzoo.atari.space_invaders_v2.",
    )
    parser.add_argument(
        "--factory",
        choices=("env", "parallel_env", "raw_env"),
        help="Optionally call this factory after import. By default the script only imports the module.",
    )
    parser.add_argument(
        "--constructor-kwargs",
        default="{}",
        help='JSON object passed to the selected factory, for example \'{"render_mode": null}\'.',
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Call reset(seed=...) after construction. This is off by default because Atari ROMs and displays may be unavailable.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed to pass to reset when --reset is used. Default: 0.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Print the Python traceback in addition to actionable advice.",
    )
    return parser.parse_args()


def family_from_module(module_path: str) -> str | None:
    parts = module_path.split(".")
    if len(parts) >= 2 and parts[0] == "pettingzoo":
        return parts[1]
    return None


def load_kwargs(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--constructor-kwargs must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--constructor-kwargs must decode to a JSON object")
    return parsed


def missing_name(exc: BaseException) -> str | None:
    if isinstance(exc, ModuleNotFoundError):
        return exc.name
    text = str(exc)
    for name in MISSING_PACKAGE_HINTS:
        if name in text:
            return name
    return None


def print_family_advice(module_path: str) -> None:
    family = family_from_module(module_path)
    if not family:
        return
    extra = FAMILY_EXTRAS.get(family)
    if extra:
        print(f"Family: {family}", file=sys.stderr)
        print(f"Suggested minimal install: {extra}", file=sys.stderr)
    if family == "atari":
        print(
            "Atari note: pettingzoo[atari] installs ALE bindings, but ROM files are separate. "
            "Use auto_rom_install_path if ROMs are not in the default location.",
            file=sys.stderr,
        )
    if family == "magent":
        print(
            "Magent note: current PettingZoo raises an import error for pettingzoo.magent; migrate old code to magent2.",
            file=sys.stderr,
        )


def print_exception_advice(stage: str, module_path: str, exc: BaseException) -> None:
    print(f"FAIL: {stage} failed for {module_path}: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    print_family_advice(module_path)

    missing = missing_name(exc)
    if missing:
        hint = MISSING_PACKAGE_HINTS.get(missing) or MISSING_PACKAGE_HINTS.get(missing.split(".")[0])
        if hint:
            print(f"Missing package advice: {hint}", file=sys.stderr)

    text = f"{exc.__class__.__name__}: {exc}"
    if any(marker in text for marker in ROM_ERROR_MARKERS):
        print(
            "ROM advice: install/acquire the required Atari ROMs separately, or pass "
            "auto_rom_install_path in --constructor-kwargs when probing an Atari constructor.",
            file=sys.stderr,
        )
    if any(marker in text for marker in DISPLAY_ERROR_MARKERS):
        print(
            "Render/display advice: avoid render_mode='human' in headless sessions; use "
            "render_mode=None for constructor checks or 'rgb_array' when pixels are needed.",
            file=sys.stderr,
        )
    if "swig" in text.lower() or "cmake" in text.lower() or "zlib" in text.lower():
        print(
            "Build advice: optional dependencies may need system packages such as cmake, swig, or zlib development headers.",
            file=sys.stderr,
        )


def close_env(env: Any) -> None:
    close = getattr(env, "close", None)
    if callable(close):
        close()


def summarize_module(module: ModuleType) -> None:
    factories = [name for name in ("env", "parallel_env", "raw_env") if callable(getattr(module, name, None))]
    print(f"OK: imported {module.__name__}")
    if factories:
        print(f"Factories: {', '.join(factories)}")
    else:
        print("Factories: none detected")


def summarize_env(env: Any, factory_name: str) -> None:
    metadata = getattr(env, "metadata", None)
    possible_agents = getattr(env, "possible_agents", None)
    agents = getattr(env, "agents", None)
    print(f"OK: constructed {factory_name}()")
    if isinstance(metadata, dict):
        name = metadata.get("name")
        render_modes = metadata.get("render_modes")
        is_parallelizable = metadata.get("is_parallelizable")
        if name is not None:
            print(f"Metadata name: {name}")
        if render_modes is not None:
            print(f"Render modes: {render_modes}")
        if is_parallelizable is not None:
            print(f"is_parallelizable: {is_parallelizable}")
    if possible_agents is not None:
        print(f"possible_agents: {len(possible_agents)}")
    if agents is not None:
        print(f"agents now: {len(agents)}")


def reset_env(env: Any, seed: int) -> None:
    result = env.reset(seed=seed)
    print(f"OK: reset(seed={seed})")
    if result is not None:
        if isinstance(result, tuple):
            print(f"Reset returned tuple length: {len(result)}")
        else:
            print(f"Reset returned: {type(result).__name__}")


def main() -> int:
    args = parse_args()

    try:
        kwargs = load_kwargs(args.constructor_kwargs)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    try:
        module = importlib.import_module(args.module)
    except BaseException as exc:  # noqa: BLE001 - CLI should turn import errors into advice.
        print_exception_advice("import", args.module, exc)
        if args.show_traceback:
            traceback.print_exc()
        return 1

    summarize_module(module)
    print_family_advice(args.module)

    if not args.factory:
        print("No factory requested; constructor and reset were skipped.")
        return 0

    factory = getattr(module, args.factory, None)
    if not callable(factory):
        print(f"FAIL: module {args.module} has no callable {args.factory}()", file=sys.stderr)
        return 1

    env = None
    try:
        env = factory(**kwargs)
        summarize_env(env, args.factory)
        if args.reset:
            reset_env(env, args.seed)
    except BaseException as exc:  # noqa: BLE001 - CLI should turn constructor/reset errors into advice.
        print_exception_advice(f"{args.factory}()/reset" if args.reset else f"{args.factory}()", args.module, exc)
        if args.show_traceback:
            traceback.print_exc()
        return 1
    finally:
        if env is not None:
            try:
                close_env(env)
            except BaseException as exc:  # noqa: BLE001 - close failures should not hide probe result.
                print(f"WARN: close() failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
