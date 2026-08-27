#!/usr/bin/env python3
"""Validate Browser Use custom tool patterns without launching a browser.

This helper is intentionally offline-safe: it imports Browser Use, registers a
few representative actions, checks schema generation and expected validation
failures, and exercises ActionResult normalization. It does not create an Agent,
open Chromium, make network calls, or require API keys.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

if (Path.cwd() / "browser_use").is_dir() and str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))


def _fail(message: str) -> None:
    raise AssertionError(message)


async def run_checks(verbose: bool = False) -> None:
    try:
        from browser_use import ActionResult, Tools
        from browser_use.tools.registry.service import Registry
        from browser_use.tools.registry.views import ActionModel as BaseActionModel
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise AssertionError(
            "Could not import browser_use and its dependencies. Install Browser Use in the active environment "
            f"or add the missing dependency reported here: {type(exc).__name__}: {exc}"
        ) from exc

    tools = Tools(exclude_actions=["search", "evaluate"])

    @tools.action("Echo a message for validation")
    async def echo_message(message: str, repeat: int = 1) -> ActionResult:
        return ActionResult(extracted_content=" ".join([message] * repeat))

    class TicketParams(BaseActionModel):
        title: str = Field(min_length=3)
        priority: str = Field(pattern="^(low|medium|high)$")

    @tools.action("Create a validation ticket", param_model=TicketParams)
    async def create_ticket(params: TicketParams) -> ActionResult:
        return ActionResult(extracted_content=f"{params.priority}:{params.title}")

    if "search" in tools.registry.registry.actions:
        _fail("exclude_actions did not remove default search action")
    if "evaluate" in tools.registry.registry.actions:
        _fail("exclude_actions did not remove default evaluate action")

    echo_action = tools.registry.registry.actions.get("echo_message")
    if echo_action is None:
        _fail("custom loose-parameter action was not registered")
    echo_schema = echo_action.param_model.model_json_schema()
    if "message" not in echo_schema.get("properties", {}):
        _fail("loose-parameter action did not expose message in schema")
    if echo_schema["properties"].get("repeat", {}).get("default") != 1:
        _fail("loose-parameter action did not preserve default repeat=1")

    ticket_action = tools.registry.registry.actions.get("create_ticket")
    if ticket_action is None or ticket_action.param_model is not TicketParams:
        _fail("param_model action did not preserve the provided Pydantic model")

    sig = inspect.signature(echo_message)
    positional = [
        param
        for param in sig.parameters.values()
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if positional:
        _fail("decorated actions should be normalized to keyword-only signatures")

    echo_params = echo_action.param_model(message="ok", repeat=2)
    result = await echo_message(params=echo_params)
    if not isinstance(result, ActionResult) or result.extracted_content != "ok ok":
        _fail("decorated action did not execute with params model")

    try:
        await echo_message("not allowed")  # type: ignore[misc]
    except TypeError as exc:
        if "positional" not in str(exc):
            _fail(f"unexpected positional-argument error: {exc}")
    else:
        _fail("decorated action accepted positional arguments")

    registry = Registry()
    try:
        @registry.action("Invalid kwargs action")
        async def bad_kwargs(name: str, **kwargs: Any) -> ActionResult:  # noqa: ARG001
            return ActionResult(extracted_content=name)
    except ValueError as exc:
        if "kwargs" not in str(exc):
            _fail(f"unexpected kwargs validation error: {exc}")
    else:
        _fail("registry accepted an action with **kwargs")

    try:
        @registry.action("Invalid special type")
        async def bad_special(browser_session: str) -> ActionResult:
            return ActionResult(extracted_content=browser_session)
    except ValueError as exc:
        if "conflicts with special argument" not in str(exc):
            _fail(f"unexpected special-parameter validation error: {exc}")
    else:
        _fail("registry accepted wrong type for browser_session")

    class SensitiveParams(BaseModel):
        text: str

    sensitive = {
        "https://example.com": {"username": "alice", "password": "secret"},
        "global_label": "legacy",
    }
    replaced = registry._replace_sensitive_data(
        SensitiveParams(text="Login <secret>username</secret> / <secret>password</secret>"),
        sensitive,
        "https://example.com/login",
    )
    if replaced.text != "Login alice / secret":
        _fail("domain-specific sensitive_data placeholders were not replaced on matching URL")

    not_replaced = registry._replace_sensitive_data(
        SensitiveParams(text="Login <secret>username</secret>"),
        sensitive,
        "https://evil.test/login",
    )
    if "alice" in not_replaced.text or "<secret>username</secret>" not in not_replaced.text:
        _fail("domain-specific sensitive_data leaked on non-matching URL")

    domain_tools = Tools()

    @domain_tools.action("Only for example", allowed_domains=["https://example.com"])
    async def only_example() -> ActionResult:
        return ActionResult(extracted_content="ok")

    prompt_without_url = domain_tools.registry.get_prompt_description(page_url=None)
    prompt_matching = domain_tools.registry.get_prompt_description(page_url="https://example.com/path")
    prompt_nonmatching = domain_tools.registry.get_prompt_description(page_url="https://evil.test/path")
    if "only_example" in prompt_without_url:
        _fail("domain-filtered action appeared in the generic prompt")
    if "only_example" not in prompt_matching:
        _fail("domain-filtered action did not appear for matching URL")
    if "only_example" in prompt_nonmatching:
        _fail("domain-filtered action appeared for non-matching URL")

    if verbose:
        print("Registered custom actions:", sorted(tools.registry.registry.actions))
        print("Echo schema properties:", sorted(echo_schema.get("properties", {})))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Browser Use custom tool patterns without launching a browser.")
    parser.add_argument("--verbose", action="store_true", help="print schema/action details after checks pass")
    args = parser.parse_args()

    try:
        asyncio.run(run_checks(verbose=args.verbose))
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"ERROR: unexpected validation failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print("OK: Browser Use custom tool validation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
