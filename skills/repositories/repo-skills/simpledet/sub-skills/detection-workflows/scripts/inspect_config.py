#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any


MARKERS = ("README.md", "detection_train.py", "detection_test.py")


def infer_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if all((parent / marker).exists() for marker in MARKERS):
            return parent
    return here.parents[6]


def module_name_from_config(config: str) -> str:
    return config.replace(".py", "").replace("/", ".").strip(".")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a SimpleDet config safely")
    parser.add_argument("--config", required=True, help="Config path or module path")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--train", action="store_true", help="Load the config in train mode")
    mode.add_argument("--test", action="store_true", help="Load the config in test mode")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root")
    return parser.parse_args()


def short_runtime_object(value: Any) -> str:
    cls = value.__class__
    module = getattr(cls, "__module__", "")
    name = getattr(cls, "__name__", cls.__class__.__name__)
    if hasattr(value, "name") and isinstance(getattr(value, "name"), str):
        return f"{module}.{name}(name={getattr(value, 'name')})"
    return f"{module}.{name}"


def serialize(value: Any, depth: int = 2) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): serialize(v, depth - 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize(v, depth - 1) for v in value]
    if inspect.isclass(value):
        if depth <= 0:
            return value.__name__
        return summarize_namespace(value, depth - 1)
    if callable(value):
        return getattr(value, "__name__", value.__class__.__name__)
    return short_runtime_object(value)


def summarize_namespace(namespace: Any, depth: int = 2) -> dict[str, Any]:
    if depth < 0:
        return {"type": getattr(namespace, "__name__", namespace.__class__.__name__)}

    if inspect.isclass(namespace):
        items = vars(namespace).items()
        ns_name = namespace.__name__
    else:
        items = vars(namespace.__class__).items()
        ns_name = namespace.__class__.__name__

    summary: dict[str, Any] = {}
    for name, value in sorted(items):
        if name.startswith("_"):
            continue
        if inspect.isclass(value):
            summary[name] = summarize_namespace(value, depth - 1)
        elif callable(value):
            summary[name] = getattr(value, "__name__", value.__class__.__name__)
        else:
            summary[name] = serialize(value, depth - 1)
    if not summary:
        return {"type": ns_name}
    return summary


def module_bindings(module: Any) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for name, value in sorted(vars(module).items()):
        if name.startswith("_"):
            continue
        module_name = getattr(value, "__module__", "")
        if not module_name.startswith(("core.", "models.", "symbol.", "mxnext.")):
            continue
        if inspect.isclass(value) or inspect.isfunction(value) or callable(value):
            bindings[name] = f"{module_name}.{getattr(value, '__name__', value.__class__.__name__)}"
    return bindings


def describe_transforms(transform: Any) -> Any:
    if isinstance(transform, dict):
        return {str(k): describe_transforms(v) for k, v in transform.items()}
    if isinstance(transform, (list, tuple)):
        out = []
        for item in transform:
            if inspect.isclass(item):
                out.append(item.__name__)
            elif hasattr(item, "__class__"):
                out.append(item.__class__.__name__)
            else:
                out.append(str(item))
        return out
    if inspect.isclass(transform):
        return transform.__name__
    return short_runtime_object(transform)


def describe_metrics(metric_list: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for metric in metric_list or []:
        out.append(
            {
                "name": getattr(metric, "name", metric.__class__.__name__),
                "type": f"{metric.__class__.__module__}.{metric.__class__.__name__}",
            }
        )
    return out


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root or infer_repo_root()
    repo_root = repo_root.resolve()
    if not repo_root.exists():
        print(json.dumps({"status": "error", "error": f"repo root not found: {repo_root}"}, indent=2))
        return 2

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)

    module_name = module_name_from_config(args.config)
    mode = "train" if args.train else "test"
    report: dict[str, Any] = {
        "status": "ok",
        "repo_root": str(repo_root),
        "config_argument": args.config,
        "module_name": module_name,
        "mode": mode,
    }

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        missing = getattr(exc, "name", None)
        if missing in {"mxnet", "mxnext"}:
            report.update(
                {
                    "status": "missing_dependency",
                    "missing": missing,
                    "error": str(exc),
                }
            )
        else:
            report.update({"status": "import_failed", "error": f"{exc.__class__.__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    report["module_bindings"] = module_bindings(module)

    if not hasattr(module, "get_config"):
        report.update({"status": "error", "error": "config module has no get_config(is_train)"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    try:
        cfg = module.get_config(is_train=args.train)
    except Exception as exc:  # noqa: BLE001
        missing = getattr(exc, "name", None)
        if missing in {"mxnet", "mxnext", "mxboard", "pycocotools"}:
            report.update(
                {
                    "status": "missing_dependency",
                    "missing": missing,
                    "error": str(exc),
                }
            )
        else:
            report.update({"status": "config_failed", "error": f"{exc.__class__.__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    if not isinstance(cfg, tuple):
        report.update({"status": "error", "error": f"get_config returned {type(cfg).__name__}, expected tuple"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    names = [
        "General",
        "KvstoreParam",
        "RpnParam",
        "RoiParam",
        "BboxParam",
        "DatasetParam",
        "ModelParam",
        "OptimizeParam",
        "TestParam",
        "transform",
        "data_name",
        "label_name",
        "metric_list",
    ]

    report["tuple_length"] = len(cfg)
    report["namespaces"] = {}
    for idx, value in enumerate(cfg[: len(names)]):
        key = names[idx]
        if key == "transform":
            report["namespaces"][key] = describe_transforms(value)
        elif key == "metric_list":
            report["namespaces"][key] = describe_metrics(value)
        else:
            report["namespaces"][key] = summarize_namespace(value)

    # key facts for quick scanning
    quick: dict[str, Any] = {}
    try:
        general = cfg[0]
        kv = cfg[1]
        dataset = cfg[5]
        model = cfg[6]
        opt = cfg[7]
        test = cfg[8]
        quick.update(
            {
                "experiment_name": getattr(general, "name", None),
                "batch_image": getattr(general, "batch_image", None),
                "fp16": getattr(general, "fp16", None),
                "kvstore": getattr(kv, "kvstore", None),
                "gpus": list(getattr(kv, "gpus", []) or []),
                "image_set": list(getattr(dataset, "image_set", []) or []),
                "pretrain_prefix": getattr(getattr(model, "pretrain", object()), "prefix", None),
                "pretrain_epoch": getattr(getattr(model, "pretrain", object()), "epoch", None),
                "begin_epoch": getattr(getattr(opt, "schedule", object()), "begin_epoch", None),
                "end_epoch": getattr(getattr(opt, "schedule", object()), "end_epoch", None),
                "lr_iter": getattr(getattr(opt, "schedule", object()), "lr_iter", None),
                "test_prefix": getattr(getattr(test, "model", object()), "prefix", None),
                "test_epoch": getattr(getattr(test, "model", object()), "epoch", None),
                "nms_type": getattr(getattr(test, "nms", object()), "type", None),
                "nms_thr": getattr(getattr(test, "nms", object()), "thr", None),
            }
        )
    except Exception as exc:  # noqa: BLE001
        quick["error"] = f"{exc.__class__.__name__}: {exc}"
    report["quick_facts"] = quick

    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
