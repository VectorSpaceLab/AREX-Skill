#!/usr/bin/env python3
"""List dm_control manipulation tasks and probe locomotion imports.

This script is intended for an installed, non-editable dm_control package. It
prints manipulation registry names/tags, imports common locomotion modules, and
optionally runs a one-reset/one-step manipulation smoke test.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Iterable

import numpy as np

EXAMPLE_MODULES = {
    "dm_control.locomotion.examples.basic_cmu_2019": [
        "cmu_humanoid_run_walls",
        "cmu_humanoid_run_gaps",
        "cmu_humanoid_go_to_target",
        "cmu_humanoid_maze_forage",
        "cmu_humanoid_heterogeneous_forage",
    ],
    "dm_control.locomotion.examples.basic_rodent_2020": [
        "rodent_escape_bowl",
        "rodent_run_gaps",
        "rodent_maze_forage",
        "rodent_two_touch",
    ],
    "dm_control.locomotion.examples.cmu_2020_tracking": [
        "cmu_humanoid_tracking",
    ],
}

COMPONENT_MODULES = [
    "dm_control.locomotion.arenas",
    "dm_control.locomotion.walkers",
    "dm_control.locomotion.tasks",
    "dm_control.locomotion.soccer",
    "dm_control.locomotion.mocap.loader",
]


def _format_tuple(values: Iterable[str]) -> str:
    values = tuple(values)
    if not values:
        return "(none)"
    return "\n".join(f"  - {value}" for value in values)


def list_manipulation() -> None:
    from dm_control import manipulation

    print("Manipulation tags:")
    print(_format_tuple(manipulation.TAGS))
    print(f"\nManipulation tasks ({len(manipulation.ALL)}):")
    print(_format_tuple(manipulation.ALL))

    print("\nManipulation tasks by tag:")
    for tag in manipulation.TAGS:
        names = manipulation.get_environments_by_tag(tag)
        print(f"[{tag}] {len(names)}")
        print(_format_tuple(names))


def probe_locomotion_imports(strict: bool = False) -> bool:
    ok = True
    print("\nLocomotion component imports:")
    for module_name in COMPONENT_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - diagnostic script
            ok = False
            print(f"  [FAIL] {module_name}: {type(exc).__name__}: {exc}")
        else:
            print(f"  [OK]   {module_name}")

    print("\nLocomotion example imports:")
    for module_name, expected_callables in EXAMPLE_MODULES.items():
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - diagnostic script
            ok = False
            print(f"  [FAIL] {module_name}: {type(exc).__name__}: {exc}")
            continue
        missing = [name for name in expected_callables if not hasattr(module, name)]
        if missing:
            ok = False
            print(f"  [FAIL] {module_name}: missing {', '.join(missing)}")
        else:
            print(f"  [OK]   {module_name}: {', '.join(expected_callables)}")

    if strict and not ok:
        print("\nOne or more locomotion imports failed.", file=sys.stderr)
    return ok


def smoke_manipulation(environment_name: str, seed: int) -> None:
    from dm_control import manipulation

    if environment_name not in manipulation.ALL:
        raise ValueError(
            f"Unknown manipulation environment {environment_name!r}. "
            "Use one of manipulation.ALL."
        )

    env = manipulation.load(environment_name, seed=seed)
    observation_spec = env.observation_spec()
    action_spec = env.action_spec()
    print(f"\nSmoke manipulation environment: {environment_name}")
    print(f"  observation keys: {list(observation_spec)}")
    print(f"  action shape: {action_spec.shape}")
    print(f"  action dtype: {action_spec.dtype}")
    print(
        "  finite action bounds: "
        f"min={np.isfinite(action_spec.minimum).all()} "
        f"max={np.isfinite(action_spec.maximum).all()}"
    )

    time_step = env.reset()
    for key, spec in observation_spec.items():
        spec.validate(time_step.observation[key])

    action = np.zeros(action_spec.shape, dtype=action_spec.dtype)
    action = np.clip(action, action_spec.minimum, action_spec.maximum)
    time_step = env.step(action)
    for key, spec in observation_spec.items():
        spec.validate(time_step.observation[key])
    print(f"  stepped: reward={time_step.reward} discount={time_step.discount}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke-manipulation",
        action="store_true",
        help="reset and step one manipulation task with a clipped zero action",
    )
    parser.add_argument(
        "--manipulation-env",
        default="reach_site_features",
        help="registered manipulation task to smoke-test",
    )
    parser.add_argument("--seed", type=int, default=0, help="seed for smoke construction")
    parser.add_argument(
        "--strict-imports",
        action="store_true",
        help="exit nonzero if a locomotion import probe fails",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    list_manipulation()
    imports_ok = probe_locomotion_imports(strict=args.strict_imports)
    if args.smoke_manipulation:
        smoke_manipulation(args.manipulation_env, args.seed)
    return 0 if imports_ok or not args.strict_imports else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
