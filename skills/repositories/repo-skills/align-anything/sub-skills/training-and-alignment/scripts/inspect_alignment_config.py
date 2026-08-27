#!/usr/bin/env python3
"""Inspect Align-Anything training config/tasks without running training.

The script is intentionally read-only. It locates an installed align_anything
package or a checkout supplied through --package-root / AA_REPO_ROOT, summarizes
YAML config sections, infers the trainer module, lists dataset templates by
static parsing, and optionally imports a trainer module to expose dependency
problems early.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - dependency diagnostic path
    print(f"ERROR: PyYAML is required to inspect Align-Anything configs: {exc}", file=sys.stderr)
    sys.exit(2)


DIFFUSION_MODALITIES = {"text_to_image", "text_to_audio", "text_to_video"}


def resolve_package_root(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    if os.environ.get("AA_REPO_ROOT"):
        candidates.append(Path(os.environ["AA_REPO_ROOT"]).expanduser())
    spec = importlib.util.find_spec("align_anything")
    if spec and spec.submodule_search_locations:
        candidates.append(Path(next(iter(spec.submodule_search_locations))))
    candidates.append(Path.cwd())

    for candidate in candidates:
        path = candidate.resolve()
        if path.name == "align_anything" and (path / "configs" / "train").is_dir():
            return path
        nested = path / "align_anything"
        if (nested / "configs" / "train").is_dir():
            return nested.resolve()
    raise SystemExit(
        "ERROR: Could not locate align_anything package. Install it, run from a checkout, "
        "set AA_REPO_ROOT, or pass --package-root."
    )


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: expected mapping in {path.name}, got {type(data).__name__}")
    return data


def available_tasks(package_root: Path) -> list[str]:
    train_root = package_root / "configs" / "train"
    tasks = []
    for path in sorted(train_root.rglob("*.yaml")):
        tasks.append(path.relative_to(train_root).with_suffix("").as_posix())
    return tasks


def config_path_for_task(package_root: Path, task: str) -> Path:
    path = package_root / "configs" / "train" / f"{task}.yaml"
    if not path.is_file():
        known = ", ".join(available_tasks(package_root)[:20])
        raise SystemExit(f"ERROR: config task {task!r} not found. Known examples: {known}")
    return path


def task_to_module(task: str) -> str:
    parts = task.split("/")
    if len(parts) != 2:
        raise SystemExit(f"ERROR: expected task as modality/algorithm, got {task!r}")
    modality, algorithm = parts
    module_algorithm = algorithm
    if modality in DIFFUSION_MODALITIES and algorithm in {"sft", "dpo"}:
        module_algorithm = f"{algorithm}_diffusion"
    return f"align_anything.trainers.{modality}.{module_algorithm}"


def module_to_task(module: str) -> str | None:
    prefix = "align_anything.trainers."
    if not module.startswith(prefix):
        return None
    rest = module[len(prefix) :].split(".")
    if len(rest) < 2:
        return None
    modality, algorithm = rest[0], rest[1]
    if modality in DIFFUSION_MODALITIES and algorithm in {"sft_diffusion", "dpo_diffusion"}:
        algorithm = algorithm.replace("_diffusion", "")
    return f"{modality}/{algorithm}"


def parse_source_like_value(value: str) -> Any:
    if value == "True":
        return True
    if value == "False":
        return False
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        pass
    if value.startswith("[") and value.endswith("]"):
        return [item for item in value[1:-1].split(",") if item]
    if "," in value:
        return [item for item in value.split(",") if item]
    return value


def find_leaf_paths(data: Any, leaf: str, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    matches: list[tuple[str, ...]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            current = (*prefix, str(key))
            if key == leaf:
                matches.append(current)
            matches.extend(find_leaf_paths(value, leaf, current))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            matches.extend(find_leaf_paths(value, leaf, (*prefix, str(index))))
    return matches


def summarize_config(data: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"sections": {}}
    interesting = {
        "train_cfgs": [
            "ds_cfgs",
            "epochs",
            "seed",
            "per_device_train_batch_size",
            "per_device_prompt_batch_size",
            "per_device_eval_batch_size",
            "gradient_accumulation_steps",
            "learning_rate",
            "actor_lr",
            "critic_lr",
            "bf16",
            "fp16",
            "eval_strategy",
            "save_total_limit",
            "save_interval",
            "beta",
            "beta_coeff",
            "kl_coeff",
            "num_generations",
            "resolution",
        ],
        "data_cfgs": [
            "train_datasets",
            "train_template",
            "train_split",
            "train_name",
            "train_data_files",
            "eval_datasets",
            "eval_template",
            "ptx_datasets",
            "ptx_template",
            "load_multi_datasets",
            "data_dir",
            "dataset_task_type",
        ],
        "model_cfgs": [
            "model_name_or_path",
            "processor_name_or_path",
            "actor_model_name_or_path",
            "reward_model_name_or_path",
            "reward_critic_model_name_or_path",
            "cost_model_name_or_path",
            "cost_critic_model_name_or_path",
            "remote_rm_url",
            "trust_remote_code",
            "model_max_length",
            "max_new_tokens",
        ],
        "logger_cfgs": ["log_type", "output_dir", "cache_dir", "save_total_limit", "save_interval"],
        "sensor_cfgs": ["input_sensors"],
        "lora_cfgs": ["use_lora", "target_modules", "save_full_model"],
        "bnb_cfgs": ["use_bnb", "load_in_4bit", "load_in_8bit"],
        "vllm_cfgs": ["use_vllm", "vllm_num_engines", "vllm_tensor_parallel_size", "vllm_max_model_len"],
    }
    for section, values in data.items():
        if isinstance(values, dict):
            keys = list(values.keys())
            selected = {key: values.get(key) for key in interesting.get(section, []) if key in values}
            summary["sections"][section] = {"keys": keys, "selected": selected}
        else:
            summary["sections"][section] = {"value": values}
    return summary


def deepspeed_config_status(package_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    train_cfgs = data.get("train_cfgs") or {}
    configured = train_cfgs.get("ds_cfgs") if isinstance(train_cfgs, dict) else None
    effective = os.environ.get("ZERO_STAGE_FILE") or configured
    result = {"configured": configured, "effective": effective, "exists": None}
    if effective:
        path = package_root / "configs" / "deepspeed" / str(effective)
        result["exists"] = path.is_file()
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                result["zero_stage"] = raw.get("zero_optimization", {}).get("stage")
            except Exception as exc:
                result["parse_error"] = str(exc)
    return result


def list_templates(package_root: Path) -> list[str]:
    path = package_root / "configs" / "format_dataset.py"
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func_name = ""
                if isinstance(decorator.func, ast.Name):
                    func_name = decorator.func.id
                elif isinstance(decorator.func, ast.Attribute):
                    func_name = decorator.func.attr
                if func_name == "register_template" and decorator.args:
                    arg = decorator.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        names.append(arg.value)
    return sorted(dict.fromkeys(names))


def check_overrides(data: dict[str, Any], overrides: list[str]) -> list[dict[str, Any]]:
    reports = []
    for item in overrides:
        if "=" not in item:
            reports.append({"override": item, "error": "expected key=value"})
            continue
        key, value = item.split("=", 1)
        leaf_key = key.replace("-", "_").split(":")[-1]
        paths = find_leaf_paths(data, leaf_key)
        reports.append(
            {
                "override": item,
                "leaf_key": leaf_key,
                "parsed_value": parse_source_like_value(value),
                "matching_paths": [".".join(path) for path in paths],
                "warning": "no matching leaf key" if not paths else ("multiple matching leaves" if len(paths) > 1 else None),
            }
        )
    return reports


def import_trainer(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # dependency diagnostics are the point of this mode
        return {"module": module, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    public = [name for name in dir(imported) if name.endswith("Trainer") or name == "main"]
    return {"module": module, "ok": True, "public_markers": public[:20]}


def print_text_report(report: dict[str, Any]) -> None:
    if "tasks" in report:
        for task in report["tasks"]:
            print(f"{task['task']} -> {task['trainer_module']}")
        return

    print(f"Task: {report['task']}")
    print(f"Trainer module: {report['trainer_module']}")
    ds = report.get("deepspeed", {})
    if ds:
        print(
            "DeepSpeed config: "
            f"configured={ds.get('configured')!r}, effective={ds.get('effective')!r}, "
            f"exists={ds.get('exists')}, zero_stage={ds.get('zero_stage', 'unknown')}"
        )
    sections = report.get("summary", {}).get("sections", {})
    for section, info in sections.items():
        if "keys" in info:
            print(f"\n[{section}] keys: {', '.join(info['keys'])}")
            selected = info.get("selected") or {}
            if selected:
                for key, value in selected.items():
                    print(f"  {key}: {value!r}")
        else:
            print(f"\n[{section}] {info.get('value')!r}")
    if report.get("templates") is not None:
        print("\nTemplates:")
        print(", ".join(report["templates"]))
    if report.get("override_checks"):
        print("\nOverride checks:")
        for item in report["override_checks"]:
            print(f"  {item['override']} -> {item.get('matching_paths', [])}")
            if item.get("warning"):
                print(f"    warning: {item['warning']}")
            if item.get("error"):
                print(f"    error: {item['error']}")
    if report.get("import_check"):
        print("\nImport check:")
        print(json.dumps(report["import_check"], indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", help="Checkout root or align_anything package directory.")
    parser.add_argument("--task", help="Training config task such as text_to_text/sft.")
    parser.add_argument("--trainer-module", help="Trainer module to inspect/import.")
    parser.add_argument("--list", action="store_true", help="List available config tasks and inferred modules.")
    parser.add_argument("--show", action="store_true", help="Show selected config keys.")
    parser.add_argument("--templates", action="store_true", help="List registered dataset template names by static parsing.")
    parser.add_argument("--check-overrides", nargs="*", default=[], metavar="KEY=VALUE", help="Check whether CLI override leaves exist in the selected config.")
    parser.add_argument("--import-trainer", action="store_true", help="Import the inferred/specified trainer module and report dependency errors.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    package_root = resolve_package_root(args.package_root)
    package_parent = str(package_root.parent)
    if package_parent not in sys.path:
        sys.path.insert(0, package_parent)

    if args.list:
        report = {
            "tasks": [
                {"task": task, "trainer_module": task_to_module(task)}
                for task in available_tasks(package_root)
            ]
        }
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text_report(report)
        return 0

    task = args.task
    if not task and args.trainer_module:
        task = module_to_task(args.trainer_module)
    if not task:
        parser.error("--task is required unless --list is used or --trainer-module can be mapped")
    config_path = config_path_for_task(package_root, task)
    data = load_yaml(config_path)
    trainer_module = args.trainer_module or task_to_module(task)

    report: dict[str, Any] = {
        "task": task,
        "trainer_module": trainer_module,
        "summary": summarize_config(data) if args.show or not args.json else summarize_config(data),
        "deepspeed": deepspeed_config_status(package_root, data),
    }
    if args.templates:
        report["templates"] = list_templates(package_root)
    if args.check_overrides:
        report["override_checks"] = check_overrides(data, args.check_overrides)
    if args.import_trainer:
        report["import_check"] = import_trainer(trainer_module)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
