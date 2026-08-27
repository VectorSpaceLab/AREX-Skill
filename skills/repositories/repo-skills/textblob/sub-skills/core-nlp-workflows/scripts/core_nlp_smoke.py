#!/usr/bin/env python3
"""Safe TextBlob core NLP smoke test.

This script exercises common TextBlob document-level workflows against an
installed TextBlob package. It does not download corpora or read any repository
checkout files.

Examples:
  python scripts/core_nlp_smoke.py
  python scripts/core_nlp_smoke.py --skip-corpus-heavy --json
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a read-only TextBlob core NLP smoke test.")
    parser.add_argument("--text", default="TextBlob is amazingly simple. Great fun!", help="Text to analyze.")
    parser.add_argument("--skip-corpus-heavy", action="store_true", help="Only run import and pattern-sentiment checks; skip tokenization/tagging/noun-phrase checks that may need NLTK data.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    result: dict[str, object] = {"ok": False, "checks": {}, "advice": []}
    try:
        from textblob import TextBlob  # noqa: PLC0415
        from textblob.exceptions import MissingCorpusError  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover
        result["checks"]["import"] = {"ok": False, "error": repr(exc)}
        result["advice"].append("Install TextBlob: python -m pip install -U textblob")
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result, file=sys.stderr)
        return 2

    blob = TextBlob(args.text)
    result["checks"]["sentiment"] = tuple(blob.sentiment)

    if not args.skip_corpus_heavy:
        try:
            result["checks"]["words"] = [str(w) for w in blob.words]
            result["checks"]["tokens"] = [str(t) for t in blob.tokens]
            result["checks"]["word_counts"] = dict(blob.word_counts)
            result["checks"]["ngrams2"] = [[str(w) for w in gram] for gram in blob.ngrams(2)]
            result["checks"]["sentences"] = [str(s) for s in blob.sentences]
            result["checks"]["tags"] = [(str(w), tag) for w, tag in blob.tags]
            result["checks"]["noun_phrases"] = [str(p) for p in blob.noun_phrases]
        except MissingCorpusError as exc:
            result["checks"]["corpus_backed"] = {"ok": False, "error": "MissingCorpusError"}
            result["advice"].append(str(exc).strip().splitlines()[0])
            result["advice"].append("Run python -m textblob.download_corpora lite for default workflows, or run it without lite for all corpora.")
        except Exception as exc:  # pragma: no cover
            result["checks"]["corpus_backed"] = {"ok": False, "error": repr(exc)}

    result["ok"] = all(not isinstance(v, dict) or v.get("ok", True) for v in result["checks"].values())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Core TextBlob smoke result:")
        for key, value in result["checks"].items():
            print(f"- {key}: {value}")
        if result["advice"]:
            print("Advice:")
            for item in result["advice"]:
                print(f"- {item}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
