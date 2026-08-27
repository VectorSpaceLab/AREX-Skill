#!/usr/bin/env python3
"""Plan or run a tiny CPU-only CogDL experiment.

Default behavior is dry-run: the script builds a synthetic NodeDataset inside a
temporary directory, prints the planned model/seed variants, and exits without
training. Pass --run to execute a very short CPU experiment on the synthetic
fixture.
"""

from __future__ import annotations

import argparse
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable


@contextmanager
def pushd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def build_tiny_dataset(root: Path, num_nodes: int, num_edges: int, num_features: int, num_classes: int):
    """Create a tiny random NodeDataset without any network access."""

    import torch
    from cogdl.datasets import NodeDataset, generate_random_graph

    graph = generate_random_graph(num_nodes=num_nodes, num_edges=num_edges, num_feats=num_features)
    if num_classes != 2:
        graph.y = torch.randint(0, num_classes, (num_nodes,))

    dataset_path = root / "tiny-node-dataset.pt"
    return NodeDataset(path=str(dataset_path), data=graph, scale_feat=True, metric="auto")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="actually train on the tiny synthetic dataset")
    parser.add_argument("--model", nargs="+", default=["gcn", "gat"], help="one or more model names")
    parser.add_argument("--seed", nargs="+", type=int, default=[0, 1], help="one or more seeds")
    parser.add_argument("--epochs", type=int, default=2, help="short CPU training length")
    parser.add_argument("--hidden-size", type=int, default=16, help="tiny hidden size for the smoke run")
    parser.add_argument("--num-nodes", type=int, default=32, help="synthetic node count")
    parser.add_argument("--num-edges", type=int, default=64, help="synthetic edge count")
    parser.add_argument("--num-features", type=int, default=16, help="synthetic feature width")
    parser.add_argument("--num-classes", type=int, default=2, help="synthetic label count")
    return parser


def format_variants(models: Iterable[str], seeds: Iterable[int]) -> int:
    from cogdl.experiments import gen_variants

    variants = list(gen_variants(dataset=["tiny-random-node"], model=list(models), seed=list(seeds), split=[0]))
    return len(variants)


def main() -> int:
    args = make_parser().parse_args()

    print("CogDL tiny experiment plan")
    print(f"  models: {args.model}")
    print(f"  seeds: {args.seed}")
    print(f"  epochs: {args.epochs}")
    print(f"  hidden_size: {args.hidden_size}")
    print(f"  synthetic graph: nodes={args.num_nodes}, edges={args.num_edges}, features={args.num_features}, classes={args.num_classes}")
    print(f"  planned variants: {format_variants(args.model, args.seed)}")

    if not args.run:
        print("Dry-run only. Re-run with --run to execute the tiny CPU experiment.")
        return 0

    with TemporaryDirectory(prefix="cogdl-tiny-exp-") as tmp:
        workdir = Path(tmp)
        dataset = build_tiny_dataset(
            workdir,
            num_nodes=args.num_nodes,
            num_edges=args.num_edges,
            num_features=args.num_features,
            num_classes=args.num_classes,
        )

        from cogdl import experiment

        with pushd(workdir):
            results = experiment(
                dataset=dataset,
                model=args.model,
                seed=args.seed,
                cpu=True,
                epochs=args.epochs,
                hidden_size=args.hidden_size,
                checkpoint_path=str(workdir / "tiny-checkpoint.pt"),
                log_path=str(workdir / "logs"),
                project="cogdl-tiny-exp",
            )

        print("Experiment completed. Result keys:")
        for key in results:
            print(f"  {key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
