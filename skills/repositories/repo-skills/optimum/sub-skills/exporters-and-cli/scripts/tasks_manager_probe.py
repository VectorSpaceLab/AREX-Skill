#!/usr/bin/env python3
"""Safe TasksManager probe for Optimum exporter routing.

The probe inspects task mappings and demonstrates backend registration in the
current Python process only. It does not download models, load weights, export,
train, quantize, write package files, or require credentials.
"""

from __future__ import annotations

import argparse
import functools
import importlib
import importlib.util
import json
import sys
from typing import Any, Dict, Mapping, MutableMapping, Sequence


def _load_tasks_manager() -> tuple[Any | None, Dict[str, Any]]:
    try:
        from optimum.exporters.tasks import TasksManager

        return TasksManager, {"ok": True}
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "")
        recovery = None
        if missing == "requests":
            recovery = "Install requests in the active environment, then rerun this probe."
        return None, {"ok": False, "error_type": type(exc).__name__, "missing_module": missing, "recovery": recovery}
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return None, {"ok": False, "error_type": type(exc).__name__, "message": str(exc)}


def _maybe_import_backend_config_modules(backend: str) -> Dict[str, Any]:
    """Try lightweight backend config imports if present; never install or download."""
    candidates = [f"optimum.exporters.{backend}.model_configs"]
    if backend == "onnx":
        candidates.extend(["optimum.onnxruntime", "optimum.exporters.onnx"])
    elif backend in {"openvino", "ov"}:
        candidates.extend(["optimum.intel", "optimum.exporters.openvino.model_configs"])

    results = []
    for module_name in candidates:
        try:
            spec = importlib.util.find_spec(module_name)
        except ModuleNotFoundError:
            spec = None
        if spec is None:
            results.append({"module": module_name, "status": "not-found"})
            continue
        try:
            importlib.import_module(module_name)
            results.append({"module": module_name, "status": "imported"})
        except Exception as exc:
            results.append({"module": module_name, "status": "import-error", "error_type": type(exc).__name__, "message": str(exc)})
    return {"backend": backend, "candidates": results}


def _safe_callable_name(obj: Any) -> str:
    while isinstance(obj, functools.partial):
        obj = obj.func
    module = getattr(obj, "__module__", "")
    name = getattr(obj, "__name__", obj.__class__.__name__)
    return f"{module}.{name}" if module else name


def _collect_registered_backend_summary(TasksManager: Any) -> Dict[str, Any]:
    library_maps: Mapping[str, MutableMapping[str, Any]] = {
        "transformers": TasksManager._SUPPORTED_MODEL_TYPE,
        "diffusers": TasksManager._DIFFUSERS_SUPPORTED_MODEL_TYPE,
        "timm": TasksManager._TIMM_SUPPORTED_MODEL_TYPE,
        "sentence_transformers": TasksManager._SENTENCE_TRANSFORMERS_SUPPORTED_MODEL_TYPE,
    }
    summary: Dict[str, Any] = {}
    for library, model_map in library_maps.items():
        backend_counts: Dict[str, Dict[str, int]] = {}
        for _model_type, backends in model_map.items():
            for backend, tasks in backends.items():
                item = backend_counts.setdefault(backend, {"model_types": 0, "task_entries": 0})
                item["model_types"] += 1
                item["task_entries"] += len(tasks)
        summary[library] = {
            "model_type_count": len(model_map),
            "backends": dict(sorted(backend_counts.items())),
        }
    return summary


def _lookup_model_class(TasksManager: Any, task: str, model_type: str, library_name: str) -> Dict[str, Any]:
    try:
        model_cls = TasksManager.get_model_class_for_task(
            task=task,
            framework="pt",
            model_type=model_type,
            library=library_name,
        )
        return {"ok": True, "class": _safe_callable_name(model_cls)}
    except Exception as exc:
        return {"ok": False, "error_type": type(exc).__name__, "message": str(exc)}


def _lookup_exporter_constructor(TasksManager: Any, backend: str, model_type: str, task: str, library_name: str) -> Dict[str, Any]:
    try:
        constructor = TasksManager.get_exporter_config_constructor(
            exporter=backend,
            model_type=model_type,
            task=task,
            library_name=library_name,
        )
        return {"ok": True, "constructor": _safe_callable_name(constructor)}
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "diagnosis": "The backend config may be unregistered or supplied by an optional partner package.",
        }


def _run_registration_demo(TasksManager: Any, include_error_examples: bool) -> Dict[str, Any]:
    """Demonstrate create_register and overwrite behavior using process-local mappings."""
    backend = "disco-probe-backend"
    model_type = "bert"
    task = "text-classification"
    library_name = "transformers"
    supported_map = TasksManager._SUPPORTED_MODEL_TYPE
    model_type_existed = model_type in supported_map
    original_model_mapping = dict(supported_map.get(model_type, {}))

    class DemoConfig:
        SUPPORTS_PAST = False

        def __init__(self, config: Any, task: str, int_dtype: str = "int64", float_dtype: str = "fp32", **kwargs: Any):
            self.config = config
            self.task = task
            self.int_dtype = int_dtype
            self.float_dtype = float_dtype
            self.kwargs = kwargs

    class DemoConfigNoOverwrite(DemoConfig):
        pass

    class DemoConfigOverwrite(DemoConfig):
        pass

    result: Dict[str, Any] = {
        "backend": backend,
        "model_type": model_type,
        "task": task,
        "library_name": library_name,
        "mutates_process_only": True,
    }

    try:
        from transformers import BertConfig

        register = TasksManager.create_register(backend, overwrite_existing=False)

        @register(model_type, task, library_name=library_name)
        class RegisteredDemoConfig(DemoConfig):
            pass

        constructor = TasksManager.get_exporter_config_constructor(
            backend, model_type=model_type, task=task, library_name=library_name
        )
        instance = constructor(BertConfig())
        result["initial_registration"] = {"ok": True, "class": instance.__class__.__name__}

        @register(model_type, task, library_name=library_name)
        class RegisteredNoOverwriteConfig(DemoConfigNoOverwrite):
            pass

        constructor = TasksManager.get_exporter_config_constructor(
            backend, model_type=model_type, task=task, library_name=library_name
        )
        instance = constructor(BertConfig())
        result["second_registration_without_overwrite"] = {
            "ok": True,
            "class": instance.__class__.__name__,
            "kept_existing": instance.__class__.__name__ == "RegisteredDemoConfig",
        }

        register_overwrite = TasksManager.create_register(backend, overwrite_existing=True)

        @register_overwrite(model_type, task, library_name=library_name)
        class RegisteredOverwriteConfig(DemoConfigOverwrite):
            pass

        constructor = TasksManager.get_exporter_config_constructor(
            backend, model_type=model_type, task=task, library_name=library_name
        )
        instance = constructor(BertConfig())
        result["third_registration_with_overwrite"] = {
            "ok": True,
            "class": instance.__class__.__name__,
            "overwrote_existing": instance.__class__.__name__ == "RegisteredOverwriteConfig",
        }

        if include_error_examples:
            try:
                @register_overwrite(model_type, "not-a-real-task", library_name=library_name)
                class UnknownTaskConfig(DemoConfig):
                    pass
            except Exception as exc:
                result["unknown_task_error"] = {"error_type": type(exc).__name__, "message_excerpt": str(exc)[:500]}
    except Exception as exc:
        result["ok"] = False
        result["error_type"] = type(exc).__name__
        result["message"] = str(exc)
    finally:
        if model_type_existed:
            supported_map[model_type] = original_model_mapping
        else:
            supported_map.pop(model_type, None)

    result.setdefault("ok", True)
    return result


def _make_report(args: argparse.Namespace) -> Dict[str, Any]:
    TasksManager, import_report = _load_tasks_manager()
    report: Dict[str, Any] = {
        "script": "tasks_manager_probe.py",
        "safe_default": True,
        "inputs": {
            "backend": args.backend,
            "model_type": args.model_type,
            "task": args.task,
            "library_name": args.library_name,
        },
        "tasks_manager_import": import_report,
    }
    if TasksManager is None:
        return report

    report["backend_module_import_attempts"] = _maybe_import_backend_config_modules(args.backend)

    all_tasks = sorted(TasksManager.get_all_tasks())
    report["tasks"] = {
        "count": len(all_tasks),
        "sample": all_tasks[: min(len(all_tasks), args.sample_size)],
        "requested_task_canonical": TasksManager.map_from_synonym(args.task),
        "requested_task_synonyms": sorted(TasksManager.synonyms_for_task(args.task)),
    }
    report["selected_synonym_examples"] = {
        name: TasksManager.map_from_synonym(name)
        for name in ["default", "causal-lm", "sequence-classification", "summarization", "translation", "text-to-speech"]
    }
    report["registered_backend_summary"] = _collect_registered_backend_summary(TasksManager)
    report["model_class_lookup"] = _lookup_model_class(TasksManager, args.task, args.model_type, args.library_name)
    report["exporter_constructor_lookup"] = _lookup_exporter_constructor(
        TasksManager, args.backend, args.model_type, args.task, args.library_name
    )
    if args.demo_registration:
        report["registration_demo"] = _run_registration_demo(TasksManager, args.include_error_examples)
    return report


def _print_text(report: Dict[str, Any]) -> None:
    print("Optimum TasksManager probe")
    import_report = report["tasks_manager_import"]
    if not import_report.get("ok"):
        print(f"- import failed: {import_report}")
        return

    inputs = report["inputs"]
    print(
        "- requested mapping: backend={backend}, model_type={model_type}, task={task}, library={library_name}".format(
            **inputs
        )
    )
    tasks = report["tasks"]
    print(f"- known task count: {tasks['count']}; requested canonical task: {tasks['requested_task_canonical']}")
    print(f"- requested task synonyms: {tasks['requested_task_synonyms']}")
    model_lookup = report["model_class_lookup"]
    if model_lookup["ok"]:
        print(f"- model class lookup: ok -> {model_lookup['class']}")
    else:
        print(f"- model class lookup: failed -> {model_lookup['error_type']}: {model_lookup['message']}")
    constructor = report["exporter_constructor_lookup"]
    if constructor["ok"]:
        print(f"- exporter constructor lookup: ok -> {constructor['constructor']}")
    else:
        print(
            "- exporter constructor lookup: unavailable -> {error_type}: {message}".format(
                error_type=constructor["error_type"], message=constructor["message"]
            )
        )
        print(f"  diagnosis: {constructor['diagnosis']}")
    if "registration_demo" in report:
        demo = report["registration_demo"]
        print(f"- registration demo: {'ok' if demo.get('ok') else 'failed'}")
        if demo.get("ok"):
            print(f"  initial class: {demo['initial_registration']['class']}")
            print(
                "  no-overwrite kept existing: {kept}".format(
                    kept=demo["second_registration_without_overwrite"]["kept_existing"]
                )
            )
            print(
                "  overwrite replaced existing: {overwrote}".format(
                    overwrote=demo["third_registration_with_overwrite"]["overwrote_existing"]
                )
            )
            if "unknown_task_error" in demo:
                print(
                    "  unknown task example: {error_type}: {message_excerpt}".format(
                        **demo["unknown_task_error"]
                    )
                )
        else:
            print(f"  {demo.get('error_type')}: {demo.get('message')}")
    print("- backend summary:")
    for library, info in report["registered_backend_summary"].items():
        print(f"  {library}: {info['model_type_count']} model types, backends={list(info['backends'].keys())}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inspect Optimum TasksManager mappings and registration behavior.")
    parser.add_argument("--backend", default="onnx", help="Exporter backend to probe, e.g. onnx or openvino.")
    parser.add_argument("--model-type", default="bert", help="Model type to probe.")
    parser.add_argument("--task", default="text-classification", help="Task name or synonym to probe.")
    parser.add_argument(
        "--library-name",
        default="transformers",
        choices=["transformers", "diffusers", "timm", "sentence_transformers"],
        help="Library mapping to probe.",
    )
    parser.add_argument("--sample-size", type=int, default=12, help="Number of known tasks to show in JSON output.")
    parser.add_argument("--no-demo-registration", dest="demo_registration", action="store_false", help="Skip safe in-memory registration demo.")
    parser.add_argument("--include-error-examples", action="store_true", help="Also demonstrate unknown-task registration error handling.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.set_defaults(demo_registration=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = _make_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0 if report["tasks_manager_import"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
