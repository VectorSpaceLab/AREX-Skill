#!/usr/bin/env python3
"""
No-network smoke test for the Trafilatura Python extraction APIs.

Usage:
    python extraction_smoke.py
    python extraction_smoke.py --show-output

The script builds an in-memory HTML fixture and asserts:
- plain text extraction removes navigation/comment noise when requested,
- JSON extraction includes metadata fields,
- Markdown extraction includes a metadata header and link markup,
- bare_extraction returns a Document with text and metadata,
- extract_metadata returns metadata without text extraction,
- html2txt returns broad visible text.

It requires an environment where `trafilatura` is installed. It does not perform
network access and does not read repository fixtures.
"""

from __future__ import annotations

import argparse
import json
import sys
from textwrap import dedent

FIXTURE_URL = "https://example.org/news/trafilatura-python-api"
FIXTURE_HTML = dedent(
    """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Trafilatura Python API Smoke</title>
        <meta name="author" content="Ada Example">
        <meta name="description" content="A no-network smoke fixture for extraction.">
        <meta property="article:published_time" content="2024-05-02T09:30:00Z">
        <link rel="canonical" href="https://example.org/news/trafilatura-python-api">
      </head>
      <body>
        <nav>Home | Search | Login</nav>
        <article>
          <h1>Trafilatura Python API Smoke</h1>
          <p>This article explains how to validate Trafilatura extraction using a bundled fixture.</p>
          <p>The main paragraph contains a <a href="/docs">documentation link</a> and enough text for stable extraction.</p>
          <p>A second substantial paragraph keeps the main extraction above fallback thresholds so inclusion flags can be checked deterministically in this smoke test.</p>
          <table><tr><th>Metric</th><td>Covered</td></tr></table>
        </article>
        <section class="comments">
          <p>This reader comment should be omitted when include_comments is false.</p>
        </section>
        <footer>Boilerplate footer text</footer>
      </body>
    </html>
    """
).strip()


def assert_contains(haystack: str | None, needle: str, label: str) -> None:
    if haystack is None or needle not in haystack:
        raise AssertionError(f"missing {label!r}: expected {needle!r} in {haystack!r}")


def run_smoke(show_output: bool = False) -> dict[str, str]:
    try:
        from trafilatura import bare_extraction, extract, extract_metadata, html2txt
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "The 'trafilatura' package is not importable. Install trafilatura before running this smoke test."
        ) from exc

    text = extract(FIXTURE_HTML, include_comments=False, include_tables=False)
    assert_contains(text, "bundled fixture", "plain text main article")
    if "reader comment" in (text or ""):
        raise AssertionError("plain text unexpectedly included comments")
    if "Metric" in (text or ""):
        raise AssertionError("plain text unexpectedly included table content")

    json_output = extract(
        FIXTURE_HTML,
        url=FIXTURE_URL,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
    )
    assert json_output is not None, "JSON extraction returned None"
    record = json.loads(json_output)
    assert record["title"] == "Trafilatura Python API Smoke"
    assert record["author"] == "Ada Example"
    assert record["date"] == "2024-05-02"
    assert record["source"] == FIXTURE_URL
    assert "bundled fixture" in record["text"]
    assert "reader comment" not in record.get("comments", "")

    markdown = extract(
        FIXTURE_HTML,
        url=FIXTURE_URL,
        output_format="markdown",
        with_metadata=True,
        include_comments=False,
        include_links=True,
    )
    assert_contains(markdown, "---\ntitle: Trafilatura Python API Smoke", "Markdown metadata header")
    assert_contains(markdown, "2024-05-02", "Markdown date metadata")
    if "[documentation link]" not in (markdown or ""):
        raise AssertionError(f"Markdown did not preserve link text/markup: {markdown!r}")

    doc = bare_extraction(FIXTURE_HTML, url=FIXTURE_URL, with_metadata=True, include_comments=False)
    assert doc is not None, "bare_extraction returned None"
    assert doc.title == "Trafilatura Python API Smoke"
    assert doc.author == "Ada Example"
    assert doc.date == "2024-05-02"
    assert doc.url == FIXTURE_URL
    assert doc.text and "main paragraph" in doc.text

    meta = extract_metadata(FIXTURE_HTML, default_url=FIXTURE_URL)
    assert meta.title == "Trafilatura Python API Smoke"
    assert meta.author == "Ada Example"
    assert meta.date == "2024-05-02"
    assert meta.url == FIXTURE_URL

    broad_text = html2txt(FIXTURE_HTML)
    assert_contains(broad_text, "Home", "html2txt broad navigation text")
    assert_contains(broad_text, "reader comment", "html2txt broad comment text")

    outputs = {
        "text": text or "",
        "json": json_output,
        "markdown": markdown or "",
        "bare_text": doc.text or "",
        "html2txt": broad_text,
    }
    if show_output:
        for name, value in outputs.items():
            print(f"\n## {name}\n{value}")
    return outputs


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a no-network Trafilatura Python extraction smoke test.")
    parser.add_argument("--show-output", action="store_true", help="print extracted outputs after assertions pass")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_smoke(show_output=args.show_output)
    print("OK: Trafilatura Python extraction smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
