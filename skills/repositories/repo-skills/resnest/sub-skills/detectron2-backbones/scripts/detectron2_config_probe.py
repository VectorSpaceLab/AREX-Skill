#!/usr/bin/env python3
"""Safely inspect ResNeSt-related Detectron2 config fields.

The default run does not train, build a model, download weights, or require a
source checkout config file. It only imports optional Detectron2/ResNeSt-D2
modules, extends a Detectron2 CfgNode with ResNeSt fields, optionally merges a
user-provided config and KEY VALUE overrides, and prints relevant fields.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

RESNEST_FIELDS = [
    "MODEL.META_ARCHITECTURE",
    "MODEL.BACKBONE.NAME",
    "MODEL.WEIGHTS",
    "MODEL.MASK_ON",
    "MODEL.RESNETS.DEPTH",
    "MODEL.RESNETS.OUT_FEATURES",
    "MODEL.RESNETS.STRIDE_IN_1X1",
    "MODEL.RESNETS.DEEP_STEM",
    "MODEL.RESNETS.AVD",
    "MODEL.RESNETS.AVG_DOWN",
    "MODEL.RESNETS.RADIX",
    "MODEL.RESNETS.BOTTLENECK_WIDTH",
    "MODEL.RESNETS.NORM",
    "MODEL.RESNETS.DEFORM_ON_PER_STAGE",
    "MODEL.RESNETS.DEFORM_MODULATED",
    "MODEL.RESNETS.DEFORM_NUM_GROUPS",
    "MODEL.FPN.IN_FEATURES",
    "MODEL.FPN.OUT_CHANNELS",
    "MODEL.FPN.NORM",
    "MODEL.PIXEL_MEAN",
    "MODEL.PIXEL_STD",
    "DATASETS.TRAIN",
    "DATASETS.TEST",
    "SOLVER.IMS_PER_BATCH",
    "SOLVER.BASE_LR",
    "SOLVER.STEPS",
    "SOLVER.MAX_ITER",
    "INPUT.MIN_SIZE_TRAIN",
    "INPUT.MIN_SIZE_TRAIN_SAMPLING",
    "INPUT.MAX_SIZE_TRAIN",
    "INPUT.FORMAT",
    "TEST.PRECISE_BN.ENABLED",
    "TEST.AUG.ENABLED",
]


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe optional Detectron2 + ResNeSt config registration and print "
            "ResNeSt-related fields without training or model construction."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help=(
            "Optional user Detectron2 config file to merge. The default run uses "
            "Detectron2 defaults plus add_resnest_config only."
        ),
    )
    parser.add_argument(
        "--opts",
        nargs=argparse.REMAINDER,
        default=[],
        help=(
            "Optional trailing Detectron2 KEY VALUE pairs, for example: "
            "--opts MODEL.BACKBONE.NAME build_resnest_fpn_backbone MODEL.RESNETS.DEPTH 50"
        ),
    )
    parser.add_argument(
        "--require-detectron2",
        action="store_true",
        help="Return a non-zero exit code if Detectron2 is missing instead of reporting a conditional skip.",
    )
    parser.add_argument(
        "--no-freeze",
        action="store_true",
        help="Do not freeze the config after merging. This is rarely needed and still does not train.",
    )
    return parser.parse_args(argv)


def emit(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def json_ready(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    return str(value)


def get_dotted(obj: Any, dotted: str) -> Any:
    current = obj
    for part in dotted.split("."):
        try:
            current = getattr(current, part)
            continue
        except Exception:
            pass
        try:
            current = current[part]
            continue
        except Exception as exc:
            raise KeyError(dotted) from exc
    return current


def collect_fields(cfg: Any, fields: Iterable[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for field in fields:
        try:
            result[field] = json_ready(get_dotted(cfg, field))
        except KeyError:
            result[field] = "<missing>"
    return result


def registry_status() -> Dict[str, bool]:
    status: Dict[str, bool] = {}
    try:
        from detectron2.modeling.backbone import BACKBONE_REGISTRY
    except Exception:
        return {
            "build_resnest_backbone": False,
            "build_resnest_fpn_backbone": False,
        }
    for name in ["build_resnest_backbone", "build_resnest_fpn_backbone"]:
        try:
            BACKBONE_REGISTRY.get(name)
            status[name] = True
        except Exception:
            status[name] = False
    return status


def recommendations(fields: Dict[str, Any]) -> List[str]:
    notes: List[str] = []
    if fields.get("MODEL.BACKBONE.NAME") != "build_resnest_fpn_backbone":
        notes.append("MODEL.BACKBONE.NAME is not build_resnest_fpn_backbone; set it for ResNeSt/FPN recipes.")
    expected = {
        "MODEL.RESNETS.STRIDE_IN_1X1": False,
        "MODEL.RESNETS.DEEP_STEM": True,
        "MODEL.RESNETS.AVD": True,
        "MODEL.RESNETS.AVG_DOWN": True,
        "MODEL.RESNETS.RADIX": 2,
        "MODEL.RESNETS.BOTTLENECK_WIDTH": 64,
    }
    for key, value in expected.items():
        if fields.get(key) != value:
            notes.append(f"{key} is {fields.get(key)!r}; released ResNeSt recipes expect {value!r}.")
    norm_values = [
        fields.get("MODEL.RESNETS.NORM"),
        fields.get("MODEL.FPN.NORM"),
    ]
    if "SyncBN" in norm_values:
        notes.append("SyncBN is selected; verify the launcher/backend supports synchronized batch norm.")
    deform = fields.get("MODEL.RESNETS.DEFORM_ON_PER_STAGE")
    if isinstance(deform, list) and any(bool(v) for v in deform):
        notes.append("DCN stages are enabled; verify Detectron2 deformable convolution operators before training/eval.")
    if fields.get("INPUT.FORMAT") not in ("RGB", "<missing>"):
        notes.append("Released ResNeSt Detectron2 weights use RGB input statistics; verify INPUT.FORMAT and pixel stats.")
    return notes


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    try:
        from detectron2.config import get_cfg
    except ModuleNotFoundError as exc:
        if exc.name == "detectron2":
            emit(
                {
                    "status": "missing_optional_dependency",
                    "detectron2_available": False,
                    "message": (
                        "Detectron2 is optional for ResNeSt and is not importable in this environment. "
                        "Install a Detectron2 build compatible with the active PyTorch/CUDA stack before "
                        "running config merges, model construction, training, or evaluation."
                    ),
                }
            )
            return 2 if args.require_detectron2 else 0
        raise
    except Exception as exc:
        emit(
            {
                "status": "detectron2_import_error",
                "detectron2_available": False,
                "error_type": exc.__class__.__name__,
                "message": "Detectron2 imported unsuccessfully; repair the Detectron2 installation before using ResNeSt-D2.",
            }
        )
        return 2 if args.require_detectron2 else 0

    try:
        from resnest.d2 import add_resnest_config  # imports/registers backbone builders
    except ModuleNotFoundError as exc:
        emit(
            {
                "status": "resnest_d2_import_error",
                "detectron2_available": True,
                "error_type": exc.__class__.__name__,
                "missing_module": exc.name,
                "message": "Detectron2 is importable, but resnest.d2 could not be imported.",
            }
        )
        return 2
    except Exception as exc:
        emit(
            {
                "status": "resnest_d2_import_error",
                "detectron2_available": True,
                "error_type": exc.__class__.__name__,
                "message": "Detectron2 is importable, but ResNeSt Detectron2 registration failed.",
            }
        )
        return 2

    if args.opts and len(args.opts) % 2 != 0:
        emit(
            {
                "status": "argument_error",
                "message": "--opts must contain an even number of KEY VALUE tokens.",
                "opts": args.opts,
            }
        )
        return 2

    cfg = get_cfg()
    try:
        add_resnest_config(cfg)
    except Exception as exc:
        emit(
            {
                "status": "add_resnest_config_error",
                "detectron2_available": True,
                "error_type": exc.__class__.__name__,
                "message": "add_resnest_config(cfg) failed before config merge.",
            }
        )
        return 2

    merged_config = None
    if args.config_file:
        config_path = Path(args.config_file).expanduser()
        if not config_path.is_file():
            emit(
                {
                    "status": "config_error",
                    "message": "The supplied --config-file does not exist or is not a file.",
                    "config_file": args.config_file,
                }
            )
            return 2
        try:
            cfg.merge_from_file(str(config_path))
            merged_config = args.config_file
        except Exception as exc:
            emit(
                {
                    "status": "config_merge_error",
                    "message": "Detectron2 could not merge the supplied config file.",
                    "config_file": args.config_file,
                    "error_type": exc.__class__.__name__,
                }
            )
            return 2

    if args.opts:
        try:
            cfg.merge_from_list(args.opts)
        except Exception as exc:
            emit(
                {
                    "status": "opts_merge_error",
                    "message": "Detectron2 could not merge the supplied KEY VALUE opts.",
                    "opts": args.opts,
                    "error_type": exc.__class__.__name__,
                }
            )
            return 2

    if not args.no_freeze:
        try:
            cfg.freeze()
        except Exception as exc:
            emit(
                {
                    "status": "freeze_error",
                    "message": "Config merge succeeded, but cfg.freeze() failed.",
                    "error_type": exc.__class__.__name__,
                }
            )
            return 2

    fields = collect_fields(cfg, RESNEST_FIELDS)
    emit(
        {
            "status": "ok",
            "detectron2_available": True,
            "merged_config_file": merged_config,
            "merged_opts": args.opts,
            "registered_backbones": registry_status(),
            "resnest_fields": fields,
            "recommendations": recommendations(fields),
            "training_or_model_build_performed": False,
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
