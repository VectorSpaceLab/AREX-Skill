#!/usr/bin/env python3
"""List importable nnU-Net extension classes without modifying files."""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import pkgutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable


KINDS = {
    "trainer": ("nnunetv2.training.nnUNetTrainer", "nnUNetTrainer"),
    "planner": ("nnunetv2.experiment_planning", "ExperimentPlanner"),
    "preprocessor": ("nnunetv2.preprocessing", "DefaultPreprocessor"),
    "normalization": ("nnunetv2.preprocessing.normalization", "ImageNormalization"),
    "imageio": ("nnunetv2.imageio", "BaseReaderWriter"),
    "label-manager": ("nnunetv2.utilities.label_handling", "LabelManager"),
}


@contextmanager
def prepend_syspath(path: str):
    resolved = str(Path(path).resolve())
    already_present = resolved in sys.path
    if not already_present:
        sys.path.insert(0, resolved)
    try:
        yield
    finally:
        if not already_present:
            try:
                sys.path.remove(resolved)
            except ValueError:
                pass


def iter_modules(package_name: str):
    package = importlib.import_module(package_name)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return
    prefix = package.__name__ + "."
    for module_info in pkgutil.walk_packages(package_path, prefix):
        yield module_info.name


def import_base_class(kind: str):
    if kind == "trainer":
        from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer

        return nnUNetTrainer
    if kind == "planner":
        from nnunetv2.experiment_planning.experiment_planners.default_experiment_planner import ExperimentPlanner

        return ExperimentPlanner
    if kind == "preprocessor":
        from nnunetv2.preprocessing.preprocessors.default_preprocessor import DefaultPreprocessor

        return DefaultPreprocessor
    if kind == "normalization":
        from nnunetv2.preprocessing.normalization.default_normalization_schemes import ImageNormalization

        return ImageNormalization
    if kind == "imageio":
        from nnunetv2.imageio.base_reader_writer import BaseReaderWriter

        return BaseReaderWriter
    if kind == "label-manager":
        from nnunetv2.utilities.label_handling.label_handling import LabelManager

        return LabelManager
    raise ValueError(f"Unsupported kind: {kind}")


def collect_classes_from_package(kind: str, package_name: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    base_class = import_base_class(kind)
    classes: list[tuple[str, str]] = []
    errors: list[tuple[str, str]] = []

    for module_name in iter_modules(package_name):
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - reporting importability is the purpose of this helper
            errors.append((module_name, f"{type(exc).__name__}: {exc}"))
            continue
        for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
            if class_obj is base_class:
                continue
            try:
                if issubclass(class_obj, base_class):
                    classes.append((class_name, class_obj.__module__))
            except TypeError:
                continue

    return sorted(set(classes)), errors


def module_name_from_file(root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(root).with_suffix("")
    return ".".join(relative.parts)


def collect_external_trainers(paths: Iterable[str]) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]]]:
    from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer

    classes: list[tuple[str, str, str]] = []
    errors: list[tuple[str, str]] = []
    for raw_path in paths:
        if not raw_path:
            continue
        root = Path(raw_path).expanduser().resolve()
        if not root.exists():
            errors.append((str(root), "path does not exist"))
            continue
        with prepend_syspath(str(root)):
            for file_path in sorted(root.rglob("*.py")):
                if file_path.name == "__init__.py":
                    continue
                module_name = module_name_from_file(root, file_path)
                try:
                    module = importlib.import_module(module_name)
                except Exception as exc:  # noqa: BLE001
                    errors.append((module_name, f"{type(exc).__name__}: {exc}"))
                    continue
                for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
                    if class_obj is nnUNetTrainer:
                        continue
                    try:
                        if issubclass(class_obj, nnUNetTrainer):
                            classes.append((class_name, class_obj.__module__, str(root)))
                    except TypeError:
                        continue
    return sorted(set(classes)), errors


def print_builtin_kind(kind: str) -> int:
    package_name, _ = KINDS[kind]
    print(f"\n[{kind}] {package_name}")
    try:
        classes, errors = collect_classes_from_package(kind, package_name)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not inspect {package_name}: {type(exc).__name__}: {exc}")
        return 1

    for class_name, module_name in classes:
        print(f"{class_name}\t{module_name}")
    if not classes:
        print("(no subclasses found)")
    if errors:
        print("Import errors:", file=sys.stderr)
        for module_name, message in errors:
            print(f"  {module_name}: {message}", file=sys.stderr)
    return 0 if not errors else 2


def split_external_paths(values: list[str]) -> list[str]:
    paths: list[str] = []
    for value in values:
        paths.extend(part for part in value.split(os.pathsep) if part)
    env_value = os.environ.get("nnUNet_extTrainer")
    if env_value:
        paths.extend(part for part in env_value.split(os.pathsep) if part)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        choices=["all", *KINDS.keys()],
        default="all",
        help="Extension class family to list.",
    )
    parser.add_argument(
        "--external-trainer-dir",
        action="append",
        default=[],
        help="External trainer root. May be passed multiple times or contain OS path separators. Also reads nnUNet_extTrainer.",
    )
    args = parser.parse_args()

    kinds = list(KINDS) if args.kind == "all" else [args.kind]
    exit_code = 0
    for kind in kinds:
        exit_code = max(exit_code, print_builtin_kind(kind))

    external_paths = split_external_paths(args.external_trainer_dir)
    if external_paths and args.kind in {"all", "trainer"}:
        print("\n[external-trainer]")
        classes, errors = collect_external_trainers(external_paths)
        for class_name, module_name, root in classes:
            print(f"{class_name}\t{module_name}\t{root}")
        if not classes:
            print("(no external trainer subclasses found)")
        if errors:
            print("External import errors:", file=sys.stderr)
            for module_name, message in errors:
                print(f"  {module_name}: {message}", file=sys.stderr)
            exit_code = max(exit_code, 2)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
