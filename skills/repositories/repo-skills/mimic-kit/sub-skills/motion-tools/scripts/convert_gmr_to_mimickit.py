#!/usr/bin/env python3
"""Convert GMR-style motion pickles to the MimicKit Motion pickle schema.

This helper is adapted for generated-skill use: it does not assume the current
working directory is a MimicKit checkout. If you want it to use a target
checkout's Motion class for saving, pass that checkout explicitly with
``--repo-root``. Without ``--repo-root`` it writes the same schema directly.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

LOOP_MODE_VALUES = {"clamp": 0, "wrap": 1}


@dataclass
class LocalMotion:
    """Minimal schema-compatible Motion writer used when MimicKit is absent."""

    loop_mode: int
    fps: float | int
    frames: np.ndarray

    def save(self, out_file: str | Path) -> None:
        out_dict = {
            "loop_mode": int(self.loop_mode),
            "fps": _clean_scalar(self.fps),
            "frames": np.asarray(self.frames, dtype=np.float32).tolist(),
        }
        with Path(out_file).open("wb") as stream:
            pickle.dump(out_dict, stream)


def _clean_scalar(value: Any) -> float | int:
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)) and float(value).is_integer():
        return int(value)
    return float(value)


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"--repo-root is not a directory: {repo_root}")
    for candidate in (root, root / "mimickit"):
        text = str(candidate)
        if candidate.exists() and text not in sys.path:
            sys.path.insert(0, text)


def _try_target_motion_api(repo_root: str | None):
    if not repo_root:
        return None
    _add_repo_root(repo_root)
    try:
        from mimickit.anim.motion import LoopMode, Motion  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller checkout
        print(f"warning: could not import target MimicKit Motion API ({exc}); writing local schema", file=sys.stderr)
        return None
    return Motion, LoopMode


def _normalize_quat_xyzw(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    norms = np.linalg.norm(q, axis=-1, keepdims=True)
    if np.any(norms <= 1e-12):
        raise ValueError("root_rot contains a zero-length quaternion")
    return q / norms


def quat_to_exp_map_xyzw(q: np.ndarray) -> np.ndarray:
    """Match MimicKit's quaternion-to-exp-map convention for xyzw quaternions."""
    q = _normalize_quat_xyzw(q)
    q = np.where(q[..., 3:4] < 0.0, -q, q)
    vec = q[..., :3]
    w = q[..., 3]
    length = np.linalg.norm(vec, axis=-1)
    angle = 2.0 * np.arctan2(length, w)

    axis = np.zeros_like(vec)
    mask = length > 1e-8
    axis[mask] = vec[mask] / length[mask, None]
    axis[~mask, 2] = 1.0
    return (axis * angle[..., None]).astype(np.float32)


def _require_array(data: dict[str, Any], key: str, shape_tail: tuple[int, ...] | None = None) -> np.ndarray:
    if key not in data:
        raise KeyError(f"input GMR pickle is missing required key {key!r}")
    arr = np.asarray(data[key], dtype=np.float32)
    if shape_tail is not None and (arr.ndim < len(shape_tail) or arr.shape[-len(shape_tail):] != shape_tail):
        raise ValueError(f"expected {key} shape ending in {shape_tail}, got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{key} contains non-finite values")
    return arr


def _resolve_frame_range(start_frame: int, end_frame: int, num_frames: int) -> tuple[int, int]:
    if end_frame == -1:
        end_frame = num_frames
    if not (0 <= start_frame < end_frame <= num_frames):
        raise ValueError(f"Invalid frame range [{start_frame}, {end_frame}] for {num_frames} frames")
    return start_frame, end_frame


def _save_motion(output_file: str | Path, loop: str, fps: float | int, frames: np.ndarray, repo_root: str | None) -> None:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True) if output_path.parent != Path("") else None
    loop_value = LOOP_MODE_VALUES[loop]
    api = _try_target_motion_api(repo_root)
    if api is None:
        LocalMotion(loop_mode=loop_value, fps=fps, frames=frames).save(output_path)
    else:
        Motion, LoopMode = api
        Motion(loop_mode=LoopMode(loop_value), fps=_clean_scalar(fps), frames=np.asarray(frames, dtype=np.float32)).save(str(output_path))


def convert_gmr_to_mimickit(
    input_file: str | Path,
    output_file: str | Path,
    loop: str,
    start_frame: int,
    end_frame: int,
    output_fps: int,
    repo_root: str | None = None,
) -> np.ndarray:
    with Path(input_file).open("rb") as stream:
        data = pickle.load(stream)
    if not isinstance(data, dict):
        raise TypeError("input GMR pickle must contain a dictionary")
    if "fps" not in data:
        raise KeyError("input GMR pickle is missing required key 'fps'")

    fps = _clean_scalar(data["fps"])
    if float(fps) <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    save_fps = fps if output_fps == -1 else output_fps
    if float(save_fps) <= 0:
        raise ValueError(f"output fps must be positive or -1, got {output_fps}")

    root_pos = _require_array(data, "root_pos", (3,))
    root_rot_quat = _require_array(data, "root_rot", (4,))
    dof_pos = _require_array(data, "dof_pos", None)

    if root_pos.ndim != 2:
        raise ValueError(f"expected root_pos to be 2D, got shape {root_pos.shape}")
    if root_rot_quat.ndim != 2:
        raise ValueError(f"expected root_rot to be 2D, got shape {root_rot_quat.shape}")
    if dof_pos.ndim != 2:
        raise ValueError(f"expected dof_pos to be 2D, got shape {dof_pos.shape}")
    if not (root_pos.shape[0] == root_rot_quat.shape[0] == dof_pos.shape[0]):
        raise ValueError(
            "root_pos, root_rot, and dof_pos must have the same frame count; "
            f"got {root_pos.shape[0]}, {root_rot_quat.shape[0]}, {dof_pos.shape[0]}"
        )

    root_rot = quat_to_exp_map_xyzw(root_rot_quat)
    frames = np.concatenate([root_pos, root_rot, dof_pos], axis=1).astype(np.float32)
    start_frame, end_frame = _resolve_frame_range(start_frame, end_frame, frames.shape[0])
    frames = frames[start_frame:end_frame]

    _save_motion(output_file, loop=loop, fps=save_fps, frames=frames, repo_root=repo_root)

    print("GMR to MimicKit conversion complete")
    print(f"  input: {input_file}")
    print(f"  output: {output_file}")
    print(f"  frames shape: {frames.shape}")
    print(f"  fps: {_clean_scalar(save_fps)}")
    print(f"  loop_mode: {loop} ({LOOP_MODE_VALUES[loop]})")
    return frames


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert GMR motion data to MimicKit Motion pickle format.")
    parser.add_argument("--input_file", required=True, help="Path to the input GMR pickle file")
    parser.add_argument("--output_file", required=True, help="Path for the output MimicKit motion pickle")
    parser.add_argument("--loop", default="wrap", choices=sorted(LOOP_MODE_VALUES), help="Motion loop mode to write")
    parser.add_argument("--start_frame", type=int, default=0, help="Inclusive start frame for clipping")
    parser.add_argument("--end_frame", type=int, default=-1, help="Exclusive end frame for clipping; -1 uses all remaining frames")
    parser.add_argument("--output_fps", type=int, default=-1, help="Output FPS; -1 keeps source fps")
    parser.add_argument("--repo-root", default=None, help="Optional target MimicKit checkout root used only for explicit imports")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    convert_gmr_to_mimickit(
        input_file=args.input_file,
        output_file=args.output_file,
        loop=args.loop,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        output_fps=args.output_fps,
        repo_root=args.repo_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
