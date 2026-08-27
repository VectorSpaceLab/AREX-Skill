#!/usr/bin/env python3
"""Inspect an AlphaFold installation without running prediction or downloads."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import sys
from typing import Any

CHECKS = ("run_alphafold", "docker", "openmm", "jax", "tensorflow", "binaries")
BINARIES = ("jackhmmer", "hhblits", "hhsearch", "hmmsearch", "hmmbuild", "kalign")


def _import_module(name: str) -> dict[str, Any]:
  try:
    module = importlib.import_module(name)
    return {
        "ok": True,
        "version": getattr(module, "__version__", None),
        "file_present": bool(getattr(module, "__file__", None)),
    }
  except Exception as exc:  # pylint: disable=broad-except
    return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _distribution(name: str) -> dict[str, Any]:
  try:
    dist = metadata.distribution(name)
    return {
        "ok": True,
        "name": dist.metadata.get("Name"),
        "version": dist.version,
        "console_scripts": sorted(
            f"{ep.name}={ep.value}"
            for ep in dist.entry_points
            if ep.group == "console_scripts"
        ),
    }
  except Exception as exc:  # pylint: disable=broad-except
    return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _binary_checks() -> dict[str, Any]:
  return {binary: {"found": shutil.which(binary) is not None} for binary in BINARIES}


def run_checks(selected: list[str]) -> dict[str, Any]:
  selected_set = set(selected or CHECKS)
  result: dict[str, Any] = {
      "python": sys.version.split()[0],
      "alphafold_distribution": _distribution("alphafold"),
      "alphafold_import": _import_module("alphafold"),
      "checks": {},
      "warnings": [],
  }

  if "run_alphafold" in selected_set:
    result["checks"]["run_alphafold"] = _import_module("run_alphafold")
  if "docker" in selected_set:
    result["checks"]["docker_python"] = _import_module("docker")
    result["checks"]["docker_cli"] = {"found": shutil.which("docker") is not None}
  if "openmm" in selected_set:
    result["checks"]["openmm"] = _import_module("openmm")
    result["checks"]["pdbfixer"] = _import_module("pdbfixer")
  if "jax" in selected_set:
    jax = _import_module("jax")
    jaxlib = _distribution("jaxlib")
    result["checks"]["jax"] = jax
    result["checks"]["jaxlib"] = jaxlib
    if jax.get("ok") and jaxlib.get("ok") and jax.get("version") != jaxlib.get("version"):
      result["warnings"].append(
          "jax and jaxlib versions differ; AlphaFold imports may fail if they are incompatible"
      )
  if "tensorflow" in selected_set:
    result["checks"]["tensorflow"] = _import_module("tensorflow")
  if "binaries" in selected_set:
    result["checks"]["external_binaries"] = _binary_checks()

  result["ready_for_full_prediction"] = False
  result["notes"] = [
      "This script only checks imports, versions, entry points, CLI presence, and binary discovery.",
      "Full AlphaFold prediction also requires model parameters, genetic/template databases, writable output storage, external binaries, and suitable CPU/GPU resources.",
  ]
  return result


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--check",
      action="append",
      choices=CHECKS,
      default=[],
      help="Check group to run. May be repeated; defaults to all groups.",
  )
  parser.add_argument("--json", action="store_true", help="Emit JSON output.")
  args = parser.parse_args(argv)
  result = run_checks(args.check)
  if args.json:
    print(json.dumps(result, indent=2, sort_keys=True))
  else:
    print("AlphaFold install inspection")
    print(f"Python: {result['python']}")
    dist = result["alphafold_distribution"]
    print(f"alphafold distribution: {dist.get('version') if dist.get('ok') else dist.get('error')}")
    print(f"alphafold import: {'ok' if result['alphafold_import'].get('ok') else result['alphafold_import'].get('error')}")
    for name, value in result["checks"].items():
      if isinstance(value, dict) and "ok" in value:
        print(f"{name}: {'ok' if value['ok'] else value.get('error')}")
      else:
        print(f"{name}: {value}")
    for warning in result["warnings"]:
      print(f"warning: {warning}")
    print("Full prediction readiness is not proven by this diagnostic.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
