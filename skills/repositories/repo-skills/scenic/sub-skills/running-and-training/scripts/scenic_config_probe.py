#!/usr/bin/env python3
"""Safely inspect a Scenic Python config without launching training.

The helper imports a user-supplied config module, calls get_config(), prints
important top-level keys, and checks runner/model/dataset/trainer/training
fields used by Scenic's generic app and main flow. It intentionally does not
import Scenic trainers, build datasets, initialize models, or call any training
loop.

Config files are Python code. Only run this helper on trusted configs.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import pathlib
import sys
import traceback
from typing import Any, Iterable

MISSING = object()
KNOWN_CENTRAL_TRAINERS = {"classification_trainer", "transfer_trainer"}


def parse_value(text: str) -> Any:
  """Parse a command-line scalar, preserving plain strings."""
  try:
    return ast.literal_eval(text)
  except Exception:  # pylint: disable=broad-except
    lowered = text.lower()
    if lowered == "true":
      return True
    if lowered == "false":
      return False
    if lowered in {"none", "null"}:
      return None
    return text


def parse_kwarg(text: str) -> tuple[str, Any]:
  if "=" not in text:
    raise argparse.ArgumentTypeError(
        f"expected KEY=VALUE for --config-kw, got {text!r}"
    )
  key, value = text.split("=", 1)
  key = key.strip()
  if not key:
    raise argparse.ArgumentTypeError("empty KEY in --config-kw")
  return key, parse_value(value)


def has_key(obj: Any, key: str) -> bool:
  try:
    return key in obj
  except Exception:  # pylint: disable=broad-except
    return hasattr(obj, key)


def get_key(obj: Any, key: str, default: Any = MISSING) -> Any:
  if obj is MISSING:
    return default
  try:
    if key in obj:
      return obj[key]
  except Exception:  # pylint: disable=broad-except
    pass
  try:
    return getattr(obj, key)
  except Exception:  # pylint: disable=broad-except
    return default


def get_path(obj: Any, dotted_path: str, default: Any = MISSING) -> Any:
  current = obj
  for part in dotted_path.split("."):
    current = get_key(current, part, MISSING)
    if current is MISSING:
      return default
  return current


def is_present_non_none(value: Any) -> bool:
  return value is not MISSING and value is not None


def sorted_keys(obj: Any) -> list[str]:
  try:
    return sorted(str(k) for k in obj.keys())
  except Exception:  # pylint: disable=broad-except
    return []


def compact_value(value: Any, max_len: int = 100) -> str:
  if value is MISSING:
    return "<missing>"
  if value is None:
    return "None"
  keys = sorted_keys(value)
  if keys:
    shown = ", ".join(keys[:8])
    if len(keys) > 8:
      shown += ", ..."
    return f"<{type(value).__name__} {len(keys)} keys: {shown}>"
  text = repr(value)
  if len(text) > max_len:
    text = text[: max_len - 3] + "..."
  return text


def load_config_module(path: pathlib.Path) -> Any:
  module_name = f"_scenic_config_probe_{path.stem}_{abs(hash(path))}"
  spec = importlib.util.spec_from_file_location(module_name, str(path))
  if spec is None or spec.loader is None:
    raise RuntimeError(f"could not create import spec for {path}")
  module = importlib.util.module_from_spec(spec)
  sys.path.insert(0, str(path.parent))
  try:
    spec.loader.exec_module(module)  # type: ignore[union-attr]
  finally:
    try:
      sys.path.remove(str(path.parent))
    except ValueError:
      pass
  return module


def numeric_positive(value: Any) -> bool:
  return isinstance(value, (int, float)) and value > 0


def check_config(config: Any, *, dataset_service_address: str | None) -> tuple[list[str], list[str]]:
  errors: list[str] = []
  warnings: list[str] = []

  def require(path: str, why: str) -> Any:
    value = get_path(config, path, MISSING)
    if value is MISSING:
      errors.append(f"missing `{path}`: {why}")
    return value

  rng_seed = require("rng_seed", "scenic.app builds jax.random.PRNGKey(config.rng_seed)")
  if rng_seed is not MISSING and not isinstance(rng_seed, int):
    warnings.append(f"`rng_seed` is {compact_value(rng_seed)}; Scenic expects an integer seed")

  dataset_name = require("dataset_name", "scenic.main resolves the dataset from config.dataset_name")
  model_name = require("model_name", "scenic.main resolves the model class from config.model_name")
  trainer_name = require("trainer_name", "scenic.main resolves the trainer from config.trainer_name")

  if is_present_non_none(trainer_name) and trainer_name not in KNOWN_CENTRAL_TRAINERS:
    warnings.append(
        "`trainer_name` is not one of the central generic trainers "
        f"{sorted(KNOWN_CENTRAL_TRAINERS)}; use the matching project entry point "
        "or register/choose a central trainer before running scenic.main"
    )
  if trainer_name == "transfer_trainer":
    warnings.append(
        "`transfer_trainer` can require optional BigVision / TensorFlow Addons / "
        "Keras-compatible dependencies; validate trainer imports before launch"
    )

  batch_size = require("batch_size", "train_utils.get_dataset shards batches across JAX devices")
  if batch_size is not MISSING and not numeric_positive(batch_size):
    errors.append(f"`batch_size` should be a positive number, got {compact_value(batch_size)}")
  eval_batch_size = get_path(config, "eval_batch_size", MISSING)
  if eval_batch_size is not MISSING and eval_batch_size is not None and not numeric_positive(eval_batch_size):
    errors.append(f"`eval_batch_size` should be positive when set, got {compact_value(eval_batch_size)}")

  require("data_dtype_str", "dataset builders receive dtype_str=config.data_dtype_str")
  if get_path(config, "dataset_configs", MISSING) is MISSING:
    warnings.append("`dataset_configs` is absent; many Scenic dataset builders expect a ConfigDict or dict")

  lr_configs = require("lr_configs", "lr_schedules.get_learning_rate_fn(config) reads config.lr_configs")
  if lr_configs is not MISSING:
    base_lr = get_path(config, "lr_configs.base_learning_rate", MISSING)
    if base_lr is MISSING:
      errors.append("missing `lr_configs.base_learning_rate`: required by get_learning_rate_fn")
    elif base_lr is None:
      warnings.append("`lr_configs.base_learning_rate` is None; this is only safe for specialized frozen-parameter flows")
    schedule = get_path(config, "lr_configs.learning_rate_schedule", MISSING)
    factors = get_path(config, "lr_configs.factors", MISSING)
    if schedule is not MISSING and schedule != "compound":
      warnings.append(f"`lr_configs.learning_rate_schedule` is {schedule!r}; central lr_fn_dict only contains 'compound'")
    if schedule == "compound" and factors is MISSING:
      errors.append("compound LR schedule requires `lr_configs.factors`")

  top_optimizer = get_path(config, "optimizer", MISSING)
  nested_optimizer = get_path(config, "optimizer_configs.optimizer", MISSING)
  if is_present_non_none(top_optimizer) and is_present_non_none(nested_optimizer):
    errors.append("both `optimizer` and `optimizer_configs.optimizer` are set; Scenic requires only one style")
  elif not is_present_non_none(top_optimizer) and not is_present_non_none(nested_optimizer):
    errors.append("missing optimizer declaration: set top-level `optimizer` or `optimizer_configs.optimizer`")

  num_steps = get_path(config, "num_training_steps", MISSING)
  num_epochs = get_path(config, "num_training_epochs", MISSING)
  has_steps = is_present_non_none(num_steps)
  has_epochs = is_present_non_none(num_epochs)
  if has_steps and has_epochs:
    errors.append("set exactly one of `num_training_steps` or `num_training_epochs`, not both")
  elif not has_steps and not has_epochs:
    errors.append("missing training length: set `num_training_steps` or `num_training_epochs`")
  if has_steps and get_path(config, "log_eval_steps", MISSING) is MISSING:
    warnings.append(
        "`num_training_steps` is set but `log_eval_steps` is absent; generic trainers "
        "may need dataset metadata to infer eval/log cadence"
    )

  for key in ("checkpoint", "debug_train", "debug_eval"):
    value = get_path(config, key, MISSING)
    if value is MISSING:
      errors.append(f"missing `{key}`: generic trainers access this field")
    elif not isinstance(value, bool) and value is not None:
      warnings.append(f"`{key}` is {compact_value(value)}; expected bool-like value")

  if get_path(config, "xprof", MISSING) is MISSING:
    warnings.append("`xprof` is absent; generic trainers default profiling on for the lead host")

  shuffle_seed = get_path(config, "shuffle_seed", MISSING)
  if dataset_service_address and shuffle_seed is not MISSING and shuffle_seed is not None:
    errors.append(
        "dataset service address was supplied while `shuffle_seed` is not None; "
        "Scenic rejects this combination to avoid identical worker shuffles"
    )

  if is_present_non_none(batch_size) and isinstance(batch_size, (int, float)) and batch_size >= 1024:
    warnings.append(f"large `batch_size` ({batch_size}) suggests an expensive or multi-device run")
  if is_present_non_none(num_epochs) and isinstance(num_epochs, (int, float)) and num_epochs > 20:
    warnings.append(f"large `num_training_epochs` ({num_epochs}) suggests a full training run")
  if get_path(config, "init_from.checkpoint_path", MISSING) is not MISSING:
    warnings.append("`init_from.checkpoint_path` is set; verify checkpoint availability and compatibility before launch")

  if model_name is not MISSING and isinstance(model_name, str) and "vit" in model_name.lower():
    if get_path(config, "model", MISSING) is MISSING:
      warnings.append("ViT-like model name without a nested `model` config may be incomplete")
  if dataset_name is not MISSING and isinstance(dataset_name, str) and dataset_name.lower() in {"imagenet", "bit"}:
    warnings.append("ImageNet/BigTransfer-style datasets require external data availability; this probe does not check data")

  return errors, warnings


def print_list(title: str, values: Iterable[str]) -> None:
  values = list(values)
  if not values:
    print(f"{title}: none")
    return
  print(f"{title}:")
  for value in values:
    print(f"  - {value}")


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
      description=(
          "Inspect a Scenic ml_collections Python config, print important keys, "
          "and report launch-risk fields without starting training."
      )
  )
  parser.add_argument("config", help="Path to a trusted Python config file")
  parser.add_argument(
      "--config-arg",
      action="append",
      default=[],
      help="Positional argument to pass to get_config(); may be repeated",
  )
  parser.add_argument(
      "--config-kw",
      action="append",
      type=parse_kwarg,
      default=[],
      metavar="KEY=VALUE",
      help="Keyword argument to pass to get_config(); may be repeated",
  )
  parser.add_argument(
      "--dataset-service-address",
      default=None,
      help="Optional address to check against config.shuffle_seed; no service is contacted",
  )
  parser.add_argument(
      "--warnings-as-errors",
      action="store_true",
      help="Exit non-zero when warnings are present even if no errors are found",
  )
  parser.add_argument(
      "--json",
      action="store_true",
      help="Emit a JSON summary in addition to human-readable output",
  )
  args = parser.parse_args(argv)

  config_path = pathlib.Path(args.config).expanduser().resolve()
  print("Scenic config probe: no training will be launched")
  print(f"config: {config_path}")
  if not config_path.exists():
    print(f"ERROR: config file does not exist: {config_path}", file=sys.stderr)
    return 2
  if not config_path.is_file():
    print(f"ERROR: config path is not a file: {config_path}", file=sys.stderr)
    return 2

  try:
    module = load_config_module(config_path)
  except Exception as exc:  # pylint: disable=broad-except
    print(f"ERROR: failed to import config module: {exc}", file=sys.stderr)
    traceback.print_exc()
    return 2

  get_config = getattr(module, "get_config", None)
  if not callable(get_config):
    print("ERROR: config module does not define callable get_config", file=sys.stderr)
    return 2

  positional_args = [parse_value(value) for value in args.config_arg]
  keyword_args = {key: value for key, value in args.config_kw}
  try:
    config = get_config(*positional_args, **keyword_args)
  except Exception as exc:  # pylint: disable=broad-except
    print(f"ERROR: get_config call failed: {exc}", file=sys.stderr)
    traceback.print_exc()
    return 2

  top_keys = sorted_keys(config)
  print(f"top-level keys ({len(top_keys)}): {', '.join(top_keys) if top_keys else '<none>'}")
  print("important values:")
  important_paths = [
      "rng_seed",
      "dataset_name",
      "model_name",
      "trainer_name",
      "batch_size",
      "eval_batch_size",
      "data_dtype_str",
      "num_training_steps",
      "num_training_epochs",
      "lr_configs",
      "optimizer",
      "optimizer_configs.optimizer",
      "checkpoint",
      "debug_train",
      "debug_eval",
      "shuffle_seed",
      "init_from.checkpoint_path",
  ]
  for path in important_paths:
    print(f"  {path}: {compact_value(get_path(config, path, MISSING))}")

  errors, warnings = check_config(config, dataset_service_address=args.dataset_service_address)
  print_list("ERRORS", errors)
  print_list("WARNINGS", warnings)

  if args.json:
    summary = {
        "config": str(config_path),
        "top_level_keys": top_keys,
        "important_values": {
            path: compact_value(get_path(config, path, MISSING))
            for path in important_paths
        },
        "errors": errors,
        "warnings": warnings,
        "training_launched": False,
    }
    print("JSON_SUMMARY:")
    print(json.dumps(summary, indent=2, sort_keys=True))

  if errors:
    print("result: NOT SAFE TO LAUNCH with generic scenic.main until errors are fixed")
    return 1
  if warnings:
    print("result: basic shape OK, but review warnings before launch")
    return 1 if args.warnings_as_errors else 0
  print("result: basic generic-runner config shape OK; data/model/backend are not proven")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
