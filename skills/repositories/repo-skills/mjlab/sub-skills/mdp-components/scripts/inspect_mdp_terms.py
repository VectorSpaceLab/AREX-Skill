from __future__ import annotations

import argparse
import importlib
import inspect
import json
from typing import Any

DEFAULT_MODULES = [
  "mjlab.envs.mdp.observations",
  "mjlab.envs.mdp.rewards",
  "mjlab.envs.mdp.terminations",
  "mjlab.envs.mdp.events",
  "mjlab.envs.mdp.metrics",
  "mjlab.envs.mdp.actions",
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


def public_callables(module_name: str) -> list[dict[str, Any]]:
  module = importlib.import_module(module_name)
  rows: list[dict[str, Any]] = []
  for name, value in sorted(vars(module).items()):
    if name.startswith("_") or not callable(value):
      continue
    owner = getattr(value, "__module__", "")
    if owner != module_name:
      continue
    try:
      signature = str(inspect.signature(value))
    except (TypeError, ValueError):
      signature = "<signature unavailable>"
    rows.append({"name": name, "signature": signature})
  return rows


def main() -> int:
  parser = argparse.ArgumentParser(
    description="List public mjlab MDP callables and signatures from installed modules."
  )
  parser.add_argument(
    "--module",
    action="append",
    dest="modules",
    help="Module to inspect. May be repeated. Defaults to common MDP modules.",
  )
  parser.add_argument("--json", action="store_true", help="Emit JSON.")
  args = parser.parse_args()

  modules = args.modules or DEFAULT_MODULES
  report = {module: public_callables(module) for module in modules}
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

  for module, rows in report.items():
    print(module)
    if not rows:
      print("  - no public callables found")
      continue
    for row in rows:
      print(f"  - {row['name']}{row['signature']}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
