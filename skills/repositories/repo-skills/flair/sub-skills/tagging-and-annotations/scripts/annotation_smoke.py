#!/usr/bin/env python3
"""No-download smoke checks for Flair annotations, tokenization, splitting, serialization, and HTML rendering.

This script is intentionally safe by default: it uses only local in-memory text,
manual labels, rule-based RegexpTagger, CPU-friendly tokenizers/splitters, and
Flair's pure-Python HTML renderer. It does not load pretrained models or access
external datasets.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

# Keep this no-download smoke script on the verified CPU baseline. This must be
# set before the first import of the public flair package.
os.environ.setdefault("FLAIR_DEVICE", "cpu")


def run_smoke() -> dict[str, Any]:
    import flair
    from flair.data import DataPair, Relation, Sentence
    from flair.models import RegexpTagger
    from flair.splitter import NewlineSentenceSplitter, NoSentenceSplitter, SegtokSentenceSplitter
    from flair.tokenization import NoTokenizer, SegtokTokenizer, SpaceTokenizer, StaccatoTokenizer
    from flair.visual.ner_html import render_ner_html

    report: dict[str, Any] = {
        "checks": [],
        "flair_version": getattr(flair, "__version__", "unknown"),
        "device": str(getattr(flair, "device", "unknown")),
    }

    def record(name: str, **details: Any) -> None:
        report["checks"].append({"name": name, **details})

    # Manual annotations across sentence, token, span, relation, and DataPair.
    sentence = Sentence("George Washington went to Washington.", use_tokenizer=SegtokTokenizer())
    sentence.add_label("topic", "history")
    sentence[2].add_label("pos", "VERB")
    person = sentence[0:2]
    place = sentence[4:5]
    person.add_label("ner", "PER", score=1.0)
    person.add_label("role", "president")
    place.add_label("ner", "LOC", score=1.0)
    Relation(person, place).add_label("relation", "visited")
    pair = DataPair(Sentence("first text"), Sentence("second text"))

    assert [token.text for token in sentence] == ["George", "Washington", "went", "to", "Washington", "."]
    assert [label.value for label in sentence.get_labels("topic")] == ["history"]
    assert [label.value for label in sentence.get_labels("pos")] == ["VERB"]
    assert [(span.text, span.get_label("ner").value) for span in sentence.get_spans("ner")] == [
        ("George Washington", "PER"),
        ("Washington", "LOC"),
    ]
    assert [(rel.first.text, rel.second.text, rel.get_label("relation").value) for rel in sentence.get_relations("relation")] == [
        ("George Washington", "Washington", "visited")
    ]
    assert pair.text == "first text || second text"
    record(
        "manual_annotations",
        labels=[(label.typename, label.value, label.data_point.text) for label in sentence.get_labels()],
        pair_text=pair.text,
    )

    # Serialization preserves labels, offsets, tokenizer config, spans, and relations.
    recreated = Sentence.from_dict(sentence.to_dict())
    assert recreated.to_original_text() == sentence.to_original_text()
    assert recreated.tokenizer.name == sentence.tokenizer.name
    assert [(span.text, span.get_label("ner").value) for span in recreated.get_spans("ner")] == [
        ("George Washington", "PER"),
        ("Washington", "LOC"),
    ]
    assert [label.value for label in recreated.get_labels("relation")] == ["visited"]
    record("serialization_round_trip", tokenizer=recreated.tokenizer.name, span_count=len(recreated.get_spans("ner")))

    # Tokenization choices that require no optional model downloads.
    tokenization_examples = {
        "segtok": [token.text for token in Sentence("A test, yes.", use_tokenizer=SegtokTokenizer())],
        "space": [token.text for token in Sentence("A test, yes.", use_tokenizer=SpaceTokenizer())],
        "no": [token.text for token in Sentence("A test, yes.", use_tokenizer=NoTokenizer())],
        "staccato": StaccatoTokenizer().tokenize("A test, yes."),
    }
    assert tokenization_examples["segtok"] == ["A", "test", ",", "yes", "."]
    assert tokenization_examples["space"] == ["A", "test,", "yes."]
    assert tokenization_examples["no"] == ["A test, yes."]
    assert tokenization_examples["staccato"]
    record("tokenizers", examples=tokenization_examples)

    # Sentence splitting with context links and offsets.
    text = "First sentence. Second sentence."
    split_sentences = SegtokSentenceSplitter().split(text)
    assert [s.to_original_text() for s in split_sentences] == ["First sentence.", "Second sentence."]
    assert [s.start_position for s in split_sentences] == [0, 16]
    assert split_sentences[0].next_sentence() is split_sentences[1]
    newline_sentences = NewlineSentenceSplitter().split("alpha\nbeta")
    no_split = NoSentenceSplitter().split(text)
    assert [s.to_original_text() for s in newline_sentences] == ["alpha", "beta"]
    assert len(no_split) == 1 and no_split[0].to_original_text() == text
    record(
        "sentence_splitters",
        segtok_offsets=[s.start_position for s in split_sentences],
        newline_count=len(newline_sentences),
        no_split_count=len(no_split),
    )

    # RegexpTagger labels only spans aligned to token boundaries.
    quote_sentence = Sentence('Der sagte: "das ist durchaus interessant"')
    regex_tagger = RegexpTagger(
        [
            (r'["„»]((?:(?=(\\?))\2.)*?)[”"“«]', "quote_part", 1),
            (r'["„»]((?:(?=(\\?))\2.)*?)[”"“«]', "quote"),
        ]
    )
    regex_tagger.predict(quote_sentence)
    assert quote_sentence.get_label("quote_part").data_point.text == "das ist durchaus interessant"
    assert quote_sentence.get_label("quote").data_point.text == '"das ist durchaus interessant"'
    record(
        "regexp_tagger",
        quote_part=quote_sentence.get_label("quote_part").data_point.text,
        quote=quote_sentence.get_label("quote").data_point.text,
    )

    # HTML rendering for one non-overlapping span layer.
    html = render_ner_html(sentence, label_name="ner", colors={"PER": "#F7FF53", "LOC": "yellow", "O": "#ddd"})
    assert "George Washington" in html
    assert "PER" in html
    assert "Washington" in html
    assert "LOC" in html
    record("html_rendering", contains_page="<html" in html.lower(), length=len(html))

    report["ok"] = True
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-download Flair annotation smoke checks.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of a short text summary.")
    args = parser.parse_args()

    report = run_smoke()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Flair annotation smoke checks passed:")
        for check in report["checks"]:
            print(f"- {check['name']}")


if __name__ == "__main__":
    main()
