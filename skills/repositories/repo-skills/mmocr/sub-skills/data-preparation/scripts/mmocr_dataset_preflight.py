#!/usr/bin/env python3
"""Safe MMOCR dataset-zoo and annotation preflight.

This helper is intentionally small and read-only. It never imports MMOCR,
never downloads datasets, and never writes output files. It can inspect a
local dataset-zoo directory or fall back to a bundled official coverage
snapshot, and it can validate tiny annotation structures before expensive
preparation or training.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

TASKS = ("textdet", "textrecog", "textspotting", "kie")

OFFICIAL_TASKS: Mapping[str, Tuple[str, ...]] = {
    "cocotextv2": ("textdet", "textrecog", "textspotting"),
    "ctw1500": ("textdet", "textrecog", "textspotting"),
    "cute80": ("textrecog",),
    "funsd": ("textdet", "textrecog", "textspotting"),
    "icdar2013": ("textdet", "textrecog", "textspotting"),
    "icdar2015": ("textdet", "textrecog", "textspotting"),
    "iiit5k": ("textrecog",),
    "mjsynth": ("textrecog",),
    "naf": ("textdet", "textrecog", "textspotting"),
    "sroie": ("textdet", "textrecog", "textspotting"),
    "svt": ("textdet", "textrecog", "textspotting"),
    "svtp": ("textrecog",),
    "synthtext": ("textdet", "textrecog", "textspotting"),
    "textocr": ("textdet", "textrecog", "textspotting"),
    "totaltext": ("textdet", "textrecog", "textspotting"),
    "wildreceipt": ("textdet", "textrecog", "textspotting", "kie"),
}


def _try_yaml_tasks(path: Path) -> Optional[List[str]]:
    try:
        import yaml  # type: ignore
    except Exception:
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tasks = data.get("Data", {}).get("Tasks", [])
    except Exception:
        return None
    return [str(t) for t in tasks if str(t) in TASKS]


def _fallback_yaml_tasks(path: Path) -> List[str]:
    tasks: List[str] = []
    in_tasks = False
    task_indent: Optional[int] = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^\s*Tasks\s*:\s*$", line):
            in_tasks = True
            task_indent = None
            continue
        if not in_tasks:
            continue
        match = re.match(r"^(\s*)-\s*([A-Za-z0-9_\-]+)\s*$", line)
        if match:
            indent = len(match.group(1))
            if task_indent is None:
                task_indent = indent
            if indent == task_indent and match.group(2) in TASKS:
                tasks.append(match.group(2))
            continue
        if line.strip() and not line.startswith(" "):
            break
        if line.strip() and task_indent is not None:
            break
    return tasks


def read_meta_tasks(path: Path) -> List[str]:
    tasks = _try_yaml_tasks(path)
    if tasks is not None:
        return tasks
    return _fallback_yaml_tasks(path)


def scan_dataset_zoo(dataset_zoo_path: Optional[Path]) -> Tuple[str, Dict[str, dict], List[str]]:
    warnings: List[str] = []
    if dataset_zoo_path is None or not dataset_zoo_path.exists():
        data = {
            name: {
                "tasks": sorted(tasks),
                "config_tasks": sorted(tasks),
                "meta_tasks": sorted(tasks),
                "has_metafile": False,
                "source": "embedded",
            }
            for name, tasks in OFFICIAL_TASKS.items()
        }
        if dataset_zoo_path is not None:
            warnings.append(f"dataset-zoo path not found; using embedded official coverage: {dataset_zoo_path}")
        return "embedded", data, warnings

    if not dataset_zoo_path.is_dir():
        raise SystemExit(f"dataset-zoo path is not a directory: {dataset_zoo_path}")

    data: Dict[str, dict] = {}
    for entry in sorted(dataset_zoo_path.iterdir()):
        if not entry.is_dir():
            continue
        config_tasks = sorted(p.stem for p in entry.glob("*.py") if p.stem in TASKS)
        meta_path = entry / "metafile.yml"
        meta_tasks = read_meta_tasks(meta_path) if meta_path.exists() else []
        tasks = sorted(set(config_tasks) | set(meta_tasks))
        data[entry.name] = {
            "tasks": tasks,
            "config_tasks": config_tasks,
            "meta_tasks": sorted(meta_tasks),
            "has_metafile": meta_path.exists(),
            "source": str(dataset_zoo_path),
        }
        if meta_tasks and config_tasks and set(meta_tasks) != set(config_tasks):
            warnings.append(
                f"metadata/task-file mismatch for {entry.name}: meta={meta_tasks}, files={config_tasks}"
            )
    return "dataset_zoo", data, warnings


def print_table(data: Mapping[str, Mapping[str, object]]) -> None:
    print("Dataset\tTasks")
    for name in sorted(data):
        tasks = data[name].get("tasks", [])
        print(f"{name}\t{', '.join(tasks) if tasks else '-'}")


def check_dataset_task(data: Mapping[str, Mapping[str, object]], dataset: str, task: Optional[str]) -> List[str]:
    errors: List[str] = []
    if dataset not in data:
        return [f"unsupported dataset: {dataset}"]
    info = data[dataset]
    tasks = set(info.get("tasks", []))
    config_tasks = set(info.get("config_tasks", []))
    meta_tasks = set(info.get("meta_tasks", []))
    if task is None:
        print(f"{dataset}: supported tasks = {', '.join(sorted(tasks)) if tasks else '-'}")
        return []
    if task not in tasks:
        errors.append(f"dataset {dataset!r} does not advertise task {task!r}")
    if info.get("source") != "embedded" and task not in config_tasks:
        errors.append(f"missing dataset-zoo task config: {dataset}/{task}.py")
    if info.get("has_metafile") and meta_tasks and task not in meta_tasks:
        errors.append(f"metafile.yml Data.Tasks does not include {task!r}")
    if not errors:
        print(f"OK: {dataset}/{task} is present in {info.get('source')}")
    return errors


def _is_number_list(value: object, length: Optional[int] = None, min_len: int = 0, even: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    if length is not None and len(value) != length:
        return False
    if len(value) < min_len:
        return False
    if even and len(value) % 2:
        return False
    return all(isinstance(x, (int, float)) for x in value)


def _validate_ocr_instance(inst: object, task: str, where: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(inst, dict):
        return [f"{where}: instance is not an object"]
    if task in {"textdet", "textspotting"}:
        has_poly = _is_number_list(inst.get("polygon"), min_len=8, even=True)
        has_bbox = _is_number_list(inst.get("bbox"), length=4)
        if not (has_poly or has_bbox):
            errors.append(f"{where}: expected polygon or bbox")
        if "ignore" not in inst:
            errors.append(f"{where}: missing ignore flag")
        elif not isinstance(inst.get("ignore"), bool):
            errors.append(f"{where}: ignore should be boolean")
        if task == "textspotting" and not isinstance(inst.get("text"), str):
            errors.append(f"{where}: textspotting instance missing text string")
    elif task == "textrecog":
        if not isinstance(inst.get("text"), str):
            errors.append(f"{where}: recognition instance missing text string")
    return errors


def validate_json_annotation(path: Path, task: str, max_items: int) -> List[str]:
    errors: List[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"could not parse JSON: {exc}"]
    if not isinstance(payload, dict):
        return ["MMOCR JSON annotation should be an object with data_list"]
    if "data_list" not in payload or not isinstance(payload["data_list"], list):
        errors.append("missing list field: data_list")
        return errors
    if "metainfo" in payload and not isinstance(payload["metainfo"], dict):
        errors.append("metainfo should be an object when present")
    for i, item in enumerate(payload["data_list"][:max_items]):
        where = f"data_list[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: item is not an object")
            continue
        if not isinstance(item.get("img_path"), str):
            errors.append(f"{where}: missing img_path string")
        insts = item.get("instances")
        if not isinstance(insts, list) or not insts:
            errors.append(f"{where}: missing non-empty instances list")
            continue
        if task in {"textdet", "textspotting"}:
            if "height" not in item or "width" not in item:
                errors.append(f"{where}: detection/spotting items should include height and width")
        for j, inst in enumerate(insts[:max_items]):
            errors.extend(_validate_ocr_instance(inst, task, f"{where}.instances[{j}]"))
    if not errors:
        print(f"OK: {path} looks like tiny MMOCR {task} JSON")
    return errors


def _parse_nonempty_lines(path: Path, max_items: int) -> Iterable[Tuple[int, str]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        count = 0
        for number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            yield number, line
            count += 1
            if count >= max_items:
                break


def validate_line_annotation(path: Path, task: str, max_items: int) -> List[str]:
    errors: List[str] = []
    seen = 0
    for number, line in _parse_nonempty_lines(path, max_items):
        seen += 1
        prefix = f"line {number}"
        if task == "kie":
            try:
                obj = json.loads(line)
            except Exception as exc:
                errors.append(f"{prefix}: KIE line is not JSON: {exc}")
                continue
            for key in ("file_name", "height", "width", "annotations"):
                if key not in obj:
                    errors.append(f"{prefix}: missing {key}")
            anns = obj.get("annotations")
            if not isinstance(anns, list) or not anns:
                errors.append(f"{prefix}: annotations should be a non-empty list")
                continue
            for j, ann in enumerate(anns[:max_items]):
                if not isinstance(ann, dict):
                    errors.append(f"{prefix}.annotations[{j}]: not an object")
                    continue
                if not _is_number_list(ann.get("box"), length=8):
                    errors.append(f"{prefix}.annotations[{j}]: box should have 8 numbers")
                if not isinstance(ann.get("text"), str):
                    errors.append(f"{prefix}.annotations[{j}]: missing text string")
                if not isinstance(ann.get("label"), int):
                    errors.append(f"{prefix}.annotations[{j}]: missing integer label")
        elif task == "textrecog":
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                except Exception as exc:
                    errors.append(f"{prefix}: JSONL parse failed: {exc}")
                    continue
                if not isinstance(obj.get("filename"), str) and not isinstance(obj.get("img"), str):
                    errors.append(f"{prefix}: JSONL should contain filename or img")
                if not isinstance(obj.get("text"), str):
                    errors.append(f"{prefix}: JSONL should contain text string")
            else:
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    errors.append(f"{prefix}: recognition txt should be '<image> <text>'")
        else:
            errors.append(f"line validation is intended for textrecog or kie, not {task}")
            break
    if seen == 0:
        errors.append(f"{path}: no non-empty lines found")
    if not errors:
        print(f"OK: {path} looks like tiny {task} line annotation data")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-zoo-path", type=Path, default=None,
                        help="Dataset-zoo directory to inspect. Falls back to ./dataset_zoo if it exists, otherwise uses embedded coverage.")
    parser.add_argument("--list", action="store_true", help="List known datasets and tasks.")
    parser.add_argument("--dataset", action="append", default=[], help="Dataset name to check. May be repeated.")
    parser.add_argument("--task", choices=TASKS, default=None, help="Task config to check for each selected dataset.")
    parser.add_argument("--annotation-task", choices=TASKS, default=None,
                        help="Task for annotation validation. Defaults to --task, then textdet.")
    parser.add_argument("--validate-json", type=Path, default=None,
                        help="Validate a tiny MMOCR JSON annotation file.")
    parser.add_argument("--validate-lines", type=Path, default=None,
                        help="Validate a tiny textrecog line-label or KIE JSONL annotation file.")
    parser.add_argument("--max-items", type=int, default=5,
                        help="Maximum data_list items, lines, and instances to inspect.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_zoo_path = args.dataset_zoo_path
    if dataset_zoo_path is None:
        default = Path("dataset_zoo")
        dataset_zoo_path = default if default.exists() else None
    source, data, warnings = scan_dataset_zoo(dataset_zoo_path)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    errors: List[str] = []
    should_list = args.list or (not args.dataset and not args.validate_json and not args.validate_lines)
    if should_list:
        print(f"Source: {source}")
        print_table(data)

    for dataset in args.dataset:
        errors.extend(check_dataset_task(data, dataset, args.task))

    annotation_task = args.annotation_task or args.task or "textdet"
    if args.validate_json is not None:
        errors.extend(validate_json_annotation(args.validate_json, annotation_task, args.max_items))
    if args.validate_lines is not None:
        errors.extend(validate_line_annotation(args.validate_lines, annotation_task, args.max_items))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
