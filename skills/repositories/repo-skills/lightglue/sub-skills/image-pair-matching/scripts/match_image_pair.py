#!/usr/bin/env python3
"""Match a pair of images with LightGlue.

This script expands the README/demo flow into a CLI with explicit device
selection, feature pairing, coordinate extraction, and optional visualization.
The compact helper equivalent is `lightglue.match_pair`.
"""

from __future__ import annotations

import argparse
import urllib.error
from pathlib import Path
from typing import Optional

SUPPORTED_FEATURES = ("superpoint", "disk", "aliked", "sift", "doghardnet")


def parse_optional_int(value: str) -> Optional[int]:
    text = str(value).strip().lower()
    if text in {"none", "null", "off", "all", "full"}:
        return None
    try:
        parsed = int(text)
    except ValueError as exc:  # pragma: no cover - argparse validation path
        raise argparse.ArgumentTypeError(
            "expected a positive integer or 'none'"
        ) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer or 'none'")
    return parsed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Match two images with LightGlue and save an optional visualization."
    )
    parser.add_argument("--image0", required=True, type=Path, help="path to image 0")
    parser.add_argument("--image1", required=True, type=Path, help="path to image 1")
    parser.add_argument(
        "--features",
        choices=SUPPORTED_FEATURES,
        default="superpoint",
        help="extractor/matcher family; use sift to avoid neural extractor downloads",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda", "mps"),
        default="auto",
        help="compute device to use",
    )
    parser.add_argument(
        "--max-keypoints",
        type=parse_optional_int,
        default=2048,
        help="cap keypoints per image; use 'none' to keep the extractor default",
    )
    parser.add_argument(
        "--resize",
        type=parse_optional_int,
        default=1024,
        help="resize the longest edge before extraction; use 'none' to keep original size",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="optional path for the saved visualization PNG",
    )
    parser.add_argument(
        "--no-viz",
        action="store_true",
        help="skip interactive display after matching",
    )
    return parser.parse_args(argv)


def fail(message: str, exc: Exception | None = None) -> None:
    if exc is not None:
        message = f"{message}\n\nOriginal error: {exc}"
    raise SystemExit(message)


def resolve_device(choice: str):
    import torch

    if choice == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if choice == "cuda":
        if not torch.cuda.is_available():
            fail(
                "CUDA was requested but torch.cuda.is_available() is False. "
                "Re-run with --device auto or --device cpu."
            )
        return torch.device("cuda")
    if choice == "mps":
        mps = getattr(torch.backends, "mps", None)
        if mps is None or not mps.is_available():
            fail(
                "MPS was requested but is not available. Re-run with --device auto "
                "or --device cpu."
            )
        return torch.device("mps")
    return torch.device("cpu")


def build_components(feature: str, max_keypoints: Optional[int], device: torch.device):
    try:
        from lightglue import ALIKED, DISK, DoGHardNet, LightGlue, SIFT, SuperPoint
    except ImportError as exc:  # pragma: no cover - import failure path
        fail(
            "Could not import the lightglue package. Install the runtime package "
            "and its dependencies before running this script.",
            exc,
        )

    try:
        if feature == "superpoint":
            extractor = (
                SuperPoint(max_num_keypoints=max_keypoints)
                if max_keypoints is not None
                else SuperPoint()
            )
        elif feature == "disk":
            extractor = (
                DISK(max_num_keypoints=max_keypoints)
                if max_keypoints is not None
                else DISK()
            )
        elif feature == "aliked":
            extractor = (
                ALIKED(max_num_keypoints=max_keypoints)
                if max_keypoints is not None
                else ALIKED()
            )
        elif feature == "sift":
            extractor = (
                SIFT(backend="opencv", max_num_keypoints=max_keypoints)
                if max_keypoints is not None
                else SIFT(backend="opencv")
            )
        elif feature == "doghardnet":
            extractor = (
                DoGHardNet(max_num_keypoints=max_keypoints)
                if max_keypoints is not None
                else DoGHardNet()
            )
        else:  # pragma: no cover - argparse choices prevent this
            raise ValueError(f"Unsupported feature family: {feature}")

        extractor = extractor.eval().to(device)
        matcher = LightGlue(features=feature).eval().to(device)
    except AttributeError as exc:
        if feature == "sift":
            fail(
                "OpenCV SIFT support is unavailable in this environment. Use an "
                "OpenCV build that exposes cv2.SIFT_create, or choose another feature.",
                exc,
            )
        fail(f"Could not initialize the {feature} extractor.", exc)
    except (OSError, RuntimeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        fail(
            f"Could not initialize the {feature} extractor or download pretrained "
            f"weights. Check network access, cache availability, and rerun.",
            exc,
        )

    return extractor, matcher


def main(argv=None) -> int:
    import torch

    args = parse_args(argv)
    args.image0 = args.image0.expanduser()
    args.image1 = args.image1.expanduser()
    if args.output is not None:
        args.output = args.output.expanduser()

    device = resolve_device(args.device)
    print(f"Using device: {device}")
    print(f"Using feature family: {args.features}")
    print("Note: the selected extractor and LightGlue head may download weights on first use.")

    try:
        from lightglue.utils import load_image, rbd
    except ImportError as exc:  # pragma: no cover - import failure path
        fail(
            "Could not import lightglue.utils. Install the runtime package and its "
            "dependencies before running this script.",
            exc,
        )

    try:
        image0 = load_image(args.image0).to(device)
        image1 = load_image(args.image1).to(device)
    except FileNotFoundError as exc:
        fail("One of the input image paths does not exist.", exc)
    except (OSError, ValueError) as exc:
        fail("One of the input images could not be read.", exc)

    extractor, matcher = build_components(args.features, args.max_keypoints, device)

    try:
        with torch.inference_mode():
            feats0 = extractor.extract(image0, resize=args.resize)
            feats1 = extractor.extract(image1, resize=args.resize)
            matches01 = matcher({"image0": feats0, "image1": feats1})
            feats0, feats1, matches01 = [rbd(x) for x in (feats0, feats1, matches01)]
    except (RuntimeError, ValueError, AssertionError) as exc:
        fail(
            "Matching failed. If you requested a GPU or MPS device, try --device cpu. "
            "If the images are large, lower --resize or --max-keypoints.",
            exc,
        )

    matches = matches01["matches"]
    points0 = feats0["keypoints"][matches[:, 0]]
    points1 = feats1["keypoints"][matches[:, 1]]

    print(f"Image 0 keypoints: {len(feats0['keypoints'])}")
    print(f"Image 1 keypoints: {len(feats1['keypoints'])}")
    print(f"Matches: {len(matches)}")
    print(f"Stopped after {matches01['stop']} layers")

    if args.output is not None or not args.no_viz:
        if args.output is not None:
            import matplotlib

            matplotlib.use("Agg", force=True)

        from lightglue import viz2d
        import matplotlib.pyplot as plt

        viz2d.plot_images([image0.cpu(), image1.cpu()])
        viz2d.plot_matches(points0.cpu(), points1.cpu(), color="lime", lw=0.2)
        viz2d.add_text(
            0,
            f"{args.features} | {len(matches)} matches | stop {matches01['stop']} layers",
            fs=18,
        )

        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            viz2d.save_plot(args.output, dpi=200)
            print(f"Saved visualization: {args.output}")
        if not args.no_viz and args.output is None:
            plt.show()
        plt.close("all")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
