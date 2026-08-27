#!/usr/bin/env python3
"""Safe LaVague Gradio and Chrome-extension server probe.

This helper only imports modules, inspects signatures, checks whether a local TCP
port appears free, and prints launch templates on request. It never calls
``WebAgent.demo()``, ``GradioAgentDemo.launch()``, ``AgentServer.serve()``, or
``lavague-serve`` without the user's separate explicit action.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import shutil
import socket
import sys
import textwrap
from dataclasses import dataclass
from types import ModuleType
from typing import Any

# Keep probes quiet/safe where LaVague honors this environment variable.
os.environ.setdefault("LAVAGUE_TELEMETRY", "NONE")


SERVER_TEMPLATE = r'''
# Persistent Chrome-extension server template. Run only when you intentionally
# want to keep a local websocket server alive for the browser extension.
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.server import AgentServer, AgentSession
from lavague.server.driver import DriverServer


def create_agent(session: AgentSession):
    # The extension owns the browser tab; DriverServer forwards driver calls
    # over the websocket session created by the extension.
    driver = DriverServer(session)
    world_model = WorldModel()
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)


server = AgentServer(create_agent, port=8000)
server.serve()
'''.strip()


GRADIO_TEMPLATE = r'''
# Persistent Gradio demo template. Run only when you intentionally want an
# interactive UI; the installed lavague-gradio launch path starts a Gradio app.
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver


driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine)

# Optional live navigation before the UI starts; replace with a user-approved target URL.
# agent.get("about:blank")
agent.demo("Describe the objective for the browser agent")
'''.strip()


@dataclass
class ProbeResult:
    label: str
    ok: bool
    detail: str


def print_result(result: ProbeResult) -> None:
    tag = "OK" if result.ok else "FAIL"
    print(f"[{tag}] {result.label}: {result.detail}")


def import_module(name: str) -> tuple[ModuleType | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"{type(exc).__name__}: {exc}"


def import_attr(module_name: str, attr_name: str) -> tuple[Any | None, str | None]:
    module, err = import_module(module_name)
    if err:
        return None, err
    try:
        return getattr(module, attr_name), None
    except AttributeError as exc:  # pragma: no cover - diagnostic path
        return None, str(exc)


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def check_port_available(port: int) -> ProbeResult:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError as exc:
        return ProbeResult(
            "local port availability",
            False,
            f"127.0.0.1:{port} is not bindable ({exc}); choose another --port or stop the conflicting process",
        )
    finally:
        sock.close()
    return ProbeResult(
        "local port availability",
        True,
        f"127.0.0.1:{port} appears free; no server was started",
    )


def check_gradio() -> bool:
    print("\n== Gradio demo probe ==")
    ok = True

    gradio_module, gradio_err = import_module("gradio")
    result = ProbeResult(
        "gradio import",
        gradio_err is None,
        "imported" if gradio_err is None else f"missing or broken ({gradio_err})",
    )
    print_result(result)
    ok = ok and result.ok

    gradio_agent, err = import_attr("lavague.gradio", "GradioAgentDemo")
    result = ProbeResult(
        "lavague-gradio import",
        err is None,
        "GradioAgentDemo imported" if err is None else f"install/repair lavague-gradio ({err})",
    )
    print_result(result)
    ok = ok and result.ok

    web_agent, web_err = import_attr("lavague.core.agents", "WebAgent")
    result = ProbeResult(
        "WebAgent import",
        web_err is None,
        "WebAgent imported" if web_err is None else web_err,
    )
    print_result(result)
    ok = ok and result.ok

    if gradio_agent is not None:
        print(f"GradioAgentDemo.__init__{safe_signature(gradio_agent.__init__)}")
        print(f"GradioAgentDemo.launch{safe_signature(gradio_agent.launch)}")
    if web_agent is not None:
        print(f"WebAgent.demo{safe_signature(web_agent.demo)}")

    print("No Gradio UI was launched.")
    return ok


def check_server(port: int) -> bool:
    print("\n== Chrome-extension server probe ==")
    ok = True

    agent_server, err = import_attr("lavague.server", "AgentServer")
    result = ProbeResult(
        "AgentServer import",
        err is None,
        "from lavague.server import AgentServer" if err is None else err,
    )
    print_result(result)
    ok = ok and result.ok

    agent_session, err = import_attr("lavague.server", "AgentSession")
    result = ProbeResult(
        "AgentSession import",
        err is None,
        "from lavague.server import AgentSession" if err is None else err,
    )
    print_result(result)
    ok = ok and result.ok

    driver_server, err = import_attr("lavague.server.driver", "DriverServer")
    result = ProbeResult(
        "DriverServer import",
        err is None,
        "from lavague.server.driver import DriverServer" if err is None else err,
    )
    print_result(result)
    ok = ok and result.ok

    cli_module, cli_err = import_module("lavague.server.cli")
    result = ProbeResult(
        "lavague.server.cli import",
        cli_err is None,
        "CLI module imported" if cli_err is None else cli_err,
    )
    print_result(result)
    ok = ok and result.ok

    command = shutil.which("lavague-serve")
    print_result(
        ProbeResult(
            "lavague-serve console script",
            command is not None,
            "found on PATH" if command else "not on PATH; try python -m lavague.server.cli or reinstall lavague-server",
        )
    )

    if agent_server is not None:
        print(f"AgentServer{safe_signature(agent_server)}")
        print(f"AgentServer.serve{safe_signature(agent_server.serve)}")
        print(f"AgentServer.close{safe_signature(agent_server.close)}")
    if agent_session is not None:
        has_sync = hasattr(agent_session, "send_command_and_get_response_sync")
        print_result(
            ProbeResult(
                "AgentSession command bridge",
                has_sync,
                "send_command_and_get_response_sync available" if has_sync else "missing sync command bridge",
            )
        )
        ok = ok and has_sync
    if driver_server is not None:
        print(f"DriverServer{safe_signature(driver_server)}")

    print_result(check_port_available(port))
    print("No websocket server was started.")
    return ok


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely probe LaVague Gradio and Chrome-extension server imports/templates without launching persistent services.",
    )
    parser.add_argument(
        "--check",
        choices=("gradio", "server", "both"),
        default="both",
        help="Which import/signature probe to run. Default: both.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Local port to test for extension-server availability. No server is started. Default: 8000.",
    )
    parser.add_argument(
        "--print-server-template",
        action="store_true",
        help="Print a corrected AgentServer/DriverServer launch template; do not execute it.",
    )
    parser.add_argument(
        "--print-gradio-template",
        action="store_true",
        help="Print a WebAgent.demo launch template; do not execute it.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.print_server_template:
        print("\n== AgentServer template ==")
        print(textwrap.dedent(SERVER_TEMPLATE))
    if args.print_gradio_template:
        print("\n== Gradio demo template ==")
        print(textwrap.dedent(GRADIO_TEMPLATE))

    ok = True
    if args.check in ("gradio", "both"):
        ok = check_gradio() and ok
    if args.check in ("server", "both"):
        ok = check_server(args.port) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
