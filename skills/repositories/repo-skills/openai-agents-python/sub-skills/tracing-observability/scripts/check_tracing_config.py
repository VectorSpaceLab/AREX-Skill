#!/usr/bin/env python3
"""Safe local tracing configuration checker for openai-agents-python.

The script performs import/config diagnostics only. It does not call OpenAI APIs,
export traces, print secret values, or require the source repository checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
from typing import Any


TRUE_VALUES = {"1", "true"}
FALSE_VALUES = {"0", "false"}
SECRET_ENV_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_ORG_ID",
    "OPENAI_PROJECT_ID",
)
FLAG_ENV_NAMES = (
    "OPENAI_AGENTS_DISABLE_TRACING",
    "OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA",
    "OPENAI_AGENTS_DONT_LOG_MODEL_DATA",
    "OPENAI_AGENTS_DONT_LOG_TOOL_DATA",
)


def _parse_bool_env(value: str | None, *, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def _secret_status(name: str) -> dict[str, Any]:
    value = os.environ.get(name)
    if value is None:
        return {"present": False}
    stripped = value.strip()
    return {
        "present": bool(stripped),
        "length": len(stripped),
        "masked_preview": "<set>" if stripped else "<empty>",
    }


def _flag_status(name: str, *, default: bool | None = None) -> dict[str, Any]:
    raw = os.environ.get(name)
    parsed = _parse_bool_env(raw, default=default)
    status: dict[str, Any] = {
        "present": raw is not None,
        "parsed": parsed,
    }
    if raw is not None and parsed is None:
        status["warning"] = "Expected one of 1/true/0/false."
    return status


def _check_imports() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "imports": {}, "errors": []}
    try:
        import agents

        result["imports"]["agents"] = True
        result["agents_version"] = getattr(agents, "__version__", None)
    except Exception as exc:  # pragma: no cover - diagnostic script
        result["imports"]["agents"] = False
        result["errors"].append(f"agents import failed: {exc.__class__.__name__}: {exc}")
        return result

    try:
        from agents import RunConfig, Usage  # noqa: F401
        from agents.tracing import (  # noqa: F401
            TracingProcessor,
            custom_span,
            flush_traces,
            gen_trace_id,
            set_trace_provider,
            trace,
        )

        result["imports"]["tracing_api"] = True
        run_config = RunConfig()
        result["run_config_defaults"] = {
            "tracing_disabled": run_config.tracing_disabled,
            "trace_include_sensitive_data": run_config.trace_include_sensitive_data,
            "workflow_name": run_config.workflow_name,
            "group_id_is_set": run_config.group_id is not None,
            "trace_metadata_is_set": run_config.trace_metadata is not None,
            "tracing_config_is_set": run_config.tracing is not None,
        }
        sample_trace_id = gen_trace_id()
        result["sample_trace_id_shape"] = {
            "starts_with_trace_prefix": sample_trace_id.startswith("trace_"),
            "length": len(sample_trace_id),
        }
        result["usage_importable"] = True
        result["ok"] = True
    except Exception as exc:  # pragma: no cover - diagnostic script
        result["imports"]["tracing_api"] = False
        result["errors"].append(f"tracing API check failed: {exc.__class__.__name__}: {exc}")
    return result


def _check_graphviz() -> dict[str, Any]:
    package_available = importlib.util.find_spec("graphviz") is not None
    dot_path = shutil.which("dot")
    result: dict[str, Any] = {
        "python_package_available": package_available,
        "dot_executable_available": dot_path is not None,
    }
    if package_available:
        try:
            from agents import Agent
            from agents.extensions.visualization import draw_graph, get_main_graph

            agent = Agent(name="VisualizationCheck")
            graph = draw_graph(agent)
            result["agents_visualization_importable"] = True
            result["dot_source_contains_agent"] = "VisualizationCheck" in graph.source
            result["main_graph_contains_digraph"] = "digraph G" in get_main_graph(agent)
        except Exception as exc:  # pragma: no cover - diagnostic script
            result["agents_visualization_importable"] = False
            result["error"] = f"{exc.__class__.__name__}: {exc}"
    else:
        result["agents_visualization_importable"] = False
        result["hint"] = "Install the optional visualization dependency and system Graphviz to render graphs."
    return result


def _processor_smoke() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "counts": {}, "errors": []}
    try:
        from agents.tracing import TracingProcessor, custom_span, set_trace_provider, trace
        from agents.tracing.provider import DefaultTraceProvider

        class CountingProcessor(TracingProcessor):
            def __init__(self) -> None:
                self.trace_starts = 0
                self.trace_ends = 0
                self.span_starts = 0
                self.span_ends = 0
                self.flushes = 0
                self.shutdowns = 0

            def on_trace_start(self, trace_obj: Any) -> None:
                self.trace_starts += 1

            def on_trace_end(self, trace_obj: Any) -> None:
                self.trace_ends += 1

            def on_span_start(self, span_obj: Any) -> None:
                self.span_starts += 1

            def on_span_end(self, span_obj: Any) -> None:
                self.span_ends += 1

            def shutdown(self) -> None:
                self.shutdowns += 1

            def force_flush(self) -> None:
                self.flushes += 1

        processor = CountingProcessor()
        provider = DefaultTraceProvider()
        provider.set_processors([processor])
        set_trace_provider(provider)

        with trace("local-tracing-config-check", group_id="local-smoke"):
            with custom_span("local-step", {"safe": True}):
                pass

        provider.force_flush()
        result["counts"] = {
            "trace_starts": processor.trace_starts,
            "trace_ends": processor.trace_ends,
            "span_starts": processor.span_starts,
            "span_ends": processor.span_ends,
            "flushes": processor.flushes,
        }
        result["ok"] = result["counts"] == {
            "trace_starts": 1,
            "trace_ends": 1,
            "span_starts": 1,
            "span_ends": 1,
            "flushes": 1,
        }
    except Exception as exc:  # pragma: no cover - diagnostic script
        result["errors"].append(f"processor smoke failed: {exc.__class__.__name__}: {exc}")
    return result


def build_report(*, check_processor: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": True,
        "secrets": {name: _secret_status(name) for name in SECRET_ENV_NAMES},
        "flags": {
            "OPENAI_AGENTS_DISABLE_TRACING": _flag_status(
                "OPENAI_AGENTS_DISABLE_TRACING", default=False
            ),
            "OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA": _flag_status(
                "OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA", default=True
            ),
            "OPENAI_AGENTS_DONT_LOG_MODEL_DATA": _flag_status(
                "OPENAI_AGENTS_DONT_LOG_MODEL_DATA", default=True
            ),
            "OPENAI_AGENTS_DONT_LOG_TOOL_DATA": _flag_status(
                "OPENAI_AGENTS_DONT_LOG_TOOL_DATA", default=True
            ),
        },
        "imports": _check_imports(),
        "graphviz": _check_graphviz(),
        "processor_smoke": None,
    }
    if check_processor:
        report["processor_smoke"] = _processor_smoke()

    report["ok"] = bool(report["imports"].get("ok")) and (
        report["processor_smoke"] is None or bool(report["processor_smoke"].get("ok"))
    )
    return report


def _print_human(report: dict[str, Any]) -> None:
    print("Tracing configuration check")
    print(f"Overall: {'ok' if report['ok'] else 'issues found'}")
    print("\nEnvironment secrets:")
    for name, status in report["secrets"].items():
        suffix = f" length={status['length']}" if status.get("present") else ""
        print(f"- {name}: {'set' if status.get('present') else 'unset'}{suffix}")

    print("\nEnvironment flags:")
    for name, status in report["flags"].items():
        parsed = status.get("parsed")
        parsed_text = "unset/default" if not status.get("present") else str(parsed)
        warning = f" ({status['warning']})" if status.get("warning") else ""
        print(f"- {name}: {parsed_text}{warning}")

    imports = report["imports"]
    print("\nImports:")
    print(f"- agents: {imports.get('imports', {}).get('agents', False)}")
    print(f"- tracing API: {imports.get('imports', {}).get('tracing_api', False)}")
    if imports.get("agents_version"):
        print(f"- version: {imports['agents_version']}")
    if imports.get("run_config_defaults"):
        defaults = imports["run_config_defaults"]
        print(f"- tracing_disabled default: {defaults['tracing_disabled']}")
        print(
            "- trace_include_sensitive_data default: "
            f"{defaults['trace_include_sensitive_data']}"
        )
        print(f"- workflow_name default: {defaults['workflow_name']}")
    for error in imports.get("errors", []):
        print(f"- error: {error}")

    graphviz = report["graphviz"]
    print("\nGraphviz:")
    print(f"- Python package: {graphviz['python_package_available']}")
    print(f"- dot executable: {graphviz['dot_executable_available']}")
    print(f"- agents visualization import: {graphviz['agents_visualization_importable']}")
    if graphviz.get("hint"):
        print(f"- hint: {graphviz['hint']}")
    if graphviz.get("error"):
        print(f"- error: {graphviz['error']}")

    smoke = report.get("processor_smoke")
    if smoke is not None:
        print("\nProcessor smoke:")
        print(f"- ok: {smoke.get('ok')}")
        for name, count in smoke.get("counts", {}).items():
            print(f"- {name}: {count}")
        for error in smoke.get("errors", []):
            print(f"- error: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--check-processor",
        action="store_true",
        help="Run a local-only trace processor smoke test with no external export.",
    )
    args = parser.parse_args(argv)

    report = build_report(check_processor=args.check_processor)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
