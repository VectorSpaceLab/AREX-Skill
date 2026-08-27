#!/usr/bin/env python3
"""Inspect X-AnyLabeling model registry/configs without loading weights.

The script reads the installed package's model registry and YAML resources,
optionally validates user-supplied custom YAMLs, and (with a temporary config
work directory) asks ModelManager to perform its normal config-list loading.
It never calls ModelManager.load_model(), never instantiates model adapter
classes, and never downloads model files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from importlib import metadata, resources
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# Avoid noisy Qt multimedia plugin diagnostics during headless registry parsing.
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.*=false")


PATH_FIELD_NAMES = {
    "model_path",
    "encoder_model_path",
    "decoder_model_path",
    "det_model_path",
    "rec_model_path",
    "cls_model_path",
    "pose_model_path",
    "tag_model_path",
    "model_pf_path",
    "embedding_model_path",
    "txt_model_path",
    "img_model_path",
    "txt_extra_path",
    "img_extra_path",
    "encoder_data_path",
    "encoder_model_data_path",
    "decoder_model_data_path",
    "language_encoder_path",
    "language_encoder_data_path",
    "rec_char_dict_path",
}

CUSTOM_NAME_EXAMPLES = [
    "ok.Name-1",
    "bad/name",
    r"nested\model",
    "/absolute/path",
    ".",
    "..",
    "has space",
    "_underscore",
    "a..b",
    "中文",
    "",
]


class InspectionError(RuntimeError):
    """Raised for user-facing inspection failures."""


def _load_dependencies():
    """Import X-AnyLabeling modules used for config parsing only."""
    try:
        import anylabeling.config as app_config
        import anylabeling.configs as config_pkg
        from anylabeling.services.auto_labeling import _CUSTOM_MODELS
        from anylabeling.services.auto_labeling.model import load_model_config
        from anylabeling.services.auto_labeling.model_manager import ModelManager
    except Exception as exc:  # pragma: no cover - environment dependent
        raise InspectionError(
            "Could not import X-AnyLabeling. Install the package in the current "
            "environment, for example with the CPU extra, before running this "
            f"script. Import error: {exc}"
        ) from exc
    return app_config, config_pkg, load_model_config, ModelManager, list(_CUSTOM_MODELS)


def _distribution_version() -> Optional[str]:
    try:
        return metadata.version("x-anylabeling-cvhub")
    except metadata.PackageNotFoundError:
        return None


def _read_yaml(load_model_config, text: str) -> Any:
    data = load_model_config(text)
    if data is None:
        return {}
    return data


def _load_registry_configs(config_pkg, load_model_config) -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    models_text = resources.files(config_pkg).joinpath("models.yaml").read_text(encoding="utf-8")
    registry = _read_yaml(load_model_config, models_text)
    if not isinstance(registry, list):
        raise InspectionError("Installed models.yaml did not parse to a list.")

    configs: List[Dict[str, Any]] = []
    for index, entry in enumerate(registry):
        if not isinstance(entry, dict):
            warnings.append(f"registry entry {index} is not a mapping; skipped")
            continue
        config_file = entry.get("config_file")
        if not isinstance(config_file, str):
            warnings.append(f"registry entry {index} has no string config_file; skipped")
            continue
        try:
            if config_file.startswith(":/"):
                name = config_file[2:]
                text = (
                    resources.files(config_pkg)
                    .joinpath("auto_labeling", name)
                    .read_text(encoding="utf-8")
                )
            else:
                text = Path(config_file).read_text(encoding="utf-8")
            cfg = _read_yaml(load_model_config, text)
            if not isinstance(cfg, dict):
                warnings.append(f"{config_file} did not parse to a mapping; skipped")
                continue
            cfg = dict(cfg)
            cfg["config_file"] = config_file
            cfg["_registry_model_name"] = entry.get("model_name")
            configs.append(cfg)
        except Exception as exc:
            warnings.append(f"could not read {config_file}: {exc}")
    return configs, warnings


@contextmanager
def _temporary_or_user_work_dir(path: Optional[str]) -> Iterator[Tuple[str, bool]]:
    if path:
        work_dir = os.path.abspath(os.path.expanduser(path))
        os.makedirs(work_dir, exist_ok=True)
        yield work_dir, False
    else:
        with tempfile.TemporaryDirectory(prefix="xanylabeling-config-") as tmp:
            yield tmp, True


def _load_model_manager_count(app_config, ModelManager, work_dir: str) -> Dict[str, Any]:
    """Load ModelManager config list without model weights/downloads."""
    old_current = getattr(app_config, "current_config_file", None)
    old_work_dir = app_config.get_work_directory()
    try:
        app_config.set_work_directory(work_dir)
        app_config.current_config_file = os.path.join(work_dir, ".xanylabelingrc")
        manager = ModelManager()
        configs = manager.get_model_configs()
        return {
            "work_dir_kind": "temporary-or-user-supplied",
            "count": len(configs),
            "type_counts": dict(Counter(c.get("type", "<missing>") for c in configs)),
            "duplicate_names": sorted(
                name
                for name, count in Counter(c.get("name") for c in configs).items()
                if name is not None and count > 1
            ),
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"count": None, "type_counts": {}, "duplicate_names": [], "error": str(exc)}
    finally:
        try:
            app_config.set_work_directory(old_work_dir)
        except Exception:
            pass
        app_config.current_config_file = old_current


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _resolve_local_path(value: str, config_file: Path) -> Dict[str, Any]:
    if _is_url(value):
        return {"value": value, "kind": "url", "exists": None}
    if not value or value.startswith(":/"):
        return {"value": value, "kind": "special-or-empty", "exists": None}
    candidates = [Path(value).expanduser()]
    if not Path(value).is_absolute():
        candidates.append((config_file.parent / value).expanduser())
    resolved = [str(p.resolve()) for p in candidates]
    exists = any(Path(p).exists() for p in candidates)
    return {"value": value, "kind": "local", "exists": exists, "checked": resolved}


def _validate_custom_config(
    path: str,
    load_model_config,
    ModelManager,
    custom_types: Iterable[str],
) -> Dict[str, Any]:
    config_path = Path(path).expanduser()
    result: Dict[str, Any] = {
        "path": str(config_path),
        "parse_ok": False,
        "valid_minimum_custom_format": False,
        "errors": [],
        "warnings": [],
        "fields": {},
        "path_fields": {},
    }
    try:
        text = config_path.read_text(encoding="utf-8")
        data = _read_yaml(load_model_config, text)
    except Exception as exc:
        result["errors"].append(f"could not parse/read YAML: {exc}")
        return result
    if not isinstance(data, dict):
        result["errors"].append("YAML root must be a mapping/object")
        return result

    result["parse_ok"] = True
    for field in ("type", "name", "display_name"):
        value = data.get(field)
        present = field in data
        result["fields"][field] = {"present": present, "value": value}
        if not present:
            result["errors"].append(f"missing required custom field: {field}")
    name = data.get("name")
    model_type = data.get("type")
    name_valid = ModelManager.is_valid_custom_model_name(name)
    type_supported = isinstance(model_type, str) and model_type in set(custom_types)
    result["name_valid"] = bool(name_valid)
    result["type_supported_for_config_only_custom_load"] = bool(type_supported)
    if "name" in data and not name_valid:
        result["errors"].append(
            "invalid custom name: use one path segment containing only letters, "
            "numbers, dots, underscores, and hyphens; not '.' or '..'"
        )
    if "type" in data and not type_supported:
        result["warnings"].append(
            "type is not in the custom-capable type list; config-only loading "
            "will fail unless source code adds an adapter for this type"
        )

    for key, value in sorted(data.items()):
        if key in PATH_FIELD_NAMES or key.endswith("_path"):
            if isinstance(value, str):
                result["path_fields"][key] = _resolve_local_path(value, config_path)
            else:
                result["path_fields"][key] = {
                    "value": value,
                    "kind": "non-string",
                    "exists": None,
                }
                result["warnings"].append(f"path-like field {key!r} is not a string")

    result["valid_minimum_custom_format"] = (
        result["parse_ok"]
        and all(result["fields"].get(k, {}).get("present") for k in ("type", "name", "display_name"))
        and bool(name_valid)
        and bool(type_supported)
    )
    return result


def _build_report(args: argparse.Namespace) -> Dict[str, Any]:
    app_config, config_pkg, load_model_config, ModelManager, custom_types = _load_dependencies()
    configs, warnings = _load_registry_configs(config_pkg, load_model_config)
    names = [cfg.get("name") for cfg in configs]
    type_counts = Counter(cfg.get("type", "<missing>") for cfg in configs)

    with _temporary_or_user_work_dir(args.work_dir) as (work_dir, is_temp):
        model_manager = _load_model_manager_count(app_config, ModelManager, work_dir)
        model_manager["work_dir"] = work_dir if args.json else ("temporary" if is_temp else work_dir)

    name_examples = {
        example: ModelManager.is_valid_custom_model_name(example)
        for example in CUSTOM_NAME_EXAMPLES
    }

    custom_validations = [
        _validate_custom_config(path, load_model_config, ModelManager, custom_types)
        for path in args.custom_config
    ]

    return {
        "package": {
            "distribution": "x-anylabeling-cvhub",
            "version": _distribution_version(),
        },
        "registry": {
            "count": len(configs),
            "type_counts": dict(sorted(type_counts.items())),
            "duplicate_names": sorted(
                str(name)
                for name, count in Counter(names).items()
                if name is not None and count > 1
            ),
            "missing_required_top_level_fields": [
                {
                    "config_file": cfg.get("config_file"),
                    "missing": [k for k in ("type", "name", "display_name") if k not in cfg],
                }
                for cfg in configs
                if any(k not in cfg for k in ("type", "name", "display_name"))
            ],
            "warnings": warnings,
        },
        "model_manager_config_load": model_manager,
        "custom_model_rules": {
            "max_custom_models": getattr(ModelManager, "MAX_NUM_CUSTOM_MODELS", None),
            "name_validation_examples": name_examples,
            "custom_capable_type_count": len(custom_types),
        },
        "custom_config_validations": custom_validations,
    }


def _print_text(report: Dict[str, Any], show_types: bool) -> None:
    pkg = report["package"]
    print(f"Package: {pkg['distribution']} {pkg.get('version') or '<not installed metadata>'}")
    reg = report["registry"]
    print(f"Registry configs parsed: {reg['count']}")
    mm = report["model_manager_config_load"]
    if mm.get("error"):
        print(f"ModelManager config load: ERROR: {mm['error']}")
    else:
        print(f"ModelManager config load count: {mm['count']}")
    duplicates = reg.get("duplicate_names") or []
    print("Duplicate config names: " + (", ".join(duplicates) if duplicates else "none"))
    if reg.get("warnings"):
        print("Registry warnings:")
        for warning in reg["warnings"]:
            print(f"  - {warning}")

    print("\nCustom-name validation examples:")
    for name, ok in report["custom_model_rules"]["name_validation_examples"].items():
        label = repr(name)
        print(f"  {label}: {'valid' if ok else 'invalid'}")
    print(f"Max retained custom models: {report['custom_model_rules']['max_custom_models']}")
    print(f"Custom-capable type count: {report['custom_model_rules']['custom_capable_type_count']}")

    if show_types:
        print("\nType counts:")
        for model_type, count in sorted(reg["type_counts"].items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {model_type}: {count}")

    validations = report.get("custom_config_validations") or []
    if validations:
        print("\nCustom config validation:")
    for item in validations:
        print(f"  {item['path']}")
        print(f"    parse_ok: {item['parse_ok']}")
        print(f"    valid_minimum_custom_format: {item['valid_minimum_custom_format']}")
        if item.get("fields"):
            for field, meta in item["fields"].items():
                print(f"    {field}: {'present' if meta['present'] else 'missing'} ({meta.get('value')!r})")
        if item.get("path_fields"):
            print("    path fields:")
            for field, meta in item["path_fields"].items():
                exists = meta.get("exists")
                exists_text = "n/a" if exists is None else ("exists" if exists else "missing")
                print(f"      {field}: {meta.get('kind')} {exists_text} {meta.get('value')!r}")
        for error in item.get("errors", []):
            print(f"    ERROR: {error}")
        for warning in item.get("warnings", []):
            print(f"    WARNING: {warning}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed X-AnyLabeling model configs safely, without "
            "loading model weights or downloading model files."
        )
    )
    parser.add_argument(
        "--work-dir",
        help=(
            "Temporary X-AnyLabeling config directory used for ModelManager "
            "config-list initialization. If omitted, a temporary directory is "
            "created and removed. Supplying a directory may create/update its "
            ".xanylabelingrc."
        ),
    )
    parser.add_argument(
        "--show-types",
        action="store_true",
        help="Print registry model type counts in text output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full report as JSON.",
    )
    parser.add_argument(
        "--custom-config",
        action="append",
        default=[],
        help=(
            "Validate a custom model YAML without loading weights. May be "
            "specified multiple times."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        report = _build_report(args)
    except InspectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _print_text(report, args.show_types)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
