#!/usr/bin/env python3
"""Benchmark LightGlue matcher latency or throughput on one image pair.

The script extracts features for each requested keypoint count and then times
only the LightGlue matcher forward pass. If no image paths are supplied, it
uses a deterministic synthetic RGB pair for smoke testing; synthetic timings are
useful for checking that the pipeline runs but are not a quality benchmark.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.error import ContentTooShortError, HTTPError, URLError


SCRIPT_PATH = Path(__file__).resolve()
for parent in SCRIPT_PATH.parents:
    if (parent / "lightglue" / "__init__.py").is_file():
        sys.path.insert(0, str(parent))
        break

FEATURE_CHOICES = ("superpoint", "disk", "aliked", "sift", "doghardnet")
DEVICE_CHOICES = ("auto", "cpu", "cuda", "mps")
MEASURE_CHOICES = ("time", "log-time", "throughput")
NETWORK_ERRORS = (HTTPError, URLError, ContentTooShortError)


def positive_int(text: str) -> int:
    """Argparse type for strictly positive integers."""
    try:
        value = int(text)
    except ValueError as exc:  # pragma: no cover - argparse formats the error.
        raise argparse.ArgumentTypeError(f"expected an integer, got {text!r}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface without importing heavy dependencies."""
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark LightGlue matcher forward latency after feature extraction. "
            "Pass both image paths for meaningful numbers, or omit both for a "
            "deterministic synthetic smoke input."
        )
    )
    parser.add_argument("--image0", type=Path, default=None, help="first RGB image path")
    parser.add_argument("--image1", type=Path, default=None, help="second RGB image path")
    parser.add_argument(
        "--device",
        choices=DEVICE_CHOICES,
        default="auto",
        help="device selection; auto prefers cuda, then mps, then cpu",
    )
    parser.add_argument(
        "--features",
        choices=FEATURE_CHOICES,
        default="superpoint",
        help="extractor and matching-weight family to benchmark",
    )
    parser.add_argument(
        "--num-keypoints",
        nargs="+",
        type=positive_int,
        default=[256, 512],
        help="one or more requested keypoint counts",
    )
    parser.add_argument(
        "--repeat",
        type=positive_int,
        default=10,
        help="timed matcher-forward repetitions per keypoint count",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="compile LightGlue transformer blocks on CUDA before timing",
    )
    parser.add_argument(
        "--no-flash",
        action="store_true",
        help="disable FlashAttention / scaled-dot-product flash paths when possible",
    )
    parser.add_argument(
        "--depth-confidence",
        type=float,
        default=None,
        help="override LightGlue depth_confidence; use -1 to disable early stopping",
    )
    parser.add_argument(
        "--width-confidence",
        type=float,
        default=None,
        help="override LightGlue width_confidence; use -1 to disable point pruning",
    )
    parser.add_argument(
        "--measure",
        choices=MEASURE_CHOICES,
        default="time",
        help="quantity to emphasize in the optional plot",
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=None,
        help="optional output path for a latency or throughput figure",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="skip interactive matplotlib display",
    )
    parser.add_argument(
        "--max-resize",
        type=positive_int,
        default=1024,
        help="resize the long image side to at most this value before extraction",
    )
    parser.add_argument(
        "--pruning-thresholds",
        nargs="*",
        default=None,
        metavar="DEVICE=N",
        help=(
            "optional LightGlue pruning threshold overrides, e.g. "
            "cpu=256 mps=-1 cuda=1024 flash=1536"
        ),
    )
    parser.add_argument(
        "--matmul-precision",
        choices=("highest", "high", "medium"),
        default="highest",
        help="set torch float32 matmul precision when the runtime supports it",
    )
    return parser


def parse_pruning_thresholds(items: Optional[Sequence[str]]) -> Optional[Dict[str, int]]:
    """Parse optional pruning threshold overrides used by LightGlue."""
    if not items:
        return None
    allowed = {"cpu", "mps", "cuda", "flash"}
    parsed: Dict[str, int] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"{item!r} is not in DEVICE=N form")
        key, raw_value = item.split("=", 1)
        key = key.strip().lower()
        if key not in allowed:
            raise ValueError(f"unknown pruning key {key!r}; choose from {sorted(allowed)}")
        try:
            parsed[key] = int(raw_value)
        except ValueError as exc:
            raise ValueError(f"invalid threshold value in {item!r}") from exc
    return parsed


def import_lightglue_components():
    """Import runtime dependencies after argparse so --help stays lightweight."""
    import torch

    from lightglue import ALIKED, DISK, DoGHardNet, LightGlue, SIFT, SuperPoint
    from lightglue.utils import load_image

    extractors = {
        "superpoint": SuperPoint,
        "disk": DISK,
        "aliked": ALIKED,
        "sift": SIFT,
        "doghardnet": DoGHardNet,
    }
    return torch, LightGlue, extractors, load_image


def select_device(torch, requested: str):
    """Resolve auto/cpu/cuda/mps to a torch.device with explicit errors."""
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
    if requested == "mps" and not (
        hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    ):
        raise RuntimeError("MPS was requested but this PyTorch build cannot use MPS.")
    return torch.device(requested)


def make_synthetic_pair(torch) -> Tuple[object, object]:
    """Create a deterministic small RGB tensor pair for offline smoke tests."""
    height, width = 256, 320
    y = torch.linspace(0.0, 1.0, height)
    x = torch.linspace(0.0, 1.0, width)
    try:
        yy, xx = torch.meshgrid(y, x, indexing="ij")
    except TypeError:  # Older PyTorch compatibility.
        yy, xx = torch.meshgrid(y, x)

    checker = ((torch.floor(xx * 16) + torch.floor(yy * 12)) % 2) * 0.25
    image0 = torch.stack(
        [
            (xx + checker).clamp(0, 1),
            (yy + 0.5 * checker).clamp(0, 1),
            (0.5 * xx + 0.5 * yy + checker).clamp(0, 1),
        ],
        dim=0,
    ).float()

    generator = torch.Generator().manual_seed(7)
    noise = torch.rand((3, height, width), generator=generator) * 0.015
    image1 = (0.98 * torch.roll(image0, shifts=(5, -7), dims=(-2, -1)) + noise).clamp(
        0, 1
    )
    return image0, image1


def load_inputs(args, torch, load_image) -> Tuple[object, object, bool]:
    """Load a real image pair or create the synthetic fallback pair."""
    if args.image0 is None and args.image1 is None:
        print(
            "WARNING: no --image0/--image1 supplied; using deterministic synthetic "
            "RGB tensors for smoke testing only. This is not a quality benchmark.",
            file=sys.stderr,
        )
        image0, image1 = make_synthetic_pair(torch)
        return image0, image1, True

    # Real-image loading deliberately avoids repo assets and uses user paths only.
    image0 = load_image(args.image0)
    image1 = load_image(args.image1)
    return image0, image1, False


def synchronize_if_needed(torch, device) -> None:
    """Synchronize asynchronous backends around perf_counter measurements."""
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "synchronize"):
        torch.mps.synchronize()


def measure_matcher(torch, matcher, data: Dict[str, object], device, repeat: int) -> Dict[str, float]:
    """Measure matcher forward; CUDA uses events, other devices use perf_counter."""
    warmup = min(2, max(1, repeat // 2))
    with torch.inference_mode():
        for _ in range(warmup):
            matcher(data)

        timings_ms: List[float] = []
        if device.type == "cuda":
            starter = torch.cuda.Event(enable_timing=True)
            ender = torch.cuda.Event(enable_timing=True)
            for _ in range(repeat):
                starter.record()
                matcher(data)
                ender.record()
                torch.cuda.synchronize()
                timings_ms.append(float(starter.elapsed_time(ender)))
        else:
            for _ in range(repeat):
                synchronize_if_needed(torch, device)
                start = time.perf_counter()
                matcher(data)
                synchronize_if_needed(torch, device)
                timings_ms.append((time.perf_counter() - start) * 1000.0)

    mean_ms = sum(timings_ms) / len(timings_ms)
    variance = sum((value - mean_ms) ** 2 for value in timings_ms) / len(timings_ms)
    return {
        "mean_ms": mean_ms,
        "std_ms": math.sqrt(variance),
        "throughput": 1000.0 / mean_ms if mean_ms > 0 else float("inf"),
    }


def make_extractor(extractor_cls, feature_name: str, num_keypoints: int):
    """Construct the requested extractor with a consistent keypoint-count knob."""
    kwargs = {"max_num_keypoints": num_keypoints}
    if feature_name == "superpoint":
        # A permissive threshold makes the synthetic smoke input less brittle while
        # still capping features by --num-keypoints.
        kwargs["detection_threshold"] = 0.0001
    return extractor_cls(**kwargs)


def count_keypoints(features: Dict[str, object]) -> int:
    """Return the number of keypoints from a LightGlue feature dictionary."""
    return int(features["keypoints"].shape[-2])


def print_table(results: List[Dict[str, float]]) -> None:
    """Print a compact benchmark table."""
    header = (
        f"{'requested':>10} {'actual0':>8} {'actual1':>8} "
        f"{'mean_ms':>10} {'std_ms':>9} {'pairs/s':>10}"
    )
    print(header)
    print("-" * len(header))
    for row in results:
        print(
            f"{int(row['requested']):10d} {int(row['actual0']):8d} "
            f"{int(row['actual1']):8d} {row['mean_ms']:10.3f} "
            f"{row['std_ms']:9.3f} {row['throughput']:10.2f}"
        )


def maybe_plot(results: List[Dict[str, float]], args) -> None:
    """Save and/or show a latency/throughput figure without requiring a display."""
    headless = bool(args.no_show)
    if not headless and sys.platform != "darwin":
        headless = not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if args.save is None and headless:
        return

    if headless:
        import matplotlib

        # Agg works in headless jobs and still allows saving a figure.
        matplotlib.use("Agg", force=True)

    import matplotlib.pyplot as plt

    xs = [row["requested"] for row in results]
    if args.measure == "throughput":
        ys = [row["throughput"] for row in results]
        ylabel = "Throughput [pairs/s]"
    else:
        ys = [row["mean_ms"] for row in results]
        ylabel = "Latency [ms]"

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(xs, ys, marker="o", label="LightGlue")
    ax.set_xscale("log", base=2)
    if args.measure == "log-time":
        ax.set_yscale("log")
    ax.set_xlabel("Requested keypoints")
    ax.set_ylabel(ylabel)
    ax.set_title(f"LightGlue {args.features} matcher benchmark")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if args.save is not None:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.save, dpi=160)
        print(f"Saved figure: {args.save}")

    if not args.no_show:
        plt.show()
    plt.close(fig)


def run(args) -> int:
    """Execute the benchmark after argument validation."""
    pruning_thresholds = parse_pruning_thresholds(args.pruning_thresholds)
    torch, LightGlue, extractors, load_image = import_lightglue_components()
    torch.set_grad_enabled(False)
    if hasattr(torch, "set_float32_matmul_precision"):
        torch.set_float32_matmul_precision(args.matmul_precision)

    device = select_device(torch, args.device)
    image0, image1, synthetic_input = load_inputs(args, torch, load_image)
    image0 = image0.to(device)
    image1 = image1.to(device)

    print("First use may download pretrained extractor or matcher weights.")
    print(
        "Timing measures matcher forward only; feature extraction is completed "
        "before each timing loop."
    )
    print(
        f"Device: {device.type} | features: {args.features} | flash: {not args.no_flash} "
        f"| compile requested: {args.compile}"
    )

    matcher_conf = {}
    if args.depth_confidence is not None:
        matcher_conf["depth_confidence"] = args.depth_confidence
    if args.width_confidence is not None:
        matcher_conf["width_confidence"] = args.width_confidence

    matcher = LightGlue(features=args.features, flash=not args.no_flash, **matcher_conf).eval().to(device)
    if matcher_conf:
        print(f"Matcher overrides: {matcher_conf}")
    if pruning_thresholds is not None:
        matcher.pruning_keypoint_thresholds = {
            **matcher.pruning_keypoint_thresholds,
            **pruning_thresholds,
        }
        print(f"Pruning thresholds: {matcher.pruning_keypoint_thresholds}")

    compiled = False
    if args.compile:
        if device.type != "cuda":
            print(
                f"NOTE: --compile is intended for CUDA; running eager mode on {device.type}.",
                file=sys.stderr,
            )
        else:
            if hasattr(torch, "_dynamo"):
                torch._dynamo.reset()
            static_lengths = sorted(set(args.num_keypoints + [256, 512, 768, 1024, 1280, 1536]))
            matcher.compile(static_lengths=static_lengths)
            compiled = True
    print(f"Compiled matcher: {compiled}")

    results: List[Dict[str, float]] = []
    preprocess_resize = None if synthetic_input else args.max_resize
    extractor_cls = extractors[args.features]

    with torch.inference_mode():
        for num_keypoints in args.num_keypoints:
            extractor = make_extractor(extractor_cls, args.features, num_keypoints).eval().to(device)
            feats0 = extractor.extract(image0, resize=preprocess_resize)
            feats1 = extractor.extract(image1, resize=preprocess_resize)
            actual0 = count_keypoints(feats0)
            actual1 = count_keypoints(feats1)
            if actual0 == 0 or actual1 == 0:
                raise RuntimeError(
                    "The extractor returned zero keypoints for at least one image. "
                    "Try real textured images, a different feature family, or a smaller resize."
                )

            timing = measure_matcher(
                torch,
                matcher,
                {"image0": feats0, "image1": feats1},
                device,
                args.repeat,
            )
            results.append(
                {
                    "requested": float(num_keypoints),
                    "actual0": float(actual0),
                    "actual1": float(actual1),
                    **timing,
                }
            )
            del extractor, feats0, feats1
            if device.type == "cuda":
                torch.cuda.empty_cache()

    print_table(results)
    maybe_plot(results, args)
    return 0


def actionable_error(exc: BaseException) -> str:
    """Convert expected runtime failures into concise recovery guidance."""
    if isinstance(exc, ImportError):
        return (
            'Import failed while loading LightGlue or its dependencies. Install the '
            'package and required runtime libraries such as torch, torchvision, '
            'numpy, opencv-python, matplotlib, and kornia. Original error: '
            f'{exc}'
        )
    if isinstance(exc, NETWORK_ERRORS):
        return (
            "A pretrained weight download failed. Check network/proxy access, retry "
            f"later, or pre-populate the PyTorch model cache. Original error: {exc}"
        )
    if isinstance(exc, OSError):
        return (
            "File or network access failed. Check image paths, permissions, and "
            f"weight-download connectivity. Original error: {exc}"
        )
    if isinstance(exc, RuntimeError):
        return (
            "Benchmark runtime failed. Verify that the requested device backend is "
            "available, dependencies match the selected feature family, and pretrained "
            "weights can be downloaded or are cached. For a smoke run, try "
            f"--device cpu --repeat 1 --num-keypoints 128. Original error: {exc}"
        )
    return f"Unexpected error: {exc}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.image0 is None) != (args.image1 is None):
        parser.error("--image0 and --image1 must be supplied together, or neither for synthetic input")
    try:
        return run(args)
    except (ImportError, RuntimeError, OSError, *NETWORK_ERRORS, ValueError) as exc:
        print(f"ERROR: {actionable_error(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
