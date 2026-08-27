#!/usr/bin/env python3
"""Validate BertViz neuron-view attention extraction with a toy BERT model.

This helper is self-contained and does not download pretrained weights. It
creates a tiny BERT config and vocabulary in a temporary directory, runs
bertviz.neuron_view.get_attention, and verifies the same core invariants as the
repo's safe toy BERT unit test.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence


CONFIG = {
    "num_hidden_layers": 12,
    "vocab_size": 18,
    "hidden_size": 12,
    "max_position_embeddings": 64,
    "type_vocab_size": 2,
    "hidden_dropout_prob": 0.1,
    "num_attention_heads": 3,
    "attention_probs_dropout_prob": 0.1,
    "intermediate_size": 6,
}

VOCAB = [
    "[PAD]",
    "[UNK]",
    "the",
    "quick",
    "##est",
    "brown",
    "fox",
    "##iest",
    "jumped",
    "over",
    "##zie",
    "##st",
    "dog",
    ".",
    "lazy",
    "la",
    "[SEP]",
    "[CLS]",
]

SENTENCE_A = "The quickest brown fox jumped over the lazy dog"
SENTENCE_B = "the quick brown fox jumped over the laziest elmo"
TOKENS_A = [
    "[CLS]",
    "the",
    "quick",
    "##est",
    "brown",
    "fox",
    "jumped",
    "over",
    "the",
    "lazy",
    "dog",
    "[SEP]",
]
TOKENS_B = [
    "the",
    "quick",
    "brown",
    "fox",
    "jumped",
    "over",
    "the",
    "la",
    "##zie",
    "##st",
    "[UNK]",
    "[SEP]",
]


def _fatal(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _import_runtime():
    try:
        import torch
        from bertviz.neuron_view import get_attention
        from bertviz.transformers_neuron_view import (
            BertConfig,
            BertForQuestionAnswering,
            BertForSequenceClassification,
            BertModel,
            BertTokenizer,
            GPT2Config,
            GPT2Model,
        )
    except ImportError as exc:  # pragma: no cover - environment specific
        _fatal(f"Missing BertViz neuron-view runtime dependency: {exc}")

    return {
        "torch": torch,
        "get_attention": get_attention,
        "BertConfig": BertConfig,
        "BertForQuestionAnswering": BertForQuestionAnswering,
        "BertForSequenceClassification": BertForSequenceClassification,
        "BertModel": BertModel,
        "BertTokenizer": BertTokenizer,
        "GPT2Config": GPT2Config,
        "GPT2Model": GPT2Model,
    }


def _write_toy_files(tmpdir: Path) -> tuple[Path, Path]:
    config_path = tmpdir / "config.json"
    vocab_path = tmpdir / "vocab.txt"
    config_path.write_text(json.dumps(CONFIG), encoding="utf-8")
    vocab_path.write_text("\n".join(VOCAB) + "\n", encoding="utf-8")
    return config_path, vocab_path


def _assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        _fatal(f"{label} mismatch:\nactual={actual!r}\nexpected={expected!r}")


def _assert_close_tensor(torch, actual, expected, label: str, atol: float = 1e-5) -> None:
    if not torch.allclose(actual, expected, atol=atol):
        max_diff = torch.max(torch.abs(actual - expected)).item()
        _fatal(f"{label} tensors differ (max diff {max_diff})")


def _validate_attention_partitions(torch, attn_data: dict) -> None:
    _assert_equal(sorted(attn_data.keys()), ["aa", "ab", "all", "ba", "bb"], "sentence-pair keys")
    _assert_equal(attn_data["all"]["left_text"], TOKENS_A + TOKENS_B, "all left_text")
    _assert_equal(attn_data["all"]["right_text"], TOKENS_A + TOKENS_B, "all right_text")
    _assert_equal(attn_data["aa"]["left_text"], TOKENS_A, "aa left_text")
    _assert_equal(attn_data["aa"]["right_text"], TOKENS_A, "aa right_text")
    _assert_equal(attn_data["ab"]["left_text"], TOKENS_A, "ab left_text")
    _assert_equal(attn_data["ab"]["right_text"], TOKENS_B, "ab right_text")
    _assert_equal(attn_data["ba"]["left_text"], TOKENS_B, "ba left_text")
    _assert_equal(attn_data["ba"]["right_text"], TOKENS_A, "ba right_text")
    _assert_equal(attn_data["bb"]["left_text"], TOKENS_B, "bb left_text")
    _assert_equal(attn_data["bb"]["right_text"], TOKENS_B, "bb right_text")

    attn_all = attn_data["all"]["attn"]
    for layer_idx, layer in enumerate(attn_all):
        attn_all_layer = torch.tensor(layer)
        num_heads, seq_len, _ = attn_all_layer.size()
        sums = attn_all_layer.sum(dim=-1)
        _assert_close_tensor(torch, sums, torch.ones(num_heads, seq_len), f"probability sums layer {layer_idx}")

        top = torch.cat((torch.tensor(attn_data["aa"]["attn"][layer_idx]), torch.tensor(attn_data["ab"]["attn"][layer_idx])), dim=-1)
        bottom = torch.cat((torch.tensor(attn_data["ba"]["attn"][layer_idx]), torch.tensor(attn_data["bb"]["attn"][layer_idx])), dim=-1)
        whole = torch.cat((top, bottom), dim=-2)
        _assert_close_tensor(torch, whole, attn_all_layer, f"partition reassembly layer {layer_idx}")


def _validate_query_key_schema(attn_data: dict) -> None:
    for key in ["all", "aa", "ab", "ba", "bb"]:
        block = attn_data[key]
        for field in ["queries", "keys"]:
            if field not in block:
                _fatal(f"Missing {field!r} in {key!r} block")
            if len(block[field]) != CONFIG["num_hidden_layers"]:
                _fatal(f"Unexpected layer count for {key}.{field}: {len(block[field])}")
            if len(block[field][0]) != CONFIG["num_attention_heads"]:
                _fatal(f"Unexpected head count for {key}.{field}: {len(block[field][0])}")


def _validate_single_sentence(torch, get_attention, model, tokenizer) -> None:
    data = get_attention(model, "bert", tokenizer, SENTENCE_A, None, include_queries_and_keys=False)
    if "aa" in data:
        _fatal("Single-sentence get_attention unexpectedly returned sentence-pair keys")
    _assert_equal(data["all"]["left_text"], TOKENS_A, "single left_text")
    for layer_idx, layer in enumerate(data["all"]["attn"]):
        attn = torch.tensor(layer)
        sums = attn.sum(dim=-1)
        _assert_close_tensor(torch, sums, torch.ones(attn.size(0), attn.size(1)), f"single probability sums layer {layer_idx}")


def _validate_errors(get_attention, model, tokenizer, runtime) -> None:
    try:
        get_attention(model, "bad", tokenizer, SENTENCE_A)
    except ValueError:
        pass
    else:
        _fatal("Invalid model_type did not raise ValueError")

    try:
        get_attention(model, "bert", tokenizer, "")
    except ValueError:
        pass
    else:
        _fatal("Empty sentence_a did not raise ValueError")

    gpt2_config = runtime["GPT2Config"](vocab_size_or_config_json_file=20, n_positions=8, n_ctx=8, n_embd=8, n_layer=1, n_head=2)
    gpt2_model = runtime["GPT2Model"](gpt2_config)
    try:
        get_attention(gpt2_model, "gpt2", tokenizer, "hello", "world")
    except ValueError:
        pass
    else:
        _fatal("GPT-2 sentence pair did not raise ValueError")

    try:
        get_attention(model, "xlnet", tokenizer, "hello", "world")
    except NotImplementedError:
        pass
    except Exception as exc:
        _fatal(f"XLNet sentence pair raised the wrong exception type: {type(exc).__name__}: {exc}")
    else:
        _fatal("XLNet sentence pair did not raise NotImplementedError")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate BertViz neuron-view get_attention with a no-network toy BERT model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--skip-task-heads",
        action="store_true",
        help="Validate only BertModel instead of BertModel plus BERT task-head subclasses.",
    )
    parser.add_argument(
        "--include-query-key-schema",
        action="store_true",
        help="Also request include_queries_and_keys=True and validate query/key schema.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    runtime = _import_runtime()
    torch = runtime["torch"]
    get_attention = runtime["get_attention"]

    with tempfile.TemporaryDirectory(prefix="bertviz-toy-") as tmp:
        config_path, vocab_path = _write_toy_files(Path(tmp))
        config = runtime["BertConfig"].from_json_file(str(config_path))
        tokenizer = runtime["BertTokenizer"](str(vocab_path))
        model_classes = [runtime["BertModel"]]
        if not args.skip_task_heads:
            model_classes.extend([runtime["BertForSequenceClassification"], runtime["BertForQuestionAnswering"]])

        for model_class in model_classes:
            model = model_class(config)
            model.eval()
            data = get_attention(
                model,
                "bert",
                tokenizer,
                SENTENCE_A,
                SENTENCE_B,
                include_queries_and_keys=args.include_query_key_schema,
            )
            _validate_attention_partitions(torch, data)
            if args.include_query_key_schema:
                _validate_query_key_schema(data)
            _validate_single_sentence(torch, get_attention, model, tokenizer)
            _validate_errors(get_attention, model, tokenizer, runtime)
            print(f"OK: {model_class.__name__} toy attention validated")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
