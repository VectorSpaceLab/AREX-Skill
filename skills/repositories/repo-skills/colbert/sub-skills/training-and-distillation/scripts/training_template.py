#!/usr/bin/env python3
"""Emit a safe ColBERT training script template with resource warnings."""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


TEMPLATE = '''\
"""ColBERT training template.

Before running real training:
- Validate triples, queries, and collection files with validate_training_files.py.
- Confirm CUDA GPUs are available for practical training.
- Ensure --bsize is divisible by --nranks.
- Pass the source checkpoint to trainer.train(checkpoint=...), not only ColBERTConfig.
"""

from colbert import Trainer
from colbert.infra import ColBERTConfig, Run, RunConfig


def train():
    triples = {triples!r}
    queries = {queries!r}
    collection = {collection!r}
    checkpoint = {checkpoint!r}

    with Run().context(RunConfig(nranks={nranks}, experiment={experiment!r})):
        config = ColBERTConfig(
            bsize={bsize},
            lr={lr},
            maxsteps={maxsteps},
            warmup={warmup},
            nway={nway},
            accumsteps={accumsteps},
            use_ib_negatives={use_ib_negatives},
            distillation_alpha={distillation_alpha},
            ignore_scores={ignore_scores},
            doc_maxlen={doc_maxlen},
            query_maxlen={query_maxlen},
            dim={dim},
            similarity={similarity!r},
            attend_to_mask_tokens={attend_to_mask_tokens},
            root={root!r},
        )

        trainer = Trainer(
            triples=triples,
            queries=queries,
            collection=collection,
            config=config,
        )

        print(f"Starting ColBERT training from checkpoint: {{checkpoint}}")
        trainer.train(checkpoint=checkpoint)
        print(f"Saved checkpoint to {{trainer.best_checkpoint_path()}}")


if __name__ == "__main__":
    train()
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a ColBERT training script template. The generated script is not executed."
    )
    parser.add_argument("--output", type=Path, help="Write the template to this path instead of stdout.")
    parser.add_argument("--triples", default="./data/triples.train.jsonl", help="Training examples path placeholder.")
    parser.add_argument("--queries", default="./data/queries.train.tsv", help="Queries TSV path placeholder.")
    parser.add_argument("--collection", default="./data/collection.tsv", help="Collection TSV path placeholder.")
    parser.add_argument("--checkpoint", default="bert-base-uncased", help="Source checkpoint passed to Trainer.train().")
    parser.add_argument("--root", default="./experiments", help="Experiment root for generated script.")
    parser.add_argument("--experiment", default="colbert-training", help="Run experiment name.")
    parser.add_argument("--nranks", type=int, default=1, help="Number of distributed GPU ranks/processes.")
    parser.add_argument("--bsize", type=int, default=32, help="Global batch size; must be divisible by nranks.")
    parser.add_argument("--lr", default="3e-6", help="Learning rate literal for generated script.")
    parser.add_argument("--maxsteps", type=int, default=500000, help="Maximum training steps.")
    parser.add_argument("--warmup", default="None", help="Warmup steps literal, e.g. 20000 or None.")
    parser.add_argument("--nway", type=int, default=2, help="Passages per query example.")
    parser.add_argument("--accumsteps", type=int, default=1, help="Gradient accumulation steps.")
    parser.add_argument("--use-ib-negatives", action="store_true", help="Enable in-batch negative loss.")
    parser.add_argument("--distillation-alpha", default="1.0", help="Teacher-score multiplier literal.")
    parser.add_argument("--ignore-scores", action="store_true", help="Ignore teacher scores in examples.")
    parser.add_argument("--doc-maxlen", type=int, default=220, help="Document max token length.")
    parser.add_argument("--query-maxlen", type=int, default=32, help="Query max token length.")
    parser.add_argument("--dim", type=int, default=128, help="Embedding dimension.")
    parser.add_argument("--similarity", default="cosine", help="Similarity function.")
    parser.add_argument("--attend-to-mask-tokens", action="store_true", help="Set attend_to_mask_tokens=True.")
    parser.add_argument(
        "--colbertv2-style",
        action="store_true",
        help="Apply README-style ColBERTv2 defaults: nway=64, lr=1e-5, warmup=20000, doc_maxlen=180, use_ib_negatives=True.",
    )
    return parser.parse_args()


def apply_presets(args: argparse.Namespace) -> argparse.Namespace:
    if args.colbertv2_style:
        args.nway = 64
        args.lr = "1e-5"
        args.warmup = "20000"
        args.doc_maxlen = 180
        args.use_ib_negatives = True
    return args


def validate_literal(name: str, value: str) -> str:
    try:
        compile(value, f"<{name}>", "eval")
    except SyntaxError as exc:
        raise ValueError(f"--{name.replace('_', '-')} must be a valid Python literal/expression: {value!r}") from exc
    return value


def validate_resource_choices(args: argparse.Namespace) -> list[str]:
    warnings: list[str] = []
    if args.nranks < 1:
        warnings.append("--nranks should be at least 1.")
    if args.bsize < 1:
        warnings.append("--bsize should be at least 1.")
    if args.accumsteps < 1:
        warnings.append("--accumsteps should be at least 1.")
    if args.nway < 2:
        warnings.append("--nway should be at least 2 for ColBERT training examples.")
    if args.nranks >= 1 and args.bsize >= 1 and args.bsize % args.nranks != 0:
        warnings.append("--bsize is not divisible by --nranks; ColBERT training asserts this.")
    if args.nway >= 32:
        warnings.append("Large nway values such as 64 require substantially more GPU memory and data volume.")
    if args.maxsteps > 1000:
        warnings.append("This template is configured for real training, not a tiny smoke test; confirm GPU/runtime budget before launching.")
    if args.ignore_scores:
        warnings.append("--ignore-scores makes scored distillation examples train with cross-entropy behavior.")
    return warnings


def render(args: argparse.Namespace) -> str:
    lr = validate_literal("lr", args.lr)
    warmup = validate_literal("warmup", args.warmup)
    distillation_alpha = validate_literal("distillation_alpha", args.distillation_alpha)

    return dedent(
        TEMPLATE.format(
            triples=args.triples,
            queries=args.queries,
            collection=args.collection,
            checkpoint=args.checkpoint,
            root=args.root,
            experiment=args.experiment,
            nranks=args.nranks,
            bsize=args.bsize,
            lr=lr,
            maxsteps=args.maxsteps,
            warmup=warmup,
            nway=args.nway,
            accumsteps=args.accumsteps,
            use_ib_negatives=args.use_ib_negatives,
            distillation_alpha=distillation_alpha,
            ignore_scores=args.ignore_scores,
            doc_maxlen=args.doc_maxlen,
            query_maxlen=args.query_maxlen,
            dim=args.dim,
            similarity=args.similarity,
            attend_to_mask_tokens=args.attend_to_mask_tokens,
        )
    )


def main() -> int:
    args = apply_presets(parse_args())

    try:
        script = render(args)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    warnings = validate_resource_choices(args)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(script, encoding="utf-8")
        print(f"Wrote ColBERT training template to {args.output}")
    else:
        print(script, end="")

    if warnings:
        print("\nResource warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\nResource warnings: none for template generation; still confirm CUDA before real training.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
