#!/usr/bin/env python3
"""Local pgmpy data/I/O/metric smoke test.

The default run does not load remote example datasets/models. It lists local
registries, performs a temporary BIF roundtrip on a tiny model, and computes
small graph metrics using only the installed pgmpy package.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-registry-items",
        type=int,
        default=5,
        help="Number of dataset/model names to show from each registry listing (default: 5).",
    )
    parser.add_argument(
        "--skip-registries",
        action="store_true",
        help="Skip list_datasets/list_models registry lookups.",
    )
    parser.add_argument(
        "--load-example",
        metavar="MODEL_NAME",
        help=(
            "Optionally load one example model, for example bnlearn/asia. This may read the "
            "Hugging Face cache or use network on cache miss; omitted by default."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of text.",
    )
    return parser


def tiny_model_roundtrip() -> dict[str, Any]:
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.models import DiscreteBayesianNetwork

    model = DiscreteBayesianNetwork([("A", "B")])
    model.add_cpds(
        TabularCPD("A", 2, [[0.6], [0.4]], state_names={"A": ["false", "true"]}),
        TabularCPD(
            "B",
            2,
            [[0.8, 0.2], [0.2, 0.8]],
            evidence=["A"],
            evidence_card=[2],
            state_names={"A": ["false", "true"], "B": ["no", "yes"]},
        ),
    )
    if model.check_model() is not True:
        raise RuntimeError("tiny model did not pass check_model() before serialization")

    with TemporaryDirectory(prefix="pgmpy-data-io-") as tmpdir:
        path = Path(tmpdir) / "tiny.bif"
        model.save(str(path), filetype="bif")
        loaded = DiscreteBayesianNetwork.load(str(path), filetype="bif")
        if loaded.check_model() is not True:
            raise RuntimeError("BIF roundtrip model did not pass check_model()")
        if set(loaded.nodes()) != {"A", "B"} or set(loaded.edges()) != {("A", "B")}:
            raise RuntimeError("BIF roundtrip changed tiny model structure")
        return {
            "filetype": "bif",
            "nodes": sorted(loaded.nodes()),
            "edges": sorted(map(list, loaded.edges())),
            "cpd_count": len(loaded.get_cpds()),
        }


def graph_metrics() -> dict[str, Any]:
    from pgmpy.base import DAG
    from pgmpy.metrics import AdjacencyConfusionMatrix, OrientationConfusionMatrix, SHD

    true_graph = DAG([("A", "B"), ("B", "C")])
    est_graph = DAG([("B", "A"), ("B", "C")])
    est_graph.add_nodes_from(true_graph.nodes())

    adjacency = AdjacencyConfusionMatrix(metrics=["precision", "recall", "f1"])(
        true_causal_graph=true_graph,
        est_causal_graph=est_graph,
    )
    orientation = OrientationConfusionMatrix(metrics=["precision", "recall"])(
        true_causal_graph=true_graph,
        est_causal_graph=est_graph,
    )
    return {
        "shd": SHD()(true_causal_graph=true_graph, est_causal_graph=est_graph),
        "adjacency": adjacency,
        "orientation": orientation,
    }


def registry_snapshot(max_items: int) -> dict[str, Any]:
    from pgmpy.datasets import list_datasets
    from pgmpy.example_models import list_models

    if max_items < 0:
        raise ValueError("--max-registry-items must be non-negative")

    datasets = list_datasets()
    models = list_models()
    return {
        "dataset_count": len(datasets),
        "dataset_sample": datasets[:max_items],
        "model_count": len(models),
        "model_sample": models[:max_items],
    }


def optional_example_model(name: str) -> dict[str, Any]:
    from pgmpy.example_models import load_model

    model = load_model(name)
    return {
        "name": name,
        "type": type(model).__name__,
        "nodes": len(model.nodes()),
        "edges": len(model.edges()),
        "has_cpds": hasattr(model, "cpds"),
    }


def main() -> int:
    args = build_parser().parse_args()
    summary: dict[str, Any] = {
        "registry": None,
        "bif_roundtrip": tiny_model_roundtrip(),
        "metrics": graph_metrics(),
        "example_model": None,
    }

    if not args.skip_registries:
        summary["registry"] = registry_snapshot(args.max_registry_items)

    if args.load_example:
        summary["example_model"] = optional_example_model(args.load_example)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        if summary["registry"] is not None:
            registry = summary["registry"]
            print(
                "registries: "
                f"{registry['dataset_count']} datasets {registry['dataset_sample']}; "
                f"{registry['model_count']} models {registry['model_sample']}"
            )
        bif = summary["bif_roundtrip"]
        print(f"bif roundtrip: nodes={bif['nodes']} edges={bif['edges']} cpds={bif['cpd_count']}")
        print(f"metrics: {summary['metrics']}")
        if summary["example_model"] is not None:
            print(f"example model: {summary['example_model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
