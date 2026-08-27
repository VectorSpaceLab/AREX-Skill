#!/usr/bin/env python3
"""Create or segment a tiny MediaWiki XML fixture with Gensim.

This helper is for dry-runs only. Full Wikipedia dumps are large jobs and should
be planned separately.
"""

from __future__ import annotations

import argparse
import bz2
import json
from pathlib import Path

TINY_XML = '''<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/">
  <page>
    <title>Tiny Article</title>
    <ns>0</ns>
    <id>1</id>
    <revision>
      <id>1</id>
      <text xml:space="preserve">Tiny article text for human computer interface testing.\n== Section ==\nMore text about graph trees and systems.</text>
    </revision>
  </page>
</mediawiki>
'''


def write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = TINY_XML.encode("utf-8")
    if path.suffix == ".bz2":
        path.write_bytes(bz2.compress(data))
    else:
        path.write_bytes(data)


def segment(input_path: Path, output_path: Path | None, min_article_character: int, include_interlinks: bool) -> int:
    from gensim.scripts.segment_wiki import segment_all_articles

    articles = list(segment_all_articles(
        str(input_path),
        min_article_character=min_article_character,
        workers=1,
        include_interlinks=include_interlinks,
    ))
    rows = []
    for article in articles:
        row = {
            "title": article[0],
            "section_titles": [section[0] for section in article[1]],
            "section_texts": [section[1] for section in article[1]],
        }
        if include_interlinks and len(article) > 2:
            row["interlinks"] = article[2]
        rows.append(row)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    else:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixture", help="Write a tiny XML or XML.BZ2 fixture to this path and exit")
    parser.add_argument("--input", help="Tiny MediaWiki XML/XML.BZ2 file to segment")
    parser.add_argument("--output", help="Optional JSONL output path")
    parser.add_argument("--min-article-character", type=int, default=10)
    parser.add_argument("--include-interlinks", action="store_true")
    args = parser.parse_args()

    if args.write_fixture:
        write_fixture(Path(args.write_fixture))
        print(f"wrote fixture {args.write_fixture}")
        return 0
    if not args.input:
        parser.error("provide --input or --write-fixture")
    input_path = Path(args.input)
    if not input_path.is_file():
        parser.error(f"input file does not exist: {input_path}")
    count = segment(input_path, Path(args.output) if args.output else None, args.min_article_character, args.include_interlinks)
    print(f"segmented {count} article(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
