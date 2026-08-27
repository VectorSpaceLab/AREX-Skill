#!/usr/bin/env python3
"""No-network smoke checks for Trafilatura corpus-quality workflows.

Run from this sub-skill directory with:
    python scripts/corpus_quality_smoke.py

The script assumes trafilatura is installed in the active Python environment.
It does not download pages or read the original repository checkout.
"""

from __future__ import annotations

import csv
import json
from io import StringIO

from lxml import etree
from lxml.etree import fromstring

from trafilatura import extract
from trafilatura.deduplication import Simhash, content_fingerprint, duplicate_test
from trafilatura.meta import reset_caches
from trafilatura.settings import Extractor, use_config
from trafilatura.xml import validate_tei


HTML_FIXTURE = """<!doctype html>
<html lang="en">
  <head>
    <title>Corpus Smoke Article</title>
    <meta name="author" content="Ada Example">
    <meta name="description" content="A tiny corpus-quality smoke-test article.">
    <meta property="article:published_time" content="2024-01-02T00:00:00Z">
  </head>
  <body>
    <article>
      <h1>Corpus Smoke Article</h1>
      <p>Corpus smoke main paragraph with enough distinctive words for extraction.</p>
      <p>The second paragraph keeps the document long enough and useful for output validation.</p>
    </article>
    <footer>Repeated site footer boilerplate should not dominate the article.</footer>
  </body>
</html>
"""


def low_threshold_config():
    """Return a config that keeps the tiny local fixture extractable."""
    config = use_config()
    config["DEFAULT"]["MIN_EXTRACTED_SIZE"] = "1"
    config["DEFAULT"]["MIN_OUTPUT_SIZE"] = "1"
    config["DEFAULT"]["MIN_EXTRACTED_COMM_SIZE"] = "1"
    config["DEFAULT"]["MIN_OUTPUT_COMM_SIZE"] = "1"
    config["DEFAULT"]["MIN_DUPLCHECK_SIZE"] = "1"
    config["DEFAULT"]["MAX_REPETITIONS"] = "0"
    return config


def check_hashes_and_simhash() -> None:
    text = "The same corpus article text appears here with meaningful tokens."
    near = "The same corpus article text appears here with meaningful token changes."
    far = "Completely different sports coverage and unrelated vocabulary."

    fp1 = content_fingerprint(text)
    fp2 = content_fingerprint(text)
    assert isinstance(fp1, str) and fp1
    assert fp1 == fp2

    base = Simhash(text)
    near_hash = Simhash(near)
    far_hash = Simhash(far)
    assert base.similarity(base) == 1.0
    assert base.similarity(near_hash) > base.similarity(far_hash)
    assert Simhash(existing_hash=base.to_hex()).similarity(base) == 1.0


def check_exact_duplicate_detection() -> None:
    reset_caches()
    options = Extractor()
    options.min_duplcheck_size = 0
    options.max_repetitions = 0

    element = fromstring("<p>Repeated boilerplate footer for exact duplicate detection.</p>")
    assert duplicate_test(element, options) is False
    assert duplicate_test(element, options) is True
    reset_caches()


def check_structured_outputs() -> None:
    config = low_threshold_config()
    url = "https://example.org/corpus-smoke"

    json_text = extract(HTML_FIXTURE, url=url, record_id="smoke-json", output_format="json", with_metadata=True, config=config)
    assert json_text is not None
    record = json.loads(json_text)
    assert "Corpus smoke main paragraph" in record["text"]
    assert record.get("source") == url
    assert "comments" in record

    csv_text = extract(HTML_FIXTURE, url=url, record_id="smoke-csv", output_format="csv", with_metadata=True, config=config)
    assert csv_text is not None
    row = next(csv.reader(StringIO(csv_text), delimiter="\t"))
    assert len(row) == 11
    assert row[0] == url
    assert row[1] == "smoke-csv"
    assert "Corpus smoke main paragraph" in row[7]

    tei_text = extract(
        HTML_FIXTURE,
        url=url,
        record_id="smoke-tei",
        output_format="xmltei",
        with_metadata=True,
        tei_validation=True,
        config=config,
    )
    assert tei_text is not None
    tei_tree = etree.fromstring(tei_text.encode("utf-8"))
    assert tei_tree.tag.endswith("TEI")
    assert validate_tei(tei_tree) is True


def main() -> None:
    check_hashes_and_simhash()
    check_exact_duplicate_detection()
    check_structured_outputs()
    print("corpus_quality_smoke: ok")


if __name__ == "__main__":
    main()
