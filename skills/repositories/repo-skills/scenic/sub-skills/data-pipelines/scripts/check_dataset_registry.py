#!/usr/bin/env python3
"""Safely inspect Scenic's dataset registry.

This helper imports registry modules and optionally resolves a dataset builder.
It never calls the returned builder, never calls train_utils.get_dataset, and
never asks TFDS to download or prepare data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from typing import Any, Dict, Iterable, List, Tuple


def _error_payload(exc: BaseException) -> Dict[str, Any]:
  payload: Dict[str, Any] = {
      "ok": False,
      "error_type": type(exc).__name__,
      "message": str(exc),
  }
  if isinstance(exc, ModuleNotFoundError):
    payload["missing_module"] = getattr(exc, "name", None)
  return payload


def _hint_for_error(payload: Dict[str, Any], dataset_name: str | None = None,
                    lazy_names: Iterable[str] = ()) -> str:
  text = " ".join(str(payload.get(k, "")) for k in ("error_type", "message", "missing_module"))
  lower = text.lower()
  if "unknown dataset" in lower:
    if dataset_name and dataset_name not in set(lazy_names):
      return ("Dataset is not in Scenic's lazy table. Import the project module "
              "that registers it with @datasets.add_dataset(...), or fix "
              "config.dataset_name if it is a typo.")
    return "Dataset is in the lazy table but lookup still failed; inspect the import error or registration name mismatch."
  if "tensorflow_addons" in lower:
    return "BigTransfer rotate/randaugment preprocessing may require tensorflow_addons compatible with TensorFlow."
  if "pycocotools" in lower:
    return "COCO annotation/evaluation utilities commonly require pycocotools; install only if the selected COCO workflow needs it."
  if "grain" in lower:
    return "FlexIO Grain-backed sources require grain.tensorflow; use TFDS sources or install Grain support."
  if "clu" in lower:
    return "FlexIO preprocessing/deterministic data requires clu."
  if "flax" in lower or "jax" in lower or "ml_collections" in lower:
    return "Importing Scenic's dataset utilities requires the Scenic runtime stack; activate/use the verified Scenic environment for registry checks."
  if "tensorflow" in lower or "cuda" in lower or "cudnn" in lower:
    return "For registry-only diagnostics, retry with CUDA_VISIBLE_DEVICES='' if TensorFlow GPU initialization is the issue."
  return "Use --verbose-traceback for the full import/lookup stack."


def _load_datasets_module() -> Tuple[Any | None, Dict[str, Any] | None]:
  try:
    module = importlib.import_module("scenic.dataset_lib.datasets")
    return module, None
  except Exception as exc:  # pylint: disable=broad-exception-caught
    return None, _error_payload(exc)


def _lazy_table(datasets_module: Any) -> Dict[str, str]:
  table = getattr(datasets_module, "_IMPORT_TABLE", {})
  return {str(k): str(v) for k, v in sorted(table.items())}


def _registered_names(datasets_module: Any) -> List[str]:
  try:
    return sorted(datasets_module.DatasetRegistry.list())
  except Exception:  # pylint: disable=broad-exception-caught
    return []


def _import_modules(modules: Iterable[str]) -> List[Dict[str, Any]]:
  results = []
  for module_name in modules:
    try:
      importlib.import_module(module_name)
      results.append({"module": module_name, "ok": True})
    except Exception as exc:  # pylint: disable=broad-exception-caught
      payload = _error_payload(exc)
      payload["module"] = module_name
      results.append(payload)
  return results


def _lookup_dataset(datasets_module: Any, dataset_name: str,
                    lazy_names: Iterable[str]) -> Dict[str, Any]:
  try:
    builder = datasets_module.get_dataset(dataset_name)
    return {
        "dataset_name": dataset_name,
        "ok": True,
        "builder_repr": repr(builder),
        "builder_module": getattr(builder, "__module__", None),
        "builder_name": getattr(builder, "__name__", None),
        "note": "Lookup succeeded; the builder was not called.",
    }
  except Exception as exc:  # pylint: disable=broad-exception-caught
    payload = _error_payload(exc)
    payload["dataset_name"] = dataset_name
    payload["hint"] = _hint_for_error(payload, dataset_name, lazy_names)
    return payload


def _print_human(report: Dict[str, Any]) -> None:
  if not report.get("scenic_import", {}).get("ok"):
    err = report["scenic_import"]
    print("Scenic dataset registry import: FAILED", file=sys.stderr)
    print(f"  {err.get('error_type')}: {err.get('message')}", file=sys.stderr)
    print(f"  hint: {err.get('hint')}", file=sys.stderr)
    return

  print("Scenic dataset registry import: OK")
  lazy_table = report.get("lazy_import_table", {})
  print(f"Known lazy dataset names ({len(lazy_table)}):")
  for name, module in lazy_table.items():
    print(f"  {name:32s} -> {module}")
  registered = report.get("registered_names", [])
  print(f"Already registered in this process ({len(registered)}): {', '.join(registered) if registered else '(none)'}")

  for item in report.get("module_imports", []):
    if item.get("ok"):
      print(f"Imported module: {item['module']}")
    else:
      print(f"Module import failed: {item['module']}", file=sys.stderr)
      print(f"  {item.get('error_type')}: {item.get('message')}", file=sys.stderr)
      if item.get("hint"):
        print(f"  hint: {item['hint']}", file=sys.stderr)

  lookup = report.get("lookup")
  if lookup:
    if lookup.get("ok"):
      print(f"Dataset lookup OK: {lookup['dataset_name']}")
      print(f"  builder: {lookup.get('builder_repr')}")
      print("  note: builder was not called; no data was downloaded or read.")
    else:
      print(f"Dataset lookup failed: {lookup.get('dataset_name')}", file=sys.stderr)
      print(f"  {lookup.get('error_type')}: {lookup.get('message')}", file=sys.stderr)
      print(f"  hint: {lookup.get('hint')}", file=sys.stderr)


def main(argv: List[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
      description=(
          "Safely list Scenic lazy dataset names and optionally resolve a "
          "dataset builder without building datasets or downloading data."),
      epilog=(
          "Examples:\n"
          "  check_dataset_registry.py --list\n"
          "  check_dataset_registry.py --dataset-name cifar10\n"
          "  check_dataset_registry.py --import-module my_project.input_pipeline "
          "--dataset-name my_dataset"),
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      "--list", action="store_true",
      help="List lazy import table and currently registered names. This is also the default when no lookup is requested.")
  parser.add_argument(
      "--dataset-name",
      help="Optionally resolve this registry name to a builder. The builder is not called.")
  parser.add_argument(
      "--import-module", action="append", default=[], metavar="MODULE",
      help="Import a registration module before lookup. May be repeated for project/custom datasets.")
  parser.add_argument(
      "--json", action="store_true",
      help="Emit machine-readable JSON instead of human-readable text.")
  parser.add_argument(
      "--verbose-traceback", action="store_true",
      help="Include traceback text in JSON and print tracebacks for failures.")
  args = parser.parse_args(argv)

  datasets_module, import_error = _load_datasets_module()
  report: Dict[str, Any] = {
      "safe_behavior": "No dataset builders are called; no TFDS download/prepare is requested.",
  }
  if import_error:
    import_error["hint"] = _hint_for_error(import_error)
    if args.verbose_traceback:
      import_error["traceback"] = traceback.format_exc()
    report["scenic_import"] = import_error
    if args.json:
      print(json.dumps(report, indent=2, sort_keys=True))
    else:
      _print_human(report)
    return 2

  report["scenic_import"] = {"ok": True}
  lazy_table = _lazy_table(datasets_module)
  report["lazy_import_table"] = lazy_table
  report["registered_names"] = _registered_names(datasets_module)

  module_results = _import_modules(args.import_module)
  for item in module_results:
    if not item.get("ok"):
      item["hint"] = _hint_for_error(item, args.dataset_name, lazy_table)
      if args.verbose_traceback:
        item["traceback"] = traceback.format_exc()
  report["module_imports"] = module_results
  if args.import_module:
    report["registered_names_after_imports"] = _registered_names(datasets_module)

  if args.dataset_name:
    report["lookup"] = _lookup_dataset(datasets_module, args.dataset_name, lazy_table)
    report["registered_names_after_lookup"] = _registered_names(datasets_module)

  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    _print_human(report)

  failed = False
  failed = failed or any(not item.get("ok") for item in module_results)
  failed = failed or bool(report.get("lookup") and not report["lookup"].get("ok"))
  return 2 if failed else 0


if __name__ == "__main__":
  raise SystemExit(main())
