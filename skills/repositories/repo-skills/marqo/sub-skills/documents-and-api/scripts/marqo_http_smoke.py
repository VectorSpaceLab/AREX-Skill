#!/usr/bin/env python3
"""Print or optionally send safe Marqo HTTP smoke requests.

Default behavior is print-only: no network calls are made unless --send is
provided. The --send sequence creates, mutates, and deletes the named index, so
use a fresh throwaway index name against a service you intend to exercise.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

try:  # Optional nicer HTTP client if available; urllib fallback is stdlib.
    import httpx  # type: ignore
except Exception:  # pragma: no cover - fallback path is intentional.
    httpx = None  # type: ignore


@dataclass(frozen=True)
class RequestSpec:
    method: str
    path: str
    body: Optional[Any] = None
    note: str = ""


@dataclass(frozen=True)
class ResponseSummary:
    status_code: int
    text: str
    headers: Dict[str, str]


def _index_path(index_name: str) -> str:
    return f"/indexes/{quote(index_name, safe='')}"


def build_request_plan(index_name: str) -> List[RequestSpec]:
    """Build a route-level smoke plan with small JSON payloads."""
    index = _index_path(index_name)
    doc_1 = quote("doc-1", safe="")

    docs_body = {
        "documents": [
            {
                "_id": "doc-1",
                "title": "Marqo API smoke",
                "text": "Documents can be added and read back.",
                "category": "demo",
            },
            {
                "_id": "doc-2",
                "title": "Typeahead smoke",
                "text": "Typeahead query examples use separate suggestion routes.",
                "category": "demo",
            },
        ],
        "tensorFields": ["title", "text"],
    }

    typeahead_queries = {
        "queries": [
            {"query": "marqo api smoke", "popularity": 10.0, "metadata": {"source": 1.0}},
            {"query": "marqo document workflows", "popularity": 5.0},
        ]
    }

    return [
        RequestSpec("GET", "/", note="Root metadata; no index needed."),
        RequestSpec("GET", "/health", note="Whole-service health."),
        RequestSpec("GET", "/indexes", note="List indexes."),
        RequestSpec(
            "POST",
            index,
            {"type": "semi-structured", "model": "random/small"},
            note="Create a throwaway semi-structured index using a small random model.",
        ),
        RequestSpec("GET", f"{index}/settings", note="Read settings for the created index."),
        RequestSpec("POST", f"{index}/documents", docs_body, note="Add two sample documents."),
        RequestSpec("PATCH", f"{index}/documents", {"documents": [{"_id": "doc-1", "category": "updated-demo"}]}, note="Partial update."),
        RequestSpec("GET", f"{index}/documents/{doc_1}?expose_facets=false", note="Get one document."),
        RequestSpec("POST", f"{index}/documents/get-batch", {"documentIds": ["doc-1", "doc-2"]}, note="Get documents by batch body."),
        RequestSpec("POST", f"{index}/embed", {"content": "api smoke query", "contentType": "query"}, note="Embed minimal query content."),
        RequestSpec("POST", f"{index}/search", {"q": "api smoke", "searchMethod": "TENSOR", "limit": 2}, note="Minimal route-level search smoke; ranking details are out of scope."),
        RequestSpec("POST", f"{index}/recommend", {"documents": ["doc-1"], "limit": 2}, note="Recommend from an indexed document vector."),
        RequestSpec("POST", f"{index}/suggestions/queries", typeahead_queries, note="Index typeahead query strings."),
        RequestSpec("POST", f"{index}/suggestions", {"q": "marqo", "limit": 5}, note="Fetch suggestions."),
        RequestSpec("GET", f"{index}/suggestions/stats", note="Count typeahead queries."),
        RequestSpec("GET", f"{index}/suggestions/queries", ["marqo api smoke"], note="Fetch exact typeahead query records."),
        RequestSpec("DELETE", f"{index}/suggestions/queries", ["marqo api smoke", "marqo document workflows"], note="Delete selected typeahead queries."),
        RequestSpec("GET", f"{index}/stats", note="Read index stats after document operations."),
        RequestSpec("POST", f"{index}/documents/delete-batch", ["doc-1", "doc-2"], note="Delete sample documents."),
        RequestSpec("DELETE", index, note="Delete the throwaway index."),
    ]


def full_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def format_body(body: Optional[Any]) -> str:
    if body is None:
        return "<none>"
    return json.dumps(body, indent=2, sort_keys=True)


def print_request(index: int, spec: RequestSpec, base_url: str) -> None:
    print(f"[{index:02d}] {spec.method} {full_url(base_url, spec.path)}")
    if spec.note:
        print(textwrap.indent(f"# {spec.note}", "     "))
    body_text = format_body(spec.body)
    if spec.body is None:
        print("     body: <none>")
    else:
        print("     body:")
        print(textwrap.indent(body_text, "       "))


def print_plan(plan: List[RequestSpec], base_url: str) -> None:
    print("# Marqo HTTP smoke plan")
    print("# Mode: print-only. No network requests were sent.")
    for i, spec in enumerate(plan, start=1):
        print_request(i, spec, base_url)


def truncate(text: str, max_chars: int = 1600) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... truncated {len(text) - max_chars} characters ..."


def send_with_httpx(spec: RequestSpec, base_url: str, timeout: float) -> ResponseSummary:
    if httpx is None:
        raise RuntimeError("httpx is unavailable")
    url = full_url(base_url, spec.path)
    try:
        with httpx.Client(timeout=timeout) as client:  # type: ignore[attr-defined]
            response = client.request(spec.method, url, json=spec.body if spec.body is not None else None)
    except Exception as exc:  # httpx may not be importable in minimal environments.
        raise RuntimeError(f"Service unreachable or HTTP client error for {spec.method} {url}: {exc}") from exc
    return ResponseSummary(response.status_code, response.text, dict(response.headers))


def send_with_urllib(spec: RequestSpec, base_url: str, timeout: float) -> ResponseSummary:
    url = full_url(base_url, spec.path)
    data = None
    headers: Dict[str, str] = {}
    if spec.body is not None:
        data = json.dumps(spec.body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=spec.method)
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec: caller controls --base-url for smoke testing.
            body = response.read().decode("utf-8", errors="replace")
            return ResponseSummary(response.status, body, dict(response.headers.items()))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return ResponseSummary(exc.code, body, dict(exc.headers.items()))
    except URLError as exc:
        raise RuntimeError(f"Service unreachable for {spec.method} {url}: {exc}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Timed out while contacting {url}") from exc


def send_request(spec: RequestSpec, base_url: str, timeout: float) -> ResponseSummary:
    if httpx is not None:
        return send_with_httpx(spec, base_url, timeout)
    # urllib is part of the Python standard library. If this path fails to import
    # in a constrained runtime, the top-level import error will be explicit.
    return send_with_urllib(spec, base_url, timeout)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print or optionally send a safe Marqo documents/API HTTP smoke sequence.",
    )
    parser.add_argument("--base-url", default="http://localhost:8882", help="Marqo API base URL. Default: http://localhost:8882")
    parser.add_argument("--index-name", default="documents-and-api-smoke", help="Throwaway index name used in generated routes.")
    parser.add_argument("--print-only", action="store_true", help="Print HTTP method/path/body without network requests. This is the default unless --send is set.")
    parser.add_argument("--send", action="store_true", help="Send the smoke requests to --base-url. This mutates and deletes --index-name.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds for --send. Default: 10.")
    args = parser.parse_args(argv)
    if args.send and args.print_only:
        parser.error("--send and --print-only are mutually exclusive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    plan = build_request_plan(args.index_name)

    if not args.send:
        print_plan(plan, args.base_url)
        return 0

    print("# Marqo HTTP smoke plan")
    print("# Mode: send. Requests will mutate the named index.")
    for i, spec in enumerate(plan, start=1):
        print_request(i, spec, args.base_url)
        try:
            response = send_request(spec, args.base_url, args.timeout)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            print("If an index was already created, delete it manually or rerun with a fresh --index-name.", file=sys.stderr)
            return 2

        print(f"     response: HTTP {response.status_code}")
        if response.text:
            print(textwrap.indent(truncate(response.text), "       "))
        if response.status_code >= 400:
            print("ERROR: stopping after failed HTTP response. Inspect the response body above.", file=sys.stderr)
            print("If an index was already created, delete it manually or rerun with a fresh --index-name.", file=sys.stderr)
            return 1

    print("# Completed Marqo HTTP smoke sequence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
