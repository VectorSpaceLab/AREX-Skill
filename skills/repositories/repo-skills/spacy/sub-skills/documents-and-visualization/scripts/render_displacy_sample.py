#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import spacy
from spacy import displacy
from spacy.tokens import Doc, Span


def build_dep_sample(manual: bool):
    words = [
        {"text": "This", "tag": "DT"},
        {"text": "is", "tag": "VBZ"},
        {"text": "a", "tag": "DT"},
        {"text": "sentence", "tag": "NN"},
    ]
    arcs = [
        {"start": 0, "end": 1, "label": "nsubj", "dir": "left"},
        {"start": 2, "end": 3, "label": "det", "dir": "left"},
        {"start": 1, "end": 3, "label": "attr", "dir": "right"},
    ]
    if manual:
        return [{"words": words, "arcs": arcs, "title": "Dependency sample"}], {
            "This",
            "sentence",
            "nsubj",
            "attr",
        }

    nlp = spacy.blank("en")
    doc = Doc(
        nlp.vocab,
        words=["This", "is", "a", "sentence"],
        spaces=[True, True, True, False],
        heads=[1, 1, 3, 1],
        tags=["DT", "VBZ", "DT", "NN"],
        deps=["nsubj", "ROOT", "det", "attr"],
    )
    return doc, {"This", "sentence", "nsubj", "attr"}


def build_ent_sample(manual: bool):
    text = "Apple is in New York."
    if manual:
        payload = [
            {
                "text": text,
                "ents": [
                    {"start": 0, "end": 5, "label": "ORG"},
                    {"start": 12, "end": 20, "label": "GPE"},
                ],
                "title": "Entity sample",
            }
        ]
        return payload, {"Apple", "New York", "ORG", "GPE"}

    nlp = spacy.blank("en")
    doc = nlp(text)
    doc.ents = [Span(doc, 0, 1, label="ORG"), Span(doc, 3, 5, label="GPE")]
    return doc, {"Apple", "New York", "ORG", "GPE"}


def build_span_sample(manual: bool, spans_key: str):
    text = "Welcome to the Bank of China."
    tokens = ["Welcome", "to", "the", "Bank", "of", "China", "."]
    if manual:
        payload = [
            {
                "text": text,
                "spans": [
                    {"start_token": 3, "end_token": 6, "label": "ORG"},
                    {"start_token": 5, "end_token": 6, "label": "GPE"},
                ],
                "tokens": tokens,
                "title": "Span sample",
            }
        ]
        return payload, {"Welcome", "Bank", "China", "ORG", "GPE"}

    nlp = spacy.blank("en")
    doc = Doc(nlp.vocab, words=tokens, spaces=[True, True, True, True, True, False, False])
    doc.spans[spans_key] = [Span(doc, 3, 6, label="ORG"), Span(doc, 5, 6, label="GPE")]
    return doc, {"Welcome", "Bank", "China", "ORG", "GPE"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a safe displaCy sample for entity, dependency, or span visualizations."
    )
    parser.add_argument("--style", choices=("dep", "ent", "span"), default="ent")
    parser.add_argument("--manual", action="store_true", help="Render from manual dict input.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the rendered HTML.",
    )
    parser.add_argument("--page", action="store_true", help="Render as a full HTML page.")
    parser.add_argument("--minify", action="store_true", help="Minify the HTML output.")
    parser.add_argument(
        "--spans-key",
        default="ruler",
        help="Span key to use when rendering a doc-based span sample.",
    )
    args = parser.parse_args()

    if args.style == "dep":
        payload, expected = build_dep_sample(args.manual)
        html = displacy.render(
            payload,
            style="dep",
            manual=args.manual,
            page=args.page,
            minify=args.minify,
            options={"fine_grained": True},
        )
    elif args.style == "ent":
        payload, expected = build_ent_sample(args.manual)
        html = displacy.render(payload, style="ent", manual=args.manual, page=args.page, minify=args.minify)
    else:
        payload, expected = build_span_sample(args.manual, args.spans_key)
        options = {"spans_key": args.spans_key} if not args.manual else {}
        html = displacy.render(payload, style="span", manual=args.manual, page=args.page, minify=args.minify, options=options)

    for fragment in expected:
        assert fragment in html, fragment

    summary = {
        "style": args.style,
        "manual": args.manual,
        "page": args.page,
        "minified": args.minify,
        "html_chars": len(html),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
    else:
        print(html)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
