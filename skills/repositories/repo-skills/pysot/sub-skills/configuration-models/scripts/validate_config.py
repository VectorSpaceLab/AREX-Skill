#!/usr/bin/env python3
"""Safe PySOT configuration validator.

This helper loads a user-supplied PySOT YAML through the repository's YACS
``cfg`` object, checks model/config consistency, and can optionally instantiate
``ModelBuilder`` plus ``build_tracker``. It does not load snapshots, open video,
run benchmarks, download data, or start training.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


BACKBONES = {"alexnetlegacy", "alexnet", "mobilenetv2", "resnet18", "resnet34", "resnet50"}
NECKS = {"AdjustLayer", "AdjustAllLayer"}
RPNS = {"UPChannelRPN", "DepthwiseRPN", "MultiRPN"}
MASKS = {"MaskCorr"}
REFINES = {"Refine"}
TRACKERS = {"SiamRPNTracker", "SiamMaskTracker", "SiamRPNLTTracker"}

MISSING = object()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a PySOT experiment YAML and optionally perform a CPU-safe "
            "ModelBuilder/build_tracker construction smoke."
        )
    )
    parser.add_argument("--config", required=True, help="Path to a PySOT YAML config file.")
    parser.add_argument(
        "--instantiate-model",
        action="store_true",
        help=(
            "After config validation, instantiate ModelBuilder() and build_tracker(model). "
            "This does not load snapshots or run inference/training."
        ),
    )
    parser.add_argument(
        "--allow-defaults",
        action="store_true",
        help=(
            "Permit YAMLs that omit model-defining paths and rely on PySOT cfg defaults. "
            "By default, missing required YAML paths are errors."
        ),
    )
    return parser.parse_args(argv)


def raw_get(node: Any, dotted_path: str) -> Any:
    cur = node
    for part in dotted_path.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            return MISSING
    return cur


def cfg_has(node: Any, key: str) -> bool:
    try:
        return key in node
    except Exception:
        return hasattr(node, key)


def cfg_get(node: Any, key: str, default: Any = MISSING) -> Any:
    try:
        if key in node:
            return node[key]
    except Exception:
        pass
    return getattr(node, key, default)


def cfg_path(node: Any, dotted_path: str, default: Any = MISSING) -> Any:
    cur = node
    for part in dotted_path.split("."):
        cur = cfg_get(cur, part, default)
        if cur is default:
            return default
    return cur


def as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def as_list(value: Any) -> list[Any]:
    if value is MISSING:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def require_raw(raw: Mapping[str, Any], path: str, errors: list[str], warnings: list[str], allow_defaults: bool) -> None:
    if raw_get(raw, path) is MISSING:
        message = f"missing required YAML path {path}"
        if allow_defaults:
            warnings.append(message + " (using PySOT default because --allow-defaults was set)")
        else:
            errors.append(message)


def load_raw_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - depends on caller env
        raise RuntimeError(
            "PyYAML is required to read config files. Install pyyaml in the PySOT environment."
        ) from exc

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:
        raise RuntimeError(f"could not parse YAML: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, Mapping):
        raise RuntimeError("top-level YAML document must be a mapping")
    return data


def check_required_raw_paths(raw: Mapping[str, Any], errors: list[str], warnings: list[str], allow_defaults: bool) -> None:
    required = [
        "META_ARC",
        "BACKBONE",
        "BACKBONE.TYPE",
        "BACKBONE.KWARGS",
        "ADJUST",
        "ADJUST.ADJUST",
        "RPN",
        "RPN.TYPE",
        "RPN.KWARGS",
        "MASK",
        "MASK.MASK",
        "ANCHOR",
        "ANCHOR.STRIDE",
        "ANCHOR.RATIOS",
        "ANCHOR.SCALES",
        "ANCHOR.ANCHOR_NUM",
        "TRACK",
        "TRACK.TYPE",
        "TRACK.EXEMPLAR_SIZE",
        "TRACK.INSTANCE_SIZE",
        "TRACK.BASE_SIZE",
        "TRACK.CONTEXT_AMOUNT",
    ]
    for path in required:
        require_raw(raw, path, errors, warnings, allow_defaults)

    adjust_enabled = raw_get(raw, "ADJUST.ADJUST")
    if adjust_enabled is not MISSING and as_bool(adjust_enabled):
        for path in ("ADJUST.TYPE", "ADJUST.KWARGS"):
            require_raw(raw, path, errors, warnings, allow_defaults)

    mask_enabled = raw_get(raw, "MASK.MASK")
    if mask_enabled is not MISSING and as_bool(mask_enabled):
        for path in ("MASK.TYPE", "MASK.KWARGS", "REFINE", "REFINE.REFINE", "REFINE.TYPE"):
            require_raw(raw, path, errors, warnings, allow_defaults)

    tracker = raw_get(raw, "TRACK.TYPE")
    if tracker == "SiamRPNLTTracker":
        for path in ("TRACK.LOST_INSTANCE_SIZE", "TRACK.CONFIDENCE_LOW", "TRACK.CONFIDENCE_HIGH"):
            if raw_get(raw, path) is MISSING:
                warnings.append(f"{path} is not explicit for SiamRPNLTTracker; PySOT default will be used")


def import_and_merge_cfg(config_path: Path, errors: list[str]) -> Any:
    try:
        from pysot.core.config import cfg
    except Exception as exc:
        errors.append(
            "could not import pysot.core.config.cfg. PySOT usually imports from a checkout/PYTHONPATH "
            f"or editable-development setup; original error: {type(exc).__name__}: {exc}"
        )
        return None

    try:
        cfg.merge_from_file(str(config_path))
    except Exception as exc:
        errors.append(f"YACS cfg.merge_from_file failed: {type(exc).__name__}: {exc}")
        return None
    return cfg


def check_component_maps(cfg: Any, errors: list[str], warnings: list[str]) -> None:
    backbone = str(cfg.BACKBONE.TYPE)
    if backbone not in BACKBONES:
        errors.append(f"unsupported BACKBONE.TYPE={backbone!r}; expected one of {sorted(BACKBONES)}")

    rpn_type = str(cfg.RPN.TYPE)
    if rpn_type not in RPNS:
        errors.append(f"unsupported RPN.TYPE={rpn_type!r}; expected one of {sorted(RPNS)}")

    adjust_enabled = as_bool(cfg.ADJUST.ADJUST)
    if adjust_enabled:
        adjust_type = str(cfg.ADJUST.TYPE)
        if adjust_type not in NECKS:
            errors.append(f"unsupported ADJUST.TYPE={adjust_type!r}; expected one of {sorted(NECKS)}")

    mask_enabled = as_bool(cfg.MASK.MASK)
    if mask_enabled:
        mask_type = str(cfg.MASK.TYPE)
        if mask_type not in MASKS:
            errors.append(f"unsupported MASK.TYPE={mask_type!r}; expected one of {sorted(MASKS)}")
        refine_enabled = as_bool(cfg.REFINE.REFINE)
        refine_type = str(cfg.REFINE.TYPE)
        if refine_enabled and refine_type not in REFINES:
            errors.append(f"unsupported REFINE.TYPE={refine_type!r}; expected one of {sorted(REFINES)}")
    else:
        refine_enabled = as_bool(cfg.REFINE.REFINE)

    tracker = str(cfg.TRACK.TYPE)
    if tracker not in TRACKERS:
        errors.append(f"unsupported TRACK.TYPE={tracker!r}; expected one of {sorted(TRACKERS)}")

    if tracker == "SiamMaskTracker" and not (mask_enabled and refine_enabled):
        errors.append("TRACK.TYPE=SiamMaskTracker requires MASK.MASK=true and REFINE.REFINE=true")
    if tracker != "SiamMaskTracker" and mask_enabled:
        warnings.append("MASK.MASK is true but TRACK.TYPE is not SiamMaskTracker; mask outputs may be unused")
    if tracker == "SiamRPNLTTracker" and mask_enabled:
        warnings.append("SiamRPNLTTracker is a long-term RPN tracker; MASK.MASK is usually false")


def check_anchor_and_shapes(cfg: Any, errors: list[str], warnings: list[str], summary: dict[str, Any]) -> None:
    ratios = as_list(cfg.ANCHOR.RATIOS)
    scales = as_list(cfg.ANCHOR.SCALES)
    computed_anchor_num = len(ratios) * len(scales)
    actual_anchor_num = int(cfg.ANCHOR.ANCHOR_NUM)
    summary["anchor_num"] = actual_anchor_num
    summary["anchor_product"] = computed_anchor_num

    if actual_anchor_num != computed_anchor_num:
        errors.append(
            f"ANCHOR.ANCHOR_NUM={actual_anchor_num} but len(RATIOS)*len(SCALES)={computed_anchor_num}"
        )

    rpn_anchor_num = cfg_path(cfg, "RPN.KWARGS.anchor_num")
    if rpn_anchor_num is not MISSING:
        try:
            rpn_anchor_int = int(rpn_anchor_num)
        except Exception:
            errors.append(f"RPN.KWARGS.anchor_num={rpn_anchor_num!r} is not an integer")
        else:
            summary["rpn_anchor_num"] = rpn_anchor_int
            if rpn_anchor_int != actual_anchor_num:
                errors.append(
                    f"RPN.KWARGS.anchor_num={rpn_anchor_int} but ANCHOR.ANCHOR_NUM={actual_anchor_num}"
                )

    stride = int(cfg.ANCHOR.STRIDE)
    exemplar = int(cfg.TRACK.EXEMPLAR_SIZE)
    instance = int(cfg.TRACK.INSTANCE_SIZE)
    base = int(cfg.TRACK.BASE_SIZE)
    if stride <= 0:
        errors.append(f"ANCHOR.STRIDE must be positive, got {stride}")
        return
    if instance <= exemplar:
        errors.append(
            f"TRACK.INSTANCE_SIZE should be greater than TRACK.EXEMPLAR_SIZE, got {instance} <= {exemplar}"
        )
    delta = instance - exemplar
    if delta % stride != 0:
        warnings.append(
            "TRACK.INSTANCE_SIZE - TRACK.EXEMPLAR_SIZE is not divisible by ANCHOR.STRIDE; "
            "tracker score_size uses floor division"
        )
    score_size = delta // stride + 1 + base
    summary["tracker_score_size"] = score_size
    if score_size <= 0:
        errors.append(f"computed tracker score_size must be positive, got {score_size}")

    rpn_type = str(cfg.RPN.TYPE)
    if rpn_type == "MultiRPN":
        in_channels = cfg_path(cfg, "RPN.KWARGS.in_channels")
        if in_channels is MISSING:
            errors.append("RPN.TYPE=MultiRPN requires RPN.KWARGS.in_channels")
        else:
            in_channels_list = as_list(in_channels)
            summary["rpn_feature_count"] = len(in_channels_list)
            if len(in_channels_list) == 0:
                errors.append("RPN.KWARGS.in_channels must not be empty for MultiRPN")
            adjust_out = cfg_path(cfg, "ADJUST.KWARGS.out_channels")
            if as_bool(cfg.ADJUST.ADJUST) and adjust_out is not MISSING:
                adjust_out_list = as_list(adjust_out)
                if len(adjust_out_list) != len(in_channels_list):
                    errors.append(
                        "MultiRPN feature count mismatch: "
                        f"len(RPN.KWARGS.in_channels)={len(in_channels_list)} but "
                        f"len(ADJUST.KWARGS.out_channels)={len(adjust_out_list)}"
                    )


def check_training_formula(raw: Mapping[str, Any], cfg: Any, errors: list[str], warnings: list[str], summary: dict[str, Any]) -> None:
    if raw_get(raw, "TRAIN") is MISSING:
        return
    try:
        search = float(cfg.TRAIN.SEARCH_SIZE)
        exemplar = float(cfg.TRAIN.EXEMPLAR_SIZE)
        stride = float(cfg.ANCHOR.STRIDE)
        base = float(cfg.TRAIN.BASE_SIZE)
        output = float(cfg.TRAIN.OUTPUT_SIZE)
    except Exception as exc:
        errors.append(f"could not read TRAIN output-size fields: {type(exc).__name__}: {exc}")
        return
    if stride <= 0:
        errors.append(f"ANCHOR.STRIDE must be positive for TRAIN formula, got {stride:g}")
        return
    desired = (search - exemplar) / stride + 1 + base
    summary["train_desired_output_size"] = desired
    summary["train_output_size"] = output
    if abs(desired - output) > 1e-9:
        errors.append(
            "TRAIN.OUTPUT_SIZE mismatch: "
            f"(SEARCH_SIZE - EXEMPLAR_SIZE) / ANCHOR.STRIDE + 1 + TRAIN.BASE_SIZE = {desired:g}, "
            f"but TRAIN.OUTPUT_SIZE={output:g}"
        )
    if abs(desired - round(desired)) > 1e-9:
        warnings.append(f"TRAIN desired output size is non-integer ({desired:g}); PySOT expects a grid size")


def check_model_instantiation(errors: list[str], summary: dict[str, Any]) -> None:
    try:
        from pysot.models.model_builder import ModelBuilder
        from pysot.tracker.tracker_builder import build_tracker
    except Exception as exc:
        errors.append(f"could not import model/tracker builders: {type(exc).__name__}: {exc}")
        return
    try:
        model = ModelBuilder()
        model.eval()
        tracker = build_tracker(model)
    except Exception as exc:
        errors.append(f"ModelBuilder/build_tracker construction failed: {type(exc).__name__}: {exc}")
        return
    summary["model_class"] = type(model).__name__
    summary["tracker_class"] = type(tracker).__name__


def print_report(errors: Iterable[str], warnings: Iterable[str], summary: Mapping[str, Any]) -> int:
    errors = list(errors)
    warnings = list(warnings)
    if errors:
        print("PySOT config validation FAILED", file=sys.stderr)
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        if warnings:
            for item in warnings:
                print(f"WARNING: {item}", file=sys.stderr)
        return 2

    print("PySOT config validation passed")
    for key in sorted(summary):
        print(f"{key}: {summary[key]}")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config_path = Path(args.config).expanduser()
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {"config": str(config_path)}

    if not config_path.is_file():
        errors.append(f"config file does not exist: {config_path}")
        return print_report(errors, warnings, summary)

    try:
        raw = load_raw_yaml(config_path)
    except RuntimeError as exc:
        errors.append(str(exc))
        return print_report(errors, warnings, summary)

    check_required_raw_paths(raw, errors, warnings, args.allow_defaults)

    cfg = import_and_merge_cfg(config_path, errors)
    if cfg is not None:
        summary["meta_arc"] = getattr(cfg, "META_ARC", "")
        summary["backbone"] = cfg.BACKBONE.TYPE
        summary["rpn"] = cfg.RPN.TYPE
        summary["tracker"] = cfg.TRACK.TYPE
        summary["mask_enabled"] = bool(cfg.MASK.MASK)
        check_component_maps(cfg, errors, warnings)
        check_anchor_and_shapes(cfg, errors, warnings, summary)
        check_training_formula(raw, cfg, errors, warnings, summary)

    if args.instantiate_model:
        if errors:
            warnings.append("skipped ModelBuilder/build_tracker construction because validation errors are present")
        else:
            check_model_instantiation(errors, summary)

    return print_report(errors, warnings, summary)


if __name__ == "__main__":
    raise SystemExit(main())
