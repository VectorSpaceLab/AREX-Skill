#!/usr/bin/env python3
"""Format label tokens for brightmart/text_classification seq2seq decoders.

The repository's seq2seq loaders create two fixed-length label arrays:
  decoder_input = [_GO] + labels[:decoder_length-1] + [_PAD]...
  target        = labels[:decoder_length-1] + [_END] + [_PAD]...
Both arrays are trimmed/padded to decoder_length.

This helper is self-contained and emits JSON so future agents can check label
shift logic without importing the original TensorFlow 1.x repository scripts.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable, List


def _split_labels(values: Iterable[str]) -> List[str]:
    labels: List[str] = []
    for value in values:
        for token in value.replace(",", " ").split():
            token = token.strip()
            if token:
                labels.append(token)
    return labels


def format_seq2seq_labels(
    labels: List[str],
    decoder_length: int,
    go_token: str = "_GO",
    end_token: str = "_END",
    pad_token: str = "_PAD",
) -> dict:
    if decoder_length < 1:
        raise ValueError("decoder_length must be at least 1")
    special = {go_token, end_token, pad_token}
    collisions = [label for label in labels if label in special]
    if collisions:
        raise ValueError(
            "ordinary labels must not equal special seq2seq tokens: "
            + ", ".join(sorted(set(collisions)))
        )

    capacity = max(decoder_length - 1, 0)
    kept_labels = labels[:capacity]
    truncated_labels = labels[capacity:]

    decoder_input = [go_token] + kept_labels
    decoder_input = decoder_input[:decoder_length]
    decoder_input.extend([pad_token] * (decoder_length - len(decoder_input)))

    target = kept_labels + [end_token]
    target = target[:decoder_length]
    target.extend([pad_token] * (decoder_length - len(target)))

    return {
        "decoder_length": decoder_length,
        "labels": labels,
        "kept_labels": kept_labels,
        "truncated_labels": truncated_labels,
        "truncated": bool(truncated_labels),
        "go_token": go_token,
        "end_token": end_token,
        "pad_token": pad_token,
        "decoder_input": decoder_input,
        "target": target,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Emit fixed-length decoder_input and target arrays for the "
            "brightmart/text_classification seq2seq label workflow."
        )
    )
    parser.add_argument(
        "labels",
        nargs="*",
        help=(
            "Label tokens. Each argument may also contain comma- or whitespace-"
            "separated labels, e.g. 'L1 L2' or L1,L2."
        ),
    )
    parser.add_argument(
        "--labels-stdin",
        action="store_true",
        help="Read additional labels from standard input.",
    )
    parser.add_argument(
        "--decoder-length",
        type=int,
        required=True,
        help="Fixed decoder sequence length used by the model.",
    )
    parser.add_argument("--go-token", default="_GO", help="Decoder start token.")
    parser.add_argument("--end-token", default="_END", help="Decoder end token.")
    parser.add_argument("--pad-token", default="_PAD", help="Decoder padding token.")
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation. Use 0 for compact single-line JSON.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    raw_values = list(args.labels)
    if args.labels_stdin:
        raw_values.append(sys.stdin.read())
    labels = _split_labels(raw_values)

    try:
        result = format_seq2seq_labels(
            labels=labels,
            decoder_length=args.decoder_length,
            go_token=args.go_token,
            end_token=args.end_token,
            pad_token=args.pad_token,
        )
    except ValueError as exc:
        parser.error(str(exc))

    indent = None if args.indent == 0 else args.indent
    print(json.dumps(result, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
