#!/usr/bin/env python3
"""Inspect SSD300 construction, prior shape, and optional zero-forward shapes.

Run from a checkout or environment where the ssd.pytorch source modules are
importable. This helper does not download data or weights.
"""

from __future__ import annotations

import argparse
import importlib
import json
import traceback
from typing import Any


def shape_of(obj: Any) -> list[int] | str:
    if hasattr(obj, "shape"):
        return [int(v) for v in obj.shape]
    if hasattr(obj, "size"):
        try:
            return [int(v) for v in obj.size()]
        except TypeError:
            pass
    return repr(obj)


def summarize_heads(net: Any) -> dict[str, Any]:
    def layer_info(layer: Any) -> dict[str, Any]:
        return {
            "in_channels": getattr(layer, "in_channels", None),
            "out_channels": getattr(layer, "out_channels", None),
            "kernel_size": list(getattr(layer, "kernel_size", ()))
            if isinstance(getattr(layer, "kernel_size", None), tuple)
            else getattr(layer, "kernel_size", None),
        }

    return {
        "loc_head_count": len(getattr(net, "loc", [])),
        "conf_head_count": len(getattr(net, "conf", [])),
        "loc_heads": [layer_info(layer) for layer in getattr(net, "loc", [])],
        "conf_heads": [layer_info(layer) for layer in getattr(net, "conf", [])],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect ssd.pytorch model shapes")
    parser.add_argument("--num-classes", type=int, default=21, help="class count including background")
    parser.add_argument("--phase", choices=["train", "test"], default="train", help="model phase to construct")
    parser.add_argument("--run-forward", action="store_true", help="run a zero-input forward pass")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "ok": False,
        "phase": args.phase,
        "num_classes": args.num_classes,
        "size": 300,
        "warnings": [],
    }

    try:
        torch = importlib.import_module("torch")
        ssd = importlib.import_module("ssd")
        build_ssd = getattr(ssd, "build_ssd")
        net = build_ssd(args.phase, 300, args.num_classes)
        if net is None:
            report["error"] = "build_ssd returned None; phase and size are unsupported"
            print(json.dumps(report, indent=2, sort_keys=True))
            return 2

        report["torch_version"] = getattr(torch, "__version__", "unknown")
        report["model_class"] = type(net).__name__
        report["prior_shape"] = shape_of(getattr(net, "priors", None))
        report["selected_cfg_name"] = getattr(getattr(net, "cfg", {}), "get", lambda _k, _d=None: _d)("name", None)
        report["head_summary"] = summarize_heads(net)
        report["has_detect"] = hasattr(net, "detect")
        report["has_softmax"] = hasattr(net, "softmax")

        if args.run_forward:
            net.eval()
            x = torch.zeros(1, 3, 300, 300)
            with torch.no_grad():
                out = net(x)
            if isinstance(out, tuple):
                report["forward_type"] = "tuple"
                report["forward_shapes"] = [shape_of(item) for item in out]
            else:
                report["forward_type"] = type(out).__name__
                report["forward_shape"] = shape_of(out)
            if args.phase == "test":
                report["warnings"].append(
                    "test-phase forward succeeded in this runtime; still verify Detect compatibility before relying on eval/demo workflows"
                )
        elif args.phase == "test":
            report["warnings"].append(
                "constructed test-phase model only; modern PyTorch may still fail when Detect.forward is executed"
            )

        report["ok"] = True
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all failures as JSON
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc().splitlines()[-8:]
        if "coco_labels.txt" in str(exc):
            report["hint"] = (
                "Importing ssd/data can require a COCO label-map file at the configured user data root. "
                "Create that file or patch the COCO default transform before model inspection."
            )
        if "Legacy autograd" in str(exc) or "non-static forward" in str(exc):
            report["hint"] = "Patch the legacy Detect autograd Function or use a legacy-compatible PyTorch runtime."
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
