#!/usr/bin/env python3
"""Tiny Ray-only smoke test for Modin's experimental Batch Pipeline API."""

from __future__ import annotations

import argparse
import os
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic Modin PandasQueryPipeline smoke test. "
            "The Batch Pipeline API is Ray/PandasOnRay-only."
        )
    )
    parser.add_argument(
        "--engine",
        choices=("Ray", "Python", "Dask"),
        default="Ray",
        help="Modin engine to request before importing modin.pandas; must be Ray.",
    )
    parser.add_argument("--cpus", type=int, default=2, help="Small local CPU count to expose to Modin/Ray for this smoke.")
    parser.add_argument("--num-partitions", type=int, default=2, help="Pipeline num_partitions used for the tiny fixture.")
    return parser.parse_args()


def add_total(partition):
    """Partition function: receives and returns a pandas DataFrame."""
    partition = partition.copy()
    partition["total"] = partition["a"] + partition["b"]
    return partition


def rename_total(partition):
    """Second output transformation used to prove multiple output IDs."""
    return partition.rename(columns={"total": "score"})


def add_metadata(partition, output_id, partition_id):
    """Postprocessor proving output_id and partition_id are passed correctly."""
    partition = partition.copy()
    partition["output_id"] = str(output_id)
    partition["partition_id"] = int(partition_id)
    return partition


def run_smoke(args: argparse.Namespace) -> None:
    if args.engine != "Ray":
        raise SystemExit("This smoke covers the Batch Pipeline API, which is only implemented for PandasOnRay. Re-run with --engine Ray.")
    if args.cpus < 1:
        raise SystemExit("--cpus must be >= 1")
    if args.num_partitions < 1:
        raise SystemExit("--num-partitions must be >= 1")

    os.environ.pop("MODIN_BACKEND", None)
    os.environ["MODIN_ENGINE"] = args.engine
    os.environ["MODIN_CPUS"] = str(args.cpus)
    os.environ["MODIN_NPARTITIONS"] = str(args.num_partitions)

    import modin.pandas as pd
    from modin.experimental.batch import PandasQueryPipeline
    from modin.utils import get_current_execution

    current_execution = get_current_execution()
    if current_execution != "PandasOnRay":
        raise RuntimeError(
            "Batch Pipeline API requires PandasOnRay execution; "
            f"current execution is {current_execution!r}. Set MODIN_ENGINE=Ray before importing modin.pandas."
        )

    df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]})
    pipeline = PandasQueryPipeline(df, num_partitions=args.num_partitions)
    pipeline.add_query(add_total, is_output=True, output_id="with_total")
    pipeline.add_query(rename_total, is_output=True, output_id="renamed")
    outputs = pipeline.compute_batch(postprocessor=add_metadata, pass_output_id=True, pass_partition_id=True)

    if set(outputs) != {"with_total", "renamed"}:
        raise AssertionError(f"Unexpected output IDs: {sorted(outputs)!r}")

    with_total = outputs["with_total"].sort_values("a").reset_index(drop=True)
    renamed = outputs["renamed"].sort_values("a").reset_index(drop=True)

    if with_total["total"].tolist() != [11, 22, 33, 44]:
        raise AssertionError(f"Unexpected totals: {with_total['total'].tolist()!r}")
    if "score" not in renamed.columns:
        raise AssertionError("Second output should contain renamed 'score' column")
    if renamed["score"].tolist() != [11, 22, 33, 44]:
        raise AssertionError(f"Unexpected renamed scores: {renamed['score'].tolist()!r}")
    if set(with_total["output_id"].unique()) != {"with_total"}:
        raise AssertionError("Postprocessor did not receive output_id for first output")
    if set(renamed["output_id"].unique()) != {"renamed"}:
        raise AssertionError("Postprocessor did not receive output_id for second output")

    print(f"Batch pipeline smoke passed: outputs=with_total,renamed rows={len(with_total)} execution={current_execution}")


def main() -> None:
    run_smoke(parse_args())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"batch_pipeline_smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
