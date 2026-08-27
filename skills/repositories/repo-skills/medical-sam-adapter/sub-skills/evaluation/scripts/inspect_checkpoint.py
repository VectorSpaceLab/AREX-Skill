#!/usr/bin/env python3
"""Read-only, bounded inspection of a PyTorch checkpoint.

The helper never imports repository modules, constructs a model, changes the
checkpoint, or creates an output file.  It loads only after the caller supplies
``--checkpoint`` and prefers PyTorch's safe ``weights_only=True`` loader.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class CheckpointDiagnostic(Exception):
    """An expected, user-actionable checkpoint diagnostic."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect PyTorch checkpoint metadata and bounded state-dict keys "
            "without constructing a model or writing output."
        )
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Path to the checkpoint to inspect; no file is read when omitted.",
    )
    parser.add_argument(
        "--max-keys",
        type=int,
        default=20,
        help="Maximum state-dict keys to print (default: 20).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON diagnostic instead of human-readable text.",
    )
    return parser.parse_args()


def safe_scalar(value: Any) -> Any:
    """Return only small, non-executable metadata values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)) and len(value) <= 16:
        if all(
            isinstance(item, (str, int, float, bool)) or item is None
            for item in value
        ):
            return list(value)
    return {"type": type(value).__name__}


def load_weights_only(path: Path) -> Any:
    """Load on CPU only when this PyTorch exposes ``weights_only``."""
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment diagnostic
        raise CheckpointDiagnostic(f"cannot import PyTorch: {exc}") from exc

    try:
        parameters = inspect.signature(torch.load).parameters
    except (TypeError, ValueError) as exc:
        raise CheckpointDiagnostic(
            "cannot inspect torch.load; refusing an unverified legacy loader"
        ) from exc

    if "weights_only" not in parameters:
        raise CheckpointDiagnostic(
            "installed PyTorch has no weights_only=True support; refusing legacy "
            "pickle loading. Use a newer compatible PyTorch to inspect this file."
        )

    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise CheckpointDiagnostic(
            "weights-only torch.load failed "
            f"({type(exc).__name__}): {exc}"
        ) from exc


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return _is_number(value) and math.isfinite(float(value))


def _tensor_mapping(value: Any) -> tuple[bool, str | None]:
    """Validate the part of a state dict that val.py will strictly load."""
    if not isinstance(value, Mapping):
        return False, f"state_dict is not a mapping; got {type(value).__name__}"
    if not value:
        return False, "state_dict is empty"
    for key, tensor in value.items():
        if not isinstance(key, str):
            return False, "state_dict contains non-string parameter keys"
        try:
            import torch

            is_tensor = isinstance(tensor, torch.Tensor)
        except Exception as exc:  # pragma: no cover - import diagnostic
            return False, f"cannot validate state_dict tensor values: {exc}"
        if not is_tensor:
            return False, (
                f"state_dict value for {key!r} is not a tensor "
                f"(got {type(tensor).__name__})"
            )
    return True, None


def inspect_checkpoint(path: Path, max_keys: int) -> tuple[int, dict[str, Any]]:
    if not path.exists():
        return 2, {"status": "error", "diagnostic": f"checkpoint does not exist: {path}"}
    if not path.is_file():
        return 2, {
            "status": "error",
            "diagnostic": f"checkpoint is not a regular file: {path}",
        }
    if max_keys < 0:
        return 2, {"status": "error", "diagnostic": "--max-keys must be non-negative"}

    try:
        loaded = load_weights_only(path)
    except CheckpointDiagnostic as exc:
        return 3, {"status": "error", "diagnostic": str(exc)}

    if not isinstance(loaded, Mapping):
        return 4, {
            "status": "error",
            "diagnostic": (
                "checkpoint did not deserialize to a mapping; "
                f"got {type(loaded).__name__}"
            ),
        }

    result: dict[str, Any] = {
        "status": "ok",
        "path_basename": path.name,
        "top_level_keys": [str(key) for key in loaded.keys()],
        "metadata": {},
        "schema_warnings": [],
    }
    for key in ("epoch", "model", "best_tol"):
        if key in loaded:
            result["metadata"][key] = safe_scalar(loaded[key])

    state_dict = loaded.get("state_dict")
    if state_dict is None:
        # A raw tensor mapping is useful to identify, but is not accepted by
        # val.py, which directly indexes the wrapper's state_dict key.
        raw_ok, _ = _tensor_mapping(loaded) if loaded else (False, None)
        if raw_ok:
            result.update(
                {
                    "state_dict_kind": "raw_tensor_mapping",
                    "state_dict_key_count": len(loaded),
                    "state_dict_keys": list(loaded.keys())[:max_keys],
                    "diagnostic": (
                        "raw tensor state dict detected; val.py requires a "
                        "wrapper with epoch, best_tol, and state_dict"
                    ),
                }
            )
            return 5, result
        result["diagnostic"] = "missing state_dict mapping required by val.py"
        return 5, result

    valid_state, state_error = _tensor_mapping(state_dict)
    if not valid_state:
        result["diagnostic"] = state_error or "malformed state_dict"
        if isinstance(state_dict, Mapping):
            result["state_dict_key_count"] = len(state_dict)
        return 5, result

    keys = list(state_dict.keys())
    module_count = sum(key.startswith("module.") for key in keys)
    if module_count == len(keys):
        prefix_mode = "module-prefixed"
    elif module_count == 0:
        prefix_mode = "unprefixed"
    else:
        prefix_mode = "mixed"

    result.update(
        {
            "state_dict_kind": "wrapper_state_dict",
            "state_dict_key_count": len(keys),
            "module_prefix_key_count": module_count,
            "unprefixed_key_count": len(keys) - module_count,
            "prefix_mode": prefix_mode,
            "state_dict_keys": keys[:max_keys],
        }
    )

    required = {"epoch", "best_tol", "state_dict"}
    missing = sorted(required.difference(loaded.keys()))
    # state_dict was present above, but retaining this check keeps the required
    # schema explicit if this function is changed later.
    if missing:
        result["diagnostic"] = "wrapper metadata missing: " + ", ".join(missing)
        return 5, result
    if not isinstance(loaded["epoch"], int) or isinstance(loaded["epoch"], bool):
        result["diagnostic"] = "epoch must be an integer"
        return 5, result
    if not _is_finite_number(loaded["best_tol"]):
        result["diagnostic"] = "best_tol must be a finite number"
        return 5, result

    # These fields are emitted by train.py, but val.py does not index them.
    # Missing fields are therefore warnings rather than blockers; malformed
    # present fields are still reported because they contradict the saver
    # schema and are often evidence of the wrong checkpoint type.
    if "model" in loaded and not isinstance(loaded["model"], str):
        return 5, {**result, "diagnostic": "model must be a string when present"}
    if "optimizer" in loaded and not isinstance(loaded["optimizer"], Mapping):
        return 5, {**result, "diagnostic": "optimizer must be a mapping when present"}
    path_helper = loaded.get("path_helper")
    if path_helper is not None and not isinstance(path_helper, Mapping):
        return 5, {**result, "diagnostic": "path_helper must be a mapping when present"}

    for optional in ("model", "optimizer", "path_helper"):
        if optional not in loaded:
            result["schema_warnings"].append(
                f"optional training field {optional!r} is absent; val.py does not index it"
            )

    if prefix_mode == "mixed":
        result["schema_warnings"].append(
            "state_dict mixes module.-prefixed and unprefixed keys; strict loading is unlikely to work"
        )
        result["diagnostic"] = (
            "malformed state_dict namespace: keys mix module.-prefixed and "
            "unprefixed names"
        )
        return 5, result
    result["diagnostic"] = (
        "valid-looking val.py wrapper; strict model compatibility and tensor "
        "shapes still require the selected net/encoder"
    )
    return 0, result


def emit(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return
    print(f"status: {result.get('status', 'error')}")
    if "path_basename" in result:
        print(f"file: {result['path_basename']}")
    if "top_level_keys" in result:
        print("top-level keys: " + ", ".join(result["top_level_keys"]))
    for key, value in result.get("metadata", {}).items():
        print(f"metadata.{key}: {value}")
    for key in (
        "state_dict_kind",
        "state_dict_key_count",
        "module_prefix_key_count",
        "unprefixed_key_count",
        "prefix_mode",
    ):
        if key in result:
            print(f"{key}: {result[key]}")
    for warning in result.get("schema_warnings", []):
        print("warning: " + warning)
    if "state_dict_keys" in result:
        print("state-dict keys:")
        for key in result["state_dict_keys"]:
            print(f"  {key}")
    print("diagnostic: " + str(result.get("diagnostic", "unknown error")))


def main() -> int:
    args = parse_args()
    if args.checkpoint is None:
        result = {
            "status": "error",
            "diagnostic": "provide --checkpoint PATH; no checkpoint was inspected",
        }
        emit(result, args.json)
        return 2

    code, result = inspect_checkpoint(args.checkpoint, args.max_keys)
    if code != 0:
        result["status"] = "error"
    emit(result, args.json)
    return code


if __name__ == "__main__":
    sys.exit(main())
