#!/usr/bin/env python3
"""No-network import, constructor, and validation probe for DeepXiv Reader."""

from __future__ import annotations

import json
import sys
from typing import Callable


def expect_value_error(label: str, call: Callable[[], object]) -> str:
    try:
        call()
    except ValueError:
        return label
    raise AssertionError(f"expected ValueError: {label}")


def main() -> int:
    try:
        import deepxiv_sdk.reader as reader_module
        from deepxiv_sdk import Reader, __version__, agent_search_sources
    except ImportError as exc:
        print(json.dumps({"status": "import_error", "message": str(exc)}), file=sys.stderr)
        return 1

    # Replace both transport methods in this process. Any accidental network path
    # becomes a visible failure instead of touching the service.
    def forbidden_network(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("reader_probe must not make network requests")

    original_get = reader_module.requests.get
    original_post = reader_module.requests.post
    reader_module.requests.get = forbidden_network
    reader_module.requests.post = forbidden_network

    checks: list[str] = []
    try:
        reader = Reader()
        assert reader.base_url == "https://data.rag.ac.cn"
        assert reader.timeout == 60
        assert reader.max_retries == 3
        assert reader.retry_delay == 1.0
        assert reader.arxiv_endpoint.endswith("/arxiv/")
        assert reader.pmc_endpoint.endswith("/pmc/")
        assert reader.agent_search_endpoints["arxiv"].endswith("/arxiv/agent/search")
        assert reader.agent_search_endpoints["web"].endswith("/web/agent/search")
        checks.append("constructor_defaults_and_endpoints")

        checks.append(expect_value_error("search_blank_query", lambda: reader.search("")))
        checks.append(expect_value_error("search_size_bounds", lambda: reader.search("q", size=0)))
        checks.append(expect_value_error("search_offset_bounds", lambda: reader.search("q", offset=-1)))
        checks.append(expect_value_error("head_blank_id", lambda: reader.head(" ")))
        checks.append(expect_value_error("brief_blank_id", lambda: reader.brief("")))
        checks.append(expect_value_error("section_blank_name", lambda: reader.section("2409.05591", "")))
        checks.append(expect_value_error("agent_blank_query", lambda: list(reader.agent_search_stream(" "))))
        checks.append(expect_value_error(
            "agent_backend_flag_rejected",
            lambda: reader.agent_search("q", source="web", top_k=1),
        ))
        checks.append(expect_value_error(
            "agent_answer_cap_rejected",
            lambda: reader.agent_search("q", max_answer_tokens=255),
        ))

        arxiv_payload = reader._build_agent_search_payload(
            "  q  ", "arxiv", "default", False, True, 4096, None
        )
        assert arxiv_payload["query"] == "q"
        assert arxiv_payload["top_k"] == 10
        assert arxiv_payload["stream_answer"] is True
        checks.append("agent_arxiv_payload_defaults")

        web_payload = reader._build_agent_search_payload(
            "q", "web", "high", False, True, 4096, None,
            search_type="scholar", gl="us", hl="en",
        )
        assert web_payload["search_type"] == "scholar"
        assert web_payload["gl"] == "us" and web_payload["hl"] == "en"
        assert "top_k" not in web_payload
        checks.append("agent_web_payload_backend_options")

        assert agent_search_sources({"papers": [{"arxiv_id": "x"}]})[0]["arxiv_id"] == "x"
        assert agent_search_sources({"pages": [{"url": "https://example.invalid"}]})[0]["url"]
        assert agent_search_sources({"sources": [{"url": "x"}]}) == [{"url": "x"}]
        assert agent_search_sources({"event": "done"}) == []
        checks.append("source_normalization")
    finally:
        reader_module.requests.get = original_get
        reader_module.requests.post = original_post

    print(json.dumps({
        "status": "ok",
        "package_version": __version__,
        "base_url": reader.base_url,
        "checks": checks,
        "network_requests": 0,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
