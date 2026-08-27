#!/usr/bin/env python3
"""Build safe SIBR viewer command strings for gaussian-splatting.

This helper does not run viewer binaries. It only emits the command that should
be run after the SIBR applications are installed or built.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def q(x) -> str:
    return shlex.quote(str(x))


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a SIBR gaussian-splatting viewer command")
    parser.add_argument("--viewer", choices=["remote", "real-time"], required=True, help="Viewer app type.")
    parser.add_argument("--bin-dir", required=True, help="Directory containing SIBR viewer binaries.")
    parser.add_argument("--model", help="Trained model path, required for real-time viewer.")
    parser.add_argument("--source", help="Override source dataset path when needed.")
    parser.add_argument("--ip", default="127.0.0.1", help="Remote viewer/optimizer IP.")
    parser.add_argument("--port", type=int, default=6009, help="Remote viewer/optimizer port.")
    parser.add_argument("--iteration", type=int, help="Iteration to load for real-time viewer.")
    parser.add_argument("--rendering-size", nargs=2, metavar=("WIDTH", "HEIGHT"), help="Viewer rendering size.")
    parser.add_argument("--force-aspect-ratio", action="store_true")
    parser.add_argument("--load-images", action="store_true")
    parser.add_argument("--device", type=int, help="CUDA device index for real-time viewer.")
    parser.add_argument("--no-interop", action="store_true", help="Disable CUDA/GL interop for real-time viewer.")
    args = parser.parse_args()

    bin_dir = Path(args.bin_dir)
    exe = bin_dir / ("SIBR_remoteGaussian_app" if args.viewer == "remote" else "SIBR_gaussianViewer_app")
    cmd = [str(exe)]
    if args.viewer == "remote":
        cmd += ["--ip", args.ip, "--port", str(args.port)]
        if args.source:
            cmd += ["-s", args.source]
    else:
        if not args.model:
            parser.error("--model is required for --viewer real-time")
        cmd += ["-m", args.model]
        if args.source:
            cmd += ["-s", args.source]
        if args.iteration is not None:
            cmd += ["--iteration", str(args.iteration)]
        if args.device is not None:
            cmd += ["--device", str(args.device)]
        if args.no_interop:
            cmd.append("--no_interop")
    if args.rendering_size:
        cmd += ["--rendering-size", *args.rendering_size]
    if args.force_aspect_ratio:
        cmd.append("--force-aspect-ratio")
    if args.load_images:
        cmd.append("--load_images")
    print(" ".join(q(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
