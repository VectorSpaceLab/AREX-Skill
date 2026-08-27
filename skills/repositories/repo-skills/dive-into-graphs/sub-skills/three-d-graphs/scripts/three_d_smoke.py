#!/usr/bin/env python3
"""Tiny DIG 3D smoke check.

Uses only import surfaces and a tiny MAE example plus one small 3D validity
example. No downloads, checkpoints, or training.
"""
import argparse
import json

import numpy as np
import torch
from rdkit import Chem

from dig.ggraph3D.evaluation import PropOptEvaluator as GeoPropOptEvaluator, RandGenEvaluator as GeoRandGenEvaluator
from dig.ggraph3D.method import G_SphereNet
from dig.threedgraph.evaluation import ThreeDEvaluator


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG 3D smoke check.")
    parser.parse_args()

    mae = ThreeDEvaluator().eval({
        "y_true": np.array([1.0, -0.5]),
        "y_pred": np.array([0.6, 0.0]),
    })

    geo = GeoRandGenEvaluator()
    mol_dicts = {
        3: {
            "_atomic_numbers": np.array([[8, 1, 1]]),
            "_positions": np.array([[[0.0, 0.0, 0.0], [0.96, 0.0, 0.0], [-0.24, 0.93, 0.0]]]),
        }
    }
    validity = geo.eval_validity(mol_dicts)

    # Only instantiate the generator wrapper; do not train or load checkpoints.
    g_spherenet = G_SphereNet()

    print(json.dumps({
        "three_d_mae": mae,
        "validity": validity,
        "g_spherenet_type": type(g_spherenet).__name__,
        "geo_prop_cls": GeoPropOptEvaluator.__name__,
    }, indent=2, sort_keys=True))
    print("three_d_smoke: ok")


if __name__ == "__main__":
    main()
