#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: python-core-check.sh [--pytest]

Run import and signature checks for the Strands Python SDK using python from PATH.

With --pytest, run a small selected pytest subset when this command is executed
from a Strands Agents checkout that has test dependencies installed.
EOF
}

run_pytest=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --pytest)
      run_pytest=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

python_bin="python"
if ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "python is not available on PATH" >&2
  exit 2
fi

"$python_bin" - <<'PY'
from __future__ import annotations

import inspect

try:
    import strands
    from strands import Agent, tool
    from strands.agent.conversation_manager import SlidingWindowConversationManager, SummarizingConversationManager
    from strands.memory import MemoryManager
    from strands.models import BedrockModel, Model
    from strands.multiagent import GraphBuilder, Swarm
    from strands.sandbox import PosixShellSandbox, Sandbox
    from strands.session import FileSessionManager, S3SessionManager, SnapshotSessionManager
    from strands.telemetry import EventLoopMetrics, StrandsTelemetry, Tracer
    from strands.tools.mcp import MCPClient, TasksConfig
except ModuleNotFoundError as error:
    missing = error.name or str(error)
    raise SystemExit(
        f"unable to import the Strands Python SDK; install the checkout dependencies and retry (missing: {missing})"
    ) from error


def param_names(callable_obj: object) -> list[str]:
    return [name for name in inspect.signature(callable_obj).parameters if name not in {"self", "cls"}]


def require_exact(name: str, actual: list[str], expected: list[str]) -> None:
    if actual != expected:
        raise AssertionError(f"{name} signature mismatch: expected {expected!r}, got {actual!r}")


def require_contains(name: str, actual: list[str], expected: list[str]) -> None:
    missing = [item for item in expected if item not in actual]
    if missing:
        raise AssertionError(f"{name} missing items: {missing!r}")


# Import sanity.
assert Agent is not None
assert tool is not None
assert BedrockModel is not None
assert Model is not None
assert MCPClient is not None
assert TasksConfig is not None
assert MemoryManager is not None
assert FileSessionManager is not None
assert S3SessionManager is not None
assert SnapshotSessionManager is not None
assert GraphBuilder is not None
assert Swarm is not None
assert Sandbox is not None
assert PosixShellSandbox is not None
assert StrandsTelemetry is not None
assert Tracer is not None
assert EventLoopMetrics is not None

# Top-level exports.
require_contains(
    "strands.__all__",
    list(getattr(strands, "__all__", [])),
    ["Agent", "tool", "Sandbox", "Snapshot", "telemetry"],
)

# Agent signatures.
require_exact(
    "Agent.__init__",
    param_names(Agent.__init__),
    [
        "model",
        "messages",
        "tools",
        "system_prompt",
        "structured_output_model",
        "callback_handler",
        "conversation_manager",
        "record_direct_tool_call",
        "load_tools_from_directory",
        "trace_attributes",
        "agent_id",
        "name",
        "description",
        "state",
        "context_manager",
        "plugins",
        "hooks",
        "interventions",
        "session_manager",
        "memory_manager",
        "structured_output_prompt",
        "tool_executor",
        "retry_strategy",
        "concurrent_invocation_mode",
        "checkpointing",
        "sandbox",
    ],
)
for surface in (Agent.__call__, Agent.invoke_async, Agent.stream_async):
    names = param_names(surface)
    require_exact(
        surface.__qualname__,
        names,
        [
            "prompt",
            "invocation_state",
            "structured_output_model",
            "structured_output_prompt",
            "idempotency_token",
            "limits",
            "kwargs",
        ],
    )
    signature = inspect.signature(surface)
    for name in ["invocation_state", "structured_output_model", "structured_output_prompt", "idempotency_token", "limits"]:
        assert signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["kwargs"].kind is inspect.Parameter.VAR_KEYWORD

require_exact("Agent.structured_output", param_names(Agent.structured_output), ["output_model", "prompt"])
require_exact("Agent.as_tool", param_names(Agent.as_tool), ["name", "description", "preserve_context"])

# Tool decorator contract.
require_exact("tool", param_names(tool), ["func", "description", "inputSchema", "name", "context"])

@tool
def _echo(text: str) -> str:
    """Echo text."""
    return text

assert _echo.tool_name == "_echo"
assert _echo.tool_spec["name"] == "_echo"
assert _echo.tool_spec["inputSchema"]["json"]["properties"]["text"]["type"] == "string"

# Conversation managers.
sliding = inspect.signature(SlidingWindowConversationManager)
assert sliding.parameters["window_size"].default == 40
assert sliding.parameters["should_truncate_results"].default is True
assert sliding.parameters["per_turn"].default is False
assert sliding.parameters["pin_first"].default is None
assert sliding.parameters["proactive_compression"].default is None

summary = inspect.signature(SummarizingConversationManager)
assert summary.parameters["summary_ratio"].default == 0.3
assert summary.parameters["preserve_recent_messages"].default == 10
assert summary.parameters["summarization_agent"].default is None
assert summary.parameters["summarization_system_prompt"].default is None
assert summary.parameters["pin_first"].default is None
assert summary.parameters["proactive_compression"].default is None

# Memory, sessions, multi-agent, sandbox, telemetry.
require_exact("MemoryManager", param_names(MemoryManager), ["stores", "search_tool_config", "add_tool_config", "injection"])
require_exact("FileSessionManager", param_names(FileSessionManager), ["session_id", "storage_dir", "kwargs"])
require_exact(
    "S3SessionManager",
    param_names(S3SessionManager),
    ["session_id", "bucket", "prefix", "boto_session", "boto_client_config", "region_name", "endpoint_url", "kwargs"],
)
require_exact(
    "SnapshotSessionManager",
    param_names(SnapshotSessionManager),
    ["session_id", "storage", "save_latest_on", "snapshot_trigger", "kwargs"],
)
require_exact("GraphBuilder", param_names(GraphBuilder), [])
require_exact(
    "Swarm",
    param_names(Swarm),
    [
        "nodes",
        "entry_point",
        "max_handoffs",
        "max_iterations",
        "execution_timeout",
        "node_timeout",
        "repetitive_handoff_detection_window",
        "repetitive_handoff_min_unique_agents",
        "session_manager",
        "hooks",
        "id",
        "trace_attributes",
        "plugins",
    ],
)
require_exact("StrandsTelemetry", param_names(StrandsTelemetry), ["tracer_provider"])
require_exact("Tracer", param_names(Tracer), [])
require_contains(
    "EventLoopMetrics",
    param_names(EventLoopMetrics),
    ["cycle_count", "tool_metrics", "cycle_durations", "agent_invocations", "traces", "accumulated_usage", "accumulated_metrics"],
)
require_exact("MCPClient.load_servers", param_names(MCPClient.load_servers), ["config"])
require_exact(
    "MCPClient",
    param_names(MCPClient),
    [
        "transport_callable",
        "startup_timeout",
        "tool_filters",
        "prefix",
        "application_name",
        "application_version",
        "continue_on_error",
        "elicitation_callback",
        "progress_callback",
        "tasks_config",
    ],
)

# MCPClient and task configuration classes stay importable.
assert TasksConfig is not None

print("python-sdk import and signature checks passed")
PY

if [ "$run_pytest" -eq 1 ]; then
  repo_root=""
  search_dir="$PWD"
  while [ "$search_dir" != "/" ]; do
    if [ -f "$search_dir/strands-py/pyproject.toml" ] && [ -d "$search_dir/strands-py/tests" ]; then
      repo_root="$search_dir"
      break
    fi
    search_dir=$(dirname "$search_dir")
  done

  if [ -z "$repo_root" ]; then
    echo "--pytest requires a Strands Agents checkout with strands-py/tests" >&2
    exit 2
  fi

  if ! "$python_bin" -c 'import pytest' >/dev/null 2>&1; then
    echo "pytest is not installed in this environment" >&2
    exit 2
  fi

  cd "$repo_root/strands-py"
  "$python_bin" -m pytest -q \
    tests/strands/tools/test_decorator.py::test_tool_spec \
    tests/strands/tools/test_decorator.py::test_stream_with_agent \
    tests/strands/agent/test_agent.py::test_agent__init__with_explicit_model \
    tests/strands/agent/test_agent.py::test_agent_tool_names \
    tests/strands/memory/test_memory_manager.py::test_constructor_creates_instance_with_valid_config_and_name \
    tests/strands/tools/mcp/test_mcp_client_tasks.py::TestTasksOptIn::test_tasks_enabled_state
fi
