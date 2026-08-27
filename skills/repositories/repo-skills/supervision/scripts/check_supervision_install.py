#!/usr/bin/env python3
"""Smoke-check an installed Supervision runtime without network or repo state.

The helper imports `supervision`, reports the selected OpenCV-compatible backend,
checks a few core APIs, and records optional dependency availability. It is safe
to run from any current working directory and does not download assets, open
windows, run models, or write output files.

Examples:
    python check_supervision_install.py
    python check_supervision_install.py --json
    python check_supervision_install.py --require-metrics
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class CheckResult:
    """Structured status for one environment check."""

    name: str
    status: str
    detail: str


def module_available(name: str) -> bool:
    """Return True when a module can be found without importing it."""
    return importlib.util.find_spec(name) is not None


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check an installed supervision package and optional media/metrics "
            "dependencies without downloads or model execution."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--require-metrics",
        action="store_true",
        help="Exit non-zero when the metrics extra/pandas is unavailable.",
    )
    parser.add_argument(
        "--require-geotiff",
        action="store_true",
        help="Exit non-zero when rasterio for GeoTIFF slicing is unavailable.",
    )
    parser.add_argument(
        "--require-native-opencv",
        action="store_true",
        help="Exit non-zero when native cv2 is unavailable and fallback backend is selected.",
    )
    return parser


def collect_checks() -> tuple[list[CheckResult], dict[str, Any]]:
    """Import Supervision and collect safe package/API checks."""
    checks: list[CheckResult] = []
    metadata: dict[str, Any] = {}

    try:
        import supervision as sv
    except Exception as exc:  # pragma: no cover - depends on caller environment
        checks.append(CheckResult("supervision-import", "fail", repr(exc)))
        return checks, metadata

    checks.append(CheckResult("supervision-import", "pass", "imported supervision"))
    metadata["version"] = getattr(sv, "__version__", "unknown")

    try:
        from supervision import _cv2

        metadata["cv2_backend"] = getattr(_cv2, "BACKEND_NAME", "unknown")
        metadata["cv2_available"] = bool(getattr(_cv2, "_IS_CV2_AVAILABLE", False))
        checks.append(
            CheckResult(
                "opencv-backend",
                "pass",
                f"backend={metadata['cv2_backend']}",
            )
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        checks.append(CheckResult("opencv-backend", "fail", repr(exc)))

    try:
        detections = sv.Detections.empty()
        key_points = sv.KeyPoints.empty()
        checks.append(
            CheckResult(
                "containers",
                "pass",
                f"Detections.empty={detections.xyxy.shape}, KeyPoints.empty={len(key_points)}",
            )
        )
    except Exception as exc:
        checks.append(CheckResult("containers", "fail", repr(exc)))

    for attr in [
        "BoxAnnotator",
        "DetectionDataset",
        "InferenceSlicer",
        "LineZone",
        "PolygonZone",
        "VideoInfo",
        "ColorPalette",
    ]:
        checks.append(
            CheckResult(
                f"public-api:{attr}",
                "pass" if hasattr(sv, attr) else "fail",
                "available" if hasattr(sv, attr) else "missing",
            )
        )

    optional = {
        "pandas": module_available("pandas"),
        "rasterio": module_available("rasterio"),
        "cv2": module_available("cv2"),
    }
    metadata["optional_modules"] = optional
    for name, available in optional.items():
        checks.append(
            CheckResult(
                f"optional:{name}",
                "pass" if available else "skip",
                "available" if available else "not installed",
            )
        )

    try:
        from supervision.assets import ImageAssets, VideoAssets, download_assets

        checks.append(
            CheckResult(
                "assets-module",
                "pass",
                (
                    f"download_assets={download_assets.__name__}; "
                    f"image_assets={len(list(ImageAssets))}; video_assets={len(list(VideoAssets))}"
                ),
            )
        )
    except Exception as exc:
        checks.append(CheckResult("assets-module", "fail", repr(exc)))

    return checks, metadata


def should_fail(
    checks: list[CheckResult],
    metadata: dict[str, Any],
    require_metrics: bool,
    require_geotiff: bool,
    require_native_opencv: bool,
) -> bool:
    """Decide whether requested required checks failed."""
    if any(check.status == "fail" for check in checks):
        return True
    optional = metadata.get("optional_modules", {})
    if require_metrics and not optional.get("pandas", False):
        return True
    if require_geotiff and not optional.get("rasterio", False):
        return True
    if require_native_opencv and not optional.get("cv2", False):
        return True
    return False


def print_text(checks: list[CheckResult], metadata: dict[str, Any]) -> None:
    """Print a human-readable report."""
    print("Supervision smoke check")
    print(f"version: {metadata.get('version', 'unknown')}")
    print(f"cv2_backend: {metadata.get('cv2_backend', 'unknown')}")
    print(f"cv2_available: {metadata.get('cv2_available', 'unknown')}")
    for check in checks:
        print(f"[{check.status}] {check.name}: {check.detail}")


def main(argv: list[str] | None = None) -> int:
    """Run checks and return a shell exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    checks, metadata = collect_checks()
    failed = should_fail(
        checks=checks,
        metadata=metadata,
        require_metrics=args.require_metrics,
        require_geotiff=args.require_geotiff,
        require_native_opencv=args.require_native_opencv,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "metadata": metadata,
                    "checks": [asdict(check) for check in checks],
                    "ok": not failed,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(checks=checks, metadata=metadata)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
