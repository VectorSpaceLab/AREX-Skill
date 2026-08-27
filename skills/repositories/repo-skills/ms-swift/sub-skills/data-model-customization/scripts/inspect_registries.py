#!/usr/bin/env python3
"""Inspect installed ms-swift registry mappings without downloading models."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def ensure_swift_importable() -> None:
    """Allow execution from an ms-swift source checkout as well as installed packages."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "swift" / "__init__.py").exists():
            parent_text = str(parent)
            if parent_text not in sys.path:
                sys.path.insert(0, parent_text)
            return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect swift DATASET_MAPPING, MODEL_MAPPING, and TEMPLATE_MAPPING safely.")
    parser.add_argument("--datasets", action="store_true", help="Print dataset registry entries.")
    parser.add_argument("--models", action="store_true", help="Print model registry entries.")
    parser.add_argument("--templates", action="store_true", help="Print template registry entries.")
    parser.add_argument("--all", action="store_true", help="Print all registries.")
    parser.add_argument("--contains", default=None, help="Case-insensitive substring filter over names and summary fields.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum entries per registry. Use 0 for no limit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text tables.")
    parser.add_argument(
        "--external-plugin",
        action="append",
        default=[],
        metavar="PATH",
        help="Import an ms-swift external plugin before inspection. Can be repeated.",
    )
    return parser.parse_args()


def import_plugin(path_text: str) -> None:
    plugin_path = Path(path_text).expanduser().resolve()
    if not plugin_path.exists():
        raise FileNotFoundError(f"external plugin not found: {path_text}")
    module_name = f"_ms_swift_skill_plugin_{abs(hash(str(plugin_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import plugin: {plugin_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def safe_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return ", ".join(safe_string(item) for item in value if safe_string(item))
    if hasattr(value, "__name__"):
        return value.__name__
    return value.__class__.__name__


def public_dataclass_dict(value: Any) -> Dict[str, Any]:
    if is_dataclass(value):
        try:
            data = asdict(value)
        except Exception:
            data = dict(getattr(value, "__dict__", {}))
    else:
        data = dict(getattr(value, "__dict__", {}))
    return {key: public_json(value) for key, value in data.items() if not key.startswith("_")}


def public_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {safe_string(key): public_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [public_json(item) for item in value]
    if is_dataclass(value):
        return public_dataclass_dict(value)
    if hasattr(value, "__name__"):
        return value.__name__
    if hasattr(value, "__dict__"):
        return public_dataclass_dict(value)
    return safe_string(value)


def matches_filter(item: Dict[str, Any], contains: Optional[str]) -> bool:
    if not contains:
        return True
    needle = contains.lower()
    text = json.dumps(item, ensure_ascii=False, default=str).lower()
    return needle in text


def apply_limit(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit == 0:
        return items
    return items[:limit]


def dataset_key_to_text(key: Any) -> str:
    if isinstance(key, tuple):
        for item in key:
            if item:
                return str(item)
        return "<empty-dataset-key>"
    return str(key)


def collect_datasets(contains: Optional[str], limit: int) -> List[Dict[str, Any]]:
    from swift.dataset import DATASET_MAPPING

    rows: List[Dict[str, Any]] = []
    for key, meta in DATASET_MAPPING.items():
        subsets = []
        for subset in getattr(meta, "subsets", []) or []:
            subsets.append(getattr(subset, "name", safe_string(subset)))
        row = {
            "name": dataset_key_to_text(key),
            "key": public_json(key),
            "ms_dataset_id": getattr(meta, "ms_dataset_id", None),
            "hf_dataset_id": getattr(meta, "hf_dataset_id", None),
            "dataset_path": bool(getattr(meta, "dataset_path", None)),
            "dataset_name": getattr(meta, "dataset_name", None),
            "subsets": subsets,
            "split": getattr(meta, "split", None),
            "tags": getattr(meta, "tags", None),
            "preprocessor": safe_string(getattr(meta, "preprocess_func", None)),
            "loader": safe_string(getattr(meta, "loader", None)),
        }
        if matches_filter(row, contains):
            rows.append(row)
    rows.sort(key=lambda item: item["name"])
    return apply_limit(rows, limit)


def collect_models(contains: Optional[str], limit: int) -> List[Dict[str, Any]]:
    from swift.model import MODEL_MAPPING

    rows: List[Dict[str, Any]] = []
    for model_type, meta in MODEL_MAPPING.items():
        model_ids: List[str] = []
        group_templates: List[str] = []
        group_requires: List[str] = []
        for group in getattr(meta, "model_groups", []) or []:
            if getattr(group, "template", None):
                group_templates.append(group.template)
            for requirement in getattr(group, "requires", []) or []:
                group_requires.append(requirement)
            for model in getattr(group, "models", []) or []:
                for attr in ["ms_model_id", "hf_model_id", "model_path"]:
                    value = getattr(model, attr, None)
                    if value:
                        model_ids.append(value)
        row = {
            "model_type": model_type,
            "template": getattr(meta, "template", None),
            "candidate_templates": getattr(meta, "candidate_templates", None),
            "group_templates": sorted(set(group_templates)),
            "model_arch": safe_string(getattr(meta, "model_arch", None)),
            "mcore_model_type": getattr(meta, "mcore_model_type", None),
            "architectures": getattr(meta, "architectures", None),
            "is_multimodal": getattr(meta, "is_multimodal", None),
            "is_reward": getattr(meta, "is_reward", None),
            "task_type": getattr(meta, "task_type", None),
            "requires": sorted(set((getattr(meta, "requires", None) or []) + group_requires)),
            "tags": getattr(meta, "tags", None),
            "model_ids": model_ids[:8],
            "model_id_count": len(model_ids),
            "loader": safe_string(getattr(meta, "loader", None)),
        }
        if matches_filter(row, contains):
            rows.append(row)
    rows.sort(key=lambda item: item["model_type"])
    return apply_limit(rows, limit)


def collect_templates(contains: Optional[str], limit: int) -> List[Dict[str, Any]]:
    from swift.template import TEMPLATE_MAPPING

    rows: List[Dict[str, Any]] = []
    for template_type, meta in TEMPLATE_MAPPING.items():
        row = {
            "template_type": template_type,
            "template_cls": safe_string(getattr(meta, "template_cls", None)),
            "support_system": getattr(meta, "support_system", None),
            "support_multi_round": getattr(meta, "support_multi_round", None),
            "agent_template": getattr(meta, "agent_template", None),
            "default_system": bool(getattr(meta, "default_system", None)),
            "stop_words_count": len(getattr(meta, "stop_words", []) or []),
            "auto_add_bos": getattr(meta, "auto_add_bos", None),
            "is_thinking": getattr(meta, "is_thinking", None),
            "prefix_preview": preview_prompt(getattr(meta, "prefix", None)),
            "prompt_preview": preview_prompt(getattr(meta, "prompt", None)),
            "suffix_preview": preview_prompt(getattr(meta, "suffix", None)),
        }
        if matches_filter(row, contains):
            rows.append(row)
    rows.sort(key=lambda item: item["template_type"])
    return apply_limit(rows, limit)


def preview_prompt(prompt: Any, max_chars: int = 80) -> str:
    text = safe_string(prompt)
    text = text.replace("\n", "\\n")
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text


def print_table(title: str, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    print(f"\n## {title} ({len(rows)} shown)")
    if not rows:
        print("No entries matched.")
        return
    widths = {column: len(column) for column in columns}
    for row in rows:
        for column in columns:
            widths[column] = min(max(widths[column], len(safe_string(row.get(column)))), 60)
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)
    print(header)
    print(separator)
    for row in rows:
        values = []
        for column in columns:
            value = safe_string(row.get(column))
            if len(value) > widths[column]:
                value = value[: widths[column] - 3] + "..."
            values.append(value.ljust(widths[column]))
        print(" | ".join(values))


def main() -> int:
    args = parse_args()
    ensure_swift_importable()
    if not (args.datasets or args.models or args.templates or args.all):
        args.all = True

    for plugin_path in args.external_plugin:
        import_plugin(plugin_path)

    output: Dict[str, List[Dict[str, Any]]] = {}
    try:
        if args.all or args.datasets:
            output["datasets"] = collect_datasets(args.contains, args.limit)
        if args.all or args.models:
            output["models"] = collect_models(args.contains, args.limit)
        if args.all or args.templates:
            output["templates"] = collect_templates(args.contains, args.limit)
    except ModuleNotFoundError as exc:
        missing_name = exc.name or str(exc)
        print(
            "Unable to import installed ms-swift registry modules because "
            f"Python dependency {missing_name!r} is missing. Run this script in an "
            "environment where ms-swift imports successfully, for example after "
            "`pip install ms-swift -U`. Registry inspection does not download models "
            "once the package imports are available.",
            file=sys.stderr,
        )
        return 2

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    if "datasets" in output:
        print_table("Datasets", output["datasets"], ["name", "subsets", "tags", "preprocessor"])
    if "models" in output:
        print_table(
            "Models",
            output["models"],
            ["model_type", "template", "is_multimodal", "requires", "model_id_count", "model_ids"],
        )
    if "templates" in output:
        print_table(
            "Templates",
            output["templates"],
            ["template_type", "agent_template", "support_system", "support_multi_round", "template_cls"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
