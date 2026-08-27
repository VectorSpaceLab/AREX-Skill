#!/usr/bin/env python3
"""Check whether RDKit is importable and basic compiled APIs work."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="Run a small RDKit environment and import smoke check.")
  parser.add_argument("--json", action="store_true", help="Write a JSON report instead of text.")
  parser.add_argument(
      "--check-checkout-shadowing",
      action="store_true",
      help="Report whether the current directory appears to be an RDKit source checkout shadowing an installed package.",
  )
  return parser


def detect_checkout_shadowing() -> dict[str, object]:
  cwd = Path.cwd().resolve()
  local_pkg = cwd / "rdkit" / "__init__.py"
  has_cmake = (cwd / "CMakeLists.txt").exists()
  return {
      "cwd_contains_rdkit_package": local_pkg.exists(),
      "cwd_contains_cmake": has_cmake,
      "likely_source_checkout": local_pkg.exists() and has_cmake,
  }


def run_check(include_shadowing: bool) -> tuple[int, dict[str, object]]:
  report: dict[str, object] = {
      "python": sys.version.split()[0],
      "cwd": os.getcwd(),
      "imports": {},
      "smoke": {},
  }
  if include_shadowing:
    report["checkout_shadowing"] = detect_checkout_shadowing()

  try:
    import rdkit
    report["rdkit_version"] = getattr(rdkit, "__version__", None)
    report["rdkit_file"] = getattr(rdkit, "__file__", None)
  except Exception as exc:  # noqa: BLE001 - diagnostic tool
    report["error"] = f"import rdkit failed: {exc}"
    return 1, report

  modules = [
      "rdkit.Chem",
      "rdkit.DataStructs",
      "rdkit.Chem.AllChem",
      "rdkit.Chem.rdFingerprintGenerator",
      "rdkit.Chem.MolStandardize",
  ]
  ok = True
  imports = report["imports"]
  assert isinstance(imports, dict)
  for name in modules:
    try:
      module = importlib.import_module(name)
      imports[name] = {"ok": True, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
      imports[name] = {"ok": False, "error": str(exc)}
      ok = False

  try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors

    mol = Chem.MolFromSmiles("c1ccccc1O")
    assert mol is not None
    fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, 2, nBits=128)
    report["smoke"] = {
        "ok": True,
        "canonical_smiles": Chem.MolToSmiles(mol),
        "mol_wt_gt_90": Descriptors.MolWt(mol) > 90,
        "fingerprint_bits": fp.GetNumBits(),
    }
  except Exception as exc:  # noqa: BLE001 - diagnostic tool
    report["smoke"] = {"ok": False, "error": str(exc)}
    ok = False

  return (0 if ok else 1), report


def print_text(report: dict[str, object]) -> None:
  print(f"Python: {report.get('python')}")
  if "rdkit_version" in report:
    print(f"RDKit version: {report.get('rdkit_version')}")
    print(f"RDKit file: {report.get('rdkit_file')}")
  if "error" in report:
    print(f"ERROR: {report['error']}")
  if "checkout_shadowing" in report:
    print(f"Checkout shadowing: {report['checkout_shadowing']}")
  for name, result in (report.get("imports") or {}).items():
    print(f"{name}: {result}")
  print(f"Smoke: {report.get('smoke')}")


def main(argv: list[str] | None = None) -> int:
  args = build_parser().parse_args(argv)
  status, report = run_check(args.check_checkout_shadowing)
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print_text(report)
  return status


if __name__ == "__main__":
  raise SystemExit(main())
