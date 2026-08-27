#!/usr/bin/env python3
"""Check that a Python environment can use MuJoCo Menagerie XML assets.

This helper is intentionally independent of the source repository checkout. It
verifies selected Python imports, compiles a tiny in-memory MuJoCo model, and
optionally compiles or short-steps a user-provided Menagerie XML path.

Examples:
  python scripts/check_menagerie_environment.py
  python scripts/check_menagerie_environment.py --xml /path/to/unitree_go2/scene.xml --step-seconds 0.02
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def _import(name: str) -> object:
  try:
    return importlib.import_module(name)
  except Exception as exc:  # pragma: no cover - diagnostics path
    raise SystemExit(f"FAILED import {name!r}: {exc}") from exc


def _warning_summary(mujoco, data) -> str:
  rows = []
  for enum_value, count in enumerate(data.warning.number):
    if count:
      rows.append(f"{mujoco.mjtWarning(enum_value).name}: count={count}")
  return "\n".join(rows)


def _set_safe_controls(mujoco, model, data, index: int, noise_scale: float) -> None:
  for actuator_id in range(model.nu):
    ctrlrange = model.actuator_ctrlrange[actuator_id]
    if model.actuator_ctrllimited[actuator_id]:
      center = 0.5 * (ctrlrange[1] + ctrlrange[0])
      radius = 0.5 * (ctrlrange[1] - ctrlrange[0])
    else:
      center = 0.0
      radius = 1.0
    data.ctrl[actuator_id] = center + radius * noise_scale * (
      2 * mujoco.mju_Halton(index, actuator_id + 2) - 1
    )


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "--xml",
    type=Path,
    help="Optional MJCF XML to compile. Keep XML beside its asset/include tree.",
  )
  parser.add_argument(
    "--step-seconds",
    type=float,
    default=0.0,
    help="Optional short simulation duration after compiling --xml.",
  )
  parser.add_argument(
    "--noise-scale",
    type=float,
    default=1.0,
    help="Control-noise scale for short stepping, matching Menagerie test style.",
  )
  parser.add_argument(
    "--optional",
    action="append",
    default=[],
    metavar="MODULE",
    help="Optional module to import and report, e.g. robot_descriptions.",
  )
  args = parser.parse_args()

  mujoco = _import("mujoco")
  print(f"mujoco import ok: {getattr(mujoco, '__version__', 'unknown')}")

  tiny = mujoco.MjModel.from_xml_string(
    '<mujoco model="smoke"><worldbody><geom type="sphere" size="0.01"/></worldbody></mujoco>'
  )
  print(f"in-memory compile ok: nbody={tiny.nbody} ngeom={tiny.ngeom}")

  for module in args.optional:
    try:
      importlib.import_module(module)
    except Exception as exc:
      print(f"optional import {module!r}: unavailable ({exc})")
    else:
      print(f"optional import {module!r}: ok")

  if args.xml is not None:
    xml = args.xml.expanduser().resolve()
    if not xml.is_file():
      raise SystemExit(f"XML file does not exist: {xml}")
    try:
      model = mujoco.MjModel.from_xml_path(str(xml))
    except Exception as exc:
      raise SystemExit(
        "FAILED to compile XML. Keep the XML beside its asset/include tree and "
        f"check the MuJoCo version. XML: {xml}\n{exc}"
      ) from exc
    print(
      "xml compile ok: "
      f"nq={model.nq} nv={model.nv} nu={model.nu} nbody={model.nbody} ngeom={model.ngeom}"
    )
    if args.step_seconds > 0:
      data = mujoco.MjData(model)
      i = 0
      while data.time < args.step_seconds:
        _set_safe_controls(mujoco, model, data, i, args.noise_scale)
        mujoco.mj_step(model, data)
        i += 1
      warnings = _warning_summary(mujoco, data)
      if warnings:
        raise SystemExit(f"FAILED: MuJoCo warnings encountered after stepping:\n{warnings}")
      print(f"short step ok: simulated {data.time:.6f}s without MuJoCo warnings")

  return 0


if __name__ == "__main__":
  sys.exit(main())
