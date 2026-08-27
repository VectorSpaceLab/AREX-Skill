#!/usr/bin/env python3
"""Static validator for projects based on TensorFlow Project Template.

This helper checks file presence, JSON config keys, class hooks, and TF1-style
symbol usage without importing TensorFlow or executing training. It can be run
against any copied template checkout:

    python scripts/check_template_static.py --repo-root /path/to/template-copy
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

EXPECTED_FILES = [
    "base/base_model.py",
    "base/base_train.py",
    "models/example_model.py",
    "models/template_model.py",
    "trainers/example_trainer.py",
    "trainers/template_trainer.py",
    "data_loader/data_generator.py",
    "utils/config.py",
    "utils/dirs.py",
    "utils/logger.py",
    "utils/utils.py",
    "mains/example.py",
    "configs/example.json",
]

REQUIRED_CONFIG_KEYS = {
    "exp_name",
    "num_epochs",
    "num_iter_per_epoch",
    "learning_rate",
    "batch_size",
    "state_size",
    "max_to_keep",
}

CLASS_REQUIREMENTS = {
    "base/base_model.py": {"BaseModel": {"save", "load", "init_cur_epoch", "init_global_step", "init_saver", "build_model"}},
    "base/base_train.py": {"BaseTrain": {"train", "train_epoch", "train_step"}},
    "models/example_model.py": {"ExampleModel": {"build_model", "init_saver"}},
    "models/template_model.py": {"TemplateModel": {"build_model", "init_saver"}},
    "trainers/example_trainer.py": {"ExampleTrainer": {"train_epoch", "train_step"}},
    "trainers/template_trainer.py": {"TemplateTrainer": {"train_epoch", "train_step"}},
    "data_loader/data_generator.py": {"DataGenerator": {"next_batch"}},
    "utils/logger.py": {"Logger": {"summarize"}},
}

INHERITANCE_EXPECTATIONS = {
    ("models/example_model.py", "ExampleModel"): "BaseModel",
    ("models/template_model.py", "TemplateModel"): "BaseModel",
    ("trainers/example_trainer.py", "ExampleTrainer"): "BaseTrain",
    ("trainers/template_trainer.py", "TemplateTrainer"): "BaseTrain",
}

TF1_SYMBOL_CHECKS = {
    "base/base_model.py": ["tf.variable_scope", "tf.Variable", "tf.assign", "tf.train.latest_checkpoint"],
    "models/example_model.py": ["tf.placeholder", "tf.layers.dense", "tf.train.AdamOptimizer", "tf.train.Saver"],
    "base/base_train.py": ["tf.global_variables_initializer", "tf.local_variables_initializer"],
    "mains/example.py": ["tf.Session"],
    "utils/logger.py": ["tf.summary.FileWriter", "tf.summary.scalar", "tf.summary.image"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate TensorFlow Project Template structure without executing training.")
    parser.add_argument("--repo-root", default=".", help="Path to the template checkout or copied project to validate.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser.parse_args()


def load_ast(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def class_defs(tree: ast.Module) -> Dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def method_names(class_node: ast.ClassDef) -> set:
    return {node.name for node in class_node.body if isinstance(node, ast.FunctionDef)}


def base_names(class_node: ast.ClassDef) -> set:
    names = set()
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def check_files(repo_root: Path) -> Tuple[List[str], List[str]]:
    passed, failed = [], []
    for rel in EXPECTED_FILES:
        path = repo_root / rel
        if path.is_file():
            passed.append(f"present: {rel}")
        else:
            failed.append(f"missing expected file: {rel}")
    return passed, failed


def check_config(repo_root: Path) -> Tuple[List[str], List[str], List[str]]:
    passed, failed, warnings = [], [], []
    config_path = repo_root / "configs/example.json"
    if not config_path.is_file():
        return passed, ["cannot validate config keys because configs/example.json is missing"], warnings
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return passed, [f"configs/example.json is invalid JSON: {exc}"], warnings
    missing = sorted(REQUIRED_CONFIG_KEYS - set(data))
    extra = sorted(set(data) - REQUIRED_CONFIG_KEYS)
    if missing:
        failed.append(f"configs/example.json missing keys: {missing}")
    else:
        passed.append("configs/example.json contains all expected template keys")
    if extra:
        warnings.append(f"configs/example.json has additional project-specific keys: {extra}")
    if not isinstance(data.get("state_size"), list):
        failed.append("configs/example.json state_size should be a list, e.g. [784]")
    if isinstance(data.get("batch_size"), int) and data["batch_size"] <= 0:
        failed.append("configs/example.json batch_size should be positive")
    return passed, failed, warnings


def check_classes(repo_root: Path) -> Tuple[List[str], List[str]]:
    passed, failed = [], []
    for rel, classes in CLASS_REQUIREMENTS.items():
        path = repo_root / rel
        if not path.is_file():
            continue
        try:
            defs = class_defs(load_ast(path))
        except SyntaxError as exc:
            failed.append(f"{rel} has syntax error: {exc}")
            continue
        for class_name, required_methods in classes.items():
            cls = defs.get(class_name)
            if cls is None:
                failed.append(f"{rel} missing class {class_name}")
                continue
            missing_methods = sorted(required_methods - method_names(cls))
            if missing_methods:
                failed.append(f"{rel}:{class_name} missing methods {missing_methods}")
            else:
                passed.append(f"{rel}:{class_name} exposes required methods")
            expected_base = INHERITANCE_EXPECTATIONS.get((rel, class_name))
            if expected_base and expected_base not in base_names(cls):
                failed.append(f"{rel}:{class_name} should inherit {expected_base}")
    return passed, failed


def check_tf1_symbols(repo_root: Path) -> Tuple[List[str], List[str]]:
    passed, failed = [], []
    for rel, symbols in TF1_SYMBOL_CHECKS.items():
        path = repo_root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        missing = [symbol for symbol in symbols if symbol not in text]
        if missing:
            failed.append(f"{rel} missing expected TF1 symbol text: {missing}")
        else:
            passed.append(f"{rel} contains expected TF1 symbol usage")
    return passed, failed


def emit_text(passed: Iterable[str], warnings: Iterable[str], failed: Iterable[str]) -> None:
    for line in passed:
        print(f"PASS {line}")
    for line in warnings:
        print(f"WARN {line}")
    for line in failed:
        print(f"FAIL {line}")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    passed: List[str] = []
    warnings: List[str] = []
    failed: List[str] = []

    if not repo_root.exists():
        failed.append(f"repo root does not exist: {repo_root}")
    elif not repo_root.is_dir():
        failed.append(f"repo root is not a directory: {repo_root}")
    else:
        p, f = check_files(repo_root)
        passed.extend(p)
        failed.extend(f)
        p, f, w = check_config(repo_root)
        passed.extend(p)
        failed.extend(f)
        warnings.extend(w)
        p, f = check_classes(repo_root)
        passed.extend(p)
        failed.extend(f)
        p, f = check_tf1_symbols(repo_root)
        passed.extend(p)
        failed.extend(f)

    if args.json:
        print(json.dumps({"passed": passed, "warnings": warnings, "failed": failed}, indent=2, sort_keys=True))
    else:
        emit_text(passed, warnings, failed)
        print(f"SUMMARY passed={len(passed)} warnings={len(warnings)} failed={len(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
