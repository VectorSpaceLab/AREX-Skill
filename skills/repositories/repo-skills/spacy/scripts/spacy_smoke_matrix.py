#!/usr/bin/env python3
"""Cross-cutting spaCy smoke matrix.

Purpose:
  Provide a quick base-package check that multiple spaCy sub-skills can rely
  on: import, blank English tokenization, DocBin round-trip, representative
  built-in factories, and the `python -m spacy` CLI help surface.

Safe defaults:
  - No downloads.
  - No training.
  - No model loading.
  - No dependency on the source checkout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small cross-cutting spaCy smoke matrix.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    import spacy
    from spacy.language import Language
    from spacy.matcher import Matcher
    from spacy.tokens import DocBin

    nlp = spacy.blank("en")
    doc = nlp("Hello, spaCy!")
    matcher = Matcher(nlp.vocab)
    matcher.add("HELLO", [[{"LOWER": "hello"}]])
    docbin = DocBin(docs=[doc]).to_bytes()
    round_trip = list(DocBin().from_bytes(docbin).get_docs(nlp.vocab))[0]
    cli = subprocess.run([sys.executable, "-m", "spacy", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    factories = ["sentencizer", "entity_ruler", "tok2vec", "ner", "textcat"]
    payload: Dict[str, Any] = {
        "spacy": spacy.__version__,
        "tokens": [token.text for token in doc],
        "matcher_hits": len(matcher(doc)),
        "docbin_round_trip": round_trip.text,
        "factories": {name: nlp.has_factory(name) for name in factories},
        "language_add_pipe": str(Language.add_pipe),
        "cli_help_exit_code": cli.returncode,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload)
    return 0 if cli.returncode == 0 else cli.returncode


if __name__ == "__main__":
    raise SystemExit(main())
