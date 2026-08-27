#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import importlib
import importlib.util
import inspect
import json
import sys
from typing import Any

LOSS_NAMES = (
    "A2CLoss",
    "ACTLoss",
    "BCLoss",
    "ClipPPOLoss",
    "CQLLoss",
    "CrossQLoss",
    "DDPGLoss",
    "DQNLoss",
    "DTLoss",
    "DiffusionBCLoss",
    "DiscreteCQLLoss",
    "DiscreteIQLLoss",
    "DiscreteSACLoss",
    "DistributionalDQNLoss",
    "DreamerActorLoss",
    "DreamerModelLoss",
    "DreamerV3ActorLoss",
    "DreamerV3ModelLoss",
    "DreamerV3ValueLoss",
    "DreamerValueLoss",
    "ExponentialQuadraticCost",
    "GAILLoss",
    "HardUpdate",
    "IQLLoss",
    "IPPOLoss",
    "KLPENPPOLoss",
    "MAPPOLoss",
    "OnlineDTLoss",
    "PPOLoss",
    "QMixerLoss",
    "REDQLoss",
    "ReinforceLoss",
    "RNDLoss",
    "SACLoss",
    "SoftUpdate",
    "TD3BCLoss",
    "TD3Loss",
    "TQCLoss",
    "ValueEstimators",
    "WorldModelLoss",
)

_HAS_TORCHRL = importlib.util.find_spec("torchrl") is not None


def _load_objectives() -> Any:
    if not _HAS_TORCHRL:
        raise RuntimeError(
            "Could not find the 'torchrl' package. Install TorchRL in the active "
            "Python environment, then rerun this helper."
        )
    try:
        return importlib.import_module("torchrl.objectives")
    except Exception as exc:  # pragma: no cover - message is for user diagnostics
        raise RuntimeError(
            "Found a torchrl package but failed to import torchrl.objectives: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


def _available_losses(objectives: Any) -> dict[str, Any]:
    return {name: getattr(objectives, name) for name in LOSS_NAMES if hasattr(objectives, name)}


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _default_key_object(cls: type[Any]) -> Any | None:
    default_keys = getattr(cls, "default_keys", None)
    if default_keys is None:
        accepted_keys = getattr(cls, "_AcceptedKeys", None)
        default_keys = accepted_keys
    if default_keys is None:
        return None
    try:
        return default_keys()
    except Exception as exc:  # pragma: no cover - defensive against custom classes
        return {"error": f"{type(exc).__name__}: {exc}"}


def _field_names(keys_obj: Any) -> list[str]:
    if keys_obj is None:
        return []
    if isinstance(keys_obj, dict):
        return sorted(keys_obj)
    if dataclasses.is_dataclass(keys_obj):
        return [field.name for field in dataclasses.fields(keys_obj)]
    fields = getattr(keys_obj, "_fields", None)
    if fields is not None:
        return list(fields)
    annotations = getattr(type(keys_obj), "__annotations__", {})
    return list(annotations)


def _default_key_map(cls: type[Any]) -> dict[str, Any] | None:
    keys_obj = _default_key_object(cls)
    if keys_obj is None:
        return None
    if isinstance(keys_obj, dict):
        return keys_obj
    names = _field_names(keys_obj)
    return {name: getattr(keys_obj, name) for name in names}


def _default_value_estimator(cls: type[Any]) -> str | None:
    estimator = getattr(cls, "default_value_estimator", None)
    if estimator is None:
        return None
    name = getattr(estimator, "name", None)
    return name if name is not None else repr(estimator)


def _describe_loss(name: str, cls: type[Any]) -> dict[str, Any]:
    try:
        signature = str(inspect.signature(cls))
    except Exception as exc:  # pragma: no cover - defensive against exotic callables
        signature = f"<unavailable: {type(exc).__name__}: {exc}>"
    default_keys = _default_key_map(cls)
    return {
        "loss": name,
        "signature": signature,
        "has_set_keys": callable(getattr(cls, "set_keys", None)),
        "accepted_keys": sorted(default_keys) if default_keys else [],
        "default_keys": _jsonable(default_keys),
        "default_value_estimator": _default_value_estimator(cls),
    }


def _print_human(info: dict[str, Any]) -> None:
    print(f"loss: {info['loss']}")
    print(f"signature: {info['signature']}")
    print(f"has_set_keys: {info['has_set_keys']}")
    print(f"default_value_estimator: {info['default_value_estimator']}")
    if info["default_keys"]:
        print("accepted/default keys:")
        for key in info["accepted_keys"]:
            print(f"  {key}: {info['default_keys'][key]!r}")
    else:
        print("accepted/default keys: <none exposed>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a TorchRL objective/updater class signature and configurable "
            "TensorDict keys without constructing networks or running training."
        )
    )
    parser.add_argument("--loss", help="Class name to inspect, e.g. ClipPPOLoss or SACLoss.")
    parser.add_argument("--list", action="store_true", help="List known inspectable class names.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        objectives = _load_objectives()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    available = _available_losses(objectives)
    if args.list:
        for name in sorted(available):
            print(name)
        return 0

    if not args.loss:
        parser.error("--loss is required unless --list is used")

    if args.loss not in available:
        known = ", ".join(sorted(available))
        print(
            f"error: unknown loss/updater class {args.loss!r}. Known names: {known}",
            file=sys.stderr,
        )
        return 2

    info = _describe_loss(args.loss, available[args.loss])
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        _print_human(info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
