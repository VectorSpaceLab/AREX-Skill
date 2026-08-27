#!/usr/bin/env python3
"""Bounded, non-rendering CPU smoke for MyoSuite site-pose IK.

The model is generated in a temporary directory; no repository asset or viewer
is required. The default target is reachable. Use --unreachable to exercise a
bounded non-convergence report or --malformed to exercise target validation.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any

import mujoco
import numpy as np

from myosuite.utils.inverse_kinematics import qpos_from_site_pose


MODEL_XML = """
<mujoco model="ik_smoke">
  <option gravity="0 0 0" />
  <worldbody>
    <body name="base">
      <joint name="shoulder" type="hinge" axis="0 0 1" />
      <geom type="capsule" fromto="0 0 0 1 0 0" size="0.04" />
      <body name="forearm" pos="1 0 0">
        <joint name="elbow" type="hinge" axis="0 0 1" />
        <geom type="capsule" fromto="0 0 0 1 0 0" size="0.04" />
        <site name="end_effector" pos="1 0 0" size="0.05" />
      </body>
    </body>
  </worldbody>
</mujoco>
"""


class _MjLibAdapter:
    """Small adapter for the RoboHive-style calls used by the IK function."""

    @staticmethod
    def mj_fwdPosition(model: mujoco.MjModel, data: mujoco.MjData) -> None:
        mujoco.mj_fwdPosition(model, data)

    @staticmethod
    def mj_jacSite(
        model: mujoco.MjModel,
        data: mujoco.MjData,
        jac_pos: np.ndarray | None,
        jac_rot: np.ndarray | None,
        site_id: int,
    ) -> None:
        mujoco.mj_jacSite(model, data, jac_pos, jac_rot, site_id)

    @staticmethod
    def mj_integratePos(
        model: mujoco.MjModel, qpos: np.ndarray, update: np.ndarray, dt: float
    ) -> None:
        mujoco.mj_integratePos(model, qpos, update, dt)

    @staticmethod
    def mju_mat2Quat(out: np.ndarray, mat: np.ndarray) -> None:
        mujoco.mju_mat2Quat(out, mat)

    @staticmethod
    def mju_negQuat(out: np.ndarray, quat: np.ndarray) -> None:
        mujoco.mju_negQuat(out, quat)

    @staticmethod
    def mju_mulQuat(
        out: np.ndarray, qa: np.ndarray, qb: np.ndarray
    ) -> None:
        mujoco.mju_mulQuat(out, qa, qb)

    @staticmethod
    def mju_quat2Vel(out: np.ndarray, quat: np.ndarray, dt: float) -> None:
        mujoco.mju_quat2Vel(out, quat, dt)


class _ModelHandle:
    """Expose the named lookup expected by the legacy physics contract."""

    def __init__(self, raw: mujoco.MjModel) -> None:
        self.raw = raw

    def __getattr__(self, name: str) -> Any:
        return getattr(self.raw, name)

    def site_name2id(self, site_name: str) -> int:
        site_id = mujoco.mj_name2id(
            self.raw, mujoco.mjtObj.mjOBJ_SITE, site_name
        )
        if site_id < 0:
            raise ValueError(f"unknown site: {site_name}")
        return site_id


@dataclass
class _Physics:
    model: _ModelHandle | mujoco.MjModel
    data: mujoco.MjData

    def __post_init__(self) -> None:
        if isinstance(self.model, mujoco.MjModel):
            self.model = _ModelHandle(self.model)
        self.named = object()  # named joint subsets are not used by this smoke

    def get_handle(self, value: Any) -> Any:
        return value.raw if isinstance(value, _ModelHandle) else value

    def get_mjlib(self) -> _MjLibAdapter:
        return _MjLibAdapter()

    def site_name2id(self, site_name: str) -> int:
        site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, site_name
        )
        if site_id < 0:
            raise ValueError(f"unknown site: {site_name}")
        return site_id

    def get_state(self) -> dict[str, np.ndarray]:
        return {
            "qpos": self.data.qpos.copy(),
            "qvel": self.data.qvel.copy(),
            "act": self.data.act.copy() if self.model.na else np.empty(0),
        }

    def set_state(
        self,
        qpos: np.ndarray,
        qvel: np.ndarray,
        act: np.ndarray | None = None,
    ) -> None:
        self.data.qpos[:] = qpos
        self.data.qvel[:] = qvel
        if act is not None and self.model.na:
            self.data.act[:] = act

    def forward(self) -> None:
        mujoco.mj_forward(self.model.raw, self.data)


def _validate_target(target_pos: Any) -> np.ndarray:
    target = np.asarray(target_pos, dtype=float)
    if target.shape != (3,) or not np.all(np.isfinite(target)):
        raise ValueError("target_pos must be finite and have shape (3,)")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-steps", type=int, default=100, help="hard IK iteration bound"
    )
    parser.add_argument(
        "--unreachable",
        action="store_true",
        help="use a target outside the generated arm's workspace",
    )
    parser.add_argument(
        "--malformed",
        action="store_true",
        help="pass a malformed target and report validation failure",
    )
    args = parser.parse_args()
    if args.max_steps < 1:
        parser.error("--max-steps must be positive")

    with tempfile.TemporaryDirectory(prefix="myosuite-ik-smoke-") as temp_dir:
        xml_path = os.path.join(temp_dir, "model.xml")
        with open(xml_path, "w", encoding="utf-8") as stream:
            stream.write(MODEL_XML)
        model = mujoco.MjModel.from_xml_path(xml_path)
        data = mujoco.MjData(model)
        physics = _Physics(model, data)

        if args.malformed:
            try:
                _validate_target([0.0, 0.0])
            except ValueError as exc:
                print(json.dumps({"validation": "rejected", "error": str(exc)}))
                return 0
            print(json.dumps({"validation": "unexpectedly accepted"}))
            return 1

        # Generate a known reachable target, then restore the zero initial state.
        data.qpos[:] = np.array([0.25, -0.35])
        physics.forward()
        target = data.site_xpos[physics.site_name2id("end_effector")].copy()
        if args.unreachable:
            target = np.array([10.0, 10.0, 10.0])
        data.qpos[:] = 0.0
        physics.forward()

        result = qpos_from_site_pose(
            physics,
            "end_effector",
            target_pos=_validate_target(target),
            max_steps=args.max_steps,
            inplace=False,
        )
        payload = {
            "success": bool(result.success),
            "err_norm": float(result.err_norm),
            "steps": int(result.steps),
            "qpos_shape": list(np.asarray(result.qpos).shape),
            "mode": "unreachable" if args.unreachable else "reachable",
        }
        print(json.dumps(payload, sort_keys=True))

        if args.unreachable:
            return 0 if not result.success else 1
        return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
