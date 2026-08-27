#!/usr/bin/env python3
"""Safe status-only checks for M-flow service integrations.

This script never starts, stops, restarts, or kills services.
It inspects local processes, ports, and health URLs for the common
service surfaces used by the service-integrations sub-skill.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ServiceTarget:
    name: str
    description: str
    process_patterns: tuple[str, ...] = ()
    ports: tuple[int, ...] = ()
    health_urls: tuple[str, ...] = ()


@dataclass
class ProbeResult:
    name: str
    status: str
    description: str
    process_matches: list[str] = field(default_factory=list)
    open_ports: list[int] = field(default_factory=list)
    url_checks: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


TARGETS: dict[str, ServiceTarget] = {
    "api": ServiceTarget(
        name="api",
        description="FastAPI backend",
        process_patterns=(r"uvicorn.*m_flow\.api\.client:app", r"m_flow\.api\.client:app", r"python.*m_flow/api/client.py"),
        ports=(8000,),
        health_urls=("http://127.0.0.1:8000/health", "http://127.0.0.1:8000/health/detailed"),
    ),
    "frontend": ServiceTarget(
        name="frontend",
        description="Next.js web console",
        process_patterns=(r"next dev", r"next start", r"pnpm dev", r"npm run dev"),
        ports=(3000,),
        health_urls=("http://127.0.0.1:3000",),
    ),
    "mcp": ServiceTarget(
        name="mcp",
        description="MCP server",
        process_patterns=(r"m_flow-mcp", r"src/server.py", r"python.*m_flow-mcp"),
        ports=(8001,),
        health_urls=("http://127.0.0.1:8001/health",),
    ),
    "neo4j": ServiceTarget(name="neo4j", description="Neo4j graph service", ports=(7474, 7687)),
    "postgres": ServiceTarget(name="postgres", description="Postgres/pgvector", ports=(5432,)),
    "chromadb": ServiceTarget(name="chromadb", description="ChromaDB vector service", ports=(3002,)),
    "redis": ServiceTarget(name="redis", description="Redis cache", ports=(6379,)),
    "fanjing-face": ServiceTarget(
        name="fanjing-face",
        description="Face-recognition companion",
        process_patterns=(r"fanjing-face-recognition", r"run_web_v2.py"),
        ports=(5001,),
        health_urls=("http://127.0.0.1:5001/api/stats", "http://127.0.0.1:5001/"),
    ),
}


def _probe_processes(patterns: tuple[str, ...]) -> list[str]:
    if not patterns:
        return []

    matches: list[str] = []
    if shutil.which("pgrep"):
        for pattern in patterns:
            proc = subprocess.run(["pgrep", "-af", pattern], capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout.strip():
                matches.extend([line.strip() for line in proc.stdout.splitlines() if line.strip()])
        return _dedupe(matches)

    ps = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True, text=True)
    if ps.returncode != 0:
        return []

    for line in ps.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(re.search(pattern, line) for pattern in patterns):
            matches.append(line)
    return _dedupe(matches)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _probe_port(port: int, timeout: float) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_url(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(200).decode("utf-8", errors="replace")
            return {
                "url": url,
                "reachable": True,
                "status_code": getattr(response, "status", 200),
                "ok": 200 <= getattr(response, "status", 200) < 400,
                "body_snippet": body.strip(),
            }
    except HTTPError as exc:
        body = exc.read(200).decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        return {
            "url": url,
            "reachable": True,
            "status_code": exc.code,
            "ok": exc.code < 500,
            "body_snippet": body.strip(),
        }
    except URLError as exc:
        return {"url": url, "reachable": False, "status_code": None, "ok": False, "error": str(exc.reason)}
    except Exception as exc:  # pragma: no cover - defensive
        return {"url": url, "reachable": False, "status_code": None, "ok": False, "error": str(exc)}


def _evaluate_target(target: ServiceTarget, timeout: float) -> ProbeResult:
    process_matches = _probe_processes(target.process_patterns)
    open_ports = [port for port in target.ports if _probe_port(port, timeout)]
    url_checks = [_probe_url(url, timeout) for url in target.health_urls]

    url_ok = any(check.get("ok") for check in url_checks)
    port_ok = bool(open_ports)
    process_ok = bool(process_matches)

    if url_ok or (port_ok and process_ok) or (port_ok and not target.health_urls):
        status = "up"
    elif port_ok or process_ok or any(check.get("reachable") for check in url_checks):
        status = "degraded"
    else:
        status = "down"

    notes: list[str] = []
    if target.process_patterns and not process_ok:
        notes.append("no matching process found")
    if target.ports and not port_ok:
        notes.append("no open port found")
    if target.health_urls and not url_ok:
        notes.append("no healthy URL probe")

    return ProbeResult(
        name=target.name,
        status=status,
        description=target.description,
        process_matches=process_matches,
        open_ports=open_ports,
        url_checks=url_checks,
        notes=notes,
    )


def _print_text(results: list[ProbeResult]) -> None:
    width = max(len(result.name) for result in results) if results else 4
    for result in results:
        print(f"{result.name:<{width}}  {result.status.upper():<8}  {result.description}")
        if result.process_matches:
            print(f"  processes: {len(result.process_matches)} match(es)")
        if result.open_ports:
            print(f"  ports: {', '.join(str(port) for port in result.open_ports)}")
        for check in result.url_checks:
            if check.get("reachable"):
                print(f"  url: {check['url']} -> {check.get('status_code')} { 'ok' if check.get('ok') else 'not-ok' }")
            else:
                print(f"  url: {check['url']} -> unreachable")
        if result.notes:
            print(f"  notes: {', '.join(result.notes)}")
        print()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check M-flow service status without mutating anything.")
    parser.add_argument(
        "--service",
        action="append",
        choices=sorted(TARGETS),
        help="Check only selected services; repeatable.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any requested service is down.")
    parser.add_argument("--timeout", type=float, default=1.5, help="Per-port and per-URL timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    selected = args.service or list(TARGETS)
    results = [_evaluate_target(TARGETS[name], timeout=args.timeout) for name in selected]

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, ensure_ascii=False))
    else:
        _print_text(results)

    if args.strict and any(result.status == "down" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
