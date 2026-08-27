#!/usr/bin/env python3
"""Run a tiny CPU-only numpy-ml neural component smoke.

This does not train a full network and does not require PyTorch/TensorFlow.
"""
import argparse
import json
import warnings

import numpy as np


def run():
    warnings.filterwarnings("ignore")
    from numpy_ml.neural_nets.activations import ReLU, Sigmoid
    from numpy_ml.neural_nets.layers import FullyConnected
    from numpy_ml.neural_nets.losses import SquaredError, CrossEntropy
    from numpy_ml.neural_nets.optimizers import SGD, Adam
    from numpy_ml.neural_nets.schedulers import ConstantScheduler

    relu = ReLU().fn(np.array([-1.0, 2.0]))
    sig = Sigmoid().fn(np.array([0.0]))

    layer = FullyConnected(3, act_fn="ReLU", optimizer=SGD(lr=0.01))
    out = layer.forward(np.ones((2, 2)))

    mse = SquaredError().loss(np.ones((2, 1)), np.zeros((2, 1)))
    ce = CrossEntropy().loss(np.eye(2), np.array([[0.9, 0.1], [0.2, 0.8]]))
    opt = Adam(lr=0.001)
    sched = ConstantScheduler(lr=0.01)

    return {
        "relu": relu.tolist(),
        "sigmoid_zero": float(sig[0]),
        "fully_connected_output_shape": list(out.shape),
        "squared_error": float(mse),
        "cross_entropy": float(ce),
        "optimizer": opt.hyperparameters["id"],
        "scheduler": sched.hyperparameters["id"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("numpy-ml neural component smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
