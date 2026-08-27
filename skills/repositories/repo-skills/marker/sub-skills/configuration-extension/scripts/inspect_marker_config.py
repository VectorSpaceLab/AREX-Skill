#!/usr/bin/env python3
"""Inspect Marker ConfigParser behavior without running conversion.

Accepts either a JSON file path or inline JSON object representing the CLI/options
mapping that would be passed to marker.config.parser.ConfigParser. The script
prints generated config keys and downstream class selections only; it does not
open input documents, create model artifacts, call LLM services, or convert files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


cwd = str(Path.cwd())
if cwd not in sys.path:
    sys.path.insert(0, cwd)


def _load_options(args: argparse.Namespace) -> dict[str, Any]:
    sources = [bool(args.config_json), bool(args.inline_json)]
    if sum(sources) != 1:
        raise SystemExit("Provide exactly one of --config-json or --inline-json.")

    if args.config_json:
        try:
            text = Path(args.config_json).read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"Could not read JSON config {args.config_json!r}: {exc}") from exc
    else:
        text = args.inline_json

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc

    if not isinstance(loaded, dict):
        raise SystemExit("The JSON value must be an object mapping option names to values.")
    return loaded


def _class_path(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    module = getattr(obj, "__module__", None)
    name = getattr(obj, "__name__", None)
    if module and name:
        return f"{module}.{name}"
    return repr(obj)


def _import_class(path: str) -> type:
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _processor_status(processors: list[str] | None) -> list[dict[str, str]]:
    if not processors:
        return []
    status = []
    for path in processors:
        try:
            cls = _import_class(path)
            status.append({"path": path, "status": "ok", "class": _class_path(cls) or path})
        except Exception as exc:  # noqa: BLE001 - inspection should report arbitrary import errors.
            status.append({"path": path, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Marker ConfigParser output without running conversion."
    )
    parser.add_argument(
        "--config-json",
        help="Path to a JSON object containing ConfigParser CLI/options values.",
    )
    parser.add_argument(
        "--inline-json",
        help="Inline JSON object containing ConfigParser CLI/options values.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    args = parser.parse_args(argv)

    options = _load_options(args)

    try:
        from marker.config.parser import ConfigParser
    except Exception as exc:  # noqa: BLE001 - expose import/setup failures clearly.
        raise SystemExit(f"Could not import marker.config.parser.ConfigParser: {exc}") from exc

    config_parser = ConfigParser(options)
    result: dict[str, Any] = {"input_options": options}
    errors: dict[str, str] = {}

    try:
        generated_config = config_parser.generate_config_dict()
        result["generated_config"] = generated_config
        result["generated_config_keys"] = sorted(generated_config.keys())
    except Exception as exc:  # noqa: BLE001
        errors["generate_config_dict"] = f"{type(exc).__name__}: {exc}"

    try:
        renderer = config_parser.get_renderer()
        result["renderer"] = renderer
    except Exception as exc:  # noqa: BLE001
        errors["get_renderer"] = f"{type(exc).__name__}: {exc}"

    processors = None
    try:
        processors = config_parser.get_processors()
        result["processors"] = processors
        result["processor_imports"] = _processor_status(processors)
    except Exception as exc:  # noqa: BLE001
        errors["get_processors"] = f"{type(exc).__name__}: {exc}"
        raw_processors = options.get("processors")
        if isinstance(raw_processors, str):
            result["processor_imports"] = _processor_status(raw_processors.split(","))

    try:
        converter_cls = config_parser.get_converter_cls()
        result["converter_class_path"] = _class_path(converter_cls)
    except Exception as exc:  # noqa: BLE001
        errors["get_converter_cls"] = f"{type(exc).__name__}: {exc}"

    try:
        result["llm_service"] = config_parser.get_llm_service()
    except Exception as exc:  # noqa: BLE001
        errors["get_llm_service"] = f"{type(exc).__name__}: {exc}"

    result["errors"] = errors
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True, default=str))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
