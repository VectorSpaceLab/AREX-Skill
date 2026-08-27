#!/usr/bin/env python3
"""Check a RAGs runtime environment and optional source checkout imports.

This diagnostic is safe by default: it imports dependencies, optionally imports
RAGs source modules with temporary dummy Streamlit secrets, and never calls
external LLMs, downloads URLs, or launches a Streamlit server.

Examples:
  python scripts/check_install.py
  python scripts/check_install.py --repo-root /path/to/rags
  python scripts/check_install.py --repo-root /path/to/rags --real-secrets
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

DEPENDENCIES = [
    ("streamlit", "streamlit"),
    ("streamlit_pills", "streamlit-pills"),
    ("llama_index", "llama-index"),
    ("llama_hub", "llama-hub"),
    ("langchain", "langchain"),
    ("pypdf", "pypdf"),
]

SOURCE_IMPORT_SNIPPET = r'''
import json
import os
from core.param_cache import RAGParams
from core.agent_builder.base import RAGAgentBuilder
from core.agent_builder.registry import AgentCacheRegistry
from core import utils
from core.agent_builder.multimodal import MultimodalRAGAgentBuilder

builder = RAGAgentBuilder(agent_registry=AgentCacheRegistry(os.environ["RAGS_INSPECT_CACHE_DIR"]))
print(json.dumps({
    "status": "ok",
    "rag_params": RAGParams().dict(),
    "builder_id_prefix_ok": builder.cache.agent_id.startswith("Agent_"),
    "has_load_data": hasattr(utils, "load_data"),
    "has_multimodal_builder": MultimodalRAGAgentBuilder.__name__,
}, sort_keys=True))
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe RAGs install/source import checker.")
    parser.add_argument(
        "--repo-root",
        help="Optional path to a RAGs checkout for source-module import checks.",
    )
    parser.add_argument(
        "--real-secrets",
        action="store_true",
        help=(
            "Use the caller's real Streamlit secrets for source imports. By default, "
            "a temporary dummy openai_key is used to avoid requiring credentials."
        ),
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for JSON output. Use 0 for compact output.",
    )
    return parser


def check_dependency(module_name: str, dist_name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"module": module_name, "distribution": dist_name}
    try:
        importlib.import_module(module_name)
        item["import"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report import failure
        item["import"] = "failed"
        item["error"] = f"{type(exc).__name__}: {exc}"
    try:
        item["version"] = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        item["version"] = None
    return item


def run_source_import(repo_root: Path, use_dummy_secrets: bool) -> dict[str, Any]:
    if not repo_root.exists() or not repo_root.is_dir():
        return {"status": "failed", "error": "repo root is missing or not a directory"}

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

    temp_home_ctx = tempfile.TemporaryDirectory() if use_dummy_secrets else None
    try:
        if temp_home_ctx is not None:
            temp_home = Path(temp_home_ctx.name)
            secrets_dir = temp_home / ".streamlit"
            secrets_dir.mkdir(parents=True, exist_ok=True)
            (secrets_dir / "secrets.toml").write_text(
                'openai_key = "sk-dummy-for-import-only"\n'
                'metaphor_key = "dummy-metaphor"\n'
                'anthropic_key = "dummy-anthropic"\n'
                'replicate_key = "dummy-replicate"\n'
            )
            env["HOME"] = str(temp_home)

        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache_dir:
            env["RAGS_INSPECT_CACHE_DIR"] = cache_dir
            proc = subprocess.run(
                [sys.executable, "-c", SOURCE_IMPORT_SNIPPET],
                cwd=cwd,
                env=env,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
        result: dict[str, Any] = {
            "status": "ok" if proc.returncode == 0 else "failed",
            "returncode": proc.returncode,
            "used_dummy_secrets": use_dummy_secrets,
        }
        if proc.stdout.strip():
            last_line = proc.stdout.strip().splitlines()[-1]
            try:
                result["details"] = json.loads(last_line)
            except json.JSONDecodeError:
                result["stdout_tail"] = last_line
        if proc.stderr.strip():
            result["stderr_tail"] = proc.stderr.strip().splitlines()[-5:]
        return result
    finally:
        if temp_home_ctx is not None:
            temp_home_ctx.cleanup()


def main() -> int:
    args = build_parser().parse_args()
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "dependencies": [check_dependency(module, dist) for module, dist in DEPENDENCIES],
    }

    if args.repo_root:
        report["source_import"] = run_source_import(
            Path(args.repo_root).expanduser().resolve(),
            use_dummy_secrets=not args.real_secrets,
        )
    else:
        report["source_import"] = {
            "status": "skipped",
            "reason": "pass --repo-root to check RAGs source modules",
        }

    failed = any(item.get("import") != "ok" for item in report["dependencies"])
    if report["source_import"].get("status") == "failed":
        failed = True

    report["status"] = "failed" if failed else "ok"
    indent = None if args.json_indent == 0 else args.json_indent
    print(json.dumps(report, indent=indent, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
