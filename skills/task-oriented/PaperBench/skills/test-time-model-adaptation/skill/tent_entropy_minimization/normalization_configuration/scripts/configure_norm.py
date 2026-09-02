#!/usr/bin/env python3
"""Configure portable model inventories for Tent normalization adaptation."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

NORMALIZATION_TYPES = {"BatchNorm", "BatchNorm1d", "BatchNorm2d", "BatchNorm3d"}


def configure_inventory(inventory: dict, target_batch_stats: bool = True) -> dict:
    configured = deepcopy(inventory)
    trainable = []
    all_params = []
    norm_count = 0
    for module in configured.get("modules", []):
        params = module.get("parameters", {})
        for param_name in params:
            full_name = f"{module.get('name', '')}.{param_name}".strip(".")
            all_params.append(full_name)
            params[param_name]["requires_grad"] = False
        if module.get("type") in NORMALIZATION_TYPES:
            norm_count += 1
            module["mode"] = "train"
            if target_batch_stats:
                module["track_running_stats"] = False
                module["running_mean"] = None
                module["running_var"] = None
            for param_name in ("weight", "bias"):
                if param_name in params:
                    params[param_name]["requires_grad"] = True
                    trainable.append(f"{module.get('name', '')}.{param_name}".strip("."))
    errors = []
    if norm_count == 0:
        errors.append("no_normalization_layers")
    if not trainable:
        errors.append("no_trainable_affine_parameters")
    if trainable and len(trainable) == len(all_params):
        errors.append("all_parameters_trainable")
    configured["model_mode"] = "train"
    return {"ok": not errors, "configured_inventory": configured, "trainable_parameters": trainable, "errors": errors}


def self_test() -> None:
    inventory = {"modules": [
        {"name": "bn", "type": "BatchNorm2d", "parameters": {"weight": {}, "bias": {}}},
        {"name": "head", "type": "Linear", "parameters": {"weight": {}, "bias": {}}},
    ]}
    report = configure_inventory(inventory)
    assert report["ok"] is True
    assert report["trainable_parameters"] == ["bn.weight", "bn.bias"]
    modules = report["configured_inventory"]["modules"]
    assert modules[0]["track_running_stats"] is False
    assert modules[1]["parameters"]["weight"]["requires_grad"] is False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", nargs="?", help="Path to inventory JSON.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"ok": True, "self_test": True}))
        return 0
    if not args.inventory:
        raise SystemExit("inventory path is required unless --self-test is used")
    report = configure_inventory(json.loads(Path(args.inventory).read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
