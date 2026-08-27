#!/usr/bin/env python3
"""Check the stable-diffusion-videos runtime environment.

This helper is intentionally small and safe to run. It verifies that the public
package imports, optional backend pieces are reachable, and tiny video/audio
smokes work when requested.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path


def _maybe_import(module_name: str):
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - surfaced to user
        return None, f"{type(exc).__name__}: {exc}"
    return module, None


def _print_line(message: str) -> None:
    print(message, flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cuda", action="store_true", help="Allocate a tiny CUDA tensor if CUDA is available.")
    parser.add_argument("--check-video", action="store_true", help="Run a tiny torchvision write_video smoke test.")
    parser.add_argument("--check-audio", type=Path, help="Run get_timesteps_arr on a local audio file.")
    parser.add_argument("--offset", type=float, default=0.0, help="Audio start offset for --check-audio.")
    parser.add_argument("--duration", type=float, default=1.0, help="Audio duration for --check-audio.")
    parser.add_argument("--fps", type=int, default=4, help="FPS for --check-audio and --check-video.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary at the end.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary: dict[str, object] = {
        "platform": {
            "python": sys.version.split()[0],
            "machine": platform.machine(),
            "system": platform.system(),
        },
        "imports": {},
        "smokes": {},
    }

    package, err = _maybe_import("stable_diffusion_videos")
    summary["imports"]["stable_diffusion_videos"] = "ok" if err is None else err
    if err:
        _print_line(err)
        return 1

    try:
        from stable_diffusion_videos import (  # type: ignore
            Interface,
            RealESRGANModel,
            StableDiffusionWalkPipeline,
            generate_images,
            get_timesteps_arr,
        )
    except Exception as exc:  # pragma: no cover - surfaced to user
        _print_line(f"package export import failed: {type(exc).__name__}: {exc}")
        return 1

    summary["package_version"] = getattr(package, "__version__", "unknown")
    summary["exports"] = [
        StableDiffusionWalkPipeline.__name__,
        generate_images.__name__,
        Interface.__name__,
        RealESRGANModel.__name__,
        get_timesteps_arr.__name__,
    ]

    for name in ["torch", "torchvision", "transformers", "diffusers", "av"]:
        module, err = _maybe_import(name)
        summary["imports"][name] = "ok" if err is None else err
        if err:
            _print_line(f"{name} import failed: {err}")
            return 1

    if shutil.which("ffmpeg"):
        summary["ffmpeg"] = shutil.which("ffmpeg")
    else:
        summary["ffmpeg"] = "missing"

    if args.check_cuda:
        try:
            import torch

            cuda_available = torch.cuda.is_available()
            summary["smokes"]["cuda"] = {
                "available": cuda_available,
                "count": torch.cuda.device_count(),
            }
            if cuda_available:
                _ = torch.empty((1,), device="cuda")
                summary["smokes"]["cuda"]["device_name"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # pragma: no cover - surfaced to user
            _print_line(f"cuda smoke failed: {type(exc).__name__}: {exc}")
            return 1

    if args.check_video:
        try:
            import torch
            from torchvision.io import write_video

            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir) / "smoke.mp4"
                frames = torch.randint(0, 255, (4, 16, 16, 3), dtype=torch.uint8)
                write_video(str(out), frames, fps=args.fps)
                summary["smokes"]["video"] = {"path": str(out), "size": out.stat().st_size}
        except Exception as exc:  # pragma: no cover - surfaced to user
            _print_line(f"video smoke failed: {type(exc).__name__}: {exc}")
            return 1

    if args.check_audio is not None:
        try:
            arr = get_timesteps_arr(args.check_audio, offset=args.offset, duration=args.duration, fps=args.fps)
            summary["smokes"]["audio"] = {
                "path": str(args.check_audio),
                "shape": list(arr.shape),
                "first": float(arr[0]),
                "last": float(arr[-1]),
            }
        except Exception as exc:  # pragma: no cover - surfaced to user
            _print_line(f"audio smoke failed: {type(exc).__name__}: {exc}")
            return 1

    if args.json:
        _print_line(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_line(f"stable_diffusion_videos={summary['package_version']}")
        _print_line(f"exports={', '.join(summary['exports'])}")
        _print_line(f"ffmpeg={summary['ffmpeg']}")
        if "cuda" in summary["smokes"]:
            _print_line(f"cuda={summary['smokes']['cuda']}")
        if "video" in summary["smokes"]:
            _print_line(f"video={summary['smokes']['video']}")
        if "audio" in summary["smokes"]:
            _print_line(f"audio={summary['smokes']['audio']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
