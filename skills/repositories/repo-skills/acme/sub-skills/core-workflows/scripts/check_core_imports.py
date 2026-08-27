#!/usr/bin/env python3
"""Inspect Acme core import surfaces and optional dependency availability.

This helper is intentionally read-only. It imports selected Acme modules,
records signatures and versions when available, and reports optional dependency
failures without running JAX, TensorFlow, Reverb, Launchpad, Gym, Atari, or
OpenSpiel workloads.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from typing import Any, Dict, Iterable, Optional


CORE_MODULES = (
    "acme",
    "acme.core",
    "acme.specs",
    "acme.environment_loop",
    "acme.wrappers.base",
    "acme.wrappers.single_precision",
    "acme.wrappers.canonical_spec",
    "acme.utils.counting",
    "acme.utils.signals",
)

SENSITIVE_MODULES = (
    "acme.utils.loggers",
    "acme.utils.observers",
    "acme.wrappers",
    "acme.wrappers.gym_wrapper",
    "acme.environment_loops.open_spiel_environment_loop",
)

OPTIONAL_PACKAGES = (
    "jax",
    "tensorflow",
    "reverb",
    "launchpad",
    "sonnet",
    "trfl",
    "gym",
    "atari_py",
    "pyspiel",
)

SIGNATURE_TARGETS = (
    ("acme.core", "Actor.select_action"),
    ("acme.core", "Actor.observe_first"),
    ("acme.core", "Actor.observe"),
    ("acme.core", "Actor.update"),
    ("acme.core", "Learner.run"),
    ("acme.specs", "Array"),
    ("acme.specs", "BoundedArray"),
    ("acme.specs", "EnvironmentSpec"),
    ("acme.specs", "make_environment_spec"),
    ("acme.environment_loop", "EnvironmentLoop.__init__"),
    ("acme.environment_loop", "EnvironmentLoop.run"),
    ("acme.utils.counting", "Counter.__init__"),
    ("acme.utils.counting", "Counter.increment"),
)


def _safe_import(module_name: str) -> Dict[str, Any]:
  try:
    module = importlib.import_module(module_name)
  except Exception as exc:  # pylint: disable=broad-except
    return {
        "ok": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }

  result: Dict[str, Any] = {"ok": True}
  version = getattr(module, "__version__", None)
  if version is not None:
    result["version"] = str(version)
  return result


def _resolve_attr(module: Any, dotted_name: str) -> Any:
  current = module
  for part in dotted_name.split("."):
    current = getattr(current, part)
  return current


def _signature_for(module_name: str, dotted_name: str) -> Dict[str, Any]:
  try:
    module = importlib.import_module(module_name)
    target = _resolve_attr(module, dotted_name)
    return {"ok": True, "signature": str(inspect.signature(target))}
  except Exception as exc:  # pylint: disable=broad-except
    return {
        "ok": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }


def _collect(include_sensitive: bool) -> Dict[str, Any]:
  modules = list(CORE_MODULES)
  if include_sensitive:
    modules.extend(SENSITIVE_MODULES)

  report: Dict[str, Any] = {
      "summary": {
          "core_modules_ok": True,
          "sensitive_modules_ok": None if not include_sensitive else True,
      },
      "modules": {},
      "optional_packages": {},
      "signatures": {},
      "notes": [],
  }

  for module_name in modules:
    module_report = _safe_import(module_name)
    report["modules"][module_name] = module_report
    if module_name in CORE_MODULES and not module_report["ok"]:
      report["summary"]["core_modules_ok"] = False
    if include_sensitive and module_name in SENSITIVE_MODULES and not module_report["ok"]:
      report["summary"]["sensitive_modules_ok"] = False

  for package_name in OPTIONAL_PACKAGES:
    report["optional_packages"][package_name] = _safe_import(package_name)

  for module_name, dotted_name in SIGNATURE_TARGETS:
    report["signatures"][f"{module_name}.{dotted_name}"] = _signature_for(
        module_name, dotted_name)

  acme_module = importlib.import_module("acme") if report["modules"].get(
      "acme", {}).get("ok") else None
  if acme_module is not None:
    version = getattr(acme_module, "__version__", None)
    if version is not None:
      report["summary"]["acme_version"] = str(version)

  if not report["optional_packages"]["jax"]["ok"]:
    report["notes"].append(
        "JAX is optional for many Acme workflows, but this Acme version imports "
        "jax from acme.utils.loggers.base; logger imports may fail in a core-only install.")
  if not report["optional_packages"]["gym"]["ok"]:
    report["notes"].append(
        "Gym is optional; GymWrapper and Gym-like environment recipes require it or a custom dm_env adapter.")
  if not report["optional_packages"]["pyspiel"]["ok"]:
    report["notes"].append(
        "OpenSpiel support is optional; ordinary EnvironmentLoop workflows do not require pyspiel.")
  if not report["optional_packages"]["tensorflow"]["ok"]:
    report["notes"].append(
        "TensorFlow/Sonnet agents are outside core workflow scope and require optional backend dependencies.")

  return report


def _print_human(report: Dict[str, Any]) -> None:
  summary = report["summary"]
  print("Acme core import report")
  if "acme_version" in summary:
    print(f"Acme version: {summary['acme_version']}")
  print(f"Core modules OK: {summary['core_modules_ok']}")
  if summary["sensitive_modules_ok"] is not None:
    print(f"Sensitive modules OK: {summary['sensitive_modules_ok']}")

  print("\nModules:")
  for name, item in report["modules"].items():
    status = "ok" if item["ok"] else f"FAILED ({item['error_type']}: {item['error']})"
    print(f"  - {name}: {status}")

  print("\nOptional packages:")
  for name, item in report["optional_packages"].items():
    if item["ok"]:
      version = item.get("version")
      suffix = f" {version}" if version else " available"
      print(f"  - {name}:{suffix}")
    else:
      print(f"  - {name}: missing or failed ({item['error_type']}: {item['error']})")

  print("\nSelected signatures:")
  for name, item in report["signatures"].items():
    if item["ok"]:
      print(f"  - {name}{item['signature']}")
    else:
      print(f"  - {name}: unavailable ({item['error_type']}: {item['error']})")

  if report["notes"]:
    print("\nNotes:")
    for note in report["notes"]:
      print(f"  - {note}")


def main(argv: Optional[Iterable[str]] = None) -> int:
  parser = argparse.ArgumentParser(
      description="Inspect Acme core imports, optional dependencies, and signatures.")
  parser.add_argument(
      "--json",
      action="store_true",
      help="Emit machine-readable JSON instead of a human-readable report.")
  parser.add_argument(
      "--include-sensitive-imports",
      action="store_true",
      help=("Also import modules that may pull optional dependencies, such as "
            "acme.utils.loggers, acme.wrappers, GymWrapper, and OpenSpiel loop."),
  )
  args = parser.parse_args(argv)

  report = _collect(include_sensitive=args.include_sensitive_imports)
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    _print_human(report)

  return 0 if report["summary"]["core_modules_ok"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
