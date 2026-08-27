#!/usr/bin/env python3
"""Safely summarize Graphormer-related fairseq registries.

The script imports a fairseq --user-dir when requested, then prints registry
contents. It does not start training, download datasets, load checkpoints, or
instantiate models.
"""

from __future__ import annotations

import argparse
import json
import traceback
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

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
            "Import a Graphormer fairseq user-dir and print Graphormer-related "
            "model, architecture, task, and criterion registry entries."
        )
    )
    parser.add_argument(
        "--user-dir",
        default=None,
        help=(
            "Path to the Graphormer fairseq user-dir package: the directory "
            "containing models/, tasks/, and criterions/. If omitted, the script "
            "prints currently loaded fairseq registries and reports missing "
            "Graphormer entries."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all fairseq registry keys in addition to Graphormer expected entries.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit nonzero if the import fails or any expected Graphormer registry name is missing.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Include a Python traceback for import or registry-inspection failures.",
    )
    return parser


def object_name(obj: Any) -> str:
    module = getattr(obj, "__module__", None)
    qualname = getattr(obj, "__qualname__", None) or getattr(obj, "__name__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    if qualname:
        return str(qualname)
    return repr(obj)


def sorted_keys(mapping: Optional[Mapping[str, Any]]) -> List[str]:
    if not mapping:
        return []
    return sorted(str(key) for key in mapping.keys())


def expected_table(keys: Iterable[str], expected: Iterable[str]) -> Dict[str, List[str]]:
    key_set = set(keys)
    present = [name for name in expected if name in key_set]
    missing = [name for name in expected if name not in key_set]
    return {"present": present, "missing": missing}


def load_fairseq() -> Tuple[
    Optional[Any],
    Optional[Any],
    Optional[Any],
    Optional[Any],
    Optional[BaseException],
    Optional[str],
]:
    try:
        from fairseq.utils import import_user_module
        from fairseq import models as fairseq_models
        from fairseq import tasks as fairseq_tasks
        from fairseq import criterions as fairseq_criterions
        return import_user_module, fairseq_models, fairseq_tasks, fairseq_criterions, None, None
    except BaseException as exc:  # pragma: no cover - depends on caller env
        return None, None, None, None, exc, traceback.format_exc()


def maybe_import_user_dir(import_user_module: Any, user_dir: Optional[str], show_traceback: bool) -> ImportStatus:
    if not user_dir:
        return ImportStatus(attempted=False, ok=False, error="--user-dir was omitted; no Graphormer plugin import was attempted")
    try:
        namespace = argparse.Namespace(user_dir=user_dir)
        import_user_module(namespace)
        return ImportStatus(attempted=True, ok=True)
    except BaseException as exc:  # pragma: no cover - depends on caller env
        return ImportStatus(
            attempted=True,
            ok=False,
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc() if show_traceback else None,
        )


def registry_summary(
    fairseq_models: Any,
    fairseq_tasks: Any,
    fairseq_criterions: Any,
    include_all: bool,
) -> Dict[str, Any]:
    model_registry = getattr(fairseq_models, "MODEL_REGISTRY", {})
    arch_registry = getattr(fairseq_models, "ARCH_MODEL_REGISTRY", {})
    arch_model_name_registry = getattr(fairseq_models, "ARCH_MODEL_NAME_REGISTRY", {})
    task_registry = getattr(fairseq_tasks, "TASK_REGISTRY", {})
    criterion_registry = getattr(fairseq_criterions, "CRITERION_REGISTRY", {})

    keys = {
        "models": sorted_keys(model_registry),
        "architectures": sorted_keys(arch_registry),
        "tasks": sorted_keys(task_registry),
        "criterions": sorted_keys(criterion_registry),
    }

    graphormer = {
        section: expected_table(keys[section], EXPECTED[section])
        for section in EXPECTED
    }

    details: Dict[str, Dict[str, str]] = {
        "models": {
            name: object_name(model_registry[name])
            for name in graphormer["models"]["present"]
        },
        "architectures": {
            name: str(arch_model_name_registry.get(name, object_name(arch_registry[name])))
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

    summary: Dict[str, Any] = {
        "expected": EXPECTED,
        "graphormer": graphormer,
        "details": details,
    }
    if include_all:
        summary["all_registry_keys"] = keys
    return summary


def missing_any(summary: Mapping[str, Any]) -> bool:
    graphormer = summary.get("graphormer", {})
    for section in EXPECTED:
        if graphormer.get(section, {}).get("missing"):
            return True
    return False


def make_report(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    notes: List[str] = [
        "This script only imports modules and reads registries; it does not train, download data, or load checkpoints."
    ]
    (
        import_user_module,
        fairseq_models,
        fairseq_tasks,
        fairseq_criterions,
        fairseq_error,
        fairseq_traceback,
    ) = load_fairseq()

    if fairseq_error is not None:
        status = ImportStatus(
            attempted=False,
            ok=False,
            error_type=type(fairseq_error).__name__,
            error=f"Could not import fairseq registry modules: {fairseq_error}",
            traceback=fairseq_traceback if args.show_traceback else None,
        )
        report: Dict[str, Any] = {
            "status": "error",
            "user_dir": args.user_dir,
            "import": asdict(status),
            "registries": None,
            "notes": notes,
        }
        return report, 1 if args.require_complete else 0

    import_status = maybe_import_user_dir(import_user_module, args.user_dir, args.show_traceback)
    registries = registry_summary(fairseq_models, fairseq_tasks, fairseq_criterions, args.include_all)

    if not args.user_dir:
        notes.append("Pass --user-dir to import Graphormer before checking expected registry names.")
    if import_status.attempted and not import_status.ok:
        notes.append("The user-dir import failed; registry results may be partial.")

    incomplete = missing_any(registries)
    status_text = "ok" if import_status.ok and not incomplete else "partial"
    if import_status.attempted and not import_status.ok:
        status_text = "error"

    report = {
        "status": status_text,
        "user_dir": args.user_dir,
        "import": asdict(import_status),
        "registries": registries,
        "notes": notes,
    }
    exit_code = 0
    if args.require_complete and (not import_status.ok or incomplete):
        exit_code = 2
    return report, exit_code


def print_text(report: Mapping[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"user_dir: {report.get('user_dir') or '<not provided>'}")
    import_info = report.get("import", {})
    print(
        "import: "
        f"attempted={import_info.get('attempted')} ok={import_info.get('ok')}"
    )
    if import_info.get("error"):
        if import_info.get("error_type"):
            print(f"import_error_type: {import_info['error_type']}")
        print(f"import_error: {import_info['error']}")
    if import_info.get("traceback"):
        print("traceback:")
        print(import_info["traceback"])

    registries = report.get("registries")
    if registries is not None:
        graphormer = registries["graphormer"]
        details = registries["details"]
        for section in ("models", "architectures", "tasks", "criterions"):
            present = graphormer[section]["present"]
            missing = graphormer[section]["missing"]
            print(f"\n{section}:")
            print(f"  present: {', '.join(present) if present else '<none>'}")
            print(f"  missing: {', '.join(missing) if missing else '<none>'}")
            if details.get(section):
                print("  details:")
                for name, target in sorted(details[section].items()):
                    print(f"    {name}: {target}")
        if "all_registry_keys" in registries:
            print("\nall_registry_keys:")
            for section, keys in registries["all_registry_keys"].items():
                print(f"  {section}: {', '.join(keys) if keys else '<none>'}")

    notes = report.get("notes") or []
    if notes:
        print("\nnotes:")
        for note in notes:
            print(f"  - {note}")


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
