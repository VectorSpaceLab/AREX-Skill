#!/usr/bin/env python3
"""Safely inspect SAM HTTP gateway endpoints without submitting tasks.

The script performs GET probes only. It never posts to message/task endpoints and
therefore does not submit a real prompt. It can be run from any working
directory because it has no repository-relative imports.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass
class ProbeResult:
    name: str
    path: str
    url: str
    status: int | None
    classification: str
    elapsed_ms: int
    content_type: str | None = None
    json_summary: Any | None = None
    body_preview: str | None = None
    error: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe a SAM Web UI or REST gateway with safe GET requests only. "
            "No tasks are submitted."
        )
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Base gateway URL, for example http://localhost:8000 or http://localhost:8080.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("SAM_AUTH_TOKEN"),
        help="Bearer token. Defaults to SAM_AUTH_TOKEN when set.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-request timeout in seconds. Default: 5.",
    )
    parser.add_argument(
        "--expect-agent",
        action="append",
        default=[],
        help="Agent name expected in /api/v1/agentCards. Repeat for multiple names.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--include-root",
        action="store_true",
        help="Also GET / . This may fetch a Web UI HTML page, but still submits no task.",
    )
    parser.add_argument(
        "--include-task-history",
        action="store_true",
        help="Also GET /api/v1/tasks. This reads task history and may require authorization.",
    )
    parser.add_argument(
        "--rest",
        action="store_true",
        help=(
            "Also probe REST-gateway read paths with fake IDs: "
            "/api/v2/tasks/__sam_probe_missing_task__ and "
            "/api/v2/artifacts/?session_id=__sam_probe__."
        ),
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Additional GET path to probe, starting with /. Repeat as needed.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for HTTPS probes.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=16384,
        help="Maximum response bytes to read per probe. Default: 16384.",
    )
    return parser


def normalize_base_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit(f"--url must include scheme and host, got: {raw_url!r}")
    return raw_url.rstrip("/")


def classify_status(status: int | None, error: str | None = None) -> str:
    if status is None:
        return "unreachable" if error else "unknown"
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        return "redirect"
    if status in (401, 403):
        return "auth-required"
    if status == 404:
        return "missing"
    if status in (405, 422):
        return "endpoint-present-but-invalid-request"
    return "http-error"


def summarize_json(name: str, value: Any) -> Any:
    if name == "agent-cards" and isinstance(value, list):
        names = [item.get("name") for item in value if isinstance(item, dict) and item.get("name")]
        return {"count": len(value), "agent_names": names}
    if name == "version" and isinstance(value, dict):
        products = value.get("products")
        if isinstance(products, list):
            return {
                "products": [
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "version": item.get("version"),
                    }
                    for item in products
                    if isinstance(item, dict)
                ]
            }
        return value
    if isinstance(value, list):
        return {"type": "list", "count": len(value)}
    if isinstance(value, dict):
        keys = sorted(str(k) for k in value.keys())[:20]
        return {"type": "object", "keys": keys}
    return value


def decode_body(raw: bytes, content_type: str | None, name: str) -> tuple[Any | None, str | None]:
    if not raw:
        return None, None
    text = raw.decode("utf-8", errors="replace")
    looks_json = "json" in (content_type or "").lower() or text.lstrip().startswith(("{", "["))
    if looks_json:
        try:
            return summarize_json(name, json.loads(text)), None
        except json.JSONDecodeError:
            pass
    preview = " ".join(text.split())[:500]
    return None, preview or None


def get_probe(
    base_url: str,
    name: str,
    path: str,
    token: str | None,
    timeout: float,
    context: ssl.SSLContext | None,
    max_bytes: int,
) -> ProbeResult:
    if not path.startswith("/"):
        path = "/" + path
    url = base_url + path
    headers = {"Accept": "application/json, text/plain;q=0.8, */*;q=0.5"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    start = time.monotonic()
    status: int | None = None
    content_type: str | None = None
    raw = b""
    error: str | None = None
    try:
        with urlopen(request, timeout=timeout, context=context) as response:  # nosec: user-requested URL probe
            status = getattr(response, "status", response.getcode())
            content_type = response.headers.get("content-type")
            raw = response.read(max(0, max_bytes) + 1)
    except HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get("content-type") if exc.headers else None
        raw = exc.read(max(0, max_bytes) + 1)
        error = str(exc)
    except (URLError, TimeoutError, OSError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed_ms = int((time.monotonic() - start) * 1000)
    json_summary, body_preview = decode_body(raw[:max_bytes], content_type, name)
    if len(raw) > max_bytes and body_preview:
        body_preview += " ...<truncated>"
    return ProbeResult(
        name=name,
        path=path,
        url=url,
        status=status,
        classification=classify_status(status, error),
        elapsed_ms=elapsed_ms,
        content_type=content_type,
        json_summary=json_summary,
        body_preview=body_preview,
        error=error,
    )


def planned_probes(args: argparse.Namespace) -> list[tuple[str, str]]:
    probes: list[tuple[str, str]] = [
        ("health", "/health"),
        ("healthz", "/healthz"),
        ("readyz", "/readyz"),
        ("startup", "/startup"),
        ("version", "/api/v1/version"),
        ("agent-cards", "/api/v1/agentCards"),
    ]
    if args.include_root:
        probes.insert(0, ("root", "/"))
    if args.include_task_history:
        probes.append(("task-history", "/api/v1/tasks"))
    if args.rest:
        probes.extend(
            [
                ("rest-task-fake-id", "/api/v2/tasks/__sam_probe_missing_task__"),
                ("rest-artifacts-fake-session", "/api/v2/artifacts/?session_id=__sam_probe__"),
            ]
        )
    for index, path in enumerate(args.path, start=1):
        probes.append((f"custom-{index}", path))
    return probes


def analyze_agents(results: list[ProbeResult], expected: list[str]) -> dict[str, Any]:
    agent_probe = next((item for item in results if item.name == "agent-cards"), None)
    summary = agent_probe.json_summary if agent_probe else None
    names: list[str] = []
    if isinstance(summary, dict) and isinstance(summary.get("agent_names"), list):
        names = [str(name) for name in summary["agent_names"]]
    missing = []
    for expected_name in expected:
        if expected_name not in names and expected_name.lower() not in {name.lower() for name in names}:
            missing.append(expected_name)
    return {"available_agent_names": names, "expected_missing": missing}


def print_text_report(payload: dict[str, Any]) -> None:
    print(f"SAM gateway probe: {payload['base_url']}")
    print("No tasks submitted; GET probes only.")
    print()
    for item in payload["probes"]:
        status = item["status"] if item["status"] is not None else "-"
        print(f"[{item['classification']:<32}] {status!s:<4} {item['elapsed_ms']:>5} ms  {item['path']}  ({item['name']})")
        if item.get("json_summary") is not None:
            print(f"    json: {json.dumps(item['json_summary'], ensure_ascii=False)}")
        elif item.get("body_preview"):
            print(f"    body: {item['body_preview']}")
        if item.get("error") and item["classification"] == "unreachable":
            print(f"    error: {item['error']}")
    agent_analysis = payload.get("agent_analysis") or {}
    if agent_analysis.get("available_agent_names"):
        print()
        print("Agents: " + ", ".join(agent_analysis["available_agent_names"]))
    if agent_analysis.get("expected_missing"):
        print("Missing expected agents: " + ", ".join(agent_analysis["expected_missing"]))
    print()
    print("Summary: " + payload["summary"])


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    base_url = normalize_base_url(args.url)
    context = None
    if args.insecure and base_url.startswith("https://"):
        context = ssl._create_unverified_context()  # nosec: explicit user opt-in

    results = [
        get_probe(
            base_url=base_url,
            name=name,
            path=path,
            token=args.token,
            timeout=args.timeout,
            context=context,
            max_bytes=args.max_bytes,
        )
        for name, path in planned_probes(args)
    ]

    agent_analysis = analyze_agents(results, args.expect_agent)
    reachable = [item for item in results if item.status is not None]
    useful = [
        item
        for item in results
        if item.classification in {"ok", "redirect", "auth-required", "endpoint-present-but-invalid-request"}
    ]
    missing_expected = agent_analysis["expected_missing"]

    if not reachable:
        summary = "no probes reached the server"
        exit_code = 2
    elif missing_expected:
        summary = "gateway reachable, but one or more expected agents were not advertised"
        exit_code = 3
    elif useful:
        summary = "gateway reachable; inspect classifications for gateway type and auth requirements"
        exit_code = 0
    else:
        summary = "server reachable, but expected SAM gateway endpoints were not confirmed"
        exit_code = 1

    payload = {
        "base_url": base_url,
        "submitted_tasks": False,
        "used_token": bool(args.token),
        "probes": [asdict(item) for item in results],
        "agent_analysis": agent_analysis,
        "summary": summary,
        "exit_code": exit_code,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        print_text_report(payload)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
