#!/usr/bin/env python3
"""Safely inspect AutoGen extension import/spec availability.

This script performs importlib metadata/spec checks and selected module imports only.
It does not call model providers, start Docker/Jupyter/MCP/browser processes,
connect to Redis/ChromaDB/mem0, bind gRPC ports, or start Azure resources.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModuleCheck:
    module: str
    extra: str | None
    surface: str
    note: str
    import_module: bool = False


PACKAGE_NAMES = [
    "autogen-core",
    "autogen-agentchat",
    "autogen-ext",
    "pyautogen",
    "agbench",
]

DEPENDENCY_SPECS = {
    "openai": ["openai", "tiktoken", "aiofiles"],
    "anthropic": ["anthropic"],
    "azure": ["azure.ai.inference", "azure.ai.projects", "azure.core", "azure.identity", "azure.search.documents"],
    "ollama": ["ollama", "tiktoken"],
    "llama-cpp": ["llama_cpp"],
    "gemini": ["google.genai"],
    "semantic-kernel-core": ["semantic_kernel"],
    "mcp": ["mcp"],
    "http-tool": ["httpx", "json_schema_to_pydantic"],
    "langchain": ["langchain_core"],
    "graphrag": ["graphrag"],
    "docker": ["docker", "asyncio_atexit"],
    "jupyter-executor": ["ipykernel", "nbclient"],
    "docker-jupyter-executor": ["docker", "websockets", "requests", "aiohttp"],
    "diskcache": ["diskcache"],
    "redis": ["redis"],
    "redisvl": ["redisvl"],
    "chromadb": ["chromadb"],
    "mem0": ["mem0"],
    "mem0-local": ["mem0", "neo4j", "chromadb"],
    "canvas": ["unidiff"],
    "grpc": ["grpc"],
    "web-surfer": ["playwright", "PIL", "magika", "markitdown"],
    "file-surfer": ["magika", "markitdown"],
    "video-surfer": ["cv2", "ffmpeg", "whisper"],
    "rich": ["rich"],
}

MODULE_CHECKS = [
    ModuleCheck("autogen_ext", None, "base package", "Base extension package", True),
    ModuleCheck("autogen_ext.models.openai", "openai", "model client", "OpenAI and Azure OpenAI clients", True),
    ModuleCheck("autogen_ext.models.azure", "azure", "model client", "Azure AI Inference/GitHub Models client", True),
    ModuleCheck("autogen_ext.models.anthropic", "anthropic", "model client", "Anthropic direct and Bedrock clients", False),
    ModuleCheck("autogen_ext.models.ollama", "ollama", "model client", "Ollama model client", False),
    ModuleCheck("autogen_ext.models.llama_cpp", "llama-cpp", "model client", "llama.cpp model client", False),
    ModuleCheck("autogen_ext.models.semantic_kernel", "semantic-kernel-core", "model client", "Semantic Kernel adapter", False),
    ModuleCheck("autogen_ext.models.replay", None, "model client", "Replay client", True),
    ModuleCheck("autogen_ext.models.cache", None, "cache wrapper", "ChatCompletionCache wrapper", True),
    ModuleCheck("autogen_ext.cache_store.diskcache", "diskcache", "cache store", "Disk cache store", False),
    ModuleCheck("autogen_ext.cache_store.redis", "redis", "cache store", "Redis cache store", False),
    ModuleCheck("autogen_ext.tools.mcp", "mcp", "tools/workbench", "MCP tools, workbench, and host", False),
    ModuleCheck("autogen_ext.tools.http", "http-tool", "tool", "HTTP tool", False),
    ModuleCheck("autogen_ext.tools.langchain", "langchain", "tool adapter", "LangChain tool adapter", False),
    ModuleCheck("autogen_ext.tools.azure", "azure", "tool", "Azure AI Search tool", False),
    ModuleCheck("autogen_ext.tools.graphrag", "graphrag", "tool", "GraphRAG search tools", False),
    ModuleCheck("autogen_ext.tools.semantic_kernel", "semantic-kernel-core", "tool adapter", "Semantic Kernel function adapter", False),
    ModuleCheck("autogen_ext.tools.code_execution", None, "tool", "Code execution tool wrapper", True),
    ModuleCheck("autogen_ext.code_executors.local", None, "code executor", "Local command-line executor", True),
    ModuleCheck("autogen_ext.code_executors.docker", "docker", "code executor", "Docker command-line executor", False),
    ModuleCheck("autogen_ext.code_executors.jupyter", "jupyter-executor", "code executor", "Local Jupyter executor", False),
    ModuleCheck("autogen_ext.code_executors.docker_jupyter", "docker-jupyter-executor", "code executor", "Docker Jupyter gateway executor", False),
    ModuleCheck("autogen_ext.code_executors.azure", "azure", "code executor", "Azure Container Apps Dynamic Sessions executor", False),
    ModuleCheck("autogen_ext.memory.chromadb", "chromadb", "memory", "ChromaDB vector memory", False),
    ModuleCheck("autogen_ext.memory.redis", "redis", "memory", "Redis memory", False),
    ModuleCheck("autogen_ext.memory.mem0", "mem0", "memory", "mem0 memory", False),
    ModuleCheck("autogen_ext.memory.canvas", "canvas", "memory", "Canvas memory", False),
    ModuleCheck("autogen_ext.experimental.task_centric_memory", "task-centric-memory", "memory", "Experimental task-centric memory", False),
    ModuleCheck("autogen_ext.agents.web_surfer", "web-surfer", "agent helper", "Multimodal web surfer", False),
    ModuleCheck("autogen_ext.agents.file_surfer", "file-surfer", "agent helper", "File surfer", False),
    ModuleCheck("autogen_ext.agents.video_surfer", "video-surfer", "agent helper", "Video surfer", False),
    ModuleCheck("autogen_ext.agents.magentic_one", "magentic-one", "agent helper", "Magentic-One helper agent", False),
    ModuleCheck("autogen_ext.agents.azure", "azure", "agent helper", "Azure AI agent", False),
    ModuleCheck("autogen_ext.agents.openai", "openai", "agent helper", "OpenAI assistant/agent wrappers", False),
    ModuleCheck("autogen_ext.runtimes.grpc", "grpc", "runtime", "gRPC worker runtime surfaces", False),
    ModuleCheck("autogen_ext.ui", "rich", "ui", "Rich console helper", False),
]

PUBLIC_SYMBOLS = {
    "autogen_ext.models.openai": ["OpenAIChatCompletionClient", "AzureOpenAIChatCompletionClient"],
    "autogen_ext.models.azure": ["AzureAIChatCompletionClient"],
    "autogen_ext.models.anthropic": ["AnthropicChatCompletionClient", "AnthropicBedrockChatCompletionClient"],
    "autogen_ext.models.ollama": ["OllamaChatCompletionClient"],
    "autogen_ext.models.llama_cpp": ["LlamaCppChatCompletionClient"],
    "autogen_ext.models.semantic_kernel": ["SKChatCompletionAdapter"],
    "autogen_ext.models.replay": ["ReplayChatCompletionClient"],
    "autogen_ext.models.cache": ["ChatCompletionCache"],
    "autogen_ext.cache_store.diskcache": ["DiskCacheStore"],
    "autogen_ext.cache_store.redis": ["RedisStore"],
    "autogen_ext.tools.mcp": ["McpWorkbench", "StdioServerParams", "SseServerParams", "StreamableHttpServerParams", "mcp_server_tools"],
    "autogen_ext.tools.http": ["HttpTool"],
    "autogen_ext.tools.langchain": ["LangChainToolAdapter"],
    "autogen_ext.tools.azure": ["AzureAISearchTool"],
    "autogen_ext.tools.graphrag": ["GlobalSearchTool", "LocalSearchTool"],
    "autogen_ext.tools.semantic_kernel": ["KernelFunctionFromTool"],
    "autogen_ext.tools.code_execution": ["PythonCodeExecutionTool"],
    "autogen_ext.code_executors.local": ["LocalCommandLineCodeExecutor"],
    "autogen_ext.code_executors.docker": ["DockerCommandLineCodeExecutor"],
    "autogen_ext.code_executors.jupyter": ["JupyterCodeExecutor"],
    "autogen_ext.code_executors.docker_jupyter": ["DockerJupyterServer", "DockerJupyterCodeExecutor"],
    "autogen_ext.code_executors.azure": ["ACADynamicSessionsCodeExecutor"],
    "autogen_ext.memory.chromadb": ["ChromaDBVectorMemory"],
    "autogen_ext.memory.redis": ["RedisMemory"],
    "autogen_ext.memory.mem0": ["Mem0Memory"],
    "autogen_ext.memory.canvas": ["TextCanvas", "TextCanvasMemory"],
    "autogen_ext.experimental.task_centric_memory": ["MemoryController"],
    "autogen_ext.agents.web_surfer": ["MultimodalWebSurfer"],
    "autogen_ext.agents.file_surfer": ["FileSurfer"],
    "autogen_ext.agents.video_surfer": ["VideoSurfer"],
    "autogen_ext.agents.magentic_one": ["MagenticOneCoderAgent"],
    "autogen_ext.agents.azure": ["AzureAIAgent"],
    "autogen_ext.agents.openai": ["OpenAIAgent", "OpenAIAssistantAgent"],
    "autogen_ext.runtimes.grpc": ["GrpcWorkerAgentRuntime", "GrpcWorkerAgentRuntimeHost"],
    "autogen_ext.ui": ["RichConsole"],
}


def package_version(package_name: str) -> dict[str, Any]:
    try:
        version = importlib.metadata.version(package_name)
        return {"name": package_name, "installed": True, "version": version}
    except importlib.metadata.PackageNotFoundError:
        return {"name": package_name, "installed": False, "version": None}


def spec_status(module_name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(module_name)
        return {"module": module_name, "available": spec is not None, "error": None}
    except Exception as exc:  # importlib can execute parent packages for dotted names.
        return {"module": module_name, "available": False, "error": f"{type(exc).__name__}: {exc}"}


def module_status(check: ModuleCheck, include_imports: bool) -> dict[str, Any]:
    status: dict[str, Any] = {
        "module": check.module,
        "surface": check.surface,
        "extra": check.extra,
        "note": check.note,
        "spec_available": False,
        "import_attempted": False,
        "import_ok": None,
        "error": None,
        "symbols": {},
    }
    spec = spec_status(check.module)
    status["spec_available"] = spec["available"]
    if spec["error"]:
        status["error"] = spec["error"]

    if include_imports or check.import_module:
        status["import_attempted"] = True
        try:
            module = importlib.import_module(check.module)
            status["import_ok"] = True
            symbols = PUBLIC_SYMBOLS.get(check.module, [])
            status["symbols"] = {symbol: hasattr(module, symbol) for symbol in symbols}
        except Exception as exc:
            status["import_ok"] = False
            status["error"] = f"{type(exc).__name__}: {exc}"

    return status


def build_report(include_imports: bool) -> dict[str, Any]:
    modules = [module_status(check, include_imports=include_imports) for check in MODULE_CHECKS]
    dependency_specs = {
        extra: [spec_status(module_name) for module_name in module_names]
        for extra, module_names in DEPENDENCY_SPECS.items()
    }
    missing_extras = sorted(
        {
            item["extra"]
            for item in modules
            if item["extra"] and (not item["spec_available"] or item.get("import_ok") is False)
        }
    )
    return {
        "script": "inspect_extensions.py",
        "safe_mode": {
            "provider_calls": False,
            "docker_ping_or_start": False,
            "jupyter_kernel_start": False,
            "mcp_server_start": False,
            "browser_start": False,
            "external_service_connections": False,
        },
        "python": {
            "version": sys.version.split()[0],
            "executable_basename": sys.executable.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
            "platform": platform.platform(),
        },
        "packages": [package_version(package_name) for package_name in PACKAGE_NAMES],
        "dependency_specs": dependency_specs,
        "modules": modules,
        "missing_or_failing_extras": missing_extras,
        "next_steps": [
            "Install only the exact extras required by the failing surface.",
            "Treat import success as package availability, not provider credential or service readiness.",
            "Review MCP, Docker, Jupyter, browser, Redis, ChromaDB, mem0, Azure, and gRPC service lifecycles before execution.",
        ],
    }


def print_text_report(report: dict[str, Any]) -> None:
    print("AutoGen extension inspection (safe import/spec only)")
    print(f"Python: {report['python']['version']} on {report['python']['platform']}")
    print("\nPackages:")
    for package in report["packages"]:
        version = package["version"] if package["installed"] else "not installed"
        print(f"  - {package['name']}: {version}")
    print("\nModules:")
    for item in report["modules"]:
        if item["import_attempted"]:
            state = "ok" if item["import_ok"] else "failed"
        else:
            state = "spec found" if item["spec_available"] else "missing"
        extra = f" [{item['extra']}]" if item["extra"] else ""
        print(f"  - {item['module']}{extra}: {state}")
        if item["error"]:
            print(f"      error: {item['error']}")
        if item["symbols"]:
            missing_symbols = [name for name, ok in item["symbols"].items() if not ok]
            if missing_symbols:
                print(f"      missing symbols: {', '.join(missing_symbols)}")
    if report["missing_or_failing_extras"]:
        print("\nMissing/failing extras to consider:")
        for extra in report["missing_or_failing_extras"]:
            print(f"  - {extra}")
    print("\nNo provider calls, Docker/Jupyter/MCP/browser starts, or external service connections were attempted.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect AutoGen extension package/module availability.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--imports",
        action="store_true",
        help="Attempt imports for all listed autogen_ext modules. Still no provider/service calls or starts.",
    )
    args = parser.parse_args()

    report = build_report(include_imports=args.imports)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
