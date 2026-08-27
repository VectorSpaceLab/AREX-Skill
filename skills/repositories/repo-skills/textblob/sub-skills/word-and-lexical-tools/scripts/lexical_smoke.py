#!/usr/bin/env python3
"""Safe smoke checks for TextBlob word-level lexical APIs.

The script is deterministic, reads only the installed Python environment, and
never downloads NLTK corpora. Use --skip-wordnet when corpus-backed checks are
not required or corpus data is unavailable.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return repr(value)


def _record(results: list[dict[str, Any]], name: str, fn: Callable[[], Any]) -> bool:
    try:
        detail = fn()
    except Exception as exc:  # pragma: no cover - failure path is for diagnostics
        results.append(
            {
                "name": name,
                "status": "failed",
                "errorType": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=4),
            }
        )
        return False
    results.append({"name": name, "status": "passed", "detail": _json_safe(detail)})
    return True


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def check_imports() -> dict[str, Any]:
    import textblob
    from textblob import Word, WordList

    try:
        dist_version = version("textblob")
    except PackageNotFoundError:
        dist_version = "unknown"

    return {
        "distributionVersion": dist_version,
        "moduleVersion": getattr(textblob, "__version__", "unknown"),
        "Word": repr(Word("cat")),
        "WordList": repr(WordList(["cat", "dog"])),
    }


def check_word_and_wordlist() -> dict[str, Any]:
    from textblob import Word, WordList

    cat = Word("cat", "NN")
    _assert_equal(cat.pos_tag, "NN", "Word pos_tag")
    _assert_equal(cat.upper(), "CAT", "Word stringlike upper")
    _assert_equal(cat[0:2], "ca", "Word stringlike slice")

    wl = WordList(["Beautiful", "is", "better"])
    _assert_equal(type(wl[0]).__name__, "Word", "WordList index returns Word")
    sliced = wl[:2]
    _assert_equal(type(sliced).__name__, "WordList", "WordList slice type")
    _assert_equal(list(sliced), ["Beautiful", "is"], "WordList slice contents")

    mutable = WordList(["dog"])
    mutable.append("cat")
    mutable.extend(["buffalo", 4])
    _assert_equal(type(mutable[1]).__name__, "Word", "append converts strings")
    _assert_equal(type(mutable[2]).__name__, "Word", "extend converts strings")
    _assert_equal(mutable[3], 4, "extend preserves non-strings")

    counts = WordList(["monty", "python", "Python", "Monty"])
    _assert_equal(counts.count("monty"), 2, "case-insensitive count")
    _assert_equal(counts.count("monty", case_sensitive=True), 1, "case-sensitive count")

    return {
        "word": str(cat),
        "sliceType": type(sliced).__name__,
        "mutableTypes": [type(item).__name__ for item in mutable],
        "caseInsensitiveMonty": counts.count("monty"),
        "caseSensitiveMonty": counts.count("monty", case_sensitive=True),
    }


def check_inflection_stemming_spelling() -> dict[str, Any]:
    from textblob import Word, WordList

    _assert_equal(Word("cats").singularize(), "cat", "singularize cats")
    _assert_equal(Word("cat").pluralize(), "cats", "pluralize cat")
    _assert_equal(Word("cars").stem(), "car", "stem cars")
    _assert_equal(Word("wolves").stem(), "wolv", "stem wolves")

    wl = WordList(["dogs", "cats", "buffaloes", "men", "mice", "offspring"])
    _assert_equal(
        wl.singularize(),
        WordList(["dog", "cat", "buffalo", "man", "mouse", "offspring"]),
        "WordList singularize",
    )
    _assert_equal(WordList(["Zen", "oF", "PYTHON"]).lower(), WordList(["zen", "of", "python"]), "WordList lower")
    _assert_equal(WordList(["cat", "dogs", "oxen"]).stem(), WordList(["cat", "dog", "oxen"]), "WordList stem")

    suggestions = Word("speling").spellcheck()
    if not suggestions or suggestions[0][0] != "spelling":
        raise AssertionError(f"expected spelling suggestion first, got {suggestions!r}")
    _assert_equal(Word("speling").correct(), Word("spelling"), "Word.correct")
    _assert_equal(Word("!").spellcheck(), [("!", 1.0)], "punctuation spellcheck")
    _assert_equal(Word("42").spellcheck(), [("42", 1.0)], "number spellcheck")

    return {
        "catPlural": str(Word("cat").pluralize()),
        "catsSingular": str(Word("cats").singularize()),
        "wolvesStem": Word("wolves").stem(),
        "spelingBest": suggestions[0],
    }


def check_wordnet() -> dict[str, Any]:
    from textblob import Word
    from textblob.wordnet import NOUN, VERB, Synset

    _assert_equal(Word("went").lemmatize("v"), "go", "lemmatize with WordNet verb code")
    _assert_equal(Word("went").lemmatize(VERB), "go", "lemmatize with WordNet VERB")
    _assert_equal(Word("went").lemmatize("VBD"), "go", "lemmatize with Penn VBD")
    _assert_equal(Word("went", "VBD").lemma, "go", "lemma property with stored POS")
    _assert_equal(Word("wolves").lemma, "wolf", "lemma property noun default")

    car_synsets = Word("car").synsets
    if not car_synsets:
        raise AssertionError("expected at least one car synset")
    noun_synsets = Word("work").get_synsets(pos=NOUN)
    if not noun_synsets or any(syn.pos() != NOUN for syn in noun_synsets):
        raise AssertionError(f"expected noun-only synsets for work, got {noun_synsets!r}")
    definitions = Word("octopus").definitions
    if not definitions or not all(isinstance(item, str) for item in definitions):
        raise AssertionError(f"expected string definitions for octopus, got {definitions!r}")
    _assert_equal(Word("dog").synsets[0], Synset("dog.n.01"), "direct Synset equality")

    return {
        "wentVerbLemma": Word("went").lemmatize(VERB),
        "wolvesLemma": Word("wolves").lemma,
        "carFirstSynset": repr(car_synsets[0]),
        "workNounSynsets": len(noun_synsets),
        "octopusDefinitionCount": len(definitions),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run safe smoke checks for installed TextBlob Word and WordList APIs."
    )
    parser.add_argument(
        "--skip-wordnet",
        action="store_true",
        help="Skip lemmatization, synset, definition, and direct WordNet checks that require NLTK WordNet data.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a concise text report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[dict[str, Any]] = []

    ok = True
    ok &= _record(results, "imports", check_imports)
    ok &= _record(results, "word-and-wordlist", check_word_and_wordlist)
    ok &= _record(results, "inflection-stemming-spelling", check_inflection_stemming_spelling)
    if args.skip_wordnet:
        results.append({"name": "wordnet", "status": "skipped", "detail": "--skip-wordnet supplied"})
    else:
        ok &= _record(results, "wordnet", check_wordnet)

    payload = {"status": "passed" if ok else "failed", "checks": results}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in results:
            print(f"[{check['status']}] {check['name']}")
            if check["status"] == "failed":
                print(f"  {check['errorType']}: {check['error']}")
        print(f"Overall: {payload['status']}")
        if not ok:
            print("Tip: re-run with --json for details, or --skip-wordnet if WordNet corpora are intentionally unavailable.")

    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
