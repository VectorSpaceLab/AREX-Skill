#!/usr/bin/env python3
"""Check that the requested spaCy model is available without downloading anything.

This helper is diagnostic-only and never calls the spaCy downloader.
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='en_core_web_md', help='spaCy model name to check')
    parser.add_argument('--strict', action='store_true', help='return non-zero when the model is missing')
    args = parser.parse_args()

    try:
        import spacy
    except Exception as exc:
        print(f'spaCy import failed: {exc}', file=sys.stderr)
        print('If the message mentions click, repair the base environment first.', file=sys.stderr)
        return 2

    try:
        nlp = spacy.load(args.model)
    except OSError as exc:
        print(f'model missing: {args.model}', file=sys.stderr)
        print(f'cause: {exc}', file=sys.stderr)
        print('action: install the model before using AnchorText similarity or language-model sampling.', file=sys.stderr)
        return 1 if args.strict else 0

    print('spaCy model available:', args.model)
    print('pipeline:', nlp.pipe_names)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
