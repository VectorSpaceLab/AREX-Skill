#!/usr/bin/env python3
"""Build, compile, step, optionally render, and optionally export a tiny dm_control MJCF model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    from dm_control import mjcf, mujoco
except Exception as exc:  # pragma: no cover - exercised by users without install.
    print(
        "Failed to import dm_control. Install with `pip install dm_control`.",
        file=sys.stderr,
    )
    print(f"Import error: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc


def build_model(offwidth: int, offheight: int) -> tuple[mjcf.RootElement, dict[str, Any]]:
    """Builds a minimal actuated model and returns useful element handles."""
    model = mjcf.RootElement(model="mjcf_smoke")
    model.compiler.angle = "radian"

    # PyMJCF child name is XML <global>, so use getattr because `global` is a
    # Python keyword. The compiled MuJoCo wrapper exposes this as global_.
    visual_global = getattr(model.visual, "global")
    visual_global.offwidth = int(max(offwidth, 64))
    visual_global.offheight = int(max(offheight, 64))

    model.worldbody.add("light", name="top_light", pos=[0, 0, 1.5])
    model.worldbody.add(
        "geom",
        name="floor",
        type="plane",
        size=[1.0, 1.0, 0.05],
        rgba=[0.8, 0.8, 0.8, 1.0],
    )
    body = model.worldbody.add("body", name="slider_body", pos=[0, 0, 0.25])
    joint = body.add(
        "joint",
        name="slide_z",
        type="slide",
        axis=[0, 0, 1],
        limited="true",
        range=[-0.15, 0.35],
        damping=1.0,
    )
    geom = body.add(
        "geom",
        name="slider_box",
        type="box",
        size=[0.06, 0.06, 0.06],
        rgba=[0.1, 0.35, 1.0, 1.0],
    )
    site = body.add("site", name="box_tip", pos=[0, 0, 0.08], size=[0.01])

    # Use a direct Element reference for the joint attribute rather than a
    # string. This remains robust if names are later changed or scoped.
    actuator = model.actuator.add(
        "motor",
        name="slide_motor",
        joint=joint,
        gear=1.0,
        ctrllimited=True,
        ctrlrange=[-1.0, 1.0],
    )
    return model, {"body": body, "joint": joint, "geom": geom, "site": site, "actuator": actuator}


def _bounded_zero_action(physics: mujoco.Physics) -> np.ndarray:
    spec = mujoco.action_spec(physics)
    action = np.zeros(spec.shape, dtype=float)
    if action.size:
        minimum = np.where(np.isfinite(spec.minimum), spec.minimum, -1.0)
        maximum = np.where(np.isfinite(spec.maximum), spec.maximum, 1.0)
        action = np.clip(action, minimum, maximum)
    return action


def _write_text(path_arg: str, text: str) -> None:
    if path_arg == "-":
        print(text)
        return
    path = Path(path_arg)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_render(path_arg: str, image: np.ndarray) -> str:
    path = Path(path_arg)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".npy":
        np.save(path, image)
        return "npy"
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("PPM render output requires an RGB image")
    with path.open("wb") as f:
        f.write(f"P6\n{image.shape[1]} {image.shape[0]}\n255\n".encode("ascii"))
        f.write(np.asarray(image, dtype=np.uint8).tobytes())
    return "ppm"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny PyMJCF model, compile dm_control mjcf.Physics, step it, "
            "optionally render, and optionally write generated XML."
        )
    )
    parser.add_argument("--steps", type=int, default=5, help="Number of physics steps to run (default: 5).")
    parser.add_argument(
        "--initial-qpos",
        type=float,
        default=0.05,
        help="Initial slider qpos assigned inside reset_context (default: 0.05).",
    )
    parser.add_argument(
        "--control",
        type=float,
        default=0.0,
        help="Scalar motor control to clip to the action spec and apply (default: 0.0).",
    )
    parser.add_argument(
        "--xml-out",
        default=None,
        help="Write generated MJCF XML to this path, or '-' for stdout.",
    )
    parser.add_argument("--render", action="store_true", help="Render one RGB frame after stepping.")
    parser.add_argument("--render-height", type=int, default=120, help="Render height when --render is set.")
    parser.add_argument("--render-width", type=int, default=160, help="Render width when --render is set.")
    parser.add_argument(
        "--render-out",
        default=None,
        help="Optional render output path. '.npy' writes NumPy; any other suffix writes binary PPM RGB.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.steps < 0:
        print("--steps must be non-negative", file=sys.stderr)
        return 2
    if args.render_height <= 0 or args.render_width <= 0:
        print("--render-height and --render-width must be positive", file=sys.stderr)
        return 2

    model, handles = build_model(args.render_width, args.render_height)
    xml = model.to_xml_string()
    if args.xml_out is not None:
        _write_text(args.xml_out, xml)

    physics = mjcf.Physics.from_mjcf_model(model)
    action_spec = mujoco.action_spec(physics)

    with physics.reset_context():
        physics.bind(handles["joint"]).qpos = args.initial_qpos

    action = _bounded_zero_action(physics)
    if action.size:
        action[...] = np.clip(args.control, action_spec.minimum, action_spec.maximum)
    physics.set_control(action)
    if args.steps:
        physics.step(args.steps)

    geom_z = float(physics.named.data.geom_xpos["slider_box", "z"])
    site_z = float(physics.bind(handles["site"]).xpos[2])

    summary: dict[str, Any] = {
        "dm_control": "ok",
        "model": model.model,
        "nq": int(physics.model.nq),
        "nv": int(physics.model.nv),
        "nu": int(physics.model.nu),
        "steps": int(args.steps),
        "time": float(physics.time()),
        "action_spec_shape": tuple(int(x) for x in action_spec.shape),
        "action_min": np.asarray(action_spec.minimum, dtype=float).tolist(),
        "action_max": np.asarray(action_spec.maximum, dtype=float).tolist(),
        "slider_box_z": geom_z,
        "box_tip_z": site_z,
        "offscreen_buffer": [
            int(physics.model.vis.global_.offheight),
            int(physics.model.vis.global_.offwidth),
        ],
    }

    if args.render:
        try:
            image = physics.render(height=args.render_height, width=args.render_width, camera_id=-1)
        except Exception as exc:  # pragma: no cover - backend dependent.
            print(
                "Render failed. Non-rendering compile/step succeeded; check MUJOCO_GL/backend configuration.",
                file=sys.stderr,
            )
            print(f"Render error: {exc}", file=sys.stderr)
            return 3
        summary["render_shape"] = tuple(int(x) for x in image.shape)
        summary["render_dtype"] = str(image.dtype)
        if args.render_out:
            summary["render_output_format"] = _write_render(args.render_out, image)
            summary["render_output"] = args.render_out

    summary_text = json.dumps(summary, indent=2, sort_keys=True)
    if args.xml_out == "-":
        print(summary_text, file=sys.stderr)
    else:
        print(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
