#!/usr/bin/env python3
"""Print or validate the legacy MedicalDetectionToolkit CLI contract.

This helper deliberately does not import exec.py or any repository module.  It
can optionally parse a user-supplied exec.py with AST to show literal
argparse declarations; the file is bounded and read-only.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any

MODES = ("train", "test", "train_test", "analysis", "create_exp")
DEFAULTS = {
    "mode": "train_test",
    "folds": None,
    "exp_dir": "/path/to/experiment/directory",
    "server_env": False,
    "data_dest": None,
    "use_stored_settings": False,
    "resume_to_checkpoint": None,
    "exp_source": "experiments/toy_exp",
    "dev": False,
}
MAX_EXEC_BYTES = 1_000_000


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        return ast.unparse(node) if hasattr(ast, "unparse") else "<expression>"


def inspect_exec_file(path: Path) -> list[dict[str, Any]]:
    """Extract literal ``add_argument`` calls from a bounded source file."""
    size = path.stat().st_size
    if size > MAX_EXEC_BYTES:
        raise ValueError(f"refusing to parse {path}: {size} bytes exceeds {MAX_EXEC_BYTES}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument":
            continue
        flags = [_literal(arg) for arg in node.args]
        keywords = {kw.arg: _literal(kw.value) for kw in node.keywords if kw.arg}
        found.append({"flags": flags, "keywords": keywords, "line": node.lineno})
    return found


def contract() -> dict[str, Any]:
    return {
        "entry_point": "exec.py",
        "modes": list(MODES),
        "arguments": [
            {"flags": ["-m", "--mode"], "type": "str", "default": "train_test"},
            {"flags": ["-f", "--folds"], "type": "int", "nargs": "+", "default": None},
            {"flags": ["--exp_dir"], "type": "str", "default": DEFAULTS["exp_dir"]},
            {"flags": ["--server_env"], "action": "store_true", "default": False},
            {"flags": ["--data_dest"], "type": "str", "default": None},
            {"flags": ["--use_stored_settings"], "action": "store_true", "default": False},
            {"flags": ["--resume_to_checkpoint"], "type": "str", "default": None},
            {"flags": ["--exp_source"], "type": "str", "default": "experiments/toy_exp"},
            {"flags": ["-d", "--dev"], "action": "store_true", "default": False},
        ],
        "notes": [
            "This report is a static contract; it does not start a job.",
            "The source parser does not bound-check fold IDs.",
            "Testing uses stored settings regardless of the training flag.",
        ],
    }


def validate(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if args.mode not in MODES:
        errors.append(f"mode must be one of {', '.join(MODES)}")
    if args.folds is not None:
        if not args.folds:
            errors.append("folds must contain at least one integer")
        elif any(f < 0 for f in args.folds):
            errors.append("fold IDs must be non-negative")
        elif any(f >= args.n_cv_splits for f in args.folds):
            errors.append(f"fold IDs must be less than n_cv_splits={args.n_cv_splits}")
    if args.exp_dir == DEFAULTS["exp_dir"]:
        errors.append("replace the placeholder --exp-dir before a real invocation")
    if not args.exp_source:
        errors.append("--exp-source must not be empty")
    if args.resume_to_checkpoint and args.folds is None:
        errors.append("--resume-to-checkpoint requires an explicit --folds selection")
    if args.server_env and not args.data_dest:
        warnings.append("server mode commonly needs --data-dest; verify the deployment contract")
    if args.mode in {"train", "train_test", "test", "analysis"}:
        warnings.append("validation only: this helper never launches the selected mode")
    if args.mode == "create_exp":
        warnings.append("create_exp can still create/copy files through legacy prep_exp")
    if not Path(args.exp_dir).is_absolute():
        warnings.append("relative exp-dir is accepted by the legacy CLI but an isolated absolute path is safer")
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exec-file", type=Path, help="optional bounded exec.py to inspect read-only")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a human report")
    parser.add_argument("--check", action="store_true", help="validate the supplied invocation fields")
    parser.add_argument("--mode", choices=MODES, default=DEFAULTS["mode"])
    parser.add_argument("--folds", nargs="+", type=int, default=None)
    parser.add_argument("--n-cv-splits", type=int, default=5)
    parser.add_argument("--exp-dir", default=DEFAULTS["exp_dir"])
    parser.add_argument("--exp-source", default=DEFAULTS["exp_source"])
    parser.add_argument("--server-env", action="store_true")
    parser.add_argument("--data-dest")
    parser.add_argument("--resume-to-checkpoint")
    ns = parser.parse_args(argv)
    if ns.n_cv_splits <= 0:
        parser.error("--n-cv-splits must be positive")

    report: dict[str, Any] = {"contract": contract()}
    if ns.exec_file:
        try:
            report["parsed_exec_file"] = str(ns.exec_file)
            report["literal_add_argument_calls"] = inspect_exec_file(ns.exec_file)
        except (OSError, SyntaxError, ValueError) as exc:
            report["exec_file_error"] = f"{type(exc).__name__}: {exc}"
            if ns.check:
                return _emit(report, ns.json, 2)
    if ns.check:
        errors, warnings = validate(ns)
        report["errors"] = errors
        report["warnings"] = warnings
        code = 2 if errors else 0
    else:
        report["errors"] = []
        report["warnings"] = ["use --check with concrete fields to validate an invocation"]
        code = 0
    return _emit(report, ns.json, code)


def _emit(report: dict[str, Any], as_json: bool, code: int) -> int:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return code
    print("MedicalDetectionToolkit CLI (static, no execution)")
    print("modes: " + ", ".join(report["contract"]["modes"]))
    for item in report["contract"]["arguments"]:
        print(f"  {'/'.join(item['flags'])}: default={item.get('default')!r}")
    if "literal_add_argument_calls" in report:
        print(f"parsed add_argument calls: {len(report['literal_add_argument_calls'])}")
    if report.get("exec_file_error"):
        print("exec-file error:", report["exec_file_error"])
    for warning in report.get("warnings", []):
        print("WARNING:", warning)
    for error in report.get("errors", []):
        print("ERROR:", error)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
