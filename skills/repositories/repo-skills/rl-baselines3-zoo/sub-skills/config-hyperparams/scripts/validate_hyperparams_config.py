#!/usr/bin/env python3
"""Validate RL Zoo hyperparameter configs without training.

Safe default behavior:
- YAML files are parsed with yaml.safe_load.
- Python files/modules are inspected statically unless --import-python is set.
- The script never launches training, downloads models, or touches network
  resources on its own.

It checks common RL Zoo config pitfalls:
- missing env-specific/default/atari coverage
- missing n_timesteps or policy fields
- malformed wrapper/callback list items and kwargs indentation
- schedule strings such as lin_0.001
- eval-backed string fields such as policy_kwargs, normalize, and
  monitor_kwargs
- order-sensitive vec_env_wrapper / frame_stack combinations

Use --import-python only for trusted Python config files or modules that need
execution to expose the final hyperparams dictionary.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on environment
    raise SystemExit("PyYAML is required to validate YAML hyperparameter files.") from exc


SEVERITY_RANK = {"info": 0, "warn": 1, "error": 2}
REQUIRED_FIELDS = ("n_timesteps", "policy")
SCHEDULE_KEYS = ("learning_rate", "clip_range", "clip_range_vf", "delta_std")
EVAL_DICT_KEYS = ("policy_kwargs", "replay_buffer_kwargs", "monitor_kwargs")
WRAPPER_KEYS = ("env_wrapper", "vec_env_wrapper", "callback")


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    path: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


def issue(severity: str, code: str, message: str, path: str = "") -> Issue:
    return Issue(severity=severity, code=code, message=message, path=path)


def path_label(path: str | Path) -> str:
    return str(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate RL Zoo hyperparameter configs without training.",
    )
    parser.add_argument("config", help="YAML file, Python file, or importable Python module path.")
    parser.add_argument("--env-id", help="Optional environment id to check fallback selection.")
    parser.add_argument(
        "--env-kind",
        choices=("auto", "atari", "non-atari"),
        default="auto",
        help="How to resolve fallback selection when --env-id is provided.",
    )
    parser.add_argument("--algo", help="Optional algorithm name for context in messages.")
    parser.add_argument(
        "--import-python",
        action="store_true",
        help="Execute a Python config file/module instead of static inspection.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of plain text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors for exit-code purposes.",
    )
    return parser.parse_args(argv)


def resolve_config_source(config: str) -> tuple[str, Path | None, str]:
    """Resolve a config path or importable Python module.

    Returns (kind, path, label) where kind is one of:
    - yaml-file
    - python-file
    - python-module
    """

    candidate = Path(config)
    if candidate.exists():
        if candidate.suffix.lower() in {".yml", ".yaml"}:
            return "yaml-file", candidate, path_label(candidate)
        if candidate.suffix.lower() == ".py":
            return "python-file", candidate, path_label(candidate)
        raise SystemExit(f"Unsupported config file extension: {candidate.suffix}")

    spec = importlib.util.find_spec(config)
    if spec is None or spec.origin is None:
        raise SystemExit(f"Could not resolve config source: {config}")

    origin = spec.origin
    if origin in {"built-in", "namespace"}:
        raise SystemExit(f"Config module {config!r} has no file origin to inspect")

    origin_path = Path(origin)
    if origin_path.suffix.lower() in {".yml", ".yaml"}:
        return "yaml-file", origin_path, f"{config} -> {origin_path}"
    if origin_path.suffix.lower() == ".py":
        return "python-module", origin_path, f"{config} -> {origin_path}"

    raise SystemExit(f"Unsupported config module origin: {origin_path}")


def safe_eval_node(node: ast.AST) -> Any:
    """Evaluate a restricted Python expression tree for static inspection.

    Unsupported nodes are returned as a source-string representation so that
    the validator can still inspect top-level dict shapes without executing the
    file.
    """

    try:
        return ast.literal_eval(node)
    except Exception:
        pass

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        if node.args:
            return ast.unparse(node)
        result: dict[Any, Any] = {}
        for keyword in node.keywords:
            if keyword.arg is None:
                return ast.unparse(node)
            result[keyword.arg] = safe_eval_node(keyword.value)
        return result

    if isinstance(node, ast.Dict):
        result: dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values, strict=True):
            if key_node is None:
                return ast.unparse(node)
            key = safe_eval_node(key_node)
            if isinstance(key, (dict, list, tuple, set)):
                key = ast.unparse(key_node)
            result[key] = safe_eval_node(value_node)
        return result

    if isinstance(node, ast.List):
        return [safe_eval_node(element) for element in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(safe_eval_node(element) for element in node.elts)

    if isinstance(node, ast.Set):
        return [safe_eval_node(element) for element in node.elts]

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = safe_eval_node(node.operand)
        if isinstance(operand, (int, float)) and not isinstance(operand, bool):
            return operand if isinstance(node.op, ast.UAdd) else -operand

    return ast.unparse(node)


def load_yaml_config(path: Path) -> tuple[dict[str, Any] | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        issues.append(issue("error", "yaml-parse-error", f"Failed to parse YAML: {exc}", path_label(path)))
        return None, issues

    if not isinstance(data, dict):
        issues.append(
            issue(
                "error",
                "bad-top-level-type",
                f"Top-level YAML object must be a mapping, got {type(data).__name__}",
                path_label(path),
            )
        )
        return None, issues

    return data, issues


def load_python_static(path: Path) -> tuple[dict[str, Any] | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception as exc:
        issues.append(issue("error", "python-source-error", f"Failed to parse Python source: {exc}", path_label(path)))
        return None, issues

    hyperparams_value: Any | None = None
    found = False
    for stmt in tree.body:
        target_nodes: list[ast.AST] = []
        value_node: ast.AST | None = None
        if isinstance(stmt, ast.Assign):
            target_nodes = list(stmt.targets)
            value_node = stmt.value
        elif isinstance(stmt, ast.AnnAssign):
            target_nodes = [stmt.target]
            value_node = stmt.value
        else:
            continue

        for target in target_nodes:
            if isinstance(target, ast.Name) and target.id == "hyperparams" and value_node is not None:
                hyperparams_value = safe_eval_node(value_node)
                found = True

    if not found:
        issues.append(
            issue(
                "error",
                "python-missing-hyperparams",
                "Python config did not define a top-level hyperparams variable.",
                path_label(path),
            )
        )
        return None, issues

    if not isinstance(hyperparams_value, dict):
        issues.append(
            issue(
                "error",
                "bad-top-level-type",
                f"hyperparams must evaluate to a mapping, got {type(hyperparams_value).__name__}",
                path_label(path),
            )
        )
        return None, issues

    return hyperparams_value, issues


def load_python_import(path: Path, source: str, kind: str) -> tuple[dict[str, Any] | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        if kind == "python-module":
            namespace = importlib.import_module(source).__dict__
        else:
            namespace = runpy.run_path(str(path), run_name="__rl_zoo_config__")
    except Exception as exc:
        issues.append(issue("error", "python-source-error", f"Failed to execute/import Python config: {exc}", source))
        return None, issues

    if "hyperparams" not in namespace:
        issues.append(
            issue(
                "error",
                "python-missing-hyperparams",
                "Python config did not expose a top-level hyperparams variable.",
                source,
            )
        )
        return None, issues

    hyperparams_value = namespace["hyperparams"]
    if not isinstance(hyperparams_value, dict):
        issues.append(
            issue(
                "error",
                "bad-top-level-type",
                f"hyperparams must be a mapping, got {type(hyperparams_value).__name__}",
                source,
            )
        )
        return None, issues

    return hyperparams_value, issues


def load_config(source: str, import_python: bool) -> tuple[dict[str, Any] | None, list[Issue], str]:
    kind, path, label = resolve_config_source(source)
    if kind == "yaml-file":
        data, issues = load_yaml_config(path) if path is not None else (None, [issue("error", "bad-top-level-type", "Missing YAML path.")])
        return data, issues, label

    assert path is not None
    if import_python:
        data, issues = load_python_import(path, source, kind)
    else:
        data, issues = load_python_static(path)
    return data, issues, label


def is_type_like(value: Any) -> bool:
    return isinstance(value, type)


def stringify_target(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return repr(value)


def validate_python_expression(value: str, *, expect_mapping: bool) -> tuple[ast.AST | None, Issue | None]:
    try:
        expr = ast.parse(value, mode="eval").body
    except SyntaxError as exc:
        return None, issue("error", "bad-expr", f"Invalid Python expression: {exc.msg}")

    if expect_mapping:
        if isinstance(expr, (ast.Dict, ast.Call)):
            return expr, None
        return expr, issue(
            "warn",
            "bad-expr",
            f"Expression parses, but this field normally expects a dict-like expression; got {type(expr).__name__}.",
        )

    return expr, None


def validate_schedule_value(key: str, value: Any) -> list[Issue]:
    issues: list[Issue] = []
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return issues
    if isinstance(value, str):
        if not value.startswith("lin_"):
            issues.append(
                issue(
                    "error",
                    "bad-schedule",
                    f"{key} uses a string value but does not start with lin_: {value!r}",
                    key,
                )
            )
            return issues
        suffix = value[4:]
        try:
            float(suffix)
        except ValueError:
            issues.append(
                issue(
                    "error",
                    "bad-schedule",
                    f"{key} schedule suffix is not numeric: {value!r}",
                    key,
                )
            )
        return issues

    issues.append(
        issue(
            "error",
            "bad-type",
            f"{key} must be a number or lin_<float> string, got {type(value).__name__}",
            key,
        )
    )
    return issues


def validate_required_number(value: Any, key: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    if isinstance(value, bool):
        issues.append(issue("error", "bad-type", f"{key} must be numeric, got bool.", path))
        return issues
    if isinstance(value, (int, float)):
        if float(value) <= 0:
            issues.append(issue("error", "bad-type", f"{key} must be positive, got {value!r}.", path))
        return issues
    if isinstance(value, str):
        try:
            if float(value) <= 0:
                raise ValueError
            return issues
        except ValueError:
            issues.append(issue("error", "bad-type", f"{key} must be positive numeric, got {value!r}.", path))
            return issues
    issues.append(issue("error", "bad-type", f"{key} must be numeric, got {type(value).__name__}.", path))
    return issues


def validate_optional_positive_int(value: Any, key: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    if isinstance(value, bool):
        issues.append(issue("error", "bad-type", f"{key} must be a positive integer, got bool.", path))
        return issues
    if isinstance(value, int):
        if value <= 0:
            issues.append(issue("error", "bad-type", f"{key} must be positive, got {value!r}.", path))
        return issues
    if isinstance(value, str):
        try:
            if int(value) <= 0:
                raise ValueError
            return issues
        except ValueError:
            issues.append(issue("error", "bad-type", f"{key} must be a positive integer, got {value!r}.", path))
            return issues
    issues.append(issue("error", "bad-type", f"{key} must be an integer, got {type(value).__name__}.", path))
    return issues


def validate_env_wrapper_item(item: Any, key: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    if isinstance(item, str):
        if not item.strip():
            issues.append(issue("error", "bad-wrapper-item", f"Empty wrapper target in {key}.", path))
        return issues

    if is_type_like(item):
        return issues

    if isinstance(item, dict):
        if len(item) != 1:
            issues.append(
                issue(
                    "error",
                    "bad-wrapper-item",
                    f"Each {key} mapping item must have exactly one key; got {len(item)} keys.",
                    path,
                )
            )
            return issues

        target, kwargs = next(iter(item.items()))
        if not isinstance(target, str) and not is_type_like(target):
            issues.append(
                issue(
                    "error",
                    "bad-wrapper-item",
                    f"Wrapper target must be a string or class object, got {type(target).__name__}.",
                    path,
                )
            )
        if kwargs is None:
            return issues
        if not isinstance(kwargs, dict):
            issues.append(
                issue(
                    "error",
                    "bad-wrapper-item",
                    f"Wrapper kwargs for {stringify_target(target)!r} must be a mapping, got {type(kwargs).__name__}.",
                    path,
                )
            )
        return issues

    issues.append(
        issue(
            "error",
            "bad-wrapper-item",
            f"{key} items must be strings, class objects, or single-key mappings, got {type(item).__name__}.",
            path,
        )
    )
    return issues


def validate_callback_item(item: Any, key: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    if isinstance(item, str) or is_type_like(item):
        if isinstance(item, str) and not item.strip():
            issues.append(issue("error", "bad-wrapper-item", f"Empty callback target in {key}.", path))
        return issues

    if isinstance(item, dict):
        if len(item) != 1:
            issues.append(
                issue(
                    "error",
                    "bad-wrapper-item",
                    f"Each {key} mapping item must have exactly one key; got {len(item)} keys.",
                    path,
                )
            )
            return issues

        target, kwargs = next(iter(item.items()))
        if not isinstance(target, str) and not is_type_like(target):
            issues.append(
                issue(
                    "error",
                    "bad-wrapper-item",
                    f"Callback target must be a string or class object, got {type(target).__name__}.",
                    path,
                )
            )
        if kwargs is None:
            return issues
        if not isinstance(kwargs, dict):
            issues.append(
                issue(
                    "error",
                    "bad-wrapper-item",
                    f"Callback kwargs for {stringify_target(target)!r} must be a mapping, got {type(kwargs).__name__}.",
                    path,
                )
            )
        return issues

    issues.append(
        issue(
            "warn",
            "bad-wrapper-item",
            f"Callback item has type {type(item).__name__}; only strings, class objects, dicts, and callback instances are expected.",
            path,
        )
    )
    return issues


def validate_wrapper_field(key: str, value: Any, path: str) -> list[Issue]:
    issues: list[Issue] = []
    if value is None:
        return issues
    if isinstance(value, list):
        for item in value:
            if key == "callback":
                issues.extend(validate_callback_item(item, key, path))
            else:
                issues.extend(validate_env_wrapper_item(item, key, path))
        return issues
    if key == "callback":
        issues.extend(validate_callback_item(value, key, path))
    else:
        issues.extend(validate_env_wrapper_item(value, key, path))
    return issues


def validate_entry(name: str, entry: Any, args: argparse.Namespace) -> list[Issue]:
    issues: list[Issue] = []
    entry_path = name

    if not isinstance(entry, dict):
        issues.append(
            issue(
                "error",
                "bad-top-level-type",
                f"Entry {name!r} must be a mapping, got {type(entry).__name__}",
                entry_path,
            )
        )
        return issues

    for field in REQUIRED_FIELDS:
        if field not in entry:
            issues.append(issue("error", "missing-field", f"Missing required field {field!r} in entry {name!r}.", entry_path))

    if "n_timesteps" in entry:
        issues.extend(validate_required_number(entry["n_timesteps"], "n_timesteps", entry_path))

    if "policy" in entry:
        policy = entry["policy"]
        if not isinstance(policy, (str,)) and not is_type_like(policy):
            issues.append(
                issue(
                    "error",
                    "bad-type",
                    f"policy must be a string or class object, got {type(policy).__name__}.",
                    entry_path,
                )
            )
    
    if "n_envs" in entry:
        issues.extend(validate_optional_positive_int(entry["n_envs"], "n_envs", entry_path))
    if "frame_stack" in entry:
        issues.extend(validate_optional_positive_int(entry["frame_stack"], "frame_stack", entry_path))

    for key in SCHEDULE_KEYS:
        if key in entry:
            issues.extend(validate_schedule_value(key, entry[key]))

    if "normalize" in entry:
        normalize = entry["normalize"]
        if isinstance(normalize, bool) or isinstance(normalize, dict):
            pass
        elif isinstance(normalize, str):
            expr, expr_issue = validate_python_expression(normalize, expect_mapping=False)
            if expr_issue is not None:
                issues.append(expr_issue)
            elif not isinstance(expr, (ast.Dict, ast.Call, ast.Constant)):
                issues.append(
                    issue(
                        "warn",
                        "bad-expr",
                        f"normalize parses but does not look like a bool/dict-like expression: {type(expr).__name__}.",
                        entry_path,
                    )
                )
        else:
            issues.append(
                issue(
                    "error",
                    "bad-type",
                    f"normalize must be bool, dict, or Python-expression string, got {type(normalize).__name__}.",
                    entry_path,
                )
            )

    if "env_kwargs" in entry:
        env_kwargs = entry["env_kwargs"]
        if not isinstance(env_kwargs, dict):
            issues.append(
                issue(
                    "error",
                    "bad-type",
                    f"env_kwargs must be a mapping in config files, got {type(env_kwargs).__name__}.",
                    entry_path,
                )
            )

    for key in EVAL_DICT_KEYS:
        if key not in entry:
            continue
        value = entry[key]
        if isinstance(value, dict):
            continue
        if isinstance(value, str):
            expr, expr_issue = validate_python_expression(value, expect_mapping=True)
            if expr_issue is not None:
                issues.append(expr_issue)
            if expr is not None and not isinstance(expr, (ast.Dict, ast.Call)):
                issues.append(
                    issue(
                        "warn",
                        "bad-expr",
                        f"{key} parses but does not look dict-like; runtime eval may fail or return the wrong type.",
                        entry_path,
                    )
                )
            continue
        issues.append(
            issue(
                "error",
                "bad-type",
                f"{key} must be a mapping or Python-expression string, got {type(value).__name__}.",
                entry_path,
            )
        )

    if "replay_buffer_class" in entry:
        replay_buffer_class = entry["replay_buffer_class"]
        if not isinstance(replay_buffer_class, (str,)) and not is_type_like(replay_buffer_class):
            issues.append(
                issue(
                    "error",
                    "bad-type",
                    f"replay_buffer_class must be a string or class object, got {type(replay_buffer_class).__name__}.",
                    entry_path,
                )
            )
        elif isinstance(replay_buffer_class, str):
            expr, expr_issue = validate_python_expression(replay_buffer_class, expect_mapping=False)
            if expr_issue is not None:
                issues.append(expr_issue)
            if expr is None:
                issues.append(
                    issue(
                        "error",
                        "bad-expr",
                        f"Could not parse replay_buffer_class expression {replay_buffer_class!r}.",
                        entry_path,
                    )
                )

    if "train_freq" in entry:
        train_freq = entry["train_freq"]
        if isinstance(train_freq, list):
            if len(train_freq) != 2:
                issues.append(
                    issue(
                        "error",
                        "bad-type",
                        f"train_freq list form must have exactly 2 items, got {len(train_freq)}.",
                        entry_path,
                    )
                )
            elif not isinstance(train_freq[1], str):
                issues.append(
                    issue(
                        "warn",
                        "bad-type",
                        "train_freq list form normally uses a step/episode string as the second item.",
                        entry_path,
                    )
                )
        elif not isinstance(train_freq, (int, float)):
            issues.append(
                issue(
                    "warn",
                    "bad-type",
                    f"train_freq is usually an int or [frequency, unit] list; got {type(train_freq).__name__}.",
                    entry_path,
                )
            )

    if "noise_type" in entry and "noise_std" not in entry:
        issues.append(issue("warn", "missing-field", "noise_type is set but noise_std is missing.", entry_path))
    if "noise_std" in entry and "noise_type" not in entry:
        issues.append(issue("warn", "missing-field", "noise_std is set but noise_type is missing.", entry_path))

    for key in WRAPPER_KEYS:
        if key in entry:
            issues.extend(validate_wrapper_field(key, entry[key], entry_path))

    if "vec_env_wrapper" in entry and "frame_stack" in entry:
        vec_wrapper = entry["vec_env_wrapper"]
        target_names: list[str] = []
        values = vec_wrapper if isinstance(vec_wrapper, list) else [vec_wrapper]
        for item in values:
            if isinstance(item, dict) and len(item) == 1:
                target_names.append(stringify_target(next(iter(item.keys()))))
            else:
                target_names.append(stringify_target(item))
        if any("VecFrameStack" in name for name in target_names):
            issues.append(
                issue(
                    "warn",
                    "frame-stack-wrapper-conflict",
                    "frame_stack is set and vec_env_wrapper also references VecFrameStack; prefer one frame-stacking path.",
                    entry_path,
                )
            )

    if "normalize" in entry and "frame_stack" in entry and "vec_env_wrapper" in entry:
        issues.append(
            issue(
                "warn",
                "frame-stack-wrapper-conflict",
                "normalize, frame_stack, and vec_env_wrapper are all set; wrapper order is sensitive, so verify the intended stack order.",
                entry_path,
            )
        )

    return issues


def select_entry(data: dict[str, Any], env_id: str | None, env_kind: str) -> tuple[str | None, list[Issue]]:
    issues: list[Issue] = []
    if env_id is None:
        return None, issues

    if env_id in data:
        issues.append(issue("info", "selected-entry", f"Using exact entry {env_id!r}.", env_id))
        return env_id, issues

    has_default = "default" in data
    has_atari = "atari" in data

    if env_kind == "atari":
        if has_atari:
            issues.append(issue("info", "selected-entry", f"Using Atari fallback for {env_id!r}.", "atari"))
            return "atari", issues
        issues.append(issue("error", "missing-entry", f"No exact entry for {env_id!r} and no atari fallback is available.", env_id))
        return None, issues

    if env_kind == "non-atari":
        if has_default:
            issues.append(issue("info", "selected-entry", f"Using default fallback for {env_id!r}.", "default"))
            return "default", issues
        issues.append(issue("error", "missing-entry", f"No exact entry for {env_id!r} and no default fallback is available.", env_id))
        return None, issues

    # auto
    if has_default:
        issues.append(
            issue(
                "info",
                "selected-entry",
                f"Using default fallback for {env_id!r}. If this env is Atari, rerun with --env-kind atari.",
                "default",
            )
        )
        return "default", issues
    if has_atari:
        issues.append(
            issue(
                "error",
                "missing-entry",
                f"No exact entry for {env_id!r}; an Atari fallback exists but auto mode does not assume Atari semantics.",
                env_id,
            )
        )
        return None, issues

    issues.append(issue("error", "missing-entry", f"No exact entry for {env_id!r} and no fallback entry is available.", env_id))
    return None, issues


def validate_config(data: dict[str, Any], args: argparse.Namespace) -> list[Issue]:
    issues: list[Issue] = []

    if not data:
        issues.append(issue("error", "bad-top-level-type", "Config mapping is empty."))
        return issues

    if args.env_id is not None:
        _, selection_issues = select_entry(data, args.env_id, args.env_kind)
        issues.extend(selection_issues)
    else:
        if "default" not in data and "atari" not in data:
            issues.append(
                issue(
                    "info",
                    "missing-fallback",
                    "No default or atari fallback entry is present. That is fine for exact-only configs, but non-listed envs will fail.",
                )
            )

    for name, entry in data.items():
        if not isinstance(name, str):
            issues.append(issue("error", "bad-top-level-type", f"Top-level key {name!r} is not a string.", str(name)))
        issues.extend(validate_entry(name, entry, args))

    return issues


def print_text_report(issues: list[Issue], source_label: str, args: argparse.Namespace) -> int:
    has_errors = any(item.severity == "error" for item in issues)
    has_warnings = any(item.severity == "warn" for item in issues)
    status = "error" if has_errors else ("warn" if has_warnings else "ok")

    print(f"Source: {source_label}")
    if args.algo:
        print(f"Algorithm: {args.algo}")
    if args.env_id:
        print(f"Env id: {args.env_id}")
        print(f"Env kind: {args.env_kind}")
    print(f"Status: {status}")

    if not issues:
        print("No issues found.")
        return 0

    for item in issues:
        location = f" [{item.path}]" if item.path else ""
        print(f"{item.severity.upper():5s} {item.code}{location}: {item.message}")

    return 1 if has_errors or (args.strict and has_warnings) else 0


def print_json_report(issues: list[Issue], source_label: str, args: argparse.Namespace) -> int:
    has_errors = any(item.severity == "error" for item in issues)
    has_warnings = any(item.severity == "warn" for item in issues)
    status = "error" if has_errors else ("warn" if has_warnings else "ok")
    payload = {
        "status": status,
        "source": source_label,
        "algo": args.algo,
        "env_id": args.env_id,
        "env_kind": args.env_kind,
        "issues": [item.to_dict() for item in issues],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if has_errors or (args.strict and has_warnings) else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data, load_issues, source_label = load_config(args.config, args.import_python)
    issues = list(load_issues)
    if data is not None:
        issues.extend(validate_config(data, args))

    if args.json:
        return print_json_report(issues, source_label, args)
    return print_text_report(issues, source_label, args)


if __name__ == "__main__":
    raise SystemExit(main())
