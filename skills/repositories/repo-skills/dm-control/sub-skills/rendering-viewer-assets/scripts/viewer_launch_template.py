#!/usr/bin/env python3
"""Safe dm_control viewer launcher template.

Default behavior is a dry run that validates the environment loader and optional
policy shape without importing dm_control.viewer or opening a GUI. Pass --launch
explicitly to start the interactive viewer.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Callable, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Template for dm_control.viewer.launch using suite or manipulation "
            "environments. Dry-run is the default; pass --launch to open a GUI."
        )
    )
    parser.add_argument(
        "--family",
        choices=("suite", "manipulation"),
        default="suite",
        help="Environment family to load.",
    )
    parser.add_argument("--domain", default="cartpole", help="Suite domain name.")
    parser.add_argument("--task", default="balance", help="Suite task name.")
    parser.add_argument(
        "--manipulation-env",
        default=None,
        help="Manipulation environment name. If omitted, a small registry default is used.",
    )
    parser.add_argument(
        "--policy",
        choices=("none", "zeros", "random"),
        default="none",
        help="Optional policy pattern to pass to the viewer.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed for random policy.")
    parser.add_argument("--title", default=None, help="Viewer window title.")
    parser.add_argument("--width", type=int, default=1024, help="Viewer window width.")
    parser.add_argument("--height", type=int, default=768, help="Viewer window height.")
    parser.add_argument(
        "--mujoco-gl",
        choices=("unchanged", "glfw", "egl", "osmesa"),
        default="unchanged",
        help=(
            "Backend environment setting before imports. Interactive viewer use "
            "expects GLFW; dry-run does not render."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--launch",
        action="store_true",
        help="Open the interactive viewer. Requires a display/windowing setup.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate loader/policy without opening a GUI. This is the default.",
    )
    return parser.parse_args()


def configure_backend(args: argparse.Namespace) -> None:
    if args.mujoco_gl != "unchanged":
        os.environ["MUJOCO_GL"] = args.mujoco_gl
    elif args.launch and os.environ.get("MUJOCO_GL") is None:
        # The viewer is GLFW-only. Set this before importing dm_control modules.
        os.environ["MUJOCO_GL"] = "glfw"
        print("launch mode: set MUJOCO_GL=glfw because dm_control.viewer uses GLFW")

    if args.launch and os.environ.get("MUJOCO_GL") != "glfw":
        print(
            "warning: dm_control.viewer is a GLFW/windowed path; "
            f"current MUJOCO_GL={os.environ.get('MUJOCO_GL')!r} may fail.",
            file=sys.stderr,
        )


def make_loader(args: argparse.Namespace) -> Tuple[Callable[[], object], str]:
    # Imported after backend configuration on purpose.
    if args.family == "suite":
        from dm_control import suite

        label = f"suite:{args.domain}.{args.task}"

        def loader():
            return suite.load(domain_name=args.domain, task_name=args.task)

        return loader, label

    from dm_control import manipulation

    env_name = args.manipulation_env
    if env_name is None:
        easy = list(manipulation.get_environments_by_tag("easy"))
        env_name = easy[0] if easy else list(manipulation.ALL)[0]
    label = f"manipulation:{env_name}"

    def loader():
        return manipulation.load(environment_name=env_name, seed=args.seed)

    return loader, label


def summarize_spec(spec) -> str:
    shape = getattr(spec, "shape", None)
    dtype = getattr(spec, "dtype", None)
    minimum = getattr(spec, "minimum", None)
    maximum = getattr(spec, "maximum", None)
    parts = [f"shape={shape}", f"dtype={dtype}"]
    if minimum is not None and maximum is not None:
        parts.append(f"minimum={minimum}")
        parts.append(f"maximum={maximum}")
    return ", ".join(parts)


def observation_keys(observation) -> str:
    if isinstance(observation, dict):
        return ", ".join(map(str, observation.keys()))
    return type(observation).__name__


def make_policy(kind: str, action_spec, seed: int) -> Optional[Callable[[object], object]]:
    if kind == "none":
        return None

    import numpy as np

    if kind == "zeros":
        minimum = np.asarray(getattr(action_spec, "minimum", -np.inf))
        maximum = np.asarray(getattr(action_spec, "maximum", np.inf))

        def zeros_policy(time_step):
            del time_step
            action = np.zeros(action_spec.shape, dtype=action_spec.dtype)
            return np.clip(action, minimum, maximum).astype(action_spec.dtype, copy=False)

        return zeros_policy

    rng = np.random.default_rng(seed)
    minimum = np.asarray(action_spec.minimum)
    maximum = np.asarray(action_spec.maximum)

    def random_policy(time_step):
        del time_step
        return rng.uniform(low=minimum, high=maximum, size=action_spec.shape).astype(
            action_spec.dtype, copy=False
        )

    return random_policy


def main() -> int:
    args = parse_args()
    configure_backend(args)

    try:
        loader, label = make_loader(args)
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", None) == "dm_control":
            print(
                "dm_control is not installed in this Python environment. Install it with "
                "'python -m pip install dm_control' or, for unreleased source snapshots, "
                "'python -m pip install git+https://github.com/google-deepmind/dm_control.git'.",
                file=sys.stderr,
            )
            return 2
        raise
    title = args.title or label

    env = loader()
    time_step = env.reset()
    action_spec = env.action_spec()
    policy = make_policy(args.policy, action_spec, args.seed)

    print(f"loader_ok label={label}")
    print(f"action_spec {summarize_spec(action_spec)}")
    print(f"initial_step step_type={time_step.step_type} reward={time_step.reward}")
    print(f"observation_keys {observation_keys(time_step.observation)}")
    if policy is not None:
        action = policy(time_step)
        print(f"policy_sample kind={args.policy} shape={getattr(action, 'shape', None)} dtype={getattr(action, 'dtype', None)}")

    if not args.launch:
        print("dry_run_ok launch=False; pass --launch only on a machine with a GUI display")
        return 0

    print(
        f"launching_viewer title={title!r} size={args.width}x{args.height} "
        f"MUJOCO_GL={os.environ.get('MUJOCO_GL', '<unset>')}"
    )
    from dm_control import viewer

    viewer.launch(loader, policy=policy, title=title, width=args.width, height=args.height)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
