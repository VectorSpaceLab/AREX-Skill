#!/usr/bin/env python3
"""Installed-package smoke checks for dm_control.

This script intentionally uses only public dm_control imports and tiny generated
models. It does not read a dm_control source checkout.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import PackageNotFoundError, version


def _fail(message: str, exc: BaseException | None = None) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    if exc is not None:
        print(f"DETAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1


def _suite_smoke(flat_observation: bool, steps: int) -> None:
    import numpy as np
    from dm_control import suite

    env = suite.load(
        "cartpole",
        "balance",
        task_kwargs={"random": 0},
        environment_kwargs={"flat_observation": flat_observation},
    )
    time_step = env.reset()
    action_spec = env.action_spec()
    action = np.zeros(action_spec.shape, dtype=action_spec.dtype)
    for _ in range(steps):
        time_step = env.step(action)
        if time_step.last():
            break
    print(
        "suite cartpole/balance:",
        f"tasks={len(suite.ALL_TASKS)}",
        f"benchmarking={len(suite.BENCHMARKING)}",
        f"action_shape={action_spec.shape}",
        f"last_step={time_step.step_type.name}",
        f"obs_keys={list(time_step.observation.keys())}",
    )


def _mjcf_smoke(render: bool, width: int, height: int) -> None:
    from dm_control import mjcf

    model = mjcf.RootElement(model="dm_control_skill_smoke")
    getattr(model.visual, "global").offwidth = width
    getattr(model.visual, "global").offheight = height
    model.worldbody.add("light", pos=[0, 0, 2])
    model.worldbody.add("geom", name="floor", type="plane", size=[1, 1, 0.1])
    body = model.worldbody.add("body", name="box_body", pos=[0, 0, 0.2])
    body.add("joint", name="slide_z", type="slide", axis=[0, 0, 1])
    body.add("geom", name="box", type="box", size=[0.05, 0.05, 0.05])

    physics = mjcf.Physics.from_mjcf_model(model)
    physics.step(2)
    print(
        "mjcf physics:",
        f"nbody={physics.model.nbody}",
        f"time={float(physics.data.time):.6f}",
        f"box={model.find('geom', 'box').name}",
    )
    if render:
        frame = physics.render(width=width, height=height, camera_id=-1)
        print(
            "render:",
            f"backend={os.environ.get('MUJOCO_GL', '<default>')}",
            f"shape={frame.shape}",
            f"dtype={frame.dtype}",
            f"mean={float(frame.mean()):.2f}",
        )


def _manipulation_smoke() -> None:
    from dm_control import manipulation

    print(
        "manipulation registry:",
        f"tasks={len(manipulation.ALL)}",
        f"tags={manipulation.TAGS}",
        f"first={manipulation.ALL[:3]}",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=1, help="suite smoke steps")
    parser.add_argument("--flat-observation", action="store_true", help="use flat Control Suite observations")
    parser.add_argument("--render", action="store_true", help="also render a tiny PyMJCF frame")
    parser.add_argument("--backend", choices=["default", "egl", "osmesa", "glfw"], default="default", help="set MUJOCO_GL before imports")
    parser.add_argument("--width", type=int, default=64, help="render width")
    parser.add_argument("--height", type=int, default=48, help="render height")
    args = parser.parse_args(argv)

    if args.backend != "default":
        os.environ["MUJOCO_GL"] = args.backend

    try:
        print("dm_control version:", version("dm_control"))
    except PackageNotFoundError as exc:
        return _fail("dm_control distribution is not installed", exc)

    try:
        from dm_control import composer, manipulation, mjcf, mujoco, suite  # noqa: F401
        print("imports: suite mjcf mujoco composer manipulation ok")
    except Exception as exc:  # pylint: disable=broad-except
        return _fail("core dm_control imports failed", exc)

    try:
        _suite_smoke(args.flat_observation, args.steps)
        _mjcf_smoke(args.render, args.width, args.height)
        _manipulation_smoke()
    except Exception as exc:  # pylint: disable=broad-except
        hint = "If only rendering failed, rerun without --render or try --backend egl/osmesa/glfw."
        return _fail(f"smoke check failed. {hint}", exc)

    print("dm_control smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
