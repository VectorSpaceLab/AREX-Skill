#!/usr/bin/env python3
"""Diagnose RDKit checkout shadowing and missing rdBase imports."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any


EXTENSION_SUFFIXES = (".so", ".pyd", ".dll", ".dylib")


def _path(value: str | None) -> str | None:
  if value is None:
    return None
  try:
    return str(Path(value).resolve())
  except OSError:
    return value


def _is_within(child: Path, parent: Path) -> bool:
  try:
    child.resolve().relative_to(parent.resolve())
    return True
  except ValueError:
    return False


def _find_checkout_root(import_file: str | None) -> str | None:
  if not import_file:
    return None
  current = Path(import_file).resolve()
  if current.is_file():
    current = current.parent
  for candidate in [current, *current.parents]:
    if (candidate / "CMakeLists.txt").is_file() and (candidate / "Code").is_dir() and (
        candidate / "rdkit").is_dir():
      return str(candidate)
  return None


def _has_rdbase_extension(rdkit_dir: Path) -> bool:
  if not rdkit_dir.is_dir():
    return False
  for child in rdkit_dir.iterdir():
    if child.name.startswith("rdBase") and child.suffix in EXTENSION_SUFFIXES:
      return True
  return False


def _diagnose(expect_binary: bool) -> dict[str, Any]:
  cwd = os.getcwd()
  result: dict[str, Any] = {
    "status": "unknown",
    "message": "",
    "cwd": _path(cwd),
    "sys_path_0": _path(sys.path[0] if sys.path else None),
    "considered_cwd_first": False,
    "rdkit_file": None,
    "rdbase_file": None,
    "checkout_root": None,
    "has_local_rdbase_extension": None,
    "expect_binary": expect_binary,
  }

  if "" not in sys.path and cwd not in sys.path:
    sys.path.insert(0, cwd)
    result["considered_cwd_first"] = True

  spec = importlib.util.find_spec("rdkit")
  spec_origin = getattr(spec, "origin", None) if spec else None
  preimport_checkout_root = _find_checkout_root(spec_origin)
  if spec_origin:
    result["rdkit_file"] = _path(spec_origin)
    result["checkout_root"] = preimport_checkout_root

  try:
    rdkit = importlib.import_module("rdkit")
  except Exception as exc:  # noqa: BLE001 - diagnostic tool should report any import failure.
    if preimport_checkout_root:
      result["status"] = "shadowing"
      result["message"] = (
        "Python resolved RDKit to a source checkout before import failed. "
        "Build the checkout or run binary-package checks outside the checkout. "
        f"Original error: {exc.__class__.__name__}: {exc}"
      )
    else:
      result["status"] = "import_error"
      result["message"] = f"Failed to import rdkit: {exc.__class__.__name__}: {exc}"
    return result

  rdkit_file = getattr(rdkit, "__file__", None)
  result["rdkit_file"] = _path(rdkit_file)
  checkout_root = _find_checkout_root(rdkit_file)
  result["checkout_root"] = checkout_root

  if rdkit_file:
    rdkit_dir = Path(rdkit_file).resolve().parent
    result["has_local_rdbase_extension"] = _has_rdbase_extension(rdkit_dir)

  try:
    rdbase = importlib.import_module("rdkit.rdBase")
  except Exception as exc:  # noqa: BLE001 - diagnostic tool should report any import failure.
    if checkout_root:
      result["status"] = "shadowing"
      result["message"] = (
        "Python imported RDKit from a source checkout, but rdkit.rdBase could not be imported. "
        "Build the checkout or run binary-package checks outside the checkout. "
        f"Original error: {exc.__class__.__name__}: {exc}"
      )
    else:
      result["status"] = "import_error"
      result["message"] = f"Imported rdkit, but failed to import rdkit.rdBase: {exc.__class__.__name__}: {exc}"
    return result

  result["rdbase_file"] = _path(getattr(rdbase, "__file__", None))

  if checkout_root and expect_binary:
    result["status"] = "shadowing"
    result["message"] = (
      "RDKit imports successfully, but it is coming from a source checkout while a binary/install "
      "import was expected. Run from a neutral directory or adjust PYTHONPATH."
    )
  elif checkout_root and not result["has_local_rdbase_extension"]:
    result["status"] = "warning"
    result["message"] = (
      "RDKit imports from a checkout and rdBase is available, but no rdBase extension was found "
      "next to rdkit/__init__.py. Confirm the import path points at the intended built tree."
    )
  else:
    result["status"] = "ok"
    result["message"] = "RDKit and rdkit.rdBase import successfully from the current Python environment."

  return result


def _print_text(result: dict[str, Any]) -> None:
  status = str(result["status"]).upper()
  print(f"{status}: {result['message']}")
  for key in ("cwd", "sys_path_0", "considered_cwd_first", "rdkit_file", "rdbase_file", "checkout_root", "has_local_rdbase_extension"):
    print(f"{key}: {result.get(key)}")


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Check whether a local RDKit source checkout shadows an installed package or lacks rdBase.")
  parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
  parser.add_argument(
    "--expect-binary",
    action="store_true",
    help="treat importing RDKit from a source checkout as a shadowing problem even if rdBase imports",
  )
  args = parser.parse_args(argv)

  result = _diagnose(expect_binary=args.expect_binary)
  if args.json:
    print(json.dumps(result, indent=2, sort_keys=True))
  else:
    _print_text(result)

  return 0 if result["status"] in {"ok", "warning"} else 1


if __name__ == "__main__":
  raise SystemExit(main())
