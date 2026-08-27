#!/usr/bin/env python3
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
"""Inspect installed RF-DETR training/config/CLI surfaces without training.

The script imports public configuration and training modules, parses optional
Lightning YAML, and instantiates Pydantic config objects only. It never
instantiates RF-DETR model wrappers, downloads pretrained weights, creates a
Trainer, or starts a run.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import inspect
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Any

TRAIN_CONFIG_CLASSES = (
    "TrainConfig",
    "SegmentationTrainConfig",
    "KeypointTrainConfig",
)
MODEL_CONFIG_CLASSES = (
    "RFDETRNanoConfig",
    "RFDETRSmallConfig",
    "RFDETRMediumConfig",
    "RFDETRLargeConfig",
    "RFDETRSegNanoConfig",
    "RFDETRSegSmallConfig",
    "RFDETRSegMediumConfig",
    "RFDETRSegLargeConfig",
    "RFDETRKeypointPreviewConfig",
)
RUNTIME_MODULES = (
    "rfdetr",
    "rfdetr.config",
    "rfdetr.cli",
    "rfdetr.training",
    "rfdetr.training.cli",
    "rfdetr.training.module_data",
    "rfdetr.training.module_model",
    "rfdetr.training.trainer",
    "rfdetr.datasets",
    "rfdetr.datasets.coco",
    "rfdetr.datasets.yolo",
    "rfdetr.datasets._keypoint_schema",
)
OPTIONAL_PACKAGES = (
    "pytorch_lightning",
    "torchmetrics",
    "pycocotools",
    "jsonargparse",
    "albumentations",
    "kornia",
    "tensorboard",
    "wandb",
    "mlflow",
    "clearml",
)
PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:/[A-Za-z0-9_.+@=-][^\s:'\"]*|[A-Za-z]:\\[^\s:'\"]*)")
TRAIN_FIELDS = (
    "dataset_file",
    "dataset_dir",
    "output_dir",
    "epochs",
    "batch_size",
    "grad_accum_steps",
    "auto_batch_target_effective",
    "resume",
    "lr",
    "lr_encoder",
    "optimizer",
    "optimizer_kwargs",
    "lr_scheduler",
    "lr_scheduler_kwargs",
    "augmentation_backend",
    "aug_config",
    "scale_jitter",
    "tensorboard",
    "wandb",
    "mlflow",
    "clearml",
    "class_names",
    "use_ema",
    "early_stopping",
    "skip_best_epochs",
    "smooth_alpha",
    "run_test",
    "accelerator",
    "devices",
    "strategy",
    "num_nodes",
    "pin_memory",
    "persistent_workers",
    "prefetch_factor",
    "keypoint_flip_pairs",
    "keypoint_oks_sigmas",
)
MODEL_FIELDS = (
    "resolution",
    "patch_size",
    "num_windows",
    "num_classes",
    "pretrain_weights",
    "gradient_checkpointing",
    "segmentation_head",
    "use_grouppose_keypoints",
    "num_keypoints_per_class",
    "model_name",
)
PATH_KEYS = {
    "dataset_dir",
    "output_dir",
    "resume",
    "pretrain_weights",
    "coco_path",
}
AUGMENTATION_VALUES = (
    "cpu",
    "auto",
    "torchvision",
    "albumentations",
    "kornia",
    "tv",
    "albu",
    "gpu",
)


def _metadata_version(package: str) -> str | None:
    """Return an installed distribution version without importing the package."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _package_status(package: str) -> dict[str, Any]:
    """Report whether a package can be discovered, without exposing file paths."""
    spec = importlib.util.find_spec(package)
    return {"available": spec is not None, "version": _metadata_version(package)}


def _clean_error(exc: BaseException) -> str:
    """Return an exception string with filesystem-looking paths redacted."""
    return PATH_PATTERN.sub("<path>", f"{type(exc).__name__}: {exc}")


def _module_status(module_name: str) -> dict[str, Any]:
    """Import a module and return status without exposing installed locations."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - probes should report all failures.
        return {"ok": False, "error": _clean_error(exc)}
    return {"ok": True}


def _safe_value(value: Any) -> Any:
    """Redact path-like values while retaining useful scalar config facts."""
    if isinstance(value, Path):
        return "<path>"
    if isinstance(value, str):
        if "/" in value or "\\" in value or value.startswith("~"):
            return "<path>"
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        prefix = [_safe_value(item) for item in list(value)[:12]]
        if len(value) > 12:
            prefix.append("<more>")
        return prefix
    if isinstance(value, dict):
        items = list(value.items())[:12]
        result = {str(key): _safe_value(item) for key, item in items}
        if len(value) > 12:
            result["<more>"] = f"{len(value) - 12} more entries"
        return result
    return type(value).__name__


def _field_default(field: Any) -> Any:
    """Return a stable field default marker/value for a Pydantic field."""
    if field is None:
        return None
    if field.is_required():
        return "<required>"
    if getattr(field, "default_factory", None) is not None:
        return "<factory>"
    return _safe_value(getattr(field, "default", None))


def _class_summary(cls: type[Any], field_names: tuple[str, ...]) -> dict[str, Any]:
    """Summarize Pydantic model fields without constructing the class."""
    fields = getattr(cls, "model_fields", {})
    selected: dict[str, Any] = {}
    for name in field_names:
        field = fields.get(name) if isinstance(fields, dict) else None
        if field is not None:
            selected[name] = _field_default(field)
    summary: dict[str, Any] = {
        "available": True,
        "field_count": len(fields) if isinstance(fields, dict) else None,
        "selected_defaults": selected,
    }
    patch_size = selected.get("patch_size")
    num_windows = selected.get("num_windows")
    if isinstance(patch_size, int) and isinstance(num_windows, int):
        summary["shape_divisor"] = patch_size * num_windows
    return summary


def _signature(module_name: str, class_name: str, method_name: str) -> str | None:
    """Return a method signature when importable/inspectable."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return str(inspect.signature(getattr(cls, method_name)))
    except Exception:  # noqa: BLE001 - missing signatures are reported as null.
        return None


def _config_class(path: str) -> tuple[type[Any] | None, str | None]:
    """Import a class from the public ``rfdetr.config`` namespace only."""
    if not path.startswith("rfdetr.config."):
        return None, "class_path must use rfdetr.config.*"
    module_name, class_name = path.rsplit(".", 1)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
    except Exception as exc:  # noqa: BLE001
        return None, _clean_error(exc)
    if not isinstance(cls, type):
        return None, "class_path did not resolve to a class"
    return cls, None


def _resolve_config_path(path: Path) -> Path:
    """Resolve a config path against cwd, then this sub-skill root."""
    if path.is_file():
        return path
    skill_root = Path(__file__).resolve().parents[1]
    candidate = skill_root / path
    if candidate.is_file():
        return candidate
    return path


def _load_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read a mapping YAML document with safe loading."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML is unavailable; install a YAML parser to inspect configs."
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return None, f"YAML error: {_clean_error(exc)}"
    if not isinstance(data, dict):
        return None, "YAML root must be a mapping"
    return data, None


def _inspect_section(section: Any, name: str, field_names: tuple[str, ...]) -> dict[str, Any]:
    """Validate and instantiate one Lightning ``class_path``/``init_args`` section."""
    result: dict[str, Any] = {"section": name, "ok": False}
    if not isinstance(section, dict):
        result["error"] = "section is missing or is not a mapping"
        return result
    path = section.get("class_path")
    init_args = section.get("init_args", {}) or {}
    result["class_path"] = path
    if not isinstance(path, str) or not isinstance(init_args, dict):
        result["error"] = "class_path must be a string and init_args a mapping"
        return result
    cls, error = _config_class(path)
    if error:
        result["error"] = error
        return result
    assert cls is not None
    result["class_summary"] = _class_summary(cls, field_names)
    result["provided_fields"] = sorted(str(key) for key in init_args)
    result["provided_args"] = {
        str(key): "<path>" if str(key) in PATH_KEYS or str(key).endswith("_dir") else _safe_value(value)
        for key, value in init_args.items()
    }
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            instance = cls(**init_args)
    except Exception as exc:  # noqa: BLE001 - validation result is the desired output.
        result["error"] = _clean_error(exc)
        return result
    result["ok"] = True
    result["resolved_class"] = type(instance).__name__
    resolved: dict[str, Any] = {}
    for key in field_names:
        if hasattr(instance, key):
            resolved[key] = _safe_value(getattr(instance, key))
    result["resolved_selected_fields"] = resolved
    return result


def _yaml_advice(model_result: dict[str, Any], train_result: dict[str, Any]) -> list[str]:
    """Produce static advice/warnings for a parsed Lightning YAML."""
    advice: list[str] = []
    model_class = str(model_result.get("resolved_class") or model_result.get("class_path") or "")
    train_class = str(train_result.get("resolved_class") or train_result.get("class_path") or "")
    train_fields = train_result.get("resolved_selected_fields", {})
    model_fields = model_result.get("resolved_selected_fields", {})

    if "Seg" in model_class and train_class != "SegmentationTrainConfig":
        advice.append("Segmentation model configs should use SegmentationTrainConfig.")
    if "Keypoint" in model_class and train_class != "KeypointTrainConfig":
        advice.append("Keypoint preview model configs should use KeypointTrainConfig.")
    if "Keypoint" not in model_class and train_class == "KeypointTrainConfig":
        advice.append("KeypointTrainConfig should be paired with RFDETRKeypointPreviewConfig.")
    if train_fields.get("batch_size") == "auto":
        advice.append("The Lightning CLI path does not resolve batch_size='auto'; use a concrete integer.")
    if train_fields.get("clearml") is True:
        advice.append("clearml=True raises NotImplementedError; initialize ClearML SDK separately and omit the flag.")
    if "Keypoint" in model_class and str(train_fields.get("augmentation_backend")).lower() in {"kornia", "gpu"}:
        advice.append("Keypoint training does not support the Kornia/GPU augmentation backend.")
    resolution = model_fields.get("resolution")
    patch_size = model_fields.get("patch_size")
    num_windows = model_fields.get("num_windows")
    if isinstance(resolution, int) and isinstance(patch_size, int) and isinstance(num_windows, int):
        divisor = patch_size * num_windows
        if divisor > 0 and resolution % divisor != 0:
            advice.append(f"resolution={resolution} is not divisible by patch_size*num_windows={divisor}.")
    return advice


def _inspect_yaml(path: Path) -> dict[str, Any]:
    """Inspect a Lightning YAML config and instantiate config objects only."""
    resolved_path = _resolve_config_path(path)
    result: dict[str, Any] = {"config": path.name, "ok": False}
    if not resolved_path.is_file():
        result["error"] = "config file does not exist"
        return result
    data, error = _load_yaml(resolved_path)
    if error:
        result["error"] = error
        return result
    assert data is not None
    model = data.get("model")
    if not isinstance(model, dict):
        result["error"] = "missing top-level model mapping"
        return result
    model_result = _inspect_section(model.get("model_config"), "model_config", MODEL_FIELDS)
    train_result = _inspect_section(model.get("train_config"), "train_config", TRAIN_FIELDS)
    result["model_config"] = model_result
    result["train_config"] = train_result
    result["advice"] = _yaml_advice(model_result, train_result)
    result["ok"] = bool(model_result.get("ok") and train_result.get("ok") and not result["advice"])
    return result


def _augmentation_report(config_module: Any | None) -> dict[str, Any]:
    """Report augmentation backend resolution and optional-package readiness."""
    report: dict[str, Any] = {
        "optional_packages": {
            "albumentations": _package_status("albumentations"),
            "kornia": _package_status("kornia"),
        },
        "values": {},
    }
    if config_module is None:
        report["error"] = "rfdetr.config is not importable"
        return report
    backend_cls = getattr(config_module, "AugmentationBackend", None)
    if backend_cls is None:
        report["error"] = "AugmentationBackend is unavailable"
        return report
    for value in AUGMENTATION_VALUES:
        item: dict[str, Any] = {}
        for has_cuda in (False, True):
            key = "cuda" if has_cuda else "no_cuda"
            try:
                resolved = backend_cls.from_str(value, has_cuda=has_cuda)
                item[key] = getattr(resolved, "value", str(resolved))
            except Exception as exc:  # noqa: BLE001
                item[key] = _clean_error(exc)
        report["values"][value] = item
    report["notes"] = [
        "cpu/auto are late-resolved sentinels and may choose different installed backends.",
        "Explicit albumentations/kornia readiness is enforced by dataset-build helpers and requires rfdetr[augment].",
        "torchvision pins the native pipeline regardless of optional packages.",
    ]
    return report


def inspect_installation(config_path: Path | None = None) -> dict[str, Any]:
    """Collect import, config, augmentation, CLI, and optional-package information."""
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distribution": {"name": "rfdetr", "version": _metadata_version("rfdetr")},
        "optional_packages": {package: _package_status(package) for package in OPTIONAL_PACKAGES},
        "runtime_modules": {module_name: _module_status(module_name) for module_name in RUNTIME_MODULES},
        "signatures": {
            "RFDETR.train": _signature("rfdetr.detr", "RFDETR", "train"),
            "RFDETR.evaluate": _signature("rfdetr.detr", "RFDETR", "evaluate"),
        },
        "train_config_classes": {},
        "model_config_classes": {},
    }

    config_module = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config_module = importlib.import_module("rfdetr.config")
    except Exception as exc:  # noqa: BLE001
        report["config_import_error"] = _clean_error(exc)
    else:
        for name in TRAIN_CONFIG_CLASSES:
            cls = getattr(config_module, name, None)
            report["train_config_classes"][name] = (
                _class_summary(cls, TRAIN_FIELDS) if isinstance(cls, type) else {"available": False}
            )
        for name in MODEL_CONFIG_CLASSES:
            cls = getattr(config_module, name, None)
            report["model_config_classes"][name] = (
                _class_summary(cls, MODEL_FIELDS) if isinstance(cls, type) else {"available": False}
            )
    report["augmentation_backend"] = _augmentation_report(config_module)
    if config_path is not None:
        report["yaml"] = _inspect_yaml(config_path)
    return report


def _print_text(report: dict[str, Any]) -> None:
    """Print a concise human-readable report."""
    version = report["distribution"].get("version") or "not installed"
    print(f"RF-DETR distribution: {version}")
    print(f"Python: {report['python']}")
    print("\nRuntime module status:")
    for name, status in report["runtime_modules"].items():
        marker = "ok" if status.get("ok") else "missing/error"
        print(f"  {name}: {marker}")
        if not status.get("ok"):
            print(f"    {status.get('error')}")
    print("\nTrainConfig variants:")
    for name, item in report.get("train_config_classes", {}).items():
        if not item.get("available"):
            print(f"  {name}: unavailable")
            continue
        defaults = item.get("selected_defaults", {})
        print(
            f"  {name}: {item.get('field_count')} fields; "
            f"batch_size={defaults.get('batch_size')!r}, devices={defaults.get('devices')!r}, "
            f"augmentation_backend={defaults.get('augmentation_backend')!r}"
        )
    print("\nModel config shape rules:")
    for name, item in report.get("model_config_classes", {}).items():
        if not item.get("available"):
            continue
        defaults = item.get("selected_defaults", {})
        print(
            f"  {name}: resolution={defaults.get('resolution')!r}, "
            f"patch={defaults.get('patch_size')!r}, windows={defaults.get('num_windows')!r}, "
            f"divisor={item.get('shape_divisor')!r}"
        )
    print("\nAugmentation backend resolution (no CUDA -> CUDA):")
    for value, item in report.get("augmentation_backend", {}).get("values", {}).items():
        print(f"  {value}: {item.get('no_cuda')} -> {item.get('cuda')}")
    if "yaml" in report:
        yaml_report = report["yaml"]
        print("\nYAML inspection:")
        print(f"  config: {yaml_report.get('config')}")
        print(f"  ok: {yaml_report.get('ok')}")
        if yaml_report.get("error"):
            print(f"  error: {yaml_report['error']}")
        for advice in yaml_report.get("advice", []):
            print(f"  advice: {advice}")
        for section in ("model_config", "train_config"):
            section_report = yaml_report.get(section, {})
            print(f"  {section}: {section_report.get('resolved_class') or section_report.get('error')}")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Optional Lightning YAML config to inspect.")
    parser.add_argument("--json", action="store_true", help="Print the complete JSON report.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when required training/CLI imports fail or inspected YAML has advice/errors.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the inspector CLI."""
    args = build_parser().parse_args(argv)
    report = inspect_installation(args.config)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_text(report)

    if not args.strict:
        return 0
    required_modules = (
        "rfdetr.config",
        "rfdetr.training.cli",
        "rfdetr.training.module_data",
        "rfdetr.training.module_model",
        "rfdetr.training.trainer",
    )
    import_failed = any(not report["runtime_modules"].get(name, {}).get("ok") for name in required_modules)
    yaml_failed = bool(args.config is not None and not report.get("yaml", {}).get("ok", False))
    config_failed = "config_import_error" in report
    return 1 if import_failed or yaml_failed or config_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
