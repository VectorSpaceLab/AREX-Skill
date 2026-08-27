#!/usr/bin/env python3
"""Static validator for PARL Waymax-RL Hydra YAML configs.

This script deliberately avoids importing JAX, Waymax, TensorFlow, Torch,
Hydra, or rl-games. It reads a YAML file, reports launch-critical Waymax-RL
settings, and exits nonzero only for static launch blockers.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable


PLACEHOLDER_PATTERNS = (
    "your_data_path",
    "replace",
    "change_me",
    "changeme",
    "todo",
    "placeholder",
    "<",
    ">",
)


class SimpleYAMLError(ValueError):
    """Raised when the built-in fallback YAML parser cannot parse input."""


def strip_inline_comment(line: str) -> str:
    """Remove YAML comments outside single/double quoted strings."""
    in_single = False
    in_double = False
    escaped = False
    out = []
    for ch in line:
        if ch == "\\" and in_double and not escaped:
            escaped = True
            out.append(ch)
            continue
        if ch == "'" and not in_double and not escaped:
            in_single = not in_single
        elif ch == '"' and not in_single and not escaped:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
        escaped = False
    return "".join(out).rstrip()


def parse_scalar(raw: str) -> Any:
    """Parse a conservative subset of YAML scalar values."""
    value = raw.strip()
    if value == "":
        return None
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"none", "null", "~"}:
        return None
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value[1:-1]
    if value.startswith("[") or value.startswith("{"):
        pythonish = re.sub(r"\btrue\b", "True", value, flags=re.IGNORECASE)
        pythonish = re.sub(r"\bfalse\b", "False", pythonish, flags=re.IGNORECASE)
        pythonish = re.sub(r"\bnull\b", "None", pythonish, flags=re.IGNORECASE)
        try:
            return ast.literal_eval(pythonish)
        except Exception:
            return value
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except Exception:
            pass
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", value):
        try:
            return float(value)
        except Exception:
            pass
    return value


def preprocess_simple_yaml(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for line_no, original in enumerate(text.splitlines(), start=1):
        if "\t" in original[: len(original) - len(original.lstrip("\t "))]:
            raise SimpleYAMLError(f"tabs in indentation at line {line_no}")
        stripped_comment = strip_inline_comment(original)
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        lines.append((indent, stripped_comment.strip()))
    return lines


def parse_key_value(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise SimpleYAMLError(f"expected 'key: value', got {content!r}")
    key, raw = content.split(":", 1)
    key = key.strip()
    if not key:
        raise SimpleYAMLError(f"empty key in {content!r}")
    if (key.startswith("'") and key.endswith("'")) or (
        key.startswith('"') and key.endswith('"')
    ):
        key = str(parse_scalar(key))
    return key, raw.strip()


def parse_simple_block(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start
    first_indent, first_content = lines[start]
    if first_indent != indent:
        raise SimpleYAMLError(
            f"internal indentation mismatch: expected {indent}, got {first_indent}"
        )

    if first_content.startswith("- "):
        result: list[Any] = []
        i = start
        while i < len(lines):
            cur_indent, content = lines[i]
            if cur_indent < indent:
                break
            if cur_indent > indent:
                raise SimpleYAMLError(f"unexpected indentation before {content!r}")
            if not content.startswith("- "):
                break
            item = content[2:].strip()
            if item == "":
                if i + 1 < len(lines) and lines[i + 1][0] > indent:
                    child, i = parse_simple_block(lines, i + 1, lines[i + 1][0])
                    result.append(child)
                else:
                    result.append(None)
                    i += 1
            elif ":" in item and not item.startswith(("'", '"')):
                key, raw = parse_key_value(item)
                mapping: dict[str, Any] = {}
                if raw == "":
                    if i + 1 < len(lines) and lines[i + 1][0] > indent:
                        child, i = parse_simple_block(lines, i + 1, lines[i + 1][0])
                        mapping[key] = child
                    else:
                        mapping[key] = {}
                        i += 1
                else:
                    mapping[key] = parse_scalar(raw)
                    i += 1
                result.append(mapping)
            else:
                result.append(parse_scalar(item))
                i += 1
        return result, i

    result_map: dict[str, Any] = {}
    i = start
    while i < len(lines):
        cur_indent, content = lines[i]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise SimpleYAMLError(f"unexpected indentation before {content!r}")
        if content.startswith("- "):
            break
        key, raw = parse_key_value(content)
        if raw == "":
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                child, i = parse_simple_block(lines, i + 1, lines[i + 1][0])
                result_map[key] = child
            else:
                result_map[key] = {}
                i += 1
        else:
            result_map[key] = parse_scalar(raw)
            i += 1
    return result_map, i


def simple_yaml_load(text: str) -> Any:
    lines = preprocess_simple_yaml(text)
    if not lines:
        return {}
    root_indent = lines[0][0]
    data, index = parse_simple_block(lines, 0, root_indent)
    if index != len(lines):
        raise SimpleYAMLError(f"could not parse line {index + 1}: {lines[index][1]!r}")
    return data


def load_yaml(path: Path) -> tuple[Any, str]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text), "PyYAML"
    except ModuleNotFoundError:
        return simple_yaml_load(text), "built-in simple parser"
    except Exception as exc:
        raise SimpleYAMLError(f"YAML parser failed: {exc}") from exc


def as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def get_path(root: Any, keys: Iterable[str], default: Any = None) -> Any:
    cur = root
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def find_training_config(cfg: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    root = as_mapping(cfg)
    params = as_mapping(root.get("params", root))
    train_cfg = as_mapping(params.get("config", root.get("config", {})))
    return params, train_cfg


def is_placeholder_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return True
    lowered = value.lower()
    return any(pattern in lowered for pattern in PLACEHOLDER_PATTERNS)


def is_interpolated(value: Any) -> bool:
    return isinstance(value, str) and "${" in value


def value_text(value: Any) -> str:
    if value is None:
        return "<missing>"
    return repr(value)


def boolish(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "<missing>"
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Statically validate a PARL Waymax-RL Hydra YAML config without "
            "importing JAX, Waymax, TensorFlow, Torch, Hydra, or starting training."
        )
    )
    parser.add_argument("config", type=Path, help="Path to the Hydra-style YAML config")
    args = parser.parse_args(argv)

    config_path = args.config
    if not config_path.exists():
        print(f"ERROR: config file does not exist: {config_path}", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"ERROR: config path is not a file: {config_path}", file=sys.stderr)
        return 2

    try:
        cfg, parser_name = load_yaml(config_path)
    except Exception as exc:
        print(f"ERROR: failed to parse YAML: {exc}", file=sys.stderr)
        return 2

    params, train_cfg = find_training_config(cfg)
    env_cfg = as_mapping(train_cfg.get("env_config", {}))
    data_cfg = as_mapping(env_cfg.get("data_cfg", {}))

    errors: list[str] = []
    warnings: list[str] = []

    outer_env_name = train_cfg.get("env_name")
    inner_env_name = env_cfg.get("env_name")
    backend = env_cfg.get("backend")
    data_type = data_cfg.get("data_type")
    data_path = data_cfg.get("data_path")
    mixed_precision = train_cfg.get("mixed_precision")
    multi_gpu = train_cfg.get("multi_gpu")
    num_actors = train_cfg.get("num_actors")
    horizon_length = train_cfg.get("horizon_length")
    minibatch_size = train_cfg.get("minibatch_size")
    max_num_objects = env_cfg.get("max_num_objects")

    if not train_cfg:
        errors.append("missing params.config mapping")
    if not env_cfg:
        errors.append("missing params.config.env_config mapping")

    if outer_env_name != "waymax":
        warnings.append(f"params.config.env_name is {value_text(outer_env_name)}; expected 'waymax'")
    if inner_env_name != "waymax":
        warnings.append(
            f"params.config.env_config.env_name is {value_text(inner_env_name)}; expected 'waymax'"
        )

    if backend != "gpu":
        errors.append(
            f"params.config.env_config.backend is {value_text(backend)}; Waymax-RL expects 'gpu'"
        )

    if data_type != "tfrecord":
        warnings.append(
            f"data_cfg.data_type is {value_text(data_type)}; only 'tfrecord' is fully evidenced"
        )

    placeholder = is_placeholder_path(data_path)
    interpolated = is_interpolated(data_path)
    path_status = "not checked"
    if placeholder:
        errors.append(f"data_cfg.data_path is missing or placeholder-like: {value_text(data_path)}")
        path_status = "placeholder"
    elif interpolated:
        warnings.append("data_cfg.data_path contains Hydra interpolation; existence was not checked")
        path_status = "interpolated"
    elif isinstance(data_path, str):
        candidate = Path(os.path.expanduser(data_path))
        if candidate.exists():
            path_status = "directory" if candidate.is_dir() else "file"
        else:
            warnings.append(f"data_cfg.data_path does not exist from this shell: {data_path}")
            path_status = "missing"
    else:
        errors.append(f"data_cfg.data_path must be a string, got {type(data_path).__name__}")

    if mixed_precision is None:
        warnings.append("mixed_precision flag is missing")
    if multi_gpu is None:
        warnings.append("multi_gpu flag is missing")
    elif multi_gpu is True:
        warnings.append("multi_gpu is true; this needs separate JAX and rl-games runtime verification")

    rollout_samples = None
    if isinstance(num_actors, int) and isinstance(horizon_length, int):
        rollout_samples = num_actors * horizon_length
        if isinstance(minibatch_size, int) and minibatch_size > rollout_samples:
            warnings.append(
                f"minibatch_size ({minibatch_size}) is larger than num_actors*horizon_length ({rollout_samples})"
            )

    print(f"Config: {config_path}")
    print(f"YAML parser: {parser_name}")
    print("\nWaymax-RL static summary")
    print(f"  params.config.env_name: {value_text(outer_env_name)}")
    print(f"  env_config.env_name: {value_text(inner_env_name)}")
    print(f"  env_config.backend: {value_text(backend)} (expected 'gpu')")
    print(f"  data_cfg.data_type: {value_text(data_type)}")
    print(f"  data_cfg.data_path: {value_text(data_path)}")
    print(f"  data_path status: {path_status}")
    print(f"  mixed_precision: {boolish(mixed_precision)}")
    print(f"  multi_gpu: {boolish(multi_gpu)}")
    print(f"  num_actors: {value_text(num_actors)}")
    print(f"  horizon_length: {value_text(horizon_length)}")
    print(f"  minibatch_size: {value_text(minibatch_size)}")
    print(f"  max_num_objects: {value_text(max_num_objects)}")
    if rollout_samples is not None:
        print(f"  rollout actor-steps: {rollout_samples}")

    if warnings:
        print("\nWarnings")
        for item in warnings:
            print(f"  - {item}")

    if errors:
        print("\nValidation errors")
        for item in errors:
            print(f"  - {item}")
        print("\nResult: not launch-ready for Waymax-RL all-GPU training")
        return 1

    print("\nResult: no static launch blockers found")
    print(
        "Reminder: this script did not import JAX/Waymax or verify GPU availability; "
        "run explicit runtime checks before training."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
