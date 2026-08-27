#!/usr/bin/env python3
"""Build a contributed Facenet embedding export command."""
from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Facenet export_embeddings command.")
    parser.add_argument("model_dir")
    parser.add_argument("data_dir")
    parser.add_argument("--is-aligned", default="True", choices=["True", "False"])
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--margin", type=int, default=44)
    parser.add_argument("--gpu-memory-fraction", type=float, default=1.0)
    parser.add_argument("--image-batch", type=int, default=500)
    parser.add_argument("--embeddings-name", default="embeddings.npy")
    parser.add_argument("--labels-name", default="labels.npy")
    parser.add_argument("--labels-strings-name", default="label_strings.npy")
    args = parser.parse_args()
    cmd = [
        "python", "-m", "export_embeddings", args.model_dir, args.data_dir,
        "--is_aligned", args.is_aligned,
        "--image_size", str(args.image_size),
        "--margin", str(args.margin),
        "--gpu_memory_fraction", str(args.gpu_memory_fraction),
        "--image_batch", str(args.image_batch),
        "--embeddings_name", args.embeddings_name,
        "--labels_name", args.labels_name,
        "--labels_strings_name", args.labels_strings_name,
    ]
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
