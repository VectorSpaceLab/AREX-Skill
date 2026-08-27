#!/usr/bin/env python
"""Assert the installed spaCy factory registry and print pipe analysis.

Run this from any working directory. It imports the installed public `spacy`
package, checks the primary pipeline-component factories, assembles a blank
pipeline, and prints `analyze_pipes` output.
"""

from __future__ import annotations

import argparse
import json
import signal
from typing import Iterable, List

import spacy
from spacy.util import registry

signal.signal(signal.SIGPIPE, signal.SIG_DFL)

PRIMARY_FACTORIES: List[str] = [
    "sentencizer",
    "entity_ruler",
    "span_ruler",
    "attribute_ruler",
    "lemmatizer",
    "trainable_lemmatizer",
    "tok2vec",
    "tagger",
    "morphologizer",
    "parser",
    "senter",
    "ner",
    "textcat",
    "textcat_multilabel",
    "spancat",
    "entity_linker",
    "doc_cleaner",
    "token_splitter",
]

OPTIONAL_FACTORIES: List[str] = [
    "spancat_singlelabel",
    "span_finder",
    "beam_ner",
    "beam_parser",
    "future_entity_ruler",
    "nn_labeller",
]

SMOKE_PIPELINE: List[str] = PRIMARY_FACTORIES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect spaCy pipeline factories and pipe analysis."
    )
    parser.add_argument("--lang", default="en", help="Language code for blank pipeline")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of a human-readable report",
    )
    return parser.parse_args()


def assert_factories(nlp: spacy.language.Language, names: Iterable[str]) -> None:
    missing = [name for name in names if not nlp.has_factory(name)]
    if missing:
        raise SystemExit(f"Missing factories for {nlp.lang}: {', '.join(missing)}")


def build_pipeline(nlp: spacy.language.Language) -> spacy.language.Language:
    for name in SMOKE_PIPELINE:
        nlp.add_pipe(name)
    return nlp


def main() -> int:
    args = parse_args()
    registry.ensure_populated()

    nlp = spacy.blank(args.lang)
    assert_factories(nlp, PRIMARY_FACTORIES)
    optional_present = [name for name in OPTIONAL_FACTORIES if nlp.has_factory(name)]

    build_pipeline(nlp)
    analysis = nlp.analyze_pipes(pretty=False)
    if any(analysis["problems"].values()):
        raise SystemExit(json.dumps(analysis["problems"], indent=2, default=str))

    if args.json:
        payload = {
            "spacy_version": spacy.__version__,
            "language": nlp.lang,
            "registry_factory_count": len(registry.factories.get_all()),
            "required_factories": PRIMARY_FACTORIES,
            "optional_factories_present": optional_present,
            "pipe_names": nlp.pipe_names,
            "pipe_factories": dict(nlp.pipe_factories),
            "analysis": analysis,
        }
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0

    print(f"spaCy version: {spacy.__version__}")
    print(f"Language: {nlp.lang}")
    print(f"Registry factories: {len(registry.factories.get_all())}")
    print("Required factories: " + ", ".join(PRIMARY_FACTORIES))
    if optional_present:
        print("Optional factories present: " + ", ".join(optional_present))
    print("Pipeline: " + ", ".join(nlp.pipe_names))
    print("Pipe factories: " + ", ".join(f"{k}={v}" for k, v in nlp.pipe_factories.items()))
    nlp.analyze_pipes(pretty=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        pass
