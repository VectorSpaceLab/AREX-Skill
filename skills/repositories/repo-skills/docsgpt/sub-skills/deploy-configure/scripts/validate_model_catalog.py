#!/usr/bin/env python3
"""Offline structural validator for DocsGPT model catalog YAML files.

This intentionally does not import DocsGPT or contact providers. It catches
common catalog mistakes before a restart; application startup remains the
canonical full schema check.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("PyYAML is required: python -m pip install PyYAML")

ALLOWED_TOP = {"provider", "display_provider", "api_key_env", "base_url", "defaults", "models"}
CAPABILITIES = {
    "supports_tools", "supports_structured_output", "supports_streaming",
    "attachments", "context_window", "input_cost_per_token", "output_cost_per_token",
    "reasoning_effort", "api_flavor",
}
MODEL_FIELDS = CAPABILITIES | {
    "id", "display_name", "description", "enabled", "base_url", "upstream_model_id", "aliases"
}
EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh"}
FLAVORS = {"chat_completions", "responses"}
DEFAULT_ALIASES = {"image", "pdf", "audio"}
BUILTIN_PROVIDERS = {
    "anthropic", "docsgpt", "google", "groq", "huggingface", "llama.cpp",
    "novita", "openai", "openai_compatible", "openrouter",
}


def validate_caps(obj: object, where: str, aliases: set[str], errors: list[str]) -> None:
    if obj is None:
        return
    if not isinstance(obj, dict):
        errors.append(f"{where}: must be a mapping")
        return
    unknown = set(obj) - CAPABILITIES
    if unknown:
        errors.append(f"{where}: unknown capability fields {sorted(unknown)}")
    effort = obj.get("reasoning_effort")
    if effort is not None and effort not in EFFORTS:
        errors.append(f"{where}: invalid reasoning_effort {effort!r}")
    flavor = obj.get("api_flavor")
    if flavor is not None and flavor not in FLAVORS:
        errors.append(f"{where}: invalid api_flavor {flavor!r}")
    attachments = obj.get("attachments", [])
    if not isinstance(attachments, list):
        errors.append(f"{where}: attachments must be a list")
    else:
        for item in attachments:
            if not isinstance(item, str) or ("/" not in item and item not in aliases):
                errors.append(f"{where}: unknown attachment alias/MIME {item!r}")


def validate(
    path: Path,
    seen: dict[str, Path],
    aliases: set[str],
    warnings: list[str],
) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as error:
        return [f"{path}: invalid YAML: {error}"]
    if not isinstance(data, dict):
        return [f"{path}: top level must be a mapping"]
    unknown = set(data) - ALLOWED_TOP
    if unknown:
        errors.append(f"{path}: unknown top-level fields {sorted(unknown)}")
    provider = data.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        errors.append(f"{path}: provider must be a non-empty string")
    elif provider not in BUILTIN_PROVIDERS:
        errors.append(f"{path}: provider {provider!r} is not registered in this DocsGPT snapshot")
    if provider == "openai_compatible":
        for field in ("display_provider", "api_key_env", "base_url"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                errors.append(f"{path}: openai_compatible requires {field}")
    validate_caps(data.get("defaults", {}), f"{path}: defaults", aliases, errors)
    models = data.get("models")
    if not isinstance(models, list):
        errors.append(f"{path}: models must be a list")
        return errors
    for index, model in enumerate(models):
        where = f"{path}: models[{index}]"
        if not isinstance(model, dict):
            errors.append(f"{where}: must be a mapping")
            continue
        unknown_model = set(model) - MODEL_FIELDS
        if unknown_model:
            errors.append(f"{where}: unknown fields {sorted(unknown_model)}")
        model_id = model.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append(f"{where}: id must be a non-empty string")
        elif model_id in seen:
            warnings.append(
                f"{where}: duplicate id {model_id!r}; later definition overrides {seen[model_id]}"
            )
            seen[model_id] = path
        else:
            seen[model_id] = path
        validate_caps(
            {k: v for k, v in model.items() if k in CAPABILITIES},
            where,
            aliases,
            errors,
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="YAML file or directory of top-level *.yaml catalogs")
    args = parser.parse_args()
    directory = args.path if args.path.is_dir() else args.path.parent
    defaults_path = directory / "_defaults.yaml"
    aliases = set(DEFAULT_ALIASES)
    if defaults_path.exists():
        try:
            defaults = yaml.safe_load(defaults_path.read_text(encoding="utf-8")) or {}
            custom = defaults.get("attachment_aliases", {}) if isinstance(defaults, dict) else {}
            if not isinstance(custom, dict):
                raise ValueError("attachment_aliases must be a mapping")
            aliases.update(str(name) for name in custom)
        except Exception as error:
            print(f"ERROR: {defaults_path}: invalid defaults: {error}", file=sys.stderr)
            return 2
    paths = [args.path] if args.path.is_file() else sorted(args.path.glob("*.yaml"))
    paths = [path for path in paths if path.name != "_defaults.yaml"]
    if not paths:
        print("No model YAML files found", file=sys.stderr)
        return 2
    seen: dict[str, Path] = {}
    warnings: list[str] = []
    errors = [error for path in paths for error in validate(path, seen, aliases, warnings)]
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(paths)} catalog(s), {len(seen)} unique model id(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
