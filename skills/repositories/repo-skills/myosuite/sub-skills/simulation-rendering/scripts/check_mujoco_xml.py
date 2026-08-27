#!/usr/bin/env python3
"""Safely load, step, and optionally render a MuJoCo XML model.

The default path is model-load plus a bounded physics smoke check. Rendering is
explicitly opt-in and uses mujoco.Renderer only; this script never launches a
MuJoCo viewer or opens a display window.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import mujoco
import numpy as np


def _vector(text: Optional[str], expected: int, label: str) -> Optional[np.ndarray]:
    if text is None:
        return None
    try:
        values = np.asarray([float(item.strip()) for item in text.split(",")], dtype=float)
    except ValueError as exc:
        raise ValueError(f"{label} must be comma-separated numbers") from exc
    if values.size != expected:
        raise ValueError(f"{label} has {values.size} values; model requires {expected}")
    return values


def _camera(value: str):
    """Keep numeric camera ids numeric and named cameras as strings."""
    try:
        return int(value)
    except ValueError:
        return value


def _write_ppm(path: Path, frame: np.ndarray) -> None:
    """Write an RGB uint8 array without requiring an image package."""
    array = np.asarray(frame)
    if array.ndim != 3 or array.shape[2] < 3:
        raise ValueError(f"renderer returned non-RGB frame with shape {array.shape}")
    rgb = np.asarray(array[:, :, :3], dtype=np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        height, width = rgb.shape[:2]
        stream.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        stream.write(rgb.tobytes(order="C"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load and step one MuJoCo XML model. The default is headless; "
            "--render offscreen writes PPM frames and never opens a viewer."
        )
    )
    parser.add_argument("--xml", "--model-path", dest="xml", required=True, help="XML model path")
    parser.add_argument("--qpos", help="optional comma-separated initial qpos values")
    parser.add_argument("--ctrl", help="optional comma-separated control values")
    parser.add_argument("--frames", type=int, default=1, help="bounded physics frames to step (default: 1)")
    parser.add_argument(
        "--render",
        choices=("none", "offscreen"),
        default="none",
        help="render mode; none is safe default and offscreen writes PPM frames",
    )
    parser.add_argument("--width", type=int, default=320, help="offscreen width in pixels")
    parser.add_argument("--height", type=int, default=240, help="offscreen height in pixels")
    parser.add_argument("--camera", default="-1", help="camera id or named camera (default: free camera -1)")
    parser.add_argument(
        "--render-every",
        type=int,
        default=1,
        help="render every Nth stepped frame (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("mujoco-check-output"),
        help="directory for PPM frames (created only with --render offscreen)",
    )
    parser.add_argument("--output-name", default="frame", help="PPM filename prefix")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    xml_path = Path(args.xml)
    if not xml_path.is_file():
        raise FileNotFoundError(f"XML model does not exist or is not a file: {xml_path}")
    if args.frames < 1:
        raise ValueError("--frames must be at least 1")
    if args.frames > 1000:
        raise ValueError("--frames is bounded to 1000; choose a shorter smoke check")
    if args.render_every < 1:
        raise ValueError("--render-every must be at least 1")
    if args.width < 1 or args.height < 1:
        raise ValueError("--width and --height must be positive")
    if args.render == "offscreen" and (args.width > 4096 or args.height > 4096):
        raise ValueError("offscreen dimensions are bounded to 4096 pixels per side")

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    qpos = _vector(args.qpos, model.nq, "--qpos")
    ctrl = _vector(args.ctrl, model.nu, "--ctrl")
    if qpos is not None:
        data.qpos[:] = qpos
        mujoco.mj_forward(model, data)
    if ctrl is not None:
        data.ctrl[:] = ctrl

    print(
        "loaded model: "
        f"nq={model.nq} nv={model.nv} nu={model.nu} "
        f"ncam={model.ncam} timestep={model.opt.timestep:g}"
    )

    renderer = None
    if args.render == "offscreen":
        # This is the only rendering construction in the script. It is the
        # headless renderer, not a window/display API.
        renderer = mujoco.Renderer(model, height=args.height, width=args.width)

    camera = _camera(args.camera)
    written: list[Path] = []
    try:
        for frame_index in range(args.frames):
            mujoco.mj_step(model, data)
            if renderer is not None and frame_index % args.render_every == 0:
                renderer.update_scene(data, camera=camera)
                frame = renderer.render()
                output = args.output_dir / f"{args.output_name}-{frame_index:04d}.ppm"
                _write_ppm(output, frame)
                written.append(output)
    finally:
        if renderer is not None:
            renderer.close()

    print(f"stepped frames: {args.frames}; final time: {data.time:g}")
    if written:
        for path in written:
            print(f"wrote: {path}")
    else:
        print("render output: none (use --render offscreen to write PPM frames)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        raise SystemExit(f"check_mujoco_xml: error: {exc}")
