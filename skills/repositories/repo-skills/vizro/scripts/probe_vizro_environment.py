#!/usr/bin/env python3
"""CPU-only import/smoke probe for the Vizro repo skill.

This script does not start a server, open a browser, call an LLM provider, or read
network resources. It verifies that the installed packages expose the APIs used by
this skill snapshot.
"""

from __future__ import annotations

import importlib
import importlib.metadata as metadata
import inspect
import sys
import warnings
from dataclasses import dataclass
from typing import Callable


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


checks: list[Check] = []


def record(name: str, func: Callable[[], str]) -> None:
    try:
        detail = func()
    except Exception as exc:  # noqa: BLE001 - probe should report all failures.
        checks.append(Check(name, False, f"{type(exc).__name__}: {exc}"))
    else:
        checks.append(Check(name, True, detail))


def version(dist: str) -> str:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "MISSING"


def check_versions() -> str:
    dists = [
        "vizro",
        "vizro-dash-components",
        "vizro-ai",
        "vizro-mcp",
        "vizro-experimental",
        "dash",
        "pandas",
        "plotly",
        "pydantic",
        "mcp",
        "pydantic-ai-slim",
    ]
    return ", ".join(f"{dist}={version(dist)}" for dist in dists)


def check_imports() -> str:
    modules = [
        "vizro",
        "vizro.models",
        "vizro.plotly.express",
        "vizro_dash_components",
        "vizro_ai.agents._chart_agent",
        "vizro_mcp.server",
        "vizro_experimental.chat.models.chat",
        "vizro_experimental.chat.popup",
    ]
    imported = []
    for module_name in modules:
        module = importlib.import_module(module_name)
        imported.append(f"{module_name}<-{getattr(module, '__file__', 'built-in')}")
    return "; ".join(imported)


def check_core_dashboard() -> str:
    from vizro import Vizro
    import vizro.models as vm

    dashboard = vm.Dashboard(
        pages=[vm.Page(title="Probe", components=[vm.Card(text="hello from probe")])],
    )
    wrapper = Vizro().build(dashboard)
    assert hasattr(wrapper, "dash"), "Vizro.build should return wrapper with .dash"
    assert wrapper.dash.layout is not None, "Dash layout was not built"
    return f"wrapper={type(wrapper).__name__}, dash={type(wrapper.dash).__name__}, title={wrapper.dash.title!r}"


def check_dash_components() -> str:
    from vizro_dash_components import Cascader, Markdown

    cascader = Cascader(id="probe-cascader", options=[{"label": "A", "value": "a"}], value=["a"])
    markdown = Markdown(id="probe-md", children="**hello**", mathjax=False)
    assert cascader.id == "probe-cascader"
    assert markdown.children == "**hello**"
    return f"components={type(cascader).__name__},{type(markdown).__name__}"


def check_legacy_ai() -> str:
    from vizro_ai.agents._chart_agent import add_df, chart_agent
    from vizro_ai.agents.response_models import BaseChartPlan

    return (
        f"agent={type(chart_agent).__name__}, "
        f"response_model={BaseChartPlan.__name__}, add_df_signature={inspect.signature(add_df)}"
    )


def check_mcp() -> str:
    import vizro_mcp.server as server

    required = ["mcp", "create_dashboard", "validate_dashboard_config"]
    missing = [name for name in required if not hasattr(server, name)]
    assert not missing, f"missing server attributes: {missing}"
    return ", ".join(required)


def check_experimental_chat() -> str:
    from vizro_experimental.chat.models.chat import Chat
    from vizro_experimental.chat.popup import add_chat_popup, create_dashboard_agent, make_generate_response

    assert callable(add_chat_popup)
    assert callable(create_dashboard_agent)
    assert callable(make_generate_response)
    return f"Chat={inspect.signature(Chat)}, add_chat_popup={inspect.signature(add_chat_popup)}"


def main() -> int:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    print(f"python={sys.version.split()[0]} executable={sys.executable}")
    record("versions", check_versions)
    record("imports", check_imports)
    record("core-dashboard", check_core_dashboard)
    record("dash-components", check_dash_components)
    record("legacy-ai", check_legacy_ai)
    record("mcp", check_mcp)
    record("experimental-chat", check_experimental_chat)

    failed = False
    for check in checks:
        status = "OK" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")
        failed = failed or not check.ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
