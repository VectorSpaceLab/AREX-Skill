#!/usr/bin/env python3
"""Read-only setup checker for a PyTracking checkout.

This helper validates the presence of PyTracking/LTR source roots and the local
configuration files that PyTracking uses for datasets, checkpoints, workspaces,
and result outputs. It does not import tracker code, download checkpoints, run
benchmarks, open cameras, or launch training.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

EVAL_DATASET_FIELDS = {
    "otb": "otb_path",
    "nfs": "nfs_path",
    "uav": "uav_path",
    "tpl": "tpl_path",
    "tpl_nootb": "tpl_path",
    "vot": "vot_path",
    "trackingnet": "trackingnet_path",
    "trackingnetvos": "trackingnet_path",
    "got10k_test": "got10k_path",
    "got10k_val": "got10k_path",
    "got10k_ltrval": "got10k_path",
    "got10kvos_val": "got10k_path",
    "lasot": "lasot_path",
    "lasot_train": "lasot_path",
    "lasotvos": "lasot_path",
    "lasot_extension_subset": "lasot_extension_subset_path",
    "oxuva_dev": "oxuva_path",
    "oxuva_test": "oxuva_path",
    "avist": "avist_path",
    "dv2016_val": "davis_dir",
    "dv2017_val": "davis_dir",
    "dv2017_test_dev": "davis_dir",
    "dv2017_test_chal": "davis_dir",
    "yt2018_jjval": "youtubevos_dir",
    "yt2018_valid_all": "youtubevos_dir",
    "yt2019_test": "youtubevos_dir",
    "yt2019_valid": "youtubevos_dir",
    "yt2019_valid_all": "youtubevos_dir",
    "yt2019_jjval": "youtubevos_dir",
    "yt2019_jjval_all": "youtubevos_dir",
    "lagot": "lagot_path",
    "lagot_sot_mode": "lagot_path",
}

COMMON_EVAL_FIELDS = ["results_path", "segmentation_path", "network_path", "result_plot_path"]
COMMON_LTR_FIELDS = ["workspace_dir", "tensorboard_dir", "pretrained_networks"]


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    candidates = [start] + list(start.parents)
    for candidate in candidates:
        if (candidate / "pytracking" / "__init__.py").exists() and (candidate / "ltr" / "__init__.py").exists():
            return candidate
    raise SystemExit(f"Could not find a PyTracking checkout from {start}")


def literal_value(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = literal_value(node.left)
            right = literal_value(node.right)
            if isinstance(left, str) and isinstance(right, str):
                return left + right
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        return "<dynamic>"


def parse_settings_assignments(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text())
    values: Dict[str, Any] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                # pytracking/evaluation/local.py: settings.attr = '...'
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    if target.value.id in {"settings", "self"}:
                        values[target.attr] = literal_value(node.value)
    return values


def check_path_field(root: Path, values: Dict[str, Any], field: str) -> Dict[str, Any]:
    value = values.get(field)
    status = "missing"
    exists = False
    if value is not None:
        if value == "" or value == "<dynamic>":
            status = "empty" if value == "" else "dynamic"
        else:
            candidate = Path(str(value)).expanduser()
            if not candidate.is_absolute():
                candidate = (root / candidate).resolve()
            exists = candidate.exists()
            status = "ok" if exists else "not-found"
    return {"field": field, "value": value, "status": status, "exists": exists}


def summarize_checks(root: Path, require_dataset: str | None, require_training: bool) -> Tuple[Dict[str, Any], int]:
    eval_local = root / "pytracking" / "evaluation" / "local.py"
    ltr_local = root / "ltr" / "admin" / "local.py"
    eval_values = parse_settings_assignments(eval_local)
    ltr_values = parse_settings_assignments(ltr_local)

    issues = []
    source_checks = {
        "pytracking_package": (root / "pytracking" / "__init__.py").exists(),
        "ltr_package": (root / "ltr" / "__init__.py").exists(),
        "evaluation_local": eval_local.exists(),
        "ltr_local": ltr_local.exists(),
    }
    for name, ok in source_checks.items():
        if not ok:
            issues.append(f"missing {name.replace('_', ' ')}")

    eval_fields = list(COMMON_EVAL_FIELDS)
    if require_dataset:
        alias = require_dataset.lower()
        if alias not in EVAL_DATASET_FIELDS:
            issues.append(f"unknown dataset alias {require_dataset!r}")
        else:
            eval_fields.append(EVAL_DATASET_FIELDS[alias])

    eval_field_checks = [check_path_field(root, eval_values, field) for field in dict.fromkeys(eval_fields)]
    ltr_field_checks = [check_path_field(root, ltr_values, field) for field in COMMON_LTR_FIELDS]
    if require_training:
        for field in ["workspace_dir", "pretrained_networks"]:
            if field not in [item["field"] for item in ltr_field_checks]:
                ltr_field_checks.append(check_path_field(root, ltr_values, field))

    for item in eval_field_checks:
        if item["status"] in {"missing", "empty", "not-found"}:
            issues.append(f"evaluation {item['field']} is {item['status']}")
    if require_training:
        for item in ltr_field_checks:
            if item["status"] in {"missing", "empty", "not-found"}:
                issues.append(f"LTR {item['field']} is {item['status']}")

    result = {
        "repoRoot": str(root),
        "sourceChecks": source_checks,
        "evaluationLocal": {"path": str(eval_local), "exists": eval_local.exists(), "fields": eval_field_checks},
        "ltrLocal": {"path": str(ltr_local), "exists": ltr_local.exists(), "fields": ltr_field_checks},
        "requiredDataset": require_dataset,
        "requireTraining": require_training,
        "issues": issues,
        "status": "ok" if not issues else "needs-attention",
    }
    return result, 0 if not issues else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only PyTracking setup/local.py checker.")
    parser.add_argument("--repo-root", default=".", help="PyTracking checkout root or a descendant directory.")
    parser.add_argument("--require-dataset", help="Dataset alias whose local path should be checked.")
    parser.add_argument("--require-training", action="store_true", help="Also require core LTR training workspace/checkpoint fields.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    root = find_repo_root(Path(args.repo_root))
    result, code = summarize_checks(root, args.require_dataset, args.require_training)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"PyTracking repo: {result['repoRoot']}")
        print(f"Status: {result['status']}")
        for label, group in [("evaluation", result["evaluationLocal"]), ("LTR", result["ltrLocal"] )]:
            print(f"\n{label} local config: {group['path']} ({'present' if group['exists'] else 'missing'})")
            for field in group["fields"]:
                print(f"- {field['field']}: {field['status']}")
        if result["issues"]:
            print("\nIssues:")
            for issue in result["issues"]:
                print(f"- {issue}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
