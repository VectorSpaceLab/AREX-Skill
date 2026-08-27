#!/usr/bin/env python3
"""Inspect BiSheng Linsight and MCP source surfaces without imports."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

TARGETS = [
    "src/backend/bisheng/linsight/worker.py",
    "src/backend/bisheng/linsight/domain/task_exec.py",
    "src/backend/bisheng/linsight/domain/services/state_message_manager.py",
    "src/backend/bisheng/linsight/domain/services/agent_factory.py",
    "src/backend/bisheng/linsight/domain/services/stream_event_mapper.py",
    "src/backend/bisheng/linsight/domain/services/workspace_backend.py",
    "src/backend/bisheng_langchain/linsight/event.py",
    "src/backend/bisheng_langchain/linsight/utils.py",
    "src/backend/bisheng/mcp_manage/manager.py",
    "src/backend/bisheng/mcp_manage/langchain/tool.py",
]


def symbols(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {"classes": [], "functions": []}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return {"classes": [], "functions": []}
    return {
        "classes": [n.name for n in tree.body if isinstance(n, ast.ClassDef)],
        "functions": [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Linsight/MCP source files.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    result = {rel: {"exists": (repo / rel).exists(), **symbols(repo / rel)} for rel in TARGETS}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("BiSheng Linsight/MCP surface")
        print("===========================")
        for rel, info in result.items():
            print(f"{rel}: {'OK' if info['exists'] else 'MISSING'}")
            if info["classes"]:
                print("  classes:", ", ".join(info["classes"]))
            if info["functions"]:
                print("  functions:", ", ".join(info["functions"]))
    return 0 if all(info["exists"] for info in result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
