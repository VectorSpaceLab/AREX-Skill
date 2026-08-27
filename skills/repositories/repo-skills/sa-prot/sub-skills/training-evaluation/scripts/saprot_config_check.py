#!/usr/bin/env python3
"""Safe SaProt YAML config diagnostics without importing ML frameworks."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


MISSING = object()
PATH_KEY_RE = re.compile(r"(?:^|_)(path|dir|lmdb)$|^(?:path|dir|lmdb)$", re.IGNORECASE)
MODULE_PATH_KEYS = {"model_py_path", "dataset_py_path"}
TOP_LEVEL_REQUIRED = ("setting", "model", "dataset", "Trainer")


def strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    result = []
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or line[index - 1].isspace():
                break
        result.append(char)
    return "".join(result).rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"~", "null", "Null", "NULL"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = []
        current = []
        in_single = False
        in_double = False
        for char in inner:
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            if char == "," and not in_single and not in_double:
                items.append(parse_scalar("".join(current).strip()))
                current = []
            else:
                current.append(char)
        if current or inner.endswith(","):
            items.append(parse_scalar("".join(current).strip()))
        return items
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value) or re.fullmatch(
        r"[-+]?\d+[eE][-+]?\d+", value
    ):
        try:
            return float(value)
        except ValueError:
            pass
    return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[: len(raw_line) - len(raw_line.lstrip(" "))].count("\t"):
            raise ValueError(f"line {line_number}: tabs are not supported")
        line = strip_inline_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if content.startswith("-"):
            raise ValueError(f"line {line_number}: list blocks are not supported by this diagnostic parser")
        if ":" not in content:
            raise ValueError(f"line {line_number}: expected 'key: value'")
        key, value = content.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"line {line_number}: empty key")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"line {line_number}: invalid indentation")
        parent = stack[-1][1]
        if value.strip() == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except Exception:
        return parse_simple_yaml(text)
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ValueError("config root must be a mapping")
    return loaded


def get_nested(data: Dict[str, Any], path: Iterable[str], default: Any = MISSING) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            if default is MISSING:
                return None
            return default
        current = current[part]
    return current


def flatten_paths(value: Any, prefix: Tuple[str, ...] = ()) -> List[Tuple[str, Any]]:
    rows: List[Tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_prefix = prefix + (str(key),)
            if str(key) not in MODULE_PATH_KEYS and PATH_KEY_RE.search(str(key)) and item is not None:
                rows.append((".".join(next_prefix), item))
            rows.extend(flatten_paths(item, next_prefix))
    return rows


def resolve_candidate(path_value: Any, repo_root: Path) -> Path | None:
    if not isinstance(path_value, str) or not path_value:
        return None
    if any(char in path_value for char in "*?["):
        return None
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


def visible_cuda_count(cuda_visible_devices: Any) -> int | None:
    if cuda_visible_devices is None:
        return None
    text = str(cuda_visible_devices).strip()
    if text in {"", "-1"}:
        return 0
    return len([part for part in text.split(",") if part.strip()])


def summarize_config(config: Dict[str, Any], config_path: Path, repo_root: Path, check_exists: bool) -> Dict[str, Any]:
    warnings: List[str] = []
    errors: List[str] = []

    top_level = sorted(config.keys())
    for section in TOP_LEVEL_REQUIRED:
        if section not in config:
            errors.append(f"missing top-level section: {section}")
        elif not isinstance(config[section], dict):
            errors.append(f"top-level section is not a mapping: {section}")

    setting = config.get("setting", {}) if isinstance(config.get("setting"), dict) else {}
    model = config.get("model", {}) if isinstance(config.get("model"), dict) else {}
    dataset = config.get("dataset", {}) if isinstance(config.get("dataset"), dict) else {}
    trainer = config.get("Trainer", {}) if isinstance(config.get("Trainer"), dict) else {}
    os_environ = setting.get("os_environ", {}) if isinstance(setting.get("os_environ"), dict) else {}
    model_kwargs = model.get("kwargs", {}) if isinstance(model.get("kwargs"), dict) else {}
    dataloader_kwargs = dataset.get("dataloader_kwargs", {}) if isinstance(dataset.get("dataloader_kwargs"), dict) else {}

    trainer_summary = {
        "accelerator": trainer.get("accelerator"),
        "devices": trainer.get("devices"),
        "precision": trainer.get("precision"),
        "logger": trainer.get("logger"),
        "num_nodes": trainer.get("num_nodes"),
        "strategy": trainer.get("strategy"),
        "max_epochs": trainer.get("max_epochs"),
        "max_steps": trainer.get("max_steps"),
        "min_steps": trainer.get("min_steps"),
        "limit_train_batches": trainer.get("limit_train_batches"),
        "limit_val_batches": trainer.get("limit_val_batches"),
        "limit_test_batches": trainer.get("limit_test_batches"),
    }

    dataset_paths = []
    for dotted, value in flatten_paths(dataset, ("dataset",)):
        dataset_paths.append({"key": dotted, "value": value})
    special_paths = {
        "model.kwargs.config_path": model_kwargs.get("config_path"),
        "model.kwargs.foldseek_path": model_kwargs.get("foldseek_path"),
        "model.kwargs.log_dir": model_kwargs.get("log_dir"),
        "model.save_path": model.get("save_path"),
        "setting.dataset_dir": setting.get("dataset_dir"),
        "setting.out_path": setting.get("out_path"),
    }

    existence = []
    if check_exists:
        for key, value in list(special_paths.items()) + [(row["key"], row["value"]) for row in dataset_paths]:
            candidate = resolve_candidate(value, repo_root)
            if candidate is None:
                continue
            exists = candidate.exists()
            existence.append({"key": key, "path": str(candidate), "exists": exists})
            if not exists and key not in {"setting.out_path", "model.kwargs.log_dir", "model.save_path"}:
                warnings.append(f"path does not exist for {key}: {value}")

    foldseek_path = model_kwargs.get("foldseek_path")
    if isinstance(foldseek_path, str) and Path(foldseek_path).is_absolute():
        warnings.append("model.kwargs.foldseek_path is absolute; verify it is valid on this machine")
    if model_kwargs.get("log_clinvar") and not model_kwargs.get("log_dir"):
        warnings.append("model.kwargs.log_clinvar is true but model.kwargs.log_dir is not set")

    devices = as_int(trainer.get("devices"))
    cuda_visible = os_environ.get("CUDA_VISIBLE_DEVICES")
    visible_count = visible_cuda_count(cuda_visible)
    accelerator = trainer.get("accelerator")
    if accelerator == "gpu" and devices is not None and visible_count is not None and visible_count and devices > visible_count:
        warnings.append("Trainer.devices exceeds the number of CUDA_VISIBLE_DEVICES entries")
    if accelerator == "gpu" and devices is not None and devices > 1:
        warnings.append("Trainer requests multiple GPU devices; ask before launching full runs")
    if as_int(trainer.get("num_nodes")) and as_int(trainer.get("num_nodes")) > 1:
        warnings.append("Trainer.num_nodes is greater than 1; verify distributed environment settings")
    if str(os_environ.get("NODE_RANK", "0")) != "0" and trainer.get("logger"):
        warnings.append("NODE_RANK is not 0; training launcher disables logger on non-root nodes")
    if trainer.get("logger"):
        warnings.append("Trainer.logger is enabled; verify WandB settings and credentials")
    if as_int(dataloader_kwargs.get("num_workers")) and as_int(dataloader_kwargs.get("num_workers")) > 4:
        warnings.append("dataloader num_workers is high for diagnostics; reduce for smoke tests")
    max_steps = as_int(trainer.get("max_steps"))
    min_steps = as_int(trainer.get("min_steps"))
    max_epochs = as_int(trainer.get("max_epochs"))
    if (max_steps and max_steps >= 100000) or (min_steps and min_steps >= 100000) or (max_epochs and max_epochs >= 50):
        warnings.append("config appears to describe a long or expensive training run")
    if setting.get("dataset_dir") and not setting.get("out_path") and "ProteinGym" in str(setting.get("dataset_dir")):
        warnings.append("ProteinGym-style zero-shot config has dataset_dir but no out_path")
    if trainer.get("precision") in {16, "16", "16-mixed"} and accelerator == "cpu":
        warnings.append("CPU diagnostics should use precision 32, not fp16")

    return {
        "config_path": str(config_path),
        "repo_root": str(repo_root),
        "top_level_sections": top_level,
        "errors": errors,
        "warnings": warnings,
        "model_py_path": model.get("model_py_path"),
        "dataset_py_path": dataset.get("dataset_py_path"),
        "model_kwargs": {
            "config_path": model_kwargs.get("config_path"),
            "foldseek_path": model_kwargs.get("foldseek_path"),
            "log_clinvar": model_kwargs.get("log_clinvar"),
            "log_dir": model_kwargs.get("log_dir"),
            "load_pretrained": model_kwargs.get("load_pretrained"),
            "use_lora": model_kwargs.get("use_lora"),
        },
        "dataset_paths": dataset_paths,
        "dataloader_kwargs": dataloader_kwargs,
        "special_paths": special_paths,
        "trainer": trainer_summary,
        "os_environ": {
            "CUDA_VISIBLE_DEVICES": os_environ.get("CUDA_VISIBLE_DEVICES"),
            "MASTER_ADDR": os_environ.get("MASTER_ADDR"),
            "MASTER_PORT": os_environ.get("MASTER_PORT"),
            "WORLD_SIZE": os_environ.get("WORLD_SIZE"),
            "NODE_RANK": os_environ.get("NODE_RANK"),
            "WANDB_API_KEY": "<set>" if os_environ.get("WANDB_API_KEY") else None,
            "WANDB_RUN_ID": "<set>" if os_environ.get("WANDB_RUN_ID") else None,
            "WANDB_MODE": os_environ.get("WANDB_MODE"),
        },
        "wandb_config": setting.get("wandb_config"),
        "existence": existence,
    }


def print_human(summary: Dict[str, Any]) -> None:
    print("SaProt config diagnostic")
    print(f"  config: {summary['config_path']}")
    print(f"  repo_root: {summary['repo_root']}")
    print(f"  top_level_sections: {', '.join(summary['top_level_sections']) or '<none>'}")
    print(f"  model_py_path: {summary.get('model_py_path')}")
    print(f"  dataset_py_path: {summary.get('dataset_py_path')}")

    print("\nModel kwargs")
    for key, value in summary["model_kwargs"].items():
        print(f"  {key}: {value}")

    print("\nDataset paths")
    if summary["dataset_paths"]:
        for row in summary["dataset_paths"]:
            print(f"  {row['key']}: {row['value']}")
    else:
        print("  <none found>")

    print("\nSpecial paths")
    for key, value in summary["special_paths"].items():
        print(f"  {key}: {value}")

    print("\nTrainer")
    for key, value in summary["trainer"].items():
        if value is not None:
            print(f"  {key}: {value}")

    print("\nDistributed/env")
    for key, value in summary["os_environ"].items():
        if value is not None:
            print(f"  {key}: {value}")

    if summary["existence"]:
        print("\nExistence checks")
        for row in summary["existence"]:
            status = "ok" if row["exists"] else "missing"
            print(f"  [{status}] {row['key']}: {row['path']}")

    if summary["warnings"]:
        print("\nWarnings")
        for warning in summary["warnings"]:
            print(f"  - {warning}")

    if summary["errors"]:
        print("\nErrors")
        for error in summary["errors"]:
            print(f"  - {error}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inspect a SaProt training/evaluation YAML config.")
    parser.add_argument("-c", "--config", required=True, help="Path to a SaProt YAML config.")
    parser.add_argument("--repo-root", default=".", help="Root used to resolve relative config paths for --check-exists.")
    parser.add_argument("--check-exists", action="store_true", help="Check existence of discovered input paths.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config_path = Path(args.config).expanduser()
    repo_root = Path(args.repo_root).expanduser().resolve()

    try:
        config = load_yaml(config_path)
        summary = summarize_config(config, config_path, repo_root, args.check_exists)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human(summary)
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
