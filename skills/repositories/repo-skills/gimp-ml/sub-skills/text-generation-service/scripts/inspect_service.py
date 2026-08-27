#!/usr/bin/env python3
"""Inspect the bundled service protocol without a source checkout.

Safe operations are limited to static route listing, port-only validation of an
operator-supplied JSON configuration, and an optional GET /status probe against
an explicitly supplied loopback HTTP endpoint. The tool never starts a server,
issues POST requests, accesses credential fields, or prints response bodies.
"""
from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

EXPECTED_ROUTES = (
    (
        "GET",
        "/status",
        "no request body",
        "object fields: service, cuda_available, cuda_total, cuda_used, "
        "cuda_free, ram_total, ram_used, ram_free, cpu, os",
    ),
    (
        "POST",
        "/download_load_model",
        "JSON fields: pipeline, model",
        'object field: status (observed values "Loaded." or "Error!")',
    ),
    (
        "POST",
        "/run_inference",
        "pipeline-specific JSON; exact fields are in the bundled API reference",
        "object fields: image, image_shape, text",
    ),
)
STATUS_FIELDS = (
    "service",
    "cuda_available",
    "cuda_total",
    "cuda_used",
    "cuda_free",
    "ram_total",
    "ram_used",
    "ram_free",
    "cpu",
    "os",
)
MAX_CONFIG_BYTES = 1024 * 1024
MAX_STATUS_BYTES = 1024 * 1024


class ProtocolError(ValueError):
    """Raised for an invalid local inspection input or protocol response."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the self-contained GIMP-ML service contract. List static "
            "routes, validate only gimpml.port in a supplied JSON config, or "
            "probe only GET /status on an explicit loopback HTTP endpoint."
        )
    )
    parser.add_argument(
        "--list-routes",
        action="store_true",
        help="List the three built-in expected routes without importing or contacting a service.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        metavar="JSON_FILE",
        help=(
            "Validate and print only gimpml.port from this operator-supplied JSON file; "
            "all unrelated object fields are discarded and never displayed."
        ),
    )
    parser.add_argument(
        "--probe-status",
        metavar="LOOPBACK_URL",
        help=(
            "Issue only GET /status to an explicit loopback URL with an explicit port, "
            "for example http://127.0.0.1:61482."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Status-probe timeout from 0.1 through 5 seconds (default: 2).",
    )
    args = parser.parse_args()
    if not (args.list_routes or args.config is not None or args.probe_status):
        parser.error("choose at least one of --list-routes, --config, or --probe-status")
    if not 0.1 <= args.timeout <= 5.0:
        parser.error("--timeout must be from 0.1 through 5 seconds")
    return args


def list_routes() -> None:
    print("Expected route contract (static bundled evidence; no service contacted):")
    for method, path, request, response in EXPECTED_ROUTES:
        print(f"  {method:4} {path}")
        print(f"       request:  {request}")
        print(f"       response: {response}")
    print("POST routes are listed only; this inspector never calls them.")


def _port_only_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Discard unrelated JSON object members during decoding.

    The JSON decoder must parse the document to validate its syntax, but this
    hook retains only the structural names needed to locate gimpml.port. Other
    values are neither inspected by application code nor emitted.
    """

    result: dict[str, Any] = {}
    seen: set[str] = set()
    for key, value in pairs:
        if key in seen:
            raise ProtocolError("configuration contains a duplicate object key")
        seen.add(key)
        if key in {"gimpml", "port"}:
            result[key] = value
    return result


def _reject_json_constant(_value: str) -> None:
    raise ProtocolError("configuration contains a non-standard JSON constant")


def validate_config(path: Path) -> int:
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise ProtocolError("configuration file does not exist") from exc
    except OSError as exc:
        raise ProtocolError(f"cannot inspect configuration file metadata: {exc}") from exc
    if size > MAX_CONFIG_BYTES:
        raise ProtocolError("configuration exceeds the 1 MiB inspection limit")

    try:
        with path.open("r", encoding="utf-8") as handle:
            config = json.load(
                handle,
                object_pairs_hook=_port_only_object,
                parse_constant=_reject_json_constant,
            )
    except UnicodeDecodeError as exc:
        raise ProtocolError("configuration is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(
            f"configuration is not valid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    except OSError as exc:
        raise ProtocolError(f"cannot read configuration file: {exc}") from exc

    if not isinstance(config, dict):
        raise ProtocolError("configuration must be a JSON object")
    namespace = config.get("gimpml")
    if not isinstance(namespace, dict):
        raise ProtocolError("configuration must contain an object at gimpml")
    port = namespace.get("port")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ProtocolError("gimpml.port must be an integer from 1 through 65535")

    print(f"Config OK: gimpml.port={port}")
    print("Only gimpml.port was retained; unrelated fields were not inspected or displayed.")
    return port


def _resolve_loopback(host: str, port: int) -> tuple[str, int]:
    normalized = host.rstrip(".").lower()
    if normalized == "localhost":
        try:
            records = socket.getaddrinfo(
                normalized,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ProtocolError("localhost could not be resolved") from exc
        addresses = {record[4][0].split("%", 1)[0] for record in records}
        if not addresses:
            raise ProtocolError("localhost did not resolve to an address")
        parsed = [ipaddress.ip_address(address) for address in addresses]
        if not all(address.is_loopback for address in parsed):
            raise ProtocolError("localhost resolved to a non-loopback address")
        preferred = sorted(parsed, key=lambda address: (address.version != 4, str(address)))[0]
        return str(preferred), preferred.version

    try:
        address = ipaddress.ip_address(normalized.split("%", 1)[0])
    except ValueError as exc:
        raise ProtocolError(
            "probe host must be localhost or a literal loopback IP address"
        ) from exc
    if not address.is_loopback:
        raise ProtocolError("non-loopback probe hosts are rejected")
    return str(address), address.version


def parse_probe_url(value: str) -> tuple[str, str, int, int]:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ProtocolError("probe URL has an invalid port or host") from exc
    if parsed.scheme != "http":
        raise ProtocolError("probe URL must use http")
    if not parsed.netloc or not parsed.hostname:
        raise ProtocolError("probe URL must include a host and explicit port")
    if parsed.username is not None or parsed.password is not None:
        raise ProtocolError("probe URL must not contain credentials")
    if port is None:
        raise ProtocolError("probe URL must include an explicit port")
    if parsed.query or parsed.fragment:
        raise ProtocolError("probe URL must not contain a query or fragment")
    if parsed.path not in {"", "/", "/status"}:
        raise ProtocolError("probe URL path must be empty, /, or /status")
    connect_host, address_version = _resolve_loopback(parsed.hostname, port)
    return parsed.hostname, connect_host, address_version, port


def probe_status(value: str, timeout: float) -> None:
    display_host, connect_host, address_version, port = parse_probe_url(value)
    host_header_name = f"[{display_host}]" if ":" in display_host else display_host
    connection = http.client.HTTPConnection(connect_host, port, timeout=timeout)
    try:
        connection.request(
            "GET",
            "/status",
            headers={
                "Accept": "application/json",
                "Host": f"{host_header_name}:{port}",
                "User-Agent": "gimp-ml-local-protocol-inspector/1",
            },
        )
        response = connection.getresponse()
        body = response.read(MAX_STATUS_BYTES + 1)
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        reason = type(exc).__name__
        if isinstance(exc, OSError) and exc.strerror:
            reason = exc.strerror
        raise ConnectionError(
            f"loopback service is not reachable on port {port} ({reason})"
        ) from exc
    finally:
        connection.close()

    if len(body) > MAX_STATUS_BYTES:
        raise ProtocolError("GET /status response exceeds the 1 MiB inspection limit")
    if response.status != 200:
        raise ProtocolError(f"GET /status returned HTTP {response.status}; body was not printed")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("GET /status did not return a valid JSON document") from exc
    if not isinstance(payload, dict):
        raise ProtocolError("GET /status JSON must be an object")

    missing = [field for field in STATUS_FIELDS if field not in payload]
    if missing:
        raise ProtocolError(
            "GET /status is missing expected fields: " + ", ".join(missing)
        )
    unexpected_count = len(set(payload) - set(STATUS_FIELDS))
    family = "IPv4" if address_version == 4 else "IPv6"
    print(
        f"Status OK: GET /status returned HTTP 200 from loopback {family} port {port}; "
        f"expected_fields={len(STATUS_FIELDS)}/{len(STATUS_FIELDS)}; "
        f"unexpected_field_count={unexpected_count}."
    )
    print("Response values and unrecognized field names were not printed.")


def main() -> int:
    args = parse_args()
    try:
        if args.list_routes:
            list_routes()
        if args.config is not None:
            validate_config(args.config.expanduser())
        if args.probe_status:
            probe_status(args.probe_status, args.timeout)
        return 0
    except ConnectionError as exc:
        print(f"BLOCKED: {exc}. Supply an operator-provided running local service.", file=sys.stderr)
        return 4
    except ProtocolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
