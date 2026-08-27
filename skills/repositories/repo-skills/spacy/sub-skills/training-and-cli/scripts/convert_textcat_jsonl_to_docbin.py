#!/usr/bin/env python3
"""Convert tiny textcat JSONL fixtures to a spaCy DocBin safely.

Purpose:
  Read JSONL rows with ``text`` and ``cats`` keys, create docs with a blank or
  explicitly supplied spaCy pipeline, and write a ``.spacy`` DocBin file for
  training-data workflows.

Safe defaults:
  - No downloads.
  - No training.
  - No mutation outside the requested output file.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a textcat JSONL file to a DocBin.")
    parser.add_argument("--input-file", type=Path, required=True, help="Input JSONL file with text/cats rows.")
    parser.add_argument("--output-file", type=Path, help="Output .spacy file. Defaults to the input stem with .spacy.")
    parser.add_argument("--lang", default="en", help="Language code for a blank pipeline when --model is not supplied.")
    parser.add_argument("--model", help="Installed model package or local pipeline directory to load instead of a blank language.")
    parser.add_argument("--limit", type=int, default=0, help="Stop after this many JSONL rows. 0 means no limit.")
    parser.add_argument("--sentencizer", action="store_true", help="Add a sentencizer when a blank pipeline is used.")
    args = parser.parse_args()

    import sys
    import srsly
    import spacy
    from spacy.tokens import DocBin

    if not args.input_file.exists():
        print(f"Input file not found: {args.input_file}", file=sys.stderr)
        return 1

    if args.output_file is None:
        output_file = args.input_file.with_suffix(".spacy")
    elif args.output_file.suffix == ".spacy":
        output_file = args.output_file
    else:
        output_file = args.output_file.with_suffix(".spacy")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if args.model:
        nlp = spacy.load(args.model)
    else:
        nlp = spacy.blank(args.lang)
        if args.sentencizer and not nlp.has_pipe("sentencizer"):
            nlp.add_pipe("sentencizer")

    docs = []
    with args.input_file.open("r", encoding="utf8") as fileh:
        for i, line in enumerate(fileh, start=1):
            data = srsly.json_loads(line)
            doc = nlp(data["text"])
            doc.cats = data["cats"]
            docs.append(doc)
            if args.limit and i >= args.limit:
                break

    DocBin(docs=docs, store_user_data=True).to_disk(output_file)
    print(output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
