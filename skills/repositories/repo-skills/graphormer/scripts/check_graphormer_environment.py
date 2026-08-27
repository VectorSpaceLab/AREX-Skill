#!/usr/bin/env python3
"""Check whether a Graphormer fairseq environment is ready for inspection.

This helper only imports modules and reads registries. It does not train,
download data, or load checkpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as dist_version
from typing import Any, Dict, List, Mapping, Optional, Tuple

EXPECTED = {
    "models": ["graphormer", "graphormer3d"],
    "architectures": [
        "graphormer",
        "graphormer_base",
        "graphormer_slim",
        "graphormer_large",
        "graphormer3d_base",
    ],
    "tasks": ["graph_prediction", "graph_prediction_with_flag", "is2re"],
    "criterions": [
        "binary_logloss",
        "binary_logloss_with_flag",
        "l1_loss",
        "l1_loss_with_flag",
        "mae_deltapos",
        "multiclass_cross_entropy",
        "multiclass_cross_entropy_with_flag",
    ],
}


@dataclass
class ImportStatus:
    attempted: bool
    ok: bool
    error_type: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a Graphormer fairseq user-dir environment can import "
            "the expected registries and, optionally, a CUDA backend."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--user-dir",
        default="graphormer",
        help=(
            "Graphormer fairseq user-dir directory or importable package. The "
            "path should contain models/, tasks/, and criterions/."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit nonzero if the expected Graphormer registries are missing.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Exit nonzero unless torch reports CUDA is available and a tiny allocation succeeds.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Include tracebacks when import or registry inspection fails.",
    )
    return parser


def safe_version(name: str) -> Optional[str]:
    try:
        return dist_version(name)
    except PackageNotFoundError:
        return None


def expected_table(keys: List[str], expected: List[str]) -> Dict[str, List[str]]:
    present = [name for name in expected if name in keys]
    missing = [name for name in expected if name not in keys]
    return {"present": present, "missing": missing}


def object_name(obj: Any) -> str:
    module = getattr(obj, "__module__", None)
    qualname = getattr(obj, "__qualname__", None) or getattr(obj, "__name__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    if qualname:
        return str(qualname)
    return repr(obj)


def import_user_module(user_dir: str, show_traceback: bool) -> ImportStatus:
    try:
        from fairseq.utils import import_user_module as fairseq_import_user_module

        fairseq_import_user_module(argparse.Namespace(user_dir=user_dir))
        return ImportStatus(attempted=True, ok=True)
    except BaseException as exc:  # pragma: no cover - depends on caller env
        return ImportStatus(
            attempted=True,
            ok=False,
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc() if show_traceback else None,
        )


def registry_summary() -> Tuple[Optional[Dict[str, Any]], Optional[BaseException], Optional[str]]:
    try:
        from fairseq import criterions as fairseq_criterions
        from fairseq import models as fairseq_models
        from fairseq import tasks as fairseq_tasks
    except BaseException as exc:  # pragma: no cover - depends on caller env
        return None, exc, traceback.format_exc()

    model_registry = getattr(fairseq_models, "MODEL_REGISTRY", {})
    arch_registry = getattr(fairseq_models, "ARCH_MODEL_REGISTRY", {})
    arch_name_registry = getattr(fairseq_models, "ARCH_MODEL_NAME_REGISTRY", {})
    task_registry = getattr(fairseq_tasks, "TASK_REGISTRY", {})
    criterion_registry = getattr(fairseq_criterions, "CRITERION_REGISTRY", {})

    sections = {
        "models": sorted(str(key) for key in model_registry),
        "architectures": sorted(str(key) for key in arch_registry),
        "tasks": sorted(str(key) for key in task_registry),
        "criterions": sorted(str(key) for key in criterion_registry),
    }

    graphormer = {
        section: expected_table(sections[section], EXPECTED[section])
        for section in EXPECTED
    }
    details = {
        "models": {
            name: object_name(model_registry[name])
            for name in graphormer["models"]["present"]
        },
        "architectures": {
            name: str(arch_name_registry.get(name, object_name(arch_registry[name])))
            for name in graphormer["architectures"]["present"]
        },
        "tasks": {
            name: object_name(task_registry[name])
            for name in graphormer["tasks"]["present"]
        },
        "criterions": {
            name: object_name(criterion_registry[name])
            for name in graphormer["criterions"]["present"]
        },
    }

    return {
        "expected": EXPECTED,
        "graphormer": graphormer,
        "details": details,
        "all_registry_keys": sections,
    }, None, None


def check_cuda() -> Dict[str, Any]:
    import torch

    result: Dict[str, Any] = {
        "version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "is_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if torch.cuda.is_available():
        result["device_name"] = torch.cuda.get_device_name(0)
        result["capability"] = list(torch.cuda.get_device_capability(0))
        tiny = torch.empty((1,), device="cuda")
        result["tiny_allocation"] = tiny.numel()
    return result


def make_report(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    notes: List[str] = [
        "This helper only imports modules and reads registries; it does not train, download data, or load checkpoints."
    ]

    try:
        import torch
    except BaseException as exc:  # pragma: no cover - depends on caller env
        report = {
            "status": "error",
            "stage": "torch import",
            "error": f"could not import torch: {exc}",
            "traceback": traceback.format_exc() if args.show_traceback else None,
        }
        return report, 1

    try:
        import fairseq  # noqa: F401
        from fairseq import __version__ as fairseq_version  # type: ignore[attr-defined]
    except BaseException:
        fairseq_version = safe_version("fairseq")

    import_status = import_user_module(args.user_dir, args.show_traceback)
    registry, registry_error, registry_traceback = registry_summary()
    graphormer_import_path = None
    graphormer_import_error = None
    graphormer_traceback = None

    if import_status.ok:
        try:
            graphormer_module = import_module("graphormer")
            graphormer_import_path = getattr(graphormer_module, "__file__", None)
        except BaseException as exc:  # pragma: no cover - depends on caller env
            graphormer_import_error = f"{type(exc).__name__}: {exc}"
            graphormer_traceback = traceback.format_exc() if args.show_traceback else None

    cuda_report = None
    cuda_ok = True
    if args.require_cuda:
        try:
            cuda_report = check_cuda()
            cuda_ok = bool(cuda_report["is_available"])
            if not cuda_ok:
                notes.append("CUDA was requested but torch did not report any available CUDA device.")
        except BaseException as exc:  # pragma: no cover - depends on caller env
            cuda_report = {
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc() if args.show_traceback else None,
            }
            cuda_ok = False

    incomplete = False
    if registry is not None:
        incomplete = any(
            registry["graphormer"][section]["missing"] for section in EXPECTED
        )

    status = "ok"
    if not import_status.ok or registry_error is not None or graphormer_import_error is not None:
        status = "error"
    elif args.require_cuda and not cuda_ok:
        status = "error"
    elif args.require_complete and incomplete:
        status = "error"
    elif incomplete:
        status = "partial"

    if not import_status.ok:
        notes.append("The Graphormer user-dir import failed before registry inspection completed.")
    if registry_error is not None:
        notes.append("fairseq registry modules could not be imported.")
    if graphormer_import_error is not None:
        notes.append("graphormer imported only partially or failed after registry import.")

    report = {
        "status": status,
        "user_dir": args.user_dir,
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
        },
        "packages": {
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "fairseq": fairseq_version,
        },
        "import": asdict(import_status),
        "graphormer_import_path": graphormer_import_path,
        "graphormer_import_error": graphormer_import_error,
        "graphormer_import_traceback": graphormer_traceback,
        "registries": registry,
        "registry_error": f"{type(registry_error).__name__}: {registry_error}" if registry_error else None,
        "registry_traceback": registry_traceback,
        "cuda": cuda_report,
        "notes": notes,
    }

    exit_code = 0
    if status == "error":
        exit_code = 2
    elif status == "partial":
        exit_code = 0
    return report, exit_code


def print_text(report: Mapping[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"python: {report['python']['version']} ({report['python']['executable']})")
    print(
        f"packages: torch={report['packages']['torch']} cuda={report['packages']['torch_cuda']} fairseq={report['packages']['fairseq']}"
    )
    print(f"user_dir: {report.get('user_dir')}")

    import_info = report.get("import", {})
    print(f"user_dir_import: attempted={import_info.get('attempted')} ok={import_info.get('ok')}")
    if import_info.get("error"):
        print(f"user_dir_import_error: {import_info['error']}")
        if import_info.get("traceback"):
            print(import_info["traceback"])

    if report.get("graphormer_import_path"):
        print(f"graphormer_import_path: {report['graphormer_import_path']}")
    if report.get("graphormer_import_error"):
        print(f"graphormer_import_error: {report['graphormer_import_error']}")
        if report.get("graphormer_import_traceback"):
            print(report["graphormer_import_traceback"])

    registries = report.get("registries")
    if registries:
        for section in ("models", "architectures", "tasks", "criterions"):
            present = registries["graphormer"][section]["present"]
            missing = registries["graphormer"][section]["missing"]
            print(f"\n{section}:")
            print(f"  present: {', '.join(present) if present else '<none>'}")
            print(f"  missing: {', '.join(missing) if missing else '<none>'}")

    if report.get("cuda"):
        print("\ncuda:")
        for key, value in report["cuda"].items():
            print(f"  {key}: {value}")

    for note in report.get("notes") or []:
        print(f"note: {note}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report, exit_code = make_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
