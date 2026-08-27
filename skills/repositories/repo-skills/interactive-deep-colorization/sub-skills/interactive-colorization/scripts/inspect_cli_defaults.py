#!/usr/bin/env python3
"""Inspect distilled GUI CLI defaults without importing GUI/Caffe dependencies.

This script intentionally does not import ideepcolor.py, PyQt, qdarkstyle,
Caffe, torch, or model weights. It encodes parser facts distilled from the
repository's root GUI script and Docker GUI script.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Any, Dict, Iterable, List

COMMON_ARGUMENTS: List[Dict[str, Any]] = [
    {
        "option": "--win_size",
        "dest": "win_size",
        "type": "int",
        "default": 512,
        "help": "the size of the main window",
        "post_parse": "win_size is truncated to a multiple of 4 in the main routine",
    },
    {
        "option": "--image_file",
        "dest": "image_file",
        "type": "str",
        "default": "test_imgs/mortar_pestle.jpg",
        "help": "input image",
    },
    {
        "option": "--gpu",
        "dest": "gpu",
        "type": "int",
        "default": 0,
        "help": "gpu id",
        "post_parse": "--cpu_mode sets gpu to -1 after parsed arguments are printed",
    },
    {
        "option": "--cpu_mode",
        "dest": "cpu_mode",
        "action": "store_true",
        "default": False,
        "help": "do not use gpu",
        "post_parse": "sets gpu to -1 in the main routine",
    },
    {
        "option": "--color_prototxt",
        "dest": "color_prototxt",
        "type": "str",
        "default": "./models/reference_model/deploy_nodist.prototxt",
        "help": "colorization caffe prototxt",
    },
    {
        "option": "--color_caffemodel",
        "dest": "color_caffemodel",
        "type": "str",
        "default": "./models/reference_model/model.caffemodel",
        "help": "colorization caffe prototxt",
    },
    {
        "option": "--dist_prototxt",
        "dest": "dist_prototxt",
        "type": "str",
        "default": "./models/reference_model/deploy_nopred.prototxt",
        "help": "distribution net prototxt",
    },
    {
        "option": "--dist_caffemodel",
        "dest": "dist_caffemodel",
        "type": "str",
        "default": "./models/reference_model/model.caffemodel",
        "help": "distribution net caffemodel",
    },
    {
        "option": "--color_model",
        "dest": "color_model",
        "type": "str",
        "default": "./models/pytorch/caffemodel.pth",
        "help": "colorization model",
    },
    {
        "option": "--dist_model",
        "dest": "color_model",
        "type": "str",
        "default": "./models/pytorch/caffemodel.pth",
        "help": "colorization distribution prediction model",
        "quirk": "shares dest='color_model'; no independent args.dist_model is created",
    },
    {
        "option": "--backend",
        "dest": "backend",
        "type": "str",
        "default": None,  # filled per variant
        "help": "caffe or pytorch",
    },
    {
        "option": "--pytorch_maskcent",
        "dest": "pytorch_maskcent",
        "action": "store_true",
        "default": False,
        "help": "need to center mask for some PyTorch checkpoints",
    },
    {
        "option": "--load_size",
        "dest": "load_size",
        "type": "int",
        "default": 256,
        "help": "image size",
        "deprecated": True,
        "post_parse": "still used as wrapper Xd/load_size by the GUI main routine",
    },
]

VARIANTS = {
    "root": {
        "source_label": "root GUI parser",
        "script_name": "ideepcolor.py",
        "backend_default": "caffe",
        "qt_binding": "PyQt4",
        "style_dependency": "qdarkstyle imported at module top level",
    },
    "docker": {
        "source_label": "Docker GUI parser",
        "script_name": "docker/ideepcolor_docker.py",
        "backend_default": "pytorch",
        "qt_binding": "PyQt5",
        "style_dependency": "qdarkstyle stylesheet call is commented out",
    },
}

QUIRKS = [
    "Both parser variants define --dist_model with dest='color_model'.",
    "There is no independent args.dist_model attribute.",
    "Both PyTorch wrapper initializations use args.color_model.",
    "If --color_model and --dist_model are both supplied, the final color_model value follows argparse option order.",
    "Parsed arguments are printed before --cpu_mode changes gpu to -1 and before win_size is truncated to a multiple of 4.",
]


def variant_arguments(variant: str) -> List[Dict[str, Any]]:
    args = deepcopy(COMMON_ARGUMENTS)
    for item in args:
        if item["option"] == "--backend":
            item["default"] = VARIANTS[variant]["backend_default"]
    return args


def build_report(variants: Iterable[str]) -> Dict[str, Any]:
    selected = {}
    for variant in variants:
        meta = deepcopy(VARIANTS[variant])
        meta["arguments"] = variant_arguments(variant)
        selected[variant] = meta
    return {
        "description": "Distilled iDeepColor GUI CLI parser facts; no GUI/Caffe/model imports performed.",
        "variants": selected,
        "quirks": QUIRKS,
        "pytorch_model_path_behavior": {
            "color_model_arg": "--color_model",
            "dist_model_arg": "--dist_model",
            "shared_dest": "color_model",
            "independent_dist_model_attr": False,
            "color_wrapper_uses": "args.color_model",
            "dist_wrapper_uses": "args.color_model",
        },
    }


def print_table(report: Dict[str, Any]) -> None:
    print(report["description"])
    print()
    for key, meta in report["variants"].items():
        print(f"[{key}] {meta['source_label']} ({meta['script_name']})")
        print(f"  Qt binding: {meta['qt_binding']}")
        print(f"  Style dependency: {meta['style_dependency']}")
        print("  Arguments:")
        for arg in meta["arguments"]:
            default = arg.get("default")
            if isinstance(default, bool):
                default_text = "true" if default else "false"
            else:
                default_text = str(default)
            extra = []
            if arg.get("action"):
                extra.append(f"action={arg['action']}")
            if arg.get("type"):
                extra.append(f"type={arg['type']}")
            if arg.get("deprecated"):
                extra.append("deprecated-comment")
            if arg.get("quirk"):
                extra.append("QUIRK: " + arg["quirk"])
            if arg.get("post_parse"):
                extra.append("post-parse: " + arg["post_parse"])
            extra_text = "; ".join(extra)
            print(f"    {arg['option']:<20} dest={arg['dest']:<18} default={default_text!r} {extra_text}")
        print()
    print("Quirks:")
    for quirk in report["quirks"]:
        print(f"  - {quirk}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect distilled interactive-deep-colorization GUI CLI defaults without importing GUI dependencies."
    )
    parser.add_argument(
        "--variant",
        choices=("root", "docker", "both"),
        default="both",
        help="which parser variant to report",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    variants = ("root", "docker") if args.variant == "both" else (args.variant,)
    report = build_report(variants)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_table(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
