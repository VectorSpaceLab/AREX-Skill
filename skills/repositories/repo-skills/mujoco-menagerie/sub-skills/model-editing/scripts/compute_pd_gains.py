#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mujoco", "numpy"]
# ///
"""Compute Menagerie-style PD gains for joint-backed position actuators.

This is a read-only helper distilled from the Menagerie Rizon gain workflow and
parameterized for arbitrary MJCF XML files. It computes effective inertia from
the diagonal of the dense joint-space mass matrix at qpos0 or a named keyframe,
then prints candidate MuJoCo position-actuator kp/kv values.

Default mode derives one natural frequency per force-limit class so that the
largest effective inertia in that class reaches its force limit at a target
saturation coordinate error:

    kp = M_ii * w_n**2
    kv = 2 * damping_ratio * M_ii * w_n
    w_n = sqrt(force_limit / (max_class_M_ii * saturation_error))

Use --frequency-hz to bypass force-limit/saturation derivation and apply one
explicit natural frequency to every selected actuator.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class GainRecord:
  actuator: str
  joint: str
  joint_type: str
  dof: int
  inertia: float
  force_limit: float | None
  force_limit_source: str | None
  frequency_hz: float
  kp: float
  kv: float


@dataclass
class SkippedActuator:
  actuator: str
  reason: str


def _load_deps():
  try:
    import mujoco  # type: ignore
    import numpy as np  # type: ignore
  except ImportError as exc:  # pragma: no cover - exercised in dependency-free envs.
    raise RuntimeError(
      "compute_pd_gains.py requires the 'mujoco' and 'numpy' Python packages. "
      "Install them in the active environment or run this script with uv."
    ) from exc
  return mujoco, np


def _object_name(mujoco: Any, model: Any, obj: Any, idx: int, fallback: str) -> str:
  if idx < 0:
    return fallback
  name = mujoco.mj_id2name(model, obj, idx)
  return name if name else fallback


def _joint_type_name(mujoco: Any, joint_type: int) -> str:
  mapping = {
    int(mujoco.mjtJoint.mjJNT_FREE): "free",
    int(mujoco.mjtJoint.mjJNT_BALL): "ball",
    int(mujoco.mjtJoint.mjJNT_SLIDE): "slide",
    int(mujoco.mjtJoint.mjJNT_HINGE): "hinge",
  }
  return mapping.get(int(joint_type), f"unknown:{int(joint_type)}")


def _single_dof_joint(mujoco: Any, joint_type: int) -> bool:
  return int(joint_type) in {
    int(mujoco.mjtJoint.mjJNT_HINGE),
    int(mujoco.mjtJoint.mjJNT_SLIDE),
  }


def _range_magnitude(values: Any, eps: float = 1e-12) -> float | None:
  lo = float(values[0])
  hi = float(values[1])
  mag = max(abs(lo), abs(hi))
  if not math.isfinite(mag) or mag <= eps or abs(hi - lo) <= eps:
    return None
  return mag


def _resolve_force_limit(
  model: Any,
  actuator_id: int,
  joint_id: int,
  source: str,
) -> tuple[float | None, str | None]:
  candidates: list[tuple[str, Any]] = []
  if source in ("auto", "actuator"):
    candidates.append(("actuator.forcerange", model.actuator_forcerange[actuator_id]))
  if source in ("auto", "joint"):
    candidates.append(("joint.actuatorfrcrange", model.jnt_actfrcrange[joint_id]))

  for label, values in candidates:
    mag = _range_magnitude(values)
    if mag is not None:
      return mag, label
  return None, None


def _compile_regex(pattern: str | None, label: str) -> re.Pattern[str] | None:
  if not pattern:
    return None
  try:
    return re.compile(pattern)
  except re.error as exc:
    raise ValueError(f"invalid {label} regex {pattern!r}: {exc}") from exc


def _selected_by_regex(name: str, pattern: re.Pattern[str] | None) -> bool:
  return pattern is None or pattern.search(name) is not None


def _set_keyframe_qpos(mujoco: Any, model: Any, data: Any, keyframe: str | None) -> str:
  if not keyframe:
    return "qpos0"
  key_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, keyframe)
  if key_id < 0:
    raise ValueError(f"keyframe {keyframe!r} not found in XML")
  data.qpos[:] = model.key_qpos[key_id]
  return f"keyframe:{keyframe}"


def _round_frequency(f_hz: float, step: float) -> float:
  if step <= 0:
    return f_hz
  rounded = round(f_hz / step) * step
  return max(rounded, step)


def _dense_mass_matrix(mujoco: Any, np: Any, model: Any, data: Any) -> Any:
  """Return the dense joint-space mass matrix across MuJoCo Python APIs."""
  mass = np.zeros((model.nv, model.nv))
  try:
    # MuJoCo 3.11+ Python API: mj_fullM(model, data, dst).
    mujoco.mj_fullM(model, data, mass)
  except TypeError:
    # Older API used the packed/sparse mass buffer as the third argument.
    packed = getattr(data, "qM", None)
    if packed is None:
      packed = getattr(data, "M", None)
    if packed is None:
      raise RuntimeError("MuJoCo data object exposes neither qM nor M mass buffer")
    mujoco.mj_fullM(model, mass, packed)
  return mass


def compute_gains(
  xml_path: Path,
  *,
  keyframe: str | None = None,
  saturation: float | None = None,
  saturation_angle_deg: float = 10.0,
  damping_ratio: float = 1.0,
  round_frequency_hz: float = 0.5,
  frequency_hz: float | None = None,
  force_limit_source: str = "auto",
  joint_regex: str | None = None,
  actuator_regex: str | None = None,
) -> tuple[list[GainRecord], dict[str, Any]]:
  """Return candidate PD gains and metadata for ``xml_path``.

  Raises:
    ValueError: If inputs are invalid or no suitable actuators are found.
    RuntimeError: If required Python packages are unavailable.
  """

  if not xml_path.exists():
    raise ValueError(f"XML path does not exist: {xml_path}")
  if damping_ratio <= 0:
    raise ValueError("--damping-ratio must be positive")
  if frequency_hz is not None and frequency_hz <= 0:
    raise ValueError("--frequency-hz must be positive when supplied")
  if round_frequency_hz < 0:
    raise ValueError("--round-frequency-hz must be non-negative")

  if saturation is None:
    if saturation_angle_deg <= 0:
      raise ValueError("--saturation-angle-deg must be positive")
    saturation_error = math.radians(saturation_angle_deg)
    saturation_label = f"{saturation_angle_deg:g} deg ({saturation_error:.8g} rad)"
  else:
    if saturation <= 0:
      raise ValueError("--saturation must be positive")
    saturation_error = float(saturation)
    saturation_label = f"{saturation_error:g} model-coordinate units"

  joint_pattern = _compile_regex(joint_regex, "joint")
  actuator_pattern = _compile_regex(actuator_regex, "actuator")

  mujoco, np = _load_deps()
  model = mujoco.MjModel.from_xml_path(str(xml_path))
  data = mujoco.MjData(model)
  pose_source = _set_keyframe_qpos(mujoco, model, data, keyframe)
  mujoco.mj_forward(model, data)

  mass = _dense_mass_matrix(mujoco, np, model, data)
  inertia_diag = np.diag(mass)

  eligible: list[dict[str, Any]] = []
  skipped: list[SkippedActuator] = []

  joint_trn_types = {
    int(mujoco.mjtTrn.mjTRN_JOINT),
    int(mujoco.mjtTrn.mjTRN_JOINTINPARENT),
  }

  saw_slide_without_explicit_saturation = False

  for actuator_id in range(model.nu):
    actuator_name = _object_name(
      mujoco,
      model,
      mujoco.mjtObj.mjOBJ_ACTUATOR,
      actuator_id,
      f"actuator_{actuator_id}",
    )
    if not _selected_by_regex(actuator_name, actuator_pattern):
      continue

    trn_type = int(model.actuator_trntype[actuator_id])
    if trn_type not in joint_trn_types:
      skipped.append(SkippedActuator(actuator_name, "actuator is not joint-backed"))
      continue

    joint_id = int(model.actuator_trnid[actuator_id, 0])
    if joint_id < 0:
      skipped.append(SkippedActuator(actuator_name, "actuator has no joint id"))
      continue

    joint_name = _object_name(
      mujoco,
      model,
      mujoco.mjtObj.mjOBJ_JOINT,
      joint_id,
      f"joint_{joint_id}",
    )
    if not _selected_by_regex(joint_name, joint_pattern):
      continue

    joint_type = int(model.jnt_type[joint_id])
    joint_type_name = _joint_type_name(mujoco, joint_type)
    if not _single_dof_joint(mujoco, joint_type):
      skipped.append(
        SkippedActuator(
          actuator_name,
          f"joint {joint_name!r} is {joint_type_name}, not a single-DoF hinge/slide",
        )
      )
      continue

    if joint_type_name == "slide" and saturation is None:
      saw_slide_without_explicit_saturation = True

    dof = int(model.jnt_dofadr[joint_id])
    inertia = float(inertia_diag[dof])
    if inertia <= 0 or not math.isfinite(inertia):
      skipped.append(SkippedActuator(actuator_name, f"joint {joint_name!r} has nonpositive inertia"))
      continue

    force_limit, force_source = _resolve_force_limit(
      model,
      actuator_id,
      joint_id,
      force_limit_source,
    )

    eligible.append(
      {
        "actuator": actuator_name,
        "joint": joint_name,
        "joint_type": joint_type_name,
        "dof": dof,
        "inertia": inertia,
        "force_limit": force_limit,
        "force_limit_source": force_source,
      }
    )

  if not eligible:
    skipped_text = "; ".join(f"{s.actuator}: {s.reason}" for s in skipped[:8])
    suffix = f" Skipped examples: {skipped_text}" if skipped_text else ""
    raise ValueError(f"no eligible joint-backed single-DoF actuators found.{suffix}")

  if frequency_hz is None:
    missing = [r for r in eligible if r["force_limit"] is None]
    if missing:
      names = ", ".join(r["actuator"] for r in missing[:8])
      raise ValueError(
        "missing force limit for actuator(s): "
        f"{names}. Add actuator/joint force limits, choose --force-limit-source, "
        "or pass --frequency-hz."
      )

    groups: dict[float, list[dict[str, Any]]] = {}
    for row in eligible:
      key = round(float(row["force_limit"]), 12)
      groups.setdefault(key, []).append(row)

    frequency_by_force_limit: dict[float, float] = {}
    for key, rows in groups.items():
      max_inertia = max(float(r["inertia"]) for r in rows)
      raw_f_hz = math.sqrt(key / (max_inertia * saturation_error)) / (2.0 * math.pi)
      frequency_by_force_limit[key] = _round_frequency(raw_f_hz, round_frequency_hz)

    for row in eligible:
      row["frequency_hz"] = frequency_by_force_limit[round(float(row["force_limit"]), 12)]
  else:
    for row in eligible:
      row["frequency_hz"] = float(frequency_hz)

  records: list[GainRecord] = []
  for row in eligible:
    w_n = 2.0 * math.pi * float(row["frequency_hz"])
    inertia = float(row["inertia"])
    records.append(
      GainRecord(
        actuator=str(row["actuator"]),
        joint=str(row["joint"]),
        joint_type=str(row["joint_type"]),
        dof=int(row["dof"]),
        inertia=inertia,
        force_limit=None if row["force_limit"] is None else float(row["force_limit"]),
        force_limit_source=row["force_limit_source"],
        frequency_hz=float(row["frequency_hz"]),
        kp=inertia * w_n**2,
        kv=2.0 * damping_ratio * inertia * w_n,
      )
    )

  meta = {
    "xml_path": str(xml_path),
    "nq": int(model.nq),
    "nv": int(model.nv),
    "nu": int(model.nu),
    "pose_source": pose_source,
    "saturation_error": saturation_error,
    "saturation_label": saturation_label,
    "damping_ratio": damping_ratio,
    "round_frequency_hz": round_frequency_hz,
    "frequency_hz": frequency_hz,
    "force_limit_source": force_limit_source,
    "slide_warning": saw_slide_without_explicit_saturation,
    "skipped": [asdict(s) for s in skipped],
  }
  return records, meta


def _print_text(records: list[GainRecord], meta: dict[str, Any]) -> None:
  print(f"XML: {meta['xml_path']}")
  print(f"model dims: nq={meta['nq']} nv={meta['nv']} nu={meta['nu']}")
  print(f"pose: {meta['pose_source']}")
  if meta["frequency_hz"] is None:
    print(
      "mode: force-limit classes; "
      f"saturation={meta['saturation_label']}; "
      f"damping_ratio={meta['damping_ratio']:g}; "
      f"round_frequency_hz={meta['round_frequency_hz']:g}; "
      f"force_limit_source={meta['force_limit_source']}"
    )
  else:
    print(
      "mode: fixed frequency; "
      f"frequency_hz={meta['frequency_hz']:g}; "
      f"damping_ratio={meta['damping_ratio']:g}"
    )
  if meta.get("slide_warning"):
    print(
      "warning: at least one slide joint used the default angle-derived saturation; "
      "pass --saturation for prismatic coordinate units.",
      file=sys.stderr,
    )
  print()

  headers = (
    "actuator",
    "joint",
    "type",
    "dof",
    "force",
    "source",
    "f_hz",
    "M_ii",
    "kp",
    "kv",
  )
  widths = (24, 24, 7, 4, 11, 24, 8, 12, 12, 12)
  print(" ".join(h.ljust(w) for h, w in zip(headers, widths)))
  print(" ".join("-" * w for w in widths))
  for r in records:
    values = (
      r.actuator[:24],
      r.joint[:24],
      r.joint_type,
      str(r.dof),
      "" if r.force_limit is None else f"{r.force_limit:.6g}",
      "" if r.force_limit_source is None else r.force_limit_source,
      f"{r.frequency_hz:.4g}",
      f"{r.inertia:.6g}",
      f"{r.kp:.6g}",
      f"{r.kv:.6g}",
    )
    print(" ".join(v.ljust(w) for v, w in zip(values, widths)))

  skipped = meta.get("skipped") or []
  if skipped:
    print("\nskipped unsupported actuators:", file=sys.stderr)
    for item in skipped[:12]:
      print(f"  - {item['actuator']}: {item['reason']}", file=sys.stderr)
    if len(skipped) > 12:
      print(f"  ... {len(skipped) - 12} more", file=sys.stderr)


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Compute Menagerie-style kp/kv gains for joint-backed MJCF actuators.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )
  parser.add_argument("xml", type=Path, help="MJCF XML path to compile and inspect.")
  parser.add_argument(
    "--keyframe",
    help="Named keyframe whose qpos should be used before computing the mass matrix. Defaults to qpos0.",
  )
  parser.add_argument(
    "--saturation-angle-deg",
    type=float,
    default=10.0,
    help="Hinge-position error, in degrees, at which the actuator should saturate in force-limit mode.",
  )
  parser.add_argument(
    "--saturation",
    type=float,
    help="Override saturation error in model coordinate units, e.g. radians for hinges or meters for slides.",
  )
  parser.add_argument(
    "--damping-ratio",
    type=float,
    default=1.0,
    help="Second-order damping ratio used for kv = 2*zeta*M_ii*w_n.",
  )
  parser.add_argument(
    "--round-frequency-hz",
    type=float,
    default=0.5,
    help="Round derived class frequencies to this Hz step; use 0 to disable rounding.",
  )
  parser.add_argument(
    "--frequency-hz",
    type=float,
    help="Use one explicit natural frequency for all selected actuators, bypassing force-limit derivation.",
  )
  parser.add_argument(
    "--force-limit-source",
    choices=("auto", "actuator", "joint"),
    default="auto",
    help="Where to read force limits in saturation mode. Auto tries actuator forcerange, then joint actuatorfrcrange.",
  )
  parser.add_argument("--joint-regex", help="Only include joints whose names match this regular expression.")
  parser.add_argument("--actuator-regex", help="Only include actuators whose names match this regular expression.")
  parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of a text table.")
  return parser


def main(argv: list[str] | None = None) -> int:
  parser = build_arg_parser()
  args = parser.parse_args(argv)

  try:
    records, meta = compute_gains(
      args.xml.expanduser().resolve(),
      keyframe=args.keyframe,
      saturation=args.saturation,
      saturation_angle_deg=args.saturation_angle_deg,
      damping_ratio=args.damping_ratio,
      round_frequency_hz=args.round_frequency_hz,
      frequency_hz=args.frequency_hz,
      force_limit_source=args.force_limit_source,
      joint_regex=args.joint_regex,
      actuator_regex=args.actuator_regex,
    )
  except Exception as exc:  # pragma: no cover - keeps CLI errors concise.
    print(f"error: {exc}", file=sys.stderr)
    return 2

  if args.json:
    print(json.dumps({"metadata": meta, "gains": [asdict(r) for r in records]}, indent=2))
  else:
    _print_text(records, meta)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
