#!/usr/bin/env python3
"""
Inspect ai-data-science-team multi-agent and app-facing APIs without invoking
LLMs, launching Streamlit apps, downloading data, training models, or writing
files.

The script imports public classes/factories, records signatures and docstring
summaries, and reports the installed Streamlit version when available.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from typing import Any

OBJECTS: list[tuple[str, str, str]] = [
    ("PandasDataAnalyst", "ai_data_science_team.multiagents.pandas_data_analyst", "PandasDataAnalyst"),
    ("make_pandas_data_analyst", "ai_data_science_team.multiagents.pandas_data_analyst", "make_pandas_data_analyst"),
    ("SQLDataAnalyst", "ai_data_science_team.multiagents.sql_data_analyst", "SQLDataAnalyst"),
    ("make_sql_data_analyst", "ai_data_science_team.multiagents.sql_data_analyst", "make_sql_data_analyst"),
    ("SupervisorDSTeam", "ai_data_science_team.multiagents.supervisor_ds_team", "SupervisorDSTeam"),
    ("make_supervisor_ds_team", "ai_data_science_team.multiagents.supervisor_ds_team", "make_supervisor_ds_team"),
    ("WorkflowPlannerAgent", "ai_data_science_team.agents.workflow_planner_agent", "WorkflowPlannerAgent"),
]

METHODS: dict[str, list[str]] = {
    "PandasDataAnalyst": [
        "invoke_agent",
        "ainvoke_agent",
        "invoke_messages",
        "ainvoke_messages",
        "get_data_wrangled",
        "get_plotly_graph",
        "get_data_wrangler_function",
        "get_data_visualization_function",
        "get_workflow_summary",
    ],
    "SQLDataAnalyst": [
        "invoke_agent",
        "ainvoke_agent",
        "invoke_messages",
        "ainvoke_messages",
        "get_data_sql",
        "get_plotly_graph",
        "get_sql_query_code",
        "get_sql_database_function",
        "get_data_visualization_function",
        "get_workflow_summary",
    ],
    "SupervisorDSTeam": [
        "invoke_agent",
        "ainvoke_agent",
        "invoke_messages",
        "ainvoke_messages",
        "invoke",
        "ainvoke",
        "get_ai_message",
        "get_artifacts",
        "show",
    ],
    "WorkflowPlannerAgent": ["invoke_messages", "get_plan", "update_params"],
}


def safe_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"error: {type(exc).__name__}: {exc}"


def first_doc_line(obj: Any) -> str:
    doc = inspect.getdoc(obj) or ""
    return doc.splitlines()[0] if doc else ""


def signature_text(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def inspect_object(label: str, module_name: str, attr_name: str) -> dict[str, Any]:
    record: dict[str, Any] = {"module": module_name, "attribute": attr_name}
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr_name)
        record.update(
            {
                "imported": True,
                "signature": signature_text(obj),
                "doc_first_line": first_doc_line(obj),
            }
        )
        if inspect.isclass(obj):
            method_records: dict[str, dict[str, str]] = {}
            for method_name in METHODS.get(label, []):
                method = getattr(obj, method_name, None)
                if method is None:
                    method_records[method_name] = {"status": "missing"}
                    continue
                method_records[method_name] = {
                    "status": "ok",
                    "signature": signature_text(method),
                    "doc_first_line": first_doc_line(method),
                }
            if method_records:
                record["methods"] = method_records
    except Exception as exc:
        record.update(
            {
                "imported": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
    return record


def build_report() -> dict[str, Any]:
    objects = {
        label: inspect_object(label, module_name, attr_name)
        for label, module_name, attr_name in OBJECTS
    }
    streamlit_import: dict[str, Any] = {"distribution_version": safe_version("streamlit")}
    try:
        st = importlib.import_module("streamlit")
        streamlit_import["imported"] = True
        streamlit_import["module_version"] = getattr(st, "__version__", None)
    except Exception as exc:
        streamlit_import.update(
            {"imported": False, "error_type": type(exc).__name__, "error": str(exc)}
        )

    report = {
        "safe_by_default": True,
        "actions_performed": [
            "import public multi-agent modules",
            "inspect signatures and docstrings",
            "read installed package metadata",
            "import streamlit only when present",
        ],
        "actions_not_performed": [
            "no LLM calls",
            "no Streamlit app launch",
            "no network access",
            "no downloads",
            "no model training",
            "no file writes",
        ],
        "distributions": {
            "ai-data-science-team": safe_version("ai-data-science-team"),
            "streamlit": safe_version("streamlit"),
        },
        "objects": objects,
        "streamlit": streamlit_import,
    }
    return report


def render_text(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("ai-data-science-team multi-agent API inspection")
    lines.append("Distributions:")
    for name, version in report.get("distributions", {}).items():
        lines.append(f"  - {name}: {version or 'not found'}")
    lines.append("Objects:")
    for label, rec in report.get("objects", {}).items():
        if rec.get("imported"):
            lines.append(f"  - {label}: {rec.get('signature')}")
        else:
            lines.append(
                f"  - {label}: import failed ({rec.get('error_type')}: {rec.get('error')})"
            )
    st = report.get("streamlit", {})
    if st.get("imported"):
        lines.append(f"Streamlit: {st.get('module_version') or st.get('distribution_version')}")
    else:
        lines.append(
            f"Streamlit: unavailable ({st.get('error_type')}: {st.get('error')})"
        )
    lines.append("No LLM calls, app launches, downloads, training, or file writes were performed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. JSON is easiest for automated checks.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Return a non-zero status if any required object import fails.",
    )
    args = parser.parse_args(argv)

    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.fail_on_error:
        failed = [
            label
            for label, rec in report.get("objects", {}).items()
            if not rec.get("imported")
        ]
        if failed:
            print("Required imports failed: " + ", ".join(failed), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
