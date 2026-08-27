#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import spacy
from spacy.attrs import ENT_IOB, ENT_TYPE, ORTH, SPACY
from spacy.matcher import DependencyMatcher, Matcher, PhraseMatcher
from spacy.scorer import Scorer
from spacy.tokens import Doc, DocBin, Span, Token
from spacy.training import Example


DOC_EXT = "dvis_doc"
TOKEN_EXT = "dvis_token"
SPAN_EXT = "dvis_span"
TEXT_ID_EXT = "dvis_text_id"


def ensure_extension(cls, name: str, **kwargs) -> None:
    cls.set_extension(name, force=True, **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a spaCy smoke check for docs, tokenization, matching, serialization, and scoring."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a JSON summary file.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Optional directory for temp serialization artifacts.",
    )
    args = parser.parse_args()

    nlp = spacy.blank("en")
    summary: dict[str, object] = {"version": spacy.__version__, "lang": nlp.lang}

    # Tokenizer and batch processing checks.
    tokenized = nlp("Hello, world! New York is big.")
    assert [t.text for t in tokenized[:4]] == ["Hello", ",", "world", "!"]
    summary["blank_tokens"] = [t.text for t in tokenized[:4]]
    summary["tokenizer_explain"] = [kind for kind, _ in nlp.tokenizer.explain("(don't)")]
    assert summary["tokenizer_explain"][0] == "PREFIX"

    ensure_extension(Doc, TEXT_ID_EXT, default=None)
    text_pairs = [
        ("First batch text.", {"text_id": "a"}),
        ("Second batch text.", {"text_id": "b"}),
    ]
    pipe_contexts: list[str | None] = []
    for doc, context in nlp.pipe(text_pairs, as_tuples=True):
        doc._.dvis_text_id = context["text_id"]
        pipe_contexts.append(doc._.dvis_text_id)
    assert pipe_contexts == ["a", "b"]
    summary["pipe_contexts"] = pipe_contexts

    # Object model, alignment, extensions, and retokenization.
    ensure_extension(Doc, DOC_EXT, default=None)
    ensure_extension(Token, TOKEN_EXT, default=False)
    ensure_extension(Span, SPAN_EXT, default=None)

    anno_doc = nlp("Hello world!")
    anno_doc._.dvis_doc = "doc-meta"
    anno_doc[0]._.dvis_token = True
    anno_doc[0:2]._.dvis_span = "phrase-meta"
    anno_doc.ents = [Span(anno_doc, 0, 2, label="GREETING")]
    anno_doc.spans["smoke"] = [Span(anno_doc, 0, 2, label="GREETING")]

    strict_none = anno_doc.char_span(1, 4) is None
    assert strict_none
    expanded = anno_doc.char_span(1, 4, alignment_mode="expand")
    assert expanded is not None and expanded.text == "Hello"
    summary["char_span_strict_none"] = strict_none
    summary["char_span_expand"] = expanded.text if expanded is not None else None

    merge_doc = nlp("New York City")
    with merge_doc.retokenize() as retokenizer:
        retokenizer.merge(merge_doc[0:2], attrs={"LEMMA": "new york"})
    assert [t.text for t in merge_doc] == ["New York", "City"]
    summary["retokenized_tokens"] = [t.text for t in merge_doc]

    # JSON, bytes, disk, array, and DocBin serialization.
    json_doc = anno_doc.to_json(underscore=[DOC_EXT, TOKEN_EXT, SPAN_EXT])
    json_round_trip = Doc(anno_doc.vocab).from_json(json_doc, validate=True)
    assert json_round_trip.text == anno_doc.text
    assert json_round_trip._.dvis_doc == "doc-meta"
    assert json_round_trip[0]._.dvis_token is True
    assert json_round_trip[0:2]._.dvis_span == "phrase-meta"
    assert "smoke" in json_round_trip.spans
    assert json_round_trip.spans["smoke"][0].text == "Hello world"

    bytes_round_trip = Doc(anno_doc.vocab).from_bytes(anno_doc.to_bytes())
    assert bytes_round_trip.text == anno_doc.text
    assert bytes_round_trip._.dvis_doc == "doc-meta"

    attrs = [ORTH, SPACY, ENT_IOB, ENT_TYPE]
    arr = anno_doc.to_array(attrs)
    array_doc = Doc(
        anno_doc.vocab,
        words=[t.text for t in anno_doc],
        spaces=[bool(t.whitespace_) for t in anno_doc],
    )
    array_doc.from_array(attrs, arr)
    assert array_doc.text == anno_doc.text
    assert [(ent.text, ent.label_) for ent in array_doc.ents] == [
        (ent.text, ent.label_) for ent in anno_doc.ents
    ]
    assert np.array_equal(array_doc.to_array(attrs), arr)

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(args.workdir) if args.workdir else Path(tmpdir)
        base.mkdir(parents=True, exist_ok=True)

        doc_dir = base / "doc"
        anno_doc.to_disk(doc_dir)
        disk_doc = Doc(anno_doc.vocab).from_disk(doc_dir)
        assert disk_doc.text == anno_doc.text
        assert disk_doc._.dvis_doc == "doc-meta"
        assert disk_doc.spans["smoke"][0].text == "Hello world"

        bin_path = base / "docs.spacy"
        doc_bin = DocBin(attrs=["ENT_IOB", "ENT_TYPE"], store_user_data=True)
        doc_bin.add(anno_doc)
        doc_bin.to_disk(bin_path)
        bin_docs = list(DocBin(store_user_data=True).from_disk(bin_path).get_docs(anno_doc.vocab))
        assert len(bin_docs) == 1
        assert bin_docs[0].text == anno_doc.text
        assert bin_docs[0]._.dvis_doc == "doc-meta"
        assert bin_docs[0].spans["smoke"][0].text == "Hello world"

        reloaded_docs = list(
            DocBin(attrs=["ENT_IOB", "ENT_TYPE"], store_user_data=True)
            .from_bytes(doc_bin.to_bytes())
            .get_docs(anno_doc.vocab)
        )
        assert len(reloaded_docs) == 1
        assert reloaded_docs[0]._.dvis_doc == "doc-meta"
        assert reloaded_docs[0].spans["smoke"][0].text == "Hello world"

    summary["serialization"] = {
        "json_entities": [(ent.text, ent.label_) for ent in json_round_trip.ents],
        "disk_entities": [(ent.text, ent.label_) for ent in disk_doc.ents],
        "docbin_entities": [(ent.text, ent.label_) for ent in bin_docs[0].ents],
    }

    # Matchers and rulers.
    match_nlp = spacy.blank("en")

    matcher = Matcher(match_nlp.vocab, validate=True)
    matcher.add(
        "HELLO_WORLD",
        [[{"LOWER": "hello"}, {"IS_PUNCT": True}, {"LOWER": "world"}]],
    )
    match_doc = match_nlp("Hello, world! Hello world!")
    matcher_hits = matcher(match_doc)
    assert len(matcher_hits) == 1

    phrase_matcher = PhraseMatcher(match_nlp.vocab, attr="LOWER", validate=True)
    phrase_matcher.add("CITY", [match_nlp.make_doc("New York")])
    phrase_doc = match_nlp("New York is big.")
    phrase_hits = phrase_matcher(phrase_doc)
    assert len(phrase_hits) == 1

    dep_doc = Doc(
        match_nlp.vocab,
        words=["The", "quick", "brown", "fox", "jumped", "over", "the", "lazy", "fox"],
        heads=[3, 3, 3, 4, 4, 4, 8, 8, 5],
        deps=["det", "amod", "amod", "nsubj", "ROOT", "prep", "pobj", "det", "amod"],
    )
    dep_matcher = DependencyMatcher(match_nlp.vocab, validate=True)
    dep_pattern = [
        {"RIGHT_ID": "jumped", "RIGHT_ATTRS": {"ORTH": "jumped"}},
        {
            "LEFT_ID": "jumped",
            "REL_OP": ">",
            "RIGHT_ID": "fox",
            "RIGHT_ATTRS": {"ORTH": "fox"},
        },
    ]
    dep_matcher.add("JUMPED_FOX", [dep_pattern])
    dep_hits = dep_matcher(dep_doc)
    assert len(dep_hits) == 1
    assert dep_hits[0][1] == [4, 3]

    ruler_nlp = spacy.blank("en")
    entity_ruler = ruler_nlp.add_pipe(
        "entity_ruler", config={"phrase_matcher_attr": "LOWER", "validate": True}
    )
    entity_ruler.add_patterns(
        [
            {"label": "ORG", "pattern": "OpenAI", "id": "openai"},
            {"label": "GPE", "pattern": [{"LOWER": "new"}, {"LOWER": "york"}], "id": "new-york"},
        ]
    )
    ruler_doc = ruler_nlp("OpenAI is in New York.")
    assert [(ent.text, ent.label_, ent.ent_id_) for ent in ruler_doc.ents] == [
        ("OpenAI", "ORG", "openai"),
        ("New York", "GPE", "new-york"),
    ]

    span_nlp = spacy.blank("en")
    span_ruler = span_nlp.add_pipe("span_ruler", config={"validate": True})
    span_ruler.add_patterns(
        [
            {"label": "ORG", "pattern": "OpenAI", "id": "openai"},
            {"label": "GPE", "pattern": [{"LOWER": "new"}, {"LOWER": "york"}], "id": "new-york"},
        ]
    )
    span_doc = span_nlp("OpenAI is in New York.")
    assert [(span.text, span.label_) for span in span_doc.spans["ruler"]] == [
        ("OpenAI", "ORG"),
        ("New York", "GPE"),
    ]

    summary["matchers"] = {
        "matcher": [match_nlp.vocab.strings[m_id] for m_id, _, _ in matcher_hits],
        "phrase_matcher": [phrase_doc[start:end].text for _, start, end in phrase_hits],
        "dependency_matcher": dep_hits[0][1],
        "entity_ruler": [(ent.text, ent.label_) for ent in ruler_doc.ents],
        "span_ruler": [(span.text, span.label_) for span in span_doc.spans["ruler"]],
    }

    # Scoring basics tied to document annotations.
    score_nlp = spacy.blank("en")
    pred_doc = score_nlp("Apple is in New York.")
    ref_doc = score_nlp("Apple is in New York.")
    pred_doc.ents = [Span(pred_doc, 0, 1, label="ORG")]
    ref_doc.ents = [Span(ref_doc, 0, 1, label="ORG")]
    span_scores = Scorer.score_spans([Example(pred_doc, ref_doc)], "ents")
    assert span_scores["ents_f"] == 1.0
    summary["span_scores"] = span_scores["ents_f"]

    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
