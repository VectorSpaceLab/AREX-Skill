#!/usr/bin/env python3
"""Credential-free smoke checks for mcp-agent core SDK usage."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import sys
from collections.abc import Callable
from typing import Any


PROVIDER_MODULES: dict[str, tuple[str, str, str]] = {
    "openai": (
        "mcp_agent.workflows.llm.augmented_llm_openai",
        "OpenAIAugmentedLLM",
        "openai.api_key",
    ),
    "anthropic": (
        "mcp_agent.workflows.llm.augmented_llm_anthropic",
        "AnthropicAugmentedLLM",
        "anthropic.api_key",
    ),
    "azure": (
        "mcp_agent.workflows.llm.augmented_llm_azure",
        "AzureAugmentedLLM",
        "azure.api_key",
    ),
    "google": (
        "mcp_agent.workflows.llm.augmented_llm_google",
        "GoogleAugmentedLLM",
        "google.api_key",
    ),
    "bedrock": (
        "mcp_agent.workflows.llm.augmented_llm_bedrock",
        "BedrockAugmentedLLM",
        "bedrock.aws_access_key_id",
    ),
    "ollama": (
        "mcp_agent.workflows.llm.augmented_llm_ollama",
        "OllamaAugmentedLLM",
        "openai.base_url",
    ),
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe, local-only mcp-agent core SDK smoke checks. "
            "The checker imports APIs and constructs objects, but does not call LLM providers, "
            "spawn MCP servers, read project config files, or require credentials."
        )
    )
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDER_MODULES),
        action="append",
        default=[],
        help="Optionally check provider wrapper import and settings shape. Can be repeated.",
    )
    parser.add_argument(
        "--max-tokens",
        type=positive_int,
        default=128,
        help="maxTokens value to validate in RequestParams. Default: 128.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    return parser


def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def echo_text(text: str) -> str:
    """Echo text locally."""
    return text


def check_signature(name: str, obj: Callable[..., Any], expected: set[str]) -> dict[str, Any]:
    signature = inspect.signature(obj)
    parameters = set(signature.parameters)
    missing = sorted(expected - parameters)
    return {
        "name": name,
        "signature": str(signature),
        "ok": not missing,
        "missing": missing,
    }


def dotted_getattr(obj: Any, dotted_path: str) -> Any:
    current = obj
    for part in dotted_path.split("."):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


async def run_core_checks(max_tokens: int) -> dict[str, Any]:
    from mcp_agent.agents.agent import Agent
    from mcp_agent.agents.agent_spec import AgentSpec
    from mcp_agent.app import MCPApp
    from mcp_agent.config import LoggerSettings, MCPSettings, Settings
    from mcp_agent.core.context import Context
    from mcp_agent.workflows.factory import agent_from_spec, create_agent, load_agent_specs_from_text
    from mcp_agent.workflows.llm.augmented_llm import RequestParams

    settings = Settings(
        execution_engine="asyncio",
        logger=LoggerSettings(transports=["console"], level="warning"),
        mcp=MCPSettings(servers={}),
    )
    app = MCPApp(name="core_sdk_smoke", settings=settings)

    @app.tool(description="Echo text locally for schema validation.")
    def local_echo(text: str) -> str:
        """Echo text without external services."""
        return text

    @app.async_tool(name="local_async_echo")
    async def local_async_echo(text: str, app_ctx: Context | None = None) -> str:
        """Echo text from an async decorator path."""
        _ = app_ctx
        return text

    request_params = RequestParams(
        model="gpt-4o-mini",
        maxTokens=max_tokens,
        temperature=0.0,
        max_iterations=1,
        use_history=False,
        tool_filter={"non_namespaced_tools": {"add_numbers", "echo_text"}},
        reasoning_effort="none",
    )

    spec = AgentSpec(
        name="local_math",
        instruction="Use local functions only.",
        server_names=[],
        connection_persistence=False,
    )

    loaded_specs = load_agent_specs_from_text(
        """
agents:
  - name: loaded_local
    instruction: Loaded from YAML text.
    server_names: []
""",
        fmt="yaml",
    )

    async with app.run() as running_app:
        agent = Agent(
            name="local_agent",
            instruction="Use only local tools.",
            functions=[add_numbers, echo_text],
            server_names=[],
            context=running_app.context,
            connection_persistence=False,
        )
        converted_agent = agent_from_spec(spec, context=running_app.context)
        created_agent = create_agent(spec, context=running_app.context)

        return {
            "imports": True,
            "app": {
                "name": running_app.name,
                "execution_engine": running_app.config.execution_engine,
                "initialized": True,
                "declared_tools": sorted(tool["name"] for tool in running_app._declared_tools),
                "workflow_count": len(running_app.workflows),
            },
            "agent": {
                "name": agent.name,
                "function_tools": sorted(agent._function_tool_map),
                "server_names": agent.server_names,
                "connection_persistence": agent.connection_persistence,
            },
            "agent_spec": {
                "name": spec.name,
                "converted_agent": converted_agent.name,
                "created_agent": created_agent.name,
                "loaded_specs": [loaded.name for loaded in loaded_specs],
            },
            "request_params": {
                "model": request_params.model,
                "maxTokens": request_params.maxTokens,
                "temperature": request_params.temperature,
                "max_iterations": request_params.max_iterations,
                "use_history": request_params.use_history,
                "tool_filter": {
                    key: sorted(value) for key, value in (request_params.tool_filter or {}).items()
                },
                "reasoning_effort": request_params.reasoning_effort,
            },
        }


def run_signature_checks() -> list[dict[str, Any]]:
    from mcp_agent.agents.agent import Agent
    from mcp_agent.agents.agent_spec import AgentSpec
    from mcp_agent.app import MCPApp
    from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM, RequestParams

    return [
        check_signature(
            "MCPApp",
            MCPApp,
            {
                "name",
                "description",
                "settings",
                "mcp",
                "human_input_callback",
                "elicitation_callback",
                "signal_notification",
                "upstream_session",
                "model_selector",
                "icons",
                "session_id",
            },
        ),
        check_signature(
            "Agent",
            Agent,
            {
                "name",
                "instruction",
                "server_names",
                "functions",
                "context",
                "connection_persistence",
                "human_input_callback",
                "llm",
                "initialized",
            },
        ),
        check_signature(
            "AgentSpec",
            AgentSpec,
            {"name", "instruction", "server_names", "connection_persistence"},
        ),
        check_signature(
            "AugmentedLLM",
            AugmentedLLM,
            {
                "agent",
                "server_names",
                "instruction",
                "name",
                "default_request_params",
                "type_converter",
                "context",
            },
        ),
        check_signature(
            "RequestParams",
            RequestParams,
            {
                "modelPreferences",
                "systemPrompt",
                "includeContext",
                "temperature",
                "maxTokens",
                "stopSequences",
                "tools",
                "toolChoice",
                "model",
                "use_history",
                "max_iterations",
                "parallel_tool_calls",
                "user",
                "strict",
                "tool_filter",
                "reasoning_effort",
            },
        ),
    ]


def check_provider(provider: str) -> dict[str, Any]:
    from mcp_agent.config import Settings

    module_name, class_name, credential_path = PROVIDER_MODULES[provider]
    result: dict[str, Any] = {
        "provider": provider,
        "module": module_name,
        "class": class_name,
        "credential_path": credential_path,
        "import_ok": False,
        "settings_field_present": False,
        "credential_present": False,
    }
    try:
        module = importlib.import_module(module_name)
        getattr(module, class_name)
        result["import_ok"] = True
    except Exception as exc:  # noqa: BLE001 - report exact provider import failure safely.
        result["error"] = f"{exc.__class__.__name__}: {exc}"
        return result

    settings = Settings()
    settings_root = credential_path.split(".", 1)[0]
    result["settings_field_present"] = getattr(settings, settings_root, None) is not None
    credential_value = dotted_getattr(settings, credential_path)
    result["credential_present"] = bool(credential_value)
    return result


def validate_report(report: dict[str, Any]) -> int:
    failures: list[str] = []
    for item in report["signatures"]:
        if not item["ok"]:
            failures.append(f"{item['name']} missing parameters: {', '.join(item['missing'])}")

    core = report["core"]
    if not core.get("imports"):
        failures.append("core imports failed")
    if "local_echo" not in core["app"]["declared_tools"]:
        failures.append("@app.tool did not register local_echo")
    if "local_async_echo" not in core["app"]["declared_tools"]:
        failures.append("@app.async_tool did not register local_async_echo")
    if sorted(core["agent"]["function_tools"]) != ["add_numbers", "echo_text"]:
        failures.append("Agent did not convert local functions into tools")
    if core["request_params"]["maxTokens"] < 1:
        failures.append("RequestParams maxTokens must be positive")

    for provider in report.get("providers", []):
        if not provider["import_ok"]:
            failures.append(f"provider {provider['provider']} import failed")
        if not provider["settings_field_present"]:
            failures.append(f"provider {provider['provider']} settings field missing")

    report["ok"] = not failures
    report["failures"] = failures
    return 0 if not failures else 1


def print_text_report(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAIL"
    print(f"core-sdk smoke check: {status}")
    print(f"app: {report['core']['app']['name']} ({report['core']['app']['execution_engine']})")
    print("declared tools:", ", ".join(report["core"]["app"]["declared_tools"]) or "none")
    print("agent function tools:", ", ".join(report["core"]["agent"]["function_tools"]) or "none")
    print("loaded specs:", ", ".join(report["core"]["agent_spec"]["loaded_specs"]) or "none")
    print("request model:", report["core"]["request_params"]["model"])

    print("signatures:")
    for item in report["signatures"]:
        marker = "ok" if item["ok"] else "missing " + ", ".join(item["missing"])
        print(f"  - {item['name']}: {marker} {item['signature']}")

    if report.get("providers"):
        print("providers:")
        for provider in report["providers"]:
            credential = "credential present" if provider["credential_present"] else "credential not present"
            import_status = "import ok" if provider["import_ok"] else provider.get("error", "import failed")
            print(f"  - {provider['provider']}: {import_status}; {credential}")

    if report["failures"]:
        print("failures:")
        for failure in report["failures"]:
            print(f"  - {failure}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report: dict[str, Any] = {
            "core": asyncio.run(run_core_checks(args.max_tokens)),
            "signatures": run_signature_checks(),
            "providers": [check_provider(provider) for provider in args.provider],
        }
        exit_code = validate_report(report)
    except Exception as exc:  # noqa: BLE001 - top-level smoke checker should report safely.
        report = {
            "ok": False,
            "failures": [f"{exc.__class__.__name__}: {exc}"],
        }
        exit_code = 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
