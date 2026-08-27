#!/usr/bin/env python3
"""Dry-run Marker ConfigParser LLM service resolution without provider API calls."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, get_args, get_origin

DEFAULT_SERVICE = "marker.services.gemini.GoogleGeminiService"

FALLBACK_SERVICE_METADATA: dict[str, dict[str, Any]] = {
    "marker.services.gemini.GoogleGeminiService": {
        "required": ["gemini_api_key"],
        "defaults": {"gemini_model_name": "gemini-2.0-flash", "timeout": 30, "max_retries": 2, "retry_wait_time": 3},
    },
    "marker.services.vertex.GoogleVertexService": {
        "required": ["vertex_project_id"],
        "defaults": {"vertex_location": "us-central1", "gemini_model_name": "gemini-2.0-flash-001", "vertex_dedicated": False, "timeout": 30, "max_retries": 2, "retry_wait_time": 3},
    },
    "marker.services.ollama.OllamaService": {
        "required": [],
        "defaults": {"ollama_base_url": "http://localhost:11434", "ollama_model": "llama3.2-vision"},
    },
    "marker.services.claude.ClaudeService": {
        "required": ["claude_api_key"],
        "defaults": {"claude_model_name": "claude-3-7-sonnet-20250219", "max_claude_tokens": 8192, "timeout": 30, "max_retries": 2, "retry_wait_time": 3},
    },
    "marker.services.openai.OpenAIService": {
        "required": ["openai_api_key"],
        "defaults": {"openai_base_url": "https://api.openai.com/v1", "openai_model": "gpt-4o-mini", "openai_image_format": "webp", "timeout": 30, "max_retries": 2, "retry_wait_time": 3},
    },
    "marker.services.azure_openai.AzureOpenAIService": {
        "required": ["azure_endpoint", "azure_api_key", "azure_api_version", "deployment_name"],
        "defaults": {"timeout": 30, "max_retries": 2, "retry_wait_time": 3},
    },
}


def import_marker_bits():
    try:
        from marker.config.parser import ConfigParser
        from marker.services import BaseService
    except Exception as exc:  # pragma: no cover - depends on installed marker extras
        return None, None, str(exc)
    return ConfigParser, BaseService, None


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def load_config_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config JSON must contain an object")
    return data


def import_class(path: str) -> type:
    module_name, class_name = path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def annotated_base(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is not None and getattr(origin, "__name__", "") == "Annotated":
        args = get_args(annotation)
        return args[0] if args else annotation
    return annotation


def required_config_fields(service_cls: type) -> list[str]:
    required: list[str] = []
    for cls in reversed(service_cls.mro()):
        for name, annotation in inspect.get_annotations(cls).items():
            base = annotated_base(annotation)
            if base is str and getattr(service_cls, name, None) is None:
                required.append(name)
    return sorted(set(required))


def visible_defaults(service_cls: type) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for cls in reversed(service_cls.mro()):
        for name in inspect.get_annotations(cls):
            value = getattr(service_cls, name, None)
            if value is not None and isinstance(value, (str, int, float, bool)):
                defaults[name] = value
    return defaults


def fallback_generate_config(options: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in options.items() if value not in (None, False, "")}


def fallback_get_llm_service(options: dict[str, Any]) -> str | None:
    if not options.get("use_llm", False):
        return None
    return options.get("llm_service") or DEFAULT_SERVICE


def collect_options(args: argparse.Namespace) -> dict[str, Any]:
    options = load_config_json(args.config_json)
    for key, value in vars(args).items():
        if key in {"config_json", "set"}:
            continue
        if value is not None and value is not False:
            options[key] = value

    for item in args.set:
        if "=" not in item:
            raise ValueError(f"--set expects KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        options[key] = parse_scalar(value)
    return options


def print_probe_result(
    *,
    options: dict[str, Any],
    generated: dict[str, Any],
    service_path: str | None,
    service_label: str | None,
    required: list[str],
    defaults: dict[str, Any],
    mode_note: str | None,
) -> int:
    print(f"use_llm: {bool(options.get('use_llm'))}")
    print(f"resolved llm_service: {service_path if service_path else 'None'}")
    if mode_note:
        print(f"NOTE: {mode_note}")
    if service_path is None:
        print("NOTE: Marker will not instantiate an LLM service unless use_llm is true.")
        return 0

    missing = [name for name in required if generated.get(name) is None]
    print(f"service class: {service_label or service_path}")
    print(f"required config fields: {', '.join(required) if required else '(none)'}")
    if missing:
        print(f"MISSING: {', '.join(missing)}")
    else:
        print("required config status: satisfied")

    if defaults:
        print("class defaults:")
        for key in sorted(defaults):
            display = "***" if "key" in key.lower() else defaults[key]
            print(f"  {key}: {display}")

    provider_keys = sorted(
        key for key in generated if any(token in key for token in ["api", "model", "vertex", "ollama", "azure", "openai", "claude", "gemini", "timeout", "retries", "retry"])
    )
    if provider_keys:
        print("provided provider-related keys:")
        for key in provider_keys:
            display = "***" if "key" in key.lower() else generated[key]
            print(f"  {key}: {display}")

    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Marker LLM config resolution without creating a provider client or sending requests."
    )
    parser.add_argument("--config-json", help="JSON object with Marker config values")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="Additional config value; may be repeated")
    parser.add_argument("--use_llm", action="store_true", help="Enable LLM service resolution")
    parser.add_argument("--llm_service", help="Full Marker LLM service class path")
    parser.add_argument("--gemini_api_key")
    parser.add_argument("--vertex_project_id")
    parser.add_argument("--vertex_location")
    parser.add_argument("--ollama_base_url")
    parser.add_argument("--ollama_model")
    parser.add_argument("--claude_api_key")
    parser.add_argument("--claude_model_name")
    parser.add_argument("--openai_api_key")
    parser.add_argument("--openai_model")
    parser.add_argument("--openai_base_url")
    parser.add_argument("--openai_image_format")
    parser.add_argument("--azure_endpoint")
    parser.add_argument("--azure_api_key")
    parser.add_argument("--azure_api_version")
    parser.add_argument("--deployment_name")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--max_retries", type=int)
    parser.add_argument("--retry_wait_time", type=int)
    parser.add_argument("--max_output_tokens", type=int)
    args = parser.parse_args()

    try:
        options = collect_options(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    ConfigParser, BaseService, import_error = import_marker_bits()
    if ConfigParser is None:
        generated = fallback_generate_config(options)
        service_path = fallback_get_llm_service(options)
        if service_path is not None and service_path not in FALLBACK_SERVICE_METADATA:
            print(
                f"ERROR: marker-pdf is not importable ({import_error}) and fallback metadata does not know {service_path!r}",
                file=sys.stderr,
            )
            return 1
        metadata = FALLBACK_SERVICE_METADATA.get(service_path or "", {"required": [], "defaults": {}})
        return print_probe_result(
            options=options,
            generated=generated,
            service_path=service_path,
            service_label=service_path,
            required=list(metadata["required"]),
            defaults=dict(metadata["defaults"]),
            mode_note=f"marker-pdf import failed ({import_error}); using bundled Marker 1.10.2 service metadata fallback",
        )

    parser_obj = ConfigParser(options)
    generated = parser_obj.generate_config_dict()
    service_path = parser_obj.get_llm_service()
    if service_path is None:
        return print_probe_result(
            options=options,
            generated=generated,
            service_path=None,
            service_label=None,
            required=[],
            defaults={},
            mode_note=None,
        )

    try:
        service_cls = import_class(service_path)
    except Exception as exc:
        print(f"ERROR: could not import service class {service_path!r}: {exc}", file=sys.stderr)
        return 1

    if not issubclass(service_cls, BaseService):
        print(f"ERROR: {service_path} is not a marker.services.BaseService subclass", file=sys.stderr)
        return 1

    return print_probe_result(
        options=options,
        generated=generated,
        service_path=service_path,
        service_label=f"{service_cls.__module__}.{service_cls.__name__}",
        required=required_config_fields(service_cls),
        defaults=visible_defaults(service_cls),
        mode_note="using installed marker-pdf ConfigParser",
    )


if __name__ == "__main__":
    raise SystemExit(main())
