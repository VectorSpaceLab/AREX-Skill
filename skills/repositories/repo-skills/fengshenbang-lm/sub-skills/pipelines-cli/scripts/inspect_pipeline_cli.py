#!/usr/bin/env python3
"""Inspect Fengshen pipeline CLI parser surfaces without downloads or training.

This script imports the installed `fengshen` package, inspects parser methods for
selected pipeline modules, and optionally prints/runs safe `--help` guidance. It
never instantiates a model unless the installed package does that during import,
and it never launches training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable, List

DEFAULT_PIPELINES = ["text_classification", "sequence_tagging"]
CLASS_FALLBACK = {
    "text_classification": "TextClassificationPipeline",
    "sequence_tagging": "SequenceTaggingPipeline",
}


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect installed Fengshen pipeline argparse surfaces safely."
    )
    parser.add_argument(
        "--pipeline",
        action="append",
        dest="pipelines",
        help=(
            "Pipeline module name to inspect, e.g. text_classification. "
            "May be supplied more than once. Defaults to text_classification "
            "and sequence_tagging."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--show-help-command",
        action="store_true",
        default=True,
        help="Include suggested fengshen-pipeline --help commands in the report.",
    )
    parser.add_argument(
        "--run-help",
        action="store_true",
        help=(
            "Actually run `fengshen-pipeline <pipeline> predict --help` with a "
            "short timeout. This is still help-only, but it depends on the "
            "installed console script and imports."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any requested pipeline cannot be inspected.",
    )
    return parser


def add_console_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--model", default="", type=str)
    parser.add_argument("--datasets", default="", type=str)
    parser.add_argument("--text", default="", type=str)
    return parser


def collect_parser_options(parser: argparse.ArgumentParser) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    for group in parser._action_groups:  # argparse public enough for inspection
        actions = []
        for action in group._group_actions:
            option_strings = [s for s in action.option_strings if s.startswith("--")]
            if not option_strings:
                continue
            item: Dict[str, Any] = {
                "options": option_strings,
                "dest": action.dest,
                "default": None if action.default is argparse.SUPPRESS else action.default,
                "required": bool(getattr(action, "required", False)),
            }
            if getattr(action, "choices", None) is not None:
                item["choices"] = list(action.choices)
            actions.append(item)
        if actions:
            groups.append({"title": group.title, "options": actions})
    return groups


def inspect_pipeline(name: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "pipeline": name,
        "module": f"fengshen.pipelines.{name}",
        "ok": False,
        "console_compatible": False,
        "help_command": f"fengshen-pipeline {name} predict --help",
        "notes": [],
    }
    try:
        module = importlib.import_module(result["module"])
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should preserve failures
        result["error"] = f"import failed: {type(exc).__name__}: {exc}"
        result["notes"].append(
            "If the module name is valid, this may be a dependency-stack import failure rather than an unknown pipeline."
        )
        return result

    cls = getattr(module, "Pipeline", None)
    if cls is None and name in CLASS_FALLBACK:
        cls = getattr(module, CLASS_FALLBACK[name], None)
        if cls is not None:
            result["notes"].append(
                f"No module-level Pipeline alias was used; inspected fallback class {CLASS_FALLBACK[name]}."
            )
    if cls is None:
        result["error"] = "module imported but has no Pipeline alias or known fallback class"
        result["notes"].append("This package surface is probably programmatic-only for the console command.")
        return result

    result["class"] = f"{cls.__module__}.{cls.__name__}"
    method = getattr(cls, "add_pipeline_specific_args", None)
    if method is None:
        result["error"] = "class has no add_pipeline_specific_args(parent_args) method"
        result["notes"].append("The generic console command requires this exact method name.")
        return result

    parser = argparse.ArgumentParser(prog=f"fengshen-pipeline {name} predict")
    add_console_common_args(parser)
    try:
        method(parser)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"parser construction failed: {type(exc).__name__}: {exc}"
        return result

    result["ok"] = True
    result["console_compatible"] = hasattr(module, "Pipeline")
    result["arg_groups"] = collect_parser_options(parser)
    result["option_count"] = sum(len(g["options"]) for g in result["arg_groups"])
    return result


def maybe_run_help(name: str, timeout: float = 15.0) -> Dict[str, Any]:
    exe = shutil.which("fengshen-pipeline")
    if exe is None:
        return {"pipeline": name, "ran": False, "error": "fengshen-pipeline not found on PATH"}
    cmd = [exe, name, "predict", "--help"]
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {"pipeline": name, "ran": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "pipeline": name,
        "ran": True,
        "returncode": proc.returncode,
        "stdout_first_lines": proc.stdout.splitlines()[:40],
        "stderr_first_lines": proc.stderr.splitlines()[:40],
    }


def text_report(results: Iterable[Dict[str, Any]], help_results: Iterable[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for item in results:
        status = "OK" if item.get("ok") else "ERROR"
        lines.append(f"[{status}] {item['pipeline']} ({item['module']})")
        if item.get("class"):
            lines.append(f"  class: {item['class']}")
        lines.append(f"  help:  {item['help_command']}")
        if item.get("console_compatible"):
            lines.append("  console contract: module has Pipeline alias and add_pipeline_specific_args")
        elif item.get("ok"):
            lines.append("  console contract: parser inspected, but module alias compatibility should be checked")
        if item.get("option_count") is not None:
            lines.append(f"  options: {item['option_count']}")
            preview: List[str] = []
            for group in item.get("arg_groups", []):
                for opt in group.get("options", []):
                    preview.extend(opt["options"][:1])
            if preview:
                lines.append("  preview: " + ", ".join(preview[:30]))
        if item.get("error"):
            lines.append(f"  error: {item['error']}")
        for note in item.get("notes", []):
            lines.append(f"  note:  {note}")
        lines.append("")

    for item in help_results:
        lines.append(f"[HELP RUN] {item['pipeline']}")
        if not item.get("ran"):
            lines.append(f"  not run: {item.get('error')}")
        else:
            lines.append(f"  returncode: {item.get('returncode')}")
            if item.get("stdout_first_lines"):
                lines.append("  stdout:")
                lines.extend("    " + line for line in item["stdout_first_lines"])
            if item.get("stderr_first_lines"):
                lines.append("  stderr:")
                lines.extend("    " + line for line in item["stderr_first_lines"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: List[str] | None = None) -> int:
    args = build_cli_parser().parse_args(argv)
    pipelines = args.pipelines or DEFAULT_PIPELINES
    results = [inspect_pipeline(name) for name in pipelines]
    help_results = [maybe_run_help(name) for name in pipelines] if args.run_help else []

    payload = {"results": results, "help_runs": help_results}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(text_report(results, help_results), end="")

    if args.strict and (any(not r.get("ok") for r in results) or any(h.get("returncode", 0) != 0 for h in help_results)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
