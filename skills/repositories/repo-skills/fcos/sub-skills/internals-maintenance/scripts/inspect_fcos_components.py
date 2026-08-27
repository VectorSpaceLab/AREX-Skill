#!/usr/bin/env python3
"""Safely inspect FCOS component availability and config-derived facts."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys


def imp(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    p = argparse.ArgumentParser(description="Inspect FCOS internals without training or downloading weights")
    p.add_argument("--config", help="Optional config to merge")
    args = p.parse_args()
    report = {"python": sys.version.split()[0], "imports": {}, "signatures": {}, "config": None}
    for name in ["torch", "fcos_core._C", "fcos_core.modeling.rpn.fcos.fcos", "fcos_core.modeling.rpn.fcos.inference", "fcos_core.structures.bounding_box"]:
        mod, err = imp(name)
        report["imports"][name] = {"ok": err is None, "error": err}
        if mod and name.endswith("fcos.fcos"):
            for obj in ["FCOSHead", "FCOSModule", "build_fcos"]:
                report["signatures"][obj] = str(inspect.signature(getattr(mod, obj)))
        if mod and name.endswith("inference"):
            report["signatures"]["make_fcos_postprocessor"] = str(inspect.signature(getattr(mod, "make_fcos_postprocessor")))
    if args.config:
        try:
            from fcos_core.config import cfg
            c = cfg.clone(); c.merge_from_file(args.config)
            report["config"] = {
                "ok": True,
                "fcos_on": bool(c.MODEL.FCOS_ON),
                "num_classes": int(c.MODEL.FCOS.NUM_CLASSES),
                "fpn_strides": list(c.MODEL.FCOS.FPN_STRIDES),
                "norm_reg_targets": bool(c.MODEL.FCOS.NORM_REG_TARGETS),
                "centerness_on_reg": bool(c.MODEL.FCOS.CENTERNESS_ON_REG),
                "iou_loss_type": str(c.MODEL.FCOS.IOU_LOSS_TYPE),
            }
        except Exception as exc:
            report["config"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["imports"].get("fcos_core.modeling.rpn.fcos.fcos", {}).get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
