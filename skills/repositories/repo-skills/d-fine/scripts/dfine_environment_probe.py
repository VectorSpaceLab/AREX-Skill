#!/usr/bin/env python3
"""Probe a D-FINE checkout and print a safe import/config/model smoke summary.

This helper is intentionally read-only. It verifies that the checkout can be
added to sys.path, that the expected core packages import, that YAMLConfig can
load a chosen config, and optionally that the smallest D-FINE model can be
constructed and run through a tiny dummy forward.
"""

from __future__ import annotations

import argparse
import json
import sys
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe a D-FINE checkout and config safely.")
    parser.add_argument("--repo-root", default=".", help="Path to a D-FINE checkout.")
    parser.add_argument("--config", required=True, help="D-FINE YAML config path.")
    parser.add_argument("--build-model", action="store_true", help="Instantiate cfg.model and cfg.postprocessor.")
    parser.add_argument("--dummy-forward", action="store_true", help="Run a tiny dummy forward after building the model.")
    parser.add_argument("--dummy-size", type=int, default=320, help="Square dummy input size.")
    parser.add_argument("--allow-pretrained", action="store_true", help="Keep HGNetv2 pretrained lookup enabled.")
    parser.add_argument("--device", default="cpu", help="Device for dummy forward.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of key/value lines.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    if not repo_root.exists():
        print(f"repo root does not exist: {repo_root}", file=sys.stderr)
        return 2
    if not config_path.exists():
        print(f"config does not exist: {config_path}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(repo_root))

    result: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "config": str(config_path),
        "warnings": [],
    }

    try:
        import torch
        import torchvision
        import yaml
        from src.core import YAMLConfig
        import src  # noqa: F401 - import side effects are part of the smoke

        result["python"] = sys.version.split()[0]
        result["torch"] = getattr(torch, "__version__", None)
        result["torchvision"] = getattr(torchvision, "__version__", None)
        result["yaml"] = getattr(yaml, "__version__", None)
        result["cuda_available"] = bool(torch.cuda.is_available())

        cfg = YAMLConfig(str(config_path))
        result["task"] = cfg.yaml_cfg.get("task")
        result["model"] = cfg.yaml_cfg.get("model")
        result["num_classes"] = cfg.yaml_cfg.get("num_classes")
        result["eval_spatial_size"] = cfg.yaml_cfg.get("eval_spatial_size")

        if "HGNetv2" in cfg.yaml_cfg and not args.allow_pretrained:
            cfg.yaml_cfg["HGNetv2"]["pretrained"] = False
            result["warnings"].append("HGNetv2.pretrained forced to False for safe inspection")

        if args.build_model or args.dummy_forward:
            model = cfg.model
            result["model_class"] = type(model).__name__
            result["parameter_count"] = int(sum(p.numel() for p in model.parameters()))
            result["trainable_parameter_count"] = int(
                sum(p.numel() for p in model.parameters() if p.requires_grad)
            )
            if "postprocessor" in cfg.yaml_cfg:
                result["postprocessor_class"] = type(cfg.postprocessor).__name__

        if args.dummy_forward:
            model = cfg.model.eval().to(args.device)
            with torch.no_grad():
                dummy = torch.rand(1, 3, int(args.dummy_size), int(args.dummy_size), device=args.device)
                output = model(dummy)
            result["dummy_forward_type"] = type(output).__name__
            if isinstance(output, dict):
                result["dummy_forward_keys"] = sorted(output.keys())
            elif isinstance(output, (list, tuple)):
                result["dummy_forward_len"] = len(output)

    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
        else:
            print(result["error"], file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
    else:
        for key in [
            "python",
            "torch",
            "torchvision",
            "yaml",
            "cuda_available",
            "task",
            "model",
            "num_classes",
            "eval_spatial_size",
            "model_class",
            "parameter_count",
            "postprocessor_class",
            "dummy_forward_type",
            "dummy_forward_keys",
        ]:
            if key in result:
                print(f"{key}: {result[key]}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
