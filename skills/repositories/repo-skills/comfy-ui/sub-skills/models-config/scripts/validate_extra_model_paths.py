#!/usr/bin/env python3
"""Validate ComfyUI extra_model_paths.yaml files without importing ComfyUI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - common in minimal Python environments
    yaml = None

SUPPORTED_CATEGORIES = {
    "checkpoints",
    "configs",
    "loras",
    "vae",
    "text_encoders",
    "diffusion_models",
    "clip_vision",
    "style_models",
    "embeddings",
    "diffusers",
    "vae_approx",
    "controlnet",
    "gligen",
    "upscale_models",
    "latent_upscale_models",
    "custom_nodes",
    "hypernetworks",
    "photomaker",
    "classifiers",
    "model_patches",
    "audio_encoders",
    "background_removal",
    "frame_interpolation",
    "geometry_estimation",
    "optical_flow",
    "detection",
}

LEGACY_CATEGORY_MAP = {
    "clip": "text_encoders",
    "unet": "diffusion_models",
}


class SimpleYamlError(ValueError):
    """Raised when the fallback parser cannot parse the expected config shape."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate ComfyUI extra_model_paths.yaml syntax and resolved model "
            "paths without importing ComfyUI or loading models."
        )
    )
    parser.add_argument("config", type=Path, help="Path to extra_model_paths.yaml")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on unknown categories and missing directories.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Warn about missing directories instead of failing. Overrides missing-directory failures from --strict.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON report instead of human-readable diagnostics.",
    )
    parser.add_argument(
        "--no-existence-check",
        action="store_true",
        help="Only validate YAML shape and path resolution; do not check whether directories exist.",
    )
    return parser.parse_args()


def diagnostic(level: str, message: str, **extra: Any) -> dict[str, Any]:
    item = {"level": level, "message": message}
    item.update(extra)
    return item


def strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or line[index - 1].isspace():
                return line[:index].rstrip()
    return line.rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lower = value.lower()
    if lower in {"true", "yes", "on"}:
        return True
    if lower in {"false", "no", "off"}:
        return False
    if lower in {"null", "none", "~"}:
        return None
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    return value


def parse_fallback_yaml(text: str) -> dict[str, Any] | None:
    """Parse the simple mapping/block-string shape used by extra_model_paths.yaml.

    This is intentionally small. It supports top-level profile mappings,
    two-space indented key/value pairs, comments, blank lines, and literal
    block scalars (`|`) for newline-separated category paths.
    """

    result: dict[str, Any] = {}
    current_profile: str | None = None
    current_block_key: str | None = None
    current_block_indent: int | None = None
    block_lines: list[str] = []

    def finish_block() -> None:
        nonlocal current_block_key, current_block_indent, block_lines
        if current_profile is not None and current_block_key is not None:
            result[current_profile][current_block_key] = "\n".join(block_lines)
        current_block_key = None
        current_block_indent = None
        block_lines = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            raise SimpleYamlError(f"line {line_number}: tabs are not supported in fallback parser")

        if current_block_key is not None:
            if raw_line.strip() == "":
                block_lines.append("")
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            if current_block_indent is None:
                current_block_indent = indent
            if indent >= current_block_indent:
                block_lines.append(raw_line[current_block_indent:].rstrip())
                continue
            finish_block()

        line = strip_inline_comment(raw_line)
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise SimpleYamlError(f"line {line_number}: expected key: value mapping")

        key, value = stripped.split(":", 1)
        key = key.strip().strip("'\"")
        value = value.strip()
        if not key:
            raise SimpleYamlError(f"line {line_number}: empty key")

        if indent == 0:
            finish_block()
            if value:
                raise SimpleYamlError(f"line {line_number}: top-level profile must be a mapping")
            current_profile = key
            result[current_profile] = {}
            continue

        if current_profile is None:
            raise SimpleYamlError(f"line {line_number}: nested key appears before any profile")
        if indent < 2:
            raise SimpleYamlError(f"line {line_number}: profile entries must be indented")

        if value in {"|", "|-", "|+"}:
            finish_block()
            current_block_key = key
            current_block_indent = None
            block_lines = []
        else:
            result[current_profile][key] = parse_scalar(value)

    finish_block()
    return result or None


def load_yaml_config(config_path: Path) -> tuple[Any, str | None]:
    text = config_path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text), None
    return parse_fallback_yaml(text), "PyYAML is not installed; used built-in parser for the expected ComfyUI extra-model-paths shape."


def normalize_category(category: str) -> tuple[str, str | None]:
    mapped = LEGACY_CATEGORY_MAP.get(category, category)
    if mapped != category:
        return mapped, category
    return mapped, None


def split_category_value(value: Any) -> tuple[list[str], str | None]:
    if value is None:
        return [], None
    if isinstance(value, str):
        return [line.strip() for line in value.split("\n") if line.strip()], None
    return [], f"category value must be a string or block string, got {type(value).__name__}"


def resolve_base_path(base_path: Any, yaml_dir: Path) -> tuple[Path | None, str | None]:
    if base_path is None:
        return None, None
    if not isinstance(base_path, str):
        return None, f"base_path must be a string, got {type(base_path).__name__}"
    expanded = os.path.expandvars(os.path.expanduser(base_path))
    path = Path(expanded)
    if not path.is_absolute():
        path = yaml_dir / path
    return path.resolve(strict=False), None


def resolve_model_path(raw_path: str, base_path: Path | None, yaml_dir: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    path = Path(expanded)
    if path.is_absolute():
        return path.resolve(strict=False)
    if base_path is not None:
        return (base_path / path).resolve(strict=False)
    return (yaml_dir / path).resolve(strict=False)


def validate_config(config_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "config": str(config_path),
        "ok": True,
        "profiles": [],
        "diagnostics": [],
    }

    if not config_path.exists():
        report["diagnostics"].append(diagnostic("error", "config file does not exist", path=str(config_path)))
        report["ok"] = False
        return report

    if not config_path.is_file():
        report["diagnostics"].append(diagnostic("error", "config path is not a file", path=str(config_path)))
        report["ok"] = False
        return report

    yaml_dir = config_path.resolve(strict=False).parent

    try:
        loaded, parser_warning = load_yaml_config(config_path)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report parser details
        report["diagnostics"].append(diagnostic("error", f"YAML parse failed: {exc}"))
        report["ok"] = False
        return report

    if parser_warning:
        report["diagnostics"].append(diagnostic("warning", parser_warning))

    if loaded is None:
        report["diagnostics"].append(diagnostic("warning", "YAML document is empty"))
        return report

    if not isinstance(loaded, dict):
        report["diagnostics"].append(
            diagnostic("error", f"top-level YAML value must be a mapping, got {type(loaded).__name__}")
        )
        report["ok"] = False
        return report

    seen_by_category: dict[str, set[str]] = {}

    for profile_name, profile_config in loaded.items():
        profile_report: dict[str, Any] = {
            "name": str(profile_name),
            "base_path": None,
            "is_default": False,
            "paths": [],
        }
        report["profiles"].append(profile_report)

        if profile_config is None:
            report["diagnostics"].append(
                diagnostic("warning", "profile is empty and will be skipped", profile=str(profile_name))
            )
            continue

        if not isinstance(profile_config, dict):
            report["diagnostics"].append(
                diagnostic(
                    "error",
                    f"profile must be a mapping, got {type(profile_config).__name__}",
                    profile=str(profile_name),
                )
            )
            report["ok"] = False
            continue

        base_path, base_error = resolve_base_path(profile_config.get("base_path"), yaml_dir)
        if base_error:
            report["diagnostics"].append(diagnostic("error", base_error, profile=str(profile_name)))
            report["ok"] = False
            continue

        if base_path is not None:
            profile_report["base_path"] = str(base_path)
            if not args.no_existence_check and not base_path.is_dir():
                level = "warning" if args.allow_missing or not args.strict else "error"
                report["diagnostics"].append(
                    diagnostic(level, "base_path directory does not exist", profile=str(profile_name), path=str(base_path))
                )
                if level == "error":
                    report["ok"] = False

        is_default = profile_config.get("is_default", False)
        profile_report["is_default"] = bool(is_default)
        if "is_default" in profile_config and not isinstance(is_default, bool):
            report["diagnostics"].append(
                diagnostic(
                    "warning",
                    f"is_default is normally boolean, got {type(is_default).__name__}",
                    profile=str(profile_name),
                )
            )

        for category, raw_value in profile_config.items():
            if category in {"base_path", "is_default"}:
                continue
            category_name = str(category)
            normalized_category, legacy_name = normalize_category(category_name)

            if legacy_name:
                report["diagnostics"].append(
                    diagnostic(
                        "warning",
                        f"legacy category '{legacy_name}' maps to '{normalized_category}'",
                        profile=str(profile_name),
                        category=legacy_name,
                    )
                )

            if normalized_category not in SUPPORTED_CATEGORIES:
                level = "error" if args.strict else "warning"
                report["diagnostics"].append(
                    diagnostic(
                        level,
                        "unknown category; this is only valid if a custom node registers it at runtime",
                        profile=str(profile_name),
                        category=category_name,
                    )
                )
                if level == "error":
                    report["ok"] = False

            entries, value_error = split_category_value(raw_value)
            if value_error:
                report["diagnostics"].append(
                    diagnostic("error", value_error, profile=str(profile_name), category=category_name)
                )
                report["ok"] = False
                continue

            if not entries:
                report["diagnostics"].append(
                    diagnostic("warning", "category has no usable paths", profile=str(profile_name), category=category_name)
                )
                continue

            for raw_entry in entries:
                resolved = resolve_model_path(raw_entry, base_path, yaml_dir)
                resolved_text = str(resolved)
                category_seen = seen_by_category.setdefault(normalized_category, set())
                duplicate = resolved_text in category_seen
                category_seen.add(resolved_text)

                path_report = {
                    "category": normalized_category,
                    "source_category": category_name,
                    "raw": raw_entry,
                    "resolved": resolved_text,
                    "exists": resolved.is_dir(),
                    "duplicate": duplicate,
                }
                profile_report["paths"].append(path_report)

                if duplicate:
                    report["diagnostics"].append(
                        diagnostic(
                            "warning",
                            "duplicate resolved path for category",
                            profile=str(profile_name),
                            category=normalized_category,
                            path=resolved_text,
                        )
                    )

                if not args.no_existence_check and not resolved.is_dir():
                    level = "warning" if args.allow_missing or not args.strict else "error"
                    report["diagnostics"].append(
                        diagnostic(
                            level,
                            "model path directory does not exist",
                            profile=str(profile_name),
                            category=normalized_category,
                            path=resolved_text,
                        )
                    )
                    if level == "error":
                        report["ok"] = False

    return report


def print_text_report(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"extra_model_paths validation: {status}")
    print(f"config: {report['config']}")

    for profile in report["profiles"]:
        print(f"\n[{profile['name']}]")
        if profile["base_path"]:
            print(f"base_path: {profile['base_path']}")
        print(f"is_default: {profile['is_default']}")
        for path_item in profile["paths"]:
            exists = "exists" if path_item["exists"] else "missing"
            duplicate = " duplicate" if path_item["duplicate"] else ""
            source = path_item["source_category"]
            category = path_item["category"]
            category_text = category if source == category else f"{source}->{category}"
            print(f"- {category_text}: {path_item['raw']} -> {path_item['resolved']} ({exists}{duplicate})")

    if report["diagnostics"]:
        print("\nDiagnostics:")
        for item in report["diagnostics"]:
            context = []
            for key in ("profile", "category", "path"):
                if key in item:
                    context.append(f"{key}={item[key]}")
            suffix = f" ({', '.join(context)})" if context else ""
            print(f"- {item['level'].upper()}: {item['message']}{suffix}")


def main() -> int:
    args = parse_args()
    report = validate_config(args.config, args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
