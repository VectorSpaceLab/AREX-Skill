#!/usr/bin/env python3
"""Read-only Viseron component schema inspector.

This helper adapts the repository's docs schema conversion idea for runtime
skill use: inspect one component, print a JSON summary, and never write
Docusaurus files or mutate application state.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections.abc import Mapping
from typing import Any

DEFAULT_DOMAINS = [
    "camera",
    "face_recognition",
    "image_classification",
    "license_plate_recognition",
    "motion_detector",
    "nvr",
    "object_detector",
]

TYPES_MAP = {
    int: "integer",
    str: "string",
    float: "float",
    bool: "boolean",
    list: "list",
    bytes: "bytes",
}


class DependencyBundle:
    """Runtime imports needed for schema conversion."""

    def __init__(self) -> None:
        self.vol = None
        self.unsupported = object()
        self.undefined = object()
        self.validators: dict[str, type | Any] = {}


def _json_safe(value: Any) -> Any:
    """Return a value that can be emitted as JSON."""
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _class_name(value: Any) -> str:
    """Return a stable class name for optional Viseron validators."""
    return value.__class__.__name__


def _load_dependencies() -> DependencyBundle:
    """Import heavy dependencies only after argparse has handled --help."""
    bundle = DependencyBundle()
    try:
        import voluptuous as vol  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on caller env
        raise SystemExit(
            "voluptuous is required to inspect Viseron schemas. "
            "Install/use a Viseron inspection environment first."
        ) from exc

    bundle.vol = vol

    try:
        config_module = importlib.import_module("viseron.config")
        bundle.unsupported = getattr(config_module, "UNSUPPORTED", bundle.unsupported)
    except Exception:  # noqa: BLE001 - schema conversion can still continue
        pass

    try:
        validators = importlib.import_module("viseron.helpers.validators")
        bundle.undefined = getattr(validators, "UNDEFINED", bundle.undefined)
        for name in (
            "CameraIdentifier",
            "CoerceNoneToDict",
            "CronExpression",
            "Deprecated",
            "Maybe",
            "PathExists",
            "Slug",
            "StringKey",
            "Timezone",
            "Url",
        ):
            if hasattr(validators, name):
                bundle.validators[name] = getattr(validators, name)
        if hasattr(validators, "jinja2_template"):
            bundle.validators["jinja2_template"] = getattr(validators, "jinja2_template")
    except Exception:  # noqa: BLE001 - keep generic conversion usable
        pass

    return bundle


def _isinstance_optional(value: Any, cls: Any) -> bool:
    """Like isinstance, but tolerant of missing optional classes."""
    return cls is not None and isinstance(value, cls)


def convert_schema(schema: Any, deps: DependencyBundle, custom_convert=None) -> Any:  # noqa: C901, PLR0911, PLR0912
    """Convert a voluptuous schema to serializable data.

    This is adapted from Viseron's docs generator but deliberately omits all file
    writes and degrades custom/unknown validators into readable placeholders.
    """
    vol = deps.vol
    assert vol is not None

    if isinstance(schema, vol.Schema):
        schema = schema.schema

    if custom_convert:
        value = custom_convert(schema)
        if value is not deps.unsupported:
            return value

    deprecated_cls = deps.validators.get("Deprecated")
    maybe_cls = deps.validators.get("Maybe")
    url_cls = deps.validators.get("Url")
    path_exists_cls = deps.validators.get("PathExists")
    camera_identifier_cls = deps.validators.get("CameraIdentifier")
    slug_cls = deps.validators.get("Slug")
    string_key_cls = deps.validators.get("StringKey")
    cron_cls = deps.validators.get("CronExpression")
    timezone_cls = deps.validators.get("Timezone")
    jinja2_template = deps.validators.get("jinja2_template")

    if isinstance(schema, Mapping):
        converted = []
        for key, value in schema.items():
            description = getattr(key, "description", None)
            plain_key = key.schema if isinstance(key, vol.Marker) else key
            converted_value = convert_schema(value, deps, custom_convert=custom_convert)
            if isinstance(converted_value, list):
                converted_value = {"type": "map", "value": converted_value}
            elif not isinstance(converted_value, dict):
                converted_value = {"type": _class_name(value), "value": _json_safe(converted_value)}

            if not isinstance(plain_key, str) or _isinstance_optional(key, deprecated_cls):
                converted_value["name"] = convert_schema(
                    key, deps, custom_convert=custom_convert
                )
            else:
                converted_value["name"] = plain_key
            converted_value["description"] = description

            if isinstance(key, (vol.Required, vol.Optional)) or _isinstance_optional(
                key, deprecated_cls
            ):
                converted_value[key.__class__.__name__.lower()] = True
                if key.default is not vol.UNDEFINED and key.default is not deps.undefined:
                    try:
                        converted_value["default"] = _json_safe(key.default())
                    except Exception as exc:  # noqa: BLE001
                        converted_value["default_error"] = repr(exc)
                else:
                    converted_value["default"] = None
            converted.append(converted_value)
        return converted

    def recurse_options(options: list[Any]) -> list[Any]:
        flattened = []
        for option in options:
            if isinstance(option, dict) and "options" in option:
                flattened += recurse_options(option["options"])
            else:
                flattened.append(option)
        return flattened

    if _isinstance_optional(schema, maybe_cls):
        values = []
        for validator in getattr(schema, "validators", []):
            if validator is None or validator is deps.undefined:
                continue
            values.append(convert_schema(validator, deps, custom_convert=custom_convert))
        options = recurse_options(values)
        if len(options) == 1:
            return options[0]
        return {"type": "select", "options": options}

    if isinstance(schema, vol.Any):
        values = [
            convert_schema(validator, deps, custom_convert=custom_convert)
            for validator in schema.validators
        ]
        return {"type": "select", "options": recurse_options(values)}

    if isinstance(schema, vol.All):
        list_values = []
        dict_value: dict[str, Any] = {}
        for validator in schema.validators:
            if _isinstance_optional(validator, deps.validators.get("CoerceNoneToDict")):
                continue
            value = convert_schema(validator, deps, custom_convert=custom_convert)
            if isinstance(value, list):
                list_values.extend(value)
            elif isinstance(value, dict):
                dict_value.update(value)
            else:
                dict_value.setdefault("validators", []).append(_json_safe(value))
        return list_values or dict_value

    if isinstance(schema, (vol.Clamp, vol.Range)):
        value = {}
        if schema.min is not None:
            value["valueMin"] = schema.min
        if schema.max is not None:
            value["valueMax"] = schema.max
        return value

    if isinstance(schema, vol.Length):
        value = {}
        if schema.min is not None:
            value["lengthMin"] = schema.min
        if schema.max is not None:
            value["lengthMax"] = schema.max
        return value

    if hasattr(vol, "Datetime") and isinstance(schema, vol.Datetime):
        return {"type": "datetime", "format": schema.format}

    if isinstance(schema, vol.In):
        return {
            "type": "select",
            "options": [
                convert_schema(item, deps, custom_convert=custom_convert)
                for item in schema.container
            ],
        }

    if schema in (vol.Lower, vol.Upper, vol.Capitalize, vol.Title, vol.Strip):
        return {schema.__name__.lower(): True}

    if schema in (vol.Email, vol.FqdnUrl):
        return {"format": schema.__name__.lower()}

    if _isinstance_optional(schema, url_cls):
        return {"type": "string", "format": _class_name(schema).lower()}

    if _isinstance_optional(schema, path_exists_cls):
        return {"type": "string", "format": "file path"}

    if isinstance(schema, vol.Coerce):
        schema = schema.type

    if isinstance(schema, list):
        return {
            "type": "list",
            "values": [
                convert_schema(item, deps, custom_convert=custom_convert)
                for item in schema
            ],
        }

    try:
        if schema in TYPES_MAP:
            return {"type": TYPES_MAP[schema]}
    except TypeError:
        pass

    if isinstance(schema, (str, int, float, bool)):
        return {"type": "constant", "value": schema}

    if schema is None:
        return {"type": "none", "value": "null"}

    if _isinstance_optional(schema, camera_identifier_cls):
        return {"type": "CAMERA_IDENTIFIER"}

    if _isinstance_optional(schema, slug_cls) or _isinstance_optional(schema, string_key_cls):
        return {"type": "string"}

    if _isinstance_optional(schema, deprecated_cls):
        return {
            "type": "deprecated",
            "name": getattr(schema, "key", None),
            "value": getattr(schema, "message", None),
        }

    if _isinstance_optional(schema, cron_cls) or _isinstance_optional(schema, timezone_cls):
        return {"type": "string"}

    if schema == jinja2_template:
        return {"type": "jinja2_template", "value": "jinja2_template"}

    if callable(schema):
        return {"type": "custom_validator", "value": getattr(schema, "__name__", repr(schema))}

    return {"type": "unsupported", "value": repr(schema)}


def sort_required(config: Any) -> None:
    """Put required options first in converted config data."""
    if isinstance(config, list):
        for item in config:
            sort_required(item)
    if isinstance(config, dict) and config.get("type") == "map":
        config["value"] = sorted(
            config["value"], key=lambda item: item.get("required", False), reverse=True
        )
        for item in config["value"]:
            sort_required(item)


def count_nodes(node: Any) -> int:
    """Count schema nodes for truncation metadata."""
    if isinstance(node, list):
        return 1 + sum(count_nodes(item) for item in node)
    if isinstance(node, dict):
        return 1 + sum(count_nodes(value) for value in node.values())
    return 1


def condense(node: Any, *, depth: int, max_depth: int, max_items: int) -> Any:
    """Build a compact schema summary while preserving names/descriptions."""
    if isinstance(node, list):
        items = node[:max_items]
        result = [
            condense(item, depth=depth, max_depth=max_depth, max_items=max_items)
            for item in items
        ]
        if len(node) > max_items:
            result.append({"truncated_items": len(node) - max_items})
        return result

    if not isinstance(node, dict):
        return _json_safe(node)

    important_keys = (
        "name",
        "type",
        "required",
        "optional",
        "inclusive",
        "deprecated",
        "default",
        "description",
        "format",
        "valueMin",
        "valueMax",
        "lengthMin",
        "lengthMax",
        "value",
    )
    summary = {key: _json_safe(node[key]) for key in important_keys if key in node}

    child_key = None
    for candidate in ("value", "values", "options"):
        if candidate in node and isinstance(node[candidate], (list, dict)):
            child_key = candidate
            break

    if child_key:
        child = node[child_key]
        if depth < max_depth:
            summary[child_key] = condense(
                child, depth=depth + 1, max_depth=max_depth, max_items=max_items
            )
        else:
            summary[f"{child_key}_truncated_node_count"] = count_nodes(child)
            if "value" in summary and child_key == "value":
                summary.pop("value", None)
    return summary


def load_supported_domains() -> list[str]:
    """Return Viseron's supported domain names without requiring docs files."""
    try:
        from typing_extensions import get_args

        viseron_types = importlib.import_module("viseron.viseron_types")
        domains = list(get_args(getattr(viseron_types, "SupportedDomains")))
        return [domain for domain in domains if isinstance(domain, str)] or DEFAULT_DOMAINS
    except Exception:  # noqa: BLE001
        return DEFAULT_DOMAINS


def load_custom_convert(component: str):
    """Load component-specific docs conversion hook when it exists."""
    try:
        config_module = importlib.import_module(f"viseron.components.{component}.config")
    except ModuleNotFoundError:
        return None
    return getattr(config_module, "custom_convert", None)


def schema_record(schema: Any, deps: DependencyBundle, *, max_depth: int, max_items: int, full: bool, custom_convert=None) -> dict[str, Any]:
    """Return converted and summarized schema data."""
    converted = convert_schema(schema, deps, custom_convert=custom_convert)
    sort_required(converted)
    record: dict[str, Any] = {
        "node_count": count_nodes(converted),
        "summary": condense(converted, depth=0, max_depth=max_depth, max_items=max_items),
    }
    if full:
        record["converted"] = converted
    return record


def inspect_component(args: argparse.Namespace) -> dict[str, Any]:
    """Inspect one Viseron component and return a JSON-serializable record."""
    # Some Viseron modules read this variable during import. Use a generic
    # process-local value if the caller has not set one; this script does not
    # read or write application config files.
    os.environ.setdefault("VISERON_CONFIG_DIR", os.getcwd())

    deps = _load_dependencies()
    component = args.component
    component_module_name = f"viseron.components.{component}"
    record: dict[str, Any] = {
        "component": component,
        "module": component_module_name,
        "read_only": True,
        "writes_files": False,
    }

    try:
        component_module = importlib.import_module(component_module_name)
    except Exception as exc:  # noqa: BLE001
        record["component_import"] = {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
        return record

    record["component_import"] = {"ok": True}
    record["hooks"] = {
        "CONFIG_SCHEMA": hasattr(component_module, "CONFIG_SCHEMA"),
        "setup": hasattr(component_module, "setup"),
        "setup_domains": hasattr(component_module, "setup_domains"),
        "unload": hasattr(component_module, "unload"),
    }

    custom_convert = load_custom_convert(component)
    if hasattr(component_module, "CONFIG_SCHEMA"):
        try:
            record["component_schema"] = schema_record(
                component_module.CONFIG_SCHEMA,
                deps,
                max_depth=args.max_depth,
                max_items=args.max_items,
                full=args.full,
                custom_convert=custom_convert,
            )
        except Exception as exc:  # noqa: BLE001
            record["component_schema_error"] = {
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }

    if args.include_domains:
        domains = []
        import_errors = []
        for domain in load_supported_domains():
            domain_module_name = f"{component_module_name}.{domain}"
            try:
                domain_module = importlib.import_module(domain_module_name)
            except ModuleNotFoundError as exc:
                # Missing direct domain modules are normal: most components only
                # implement a subset of domains. Nested optional-dependency errors
                # are reported because they explain why an expected domain failed.
                if exc.name == domain_module_name:
                    continue
                import_errors.append(
                    {
                        "domain": domain,
                        "module": domain_module_name,
                        "error_type": exc.__class__.__name__,
                        "error": str(exc),
                    }
                )
                continue
            except Exception as exc:  # noqa: BLE001
                import_errors.append(
                    {
                        "domain": domain,
                        "module": domain_module_name,
                        "error_type": exc.__class__.__name__,
                        "error": str(exc),
                    }
                )
                continue

            domain_record: dict[str, Any] = {
                "domain": domain,
                "module": domain_module_name,
                "hooks": {
                    "CONFIG_SCHEMA": hasattr(domain_module, "CONFIG_SCHEMA"),
                    "setup": hasattr(domain_module, "setup"),
                    "unload": hasattr(domain_module, "unload"),
                    "setup_failed": hasattr(domain_module, "setup_failed"),
                },
            }
            if hasattr(domain_module, "CONFIG_SCHEMA"):
                try:
                    domain_record["schema"] = schema_record(
                        domain_module.CONFIG_SCHEMA,
                        deps,
                        max_depth=args.max_depth,
                        max_items=args.max_items,
                        full=args.full,
                        custom_convert=custom_convert,
                    )
                except Exception as exc:  # noqa: BLE001
                    domain_record["schema_error"] = {
                        "error_type": exc.__class__.__name__,
                        "error": str(exc),
                    }
            domains.append(domain_record)
        record["domains"] = domains
        if import_errors:
            record["domain_import_errors"] = import_errors

    return record


def build_parser() -> argparse.ArgumentParser:
    """Build command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Viseron CONFIG_SCHEMA inspector for one component. "
            "Prints JSON to stdout and never writes Docusaurus files."
        )
    )
    parser.add_argument("component", help="Component name, for example: logger, yolo, ffmpeg")
    parser.add_argument(
        "--include-domains",
        action="store_true",
        help="Also import implemented domain modules and summarize their schemas.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum nested schema depth to include in the compact summary.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=80,
        help="Maximum list items to include per schema level before truncating.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include the full converted schema in addition to the compact summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_depth < 0:
        parser.error("--max-depth must be >= 0")
    if args.max_items < 1:
        parser.error("--max-items must be >= 1")

    result = inspect_component(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("component_import", {}).get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
