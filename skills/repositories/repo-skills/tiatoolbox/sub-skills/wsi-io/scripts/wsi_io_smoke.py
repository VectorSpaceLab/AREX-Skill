#!/usr/bin/env python3
"""Tiny WSI I/O smoke checks for the TIAToolbox wsi-io skill.

This script intentionally avoids network access and WSI downloads. It uses a
small numpy array with VirtualWSIReader to verify imports, metadata, read_rect,
read_bounds, slide_thumbnail, and multichannel preservation. Registration is
reported by module availability only; the script never constructs registration
models or downloads weights.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from typing import Any


def _json_ready(value: Any) -> Any:
    """Convert common numpy/path-like objects into JSON-friendly values."""
    try:
        import numpy as np
    except ModuleNotFoundError:  # pragma: no cover - help path on bare Python
        np = None

    if np is not None and isinstance(value, np.ndarray):
        return value.tolist()
    if np is not None and isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def run_tiny_smoke() -> dict[str, Any]:
    """Run a tiny in-memory WSIReader smoke check."""
    import numpy as np

    from tiatoolbox.wsicore.wsireader import VirtualWSIReader, WSIReader
    from tiatoolbox.wsicore.wsimeta import WSIMeta

    rgb = np.zeros((64, 96, 3), dtype=np.uint8)
    rgb[8:56, 16:80] = [180, 60, 120]

    reader = WSIReader.open(rgb, mpp=(0.5, 0.5), post_proc=None)
    rect = reader.read_rect((4, 6), (24, 16), resolution=0, units="level")
    bounds = reader.read_bounds((0, 0, 48, 32), resolution=1.0, units="baseline")
    thumbnail = reader.slide_thumbnail(resolution=1.0, units="baseline")
    converted = reader.convert_resolution_units(1.0, "baseline")

    feature = np.zeros((32, 40, 5), dtype=np.uint8)
    feature[..., 0] = 1
    feature_meta = WSIMeta(slide_dimensions=(40, 32), axes="YXS", mpp=(1.0, 1.0))
    feature_reader = VirtualWSIReader(
        feature,
        info=feature_meta,
        mode="feature",
        post_proc=None,
    )
    feature_crop = feature_reader.read_rect((0, 0), (8, 8), resolution=0, units="level")

    registration_status = (
        "module available; construction intentionally skipped to avoid downloads"
        if importlib.util.find_spec("tiatoolbox.tools.registration.wsi_registration")
        else "module unavailable"
    )

    return {
        "reader_class": type(reader).__name__,
        "metadata": _json_ready(reader.info.as_dict()),
        "rect_shape": list(rect.shape),
        "bounds_shape": list(bounds.shape),
        "thumbnail_shape": list(thumbnail.shape),
        "baseline_conversion": _json_ready(converted),
        "feature_reader_class": type(feature_reader).__name__,
        "feature_crop_shape": list(feature_crop.shape),
        "feature_channels_preserved": feature_crop.shape[-1] == 5,
        "registration": registration_status,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run safe, tiny TIAToolbox WSI I/O checks using numpy arrays and "
            "VirtualWSIReader. No network access or WSI fixtures are required."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["tiny"],
        default="tiny",
        help="Smoke mode to run. Only 'tiny' is intentionally supported.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print compact JSON instead of a readable summary.",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.mode != "tiny":
        parser.error("Only --mode tiny is supported")

    result = run_tiny_smoke()
    if args.json:
        print(json.dumps(result, sort_keys=True))
        return

    print("TIAToolbox WSI I/O tiny smoke: OK")
    print(f"reader: {result['reader_class']}")
    print(f"rect_shape: {result['rect_shape']}")
    print(f"bounds_shape: {result['bounds_shape']}")
    print(f"thumbnail_shape: {result['thumbnail_shape']}")
    print(f"feature_crop_shape: {result['feature_crop_shape']}")
    print(f"feature_channels_preserved: {result['feature_channels_preserved']}")
    print(f"registration: {result['registration']}")


if __name__ == "__main__":
    main()
