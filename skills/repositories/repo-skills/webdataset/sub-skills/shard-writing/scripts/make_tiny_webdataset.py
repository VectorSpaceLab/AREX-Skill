#!/usr/bin/env python3
"""Generate a deterministic tiny WebDataset shard set and validate round-trip reading.

This helper stays local on purpose. It writes a few samples with common WebDataset
field types, forces a small rollover, and then reads the result back through the
reader pipeline to verify that the written shards are usable.
"""

from __future__ import annotations

import argparse
import math
import tempfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import webdataset as wds


def fail(message: str) -> None:
    raise RuntimeError(message)


def make_image(index: int) -> np.ndarray:
    """Build a tiny deterministic RGB image."""
    base = index % 256
    return np.array(
        [
            [[base, 0, 255 - base], [0, base, 255 - base]],
            [[255 - base, base, 0], [base, 255 - base, 0]],
        ],
        dtype=np.uint8,
    )


def make_sample(index: int) -> dict[str, Any]:
    """Build one deterministic sample with common WebDataset value types."""
    return {
        "__key__": f"tiny-{index:03d}",
        "txt.gz": f"sample {index}\n",
        "cls": str(index),
        "json": {"index": index, "square": index * index},
        "npy": np.array([[index, index + 1], [index + 2, index + 3]], dtype=np.int32),
        "npz": {"value": np.array([index], dtype=np.int64)},
        "ten": [np.array([[index, index + 1]], dtype=np.float32)],
        "png": make_image(index),
    }


def expected_shard_paths(output_dir: Path, pattern: str, samples: int, maxcount: int) -> list[Path]:
    n_shards = max(1, math.ceil(samples / maxcount))
    return [output_dir / (pattern % shard_index) for shard_index in range(n_shards)]


def compare_arrays(name: str, actual: Any, expected: np.ndarray) -> None:
    if not isinstance(actual, np.ndarray):
        fail(f"{name}: expected numpy.ndarray, got {type(actual).__name__}")
    if actual.shape != expected.shape:
        fail(f"{name}: shape mismatch, expected {expected.shape}, got {actual.shape}")
    if actual.dtype != expected.dtype:
        fail(f"{name}: dtype mismatch, expected {expected.dtype}, got {actual.dtype}")
    if not np.array_equal(actual, expected):
        fail(f"{name}: array values differ")


def compare_ten(name: str, actual: Any, expected: Iterable[np.ndarray]) -> None:
    if not isinstance(actual, list):
        fail(f"{name}: expected list, got {type(actual).__name__}")
    expected_list = list(expected)
    if len(actual) != len(expected_list):
        fail(f"{name}: list length mismatch, expected {len(expected_list)}, got {len(actual)}")
    for idx, (a_item, e_item) in enumerate(zip(actual, expected_list)):
        compare_arrays(f"{name}[{idx}]", a_item, e_item)


def compare_npz(name: str, actual: Any, expected: dict[str, np.ndarray]) -> None:
    if not isinstance(actual, dict):
        fail(f"{name}: expected dict, got {type(actual).__name__}")
    if set(actual) != set(expected):
        fail(f"{name}: key mismatch, expected {sorted(expected)}, got {sorted(actual)}")
    for key, expected_value in expected.items():
        compare_arrays(f"{name}.{key}", actual[key], expected_value)


def compare_sample(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    if actual.get("__key__") != expected["__key__"]:
        fail(f"__key__: expected {expected['__key__']!r}, got {actual.get('__key__')!r}")

    payload_keys = {key for key in actual if not key.startswith("_")}
    expected_keys = {key for key in expected if not key.startswith("_")}
    if payload_keys != expected_keys:
        fail(f"payload keys mismatch, expected {sorted(expected_keys)}, got {sorted(payload_keys)}")

    if actual["txt.gz"] != expected["txt.gz"]:
        fail(f"txt.gz: expected {expected['txt.gz']!r}, got {actual['txt.gz']!r}")
    if actual["cls"] != int(expected["cls"]):
        fail(f"cls: expected {int(expected['cls'])!r}, got {actual['cls']!r}")
    if actual["json"] != expected["json"]:
        fail(f"json: expected {expected['json']!r}, got {actual['json']!r}")

    compare_arrays("npy", actual["npy"], expected["npy"])
    compare_npz("npz", actual["npz"], expected["npz"])
    compare_ten("ten", actual["ten"], expected["ten"])
    compare_arrays("png", actual["png"], expected["png"])


def write_dataset(output_dir: Path, pattern: str, samples: int, maxcount: int) -> list[Path]:
    if output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(output_dir.glob("*.tar"))
    if existing:
        fail(f"{output_dir}: directory already contains tar files ({', '.join(p.name for p in existing)})")

    finished: list[Path] = []

    def post(fname: str) -> None:
        finished.append(Path(fname))

    writer_pattern = str(output_dir / pattern)
    with wds.ShardWriter(writer_pattern, maxcount=maxcount, maxsize=10**12, post=post, mtime=0, verbose=0) as sink:
        for index in range(samples):
            sink.write(make_sample(index))

    expected = expected_shard_paths(output_dir, pattern, samples, maxcount)
    if finished != expected:
        fail(f"post hook mismatch, expected {[p.name for p in expected]}, got {[p.name for p in finished]}")
    for shard_path in expected:
        if not shard_path.exists():
            fail(f"missing shard after write: {shard_path}")
    return expected


def read_back(shards: list[Path]) -> list[dict[str, Any]]:
    dataset = wds.DataPipeline(
        wds.SimpleShardList([str(path) for path in shards]),
        wds.tarfile_samples,
        wds.decode("rgb8"),
    )
    return list(dataset)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a tiny deterministic WebDataset shard set and validate it by reading it back."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for the generated shards. Defaults to a fresh temporary directory.",
    )
    parser.add_argument(
        "--pattern",
        default="tiny-%06d.tar",
        help="Shard filename pattern relative to the output directory.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="Number of deterministic samples to write.",
    )
    parser.add_argument(
        "--maxcount",
        type=int,
        default=2,
        help="Maximum samples per shard before rollover.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.samples < 1:
        fail("--samples must be at least 1")
    if args.maxcount < 1:
        fail("--maxcount must be at least 1")

    output_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="webdataset-tiny-"))
    shards = write_dataset(output_dir, args.pattern, args.samples, args.maxcount)
    records = read_back(shards)

    if len(records) != args.samples:
        fail(f"round-trip sample count mismatch, expected {args.samples}, got {len(records)}")

    expected_by_key = {make_sample(index)["__key__"]: make_sample(index) for index in range(args.samples)}
    seen_keys: list[str] = []
    for record in records:
        key = record.get("__key__")
        if key is None:
            fail("read-back sample is missing __key__")
        if key not in expected_by_key:
            fail(f"unexpected key in read-back data: {key!r}")
        seen_keys.append(key)
        compare_sample(record, expected_by_key[key])

    expected_keys = [f"tiny-{index:03d}" for index in range(args.samples)]
    if seen_keys != expected_keys:
        fail(f"sample order mismatch, expected {expected_keys}, got {seen_keys}")

    print(f"validated {len(records)} samples across {len(shards)} shard(s)")
    for shard_path in shards:
        print(shard_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
