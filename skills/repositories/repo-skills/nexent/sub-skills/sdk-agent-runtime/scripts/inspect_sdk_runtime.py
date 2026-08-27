#!/usr/bin/env python3
"""Safely inspect Nexent SDK runtime APIs without starting services.

The script performs import-based signature inspection when dependencies are
available and falls back to AST/static source summaries when imports fail. It
never starts FastAPI, runs agents, opens MCP/A2A connections, calls external
models, starts Docker/Kubernetes, or touches live databases.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import os
import sys
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any


MODULE_TARGETS: dict[str, list[str]] = {
    "nexent.core.agents.agent_model": [
        "ModelConfig",
        "ToolConfig",
        "AgentConfig",
        "AgentRunInfo",
        "AgentVerificationConfig",
        "GuardrailConfig",
        "GuardrailRule",
        "ExternalA2AAgentConfig",
    ],
    "nexent.core.agents.core_agent": [
        "CoreAgent",
        "CoreAgent.run",
        "parse_code_blobs",
        "convert_code_format",
    ],
    "nexent.core.agents.nexent_agent": [
        "NexentAgent",
        "NexentAgent.create_model",
        "NexentAgent.create_tool",
        "NexentAgent.create_single_agent",
        "NexentAgent.agent_run_with_observer",
    ],
    "nexent.core.agents.run_agent": [
        "agent_run",
        "agent_run_thread",
        "_normalize_mcp_config",
    ],
    "nexent.core.agents.a2a_agent_proxy": [
        "A2AAgentInfo",
        "ExternalA2AAgentProxy",
        "ExternalA2AAgentProxy.call",
        "ExternalA2AAgentProxy.sync_call",
        "A2AAgentProxyTool",
        "A2AAgentProxyTool.forward",
        "ExternalA2AAgentWrapper",
        "ExternalA2AAgentWrapper.run",
    ],
    "nexent.core.agents.sandbox": [
        "SandboxConfig",
        "SandboxLevel",
        "SandboxScope",
        "ShellPolicy",
        "build_python_executor",
        "release_python_executor",
    ],
    "nexent.core.models.openai_llm": ["OpenAIModel", "OpenAIModel.check_connectivity"],
    "nexent.core.tools": [
        "ExaSearchTool",
        "KnowledgeBaseSearchTool",
        "TavilySearchTool",
        "LinkupSearchTool",
        "TerminalTool",
        "CreatePlanTool",
        "UpdatePlanStepTool",
    ],
    "nexent.core.utils.observer": [
        "MessageObserver",
        "MessageObserver.add_message",
        "MessageObserver.get_cached_message",
        "MessageObserver.get_final_answer",
        "ProcessType",
    ],
    "nexent.scheduler.triggers": [
        "ScheduleMode",
        "ScheduleRuleType",
        "ScheduleSpec",
        "is_valid_cron_expression",
        "compute_next_fire_at",
    ],
    "nexent.scheduler.core": [
        "SchedulerConfig",
        "LeaseScheduler",
        "LeaseScheduler.start",
        "LeaseScheduler.stop",
    ],
    "nexent.skills.skill_manager": [
        "SkillManager",
        "SkillManager.list_skills",
        "SkillManager.load_skill",
        "SkillManager.save_skill",
        "SkillManager.run_skill_script",
    ],
    "nexent.skills.skill_loader": ["SkillLoader", "SkillLoader.load", "SkillLoader.parse"],
    "nexent.monitor.monitoring": [
        "AgentRunMetadata",
        "MonitoringConfig",
        "MonitoringManager",
        "MonitoringManager.configure",
        "MonitoringManager.start_agent_run",
        "MonitoringManager.trace_tool_call",
        "MonitoringManager.trace_retriever_call",
        "get_monitoring_manager",
    ],
}

SOURCE_FILES = [
    "sdk/nexent/core/agents/agent_model.py",
    "sdk/nexent/core/agents/core_agent.py",
    "sdk/nexent/core/agents/nexent_agent.py",
    "sdk/nexent/core/agents/run_agent.py",
    "sdk/nexent/core/agents/a2a_agent_proxy.py",
    "sdk/nexent/core/agents/sandbox.py",
    "sdk/nexent/core/agents/verification.py",
    "sdk/nexent/core/models/openai_llm.py",
    "sdk/nexent/core/tools/__init__.py",
    "sdk/nexent/core/tools/README_EN.md",
    "sdk/nexent/skills/skill_manager.py",
    "sdk/nexent/skills/skill_loader.py",
    "sdk/nexent/scheduler/triggers.py",
    "sdk/nexent/scheduler/core.py",
    "sdk/nexent/monitor/monitoring.py",
    "sdk/ctx_debugger/README.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect Nexent SDK runtime imports, signatures, fields, tool exports, "
            "and static source summaries without starting services or network calls."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a Nexent checkout. Defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of Markdown.",
    )
    return parser.parse_args()


def sanitize(text: Any, repo_root: Path) -> str:
    value = str(text)
    try:
        value = value.replace(str(repo_root.resolve()), "<repo-root>")
    except OSError:
        value = value.replace(str(repo_root), "<repo-root>")
    home = os.path.expanduser("~")
    if home and home != "~":
        value = value.replace(home, "~")
    return value


def configure_path(repo_root: Path) -> None:
    for candidate in (repo_root / "sdk", repo_root, repo_root / "backend"):
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)


def object_by_path(module: Any, dotted: str) -> Any:
    obj = module
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def safe_signature(obj: Any, repo_root: Path) -> str:
    try:
        return sanitize(inspect.signature(obj), repo_root)
    except Exception as exc:  # pragma: no cover - depends on optional deps
        return f"<unavailable: {sanitize(exc, repo_root)}>"


def doc_first_line(obj: Any, repo_root: Path) -> str:
    try:
        doc = inspect.getdoc(obj) or ""
    except Exception as exc:  # pragma: no cover
        return f"<doc unavailable: {sanitize(exc, repo_root)}>"
    return sanitize(doc.splitlines()[0], repo_root) if doc else ""


def fields_for(obj: Any, repo_root: Path) -> list[dict[str, Any]]:
    fields = getattr(obj, "model_fields", None)
    if fields:
        rows = []
        for name, field in fields.items():
            try:
                required = bool(field.is_required())
            except Exception:
                required = None
            default = getattr(field, "default", None)
            default_text = "<required>" if required else sanitize(repr(default), repo_root)
            rows.append(
                {
                    "name": name,
                    "required": required,
                    "default": default_text,
                    "description": sanitize(getattr(field, "description", "") or "", repo_root),
                }
            )
        return rows
    if is_dataclass(obj) or hasattr(obj, "__dataclass_fields__"):
        rows = []
        for name, field in getattr(obj, "__dataclass_fields__", {}).items():
            rows.append({"name": name, "default": sanitize(repr(field.default), repo_root)})
        return rows
    return []


def enum_values(obj: Any) -> list[Any]:
    try:
        return [item.value for item in obj]  # EnumMeta
    except Exception:
        return []


def public_methods(obj: Any, repo_root: Path, limit: int = 20) -> list[dict[str, str]]:
    if not inspect.isclass(obj):
        return []
    rows = []
    for name, member in inspect.getmembers(obj):
        if name.startswith("_"):
            continue
        if not callable(member):
            continue
        try:
            # Skip inherited object helpers that do not help runtime diagnosis.
            if getattr(member, "__qualname__", "").startswith("object."):
                continue
        except Exception:
            pass
        rows.append({"name": name, "signature": safe_signature(member, repo_root)})
        if len(rows) >= limit:
            break
    return rows


def inspect_imports(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    imports: dict[str, Any] = {}
    targets: dict[str, Any] = {}
    for module_name, names in MODULE_TARGETS.items():
        try:
            module = importlib.import_module(module_name)
            imports[module_name] = {"ok": True}
        except Exception as exc:
            imports[module_name] = {"ok": False, "error": sanitize(f"{type(exc).__name__}: {exc}", repo_root)}
            continue
        for dotted in names:
            key = f"{module_name}.{dotted}"
            try:
                obj = object_by_path(module, dotted)
                targets[key] = {
                    "ok": True,
                    "kind": "class" if inspect.isclass(obj) else "function" if callable(obj) else type(obj).__name__,
                    "signature": safe_signature(obj, repo_root) if callable(obj) or inspect.isclass(obj) else "",
                    "doc": doc_first_line(obj, repo_root),
                    "fields": fields_for(obj, repo_root),
                    "enum_values": enum_values(obj),
                    "public_methods": public_methods(obj, repo_root),
                }
            except Exception as exc:
                targets[key] = {"ok": False, "error": sanitize(f"{type(exc).__name__}: {exc}", repo_root)}
    return imports, targets


def ast_summary(path: Path, repo_root: Path) -> dict[str, Any]:
    rel = sanitize(path, repo_root)
    if not path.exists():
        return {"path": rel, "exists": False}
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except Exception as exc:
        return {"path": rel, "exists": True, "error": sanitize(f"{type(exc).__name__}: {exc}", repo_root)}

    classes = []
    functions = []
    exports = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "doc": (ast.get_docstring(node) or "").splitlines()[0] if ast.get_docstring(node) else "",
                    "methods": [
                        item.name
                        for item in node.body
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_")
                    ][:20],
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "doc": (ast.get_docstring(node) or "").splitlines()[0] if ast.get_docstring(node) else "",
                }
            )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    try:
                        exports = ast.literal_eval(node.value)
                    except Exception:
                        exports = "<unparseable>"
    return {
        "path": rel,
        "exists": True,
        "classes": classes,
        "functions": functions,
        "__all__": exports,
    }


def source_summaries(repo_root: Path) -> dict[str, Any]:
    return {item: ast_summary(repo_root / item, repo_root) for item in SOURCE_FILES}


def mcp_examples(repo_root: Path) -> list[dict[str, Any]]:
    try:
        module = importlib.import_module("nexent.core.agents.run_agent")
        normalize = getattr(module, "_normalize_mcp_config")
    except Exception as exc:
        return [{"ok": False, "error": sanitize(f"{type(exc).__name__}: {exc}", repo_root)}]
    examples: list[Any] = [
        "http://mcp.example/sse",
        "http://mcp.example/mcp",
        "http://mcp.example/base/",
        {"url": "http://mcp.example/sse", "authorization": "Bearer token"},
        {"url": "http://mcp.example/mcp", "headers": {"X-Test": "1"}, "authorization": "Bearer token"},
    ]
    rows = []
    for item in examples:
        try:
            rows.append({"input": item, "ok": True, "normalized": normalize(item)})
        except Exception as exc:
            rows.append({"input": item, "ok": False, "error": sanitize(f"{type(exc).__name__}: {exc}", repo_root)})
    return rows


def build_report(repo_root: Path) -> dict[str, Any]:
    configure_path(repo_root)
    imports, targets = inspect_imports(repo_root)
    return {
        "schema_version": 1,
        "repo_root": sanitize(repo_root.resolve(), repo_root),
        "python": {
            "version": sys.version.split()[0],
            "executable": sanitize(sys.executable, repo_root),
        },
        "safety": {
            "network_calls": False,
            "service_startup": False,
            "agent_run_execution": False,
            "native_tests_run": False,
        },
        "imports": imports,
        "targets": targets,
        "mcp_normalization_examples": mcp_examples(repo_root),
        "source_summaries": source_summaries(repo_root),
    }


def print_markdown(report: dict[str, Any]) -> None:
    print("# Nexent SDK Runtime Inspection")
    print()
    print(f"- Repo root: `{report['repo_root']}`")
    print(f"- Python: `{report['python']['version']}` (`{report['python']['executable']}`)")
    print("- Safety: no network calls, no service startup, no agent execution, no native tests")
    print()

    print("## Imports")
    for module_name, result in sorted(report["imports"].items()):
        if result.get("ok"):
            print(f"- ✅ `{module_name}`")
        else:
            print(f"- ❌ `{module_name}`: {result.get('error')}")
    print()

    print("## Signatures and fields")
    for name, result in sorted(report["targets"].items()):
        if not result.get("ok"):
            print(f"### `{name}`")
            print(f"- Error: {result.get('error')}")
            print()
            continue
        print(f"### `{name}`")
        if result.get("signature"):
            print(f"```text\n{result['signature']}\n```")
        if result.get("doc"):
            print(f"- Doc: {result['doc']}")
        if result.get("enum_values"):
            print(f"- Values: {', '.join(map(str, result['enum_values']))}")
        fields = result.get("fields") or []
        if fields:
            print("- Fields:")
            for field in fields:
                details = []
                if "required" in field and field["required"] is not None:
                    details.append("required" if field["required"] else f"default={field.get('default')}")
                elif "default" in field:
                    details.append(f"default={field.get('default')}")
                if field.get("description"):
                    details.append(field["description"])
                print(f"  - `{field['name']}`: {'; '.join(details)}")
        methods = result.get("public_methods") or []
        if methods:
            print("- Public methods (sample):")
            for method in methods[:8]:
                print(f"  - `{method['name']}` `{method['signature']}`")
        print()

    print("## MCP normalization examples")
    for row in report["mcp_normalization_examples"]:
        if row.get("ok"):
            print(f"- `{row['input']}` -> `{row['normalized']}`")
        else:
            print(f"- `{row.get('input')}` -> ERROR {row.get('error')}")
    print()

    print("## Static source summaries")
    for rel, summary in sorted(report["source_summaries"].items()):
        if not summary.get("exists"):
            print(f"- ❌ `{rel}` missing")
            continue
        if summary.get("error"):
            print(f"- ❌ `{rel}` parse error: {summary['error']}")
            continue
        classes = ", ".join(cls["name"] for cls in summary.get("classes", [])[:10])
        funcs = ", ".join(fn["name"] for fn in summary.get("functions", [])[:10])
        exports = summary.get("__all__")
        print(f"- ✅ `{rel}`")
        if classes:
            print(f"  - Classes: {classes}")
        if funcs:
            print(f"  - Functions: {funcs}")
        if exports:
            print(f"  - `__all__`: {exports}")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
