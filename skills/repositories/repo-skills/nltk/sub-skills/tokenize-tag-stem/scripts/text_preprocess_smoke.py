#!/usr/bin/env python3
"""No-download smoke check for NLTK text preprocessing APIs.

The required checks use only bundled code paths: Treebank/WordPunct/Tweet
 tokenizers, Porter/Snowball stemmers, a tiny RegexpTagger/UnigramTagger, and
 span/detokenization helpers. Optional data-backed checks are reported as
 present/missing and are only executed when their NLTK data resources already
 exist. This script never calls nltk.download().
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any


RESOURCE_PROBES = {
    "punkt_tab_english": [
        "tokenizers/punkt_tab/english/",
        "tokenizers/punkt_tab.zip/punkt_tab/english/",
    ],
    "averaged_perceptron_tagger_eng": [
        "taggers/averaged_perceptron_tagger_eng/",
        "taggers/averaged_perceptron_tagger_eng.zip/averaged_perceptron_tagger_eng/",
    ],
    "averaged_perceptron_tagger_rus": [
        "taggers/averaged_perceptron_tagger_rus/",
        "taggers/averaged_perceptron_tagger_rus.zip/averaged_perceptron_tagger_rus/",
    ],
    "universal_tagset": [
        "taggers/universal_tagset/",
        "taggers/universal_tagset.zip/universal_tagset/",
    ],
    "wordnet": [
        "corpora/wordnet/",
        "corpora/wordnet.zip/wordnet/",
    ],
    "omw-2.0": [
        "corpora/omw-2.0/",
        "corpora/omw-2.0.zip/omw-2.0/",
    ],
    "vader_lexicon": [
        "sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt",
        "sentiment/vader_lexicon/vader_lexicon.txt",
    ],
}


def _find_first(nltk, resources: list[str]) -> str | None:
    for resource in resources:
        try:
            nltk.data.find(resource)
        except (LookupError, ValueError):
            continue
        return resource
    return None


def run_smoke(run_optional: bool = True) -> dict[str, Any]:
    try:
        import nltk
        from nltk import pos_tag, word_tokenize
        from nltk.sentiment import SentimentIntensityAnalyzer
        from nltk.stem import PorterStemmer, SnowballStemmer, WordNetLemmatizer
        from nltk.tag import RegexpTagger, UnigramTagger
        from nltk.tokenize import (
            TweetTokenizer,
            TreebankWordDetokenizer,
            TreebankWordTokenizer,
            WhitespaceTokenizer,
            WordPunctTokenizer,
        )
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        raise RuntimeError(
            "Could not import required NLTK preprocessing APIs. Install NLTK with "
            "its base runtime dependencies in the active Python environment."
        ) from exc

    summary: dict[str, Any] = {
        "status": "ok",
        "python": platform.python_version(),
        "executable": sys.executable,
        "nltk_version": getattr(nltk, "__version__", "unknown"),
        "downloads_invoked": False,
        "required_checks": {},
        "resource_probes": {},
        "optional_checks": {},
    }

    text = "Good muffins cost $3.88 in New York."
    treebank_tokens = TreebankWordTokenizer().tokenize(text)
    if treebank_tokens[:5] != ["Good", "muffins", "cost", "$", "3.88"]:
        raise AssertionError(f"Unexpected Treebank tokens: {treebank_tokens!r}")
    summary["required_checks"]["treebank_tokens"] = treebank_tokens

    wordpunct_tokens = WordPunctTokenizer().tokenize(text)
    if wordpunct_tokens[:7] != ["Good", "muffins", "cost", "$", "3", ".", "88"]:
        raise AssertionError(f"Unexpected WordPunct tokens: {wordpunct_tokens!r}")
    summary["required_checks"]["wordpunct_tokens"] = wordpunct_tokens

    tweet_tokens = TweetTokenizer(strip_handles=True, reduce_len=True).tokenize("@myke soooo coool!!!")
    if tweet_tokens != ["sooo", "coool", "!", "!", "!"]:
        raise AssertionError(f"Unexpected TweetTokenizer tokens: {tweet_tokens!r}")
    summary["required_checks"]["tweet_tokens"] = tweet_tokens

    spans = list(WhitespaceTokenizer().span_tokenize("Good muffins"))
    if spans != [(0, 4), (5, 12)]:
        raise AssertionError(f"Unexpected whitespace spans: {spans!r}")
    summary["required_checks"]["whitespace_spans"] = spans

    detok = TreebankWordDetokenizer().detokenize(TreebankWordTokenizer().tokenize("Don't stop."))
    if detok != "Don't stop.":
        raise AssertionError(f"Unexpected detokenized text: {detok!r}")
    summary["required_checks"]["detokenized"] = detok

    porter = PorterStemmer().stem("running")
    snowball = SnowballStemmer("german").stem("Schränke")
    if porter != "run" or snowball != "schrank":
        raise AssertionError(f"Unexpected stems: porter={porter!r}, snowball={snowball!r}")
    summary["required_checks"]["stems"] = {"porter_running": porter, "snowball_german_schraenke": snowball}

    backoff = RegexpTagger([(r"^-?[0-9]+(\.[0-9]+)?$", "CD"), (r".*ing$", "VBG"), (r".*s$", "NNS"), (r".*", "NN")])
    train = [[("the", "DT"), ("dog", "NN"), ("runs", "VBZ")]]
    tagger = UnigramTagger(train, backoff=backoff)
    tagged = tagger.tag(["the", "cats", "running", "42"])
    if tagged != [("the", "DT"), ("cats", "NNS"), ("running", "VBG"), ("42", "CD")]:
        raise AssertionError(f"Unexpected custom tagger output: {tagged!r}")
    summary["required_checks"]["custom_backoff_tagger"] = tagged

    # `word_tokenize(..., preserve_line=True)` should avoid Punkt data.
    no_punkt_tokens = word_tokenize("Hello, world!", preserve_line=True)
    if no_punkt_tokens != ["Hello", ",", "world", "!"]:
        raise AssertionError(f"Unexpected preserve_line word_tokenize output: {no_punkt_tokens!r}")
    summary["required_checks"]["word_tokenize_preserve_line"] = no_punkt_tokens

    for name, probes in RESOURCE_PROBES.items():
        matched = _find_first(nltk, probes)
        summary["resource_probes"][name] = {"present": matched is not None, "matched": matched}

    if run_optional:
        if summary["resource_probes"]["punkt_tab_english"]["present"]:
            summary["optional_checks"]["sent_tokenize"] = nltk.sent_tokenize("Dr. Jones left. He returned.", language="english")
        else:
            summary["optional_checks"]["sent_tokenize"] = "SKIPPED_MISSING punkt_tab"

        if summary["resource_probes"]["averaged_perceptron_tagger_eng"]["present"]:
            summary["optional_checks"]["pos_tag_eng"] = pos_tag(["John", "saw", "Mary", "."], lang="eng")
        else:
            summary["optional_checks"]["pos_tag_eng"] = "SKIPPED_MISSING averaged_perceptron_tagger_eng"

        if summary["resource_probes"]["wordnet"]["present"]:
            summary["optional_checks"]["wordnet_lemmatizer"] = WordNetLemmatizer().lemmatize("dogs", pos="n")
        else:
            summary["optional_checks"]["wordnet_lemmatizer"] = "SKIPPED_MISSING wordnet"

        if summary["resource_probes"]["vader_lexicon"]["present"]:
            summary["optional_checks"]["vader_empty"] = SentimentIntensityAnalyzer().polarity_scores("")
        else:
            summary["optional_checks"]["vader_empty"] = "SKIPPED_MISSING vader_lexicon"

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic no-download smoke check for NLTK preprocessing APIs."
    )
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    parser.add_argument("--skip-optional", action="store_true", help="skip optional data-backed checks")
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(run_optional=not args.skip_optional)
    except Exception as exc:
        print(f"text_preprocess_smoke: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True, ensure_ascii=False))
    else:
        print("text_preprocess_smoke: OK")
        for key in sorted(summary["required_checks"]):
            print(f"  {key}: {summary['required_checks'][key]}")
        print("  data resources:")
        for key, value in sorted(summary["resource_probes"].items()):
            print(f"    {key}: {'present' if value['present'] else 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
