#!/usr/bin/env python3
"""No-download smoke test for OpenCLIP-style zero-shot classifier construction.

This script mirrors the public build_zero_shot_classifier contract with a tiny
fake tokenizer and deterministic text model. It is useful when checking prompt
batching, template formatting, output orientation, and normalization without
loading OpenCLIP weights or downloading datasets.
"""

from __future__ import annotations

import argparse
import json
from itertools import islice
from typing import Callable, Iterable, Sequence, Union

import torch


def batched(iterable: Iterable[str], batch_size: int):
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            break
        yield batch


def build_zero_shot_classifier_like(
    model,
    tokenizer,
    classnames: Sequence[str],
    templates: Sequence[Union[Callable[[str], str], str]],
    num_classes_per_batch: int | None = 10,
    device: str | torch.device = "cpu",
):
    assert isinstance(templates, Sequence) and len(templates) > 0
    assert isinstance(classnames, Sequence) and len(classnames) > 0
    use_format = isinstance(templates[0], str)
    num_templates = len(templates)

    def process_batch(batch_classnames: Sequence[str]):
        texts = [
            template.format(classname) if use_format else template(classname)
            for classname in batch_classnames
            for template in templates
        ]
        tokenized = tokenizer(texts).to(device)
        output = model(text=tokenized)
        if isinstance(output, dict):
            class_embeddings = output["text_features"]
        elif isinstance(output, (tuple, list)):
            class_embeddings = output[1]
        else:
            class_embeddings = output
        class_embeddings = class_embeddings.reshape(len(batch_classnames), num_templates, -1).mean(dim=1)
        class_embeddings = class_embeddings / class_embeddings.norm(dim=1, keepdim=True)
        return class_embeddings.T

    with torch.no_grad():
        if num_classes_per_batch:
            return torch.cat(
                [process_batch(batch) for batch in batched(classnames, num_classes_per_batch)],
                dim=1,
            )
        return process_batch(classnames)


class TinyTokenizer:
    def __init__(self, context_length: int = 16):
        self.context_length = context_length

    def __call__(self, texts: Sequence[str]) -> torch.Tensor:
        rows = []
        for text in texts:
            encoded = [ord(char) % 251 + 1 for char in text[: self.context_length]]
            encoded += [0] * (self.context_length - len(encoded))
            rows.append(encoded)
        return torch.tensor(rows, dtype=torch.long)


class TinyTextModel(torch.nn.Module):
    def __init__(self, vocab_size: int = 256, embed_dim: int = 8):
        super().__init__()
        torch.manual_seed(0)
        self.embedding = torch.nn.Embedding(vocab_size, embed_dim)
        self.proj = torch.nn.Linear(embed_dim, embed_dim, bias=False)
        self.eval()

    def forward(self, text: torch.Tensor):
        mask = (text != 0).unsqueeze(-1)
        embedded = self.embedding(text.clamp_min(0)) * mask
        lengths = mask.sum(dim=1).clamp_min(1)
        features = self.proj(embedded.sum(dim=1) / lengths)
        features = features / features.norm(dim=-1, keepdim=True)
        return {"text_features": features}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a tiny fake OpenCLIP-style zero-shot classifier without downloads."
    )
    parser.add_argument(
        "--classnames",
        nargs="+",
        default=["tabby cat", "golden retriever", "espresso"],
        help="Class names to format into templates.",
    )
    parser.add_argument(
        "--templates",
        nargs="+",
        default=["a photo of a {}.", "a blurry photo of a {}."],
        help="Format-string templates containing {}.",
    )
    parser.add_argument(
        "--num-classes-per-batch",
        type=int,
        default=2,
        help="Class batching; use 0 to process all classes in one batch.",
    )
    parser.add_argument("--embed-dim", type=int, default=8, help="Tiny fake embedding dimension.")
    parser.add_argument("--context-length", type=int, default=16, help="Tiny fake tokenizer context length.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if any("{}" not in template for template in args.templates):
        raise SystemExit("All string templates must contain '{}' for the class name.")

    model = TinyTextModel(embed_dim=args.embed_dim)
    tokenizer = TinyTokenizer(context_length=args.context_length)
    batch_size = args.num_classes_per_batch or None
    classifier = build_zero_shot_classifier_like(
        model,
        tokenizer,
        classnames=args.classnames,
        templates=args.templates,
        num_classes_per_batch=batch_size,
        device="cpu",
    )
    column_norms = classifier.norm(dim=0)
    summary = {
        "num_classes": len(args.classnames),
        "num_templates": len(args.templates),
        "shape": list(classifier.shape),
        "column_norms": [round(value, 6) for value in column_norms.tolist()],
        "all_finite": bool(torch.isfinite(classifier).all().item()),
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("zero-shot classifier smoke summary")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
