#!/usr/bin/env python3
"""Estimate approximate render-buffer memory for NeRF and 3D Gaussian Splatting.

The estimator is shape-based and uses only the Python standard library. It does
not load ML libraries, read datasets, or execute any renderer. Use it for
preflight comparison before deciding whether a render configuration is small
enough to try.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Dict, Iterable, List, Tuple


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {text!r}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return value


def nonnegative_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a number, got {text!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return value


def positive_float(text: str) -> float:
    value = nonnegative_float(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return value


def human_bytes(num_bytes: float) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    value = float(num_bytes)
    for unit in units:
        if abs(value) < 1024.0 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PiB"


def ceil_int(value: float) -> int:
    return int(math.ceil(value))


def estimate_nerf(args: argparse.Namespace) -> Dict[str, Any]:
    pixels = args.height * args.width
    full_rays = args.rays if args.rays is not None else pixels
    chunk_rays = args.chunk_rays if args.chunk_rays is not None else full_rays
    chunk_rays = min(chunk_rays, full_rays)
    samples = chunk_rays * args.nb_bins

    # Typical no-grad render_rays scratch includes t/delta/alpha/transmittance,
    # sampled xyz, expanded directions, colors, sigma, weights, and output RGB.
    # It excludes model parameters, autograd activations, optimizer state,
    # dataloader copies, and framework allocator fragmentation.
    core_bytes = samples * args.nerf_float_buffers * args.dtype_bytes
    chunk_rgb_bytes = chunk_rays * 3 * args.dtype_bytes
    full_output_bytes = full_rays * 3 * args.dtype_bytes
    overhead_bytes = args.nerf_overhead_mib * 1024 * 1024
    total = core_bytes + chunk_rgb_bytes + full_output_bytes + overhead_bytes

    return {
        "mode": "nerf",
        "height": args.height,
        "width": args.width,
        "full_rays": full_rays,
        "chunk_rays": chunk_rays,
        "nb_bins": args.nb_bins,
        "ray_bin_samples_in_chunk": samples,
        "dtype_bytes": args.dtype_bytes,
        "assumed_float_buffers_per_ray_bin": args.nerf_float_buffers,
        "core_ray_bin_buffers_bytes": int(core_bytes),
        "chunk_rgb_bytes": int(chunk_rgb_bytes),
        "full_output_rgb_bytes": int(full_output_bytes),
        "extra_overhead_bytes": int(overhead_bytes),
        "estimated_bytes": int(total),
        "notes": [
            "Approximate no-grad render scratch for ray/bin tensors.",
            "Training can require several times more memory because of activations, gradients, optimizer state, and data copies.",
            "If the renderer processes image rows or ray chunks, set --chunk-rays to the largest chunk rather than H*W.",
        ],
    }


def estimate_3dgs(args: argparse.Namespace) -> Dict[str, Any]:
    pixels = args.height * args.width
    visible_gaussians = ceil_int(args.gaussians * args.visible_ratio)
    tiles_u = ceil_int(args.width / args.tile_size)
    tiles_v = ceil_int(args.height / args.tile_size)
    tile_count = tiles_u * tiles_v
    tile_refs = ceil_int(visible_gaussians * args.avg_tiles_per_gaussian)

    image_bytes = pixels * args.image_float_fields * args.dtype_bytes
    gaussian_state_bytes = visible_gaussians * args.gaussian_float_fields * args.dtype_bytes
    tile_ref_bytes = tile_refs * args.tile_reference_int_fields * args.int_bytes
    tile_range_bytes = tile_count * 2 * args.int_bytes
    tile_scratch_bytes = (
        args.avg_gaussians_per_tile
        * (args.tile_size * args.tile_size)
        * args.tile_scratch_float_fields
        * args.dtype_bytes
    )
    total = image_bytes + gaussian_state_bytes + tile_ref_bytes + tile_range_bytes + tile_scratch_bytes

    return {
        "mode": "3dgs",
        "height": args.height,
        "width": args.width,
        "pixels": pixels,
        "gaussians_input": args.gaussians,
        "visible_ratio": args.visible_ratio,
        "visible_gaussians_estimate": visible_gaussians,
        "tile_size": args.tile_size,
        "tiles_u": tiles_u,
        "tiles_v": tiles_v,
        "tile_count": tile_count,
        "avg_tiles_per_gaussian": args.avg_tiles_per_gaussian,
        "tile_reference_count_estimate": tile_refs,
        "avg_gaussians_per_tile": args.avg_gaussians_per_tile,
        "dtype_bytes": args.dtype_bytes,
        "int_bytes": args.int_bytes,
        "image_buffer_bytes": int(image_bytes),
        "gaussian_state_bytes": int(gaussian_state_bytes),
        "tile_reference_bytes": int(tile_ref_bytes),
        "tile_range_bytes": int(tile_range_bytes),
        "one_tile_compositing_scratch_bytes": int(tile_scratch_bytes),
        "estimated_bytes": int(total),
        "notes": [
            "Approximate visible Gaussian, tile-list, one-tile scratch, and final image buffers.",
            "Peak memory can be higher because renderers may keep projected covariances, sorted copies, color tensors, framework allocator caches, and source assets resident.",
            "Increase --avg-tiles-per-gaussian for large projected covariances, high pix_guard, or weak culling.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate approximate memory for NeRF rays*bins and 3D Gaussian "
            "splatting Gaussian/tile/image buffers without importing torch."
        )
    )
    parser.add_argument("--mode", choices=("nerf", "3dgs", "both"), default="both", help="which estimate to print")
    parser.add_argument("--height", type=positive_int, default=400, help="render image height in pixels")
    parser.add_argument("--width", type=positive_int, default=400, help="render image width in pixels")
    parser.add_argument("--dtype-bytes", type=positive_int, default=4, help="bytes per floating-point value, usually 4 for float32 or 2 for float16")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a text report")

    nerf = parser.add_argument_group("NeRF ray/bin options")
    nerf.add_argument("--rays", type=positive_int, default=None, help="total rays to render; defaults to height*width")
    nerf.add_argument("--chunk-rays", type=positive_int, default=None, help="largest ray chunk processed at once; defaults to total rays")
    nerf.add_argument("--nb-bins", type=positive_int, default=192, help="samples/bins per ray")
    nerf.add_argument("--nerf-float-buffers", type=positive_float, default=14.0, help="approximate simultaneous float buffers per ray-bin sample for no-grad render_rays")
    nerf.add_argument("--nerf-overhead-mib", type=nonnegative_float, default=0.0, help="optional extra MiB for model/cache/framework overhead to add to the NeRF estimate")

    gs = parser.add_argument_group("3D Gaussian Splatting options")
    gs.add_argument("--gaussians", type=positive_int, default=100_000, help="number of input Gaussians/primitives")
    gs.add_argument("--visible-ratio", type=positive_float, default=1.0, help="fraction of input Gaussians expected to remain after frustum/near/far culling")
    gs.add_argument("--tile-size", type=positive_int, default=16, help="square tile size in pixels")
    gs.add_argument("--avg-tiles-per-gaussian", type=positive_float, default=4.0, help="average number of tiles touched by each visible Gaussian")
    gs.add_argument("--avg-gaussians-per-tile", type=positive_float, default=64.0, help="representative number of Gaussians composited in one tile scratch buffer")
    gs.add_argument("--gaussian-float-fields", type=positive_float, default=32.0, help="approximate retained float fields per visible Gaussian after projection/covariance/color preparation")
    gs.add_argument("--tile-reference-int-fields", type=positive_float, default=3.0, help="integer-like fields per Gaussian-tile reference, e.g. Gaussian id, tile id, sort key/copy")
    gs.add_argument("--tile-scratch-float-fields", type=positive_float, default=6.0, help="float fields per Gaussian-pixel pair in a representative tile scratch calculation")
    gs.add_argument("--image-float-fields", type=positive_float, default=3.0, help="float fields per output pixel, normally RGB=3")
    gs.add_argument("--int-bytes", type=positive_int, default=8, help="bytes per integer/sort-index value")
    return parser


def rows_for_report(estimate: Dict[str, Any]) -> List[Tuple[str, str]]:
    scalar_size_keys = {"dtype_bytes", "int_bytes"}
    byte_keys = [key for key in estimate if key.endswith("_bytes") and key not in scalar_size_keys]
    rows: List[Tuple[str, str]] = []
    for key, value in estimate.items():
        if key == "notes":
            continue
        if key in byte_keys:
            rows.append((key, f"{value} ({human_bytes(float(value))})"))
        else:
            rows.append((key, str(value)))
    return rows


def print_text_report(estimates: Iterable[Dict[str, Any]]) -> None:
    print("Approximate render memory estimate")
    print("==================================")
    for estimate in estimates:
        print(f"\n[{estimate['mode']}]")
        for key, value in rows_for_report(estimate):
            print(f"{key}: {value}")
        print("notes:")
        for note in estimate.get("notes", []):
            print(f"  - {note}")


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.visible_ratio > 1.0:
        parser.error("--visible-ratio should be <= 1.0 for a culled visible fraction")

    estimates: List[Dict[str, Any]] = []
    if args.mode in ("nerf", "both"):
        estimates.append(estimate_nerf(args))
    if args.mode in ("3dgs", "both"):
        estimates.append(estimate_3dgs(args))

    if args.json:
        print(json.dumps({"estimates": estimates}, indent=2, sort_keys=True))
    else:
        print_text_report(estimates)
    return 0


if __name__ == "__main__":
    sys.exit(main())
