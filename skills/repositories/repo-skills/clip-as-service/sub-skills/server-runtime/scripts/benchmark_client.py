#!/usr/bin/env python3
"""Bounded benchmark helper for an already-running CLIP-as-service server.

This adapts the repository benchmark idea into a safer standalone helper. It
never starts a server or downloads models. It contacts only the --server URI
provided by the user.
"""

from __future__ import annotations

import argparse
import random
import statistics
import string
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def make_text_batch(size: int) -> list[str]:
    rng = random.Random(123)
    words = ["clip", "image", "text", "retrieval", "service", "vector", "rank", "search"]
    return [" ".join(rng.choice(words) for _ in range(12)) for _ in range(size)]


def make_image_batch(size: int, image_sample: Path) -> list[bytes]:
    data = image_sample.read_bytes()
    from docarray import Document

    return [Document(blob=data) for _ in range(size)]


def run_client(server: str, batch_size: int, num_iter: int, modality: str, image_sample: Path | None) -> float:
    from clip_client import Client

    if modality == "text":
        batch = make_text_batch(batch_size)
    elif modality == "image":
        if image_sample is None:
            raise ValueError("image modality requires --image-sample")
        batch = make_image_batch(batch_size, image_sample)
    else:
        raise ValueError(f"unsupported modality {modality!r}")

    client = Client(server)
    times: list[float] = []
    for _ in range(num_iter):
        started = time.perf_counter()
        client.encode(batch, batch_size=batch_size)
        times.append(time.perf_counter() - started)
    trimmed = times[2:] if len(times) > 2 else times
    return batch_size / statistics.mean(trimmed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark clip_client.encode against an existing CLIP-as-service server.")
    parser.add_argument("--server", required=True, help="Server URI such as grpc://127.0.0.1:51000.")
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 8, 16], help="Batch sizes to test.")
    parser.add_argument("--concurrent-clients", type=int, nargs="+", default=[1, 4], help="Concurrent client counts.")
    parser.add_argument("--num-iter", type=int, default=5, help="Repeat count per client; must be >=3.")
    parser.add_argument("--modality", choices=["text", "image"], default="text")
    parser.add_argument("--image-sample", type=Path, help="Small image file for image benchmark.")
    args = parser.parse_args()

    if args.num_iter < 3:
        parser.error("--num-iter must be at least 3")
    if args.modality == "image" and not args.image_sample:
        parser.error("--modality image requires --image-sample")

    for batch_size in args.batch_sizes:
        for clients in args.concurrent_clients:
            with ThreadPoolExecutor(max_workers=clients) as pool:
                futures = [pool.submit(run_client, args.server, batch_size, args.num_iter, args.modality, args.image_sample) for _ in range(clients)]
                speeds = [future.result() for future in futures]
            print(
                f"concurrent_clients={clients} batch_size={batch_size} "
                f"avg_qps={statistics.mean(speeds):.3f} max_qps={max(speeds):.3f} min_qps={min(speeds):.3f}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
