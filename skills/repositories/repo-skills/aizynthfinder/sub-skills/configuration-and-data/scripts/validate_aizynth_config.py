#!/usr/bin/env python3
"""Static validator for AiZynthFinder YAML configuration files.

This script is intentionally conservative and safe:
- it does not import AiZynthFinder;
- it does not load model, template, stock, bloom, or HDF5 files;
- it does not connect to MongoDB or TensorFlow serving;
- it does not run retrosynthesis.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal Python envs
    yaml = None  # type: ignore[assignment]

ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
KNOWN_TOP_LEVEL = {
    "search",
    "post_processing",
    "expansion",
    "filter",
    "stock",
    "scorer",
}
KNOWN_SEARCH_KEYS = {
    "algorithm",
    "algorithm_config",
    "max_transforms",
    "iteration_limit",
    "time_limit",
    "return_first",
    "exclude_target_from_stock",
    "break_bonds",
    "freeze_bonds",
    "break_bonds_operator",
}
KNOWN_POST_PROCESSING_KEYS = {
    "min_routes",
    "max_routes",
    "all_routes",
    "route_distance_model",
    "route_scorer",
    "route_scorers",
    "scorer_weights",
}
PATH_EXTENSIONS = {
    ".bloom",
    ".csv",
    ".gz",
    ".h5",
    ".hdf5",
    ".hdf",
    ".keras",
    ".npz",
    ".onnx",
    ".pkl",
    ".pickle",
    ".pt",
    ".pth",
    ".smi",
    ".sdf",
    ".txt",
    ".yml",
    ".yaml",
}
PATH_KEYS = {
    "model",
    "template",
    "mask",
    "path",
    "route_distance_model",
}
REMOTE_LIKE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.env: dict[str, list[str]] = {"resolved": [], "missing": []}
        self.path_checks: list[dict[str, Any]] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate AiZynthFinder YAML config shape and local asset "
            "references without importing AiZynthFinder or loading assets."
        )
    )
    parser.add_argument("config", help="Path to the AiZynthFinder YAML config file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report instead of a human summary",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit nonzero when warnings are present, not only when errors are present",
    )
    return parser.parse_args(argv)


def resolve_env_placeholders(text: str, reporter: Reporter) -> str:
    missing: list[str] = []
    resolved: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in os.environ:
            missing.append(name)
            return match.group(0)
        resolved.append(name)
        return os.environ[name]

    resolved_text = ENV_PATTERN.sub(replace, text)
    for name in sorted(set(resolved)):
        reporter.env["resolved"].append(name)
    for name in sorted(set(missing)):
        reporter.env["missing"].append(name)
        reporter.error(
            f"Missing environment variable '{name}' required by a ${{{name}}} placeholder"
        )
    return resolved_text


class FallbackYamlError(ValueError):
    """Raised when the bundled minimal YAML parser cannot parse input."""


def strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if char == "\\" and in_double and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index].rstrip()
        escaped = False
    return line.rstrip()


def split_top_level(text: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(text):
        if char == "\\" and in_double and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif not in_single and not in_double:
            if char in "[{(":
                depth += 1
            elif char in "]})":
                depth -= 1
            elif char == delimiter and depth == 0:
                parts.append(text[start:index].strip())
                start = index + 1
        escaped = False
    parts.append(text[start:].strip())
    return parts


def split_key_value(text: str) -> tuple[str, str | None]:
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(text):
        if char == "\\" and in_double and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif not in_single and not in_double:
            if char in "[{(":
                depth += 1
            elif char in "]})":
                depth -= 1
            elif char == ":" and depth == 0:
                return text[:index].strip(), text[index + 1 :].strip()
        escaped = False
    return text.strip(), None


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in split_top_level(inner, ",")]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: dict[Any, Any] = {}
        for part in split_top_level(inner, ","):
            key, item_value = split_key_value(part)
            if item_value is None:
                raise FallbackYamlError(f"Cannot parse inline mapping item: {part}")
            result[parse_scalar(key)] = parse_scalar(item_value)
        return result
    if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
        try:
            return ast.literal_eval(value)
        except Exception:  # pylint: disable=broad-except
            return value[1:-1]
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", value) or re.fullmatch(
            r"[-+]?\d+[eE][-+]?\d+", value
        ):
            return float(value)
    except ValueError:
        pass
    return value


def parse_fallback_yaml(text: str) -> Any:
    lines: list[tuple[int, int, str]] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip("\t "))]:
            raise FallbackYamlError(f"Line {line_no}: tabs in indentation are not supported")
        stripped_comment = strip_yaml_comment(raw_line)
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        lines.append((line_no, indent, stripped_comment.strip()))

    if not lines:
        return None

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return None, index
        line_no, current_indent, content = lines[index]
        if current_indent < indent:
            return None, index
        if current_indent > indent:
            raise FallbackYamlError(f"Line {line_no}: unexpected indentation")
        if content.startswith("- ") or content == "-":
            return parse_list(index, indent)
        return parse_mapping(index, indent)

    def parse_list(index: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(lines):
            line_no, current_indent, content = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise FallbackYamlError(f"Line {line_no}: unexpected indentation in list")
            if not (content.startswith("- ") or content == "-"):
                break
            item_text = content[1:].strip()
            index += 1
            if item_text == "":
                if index < len(lines) and lines[index][1] > indent:
                    item, index = parse_block(index, lines[index][1])
                    result.append(item)
                else:
                    result.append(None)
                continue
            key, value = split_key_value(item_text)
            if value is not None:
                item_dict: dict[Any, Any] = {parse_scalar(key): parse_scalar(value) if value != "" else None}
                if index < len(lines) and lines[index][1] > indent:
                    nested, index = parse_block(index, lines[index][1])
                    if isinstance(nested, dict):
                        item_dict.update(nested)
                    else:
                        raise FallbackYamlError(f"Line {line_no}: cannot merge non-mapping list item")
                result.append(item_dict)
            else:
                result.append(parse_scalar(item_text))
        return result, index

    def parse_mapping(index: int, indent: int) -> tuple[dict[Any, Any], int]:
        result: dict[Any, Any] = {}
        while index < len(lines):
            line_no, current_indent, content = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise FallbackYamlError(f"Line {line_no}: unexpected indentation in mapping")
            if content.startswith("- ") or content == "-":
                break
            key, value = split_key_value(content)
            if value is None or key == "":
                raise FallbackYamlError(f"Line {line_no}: expected 'key: value' mapping item")
            parsed_key = parse_scalar(key)
            index += 1
            if value == "":
                if index < len(lines) and lines[index][1] > indent:
                    parsed_value, index = parse_block(index, lines[index][1])
                else:
                    parsed_value = None
            else:
                parsed_value = parse_scalar(value)
            result[parsed_key] = parsed_value
        return result, index

    parsed, final_index = parse_block(0, lines[0][1])
    if final_index != len(lines):
        line_no = lines[final_index][0]
        raise FallbackYamlError(f"Line {line_no}: could not parse remaining YAML")
    return parsed


def load_yaml(text: str, reporter: Reporter) -> Any:
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception as err:  # pylint: disable=broad-except
            reporter.error(f"YAML parse error: {err}")
            return None
    reporter.note("PyYAML is not installed; using bundled minimal YAML parser")
    try:
        return parse_fallback_yaml(text)
    except FallbackYamlError as err:
        reporter.error(f"YAML parse error: {err}")
        return None


def is_mapping(value: Any) -> bool:
    return isinstance(value, dict)


def is_path_like(value: str) -> bool:
    if not value or "${" in value or REMOTE_LIKE.match(value):
        return False
    lowered = value.lower()
    suffixes = Path(lowered).suffixes
    if any(suffix in PATH_EXTENSIONS for suffix in suffixes):
        return True
    if "/" in value or "\\" in value:
        return True
    return False


def check_path(value: Any, label: str, config_dir: Path, reporter: Reporter) -> None:
    if not isinstance(value, str) or not is_path_like(value):
        return
    path = Path(value).expanduser()
    candidates = [path] if path.is_absolute() else [config_dir / path, Path.cwd() / path]
    exists = any(candidate.exists() for candidate in candidates)
    reporter.path_checks.append(
        {
            "label": label,
            "value": value,
            "exists": exists,
            "checked_relative_to_config": not path.is_absolute(),
            "checked_relative_to_cwd": not path.is_absolute(),
        }
    )
    if not exists:
        reporter.warn(
            f"Referenced local file for {label!s} does not exist relative to config dir or current working directory: {value}"
        )


def validate_top_level(config: Any, reporter: Reporter) -> None:
    if config is None:
        reporter.warn("YAML document is empty; AiZynthFinder would use defaults only")
        return
    if not is_mapping(config):
        reporter.error("Top-level YAML document must be a mapping")
        return
    for key in config:
        if key not in KNOWN_TOP_LEVEL:
            reporter.warn(f"Unknown top-level section '{key}'")


def validate_search(config: dict[str, Any], reporter: Reporter) -> None:
    search = config.get("search", {})
    if search is None:
        return
    if not is_mapping(search):
        reporter.error("search section must be a mapping")
        return
    for key, value in search.items():
        if key not in KNOWN_SEARCH_KEYS:
            reporter.error(f"Unknown search setting '{key}'")
        if key == "algorithm_config" and value is not None and not is_mapping(value):
            reporter.error("search.algorithm_config must be a mapping")
        if key in {"break_bonds", "freeze_bonds"}:
            validate_bonds(value, f"search.{key}", reporter)
        if key == "break_bonds_operator" and isinstance(value, str):
            if value.lower() not in {"and", "or"}:
                reporter.warn("search.break_bonds_operator is usually 'and' or 'or'")


def validate_bonds(value: Any, label: str, reporter: Reporter) -> None:
    if value in (None, []):
        return
    if not isinstance(value, list):
        reporter.error(f"{label} must be a list of 2-item lists")
        return
    for index, pair in enumerate(value):
        if not isinstance(pair, list) or len(pair) != 2:
            reporter.error(f"{label}[{index}] must be a 2-item list")
            continue
        for atom_index in pair:
            if not isinstance(atom_index, int):
                reporter.warn(f"{label}[{index}] contains a non-integer atom index")


def validate_post_processing(
    config: dict[str, Any], config_dir: Path, reporter: Reporter
) -> None:
    post_processing = config.get("post_processing", {})
    if post_processing is None:
        return
    if not is_mapping(post_processing):
        reporter.error("post_processing section must be a mapping")
        return
    for key, value in post_processing.items():
        if key not in KNOWN_POST_PROCESSING_KEYS:
            reporter.warn(f"Unknown post_processing setting '{key}'")
        if key in PATH_KEYS:
            check_path(value, f"post_processing.{key}", config_dir, reporter)


def validate_expansion(config: dict[str, Any], config_dir: Path, reporter: Reporter) -> None:
    expansion = config.get("expansion", {})
    if expansion is None:
        return
    if not is_mapping(expansion):
        reporter.error("expansion section must be a mapping of policy names to settings")
        return
    if not expansion:
        reporter.warn("No expansion policies are defined; planning needs at least one")
    defined_policies = set(expansion)
    for name, spec in expansion.items():
        label = f"expansion.{name}"
        if isinstance(spec, (list, tuple)):
            if len(spec) != 2:
                reporter.error(f"{label} short form must contain exactly [model, template]")
                continue
            check_path(spec[0], f"{label}.model", config_dir, reporter)
            check_path(spec[1], f"{label}.template", config_dir, reporter)
            continue
        if not is_mapping(spec):
            reporter.error(f"{label} must be a mapping or a two-item [model, template] list")
            continue
        strategy_type = str(spec.get("type", "template-based"))
        template_strategy_aliases = {
            "template-based",
            "TemplateBasedExpansionStrategy",
            "TemplateBasedDirectExpansionStrategy",
        }
        if strategy_type in template_strategy_aliases:
            if "model" not in spec:
                reporter.error(f"{label} is missing required model")
            if "template" not in spec:
                reporter.error(f"{label} is missing required template")
        elif "ExpansionStrategy" not in strategy_type:
            reporter.warn(
                f"{label} appears to use a custom expansion type; static validation cannot prove its required keys"
            )
        if "model" in spec:
            check_path(spec.get("model"), f"{label}.model", config_dir, reporter)
        if "template" in spec:
            check_path(spec.get("template"), f"{label}.template", config_dir, reporter)
        if "mask" in spec:
            check_path(spec.get("mask"), f"{label}.mask", config_dir, reporter)
        if "expansion_strategies" in spec:
            strategies = spec.get("expansion_strategies")
            if not isinstance(strategies, list) or not all(isinstance(item, str) for item in strategies):
                reporter.error(f"{label}.expansion_strategies must be a list of policy names")
            else:
                for referenced in strategies:
                    if referenced not in defined_policies:
                        reporter.error(
                            f"{label}.expansion_strategies references undefined policy '{referenced}'"
                        )
        if "expansion_strategy_weights" in spec:
            weights = spec.get("expansion_strategy_weights")
            if not isinstance(weights, list) or not all(isinstance(item, (int, float)) for item in weights):
                reporter.error(f"{label}.expansion_strategy_weights must be numeric list")
            elif abs(sum(weights) - 1.0) > 1e-9:
                reporter.error(f"{label}.expansion_strategy_weights must sum to 1")


def validate_filter(config: dict[str, Any], config_dir: Path, reporter: Reporter) -> None:
    filters = config.get("filter", {})
    if filters is None:
        return
    if not is_mapping(filters):
        reporter.error("filter section must be a mapping of filter names to settings")
        return
    for name, spec in filters.items():
        label = f"filter.{name}"
        if isinstance(spec, str):
            check_path(spec, f"{label}.model", config_dir, reporter)
            continue
        if not is_mapping(spec):
            reporter.error(f"{label} must be a model path string or a mapping")
            continue
        filter_type = str(spec.get("type", "quick-filter"))
        quick_filter_aliases = {"quick-filter", "feasibility", "quick_keras_filter", "QuickKerasFilter"}
        if filter_type in quick_filter_aliases and "model" not in spec:
            reporter.error(f"{label} quick-filter config is missing required model")
        if "model" in spec:
            check_path(spec.get("model"), f"{label}.model", config_dir, reporter)
        if "exclude_from_policy" in spec and not isinstance(spec.get("exclude_from_policy"), list):
            reporter.warn(f"{label}.exclude_from_policy is usually a list of expansion policy names")
        if filter_type in {"frozen_substructure", "FrozenSubstructureFilter"}:
            smarts_list = spec.get("smarts_list")
            if not isinstance(smarts_list, list):
                reporter.error(f"{label}.smarts_list must be a list for frozen-substructure filters")


def validate_stock(config: dict[str, Any], config_dir: Path, reporter: Reporter) -> None:
    stock = config.get("stock", {})
    if stock is None:
        return
    if not is_mapping(stock):
        reporter.error("stock section must be a mapping of stock names to settings")
        return
    if not stock:
        reporter.warn("No stocks are defined; planning normally needs at least one stock")
    for name, spec in stock.items():
        label = f"stock.{name}"
        if name == "stop_criteria":
            validate_stop_criteria(spec, reporter)
            continue
        if isinstance(spec, str):
            check_path(spec, f"{label}.path", config_dir, reporter)
            if spec.endswith(".bloom"):
                reporter.warn(f"{label} appears to be a molbloom stock; molbloom must be installed")
            continue
        if not is_mapping(spec):
            reporter.error(f"{label} must be a path string or a mapping")
            continue
        stock_type = str(spec.get("type", "inchiset"))
        if stock_type in {"inchiset", "InMemoryInchiKeyQuery", "bloom", "MolbloomFilterQuery"}:
            if "path" not in spec:
                reporter.error(f"{label} is missing required path")
            else:
                check_path(spec.get("path"), f"{label}.path", config_dir, reporter)
        if stock_type in {"mongodb", "MongoDbInchiKeyQuery"}:
            reporter.warn(f"{label} is a MongoDB stock; confirm pymongo, credentials, service, and collection schema")
            for key in ("host", "database", "collection"):
                if key in spec and not isinstance(spec.get(key), str):
                    reporter.warn(f"{label}.{key} should be a string")
        if stock_type in {"bloom", "MolbloomFilterQuery"}:
            reporter.warn(f"{label} is a molbloom stock; confirm optional molbloom dependency")
        if "price_col" in spec and "path" not in spec:
            reporter.warn(f"{label}.price_col is only useful for file-backed in-memory stocks")


def validate_stop_criteria(value: Any, reporter: Reporter) -> None:
    if value is None:
        return
    if not is_mapping(value):
        reporter.error("stock.stop_criteria must be a mapping")
        return
    for numeric_key in ("price", "amount", "weight"):
        if numeric_key in value and value[numeric_key] is not None and not isinstance(value[numeric_key], (int, float)):
            reporter.warn(f"stock.stop_criteria.{numeric_key} is usually numeric")
    counts = value.get("counts", value.get("size"))
    if counts is not None:
        if not is_mapping(counts):
            reporter.error("stock.stop_criteria.counts must be a mapping of element symbols to limits")
        else:
            for symbol, limit in counts.items():
                if not isinstance(symbol, str) or not isinstance(limit, int):
                    reporter.warn("stock.stop_criteria.counts entries should map element symbols to integer limits")


def scan_extra_path_like_values(
    node: Any,
    config_dir: Path,
    reporter: Reporter,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if not path and str(key) in {"expansion", "filter", "stock", "post_processing"}:
                continue
            next_path = path + (str(key),)
            if str(key) in PATH_KEYS:
                check_path(value, ".".join(next_path), config_dir, reporter)
            scan_extra_path_like_values(value, config_dir, reporter, next_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            scan_extra_path_like_values(value, config_dir, reporter, path + (str(index),))
    elif isinstance(node, str) and is_path_like(node):
        joined = ".".join(path) if path else "value"
        already_checked = any(item["label"] == joined and item["value"] == node for item in reporter.path_checks)
        if not already_checked:
            check_path(node, joined, config_dir, reporter)


def build_report(config_path: Path, reporter: Reporter) -> dict[str, Any]:
    return {
        "config": str(config_path),
        "ok": not reporter.errors,
        "errors": reporter.errors,
        "warnings": reporter.warnings,
        "info": reporter.info,
        "env": reporter.env,
        "path_checks": reporter.path_checks,
        "summary": {
            "error_count": len(reporter.errors),
            "warning_count": len(reporter.warnings),
            "path_check_count": len(reporter.path_checks),
        },
    }


def print_human(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"AiZynthFinder config static validation: {status}")
    print(f"Config: {report['config']}")
    summary = report["summary"]
    print(
        f"Errors: {summary['error_count']}  Warnings: {summary['warning_count']}  "
        f"Path checks: {summary['path_check_count']}"
    )
    if report["env"]["resolved"]:
        print("Resolved env vars: " + ", ".join(report["env"]["resolved"]))
    if report["env"]["missing"]:
        print("Missing env vars: " + ", ".join(report["env"]["missing"]))
    if report["errors"]:
        print("\nErrors:")
        for item in report["errors"]:
            print(f"- {item}")
    if report["warnings"]:
        print("\nWarnings:")
        for item in report["warnings"]:
            print(f"- {item}")
    if report["path_checks"]:
        print("\nPath checks:")
        for item in report["path_checks"]:
            marker = "exists" if item["exists"] else "missing"
            print(f"- {item['label']}: {item['value']} ({marker})")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    reporter = Reporter()
    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        reporter.error(f"Config file does not exist: {config_path}")
        report = build_report(config_path, reporter)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_human(report)
        return 2

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as err:
        reporter.error(f"Could not read config file: {err}")
        report = build_report(config_path, reporter)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_human(report)
        return 2

    resolved_text = resolve_env_placeholders(text, reporter)
    config = load_yaml(resolved_text, reporter)
    validate_top_level(config, reporter)

    if is_mapping(config):
        config_dir = config_path.resolve().parent
        validate_search(config, reporter)
        validate_post_processing(config, config_dir, reporter)
        validate_expansion(config, config_dir, reporter)
        validate_filter(config, config_dir, reporter)
        validate_stock(config, config_dir, reporter)
        scan_extra_path_like_values(config, config_dir, reporter)

    report = build_report(config_path, reporter)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    if reporter.errors:
        return 1
    if args.strict_warnings and reporter.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
