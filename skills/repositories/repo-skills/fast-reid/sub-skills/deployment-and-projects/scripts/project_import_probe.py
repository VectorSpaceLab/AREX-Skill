#!/usr/bin/env python3
"""Probe FastReID extension-project imports and registry side effects safely."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PROJECTS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict(
    [
        (
            "FastAttr",
            {
                "relative_path": "projects/FastAttr",
                "package": "fastattr",
                "config_hook": "add_attr_config",
                "note": "Pedestrian attribute project; registers attribute datasets/meta-arch/head/evaluator; some attribute dataset modules require mat4py.",
            },
        ),
        (
            "FastClas",
            {
                "relative_path": "projects/FastClas",
                "package": "fastclas",
                "config_hook": None,
                "note": "Image classification project; package-wide import may expose missing-module issues in this checkout.",
            },
        ),
        (
            "FastDistill",
            {
                "relative_path": "projects/FastDistill",
                "package": "fastdistill",
                "config_hook": None,
                "note": "Distillation project; registers distillation meta-architecture/backbone pieces.",
            },
        ),
        (
            "FastFace",
            {
                "relative_path": "projects/FastFace",
                "package": "fastface",
                "config_hook": "add_face_cfg",
                "note": "Face recognition project; may require bcolz and optionally mxnet for project datasets.",
            },
        ),
        (
            "FastRetri",
            {
                "relative_path": "projects/FastRetri",
                "package": "fastretri",
                "config_hook": "add_retri_config",
                "note": "Fine-grained image retrieval project; registers retrieval datasets/evaluator.",
            },
        ),
        (
            "FastTune",
            {
                "relative_path": "projects/FastTune",
                "package": "autotuner",
                "config_hook": None,
                "note": "Ray Tune project; imports require tuning dependencies but the probe does not launch tuning.",
            },
        ),
        (
            "PartialReID",
            {
                "relative_path": "projects/PartialReID",
                "package": "partialreid",
                "config_hook": "add_partialreid_config",
                "note": "Partial/occluded ReID project; registers partial datasets/meta-arch/head/evaluator.",
            },
        ),
        (
            "NAIC20",
            {
                "relative_path": "projects/NAIC20",
                "package": "naic",
                "config_hook": "add_naic_config",
                "note": "Competition project; registers NAIC datasets/evaluator and submission behavior.",
            },
        ),
        (
            "FastRT",
            {
                "relative_path": "projects/FastRT",
                "package": None,
                "config_hook": None,
                "note": "C++ TensorRT project; no regular Python package is expected.",
            },
        ),
        (
            "CrossDomainReID",
            {
                "relative_path": "projects/CrossDomainReID",
                "package": None,
                "config_hook": None,
                "note": "Research project material without a regular Python package in this checkout.",
            },
        ),
        (
            "DG-ReID",
            {
                "relative_path": "projects/DG-ReID",
                "package": None,
                "config_hook": None,
                "note": "Research project material without a regular Python package in this checkout.",
            },
        ),
        (
            "HAA",
            {
                "relative_path": "projects/HAA",
                "package": None,
                "config_hook": None,
                "note": "Research project material without a regular Python package in this checkout.",
            },
        ),
    ]
)

REGISTRIES: Tuple[Tuple[str, str, str], ...] = (
    ("datasets", "fastreid.data.datasets", "DATASET_REGISTRY"),
    ("meta_arch", "fastreid.modeling.meta_arch", "META_ARCH_REGISTRY"),
    ("backbones", "fastreid.modeling.backbones", "BACKBONE_REGISTRY"),
    ("heads", "fastreid.modeling.heads.build", "REID_HEADS_REGISTRY"),
)


def safe_insert_path(path: Path) -> None:
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


def expand_projects(selected: Optional[Iterable[str]]) -> List[str]:
    if not selected:
        return list(PROJECTS.keys())
    expanded: List[str] = []
    for item in selected:
        if item == "all":
            for name in PROJECTS:
                if name not in expanded:
                    expanded.append(name)
        elif item not in expanded:
            expanded.append(item)
    return expanded


def registry_snapshot() -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    snapshot: Dict[str, List[str]] = {}
    errors: Dict[str, str] = {}
    for label, module_name, attr_name in REGISTRIES:
        try:
            module = importlib.import_module(module_name)
            registry = getattr(module, attr_name)
            obj_map = getattr(registry, "_obj_map", {})
            snapshot[label] = sorted(str(k) for k in obj_map.keys())
        except Exception as exc:
            snapshot[label] = []
            errors[label] = f"{exc.__class__.__name__}: {exc}"
    return snapshot, errors


def diff_registries(before: Dict[str, List[str]], after: Dict[str, List[str]]) -> Dict[str, List[str]]:
    diff: Dict[str, List[str]] = {}
    for key in sorted(set(before) | set(after)):
        before_set = set(before.get(key, []))
        after_set = set(after.get(key, []))
        added = sorted(after_set - before_set)
        if added:
            diff[key] = added
    return diff


def probe_project(repo_root: Path, name: str) -> Dict[str, Any]:
    meta = PROJECTS[name]
    project_dir = (repo_root / meta["relative_path"]).resolve(strict=False)
    result: Dict[str, Any] = {
        "project": name,
        "project_path": str(project_dir),
        "package": meta["package"],
        "config_hook": meta["config_hook"],
        "note": meta["note"],
        "status": "unknown",
        "error": None,
        "traceback": None,
        "registry_added": {},
        "registry_probe_errors": {},
    }

    try:
        project_dir.relative_to(repo_root)
    except ValueError:
        result["status"] = "invalid_path"
        result["error"] = "Resolved project directory escapes the selected repo root."
        return result

    if not project_dir.exists():
        result["status"] = "missing_path"
        result["error"] = "Project directory does not exist under the selected repo root."
        return result

    before, before_errors = registry_snapshot()
    safe_insert_path(project_dir)
    importlib.invalidate_caches()

    package = meta["package"]
    if not package:
        after, after_errors = registry_snapshot()
        result["status"] = "not_python_project"
        result["registry_added"] = diff_registries(before, after)
        result["registry_probe_errors"] = {**before_errors, **after_errors}
        return result

    try:
        module = importlib.import_module(package)
        result["status"] = "imported"
        result["module_file"] = getattr(module, "__file__", None)
        hook = meta.get("config_hook")
        if hook:
            result["config_hook_present"] = hasattr(module, hook)
    except Exception as exc:
        result["status"] = "import_failed"
        result["error"] = f"{exc.__class__.__name__}: {exc}"
        result["traceback"] = traceback.format_exc(limit=8)

    after, after_errors = registry_snapshot()
    result["registry_added"] = diff_registries(before, after)
    result["registry_probe_errors"] = {**before_errors, **after_errors}
    return result


def build_report(repo_root_arg: str, selected: List[str]) -> Dict[str, Any]:
    repo_root = Path(repo_root_arg).expanduser().resolve(strict=False)
    report: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "projects_requested": selected,
        "status": "ok",
        "warnings": [],
        "results": [],
    }

    if not repo_root.exists():
        report["status"] = "repo_missing"
        report["warnings"].append("Selected repo root does not exist.")
        return report
    if not (repo_root / "fastreid").exists():
        report["warnings"].append("Selected repo root does not contain a fastreid package directory.")

    safe_insert_path(repo_root)
    importlib.invalidate_caches()

    expanded = expand_projects(selected)
    report["projects_expanded"] = expanded
    for name in expanded:
        report["results"].append(probe_project(repo_root, name))
    return report


def print_text(report: Dict[str, Any]) -> None:
    print(f"Repo root: {report['repo_root']}")
    if report.get("warnings"):
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"- {warning}")
    for item in report.get("results", []):
        print(f"\n[{item['project']}] {item['status']}")
        print(f"  package: {item['package'] or '(no Python package)'}")
        print(f"  project path: {item['project_path']}")
        print(f"  note: {item['note']}")
        if item.get("config_hook"):
            present = item.get("config_hook_present")
            suffix = "" if present is None else f" present={present}"
            print(f"  config hook: {item['config_hook']}{suffix}")
        if item.get("module_file"):
            print(f"  module file: {item['module_file']}")
        if item.get("registry_added"):
            print("  registry additions:")
            for label, values in sorted(item["registry_added"].items()):
                print(f"    {label}: {', '.join(values)}")
        if item.get("registry_probe_errors"):
            print("  registry probe errors:")
            for label, error in sorted(item["registry_probe_errors"].items()):
                print(f"    {label}: {error}")
        if item.get("error"):
            print(f"  error: {item['error']}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely import FastReID extension project packages and report registry side effects without training.",
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="FastReID application checkout root whose fastreid package and projects directory should be probed.",
    )
    parser.add_argument(
        "--project",
        action="append",
        choices=["all"] + list(PROJECTS.keys()),
        help="Project to probe; may be repeated. Use 'all' or omit to probe every supported project.",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON report instead of human-readable text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if the repo root is missing, a selected project path is missing/invalid, or a selected Python package import fails",
    )
    return parser.parse_args(argv)


def strict_failed(report: Dict[str, Any]) -> bool:
    if report.get("status") != "ok":
        return True
    failing_statuses = {"missing_path", "invalid_path", "import_failed"}
    return any(item.get("status") in failing_statuses for item in report.get("results", []))


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    selected = args.project if args.project else ["all"]
    report = build_report(args.repo_root, selected)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and strict_failed(report):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
