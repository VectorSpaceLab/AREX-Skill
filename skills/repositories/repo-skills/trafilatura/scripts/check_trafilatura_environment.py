#!/usr/bin/env python3
"""No-network Trafilatura environment check.

The check verifies import/version metadata, a small Python API extraction,
metadata and deduplication helpers, and CLI help via the current Python. It does
not contact the network and does not require the original source checkout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

HTML = """<!doctype html>
<html lang="en">
<head>
  <title>Trafilatura Environment Fixture</title>
  <meta name="author" content="Environment Check">
  <meta property="article:published_time" content="2024-01-02">
</head>
<body>
  <nav>Navigation noise.</nav>
  <article>
    <h1>Trafilatura Environment Fixture</h1>
    <p>{body}</p>
    <p>A second paragraph includes enough local content for extraction without network access.</p>
  </article>
</body>
</html>
""".format(
    body=" ".join(
        [
            "This local article paragraph verifies Trafilatura extraction, metadata, and output serialization."
        ]
        * 16
    )
)


def check_imports() -> dict[str, str]:
    try:
        dist_version = version("trafilatura")
    except PackageNotFoundError as exc:
        raise AssertionError("The trafilatura distribution is not installed for this Python") from exc

    import trafilatura

    module_version = getattr(trafilatura, "__version__", "unknown")
    exports = getattr(trafilatura, "__all__", [])
    required = {"extract", "bare_extraction", "fetch_url", "fetch_response", "html2txt", "extract_metadata"}
    missing = sorted(required.difference(exports))
    if missing:
        raise AssertionError(f"trafilatura.__all__ missing expected exports: {missing}")
    return {"distribution": dist_version, "module": module_version}


def check_api() -> None:
    from trafilatura import bare_extraction, extract, extract_metadata, html2txt
    from trafilatura.deduplication import Simhash, content_fingerprint
    from trafilatura.settings import Extractor

    text = extract(HTML, output_format="txt", include_comments=False)
    assert text and "local article paragraph" in text, "text extraction did not include fixture paragraph"

    markdown = extract(HTML, output_format="markdown", with_metadata=True)
    assert markdown and markdown.startswith("---") and "# Trafilatura Environment Fixture" in markdown

    json_output = extract(HTML, output_format="json", with_metadata=True)
    parsed = json.loads(json_output or "{}")
    assert "Trafilatura Environment Fixture" in json.dumps(parsed), "JSON output missing fixture title"

    doc = bare_extraction(HTML, output_format="python", with_metadata=True)
    assert doc is not None and doc.title == "Trafilatura Environment Fixture"

    metadata = extract_metadata(HTML)
    assert metadata.title == "Trafilatura Environment Fixture"

    assert "Navigation noise" in html2txt(HTML), "html2txt should expose broad text content"
    assert len(content_fingerprint(text)) == 16
    assert Simhash(text).similarity(Simhash(text)) == 1.0
    options = Extractor(output_format="json", with_metadata=True, dedup=True)
    assert options.format == "json" and options.with_metadata and options.dedup


def check_cli(timeout: float) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "trafilatura.cli", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")
    if completed.returncode != 0:
        raise AssertionError(f"CLI help failed with exit {completed.returncode}: {stderr[:1000]}")
    for flag in ("--input-file", "--input-dir", "--sitemap", "--crawl", "--json", "--xmltei"):
        assert flag in stdout, f"CLI help missing expected flag {flag}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a no-network Trafilatura environment smoke check.")
    parser.add_argument("--skip-cli", action="store_true", help="skip the CLI help check")
    parser.add_argument("--timeout", type=float, default=30.0, help="CLI subprocess timeout in seconds")
    parser.add_argument("--json", action="store_true", help="print a JSON summary instead of a short text line")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    versions = check_imports()
    check_api()
    cli_status = "skipped" if args.skip_cli else "passed"
    if not args.skip_cli:
        check_cli(args.timeout)
    summary = {
        "status": "ok",
        "distribution_version": versions["distribution"],
        "module_version": versions["module"],
        "api_smoke": "passed",
        "cli_help": cli_status,
        "network": "not used",
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            "trafilatura-environment-ok "
            f"version={summary['distribution_version']} api={summary['api_smoke']} cli={summary['cli_help']} network={summary['network']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
