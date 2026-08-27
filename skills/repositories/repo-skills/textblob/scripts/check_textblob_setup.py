#!/usr/bin/env python3
"""Read-only TextBlob setup diagnostic.

Purpose: verify that an installed TextBlob package can be imported and that the
NLTK corpora required by common TextBlob workflows are visible. This script does
not download data, mutate the environment, or require the original TextBlob
repository checkout.

Examples:
  python scripts/check_textblob_setup.py
  python scripts/check_textblob_setup.py --require-all-corpora --json
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version

MIN_CORPORA = {
    "brown": "corpora/brown",
    "punkt_tab": "tokenizers/punkt_tab",
    "wordnet": "corpora/wordnet",
    "wordnet.zip": "corpora/wordnet.zip",
    "averaged_perceptron_tagger_eng": "taggers/averaged_perceptron_tagger_eng",
}
ADDITIONAL_CORPORA = {
    "conll2000": "corpora/conll2000",
    "movie_reviews": "corpora/movie_reviews",
}


def find_corpus(nltk_module, name: str, locator: str) -> dict[str, object]:
    try:
        found = nltk_module.data.find(locator)
        return {"name": name, "locator": locator, "present": True, "detail": str(found)}
    except LookupError:
        return {"name": name, "locator": locator, "present": False, "detail": "not found"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check TextBlob import and NLTK corpus readiness.")
    parser.add_argument("--require-all-corpora", action="store_true", help="Require optional conll2000 and movie_reviews corpora in addition to lite corpora.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    result: dict[str, object] = {"ok": False, "imports": {}, "corpora": [], "smoke": {}, "advice": []}

    try:
        import nltk  # noqa: PLC0415
        from textblob import TextBlob, Word  # noqa: PLC0415
        from textblob.exceptions import MissingCorpusError  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - diagnostic surface
        result["imports"] = {"ok": False, "error": repr(exc)}
        result["advice"].append("Install TextBlob first, for example: python -m pip install -U textblob")
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("TextBlob import failed:", repr(exc), file=sys.stderr)
        return 2

    try:
        dist_version = version("textblob")
    except PackageNotFoundError:
        dist_version = "unknown"
    result["imports"] = {"ok": True, "textblob_version": dist_version, "nltk_version": getattr(nltk, "__version__", "unknown")}

    corpus_plan = dict(MIN_CORPORA)
    if args.require_all_corpora:
        corpus_plan.update(ADDITIONAL_CORPORA)
    corpus_rows = [find_corpus(nltk, name, locator) for name, locator in corpus_plan.items()]

    # NLTK may keep WordNet only as a zip file. Count either wordnet directory or zip as satisfying WordNet.
    wordnet_present = any(row["name"].startswith("wordnet") and row["present"] for row in corpus_rows)
    normalized_rows = []
    for row in corpus_rows:
        if row["name"] == "wordnet" and not row["present"] and wordnet_present:
            continue
        if row["name"] == "wordnet.zip" and not row["present"] and any(r["name"] == "wordnet" and r["present"] for r in corpus_rows):
            continue
        normalized_rows.append(row)
    result["corpora"] = normalized_rows

    missing = [row["name"] for row in normalized_rows if not row["present"]]
    if missing:
        result["advice"].append("Missing corpora: " + ", ".join(missing))
        result["advice"].append("Run python -m textblob.download_corpora lite for default workflows, or omit lite for all corpora.")

    try:
        blob = TextBlob("TextBlob is amazingly simple. Great fun!")
        result["smoke"] = {
            "sentiment": tuple(blob.sentiment),
            "word_correct": str(Word("speling").correct()),
        }
        # Corpus-backed checks. Keep small and catch the TextBlob-friendly exception.
        result["smoke"].update(
            {
                "sentences": [str(s) for s in blob.sentences],
                "tags_first3": [(str(w), tag) for w, tag in blob.tags[:3]],
                "noun_phrases": [str(p) for p in blob.noun_phrases],
            }
        )
    except MissingCorpusError as exc:
        result["smoke"]["corpus_backed_error"] = "MissingCorpusError"
        result["advice"].append(str(exc).strip().splitlines()[0])
    except Exception as exc:  # pragma: no cover - diagnostic surface
        result["smoke"]["error"] = repr(exc)

    result["ok"] = not missing and "error" not in result["smoke"] and "corpus_backed_error" not in result["smoke"]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"TextBlob import: ok (version {dist_version})")
        for row in normalized_rows:
            status = "ok" if row["present"] else "missing"
            print(f"corpus {row['name']}: {status}")
        if result["smoke"]:
            print("smoke:", result["smoke"])
        if result["advice"]:
            print("advice:")
            for item in result["advice"]:
                print(f"- {item}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
