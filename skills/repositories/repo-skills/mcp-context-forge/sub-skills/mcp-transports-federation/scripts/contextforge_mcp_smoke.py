#!/usr/bin/env python3
"""Read-only smoke checks for ContextForge MCP transports and health headers."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any, Optional, Sequence
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class HealthSummary:
    """Small summary of the gateway health headers."""

    runtime_mode: str
    transport_mounted: str
    raw: dict[str, str]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only health and transport smoke for ContextForge MCP endpoints.",
    )
    parser.add_argument("--base-url", required=True, help="Gateway base URL, for example http://127.0.0.1:8080")
    parser.add_argument("--transport-endpoint", default="/mcp", help="Transport path or full URL to probe; default: /mcp")
    parser.add_argument("--server-id", help="Virtual server id used when the endpoint path contains {server_id}")
    parser.add_argument("--token", help="Bearer token for authenticated transport checks")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    parser.add_argument("--protocol-version", default="2025-11-25", help="MCP protocol version to advertise during initialize")
    parser.add_argument("--client-name", default="contextforge-mcp-smoke", help="Client name advertised in initialize")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--health-only", dest="health_only", action="store_true", help="Only check /health and exit")
    group.add_argument("--exercise-transport", dest="health_only", action="store_false", help="Also initialize and list transport capabilities")
    parser.set_defaults(health_only=True)

    parser.add_argument("--expect-runtime-mode", help="Fail if /health reports a different x-contextforge-mcp-runtime-mode")
    parser.add_argument("--expect-transport-mounted", help="Fail if /health reports a different x-contextforge-mcp-transport-mounted")
    return parser


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _build_transport_url(base_url: str, endpoint_path: str, server_id: Optional[str]) -> str:
    if endpoint_path.startswith(("http://", "https://")):
        url = endpoint_path
    else:
        path = endpoint_path.strip()
        if "{server_id}" in path:
            if not server_id:
                raise ValueError("--server-id is required when --transport-endpoint contains {server_id}")
            path = path.format(server_id=server_id)
        if not path.startswith("/"):
            path = f"/{path}"
        url = f"{_normalize_base_url(base_url)}{path}"

    parsed = urlsplit(url)
    if parsed.path.endswith("/mcp") and not parsed.path.endswith("/mcp/"):
        parsed = parsed._replace(path=f"{parsed.path}/")
        url = urlunsplit(parsed)
    return url


async def _probe_health(base_url: str, timeout: float) -> HealthSummary:
    import httpx

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(f"{_normalize_base_url(base_url)}/health")
        response.raise_for_status()
        headers = {key.lower(): value for key, value in response.headers.items()}

    return HealthSummary(
        runtime_mode=headers.get("x-contextforge-mcp-runtime-mode", "unknown"),
        transport_mounted=headers.get("x-contextforge-mcp-transport-mounted", "unknown"),
        raw=headers,
    )


def _print_health(summary: HealthSummary) -> None:
    print("/health")
    print(f"  runtime-mode:      {summary.runtime_mode}")
    print(f"  transport-mounted:  {summary.transport_mounted}")
    for key in (
        "x-contextforge-mcp-session-core-mode",
        "x-contextforge-mcp-event-store-mode",
        "x-contextforge-mcp-resume-core-mode",
        "x-contextforge-mcp-live-stream-core-mode",
        "x-contextforge-mcp-affinity-core-mode",
        "x-contextforge-mcp-session-auth-reuse-mode",
    ):
        if key in summary.raw:
            print(f"  {key}: {summary.raw[key]}")


async def _probe_transport(url: str, token: Optional[str], timeout: float, protocol_version: str, client_name: str) -> dict[str, Any]:
    from datetime import timedelta

    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("The 'mcp' package is required for transport probing") from exc

    headers: dict[str, str] = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": protocol_version,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    transport_timeout = timedelta(seconds=timeout)
    async with streamablehttp_client(url, headers=headers, timeout=transport_timeout, sse_read_timeout=transport_timeout) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()
            tools_result = await session.list_tools()
            resources_result = await session.list_resources()
            prompts_result = await session.list_prompts()

    return {
        "client": client_name,
        "protocol_version": getattr(init_result, "protocolVersion", None),
        "server_name": getattr(getattr(init_result, "serverInfo", None), "name", None),
        "server_version": getattr(getattr(init_result, "serverInfo", None), "version", None),
        "tools": len(getattr(tools_result, "tools", []) or []),
        "resources": len(getattr(resources_result, "resources", []) or []),
        "prompts": len(getattr(prompts_result, "prompts", []) or []),
    }


async def _run(args: argparse.Namespace) -> int:
    health = await _probe_health(args.base_url, args.timeout)
    _print_health(health)

    if args.expect_runtime_mode and health.runtime_mode != args.expect_runtime_mode:
        raise SystemExit(f"Expected runtime mode {args.expect_runtime_mode!r}, got {health.runtime_mode!r}")
    if args.expect_transport_mounted and health.transport_mounted != args.expect_transport_mounted:
        raise SystemExit(f"Expected transport-mounted {args.expect_transport_mounted!r}, got {health.transport_mounted!r}")

    if args.health_only:
        return 0

    transport_url = _build_transport_url(args.base_url, args.transport_endpoint, args.server_id)
    print()
    print("transport")
    print(f"  url: {transport_url}")

    try:
        summary = await _probe_transport(transport_url, args.token, args.timeout, args.protocol_version, args.client_name)
    except Exception as exc:
        message = str(exc)
        print(f"  error: {message}")
        lower = message.lower()
        if "405" in lower or "mcp-session-id" in lower:
            print("  hint: initialize first, then retry with the returned session id on the proper MCP path")
        elif "401" in lower or "403" in lower:
            print("  hint: check the bearer token and whether the target server requires OAuth or public-only access")
        elif "404" in lower:
            print("  hint: confirm the endpoint path and, if needed, provide --server-id for a scoped virtual server")
        elif "503" in lower:
            print("  hint: the transport stack or session backend is unavailable right now")
        return 1

    print(f"  protocol-version:  {summary['protocol_version']}")
    print(f"  server:            {summary['server_name']} {summary['server_version']}")
    print(f"  tools:             {summary['tools']}")
    print(f"  resources:         {summary['resources']}")
    print(f"  prompts:           {summary['prompts']}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
