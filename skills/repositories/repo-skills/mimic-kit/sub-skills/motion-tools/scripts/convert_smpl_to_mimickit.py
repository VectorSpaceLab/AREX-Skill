#!/usr/bin/env python3
"""Convert SMPL/AMASS npz motion data to MimicKit's SMPL humanoid schema.

This generated-skill helper preserves the source converter's SMPL constants,
joint-name reorder, parent structure, and z-correction modes while avoiding any
implicit dependency on the current working directory. Pass ``--repo-root`` only
when a target MimicKit checkout should be imported explicitly for saving.
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

SMPL_BONE_ORDER_NAMES = [
    "Pelvis", "L_Hip", "R_Hip", "Torso", "L_Knee", "R_Knee", "Spine", "L_Ankle",
    "R_Ankle", "Chest", "L_Toe", "R_Toe", "Neck", "L_Thorax", "R_Thorax", "Head",
    "L_Shoulder", "R_Shoulder", "L_Elbow", "R_Elbow", "L_Wrist", "R_Wrist", "L_Hand", "R_Hand",
]

SMPL_MUJOCO_NAMES = [
    "Pelvis", "L_Hip", "L_Knee", "L_Ankle", "L_Toe", "R_Hip", "R_Knee", "R_Ankle",
    "R_Toe", "Torso", "Spine", "Chest", "Neck", "Head", "L_Thorax", "L_Shoulder",
    "L_Elbow", "L_Wrist", "L_Hand", "R_Thorax", "R_Shoulder", "R_Elbow", "R_Wrist", "R_Hand",
]

PARENT_INDICES = [-1, 0, 1, 2, 3, 0, 5, 6, 7, 0, 9, 10, 11, 12, 11, 14, 15, 16, 17, 11, 19, 20, 21, 22]

LOCAL_TRANSLATION = np.array([
    [0.0000, 0.0000, 0.0000],
    [-0.0068, 0.0695, -0.0914],
    [-0.0045, 0.0343, -0.3752],
    [-0.0437, -0.0136, -0.3980],
    [0.1193, 0.0124, -0.0258],
    [-0.0043, -0.0677, -0.0905],
    [-0.0089, -0.0383, -0.3826],
    [-0.0423, 0.0158, -0.3984],
    [0.1193, -0.0124, -0.0258],
    [-0.0267, -0.0025, 0.1090],
    [0.0011, 0.0055, 0.1352],
    [0.0254, 0.0015, 0.0529],
    [-0.0429, -0.0028, 0.2139],
    [0.0513, 0.0052, 0.0650],
    [-0.0341, 0.0788, 0.1217],
    [-0.0089, 0.0910, 0.0305],
    [-0.0275, 0.2596, -0.0128],
    [-0.0012, 0.2492, 0.0090],
    [-0.0149, 0.0840, -0.0082],
    [-0.0386, -0.0818, 0.1188],
    [-0.0091, -0.0960, 0.0326],
    [-0.0214, -0.2537, -0.0133],
    [-0.0056, -0.2553, 0.0078],
    [-0.0103, -0.0846, -0.0061],
], dtype=np.float32)

ZUP_TO_YUP = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
YUP_TO_ZUP = np.array([-0.5, -0.5, -0.5, 0.5], dtype=np.float32)


@dataclass
class LocalMotion:
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
        raise ValueError("encountered a zero-length quaternion")
    return q / norms


def quat_conjugate(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    out = q.copy()
    out[..., :3] *= -1.0
    return out


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"quat_mul expects equal shapes, got {a.shape} and {b.shape}")
    x1, y1, z1, w1 = np.moveaxis(a, -1, 0)
    x2, y2, z2, w2 = np.moveaxis(b, -1, 0)
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    return np.stack([x, y, z, w], axis=-1)


def quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    q = _normalize_quat_xyzw(q)
    v = np.asarray(v, dtype=np.float64)
    q_v = q[..., :3]
    q_w = q[..., 3:4]
    t = 2.0 * np.cross(q_v, v)
    return v + q_w * t + np.cross(q_v, t)


def normalize_angle(angle: np.ndarray) -> np.ndarray:
    return np.arctan2(np.sin(angle), np.cos(angle))


def exp_map_to_quat(exp_map: np.ndarray) -> np.ndarray:
    exp_map = np.asarray(exp_map, dtype=np.float64)
    angle = np.linalg.norm(exp_map, axis=-1)
    axis = np.zeros_like(exp_map)
    mask = np.abs(angle) > 1e-5
    axis[mask] = exp_map[mask] / angle[mask, None]
    axis[~mask, 2] = 1.0
    angle = np.where(mask, normalize_angle(angle), 0.0)
    half = 0.5 * angle
    quat = np.concatenate([axis * np.sin(half)[..., None], np.cos(half)[..., None]], axis=-1)
    return _normalize_quat_xyzw(quat)


def quat_to_exp_map(q: np.ndarray) -> np.ndarray:
    q = _normalize_quat_xyzw(q)
    q = np.where(q[..., 3:4] < 0.0, -q, q)
    vec = q[..., :3]
    w = q[..., 3]
    length = np.linalg.norm(vec, axis=-1)
    angle = 2.0 * np.arctan2(length, w)
    axis = np.zeros_like(vec)
    mask = length > 1e-5
    axis[mask] = vec[mask] / length[mask, None]
    axis[~mask, 2] = 1.0
    return axis * angle[..., None]


def compute_global_rotations(local_quats: np.ndarray, parents: list[int]) -> np.ndarray:
    num_frames, num_joints, _ = local_quats.shape
    globals_per_joint: list[np.ndarray | None] = [None] * num_joints
    for joint_id, parent_idx in enumerate(parents):
        if parent_idx == -1:
            globals_per_joint[joint_id] = local_quats[:, joint_id, :]
        else:
            parent = globals_per_joint[parent_idx]
            if parent is None:
                raise ValueError("parent indices must be topologically sorted")
            globals_per_joint[joint_id] = quat_mul(parent, local_quats[:, joint_id, :])
    return np.stack([g for g in globals_per_joint if g is not None], axis=1).reshape(num_frames, num_joints, 4)


def compute_local_rotations(global_quats: np.ndarray, parents: list[int]) -> np.ndarray:
    num_frames, num_joints, _ = global_quats.shape
    locals_per_joint: list[np.ndarray | None] = [None] * num_joints
    for joint_id, parent_idx in enumerate(parents):
        if parent_idx == -1:
            locals_per_joint[joint_id] = global_quats[:, joint_id, :]
        else:
            parent_q = global_quats[:, parent_idx, :]
            child_q = global_quats[:, joint_id, :]
            locals_per_joint[joint_id] = quat_mul(quat_conjugate(parent_q), child_q)
    return np.stack([g for g in locals_per_joint if g is not None], axis=1).reshape(num_frames, num_joints, 4)


def compute_global_translations(global_rotations: np.ndarray, local_offsets: np.ndarray, parents: list[int]) -> np.ndarray:
    num_frames, num_joints, _ = global_rotations.shape
    out = np.zeros((num_frames, num_joints, 3), dtype=np.float64)
    for joint_id, parent_idx in enumerate(parents):
        if parent_idx == -1:
            out[:, joint_id, :] = local_offsets[joint_id]
        else:
            parent_pos = out[:, parent_idx, :]
            parent_rot = global_rotations[:, parent_idx, :]
            offset = np.broadcast_to(local_offsets[joint_id], (num_frames, 3))
            out[:, joint_id, :] = parent_pos + quat_rotate(parent_rot, offset)
    return out


def load_smpl_motion(input_file: str | Path) -> tuple[np.ndarray, np.ndarray, int]:
    path = Path(input_file)
    if path.suffix != ".npz":
        raise ValueError("Unsupported SMPL input format; provide an AMASS-style .npz file")
    with np.load(path, allow_pickle=True) as data:
        if "poses" not in data or "trans" not in data:
            raise KeyError("SMPL/AMASS npz must contain 'poses' and 'trans'")
        poses = np.asarray(data["poses"], dtype=np.float32)
        trans = np.asarray(data["trans"], dtype=np.float32)
        if "mocap_framerate" in data:
            fps = data["mocap_framerate"]
        elif "fps" in data:
            fps = data["fps"]
        else:
            fps = 30
    fps_int = int(_clean_scalar(fps))
    if fps_int <= 0:
        raise ValueError(f"fps must be positive, got {fps_int}")
    if poses.ndim != 2 or poses.shape[1] < 66:
        raise ValueError(f"poses must have shape (num_frames, >=66), got {poses.shape}")
    if trans.ndim != 2 or trans.shape[1] != 3:
        raise ValueError(f"trans must have shape (num_frames, 3), got {trans.shape}")
    if poses.shape[0] != trans.shape[0]:
        raise ValueError(f"poses and trans frame counts differ: {poses.shape[0]} vs {trans.shape[0]}")
    if not np.all(np.isfinite(poses)) or not np.all(np.isfinite(trans)):
        raise ValueError("poses/trans contain non-finite values")
    return poses, trans.copy(), fps_int


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


def convert_smpl_to_mimickit(
    input_file: str | Path,
    output_file: str | Path,
    loop: str,
    start_frame: int,
    end_frame: int,
    output_fps: int,
    z_correction: str,
    repo_root: str | None = None,
) -> np.ndarray:
    poses, trans, fps = load_smpl_motion(input_file)
    num_frames = poses.shape[0]
    save_fps = fps if output_fps == -1 else output_fps
    if int(save_fps) <= 0:
        raise ValueError(f"output fps must be positive or -1, got {output_fps}")

    root_rot_quat = exp_map_to_quat(poses[:, 0:3])
    pose_aa = np.concatenate([poses[:, :66], np.zeros((num_frames, 6), dtype=np.float32)], axis=-1)
    smpl_to_mujoco = [SMPL_BONE_ORDER_NAMES.index(name) for name in SMPL_MUJOCO_NAMES]
    pose_aa_mj = pose_aa.reshape(num_frames, 24, 3)[:, smpl_to_mujoco]
    pose_quat = exp_map_to_quat(pose_aa_mj.reshape(-1, 3)).reshape(num_frames, 24, 4)

    global_rot = compute_global_rotations(pose_quat, PARENT_INDICES)
    y_to_z = np.broadcast_to(YUP_TO_ZUP, global_rot.reshape(-1, 4).shape)
    rotated_global_rot = quat_mul(global_rot.reshape(-1, 4), y_to_z).reshape(num_frames, 24, 4)
    rotated_local_rot = compute_local_rotations(rotated_global_rot, PARENT_INDICES)

    global_translation = compute_global_translations(rotated_global_rot, LOCAL_TRANSLATION, PARENT_INDICES)
    global_translation += trans[:, None, :]

    dof_pos = quat_to_exp_map(rotated_local_rot[:, 1:, :]).reshape(num_frames, -1)

    root_y_to_z = np.broadcast_to(YUP_TO_ZUP, root_rot_quat.shape)
    root_rot = quat_to_exp_map(quat_mul(root_rot_quat, root_y_to_z))

    if z_correction == "full":
        min_height = np.min(global_translation[:, :, 2])
        trans[:, 2] -= min_height - 0.025
    elif z_correction == "calibrate":
        sample_count = min(30, num_frames)
        min_height = np.min(global_translation[:sample_count, :, 2])
        trans[:, 2] -= min_height - 0.025
    elif z_correction != "none":
        raise ValueError(f"unsupported z_correction: {z_correction}")

    frames = np.concatenate([trans, root_rot, dof_pos], axis=1).astype(np.float32)
    start_frame, end_frame = _resolve_frame_range(start_frame, end_frame, frames.shape[0])
    frames = frames[start_frame:end_frame]

    _save_motion(output_file, loop=loop, fps=save_fps, frames=frames, repo_root=repo_root)

    print("SMPL/AMASS to MimicKit conversion complete")
    print(f"  input: {input_file}")
    print(f"  output: {output_file}")
    print(f"  frames shape: {frames.shape}")
    print(f"  fps: {_clean_scalar(save_fps)}")
    print(f"  loop_mode: {loop} ({LOOP_MODE_VALUES[loop]})")
    print(f"  z_correction: {z_correction}")
    print("  joint_dofs: 69")
    return frames


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert SMPL/AMASS npz data to MimicKit SMPL humanoid Motion pickle format.")
    parser.add_argument("--input_file", required=True, help="Path to the input AMASS-style SMPL .npz file")
    parser.add_argument("--output_file", required=True, help="Path for the output MimicKit motion pickle")
    parser.add_argument("--loop", default="wrap", choices=sorted(LOOP_MODE_VALUES), help="Motion loop mode to write")
    parser.add_argument("--start_frame", type=int, default=0, help="Inclusive start frame for clipping")
    parser.add_argument("--end_frame", type=int, default=-1, help="Exclusive end frame for clipping; -1 uses all remaining frames")
    parser.add_argument("--output_fps", type=int, default=-1, help="Output FPS; -1 keeps source fps")
    parser.add_argument("--z_correction", default="calibrate", choices=["none", "calibrate", "full"], help="Root-height correction strategy")
    parser.add_argument("--repo-root", default=None, help="Optional target MimicKit checkout root used only for explicit imports")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    convert_smpl_to_mimickit(
        input_file=args.input_file,
        output_file=args.output_file,
        loop=args.loop,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        output_fps=args.output_fps,
        z_correction=args.z_correction,
        repo_root=args.repo_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
