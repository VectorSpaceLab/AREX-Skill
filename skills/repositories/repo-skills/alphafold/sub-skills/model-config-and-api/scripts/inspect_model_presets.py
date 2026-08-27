#!/usr/bin/env python3
"""Inspect AlphaFold model presets and lightweight config fields.

This helper imports alphafold.model.config only. It does not load model weights,
construct RunModel, preprocess features, compile JAX functions, or run inference.
"""

from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import sys
from typing import Any


SELECTED_FIELDS = (
    "model.global_config.multimer_mode",
    "model.num_recycle",
    "model.num_ensemble_eval",
    "model.recycle_early_stop_tolerance",
    "model.resample_msa_in_recycling",
    "model.heads.predicted_aligned_error.weight",
    "model.embeddings_and_evoformer.template.enabled",
    "model.embeddings_and_evoformer.template.embed_torsion_angles",
    "model.embeddings_and_evoformer.num_msa",
    "model.embeddings_and_evoformer.num_extra_msa",
    "model.embeddings_and_evoformer.evoformer.triangle_multiplication_incoming.fuse_projection_weights",
    "data.common.use_templates",
    "data.common.max_extra_msa",
    "data.common.reduce_msa_clusters_by_max_templates",
    "data.eval.num_ensemble",
    "data.eval.max_templates",
)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description=(
          "Print AlphaFold model presets and selected config fields without "
          "loading parameters or running inference."
      )
  )
  parser.add_argument(
      "--model",
      action="append",
      default=[],
      help="Inspect only this model name. May be repeated.",
  )
  parser.add_argument(
      "--include-historical",
      action="store_true",
      help="Also include CONFIG_DIFFS model names that are not in MODEL_PRESETS.",
  )
  parser.add_argument(
      "--fields",
      nargs="*",
      default=list(SELECTED_FIELDS),
      help="Dot-path config fields to print. Defaults to a curated model summary.",
  )
  parser.add_argument(
      "--json",
      action="store_true",
      help="Emit JSON instead of human-readable text.",
  )
  parser.add_argument(
      "--source-root",
      default=None,
      help=(
          "Optional local checkout root containing alphafold/model/config.py. "
          "Use only when inspecting an editable checkout that is not importable "
          "from the current Python environment."
      ),
  )
  return parser.parse_args()


def package_version() -> str | None:
  for distribution_name in ("alphafold", "alphafold-colabfold"):
    try:
      return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
      continue
  return None


def get_path(value: Any, path: str) -> Any:
  current = value
  for part in path.split("."):
    if current is None:
      return None
    try:
      current = getattr(current, part)
    except AttributeError:
      try:
        current = current[part]
      except (KeyError, TypeError):
        return None
  return current


def normalize(value: Any) -> Any:
  if isinstance(value, tuple):
    return list(value)
  if isinstance(value, (str, int, float, bool)) or value is None:
    return value
  try:
    return value.item()
  except AttributeError:
    return str(value)


def model_to_presets(presets: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
  result: dict[str, list[str]] = {}
  for preset, names in presets.items():
    for name in names:
      result.setdefault(name, []).append(preset)
  return result


def summarize_model(config_module: Any, model_name: str, fields: list[str]) -> dict[str, Any]:
  cfg = config_module.model_config(model_name)
  return {
      "model_name": model_name,
      "fields": {field: normalize(get_path(cfg, field)) for field in fields},
  }


def maybe_add_source_root(path: Path) -> bool:
  root = path.expanduser().resolve()
  if not (root / "alphafold" / "model" / "config.py").is_file():
    return False
  root_text = str(root)
  if root_text not in sys.path:
    sys.path.insert(0, root_text)
  return True


def add_import_fallbacks(args: argparse.Namespace) -> bool:
  candidates: list[Path] = []
  if args.source_root:
    candidates.append(Path(args.source_root))
  cwd = Path.cwd()
  candidates.extend([cwd, *list(cwd.parents)[:5]])

  for candidate in candidates:
    if maybe_add_source_root(candidate):
      return True
  return False


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
  source_root_fallback_used = add_import_fallbacks(args)
  try:
    from alphafold.model import config as model_config_module
  except Exception as exc:  # pylint: disable=broad-exception-caught
    return {
        "ok": False,
        "error": f"failed to import alphafold.model.config: {exc}",
        "source_root_fallback_used": source_root_fallback_used,
        "repair_hint": (
            "Check pinned dependencies such as dm-haiku, ml-collections, jax, "
            "jaxlib, numpy, ml-dtypes, and tensorflow-cpu before debugging model code."
        ),
    }

  presets = {
      preset: list(names)
      for preset, names in model_config_module.MODEL_PRESETS.items()
  }
  configured_names = set(model_config_module.CONFIG_DIFFS)
  preset_names = {name for names in presets.values() for name in names}
  requested_names = list(dict.fromkeys(args.model))
  if requested_names:
    model_names = requested_names
  else:
    model_names = sorted(configured_names if args.include_historical else preset_names)

  unknown = [name for name in model_names if name not in configured_names]
  if unknown:
    return {
        "ok": False,
        "error": f"unknown model name(s): {', '.join(unknown)}",
        "available_model_names": sorted(configured_names),
        "presets": presets,
    }

  model_presets = model_to_presets(model_config_module.MODEL_PRESETS)
  models = []
  for model_name in model_names:
    summary = summarize_model(model_config_module, model_name, args.fields)
    summary["presets"] = model_presets.get(model_name, [])
    summary["historical_only"] = model_name not in preset_names
    models.append(summary)

  return {
      "ok": True,
      "package_version": package_version(),
      "presets": presets,
      "inspected_model_count": len(models),
      "models": models,
      "source_root_fallback_used": source_root_fallback_used,
      "safety": {
          "loaded_weights": False,
          "constructed_run_model": False,
          "ran_inference": False,
      },
  }


def print_text(payload: dict[str, Any]) -> None:
  if not payload.get("ok"):
    print(f"ERROR: {payload.get('error')}", file=sys.stderr)
    if payload.get("repair_hint"):
      print(f"Hint: {payload['repair_hint']}", file=sys.stderr)
    return

  print("AlphaFold model preset inspection")
  if payload.get("package_version"):
    print(f"Package version: {payload['package_version']}")
  print("Safety: no weights loaded; no RunModel constructed; no inference run")
  print("\nPresets:")
  for preset, names in payload["presets"].items():
    print(f"  {preset}: {', '.join(names)}")

  print("\nModels:")
  for model in payload["models"]:
    preset_label = ", ".join(model["presets"]) or "historical/config-only"
    print(f"  {model['model_name']} ({preset_label})")
    if model["historical_only"]:
      print("    historical_only: true")
    for field, value in model["fields"].items():
      if value is not None:
        print(f"    {field}: {value}")


def main() -> int:
  args = parse_args()
  payload = build_payload(args)
  if args.json:
    print(json.dumps(payload, indent=2, sort_keys=True))
  else:
    print_text(payload)
  return 0 if payload.get("ok") else 1


if __name__ == "__main__":
  raise SystemExit(main())
