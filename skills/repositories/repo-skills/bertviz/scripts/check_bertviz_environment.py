#!/usr/bin/env python3
"""Check a BertViz runtime without downloading models.

The script verifies imports, public signatures, packaged JavaScript assets, and
optionally neuron-view modified model/tokenizer exports. It is safe to run from
any current working directory.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from importlib import resources
from importlib.metadata import PackageNotFoundError, version
from typing import Iterable


EXPECTED = {
    "head_view": "(attention=None, tokens=None, sentence_b_start=None, prettify_tokens=True, layer=None, heads=None, encoder_attention=None, decoder_attention=None, cross_attention=None, encoder_tokens=None, decoder_tokens=None, include_layers=None, html_action='view')",
    "model_view": "(attention=None, tokens=None, sentence_b_start=None, prettify_tokens=True, display_mode='dark', encoder_attention=None, decoder_attention=None, cross_attention=None, encoder_tokens=None, decoder_tokens=None, include_layers=None, include_heads=None, html_action='view')",
    "show": "(model, model_type, tokenizer, sentence_a, sentence_b=None, display_mode='dark', layer=None, head=None, html_action='view')",
    "get_attention": "(model, model_type, tokenizer, sentence_a, sentence_b=None, include_queries_and_keys=False)",
}

JS_ASSETS = ["head_view.js", "model_view.js", "neuron_view.js"]
NEURON_EXPORTS = [
    "BertModel",
    "BertTokenizer",
    "BertConfig",
    "BertForSequenceClassification",
    "BertForQuestionAnswering",
    "GPT2Model",
    "GPT2Tokenizer",
    "RobertaModel",
    "RobertaTokenizer",
    "XLNetModel",
    "XLNetTokenizer",
]


def _fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _check_signature(name: str, obj) -> None:
    actual = str(inspect.signature(obj))
    expected = EXPECTED[name]
    if actual != expected:
        _fail(f"Unexpected signature for {name}: {actual} != {expected}")
    print(f"OK: {name} signature {actual}")


def _check_js_assets() -> None:
    try:
        root = resources.files("bertviz")
    except Exception as exc:  # pragma: no cover - importlib/resources edge
        _fail(f"Could not inspect bertviz package resources: {exc}")
    for asset in JS_ASSETS:
        candidate = root / asset
        if not candidate.is_file():
            _fail(f"Missing packaged JavaScript asset: bertviz/{asset}")
        print(f"OK: packaged asset bertviz/{asset}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify BertViz imports, signatures, and package assets without model downloads.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--include-neuron-view",
        action="store_true",
        help="Also import bertviz.neuron_view and modified transformers_neuron_view exports.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        import bertviz
        from bertviz import head_view, model_view
    except ImportError as exc:
        _fail(f"Could not import BertViz root APIs: {exc}")

    try:
        print(f"OK: bertviz distribution version {version('bertviz')}")
    except PackageNotFoundError:
        print("WARN: bertviz distribution metadata not found, but imports succeeded")

    _check_signature("head_view", head_view)
    _check_signature("model_view", model_view)
    _check_js_assets()

    if args.include_neuron_view:
        try:
            from bertviz.neuron_view import get_attention, show
            import bertviz.transformers_neuron_view as tnv
        except ImportError as exc:
            _fail(f"Could not import neuron-view APIs: {exc}")
        _check_signature("show", show)
        _check_signature("get_attention", get_attention)
        missing = [name for name in NEURON_EXPORTS if not hasattr(tnv, name)]
        if missing:
            _fail(f"Missing neuron-view exports: {', '.join(missing)}")
        print("OK: neuron-view modified model/tokenizer exports available")

    print("BertViz environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
