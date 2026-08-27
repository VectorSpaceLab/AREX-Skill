#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

VALID_ROUTING_STRATEGIES = frozenset(
    {
        "simple-shuffle",
        "least-busy",
        "usage-based-routing",
        "usage-based-routing-v2",
        "latency-based-routing",
        "cost-based-routing",
    }
)
FALLBACK_KEYS = (
    "fallbacks",
    "context_window_fallbacks",
    "content_policy_fallbacks",
)
ROUTER_SETTING_CONTAINERS = ("router_settings", "litellm_settings")
ADVANCED_ROUTER_PREFIXES = (
    "auto_router/adaptive_router",
    "auto_router/quality_router",
    "auto_router/complexity_router",
)


def strip_yaml_comment(line: str) -> str:
    in_single_quote = False
    in_double_quote = False
    for index, char in enumerate(line):
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == "#" and not in_single_quote and not in_double_quote:
            return line[:index].rstrip()
    return line.rstrip()


def parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped == "":
        return ""
    if stripped in {"true", "True"}:
        return True
    if stripped in {"false", "False"}:
        return False
    if stripped in {"null", "None", "~"}:
        return None
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped
    if (stripped.startswith('"') and stripped.endswith('"')) or (
        stripped.startswith("'") and stripped.endswith("'")
    ):
        return stripped[1:-1]
    try:
        return int(stripped)
    except ValueError:
        try:
            return float(stripped)
        except ValueError:
            return stripped


def parse_key_value(text: str) -> tuple[str, Any | None, bool]:
    key, separator, value = text.partition(":")
    if separator == "":
        raise ValueError(f"expected key: value, got {text!r}")
    key_text = key.strip().strip('"').strip("'")
    if not key_text:
        raise ValueError(f"empty YAML key in {text!r}")
    value_text = value.strip()
    if value_text == "":
        return key_text, None, True
    return key_text, parse_scalar(value_text), False


def normalized_yaml_lines(raw_text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in raw_text.splitlines():
        line = strip_yaml_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))
    return lines


def parse_yaml_block(lines: list[tuple[int, str]], start: int, indent: int) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start
    first_indent, first_text = lines[start]
    if first_indent < indent:
        return {}, start
    if first_text.startswith("- "):
        values: list[Any] = []
        index = start
        while index < len(lines):
            line_indent, text = lines[index]
            if line_indent != first_indent or not text.startswith("- "):
                break
            item_text = text[2:].strip()
            if item_text == "":
                child, next_index = parse_yaml_block(lines, index + 1, first_indent + 2)
                values.append(child)
                index = next_index
            elif ":" in item_text and not item_text.startswith(('"', "'")):
                key, value, needs_child = parse_key_value(item_text)
                item: dict[str, Any] = {}
                if needs_child:
                    child, next_index = parse_yaml_block(lines, index + 1, first_indent + 2)
                    item[key] = child
                    index = next_index
                else:
                    item[key] = value
                    index += 1
                while index < len(lines):
                    child_indent, child_text = lines[index]
                    if child_indent <= first_indent:
                        break
                    if child_text.startswith("- "):
                        break
                    child_key, child_value, child_needs_nested = parse_key_value(child_text)
                    if child_needs_nested:
                        nested, next_index = parse_yaml_block(lines, index + 1, child_indent + 2)
                        item[child_key] = nested
                        index = next_index
                    else:
                        item[child_key] = child_value
                        index += 1
                values.append(item)
            else:
                values.append(parse_scalar(item_text))
                index += 1
        return values, index

    values: dict[str, Any] = {}
    index = start
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"unexpected indentation before {text!r}")
        if text.startswith("- "):
            break
        key, value, needs_child = parse_key_value(text)
        if needs_child:
            child, next_index = parse_yaml_block(lines, index + 1, indent + 2)
            values[key] = child
            index = next_index
        else:
            values[key] = value
            index += 1
    return values, index


def parse_tiny_yaml(raw_text: str) -> Any:
    lines = normalized_yaml_lines(raw_text)
    if not lines:
        return {}
    parsed, next_index = parse_yaml_block(lines, 0, lines[0][0])
    if next_index != len(lines):
        raise ValueError(f"could not parse YAML near line content {lines[next_index][1]!r}")
    return parsed


def load_config(path: Path) -> Any:
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw_text)
    if yaml is not None:
        return yaml.safe_load(raw_text)
    return parse_tiny_yaml(raw_text)


def mapping_at(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    return value if isinstance(value, dict) else {}


def setting_value(config: dict[str, Any], key: str) -> Any:
    if key in config:
        return config[key]
    for container in ROUTER_SETTING_CONTAINERS:
        settings = mapping_at(config, container)
        if key in settings:
            return settings[key]
    return None


def collect_model_groups(model_list: list[Any], errors: list[str], warnings: list[str]) -> tuple[set[str], dict[str, int]]:
    groups: dict[str, int] = {}
    for index, deployment in enumerate(model_list):
        location = f"model_list[{index}]"
        if not isinstance(deployment, dict):
            errors.append(f"{location} must be an object")
            continue
        model_name = deployment.get("model_name")
        if not isinstance(model_name, str) or not model_name.strip():
            errors.append(f"{location}.model_name must be a non-empty string")
        else:
            groups[model_name] = groups.get(model_name, 0) + 1
        litellm_params = deployment.get("litellm_params")
        if not isinstance(litellm_params, dict):
            errors.append(f"{location}.litellm_params must be an object")
            continue
        provider_model = litellm_params.get("model")
        if not isinstance(provider_model, str) or not provider_model.strip():
            errors.append(f"{location}.litellm_params.model must be a non-empty string")
        tags = litellm_params.get("tags")
        if tags is not None and not isinstance(tags, list):
            warnings.append(f"{location}.litellm_params.tags should be a list when tag filtering is used")
    return set(groups), groups


def alias_targets(config: dict[str, Any], warnings: list[str]) -> set[str]:
    aliases = setting_value(config, "model_group_alias")
    if aliases is None:
        return set()
    if not isinstance(aliases, dict):
        warnings.append("model_group_alias should be an object mapping aliases to target model groups")
        return set()
    targets: set[str] = set()
    for alias, target in aliases.items():
        if not isinstance(alias, str) or not alias.strip():
            warnings.append("model_group_alias contains a non-string or empty alias key")
            continue
        if isinstance(target, str):
            targets.add(alias)
            targets.add(target)
        elif isinstance(target, dict):
            targets.add(alias)
            model_group = target.get("model") or target.get("model_group") or target.get("target_model_name")
            if isinstance(model_group, str):
                targets.add(model_group)
        else:
            warnings.append(f"model_group_alias.{alias} should be a string or object")
    return targets


def iter_fallback_entries(value: Any, path: str, errors: list[str]) -> list[tuple[str, list[Any], str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    entries: list[tuple[str, list[Any], str]] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if isinstance(item, str):
            entries.append(("*", [item], item_path))
            continue
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object or string")
            continue
        for source, targets in item.items():
            if not isinstance(source, str) or not source.strip():
                errors.append(f"{item_path} has a non-empty string source requirement")
                continue
            if isinstance(targets, str):
                entries.append((source, [targets], item_path))
            elif isinstance(targets, list):
                entries.append((source, targets, item_path))
            else:
                errors.append(f"{item_path}.{source} must be a string or list of strings")
    return entries


def validate_fallbacks(config: dict[str, Any], known_names: set[str], errors: list[str], warnings: list[str]) -> None:
    aliases = alias_targets(config, warnings)
    allowed_names = known_names | aliases | {"*"}
    for fallback_key in FALLBACK_KEYS:
        value = setting_value(config, fallback_key)
        for source, targets, item_path in iter_fallback_entries(value, fallback_key, errors):
            if source not in allowed_names:
                errors.append(f"{item_path} source '{source}' is not a model group, alias, or '*'")
            for target in targets:
                if isinstance(target, str):
                    if target not in allowed_names:
                        errors.append(f"{item_path} target '{target}' is not a model group, alias, or '*'")
                elif isinstance(target, dict):
                    model_target = target.get("model")
                    if isinstance(model_target, str) and model_target not in allowed_names:
                        errors.append(f"{item_path} target model '{model_target}' is not a model group, alias, or '*'")
                else:
                    errors.append(f"{item_path} target entries must be strings or objects")


def validate_strategy(config: dict[str, Any], errors: list[str]) -> None:
    strategy = setting_value(config, "routing_strategy")
    if strategy is not None and strategy not in VALID_ROUTING_STRATEGIES:
        errors.append(
            f"routing_strategy '{strategy}' is invalid. Expected one of: {', '.join(sorted(VALID_ROUTING_STRATEGIES))}"
        )


def validate_routing_groups(config: dict[str, Any], known_names: set[str], errors: list[str], warnings: list[str]) -> None:
    groups = setting_value(config, "routing_groups")
    if groups is None:
        return
    if not isinstance(groups, list):
        errors.append("routing_groups must be a list")
        return
    seen_group_names: set[str] = set()
    assigned_models: dict[str, str] = {}
    for index, group in enumerate(groups):
        path = f"routing_groups[{index}]"
        if not isinstance(group, dict):
            errors.append(f"{path} must be an object")
            continue
        group_name = group.get("group_name")
        if not isinstance(group_name, str) or not group_name.strip():
            errors.append(f"{path}.group_name must be a non-empty string")
        elif group_name == "default":
            errors.append(f"{path}.group_name cannot be 'default'")
        elif group_name in seen_group_names:
            errors.append(f"{path}.group_name '{group_name}' is duplicated")
        else:
            seen_group_names.add(group_name)
        strategy = group.get("routing_strategy")
        if strategy not in VALID_ROUTING_STRATEGIES:
            errors.append(f"{path}.routing_strategy '{strategy}' is invalid")
        models = group.get("models")
        if not isinstance(models, list):
            errors.append(f"{path}.models must be a list")
            continue
        for model in models:
            if not isinstance(model, str) or not model.strip():
                errors.append(f"{path}.models contains a non-empty string requirement")
                continue
            if model in assigned_models:
                errors.append(f"{path}.models assigns '{model}' after group '{assigned_models[model]}' already claimed it")
            assigned_models[model] = str(group_name)
            if model not in known_names:
                warnings.append(f"{path}.models references '{model}', which is not currently in model_list")


def validate_advanced_routers(model_list: list[Any], known_names: set[str], errors: list[str]) -> None:
    for index, deployment in enumerate(model_list):
        if not isinstance(deployment, dict):
            continue
        litellm_params = deployment.get("litellm_params")
        if not isinstance(litellm_params, dict):
            continue
        provider_model = litellm_params.get("model")
        if provider_model not in ADVANCED_ROUTER_PREFIXES:
            continue
        location = f"model_list[{index}]"
        if provider_model == "auto_router/adaptive_router":
            config = litellm_params.get("adaptive_router_config")
            if not isinstance(config, dict):
                errors.append(f"{location}.litellm_params.adaptive_router_config must be an object")
                continue
            available_models = config.get("available_models")
            if not isinstance(available_models, list) or not available_models:
                errors.append(f"{location}.litellm_params.adaptive_router_config.available_models must be a non-empty list")
                continue
            for target in available_models:
                if not isinstance(target, str) or target not in known_names:
                    errors.append(f"{location} adaptive router target '{target}' is not a model group")


def summarize(groups: dict[str, int]) -> str:
    lines = ["Model groups:"]
    for group_name in sorted(groups):
        count = groups[group_name]
        suffix = "deployment" if count == 1 else "deployments"
        lines.append(f"  - {group_name}: {count} {suffix}")
    return "\n".join(lines)


def inspect_config(config: Any) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(config, dict):
        return ["config root must be an object"], warnings, {}
    model_list = config.get("model_list")
    if not isinstance(model_list, list):
        return ["model_list must be a list"], warnings, {}
    known_names, groups = collect_model_groups(model_list, errors, warnings)
    validate_strategy(config, errors)
    validate_fallbacks(config, known_names, errors, warnings)
    validate_routing_groups(config, known_names, errors, warnings)
    validate_advanced_routers(model_list, known_names, errors)
    if setting_value(config, "enable_tag_filtering") is True:
        tagged_count = sum(
            1
            for deployment in model_list
            if isinstance(deployment, dict)
            and isinstance(deployment.get("litellm_params"), dict)
            and isinstance(deployment["litellm_params"].get("tags"), list)
        )
        if tagged_count == 0:
            warnings.append("enable_tag_filtering is true, but no deployments define litellm_params.tags")
    return errors, warnings, groups


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Statically inspect a tiny LiteLLM Router YAML/JSON config without calling providers."
    )
    parser.add_argument("config", type=Path, help="Path to a LiteLLM proxy/router YAML or JSON file")
    parser.add_argument("--print-summary", action="store_true", help="Print model group summary even when valid")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except Exception as exc:
        print(f"ERROR: failed to load config: {exc}", file=sys.stderr)
        return 2

    errors, warnings, groups = inspect_config(config)
    if args.print_summary and groups:
        print(summarize(groups))
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: router config passed static checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
