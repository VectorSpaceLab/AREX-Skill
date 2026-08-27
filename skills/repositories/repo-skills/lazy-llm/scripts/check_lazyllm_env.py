#!/usr/bin/env python3
"""Safe LazyLLM import and optional workflow dependency checker.

Examples:
  python scripts/check_lazyllm_env.py
  python scripts/check_lazyllm_env.py --require-rag --require-agent --require-writer --json
  python scripts/check_lazyllm_env.py --repo-root /path/to/LazyLLM --require-rag

This script performs imports and tiny local object checks only. It does not call
model providers, download models, start external services, or launch MCP/npm.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _add_repo_root(repo_root: Optional[str]) -> None:
    if repo_root:
        root = os.path.abspath(repo_root)
        if root not in sys.path:
            sys.path.insert(0, root)


def _run_check(name: str, fn: Callable[[], str]) -> CheckResult:
    try:
        return CheckResult(name=name, ok=True, detail=fn())
    except Exception as exc:  # noqa: BLE001 - diagnostic surface should report any import failure
        return CheckResult(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}")


def _base() -> str:
    lazyllm = importlib.import_module("lazyllm")
    version = getattr(lazyllm, "__version__", "unknown")
    return f"lazyllm {version}; python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _cli() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "lazyllm.cli.main", "skills", "list"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        combined = (proc.stdout + proc.stderr).strip().splitlines()
        raise RuntimeError("lazyllm skills list failed: " + (combined[-1] if combined else "no output"))
    return "lazyllm skills list succeeded"


def _rag() -> str:
    from lazyllm.tools import Document, Retriever, Reranker  # noqa: F401
    from lazyllm.tools.rag.component.bm25 import BM25
    from lazyllm.tools.rag.doc_node import DocNode

    nodes = [DocNode(text="alpha beta"), DocNode(text="beta gamma")]
    hits = BM25(nodes, language="en", topk=1).retrieve("alpha")
    if not hits or hits[0][0] is not nodes[0]:
        raise AssertionError("BM25 smoke query did not return the expected node")
    return "RAG imports and BM25 tiny retrieval succeeded"


def _agent() -> str:
    import lazyllm
    from lazyllm.tools import ToolManager, fc_register  # noqa: F401

    @fc_register("tool", execute_in_sandbox=False)
    def lazyllm_env_probe_tool(x: int):
        """Return an integer unchanged for schema/sandbox smoke checks."""
        return x

    tool = lazyllm.tool.lazyllm_env_probe_tool()
    if getattr(tool, "execute_in_sandbox", None) is not False:
        raise AssertionError("fc_register sandbox metadata was not preserved")
    return "agent/tool imports and fc_register metadata succeeded"


def _writer() -> str:
    from lazyllm.tools.writer.data_models import WriterBlock, WriterDocument, WriterSpan

    doc = WriterDocument(
        document_id="env-smoke",
        title="Smoke",
        blocks=[WriterBlock(node_id="b1", type="paragraph", content="hello", spans=[WriterSpan(text="hello")])],
    )
    restored = WriterDocument.model_validate_json(doc.model_dump_json())
    if restored.blocks[0].spans[0].text != "hello":
        raise AssertionError("writer artifact round trip failed")
    return "writer artifact model round trip succeeded"


def _model() -> str:
    from lazyllm.module.llms.onlinemodule.map_model_type import get_model_type

    if get_model_type("qwen3-coder-plus") != "llm":
        raise AssertionError("model type inference failed for qwen3-coder-plus")
    return "model type inference smoke succeeded"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check LazyLLM imports and selected optional workflow groups.")
    parser.add_argument("--repo-root", help="Optional source checkout root to prepend to sys.path before imports.")
    parser.add_argument("--require-rag", action="store_true", help="Fail if LazyLLM RAG imports or local BM25 smoke fail.")
    parser.add_argument("--require-agent", action="store_true", help="Fail if LazyLLM agent/tool imports or fc_register smoke fail.")
    parser.add_argument("--require-writer", action="store_true", help="Fail if LazyLLM writer artifact imports or round-trip smoke fail.")
    parser.add_argument("--require-model", action="store_true", help="Fail if LazyLLM model helper imports or model type smoke fail.")
    parser.add_argument("--check-cli", action="store_true", help="Also run a safe lazyllm skills list CLI smoke.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    _add_repo_root(args.repo_root)

    checks: List[CheckResult] = [_run_check("base", _base)]
    if args.check_cli:
        checks.append(_run_check("cli", _cli))
    if args.require_rag:
        checks.append(_run_check("rag", _rag))
    if args.require_agent:
        checks.append(_run_check("agent", _agent))
    if args.require_writer:
        checks.append(_run_check("writer", _writer))
    if args.require_model:
        checks.append(_run_check("model", _model))

    ok = all(result.ok for result in checks)
    if args.json:
        print(json.dumps({"ok": ok, "checks": [asdict(result) for result in checks]}, indent=2, ensure_ascii=False))
    else:
        for result in checks:
            status = "OK" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {result.detail}")

    if not ok:
        print("\nInstall the smallest LazyLLM extra named by the failure before rerunning this check.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
