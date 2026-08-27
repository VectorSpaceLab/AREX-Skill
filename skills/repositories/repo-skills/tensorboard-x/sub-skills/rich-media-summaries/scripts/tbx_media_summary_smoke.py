#!/usr/bin/env python3
"""Run a tiny tensorboardX rich-media smoke in a temporary run directory.

The helper writes a few small payloads and skips optional media branches when
those dependencies are unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

import numpy as np
from tensorboardX import SummaryWriter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="directory to keep the smoke run; defaults to a temporary directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of a short text summary",
    )
    return parser


def _tiny_image() -> np.ndarray:
    image = np.zeros((3, 8, 8), dtype=np.float32)
    image[0, 2:6, 2:6] = 0.9
    image[1, 1:7, 1:7] = 0.2
    return image


def _tiny_boxes() -> np.ndarray:
    return np.array([[1, 1, 6, 6], [2, 2, 5, 5]], dtype=np.float32)


def _tiny_audio() -> np.ndarray:
    samples = np.linspace(0, 2 * math.pi, 800, dtype=np.float32)
    return 0.2 * np.sin(samples)


def _tiny_video() -> np.ndarray:
    # NTCHW with one clip, two frames, three channels, tiny spatial size.
    video = np.zeros((1, 2, 3, 4, 4), dtype=np.float32)
    video[:, :, 0, 1:3, 1:3] = 1.0
    video[:, :, 1, 0:2, 0:2] = 0.5
    return video


def _tiny_mesh() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices = np.array([
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    ], dtype=np.float32)
    colors = np.array([
        [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
    ], dtype=np.int32)
    faces = np.array([
        [[0, 1, 2]],
    ], dtype=np.int32)
    return vertices, colors, faces


def run_smoke(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[dict[str, str]] = []

    with SummaryWriter(output_dir, filename_suffix=".media-smoke") as writer:
        writer.add_image("media/image", _tiny_image(), 0)
        writer.add_image_with_boxes(
            "media/image_boxes",
            _tiny_image(),
            _tiny_boxes(),
            0,
            labels=["one", "two"],
        )
        writer.add_text("media/text", "tensorboardX media smoke", 0)
        writer.add_histogram("media/hist", np.linspace(-1.0, 1.0, 32), 0)
        writer.add_pr_curve(
            "media/pr",
            np.array([0, 0, 1, 1], dtype=np.int32),
            np.array([0.1, 0.4, 0.6, 0.9], dtype=np.float32),
            0,
        )
        writer.add_mesh("media/mesh", *_tiny_mesh(), global_step=0)
        written.extend(["image", "image_with_boxes", "text", "histogram", "pr_curve", "mesh"])

        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            skipped.append({"payload": "figure", "reason": str(exc)})
        else:
            fig = plt.figure(figsize=(1.5, 1.5))
            ax = fig.add_subplot(1, 1, 1)
            ax.plot([0, 1], [0, 1])
            ax.set_title("smoke")
            writer.add_figure("media/figure", fig, 0)
            written.append("figure")

        try:
            import soundfile  # noqa: F401
        except ImportError as exc:
            skipped.append({"payload": "audio", "reason": str(exc)})
        else:
            writer.add_audio("media/audio", _tiny_audio(), 0, sample_rate=8000)
            written.append("audio")

        try:
            import moviepy  # noqa: F401
            import imageio  # noqa: F401
        except ImportError as exc:
            skipped.append({"payload": "video", "reason": str(exc)})
        else:
            writer.add_video("media/video", _tiny_video(), 0, fps=1)
            written.append("video")

        writer.flush()

    event_files = sorted(output_dir.glob("events.out.tfevents.*"))
    return {
        "output_dir": str(output_dir),
        "event_files": [p.name for p in event_files],
        "event_file_count": len(event_files),
        "written": written,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.output_dir is None:
        with tempfile.TemporaryDirectory(prefix="tbx-media-smoke-") as tmp:
            report = run_smoke(Path(tmp))
            report["temporary"] = True
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"output_dir: {report['output_dir']}")
                print(f"event_files: {report['event_file_count']}")
                print("written: " + ", ".join(report["written"]))
                if report["skipped"]:
                    print("skipped: " + ", ".join(f"{item['payload']} ({item['reason']})" for item in report["skipped"]))
                else:
                    print("skipped: none")
        return 0

    report = run_smoke(args.output_dir)
    report["temporary"] = False
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"output_dir: {report['output_dir']}")
        print(f"event_files: {report['event_file_count']}")
        print("written: " + ", ".join(report["written"]))
        if report["skipped"]:
            print("skipped: " + ", ".join(f"{item['payload']} ({item['reason']})" for item in report["skipped"]))
        else:
            print("skipped: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
