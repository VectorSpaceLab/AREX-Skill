#!/usr/bin/env python3
"""Inspect tiny MMDetection3D geometry and visualization helpers.

The helper is synthetic and CPU-only by default. It prints a compact report for
box origins, yaw conversion, point projection, and an optional visualizer smoke
check. It does not load checkpoints or open a live window.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


def build_parser() -> argparse.ArgumentParser:
    epilog = """Examples:
  python scripts/inspect_geometry.py
  python scripts/inspect_geometry.py --json
  python scripts/inspect_geometry.py --visualizer-smoke
"""
    return argparse.ArgumentParser(
        description=(
            "Inspect MMDetection3D box, point, projection, and visualizer "
            "geometry with tiny synthetic data."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of a short human-readable summary.",
    )
    parser.add_argument(
        "--visualizer-smoke",
        action="store_true",
        help=(
            "Also exercise Det3DLocalVisualizer on a blank RGB canvas. The "
            "smoke check stays headless-safe and does not call show()."
        ),
    )


def _prepend_visible_checkout() -> None:
    """Allow running the helper from a package checkout without installation."""
    cwd = Path.cwd()
    if (cwd / "mmdet3d" / "__init__.py").is_file():
        cwd_text = str(cwd)
        if cwd_text not in sys.path:
            sys.path.insert(0, cwd_text)


def _load_runtime() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    _prepend_visible_checkout()
    try:
        import numpy as np
        import torch

        import mmdet3d
        from mmdet3d.structures import (Box3DMode, CameraInstance3DBoxes,
                                        CameraPoints, Coord3DMode,
                                        DepthInstance3DBoxes, DepthPoints,
                                        LiDARInstance3DBoxes, LiDARPoints,
                                        points_cam2img, points_img2cam)
        from mmdet3d.structures.bbox_3d.utils import get_lidar2img, limit_period
        from mmdet3d.visualization.vis_utils import (
            proj_camera_bbox3d_to_img, proj_lidar_bbox3d_to_img)
    except Exception as exc:  # pragma: no cover - depends on caller env
        return None, f"{type(exc).__name__}: {exc}"

    return {
        "np": np,
        "torch": torch,
        "mmdet3d": mmdet3d,
        "Box3DMode": Box3DMode,
        "CameraInstance3DBoxes": CameraInstance3DBoxes,
        "CameraPoints": CameraPoints,
        "Coord3DMode": Coord3DMode,
        "DepthInstance3DBoxes": DepthInstance3DBoxes,
        "DepthPoints": DepthPoints,
        "LiDARInstance3DBoxes": LiDARInstance3DBoxes,
        "LiDARPoints": LiDARPoints,
        "points_cam2img": points_cam2img,
        "points_img2cam": points_img2cam,
        "get_lidar2img": get_lidar2img,
        "limit_period": limit_period,
        "proj_camera_bbox3d_to_img": proj_camera_bbox3d_to_img,
        "proj_lidar_bbox3d_to_img": proj_lidar_bbox3d_to_img,
    }, None


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if hasattr(value, "detach"):
        try:
            value = value.detach().cpu()
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _max_abs_error(tensor_a: Any, tensor_b: Any) -> float:
    diff = tensor_a - tensor_b
    return float(diff.abs().max().item())


def _visualizer_smoke(rt: Mapping[str, Any], cam_box: Any, cam2img: Any) -> Dict[str, Any]:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        from mmdet3d.visualization import Det3DLocalVisualizer
    except Exception as exc:  # pragma: no cover - optional dependency
        return {
            "status": "skipped",
            "reason": f"{type(exc).__name__}: {exc}",
        }

    np = rt["np"]
    try:
        visualizer = Det3DLocalVisualizer()
        visualizer.set_image(np.zeros((64, 96, 3), dtype=np.uint8))
        visualizer.draw_proj_bboxes_3d(cam_box, {"cam2img": cam2img})
        drawn = None
        if hasattr(visualizer, "get_image"):
            try:
                drawn = visualizer.get_image()
            except Exception:
                drawn = None
        return {
            "status": "ok",
            "drawn_shape": list(drawn.shape) if hasattr(drawn, "shape") else None,
        }
    except Exception as exc:  # pragma: no cover - optional dependency
        return {
            "status": "skipped",
            "reason": f"{type(exc).__name__}: {exc}",
        }


def build_report(rt: Mapping[str, Any], visualizer_smoke: bool) -> Dict[str, Any]:
    torch = rt["torch"]
    mmdet3d = rt["mmdet3d"]

    Box3DMode = rt["Box3DMode"]
    CameraInstance3DBoxes = rt["CameraInstance3DBoxes"]
    CameraPoints = rt["CameraPoints"]
    Coord3DMode = rt["Coord3DMode"]
    DepthInstance3DBoxes = rt["DepthInstance3DBoxes"]
    LiDARInstance3DBoxes = rt["LiDARInstance3DBoxes"]
    points_cam2img = rt["points_cam2img"]
    points_img2cam = rt["points_img2cam"]
    get_lidar2img = rt["get_lidar2img"]
    limit_period = rt["limit_period"]
    proj_camera_bbox3d_to_img = rt["proj_camera_bbox3d_to_img"]
    proj_lidar_bbox3d_to_img = rt["proj_lidar_bbox3d_to_img"]

    report: Dict[str, Any] = {
        "package": {
            "mmdet3d_version": getattr(mmdet3d, "__version__", None),
        },
        "checks": {},
    }

    # Geometry smoke data that keeps boxes in front of the camera.
    lidar_box_tensor = torch.tensor(
        [[12.0, 0.0, 0.0, 2.0, 1.0, 1.0, 0.1]], dtype=torch.float32)
    lidar_box = LiDARInstance3DBoxes(lidar_box_tensor)
    cam_box = lidar_box.convert_to(Box3DMode.CAM)
    depth_box = lidar_box.convert_to(Box3DMode.DEPTH)

    lidar_roundtrip = cam_box.convert_to(Box3DMode.LIDAR)
    depth_roundtrip = depth_box.convert_to(Box3DMode.LIDAR)
    lidar_roundtrip_error = _max_abs_error(lidar_roundtrip.tensor,
                                           lidar_box.tensor)
    depth_roundtrip_error = _max_abs_error(depth_roundtrip.tensor,
                                           lidar_box.tensor)

    cam_default = CameraInstance3DBoxes(cam_box.tensor.clone())
    cam_origin_shift = CameraInstance3DBoxes(
        cam_box.tensor.clone(), origin=(0.5, 0.5, 0.5))

    cam_points = CameraPoints(
        torch.tensor([[0.5, -0.2, 12.0, 0.3], [1.5, 0.1, 8.0, 0.7]],
                     dtype=torch.float32),
        points_dim=4,
        attribute_dims={"score": [3]},
    )
    lidar_points = cam_points.convert_to(Coord3DMode.LIDAR)
    depth_points = cam_points.convert_to(Coord3DMode.DEPTH)
    point_tail_preserved = bool(
        torch.allclose(lidar_points.tensor[:, 3:], cam_points.tensor[:, 3:]))
    lidar_point_is_expected = isinstance(lidar_points, rt["LiDARPoints"])
    depth_point_is_expected = isinstance(depth_points, rt["DepthPoints"])

    cam2img = torch.tensor(
        [[60.0, 0.0, 48.0, 0.0],
         [0.0, 60.0, 32.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]],
        dtype=torch.float32,
    )
    lidar2cam = torch.tensor(
        [[0.0, -1.0, 0.0, 0.0],
         [0.0, 0.0, -1.0, 0.0],
         [1.0, 0.0, 0.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]],
        dtype=torch.float32,
    )
    lidar2img = get_lidar2img(cam2img, lidar2cam)

    cam_xyz = cam_points.tensor[:, :3]
    pixels_2d = points_cam2img(cam_xyz, cam2img)
    pixels_2d_depth = points_cam2img(cam_xyz, cam2img, with_depth=True)
    back_projected = points_img2cam(pixels_2d_depth, cam2img)
    back_projection_error = _max_abs_error(back_projected, cam_xyz)

    camera_box_proj = proj_camera_bbox3d_to_img(cam_default, {
        "cam2img": cam2img.numpy(),
    })
    lidar_box_proj = proj_lidar_bbox3d_to_img(lidar_box, {
        "lidar2img": lidar2img.numpy(),
    })

    report["checks"] = {
        "lidar_roundtrip": {
            "ok": lidar_roundtrip_error < 1e-5,
            "max_abs_error": lidar_roundtrip_error,
            "roundtrip_tensor": _plain(lidar_roundtrip.tensor),
        },
        "depth_roundtrip": {
            "ok": depth_roundtrip_error < 1e-5,
            "max_abs_error": depth_roundtrip_error,
            "roundtrip_tensor": _plain(depth_roundtrip.tensor),
        },
        "camera_origin_shift": {
            "default_tensor": _plain(cam_default.tensor),
            "shifted_tensor": _plain(cam_origin_shift.tensor),
            "delta": _plain(cam_origin_shift.tensor - cam_default.tensor),
        },
        "camera_yaw": {
            "yaw": _plain(cam_default.yaw),
            "local_yaw": _plain(cam_default.local_yaw),
            "wrapped_yaw": _plain(limit_period(cam_default.yaw,
                                               period=math.pi * 2)),
        },
        "points": {
            "camera_points": _plain(cam_points.tensor),
            "lidar_points": _plain(lidar_points.tensor),
            "depth_points": _plain(depth_points.tensor),
            "camera_point_class": type(cam_points).__name__,
            "lidar_point_class": type(lidar_points).__name__,
            "depth_point_class": type(depth_points).__name__,
            "lidar_point_is_expected": lidar_point_is_expected,
            "depth_point_is_expected": depth_point_is_expected,
            "tail_preserved": point_tail_preserved,
        },
        "projection": {
            "cam2img_shape": list(cam2img.shape),
            "lidar2img_shape": list(lidar2img.shape),
            "points_cam2img": _plain(pixels_2d),
            "points_cam2img_with_depth": _plain(pixels_2d_depth),
            "points_img2cam": _plain(back_projected),
            "back_projection_error": back_projection_error,
            "camera_box_proj_shape": list(camera_box_proj.shape),
            "lidar_box_proj_shape": list(lidar_box_proj.shape),
            "camera_box_proj_first_corner": _plain(camera_box_proj[0, 0]),
            "lidar_box_proj_first_corner": _plain(lidar_box_proj[0, 0]),
        },
    }

    if visualizer_smoke:
        report["checks"]["visualizer_smoke"] = _visualizer_smoke(
            rt, cam_default, cam2img.numpy())
    else:
        report["checks"]["visualizer_smoke"] = {
            "status": "not_requested",
        }

    return report


def print_summary(report: Mapping[str, Any]) -> None:
    checks = report["checks"]
    print(f"mmdet3d: {report['package'].get('mmdet3d_version')}")
    print(
        "lidar roundtrip max error:",
        checks["lidar_roundtrip"]["max_abs_error"],
    )
    print(
        "depth roundtrip max error:",
        checks["depth_roundtrip"]["max_abs_error"],
    )
    print("camera origin delta:", checks["camera_origin_shift"]["delta"])
    print("camera local yaw:", checks["camera_yaw"]["local_yaw"])
    print("points tail preserved:", checks["points"]["tail_preserved"])
    print(
        "points_cam2img back-projection error:",
        checks["projection"]["back_projection_error"],
    )
    print(
        "projection helper shapes:",
        checks["projection"]["camera_box_proj_shape"],
        checks["projection"]["lidar_box_proj_shape"],
    )
    print("visualizer smoke:", checks["visualizer_smoke"]["status"])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    add_arguments(parser)
    args = parser.parse_args(argv)

    runtime, error = _load_runtime()
    if runtime is None:
        print(
            "ERROR: MMDetection3D geometry helpers are unavailable.",
            file=sys.stderr,
        )
        print(f"Import failure: {error}", file=sys.stderr)
        return 2

    report = build_report(runtime, args.visualizer_smoke)
    if args.json:
        print(json.dumps(_plain(report), indent=2, sort_keys=True))
    else:
        print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
