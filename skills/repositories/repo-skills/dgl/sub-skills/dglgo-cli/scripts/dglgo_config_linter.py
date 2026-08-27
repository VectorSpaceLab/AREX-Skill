#!/usr/bin/env python3
"""Safely lint DGL-Go YAML configs without importing DGL-Go or training."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised only when PyYAML is absent
    yaml = None

KNOWN_TRAIN_PIPELINES = {"nodepred", "nodepred-ns", "linkpred", "graphpred"}
KNOWN_APPLY_PIPELINES = {"nodepred", "nodepred-ns", "graphpred"}
KNOWN_MODES = {"train", "apply"}
COMMON_TOP_KEYS = {"version", "pipeline_name", "pipeline_mode", "device", "data", "general_pipeline"}
DEVICE_RE = re.compile(r"^(cpu|cuda(?::\d+)?)$")


class FallbackYamlError(ValueError):
    """Raised when the built-in minimal YAML parser cannot read a file."""


def strip_comment(line: str) -> str:
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


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", value):
            return float(value)
    except Exception:
        pass
    return value


def next_significant(lines: list[tuple[int, str]], start: int) -> tuple[int, str] | None:
    for index in range(start, len(lines)):
        return lines[index]
    return None


def parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    next_line = next_significant(lines, index)
    if next_line is None:
        return {}, index
    if next_line[0] < indent:
        return {}, index
    if next_line[0] > indent:
        indent = next_line[0]
    if next_line[1].startswith("- "):
        return parse_list(lines, index, indent)
    return parse_mapping(lines, index, indent)


def parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise FallbackYamlError(f"Unexpected indentation near: {text}")
        if not text.startswith("- "):
            break
        item_text = text[2:].strip()
        index += 1
        if item_text == "":
            child, index = parse_block(lines, index, indent + 2)
            result.append(child)
        elif ":" in item_text and not item_text.startswith(("'", '"')):
            key, value = item_text.split(":", 1)
            item: dict[str, Any] = {key.strip(): parse_scalar(value)}
            if index < len(lines) and lines[index][0] > indent:
                child, index = parse_mapping(lines, index, lines[index][0])
                if isinstance(child, dict):
                    item.update(child)
            result.append(item)
        else:
            result.append(parse_scalar(item_text))
    return result, index


def parse_mapping(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise FallbackYamlError(f"Unexpected indentation near: {text}")
        if text.startswith("- "):
            break
        if ":" not in text:
            raise FallbackYamlError(f"Expected key: value mapping near: {text}")
        key, value = text.split(":", 1)
        key = key.strip()
        if not key:
            raise FallbackYamlError(f"Empty key near: {text}")
        value = value.strip()
        index += 1
        if value == "":
            if index < len(lines) and lines[index][0] > indent:
                child, index = parse_block(lines, index, lines[index][0])
                result[key] = child
            elif index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
                child, index = parse_list(lines, index, indent)
                result[key] = child
            else:
                result[key] = None
        else:
            result[key] = parse_scalar(value)
    return result, index


def fallback_yaml_load(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip("\t "))]:
            raise FallbackYamlError("Tabs in indentation are not supported.")
        stripped = strip_comment(raw_line)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.strip()))
    if not lines:
        return None
    parsed, index = parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise FallbackYamlError(f"Could not parse line: {lines[index][1]}")
    return parsed


def load_yaml(path: pathlib.Path) -> tuple[Any, list[str], list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [f"Config file does not exist: {path}"], []
    except Exception as exc:
        return None, [f"Could not read config file: {exc}"], []

    if yaml is not None:
        try:
            return yaml.safe_load(text), [], []
        except Exception as exc:
            return None, [f"YAML parse error: {exc}"], []

    try:
        return fallback_yaml_load(text), [], ["PyYAML is not installed; used built-in parser for simple DGL-Go YAML."]
    except Exception as exc:
        return None, [f"YAML parse error with built-in parser: {exc}"], ["Install PyYAML for full YAML syntax support."]


def is_mapping(value: Any) -> bool:
    return isinstance(value, dict)


def is_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple))


def check_mapping(cfg: Any) -> list[str]:
    if cfg is None:
        return ["YAML document is empty."]
    if not is_mapping(cfg):
        return ["Top-level YAML document must be a mapping/object."]
    return []


def lint_split_ratio(value: Any, path: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if value is None:
        return errors, warnings
    if not is_sequence(value) or len(value) != 3:
        errors.append(f"{path} should be a list of three numbers such as [0.8, 0.1, 0.1].")
        return errors, warnings
    try:
        floats = [float(item) for item in value]
    except Exception:
        errors.append(f"{path} should contain only numeric values.")
        return errors, warnings
    if any(item < 0 for item in floats):
        errors.append(f"{path} should not contain negative values.")
    total = sum(floats)
    if abs(total - 1.0) > 1e-6:
        warnings.append(f"{path} sums to {total:.6g}; DGL-Go examples expect train/val/test ratios summing to 1.0.")
    return errors, warnings


def lint_device(value: Any) -> list[str]:
    if not isinstance(value, str):
        return ["device should be a string such as cpu, cuda, or cuda:0."]
    if not DEVICE_RE.match(value):
        return [f"device {value!r} is unusual; expected cpu, cuda, or cuda:N."]
    return []


def lint_cfg(cfg: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for key in ["pipeline_name", "pipeline_mode", "device", "data", "general_pipeline"]:
        if key not in cfg:
            errors.append(f"Missing required top-level key: {key}")

    pipeline_name = cfg.get("pipeline_name")
    pipeline_mode = cfg.get("pipeline_mode")

    if pipeline_mode not in KNOWN_MODES:
        errors.append(f"pipeline_mode must be one of {sorted(KNOWN_MODES)}, got {pipeline_mode!r}.")
    if pipeline_mode == "train" and pipeline_name not in KNOWN_TRAIN_PIPELINES:
        errors.append(f"train pipeline_name must be one of {sorted(KNOWN_TRAIN_PIPELINES)}, got {pipeline_name!r}.")
    if pipeline_mode == "apply" and pipeline_name not in KNOWN_APPLY_PIPELINES:
        errors.append(f"apply pipeline_name must be one of {sorted(KNOWN_APPLY_PIPELINES)}, got {pipeline_name!r}.")
    if pipeline_name == "linkpred" and pipeline_mode == "apply":
        errors.append("linkpred apply is not registered in the inspected DGL-Go source; use train/export only unless your installed version proves otherwise.")

    if "device" in cfg:
        warnings.extend(lint_device(cfg.get("device")))
    if "eval_device" in cfg:
        warnings.extend([f"eval_{msg}" for msg in lint_device(cfg.get("eval_device"))])

    data = cfg.get("data")
    if not is_mapping(data):
        errors.append("data must be a mapping with at least name.")
        data = {}
    elif "name" not in data:
        errors.append("data.name is required.")

    general = cfg.get("general_pipeline")
    if not is_mapping(general):
        errors.append("general_pipeline must be a mapping.")
        general = {}

    split_errors, split_warnings = lint_split_ratio(data.get("split_ratio"), "data.split_ratio")
    errors.extend(split_errors)
    warnings.extend(split_warnings)

    if data.get("name") == "csv":
        if not data.get("data_path"):
            warnings.append("data.name is csv; set data.data_path to the directory containing metadata and CSV graph files.")
        if data.get("split_ratio") is None:
            warnings.append("data.name is csv; set data.split_ratio when CSV data has no native train/val/test masks or splits.")

    save_path = general.get("save_path") if is_mapping(general) else None
    if pipeline_mode == "train":
        if pipeline_name in {"nodepred", "nodepred-ns", "graphpred"}:
            model = cfg.get("model")
            if not is_mapping(model):
                errors.append(f"{pipeline_name} training config requires model mapping.")
            elif "name" not in model:
                errors.append("model.name is required.")
        if pipeline_name == "linkpred":
            for section in ["node_model", "edge_model", "neg_sampler"]:
                value = cfg.get(section)
                if not is_mapping(value):
                    errors.append(f"linkpred training config requires {section} mapping.")
                elif "name" not in value:
                    errors.append(f"{section}.name is required.")
            if data.get("split_ratio") is not None and data.get("neg_ratio") is None:
                errors.append("linkpred configs with data.split_ratio must also set data.neg_ratio.")
        if pipeline_name == "nodepred-ns":
            sampler = general.get("sampler") if is_mapping(general) else None
            if not is_mapping(sampler):
                errors.append("nodepred-ns requires general_pipeline.sampler mapping.")
            else:
                if sampler.get("name") != "neighbor":
                    warnings.append("nodepred-ns examples use general_pipeline.sampler.name: neighbor.")
                fan_out = sampler.get("fan_out")
                model = cfg.get("model")
                num_layers = model.get("num_layers") if is_mapping(model) else None
                if fan_out is not None and not is_sequence(fan_out):
                    errors.append("general_pipeline.sampler.fan_out should be a list of integers.")
                if isinstance(num_layers, int) and is_sequence(fan_out) and len(fan_out) != num_layers:
                    errors.append("model.num_layers should equal len(general_pipeline.sampler.fan_out) for nodepred-ns.")
        if not save_path:
            warnings.append("general_pipeline.save_path is not set; DGL-Go checkpoints are usually saved as save_path/run_i.pth.")
    elif pipeline_mode == "apply":
        if "cpt_path" not in cfg:
            errors.append("apply config requires cpt_path pointing to a DGL-Go checkpoint such as results/run_0.pth.")
        elif not isinstance(cfg.get("cpt_path"), str):
            errors.append("cpt_path should be a string path.")
        elif not re.search(r"run_\d+\.pth$", cfg.get("cpt_path", "")):
            warnings.append("cpt_path does not end with run_i.pth; DGL-Go training templates usually save checkpoints that way.")
        if not save_path:
            warnings.append("apply general_pipeline.save_path is not set; generated apply configs usually use apply_results.")

    unknown = sorted(set(cfg) - COMMON_TOP_KEYS - {"eval_device", "model", "node_model", "edge_model", "neg_sampler", "cpt_path"})
    for key in unknown:
        warnings.append(f"Unknown top-level key {key!r}; verify it is consumed by your installed DGL-Go version.")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely lint a DGL-Go YAML config without importing dglgo or running training.")
    parser.add_argument("config", type=pathlib.Path, help="Path to a DGL-Go YAML config.")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Exit non-zero when warnings are present.")
    args = parser.parse_args(argv)

    loaded, load_errors, parser_warnings = load_yaml(args.config)
    for warning in parser_warnings:
        print(f"WARNING: {warning}")
    if load_errors:
        for error in load_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    shape_errors = check_mapping(loaded)
    if shape_errors:
        for error in shape_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    errors, warnings = lint_cfg(loaded)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        return 1
    if (warnings or parser_warnings) and args.warnings_as_errors:
        return 1
    print(f"OK: {args.config} looks like a DGL-Go {loaded.get('pipeline_name')} {loaded.get('pipeline_mode')} config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
