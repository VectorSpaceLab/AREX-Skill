#!/usr/bin/env python3
"""Safely inspect Igel Auto-ML imports and task selector behavior.

This helper does not train, load datasets, download data, or require the original
source checkout. It inspects the installed Python environment only.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

EXPECTED_TASKS = [
    "ImageClassification",
    "ImageRegression",
    "TextClassification",
    "TextRegression",
    "StructuredDataClassification",
    "StructuredDataRegression",
]


def _error_summary(exc: BaseException) -> str:
    return f"{exc.__class__.__name__}: {exc}"


def _import_module(name: str) -> Tuple[Optional[Any], Dict[str, Any]]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on caller env
        return None, {"ok": False, "error": _error_summary(exc)}

    result: Dict[str, Any] = {"ok": True}
    version = getattr(module, "__version__", None)
    if version is not None:
        result["version"] = str(version)
    return module, result


def _tensorflow_devices(tf_module: Any) -> Any:
    try:
        return [
            {
                "name": str(getattr(device, "name", "")),
                "type": str(getattr(device, "device_type", "")),
            }
            for device in tf_module.config.list_physical_devices()
        ]
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"error": _error_summary(exc)}


def _class_name(value: Any) -> str:
    module = getattr(value, "__module__", "")
    name = getattr(value, "__name__", repr(value))
    return f"{module}.{name}" if module else name


def build_report(task: Optional[str] = None) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "ok": False,
        "python": sys.version.split()[0],
        "modules": {},
        "expectedTasks": EXPECTED_TASKS,
        "notes": [
            "Inspection only: no training, dataset reads, or downloads were run.",
            "The current Igel docs mention 'igel auto-train', but this version's Click CLI may not expose that command.",
        ],
    }

    tf_module, tf_info = _import_module("tensorflow")
    if tf_module is not None:
        tf_info["devices"] = _tensorflow_devices(tf_module)
    report["modules"]["tensorflow"] = tf_info

    _, ak_info = _import_module("autokeras")
    report["modules"]["autokeras"] = ak_info

    auto_module, auto_info = _import_module("igel.auto")
    report["modules"]["igel.auto"] = auto_info
    if auto_module is None:
        return report

    try:
        igel_cnn = getattr(auto_module, "IgelCNN")
        report["IgelCNN"] = {"signature": str(inspect.signature(igel_cnn))}
    except Exception as exc:  # pragma: no cover - unexpected API variation
        report["IgelCNN"] = {"error": _error_summary(exc)}

    models_module, models_info = _import_module("igel.auto.models")
    report["modules"]["igel.auto.models"] = models_info
    if models_module is None:
        return report

    try:
        models = getattr(models_module, "Models")
        models_map = getattr(models, "models_map", {})
        report["supportedTasks"] = list(models_map.keys())
        report["modelClasses"] = {
            name: _class_name(entry.get("class"))
            for name, entry in models_map.items()
            if isinstance(entry, dict) and "class" in entry
        }
        if task:
            try:
                selected = models.get(task)
                report["taskCheck"] = {
                    "task": task,
                    "ok": True,
                    "class": _class_name(selected),
                }
            except Exception as exc:  # pragma: no cover - env/API dependent
                report["taskCheck"] = {
                    "task": task,
                    "ok": False,
                    "error": _error_summary(exc),
                }
    except Exception as exc:  # pragma: no cover - unexpected API variation
        report["modelsError"] = _error_summary(exc)

    report["ok"] = bool(
        report["modules"].get("tensorflow", {}).get("ok")
        and report["modules"].get("autokeras", {}).get("ok")
        and report["modules"].get("igel.auto", {}).get("ok")
        and report["modules"].get("igel.auto.models", {}).get("ok")
        and not ("taskCheck" in report and not report["taskCheck"].get("ok"))
    )
    return report


def print_text_report(report: Dict[str, Any]) -> None:
    print("Igel Auto-ML inspection")
    print(f"Python: {report.get('python')}")
    print("\nModules:")
    for name, info in report.get("modules", {}).items():
        if info.get("ok"):
            version = info.get("version")
            suffix = f" {version}" if version else ""
            print(f"  [ok]   {name}{suffix}")
            if name == "tensorflow" and "devices" in info:
                print(f"         devices: {info['devices']}")
        else:
            print(f"  [fail] {name}: {info.get('error')}")

    if "IgelCNN" in report:
        print("\nIgelCNN:")
        igel_cnn = report["IgelCNN"]
        if "signature" in igel_cnn:
            print(f"  signature: {igel_cnn['signature']}")
        else:
            print(f"  error: {igel_cnn.get('error')}")

    if report.get("supportedTasks"):
        print("\nSupported task names:")
        for task_name in report["supportedTasks"]:
            cls = report.get("modelClasses", {}).get(task_name, "unknown")
            print(f"  - {task_name}: {cls}")

    if "taskCheck" in report:
        task_check = report["taskCheck"]
        print("\nTask check:")
        if task_check.get("ok"):
            print(f"  [ok] {task_check['task']} -> {task_check['class']}")
        else:
            print(f"  [fail] {task_check['task']}: {task_check.get('error')}")

    if report.get("notes"):
        print("\nNotes:")
        for note in report["notes"]:
            print(f"  - {note}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed Igel Auto-ML imports, IgelCNN signature, and "
            "Models.get task selection without training or downloading data."
        )
    )
    parser.add_argument(
        "--task",
        help="Optional exact task string to resolve with igel.auto.models.Models.get.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the inspection report as JSON instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    report = build_report(task=args.task)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
