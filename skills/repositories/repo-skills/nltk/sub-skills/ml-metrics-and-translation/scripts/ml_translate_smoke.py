#!/usr/bin/env python3
"""Tiny no-download smoke check for NLTK ML/metrics/translation APIs."""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


def _assert_close(name: str, value: float, expected: float, tol: float = 1e-9) -> None:
    if not math.isclose(value, expected, rel_tol=tol, abs_tol=tol):
        raise AssertionError(f"{name}: expected {expected!r}, got {value!r}")


def run_smoke() -> dict[str, Any]:
    """Run deterministic in-memory checks and return a compact summary."""
    try:
        from nltk.classify import NaiveBayesClassifier, accuracy as classifier_accuracy
        from nltk.lm import Lidstone
        from nltk.lm.preprocessing import padded_everygram_pipeline, padded_everygrams
        from nltk.metrics import f_measure, precision, recall
        from nltk.probability import ELEProbDist, FreqDist
        from nltk.translate import Alignment, AlignedSent, IBMModel1, alignment_error_rate
        from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
    except Exception as exc:  # pragma: no cover - message path only
        raise RuntimeError(
            "Could not import the required NLTK APIs. Install NLTK with its base "
            "runtime dependencies in the active Python environment."
        ) from exc

    # Classifier: feature dictionaries + Naive Bayes.
    train = [
        ({"word:good": True, "has_exclaim": False}, "pos"),
        ({"word:great": True, "has_exclaim": True}, "pos"),
        ({"word:bad": True, "has_exclaim": False}, "neg"),
        ({"word:awful": True, "has_exclaim": True}, "neg"),
    ]
    classifier = NaiveBayesClassifier.train(train)
    nb_label = classifier.classify({"word:good": True, "has_exclaim": True})
    nb_accuracy = classifier_accuracy(classifier, train)
    if nb_label != "pos":
        raise AssertionError(f"NaiveBayes label: expected 'pos', got {nb_label!r}")
    if nb_accuracy < 0.75:
        raise AssertionError(f"NaiveBayes training accuracy too low: {nb_accuracy!r}")

    # Probability: counts and smoothed distribution.
    fd = FreqDist(["red", "blue", "red", "green"])
    if fd.N() != 4 or fd.B() != 3 or fd["red"] != 2:
        raise AssertionError(f"Unexpected FreqDist summary: N={fd.N()} B={fd.B()} red={fd['red']}")
    pdist = ELEProbDist(fd, bins=4)
    if pdist.prob("missing") <= 0:
        raise AssertionError("ELEProbDist should assign non-zero probability to an unseen bin")

    # Language model: padded bigrams + Lidstone smoothing + <UNK> lookup.
    sentences = [["a", "b", "a"], ["a", "c"]]
    train_data, vocab_data = padded_everygram_pipeline(2, sentences)
    lm = Lidstone(0.1, 2)
    lm.fit(train_data, vocab_data)
    seen_score = lm.score("a", ("b",))
    unseen_score = lm.score("alien", ("b",))
    if not (seen_score > unseen_score > 0):
        raise AssertionError(f"Expected seen > unseen > 0, got {seen_score!r}, {unseen_score!r}")
    if lm.vocab.lookup("alien") != "<UNK>":
        raise AssertionError("Vocabulary did not map unseen word to <UNK>")
    entropy = lm.entropy(list(padded_everygrams(2, ["a", "b", "a"])))
    if not math.isfinite(entropy):
        raise AssertionError(f"Expected finite smoothed entropy, got {entropy!r}")

    # Metrics and short-translation scoring.
    reference = {"NP@0", "VP@2", "NP@4"}
    predicted = {"NP@0", "NP@4", "PP@5"}
    prec = precision(reference, predicted)
    rec = recall(reference, predicted)
    f1 = f_measure(reference, predicted)
    _assert_close("precision", prec, 2 / 3)
    _assert_close("recall", rec, 2 / 3)
    _assert_close("f_measure", f1, 2 / 3)

    bleu = sentence_bleu(
        [["the", "cat", "sat"], ["a", "cat", "is", "sitting"]],
        ["the", "cat", "is", "sitting"],
        smoothing_function=SmoothingFunction().method1,
    )
    if not (0 < bleu <= 1):
        raise AssertionError(f"Expected smoothed BLEU in (0, 1], got {bleu!r}")

    # Alignment and IBM Model 1: tiny in-memory parallel corpus.
    gold = Alignment.fromstring("0-0 1-1")
    hyp = Alignment([(0, 0), (1, 0)])
    aer = alignment_error_rate(gold, hyp)
    _assert_close("alignment_error_rate", aer, 0.5)

    corpus = [
        AlignedSent(["the", "house"], ["das", "Haus"]),
        AlignedSent(["the", "book"], ["das", "Buch"]),
        AlignedSent(["a", "book"], ["ein", "Buch"]),
    ]
    ibm1 = IBMModel1(corpus, 20)
    if round(ibm1.translation_table["the"]["das"], 1) != 1.0:
        raise AssertionError("IBMModel1 did not learn the expected 'das' -> 'the' relation")
    if str(corpus[0].alignment) != "0-0 1-1":
        raise AssertionError(f"Unexpected IBMModel1 alignment: {corpus[0].alignment}")

    return {
        "naive_bayes_label": nb_label,
        "naive_bayes_train_accuracy": round(nb_accuracy, 6),
        "freqdist": {"N": fd.N(), "B": fd.B(), "red": fd["red"]},
        "lidstone_seen_score": round(seen_score, 6),
        "lidstone_unseen_score": round(unseen_score, 6),
        "lidstone_entropy": round(entropy, 6),
        "precision_recall_f": [round(prec, 6), round(rec, 6), round(f1, 6)],
        "sentence_bleu_smoothed": round(bleu, 6),
        "alignment_error_rate": round(aer, 6),
        "ibm1_the_given_das": round(ibm1.translation_table["the"]["das"], 6),
        "ibm1_first_alignment": str(corpus[0].alignment),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic no-download smoke check for NLTK ML, metrics, LM, and translation APIs."
    )
    parser.add_argument("--json", action="store_true", help="emit the smoke summary as JSON")
    args = parser.parse_args(argv)

    try:
        summary = run_smoke()
    except Exception as exc:
        print(f"ml_translate_smoke: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print("ml_translate_smoke: OK")
        for key in sorted(summary):
            print(f"  {key}: {summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
