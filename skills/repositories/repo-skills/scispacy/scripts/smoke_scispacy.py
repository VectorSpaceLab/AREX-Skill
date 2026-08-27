#!/usr/bin/env python3
"""Run small, deterministic scispaCy smoke checks.

This helper is safe to run from any working directory. It checks:

- the scispaCy package import,
- the biomedical tokenizer / abbreviation / hyponym component path,
- the whitespace tokenizer path used for pretokenized text, and
- a tiny in-memory linker build using the installed linker dependencies.

Example:
    python scripts/smoke_scispacy.py --mode all
    python scripts/smoke_scispacy.py --mode components --sci-model en_core_sci_sm
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import spacy

import scispacy
import scispacy.abbreviation  # register abbreviation_detector
import scispacy.hyponym_detector  # register hyponym_detector
from scispacy.util import WhitespaceTokenizer

try:
    from scispacy.candidate_generation import CandidateGenerator, create_tfidf_ann_index
    from scispacy.linking_utils import KnowledgeBase
except ImportError as exc:  # pragma: no cover - diagnostic helper
    raise SystemExit(
        "Missing optional linker dependencies. Install scispacy's runtime dependencies, "
        "including nmslib, scipy, and scikit-learn, before running the linker smoke."
    ) from exc


COMPONENT_TEXT = "Spinal and bulbar muscular atrophy (SBMA) is a disease."
HYPONYM_TEXT = "Keystone plant species such as fig trees are important."
WHITESPACE_TEXT = "don't split this contraction."


def load_model(name: str, purpose: str) -> spacy.language.Language:
    try:
        return spacy.load(name)
    except Exception as exc:  # pragma: no cover - diagnostic helper
        raise SystemExit(
            f"Missing or incompatible spaCy model package {name!r} required for {purpose}. "
            f"Install the model package before running this smoke test."
        ) from exc


def run_component_smoke(sci_model: str, web_model: str) -> None:
    sci_nlp = load_model(sci_model, "abbreviation and hyponym smoke")
    sci_nlp.add_pipe("abbreviation_detector")
    doc = sci_nlp(COMPONENT_TEXT)
    assert len(doc._.abbreviations) == 1, doc._.abbreviations
    assert doc._.abbreviations[0]._.long_form.text == "Spinal and bulbar muscular atrophy"

    sci_nlp = load_model(sci_model, "hyponym smoke")
    sci_nlp.add_pipe("hyponym_detector", last=True, config={"extended": True})
    doc = sci_nlp(HYPONYM_TEXT)
    assert doc._.hearst_patterns, "Expected at least one Hearst-pattern hit"
    assert doc._.hearst_patterns[0][0] == "such_as", doc._.hearst_patterns

    web_nlp = load_model(web_model, "whitespace tokenization smoke")
    web_nlp.tokenizer = WhitespaceTokenizer(web_nlp.vocab)
    assert [t.text for t in web_nlp(WHITESPACE_TEXT)] == ["don't", "split", "this", "contraction."]

    print("component smoke passed")


def run_linker_smoke() -> None:
    entities = []
    for i in range(10):
        entities.append(
            {
                "concept_id": f"C{i:07d}",
                "canonical_name": f"Alias {i}",
                "aliases": [f"Alias {i}", f"Alias common {i}"],
                "types": ["T000"],
                "definition": "d",
            }
        )

    with tempfile.TemporaryDirectory() as td:
        kb_path = Path(td) / "kb.json"
        kb_path.write_text(json.dumps(entities))
        kb = KnowledgeBase(kb_path)
        concept_aliases, tfidf_vectorizer, ann_index = create_tfidf_ann_index(None, kb)
        generator = CandidateGenerator(ann_index, tfidf_vectorizer, concept_aliases, kb)
        results = generator(["Alias 3"], 5)

    assert results and results[0], "Expected at least one linker candidate"
    assert results[0][0].concept_id.startswith("C")
    print("linker smoke passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("components", "linker", "all"),
        default="all",
        help="Which smoke checks to run.",
    )
    parser.add_argument(
        "--sci-model",
        default="en_core_sci_sm",
        help="Biomedical spaCy model used for abbreviation and hyponym checks.",
    )
    parser.add_argument(
        "--web-model",
        default="en_core_web_sm",
        help="General English spaCy model used for the whitespace tokenizer check.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(f"scispacy={scispacy.__version__} spacy={spacy.__version__}")

    if args.mode in {"components", "all"}:
        run_component_smoke(args.sci_model, args.web_model)

    if args.mode in {"linker", "all"}:
        run_linker_smoke()

    print(f"smoke {args.mode} passed")


if __name__ == "__main__":
    main()
