#!/usr/bin/env python3
"""Tiny self-contained DoWhy GCM smoke script.

The script creates synthetic data, builds a graph, assigns causal mechanisms,
fits a GCM, draws samples, and can optionally run a simple intervention and GCM
average causal effect estimate. It performs no downloads and does not depend on
the current working directory.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from dowhy import gcm


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def make_data(samples: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = rng.normal(loc=0.0, scale=1.0, size=samples)
    treatment = 0.8 * x + rng.normal(loc=0.0, scale=0.5, size=samples)
    outcome = 1.7 * treatment + 0.4 * x + rng.normal(loc=0.0, scale=0.5, size=samples)
    return pd.DataFrame({"X": x, "T": treatment, "Y": outcome})


def build_model(data: pd.DataFrame) -> gcm.StructuralCausalModel:
    graph = nx.DiGraph([("X", "T"), ("X", "Y"), ("T", "Y")])
    causal_model = gcm.StructuralCausalModel(graph)
    gcm.auto.assign_causal_mechanisms(
        causal_model,
        data,
        quality=gcm.auto.AssignmentQuality.GOOD,
    )
    gcm.fit(causal_model, data)
    return causal_model


def summarize_frame(frame: pd.DataFrame, rows: int) -> list[dict[str, Any]]:
    rounded = frame.head(rows).round(4)
    return rounded.to_dict(orient="records")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny DoWhy GCM smoke workflow.")
    parser.add_argument("--samples", type=_positive_int, default=300, help="training rows to generate")
    parser.add_argument("--seed", type=int, default=7, help="NumPy random seed")
    parser.add_argument("--draws", type=_positive_int, default=5, help="rows to draw from the fitted model")
    parser.add_argument(
        "--intervene",
        action="store_true",
        help="also run an atomic intervention on T and estimate a small GCM ACE",
    )
    parser.add_argument(
        "--intervention-value",
        type=float,
        default=1.0,
        help="value used for the optional do(T := value) intervention",
    )
    parser.add_argument(
        "--ace-samples",
        type=_positive_int,
        default=100,
        help="sample count for the optional GCM average causal effect estimate",
    )
    args = parser.parse_args()

    np.random.seed(args.seed)
    gcm.config.disable_progress_bars()

    data = make_data(args.samples, args.seed)
    causal_model = build_model(data)
    drawn = gcm.draw_samples(causal_model, args.draws)

    result: dict[str, Any] = {
        "status": "ok",
        "nodes": list(causal_model.graph.nodes),
        "edges": list(map(list, causal_model.graph.edges)),
        "training_rows": int(data.shape[0]),
        "drawn_samples": summarize_frame(drawn, args.draws),
    }

    if args.intervene:
        intervention = {"T": lambda _x: args.intervention_value}
        intervened = gcm.interventional_samples(
            causal_model,
            intervention,
            num_samples_to_draw=args.draws,
        )
        ace = gcm.average_causal_effect(
            causal_model,
            target_node="Y",
            interventions_alternative=intervention,
            interventions_reference={"T": lambda _x: 0.0},
            num_samples_to_draw=args.ace_samples,
        )
        result["intervention"] = f"do(T := {args.intervention_value})"
        result["interventional_samples"] = summarize_frame(intervened, args.draws)
        result["gcm_average_causal_effect_vs_T0"] = round(float(ace), 4)

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
