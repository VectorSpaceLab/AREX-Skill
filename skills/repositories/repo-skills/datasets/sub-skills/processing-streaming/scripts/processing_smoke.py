#!/usr/bin/env python3
"""Self-contained smoke checks for datasets processing and streaming APIs."""

from __future__ import annotations

import argparse
import itertools
import json
from typing import Any, Iterable


def duplicate_tokens(batch: dict[str, list[str]]) -> dict[str, list[str]]:
    return {"token": [token for text in batch["text"] for token in text.split()]}


def add_length(example: dict[str, object]) -> dict[str, int]:
    return {"length": len(str(example["text"]).split())}


def keep_nonempty(example: dict[str, object]) -> bool:
    return bool(str(example["text"]).strip())


def make_stream(iterable_dataset_cls: Any, values: Iterable[str]) -> Any:
    def generator() -> Iterable[dict[str, str]]:
        for value in values:
            yield {"text": value}

    return iterable_dataset_cls.from_generator(generator)


def run_smoke(buffer_size: int) -> dict[str, object]:
    try:
        from datasets import Dataset, Features, IterableDataset, Value, concatenate_datasets, interleave_datasets
    except ModuleNotFoundError as error:
        raise SystemExit(
            "This smoke check requires an environment where the datasets package and its runtime dependencies are installed. "
            f"Missing module: {error.name}"
        ) from error

    dataset = Dataset.from_dict({"text": ["red blue", "green", "", "blue red"], "label": [0, 1, 0, 1]})

    processed = dataset.filter(keep_nonempty).map(add_length)
    split = processed.train_test_split(test_size=0.5, seed=7)

    token_features = Features({"token": Value("string")})
    tokens = dataset.map(
        duplicate_tokens,
        batched=True,
        remove_columns=dataset.column_names,
        features=token_features,
    )

    iterable = dataset.to_iterable_dataset(num_shards=2).shuffle(seed=11, buffer_size=buffer_size)
    iterable_head = list(itertools.islice(iterable, 3))

    stream = make_stream(IterableDataset, ["alpha beta", "", "gamma"])
    stream_processed = stream.filter(keep_nonempty).map(add_length)
    stream_head = list(itertools.islice(stream_processed, 2))

    concatenated = concatenate_datasets([tokens.select([0]), tokens.select([1])])
    interleaved = interleave_datasets(
        [Dataset.from_dict({"source": ["a0", "a1"]}), Dataset.from_dict({"source": ["b0", "b1"]})]
    )

    torch_format_available = True
    try:
        formatted = processed.with_format("torch", columns=["label", "length"])
        _ = formatted[0]
    except Exception:
        torch_format_available = False

    return {
        "processed_rows": len(processed),
        "split_names": sorted(split.keys()),
        "token_rows": len(tokens),
        "tokens": tokens["token"],
        "iterable_head_size": len(iterable_head),
        "stream_lengths": [row["length"] for row in stream_head],
        "concatenated_rows": len(concatenated),
        "interleaved_sources": interleaved["source"],
        "torch_format_available": torch_format_available,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run dependency-light smoke checks for datasets map/filter/batching/streaming/combine behavior."
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=2,
        help="Shuffle buffer size for the local iterable smoke check. Default: 2.",
    )
    parser.add_argument("--json", action="store_true", help="Print the smoke summary as JSON.")
    args = parser.parse_args()

    if args.buffer_size < 1:
        raise SystemExit("--buffer-size must be >= 1")

    summary = run_smoke(buffer_size=args.buffer_size)
    expected = {
        "processed_rows": 3,
        "split_names": ["test", "train"],
        "token_rows": 5,
        "tokens": ["red", "blue", "green", "blue", "red"],
        "iterable_head_size": 3,
        "stream_lengths": [2, 1],
        "concatenated_rows": 2,
        "interleaved_sources": ["a0", "b0", "a1", "b1"],
    }
    for key, value in expected.items():
        if summary[key] != value:
            raise AssertionError(f"{key}: expected {value!r}, got {summary[key]!r}")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("datasets processing smoke passed")
        print(f"token rows: {summary['token_rows']} | stream lengths: {summary['stream_lengths']}")
        print(f"torch formatter available: {summary['torch_format_available']}")


if __name__ == "__main__":
    main()
