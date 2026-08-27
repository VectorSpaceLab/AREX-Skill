#!/usr/bin/env python3
"""Probe dm_control OpenGL rendering backends with a tiny installed-package model."""

from __future__ import annotations

import argparse
import os
import sys
import traceback


def _camera_id(value: str):
    try:
        return int(value)
    except ValueError:
        return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a tiny dm_control frame in a fresh process. Set --backend "
            "to default, egl, osmesa, or glfw before dm_control is imported."
        )
    )
    parser.add_argument(
        "--backend",
        choices=("default", "egl", "osmesa", "glfw"),
        default="default",
        help="Rendering backend to select. 'default' unsets MUJOCO_GL.",
    )
    parser.add_argument(
        "--egl-device-id",
        type=int,
        default=None,
        help="Optional MUJOCO_EGL_DEVICE_ID value when probing EGL.",
    )
    parser.add_argument("--height", type=int, default=48, help="Frame height in pixels.")
    parser.add_argument("--width", type=int, default=64, help="Frame width in pixels.")
    parser.add_argument(
        "--camera-id",
        type=_camera_id,
        default=-1,
        help="Camera id/name passed to physics.render; default -1 is the free camera.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--depth", action="store_true", help="Probe depth rendering.")
    mode.add_argument(
        "--segmentation", action="store_true", help="Probe segmentation rendering."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print a traceback on failure."
    )
    return parser.parse_args()


def configure_backend(args: argparse.Namespace) -> None:
    if args.backend == "default":
        os.environ.pop("MUJOCO_GL", None)
    else:
        os.environ["MUJOCO_GL"] = args.backend

    if args.egl_device_id is not None:
        os.environ["MUJOCO_EGL_DEVICE_ID"] = str(args.egl_device_id)


def build_tiny_physics(width: int, height: int):
    # Imported after backend configuration on purpose.
    from dm_control import mjcf

    model = mjcf.RootElement(model="render_backend_probe")
    visual_global = getattr(model.visual, "global")
    visual_global.offwidth = max(width, 64)
    visual_global.offheight = max(height, 48)
    model.worldbody.add("light", name="light", pos=[0, 0, 2])
    model.worldbody.add("geom", name="floor", type="plane", size=[1, 1, 0.01])
    model.worldbody.add(
        "geom",
        name="box",
        type="box",
        pos=[0, 0, 0.1],
        size=[0.05, 0.05, 0.05],
        rgba=[1, 0, 0, 1],
    )
    physics = mjcf.Physics.from_mjcf_model(model)
    physics.step()
    return physics


def failure_hint(args: argparse.Namespace, exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    backend = args.backend
    if isinstance(exc, ModuleNotFoundError) and getattr(exc, "name", None) == "dm_control":
        return (
            "dm_control is not installed in this Python environment. Install it with "
            "'python -m pip install dm_control' or, for unreleased source snapshots, "
            "'python -m pip install git+https://github.com/google-deepmind/dm_control.git'."
        )
    if backend == "default":
        default_hint = (
            "Default mode tries GLFW, then EGL, then OSMesa. Pin --backend egl "
            "or --backend osmesa for deterministic headless probes."
        )
    else:
        default_hint = "Run the probe again in a fresh process after changing backend settings."

    if backend == "glfw" or "display" in text or "x11" in text or "glfw" in text:
        return (
            "GLFW needs a real windowing display. On headless hosts use "
            "--backend egl for hardware offscreen rendering or --backend osmesa "
            "if software rendering libraries are installed."
        )
    if backend == "osmesa" or "glgeterror" in text or "osmesa" in text:
        return (
            "OSMesa failures usually mean the native OSMesa/OpenGL library is "
            "missing or incompatible. Install host OSMesa/OpenGL packages or use EGL."
        )
    if backend == "egl" or "egl" in text:
        return (
            "EGL needs a compatible headless EGL driver. Try --egl-device-id, "
            "verify GPU/driver visibility, or use OSMesa if software rendering is installed."
        )
    if "must be one of" in text or "mujoco_gl" in text:
        return "MUJOCO_GL must be one of glfw, egl, or osmesa for rendering probes."
    if "no opengl rendering backend" in text:
        return "No backend imported successfully. Install or select one OpenGL backend."
    return default_hint


def main() -> int:
    args = parse_args()
    configure_backend(args)

    print(
        "probe_start "
        f"backend={args.backend} "
        f"MUJOCO_GL={os.environ.get('MUJOCO_GL', '<unset>')} "
        f"MUJOCO_EGL_DEVICE_ID={os.environ.get('MUJOCO_EGL_DEVICE_ID', '<unset>')} "
        f"size={args.height}x{args.width} camera_id={args.camera_id!r}",
        flush=True,
    )

    try:
        physics = build_tiny_physics(args.width, args.height)
        frame = physics.render(
            height=args.height,
            width=args.width,
            camera_id=args.camera_id,
            depth=args.depth,
            segmentation=args.segmentation,
        )
        try:
            from dm_control import _render as render_module

            actual_backend = getattr(render_module, "BACKEND", "unknown")
        except Exception:  # Rendering already succeeded; backend reporting is best effort.
            actual_backend = "unknown"

        mean = float(frame.mean())
        min_value = float(frame.min())
        max_value = float(frame.max())
        print(
            "render_ok "
            f"requested_backend={args.backend} actual_backend={actual_backend} "
            f"shape={tuple(frame.shape)} dtype={frame.dtype} "
            f"mean={mean:.6g} min={min_value:.6g} max={max_value:.6g}"
        )
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(
            "render_failed "
            f"requested_backend={args.backend} "
            f"error_type={type(exc).__name__} error={exc}",
            file=sys.stderr,
        )
        print(f"hint: {failure_hint(args, exc)}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
