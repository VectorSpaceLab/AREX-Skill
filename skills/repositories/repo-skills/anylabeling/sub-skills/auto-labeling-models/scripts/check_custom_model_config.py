#!/usr/bin/env python3
"""Validate an AnyLabeling custom auto-labeling model config without downloads.

This helper is intentionally read-only. It checks the YAML shape that
AnyLabeling's custom-model loader expects, resolves referenced local files when
possible, and optionally inspects an already-present ONNX decoder to report the
SAM-family variant that AnyLabeling would infer.

Examples:
  python check_custom_model_config.py /path/to/config.yaml
  python check_custom_model_config.py /path/to/config.yaml --json
  python check_custom_model_config.py /path/to/config.yaml --model-cache ~/anylabeling_data/models
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_TYPES = {"segment_anything", "yolov5", "yolov8"}
COMMON_REQUIRED = {"type", "name", "display_name"}
SEGMENT_REQUIRED = {"encoder_model_path", "decoder_model_path"}
YOLO_REQUIRED = {
    "model_path",
    "input_width",
    "input_height",
    "score_threshold",
    "nms_threshold",
    "confidence_threshold",
    "classes",
}


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if text[0:1] in {'"', "'"} and text[-1:] == text[0]:
        return text[1:-1]
    low = text.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none", "~"}:
        return None
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in inner.split(",")]
    try:
        if any(ch in text for ch in (".", "e", "E")):
            return float(text)
        return int(text)
    except ValueError:
        return text


def _simple_yaml_mapping(raw: str) -> dict[str, Any]:
    """Very small fallback for flat AnyLabeling custom config YAML."""
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[Any] | None = None
    for raw_line in raw.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent and current_key and current_list is not None and stripped.startswith("- "):
            current_list.append(_parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise ValueError(f"unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            current_key = key
            current_list = []
            data[key] = current_list
        else:
            current_key = None
            current_list = None
            data[key] = _parse_scalar(value)
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        import yaml  # type: ignore
    except ImportError:
        data = _simple_yaml_mapping(raw)
    else:
        data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("custom model config must be a YAML mapping")
    return data


def resolve_model_path(config_path: Path, cfg: dict[str, Any], field: str, model_cache: Path | None) -> dict[str, Any]:
    value = cfg.get(field)
    result: dict[str, Any] = {"field": field, "value": value, "status": "missing"}
    if not isinstance(value, str) or not value:
        return result

    candidates: list[Path] = []
    raw = Path(value).expanduser()
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append((config_path.parent / raw).resolve())
        if model_cache is not None and isinstance(cfg.get("name"), str):
            candidates.append((model_cache.expanduser() / cfg["name"] / raw).resolve())

    for candidate in candidates:
        if candidate.is_file():
            result.update({"status": "file", "resolved": str(candidate)})
            return result
        if candidate.is_dir():
            result.update({"status": "directory", "resolved": str(candidate)})
            return result
    result.update({"status": "not_found", "checked": [str(p) for p in candidates]})
    return result


def inspect_decoder_variant(path: Path) -> dict[str, Any]:
    try:
        import onnx  # type: ignore
    except ImportError:
        return {"status": "skipped", "reason": "onnx package is not installed"}
    try:
        model = onnx.load(str(path))
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"status": "error", "reason": str(exc)}
    input_names = sorted({inp.name for inp in model.graph.input})
    if "backbone_fpn_0" in input_names or "language_mask" in input_names:
        variant = "sam3"
    elif "high_res_feats_0" in input_names:
        variant = "sam2"
    else:
        variant = "sam-or-unknown"
    return {"status": "inspected", "variant": variant, "input_names": input_names}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    config_path = Path(args.config).expanduser().resolve()
    cfg = load_yaml(config_path)
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    missing_common = sorted(COMMON_REQUIRED - set(cfg))
    if missing_common:
        errors.append("missing required common fields: " + ", ".join(missing_common))

    model_type = cfg.get("type")
    if model_type not in ALLOWED_TYPES:
        errors.append(f"unsupported type {model_type!r}; expected one of {sorted(ALLOWED_TYPES)}")

    if model_type == "segment_anything":
        missing = sorted(SEGMENT_REQUIRED - set(cfg))
        if missing:
            errors.append("missing segment_anything fields: " + ", ".join(missing))
        if "language_encoder_path" in cfg:
            info.append("language_encoder_path is present, so AnyLabeling treats this as SAM3-capable")
        elif args.expect_variant == "sam3":
            warnings.append("expected SAM3 but language_encoder_path is absent; decoder ONNX inputs must prove SAM3")
        if "input_size" not in cfg or "max_width" not in cfg or "max_height" not in cfg:
            warnings.append("segment_anything config usually needs input_size, max_width, and max_height for runtime initialization")
    elif model_type in {"yolov5", "yolov8"}:
        missing = sorted(YOLO_REQUIRED - set(cfg))
        if missing:
            errors.append(f"missing {model_type} fields: " + ", ".join(missing))
        classes = cfg.get("classes")
        if not isinstance(classes, list) or not all(isinstance(item, str) for item in classes):
            warnings.append("classes should be a YAML list of class-name strings")

    path_fields = []
    for key in sorted(k for k in cfg if k == "model_path" or k.endswith("_path")):
        if key in {"config_file"}:
            continue
        path_fields.append(resolve_model_path(config_path, cfg, key, Path(args.model_cache) if args.model_cache else None))

    decoder_variant = {"status": "not_applicable"}
    decoder_entries = [p for p in path_fields if p["field"] == "decoder_model_path" and p["status"] == "file"]
    if decoder_entries and not args.skip_onnx_inspection:
        decoder_variant = inspect_decoder_variant(Path(decoder_entries[0]["resolved"]))
        if decoder_variant.get("status") == "inspected":
            variant = decoder_variant.get("variant")
            if args.expect_variant != "auto" and variant != args.expect_variant:
                warnings.append(f"decoder appears to be {variant}, not expected {args.expect_variant}")
            if model_type == "segment_anything" and variant == "sam3" and "language_encoder_path" not in cfg:
                warnings.append("decoder looks like SAM3 but language_encoder_path is missing; text prompts will not have a language encoder path")

    missing_paths = [p for p in path_fields if p["status"] in {"missing", "not_found"}]
    if missing_paths:
        message = (
            "some model path fields are absent or not found locally; custom configs "
            "should point to usable files because AnyLabeling treats them as already downloaded"
        )
        if args.allow_missing_files:
            warnings.append(message)
        else:
            errors.append(message)

    return {
        "config": str(config_path),
        "type": model_type,
        "name": cfg.get("name"),
        "display_name": cfg.get("display_name"),
        "path_fields": path_fields,
        "decoder_variant": decoder_variant,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "ok": not errors,
    }


def print_text(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "ERROR"
    print(f"{status}: {report['config']}")
    print(f"type={report.get('type')!r} name={report.get('name')!r} display_name={report.get('display_name')!r}")
    for entry in report["path_fields"]:
        print(f"path {entry['field']}: {entry['status']} {entry.get('resolved') or entry.get('value') or ''}")
    variant = report["decoder_variant"]
    if variant.get("status") == "inspected":
        print(f"decoder_variant={variant.get('variant')} inputs={', '.join(variant.get('input_names', [])[:12])}")
    elif variant.get("status") not in {"not_applicable"}:
        print(f"decoder_variant={variant.get('status')}: {variant.get('reason', '')}")
    for key in ("info", "warnings", "errors"):
        for message in report[key]:
            print(f"{key[:-1].upper()}: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="custom AnyLabeling model config.yaml to inspect")
    parser.add_argument("--model-cache", default="~/anylabeling_data/models", help="model cache root used when resolving relative model paths by model name")
    parser.add_argument("--expect-variant", choices=["auto", "sam", "sam2", "sam3"], default="auto", help="expected SAM-family decoder variant when decoder inspection is possible")
    parser.add_argument("--skip-onnx-inspection", action="store_true", help="do not import onnx or inspect decoder inputs")
    parser.add_argument("--allow-missing-files", action="store_true", help="warn rather than fail when referenced model files are not present")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    try:
        report = build_report(args)
    except Exception as exc:  # noqa: BLE001 - diagnostic CLI
        if args.json:
            print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
