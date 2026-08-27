#!/usr/bin/env python3
"""Safe Dagster GraphQL health-check helper."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from typing import Any

VERSION_QUERY = "query DagsterVersionHealthCheck { version }"
SERVER_INFO_QUERY = "query DagsterServerInfoHealthCheck { version }"
QUERY_CHOICES = {
    "version": VERSION_QUERY,
    "server-info": SERVER_INFO_QUERY,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a read-only Dagster GraphQL health query against a webserver URL, "
            "or print the equivalent dagster-graphql CLI command with --dry-run."
        )
    )
    parser.add_argument(
        "--url",
        required=True,
        help=(
            "Dagster webserver base URL, including scheme and any path prefix, "
            "for example http://localhost:3000 or http://localhost:3000/dagster."
        ),
    )
    parser.add_argument(
        "--query",
        choices=sorted(QUERY_CHOICES),
        default="version",
        help="Bundled read-only query to issue. Defaults to version.",
    )
    parser.add_argument(
        "--variables",
        default=None,
        help="Optional JSON object string for GraphQL variables. Usually unnecessary for health checks.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds for non-dry-run checks. Defaults to 10.",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help=(
            "Additional HTTP header for non-dry-run checks. May be repeated. "
            "Avoid passing secrets on shared shells."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the equivalent dagster-graphql --remote command without making a network request.",
    )
    return parser


def _normalize_base_url(raw_url: str) -> str:
    parsed = urllib.parse.urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--url must include http:// or https:// plus a host")
    return raw_url.rstrip("/")


def _parse_variables(raw_variables: str | None) -> dict[str, Any] | None:
    if raw_variables is None:
        return None
    try:
        parsed = json.loads(raw_variables)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--variables must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--variables must decode to a JSON object")
    return parsed


def _parse_headers(raw_headers: Sequence[str]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    for raw_header in raw_headers:
        if "=" not in raw_header:
            raise ValueError(f"--header must be NAME=VALUE, got {raw_header!r}")
        name, value = raw_header.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"--header name cannot be empty in {raw_header!r}")
        headers[name] = value.strip()
    return headers


def _shell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _print_dry_run_command(
    base_url: str,
    query: str,
    variables: dict[str, Any] | None,
    raw_headers: Sequence[str],
) -> bool:
    if raw_headers:
        print(
            "dagster-graphql does not support arbitrary HTTP headers; "
            "omit --header for CLI dry-run output or run this helper without --dry-run.",
            file=sys.stderr,
        )
        return False

    command = [
        "dagster-graphql",
        "--remote",
        _shell_single_quote(base_url),
        "--text",
        _shell_single_quote(query),
    ]
    if variables is not None:
        command.extend(["--variables", _shell_single_quote(json.dumps(variables, sort_keys=True))])
    print(" ".join(command))
    return True


def _execute_query(
    base_url: str,
    query: str,
    variables: dict[str, Any] | None,
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    graphql_url = urllib.parse.urljoin(base_url + "/", "graphql")
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(graphql_url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
    decoded = json.loads(response_body)
    if not isinstance(decoded, dict):
        raise ValueError("GraphQL response did not decode to a JSON object")
    return decoded


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        base_url = _normalize_base_url(args.url)
        variables = _parse_variables(args.variables)
        headers = _parse_headers(args.header)
    except ValueError as exc:
        parser.error(str(exc))

    query = QUERY_CHOICES[args.query]

    if args.dry_run:
        return 0 if _print_dry_run_command(base_url, query, variables, args.header) else 2

    try:
        result = _execute_query(base_url, query, variables, headers, args.timeout)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error from Dagster GraphQL endpoint: {exc.code} {exc.reason}", file=sys.stderr)
        return 2
    except urllib.error.URLError as exc:
        print(f"Could not reach Dagster GraphQL endpoint: {exc.reason}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"GraphQL endpoint did not return JSON: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
