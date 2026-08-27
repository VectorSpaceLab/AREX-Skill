#!/usr/bin/env python3
"""Print installed stitching defaults, signatures, and public choices.

This helper is safe to run from any working directory. It imports the installed
package, optionally prepends a local checkout for editable-inspection use, and
prints a machine-readable summary of the verified public defaults.

Example:
  python scripts/inspect_stitching_defaults.py
  python scripts/inspect_stitching_defaults.py --json
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional local checkout to prepend to sys.path before importing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of human-readable text.",
    )
    return parser.parse_args()


def maybe_prepend_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    sys.path.insert(0, str(repo_root.resolve()))


def build_report() -> dict:
    import cv2 as cv
    import stitching
    from stitching import AffineStitcher, Stitcher
    from stitching.camera_adjuster import CameraAdjuster
    from stitching.camera_estimator import CameraEstimator
    from stitching.camera_wave_corrector import WaveCorrector
    from stitching.exposure_error_compensator import ExposureErrorCompensator
    from stitching.feature_detector import FeatureDetector
    from stitching.feature_matcher import FeatureMatcher
    from stitching.images import Images
    from stitching.seam_finder import SeamFinder
    from stitching.timelapser import Timelapser
    from stitching.warper import Warper
    from stitching.blender import Blender

    return {
        "package": {
            "name": stitching.__name__,
            "version": getattr(stitching, "__version__", None),
            "opencv_version": cv.__version__,
        },
        "signatures": {
            "Stitcher": str(inspect.signature(Stitcher)),
            "Stitcher.stitch": str(inspect.signature(Stitcher.stitch)),
            "Stitcher.stitch_verbose": str(inspect.signature(Stitcher.stitch_verbose)),
            "AffineStitcher": str(inspect.signature(AffineStitcher)),
            "FeatureDetector": str(inspect.signature(FeatureDetector)),
            "FeatureMatcher": str(inspect.signature(FeatureMatcher)),
            "Images.of": str(inspect.signature(Images.of)),
        },
        "defaults": {
            "stitcher": Stitcher.DEFAULT_SETTINGS,
            "affine": AffineStitcher.AFFINE_DEFAULTS,
            "detectors": list(FeatureDetector.DETECTOR_CHOICES.keys()),
            "matchers": list(FeatureMatcher.MATCHER_CHOICES),
            "camera_estimators": list(CameraEstimator.CAMERA_ESTIMATOR_CHOICES.keys()),
            "camera_adjusters": list(CameraAdjuster.CAMERA_ADJUSTER_CHOICES.keys()),
            "wave_correct": list(WaveCorrector.WAVE_CORRECT_CHOICES.keys()),
            "warpers": list(Warper.WARP_TYPE_CHOICES),
            "compensators": list(ExposureErrorCompensator.COMPENSATOR_CHOICES.keys()),
            "seam_finders": list(SeamFinder.SEAM_FINDER_CHOICES.keys()),
            "blenders": list(Blender.BLENDER_CHOICES),
            "timelapse": list(Timelapser.TIMELAPSE_CHOICES),
            "resolutions": {name: member.value for name, member in Images.Resolution.__members__.items()},
        },
    }


def main() -> int:
    args = parse_args()
    maybe_prepend_repo_root(args.repo_root)

    try:
        report = build_report()
    except Exception as exc:  # pragma: no cover - diagnostic helper
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload["error"])
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"stitching {report['package']['version']} / OpenCV {report['package']['opencv_version']}")
        print(f"Stitcher: {report['signatures']['Stitcher']}")
        print(f"AffineStitcher: {report['signatures']['AffineStitcher']}")
        print(f"Detectors: {', '.join(report['defaults']['detectors'])}")
        print(f"Matchers: {', '.join(report['defaults']['matchers'])}")
        print(f"Wave correction: {', '.join(report['defaults']['wave_correct'])}")
        print(f"Timelapse: {', '.join(report['defaults']['timelapse'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
