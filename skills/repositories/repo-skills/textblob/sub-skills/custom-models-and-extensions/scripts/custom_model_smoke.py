#!/usr/bin/env python3
"""Safe TextBlob custom model and extension-interface smoke test.

Defines tiny custom components that satisfy TextBlob base interfaces and checks
that TextBlob/Blobber accept them. No corpora, downloads, or original checkout
files are required.
"""

from __future__ import annotations

import argparse
import json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TextBlob custom model interface smoke checks.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    result: dict[str, object] = {"ok": False, "checks": {}, "advice": []}
    try:
        from textblob import Blobber, TextBlob  # noqa: PLC0415
        from textblob.base import BaseNPExtractor, BaseParser, BaseSentimentAnalyzer, BaseTagger, BaseTokenizer  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover
        result["checks"]["import"] = {"ok": False, "error": repr(exc)}
        result["advice"].append("Install TextBlob: python -m pip install -U textblob")
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
        return 2

    class PipeTokenizer(BaseTokenizer):
        def tokenize(self, text):
            return [part.strip() for part in text.split("|") if part.strip()]

    class StaticTagger(BaseTagger):
        def tag(self, text, tokenize=True):
            raw = text if isinstance(text, str) else text.raw
            return [(token, "NN") for token in raw.replace("|", " ").split()]

    class KeywordNPExtractor(BaseNPExtractor):
        def extract(self, text):
            return [part.strip().lower() for part in text.split("|") if len(part.strip()) > 3]

    class LengthAnalyzer(BaseSentimentAnalyzer):
        def analyze(self, text):
            return {"length": len(text), "kind": "custom"}

    class EchoParser(BaseParser):
        def parse(self, text):
            return f"PARSED:{text}"

    tokenizer = PipeTokenizer()
    tagger = StaticTagger()
    extractor = KeywordNPExtractor()
    analyzer = LengthAnalyzer()
    parser_obj = EchoParser()
    blob = TextBlob("alpha|beta words", tokenizer=tokenizer, pos_tagger=tagger, np_extractor=extractor, analyzer=analyzer, parser=parser_obj)
    result["checks"]["tokens"] = [str(t) for t in blob.tokens]
    result["checks"]["words"] = [str(w) for w in blob.words]
    result["checks"]["tags"] = [(str(w), tag) for w, tag in blob.tags]
    result["checks"]["noun_phrases"] = [str(p) for p in blob.noun_phrases]
    result["checks"]["sentiment"] = blob.sentiment
    result["checks"]["parse"] = blob.parse()

    tb = Blobber(tokenizer=tokenizer, pos_tagger=tagger, np_extractor=extractor, analyzer=analyzer, parser=parser_obj)
    b1 = tb("one|two")
    b2 = tb("three|four")
    result["checks"]["blobber_shares_tokenizer"] = b1.tokenizer is b2.tokenizer

    class NotATagger:
        def tag(self, text):
            return []

    try:
        TextBlob("bad", pos_tagger=NotATagger())
        result["checks"]["invalid_tagger_rejected"] = False
    except ValueError:
        result["checks"]["invalid_tagger_rejected"] = True

    result["ok"] = bool(result["checks"].get("invalid_tagger_rejected")) and bool(result["checks"].get("blobber_shares_tokenizer"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("TextBlob custom model smoke result:")
        for key, value in result["checks"].items():
            print(f"- {key}: {value}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
