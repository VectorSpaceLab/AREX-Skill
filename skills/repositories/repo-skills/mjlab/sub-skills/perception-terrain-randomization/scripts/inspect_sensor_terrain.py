from __future__ import annotations

import argparse
import importlib
import inspect
import json
from typing import Any

OBJECTS = [
  ("mjlab.sensor", "BuiltinSensorCfg"),
  ("mjlab.sensor", "ContactMatch"),
  ("mjlab.sensor", "ContactSensorCfg"),
  ("mjlab.sensor", "GridPatternCfg"),
  ("mjlab.sensor", "PinholeCameraPatternCfg"),
  ("mjlab.sensor", "RingPatternCfg"),
  ("mjlab.sensor", "RayCastSensorCfg"),
  ("mjlab.sensor", "TerrainHeightSensorCfg"),
  ("mjlab.sensor", "CameraSensorCfg"),
  ("mjlab.terrains", "TerrainEntityCfg"),
  ("mjlab.terrains", "TerrainGeneratorCfg"),
  ("mjlab.terrains", "FlatPatchSamplingCfg"),
]

DR_MODULES = [
  "mjlab.envs.mdp.dr.body",
  "mjlab.envs.mdp.dr.geom",
  "mjlab.envs.mdp.dr.joint",
  "mjlab.envs.mdp.dr.actuator",
  "mjlab.envs.mdp.dr.camera",
  "mjlab.envs.mdp.dr.light",
  "mjlab.envs.mdp.dr.material",
  "mjlab.envs.mdp.dr.site",
  "mjlab.envs.mdp.dr.tendon",
]


def _signature(obj: Any) -> str:
  try:
    return str(inspect.signature(obj))
  except (TypeError, ValueError):
    return "<signature unavailable>"


def build_report() -> dict[str, Any]:
  signatures = {}
  for module_name, name in OBJECTS:
    module = importlib.import_module(module_name)
    signatures[f"{module_name}.{name}"] = _signature(getattr(module, name))

  import mjlab.terrains.config as terrain_config

  presets = sorted(
    name
    for name, value in vars(terrain_config).items()
    if not name.startswith("_") and callable(value)
  )

  dr = {}
  for module_name in DR_MODULES:
    module = importlib.import_module(module_name)
    dr[module_name] = sorted(
      name
      for name, value in vars(module).items()
      if not name.startswith("_")
      and callable(value)
      and getattr(value, "__module__", "") == module_name
    )

  return {"signatures": signatures, "terrain_presets": presets, "dr_functions": dr}


def main() -> int:
  parser = argparse.ArgumentParser(
    description="Inspect installed mjlab sensor, terrain, and DR APIs."
  )
  parser.add_argument("--json", action="store_true", help="Emit JSON.")
  args = parser.parse_args()

  report = build_report()
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

  print("Sensor and terrain signatures")
  for name, sig in report["signatures"].items():
    print(f"- {name}: {sig}")
  print("\nTerrain presets")
  for name in report["terrain_presets"]:
    print(f"- {name}")
  print("\nDomain-randomization functions")
  for module, names in report["dr_functions"].items():
    print(f"- {module}: {', '.join(names) if names else '-'}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
