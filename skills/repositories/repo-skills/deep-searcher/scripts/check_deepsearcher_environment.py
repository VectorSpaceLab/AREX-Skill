#!/usr/bin/env python3
"""Read-only DeepSearcher environment sanity check.

This helper reports installed versions, importability of key public modules, and
optionally a temp-cwd CLI help probe. It does not contact provider APIs, load a
corpus, or mutate the environment.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from importlib.metadata import PackageNotFoundError, entry_points, version
from pathlib import Path
from typing import Any

MODULES = [
    "deepsearcher",
    "deepsearcher.configuration",
    "deepsearcher.offline_loading",
    "deepsearcher.online_query",
    "deepsearcher.agent",
    "deepsearcher.loader.file_loader",
    "deepsearcher.loader.web_crawler",
    "deepsearcher.llm",
    "deepsearcher.embedding",
    "deepsearcher.vector_db",
]

DISTRIBUTIONS = ["deepsearcher", "firecrawl-py", "pymilvus", "milvus-lite", "fastapi", "openai"]


@dataclass
class ImportResult:
    module: str
    ok: bool
    message: str = ""


@dataclass
class CliProbeResult:
    command: str
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the installed DeepSearcher environment safely.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    parser.add_argument(
        "--check-cli-help",
        action="store_true",
        help="Run a temp-cwd CLI help probe with a dummy OpenAI key.",
    )
    parser.add_argument(
        "--entrypoint",
        choices=["module", "console"],
        default="module",
        help="Which CLI entrypoint to probe when --check-cli-help is used.",
    )
    return parser.parse_args()


def get_versions() -> dict[str, str]:
    data: dict[str, str] = {}
    for dist in DISTRIBUTIONS:
        try:
            data[dist] = version(dist)
        except PackageNotFoundError:
            data[dist] = "missing"
    return data


def get_console_script() -> str:
    for ep in entry_points(group="console_scripts"):
        if ep.name == "deepsearcher":
            return f"{ep.name}={ep.value}"
    return "missing"


def check_imports() -> list[ImportResult]:
    results: list[ImportResult] = []
    for module in MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - environment dependent
            results.append(ImportResult(module=module, ok=False, message=f"{type(exc).__name__}: {exc}"))
        else:
            results.append(ImportResult(module=module, ok=True))
    return results


def classify_cli_failure(stderr: str) -> str:
    lowered = stderr.lower()
    if "missing credentials" in lowered or "openaierror" in lowered:
        return "provider credentials are missing or the default OpenAI config is active"
    if "scrapeoptions" in lowered:
        return "the installed FireCrawl client is incompatible with this checkout"
    if "milvus-lite" in lowered and "required" in lowered:
        return "local Milvus Lite support is missing"
    if "showcollectionsresponse has no \"shards_num\" field" in lowered:
        return "pymilvus and milvus-lite versions are mismatched"
    if "pkg_resources" in lowered:
        return "setuptools is too new for the pinned milvus-lite release"
    if "module not found" in lowered:
        return "a required package is missing from the environment"
    return "the CLI help probe failed for an environment-specific reason"


def run_cli_probe(entrypoint: str) -> CliProbeResult:
    with tempfile.TemporaryDirectory(prefix="deepsearcher-cli-help-") as tmp:
        env = os.environ.copy()
        env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY", "dummy")
        env["PYTHONPATH"] = env.get("PYTHONPATH", "")
        cwd = Path(tmp)
        if entrypoint == "module":
            command = [sys.executable, "-m", "deepsearcher.cli", "--help"]
        else:
            command = ["deepsearcher", "--help"]
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        stderr = completed.stderr.strip()
        note = ""
        if completed.returncode != 0:
            note = classify_cli_failure(stderr)
        return CliProbeResult(
            command=" ".join(command),
            ok=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=stderr,
            note=note,
        )


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "versions": get_versions(),
        "console_script": get_console_script(),
        "imports": [asdict(item) for item in check_imports()],
    }
    if args.check_cli_help:
        report["cli_probe"] = asdict(run_cli_probe(args.entrypoint))

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DeepSearcher environment summary")
        print("================================")
        for dist, dist_version in report["versions"].items():
            print(f"{dist}: {dist_version}")
        print(f"console script: {report['console_script']}")
        print("\nImports:")
        for item in report["imports"]:
            status = "OK" if item["ok"] else "FAIL"
            detail = f" - {item['message']}" if item["message"] else ""
            print(f"- {status} {item['module']}{detail}")
        if args.check_cli_help:
            probe = report["cli_probe"]
            print("\nCLI help probe:")
            print(f"- command: {probe['command']}")
            print(f"- exit_code: {probe['exit_code']}")
            print(f"- ok: {probe['ok']}")
            if probe["note"]:
                print(f"- note: {probe['note']}")
            if probe["stderr"]:
                print(f"- stderr: {probe['stderr']}")

    return 0 if all(item["ok"] for item in report["imports"]) and (not args.check_cli_help or report["cli_probe"]["ok"]) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
