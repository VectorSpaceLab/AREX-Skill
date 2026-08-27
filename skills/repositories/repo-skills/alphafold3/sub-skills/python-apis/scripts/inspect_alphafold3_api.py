#!/usr/bin/env python3
"""Safely inspect an installed AlphaFold 3 Python package.

This script imports key modules, reports package/version/resource facts, and
prints selected signatures. It never runs the data pipeline or model inference.
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
from importlib import resources
import inspect
from typing import Any


def _distribution_version() -> str:
  try:
    return metadata.version("alphafold3")
  except metadata.PackageNotFoundError:
    return "not installed as a distribution"


def _import_module(name: str) -> Any | None:
  try:
    module = importlib.import_module(name)
  except Exception as exc:  # pylint: disable=broad-exception-caught
    print(f"IMPORT {name}: FAILED: {type(exc).__name__}: {exc}")
    return None
  print(f"IMPORT {name}: ok")
  return module


def _signature(label: str, obj: Any) -> None:
  try:
    signature = inspect.signature(obj)
  except Exception as exc:  # pylint: disable=broad-exception-caught
    print(f"SIGNATURE {label}: unavailable: {type(exc).__name__}: {exc}")
    return
  print(f"SIGNATURE {label}: {signature}")


def _resource_exists(package_name: str, resource_name: str) -> bool | None:
  try:
    package = importlib.import_module(package_name)
    return resources.files(package).joinpath(resource_name).is_file()
  except Exception as exc:  # pylint: disable=broad-exception-caught
    print(
        f"RESOURCE {package_name}/{resource_name}: check failed: "
        f"{type(exc).__name__}: {exc}"
    )
    return None


def inspect_package(check_ccd_load: bool) -> int:
  print(f"alphafold3 distribution version: {_distribution_version()}")

  alphafold3 = _import_module("alphafold3")
  folding_input = _import_module("alphafold3.common.folding_input")
  data_pipeline = _import_module("alphafold3.data.pipeline")
  msa_config = _import_module("alphafold3.data.msa_config")
  model_config = _import_module("alphafold3.model.model_config")
  structure = _import_module("alphafold3.structure")
  mmcif = _import_module("alphafold3.structure.mmcif")
  chemical_components = _import_module("alphafold3.constants.chemical_components")
  build_data = _import_module("alphafold3.build_data")

  print("\nJSON constants:")
  if folding_input is not None:
    print(f"JSON_DIALECT: {getattr(folding_input, 'JSON_DIALECT', '<missing>')}")
    print(f"JSON_VERSION: {getattr(folding_input, 'JSON_VERSION', '<missing>')}")
    print(f"JSON_VERSIONS: {getattr(folding_input, 'JSON_VERSIONS', '<missing>')}")

  print("\nGenerated resource checks:")
  for resource_name in ("ccd.pickle", "chemical_component_sets.pickle"):
    exists = _resource_exists("alphafold3.constants.converters", resource_name)
    if exists is not None:
      print(f"RESOURCE alphafold3.constants.converters/{resource_name}: {'present' if exists else 'missing'}")

  print("\nSelected signatures:")
  if folding_input is not None:
    _signature("folding_input.Input.from_json", folding_input.Input.from_json)
    _signature("folding_input.Input.to_json", folding_input.Input.to_json)
    _signature("folding_input.Input.sanitised_name", folding_input.Input.sanitised_name)
  if data_pipeline is not None:
    _signature("pipeline.DataPipelineConfig", data_pipeline.DataPipelineConfig)
    _signature("pipeline.DataPipeline", data_pipeline.DataPipeline)
    _signature("pipeline.DataPipeline.process", data_pipeline.DataPipeline.process)
  if msa_config is not None:
    for name in ("RunConfig", "TemplatesConfig"):
      if hasattr(msa_config, name):
        _signature(f"msa_config.{name}", getattr(msa_config, name))
  if model_config is not None and hasattr(model_config, "GlobalConfig"):
    _signature("model_config.GlobalConfig", model_config.GlobalConfig)
  if chemical_components is not None and hasattr(chemical_components, "Ccd"):
    _signature("chemical_components.Ccd", chemical_components.Ccd)
  if build_data is not None and hasattr(build_data, "build_data"):
    _signature("build_data.build_data", build_data.build_data)

  run_alphafold = _import_module("run_alphafold")
  if run_alphafold is not None:
    for label in (
        "make_model_config",
        "process_fold_input",
        "ModelRunner",
        "ModelRunner.run_inference",
        "ModelRunner.extract_inference_results",
        "ModelRunner.extract_embeddings",
    ):
      obj = run_alphafold
      try:
        for part in label.split("."):
          obj = getattr(obj, part)
      except AttributeError:
        print(f"SIGNATURE run_alphafold.{label}: missing")
        continue
      _signature(f"run_alphafold.{label}", obj)
  else:
    print(
        "NOTE: run_alphafold is not importable as a module. This is expected "
        "when the runner script is not on PYTHONPATH."
    )

  if structure is not None:
    for name in ("from_mmcif", "from_sequences_and_bonds"):
      if hasattr(structure, name):
        _signature(f"structure.{name}", getattr(structure, name))
  if mmcif is not None:
    for name in (
        "from_string",
        "parse_multi_data_cif",
        "int_id_to_str_id",
        "str_id_to_int_id",
        "get_bond_atom_indices",
        "get_or_infer_type_symbol",
    ):
      if hasattr(mmcif, name):
        _signature(f"mmcif.{name}", getattr(mmcif, name))

  if check_ccd_load:
    print("\nCCD load check:")
    if chemical_components is None:
      print("CCD load skipped: chemical_components import failed")
    else:
      try:
        ccd = chemical_components.Ccd()
      except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"chemical_components.Ccd(): FAILED: {type(exc).__name__}: {exc}")
      else:
        print(f"chemical_components.Ccd(): ok, entries={len(ccd)}")

  if alphafold3 is None or folding_input is None:
    return 1
  return 0


def main() -> int:
  parser = argparse.ArgumentParser(
      description=(
          "Inspect an installed AlphaFold 3 Python package without running "
          "the data pipeline or model inference."
      )
  )
  parser.add_argument(
      "--check-ccd-load",
      action="store_true",
      help=(
          "Attempt chemical_components.Ccd() after checking resource presence. "
          "This still avoids model inference, but can fail if generated CCD "
          "pickles are missing."
      ),
  )
  args = parser.parse_args()
  return inspect_package(check_ccd_load=args.check_ccd_load)


if __name__ == "__main__":
  raise SystemExit(main())
