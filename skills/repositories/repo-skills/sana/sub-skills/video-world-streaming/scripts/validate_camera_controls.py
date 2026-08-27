#!/usr/bin/env python3
"""Validate Sana-WM action DSL and optional camera/intrinsics .npy files.

The script performs local, model-free checks only. It can be used before SANA-WM
bidirectional, chunk-causal, or streaming commands to catch malformed action
segments, outdated key assumptions, frame-count mismatches, invalid pose matrix
shapes, and intrinsics shapes/FOV ranges.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Sequence

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - depends on environment
    print(f"ERROR: numpy is required for .npy validation: {exc}", file=sys.stderr)
    raise SystemExit(2)

ALLOWED_ACTION_KEYS = set("wasdijkl")
KEY_MAP = {
    "w": "forward",
    "s": "back",
    "a": "yaw_left",
    "d": "yaw_right",
    "i": "pitch_up",
    "k": "pitch_down",
    "j": "strafe_left",
    "l": "strafe_right",
}


def load_npy(path: Path) -> np.ndarray:
    try:
        return np.load(path, allow_pickle=False)
    except Exception as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc


def parse_action(action: str) -> tuple[int, list[dict[str, object]], list[str]]:
    cleaned = "".join(action.replace("，", ",").split())
    if not cleaned:
        raise ValueError("action string is empty")
    total = 0
    segments: list[dict[str, object]] = []
    warnings: list[str] = []
    saw_updated_keys = False
    for segment in cleaned.split(","):
        if not segment or "-" not in segment:
            raise ValueError(f"invalid action segment {segment!r}: expected '<keys>-<frames>'")
        keys_part, duration_text = segment.rsplit("-", 1)
        if not duration_text.isdigit() or int(duration_text) <= 0:
            raise ValueError(f"segment {segment!r} has non-positive frame duration {duration_text!r}")
        duration = int(duration_text)
        keys_lower = keys_part.lower()
        if keys_lower == "none":
            keys: list[str] = []
        else:
            bad = sorted({c for c in keys_lower if c not in ALLOWED_ACTION_KEYS})
            if bad:
                raise ValueError(
                    f"segment {segment!r} has unknown key(s) {bad}; allowed keys are wasdijkl or none"
                )
            duplicate = sorted({c for c in keys_lower if keys_lower.count(c) > 1})
            if duplicate:
                warnings.append(f"segment {segment!r} repeats {duplicate}; native rollout de-duplicates held keys")
            keys = sorted(set(keys_lower))
            saw_updated_keys = saw_updated_keys or any(k in {"a", "d", "j", "l"} for k in keys)
        controls = [KEY_MAP[k] for k in keys]
        segments.append({"raw": segment, "frames": duration, "keys": keys, "controls": controls})
        total += duration
    if saw_updated_keys:
        warnings.append("updated Sana-WM mapping: a/d yaw; j/l strafe. Swap a/d with j/l for older-release action strings.")
    return total, segments, warnings


def fov_degrees(focal: float, pixels: float) -> float:
    if focal <= 0 or pixels <= 0:
        return float("nan")
    return math.degrees(2.0 * math.atan(pixels / (2.0 * focal)))


def fit_intrinsics_shape(arr: np.ndarray, num_frames: int | None) -> tuple[dict[str, object], list[str]]:
    warnings: list[str] = []
    shape = tuple(int(x) for x in arr.shape)
    result: dict[str, object] = {"shape": shape, "dtype": str(arr.dtype), "accepted": False}
    if arr.shape == (3, 3):
        fx, fy, cx, cy = [float(arr[0, 0]), float(arr[1, 1]), float(arr[0, 2]), float(arr[1, 2])]
        result.update({"accepted": True, "kind": "single-matrix", "frames": "broadcast", "fx": fx, "fy": fy, "cx": cx, "cy": cy})
    elif arr.shape == (4,):
        fx, fy, cx, cy = [float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3])]
        result.update({"accepted": True, "kind": "single-vector", "frames": "broadcast", "fx": fx, "fy": fy, "cx": cx, "cy": cy})
    elif arr.ndim == 3 and arr.shape[1:] == (3, 3):
        fx, fy, cx, cy = [float(np.nanmean(arr[:, 0, 0])), float(np.nanmean(arr[:, 1, 1])), float(np.nanmean(arr[:, 0, 2])), float(np.nanmean(arr[:, 1, 2]))]
        result.update({"accepted": True, "kind": "per-frame-matrix", "frames": int(arr.shape[0]), "fx_mean": fx, "fy_mean": fy, "cx_mean": cx, "cy_mean": cy})
    elif arr.ndim == 2 and arr.shape[1] == 4:
        fx, fy, cx, cy = [float(np.nanmean(arr[:, 0])), float(np.nanmean(arr[:, 1])), float(np.nanmean(arr[:, 2])), float(np.nanmean(arr[:, 3]))]
        result.update({"accepted": True, "kind": "per-frame-vector", "frames": int(arr.shape[0]), "fx_mean": fx, "fy_mean": fy, "cx_mean": cx, "cy_mean": cy})
    else:
        result["error"] = "expected (3,3), (F,3,3), (4,), or (F,4)"
        return result, warnings

    if not np.isfinite(arr).all():
        warnings.append("intrinsics contain NaN or Inf values")
    if num_frames is not None and isinstance(result.get("frames"), int) and result["frames"] != num_frames:
        if result["frames"] > num_frames:
            warnings.append(f"intrinsics has {result['frames']} frames and will be truncated to {num_frames}")
        elif result["frames"] == 1:
            warnings.append(f"single-frame intrinsics will be broadcast to {num_frames}")
        else:
            warnings.append(f"intrinsics has {result['frames']} frames and native loader resamples to {num_frames}")
    width = None
    height = None
    if "cx" in result and "cy" in result:
        width = 2.0 * float(result["cx"])
        height = 2.0 * float(result["cy"])
        fx = float(result["fx"])
        fy = float(result["fy"])
    else:
        width = 2.0 * float(result.get("cx_mean", 0.0))
        height = 2.0 * float(result.get("cy_mean", 0.0))
        fx = float(result.get("fx_mean", 0.0))
        fy = float(result.get("fy_mean", 0.0))
    fov_x = fov_degrees(fx, width)
    fov_y = fov_degrees(fy, height)
    result["approx_fov_x_deg"] = fov_x
    result["approx_fov_y_deg"] = fov_y
    if not np.isfinite([fov_x, fov_y]).all():
        warnings.append("intrinsics focal lengths or principal point are not positive enough to estimate FOV")
    elif not (25.0 <= fov_x <= 120.0 and 25.0 <= fov_y <= 120.0):
        warnings.append(f"approximate FOV outside SANA-WM Pi3X guard range: H={fov_x:.1f}, V={fov_y:.1f} degrees")
    return result, warnings


def validate_camera(arr: np.ndarray, num_frames: int | None) -> tuple[dict[str, object], list[str]]:
    warnings: list[str] = []
    result: dict[str, object] = {
        "shape": tuple(int(x) for x in arr.shape),
        "dtype": str(arr.dtype),
        "accepted": bool(arr.ndim == 3 and arr.shape[1:] == (4, 4)),
    }
    if not result["accepted"]:
        result["error"] = "expected (F,4,4) camera-to-world matrices"
        return result, warnings
    frames = int(arr.shape[0])
    result["frames"] = frames
    if not np.isfinite(arr).all():
        warnings.append("camera poses contain NaN or Inf values")
    bottom = arr[:, 3, :]
    if not np.allclose(bottom, np.array([0, 0, 0, 1], dtype=arr.dtype), atol=1e-3):
        warnings.append("camera pose bottom rows are not all close to [0,0,0,1]")
    rotations = arr[:, :3, :3]
    dets = np.linalg.det(rotations.astype(np.float64))
    result["rotation_det_min"] = float(np.nanmin(dets))
    result["rotation_det_max"] = float(np.nanmax(dets))
    if not np.allclose(dets, 1.0, atol=5e-2):
        warnings.append("some camera rotation determinants are not close to 1; check coordinate convention or file corruption")
    translations = arr[:, :3, 3]
    result["translation_abs_max"] = float(np.nanmax(np.abs(translations)))
    if num_frames is not None and frames != num_frames:
        if frames > num_frames:
            warnings.append(f"camera has {frames} poses; command with num_frames={num_frames} will truncate")
        else:
            warnings.append(f"camera has {frames} poses; command requesting {num_frames} frames will be limited by trajectory length")
    return result, warnings


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--action", help="SANA-WM action DSL, e.g. 'w-80,dw-40,none-24'.")
    parser.add_argument("--camera", type=Path, help="Optional .npy camera-to-world array of shape (F,4,4).")
    parser.add_argument("--intrinsics", type=Path, help="Optional .npy intrinsics: (3,3), (F,3,3), (4,), or (F,4).")
    parser.add_argument("--num-frames", type=int, default=None, help="Expected output frame count used for mismatch warnings.")
    parser.add_argument("--wm-streaming", action="store_true", help="Also check SANA-WM streaming frame snapping rule.")
    parser.add_argument("--refiner-block-size", type=int, default=3, help="Streaming refiner block size for snapping checks.")
    parser.add_argument("--output-format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero on warnings as well as errors.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_args(parser)
    args = parser.parse_args(argv)
    if not args.action and not args.camera and not args.intrinsics:
        parser.error("provide at least one of --action, --camera, or --intrinsics")
    if args.num_frames is not None and args.num_frames < 1:
        parser.error("--num-frames must be positive")
    errors: list[str] = []
    warnings: list[str] = []
    payload: dict[str, object] = {"ok": True, "warnings": warnings, "errors": errors}

    if args.action:
        try:
            duration, segments, action_warnings = parse_action(args.action)
            warnings.extend(action_warnings)
            poses = duration + 1
            payload["action"] = {"duration_frames": duration, "trajectory_poses": poses, "segments": segments}
            if args.num_frames is not None:
                if poses < args.num_frames:
                    warnings.append(f"action rollout has {poses} poses but num_frames={args.num_frames}; generation will be capped by action length")
                elif duration not in {args.num_frames, args.num_frames - 1}:
                    warnings.append(f"action duration {duration} is unusual for num_frames={args.num_frames}; common command uses duration=num_frames-1")
        except ValueError as exc:
            errors.append(str(exc))

    if args.camera:
        if not args.camera.exists():
            errors.append(f"camera file does not exist: {args.camera}")
        else:
            try:
                result, cam_warnings = validate_camera(load_npy(args.camera), args.num_frames)
                payload["camera"] = result
                warnings.extend(cam_warnings)
                if not result.get("accepted"):
                    errors.append(f"invalid camera: {result.get('error')}")
            except ValueError as exc:
                errors.append(str(exc))

    if args.intrinsics:
        if not args.intrinsics.exists():
            errors.append(f"intrinsics file does not exist: {args.intrinsics}")
        else:
            try:
                result, intr_warnings = fit_intrinsics_shape(load_npy(args.intrinsics), args.num_frames)
                payload["intrinsics"] = result
                warnings.extend(intr_warnings)
                if not result.get("accepted"):
                    errors.append(f"invalid intrinsics: {result.get('error')}")
            except ValueError as exc:
                errors.append(str(exc))

    if args.num_frames is not None:
        if (args.num_frames - 1) % 8 != 0:
            nearest = args.num_frames - ((args.num_frames - 1) % 8)
            alt = nearest + 8
            warnings.append(f"SANA-WM bidirectional/chunk-causal LTX-2 VAE prefers num_frames=8*k+1; nearest values: {nearest}, {alt}")
        if args.wm_streaming:
            stride = 8 * args.refiner_block_size
            if (args.num_frames - 1) % stride != 0:
                nearest = args.num_frames - ((args.num_frames - 1) % stride)
                alt = nearest + stride
                warnings.append(f"SANA-WM streaming prefers num_frames={stride}*k+1; nearest values: {nearest}, {alt}")
    payload["ok"] = not errors and (not warnings or not args.strict)

    if args.output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("# Sana-WM camera/control validation")
        print(f"\nStatus: {'OK' if payload['ok'] else 'CHECK'}")
        for key in ("action", "camera", "intrinsics"):
            if key in payload:
                print(f"\n## {key}")
                print("```json")
                print(json.dumps(payload[key], indent=2, sort_keys=True))
                print("```")
        if warnings:
            print("\n## Warnings")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("\n## Errors")
            for error in errors:
                print(f"- {error}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
