#!/usr/bin/env python3
"""Describe an Acme replay data structure and recommend an adder family.

The input is a JSON file with observation/action/reward/discount/extras leaves.
Leaves can be written as objects with shape/dtype keys, nested dictionaries, or
nested lists. This helper performs structural validation only; it does not import
Acme, Reverb, TensorFlow, or JAX.

Example:
  python describe_replay_structure.py replay_description.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable

_REQUIRED_TOP_LEVEL = ("observation", "action", "reward", "discount")
_LEAF_KEYS = {"shape", "dtype"}
_SEQUENCE_HINTS = ("sequence_length", "period", "burn_in", "unroll_length")


class StructureError(ValueError):
  """Raised when a replay description is malformed."""


def _is_leaf(value: Any) -> bool:
  return isinstance(value, dict) and bool(_LEAF_KEYS & set(value))


def _format_path(path: Iterable[str]) -> str:
  parts = list(path)
  return ".".join(parts) if parts else "<root>"


def _validate_shape(shape: Any, path: Iterable[str]) -> None:
  if shape is None:
    return
  if not isinstance(shape, list):
    raise StructureError(f"{_format_path(path)}.shape must be a list")
  for index, dimension in enumerate(shape):
    if not (isinstance(dimension, int) or dimension is None):
      raise StructureError(
          f"{_format_path(path)}.shape[{index}] must be an integer or null")
    if isinstance(dimension, int) and dimension < 0:
      raise StructureError(
          f"{_format_path(path)}.shape[{index}] must be non-negative")


def _validate_leaf(value: dict[str, Any], path: Iterable[str]) -> None:
  if "dtype" not in value:
    raise StructureError(f"{_format_path(path)} leaf is missing dtype")
  if not isinstance(value["dtype"], str) or not value["dtype"].strip():
    raise StructureError(f"{_format_path(path)}.dtype must be a non-empty string")
  if "shape" in value:
    _validate_shape(value["shape"], path)


def _walk(value: Any, path: tuple[str, ...] = ()) -> list[tuple[str, dict[str, Any]]]:
  if _is_leaf(value):
    _validate_leaf(value, path)
    return [(_format_path(path), value)]

  if isinstance(value, dict):
    leaves: list[tuple[str, dict[str, Any]]] = []
    for key, child in value.items():
      if not isinstance(key, str) or not key:
        raise StructureError(f"{_format_path(path)} contains a non-string key")
      leaves.extend(_walk(child, (*path, key)))
    return leaves

  if isinstance(value, list):
    leaves = []
    for index, child in enumerate(value):
      leaves.extend(_walk(child, (*path, str(index))))
    return leaves

  raise StructureError(
      f"{_format_path(path)} must be a leaf object, nested object, or list")


def _count_leaves(value: Any) -> int:
  return len(_walk(value))


def _has_extras(description: dict[str, Any]) -> bool:
  extras = description.get("extras", ())
  if extras in (None, [], {}, ()):
    return False
  return _count_leaves(extras) > 0


def _as_bool(value: Any) -> bool:
  if isinstance(value, bool):
    return value
  if isinstance(value, str):
    return value.strip().lower() in {"1", "true", "yes", "y"}
  return bool(value)


def _learner_hints(description: dict[str, Any]) -> dict[str, Any]:
  learner = description.get("learner", {})
  if learner is None:
    return {}
  if not isinstance(learner, dict):
    raise StructureError("learner must be an object when provided")
  return learner


def _recommend(description: dict[str, Any]) -> tuple[str, list[str]]:
  learner = _learner_hints(description)
  reasons: list[str] = []

  if _as_bool(learner.get("custom_patterns")) or _as_bool(learner.get("multiple_tables")):
    reasons.append("learner hints request custom Reverb patterns or multiple tables")
    return "StructuredAdder", reasons

  if _as_bool(learner.get("full_episodes")) or _as_bool(learner.get("episode_level")):
    reasons.append("learner hints request complete episodes")
    return "EpisodeAdder", reasons

  if _as_bool(learner.get("recurrent")):
    reasons.append("learner is recurrent")
    return "SequenceAdder", reasons

  if any(key in learner for key in _SEQUENCE_HINTS):
    reasons.append("learner hints include sequence/unroll settings")
    return "SequenceAdder", reasons

  if _has_extras(description):
    reasons.append("extras are present; transitions are safe only if learner needs one extras tree per step")

  n_step = learner.get("n_step", description.get("n_step"))
  if n_step is not None:
    try:
      n_step_int = int(n_step)
    except (TypeError, ValueError) as exc:
      raise StructureError("n_step must be an integer when provided") from exc
    if n_step_int > 1:
      reasons.append(f"n_step={n_step_int} requests transition return accumulation")
    elif n_step_int < 1:
      raise StructureError("n_step must be >= 1")

  if not reasons:
    reasons.append("default feed-forward learner assumption")
  return "NStepTransitionAdder", reasons


def _print_summary(description: dict[str, Any]) -> None:
  print("Replay structure summary")
  print("========================")
  for key in (*_REQUIRED_TOP_LEVEL, "extras"):
    if key not in description:
      if key == "extras":
        print(f"{key}: <absent>")
      continue
    leaves = _walk(description[key], (key,))
    print(f"{key}: {len(leaves)} leaf/leaves")
    for path, leaf in leaves:
      shape = leaf.get("shape", "<unspecified>")
      dtype = leaf.get("dtype", "<missing>")
      print(f"  - {path}: shape={shape}, dtype={dtype}")

  family, reasons = _recommend(description)
  print()
  print(f"Recommended adder family: {family}")
  for reason in reasons:
    print(f"  - {reason}")

  learner = _learner_hints(description)
  if family == "SequenceAdder":
    sequence_length = learner.get("sequence_length", "<choose learner unroll length>")
    period = learner.get("period", "<choose overlap period>")
    print(f"Suggested sequence_length: {sequence_length}")
    print(f"Suggested period: {period}")
    if _has_extras(description):
      print("Note: include an extras_spec with the same nested structure as extras.")
  elif family == "NStepTransitionAdder":
    n_step = learner.get("n_step", description.get("n_step", 1))
    discount = learner.get("discount", description.get("discount_factor", "<agent discount>"))
    print(f"Suggested n_step: {n_step}")
    print(f"Suggested discount: {discount}")
  elif family == "EpisodeAdder":
    max_len = learner.get("max_sequence_length", "<max observations per episode>")
    print(f"Suggested max_sequence_length: {max_len}")
  else:
    print("Suggested next step: build create_step_spec(...) and structured_writer configs.")


def _load_description(path: str) -> dict[str, Any]:
  with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
  if not isinstance(data, dict):
    raise StructureError("top-level JSON value must be an object")
  missing = [key for key in _REQUIRED_TOP_LEVEL if key not in data]
  if missing:
    raise StructureError("missing required top-level key(s): " + ", ".join(missing))
  for key in _REQUIRED_TOP_LEVEL:
    _walk(data[key], (key,))
  if "extras" in data and data["extras"] not in (None, [], {}, ()):  # JSON never yields tuple.
    _walk(data["extras"], ("extras",))
  _learner_hints(data)
  return data


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("json_path", help="Path to a replay structure JSON file.")
  args = parser.parse_args(argv)

  try:
    description = _load_description(args.json_path)
    _print_summary(description)
  except (OSError, json.JSONDecodeError, StructureError) as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 2
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
