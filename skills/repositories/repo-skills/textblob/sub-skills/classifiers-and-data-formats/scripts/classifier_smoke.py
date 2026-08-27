#!/usr/bin/env python3
"""Safe smoke checks for TextBlob classifiers and data formats.

The script uses only tiny in-memory data and temporary files. It does not read
repository fixtures or require a particular current working directory.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny TextBlob NaiveBayesClassifier, optionally exercise "
            "DecisionTreeClassifier, and validate CSV/JSON/TSV/custom format detection."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit machine-readable JSON instead of a text summary",
    )
    parser.add_argument(
        "--skip-decision-tree",
        action="store_true",
        help="skip the optional DecisionTreeClassifier check",
    )
    return parser.parse_args()


def simple_features(document: Any) -> dict[str, bool]:
    """Corpus-free feature extractor that accepts strings or token iterables."""
    if isinstance(document, str):
        tokens = document.lower().split()
    else:
        tokens = [str(token).lower() for token in document]
    return {f"has({token})": True for token in tokens}


def write_temp_data(tmpdir: Path) -> dict[str, Path]:
    paths = {
        "csv": tmpdir / "train.csv",
        "json": tmpdir / "train.json",
        "tsv": tmpdir / "train.tsv",
        "psv_smoke": tmpdir / "train.psv",
    }
    rows = [
        ("good bright joy", "pos"),
        ("bad awful dull", "neg"),
        ("excellent happy win", "pos"),
        ("terrible poor loss", "neg"),
    ]
    paths["csv"].write_text("\n".join(f"{text},{label}" for text, label in rows) + "\n", encoding="utf-8")
    paths["tsv"].write_text("\n".join(f"{text}\t{label}" for text, label in rows) + "\n", encoding="utf-8")
    paths["psv_smoke"].write_text("\n".join(f"{text}|{label}" for text, label in rows) + "\n", encoding="utf-8")
    paths["json"].write_text(
        json.dumps(
            [{"text": text, "label": label} for text, label in rows],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return paths


def run_smoke(skip_decision_tree: bool) -> dict[str, Any]:
    from textblob import TextBlob, formats
    from textblob.classifiers import DecisionTreeClassifier, NaiveBayesClassifier

    train = [
        (["good", "bright", "joy"], "pos"),
        (["excellent", "happy", "win"], "pos"),
        (["bad", "awful", "dull"], "neg"),
        (["terrible", "poor", "loss"], "neg"),
    ]
    test = [
        ("good joy", "pos"),
        ("awful loss", "neg"),
    ]

    cl = NaiveBayesClassifier(train, feature_extractor=simple_features)
    nb_label = cl.classify("good bright")
    neg_label = cl.classify("awful poor")
    prob = cl.prob_classify("excellent joy")
    accuracy = cl.accuracy(test)
    before_len = len(cl.train_set)
    update_ok = cl.update([(["delight", "win"], "pos"), (["failure", "loss"], "neg")])
    after_len = len(cl.train_set)
    blob_label = TextBlob("good joy", classifier=cl).classify()

    if nb_label != "pos" or neg_label != "neg" or blob_label != "pos":
        raise AssertionError("NaiveBayes/TextBlob classification smoke produced unexpected labels")
    if not update_ok or after_len != before_len + 2:
        raise AssertionError("classifier update smoke failed")
    if accuracy < 0.5:
        raise AssertionError(f"unexpectedly low smoke accuracy: {accuracy}")

    result: dict[str, Any] = {
        "naive_bayes": {
            "positive_label": nb_label,
            "negative_label": neg_label,
            "labels": sorted(cl.labels()),
            "accuracy": accuracy,
            "probability_pos_for_excellent_joy": prob.prob("pos"),
            "updated_examples": after_len,
            "textblob_label": blob_label,
        }
    }

    if not skip_decision_tree:
        dt = DecisionTreeClassifier(train, feature_extractor=simple_features)
        dt_label = dt.classify("good win")
        pseudo = dt.pseudocode()
        pretty = dt.pretty_format(width=60)
        if dt_label != "pos" or "if" not in pseudo.lower() or not pretty.strip():
            raise AssertionError("DecisionTreeClassifier smoke failed")
        result["decision_tree"] = {
            "label": dt_label,
            "pseudocode_contains_if": "if" in pseudo.lower(),
            "pretty_format_nonempty": bool(pretty.strip()),
        }
    else:
        result["decision_tree"] = "skipped"

    with tempfile.TemporaryDirectory(prefix="textblob-classifier-smoke-") as tmp:
        paths = write_temp_data(Path(tmp))

        class PipeDelimitedFormat(formats.DelimitedFormat):
            delimiter = "|"

        formats.register("psv_smoke", PipeDelimitedFormat)
        expected = {
            "csv": "CSV",
            "json": "JSON",
            "tsv": "TSV",
            "psv_smoke": "PipeDelimitedFormat",
        }
        detected: dict[str, str] = {}
        parsed_lengths: dict[str, int] = {}
        for name, path in paths.items():
            with path.open(encoding="utf-8", newline="") as fp:
                fmt_cls = formats.detect(fp)
                if fmt_cls is None:
                    raise AssertionError(f"format detection failed for {name}")
                detected[name] = fmt_cls.__name__
                parsed_lengths[name] = len(list(fmt_cls(fp).to_iterable()))

        if detected != expected:
            raise AssertionError(f"unexpected detected formats: {detected!r}")
        if any(length != 4 for length in parsed_lengths.values()):
            raise AssertionError(f"unexpected parsed lengths: {parsed_lengths!r}")
        registry_keys = sorted(k for k in formats.get_registry().keys() if k in {"csv", "json", "tsv", "psv_smoke"})

    result["formats"] = {
        "detected": detected,
        "parsed_lengths": parsed_lengths,
        "registry_keys_present": registry_keys,
    }
    return result


def main() -> int:
    args = parse_args()
    try:
        result = run_smoke(skip_decision_tree=args.skip_decision_tree)
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failure.
        if args.as_json:
            print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps({"status": "ok", **result}, indent=2, sort_keys=True))
    else:
        print("TextBlob classifier smoke: ok")
        print(f"NaiveBayes labels: {', '.join(result['naive_bayes']['labels'])}")
        print(f"NaiveBayes accuracy: {result['naive_bayes']['accuracy']:.3f}")
        print(f"DecisionTree: {result['decision_tree']}")
        print(f"Formats detected: {result['formats']['detected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
