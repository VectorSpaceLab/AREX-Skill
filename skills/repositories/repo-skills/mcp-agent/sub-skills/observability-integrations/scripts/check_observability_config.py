#!/usr/bin/env python3
"""Credential-safe observability config checker for mcp-agent projects.

The checker reads YAML config/secrets files, validates the observability-related
shape, redacts sensitive values, and reports likely optional-extra requirements.
It intentionally avoids importing mcp-agent or provider SDK modules and never
contacts OTEL collectors or model providers.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised by environments without PyYAML
    yaml = None

LOGGER_TRANSPORTS = {"none", "console", "file", "http"}
OTEL_EXPORTERS = {"console", "file", "otlp"}
SENSITIVE_RE = re.compile(
    r"(api[_-]?key|authorization|token|secret|password|credential|headers?)",
    re.IGNORECASE,
)

PROVIDER_EXTRAS = {
    "openai": "mcp-agent[openai]",
    "anthropic": "mcp-agent[anthropic]",
    "azure": "mcp-agent[azure]",
    "google": "mcp-agent[google]",
    "bedrock": "mcp-agent[bedrock]",
    "cohere": "mcp-agent[cohere]",
    "lm_studio": "mcp-agent[openai]",
}


def strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    result: list[str] = []
    for char in line:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\" and in_double:
            result.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            result.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            result.append(char)
            continue
        if char == "#" and not in_single and not in_double:
            break
        result.append(char)
    return "".join(result).rstrip()


def split_top_level_csv(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_single = False
    in_double = False
    for char in text:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if char in "[{(":
                depth += 1
            elif char in "]})":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
                continue
        current.append(char)
    if current or text.strip():
        parts.append("".join(current).strip())
    return parts


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [] if not inner else [parse_scalar(item) for item in split_top_level_csv(inner)]
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", value):
            return float(value)
    except ValueError:
        pass
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by common mcp-agent config files.

    This is a fallback for environments without PyYAML. It supports nested
    mappings, scalar values, inline lists, and simple list items. Complex YAML
    features such as anchors, multiline scalars, and flow mappings require
    PyYAML.
    """

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending_key: tuple[int, dict[str, Any], str] | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = strip_inline_comment(raw_line.rstrip("\n"))
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if pending_key and pending_key[0] < indent:
            _, pending_parent, key = pending_key
            if content.startswith("- "):
                if not isinstance(pending_parent.get(key), list):
                    pending_parent[key] = []
                parent = pending_parent[key]
                stack.append((indent - 1, parent))
            else:
                parent = pending_parent[key]
                stack.append((indent - 1, parent))
            pending_key = None

        if content.startswith("- "):
            item_text = content[2:].strip()
            if not isinstance(parent, list):
                raise ValueError(f"list item without list parent near: {raw_line.strip()}")
            if ":" in item_text and not item_text.startswith(('"', "'")):
                key, _, remainder = item_text.partition(":")
                item: dict[str, Any] = {}
                parent.append(item)
                key = key.strip()
                if remainder.strip():
                    item[key] = parse_scalar(remainder.strip())
                else:
                    item[key] = {}
                    pending_key = (indent, item, key)
                stack.append((indent, item))
            else:
                parent.append(parse_scalar(item_text))
            continue

        if ":" not in content:
            raise ValueError(f"unsupported YAML line: {raw_line.strip()}")
        key, _, remainder = content.partition(":")
        key = key.strip().strip('"\'')
        if not isinstance(parent, dict):
            raise ValueError(f"mapping item without mapping parent near: {raw_line.strip()}")

        if remainder.strip():
            parent[key] = parse_scalar(remainder.strip())
            pending_key = None
            continue

        next_container: Any = {}
        parent[key] = next_container
        pending_key = (indent, parent, key)
        stack.append((indent, next_container))

    return root


def load_yaml(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not path.exists():
        warnings.append(f"missing file: {path}")
        return {}, warnings
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        try:
            return parse_simple_yaml(text), [
                "PyYAML is not installed; used a limited fallback parser for common config syntax"
            ]
        except Exception as exc:  # noqa: BLE001 - diagnostics should catch parse failures
            warnings.append(f"failed to parse {path} without PyYAML: {exc}")
            return {}, warnings
    try:
        data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001 - diagnostics should catch parse failures
        warnings.append(f"failed to parse {path}: {exc}")
        return {}, warnings
    if data is None:
        return {}, warnings
    if not isinstance(data, dict):
        warnings.append(f"top-level YAML in {path} is {type(data).__name__}, expected mapping")
        return {}, warnings
    return data, warnings


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def redact(value: Any, key: str = "") -> Any:
    if SENSITIVE_RE.search(key):
        if value in (None, "") or isinstance(value, bool):
            return value
        if isinstance(value, dict):
            return {nested_key: "<redacted>" for nested_key in value}
        return "<redacted>"
    if isinstance(value, dict):
        return {item_key: redact(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    return value


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def exporter_name(entry: Any) -> tuple[str | None, dict[str, Any]]:
    if isinstance(entry, str):
        return entry, {}
    if isinstance(entry, dict):
        if "type" in entry:
            payload = dict(entry)
            name = str(payload.pop("type"))
            return name, payload
        if len(entry) == 1:
            name, payload = next(iter(entry.items()))
            return str(name), payload if isinstance(payload, dict) else {}
    return None, {}


def has_nonempty(mapping: dict[str, Any], key: str) -> bool:
    value = mapping.get(key)
    return value is not None and value != ""


def analyze(config: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    suggestions: list[str] = []

    logger_cfg = config.get("logger") or {}
    if not isinstance(logger_cfg, dict):
        errors.append("logger must be a mapping when present")
        logger_cfg = {}

    transports = normalize_list(logger_cfg.get("transports") or logger_cfg.get("type"))
    if not transports:
        transports = ["console"]
    normalized_transports: list[str] = []
    for transport in transports:
        name = str(transport)
        normalized_transports.append(name)
        if name not in LOGGER_TRANSPORTS:
            errors.append(f"unsupported logger transport: {name}")
    if "file" in normalized_transports and not (
        has_nonempty(logger_cfg, "path") or isinstance(logger_cfg.get("path_settings"), dict)
    ):
        suggestions.append("logger file transport will use the default path unless path/path_settings is set")
    if "http" in normalized_transports and not has_nonempty(logger_cfg, "http_endpoint"):
        warnings.append("logger http transport is enabled but logger.http_endpoint is missing")
    if logger_cfg.get("progress_display") and normalized_transports == ["none"]:
        warnings.append("progress_display is enabled while logger transport is none; progress events may be hard to inspect")

    otel_cfg = config.get("otel") or {}
    if not isinstance(otel_cfg, dict):
        errors.append("otel must be a mapping when present")
        otel_cfg = {}

    otel_exporters: list[dict[str, Any]] = []
    for entry in normalize_list(otel_cfg.get("exporters")):
        name, payload = exporter_name(entry)
        otel_exporters.append({"name": name, "config": redact(payload)})
        if name not in OTEL_EXPORTERS:
            errors.append(f"unsupported OTEL exporter: {entry!r}")
            continue
        if name == "otlp":
            endpoint = payload.get("endpoint") or (otel_cfg.get("otlp_settings") or {}).get("endpoint")
            if not endpoint:
                errors.append("OTEL otlp exporter requires an endpoint")
        if name == "file":
            if not (payload.get("path") or payload.get("path_settings") or otel_cfg.get("path") or otel_cfg.get("path_settings")):
                suggestions.append("OTEL file exporter will use its default trace path unless path/path_settings is set")
    if otel_cfg.get("enabled") and not otel_exporters:
        warnings.append("otel.enabled is true but no exporters are configured")
    sample_rate = otel_cfg.get("sample_rate")
    if sample_rate is not None:
        try:
            rate = float(sample_rate)
            if not 0.0 <= rate <= 1.0:
                warnings.append("otel.sample_rate should be between 0.0 and 1.0; runtime clamps invalid values")
        except (TypeError, ValueError):
            errors.append("otel.sample_rate must be numeric")

    usage_telemetry = config.get("usage_telemetry") or {}
    if usage_telemetry and not isinstance(usage_telemetry, dict):
        errors.append("usage_telemetry must be a mapping when present")
        usage_telemetry = {}
    if usage_telemetry.get("enable_detailed_telemetry"):
        warnings.append("usage_telemetry.enable_detailed_telemetry may include prompts or agent details; confirm data policy")

    provider_findings = []
    for provider, extra in PROVIDER_EXTRAS.items():
        provider_cfg = config.get(provider)
        if isinstance(provider_cfg, dict) and provider_cfg:
            finding = {
                "provider": provider,
                "required_extra": extra,
                "has_default_model": has_nonempty(provider_cfg, "default_model"),
                "has_api_key_or_local_default": has_nonempty(provider_cfg, "api_key") or provider == "lm_studio",
                "base_url": redact(provider_cfg.get("base_url"), "base_url"),
            }
            if provider == "lm_studio" and not has_nonempty(provider_cfg, "default_model"):
                warnings.append("lm_studio.default_model should match a loaded local model")
            if provider in {"openai", "anthropic"} and not finding["has_api_key_or_local_default"]:
                suggestions.append(f"{provider} config has no api_key; use env/secrets or a local-compatible endpoint")
            provider_findings.append(finding)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "logger": {
            "transports": normalized_transports,
            "level": logger_cfg.get("level", "info"),
            "progress_display": bool(logger_cfg.get("progress_display", False)),
            "path": logger_cfg.get("path"),
            "path_settings": redact(logger_cfg.get("path_settings") or {}),
            "http_endpoint_configured": has_nonempty(logger_cfg, "http_endpoint"),
        },
        "otel": {
            "enabled": bool(otel_cfg.get("enabled", False)),
            "service_name": otel_cfg.get("service_name", "mcp-agent"),
            "sample_rate": otel_cfg.get("sample_rate", 1.0),
            "exporters": otel_exporters,
        },
        "usage_telemetry": redact(usage_telemetry),
        "providers": provider_findings,
    }


def print_text(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"Observability config: {status}")
    print(f"Logger transports: {', '.join(report['logger']['transports'])}")
    print(f"Logger level: {report['logger']['level']}")
    print(f"Progress display: {report['logger']['progress_display']}")
    print(f"OTEL enabled: {report['otel']['enabled']}")
    print(f"OTEL exporters: {', '.join(str(item['name']) for item in report['otel']['exporters']) or '(none)'}")
    if report["providers"]:
        print("Provider configs:")
        for provider in report["providers"]:
            print(f"  - {provider['provider']}: extra {provider['required_extra']}, default_model={provider['has_default_model']}")
    for label in ("errors", "warnings", "suggestions"):
        if report[label]:
            print(f"{label.capitalize()}:")
            for item in report[label]:
                print(f"  - {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check mcp-agent observability and integration config safely.")
    parser.add_argument("--config", type=Path, default=Path("mcp_agent.config.yaml"), help="Path to mcp_agent.config.yaml")
    parser.add_argument("--secrets", type=Path, default=None, help="Optional mcp_agent.secrets.yaml to merge for presence checks")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    config, load_warnings = load_yaml(args.config)
    if args.secrets:
        secrets, secret_warnings = load_yaml(args.secrets)
        load_warnings.extend(secret_warnings)
        config = deep_merge(config, secrets)

    report = analyze(config)
    report["warnings"] = load_warnings + report["warnings"]

    if args.json:
        print(json.dumps(redact(report), indent=2, sort_keys=True))
    else:
        print_text(redact(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
