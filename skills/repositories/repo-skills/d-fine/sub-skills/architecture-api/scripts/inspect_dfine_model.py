#!/usr/bin/env python3
"""Inspect a D-FINE checkout, YAML config, and optional model construction.

This helper is safe by default: it does not download weights, open datasets, or
run training. It adds the supplied repo root to sys.path, loads YAMLConfig,
disables HGNetv2 pretrained lookup unless --allow-pretrained is set, and prints
config/model facts useful for debugging registry and architecture issues.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    return repr(value)


def _short_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _advice(exc: BaseException) -> str:
    text = str(exc)
    if "not registered" in text or "registered" in text:
        return "Check the YAML type/component name and make sure the module defining that class is imported and decorated with @register()."
    if "Missing inject config" in text or "Missing inject" in text:
        return "Check __inject__ fields: parent YAML entries must point to existing registered config blocks or inline dictionaries with type."
    if "No such file" in text or "weight" in text or "pretrained" in text:
        return "Retry without --allow-pretrained so HGNetv2 pretrained lookup is disabled, or provide the expected backbone weights."
    if "size mismatch" in text or "shape" in text or "channels" in text:
        return "Check num_classes, feature channels, feat_strides, num_levels, reg_max, and checkpoint/config compatibility."
    return "Inspect the traceback with --traceback and compare the config against a stock D-FINE config."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a D-FINE config and optionally build the model without training."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a D-FINE checkout; defaults to the current working directory.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="D-FINE YAML config path, relative to repo root or absolute.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device for optional dummy forward, for example cpu or cuda:0.",
    )
    parser.add_argument(
        "--allow-pretrained",
        action="store_true",
        help="Do not force HGNetv2.pretrained=False before model construction.",
    )
    parser.add_argument(
        "--build-model",
        action="store_true",
        help="Instantiate cfg.model and cfg.postprocessor after loading YAML.",
    )
    parser.add_argument(
        "--dummy-forward",
        action="store_true",
        help="Run a tiny dummy forward after --build-model. Can be slow on CPU.",
    )
    parser.add_argument("--dummy-size", type=int, default=320, help="Square input size for dummy forward.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--traceback", action="store_true", help="Print traceback on failure.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    result: Dict[str, Any] = {
        "repo_root_ok": repo_root.exists(),
        "config_ok": config_path.exists(),
        "config": args.config,
        "allow_pretrained": args.allow_pretrained,
        "build_model": args.build_model,
        "dummy_forward": args.dummy_forward,
        "warnings": [],
    }

    if not repo_root.exists():
        print(f"repo root does not exist: {args.repo_root}", file=sys.stderr)
        return 2
    if not config_path.exists():
        print(f"config does not exist: {args.config}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(repo_root))

    try:
        import torch
        from src.core import YAMLConfig

        cfg = YAMLConfig(str(config_path))
        result["task"] = cfg.yaml_cfg.get("task")
        result["model_name"] = cfg.yaml_cfg.get("model")
        result["criterion_name"] = cfg.yaml_cfg.get("criterion")
        result["postprocessor_name"] = cfg.yaml_cfg.get("postprocessor")
        result["num_classes"] = cfg.yaml_cfg.get("num_classes")
        result["eval_spatial_size"] = cfg.yaml_cfg.get("eval_spatial_size")
        result["top_level_components"] = {
            key: cfg.yaml_cfg.get(key)
            for key in ["DFINE", "HGNetv2", "HybridEncoder", "DFINETransformer"]
            if key in cfg.yaml_cfg
        }

        if "HGNetv2" in cfg.yaml_cfg and not args.allow_pretrained:
            cfg.yaml_cfg["HGNetv2"]["pretrained"] = False
            result["warnings"].append("HGNetv2.pretrained forced to False for safe inspection")

        if args.build_model or args.dummy_forward:
            model = cfg.model
            postprocessor = cfg.postprocessor if "postprocessor" in cfg.yaml_cfg else None
            result["model_class"] = type(model).__name__
            result["postprocessor_class"] = type(postprocessor).__name__ if postprocessor else None
            result["parameter_count"] = int(sum(p.numel() for p in model.parameters()))
            result["trainable_parameter_count"] = int(
                sum(p.numel() for p in model.parameters() if p.requires_grad)
            )
            result["component_classes"] = {
                "backbone": type(getattr(model, "backbone", None)).__name__,
                "encoder": type(getattr(model, "encoder", None)).__name__,
                "decoder": type(getattr(model, "decoder", None)).__name__,
            }

        if args.dummy_forward:
            if not (args.build_model or "model" in locals()):
                model = cfg.model
            model.eval().to(args.device)
            size = int(args.dummy_size)
            with torch.no_grad():
                dummy = torch.rand(1, 3, size, size, device=args.device)
                output = model(dummy)
            result["dummy_forward_output_type"] = type(output).__name__
            if isinstance(output, dict):
                result["dummy_forward_keys"] = sorted(output.keys())
            elif isinstance(output, (list, tuple)):
                result["dummy_forward_length"] = len(output)

    except Exception as exc:  # noqa: BLE001 - diagnostic helper should explain broad failures
        result["error"] = _short_error(exc)
        result["advice"] = _advice(exc)
        if args.json:
            print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
        else:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            print(f"Advice: {result['advice']}", file=sys.stderr)
        if args.traceback:
            traceback.print_exc()
        return 1

    if args.json:
        print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
    else:
        for key in [
            "task",
            "model_name",
            "criterion_name",
            "postprocessor_name",
            "num_classes",
            "eval_spatial_size",
            "model_class",
            "postprocessor_class",
            "parameter_count",
            "trainable_parameter_count",
            "component_classes",
            "dummy_forward_output_type",
            "dummy_forward_keys",
        ]:
            if key in result:
                print(f"{key}: {result[key]}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
