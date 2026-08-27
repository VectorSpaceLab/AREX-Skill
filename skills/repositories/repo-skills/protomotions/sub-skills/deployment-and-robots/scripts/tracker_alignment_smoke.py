#!/usr/bin/env python3
"""Pure NumPy smoke for tracker reference-position alignment semantics."""

from __future__ import annotations

import numpy as np


def yaw_quat(deg: float) -> np.ndarray:
    half = np.deg2rad(deg) / 2.0
    return np.array([0.0, 0.0, np.sin(half), np.cos(half)], dtype=np.float32)


def quat_conjugate(q: np.ndarray) -> np.ndarray:
    out = q.copy()
    out[:3] *= -1
    return out


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ], dtype=np.float32)


def quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    q_w = q[..., 3:4]
    q_vec = q[..., :3]
    return (v * (2.0 * q_w**2 - 1.0) + np.cross(q_vec, v) * q_w * 2.0 + q_vec * np.sum(q_vec * v, axis=-1, keepdims=True) * 2.0).astype(np.float32)


def compute_heading_offset(robot_anchor_rot: np.ndarray, motion_anchor_rot: np.ndarray) -> np.ndarray:
    # The deployment path uses a yaw-only offset. For this smoke, inputs are yaw-only.
    return quat_mul(robot_anchor_rot, quat_conjugate(motion_anchor_rot))


def main() -> int:
    motion_start = np.array([-9.0, -18.0, 0.75], dtype=np.float32)
    robot_start = np.array([0.0, 0.0, 0.75], dtype=np.float32)
    heading_offset = compute_heading_offset(yaw_quat(40.0), yaw_quat(-25.0))
    current_anchor = motion_start + np.array([1.0, 0.0, 0.0], dtype=np.float32)
    future = np.stack([current_anchor + np.array([0.25 * (k + 1), 0.0, 0.0], dtype=np.float32) for k in range(4)])
    aligned_current = robot_start + quat_rotate(heading_offset, current_anchor - motion_start)
    aligned_future = robot_start + quat_rotate(heading_offset, future - motion_start)
    travel = aligned_future[:, :2] - aligned_current[:2]
    expected_last = quat_rotate(heading_offset, np.array([1.0, 0.0, 0.0], dtype=np.float32))[:2]
    if not np.allclose(travel[-1], expected_last, atol=1e-5):
        raise SystemExit(f"alignment smoke failed: {travel[-1]} != {expected_last}")
    print("alignment smoke passed")
    print("last_step_travel_xy", travel[-1].tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
