#!/usr/bin/env python3
"""Read-only static checks for pgmpy extension placement and template use."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CategorySpec:
    label: str
    template: str
    package: str
    test_dir: str
    base_names: tuple[str, ...]
    required_methods: tuple[str, ...]
    tag_keys: tuple[str, ...]
    export_init: bool
    test_list_file: str | None = None
    placement_note: str = ""


CATEGORIES: dict[str, CategorySpec] = {
    "causal-discovery": CategorySpec(
        label="causal-discovery",
        template="devtools/extension_templates/_causal_discovery.py",
        package="pgmpy/causal_discovery",
        test_dir="pgmpy/tests/test_causal_discovery",
        base_names=("BaseCausalDiscovery",),
        required_methods=("_fit",),
        tag_keys=(),
        export_init=True,
        placement_note="new discovery algorithms live directly under pgmpy/causal_discovery",
    ),
    "ci-test": CategorySpec(
        label="ci-test",
        template="devtools/extension_templates/_ci_tests.py",
        package="pgmpy/ci_tests",
        test_dir="pgmpy/tests/test_ci_tests",
        base_names=("BaseCITest",),
        required_methods=("_compute_result",),
        tag_keys=("name", "data_types", "default_for", "requires_data", "is_symmetric"),
        export_init=True,
        placement_note="new CI tests live directly under pgmpy/ci_tests",
    ),
    "structure-score": CategorySpec(
        label="structure-score",
        template="devtools/extension_templates/_structure_score.py",
        package="pgmpy/structure_score",
        test_dir="pgmpy/tests/test_structure_score",
        base_names=("BaseStructureScore",),
        required_methods=("_local_score",),
        tag_keys=("name", "supported_datatype", "default_for"),
        export_init=True,
        placement_note="new score filenames should not start with an underscore",
    ),
    "metric": CategorySpec(
        label="metric",
        template="devtools/extension_templates/_metrics.py",
        package="pgmpy/metrics",
        test_dir="pgmpy/tests/test_metrics",
        base_names=("BaseSupervisedMetric", "BaseUnsupervisedMetric"),
        required_methods=("_evaluate",),
        tag_keys=("name", "requires_true_graph", "requires_data", "supported_graph_types"),
        export_init=True,
        placement_note="choose exactly one metric base class and remove unused scaffold code",
    ),
    "dataset": CategorySpec(
        label="dataset",
        template="devtools/extension_templates/_dataset.py",
        package="pgmpy/datasets",
        test_dir="pgmpy/tests/test_datasets",
        base_names=("BaseDataset", "BaseCovarianceDataset", "BaseTubingenDataset", "BaseSimulatedDataset"),
        required_methods=(),
        tag_keys=(
            "name",
            "n_variables",
            "n_samples",
            "has_ground_truth",
            "has_expert_knowledge",
            "has_missing_data",
            "is_simulated",
            "is_discrete",
            "is_continuous",
            "is_mixed",
        ),
        export_init=False,
        test_list_file="pgmpy/tests/test_datasets/test_datasets.py",
        placement_note="dataset classes are package-discovered; update dataset tests/list entries",
    ),
    "example-model": CategorySpec(
        label="example-model",
        template="devtools/extension_templates/_example_model.py",
        package="pgmpy/example_models",
        test_dir="pgmpy/tests/test_example_models",
        base_names=("BaseExampleModel",),
        required_methods=(),
        tag_keys=("name", "n_nodes", "n_edges", "is_parameterized"),
        export_init=False,
        test_list_file="pgmpy/tests/test_example_models/test_example_models.py",
        placement_note="example models live under pgmpy/example_models/<source>/ with a source __init__.py",
    ),
}

ALIASES = {
    "causal": "causal-discovery",
    "causal_discovery": "causal-discovery",
    "ci": "ci-test",
    "ci_tests": "ci-test",
    "ci-test": "ci-test",
    "score": "structure-score",
    "structure_score": "structure-score",
    "structure-score": "structure-score",
    "metrics": "metric",
    "model": "example-model",
    "example_model": "example-model",
    "example-model": "example-model",
    "datasets": "dataset",
}


@dataclass
class ClassSummary:
    name: str
    bases: set[str]
    methods: set[str]
    tag_keys: set[str]


def status(level: str, message: str, path: Path | None = None) -> dict[str, str]:
    item = {"level": level, "message": message}
    if path is not None:
        item["path"] = str(path)
    return item


def dotted_or_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_or_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Subscript):
        return dotted_or_name(node.value)
    if isinstance(node, ast.Call):
        return dotted_or_name(node.func)
    return ""


def literal_dict_keys(node: ast.AST) -> set[str]:
    if not isinstance(node, ast.Dict):
        return set()
    keys: set[str] = set()
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            keys.add(key.value)
    return keys


def summarize_classes(path: Path) -> tuple[list[ClassSummary], str | None]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [], f"syntax error: {exc}"
    except OSError as exc:
        return [], f"cannot read file: {exc}"

    summaries: list[ClassSummary] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {dotted_or_name(base).split(".")[-1] for base in node.bases}
        methods = {child.name for child in node.body if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)}
        tag_keys: set[str] = set()
        for child in node.body:
            if isinstance(child, ast.Assign):
                targets = [target.id for target in child.targets if isinstance(target, ast.Name)]
                if "_tags" in targets:
                    tag_keys |= literal_dict_keys(child.value)
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name) and child.target.id == "_tags":
                tag_keys |= literal_dict_keys(child.value)
        summaries.append(ClassSummary(node.name, bases, methods, tag_keys))
    return summaries, None


def resolve_repo(repo_arg: str | None) -> tuple[Path | None, list[dict[str, str]]]:
    messages: list[dict[str, str]] = []
    if repo_arg:
        root = Path(repo_arg).expanduser().resolve()
        if not root.exists():
            return None, [status("FAIL", "--repo path does not exist", root)]
        return root, messages

    spec = importlib.util.find_spec("pgmpy")
    if spec and spec.origin:
        root = Path(spec.origin).resolve().parents[1]
        messages.append(status("INFO", "resolved pgmpy root from installed import", root))
        return root, messages

    return None, [status("FAIL", "could not resolve pgmpy; pass --repo <pgmpy-checkout>")]


def normalize_category(category: str) -> list[str]:
    if category == "all":
        return list(CATEGORIES)
    canonical = ALIASES.get(category, category)
    if canonical not in CATEGORIES:
        valid = ", ".join(["all", *CATEGORIES])
        raise argparse.ArgumentTypeError(f"unknown category {category!r}; valid values: {valid}")
    return [canonical]


def expected_module_path(root: Path, spec: CategorySpec, module_name: str | None, model_source: str | None) -> Path | None:
    if not module_name:
        return None
    file_name = module_name if module_name.endswith(".py") else f"{module_name}.py"
    file_name = Path(file_name).name
    if spec.label == "example-model":
        source = model_source or "<source>"
        return root / spec.package / source / file_name
    return root / spec.package / file_name


def select_class(classes: list[ClassSummary], class_name: str | None, spec: CategorySpec) -> ClassSummary | None:
    if class_name:
        return next((cls for cls in classes if cls.name == class_name), None)
    for cls in classes:
        if cls.bases & set(spec.base_names):
            return cls
    return classes[0] if classes else None


def check_init_export(root: Path, spec: CategorySpec, class_name: str | None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if not spec.export_init or not class_name:
        return messages
    init_path = root / spec.package / "__init__.py"
    if not init_path.exists():
        return [status("FAIL", "package __init__.py not found for public export", init_path)]
    text = init_path.read_text(encoding="utf-8", errors="replace")
    if class_name in text:
        messages.append(status("OK", f"{class_name} appears in package __init__.py", init_path))
    else:
        messages.append(status("WARN", f"{class_name} is not mentioned in package __init__.py", init_path))
    return messages


def check_test_list(root: Path, spec: CategorySpec, registry_name: str | None) -> list[dict[str, str]]:
    if not spec.test_list_file or not registry_name:
        return []
    path = root / spec.test_list_file
    if not path.exists():
        return [status("WARN", "expected test-list file not found", path)]
    text = path.read_text(encoding="utf-8", errors="replace")
    if registry_name in text:
        return [status("OK", f"{registry_name} appears in the focused test-list file", path)]
    return [status("WARN", f"{registry_name} is not mentioned in the focused test-list file", path)]


def check_category(
    root: Path,
    category: str,
    module_name: str | None,
    class_name: str | None,
    registry_name: str | None,
    model_source: str | None,
) -> list[dict[str, str]]:
    spec = CATEGORIES[category]
    messages: list[dict[str, str]] = [status("INFO", f"checking category: {category}")]

    for label, rel_path in (("template", spec.template), ("package", spec.package), ("test directory", spec.test_dir)):
        path = root / rel_path
        if path.exists():
            messages.append(status("OK", f"{label} exists", path))
        else:
            level = "WARN" if label == "template" else "FAIL"
            messages.append(status(level, f"{label} is missing", path))

    if spec.placement_note:
        messages.append(status("INFO", spec.placement_note))

    candidate = expected_module_path(root, spec, module_name, model_source)
    if candidate is None:
        return messages

    if Path(candidate.name).stem.startswith("_"):
        messages.append(status("WARN", "public extension module filenames should not start with '_'", candidate))

    if candidate.exists():
        messages.append(status("OK", "candidate module exists at expected location", candidate))
        classes, error = summarize_classes(candidate)
        if error:
            messages.append(status("FAIL", error, candidate))
        else:
            chosen = select_class(classes, class_name, spec)
            if chosen is None:
                messages.append(status("WARN", "no class definitions found in candidate module", candidate))
            else:
                messages.append(status("INFO", f"selected class {chosen.name}; bases={sorted(chosen.bases)}"))
                if class_name and chosen.name != class_name:
                    messages.append(status("WARN", f"requested class {class_name} not found; inspected {chosen.name}", candidate))
                if spec.base_names and not (chosen.bases & set(spec.base_names)):
                    messages.append(
                        status(
                            "WARN",
                            f"selected class does not directly inherit one of {list(spec.base_names)}; verify inherited base contract",
                            candidate,
                        )
                    )
                missing_methods = sorted(set(spec.required_methods) - chosen.methods)
                if missing_methods:
                    messages.append(status("WARN", f"missing expected method(s): {missing_methods}", candidate))
                elif spec.required_methods:
                    messages.append(status("OK", "expected method hooks are present", candidate))
                missing_tags = sorted(set(spec.tag_keys) - chosen.tag_keys)
                if missing_tags:
                    messages.append(status("WARN", f"missing expected _tags keys: {missing_tags}", candidate))
                elif spec.tag_keys:
                    messages.append(status("OK", "expected _tags keys are present", candidate))
                if category == "structure-score":
                    if "is_parametric" in chosen.tag_keys and "is_parameteric" not in chosen.tag_keys:
                        messages.append(
                            status(
                                "WARN",
                                "candidate uses is_parametric; current concrete scores use is_parameteric, so verify current base/template sync",
                                candidate,
                            )
                        )
    else:
        messages.append(status("WARN", "candidate module does not exist at expected location", candidate))

    if spec.label == "example-model" and model_source:
        source_init = root / spec.package / model_source / "__init__.py"
        if source_init.exists():
            messages.append(status("OK", "example-model source package __init__.py exists", source_init))
        else:
            messages.append(status("WARN", "new example-model source package needs __init__.py", source_init))

    messages.extend(check_init_export(root, spec, class_name))
    messages.extend(check_test_list(root, spec, registry_name))
    return messages


def print_text_report(messages: list[dict[str, str]]) -> None:
    order = {"FAIL": 0, "WARN": 1, "OK": 2, "INFO": 3}
    for item in messages:
        level = item["level"]
        prefix = f"[{level}]"
        path = item.get("path")
        if path:
            print(f"{prefix} {item['message']}: {path}")
        else:
            print(f"{prefix} {item['message']}")
    totals: dict[str, int] = {}
    for item in messages:
        totals[item["level"]] = totals.get(item["level"], 0) + 1
    summary = " ".join(f"{key}={totals.get(key, 0)}" for key in sorted(totals, key=lambda key: order.get(key, 9)))
    print(f"SUMMARY {summary}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only static report for pgmpy extension template categories and candidate file placement.",
    )
    parser.add_argument(
        "--repo",
        help="Path to a pgmpy checkout. If omitted, the script tries to resolve the installed pgmpy package root.",
    )
    parser.add_argument(
        "--category",
        default="all",
        type=str,
        help="Extension category: all, causal-discovery, ci-test, structure-score, metric, dataset, or example-model.",
    )
    parser.add_argument("--module-name", help="Candidate module name or filename to check, such as my_score or my_score.py.")
    parser.add_argument("--class-name", help="Candidate public class name to check inside the module.")
    parser.add_argument("--registry-name", help="Lookup/listing name tag to look for in dataset/model test-list files.")
    parser.add_argument("--model-source", help="Example-model source namespace, such as bnlearn, bnrep, or dagitty.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when FAIL entries are present.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        categories = normalize_category(args.category)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    root, messages = resolve_repo(args.repo)
    if root is None:
        if args.json:
            print(json.dumps({"messages": messages}, indent=2, sort_keys=True))
        else:
            print_text_report(messages)
        return 2

    for category in categories:
        messages.extend(
            check_category(
                root=root,
                category=category,
                module_name=args.module_name if len(categories) == 1 else None,
                class_name=args.class_name if len(categories) == 1 else None,
                registry_name=args.registry_name if len(categories) == 1 else None,
                model_source=args.model_source,
            )
        )

    if args.json:
        print(json.dumps({"repo": str(root), "messages": messages}, indent=2, sort_keys=True))
    else:
        print_text_report(messages)

    has_fail = any(item["level"] == "FAIL" for item in messages)
    return 1 if args.strict and has_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
