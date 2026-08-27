#!/usr/bin/env python3
"""Deterministic pymoo postprocessing smoke checks.

The script builds a small ZDT1 Pareto-front fixture, scores a degraded result
set with core indicators, and also checks reference directions, decomposition,
and simple MCDM selection. It is intentionally tiny and CPU-only.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np

from pymoo.decomposition.asf import ASF
from pymoo.decomposition.weighted_sum import WeightedSum
from pymoo.indicators.epsilon import Epsilon, EpsilonMultiplicative
from pymoo.indicators.gd import GD
from pymoo.indicators.gd_plus import GDPlus
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD
from pymoo.indicators.igd_plus import IGDPlus
from pymoo.mcdm.high_tradeoff import HighTradeoffPoints
from pymoo.mcdm.pseudo_weights import PseudoWeights
from pymoo.problems import get_problem
from pymoo.util.ref_dirs import get_reference_directions


def as_float(value: Any) -> float:
    """Convert NumPy scalar-like outputs into a JSON-friendly float."""
    return float(np.asarray(value).reshape(()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a compact text summary.",
    )
    args = parser.parse_args()

    pf = np.asarray(get_problem("zdt1").pareto_front(), dtype=float)
    F = pf[::10] * 1.1
    ref_point = np.array([1.2, 1.2], dtype=float)

    assert pf.ndim == 2 and F.ndim == 2
    assert pf.shape[1] == F.shape[1] == ref_point.size
    assert np.isfinite(pf).all() and np.isfinite(F).all()
    assert np.all(F <= ref_point + 1e-12), "HV reference point must be worse than F"

    scores = {
        "GD": as_float(GD(pf).do(F)),
        "GDPlus": as_float(GDPlus(pf).do(F)),
        "IGD": as_float(IGD(pf).do(F)),
        "IGDPlus": as_float(IGDPlus(pf).do(F)),
        "HV": as_float(HV(ref_point=ref_point).do(F)),
        "Epsilon": as_float(Epsilon(pf).do(F)),
        # Multiplicative epsilon needs positive values, so shift both matrices.
        "EpsilonMultiplicative": as_float(EpsilonMultiplicative(pf + 1.0).do(F + 1.0)),
    }

    expected = {
        "GD": 0.05497689467314528,
        "GDPlus": 0.05497689467314528,
        "IGD": 0.06690908300327661,
        "IGDPlus": 0.06466828842775944,
        "HV": 0.9631646448182306,
        "Epsilon": 0.10101010101010104,
        "EpsilonMultiplicative": 1.1,
    }
    for name, target in expected.items():
        assert np.isclose(scores[name], target, rtol=1e-9, atol=1e-12), (name, scores[name], target)

    ref_dirs = get_reference_directions("uniform", 3, n_partitions=4)
    assert ref_dirs.shape == (15, 3)
    assert np.allclose(ref_dirs.sum(axis=1), 1.0)
    assert np.all(ref_dirs >= -1e-12)

    toy_F = np.array([[0.0, 1.0], [0.5, 0.25], [1.0, 0.0]], dtype=float)
    weights = np.array([0.4, 0.6], dtype=float)
    ws = WeightedSum().do(toy_F, weights)
    asf = ASF().do(toy_F, weights)
    np.testing.assert_allclose(ws, np.array([0.6, 0.35, 0.4]))
    assert int(np.argmin(asf)) == 1

    chosen, pseudo = PseudoWeights(np.array([0.5, 0.5])).do(toy_F, return_pseudo_weights=True)
    knees = HighTradeoffPoints().do(toy_F)
    assert int(chosen) == 1
    assert pseudo.shape == toy_F.shape
    assert knees is not None and 1 in np.asarray(knees, dtype=int)

    payload = {
        "indicator_scores": scores,
        "ref_dirs_shape": list(ref_dirs.shape),
        "weighted_sum": ws.tolist(),
        "asf_selected_index": int(np.argmin(asf)),
        "pseudo_weights_selected_index": int(chosen),
        "high_tradeoff_indices": np.asarray(knees, dtype=int).tolist(),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("pymoo analysis smoke passed")
        for key, value in scores.items():
            print(f"{key}: {value:.12g}")
        print(f"reference directions: {ref_dirs.shape[0]}x{ref_dirs.shape[1]}")
        print(f"ASF selected index: {payload['asf_selected_index']}")
        print(f"PseudoWeights selected index: {payload['pseudo_weights_selected_index']}")
        print(f"HighTradeoff indices: {payload['high_tradeoff_indices']}")


if __name__ == "__main__":
    main()
