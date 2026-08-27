#!/usr/bin/env python3
"""Validate a Graphormer custom dataset registration contract.

Safe default behavior:
- installs a tiny `graphormer.data` registry shim for the imported user module
- records `@register_dataset(...)` names without calling the decorated functions
- lists what was registered and explains how to opt into full validation

Full validation requires `--execute-registrations`, because Graphormer's real
`register_dataset` contract executes the decorated function during import, and
those functions often construct datasets that may download data.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

ALLOWED_SOURCES = {"dgl", "pyg"}
REQUIRED_KEYS = ("dataset", "train_idx", "valid_idx", "test_idx", "source")


@dataclass
class DeferredRegistration:
    """Registration captured without executing the dataset factory."""

    name: str
    function_path: str
    function: Any


@contextlib.contextmanager
def prepend_sys_path(path: Path):
    path_str = str(path)
    inserted = False
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
        inserted = True
    try:
        yield
    finally:
        if inserted:
            try:
                sys.path.remove(path_str)
            except ValueError:
                pass


def function_path(func: Any) -> str:
    module = getattr(func, "__module__", "<unknown>")
    name = getattr(func, "__qualname__", getattr(func, "__name__", "<unknown>"))
    return f"{module}.{name}"


def make_register_dataset(registry: Dict[str, Any], execute: bool):
    def register_dataset(name: str):
        def decorator(func):
            if execute:
                registry[name] = func()
            else:
                registry[name] = DeferredRegistration(name, function_path(func), func)
            return func

        return decorator

    return register_dataset


@contextlib.contextmanager
def graphormer_data_shim(execute: bool):
    """Temporarily provide graphormer.data with the registry API only."""

    saved_graphormer = sys.modules.get("graphormer")
    saved_data = sys.modules.get("graphormer.data")
    had_graphormer = "graphormer" in sys.modules
    had_data = "graphormer.data" in sys.modules

    registry: Dict[str, Any] = {}
    graphormer_module = ModuleType("graphormer")
    graphormer_module.__path__ = []  # mark as package-like for import machinery
    data_module = ModuleType("graphormer.data")
    data_module.DATASET_REGISTRY = registry
    data_module.register_dataset = make_register_dataset(registry, execute)
    graphormer_module.data = data_module

    sys.modules["graphormer"] = graphormer_module
    sys.modules["graphormer.data"] = data_module
    try:
        yield registry
    finally:
        if had_data:
            sys.modules["graphormer.data"] = saved_data  # type: ignore[assignment]
        else:
            sys.modules.pop("graphormer.data", None)
        if had_graphormer:
            sys.modules["graphormer"] = saved_graphormer  # type: ignore[assignment]
        else:
            sys.modules.pop("graphormer", None)


def load_installed_registry() -> Mapping[str, Any]:
    try:
        from graphormer.data import DATASET_REGISTRY
    except Exception as exc:  # pragma: no cover - import failure is environment specific
        raise RuntimeError(
            "failed to import graphormer.data.DATASET_REGISTRY"
        ) from exc
    if not isinstance(DATASET_REGISTRY, dict):
        raise RuntimeError(
            "expected graphormer.data.DATASET_REGISTRY to be a dict, "
            f"got {type(DATASET_REGISTRY).__name__}"
        )
    return DATASET_REGISTRY


def stable_module_name(path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"graphormer_user_module_{path.stem}_{digest}"


def import_python_file(path: Path) -> ModuleType:
    module_name = stable_module_name(path)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from file path: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    with prepend_sys_path(path.parent.resolve()):
        spec.loader.exec_module(module)
    return module


def import_directory(path: Path) -> ModuleType:
    package_name = path.name
    parent = path.parent.resolve()
    importlib.invalidate_caches()
    with prepend_sys_path(parent):
        module = importlib.import_module(package_name)
        for child in sorted(path.iterdir()):
            if child.name.startswith(("_", ".")):
                continue
            if child.is_file() and child.suffix == ".py":
                importlib.import_module(f"{package_name}.{child.stem}")
            elif child.is_dir():
                importlib.import_module(f"{package_name}.{child.name}")
        return module


def import_user_module(spec: str) -> ModuleType:
    path = Path(spec).expanduser()
    if path.exists():
        if path.is_file():
            return import_python_file(path)
        if path.is_dir():
            return import_directory(path)
        raise ImportError(f"module path exists but is neither file nor directory: {spec}")

    if any(sep in spec for sep in ("/", "\\")) or spec.endswith(".py"):
        raise FileNotFoundError(f"module path does not exist: {spec}")

    return importlib.import_module(spec)


def safe_len(value: Any) -> Optional[int]:
    try:
        return len(value)
    except Exception:
        return None


def describe_value(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, DeferredRegistration):
        return f"deferred({value.function_path})"
    value_type = type(value).__name__
    length = safe_len(value)
    if length is None:
        return value_type
    return f"{value_type}(len={length})"


def registry_summary(registry: Mapping[str, Any]) -> str:
    lines = [f"registered datasets: {len(registry)}"]
    for name in sorted(registry):
        entry = registry[name]
        if isinstance(entry, DeferredRegistration):
            lines.append(f"- {name}: deferred factory {entry.function_path}")
            continue
        if not isinstance(entry, dict):
            lines.append(f"- {name}: non-dict {type(entry).__name__}")
            continue
        source = entry.get("source", "<missing>")
        keys = ", ".join(sorted(entry))
        split_bits = ", ".join(
            f"{split}={describe_value(entry.get(split))}"
            for split in ("train_idx", "valid_idx", "test_idx")
        )
        lines.append(f"- {name}: source={source}; {split_bits}; keys=[{keys}]")
    return "\n".join(lines)


def validate_entry(name: str, entry: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if isinstance(entry, DeferredRegistration):
        errors.append(
            f"{name}: registration factory was not executed; rerun with --execute-registrations "
            "only when dataset construction is safe in this environment"
        )
        return errors, warnings

    if not isinstance(entry, dict):
        errors.append(f"{name}: expected a dict, got {type(entry).__name__}")
        return errors, warnings

    missing = [key for key in REQUIRED_KEYS if key not in entry]
    if missing:
        errors.append(f"{name}: missing required keys: {', '.join(missing)}")

    source = entry.get("source")
    if source not in ALLOWED_SOURCES:
        errors.append(
            f"{name}: source must be one of {sorted(ALLOWED_SOURCES)}, got {source!r}"
        )

    for split_name in ("train_idx", "valid_idx", "test_idx"):
        split_value = entry.get(split_name)
        if split_value is None:
            errors.append(f"{name}: {split_name} is missing")
            continue
        split_len = safe_len(split_value)
        if split_len == 0:
            warnings.append(f"{name}: {split_name} is empty")

    dataset = entry.get("dataset")
    if dataset is None:
        errors.append(f"{name}: dataset is missing")
    else:
        if not hasattr(dataset, "__len__"):
            warnings.append(f"{name}: dataset does not expose __len__")
        if not hasattr(dataset, "__getitem__"):
            warnings.append(f"{name}: dataset does not expose __getitem__")

    return errors, warnings


def choose_names(registry: Mapping[str, Any], dataset_name: Optional[str]) -> List[str]:
    if dataset_name:
        if dataset_name not in registry:
            available = ", ".join(sorted(registry)) or "<empty>"
            raise KeyError(
                f"dataset {dataset_name!r} is not registered; available: {available}"
            )
        return [dataset_name]
    return sorted(registry)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import a Graphormer custom dataset module, inspect DATASET_REGISTRY, "
            "and optionally validate registered dataset dictionaries."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--module",
        required=True,
        help=(
            "Importable module name, package directory, or .py file that registers "
            "Graphormer datasets."
        ),
    )
    parser.add_argument(
        "--dataset-name",
        help=(
            "Registered dataset name to validate. If omitted in validation mode, "
            "every registry entry is checked."
        ),
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="List registered datasets and exit without contract checks.",
    )
    parser.add_argument(
        "--execute-registrations",
        action="store_true",
        help=(
            "Execute registered dataset factories and validate the returned dicts. "
            "This can download or process data if the factory does so."
        ),
    )
    parser.add_argument(
        "--use-installed-graphormer",
        action="store_true",
        help=(
            "Use the installed graphormer.data module instead of the safe registry "
            "shim. This requires a working Graphormer/fairseq environment."
        ),
    )
    return parser


def print_summary(imported: ModuleType, registry: Mapping[str, Any]) -> None:
    print(f"imported module: {getattr(imported, '__name__', '<unknown>')}")
    print(registry_summary(registry))


def run_validation(registry: Mapping[str, Any], dataset_name: Optional[str]) -> int:
    if not registry:
        print("error: no datasets were registered by the imported module", file=sys.stderr)
        return 1

    try:
        names = choose_names(registry, dataset_name)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    overall_ok = True
    for name in names:
        entry = registry[name]
        errors, warnings = validate_entry(name, entry)
        if errors:
            overall_ok = False
            print(f"[error] {name}")
            for message in errors:
                print(f"  - {message}")
        else:
            print(f"[ok] {name}")

        if isinstance(entry, dict):
            print(f"  source: {entry.get('source', '<missing>')}")
            print(f"  dataset: {type(entry.get('dataset')).__name__}")
            for split_name in ("train_idx", "valid_idx", "test_idx"):
                print(f"  {split_name}: {describe_value(entry.get(split_name))}")
        elif isinstance(entry, DeferredRegistration):
            print(f"  factory: {entry.function_path}")

        for warning in warnings:
            print(f"  [warn] {warning}")

    return 0 if overall_ok else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.use_installed_graphormer:
            imported = import_user_module(args.module)
            registry = load_installed_registry()
        else:
            with graphormer_data_shim(execute=args.execute_registrations) as registry:
                imported = import_user_module(args.module)
                registry = dict(registry)
    except Exception as exc:
        parser.exit(2, f"error: failed to import user module {args.module!r}: {exc}\n")

    if args.list_only:
        print_summary(imported, registry)
        return 0

    print_summary(imported, registry)

    if not args.execute_registrations and not args.use_installed_graphormer:
        print(
            "validation skipped: dataset factories were not executed by default. "
            "Rerun with --execute-registrations only when dataset construction is safe."
        )
        return 0

    return run_validation(registry, args.dataset_name)


if __name__ == "__main__":
    raise SystemExit(main())
