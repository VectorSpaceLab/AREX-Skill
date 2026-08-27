#!/usr/bin/env python3
"""No-network PaperQA readiness check for installed package environments.

The script imports core modules, reports installed distribution versions, checks
safe CLI help availability, constructs Settings, and optionally inspects parser
extras. It does not call LLMs, embeddings, metadata providers, ClinicalTrials.gov,
OpenReview, Zotero, Qdrant services, or PDF parsing APIs.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

CORE_MODULES = [
    "paperqa",
    "paperqa.agents",
    "paperqa.settings",
    "paperqa.readers",
    "paperqa.clients",
]
OPTIONAL_MODULES = [
    "paperqa_pypdf",
    "paperqa_pymupdf",
    "paperqa_docling",
    "paperqa_nemotron",
    "qdrant_client",
    "sentence_transformers",
    "unstructured",
    "pyzotero",
    "openreview",
]
DISTRIBUTIONS = [
    "paper-qa",
    "paper-qa-pypdf",
    "paper-qa-pymupdf",
    "paper-qa-docling",
    "paper-qa-nemotron",
]


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def import_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "file": getattr(module, "__file__", None)}


def run_cli_help(timeout: float) -> dict[str, Any]:
    exe = shutil.which("pqa")
    if not exe:
        sibling = Path(sys.executable).with_name("pqa")
        exe = str(sibling) if sibling.exists() else None
    if not exe:
        return {"ok": False, "error": "pqa entry point not found on PATH or beside sys.executable"}
    try:
        proc = subprocess.run(
            [exe, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return {"ok": False, "command": [exe, "--help"], "error": f"{type(exc).__name__}: {exc}"}
    expected = all(token in proc.stdout for token in ["ask", "search", "index", "view", "save"])
    return {
        "ok": proc.returncode == 0 and expected,
        "command": [exe, "--help"],
        "returncode": proc.returncode,
        "contains_commands": expected,
        "stderr": proc.stderr.strip()[:500],
    }


def settings_smoke() -> dict[str, Any]:
    from paperqa import Settings

    default = Settings()
    fast = Settings.from_name("fast")
    return {
        "ok": True,
        "default": {
            "llm": default.llm,
            "summary_llm": default.summary_llm,
            "embedding": default.embedding,
            "agent_type": default.agent.agent_type,
            "evidence_k": default.answer.evidence_k,
        },
        "fast": {
            "agent_type": fast.agent.agent_type,
            "evidence_k": fast.answer.evidence_k,
            "answer_max_sources": fast.answer.answer_max_sources,
        },
    }


def parser_signature_smoke() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for module_name in ["paperqa_pypdf", "paperqa_pymupdf", "paperqa_docling", "paperqa_nemotron"]:
        try:
            module = importlib.import_module(module_name)
            parser = getattr(module, "parse_pdf_to_pages")
        except Exception as exc:  # noqa: BLE001 - optional diagnostic
            result[module_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        else:
            result[module_name] = {"ok": True, "signature": str(inspect.signature(parser))}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--include-optional", action="store_true", help="Inspect optional module imports/signatures.")
    parser.add_argument("--cli-timeout", type=float, default=10.0, help="Timeout for `pqa --help`.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version,
        "executable": sys.executable,
        "distributions": {name: dist_version(name) for name in DISTRIBUTIONS},
        "imports": {name: import_status(name) for name in CORE_MODULES},
        "settings": None,
        "cli_help": run_cli_help(args.cli_timeout),
    }
    try:
        report["settings"] = settings_smoke()
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        report["settings"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.include_optional:
        report["optional_imports"] = {name: import_status(name) for name in OPTIONAL_MODULES}
        report["parser_signatures"] = parser_signature_smoke()

    core_ok = all(item["ok"] for item in report["imports"].values())
    settings_ok = bool(report["settings"] and report["settings"].get("ok"))
    cli_ok = bool(report["cli_help"].get("ok"))
    report["ok"] = core_ok and settings_ok and cli_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok={report['ok']} paper-qa={report['distributions'].get('paper-qa')} cli={cli_ok}")
        for name, status in report["imports"].items():
            print(f"import {name}: {'ok' if status['ok'] else status['error']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
