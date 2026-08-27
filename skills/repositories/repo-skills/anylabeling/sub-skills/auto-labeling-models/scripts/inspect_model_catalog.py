#!/usr/bin/env python3
"""Read-only inspection for AnyLabeling auto-labeling model catalogs.

The script performs no downloads and does not import PyQt or model modules. It can
inspect a supplied models.yaml file or, when AnyLabeling is installed, locate the
packaged catalog through importlib metadata.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_ALLOWED_TYPES = ("segment_anything", "yolov5", "yolov8")
CATALOG_REQUIRED_FIELDS = ("name", "display_name", "download_url", "type")
PATH_FIELD_SUFFIXES = ("_path",)


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


def _simple_yaml_load(raw: str) -> Any:
    """Tiny fallback parser for the flat YAML maps used by model configs.

    It supports a top-level list of flat mappings or one flat mapping. PyYAML is
    preferred when installed; this fallback keeps --help and basic diagnostics
    usable in minimal Python environments.
    """
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    mapping: dict[str, Any] = {}
    saw_list = False
    for raw_line in raw.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            saw_list = True
            if current is not None:
                items.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if stripped:
                if ":" not in stripped:
                    raise ValueError(f"unsupported YAML list item: {raw_line!r}")
                key, value = stripped.split(":", 1)
                current[key.strip()] = _parse_scalar(value)
            continue
        if ":" not in stripped:
            raise ValueError(f"unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        target = current if saw_list else mapping
        if target is None:
            raise ValueError(f"mapping entry before list item: {raw_line!r}")
        target[key.strip()] = _parse_scalar(value)
    if saw_list:
        if current is not None:
            items.append(current)
        return items
    return mapping


def load_yaml(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        import yaml  # type: ignore
    except ImportError:
        return _simple_yaml_load(raw)
    return yaml.safe_load(raw)


def find_packaged_catalog() -> Path | None:
    spec = importlib.util.find_spec("anylabeling")
    if spec is None or not spec.submodule_search_locations:
        return None
    package_root = Path(next(iter(spec.submodule_search_locations)))
    candidate = package_root / "configs" / "auto_labeling" / "models.yaml"
    return candidate if candidate.is_file() else None


def resolve_catalog_path(arg_path: str | None, package_root: str | None) -> Path:
    if arg_path:
        return Path(arg_path).expanduser().resolve()
    if package_root:
        root = Path(package_root).expanduser().resolve()
        candidate = root / "configs" / "auto_labeling" / "models.yaml"
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(
            f"no configs/auto_labeling/models.yaml found under package root: {root}"
        )
    candidate = find_packaged_catalog()
    if candidate is None:
        raise FileNotFoundError(
            "could not locate installed AnyLabeling catalog; pass a models.yaml path"
        )
    return candidate.resolve()


def download_source(url: str | None) -> str:
    if not url:
        return "none"
    if url.endswith(".zip"):
        return "zip"
    if url.startswith("https://huggingface.co"):
        return "huggingface"
    return "other"


def variant_hint(model: dict[str, Any]) -> str:
    model_type = model.get("type")
    name = str(model.get("name", "")).lower()
    url = str(model.get("download_url", "")).lower()
    decoder = str(model.get("decoder_model_path", "")).lower()
    encoder = str(model.get("encoder_model_path", "")).lower()
    if model_type == "yolov5":
        return "yolov5-rectangle-detector"
    if model_type == "yolov8":
        return "yolov8-rectangle-detector"
    if model_type != "segment_anything":
        return "unknown"
    if "language_encoder_path" in model:
        return "sam3-config"
    if "coreml" in name or "coreml" in url or "coreml" in decoder or decoder.endswith(".mlpackage") or encoder.endswith(".mlpackage"):
        return "sam2-coreml-candidate"
    if "decoder_model_path" in model:
        return "sam-decoder-probe-needed"
    return "download-config-required"


def path_fields(model: dict[str, Any]) -> list[str]:
    fields = []
    for key in model:
        if key == "model_path" or any(key.endswith(suffix) for suffix in PATH_FIELD_SUFFIXES):
            fields.append(key)
    return sorted(fields)


def inspect_entry(
    entry: dict[str, Any],
    index: int,
    allowed_types: set[str],
    cache_dir: Path | None,
) -> dict[str, Any]:
    base = dict(entry)
    merged = dict(base)
    errors: list[str] = []
    warnings: list[str] = []
    missing = [field for field in CATALOG_REQUIRED_FIELDS if field not in base]
    if missing:
        errors.append("missing catalog fields: " + ", ".join(missing))
    model_type = base.get("type")
    if model_type not in allowed_types:
        errors.append(f"type {model_type!r} is not in allowed types {sorted(allowed_types)}")

    cache_config = "not_checked"
    cache_has_downloaded: Any = None
    name = str(base.get("name", ""))
    if cache_dir is not None and name:
        cfg = cache_dir.expanduser() / name / "config.yaml"
        if cfg.is_file():
            cache_config = "present"
            try:
                cached = load_yaml(cfg)
                if isinstance(cached, dict):
                    merged.update(cached)
                    cache_has_downloaded = merged.get("has_downloaded")
                else:
                    warnings.append("cache config is not a mapping")
            except Exception as exc:  # noqa: BLE001 - diagnostic script
                warnings.append(f"could not read cache config: {exc}")
        else:
            cache_config = "absent"

    if merged.get("type") == "segment_anything" and not {
        "encoder_model_path",
        "decoder_model_path",
    }.issubset(merged):
        warnings.append(
            "segment_anything entry lacks encoder/decoder paths in inspected config; "
            "this is normal for pre-download built-ins but not for load-ready configs"
        )
    if merged.get("type") in {"yolov5", "yolov8"} and "model_path" not in merged:
        warnings.append(
            "YOLO entry lacks model_path in inspected config; this is normal only before a built-in download supplies a fuller config"
        )

    return {
        "index": index,
        "name": base.get("name"),
        "display_name": base.get("display_name"),
        "type": model_type,
        "download_source": download_source(base.get("download_url")),
        "variant_hint": variant_hint(merged),
        "path_fields": path_fields(merged),
        "cache_config": cache_config,
        "cache_has_downloaded": cache_has_downloaded,
        "errors": errors,
        "warnings": warnings,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    catalog_path = resolve_catalog_path(args.models_yaml, args.package_root)
    if not catalog_path.is_file():
        raise FileNotFoundError(f"catalog file not found: {catalog_path}")
    data = load_yaml(catalog_path)
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("catalog must be a YAML list of mappings")

    allowed_types = {part.strip() for part in args.allowed_types.split(",") if part.strip()}
    cache_dir = None if args.no_cache_check else Path(args.cache_dir).expanduser()
    entries = [
        inspect_entry(entry, i, allowed_types, cache_dir)
        for i, entry in enumerate(data, start=1)
    ]
    counts = Counter(entry.get("type") for entry in data)
    errors = sum(len(entry["errors"]) for entry in entries)
    warnings = sum(len(entry["warnings"]) for entry in entries)
    return {
        "catalog_path": str(catalog_path),
        "entry_count": len(data),
        "type_counts": dict(sorted(counts.items(), key=lambda item: str(item[0]))),
        "allowed_types": sorted(allowed_types),
        "cache_checked": cache_dir is not None,
        "entries": entries,
        "error_count": errors,
        "warning_count": warnings,
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Catalog: {report['catalog_path']}")
    print(f"Entries: {report['entry_count']}")
    print("Types:")
    for model_type, count in report["type_counts"].items():
        print(f"  {model_type}: {count}")
    print("Allowed registry/custom-check types: " + ", ".join(report["allowed_types"]))
    print(f"Cache checked: {'yes' if report['cache_checked'] else 'no'}")
    print(f"Errors: {report['error_count']}  Warnings: {report['warning_count']}")
    print("\nModels:")
    for entry in report["entries"]:
        fields = ",".join(entry["path_fields"]) if entry["path_fields"] else "none"
        print(
            f"  {entry['index']:02d}. {entry.get('name')} "
            f"[{entry.get('type')}] variant={entry['variant_hint']} "
            f"download={entry['download_source']} cache={entry['cache_config']} "
            f"has_downloaded={entry['cache_has_downloaded']} path_fields={fields}"
        )
        for message in entry["errors"]:
            print(f"      ERROR: {message}")
        for message in entry["warnings"]:
            print(f"      WARN: {message}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize an AnyLabeling auto-labeling models.yaml catalog without "
            "downloading models or importing UI/model modules."
        )
    )
    parser.add_argument(
        "models_yaml",
        nargs="?",
        help="Path to models.yaml. If omitted, locate the catalog from an installed AnyLabeling package.",
    )
    parser.add_argument(
        "--package-root",
        help="Path to an anylabeling package directory containing configs/auto_labeling/models.yaml.",
    )
    parser.add_argument(
        "--cache-dir",
        default=os.path.join("~", "anylabeling_data", "models"),
        help="Model cache root used only for reading already-present config.yaml files.",
    )
    parser.add_argument(
        "--no-cache-check",
        action="store_true",
        help="Do not inspect local model-cache config.yaml files.",
    )
    parser.add_argument(
        "--allowed-types",
        default=",".join(DEFAULT_ALLOWED_TYPES),
        help="Comma-separated model type allow-list for diagnostics.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit non-zero when warnings are present, not only errors.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = build_report(args)
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if report["error_count"]:
        return 1
    if args.fail_on_warnings and report["warning_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
