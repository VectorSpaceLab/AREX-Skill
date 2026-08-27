#!/usr/bin/env python3
"""Probe a running gptme-server without making destructive requests.

This helper checks the public API root and version endpoint, then attempts the
health endpoint with an optional bearer token. It is safe to run against a live
server because it only issues read-only GET requests.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class ProbeResult:
    name: str
    url: str
    ok: bool
    status: int | None
    message: str
    data: dict[str, Any] | list[Any] | str | None = None
    api_version: int | None = None
    contract_revision: int | None = None
    x_api_version: str | None = None
    auth_required: bool = False


def _normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise ValueError("base URL must not be empty")
    return value


def _load_json_bytes(raw: bytes) -> dict[str, Any] | list[Any] | str | None:
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _request_json(url: str, token: str | None, timeout: float) -> tuple[int, dict[str, Any] | list[Any] | str | None, str | None]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            payload = _load_json_bytes(response.read())
            x_api_version = response.headers.get("X-API-Version")
            return status, payload, x_api_version
    except HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        payload = _load_json_bytes(body)
        x_api_version = exc.headers.get("X-API-Version") if exc.headers else None
        return exc.code, payload, x_api_version


def _make_result(name: str, url: str, token: str | None, timeout: float) -> ProbeResult:
    try:
        status, payload, x_api_version = _request_json(url, token, timeout)
    except URLError as exc:
        return ProbeResult(
            name=name,
            url=url,
            ok=False,
            status=None,
            message=str(exc.reason) if getattr(exc, "reason", None) else str(exc),
        )

    auth_required = status == 401
    ok = 200 <= status < 300
    message = f"HTTP {status}"

    result = ProbeResult(
        name=name,
        url=url,
        ok=ok,
        status=status,
        message=message,
        data=payload,
        x_api_version=x_api_version,
        auth_required=auth_required,
    )

    if not isinstance(payload, dict):
        if name in {"root", "version", "health"} and ok:
            result.ok = False
            result.message = "non-JSON response"
        return result

    api_version = payload.get("api_version")
    contract_revision = payload.get("contract_revision")
    if isinstance(api_version, int):
        result.api_version = api_version
    elif name in {"root", "version"}:
        result.ok = False
        result.message = "missing api_version"
    if isinstance(contract_revision, int):
        result.contract_revision = contract_revision
    elif name in {"root", "version"}:
        result.ok = False
        result.message = "missing contract_revision"
    if name == "health" and auth_required:
        result.message = "authentication required"
    elif name == "root":
        provider_configured = payload.get("provider_configured")
        if isinstance(provider_configured, bool):
            result.message = (
                f"provider_configured={provider_configured}"
                f" api_version={result.api_version!s}"
                f" contract_revision={result.contract_revision!s}"
            )
    elif name == "version":
        result.message = (
            f"api_version={result.api_version!s}"
            f" contract_revision={result.contract_revision!s}"
        )
    elif name == "health":
        health = payload.get("health")
        session_count = payload.get("session_count")
        generating_count = payload.get("generating_count")
        if isinstance(health, str):
            result.message = (
                f"health={health}"
                f" sessions={session_count!s}"
                f" generating={generating_count!s}"
            )

    return result


def _compare_versions(root: ProbeResult, version: ProbeResult) -> list[str]:
    issues: list[str] = []
    if not isinstance(root.data, dict) or not isinstance(version.data, dict):
        return issues
    root_api = root.data.get("api_version")
    version_api = version.data.get("api_version")
    if root_api != version_api:
        issues.append(
            f"api_version mismatch: root={root_api!r} version={version_api!r}"
        )
    root_contract = root.data.get("contract_revision")
    version_contract = version.data.get("contract_revision")
    if root_contract != version_contract:
        issues.append(
            "contract_revision mismatch: "
            f"root={root_contract!r} version={version_contract!r}"
        )
    if root.x_api_version and version.x_api_version and root.x_api_version != version.x_api_version:
        issues.append(
            f"X-API-Version mismatch: root={root.x_api_version!r} version={version.x_api_version!r}"
        )
    return issues


def _render_text(results: list[ProbeResult], issues: list[str]) -> str:
    lines = []
    for result in results:
        status = result.status if result.status is not None else "error"
        suffix = " [auth required]" if result.auth_required else ""
        lines.append(f"{result.name}: {status}{suffix} — {result.message}")
        if result.x_api_version:
            lines.append(f"  X-API-Version: {result.x_api_version}")
    if issues:
        lines.append("")
        lines.append("consistency issues:")
        for issue in issues:
            lines.append(f"- {issue}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe a running gptme-server with read-only HTTP requests.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5700",
        help="Base server URL, for example http://127.0.0.1:5700",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional bearer token for authenticated endpoints.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        base_url = _normalize_base_url(args.base_url)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    results = [
        _make_result("root", f"{base_url}/api/v2", args.token, args.timeout),
        _make_result("version", f"{base_url}/api/v2/version", args.token, args.timeout),
        _make_result("health", f"{base_url}/api/v2/server/health", args.token, args.timeout),
    ]

    issues = _compare_versions(results[0], results[1])
    healthy = all(r.ok or (r.name == "health" and r.auth_required and not args.token) for r in results)
    if any(not r.ok and not (r.name == "health" and r.auth_required and not args.token) for r in results[:2]):
        healthy = False
    if issues:
        healthy = False

    if args.json:
        payload = {
            "base_url": base_url,
            "results": [asdict(result) for result in results],
            "issues": issues,
            "healthy": healthy,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_text(results, issues))

    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
